"""
Структурированное логирование.

Почему JSON, а не текст: неструктурированную строку приходится разбирать
регулярками на стороне сборщика логов, и любое изменение формата сообщения
ломает парсинг. JSON разбирается однозначно, а поля становятся доступны для
фильтрации в Loki без всяких regex.

Почему свой форматтер, а не библиотека: нужно около тридцати строк, а лишняя
зависимость в проде — это лишняя поверхность для CVE и лишний повод для
обновлений. Для сложных случаев (маскирование PII, sampling) библиотека
оправдана, здесь — нет.
"""

import json
import logging
import logging.config
from contextvars import ContextVar
from typing import Any

from opentelemetry import trace

# ContextVar, а не глобальная переменная: значение изолировано в рамках одной
# асинхронной задачи. При конкурентной обработке десятков запросов каждый видит
# только свой request_id, и логи не перемешиваются между запросами.
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Атрибуты LogRecord, которые не нужно тащить в вывод — это внутренности
# stdlib logging, а не полезная информация.
_RESERVED = frozenset(
    {
        "args", "asctime", "created", "exc_info", "exc_text", "filename",
        "funcName", "levelname", "levelno", "lineno", "module", "msecs",
        "message", "msg", "name", "pathname", "process", "processName",
        "relativeCreated", "stack_info", "thread", "threadName", "taskName",
        # uvicorn прокидывает в записи дублирующее сообщение с ANSI-кодами
        # для раскраски терминала — в структурированном выводе это мусор.
        "color_message",
    }
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            # ISO-8601 в UTC — единственный формат, который однозначно
            # сортируется и не зависит от локали машины.
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = request_id_var.get()
        if request_id is not None:
            payload["request_id"] = request_id

        # Связка с трейсингом (Phase 8): если запрос сейчас внутри активного
        # OTel-спана (значит opentelemetry-instrument реально обернул процесс),
        # добавляем trace_id и span_id. Именно по trace_id Grafana строит
        # переход "лог -> конкретный трейс в Tempo" -- derived field в
        # конфиге источника данных Loki ищет ровно "trace_id":"...".
        #
        # get_current_span() безопасен без активной инструментации: в тестах
        # (pytest не запускается под opentelemetry-instrument) возвращается
        # no-op спан с is_valid=False, и поля просто не добавляются -- никакой
        # жёсткой зависимости от реально работающего трейсинга.
        span_context = trace.get_current_span().get_span_context()
        if span_context.is_valid:
            payload["trace_id"] = format(span_context.trace_id, "032x")
            payload["span_id"] = format(span_context.span_id, "016x")

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Любые дополнительные поля, переданные через logger.info(..., extra={...}),
        # попадают в вывод автоматически — не нужно менять форматтер под каждый
        # новый случай.
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging(level: str = "INFO", sql_echo: bool = False) -> None:
    """
    Настраивает логирование для приложения, uvicorn и SQLAlchemy.

    Логгеры uvicorn перенастраиваются явно: uvicorn при старте применяет свой
    конфиг с propagate=False, поэтому без явного перечисления его сообщения
    остались бы обычным текстом, а логи стали бы смесью двух форматов.

    SQLAlchemy тоже настраивается здесь, а не через echo=True в engine: echo
    добавляет собственный обработчик и печатает каждый запрос вторично в обход
    форматтера. Через стандартный logging вывод идёт единожды и в JSON.

    Вызывается при импорте app.main — то есть уже после того, как uvicorn
    применил свой конфиг, поэтому наши настройки перекрывают его.
    """
    uvicorn_logger = {"handlers": ["stdout"], "level": level, "propagate": False}

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": JsonFormatter}},
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    # stdout, а не файл: в контейнерах логи пишут в поток, а
                    # сбором занимается платформа. Файл внутри контейнера
                    # исчезнет при пересоздании и не виден docker logs.
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {"handlers": ["stdout"], "level": level},
            "loggers": {
                "uvicorn": uvicorn_logger,
                "uvicorn.error": uvicorn_logger,
                # uvicorn.access заглушён: структурированный access-лог пишет
                # RequestContextMiddleware, где ещё доступен request_id и есть
                # отдельные поля method/path/status_code/duration_ms. Оставить
                # оба логгера означало бы дублировать каждую запись.
                "uvicorn.access": {"level": "WARNING", "propagate": False},
                # INFO у sqlalchemy.engine означает "логировать каждый SQL".
                # В production это недопустимо: огромный объём и риск утечки
                # данных из параметров запроса в логи.
                "sqlalchemy.engine": {
                    "level": "INFO" if sql_echo else "WARNING",
                    "propagate": True,
                },
            },
        }
    )

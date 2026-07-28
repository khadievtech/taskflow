"""
Middleware корреляции запросов и структурированного access-лога.

Зачем request_id: без общего идентификатора логи одного запроса невозможно
связать между собой. При десяти конкурентных запросах вы видите перемешанные
строки от всех и не можете понять, какие относятся к упавшему. С request_id
достаточно отфильтровать логи по одному значению.

Если клиент прислал X-Request-ID, используем его: так идентификатор сохраняется
при прохождении через несколько сервисов, и по одному значению можно проследить
запрос через всю систему. Это основа distributed tracing — полноценный трейсинг
(OpenTelemetry) добавляет спаны и тайминги, но идея корреляции та же.

Почему access-лог пишет middleware, а не uvicorn:
1. uvicorn формирует строку на уровне ASGI-сервера, то есть уже за пределами
   области видимости ContextVar — request_id туда не попадает. Именно на этом
   первая версия и сломалась: заголовок возвращался, а в логах корреляции не
   было ни в одной строке.
2. Сообщение uvicorn это текст ('GET /path 200'), а нужны отдельные поля
   method, path, status_code, duration_ms — по ним фильтруют в Loki без
   регулярных выражений.

Поэтому логгер uvicorn.access заглушён в app/core/logging.py, а его роль
выполняет этот middleware.
"""

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_var

REQUEST_ID_HEADER = "X-Request-ID"

# Prometheus скрейпит /metrics каждые 15 секунд. Логировать эти обращения —
# значит утопить полезные логи в постоянном шуме от системы мониторинга.
_SILENT_PATHS = frozenset({"/metrics"})

logger = logging.getLogger("app.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        token = request_id_var.set(request_id)
        # perf_counter, а не time(): монотонные часы не прыгают при коррекции
        # системного времени, поэтому длительность не может выйти отрицательной.
        started = time.perf_counter()

        # Вложенный try не случаен: внутренний ловит исключение, чтобы записать
        # лог об ошибке, а внешний finally гарантирует сброс контекста — но уже
        # ПОСЛЕ логирования. Обратный порядок лишил бы запись об ошибке
        # request_id, то есть именно там, где он нужнее всего.
        try:
            try:
                response = await call_next(request)
            except Exception:
                self._log(request, status_code=500, started=started, failed=True)
                raise
            self._log(
                request, status_code=response.status_code, started=started, failed=False
            )
        finally:
            request_id_var.reset(token)

        response.headers[REQUEST_ID_HEADER] = request_id
        return response

    def _log(
        self, request: Request, *, status_code: int, started: float, failed: bool
    ) -> None:
        if request.url.path in _SILENT_PATHS:
            return

        logger.log(
            logging.ERROR if failed else logging.INFO,
            "request failed" if failed else "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
            exc_info=failed,
        )

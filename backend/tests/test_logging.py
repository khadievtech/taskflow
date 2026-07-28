import json
import logging

import pytest
from httpx import AsyncClient

from app.core.logging import JsonFormatter, request_id_var


async def test_response_carries_request_id_header(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/live")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


async def test_client_supplied_request_id_is_preserved(client: AsyncClient) -> None:
    """
    Пробрасывание входящего X-Request-ID — основа сквозной трассировки:
    идентификатор, присвоенный на входе в систему, должен сохраняться при
    прохождении через все сервисы.
    """
    response = await client.get(
        "/api/v1/health/live", headers={"X-Request-ID": "trace-from-client"}
    )
    assert response.headers["x-request-id"] == "trace-from-client"


async def test_request_ids_are_unique_per_request(client: AsyncClient) -> None:
    first = await client.get("/api/v1/health/live")
    second = await client.get("/api/v1/health/live")
    assert first.headers["x-request-id"] != second.headers["x-request-id"]


def test_formatter_emits_valid_json() -> None:
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="x", lineno=1,
        msg="hello %s", args=("world",), exc_info=None,
    )
    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "test"
    # Сообщение должно быть уже подставленным, а не шаблоном с %s.
    assert payload["message"] == "hello world"
    assert "timestamp" in payload


def test_formatter_includes_extra_fields() -> None:
    record = logging.LogRecord(
        name="test", level=logging.WARNING, pathname="x", lineno=1,
        msg="msg", args=(), exc_info=None,
    )
    record.task_id = "abc-123"  # аналог logger.warning(..., extra={"task_id": ...})

    payload = json.loads(JsonFormatter().format(record))
    assert payload["task_id"] == "abc-123"


def test_formatter_includes_request_id_from_context() -> None:
    token = request_id_var.set("ctx-req-1")
    try:
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="x", lineno=1,
            msg="msg", args=(), exc_info=None,
        )
        payload = json.loads(JsonFormatter().format(record))
        assert payload["request_id"] == "ctx-req-1"
    finally:
        request_id_var.reset(token)


def test_formatter_serialises_exceptions() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="x", lineno=1,
            msg="failed", args=(), exc_info=sys.exc_info(),
        )

    payload = json.loads(JsonFormatter().format(record))
    assert "ValueError: boom" in payload["exception"]


@pytest.fixture
def access_logs():
    """
    Перехватывает записи app.access, форматируя их тем же JsonFormatter, что и
    в проде. Форматирование происходит синхронно внутри logger.log(), то есть
    пока ContextVar ещё установлен — иначе request_id в вывод не попал бы.
    """
    captured: list[str] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(JsonFormatter().format(record))

    handler = Capture()
    logger = logging.getLogger("app.access")
    logger.addHandler(handler)
    previous = logger.level
    logger.setLevel(logging.INFO)
    try:
        yield captured
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous)


async def test_access_log_carries_request_id_and_fields(
    client: AsyncClient, access_logs: list[str]
) -> None:
    """
    Регрессионный тест на реальный баг: в первой версии access-лог писал
    uvicorn на уровне ASGI-сервера, то есть уже вне области видимости
    ContextVar. Заголовок X-Request-ID возвращался, но ни одна строка логов
    в production не содержала request_id — корреляция была бесполезна.
    """
    await client.get("/api/v1/health/live", headers={"X-Request-ID": "corr-1"})

    entries = [json.loads(line) for line in access_logs]
    completed = [e for e in entries if e.get("message") == "request completed"]

    assert completed, "access-лог не был записан"
    entry = completed[0]
    assert entry["request_id"] == "corr-1"
    assert entry["method"] == "GET"
    assert entry["path"] == "/api/v1/health/live"
    assert entry["status_code"] == 200
    assert isinstance(entry["duration_ms"], float)


async def test_metrics_scrapes_are_not_logged(
    client: AsyncClient, access_logs: list[str]
) -> None:
    """
    Prometheus скрейпит /metrics каждые 15 секунд. Без фильтра эти записи
    утопили бы полезные логи в шуме от системы мониторинга.
    """
    await client.get("/metrics")

    paths = [json.loads(line).get("path") for line in access_logs]
    assert "/metrics" not in paths

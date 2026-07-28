import json
import logging

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

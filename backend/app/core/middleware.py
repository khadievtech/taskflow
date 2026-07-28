"""
Middleware корреляции запросов.

Зачем: без общего идентификатора логи одного запроса невозможно связать между
собой. При десяти конкурентных запросах вы видите перемешанные строки от всех
и не можете понять, какие из них относятся к упавшему. С request_id достаточно
отфильтровать логи по одному значению и получить полную историю запроса.

Если клиент прислал заголовок X-Request-ID, используем его: так идентификатор
сохраняется при прохождении через несколько сервисов, и по одному значению
можно проследить запрос через всю систему. Это основа distributed tracing —
полноценный трейсинг (OpenTelemetry) добавляет к этому спаны и тайминги,
но идея корреляции та же.
"""

import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_var

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            # Обязательно сбрасываем контекст: без reset значение утекло бы
            # в следующую задачу, переиспользующую тот же контекст.
            request_id_var.reset(token)

        # Возвращаем идентификатор клиенту — тогда пользователь может приложить
        # его к обращению в поддержку, а вы найдёте точную историю запроса.
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

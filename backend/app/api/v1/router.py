"""
Версионирование API через префикс /api/v1 закладываем с первого дня.

Почему это важно: когда через полгода понадобится breaking change в схеме
задач, вы заведёте /api/v2, а фронтенд и мобильные клиенты продолжат
работать со старой версией, пока не мигрируют. Добавлять версионирование
задним числом на живом проекте — боль.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, prefix="/health")

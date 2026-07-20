"""
Engine и session factory.

Почему async, а не sync SQLAlchemy: FastAPI построен на ASGI/asyncio.
Синхронный психопг-драйвер в async-эндпоинте заблокирует event loop на
время запроса к БД — под нагрузкой это душит пропускную способность всего
приложения, а не только одного запроса. asyncpg + SQLAlchemy async — это
то, что реально используют в production FastAPI-проектах.

Почему expire_on_commit=False: по умолчанию SQLAlchemy инвалидирует все
атрибуты объекта после commit, и следующее обращение к ним вызовет ленивую
подгрузку из БД — в async-режиме ленивая подгрузка вне сессии упадёт с
ошибкой (MissingGreenlet). Отключаем, чтобы можно было безопасно вернуть
объект из сессии после commit (типичный кейс: create → commit → return).
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # проверяет "протухшие" соединения перед использованием
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI-dependency: одна сессия на один HTTP-запрос."""
    async with async_session_factory() as session:
        yield session

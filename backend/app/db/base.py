"""
Базовый класс моделей.

Зачем отдельный Base с миксином TimestampMixin, а не просто `declarative_base()`
в каждом файле модели: created_at/updated_at нужны практически всем таблицам
в реальном проекте (аудит, сортировка "последние изменённые", отладка).
Вынос в миксин — DRY, и Alembic autogenerate увидит эти колонки одинаково
для всех таблиц.
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

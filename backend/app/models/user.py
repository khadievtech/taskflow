"""
Модель User.

Пароль хранится ТОЛЬКО в виде хеша — колонка называется hashed_password,
а не password, чтобы случайное `user.password = "..."` не прошло незамеченным
при чтении кода.
"""

import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # unique=True создаёт уникальный индекс — он же обслуживает поиск по email
    # при входе, поэтому отдельный индекс не нужен.
    email: Mapped[str] = mapped_column(String(320), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    # Флаг вместо удаления записи: удалять пользователя означает терять историю
    # и ломать ссылки. Отключённый пользователь не может войти, но остаётся
    # в базе.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

"""
Модель Task.

Почему статус — Python Enum, а не просто строка:
- на уровне БД это создаст PostgreSQL ENUM-тип — недопустимые значения
  ("in_progres" с опечаткой) отклонит сама база, а не только приложение
- в коде автодополнение IDE подскажет допустимые значения
- Alembic autogenerate корректно создаст/изменит enum-тип при миграции

Trade-off: изменение enum (добавление нового статуса) в Postgres требует
отдельной миграции с ALTER TYPE — чуть менее гибко, чем VARCHAR + CHECK,
но для набора статусов, который меняется редко (task workflow), строгая
типизация того стоит.
"""

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class TaskStatus(enum.StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    # UUID вместо auto-increment int: не раскрывает количество задач в системе
    # через порядковый номер в URL, и не конфликтует при будущем шардировании
    # или merge данных из разных окружений.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(2000), default=None)
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(
            TaskStatus,
            name="task_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=TaskStatus.TODO,
    )
    assignee: Mapped[str | None] = mapped_column(String(100), default=None)

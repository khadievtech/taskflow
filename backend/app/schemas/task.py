"""
Схемы Task.

Три отдельных класса, а не один — устоявшийся паттерн:
- TaskCreate:  что клиент отправляет при создании (нет id/timestamps — их
  назначает сервер, клиент не должен иметь возможность их подделать)
- TaskUpdate:  все поля опциональны — это PATCH-семантика, частичное
  обновление без необходимости присылать весь объект целиком
- TaskRead:    что сервер возвращает клиенту — включает id и timestamps

Если бы мы использовали одну схему для всего, пришлось бы либо делать все
поля в Create опциональными (клиент случайно может прислать id и подделать
чужую задачу), либо городить костыли. Разделение по direction (in/out) —
то, как это делают в реальных FastAPI-проектах.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    assignee: str | None = Field(default=None, max_length=100)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus | None = None
    assignee: str | None = Field(default=None, max_length=100)


class TaskRead(BaseModel):
    # from_attributes=True позволяет создавать схему прямо из ORM-объекта
    # (TaskRead.model_validate(task_orm_instance)), без ручного маппинга полей
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    status: TaskStatus
    assignee: str | None
    created_at: datetime
    updated_at: datetime

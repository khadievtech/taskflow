"""
Сервисный слой Task.

Почему логика не написана прямо в endpoint-функции: этот код должен уметь
вызываться не только из HTTP-роута, но и, например, из Kafka-консьюмера
(Phase 9) или из фонового job'а — без необходимости поднимать HTTP-стек
ради unit-теста. Роут — это тонкая обёртка, которая парсит HTTP-запрос и
вызывает сервис.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


async def create_task(session: AsyncSession, data: TaskCreate) -> Task:
    task = Task(**data.model_dump())
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def list_tasks(session: AsyncSession) -> list[Task]:
    result = await session.execute(select(Task).order_by(Task.created_at.desc()))
    return list(result.scalars().all())


async def get_task(session: AsyncSession, task_id: uuid.UUID) -> Task | None:
    return await session.get(Task, task_id)


async def update_task(session: AsyncSession, task: Task, data: TaskUpdate) -> Task:
    # exclude_unset=True — обновляем только те поля, что реально пришли в
    # запросе (PATCH-семантика). Без этого None из непереданных полей
    # затёр бы существующие значения в БД.
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await session.commit()
    await session.refresh(task)
    return task


async def delete_task(session: AsyncSession, task: Task) -> None:
    await session.delete(task)
    await session.commit()

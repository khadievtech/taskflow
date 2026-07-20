import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services import task_service

router = APIRouter(tags=["tasks"])


async def _get_task_or_404(
    task_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
) -> Task:
    task = await task_service.get_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate, session: AsyncSession = Depends(get_db_session)
) -> Task:
    return await task_service.create_task(session, data)


@router.get("", response_model=list[TaskRead])
async def list_tasks(session: AsyncSession = Depends(get_db_session)) -> list[Task]:
    return await task_service.list_tasks(session)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task: Task = Depends(_get_task_or_404)) -> Task:
    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    data: TaskUpdate,
    task: Task = Depends(_get_task_or_404),
    session: AsyncSession = Depends(get_db_session),
) -> Task:
    return await task_service.update_task(session, task, data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task: Task = Depends(_get_task_or_404),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await task_service.delete_task(session, task)

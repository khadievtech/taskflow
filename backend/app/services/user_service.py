"""Бизнес-логика работы с пользователями."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    # Приводим к нижнему регистру: адреса Example@Mail.com и example@mail.com
    # принадлежат одному человеку, и без нормализации он смог бы завести две
    # учётные записи, а потом не понять, под какой входит.
    result = await session.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await session.get(User, user_id)


async def create_user(session: AsyncSession, data: UserCreate) -> User:
    user = User(
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate(session: AsyncSession, email: str, password: str) -> User | None:
    """
    Проверяет пару email/пароль.

    Возвращает None и для несуществующего пользователя, и для неверного пароля,
    и для отключённой учётной записи — вызывающий код не должен различать эти
    случаи в ответе. Сообщение "такого пользователя нет" позволило бы перебором
    выяснить, кто зарегистрирован в системе (user enumeration).
    """
    user = await get_by_email(session, email)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

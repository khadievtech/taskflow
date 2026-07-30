from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ACCESS_TOKEN_COOKIE, get_current_user
from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.services import user_service

router = APIRouter(tags=["auth"])
settings = get_settings()


def _set_auth_cookie(response: Response, user: User) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=create_access_token(str(user.id)),
        httponly=True,
        # Lax, а не Strict: при Strict cookie не отправлялась бы даже при
        # переходе по ссылке с другого сайта, и пользователь видел бы себя
        # разлогиненным. Lax блокирует кросс-сайтовые POST — то есть основной
        # вектор CSRF — но сохраняет обычную навигацию.
        samesite="lax",
        # Пока TLS нет (Phase 5b), флаг выключен: с Secure браузер вообще не
        # отправлял бы cookie по HTTP, и вход не работал бы.
        secure=settings.cookie_secure,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    if not settings.allow_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Регистрация закрыта",
        )

    if await user_service.get_by_email(session, data.email) is not None:
        # 409 Conflict, а не 400: ресурс с таким идентификатором уже существует.
        #
        # Оговорка про приватность: этот ответ позволяет узнать, зарегистрирован
        # ли конкретный адрес (user enumeration). Полностью скрыть это можно
        # только подтверждением по почте — отвечать 201 всегда, а письмо
        # отправлять лишь новому адресу. Без почтового сервиса такой обмен
        # ухудшил бы удобство без реальной выгоды.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        )

    user = await user_service.create_user(session, data)
    _set_auth_cookie(response, user)
    return user


@router.post("/login", response_model=UserRead)
async def login(
    data: UserLogin,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    user = await user_service.authenticate(session, data.email, data.password)
    if user is None:
        # Одинаковый ответ для несуществующего пользователя, неверного пароля и
        # отключённой учётной записи — чтобы нельзя было перебором выяснить,
        # какие адреса зарегистрированы.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    _set_auth_cookie(response, user)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    # Удаление cookie — единственное, что можно сделать без серверного списка
    # отозванных токенов. Если токен уже украден, он останется валидным до
    # истечения срока: JWT по устройству не отзывается. Отзыв требует либо
    # хранения чёрного списка, либо коротких токенов с refresh-механизмом.
    response.delete_cookie(ACCESS_TOKEN_COOKIE, path="/")


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)) -> User:
    return user

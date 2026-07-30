"""
Зависимости аутентификации.

Токен передаётся в httpOnly cookie, а не в заголовке Authorization. Разбор
компромисса:

**localStorage + заголовок Authorization** — распространённый вариант, но токен
доступен JavaScript. Любая XSS-уязвимость (в том числе в сторонней библиотеке
из бандла) позволяет его прочитать и унести.

**httpOnly cookie** — браузер не даёт JavaScript доступ к содержимому, поэтому
XSS не приводит к краже токена. Взамен появляется риск CSRF: браузер сам
прикладывает cookie к запросам, в том числе инициированным другим сайтом.
Защита — атрибут SameSite=Lax, при котором cookie не отправляется в
кросс-сайтовых POST-запросах.

Выбран второй вариант, и обратный прокси из Phase 5a делает его особенно
удобным: фронтенд и API на одном origin, поэтому cookie работают без
настройки CORS с credentials.
"""

import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db_session
from app.models.user import User
from app.services import user_service

ACCESS_TOKEN_COOKIE = "taskflow_access_token"

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Требуется аутентификация",
)


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        raise _UNAUTHORIZED

    subject = decode_access_token(token)
    if subject is None:
        raise _UNAUTHORIZED

    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        raise _UNAUTHORIZED from None

    # Проверка в БД на каждом запросе, а не доверие содержимому токена:
    # подписанный токен подтверждает лишь, что мы его выдали. Если после
    # выдачи пользователя отключили, токен всё ещё валиден по подписи — и без
    # обращения к БД отключение не подействовало бы до истечения срока.
    #
    # Цена — один запрос к БД на каждый обращение. При росте нагрузки его
    # кэшируют (Redis), но кэш возвращает ту же проблему устаревших данных,
    # только с меньшим окном.
    user = await user_service.get_by_id(session, user_id)
    if user is None or not user.is_active:
        raise _UNAUTHORIZED

    return user

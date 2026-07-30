"""
Хеширование паролей и работа с JWT.

Про выбор библиотек — это область, где устаревшая рекомендация опасна:

**pwdlib с Argon2id вместо passlib.** Библиотека passlib до сих пор фигурирует
в официальной документации FastAPI, но она не поддерживается с 2020 года,
использует модуль `crypt`, удалённый из Python 3.13, и ломается на bcrypt 5.0.
На pwdlib перешёл fastapi-users начиная с версии 13.

Argon2id — рекомендация OWASP и победитель Password Hashing Competition.
Он memory-hard: подбор требует не только вычислений, но и памяти, что резко
удорожает атаку на GPU. У bcrypt есть неочевидная ловушка — он молча обрезает
пароль на 72 байтах, то есть длинные парольные фразы теряют часть энтропии.

**PyJWT вместо python-jose.** PyJWT развивается организацией pyca — той же,
что поддерживает `cryptography`. У python-jose давно нет релизов, а для
библиотеки, отвечающей за подпись токенов, это неприемлемо.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

settings = get_settings()

# PasswordHash.recommended() даёт Argon2id с параметрами, актуальными на момент
# выпуска библиотеки. Использовать рекомендованный набор, а не фиксировать
# параметры руками — осознанный выбор: рекомендации меняются вслед за
# производительностью железа, и обновление библиотеки подтянет их само.
_password_hash = PasswordHash.recommended()


def hash_password(plain: str) -> str:
    return _password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Проверка пароля.

    Возвращает False при любой ошибке разбора хеша, а не поднимает исключение:
    повреждённая или устаревшая запись в БД не должна приводить к 500 — с точки
    зрения пользователя это просто неверный пароль.
    """
    try:
        return _password_hash.verify(plain, hashed)
    except Exception:  # noqa: BLE001 — намеренно широкий catch, см. docstring
        return False


def create_access_token(subject: str) -> str:
    """
    Создаёт JWT.

    Claim `sub` (subject) — стандартное поле для идентификатора владельца
    токена, `exp` — момент истечения. PyJWT сам проверяет `exp` при разборе и
    поднимает ExpiredSignatureError, поэтому вручную сравнивать время не нужно.
    """
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    """
    Проверяет подпись и срок действия токена, возвращает значение `sub`.

    Важно: алгоритм передаётся списком явно. Если бы декодирование принимало
    любой алгоритм из заголовка токена, атакующий мог бы подставить `alg: none`
    или сменить алгоритм на симметричный и подписать токен публичным ключом —
    классическая уязвимость реализаций JWT.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError:
        return None

    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None

import uuid

import pytest
from httpx import AsyncClient

from app.api.deps import ACCESS_TOKEN_COOKIE
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def unique_email() -> str:
    return f"user-{uuid.uuid4()}@example.com"


# --- Хеширование паролей ---


def test_hash_is_not_the_plain_password() -> None:
    hashed = hash_password("super-secret-123")
    assert hashed != "super-secret-123"
    # Argon2id помечает свои хеши префиксом $argon2id$ — проверяем, что
    # используется именно рекомендованный OWASP вариант, а не argon2i или
    # неожиданно подставленный bcrypt.
    assert hashed.startswith("$argon2id$")


def test_same_password_gives_different_hashes() -> None:
    """
    Соль должна быть случайной. Одинаковые хеши для одного пароля означали бы,
    что по базе видно, у кого совпадают пароли, и что таблицы предвычисленных
    хешей (rainbow tables) применимы.
    """
    assert hash_password("same-password-1") != hash_password("same-password-1")


def test_verify_accepts_correct_and_rejects_wrong() -> None:
    hashed = hash_password("correct-password")
    assert verify_password("correct-password", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_verify_returns_false_on_malformed_hash() -> None:
    """Повреждённая запись в БД не должна приводить к 500."""
    assert verify_password("any-password", "not-a-valid-hash") is False


# --- JWT ---


def test_token_roundtrip_preserves_subject() -> None:
    subject = str(uuid.uuid4())
    assert decode_access_token(create_access_token(subject)) == subject


def test_tampered_token_is_rejected() -> None:
    """
    Тамперим ПРЕДпоследний символ подписи, а не последний — и это не
    произвольный выбор.

    HMAC-SHA256 даёт 32 байта, а base64 кодирует группами по 3 байта.
    32 не делится на 3 нацело (32 = 10*3 + 2), поэтому последняя группа
    base64 кодирует только 2 байта из возможных 3, и у последнего символа
    такой неполной группы есть 2 "лишних" бита выравнивания, которые по
    спецификации должны быть нулём, но декодер PyJWT их не проверяет и
    просто отбрасывает.

    Из-за этого замена ИМЕННО последнего символа токена иногда (в
    зависимости от того, какой символ там оказался у исходной подписи)
    декодируется в те же самые байты — тест был нестабильным (flaky):
    проходил или падал в зависимости от случайных данных токена.
    Проверено вычислением: символы 'a' и 'b' на последней позиции дают
    БАЙТ-В-БАЙТ идентичный результат декодирования, а на предпоследней —
    разный. Ни один символ, кроме самого последнего, такой неоднозначности
    не имеет — там любое изменение гарантированно меняет декодированные
    байты подписи.

    Важно: это не брешь в проверке JWT — decode_access_token отработал
    корректно и там, и там. Проблема была в способе, которым сам тест
    имитировал подделку.
    """
    token = create_access_token(str(uuid.uuid4()))
    tampered = token[:-2] + ("a" if token[-2] != "a" else "b") + token[-1]
    assert decode_access_token(tampered) is None


def test_garbage_token_is_rejected() -> None:
    assert decode_access_token("not.a.jwt") is None


# --- Регистрация и вход ---


async def test_register_returns_user_without_password_hash(client: AsyncClient) -> None:
    email = unique_email()
    response = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "test-password-123"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == email
    # Главная проверка: хеш пароля не должен попадать в ответ ни под каким
    # именем поля.
    assert "hashed_password" not in body
    assert "password" not in body


async def test_register_sets_httponly_cookie(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": unique_email(), "password": "test-password-123"},
    )
    assert ACCESS_TOKEN_COOKIE in response.cookies
    # httponly и samesite не видны через response.cookies, проверяем заголовок.
    set_cookie = response.headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie


async def test_email_is_normalised_to_lowercase(client: AsyncClient) -> None:
    local = f"MixedCase-{uuid.uuid4()}"
    await client.post(
        "/api/v1/auth/register",
        json={"email": f"{local}@Example.COM", "password": "test-password-123"},
    )
    # Вход тем же адресом в другом регистре должен сработать: иначе человек
    # заведёт вторую учётную запись и не поймёт, под какой входит.
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": f"{local.lower()}@example.com", "password": "test-password-123"},
    )
    assert response.status_code == 200


async def test_duplicate_email_returns_409(client: AsyncClient) -> None:
    email = unique_email()
    payload = {"email": email, "password": "test-password-123"}
    assert (await client.post("/api/v1/auth/register", json=payload)).status_code == 201
    assert (await client.post("/api/v1/auth/register", json=payload)).status_code == 409


@pytest.mark.parametrize("password", ["short", "1234567"])
async def test_short_password_is_rejected(client: AsyncClient, password: str) -> None:
    response = await client.post(
        "/api/v1/auth/register", json={"email": unique_email(), "password": password}
    )
    assert response.status_code == 422


async def test_invalid_email_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register", json={"email": "not-an-email", "password": "test-password-123"}
    )
    assert response.status_code == 422


async def test_login_with_wrong_password_returns_401(client: AsyncClient) -> None:
    email = unique_email()
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "test-password-123"}
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong-password"}
    )
    assert response.status_code == 401


async def test_login_for_unknown_user_gives_same_error_as_wrong_password(
    client: AsyncClient,
) -> None:
    """
    Одинаковый ответ в обоих случаях не даёт перебором выяснить, какие адреса
    зарегистрированы (user enumeration).
    """
    email = unique_email()
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "test-password-123"}
    )

    wrong_password = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong-password"}
    )
    unknown_user = await client.post(
        "/api/v1/auth/login", json={"email": unique_email(), "password": "test-password-123"}
    )

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json()["detail"] == unknown_user.json()["detail"]


# --- Текущий пользователь и выход ---


async def test_me_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_me_returns_current_user(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert "@example.com" in response.json()["email"]


async def test_logout_clears_cookie_and_revokes_access(auth_client: AsyncClient) -> None:
    assert (await auth_client.post("/api/v1/auth/logout")).status_code == 204
    assert (await auth_client.get("/api/v1/auth/me")).status_code == 401


async def test_forged_cookie_is_rejected(client: AsyncClient) -> None:
    """Подписанный не нашим ключом токен не должен приниматься."""
    client.cookies.set(ACCESS_TOKEN_COOKIE, "fake-token-value")
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_token_for_nonexistent_user_is_rejected(client: AsyncClient) -> None:
    """
    Токен с корректной подписью, но ссылающийся на удалённого пользователя.
    Проверяет, что зависимость обращается к БД, а не доверяет содержимому
    токена — иначе отключение пользователя не действовало бы до истечения срока.
    """
    client.cookies.set(ACCESS_TOKEN_COOKIE, create_access_token(str(uuid.uuid4())))
    assert (await client.get("/api/v1/auth/me")).status_code == 401


# --- Защита задач ---


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/v1/tasks"),
        ("post", "/api/v1/tasks"),
        ("get", "/api/v1/tasks/00000000-0000-0000-0000-000000000000"),
        ("patch", "/api/v1/tasks/00000000-0000-0000-0000-000000000000"),
        ("delete", "/api/v1/tasks/00000000-0000-0000-0000-000000000000"),
    ],
)
async def test_task_endpoints_require_authentication(
    client: AsyncClient, method: str, path: str
) -> None:
    """
    Все методы задач закрыты. Защита объявлена на уровне роутера, поэтому новый
    эндпоинт нельзя случайно оставить открытым — но тест фиксирует это как
    требование, а не как деталь реализации.
    """
    # client.request(...) вместо getattr(client, method): в httpx у get и
    # delete нет параметра json, а универсальный request принимает его для
    # любого метода.
    kwargs = {"json": {}} if method in {"post", "patch"} else {}
    response = await client.request(method.upper(), path, **kwargs)
    assert response.status_code == 401


async def test_health_endpoints_stay_public(client: AsyncClient) -> None:
    """
    Health-check должен оставаться доступным без аутентификации: его опрашивают
    Docker и Kubernetes, у которых нет учётных данных.
    """
    assert (await client.get("/api/v1/health/live")).status_code == 200
    assert (await client.get("/api/v1/health/ready")).status_code == 200

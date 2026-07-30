"""
Общие фикстуры для всех тестов.

pytest автоматически подхватывает conftest.py и делает его фикстуры видимыми
во всех тестовых файлах в этой директории и поддиректориях — не нужно
импортировать их вручную в каждом test_*.py.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Клиент без аутентификации — для проверки, что защита действительно есть."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_client():
    """
    Клиент с выполненным входом.

    Регистрация сама выставляет httpOnly cookie, а AsyncClient хранит cookie
    между запросами — поэтому дополнительный вызов /login не нужен.

    Email уникален на каждый тест: тесты делят одну БД (пункт 2 реестра
    техдолга), и фиксированный адрес приводил бы к конфликту уникального
    ограничения на втором тесте.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/register",
            json={"email": f"user-{uuid.uuid4()}@example.com", "password": "test-password-123"},
        )
        assert response.status_code == 201, response.text
        yield ac

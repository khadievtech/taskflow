"""
Общие фикстуры для всех тестов.

pytest автоматически подхватывает conftest.py и делает его фикстуры видимыми
во всех тестовых файлах в этой директории и поддиректориях — не нужно
импортировать `client` вручную в каждом test_*.py.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

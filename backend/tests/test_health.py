from httpx import AsyncClient


async def test_liveness(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readiness(client: AsyncClient) -> None:
    # Требует реальный Postgres, доступный по DATABASE_URL из .env/окружения.
    # В CI (Phase 2) это будет сервис-контейнер postgres в GitHub Actions.
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200


async def test_root(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()

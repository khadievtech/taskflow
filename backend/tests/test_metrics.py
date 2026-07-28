from httpx import AsyncClient


async def test_metrics_endpoint_available(client: AsyncClient) -> None:
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


async def test_metrics_track_requests_with_status_label(client: AsyncClient) -> None:
    await client.get("/api/v1/health/live")

    response = await client.get("/metrics")
    body = response.text

    # Проверяем, что коды ответа НЕ сгруппированы в "2xx" —
    # should_group_status_codes=False должен давать точный код.
    assert 'status="200"' in body
    assert 'status="2xx"' not in body


async def test_metrics_use_path_template_not_raw_path(client: AsyncClient) -> None:
    """
    Критично для кардинальности: путь с параметром должен попадать в метрики
    как шаблон /api/v1/tasks/{task_id}, а не как конкретный UUID. Иначе каждая
    задача создавала бы новый временной ряд, и Prometheus со временем
    захлебнулся бы — классическая ошибка cardinality explosion.
    """
    task_id = "11111111-1111-1111-1111-111111111111"
    await client.get(f"/api/v1/tasks/{task_id}")

    body = (await client.get("/metrics")).text

    assert "/api/v1/tasks/{task_id}" in body
    assert task_id not in body

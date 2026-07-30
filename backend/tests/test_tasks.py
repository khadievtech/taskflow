from httpx import AsyncClient


async def test_create_and_get_task(auth_client: AsyncClient) -> None:
    response = await auth_client.post("/api/v1/tasks", json={"title": "Write tests"})
    assert response.status_code == 201
    created = response.json()
    assert created["title"] == "Write tests"
    assert created["status"] == "todo"

    get_response = await auth_client.get(f"/api/v1/tasks/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]


async def test_list_tasks(auth_client: AsyncClient) -> None:
    await auth_client.post("/api/v1/tasks", json={"title": "Task A"})
    await auth_client.post("/api/v1/tasks", json={"title": "Task B"})

    response = await auth_client.get("/api/v1/tasks")
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert "Task A" in titles
    assert "Task B" in titles


async def test_update_task_status(auth_client: AsyncClient) -> None:
    created = (await auth_client.post("/api/v1/tasks", json={"title": "To be updated"})).json()

    response = await auth_client.patch(
        f"/api/v1/tasks/{created['id']}", json={"status": "in_progress"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
    # title не передавали в PATCH — должен остаться прежним (частичное обновление)
    assert response.json()["title"] == "To be updated"


async def test_delete_task(auth_client: AsyncClient) -> None:
    created = (await auth_client.post("/api/v1/tasks", json={"title": "To be deleted"})).json()

    delete_response = await auth_client.delete(f"/api/v1/tasks/{created['id']}")
    assert delete_response.status_code == 204

    get_response = await auth_client.get(f"/api/v1/tasks/{created['id']}")
    assert get_response.status_code == 404


async def test_get_nonexistent_task_returns_404(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/tasks/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

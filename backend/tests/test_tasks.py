def _register_and_login(client, username="alice", password="secret123"):
    client.post("/api/auth/register", json={"username": username, "password": password})
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    return resp.cookies["token"]


def test_create_task(client):
    token = _register_and_login(client)
    resp = client.post("/api/tasks", json={
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "quality": "1080p",
    }, cookies={"token": token})
    assert resp.status_code == 201
    data = resp.json()
    assert data["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert data["quality"] == "1080p"
    assert data["status"] == "pending"
    assert data["id"] is not None


def test_list_tasks(client):
    token = _register_and_login(client)
    for url in ["https://example.com/1", "https://example.com/2"]:
        client.post("/api/tasks", json={"url": url}, cookies={"token": token})

    resp = client.get("/api/tasks", cookies={"token": token})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_filter_tasks_by_status(client):
    token = _register_and_login(client)
    client.post("/api/tasks", json={"url": "https://example.com/1"}, cookies={"token": token})
    client.post("/api/tasks", json={"url": "https://example.com/2"}, cookies={"token": token})

    resp = client.get("/api/tasks?status=pending", cookies={"token": token})
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = client.get("/api/tasks?status=completed", cookies={"token": token})
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_delete_task(client):
    token = _register_and_login(client)
    resp = client.post("/api/tasks", json={"url": "https://example.com/1"}, cookies={"token": token})
    task_id = resp.json()["id"]

    resp = client.delete(f"/api/tasks/{task_id}", cookies={"token": token})
    assert resp.status_code == 200

    resp = client.get("/api/tasks", cookies={"token": token})
    assert len(resp.json()) == 0


def test_task_isolation_between_users(client):
    token1 = _register_and_login(client, "alice")
    token2 = _register_and_login(client, "bob")

    client.post("/api/tasks", json={"url": "https://alice.com/1"}, cookies={"token": token1})
    resp = client.get("/api/tasks", cookies={"token": token2})
    assert len(resp.json()) == 0

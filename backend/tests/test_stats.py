def _register_and_login(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "secret123"})
    resp = client.post("/api/auth/login", json={"username": "alice", "password": "secret123"})
    return resp.cookies["token"]


def test_stats_returns_counts(client):
    token = _register_and_login(client)
    resp = client.get("/api/stats", cookies={"token": token})
    assert resp.status_code == 200
    data = resp.json()
    assert "disk_free_bytes" in data
    assert "tasks_pending" in data
    assert "tasks_downloading" in data
    assert "tasks_completed" in data
    assert "tasks_failed" in data
    assert "videos_count" in data
    assert all(isinstance(data[k], int) for k in data)

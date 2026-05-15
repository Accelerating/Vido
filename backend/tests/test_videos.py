def _register_and_login(client, username="alice", password="secret123"):
    client.post("/api/auth/register", json={"username": username, "password": password})
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    return resp.cookies["token"]


def test_list_videos_empty(client):
    token = _register_and_login(client)
    resp = client.get("/api/videos", cookies={"token": token})
    assert resp.status_code == 200
    assert resp.json() == []


def test_video_access_requires_auth(client):
    resp = client.get("/api/videos")
    assert resp.status_code == 401

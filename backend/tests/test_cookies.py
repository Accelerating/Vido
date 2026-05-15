def _register_and_login(client, username="alice", password="secret123"):
    client.post("/api/auth/register", json={"username": username, "password": password})
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    return resp.cookies["token"]


def test_create_cookie_profile(client):
    token = _register_and_login(client)
    resp = client.post("/api/cookies", json={
        "site": "youtube",
        "source_type": "paste",
        "cookie_content": "Netscape HTTP Cookie File ..."
    }, cookies={"token": token})
    assert resp.status_code == 201
    data = resp.json()
    assert data["site"] == "youtube"
    assert data["source_type"] == "paste"
    assert "id" in data


def test_list_cookie_profiles(client):
    token = _register_and_login(client)
    client.post("/api/cookies", json={
        "site": "youtube", "source_type": "paste",
        "cookie_content": "c1"
    }, cookies={"token": token})
    client.post("/api/cookies", json={
        "site": "bilibili", "source_type": "file_upload",
        "cookie_content": "c2"
    }, cookies={"token": token})

    resp = client.get("/api/cookies", cookies={"token": token})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["site"] == "youtube"
    assert "cookie_content" not in str(data)  # never expose raw cookie data in list


def test_delete_cookie_profile(client):
    token = _register_and_login(client)
    resp = client.post("/api/cookies", json={
        "site": "youtube", "source_type": "paste",
        "cookie_content": "c1"
    }, cookies={"token": token})
    cid = resp.json()["id"]

    resp = client.delete(f"/api/cookies/{cid}", cookies={"token": token})
    assert resp.status_code == 200

    resp = client.get("/api/cookies", cookies={"token": token})
    assert len(resp.json()) == 0


def test_cookie_isolation_between_users(client):
    token1 = _register_and_login(client, "alice")
    token2 = _register_and_login(client, "bob")

    client.post("/api/cookies", json={
        "site": "youtube", "source_type": "paste",
        "cookie_content": "alice_cookie"
    }, cookies={"token": token1})

    resp = client.get("/api/cookies", cookies={"token": token2})
    assert len(resp.json()) == 0


def test_cookie_update(client):
    token = _register_and_login(client)
    resp = client.post("/api/cookies", json={
        "site": "youtube", "source_type": "paste",
        "cookie_content": "old"
    }, cookies={"token": token})
    cid = resp.json()["id"]

    resp = client.put(f"/api/cookies/{cid}", json={
        "cookie_content": "new"
    }, cookies={"token": token})
    assert resp.status_code == 200
    assert resp.json()["site"] == "youtube"  # unchanged

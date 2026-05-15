def test_register_creates_user(client):
    resp = client.post("/api/auth/register", json={
        "username": "alice",
        "password": "secret123"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alice"
    assert "password" not in str(data)


def test_register_rejects_duplicate_username(client):
    client.post("/api/auth/register", json={
        "username": "bob", "password": "pass1234"
    })
    resp = client.post("/api/auth/register", json={
        "username": "bob", "password": "other5678"
    })
    assert resp.status_code == 409


def test_register_validates_input(client):
    resp = client.post("/api/auth/register", json={
        "username": "a", "password": "123"
    })
    assert resp.status_code == 422


def test_login_sets_cookie_and_returns_user(client):
    client.post("/api/auth/register", json={
        "username": "alice", "password": "secret123"
    })
    resp = client.post("/api/auth/login", json={
        "username": "alice", "password": "secret123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "alice"
    assert "token" in resp.cookies
    assert resp.cookies["token"] != ""


def test_login_rejects_wrong_password(client):
    client.post("/api/auth/register", json={
        "username": "alice", "password": "secret123"
    })
    resp = client.post("/api/auth/login", json={
        "username": "alice", "password": "wrong"
    })
    assert resp.status_code == 401


def test_login_rejects_nonexistent_user(client):
    resp = client.post("/api/auth/login", json={
        "username": "ghost", "password": "whatever"
    })
    assert resp.status_code == 401


def test_protected_route_requires_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_protected_route_accepts_valid_token(client):
    client.post("/api/auth/register", json={
        "username": "alice", "password": "secret123"
    })
    login_resp = client.post("/api/auth/login", json={
        "username": "alice", "password": "secret123"
    })
    token = login_resp.cookies["token"]
    resp = client.get("/api/auth/me", cookies={"token": token})
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


def test_protected_route_rejects_invalid_token(client):
    resp = client.get("/api/auth/me", cookies={"token": "bad-token"})
    assert resp.status_code == 401


def test_logout_clears_cookie_and_deletes_token(client):
    client.post("/api/auth/register", json={
        "username": "alice", "password": "secret123"
    })
    login_resp = client.post("/api/auth/login", json={
        "username": "alice", "password": "secret123"
    })
    token = login_resp.cookies["token"]

    resp = client.post("/api/auth/logout", cookies={"token": token})
    assert resp.status_code == 200

    # Cookie should be cleared
    cookies = resp.headers.get("set-cookie", "")
    assert 'token="";' in cookies or "token=;" in cookies or 'Max-Age=0' in cookies

    # Token should no longer work
    resp2 = client.get("/api/auth/me", cookies={"token": token})
    assert resp2.status_code == 401

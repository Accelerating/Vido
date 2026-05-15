import time
import uuid
from typing import Annotated, Optional

import bcrypt as _bcrypt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from app.database import get_db
from app.models import LoginRequest, RegisterRequest, UserResponse

router = APIRouter()

# In-memory rate limiting
_login_attempts: dict[str, list[float]] = {}  # {ip: [timestamps]}
_locked_until: dict[str, float] = {}  # {ip: lockout_end_timestamp}


def get_current_user(token: Annotated[Optional[str], Cookie()] = None):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    db = get_db()
    row = db.execute(
        "SELECT u.id, u.username, u.created_at, u.is_admin "
        "FROM auth_tokens t JOIN users u ON t.user_id = u.id "
        "WHERE t.token = ?",
        (token,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = dict(row)
    result["_token"] = token
    return result


CurrentUser = Annotated[dict, Depends(get_current_user)]


def require_admin(user: CurrentUser):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


CurrentAdminUser = Annotated[dict, Depends(require_admin)]


@router.post("/api/auth/register", status_code=201)
def register(req: RegisterRequest, response: Response):
    db = get_db()

    # Only allow public registration when no users exist yet
    user_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_count > 0:
        response.status_code = 403
        return {"detail": "Registration closed"}

    existing = db.execute(
        "SELECT id FROM users WHERE username = ?", (req.username,)
    ).fetchone()
    if existing:
        response.status_code = 409
        return {"detail": "Username already taken"}

    password_hash = _bcrypt.hashpw(req.password.encode(), _bcrypt.gensalt()).decode()
    cursor = db.execute(
        "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)",
        (req.username, password_hash),
    )
    user_id = cursor.lastrowid

    token = str(uuid.uuid4())
    db.execute(
        "INSERT INTO auth_tokens (user_id, token) VALUES (?, ?)",
        (user_id, token),
    )
    db.commit()

    user = db.execute(
        "SELECT id, username, created_at, is_admin FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()

    from fastapi.responses import JSONResponse
    r = JSONResponse(
        content={
            "id": user["id"],
            "username": user["username"],
            "created_at": str(user["created_at"]),
            "is_admin": bool(user["is_admin"]),
        },
        status_code=201,
    )
    r.set_cookie(
        key="token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400 * 30,
    )
    return r


@router.post("/api/auth/login")
def login(req: LoginRequest, request: Request, response: Response):
    db = get_db()
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    # Clean up expired lockouts
    if client_ip in _locked_until and now >= _locked_until[client_ip]:
        del _locked_until[client_ip]
        _login_attempts.pop(client_ip, None)

    # Check if currently locked out
    if client_ip in _locked_until and now < _locked_until[client_ip]:
        response.status_code = 429
        return {"detail": "Invalid username or password"}

    # Purge old attempts and count recent failures (last 10 min)
    attempts = [t for t in _login_attempts.get(client_ip, []) if now - t < 600]
    _login_attempts[client_ip] = attempts

    if len(attempts) >= 5:
        _locked_until[client_ip] = now + 3600
        response.status_code = 429
        return {"detail": "Invalid username or password"}

    user = db.execute(
        "SELECT id, username, password_hash, created_at, is_admin FROM users WHERE username = ?",
        (req.username,),
    ).fetchone()

    if not user or not _bcrypt.checkpw(
        req.password.encode(), user["password_hash"].encode()
    ):
        _login_attempts.setdefault(client_ip, []).append(now)
        response.status_code = 401
        return {"detail": "Invalid username or password"}

    token = str(uuid.uuid4())
    db.execute(
        "INSERT INTO auth_tokens (user_id, token) VALUES (?, ?)",
        (user["id"], token),
    )
    db.commit()

    resp_data = {
        "id": user["id"],
        "username": user["username"],
        "created_at": str(user["created_at"]),
        "is_admin": bool(user["is_admin"]),
    }
    from fastapi.responses import JSONResponse
    r = JSONResponse(content=resp_data)
    r.set_cookie(
        key="token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400 * 30,  # 30 days
    )
    return r


@router.get("/api/auth/me")
def me(user: CurrentUser):
    return {
        "id": user["id"],
        "username": user["username"],
        "created_at": str(user["created_at"]),
        "is_admin": bool(user["is_admin"]),
    }


@router.post("/api/auth/logout")
def logout(user: CurrentUser):
    db = get_db()
    db.execute("DELETE FROM auth_tokens WHERE token = ?", (user["_token"],))
    db.commit()

    from fastapi.responses import JSONResponse
    r = JSONResponse(content={"detail": "Logged out"})
    r.delete_cookie(key="token")
    return r


@router.get("/api/auth/can-register")
def can_register():
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    return {"can_register": count == 0}

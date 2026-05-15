import bcrypt as _bcrypt
from fastapi import APIRouter, Response
from app.auth import CurrentAdminUser
from app.database import get_db
from app.models import UserCreateRequest, UserUpdateRequest

router = APIRouter()


@router.get("/api/users")
def list_users(admin: CurrentAdminUser):
    db = get_db()
    rows = db.execute(
        "SELECT id, username, is_admin, created_at FROM users ORDER BY id"
    ).fetchall()
    return [
        {
            "id": r["id"],
            "username": r["username"],
            "is_admin": bool(r["is_admin"]),
            "created_at": str(r["created_at"]),
        }
        for r in rows
    ]


@router.post("/api/users", status_code=201)
def create_user(req: UserCreateRequest, admin: CurrentAdminUser):
    db = get_db()
    existing = db.execute(
        "SELECT id FROM users WHERE username = ?", (req.username,)
    ).fetchone()
    if existing:
        return Response(status_code=409, content='{"detail":"Username already taken"}')

    password_hash = _bcrypt.hashpw(req.password.encode(), _bcrypt.gensalt()).decode()
    cursor = db.execute(
        "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
        (req.username, password_hash, int(req.is_admin)),
    )
    db.commit()

    user = db.execute(
        "SELECT id, username, is_admin, created_at FROM users WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return {
        "id": user["id"],
        "username": user["username"],
        "is_admin": bool(user["is_admin"]),
        "created_at": str(user["created_at"]),
    }


@router.put("/api/users/{user_id}")
def update_user(user_id: int, req: UserUpdateRequest, admin: CurrentAdminUser):
    db = get_db()
    row = db.execute(
        "SELECT id, username, is_admin FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if not row:
        return Response(status_code=404, content='{"detail":"Not found"}')

    if req.username is not None:
        dup = db.execute(
            "SELECT id FROM users WHERE username = ? AND id != ?",
            (req.username, user_id),
        ).fetchone()
        if dup:
            return Response(status_code=409, content='{"detail":"Username already taken"}')
        db.execute("UPDATE users SET username = ? WHERE id = ?", (req.username, user_id))

    if req.password is not None and req.password != "":
        password_hash = _bcrypt.hashpw(req.password.encode(), _bcrypt.gensalt()).decode()
        db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))

    if req.is_admin is not None:
        db.execute("UPDATE users SET is_admin = ? WHERE id = ?", (int(req.is_admin), user_id))

    db.commit()

    user = db.execute(
        "SELECT id, username, is_admin, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    return {
        "id": user["id"],
        "username": user["username"],
        "is_admin": bool(user["is_admin"]),
        "created_at": str(user["created_at"]),
    }


@router.delete("/api/users/{user_id}")
def delete_user(user_id: int, admin: CurrentAdminUser):
    if user_id == admin["id"]:
        return Response(status_code=400, content='{"detail":"Cannot delete yourself"}')

    db = get_db()
    row = db.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        return Response(status_code=404, content='{"detail":"Not found"}')

    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    return {"detail": "Deleted"}

import os

from fastapi import APIRouter, Response

from app.auth import CurrentUser
from app.database import get_db
from app.config import COOKIES_DIR
from app.models import CookieCreateRequest, CookieUpdateRequest

router = APIRouter()


def _user_cookie_path(user_id: int, profile_id: int) -> str:
    d = os.path.join(COOKIES_DIR, str(user_id))
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{profile_id}.txt")


@router.post("/api/cookies", status_code=201)
def create_cookie(req: CookieCreateRequest, user: CurrentUser):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO cookie_profiles (user_id, site, cookie_data, source_type) "
        "VALUES (?, ?, ?, ?)",
        (user["id"], req.site, "", req.source_type),
    )
    profile_id = cursor.lastrowid

    cookie_path = _user_cookie_path(user["id"], profile_id)
    with open(cookie_path, "w") as f:
        f.write(req.cookie_content)

    db.execute(
        "UPDATE cookie_profiles SET cookie_data = ? WHERE id = ?",
        (cookie_path, profile_id),
    )
    db.commit()

    row = db.execute(
        "SELECT id, site, source_type, created_at, updated_at "
        "FROM cookie_profiles WHERE id = ?",
        (profile_id,),
    ).fetchone()
    return {
        "id": row["id"],
        "site": row["site"],
        "source_type": row["source_type"],
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
    }


@router.get("/api/cookies")
def list_cookies(user: CurrentUser):
    db = get_db()
    rows = db.execute(
        "SELECT id, site, source_type, created_at, updated_at "
        "FROM cookie_profiles WHERE user_id = ? ORDER BY created_at DESC",
        (user["id"],),
    ).fetchall()
    return [
        {
            "id": r["id"],
            "site": r["site"],
            "source_type": r["source_type"],
            "created_at": str(r["created_at"]),
            "updated_at": str(r["updated_at"]),
        }
        for r in rows
    ]


@router.put("/api/cookies/{cookie_id}")
def update_cookie(cookie_id: int, req: CookieUpdateRequest, user: CurrentUser):
    db = get_db()
    row = db.execute(
        "SELECT id, user_id, cookie_data FROM cookie_profiles WHERE id = ?",
        (cookie_id,),
    ).fetchone()
    if not row or row["user_id"] != user["id"]:
        return Response(status_code=404, content='{"detail":"Not found"}')

    if req.site is not None:
        db.execute(
            "UPDATE cookie_profiles SET site = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (req.site, cookie_id),
        )
    if req.cookie_content is not None:
        cookie_path = row["cookie_data"] or _user_cookie_path(user["id"], cookie_id)
        with open(cookie_path, "w") as f:
            f.write(req.cookie_content)
        if not row["cookie_data"]:
            db.execute(
                "UPDATE cookie_profiles SET cookie_data = ? WHERE id = ?",
                (cookie_path, cookie_id),
            )
        db.execute(
            "UPDATE cookie_profiles SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (cookie_id,),
        )
    db.commit()

    row = db.execute(
        "SELECT id, site, source_type, created_at, updated_at "
        "FROM cookie_profiles WHERE id = ?",
        (cookie_id,),
    ).fetchone()
    return {
        "id": row["id"],
        "site": row["site"],
        "source_type": row["source_type"],
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
    }


@router.delete("/api/cookies/{cookie_id}")
def delete_cookie(cookie_id: int, user: CurrentUser):
    db = get_db()
    row = db.execute(
        "SELECT id, user_id, cookie_data FROM cookie_profiles WHERE id = ?",
        (cookie_id,),
    ).fetchone()
    if not row or row["user_id"] != user["id"]:
        return Response(status_code=404, content='{"detail":"Not found"}')

    if row["cookie_data"] and os.path.exists(row["cookie_data"]):
        os.remove(row["cookie_data"])

    db.execute("DELETE FROM cookie_profiles WHERE id = ?", (cookie_id,))
    db.commit()
    return {"detail": "Deleted"}

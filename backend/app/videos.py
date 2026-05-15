import os
from fastapi import APIRouter, Response
from fastapi.responses import FileResponse
from app.auth import CurrentUser
from app.database import get_db

router = APIRouter()


@router.get("/api/videos")
def list_videos(user: CurrentUser):
    db = get_db()
    rows = db.execute(
        """
        SELECT v.* FROM video_files v
        JOIN download_tasks t ON v.task_id = t.id
        WHERE t.user_id = ?
        ORDER BY v.created_at DESC
        """,
        (user["id"],),
    ).fetchall()
    return [
        {
            "id": r["id"],
            "task_id": r["task_id"],
            "title": r["title"],
            "file_path": r["file_path"],
            "file_size": r["file_size"],
            "duration": r["duration"],
            "has_thumbnail": bool(r["thumbnail_path"] and os.path.exists(r["thumbnail_path"])),
            "created_at": str(r["created_at"]),
        }
        for r in rows
    ]


@router.get("/api/videos/{video_id}")
def get_video(video_id: int, user: CurrentUser):
    db = get_db()
    row = db.execute(
        """
        SELECT v.* FROM video_files v
        JOIN download_tasks t ON v.task_id = t.id
        WHERE v.id = ? AND t.user_id = ?
        """,
        (video_id, user["id"]),
    ).fetchone()
    if not row:
        return Response(status_code=404, content='{"detail":"Not found"}')
    return {
        "id": row["id"],
        "task_id": row["task_id"],
        "title": row["title"],
        "file_path": row["file_path"],
        "file_size": row["file_size"],
        "duration": row["duration"],
        "has_thumbnail": bool(row["thumbnail_path"] and os.path.exists(row["thumbnail_path"])),
        "created_at": str(row["created_at"]),
    }


@router.get("/api/videos/{video_id}/stream")
def stream_video(video_id: int, user: CurrentUser):
    db = get_db()
    row = db.execute(
        """
        SELECT v.file_path FROM video_files v
        JOIN download_tasks t ON v.task_id = t.id
        WHERE v.id = ? AND t.user_id = ?
        """,
        (video_id, user["id"]),
    ).fetchone()
    if not row or not os.path.exists(row["file_path"]):
        return Response(status_code=404, content='{"detail":"Not found"}')

    file_path = row["file_path"]
    filename = os.path.basename(file_path)
    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=filename,
        headers={"Accept-Ranges": "bytes"},
    )


@router.get("/api/videos/{video_id}/thumbnail")
def get_thumbnail(video_id: int, user: CurrentUser):
    db = get_db()
    row = db.execute(
        """
        SELECT v.thumbnail_path FROM video_files v
        JOIN download_tasks t ON v.task_id = t.id
        WHERE v.id = ? AND t.user_id = ?
        """,
        (video_id, user["id"]),
    ).fetchone()
    if not row or not row["thumbnail_path"] or not os.path.exists(row["thumbnail_path"]):
        return Response(status_code=404, content='{"detail":"Not found"}')

    return FileResponse(row["thumbnail_path"], media_type="image/jpeg")

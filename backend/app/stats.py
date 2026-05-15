import shutil
from fastapi import APIRouter
from app.auth import CurrentUser
from app.database import get_db
from app.config import DOWNLOADS_DIR

router = APIRouter()


@router.get("/api/stats")
def get_stats(user: CurrentUser):
    db = get_db()

    counts = {}
    for status in ("pending", "downloading", "completed", "failed"):
        row = db.execute(
            "SELECT COUNT(*) as cnt FROM download_tasks WHERE user_id = ? AND status = ?",
            (user["id"], status),
        ).fetchone()
        counts[f"tasks_{status}"] = row["cnt"]

    vids = db.execute(
        "SELECT COUNT(*) as cnt FROM video_files v "
        "JOIN download_tasks t ON v.task_id = t.id WHERE t.user_id = ?",
        (user["id"],),
    ).fetchone()

    disk = shutil.disk_usage(DOWNLOADS_DIR)

    return {
        "disk_free_bytes": disk.free,
        "disk_total_bytes": disk.total,
        "tasks_pending": counts["tasks_pending"],
        "tasks_downloading": counts["tasks_downloading"],
        "tasks_completed": counts["tasks_completed"],
        "tasks_failed": counts["tasks_failed"],
        "videos_count": vids["cnt"],
    }

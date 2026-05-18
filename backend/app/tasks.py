import asyncio
import os
import re
import shutil
import sys
from fastapi import APIRouter, Response
from app.auth import CurrentUser
from app.database import get_db
from app.models import TaskCreateRequest, ListFormatsRequest
from app.config import DOWNLOADS_DIR, LOGS_DIR

router = APIRouter()


def _ytdlp_path() -> str:
    venv_bin = os.path.join(sys.prefix, "bin", "yt-dlp")
    if os.path.exists(venv_bin):
        return venv_bin
    found = shutil.which("yt-dlp")
    return found or "yt-dlp"


def _detect_site(url: str) -> str:
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    if "bilibili.com" in url:
        return "bilibili"
    return "other"


def _read_log(log_path: str) -> str:
    if log_path and os.path.exists(log_path):
        with open(log_path, errors="replace") as f:
            return f.read()
    return ""


def _row_to_task(row) -> dict:
    return {
        "id": row["id"],
        "url": row["url"],
        "site": row["site"],
        "quality": row["quality"],
        "format": row["format"],
        "format_desc": row["format_desc"] if "format_desc" in row.keys() else None,
        "cookie_profile_id": row["cookie_profile_id"],
        "status": row["status"],
        "title": row["title"],
        "file_path": row["file_path"],
        "error_message": row["error_message"],
        "log": _read_log(row["log"]) if row["log"] else None,
        "created_at": str(row["created_at"]),
        "finished_at": str(row["finished_at"]) if row["finished_at"] else None,
    }


@router.post("/api/tasks/formats")
async def list_formats(req: ListFormatsRequest, user: CurrentUser):
    cmd = [_ytdlp_path(), "--js-runtimes", "node", "--remote-components", "ejs:github", "--list-formats", req.url]

    if req.cookie_profile_id:
        db = get_db()
        cookie_row = db.execute(
            "SELECT cookie_data FROM cookie_profiles WHERE id = ? AND user_id = ?",
            (req.cookie_profile_id, user["id"]),
        ).fetchone()
        if cookie_row and cookie_row["cookie_data"] and os.path.exists(cookie_row["cookie_data"]):
            cmd.extend(["--cookies", cookie_row["cookie_data"]])

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        error = stderr.decode(errors="replace")[:500]
        return Response(
            status_code=400,
            content='{"detail":"' + error.replace('"', "'") + '"}',
        )

    output = stdout.decode(errors="replace")
    formats = _parse_formats(output)
    if not formats:
        return Response(
            status_code=400,
            content='{"detail":"Could not parse any formats from output"}',
        )
    return formats


def _parse_formats(output: str) -> list[dict]:
    formats = []
    in_table = False

    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "ID" in stripped and "EXT" in stripped and "RESOLUTION" in stripped:
            in_table = True
            continue
        if not in_table:
            continue
        if stripped in ("Video only", "Audio only") or stripped.startswith("--"):
            continue

        parts = stripped.split()
        if len(parts) < 3:
            continue

        code = parts[0]
        if not re.match(r"^[\d]+[\-\+]?", code):
            continue

        after_last_pipe = stripped.rsplit("|", 1)[-1] if "|" in stripped else ""
        alp_parts = after_last_pipe.split()
        if len(alp_parts) >= 3 and alp_parts[1] == "video" and alp_parts[2] == "only":
            vcodec = alp_parts[0]
            acodec = "video only"
        elif len(alp_parts) >= 2 and alp_parts[0] == "audio" and alp_parts[1] == "only":
            vcodec = "audio only"
            acodec = alp_parts[2] if len(alp_parts) > 2 else "audio only"
        elif len(alp_parts) >= 2:
            vcodec = alp_parts[0]
            acodec = alp_parts[1]
        else:
            vcodec = alp_parts[0] if alp_parts else ""
            acodec = ""

        fps = None
        if len(parts) > 3 and re.match(r"^\d+$", parts[3]):
            fps = parts[3]

        note = ""
        raw = after_last_pipe.strip()
        raw_parts = raw.split(None, 1)
        if raw_parts and raw_parts[0] in ("video", "audio"):
            note = " ".join(raw_parts[2:]) if len(raw_parts) > 2 else ""
        elif raw_parts:
            note = " ".join(raw_parts[2:]) if len(raw_parts) > 2 else ""

        formats.append({
            "code": code,
            "ext": parts[1] if len(parts) > 1 else "",
            "resolution": parts[2] if len(parts) > 2 else "",
            "fps": fps,
            "file_size": parts[5] if len(parts) > 5 and "|" in stripped else "",
            "tbr": parts[6] if len(parts) > 6 and "|" in stripped else "",
            "vcodec": vcodec,
            "acodec": acodec,
            "note": note,
        })

    return formats


@router.post("/api/tasks", status_code=201)
async def create_task(req: TaskCreateRequest, user: CurrentUser):
    db = get_db()
    site = _detect_site(req.url)

    cursor = db.execute(
        "INSERT INTO download_tasks (user_id, url, site, quality, format, cookie_profile_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user["id"], req.url, site, req.quality, req.format, req.cookie_profile_id),
    )
    db.commit()
    task_id = cursor.lastrowid

    row = db.execute("SELECT * FROM download_tasks WHERE id = ?", (task_id,)).fetchone()

    try:
        asyncio.create_task(_run_download(task_id))
    except RuntimeError:
        pass

    return _row_to_task(row)


@router.get("/api/tasks")
def list_tasks(user: CurrentUser, status: str = None):
    db = get_db()
    if status:
        rows = db.execute(
            "SELECT * FROM download_tasks WHERE user_id = ? AND status = ? "
            "ORDER BY created_at DESC",
            (user["id"], status),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM download_tasks WHERE user_id = ? ORDER BY created_at DESC",
            (user["id"],),
        ).fetchall()
    return [_row_to_task(r) for r in rows]


@router.get("/api/tasks/{task_id}")
def get_task(task_id: int, user: CurrentUser):
    db = get_db()
    row = db.execute(
        "SELECT * FROM download_tasks WHERE id = ? AND user_id = ?",
        (task_id, user["id"]),
    ).fetchone()
    if not row:
        return Response(status_code=404, content='{"detail":"Not found"}')
    return _row_to_task(row)


@router.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, user: CurrentUser):
    db = get_db()
    row = db.execute(
        "SELECT * FROM download_tasks WHERE id = ? AND user_id = ?",
        (task_id, user["id"]),
    ).fetchone()
    if not row:
        return Response(status_code=404, content='{"detail":"Not found"}')

    if row["file_path"] and os.path.exists(row["file_path"]):
        os.remove(row["file_path"])
    video_row = db.execute(
        "SELECT thumbnail_path FROM video_files WHERE task_id = ?", (task_id,)
    ).fetchone()
    if video_row and video_row["thumbnail_path"] and os.path.exists(video_row["thumbnail_path"]):
        os.remove(video_row["thumbnail_path"])
    if row["log"] and os.path.exists(row["log"]):
        os.remove(row["log"])

    db.execute("DELETE FROM download_tasks WHERE id = ?", (task_id,))
    db.commit()
    return {"detail": "Deleted"}


async def _run_download(task_id: int):
    """Background yt-dlp subprocess."""
    if os.environ.get("VIDO_TEST") == "1":
        return
    db = get_db()
    row = db.execute("SELECT * FROM download_tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        return

    user_id = row["user_id"]

    db.execute("UPDATE download_tasks SET status = 'downloading' WHERE id = ?", (task_id,))
    db.commit()

    task_downloads = os.path.join(DOWNLOADS_DIR, str(user_id), str(task_id))
    user_logs = os.path.join(LOGS_DIR, str(user_id))
    os.makedirs(task_downloads, exist_ok=True)
    os.makedirs(user_logs, exist_ok=True)

    output_template = os.path.join(task_downloads, "%(title)s-%(id)s.%(ext)s")

    quality_map = {
        "2160p": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
        "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
        "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
    }
    fmt = quality_map.get(row["quality"], "bestvideo[height<=1080]+bestaudio/best[height<=1080]")
    if row["format"]:
        fmt = row["format"]
        # Single format codes (e.g. "136") are usually video-only. Merge with
        # best audio so the output has sound. Combined codes (with "+") are
        # already complete. Quality presets already include "+bestaudio".
        if "+" not in fmt:
            fmt = f"{fmt}+bestaudio/best"

    cookie_path = None
    if row["cookie_profile_id"]:
        cookie_row = db.execute(
            "SELECT cookie_data FROM cookie_profiles WHERE id = ?",
            (row["cookie_profile_id"],),
        ).fetchone()
        if cookie_row and cookie_row["cookie_data"] and os.path.exists(cookie_row["cookie_data"]):
            cookie_path = cookie_row["cookie_data"]

    # Resolve format description for logging
    format_desc = ""
    try:
        list_cmd = [_ytdlp_path(), "--js-runtimes", "node", "--remote-components", "ejs:github",
                    "--list-formats"]
        if cookie_path:
            list_cmd.extend(["--cookies", cookie_path])
        list_cmd.append(row["url"])
        list_proc = await asyncio.create_subprocess_exec(
            *list_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        list_stdout, _ = await list_proc.communicate()
        if list_proc.returncode == 0:
            fmts = _parse_formats(list_stdout.decode(errors="replace"))
            for f in fmts:
                if f["code"] == fmt:
                    parts = [f["resolution"], f["ext"]]
                    if f["vcodec"] and f["vcodec"] not in ("audio only",):
                        parts.append(f["vcodec"])
                    if f["acodec"] and f["acodec"] not in ("video only",):
                        parts.append(f["acodec"])
                    if f["fps"]:
                        parts.append(f"{f['fps']}fps")
                    if f["note"]:
                        parts.append(f["note"])
                    format_desc = ", ".join(parts)
                    break
    except Exception:
        pass

    cmd = [
        _ytdlp_path(),
        "--js-runtimes", "node",
        "--remote-components", "ejs:github",
        "-f", fmt,
        "-o", output_template,
        "--write-thumbnail",
        "--convert-thumbnails", "jpg",
        "--no-mtime",
        row["url"],
    ]
    if cookie_path:
        cmd.extend(["--cookies", cookie_path])

    log_lines = [f"=== FORMAT: {fmt}" + (f" ({format_desc})" if format_desc else "") + " ===\n"]
    log_lines.append(f"=== COMMAND ===\n{' '.join(cmd)}\n")

    log_path = os.path.join(user_logs, f"{task_id}.log")
    full_log = ""
    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        stdout_str = stdout.decode(errors="replace")
        stderr_str = stderr.decode(errors="replace")

        log_lines.append(f"=== EXIT CODE: {proc.returncode} ===\n")
        log_lines.append(f"=== STDOUT ===\n{stdout_str}\n=== STDERR ===\n{stderr_str}")
        full_log = "".join(log_lines)

        with open(log_path, "w") as f:
            f.write(full_log)

        if proc.returncode == 0:
            video_file, thumb_file = _scan_download_dir(task_downloads)

            if video_file:
                file_size = os.path.getsize(video_file)
                title = _extract_title(stdout_str)

                cursor = db.execute(
                    "INSERT INTO video_files (task_id, title, file_path, file_size) "
                    "VALUES (?, ?, ?, ?)",
                    (task_id, title or row["url"], video_file, file_size),
                )
                if thumb_file:
                    db.execute(
                        "UPDATE video_files SET thumbnail_path = ? WHERE id = ?",
                        (thumb_file, cursor.lastrowid),
                    )

                db.execute(
                    "UPDATE download_tasks SET status = 'completed', title = ?, "
                    "file_path = ?, format_desc = ?, log = ?, "
                    "finished_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (title, video_file, format_desc, log_path, task_id),
                )
            else:
                files = os.listdir(task_downloads)
                db.execute(
                    "UPDATE download_tasks SET status = 'failed', "
                    "error_message = ?, format_desc = ?, log = ?, "
                    "finished_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (f"No video found in {task_downloads}, contents: {files}",
                     format_desc, log_path, task_id),
                )
        else:
            error = stderr_str[:500]
            db.execute(
                "UPDATE download_tasks SET status = 'failed', error_message = ?, "
                "format_desc = ?, log = ?, finished_at = CURRENT_TIMESTAMP WHERE id = ?",
                (error, format_desc, log_path, task_id),
            )
    except asyncio.CancelledError:
        if proc is not None and proc.returncode is None:
            try:
                proc.terminate()
            except Exception:
                pass
        log_lines.append("\n=== CANCELLED (server shutdown) ===\n")
        full_log = "".join(log_lines)
        with open(log_path, "w") as f:
            f.write(full_log)
        db.execute(
            "UPDATE download_tasks SET status = 'failed', error_message = ?, "
            "format_desc = ?, log = ?, finished_at = CURRENT_TIMESTAMP WHERE id = ?",
            ("Download interrupted by server shutdown", format_desc, log_path, task_id),
        )
    except Exception as e:
        log_lines.append(f"\n=== EXCEPTION ===\n{str(e)}")
        full_log = "".join(log_lines)
        with open(log_path, "w") as f:
            f.write(full_log)
        db.execute(
            "UPDATE download_tasks SET status = 'failed', error_message = ?, "
            "format_desc = ?, log = ?, finished_at = CURRENT_TIMESTAMP WHERE id = ?",
            (str(e)[:500], format_desc, log_path, task_id),
        )
    finally:
        db.commit()


def _extract_title(output: str) -> str:
    for line in output.splitlines():
        if line.startswith("[download] Destination:"):
            name = line.split("Destination:", 1)[1].strip()
            return os.path.splitext(os.path.basename(name))[0]
    return ""


def _scan_download_dir(directory: str) -> tuple:
    """Scan download directory for video + thumbnail files.
    Returns (video_path, thumbnail_path) or ("", "").
    """
    video_exts = {".mp4", ".webm", ".mkv", ".mp3", ".m4a", ".mov", ".flv", ".avi"}
    pic_exts = {".jpg", ".jpeg", ".png", ".webp"}
    video_file = ""
    thumb_file = ""

    try:
        for f in sorted(os.listdir(directory)):
            path = os.path.join(directory, f)
            if not os.path.isfile(path) or f.startswith("."):
                continue
            ext = os.path.splitext(f)[1].lower()
            if ext in video_exts and not video_file:
                video_file = path
            elif ext in pic_exts and not thumb_file:
                thumb_file = path
    except Exception:
        pass

    return video_file, thumb_file

import asyncio
import shutil
import sys
from fastapi import APIRouter
from app.auth import CurrentUser

router = APIRouter()


def _ytdlp_path() -> str:
    import os
    venv_bin = os.path.join(sys.prefix, "bin", "yt-dlp")
    if os.path.exists(venv_bin):
        return venv_bin
    found = shutil.which("yt-dlp")
    return found or "yt-dlp"


@router.get("/api/system/ytdlp-version")
async def ytdlp_version(user: CurrentUser):
    proc = await asyncio.create_subprocess_exec(
        _ytdlp_path(), "--version",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    version = stdout.decode().strip() if proc.returncode == 0 else ""
    error = stderr.decode()[:200] if proc.returncode != 0 else None
    return {"version": version, "error": error}


@router.post("/api/system/ytdlp-update")
async def ytdlp_update(user: CurrentUser):
    # Use uv if available, fall back to pip
    uv = shutil.which("uv")
    if uv:
        pip = uv
        args = ["pip", "install", "--upgrade", "yt-dlp"]
    else:
        pip = shutil.which("pip") or "pip"
        args = ["install", "--upgrade", "yt-dlp"]

    proc = await asyncio.create_subprocess_exec(
        pip, *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        return {"ok": False, "error": stderr.decode()[:500]}

    # Get new version
    vproc = await asyncio.create_subprocess_exec(
        _ytdlp_path(), "--version",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    vstdout, _ = await vproc.communicate()
    new_version = vstdout.decode().strip()

    return {"ok": True, "version": new_version}

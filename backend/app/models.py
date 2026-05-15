from pydantic import BaseModel, Field
from typing import Optional


# --- Auth ---

class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=4, max_length=100)


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: str
    is_admin: bool = False


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=4, max_length=100)
    is_admin: bool = False


class UserUpdateRequest(BaseModel):
    username: Optional[str] = Field(default=None, min_length=2, max_length=50)
    password: Optional[str] = Field(default=None, min_length=4, max_length=100)
    is_admin: Optional[bool] = None


# --- Cookie Profiles ---

class CookieCreateRequest(BaseModel):
    site: str = Field(min_length=1, max_length=50)
    source_type: str = Field(pattern="^(file_upload|paste)$")
    cookie_content: str  # raw cookie text or file content


class CookieUpdateRequest(BaseModel):
    site: Optional[str] = None
    cookie_content: Optional[str] = None


class CookieProfileResponse(BaseModel):
    id: int
    site: str
    source_type: str
    created_at: str
    updated_at: str


# --- Download Tasks ---

class FormatInfo(BaseModel):
    code: str        # e.g. "247+251"
    ext: str         # e.g. "webm"
    resolution: str  # e.g. "1280x720"
    fps: Optional[str] = None
    file_size: str   # e.g. "~45.23MiB"
    tbr: str         # e.g. "~1000kbps"
    vcodec: str      # e.g. "av01"
    acodec: str      # e.g. "opus"
    note: str = ""   # e.g. "Premium", "HDR"


class ListFormatsRequest(BaseModel):
    url: str
    cookie_profile_id: Optional[int] = None


class TaskCreateRequest(BaseModel):
    url: str
    quality: str = "1080p"
    format: Optional[str] = None  # e.g. "mp4", None means best
    cookie_profile_id: Optional[int] = None


class TaskResponse(BaseModel):
    id: int
    url: str
    site: Optional[str]
    quality: str
    format: Optional[str]
    format_desc: Optional[str] = None
    cookie_profile_id: Optional[int]
    status: str
    title: Optional[str]
    file_path: Optional[str]
    error_message: Optional[str]
    log: Optional[str] = None
    created_at: str
    finished_at: Optional[str]


# --- Videos ---

class VideoResponse(BaseModel):
    id: int
    task_id: int
    title: Optional[str]
    file_path: str
    file_size: Optional[int]
    duration: Optional[int]
    has_thumbnail: bool
    created_at: str


# --- Stats ---

class StatsResponse(BaseModel):
    disk_free_bytes: int
    disk_total_bytes: int
    tasks_pending: int
    tasks_downloading: int
    tasks_completed: int
    tasks_failed: int
    videos_count: int


# --- Health check (unauthenticated) ---

class HealthResponse(BaseModel):
    status: str = "ok"

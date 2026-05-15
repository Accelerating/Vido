# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Vido is a self-hosted web service for downloading videos via yt-dlp, with offline playback, task management, cookie profile management, and per-user authentication. It runs as a single FastAPI process serving both the API and the built React frontend.

## Commands

### Backend (Python / FastAPI)

```bash
cd backend
uv sync                           # install dependencies
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000   # dev server
uv run pytest -v                  # run all tests
uv run pytest -v tests/test_auth.py -k test_register       # run a single test
```

Key dependencies: FastAPI, bcrypt, and a system-installed `yt-dlp` (managed via `uv tool install yt-dlp`).

### Frontend (React / Vite)

```bash
cd frontend
pnpm install                      # install dependencies
pnpm dev                          # Vite dev server (proxies /api to 127.0.0.1:8000)
pnpm build                        # type-check + build into ../backend/static/
pnpm lint                         # ESLint
```

### Full deployment

```bash
./deploy.sh                       # install toolchain, clone repo, build frontend, start backend
```

`deploy.sh` is the all-in-one deployment script: it installs nvm + Node.js, pnpm, uv, and yt-dlp, clones the repository from GitHub (or `git pull` if already cloned), builds the frontend into `backend/static/`, and starts uvicorn. The backend serves these static files via a catch-all route — no separate web server is needed.

## Architecture

### Backend (`backend/app/`)

**Single-process, thread-local SQLite.** `database.py` creates a new connection per thread via `threading.local()`. The test env var `VIDO_TEST=1` switches the db path to `test_vido.db` so tests don't touch production data.

**Auth is cookie-based.** On login/register, a random UUID token is inserted into `auth_tokens` and set as an `httponly` cookie. `get_current_user` is a FastAPI dependency that reads the cookie, looks up the token join, and injects the user dict (including `_token` for logout). All protected routes use the `CurrentUser` annotated dependency.

**yt-dlp runs as a subprocess** (not a Python library). `tasks.py:_run_download` runs `yt-dlp` via `asyncio.create_subprocess_exec` in a background asyncio task. It writes logs to `backend/logs/{user_id}/{task_id}.log` and downloads to `backend/downloads/{user_id}/{task_id}/`. On startup, any `downloading` tasks are marked as `failed` with "Server restarted".

**Router pattern:** Each feature module (`auth.py`, `tasks.py`, `videos.py`, `cookies.py`, `stats.py`, `system.py`, `users.py`) defines its own `APIRouter` and is included in `main.py:create_app()`.

**Database tables (SQLite):** `users` (with `is_admin` flag), `auth_tokens`, `cookie_profiles`, `download_tasks`, `video_files`. Cookie content is stored as files on disk (under `backend/cookies/{user_id}/{profile_id}.txt`) with the file path stored in `cookie_profiles.cookie_data`.

**Auth & admin:** Registration is only open when the `users` table is empty. The first registered user automatically becomes admin (`is_admin = 1`). Admin-only endpoints use the `CurrentAdminUser` dependency (checks `is_admin`). Login is rate-limited: 5 failed attempts from the same IP within 10 minutes triggers a 1-hour lockout (in-memory, 429 status).

### Frontend (`frontend/src/`)

**Stack:** React 19, react-router v7, TanStack Query, Tailwind CSS v4, shadcn/ui components.

**Auth flow:** `useAuth` context hydrates from `GET /api/auth/me` on mount. `ProtectedRoute` redirects to `/login` if unauthenticated.

**API client** (`api/client.ts`): thin wrappers around `fetch` with `credentials: "include"` for cookie auth.

**i18n:** Custom `I18nProvider` context with zh/en translations in `i18n/translations.ts`. Language persisted to `localStorage`.

**Build output** goes to `../backend/static/` (configured in `vite.config.ts`). The Vite dev server proxies `/api` to `http://127.0.0.1:8000`.

### Testing

Tests live in `backend/tests/` with pytest. `conftest.py` sets `VIDO_TEST=1`, creates a fresh test DB, and tears it down after each test. Uses `fastapi.testclient.TestClient`. No frontend tests exist currently.

## Key conventions

- yt-dlp path resolution: checks `$VIRTUAL_ENV/bin/yt-dlp` first, then falls back to `shutil.which("yt-dlp")`
- Task status lifecycle: `pending` → `downloading` → `completed` / `failed`
- Format parsing: `tasks.py:_parse_formats` parses yt-dlp's tabular `--list-formats` text output by splitting lines and columns
- Cookie profiles support two import methods: `file_upload` (upload a Netscape-format cookie file) or `paste` (paste raw cookie text)

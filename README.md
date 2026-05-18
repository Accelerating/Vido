# Vido

[中文文档](README_zh.md)

A self-hosted web service for downloading videos via yt-dlp, with online playback, download task management, cookie profile management, and per-user authentication.

## Features

- **Video downloading** — submit YouTube URLs and download them with yt-dlp
- **Format selection** — choose video resolution and format before downloading
- **Offline playback** — stream downloaded videos directly in the browser
- **Task management** — track download progress, cancel tasks, view logs
- **Cookie profiles** — import Netscape-format cookies (file upload or paste) for authenticated downloads
- **Multi-user** — register/login with cookie-based auth, each user has isolated tasks and files
- **i18n** — English and Chinese UI

## Dependencies

### System requirements

- **Python >= 3.13**
- **Node.js >= 24** (for building the frontend)
- **pnpm** (enabled via corepack or installed globally)
- **uv** (Python package manager)

### Backend

| Dependency | Purpose |
|---|---|
| [FastAPI](https://fastapi.tiangolo.com/) | Web framework |
| [uvicorn](https://www.uvicorn.org/) | ASGI server |
| [bcrypt](https://pypi.org/project/bcrypt/) | Password hashing |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Video downloading engine |
| [python-multipart](https://pypi.org/project/python-multipart/) | Form/file upload support |

### Frontend

| Dependency | Purpose |
|---|---|
| [React 19](https://react.dev/) | UI framework |
| [react-router v7](https://reactrouter.com/) | Client-side routing |
| [TanStack Query](https://tanstack.com/query) | Server state management |
| [Tailwind CSS v4](https://tailwindcss.com/) | Styling |
| [shadcn/ui](https://ui.shadcn.com/) | UI components |
| [Vite](https://vitejs.dev/) | Build tool |

## Quick Start

One command to deploy Vido on a fresh machine:

```bash
curl -fsSL https://raw.githubusercontent.com/Accelerating/Vido/refs/heads/main/deploy.sh | bash
```

This downloads and runs the deploy script, which installs all system dependencies (nvm + Node.js 24, pnpm, uv, yt-dlp), clones the repository, builds the frontend, and starts the server on `http://localhost:8000`.

After the first deployment, re-running the same command will `git pull` the latest changes and rebuild automatically — no manual update steps needed.

## Development

### Backend dev server

```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend dev server

```bash
cd frontend
pnpm dev
```

The Vite dev server runs on `http://localhost:5173` and proxies `/api` requests to the backend at `127.0.0.1:8000`.

### Running tests

```bash
cd backend
uv run pytest -v
```

Tests use a separate database (`test_vido.db`) via the `VIDO_TEST=1` environment variable, set automatically by `conftest.py`.

## Architecture

Vido runs as a **single FastAPI process** serving both the REST API and the built React frontend. No separate web server (nginx, etc.) is required.

- **Database:** SQLite with thread-local connections. The database file is created at `backend/vido.db` on first startup.
- **Auth:** Cookie-based with UUID tokens stored in the `auth_tokens` table. Cookies are `httponly`.
- **Download engine:** yt-dlp runs as a subprocess via `asyncio.create_subprocess_exec`. Downloads are stored at `backend/downloads/{user_id}/{task_id}/` and logs at `backend/logs/{user_id}/{task_id}.log`.
- **Cookie storage:** Cookie file content is stored on disk at `backend/cookies/{user_id}/{profile_id}.txt`, with metadata in the SQLite `cookie_profiles` table.

### Task lifecycle

```
pending → downloading → completed
                      → failed
```

On server restart, any tasks stuck in `downloading` state are automatically marked as `failed` with the message "Server restarted".

### Directory structure

```
Vido/
├── backend/
│   ├── app/            # FastAPI application
│   │   ├── auth.py     # Registration, login, logout
│   │   ├── tasks.py    # Download task CRUD + yt-dlp subprocess
│   │   ├── videos.py   # Video listing, playback, deletion
│   │   ├── cookies.py  # Cookie profile management
│   │   ├── stats.py    # Usage statistics
│   │   ├── system.py   # yt-dlp version, system info
│   │   ├── database.py # SQLite connection management
│   │   ├── config.py   # Paths and constants
│   │   └── main.py     # App factory and router registration
│   ├── tests/           # pytest test suite
│   ├── static/          # Built frontend output
│   ├── downloads/       # Downloaded video files
│   ├── cookies/         # Cookie profile files
│   ├── logs/            # Download task logs
│   └── pyproject.toml
├── frontend/
│   └── src/
│       ├── api/         # API client
│       ├── components/  # Reusable UI components
│       ├── i18n/        # Translations (zh/en)
│       ├── lib/         # Utilities
│       └── pages/       # Route pages
├── deploy.sh            # All-in-one deployment script
└── README.md
```

import os
from fastapi import FastAPI

from app.database import init_db, close_db, get_db
from app.config import STATIC_DIR


def create_app() -> FastAPI:
    app = FastAPI(title="Vido")

    @app.on_event("startup")
    def startup():
        init_db()
        db = get_db()
        db.execute(
            "UPDATE download_tasks SET status = 'failed', "
            "error_message = 'Server restarted', finished_at = CURRENT_TIMESTAMP "
            "WHERE status = 'downloading'"
        )
        db.commit()

    @app.on_event("shutdown")
    def shutdown():
        close_db()

    from app.auth import router as auth_router
    from app.cookies import router as cookies_router
    from app.tasks import router as tasks_router
    from app.videos import router as videos_router
    from app.stats import router as stats_router
    from app.system import router as system_router
    from app.users import router as users_router

    app.include_router(auth_router)
    app.include_router(cookies_router)
    app.include_router(tasks_router)
    app.include_router(videos_router)
    app.include_router(stats_router)
    app.include_router(system_router)
    app.include_router(users_router)

    if os.path.isdir(STATIC_DIR):
        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            import os as _os
            path = _os.path.join(STATIC_DIR, full_path)
            if _os.path.isfile(path):
                from fastapi.responses import FileResponse
                return FileResponse(path)
            from fastapi.responses import FileResponse
            return FileResponse(_os.path.join(STATIC_DIR, "index.html"))

    return app


app = create_app()

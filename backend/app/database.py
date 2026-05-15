import os
import sqlite3
import threading
from app.config import DATABASE_PATH

_conn_local = threading.local()


def get_db_path():
    if os.environ.get("VIDO_TEST") == "1":
        return "test_vido.db"
    return DATABASE_PATH


def get_db():
    if not hasattr(_conn_local, "conn") or _conn_local.conn is None:
        _conn_local.conn = sqlite3.connect(get_db_path())
        _conn_local.conn.row_factory = sqlite3.Row
        _conn_local.conn.execute("PRAGMA journal_mode=WAL")
        _conn_local.conn.execute("PRAGMA foreign_keys=ON")
    return _conn_local.conn


def close_db():
    if hasattr(_conn_local, "conn") and _conn_local.conn is not None:
        _conn_local.conn.close()
        _conn_local.conn = None


def init_db(test=False):
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS auth_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS cookie_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            site TEXT NOT NULL,
            cookie_data TEXT NOT NULL,
            source_type TEXT NOT NULL CHECK(source_type IN ('file_upload', 'paste')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS download_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            url TEXT NOT NULL,
            site TEXT,
            quality TEXT DEFAULT '1080p',
            format TEXT,
            cookie_profile_id INTEGER REFERENCES cookie_profiles(id) ON DELETE SET NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending','downloading','completed','failed')),
            title TEXT,
            file_path TEXT,
            error_message TEXT,
            log TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS video_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL REFERENCES download_tasks(id) ON DELETE CASCADE,
            title TEXT,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            duration INTEGER,
            thumbnail_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

    """)
    # Migration: add log column if upgrading from older schema
    try:
        conn.execute("ALTER TABLE download_tasks ADD COLUMN log TEXT")
    except Exception:
        pass  # column already exists
    try:
        conn.execute("ALTER TABLE download_tasks ADD COLUMN format_desc TEXT")
    except Exception:
        pass  # column already exists
    try:
        conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    except Exception:
        pass  # column already exists

    conn.commit()

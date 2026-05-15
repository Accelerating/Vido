from app.database import init_db, get_db, close_db


def test_init_db_creates_tables():
    init_db(test=True)
    conn = get_db()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = [t["name"] for t in tables]
    assert "users" in table_names
    assert "auth_tokens" in table_names
    assert "cookie_profiles" in table_names
    assert "download_tasks" in table_names
    assert "video_files" in table_names
    close_db()

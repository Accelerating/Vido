import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE_PATH = os.path.join(BASE_DIR, "vido.db")
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
STATIC_DIR = os.path.join(BASE_DIR, "static")
COOKIES_DIR = os.path.join(BASE_DIR, "cookies")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

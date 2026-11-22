import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

API_ID = int(os.getenv("TG_API_ID", "0"))
API_HASH = os.getenv("TG_API_HASH", "").strip()

TDLIB_PATH = BASE_DIR / "tdlib" / "tdjson.dll"

DATABASE_DIR = BASE_DIR / "session" / "database"
FILES_DIR = BASE_DIR / "session" / "files"
DOWNLOADS_DIR = BASE_DIR / "downloads"
VOICE_DIR = DOWNLOADS_DIR / "voice"

if API_ID <= 0:
    raise RuntimeError("Неверный Telegram API ID")

if not API_HASH:
    raise RuntimeError("Не задан Telegram API HASH")

if not TDLIB_PATH.exists():
    raise FileNotFoundError(f"Не найдена библиотека: {TDLIB_PATH}")

DATABASE_DIR.mkdir(parents=True, exist_ok=True)
FILES_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
VOICE_DIR.mkdir(parents=True, exist_ok=True)

# src/teams_transcript_notion_sync/config.py
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str) -> str:
    """必須の環境変数を取得する。存在しない場合は例外を投げる。"""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable '{name}' is not set")
    return value


BASE_DIR = Path(os.environ.get("APP_BASE_DIR", Path(__file__).resolve().parents[2]))

# ===== パス関連 =====
ONEDRIVE_MEETINGS_DIR = Path(_require_env("ONEDRIVE_MEETINGS_DIR"))

DATA_DIR = BASE_DIR / "data"
TRANSCRIPT_DIR = BASE_DIR / "transcripts"
SUMMARY_DIR = BASE_DIR / "summaries"
PROCESSED_DB = DATA_DIR / "processed_files.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

# ===== whisper.cpp =====
WHISPER_BIN = Path(_require_env("WHISPER_BIN"))
WHISPER_MODEL = Path(_require_env("WHISPER_MODEL"))

# ===== ffmpeg =====
# パス通っていればデフォルト "ffmpeg" でOK。必要なら .env で FFMPEG_BIN を上書き。
FFMPEG_BIN = os.environ.get("FFMPEG_BIN", "ffmpeg")

# ===== Notion =====
NOTION_TOKEN = _require_env("NOTION_TOKEN")
NOTION_DATABASE_ID = _require_env("NOTION_DATABASE_ID")

# ===== LLM (Local Gateway) =====
# ゲートウェイURLとモデルは必須
LLM_BASE_URL = _require_env("BASE_URL")
LLM_MODEL = _require_env("MODEL")
LLM_API_KEY = os.environ.get("API_KEY")  # APIキーは任意

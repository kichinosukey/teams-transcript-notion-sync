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
TRANSCRIPT_DIR = DATA_DIR / "transcripts"
SUMMARY_DIR = DATA_DIR / "summaries"
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

# ===== Speaker diarization (pyannote) =====
def _optional_int(name: str) -> int | None:
    """任意の環境変数を整数として取得する。

    Args:
        name (str): 環境変数名。

    Returns:
        int | None: 取得できた場合は整数、未設定/空の場合はNone。

    Raises:
        RuntimeError: 整数に変換できない場合。
    """
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Invalid integer for '{name}': {value}") from exc


SPEAKER_COUNT = _optional_int("SPEAKER_COUNT")
SPEAKER_LABELS = [
    label.strip()
    for label in os.environ.get("SPEAKER_LABELS", "").split(",")
    if label.strip()
]
PYANNOTE_MODEL = os.environ.get(
    "PYANNOTE_MODEL", "pyannote/speaker-diarization-3.1"
)
HF_TOKEN = os.environ.get("HF_TOKEN")

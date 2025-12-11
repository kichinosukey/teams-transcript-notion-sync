# src/teams_transcript_notion_sync/db.py
import json
from pathlib import Path
from typing import Dict, Any


def load_db(path: Path) -> Dict[str, Any]:
    """JSONファイルからDBを読み込む。存在しない場合は空の辞書を返す。"""
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_db(path: Path, data: Dict[str, Any]) -> None:
    """DBをJSONファイルに保存する。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

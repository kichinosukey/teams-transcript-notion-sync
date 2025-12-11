from __future__ import annotations
import os
from pathlib import Path
from typing import List, Literal, TypedDict

from .config import ONEDRIVE_MEETINGS_DIR, PROCESSED_DB
from .db import load_db, save_db


class ProcessedRecord(TypedDict, total=False):
    """処理済みファイルの記録用レコード。"""

    mtime: int
    status: str
    note: str


def _is_target_file(path: Path) -> bool:
    """対象のMP4ファイルかどうかを判定する。"""
    if not path.is_file():
        return False
    if path.suffix.lower() != ".mp4":
        return False
    if path.stat().st_size == 0:
        return False
    return True


def find_new_mp4s() -> List[Path]:
    """新規または更新されたMP4ファイルをOneDriveのディレクトリから探す。"""
    db = load_db(PROCESSED_DB)
    new_files: List[Path] = []

    for root, _, files in os.walk(ONEDRIVE_MEETINGS_DIR):
        root_path = Path(root)
        for name in files:
            path = root_path / name

            if not _is_target_file(path):
                continue

            mtime = int(path.stat().st_mtime)
            key = str(path)
            rec = db.get(key)

            if rec is None or rec.get("mtime") != mtime:
                new_files.append(path)

    return new_files


def mark_processed(
    path: Path,
    status: Literal["new", "transcribed", "done", "error"] = "done",
    note: str | None = None,
) -> None:
    """指定のファイルを処理済みとしてマークする。"""
    db = load_db(PROCESSED_DB)
    key = str(path)
    rec: ProcessedRecord = {
        "mtime": int(path.stat().st_mtime),
        "status": status,
    }
    if note:
        rec["note"] = note

    db[key] = rec
    save_db(PROCESSED_DB, db)

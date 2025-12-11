# src/teams_transcript_notion_sync/audio.py
from pathlib import Path
import subprocess

from .config import FFMPEG_BIN, TRANSCRIPT_DIR


def convert_mp4_to_wav(mp4_path: Path) -> Path:
    """
    .mp4 ファイルを .wav に変換する。
    出力先は transcripts/ 配下の同名 .wav とする。
    """
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

    wav_path = TRANSCRIPT_DIR / f"{mp4_path.stem}.wav"

    cmd = [
        FFMPEG_BIN,
        "-y",  # 上書き
        "-i",
        str(mp4_path),
        "-ac",
        "1",  # モノラル
        "-ar",
        "16000",  # 16kHz
        str(wav_path),
    ]

    subprocess.run(cmd, check=True)
    return wav_path

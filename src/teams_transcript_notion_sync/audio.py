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


def remove_silence_from_wav(
    wav_path: Path,
    *,
    start_silence: float = 5,
    start_threshold_db: float = -40.0,
    output_path: Path | None = None,
) -> Path:
    """
    ffmpeg の silenceremove フィルタで無音区間を除去した .wav を生成する。

    例:
      ffmpeg -i input.wav \\
        -af "silenceremove=start_periods=1:start_silence=0.5:start_threshold=-40dB" \\
        output.wav
    """
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        output_path = wav_path.with_name(f"{wav_path.stem}-nosilence{wav_path.suffix}")
        # -nosilenceを.nosilenceに変更すると、.stemが正しく取得できない
        # e.g. sample.nosilence.wav -> sample.nosilence
        # FilenotFoundError: [Errno 2] No such file or directory: 'sample.nosilence.wav'となる

    af = (
        "silenceremove="
        f"start_periods=1:start_silence={start_silence}:start_threshold={start_threshold_db}dB"
    )

    cmd = [
        FFMPEG_BIN,
        "-y",  # 上書き
        "-i",
        str(wav_path),
        "-af",
        af,
        str(output_path),
    ]

    subprocess.run(cmd, check=True)
    return output_path

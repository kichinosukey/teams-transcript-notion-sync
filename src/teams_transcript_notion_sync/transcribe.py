# src/teams_transcript_notion_sync/transcribe.py
from pathlib import Path
import subprocess

from .config import TRANSCRIPT_DIR, WHISPER_BIN, WHISPER_MODEL
from .scanner import mark_processed
from .noise_filter import remove_fake_speaker_labels
from .speaker_annotator import annotate_transcript_with_speakers


def transcribe_meeting(wav_path: Path, original_mp4: Path | None = None) -> Path:
    """
    .wav を whisper.cpp で文字起こしして .txt を生成する。
    original_mp4 は processed 状態管理用（なければ無視）。
    """
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

    out_prefix = TRANSCRIPT_DIR / wav_path.stem

    cmd = [
        str(WHISPER_BIN),
        "-m",
        str(WHISPER_MODEL),
        "-f",
        str(wav_path),
        "-l",
        "ja",
        "-of",
        str(out_prefix),
        "-otxt",
        "-osrt",
    ]

    subprocess.run(cmd, check=True)

    txt_path = out_prefix.with_suffix(".txt")
    srt_path = out_prefix.with_suffix(".srt")
    annotated_txt_path = out_prefix.with_name(f"{out_prefix.name}_annotated.txt")
    try:
        annotated_text = annotate_transcript_with_speakers(wav_path, srt_path)
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"[WARN] Speaker annotation skipped: {exc}")
        annotated_text = ""

    if annotated_text:
        annotated_txt_path.write_text(annotated_text)
    else:
        # whisper.cpp が生成した txt を読み込み、ノイズを除去して上書き保存する
        raw_text = txt_path.read_text()
        cleaned_text = remove_fake_speaker_labels(raw_text)
        if cleaned_text != raw_text:
            txt_path.write_text(cleaned_text)

    # mp4 が渡されていれば status 更新
    if original_mp4 is not None:
        mark_processed(original_mp4, status="transcribed")

    return txt_path

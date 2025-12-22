# src/teams_transcript_notion_sync/pipeline.py
from datetime import datetime
from pathlib import Path

from .scanner import find_new_mp4s, mark_processed
from .audio import convert_mp4_to_wav, remove_silence_from_wav
from .transcribe import transcribe_meeting
from .summarizer import summarize_transcript
from .notion_writer import create_meeting_page


def process_single_meeting(mp4: Path):
    """1つの会議(mp4)を処理してNotionにアップロードする。"""

    print(f"[INFO] Start processing: {mp4}")

    # 0) mp4 -> wav
    wav_path = convert_mp4_to_wav(mp4)
    print(f"[INFO] Converted to wav: {wav_path}")

    # 無音除去
    wav_path_no_silence = remove_silence_from_wav(
        wav_path,
        start_silence=5,
        start_threshold_db=-40.0,
    )
    print(f"[INFO] Removed silence: {wav_path_no_silence}")

    # 1) 文字起こし（wav入力）
    transcript_path = transcribe_meeting(wav_path_no_silence, original_mp4=mp4)
    print("*" * 20)
    print(f"[INFO] Transcription completed: {transcript_path}")

    # 2) 要約
    summary_path = summarize_transcript(transcript_path)

    summary_text = summary_path.read_text()
    transcript_text = transcript_path.read_text()

    # 3) Notionページ作成
    create_meeting_page(
        title=mp4.stem,
        date=datetime.fromtimestamp(mp4.stat().st_mtime),
        teams_url=None,
        summary_text=summary_text,
        transcript_text=transcript_text,
    )

    # 4) 状態管理（最終的に done にする）
    mark_processed(mp4, status="done")


def process_new_meetings():
    """新しいmp4を見つけて、それぞれ process_single_meeting を呼ぶ"""

    files = find_new_mp4s()
    if not files:
        print("No new meetings.")
        return

    for mp4 in files:
        try:
            process_single_meeting(mp4)
        except Exception as e:
            print(f"[ERROR] while processing {mp4}: {e}")
            mark_processed(mp4, status="error", note=str(e))


if __name__ == "__main__":
    process_new_meetings()

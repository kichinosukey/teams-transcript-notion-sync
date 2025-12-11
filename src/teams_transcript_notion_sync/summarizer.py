from pathlib import Path
import openai

from .config import SUMMARY_DIR, LLM_BASE_URL, LLM_MODEL, LLM_API_KEY


SUMMARY_PROMPT_TEMPLATE = """
あなたは日本語の社内会議録の要約に詳しいアシスタントです。
以下の文字起こしからトピック別要約を生成してください。

ーーー ここから文字起こし ーーー
{transcript}
"""


def summarize_transcript(transcript_path: Path) -> Path:
    """指定された文字起こしファイルを要約し、要約ファイルのパスを返す。"""
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    transcript = transcript_path.read_text()
    truncated = transcript[:15000]
    prompt = SUMMARY_PROMPT_TEMPLATE.format(transcript=truncated)

    client = openai.OpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
    )

    res = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": "あなたは厳密で要約が得意なアシスタントです。",
            },
            {"role": "user", "content": prompt},
        ],
    )

    summary = res.choices[0].message.content
    out_path = SUMMARY_DIR / f"{transcript_path.stem}_summary.txt"
    out_path.write_text(summary)
    return out_path

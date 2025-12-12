import re

import openai

from pathlib import Path
from typing import Tuple

from .config import SUMMARY_DIR, LLM_BASE_URL, LLM_MODEL, LLM_API_KEY

# 正規表現: Markdownテーブルの区切り行検出用
_SEP_RE = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$")

SUMMARY_PROMPT_TEMPLATE = """
あなたは日本語の社内会議録を「トピック別に表で要約」する専門家です。
以下の文字起こしから要約を作成してください。

【出力フォーマットの絶対ルール】
- 出力は Markdown のテーブル「1つだけ」。テーブル以外の文章・見出し・注釈・引用・箇条書きは禁止。
- テーブルは必ず次の2列で固定する（列の追加/削除は禁止）。
  1) トピック
  2) 内容
- 1行目はヘッダ行、2行目は区切り行（---）とする。
- 3行目以降にトピック別要約を3〜7行で書く。
- 各セルは1〜3文で簡潔に。
- セル内に改行は入れない。必要なら「、」「;」でつなぐ。
- セル内で “|” を使わない（使うと列が壊れるため）。

【出力例（この形式のみ）】
| トピック | 内容 |
|---|---|
| 会話の内容 | … |
| 決定事項 | … |
| 次のステップ | … |

ーーー ここから文字起こし ーーー
{transcript}
ーーー ここまで文字起こし ーーー
"""


def validate_and_normalize_markdown_table(text: str) -> Tuple[bool, str, str]:
    """Markdownテーブル形式の要約テキストを検証・正規化する。
    Args:
        text (str): 要約テキスト
    Returns:
        Tuple[bool, str, str]: (is_valid, normalized_text, error_code)
            is_valid: 検証結果（True: 正常, False: 異常）
            normalized_text: 正規化済みテキスト（異常時は元のまま返す）
            error_code: エラーコード（正常時は空文字列）
    """
    lines = text.strip().splitlines()
    non_empty = [l.strip() for l in lines if l.strip()]

    # validate: 空 or テーブル外混在
    if not non_empty:
        return False, text, "no_data_rows"
    if any("|" not in l for l in non_empty):
        return False, text, "non_table_text_detected"

    # validate: ヘッダ+区切り
    if len(non_empty) < 2 or not _SEP_RE.match(non_empty[1]):
        return False, text, "separator_missing_or_invalid"

    def split_row(line: str) -> list[str]:
        line = line.strip().strip("|")
        return [c.strip() for c in line.split("|")]

    header_cells = split_row(non_empty[0])
    if len(header_cells) != 2:
        return False, text, "header_not_two_columns"

    data_lines = non_empty[2:]
    if not data_lines:
        return False, text, "no_data_rows"

    # normalize: 各行を必ず2列に収束
    normalized_rows = []
    for line in data_lines:
        cells = split_row(line)

        if len(cells) == 1:
            cells = [cells[0], ""]
        elif len(cells) > 2:
            cells = [cells[0], " / ".join(cells[1:])]

        # セル内の安全化
        cells = [c.replace("\n", " ").replace("|", "｜") for c in cells]

        normalized_rows.append(f"| {cells[0]} | {cells[1]} |")

    normalized = (
        "\n".join(["| トピック | 内容 |", "|---|---|", *normalized_rows]).rstrip()
        + "\n"
    )

    return True, normalized, ""


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
    is_valid, normalized, error_code = validate_and_normalize_markdown_table(summary)
    if not is_valid:

        raise ValueError(
            f"要約のフォーマットが不正です (error_code={error_code}):\n{summary}"
        )
    summary = normalized
    out_path = SUMMARY_DIR / f"{transcript_path.stem}_summary.txt"
    out_path.write_text(summary)
    return out_path

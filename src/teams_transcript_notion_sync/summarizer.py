import re

import openai

from pathlib import Path
from typing import Tuple

from .config import SUMMARY_DIR, LLM_BASE_URL, LLM_MODEL, LLM_API_KEY

# 正規表現: Markdownテーブルの区切り行検出用
_SEP_RE = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$")

SUMMARY_PROMPT_TEMPLATE = """
以下の文字起こしを読み、社内MTGの議事録要約を作成してください。

Speaker1 / Speaker2 は話者ラベルです。

【出力形式】
- 出力は Markdown の表のみとする
- 表の列は必ず以下の3列に固定する
  1. トピック
  2. 要約（議事録）
  3. 根拠となる発言（引用）
- 1行目はヘッダ行、2行目は区切り行（---）とする

【内容ルール】
- トピックごとに「何が話されたか」を要約する
- 要約には誰が何を言ったかが分かるように、話者の視点差を含める
- 引用は Speaker1 / Speaker2 を付けた原文ママ（完全一致）で記載する
- 1行につき1トピックのみ
- すべて時系列順に並べる
- セル内で改行はしない（必要なら「、」「;」でつなぐ）
- セル内で “|” を使わない（使うと列が壊れるため）

【出力イメージ（構造のみ）】
| トピック | 要約（議事録） | 根拠となる発言（引用） |
|---|---|---|
| 進捗共有 | Speaker1がAの進捗を報告し、Speaker2がBの遅延を共有した | "Speaker1: Aは今週中に完了見込み" / "Speaker2: Bは来週にずれそうです" |
| 次アクション | Speaker2が対応方針を提案し、Speaker1が了承した | "Speaker2: 先にCを片付けます" / "Speaker1: それでお願いします" |

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
    if len(header_cells) != 3:
        return False, text, "header_not_three_columns"

    data_lines = non_empty[2:]
    if not data_lines:
        return False, text, "no_data_rows"

    # normalize: 各行を必ず3列に収束
    normalized_rows = []
    for line in data_lines:
        cells = split_row(line)

        if len(cells) == 1:
            cells = [cells[0], "", ""]
        elif len(cells) == 2:
            cells = [cells[0], cells[1], ""]
        elif len(cells) > 3:
            cells = [cells[0], cells[1], " / ".join(cells[2:])]

        # セル内の安全化
        cells = [c.replace("\n", " ").replace("|", "｜") for c in cells]

        normalized_rows.append(f"| {cells[0]} | {cells[1]} | {cells[2]} |")

    normalized = (
        "\n".join(
            [
                "| トピック | 要約（議事録） | 根拠となる発言（引用） |",
                "|---|---|---|",
                *normalized_rows,
            ]
        ).rstrip()
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

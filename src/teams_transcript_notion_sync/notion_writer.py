from datetime import datetime
from typing import Optional, Iterable, List
from notion_client import Client
from .config import NOTION_TOKEN, NOTION_DATABASE_ID


notion = Client(auth=NOTION_TOKEN)


def _chunk(text: str, size: int = 1800) -> Iterable[str]:
    """テキストを指定されたサイズで分割するジェネレーター。

    Args:
        text (str): 分割対象のテキスト
        size (int): 分割サイズ（デフォルト: 1800文字）

    Note:
        Notionの1ブロックあたりのテキスト上限は約2000文字。
        安全を見て1800文字で分割する。
    """
    for i in range(0, len(text), size):
        yield text[i : i + size]


def _split_markdown_row(line: str) -> List[str]:
    line = line.strip().strip("|")
    return [c.strip() for c in line.split("|")]


def markdown_table_to_notion_table_block(summary_text: str) -> dict:
    """2列MarkdownテーブルをNotionのtable/table_rowブロックに変換する。

    前提: summary_text は summarizer により検証済みの2列Markdownテーブル。
    """
    lines = [l.strip() for l in summary_text.strip().splitlines() if l.strip()]
    header_cells = _split_markdown_row(lines[0])
    data_lines = lines[2:]  # skip separator
    rows: List[List[str]] = [header_cells] + [_split_markdown_row(l) for l in data_lines]

    children = []
    for r in rows:
        cells = [
            [{"type": "text", "text": {"content": r[0]}}],
            [{"type": "text", "text": {"content": r[1]}}],
        ]
        children.append(
            {
                "object": "block",
                "type": "table_row",
                "table_row": {"cells": cells},
            }
        )

    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": 2,
            "has_column_header": True,
            "has_row_header": False,
            "children": children,
        },
    }


def create_meeting_page(title, date, teams_url, summary_text, transcript_text):
    """Notionに会議ページを作成する。

    Args:
        title (str): ページタイトル
        date (Optional[datetime]): 会議日時
        teams_url (Optional[str]): Teams会議URL
        summary_text (str): 会議要約テキスト
        transcript_text (str): 文字起こし全文テキスト

    """

    children = []

    # 会議要約セクション
    children.append(
        {
            "object": "block",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "会議要約"}}]
            },
        }
    )
    # 会議要約テキストをMarkdownテーブルとして追加
    children.append(markdown_table_to_notion_table_block(summary_text))
    # 文字起こし全文セクション
    children.append(
        {
            "object": "block",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "全文文字起こし"}}]
            },
        }
    )
    # 文字起こし全文テキストをチャンクに分割して追加
    for c in _chunk(transcript_text):
        children.append(
            {
                "object": "block",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": c}}]},
            }
        )

    # ページプロパティ設定
    props = {"Name": {"title": [{"text": {"content": title}}]}}
    # オプションプロパティ設定
    ## 日時
    if date:
        props["Date"] = {"date": {"start": date.isoformat()}}
    ## Teams URL
    if teams_url:
        props["Teams URL"] = {"url": teams_url}

    # Notionページ作成
    notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
        properties=props,
        children=children,
    )

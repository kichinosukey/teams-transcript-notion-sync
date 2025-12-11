from datetime import datetime
from typing import Optional, Iterable
from notion_client import Client
from .config import NOTION_TOKEN, NOTION_DATABASE_ID


notion = Client(auth=NOTION_TOKEN)


def _chunk(text: str, size: int = 1800) -> Iterable[str]:
    """テキストを指定されたサイズで分割するジェネレーター。"""
    for i in range(0, len(text), size):
        yield text[i : i + size]


def create_meeting_page(title, date, teams_url, summary_text, transcript_text):
    """Notionに会議ページを作成する。"""

    children = []

    children.append(
        {
            "object": "block",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "会議要約"}}]
            },
        }
    )
    for c in _chunk(summary_text):
        children.append(
            {
                "object": "block",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": c}}]},
            }
        )

    children.append(
        {
            "object": "block",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "全文文字起こし"}}]
            },
        }
    )
    for c in _chunk(transcript_text):
        children.append(
            {
                "object": "block",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": c}}]},
            }
        )

    props = {"Name": {"title": [{"text": {"content": title}}]}}
    if date:
        props["Date"] = {"date": {"start": date.isoformat()}}
    if teams_url:
        props["Teams URL"] = {"url": teams_url}

    notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
        properties=props,
        children=children,
    )

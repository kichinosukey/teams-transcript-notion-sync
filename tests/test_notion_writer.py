from datetime import datetime
from teams_transcript_notion_sync import notion_writer


class DummyPages:
    """ダミーのNotionページオブジェクト。"""

    def __init__(self):
        self.called = False
        self.data = None

    def create(self, **kwargs):
        self.called = True
        self.data = kwargs


class DummyClient:
    """ダミーのNotionクライアント。"""

    def __init__(self, auth):
        self.pages = DummyPages()


def test_notion_writer(monkeypatch):
    """Notionへの会議ページ作成が正しく行われることを確認する。

    Args:
        monkeypatch: 環境変数や属性を一時的に変更するためのフィクスチャ
    """
    dummy = DummyClient("auth")
    monkeypatch.setattr(notion_writer, "notion", dummy)

    notion_writer.create_meeting_page(
        title="Test",
        date=datetime.now(),
        teams_url=None,
        summary_text="| トピック | 内容 |\n|---|---|\n| 会話の内容 | テスト |\n",
        transcript_text="t",
    )

    assert dummy.pages.called

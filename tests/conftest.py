# tests/conftest.py
import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _set_test_env(tmp_path, monkeypatch):
    """
    すべてのテストで共通の環境変数をセットする。
    - ONEDRIVE_MEETINGS_DIR: 一時ディレクトリ
    - WHISPER_BIN / WHISPER_MODEL: ダミーパス
    - NOTION_TOKEN / NOTION_DATABASE_ID: ダミー
    - BASE_URL / MODEL: LLM用ダミー
    """
    onedrive = tmp_path / "onedrive"
    onedrive.mkdir()

    monkeypatch.setenv("ONEDRIVE_MEETINGS_DIR", str(onedrive))
    monkeypatch.setenv("WHISPER_BIN", "/tmp/fake-whisper-bin")
    monkeypatch.setenv("WHISPER_MODEL", "/tmp/fake-whisper-model")
    monkeypatch.setenv("NOTION_TOKEN", "test-notion-token")
    monkeypatch.setenv("NOTION_DATABASE_ID", "test-db-id")

    # LLM 関連
    monkeypatch.setenv("BASE_URL", "http://localhost:9999/v1")
    monkeypatch.setenv("MODEL", "dummy/model")

    yield

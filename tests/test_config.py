from teams_transcript_notion_sync import config


def test_config_paths():
    """設定ファイルのパスが存在することを確認する。"""
    assert config.DATA_DIR.exists()
    assert config.TRANSCRIPT_DIR.exists()
    assert config.SUMMARY_DIR.exists()

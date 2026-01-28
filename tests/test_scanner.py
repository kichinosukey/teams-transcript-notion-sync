from teams_transcript_notion_sync import scanner


def test_find_new_mp4s(tmp_path, monkeypatch):
    """新しいMP4ファイルを正しく検出できることを確認する。

    Args:
        tmp_path: pytestの一時ディレクトリ用フィクスチャ
        monkeypatch: 環境変数や属性を一時的に変更するためのフィクスチャ
    """
    recordings = tmp_path / "onedrive"  # tmp_path
    recordings.mkdir(exist_ok=True)
    db_path = tmp_path / "db.json"

    monkeypatch.setattr(scanner, "ONEDRIVE_MEETINGS_DIR", recordings)
    monkeypatch.setattr(scanner, "PROCESSED_DB", db_path)

    f = recordings / "a.mp4"
    f.write_bytes(b"data")

    files = scanner.find_new_mp4s()
    assert f in files

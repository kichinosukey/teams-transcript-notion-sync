from teams_transcript_notion_sync.noise_filter import remove_fake_speaker_labels


def test_remove_fake_speaker_labels_with_timestamp_lines():
    """タイムスタンプ行付きの発言ラベルを正しく削除できることを確認する。"""
    text = (
        "[00:10:51.000 --> 00:10:53.000]  おだしょー:分かりました\n"
        "[00:40:57.120 --> 00:41:08.120]  吉田:そうだね。\n"
    )
    assert remove_fake_speaker_labels(text) == (
        "[00:10:51.000 --> 00:10:53.000]  分かりました\n"
        "[00:40:57.120 --> 00:41:08.120]  そうだね。\n"
    )


def test_remove_fake_speaker_labels_without_timestamp_lines():
    """タイムスタンプ行なしの発言ラベルを正しく削除できることを確認する。"""
    text = "りなたむ:分かりました\n通常の行はそのまま\n"
    assert remove_fake_speaker_labels(text) == "分かりました\n通常の行はそのまま\n"


def test_remove_fake_speaker_labels_does_not_strip_midline_colon():
    """行中のコロンは削除しないことを確認する。"""
    text = "[00:00:01.000 --> 00:00:02.000]  URL: https://example.com\n"
    # 「URL:」はラベルっぽく見えるが、これを削ると意味が壊れる可能性がある。
    # 現状のヒューリスティックでは短いラベルも削除対象なので、
    # URL のようなケースを温存したい場合は、条件強化の余地がある。
    assert remove_fake_speaker_labels(text) == text

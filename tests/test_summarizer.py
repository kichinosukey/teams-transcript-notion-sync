from teams_transcript_notion_sync import summarizer


def test_validate_accepts_valid_table():
    """ValidなMarkdownテーブルを受け入れることを確認する。"""
    ok, normalized, reason = summarizer.validate_and_normalize_markdown_table(
        "| トピック | 要約（議事録） | 根拠となる発言（引用） |\n|---|---|---|\n| A | B | C |\n"
    )
    assert ok
    assert reason == ""
    assert normalized == (
        "| トピック | 要約（議事録） | 根拠となる発言（引用） |\n"
        "|---|---|---|\n"
        "| A | B | C |\n"
    )


def test_validate_rejects_non_table_text_mixed_in():
    """テーブル外のテキストが混在している場合に拒否されることを確認する。"""
    ok, _normalized, reason = summarizer.validate_and_normalize_markdown_table(
        "前置き\n| トピック | 要約（議事録） | 根拠となる発言（引用） |\n|---|---|---|\n| A | B | C |\n"
    )
    assert not ok
    assert reason == "non_table_text_detected"


def test_validate_rejects_missing_separator():
    """区切り行がない場合に拒否されることを確認する。"""
    ok, _normalized, reason = summarizer.validate_and_normalize_markdown_table(
        "| トピック | 要約（議事録） | 根拠となる発言（引用） |\n| A | B | C |\n"
    )
    assert not ok
    assert reason == "separator_missing_or_invalid"


def test_validate_rejects_header_not_three_columns():
    """ヘッダ行が3列でない場合に拒否されることを確認する。"""
    ok, _normalized, reason = summarizer.validate_and_normalize_markdown_table(
        "| トピック | 内容 |\n|---|---|\n| A | B |\n"
    )
    assert not ok
    assert reason == "header_not_three_columns"


def test_normalize_fills_missing_third_column():
    """3列目が欠落している場合に空文字で埋めることを確認する。"""
    ok, normalized, reason = summarizer.validate_and_normalize_markdown_table(
        "| トピック | 要約（議事録） | 根拠となる発言（引用） |\n|---|---|---|\n| A | B |\n"
    )
    assert ok
    assert reason == ""
    assert normalized == (
        "| トピック | 要約（議事録） | 根拠となる発言（引用） |\n"
        "|---|---|---|\n"
        "| A | B |  |\n"
    )


def test_normalize_merges_extra_columns_into_third():
    """4列以上ある場合に3列目に結合することを確認する。"""
    ok, normalized, reason = summarizer.validate_and_normalize_markdown_table(
        "| トピック | 要約（議事録） | 根拠となる発言（引用） |\n|---|---|---|\n| A | B | C | D |\n"
    )
    assert ok
    assert reason == ""
    assert normalized == (
        "| トピック | 要約（議事録） | 根拠となる発言（引用） |\n"
        "|---|---|---|\n"
        "| A | B | C / D |\n"
    )


def test_normalize_replaces_inner_pipes_and_newlines():
    """セル内の改行を空白に、パイプを全角に置換することを確認する。"""
    ok, normalized, reason = summarizer.validate_and_normalize_markdown_table(
        "| トピック | 要約（議事録） | 根拠となる発言（引用） |\n"
        "|---|---|---|\n"
        "| A | B | C |\n"
        "| D | E|\nF | G |\n"
    )
    assert ok
    assert reason == ""
    # 行またぎの結合は行わないため、E行は独立行として補完される
    assert normalized == (
        "| トピック | 要約（議事録） | 根拠となる発言（引用） |\n"
        "|---|---|---|\n"
        "| A | B | C |\n"
        "| D | E |  |\n"
        "| F | G |  |\n"
    )

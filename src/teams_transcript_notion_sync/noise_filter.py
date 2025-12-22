"""
Transcript noise filtering utilities.

背景
----
Teams + whisper.cpp の文字起こしでは、以下のように「存在しないはずの発話者ラベル」
が行頭に混ざることがあります。

例:
    [00:10:51.000 --> 00:10:53.000]  おだしょー:分かりました
    [00:40:57.120 --> 00:41:08.120]  吉田:そうだね。…

ここでの「おだしょー:」「りなたむ:」「吉田:」のようなラベルは、
本来の文字起こしには不要なノイズとして扱い、行頭から削除したい。

方針
----
1) タイムスタンプは残す。
2) 行頭に「短いラベル + コロン(: / ：) + 発話」の形がある場合のみ削除する。
3) それ以外の行はそのまま残す（誤検出を避ける）。

設計上の注意
------------
このフィルターは「正解の発話者名リスト」を持たないヒューリスティックです。
そのため、ラベルと見なす条件はできるだけ控えめにしてあります。
"""

from __future__ import annotations

import re


# Teams の txt/vtt 出力に見られるタイムスタンプ行の前置きを検出する。
# 先頭の "[00:10:51.000 --> 00:10:53.000]" 部分は残したいので、2グループに分ける。
_TIMESTAMP_PREFIX_RE = re.compile(
    r"^(\s*\[[0-9:.]+\s*-->\s*[0-9:.]+\]\s*)(.*)$"
)

# 行頭の「発話者ラベルっぽいもの」を検出する。
#
# 条件:
# - ラベル長は 1〜20 文字程度（異常に長いものは除外）
# - ひらがな/カタカナ/漢字/英数/一部記号（_ -）/長音記号(ー)を許可
# - ":" または "：" に続いて、空白でない文字が1文字以上（発話がある）
#
# これにより、例えば「URL: https://…」のような行内コロンは
# 行頭かつ短いラベルでない限りマッチしにくくする。
_SPEAKER_LABEL_RE = re.compile(
    r"^(?P<label>[A-Za-z0-9_\-\u3040-\u30ff\u3400-\u9fff\u30fc]{1,20})\s*[:：](?P<utterance>\S.*)$"
)


def remove_speaker_label_noise(text: str) -> str:
    """
    行頭の「発話者ラベル:」ノイズを削除したテキストを返す。

    Args:
        text: 文字起こし全文

    Returns:
        フィルター適用後のテキスト。

    挙動:
    - タイムスタンプ付き行:
        "[...]" 以降の先頭にラベルがあれば、それだけ取り除く。
    - タイムスタンプなし行:
        行頭にラベルがあれば、それだけ取り除く。
    - マッチしない行:
        そのまま返す。
    """
    cleaned_lines: list[str] = []

    for line in text.splitlines():
        # 1) まずタイムスタンプ前置きの有無を見る
        m_ts = _TIMESTAMP_PREFIX_RE.match(line)
        if m_ts:
            prefix, rest = m_ts.group(1), m_ts.group(2).lstrip()
            m_label = _SPEAKER_LABEL_RE.match(rest)
            if m_label:
                # タイムスタンプは残してラベルだけ落とす
                line = prefix + m_label.group("utterance")
        else:
            # タイムスタンプが無い場合は、元のインデントだけ保持する
            rest = line.lstrip()
            m_label = _SPEAKER_LABEL_RE.match(rest)
            if m_label:
                leading_ws = line[: len(line) - len(rest)]
                line = leading_ws + m_label.group("utterance")

        cleaned_lines.append(line)

    # 入力の末尾に改行があった場合は保持する
    result = "\n".join(cleaned_lines)
    if text.endswith("\n"):
        result += "\n"
    return result


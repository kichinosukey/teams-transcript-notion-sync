import teams_transcript_notion_sync.speaker_annotator as sa


def test_parse_srt_extracts_segments():
    srt_text = (
        "1\n"
        "00:00:00,000 --> 00:00:02,000\n"
        "こんにちは\n"
        "\n"
        "2\n"
        "00:00:02,500 --> 00:00:04,000\n"
        "はい\n"
        "\n"
    )
    segments = sa.parse_srt(srt_text)
    assert len(segments) == 2
    assert segments[0].start == 0.0
    assert segments[0].end == 2.0
    assert segments[0].text == "こんにちは"
    assert segments[1].start == 2.5
    assert segments[1].end == 4.0
    assert segments[1].text == "はい"


def test_resolve_labels_prefers_env_labels(monkeypatch):
    monkeypatch.setattr(sa, "SPEAKER_COUNT", 2)
    monkeypatch.setattr(sa, "SPEAKER_LABELS", ["Alice", "Bob"])
    mapping = sa._resolve_labels(["SPEAKER_00", "SPEAKER_01"])
    assert mapping["SPEAKER_00"] == "Alice"
    assert mapping["SPEAKER_01"] == "Bob"


def test_pick_speaker_uses_max_overlap():
    segment = sa.TranscriptSegment(start=1.0, end=3.0, text="test")
    diarization = [
        sa.SpeakerSegment(start=0.0, end=1.5, speaker="SPEAKER_00"),
        sa.SpeakerSegment(start=1.6, end=4.0, speaker="SPEAKER_01"),
    ]
    assert sa._pick_speaker(segment, diarization) == "SPEAKER_01"

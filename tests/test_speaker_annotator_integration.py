import os
import wave

import pytest

import teams_transcript_notion_sync.speaker_annotator as sa


def _write_silence_wav(path, seconds: float = 1.0, sample_rate: int = 16000):
    frames = int(seconds * sample_rate)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * frames)


@pytest.mark.integration
def test_diarize_audio_runs_with_real_model(tmp_path):
    if os.environ.get("RUN_PYANNOTE_INTEGRATION") != "1":
        pytest.skip("Set RUN_PYANNOTE_INTEGRATION=1 to run this test.")
    if not os.environ.get("HF_TOKEN"):
        pytest.skip("HF_TOKEN is required for pyannote integration test.")

    wav_path = tmp_path / "silence.wav"
    _write_silence_wav(wav_path)

    segments = sa.diarize_audio(wav_path)
    assert isinstance(segments, list)
    if segments:
        assert segments[0].start <= segments[0].end

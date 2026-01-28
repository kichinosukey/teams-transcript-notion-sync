# src/teams_transcript_notion_sync/speaker_annotator.py
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .config import SPEAKER_COUNT, SPEAKER_LABELS, PYANNOTE_MODEL, HF_TOKEN


@dataclass(frozen=True)
class TranscriptSegment:
    """WhisperのSRTから抽出したセグメント。

    Args:
        start (float): 開始秒。
        end (float): 終了秒。
        text (str): セグメントの発話テキスト。
    """

    start: float
    end: float
    text: str


@dataclass(frozen=True)
class SpeakerSegment:
    """話者分離のセグメント。

    Args:
        start (float): 開始秒。
        end (float): 終了秒。
        speaker (str): 話者ID。
    """

    start: float
    end: float
    speaker: str


def _parse_srt_timestamp(value: str) -> float:
    """SRTの時刻文字列を秒に変換する。

    Args:
        value (str): `HH:MM:SS,mmm` 形式の時刻。

    Returns:
        float: 秒単位の時刻。
    """
    hh, mm, rest = value.split(":")
    ss, ms = rest.split(",")
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000.0


def parse_srt(srt_text: str) -> list[TranscriptSegment]:
    """SRT文字列をセグメントに分解する。

    Args:
        srt_text (str): SRT形式の全文テキスト。

    Returns:
        list[TranscriptSegment]: 解析結果のセグメント一覧。
    """
    segments: list[TranscriptSegment] = []
    # SRTを行単位で処理する
    lines = [line.rstrip("\n") for line in srt_text.splitlines()]
    i = 0
    while i < len(lines):
        # セグメント番号行をスキップ
        line = lines[i].strip()
        # 空行はスキップ
        if not line:
            i += 1
            continue
        # セグメント番号行の想定で数字か確認
        if line.isdigit():
            i += 1
        # 時刻行を処理
        if i >= len(lines):
            break
        time_line = lines[i].strip()
        # 時刻行の形式確認
        if "-->" not in time_line:
            i += 1
            continue
        # 時刻を解析、テキスト行を収集
        start_raw, end_raw = [x.strip() for x in time_line.split("-->")]
        # 開始時刻を秒に変換
        start = _parse_srt_timestamp(start_raw)
        # 終了時刻を秒に変換
        end = _parse_srt_timestamp(end_raw)
        # テキスト行を収集、次のセグメントへ
        i += 1
        text_lines = []
        while i < len(lines) and lines[i].strip():
            text_lines.append(lines[i].strip())
            i += 1
        # テキスト行を結合してセグメントを追加
        text = " ".join(text_lines).strip()
        # 空テキストは無視
        if text:
            segments.append(TranscriptSegment(start=start, end=end, text=text))
    return segments


def _load_diarization_pipeline():
    """pyannoteの話者分離パイプラインをロードする。

    Returns:
        pyannote.audio.Pipeline: 事前学習済みパイプライン。

    Raises:
        RuntimeError: 依存パッケージ未インストール、またはトークン未設定の場合。
    """
    try:
        from pyannote.audio import Pipeline
    except ImportError as exc:
        raise RuntimeError(
            "pyannote.audio is not installed. Install it to enable speaker annotation."
        ) from exc

    # PyTorchの安全なグローバル登録を追加
    # これが無いとWeightsOnlyLoadErrorになる場合がある
    try:
        import torch

        from pyannote.audio.core import task as task_module

        allowlist = [torch.torch_version.TorchVersion]
        for name in ("Specifications", "Problem", "Resolution"):
            candidate = getattr(task_module, name, None)
            if candidate is not None:
                allowlist.append(candidate)

        torch.serialization.add_safe_globals(allowlist)
    except Exception:
        # PyTorch未導入などのケースはpyannote側でエラーになるため握りつぶさない
        pass

    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN is not set. Set it to enable speaker annotation.")

    try:
        return Pipeline.from_pretrained(PYANNOTE_MODEL, token=HF_TOKEN)
    except TypeError:
        return Pipeline.from_pretrained(PYANNOTE_MODEL, use_auth_token=HF_TOKEN)


def diarize_audio(wav_path: Path) -> list[SpeakerSegment]:
    """音声ファイルを話者分離してセグメントを返す。

    Args:
        wav_path (Path): 解析対象のWAVファイルパス。

    Returns:
        list[SpeakerSegment]: 話者セグメントの一覧。
    """
    # 話者分離パイプラインをロード
    pipeline = _load_diarization_pipeline()
    # 音声ファイルを話者分離
    diarization = pipeline(
        {"audio": str(wav_path)},
        num_speakers=SPEAKER_COUNT,
    )

    segments: list[SpeakerSegment] = []

    def _iter_tracks_from_output(output):
        visited: set[int] = set()
        stack = [output]
        while stack:
            obj = stack.pop()
            obj_id = id(obj)
            if obj_id in visited:
                continue
            visited.add(obj_id)

            try:
                method = getattr(obj, "itertracks", None)
            except Exception:
                method = None
            if callable(method):
                try:
                    return method(yield_label=True)
                except Exception:
                    pass

            if isinstance(obj, dict):
                stack.extend(obj.values())
                continue

            if hasattr(obj, "__dict__"):
                stack.extend(obj.__dict__.values())

            slots = getattr(obj, "__slots__", None)
            if slots:
                for name in slots:
                    try:
                        stack.append(getattr(obj, name))
                    except Exception:
                        pass

            for name in ("annotation", "diarization", "output"):
                try:
                    stack.append(getattr(obj, name))
                except Exception:
                    continue
        return None

    iterable = _iter_tracks_from_output(diarization)
    if iterable is None:
        raise RuntimeError(
            "Unsupported diarization output type; cannot iterate speaker tracks. "
            f"type={type(diarization)}"
        )

    for segment, _, speaker in iterable:
        segments.append(
            SpeakerSegment(start=segment.start, end=segment.end, speaker=speaker)
        )
    return segments


def _resolve_labels(speaker_ids: Iterable[str]) -> dict[str, str]:
    """話者IDを表示用ラベルに変換する。

    Args:
        speaker_ids (Iterable[str]): diarizationの話者ID列。

    Returns:
        dict[str, str]: 話者IDと表示ラベルの対応表。
    """
    ordered_ids: list[str] = []
    for speaker_id in speaker_ids:
        if speaker_id not in ordered_ids:
            ordered_ids.append(speaker_id)

    count = SPEAKER_COUNT or len(ordered_ids)
    labels = list(SPEAKER_LABELS)
    while len(labels) < count:
        labels.append(f"Speaker {len(labels) + 1}")

    mapping: dict[str, str] = {}
    for idx, speaker_id in enumerate(ordered_ids):
        if idx < len(labels):
            mapping[speaker_id] = labels[idx]
        else:
            mapping[speaker_id] = f"Speaker {idx + 1}"
    return mapping


def _pick_speaker(
    segment: TranscriptSegment, diarization: list[SpeakerSegment]
) -> str | None:
    """発話セグメントに最も重なる話者IDを選ぶ。

    Args:
        segment (TranscriptSegment): Whisperのセグメント。
        diarization (list[SpeakerSegment]): 話者セグメント一覧。

    Returns:
        str | None: 重なりが最大の話者ID。重なりが無い場合はNone。
    """
    best_speaker = None
    best_overlap = 0.0
    for speaker_segment in diarization:
        overlap_start = max(segment.start, speaker_segment.start)
        overlap_end = min(segment.end, speaker_segment.end)
        overlap = max(0.0, overlap_end - overlap_start)
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = speaker_segment.speaker
    return best_speaker


def annotate_transcript_with_speakers(wav_path: Path, srt_path: Path) -> str:
    """SRTと話者分離結果を突合して話者付き全文を生成する。

    Args:
        wav_path (Path): 話者分離に使うWAVファイルパス。
        srt_path (Path): WhisperのSRT出力パス。

    Returns:
        str: `Speaker X: 発話` 形式で連結した全文テキスト。
    """
    srt_text = srt_path.read_text()
    transcript_segments = parse_srt(srt_text)
    if not transcript_segments:
        return ""

    diarization = diarize_audio(wav_path)
    label_map = _resolve_labels([seg.speaker for seg in diarization])

    lines = []
    for segment in transcript_segments:
        speaker_id = _pick_speaker(segment, diarization)
        speaker_label = label_map.get(speaker_id, "Unknown")
        lines.append(f"{speaker_label}: {segment.text}")
    return "\n".join(lines).strip() + "\n"

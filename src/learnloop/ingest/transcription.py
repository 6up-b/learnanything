"""Audio transcription via an OpenAI-compatible /audio/transcriptions endpoint.

The default audio-ingest path (``[ingest.audio]``): the file is uploaded to
``{transcription_base_url}/audio/transcriptions`` (OpenAI whisper-1, Groq, a
local faster-whisper server, ...) with ``response_format="verbose_json"`` so
per-segment timestamps come back and the normalizer can build the same
``time_range`` IR the caption/transcript paths use. Endpoints that reject
verbose_json (e.g. gpt-4o-transcribe) degrade to a single untimestamped cue.

Offline tests fake the ``openai`` module (tests/openai_fakes.py) — the import
is lazy, mirroring ai/openai_chat.py.
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import Any

from learnloop.config import AudioIngestConfig
from learnloop.ingest.transcripts import TranscriptCue


class TranscriptionUnavailable(Exception):
    """Transcription cannot run at all: missing openai package or API key."""


class TranscriptionFailed(Exception):
    """The endpoint errored at runtime (auth, model, network, bad audio)."""


@dataclass(frozen=True)
class TranscriptionResult:
    cues: list[TranscriptCue]
    language: str | None
    duration_seconds: float | None
    model: str
    # False when the endpoint rejected verbose_json and we fell back to a
    # single whole-file cue without timestamps.
    timestamped: bool


def _segment_value(segment: Any, key: str, default: Any = None) -> Any:
    if isinstance(segment, dict):
        return segment.get(key, default)
    return getattr(segment, key, default)


def _cues_from_segments(segments: list[Any]) -> list[TranscriptCue]:
    cues: list[TranscriptCue] = []
    for segment in segments:
        text = str(_segment_value(segment, "text", "") or "").strip()
        if not text:
            continue
        cues.append(
            TranscriptCue(
                start=float(_segment_value(segment, "start", 0.0) or 0.0),
                end=float(_segment_value(segment, "end", 0.0) or 0.0),
                text=text,
                speaker=None,
            )
        )
    return cues


def transcribe_audio(raw_bytes: bytes, *, filename: str, config: AudioIngestConfig) -> TranscriptionResult:
    api_key = os.environ.get(config.transcription_api_key_env)
    if not api_key:
        raise TranscriptionUnavailable(
            f"Environment variable {config.transcription_api_key_env} is required for audio transcription."
        )
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise TranscriptionUnavailable("The openai package is required for audio transcription.") from exc

    client = OpenAI(
        api_key=api_key,
        base_url=config.transcription_base_url,
        timeout=config.timeout_seconds,
    )

    def _create(response_format: str) -> Any:
        kwargs: dict[str, Any] = {
            "model": config.transcription_model,
            "file": (filename, io.BytesIO(raw_bytes)),
            "response_format": response_format,
        }
        if config.language:
            kwargs["language"] = config.language
        return client.audio.transcriptions.create(**kwargs)

    try:
        response = _create("verbose_json")
    except Exception as exc:  # noqa: BLE001 — SDK error taxonomy varies per server
        if "response_format" not in str(exc):
            raise TranscriptionFailed(str(exc)) from exc
        # gpt-4o-transcribe-style models reject verbose_json; retry degraded.
        try:
            response = _create("json")
        except Exception as retry_exc:  # noqa: BLE001
            raise TranscriptionFailed(str(retry_exc)) from retry_exc
        text = str(getattr(response, "text", "") or "").strip()
        if not text:
            raise TranscriptionFailed("transcription endpoint returned no text")
        duration = getattr(response, "duration", None)
        end = float(duration) if duration else 0.0
        return TranscriptionResult(
            cues=[TranscriptCue(start=0.0, end=end, text=text, speaker=None)],
            language=getattr(response, "language", None),
            duration_seconds=float(duration) if duration else None,
            model=config.transcription_model,
            timestamped=False,
        )

    segments = getattr(response, "segments", None) or []
    cues = _cues_from_segments(list(segments))
    if not cues:
        text = str(getattr(response, "text", "") or "").strip()
        if not text:
            raise TranscriptionFailed("transcription endpoint returned no segments or text")
        duration = getattr(response, "duration", None)
        cues = [TranscriptCue(start=0.0, end=float(duration) if duration else 0.0, text=text, speaker=None)]
    duration = getattr(response, "duration", None)
    return TranscriptionResult(
        cues=cues,
        language=getattr(response, "language", None),
        duration_seconds=float(duration) if duration else None,
        model=config.transcription_model,
        timestamped=bool(segments),
    )

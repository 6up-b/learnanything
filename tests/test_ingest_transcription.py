from __future__ import annotations

import sys
import types

import pytest

from learnloop.config import AudioIngestConfig
from learnloop.ingest.transcription import (
    TranscriptionFailed,
    TranscriptionUnavailable,
    transcribe_audio,
)

from tests.openai_fakes import fake_verbose_transcription, install_fake_openai


def _config(**overrides) -> AudioIngestConfig:
    return AudioIngestConfig(**overrides)


def test_transcribe_audio_parses_segments_and_records_request(monkeypatch):
    fake = install_fake_openai(
        monkeypatch,
        transcriptions=(fake_verbose_transcription((0.0, 2.5, "hello"), (2.5, 6.0, "world")),),
    )
    monkeypatch.setenv("LEARNLOOP_TRANSCRIPTION_API_KEY", "tr-secret")

    result = transcribe_audio(b"fake-mp3-bytes", filename="lecture.mp3", config=_config())

    assert [cue.text for cue in result.cues] == ["hello", "world"]
    assert result.cues[0].start == 0.0 and result.cues[1].end == 6.0
    assert result.language == "en"
    assert result.duration_seconds == 6.0
    assert result.timestamped is True
    assert result.model == "whisper-1"
    instance = fake.instances[0]
    assert instance.kwargs["api_key"] == "tr-secret"
    assert instance.kwargs["base_url"] == "https://api.openai.com/v1"
    request = instance.transcription_requests[0]
    assert request["model"] == "whisper-1"
    assert request["response_format"] == "verbose_json"
    assert "language" not in request


def test_transcribe_audio_accepts_dict_segments_and_language_hint(monkeypatch):
    fake = install_fake_openai(
        monkeypatch,
        transcriptions=(
            fake_verbose_transcription({"start": 0.0, "end": 3.0, "text": "hola"}, language="es"),
        ),
    )
    monkeypatch.setenv("LEARNLOOP_TRANSCRIPTION_API_KEY", "tr-secret")

    result = transcribe_audio(b"x", filename="a.wav", config=_config(language="es"))

    assert [cue.text for cue in result.cues] == ["hola"]
    assert result.language == "es"
    assert fake.instances[0].transcription_requests[0]["language"] == "es"


def test_transcribe_audio_missing_key_raises_unavailable(monkeypatch):
    install_fake_openai(monkeypatch, transcriptions=())
    monkeypatch.delenv("LEARNLOOP_TRANSCRIPTION_API_KEY", raising=False)

    with pytest.raises(TranscriptionUnavailable, match="LEARNLOOP_TRANSCRIPTION_API_KEY"):
        transcribe_audio(b"x", filename="a.mp3", config=_config())


def test_transcribe_audio_missing_package_raises_unavailable(monkeypatch):
    monkeypatch.setenv("LEARNLOOP_TRANSCRIPTION_API_KEY", "tr-secret")
    monkeypatch.setitem(sys.modules, "openai", None)

    with pytest.raises(TranscriptionUnavailable, match="openai package"):
        transcribe_audio(b"x", filename="a.mp3", config=_config())


def test_transcribe_audio_api_error_raises_failed(monkeypatch):
    install_fake_openai(monkeypatch, transcriptions=(RuntimeError("server exploded"),))
    monkeypatch.setenv("LEARNLOOP_TRANSCRIPTION_API_KEY", "tr-secret")

    with pytest.raises(TranscriptionFailed, match="server exploded"):
        transcribe_audio(b"x", filename="a.mp3", config=_config())


def test_transcribe_audio_degrades_when_verbose_json_rejected(monkeypatch):
    fake = install_fake_openai(
        monkeypatch,
        transcriptions=(
            RuntimeError("400: response_format 'verbose_json' is not supported"),
            types.SimpleNamespace(text="whole transcript", duration=42.0, language="en"),
        ),
    )
    monkeypatch.setenv("LEARNLOOP_TRANSCRIPTION_API_KEY", "tr-secret")

    result = transcribe_audio(
        b"x", filename="a.m4a", config=_config(transcription_model="gpt-4o-transcribe")
    )

    assert result.timestamped is False
    assert len(result.cues) == 1
    assert result.cues[0].text == "whole transcript"
    assert result.cues[0].end == 42.0
    requests = fake.instances[0].transcription_requests
    assert [request["response_format"] for request in requests] == ["verbose_json", "json"]

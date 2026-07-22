from __future__ import annotations

import base64
import json

import pytest

from learnloop.ai.multimodal import (
    MediaTranscript,
    MediaTranscriptionContext,
    PdfExtractionContextNative,
    chat_audio_format,
    strip_markdown_fences,
    supports_input_modality,
)
from learnloop.ai.openai_chat import OpenAIChatProviderClient
from learnloop.ai.openrouter import OpenRouterProviderClient
from learnloop.config import AIProviderConfig

from tests.openai_fakes import install_fake_openai


def _profile(**overrides) -> AIProviderConfig:
    settings = {
        "type": "openai_chat",
        "base_url": "https://api.example.com/v1",
        "api_key_env": "EXAMPLE_API_KEY",
        "model": "example/multimodal",
        "response_format": "json_object",
    }
    settings.update(overrides)
    return AIProviderConfig(**settings)


def _transcript_json() -> str:
    return json.dumps(
        {
            "segments": [
                {"start_seconds": 0.0, "end_seconds": 3.5, "speaker": None, "text": "hello"},
                {"start_seconds": 3.5, "end_seconds": 8.0, "speaker": "A", "text": "world"},
            ],
            "language": "en",
        }
    )


def test_run_media_transcription_builds_input_audio_parts(monkeypatch):
    fake = install_fake_openai(monkeypatch, _transcript_json())
    monkeypatch.setenv("EXAMPLE_API_KEY", "secret")
    client = OpenAIChatProviderClient("example", _profile())

    result = client.run_media_transcription(
        MediaTranscriptionContext(media_bytes=b"raw-audio", media_format="mp3", title="Lecture 1")
    )

    assert isinstance(result, MediaTranscript)
    assert [segment.text for segment in result.segments] == ["hello", "world"]
    assert result.language == "en"
    request = fake.instances[0].requests[0]
    parts = request["messages"][1]["content"]
    assert parts[0]["type"] == "text"
    assert "Transcribe" in parts[0]["text"]
    assert "Lecture 1" in parts[0]["text"]
    assert parts[1]["type"] == "input_audio"
    assert parts[1]["input_audio"]["format"] == "mp3"
    assert base64.b64decode(parts[1]["input_audio"]["data"]) == b"raw-audio"
    assert request["response_format"] == {"type": "json_object"}


def test_run_media_transcription_repairs_invalid_json_text_only(monkeypatch):
    fake = install_fake_openai(monkeypatch, "not json", _transcript_json())
    monkeypatch.setenv("EXAMPLE_API_KEY", "secret")
    client = OpenAIChatProviderClient("example", _profile())

    result = client.run_media_transcription(
        MediaTranscriptionContext(media_bytes=b"raw-audio", media_format="wav")
    )

    assert len(result.segments) == 2
    requests = fake.instances[0].requests
    assert len(requests) == 2
    # The repair round is text-only: the audio is never re-uploaded.
    repair_content = requests[1]["messages"][1]["content"]
    assert isinstance(repair_content, str)
    assert "Repair the following model output" in repair_content


def test_run_media_markdown_sends_file_part_and_suppresses_response_format(monkeypatch):
    fake = install_fake_openai(monkeypatch, "```markdown\n# Chapter 1\n\nBody text.\n```")
    monkeypatch.setenv("EXAMPLE_API_KEY", "secret")
    client = OpenAIChatProviderClient("example", _profile())

    markdown = client.run_media_markdown(
        PdfExtractionContextNative(media_bytes=b"%PDF-1.4", filename="chapter.pdf")
    )

    assert markdown == "# Chapter 1\n\nBody text."
    request = fake.instances[0].requests[0]
    # The profile's json_object response_format must NOT apply to markdown output.
    assert "response_format" not in request
    parts = request["messages"][1]["content"]
    assert parts[1]["type"] == "file"
    assert parts[1]["file"]["filename"] == "chapter.pdf"
    assert parts[1]["file"]["file_data"].startswith("data:application/pdf;base64,")


def test_openrouter_inherits_media_methods_with_headers(monkeypatch):
    fake = install_fake_openai(monkeypatch, _transcript_json())
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    client = OpenRouterProviderClient(
        "openrouter",
        AIProviderConfig(type="openrouter", model="google/gemini-2.5-flash", response_format="json_object"),
    )

    result = client.run_media_transcription(
        MediaTranscriptionContext(media_bytes=b"x", media_format="mp3")
    )

    assert isinstance(result, MediaTranscript)
    assert fake.instances[0].kwargs["default_headers"] == {"X-Title": "LearnLoop"}


def test_supports_input_modality_and_audio_format_helpers():
    profile = AIProviderConfig(type="openrouter", model="x", input_modalities=["audio"])
    assert supports_input_modality(profile, "audio") is True
    assert supports_input_modality(profile, "pdf") is False
    assert chat_audio_format("talk.mp3") == "mp3"
    assert chat_audio_format("talk.WAV") == "wav"
    assert chat_audio_format("talk.flac") is None
    assert chat_audio_format("noext") is None


def test_strip_markdown_fences_variants():
    assert strip_markdown_fences("plain # md") == "plain # md"
    assert strip_markdown_fences("```\nbody\n```") == "body"
    assert strip_markdown_fences("```markdown\n# H\n\ntext\n```") == "# H\n\ntext"
    # Inner fences survive when the whole document isn't wrapped.
    inner = "# H\n\n```python\ncode\n```\n\ntail"
    assert strip_markdown_fences(inner) == inner


def test_empty_markdown_raises(monkeypatch):
    install_fake_openai(monkeypatch, "```\n\n```")
    monkeypatch.setenv("EXAMPLE_API_KEY", "secret")
    client = OpenAIChatProviderClient("example", _profile())

    from learnloop.codex.client import CodexUnavailable

    with pytest.raises(CodexUnavailable, match="empty"):
        client.run_media_markdown(
            PdfExtractionContextNative(media_bytes=b"%PDF-1.4", filename="c.pdf")
        )

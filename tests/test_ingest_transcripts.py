"""Transcript-aware ingest: WebVTT/SRT detection, cue parsing, and the
``transcript_to_ir`` normalizer (time_range units, speaker-labelled turn blocks).
"""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.ingest.extractors.normalizers import transcript_to_ir
from learnloop.ingest.resolution import resolve_source
from learnloop.ingest.transcripts import (
    TranscriptCue,
    detect_transcript_format,
    parse_transcript,
)
from learnloop.services.ingest_runner import (
    FetchedBytes,
    default_extract,
    default_extraction_identity,
)

VTT = """WEBVTT

NOTE this block is metadata and must be skipped

1
00:00:01.000 --> 00:00:04.000
<v Alice>Welcome to the lecture.

2
00:00:04.500 --> 00:00:08.000
Today we cover eigenvalues.

3
00:00:20.000 --> 00:00:24.000
<v Bob>Quick question about the previous slide.
"""

SRT = """1
00:00:01,000 --> 00:00:03,500
ALICE: Determinants measure volume scaling.

2
00:00:04,000 --> 00:00:07,000
So a zero determinant collapses space.
"""


def test_detects_vtt_and_srt_from_head() -> None:
    assert detect_transcript_format(VTT[:200]) == "vtt"
    assert detect_transcript_format(SRT[:200]) == "srt"
    assert detect_transcript_format("# Just a markdown file\n\nProse.") is None
    # A prose file that merely mentions an arrow is not a transcript.
    assert detect_transcript_format("intro\nA --> B\n") is None


def test_parse_vtt_keeps_timing_speakers_and_continuation() -> None:
    cues = parse_transcript(VTT)
    assert [c.text for c in cues] == [
        "Welcome to the lecture.",
        "Today we cover eigenvalues.",
        "Quick question about the previous slide.",
    ]
    assert cues[0].start == 1.0 and cues[0].end == 4.0
    assert cues[0].speaker == "Alice"
    # Un-voiced continuation cue keeps the previous speaker.
    assert cues[1].speaker == "Alice"
    assert cues[2].speaker == "Bob"


def test_parse_srt_all_caps_speaker_prefix() -> None:
    cues = parse_transcript(SRT)
    assert cues[0].speaker == "ALICE"
    assert cues[0].text == "Determinants measure volume scaling."
    assert cues[1].speaker == "ALICE"  # continuation
    assert cues[0].start == 1.0 and cues[1].end == 7.0


def test_transcript_ir_units_carry_time_range_locators() -> None:
    # Two speakers with a long gap → distinct segments once the minimum segment
    # duration is met; every unit locator is a time_range.
    cues = [
        TranscriptCue(start=i * 10.0, end=i * 10.0 + 8.0, text=f"alice segment {i}", speaker="Alice")
        for i in range(16)
    ] + [
        TranscriptCue(start=400.0 + i * 10.0, end=400.0 + i * 10.0 + 8.0, text=f"bob segment {i}", speaker="Bob")
        for i in range(16)
    ]
    ir = transcript_to_ir(cues, title="Interview")
    assert ir.extractor == "transcript"
    assert len(ir.units) >= 2
    for unit in ir.units:
        assert unit.locator["scheme"] == "time_range"
        assert unit.locator["end"] > unit.locator["start"]
    # Speaker labels survive on the block text.
    assert any(block.text.startswith("Alice: ") for block in ir.blocks)
    assert any(block.text.startswith("Bob: ") for block in ir.blocks)
    assert all(block.block_type == "Caption" for block in ir.blocks)
    # Units partition the blocks in order.
    spanned = [sid for unit in ir.units for sid in unit.span_ids]
    assert spanned == [block.span_id for block in ir.blocks]


def test_default_extract_routes_caption_text_to_transcript_ir() -> None:
    ctx = SimpleNamespace(payload={"title": "Lecture 3"}, job={})
    fetched = FetchedBytes(raw_bytes=VTT.encode(), content_type="text/plain", original_uri="lecture.vtt", retrieved_at="2026-07-20T00:00:00Z")
    ir = default_extract(fetched, "textfile", ctx)
    assert ir.extractor == "transcript"
    assert ir.units and ir.units[0].locator["scheme"] == "time_range"

    identity = default_extraction_identity(fetched, "textfile", ctx)
    assert identity["extractor"] == "transcript"
    assert identity["extractor_version"] == ir.extractor_version

    # Plain prose still takes the text path with the same identity agreement.
    prose = FetchedBytes(raw_bytes=b"# Notes\n\nParagraph one.", content_type="text/plain", original_uri="notes.md", retrieved_at="2026-07-20T00:00:00Z")
    assert default_extract(prose, "textfile", ctx).extractor == "text"
    assert default_extraction_identity(prose, "textfile", ctx)["extractor"] == "text"


def test_resolution_classifies_caption_files_as_textfile() -> None:
    assert resolve_source("lecture.vtt").category == "textfile"
    assert resolve_source("lecture.srt").category == "textfile"

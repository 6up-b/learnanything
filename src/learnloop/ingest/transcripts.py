"""Caption/transcript file parsing (WebVTT + SRT) for transcript-aware ingest.

A dropped ``.vtt``/``.srt`` (or a text file that starts with caption cues) used to
fall through to ``markdown_to_ir`` where cue timestamps and speaker labels were
treated as ordinary prose. This module recognizes the two caption formats and
parses them into timed cues so the normalizer can build an IR whose units carry
``time_range`` locators — the same locator scheme the YouTube caption path uses,
so downstream citation/resolution machinery needs nothing new.

Detection is HEAD-BASED (first few KB only) so ``default_extraction_identity``
and ``default_extract`` agree on the chosen extractor without decoding the whole
payload twice.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# HH:MM:SS.mmm / MM:SS.mmm (VTT uses ".", SRT uses ",")
_TIMESTAMP = r"(?:\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{3}"
_VTT_HEADER_RE = re.compile(r"^﻿?WEBVTT(?:[ \t].*)?$")
_CUE_TIMING_RE = re.compile(rf"^\s*({_TIMESTAMP})\s+-->\s+({_TIMESTAMP})(?:\s+.*)?$")
_SRT_INDEX_RE = re.compile(r"^\s*\d+\s*$")
_VOICE_TAG_RE = re.compile(r"<v(?:\.[^ >]*)?\s+([^>]+)>")
_MARKUP_RE = re.compile(r"</?[^>]+>")
# Conservative speaker prefix: ALL-CAPS name ("ALICE:", "DR. WHO:") or the ">>"
# broadcast convention. Mixed-case prefixes ("Note:", "Example:") are left alone.
_SPEAKER_PREFIX_RE = re.compile(r"^(?:-\s*)?(?:>>\s*([^:]{1,40})|([A-Z][A-Z0-9 .'\-]{1,29})):\s+")


@dataclass(frozen=True)
class TranscriptCue:
    start: float
    end: float
    text: str
    speaker: str | None = None


def _parse_timestamp(value: str) -> float:
    parts = value.replace(",", ".").split(":")
    seconds = float(parts[-1])
    minutes = int(parts[-2]) if len(parts) >= 2 else 0
    hours = int(parts[-3]) if len(parts) >= 3 else 0
    return hours * 3600.0 + minutes * 60.0 + seconds


def detect_transcript_format(head: str) -> str | None:
    """Classify a text head (first few KB) as ``"vtt"``, ``"srt"``, or None.

    VTT: the mandatory ``WEBVTT`` header line. SRT: an index line followed by a
    ``-->`` timing line within the first non-blank lines.
    """

    lines = head.splitlines()
    for line in lines[:4]:
        if _VTT_HEADER_RE.match(line.strip("\r")):
            return "vtt"
    meaningful = [line.strip() for line in lines if line.strip()]
    for index, line in enumerate(meaningful[:8]):
        if _SRT_INDEX_RE.match(line) and index + 1 < len(meaningful) and _CUE_TIMING_RE.match(meaningful[index + 1]):
            return "srt"
    return None


def _clean_cue_text(raw: str) -> tuple[str, str | None]:
    """Strip cue markup, extracting a speaker from a VTT voice tag or a
    conservative ``NAME:`` / ``>>`` prefix. Returns ``(text, speaker)``."""

    speaker: str | None = None
    voice = _VOICE_TAG_RE.search(raw)
    if voice:
        speaker = voice.group(1).strip() or None
    text = _MARKUP_RE.sub("", raw).strip()
    if speaker is None:
        prefix = _SPEAKER_PREFIX_RE.match(text)
        if prefix:
            speaker = (prefix.group(1) or prefix.group(2) or "").strip() or None
            text = text[prefix.end():].strip()
    return text, speaker


def parse_transcript(text: str, *, fmt: str | None = None) -> list[TranscriptCue]:
    """Parse WebVTT or SRT content into ordered cues. Unknown format → []."""

    fmt = fmt or detect_transcript_format(text[:4096])
    if fmt not in ("vtt", "srt"):
        return []

    cues: list[TranscriptCue] = []
    lines = text.splitlines()
    i = 0
    last_speaker: str | None = None
    while i < len(lines):
        line = lines[i].strip()
        timing = _CUE_TIMING_RE.match(line)
        if not timing:
            # Skip headers, cue identifiers, NOTE/STYLE blocks, SRT indices.
            i += 1
            continue
        start = _parse_timestamp(timing.group(1))
        end = _parse_timestamp(timing.group(2))
        i += 1
        body: list[str] = []
        while i < len(lines) and lines[i].strip():
            body.append(lines[i].strip())
            i += 1
        text_joined = " ".join(body)
        cleaned, speaker = _clean_cue_text(text_joined)
        if speaker is None:
            # A continued turn: cues after a voiced cue keep the speaker until a
            # new voice tag / prefix names someone else (VTT continuation style).
            speaker = last_speaker
        else:
            last_speaker = speaker
        if cleaned:
            cues.append(TranscriptCue(start=start, end=end, text=cleaned, speaker=speaker))
    return cues


__all__ = ["TranscriptCue", "detect_transcript_format", "parse_transcript"]

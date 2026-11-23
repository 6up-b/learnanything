from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from learnloop.ingest.models import UnsupportedSourceError
from learnloop.ingest.source_kinds import SOURCE_KINDS, SourceCategory

_ARXIV_NEW = re.compile(r"^(arxiv:)?\d{4}\.\d{4,5}(v\d+)?$", re.IGNORECASE)
_ARXIV_OLD = re.compile(r"^(arxiv:)?[a-z\-]+(\.[a-z]{2})?/\d{7}(v\d+)?$", re.IGNORECASE)
_YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}
# The suffixes are the kinds' (``SOURCE_KINDS``); the order they are tried in is this module's.
_IMAGE_URL_SUFFIXES = SOURCE_KINDS["image"].url_extensions
_PDF_URL_SUFFIXES = SOURCE_KINDS["pdf"].url_extensions
_IMAGE_SUFFIXES = frozenset(SOURCE_KINDS["image"].extensions)
_PDF_SUFFIXES = frozenset(SOURCE_KINDS["pdf"].extensions)
_WEB_SUFFIXES = frozenset(SOURCE_KINDS["web"].extensions)
_TEXT_SUFFIXES = frozenset(SOURCE_KINDS["textfile"].extensions)
_AUDIO_SUFFIXES = frozenset(SOURCE_KINDS["audio"].extensions)


@dataclass(frozen=True)
class ResolvedSource:
    """One authoritative classification plus a fetchable source value."""

    category: SourceCategory
    source: str


def is_arxiv_id(source: str) -> bool:
    return bool(_ARXIV_NEW.match(source) or _ARXIV_OLD.match(source))


def resolve_source(source: str) -> ResolvedSource:
    candidate = source.strip()
    if not candidate:
        raise UnsupportedSourceError("empty source")

    if candidate.lower().startswith(("http://", "https://")):
        parsed = urlparse(candidate)
        host = parsed.netloc.lower().split(":", 1)[0]
        path = parsed.path.lower()
        if host in _YOUTUBE_HOSTS:
            return ResolvedSource("youtube", candidate)
        if host == "arxiv.org" or host.endswith(".arxiv.org"):
            return ResolvedSource("arxiv", candidate)
        if path.endswith(_IMAGE_URL_SUFFIXES):
            return ResolvedSource("image", candidate)
        if path.endswith(_PDF_URL_SUFFIXES):
            return ResolvedSource("pdf", candidate)
        return ResolvedSource("web", candidate)

    if is_arxiv_id(candidate):
        arxiv_id = re.sub(r"^arxiv:", "", candidate, flags=re.IGNORECASE)
        return ResolvedSource("arxiv", f"https://arxiv.org/abs/{arxiv_id}")

    path = Path(candidate).expanduser()
    suffix = path.suffix.lower()
    if suffix in _IMAGE_SUFFIXES:
        return ResolvedSource("image", str(path))
    if suffix in _PDF_SUFFIXES:
        return ResolvedSource("pdf", str(path))
    if suffix in _WEB_SUFFIXES:
        return ResolvedSource("web", str(path))
    if suffix in _TEXT_SUFFIXES:
        return ResolvedSource("textfile", str(path))
    # Audio before the null-byte sniff: audio is binary and would otherwise
    # fall through to the unsupported-source error.
    if suffix in _AUDIO_SUFFIXES:
        return ResolvedSource("audio", str(path))
    if path.exists() and path.is_file():
        sample = path.read_bytes()[:4096]
        if b"\x00" not in sample:
            return ResolvedSource("textfile", str(path))

    raise UnsupportedSourceError(
        f"Could not classify source {source!r}. Pass a URL (web/arXiv/YouTube), "
        "an arXiv id, or a local .pdf/.md/.txt/.vtt/.srt/.mp3/.wav/.m4a file path."
    )


__all__ = ["ResolvedSource", "SourceCategory", "is_arxiv_id", "resolve_source"]

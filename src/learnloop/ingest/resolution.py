from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from learnloop.ingest.models import UnsupportedSourceError

SourceCategory = Literal["web", "arxiv", "pdf", "youtube", "textfile"]

_ARXIV_NEW = re.compile(r"^(arxiv:)?\d{4}\.\d{4,5}(v\d+)?$", re.IGNORECASE)
_ARXIV_OLD = re.compile(r"^(arxiv:)?[a-z\-]+(\.[a-z]{2})?/\d{7}(v\d+)?$", re.IGNORECASE)
_YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}
_TEXT_SUFFIXES = {".md", ".markdown", ".mdown", ".txt", ".text", ".rst", ".vtt", ".srt"}


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
        if path.endswith(".pdf"):
            return ResolvedSource("pdf", candidate)
        return ResolvedSource("web", candidate)

    if is_arxiv_id(candidate):
        arxiv_id = re.sub(r"^arxiv:", "", candidate, flags=re.IGNORECASE)
        return ResolvedSource("arxiv", f"https://arxiv.org/abs/{arxiv_id}")

    path = Path(candidate).expanduser()
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return ResolvedSource("pdf", str(path))
    if suffix in {".html", ".htm"}:
        return ResolvedSource("web", str(path))
    if suffix in _TEXT_SUFFIXES:
        return ResolvedSource("textfile", str(path))
    if path.exists() and path.is_file():
        sample = path.read_bytes()[:4096]
        if b"\x00" not in sample:
            return ResolvedSource("textfile", str(path))

    raise UnsupportedSourceError(
        f"Could not classify source {source!r}. Pass a URL (web/arXiv/YouTube), "
        "an arXiv id, or a local .pdf/.md/.txt/.vtt/.srt file path."
    )


__all__ = ["ResolvedSource", "SourceCategory", "is_arxiv_id", "resolve_source"]

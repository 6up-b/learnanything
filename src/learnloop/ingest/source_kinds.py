"""What a source kind is, in one row: ``SOURCE_KINDS``.

A kind (``resolution.SourceCategory``) once lived in seven backend places (the
classifier's suffix sets, the import's fetch, document, extract and identity
dispatch, the learner noun, two role guesses and the legacy pipeline's kind)
and six desktop tables, two of which missed the last kind added. Each of those
readers now reads its column here, and the desktop's kind table is generated
from it (``tests/test_source_kinds.py --write``).

A new kind is one row, its IR builder in ``content/pipeline/jobs.py``'s
dispatch on ``reader``, and one test. The classifier's *order* of checks
(hosts before suffixes, an image URL before a PDF one) stays in
``resolution.resolve_source``; only the suffixes are here.

This module is a leaf: it imports nothing from LearnLoop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SourceCategory = Literal["web", "arxiv", "pdf", "youtube", "textfile", "audio", "image"]

#: How the import reads a kind's bytes into Document IR (``content/pipeline/jobs.py``'s
#: ``default_extract`` and ``default_extraction_identity`` dispatch on it). ``document``
#: goes to the document extractors (GLM-OCR, Marker, pypdf); ``html`` to the web-page
#: reader; ``captions`` tries YouTube caption cues first; ``audio`` is transcribed;
#: ``text`` sniffs HTML and transcript formats and otherwise reads Markdown.
Reader = Literal["document", "html", "captions", "audio", "text"]


@dataclass(frozen=True)
class SourceKind:
    #: A ``SourceCategory``; ``UNKNOWN_KIND`` alone names none.
    category: str
    #: The desktop's kind label ("web page"), as the kind chip shows it.
    label: str
    #: What the learner's book card calls a source of this kind (``add_source.kind_noun``).
    noun: str
    #: Local file suffixes the classifier reads as this kind (lower case, with the dot).
    extensions: tuple[str, ...]
    #: URL path suffixes the classifier reads as this kind.
    url_extensions: tuple[str, ...]
    #: What ``source_ingestion.fetch_source`` fetches a URL of this kind as.
    fetch_as: Literal["website_page", "youtube_video"]
    #: Read by the document extractors whatever its content type says.
    document: bool
    reader: Reader
    #: The source-set role Add and Quick Add guess for it, and whether that guess is confident
    #: (an unconfident one proceeds flagged, never blocked).
    suggested_role: str
    confident_role: bool
    #: The kind the legacy one-shot pipeline (``source_ingestion.resolve_canonical_source``)
    #: reads it as; ``None`` where that pipeline cannot read it at all.
    legacy_kind: str | None


SOURCE_KINDS: dict[str, SourceKind] = {
    kind.category: kind
    for kind in (
        SourceKind("web", "web page", "article", (".html", ".htm"), (), "website_page", False, "html",
                   "reference", False, "website_page"),
        SourceKind("arxiv", "arXiv paper", "paper", (), (), "website_page", False, "html",
                   "paper", True, "arxiv_html"),
        SourceKind("pdf", "PDF", "PDF", (".pdf",), (".pdf",), "website_page", True, "document",
                   "primary_textbook", True, "website_page"),
        SourceKind("youtube", "YouTube transcript", "video", (), (), "youtube_video", False, "captions",
                   "lecture", True, "youtube_video"),
        SourceKind("textfile", "local file", "book",
                   (".md", ".markdown", ".mdown", ".txt", ".text", ".rst", ".vtt", ".srt"), (), "website_page",
                   False, "text", "reference", False, "website_page"),
        SourceKind("audio", "audio file", "recording", (".mp3", ".wav", ".m4a", ".flac", ".ogg", ".oga", ".opus", ".aac"),
                   (), "website_page", False, "audio", "reference", False, None),
        SourceKind("image", "image", "image", (".png", ".jpg", ".jpeg"), (".png", ".jpg", ".jpeg"), "website_page",
                   True, "document", "reference", False, None),
    )
}

#: The row for a category no table row names (an artifact stored under a retired kind): it reads
#: as plain text, is guessed a reference, and is called a book, as each reader did before the table.
UNKNOWN_KIND = SourceKind("unknown", "unknown", "book", (), (), "website_page", False, "text",
                          "reference", False, None)


def source_kind(category: str | None) -> SourceKind:
    """The row for ``category``; :data:`UNKNOWN_KIND` for one no row names."""

    return SOURCE_KINDS.get(str(category or ""), UNKNOWN_KIND)


__all__ = ["Reader", "SOURCE_KINDS", "SourceCategory", "SourceKind", "UNKNOWN_KIND", "source_kind"]

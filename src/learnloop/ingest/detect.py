from __future__ import annotations

from learnloop.ingest.resolution import resolve_source


def detect_source_kind(source: str) -> str:
    """Classify a source string into one of the supported ingestion kinds.

    Returns one of ``web``, ``arxiv``, ``pdf``, ``youtube``, ``textfile``,
    ``audio`` or ``image``.
    Raises :class:`UnsupportedSourceError` for anything unrecognized.
    """

    return resolve_source(source).category

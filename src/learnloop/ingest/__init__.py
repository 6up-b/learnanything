"""Canonical-source ingestion: fetch and normalize external material into the vault.

What a source is (``resolution``, ``source_kinds``), how its bytes become
Document IR (``extractors``, ``ir``) and the errors the import raises
(``models``). Network-bound extraction libraries are optional (see the
``ingest`` extra in ``pyproject.toml``); importing this package never requires
them.
"""

from learnloop.ingest.models import (
    FetchedSource,
    IngestDependencyMissing,
    IngestError,
    IngestResult,
    SourceFetchError,
    UnsupportedSourceError,
)

__all__ = [
    "FetchedSource",
    "IngestResult",
    "IngestError",
    "IngestDependencyMissing",
    "SourceFetchError",
    "UnsupportedSourceError",
]

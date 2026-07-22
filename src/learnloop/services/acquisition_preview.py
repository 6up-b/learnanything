"""Deterministic acquisition preview (spec_source_ingestion_v2 §8.6.1).

Before any import runs, tell the user what a set of candidate inputs (paths / URLs)
*would* become: which inputs are recognized, their normalized artifact identity,
obvious duplicates (within the batch or already in the library), local file sizes
and any already-known remote metadata, the configured local extractor, and any
external processing that would later need consent.

Zero pedagogical work: **no downloads, no extraction, no LLM.** Remote inputs are
classified from their URL only; sizes are read for local files that exist.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import Repository
from learnloop.ingest.models import UnsupportedSourceError
from learnloop.ingest.resolution import resolve_source

# Configured local extractor per acquisition category (the marker/pypdf choice is
# resolved live for PDFs; everything else has a fixed trivial-IR normalizer).
_NORMALIZER_BY_CATEGORY = {
    "web": "html_normalizer",
    "arxiv": "html_normalizer",
    "youtube": "youtube_captions",
    "textfile": "text_normalizer",
    "audio": "audio_transcription",
}


@dataclass
class AcquisitionItem:
    input: str
    recognized: bool
    category: str | None = None
    normalized_uri: str | None = None
    error: str | None = None
    is_local: bool = False
    file_size_bytes: int | None = None
    remote_metadata: dict | None = None
    duplicate_of_input: str | None = None
    existing_source_id: str | None = None
    existing_revision_count: int = 0
    configured_extractor: str | None = None
    potential_external: list[dict] = field(default_factory=list)


@dataclass
class AcquisitionPreview:
    items: list[AcquisitionItem] = field(default_factory=list)

    @property
    def recognized_count(self) -> int:
        return sum(1 for item in self.items if item.recognized)

    @property
    def duplicate_count(self) -> int:
        return sum(1 for item in self.items if item.duplicate_of_input is not None)

    @property
    def existing_count(self) -> int:
        return sum(1 for item in self.items if item.existing_source_id is not None)

    @property
    def needs_consent_count(self) -> int:
        return sum(1 for item in self.items if item.potential_external)

    def as_dict(self) -> dict:
        return {
            "items": [
                {
                    "input": item.input,
                    "recognized": item.recognized,
                    "category": item.category,
                    "normalized_uri": item.normalized_uri,
                    "error": item.error,
                    "is_local": item.is_local,
                    "file_size_bytes": item.file_size_bytes,
                    "remote_metadata": item.remote_metadata,
                    "duplicate_of_input": item.duplicate_of_input,
                    "existing_source_id": item.existing_source_id,
                    "existing_revision_count": item.existing_revision_count,
                    "configured_extractor": item.configured_extractor,
                    "potential_external": item.potential_external,
                }
                for item in self.items
            ],
            "summary": {
                "input_count": len(self.items),
                "recognized_count": self.recognized_count,
                "duplicate_count": self.duplicate_count,
                "existing_count": self.existing_count,
                "needs_consent_count": self.needs_consent_count,
            },
        }


def build_acquisition_preview(
    repo: Repository,
    config: LearnLoopConfig,
    inputs: list[str],
) -> AcquisitionPreview:
    """Preview a batch of candidate inputs deterministically (§8.6.1)."""

    preview = AcquisitionPreview()
    seen_uris: dict[str, str] = {}
    for raw in inputs:
        source = (raw or "").strip()
        if not source:
            preview.items.append(AcquisitionItem(input=raw, recognized=False, error="empty input"))
            continue
        try:
            resolved = resolve_source(source)
        except UnsupportedSourceError as exc:
            preview.items.append(AcquisitionItem(input=source, recognized=False, error=str(exc)))
            continue

        item = AcquisitionItem(
            input=source,
            recognized=True,
            category=resolved.category,
            normalized_uri=resolved.source,
            configured_extractor=_configured_extractor(resolved.category, config),
            potential_external=_potential_external(resolved.category, config),
        )
        _annotate_local(item, resolved.source)
        _annotate_existing(item, repo, resolved.category, resolved.source)

        if resolved.source in seen_uris:
            item.duplicate_of_input = seen_uris[resolved.source]
        else:
            seen_uris[resolved.source] = source
        preview.items.append(item)
    return preview


def _configured_extractor(category: str, config: LearnLoopConfig) -> str:
    if category in {"pdf", "arxiv"}:
        # arXiv abstract pages resolve to HTML, but a linked PDF uses the PDF path.
        if category == "pdf":
            from learnloop.ingest.extractors import marker_available

            engine = config.ingest.pdf.engine
            if engine == "pypdf":
                return "pypdf"
            if engine == "marker":
                return "marker"
            return "marker" if marker_available() else "pypdf"
    return _NORMALIZER_BY_CATEGORY.get(category, "text_normalizer")


def _potential_external(category: str, config: LearnLoopConfig) -> list[dict]:
    external: list[dict] = []
    if category == "pdf" and config.ingest.pdf.use_llm:
        external.append(
            {
                "kind": "pdf_llm_extraction",
                "service": config.ingest.pdf.llm_service,
                "base_url": config.ingest.pdf.llm_base_url or None,
                "model": config.ingest.pdf.llm_model or None,
                "reason": "marker VLM boost sends difficult pages to an external service",
            }
        )
    if category == "audio":
        # Audio ingestion is ALWAYS external (transcription endpoint), so the
        # consent card fires before any bytes leave the machine.
        external.append(
            {
                "kind": "audio_transcription",
                "base_url": config.ingest.audio.transcription_base_url,
                "model": config.ingest.audio.transcription_model,
                "reason": "audio files are transcribed by the configured [ingest.audio] endpoint",
            }
        )
    return external


def _annotate_local(item: AcquisitionItem, normalized_uri: str) -> None:
    path = Path(normalized_uri).expanduser()
    if path.exists() and path.is_file():
        item.is_local = True
        try:
            item.file_size_bytes = path.stat().st_size
        except OSError:
            item.file_size_bytes = None


def _annotate_existing(item: AcquisitionItem, repo: Repository, category: str, normalized_uri: str) -> None:
    artifact = repo.source_artifact_by_uri(category, normalized_uri)
    if artifact is not None:
        item.existing_source_id = artifact["id"]
        item.existing_revision_count = len(repo.source_revisions_for(artifact["id"]))

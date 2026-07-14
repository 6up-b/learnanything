"""Deterministic source outline view (spec_source_ingestion_v2 §3, §5.3, §8.6).

From a persisted ExtractionRun this produces the token-budgeted **outline view**:
title/authors, the unit tree with page ranges/timestamps, block counts by type,
structural signals (examples/exercises/equations/figures from M1's role hints),
per-unit extraction-health flags, an approximate token size per unit (a single
deterministic estimator so the number is consistent everywhere), and
already-inventoried markers (an M4 seam — empty/false for now).

Hard invariant (§14 "Outline determinism"): **zero agent runs**, and the same
extraction run yields a byte-identical outline. Nothing here fetches, extracts, or
calls an LLM; it reads only persisted IR rows.
"""

from __future__ import annotations

from collections import Counter

from pydantic import BaseModel, ConfigDict, Field

from learnloop.db.repositories import Repository
from learnloop.ingest.hashing import normalize_semantic_text
from learnloop.ingest.ir import DocumentIR
from learnloop.services.extraction_health import analyze_extraction_health

# One estimator, used by the outline AND the build plan (§3.1) so a unit's token
# size never disagrees between the two screens. chars/4 is the house heuristic.
_CHARS_PER_TOKEN = 4


def approx_token_count(text: str) -> int:
    """Deterministic approximate token count for a string (chars / 4, §3.1).

    The single source of truth for token sizing across outline and build plan."""

    if not text:
        return 0
    return (len(text) + _CHARS_PER_TOKEN - 1) // _CHARS_PER_TOKEN


# Role hints (block_roles.ROLES) rolled up into the four structural signals the
# outline card leads with, plus a few cheap extras that help unit triage.
_SIGNAL_ROLES = {
    "examples": {"worked_example"},
    "exercises": {"exercise"},
    "equations": {"equation"},
    "figures": {"figure"},
    "definitions": {"definition"},
    "theorems": {"theorem"},
    "tables": {"table"},
}


def unit_inventory_marker(repo: Repository, extraction_id: str, unit_id: str) -> dict[str, object]:
    """Whether a unit already has a cached inventory (ING M4).

    Reads real `source_unit_inventories` rows so the outline and build plan render
    the "cached" affordance from actual data. Returns the richest cached profile
    for the unit's current semantic hash."""

    from learnloop.services.source_unit_inventory import inventory_marker

    return inventory_marker(repo, extraction_id, unit_id)


class OutlineUnit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    unit_id: str
    parent_unit_id: str | None = None
    label: str
    ordinal: int
    locator: dict = Field(default_factory=dict)
    semantic_hash: str
    page_start: int | None = None
    page_end: int | None = None
    block_count: int
    block_counts: dict[str, int] = Field(default_factory=dict)
    structural_signals: dict[str, int] = Field(default_factory=dict)
    health_flags: list[str] = Field(default_factory=list)
    approx_tokens: int
    inventory: dict[str, object] = Field(default_factory=dict)


class SourceOutline(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extraction_id: str
    revision_id: str | None = None
    source_id: str | None = None
    title: str
    authors: list[str] = Field(default_factory=list)
    extractor: str
    extractor_version: str
    unit_count: int
    block_count: int
    approx_tokens: int
    health_flags: list[str] = Field(default_factory=list)
    difficult_page_count: int = 0
    units: list[OutlineUnit] = Field(default_factory=list)


def build_source_outline(repo: Repository, extraction_id: str) -> SourceOutline:
    """Build the deterministic outline for one completed extraction run.

    Raises :class:`OutlineNotFound` when the extraction (or its IR) is absent."""

    ir = repo.load_document_ir(extraction_id)
    if ir is None:
        raise OutlineNotFound(f"extraction '{extraction_id}' has no persisted IR.")
    run = repo.get_extraction_run(extraction_id)
    revision_id = run["revision_id"] if run else None
    revision = repo.get_source_revision(revision_id) if revision_id else None
    source_id = revision["source_id"] if revision else None
    artifact = repo.get_source_artifact(source_id) if source_id else None

    health = analyze_extraction_health(ir)
    by_span = {block.span_id: block for block in ir.blocks}

    units: list[OutlineUnit] = []
    for unit in ir.units:
        blocks = [by_span[span_id] for span_id in unit.span_ids if span_id in by_span]
        block_counts = dict(sorted(Counter(block.block_type for block in blocks).items()))
        signals = _structural_signals(blocks)
        flags = _unit_health_flags(unit.page_start, unit.page_end, health)
        approx = approx_token_count(normalize_semantic_text(blocks))
        units.append(
            OutlineUnit(
                unit_id=unit.unit_id,
                parent_unit_id=unit.parent_unit_id,
                label=unit.label,
                ordinal=unit.ordinal,
                locator=dict(unit.locator),
                semantic_hash=unit.semantic_hash,
                page_start=unit.page_start,
                page_end=unit.page_end,
                block_count=len(blocks),
                block_counts=block_counts,
                structural_signals=signals,
                health_flags=flags,
                approx_tokens=approx,
                inventory=unit_inventory_marker(repo, extraction_id, unit.unit_id),
            )
        )

    return SourceOutline(
        extraction_id=extraction_id,
        revision_id=revision_id,
        source_id=source_id,
        title=_derive_title(artifact, revision, ir),
        authors=_derive_authors(artifact, revision),
        extractor=ir.extractor,
        extractor_version=ir.extractor_version,
        unit_count=len(ir.units),
        block_count=len(ir.blocks),
        approx_tokens=sum(unit.approx_tokens for unit in units),
        health_flags=list(ir.health.flags),
        difficult_page_count=health.difficult_page_count,
        units=units,
    )


def _structural_signals(blocks) -> dict[str, int]:
    counts = Counter(block.role_hint for block in blocks if block.role_hint)
    return {signal: sum(counts.get(role, 0) for role in roles) for signal, roles in _SIGNAL_ROLES.items()}


def _unit_health_flags(page_start: int | None, page_end: int | None, health) -> list[str]:
    if page_start is None:
        return []
    end = page_end if page_end is not None else page_start
    reasons: list[str] = []
    for flagged in health.flagged_pages:
        lo, hi = flagged.page_range
        if hi >= page_start and lo <= end:
            reasons.extend(flagged.reasons)
    return sorted(set(reasons))


def _derive_title(artifact, revision, ir: DocumentIR) -> str:
    """Deterministic display title from artifact metadata, never an LLM guess."""

    display_title = artifact.get("display_title") if artifact else None
    if isinstance(display_title, str) and display_title.strip():
        return display_title
    for candidate in (
        revision.get("original_uri") if revision else None,
        artifact.get("canonical_uri") if artifact else None,
    ):
        title = _basename(candidate)
        if title:
            return title
    for unit in ir.units:
        if unit.label and unit.label.lower() not in {"root", "document"}:
            return unit.label
    if artifact:
        return str(artifact.get("id"))
    return "Untitled source"


def _derive_authors(artifact, revision) -> list[str]:
    """Authors from artifact metadata. No metadata field carries authors in the
    source layer today, so this is deterministically empty (M4/M6 populate it)."""

    return []


def _basename(uri: object) -> str | None:
    if not isinstance(uri, str) or not uri.strip():
        return None
    trimmed = uri.split("?", 1)[0].split("#", 1)[0].rstrip("/")
    tail = trimmed.rsplit("/", 1)[-1]
    return tail or None


def resolve_extraction_id(repo: Repository, ref: str) -> str | None:
    """Resolve an extraction / revision / artifact reference to an extraction id.

    Accepts an extraction id directly, a revision id (→ its latest completed
    top-level extraction), or an artifact id (→ current revision's extraction).
    Returns None when nothing resolves."""

    if repo.get_extraction_run(ref) is not None:
        return ref
    revision = repo.get_source_revision(ref)
    if revision is not None:
        return _latest_completed(repo, ref)
    artifact = repo.get_source_artifact(ref)
    if artifact is not None:
        revision_id = artifact.get("current_revision_id")
        if revision_id is None:
            revisions = repo.source_revisions_for(ref)
            revision_id = revisions[-1]["id"] if revisions else None
        if revision_id is not None:
            return _latest_completed(repo, revision_id)
    return None


def _latest_completed(repo: Repository, revision_id: str) -> str | None:
    completed = [
        run
        for run in repo.extraction_runs_for_revision(revision_id)
        if run.get("status") == "completed" and run.get("parent_extraction_id") is None
    ]
    if completed:
        return completed[-1]["id"]
    runs = repo.extraction_runs_for_revision(revision_id)
    return runs[-1]["id"] if runs else None


class OutlineNotFound(ValueError):
    """The requested extraction run has no persisted IR to outline."""

"""Document Intermediate Representation (IR) — the common source-layer contract.

Every extractor (marker, pypdf, HTML, YouTube captions, text files, and future
providers) returns this IR; extractor-native types MUST NOT leak past the source
layer (spec_source_ingestion_v2 §2.3). Markdown remains the display/export
rendering of a note, but it is no longer the canonical intermediate.

This module is pure: it imports no extractor and performs no I/O. Downstream code
depends on these types, not on marker/pypdf classes.
"""

from __future__ import annotations

import hashlib

from pydantic import BaseModel, ConfigDict, Field

# Bumping this participates in every extraction_request_hash (§2.2): a schema
# change invalidates the extraction cache and forces re-extraction.
IR_SCHEMA_VERSION = "ir-1"


def block_content_hash(text: str) -> str:
    """Per-block content hash over the block's normalized text (§2.3)."""

    return "sha256:" + hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


class DocumentBlock(BaseModel):
    """A span-addressable block within one ExtractionRun (§2.3).

    ``span_id`` is stable only within its run; cross-run identity is recovered by
    re-anchoring (§2.4) using content hashes, geometry, and section path.
    """

    model_config = ConfigDict(extra="forbid")

    span_id: str
    extractor_block_id: str | None = None
    block_type: str
    role_hint: str | None = None
    page: int | None = None
    bbox: list[float] | None = None
    polygon: list[list[float]] | None = None
    section_path: list[str] = Field(default_factory=list)
    text: str
    content_hash: str
    asset_ids: list[str] = Field(default_factory=list)
    ordinal: int

    @classmethod
    def build(
        cls,
        *,
        span_id: str,
        block_type: str,
        text: str,
        ordinal: int,
        extractor_block_id: str | None = None,
        role_hint: str | None = None,
        page: int | None = None,
        bbox: list[float] | None = None,
        polygon: list[list[float]] | None = None,
        section_path: list[str] | None = None,
        asset_ids: list[str] | None = None,
    ) -> DocumentBlock:
        return cls(
            span_id=span_id,
            extractor_block_id=extractor_block_id,
            block_type=block_type,
            role_hint=role_hint,
            page=page,
            bbox=bbox,
            polygon=polygon,
            section_path=list(section_path or []),
            text=text,
            content_hash=block_content_hash(text),
            asset_ids=list(asset_ids or []),
            ordinal=ordinal,
        )


class DocumentUnit(BaseModel):
    """A chapter/section with a stable id, label, and (paged) page range (§2.3)."""

    model_config = ConfigDict(extra="forbid")

    unit_id: str
    parent_unit_id: str | None = None
    label: str
    ordinal: int
    locator: dict = Field(default_factory=dict)
    semantic_hash: str
    page_start: int | None = None
    page_end: int | None = None
    span_ids: list[str] = Field(default_factory=list)


class DocumentAsset(BaseModel):
    """An extracted figure/image asset with citation context (§2.7)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    media_type: str
    content_hash: str
    path: str | None = None
    caption: str | None = None
    page: int | None = None
    geometry: dict | None = None
    neighboring_span_ids: list[str] = Field(default_factory=list)


class PageHealth(BaseModel):
    """Per-page extraction-quality signals (§2.5, from marker ``page_stats``)."""

    model_config = ConfigDict(extra="forbid")

    page: int
    text_extraction_method: str | None = None
    block_counts: dict[str, int] = Field(default_factory=dict)
    flags: list[str] = Field(default_factory=list)


class ExtractionHealth(BaseModel):
    """Aggregated extraction-health signals across the run (§2.3/§2.5)."""

    model_config = ConfigDict(extra="forbid")

    pages: list[PageHealth] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)

    def flagged_pages(self) -> list[int]:
        return [page.page for page in self.pages if page.flags]


class DocumentIR(BaseModel):
    """The full extractor output: blocks, units, assets, and health (§2.3)."""

    model_config = ConfigDict(extra="forbid")

    ir_schema_version: str = IR_SCHEMA_VERSION
    extractor: str
    extractor_version: str
    blocks: list[DocumentBlock] = Field(default_factory=list)
    units: list[DocumentUnit] = Field(default_factory=list)
    assets: list[DocumentAsset] = Field(default_factory=list)
    health: ExtractionHealth = Field(default_factory=ExtractionHealth)

    def block_by_span(self, span_id: str) -> DocumentBlock | None:
        for block in self.blocks:
            if block.span_id == span_id:
                return block
        return None

    def unit_blocks(self, unit_id: str) -> list[DocumentBlock]:
        unit = next((u for u in self.units if u.unit_id == unit_id), None)
        if unit is None:
            return []
        by_span = {block.span_id: block for block in self.blocks}
        return [by_span[span_id] for span_id in unit.span_ids if span_id in by_span]


def compose_extraction_runs(parent: DocumentIR, repair: DocumentIR) -> DocumentIR:
    """Deterministically compose a parent run with a targeted repair run (§2.3).

    A repair ExtractionRun contains only re-extracted pages. The active document
    view replaces every parent block on a repaired page with the repair's blocks
    for that page; parent blocks on untouched pages are retained. Blocks are
    re-ordered by ``ordinal`` and given fresh sequential span ids so the composed
    view is itself a valid single run. Units are recomputed from the composition
    by the caller if page assignments changed; here we preserve parent units whose
    pages were untouched and take repair units for repaired pages.
    """

    repaired_pages = {block.page for block in repair.blocks if block.page is not None}
    kept = [block for block in parent.blocks if block.page not in repaired_pages]
    composed_blocks = sorted([*kept, *repair.blocks], key=lambda b: (b.page if b.page is not None else 0, b.ordinal))

    reindexed: list[DocumentBlock] = [
        block.model_copy(update={"span_id": f"s{index}", "ordinal": index})
        for index, block in enumerate(composed_blocks, start=1)
    ]

    kept_units = [unit for unit in parent.units if not _unit_touches_pages(unit, repaired_pages)]
    repair_units = list(repair.units)
    composed_units = sorted(
        [*kept_units, *repair_units],
        key=lambda u: (u.page_start if u.page_start is not None else 0, u.ordinal),
    )
    reindexed_units = [unit.model_copy(update={"ordinal": index}) for index, unit in enumerate(composed_units, start=1)]

    kept_assets = [
        asset for asset in parent.assets if asset.page is None or asset.page not in repaired_pages
    ]
    composed_assets = [*kept_assets, *repair.assets]

    composed_pages = {
        page.page: page
        for page in parent.health.pages
        if page.page not in repaired_pages
    }
    for page in repair.health.pages:
        composed_pages[page.page] = page
    composed_health = ExtractionHealth(
        pages=[composed_pages[key] for key in sorted(composed_pages)],
        flags=sorted(set(parent.health.flags) | set(repair.health.flags)),
    )

    return DocumentIR(
        ir_schema_version=parent.ir_schema_version,
        extractor=parent.extractor,
        extractor_version=parent.extractor_version,
        blocks=reindexed,
        units=reindexed_units,
        assets=composed_assets,
        health=composed_health,
    )


def _unit_touches_pages(unit: DocumentUnit, pages: set[int]) -> bool:
    if unit.page_start is None:
        return False
    end = unit.page_end if unit.page_end is not None else unit.page_start
    return any(unit.page_start <= page <= end for page in pages)

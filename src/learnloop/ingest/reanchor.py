"""Deterministic cross-run span re-anchoring (spec_source_ingestion_v2 §2.4).

A new ExtractionRun over the same revision attempts to rebind each old span to a
new one. An exact content-hash match wins **only** when it is unique within the
resolution scope; duplicated hashes (boilerplate, repeated equations) disambiguate
via section path, page/geometry, and neighboring-block context. A still-ambiguous
or unresolved span becomes ``needs_reanchor`` — never silently resolved and never
semantically stale. Successful aliases persist in ``source_span_reanchors``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from learnloop.ingest.ir import DocumentBlock, DocumentIR

# match_kind values, constrained by the source_span_reanchors CHECK.
EXACT_HASH = "exact_hash"
GEOMETRY_SECTION = "geometry_section"
MANUAL = "manual"


@dataclass(frozen=True)
class SpanAlias:
    from_span_id: str
    to_span_id: str
    match_kind: str
    confidence: float


@dataclass
class ReanchorResult:
    aliases: list[SpanAlias] = field(default_factory=list)
    needs_reanchor: list[str] = field(default_factory=list)

    def alias_for(self, from_span_id: str) -> SpanAlias | None:
        return next((alias for alias in self.aliases if alias.from_span_id == from_span_id), None)


def reanchor_spans(from_ir: DocumentIR, to_ir: DocumentIR) -> ReanchorResult:
    """Re-anchor every span of ``from_ir`` onto ``to_ir`` deterministically."""

    to_blocks = list(to_ir.blocks)
    by_hash: dict[str, list[DocumentBlock]] = {}
    for block in to_blocks:
        by_hash.setdefault(block.content_hash, []).append(block)

    from_neighbors = _neighbor_index(from_ir.blocks)
    to_neighbors = _neighbor_index(to_blocks)
    result = ReanchorResult()
    for block in from_ir.blocks:
        want = from_neighbors.get(block.span_id, ("", ""))
        candidates = by_hash.get(block.content_hash, [])
        if len(candidates) == 1:
            result.aliases.append(SpanAlias(block.span_id, candidates[0].span_id, EXACT_HASH, 1.0))
            continue
        if len(candidates) > 1:
            disambiguated = _pick_unique(block, candidates, want, to_neighbors)
            if disambiguated is not None:
                result.aliases.append(SpanAlias(block.span_id, disambiguated.span_id, EXACT_HASH, 0.9))
            else:
                result.needs_reanchor.append(block.span_id)
            continue
        fallback_pool = [candidate for candidate in to_blocks if candidate.block_type == block.block_type]
        fallback = _pick_unique(block, fallback_pool, want, to_neighbors)
        if fallback is not None:
            result.aliases.append(SpanAlias(block.span_id, fallback.span_id, GEOMETRY_SECTION, 0.6))
        else:
            result.needs_reanchor.append(block.span_id)
    return result


def _neighbor_index(blocks: list[DocumentBlock]) -> dict[str, tuple[str, str]]:
    ordered = sorted(blocks, key=lambda b: b.ordinal)
    index: dict[str, tuple[str, str]] = {}
    for position, block in enumerate(ordered):
        prev_hash = ordered[position - 1].content_hash if position > 0 else ""
        next_hash = ordered[position + 1].content_hash if position + 1 < len(ordered) else ""
        index[block.span_id] = (prev_hash, next_hash)
    return index


def _pick_unique(
    block: DocumentBlock,
    candidates: list[DocumentBlock],
    want_neighbors: tuple[str, str],
    to_neighbors: dict[str, tuple[str, str]],
) -> DocumentBlock | None:
    scored = [
        (_context_score(block, candidate, want_neighbors, to_neighbors.get(candidate.span_id, ("", ""))), candidate)
        for candidate in candidates
    ]
    scored = [pair for pair in scored if pair[0] > 0]
    if not scored:
        return None
    scored.sort(key=lambda pair: (-pair[0], pair[1].ordinal))
    if len(scored) > 1 and scored[1][0] == scored[0][0]:
        return None  # a tie stays ambiguous → needs_reanchor
    return scored[0][1]


def _context_score(
    block: DocumentBlock,
    candidate: DocumentBlock,
    want_neighbors: tuple[str, str],
    have_neighbors: tuple[str, str],
) -> int:
    score = 0
    if block.section_path and block.section_path == candidate.section_path:
        score += 3
    if block.page is not None and block.page == candidate.page:
        score += 2
    if block.bbox is not None and candidate.bbox is not None and block.bbox == candidate.bbox:
        score += 2
    want_prev, want_next = want_neighbors
    have_prev, have_next = have_neighbors
    if want_prev and want_prev == have_prev:
        score += 1
    if want_next and want_next == have_next:
        score += 1
    return score

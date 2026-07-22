"""Deterministic cross-run span re-anchoring (spec_source_ingestion_v2 §2.4).

A new ExtractionRun over the same revision attempts to rebind each old span to a
new one. An exact content-hash match wins **only** when it is unique within the
resolution scope; duplicated hashes (boilerplate, repeated equations) disambiguate
via section path, page/geometry, and neighboring-block context. A still-ambiguous
or unresolved span becomes ``needs_reanchor`` — never silently resolved and never
semantically stale. Successful aliases persist in ``source_span_reanchors``.
"""

from __future__ import annotations

import difflib
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


# ---------------------------------------------------------------------------
# Sub-block (annotation-anchor) re-anchoring (spec_p3_reader_integration §4.4).
#
# On a new render of the SAME extraction only the crosswalk rebuilds -- source
# anchors do not change. On a new extraction/revision: reuse the deterministic
# block reanchor above to find the candidate block, then within it require a
# unique exact-quote match; disambiguate duplicates with prefix/suffix; if the
# source text changed, compute a bounded fuzzy candidate + confidence but NEVER
# auto-accept an ambiguous match (the caller gates on a registered confidence
# floor). Automatic reanchor never changes annotation content or mappings.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SubBlockAnchor:
    to_span_id: str
    codepoint_start: int
    codepoint_end: int
    quote: str
    status: str  # exact | reanchored | needs_reanchor
    confidence: float
    block_content_hash: str = ""


def _locate_with_context(text: str, quote: str, prefix: str, suffix: str) -> int | None:
    """Among duplicate quote occurrences, pick the one whose surrounding text best
    matches the stored prefix/suffix. Returns the unique winning start or None."""

    starts: list[int] = []
    idx = text.find(quote)
    while idx != -1:
        starts.append(idx)
        idx = text.find(quote, idx + 1)
    if not starts:
        return None
    if len(starts) == 1:
        return starts[0]
    scored: list[tuple[int, int]] = []
    for start in starts:
        before = text[max(0, start - len(prefix)) : start]
        after = text[start + len(quote) : start + len(quote) + len(suffix)]
        score = 0
        if prefix and before.endswith(prefix[-len(before):] if before else prefix):
            score += 1
        if prefix and before == prefix:
            score += 2
        if suffix and after.startswith(suffix[: len(after)] if after else suffix):
            score += 1
        if suffix and after == suffix:
            score += 2
        scored.append((score, start))
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    if scored[0][0] == 0:
        return None
    if len(scored) > 1 and scored[1][0] == scored[0][0]:
        return None  # tie stays ambiguous
    return scored[0][1]


def _fuzzy_locate(text: str, quote: str) -> tuple[int, int, float] | None:
    """Bounded fuzzy candidate when the source text changed and the exact quote is
    gone. Returns (start, end, confidence) of the best matching window, or None."""

    if not quote or not text:
        return None
    matcher = difflib.SequenceMatcher(None, text, quote, autojunk=False)
    match = matcher.find_longest_match(0, len(text), 0, len(quote))
    if match.size == 0:
        return None
    ratio = match.size / len(quote)
    # Expand the window to cover the aligned block region.
    start = match.a - match.b
    start = max(0, start)
    end = min(len(text), start + len(quote))
    return start, end, round(ratio, 4)


def reanchor_subblock(
    from_ir: DocumentIR,
    to_ir: DocumentIR,
    *,
    from_span_id: str,
    quote: str,
    prefix: str = "",
    suffix: str = "",
    block_result: ReanchorResult | None = None,
) -> SubBlockAnchor:
    """Re-anchor one annotation segment from ``from_ir`` onto ``to_ir``. Never
    raises; an unresolved/ambiguous segment returns ``status='needs_reanchor'`` with
    the best-effort candidate so the caller can gate on its confidence floor."""

    result = block_result if block_result is not None else reanchor_spans(from_ir, to_ir)
    alias = result.alias_for(from_span_id)
    if alias is None:
        return SubBlockAnchor("", 0, 0, quote, "needs_reanchor", 0.0)
    to_block = to_ir.block_by_span(alias.to_span_id)
    if to_block is None:
        return SubBlockAnchor("", 0, 0, quote, "needs_reanchor", 0.0)
    text = to_block.text
    occurrences = text.count(quote)
    if occurrences == 1:
        start = text.index(quote)
        status = "exact" if alias.match_kind == EXACT_HASH and alias.confidence >= 0.999 else "reanchored"
        return SubBlockAnchor(alias.to_span_id, start, start + len(quote), quote, status, alias.confidence, to_block.content_hash)
    if occurrences > 1:
        start = _locate_with_context(text, quote, prefix, suffix)
        if start is not None:
            return SubBlockAnchor(alias.to_span_id, start, start + len(quote), quote, "reanchored", round(alias.confidence * 0.9, 4), to_block.content_hash)
        return SubBlockAnchor(alias.to_span_id, 0, 0, quote, "needs_reanchor", 0.0, to_block.content_hash)
    # occurrences == 0: source text changed. Bounded fuzzy candidate, never auto-accept here.
    fuzzy = _fuzzy_locate(text, quote)
    if fuzzy is None:
        return SubBlockAnchor(alias.to_span_id, 0, 0, quote, "needs_reanchor", 0.0, to_block.content_hash)
    start, end, ratio = fuzzy
    return SubBlockAnchor(alias.to_span_id, start, end, text[start:end], "needs_reanchor", ratio, to_block.content_hash)

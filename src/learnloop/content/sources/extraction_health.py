"""Deterministic extraction-health analysis (spec_source_ingestion_v2 §2.5, §5.3).

Turns an ExtractionRun's per-page stats and block structure into flagged page
ranges with human-readable reasons — the single analysis that powers both the
source card's health line and the "Improve N difficult pages" repair dialog. It
is pure and deterministic: no fetch, no re-extraction, no LLM.

Flagging reasons (§2.5):
- image_only ................ a page with figures/images but no readable text
- low_text_density ......... far fewer text blocks than neighboring pages
- replacement_chars ........ U+FFFD replacement characters in the page's text
- heading_discontinuity .... a heading level was skipped across the page
- near_empty_table ......... a table block with essentially no cell text
- method_differs ........... the page's extraction method differs from neighbors
plus any native page flags carried on the marker ``page_stats``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from learnloop.ingest.ir import DocumentIR

_REPLACEMENT_CHAR = "�"
_IMAGE_BLOCK_TYPES = {"figure", "picture", "figuregroup", "image", "table", "tablegroup"}
_TABLE_BLOCK_TYPES = {"table", "tablegroup", "tablecell"}
_NEAR_EMPTY_TABLE_CHARS = 8
_LOW_DENSITY_RATIO = 0.34


@dataclass(frozen=True)
class FlaggedPageRange:
    page_range: tuple[int, int]
    reasons: list[str]


@dataclass
class ExtractionHealthReport:
    flagged_pages: list[FlaggedPageRange] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    @property
    def difficult_page_count(self) -> int:
        return sum(hi - lo + 1 for (lo, hi) in (fp.page_range for fp in self.flagged_pages))

    def as_dict(self) -> dict:
        return {
            "flagged_pages": [
                {"page_range": list(fp.page_range), "reasons": list(fp.reasons)}
                for fp in self.flagged_pages
            ],
            "flags": list(self.flags),
            "difficult_page_count": self.difficult_page_count,
        }


def analyze_extraction_health(ir: DocumentIR) -> ExtractionHealthReport:
    """Analyze one IR into flagged page ranges with reasons (§2.5)."""

    blocks_by_page: dict[int, list] = {}
    for block in ir.blocks:
        if block.page is not None:
            blocks_by_page.setdefault(block.page, []).append(block)

    page_health = {ph.page: ph for ph in ir.health.pages}
    pages = sorted(set(blocks_by_page) | set(page_health))
    if not pages:
        return ExtractionHealthReport(flagged_pages=[], flags=list(ir.health.flags))

    text_counts = {page: _text_block_count(blocks_by_page.get(page, [])) for page in pages}
    methods = {page: _method(page_health.get(page)) for page in pages}

    per_page: dict[int, list[str]] = {}
    for page in pages:
        reasons = _page_reasons(
            page,
            blocks_by_page.get(page, []),
            page_health.get(page),
            text_counts,
            methods,
            pages,
        )
        if reasons:
            per_page[page] = sorted(set(reasons))

    return ExtractionHealthReport(
        flagged_pages=_merge_ranges(per_page),
        flags=list(ir.health.flags),
    )


def _page_reasons(page, blocks, ph, text_counts, methods, pages) -> list[str]:
    reasons: list[str] = []
    if ph is not None:
        reasons.extend(ph.flags)

    non_empty = [b for b in blocks if b.text and b.text.strip()]
    text_blocks = [b for b in non_empty if b.block_type.replace(" ", "").lower() not in _IMAGE_BLOCK_TYPES]
    image_blocks = [b for b in non_empty if b.block_type.replace(" ", "").lower() in _IMAGE_BLOCK_TYPES]
    if image_blocks and not text_blocks:
        reasons.append("image_only")

    if any(_REPLACEMENT_CHAR in (b.text or "") for b in blocks):
        reasons.append("replacement_chars")

    for b in blocks:
        if b.block_type.replace(" ", "").lower() in _TABLE_BLOCK_TYPES and len((b.text or "").strip()) < _NEAR_EMPTY_TABLE_CHARS:
            reasons.append("near_empty_table")
            break

    if _has_heading_discontinuity(blocks):
        reasons.append("heading_discontinuity")

    if _is_low_density(page, text_counts, pages):
        reasons.append("low_text_density")

    if _method_differs(page, methods, pages):
        reasons.append("method_differs")

    return reasons


def _text_block_count(blocks) -> int:
    return sum(
        1
        for b in blocks
        if b.text
        and b.text.strip()
        and b.block_type.replace(" ", "").lower() not in _IMAGE_BLOCK_TYPES
    )


def _method(ph) -> str | None:
    return ph.text_extraction_method if ph is not None else None


def _has_heading_discontinuity(blocks) -> bool:
    depths = [len(b.section_path) for b in blocks if b.section_path]
    prev: int | None = None
    for depth in depths:
        if prev is not None and depth - prev >= 2:
            return True
        prev = depth
    return False


def _is_low_density(page, text_counts, pages) -> bool:
    here = text_counts.get(page, 0)
    neighbors = [text_counts.get(p, 0) for p in _neighbors(page, pages)]
    neighbors = [n for n in neighbors if n > 0]
    if not neighbors:
        return False
    avg = sum(neighbors) / len(neighbors)
    return avg >= 3 and here < avg * _LOW_DENSITY_RATIO


def _method_differs(page, methods, pages) -> bool:
    here = methods.get(page)
    if here is None:
        return False
    neighbor_methods = [methods.get(p) for p in _neighbors(page, pages)]
    neighbor_methods = [m for m in neighbor_methods if m is not None]
    if not neighbor_methods:
        return False
    return all(m != here for m in neighbor_methods)


def _neighbors(page, pages) -> list[int]:
    ordered = sorted(pages)
    idx = ordered.index(page)
    out: list[int] = []
    if idx > 0:
        out.append(ordered[idx - 1])
    if idx + 1 < len(ordered):
        out.append(ordered[idx + 1])
    return out


def _merge_ranges(per_page: dict[int, list[str]]) -> list[FlaggedPageRange]:
    """Merge contiguous flagged pages into ranges, unioning their reasons."""

    result: list[FlaggedPageRange] = []
    run_pages: list[int] = []
    run_reasons: set[str] = set()
    for page in sorted(per_page):
        if run_pages and page == run_pages[-1] + 1:
            run_pages.append(page)
            run_reasons.update(per_page[page])
        else:
            if run_pages:
                result.append(FlaggedPageRange((run_pages[0], run_pages[-1]), sorted(run_reasons)))
            run_pages = [page]
            run_reasons = set(per_page[page])
    if run_pages:
        result.append(FlaggedPageRange((run_pages[0], run_pages[-1]), sorted(run_reasons)))
    return result

"""What the tutor actually reads of its sources (tutor delivery fixes, 2026-10-13).

Three rules, shared by every tutor context:

* **Complete blocks.** A passage reaches the tutor as its whole canonical
  block text (``source_document_blocks.text``, unchanged, so offsets into it
  stay canonical), never a preview cut. The only cut is the budget's.
* **One explicit budget.** ``tutor_qa.context_token_budget`` bounds the source
  text of one tutor turn (the repository's chars/4 token estimate). Passages
  are kept in priority order; the first one that does not fit is trimmed to
  what is left (a prefix of its canonical text, at a word boundary) and every
  later one is dropped. A trim or a drop is recorded on the question's
  ``source_context.delivery``.
* **Followed references.** "by Theorem 3.2", "Example 1.4.13", "Equation
  (3.4)" in a delivered passage (or the learner's selection) is resolved to the
  numbered block of the same extraction (``ingest.block_roles``' numbered
  environments): the nearest occurrence before the passage, else the nearest
  after it; never another extraction or source. The block, with the blocks
  that complete its statement, joins the context as ``referenced`` citation
  spans, within the budget and the caller's material rule (held-out and exam
  material never). A reference that does not resolve is recorded.

Reader neighbours (``neighbour_order``) are the nearest content blocks around
the passage in view, alternating sides and widening: i-1, i+1, i-2, i+2, ...

Nothing here is evidence: the delivery is context for one answer, and replay
reads none of it.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
import math
from pathlib import Path
import re
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.stores.source_block_fts import EXCLUDED_BLOCK_TYPES, BlockRow, extraction_blocks
from learnloop.ingest.block_roles import (
    NumberedLabel,
    NumberedReference,
    lead_role,
    numbered_label,
    numbered_references,
)

#: The repository's token estimate (``ai.spend``, ``source_outline``): characters / 4.
CHARS_PER_TOKEN = 4
#: Content blocks delivered on each side of a Reader passage.
NEIGHBOUR_RADIUS = 3
#: Distinct references followed per tutor turn (the rest are recorded unresolved).
MAX_REFERENCES = 4
#: Blocks one referenced environment may span (its numbered block included).
MAX_REFERENCE_BLOCKS = 4
#: The smallest remainder worth a trimmed passage; below it the passage is dropped.
MIN_TRIM_TOKENS = 32

_TERMINAL = re.compile(r"[.!?…)\]]\s*(?:\$\$|\\\]|\$)?\s*[*_]*\s*$")
_HEADER_TYPES = frozenset({"sectionheader", "title", "heading"})
_EQUATION_TYPES = frozenset({"equation", "equationnumber", "math"})
_BOUNDARY_LEADS = frozenset({"proof", "solution"})

#: ``allow(extraction_id, block) -> None`` (allowed) or the reason it is not.
BlockFilter = Callable[[str, BlockRow], str | None]
SpanKey = tuple[str, str]


def estimate_tokens(text: str | None) -> int:
    return math.ceil(len(text or "") / CHARS_PER_TOKEN)


def _block_kind(block: BlockRow) -> str:
    return (block.block_type or "").replace(" ", "").lower()


def is_content(block: BlockRow) -> bool:
    """A block a reader would read: not page furniture, not empty."""

    return block.block_type not in EXCLUDED_BLOCK_TYPES and bool((block.text or "").strip())


@dataclass
class ExtractionText:
    """One extraction's blocks in document order, with its numbered labels."""

    extraction_id: str
    blocks: list[BlockRow]
    _positions: dict[str, int] = field(default_factory=dict)
    _labels: dict[str, list[tuple[int, NumberedLabel]]] | None = None

    def __post_init__(self) -> None:
        self._positions = {block.span_id: index for index, block in enumerate(self.blocks)}

    def position(self, span_id: str) -> int | None:
        return self._positions.get(str(span_id))

    def block(self, span_id: str) -> BlockRow | None:
        index = self.position(span_id)
        return None if index is None else self.blocks[index]

    def label_of(self, index: int) -> NumberedLabel | None:
        block = self.blocks[index]
        return numbered_label(block.text, block.block_type) if is_content(block) else None

    @property
    def labels(self) -> dict[str, list[tuple[int, NumberedLabel]]]:
        """``number -> [(position, label)]`` of every numbered block, in order."""

        if self._labels is None:
            labels: dict[str, list[tuple[int, NumberedLabel]]] = {}
            for index in range(len(self.blocks)):
                label = self.label_of(index)
                if label is not None:
                    labels.setdefault(label.number, []).append((index, label))
            self._labels = labels
        return self._labels

    def resolve(self, reference: NumberedReference, anchor: int) -> int | None:
        """The numbered block ``reference`` names, nearest before ``anchor``, else after.

        A named reference ("Theorem 3.2") matches a label of its kind; a bare
        number ("by 1.32") a number-first label of any kind."""

        positions = [
            index for index, label in self.labels.get(reference.number, [])
            if (label.number_first if reference.kind is None else label.kind == reference.kind)
        ]
        before = [index for index in positions if index < anchor]
        if before:
            return before[-1]
        after = [index for index in positions if index > anchor]
        return after[0] if after else None


class BlockSource:
    """Extraction texts read once per delivery (read-only)."""

    def __init__(self, sqlite_path: Path | str) -> None:
        self.sqlite_path = Path(sqlite_path)
        self._cache: dict[str, ExtractionText | None] = {}

    def extraction(self, extraction_id: str | None) -> ExtractionText | None:
        if not extraction_id:
            return None
        key = str(extraction_id)
        if key not in self._cache:
            with closing(connect(self.sqlite_path, read_only=True)) as connection:
                blocks = extraction_blocks(connection, key)
            self._cache[key] = ExtractionText(key, blocks) if blocks else None
        return self._cache[key]

    def block(self, extraction_id: str | None, span_id: str | None) -> BlockRow | None:
        text = self.extraction(extraction_id)
        return None if text is None or span_id is None else text.block(str(span_id))


def passage_label(text: str | None) -> str:
    """A short citation label from a passage's own words."""

    value = " ".join((text or "").split())
    return value[:59].rstrip() + "…" if len(value) > 60 else value


def neighbour_order(text: ExtractionText, first: int, last: int, *, radius: int = NEIGHBOUR_RADIUS) -> list[tuple[int, int]]:
    """``(position, offset)`` of the content blocks around ``first..last``,
    nearest first and alternating sides: i-1, i+1, i-2, i+2, ... up to
    ``radius`` content blocks on each side (offset negative before, positive
    after). Page furniture and empty blocks are not neighbours."""

    before: list[int] = []
    index = first - 1
    while index >= 0 and len(before) < radius:
        if is_content(text.blocks[index]):
            before.append(index)
        index -= 1
    after: list[int] = []
    index = last + 1
    while index < len(text.blocks) and len(after) < radius:
        if is_content(text.blocks[index]):
            after.append(index)
        index += 1
    order: list[tuple[int, int]] = []
    for distance in range(radius):
        if distance < len(before):
            order.append((before[distance], -(distance + 1)))
        if distance < len(after):
            order.append((after[distance], distance + 1))
    return order


@dataclass
class References:
    """The referenced spans to add, and what was and was not followed."""

    spans: list[dict[str, Any]] = field(default_factory=list)
    resolved: list[dict[str, Any]] = field(default_factory=list)
    unresolved: list[dict[str, Any]] = field(default_factory=list)

    def describe(self) -> dict[str, Any]:
        return {"resolved": list(self.resolved), "unresolved": list(self.unresolved)}

    @property
    def empty(self) -> bool:
        return not (self.spans or self.resolved or self.unresolved)


def _completes_statement(previous: BlockRow, following: BlockRow, *, header: bool) -> bool:
    """Whether ``following`` still belongs to the environment ``previous`` is part of."""

    if _block_kind(following) in _HEADER_TYPES:
        return False
    if lead_role(following.text) in _BOUNDARY_LEADS:
        return False
    if header:
        return True
    if _block_kind(following) in _EQUATION_TYPES:
        return True
    return not _TERMINAL.search(previous.text or "")


def _environment(text: ExtractionText, start: int) -> list[int]:
    """The numbered block at ``start`` and the blocks completing its statement:
    a heading label's body, a display equation after it, or a sentence the
    label block leaves open ("... The naive probability of A is" + the
    formula), up to ``MAX_REFERENCE_BLOCKS`` blocks, never into the next
    numbered block, heading, proof or solution."""

    group = [start]
    header = _block_kind(text.blocks[start]) in _HEADER_TYPES
    previous = text.blocks[start]
    index = start + 1
    while index < len(text.blocks) and len(group) < MAX_REFERENCE_BLOCKS:
        block = text.blocks[index]
        if not is_content(block):
            index += 1
            continue
        if text.label_of(index) is not None or not _completes_statement(previous, block, header=header):
            break
        group.append(index)
        previous = block
        index += 1
    return group


def follow_references(
    source: BlockSource,
    spans: Sequence[Mapping[str, Any]],
    *,
    allow: BlockFilter,
    delivered: Iterable[SpanKey] = (),
    max_references: int = MAX_REFERENCES,
    span_extra: Callable[[str, BlockRow], Mapping[str, Any]] | None = None,
) -> References:
    """Resolve the numbered references in ``spans`` (in order) to ``referenced`` spans.

    A span is scanned in its own extraction, anchored at its own block (the
    learner's quoted selection at the block it is anchored to). ``allow``
    keeps the caller's material rule: a numbered block it refuses is recorded
    unresolved with its reason, and a continuation block it refuses ends the
    environment there. ``delivered`` spans are not repeated. ``span_extra``
    adds caller fields (a source title) to each new span."""

    result = References()
    seen_keys: set[SpanKey] = {(str(key[0]), str(key[1])) for key in delivered}
    followed: set[tuple[str, str | None, str]] = set()
    for span in spans:
        extraction_id = str(span.get("extraction_id") or "")
        span_id = str(span.get("span_id") or "")
        text = source.extraction(extraction_id)
        if text is None:
            continue
        anchor = text.position(span_id)
        if anchor is None:
            continue
        own = text.label_of(anchor)
        for reference in numbered_references(str(span.get("text") or "")):
            if own is not None and (own.kind, own.number) == (reference.kind, reference.number):
                continue
            key = (extraction_id, reference.kind, reference.number)
            if key in followed:
                continue
            followed.add(key)
            entry = {"reference": reference.text, "extraction_id": extraction_id, "from_span_id": span_id}
            target = text.resolve(reference, anchor)
            if target is None:
                # A bare number ("by 1.32") that names no number-first label is prose, not a reference.
                if reference.kind is not None:
                    result.unresolved.append({**entry, "reason": "no numbered block with this label"})
                continue
            if target == anchor:
                continue
            block = text.blocks[target]
            refused = allow(extraction_id, block)
            if refused is not None:
                result.unresolved.append({**entry, "span_id": block.span_id, "reason": refused})
                continue
            if len(result.resolved) >= max_references:
                result.unresolved.append({**entry, "span_id": block.span_id,
                                          "reason": f"more than {max_references} references in one turn"})
                continue
            added: list[str] = []
            for position in _environment(text, target):
                member = text.blocks[position]
                member_key = (extraction_id, member.span_id)
                if position != target and allow(extraction_id, member) is not None:
                    break
                if member_key in seen_keys:
                    continue
                seen_keys.add(member_key)
                added.append(member.span_id)
                result.spans.append({
                    "extraction_id": extraction_id,
                    "span_id": member.span_id,
                    "label": passage_label(member.text),
                    "text": member.text,
                    "relation": "referenced",
                    "reference": reference.text if position == target else f"{reference.text} (continued)",
                    "referenced_from": [extraction_id, span_id],
                    **(dict(span_extra(extraction_id, member)) if span_extra is not None else {}),
                })
            result.resolved.append({**entry, "span_id": block.span_id, "spans": added,
                                    **({"already_delivered": True} if not added else {})})
    return result


def _trim(text: str, max_chars: int) -> str:
    """A prefix of ``text`` of at most ``max_chars``, cut at a word boundary
    when one is near (the last tenth); the canonical text up to that point."""

    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    space = max(cut.rfind(" "), cut.rfind("\n"))
    if space >= max_chars - max(1, max_chars // 10):
        cut = cut[:space]
    return cut


def apply_budget(spans: Sequence[Mapping[str, Any]], budget_tokens: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Keep ``spans`` in order within ``budget_tokens``: the first that does not
    fit is trimmed to the remainder (dropped below ``MIN_TRIM_TOKENS``), every
    later one dropped. Returns the kept spans and the budget receipt."""

    kept: list[dict[str, Any]] = []
    trimmed: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    used = 0
    full = False
    for span in spans:
        text = str(span.get("text") or "")
        tokens = estimate_tokens(text)
        key = {"extraction_id": span.get("extraction_id"), "span_id": span.get("span_id"),
               "relation": span.get("relation"), "tokens": tokens}
        if not full and used + tokens <= budget_tokens:
            kept.append(dict(span))
            used += tokens
            continue
        if not full and budget_tokens - used >= MIN_TRIM_TOKENS:
            cut = _trim(text, (budget_tokens - used) * CHARS_PER_TOKEN)
            kept.append({**span, "text": cut, "trimmed": {"kept_chars": len(cut), "total_chars": len(text)}})
            used += estimate_tokens(cut)
            trimmed.append({**key, "kept_chars": len(cut), "total_chars": len(text)})
        else:
            dropped.append(key)
        full = True
    return kept, {"budget_tokens": budget_tokens, "used_tokens": used, "spans": len(kept),
                  "trimmed": trimmed, "dropped": dropped}


def hydrate(source: BlockSource, spans: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Each span with its complete canonical block text (when its block is
    found); returns the spans and how many were completed from a cut."""

    out: list[dict[str, Any]] = []
    completed = 0
    for span in spans:
        block = source.block(span.get("extraction_id"), span.get("span_id"))
        if block is None or not (block.text or "").strip():
            out.append(dict(span))
            continue
        if (span.get("text") or "") != block.text:
            completed += 1
        out.append({**span, "text": block.text})
    return out, completed


def notable(receipt: Mapping[str, Any]) -> bool:
    """Whether a delivery receipt records something (a trim, a drop, a reference)."""

    references = receipt.get("references") or {}
    return bool(receipt.get("trimmed") or receipt.get("dropped")
                or references.get("resolved") or references.get("unresolved"))


__all__ = [
    "CHARS_PER_TOKEN",
    "MAX_REFERENCES",
    "MAX_REFERENCE_BLOCKS",
    "MIN_TRIM_TOKENS",
    "NEIGHBOUR_RADIUS",
    "BlockFilter",
    "BlockSource",
    "ExtractionText",
    "References",
    "apply_budget",
    "estimate_tokens",
    "follow_references",
    "hydrate",
    "is_content",
    "neighbour_order",
    "notable",
    "passage_label",
]

"""E0 delivery arms D0-D3 (spec §5.3): what the same tutor reads.

* **D0, today's context**: the delivery stage's kill-switch behaviour
  (``tutor_qa.expanded_delivery = false``, ``resolve_references = false``):
  for a Reader selection the span view's predecessor window (three blocks
  before, then three after, furniture and empty blocks included, 240-character
  previews) until max(4, spans + 2) spans, so a quoted one-block selection gets
  i-3 and i-2 only; for retrieved evidence the first four spans cut to 600
  whitespace-collapsed characters.
* **D1, fixed delivery**: the delivery stage's behaviour: complete blocks, the
  nearest neighbours i-1, i+1, widening to three a side, numbered references
  followed in the same extraction, all within ``D1_EVIDENCE_TOKENS`` (8,192,
  chars/4) with trims and drops recorded.
* **D2, whole section**: every permitted block of the smallest outline unit
  holding the selection (else its section path), complete, in order;
  omissions recorded.
* **D3, whole source**: every permitted block of the selected source.

Both D0 and D1 are rebuilt from ``learnloop.tutor.context_delivery``'s public
primitives; ``tests/test_e0_delivery.py`` checks them span for span against
``tutor_qa``'s own Reader delivery with the kill switch off and on.

The experiment's policy is stricter than the Reader's held-out-only neighbour
filter: every arm drops what ``PolicySnapshot`` withholds (solutions, the
assessment lane, exam and held-out material) and records it. No arm ever
delivers solution or learner-held-out text, even as a "direct" control. A
D2/D3 delivery that does not fit the generator's context records
``does_not_fit`` and runs its named bounded fallback (D2 -> D1, D3 -> D2);
nothing is silently truncated.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.db.stores.source_block_fts import BlockRow
from learnloop.tutor.context_delivery import (
    MAX_REFERENCES,
    NEIGHBOUR_RADIUS,
    PREVIEW_CHARS,
    SPAN_CHARS,
    BlockSource,
    apply_budget,
    estimate_tokens,
    follow_references,
    is_content,
    neighbour_order,
    passage_label,
    predecessor_window,
)

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.corpus import CorpusSnapshot

#: The production tutor's defaults the D0 baseline used (tutor_qa).
D0_BUDGET_TOKENS = 24_000
MAX_CITATION_SPANS = 4
MAX_SELECTION_SPANS = 8


@dataclass
class Selection:
    """A known location: a Reader selection (its primary block, the other
    blocks it covers, the learner's exact quote)."""

    extraction_id: str
    span_id: str
    selection_span_ids: tuple[str, ...] = ()
    quote: str | None = None


@dataclass
class Delivered:
    arm: str
    spans: list[dict[str, Any]]
    receipt: dict[str, Any] = field(default_factory=dict)

    @property
    def tokens(self) -> int:
        return sum(estimate_tokens(span.get("text")) for span in self.spans)

    def coverage(self, blocks: Mapping[tuple[str, str], BlockRow]) -> list[tuple[str, str, int, int]]:
        """``(extraction, span, start, end)`` of canonical text actually
        delivered (a cut covers only its canonical prefix)."""

        found: list[tuple[str, str, int, int]] = []
        for span in self.spans:
            if span.get("relation") == "selected_text":
                continue
            key = (str(span.get("extraction_id")), str(span.get("span_id")))
            block = blocks.get(key)
            if block is None:
                continue
            start = int(span.get("start") or 0)
            end = start + canonical_prefix_end(block.text[start:], str(span.get("text") or ""))
            if end > start:
                found.append((key[0], key[1], start, end))
        return found


def canonical_prefix_end(canonical: str, delivered: str) -> int:
    """How much of ``canonical`` a delivered prefix covers: exact for a
    canonical prefix, and for a whitespace-collapsed cut the canonical offset
    reached after the same non-whitespace characters."""

    if canonical.startswith(delivered):
        return len(delivered)
    wanted = sum(1 for char in delivered if not char.isspace())
    seen = 0
    for index, char in enumerate(canonical):
        if not char.isspace():
            seen += 1
            if seen >= wanted:
                return index + 1
    return len(canonical)


class _Policy:
    def __init__(self, snapshot: CorpusSnapshot) -> None:
        self.snapshot = snapshot
        self.dropped: list[dict[str, Any]] = []

    def refused(self, extraction_id: str, block: Any) -> str | None:
        return self.snapshot.policy.verdict(extraction_id, str(block.span_id))

    def keep(self, spans: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        kept: list[dict[str, Any]] = []
        for span in spans:
            reason = self.snapshot.policy.verdict(str(span.get("extraction_id")), str(span.get("span_id")))
            if reason is not None and span.get("relation") != "selected_text":
                self.dropped.append({"span_id": span.get("span_id"), "relation": span.get("relation"),
                                     "reason": reason})
                continue
            kept.append(dict(span))
        return kept


def _span(extraction_id: str, block: BlockRow, relation: str, **extra: Any) -> dict[str, Any]:
    return {"extraction_id": extraction_id, "span_id": block.span_id, "label": passage_label(block.text),
            "text": block.text, "relation": relation, **extra}


def _selection_spans(text: Any, selection: Selection) -> tuple[list[dict[str, Any]], list[int]] | None:
    primary = text.position(selection.span_id)
    if primary is None:
        return None
    spans: list[dict[str, Any]] = []
    if selection.quote and selection.quote.strip():
        spans.append({"extraction_id": selection.extraction_id, "span_id": selection.span_id,
                      "label": "learner selection", "text": selection.quote, "relation": "selected_text"})
    spans.append(_span(selection.extraction_id, text.blocks[primary], "in_view"))
    in_view = [primary]
    for extra_id in list(dict.fromkeys(selection.selection_span_ids))[:MAX_SELECTION_SPANS]:
        position = text.position(extra_id)
        if extra_id == selection.span_id or position is None:
            continue
        in_view.append(position)
        spans.append(_span(selection.extraction_id, text.blocks[position], "in_view"))
    return spans, in_view


def reader_d0(source: BlockSource, snapshot: CorpusSnapshot, selection: Selection,
              *, budget_tokens: int = D0_BUDGET_TOKENS) -> Delivered:
    """Today's Reader context (the kill switch off; no references)."""

    policy = _Policy(snapshot)
    text = source.extraction(selection.extraction_id)
    built = _selection_spans(text, selection) if text is not None else None
    if built is None:
        return Delivered("D0", [], {"error": "selection_not_found"})
    spans, _in_view = built
    primary = text.position(selection.span_id)
    limit = max(MAX_CITATION_SPANS, len(spans) + 2)
    neighbours: list[dict[str, Any]] = []
    withheld = 0
    for position in predecessor_window(text, primary):
        if len(spans) + len(neighbours) >= limit:
            break
        block = text.blocks[position]
        if policy.refused(selection.extraction_id, block) is not None:
            withheld += 1
            continue
        preview = (block.text or "")[:PREVIEW_CHARS]
        neighbours.append({"extraction_id": selection.extraction_id, "span_id": block.span_id,
                           "label": passage_label(preview), "text": preview, "relation": "surrounding"})
    kept, receipt = apply_budget(policy.keep([*spans, *neighbours]), budget_tokens)
    receipt["neighbours"] = {"window": "predecessor", "delivered": len(neighbours), "withheld": withheld}
    receipt["policy_dropped"] = policy.dropped
    return Delivered("D0", kept, receipt)


def reader_d1(source: BlockSource, snapshot: CorpusSnapshot, selection: Selection,
              *, budget_tokens: int = pins.D1_EVIDENCE_TOKENS) -> Delivered:
    """The delivery stage's Reader context within the D1 ceiling."""

    policy = _Policy(snapshot)
    extraction_id = selection.extraction_id
    text = source.extraction(extraction_id)
    built = _selection_spans(text, selection) if text is not None else None
    if built is None:
        return Delivered("D1", [], {"error": "selection_not_found"})
    spans, in_view = built
    delivered = {(extraction_id, str(span["span_id"])) for span in spans}
    cited = follow_references(source, spans, allow=policy.refused, delivered=delivered)
    delivered |= {(extraction_id, str(span["span_id"])) for span in cited.spans}
    neighbours: list[dict[str, Any]] = []
    withheld = 0
    for position, offset in neighbour_order(text, min(in_view), max(in_view)):
        block = text.blocks[position]
        if (extraction_id, block.span_id) in delivered:
            continue
        if policy.refused(extraction_id, block) is not None:
            withheld += 1
            continue
        neighbours.append(_span(extraction_id, block, "surrounding", offset=offset))
        delivered.add((extraction_id, block.span_id))
    further = follow_references(source, neighbours, allow=policy.refused, delivered=delivered,
                                max_references=max(0, MAX_REFERENCES - len(cited.resolved)))
    kept, receipt = apply_budget(policy.keep([*spans, *cited.spans, *neighbours, *further.spans]), budget_tokens)
    receipt["neighbours"] = {"radius": NEIGHBOUR_RADIUS, "delivered": len(neighbours), "withheld": withheld}
    receipt["references"] = {"resolved": [*cited.resolved, *further.resolved],
                             "unresolved": [*cited.unresolved, *further.unresolved]}
    receipt["policy_dropped"] = policy.dropped
    return Delivered("D1", kept, receipt)


def retrieved_d0(snapshot: CorpusSnapshot, unit_ids: Sequence[str]) -> Delivered:
    """Today's retrieved context: the first four spans, 600 collapsed characters."""

    policy = _Policy(snapshot)
    spans: list[dict[str, Any]] = []
    for unit_id in unit_ids:
        unit = snapshot.unit(unit_id)
        for member in unit.members:
            block = _block(snapshot, unit.extraction_id, member.span_id)
            if block is None or any(span["span_id"] == block.span_id for span in spans):
                continue
            spans.append({"extraction_id": unit.extraction_id, "span_id": block.span_id, "relation": "retrieved",
                          "label": passage_label(block.text), "text": " ".join(block.text.split())[:SPAN_CHARS]})
        if len(spans) >= MAX_CITATION_SPANS:
            break
    kept, receipt = apply_budget(policy.keep(spans[:MAX_CITATION_SPANS]), D0_BUDGET_TOKENS)
    receipt["policy_dropped"] = policy.dropped
    return Delivered("D0", kept, receipt)


def retrieved_d1(source: BlockSource, snapshot: CorpusSnapshot, unit_ids: Sequence[str],
                 *, budget_tokens: int = pins.D1_EVIDENCE_TOKENS) -> Delivered:
    """Complete blocks of the ranked units, their references, one budget."""

    policy = _Policy(snapshot)
    spans: list[dict[str, Any]] = []
    for unit_id in unit_ids:
        unit = snapshot.unit(unit_id)
        for member in unit.members:
            block = _block(snapshot, unit.extraction_id, member.span_id)
            if block is None or any(span["span_id"] == block.span_id and span["extraction_id"] == unit.extraction_id
                                    for span in spans):
                continue
            spans.append(_span(unit.extraction_id, block, "retrieved"))
    keys = {(span["extraction_id"], span["span_id"]) for span in spans}
    cited = follow_references(source, spans, allow=policy.refused, delivered=keys)
    kept, receipt = apply_budget(policy.keep([*spans, *cited.spans]), budget_tokens)
    receipt["references"] = cited.describe()
    receipt["policy_dropped"] = policy.dropped
    return Delivered("D1", kept, receipt)


def _block(snapshot: CorpusSnapshot, extraction_id: str, span_id: str) -> BlockRow | None:
    for block in snapshot.blocks.get(extraction_id, []):
        if block.span_id == span_id:
            return block
    return None


def _fits(tokens: int) -> bool:
    return tokens + sum(pins.GENERATOR_RESERVES.values()) <= pins.GENERATOR_CONTEXT_TOKENS


def _whole(snapshot: CorpusSnapshot, extraction_id: str, span_ids: Sequence[str] | None, arm: str) -> Delivered:
    policy = _Policy(snapshot)
    blocks = snapshot.blocks.get(extraction_id, [])
    wanted = None if span_ids is None else set(span_ids)
    spans: list[dict[str, Any]] = []
    omitted = {"withheld": 0, "furniture_or_empty": 0}
    for block in blocks:
        if wanted is not None and block.span_id not in wanted:
            continue
        if not is_content(block):
            omitted["furniture_or_empty"] += 1
            continue
        if policy.refused(extraction_id, block) is not None:
            omitted["withheld"] += 1
            continue
        spans.append(_span(extraction_id, block, "section" if arm == "D2" else "source"))
    return Delivered(arm, spans, {"omitted": omitted, "blocks": len(spans)})


def section_span_ids(snapshot: CorpusSnapshot, selection: Selection) -> tuple[list[str], str]:
    """The smallest outline unit holding the selection, else its section path."""

    containing = [unit for unit in snapshot.outline_units.get(selection.extraction_id, [])
                  if selection.span_id in unit.span_ids]
    if containing:
        smallest = min(containing, key=lambda unit: (len(unit.span_ids), unit.unit_id))
        return list(smallest.span_ids), "outline_unit"
    target = next((unit for unit in snapshot.units if unit.extraction_id == selection.extraction_id
                   and any(member.span_id == selection.span_id for member in unit.members)), None)
    if target is None:
        return [selection.span_id], "selection_only"
    ids = [member.span_id for unit in snapshot.units if unit.extraction_id == selection.extraction_id
           and unit.section == target.section for member in unit.members]
    return list(dict.fromkeys(ids)), "section_path"


def whole_section(source: BlockSource, snapshot: CorpusSnapshot, selection: Selection) -> Delivered:
    span_ids, basis = section_span_ids(snapshot, selection)
    result = _whole(snapshot, selection.extraction_id, span_ids, "D2")
    result.receipt["basis"] = basis
    if not _fits(result.tokens):
        fallback = reader_d1(source, snapshot, selection)
        fallback.arm = "D2_fallback_d1"
        fallback.receipt["does_not_fit"] = {"arm": "D2", "tokens": result.tokens}
        return fallback
    return result


def whole_source(source: BlockSource, snapshot: CorpusSnapshot, selection: Selection) -> Delivered:
    result = _whole(snapshot, selection.extraction_id, None, "D3")
    if not _fits(result.tokens):
        fallback = whole_section(source, snapshot, selection)
        fallback.receipt["does_not_fit"] = {"arm": "D3", "tokens": result.tokens}
        fallback.arm = "D3_fallback_" + fallback.arm.lower()
        return fallback
    return result


def deliver(arm: str, source: BlockSource, snapshot: CorpusSnapshot, selection: Selection) -> Delivered:
    if arm == "D0":
        return reader_d0(source, snapshot, selection)
    if arm == "D1":
        return reader_d1(source, snapshot, selection)
    if arm == "D2":
        return whole_section(source, snapshot, selection)
    if arm == "D3":
        return whole_source(source, snapshot, selection)
    raise ValueError(f"unknown delivery arm {arm!r}")


__all__ = ["Delivered", "Selection", "canonical_prefix_end", "deliver", "reader_d0", "reader_d1",
           "retrieved_d0", "retrieved_d1", "section_span_ids", "whole_section", "whole_source"]

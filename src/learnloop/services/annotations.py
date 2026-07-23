"""Annotation service (spec_p3_reader_integration §4, design B step 3).

Selection -> sub-block anchor translation, append-only annotation CRUD, and
cross-extraction sub-block reanchoring. All persistence is append-only: an edit or
reanchor appends a new version/anchor + event; deletion is a tombstone disposition
event (invariant 1.1.11). Anchors are sub-block: ordered segments pinning block
span id + block content hash + Unicode code-point offsets against SOURCE-BLOCK text
plus the exact quote and bounded prefix/suffix. Ambiguous translation saves the raw
selection + ``needs_reanchor`` and never discards learner text (§3.2, §13.3).
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.ingest.reanchor import reanchor_spans, reanchor_subblock

ALGO_VERSION = "anchor-v1"
_context_chars = 32

# Decision parameters (registered in parameter_registry §E).
SUBBLOCK_CONFIDENCE_MIN = 0.6
MANUAL_REVIEW_BATCH = 25

ANNOTATION_TYPES = ("highlight", "question", "confusion", "interpretation", "disposition")


class AnnotationError(ValueError):
    """Domain error for the annotation service."""


def _hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _neighbor_hashes(ir: Any, span_id: str) -> list[str]:
    blocks = sorted(ir.blocks, key=lambda b: b.ordinal)
    for i, block in enumerate(blocks):
        if block.span_id == span_id:
            prev_hash = blocks[i - 1].content_hash if i > 0 else ""
            next_hash = blocks[i + 1].content_hash if i + 1 < len(blocks) else ""
            return [prev_hash, next_hash]
    return ["", ""]


# Fuzzy tier acceptance: at least half the quote's word tokens must align
# inside one window of the block, and the window must not balloon far past the
# quote's own length (a degenerate alignment scattered across the block).
FUZZY_COVERAGE_MIN = 0.5
FUZZY_WINDOW_SLACK = 8


def _fuzzy_locate(text: str, quote: str) -> tuple[int, int] | None:
    """Tolerant alignment for quotes captured off a *rendered* surface (pdf.js
    text layer, rendered MathML): rendered glyphs and extraction text disagree
    wherever the extractor dropped math or stored it as LaTeX, so exact and
    whitespace-normalized matching both fail. Align word tokens with difflib and
    accept the covering window when enough of the quote lands in it; the offsets
    are approximate but stay inside the learner-chosen block."""

    text_tokens = [(m.group(0).casefold(), m.start(), m.end()) for m in re.finditer(r"\w+", text)]
    quote_tokens = [m.group(0).casefold() for m in re.finditer(r"\w+", quote)]
    if not text_tokens or not quote_tokens:
        return None
    matcher = difflib.SequenceMatcher(
        None, [token for token, _, _ in text_tokens], quote_tokens, autojunk=False
    )
    matching = [b for b in matcher.get_matching_blocks() if b.size > 0]
    if not matching:
        return None
    matched = sum(b.size for b in matching)
    if matched / len(quote_tokens) < FUZZY_COVERAGE_MIN:
        return None
    first, last = matching[0], matching[-1]
    window = (last.a + last.size) - first.a
    if window > 2 * len(quote_tokens) + FUZZY_WINDOW_SLACK:
        return None
    start = text_tokens[first.a][1]
    end = text_tokens[last.a + last.size - 1][2]
    # Snap outward to whitespace so a window ending inside a LaTeX run (e.g.
    # ``\mathbb{C}$.``) keeps the whole token in the exact quote.
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    while end < len(text) and not text[end].isspace():
        end += 1
    return start, end


# Context disambiguation: with client-supplied glyph context (the text around
# an atomic-unit capture), an occurrence may be chosen among several — but only
# when it wins clearly; a murky contest stays needs_reanchor (§3.2).
CONTEXT_SCORE_MIN = 0.4
CONTEXT_MARGIN_MIN = 0.1


def _context_score(
    text: str, start: int, end: int, prefix: str | None, suffix: str | None
) -> float:
    """Similarity between the extraction text around an occurrence and the
    rendered-surface context the capture arrived with (0..1)."""

    def normalize(value: str) -> str:
        return " ".join(value.split()).casefold()

    scores: list[float] = []
    if prefix:
        around = normalize(text[max(0, start - _context_chars) : start])
        scores.append(difflib.SequenceMatcher(None, around, normalize(prefix)[-_context_chars:]).ratio())
    if suffix:
        around = normalize(text[end : end + _context_chars])
        scores.append(difflib.SequenceMatcher(None, around, normalize(suffix)[:_context_chars]).ratio())
    return sum(scores) / len(scores) if scores else 0.0


def _disambiguate(
    text: str,
    candidates: list[tuple[int, int]],
    prefix: str | None,
    suffix: str | None,
) -> tuple[int, int] | None:
    """Pick among several occurrences of the same quote using surrounding
    context — only on a clear win; otherwise refuse (§3.2)."""

    if not (prefix or suffix):
        return None
    scored = sorted(
        ((_context_score(text, start, end, prefix, suffix), start, end) for start, end in candidates),
        reverse=True,
    )
    best, runner_up = scored[0], scored[1]
    if best[0] < CONTEXT_SCORE_MIN or best[0] - runner_up[0] < CONTEXT_MARGIN_MIN:
        return None
    return best[1], best[2]


def _locate_quote(
    text: str,
    quote: str | None,
    *,
    prefix: str | None = None,
    suffix: str | None = None,
) -> tuple[int, int] | None:
    """Locate a quote in source-block text: exact unique match first, else a
    unique whitespace-normalized match, else a fuzzy token alignment. The
    fallbacks matter for selections made over a PDF text layer or rendered
    math, whose glyphs legitimately differ from the extraction text. Repeated
    occurrences are disambiguated by the capture's surrounding glyph context
    when that context picks a clear winner; anything still unmatched or
    ambiguous stays ``needs_reanchor``."""

    if not quote:
        return None
    exact_count = text.count(quote)
    if exact_count == 1:
        start = text.index(quote)
        return start, start + len(quote)
    if exact_count > 1:
        candidates = []
        at = text.find(quote)
        while at != -1:
            candidates.append((at, at + len(quote)))
            at = text.find(quote, at + 1)
        return _disambiguate(text, candidates, prefix, suffix)
    tokens = quote.split()
    if not tokens:
        return None
    pattern = r"\s+".join(re.escape(token) for token in tokens)
    matches = list(re.finditer(pattern, text))
    if len(matches) == 1:
        return matches[0].start(), matches[0].end()
    if matches:
        return _disambiguate(text, [(m.start(), m.end()) for m in matches], prefix, suffix)
    # Zero verbatim occurrences means the surfaces genuinely diverge (rendered
    # glyphs vs extraction text) — only then is fuzzy alignment in play.
    return _fuzzy_locate(text, quote)


def _segment_from_block(block: Any, ir: Any, start: int, end: int) -> dict[str, Any]:
    text = block.text
    start = max(0, min(start, len(text)))
    end = max(start, min(end, len(text)))
    quote = text[start:end]
    prefix = text[max(0, start - _context_chars) : start]
    suffix = text[end : end + _context_chars]
    geometry = None
    if block.page is not None and block.bbox:
        geometry = {"page": block.page, "bbox": list(block.bbox)}
    return {
        "span_id": block.span_id,
        "block_content_hash": block.content_hash,
        "codepoint_start": start,
        "codepoint_end": end,
        "exact_quote": quote,
        "prefix": prefix,
        "suffix": suffix,
        "geometry": geometry,
        "section_path": list(block.section_path),
        "neighbor_hashes": _neighbor_hashes(ir, block.span_id),
        "selection_text_hash": _hash(quote),
    }


def translate_selection(
    repository: Repository,
    *,
    extraction_id: str,
    raw_selection: Mapping[str, Any],
    render_view_id: str | None = None,
) -> dict[str, Any]:
    """Translate a raw display-coordinate selection through the crosswalk into
    ordered source-block anchor segments. Returns ``{"status", "segments",
    "confidence", "raw_selection"}``. ``status`` is ``exact`` or ``needs_reanchor``;
    on ``needs_reanchor`` the raw selection is preserved and learner text is never
    discarded (§3.2)."""

    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        return {"status": "needs_reanchor", "segments": [], "confidence": 0.0, "raw_selection": dict(raw_selection)}

    crosswalk: dict[str, dict[str, Any]] = {}
    if render_view_id is not None:
        crosswalk = {n["display_node_id"]: n for n in repository.render_crosswalk(render_view_id)}

    nodes = list(raw_selection.get("nodes", []))
    if not nodes:
        return {"status": "needs_reanchor", "segments": [], "confidence": 0.0, "raw_selection": dict(raw_selection)}

    segments: list[dict[str, Any]] = []
    status = "exact"
    for raw_node in nodes:
        # The raw selection dict rides the wire opaquely, so accept camelCase and
        # snake_case keys from the TS display-coordinate capture (design §A.2).
        node = {
            "span_id": raw_node.get("span_id", raw_node.get("spanId")),
            "display_node_id": raw_node.get("display_node_id", raw_node.get("displayNodeId")),
            "start": raw_node.get("start"),
            "end": raw_node.get("end"),
            "quote": raw_node.get("quote"),
            # Optional rendered-surface context around the capture (atomic-unit
            # ctrl+click sends it) — used only to disambiguate repeated quotes.
            "prefix": raw_node.get("prefix"),
            "suffix": raw_node.get("suffix"),
        }
        span_id = node.get("span_id")
        if span_id is None:
            cw = crosswalk.get(node.get("display_node_id") or "")
            span_id = cw.get("span_id") if cw else None
        block = ir.block_by_span(span_id) if span_id is not None else None
        if block is None:
            status = "needs_reanchor"
            continue
        start = node.get("start")
        end = node.get("end")
        quote = node.get("quote")
        context = {"prefix": node.get("prefix"), "suffix": node.get("suffix")}
        if start is None or end is None:
            located = _locate_quote(block.text, quote, **context)
            if located is None:
                status = "needs_reanchor"
                continue
            start, end = located
        else:
            start = int(start)
            end = int(end)
            if quote is not None and block.text[max(0, min(start, len(block.text))) : max(0, min(end, len(block.text)))] != quote:
                # display offsets drifted from the quote -> relocate uniquely or fail visibly.
                located = _locate_quote(block.text, quote, **context)
                if located is None:
                    status = "needs_reanchor"
                    continue
                start, end = located
        segments.append(_segment_from_block(block, ir, start, end))

    if status == "needs_reanchor" or not segments:
        return {
            "status": "needs_reanchor",
            "segments": segments,
            "confidence": 0.0,
            "raw_selection": dict(raw_selection),
        }
    return {"status": "exact", "segments": segments, "confidence": 1.0, "raw_selection": dict(raw_selection)}


def _anchor_payload(
    *, source_id: str, revision_id: str, extraction_id: str, render_view_id: str | None,
    translation: Mapping[str, Any], status: str | None = None,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "revision_id": revision_id,
        "extraction_id": extraction_id,
        "render_view_id": render_view_id,
        "status": status or translation["status"],
        "algo_version": ALGO_VERSION,
        "confidence": translation.get("confidence"),
        "raw_selection": translation.get("raw_selection") if (status or translation["status"]) == "needs_reanchor" else None,
        "segments": translation.get("segments", []),
    }


def append_annotation(
    repository: Repository,
    *,
    source_id: str,
    revision_id: str,
    extraction_id: str,
    annotation_type: str,
    learner_text: str = "",
    what_i_think_is_going_on: str | None = None,
    translation: Mapping[str, Any],
    render_view_id: str | None = None,
    privacy_locality: str = "local_private",
    client_idempotency_key: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Create a new annotation (version 1) + its anchor + a ``create`` event."""

    if annotation_type not in ANNOTATION_TYPES:
        raise AnnotationError(f"unknown annotation_type: {annotation_type!r}")
    annotation_id = repository.create_annotation(source_id=source_id, clock=clock)
    version = {
        "annotation_type": annotation_type,
        "learner_text": learner_text,
        "what_i_think_is_going_on": what_i_think_is_going_on,
        "privacy_locality": privacy_locality,
        "authorship": "learner",
        "client_idempotency_key": client_idempotency_key,
    }
    anchor = _anchor_payload(
        source_id=source_id, revision_id=revision_id, extraction_id=extraction_id,
        render_view_id=render_view_id, translation=translation,
    )
    written = repository.append_annotation_version(
        annotation_id=annotation_id, version=version, anchor=anchor,
        event_type="create", event_payload={"annotation_type": annotation_type},
        clock=clock,
    )
    return {"annotation_id": annotation_id, "status": anchor["status"], **written}


def edit_annotation(
    repository: Repository,
    *,
    annotation_id: str,
    learner_text: str | None = None,
    what_i_think_is_going_on: str | None = None,
    annotation_type: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Append an edited version, carrying the existing anchor forward unchanged."""

    head = repository.annotation_head(annotation_id)
    if head is None or head["version"] is None:
        raise AnnotationError(f"unknown annotation: {annotation_id!r}")
    prev = head["version"]
    prev_anchor = head["anchor"] or {}
    version = {
        "annotation_type": annotation_type or prev["annotation_type"],
        "learner_text": learner_text if learner_text is not None else prev["learner_text"],
        "what_i_think_is_going_on": (
            what_i_think_is_going_on if what_i_think_is_going_on is not None else prev.get("what_i_think_is_going_on")
        ),
        "privacy_locality": prev.get("privacy_locality", "local_private"),
        "authorship": "learner",
    }
    anchor = {
        "source_id": prev_anchor.get("source_id", ""),
        "revision_id": prev_anchor.get("revision_id", ""),
        "extraction_id": prev_anchor.get("extraction_id", ""),
        "render_view_id": prev_anchor.get("render_view_id"),
        "status": prev_anchor.get("status", "exact"),
        "algo_version": ALGO_VERSION,
        "confidence": prev_anchor.get("confidence"),
        "segments": [
            {
                "span_id": s["span_id"],
                "block_content_hash": s["block_content_hash"],
                "codepoint_start": s["codepoint_start"],
                "codepoint_end": s["codepoint_end"],
                "exact_quote": s["exact_quote"],
                "prefix": s["prefix"],
                "suffix": s["suffix"],
                # Carry the resolved anchor geometry/section/neighbors forward
                # unchanged (a text-only edit never moves the anchor).
                "geometry": json.loads(s["geometry_json"]) if s.get("geometry_json") else None,
                "section_path": json.loads(s["section_path_json"] or "[]"),
                "neighbor_hashes": json.loads(s["neighbor_hashes_json"] or "[]"),
                "selection_text_hash": s["selection_text_hash"],
            }
            for s in head["segments"]
        ],
    }
    written = repository.append_annotation_version(
        annotation_id=annotation_id, version=version, anchor=anchor,
        event_type="edit", event_payload={"edited": True}, clock=clock,
    )
    return {"annotation_id": annotation_id, **written}


def delete_intent_annotation(
    repository: Repository, *, annotation_id: str, reason: str | None = None, clock: Clock | None = None
) -> str:
    """Deletion is a tombstone disposition event -- never a hard delete (§4.1)."""

    return repository.append_annotation_event(
        annotation_id=annotation_id, event_type="delete_intent",
        payload={"reason": reason}, clock=clock,
    )


def reanchor_annotation(
    repository: Repository,
    *,
    annotation_id: str,
    new_extraction_id: str,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Re-anchor an annotation's segments onto a new extraction. Reuses the
    deterministic block reanchor, then a sub-block quote match; a candidate below
    ``SUBBLOCK_CONFIDENCE_MIN`` is never auto-accepted (-> needs_reanchor). Appends a
    successor anchor and preserves the old anchor + learner content untouched."""

    head = repository.annotation_head(annotation_id)
    if head is None or head["anchor"] is None:
        raise AnnotationError(f"unknown/anchorless annotation: {annotation_id!r}")
    prev_anchor = head["anchor"]
    from_extraction_id = prev_anchor["extraction_id"]
    from_ir = repository.load_document_ir(from_extraction_id)
    to_ir = repository.load_document_ir(new_extraction_id)
    if from_ir is None or to_ir is None:
        raise AnnotationError("cannot reanchor: extraction IR missing")

    block_result = reanchor_spans(from_ir, to_ir)
    run = repository.get_extraction_run(new_extraction_id) or {}
    revision_id = run.get("revision_id", prev_anchor["revision_id"])
    source_id = prev_anchor["source_id"]

    segments: list[dict[str, Any]] = []
    statuses: list[str] = []
    confidences: list[float] = []
    for seg in head["segments"]:
        candidate = reanchor_subblock(
            from_ir, to_ir, from_span_id=seg["span_id"], quote=seg["exact_quote"],
            prefix=seg.get("prefix", ""), suffix=seg.get("suffix", ""), block_result=block_result,
        )
        seg_status = candidate.status
        if seg_status == "reanchored" and candidate.confidence < SUBBLOCK_CONFIDENCE_MIN:
            seg_status = "needs_reanchor"
        statuses.append(seg_status)
        confidences.append(candidate.confidence)
        to_block = to_ir.block_by_span(candidate.to_span_id) if candidate.to_span_id else None
        segments.append(
            {
                "span_id": candidate.to_span_id or seg["span_id"],
                "block_content_hash": candidate.block_content_hash or seg["block_content_hash"],
                "codepoint_start": candidate.codepoint_start,
                "codepoint_end": candidate.codepoint_end,
                "exact_quote": candidate.quote,
                "prefix": seg.get("prefix", ""),
                "suffix": seg.get("suffix", ""),
                "geometry": None,
                "section_path": list(to_block.section_path) if to_block else [],
                "neighbor_hashes": _neighbor_hashes(to_ir, candidate.to_span_id) if candidate.to_span_id else [],
                "selection_text_hash": seg["selection_text_hash"],
            }
        )

    overall = "needs_reanchor" if ("needs_reanchor" in statuses or not statuses) else "reanchored"
    if overall == "reanchored" and all(s == "exact" for s in statuses):
        overall = "reanchored"  # cross-extraction is at best `reanchored`, never `exact`
    version = head["version"] or {"annotation_type": "highlight", "learner_text": ""}
    anchor = {
        "source_id": source_id,
        "revision_id": revision_id,
        "extraction_id": new_extraction_id,
        "render_view_id": None,
        "status": overall,
        "algo_version": ALGO_VERSION,
        "confidence": min(confidences) if confidences else 0.0,
        "raw_selection": {"prior_extraction_id": from_extraction_id} if overall == "needs_reanchor" else None,
        "segments": segments,
    }
    carry_version = {
        "annotation_type": version["annotation_type"],
        "learner_text": version.get("learner_text", ""),
        "what_i_think_is_going_on": version.get("what_i_think_is_going_on"),
        "privacy_locality": version.get("privacy_locality", "local_private"),
        "authorship": "learner",
    }
    written = repository.append_annotation_version(
        annotation_id=annotation_id, version=carry_version, anchor=anchor,
        event_type="reanchor",
        event_payload={"from_extraction_id": from_extraction_id, "to_extraction_id": new_extraction_id, "status": overall},
        clock=clock,
    )
    return {"annotation_id": annotation_id, "status": overall, "segment_statuses": statuses, **written}


def reanchor_annotations_for_source(
    repository: Repository,
    *,
    source_id: str,
    new_extraction_id: str,
    review_batch: int = MANUAL_REVIEW_BATCH,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Re-anchor every annotation on a source onto a new extraction, honoring the
    review-volume budget (§A.3.5). The re-extraction always proceeds; the budget is
    only a SURFACE CAP on the review queue: at most ``review_batch`` needs_reanchor
    annotations are surfaced (``surfaced_for_review``), and ``parked_for_review`` is
    flagged when more than that many landed in ``needs_reanchor`` (so the overflow is
    reviewable, never silently orphaned). Nothing blocks or parks the re-extraction."""

    heads = repository.annotations_for_source(source_id)
    results: list[dict[str, Any]] = []
    for head in heads:
        if head is None or head.get("anchor") is None:
            continue
        results.append(reanchor_annotation(
            repository, annotation_id=head["annotation"]["id"], new_extraction_id=new_extraction_id, clock=clock,
        ))
    needs = [r for r in results if r["status"] == "needs_reanchor"]
    parked = len(needs) > review_batch
    return {
        "reanchored": len([r for r in results if r["status"] == "reanchored"]),
        "needs_reanchor": len(needs),
        "surfaced_for_review": needs[:review_batch],
        "parked_for_review": parked,
        "review_batch": review_batch,
    }


def manual_anchor(
    repository: Repository,
    *,
    annotation_id: str,
    source_id: str,
    revision_id: str,
    extraction_id: str,
    segments: list[Mapping[str, Any]],
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Append a learner-supplied manual anchor successor (§4.4 step 6). Preserves
    every prior anchor version."""

    head = repository.annotation_head(annotation_id)
    if head is None or head["version"] is None:
        raise AnnotationError(f"unknown annotation: {annotation_id!r}")
    version = head["version"]
    anchor = {
        "source_id": source_id,
        "revision_id": revision_id,
        "extraction_id": extraction_id,
        "render_view_id": None,
        "status": "manually_anchored",
        "algo_version": ALGO_VERSION,
        "confidence": 1.0,
        "segments": [dict(s) for s in segments],
    }
    carry_version = {
        "annotation_type": version["annotation_type"],
        "learner_text": version.get("learner_text", ""),
        "what_i_think_is_going_on": version.get("what_i_think_is_going_on"),
        "privacy_locality": version.get("privacy_locality", "local_private"),
        "authorship": "learner",
    }
    written = repository.append_annotation_version(
        annotation_id=annotation_id, version=carry_version, anchor=anchor,
        event_type="manual_anchor", event_payload={"manual": True}, clock=clock,
    )
    return {"annotation_id": annotation_id, "status": "manually_anchored", **written}

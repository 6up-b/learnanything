"""Unit selection persistence with re-anchoring (spec_source_ingestion_v2 §5.3).

The learner chooses which units of an extraction feed synthesis, and may override
unit boundaries (merge adjacent units / split a unit at a heading). Selections and
overrides are stored per (artifact, revision, extraction) and MUST survive a
re-extraction: on a new ExtractionRun the old selection is re-anchored onto the new
units deterministically via M1's re-anchor machinery (semantic-hash / unit-id
match, span-alias fallback). Anything that cannot be re-anchored is **flagged for
review — never silently dropped** (§5.3, §14 selection-survival row).

Pure/deterministic: no fetch, no extraction, no LLM.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentIR
from learnloop.ingest.reanchor import reanchor_spans
from learnloop.services.role_authority import KNOWN_ROLES

# Boundary-override operations a user can layer over the ExtractionRun (§5.3).
MERGE_WITH_NEXT = "merge_with_next"
SPLIT_AT_HEADING = "split_at_heading"
_OVERRIDE_OPS = {MERGE_WITH_NEXT, SPLIT_AT_HEADING}


class SelectionValidationError(ValueError):
    """A selection or boundary override references units/spans that don't exist."""


@dataclass
class ReanchoredSelection:
    selected_unit_ids: list[str] = field(default_factory=list)
    boundary_overrides: list[dict] = field(default_factory=list)
    needs_review: list[str] = field(default_factory=list)


def _override_unit_id(override: dict) -> str | None:
    return override.get("unit_id") if override.get("unit_id") is not None else override.get("unitId")


def _override_at_span(override: dict) -> str | None:
    return override.get("at_span_id") if override.get("at_span_id") is not None else override.get("atSpanId")


def normalize_overrides(boundary_overrides: list[dict] | None) -> list[dict]:
    """Normalize free-form override dicts to canonical snake_case keys.

    The overrides arrive as free-form JSON from the frontend (camelCase) or CLI
    (snake_case); we store one canonical shape so downstream code and re-anchoring
    read a single key set."""

    normalized: list[dict] = []
    for override in boundary_overrides or []:
        entry = {"op": override.get("op"), "unit_id": _override_unit_id(override)}
        at_span = _override_at_span(override)
        if at_span is not None:
            entry["at_span_id"] = at_span
        normalized.append(entry)
    return normalized


def _override_op_by_unit(boundary_overrides: list[dict] | None) -> dict[str, str]:
    """Map unit_id → op for the recognized boundary-override operations."""

    ops: dict[str, str] = {}
    for override in normalize_overrides(boundary_overrides):
        op = override.get("op")
        unit_id = override.get("unit_id")
        if unit_id is not None and op in _OVERRIDE_OPS:
            ops[unit_id] = op
    return ops


def _approx_tokens(blocks: list) -> int:
    return sum(len(block.text) // 4 for block in blocks)


def compute_effective_units(ir: DocumentIR, boundary_overrides: list[dict] | None) -> list[dict]:
    """Deterministically compute the *effective* unit shape after boundary overrides.

    Walks ``ir.units`` in ``ordinal`` order and applies each unit's override:

    - ``merge_with_next`` fuses a unit with the unit that follows it; chains fold
      (A merge + B merge + C → one effective unit A+B+C), and the effective label
      joins the source labels with ``" + "``.
    - ``split_at_heading`` partitions the unit's blocks (resolved via ``span_ids``,
      ordered by block ``ordinal``) by their level-2 heading (second ``section_path``
      segment). Blocks with no second segment form a leading ``"(intro)"`` part.
      Each part is labeled ``"{unit.label} › {sub-slug}"``. A unit with no level-2
      headings is a no-op: it passes through unchanged with ``"split_noop": True``.
    - A unit with no override passes through unchanged.

    Pure and side-effect free; the same inputs always yield the same output.
    """

    ops = _override_op_by_unit(boundary_overrides)
    units = sorted(ir.units, key=lambda u: u.ordinal)
    blocks_by_span = {block.span_id: block for block in ir.blocks}

    def unit_blocks(unit) -> list:
        resolved = [blocks_by_span[span_id] for span_id in unit.span_ids if span_id in blocks_by_span]
        return sorted(resolved, key=lambda b: b.ordinal)

    effective: list[dict] = []
    index = 0
    while index < len(units):
        unit = units[index]
        op = ops.get(unit.unit_id)

        if op == MERGE_WITH_NEXT:
            # Fold this unit with the following unit(s), chaining while each merged
            # unit (except the last in the chain) also carries merge_with_next.
            chain = [unit]
            cursor = index
            while ops.get(units[cursor].unit_id) == MERGE_WITH_NEXT and cursor + 1 < len(units):
                cursor += 1
                chain.append(units[cursor])
            collected: list = []
            for member in chain:
                collected.extend(unit_blocks(member))
            collected = sorted(collected, key=lambda b: b.ordinal)
            label = " + ".join(member.label for member in chain)
            if len(chain) == 1:
                # merge_with_next on the last unit has no following unit to fuse.
                effective.append(
                    {
                        "effective_id": unit.unit_id,
                        "label": unit.label,
                        "source_unit_ids": [unit.unit_id],
                        "block_count": len(collected),
                        "approx_tokens": _approx_tokens(collected),
                        "kind": "unchanged",
                    }
                )
            else:
                effective.append(
                    {
                        "effective_id": "+".join(member.unit_id for member in chain),
                        "label": label,
                        "source_unit_ids": [member.unit_id for member in chain],
                        "block_count": len(collected),
                        "approx_tokens": _approx_tokens(collected),
                        "kind": "merged",
                    }
                )
            index = cursor + 1
            continue

        if op == SPLIT_AT_HEADING:
            blocks = unit_blocks(unit)
            # Partition by the level-2 heading slug (second section_path segment),
            # preserving first-seen order; blocks lacking one form an "(intro)" part.
            order: list[str | None] = []
            parts: dict[str | None, list] = {}
            for block in blocks:
                sub = block.section_path[1] if len(block.section_path) >= 2 else None
                if sub not in parts:
                    parts[sub] = []
                    order.append(sub)
                parts[sub].append(block)
            real_headings = [sub for sub in order if sub is not None]
            if not real_headings:
                # No level-2 headings — splitting does nothing.
                effective.append(
                    {
                        "effective_id": unit.unit_id,
                        "label": unit.label,
                        "source_unit_ids": [unit.unit_id],
                        "block_count": len(blocks),
                        "approx_tokens": _approx_tokens(blocks),
                        "kind": "split",
                        "split_noop": True,
                    }
                )
            else:
                for sub in order:
                    part_blocks = parts[sub]
                    slug = sub if sub is not None else "(intro)"
                    effective.append(
                        {
                            "effective_id": f"{unit.unit_id}#{slug}",
                            "label": f"{unit.label} › {slug}",
                            "source_unit_ids": [unit.unit_id],
                            "block_count": len(part_blocks),
                            "approx_tokens": _approx_tokens(part_blocks),
                            "kind": "split",
                        }
                    )
            index += 1
            continue

        # No override — pass through unchanged.
        blocks = unit_blocks(unit)
        effective.append(
            {
                "effective_id": unit.unit_id,
                "label": unit.label,
                "source_unit_ids": [unit.unit_id],
                "block_count": len(blocks),
                "approx_tokens": _approx_tokens(blocks),
                "kind": "unchanged",
            }
        )
        index += 1

    return effective


def validate_unit_selection(
    ir: DocumentIR,
    selected_unit_ids: list[str],
    boundary_overrides: list[dict] | None = None,
) -> None:
    """App-level validation of a selection against its extraction's IR."""

    unit_ids = {unit.unit_id for unit in ir.units}
    span_ids = {block.span_id for block in ir.blocks}
    seen: set[str] = set()
    for unit_id in selected_unit_ids:
        if unit_id not in unit_ids:
            raise SelectionValidationError(f"unit '{unit_id}' is not in extraction units.")
        if unit_id in seen:
            raise SelectionValidationError(f"unit '{unit_id}' selected more than once.")
        seen.add(unit_id)
    for override in normalize_overrides(boundary_overrides):
        op = override.get("op")
        if op not in _OVERRIDE_OPS:
            raise SelectionValidationError(f"unknown boundary-override op '{op}'.")
        target = override.get("unit_id")
        if target not in unit_ids:
            raise SelectionValidationError(f"boundary override targets missing unit '{target}'.")
        at_span = override.get("at_span_id")
        if op == SPLIT_AT_HEADING and at_span is not None and at_span not in span_ids:
            raise SelectionValidationError(f"split references missing span '{at_span}'.")


# Exam per-unit use modes chosen at selection (spec_source_ingestion_v2 §4.2).
EXAM_USE_MODES = frozenset({"held_out_evaluation", "available_for_practice", "blueprint_only"})
# Default: a configurable held-out fraction, remainder blueprint_only (§4.2).
DEFAULT_EXAM_USE_MODE = "blueprint_only"
DEFAULT_HELD_OUT_FRACTION = 0.3


def default_exam_use_modes(unit_ids: list[str], *, held_out_fraction: float = DEFAULT_HELD_OUT_FRACTION) -> dict[str, str]:
    """Deterministic default: the first ``held_out_fraction`` of units (by sorted
    id) are held-out evaluation, the rest blueprint_only (§4.2)."""

    ordered = sorted(unit_ids)
    held_out_count = int(len(ordered) * max(0.0, min(1.0, held_out_fraction)))
    held_out = set(ordered[:held_out_count])
    return {unit_id: ("held_out_evaluation" if unit_id in held_out else DEFAULT_EXAM_USE_MODE) for unit_id in ordered}


def save_unit_selection(
    repo: Repository,
    extraction_id: str,
    selected_unit_ids: list[str],
    *,
    boundary_overrides: list[dict] | None = None,
    exam_use_modes: dict[str, str] | None = None,
    exam_paper_metadata: dict | None = None,
    role_override: str | None = None,
    clock: Clock | None = None,
) -> dict:
    """Validate and persist a selection for one extraction run.

    ``exam_use_modes`` maps unit_id → use mode (§4.2); ``exam_paper_metadata``
    carries administration year/syllabus/weighting for the paper. Both are chosen
    at selection so downstream exam-profile aggregation and leakage policy read
    them without a second decision point.

    ``role_override`` records the role the learner picked in the outline flow.
    Authority still lives on source-set membership (§4.2) — this is a UI-round-trip
    hint for the import-batch path, which has no collection yet. Must be a known
    role (role_authority.KNOWN_ROLES) when set; ``None`` means "no override"."""

    ir = repo.load_document_ir(extraction_id)
    if ir is None:
        raise SelectionValidationError(f"extraction '{extraction_id}' has no persisted IR.")
    validate_unit_selection(ir, selected_unit_ids, boundary_overrides)
    for unit_id, mode in (exam_use_modes or {}).items():
        if mode not in EXAM_USE_MODES:
            raise SelectionValidationError(f"unknown exam use mode '{mode}' for unit '{unit_id}'.")
    normalized_role = (role_override or "").strip() or None
    if normalized_role is not None and normalized_role not in KNOWN_ROLES:
        raise SelectionValidationError(f"unknown source role '{normalized_role}'.")
    run = repo.get_extraction_run(extraction_id)
    revision_id = run["revision_id"] if run else None
    revision = repo.get_source_revision(revision_id) if revision_id else None
    source_id = revision["source_id"] if revision else None
    repo.upsert_unit_selection(
        extraction_id=extraction_id,
        source_id=source_id,
        revision_id=revision_id,
        selected_unit_ids=list(selected_unit_ids),
        boundary_overrides=normalize_overrides(boundary_overrides),
        needs_review=[],
        exam_use_modes=dict(exam_use_modes or {}),
        exam_paper_metadata=dict(exam_paper_metadata or {}),
        role_override=normalized_role,
        clock=clock,
    )
    return repo.get_unit_selection(extraction_id) or {}


def reanchor_units(from_ir: DocumentIR, to_ir: DocumentIR) -> dict[str, str | None]:
    """Map each old unit id onto a new unit id (or ``None`` when unresolved).

    Resolution order (§5.3): exact unit-id + semantic-hash match, then a unique
    semantic-hash match, then M1 span-alias majority. A tie stays unresolved."""

    to_by_id = {unit.unit_id: unit for unit in to_ir.units}
    to_by_hash: dict[str, list] = {}
    for unit in to_ir.units:
        to_by_hash.setdefault(unit.semantic_hash, []).append(unit)
    span_result = reanchor_spans(from_ir, to_ir)
    to_unit_of_span: dict[str, str] = {}
    for unit in to_ir.units:
        for span_id in unit.span_ids:
            to_unit_of_span[span_id] = unit.unit_id

    resolved: dict[str, str | None] = {}
    for unit in from_ir.units:
        same_id = to_by_id.get(unit.unit_id)
        if same_id is not None and same_id.semantic_hash == unit.semantic_hash:
            resolved[unit.unit_id] = same_id.unit_id
            continue
        by_hash = to_by_hash.get(unit.semantic_hash, [])
        if len(by_hash) == 1:
            resolved[unit.unit_id] = by_hash[0].unit_id
            continue
        if len(by_hash) > 1:
            disambiguated = [c for c in by_hash if c.unit_id == unit.unit_id]
            resolved[unit.unit_id] = disambiguated[0].unit_id if len(disambiguated) == 1 else None
            continue
        resolved[unit.unit_id] = _span_majority_unit(unit, span_result, to_unit_of_span)
    return resolved


def _span_majority_unit(unit, span_result, to_unit_of_span) -> str | None:
    mapped: list[str] = []
    for span_id in unit.span_ids:
        alias = span_result.alias_for(span_id)
        if alias is not None:
            new_unit = to_unit_of_span.get(alias.to_span_id)
            if new_unit is not None:
                mapped.append(new_unit)
    if not mapped:
        return None
    counts = Counter(mapped)
    top_unit, top_n = counts.most_common(1)[0]
    ties = list(counts.values()).count(top_n)
    if ties == 1 and top_n * 2 > len(unit.span_ids):
        return top_unit
    return None


def reanchor_selection(
    from_ir: DocumentIR,
    to_ir: DocumentIR,
    selected_unit_ids: list[str],
    boundary_overrides: list[dict] | None = None,
) -> ReanchoredSelection:
    """Re-anchor a stored selection + overrides onto a fresh extraction (§5.3)."""

    unit_map = reanchor_units(from_ir, to_ir)
    result = ReanchoredSelection()
    for unit_id in selected_unit_ids:
        new_id = unit_map.get(unit_id)
        if new_id is not None:
            if new_id not in result.selected_unit_ids:
                result.selected_unit_ids.append(new_id)
        else:
            result.needs_review.append(unit_id)
    for override in boundary_overrides or []:
        remapped = dict(override)
        target = override.get("unit_id")
        new_target = unit_map.get(target)
        if new_target is None:
            result.needs_review.append(str(target))
            continue
        remapped["unit_id"] = new_target
        result.boundary_overrides.append(remapped)
    return result


def reanchor_selection_to(
    repo: Repository,
    from_extraction_id: str,
    to_extraction_id: str,
    *,
    clock: Clock | None = None,
) -> dict:
    """Re-anchor the stored selection of ``from`` onto ``to`` and persist it.

    Returns the new selection row (with any ``needs_review`` unit ids)."""

    stored = repo.get_unit_selection(from_extraction_id)
    if stored is None:
        raise SelectionValidationError(f"extraction '{from_extraction_id}' has no stored selection.")
    from_ir = repo.load_document_ir(from_extraction_id)
    to_ir = repo.load_document_ir(to_extraction_id)
    if from_ir is None or to_ir is None:
        raise SelectionValidationError("both extractions must have persisted IR to re-anchor.")
    reanchored = reanchor_selection(
        from_ir,
        to_ir,
        stored.get("selected_unit_ids") or [],
        stored.get("boundary_overrides") or [],
    )
    run = repo.get_extraction_run(to_extraction_id)
    revision_id = run["revision_id"] if run else None
    revision = repo.get_source_revision(revision_id) if revision_id else None
    source_id = revision["source_id"] if revision else None
    # Carry exam use modes/metadata forward, re-anchoring per-unit modes onto the
    # new unit ids (dropping modes for units that failed to re-anchor).
    old_modes = stored.get("exam_use_modes") or {}
    from_ir_units = {unit.unit_id for unit in from_ir.units}
    reanchor_map = reanchor_units(from_ir, to_ir)
    new_modes = {
        reanchor_map[old_id]: mode
        for old_id, mode in old_modes.items()
        if old_id in from_ir_units and reanchor_map.get(old_id) is not None
    }
    repo.upsert_unit_selection(
        extraction_id=to_extraction_id,
        source_id=source_id,
        revision_id=revision_id,
        selected_unit_ids=reanchored.selected_unit_ids,
        boundary_overrides=reanchored.boundary_overrides,
        needs_review=reanchored.needs_review,
        exam_use_modes=new_modes,
        exam_paper_metadata=stored.get("exam_paper_metadata") or {},
        role_override=stored.get("role_override"),
        clock=clock,
    )
    return repo.get_unit_selection(to_extraction_id) or {}

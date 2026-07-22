"""Role-specific unit inventories (spec_source_ingestion_v2 §7, ING M4).

This is the token-economics linchpin of the source layer. The cacheable unit is
the DocumentUnit; an inventory is produced once and reused — at ZERO new tokens —
across every collection/revision that presents the same normalized unit view
under the same profile/schema/prompt/provider/model (the §7 UNIQUE key). A
`combined` inventory may satisfy a narrower request only when its schema version
guarantees the required fields (`profile_satisfies`, the one deterministic
decider).

Pipeline for one uncached unit:

1. `build_inventory_windows` — the deterministic M3-style inventory view over the
   unit (section heading once; prose blocks with short span ids; equations; table
   captions/headers; figure captions + nearby text; boilerplate omitted), split
   on block/section boundaries when the unit exceeds `[ingest.budgets].
   inventory_input_tokens`.
2. one `run_source_unit_inventory` codex call per window (getattr-discovered so
   providers degrade), delimiting the untrusted source text.
3. `assign_deterministic_ids` — service-owned ids from
   (unit_id, window_ordinal, item_ordinal, normalized-content-hash).
4. `merge_windows` — deterministic concatenation + dedup by assigned id, NOT
   fuzzy merging (cross-window equivalence is synthesis work).
5. `validate_inventory` — reject any assertion that cites an unknown span id or
   cites no span at all; the model never invents a locator.

Inventory rows are CANDIDATES: nothing here writes curriculum or learner state,
and an exam occurrence never becomes a canonical claim.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from learnloop.clock import Clock
from learnloop.codex.prompts import SOURCE_UNIT_INVENTORY_PROMPT_VERSION
from learnloop.codex.schemas import SourceUnitInventory
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.ingest.hashing import normalize_semantic_text
from learnloop.ingest.ir import DocumentIR
from learnloop.services.role_authority import default_inventory_profile

# Bump when the inventory JSON shape changes (part of cache identity, §7).
INVENTORY_SCHEMA_VERSION = 1

INVENTORY_PROFILES: frozenset[str] = frozenset({"semantic", "practice", "assessment", "combined"})

# Block types/role hints that are boilerplate and omitted from the inventory view
# (§3: repeated headers/footers/boilerplate omitted; bibliography/index low-priority).
_OMIT_BLOCK_TYPES: frozenset[str] = frozenset({"page_header", "page_footer", "page_number"})
_OMIT_ROLE_HINTS: frozenset[str] = frozenset({"header", "footer", "boilerplate", "page_number"})

_CHARS_PER_TOKEN = 4

# Which profiles a `combined` inventory at a given schema version guarantees it
# can satisfy (§7). The ONE deterministic decider — keyed by schema version so a
# future combined shape that drops a section cannot silently satisfy it.
_COMBINED_SATISFIES: dict[int, frozenset[str]] = {
    1: frozenset({"semantic", "practice", "assessment", "combined"}),
}


class InventoryError(ValueError):
    """A unit/extraction reference or inventory profile is invalid."""


class InventoryValidationError(ValueError):
    """A returned inventory cites an unknown span id or an uncited assertion."""


def normalize_profile(profile: str | None) -> str:
    normalized = (profile or "").strip() or "combined"
    if normalized not in INVENTORY_PROFILES:
        raise InventoryError(
            f"inventory_profile '{normalized}' is not one of {sorted(INVENTORY_PROFILES)}."
        )
    return normalized


def profile_satisfies(
    stored_profile: str,
    stored_schema_version: int,
    requested_profile: str,
) -> bool:
    """Does a cached inventory satisfy a request? (§7 combined-narrower rule).

    Exact-profile match always satisfies. Otherwise a `combined` inventory
    satisfies a narrower request ONLY when its schema version guarantees the
    requested profile's fields — the single deterministic decision."""

    if stored_profile == requested_profile:
        return True
    if stored_profile == "combined":
        return requested_profile in _COMBINED_SATISFIES.get(stored_schema_version, frozenset())
    return False


def _approx_tokens(text: str) -> int:
    if not text:
        return 0
    return (len(text) + _CHARS_PER_TOKEN - 1) // _CHARS_PER_TOKEN


def _view_block(block) -> dict[str, Any] | None:
    """One inventory-view block, or None when it is omitted boilerplate (§3)."""

    if block.block_type in _OMIT_BLOCK_TYPES:
        return None
    if block.role_hint in _OMIT_ROLE_HINTS:
        return None
    text = (block.text or "").strip()
    if not text:
        return None
    kind = block.role_hint or block.block_type
    return {"span_id": block.span_id, "kind": kind, "text": text}


def _section_key(block) -> tuple[str, ...]:
    return tuple(block.section_path or ())


def build_inventory_windows(
    ir: DocumentIR,
    unit_id: str,
    *,
    input_budget_tokens: int,
) -> list[dict[str, Any]]:
    """Deterministic inventory view for one unit, split into windows (§3, §7).

    Splits on section boundaries first, packing sections into windows up to the
    budget; a single oversize section splits at block boundaries. Section heading
    text appears once per window. Windows are stable for an unchanged unit."""

    unit = next((candidate for candidate in ir.units if candidate.unit_id == unit_id), None)
    if unit is None:
        raise InventoryError(f"unit '{unit_id}' is not in the extraction.")
    by_span = {block.span_id: block for block in ir.blocks}
    blocks = [by_span[span_id] for span_id in unit.span_ids if span_id in by_span]
    view_blocks = [entry for entry in (_view_block(block) for block in blocks) if entry is not None]
    kept_blocks = [block for block, entry in zip(blocks, [_view_block(b) for b in blocks]) if entry is not None]

    budget = max(int(input_budget_tokens), 1000)
    heading = _unit_heading(unit, blocks)

    windows: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_tokens = 0
    last_section: tuple[str, ...] | None = None

    for block, entry in zip(kept_blocks, view_blocks):
        block_tokens = _approx_tokens(entry["text"])
        section = _section_key(block)
        at_boundary = section != last_section
        if current and current_tokens + block_tokens > budget and at_boundary:
            windows.append(current)
            current = []
            current_tokens = 0
        elif current and current_tokens + block_tokens > budget and not at_boundary:
            # An oversize section: split at a hard block boundary to make progress.
            windows.append(current)
            current = []
            current_tokens = 0
        current.append(entry)
        current_tokens += block_tokens
        last_section = section
    if current:
        windows.append(current)
    if not windows:
        windows = [[]]

    total = len(windows)
    return [
        {
            "unit_id": unit.unit_id,
            "semantic_hash": unit.semantic_hash,
            "label": unit.label,
            "section_heading": heading,
            "window_ordinal": ordinal,
            "window_count": total,
            "blocks": window,
        }
        for ordinal, window in enumerate(windows)
    ]


def _unit_heading(unit, blocks) -> str:
    for block in blocks:
        if block.block_type in {"heading", "title", "section_header"} or block.role_hint in {"heading", "title"}:
            text = (block.text or "").strip()
            if text:
                return text
    return unit.label or unit.unit_id


def _content_hash(*parts: Any) -> str:
    joined = "␟".join(_stringify(part) for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:12]


def _stringify(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return "␞".join(_stringify(item) for item in value)
    return str(value)


def _assign_id(unit_id: str, window_ordinal: int, item_ordinal: int, content_hash: str) -> str:
    """Service-owned deterministic id (§7): stable for an unchanged semantic view."""

    return f"{unit_id}|w{window_ordinal}|i{item_ordinal}|{content_hash}"


def assign_deterministic_ids(
    inventory: SourceUnitInventory,
    *,
    unit_id: str,
    window_ordinal: int,
) -> SourceUnitInventory:
    """Reassign every id from (unit_id, window_ordinal, item_ordinal, content-hash)
    and rewrite intra-inventory `*_ids`/`concept_mention_id` references (§7)."""

    data = inventory.model_dump()
    data["unit_id"] = unit_id
    ordinal = 0

    mention_map: dict[str, str] = {}
    for index, mention in enumerate(data.get("concept_mentions", [])):
        old = mention.get("mention_id") or f"__m{index}"
        new_id = _assign_id(unit_id, window_ordinal, ordinal, _content_hash("mention", mention.get("name"), mention.get("span_ids")))
        mention["mention_id"] = new_id
        mention_map[old] = new_id
        ordinal += 1

    def _remap_mentions(ids: list[str]) -> list[str]:
        return [mention_map[old] for old in ids if old in mention_map]

    for index, claim in enumerate(data.get("claims", [])):
        claim["claim_id"] = _assign_id(unit_id, window_ordinal, ordinal, _content_hash("claim", claim.get("statement"), claim.get("span_ids")))
        claim["concept_mention_ids"] = _remap_mentions(claim.get("concept_mention_ids", []))
        ordinal += 1
    for index, proc in enumerate(data.get("procedure_signals", [])):
        proc["procedure_id"] = _assign_id(unit_id, window_ordinal, ordinal, _content_hash("proc", proc.get("contract"), proc.get("observable_step_span_ids")))
        ordinal += 1
    for index, practice in enumerate(data.get("practice_signals", [])):
        practice["signal_id"] = _assign_id(unit_id, window_ordinal, ordinal, _content_hash("practice", practice.get("task_family"), practice.get("span_ids")))
        practice["concept_mention_ids"] = _remap_mentions(practice.get("concept_mention_ids", []))
        ordinal += 1
    for index, assessment in enumerate(data.get("assessment_signals", [])):
        assessment["assessment_item_id"] = _assign_id(unit_id, window_ordinal, ordinal, _content_hash("assess", assessment.get("task_family"), assessment.get("span_ids")))
        ordinal += 1
    for coverage in data.get("coverage_claims", []):
        old = coverage.get("concept_mention_id")
        if old in mention_map:
            coverage["concept_mention_id"] = mention_map[old]
    return SourceUnitInventory.model_validate(data)


# Every id-bearing list and the span-citation fields the validator enforces (§7).
_SPAN_CITING_FIELDS: tuple[tuple[str, str], ...] = (
    ("concept_mentions", "span_ids"),
    ("claims", "span_ids"),
    ("procedure_signals", "observable_step_span_ids"),
    ("practice_signals", "span_ids"),
    ("assessment_signals", "span_ids"),
    ("misconception_signals", "span_ids"),
    ("coverage_claims", "span_ids"),
)


def validate_inventory(inventory: SourceUnitInventory, valid_span_ids: set[str]) -> None:
    """Reject uncited assertions and unknown span ids (§7, §3).

    Every assertion must cite at least one span id, and every cited span id must
    be one the model was given — the model never invents a locator."""

    data = inventory.model_dump()
    for list_name, span_field in _SPAN_CITING_FIELDS:
        for index, item in enumerate(data.get(list_name, [])):
            span_ids = item.get(span_field) or []
            if not span_ids:
                raise InventoryValidationError(
                    f"{list_name}[{index}] cites no span id (every assertion must cite provided spans)."
                )
            unknown = [span for span in span_ids if span not in valid_span_ids]
            if unknown:
                raise InventoryValidationError(
                    f"{list_name}[{index}] cites unknown span id(s) {unknown}; the model may not invent locators."
                )


def merge_windows(inventories: list[SourceUnitInventory]) -> SourceUnitInventory:
    """Deterministic concat + dedup by assigned id (§7). No fuzzy merging."""

    if not inventories:
        return SourceUnitInventory()
    first = inventories[0]
    merged = SourceUnitInventory(
        unit_id=first.unit_id,
        semantic_hash=first.semantic_hash,
        outline_summary=first.outline_summary,
    )
    seen: dict[str, set[str]] = {}

    def _extend(field_name: str, id_field: str | None) -> None:
        target = getattr(merged, field_name)
        seen.setdefault(field_name, set())
        for inventory in inventories:
            for item in getattr(inventory, field_name):
                if id_field is not None:
                    key = getattr(item, id_field, "") or ""
                    if key and key in seen[field_name]:
                        continue
                    if key:
                        seen[field_name].add(key)
                target.append(item)

    _extend("concept_mentions", "mention_id")
    _extend("claims", "claim_id")
    _extend("procedure_signals", "procedure_id")
    _extend("practice_signals", "signal_id")
    _extend("assessment_signals", "assessment_item_id")
    _extend("misconception_signals", None)
    _extend("coverage_claims", None)
    _extend("inventory_warnings", None)
    if len(inventories) > 1:
        merged.outline_summary = " ".join(
            inv.outline_summary for inv in inventories if inv.outline_summary
        ).strip()
    return merged


@dataclass
class InventoryResult:
    inventory: SourceUnitInventory
    inventory_id: str
    profile: str
    cache_hit: bool
    reused_profile: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)


def run_unit_inventory(
    repo: Repository,
    extraction_id: str,
    unit_id: str,
    *,
    role: str,
    profile: str | None = None,
    client: Any = None,
    provider: str | None = None,
    model: str | None = None,
    input_budget_tokens: int = 20000,
    output_budget_tokens: int | None = 3000,
    clock: Clock | None = None,
    prompt_version: str = SOURCE_UNIT_INVENTORY_PROMPT_VERSION,
    schema_version: int = INVENTORY_SCHEMA_VERSION,
) -> InventoryResult:
    """Produce (or reuse) the inventory for one unit under a role/profile (§7).

    Cache hit → zero new tokens. Cache miss → windows, one codex call each,
    deterministic ids, merge, validate, persist under the full UNIQUE key.
    """

    requested_profile = normalize_profile(profile or default_inventory_profile(role))
    run = repo.get_extraction_run(extraction_id)
    if run is None:
        raise InventoryError(f"extraction '{extraction_id}' does not exist.")
    revision_id = run["revision_id"]
    ir = repo.load_document_ir(extraction_id)
    if ir is None:
        raise InventoryError(f"extraction '{extraction_id}' has no persisted IR.")
    unit = next((candidate for candidate in ir.units if candidate.unit_id == unit_id), None)
    if unit is None:
        raise InventoryError(f"unit '{unit_id}' is not in the extraction.")
    provider_name = provider or getattr(client, "provider_type", None) or "codex"
    model_name = model or getattr(client, "model", None) or "unknown"

    # Cache lookup (§3.2 reuse): any row with the same non-profile identity whose
    # stored profile satisfies the request — even across collections/revisions is
    # handled by the semantic-hash index; here we key on this revision's row.
    for candidate in repo.reusable_unit_inventories(
        source_revision_id=revision_id,
        unit_id=unit_id,
        unit_semantic_hash=unit.semantic_hash,
        inventory_schema_version=schema_version,
        prompt_version=prompt_version,
        provider=provider_name,
        model=model_name,
    ):
        if profile_satisfies(candidate["inventory_profile"], candidate["inventory_schema_version"], requested_profile):
            return InventoryResult(
                inventory=SourceUnitInventory.model_validate(candidate["inventory"]),
                inventory_id=candidate["id"],
                profile=requested_profile,
                cache_hit=True,
                reused_profile=candidate["inventory_profile"],
            )

    run_inventory = getattr(client, "run_source_unit_inventory", None)
    if run_inventory is None:
        raise InventoryError(
            "the configured provider has no run_source_unit_inventory; inventory degrades unavailable."
        )

    from learnloop.codex.client import SourceUnitInventoryContext

    windows = build_inventory_windows(ir, unit_id, input_budget_tokens=input_budget_tokens)
    valid_span_ids = {block["span_id"] for window in windows for block in window["blocks"]}
    per_window: list[SourceUnitInventory] = []
    usage: dict[str, Any] = {
        "calls": 0,
        "input_tokens_estimate": sum(
            max(1, len(json.dumps(window, default=str)) // _CHARS_PER_TOKEN)
            for window in windows
        ),
    }
    for window in windows:
        context = SourceUnitInventoryContext(
            unit_id=unit.unit_id,
            semantic_hash=unit.semantic_hash,
            role=role,
            inventory_profile=requested_profile,
            unit_view=window,
        )
        raw = run_inventory(context)
        assigned = assign_deterministic_ids(raw, unit_id=unit.unit_id, window_ordinal=window["window_ordinal"])
        assigned.semantic_hash = unit.semantic_hash
        validate_inventory(assigned, valid_span_ids)
        per_window.append(assigned)
        usage["calls"] += 1

    merged = merge_windows(per_window)
    merged.unit_id = unit.unit_id
    merged.semantic_hash = unit.semantic_hash
    usage["output_tokens_estimate"] = max(
        1, len(merged.model_dump_json()) // _CHARS_PER_TOKEN
    )
    if (
        output_budget_tokens is not None
        and usage["output_tokens_estimate"] > output_budget_tokens
    ):
        raise InventoryValidationError(
            "inventory output exceeded its configured token budget"
        )

    inventory_id = f"inv_{new_ulid()}"
    repo.insert_unit_inventory(
        id=inventory_id,
        source_revision_id=revision_id,
        extraction_id=extraction_id,
        unit_id=unit_id,
        unit_semantic_hash=unit.semantic_hash,
        inventory_profile=requested_profile,
        inventory_schema_version=schema_version,
        prompt_version=prompt_version,
        provider=provider_name,
        model=model_name,
        inventory=merged.model_dump(),
        usage=usage,
        clock=clock,
    )
    return InventoryResult(
        inventory=merged,
        inventory_id=inventory_id,
        profile=requested_profile,
        cache_hit=False,
        usage=usage,
    )


def inventory_marker(repo: Repository, extraction_id: str, unit_id: str) -> dict[str, Any]:
    """Whether a unit already has a cached inventory (wires the M3 outline seam).

    Returns the richest cached profile for the unit's current semantic hash, so
    the outline/build-plan can render the "cached" affordance from real rows."""

    run = repo.get_extraction_run(extraction_id)
    if run is None:
        return {"inventoried": False, "inventory_profile": None}
    rows = repo.unit_inventories_for_extraction(extraction_id)
    profiles = sorted({row["inventory_profile"] for row in rows if row["unit_id"] == unit_id})
    if not profiles:
        return {"inventoried": False, "inventory_profile": None}
    best = "combined" if "combined" in profiles else profiles[0]
    return {"inventoried": True, "inventory_profile": best, "profiles": profiles}

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
from learnloop.ai.transport import StructuredTransport, execute_structured_operation
from learnloop.content.synthesis.ai_contracts import (
    SOURCE_UNIT_INVENTORY_PROMPT_VERSION,
    SourceUnitInventory,
    SourceUnitInventoryContext,
    source_unit_inventory_prompt,
)
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.ingest.hashing import normalize_semantic_text
from learnloop.ingest.ir import DocumentIR
from learnloop.ingest.reanchor import EXACT_HASH, reanchor_spans
from learnloop.content.sources.role_authority import default_inventory_profile

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


def request_source_unit_inventory(
    client: StructuredTransport, context: SourceUnitInventoryContext
) -> SourceUnitInventory:
    """Inventory one source-unit window through the shared transport."""

    return execute_structured_operation(
        client,
        purpose="source_unit_inventory",
        prompt=source_unit_inventory_prompt(context),
        result_model=SourceUnitInventory,
    )


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


def _inventory_members(ir: DocumentIR, unit_ids: list[str]) -> list[Any]:
    """Resolve an ordered effective inventory unit from its source members."""

    by_id = {unit.unit_id: unit for unit in ir.units}
    missing = [unit_id for unit_id in unit_ids if unit_id not in by_id]
    if missing:
        raise InventoryError(
            "inventory unit member(s) are not in the extraction: "
            + ", ".join(missing)
        )
    if len(set(unit_ids)) != len(unit_ids):
        raise InventoryError("an effective inventory unit cannot repeat a source unit")
    return [by_id[unit_id] for unit_id in unit_ids]


def _effective_unit_id(unit_ids: list[str]) -> str:
    return "+".join(unit_ids)


def _effective_semantic_hash(members: list[Any]) -> str:
    if len(members) == 1:
        return str(members[0].semantic_hash)
    payload = json.dumps(
        {
            "kind": "merged_inventory_unit_v1",
            "member_semantic_hashes": [str(member.semantic_hash) for member in members],
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_inventory_windows(
    ir: DocumentIR,
    unit_id: str,
    *,
    unit_ids: list[str] | None = None,
    input_budget_tokens: int,
) -> list[dict[str, Any]]:
    """Deterministic inventory view for one effective unit, split into windows.

    Splits on section boundaries first, packing sections into windows up to the
    budget; a single oversize section splits at block boundaries. Section heading
    text appears once per window.  ``unit_ids`` is the ordered source membership
    of an explicit ``merge_with_next`` group; its composite id and semantic hash
    remain stable while every member remains semantically unchanged.
    """

    source_unit_ids = list(unit_ids or [unit_id])
    members = _inventory_members(ir, source_unit_ids)
    effective_id = _effective_unit_id(source_unit_ids)
    if len(source_unit_ids) == 1 and unit_id != effective_id:
        raise InventoryError(
            f"unit '{unit_id}' does not match source member '{effective_id}'"
        )
    by_span = {block.span_id: block for block in ir.blocks}
    blocks = []
    seen_spans: set[str] = set()
    for member in members:
        for span_id in member.span_ids:
            if span_id in by_span and span_id not in seen_spans:
                blocks.append(by_span[span_id])
                seen_spans.add(span_id)
    kept_blocks = []
    view_blocks = []
    for block in blocks:
        entry = _view_block(block)
        if entry is not None:
            kept_blocks.append(block)
            view_blocks.append(entry)

    budget = max(int(input_budget_tokens), 1000)
    heading = " + ".join(member.label for member in members)
    semantic_hash = _effective_semantic_hash(members)

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
            "unit_id": effective_id,
            "semantic_hash": semantic_hash,
            "label": heading,
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
            span_ids = item.get(span_field) or item.get("span_ids") or []
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


def _cited_span_ids(inventory: SourceUnitInventory) -> set[str]:
    data = inventory.model_dump()
    cited: set[str] = set()
    for list_name, span_field in _SPAN_CITING_FIELDS:
        for item in data.get(list_name, []):
            cited.update(str(span) for span in (item.get(span_field) or []))
    return cited


def _rebind_inventory_spans(
    inventory: SourceUnitInventory,
    *,
    span_aliases: Mapping[str, str],
    unit_id: str,
    semantic_hash: str,
) -> SourceUnitInventory:
    """Return the same semantic artifact bound to a new extraction's span ids."""

    data = inventory.model_dump()
    data["unit_id"] = unit_id
    data["semantic_hash"] = semantic_hash
    for list_name, span_field in _SPAN_CITING_FIELDS:
        for item in data.get(list_name, []):
            item[span_field] = [
                span_aliases[str(span)] for span in (item.get(span_field) or [])
            ]
    return SourceUnitInventory.model_validate(data)


def _reusable_inventory_for_extraction(
    repo: Repository,
    candidate: Mapping[str, Any],
    *,
    current_ir: DocumentIR,
    current_extraction_id: str,
    current_unit_id: str,
    current_semantic_hash: str,
    valid_span_ids: set[str],
) -> SourceUnitInventory | None:
    """Safely bind a cached semantic artifact to the current extraction.

    A direct row is accepted after the same citation validation used for fresh
    output.  A row from another extraction/revision must re-anchor every cited
    span by an exact content-hash match; fuzzy/ambiguous aliases deliberately turn
    the lookup into a miss.
    """

    cached = SourceUnitInventory.model_validate(candidate["inventory"])
    if str(candidate.get("extraction_id") or "") == current_extraction_id:
        try:
            validate_inventory(cached, valid_span_ids)
        except InventoryValidationError:
            return None
        return cached

    previous_ir = repo.load_document_ir(str(candidate.get("extraction_id") or ""))
    if previous_ir is None:
        return None
    reanchored = reanchor_spans(previous_ir, current_ir)
    aliases = {
        alias.from_span_id: alias.to_span_id
        for alias in reanchored.aliases
        if alias.match_kind == EXACT_HASH
    }
    cited = _cited_span_ids(cached)
    if not cited.issubset(aliases):
        return None
    rebound = _rebind_inventory_spans(
        cached,
        span_aliases=aliases,
        unit_id=current_unit_id,
        semantic_hash=current_semantic_hash,
    )
    try:
        validate_inventory(rebound, valid_span_ids)
    except InventoryValidationError:
        return None
    return rebound


@dataclass
class InventoryResult:
    inventory: SourceUnitInventory
    inventory_id: str
    profile: str
    cache_hit: bool
    reused_profile: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PreparedInventory:
    """Cache-missed inventory work with every database read already resolved.

    Instances are safe to hand to a provider worker thread: the remaining
    execution path is pure model I/O plus deterministic validation/merging.
    """

    extraction_id: str
    revision_id: str
    unit_id: str
    source_unit_ids: tuple[str, ...]
    semantic_hash: str
    role: str
    profile: str
    provider: str
    model: str
    windows: tuple[dict[str, Any], ...]
    valid_span_ids: frozenset[str]
    output_budget_tokens: int | None
    prompt_version: str
    schema_version: int


@dataclass(frozen=True)
class InventoryExecution:
    """Fresh provider output awaiting runner-thread persistence."""

    inventory: SourceUnitInventory
    usage: dict[str, Any]


def prepare_unit_inventory(
    repo: Repository,
    extraction_id: str,
    unit_id: str,
    *,
    unit_ids: list[str] | None = None,
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
) -> InventoryResult | PreparedInventory:
    """Resolve one inventory from cache or return provider-only work.

    Cache lookup, cross-revision re-anchoring, and binding-row writes happen
    here on the runner thread. A miss returns a self-contained object whose
    execution requires no repository access.
    """

    requested_profile = normalize_profile(profile or default_inventory_profile(role))
    run = repo.get_extraction_run(extraction_id)
    if run is None:
        raise InventoryError(f"extraction '{extraction_id}' does not exist.")
    revision_id = run["revision_id"]
    ir = repo.load_document_ir(extraction_id)
    if ir is None:
        raise InventoryError(f"extraction '{extraction_id}' has no persisted IR.")
    source_unit_ids = list(unit_ids or [unit_id])
    members = _inventory_members(ir, source_unit_ids)
    effective_id = _effective_unit_id(source_unit_ids)
    semantic_hash = _effective_semantic_hash(members)
    provider_name = provider or getattr(client, "provider_type", None) or "codex"
    model_name = model or getattr(client, "model", None) or "unknown"
    by_span = {block.span_id: block for block in ir.blocks}
    valid_span_ids = frozenset(
        span_id
        for member in members
        for span_id in member.span_ids
        if span_id in by_span and _view_block(by_span[span_id]) is not None
    )

    # Cache lookup (§3.2 reuse): any row with the same non-profile identity whose
    # stored profile satisfies the request. Cross-revision candidates are rebound
    # only after all cited spans re-anchor exactly, then materialized as a binding
    # row for this revision/extraction.
    for candidate in repo.reusable_unit_inventories(
        source_revision_id=revision_id,
        unit_id=effective_id,
        unit_semantic_hash=semantic_hash,
        inventory_schema_version=schema_version,
        prompt_version=prompt_version,
        provider=provider_name,
        model=model_name,
    ):
        if not profile_satisfies(
            candidate["inventory_profile"],
            candidate["inventory_schema_version"],
            requested_profile,
        ):
            continue
        reusable = _reusable_inventory_for_extraction(
            repo,
            candidate,
            current_ir=ir,
            current_extraction_id=extraction_id,
            current_unit_id=effective_id,
            current_semantic_hash=semantic_hash,
            valid_span_ids=set(valid_span_ids),
        )
        if reusable is None:
            continue
        inventory_id = str(candidate["id"])
        if (
            str(candidate.get("source_revision_id") or "") != revision_id
            or str(candidate.get("extraction_id") or "") != extraction_id
        ):
            binding_id = f"inv_{new_ulid()}"
            repo.insert_unit_inventory(
                id=binding_id,
                source_revision_id=revision_id,
                extraction_id=extraction_id,
                unit_id=effective_id,
                unit_semantic_hash=semantic_hash,
                inventory_profile=str(candidate["inventory_profile"]),
                inventory_schema_version=schema_version,
                prompt_version=prompt_version,
                provider=provider_name,
                model=model_name,
                inventory=reusable.model_dump(),
                usage={"calls": 0, "rebound_from_inventory_id": candidate["id"]},
                clock=clock,
            )
            # The table has one binding per semantic identity within a revision.
            # Rebinding a repaired extraction therefore updates that existing row
            # through its UNIQUE key and retains its id; a genuinely new revision
            # inserts the fresh binding id.
            inventory_id = (
                str(candidate["id"])
                if str(candidate.get("source_revision_id") or "") == revision_id
                else binding_id
            )
        return InventoryResult(
            inventory=reusable,
            inventory_id=inventory_id,
            profile=requested_profile,
            cache_hit=True,
            reused_profile=candidate["inventory_profile"],
        )

    # Window construction can be substantial for a large composite. Keep it
    # strictly on the miss path so a cache hit performs no prompt preparation.
    windows = build_inventory_windows(
        ir,
        effective_id,
        unit_ids=source_unit_ids,
        input_budget_tokens=input_budget_tokens,
    )
    return PreparedInventory(
        extraction_id=extraction_id,
        revision_id=revision_id,
        unit_id=effective_id,
        source_unit_ids=tuple(source_unit_ids),
        semantic_hash=semantic_hash,
        role=role,
        profile=requested_profile,
        provider=provider_name,
        model=model_name,
        windows=tuple(windows),
        valid_span_ids=valid_span_ids,
        output_budget_tokens=output_budget_tokens,
        prompt_version=prompt_version,
        schema_version=schema_version,
    )


def execute_prepared_inventory(
    prepared: PreparedInventory,
    client: Any,
    *,
    progress: Callable[[int, int], None] | None = None,
) -> InventoryExecution:
    """Run provider windows without touching SQLite."""

    per_window: list[SourceUnitInventory] = []
    usage: dict[str, Any] = {
        "calls": 0,
        "input_tokens_estimate": sum(
            max(1, len(json.dumps(window, default=str)) // _CHARS_PER_TOKEN)
            for window in prepared.windows
        ),
    }
    total_windows = len(prepared.windows)
    for ordinal, window in enumerate(prepared.windows, start=1):
        context = SourceUnitInventoryContext(
            unit_id=prepared.unit_id,
            semantic_hash=prepared.semantic_hash,
            role=prepared.role,
            inventory_profile=prepared.profile,
            unit_view=window,
        )
        raw = request_source_unit_inventory(client, context)
        assigned = assign_deterministic_ids(
            raw,
            unit_id=prepared.unit_id,
            window_ordinal=window["window_ordinal"],
        )
        assigned.semantic_hash = prepared.semantic_hash
        validate_inventory(assigned, set(prepared.valid_span_ids))
        per_window.append(assigned)
        usage["calls"] += 1
        if progress is not None:
            progress(ordinal, total_windows)

    merged = merge_windows(per_window)
    merged.unit_id = prepared.unit_id
    merged.semantic_hash = prepared.semantic_hash
    usage["output_tokens_estimate"] = max(
        1, len(merged.model_dump_json()) // _CHARS_PER_TOKEN
    )
    if (
        prepared.output_budget_tokens is not None
        and usage["output_tokens_estimate"] > prepared.output_budget_tokens
    ):
        raise InventoryValidationError(
            "inventory output exceeded its configured token budget"
        )
    return InventoryExecution(inventory=merged, usage=usage)


def persist_prepared_inventory(
    repo: Repository,
    prepared: PreparedInventory,
    execution: InventoryExecution,
    *,
    clock: Clock | None = None,
) -> InventoryResult:
    """Persist fresh provider output on the runner thread."""

    inventory_id = f"inv_{new_ulid()}"
    repo.insert_unit_inventory(
        id=inventory_id,
        source_revision_id=prepared.revision_id,
        extraction_id=prepared.extraction_id,
        unit_id=prepared.unit_id,
        unit_semantic_hash=prepared.semantic_hash,
        inventory_profile=prepared.profile,
        inventory_schema_version=prepared.schema_version,
        prompt_version=prepared.prompt_version,
        provider=prepared.provider,
        model=prepared.model,
        inventory=execution.inventory.model_dump(),
        usage=execution.usage,
        clock=clock,
    )
    return InventoryResult(
        inventory=execution.inventory,
        inventory_id=inventory_id,
        profile=prepared.profile,
        cache_hit=False,
        usage=execution.usage,
    )


def run_unit_inventory(
    repo: Repository,
    extraction_id: str,
    unit_id: str,
    *,
    unit_ids: list[str] | None = None,
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
    progress: Callable[[int, int], None] | None = None,
) -> InventoryResult:
    """Produce or reuse one effective unit inventory under a role/profile (§7).

    Cache hit → zero new tokens. Cache miss → windows, one codex call each,
    deterministic ids, merge, validate, persist under the full UNIQUE key.
    ``unit_ids`` carries the ordered source membership of an explicit
    ``merge_with_next`` composite.
    """

    prepared = prepare_unit_inventory(
        repo,
        extraction_id,
        unit_id,
        unit_ids=unit_ids,
        role=role,
        profile=profile,
        client=client,
        provider=provider,
        model=model,
        input_budget_tokens=input_budget_tokens,
        output_budget_tokens=output_budget_tokens,
        clock=clock,
        prompt_version=prompt_version,
        schema_version=schema_version,
    )
    if isinstance(prepared, InventoryResult):
        return prepared
    execution = execute_prepared_inventory(prepared, client, progress=progress)
    return persist_prepared_inventory(repo, prepared, execution, clock=clock)


def inventory_marker(repo: Repository, extraction_id: str, unit_id: str) -> dict[str, Any]:
    """Whether a unit already has a cached inventory (wires the M3 outline seam).

    Returns the richest cached profile for the unit's current semantic hash, so
    the outline/build-plan can render the "cached" affordance from real rows."""

    run = repo.get_extraction_run(extraction_id)
    if run is None:
        return {"inventoried": False, "inventory_profile": None}
    rows = repo.unit_inventories_for_extraction(extraction_id)
    covering_ids = {unit_id}
    ir = repo.load_document_ir(extraction_id)
    selection = repo.get_unit_selection(extraction_id)
    if ir is not None and selection is not None:
        from learnloop.content.synthesis.source_unit_selection import compute_effective_units

        for effective in compute_effective_units(
            ir, selection.get("boundary_overrides") or []
        ):
            source_ids = {
                str(source_id) for source_id in effective["source_unit_ids"]
            }
            if unit_id == effective["effective_id"] or unit_id in source_ids:
                covering_ids.add(str(effective["effective_id"]))
    profiles = sorted(
        {
            row["inventory_profile"]
            for row in rows
            if row["unit_id"] in covering_ids
        }
    )
    if not profiles:
        return {"inventoried": False, "inventory_profile": None}
    best = "combined" if "combined" in profiles else profiles[0]
    return {"inventoried": True, "inventory_profile": best, "profiles": profiles}

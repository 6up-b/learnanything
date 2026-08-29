---
title: "learnloop.content.synthesis.source_unit_inventory"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/source_unit_inventory.py"
source_paths:
  - "src/learnloop/content/synthesis/source_unit_inventory.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.synthesis.source_unit_inventory module"
  - "src/learnloop/content/synthesis/source_unit_inventory.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.source_unit_inventory`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.source_unit_inventory` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Role-specific unit inventories (spec_source_ingestion_v2 §7, ING M4).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py) |
| Source lines | 839 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class InventoryError(ValueError)` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 73) — A unit/extraction reference or inventory profile is invalid.
- `class InventoryValidationError(ValueError)` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 77) — A returned inventory cites an unknown span id or an uncited assertion.
- `request_source_unit_inventory(client: StructuredTransport, context: SourceUnitInventoryContext) -> SourceUnitInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 81) — Inventory one source-unit window through the shared transport.
- `normalize_profile(profile: str | None) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 94)
- `profile_satisfies(stored_profile: str, stored_schema_version: int, requested_profile: str) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 103) — Does a cached inventory satisfy a request?
- `build_inventory_windows(ir: DocumentIR, unit_id: str, *, unit_ids: list[str] | None=None, input_budget_tokens: int) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 178) — Deterministic inventory view for one effective unit, split into windows.
- `assign_deterministic_ids(inventory: SourceUnitInventory, *, unit_id: str, window_ordinal: int) -> SourceUnitInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 288) — Reassign every id from (unit_id, window_ordinal, item_ordinal, content-hash) and rewrite intra-inventory `*_ids`/`concept_mention_id` references (§7).
- `validate_inventory(inventory: SourceUnitInventory, valid_span_ids: set[str]) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 345) — Reject uncited assertions and unknown span ids (§7, §3).
- `merge_windows(inventories: list[SourceUnitInventory]) -> SourceUnitInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 366) — Deterministic concat + dedup by assigned id (§7).
- `class InventoryResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 488)
- `class PreparedInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 498) — Cache-missed inventory work with every database read already resolved.
- `class InventoryExecution` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 522) — Fresh provider output awaiting runner-thread persistence.
- `prepare_unit_inventory(repo: Repository, extraction_id: str, unit_id: str, *, unit_ids: list[str] | None=None, role: str, profile: str | None=None, client: Any=None, provider: str | None=None, model: str | None=None, input_budget_tokens: int=20000, output_budget_tokens: int | None=3000, clock: Clock | None=None, prompt_version: str=SOURCE_UNIT_INVENTORY_PROMPT_VERSION, schema_version: int=INVENTORY_SCHEMA_VERSION) -> InventoryResult | PreparedInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 529) — Resolve one inventory from cache or return provider-only work.
- `execute_prepared_inventory(prepared: PreparedInventory, client: Any, *, progress: Callable[[int, int], None] | None=None) -> InventoryExecution` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 669) — Run provider windows without touching SQLite.
- `persist_prepared_inventory(repo: Repository, prepared: PreparedInventory, execution: InventoryExecution, *, clock: Clock | None=None) -> InventoryResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 723) — Persist fresh provider output on the runner thread.
- `run_unit_inventory(repo: Repository, extraction_id: str, unit_id: str, *, unit_ids: list[str] | None=None, role: str, profile: str | None=None, client: Any=None, provider: str | None=None, model: str | None=None, input_budget_tokens: int=20000, output_budget_tokens: int | None=3000, clock: Clock | None=None, prompt_version: str=SOURCE_UNIT_INVENTORY_PROMPT_VERSION, schema_version: int=INVENTORY_SCHEMA_VERSION, progress: Callable[[int, int], None] | None=None) -> InventoryResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 757) — Produce or reuse one effective unit inventory under a role/profile (§7).
- `inventory_marker(repo: Repository, extraction_id: str, unit_id: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 805) — Whether a unit already has a cached inventory (wires the M3 outline seam).

### Module constants

- `INVENTORY_SCHEMA_VERSION` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 54)
- `INVENTORY_PROFILES` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 56)
- `_OMIT_BLOCK_TYPES` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 60)
- `_OMIT_ROLE_HINTS` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 61)
- `_CHARS_PER_TOKEN` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 63)
- `_COMBINED_SATISFIES` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 68)
- `_SPAN_CITING_FIELDS` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 334)

## Internal implementation anchors

- `_approx_tokens(text: str) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 121)
- `_view_block(block) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 127) — One inventory-view block, or None when it is omitted boilerplate (§3).
- `_section_key(block) -> tuple[str, ...]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 141)
- `_inventory_members(ir: DocumentIR, unit_ids: list[str]) -> list[Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 145) — Resolve an ordered effective inventory unit from its source members.
- `_effective_unit_id(unit_ids: list[str]) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 160)
- `_effective_semantic_hash(members: list[Any]) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 164)
- `_unit_heading(unit, blocks) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 262)
- `_content_hash(*parts: Any) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 271)
- `_stringify(value: Any) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 276)
- `_assign_id(unit_id: str, window_ordinal: int, item_ordinal: int, content_hash: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 282) — Service-owned deterministic id (§7): stable for an unchanged semantic view.
- `_cited_span_ids(inventory: SourceUnitInventory) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 407)
- `_rebind_inventory_spans(inventory: SourceUnitInventory, *, span_aliases: Mapping[str, str], unit_id: str, semantic_hash: str) -> SourceUnitInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 416) — Return the same semantic artifact bound to a new extraction's span ids.
- `_reusable_inventory_for_extraction(repo: Repository, candidate: Mapping[str, Any], *, current_ir: DocumentIR, current_extraction_id: str, current_unit_id: str, current_semantic_hash: str, valid_span_ids: set[str]) -> SourceUnitInventory | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 436) — Safely bind a cached semantic artifact to the current extraction.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `run_unit_inventory`; statically calls `run_unit_inventory`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `InventoryExecution`, `InventoryResult`, `PreparedInventory`, `execute_prepared_inventory`, `normalize_profile`, `persist_prepared_inventory`, `prepare_unit_inventory`; statically calls `execute_prepared_inventory`, `normalize_profile`, `persist_prepared_inventory`, `prepare_unit_inventory`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `inventory_marker`; statically calls `inventory_marker`
- [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]] — imports `profile_satisfies`; statically calls `profile_satisfies`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `profile_satisfies`; statically calls `profile_satisfies`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `default_inventory_profile`; calls `default_inventory_profile`
- [[Reference/Modules/learnloop/content/synthesis/ai_contracts|learnloop.content.synthesis.ai_contracts]] — imports `SOURCE_UNIT_INVENTORY_PROMPT_VERSION`, `SourceUnitInventory`, `SourceUnitInventoryContext`, `source_unit_inventory_prompt`; calls `SourceUnitInventory`, `SourceUnitInventoryContext`, `source_unit_inventory_prompt`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `compute_effective_units`; calls `compute_effective_units`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `normalize_semantic_text`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentIR`
- [[Reference/Modules/learnloop/ingest/reanchor|learnloop.ingest.reanchor]] — imports `EXACT_HASH`, `reanchor_spans`; calls `reanchor_spans`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]], [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_build_study_map_routing.py](../../../../../../../tests/test_build_study_map_routing.py) — direct import
- [tests/test_facet_candidates.py](../../../../../../../tests/test_facet_candidates.py) — direct import
  - `test_harvests_candidates_from_unit_inventories`
- [tests/test_inventory_merge_parallel.py](../../../../../../../tests/test_inventory_merge_parallel.py) — direct import
  - `test_full_inventory_cache_hit_never_constructs_provider`
  - `test_merged_inventory_marker_covers_member_units`
  - `test_synthesis_gather_folds_merged_group_once_with_member_fallback`
- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — direct import
  - `test_n_sources_append_linear_inventory_and_bounded_context`
- [tests/test_source_inventory.py](../../../../../../../tests/test_source_inventory.py) — direct import
  - `test_changed_page_reinventories_only_that_unit`
  - `test_combined_inventory_reused_for_semantic_request`
  - `test_combined_satisfies_narrower_only_when_schema_allows`
  - `test_composite_inventory_cache_rebinds_all_member_spans_across_revisions`
  - `test_deterministic_inventory_ids_stable`
  - `test_inventory_can_disable_the_output_ceiling`
  - `test_inventory_rejects_uncited_and_unknown_spans`
  - `test_oversize_unit_splits_into_windows`
  - `test_procedure_signal_span_ids_coercion_and_validation`
  - `test_role_aware_inventory_profiles`
  - `test_semantic_inventory_cache_rebinds_across_revisions`
  - `test_unit_inventory_cache_reuse_across_collections`
- [tests/test_source_set_synthesis.py](../../../../../../../tests/test_source_set_synthesis.py) — direct import
- [tests/test_source_sets.py](../../../../../../../tests/test_source_sets.py) — direct import
  - `test_one_source_two_sets_different_roles`
  - `test_source_coverage_readiness_report`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change source unit inventory policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

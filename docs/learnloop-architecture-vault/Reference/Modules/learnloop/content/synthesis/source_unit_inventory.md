---
title: "learnloop.content.synthesis.source_unit_inventory"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/source_unit_inventory.py"
source_paths:
  - "src/learnloop/content/synthesis/source_unit_inventory.py"
source_commit: "5f7340aaf0366e30dca27f6cfc233dae3e37c850"
source_commit_timestamp: "2026-09-23T12:54:18-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
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
| Source lines | 930 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5f7340aaf0366e30dca27f6cfc233dae3e37c850` |
| Commit timestamp | `2026-09-23T12:54:18-04:00` |

## Public API

- `class InventoryError(ValueError)` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 77) — A unit/extraction reference or inventory profile is invalid.
- `class InventoryValidationError(ValueError)` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 81) — A returned inventory cites an unknown span id or an uncited assertion.
- `request_source_unit_inventory(client: StructuredTransport, context: SourceUnitInventoryContext) -> SourceUnitInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 85) — Inventory one source-unit window through the shared transport.
- `normalize_profile(profile: str | None) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 98)
- `profile_satisfies(stored_profile: str, stored_schema_version: int, requested_profile: str) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 107) — Does a cached inventory satisfy a request?
- `build_inventory_windows(ir: DocumentIR, unit_id: str, *, unit_ids: list[str] | None=None, input_budget_tokens: int) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 182) — Deterministic inventory view for one effective unit, split into windows.
- `assign_deterministic_ids(inventory: SourceUnitInventory, *, unit_id: str, window_ordinal: int) -> SourceUnitInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 292) — Reassign every id from (unit_id, window_ordinal, item_ordinal, content-hash) and rewrite intra-inventory `*_ids`/`concept_mention_id` references (§7).
- `validate_inventory(inventory: SourceUnitInventory, valid_span_ids: set[str]) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 349) — Reject uncited assertions and unknown span ids (§7, §3).
- `merge_windows(inventories: list[SourceUnitInventory]) -> SourceUnitInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 370) — Deterministic concat + dedup by assigned id (§7).
- `class InventoryResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 492)
- `class PreparedInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 502) — Cache-missed inventory work with every database read already resolved.
- `class InventoryExecution` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 528) — Fresh provider output awaiting runner-thread persistence.
- `prepare_unit_inventory(repo: Repository, extraction_id: str, unit_id: str, *, unit_ids: list[str] | None=None, role: str, profile: str | None=None, client: Any=None, provider: str | None=None, model: str | None=None, input_budget_tokens: int=20000, output_budget_tokens: int | None=3000, clock: Clock | None=None, prompt_version: str=SOURCE_UNIT_INVENTORY_PROMPT_VERSION, schema_version: int=INVENTORY_SCHEMA_VERSION) -> InventoryResult | PreparedInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 535) — Resolve one inventory from cache or return provider-only work.
- `inventory_window_key(context: SourceUnitInventoryContext, settings: dict[str, Any], *, schema_version: int) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 721) — Checkpoint identity of one inventory window.
- `execute_prepared_inventory(prepared: PreparedInventory, client: Any, *, progress: Callable[[int, int], None] | None=None, checkpoint: Callable[[str, SourceUnitInventory, dict[str, Any]], None] | None=None) -> InventoryExecution` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 739) — Run provider windows without touching SQLite.
- `persist_prepared_inventory(repo: Repository, prepared: PreparedInventory, execution: InventoryExecution, *, clock: Clock | None=None) -> InventoryResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 811) — Persist fresh provider output on the runner thread.
- `run_unit_inventory(repo: Repository, extraction_id: str, unit_id: str, *, unit_ids: list[str] | None=None, role: str, profile: str | None=None, client: Any=None, provider: str | None=None, model: str | None=None, input_budget_tokens: int=20000, output_budget_tokens: int | None=3000, clock: Clock | None=None, prompt_version: str=SOURCE_UNIT_INVENTORY_PROMPT_VERSION, schema_version: int=INVENTORY_SCHEMA_VERSION, progress: Callable[[int, int], None] | None=None) -> InventoryResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 845) — Produce or reuse one effective unit inventory under a role/profile (§7).
- `inventory_marker(repo: Repository, extraction_id: str, unit_id: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 896) — Whether a unit already has a cached inventory (wires the M3 outline seam).

### Module constants

- `INVENTORY_SCHEMA_VERSION` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 58)
- `INVENTORY_PROFILES` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 60)
- `_OMIT_BLOCK_TYPES` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 64)
- `_OMIT_ROLE_HINTS` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 65)
- `_CHARS_PER_TOKEN` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 67)
- `_COMBINED_SATISFIES` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 72)
- `_SPAN_CITING_FIELDS` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 338)

## Internal implementation anchors

- `_approx_tokens(text: str) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 125)
- `_view_block(block) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 131) — One inventory-view block, or None when it is omitted boilerplate (§3).
- `_section_key(block) -> tuple[str, ...]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 145)
- `_inventory_members(ir: DocumentIR, unit_ids: list[str]) -> list[Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 149) — Resolve an ordered effective inventory unit from its source members.
- `_effective_unit_id(unit_ids: list[str]) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 164)
- `_effective_semantic_hash(members: list[Any]) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 168)
- `_unit_heading(unit, blocks) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 266)
- `_content_hash(*parts: Any) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 275)
- `_stringify(value: Any) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 280)
- `_assign_id(unit_id: str, window_ordinal: int, item_ordinal: int, content_hash: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 286) — Service-owned deterministic id (§7): stable for an unchanged semantic view.
- `_cited_span_ids(inventory: SourceUnitInventory) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 411)
- `_rebind_inventory_spans(inventory: SourceUnitInventory, *, span_aliases: Mapping[str, str], unit_id: str, semantic_hash: str) -> SourceUnitInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 420) — Return the same semantic artifact bound to a new extraction's span ids.
- `_reusable_inventory_for_extraction(repo: Repository, candidate: Mapping[str, Any], *, current_ir: DocumentIR, current_extraction_id: str, current_unit_id: str, current_semantic_hash: str, valid_span_ids: set[str]) -> SourceUnitInventory | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 440) — Safely bind a cached semantic artifact to the current extraction.
- `_reusable_window_checkpoint(repo: Repository, key: str, valid_span_ids: frozenset[str]) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 700) — Return a saved inventory window, discarding one that no longer validates.

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

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `generation_limit`, `model_settings`; calls `content_key`, `generation_limit`, `model_settings`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `UsageMeter`; calls `UsageMeter`
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
- Third party: `pydantic`

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
- [tests/test_ingestion_checkpoints.py](../../../../../../../tests/test_ingestion_checkpoints.py) — direct import
  - `test_inventory_retry_reuses_validated_window_after_interruption`
  - `test_inventory_window_key_changes_with_each_provider_setting`
  - `test_inventory_window_key_follows_the_rendered_prompt`
- [tests/test_inventory_merge_parallel.py](../../../../../../../tests/test_inventory_merge_parallel.py) — direct import
  - `test_full_inventory_cache_hit_never_constructs_provider`
  - `test_merged_inventory_marker_covers_member_units`
  - `test_synthesis_gather_folds_merged_group_once_with_member_fallback`
- [tests/test_model_work_checkpoints.py](../../../../../../../tests/test_model_work_checkpoints.py) — direct import
  - `test_ingest_job_and_direct_inventory_key_windows_identically`
  - `test_inventory_window_checkpoint_that_no_longer_validates_is_discarded`
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

---
title: "learnloop.content.synthesis.source_unit_inventory"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/source_unit_inventory.py"
source_paths:
  - "src/learnloop/content/synthesis/source_unit_inventory.py"
generated: true
generated_at: "2026-11-02"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.source_unit_inventory` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Role-specific unit inventories (spec_source_ingestion_v2 §7, ING M4).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py) |
| Source lines | 1151 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class InventoryError(ValueError)` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 79) — A unit/extraction reference or inventory profile is invalid.
- `class InventoryValidationError(ValueError)` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 83) — A returned inventory cites an unknown span id or an uncited assertion.
- `request_source_unit_inventory(client: StructuredTransport, context: SourceUnitInventoryContext) -> SourceUnitInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 87) — Inventory one source-unit window through the shared transport.
- `normalize_profile(profile: str | None) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 100)
- `profile_satisfies(stored_profile: str, stored_schema_version: int, requested_profile: str) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 109) — Does a cached inventory satisfy a request?
- `best_inventory(rows: list[dict[str, Any]], unit_id: str, *, semantic_hash: str | None, prompt_version: str, provider: str | None, model: str | None, profile: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 127) — The one inventory row synthesis and coverage read for a unit.
- `class InventoryChoice` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 160) — Which inventory row a unit's synthesis reads (``row``, ``None`` when the unit has none), and why: ``rule`` is the preference that set it above the next row (``only_row``, ``newest``, ``no_row``, or one of :data:`INVENTORY_PREFERENCES`), with ``profile_unsatisfied`` when no row s…
- `inventory_choice(rows: list[dict[str, Any]], unit_id: str, *, semantic_hash: str | None, prompt_version: str, provider: str | None, model: str | None, profile: str) -> InventoryChoice` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 173) — :func:`best_inventory` with its reasons (the same row, by the same ranking).
- `choose_unit_inventory(rows: list[dict[str, Any]], unit_id: str, unit_ids: list[str], *, ir: DocumentIR | None, route: tuple[str, str] | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 226) — ``best_inventory`` for one effective unit of ``ir``, under today's prompt label and ``route`` (``current_inventory_identity``), for synthesis's combined request.
- `choose_unit_inventory_with_reasons(rows: list[dict[str, Any]], unit_id: str, unit_ids: list[str], *, ir: DocumentIR | None, route: tuple[str, str] | None) -> InventoryChoice` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 241) — :func:`choose_unit_inventory` with its reasons (:func:`inventory_choice`).
- `current_unit_semantic_hash(ir: DocumentIR | None, unit_ids: list[str]) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 263) — The semantic hash an inventory of these units would carry today, or ``None``.
- `current_inventory_identity(config: Any) -> tuple[str, str] | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 274) — The provider type and model an inventory job would record now.
- `inventoried_unit_ids(rows: list[dict[str, Any]]) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 336) — The source units these inventory rows cover, alone or as a member of a merged (``merge_with_next``) unit.
- `build_inventory_windows(ir: DocumentIR, unit_id: str, *, unit_ids: list[str] | None=None, input_budget_tokens: int) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 357) — Deterministic inventory view for one effective unit, split into windows.
- `assign_deterministic_ids(inventory: SourceUnitInventory, *, unit_id: str, window_ordinal: int) -> SourceUnitInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 458) — Reassign every id from (unit_id, window_ordinal, item_ordinal, content-hash) and rewrite intra-inventory `*_ids`/`concept_mention_id` references (§7).
- `validate_inventory(inventory: SourceUnitInventory, valid_span_ids: set[str]) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 515) — Reject uncited assertions and unknown span ids (§7, §3).
- `merge_windows(inventories: list[SourceUnitInventory]) -> SourceUnitInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 536) — Deterministic concat + dedup by assigned id (§7).
- `class InventoryResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 658)
- `class PreparedInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 668) — Cache-missed inventory work with every database read already resolved.
- `class InventoryExecution` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 698) — Fresh provider output awaiting runner-thread persistence.
- `prepare_unit_inventory(repo: Repository, extraction_id: str, unit_id: str, *, unit_ids: list[str] | None=None, role: str, profile: str | None=None, client: Any=None, provider: str | None=None, model: str | None=None, input_budget_tokens: int=20000, output_budget_tokens: int | None=3000, output_ceiling_tokens: int | None=None, clock: Clock | None=None, prompt_version: str=SOURCE_UNIT_INVENTORY_PROMPT_VERSION, schema_version: int=INVENTORY_SCHEMA_VERSION) -> InventoryResult | PreparedInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 705) — Resolve one inventory from cache or return provider-only work.
- `window_checkpoint(repo: Any, key: str, valid_span_ids: Collection[str]) -> ModelCheckpoint[SourceUnitInventory]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 883) — One inventory window's checkpoint.
- `inventory_window_key(context: SourceUnitInventoryContext, settings: dict[str, Any], *, schema_version: int) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 896) — Checkpoint identity of one inventory window.
- `inventory_row_key(*, provider: str, model: str, schema_version: int) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 913) — What an inventory row was asked, compared before the row is reused: the request key of the inventory prompt rendered over an empty context, under the schema version, provider and model.
- `execute_prepared_inventory(prepared: PreparedInventory, client: Any, *, progress: Callable[[int, int], None] | None=None, checkpoint: Callable[[str, SourceUnitInventory, dict[str, Any]], None] | None=None) -> InventoryExecution` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 940) — Run provider windows without touching SQLite.
- `persist_prepared_inventory(repo: Repository, prepared: PreparedInventory, execution: InventoryExecution, *, clock: Clock | None=None) -> InventoryResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 1025) — Persist fresh provider output on the runner thread.
- `run_unit_inventory(repo: Repository, extraction_id: str, unit_id: str, *, unit_ids: list[str] | None=None, role: str, profile: str | None=None, client: Any=None, provider: str | None=None, model: str | None=None, input_budget_tokens: int=20000, output_budget_tokens: int | None=3000, output_ceiling_tokens: int | None=None, clock: Clock | None=None, prompt_version: str=SOURCE_UNIT_INVENTORY_PROMPT_VERSION, schema_version: int=INVENTORY_SCHEMA_VERSION, progress: Callable[[int, int], None] | None=None) -> InventoryResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 1064) — Produce or reuse one effective unit inventory under a role/profile (§7).
- `inventory_marker(repo: Repository, extraction_id: str, unit_id: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 1117) — Whether a unit already has a cached inventory (wires the M3 outline seam).

### Module constants

- `INVENTORY_SCHEMA_VERSION` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 56)
- `INVENTORY_PROFILES` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 58)
- `_OMIT_BLOCK_TYPES` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 62)
- `_OMIT_ROLE_HINTS` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 63)
- `_CHARS_PER_TOKEN` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 65)
- `INVENTORY_WINDOW_PURPOSE` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 66)
- `INVENTORY_ROW_PURPOSE` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 67)
- `INVENTORY_ROW_KEY_FIELD` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 69)
- `_COMBINED_SATISFIES` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 74)
- `INVENTORY_PREFERENCES` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 156)
- `_SPAN_CITING_FIELDS` ([src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 504)

## Internal implementation anchors

- `_approx_tokens(text: str) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 293)
- `_view_block(block) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 299) — One inventory-view block, or None when it is omitted boilerplate (§3).
- `_section_key(block) -> tuple[str, ...]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 313)
- `_inventory_members(ir: DocumentIR, unit_ids: list[str]) -> list[Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 317) — Resolve an ordered effective inventory unit from its source members.
- `_effective_unit_id(unit_ids: list[str]) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 332)
- `_effective_semantic_hash(members: list[Any]) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 343)
- `_content_hash(*parts: Any) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 441)
- `_stringify(value: Any) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 446)
- `_assign_id(unit_id: str, window_ordinal: int, item_ordinal: int, content_hash: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 452) — Service-owned deterministic id (§7): stable for an unchanged semantic view.
- `_cited_span_ids(inventory: SourceUnitInventory) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 577)
- `_rebind_inventory_spans(inventory: SourceUnitInventory, *, span_aliases: Mapping[str, str], unit_id: str, semantic_hash: str) -> SourceUnitInventory` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 586) — Return the same semantic artifact bound to a new extraction's span ids.
- `_reusable_inventory_for_extraction(repo: Repository, candidate: Mapping[str, Any], *, current_ir: DocumentIR, current_extraction_id: str, current_unit_id: str, current_semantic_hash: str, valid_span_ids: set[str]) -> SourceUnitInventory | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py), line 606) — Safely bind a cached semantic artifact to the current extraction.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `run_unit_inventory`; statically calls `run_unit_inventory`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `InventoryResult`, `PreparedInventory`, `current_inventory_identity`, `execute_prepared_inventory`, `normalize_profile`, `persist_prepared_inventory`, `prepare_unit_inventory`, `window_checkpoint`; statically calls `current_inventory_identity`, `execute_prepared_inventory`, `normalize_profile`, `persist_prepared_inventory`, `prepare_unit_inventory`, `window_checkpoint`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `InventoryValidationError`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `inventory_marker`; statically calls `inventory_marker`
- [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]] — imports `choose_unit_inventory`, `current_inventory_identity`; statically calls `choose_unit_inventory`, `current_inventory_identity`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `InventoryChoice`, `choose_unit_inventory_with_reasons`, `current_inventory_identity`; statically calls `choose_unit_inventory_with_reasons`, `current_inventory_identity`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `inventoried_unit_ids`; statically calls `inventoried_unit_ids`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `ModelCheckpoint`, `generation_limit`, `model_settings`, `request_key`; calls `ModelCheckpoint`, `generation_limit`, `model_settings`, `request_key`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`; calls `provider_for_task`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `UsageMeter`; calls `UsageMeter`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `default_inventory_profile`; calls `default_inventory_profile`
- [[Reference/Modules/learnloop/content/synthesis/ai_contracts|learnloop.content.synthesis.ai_contracts]] — imports `SOURCE_UNIT_INVENTORY_PROMPT_VERSION`, `SourceUnitInventory`, `SourceUnitInventoryContext`, `source_unit_inventory_prompt`; calls `SourceUnitInventory`, `SourceUnitInventoryContext`, `source_unit_inventory_prompt`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `compute_effective_units`; calls `compute_effective_units`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentIR`
- [[Reference/Modules/learnloop/ingest/reanchor|learnloop.ingest.reanchor]] — imports `EXACT_HASH`, `reanchor_spans`; calls `reanchor_spans`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]], [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]], [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/facet_authority_helpers.py](../../../../../../../tests/facet_authority_helpers.py) — direct import
- [tests/identity_pins_helpers.py](../../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/source_append_helpers.py](../../../../../../../tests/source_append_helpers.py) — direct import
- [tests/source_set_synthesis_helpers.py](../../../../../../../tests/source_set_synthesis_helpers.py) — direct import
- [tests/test_build_study_map_routing.py](../../../../../../../tests/test_build_study_map_routing.py) — direct import
- [tests/test_cli_append_units.py](../../../../../../../tests/test_cli_append_units.py) — direct import
- [tests/test_collection_append_units.py](../../../../../../../tests/test_collection_append_units.py) — direct import
  - `test_a_fully_inventoried_unsent_member_is_appended_with_no_inventory_work`
  - `test_inventoried_unit_ids_counts_merged_members`
  - `test_new_units_of_a_partly_inventoried_member_are_inventoried_and_appended`
- [tests/test_exam_protection_identity.py](../../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_f2_a_reused_inventory_never_releases_duplicate_or_fragment_copies`
  - `test_f2_reuse_never_erases_the_origins_signal`
  - `test_identity_review_f2_an_unbound_signal_never_lets_a_known_one_mark_its_origin`
- [tests/test_facet_candidates.py](../../../../../../../tests/test_facet_candidates.py) — direct import
  - `test_harvests_candidates_from_unit_inventories`
- [tests/test_ingest_decision_records.py](../../../../../../../tests/test_ingest_decision_records.py) — direct import
  - `test_the_inventory_choice_is_best_inventory_with_its_reasons`
- [tests/test_ingestion_checkpoints.py](../../../../../../../tests/test_ingestion_checkpoints.py) — direct import
  - `test_inventory_retry_reuses_validated_window_after_interruption`
  - `test_inventory_window_key_changes_with_each_provider_setting`
  - `test_inventory_window_key_follows_the_rendered_prompt`
- [tests/test_inventory_choice.py](../../../../../../../tests/test_inventory_choice.py) — direct import
  - `test_a_reinventory_by_a_newer_model_reaches_the_synthesis_prompt`
  - `test_coverage_reads_the_row_synthesis_reads`
- [tests/test_inventory_merge_parallel.py](../../../../../../../tests/test_inventory_merge_parallel.py) — direct import
  - `test_full_inventory_cache_hit_never_constructs_provider`
  - `test_merged_inventory_marker_covers_member_units`
  - `test_synthesis_gather_folds_merged_group_once_with_member_fallback`
- [tests/test_inventory_output_allowance.py](../../../../../../../tests/test_inventory_output_allowance.py) — direct import
  - `test_a_build_that_stopped_does_not_show_the_internal_reason_on_the_library_card`
  - `test_a_unit_long_enough_for_several_windows_is_allowed_one_windows_amount_for_each`
  - `test_a_window_a_little_over_its_budget_is_kept_under_a_ceiling_above_it`
  - `test_a_window_that_keeps_to_its_limit_is_not_charged_for_the_ids_the_service_adds`
  - `test_after_a_window_writes_past_its_ceiling_retry_goes_on_from_where_it_stopped`
- [tests/test_model_work_checkpoints.py](../../../../../../../tests/test_model_work_checkpoints.py) — direct import
  - `test_ingest_job_and_direct_inventory_key_windows_identically`
  - `test_inventory_window_checkpoint_that_no_longer_validates_is_discarded`
- [tests/test_outer_cache_keys.py](../../../../../../../tests/test_outer_cache_keys.py) — direct import
  - `test_a_changed_inventory_model_is_paid_and_not_answered_by_the_old_row`
  - `test_an_inventory_prompt_edited_under_the_same_label_is_paid_once`
  - `test_an_inventory_row_answers_a_request_recorded_under_another_label`
  - `test_an_inventory_row_from_before_the_request_key_keeps_its_label_match`
- [tests/test_rerun_proposals.py](../../../../../../../tests/test_rerun_proposals.py) — direct import
  - `test_an_inventory_re_read_in_place_reaches_synthesis_and_the_record`
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
- [tests/test_source_sets.py](../../../../../../../tests/test_source_sets.py) — direct import
  - `test_one_source_two_sets_different_roles`
  - `test_source_coverage_readiness_report`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_ux11_html_extraction.py](../../../../../../../tests/test_ux11_html_extraction.py) — direct import
  - `test_ux11_a_page_read_before_keeps_its_stored_reading_under_the_new_code`
  - `test_ux11_reading_it_again_gives_the_new_text_and_carries_progress_the_study_map_and_a_highlight`
- [tests/test_ux_phase1_usability_round1.py](../../../../../../../tests/test_ux_phase1_usability_round1.py) — direct import

## Modification guidance

- Change source unit inventory policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/source_unit_inventory.py](../../../../../../../src/learnloop/content/synthesis/source_unit_inventory.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

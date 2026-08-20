---
title: "learnloop.content.proposals.patches"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/proposals/patches.py"
source_paths:
  - "src/learnloop/content/proposals/patches.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.proposals"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.proposals.patches module"
  - "src/learnloop/content/proposals/patches.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-proposals"
---

# `learnloop.content.proposals.patches`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps patches behavior inside its owning package, [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]]. Its public surface centers on `PatchApplicationError`, `CompiledPatch`, `PatchApplyResult`, `apply_accepted_items`, `compute_target_hash`, `reject_applied_items`, `compile_proposal_item`.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/proposals/patches.py](../../../../../../../src/learnloop/content/proposals/patches.py) |
| Source lines | 1041 |
| Owning package | [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class PatchApplicationError(ValueError)` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 37)
- `class CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 42)
- `class PatchApplyResult` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 58)
- `apply_accepted_items(root: Path, patch_id: str, item_ids: list[str] | None=None, *, clock: Clock | None=None) -> PatchApplyResult` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 63) — Accept a dependency-closed set of proposal items as one logical transaction.
- `compute_target_hash(vault: LoadedVault, item_type: str, entity_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 177) — Content hash of the current on-vault target entity (§8.2 expected_target_hash).
- `reject_applied_items(root: Path, patch_id: str, item_ids: list[str] | None=None, *, clock: Clock | None=None) -> int` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 244)
- `compile_proposal_item(vault: LoadedVault, item: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 278)

### Module constants

- `LEARNABLE_MAP_ITEM_TYPES` ([src/learnloop/content/proposals/patches.py](../../../../../../../src/learnloop/content/proposals/patches.py), line 34)
- `_LINK_RELATIONS` ([src/learnloop/content/proposals/patches.py](../../../../../../../src/learnloop/content/proposals/patches.py), line 313)

## Internal implementation anchors

- `_apply_accepted_locked(vault: LoadedVault, repository: Repository, patch_id: str, item_ids: list[str] | None, clock: Clock | None) -> PatchApplyResult` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 87)
- `_accept_time_rechecks(vault: LoadedVault, repository: Repository, ordered_items: list[dict[str, Any]]) -> None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 207)
- `_noop_apply(root: Path, clock: Clock | None) -> None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 316)
- `_compile_provenance_link(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 320) — `provenance_link` create: insert a supporting entity_source_links row (§10.3).
- `_compile_notation_mapping(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 373) — `notation_mapping` create: append a contextual notation equivalence (§10.2).
- `_compile_source_conflict(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 415) — `source_conflict` create: persist an OPEN two-sided conflict (§10.2).
- `_refuse_learnable_on_legacy(vault: LoadedVault, item_type: str, entity_id: str) -> None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 460) — Bootstrap evidence refusal (§8.2 enforcement 2, knowledge-model §12.7).
- `_compile_facet(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 475)
- `_compile_task_blueprint(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 493)
- `_proposal_apply_order(item: dict[str, Any]) -> tuple[int, int, str]` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 525)
- `_proposal_origin(repository: Repository, patch_id: str) -> str` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 548)
- `_compile_concept(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 561)
- `_compile_concept_edge(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 577)
- `_compile_learning_object(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 612)
- `_upsert_learning_object_with_concept(root: Path, data: dict[str, Any], *, auto_create_concept: bool, clock: Clock | None) -> Path` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 645)
- `_concept_from_learning_object(data: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 658)
- `_compile_practice_item(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 679)
- `_reject_unregistered_facets(vault: LoadedVault, entity_id: str, data: dict[str, Any]) -> None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 709) — Generated-item facet gate (knowledge-model §3.2, mirrors the probe gate).
- `_compile_rubric(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 758)
- `_compile_error_type(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 777)
- `_compile_deactivate(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 796)
- `_compile_concept_edge_deactivate(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 819) — Retire a concept edge: accepting removes it from relations.yaml.
- `_apply_reject_side_effect(vault: LoadedVault, repository: Repository, item: dict[str, Any], *, origin: str, clock: Clock | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 843)
- `_revert_deactivate_side_effect(vault: LoadedVault, repository: Repository, item: dict[str, Any], payload: dict[str, Any], entity_id: str, *, origin: str, now: str, clock: Clock | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 930) — Revert an applied ``deactivate``.
- `_concept_revert_blockers(vault: LoadedVault, concept_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 977)
- `_normalize_rubric_payload(payload: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1009)
- `_entity_id(item: dict[str, Any], payload: dict[str, Any], default: str | None=None) -> str` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1017)
- `_default_edge_id(payload: dict[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1024)
- `_edge_by_id(vault: LoadedVault, edge_id: str) -> Any | None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1033)
- `_event_type(operation: str) -> str` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1040)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `PatchApplicationError`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `PatchApplicationError`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `PatchApplicationError`, `_proposal_apply_order`, `compile_proposal_item`; statically calls `PatchApplicationError`, `_proposal_apply_order`, `compile_proposal_item`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `PatchApplyResult`, `apply_accepted_items`, `reject_applied_items`; statically calls `apply_accepted_items`, `reject_applied_items`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `apply_accepted_items`, `compute_target_hash`; statically calls `apply_accepted_items`, `compute_target_hash`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `apply_accepted_items`; statically calls `apply_accepted_items`
- [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] — imports `compute_target_hash`; statically calls `compute_target_hash`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `PatchApplicationError`
- [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]] — imports `PatchApplicationError`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `compute_dependency_closure`, `materialize_targets`, `perform_db_effects`, `stage_target_contents`; calls `compute_dependency_closure`, `materialize_targets`, `perform_db_effects`, `stage_target_contents`
- [[Reference/Modules/learnloop/curriculum/curriculum_locks|learnloop.curriculum.curriculum_locks]] — imports `Operation`, `can_apply`; calls `Operation`, `can_apply`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`; calls `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`, `snake_case`; calls `new_ulid`, `snake_case`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `unregistered_facet_errors`; calls `unregistered_facet_errors`
- [[Reference/Modules/learnloop/ops/vault_lock|learnloop.ops.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `record_content_recalibration`; calls `record_content_recalibration`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `VaultWriterError`, `delete_concept`, `delete_concept_edge`, `upsert_concept`, `upsert_concept_edge`, `upsert_error_type`, `upsert_facet`, `upsert_learning_object`, `upsert_practice_item`; calls `delete_concept`, `delete_concept_edge`, `upsert_concept`, `upsert_concept_edge`, `upsert_error_type`, `upsert_facet`, `upsert_learning_object`, `upsert_practice_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]], [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]], [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_apply_write_ahead.py](../../../../../../../tests/test_apply_write_ahead.py) — direct import
  - `test_apply_writes_entity_source_links_and_marks_intent_applied`
  - `test_dependency_closure_accepts_full_closure_in_order`
  - `test_dependency_closure_reject_prereq_blocks_dependents`
  - `test_expected_target_hash_mismatch_refuses`
  - `test_race_attempt_inserted_after_synthesis_refuses_under_lock`
  - `test_recovery_is_idempotent_and_noop_when_clean`
- [tests/test_generated_item_gate.py](../../../../../../../tests/test_generated_item_gate.py) — direct import
  - `test_legacy_vault_allows_unregistered_facet`
  - `test_registered_facet_accepted`
  - `test_unregistered_facet_rejected`
- [tests/test_graph_edit_proposals.py](../../../../../../../tests/test_graph_edit_proposals.py) — direct import
  - `test_accept_concept_edge_deactivate_removes_edge`
  - `test_reject_after_apply_restores_concept_edge`
  - `test_resolve_edge_direction_retire_removes_and_can_restore`
- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_goal_population_handler_generates_and_applies_practice`
- [tests/test_patch_applier.py](../../../../../../../tests/test_patch_applier.py) — direct import
  - `test_accept_proposal_creates_yaml_content_events_and_state`
  - `test_invalid_proposal_item_cannot_be_accepted`
  - `test_reject_accepted_concept_create_blocks_when_referenced`
  - `test_reject_accepted_concept_create_removes_concept`
- [tests/test_patch_compiler.py](../../../../../../../tests/test_patch_compiler.py) — direct import
  - `test_compile_concept_create`
  - `test_compile_concept_edge_update_preserves_existing_endpoints`
  - `test_compile_concept_edge_validates_endpoints`
  - `test_compile_error_type_create`
  - `test_compile_learning_object_can_introduce_concept`
  - `test_compile_practice_item_requires_known_learning_object`
  - `test_compile_rubric_targets_existing_practice_item`
- [tests/test_proposal_persistence.py](../../../../../../../tests/test_proposal_persistence.py) — direct import
  - `test_create_payload_missing_required_fields_is_invalid`
  - `test_invalid_concept_edge_proposal_is_persisted_invalid`
  - `test_practice_item_without_resolved_rubric_is_invalid_until_edited`
  - `test_reject_route_item_is_persisted_invalid_and_not_applied`
  - `test_source_linked_generated_practice_missing_audit_is_invalid`
  - `test_unresolved_source_ref_is_persisted_invalid`
- [tests/test_sidecar_contract.py](../../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_sidecar_reject_accepted_concept_reports_reference_blocker`
- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — direct import
  - `test_conflict_accept_creates_open_row_reject_creates_none`
  - `test_post_append_near_duplicate_is_aliased_at_mint_and_never_auto_merged`
  - `test_specialized_side_effects_recover_idempotently`
- [tests/test_source_set_synthesis.py](../../../../../../../tests/test_source_set_synthesis.py) — direct import
  - `test_legacy_vault_acceptance_refused`
- [tests/test_synthesis_runs_repo.py](../../../../../../../tests/test_synthesis_runs_repo.py) — direct import
  - `test_synthesis_run_introducing_entity_lineage`

## Modification guidance

- Change patches policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/proposals/patches.py](../../../../../../../src/learnloop/content/proposals/patches.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

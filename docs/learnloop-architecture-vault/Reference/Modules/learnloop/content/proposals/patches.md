---
title: "learnloop.content.proposals.patches"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/proposals/patches.py"
source_paths:
  - "src/learnloop/content/proposals/patches.py"
generated: true
generated_at: "2026-11-02"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps patches behavior inside its owning package, [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]]. Its public surface centers on `PatchApplicationError`, `OutstandingApplyIntentError`, `refuse_while_an_apply_is_outstanding`, `CompiledPatch`, `PatchApplyResult`, `apply_accepted_items`, `applied_content_learning_object_ids`, `recalibrate_applied_content` and 3 more public symbols.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/proposals/patches.py](../../../../../../../src/learnloop/content/proposals/patches.py) |
| Source lines | 1414 |
| Owning package | [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class PatchApplicationError(ValueError)` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 40)
- `class OutstandingApplyIntentError(PatchApplicationError)` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 44) — An earlier apply is pending or conflicted, so no accept or undo may build on the vault (K3.5; D-10 for undo).
  - `__init__(self, intents: list[dict[str, Any]], *, action: str='accept') -> None` (line 53; internal)
- `refuse_while_an_apply_is_outstanding(repository: Repository, *, action: str) -> None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 74) — Raise :class:`OutstandingApplyIntentError` while an intent is pending or conflicted.
- `class CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 83)
- `class PatchApplyResult` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 103)
- `apply_accepted_items(root: Path, patch_id: str, item_ids: list[str] | None=None, *, clock: Clock | None=None) -> PatchApplyResult` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 108) — Accept a dependency-closed set of proposal items as one logical transaction.
- `applied_content_learning_object_ids(items: list[dict[str, Any]]) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 280) — The learning objects whose LO or blueprint content an applied closure changed.
- `recalibrate_applied_content(vault_after: LoadedVault, repository: Repository, items: list[dict[str, Any]], *, clock: Clock | None) -> None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 298) — Stamp the recalibration boundary at an apply that changed LO or blueprint content.
- `compute_target_hash(vault: LoadedVault, item_type: str, entity_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 326) — Content hash of the current on-vault target entity (§8.2 expected_target_hash).
- `reject_applied_items(root: Path, patch_id: str, item_ids: list[str] | None=None, *, clock: Clock | None=None) -> int` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 393)
- `compile_proposal_item(vault: LoadedVault, item: dict[str, Any], *, facet_authority: authority.ProposalAuthority | None=None) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 430) — Compile one proposal item against ``vault`` (the staging vault at apply).

### Module constants

- `LEARNABLE_MAP_ITEM_TYPES` ([src/learnloop/content/proposals/patches.py](../../../../../../../src/learnloop/content/proposals/patches.py), line 37)
- `_LINK_RELATIONS` ([src/learnloop/content/proposals/patches.py](../../../../../../../src/learnloop/content/proposals/patches.py), line 472)

## Internal implementation anchors

- `_ask_span_support(vault: LoadedVault, repository: Repository, patch_id: str, item_ids: list[str] | None, clock: Clock | None) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 137) — Each facet item's span-support verdict, asked before the vault lock, by input hash (review F1).
- `_apply_accepted_locked(vault: LoadedVault, repository: Repository, patch_id: str, item_ids: list[str] | None, clock: Clock | None, *, span_verdicts: Mapping[str, Mapping[str, Any]] | None=None) -> PatchApplyResult` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 181)
- `_accept_time_rechecks(vault: LoadedVault, repository: Repository, ordered_items: list[dict[str, Any]]) -> None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 356)
- `_noop_apply(root: Path, clock: Clock | None) -> None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 475)
- `_compile_provenance_link(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 479) — `provenance_link` create: insert a supporting entity_source_links row (§10.3).
- `_compile_notation_mapping(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 532) — `notation_mapping` create: append a contextual notation equivalence (§10.2).
- `_compile_source_conflict(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 574) — `source_conflict` create: persist an OPEN two-sided conflict (§10.2).
- `_refuse_learnable_on_legacy(vault: LoadedVault, item_type: str, entity_id: str) -> None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 619) — Bootstrap evidence refusal (§8.2 enforcement 2, knowledge-model §12.7).
- `_compile_facet(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any], *, facet_authority: authority.ProposalAuthority | None=None) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 634) — A facet create or update, through the meaning-authority chokepoint.
- `_held_for_confirm(item: dict[str, Any], entity_id: str, before: dict[str, Any] | None, data: dict[str, Any], payload: dict[str, Any], verdict: authority.MeaningVerdict, contributed: tuple[authority.Contribution, ...], facet_authority: authority.ProposalAuthority) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 720) — A reword with no explanatory support, held for the owner's one-tap confirm (owner, 2026-10-13).
- `_facet_version(vault: LoadedVault, item: dict[str, Any], entity_id: str, data: dict[str, Any], *, sources: list[dict[str, Any]] | None=None, span_support: dict[str, Any] | None=None) -> tuple[dict[str, Any], dict[str, Any] | None]` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 778) — A write that changes an existing facet's meaning becomes a facet version.
- `_compile_task_blueprint(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 843)
- `_proposal_apply_order(item: dict[str, Any]) -> tuple[int, int, str]` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 875)
- `_proposal_origin(repository: Repository, patch_id: str) -> str` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 898)
- `_compile_concept(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 911)
- `_compile_concept_edge(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 927)
- `_compile_learning_object(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 962)
- `_upsert_learning_object_with_concept(root: Path, data: dict[str, Any], *, auto_create_concept: bool, clock: Clock | None) -> Path` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 995)
- `_concept_from_learning_object(data: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1008)
- `_compile_practice_item(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1029)
- `_reject_unregistered_facets(vault: LoadedVault, entity_id: str, data: dict[str, Any]) -> None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1082) — Generated-item facet gate (knowledge-model §3.2, mirrors the probe gate).
- `_compile_rubric(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1131)
- `_compile_error_type(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1150)
- `_compile_deactivate(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1169)
- `_compile_concept_edge_deactivate(vault: LoadedVault, item: dict[str, Any], payload: dict[str, Any]) -> CompiledPatch` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1192) — Retire a concept edge: accepting removes it from relations.yaml.
- `_apply_reject_side_effect(vault: LoadedVault, repository: Repository, item: dict[str, Any], *, origin: str, clock: Clock | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1216)
- `_revert_deactivate_side_effect(vault: LoadedVault, repository: Repository, item: dict[str, Any], payload: dict[str, Any], entity_id: str, *, origin: str, now: str, clock: Clock | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1303) — Revert an applied ``deactivate``.
- `_concept_revert_blockers(vault: LoadedVault, concept_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1350)
- `_normalize_rubric_payload(payload: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1382)
- `_entity_id(item: dict[str, Any], payload: dict[str, Any], default: str | None=None) -> str` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1390)
- `_default_edge_id(payload: dict[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1397)
- `_edge_by_id(vault: LoadedVault, edge_id: str) -> Any | None` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1406)
- `_event_type(operation: str) -> str` ([source](../../../../../../../src/learnloop/content/proposals/patches.py), line 1413)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `PatchApplicationError`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `refuse_while_an_apply_is_outstanding`; statically calls `refuse_while_an_apply_is_outstanding`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `PatchApplicationError`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `PatchApplicationError`, `_proposal_apply_order`, `compile_proposal_item`, `recalibrate_applied_content`; statically calls `PatchApplicationError`, `_proposal_apply_order`, `compile_proposal_item`, `recalibrate_applied_content`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `compute_target_hash`; statically calls `compute_target_hash`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `PatchApplyResult`, `apply_accepted_items`, `reject_applied_items`; statically calls `apply_accepted_items`, `reject_applied_items`
- [[Reference/Modules/learnloop/content/proposals/required_method_override|learnloop.content.proposals.required_method_override]] — imports `compute_target_hash`; statically calls `compute_target_hash`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `apply_accepted_items`, `compute_target_hash`; statically calls `apply_accepted_items`, `compute_target_hash`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `apply_accepted_items`, `compute_target_hash`; statically calls `apply_accepted_items`, `compute_target_hash`
- [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] — imports `compute_target_hash`; statically calls `compute_target_hash`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `PatchApplicationError`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `OutstandingApplyIntentError`
- [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]] — imports `OutstandingApplyIntentError`, `PatchApplicationError`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `meaning_changes`; calls `meaning_changes`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `module`; calls `added_provenance`, `authority_changes`, `check_meaning_write`, `meaning_policy`, `overlay`, `source_views`, `support_entries`, `verify_registry_transition`, `write_contributions`, `written_provenance`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `ApplyTargetConflict`, `compute_dependency_closure`, `materialize_targets`, `perform_db_effects`, `stage_target_contents`; calls `compute_dependency_closure`, `materialize_targets`, `perform_db_effects`, `stage_target_contents`
- [[Reference/Modules/learnloop/content/proposals/required_method_override|learnloop.content.proposals.required_method_override]] — imports `is_override_item`, `owner_verdict_side_effect`; calls `is_override_item`, `owner_verdict_side_effect`
- [[Reference/Modules/learnloop/curriculum/curriculum_locks|learnloop.curriculum.curriculum_locks]] — imports `Operation`, `can_apply`; calls `Operation`, `can_apply`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `enabled`; calls `enabled`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`, `snake_case`; calls `new_ulid`, `snake_case`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `unregistered_facet_errors`; calls `unregistered_facet_errors`
- [[Reference/Modules/learnloop/ops/vault_lock|learnloop.ops.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `record_content_recalibration`; calls `record_content_recalibration`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `EvidenceFacet`, `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `rewrites_decided_statement`; calls `rewrites_decided_statement`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `delete_concept`, `delete_concept_edge`, `upsert_concept`, `upsert_concept_edge`, `upsert_error_type`, `upsert_facet`, `upsert_learning_object`, `upsert_practice_item`; calls `delete_concept`, `delete_concept_edge`, `upsert_concept`, `upsert_concept_edge`, `upsert_error_type`, `upsert_facet`, `upsert_learning_object`, `upsert_practice_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]], [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] and 8 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/facet_reword_confirm_helpers.py](../../../../../../../tests/facet_reword_confirm_helpers.py) — direct import
- [tests/identity_pins_helpers.py](../../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_apply_recovery.py](../../../../../../../tests/test_apply_recovery.py) — direct import
  - `test_an_accept_whose_target_changes_under_it_writes_nothing_and_rolls_back`
  - `test_an_accept_with_a_pending_intent_is_refused`
  - `test_an_undo_with_a_pending_intent_is_refused`
  - `test_keep_files_sets_the_intent_aside_and_accepts_open_again`
  - `test_the_apply_recalibrates_before_it_marks_the_intent_applied`
- [tests/test_apply_write_ahead.py](../../../../../../../tests/test_apply_write_ahead.py) — direct import
  - `test_apply_writes_entity_source_links_and_marks_intent_applied`
  - `test_dependency_closure_accepts_full_closure_in_order`
  - `test_dependency_closure_reject_prereq_blocks_dependents`
  - `test_expected_target_hash_mismatch_refuses`
  - `test_race_attempt_inserted_after_synthesis_refuses_under_lock`
  - `test_recovery_is_idempotent_and_noop_when_clean`
- [tests/test_decider_landing.py](../../../../../../../tests/test_decider_landing.py) — direct import
  - `test_a_book_carrying_the_retired_keep_local_is_asked_like_any_other`
- [tests/test_exam_protection_landing.py](../../../../../../../tests/test_exam_protection_landing.py) — direct import
  - `test_a_reword_resting_only_on_held_out_text_never_reaches_the_decider`
  - `test_the_span_support_check_never_sends_held_out_text_to_the_decider`
- [tests/test_facet_authority.py](../../../../../../../tests/test_facet_authority.py) — direct import
  - `test_a_facet_write_compiled_without_the_authority_context_is_refused`
  - `test_a_proposal_create_over_a_registered_facet_needs_explanatory_support_or_the_owners_confirm`
  - `test_the_writer_judges_a_persisted_citation_by_the_span_its_locator_names`
  - `test_the_writer_never_writes_a_reword_whose_only_support_is_unselected`
  - `test_the_writer_refuses_a_new_facet_one_of_whose_contributions_is_exam_only`
  - `test_the_writer_refuses_a_reword_citing_an_exam_override_only`
  - `test_the_writer_refuses_a_reword_supported_by_exam_and_notes_only`
- [tests/test_facet_authority_rereview.py](../../../../../../../tests/test_facet_authority_rereview.py) — direct import
  - `test_a_declared_citation_that_does_not_resolve_never_hides_the_writes_exam_ref`
  - `test_a_write_declaring_both_halves_of_a_split_unit_under_their_own_units_applies`
- [tests/test_facet_authority_review.py](../../../../../../../tests/test_facet_authority_review.py) — direct import
  - `test_a_citation_that_does_not_resolve_never_becomes_a_semantic_authority_link`
  - `test_a_citation_the_write_records_but_its_meaning_support_leaves_out_is_judged_on_its_own`
  - `test_a_malformed_meaning_support_is_refused`
  - `test_a_write_whose_meaning_support_declares_its_exam_citation_with_textbook_support_applies`
  - `test_an_empty_meaning_support_never_hides_a_writes_exam_citation`
  - `test_the_writer_never_writes_a_reword_citing_the_unselected_half_of_a_split_unit`
- [tests/test_facet_identity_ingest.py](../../../../../../../tests/test_facet_identity_ingest.py) — direct import
  - `test_append_attaches_a_new_facet_to_the_registered_one_it_restates`
- [tests/test_facet_reword_confirm.py](../../../../../../../tests/test_facet_reword_confirm.py) — direct import
  - `test_a_cited_reword_records_its_sources_on_the_facets_history`
  - `test_a_confirm_never_shows_exam_text`
  - `test_a_confirm_refuses_when_the_facets_wording_changed_since`
  - `test_a_confirm_whose_support_became_exam_material_is_refused`
  - `test_a_held_out_evaluation_unit_is_exam_material_whatever_its_members_role`
  - `test_a_notes_cited_append_reword_reaches_the_owner_as_a_confirm`
  - `test_a_pending_proposal_the_old_code_refused_becomes_a_confirm_naming_the_facet`
  - `test_a_reword_supported_only_by_a_non_explanatory_role_waits_for_confirm`
  - `test_a_title_change_needs_no_explanatory_citation_and_is_on_the_facets_history`
  - `test_a_worked_example_change_applies_with_its_source_on_the_facets_history`
  - `test_an_exam_only_change_through_a_proposal_is_refused_never_held`
  - `test_an_exam_only_create_carrying_a_registered_id_is_refused`
  - `test_an_exam_span_cited_under_the_wrong_unit_is_refused_not_held`
  - `test_an_uncited_append_reword_reaches_the_owner_as_a_confirm`
  - `test_an_uncited_reword_of_a_registered_facet_waits_for_the_owners_confirm`
  - `test_claim_definition_preconditions_and_non_goals_stay_meaning`
  - `test_confirming_keeps_what_changed_on_the_facet_since_beside_the_new_wording`
  - `test_registry_review_lists_a_pending_confirm_with_its_wording_and_sources`
- [tests/test_facet_reword_confirm_review.py](../../../../../../../tests/test_facet_reword_confirm_review.py) — direct import
  - `test_a_confirm_keeps_an_alias_added_since_when_the_reword_adds_one_too`
  - `test_a_confirm_keeps_error_signatures_and_repairs_changed_since`
  - `test_a_confirm_refuses_a_conflicting_change_it_cannot_merge`
  - `test_with_the_kill_switch_an_unsupported_change_is_refused_at_accept_not_held`
- [tests/test_facet_reword_paths.py](../../../../../../../tests/test_facet_reword_paths.py) — direct import
  - `test_a_cited_facet_reword_records_its_spans_in_the_facets_provenance`
  - `test_a_reword_after_a_reword_undoes_in_order_with_server_versions`
  - `test_a_stale_version_on_an_unchanged_meaning_keeps_the_current_version_and_the_undo`
  - `test_an_append_facet_restructure_applies_as_a_facet_version_with_undo`
  - `test_an_append_facet_restructure_refuses_when_the_facet_changed_since`
  - `test_an_interrupted_reword_undo_records_the_verdict_once`
  - `test_an_oversized_incoming_version_is_ignored_and_every_undo_still_applies`
  - `test_an_uncited_facet_reword_waits_for_the_owners_confirm`
  - `test_undoing_a_reword_appends_the_owners_verdict_to_the_judgment_ledger`
- [tests/test_facet_rewords.py](../../../../../../../tests/test_facet_rewords.py) — direct import
  - `test_a_growth_only_update_is_not_a_version`
  - `test_a_reword_undo_refuses_after_a_later_edit`
  - `test_rewording_an_evidenced_facet_records_a_version_and_its_undo_restores_the_old_wording`
  - `test_the_facet_inspector_shows_the_version_history_and_undoes_a_reword`
- [tests/test_facet_span_support.py](../../../../../../../tests/test_facet_span_support.py) — direct import
  - `test_keeping_a_card_that_went_stale_is_no_label`
- [tests/test_generated_item_gate.py](../../../../../../../tests/test_generated_item_gate.py) — direct import
  - `test_legacy_vault_allows_unregistered_facet`
  - `test_registered_facet_accepted`
  - `test_unregistered_facet_rejected`
- [tests/test_graph_edit_proposals.py](../../../../../../../tests/test_graph_edit_proposals.py) — direct import
  - `test_accept_concept_edge_deactivate_removes_edge`
  - `test_reject_after_apply_restores_concept_edge`
  - `test_resolve_edge_direction_retire_removes_and_can_restore`
- [tests/test_graph_nomination_ingest.py](../../../../../../../tests/test_graph_nomination_ingest.py) — direct import
  - `test_kill_switch_never_reuses_a_nominated_bootstrap_cached_before_the_fix`
- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_goal_population_handler_generates_and_applies_practice`
- [tests/test_method_phrasing_report.py](../../../../../../../tests/test_method_phrasing_report.py) — direct import
  - `test_f3_a_repair_refuses_a_rubric_edited_before_acceptance`
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
- [tests/test_required_method_reopened.py](../../../../../../../tests/test_required_method_reopened.py) — direct import
  - `test_f15_a_generated_update_that_rewrites_a_judged_source_statement_is_refused`
  - `test_f15_an_owner_edit_of_a_pending_update_cannot_rewrite_the_statement_either`
  - `test_f16_a_generated_items_override_is_ledgered_and_the_write_is_idempotent`
- [tests/test_rerun_proposals.py](../../../../../../../tests/test_rerun_proposals.py) — direct import
  - `test_a_retry_after_an_apply_failure_applies_the_proposal_it_persisted`
- [tests/test_sidecar_contract.py](../../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_sidecar_reject_accepted_concept_reports_reference_blocker`
- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — direct import
  - `test_conflict_accept_creates_open_row_reject_creates_none`
  - `test_post_append_near_duplicate_is_aliased_at_mint_and_never_auto_merged`
  - `test_specialized_side_effects_recover_idempotently`
- [tests/test_source_set_synthesis.py](../../../../../../../tests/test_source_set_synthesis.py) — direct import
  - `test_cached_generation_resume_creates_goal_without_new_model_calls`
  - `test_cached_generation_resumes_apply_after_failure_without_new_model_calls`
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

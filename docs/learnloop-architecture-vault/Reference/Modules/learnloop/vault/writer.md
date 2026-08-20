---
title: "learnloop.vault.writer"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/writer.py"
source_paths:
  - "src/learnloop/vault/writer.py"
source_commit: "a6c3391bee0c4732249b52d238aa1660b1a3042e"
source_commit_timestamp: "2026-07-28T01:49:30-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.vault.writer module"
  - "src/learnloop/vault/writer.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.writer`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps writer behavior inside its owning package, [[Reference/Modules/learnloop/vault/_package|learnloop.vault]]. Its public surface centers on `VaultWriterError`, `upsert_concept`, `delete_concept`, `upsert_concept_edge`, `delete_concept_edge`, `upsert_learning_object`, `upsert_practice_item`, `upsert_error_type` and 2 more public symbols.

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py) |
| Source lines | 481 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a6c3391bee0c4732249b52d238aa1660b1a3042e` |
| Commit timestamp | `2026-07-28T01:49:30-04:00` |

## Public API

- `class VaultWriterError(ValueError)` ([source](../../../../../../src/learnloop/vault/writer.py), line 25)
- `upsert_concept(root: Path, concept_id: str, payload: Concept | dict[str, Any], *, clock: Clock | None=None) -> Path` ([source](../../../../../../src/learnloop/vault/writer.py), line 126)
- `delete_concept(root: Path, concept_id: str) -> Path | None` ([source](../../../../../../src/learnloop/vault/writer.py), line 154)
- `upsert_concept_edge(root: Path, payload: ConceptEdge | dict[str, Any], *, clock: Clock | None=None) -> Path` ([source](../../../../../../src/learnloop/vault/writer.py), line 168)
- `delete_concept_edge(root: Path, edge_id: str) -> Path | None` ([source](../../../../../../src/learnloop/vault/writer.py), line 196)
- `upsert_learning_object(root: Path, payload: LearningObject | dict[str, Any], *, clock: Clock | None=None) -> Path` ([source](../../../../../../src/learnloop/vault/writer.py), line 211)
- `upsert_practice_item(root: Path, payload: PracticeItem | dict[str, Any], *, clock: Clock | None=None, loaded_vault: LoadedVault | None=None) -> Path` ([source](../../../../../../src/learnloop/vault/writer.py), line 241)
- `upsert_error_type(root: Path, payload: ErrorType | dict[str, Any], *, clock: Clock | None=None) -> Path` ([source](../../../../../../src/learnloop/vault/writer.py), line 281)
- `upsert_facet(root: Path, payload: EvidenceFacet | dict[str, Any], *, clock: Clock | None=None) -> Path` ([source](../../../../../../src/learnloop/vault/writer.py), line 330) — Create or update a canonical facet in facets.yaml (knowledge-model §3.2).
- `upsert_source_set(root: Path, payload: SourceSet | dict[str, Any], *, clock: Clock | None=None) -> Path` ([source](../../../../../../src/learnloop/vault/writer.py), line 388) — Create or update a source set in sources/source_sets.yaml (§4.3).

### Module constants

- `CONCEPT_ORDER` ([src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py), line 29)
- `EDGE_ORDER` ([src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py), line 39)
- `LEARNING_OBJECT_ORDER` ([src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py), line 49)
- `PRACTICE_ITEM_ORDER` ([src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py), line 69)
- `ERROR_TYPE_ORDER` ([src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py), line 113)
- `FACET_ORDER` ([src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py), line 309)
- `SOURCE_SET_ORDER` ([src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py), line 377)

## Internal implementation anchors

- `_payload(value: BaseModel | dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/vault/writer.py), line 423)
- `_mapping(value: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/vault/writer.py), line 429)
- `_read_yaml_or(path: Path, default: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/vault/writer.py), line 437)
- `_merge_entity(existing: dict[str, Any], incoming: dict[str, Any], order: list[str], *, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/vault/writer.py), line 443)
- `_list_index_by_id(items: list[Any], entity_id: str) -> int | None` ([source](../../../../../../src/learnloop/vault/writer.py), line 464)
- `_locate_entity_path(root: Path, folder: str, entity_id: str) -> Path | None` ([source](../../../../../../src/learnloop/vault/writer.py), line 471)
- `_ensure_subject_path(paths: VaultPaths, subject_id: str, target_path: Path) -> None` ([source](../../../../../../src/learnloop/vault/writer.py), line 476)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/cli/source_set|learnloop.cli.source_set]] — imports `upsert_source_set`; statically calls `upsert_source_set`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `upsert_source_set`; statically calls `upsert_source_set`
- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `upsert_source_set`; statically calls `upsert_source_set`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `VaultWriterError`, `delete_concept`, `delete_concept_edge`, `upsert_concept`, `upsert_concept_edge`, `upsert_error_type`, `upsert_facet`, `upsert_learning_object`, `upsert_practice_item`; statically calls `delete_concept`, `delete_concept_edge`, `upsert_concept`, `upsert_concept_edge`, `upsert_error_type`, `upsert_facet`, `upsert_learning_object`, `upsert_practice_item`
- [[Reference/Modules/learnloop/content/sources/source_deletion|learnloop.content.sources.source_deletion]] — imports `upsert_source_set`; statically calls `upsert_source_set`
- [[Reference/Modules/learnloop/curriculum/rung_backfill|learnloop.curriculum.rung_backfill]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] — imports `upsert_concept`, `upsert_learning_object`, `upsert_practice_item`; statically calls `upsert_concept`, `upsert_learning_object`, `upsert_practice_item`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `upsert_source_set`; statically calls `upsert_source_set`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/vault/facet_fingerprint|learnloop.vault.facet_fingerprint]] — imports `semantic_fingerprint`; calls `semantic_fingerprint`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Concept`, `ConceptEdge`, `ErrorType`, `EvidenceFacet`, `LearningObject`, `LoadedVault`, `PracticeItem`, `SourceSet`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `write_yaml`; calls `read_yaml`, `write_yaml`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]], [[Reference/Modules/learnloop/cli/source_set|learnloop.cli.source_set]], [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]], [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]], [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] and 11 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/helpers.py](../../../../../../tests/helpers.py) — direct import
- [tests/test_activity_substrate.py](../../../../../../tests/test_activity_substrate.py) — direct import
- [tests/test_assessment_enforcement.py](../../../../../../tests/test_assessment_enforcement.py) — direct import
- [tests/test_build_study_map_routing.py](../../../../../../tests/test_build_study_map_routing.py) — direct import
- [tests/test_calibration.py](../../../../../../tests/test_calibration.py) — direct import
- [tests/test_causal_cold_outcomes.py](../../../../../../tests/test_causal_cold_outcomes.py) — direct import
- [tests/test_causal_factor_deferral.py](../../../../../../tests/test_causal_factor_deferral.py) — direct import
- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
- [tests/test_certification_cold_probe.py](../../../../../../tests/test_certification_cold_probe.py) — direct import
  - `test_probe_prefers_the_whole_task_item_that_covers_integration`
  - `test_shared_surface_group_makes_the_certificate_unmeasurable`
- [tests/test_characterization_assessment_exam.py](../../../../../../tests/test_characterization_assessment_exam.py) — direct import
- [tests/test_cli_json.py](../../../../../../tests/test_cli_json.py) — direct import
  - `test_misconception_gate_backfill_json_contract`
- [tests/test_coldness_receipt.py](../../../../../../tests/test_coldness_receipt.py) — direct import
- [tests/test_controller_cutover.py](../../../../../../tests/test_controller_cutover.py) — direct import
- [tests/test_cross_seam_exposure.py](../../../../../../tests/test_cross_seam_exposure.py) — direct import
- [tests/test_diagnostic_gate.py](../../../../../../tests/test_diagnostic_gate.py) — direct import
- [tests/test_diagnostic_probe_freshness.py](../../../../../../tests/test_diagnostic_probe_freshness.py) — direct import
- [tests/test_dual_authority_administration.py](../../../../../../tests/test_dual_authority_administration.py) — direct import
- [tests/test_e2e_local.py](../../../../../../tests/test_e2e_local.py) — direct import
- [tests/test_exam_pool.py](../../../../../../tests/test_exam_pool.py) — direct import
- [tests/test_exam_seeding.py](../../../../../../tests/test_exam_seeding.py) — direct import
- [tests/test_exam_session.py](../../../../../../tests/test_exam_session.py) — direct import
- [tests/test_facet_diagnostics_v03.py](../../../../../../tests/test_facet_diagnostics_v03.py) — direct import
  - `test_tiny_authored_facet_share_does_not_earn_per_facet_coverage`
- [tests/test_facet_registry_v2.py](../../../../../../tests/test_facet_registry_v2.py) — direct import
  - `test_upsert_facet_promotes_v1_registry_to_v2`
- [tests/test_followup_diagnostic_selection.py](../../../../../../tests/test_followup_diagnostic_selection.py) — direct import
- [tests/test_goal_decay_projection.py](../../../../../../tests/test_goal_decay_projection.py) — direct import
- [tests/test_goal_frontier.py](../../../../../../tests/test_goal_frontier.py) — direct import
- [tests/test_grade_resolution_pipeline.py](../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_exam_answer_dual_writes_assessment_grade`
- [tests/test_graph_edit_proposals.py](../../../../../../tests/test_graph_edit_proposals.py) — direct import
- [tests/test_guided_redo.py](../../../../../../tests/test_guided_redo.py) — direct import
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_the_certification_cold_probe_selects_an_instrument_as_its_held_out_item`
- [tests/test_inventory_merge_parallel.py](../../../../../../tests/test_inventory_merge_parallel.py) — direct import
  - `test_synthesis_gather_folds_merged_group_once_with_member_fallback`
- [tests/test_irt_difficulty.py](../../../../../../tests/test_irt_difficulty.py) — direct import
  - `test_difficulty_source_round_trips_through_the_writer`
- [tests/test_irt_end_to_end.py](../../../../../../tests/test_irt_end_to_end.py) — direct import
- [tests/test_item_authoring.py](../../../../../../tests/test_item_authoring.py) — direct import
  - `test_retire_item_reuses_loaded_vault_and_clears_serving_backdoors`
- [tests/test_patch_applier.py](../../../../../../tests/test_patch_applier.py) — direct import
  - `test_reject_accepted_concept_create_blocks_when_referenced`
- [tests/test_patch_compiler.py](../../../../../../tests/test_patch_compiler.py) — direct import
  - `test_compile_concept_edge_update_preserves_existing_endpoints`
- [tests/test_post_attempt_pipeline.py](../../../../../../tests/test_post_attempt_pipeline.py) — direct import
- [tests/test_probe_audit.py](../../../../../../tests/test_probe_audit.py) — direct import
- [tests/test_probe_block_end.py](../../../../../../tests/test_probe_block_end.py) — direct import
- [tests/test_probe_eig.py](../../../../../../tests/test_probe_eig.py) — direct import
- [tests/test_probe_episodes.py](../../../../../../tests/test_probe_episodes.py) — direct import
- [tests/test_probe_instance_generation.py](../../../../../../tests/test_probe_instance_generation.py) — direct import
- [tests/test_probe_llm_instances.py](../../../../../../tests/test_probe_llm_instances.py) — direct import
- [tests/test_probe_longform_families.py](../../../../../../tests/test_probe_longform_families.py) — direct import
- [tests/test_probe_orchestration_remainder.py](../../../../../../tests/test_probe_orchestration_remainder.py) — direct import
  - `test_session_cap_blocks_further_probe_serving`
- [tests/test_probe_policy.py](../../../../../../tests/test_probe_policy.py) — direct import
- [tests/test_probe_pool_empty.py](../../../../../../tests/test_probe_pool_empty.py) — direct import
- [tests/test_probe_predictive_eig.py](../../../../../../tests/test_probe_predictive_eig.py) — direct import
- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — direct import
- [tests/test_probe_surface_mint.py](../../../../../../tests/test_probe_surface_mint.py) — direct import
  - `test_mint_refuses_a_surface_group_the_learner_has_seen`
- [tests/test_repair_splice.py](../../../../../../tests/test_repair_splice.py) — direct import
- [tests/test_scheduler_golden.py](../../../../../../tests/test_scheduler_golden.py) — direct import
- [tests/test_scheduler_probe_eig.py](../../../../../../tests/test_scheduler_probe_eig.py) — direct import
  - `test_probe_eig_uses_prospective_familiarity_discount`
- [tests/test_show.py](../../../../../../tests/test_show.py) — direct import
  - `test_show_inspects_every_deterministic_id`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_missing_diagnostic_receipt_fails_closed_and_keeps_recovery_key`
  - `test_sidecar_inspect_concept_and_resolve_lo_concept_references`
  - `test_sidecar_reject_accepted_concept_reports_reference_blocker`
- [tests/test_sidecar_teach_back.py](../../../../../../tests/test_sidecar_teach_back.py) — direct import
- [tests/test_sidecar_tutor_qa.py](../../../../../../tests/test_sidecar_tutor_qa.py) — direct import
  - `test_sidecar_ask_is_rejected_during_teach_back`
- [tests/test_sim_probe_validation.py](../../../../../../tests/test_sim_probe_validation.py) — direct import
- [tests/test_source_append.py](../../../../../../tests/test_source_append.py) — direct import
  - `test_n_sources_append_linear_inventory_and_bounded_context`
  - `test_post_append_near_duplicate_is_aliased_at_mint_and_never_auto_merged`
- [tests/test_source_deletion.py](../../../../../../tests/test_source_deletion.py) — direct import
  - `test_delete_drops_the_source_from_its_collections`
- [tests/test_source_set_synthesis.py](../../../../../../tests/test_source_set_synthesis.py) — direct import
- [tests/test_source_sets.py](../../../../../../tests/test_source_sets.py) — direct import
  - `test_doctor_flags_source_set_issues`
  - `test_one_source_two_sets_different_roles`
  - `test_source_coverage_readiness_report`
- [tests/test_state_sync.py](../../../../../../tests/test_state_sync.py) — direct import
  - `test_state_sync_enters_probe_when_practice_item_arrives_after_learning_object`
  - `test_state_sync_no_probe_gap_for_item_less_goal_lo`
- [tests/test_subject_registry.py](../../../../../../tests/test_subject_registry.py) — direct import
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
- [tests/test_tui_practice.py](../../../../../../tests/test_tui_practice.py) — direct import
  - `test_practice_screen_uses_item_allowed_attempt_type`
- [tests/test_vault_watcher_refresh.py](../../../../../../tests/test_vault_watcher_refresh.py) — direct import
  - `test_practice_item_watch_refresh_is_incremental`
- [tests/test_vault_writer.py](../../../../../../tests/test_vault_writer.py) — direct import
  - `test_writer_preserves_unknown_keys_and_timestamps`
  - `test_writer_refuses_implicit_entity_moves`
  - `test_writer_updates_depth_rung_metadata_on_existing_practice_item`
  - `test_writer_upserts_graph_error_lo_and_practice_item`

## Modification guidance

- Make changes here when the responsibility remains writer within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

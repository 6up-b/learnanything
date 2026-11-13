---
title: "learnloop.vault.writer"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/writer.py"
source_paths:
  - "src/learnloop/vault/writer.py"
generated: true
generated_at: "2026-11-02"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps writer behavior inside its owning package, [[Reference/Modules/learnloop/vault/_package|learnloop.vault]]. Its public surface centers on `VaultWriterError`, `upsert_activity_family`, `upsert_concept`, `delete_concept`, `upsert_concept_edge`, `delete_concept_edge`, `upsert_learning_object`, `upsert_practice_item` and 4 more public symbols.

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py) |
| Source lines | 617 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class VaultWriterError(ValueError)` ([source](../../../../../../src/learnloop/vault/writer.py), line 37)
- `upsert_activity_family(root: Path, family: ActivityFamily) -> Path` ([source](../../../../../../src/learnloop/vault/writer.py), line 41) — Write authored family content; identity/history syncing belongs to substrate.
- `upsert_concept(root: Path, concept_id: str, payload: Concept | dict[str, Any], *, clock: Clock | None=None) -> Path` ([source](../../../../../../src/learnloop/vault/writer.py), line 154)
- `delete_concept(root: Path, concept_id: str) -> Path | None` ([source](../../../../../../src/learnloop/vault/writer.py), line 181)
- `upsert_concept_edge(root: Path, payload: ConceptEdge | dict[str, Any], *, clock: Clock | None=None) -> Path` ([source](../../../../../../src/learnloop/vault/writer.py), line 194)
- `delete_concept_edge(root: Path, edge_id: str) -> Path | None` ([source](../../../../../../src/learnloop/vault/writer.py), line 221)
- `upsert_learning_object(root: Path, payload: LearningObject | dict[str, Any], *, clock: Clock | None=None) -> Path` ([source](../../../../../../src/learnloop/vault/writer.py), line 235)
- `upsert_practice_item(root: Path, payload: PracticeItem | dict[str, Any], *, clock: Clock | None=None, loaded_vault: LoadedVault | None=None) -> Path` ([source](../../../../../../src/learnloop/vault/writer.py), line 265)
- `current_practice_item(root: Path, practice_item_id: str, *, loaded_vault: LoadedVault) -> PracticeItem | None` ([source](../../../../../../src/learnloop/vault/writer.py), line 310) — The item as written on disk now, parsed like the full loader.
- `upsert_error_type(root: Path, payload: ErrorType | dict[str, Any], *, clock: Clock | None=None) -> Path` ([source](../../../../../../src/learnloop/vault/writer.py), line 323)
- `upsert_facet(root: Path, payload: EvidenceFacet | dict[str, Any], *, clock: Clock | None=None) -> Path` ([source](../../../../../../src/learnloop/vault/writer.py), line 371) — Create or update a canonical facet in facets.yaml (knowledge-model §3.2).
- `upsert_source_set(root: Path, payload: SourceSet | dict[str, Any], *, clock: Clock | None=None) -> Path` ([source](../../../../../../src/learnloop/vault/writer.py), line 428) — Create or update a source set in sources/source_sets.yaml (§4.3).

### Module constants

- `CONCEPT_ORDER` ([src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py), line 56)
- `EDGE_ORDER` ([src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py), line 66)
- `LEARNING_OBJECT_ORDER` ([src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py), line 76)
- `PRACTICE_ITEM_ORDER` ([src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py), line 96)
- `ERROR_TYPE_ORDER` ([src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py), line 141)
- `FACET_ORDER` ([src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py), line 350)
- `SOURCE_SET_ORDER` ([src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py), line 417)
- `_SCOPE_READING_FIELDS` ([src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py), line 494)

## Internal implementation anchors

- `_record_exam_qualification(sqlite_path: Path, source_ids: set[str], *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/vault/writer.py), line 467) — Before a write ends these books' exam membership in the set, record their held-out signals whose role was not recorded (signals migration 204 backfilled) as exam material, so the change never releases protection they gave (``db.stores.held_out_signals``; Codex review of exam pro…
- `_scope_key(member: Any) -> tuple[Any, ...] | None` ([source](../../../../../../src/learnloop/vault/writer.py), line 497)
- `_without_reading(member: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/vault/writer.py), line 508)
- `_keep_scope_readings(existing: Any, incoming: list[Any]) -> list[Any]` ([source](../../../../../../src/learnloop/vault/writer.py), line 512) — Seal and keep the reading each member's scope names (exam protection by extraction identity).
- `_vault_paths(root: Path) -> VaultPaths` ([source](../../../../../../src/learnloop/vault/writer.py), line 552) — Paths for a registry edit; the rest of the vault does not need to be parsed.
- `_payload(value: BaseModel | dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/vault/writer.py), line 559)
- `_mapping(value: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/vault/writer.py), line 565)
- `_read_yaml_or(path: Path, default: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/vault/writer.py), line 573)
- `_merge_entity(existing: dict[str, Any], incoming: dict[str, Any], order: list[str], *, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/vault/writer.py), line 579)
- `_list_index_by_id(items: list[Any], entity_id: str) -> int | None` ([source](../../../../../../src/learnloop/vault/writer.py), line 600)
- `_locate_entity_path(root: Path, folder: str, entity_id: str) -> Path | None` ([source](../../../../../../src/learnloop/vault/writer.py), line 607)
- `_ensure_subject_path(paths: VaultPaths, subject_id: str, target_path: Path) -> None` ([source](../../../../../../src/learnloop/vault/writer.py), line 612)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/cli/source_set|learnloop.cli.source_set]] — imports `upsert_source_set`; statically calls `upsert_source_set`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `current_practice_item`, `upsert_practice_item`; statically calls `current_practice_item`, `upsert_practice_item`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `upsert_source_set`; statically calls `upsert_source_set`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `upsert_source_set`; statically calls `upsert_source_set`
- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `upsert_source_set`; statically calls `upsert_source_set`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `delete_concept`, `delete_concept_edge`, `upsert_concept`, `upsert_concept_edge`, `upsert_error_type`, `upsert_facet`, `upsert_learning_object`, `upsert_practice_item`; statically calls `delete_concept`, `delete_concept_edge`, `upsert_concept`, `upsert_concept_edge`, `upsert_error_type`, `upsert_facet`, `upsert_learning_object`, `upsert_practice_item`
- [[Reference/Modules/learnloop/content/sources/source_deletion|learnloop.content.sources.source_deletion]] — imports `upsert_source_set`; statically calls `upsert_source_set`
- [[Reference/Modules/learnloop/curriculum/rung_backfill|learnloop.curriculum.rung_backfill]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `delete_concept_edge`, `upsert_concept`, `upsert_concept_edge`, `upsert_learning_object`; statically calls `delete_concept_edge`, `upsert_concept`, `upsert_concept_edge`, `upsert_learning_object`
- [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/goals/goal_lo|learnloop.goals.goal_lo]] — imports `upsert_concept`, `upsert_learning_object`; statically calls `upsert_concept`, `upsert_learning_object`
- [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] — imports `upsert_concept`, `upsert_learning_object`, `upsert_practice_item`; statically calls `upsert_concept`, `upsert_learning_object`, `upsert_practice_item`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `upsert_activity_family`; statically calls `upsert_activity_family`
- [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `upsert_practice_item`; statically calls `upsert_practice_item`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `upsert_source_set`; statically calls `upsert_source_set`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `load_config`; calls `load_config`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/held_out_signals|learnloop.db.stores.held_out_signals]] — imports `exam_member_sources`, `qualify_unrecorded_signals`, `unqualified_signal_count`; calls `exam_member_sources`, `qualify_unrecorded_signals`, `unqualified_signal_count`
- [[Reference/Modules/learnloop/vault/facet_fingerprint|learnloop.vault.facet_fingerprint]] — imports `semantic_fingerprint`; calls `semantic_fingerprint`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_practice_item_file`, `load_vault`; calls `load_practice_item_file`, `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `ActivityFamily`, `Concept`, `ConceptEdge`, `ErrorType`, `EvidenceFacet`, `LearningObject`, `LoadedVault`, `PracticeItem`, `SourceSet`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/scope_seal|learnloop.vault.scope_seal]] — imports `scope_seal`; calls `scope_seal`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `write_yaml`, `write_yaml_atomic`; calls `read_yaml`, `write_yaml`, `write_yaml_atomic`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `pathlib`, `sqlite3`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]], [[Reference/Modules/learnloop/cli/source_set|learnloop.cli.source_set]], [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]], [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]], [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] and 18 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/causal_orchestrator_helpers.py](../../../../../../tests/causal_orchestrator_helpers.py) — direct import
- [tests/causal_p2_acceptance_helpers.py](../../../../../../tests/causal_p2_acceptance_helpers.py) — direct import
- [tests/contamination_report_helpers.py](../../../../../../tests/contamination_report_helpers.py) — direct import
- [tests/curriculum_c2b_past_papers_helpers.py](../../../../../../tests/curriculum_c2b_past_papers_helpers.py) — direct import
- [tests/deliverable_fixtures.py](../../../../../../tests/deliverable_fixtures.py) — direct import
- [tests/device_eligibility_helpers.py](../../../../../../tests/device_eligibility_helpers.py) — direct import
- [tests/e0_fakes.py](../../../../../../tests/e0_fakes.py) — direct import
- [tests/exam_pool_helpers.py](../../../../../../tests/exam_pool_helpers.py) — direct import
- [tests/exam_protection_identity_helpers.py](../../../../../../tests/exam_protection_identity_helpers.py) — direct import
- [tests/exam_protection_review_helpers.py](../../../../../../tests/exam_protection_review_helpers.py) — direct import
- [tests/exam_scope_fixtures.py](../../../../../../tests/exam_scope_fixtures.py) — direct import
- [tests/exam_seeding_helpers.py](../../../../../../tests/exam_seeding_helpers.py) — direct import
- [tests/facet_authority_helpers.py](../../../../../../tests/facet_authority_helpers.py) — direct import
- [tests/facet_authority_review_helpers.py](../../../../../../tests/facet_authority_review_helpers.py) — direct import
- [tests/figure_fixtures.py](../../../../../../tests/figure_fixtures.py) — direct import
- [tests/goal_decay_projection_helpers.py](../../../../../../tests/goal_decay_projection_helpers.py) — direct import
- [tests/helpers.py](../../../../../../tests/helpers.py) — direct import
- [tests/mcp_world.py](../../../../../../tests/mcp_world.py) — direct import
- [tests/mobile_rpc_helpers.py](../../../../../../tests/mobile_rpc_helpers.py) — direct import
- [tests/passage_cue_fakes.py](../../../../../../tests/passage_cue_fakes.py) — direct import
- [tests/pf_fakes.py](../../../../../../tests/pf_fakes.py) — direct import
- [tests/probe_block_end_helpers.py](../../../../../../tests/probe_block_end_helpers.py) — direct import
- [tests/probe_episodes_helpers.py](../../../../../../tests/probe_episodes_helpers.py) — direct import
- [tests/probe_policy_helpers.py](../../../../../../tests/probe_policy_helpers.py) — direct import
- [tests/probe_predictive_eig_helpers.py](../../../../../../tests/probe_predictive_eig_helpers.py) — direct import
- [tests/reader_cues_helpers.py](../../../../../../tests/reader_cues_helpers.py) — direct import
- [tests/reader_rw3a_landing_helpers.py](../../../../../../tests/reader_rw3a_landing_helpers.py) — direct import
- [tests/regrade_contract_replay_helpers.py](../../../../../../tests/regrade_contract_replay_helpers.py) — direct import
- [tests/required_method_authority_helpers.py](../../../../../../tests/required_method_authority_helpers.py) — direct import
- [tests/required_method_rereview_helpers.py](../../../../../../tests/required_method_rereview_helpers.py) — direct import
- [tests/required_method_round3_review_helpers.py](../../../../../../tests/required_method_round3_review_helpers.py) — direct import
- [tests/ro2_history_protection_helpers.py](../../../../../../tests/ro2_history_protection_helpers.py) — direct import
- [tests/rw5c_fixtures.py](../../../../../../tests/rw5c_fixtures.py) — direct import
- [tests/section_coverage_fixtures.py](../../../../../../tests/section_coverage_fixtures.py) — direct import
- [tests/sim_probe_validation_helpers.py](../../../../../../tests/sim_probe_validation_helpers.py) — direct import
- [tests/source_append_helpers.py](../../../../../../tests/source_append_helpers.py) — direct import
- [tests/source_retrieval_fakes.py](../../../../../../tests/source_retrieval_fakes.py) — direct import
- [tests/source_service_fakes.py](../../../../../../tests/source_service_fakes.py) — direct import
- [tests/source_set_synthesis_helpers.py](../../../../../../tests/source_set_synthesis_helpers.py) — direct import
- [tests/teach_back_helpers.py](../../../../../../tests/teach_back_helpers.py) — direct import
- [tests/test_activity_families.py](../../../../../../tests/test_activity_families.py) — direct import
  - `test_authored_family_versions`
  - `test_ensemble_source_kind_loads_and_round_trips`
  - `test_undo_does_not_revert_owner_family_revision`
- [tests/test_activity_substrate.py](../../../../../../tests/test_activity_substrate.py) — direct import
- [tests/test_ad3_relatedness.py](../../../../../../tests/test_ad3_relatedness.py) — direct import
  - `test_relatedness_proposal_reads_no_learner_or_held_out_data`
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_held_out_sentinel_never_reaches_ad_inputs`
- [tests/test_assessment_enforcement.py](../../../../../../tests/test_assessment_enforcement.py) — direct import
- [tests/test_attempt_content_state_race.py](../../../../../../tests/test_attempt_content_state_race.py) — direct import
- [tests/test_build_study_map_routing.py](../../../../../../tests/test_build_study_map_routing.py) — direct import
- [tests/test_calibration.py](../../../../../../tests/test_calibration.py) — direct import
- [tests/test_canonical_exercise_serialization.py](../../../../../../tests/test_canonical_exercise_serialization.py) — direct import
  - `test_a_pf_variant_of_a_textbook_exercise_points_at_it`
  - `test_round_trip_and_hash_independence`
- [tests/test_causal_cold_outcomes.py](../../../../../../tests/test_causal_cold_outcomes.py) — direct import
- [tests/test_causal_factor_deferral.py](../../../../../../tests/test_causal_factor_deferral.py) — direct import
- [tests/test_certification_cold_probe.py](../../../../../../tests/test_certification_cold_probe.py) — direct import
  - `test_probe_prefers_the_whole_task_item_that_covers_integration`
  - `test_shared_surface_group_makes_the_certificate_unmeasurable`
- [tests/test_characterization_assessment_exam.py](../../../../../../tests/test_characterization_assessment_exam.py) — direct import
- [tests/test_cli_append_units.py](../../../../../../tests/test_cli_append_units.py) — direct import
- [tests/test_cli_json.py](../../../../../../tests/test_cli_json.py) — direct import
  - `test_misconception_gate_backfill_json_contract`
- [tests/test_coldness_receipt.py](../../../../../../tests/test_coldness_receipt.py) — direct import
- [tests/test_collection_append_units.py](../../../../../../tests/test_collection_append_units.py) — direct import
  - `test_a_wholly_new_member_keeps_the_unfiltered_append`
- [tests/test_contamination_report.py](../../../../../../tests/test_contamination_report.py) — direct import
  - `test_exam_leakage_shortlists_nearest_held_out_spans_for_the_judge`
- [tests/test_coverage_on_extract.py](../../../../../../tests/test_coverage_on_extract.py) — direct import
  - `test_the_job_rejudges_covered_los_a_new_book_joins_and_a_fresh_state_pays_nothing`
- [tests/test_cross_seam_exposure.py](../../../../../../tests/test_cross_seam_exposure.py) — direct import
- [tests/test_curriculum_c3_codex_review.py](../../../../../../tests/test_curriculum_c3_codex_review.py) — direct import
  - `test_a_syllabus_made_during_the_import_writes_nothing`
  - `test_a_unit_override_leaves_the_rest_of_the_book_practice`
  - `test_the_one_write_refuses_a_syllabus_draft`
- [tests/test_curriculum_c3_exam_scoping.py](../../../../../../tests/test_curriculum_c3_exam_scoping.py) — direct import
  - `test_a_syllabus_made_exam_during_the_call_keeps_nothing`
  - `test_gc2_a_syllabus_made_exam_after_it_was_added_is_never_sent`
- [tests/test_daily_plan_review_regressions.py](../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
  - `test_f8_out_of_range_expected_minutes_reach_the_writer_bounded`
- [tests/test_device_eligibility.py](../../../../../../tests/test_device_eligibility.py) — direct import
  - `test_a_skip_on_the_phone_rebuilds_with_the_same_filter`
- [tests/test_diagnostic_gate.py](../../../../../../tests/test_diagnostic_gate.py) — direct import
- [tests/test_diagnostic_probe_freshness.py](../../../../../../tests/test_diagnostic_probe_freshness.py) — direct import
- [tests/test_dual_authority_administration.py](../../../../../../tests/test_dual_authority_administration.py) — direct import
- [tests/test_e2e_local.py](../../../../../../tests/test_e2e_local.py) — direct import
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
- [tests/test_exam_protection_identity.py](../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_a_scope_edited_outside_the_writer_names_no_reading`
  - `test_doctor_names_a_legacy_mark_plainly`
  - `test_identity_rereview_f3_exam_membership_the_writer_adds_survives_a_hand_edit`
  - `test_identity_review_a_signal_of_unknown_reading_is_named_plainly`
  - `test_identity_review_f3_a_legacy_signal_survives_its_exam_membership_changing`
  - `test_identity_review_f3_an_unchanged_membership_records_nothing`
  - `test_the_scopes_reading_round_trips_through_the_writers`
- [tests/test_exam_session.py](../../../../../../tests/test_exam_session.py) — direct import
- [tests/test_exercise_arm.py](../../../../../../tests/test_exercise_arm.py) — direct import
  - `test_an_already_imported_exercise_is_dropped`
- [tests/test_facet_authority_review.py](../../../../../../tests/test_facet_authority_review.py) — direct import
  - `test_an_undo_never_mints_a_candidate_whose_recorded_citations_no_longer_resolve`
- [tests/test_facet_belief_successor.py](../../../../../../tests/test_facet_belief_successor.py) — direct import
- [tests/test_facet_belief_successor_derivation.py](../../../../../../tests/test_facet_belief_successor_derivation.py) — direct import
- [tests/test_facet_diagnostics_v03.py](../../../../../../tests/test_facet_diagnostics_v03.py) — direct import
  - `test_tiny_authored_facet_share_does_not_earn_per_facet_coverage`
- [tests/test_facet_identity_composition.py](../../../../../../tests/test_facet_identity_composition.py) — direct import
- [tests/test_facet_registry_v2.py](../../../../../../tests/test_facet_registry_v2.py) — direct import
  - `test_upsert_facet_promotes_v1_registry_to_v2`
- [tests/test_facet_reword_confirm.py](../../../../../../tests/test_facet_reword_confirm.py) — direct import
  - `test_a_confirm_whose_support_became_exam_material_is_refused`
- [tests/test_facet_reword_confirm_review.py](../../../../../../tests/test_facet_reword_confirm_review.py) — direct import
  - `test_a_pending_confirm_hides_a_sources_text_once_its_member_is_an_exam`
- [tests/test_family_proposals.py](../../../../../../tests/test_family_proposals.py) — direct import
  - `test_inputs_or_model_changes_do_not_reuse_paid_verdict`
  - `test_reject_identity_excludes_unrelated_pairs`
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f3_a_failed_file_write_serves_nothing_and_the_retry_goes_on`
- [tests/test_followup_diagnostic_selection.py](../../../../../../tests/test_followup_diagnostic_selection.py) — direct import
- [tests/test_goal_frontier.py](../../../../../../tests/test_goal_frontier.py) — direct import
- [tests/test_grade_resolution_pipeline.py](../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_exam_answer_dual_writes_assessment_grade`
- [tests/test_graph_edit_proposals.py](../../../../../../tests/test_graph_edit_proposals.py) — direct import
- [tests/test_graph_nomination_ingest.py](../../../../../../tests/test_graph_nomination_ingest.py) — direct import
  - `test_registry_definition_change_is_a_new_bootstrap_and_repeats_reuse`
  - `test_revalidation_reuses_paid_vectors_and_makes_no_embedding_call`
- [tests/test_guided_redo.py](../../../../../../tests/test_guided_redo.py) — direct import
- [tests/test_ih7_lesson_sources_follow_diagnosis.py](../../../../../../tests/test_ih7_lesson_sources_follow_diagnosis.py) — direct import
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_the_certification_cold_probe_selects_an_instrument_as_its_held_out_item`
- [tests/test_inventory_merge_parallel.py](../../../../../../tests/test_inventory_merge_parallel.py) — direct import
  - `test_synthesis_gather_folds_merged_group_once_with_member_fallback`
- [tests/test_irt_difficulty.py](../../../../../../tests/test_irt_difficulty.py) — direct import
  - `test_difficulty_source_round_trips_through_the_writer`
- [tests/test_irt_end_to_end.py](../../../../../../tests/test_irt_end_to_end.py) — direct import
- [tests/test_item_authoring.py](../../../../../../tests/test_item_authoring.py) — direct import
  - `test_retire_item_reuses_loaded_vault_and_clears_serving_backdoors`
- [tests/test_item_fingerprints.py](../../../../../../tests/test_item_fingerprints.py) — direct import
  - `test_a_published_item_later_used_as_the_parent_rebuilds`
- [tests/test_k1_mcp_find_sources.py](../../../../../../tests/test_k1_mcp_find_sources.py) — direct import
  - `test_a_problem_set_passage_is_not_returned_to_the_chat_host`
- [tests/test_k1_source_sets_gate.py](../../../../../../tests/test_k1_source_sets_gate.py) — direct import
  - `test_the_source_sets_write_never_leaves_a_truncated_file`
- [tests/test_knowledge_map_text_neighbors.py](../../../../../../tests/test_knowledge_map_text_neighbors.py) — direct import
- [tests/test_learner_text_gaps.py](../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_candidates_are_grounded_in_the_asking_subject`
  - `test_declared_prerequisites_and_the_shortlist_share_the_judge_budget`
- [tests/test_learner_text_gaps_review.py](../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f10_the_cycle_is_rechecked_on_the_file_inside_the_lock`
  - `test_f16_a_removed_edge_reloads_once_and_bumps_nothing`
  - `test_f4_without_a_grounded_subject_only_the_anchors_are_judged_and_nothing_is_created`
- [tests/test_method_explicit_landing.py](../../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_a_check_recorded_on_main_still_verifies_and_the_fresh_check_label_needs_a_change`
  - `test_check_me_keeps_the_sentence_whole_when_it_clips`
- [tests/test_mobile_v4_codex_review.py](../../../../../../tests/test_mobile_v4_codex_review.py) — direct import
- [tests/test_mobile_v4_reader.py](../../../../../../tests/test_mobile_v4_reader.py) — direct import
  - `test_a_reading_exam_material_covers_whole_reaches_the_phone_not_at_all`
  - `test_an_image_that_is_a_protected_books_original_is_withheld`
- [tests/test_model_grade_lane.py](../../../../../../tests/test_model_grade_lane.py) — direct import
- [tests/test_patch_applier.py](../../../../../../tests/test_patch_applier.py) — direct import
  - `test_reject_accepted_concept_create_blocks_when_referenced`
- [tests/test_patch_compiler.py](../../../../../../tests/test_patch_compiler.py) — direct import
  - `test_compile_concept_edge_update_preserves_existing_endpoints`
- [tests/test_pf_generation.py](../../../../../../tests/test_pf_generation.py) — direct import
  - `test_a_selection_whose_parent_contract_changed_is_never_published`
  - `test_an_unparseable_parent_reference_gives_a_neutral_difficulty_basis`
  - `test_every_pf_request_reaches_its_transport_as_an_isolated_turn`
  - `test_source_anchored_items_need_a_quote_verified_span_and_must_not_be_closed_book`
- [tests/test_plan_first_transport_today_quiet.py](../../../../../../tests/test_plan_first_transport_today_quiet.py) — direct import
- [tests/test_post_attempt_pipeline.py](../../../../../../tests/test_post_attempt_pipeline.py) — direct import
- [tests/test_probe_audit.py](../../../../../../tests/test_probe_audit.py) — direct import
- [tests/test_probe_instance_generation.py](../../../../../../tests/test_probe_instance_generation.py) — direct import
- [tests/test_probe_llm_instances.py](../../../../../../tests/test_probe_llm_instances.py) — direct import
- [tests/test_probe_longform_families.py](../../../../../../tests/test_probe_longform_families.py) — direct import
- [tests/test_probe_orchestration_remainder.py](../../../../../../tests/test_probe_orchestration_remainder.py) — direct import
  - `test_session_cap_blocks_further_probe_serving`
- [tests/test_probe_pool_empty.py](../../../../../../tests/test_probe_pool_empty.py) — direct import
- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — direct import
- [tests/test_probe_surface_mint.py](../../../../../../tests/test_probe_surface_mint.py) — direct import
  - `test_mint_refuses_a_surface_group_the_learner_has_seen`
- [tests/test_reader_ca5a_find_section.py](../../../../../../tests/test_reader_ca5a_find_section.py) — direct import
  - `test_a_peeked_paragraph_that_is_the_replacement_surfaces_source_is_skipped_by_the_reschedule`
- [tests/test_reader_cues.py](../../../../../../tests/test_reader_cues.py) — direct import
  - `test_exam_material_never_carries_a_cue`
- [tests/test_reader_followups_review.py](../../../../../../tests/test_reader_followups_review.py) — direct import
- [tests/test_rebuild_closed_row_answer.py](../../../../../../tests/test_rebuild_closed_row_answer.py) — direct import
- [tests/test_reference_gate_imports.py](../../../../../../tests/test_reference_gate_imports.py) — direct import
  - `test_a_historical_reader_import_resolves_to_model_answer`
- [tests/test_regrade_contract_successor.py](../../../../../../tests/test_regrade_contract_successor.py) — direct import
  - `test_a_first_grade_made_before_contracts_keeps_its_compatibility_reading`
- [tests/test_repair_splice.py](../../../../../../tests/test_repair_splice.py) — direct import
- [tests/test_required_method_reopened.py](../../../../../../tests/test_required_method_reopened.py) — direct import
  - `test_f13_when_the_graded_revision_cannot_be_rebuilt_it_needs_a_fresh_check`
- [tests/test_required_method_round3.py](../../../../../../tests/test_required_method_round3.py) — direct import
  - `test_f14_the_grader_renders_the_instruction_the_frozen_contract_presented`
- [tests/test_reread_safety.py](../../../../../../tests/test_reread_safety.py) — direct import
  - `test_redesign_a_refresh_keeps_an_exam_scoped_member_on_its_revision`
- [tests/test_router_offer_log.py](../../../../../../tests/test_router_offer_log.py) — direct import
  - `test_teach_back_readiness_is_probed_once_per_offer`
- [tests/test_router_probe_ties.py](../../../../../../tests/test_router_probe_ties.py) — direct import
  - `test_teach_back_items_are_probe_near_ties_at_the_successor`
- [tests/test_router_r2a_landing.py](../../../../../../tests/test_router_r2a_landing.py) — direct import
- [tests/test_rw5c_recheck.py](../../../../../../tests/test_rw5c_recheck.py) — direct import
  - `test_the_audit_lists_no_equation_of_a_source_held_out_after_its_check`
- [tests/test_rw5c_source_check.py](../../../../../../tests/test_rw5c_source_check.py) — direct import
  - `test_a_held_out_block_later_withholds_the_figure_and_its_check`
  - `test_a_withheld_span_is_never_read`
- [tests/test_scheduler_golden.py](../../../../../../tests/test_scheduler_golden.py) — direct import
- [tests/test_scheduler_probe_eig.py](../../../../../../tests/test_scheduler_probe_eig.py) — direct import
  - `test_probe_eig_uses_prospective_familiarity_discount`
- [tests/test_section_coverage_review.py](../../../../../../tests/test_section_coverage_review.py) — direct import
- [tests/test_show.py](../../../../../../tests/test_show.py) — direct import
  - `test_show_inspects_every_deterministic_id`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_missing_diagnostic_receipt_recovers_only_from_durable_completion`
  - `test_sidecar_inspect_concept_and_resolve_lo_concept_references`
  - `test_sidecar_reject_accepted_concept_reports_reference_blocker`
- [tests/test_sidecar_teach_back.py](../../../../../../tests/test_sidecar_teach_back.py) — direct import
- [tests/test_sidecar_tutor_qa.py](../../../../../../tests/test_sidecar_tutor_qa.py) — direct import
  - `test_sidecar_ask_is_rejected_during_teach_back`
- [tests/test_source_append.py](../../../../../../tests/test_source_append.py) — direct import
  - `test_n_sources_append_linear_inventory_and_bounded_context`
  - `test_post_append_near_duplicate_is_aliased_at_mint_and_never_auto_merged`
- [tests/test_source_deletion.py](../../../../../../tests/test_source_deletion.py) — direct import
  - `test_delete_drops_the_source_from_its_collections`
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
  - `test_a_teaching_span_stating_a_short_answer_is_withheld`
  - `test_a_unit_override_is_resolved_on_its_reading_and_an_unmarked_reimport_is_held_back_whole`
  - `test_practice_and_feedback_drop_exercise_and_solution_blocks`
- [tests/test_source_retrieval_rereview.py](../../../../../../tests/test_source_retrieval_rereview.py) — direct import
- [tests/test_source_sets.py](../../../../../../tests/test_source_sets.py) — direct import
  - `test_doctor_flags_source_set_issues`
  - `test_one_source_two_sets_different_roles`
  - `test_source_coverage_readiness_report`
- [tests/test_state_sync.py](../../../../../../tests/test_state_sync.py) — direct import
  - `test_state_sync_enters_probe_when_practice_item_arrives_after_learning_object`
  - `test_state_sync_no_probe_gap_for_item_less_goal_lo`
- [tests/test_state_sync_scheduling_race.py](../../../../../../tests/test_state_sync_scheduling_race.py) — direct import
  - `test_incremental_watch_refresh_keeps_an_attempt_committed_after_its_read`
- [tests/test_subject_registry.py](../../../../../../tests/test_subject_registry.py) — direct import
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
- [tests/test_teacher_te2log_episodes.py](../../../../../../tests/test_teacher_te2log_episodes.py) — direct import
- [tests/test_tui_practice.py](../../../../../../tests/test_tui_practice.py) — direct import
  - `test_practice_screen_uses_item_allowed_attempt_type`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
- [tests/test_ux_phase1_round2_review.py](../../../../../../tests/test_ux_phase1_round2_review.py) — direct import
- [tests/test_ux_phase1_usability_round1.py](../../../../../../tests/test_ux_phase1_usability_round1.py) — direct import
- [tests/test_ux_phase1_usability_round2.py](../../../../../../tests/test_ux_phase1_usability_round2.py) — direct import
  - `test_a_book_filed_in_a_collection_still_says_it_has_no_questions`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f5_a_method_explicit_answer_keeps_its_question_key_and_rubric_together`
  - `test_f5_historical_feedback_shows_the_frozen_question_answer_key_and_rubric`
  - `test_f9f_a_blind_regrade_keeps_the_maximum_recorded_with_it_after_the_question_changed`
  - `test_the_bundle_carries_the_question_as_it_was_given`
- [tests/test_vault_watcher_refresh.py](../../../../../../tests/test_vault_watcher_refresh.py) — direct import
  - `test_practice_item_watch_refresh_is_incremental`
- [tests/test_vault_writer.py](../../../../../../tests/test_vault_writer.py) — direct import
  - `test_registry_writers_do_not_parse_the_whole_vault`
  - `test_writer_preserves_unknown_keys_and_timestamps`
  - `test_writer_refuses_implicit_entity_moves`
  - `test_writer_updates_depth_rung_metadata_on_existing_practice_item`
  - `test_writer_upserts_graph_error_lo_and_practice_item`
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
  - `test_a_served_probe_records_its_probability_over_the_composed_queue`

## Modification guidance

- Make changes here when the responsibility remains writer within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/writer.py](../../../../../../src/learnloop/vault/writer.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

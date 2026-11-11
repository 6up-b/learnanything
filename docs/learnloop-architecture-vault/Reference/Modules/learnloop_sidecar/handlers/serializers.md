---
title: "learnloop_sidecar.handlers.serializers"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/serializers.py"
source_paths:
  - "src/learnloop_sidecar/handlers/serializers.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.serializers module"
  - "src/learnloop_sidecar/handlers/serializers.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.serializers`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps serializers behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `scheduled_item_dtos`, `scheduled_item_dto`, `scheduler_explanation_dto`, `latest_scheduler_explanation_dto`, `item_presentation`, `answered_presentation`, `practice_item_detail`, `practice_item_attempts` and 15 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/serializers.py](../../../../../../src/learnloop_sidecar/handlers/serializers.py) |
| Source lines | 1633 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `scheduled_item_dtos(vault: LoadedVault, repository: Repository, scheduled_items: list[ScheduledItem], *, now: datetime | None=None, item_states: Mapping[str, PracticeItemState] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 64) — Serialize a queue with two bulk state reads, independent of its size.
- `scheduled_item_dto(vault: LoadedVault, repository: Repository, scheduled: ScheduledItem) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 94) — Serialize one item; queue callers should use :func:`scheduled_item_dtos`.
- `scheduler_explanation_dto(scheduled: ScheduledItem) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 156)
- `latest_scheduler_explanation_dto(record: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 170)
- `item_presentation(item: PracticeItem) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 197) — Everything the learner must SEE to answer ``item``, as ONE structure.
- `answered_presentation(item: PracticeItem, contract: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 303) — The presentation of the question a recorded answer was given (method-explicit-3 review F3), for a screen that reviews that answer.
- `practice_item_detail(vault: LoadedVault, repository: Repository, practice_item_id: str, *, administer: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 335) — An item's detail.
- `practice_item_attempts(repository: Repository, practice_item_id: str, max_points: int, limit: int=10) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 510) — Recent attempts on a Practice Item, newest first — the inspector's attempt-history table.
- `learning_object_detail(vault: LoadedVault, repository: Repository, learning_object_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 534)
- `resolve_concept_id(vault: LoadedVault, reference: str) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 615) — Resolve an exact concept id or an unambiguous title/alias reference.
- `concept_reference_dto(vault: LoadedVault, reference: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 631)
- `concept_detail(vault: LoadedVault, concept_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 642)
- `attempt_detail(vault: LoadedVault, repository: Repository, attempt_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 692)
- `feedback_bundle(vault: LoadedVault, repository: Repository, attempt_id: str, *, live_record: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 832)
- `intervention_need_dto(row: dict[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1093)
- `live_grading_record(vault: LoadedVault, item: PracticeItem) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1218) — The key, criteria and maximum an ordinary regrade reads: the item as the vault holds it now and its resolved rubric (``regrade.regrade_attempt``).
- `criterion_evidence_dto(row: GradingEvidenceRecord, rubric: Rubric | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1376)
- `error_event_dto(vault: LoadedVault, row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1405)
- `mastery_before_dto(surprise: dict[str, Any], mastery_after: dict[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1423) — Reconstruct the pre-attempt mastery posterior for the Belief-update panel.
- `mastery_step_dto(repository: Repository, attempt_id: str, observed_correctness: float | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1455) — Why the posterior moved this far: the observation-weight factor chain.
- `surprise_dto(row: dict[str, Any], followup_threshold_nats: float | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1492)
- `practice_item_state_dto(repository: Repository, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1512)
- `rubric_dto(rubric: Rubric | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1528) — The resolved rubric, criteria dumped WHOLE.

### Module constants

- `_FOLLOWUP_KIND_BY_REASON` ([src/learnloop_sidecar/handlers/serializers.py](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 45)
- `PRESENTATION_BLOCK_KINDS` ([src/learnloop_sidecar/handlers/serializers.py](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 189)
- `GRADING_RECORD_SOURCES` ([src/learnloop_sidecar/handlers/serializers.py](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1162)

## Internal implementation anchors

- `_followup_kind(scheduled: ScheduledItem) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 50)
- `_scheduled_item_dto(vault: LoadedVault, scheduled: ScheduledItem, *, state: PracticeItemState | None, mastery: MasteryState | None, now: datetime | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 109)
- `_canonical_exercise_dto(repository: Repository, item: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 476)
- `_placement_active(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 504)
- `_learning_object_placement(vault: LoadedVault, repository: Repository, learning_object_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 570)
- `_learning_object_confusable_concepts(vault: LoadedVault, repository: Repository, learning_object_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 578)
- `_normalize_concept_reference(value: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 688)
- `_cold_check_result(vault: LoadedVault, repository: Repository, attempt: dict[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 729) — What the cold check this attempt just spent turned out to say.
- `_displayed_repairs(vault: LoadedVault, repository: Repository, attempt_id: str, metadata: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 826)
- `_diagnosis_status_field(repository: Repository, attempt_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1080) — Slice 1 §11: ``diagnosis_status`` when the attempt queued a diagnosis.
- `_answered_presentation_or_none(item: PracticeItem, contract: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1117) — :func:`answered_presentation`, or None when the item cannot be rendered (the screen then falls back to the item's own presentation; feedback is never refused over the question's display).
- `_grading_epochs(repository: Repository, attempt_id: str) -> list[list[GradingEvidenceRecord]]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1165) — The attempt's grading epochs in written order, the grade's current one last.
- `_epoch_recorded_max_points(repository: Repository, attempt_id: str, epoch: list[GradingEvidenceRecord]) -> int | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1185) — The maximum written WITH this epoch's grade, or None.
- `_epoch_grading_record(repository: Repository, attempt_id: str, epoch: list[GradingEvidenceRecord], live_record: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1240) — What one grading epoch stands on (UX Phase 4, round 3 F9): its cited contract, exactly; else the ``live`` content of the regrade that just ran, when this is that regrade's own response; else ``unrecorded``.
- `_grading_records(repository: Repository, attempt_id: str, live_record: Mapping[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any] | None]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1271) — (the grading record of the grade's current epoch, that of the epoch it replaced or None).
- `_answered_criteria(contract: Mapping[str, Any] | None) -> list[dict[str, Any]] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1285) — ``[{"criterion_id", "description", "points_possible"}]`` as the grading contract froze them (Codex review F5), or None without one.
- `_answered_max_points(contract: Mapping[str, Any] | None) -> int | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1306) — The grading contract's maximum score (re-review F9), or None without one.
- `_regrade_replaced_held(repository: Repository, attempt_id: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1319) — Was the grade the latest regrade replaced held for review (Codex review F6)?
- `_latest_evidence_per_criterion(rows: list[GradingEvidenceRecord]) -> list[GradingEvidenceRecord]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1355) — One live row per criterion for display: the latest grading epoch's.
- `_candidate_error_types(vault: LoadedVault, concept: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1549) — Error taxonomy the self-grade form offers per under-credited criterion.
- `_require_item(vault: LoadedVault, practice_item_id: str) -> PracticeItem` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1577)
- `_rubric_for_item(vault: LoadedVault, item: PracticeItem) -> Rubric | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1584)
- `_primary_subject(vault: LoadedVault, item: PracticeItem) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1591)
- `_due_status(scheduled: ScheduledItem, due_at: str | None, *, now: datetime | None=None) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1596)
- `_legacy_feedback_metadata(repository: Repository, attempt_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1612)
- `_rating_from_score(score: int, rubric: Rubric | None) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1624)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `answered_presentation`, `item_presentation`; statically calls `answered_presentation`, `item_presentation`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `attempt_detail`, `feedback_bundle`, `live_grading_record`, `practice_item_detail`; statically calls `attempt_detail`, `feedback_bundle`, `live_grading_record`, `practice_item_detail`
- [[Reference/Modules/learnloop_sidecar/handlers/inspector|learnloop_sidecar.handlers.inspector]] — imports `attempt_detail`, `concept_detail`, `error_event_dto`, `learning_object_detail`, `practice_item_detail`, `resolve_concept_id`; statically calls `attempt_detail`, `concept_detail`, `error_event_dto`, `learning_object_detail`, `practice_item_detail`, `resolve_concept_id`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `practice_item_detail`; statically calls `practice_item_detail`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `_due_status`, `latest_scheduler_explanation_dto`, `practice_item_detail`, `scheduled_item_dtos`, `scheduler_explanation_dto`; statically calls `_due_status`, `latest_scheduler_explanation_dto`, `practice_item_detail`, `scheduled_item_dtos`, `scheduler_explanation_dto`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `practice_item_detail`; statically calls `practice_item_detail`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `item_presentation`; statically calls `item_presentation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `attempt_graded_contract`; calls `attempt_graded_contract`
- [[Reference/Modules/learnloop/attempts/coldness_receipt|learnloop.attempts.coldness_receipt]] — imports `record_administration_snapshot`, `record_certification_administration_snapshot`; calls `record_administration_snapshot`, `record_certification_administration_snapshot`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolved_rubric`; calls `resolved_rubric`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `UNASSESSED_CRITERION_LABEL`
- [[Reference/Modules/learnloop/attempts/trace_evidence|learnloop.attempts.trace_evidence]] — imports `learner_answer_part`, `volunteered_explanation`; calls `learner_answer_part`, `volunteered_explanation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `learner_title`; calls `learner_title`
- [[Reference/Modules/learnloop/content/sources/source_refs|learnloop.content.sources.source_refs]] — imports `source_ref_display_dto`; calls `source_ref_display_dto`
- [[Reference/Modules/learnloop/curriculum/confusable_concepts|learnloop.curriculum.confusable_concepts]] — imports `learner_observed_confusable_concepts`; calls `learner_observed_confusable_concepts`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `GradingEvidenceRecord`, `MasteryState`, `PracticeItemState`, `Repository`
- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `pinned_repository_call`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `KEY_STATUS_LABELS`, `effective_key_status`; calls `effective_key_status`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `causal_episode_for_attempt`, `claim_checked_feedback`; calls `causal_episode_for_attempt`, `claim_checked_feedback`
- [[Reference/Modules/learnloop/diagnosis/guided_redo|learnloop.diagnosis.guided_redo]] — imports `guided_redo_available`; calls `guided_redo_available`
- [[Reference/Modules/learnloop/diagnosis/recurrence/display|learnloop.diagnosis.recurrence.display]] — imports `displayed_repair_suggestions`; calls `displayed_repair_suggestions`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `NOT_NEEDED`, `diagnosis_status`; calls `diagnosis_status`
- [[Reference/Modules/learnloop/grading_epochs|learnloop.grading_epochs]] — imports `ordered_epochs`; calls `ordered_epochs`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `attempt_grade_held`; calls `attempt_grade_held`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`, `contract_required_method`, `rubric_from_contract`, `snapshot_for_presentation`; calls `contract_required_method`, `rubric_from_contract`, `snapshot_for_presentation`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `display_mastery`, `sigmoid`; calls `display_mastery`, `sigmoid`
- [[Reference/Modules/learnloop/learner/mastery_step_attribution|learnloop.learner.mastery_step_attribution]] — imports `explain_mastery_step`; calls `explain_mastery_step`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `grade_held_for_review`, `unassessed_evidence_row`; calls `grade_held_for_review`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `placement_active`; calls `placement_active`
- [[Reference/Modules/learnloop/reader/source_review|learnloop.reader.source_review]] — imports `resolve_source_refs`; calls `resolve_source_refs`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `FOLLOWUP_REASONS`, `ScheduledItem`, `dominant_scheduler_reason`, `explain_practice_item`; calls `dominant_scheduler_reason`, `explain_practice_item`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `unassessed_evidence_row`; calls `unassessed_evidence_row`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `hint_equivalents_for_attempt`; calls `hint_equivalents_for_attempt`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `ErrorType`, `LoadedVault`, `PracticeItem`, `Rubric`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `method_instruction`; calls `method_instruction`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `mastery_dto`; calls `mastery_dto`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `to_camel`, `versioned`; calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/placement|learnloop_sidecar.handlers.placement]] — imports `placement_payload`; calls `placement_payload`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `json`, `logging`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]], [[Reference/Modules/learnloop_sidecar/handlers/inspector|learnloop_sidecar.handlers.inspector]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]], [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_attribution_p0.py](../../../../../../tests/test_causal_attribution_p0.py) — direct import
  - `test_learner_confirmation_resolves_factor_to_provisional_belief`
  - `test_nonconfirming_self_report_is_recorded_once_without_reprompt`
- [tests/test_causal_attribution_p1.py](../../../../../../tests/test_causal_attribution_p1.py) — direct import
  - `test_feedback_overlay_and_cli_are_receipt_checked`
- [tests/test_coldness_receipt.py](../../../../../../tests/test_coldness_receipt.py) — direct import
  - `test_detail_serve_writes_one_snapshot_for_an_active_cold_task`
- [tests/test_guided_redo.py](../../../../../../tests/test_guided_redo.py) — direct import
  - `test_feedback_reports_guided_redo_availability`
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — direct import
  - `test_feedback_bundle_carries_regrade_marker_after_regrade`
  - `test_feedback_bundle_lacks_regrade_marker_without_regrade`
- [tests/test_pfc_unverified_unassessed.py](../../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
  - `test_feedback_shows_an_unverified_criterion_as_not_assessed`
- [tests/test_reader_ca1_astra_fixes.py](../../../../../../tests/test_reader_ca1_astra_fixes.py) — direct import
  - `test_the_canonical_exercise_dto_names_the_book_by_its_learner_title`
- [tests/test_recurrence_live.py](../../../../../../tests/test_recurrence_live.py) — direct import
  - `test_a_generated_escalated_repair_is_validated_shown_like_any_repair_and_debited_once`
- [tests/test_regrade_contract_successor.py](../../../../../../tests/test_regrade_contract_successor.py) — direct import
  - `test_an_uncited_regrade_epoch_is_held_with_the_maximum_recorded_with_it`
  - `test_feedback_reads_a_reopened_regrade_from_the_contract_it_cites`
- [tests/test_required_method_round3.py](../../../../../../tests/test_required_method_round3.py) — direct import
  - `test_a_published_pf_variant_is_presented_with_the_parents_instruction`
  - `test_every_surface_renders_the_instruction_only_for_a_method_item`
  - `test_f14_a_generated_update_quoting_the_sentence_is_stored_verbatim_and_the_block_rendered`
- [tests/test_self_grade.py](../../../../../../tests/test_self_grade.py) — direct import
  - `test_practice_item_detail_displays_source_name_instead_of_id`
  - `test_practice_item_detail_lists_candidate_error_types`
- [tests/test_sidecar_item_presentation.py](../../../../../../tests/test_sidecar_item_presentation.py) — direct import
  - `test_the_exam_surface_serves_the_same_payload_as_practice`
- [tests/test_sidecar_queue_serialization.py](../../../../../../tests/test_sidecar_queue_serialization.py) — direct import
  - `test_queue_serialization_bulk_loads_state_once`
- [tests/test_sidecar_remediation_surfaces.py](../../../../../../tests/test_sidecar_remediation_surfaces.py) — direct import
  - `test_auto_primed_is_absent_when_the_ledger_did_not_force_it`
  - `test_auto_primed_reports_the_reveal_total_behind_the_reclassification`
  - `test_cold_check_result_is_null_on_an_ordinary_attempt`
  - `test_cold_check_result_reports_the_span_and_the_claim`
  - `test_the_primed_repair_attempt_gets_no_cold_check_result`
- [tests/test_sidecar_serializer_snapshot.py](../../../../../../tests/test_sidecar_serializer_snapshot.py) — direct import
  - `test_queue_practice_and_reader_wire_snapshots`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_a_regrade_shows_one_rubric_row_per_criterion`
  - `test_an_ordinary_answer_carries_no_answered_presentation`
  - `test_f5_a_method_explicit_answer_keeps_its_question_key_and_rubric_together`
  - `test_f5_an_answer_with_no_contract_is_unrecorded`
  - `test_f5_historical_feedback_shows_the_frozen_question_answer_key_and_rubric`
  - `test_f6_an_ordinary_regrade_history_was_not_held`
  - `test_f6_the_regrade_history_says_the_grade_it_replaced_was_held`
  - `test_f8_frozen_criteria_keep_their_original_ids_through_serialization`
  - `test_f9_a_regrade_outside_the_screen_is_the_current_grade_and_unrecorded`
  - `test_f9_an_answer_not_regraded_keeps_the_key_and_maximum_it_was_graded_under`
  - `test_f9f_a_blind_regrade_keeps_the_maximum_recorded_with_it_after_the_question_changed`
  - `test_f9g_a_contract_cited_epoch_stays_exact_whatever_was_served_since`
  - `test_the_bundle_carries_the_learners_own_answer_apart_from_the_volunteered_line`
  - `test_the_bundle_carries_the_question_as_it_was_given`
  - `test_the_bundle_says_when_a_grade_is_held_for_review`
- [tests/test_ux_phase4_landing.py](../../../../../../tests/test_ux_phase4_landing.py) — direct import
  - `test_a_held_grade_resolves_nothing_until_a_contest_regrade_releases_it`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/serializers.py](../../../../../../src/learnloop_sidecar/handlers/serializers.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

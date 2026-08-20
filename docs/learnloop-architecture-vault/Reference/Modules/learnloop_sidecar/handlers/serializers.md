---
title: "learnloop_sidecar.handlers.serializers"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/serializers.py"
source_paths:
  - "src/learnloop_sidecar/handlers/serializers.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps serializers behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `scheduled_item_dtos`, `scheduled_item_dto`, `scheduler_explanation_dto`, `latest_scheduler_explanation_dto`, `item_presentation`, `practice_item_detail`, `practice_item_attempts`, `learning_object_detail` and 13 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/serializers.py](../../../../../../src/learnloop_sidecar/handlers/serializers.py) |
| Source lines | 1154 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `scheduled_item_dtos(vault: LoadedVault, repository: Repository, scheduled_items: list[ScheduledItem]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 61) — Serialize a queue with two bulk state reads, independent of its size.
- `scheduled_item_dto(vault: LoadedVault, repository: Repository, scheduled: ScheduledItem) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 81) — Serialize one item; queue callers should use :func:`scheduled_item_dtos`.
- `scheduler_explanation_dto(scheduled: ScheduledItem) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 140)
- `latest_scheduler_explanation_dto(record: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 154)
- `item_presentation(item: PracticeItem) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 180) — Everything the learner must SEE to answer ``item``, as ONE structure.
- `practice_item_detail(vault: LoadedVault, repository: Repository, practice_item_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 276)
- `practice_item_attempts(repository: Repository, practice_item_id: str, max_points: int, limit: int=10) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 402) — Recent attempts on a Practice Item, newest first — the inspector's attempt-history table.
- `learning_object_detail(vault: LoadedVault, repository: Repository, learning_object_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 426)
- `resolve_concept_id(vault: LoadedVault, reference: str) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 496) — Resolve an exact concept id or an unambiguous title/alias reference.
- `concept_reference_dto(vault: LoadedVault, reference: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 512)
- `concept_detail(vault: LoadedVault, concept_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 523)
- `attempt_detail(vault: LoadedVault, repository: Repository, attempt_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 573)
- `feedback_bundle(vault: LoadedVault, repository: Repository, attempt_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 706)
- `intervention_need_dto(row: dict[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 883)
- `criterion_evidence_dto(row: GradingEvidenceRecord, rubric: Rubric | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 907)
- `error_event_dto(vault: LoadedVault, row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 927)
- `mastery_before_dto(surprise: dict[str, Any], mastery_after: dict[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 945) — Reconstruct the pre-attempt mastery posterior for the Belief-update panel.
- `mastery_step_dto(repository: Repository, attempt_id: str, observed_correctness: float | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 977) — Why the posterior moved this far: the observation-weight factor chain.
- `surprise_dto(row: dict[str, Any], followup_threshold_nats: float | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1014)
- `practice_item_state_dto(repository: Repository, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1034)
- `rubric_dto(rubric: Rubric | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1050) — The resolved rubric, criteria dumped WHOLE.

### Module constants

- `_FOLLOWUP_KIND_BY_REASON` ([src/learnloop_sidecar/handlers/serializers.py](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 43)
- `PRESENTATION_BLOCK_KINDS` ([src/learnloop_sidecar/handlers/serializers.py](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 173)

## Internal implementation anchors

- `_followup_kind(scheduled: ScheduledItem) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 48)
- `_scheduled_item_dto(vault: LoadedVault, scheduled: ScheduledItem, *, state: PracticeItemState | None, mastery: MasteryState | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 96)
- `_learning_object_confusable_concepts(vault: LoadedVault, repository: Repository, learning_object_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 459)
- `_normalize_concept_reference(value: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 569)
- `_cold_check_result(vault: LoadedVault, repository: Repository, attempt: dict[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 610) — What the cold check this attempt just spent turned out to say.
- `_candidate_error_types(vault: LoadedVault, concept: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1071) — Error taxonomy the self-grade form offers per under-credited criterion.
- `_require_item(vault: LoadedVault, practice_item_id: str) -> PracticeItem` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1099)
- `_rubric_for_item(vault: LoadedVault, item: PracticeItem) -> Rubric | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1106)
- `_primary_subject(vault: LoadedVault, item: PracticeItem) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1113)
- `_due_status(scheduled: ScheduledItem, due_at: str | None) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1118)
- `_legacy_feedback_metadata(repository: Repository, attempt_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1133)
- `_rating_from_score(score: int, rubric: Rubric | None) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/serializers.py), line 1145)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `item_presentation`; statically calls `item_presentation`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `attempt_detail`, `feedback_bundle`, `practice_item_detail`; statically calls `attempt_detail`, `feedback_bundle`, `practice_item_detail`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]] — imports `item_presentation`; statically calls `item_presentation`
- [[Reference/Modules/learnloop_sidecar/handlers/inspector|learnloop_sidecar.handlers.inspector]] — imports `attempt_detail`, `concept_detail`, `error_event_dto`, `learning_object_detail`, `practice_item_detail`, `resolve_concept_id`; statically calls `attempt_detail`, `concept_detail`, `error_event_dto`, `learning_object_detail`, `practice_item_detail`, `resolve_concept_id`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `practice_item_detail`, `scheduled_item_dtos`; statically calls `practice_item_detail`, `scheduled_item_dtos`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `latest_scheduler_explanation_dto`, `practice_item_detail`, `scheduled_item_dtos`, `scheduler_explanation_dto`; statically calls `latest_scheduler_explanation_dto`, `practice_item_detail`, `scheduled_item_dtos`, `scheduler_explanation_dto`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `practice_item_detail`; statically calls `practice_item_detail`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/coldness_receipt|learnloop.attempts.coldness_receipt]] — imports `record_administration_snapshot`, `record_certification_administration_snapshot`; calls `record_administration_snapshot`, `record_certification_administration_snapshot`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolved_rubric`; calls `resolved_rubric`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/content/sources/source_refs|learnloop.content.sources.source_refs]] — imports `source_ref_display_dto`; calls `source_ref_display_dto`
- [[Reference/Modules/learnloop/curriculum/confusable_concepts|learnloop.curriculum.confusable_concepts]] — imports `learner_observed_confusable_concepts`; calls `learner_observed_confusable_concepts`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `GradingEvidenceRecord`, `MasteryState`, `PracticeItemState`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `causal_episode_for_attempt`, `claim_checked_feedback`; calls `causal_episode_for_attempt`, `claim_checked_feedback`
- [[Reference/Modules/learnloop/diagnosis/guided_redo|learnloop.diagnosis.guided_redo]] — imports `guided_redo_available`; calls `guided_redo_available`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `KM_ALGORITHM_VERSION`, `snapshot_for_presentation`; calls `snapshot_for_presentation`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `display_mastery`, `sigmoid`; calls `display_mastery`, `sigmoid`
- [[Reference/Modules/learnloop/learner/mastery_step_attribution|learnloop.learner.mastery_step_attribution]] — imports `explain_mastery_step`; calls `explain_mastery_step`
- [[Reference/Modules/learnloop/reader/source_review|learnloop.reader.source_review]] — imports `resolve_source_refs`; calls `resolve_source_refs`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `FOLLOWUP_REASONS`, `ScheduledItem`, `dominant_scheduler_reason`, `explain_practice_item`; calls `dominant_scheduler_reason`, `explain_practice_item`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `hint_equivalents_for_attempt`; calls `hint_equivalents_for_attempt`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `ErrorType`, `LearningObject`, `LoadedVault`, `PracticeItem`, `Rubric`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `mastery_dto`; calls `mastery_dto`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `to_camel`, `versioned`; calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `logging`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]], [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]], [[Reference/Modules/learnloop_sidecar/handlers/inspector|learnloop_sidecar.handlers.inspector]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] and 2 more.

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

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/serializers.py](../../../../../../src/learnloop_sidecar/handlers/serializers.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

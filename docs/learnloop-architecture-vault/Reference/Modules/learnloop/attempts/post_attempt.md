---
title: "learnloop.attempts.post_attempt"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/post_attempt.py"
source_paths:
  - "src/learnloop/attempts/post_attempt.py"
source_commit: "workspace/uncommitted @ HEAD efd894886714472c5495a6a6b87e97e8a774701a"
source_commit_timestamp: "2026-11-04T00:19:09-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.post_attempt module"
  - "src/learnloop/attempts/post_attempt.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.post_attempt`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.post_attempt` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: One post-attempt pipeline for every attempt-recording door.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/post_attempt.py](../../../../../../src/learnloop/attempts/post_attempt.py) |
| Source lines | 456 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD efd894886714472c5495a6a6b87e97e8a774701a` |
| Commit timestamp | `2026-11-04T00:19:09-05:00` |

## Public API

- `class CompletionRouteUnknown(RuntimeError)` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 59) — A pending completion does not record which probe episode it belongs to.
- `class PostAttemptOutcome` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 68)
  - `inserted(self) -> bool` (line 76; public) — Did the follow-up evaluation insert queue work or mint a need?
- `run_post_attempt_pipeline(vault: LoadedVault, repository: Repository, *, result: Any, purpose: str='practice', session_id: str | None=None, self_grade: Any=None, ai_client: Any=None, available_minutes: int | None=None, suppress_insertion_reason: str | None=None, followup_surface: str | None=None, clock: Clock | None=None) -> PostAttemptOutcome` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 89) — Complete one applied attempt; a completed attempt is not completed again.
- `probe_route(repository: Repository, result: Any, *, episode_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 323) — The learner route for an attempt applied under ``episode_id``.
- `persist_attempt_feedback_metadata(repository: Repository, result: Any, self_grade: Any=None, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 342) — Persist the grade's feedback/repair metadata for later surfaces.
- `run_exam_sitting_pipeline(vault: LoadedVault, repository: Repository, *, results: list[Any], intervention_cap: int=EXAM_SITTING_INTERVENTION_CAP, followup_surface: str | None=None, clock: Clock | None=None) -> list[PostAttemptOutcome]` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 374) — Run the pipeline for every attempt an exam sitting just applied.
- `committed_submission_result(repository: Repository, submission_id: str | None) -> Any` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 438) — The saved result of the attempt a submission id already committed.

### Module constants

- `EXAM_SITTING_INTERVENTION_CAP` ([src/learnloop/attempts/post_attempt.py](../../../../../../src/learnloop/attempts/post_attempt.py), line 55)
- `EXAM_SITTING_CAP_REASON` ([src/learnloop/attempts/post_attempt.py](../../../../../../src/learnloop/attempts/post_attempt.py), line 56)

## Internal implementation anchors

- `_open_followup_workflow(vault: LoadedVault, repository: Repository, *, result: Any, surface: str | None, session_id: str | None, purpose: str, applied_episode: Any, clock: Clock | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 217) — FG1: the workflow that owns this miss, or None (the predecessor's path).
- `_shadow_diagnosis_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 253)
- `_applied_probe_episode_id(vault: LoadedVault, repository: Repository, result: Any, work: dict[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 257) — The probe episode the attempt was applied under.
- `_record_normalization_inputs(vault: LoadedVault, repository: Repository, *, result: Any, self_grade: Any, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 281) — Write what normalization and follow-up evaluation read back.
- `_defers_to_block_end(repository: Repository, result: Any, episode: Any) -> bool` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 310) — Is this a diagnostic submission inside a block that is still measuring?

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `run_exam_sitting_pipeline`; statically calls `run_exam_sitting_pipeline`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `committed_submission_result`, `run_post_attempt_pipeline`; statically calls `committed_submission_result`, `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `committed_submission_result`, `run_post_attempt_pipeline`; statically calls `committed_submission_result`, `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `CompletionRouteUnknown`, `probe_route`, `run_post_attempt_pipeline`; statically calls `probe_route`, `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `run_post_attempt_pipeline`; statically calls `run_post_attempt_pipeline`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AttemptResult`
- [[Reference/Modules/learnloop/attempts/completion_lock|learnloop.attempts.completion_lock]] — imports `attempt_completion_lock`; calls `attempt_completion_lock`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `FollowupDecision`, `attempt_followup_grade`, `enqueue_post_attempt_diagnosis`, `enqueue_post_attempt_learner_text`, `evaluate_attempt_intervention_followup`, `normalize_and_resolve_attempt`; calls `attempt_followup_grade`, `enqueue_post_attempt_diagnosis`, `enqueue_post_attempt_learner_text`, `evaluate_attempt_intervention_followup`, `normalize_and_resolve_attempt`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `SERVING_SURFACE`, `generate_and_serve_on`; calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/followup_serve/queue|learnloop.followup_serve.queue]] — imports `enqueue_workflow`; calls `enqueue_workflow`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `WORKFLOW_OWNS_REASON`, `open_for_attempt`, `probe_answered`; calls `open_for_attempt`, `probe_answered`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `schedule_certification_cold_probes`; calls `schedule_certification_cold_probes`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `attempt_grade_held`; calls `attempt_grade_held`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `GRADE_HELD_FOR_REVIEW`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `servable_open_episode`; calls `servable_open_episode`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]], [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]], [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/followup_serve_helpers.py](../../../../../../tests/followup_serve_helpers.py) — direct import
- [tests/split_live_helpers.py](../../../../../../tests/split_live_helpers.py) — direct import
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
- [tests/test_attempt_completion.py](../../../../../../tests/test_attempt_completion.py) — direct import
  - `test_block_closing_diagnostic_answer_keeps_grader_provenance`
  - `test_committed_model_grade_keeps_its_provenance_through_recovery`
  - `test_completion_lock_contention_raises_busy`
  - `test_concurrent_completions_normalize_an_attempt_once`
  - `test_pending_completion_without_its_episode_is_not_resumed`
  - `test_pipeline_keeps_one_hypothesis_version_with_grader_provenance`
  - `test_resumed_completion_routes_to_the_episode_the_attempt_was_applied_under`
  - `test_resumed_diagnostic_completion_evaluates_followups_after_its_episode_ended`
- [tests/test_attempt_write_order.py](../../../../../../tests/test_attempt_write_order.py) — direct import
  - `test_canonical_attempt_write_order_is_receipt_grade_evidence_state_then_post`
- [tests/test_coldness_receipt.py](../../../../../../tests/test_coldness_receipt.py) — direct import
- [tests/test_collection_dataset.py](../../../../../../tests/test_collection_dataset.py) — direct import
  - `test_exact_offer_survives_refresh_recovery_and_dataset_export`
- [tests/test_diagnosis_pipeline.py](../../../../../../tests/test_diagnosis_pipeline.py) — direct import
  - `test_completion_resume_enqueues_the_diagnosis_once`
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f6_a_crash_after_the_diagnosis_ended_is_recovered_by_next`
  - `test_f6_a_crash_right_after_a_probe_answer_has_settled_its_workflow`
  - `test_f6_a_crash_right_after_completion_still_has_the_job`
  - `test_f6_a_shadow_vault_has_its_workflows_job_at_once`
  - `test_f6_startup_recovery_needs_no_click`
- [tests/test_followup_journey.py](../../../../../../tests/test_followup_journey.py) — direct import
- [tests/test_followup_workflow.py](../../../../../../tests/test_followup_workflow.py) — direct import
  - `test_a_practice_lane_fallback_runs_the_predecessors_chooser_once`
  - `test_an_exam_sitting_records_eligibility_inside_its_cap`
- [tests/test_forecast_receipts.py](../../../../../../tests/test_forecast_receipts.py) — direct import
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_f5_an_adjudication_releases_the_follow_up_suppression`
- [tests/test_learner_text_gaps_composition.py](../../../../../../tests/test_learner_text_gaps_composition.py) — direct import
- [tests/test_learner_text_gaps_review.py](../../../../../../tests/test_learner_text_gaps_review.py) — direct import
- [tests/test_post_attempt_pipeline.py](../../../../../../tests/test_post_attempt_pipeline.py) — direct import
  - `test_exam_sitting_cap_processes_worst_first_and_suppresses_the_rest`
  - `test_exam_sitting_pipeline_survives_a_failing_attempt`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_recovery_normalizes_with_the_configured_grading_provider`
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_tui_empty_stuck_probe_answer_keeps_feedback_deferred`
- [tests/test_stuck_prompt_composition.py](../../../../../../tests/test_stuck_prompt_composition.py) — direct import

## Modification guidance

- Change post attempt policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/post_attempt.py](../../../../../../src/learnloop/attempts/post_attempt.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

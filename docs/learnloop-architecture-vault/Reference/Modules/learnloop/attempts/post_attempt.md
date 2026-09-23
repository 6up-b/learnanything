---
title: "learnloop.attempts.post_attempt"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/post_attempt.py"
source_paths:
  - "src/learnloop/attempts/post_attempt.py"
source_commit: "18e074a6f785e305c513ab1ebcfcfb0b253342db"
source_commit_timestamp: "2026-09-23T12:51:27-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
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
| Source lines | 342 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `18e074a6f785e305c513ab1ebcfcfb0b253342db` |
| Commit timestamp | `2026-09-23T12:51:27-04:00` |

## Public API

- `class CompletionRouteUnknown(RuntimeError)` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 49) — A pending completion does not record which probe episode it belongs to.
- `class PostAttemptOutcome` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 58)
  - `inserted(self) -> bool` (line 64; public) — Did the follow-up evaluation insert queue work or mint a need?
- `run_post_attempt_pipeline(vault: LoadedVault, repository: Repository, *, result: Any, purpose: str='practice', session_id: str | None=None, self_grade: Any=None, ai_client: Any=None, available_minutes: int | None=None, suppress_insertion_reason: str | None=None, clock: Clock | None=None) -> PostAttemptOutcome` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 73) — Complete one applied attempt; a completed attempt is not completed again.
- `probe_route(repository: Repository, result: Any, *, episode_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 211) — The learner route for an attempt applied under ``episode_id``.
- `persist_attempt_feedback_metadata(repository: Repository, result: Any, self_grade: Any=None, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 230) — Persist the grade's feedback/repair metadata for later surfaces.
- `run_exam_sitting_pipeline(vault: LoadedVault, repository: Repository, *, results: list[Any], intervention_cap: int=EXAM_SITTING_INTERVENTION_CAP, clock: Clock | None=None) -> list[PostAttemptOutcome]` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 262) — Run the pipeline for every attempt an exam sitting just applied.
- `committed_submission_result(repository: Repository, submission_id: str | None) -> Any` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 324) — The saved result of the attempt a submission id already committed.

### Module constants

- `EXAM_SITTING_INTERVENTION_CAP` ([src/learnloop/attempts/post_attempt.py](../../../../../../src/learnloop/attempts/post_attempt.py), line 45)
- `EXAM_SITTING_CAP_REASON` ([src/learnloop/attempts/post_attempt.py](../../../../../../src/learnloop/attempts/post_attempt.py), line 46)

## Internal implementation anchors

- `_applied_probe_episode_id(repository: Repository, result: Any, work: dict[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 149) — The probe episode the attempt was applied under.
- `_record_normalization_inputs(vault: LoadedVault, repository: Repository, *, result: Any, self_grade: Any, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 169) — Write what normalization and follow-up evaluation read back.
- `_defers_to_block_end(repository: Repository, result: Any, episode: Any) -> bool` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 198) — Is this a diagnostic submission inside a block that is still measuring?

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
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `FollowupDecision`, `evaluate_attempt_intervention_followup`, `normalize_and_resolve_attempt`; calls `evaluate_attempt_intervention_followup`, `normalize_and_resolve_attempt`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `schedule_certification_cold_probes`; calls `schedule_certification_cold_probes`
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
- [tests/test_post_attempt_pipeline.py](../../../../../../tests/test_post_attempt_pipeline.py) — direct import
  - `test_exam_sitting_cap_processes_worst_first_and_suppresses_the_rest`
  - `test_exam_sitting_pipeline_survives_a_failing_attempt`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_recovery_normalizes_with_the_configured_grading_provider`

## Modification guidance

- Change post attempt policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/post_attempt.py](../../../../../../src/learnloop/attempts/post_attempt.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

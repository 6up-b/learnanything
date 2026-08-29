---
title: "learnloop.goals.exam_session"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/exam_session.py"
source_paths:
  - "src/learnloop/goals/exam_session.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.goals"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.goals.exam_session module"
  - "src/learnloop/goals/exam_session.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.exam_session`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.exam_session` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Exam session: one sitting of a goal's held-out practice exam.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/exam_session.py](../../../../../../src/learnloop/goals/exam_session.py) |
| Source lines | 704 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ExamSessionError(ValueError)` ([source](../../../../../../src/learnloop/goals/exam_session.py), line 49)
- `start_exam(vault: LoadedVault, repository: Repository, goal_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/exam_session.py), line 100) — Open an exam session for a goal, freezing predictions first.
- `queue_exam_answer(vault: LoadedVault, repository: Repository, session_id: str, practice_item_id: str, *, answer_md: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/exam_session.py), line 178) — Persist a final learner answer before its grade exists.
- `record_exam_answer(vault: LoadedVault, repository: Repository, session_id: str, practice_item_id: str, *, answer_md: str, resolved_grade: ResolvedGrade, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/exam_session.py), line 240) — Store one graded answer on the session (no mastery writes yet).
- `finish_exam(vault: LoadedVault, repository: Repository, session_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/exam_session.py), line 349) — Apply every answered item as an ``exam_attempt`` and persist the report.
- `exam_report(vault: LoadedVault, repository: Repository, session_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/exam_session.py), line 532) — Return the persisted report (completed) or a live progress view.
- `exam_availability(vault: LoadedVault, repository: Repository, goal: Goal, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/exam_session.py), line 554) — Policy data for whether a goal's exam is "due" — not enforced.

### Module constants

- `_WINDOW_DAYS` ([src/learnloop/goals/exam_session.py](../../../../../../src/learnloop/goals/exam_session.py), line 46)
- `_ATTRIBUTION_FIELD_NAMES` ([src/learnloop/goals/exam_session.py](../../../../../../src/learnloop/goals/exam_session.py), line 655)

## Internal implementation anchors

- `_goal(vault: LoadedVault, goal_id: str) -> Goal` ([source](../../../../../../src/learnloop/goals/exam_session.py), line 53)
- `_predicted_correctness_for_item(vault: LoadedVault, repository: Repository, item) -> float` ([source](../../../../../../src/learnloop/goals/exam_session.py), line 65)
- `_facet_projection_snapshot(vault, item, projection_by_key, scope, target_recall) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/exam_session.py), line 83)
- `_dual_write_exam_grade(vault: LoadedVault, repository: Repository, *, item: Any, rubric: Any, max_points: int, answer_md: str, resolved_grade: ResolvedGrade, attempt_id: str, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/goals/exam_session.py), line 298) — P0.2 dual-write for exam answers (§4.1, §7.2).
- `_compute_report(vault: LoadedVault, repository: Repository, session, goal) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/exam_session.py), line 455)
- `_session_view(repository: Repository, session_id: str, *, already_started: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/exam_session.py), line 599)
- `_grade_to_dict(grade: ResolvedGrade) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/exam_session.py), line 619) — Serialize a resolved grade LOSSLESSLY into ``exam_answers.grade_json``.
- `_attribution_from_dict(payload: dict[str, Any]) -> GradeAttribution` ([source](../../../../../../src/learnloop/goals/exam_session.py), line 660) — Rebuild one attribution, tolerating legacy six-field rows.
- `_grade_from_dict(payload: dict[str, Any]) -> ResolvedGrade` ([source](../../../../../../src/learnloop/goals/exam_session.py), line 683)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `ExamSessionError`, `exam_availability`, `exam_report`, `finish_exam`, `record_exam_answer`, `start_exam`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `ExamSessionError`, `exam_availability`, `exam_report`, `finish_exam`, `queue_exam_answer`, `record_exam_answer`, `start_exam`; statically calls `ExamSessionError`, `exam_availability`, `finish_exam`, `queue_exam_answer`, `record_exam_answer`, `start_exam`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`; calls `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `record_grade_dual_write`; calls `record_grade_dual_write`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `run_exam_sitting_pipeline`; calls `run_exam_sitting_pipeline`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `FrozenClock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `FrozenClock`, `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `release_exam_pool`; calls `release_exam_pool`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `goal_report`, `resolve_goal_scope`; calls `goal_report`, `resolve_goal_scope`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `facet_recall_states_for_lo`; calls `facet_recall_states_for_lo`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `ability_vector`, `item_demand_vector`, `predicted_correctness_from_vectors`; calls `ability_vector`, `item_demand_vector`, `predicted_correctness_from_vectors`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Goal`, `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_characterization_assessment_exam.py](../../../../../../tests/test_characterization_assessment_exam.py) — direct import
  - `test_finish_releases_pool_and_reservation_is_blocked_only_by_attempt_history`
  - `test_predictions_are_not_refrozen_on_restart`
  - `test_predictions_frozen_at_start_with_snapshot_fields`
- [tests/test_exam_session.py](../../../../../../tests/test_exam_session.py) — direct import
  - `test_availability_in_window_near_due_date`
  - `test_availability_open_ended_goal_never_in_window_but_startable`
  - `test_exam_answer_submission_is_final_but_idempotent`
  - `test_exam_answers_certify_facet_evidence_on_canonical_vault`
  - `test_finish_is_idempotent_by_session_id`
  - `test_finish_lands_exam_attempt_evidence_with_full_mass`
  - `test_finish_releases_the_exam_pool`
  - `test_report_has_per_facet_predicted_vs_actual`
  - `test_start_is_idempotent`
  - `test_ungraded_answer_is_durable_and_blocks_finish`
- [tests/test_grade_resolution_pipeline.py](../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_exam_answer_dual_writes_assessment_grade`
- [tests/test_post_attempt_pipeline.py](../../../../../../tests/test_post_attempt_pipeline.py) — direct import
  - `test_finish_exam_failure_reaches_needs_metadata_and_hypotheses`
  - `test_finish_exam_passing_answers_do_not_mint_followup_noise`
  - `test_finish_exam_remains_idempotent_with_pipeline`
  - `test_grade_json_round_trip_is_lossless_for_every_attribution_field`
  - `test_grade_json_round_trip_tolerates_legacy_six_field_rows`
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — direct import
  - `test_exam_submit_advances_before_background_grade_finishes`
  - `test_finished_report_carries_per_item_feedback_and_repairs`

## Modification guidance

- Change exam session policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/exam_session.py](../../../../../../src/learnloop/goals/exam_session.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

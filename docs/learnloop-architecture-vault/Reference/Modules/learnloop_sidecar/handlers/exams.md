---
title: "learnloop_sidecar.handlers.exams"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/exams.py"
source_paths:
  - "src/learnloop_sidecar/handlers/exams.py"
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
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop_sidecar.handlers.exams module"
  - "src/learnloop_sidecar/handlers/exams.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.exams`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.exams` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Practice-exam endpoints: status, start, answer, finish.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/exams.py](../../../../../../src/learnloop_sidecar/handlers/exams.py) |
| Source lines | 509 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class StartExamInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 43)
- `class SubmitExamAnswerInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 47)
- `class FinishExamInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 53)
- `get_answer_calibration(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 58)
- `get_exam_status(ctx: SidecarContext, params: GoalIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 68)
- `start_exam_handler(ctx: SidecarContext, params: StartExamInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 275)
- `submit_exam_answer(ctx: SidecarContext, params: SubmitExamAnswerInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 291)
- `finish_exam_handler(ctx: SidecarContext, params: FinishExamInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 338)

### Module constants

- `_LEARNER_TRACE_FIELDS` ([src/learnloop_sidecar/handlers/exams.py](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 390)

## Internal implementation anchors

- `_session_snapshot(ctx: SidecarContext, view: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 105)
- `_grade_and_record_exam_answer(vault, repository, client, *, session_id: str, practice_item_id: str, answer_md: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 160) — Resolve one persisted answer and attach its grade idempotently.
- `_schedule_exam_answer_grading(ctx: SidecarContext, *, vault, repository, session_id: str, practice_item_id: str, answer_md: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 203)
- `_schedule_pending_exam_grading(ctx: SidecarContext, session_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 236) — Resume durable ungraded rows without delaying the exam snapshot.
- `_raise_exam_grading_error(exc: Exception) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 255)
- `_learner_repair_dto(suggestion: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 399) — The learner-facing subset of one validated repair suggestion.
- `_item_review_fields(vault, answer: dict[str, Any] | None, practice_item_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 426) — Post-sitting review payload for one exam item.
- `_report_dto(vault, repository, report: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/exams.py), line 460)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `resolved_codex_grade`; calls `resolved_codex_grade`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `GradingValidationError`, `build_grading_context`, `request_grading_proposal`, `validate_codex_grading_proposal`; calls `build_grading_context`, `request_grading_proposal`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop/goals/exam_calibration|learnloop.goals.exam_calibration]] — imports `calibration_report`; calls `calibration_report`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `reserve_exam_pool`; calls `reserve_exam_pool`
- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `ExamSessionError`, `exam_availability`, `exam_report`, `finish_exam`, `queue_exam_answer`, `record_exam_answer`, `start_exam`; calls `ExamSessionError`, `exam_availability`, `finish_exam`, `queue_exam_answer`, `record_exam_answer`, `start_exam`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `resolve_goal_scope`; calls `resolve_goal_scope`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `EmptyParams`, `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `ready_grading_provider`; calls `ready_grading_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `GoalIdInput`, `_find_goal`; calls `_find_goal`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `item_presentation`; calls `item_presentation`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — direct import
  - `test_exam_submit_advances_before_background_grade_finishes`
- [tests/test_sidecar_item_presentation.py](../../../../../../tests/test_sidecar_item_presentation.py) — direct import
  - `test_an_exam_item_deleted_from_the_vault_still_renders_rather_than_failing`
  - `test_the_exam_surface_serves_the_same_payload_as_practice`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/exams.py](../../../../../../src/learnloop_sidecar/handlers/exams.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

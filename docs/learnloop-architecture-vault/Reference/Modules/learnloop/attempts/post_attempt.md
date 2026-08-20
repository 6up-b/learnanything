---
title: "learnloop.attempts.post_attempt"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/post_attempt.py"
source_paths:
  - "src/learnloop/attempts/post_attempt.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
| Source lines | 221 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class PostAttemptOutcome` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 56)
  - `inserted(self) -> bool` (line 62; public) — Did the follow-up evaluation insert queue work or mint a need?
- `run_post_attempt_pipeline(vault: LoadedVault, repository: Repository, *, result: Any, purpose: str='practice', session_id: str | None=None, self_grade: Any=None, ai_client: Any=None, available_minutes: int | None=None, suppress_insertion_reason: str | None=None, clock: Clock | None=None) -> PostAttemptOutcome` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 71) — Run the composed post-attempt steps for one applied attempt.
- `persist_attempt_feedback_metadata(repository: Repository, result: Any, self_grade: Any=None, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 130) — Persist the grade's feedback/repair metadata for later surfaces.
- `run_exam_sitting_pipeline(vault: LoadedVault, repository: Repository, *, results: list[Any], intervention_cap: int=EXAM_SITTING_INTERVENTION_CAP, clock: Clock | None=None) -> list[PostAttemptOutcome]` ([source](../../../../../../src/learnloop/attempts/post_attempt.py), line 162) — Run the pipeline for every attempt an exam sitting just applied.

### Module constants

- `EXAM_SITTING_INTERVENTION_CAP` ([src/learnloop/attempts/post_attempt.py](../../../../../../src/learnloop/attempts/post_attempt.py), line 51)
- `EXAM_SITTING_CAP_REASON` ([src/learnloop/attempts/post_attempt.py](../../../../../../src/learnloop/attempts/post_attempt.py), line 52)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `run_exam_sitting_pipeline`; statically calls `run_exam_sitting_pipeline`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `run_post_attempt_pipeline`; statically calls `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `run_post_attempt_pipeline`; statically calls `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `run_post_attempt_pipeline`; statically calls `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `run_post_attempt_pipeline`; statically calls `run_post_attempt_pipeline`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `FollowupDecision`, `evaluate_attempt_intervention_followup`; calls `evaluate_attempt_intervention_followup`
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

- [tests/test_attempt_write_order.py](../../../../../../tests/test_attempt_write_order.py) — direct import
  - `test_canonical_attempt_write_order_is_receipt_grade_evidence_state_then_post`
- [tests/test_coldness_receipt.py](../../../../../../tests/test_coldness_receipt.py) — direct import
- [tests/test_post_attempt_pipeline.py](../../../../../../tests/test_post_attempt_pipeline.py) — direct import
  - `test_exam_sitting_cap_processes_worst_first_and_suppresses_the_rest`
  - `test_exam_sitting_pipeline_survives_a_failing_attempt`

## Modification guidance

- Change post attempt policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/post_attempt.py](../../../../../../src/learnloop/attempts/post_attempt.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

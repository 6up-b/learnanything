---
title: "learnloop_sidecar.handlers.teach_back"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/teach_back.py"
source_paths:
  - "src/learnloop_sidecar/handlers/teach_back.py"
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
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop_sidecar.handlers.teach_back module"
  - "src/learnloop_sidecar/handlers/teach_back.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.teach_back`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.teach_back` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Teach-back conversation RPCs: start, submit turn, finish (grade transcript).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/teach_back.py](../../../../../../src/learnloop_sidecar/handlers/teach_back.py) |
| Source lines | 449 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class RequestTeachBackInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 49)
- `request_teach_back(ctx: SidecarContext, params: RequestTeachBackInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 57) — Learner opt-in to a source-item teach-back: find or author the card.
- `class StartTeachBackInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 107)
- `class SubmitTeachBackTurnInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 112)
- `start_teach_back(ctx: SidecarContext, params: StartTeachBackInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 122) — Plan the conversation and persist an empty state into the checkpoint.
- `submit_teach_back_turn(ctx: SidecarContext, params: SubmitTeachBackTurnInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 163) — Record a learner turn, then either ask the next question or finish.
- `filter_unready_teach_back_items(vault, queue: list, *, grading_provider_override: str | None=None) -> list` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 239) — Drop teach_back items from a built queue when AI is unavailable for them.

## Internal implementation anchors

- `_finish(ctx: SidecarContext, vault, repository, params: SubmitTeachBackTurnInput, state: TeachBackState) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 265)
- `_existing_attempt_payload(vault, repository, state: TeachBackState, attempt_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 367) — Response for a finish retry whose attempt was already recorded.
- `_require_teach_back_item(vault, practice_item_id: str)` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 416)
- `_load_state(repository, session_id: str, practice_item_id: str) -> TeachBackState | None` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 428)
- `_persist_state(repository, session_id: str, state: TeachBackState) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 439)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `filter_unready_teach_back_items`; statically calls `filter_unready_teach_back_items`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `filter_unready_teach_back_items`; statically calls `filter_unready_teach_back_items`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AttemptValidationError`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `run_post_attempt_pipeline`; calls `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `TEACH_BACK_PRACTICE_MODE`, `TeachBackError`, `TeachBackState`, `asked_criterion_ids`, `begin_teach_back`, `ensure_teach_back_item`, `finish_teach_back`, `next_question`, `plan_followups`, `record_answer`, `render_transcript_md`; calls `TeachBackError`, `TeachBackState`, `asked_criterion_ids`, `begin_teach_back`, `ensure_teach_back_item`, `finish_teach_back`, `next_question`, `plan_followups`, `record_answer`, `render_transcript_md`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`, `teach_back_envelope`; calls `teach_back_envelope`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `MANUAL_PROVIDER`, `provider_label`, `ready_grading_provider`, `ready_teach_back_provider`; calls `provider_label`, `ready_grading_provider`, `ready_teach_back_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `_log_attempt_recorded`; calls `_log_attempt_recorded`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `SessionCheckpointInput`, `_require_open_session`, `patch_checkpoint`; calls `SessionCheckpointInput`, `_require_open_session`, `patch_checkpoint`
- [[Reference/Modules/learnloop_sidecar/logging|learnloop_sidecar.logging]] — imports `log_event`; calls `log_event`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]], [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_desktop_rpc_contract.py](../../../../../../tests/test_desktop_rpc_contract.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_adjudication.py](../../../../../../tests/test_sidecar_adjudication.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_goals.py](../../../../../../tests/test_sidecar_goals.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_item_presentation.py](../../../../../../tests/test_sidecar_item_presentation.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_measurement.py](../../../../../../tests/test_sidecar_measurement.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_trace_and_clarification.py](../../../../../../tests/test_sidecar_trace_and_clarification.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/teach_back.py](../../../../../../src/learnloop_sidecar/handlers/teach_back.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

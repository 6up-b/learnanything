---
title: "learnloop_sidecar.handlers.teach_back"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/teach_back.py"
source_paths:
  - "src/learnloop_sidecar/handlers/teach_back.py"
source_commit: "workspace/uncommitted @ HEAD 79532f7149b554db05a40c2ae1dbde68d9efec5a"
source_commit_timestamp: "2026-11-09T16:01:49-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
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
| Source lines | 565 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 79532f7149b554db05a40c2ae1dbde68d9efec5a` |
| Commit timestamp | `2026-11-09T16:01:49-05:00` |

## Public API

- `class RequestTeachBackInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 60)
- `request_teach_back(ctx: SidecarContext, params: RequestTeachBackInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 68) — Learner opt-in to a source-item teach-back: find or author the card.
- `class StartTeachBackInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 118)
- `class SubmitTeachBackTurnInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 125)
- `start_teach_back(ctx: SidecarContext, params: StartTeachBackInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 138) — Plan the conversation and persist an empty state into the checkpoint.
- `submit_teach_back_turn(ctx: SidecarContext, params: SubmitTeachBackTurnInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 190) — Record a learner turn, then either ask the next question or finish.
- `filter_unready_teach_back_items(vault, queue: list, *, grading_provider_override: str | None=None, offerable: Callable[[], bool] | None=None) -> list` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 276) — Drop teach_back items from a built queue when AI is unavailable for them.
- `teach_back_offerable(vault, *, grading_provider_override: str | None=None) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 310) — Both halves of a teach-back are available: the naive student and an AI grader.

## Internal implementation anchors

- `_finish(ctx: SidecarContext, vault, repository, params: SubmitTeachBackTurnInput, state: TeachBackState) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 335)
- `_schedule_router_summary(vault, repository, attempt_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 443)
- `_existing_attempt_payload(vault, repository, state: TeachBackState, attempt_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 449) — Response for a finish retry whose attempt was already recorded.
- `_conversation_offer(repository, params, bound_offer: str | None) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 498) — The scheduler offer this conversation answers, validating a new one.
- `_require_teach_back_item(vault, practice_item_id: str)` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 531)
- `_load_state(repository, session_id: str, practice_item_id: str) -> TeachBackState | None` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 543)
- `_persist_state(ctx: SidecarContext, repository, session_id: str, state: TeachBackState) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/teach_back.py), line 554)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `filter_unready_teach_back_items`; statically calls `filter_unready_teach_back_items`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `TEACH_BACK_PRACTICE_MODE`, `filter_unready_teach_back_items`, `teach_back_offerable`; statically calls `filter_unready_teach_back_items`, `teach_back_offerable`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `status_as`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AttemptValidationError`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `run_post_attempt_pipeline`; calls `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop/daily_plan/router_teach_back|learnloop.daily_plan.router_teach_back]] — imports `schedule`; calls `schedule`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `TEACH_BACK_PRACTICE_MODE`, `TeachBackError`, `TeachBackState`, `asked_criterion_ids`, `begin_teach_back`, `ensure_teach_back_item`, `finish_teach_back`, `next_question`, `plan_followups`, `record_answer`, `render_transcript_md`; calls `TeachBackError`, `TeachBackState`, `asked_criterion_ids`, `begin_teach_back`, `ensure_teach_back_item`, `finish_teach_back`, `next_question`, `plan_followups`, `record_answer`, `render_transcript_md`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `presented_prompt`; calls `presented_prompt`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`, `teach_back_envelope`; calls `teach_back_envelope`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `MANUAL_PROVIDER`, `grading_source_for_provider`, `provider_label`, `ready_grading_provider`, `ready_teach_back_provider`; calls `grading_source_for_provider`, `provider_label`, `ready_grading_provider`, `ready_teach_back_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `_log_attempt_recorded`; calls `_log_attempt_recorded`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `SessionCheckpointInput`, `patch_checkpoint`, `require_owned_session`; calls `SessionCheckpointInput`, `patch_checkpoint`, `require_owned_session`
- [[Reference/Modules/learnloop_sidecar/logging|learnloop_sidecar.logging]] — imports `log_event`; calls `log_event`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `refuse_held_out_item`, `refuse_unservable_item`; calls `refuse_held_out_item`, `refuse_unservable_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]], [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_router_offer_log.py](../../../../../../tests/test_router_offer_log.py) — direct import
  - `test_a_teach_back_reopened_from_a_refreshed_list_is_one_pick`
  - `test_teach_back_readiness_is_probed_once_per_offer`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/teach_back.py](../../../../../../src/learnloop_sidecar/handlers/teach_back.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

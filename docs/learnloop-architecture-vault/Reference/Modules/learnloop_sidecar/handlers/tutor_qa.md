---
title: "learnloop_sidecar.handlers.tutor_qa"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/tutor_qa.py"
source_paths:
  - "src/learnloop_sidecar/handlers/tutor_qa.py"
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
  - "learnloop_sidecar.handlers.tutor_qa module"
  - "src/learnloop_sidecar/handlers/tutor_qa.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.tutor_qa`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.tutor_qa` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Tutor Q&A RPCs: ask, rate, save-as-note, transcript.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/tutor_qa.py](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py) |
| Source lines | 399 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class AskTutorQuestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 26)
- `class RateTutorAnswerInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 47)
- `class SaveTutorAnswerNoteInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 52)
- `class GetTutorTranscriptInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 57)
- `class PromoteTutorQuestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 65)
- `class ListQuestionQueueInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 72)
- `class ResolveQuestionEventInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 78)
- `list_question_queue(ctx: SidecarContext, params: ListQuestionQueueInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 84) — The outstanding-question queue (newest first) + the open count.
- `resolve_question_event(ctx: SidecarContext, params: ResolveQuestionEventInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 103) — Flip one question to open/resolved/dismissed (learner-owned queue state).
- `ask_tutor_question(ctx: SidecarContext, params: AskTutorQuestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 123)
- `class PreviewTutorOpeningInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 195)
- `preview_tutor_opening(ctx: SidecarContext, params: PreviewTutorOpeningInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 201) — A proactive tutor opening for a just-closed diagnostic block (§12.1).
- `rate_tutor_answer(ctx: SidecarContext, params: RateTutorAnswerInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 224)
- `save_tutor_answer_note(ctx: SidecarContext, params: SaveTutorAnswerNoteInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 232)
- `promote_tutor_question(ctx: SidecarContext, params: PromoteTutorQuestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 253) — Persist and enqueue an answered tutor turn for durable promotion.
- `get_tutor_transcript(ctx: SidecarContext, params: GetTutorTranscriptInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 354)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/tutor/question_queue|learnloop.tutor.question_queue]] — imports `QuestionQueueError`, `module`; calls `count_open_questions`, `list_question_queue`, `set_question_resolution`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `TEACH_BACK_PRACTICE_MODE`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `QuestionLimitReached`, `TutorQAError`, `ask_question`, `build_tutor_opening`, `build_tutor_qa_note`, `question_usage`; calls `ask_question`, `build_tutor_opening`, `build_tutor_qa_note`, `question_usage`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `provider_label`, `ready_tutor_qa_provider`; calls `provider_label`, `ready_tutor_qa_provider`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

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

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/tutor_qa.py](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

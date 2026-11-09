---
title: "learnloop.tutor.question_queue"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tutor/question_queue.py"
source_paths:
  - "src/learnloop/tutor/question_queue.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.tutor"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop.tutor.question_queue module"
  - "src/learnloop/tutor/question_queue.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-tutor"
---

# `learnloop.tutor.question_queue`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.tutor.question_queue` exists within [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] to own the behavior summarized by its module contract: The outstanding-question queue (spec_andymatusnotes: "a queue of outstanding questions ...

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tutor/question_queue.py](../../../../../../src/learnloop/tutor/question_queue.py) |
| Source lines | 242 |
| Owning package | [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class QuestionQueueError(ValueError)` ([source](../../../../../../src/learnloop/tutor/question_queue.py), line 25) — Invalid queue operation (unknown event id or resolution state).
- `list_question_queue(repository: Repository, *, vault: LoadedVault | None=None, resolution: str | None='open', limit: int | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/question_queue.py), line 29) — Queue rows, newest first, each carrying its promotion (if any).
- `count_open_questions(repository: Repository) -> int` ([source](../../../../../../src/learnloop/tutor/question_queue.py), line 219)
- `set_question_resolution(repository: Repository, *, question_event_id: str, resolution: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/tutor/question_queue.py), line 223) — Move one question to ``open``/``resolved``/``dismissed``; returns the row.

### Module constants

- `RESOLUTIONS` ([src/learnloop/tutor/question_queue.py](../../../../../../src/learnloop/tutor/question_queue.py), line 22)

## Internal implementation anchors

- `_source_citation(repository: Repository, event: dict[str, Any], *, vault: LoadedVault | None) -> dict[str, str | None] | None` ([source](../../../../../../src/learnloop/tutor/question_queue.py), line 92) — Best canonical teaching span for an outstanding question.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/questions|learnloop.cli.questions]] — imports `QuestionQueueError`, `list_question_queue`, `set_question_resolution`; statically calls `list_question_queue`, `set_question_resolution`
- [[Reference/Modules/learnloop/reader/reader_inquiry|learnloop.reader.reader_inquiry]] — imports `module`; statically calls `set_question_resolution`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `count_open_questions`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `QuestionQueueError`, `module`; statically calls `count_open_questions`, `list_question_queue`, `set_question_resolution`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `promotion_target_ids`; calls `promotion_target_ids`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `_source_spans`, `delivered_answer_md`; calls `_source_spans`, `delivered_answer_md`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/questions|learnloop.cli.questions]], [[Reference/Modules/learnloop/reader/reader_inquiry|learnloop.reader.reader_inquiry]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]], [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_question_queue.py](../../../../../../tests/test_question_queue.py) — direct import
  - `test_captured_questions_start_open_and_list_newest_first`
  - `test_invalid_operations_raise`
  - `test_reader_question_exposes_exact_dialogue_and_source_context`
  - `test_resolution_is_learner_owned_and_reopenable`

## Modification guidance

- Change question queue policy here when tutor owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tutor/question_queue.py](../../../../../../src/learnloop/tutor/question_queue.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

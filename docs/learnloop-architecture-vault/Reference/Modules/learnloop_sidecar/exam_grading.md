---
title: "learnloop_sidecar.exam_grading"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/exam_grading.py"
source_paths:
  - "src/learnloop_sidecar/exam_grading.py"
source_commit: "7353a4204e5cc8ca4a15010a78ac3f84b8295617"
source_commit_timestamp: "2026-09-23T12:27:35-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop_sidecar"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop_sidecar.exam_grading module"
  - "src/learnloop_sidecar/exam_grading.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.exam_grading`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.exam_grading` exists within [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] to own the behavior summarized by its module contract: In-process background grading for durable practice-exam answers.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/exam_grading.py](../../../../../src/learnloop_sidecar/exam_grading.py) |
| Source lines | 103 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7353a4204e5cc8ca4a15010a78ac3f84b8295617` |
| Commit timestamp | `2026-09-23T12:27:35-04:00` |

## Public API

- `class ExamGradingManager` ([source](../../../../../src/learnloop_sidecar/exam_grading.py), line 20) — Own daemon grading workers and make scheduling idempotent per exam item.
  - `__init__(self) -> None` (line 23; internal)
  - `submit(self, session_id: str, practice_item_id: str, work: Callable[[], None]) -> bool` (line 31; public) — Start ``work`` unless this item already has an active worker.
  - `_run(self, key: ExamGradingKey, work: Callable[[], None]) -> None` (line 59; internal)
  - `wait_for_session(self, session_id: str) -> None` (line 76; public) — Join every worker currently grading an answer in ``session_id``.
  - `pop_error(self, session_id: str, practice_item_id: str) -> Exception | None` (line 91; public)
  - `shutdown(self) -> None` (line 97; public) — Give active workers a short grace period; they are daemon threads.

### Module constants

- `LOG` ([src/learnloop_sidecar/exam_grading.py](../../../../../src/learnloop_sidecar/exam_grading.py), line 15)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `ExamGradingManager`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextvars`, `logging`, `threading`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_sidecar_exams.py](../../../../../tests/test_sidecar_exams.py) — direct import
  - `test_exam_grading_workers_run_in_the_submitting_request_context`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/exam_grading.py](../../../../../src/learnloop_sidecar/exam_grading.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.teacher.actions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/actions.py"
source_paths:
  - "src/learnloop/teacher/actions.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.teacher"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.teacher.actions module"
  - "src/learnloop/teacher/actions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.actions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.actions` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: The teacher's read actions (spec_teacher_v1 §9, §9.1, §9.2; curriculum C4's ``read_note``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/actions.py](../../../../../../src/learnloop/teacher/actions.py) |
| Source lines | 243 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ActionRefused(ValueError)` ([source](../../../../../../src/learnloop/teacher/actions.py), line 36)
  - `__init__(self, code: str, message: str) -> None` (line 37; internal)
- `caller_for(state: Any) -> Any` ([source](../../../../../../src/learnloop/teacher/actions.py), line 42)
- `run_read(vault: Any, repository: Any, state: Any, request: ActionRequestV1, *, model: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/actions.py), line 53)
- `read_source(vault: Any, repository: Any, state: Any, refs: list[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/actions.py), line 73)
- `find(vault: Any, repository: Any, state: Any, request: ActionRequestV1, *, model: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/actions.py), line 129)
- `read_history(vault: Any, repository: Any, state: Any, refs: list[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/actions.py), line 173)

### Module constants

- `_HISTORY_TEXT_CHARS` ([src/learnloop/teacher/actions.py](../../../../../../src/learnloop/teacher/actions.py), line 33)

### Explicit exports

`__all__` declares:

- `ActionRefused`
- `caller_for`
- `find`
- `read_history`
- `read_source`
- `run_read`

## Internal implementation anchors

- `_open_solution(state: Any) -> str | None` ([source](../../../../../../src/learnloop/teacher/actions.py), line 67)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `caller_for`, `module`; statically calls `caller_for`, `run_read`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] — imports `module`; calls `receipt`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `ToolArgumentsInvalid`, `request_tool`, `run_requested_tool`; calls `request_tool`, `run_requested_tool`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `attempt_protection`, `withheld_items`; calls `attempt_protection`, `withheld_items`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `CallerContext`, `PolicyRefused`; calls `CallerContext`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `Library`; calls `Library`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `admitted_recap`, `passage_teachable`, `protection_state`; calls `admitted_recap`, `passage_teachable`, `protection_state`
- [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]] — imports `ActionRequestV1`
- [[Reference/Modules/learnloop/teacher/notes|learnloop.teacher.notes]] — imports `notes_still_deliverable`, `read_note`; calls `read_note`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `span_leaks_expected`; calls `span_leaks_expected`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ih7_lesson_sources_follow_diagnosis.py](../../../../../../tests/test_ih7_lesson_sources_follow_diagnosis.py) — direct import
  - `test_over_budget_the_added_section_falls_to_the_outline_and_the_linked_one_stays_whole`
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_switching_visuals_off_hides_a_lessons_figures_and_stops_a_pending_one`

## Modification guidance

- Make changes here when the responsibility remains actions within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/actions.py](../../../../../../src/learnloop/teacher/actions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

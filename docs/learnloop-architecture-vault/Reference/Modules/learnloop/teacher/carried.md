---
title: "learnloop.teacher.carried"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/carried.py"
source_paths:
  - "src/learnloop/teacher/carried.py"
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
  - "learnloop.teacher.carried module"
  - "src/learnloop/teacher/carried.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.carried`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.carried` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: The learner's open carried questions in a lesson's brief (owner decision 2026-11-23: "carried questions: Teacher context only").

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/carried.py](../../../../../../src/learnloop/teacher/carried.py) |
| Source lines | 97 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `for_brief(repository: Any, library: Any, teachable: Callable[[Any, str, str], bool]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/carried.py), line 46) — The brief's ``carried_questions`` entry, or None when no question is open.
- `in_brief(brief: Any) -> bool` ([source](../../../../../../src/learnloop/teacher/carried.py), line 84)
- `instructions(text: str, on: bool) -> str` ([source](../../../../../../src/learnloop/teacher/carried.py), line 88)
- `prompt_version(base: str, on: bool) -> str` ([source](../../../../../../src/learnloop/teacher/carried.py), line 92)

### Module constants

- `VERSION` ([src/learnloop/teacher/carried.py](../../../../../../src/learnloop/teacher/carried.py), line 27)
- `PROMPT_SUFFIX` ([src/learnloop/teacher/carried.py](../../../../../../src/learnloop/teacher/carried.py), line 29)
- `MAX_QUESTIONS` ([src/learnloop/teacher/carried.py](../../../../../../src/learnloop/teacher/carried.py), line 31)
- `OPEN_STATES` ([src/learnloop/teacher/carried.py](../../../../../../src/learnloop/teacher/carried.py), line 33)
- `ABOUT` ([src/learnloop/teacher/carried.py](../../../../../../src/learnloop/teacher/carried.py), line 35)
- `PARAGRAPH` ([src/learnloop/teacher/carried.py](../../../../../../src/learnloop/teacher/carried.py), line 38)

### Explicit exports

`__all__` declares:

- `MAX_QUESTIONS`
- `OPEN_STATES`
- `PROMPT_SUFFIX`
- `VERSION`
- `for_brief`
- `in_brief`
- `instructions`
- `prompt_version`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `module`; statically calls `for_brief`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `in_brief`, `instructions`, `prompt_version`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `list_carried`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]], [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_teacher_carried_questions.py](../../../../../../tests/test_teacher_carried_questions.py) — direct import
  - `test_a_lesson_carries_the_learners_open_questions_with_the_passages_they_sit_beside`
  - `test_a_lesson_with_no_open_carried_question_is_unchanged`

## Modification guidance

- Make changes here when the responsibility remains carried within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/carried.py](../../../../../../src/learnloop/teacher/carried.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

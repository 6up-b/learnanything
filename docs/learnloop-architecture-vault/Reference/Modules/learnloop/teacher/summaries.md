---
title: "learnloop.teacher.summaries"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/summaries.py"
source_paths:
  - "src/learnloop/teacher/summaries.py"
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
  - "learnloop.teacher.summaries module"
  - "src/learnloop/teacher/summaries.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.summaries`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.summaries` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: Reader workbench RD9a (spec §11.1, §12.5): what a lesson window's tab and the path view's Teacher lesson row say about a lesson, read from what the lesson recorded.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/summaries.py](../../../../../../src/learnloop/teacher/summaries.py) |
| Source lines | 74 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `made_from(lesson: dict[str, Any], open_refs: dict[str, Any]) -> MadeFrom` ([source](../../../../../../src/learnloop/teacher/summaries.py), line 19) — Where a lesson came from, in the order a later fact outranks an earlier one: a suggestion's Start is the router's whatever its entry, a check's hand-off names its episode, and a typed goal is stored with entry ``learning_object`` (its goal JSON keeps the ``typed`` block).
- `lesson_summaries(vault: Any, repository: Any, *, lesson_ids: Sequence[str] | None=None, learning_object_ids: Sequence[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/summaries.py), line 35) — The lessons named (``lesson_ids``), or those on any of ``learning_object_ids``, or every lesson; newest first.

### Explicit exports

`__all__` declares:

- `MadeFrom`
- `lesson_summaries`
- `made_from`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `lesson_summaries`; statically calls `lesson_summaries`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] — imports `module`; calls `lesson`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd9a_lesson_windows.py](../../../../../../tests/test_reader_rd9a_lesson_windows.py) — direct import
  - `test_made_from_reads_the_lessons_own_record`

## Modification guidance

- Make changes here when the responsibility remains summaries within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/summaries.py](../../../../../../src/learnloop/teacher/summaries.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

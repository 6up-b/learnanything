---
title: "learnloop.notebook_runtime.lessons"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_runtime/lessons.py"
source_paths:
  - "src/learnloop/notebook_runtime/lessons.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.notebook_runtime"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.notebook_runtime.lessons module"
  - "src/learnloop/notebook_runtime/lessons.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-runtime"
---

# `learnloop.notebook_runtime.lessons`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_runtime.lessons` exists within [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] to own the behavior summarized by its module contract: A Teacher lesson whose medium is a marimo notebook (spec §11.2): where its notebook is, and its commit points.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_runtime/lessons.py](../../../../../../src/learnloop/notebook_runtime/lessons.py) |
| Source lines | 83 |
| Owning package | [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `lesson_notebook_path(vault_root: Path, lesson_id: str) -> str | None` ([source](../../../../../../src/learnloop/notebook_runtime/lessons.py), line 31) — The lesson's notebook relative to the vault (posix), or None when the lesson has none.
- `lesson_contract(source: bytes) -> dict[str, Any]` ([source](../../../../../../src/learnloop/notebook_runtime/lessons.py), line 53) — ``{"points": [{"name", "held"}], "held": [...]}`` read from the notebook's cells, in order.
- `committed_value(value: Any) -> bool` ([source](../../../../../../src/learnloop/notebook_runtime/lessons.py), line 77) — A control's value that says the learner answered (an empty form or field is not a commit).

### Module constants

- `LESSON_NOTEBOOKS` ([src/learnloop/notebook_runtime/lessons.py](../../../../../../src/learnloop/notebook_runtime/lessons.py), line 24)
- `COMMIT_PREFIX` ([src/learnloop/notebook_runtime/lessons.py](../../../../../../src/learnloop/notebook_runtime/lessons.py), line 26)
- `_LESSON_ID` ([src/learnloop/notebook_runtime/lessons.py](../../../../../../src/learnloop/notebook_runtime/lessons.py), line 28)

### Explicit exports

`__all__` declares:

- `COMMIT_PREFIX`
- `LESSON_NOTEBOOKS`
- `committed_value`
- `lesson_contract`
- `lesson_notebook_path`

## Internal implementation anchors

- `_is_cell(decorator: ast.expr) -> tuple[bool, bool]` ([source](../../../../../../src/learnloop/notebook_runtime/lessons.py), line 41) — (a marimo cell decorator, it holds the cell).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/notebook_runtime/supervisor|learnloop.notebook_runtime.supervisor]] — imports `committed_value`; statically calls `committed_value`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `lesson_notebook_path`; statically calls `lesson_notebook_path`
- [[Reference/Modules/learnloop_sidecar/handlers/notebooks|learnloop_sidecar.handlers.notebooks]] — imports `lesson_contract`, `lesson_notebook_path`; statically calls `lesson_contract`, `lesson_notebook_path`

### Repository tooling consumers

- [scripts/desk_harness/notebook.py](../../../../../../scripts/desk_harness/notebook.py); calls `lesson_contract`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `ast`, `pathlib`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/notebook_runtime/supervisor|learnloop.notebook_runtime.supervisor]], [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]], [[Reference/Modules/learnloop_sidecar/handlers/notebooks|learnloop_sidecar.handlers.notebooks]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notebook_lessons.py](../../../../../../tests/test_notebook_lessons.py) — direct import
  - `test_a_commit_is_a_value_on_a_commit_points_own_control_and_a_review_commits_nothing`
  - `test_a_lesson_opens_on_its_own_notebook_with_its_commit_points`
  - `test_a_lessons_notebook_is_its_vault_file_or_none`
  - `test_commit_points_and_held_cells_are_read_from_the_notebooks_cells`
- [tests/test_notebook_runtime_sandbox.py](../../../../../../tests/test_notebook_runtime_sandbox.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains lessons within learnloop.notebook_runtime; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_runtime/lessons.py](../../../../../../src/learnloop/notebook_runtime/lessons.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.hints.options"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/options.py"
source_paths:
  - "src/learnloop/hints/options.py"
source_commit: "e6d3c96710df3cbdb228f505cada139d72f82cda"
source_commit_timestamp: "2026-11-01T19:56:33-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.hints"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.hints.options module"
  - "src/learnloop/hints/options.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.options`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.options` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: Adaptive hints H2a: the (kind, level) options a request allows (spec §4.2, §4.5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/options.py](../../../../../../src/learnloop/hints/options.py) |
| Source lines | 198 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e6d3c96710df3cbdb228f505cada139d72f82cda` |
| Commit timestamp | `2026-11-01T19:56:33-05:00` |

## Public API

- `class Option` ([source](../../../../../../src/learnloop/hints/options.py), line 46)
  - `id(self) -> str` (line 51; public)
- `class OptionSet` ([source](../../../../../../src/learnloop/hints/options.py), line 56) — What a request may be served, and why the rest is absent.
  - `ids(self) -> list[str]` (line 75; public)
  - `has(self, kind: str, level: int | None=None) -> bool` (line 78; public)
  - `record(self) -> dict[str, Any]` (line 81; public)
- `precondition(kind: str, state: HintState) -> str | None` ([source](../../../../../../src/learnloop/hints/options.py), line 89) — Why ``kind`` cannot be offered for this state, or None.
- `build_options(state: HintState, *, request: str, answered: EarlierHint | None=None, shortcut: str | None=None, taken_level: int | None=None) -> OptionSet` ([source](../../../../../../src/learnloop/hints/options.py), line 126) — The options for one request (the caller has validated ``answered``).

### Module constants

- `FIGURE_KIND` ([src/learnloop/hints/options.py](../../../../../../src/learnloop/hints/options.py), line 41)
- `OFFERABLE` ([src/learnloop/hints/options.py](../../../../../../src/learnloop/hints/options.py), line 42)

### Explicit exports

`__all__` declares:

- `FIGURE_KIND`
- `OFFERABLE`
- `Option`
- `OptionSet`
- `build_options`
- `precondition`

## Internal implementation anchors

- `_offer(levels: tuple[int, ...], state: HintState, excluded: dict[str, str], kinds: tuple[str, ...]=OFFERABLE) -> list[Option]` ([source](../../../../../../src/learnloop/hints/options.py), line 111)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/hints/chooser|learnloop.hints.chooser]] — imports `OptionSet`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `FIGURE_KIND`, `OptionSet`, `build_options`; statically calls `build_options`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `OFFERABLE`, `Option`, `OptionSet`, `build_options`, `precondition`; statically calls `Option`, `OptionSet`, `build_options`, `precondition`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/hints/kinds|learnloop.hints.kinds]] — imports `GRAIN`, `KINDS`, `PRESS_LEVELS`, `WORKED_LEVELS`, `option_id`; calls `option_id`
- [[Reference/Modules/learnloop/hints/state|learnloop.hints.state]] — imports `EarlierHint`, `HintState`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/hints/chooser|learnloop.hints.chooser]], [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]], [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_hint_discriminating.py](../../../../../../tests/test_hint_discriminating.py) — direct import
  - `test_offered_only_with_two_open_rivals`
  - `test_on_new_work_a_new_discriminating_question_may_be_offered`
- [tests/test_hint_service.py](../../../../../../tests/test_hint_service.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains options within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/options.py](../../../../../../src/learnloop/hints/options.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

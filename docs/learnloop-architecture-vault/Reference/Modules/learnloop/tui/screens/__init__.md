---
title: "learnloop.tui.screens"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tui/screens/__init__.py"
source_paths:
  - "src/learnloop/tui/screens/__init__.py"
source_commit: "4b62bc29c46b5f2b8cabe5ac49c9959429cc3ab7"
source_commit_timestamp: "2026-05-19T19:15:00-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop.tui.screens"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.tui.screens module"
  - "src/learnloop/tui/screens/__init__.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-tui-screens"
---

# `learnloop.tui.screens`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.tui.screens` exists within [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] to own the behavior summarized by its module contract: Textual screens.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tui/screens/__init__.py](../../../../../../../src/learnloop/tui/screens/__init__.py) |
| Source lines | 1 |
| Owning package | [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `4b62bc29c46b5f2b8cabe5ac49c9959429cc3ab7` |
| Commit timestamp | `2026-05-19T19:15:00-04:00` |

## Public API

No public top-level function or class definition is declared in this file.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: none imported directly
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No direct or one-hop consumer test was found by static import analysis.

> [!caution] Test gap signal
> Treat this as a navigation signal, not proof that behavior is untested: dynamic and higher-level coverage is outside this static map. Add focused coverage when changing isolated behavior here.

## Modification guidance

- Change this file when intentionally adding or removing a package-level re-export; keep implementation logic in the owning module.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tui/screens/__init__.py](../../../../../../../src/learnloop/tui/screens/__init__.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

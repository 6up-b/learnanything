---
title: "learnloop.router_objective.trajectory"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/trajectory.py"
source_paths:
  - "src/learnloop/router_objective/trajectory.py"
source_commit: "dd62a5964ef51df8d2279346e426225c7293e452"
source_commit_timestamp: "2026-11-04T09:28:50-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router_objective.trajectory module"
  - "src/learnloop/router_objective/trajectory.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.trajectory`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.trajectory` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO0 row 12 (spec_router_objective_v1 §4): decision-to-next-state links, with censoring.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/trajectory.py](../../../../../../src/learnloop/router_objective/trajectory.py) |
| Source lines | 61 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `dd62a5964ef51df8d2279346e426225c7293e452` |
| Commit timestamp | `2026-11-04T09:28:50-05:00` |

## Public API

- `rows(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/trajectory.py), line 55) — Every decision's links, read-only.

### Module constants

- `VERSION` ([src/learnloop/router_objective/trajectory.py](../../../../../../src/learnloop/router_objective/trajectory.py), line 20)
- `TRAJECTORY_SQL` ([src/learnloop/router_objective/trajectory.py](../../../../../../src/learnloop/router_objective/trajectory.py), line 24)

### Explicit exports

`__all__` declares:

- `TRAJECTORY_SQL`
- `VERSION`
- `rows`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/router_objective/report|learnloop.router_objective.report]] — imports `module`; statically calls `rows`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/router_objective/report|learnloop.router_objective.report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro0_row12_trajectory.py](../../../../../../tests/test_ro0_row12_trajectory.py) — direct import
  - `test_the_read_runs_on_the_head_schema`

## Modification guidance

- Make changes here when the responsibility remains trajectory within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/trajectory.py](../../../../../../src/learnloop/router_objective/trajectory.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

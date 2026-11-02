---
title: "learnloop.experiments.contextual_embeddings.e1.ledger"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/e1/ledger.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/e1/ledger.py"
source_commit: "f33994399e9e5ec0063191972fdfc28c0e7c9487"
source_commit_timestamp: "2026-10-23T22:20:45-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings.e1"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.e1.ledger module"
  - "src/learnloop/experiments/contextual_embeddings/e1/ledger.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings-e1"
---

# `learnloop.experiments.contextual_embeddings.e1.ledger`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.e1.ledger` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] to own the behavior summarized by its module contract: E1's own hard-cap ledger: <= $5 across every E1 authorization (spec §8).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/e1/ledger.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/ledger.py) |
| Source lines | 90 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `f33994399e9e5ec0063191972fdfc28c0e7c9487` |
| Commit timestamp | `2026-10-23T22:20:45-04:00` |

## Public API

- `local_root(path: Path) -> Path` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/ledger.py), line 24)
- `ledger_dir(anchor: Path) -> Path` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/ledger.py), line 32) — E1's ledger directory for the fixtures-local root holding ``anchor``.
- `prior_spend(anchor: Path, *, exclude: str | None=None) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/ledger.py), line 38)
- `authorized_ledger(anchor: Path, plan_id: str, *, new_authorization: str | None=None) -> E0Ledger` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/ledger.py), line 54) — The ONE ledger of an E1 plan's authorization (``<plan_id>.ledger``).
- `budget_check(estimate: dict[str, float], prior: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/ledger.py), line 75) — Whether ``estimate`` fits E1's cumulative cap and allocations after ``prior``.

### Module constants

- `_PLAN_ID` ([src/learnloop/experiments/contextual_embeddings/e1/ledger.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/ledger.py), line 21)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/plan|learnloop.experiments.contextual_embeddings.e1.plan]] — imports `budget_check`; statically calls `budget_check`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `authorized_ledger`, `ledger_dir`, `prior_spend`; statically calls `authorized_ledger`, `ledger_dir`, `prior_spend`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/budget|learnloop.experiments.contextual_embeddings.budget]] — imports `E0Ledger`, `ledger_spend`, `seal_ledger`; calls `E0Ledger`, `ledger_spend`, `seal_ledger`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/pins|learnloop.experiments.contextual_embeddings.e1.pins]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `decimal`, `pathlib`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/plan|learnloop.experiments.contextual_embeddings.e1.plan]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e1_harness.py](../../../../../../../../tests/test_e1_harness.py) — direct import
  - `test_the_e1_ledger_is_cumulative_across_e1_plans_and_never_touches_e0`
  - `test_the_whole_pilot_with_fakes`

## Modification guidance

- Make changes here when the responsibility remains ledger within learnloop.experiments.contextual_embeddings.e1; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/e1/ledger.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/ledger.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

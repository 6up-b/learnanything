---
title: "learnloop.router.agreement"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router/agreement.py"
source_paths:
  - "src/learnloop/router/agreement.py"
source_commit: "bf51a51a9634f2570fdefe3bace585bb7506424e"
source_commit_timestamp: "2026-10-14T09:16:50-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router.agreement module"
  - "src/learnloop/router/agreement.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router"
---

# `learnloop.router.agreement`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router/_package|learnloop.router]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router.agreement` exists within [[Reference/Modules/learnloop/router/_package|learnloop.router]] to own the behavior summarized by its module contract: Router R2b: the router's decisions as rows of the Decider agreement report.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router/agreement.py](../../../../../../src/learnloop/router/agreement.py) |
| Source lines | 119 |
| Owning package | [[Reference/Modules/learnloop/router/_package|learnloop.router]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `bf51a51a9634f2570fdefe3bace585bb7506424e` |
| Commit timestamp | `2026-10-14T09:16:50-04:00` |

## Public API

- `router_agreement_rows(decisions: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router/agreement.py), line 64) — Ledger-shaped rows for every decision with logged model answers.
- `router_decision_rows_for_agreement(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router/agreement.py), line 97) — The decisions with logged model answers, from one database (none without the ledger).

### Module constants

- `TASK_CHOOSE` ([src/learnloop/router/agreement.py](../../../../../../src/learnloop/router/agreement.py), line 29)
- `TASK_SENSOR` ([src/learnloop/router/agreement.py](../../../../../../src/learnloop/router/agreement.py), line 30)
- `TASK_INTERVENE` ([src/learnloop/router/agreement.py](../../../../../../src/learnloop/router/agreement.py), line 31)
- `_FAILURE_VERDICTS` ([src/learnloop/router/agreement.py](../../../../../../src/learnloop/router/agreement.py), line 32)

### Explicit exports

`__all__` declares:

- `TASK_CHOOSE`
- `TASK_INTERVENE`
- `TASK_SENSOR`
- `router_agreement_rows`
- `router_decision_rows_for_agreement`

## Internal implementation anchors

- `_json(value: Any) -> Any` ([source](../../../../../../src/learnloop/router/agreement.py), line 35)
- `_argmax(distribution: Mapping[str, float]) -> str` ([source](../../../../../../src/learnloop/router/agreement.py), line 42)
- `_row(decision: Mapping[str, Any], *, task: str, judge: str, verdict: str, probabilities: Mapping[str, float] | None, right: tuple[str, str] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/agreement.py), line 46)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/decider|learnloop.cli.decider]] — imports `router_agreement_rows`, `router_decision_rows_for_agreement`; statically calls `router_agreement_rows`, `router_decision_rows_for_agreement`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/decider|learnloop.cli.decider]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_router_r2b_agreement.py](../../../../../../tests/test_router_r2b_agreement.py) — direct import
  - `test_a_failed_decider_is_a_fallback_in_the_report`
  - `test_the_router_decisions_feed_the_agreement_report`

## Modification guidance

- Make changes here when the responsibility remains agreement within learnloop.router; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router/agreement.py](../../../../../../src/learnloop/router/agreement.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.router_objective.objective_report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/objective_report.py"
source_paths:
  - "src/learnloop/router_objective/objective_report.py"
source_commit: "workspace/uncommitted @ HEAD 220bb12fda841f33b5a7166e8f8bdd5266a28a25"
source_commit_timestamp: "2026-11-05T04:42:23-05:00"
source_worktree_state: "modified"
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
  - "learnloop.router_objective.objective_report module"
  - "src/learnloop/router_objective/objective_report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.objective_report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.objective_report` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO4 §8.9: the objective's report, its evaluations kept apart, with counts and versioned comparators.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/objective_report.py](../../../../../../src/learnloop/router_objective/objective_report.py) |
| Source lines | 168 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 220bb12fda841f33b5a7166e8f8bdd5266a28a25` |
| Commit timestamp | `2026-11-05T04:42:23-05:00` |

## Public API

- `build(connection: Any, *, now: str, weight: Mapping[str, Any] | None=None, forecasts: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/objective_report.py), line 37) — The report over every trace (``connection`` read-only; the traces table at migration 246).
- `lines(report: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/router_objective/objective_report.py), line 137)

### Module constants

- `REPORT_VERSION` ([src/learnloop/router_objective/objective_report.py](../../../../../../src/learnloop/router_objective/objective_report.py), line 30)

### Explicit exports

`__all__` declares:

- `REPORT_VERSION`
- `build`
- `lines`

## Internal implementation anchors

- `_share(counter: Counter, total: int) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/objective_report.py), line 33)
- `_llm_favoured(row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/router_objective/objective_report.py), line 132)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `module`; statically calls `build`, `lines`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `table_present`
- [[Reference/Modules/learnloop/router_objective/forecast_resolve|learnloop.router_objective.forecast_resolve]] — imports `module`; calls `summary`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro4_codex_review.py](../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f9_the_drawn_options_forecast_is_resolved_and_reported`
- [tests/test_ro4_trace_report.py](../../../../../../tests/test_ro4_trace_report.py) — direct import
  - `test_the_first_day_report_against_the_predecessor_on_a_synthetic_vault`

## Modification guidance

- Make changes here when the responsibility remains objective report within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/objective_report.py](../../../../../../src/learnloop/router_objective/objective_report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

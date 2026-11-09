---
title: "learnloop.router_objective.tail_report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/tail_report.py"
source_paths:
  - "src/learnloop/router_objective/tail_report.py"
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
  - "learnloop.router_objective.tail_report module"
  - "src/learnloop/router_objective/tail_report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.tail_report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.tail_report` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO6 (spec_router_objective_v1 §10): the learned tail's section of ``learnloop router objective-report``.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/tail_report.py](../../../../../../src/learnloop/router_objective/tail_report.py) |
| Source lines | 200 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `build(connection: Any, vault: Any, *, now: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/tail_report.py), line 115) — The section (module docstring), as of ``now``.
- `lines(report: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/router_objective/tail_report.py), line 162)

### Module constants

- `VERSION` ([src/learnloop/router_objective/tail_report.py](../../../../../../src/learnloop/router_objective/tail_report.py), line 34)
- `CLAIM` ([src/learnloop/router_objective/tail_report.py](../../../../../../src/learnloop/router_objective/tail_report.py), line 35)
- `NO_GUARANTEE` ([src/learnloop/router_objective/tail_report.py](../../../../../../src/learnloop/router_objective/tail_report.py), line 37)

### Explicit exports

`__all__` declares:

- `CLAIM`
- `NO_GUARANTEE`
- `VERSION`
- `build`
- `lines`

## Internal implementation anchors

- `_history(connection: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/tail_report.py), line 43)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `module`; statically calls `build`, `lines`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router_objective/learned_tail|learnloop.router_objective.learned_tail]] — imports `module`; calls `names_for`, `residual_weight`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `module`; calls `contrasts`, `cross_check`, `features_version`, `fits`, `logged`, `predicted_improvement`

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

- [tests/test_ro6_tail_data.py](../../../../../../tests/test_ro6_tail_data.py) — direct import
  - `test_a_few_weeks_on_a_copy_shaped_synthetic_vault`
  - `test_the_report_states_the_claim_and_lists_versions_and_w_hats_history`

## Modification guidance

- Make changes here when the responsibility remains tail report within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/tail_report.py](../../../../../../src/learnloop/router_objective/tail_report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

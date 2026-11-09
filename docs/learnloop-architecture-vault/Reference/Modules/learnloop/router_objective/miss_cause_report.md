---
title: "learnloop.router_objective.miss_cause_report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/miss_cause_report.py"
source_paths:
  - "src/learnloop/router_objective/miss_cause_report.py"
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
  - "learnloop.router_objective.miss_cause_report module"
  - "src/learnloop/router_objective/miss_cause_report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.miss_cause_report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.miss_cause_report` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: ``learnloop data-capture report``'s slip-or-gap section (``docs/specs/spec_slip_vs_gap_v1.md`` §3, SG1 item 4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/miss_cause_report.py](../../../../../../src/learnloop/router_objective/miss_cause_report.py) |
| Source lines | 129 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `section(connection: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/miss_cause_report.py), line 58)
- `lines(report: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/router_objective/miss_cause_report.py), line 106)

### Module constants

- `VERSION` ([src/learnloop/router_objective/miss_cause_report.py](../../../../../../src/learnloop/router_objective/miss_cause_report.py), line 26)
- `OFFER_PREFIX` ([src/learnloop/router_objective/miss_cause_report.py](../../../../../../src/learnloop/router_objective/miss_cause_report.py), line 27)
- `WHAT_MOVES` ([src/learnloop/router_objective/miss_cause_report.py](../../../../../../src/learnloop/router_objective/miss_cause_report.py), line 28)

### Explicit exports

`__all__` declares:

- `VERSION`
- `lines`
- `section`

## Internal implementation anchors

- `_loads(raw: Any) -> Any` ([source](../../../../../../src/learnloop/router_objective/miss_cause_report.py), line 33)
- `_weighted(rows: list[tuple[Mapping[str, Any], float | None]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/miss_cause_report.py), line 40)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] — imports `module`; statically calls `lines`, `section`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `qualifying_outcomes`; calls `qualifying_outcomes`
- [[Reference/Modules/learnloop/router_objective/miss_cause|learnloop.router_objective.miss_cause]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_sg_slip_vs_gap.py](../../../../../../tests/test_sg_slip_vs_gap.py) — direct import
  - `test_the_report_names_its_labels`

## Modification guidance

- Make changes here when the responsibility remains miss cause report within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/miss_cause_report.py](../../../../../../src/learnloop/router_objective/miss_cause_report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

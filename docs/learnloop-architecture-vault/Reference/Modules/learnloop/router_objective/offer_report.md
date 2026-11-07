---
title: "learnloop.router_objective.offer_report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/offer_report.py"
source_paths:
  - "src/learnloop/router_objective/offer_report.py"
source_commit: "workspace/uncommitted @ HEAD bc9eadcc88232d3af229b26b721d88b037e39f7d"
source_commit_timestamp: "2026-11-07T01:13:16-05:00"
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
  - "learnloop.router_objective.offer_report module"
  - "src/learnloop/router_objective/offer_report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.offer_report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.offer_report` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: Teacher TE3b (spec_teacher_v1 rev 5 §15.1a, "Evaluation" and "What the trace records"): the lesson offers' rows of ``learnloop router objective-report`` and a drawn offer's binding for ``learnloop router trace``.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/offer_report.py](../../../../../../src/learnloop/router_objective/offer_report.py) |
| Source lines | 126 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD bc9eadcc88232d3af229b26b721d88b037e39f7d` |
| Commit timestamp | `2026-11-07T01:13:16-05:00` |

## Public API

- `binding(connection: Any, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/offer_report.py), line 27) — A drawn offer's chain of ids and outcomes, or None when the decision drew no offer.
- `build(connection: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/offer_report.py), line 67) — The lesson-offer rows (module docstring).
- `lines(report: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/router_objective/offer_report.py), line 117)

### Module constants

- `VERSION` ([src/learnloop/router_objective/offer_report.py](../../../../../../src/learnloop/router_objective/offer_report.py), line 18)
- `PREFIX` ([src/learnloop/router_objective/offer_report.py](../../../../../../src/learnloop/router_objective/offer_report.py), line 19)

### Explicit exports

`__all__` declares:

- `VERSION`
- `binding`
- `build`
- `lines`

## Internal implementation anchors

- `_has(connection: Any, table: str) -> bool` ([source](../../../../../../src/learnloop/router_objective/offer_report.py), line 22)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `binding`, `module`; statically calls `binding`, `build`, `lines`

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

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No direct or one-hop consumer test was found by static import analysis.

> [!caution] Test gap signal
> Treat this as a navigation signal, not proof that behavior is untested: dynamic and higher-level coverage is outside this static map. Add focused coverage when changing isolated behavior here.

## Modification guidance

- Make changes here when the responsibility remains offer report within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/offer_report.py](../../../../../../src/learnloop/router_objective/offer_report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

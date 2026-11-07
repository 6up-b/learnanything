---
title: "learnloop.router_objective.forecast_resolve"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/forecast_resolve.py"
source_paths:
  - "src/learnloop/router_objective/forecast_resolve.py"
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
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.router_objective.forecast_resolve module"
  - "src/learnloop/router_objective/forecast_resolve.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.forecast_resolve`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.forecast_resolve` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO4 §8.9's forecast evaluation: the LLM policy's per-option forecasts, bound to observed outcomes.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/forecast_resolve.py](../../../../../../src/learnloop/router_objective/forecast_resolve.py) |
| Source lines | 175 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD bc9eadcc88232d3af229b26b721d88b037e39f7d` |
| Commit timestamp | `2026-11-07T01:13:16-05:00` |

## Public API

- `groups(connection: Any) -> tuple[list[dict[str, Any]], dict[str, int]]` ([source](../../../../../../src/learnloop/router_objective/forecast_resolve.py), line 62) — The resolvable curves (one per served decision whose drawn option the LLM policy forecast) and the counts of those censored at birth, by reason.
- `resolve(connection: Any, vault: Any, repository: Any, *, now: str, resolve_curves: Callable[..., list[dict[str, Any]]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/forecast_resolve.py), line 119) — The bound forecasts resolved by RO2's resolver, and the censored-at-birth counts (pure reads).
- `summary(resolved: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/forecast_resolve.py), line 130) — Counts and scores per binding and comparator (model, prompt, card): scored, pending, censored by reason, mean log loss and Brier score, and observed against forecast (calibration in the large).

### Module constants

- `BINDING_VERSION` ([src/learnloop/router_objective/forecast_resolve.py](../../../../../../src/learnloop/router_objective/forecast_resolve.py), line 28)
- `FORECASTER` ([src/learnloop/router_objective/forecast_resolve.py](../../../../../../src/learnloop/router_objective/forecast_resolve.py), line 29)
- `STOP` ([src/learnloop/router_objective/forecast_resolve.py](../../../../../../src/learnloop/router_objective/forecast_resolve.py), line 30)
- `OFFER_BINDING_VERSION` ([src/learnloop/router_objective/forecast_resolve.py](../../../../../../src/learnloop/router_objective/forecast_resolve.py), line 34)
- `OFFER_PREFIX` ([src/learnloop/router_objective/forecast_resolve.py](../../../../../../src/learnloop/router_objective/forecast_resolve.py), line 35)

### Explicit exports

`__all__` declares:

- `BINDING_VERSION`
- `FORECASTER`
- `OFFER_BINDING_VERSION`
- `groups`
- `resolve`
- `summary`

## Internal implementation anchors

- `_offer_anchor(connection: Any, decision_id: str) -> tuple[dict[str, Any] | None, str]` ([source](../../../../../../src/learnloop/router_objective/forecast_resolve.py), line 38) — An accepted offer's lesson and the moment it closed, or why the forecast is censored.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `module`; statically calls `resolve`
- [[Reference/Modules/learnloop/router_objective/objective_report|learnloop.router_objective.objective_report]] — imports `module`; statically calls `summary`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `table_present`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]], [[Reference/Modules/learnloop/router_objective/objective_report|learnloop.router_objective.objective_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro4_codex_review.py](../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f9_the_drawn_options_forecast_is_resolved_and_reported`
- [tests/test_te3b_binding.py](../../../../../../tests/test_te3b_binding.py) — direct import
  - `test_an_offers_forecast_is_bound_after_the_lesson_or_censored`

## Modification guidance

- Make changes here when the responsibility remains forecast resolve within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/forecast_resolve.py](../../../../../../src/learnloop/router_objective/forecast_resolve.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.router_objective.objective"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/objective.py"
source_paths:
  - "src/learnloop/router_objective/objective.py"
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
  - "learnloop.router_objective.objective module"
  - "src/learnloop/router_objective/objective.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.objective`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.objective` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: What the router's numeric policy optimizes (spec_router_objective_v1 §3): the terms of one path, their sum, and how a candidate's value is reported.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/objective.py](../../../../../../src/learnloop/router_objective/objective.py) |
| Source lines | 189 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Valued` ([source](../../../../../../src/learnloop/router_objective/objective.py), line 110) — One candidate's value (§8.8's terms).
  - `q(self) -> float` (line 121; public)
- `class Evaluation` ([source](../../../../../../src/learnloop/router_objective/objective.py), line 126)
  - `by_ref(self) -> dict[str, Valued]` (line 135; public)
  - `v(self) -> float` (line 139; public) — ``V = Σ_a π_tail(a)·Q(a)``: the tail's next action is deterministic, so ``V`` is its row's ``Q``.
- `paired_standard_error(a: Valued, b: Valued) -> float` ([source](../../../../../../src/learnloop/router_objective/objective.py), line 161) — The standard error of ``Q̄(a) − Q̄(b)`` over the shared draws (common random numbers).
- `numeric_choice(evaluation: Evaluation, support: Sequence[str]) -> tuple[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/objective.py), line 170) — ``π_Q`` (§8.3): plain argmax of ``Q̄``; candidates within the paired precision of the maximum are broken by support order (staged's pick first).

### Module constants

- `OBJECTIVE_VERSION` ([src/learnloop/router_objective/objective.py](../../../../../../src/learnloop/router_objective/objective.py), line 54)
- `TERMINAL_VERSION` ([src/learnloop/router_objective/objective.py](../../../../../../src/learnloop/router_objective/objective.py), line 55)
- `_LEDGER_FIELDS` ([src/learnloop/router_objective/objective.py](../../../../../../src/learnloop/router_objective/objective.py), line 58)

### Explicit exports

`__all__` declares:

- `OBJECTIVE_VERSION`
- `TERMINAL_VERSION`
- `Evaluation`
- `Valued`
- `numeric_choice`
- `paired_standard_error`

## Internal implementation anchors

- `class _Ledger` ([source](../../../../../../src/learnloop/router_objective/objective.py), line 63) — Per draw: the terms of one path (§8.8's per-candidate terms).
- `_terms(ledger: _Ledger, model: Any=None) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/objective.py), line 145)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `numeric_choice`
- [[Reference/Modules/learnloop/daily_plan/objective_job|learnloop.daily_plan.objective_job]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/diagnostic_value|learnloop.router_objective.diagnostic_value]] — imports `Evaluation`, `Valued`, `_LEDGER_FIELDS`, `_Ledger`, `_terms`, `numeric_choice`; statically calls `Evaluation`, `Valued`, `_Ledger`, `_terms`, `numeric_choice`
- [[Reference/Modules/learnloop/router_objective/rollouts|learnloop.router_objective.rollouts]] — imports `Evaluation`, `Valued`, `_Ledger`, `_terms`; statically calls `Evaluation`, `Valued`, `_terms`
- [[Reference/Modules/learnloop/router_objective/trace_assembly|learnloop.router_objective.trace_assembly]] — imports `module`; statically calls `paired_standard_error`

### Repository tooling consumers

- [scripts/probe_router_report.py](../../../../../../scripts/probe_router_report.py); calls `numeric_choice`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/daily_plan/objective_job|learnloop.daily_plan.objective_job]], [[Reference/Modules/learnloop/router_objective/diagnostic_value|learnloop.router_objective.diagnostic_value]], [[Reference/Modules/learnloop/router_objective/rollouts|learnloop.router_objective.rollouts]], [[Reference/Modules/learnloop/router_objective/trace_assembly|learnloop.router_objective.trace_assembly]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/rospeed_ad_link_helpers.py](../../../../../../tests/rospeed_ad_link_helpers.py) — direct import
- [tests/test_action_kinds_complete.py](../../../../../../tests/test_action_kinds_complete.py) — direct import
  - `test_action_kind_has_a_rollout_effect`
- [tests/test_diagnostic_probe_value.py](../../../../../../tests/test_diagnostic_probe_value.py) — direct import
  - `test_the_probe_answer_is_not_also_a_binary_ability_observation`
- [tests/test_objective_terms.py](../../../../../../tests/test_objective_terms.py) — direct import
  - `test_a_candidates_value_is_the_mean_of_its_draws_and_v_is_the_reference_rows`
  - `test_the_ledger_holds_every_term_and_nothing_else`
  - `test_the_numeric_policy_takes_the_argmax_and_breaks_ties_within_the_paired_precision_by_support_order`
  - `test_the_trace_reports_each_terms_mean_in_a_fixed_order`
- [tests/test_ro4_codex_review.py](../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f9_the_drawn_options_forecast_is_resolved_and_reported`
- [tests/test_ro4_value.py](../../../../../../tests/test_ro4_value.py) — direct import
  - `test_f12_one_draws_action_duration_never_moves_another_draws_clock`
  - `test_the_numeric_policy_is_argmax_with_ties_by_support_order`
- [tests/test_rospeed_ad_link.py](../../../../../../tests/test_rospeed_ad_link.py) — direct import
- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains objective within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/objective.py](../../../../../../src/learnloop/router_objective/objective.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

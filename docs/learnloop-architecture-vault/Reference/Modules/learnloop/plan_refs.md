---
title: "learnloop.plan_refs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/plan_refs.py"
source_paths:
  - "src/learnloop/plan_refs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.plan_refs module"
  - "src/learnloop/plan_refs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.plan_refs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.plan_refs` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: The plan's option names that every layer reads: a lesson offer's block subtype and the prefix of its ref, and the stop option's ref.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/plan_refs.py](../../../../../src/learnloop/plan_refs.py) |
| Source lines | 28 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `is_offer_subtype(subtype: str | None) -> bool` ([source](../../../../../src/learnloop/plan_refs.py), line 19) — Whether a block subtype is a lesson offer's.

### Module constants

- `LESSON_OFFER_SUBTYPE` ([src/learnloop/plan_refs.py](../../../../../src/learnloop/plan_refs.py), line 13)
- `LESSON_OFFER_PREFIX` ([src/learnloop/plan_refs.py](../../../../../src/learnloop/plan_refs.py), line 14)
- `STOP_FOR_TODAY` ([src/learnloop/plan_refs.py](../../../../../src/learnloop/plan_refs.py), line 16)

### Explicit exports

`__all__` declares:

- `LESSON_OFFER_PREFIX`
- `LESSON_OFFER_SUBTYPE`
- `STOP_FOR_TODAY`
- `is_offer_subtype`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `is_offer_subtype`; statically calls `is_offer_subtype`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `is_offer_subtype`; statically calls `is_offer_subtype`
- [[Reference/Modules/learnloop/daily_plan/objective_card|learnloop.daily_plan.objective_card]] — imports `is_offer_subtype`; statically calls `is_offer_subtype`
- [[Reference/Modules/learnloop/daily_plan/records|learnloop.daily_plan.records]] — imports `is_offer_subtype`; statically calls `is_offer_subtype`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `LESSON_OFFER_PREFIX`, `LESSON_OFFER_SUBTYPE`, `STOP_FOR_TODAY`
- [[Reference/Modules/learnloop/db/stores/router_suggestions|learnloop.db.stores.router_suggestions]] — imports `LESSON_OFFER_PREFIX`
- [[Reference/Modules/learnloop/followup_run/decision_view|learnloop.followup_run.decision_view]] — imports `LESSON_OFFER_PREFIX`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `LESSON_OFFER_PREFIX`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `LESSON_OFFER_PREFIX`
- [[Reference/Modules/learnloop/router/decisions|learnloop.router.decisions]] — imports `STOP_FOR_TODAY`
- [[Reference/Modules/learnloop/router/plan_log|learnloop.router.plan_log]] — imports `LESSON_OFFER_PREFIX`, `STOP_FOR_TODAY`
- [[Reference/Modules/learnloop/router_objective/forecast_resolve|learnloop.router_objective.forecast_resolve]] — imports `LESSON_OFFER_PREFIX`, `STOP_FOR_TODAY`
- [[Reference/Modules/learnloop/router_objective/miss_cause_report|learnloop.router_objective.miss_cause_report]] — imports `LESSON_OFFER_PREFIX`
- [[Reference/Modules/learnloop/router_objective/objective_report|learnloop.router_objective.objective_report]] — imports `STOP_FOR_TODAY`
- [[Reference/Modules/learnloop/router_objective/offer_report|learnloop.router_objective.offer_report]] — imports `LESSON_OFFER_PREFIX`
- [[Reference/Modules/learnloop/router_objective/preference_report|learnloop.router_objective.preference_report]] — imports `LESSON_OFFER_PREFIX`, `STOP_FOR_TODAY`
- [[Reference/Modules/learnloop/router_objective/sessions|learnloop.router_objective.sessions]] — imports `STOP_FOR_TODAY`
- [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]] — imports `STOP_FOR_TODAY`
- [[Reference/Modules/learnloop/router_objective/types|learnloop.router_objective.types]] — imports `LESSON_OFFER_PREFIX`, `LESSON_OFFER_SUBTYPE`, `STOP_FOR_TODAY`, `is_offer_subtype`
- [[Reference/Modules/learnloop/teacher/diagnosed_sources|learnloop.teacher.diagnosed_sources]] — imports `LESSON_OFFER_PREFIX`
- [[Reference/Modules/learnloop/why/reconstructed|learnloop.why.reconstructed]] — imports `LESSON_OFFER_PREFIX`

### Repository tooling consumers

- [scripts/check_credit_report.py](../../../../../scripts/check_credit_report.py)

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]], [[Reference/Modules/learnloop/daily_plan/objective_card|learnloop.daily_plan.objective_card]], [[Reference/Modules/learnloop/daily_plan/records|learnloop.daily_plan.records]], [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] and 16 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_plan_refs.py](../../../../../tests/test_plan_refs.py) — direct import
  - `test_the_strings_keep_their_bytes_and_every_layer_reads_the_leafs`
  - `test_the_subtype_predicate_takes_a_subtype_and_refuses_a_candidate`
- [tests/test_probe_router_authority.py](../../../../../tests/test_probe_router_authority.py) — direct import
  - `test_d_a_retry_keeps_the_first_draw_and_asks_only_the_hard_refusals_again`
  - `test_f_a_lesson_win_releases_the_hold_and_generates_nothing`
  - `test_f_on_a_plan_the_router_draws_once_over_its_arms_and_a_lesson_at_the_same_boundary`
  - `test_f_with_no_room_to_wait_the_probe_is_forced_unless_a_lesson_contests_it`

## Modification guidance

- Make changes here when the responsibility remains plan refs within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/plan_refs.py](../../../../../src/learnloop/plan_refs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

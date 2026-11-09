---
title: "learnloop.router_objective.cold_timing"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/cold_timing.py"
source_paths:
  - "src/learnloop/router_objective/cold_timing.py"
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
  - "learnloop.router_objective.cold_timing module"
  - "src/learnloop/router_objective/cold_timing.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.cold_timing`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.cold_timing` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO0 row 10 (spec_router_objective_v1 §4): how a cold check's target delay was chosen, and why one was not served.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/cold_timing.py](../../../../../../src/learnloop/router_objective/cold_timing.py) |
| Source lines | 65 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `non_service_type(reason: str) -> str | None` ([source](../../../../../../src/learnloop/router_objective/cold_timing.py), line 42) — The type of an unserved check's reason, or None for one not typed yet.
- `delay_receipt(vault: Any, *, days: float, basis: str, purpose: str) -> str` ([source](../../../../../../src/learnloop/router_objective/cold_timing.py), line 51) — How a check's delay was chosen: the rule, its inputs in force, and whether the cap decided it.

### Module constants

- `DELAY_VERSION` ([src/learnloop/router_objective/cold_timing.py](../../../../../../src/learnloop/router_objective/cold_timing.py), line 16)
- `STRUCTURALLY_REFUSED` ([src/learnloop/router_objective/cold_timing.py](../../../../../../src/learnloop/router_objective/cold_timing.py), line 17)
- `POLICY_REFUSED` ([src/learnloop/router_objective/cold_timing.py](../../../../../../src/learnloop/router_objective/cold_timing.py), line 18)
- `OPERATIONALLY_UNAVAILABLE` ([src/learnloop/router_objective/cold_timing.py](../../../../../../src/learnloop/router_objective/cold_timing.py), line 19)
- `LEARNER_DECLINED` ([src/learnloop/router_objective/cold_timing.py](../../../../../../src/learnloop/router_objective/cold_timing.py), line 20)
- `ANSWERED_UNREAD` ([src/learnloop/router_objective/cold_timing.py](../../../../../../src/learnloop/router_objective/cold_timing.py), line 21)
- `_REPLACEMENT_PREFIX` ([src/learnloop/router_objective/cold_timing.py](../../../../../../src/learnloop/router_objective/cold_timing.py), line 23)
- `_TYPES` ([src/learnloop/router_objective/cold_timing.py](../../../../../../src/learnloop/router_objective/cold_timing.py), line 25)

### Explicit exports

`__all__` declares:

- `ANSWERED_UNREAD`
- `DELAY_VERSION`
- `LEARNER_DECLINED`
- `OPERATIONALLY_UNAVAILABLE`
- `POLICY_REFUSED`
- `STRUCTURALLY_REFUSED`
- `delay_receipt`
- `non_service_type`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]] — imports `module`; statically calls `delay_receipt`, `non_service_type`

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

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro0_codex_verify.py](../../../../../../tests/test_ro0_codex_verify.py) — direct import
  - `test_r1_an_arranged_check_keeps_its_objective_whatever_its_delay_meets`
  - `test_r1_an_unserved_check_keeps_its_state_whatever_its_type_meets`
- [tests/test_ro0_row10_cold_timing.py](../../../../../../tests/test_ro0_row10_cold_timing.py) — direct import
  - `test_an_arranged_check_says_how_its_delay_was_chosen`
  - `test_each_reason_has_its_type_and_a_new_one_stays_untyped`
  - `test_every_reason_the_measurement_writes_is_typed`
  - `test_no_question_to_ask_is_typed_structural`

## Modification guidance

- Make changes here when the responsibility remains cold timing within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/cold_timing.py](../../../../../../src/learnloop/router_objective/cold_timing.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

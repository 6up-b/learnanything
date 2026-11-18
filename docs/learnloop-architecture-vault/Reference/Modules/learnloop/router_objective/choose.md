---
title: "learnloop.router_objective.choose"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/choose.py"
source_paths:
  - "src/learnloop/router_objective/choose.py"
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
  - "learnloop.router_objective.choose module"
  - "src/learnloop/router_objective/choose.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.choose`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.choose` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO4/RO5: the objective router's choice at a block boundary, as one pure function.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/choose.py](../../../../../../src/learnloop/router_objective/choose.py) |
| Source lines | 264 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class OptionFacts` ([source](../../../../../../src/learnloop/router_objective/choose.py), line 45) — What the rule sentence reads of one option in the support: the reason code the staged frame (or the boundary, for an offer or IH2's contest) gave it, and the topic or section its sentence names.
- `class ChoiceInputs` ([source](../../../../../../src/learnloop/router_objective/choose.py), line 55) — Everything one boundary's choice depends on, as read before it.
- `class Choice` ([source](../../../../../../src/learnloop/router_objective/choose.py), line 96) — What :func:`choose` decided, as the router logs it.
- `coin_reads_minutes(stop_rate: float, support: tuple[str, ...] | list[str]) -> bool` ([source](../../../../../../src/learnloop/router_objective/choose.py), line 136) — Whether the coin could apply, so the session's minutes are read for it: a positive rate and stop offered.
- `coin_applies(stop_rate: float, support: tuple[str, ...] | list[str], session_minutes: float | None) -> bool` ([source](../../../../../../src/learnloop/router_objective/choose.py), line 142) — Whether the coin is flipped (and its availability read first): a positive rate at a boundary where stop sits beside a block once the session holds active minutes (``stop_coin.eligible``).
- `choose(inputs: ChoiceInputs) -> Choice` ([source](../../../../../../src/learnloop/router_objective/choose.py), line 149) — The boundary's choice: the mix of the two policies over the support, the stop coin on its own uniform, the rule sentence of what is served and the why the learner sees.

### Module constants

- `MODE` ([src/learnloop/router_objective/choose.py](../../../../../../src/learnloop/router_objective/choose.py), line 32)
- `NO_MODELS` ([src/learnloop/router_objective/choose.py](../../../../../../src/learnloop/router_objective/choose.py), line 33)
- `WHY_VERSION` ([src/learnloop/router_objective/choose.py](../../../../../../src/learnloop/router_objective/choose.py), line 35)
- `ANSWERED` ([src/learnloop/router_objective/choose.py](../../../../../../src/learnloop/router_objective/choose.py), line 37)
- `NOT_READY` ([src/learnloop/router_objective/choose.py](../../../../../../src/learnloop/router_objective/choose.py), line 38)
- `STOP_OFFER` ([src/learnloop/router_objective/choose.py](../../../../../../src/learnloop/router_objective/choose.py), line 40)
- `PLAN_BLOCK` ([src/learnloop/router_objective/choose.py](../../../../../../src/learnloop/router_objective/choose.py), line 41)

### Explicit exports

`__all__` declares:

- `ANSWERED`
- `Choice`
- `ChoiceInputs`
- `MODE`
- `NOT_READY`
- `NO_MODELS`
- `OptionFacts`
- `STOP_OFFER`
- `WHY_VERSION`
- `choose`
- `coin_applies`
- `coin_reads_minutes`

## Internal implementation anchors

- `_code(value: Any) -> str | None` ([source](../../../../../../src/learnloop/router_objective/choose.py), line 210)
- `_number(value: Any) -> float | int | None` ([source](../../../../../../src/learnloop/router_objective/choose.py), line 214)
- `_compact(values: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/choose.py), line 220)
- `_with_record(choice: Choice, inputs: ChoiceInputs) -> Choice` ([source](../../../../../../src/learnloop/router_objective/choose.py), line 224) — The decision's ``plan_block`` record: chosen, its rule, the support's other options with their logged probabilities, and the draw's facts and versions.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `ChoiceInputs`, `OptionFacts`, `choose`, `coin_applies`, `coin_reads_minutes`
- [[Reference/Modules/learnloop/router_objective/trace_assembly|learnloop.router_objective.trace_assembly]] — imports `ANSWERED`, `NOT_READY`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `DecisionRecord`, `module`; calls `DecisionRecord`, `is_code`, `ref`
- [[Reference/Modules/learnloop/router/mixture|learnloop.router.mixture]] — imports `module`
- [[Reference/Modules/learnloop/router/why|learnloop.router.why]] — imports `module`; calls `objective_why`, `rationale_guard`, `sentence`
- [[Reference/Modules/learnloop/router_objective/mix|learnloop.router_objective.mix]] — imports `module`; calls `components`, `draw`, `effective_weights`, `fallback_label`
- [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]] — imports `module`; calls `eligible`, `flip`, `pending_assignment`, `served_distribution`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/router_objective/trace_assembly|learnloop.router_objective.trace_assembly]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_choose.py](../../../../../../tests/test_choose.py) — direct import
  - `test_a_block_with_no_code_has_no_rule_and_the_staged_pick_keeps_the_plans_why`
  - `test_a_failed_llm_policys_share_goes_to_the_numeric_policy_with_the_switch_on`
  - `test_a_numeric_choice_outside_the_support_fails_the_numeric_policy`
  - `test_a_one_hot_mix_is_served_with_propensity_one`
  - `test_both_failed_leave_staged_the_whole_mix_and_a_missing_answer_reads_not_ready`
  - `test_it_reads_no_database_clock_or_id_stream_and_leaves_its_inputs_alone`
  - `test_the_choice_returns_its_own_plan_block_record`
  - `test_the_coin_draws_after_the_mix_on_its_own_uniform_and_leaves_the_mixs_draw_alone`
  - `test_the_coin_skips_the_sessions_opening_boundary_and_needs_its_availability`
  - `test_the_statuses_it_compares_are_the_runtimes`
  - `test_with_no_coin_the_logged_distribution_is_the_mixs_and_the_propensity_its_draws`
  - `test_with_the_switch_off_a_failed_policys_share_goes_to_staged`

## Modification guidance

- Make changes here when the responsibility remains choose within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/choose.py](../../../../../../src/learnloop/router_objective/choose.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

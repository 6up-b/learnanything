---
title: "learnloop.router_objective.diagnostic_value"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/diagnostic_value.py"
source_paths:
  - "src/learnloop/router_objective/diagnostic_value.py"
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
  - "learnloop.router_objective.diagnostic_value module"
  - "src/learnloop/router_objective/diagnostic_value.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.diagnostic_value`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.diagnostic_value` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: The successor's value of a post-miss probe (G2 design §2b): ask the probe, then act on its result, priced against acting now without it, over the locked hypotheses, in the router objective's own terms.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/diagnostic_value.py](../../../../../../src/learnloop/router_objective/diagnostic_value.py) |
| Source lines | 320 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ProbeValuation` ([source](../../../../../../src/learnloop/router_objective/diagnostic_value.py), line 63) — The candidate's row (the probe's policy, a sequence holding it, or an offer declining into it) and each acting-now arm's, in the objective's :class:`Valued` terms; the choice among them (``π_Q``'s rule, acting now first in the support order, so a probe that only ties acting now…
  - `by_ref(self) -> dict[str, Valued]` (line 72; public)
- `evaluate_probe(inputs: Inputs, action: Action, *, decisions: DP.OwnerDecisions, draws: int, seed: str, wait_feasible: bool=True, base_stream: int=0, merged_sessions: bool=False, consistent_review_draw: bool=False, held_ad_link: bool=False, clock: Callable[[], float]=time.perf_counter) -> ProbeValuation` ([source](../../../../../../src/learnloop/router_objective/diagnostic_value.py), line 201) — The value of the diagnostic probe ``action`` carries (alone, as one step of a sequence, or in an offer's declined branch) against acting now, with its record.

### Module constants

- `POLICY_VERSION` ([src/learnloop/router_objective/diagnostic_value.py](../../../../../../src/learnloop/router_objective/diagnostic_value.py), line 51)
- `ACT_NOW` ([src/learnloop/router_objective/diagnostic_value.py](../../../../../../src/learnloop/router_objective/diagnostic_value.py), line 53)
- `NONE` ([src/learnloop/router_objective/diagnostic_value.py](../../../../../../src/learnloop/router_objective/diagnostic_value.py), line 54)
- `REPAIR_STREAM` ([src/learnloop/router_objective/diagnostic_value.py](../../../../../../src/learnloop/router_objective/diagnostic_value.py), line 57)
- `DECLINED_STREAM` ([src/learnloop/router_objective/diagnostic_value.py](../../../../../../src/learnloop/router_objective/diagnostic_value.py), line 59)

### Explicit exports

`__all__` declares:

- `ACT_NOW`
- `DECLINED_STREAM`
- `NONE`
- `POLICY_VERSION`
- `REPAIR_STREAM`
- `ProbeValuation`
- `evaluate_probe`

## Internal implementation anchors

- `_weighted(parts: Sequence[tuple[float, _Ledger]]) -> _Ledger` ([source](../../../../../../src/learnloop/router_objective/diagnostic_value.py), line 76) — ``Σ w·ledger``, term by term, per draw (each branch's path weighted by its probability).
- `_world(model: _Model, lo: int | None, key: str) -> Iterator[None]` ([source](../../../../../../src/learnloop/router_objective/diagnostic_value.py), line 83) — While a repair runs, its topic learns as it would if the hypothesis behind ``key`` were true: the cause-class slope through the rollouts' own ``_cause_gain`` (a one-hot split), or practice's ``γ`` (no split) when the repair does not cover it or the inputs carry no cause slopes.
- `class _Place` ([source](../../../../../../src/learnloop/router_objective/diagnostic_value.py), line 108) — Where the probe sits: the steps before it and after it (each with its stream), the probe's own stream, the offer wrapping it (None: none), and the record's words for the position.
- `_place(model: _Model, action: Action, base_stream: int) -> _Place` ([source](../../../../../../src/learnloop/router_objective/diagnostic_value.py), line 122)
- `class _Paths` ([source](../../../../../../src/learnloop/router_objective/diagnostic_value.py), line 142) — Every path one model needs: the steps before the probe once, then per option and effect key a copy that runs the probe (or not), the option, the steps after and the tail.
- `_choose(options: Sequence[tuple[str, DP.RepairOption | None]], hypotheses: Sequence[DP.Hypothesis], q: Mapping[tuple[str, str], float], posterior: Mapping[str, float]) -> tuple[str, dict[str, float]]` ([source](../../../../../../src/learnloop/router_objective/diagnostic_value.py), line 188) — The option with the highest posterior-expected ``Q̄`` (the first in option order on a tie: no repair first).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

### Repository tooling consumers

- [scripts/probe_router_report.py](../../../../../../scripts/probe_router_report.py); calls `evaluate_probe`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router_objective/check_value|learnloop.router_objective.check_value]] — imports `_CheckModel`
- [[Reference/Modules/learnloop/router_objective/diagnostic_payload|learnloop.router_objective.diagnostic_payload]] — imports `module`; calls `effect_key`, `posterior_table`
- [[Reference/Modules/learnloop/router_objective/objective|learnloop.router_objective.objective]] — imports `Evaluation`, `Valued`, `_LEDGER_FIELDS`, `_Ledger`, `_terms`, `numeric_choice`; calls `Evaluation`, `Valued`, `_Ledger`, `_terms`, `numeric_choice`
- [[Reference/Modules/learnloop/router_objective/rollouts|learnloop.router_objective.rollouts]] — imports `_Model`, `_State`, `_beta_draw`, `_carries`; calls `_beta_draw`, `_carries`
- [[Reference/Modules/learnloop/router_objective/types|learnloop.router_objective.types]] — imports `Action`, `Inputs`, `PROBE`, `SEQUENCE`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `time`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_action_kinds_complete.py](../../../../../../tests/test_action_kinds_complete.py) — direct import
  - `test_a_probe_with_a_diagnostic_payload_has_its_effect_through_the_successor_evaluator`
- [tests/test_check_value.py](../../../../../../tests/test_check_value.py) — direct import
  - `test_the_rollouts_refuse_typed_checks_and_this_path_refuses_untyped_ones`
- [tests/test_diagnostic_probe_value.py](../../../../../../tests/test_diagnostic_probe_value.py) — direct import
  - `test_a_flat_channel_changes_nothing_and_its_probe_is_worth_only_its_burden`
  - `test_a_probe_anywhere_in_a_sequence_appends_the_rest_and_the_tail_once`
  - `test_acting_now_is_always_valued_beside_the_probe`
  - `test_the_evaluator_is_deterministic_and_its_record_names_its_inputs`
  - `test_the_owner_decisions_are_named_inputs_marked_pending`
  - `test_the_probe_duration_is_charged_once`

## Modification guidance

- Make changes here when the responsibility remains diagnostic value within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/diagnostic_value.py](../../../../../../src/learnloop/router_objective/diagnostic_value.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

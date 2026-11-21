---
title: "learnloop.router_objective.check_value"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/check_value.py"
source_paths:
  - "src/learnloop/router_objective/check_value.py"
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
  - "learnloop.router_objective.check_value module"
  - "src/learnloop/router_objective/check_value.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.check_value`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.check_value` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: The successor's value of a lesson's committed delayed checks (spec_teacher_v2 §7.4): a check happens only when the simulated learner returns, costs its minutes on that session's clock, and is answered only as often as checks like it are answered cold.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/check_value.py](../../../../../../src/learnloop/router_objective/check_value.py) |
| Source lines | 187 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `uniforms(seed: str, name: str, draws: int) -> np.ndarray` ([source](../../../../../../src/learnloop/router_objective/check_value.py), line 69) — The named stream's ``draws`` uniforms (one array per name: a longer one extends a shorter one's prefix).
- `propensity(u: np.ndarray, delivery: tuple[float, float]) -> np.ndarray` ([source](../../../../../../src/learnloop/router_objective/check_value.py), line 75) — The delivery posterior's draw at ``u``: the Beta quantile, or the point mass at an endpoint.
- `evaluate(inputs: Inputs, actions: Sequence[Action], *, draws: int, seed: str, max_draws: int | None=None, keep_going: Callable[[], bool] | None=None, deadline: float | None=None, clock: Callable[[], float]=time.monotonic, on_complete: Callable[[Evaluation], None] | None=None, cutoff: float | None=None, unmeasured: Collection[str] | None=None, merged_sessions: bool=False, consistent_review_draw: bool=False, held_ad_link: bool=False) -> Evaluation` ([source](../../../../../../src/learnloop/router_objective/check_value.py), line 158) — ``rollouts.evaluate`` with typed committed checks priced by this module's rule (its arguments, its loop, its refinement and its reference row); an action with no typed checks gets exactly the rollouts' value.
- `simulate(inputs: Inputs, action: Action, *, draws: int, seed: str, **options: Any) -> tuple[_Ledger, _State, tuple[np.ndarray, ...]]` ([source](../../../../../../src/learnloop/router_objective/check_value.py), line 173) — One action's own path (no offer mixing: an offer's accepted branch is the action without ``accept``): its ledger, the state after its tail, and each typed check's answer time per draw (NaN: not answered), in due order.

### Module constants

- `POLICY_VERSION` ([src/learnloop/router_objective/check_value.py](../../../../../../src/learnloop/router_objective/check_value.py), line 59)
- `STREAM_LAYOUT_VERSION` ([src/learnloop/router_objective/check_value.py](../../../../../../src/learnloop/router_objective/check_value.py), line 61)
- `FIT_TOLERANCE_MINUTES` ([src/learnloop/router_objective/check_value.py](../../../../../../src/learnloop/router_objective/check_value.py), line 65)
- `_UNTYPED` ([src/learnloop/router_objective/check_value.py](../../../../../../src/learnloop/router_objective/check_value.py), line 66)

### Explicit exports

`__all__` declares:

- `FIT_TOLERANCE_MINUTES`
- `POLICY_VERSION`
- `STREAM_LAYOUT_VERSION`
- `evaluate`
- `propensity`
- `simulate`
- `uniforms`

## Internal implementation anchors

- `class _Check` ([source](../../../../../../src/learnloop/router_objective/check_value.py), line 86) — One typed check on one path: its topic, due time, minutes, whether it is delivered, its outcome draws.
- `class _CheckModel(_Model)` ([source](../../../../../../src/learnloop/router_objective/check_value.py), line 102) — The rollouts' model with typed checks executed on simulated returns (the module docstring's rule).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/check_inputs|learnloop.daily_plan.check_inputs]] — imports `POLICY_VERSION`, `STREAM_LAYOUT_VERSION`
- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/diagnostic_value|learnloop.router_objective.diagnostic_value]] — imports `_CheckModel`

### Repository tooling consumers

- [scripts/check_credit_report.py](../../../../../../scripts/check_credit_report.py); calls `evaluate`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router_objective/objective|learnloop.router_objective.objective]] — imports `Evaluation`, `_Ledger`
- [[Reference/Modules/learnloop/router_objective/rollouts|learnloop.router_objective.rollouts]] — imports `MINUTES_PER_DAY`, `_Model`, `_State`, `_beta_draw`, `_carries`, `_evaluate`, `_seed_int`; calls `_beta_draw`, `_carries`, `_evaluate`, `_seed_int`
- [[Reference/Modules/learnloop/router_objective/types|learnloop.router_objective.types]] — imports `Action`, `CheckCommitment`, `Inputs`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `time`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/check_inputs|learnloop.daily_plan.check_inputs]], [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/router_objective/diagnostic_value|learnloop.router_objective.diagnostic_value]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_check_credit_activation.py](../../../../../../tests/test_check_credit_activation.py) — direct import
  - `test_both_tags_the_decisions_numeric_answer_and_its_trace`
  - `test_both_tags_the_offer_record_and_its_action`
  - `test_the_payload_is_lossless_and_refuses_what_it_cannot_hold`
  - `test_the_tag`
- [tests/test_check_credit_characterization.py](../../../../../../tests/test_check_credit_characterization.py) — direct import
  - `test_both_paths_a_check_happens_only_on_a_simulated_return`
  - `test_both_paths_a_check_is_charged_its_minutes_on_the_session_clock`
  - `test_both_paths_the_ninth_commitment_draws_its_own_outcome`
  - `test_both_tags_an_offer_with_no_eligible_question`
  - `test_finding_a_first_graded_attempt_switches_an_unpractised_topic_onto_forgetting`
- [tests/test_check_value.py](../../../../../../tests/test_check_value.py) — direct import
  - `test_a_lesson_offer_without_checks_and_the_eve_of_exam_case_are_unchanged`
  - `test_actions_without_typed_checks_are_valued_identically_on_both_paths`
  - `test_an_undelivered_check_is_no_event`
  - `test_delivery_and_outcome_streams_are_apart_and_keep_their_prefixes`
  - `test_refining_the_draws_keeps_every_earlier_draws_value`
  - `test_the_delivery_posterior_is_sampled_once_per_path_and_shared_within_its_group`
  - `test_the_fit_tolerance_is_the_plans`
  - `test_the_rollouts_refuse_typed_checks_and_this_path_refuses_untyped_ones`
  - `test_two_checks_on_one_topic_are_two_commitments`
  - `test_two_checks_that_do_not_fit_one_session_wait_for_the_next_return`
- [tests/test_objective_refinement.py](../../../../../../tests/test_objective_refinement.py) — direct import
- [tests/test_rofu_carried.py](../../../../../../tests/test_rofu_carried.py) — direct import
  - `test_an_early_publication_served_keeps_its_carried_valuation`
  - `test_the_no_model_branch_defers_its_carried_valuation_off_the_serving_path`
  - `test_with_models_the_wait_returns_and_the_next_prefetch_runs_it`

## Modification guidance

- Make changes here when the responsibility remains check value within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/check_value.py](../../../../../../src/learnloop/router_objective/check_value.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

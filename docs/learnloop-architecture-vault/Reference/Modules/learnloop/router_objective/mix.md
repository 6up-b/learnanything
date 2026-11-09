---
title: "learnloop.router_objective.mix"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/mix.py"
source_paths:
  - "src/learnloop/router_objective/mix.py"
source_commit: "d602dc8472b09d92a6b854c9fbf969355b1ae1e0"
source_commit_timestamp: "2026-11-08T20:56:56-05:00"
source_worktree_state: "clean"
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
  - "learnloop.router_objective.mix module"
  - "src/learnloop/router_objective/mix.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.mix`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.mix` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO4 §8.3: the served distribution of the two policies' learned mix, exact and logged (G3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py) |
| Source lines | 164 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `d602dc8472b09d92a6b854c9fbf969355b1ae1e0` |
| Commit timestamp | `2026-11-08T20:56:56-05:00` |

## Public API

- `class ObjectiveMixError(ValueError)` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 46) — The mix's inputs cannot give an exact distribution.
- `failure_rule_name(to_other_policy: bool) -> str` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 50)
- `effective_weights(w: float, failed: Sequence[str] | set[str] | frozenset[str], *, to_other_policy: bool=False) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 54) — ``{staged, llm, numeric}``: ``w`` to the LLM policy and ``1 − w`` to the numeric one, each failed policy's share moved to ``staged`` (failure redistribution as §8.3 wrote it).
- `fallback_label(failed: Sequence[str] | set[str] | frozenset[str]) -> str | None` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 79)
- `one_hot(support: Sequence[str], ref: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 86)
- `components(support: Sequence[str], staged_ref: str, *, llm: Mapping[str, float] | None, numeric_ref: str | None) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 92) — Every live component's distribution over the support (a failed policy's is absent).
- `mu(support: Sequence[str], parts: Mapping[str, Mapping[str, float]], weights: Mapping[str, float], epsilon: float) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 106)
- `draw(support: Sequence[str], parts: Mapping[str, Mapping[str, float]], weights: Mapping[str, float], epsilon: float, seed: str) -> mx.Draw` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 118) — The two-stage draw (its marginal is :func:`mu`).
- `seed_for(boundary_key: str, decision_id: str) -> str` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 137)
- `recompute(record: Mapping[str, Any]) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 143) — G3: ``μ`` over the support from a logged decision's own values (``support``, ``staged_ref``, ``epsilon``, ``w``, ``failed``, ``llm_distribution``, ``numeric_choice``, and ``failure_rule`` when present).

### Module constants

- `DESIGN` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 32)
- `POLICY` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 33)
- `LLM` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 34)
- `NUMERIC` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 35)
- `STAGED` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 36)
- `COMPONENTS` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 37)
- `POLICIES` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 38)
- `STAGED_RULE` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 41)
- `OTHER_POLICY_RULE` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 42)
- `FAILURE_RULES` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 43)

### Explicit exports

`__all__` declares:

- `COMPONENTS`
- `DESIGN`
- `FAILURE_RULES`
- `LLM`
- `NUMERIC`
- `ObjectiveMixError`
- `OTHER_POLICY_RULE`
- `POLICIES`
- `POLICY`
- `STAGED`
- `STAGED_RULE`
- `components`
- `draw`
- `effective_weights`
- `failure_rule_name`
- `fallback_label`
- `mu`
- `one_hot`
- `recompute`
- `seed_for`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `components`, `draw`, `effective_weights`, `fallback_label`, `seed_for`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router/mixture|learnloop.router.mixture]] — imports `module`; calls `Draw`, `_pick`, `normalized`, `uniform`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ih2_lessons_compete.py](../../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_a_lesson_win_after_a_miss_generates_nothing_and_the_offer_page_opens_from_next`
- [tests/test_ih3_learner_preferences.py](../../../../../../tests/test_ih3_learner_preferences.py) — direct import
  - `test_the_options_are_the_plans_own_candidates_and_the_waiting_draw_is_the_parent`
- [tests/test_ih5_successor.py](../../../../../../tests/test_ih5_successor.py) — direct import
  - `test_a_lesson_offer_in_the_support_can_be_drawn_when_the_llm_has_no_answer`
  - `test_a_logged_decision_replays_to_its_logged_mu_under_its_own_rule`
  - `test_each_row_of_the_table_produces_its_weights`
  - `test_replay_under_both_rules_on_a_synthetic_history_reports_how_often_the_served_choice_changes`
  - `test_switch_off_or_below_the_tag_the_mix_is_the_predecessors_exactly`
  - `test_the_floor_is_kept_and_propensities_are_exact_in_every_row`
  - `test_with_the_llm_down_numeric_takes_the_whole_mix_and_staged_is_only_the_last_resort`
- [tests/test_instruct_handoff_ih1.py](../../../../../../tests/test_instruct_handoff_ih1.py) — direct import
  - `test_no_new_draw_joins_an_open_item`
- [tests/test_ro4_codex_review.py](../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f1_a_slow_llm_leaves_the_numeric_share_in_place`
- [tests/test_ro4_objective_serving.py](../../../../../../tests/test_ro4_objective_serving.py) — direct import
  - `test_a_failed_llm_moves_only_its_share_to_staged`
  - `test_a_numeric_timeout_is_a_failure_and_both_failed_keeps_the_floor`
  - `test_both_policies_mix_with_exact_propensities_and_the_decider_is_advice`
  - `test_the_seed_reproduces_the_draw`
  - `test_with_no_model_the_numeric_policy_serves_with_stop_in_every_support`
- [tests/test_ro5_checks.py](../../../../../../tests/test_ro5_checks.py) — direct import
  - `test_the_check_takes_the_first_practice_slot_outside_the_mix_with_no_label`
- [tests/test_ro5_landing.py](../../../../../../tests/test_ro5_landing.py) — direct import
  - `test_r4_the_coin_is_not_drawn_before_any_active_minute_of_the_session`
  - `test_r5_1_at_the_tag_fg1s_gate_is_the_two_policy_mix_with_its_trace`
  - `test_r8_each_arm_can_be_drawn_with_its_logged_probability_and_no_intervention_serves_no_probe`
- [tests/test_ro5_stop_coin.py](../../../../../../tests/test_ro5_stop_coin.py) — direct import
  - `test_serving_records_each_coin_with_its_exact_probability_and_availability`
- [tests/test_te3b_offers.py](../../../../../../tests/test_te3b_offers.py) — direct import
  - `test_g3_mu_recomputes_with_an_offer_in_the_support_on_every_path`

## Modification guidance

- Make changes here when the responsibility remains mix within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

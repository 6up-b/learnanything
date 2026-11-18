---
title: "learnloop.router_objective_switches"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective_switches.py"
source_paths:
  - "src/learnloop/router_objective_switches.py"
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
  - "learnloop.router_objective_switches module"
  - "src/learnloop/router_objective_switches.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.router_objective_switches`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective_switches` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Configuration gates and parameters for the objective router and daily plan.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py) |
| Source lines | 311 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `objective_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 15) — RO4 (§8.3): the objective serves: ``[router_objective] enabled``.
- `objective_scores_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 23) — RO4 (§8.3, §8.7): a comparison score can be formed: the objective serves AND RO0's receipts are on (with receipts off the objective serves and no score forms).
- `sensors_in_value_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 31) — RO4 (§8.4): the LLM's effect-slope correction enters the value (by hand off).
- `stop_coin_rate(config: Any) -> float` ([source](../../../../../src/learnloop/router_objective_switches.py), line 38) — RO5 §9 item 1: the stop coin's probability each way at a reversible boundary (0: no coin drawn).
- `check_mode(config: Any) -> tuple[str, float]` ([source](../../../../../src/learnloop/router_objective_switches.py), line 51) — RO5 §9 item 2: ``(mode, value)``: ``("embedded", checks per day)``, ``("rate", per topic per day)`` or ``("off", 0)``.
- `calibrated_weight_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 67) — RO5 §9 item 2 into §8.7: the randomized checks' comparison scores move ``w``.
- `pick_open_share(config: Any) -> float` ([source](../../../../../src/learnloop/router_objective_switches.py), line 75) — RO5 §9 item 6: the seeded share of misconception picks left open.
- `fitted_models_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 81) — RO5 §9 item 7: the rollouts read AD's fitted learning posterior and the combiner fed resolved checks.
- `learned_tail_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 88) — RO6 (§10): the numeric policy values its candidates with the learned tail's residual (the objective serving and ``[router_objective] learned_tail``).
- `followup_on(config: Any, key: str) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 96) — One part of the follow-up batch serves: the tag, the objective serving and its own ``[router_objective]`` switch ``key`` (default true).
- `monotone_combiner_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 104) — The follow-up batch's landing ruling R6: the memory model's combiner is monotone in ability by construction (``memory.FORM_MONOTONE``), in its prior and its fit: the tag, the objective serving and ``[router_objective] monotone_combiner`` (a structural kill switch, default true);…
- `followup_generator_switches(config: Any) -> dict[str, bool]` ([source](../../../../../src/learnloop/router_objective_switches.py), line 124) — R8: each of :data:`FOLLOWUP_GENERATOR_SWITCHES` as it serves (:func:`followup_on`), and slip or gap SG2's.
- `followup_switch_snapshot(config: Any) -> dict[str, bool]` ([source](../../../../../src/learnloop/router_objective_switches.py), line 162) — R12: each of :data:`FOLLOWUP_SWITCHES` as it serves.
- `lesson_offers_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 168) — Teacher TE3b: lesson offers are candidates of the router objective, lesson minutes count on its clock and LOs with a pending lesson check join its population: the objective serving and TE1b's suggestions on (the router and its decision log, lessons able to open).
- `failure_share_to_other_policy_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 181) — IH5: a failed policy's share of the objective's mix goes to the other policy, not staged: the tag, the objective serving and ``[router_objective] failure_share_to_other_policy`` (default true).
- `lessons_compete_with_followups_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 191) — IH2 (spec_instruct_handoff_v1 §5, the same unreleased tag as IH5): a lesson offer and a follow-up compete in one logged decision wherever a lesson is available: the tag, lesson offers on (:func:`lesson_offers_on`: the objective serving and TE1b's suggestions) and ``[router_objec…
- `learner_preferences_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 202) — IH3 (spec_instruct_handoff_v1 §6, the same unreleased tag as IH5): the learner may name what would help and have it served: the tag and ``[router_objective] learner_preferences`` (default true).
- `workbench_is_open_item_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 212) — IH6 (spec_instruct_handoff_v1 §7b, the same unreleased tag as IH5): an open workbench is an open item for the plan: the tag, the workbench itself on (off, nothing can resume the problem, so it holds nothing) and ``[router_objective] workbench_is_open_item`` (default true).
- `lesson_sources_follow_diagnosis_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 224) — IH7 (spec_instruct_handoff_v1 §7c, the same unreleased tag as IH5): a lesson opened from an offer or a suggestion reads the sections matching the diagnosed confusion beside the topic's linked ones: the tag and ``[router_objective] lesson_sources_follow_diagnosis`` (default true).
- `lesson_candidate_after_cold_miss_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 234) — The owner's decision 4 of Nov 9 (spec_instruct_handoff_v1 §8, the same unreleased tag as IH5): a topic with a missed cold check since its last lesson is a lesson candidate, with no threshold on the miss's size, count or error type (the router, the diagnosis and the teacher then…
- `preferences_inform_router_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 246) — IH4 (spec_instruct_handoff_v1 §7, the same unreleased tag as IH5): what the learner said would help informs the objective's non-LLM parts and its LLM card: the tag, the objective serving and ``[router_objective] preferences_inform_router`` (default true).
- `miss_cause_sensor_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 257) — SG1 (spec_slip_vs_gap_v1 §3): each candidate topic's ``miss_cause`` sensor is frozen in the objective's trace, on a lesson offer's card record and on the LLM policy's card: the tag, the objective serving and ``[router_objective] miss_cause_sensor`` (default true).
- `miss_cause_in_value_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 267) — SG2 (spec_slip_vs_gap_v1 §3): the numeric policy's lesson and repair effect slopes split by the miss's cause, with the surprise calibrating ``p_gap``: SG1 on (it reads SG1's sensor) and ``[router_objective] miss_cause_in_value`` (default true).

### Module constants

- `CHECKS_EMBEDDED` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 46)
- `CHECKS_RATE` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 47)
- `CHECKS_OFF` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 48)
- `FOLLOWUP_GENERATOR_SWITCHES` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 119)
- `FOLLOWUP_SWITCHES` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 137)
- `SEED_NEUTRAL_SWITCHES` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 143)
- `SEED_NEUTRAL_OBJECTIVE_KEYS` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 148)
- `SEED_NEUTRAL_IDENTITY_KEYS` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 149)
- `COMMON_DRAW_OBJECTIVE_KEYS` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 157)
- `COMMON_DRAW_IDENTITY_KEYS` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 158)
- `MISS_CAUSE_OFFER_KEY` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 159)

### Explicit exports

`__all__` declares:

- `CHECKS_EMBEDDED`
- `CHECKS_OFF`
- `CHECKS_RATE`
- `calibrated_weight_on`
- `check_mode`
- `fitted_models_on`
- `FOLLOWUP_GENERATOR_SWITCHES`
- `FOLLOWUP_SWITCHES`
- `SEED_NEUTRAL_IDENTITY_KEYS`
- `SEED_NEUTRAL_OBJECTIVE_KEYS`
- `SEED_NEUTRAL_SWITCHES`
- `followup_generator_switches`
- `followup_switch_snapshot`
- `failure_share_to_other_policy_on`
- `followup_on`
- `learner_preferences_on`
- `lessons_compete_with_followups_on`
- `lesson_offers_on`
- `monotone_combiner_on`
- `learned_tail_on`
- `pick_open_share`
- `stop_coin_rate`
- `workbench_is_open_item_on`
- `lesson_sources_follow_diagnosis_on`
- `lesson_candidate_after_cold_miss_on`
- `preferences_inform_router_on`
- `COMMON_DRAW_IDENTITY_KEYS`
- `COMMON_DRAW_OBJECTIVE_KEYS`
- `MISS_CAUSE_OFFER_KEY`
- `miss_cause_in_value_on`
- `miss_cause_sensor_on`
- `objective_on`
- `objective_scores_on`
- `sensors_in_value_on`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/reading_cache|learnloop.adaptive_difficulty.reading_cache]] — imports `followup_on`; statically calls `followup_on`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `CHECKS_OFF`, `check_mode`, `lessons_compete_with_followups_on`, `workbench_is_open_item_on`; statically calls `check_mode`, `lessons_compete_with_followups_on`, `workbench_is_open_item_on`
- [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]] — imports `learner_preferences_on`, `preferences_inform_router_on`; statically calls `learner_preferences_on`, `preferences_inform_router_on`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `MISS_CAUSE_OFFER_KEY`, `lesson_offers_on`, `lessons_compete_with_followups_on`, `miss_cause_sensor_on`, `preferences_inform_router_on`; statically calls `lesson_offers_on`, `lessons_compete_with_followups_on`, `miss_cause_sensor_on`, `preferences_inform_router_on`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `lesson_candidate_after_cold_miss_on`, `lesson_offers_on`; statically calls `lesson_candidate_after_cold_miss_on`, `lesson_offers_on`
- [[Reference/Modules/learnloop/daily_plan/objective_card|learnloop.daily_plan.objective_card]] — imports `miss_cause_sensor_on`, `preferences_inform_router_on`; statically calls `miss_cause_sensor_on`, `preferences_inform_router_on`
- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `CHECKS_OFF`, `COMMON_DRAW_IDENTITY_KEYS`, `COMMON_DRAW_OBJECTIVE_KEYS`, `MISS_CAUSE_OFFER_KEY`, `SEED_NEUTRAL_IDENTITY_KEYS`, `SEED_NEUTRAL_OBJECTIVE_KEYS`, `SEED_NEUTRAL_SWITCHES`, `calibrated_weight_on`, `check_mode`, `failure_share_to_other_policy_on`, `followup_generator_switches`, `followup_on`, `followup_switch_snapshot`, `learned_tail_on`, `lessons_compete_with_followups_on`, `miss_cause_in_value_on`, `miss_cause_sensor_on`, `objective_scores_on`, `preferences_inform_router_on`, `stop_coin_rate`; statically calls `calibrated_weight_on`, `check_mode`, `failure_share_to_other_policy_on`, `followup_generator_switches`, `followup_on`, `followup_switch_snapshot`, `learned_tail_on`, `lessons_compete_with_followups_on`, `miss_cause_in_value_on`, `miss_cause_sensor_on`, `objective_scores_on`, `preferences_inform_router_on`, `stop_coin_rate`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `fitted_models_on`, `followup_on`, `lesson_offers_on`, `miss_cause_in_value_on`, `miss_cause_sensor_on`, `monotone_combiner_on`, `stop_coin_rate`; statically calls `fitted_models_on`, `followup_on`, `lesson_offers_on`, `miss_cause_in_value_on`, `miss_cause_sensor_on`, `monotone_combiner_on`, `stop_coin_rate`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `lesson_offers_on`, `lessons_compete_with_followups_on`, `objective_on`; statically calls `lesson_offers_on`, `lessons_compete_with_followups_on`, `objective_on`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `objective_on`; statically calls `objective_on`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `pick_open_share`; statically calls `pick_open_share`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `objective_on`; statically calls `objective_on`
- [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] — imports `miss_cause_sensor_on`, `preferences_inform_router_on`; statically calls `miss_cause_sensor_on`, `preferences_inform_router_on`
- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `CHECKS_EMBEDDED`, `CHECKS_OFF`, `check_mode`; statically calls `check_mode`
- [[Reference/Modules/learnloop/router_objective/preferences|learnloop.router_objective.preferences]] — imports `preferences_inform_router_on`; statically calls `preferences_inform_router_on`
- [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] — imports `lesson_offers_on`; statically calls `lesson_offers_on`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `followup_on`, `lesson_offers_on`; statically calls `followup_on`, `lesson_offers_on`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `lesson_sources_follow_diagnosis_on`; statically calls `lesson_sources_follow_diagnosis_on`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `workbench_is_open_item_on`; statically calls `workbench_is_open_item_on`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `objective_on`; statically calls `objective_on`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/reading_cache|learnloop.adaptive_difficulty.reading_cache]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]], [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] and 15 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/successor_switches.py](../../../../../tests/successor_switches.py) — direct import
- [tests/test_ih2_lessons_compete.py](../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_off_or_below_the_tag_a_probe_withdraws_the_offer_as_the_predecessor`
  - `test_the_switch_defaults_on_is_classified_and_names_itself_in_the_prefetch_key`
- [tests/test_ih3_learner_preferences.py](../../../../../tests/test_ih3_learner_preferences.py) — direct import
  - `test_below_the_tag_the_switch_does_nothing`
  - `test_with_the_switch_off_there_is_no_link_and_nothing_is_written`
- [tests/test_ih4_preferences_inform_router.py](../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
  - `test_staged_reads_nothing`
  - `test_the_gate_reads_off_below_the_tag_switched_off_and_with_the_objective_off`
- [tests/test_ih5_successor.py](../../../../../tests/test_ih5_successor.py) — direct import
  - `test_switch_off_or_below_the_tag_the_mix_is_the_predecessors_exactly`
  - `test_the_gate_reads_off_switched_off_and_with_the_objective_off`
- [tests/test_ih6_workbench_open_item.py](../../../../../tests/test_ih6_workbench_open_item.py) — direct import
  - `test_the_gate_reads_the_tag_the_switch_and_the_workbench`
  - `test_the_switch_is_not_in_the_prefetch_key_so_it_moves_no_seed`
- [tests/test_ih7_lesson_sources_follow_diagnosis.py](../../../../../tests/test_ih7_lesson_sources_follow_diagnosis.py) — direct import
  - `test_the_switch_needs_the_tag_and_defaults_on`
- [tests/test_ih_lesson_candidate_after_cold_miss.py](../../../../../tests/test_ih_lesson_candidate_after_cold_miss.py) — direct import
  - `test_the_switch_is_not_in_the_prefetch_key_and_moves_no_seed_by_itself`
  - `test_the_switch_needs_the_tag_defaults_on_and_is_registered`
- [tests/test_ro4_successor.py](../../../../../tests/test_ro4_successor.py) — direct import
  - `test_the_gates_read_off_and_below_the_tag`
- [tests/test_ro5_checks.py](../../../../../tests/test_ro5_checks.py) — direct import
  - `test_the_draw_is_uniform_over_topics_across_dates`
  - `test_the_same_date_and_eligible_set_draw_the_same_and_r_is_exact`
- [tests/test_ro5_successor.py](../../../../../tests/test_ro5_successor.py) — direct import
  - `test_the_gates_read_off_below_the_tag_and_at_zero`
- [tests/test_ro6_successor.py](../../../../../tests/test_ro6_successor.py) — direct import
  - `test_the_gate_reads_off_below_the_tag_switched_off_and_with_the_objective_off`
- [tests/test_rofu_generator_switches.py](../../../../../tests/test_rofu_generator_switches.py) — direct import
  - `test_at_the_defaults_the_payload_is_stable_across_decisions_and_is_the_one_served`
  - `test_flipping_a_serving_switch_is_a_new_generator_version`
- [tests/test_rofu_successor.py](../../../../../tests/test_rofu_successor.py) — direct import
  - `test_each_part_reads_off_below_the_tag_switched_off_and_with_the_objective_off`
- [tests/test_rofu_switch_key.py](../../../../../tests/test_rofu_switch_key.py) — direct import
  - `test_flipping_a_switch_between_prefetch_and_serve_starts_a_new_job`
  - `test_the_key_names_the_switches_at_every_tag_a_vault_can_hold`
- [tests/test_rospeed2_connections.py](../../../../../tests/test_rospeed2_connections.py) — direct import
  - `test_r2_the_numeric_seed_is_mains_whatever_the_speed_switches`
  - `test_the_pool_and_the_held_map_follow_their_switches`
- [tests/test_rospeed_ad_link.py](../../../../../tests/test_rospeed_ad_link.py) — direct import
  - `test_the_switch_reaches_every_rollout_from_the_config`
- [tests/test_sg_slip_vs_gap.py](../../../../../tests/test_sg_slip_vs_gap.py) — direct import
  - `test_off_and_below_the_tag_the_card_is_the_predecessors`
  - `test_the_gates_need_the_tag_the_objective_and_sg2_needs_sg1`
- [tests/test_sg_successor.py](../../../../../tests/test_sg_successor.py) — direct import
  - `test_sg2_is_in_ro6s_generator_payload_and_sg1_is_not`
  - `test_the_prefetch_key_names_both_switches_as_they_serve`
- [tests/test_te3b_successor.py](../../../../../tests/test_te3b_successor.py) — direct import
  - `test_the_gate_reads_on_and_off_with_the_objective_or_lessons_off`

## Modification guidance

- Make changes here when the responsibility remains router objective switches within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

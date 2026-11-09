---
title: "learnloop.router_objective_switches"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective_switches.py"
source_paths:
  - "src/learnloop/router_objective_switches.py"
source_commit: "e79907584a31e88ee6c1f20792f2dc9642a671d3"
source_commit_timestamp: "2026-11-09T03:56:19-05:00"
source_worktree_state: "clean"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective_switches` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Router objective RO1's switches and the availability time (spec_router_objective_v1 §5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py) |
| Source lines | 458 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e79907584a31e88ee6c1f20792f2dc9642a671d3` |
| Commit timestamp | `2026-11-09T03:56:19-05:00` |

## Public API

- `interval_factor_removed(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 70) — §5.1: True when the FSRS interval carries no surprise factor (the tag and the switch).
- `available_at_reads_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 78) — §5.3: True when decision-time attempt reads use the availability time.
- `self_report_not_validated_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 85) — §5.4: True when a learner's pick is not counted as validated evidence.
- `available_at(row: Mapping[str, Any]) -> str | None` ([source](../../../../../src/learnloop/router_objective_switches.py), line 92) — ``coalesce(received_at, created_at)``: when the attempt became known to the system.
- `attempt_time_sql(config: Any, connection: Any=None, *, alias: str | None=None) -> str` ([source](../../../../../src/learnloop/router_objective_switches.py), line 105) — THE availability predicate's SQL form: the expression a decision-time read of ``practice_attempts`` compares its time cutoff with (``<expr> < ?``, ``<expr> <= ?``).
- `known_at(row: Mapping[str, Any], config: Any) -> str | None` ([source](../../../../../src/learnloop/router_objective_switches.py), line 127) — THE availability predicate over a loaded ``practice_attempts`` row: the time a decision-time cutoff compares with.
- `validated_resolution_ids(ids: Iterable[Any], config: Any) -> list[Any]` ([source](../../../../../src/learnloop/router_objective_switches.py), line 142) — The resolution ids that count as validated evidence: all of them below the tag or with the switch off; otherwise all but a learner's own reports (§5.4).
- `objective_tag(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 152) — RO4 (§8): the vault is at the router objective's successor (mvp-0.47) or later.
- `objective_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 159) — RO4 (§8.3): the objective serves: the tag and ``[router_objective] enabled``.
- `objective_scores_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 167) — RO4 (§8.3, §8.7): a comparison score can be formed: the objective serves AND RO0's receipts are on (with receipts off the objective serves and no score forms).
- `sensors_in_value_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 175) — RO4 (§8.4): the LLM's effect-slope correction enters the value (by hand off).
- `calibration_tag(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 182) — RO5 (§9): the vault is at the calibration successor (mvp-0.48) or later.
- `stop_coin_rate(config: Any) -> float` ([source](../../../../../src/learnloop/router_objective_switches.py), line 189) — RO5 §9 item 1: the stop coin's probability each way at a reversible boundary (0: no coin drawn).
- `check_mode(config: Any) -> tuple[str, float]` ([source](../../../../../src/learnloop/router_objective_switches.py), line 202) — RO5 §9 item 2: ``(mode, value)``: ``("embedded", checks per day)``, ``("rate", per topic per day)`` or ``("off", 0)``.
- `calibrated_weight_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 218) — RO5 §9 item 2 into §8.7: the randomized checks' comparison scores move ``w``.
- `pick_open_share(config: Any) -> float` ([source](../../../../../src/learnloop/router_objective_switches.py), line 226) — RO5 §9 item 6: the seeded share of misconception picks left open (0 below the tag).
- `fitted_models_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 234) — RO5 §9 item 7: the rollouts read AD's fitted learning posterior and the combiner fed resolved checks.
- `learned_tail_tag(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 241) — RO6 (§10): the vault is at the learned tail's successor (mvp-0.49) or later.
- `learned_tail_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 248) — RO6 (§10): the numeric policy values its candidates with the learned tail's residual (the tag, the objective serving and ``[router_objective] learned_tail``).
- `followups_tag(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 257) — The router objective's follow-up batch: the vault is at its successor (mvp-0.50) or later.
- `followup_on(config: Any, key: str) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 264) — One part of the follow-up batch serves: the tag, the objective serving and its own ``[router_objective]`` switch ``key`` (default true).
- `monotone_combiner_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 272) — The follow-up batch's landing ruling R6: the memory model's combiner is monotone in ability by construction (``memory.FORM_MONOTONE``), in its prior and its fit: the tag, the objective serving and ``[router_objective] monotone_combiner`` (a structural kill switch, default true);…
- `followup_generator_switches(config: Any) -> dict[str, bool] | None` ([source](../../../../../src/learnloop/router_objective_switches.py), line 292) — R8: each of :data:`FOLLOWUP_GENERATOR_SWITCHES` as it serves (:func:`followup_on`) at the batch's tag; None below it, so a predecessor's generator payload (and its trace) keeps its bytes.
- `followup_switch_snapshot(config: Any) -> dict[str, bool] | None` ([source](../../../../../src/learnloop/router_objective_switches.py), line 313) — R12: each of :data:`FOLLOWUP_SWITCHES` as it serves, at the batch's tag; None below it (the boundary key keeps its predecessor's bytes).
- `lesson_offers_tag(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 322) — Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): the vault is at the lesson offers' successor (mvp-0.53) or later.
- `lesson_offers_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 330) — Teacher TE3b: lesson offers are candidates of the router objective, lesson minutes count on its clock and LOs with a pending lesson check join its population: the tag, the objective serving, TE1b's suggestions on (``router.lesson_suggestions.enabled`` with the router and its dec…
- `failure_share_tag(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 346) — Instruct hand-off IH5 (spec_instruct_handoff_v1 §7a): the vault is at the failure-share successor (mvp-0.55) or later.
- `failure_share_to_other_policy_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 354) — IH5: a failed policy's share of the objective's mix goes to the other policy, not staged: the tag, the objective serving and ``[router_objective] failure_share_to_other_policy`` (default true).
- `lessons_compete_with_followups_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 364) — IH2 (spec_instruct_handoff_v1 §5, the same unreleased tag as IH5): a lesson offer and a follow-up compete in one logged decision wherever a lesson is available: the tag, lesson offers on (:func:`lesson_offers_on`: the objective serving and TE1b's suggestions) and ``[router_objec…
- `learner_preferences_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 375) — IH3 (spec_instruct_handoff_v1 §6, the same unreleased tag as IH5): the learner may name what would help and have it served: the tag and ``[router_objective] learner_preferences`` (default true).
- `workbench_is_open_item_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 385) — IH6 (spec_instruct_handoff_v1 §7b, the same unreleased tag as IH5): an open workbench is an open item for the plan: the tag, the workbench itself on (off, nothing can resume the problem, so it holds nothing) and ``[router_objective] workbench_is_open_item`` (default true).
- `lesson_sources_follow_diagnosis_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 397) — IH7 (spec_instruct_handoff_v1 §7c, the same unreleased tag as IH5): a lesson opened from an offer or a suggestion reads the sections matching the diagnosed confusion beside the topic's linked ones: the tag and ``[router_objective] lesson_sources_follow_diagnosis`` (default true).
- `projection_switches(config: Any) -> dict[str, bool]` ([source](../../../../../src/learnloop/router_objective_switches.py), line 407) — What a whole-vault rebuild derived persisted due dates under (§5.5): whether the factor was removed.

### Module constants

- `LEARNER_REPORT_PREFIX` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 51)
- `AVAILABLE_AT_SQL` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 54)
- `RECEIVED_AT_RECORDED` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 58)
- `RECEIVED_AT_INFERRED` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 59)
- `INTERVAL_FACTOR_SNAPSHOT_KEY` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 62)
- `CHECKS_EMBEDDED` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 197)
- `CHECKS_RATE` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 198)
- `CHECKS_OFF` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 199)
- `FOLLOWUP_GENERATOR_SWITCHES` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 287)
- `FOLLOWUP_SWITCHES` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 304)
- `SEED_NEUTRAL_SWITCHES` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 310)

### Explicit exports

`__all__` declares:

- `AVAILABLE_AT_SQL`
- `INTERVAL_FACTOR_SNAPSHOT_KEY`
- `LEARNER_REPORT_PREFIX`
- `RECEIVED_AT_INFERRED`
- `RECEIVED_AT_RECORDED`
- `attempt_time_sql`
- `available_at`
- `CHECKS_EMBEDDED`
- `CHECKS_OFF`
- `CHECKS_RATE`
- `available_at_reads_on`
- `calibrated_weight_on`
- `calibration_tag`
- `check_mode`
- `fitted_models_on`
- `FOLLOWUP_GENERATOR_SWITCHES`
- `FOLLOWUP_SWITCHES`
- `SEED_NEUTRAL_SWITCHES`
- `followup_generator_switches`
- `followup_switch_snapshot`
- `failure_share_tag`
- `failure_share_to_other_policy_on`
- `followup_on`
- `learner_preferences_on`
- `lessons_compete_with_followups_on`
- `lesson_offers_on`
- `lesson_offers_tag`
- `monotone_combiner_on`
- `followups_tag`
- `interval_factor_removed`
- `learned_tail_on`
- `learned_tail_tag`
- `pick_open_share`
- `stop_coin_rate`
- `workbench_is_open_item_on`
- `lesson_sources_follow_diagnosis_on`
- `known_at`
- `objective_on`
- `objective_scores_on`
- `objective_tag`
- `projection_switches`
- `sensors_in_value_on`
- `self_report_not_validated_on`
- `validated_resolution_ids`

## Internal implementation anchors

- `_at_tag(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 65)
- `_has_received_at(connection: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 138)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/history_card|learnloop.adaptive_difficulty.history_card]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `known_at`; statically calls `known_at`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading_cache|learnloop.adaptive_difficulty.reading_cache]] — imports `followup_on`; statically calls `followup_on`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `interval_factor_removed`; statically calls `interval_factor_removed`
- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `calibration_tag`, `learned_tail_tag`, `lesson_offers_tag`; statically calls `calibration_tag`, `learned_tail_tag`, `lesson_offers_tag`
- [[Reference/Modules/learnloop/confidence_events|learnloop.confidence_events]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `CHECKS_OFF`, `check_mode`, `lessons_compete_with_followups_on`, `workbench_is_open_item_on`; statically calls `check_mode`, `lessons_compete_with_followups_on`, `workbench_is_open_item_on`
- [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]] — imports `learner_preferences_on`; statically calls `learner_preferences_on`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `lesson_offers_on`; statically calls `lesson_offers_on`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `lesson_offers_on`; statically calls `lesson_offers_on`
- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `CHECKS_OFF`, `SEED_NEUTRAL_SWITCHES`, `calibrated_weight_on`, `calibration_tag`, `check_mode`, `failure_share_tag`, `failure_share_to_other_policy_on`, `followup_generator_switches`, `followup_on`, `followup_switch_snapshot`, `learned_tail_on`, `lessons_compete_with_followups_on`, `objective_scores_on`, `stop_coin_rate`; statically calls `calibrated_weight_on`, `calibration_tag`, `check_mode`, `failure_share_tag`, `failure_share_to_other_policy_on`, `followup_generator_switches`, `followup_on`, `followup_switch_snapshot`, `learned_tail_on`, `lessons_compete_with_followups_on`, `objective_scores_on`, `stop_coin_rate`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `fitted_models_on`, `followup_on`, `followups_tag`, `known_at`, `lesson_offers_on`, `monotone_combiner_on`, `stop_coin_rate`; statically calls `fitted_models_on`, `followup_on`, `followups_tag`, `known_at`, `lesson_offers_on`, `monotone_combiner_on`, `stop_coin_rate`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `lesson_offers_on`, `lessons_compete_with_followups_on`, `objective_on`; statically calls `lesson_offers_on`, `lessons_compete_with_followups_on`, `objective_on`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `attempt_time_sql`, `objective_on`; statically calls `attempt_time_sql`, `objective_on`
- [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `pick_open_share`; statically calls `pick_open_share`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `attempt_time_sql`, `known_at`, `validated_resolution_ids`; statically calls `attempt_time_sql`, `known_at`, `validated_resolution_ids`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `calibration_tag`; statically calls `calibration_tag`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `objective_on`; statically calls `objective_on`
- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] — imports `calibration_tag`; statically calls `calibration_tag`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `INTERVAL_FACTOR_SNAPSHOT_KEY`, `projection_switches`; statically calls `projection_switches`
- [[Reference/Modules/learnloop/reader_learner_state|learnloop.reader_learner_state]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `CHECKS_EMBEDDED`, `CHECKS_OFF`, `check_mode`; statically calls `check_mode`
- [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] — imports `attempt_time_sql`, `lesson_offers_on`; statically calls `attempt_time_sql`, `lesson_offers_on`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `followup_on`, `known_at`, `lesson_offers_on`; statically calls `followup_on`, `known_at`, `lesson_offers_on`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `projection_switches`; statically calls `projection_switches`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `projection_switches`; statically calls `projection_switches`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `lesson_sources_follow_diagnosis_on`; statically calls `lesson_sources_follow_diagnosis_on`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `workbench_is_open_item_on`; statically calls `workbench_is_open_item_on`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `objective_on`; statically calls `objective_on`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `FAILURE_SHARE_VERSIONS`, `INTERVAL_FACTOR_VERSIONS`, `LESSON_OFFERS_VERSIONS`, `ROUTER_CALIBRATION_VERSIONS`, `ROUTER_FOLLOWUPS_VERSIONS`, `ROUTER_LEARNED_TAIL_VERSIONS`, `ROUTER_OBJECTIVE_VERSIONS`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/history_card|learnloop.adaptive_difficulty.history_card]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]], [[Reference/Modules/learnloop/adaptive_difficulty/reading_cache|learnloop.adaptive_difficulty.reading_cache]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] and 26 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ih2_lessons_compete.py](../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_off_or_below_the_tag_a_probe_withdraws_the_offer_as_the_predecessor`
  - `test_the_switch_defaults_on_is_classified_and_names_itself_in_the_prefetch_key`
- [tests/test_ih3_learner_preferences.py](../../../../../tests/test_ih3_learner_preferences.py) — direct import
  - `test_below_the_tag_the_switch_does_nothing`
  - `test_with_the_switch_off_there_is_no_link_and_nothing_is_written`
- [tests/test_ih5_successor.py](../../../../../tests/test_ih5_successor.py) — direct import
  - `test_switch_off_or_below_the_tag_the_mix_is_the_predecessors_exactly`
  - `test_the_gate_reads_off_below_the_tag_switched_off_and_with_the_objective_off`
- [tests/test_ih6_workbench_open_item.py](../../../../../tests/test_ih6_workbench_open_item.py) — direct import
  - `test_the_gate_reads_the_tag_the_switch_and_the_workbench`
  - `test_the_switch_is_not_in_the_prefetch_key_so_it_moves_no_seed`
- [tests/test_ih7_lesson_sources_follow_diagnosis.py](../../../../../tests/test_ih7_lesson_sources_follow_diagnosis.py) — direct import
  - `test_the_switch_needs_the_tag_and_defaults_on`
- [tests/test_ro1_availability.py](../../../../../tests/test_ro1_availability.py) — direct import
  - `test_available_at_is_received_at_else_created_at`
  - `test_exam_seeding_records_the_import_time_and_replay_keeps_it`
  - `test_the_router_cards_decision_time_reads_use_availability_at_the_tag`
- [tests/test_ro1_availability_reads.py](../../../../../tests/test_ro1_availability_reads.py) — direct import
  - `test_the_predicate_is_the_predecessors_column_below_the_tag_or_switched_off`
- [tests/test_ro1_interval_factor.py](../../../../../tests/test_ro1_interval_factor.py) — direct import
  - `test_the_gate_is_the_tag_and_the_switch`
- [tests/test_ro1_projection.py](../../../../../tests/test_ro1_projection.py) — direct import
  - `test_every_switch_combination_moves_exactly_its_own_part`
  - `test_every_whole_vault_rebuild_records_the_factors_switch`
- [tests/test_ro1_self_report.py](../../../../../tests/test_ro1_self_report.py) — direct import
  - `test_a_probes_observation_still_counts_and_only_reports_are_dropped`
- [tests/test_ro1_successor.py](../../../../../tests/test_ro1_successor.py) — direct import
  - `test_each_switch_is_classified_and_reads_off_or_below_the_tag`
- [tests/test_ro4_successor.py](../../../../../tests/test_ro4_successor.py) — direct import
  - `test_the_gates_read_off_and_below_the_tag`
- [tests/test_ro5_calibration.py](../../../../../tests/test_ro5_calibration.py) — direct import
  - `test_below_the_tag_the_cli_report_has_no_calibration_section`
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
- [tests/test_rofu_learning.py](../../../../../tests/test_rofu_learning.py) — direct import
  - `test_the_join_rows_count_one_outcome_once_per_protocol_and_only_when_known`
- [tests/test_rofu_successor.py](../../../../../tests/test_rofu_successor.py) — direct import
  - `test_each_part_reads_off_below_the_tag_switched_off_and_with_the_objective_off`
- [tests/test_rofu_switch_key.py](../../../../../tests/test_rofu_switch_key.py) — direct import
  - `test_flipping_a_switch_between_prefetch_and_serve_starts_a_new_job`
- [tests/test_rospeed2_connections.py](../../../../../tests/test_rospeed2_connections.py) — direct import
  - `test_r2_the_numeric_seed_is_mains_whatever_the_speed_switches`
  - `test_the_pool_and_the_held_map_follow_their_switches`
- [tests/test_rospeed_ad_link.py](../../../../../tests/test_rospeed_ad_link.py) — direct import
  - `test_the_switch_reaches_every_rollout_from_the_config`
- [tests/test_te3b_successor.py](../../../../../tests/test_te3b_successor.py) — direct import
  - `test_the_gate_reads_off_below_the_tag_switched_off_and_with_suggestions_or_the_objective_off`

## Modification guidance

- Make changes here when the responsibility remains router objective switches within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

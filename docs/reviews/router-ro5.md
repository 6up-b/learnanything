# Router objective RO5: return and calibration (`router/ro5-calibration`)

Spec: `docs/specs/spec_router_objective_v1.md` §9 (as built: §9.1), §12. Base `59a0de9832` (RO4's branch: mvp-0.47,
migration 246; RO4 is landing now and this branch merges main after it). Successor **mvp-0.48**
(`ROUTER_CALIBRATION_ALGORITHM_VERSION`), rechecked at landing. **No migration**: every arm writes the existing
`policy_experiment_assignments` (migration 098) under its own `experiment_id`. Fakes only: no paid call was made in this
stage, no real request was sent, no owner vault was opened, no tracked working vault was touched.

## What exists

| Part | Where |
|---|---|
| Successor, upgrade (projection activation, journalled), defaults snapshot, the keys and gates | `algorithm_versions.py`, `router_calibration_upgrade.py`, `config/schema.py` (`RouterObjectiveConfig`: `stop_coin`, `check_rate`, `embedded_checks_per_day`, `pick_open_share`, `kappa_prior_log_sd`, `return_slope_prior_sd`, `goal_transfer_prior_sd`, `fitted_models`), `config/template.py`, `router_objective_switches` (`calibration_tag`, `stop_coin_rate`, `check_mode`, `pick_open_share`, `fitted_models_on`), `params/parameter_registry.py` |
| The arms' rows (one place, `experiment_id`s `ro5_stop_coin:v1`, `ro5_randomized_check:v1`, `ro5_open_pick:v1`) | `router_objective/assignments.py`, `db/stores/router_objective.insert_assignment` |
| §9 item 1: the stop coin, κ0's hand-over, the return model | `router_objective/stop_coin.py`; `daily_plan/objective_chooser.py` (`_decide_objective`, `_availability`, `_posterior_price`); `router_objective/value.py` (`Inputs.return_slope`, the stop row's `return_effect`); `daily_plan/objective_inputs._return_model`; the coin's row written by the `plan_block` logger (`daily_plan/engine._log_plan_decision`) |
| §9 item 2: randomized checks and their scores | `router_objective/checks.py` (draw, placement, resolution, completion gap, `r`); `daily_plan/engine.py` (`_draw_randomized_checks`, `_place_randomized_checks`, the `item_planned` receipt's `ro5_check`); `daily_plan/objective_inputs.py` (`population`, `check_eligible_items`, `check_sensors`); `router_objective/scores.py`; `objective_chooser.current_weight`; `router/outcomes.py` and `daily_plan/view.py` (the check's origin) |
| §9 item 3: the goal-date read | `router_objective/goal_read.py` |
| §9 item 4: `α` provisional | `router/outcomes.py` (`S_ALPHA_STATUS`, docstring) |
| §9 item 5: the floor contrast | `router_objective/calibration_report.floor_section` |
| §9 item 6: open picks | `router_objective/picks.py`, `diagnosis/causal_attribution.record_unresolved_cause_self_report`, `ops/capture_report.py` (`open_picks`) |
| §9 item 7: RO4's follow-ups | `adaptive_difficulty/readiness.decision_state_fields(learning_moments=True)`, `objective_inputs._learning`, `_combiner` |
| The report | `router_objective/calibration_report.py`, `learnloop router objective-report` (its `calibration` section at the tag) |
| Specs (§13) | `spec_router_objective_v1.md` §9.1 and status; `spec_action_router_v1.md` (§7.3's RO5 note, §15.2's provisional `α`); `spec_daily_loop_v1.md` (the coin and the embedded check in the frame) |

## For the owner before landing: what it costs and how it is enabled

- **Enabled at the tag by default**, where RO4's objective serves. `learnloop upgrade` (default target) moves a vault from
  mvp-0.47; nothing recorded changes. Each arm off, `stop_coin = 0`, `check_rate = "off"`, `pick_open_share = 0`, with
  `fitted_models = false`, serves mvp-0.47 exactly (tested against mvp-0.47 with the draw and the numeric policy's seed
  pinned, `tests/test_ro5_stop_coin.py::test_every_arm_off_at_the_tag_is_mvp_047_exactly`).
- **Paid routes: RO5 adds no model request.** No call per day. The checks raise generation needs through the existing
  path (`intervention_needs`, pending): nothing generates them until the owner runs `learnloop generate-diagnostics`
  (the existing paid generator, its own caps). On the synthetic first week: **2 needs raised** (topics with no unseen
  item), none generated.
- **Learner minutes** (the arms' declared prices; the report shows them per day): the coin's accepted randomized offers
  forgo at most the plan's suggested remainder (an upper bound), its presented blocks add their estimate; an embedded
  check adds its estimate minus the replaced question's (0.0 on the synthetic vault, equal estimates); open picks cost
  no minutes (they may change repair targeting, which is what they measure).
- **Latency**: the day's draw runs once at its first boundary (eligibility over the population: one read of attempts,
  reveals, help rows and the routine exclusions); a placement adds one AD read for the topic's frozen sensors; the
  weight's scores parse each closed trace once per decision (linear in the traces whose windows closed; no cache at this
  version, see open items).

## Choices where the spec was open, or the code had moved (the smallest alternative, recorded)

1. **No migration, no new table.** Administration is the `item_planned` receipt's `ro5_check` entry (block, item,
   topic, `r`, the replaced item, net minutes, frozen sensors), and completion with its reasons is a versioned read
   (`ro5_check_resolver_v1`), so assignment, administration, completion and noncompletion are recorded apart without a
   schema change. `decision_id` stays NULL (its FK is to the P4 controller's decisions); the unit (router decision, check
   day/slot, factor) is in `unit_id`; `design = mrt_reversible` (the table's CHECK allows three designs).
2. **The coin's "both directions"**: `offer_stop` serves the stop offer; `present_next` overrides a stop the mix drew with
   a block drawn from `μ` restricted to the blocks (otherwise the mix's block stands). The router ledger's per-candidate
   probabilities are the served distribution; the trace keeps the mix's `μ`, so G3 recomputes it unchanged, and the §8.7
   score of a `policy`-arm decision uses `μ` (exact, given the coin's independence); forced decisions carry none.
3. **The coin at the first boundary.** "At a reversible block boundary" includes the session's first one, so an offer to
   stop can come before any block; in the synthetic week (where nobody presses "keep going") one such offer ended a day
   (25 minutes forgone, upper bound). The smallest change if the owner wants it: `stop_coin.eligible` also requiring the
   session's active minutes above zero.
4. **κ0's hand-over** (the brief's "say exactly how"): at the first randomized offer with a response, κ0 becomes
   `exp(E[log κ0 | offers])` with prior `N(log κ_s, 0.7²)`, `κ_s` the seed then in force, frozen. With no observation the
   posterior equals the seed, so the switch is continuous, and no count or threshold decides it: the regime changes when
   the posterior first holds randomized evidence. The likelihood is §8.6's logistic choice on the log ratio of gain to
   price (Luce's form, no scale constant). Availability is logged with each observation; its coefficient is not fitted
   (follow-up: one more grid axis).
5. **The return model enters `V` only with a randomized return**, and only with the coin on: before, it is the prior's
   mean (no effect), which is RO4's form exactly. Only today's session's gap moves (the tail's sessions run `m̄`).
6. **Checks only in the day's first session**: if the first session has no practice block (or no eligible item of the
   drawn topic in the plan's pool), the check is not administered that day (`not_administered:no_practice_slot`); a
   later session never takes it. A drawn item no longer eligible is redrawn within the topic among the pool's eligible
   items; the topic, the randomized unit, never changes.
7. **Days with no session**: no row is fabricated. The completion gap counts each such day since the first draw as that
   day's expected checks, uncompleted, and a use on such a day reads the last earlier draw's `r` (labelled).
8. **The check's identity**: plan origin `randomized_check` (AD's slot needs `chooser`, so AD never replaces it; the
   decision's logged items and `router_outcomes`' action binding skip it); the learner's view maps it to `chooser`.
9. **Help makes the check a non-success**: AD's category with any hint, or any help row on the item between its planning
   and its answer, counts as help.
10. **The goal-date read is reported, not yet a sensor inside `V`** (§9.1): both stages are versioned
    (`ro5_pool_calibration_v1`, `ro5_goal_transfer_v1`) and in `objective-report`. Smallest finish: add the read to the
    trace's `sensors` at the day's first decision and, when its transfer slope has a pair, scale the dated uses' `m⁰`.
11. **Goal type** has no field: `exam` when the goal sits an exam (`goal.exam.enabled`), else `dated`.
12. **Open picks' eligibility** is exactly "a pick that would resolve" (concrete candidate, trace consistent), computed
    before the report is written so the arm lands in the report's transaction; the factor's own seed makes a retried
    report draw the same arm, and an existing row is reused.
13. **`fitted_models` defaults true at the tag**, so AD's fitted moments of `γ` and the reading curve enter the rollouts
    even before any check resolves (each parameter its prior where AD has none). It is a kill switch apart from the
    arms; the arms-off equivalence test turns it off too.
14. **One code commit** (`84b890f02c`) for parts 0-7, because they share the plan engine, the chooser and its inputs and
    there is no interactive staging here; each part has its own test file, written against its interface first.
15. **`S`'s `α`** is labelled in code and docs; `router/outcomes.py` is not in the parameter registry's module inventory
    (adding it would require registering every numeric constant there), so it is not registered as a constant.

## Not built, and the smallest way to finish

- **The higher no-probe share (§9 item 5)**: not built; the report says "follow-up" because the floor's count is zero on a
  typical day of the synthetic vault (which has no follow-up workflows). On a real copy, rerun `objective-report` and
  build it only if the floor's median per active day is zero there too: one more arm in FG1's mixture with its own
  logged probability.
- **The leave-alone arm**: not built (§12 D1).
- **Availability as a covariate in κ0's likelihood**: logged, not fitted.
- **The score cache**: `current_weight` recomputes every closed window's score at each decision; once traces number in
  the thousands, cache closed scores by decision id (they never change once closed).
- **The goal-date read inside `V`**: see choice 10.

## The first week (copy-shaped synthetic vault)

`tests/test_ro5_calibration.py::test_the_first_week_on_a_copy_shaped_synthetic_vault`: six practised topics with four
unseen items each, both policies answering (fake LLM), the default arms, seven days with one (day 4) without a session,
nobody pressing "keep going".

| Day | Coin draws | Offers (accepted) | Next block over a drawn stop | Minutes forgone (upper) | Checks assigned / administered / completed | Check net minutes |
|---|---|---|---|---|---|---|
| 1 | 7 | 1 | 0 | 1.0 | 1 / 1 / 1 | 0.0 |
| 2 | 1 | 1 (at minute 0: the day ended) | 0 | 25.0 | 1 / 0 / 0 (no practice slot) | 0.0 |
| 3 | 5 | 0 | 0 | 0.0 | 1 / 1 / 1 | 0.0 |
| 4 | no session | | | | (counts toward the completion gap) | |
| 5 | 3 | 1 | 0 | 17.0 | 1 / 1 / 1 | 0.0 |
| 6 | 7 | 0 | 0 | 0.0 | 1 / 1 / 1 | 0.0 |
| 7 | 1 | 0 | 0 | 0.0 | 1 / 0 / 0 (no practice slot) | 0.0 |

Totals: 24 coin draws (3 `offer_stop`, 1 `present_next` that did not override a block, 20 `policy`); 6 checks assigned, 4
administered and completed, each displacing one targeted question; completion rate 4/7 = 0.57 with the day without a
session counted; a median of 7 eligible topics a day; 2 generation needs raised; 4 unseen items used. The return model
had 5 coin sessions (posterior mean of `b` 0.15, sd 0.27, synthetic gaps). **`w` did not move: 0.8**, with no closed
score: no 14-day window closes inside a week (and the posterior needs two 28-day bins of closed scores), by design. κ0
stayed the daily seed: no randomized offer received a response in the fake env (no `end` or `stop_response` receipt is
written there). The `no_intervention` floor had no decisions.

## The gate (this step)

Recorded at the end of the stage below; the full suite, the whole durability lane and the whole vitest run are the
landing gate's. No frontend or `src-tauri` file changed, so no npm, vitest or cargo step applies. No schema change, so
the DB reference was regenerated only for the configuration leaves (1159 to 1167) and validated.

## Files RO5 added or changed tests in (for the landing gate)

`tests/test_ro5_successor.py`, `test_ro5_stop_coin.py`, `test_ro5_checks.py`, `test_ro5_picks.py`,
`test_ro5_calibration.py`; pins moved in every upgrade and successor test that names the latest tag
(`test_ad23_successor.py`, `test_attempt_content_state_successor.py`, `test_batch3_landing.py`,
`test_cold_retry_reschedule.py`, `test_curriculum_c1_plan_follows_path.py`, `test_data_capture_successor.py`,
`test_field_workbench_signals.py`, `test_help_fold_attach_successor.py`, `test_intent_codex_rereview.py`,
`test_learner_report_superseded.py`, `test_lp_claim_fixes.py`, `test_method_explicit_upgrade.py`,
`test_mvp011_upgrade.py`, `test_mvp013_upgrade.py`, `test_mvp014_upgrade.py`, `test_mvp015_upgrade.py`,
`test_mvp016_upgrade.py`, `test_mvp017_upgrade.py`, `test_mvp018_upgrade.py`, `test_mvp020_upgrade.py` to
`test_mvp024_upgrade.py`, `test_plan_follows_path.py`, `test_pr4_superseded_claims_landing.py`,
`test_reader_ca2_one_ask.py`, `test_reader_followups_successor.py`, `test_reading_step_switch.py`,
`test_rebuild_equivalence_review.py`, `test_recurrence_commands.py`, `test_regrade_contract_successor.py`,
`test_required_method_grading.py`, `test_ro1_successor.py`, `test_ro4_successor.py`, `test_route_rules_in_grader.py`,
`test_serve_eligibility_review.py`, `test_teacher_te1_successor.py`, `test_teacher_te1b_suggestions.py`);
`test_ro1_availability_reads.py` (the scores' session read named on the occurrence-time allowlist), `test_ro4_value.py`
(the world permutation skips RO5's None fields), `cli_help_snapshot.json`.

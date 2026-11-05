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
  forgo at most the plan's suggested remainder (an upper bound), its presented blocks add their estimate; a check is
  its own one-question block and its minutes come off the plan's like any block's (2.0-2.5 minutes a day on the
  synthetic vault; in rate mode too, since minutes are a suggestion at the tag: landing ruling R3); open picks cost
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
3. **The coin at the first boundary.** As first built, "at a reversible block boundary" included the session's first
   one, and in the synthetic week one offer at minute 0 ended a day. Landing ruling R4 changed this: an offer before
   any active minute in the session is not a stop decision (the learner has just chosen to start), so
   `stop_coin.eligible` requires the session's active minutes above zero, read on the serving clock before the coin's
   uniform (`tests/test_ro5_landing.py::test_r4_...`, the week's case as a regression test).
4. **κ0's hand-over** (the brief's "say exactly how"): at the first randomized offer with a response, κ0 becomes
   `exp(E[log κ0 | offers])` with prior `N(log κ_s, 0.7²)`, `κ_s` the seed then in force, frozen. With no observation the
   posterior equals the seed, so the switch is continuous, and no count or threshold decides it: the regime changes when
   the posterior first holds randomized evidence. The likelihood is §8.6's logistic choice on the log ratio of gain to
   price (Luce's form, no scale constant). Availability is logged with each observation; its coefficient is not fitted
   (follow-up: one more grid axis).
5. **The return model enters `V` only with a randomized return**, and only with the coin on: before, it is the prior's
   mean (no effect), which is RO4's form exactly. Only today's session's gap moves (the tail's sessions run `m̄`).
6. **The check's placement, as built** (after Codex re-review F2; accepted by landing ruling R3): the day's checks are
   their own one-question block at the first boundary of the day's first session, placed by the rules
   (`daily_plan/engine._randomized_check_block`, decision `forced:randomized_check`, deterministic, no mixture, trace,
   coin or score) BEFORE that boundary's decision and before any action draw, as §8.7's `r` requires: whatever a
   decision would draw (practice, reading or stop), the check has already been served. To the learner it is an
   ordinary question. It replaces no chooser item; its minutes come off the plan's like any block's, in embedded and in
   rate mode alike (minutes are a suggestion at the tag). The draw is over items the day's plan pool can serve, fixed
   before the day's action draws (a topic whose eligible items all fall outside the pool has `r_L = 0` that day,
   recorded as `eligible_outside_plan_pool`, no generation need). A later session never takes the day's check; one the
   first session could not place is `not_administered:no_practice_slot`. A drawn item no longer eligible is redrawn
   within the topic among the pool's eligible items; the topic, the randomized unit, never changes.
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

- **The no_intervention floor at the tag**: by landing rulings R5 (1) and R8 FG1's gate at the tag is §8.3's mix
  over `insert_now`, `continue_current` and `no_intervention`, so the floor keeps getting rows at the tag.
- **The higher no-probe share (§9 item 5)**: not built; the report says "follow-up" because the floor's count is zero on a
  typical day of the synthetic vault (which has no follow-up workflows). On a real copy, rerun `objective-report` and
  build it only if the floor's median per active day is zero there too: one more arm in FG1's mixture with its own
  logged probability.
- **The leave-alone arm**: not built (§12 D1).
- **Availability as a covariate in κ0's likelihood**: logged, not fitted.
- **The score cache**: `current_weight` recomputes every closed window's score at each decision; once traces number in
  the thousands, cache closed scores by decision id (they never change once closed).
- **The goal-date read inside `V`**: see choice 10.

## The first week, rerun at landing (copy-shaped synthetic vault, the placement as built)

`tests/test_ro5_calibration.py::test_the_first_week_on_a_copy_shaped_synthetic_vault`, rerun on the landing's step-0
tree (rulings R1, R2, R4, R5 and R6 in): the default arms, both policies answering (fake LLM), answers graded by a
seeded synthetic learner at about 70%, seven days with day 4 sessionless, nobody pressing "keep going". Each day's
check is its own block at the first boundary of the day's first session, before any decision (choice 6).

| Day | Coin draws | Offers (accepted) | Next block over a drawn stop | Minutes forgone (upper) / added | Checks assigned / administered / completed | Check minutes |
|---|---|---|---|---|---|---|
| 1 (10-12) | 1 | 1 (no response; after the check, not at minute 0) | 0 | 23.0 / 0.0 | 1 / 1 / 1 | 2.5 |
| 2 (10-13) | 8 | 0 | 0 | 0.0 / 0.0 | 1 / 1 / 1 | 2.5 |
| 3 (10-14) | 5 | 0 | 0 | 0.0 / 0.0 | 1 / 1 / 1 | 2.0 |
| 4 (10-15) | no session | | | | (counts toward the completion gap) | |
| 5 (10-16) | 5 | 1 (no response) | 0 | 0.0 / 0.0 | 1 / 1 / 1 | 2.0 |
| 6 (10-17) | 5 | 0 | 0 | 0.0 / 0.0 | 1 / 1 / 1 | 2.0 |
| 7 (10-18) | 6 | 0 | 0 | 0.0 / 0.0 | 1 / 1 / 1 | 2.0 |

- **Coin:** 30 draws (28 `policy`, 2 `offer_stop`, 0 `present_next`); no session's opening boundary drew one (R4).
  Both offers stayed open (no "keep going" in the fake env).
- **Checks:** 6 assigned, 6 administered and 6 completed with a label, none displacing a question inside a policy
  block (13.0 minutes over the week); completion rate 6/7 = 0.857 with the sessionless day counted; a median of 5
  eligible topics a day, 5 generation needs raised (none generated), 6 unseen items used.
- **Return model:** 24 coins in 5 sessions, 2 with a contrast: posterior mean of `b` −0.025, variance 0.228 against the
  prior's 0.25 (synthetic gaps), its assumption labelled (R6).
- **Price:** κ0 stays the daily seed (no randomized offer had a response). **Weight: `w` did not move: 0.8**; no 14-day
  window closes inside a week. The `no_intervention` floor had no decisions.

The first build's week, kept for history below, is superseded: its fake answers were ungraded and the pre-fix
resolver read them as zeros (Codex review F1), its return model was the observational fit F3 replaced, and its checks
replaced a chooser question in a policy block. `docs/reviews/router-ro5-codex-review.md` keeps the re-review's rerun.

### The first build's week (history)

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

The full suite, the whole durability lane and the whole vitest run are the landing gate's. No frontend or `src-tauri`
file changed, so no npm, vitest or cargo step applies. No schema change, so the DB reference was regenerated only for
the configuration leaves (1159 to 1167) and validated.

| Step | What ran | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| Import contracts | `uv run lint-imports --no-cache` | 43 kept, 0 broken (one ignore added: `router_objective.checks -> adaptive_difficulty.outcomes`, §6.2's label, function-local) |
| Version pins | the 42 files naming mvp-0.47 (every upgrade and successor test), `-n 6` | 717 passed, 64 failed (pins); fixed, the 39 files rerun: 750 passed, 10 failed (negative slices, `LATEST` sets); fixed, those 10 rerun with the help snapshot and calibration: 20 passed |
| RO4, RO5 and nearby | `tests/test_ro4_*.py`, `tests/test_ro5_*.py`, `test_ro0_gate`, `test_ro1_availability_reads`, `test_data_capture_successor`, `test_registry_audit`, `test_table_roles`, `test_architecture` | 215 passed, 4 failed (RO4's world permutation and `_ad` spy, RO1's allowlist, the SQL-owner rule); fixed (the insert moved to `db/stores/router_objective`), rerun with RO5's: 97 passed |
| Targeted batch | the 295 test files naming the plan, the router outcomes, causal attribution, the capture report, AD's readiness, the router CLI, the router objective, the registry, the snapshots or the activation openers, `-n 6` under the shared lock | 11158 passed, 24 skipped, 3 xfailed, 2 failed (two more pins, one of them, `test_followup_successor`'s opener, already failing at the base); fixed, rerun: passed |
| Contract and audit set | `test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels` (display labels), `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_sidecar_registry`, `test_mobile_allowlist`, `test_architecture`, `test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_registry_audit`, `test_cli_help_snapshot`, `test_codex_tool_lockdown`, `test_e0_isolation`, `test_ai_tool_isolation` (process launch), `test_module_catalog_inventory`, `test_public_tip_guards`, `test_sqlite_file_copies`, `test_ro0_gate`, `test_data_capture_successor`, `test_ro1_availability_reads` and the two fixed pin files | 837 passed, 1 skipped, 1 failed (the catalog notes not yet tracked); committed, rerun: passed |
| Durable SQLite | `--durable-sqlite` on the five `tests/test_ro5_*.py` | 50 passed |
| References | `db_generate_reference.py` / `db_validate_reference.py` (head 246, 1167 leaves: errors []), `module_generate.py` / `module_validate.py` (PASS), `desktop_validate.py` (passed, unchanged) | ok |

Every test ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`, one run at a
time. Every script outside pytest ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

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

## Landing onto main

### Orchestrator rulings (verbatim)

- R1: "F10 has reopened on historical reads, so it goes structural: every read that forms a check's completion, a completion rate or a comparison score reads as of one cutoff through one function, the check's or the window's closure, applied to every event it counts (answers, skips, displacements, grades and holds, administrations), on both occurrence time and received time as RO1's availability predicate does. Codex's two reproductions are tests. The current-grade hold and regrade behaviour stays as intended and is named in the function's docstring. No further Codex round on this class; a further finding there is Low unless a closed score or rate moves with later data in a way RO4's weight would serve."
- R2: "F11 is fixed by adapting the integration to the posterior: the grid covers the prior's and the likelihood's peaks and the region between, its bounds widen until the tail mass beyond them is negligible against the mass inside, and convergence is declared only when both the spacing and the tail mass pass. Codex's reproduction is a test, with a planted-slope recovery test at a narrow prior and at a wide one. If it can't converge, the labelled prior stands and the trace says so."
- R3: "The check as its own one-question block at the start of the day's first session is accepted: it is an ordinary question to the learner, its minutes come off the plan like any block's, and it is placed before any action draw, which §8.7's r requires. Rate-mode checks also come off the plan's minutes, since minutes are a suggestion at the tag. The stage record docs/reviews/router-ro5.md is updated to describe the placement as built and the rerun first week; the re-review section stays as history."
- R4: "The stop coin skips the session's opening boundary: an offer before any active minute in the session isn't a stop decision, since the learner has just chosen to start. Eligibility requires the session's active minutes above zero, which is structural. The test from the synthetic week (an offer at minute 0 that ended a day) becomes a regression test."
- R5: "RO4's open items 1-3 are fixed here because RO5 builds on them. (1) FG1's follow-up gate, the generated-probe plan_interrupt decision, moves onto the two-policy mix at the tag as spec §8.3 says, over insert_now and continue_current, with its trace row and μ recomputable, and the old RouterLLMAnswerV1 request is no longer sent there at the tag; below the tag and with [router_objective] enabled = false, FG1's gate serves exactly as now; FG1's serve-at-once and single-use rules are unchanged. (2) `learnloop router objective-report` passes the weight, so it prints w and its posterior. (3) The why surface's 'how was this chosen?' is plain words with no stage names or symbols, under the display-label audit. Items 4-6 are measured at the smoke."
- R6: "The open item on the lag join's end-to-end test is fixed here (one trace row with a known m0 vector and one graded check two days later). The return model's assumption (the offer changes the return gap only through the session's minutes) stays labelled in the trace and the report. Availability as a covariate in κ0's likelihood, a cache for closed-window scores, the goal-date read inside V and the higher no-probe share go to the follow-up batch as recorded."
- R7: "Owner, Nov 5: the old item difficulty scalar is to be retired in the refactor. RO5 adds no new reader or writer of it; the landing checks this with a grep of the diff against main for the difficulty columns, mastery.irt.difficulty_from_prior and surprise's b, and records the result."
- R8: "The owner decided for FG1 (Nov 3): 'Yes, the router should be able to choose no intervention. The router will decide for weak cases.' So the objective's follow-up gate keeps no_intervention in its support at the tag, beside insert_now and continue_current (the 'wait' option the owner also kept). The numeric policy values it as no probe served, with the workflow's hypotheses left as they are; the LLM side may choose it, with probabilities over all three; the Decider stays advice; the ledger records it as offered, and §9 item 5's floor keeps getting rows at the tag. 'No room to wait' still asks now. A test shows each of the three can be drawn with its logged probability, and that choosing no_intervention serves no probe and strands no Next."
- R9: "Your question 1: R5 (1) follows the tag and [router_objective] enabled, with no switch of its own. That is the ruling's intent: it's RO4's spec for mid-block follow-ups, not an RO5 arm. The smoke's 'every RO5 arm off' comparison is identical to main at mvp-0.47 except this gate, which it reports separately."
- R10: "Your questions 3 and 4 stand as built: a dated use whose exam import arrives after its window closed is censored as no_result, since a closed score never moves; the realized-cost read stays on occurrence time through the window's end, since activity is recorded where it happens and the serving clock shares it. Both are named in the record."
- R11: "The daily price a score charges is read as of the window's closure: each price-source trace is admitted through Closure.admits on its created time, and prices are built per closure. R10's occurrence-time activity read stays. Codex's reproduction (a trace appended after closure must not move the closed score or current_weight) is the test. No further Codex round: R1's class is now closed by this fix plus the Ledger; a further finding there is Low unless a closed score moves with later data."

### Step 0: the rulings' fixes (on `5f02be6eb2`, before merging main)

One commit each, reproduced first in `tests/test_ro5_landing.py` (see `docs/reviews/router-ro5-codex-review.md`,
"Final verify"): R2 `eebca9b33b`, R4 `a5e12c2d7f`, R1 `e16d1253e8`, R6 `8fd2a5a8ba`, R5 (3) `cdcc7537c4`, R5 (2)
`3c78b28fa3`, R5 (1) `29464fb3f9`, R8 `940190f3d6`, R11 `db5a1b3c96`; R3 is this record's choices 3 and 6 and the first week rerun above.

**R5 (1) as built.** At RO5's tag with the objective serving, `followup_run.router._plan_context` gives the generated
probe's `plan_interrupt` decision to `objective_chooser.ObjectiveFollowupGate` (RO4's `ObjectiveRestraintGate`'s draw,
factored into `_mixed`, its records unchanged): §8.3's mix over `insert_now` and `continue_current`, `π_L` the LLM
policy's `intervene_now` on the restraint card (`router_llm_restraint_v3`), `π_Q` the two orders valued as one repair
question on the workflow's LO (the missed question's minutes; the probe does not exist yet) now or after the current
block's remaining questions, the Decider's `P(yes)` as advice. No room to wait asks now, deterministically, with no
model asked. `record_decision` writes the trace row and freezes the decision's own support for data capture. FG1's
hard refusals, serve-at-once and single-use rules are untouched.

**R8 as built** (`940190f3d6`; supersedes the two-arm support of `29464fb3f9`). The support at the tag is
`insert_now`, `continue_current`, `no_intervention`:
- `π_L` is the LLM policy's `router_llm_choice_v3` over the three options (a probability per option, every one
  positive) with a non-choosable reference row, the current block's rest; R2b's `RouterLLMAnswerV1` is not sent.
- `π_Q` values three sequences: the repair question then the block's rest, the rest then the question, and the rest
  alone (no probe served, the workflow's hypotheses left as they are).
- The Decider's restraint `P(yes)` stays advice. The ledger row records `no_intervention` as offered, so §9 item 5's
  floor keeps getting rows at the tag. No room to wait still asks now, deterministically.
- `tests/test_ro5_landing.py::test_r8_each_arm_can_be_drawn_with_its_logged_probability_and_no_intervention_serves_no_probe`:
  each of the three drawn with its logged probability (`μ` recomputed), and a drawn `no_intervention` logged, Next
  serving the block's own question and no probe generated.

Requests per follow-up decision (fakes, `tests/test_followup_router.py`'s plan shape, both models answering):

| | router_llm | Decider |
|---|---|---|
| Before, at the tag (FG1's gate) | 1, `RouterLLMAnswerV1` (three options), 2,568 bytes | 1, `choose_block` |
| After R5 (1), at the tag (two arms; superseded) | 1, `RouterLLMRestraintV3`, 2,658 bytes | 1, `intervene_now` |
| After R8, at the tag | 1, `RouterLLMChoiceV3`, options `insert_now`, `continue_current`, `no_intervention`, 3,939 bytes | 1, `intervene_now` |
| Below the tag, or objective off | 1, `RouterLLMAnswerV1`, unchanged code (2,568-2,669 bytes with the plan's card) | 1, `choose_block` (unchanged) |

As ruled (R9), the gate follows the tag and `[router_objective] enabled` with no switch of its own, so the smoke's
"every RO5 arm off" comparison is identical to main at mvp-0.47 except this gate, reported separately. As ruled
(R10), a dated use whose exam import arrives after its window closed is censored `no_result` (a closed score never
moves), and the realized cost reads activity on occurrence time through the window's end (`price.activity_spans`,
shared with the serving clock).

**R11** (`db5a1b3c96`, after the scoped verify of step 0, job `20261105-120414-0Bm9lB`): the daily prices a score
charges are built per window closure, each price-source trace admitted through `Closure.admits` on its created time
(Codex's reproduction is `tests/test_ro5_landing.py::test_r11_...`). With it and the `Ledger`, R1's class is closed.

### Step 1: the merge (`daf69d74c5`)

Main `5b2b56b0de` merged; no migration on RO5's side, so head 246 and main's sanitized `migration_head_246` carry
over byte for byte (`git diff main -- fixtures migrations` is empty). Conflicts: `tests/test_followup_successor.py`
(the openers' pin names RO5's `learnloop.router_calibration_upgrade`) and the generated reference (regenerated in
step 3). Checked after the merge:
- `objective_inputs` carries RO4's R6 reading path; RO5's rollouts read AD's fitted reading curve through it.
- The goal wizard's `use_weight` is kept.
- The objective report's `kappa_seed` count (RO4's R5) sits beside RO5's calibration section. A day priced by κ0's
  posterior from stop offers is not a fall-back: it is counted apart as `posterior_days`.
- `tests/test_ro2_ad_raw_document_reads.py`'s walk now starts from RO5's `checks`, `scores`, `stop_coin` and
  `goal_read` as well; no raw document load is reached.
- Version pins, defaults snapshots, config fingerprints and the CLI help snapshot needed no further change.

### Step 2: early checks (on the merged tree)

| Set | Result |
|---|---|
| `lint-imports --no-cache` | 43 kept, 0 broken. The documented ignore `router_objective.checks -> adaptive_difficulty.outcomes` is still needed (two function-local imports of §6.2's label) |
| `test_measurement_state_labels`, `test_cli_help_snapshot`, `test_codex_lockdown_round3` (process-launch allowlist), `test_ro1_availability_reads`, every `test_ro0_*`, `test_ro2_*`, `test_ro4_*`, `test_ro5_*`, `test_followup_*`, `test_registry_audit`, `test_architecture`, `test_data_capture_successor`, `test_config_refactor`; `-n 6` | 964 passed, 2 failed: `test_ro4_trace_report::test_the_report_counts_how_often_the_days_seed_fell_back` (the merge's `posterior_days` key; its pin updated) and `test_ro0_rows9_13_decision_state::test_receipts_hold_ids_and_numbers` (an LO title "M2" found inside a random ULID; 3 of 3 alone) |
| `test_ro1_availability_reads` | passes. RO5's reads of attempts filter in Python through `Closure.admits`, which applies RO1's predicate (received time); none is a SQL time cutoff on `created_at` |

### Step 3: references (`0a2574d89e`)

`db_generate_reference` (head 246, 393 table notes) / `db_validate_reference` (errors []); `desktop_generate` /
`desktop_validate` (319/319 TS/TSX, 6/6 Rust); `module_generate` (1231 module notes, 67 package maps, 1383 test files)
/ `module_validate` (PASS, 42583/42583 wikilinks); `validate_vault.py` (2218 notes: passed).

### Step 4: the gate (at `0a2574d89e`)

| Lane | Result |
|---|---|
| Setup | `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0`: ok |
| Import contracts | 43 kept, 0 broken |
| Full suite (`-n 8`, 10G scope, under the shared lock) | 26570 passed, 91 skipped, 47 xfailed, 1 failed in 58 min: `test_ro4_trace_report::test_the_why_surface_offers_the_trace_in_plain_words` (`assert decided and ...`: no decided block on the plan when the mix draws stop first; it failed the same way once in step 0). Passed 3 of 3 alone |
| Durability lane (`-m durability`) | 402 passed, 1 skipped |
| Owner lane (fresh backup-API copies of `owner-copies-mvp035` in `fixtures-local/landing-ro5/`, since deleted) | 83 passed, 4 skipped, and the same 2 known failures as at RO4's landing: `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies[arxiv_v2]` |
| Desktop | typecheck ok; whole vitest at `--maxWorkers=4`: 2756 passed; `frontend:build` ok |
| Rust | `cargo check`: ok |
| Mobile | typecheck ok, build ok (no phone file changed) |

### Step 5: the smoke

Fresh backup-API copies of `~/learnloop-backups/mvp043-20261103-copy` (arxiv_v2, linear_algebra, probability) under
`fixtures-local/landing-ro5-smoke/`, since deleted. Every AI route pointed at 127.0.0.1:9; the router LLM and the
Decider were in-process fakes, grading and diagnosis the tests' `BlindRivalClient`, probe authoring the tests'
`AuthorFake`. Main code and branch code were `git archive`d with `migrations/`. On main code each copy was upgraded as
RO4's record says (mvp-0.45, rebuild, mvp-0.46; then mvp-0.47, rebuild); on branch code, the default upgrade took it
from mvp-0.47 to mvp-0.48. The driver goes through the real sidecar handlers, and after a miss it runs FG1's job and
presses Next through `followup_next` as the app does.

**Identity** (seed pinned to the decision id on both sides; ids and wall times aside). All nine pairs were
IDENTICAL: Today, plan, every step, every written row, every router LLM and Decider request, and the follow-up gate.

| Copy | Below the tag: main vs branch at mvp-0.47, with a generated follow-up's gate | At the tag, every RO5 arm and `fitted_models` off, vs main at mvp-0.47 (no miss: R9) | At the tag, `enabled = false`, vs main at mvp-0.46, with a generated follow-up's gate |
|---|---|---|---|
| arxiv_v2 | identical (10 LLM, 10 Decider requests, 1 gate) | identical (8, 8) | identical (6, 6, 1 gate) |
| linear_algebra | identical (13, 13, 1 gate) | identical (13, 13) | identical (7, 7, 1 gate) |
| probability | identical (8, 8, 1 gate) | identical (6, 6) | identical (5, 5, 1 gate) |

For the arms-off pair, the boundary key's version string was dropped on both sides, as RO5's own every-arm-off
test does. That string seeds the numeric policy's rollouts, so mvp-0.47 and mvp-0.48 otherwise roll different noise
from the same distribution. Without the drop, μ differed (0.632 vs 0.452) on probability's first decision. As R9
says, the follow-up gate at the tag is reported apart, below (R5 (1)).

**The week at the tag, every arm on.** Seven days per copy: one session a day at 15:00 with 30 minutes offered, day
4 sessionless. A seeded synthetic learner answered the copy's real items about 70% right. Offered stops were kept
going or accepted at random (seeded, at most 2 keep-goings a day), and every miss opened FG1's follow-up. Per day:

arxiv_v2

| Day | Coin draws (offers) | Checks assigned / administered / completed | Check: topic, item, r_L of eligible | Gen. needs | Minutes: coin forgone / added; check | Session min (plan 30) | κ0 (how) | w (posterior) |
|---|---|---|---|---|---|---|---|---|
| 11-05 | 1 (0) | 1 / 1 / 1 | lo_render_a_classifier_s_decision_regions, pi_recall_classifier_grid_components, 1 of 1 | 1 | 0 / 0; 3.5 | 6.0 | 0.000114 (day_seed) | 0.8 (prior, n 0) |
| 11-06 | 6 (0) | 0 (no eligible topic in the plan's pool) | — | 2 | 0 / 0 | 10.5 | 0.000114 (floored) | 0.8 |
| 11-07 | 3 (1, accepted) | 0 | — | 7 | 25.5 / 0 | 4.5 | 0.00294 (day_seed) | 0.8 |
| 11-08 | no session | | | | | | | |
| 11-09 | 7 (0) | 0 | — | 8 | 0 / 0 | 21.0 | 0.004409 (posterior) | 0.8 |
| 11-10 | 2 (0) | 0 | — | 15 | 0 / 0 | 7.5 | 0.004409 (posterior) | 0.8 |
| 11-11 | 2 (0) | 0 | — | 20 | 0 / 0 | 9.0 | 0.006465 (posterior) | 0.8 |

linear_algebra

| Day | Coin draws (offers) | Checks assigned / administered / completed | Check: topic, item, r_L of eligible | Gen. needs | Minutes: coin forgone / added; check | Session min (plan 30) | κ0 (how) | w (posterior) |
|---|---|---|---|---|---|---|---|---|
| 11-05 | 2 (0) | 1 / 1 / 1 | lo_what_makes_a_vector_space, pi_what_makes_test_strategy_01, 0.2 of 5 | 2 | 0 / 0; 2.78 | 6.0 | 0.0 (tail_average) | 0.8 (prior, n 0) |
| 11-06 | 2 (0) | 1 / 1 / 1 | lo_read_and_apply_the_vector_space_definition, pi_read_definition_nonempty_sets_method, 0.2 of 5 | 2 | 0 / 0; 2.56 | 3.0 | 0.0 (tail_average) | 0.8 |
| 11-07 | 13 (0) | 1 / 1 / 1 | lo_operations_and_the_vector_space_axiom_checklist, pi_axiom_operation_totality_01, 0.25 of 4 | 2 | 0 / 0; 2.40 | 49.5 | 0.0 (tail_average) | 0.8 |
| 11-08 | no session | | | | | | | |
| 11-09 | 8 (0) | 1 / 1 / 1 | lo_read_and_apply_the_vector_space_definition, pi_histogram_definition_gate, 0.333 of 3 | 2 | 0 / 0; 2.61 | 42.0 | 0.0 (tail_average) | 0.8 |
| 11-10 | 9 (0) | 1 / 1 / 1 | lo_prove_vector_identities_from_scalar_laws, pi_coordinate_negation_proof_route, 0.333 of 3 | 3 | 0 / 0; 2.58 | 46.5 | 0.0 (tail_average) | 0.8 |
| 11-11 | 9 (1, accepted) | 1 / 1 / 1 | lo_read_and_apply_the_vector_space_definition, pi_definition_vector_term_interpret_02, 0.5 of 2 | 3 | 0 / 6.08; 2.56 | 48.0 | 0.006108 (floored) | 0.8 |

probability

| Day | Coin draws (offers) | Checks assigned / administered / completed | Check: topic, item, r_L of eligible | Gen. needs | Minutes: coin forgone / added; check | Session min (plan 30) | κ0 (how) | w (posterior) |
|---|---|---|---|---|---|---|---|---|
| 11-05 | 1 (0) | 1 / 1 / 1 | lo_analyze_and_optimize_nonuniform_collision_probab, pi_exercise_01kyn2kdf7h2kba1fp7wv7t3w5, 1 of 1 | 0 | 0 / 0; 3.5 | 4.5 | 0.0 (tail_average) | 0.8 (prior, n 0) |
| 11-06 | 5 (0) | 0 | — | 0 | 0 / 0 | 16.5 | 3.4e-05 (day_seed) | 0.8 |
| 11-07 | 6 (0) | 1 / 1 / 1 | lo_build_a_valid_counting_based_probability_model, pi_birthday_ordered_model_exact_pair, 1 of 1 | 2 | 0 / 0; 2.56 | 28.5 | 0.026618 (day_seed) | 0.8 |
| 11-08 | no session | | | | | | | |
| 11-09 | 2 (0) | 0 | — | 4 | 0 / 0 | 15.0 | 0.017212 (day_seed) | 0.8 |
| 11-10 | 2 (0) | 0 | — | 4 | 0 / 0 | 12.0 | 0.014838 (day_seed) | 0.8 |
| 11-11 | 3 (0) | 1 / 1 / 1 | lo_simulate_a_counting_probability_model, pi_trace_encoded_dice_simulation, 0.5 of 2 | 5 | 0 / 0; 2.70 | 12.0 | 0.014687 (day_seed) | 0.8 |

Across the week:
- **Coin.** 21, 43 and 19 draws (arms: arxiv_v2 1 `offer_stop` / 2 `present_next` / 18 `policy`; linear_algebra
  1 / 4 / 38; probability 0 / 0 / 19). No coin at an opening boundary (R4): the smallest session minutes at a coin was
  1.5, after the day's check.
- **Checks.** No check was excluded and none failed to be completed. Every unassigned day is a day with no eligible
  topic in the plan's pool (`r_L = 0`, a generation need raised; none generated).
- **Open picks.** 0 on every copy: no misconception pick was reported. The arm costs no minutes.
- **κ0.** On arxiv_v2 it handed over to the posterior after day 3's randomized offer was accepted (3 posterior days).
  Elsewhere it stayed the seed.
- **Weight.** `w` stayed 0.8 with its prior (no 14-day window closes in a week).
- **Return model.** arxiv_v2: posterior from 19 coins in 5 sessions, 3 contrasted (mean −0.090, variance 0.274).
  linear_algebra: −0.038, 0.241. probability: its prior (no contrast). The assumption is labelled.

**RO4's item 4 (session length).** linear_algebra's sessions ran 42-49.5 minutes against the plan's 30 on four of
six days. κ0 stayed at the tail's average marginal gain, 0.0 there, so the soft budget prices nothing. The learned
κ0 did not move them within the week: its only randomized offer with a response came on the last day.

**Assignments.**
- Every `policy_experiment_assignments` row's logged probability was recomputed from its own frozen values: the
  coin's arm from its rate, its served probability from the mix's μ (itself recomputed by `mix.recompute`) and the
  support, its uniform from its own stream; each check day's `r_L = k/N` from its eligible counts, each slot's topic,
  item and item probability from the date's seed. Problems: 0 on all three copies (83 coins, 18 check days, 10
  slots).
- Each copy had one decision where the boundary's forced rule (a waiting follow-up opens the next block) superseded
  the drawn candidate after the draw. The ledger logs that forced block as deterministic, while the coin's row keeps
  the coin and mix's served candidate with its exact probability (recomputed). This is the live continuation, as §8.7
  reads it.
- The check's draw does not depend on the action draw: rerunning day 1 with another action seed (different decision
  ids, different coin seeds) drew the same topic, item and `r_L` on every copy.
- No protected, held-out, exam-reserved or generated item was drawn, and no drawn item had an earlier attempt.

**R5 (1) and R8: generated follow-ups at the tag.**
- **Gate decisions.** 9 on arxiv_v2 (5 `insert_now`, 2 `continue_current` by the mix; 2 no room to wait),
  36 on linear_algebra (5 / 1 / 3 `no_intervention` by the mix; 27 no room, its sessions past the plan) and 16 on
  probability (5 / 1 / 2; 8 no room).
- **Every mix decision.** Support `insert_now`, `continue_current`, `no_intervention`; a trace row; μ recomputed from
  the ledger row (24/24).
- **Requests.** 1 `RouterLLMChoiceV3` with the three options (4,319, 13,554 and 7,561 bytes on the first decision of
  each copy) and 1 Decider `intervene_now`; no `RouterLLMAnswerV1`.
- **Ask now.** The probe was the very next step every time (7/7, 32/32, 13/13).
- **Wait.** The probe opened the next block (one plan presentation).
- **No intervention.** No probe was written, and Next continued the block.
- **Never again.** Every probe was served at most once and answered once. A later `open_queue_item` on each was
  refused with `generated_probe_closed` (9/9, 33/33, 14/14).
- **Below the tag** the same miss's gate is FG1's, identical to main (table above).

**Protection on the cards.** All 72, 122 and 74 router LLM cards and every Decider state of the week were scanned
(`prot5.py`, RO4's scan). There were no protected, unattempted or invisible stems and no attempt cited after its
decision. Every reference-solution hit sits in the learner's answer: the synthetic learner types the expected answer
when right (`answer`, `answer_excerpt` or the text card's `answer:`). The exception is 2 hits on linear_algebra: an
attempted multiple-choice stem whose option A is its reference answer, 108 days before. This is the same false
positive as at RO2's and RO4's landings.

| Copy | π_L card bytes min / median / max (n) | Decider state median bytes |
|---|---|---|
| arxiv_v2 | 3,993 / 9,835 / 29,971 (36) | 2,375 |
| linear_algebra | 2,504 / 50,509 / 50,892 (61) | 19,969 |
| probability | 4,240 / 37,765 / 50,955 (37) | 11,562 |

**Time** (main at mvp-0.47 against branch at mvp-0.48 with every arm on; one day with a generated follow-up; the full
suite ran alongside, on both sides alike):

| Copy | Next after | Side | Today ms | Next at a boundary ms (median, n) | Next inside a block | Submit | Follow-up gate | Numeric policy per decision (median, p90) |
|---|---|---|---|---|---|---|---|---|
| arxiv_v2 | 0 s | main | 240 | 2281 (9) | 436 | 276 | 382 | 1491, 1704 |
| arxiv_v2 | 0 s | branch | 233 | 2631 (9) | 448 | 293 | 257 | 1922, 1961 |
| arxiv_v2 | 3 s | main | 247 | 760 (9) | 476 | 293 | 286 | 1308, 1489 |
| arxiv_v2 | 3 s | branch | 235 | 763 (9) | 473 | 287 | 255 | 1270, 1305 |
| linear_algebra | 0 s | main | 1039 | 2984 (14) | 783 | 312 | 440 | 904, 1062 |
| linear_algebra | 0 s | branch | 1095 | 2460 (7) | 707 | 309 | 278 | 797, 897 |
| linear_algebra | 3 s | main | 1062 | 1203 (14) | 911 | 310 | 406 | 921, 1048 |
| linear_algebra | 3 s | branch | 981 | 919 (7) | 741 | 298 | 235 | 725, 877 |
| probability | 0 s | main | 821 | 1015 (1) | — | 553 | — | 286 |
| probability | 0 s | branch | 828 | 968 (3) | — | 336 | 319 | 332 |
| probability | 3 s | main | 845 | 1009 (1) | — | 554 | — | 322 |
| probability | 3 s | branch | 857 | 607 (3) | — | 336 | 338 | 265 |

- The branch's gate is the deterministic no-room ask-now here. The week's mix gates took 0.72-0.95 s, which
  includes the numeric policy over three sequences.
- No deadline was missed.
- **RO4's item 6 (arxiv_v2's numeric policy).** `cProfile` over its `run_numeric` calls: 12.3 of 17.0 s sit in the
  tail rollouts (`value.run_tail` / `evaluate`). The largest single cost is the memory model's per-review FSRS
  update, `memory.review`: 177,029 calls, 6.0 s cumulative, with scalar numpy `clip` / `broadcast_to` overhead and
  `retrievability`. Then `_practice_batch` and `_session` (2.8 s and 1.0 s own time), then SQLite reads (1.5 s).
  arxiv_v2 has 22 LOs, so the tail simulates more topic reviews per draw than the other copies. Vectorizing
  `memory.review` over topics is the smallest speed-up (follow-up batch).

**Reports after the week.**
- `learnloop router objective-report --json` exits 0 on every copy and prints `w` 0.8 with its posterior (R5 (2))
  and `kappa_seed` (arxiv_v2: day_seed 2, floored 1, posterior 3, `posterior_days` 3).
- Its calibration section, as of the week's last day:
  - completion: 1/1 (arxiv_v2), 6/6 (linear_algebra), 3/3 (probability), each 0.857 with the sessionless day;
  - generation needs: 53, 14 and 15;
  - weight: 0 closed scores, `w` 0.8, not moved;
  - price: posterior, seed and seed;
  - floor: `no_intervention` decisions at the tag 0, 3 and 2, beside 9, 33 and 14 probes (R8: the floor keeps rows);
  - goal read: its prior (no pair).
- The CLI reads as of the real clock (Nov 5), which is before the week's later frozen days, so it shows day 1's
  checks.
- `learnloop data-capture report --json` exits 0. Its `open_picks` section: available, 0 assignments, 0
  administered and 0 completed per arm.

**Shadow, survival, isolation.**
- `rebuild --shadow` after the week: facet 0, schedule 0, mastery 13, 14 and 8, all stamp-only (mvp-0.47 to mvp-0.48:
  the rows the upgrade activates without rebuilding, RO4's item 5).
- Every assignment and trace row is byte-identical after `rebuild-derived-state` and a state sync.
- New `model_call_receipts` came only from the fakes; the backups' own 42 chatgpt and 14 openrouter_decider receipts
  are from Oct 25-26.
- The socket watch logged no connect at all and no non-loopback address. The only subprocesses were
  `powerprofilesctl get` and `git -C` (the code stamp); there was no Codex process.

**R7.** `git diff main...HEAD -- src migrations` adds no reader or writer of the item difficulty scalar: no
difficulty column, no `mastery.irt.difficulty_from_prior` and no surprise `b`. The only added lines matching
"difficulty" name the `adaptive_difficulty` package (AD's subject view, its outcomes label).

### What the owner runs after the fast-forward

For each vault (`~/learnloop-vaults/<name>`), from where RO4's record leaves them (mvp-0.47):

```bash
learnloop upgrade --vault ~/learnloop-vaults/<name>             # mvp-0.47 -> mvp-0.48 (the default target; no migration)
learnloop rebuild-derived-state --vault ~/learnloop-vaults/<name>   # optional: clears the stamp-only shadow rows
```

A vault still below mvp-0.47 takes RO4's commands first. Then rebuild the desktop app and restart the phone host.
After a few days:

```bash
learnloop router objective-report --vault ~/learnloop-vaults/<name>   # w and its posterior, the calibration section
learnloop data-capture report --vault ~/learnloop-vaults/<name>       # open_picks
```

**To turn an arm off**, set it in the vault's `learnloop.toml`. With all four set, Today serves mvp-0.47 exactly, apart
from FG1's follow-up gate (R9):

```toml
[router_objective]
stop_coin = 0.0          # no stop coin
check_rate = "off"       # no randomized checks (w then stays RO4's calculation)
pick_open_share = 0.0    # no open picks
fitted_models = false    # the rollouts read AD's priors, the combiner its prior
```

`enabled = false` turns the whole objective off, the follow-up gate on the mix included, and serves mvp-0.46's
mixture and frame, as the smoke shows.

### Open items (for the orchestrator)

1. **Sessions past the plan with a zero price** (RO4's item 4, measured above): linear_algebra ran about 45 minutes
   against 30, because κ0's seed is the tail's average gain, 0.0 there. The coin's randomized offers move κ0 only once
   one has a response. On arxiv_v2 that happened on day 3; on linear_algebra, on day 7. Expect long sessions until a
   few offers are answered.
2. **Check coverage depends on eligible items in the plan's pool.** arxiv_v2 had an eligible topic on only 1 of 6
   days (53 generation needs raised by the week's end). Checks resume once `learnloop generate-diagnostics` (the
   existing paid generator) writes unseen items.
3. **The numeric policy on arxiv_v2** (RO4's item 6): 1.3-1.9 s per decision, dominated by `memory.review` in the tail
   rollouts. Next at a boundary right after feedback is about 0.35 s slower than main on arxiv_v2 and faster on the
   other two; after 3 s of reading it matches main.
4. **The upgrade activates without a rebuild** (RO4's item 5): stamp-only mastery rows until `rebuild-derived-state`.
5. As ruled (R6), the follow-up batch has availability as a covariate in κ0's likelihood, a cache for closed-window
   scores, the goal-date read inside `V` and the higher no-probe share.

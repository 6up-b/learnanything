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

- **The no_intervention floor at the tag**: by landing ruling R5 (1) FG1's gate at the tag is §8.3's mix over
  `insert_now` and `continue_current`, so new `no_intervention` decisions come only from below the tag or with the
  objective off; the floor section reads those.
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

### Step 0: the rulings' fixes (on `5f02be6eb2`, before merging main)

One commit each, reproduced first in `tests/test_ro5_landing.py` (see `docs/reviews/router-ro5-codex-review.md`,
"Final verify"): R2 `eebca9b33b`, R4 `a5e12c2d7f`, R1 `e16d1253e8`, R6 `8fd2a5a8ba`, R5 (3) `cdcc7537c4`, R5 (2)
`3c78b28fa3`, R5 (1) `29464fb3f9`; R3 is this record's choices 3 and 6 and the first week rerun above.

**R5 (1) as built.** At RO5's tag with the objective serving, `followup_run.router._plan_context` gives the generated
probe's `plan_interrupt` decision to `objective_chooser.ObjectiveFollowupGate` (RO4's `ObjectiveRestraintGate`'s draw,
factored into `_mixed`, its records unchanged): §8.3's mix over `insert_now` and `continue_current`, `π_L` the LLM
policy's `intervene_now` on the restraint card (`router_llm_restraint_v3`), `π_Q` the two orders valued as one repair
question on the workflow's LO (the missed question's minutes; the probe does not exist yet) now or after the current
block's remaining questions, the Decider's `P(yes)` as advice. No room to wait asks now, deterministically, with no
model asked. `record_decision` writes the trace row and freezes the decision's own support for data capture; the
ledger row marks `no_intervention` not offered. FG1's hard refusals, serve-at-once and single-use rules are untouched.

Requests per follow-up decision (fakes, `tests/test_followup_router.py`'s plan shape):

| | router_llm | Decider |
|---|---|---|
| Before, at the tag (FG1's gate) | 1, `RouterLLMAnswerV1`, 2,568 bytes | 1, `choose_block` |
| After, at the tag | 1, `RouterLLMRestraintV3`, 2,658 bytes | 1, `intervene_now` |
| Below the tag, or objective off | 1, `RouterLLMAnswerV1`, 2,568 bytes (unchanged) | 1, `choose_block` (unchanged) |

Consequences recorded for the orchestrator: at the tag no new `no_intervention` decision is drawn, so §9 item 5's
floor reads only rows from below the tag or with the objective off; and the smoke's "every RO5 arm off" identity
against mvp-0.47 holds for every journey except a generated probe's gate, which has no switch of its own (it follows
the tag and `[router_objective] enabled`).

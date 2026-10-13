# Value-of-information stopping: Codex review and fixes

Branch `serving/voi-stopping`, worktree `learnanything-voi`. Codex reviewed the
stage at `8c9971a6` (job `~/.cache/codex-agent/jobs/20261013-040151-zfvgB9`)
and found nine defects (three High, six Medium). Every finding reproduced at
`8c9971a6` and is fixed in `6e558328`; none was rejected. Owner decisions in
force (2026-10-12): recommended defaults accepted; frictionless defaults
(honest labels, generous defaults, live behind kill switches, no shadow
stage); LLM judgment and measured values over hand-picked constants; no
artificial count caps.

An earlier, interrupted run of this fix step had left uncommitted work in
`voi_stopping.py` (the greedy conditional machinery, the served/recommended
receipt fields, the F6 change, the episode-maximum counterfactual). It was
reviewed and built on; its follow-up receipt used a new
`decision_features.decision_type` that the table's CHECK rejects, so that part
was replaced (F1 below).

## 1. Reproduction at `8c9971a6`

Each finding was reproduced first with a throwaway test against the
unchanged code (outputs as observed):

| Id | What the reproduction did | Observed at `8c9971a6` |
|---|---|---|
| F1 | queue a further follow-up at mvp-0.17, then `rebuild_all_derived_state` | `gate_diagnostics` after the rebuild: `None` (the forecast is gone) |
| F2 | five project probes on one LO and facet; two teach-backs on the test vault | every probe valued at 0.2 nats; the second teach-back valued at 7.947 nats, exactly its standalone `probe_eig_total` |
| F3 | `maximum_observations = 1`, value paying (0.0001-minute probes), one answer | episode `complete`, `observation_budget_exhausted` |
| F4 | two eligible follow-ups; the slate ranking's pick costs 10,000 minutes, the other 0.01 | suppressed `voi_value_below_minutes_cost`, `candidate_count` 1 |
| F5 | probes worth 12 and 60 minutes, five minutes each, five minutes to spend, real classifier + `LegacyLanesSource` + `LaneQuotaChooser` | pool order `pi_high, pi_low` but block `planner_value` 0.5 vs 1.0: the chooser picks `pi_low` |
| F6 | complete routes, half-minute instrument, likelihoods 0.9/0.1, priors 0.89/0.11 and 0.91/0.09 (the old `value_candidates`) | 0.89: `stop`, robust EVSI 0.06 min; 0.91: `continue`, EIG value 8.04 min |
| F7 | a sole teach-back, 10,000-minute cost | kept, no receipt |
| F8 | two admitted instruments, exploration forced to the second | presentation of `pi_svd_define_002` carries `chosen_ref = pi_svd_define_001` and only its forecast |
| F9 | a value-suppressed further follow-up, then `assemble_gate_training_set` | one `silent_gate` example, label 0, weight 0.25 |

## 2. Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Rebuild destroys follow-up forecasts | fixed | `6e558328` | `test_the_follow_up_forecast_survives_rebuilds_and_replay_unrevalued`, `test_a_value_suppressed_follow_up_keeps_its_receipt`, `test_below_the_successor_no_follow_up_receipt_carries_a_value_decision` |
| F2 | High | Multiple checks are never valued conditionally | fixed | `6e558328` | `test_a_second_teach_back_that_tells_the_same_thing_is_not_admitted`, `test_teach_backs_stay_while_their_conditional_value_pays`, `test_a_project_probe_that_duplicates_an_admitted_one_is_not_admitted`, `test_valued_project_probes_have_no_count_cap_and_are_planned_in_value_order` |
| F3 | High | The episode's four-observation cap still overrides value | fixed | `6e558328` | `test_value_carries_one_episode_past_its_former_maximum` (a real fifth observation in one episode), `test_the_episode_maximum_still_ends_an_episode_off_the_value_rule` (mvp-0.16, sub-switch off), `test_a_calibration_session_keeps_the_episode_maximum`, `test_the_probe_contract_says_value_decides_only_at_the_successor`; vitest `labels a value-stopped diagnostic check without a count ceiling` |
| F4 | Medium | Follow-ups can stop despite a worthwhile alternative | fixed | `6e558328` | `test_a_cheaper_follow_up_that_pays_is_queued_when_the_old_winner_does_not` |
| F5 | Medium | The plan chooser reverses project-probe value ordering | fixed | `6e558328` | `test_the_block_chooser_plans_the_best_probe_per_minute_first` (pool order and re-entry order, the real block source and chooser) |
| F6 | Medium | Greater certainty can restart an unprofitable measurement | fixed | `6e558328` | `test_greater_certainty_never_restarts_an_unprofitable_measurement`; `test_where_routes_differ_robust_evsi_and_rank_feasibles_stop_rule_decide` updated |
| F7 | Medium | Former caps become unconditional admission floors | fixed | `6e558328` | `test_the_first_follow_up_in_a_session_is_valued_too`, `test_a_teach_back_whose_value_does_not_pay_is_dropped_the_first_included`, `test_a_sole_teach_back_is_valued_and_receipted`, `test_a_project_probe_whose_value_does_not_pay_stays_later` |
| F8 | Medium | Probe receipts can forecast a different item from the one served | fixed | `6e558328` | `test_an_explored_probe_carries_its_own_forecast`; the commit door's receipt in `test_value_carries_one_episode_past_its_former_maximum` |
| F9 | Medium | New suppression reasons contaminate gate-training labels | fixed | `6e558328` | `test_value_suppressions_never_label_the_trigger` |

### F1: the follow-up forecast lives on a receipt

*Superseded by the re-review (§7.3): one row per decision in
`followup_value_decisions` (migration 188); `decision_features` is mvp-0.16's
again.*

The follow-up's value decision now rides on its `decision_features` row
(`decision_type = 'followup'`, `decision_id` = the source attempt):
RECEIPT, immutable by trigger (migration 161), written once with
`ON CONFLICT DO NOTHING`, and never touched by a rebuild or a regrade's LO
replay. That row already was the follow-up decision's feature receipt; it
gains `context.voi_stopping` (mvp-0.17 only) and is now also written when
value suppresses the follow-up (`decision_outcome =
suppressed_voi_value_below_minutes_cost`). No migration: the CHECK on
`decision_type` would have needed one for a new type, and the existing row is
the natural stable key. `voi_stopping.followup_receipt(repository,
attempt_id)` reads it. The copy on `attempt_surprise.gate_diagnostics_json`
stays for the feedback screen; it is DERIVED and the test shows a rebuild
dropping it while the receipt survives two rebuilds, an LO replay (the step
`regrade_attempt` runs) and a later re-evaluation of the same attempt, which
does not re-value it. Pre-existing and out of scope: every other key of the
gate diagnostics is lost on rebuild the same way (not this stage's data).

### F2: greedy conditional valuation

*The hypothesis term below was revised by the re-review (§7.4): it is valued
over the expected posterior branches from each check's likelihood rows, not
once per LO.*

`voi_stopping.greedy_information_admission` admits checks one at a time: at
each step every remaining check is valued given the belief the admitted ones
are expected to leave, the best by robust value per minute is admitted while
it pays, and adding stops at the first step whose best remaining check does
not pay. The information is the selection reward's own `probe_eig_total`,
decomposed from the item's reward body (`InformationTerms.from_reward_debug`,
which refuses a body that does not reproduce the logged total):

* LO mastery is a Gaussian, so its posterior variance does not depend on the
  outcome: each check adds its precision `1/posterior_var - 1/prior_var` to
  the variance the earlier checks left (one deterministic expected branch);
* each facet's variance shrinks by the earlier checks' evidence, against the
  evidence mass they add (`w * discount` each), exactly the reward's formula;
* the hypothesis EIG is counted once per learning object (an approximation:
  an episode's observations are re-valued one at a time on the observed
  posterior by the `probe_episode` site; labelled in each receipt's
  `conditional_parts_nats`).

For the first check the terms reproduce the reward's number exactly. Teach-backs
(scheduler) and project probes (plan engine) use it; each candidate gets a
receipt (its step, its own valuation as `subject`, `conditioning`:
`none_chosen` | `chosen_before` | `unavailable`, `unconditioned_eig_nats`).
Three structural constants repeat the reward's variance floor and default
facet variance and set the reconstruction tolerance; all are registered in
the parameter registry. On the linear_algebra copy the decomposition
reproduced every teach-back's total (`conditioning: chosen_before`).

### F3: the episode maximum is lifted with the session cap

`probe_episodes.episode_maximum_binds` gates both the completion policy's
`observation_budget_exhausted` and `probe_blocks.block_complete`'s close and
block size: the count ends an episode only below mvp-0.17, with the
`probe_episodes` sub-switch off, or in a calibration session (the learner's
opt-in lifts the value rule, so the count is what ends that measurement).
The receipt keeps the counterfactual (`former_cap.episode_maximum`). The
test serves and records a real fifth observation in one episode. Honest
label: the probe contract gains `value_stopping` at mvp-0.17, and the desktop
and TUI headers then say "question N · continues while the next question is
worth your time" instead of "of up to 4" (the only frontend change).

### F4: the whole slate is valued

`followups._intervention_value` values every gate-passing slate candidate
(each with its hypothesis conditionals, facet EIG and familiarity discount)
in one `value_candidates` call: `rank_feasible` ranks and stops where a
decision is at stake, the EIG fallback otherwise. The best candidate that
pays (`SiteDecision.chosen`) is queued and the slate rows mark it selected;
the follow-up stops only when the best remaining one does not pay. The
receipt names the old ranking's pick (`context.slate_ranking_pick`). With no
candidate there is nothing to value, and the need is recorded whatever the
count (the first build's `voi_no_candidate` suppression is gone with the
count it depended on).

### F5: the value order reaches the chooser

Admitted project probes carry their admission order as `PoolItem.plan_rank`
(the rank of the position each moves into). `order_rank` (plan rank, else the
scheduler's rank) feeds the block source's `planner_value`, the new lane's
order and `reentry_order`. Below mvp-0.17 no item has a plan rank, so every
order is the scheduler's exactly. `PoolItem.as_dict` adds `plan_rank` only
when set.

### F6: the loss table decides across the posterior

A decision is at stake when the hypotheses with posterior mass route to two
or more repairs through a complete loss table; the plausibility cutoff only
describes the belief in the receipt. The EIG fallback is kept for its
specified cases: no complete loss table, one repair across the posterior, or
`rank_feasible` abstaining or excluding an input (`value_uncertain`). The
test sweeps the prior from 0.85 to 0.99: EVSI decides throughout and its
value only falls.

### F7: no floors

The first follow-up and the first teach-back are valued like any other; the
former count is read only for the receipt's counterfactual (`would_bind`,
`cap_comparison`) and the switched-off path. Project probes were already
valued from the first; their counterfactual counts the probes planned today
plus those admitted before each step.

### F8: recommended and served

`SiteDecision.as_dict(served_ref=..., served_by=...)` adds `recommended_ref`
(value's pick), `served_ref` (= `chosen_ref`), `served_is_recommended`,
`served` (the served candidate's complete forecast: emission alphabet,
predicted outcomes, likelihood rows) and `served_by`. The scheduler's commit
passes the item at the front with `scheduler_seeded_exploration` (and its
rate) or `scheduler_greedy_order`, the selection propensity and the greedy
item; the sidecar/TUI door passes `learner_opened_item` (a refused item gets
its own valuation as `subject`, not `served`); a manual follow-up passes
`manual_override`.

### F9: trigger quality and valuation stay separate

`gate_fit` excludes `voi_stopping.VALUATION_SUPPRESSION_REASONS`
(`voi_value_below_minutes_cost`) from silent negatives, and a manual override
whose only would-suppress reasons are valuation ones yields no label (the
trigger did fire). `would_auto_fire` stays honest (False: value would have
stopped it).

### The review's "claims that don't hold"

* *Every decision is logged with its forecast as durable calibration input*:
  now true for follow-ups (F1) and for explored probes (F8). The other sites
  already wrote to tables no rebuild clears (`router_decisions` RAW_LEDGER,
  the presentation's selection components, `probe_episodes`).
* *The best probe per minute is planned first*: now true through the chooser
  (F5).
* *`maximum_observations` is outside the four-cap decision*: agreed, it is
  not; lifted (F3). The stage notes are corrected.
* *The value-based replacement is complete*: conditional valuation added
  (F2) and the floors removed (F7).

### Spec conformance after the fixes

| Requirement | Assessment |
|---|---|
| Lift probe counts onto value | Session cap and episode maximum both lifted (calibration sessions and the kill switch keep the counts) |
| Follow-up selection and stopping | Whole eligible slate valued from the first intervention; stops only when the best remaining candidate fails |
| Teach-back stopping | Valued from the first, greedily and conditionally |
| Project-probe selection | Greedy conditional admission; the value order reaches the block score, the chooser and re-entry |
| Greedy conditional information gain | Present (`greedy_information_admission`); the hypothesis term over the expected posterior branches since the re-review (§7.4) |
| Shared valuation machinery | Unchanged: EVSI/EIG primitives through `value_candidates`; the adapter is this stage's, pending the sources spec's `value_candidates` |
| Successor and kill switches | Unchanged; every switched-off path still equals mvp-0.16 (tests) |
| Heuristic parameter labels | Unchanged; EVSI applicability no longer depends on the plausibility cutoff (F6) |
| Durable receipts and replay | Follow-up receipts survive rebuild and replay; probe receipts carry the served item's forecast |
| Migration and table ownership | After the re-review: migration 188's `followup_value_decisions` (RECEIPT, one owner store) carries each follow-up decision |

## 3. Refreshed report (backup-API copies)

`scripts/voi_cap_report.py --simulate 2000` rerun after the fixes on the same
copies under `fixtures-local/voi-copies/` (already at mvp-0.17; no upgrade
step ran; the owner's vaults were not read). The script now reports each
teach-back's own valuation and its conditioning.

**History, follow-ups the former cap suppressed:**

| | linear_algebra | probability |
|---|---|---|
| first build | `agree`: old winner 1.66 min against 2.28 (stop) | `agree`: 1.90 min against 3.00 |
| after the fixes | **`later`**: the whole slate is valued (F4) and `pi_orient_incomplete_spec_02` pays, 2.17 min against 2.03 | `agree`: 1.95 min against 3.00 |

**Now** (one Today build, sites on vs off): linear_algebra keeps all three
teach-backs (43 vs 41 items), on three different LOs, so conditioning
(`chosen_before` for the second and third) leaves their values unchanged:
69.8, 57.8 and 20.0 minutes against 3.0 each. probability: 67 vs 67, no
teach-back. Build time 10 ms vs 12 ms and 7 ms vs 8 ms.

**Synthetic probe episodes (labelled synthetic; same card, prior and
45-second probe as the stage report):**

| | point conditionals, 2,000 learners | robust ensemble (129 members), 200 learners |
|---|---|---|
| value stops after 1 answer | 1,533 (76.7%; was 51.8%) | 200 (100%; was 71.0%) |
| after 2 / 3 / 4 answers | 340 / 79 / 32 | 0 / 0 / 0 |
| continues past 4 (now within the same episode, F3) | 16 (0.8%) | 0 |
| earlier than the cap of 4 | 1,952 (97.6%; was 89.5%) | 200 (100%) |
| `decision_stable` reached when value stopped | 23 (1.2%; was 19.9%) | 0 |
| decisions by method | 2,000 robust EVSI (every stop), 2,663 EIG (every continue: `rank_feasible` abstained on an action flip and the EIG fallback, `value_uncertain`, paid) | 200 robust EVSI (the stops), 200 EIG (the first steps, the same abstention) |

Read: F6 is the cause. In the traced runs (two seeds), after one answer the
top hypothesis holds about 0.79 and the others each fall below the 0.10
plausibility cutoff; the
first build then stopped weighing the repair decision and continued on the
EIG objective (about 12 minutes of "value" against 0.75), while EVSI over the
whole posterior says the next 45-second answer changes the repair with
expected value 0.03 minutes. With today's heuristic loss model (3 minutes a
repair), value therefore stops nearly every synthetic episode after one
answer. This strengthens the stage's open question 1.

## 4. Paid calls

None. Every test uses fakes; the report runs locally on copies. $0.00.

## 5. Gate

Run at `6e558328` (the fix commit; the commit that adds this file is
documentation only), `TMPDIR` = the worktree's `fixtures-local/tmp`, the two
suites under `flock /tmp/learnloop-fullsuite.lock`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 15 kept, 0 broken |
| `flock … uv run pytest -n auto` | **9,019 passed**, 0 failed (424 s) |
| `flock … uv run pytest -m durability` | **95 passed**, 8,924 deselected (125 s) |
| Frontend (`apps/learnloop-tauri`): `npm install`, `npm run typecheck`, `npm test`, `npm run frontend:build` | ok; typecheck clean; **182 passed** in 35 files (vitest, the new header case included); build ok (the usual chunk-size warning) |
| `cargo check` | not run: nothing under `src-tauri` changed |
| DB reference scripts | not run: no schema change (no migration, no new table) |

Stage tests: `tests/test_voi_stopping.py` 61 cases (44 before; four
tests rewritten and 15 added for F1 to F9, two of them parametrized),
`tests/test_mvp017_upgrade.py` 12, all passing.

## 6. Open questions for the owner (added by the fixes)

1. **Episodes now stop after one answer almost always** (synthetic: 76.7% on
   point conditionals, 100% on the robust ensemble) because EVSI weighs the
   whole posterior (F6) against a 3-minute heuristic repair cost. Same choice
   as the stage's question 1, with sharper numbers: keep it live behind
   `voi_stopping.probe_episodes`, or hold the probe site off until the
   `evsi/calibration` report has scored live forecasts?
2. *Resolved by the re-review (§7.4):* the candidates now carry their
   `P(E | H)` rows and the hypothesis term is the exact conditional.
3. **A follow-up with no candidate records a generation need whatever the
   count** (F4/F7; the first build suppressed further ones as
   `voi_no_candidate`). Needs are deduplicated per LO, intent and facets and
   generation is spend-capped. Keep?
4. **The value decides the first follow-up and teach-back too** (F7), which
   settles the stage's question 3 in the direction the spec's text reads;
   the owner may still prefer the old floor.

## 7. Re-review (Codex job `20261013-053803-RzVqmE`)

Codex re-reviewed the fixes at `2773543d` (verdict REOPENED): F1 and F2
reopened, F3 confirmed fixed, two new Medium findings (F10, F11). Every open
finding reproduced at `2773543d` and is fixed in `086c24c0`; none was
rejected. Owner decisions in force as in the first round.

### 7.1 Reproduction at `2773543d`

Throwaway tests against the unchanged code (outputs as observed):

| Id | What the reproduction did | Observed at `2773543d` |
|---|---|---|
| F1 (a) | no candidate: a generation need is recorded; the item is added; the same attempt is evaluated again and queued; `rebuild_all_derived_state` | `followup_receipt` after the rebuild: `None` (the need took the attempt's one `decision_features` row; the queue's insert was ignored) |
| F1 (b) | 10,000-minute candidates: value suppresses the follow-up; then the learner's manual override queues one | the receipt holds only the suppression (`decision: stop`, no `served_by`); the manual decision's forecast is lost |
| F2 | four equally likely hypotheses, two checks on one LO worth `ln 2` each (independent bits), `InformationState().after(first)` | the second check's conditional hypothesis term: `0.0` (true value `ln 2` = 0.693) |
| F10 | project probes A (12 minutes, `{facet_x: 2, facet_y: 1}`, 1,146.8 minutes of value) and B (5 minutes, `{facet_x: 1}`, 33.7 minutes alone) on one LO, five minutes to spend | A admitted first; B stopped at 0.0 minutes conditional on A; `LegacyLanesSource.candidates` with five minutes: none (the plan is empty; B alone fits) |
| F11 | the probe vault plus a teach-back, `selection_exploration_rate = 0`, value drops the teach-back | greedy head `pi_svd_teach_001` (draw probability 1); the served probe `pi_svd_define_001` receipt: `selection_propensity: 0.0` |

### 7.2 Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Later follow-up decisions on one attempt are not recorded (reopened) | fixed | `086c24c0` | `test_a_need_then_a_queue_on_one_attempt_keeps_both_decisions`, `test_an_automatic_suppression_then_a_manual_follow_up_keeps_both_decisions` (both across two rebuilds and an LO replay), `test_each_follow_up_decision_keeps_its_own_receipt_through_rebuilds` (rewritten: a later decision is a new row, the first is unchanged; the table refuses UPDATE and DELETE), `test_a_value_suppressed_follow_up_keeps_its_receipt`, `test_below_the_successor_no_follow_up_receipt_carries_a_value_decision` |
| F2 | High | Hypothesis information is zeroed after one check per LO (reopened) | fixed | `086c24c0` | `test_hypothesis_information_is_valued_over_the_expected_posterior_branches` (independent bits keep `ln 2`; a repeat adds 0; a 90%-accurate earlier check leaves `h(0.1)`; the reward's scale; another episode is independent), `test_greedy_admission_keeps_independent_checks_and_drops_a_repeat`, `test_the_plan_values_probes_on_one_episode_over_its_hypotheses`, `test_the_scheduler_hands_an_in_episode_probe_its_likelihood_rows`, `test_past_the_branch_bound_posteriors_merge_and_the_receipt_says_so` |
| F3 | High | The episode maximum overrides value | confirmed fixed by the re-review | `6e558328` | no change |
| F10 | Medium | An unplannable probe suppresses a worthwhile alternative | fixed | `086c24c0` | `test_a_probe_the_plan_cannot_fit_neither_takes_a_slot_nor_discounts_another` (the reviewer's scenario: B is planned in a five-minute block; plus the cumulative budget), `test_the_plan_values_project_probes_at_the_successor_and_counts_them_below` (the plan passes its own minutes) |
| F11 | Medium | Served-probe receipts can record zero selection probability | fixed | `086c24c0` | `test_a_served_probe_records_its_probability_over_the_composed_queue` (the reviewer's scenario through `build_due_queue`: 1.0 over the composed outcomes, the draw's 0.0 kept as `base_draw_propensity`, equal to the offer trace's own head probability), `test_an_explored_probe_carries_its_own_forecast` (now a real seeded draw: 0.25 composed and base) |

### 7.3 F1: one receipt per decision (migration 188)

The first fix rode on the follow-up's `decision_features` row, which is one
row per source attempt (`UNIQUE(decision_id, decision_type)`, first write
wins), so any later decision on the same attempt was dropped. Migration 188
adds `followup_value_decisions` (RECEIPT, append-only by trigger): one row per
follow-up decision the value rule takes part in, each with its own id and a
per-attempt `decision_ordinal` (assigned in the INSERT itself, so atomic under
SQLite's write lock), its `source_attempt_id`, the outcome
(`queued_*`, `suppressed_voi_value_below_minutes_cost`,
`created_need_for_generation`, `created_need_no_discriminator`), the verdict,
`manual_override`, the recommended and served refs, the need id, and the
`SiteDecision.as_dict` body (`decision_json`, NULL when nothing was valued).
Written by the live follow-up path at mvp-0.17 with `voi_stopping.followups`
on (one owner, `db/stores/followup_value.py`); never by a rebuild or a replay.
`voi_stopping.followup_receipts(repository, attempt_id)` reads them in
order; `followup_receipt` returns the latest valued one.

The follow-up's `decision_features` row is mvp-0.16's again: the first fix's
`context.voi_stopping` key and its extra row on a value suppression are gone,
so a suppression no longer takes the attempt's one features slot and a later
manual follow-up writes its features as before the stage (the test checks
this). Not a new table for its own sake: main's `voi_forecasts` (184,
`evsi/calibration`) is the natural home at the merge; this branch cannot
rebase onto it, so 188 is a placeholder that may fold into it.

Head fixture: `migration_head_187` became `migration_head_188` (only 188
applied in place with the project's incremental migrator, rollback journal,
`integrity_check` ok, `foreign_key_check` clean); its README, the 12 test
paths, both reference scripts and their `SCHEMA_HEAD` follow. The SQL-owner
registry (`tests/test_architecture.py`) names the new store. The DB reference
generator gives the table a purpose note and the tutor-and-remediation family
(with `followup_tasks`).

### 7.4 F2: the hypothesis term over expected posterior branches

`voi_stopping.HypothesisChannel` carries a check's likelihood rows `P(E | H)`
over its open probe episode's locked hypotheses (`belief_key` = the episode),
with the episode's current posterior. The scheduler hands every in-episode
probe these rows (`ScheduledItem.hypothesis_channel`, built by
`voi_stopping.hypothesis_channel_body` from the eligible instrument's
composed conditionals, the same rows the probe-episode site values; never
persisted or compared; attached only while the teach-back or project-probe
site is on). `InformationState` keeps, per episode, the expected posterior
branches the admitted checks' outcomes leave (`probability, posterior`),
merged when posteriors agree to 12 decimals; a later check's hypothesis term
is `scale * sum_b p_b * EIG(P(E | H), posterior_b)` = `scale *
I(E; H | E_admitted)` (outcomes independent given H). `scale` is the reward's
logged term over the check's standalone EIG, so the first check reproduces
`probe_eig_total` exactly (the decomposition check still applies). With the
hypothesis-EIG objective this is exact; with the §7.4 predictive objective the
reward's term is scaled by the conditional hypothesis information
(an approximation, labelled `expected_posterior_branches:predictive_term_
scaled_by_hypothesis_eig`). A label a check has no row for is one it says
nothing about. Each receipt names its `hypothesis_conditioning`.

Two bounds that are not count caps, registered as structural constants:
branches merge at 12 decimals (`_BRANCH_MERGE_DIGITS`), and past 4,096
branches per episode (`_MAX_BELIEF_BRANCHES`) they merge at fewer decimals
(`_COARSE_MERGE_DIGITS`, keeping total probability and the mean posterior),
labelled `hypothesis_branches: coarsely_merged` in later receipts. The
once-per-LO rule survives only for a check with a hypothesis term and no
rows (labelled `once_per_learning_object`); the scheduler gives every
in-episode probe its rows.

### 7.5 F10: feasibility inside the greedy selection

`greedy_information_admission` takes `minutes_budget` and
`max_item_minutes`. At each step a check is admissible only when its minutes
fit what the admitted checks leave of the budget, and one block; a check that
does not fit is still valued for its receipt but never admitted
(`does_not_fit_plan_minutes`, via `Candidate.infeasible_reason`), so nothing
is conditioned on it. The plan engine passes the plan's own minutes and
`min(BLOCK_MAX_MINUTES, minutes)`; a probe left out this way stays "later"
with the reason "a due project probe that does not fit today's minutes".
These are the constraints known before the split (the lanes' shares come from
the classified pool, and the maintain lane can receive the plan's whole
minutes when the other lanes are idle), so a probe that fits may still lose a
block to another lane in the chooser; it is then simply not planned, and
nothing after it was discounted for an impossible probe.

### 7.6 F11: the served item's probability over the composed queue

The presentation receipt's `served_by.selection_propensity` is now
`P(served item heads the composed queue)`: every outcome of the seeded draw is
recomposed through the build's own `compose` (the factored
`_support_outcomes`, which `_fill_offer_trace` now uses too, so the offer log
and the receipt share one enumeration), and the probability sums the outcomes
whose head is the served item (`selection_propensity_kind:
composed_outcomes`). The pre-composition draw probability is kept apart as
`base_draw_propensity`. Router R1's existing `scheduler_exploration.
exploration_propensity` (the draw) is unchanged.

### 7.7 Open questions for the owner (added by the re-review fixes)

1. **The F10 bound is the plan's minutes and one block**, not the maintain
   lane's share (known only after the split). Enough, or should project
   probes be admitted against the maintain lane's allotment once split?
2. **Predictive-objective episodes** scale the reward's hypothesis term by the
   conditional hypothesis EIG (labelled approximation). Acceptable until the
   predictive objective has its own conditional form?
3. **Migration 188 at the merge**: fold `followup_value_decisions` into main's
   `voi_forecasts` (site `followup_intervention`, one row per decision), or
   keep it beside?

### 7.8 Paid calls

None. Every test uses fakes. $0.00.

### 7.9 Gate

Run at `086c24c0` (the fix commit; the commit that adds this section and
the regenerated references is documentation only), `TMPDIR` = the worktree's
`fixtures-local/tmp`, the two suites under
`flock /tmp/learnloop-fullsuite.lock`. Before the gate, the reviewer's F2
scenario was rerun by hand against `086c24c0`: four equally likely
hypotheses, two checks revealing independent bits. Conditional on the first,
the second's hypothesis term is 0.6931 (`ln 2`), a repeat of the first is 0,
and the label is `expected_posterior_branches`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 15 kept, 0 broken |
| `flock … uv run pytest -n auto` | **9,028 passed**, 0 failed (344 s) |
| `flock … uv run pytest -m durability` | **95 passed**, 8,933 deselected (99 s) |
| Frontend (`apps/learnloop-tauri`; unchanged since the first round): `npm install`, `npm run typecheck`, `npm test`, `npm run frontend:build` | ok; typecheck clean; **182 passed** in 35 files (vitest); build ok (the usual chunk-size warning) |
| `cargo check` | not run: nothing under `src-tauri` changed |
| DB reference scripts (schema changed: migration 188) | `db_generate_reference.py`: schema head 188, 308 table notes, the new `followup_value_decisions` note included; a second run is stable. `db_validate_reference.py`: `errors: []` (366 owned notes, 852 path-qualified table links, 4,064 wikilinks checked) |

Stage tests: `tests/test_voi_stopping.py` 70 cases from 58 test functions
(61 cases from 49 functions before the re-review: 9 added, the F1 receipt
test and the F11 explored-probe test rewritten), and
`tests/test_mvp017_upgrade.py` 12. All pass.

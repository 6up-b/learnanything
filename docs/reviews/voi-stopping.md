# Value-of-information stopping (mvp-0.17)

Branch `serving/voi-stopping`, worktree `learnanything-voi`, from `main` at
`11177f6f` (mvp-0.16 LATEST, migrations to 183). Owner-directed
(2026-10-12/13): "lift the other 4 caps on the same value of information
basis"; follow-ups and probes are chosen by EIG/EVSI ("multiple follow ups
might be high ROI to search for the true misconception or decide between
hypotheses/decide between actions"), not hard caps. Part 2 is the Guide-fix
audit's three open questions (`docs/reviews/guide-overlay.md`). Owner
decisions in force: recommended defaults accepted; frictionless defaults
(honest labels, generous defaults, live behind kill switches, no shadow
stage).

Both parts change what is served, so they ship as one algorithm successor,
**`mvp-0.17` (a placeholder label: expect relabelling at the merge)**, with
**migration 187 (a placeholder number: 184 to 186 are held by branches in
flight)**.

## 1. What changed

### Part 1: four count caps lifted onto value of information

`src/learnloop/diagnosis/voi_stopping.py` (new). One rule for every site:
serve the next observation while its value of information pays for its
minutes. Kill switch `voi_stopping.enabled`, one sub-switch per site; each
former cap stays in config and is exactly the switched-off path.

| Site | Former cap (the kill-switch path) | What decides at mvp-0.17 | Scope |
|---|---|---|---|
| `probe_episode` | `probe.episode.session_qualifying_observation_cap` (4 qualifying observations per session) | Each next observation of an episode is served while its value pays. When it no longer does, the sequential block closes (the learner's deferred feedback is released) and the episode completes with the new `completion_reason = 'value_of_information_stop'`, its decision kept in the new `probe_episodes.completion_detail_json` (migration 187) | every observation |
| `followup_intervention` | `scheduler.followup.max_interventions_per_lo_per_session` (1) | A further intervention on an LO in a session (where the cap bound) is queued while its value pays; otherwise suppressed `voi_value_below_minutes_cost` (or `voi_no_candidate`: a further intervention never records a generation need). The first one keeps the existing trigger gate. A learner's manual override still wins; the log says what value would have done | further interventions |
| `teach_back` | `teach_back.session_cap` (1 per built queue) | The cap becomes a floor: each teach-back beyond it stays in the queue while its value pays, ordered by the queue's own value order (a teach-back is a valued probe, router D11), so it heads the offer whenever it is the highest-value probe | further teach-backs |
| `project_probe` | `plan.project_probes_max_per_day` (4) | No count: every due project probe whose value pays takes the maintain lane, the probes ordered among themselves by value per minute, and the plan's finite minutes bound how many are planned. A probe whose value does not pay stays "later" with that reason | every due probe |

Gates: `voi_stopping_active(config, site)` is true only at a
`VOI_STOPPING_VERSIONS` member with the switch and the site's sub-switch on. A
calibration session (the learner's explicit opt-in) lifts the probe rule as it
lifted the session cap. Wired at: `scheduling/scheduler.py` (probe candidates,
further teach-backs, the offer trace), `diagnosis/probe_episodes.py`
(`probe_serving_block_reason` drops the session arm; `probe_value_block_reason`
for the sidecar and TUI commit doors; the completion policy),
`diagnosis/probe_blocks.py` (a sequential block closes on a value stop),
`diagnosis/followups.py`, `daily_plan/lanes.py` and `daily_plan/engine.py`.

### The value rule: existing machinery, no new constants

* **Information (EIG, nats)** over the learner's rival hypotheses through the
  existing adapters: a probe instrument's composed `P(E | H)`
  (`probe_families.instrument_conditionals`), over the episode's pinned
  robust ensemble (member 0 plus 128 draws) when it has one; a follow-up's
  hypothesis-set conditionals (`probes.hypothesis_conditionals`, factored out
  of `probes.expected_information_gain` unchanged) plus the slate's facet EIG,
  familiarity-discounted, without the slate's ranking-only boosts; a
  teach-back's or project probe's `probe_eig_total` (the selection reward's
  LO-mastery and facet-recall entropy reduction). The robust EIG is the
  credible set's lower quantile.
* **Decision value (robust EVSI, minutes)** where a next-action decision is at
  stake: each plausible hypothesis (posterior at least
  `probe.episode.action_equivalence_plausible_threshold`, the existing
  plausibility cutoff) maps through `probe_hypotheses.triage_reason_for_label`
  to its triage route's first intervention (a misconception's or confusion's
  repair targets that belief, so two rival misconceptions are two repairs:
  the owner's "search for the true misconception"), and
  `action_loss.build_loss_table` prices a wrong repair in wasted
  learner-minutes. At stake = two or more distinct repairs among the plausible
  hypotheses. Then `evsi.rank_feasible` values and stops: continue while the
  robust EVSI's lower bound exceeds `lambda_time * minutes + burden`.
* **Otherwise** (no decision at stake, a route missing, or `rank_feasible`
  abstaining on an action flip or excluding an input) the robust EIG is
  converted to minutes with `robust_composition.VALUE_PER_NAT_MINUTES`, as
  `evaluate_selection`'s stop rule does, against the same cost. The
  abstention fallback is labelled `value_uncertain` (reader spec §9.3).
* **Minutes** are the learner's own: the item's median latency, else its
  practice mode's median shrunk toward the authored estimate with DL1's three
  pseudo-observations, else the authored estimate (a probe card's expected
  seconds, an item's `expected_minutes`), else
  `action_loss.DEFAULT_INTERVENTION_MINUTES`; project probes use the plan's own
  estimate.

Every decision parameter is read from where it already lives and labelled
**heuristic** in each receipt: `lambda_time` 1, `burden_cost` 0, the
nat-to-minutes scale 60, the robust quantile 0.10, the ±0.15 stress, the loss
model (`triage_route_wasted_minutes`). The `evsi/calibration` stage will
recommend values. Four new module constants only shape estimates and
receipts and are registered in the parameter registry
(`DURATION_PSEUDO_OBSERVATIONS`, DL1's constant repeated because serving
never imports the plan; `DEFAULT_LATENCY_CAP_MINUTES`;
`MAX_RECORDED_CANDIDATES`; `_ROUND_DIGITS`).

### Part 2: the probe hypothesis lane reads the diagnoser's verdict

`probes.build_hypothesis_set`'s legacy raw-event lane and its neighbour lane
(`_neighbor_misconceptions`) read error events through `_lane_error_events`:
at mvp-0.17 with `diagnosis.probe_lane_reads_diagnosis` on, through the
diagnosis overlay (`active_errors_by_learning_object_overlaid` and the new
all-LO `Repository.active_error_events_overlaid`), so a blind-graded event's
`is_misconception` is the diagnoser's verdict once its live diagnosis is in
force. While a diagnosis is pending the event is left out
(`diagnosis.probe_lane_pending = "hold_out"`, the recommended default;
`keep_prior` admits it on the stored flag). A failed or skipped diagnosis
never arrives, so its event reads as stored. `ActiveErrorEvent` gains
`attempt_id` (additive). A joint-graded vault reads exactly what it read. The
follow-up misconception gate (`followups._choose_intervention_item`) is the
lane's live consumer, so follow-up EIG no longer gives prior mass to a
misconception the diagnoser ruled out (the audit's scenario A; scenario B, a
diagnoser `learner_state` over a blind prior of False, now enters the lane).

### Display and logging (every version: neither serves anything)

* **`learnloop misconceptions`**: lists by the diagnoser's verdict where its
  diagnosis is in force. The `--json` shape is kept and **two fields are
  added, said rather than silently changing a meaning**:
  `misconception_verdict` (the verdict the listing uses) and `verdict_source`
  (`diagnosis` | `diagnosis_pending` | `stored`). `is_misconception` keeps its
  stored meaning (the grader's verdict on a joint grade, the taxonomy prior on
  a blind one). Joint vaults list exactly what they listed, text output
  included.
* **`decision_features` receipt**: the ability vector's
  `misconception_posterior_by_error_type` reads the overlay, and every row's
  `context` now says so (`"error_events": "diagnosis_overlay"`), so a learned
  router can tell these rows from older ones.

### Version, upgrade, defaults, migration

* `VOI_STOPPING_ALGORITHM_VERSION = "mvp-0.17"` appended to `SUCCESSOR_CHAIN`
  (LATEST; new vaults start here); `VOI_STOPPING_VERSIONS` gates both parts.
* `learnloop/voi_stopping_upgrade.py`: `upgrade_to_mvp017` accepts mvp-0.16,
  or mvp-0.9 to mvp-0.15 through `upgrade_to_mvp016`, passing the chain's
  advisory-guard notes through and prefixing its refusals; it freezes the
  manifest, rebuilds the same projection namespace before the atomic rename.
  `learnloop upgrade` defaults to it; `--to mvp-0.17` is accepted.
* New config: `[voi_stopping]` (`enabled`, `probe_episodes`, `followups`,
  `teach_back`, `project_probes`, all true) and
  `diagnosis.probe_lane_reads_diagnosis = true`,
  `diagnosis.probe_lane_pending = "hold_out"`; modelled defaults, left out of
  the decision-only template. Every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry was
  recomputed (each moves only because the effective config gains the keys)
  and `mvp-0.17` added.
* **Migration 187** rebuilds `probe_episodes` (same columns, indexes and data)
  so its `completion_reason` CHECK accepts `value_of_information_stop`, and
  adds the nullable `completion_detail_json`. `probe_episodes` stays
  WORKFLOW; nothing below mvp-0.17 writes either. `fixtures/migration_head_183`
  became `migration_head_187` (only 187 applied, rollback journal,
  `foreign_key_check` clean, `integrity_check` ok); its README and every
  hard-coded path (12 existing test files, the two reference scripts and
  their `SCHEMA_HEAD`) follow. A VOI-stopped episode is not a "trusted" hypothesis
  conclusion for depth-rung entry (`curriculum/depth_rungs.py` keeps its
  list): a stop because more minutes do not pay is not a demonstration.
* Import contracts: the module sits in `diagnosis` beside the probe machinery
  it composes and reads `scheduling.evsi`/`action_loss` in the allowed
  direction; one frozen-cycle edge is added and documented
  (`scheduling.scheduler -> diagnosis.voi_stopping`, like the scheduler's
  other probe imports).
* References regenerated at head 187 (DB and config notes, 756 config leaves,
  44 sections); the CLI help snapshot refreshed (the `upgrade` help).

## 2. What remains as limits

Every remaining number is a cap on time or money, never a learning threshold:

* **Time.** The plan's finite minutes (`plan.default_minutes` and the
  remembered budget; the maintain lane's share `plan.maintain_max_share`) bound
  project probes and every planned block. A session's `available_minutes`
  stays the follow-up gate's `no_time` suppression. Each observation's own
  minutes are the cost the value must pay.
* **The learner's own stop.** "Stop for today" (always a candidate), "Stop
  diagnosing and teach me" (`stop_diagnosing_and_teach`), and a manual
  follow-up override.
* **Money.** Unchanged and untouched by this stage (diagnosis
  `max_calls_per_day`, the learner-text gap and practice-index spend caps):
  the valuation itself makes no model call.
* **The burden term the EVSI machinery already has:**
  `robust_composition.BURDEN_COST` = 0 minutes (heuristic).

Counts that are **not** among the four and still bind (listed for the owner,
not changed here): `probe.episode.maximum_observations` (4 per episode, the
`observation_budget_exhausted` completion; with it a single episode can never
run past 4, so "value continues past the former cap" needs a second episode
in the session), `probe.episode.onboarding_practice_ceiling_observations` (4,
a fresh vault reaches ordinary practice), `tutor_promotion.requested_items_per_session`,
`trace_evidence.max_elicitations_per_session`, `plan.reentry_max_items` and
the new-item admission caps.

## 3. Repeated-question guards kept, and why

No new guard was added. The existing ones are about the learner's experience
or the measurement's validity, not about learning:

* a probe is never served on a surface the learner has already answered
  (`administered_surface_exclusions`, the never-before-seen rule): a repeat
  measures memory of the question;
* a follow-up never re-serves the item just answered
  (`exclude_practice_item_id`): never the same item twice in a row;
* the queue and the plan pool hold each item once; a single-use
  `diagnostic_probe` surface is never re-served.

## 4. Every stop/continue decision is logged with its forecast

Each decision is a `voi_stop_forecast_v1` body (`SiteDecision.as_dict`): the
site, the decision and reason, the best candidate's forecast (emission
alphabet, predicted outcome distribution, prior, member-0 likelihood rows,
the action before and after each emission with its proxy
(`triage_route_repair` or `map_hypothesis`), EIG, `p_action_change`), the EIG
point/robust, the EVSI point/robust/UCB in minutes, the cost, the minutes and
their provenance, up to six candidate summaries, the `rank_feasible` verdict,
whether a decision was at stake (with the label-to-repair map, the loss table
hash and its duration sources), every parameter with its provenance
(`calibration_label: heuristic`), and the former cap's counterfactual
(`former_cap`: name, value, count, `would_bind`) with `cap_comparison`
(`agree` | `earlier` | `later`). Where:

| Site | Recorded on |
|---|---|
| probe episode (continue) | the committed presentation's `selection_components.voi_stopping`; the Today offer's `router_decisions.detail_json.voi_decisions`; the scheduler slate candidate's components (`voi_value_minutes`, `voi_cost_minutes`, `voi_stop`) |
| probe episode (stop) | `probe_episodes.completion_detail_json` (migration 187); the offer's `voi_decisions`; the withheld item's exclusion `voi_value_below_minutes_cost` |
| further follow-up | `attempt_surprise.gate_diagnostics_json.voi_stopping` (queued or suppressed) |
| further teach-back | the Today offer's `voi_decisions`; a dropped teach-back's exclusion is now `teach_back_value_below_minutes_cost` |
| project probe | the plan-block `router_decisions.detail_json.voi_decisions` (and the block decision detail) |

Below mvp-0.17 none of these keys is written. The body follows the
`evsi/calibration` branch's `voi_forecast_v2` field names (its
`voi_forecasts` table had not landed when this was built, so the existing
tables carry it); when that table lands, these sites add themselves to its
`VOI_SITES` and record there too.

## 5. Report: how often the former caps bound, and what value does instead

`scripts/voi_cap_report.py` on backup-API copies
(`learnloop.db.copies.copy_tree_with_databases`) of the worktree's committed
`fixtures/linear_algebra` and `fixtures/probability` snapshots, under
`fixtures-local/voi-copies/` (the owner's live vaults were not read). It
upgrades each copy through the chain (mvp-0.8 -> mvp-0.9 -> mvp-0.17; the
mvp-0.12 guard is advisory), then reports the history and one Today build.
Both copies' loss tables price every repair at the 3-minute heuristic default
(no logged attempt durations in `interaction_events`).

**History** (the copies' recorded sessions: linear_algebra 70 attempts in 11
sessions, probability 2 attempts in 1 session; neither has a probe
observation; 9 and 18 episodes wait in `pending_items` with no instrument):

| Site | Former cap | linear_algebra: cap bound | probability: cap bound | What value decides there (copy's current state) |
|---|---|---|---|---|
| probe episode | 4 qualifying observations / session | 0 (no qualifying observation) | 0 | nothing to decide: no episode in progress |
| follow-up | 1 intervention / LO / session | 1 (`lo_orient_to_the_vector_space_idea`) | 1 (`lo_analyze_and_optimize_nonuniform_collision_probab`) | **agree** both times: a decision is at stake and the robust EVSI is 1.66 min against 2.28 min (linear_algebra) and 1.90 min against 3.00 min (probability), so value also stops |
| teach-back | 1 / queue | 0 sessions with more than one teach-back attempt | 0 | see "now" |
| project probe | 4 / day | never applies (no project-probe provider on this base) | never applies | none |

**Now** (one Today build in a fresh session at mvp-0.17, sites on vs off):

| | linear_algebra | probability |
|---|---|---|
| queue length, value on / off | 43 / 41 | 67 / 67 |
| teach-back decisions | 3: 1 within the old cap (continue, agree), **2 past it (continue: later)**; values 69.8, 57.8 and 20.0 min against 3.0 min each (EIG method: no hypothesis set, no decision at stake) | none (no teach-back items) |
| probe-episode decisions | none (no episode in progress) | none |
| build time, best of 3 | 9 ms / 9 ms | 8 ms / 8 ms |

So on these snapshots the former caps bound twice (one follow-up each), and
value agreed both times; value would let two more teach-backs into
linear_algebra's queue. The teach-back values are large because a
teach-back's `probe_eig_total` (0.3 to 1.2 nats here) is multiplied by the
heuristic 60 minutes a nat: as built, a teach-back beyond the old cap almost
always pays, so in practice the plan's and the session's minutes are its
limit.

**Synthetic (labelled as such): how many observations value asks for in one
probe episode.** The production `contrast_confusable` card with its default
rows and the grader channel composed in (45 s a probe), a five-hypothesis
cold-start prior (robust grasp 0.30, confusion 0.20, surface-only 0.20,
unfamiliar 0.20, other 0.10), the copy's triage routes, a fresh instrument
each step; each simulated learner's true hypothesis is drawn from the prior
and each answer from its row.

| | point conditionals, 2,000 learners | robust ensemble (129 members), 200 learners |
|---|---|---|
| value stops after 1 answer | 1,036 (51.8%) | 142 (71.0%) |
| after 2 / 3 answers | 446 / 308 | 17 / 27 |
| after 4 (where the session cap would have bound alone) | 160 (8.0%) | 4 (2.0%) |
| continues past 4 | 50 (2.5%) | 10 (5.0%) |
| **earlier than the cap of 4** | **1,790 (89.5%)** | **186 (93.0%)** |
| `decision_stable` (85%) already reached when value stopped | 397 (19.9%) | 40 (20.0%) |
| decisions by method | 1,655 robust EVSI, 4,117 EIG (abstention fallback or nothing at stake) | 164 robust EVSI, 360 EIG |

`rank_feasible` abstains whenever its value clears the cost but the action
flips across the credible set or the ±0.15 stress; the fallback then
continues (the EIG in minutes is far above 45 s), so in effect value stops
exactly when the robust EVSI's lower bound falls to the minutes cost. With
`probe.episode.maximum_observations = 4` still in force, the "continues past
4" cases end at 4 within one episode.

Read: with today's heuristic parameters, value stops most episodes after one
or two answers, well before the former session cap of 4 and usually before
the episode's own `decision_stable` rule (85% top posterior) would have ended
it. The decision value is small because a wrong repair costs only about six
heuristic minutes, so once one hypothesis leads, a 45-second answer no longer
pays. This is the most consequential behaviour change of the stage, and it
rests entirely on heuristic numbers (lambda, the loss model, the minutes); it
is the first thing the `evsi/calibration` report should check against
outcomes.

**Cost.** On the copies the Today build's time is unchanged (no episode in
progress). With one in-progress episode and two eligible instruments (the test
vault, pinned robust channel) a build takes about 80 ms at mvp-0.17 against
4 ms at mvp-0.16; the time is `rank_feasible`'s stress re-valuation over the
129-member credible set. Each additional in-progress episode adds about that
much.

## 6. Tests

New: `tests/test_voi_stopping.py` (44 cases) and `tests/test_mvp017_upgrade.py` (12).

* Gates per site and per version; Part 2's gate independent of Part 1.
* The value rule: EIG-in-minutes against minutes; robust EVSI and
  `rank_feasible`'s stop where repairs differ (spread belief continues, a
  costly observation stops); rival misconceptions are rival repairs; a
  missing route means no loss table; every decision body serializes with
  predicted outcomes summing to 1, `p_action_change`, the heuristic
  parameters and the cap counterfactual.
* (a) below the successor the spent session cap blocks probes; at it value
  keeps asking past the cap (`later`) and stops where nothing pays
  (`earlier`), the sidecar/TUI door applies the same rule, a calibration
  session lifts it; the offer and the committed presentation carry the
  decision; a value stop closes the block and completes the episode with
  `value_of_information_stop` and its decision, only at the successor; while
  value pays the episode keeps asking.
* (b) further follow-ups: suppressed by count below; queued or suppressed by
  value at the successor with the decision in the gate diagnostics; the
  manual override wins and logs `would_suppress`; the first follow-up is not
  valued.
* (c) further teach-backs kept while they pay, dropped (first kept) when not.
* (d) project probes: no count cap, value-per-minute order, "later" when the
  value does not pay; end to end, the plan plans 5 at mvp-0.17 and 4 below it
  or with the sub-switch off, with the decisions on the plan-block rows.
* Part 2: a slip the diagnoser ruled out leaves the lane only at the
  successor; the lane switch restores the stored flag; a pending diagnosis is
  held out (`hold_out`) or admitted (`keep_prior`, and below the successor);
  a joint vault's lane is unchanged.
* CLI and `decision_features`: the diagnoser's verdict with the added fields;
  a joint vault only gains fields (text unchanged); the receipt's posterior
  follows the overlay and says so. Both tests fail with the overlay replaced
  by the raw read.
* Parity: with each kill switch (and each sub-switch) off at mvp-0.17 the
  probe queue, the follow-up decision and the teach-back queue equal
  mvp-0.16's exactly; at mvp-0.10, 0.14, 0.15 and 0.16 the new switches
  change nothing and the count cap still serves.
* Upgrade and replay (playbook items 3, 4, 6, 8): the chain and LATEST, each
  version's features, the upgrade from mvp-0.16 rewrites nothing, the guarded
  chain from mvp-0.10, refusals and idempotence, the CLI default, new vaults,
  every defaults snapshot, the head fixture's predecessor-to-successor path
  (FK check, doctor, idempotent rebuild), the rebuild at mvp-0.17 equals
  mvp-0.16's projection, and migration 187's schema.
* Updated: the version-chain assertions of the mvp-0.11/0.13/0.14/0.15/0.16
  tests and `test_recurrence_commands.py`, and every head-fixture path.

## 7. Paid calls

None. Everything ran on fakes or locally; no model route, no network, $0.00.

## 8. Gate

GATE_TABLE

## 9. Open questions for the owner

1. **Probe episodes now stop much earlier.** With today's heuristic
   parameters (3 minutes per wrong repair, lambda 1, a 45-second probe), value
   stops about 90% of synthetic episodes before the old cap of 4 and most
   after one answer, usually before `decision_stable`. Keep this live (the
   recommended frictionless default, behind `voi_stopping.probe_episodes`), or
   hold the probe site off until the `evsi/calibration` report has scored the
   first live forecasts?
2. **Teach-backs past the old cap nearly always pay.** Their information is
   the reward's `probe_eig_total` at the heuristic 60 minutes a nat, so on
   linear_algebra all three teach-backs stay (values 20 to 70 minutes against
   3). Is "only the plan's and the session's minutes limit them" the intent, or
   should a teach-back be valued over a hypothesis set (EVSI) once one exists
   for it?
3. **Scope of (b) and (c).** The first follow-up per LO per session and the
   first teach-back per queue keep their existing rules (the old cap is a
   floor); value decides only where the count used to bind. Should value also
   decide the first one (it could then stop earlier, as it does for probes)?
4. **Counts that remain.** `probe.episode.maximum_observations` (4 per
   episode) still ends an episode whatever its value, and the onboarding
   ceiling (4), `requested_items_per_session`,
   `trace_evidence.max_elicitations_per_session` and the plan's re-entry and
   new-item caps are counts too. Lift any of them onto value next?
5. **A value stop before the first answer.** An episode whose very first
   observation does not pay is withheld but stays `in_progress` (completion
   runs only after an answer). It is rare (value is highest at the prior);
   should it complete at entry instead?
6. **Depth-rung entry.** A `value_of_information_stop` episode is not a
   trusted conclusion for depth-rung entry (only `decision_stable`,
   `action_equivalent` and the strong-claim fast path are). Keep that?
7. **The `decision_features` marker** is written on every new selection row
   at every version (logging only; joint vaults log the same posterior as
   before plus the marker). Fine, or gate it on the successor?
8. **Placeholders and the calibration branch.** `mvp-0.17` and migration 187
   will be renumbered at the merge (the head fixture is now
   `migration_head_187`). When `evsi/calibration`'s `voi_forecasts` table
   lands, should these four sites also write there (they already carry its
   field names), and should the sidecar/TUI commit door's value refusal be
   persisted (today only the scheduler's offer and the episode's completion
   record it)?

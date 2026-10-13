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

**Revised by the Codex review fixes** (`docs/reviews/voi-stopping-codex-review.md`,
findings F1 to F9, and the re-review's F1, F2, F10 and F11): the sections
below describe the stage as fixed; where the first build differed, the fix is
named inline. **Then by voi-v2** (`docs/reviews/voi-v2.md`): the final
verify's F2, F10 and F12, and the multi-family EVSI study's ranks 1-3 behind
`voi_stopping.robust_gate_with_value`, `lookahead_max_checks` and
`robust_quantile` (the "robust quantile 0.10" and "the gate" below are the
switches' restore values).

Both parts change what is served, so they ship as one algorithm successor,
**`mvp-0.17` (a placeholder label: expect relabelling at the merge)**, with
**migrations 187 and 188 (placeholder numbers: 184 to 186 are held by
branches in flight)**.

## 1. What changed

### Part 1: four count caps lifted onto value of information

`src/learnloop/diagnosis/voi_stopping.py` (new). One rule for every site:
serve the next observation while its value of information pays for its
minutes. Kill switch `voi_stopping.enabled`, one sub-switch per site; each
former cap stays in config and is exactly the switched-off path.

| Site | Former cap (the kill-switch path) | What decides at mvp-0.17 | Scope |
|---|---|---|---|
| `probe_episode` | `probe.episode.session_qualifying_observation_cap` (4 qualifying observations per session) and `probe.episode.maximum_observations` (4 per episode; lifted with it, review F3: kept off the value rule and in a calibration session) | Each next observation of an episode is served while its value pays. When it no longer does, the sequential block closes (the learner's deferred feedback is released) and the episode completes with the new `completion_reason = 'value_of_information_stop'`, its decision kept in the new `probe_episodes.completion_detail_json` (migration 187) | every observation |
| `followup_intervention` | `scheduler.followup.max_interventions_per_lo_per_session` (1) | Every intervention on an LO, the first included (review F7), once the trigger gate fires: the whole eligible slate is valued and the best candidate whose value pays is queued (review F4); when none pays, suppressed `voi_value_below_minutes_cost`. With no candidate the need is recorded as for any first intervention. A learner's manual override still wins (value's best candidate is queued); the log says what value would have done | every intervention |
| `teach_back` | `teach_back.session_cap` (1 per built queue) | Every teach-back, the first included (review F7): admitted greedily, each valued conditionally on those already admitted (review F2), while its value pays; kept teach-backs stay in the queue's own order (a teach-back is a valued probe, router D11) | every teach-back |
| `project_probe` | `plan.project_probes_max_per_day` (4) | No count: due project probes are admitted greedily and conditionally (review F2) while their value pays and while they fit the plan's minutes (re-review F10: a probe is admissible only while it fits the minutes the probes admitted before it leave, and one block), take the maintain lane in that order and carry it as `plan_rank`, which the block score and the chooser read (review F5). A probe whose value does not pay, or that does not fit, stays "later" with that reason | every due probe |

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
  stake: each hypothesis with posterior mass maps through
  `probe_hypotheses.triage_reason_for_label`
  to its triage route's first intervention (a misconception's or confusion's
  repair targets that belief, so two rival misconceptions are two repairs:
  the owner's "search for the true misconception"), and
  `action_loss.build_loss_table` prices a wrong repair in wasted
  learner-minutes. At stake = two or more distinct repairs across the whole
  posterior through a complete loss table (review F6: the plausibility cutoff,
  `probe.episode.action_equivalence_plausible_threshold`, only describes the
  belief in the receipt; gating on it switched a near-sure belief onto the EIG
  objective and restarted measurement). Then `evsi.rank_feasible` values and
  stops: continue while the robust EVSI's lower bound exceeds
  `lambda_time * minutes + burden`.
* **Several checks chosen together** (teach-backs in one queue, project
  probes in one plan; review F2) are admitted greedily: each step values every
  remaining check given the belief the admitted ones are expected to leave
  (the reward's `probe_eig_total` decomposed from its own body: the LO-mastery
  Gaussian adds the check's precision, a facet's variance shrinks by the
  evidence the earlier checks add, and the hypothesis term is valued over the
  expected posterior branches the earlier checks on the same open episode
  leave, from the check's own `P(E | H)` rows, which the scheduler hands each
  in-episode probe as `ScheduledItem.hypothesis_channel`; re-review F2), and
  adding stops when the best remaining check does not pay. A project probe
  that does not fit the plan's minutes is never admitted nor conditioned on
  (re-review F10).
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
  their `SCHEMA_HEAD`) follow. **Migration 188** (re-review F1) adds
  `followup_value_decisions` (RECEIPT, append-only by trigger): one row per
  follow-up value decision, with its own id and per-attempt ordinal and its
  source-attempt link; the head fixture became `migration_head_188` (only 188
  applied in place, same checks). A VOI-stopped episode is not a "trusted" hypothesis
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
not changed here; `probe.episode.maximum_observations` was listed here until
review F3 lifted it with the session cap, which reader spec §18 and §20.7
name it with): `probe.episode.onboarding_practice_ceiling_observations` (4,
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
| probe episode (continue) | the committed presentation's `selection_components.voi_stopping` (its `served_by.selection_propensity` is the served item's probability over the composed queue, every draw outcome recomposed as the build composes, with `base_draw_propensity` kept apart; re-review F11); the Today offer's `router_decisions.detail_json.voi_decisions`; the scheduler slate candidate's components (`voi_value_minutes`, `voi_cost_minutes`, `voi_stop`) |
| probe episode (stop) | `probe_episodes.completion_detail_json` (migration 187); the offer's `voi_decisions`; the withheld item's exclusion `voi_value_below_minutes_cost` |
| follow-up | `followup_value_decisions` (migration 188, RECEIPT, immutable): one row per decision, queued, value-suppressed or a recorded need, each with its own id and ordinal and its source attempt (re-review F1: a later decision on the same attempt, such as the learner's manual follow-up, never overwrites an earlier one; a rebuild never clears them); read with `voi_stopping.followup_receipts`. A copy rides on `attempt_surprise.gate_diagnostics_json.voi_stopping` (DERIVED, for the feedback screen). The follow-up's `decision_features` row is mvp-0.16's again (a queue or a need only) |
| teach-back | the Today offer's `voi_decisions`, one receipt per teach-back (its greedy step, its own valuation as `subject`); a dropped teach-back's exclusion is now `teach_back_value_below_minutes_cost` |
| project probe | the plan-block `router_decisions.detail_json.voi_decisions` (and the block decision detail) |

Below mvp-0.17 none of these keys is written. The body follows the
`evsi/calibration` branch's `voi_forecast_v2` field names (its
`voi_forecasts` table had not landed when this was built, so the existing
tables carry it); when that table lands, these sites add themselves to its
`VOI_SITES` and record there too.

## 5. Report: how often the former caps bound, and what value does instead

*The numbers in this section are the first build's. After the Codex review
fixes the report was rerun on the same copies; the refreshed numbers (the
follow-up revaluation on linear_algebra is now `later`, and value stops more
synthetic episodes after one answer) are in
`docs/reviews/voi-stopping-codex-review.md`.*

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

Run at `cbfb9f5f` (the code is that of `65549c98`; the later commit is
documentation only), `TMPDIR` = the worktree's `fixtures-local/tmp`, the two
suites under `flock /tmp/learnloop-fullsuite.lock`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 15 kept, 0 broken |
| `flock … uv run pytest -n auto` | **9,001 passed, 1 failed** of 9,002 (417 s). The failure, `test_stuck_prompt.py::test_kill_switch_restores_dont_know_exactly`, compares mvp-0.12 with mvp-0.13 (code this stage does not touch) and its field mass depends on wall-clock familiarity between attempts; it passed in the previous full run and passes alone 3 of 3 |
| `flock … uv run pytest -m durability` | **95 passed**, 8,907 deselected (109 s) |
| DB and config references (`db_generate_reference.py`, `db_validate_reference.py`) | regenerated at head 187; validator `errors: []` |
| Frontend, `src-tauri` | not changed: not run |

The previous full run (at `bc756e53`) had 8,999 passed and 3 failed: the
`decision_features` compactness test expected the old context (fixed in
`65549c98`), and the two `test_diagnosis_isolation.py` cases timed out in the
real `codex sandbox` under load (16 of 16 pass alone).

## 9. Open questions for the owner

1. **Probe episodes now stop much earlier.** With today's heuristic
   parameters (3 minutes per wrong repair, lambda 1, a 45-second probe), value
   stops about 90% of synthetic episodes before the old cap of 4 and most
   after one answer, usually before `decision_stable` (after the review fixes,
   F6 above all: 97.6% before 4 and 76.7% after one answer on point
   conditionals, every robust episode after one answer; see the codex review
   file's refreshed report). Keep this live (the
   recommended frictionless default, behind `voi_stopping.probe_episodes`), or
   hold the probe site off until the `evsi/calibration` report has scored the
   first live forecasts?
2. **Teach-backs past the old cap nearly always pay.** Their information is
   the reward's `probe_eig_total` at the heuristic 60 minutes a nat, so on
   linear_algebra all three teach-backs stay (values 20 to 70 minutes against
   3). Is "only the plan's and the session's minutes limit them" the intent, or
   should a teach-back be valued over a hypothesis set (EVSI) once one exists
   for it?
3. **Scope of (b) and (c).** *Settled by review F7:* value decides the first
   follow-up and the first teach-back too (the spec does not make a cap a
   floor); the old count is only the receipt's counterfactual.
4. **Counts that remain.** *`probe.episode.maximum_observations` was lifted by
   review F3.* The onboarding ceiling (4), `requested_items_per_session`,
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
8. **Placeholders and the calibration branch.** `mvp-0.17` and migrations
   187 and 188 will be renumbered at the merge (the head fixture is now
   `migration_head_188`; main's 184 `voi_forecasts` may absorb 188's rows). When `evsi/calibration`'s `voi_forecasts` table
   lands, should these four sites also write there (they already carry its
   field names), and should the sidecar/TUI commit door's value refusal be
   persisted (today only the scheduler's offer and the episode's completion
   record it)?

## Landing onto main

Branch `merge/voi-onto-main` (worktree `learnanything-merge2`), from main
`9fd00e9fe` (the route rules, mvp-0.20 LATEST, with UX Phase 1; migration
head 199, head fixture `fixtures/migration_head_199`). §1-§9 above, the
Codex reviews and `voi-v2.md` describe the branch and keep its placeholders
(`mvp-0.17`, migrations 187/188). No paid call.

| Commit | What |
|---|---|
| `cbd26b3e7` | a real `--no-ff` merge of `serving/voi-stopping` (`88c933686`, unchanged), with the renumbering, the relabel and the composition below |
| `2ad33b5a5` | regenerated references |
| (this commit) | this section |

### Renumbered and relabelled

| On the branch | On main |
|---|---|
| migration `187_probe_value_of_information_stop` | `200_probe_value_of_information_stop` |
| migration `188_followup_value_decisions` | `201_followup_value_decisions` |
| `fixtures/migration_head_188` | `fixtures/migration_head_201` (main's `migration_head_199` renamed) |
| `mvp-0.17` (`VOI_STOPPING_ALGORITHM_VERSION`) | **`mvp-0.21`**, after the route rules' `mvp-0.20` |
| `voi_stopping_upgrade.upgrade_to_mvp017` | `upgrade_to_mvp021` |
| `tests/test_mvp017_upgrade.py` (add/add with main's route-check file) | `tests/test_mvp021_upgrade.py`; main's file kept |

- **Migrations.** `ls migrations` runs 1..201 with only main's historical
  gaps. Main's 184-199 touch neither `probe_episodes` nor `decision_features`,
  so 200's rebuild copies main's columns exactly (the table at 199 is the
  branch's base table) and 201's backfill reads main's `decision_features`
  unchanged. `tests/test_voi_v2.py::test_migration_201_backfills_a_legacy_follow_up_receipt_once`
  builds a database at 200 from main's 1..200 with the real incremental
  migrator and applies 201: the suppression and the manual queue are
  backfilled once, the mvp-0.16 row is not, a later decision is ordinal 2. No
  owner vault ever ran the branch's 188; the head fixture has no legacy row.
  Each migration's comment names both numbers.
- **Head fixture.** `git mv fixtures/migration_head_199 fixtures/migration_head_201`;
  a backup-API copy (`learnloop.db.copies.backup_database`) of its database
  had only 200-201 applied through `learnloop.db.migrate.apply_migrations`,
  then `wal_checkpoint(TRUNCATE)`, `journal_mode=DELETE`, `integrity_check`
  ok, `foreign_key_check` clean, no `-wal`/`-shm`, and was copied back with
  the backup API. Its README says so. Every hard-coded head path moved:
  the branch's own tests, main's `test_mvp017/018/020_upgrade.py`,
  `test_reading_step_switch.py`, `test_route_rules_in_grader.py` (whose
  max-migration assertion is now 201) and the two reference scripts with
  their `SCHEMA_HEAD`.
- **The successor.** `VOI_STOPPING_ALGORITHM_VERSION = "mvp-0.21"`, appended
  to `SUCCESSOR_CHAIN` after `ROUTE_RULES_ALGORITHM_VERSION`; `LATEST` is
  mvp-0.21 and new vaults start there. `upgrade_to_mvp021` accepts mvp-0.20,
  or mvp-0.9 to mvp-0.19 through `route_rules_upgrade.upgrade_to_mvp020`,
  passes the chained notes through (`chained_notes = list(chained.notes or [])`)
  and passes an earlier step's refusal unprefixed (`_STEP_REFUSAL`), as the
  route rules' upgrade does. T1's guard stays advisory; the refusal test sets
  `config="[recurrence]\nrequire_guard = true"` and the vault stays at
  mvp-0.10. `learnloop upgrade` defaults to mvp-0.21; `--to mvp-0.21` is new
  and `--to mvp-0.10` to `--to mvp-0.20` still reach those tags.
- **Every mention.** The branch's code, comments, receipts' docs, the
  reference generator's section and table descriptions, the frontend's two
  comments and its tests now say mvp-0.21 (a line-by-line pass over every
  line the branch added). Main's own mvp-0.17 (the route check) is untouched.
  Tests that pinned the predecessor as mvp-0.16 (the kill-switch equivalence
  and "below the successor" cases) now use mvp-0.20, the immediate
  predecessor, and the lists of earlier versions include mvp-0.17 to
  mvp-0.20. Main's tests that pinned mvp-0.20 as the latest
  (`test_mvp011/013/014/015/016/017/018/020_upgrade.py`,
  `test_recurrence_commands.py`, `test_route_rules_in_grader.py`,
  `test_reading_step_switch.py`) now pin mvp-0.21.
- **Defaults.** All thirteen `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries (mvp-0.9
  to mvp-0.21) were recomputed with `defaults_fingerprint_for_version` from
  the composed defaults; the template `.pyc` was cleared before and after and
  the file touched. Each moves only because the effective config gains
  `[voi_stopping]` and the two `diagnosis.probe_lane_*` keys (dormant below
  mvp-0.21). The CLI help snapshot was rewritten (`misconceptions`,
  `upgrade`). `Version Registry.md` and `Algorithm Versions and
  Reproducibility.md` read mvp-0.21 and head 201.

### Composition

- **Rank 4, the measured unresolved cost** (`evsi-multisim.md` §6.1, Part C on
  main). `VoiContext.loss_table` passes
  `unresolved_minutes=unresolved_minutes_for_hypotheses(repository, labels,
  pseudo_count=config.evsi.unresolved_cost_prior_pseudo_count)[0]` to
  `action_loss.build_loss_table` when `evsi.measured_loss_enabled` (default
  **off**, unchanged), and keys its cache on the regime and the charged
  minutes. Every decision at stake names its regime: `context.loss_regime`
  and the `loss_model` parameter are `triage_route_wasted_minutes` or
  `route_plus_measured_unresolved_minutes_v1` (the causal shadow selector's
  name for the same regime), and with the measured regime the receipt adds the
  estimate (`context.unresolved_cost`, parameter `unresolved_minutes` with its
  provenance). Off, the table is built exactly as before (same hash, the
  unresolved cost never read) and the restore golden reproduces; on, every
  off-diagonal cell charges the estimate and EVSI rises
  (`tests/test_voi_merge_composition.py`). One thing for the owner before
  turning it on: the value rule's hypotheses are probe labels, not
  `causal_hypotheses` rows, so `unresolved_minutes_for_hypotheses` reads each
  label's scope as `unknown`, which it treats as persistent: every label
  (`mastered` and `unfamiliar` included) is charged the estimate on its
  off-diagonal cells.
- **EVSI calibration's forecast log.** Every value decision the successor
  takes is now also a `voi_forecasts` row (behind `evsi.forecast_logging`),
  logged once, where it acts, at four new sites in `VOI_SITES`
  (`diagnosis.voi_forecasting.record_value_decision_forecast`):

  | Site | Logged when | Receipt key |
  |---|---|---|
  | `probe_episode_value_decision` | a continue, at the committed presentation (every commit door: the scheduler, the sidecar, the TUI, all through `record_presentation_forecast`) | `…:<presentation>` |
  | | a stop that ends the episode, at its completion | `…:<episode>:value_of_information_stop` |
  | | a stop that withholds the episode's probes from a Today offer (before the first answer the episode stays open, §9 Q5) | `…:<slate>:<episode>` |
  | `followup_value_decision` | each `followup_value_decisions` receipt with a valuation (a need with nothing to value is not one) | `…:<receipt id>` |
  | `teach_back_value_decision` | each teach-back an offer kept or dropped, per offer (router R1's grain) | `…:<slate>:<item>` |
  | `project_probe_value_decision` | each due project probe a plan-block decision (or the chooser's stop) admitted or held back, after the block commits, with R1's `plan_block` row as `decision_ref` | `…:<block>:<item>` |

  The body describes one check (`forecast_of`: `committed`, the administered
  observation; `subject`, the check a per-check receipt is about; or
  `nominal_best`, value's best where nothing was administered) with its
  predicted outcomes, likelihood rows, EIG, P(action change) and EVSI point
  and robust; the whole decision rides as `value_decision`, a lookahead's
  batches as `lookahead` (the described check's value is the batch's, method
  `robust_evsi_lookahead_<k>`), and `selection` carries the serving path's
  `served_by` and router R1's `scheduler_exploration` marker verbatim (the
  committed probe's, and a teach-back's the draw moved forward), as main's
  `probe_selection` forecast does. Parameters keep `voi_forecasts`' coarse
  provenance vocabulary: the study's `evsi_multisim` values read `heuristic`
  with `fine_provenance` kept. A check the plan already holds, a learner
  request and a check a refresh cannot take are not value decisions and log
  nothing.

  **No double record.** Each decision has one key, so a rebuild of the
  same offer, a second pass over a presentation or a replay adds nothing;
  the successor's own receipts (the presentation's components, the
  completion detail, `followup_value_decisions`, R1's offer and plan-block
  details) stay where they were and are the same bodies. Main's own sites
  stay their own decisions: `probe_selection` (which instrument), beside
  `probe_episode_value_decision` (whether to ask again) on the same
  presentation; `followup_selection` (the queued item's target facet), beside
  `followup_value_decision`. One composition fix: rank 1 evaluates the
  robust gate only as a counterfactual while value decides, and main's gate
  logs a `probe_robust_selection` forecast whenever it is evaluated. The
  counterfactual evaluations (`robust_gate_counterfactual` and the value
  stop's) now pass `record_forecast=False`, so `voi_forecasts` never holds a
  gate decision that was not taken; where the gate decides (rank 1's switch
  on, the site off, below the successor, a calibration session) it logs as on
  main. (The branch's refactor also left main's logging call reading an
  undefined `posterior`; it reads the gate's own belief now.) The live
  calibration report counts and joins the new sites; it has no realized-
  emission mapping for them yet (`site_without_outcome_mapping`), so nothing
  is scored twice.
- **The restore golden.** It reproduces exactly with the switches at their
  restore values, unchanged, with `evsi.forecast_logging = false` in its
  integration scenarios (`voi_restore_scenarios.PINNED_ID_STREAM_TOML`). The
  pinned channel's credible sets are seeded by ids, and each `voi_forecasts`
  receipt draws an id from the test's seeded stream, so with logging on the
  episodes', calibration schema's and models' ids shift and the ensembles are
  other (equally valid) draws: in the gate scenario the robust EIG of the
  first decision moved by about 1% (0.2609 to 0.2637 nats) and the ranking
  among equally valued checks changed. With logging off every decision,
  reason, method and value matches to 9 decimals; the 150 pure scenarios
  match with logging on (they draw no id). Not re-pinned: the golden still
  pins the branch's own pre-study decisions.
- **The daily plan.** The admission against the minutes left composes with
  UX Phase 1 without a change: the reading step changes which section a
  reading block offers (`plan.reading_from_furthest`), not the plan's minutes
  or lanes, and Today's begin calls the same `start_session` /
  `next_plan_item` / `plan_learner_pick` RPCs whose builds value the probes.
  R1's plan-block logging carries the probes' receipts as before
  (`voi_decisions`) and its row id is now each probe forecast's
  `decision_ref`. The sources' proposal pick (`plan_learner_pick` with
  `proposal_id`) goes through `learner_pick`, a one-item learner-pick block
  whose `decision_ref` the S5 intervention reads; the branch changes only the
  refresh's probe valuation inside it (`_live_context`, against the minutes
  left), not the pick's block or its decision, and
  `test_learner_pick_proposal.py` passes.
- **Held grades.** The successor reads no grade of its own: episode evidence
  comes through main's effective view (`probe_observations_for_episode`,
  `qualifying_probe_observation_count_for_session`, `episode_posterior`, all
  on `learnloop.held_grades`), and a held grade writes no error event, so the
  probe lane and the overlay never see one. The one direct read, the cap
  report's per-session qualifying count (`scripts/voi_cap_report.py`), now
  leaves held attempts out through `held_grades.held_for_review_attempts`.
  The minutes estimate reads attempt latencies, which are time, not an
  outcome; main's own latency readers (`median_attempt_latency_seconds`,
  `unresolved_cost`) read them the same way.
- **Import contracts.** No new edge: the scheduler and the plan reach the
  forecast log through `diagnosis.voi_stopping`
  (`record_offer_value_forecasts`, `record_plan_value_forecasts`), which
  imports `diagnosis.voi_forecasting` lazily.

### Tests (phase 1, before main moved)

Targeted selection of 79 files (`-n 8`, `TMPDIR` = the worktree's
`fixtures-local/tmp`, under another worktree's full suite): the branch's
`test_voi_stopping.py`, `test_voi_v2.py`, `test_mvp021_upgrade.py`; the new
`test_voi_merge_composition.py` (11: rank 4 off and on, each forecast site,
the gate counterfactual, logging off); the upgrade chain
`test_mvp09/010/011/013/014/015/016/017/018/020_upgrade.py`,
`test_mvp017_route_check_replay.py`, `test_recurrence_commands.py`,
`test_route_rules_in_grader.py`, `test_reading_step_switch.py`; the daily plan
(`test_daily_plan_*.py`, `test_learner_pick_proposal.py`), Today
(`test_today_headline.py`, `test_today_surfaces.py`, `test_tui_today.py`);
EVSI calibration (`test_evsi*.py`, `test_voi_forecasts.py`,
`test_action_loss.py`, `test_staged_policy_evsi.py`); router R1
(`test_router_*.py`, `test_diagnosis_async_router.py`); follow-ups, probes,
teach-backs, held grades, sources composition, migrations, table roles,
rebuild, replay, the architecture ratchet, the CLI help snapshot, config and
template, the registry audit, the tracked-fixture and copy guards.

| Run | Result |
|---|---|
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| targeted selection | **1,074 passed, 1 failed** (8 min 14 s). The failure was the architecture ratchet: the rank-4 wiring added a function-local edge `diagnosis.voi_stopping -> scheduling.unresolved_cost`; it is now a module-level import beside `action_loss` and `evsi` (no new contract edge) |
| after the fix: `test_architecture.py`, `test_voi_merge_composition.py` | 25 passed |
| after the fix: `test_voi_stopping.py`, `test_voi_v2.py`, `test_mvp021_upgrade.py` | 123 passed |
| `db_generate_reference.py`, `db_validate_reference.py` | head 201, 319 table notes, 804 leaves in 48 sections, **0 errors** |
| `validate_vault.py` | passed |

Main moved to `1def803a1` (the EVSI multi-family study, merged after
`9fd00e9fe`) while this phase ran; the full gate, the durability lane and
parity follow once that main is merged in.

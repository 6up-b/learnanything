# EVSI calibration: Codex review fixes

Stage `evsi-calibration`, branch `evsi/calibration`. Codex review job
`20261013-010220-TFyMeJ` (read-only; it ran no gate). Every finding was
reproduced first (a failing test, or for F2 the exact numbers Codex quoted),
then fixed. None was rejected. No paid call, no vault database read, no
tracked working vault touched; the study rerun used the Eedi files only
(2024 bank copied into the worktree's gitignored `fixtures-local/eedi-2024`,
the saved Eedi 2020 fit reused).

## Findings

| ID | Severity | Title | Verdict | Commit | Test (fails before the fix) or reason |
|---|---|---|---|---|---|
| F1 | High | Repair outcomes treated as diagnostic truth | fixed | `6cd87a23` | `tests/test_voi_forecasts.py::test_repair_outcomes_are_not_diagnostic_truth` (another episode's repair class confirmed `h2`), `::test_factor_resolution_by_repair_is_repair_effect_and_by_observation_is_truth` (`repair_confirmed` confirmed by route), `::test_cold_verification_with_independent_diagnostic_support_is_truth`; the test that asserted route-only confirmation is replaced |
| F2 | High | Strong-instrument experiments start from weak-world histories | fixed, study rerun | `96588eb7`, rerun `e1f5b98f` | `tests/test_evsi_calibration_sim.py::test_each_response_world_simulates_histories_generated_in_that_world`; Codex's numbers reproduced exactly on the real bank and fit: holders' mean starting probability on their true misconception at consistency 0.9 is **0.1250** with reused histories, **0.1939** with histories drawn in that world (0.126 vs 0.152 at 0.7) |
| F3 | Medium | Staged forecasts neither identify nor describe the administered candidate | fixed | `15c7d8d0` | `tests/test_voi_forecasts.py::test_staged_forecast_is_the_committed_selection_with_its_decision` (no receipt carried the decision id; the receipt described the ranking's best, not the tie-break's choice) |
| F4 | Medium | The forecast kill switch does not cover staged decisions | fixed | `15c7d8d0` | `tests/test_voi_forecasts.py::test_staged_forecast_obeys_the_kill_switch` (a receipt was written with `forecast_logging = false`, `algorithm_version` null) |
| F5 | Medium | Follow-up calibration scores a facet forecast against the whole-item grade | fixed | `8012c46b` | `tests/test_voi_forecasts.py::test_followup_outcome_is_the_target_facets_not_the_whole_items` (recall fully right, method wrong: realized `mid\|` before, `high\|` after) |
| F6 | Medium | Untaken follow-ups acquire outcomes from unrelated later attempts | fixed | `8ed9a913` | `tests/test_voi_forecasts.py::test_followup_outcome_joins_only_the_attempt_that_took_the_followup` (a superseded decision and the newer one both consumed one answer; an unbound ordinary attempt counted as taken) |
| F7 | Medium | Missing timings become measured zero-cost recurrence | fixed | `075a3883` | `tests/test_voi_forecasts.py::test_untimed_recurrence_is_not_a_measured_zero` (an untimed recurring class was a measured 0 and pulled 2.72 minutes to 1.81) |
| F8 | Medium | The "today's caps" baseline omits today's robust completion gate | fixed, study rerun | `96588eb7`, rerun `e1f5b98f` | `tests/test_evsi_calibration_sim.py::test_the_incumbent_arm_includes_todays_robust_completion_gate` (unstable posterior, robust abstention after the minimum: serving stops, the old arm kept checking) |

## What changed

**F1 (truth).** `live_report.truth_for` counts diagnostic truth only with
explicit linkage (the evidence names the forecast's own hypothesis ids; they
belong to one episode, and a shared repair class is not linkage) and
independent diagnostic evidence: a cold verification's
`diagnosis_support_update` with a non-zero delta on an admitted basis
(`causal_attribution.SUPPORT_BASIS_AUTHORITY`) citing its observation, an
admitted `matched_single` discriminating observation that is not the
forecast's own realized answer, or teach-back recurrence (unchanged). Repair
success and failure, and factors closed as `repair_confirmed` /
`escalated_unrepaired`, are reported per site as `repair_effect`, never as
truth.

**F2 (histories).** `experiments.run_experiments` draws each response world's
learners in that world (`draw_learners(with_truth(...))`) with the same
per-learner seeds, so truth, subject, question order and the uniforms behind
every answer are common across worlds, and each world's learners are shared by
all its policies. Regimes, the sensitivity sweep and Part C all use them. The
report adds `flagged_learners_by_world` and `starting_belief` (mean probability
on the truth per truth class and world).

**F3, F4 (staged).** The forecast is written in `staged_policy.decide` after
the decision is persisted: receipt key and `decision_ref` = the decision id;
`chosen_ref` = the candidate actually committed after the near-tie
randomization (`forecast_of: committed`), with `extra.assignment` (assignment
id, propensity, seed, draw) and `chosen_practice_item_id` when the candidate is
a practice item; the ranking's best kept apart (`nominal_best_ref`, and the
`nominal` forecast block when it differs). Stops and abstentions record
`forecast_of: nominal_best`. The vault is threaded through, the kill switch
(`voi_forecasts.forecast_enabled`) is read before anything is built, and
`algorithm_version` is filled. The report's staged outcome adapter returns
`not_administered`, `shadow_not_administered` (shadow mode composes no work) or
`no_attempt_binding`: no production caller passes a `DiagnosticSelector` today
and the staged controller writes no decision-to-attempt receipt, so a live
staged forecast stays right-censored rather than guessed from the next attempt
on the item (the F6 error). The staged emission adapter reads the graded probe
outcome once an attempt is bound (R1's router adapter runs first).

**F5 (follow-up facet).** The follow-up forecast freezes
`target_facet_contract`: the criteria mapped to the target facet with their
points and facet share (`criterion_facet_weights_for_item`, as
`derive_facet_outcomes` reads it), the fatal errors, and the item and rubric
content hashes of the assessment contract. The report scores the attempt's
surviving grading evidence on those criteria with `derive_facet_outcomes`'s
weighting (unassessed criteria contribute nothing), buckets it with the facet
updater's cut points (`facet_diagnostics.facet_outcome_bucket`, now public),
and keeps a fatal error only if the frozen rubric lists it. An answer graded
under another contract (`graded_under_another_contract`), with no contract
(`graded_contract_unknown`), with the target facet unassessed
(`facet_unassessed`) or unmapped (`facet_unmapped`), or a forecast without a
frozen contract (`no_frozen_facet_contract`) stays unmapped. Today's rubric is
never read.

**F6 (follow-up join).** Taken = the first attempt on the item after the queue
is bound to this decision by the scheduler's own rule
(`Repository.followup_source_attempt`) and was answered through the follow-up
lane (`practice_attempts.scheduler_candidate_id` → a slate candidate with the
`intervention_followup` component). Otherwise `superseded` (a newer decision
queued the item first), `not_taken` (answered through another lane, which ends
the queued follow-up), `unbound_attempt` (no offer binding) or `pending`.
Follow-up tasks of this lane have no `consumed_attempt_id` (that column
belongs to the delayed `followup_tasks` lanes), so the offer binding is the
explicit decision-to-attempt receipt used.

**F7 (missing time).** A recurring class with untimed repeats and no pooled
personal latency is `unmeasurable`: out of the mean and the sample count,
counted in `detail.unmeasurable_classes`. With pooled latency available the
untimed repeats are imputed from it and labelled (`imputed_classes`,
`imputation: pooled_personal_median_latency`).

**F8 (incumbent).** `policies.incumbent` follows
`probe_episodes._evaluate_completion` in its order: the observation budget; on
an unstable posterior action equivalence, then from the minimum independent
observations the robust completion gate (`robust_composition.evaluate_selection`
abstains → `couldnt_reliably_distinguish`); on a stable one `decision_stable`
after the minimum, else action equivalence. The old arm is kept as
`caps_only`, labelled a simplified cap-only comparator (a legacy unpinned
episode); `random` and `max_entropy` use its rules.

## The rerun (F2, F8)

`learnloop evsi simulate --eedi-2024 fixtures-local/eedi-2024 --fit
fixtures-local/evsi-calibration-v2/response_fit.json --output
fixtures-local/evsi-calibration-v2 --workers 12` (the saved Eedi 2020 fit
reused; 711 s; no network, no paid call). The study review
[`evsi-calibration.md`](evsi-calibration.md) §Summary, §4 and §5 now carry
these numbers; what moved:

| Claim | Before (reused histories, `caps` without the gate) | After the rerun |
|---|---|---|
| Fitted world, repair 3: today's policy vs value rules | caps 5.18 (3.4 checks) vs 1.81 min | **incumbent 3.77 (2.0 checks)** vs 1.81; the gate ends 296/400 episodes as `couldnt_reliably_distinguish` |
| Hand-set forecasts, today's checks | 0.38 min / 0.32 nats predicted, −0.02 min / −0.04 nats realized | 0.38 min / 0.33 nats predicted, **−0.02 min / −0.06 nats** realized |
| 0.9 / 30 min: EVSI as built vs today | 18.8 vs caps 11.9 | **17.9 vs incumbent 13.3** (caps-only 9.6); lcb-only 12.5, lookahead 10.8 |
| 0.9 / 10 min best rule | lookahead 5.63 vs caps 5.92 | lookahead **4.99** vs incumbent 5.82, caps-only 5.13 |
| Robust completion gate | not simulated | **costs 3.7 min per episode at 0.9/30** (13.3 vs 9.6, CIs 11.7–15.0 vs 8.1–11.3) |
| Minutes per nat at 0.9 | 0.43 × repair | 0.41 × (incumbent's checks) – 0.51 × (caps-only's) |
| Knowing the true repair minutes | 0.70 [0.22, 1.15] | 0.71 [0.29, 1.10] (lcb-only) to 1.06 [0.58, 1.47] (lookahead) |
| `ROBUST_QUANTILE` 0.25 | Δ −0.16 [−0.33, −0.00], "25th within ±0.09" | Δ −0.10 [−0.30, 0.12] / −0.15 [−0.38, 0.08]; realized value between the 25th and 50th percentiles; confidence lowered to low–medium |
| Part C at 0.9 | clear only at U = 7.25 (−1.11), +0.12 at U = 0.91 | clear from U = 3.63 (−0.54 [−0.89, −0.26]); no distinguishable cost below |

Recommendations unchanged in direction; three gained evidence (stop the
agreement gate, including today's robust completion gate, from ending
diagnosis alone; turn on Part C; replace the flip abstention), one lost
confidence (`ROBUST_QUANTILE` 0.25), and one claim in the study review was
corrected outright: `ROBUST_QUANTILE` feeds today's robust completion gate, so
changing it is a serving change.

## Claims withdrawn or corrected

* "Truth adapters count only independent evidence": now true as stated above
  (F1); repair effect is reported separately.
* "Every instrumented decision can be scored against its realized answer":
  corrected. Probe, robust-gate, follow-up and causal-shadow forecasts join
  through explicit bindings; staged forecasts are logged with full identity
  but stay right-censored (`shadow_not_administered` / `no_attempt_binding`)
  until the staged controller writes an administration receipt.
* "`forecast_logging = false` disables the forecast ledger": now true for
  every site (F4).
* "The `caps` arm implements today's probe-episode rules": withdrawn; the
  `incumbent` arm does, and the review file's comparisons now use it (F8).
* "Personal unresolved cost is measured": now only from timed or labelled
  imputed repeats (F7).

## Gate

Source and tests as of `e1f5b98f` (the commit that adds this file changes no
code). `TMPDIR` = the worktree's `fixtures-local/tmp`. No migration, config,
CLI-surface or frontend change, so the DB/config reference scripts and the
frontend steps do not apply.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 14 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto -q -p no:cacheprovider` | **8,645 passed**, 0 failed, 0 skipped (257 s; 8,635 before the fixes + 10 new tests) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability -q -p no:cacheprovider` | **94 passed**, 8,551 deselected (85 s) |
| Review tests | `tests/test_voi_forecasts.py` 25 passed (8 new, 2 rewritten), `tests/test_evsi_calibration_sim.py` 10 passed (2 new) |
| `learnloop evsi simulate` (full study rerun) | ok, 711 s on 12 workers, report in `fixtures-local/evsi-calibration-v2/` |
| Paid calls | none ($0.00) |

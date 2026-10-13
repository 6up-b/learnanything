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

## Re-review

Codex re-review job `20261013-020340-mSpHWK` (read-only over
`2a75656e..evsi/calibration`; it ran no gate): F2, F4, F7 and F8 confirmed
fixed; F1, F3, F5 and F6 reopened; two new findings, F9 and F10. Each
reopened or new finding was reproduced with a failing test first, then fixed,
except F3, which is rejected below with its reason. No paid call, no vault
database read, no tracked working vault touched.

### Findings

| ID | Severity | Title | Verdict | Commit | Test (fails before the fix) or reason |
|---|---|---|---|---|---|
| F1 | High | Cited diagnosis support trusted without resolving the cited evidence | fixed | `9bd071e6` | `tests/test_voi_forecasts.py::test_cold_verification_support_counts_only_its_resolved_admitted_observation` (a verification naming `h1`, `h2` with a positive delta citing a missing observation confirmed **both** `h1` and `h2`; so did one citing an observation of an unrelated hypothesis); `::test_cold_verification_with_independent_diagnostic_support_is_truth` rewritten on real observation receipts (it cited ids that did not exist) |
| F3 | Medium | Live staged decisions have no administration-to-attempt linkage | rejected (deferred, conflicts with the staged policy's spec step) | — | No production code builds a `DiagnosticSelector` (`plan_short_session` has no caller), so no staged diagnostic forecast is written in production; the one live staged path (`controller_cutover.staged_next_action`) passes no selector and uses the decision only to veto or confirm a P2 run transition, administering no candidate as an attempt. `staged_policy` "composes no live Today work. Making it live for P2 runs is the §14.2 cutover (a later step)": there is no administration event to bind, and the receipt belongs to that cutover, outside this stage. Guessing the next attempt on the chosen item is the error F6 removed. Live staged forecasts stay right-censored as `no_attempt_binding` (labelled; study §14 open question) |
| F5 | Medium | Historical-contract validation misses facet-map changes | fixed (through F9) | `0c8c8500` | see F9 |
| F6 | Medium | Queue identity inferred chronologically: an answer to A's offer credited to B | fixed | `48130a0d` | `::test_followup_offer_belongs_to_the_decision_that_produced_it` (A queues, the slate offers, B re-queues, the learner answers A's offer: B was `taken` and A `superseded`; an answer that consumed a cold-retry task, same component, was also `taken`); `::test_followup_outcome_joins_only_the_attempt_that_took_the_followup` now builds its slate after the newer queue (its single slate predated that queue, so it had Codex's scenario built in and asserted the wrong side) |
| F9 | Medium | Facet-map edits bypass the frozen-contract check | fixed | `0c8c8500` | `::test_followup_outcome_needs_the_frozen_facet_map` (map swapped after the forecast, prompt and rubric unchanged, `recall_criterion` 2/2 and `method_criterion` 0/2: realized `high\|` before, `graded_under_another_contract` after; also an attempt that recorded other evidence facets) |
| F10 | Low | One repair outcome counted twice | fixed | `9bd071e6` | `::test_one_cold_verification_is_one_repair_outcome` (one verification plus the factor closure it caused gave two `repair_effect` entries, `{"success": 2}`) |

F2, F4, F7 and F8: confirmed fixed by Codex; untouched.

### What changed

**F1 (cited support).** `live_report._cited_support` resolves the
verification's `diagnosis_support_update.observation_id` in
`causal_discriminating_observations`. It counts only when the receipt exists,
is admitted, is a `matched_single` naming one hypothesis, is independent
(`admissible_as_independent` is not 0, and it is not the forecast's own
realized answer), carries the support authority its basis grants
(`SUPPORT_BASIS_AUTHORITY`, the one grant table: a `blind_probe_match` must
cite a `validator_owned` receipt), and matches one of the forecast's
hypotheses. Positive support then confirms the matched hypothesis only, and
only when the verification names it; negative support rules out the
verification's hypotheses only when the observation matched another
hypothesis of the forecast. The discriminating-observation adapter uses the
same independence check (`_independent_match`). The bases with no receipt
table of their own (`learner_confirmation`, `adjudication`,
`fingerprint_distinct_recurrence`) cannot be resolved and so prove nothing
here; no production caller supplies diagnosis support today
(`causal_orchestrator.record_cold_verification_from_task` passes none).

**F10 (repair outcomes).** A factor resolution keeps the
`cold_verification_id` it cites; when that verification is already listed it
is annotated (`factor_resolution`) instead of appended, and
`summarize_joined` counts one outcome per cold verification.

**F6 (offer identity).** The first attempt on the item after the decision's
queue decides its fate (any attempt ends every earlier queue). It took this
decision only when its offer is a slate candidate inserted as an intervention
follow-up, the attempt consumed no delayed task (cold retry and certification
probe ride the same component and shadow a queued follow-up of the item), and
the queue the scheduler was serving for the item when that slate was built is
this decision's (`_queue_serving_at`: `pending_followup_practice_items` as of
the slate's `created_at`, newest queue first, ended by any attempt since).
Otherwise `superseded` (a newer decision produced the offer or re-queued
first), `answered_earlier_offer` (an older one produced it), `not_taken`,
`unbound_attempt`, `no_queue_receipt` (the decision's own queue is not on
record) or `pending`. `Repository.followup_source_attempt` is no longer used:
it names the queue active when the answer arrived, not the one that produced
the offer.

**F9 (facet map).** The frozen contract (`followup_target_facet_v2`) reads
the criterion -> facet map from the assessment contract's own criterion
targets, role-weighted as `target_criterion_facet_weights` reads them, and
freezes the hash of the contract's `criteria` (targets included) and the
item's evidence facets beside the item and rubric hashes. An answer whose
stored contract has other criteria or targets, or whose attempt recorded
other evidence facets, is `graded_under_another_contract`; a contract frozen
without the hash is `frozen_contract_without_facet_map`. Why the targets and
not the item's numeric `criterion_facet_weights`: the graded attempt's stored
contract records targets, but no grading record keeps numeric facet weights
(`field.outcomes._revision` reached the same limit), so only the targets can
be checked against the contract an answer was graded under. The consequence,
labelled in the contract (`facet_map: assessment_contract_targets`): on an
item whose criteria split across facets by authored numeric weights, the
realized target-facet outcome uses role weights (primary 1.0, supporting 0.3)
where the facet updater uses the numeric map. Forecast body
`voi_forecast_v3`, report `voi_calibration_report_v3`.

**References.** The fixes moved source lines the config notes cite, and
`db_validate_reference.py` already failed on 14 stale citations (some from the
first review round's `policies.py` edits). Regenerated (`c14b0e6a`):
`errors: []`, 300 table notes, 681 config leaves. No schema or config change.

### Claims withdrawn or corrected

* "The follow-up adapter binds an answer through the scheduler's own rule":
  corrected. That rule names the queue active when the answer arrived; the
  adapter now credits the queue that produced the answered offer (F6).
* "Truth counts a cold verification's diagnosis support on an admitted basis
  citing its observation": corrected. The citation is now resolved and checked
  (F1).
* "The frozen follow-up contract can never be reinterpreted by a later edit":
  now true for the facet map too, read from the contract's targets (F9).

### Gate (re-review)

Source and tests as of `c14b0e6a` (the commit that adds this section changes
no code). `TMPDIR` = the worktree's `fixtures-local/tmp`. No migration,
config, CLI-surface, sidecar-RPC or frontend change, so the frontend steps and
the mobile allowlist do not apply; the DB/config references were regenerated
because their source citations had gone stale.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 14 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto -q -p no:cacheprovider` | **8,649 passed**, 0 failed, 0 skipped (280 s; 8,645 after the first round + 4 new tests) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability -q -p no:cacheprovider` | **94 passed**, 8,555 deselected (128 s) |
| Re-review tests | `tests/test_voi_forecasts.py` 29 passed (4 new, 3 rewritten), `tests/test_evsi_calibration_sim.py` 10 passed |
| Each fix commit on its own | `9bd071e6` and `48130a0d` checked from an exported index: `tests/test_voi_forecasts.py` + `tests/test_architecture.py` 41 and 42 passed |
| `db_generate_reference.py` then `db_validate_reference.py` | `errors: []`, 300 table notes, 681 config leaves (before: 14 stale source citations) |
| Paid calls | none ($0.00) |

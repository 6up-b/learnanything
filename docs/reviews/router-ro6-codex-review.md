# Router objective RO6: Codex review fixes (`router/ro6-learned-tail`)

Review job `20261105-125456-EfabRp` (gpt-6.1-sol), on the stage record `docs/reviews/router-ro6.md` at `7f0d6dab15`.
Every finding was reproduced first: each has a test in `tests/test_ro6_codex_review.py` that fails on the pre-fix
source and passes after the fix. To check that, the pre-fix tree (`git archive 7f0d6dab15 src migrations`, unpacked
in the stage's scratch directory outside the worktree) was put on pytest's `pythonpath` (`-o pythonpath=...`) and the
new file run against it: **15 of 15 failed** there, and all 15 pass on the fix. Fakes and synthetic data only; no paid
or real model call, no owner vault opened, no tracked working vault touched. RO6 still adds **no model request**.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Outcome-dependent censoring creates a false randomized calibration signal | fixed | `20a5e984d0` | `test_ro6_codex_review.py::test_f1_an_arm_difference_in_observation_alone_is_no_contrast` (balanced coin, identical returns in both arms, half the `present_next` returns unobserved: pre-fix `ŵ = 0.561`, slope 0.561 sd 0.040; now `ŵ < 0.15`, slope within 3 sd of 0, and the cohort whole), `::test_f1_an_arm_with_no_observed_return_leaves_the_contrast_unidentified` (pre-fix: 1916 contrasts fitted from the other arm and the policy zeros; now none, `status: unidentified`), `::test_f1_the_policy_arm_stays_a_zero_whatever_its_return` |
| F2 | High | Same-day exam crossings disappear from the fitted reward | fixed | `20a5e984d0` | `::test_f2_a_same_day_exam_after_the_decision_enters_its_reward` (decision 10:00, exam 18:00, next decision 19:00, `ω = 1`, `Y = 1`, no cost: pre-fix reward 0, now 1), `::test_f2_a_same_day_exam_with_no_import_censors_the_transition` (pre-fix: kept with reward 0; now `no_result`), `::test_f2_the_use_moment_is_the_goals_due_at_else_the_exact_delay` |
| F3 | Medium | The backup does not preserve the decision's cutoff | fixed | `20a5e984d0` | `::test_f3_the_next_state_is_valued_at_the_decisions_own_cutoff` (pre-fix next value 2.4 = `Σπq − (C′−C)·T/H`; now 2.125 = `Σπ(q − past_trim)`, and the next features' cutoff span `89/90`), `::test_f3_a_later_cutoff_with_no_value_at_the_earlier_one_is_censored` (pre-fix: fitted through the average terminal rate; now `cutoff_unmatched`), `::test_f3_a_shared_cutoff_needs_no_trim`, `::test_f3_the_rollouts_keep_the_value_past_the_trim_apart_without_moving_q` (`past_trim` at `C` equals `T_C` to 1e-12 for a review, a probe and stop; at `C + H` it is 0; `q`'s draws are identical with and without the trim) |
| F4 | Medium | Serving features read state newer than their declared decision time | fixed | `20a5e984d0` | `::test_f4_a_diagnosis_queued_after_the_decisions_moment_never_enters_its_features` (a diagnosis queued after the decision froze its moment and before the prefetch job ran: pre-fix the traced `pending_reports` was 1, its feature `log 2`; now 0), `::test_f4_no_snapshot_leaves_the_residual_out` |
| F5 | Medium | The new contrast-return reader includes imports received after its cutoff | fixed | `20a5e984d0` | `::test_f5_the_contrasts_return_reader_admits_an_import_only_once_known` (exam sat May 1, imported May 19, read on May 5: pre-fix `(0.5, None)`, now `(None, "no_result")`; after the import it is read) |
| F6 | Medium | Partial-history weights omit actions inside the evaluated window | fixed | `20a5e984d0` | `::test_f6_a_windows_product_includes_a_decision_whose_own_window_is_open` (October 1 window, October 10 decision with its window open on October 20, ratios 1 and 2, return 1: pre-fix 0, now 1), `::test_f6_a_window_with_a_decision_of_unknown_ratio_is_censored` (pre-fix: the factor silently dropped; now `incomplete_history`) |
| C1 | (claim) | "Every read passes the availability predicate" | fixed with F4, F5 | `20a5e984d0` | as F4 and F5 |
| C2 | (claim) | Reward test permits nonpositive rewards with no check; planted FQE test builds rewards from the equation fitted | partly addressed | `20a5e984d0` | The reward is now pinned exactly (F2's tests, `R = ω·Y`), and the backup's next value exactly (F3's). The planted-residual FQE test stays as it was: it is a recovery check of the estimator on data it is specified for, not evidence about the reward, and is labelled as such |

None rejected. Nothing re-argues the owner's decisions in §1 or §12; no new config key, weight, margin or threshold
(the one new constant, `tail_data._SAME_CUTOFF_SECONDS = 1.0`, is a numerical tolerance for two cutoffs the trace
keeps to six places, about 0.09 s, labelled as such). The old item difficulty scalar is neither read nor written.

## What changed

- **F1** (`learned_tail.coin_contrasts`, `CoinDraw`; `tail_data.contrasts`): the cohort is chosen only on what was
  fixed before the coin (a frozen residual, stop in the support, a predicted contrast, a closed window), and every
  draw stays. The `policy` arm's contrast is zero whatever its return (its weight is zero). A forced arm's observed
  return is weighted by the inverse of that arm's observed share in the cohort,
  `Ĉ_i = (1[offer]/p − 1[present_next]/p)·Ĝ_i·1[observed]/q_arm`; an unobserved one contributes zero. That is
  unbiased when observation depends on the arm alone (missing at random given the arm). A return missing because of
  its own value is not corrected, and the record says how many were missing by arm and reason (`assigned`,
  `observed`, `observed_share`, `unobserved`, `assumption`). A forced arm with draws and no observed return leaves the
  contrast **unidentified**: no contrast is returned, `ŵ` stays at its prior, and the record says why. `WEIGHT_VERSION`
  moves to `ro6_residual_weight_slope_rank_v2`.
- **F2** (`tail_data.use_moment`, `Logged.dated`, `transitions`): each frozen dated use carries its moment, the goal's
  `due_at` as the rollouts parse it (`clock.parse_utc`, the use's own or the goal's frozen in the trace), else the
  decision's moment plus the exact delay. A use counts in `(t_i, t_{i+1}]` by that moment; its calendar date stays
  the join key for the import, so a same-day exam with no import censors `no_result`.
- **F3** (`value._Ledger.past_trim`, `value.evaluate(trim_at=…)`; `tail_serve.previous_cutoff`, `trim_at`;
  `objective_chooser.run_numeric`; `tail_data._logged`, `transitions`; `learned_tail` feature `cutoff_span`): each
  decision at the tag finds the latest earlier logged decision and its cutoff `C_prev`. Its rollouts keep the net value
  past `C_prev + H` apart on the same draws (`terms.past_trim`: the undated uses of every piece past the trim at the
  piece's own midpoint, every tail session starting past it, any dated use past it, and a segment's minutes past it).
  `q` is unchanged, so `Q_tail(x′, a′; C_prev) = q − past_trim` is that cutoff's value exactly: the rollout ended at
  `C_prev + H` is the same path stopped earlier. The backup reads `Σ π·(q − past_trim)` with the next state's
  features at `C_prev`'s span `(C_prev − t′)/H` (a fourteenth feature, `cutoff_span = (C − t)/H`, the same function at
  serve time and over a trace). A shared cutoff (a goal date beyond the horizon) needs no trim. A next decision that
  did not value the earlier cutoff (an earlier version's trace, a goal dropped so that `C_prev + H` lies past its
  rollouts, `C_prev` already past) is censored `cutoff_unmatched`; the average-terminal-rate move-back is gone. One
  second-order caveat is recorded in the spec: the tail's topic ranking reads the remaining span to its own end, so
  with a dated use competing, the trimmed path can differ from a rollout ended at `C_prev + H` in which topic a
  session practises (undated uses rank the same). The trim costs nothing measurable: six topics, five candidates,
  16 draws, a 90-day horizon: 280.8 ms without and 278.5 ms with (median of 5). `FEATURES_VERSION` moves to
  `ro6_belief_features_v2` (so the generator key moves too) and `tail_data.VERSION` to `ro6_tail_data_v2`.
- **F4** (`tail_serve.snapshot`, `features`, `residual(frozen=…)`; `objective_chooser._tail_snapshot`,
  `_start_objective`, the inline path): the residual's mutable inputs (`decision_state`'s pending-report counts and
  every LO's mastery logit mean and variance, RO0 row 9's numbers) are read in the decision's own thread at its
  moment, before the prefetch job is started (or, with no model ready, before `run_numeric`). The job hands that
  snapshot to the features, which read nothing from the vault. With no snapshot for the decision's moment the
  residual is left out (`no_snapshot`), never computed from a later read. Below the tag or with `learned_tail` off
  nothing is read (the predecessor's path).
- **F5** (`scores.exam_result_known`, `window_uses(exam_result=…)`, `observed_return`, `observed_returns`): the RO6
  return reader passes its exact cutoff and config to one shared as-of reader (THE availability predicate,
  `attempt_time_sql`); `tail_data._exam_result_known` delegates to it. RO5's own `scores()` keeps its reader as at its
  base (RO5's landing owns that path).
- **F6** (`learned_tail.partial_history(sequence=…)`, `Ratio`, `WeightedRow.window_closes_at`;
  `tail_data.cross_check`): the windows evaluated are the closed ones with a ratio and an observed return; each
  window's product runs over the complete logged sequence in `[t_i, window close)`, its decisions' own windows open
  or not. A window holding a decision with no computable ratio is censored `incomplete_history`, never shortened.
  `CROSS_CHECK_VERSION` moves to `ro6_partial_history_v2`.

## A few simulated weeks, rerun (copy-shaped synthetic vault)

`tests/test_ro6_tail_data.py::test_a_few_weeks_on_a_copy_shaped_synthetic_vault` with `LEARNLOOP_RO6_DAYS=21` (as in
the stage record: RO5's copy-shaped vault, both policies answering through fakes, the default arms, one day a week
without a session, a seeded ~70% learner), on the fix:

| Measure | Value |
|---|---|
| Decisions, transitions | 110 traced block decisions, 109 transitions (1 censored `no_later_decision`; none `cutoff_unmatched`: every next decision valued the earlier cutoff); returns: 8 `no_later_session`; one generator version, features frozen at all 110 |
| The fit | n 109, 14 coefficients, noise σ² 4.04 (the checks' `c/r` terms dominate), condition 5.1e5 |
| `ŵ`'s path (each day's last decision) | 0.0 every day: no window closed through 10-25; then 6 (10-26), 12, 17, 22, 24, 32 (11-01) contrasts; as of the end 37 contrasts, 1 forced arm, slope −0.008 sd 0.577, rank undefined (`P(rank > 0)` one half), `ŵ = 0`. The first build's run had moved `ŵ` to 0.10 on noise at 7 contrasts |
| Residual's share of `Ṽ` per candidate | 0 at all 510 candidate valuations (`ŵ = 0`); argmax moved 0 times |
| Serving time per decision against mvp-0.48 | the residual's step adds median 45.5 ms, max 130 ms (n 110; features from the snapshot, the fit, the contrasts, `ŵ`). The snapshot read (three counts and the mastery table) and the rollouts' trim are outside that figure; the trim measured nothing (above) |
| Cross-check | one step: estimate −0.0075, se 0.0063, ESS 32.8 of 37, max weight 2.10; the fit's own projection 0.0039 over 110 |

## Not done, and the smallest way to finish

- **Observation probabilities beyond the arm** (F1): a return missing because of its own value (MNAR) is not
  corrected, only counted. Smallest finish: per-arm observation shares within strata fixed before the coin (the
  day's check draw, a goal date in the window) once the log has enough of each.
- **The trimmed path's topic ranking** (F3's caveat): exactness would need the tail's ranking to read the remaining
  span to `C_prev + H` on the trimmed path. Smallest finish: a second ranking span in `_priority`, used only for the
  part before the trim, if a dated use's competition ever shows in the report.
- Everything listed in the stage record's "Not built" is unchanged.

## The gate (this step)

This step did not run the full suite, the whole durability lane or vitest; those belong to the landing gate. No
frontend, `src-tauri`, migration, schema or DB/connection code changed, so no npm, vitest, cargo or durability step
applies.

| Step | What ran | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| Import contracts | `lint-imports --no-cache` (under `env -i`) | 43 kept, 0 broken |
| Baseline before the fix | the four `tests/test_ro6_*.py` | 34 passed |
| Reproductions on the pre-fix tree | `tests/test_ro6_codex_review.py` with `-o pythonpath=<7f0d6dab15's src>` | 15 failed (all) |
| New and RO6 files on the fix | `test_ro6_codex_review.py`, `test_ro6_learned_tail.py`, `test_ro6_tail_data.py`, `test_ro6_serving.py`, `test_ro6_successor.py`, `test_ro4_value.py`, `-n 6` | 72 passed |
| A few simulated weeks | `test_ro6_tail_data.py::test_a_few_weeks_on_a_copy_shaped_synthetic_vault`, `LEARNLOOP_RO6_DAYS=21`, `-s` | 1 passed (numbers above) |
| Targeted batch | 82 files, `-n 6` under `flock /tmp/learnloop-fullsuite.lock`: every test file naming the objective chooser, the mixture helpers or the router objective's `value`, `scores`, `tail_data`, `tail_serve`, `learned_tail` or `decision_state`; every `test_ro[0-9]*.py`; the display-label audit (`test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`), `test_architecture` (frozen cycles), `test_table_roles`, `test_registry_audit`, the process-launch allowlist (`test_ai_tool_isolation`, `test_e0_isolation`, `test_codex_tool_lockdown`), `test_module_catalog_inventory`, `test_cli_help_snapshot`, `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_sidecar_registry`, `test_mobile_allowlist`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_public_tip_guards`, `test_sqlite_file_copies`, `test_data_capture_successor` | 1458 passed, 4 skipped, 6 failed: 4 in `test_registry_audit.py` (the new numerical tolerance unregistered: registered), `test_ro1_availability_reads.py::test_the_decision_time_readers_ask_the_predicate` (the imported-result reader moved to `scores.exam_result_known`: the pin now names it), and `test_ro4_trace_report.py::test_the_why_surface_offers_the_trace_in_plain_words` (below RO6's tag, no RO6 path runs; passes alone on the fix and on the pre-fix tree, and its file passed 3 of 3 runs at `-n 6`: load-dependent timing, unrelated) |
| The failed files rerun | `test_registry_audit.py`, `test_ro1_availability_reads.py`, `test_ro4_trace_report.py`, `test_ro6_codex_review.py`, `-n 6` | 62 passed |
| After the references | `test_module_catalog_inventory.py`, `test_cli_help_snapshot.py`, `test_architecture.py`, `-n 6` | 28 passed |
| References | `module_generate.py` / `module_validate.py` (1236 module notes, 1383 test files: PASS), `db_generate_reference.py` / `db_validate_reference.py` (393 table notes; errors []), `validate_vault.py` (2223 notes: passed), under `env -i` | ok |

Every test ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`, one run at a
time. Every script outside pytest (lint-imports, the reference scripts, the trim timing) ran under `env -i` with
empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

Test files added or changed by this step, for the landing gate: `tests/test_ro6_codex_review.py` (new),
`tests/test_ro6_tail_data.py` (`cutoff_unmatched` in the reasons; no transition unmatched on a real run),
`tests/test_ro1_availability_reads.py` (the reader pin).

## Commits

- `20a5e984d0` RO6 Codex review fixes: F1-F6, the tests, the registry entry, spec §10.1 and the stage record's note.
- `f8722c8562` References regenerated.
- This file.

---

# Re-review (job `20261105-140523-n40uvz`, on `02a3ee8563`)

Verdict REOPENED: F1 and F3 reopened, F2, F4, F5, F6 confirmed fixed, one new finding F7 (Medium). Every reopened or new
finding was reproduced first. The new file `tests/test_ro6_codex_rereview.py` was run against the pre-fix tree
(`git archive 02a3ee8563 src migrations`, unpacked in the stage's scratch directory outside the worktree, put on
pytest's `pythonpath`): **9 of 10 failed** there. The tenth,
`test_f1_complete_returns_with_identical_arms_give_no_contrast`, is a control (complete returns, identical arms, no
contrast) and passes on both trees. All 10 pass on the fix. Fakes and synthetic data only; no paid or real model call;
no owner vault opened; no tracked working vault touched. RO6 still adds **no model request**.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High (reopened) | Pooled per-arm observation shares do not correct observation that depends on a pre-coin feature | fixed | `5d726bbc21` | `test_ro6_codex_rereview.py::test_f1_observation_on_a_pre_coin_feature_leaves_the_contrast_unidentified`: 8,000 balanced draws, identical returns `G = 1 + x` in both arms, offer stop losing low-`x` returns and present next losing high-`x` ones (pooled shares 0.683 and 0.673). Pre-fix: status `identified`, `ŵ = 0.493` (slope 0.493, sd 0.121). Now `unidentified`, `ŵ = 0`. Also `::test_f1_the_contrasts_read_every_window_complete`, `::test_f1_a_complete_return_leaves_an_unknown_dated_use_out_and_keeps_a_window_with_no_checkable_use`, and the control `::test_f1_complete_returns_with_identical_arms_give_no_contrast` |
| F2 | High | Same-day exam crossings | confirmed fixed | `20a5e984d0` | (Codex) |
| F3 | Medium (reopened) | `q − past_trim` is not the value at the carried cutoff (ranking, branch choice and quadrature use the longer horizon) | fixed | `5d726bbc21` | `::test_f3_a_carried_cutoff_runs_every_rollout_at_it`: `evaluate(cutoff=c)` with `c` off the day grid equals, draw for draw, the model whose inputs' own cutoff is `c` (an independent route: the probe's branch choice and the ranking read it too). `::test_f3_the_backup_reads_the_values_and_features_at_the_carried_cutoff` (pre-fix `cutoff_unmatched`). `::test_f3_a_trimmed_value_alone_is_no_value_at_the_carried_cutoff` (pre-fix: fitted through `q − past_trim`, next value 2.125). `::test_f3_the_chooser_values_the_candidates_again_at_the_carried_cutoff`. `test_ro6_codex_review.py::test_f3_no_carried_cutoff_leaves_the_rollouts_as_ro4s` |
| F4 | Medium | Serving features read newer state | confirmed fixed | `20a5e984d0` | (Codex) |
| F5 | Medium | Contrast-return reader admits later imports | confirmed fixed | `20a5e984d0` | (Codex) |
| F6 | Medium | Partial-history windows omit decisions | confirmed fixed | `20a5e984d0` | (Codex) |
| F7 | Medium | Legacy frozen 13-feature vectors break fitting after the upgrade | fixed | `5d726bbc21` | `::test_f7_an_earlier_builds_thirteen_features_are_rebuilt`: two legacy decisions sharing an absolute cutoff. Pre-fix: `IndexError: tuple index out of range`. Now one transition, 14-wide vectors rebuilt, a 14-coefficient fit. `::test_f7_the_served_features_version_is_part_of_the_generator` |

None rejected. Nothing re-argues the owner's decisions in §1 or §12. No new config key, weight, margin, threshold or
numerical constant. The cutoff-equality tolerance reused is `tail_data._SAME_CUTOFF_SECONDS`, already registered. The
old item difficulty scalar is neither read nor written. `value.py` is byte-identical to RO5's base (`5f02be6eb2`)
except for the optional `cutoff` argument; with it None (every caller below the tag, and with `learned_tail` off), the
rollouts are RO4's/RO5's (`test_f3_no_carried_cutoff_leaves_the_rollouts_as_ro4s`, `test_ro4_value.py`,
`test_ro6_serving.py::test_below_the_tag_and_switched_off_serve_mvp_048_exactly`).

## What changed

- **F1** (`scores.observed_return(complete=True)`, `observed_returns(complete=…)`, `window_uses(left_out=…)`;
  `learned_tail.coin_contrasts`; `tail_data.contrasts`): I took Codex's second option and did not model observation
  probabilities. Nothing in the log justifies an observation probability for a return that goes unobserved after the
  coin, so the stop coin's contrasts now read every window's return **complete**, and nothing is left to correct:
  - The bracket is unbiased for its own sum over the uses a check could observe (the checks' exact assignment
    probabilities `r`). A window with no such use is therefore its cost term alone, `−(C − C⁰)` (noted
    `no_randomized_use`).
  - A dated use whose result is not known at the cutoff is left out of the sum (noted `dated_left_out:n`). Whether it
    is known is `exam_result_known(lo, date, at)`: a function of the use and the cutoff, the same for every decision
    whose window holds that use, whichever arm its coin drew.

  `coin_contrasts` drops the share weighting. `Ĉ = (1[offer]/p − 1[present_next]/p)·Ĝ`, and the `policy` arm's
  contrast is zero. Any forced draw that still arrives with no return leaves the contrast `unidentified` (no contrast,
  `ŵ` at its prior), and the record says how many, by arm and reason, plus each arm's notes. RO5's `scores()` and the
  cross-check keep the default reader, unchanged. `WEIGHT_VERSION` moves to `ro6_residual_weight_slope_rank_v3`.
- **F3** (`value._Model(cutoff=…)`, `value.evaluate(cutoff=…)`; `tail_serve.previous_cutoff`, `carried_cutoff`,
  `with_carried_values`, `features(cutoff_days=…)`; `objective_chooser.run_numeric`; `tail_data._logged`,
  `transitions`; `tail_report`):
  - The trim (`past_trim`, `trim_at`) is removed entirely.
  - When the latest earlier decision's cutoff differs from this one's (`carried`), the candidates are valued a second
    time after the answer, on the answer's inputs and the first batch's draws, with every rollout run at `C_prev`:
    the tail's topic ranking (its remaining span to `C_prev + H`), a probe's repair choice in the belief's world (the
    belief model carries the cutoff), the quadrature's boundaries and the end. The results go in
    `residual.previous.q`, together with the candidates' features taken at `C_prev`'s span
    (`residual.previous.features`, the same function).
  - The backup reads `Σ π·previous.q` and `Σ π·previous.features`. A shared cutoff (`same_cutoff`) needs no second
    valuation.
  - Anything less is censored `cutoff_unmatched`: an earlier build's trace, a second valuation the deadline cut
    short, or a published answer served before it.
  - This decision's own `Q̄`, terms and choice are untouched.
  - Measured on the pre-fix tree's trim against the carried valuation, for two topics, a dated use at 3.5 days,
    `H = 6` and 16 draws: shift 0.37 d gives the same values to 9 places; shift 1.6 d gives 1.993417 against 1.993000
    (review); shift 2.9 d gives 1.792058 against 1.791225.
- **F7** (`tail_data.served_features_version`, `generator_payload(features=…)`, `_logged`; `tail_serve.residual`
  records `features_version`): frozen features are read only at this build's features version and width. A trace
  frozen by another version (an earlier RO6 build's thirteen, read from its fit's `features_version`; `unversioned`
  if none) is rebuilt with this build's function from its frozen belief numbers and RO0's receipt, like any earlier
  trace. Its carried values are not read. The features version a decision's residual served with is part of its
  generator key, so two loggers never share a fit. A decision with no applied residual never read features, so it
  keeps this build's version (`generator_now` is unchanged for it). `tail_data.VERSION` moves to
  `ro6_tail_data_v3`.

## A few simulated weeks, rerun (copy-shaped synthetic vault)

`tests/test_ro6_tail_data.py::test_a_few_weeks_on_a_copy_shaped_synthetic_vault`, `LEARNLOOP_RO6_DAYS=21`, `-s`, on
the fix. The same test on the pre-fix tree is beside it. The number of traced decisions varies from run to run on
both trees: the prefetch threads' timing decides which block boundaries the fake session hits. The stage record's
110 came from a third run.

| Measure | Fix | Pre-fix tree (`02a3ee8563`), same test |
|---|---|---|
| Decisions, transitions | 94, 93 (1 `no_later_decision`; none `cutoff_unmatched`). Previous cutoff `carried:valued` at 93 of 93 | 77, 76 |
| The fit | n 93, 14 coefficients, σ² 4.18, condition 2.8e5; features frozen at all 94 | n 76, σ² 4.65, condition 1.4e5 |
| `ŵ`'s path (each day's last decision) | 0 every day; contrasts 0 through 10-25, then 4, 5, 11, 18, 27, 37 (11-01). At the end: 37 contrasts, 8 forced, slope −2.56 sd 0.41, rank −0.83, `P(rank > 0)` 0.014, `ŵ = 0` | 0 every day; 31 contrasts at 11-01 |
| Residual's share of `Ṽ` per candidate | 0 at all 449 candidate valuations; argmax moved 0 times | 0 at 376 |
| Serving time per decision against mvp-0.48 | the residual's step: median 25.5 ms, max 98 ms (n 94). **The second valuation at the carried cutoff: median 472 ms, max 665 ms (n 93)**. It runs in the numeric prefetch job after the answer is complete, not on the serve path | residual step median 28 ms; no second valuation |
| Cross-check (one step) | estimate −0.0065, se 0.0036, ESS 29.7 of 40, max weight 3.31 | −0.0006, se 0.0038 |

In a first run of the fix (an earlier draft that valued the carried cutoff at the answer's refined draws), `ŵ` moved to
0.132 on 10-30 with 12 contrasts and back to 0.015 by 11-01. Noise on few contrasts, as in the stage's first build. No
gate is added, by the owner's decision.

**For the orchestrator (cost):** the second valuation adds no model request, but about as much CPU per traced decision
as the numeric policy's own first batch: one more evaluation at `rollout_theta_draws`. It runs inside the prefetch job,
after the answer is published, so the learner should not wait on it. A serve that takes the earlier published answer
leaves the next transition `cutoff_unmatched` rather than waiting.

## Not done, and the smallest way to finish

- **A goal added between two decisions:** the carried valuation runs the later decision's goals at the earlier
  cutoff, so a goal added in between is valued inside it. The earlier decision's objective had no such goal. Smallest
  finish: censor such a transition as a change of objective (compare the two traces' goal ids) if it ever shows in
  the report.
- **The checkable-use support** (F1): the bracket's estimand is the sum over the uses a check could observe. That
  support comes from RO5's check draws (the last draw stands on a day with no session), and a coin's arm can move
  later days' eligible sets. This is the same estimand RO5's scores use, and it is not changed here.
- Everything in the first review's and the stage record's "Not built" lists, except the trimmed-path ranking caveat,
  which this fix removes.

## The gate (this step)

This step did not run the full suite, the whole durability lane or vitest; those belong to the landing gate. No
frontend, `src-tauri`, migration, schema or DB/connection code changed, so no npm, vitest, cargo or durability step
applies.

| Step | What ran | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| Import contracts | `lint-imports --no-cache` (under `env -i`) | 43 kept, 0 broken |
| Reproductions on the pre-fix tree | `tests/test_ro6_codex_rereview.py` with `-o pythonpath=<02a3ee8563's src>` | 9 failed, 1 passed (the control) |
| RO6 set on the fix | `test_ro6_codex_rereview.py`, `test_ro6_codex_review.py`, `test_ro6_learned_tail.py`, `test_ro6_tail_data.py`, `test_ro6_serving.py`, `test_ro6_successor.py`, `test_ro4_value.py`, `test_ro1_availability_reads.py`, `-n 6` | 104 passed |
| A few simulated weeks | `test_ro6_tail_data.py::test_a_few_weeks_on_a_copy_shaped_synthetic_vault`, `LEARNLOOP_RO6_DAYS=21`, `-s` (fix, then the pre-fix tree for comparison) | 1 passed, 1 passed (numbers above) |
| Targeted batch | 84 files, `-n 6` under `flock /tmp/learnloop-fullsuite.lock`: every test file naming the objective chooser, the mixture helpers or the router objective's `value`, `scores`, `tail_data`, `tail_serve`, `tail_report` or `learned_tail`; every `test_ro[0-9]*.py`; the display-label audit (`test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`), `test_architecture` (frozen cycles), `test_table_roles`, `test_registry_audit`, the process-launch allowlist (`test_ai_tool_isolation`, `test_e0_isolation`, `test_codex_tool_lockdown`), `test_module_catalog_inventory`, `test_cli_help_snapshot`, `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_sidecar_registry`, `test_mobile_allowlist`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_public_tip_guards`, `test_sqlite_file_copies`, `test_data_capture_successor`, `test_config_refactor` | 1531 passed, 4 skipped, 1 failed: the new `test_f3_the_chooser_values_the_candidates_again_at_the_carried_cutoff`, whose 4-item run sometimes held only one block decision (no earlier decision to carry). Now 16 items |
| The fixed test rerun | `test_ro6_codex_rereview.py`, `test_ro6_codex_review.py`, `test_ro6_serving.py`, `-n 6`, three times | 29 passed ×3 |
| After the references | `test_module_catalog_inventory.py`, `test_cli_help_snapshot.py`, `test_architecture.py`, `test_ro6_codex_rereview.py`, `test_registry_audit.py`, `-n 6` | 56 passed |
| References | `module_generate.py` / `module_validate.py` (1236 module notes, 1384 test files: PASS), `db_generate_reference.py` / `db_validate_reference.py` (393 table notes; errors []), `validate_vault.py` (2223 notes: passed), under `env -i`; stamp-only churn left out | ok |

Every test ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`, one run at a
time. Every script outside pytest (lint-imports, the reference scripts, the two comparison scripts for F1 and F3, run
from the stage's scratch directory with `python -I`) ran under `env -i` with empty `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR`. One deviation from the patch rule: a single literal in the new test file was changed with
`sed` instead of the Edit tool (no Python text patch). An empty `python3` heredoc ran once outside `env -i`; it
executed nothing.

Test files added or changed by this step, for the landing gate: `tests/test_ro6_codex_rereview.py` (new) and
`tests/test_ro6_codex_review.py` (its helper's trace records `features_version`; the trim tests replaced by
`test_f3_no_carried_cutoff_leaves_the_rollouts_as_ro4s`; F1's censored cohort now expects `unidentified`).

## Commits (re-review)

- `5d726bbc21` RO6 Codex re-review fixes: F1, F3, F7, the tests, spec §10.1 and the stage record's note.
- `76b6bd7e66` References regenerated.
- This file.

# The single-family EVSI study without its count bound

Stage `evsi-single-family-unbounded`, branch `evsi/calibration` (base
`95d51782`). Owner-approved 2026-10-13: rerun the single-family EVSI
calibration study ([`evsi-calibration.md`](evsi-calibration.md)) without its
artificial 25-check bound, so its numbers can be relied on. The multi-family
review found `PolicySettings.safety_bound = 25` binding in some episodes there
(F4 in [`evsi-multisim-codex-review.md`](evsi-multisim-codex-review.md)), and
[`evsi-multisim.md`](evsi-multisim.md) §12 item 7 asked for this rerun.
The multi-family study already ran without a bound.

Offline only: no serving code, default or schema changed, no paid call, no
vault read.

Revised after the Codex review
([`evsi-single-family-unbounded-codex-review.md`](evsi-single-family-unbounded-codex-review.md)):
the comparison now covers every recorded value (F1), attributes differences to
a bound only when the unbounded run counted that same bound (F2), and checks
each headline claim as separate assertions, its conclusions and its stated
figures (F3). The comparison below was regenerated with it.

## Summary

* **The bound stopped 2 of 400 episodes, in one arm and one world.** Both
  were `eig_no_gate` episodes (the EIG rule at 60 minutes per nat with its
  agreement gate removed) at Eedi's fitted strength: learners 42 and 206,
  whose subjects have 30 and 53 questions. Without the bound they stop by
  their own value rule at 26 and 34 checks (+1 and +9 minutes). Neither
  episode's action changes: both truths are `other`, and the action is wrong
  either way. The same two episodes appear in four cells: the main
  comparison under the fitted system, and the fitted world at repairs of 3,
  10 and 30 minutes (the EIG rule never reads the repair minutes). The bound
  stopped no other episode in any arm, cell, sweep or Part C row. Without it,
  the largest episode anywhere else is 19 checks (`eig_no_gate`); the value
  rules reach at most 8 and the capped arms 4.
* **Everything else reproduces exactly.** The rerun used the same seeds and
  the stored fit. Every recorded value was compared, leaf by leaf: each arm's
  block in every cell (calibration bins, member quantiles, stop reasons,
  counts included), each cell's own values, and every report-level section
  (the fit, the bank, the misfit, the starting beliefs, Part C's measured
  rates, the recommendations); only the run's metadata (version, settings,
  timing, the bound counts) is left out. 299 of the 303 rows match the stored
  report number for number, CIs included, and every one of them is a row the
  bound never reached. Only the four `eig_no_gate` rows above moved. So every
  difference between the two reports is the bound's.
* **What moved, and by how much.** In the fitted world, `eig_no_gate` costs
  **8.46** minutes per episode instead of 8.44 at repair 3 (95% CI [7.89,
  9.07] instead of [7.88, 9.02]). It costs 12.41 instead of 12.39 at repair
  10, and 23.71 instead of 23.69 at 30. Its checks rise from 6.74 to 6.77 per
  episode and its value stops from 317 to 319. In the forecast table its log
  loss goes from 1.212 to 1.213, its predicted EIG from 0.069 to 0.068 and the
  upper end of its realized-gain CI from 0.085 to 0.084. Its other forecast
  and value numbers move in the fourth decimal: Brier 0.1620 → 0.1622,
  action-change ECE 0.0038 → 0.0041, the member quantiles' bias against
  realized value by at most 0.0004 (q10 −0.0038 → −0.0037 at repair 3,
  −0.0378 → −0.0374 at 30), minutes per nat 0.5164 → 0.5163 and 1.5492 →
  1.5490 at repairs 10 and 30, and the calibration bins by a few checks each.
  **No number moved outside its CI.**
* **No conclusion changes, and no rank.** Each of the 17 headline claims of
  the calibration review is checked as separate assertions: 31 conclusions
  (directions, rankings, CIs clear of or spanning 0, stated bounds such as
  "|Δ| ≤ 0.03" and "60 is at least 4×") and 42 figures it states, each at its
  stated precision. Every conclusion holds in both reports. Every stated
  figure holds in the stored report, and all but one in the rerun: `S3g`'s
  "8.44 min at Eedi/3" is now 8.46 (superseded in place in the calibration
  review). The quantities of 16 claims are identical to the last stored digit:
  * EVSI as built against today's serving where checks are strong (17.9 vs
    13.3 minutes per episode);
  * the flip abstention (12.5) and the 2–3 check lookahead (10.8);
  * the robust completion gate's 3.7 minutes;
  * `VALUE_PER_NAT_MINUTES`;
  * the measured-loss break-even (about 3.6 minutes);
  * the `ROBUST_QUANTILE`, `PERTURBATION_DELTA`, concentration, draw,
    burden, repair-minute and check-minute sensitivities.

  The 17th claim is the `eig_no_gate` arm itself, whose minutes moved within
  their CI (and its checks, which carry none): it is still the worst rule at
  Eedi's strength and the best at 0.7/30 and 0.9/30. All 11 cells rank the
  nine arms in the same order. Nothing in
  [`evsi-multisim.md`](evsi-multisim.md) §6 changes. Its ranks rest on the
  multi-family evidence, which ran unbounded, and the single-family values it
  quotes are among the identical numbers.
* The pseudo-count was never simulated in the single-family study (its §5
  says so). The multi-family study's pseudo-count streams cap themselves at 4
  checks and never read the bound, so this stage does not touch them.

## 1. What changed

All inside `src/learnloop/evsi_calibration/`, its CLI, tests and docs.

* `policies.PolicySettings.safety_bound` now defaults to `None`, the
  multi-family default since F4. A bound stays available as an explicit
  option: `PolicySettings(safety_bound=N)`, `ExperimentSettings(safety_bound=N)`
  or `learnloop evsi simulate --safety-bound N`. The multi-family code sets
  `None` explicitly everywhere it decides, so its behaviour is unchanged.
* `experiments.bound_counts` counts, per arm, in the `count_bound` style of
  the multi-family tables:
  * `count_bound_stops`: the run's own bound stops;
  * `reference_bound_stops`: the stops a 25-check bound makes, meaning the
    episodes that reach 25 checks with a question left;
  * `reference_bound_censored`: the episodes that run past 25;
  * `max_checks` and `ran_out_of_questions`.

  An episode runs identically up to the bound (common random numbers), so on
  an unbounded run `reference_bound_stops` is exactly what the old bound
  stopped. Every simulated cell (main, regimes, sweeps, Part C) records these
  counts under the report's `count_bound`. Report version
  `evsi_calibration_experiments_v3`.
* `learnloop evsi compare --old <report> --new <report>` (`compare.py`)
  lines up two `simulate` reports. It shows:
  * every recorded value, old against new, flagged when a point estimate
    leaves the other report's 95% CI or a value is present in one report
    only. Each arm's block in every cell and every report-level section is
    flattened leaf by leaf; only the metadata keys (`version`,
    `simulation_version`, `elapsed_seconds`, `settings`, `policy_defaults`,
    `sweeps`, `count_bound`) are left out, and the header shows them;
  * the bound's stops per arm and cell, cross-checked against the stop
    reasons the stored report kept. They count only when the unbounded
    report's `count_bound` counted the very bound the other report applied;
    otherwise the comparison says the attribution is unavailable, and why.
    `learnloop evsi simulate --reference-bound N` (default 25) makes an
    unbounded run count a bound of N;
  * the attribution check: every arm where the bound stopped no episode must
    be identical, and an arm where it stopped episodes only at a check their
    own rule would have stopped at anyway may differ only in its stop
    reasons;
  * the review's 17 headline claims, each as separate assertions (its
    conclusions, and the figures it states at their precision), under each
    report;
  * each cell's ranking of the arms.

  Ordering follows the study (sections, regimes, sweeps, then
  `ALL_POLICIES`), never a stored dict's. Outputs are written atomically and
  never over an input report. The CLI help snapshot was regenerated.

## 2. The rerun

```bash
uv run learnloop evsi simulate --eedi-2024 fixtures-local/eedi-2024 \
    --fit fixtures-local/evsi-calibration-v2/response_fit.json \
    --output fixtures-local/evsi-calibration-v3-unbounded \
    --workers 8 --seed 20261012 --learners 400 --sensitivity-learners 300
uv run learnloop evsi compare \
    --old fixtures-local/evsi-calibration-v2/simulation_report.json \
    --new fixtures-local/evsi-calibration-v3-unbounded/simulation_report.json \
    --output fixtures-local/evsi-calibration-v3-unbounded/comparison_vs_v2.json \
    --markdown fixtures-local/evsi-calibration-v3-unbounded/comparison_vs_v2.md
```

The run took 730 s on 8 workers, from commit `a2521921`. It used the stored
fit (Eedi 2020 source hash `70a1c5606097637b`) on the same Eedi 2024 bank
(`8e78726b96e79fae`). It kept the same seed and sizes: 400 flagged learners
per world, 300 per sensitivity arm, 32 ensemble draws and 400 bootstrap
draws. Everything lives in the worktree's gitignored `fixtures-local/`:

* the new report is in `fixtures-local/evsi-calibration-v3-unbounded/`;
* the stored report, `fixtures-local/evsi-calibration-v2/simulation_report.json`
  (`evsi_calibration_experiments_v2`, sha256 `4e6c5b1d…`), was read and
  never written.

## 3. What the bound stopped in the stored run

Per arm and section, over every cell: the episodes the 25-check bound stopped
(from the unbounded run's `count_bound`) and the largest episode without it:

| Section (cells) | Arm | Stopped at 25 | Of which ran past 25 unbounded | Largest episode unbounded | Ran out of questions |
|---|---|---:|---:|---:|---:|
| main (2) | `eig_no_gate` | **2** (fitted system; 0 under `hand_set`) | 2 | 34 (hand-set: 19) | 115 |
| main (2) | `eig` / `evsi` / `evsi_lcb_only` / `evsi_lookahead` | 0 | 0 | 3 / 1 / 3 / 3 | 16 / 8 / 8 / 8 |
| main (2) | `incumbent`, `caps_only`, `random`, `max_entropy` | 0 | 0 | 4 | 50–70 |
| regimes (9) | `eig_no_gate` | **6** (2 in each fitted regime; 0 at 0.7 and 0.9) | 6 | 34 (0.7: 16; 0.9: 14) | 531 |
| regimes (9) | `eig` / `evsi` / `evsi_lcb_only` / `evsi_lookahead` | 0 | 0 | 5 / 1 / 8 / 8 | 75 / 36 / 39 / 39 |
| regimes (9) | capped arms | 0 | 0 | 4 | 222–300 |
| sensitivity (30 runs) | `evsi` / `evsi_lcb_only` / `evsi_lookahead` | 0 | 0 | 2 / 5 / 8 | 90 / 111 / 111 |
| sensitivity (8 runs, nat scale) | `eig` / `eig_no_gate` | 0 | 0 | 2 / 18 | 38 / 146 |
| Part C (16 runs) | `evsi_lcb_only` / `evsi_lookahead` / `incumbent` | 0 | 0 | 5 / 5 / 4 | 66 / 66 / 400 |

The 8 stops are the same two learners counted in four cells:

| Learner | Subject (questions) | Truth | Stored (bounded) | Unbounded | Action |
|---:|---|---|---|---|---|
| 42 | 224 (30) | `other` | 25 checks, `safety_bound`, 28 min | 26 checks, `robust_eig_stop`, 29 min | `continue` (wrong) both |
| 206 | 64 (53) | `other` | 25 checks, `safety_bound`, 28 min | 34 checks, `robust_eig_stop`, 37 min | `continue` (wrong) both |

**Cross-checks.** The 253 counted (cell, arm) pairs were checked against the
stored report's own stop reasons wherever it kept them:

* **173 agree**: all 18 main pairs (each keeps every reason, and the fitted
  `eig_no_gate` lists `safety_bound: 2`), 77 regime pairs and 78 sweep pairs
  whose kept reasons are complete.
* **None disagree.**
* **80 cannot be checked from the stored report**: the 48 Part C runs keep no
  stop reasons, and 32 regime and sweep pairs kept only their top four or
  three reasons. For those the unbounded count (0 stops, at most 8 checks) is
  the evidence, together with their numbers, which reproduce exactly.

An independent per-learner replay of the fitted-world `eig_no_gate` arm, run
bounded at 25 and unbounded (a scratch script, not committed), differs in
exactly learners 42 and 206. It reproduces both means: 8.435 bounded, as
stored, and 8.46 unbounded, as rerun.

Why so few: only a rule that keeps checking reaches 25. The capped arms stop
at 4, and the value rules stop after at most 8 checks. Only the gate-free EIG
rule at 60 minutes per nat keeps going, and only in a subject with more than
25 unanswered questions; the bank averages 15.5 questions per subject. The
multi-family study found more (181 episodes across 54 cell × arm vectors).
Its other families and worlds keep that rule checking longer.

## 4. Old against new, claim by claim

"Stored" is `fixtures-local/evsi-calibration-v2/` (bound 25); "unbounded" is
this rerun. Minutes per episode with 95% CIs unless stated. ✓ means the
numbers are identical to the last stored digit.

| Claim (calibration review) | Stored | Unbounded | Beyond CI? | Verdict |
|---|---|---|---|---|
| `S2` Value rules beat today's serving at Eedi's strength (Summary 2, §4.2–4.3) | incumbent 3.77 [3.59, 3.92] / 7.98 / 20.03 vs `evsi` 1.81 [1.67, 1.96] / 6.03 / 18.08 at repairs 3 / 10 / 30 | ✓ | no | **holds, unchanged** |
| `S3a` EVSI as built under-probes where checks are strong (0.9/30) | `evsi` 17.93 [16.44, 19.36] vs incumbent 13.32 [11.65, 15.05] | ✓ | no | **holds, unchanged** |
| `S3b` … because of the flip abstention | `evsi_lcb_only` 12.52 [11.11, 14.02] (−5.4) | ✓ | no | **holds, unchanged** |
| `S3c` … and one-step valuation: the 2–3 check lookahead | `evsi_lookahead` 10.76 [9.09, 12.59] (−1.8 vs lcb-only, −2.6 vs incumbent) | ✓ | no | **holds, unchanged** |
| `S3d` 1.1–1.2 remain against caps-only and `eig_no_gate` (0.9/30) | caps_only 9.63 [8.14, 11.28], `eig_no_gate` 9.58 [7.77, 11.17] | ✓ | no | **holds, unchanged** |
| `S3e` The lookahead is the best rule at 0.9/10 | 4.99 [4.43, 5.61] vs incumbent 5.82, caps-only 5.13 | ✓ | no | **holds, unchanged** |
| `S3f` Today's robust completion gate costs 3.7 at 0.9/30 | 13.32 − 9.63 = 3.69; gate stops 190/400 at 0.9, 296/400 at Eedi's strength | ✓ | no | **holds, unchanged** |
| `S3g` The `eig_no_gate` arm in every regime | fitted: 8.44 [7.88, 9.02] / 12.39 [11.48, 13.34] / 23.69 [21.58, 25.79], 6.74 checks; 0.7: 6.54 / 8.85 / 15.45; 0.9: 4.99 / 6.18 / 9.58 | fitted: **8.46 [7.89, 9.07] / 12.41 [11.50, 13.35] / 23.71 [21.60, 25.79], 6.77 checks**; 0.7 and 0.9 ✓ | no | **holds**: worst rule at Eedi/3, best at 0.7/30 and 0.9/30; the stated figure 8.44 is now 8.46 |
| `S4a` `VALUE_PER_NAT_MINUTES` on the gate-free EIG rule (0.9/10) | 6.17 / 5.90 / 5.10 / **4.75** / 5.52 / 6.28 / 6.64 / 7.32 at 1 … 120; at 10: Δ −1.89 [−2.26, −1.52] vs 60; with the gate \|Δ\| ≤ 0.19 | ✓ (this sweep's longest episode: 18 checks) | no | **holds, unchanged** |
| `S4b` 60 is 4–500× the measured minutes per nat; the agreement gate abstains in 89% | 4.06 [2.88, 5.20] / 5.10 at 0.9/10, 12.19 [8.95, 15.72] / 15.31 at 0.9/30 (incumbent / caps-only); abstentions 354/400 | ✓ | no | **holds, unchanged** |
| `S5a` `ROBUST_QUANTILE` 0.10 → 0.25 within noise | Δ −0.10 [−0.30, 0.12] (lcb-only), −0.15 [−0.38, 0.08] (lookahead); at 0.5: −0.24, −0.30 | ✓ | no | **holds, unchanged** |
| `S5b` `PERTURBATION_DELTA` has no minutes effect | \|Δ\| ≤ 0.027 (`evsi`), 0 exactly for lcb-only and lookahead | ✓ | no | **holds, unchanged** |
| `S5c` Concentration and draws move rankings, not minutes | every \|Δ\| ≤ 0.24 with CI spanning 0, except `evsi` at concentration 4 and 10: −0.013 [−0.027, −0.003] | ✓ | no | **holds, unchanged** (see below) |
| `S5d` A positive `BURDEN_COST` only adds minutes | +0.30 [0.05, 0.53] … +0.79 [0.34, 1.15] | ✓ | no | **holds, unchanged** |
| `S5e` Knowing the true repair minutes is worth 0.7–1.1 | −0.71 [−1.10, −0.29], −1.06 [−1.47, −0.58] | ✓ | no | **holds, unchanged** |
| `S5f` The causal 1.5-minute check burden over-states a 1-minute check | +0.30 [0.05, 0.53], +0.44 [0.20, 0.71] | ✓ | no | **holds, unchanged** |
| `S6` The measured loss pays off from about 3.6 minutes (Part C) | at 0.9, U = 3.63: −0.54 [−0.89, −0.26] (lcb-only), −0.56 [−0.93, −0.26] (lookahead); U = 7.25: −1.53, −1.47; no CI below 0 at Eedi's strength or below U = 3.63 | ✓ | no | **holds, unchanged** |
| `DEFAULT_CONDITIONAL_PSEUDO_COUNT` 8 → 2 | not simulated in the single-family study (§5 there) | — | — | **out of scope**: the multi-family §4.9 streams cap at 4 checks and never read the bound |

Every recorded value outside the four fitted-world `eig_no_gate` rows is
identical: forecast quality and its calibration bins (§4.1), checks,
identification and waste (§4.2), minutes per nat, member quantiles, Kendall τ
in the sweeps, Part C, the recommendations, the fit and every other
report-level section. In all, 4,104 of the 4,208 compared values are
identical and 104 moved (9 within their CIs, 95 carry none; none beyond a CI),
all of them in those four rows: the 71 of the main comparison's row (its
episode summary, outcome and action-change calibration with their bins,
information by predicted-EIG quintile, value of checks and member quantiles)
and 9 to 12 in each regime row (minutes, checks, waste, stop reasons, realized
value, member quantiles, minutes per nat). 71 values are absent from both
reports: the forecast and value metrics of arms that never check, and τ where
a sweep records none. The complete list is in `comparison_vs_v2.md` beside
the report.

One imprecision predates the bound and is unchanged by it. The calibration
review's Summary 5 says the concentration and draw-count sweeps' "paired 95%
CIs include 0". For EVSI as built at a concentration of 4 or 10, the
difference is −0.013 minutes per episode with a CI just clear of 0, [−0.027,
−0.003]. That is no decision effect, and the conclusion stands. The same
−0.013 [−0.027, −0.003] appears for EVSI as built at a `BURDEN_COST` of 2, so
"a positive burden only adds minutes" (`S5d`) holds for `evsi_lcb_only` and
`evsi_lookahead`, the arms the calibration review's §4.4 reports differences
for (EVSI as built is "≈ 6.18" there), and those are the arms its assertion
checks. The assertion labels in `comparison_vs_v2.md` say exactly what each
checks.

## 5. Ranks, and `evsi-multisim.md` §6

**Ranks.** The two main cells and the nine regime cells each rank the nine
arms by mean minutes per episode, and every ranking is the same in both
reports. No winner changes. The only arm that moved, `eig_no_gate` in the
fitted world, moved by 0.025 minutes. Its nearest neighbour there is at least 2.4
minutes away (8.46 against caps-only's 5.18 at repair 3; 23.71 against
random's 21.31 at repair 30).

**`evsi-multisim.md` §6.** Nothing changes:

* **Ranks 1–5 (ship)** are each decided by multi-family claims (`A1`, `A3`,
  `C6a`/`C6`, `C5`, `S4`/`A2`/`A4`). They come from the multi-family run,
  which had no count bound.
* **§6.2 (wait)** and **§6.3 (no change)** rest on the same evidence.
* **The single-family values the multisim Summary quotes** as its
  "Single-family value" column are all identical in this rerun: 0.83 vs
  0.41, −0.06 and +0.10 nats, 1.81 vs 3.77, 17.9 vs 13.3, 17.9 → 12.5,
  12.5 → 10.8, 10.8 vs 13.3, +3.7, 4–500×, 3.6 and "within noise". So are
  the 0.9/30 numbers its §4.3 compares the refitted `lca` with (13.32, 9.63,
  17.94, 12.52, 10.76).

## 6. Superseded numbers in `evsi-calibration.md`

Only these, all for `eig_no_gate` in the fitted world (each marked in place
there, with an addendum pointing here):

| Where | Stored | Unbounded |
|---|---|---|
| §4.1, `eedi_fitted` `eig_no_gate` row | log loss 1.212; predicted EIG 0.069; realized gain 0.073 [0.063, 0.085] | 1.213; 0.068; 0.073 [0.063, 0.084]. The table's other columns round as before: ECE 0.0029 (identical); entropy drop 0.0733 → 0.0731; P(action change) 0.0665 → 0.0666 predicted, 0.0668 → 0.0665 realized; EVSI per check 0.0233 (identical) / 0.0167 → 0.0166 |
| §4.2, `eedi_fitted` `eig_no_gate` row | 6.74 checks; 8.44 [7.88, 9.02]; wasted 6.96; value stop 317 | 6.77; 8.46 [7.89, 9.07]; 6.99; 319 |
| §4.3, Eedi 0.41 rows, `eig_no_gate` column | 8.44 (6.7; .53) / 12.39 / 23.69 | 8.46 (6.8; .53) / 12.41 / 23.71 |

## 7. Tests

`tests/test_evsi_single_family_unbounded.py` (5 tests at the stage, 41 after
the Codex review; the review's additions are listed below these):

* **The single-family path defaults to no bound.** `PolicySettings`,
  `SimulationSettings` and `ExperimentSettings` default to `None`. Every
  `run_simulation` the study makes (main, regimes, sweeps, Part C) is
  unbounded, the report records it, and every section's cells are counted.
  On a 40-question bank, episodes run past 25 checks and end by their rule or
  the bank.
* **An explicit bound still stops,** and the unbounded run counts exactly its
  stops. With `safety_bound=25` every episode stops at 25 (`safety_bound`).
  `bound_counts` on the unbounded run equals the bounded run's stops, and an
  episode that its own rule stops at exactly 25, or that the bank ends there,
  is counted correctly.
* **The CLI passes `--safety-bound` and `--reference-bound` through:** the
  report's settings, the `count_bound` block and every cell's `max_checks` ≤
  the bound.
* **The comparison's ordering is stable.** Comparing reports whose dict keys
  and record lists are reversed, or that were round-tripped through JSON with
  sorted keys, gives byte-identical output and Markdown. Sections, regimes,
  arms and claims come out in the study's order. A number moved beyond its CI
  is flagged where it is, and only there.
* **The stored report's own stop reasons are read only where complete**
  (main always; regimes and sweeps when fewer than the kept count, or when
  they sum to the episodes).
* After the Codex review:
  * **every recorded value is compared** (F1): an untouched arm's member
    quantile set to 999 is flagged, and so is a change to one representative
    leaf of every kind in a report (each arm block's fields, bins and stop
    reasons, each cell's own values, every report-level section). A change to
    a metadata key is not;
  * **the bound's counts are the bound's only for the bound applied** (F2): a
    3-check run against an unbounded run that counted the 25-check bound is
    unsupported; against one that counted the 3-check bound, the stops agree
    with the stored stop reasons and every differing row is one the bound
    reached, in both directions; two bounded reports, or one without
    `count_bound`, are unsupported; the same bound in both explains nothing;
  * **each claim is its assertions** (F3): on the stored run's numbers
    (`tests/evsi_calibration_claims_v2.json`) all 31 conclusions and 42
    figures hold; each conclusion has a change that falsifies it while the
    claim's other conclusions still hold (31 parametrized cases, one of them
    with the conclusion it logically implies); each figure fails just outside
    its stated precision; the Codex case (minutes per nat at 50 [49, 51], no
    abstentions) no longer certifies `S4b`.

Also updated: `tests/test_evsi_multisim.py` (the default is `None`; an
explicit bound still stops the successor) and
`tests/test_evsi_calibration_sim.py` (the quick CLI run records no bound).

## 8. Gate

In the worktree, with `TMPDIR` set to its `fixtures-local/tmp`, at the code
commit `e2794743` (the commits after it change documentation only). The gate
after the Codex review's fixes is in its review file.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 14 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8,683 passed**, 0 failed, 0 skipped (4 min 42 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **94 passed**, 8,589 deselected (1 min 34 s) |
| targeted: `tests/test_evsi_single_family_unbounded.py`, `tests/test_evsi_calibration_sim.py`, `tests/test_evsi_multisim.py`, `tests/test_evsi.py`, `tests/test_cli_help_snapshot.py` | 56 passed |

No frontend, `src-tauri`, schema or migration change, so the npm, cargo and DB
reference steps do not apply.

## 9. Paid calls and data

None: no model route, no OpenRouter or Codex call, $0.00. The study reads only
the Eedi files and the stored fit under the worktree's gitignored
`fixtures-local/`. No vault was opened, and no tracked fixture vault was
touched.

## 10. Open questions

None that block anything. One housekeeping choice for the owner: should
`fixtures-local/evsi-calibration-v3-unbounded/` become the study's reference
report? It is the stored one with two episodes corrected. The multi-family
commands' `--fit` still names `evsi-calibration-v2/response_fit.json`, which
this rerun reused unchanged.

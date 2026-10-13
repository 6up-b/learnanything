# Codex review: the single-family EVSI study without its count bound

Stage `evsi-single-family-unbounded`, branch `evsi/calibration`. Codex
reviewed the stage at `013a0ca4` (job `20261013-150228-cdrx9F`). It confirmed
the bound removal: learners 42 and 206 run to 26 and 34 checks, with their
final actions unchanged. It found three Medium defects in the new comparator,
`learnloop evsi compare` (`src/learnloop/evsi_calibration/compare.py`). All
three reproduced and are fixed in `da5c9ecf`. The stage review
([`evsi-single-family-unbounded.md`](evsi-single-family-unbounded.md)) is
corrected in place, and its comparison
(`fixtures-local/evsi-calibration-v3-unbounded/comparison_vs_v2.{json,md}`)
was regenerated with the fixed comparator.

## Review

### Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | The "every metric" comparison silently omits changed metrics | fixed | `da5c9ecf` | `test_every_recorded_value_is_compared` |
| F2 | Medium | Comparisons against other supported bounds use the wrong censoring counts | fixed | `da5c9ecf` | `test_the_bound_attribution_needs_the_bound_the_other_report_applied`, `test_cli_simulate_passes_an_explicit_bound_through` |
| F3 | Medium | Headline verdicts certify weaker conditions than their statements | fixed | `da5c9ecf` | `test_each_conclusion_is_falsified_on_its_own` (31 cases), `test_each_stated_figure_is_checked_at_its_precision`, `test_the_codex_case_no_longer_certifies_s4b`, `test_every_assertion_of_every_claim_holds_on_the_stored_run` |

All tests are in `tests/test_evsi_single_family_unbounded.py`.

### Reproduction (before the fix, at `013a0ca4`)

* **F1.** On the stored reports, no compared label named a member quantile,
  a Brier score or a calibration bin. Setting an untouched arm's q10 (main
  `hand_set`, `incumbent`) to 999 left that arm `identical` and
  `untouched_differing` empty. A full leaf diff of the two reports shows
  values that changed in the rerun and were never compared: the fitted
  `eig_no_gate` quantiles (q10 −0.0038 → −0.0037, q25 0.0059 → 0.0060 in the
  main row; q05–q50 in each fitted regime), action-change ECE 0.0038 →
  0.0041, Brier 0.1620 → 0.1622, `model_minutes_per_nat`, and the
  calibration bins and predicted-EIG quintiles.
* **F2.** Two tiny synthetic studies (the stage tests' Eedi stand-ins) were
  compared: one bounded at 3 checks, one unbounded that counted the 25-check
  bound's stops. The 3-check bound stopped 192 episodes. The reviewed
  comparator reported 0 stops, treated the attribution as checked, and listed
  47 rows as unexplained differences (`main hand_set caps_only`, …).
* **F3.** S4b held with every relevant minutes-per-nat value at 50 [49, 51]
  and no agreement-gate abstention (`holds_new=True`,
  `conclusion_changed=False`). Two more gaps were found while splitting the
  claims. S5b's predicate allowed |Δ| ≤ 0.05 where the claim states 0.03, so
  a Δ of 0.045 still held. S3g's "worst rule at Eedi/3" was never checked.

### Fixes

* **F1: every recorded value.** Each arm's block in every cell (main,
  regimes, sensitivity rows, Part C) is flattened leaf by leaf. Each cell's
  own values (a sweep row's `current` flag) are compared, and so is every
  report-level section: the fit, the bank, the misfit, the hand-set implied
  values, the starting beliefs, the worlds' learner counts, Part C's measured
  rates, the sweeps' parameters, and the recommendations (one row per
  parameter and arm). The comparison leaves out only an explicit list of
  metadata keys (`METADATA_KEYS`: `version`, `simulation_version`,
  `elapsed_seconds`, `settings`, `policy_defaults`, `sweeps`, `count_bound`).
  The header shows them, and the output names them under `not_compared`.

  How the flattening matches values:
  * Lists are named by content, not position. Reliability bins are named by
    their fixed range, predicted-EIG quintiles by rank, and records by
    `parameter` / `policy` / `name`. Reordered input still compares
    byte-identically.
  * Each CI travels with its point estimate.
  * A value present in one report only is a new status, `changed`. A stop
    reason absent from a record that keeps every reason reads 0, so the
    stored `safety_bound: 2` compares as 2 → 0.

  Markdown cells escape `|`, and numbers show the 4 places stored (3 places
  hid the q10 move).
* **F2: the bound's counts only for the bound applied.** `bound_stops` uses
  the unbounded report's `count_bound` only when its `reference_bound` equals
  the bound the other report applied, and its own `applied_bound` is none.
  Otherwise the comparison says `relation: unsupported`, sets `available`
  false and gives the reason, and the attribution reads `checked: false`.
  This covers two bounded reports, an unbounded report without
  `count_bound`, and one that counted another bound. Two reports under the
  same bound (or both unbounded) are `same_bound`: the bound explains no
  difference, so every row must match. To get counts for another bound, run
  `learnloop evsi simulate --reference-bound N` (new, default 25).

  The attribution now separates three kinds of row:
  * rows the bound never reached, which must be identical;
  * rows where it stopped episodes only at a check their own rule would have
    stopped at anyway, which may differ in their stop reasons alone. A bound
    is checked before a rule, so the stop is renamed `safety_bound`. These
    rows appear when the bound is 3 and the capped arms stop at 3;
  * rows with episodes that ran past the bound.

  On real 3-check runs, both directions of the comparison attribute every
  differing row to the bound. The stops agree with the bounded report's own
  stop reasons.
* **F3: claims as separate assertions.** Each of the 17 claims is a list of
  assertions, each evaluated on its own and labelled with exactly what it
  checks. There are 31 conclusions and 42 stated figures.
  * **Conclusions:** directions, strict best or worst arm, CIs below, above
    or spanning 0, and the bounds a claim states. S4b's conclusions are "60
    is above every measured CI", "60 is at least 4× every measured point" and
    "the gate stops most EIG episodes". S5b's is "|Δ| ≤ 0.03" at its stated
    precision. S3g's include "worst at Eedi/3". S5c's include "rankings
    move".
  * **Figures:** each number a statement gives, within half a unit of its
    last digit, or within a stated range such as "1.1–1.2", "500×" or
    "89%".

  `holds_old` and `holds_new` are now all of the conclusions. Figures are
  reported separately (`figures_old`, `figures_new`, `figures_changed`), and
  so is every assertion's verdict.

### The regenerated comparison (stored v2 against the unbounded rerun)

* **Values:** 4,104 of 4,208 compared values are identical. 104 moved: 9
  within their CIs and 95 with none. None moved beyond a CI, and none is
  `changed`. 71 are absent from both reports.
* **Rows and attribution:** 299 of 303 rows are identical. Every one of them
  is a row the bound never reached. The other 4 are the fitted-world
  `eig_no_gate` rows, the only rows the bound changed (8 stops, 8 censored).
  The cross-checks are as before: 173 agree, 0 disagree, 80 unverifiable.
* **Claims:** all 31 conclusions hold in both reports. All 42 figures hold
  in the stored report and 41 in the rerun. The exception is S3g's "8.44
  min at Eedi/3", now 8.46, which the calibration review already marks as
  superseded.
* **Ranks:** no rank changes.

The stage's verdict stands: every difference is the bound's, and no
conclusion changes.

### Claims Codex said do not hold

* **"Every metric of every cell" is compared:** true now (F1). The stage
  review's §1 and §4 describe what is compared and what is left out.
* **"Every other metric … member quantiles" is identical:** this was wrong
  for the fitted-world `eig_no_gate` rows. The review now lists what moved
  there: quantiles by at most 0.0004, action-change ECE, Brier, minutes per
  nat in the fourth decimal, and bins. Its §6 now gives the §4.1 columns'
  exact values instead of "unchanged at the table's precision".
* **All 17 headline claims are checked:** each is now checked as its
  separate assertions (F3). The review says which conclusions and figures
  hold. It also notes one scope narrowing found while splitting the claims.
  S5d ("a positive `BURDEN_COST` only adds minutes") is checked on
  `evsi_lcb_only` and `evsi_lookahead`, the arms the calibration review
  reports differences for. EVSI as built moves −0.013 [−0.027, −0.003] at a
  burden of 2. That is the same one-episode effect as the concentration
  imprecision the stage review already notes.

### Scope

All changes are in `src/learnloop/evsi_calibration/compare.py`,
`src/learnloop/cli/evsi.py` (`--reference-bound`, compare output),
`tests/test_evsi_single_family_unbounded.py`, the new test data file
`tests/evsi_calibration_claims_v2.json`, the regenerated
`tests/cli_help_snapshot.json`, and the review files. The test data holds the
fields the claims read of the stored v2 report: aggregate simulation outputs
the calibration review already publishes, and no Eedi rows. No serving code,
default, schema, migration or persisted meaning changed. Read-only reports
only. No vault was opened.

### Paid calls

None: $0.00, no model route, no OpenRouter or Codex call from this fix step.

### Gate

In the worktree, with `TMPDIR` set to its `fixtures-local/tmp`, at
`da5c9ecf` (the commit after it changes this file only):

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 14 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8,719 passed**, 0 failed, 0 skipped (5 min 5 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **94 passed**, 8,625 deselected (1 min 34 s) |
| targeted: `tests/test_evsi_single_family_unbounded.py` (41), `tests/test_evsi_calibration_sim.py`, `tests/test_evsi_multisim.py`, `tests/test_evsi.py`, `tests/test_cli_help_snapshot.py` | 92 passed |

The CLI help snapshot was regenerated (`evsi`, `evsi simulate`,
`evsi compare`). No frontend, `src-tauri`, schema or migration change, so
the npm, cargo and DB reference steps do not apply.

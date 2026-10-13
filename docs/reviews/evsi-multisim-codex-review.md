# EVSI multi-family study: Codex review fixes

Stage `evsi-multisim`, branch `evsi/calibration`. Codex review job
`20261013-094805-rur4XA` (read-only; it ran no gate: the sandbox was
read-only and the full suite was cancelled while waiting on the lock). Every
finding was reproduced first: a test that fails on the reviewed code
(`b3092af9`), and for F1–F4 the scenario Codex quoted, replayed on the reviewed
code from a `git archive` of it (numbers below). All five were fixed; none was
rejected. The study was rerun in every family with the fixes. No paid call,
no network, no vault database read, no tracked working vault touched: the
study reads only the Eedi files under the worktree's gitignored
`fixtures-local/`.

## Findings

| ID | Severity | Title | Verdict | Commit | Test (fails on `b3092af9`) and reproduction |
|---|---|---|---|---|---|
| F1 | High | The proposed package silently changes question selection | fixed, study rerun | `04af4cf8`, rerun `c36bf8cd` | `tests/test_evsi_multisim.py::test_the_package_with_every_piece_put_back_is_the_successor` (with the gate, the fallback and no lookahead put back, the package must equal `decide_successor` decision for decision on 27 beliefs × 3 repairs × 4 observation counts; and on a no-abstention state where two checks pay, the successor and the package serve the highest-EIG one). Replayed on `b3092af9`: LCBs `1` 5.50, `2` 5.48, `0` 5.07 (all pay), EIG `0` 0.809 highest; the successor served `0`, the package with every piece put back served `1` |
| F2 | Medium | Certification ignores adequacy and missing family coverage | fixed | `04af4cf8` | `::test_certification_needs_adequate_families_and_every_cell`, `::test_c1a_certifies_through_the_consistency_ci_not_a_fixed_margin`. Replayed on `b3092af9` with the stored report: every `adequate` set false still voted all four families, 20 claims `supported`, `voi_proposed` first by regret; `nrm`'s 0.9/30 cell removed gave `C2b:0.9/30` **supported, 3/3**. Fixed: no family votes, every claim `insufficient evidence`; with the cell removed, `insufficient evidence`, missing `nrm` |
| F3 | Medium | The NRM "calibrated" system averages the wrong quantity | fixed, study rerun | `04af4cf8`, rerun `c36bf8cd` | `::test_the_calibrated_systems_average_responses_over_the_item_pool` (an explicit item-mixture oracle built from the truth's own answer rows, one-item pools over the identical population, for `nrm` fitted and at 0.9, and for `cdm`). Replayed on the real fits: subject 239 / question 1260 / `mis:61`, option B **0.5894** on `b3092af9`, **0.5090** fixed (Codex's oracle value) |
| F4 | Medium | The safety cap changes the reported value-only results | fixed, study rerun | `04af4cf8`, rerun `c36bf8cd` | `::test_the_multi_family_study_runs_every_episode_without_a_count_bound` (a 40-question subject: every episode of a rule that never stops runs to the bank's end; with the old bound each stops at 25, `safety_bound`). Replayed on `b3092af9`, `nrm` fitted/3 `eig_no_gate`: learner 357 **25 checks, 31 min, `safety_bound`**, learner 402 25 checks, `safety_bound`. Fixed (with F3's system): 357 **40 checks, 46 min, ending on its value rule**; 402 27 checks, its subject's questions exhausted |
| F5 | Medium | Reanalysis can destroy the expensive simulation artifact | fixed | `04af4cf8` | `::test_reanalysis_never_destroys_the_stored_report` (an interrupted `--reanalyze`, the disk full while flushing: on `b3092af9` the stored report was truncated to a third), `::test_the_atomic_writer_keeps_the_old_file_on_any_failure` |

The review's "claims that don't hold" are each corrected in
[`evsi-multisim.md`](evsi-multisim.md): the package is now the successor plus
exactly three changes (F1); a conclusion counts only when every *adequate*
family agrees, and a missing cell is `insufficient evidence` (F2); the
calibrated systems are population-and-item-pool averages (F3); value rules run
with no count bound (F4); and `C1a` is certified through a 95% CI, not a
fixed 0.2 margin.

## What changed

**F1 (selection).** `policies.decide_package` builds on the successor's own
pieces: its value gate (`_successor_value_gate`, now returning a `ValueGate`
with the ranking) when the fallback is put back, else the robust-LCB gate
(`_lcb_value_gate`: `rank_feasible`'s paying checks, a flip abstention
included); then the successor's serving rule (`_serve_paying`: the
highest-EIG check when it pays, else the best paying one). When no single
check pays and the LCB decided, the 2–3 check lookahead (`_paying_batch`,
factored out of `decide_lookahead` unchanged) makes every check of the paying
batch pay; the highest-EIG one is served when it is in the batch, else the
batch's top-ranked one. With the gate, the fallback and no lookahead put back
the package **is** `decide_successor` (tested decision for decision). The
top-value serving the first run measured unawares is now its own arm,
`voi_p_top_value`, ablated as claim `A4`; `S4` (the stability stops) now
compares `voi_p_top_value` with `evsi_lookahead`, which differ by the stops
alone.

**F2 (certification).** `multifamily.analyze` lets only families that pass
the held-out adequacy gate vote (`_voting_families`; a family failing it,
without validation, or required by the study's settings but absent from the
report is listed in `excluded_families` with its reason). Every claim checks
coverage: each voting family (for `C6c` each family × regime, for rotation
claims each truth × other-family system) must have a value, else the verdict
is `insufficient evidence` and the claim names what is missing; with fewer
than two voting families (`MIN_VOTING_FAMILIES`) every claim is
`insufficient evidence`. A value certifies only through its 95% CI
(`_ci_only`): `implied_quantities` now returns a CI of the bank-mean
consistency (subjects resampled, 400 draws), and `C1a` is certified when it
lies below the card's 0.83. Winners and the regret ranking report
`complete`/`missing`, and an arm with a missing cell ranks after every
complete one.

**F3 (calibrated systems).** `NrmScenario` averages each population state's
response probabilities over the item pool (`pool_probabilities`, vectorized in
blocks of 64 items; `_logits` takes one item or a block); `CdmScenario`
averages each profile's rows over the pool (`_cdm_rows`). The strength
bisection reads the holders' rows only (`NrmScenario.targeted_consistencies`:
the same rows, without the population states that hold nothing, 4 s per pass
instead of 77 s), and each worker caches finished `nrm` rows per study, keyed
by a fingerprint of the pool, typical item, shift and subject. On the real
fits `nrm`'s knower slip moves from 0.141 to 0.183 and its consistency from
0.460 to 0.439; `cdm` moves by under 0.006.

**F4 (count bound).** `PolicySettings.safety_bound` is optional; the
multi-family study (`multifamily.study_base`, and `MultiSimSettings`' default)
runs with none. The single-family study keeps its 25. Each cell's policy table
records `max_checks`, `ran_out_of_questions` and `count_bound_stops`.

**F5 (artifacts).** `evsi_calibration.artifacts.write_text_atomic` writes a
sibling temporary file, flushes and fsyncs it, `os.replace`s the destination
and fsyncs the directory; on any failure the destination is untouched and the
temporary removed. Every fit and report the CLI writes goes through it,
`--reanalyze` included.

## The rerun (F1, F3, F4)

`learnloop evsi multisim` with the stored family fits, every family, every
arm, 12 workers: 99 minutes (`fixtures-local/evsi-multisim-v4/`, gitignored;
re-scored with `--reanalyze` after `e3df1f50` added claims `S5`/`S6`, the
as-run copy kept beside it). All four families pass the adequacy gate, so
none is excluded and every claim covers every voting family's cells.

**Consistency with the first run.** In `lca`, `lta` and `lta_reveal` (any
system not calibrated to `cdm` or `nrm`), every arm's per-learner episodes are
identical to the first run's except where a fix changed them: `eig_no_gate`
only for learners the old bound had stopped at 25 checks (the first run had
181 such episodes across 54 cell × arm vectors), and the package arms. The
new `voi_p_top_value` reproduces the first run's `voi_proposed` in all 39
such cells, which confirms F1's diagnosis: the first run's package was the
top-value serving variant. `cdm` and `nrm` change throughout (F3).

**What moved** (every number in [`evsi-multisim.md`](evsi-multisim.md)):

| Result | First run | After the fixes |
|---|---|---|
| `nrm` system: knower slip / consistency | 0.141 / 0.460 | 0.183 / 0.439 |
| `C1a` (the card is overconfident) | supported by a fixed 0.2 margin, no CI | supported through each family's CI (`lca` 0.41–0.44, `cdm` 0.24–0.26, `nrm` 0.43–0.45, `lta` 0.36–0.39) |
| `C1c` (calibrated checks inform) | directional (`nrm`'s CI touched 0) | **supported** (`nrm` +0.04 [0.01, 0.08]) |
| `C2c:0.9/30` (the lookahead over the one-step rule) | family-dependent (`nrm` +0.03) | **directional** (−0.18 to −2.59) |
| `C6a` (q10 under-predicts realized value) | family-dependent (`nrm` 0/5) | **directional** (28 of 28 cells) |
| `S2:0.9/30` (package vs successor) | family-dependent (`nrm` +0.12) | directional (−0.29 to −3.56) |
| `S3:0.9/30` (package vs incumbent) | directional | **supported** (−1.15 to −3.29) |
| `A4` (top-value serving inside the package) | not measured | family-dependent; costs +0.48 [0.05, 1.01] (`nrm`) and +0.54 [0.04, 1.12] (`cdm`) at 0.9/30 |
| `A2` (the abstention fallback) | no measurable effect | no effect in 19 of 20 cells; keeping it saves 0.56 [0.02, 1.14] in `cdm` 0.7/30 |
| Worst-case regret: `voi_proposed` / best arm | 1.21 / `voi_proposed` | 1.50 / `voi_p_top_value` 1.21 (fails the bounded-harm rule); `voi_p_with_fallback` 1.28 with the lowest mean regret |
| `C4` (60 vs the largest minutes per nat) | 3.8–8.6× | 3.8–6.2× (`nrm` 9.7, not 7.0) |
| `eig_no_gate` episode length | capped at 25 | up to 26–43 checks |

**The proposal changed.** The first report's rank 3 (decide a flip
abstention by the robust LCB instead of the nat scale) is withdrawn: `A2`
finds no gain and the fallback-kept package has the better worst case and
the lowest mean regret. Its rank 4 (a successor-scoped nat scale of 5)
depended on rank 3 and moves to "wait". `ROBUST_QUANTILE` 0.25 moves from
"wait" to rank 3 (`C6a` now directional). The recommended package is the
successor with the gate dropped and the lookahead added
(`voi_p_with_fallback`), and the successor's serving rule is kept (`A4`).

## Claims withdrawn or corrected

* "The package keeps the successor's structure with three changes" (F1): it
  also changed the serving rule. The package now differs by exactly its named
  changes; the serving change is measured as `A4` and is not proposed.
* "The proposed package has the smallest worst-case regret of all 14 arms:
  1.21": with the successor's serving rule and the corrected `nrm` system the
  package's worst case is 1.50; the recommendation is now the fallback-kept
  package (1.28, lowest mean regret).
* "A conclusion counts only when every family agrees" (F2): now enforced:
  only adequate families vote, a missing cell is `insufficient evidence`.
* "Population-average calibrated single-cause model" (F3): now also an
  average over the item pool, for `nrm` and `cdm`.
* "Value rules carry no count cap (a 25-check safety bound, never reached in a
  cell's mean)" (F4): the bound was reached by 181 episodes; there is no
  bound now.
* "`C1a` supported: every family's 95% CI agrees": `C1a` had no CI; it now
  has one, and a value without a CI is never certified.
* "`C1c` directional because the single-cause system approximates `nrm`'s
  continuous trait least well", "`ROBUST_QUANTILE` waits because `nrm`
  over-predicts value", "the lookahead gains nothing in `nrm`": all three
  were F3, `nrm`'s mean-parameter system.
* The first report's ranks 3 and 4 (above).

## Gate

Run at `e3df1f50` (the last code commit; this file and the report are
documentation only), in the worktree, `TMPDIR` under its `fixtures-local/tmp`:

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 14 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8676 passed**, 0 failed, 0 skipped (5 min 2 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **94 passed**, 8582 deselected (1 min 48 s) |
| the same two at `04af4cf8` (the fixes, before `S5`/`S6`) | 8676 passed, 0 failed, 0 skipped (5 min 27 s); 94 passed, 8582 deselected (1 min 30 s) |
| targeted: `tests/test_evsi_multisim.py`, `tests/test_evsi_calibration_sim.py`, `tests/test_evsi.py` | 48 passed |

The new tests are 8 of the full suite's count (8668 at `e6cac56e`, the
reviewed stage's gate). No frontend, `src-tauri`, schema or migration
change: the npm, cargo and DB reference steps do not apply. No paid call.

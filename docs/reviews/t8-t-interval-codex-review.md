# T8 t-interval (pre-registration v4): review fixes

**Checkpoint:** branch `fix/t8-t-interval` (worktree `learnanything-t8-t`).
- **Reviewed:** code commit `1ff2c89d` and docs commit `8340a7e6`.
- **Fix commit:** `61953acd`. This file is committed after it.
- **Scope:** offline research code only. There is no serving effect, no
  successor, no migration and no config default change.
- **Not touched:** `field/offline_llm.py` (router R0 changes it next).
- **Not done:** nothing was merged or pushed.

**Owner decisions in force (2026-10-12):**
- For T8, in the owner's words: "1. Yes to a t interval. 2. Yes you can
  "kill" but log it with our delta value so we can monitor if delta needs
  changing in the future as a value."
- The recommended defaults recorded in each spec are accepted; the owner may
  override any of them at its checkpoint.
- Frictionless defaults: honest labels, generous defaults.

**The pre-registration** stays `t8-preregistration-v4`. It was amended in
review, before merge and before any owner-data run, as v3 was in its own
review. That changed its hash:
- **Now:** `9f686a23048ea1403b233ee15983c83a93f38f0af75da219f31c53f1f087866b`.
- **First staged:** `6c7223178ce70c10b83364e356fc5bafea7e7c799c6bed8f60f213fa97717e18`.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | A real gain below δ is now `kill`, which changes what the router trigger reads | fixed | `61953acd` | Docs only: no code reads the verdict for the router (grep). Router §13 condition 3 now names the outcomes that meet it, recorded as router D10. Reproduced by `_verdict` on [0.001, 0.004]: `kill` / `real_gain_below_delta` (v3: `embeddings_add_value`); pinned by `test_a_real_gain_below_delta_is_kill_with_its_reason` |
| F2 | Medium | v3's nested-baseline assurance was not re-checked under the kill-first rule | fixed | `61953acd` | The synthetic grid was rerun under v4 (below). A `real_gain_below_delta` kill is now provisional in the frozen pre-registration, the report and spec §11. `test_a_real_gain_below_delta_is_kill_with_its_reason` checks the provisional text in each place |
| F3 | Low | Reason text rounded to 4 significant figures can contradict itself at the δ boundary | fixed | `61953acd` | `test_the_verdict_at_the_boundaries_never_contradicts_its_reason` (6 cases, including exactly upper = δ and lower = m) and `test_the_flipping_delta_is_where_the_verdict_changes` |
| F4 | Low | The same comparison is reported with two different intervals | fixed | `61953acd` | `test_the_primary_comparison_is_never_reported_with_a_second_interval`; `test_every_interval_in_the_t8_report_clusters_items_and_names_its_method` updated |
| F5 | Low | D9 still names a bootstrap interval while T8 takes its margin "from D9" | fixed | `61953acd` | Docs only: spec §11 and field D9 |

**Fail-first.** The final `test_success_head.py` was run against the reviewed
source (`git archive 8340a7e6 src migrations`, on `PYTHONPATH`): 12 failed,
36 passed. Each failure has the cause the findings describe:
- **F3, all 6 boundary cases:** there was no `flipping_delta`. Two cases also
  printed a contradiction, for example "upper bound 0.005 < δ = 0.005 … for
  any δ <= 0.005" for an upper bound of 0.0049996. The flip test failed too.
- **F4:** the descriptive interval was the percentile [−0.00094, 0.00942],
  and the primary's t interval was [−0.00089, 0.01085]. The every-interval
  test expected the t method for this comparison.
- **F2 and F3:** the real-gain test, which also asserts the provisional
  text, failed at its first new assertion (no `flipping_delta`). The
  δ-recorded test found no `real_gain_below_delta` or `flipping_delta` entry
  in `decision_rule`.
- **The hash test:** the digest still equalled the first-staged v4 hash.

On the fixed source, all 48 pass.

### F1: the router trigger reads the lower bound

**Reproduced.** For a primary interval of [0.001, 0.004], v4 gives `kill` /
`real_gain_below_delta`; v3 gave `embeddings_add_value`. Router §13
condition 3 ("Slice 2 T8 shows embeddings add held-out predictive value") is
literally met here. A trigger that checks the verdict name would read it as
not met.

**Fixed** (`spec_action_router_v1.md`):
- **§13 condition 3** now says it is met when the primary verdict's lower
  bound is above m: `embeddings_add_value`, or `kill` with reason code
  `real_gain_below_delta`. It also says to read `reason_code`, not the
  verdict name alone.
- **§14 D10** records this as a recommended default, which the owner may
  narrow to `embeddings_add_value` only. It is the recommendation for three
  reasons:
  - δ is the bar for building the success head, not for a learned action
    scorer.
  - Conditions 2 and 4 gate that scorer on their own.
  - Before v4, every interval with its lower bound above m was
    `embeddings_add_value`, so this keeps condition 3's meaning unchanged.
- **The same reading** is stated in spec §11 ("Why it matters beyond T8"),
  in `slice-2-t8.md` ("Reading the report", and Revision v4, which now says
  the meaning of `kill` changed for this consumer) and in `t8-t-interval.md`.
  The claim that the router was safe because the names were unchanged is
  corrected in both review files.

### F2: the nested baseline under the kill-first rule

**The rerun.** It is v3's learning-curve grid: synthetic replay through the
real arms (`_rows_and_content`, items = 0.7 n). It now has 20 seeds instead
of 3, two weaker signals (strength 0.25 and 0.5), and n up to 3200 (10 seeds
at 3200). For each cell it records:
- the v4 verdict;
- v3's verdict on the same data (percentile item bootstrap, B = 1000,
  lower bound checked first);
- the same pair for the nested comparison alone (`emb_ridge` against
  `tag_logistic`, the case the finding names), whatever e* is;
- the mean gain over all attempts and over the second half.

The script was scratch, not committed. Under v3's own 3 seeds and sizes it
reproduces v3's table cell for cell.

*Nested comparison, `emb_ridge` against `tag_logistic`: v4 add value / kill / undecided, with v3's kills in brackets (20 seeds; 10–12 at n = 3200):*

| Text signal | n = 53 | n = 100 | n = 200 | n = 400 | n = 800 | n = 1600 | n = 3200 |
|---|---|---|---|---|---|---|---|
| None (0) | 0/3/17 (4) | 0/3/17 (4) | 0/8/12 (7) | 0/9/11 (11) | 0/16/4 (16) | 0/20/0 (20) | 0/12/0 (12) |
| Very weak (0.25) | 0/4/16 (4) | 0/2/18 (2) | 0/4/16 (4) | 0/5/15 (5) | 0/9/11 (9) | 0/8/12 (7) | 1/4/6 (4) |
| Weaker (0.5) | 0/6/14 (6) | 2/1/17 (1) | 1/1/18 (1) | 5/1/14 (1) | 9/0/11 (0) | 19/0/1 (0) | 12/0/0 (0) |
| Weak (1) | 2/1/17 (0) | 5/0/15 (0) | 13/0/7 (0) | 20/0/0 (0) | 20/0/0 (0) | 20/0/0 (0) | 11/0/0 (0) |
| Strong (2) | 9/0/11 (0) | 19/0/1 (0) | 20/0/0 (0) | 20/0/0 (0) | 20/0/0 (0) | 20/0/0 (0) | 11/0/0 (0) |
| Very strong (4) | 15/0/5 (0) | 20/0/0 (0) | 20/0/0 (0) | 20/0/0 (0) | 20/0/0 (0) | 20/0/0 (0) | 11/0/0 (0) |

*Primary comparison, against e*: v4 add value / kill / undecided, with v3's kills in brackets (20 seeds; 10–12 at n = 3200):*

| Text signal | n = 53 | n = 100 | n = 200 | n = 400 | n = 800 | n = 1600 | n = 3200 |
|---|---|---|---|---|---|---|---|
| None (0) | 0/3/17 (3) | 0/4/16 (5) | 0/9/11 (8) | 0/13/7 (15) | 0/20/0 (20) | 0/20/0 (20) | 0/12/0 (12) |
| Very weak (0.25) | 0/1/19 (1) | 0/1/19 (1) | 0/9/11 (9) | 0/9/11 (9) | 0/12/8 (13) | 0/12/8 (12) | 0/7/4 (7) |
| Weaker (0.5) | 0/4/16 (4) | 1/0/19 (0) | 0/4/16 (4) | 0/2/18 (4) | 0/0/20 (0) | 11/0/9 (0) | 12/0/0 (0) |
| Weak (1) | 0/1/19 (1) | 0/0/20 (0) | 0/0/20 (0) | 11/0/9 (0) | 20/0/0 (0) | 20/0/0 (0) | 11/0/0 (0) |
| Strong (2) | 0/1/19 (1) | 4/0/16 (0) | 15/0/5 (0) | 20/0/0 (0) | 20/0/0 (0) | 20/0/0 (0) | 11/0/0 (0) |
| Very strong (4) | 4/0/16 (0) | 17/0/3 (0) | 20/0/0 (0) | 20/0/0 (0) | 20/0/0 (0) | 20/0/0 (0) | 11/0/0 (0) |

*Nested comparison, mean gain over all attempts → over the second half (nats per attempt):*

| Text signal | n = 53 | n = 100 | n = 200 | n = 400 | n = 800 | n = 1600 | n = 3200 |
|---|---|---|---|---|---|---|---|
| None (0) | −0.0016 → −0.0024 | −0.0019 → −0.0016 | −0.0041 → −0.0059 | −0.0054 → −0.0080 | −0.0064 → −0.0079 | −0.0062 → −0.0068 | −0.0045 → −0.0035 |
| Very weak (0.25) | −0.0016 → −0.0008 | −0.0009 → +0.0011 | −0.0024 → −0.0020 | −0.0018 → −0.0022 | −0.0014 → −0.0011 | +0.0001 → +0.0002 | +0.0015 → +0.0041 |
| Weaker (0.5) | −0.0008 → +0.0018 | +0.0038 → +0.0078 | +0.0040 → +0.0069 | +0.0076 → +0.0107 | +0.0104 → +0.0144 | +0.0149 → +0.0182 | +0.0183 → +0.0225 |
| Weak (1) | +0.0078 → +0.0157 | +0.0137 → +0.0218 | +0.0194 → +0.0275 | +0.0322 → +0.0433 | +0.0414 → +0.0531 | +0.0549 → +0.0647 | +0.0646 → +0.0729 |
| Strong (2) | +0.0207 → +0.0339 | +0.0331 → +0.0471 | +0.0415 → +0.0543 | +0.0632 → +0.0798 | +0.0853 → +0.1055 | +0.1133 → +0.1296 | +0.1387 → +0.1488 |
| Very strong (4) | +0.0335 → +0.0504 | +0.0424 → +0.0563 | +0.0557 → +0.0699 | +0.0809 → +0.0955 | +0.1079 → +0.1225 | +0.1467 → +0.1587 | +0.1799 → +0.1841 |

788 cells in all: 6 signal strengths, 7 sizes and up to 20 seeds each.

**Reading it:**
- **`real_gain_below_delta` never fired.** It fired in 0 of 788 cells, on
  the primary comparison and on the nested one. So the kill-first rule turned
  no real signal into a kill in this grid.
  - **Why:** an interval wholly inside (0, δ) must be narrower than δ =
    0.005. Among intervals whose lower bound was above 0, the smallest upper
    bound was 0.0122 (nested) and 0.0161 (primary).
  - **When it could fire:** the median nested width at n = 3200 is 0.009 for
    the 0.25 signal and 0.013 for the 0.5 signal. Width falls as 1/√n, so
    such an interval needs roughly 10⁴ or more attempts. The tracked fixture
    has 53.
- **Which verdicts v4 changed.** Against v3 on the same data:
  - on the primary comparison, v4 changed 13 of 788 verdicts: 6 kill → undecided,
    4 add value → undecided, 2 undecided → add value and 1 undecided → kill
    (a null);
  - on the nested comparison, it changed 16 of 788: 5 kill → undecided,
    7 add value → undecided and 4 undecided → kill.

  Every v4 kill is `upper_bound_below_delta`. Where v4 kills and v3 did not
  (4 nested cells, 3 of them with a real signal, and 1 null primary cell),
  the t interval's upper bound fell just under δ, between 0.0045 and 0.0049,
  where the percentile one did not. That is the interval method, not the
  rule order.
- **The dilution the finding describes is real, but it acts through
  `upper_bound_below_delta`, as it did in v3.**
  - **Weak signals.** At strengths 0.25 and 0.5 the realized nested gain
    starts at or below 0, while the embedding block learns. It rises with n.
    Averaged over seeds, the second-half mean is above the overall mean in 34
    of the 35 real-signal cells. Meanwhile, some seeds are killed because the
    upper bound is below δ:
    - the 0.5 signal: 6 of 20 at n = 53, then 1 of 20 at each n from 100 to
      400, and none from 800 on, where add value takes over (9 of 20 at 800,
      19 of 20 at 1600);
    - the 0.25 signal: 2 to 9 per cell at every n up to 3200, where the
      nested mean is only +0.0015 (+0.0041 over the second half).
  - **Not new.** v3 killed about as many (the bracketed counts). Across the
    656 real-signal cells, v3 made 66 primary and 44 nested kills, and v4
    makes 63 and 46. None of v4's comes from the rule order.
  - **Stronger signals.** From strength 1, no real signal is killed past
    n = 53. At n = 53 one seed in 20 is killed: on the nested comparison
    only by the t interval, and on the primary comparison by v3 as well.

**Fixed:**
- **A `real_gain_below_delta` kill is provisional.** The realized
  prequential gain includes the embedding block's learning period, so a real
  gain grows with data. The rule is to rerun when the data has grown; the
  kill is not terminal. This is stated in:
  - the frozen pre-registration (`decision_rule.real_gain_below_delta`);
  - the report's `decision_rule`, `kill_rule` and verdict reason;
  - spec §11;
  - `slice-2-t8.md`.
- **The grid** is recorded here.
- **Not changed:** an `upper_bound_below_delta` kill keeps its meaning. Its
  interval reaches m, so the data has not shown that embeddings help at all.
  Whether such kills should also be read as provisional is open question 2.

### F3: no self-contradiction at the δ boundary, and a numeric flip value

**Reproduced.** For [0.001, 0.0049996] the reason read "upper bound 0.005 <
δ = 0.005 … (it would be embeddings_add_value for any δ <= 0.005)".

**Fixed** (`field/success_head_analysis.py`):
- **Printed bounds.** Each bound in a reason prints at 4 significant figures,
  or with as many more as it takes for the printed number to satisfy the
  comparison the reason states. It now reads "upper bound 0.0049996 < δ =
  0.005".
- **The "δ <=" figure** is rounded down to 4 significant figures (0.004999),
  so "any δ <= it" stays true.
- **`flipping_delta`** is on every verdict (`verdict_flipping_delta` on each
  gated comparison). It is the interval's upper bound, or None without an
  interval. The verdict is `kill` exactly when δ > `flipping_delta`. At or
  below it, the verdict is `embeddings_add_value` if the lower bound is above
  m, otherwise `insufficient_data`. The report's `decision_rule` says so, and
  a test checks it by moving δ to each side of the value.
- **Boundary tests:** upper = δ is not a kill; lower = m is not
  `embeddings_add_value`; both at once is `undecided`.

### F4: one interval per comparison

**Reproduced.** In `test_the_primary_comparison_is_never_reported_with_a_second_interval`,
run against the reviewed source with e* = `tag_logistic`,
`emb_ridge_vs_tag_logistic` carried the percentile [−0.00094, 0.00942]. The
primary carried the t interval [−0.00089, 0.01085] for the same Δ.

**Fixed:**
- **`emb_ridge_vs_tag_logistic` always takes the cluster-robust t interval.**
  When e* is `tag_logistic` it equals the primary's interval exactly.
- **An unconditional rule.** I chose it over "only when e* is
  `tag_logistic`", so the method never depends on the data.
- **Unchanged:** the splits and the LLM comparisons stay percentile item
  bootstraps, labelled with their method, as the owner allowed.
- **The pre-registration** was updated to match:
  - `decision_interval.scope` now names this comparison;
  - `bootstrap.scope` now lists "the splits, the LLM comparisons, report 1
    and report 2";
  - this, with F2, is why the hash changed.

### F5: D9's margin, T8's own interval

**Fixed** (docs only):
- **Spec §11's constants** now say that T8 takes only D9's margin (0). Its
  interval is the registered t interval, not the bootstrap interval D9 names
  for the field's switching rule.
- **D9 in `spec_learner_field_v1.md`** carries the matching note.

### Claims corrected

- **"Verdict names are unchanged … the learned-router trigger reads them":**
  corrected in `t8-t-interval.md` and in `slice-2-t8.md` Revision v4 (F1).
- **"It matches R's qt to better than 1e-9":** checked against scipy's
  `t.ppf`:
  - better than 1e-13 at df ≤ 1000;
  - 2.2e-12 at 1e4, 1.9e-11 at 1e5 and 2.4e-10 at 1e6;
  - 2.5e-9 at 1e7 and 1.9e-8 at 1e8.

  The claim now reads "to better than 1e-9 up to df = 1e6". T8's df is
  items − 1.
- **"Every T8 report records δ … so the owner can monitor δ":** the flip value
  is now a field (F3). There is still no cross-run log (open question 3).

## Fakes run on the existing fixtures-local copy

**Setup:**
- **Command:** `learnloop eval success-head --vault fixtures-local/t8t-la-FAKES --legacy-fallback current_content`,
  first with `--dry-run`, then with `--output fixtures-local/reports/t8t-fakes-review`.
- **The copy:** the backup-API copy with stored noise vectors from the v4
  stage.
- **Calls:** replay only, so zero calls. The `state.sqlite` sha256 is
  identical before and after.

**Results:**

| | Value |
|---|---|
| Pre-registration | `t8-preregistration-v4`, hash `9f686a23…`, no deviations |
| Primary | e* `tag_logistic`; 53 attempts in 37 items; t interval [−0.005297, 0.0008547]; `kill` (`upper_bound_below_delta`); `flipping_delta` 0.0008547 |
| `emb_ridge_vs_tag_logistic` | `cluster_robust_t_cr1`, the same interval, and equal to the primary's `log_loss_gain` (F4). v3's percentile interval no longer appears |
| Gated `success_head` | `insufficient_data` (`undecided`), [−0.04634, 0.01311], `verdict_flipping_delta` 0.01311, `not_interpreted` |
| Method labels in the JSON | 6 `cluster_robust_t_cr1`, 12 `item_bootstrap_percentile` |

- **Report:** `fixtures-local/reports/t8t-fakes-review/t8-success-head-936fa75bdc86adf2.{json,md}`.
- **Leak check:** neither file contains any of the copy's 198 item ids or
  prompt texts.
- **The numbers carry no meaning:** they come from noise vectors.

## Real paid calls and cost

None: 0 Codex calls, 0 OpenRouter calls, $0. No external interface needed
checking, and Codex is exhausted until 2026-10-18.

## Gate

Run in this worktree at the fix commit `61953acd`. The commit for this file
changes docs only.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 12 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7788 passed**, 0 failed, 0 skipped (209 s); 7780 before, plus the 8 new tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **84 passed**, 7704 deselected (86 s) |
| Targeted (`test_success_head.py`, `test_success_head_cli.py`, `test_eval_harness.py`, `test_numeric.py`, `test_zero_data_llm.py`) | 143 passed |

- **`TMPDIR`.** As in the stage, both suite runs set `TMPDIR` to the
  worktree's gitignored `fixtures-local/tmp`, because `/tmp` is a shared
  16 GB tmpfs. The commands are otherwise as given.
- **A shared log file.** Another stage in this workflow wrote its own
  durability output into the same scratch log. The 84 / 7704 result above is
  this worktree's: it ended at this run's time, and `pytest -m durability
  --collect-only` here gives "84/7788 tests collected (7704 deselected)".
- **Not needed:** the frontend and the schema are unchanged, so neither the
  `npm` checks nor the DB reference scripts were run.

## Open questions

1. **Router D10.** Condition 3 is met by `embeddings_add_value` or by a
   `real_gain_below_delta` kill. That is the recommended default, so it is in
   force. The owner may narrow it to `embeddings_add_value` only.
2. **Kills of weak signals through `upper_bound_below_delta`.** A very weak
   real signal (strength 0.25 to 0.5 in the grid above) can be killed through
   `upper_bound_below_delta` while the embedding block is still learning. The realized gain is still at or below 0, though it would
   grow with data. That has been true since v3, and v4 does not change it.
   F2 marks only `real_gain_below_delta` as provisional, as the finding asked;
   an interval that reaches 0 has not shown that embeddings help at all.
   Should every kill be read as provisional and rerun when the data has
   grown? Or should the statistic weight later attempts, which would need a
   new pre-registration?
3. **A cross-run δ log.** Each report now has `flipping_delta` as a number,
   but there is still no ledger of (date, δ, interval, verdict) across runs.
   It can be built from the JSON reports' `analyses.t8.decision_rule` and
   `primary.verdict`. It was not built here (scope).
4. **The other descriptive intervals.** The splits and the LLM comparisons
   keep the percentile item bootstrap. It under-covers with few items, and the
   owner allowed it. Moving them to t is `t_interval=True` in
   `_comparison`. Report 1 and report 2 would need a harness option.

# T8 interval rule: Codex review fixes

**Stage:** `t8-interval-rule`, branch `fix/t8-interval-rule` (worktree
`learnanything-t8-interval`). The review covered the stage at `b503e526`
(Codex job `20261012-134326-g5v5ag`). This is offline research code only. It
has no serving, scheduling or projection effect, so no algorithm successor is
needed. There is no migration, no config knob and no frontend change.
`field/offline_llm.py` (router R0) is untouched. Nothing was merged or pushed.

## Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | Medium | T8 reports mix item and attempt bootstrap intervals | fixed | `4c45e8e0` | `test_every_interval_in_the_t8_report_resamples_items`, `test_the_item_unit_resamples_items_in_every_interval_and_the_manifest_says_so`, `test_t8_refuses_a_harness_that_resamples_attempts`, the CLI report test |
| F2 | Medium | The six-item cutoff relies on a bound for the wrong statistic | fixed | `4c45e8e0` | `test_five_items_with_a_clear_gain_are_decided`, `test_a_few_items_are_decided_by_their_interval_alone[2,3,5]`, `test_cluster_bootstrap_reports_no_interval_only_when_every_draw_is_the_same` |

No High findings.

### F1: one resampling unit for the whole T8 report

**Reproduced** with the stage's code, through the harness. The input was 60
attempts on three items, using T8's arms and analysis:
- `analyses.t8`: no interval ("3 clusters, fewer than 6").
- `report1`, resampled by attempt:
  - `emb_ridge` log loss: 95% interval [0.183, 0.534];
  - Brier: [0.047, 0.158];
  - the `emb_ridge`-vs-`mastery_ekf` comparison: [−0.079, 0.053].
- The manifest said `"unit": "attempt"`.

The v3 registration says every T8 interval, descriptive ones included,
resamples items. The registered descriptive metrics include "log loss, Brier,
AUC and reliability bins for every arm".

**Fix** (`field/evaluation.py`, additive):
- **New option.** `evaluate(..., bootstrap_unit="attempt" | "item")`, where
  `"attempt"` is the default. With `"item"`, every bootstrap interval the
  harness computes draws whole items:
  - report 1 log loss and Brier, overall and per split;
  - the comparisons against `mastery_ekf`, overall and first-unseen-LO;
  - report 2 miss rates;
  - the paired miss-rate improvement. Here a drawn item brings its later
    attempts under both policies.
- **Interval results** carry `clusters`.
- **The manifest** records the method:
  - `bootstrap.unit = "item"`;
  - `resample`: each drawn item brings all its scored attempts, and the
    statistic is the mean over the drawn attempts;
  - `scope`: every bootstrap interval in the report. The Wilson intervals are
    analytic, and the manifest says so.
- **`ReplayArrays.bootstrap_unit`** tells an analysis which unit the rest of
  the report used. The T8 analysis raises unless that unit is `"item"`, so a
  T8 report can never mix units. The T8 command passes
  `bootstrap_unit="item"`.
- **Pre-registration:** the `bootstrap` block gains `"scope": "every bootstrap
  interval in the T8 report"`.
- **Other reports are unchanged.** The attempt-unit learner-field and families
  digests still match those recorded on `d154f85e`, with and without an
  explicit `bootstrap_unit="attempt"`.

**Tests:**
- **The full-report regression the review asked for.**
  `test_every_interval_in_the_t8_report_resamples_items` runs the 60-attempt,
  three-item replay through `evaluate` with T8's arms and analysis. It walks
  every interval in the report and checks that each one carries an item
  count of 1–3. It also checks two intervals exactly against
  `paired_bootstrap(..., clusters=items)`: `emb_ridge`'s report 1 log loss
  and its comparison against the incumbent.
- **The harness test** checks the same things on a Spy stream with four
  rotating items, including report 2's miss rate and the miss improvement.
  It also checks the default manifest and that an unknown unit is rejected.
- **The CLI report test** checks the real command's manifest, and that every
  interval in its report carries an item count.

**Manual run.** The run used the existing fake-vector backup copy
`fixtures-local/t8i-la-FAKES`:
- **Dry run first.** It made 0 calls and printed the new hash.
- **The report:**
  - every interval carries an item count;
  - the manifest reads `unit: item`;
  - the verdict is unchanged: `kill`, 53 attempts in 37 items, interval
    [−0.00586, 0.00017].
- **Read-only.** The database's sha256 was the same before and after.
- **Leak check:** neither report file contains an item id or a prompt.
- **Files:** `fixtures-local/reports/t8i-fakes-review/t8-success-head-b5cfdbd9018a0333.{json,md}`.

### F2: no item minimum

**Reproduced** with five items, 100 attempts each, and gains of 0.10–0.14
nats over e*:
- the stage's code returned `insufficient_data`, with the reason "5 clusters,
  fewer than 6: no distribution-free 95% interval exists";
- enumerating all 5⁵ = 3125 item draws gives the percentile interval
  [0.108, 0.132].

The cutoff's derivation was wrong. The full range of G sample values misses a
population *median* with probability 2^(1−G). T8's statistic is an
attempt-weighted *mean*, so that calculation neither forbids an interval below
6 items nor guarantees coverage above 6.

**Fix.**
- **Removed.** `MIN_CLUSTERS`, `_min_clusters` and the pre-registration's
  `min_clusters` are gone.
- **Only the degenerate cases remain.** `_cluster_bootstrap` withholds an
  interval only where every resample gives the same mean: no attempts, one
  cluster, or cluster means within 1e-12 nats. The pre-registration's
  `no_interval` now says exactly that.
- **Result.** The five-item case decides `embeddings_add_value`, with an
  interval within 0.002 of the enumerated one (B = 1000).

**Why removal, not a registered minimum.** The review allowed either. The
owner removed v2's 100-attempt floor because it was hand-picked and nothing
derived it. A coverage-motivated item minimum would be another chosen
constant.

The synthetic coverage of the registered 95% percentile interval for a mean
also shows no natural threshold at 6 (2000 replications, B = 1000, one
attempt per cluster):

| Item clusters G | 2 | 3 | 4 | 5 | 6 | 8 | 12 | 20 | 37 |
|---|---|---|---|---|---|---|---|---|---|
| Normal item effects | 0.51 | 0.75 | 0.80 | 0.84 | 0.84 | 0.89 | 0.92 | 0.91 | 0.93 |
| Skewed (exponential) | 0.46 | 0.69 | 0.73 | 0.78 | 0.80 | 0.83 | 0.88 | 0.91 | 0.92 |

Under-coverage fades gradually up to about 20 items. Six items covered no
better than five, so the cutoff was not buying coverage. The report already
shows n and the item count next to every verdict. Whether to register an
explicit minimum is left to the owner (open question 1).

**What changes in behaviour:**
- **Few items decide from their interval.** Two, three and five items all
  favouring e* by 0.2 nats now give `kill` (parametrized test).
- **The CLI test vault** (seven attempts on three items, 20 resamples) now
  gets the interval [−0.173, −0.0001] and `kill`. The test asserts the
  verdict that the interval implies, not a fixed label.

**Tests replaced.** The tests that asserted the constant are gone:
`MIN_CLUSTERS == 6`, the 2^(1−G) arithmetic, and "five items give
`insufficient_data`, six give `kill`". The F2 scenario, the few-items cases
and the degenerate cases replace them. The degenerate cases are one cluster,
two clusters (an interval now exists), equal means and no attempts.

### The review's "claims that don't hold"

All three claims were corrected in the stage documents:
- "Every T8 interval uses the same item-cluster bootstrap" now holds (F1).
  `slice-2-t8.md` says it covers report 1, its comparisons and report 2.
- "Below 6 clusters, no distribution-free 95% interval exists" is withdrawn.
  The guard section of `t8-interval-rule.md` now explains why.
- "Not a decision floor" is withdrawn with the cutoff.

### Spec conformance notes

- **§11's original kill wording.** It still says an interval that includes 0
  means no value. v3 supersedes it for T8 (deviation 4 in `slice-2-t8.md`).
  The spec text was out of this stage's scope and is unchanged; it stays as
  open question 5 in `t8-interval-rule.md`.
- **The other rows** (replay purity, paid controls, migrations, config, R0)
  were assessed as conforming. This fix touches none of them.

## Pre-registration

- **Version:** still `t8-preregistration-v3`. Both amendments were made in
  review, before merge and before any owner-data run.
- **Hash:** `a2beed27c4ee19db039c55d112e732850c223c2e6cbb277ee6cbdd9278cc1372`,
  first staged as
  `e7a174f459e7613857e072a59d00c92b5dd495047e31f7bf01c9729117dc9976`.
- **Where it is updated:** `slice-2-t8.md`, `t8-interval-rule.md` and the
  hash test. The test asserts that the hash differs from both v2's and the
  first-staged v3's.

## Fail-first

**Reproduction script.** It ran against the stage's code (`b503e526`):
- F2: `insufficient_data` against the enumerated [0.108, 0.132];
- F1: the attempt-resampled report 1 intervals and the `"unit": "attempt"`
  manifest, quoted above.

**The new and revised tests on the unfixed code** (`test_eval_harness.py`,
`test_success_head.py`, `test_success_head_cli.py`): 28 failed and 57 passed.
- Most failures are the new `bootstrap_unit` keyword or `ReplayArrays` field.
- The assertion failures are in the F1 report walk, the F2 five-item case and
  the CLI manifest check.

After the fix, all 85 pass. With `test_zero_data_llm.py`, the targeted count
is 106 passed.

## Real paid calls and cost

None: 0 Codex calls, 0 OpenRouter calls, $0. Neither finding needed an
external interface check. The manual run is a cache-free replay of the
fake-vector copy, with zero calls.

## Gate

Run in this worktree at code commit `4c45e8e0`. The review-file commit
changes docs only.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 12 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7522 passed**, 0 failed, 0 skipped (226 s); the stage gate had 7515, and this fix adds 7 net tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **80 passed**, 7442 deselected (53 s) |
| T8 and harness tests (`test_eval_harness.py`, `test_success_head.py`, `test_success_head_cli.py`, `test_zero_data_llm.py`) | 106 passed |

- **`TMPDIR`.** As at the stage gate, both suite runs set `TMPDIR` to the
  worktree's gitignored `fixtures-local/tmp`, because the shared `/tmp`
  tmpfs is short of space. The commands are otherwise as given.
- **Not needed:** the frontend and the schema are unchanged, so neither the
  `npm` checks nor the DB reference scripts were run.

## Open questions for the owner

1. **An explicit item minimum?** None is registered now. The coverage table
   above shows the percentile interval under-covers with few items, for
   example about 75% at G = 3. Registering a minimum (say 12 or 20 items, a
   coverage policy) would be a new chosen constant, so it is left to the
   owner's checkpoint. Until then, n and the item count are shown next to
   every verdict.
2. **The recommendation block.** A T8 report's `recommendation` (the
   learner-field `review_challenger` rule) now reads item-resampled
   comparisons. It never activates anything, and the manifest states the
   unit. It is noted only because the same comparison can read differently
   in a learner-field report, which resamples attempts.

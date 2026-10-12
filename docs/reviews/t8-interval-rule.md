# T8 interval rule — pre-registration v3

**Checkpoint:** branch `fix/t8-interval-rule` (worktree
`learnanything-t8-interval`, base `main` at `d154f85e`). This changes offline
research code only. There is no serving, scheduling or projection effect, so
no algorithm successor is needed. There is no migration, no config knob and no
frontend change. Nothing was merged or pushed.

**Owner decision (2026-10-12).** Revise T8's pre-registered decision rule
(`docs/reviews/slice-2-t8.md`, then at v2):
- remove the fixed `min_common_attempts = 100`;
- decide from the 95% interval with a three-way rule;
- resample items, not attempts.

The rule had run only on fakes, never on owner data, so revising it is
legitimate. It is recorded as v3, the same way v1 became v2.

## What changed

### The rule (`field/success_head_analysis.py`, `field/success_head.py`)

The statistic is unchanged: Δᵢ = loss(e*)ᵢ − loss(`emb_ridge`)ᵢ on the common
attempts, where e* is the best explicit arm. The verdict now comes from the
95% item-cluster interval of its mean:

| Verdict | When |
|---|---|
| `embeddings_add_value` | lower bound > m = 0.0 (D9, unchanged) |
| `kill` | upper bound < δ = 0.005 nats per attempt |
| `insufficient_data` | otherwise: the interval reaches both m and δ |
| `insufficient_data` | no interval: fewer than 6 item clusters, cluster means within 1e-12 nats, or no common attempts. The reason is reported |

- **No attempt floor.** `min_common_attempts` is gone from the
  pre-registration.
- **δ** is the smallest gain worth building the success head for: T8's own
  "weak signal" scale, the 0.005 gain at block variance 0.25 in the v2
  synthetic table.
- **Rule order.** An interval that lies wholly inside (m, δ) is
  `embeddings_add_value`, because the lower-bound test comes first. Its reason
  says the gain is real but smaller than the smallest worth building (see open
  question 2).
- **Verdict names are unchanged.** The learned-router trigger
  (`spec_action_router_v1.md` §13) reads them.
- **The gate.** `success_head`, then `success_head+difficulty`, use the same
  three-way rule. Only `embeddings_add_value` opens the gate; `kill`,
  `insufficient_data` and an unavailable arm close it. Later comparisons are
  still computed and printed, labelled `not_interpreted`. Each gated result
  now carries `verdict_reason`.
- **The report.** The verdict JSON and the markdown preamble show n, the
  number of item clusters, the mean, the interval, m, δ, the verdict and its
  reason. Example from the fake-vector copy:

  > Primary: `emb_ridge` vs best explicit arm `tag_logistic`: n = 53 common
  > attempts in 37 item clusters.
  > Log-loss gain per attempt, loss(e*) − loss(`emb_ridge`): mean −0.002221;
  > 95% item-cluster interval [−0.00586, 0.0001702].
  > Rule: `embeddings_add_value` if the lower bound > m = 0.0; `kill` if the
  > upper bound < δ = 0.005; otherwise `insufficient_data`.
  > **Decision: kill**: upper bound 0.0001702 < δ = 0.005: any gain is smaller
  > than the smallest worth building.

- **Pre-registration:**
  - version `t8-preregistration-v3`;
  - hash `e7a174f459e7613857e072a59d00c92b5dd495047e31f7bf01c9729117dc9976`;
  - v2's hash was `746e4938a258896ac884aeaf95d544d3a148e26429a86b9307f83532a1e142ee`.

  Every report carries the new hash: the analysis block, the manifest's `t8`
  entry, the dry-run plan and the markdown preamble.

### The cluster bootstrap (`field/evaluation.py`, additive)

- **The option.** `paired_bootstrap(..., clusters=None)` is unchanged without
  `clusters`. With it, each of the B = 1000 draws (seed 0) takes G clusters
  with replacement, and each drawn cluster brings all its attempts. The
  statistic is the mean over the drawn attempts.
- **What it returns:** `n`, `clusters`, `mean`, `ci95` and `degenerate`.
  `ci95` is None, with the reason in `degenerate`, where no 95% interval can
  be computed.
- **Item labels.** `ReplayArrays` gains `item_clusters`: one opaque integer per
  scored row, in order of the item's first appearance. No item id is held, and
  nothing is exported. The field defaults to None, so other callers are
  untouched.
- **No silent fallback.** The T8 analysis refuses to run without item
  clusters rather than falling back to attempts.
- **Every T8 interval resamples items:** primary, gated and descriptive,
  including the `item_position` and `attempt_position` splits.
- **Other reports are byte-identical.** Only T8 passes `clusters`. A test pins
  the learner-field and families report digests, and one attempt-bootstrap
  result, to the values recorded on `d154f85e`.

### The no-interval guard: 6 item clusters, derived

The task named fewer than 2 clusters, or zero variance, as examples of an
interval that can't be computed. Building the rule showed one more case, and
the guard covers it with a derived bound, not a chosen one.

- **The case.** The CLI test vault has seven attempts on three items.
  - Under the bare rule, the percentile interval over those three items was
    wholly negative, [−0.173, −0.0001] (the test runs 20 resamples), and the
    verdict was `kill`.
  - This is exactly the small-sample false kill the owner wants removed.
  - A percentile interval over G clusters can never reach beyond the range of
    the G cluster means.
- **The bound.** Even that full range misses the cluster means' median with
  probability 2^(1−G): 25% at G = 3, 6.25% at G = 5 and 3.1% at G = 6. Below
  6 clusters, no distribution-free 95% interval exists, whatever the data.
- **In code:**
  - `MIN_CLUSTERS` is computed from the 95% level (`_min_clusters`);
  - the pre-registration records 6;
  - a test ties the two together.
- **Not a decision floor.** Six items with one attempt each can be decided.
  A test shows that six items all favouring e* give `kill`, while five give
  `insufficient_data`.
- **Numerical tolerance.** 1e-12 nats is the resolution for "zero variance":
  cluster means closer than that give the same mean on every resample.

## Why items are the cluster unit

- **The question is about new items.** The embedding is a function of the
  item's text. Repeated attempts on one item share that input and any
  item-specific residual the arms miss. Resampling items asks how the gain
  would vary over a different set of items, which is the §11 question
  ("success on never-seen items").
- **LOs give too few clusters.** The tracked fixture has 8 LOs, just above
  the 6-cluster bound, where percentile intervals are known to under-cover.
  On the fake-vector copy, the LO interval came out *narrower* than the item
  interval despite being the coarser unit, a symptom of exactly that.
- **Sessions cut across items.** Session-level dependence (fatigue, priming)
  is partly modelled by the recency and forgetting features. Two-way
  clustering (item × session) is out of scope.

**Are item clusters degenerate on real data? No.** On a backup-API copy of
the tracked `linear_algebra` fixture (`--legacy-fallback current_content`):

| | Count |
|---|---|
| Ability-scored attempts | 53 |
| Items | 37 (25 seen once; 9 twice; 2 three times; 1 four times) |
| LOs | 8 |

- **Plenty of clusters.** 37 is far above 6.
- **Small clusters.** Most clusters are singletons, so the item bootstrap
  stays close to the attempt bootstrap and only corrects for the 28 attempts
  on 12 repeated items. Singletons are valid clusters: a singleton cluster has
  no within-item correlation to correct for. A test shows that singleton
  clusters reproduce the attempt bootstrap exactly.
- **Widths on the fake-vector copy** (primary Δ; noise vectors, so only the
  widths mean anything):

| Unit | Clusters | 95% interval | Width |
|---|---|---|---|
| attempt (v2) | 53 | [−0.00477, −0.00019] | 0.00458 |
| item (v3) | 37 | [−0.00586, 0.00017] | 0.00603 (+32%) |
| LO | 8 | [−0.00555, −0.00021] | 0.00534 |

## Evidence (synthetic and fakes only)

**v2 and v3 on the same synthetic inputs** (the new tests' scenarios, run
through each version's analysis):

| Scenario | v2 | v3 |
|---|---|---|
| Large effect, n = 40 | `insufficient_data` (n < 100) | `embeddings_add_value` |
| Null, n = 150, noisy | `kill` | `insufficient_data` (interval [−0.014, 0.019]) |
| Null, n = 8000 | `kill` | `kill` (upper bound 0.0029 < δ) |
| Primary is a noisy null, n = 400 | `kill` | `insufficient_data`; gate closed |
| `success_head` is a noisy null | `kill`; next `not_interpreted` | `insufficient_data`; next `not_interpreted` |
| Five items, all favouring e* | `insufficient_data` (n < 100) | `insufficient_data` (no interval) |

**Learning curves under v3.** Synthetic replay through the real arms
(`_rows_and_content`, items = 0.7 n, three seeds, B = 1000):

| Text signal | n = 53 | n = 100 | n = 200 | n = 400 | n = 800 |
|---|---|---|---|---|---|
| None | 3 × insufficient | 1 kill, 2 insufficient | 3 × insufficient | 2 kill, 1 insufficient | 3 × kill |
| Weak (strength 1) | 3 × insufficient | 3 × insufficient | 3 × insufficient | 3 × add value | 3 × add value |
| Strong (2) | 3 × insufficient | 1 add value, 2 insufficient | 3 × add value | 3 × add value | 3 × add value |
| Very strong (4) | 3 × insufficient | 3 × add value | 3 × add value | 3 × add value | 3 × add value |

- **No false kills.** No weak or strong signal was killed at any n.
- **The null is killed only with data:** sometimes from 100 attempts, always
  by 800.
- **Small samples stay undecided:** every scenario is `insufficient_data` at
  n = 53.

**Fake-vector fixture copy.** This is a backup-API copy at
`fixtures-local/t8i-la-FAKES`:
- migrated with `doctor --fix-state`, which exits 1 only for the missing
  `rubrics/` directory;
- holding deterministic noise `item/stem` vectors for the 37 seen stems,
  stored directly. No calls were made.

The v3 report decides `kill` on 53 attempts. e* is `tag_logistic`, the nested
head without the embedding block, and noise vectors barely move `emb_ridge`
from it, so the interval is narrow. That is the right answer for noise, but
the numbers carry no meaning.
- **Report:** `fixtures-local/reports/t8i-fakes/t8-success-head-23ef5b2f95887a21.{json,md}`.
- **Leak check:** neither file contains an item id or prompt text.

**Do not reuse that copy for real runs:** it holds fake vectors under the
real model id.

## Tests (fakes only)

**Fail-first.** The new and revised tests were run against the base source
(`d154f85e`, `git archive` of `src/` and `migrations/`, via
`-o pythonpath`) before being run against this branch:

| File | On base | On this branch |
|---|---|---|
| `test_success_head.py` + `test_eval_harness.py` | 21 failed, 45 passed | all pass |
| `test_success_head_cli.py` | 1 failed (the v3 verdict and hash assertions), 11 passed | all pass |

The base-passing tests are the unchanged older ones. Some fail on base only
because the new `ReplayArrays` argument doesn't exist there. The meaningful
v2/v3 differences are in the scenario table above.

**What the tests cover:**
- **No attempt floor:** `test_a_large_effect_is_decided_with_fewer_than_100_attempts`.
- **A null waits for data:**
  `test_a_null_effect_is_undecided_until_the_upper_bound_falls_below_delta`.
  At 150 attempts the null is `insufficient_data` (upper bound ≥ δ); at 8000
  it is `kill` (upper bound < δ).
- **Interval wholly inside (m, δ):** `test_a_real_gain_below_delta_still_adds_value_and_says_so`.
- **Cluster width:**
  `test_cluster_bootstrap_is_at_least_as_wide_as_the_attempt_bootstrap_on_clustered_data`.
  With 30 items × 8 attempts it is more than twice as wide; singleton clusters
  reproduce the attempt bootstrap.
- **Other reports unchanged:**
  `test_the_cluster_option_leaves_every_other_report_byte_identical`. It pins
  golden digests recorded on base, and `clusters=None` equals the default.
- **The gate, for each verdict:**
  - `test_only_embeddings_add_value_opens_the_gate[add/kill/insufficient]`;
  - `test_each_secondary_verdict_gates_the_next_comparison[add/kill/insufficient]`.
- **No interval:**
  - `test_no_interval_is_insufficient_data_with_the_reason`: one item, five
    items vs six, zero variance and an arm that wasn't run;
  - `test_cluster_bootstrap_reports_no_interval_when_it_cannot_be_computed`.
- **The hash:** `test_preregistration_v3_changes_the_hash_and_every_report_carries_it`.
  The CLI test also checks the report's hash against the manifest.
- **What the report shows:** `test_the_report_shows_how_far_the_data_is_from_a_decision`.
- **Item clusters from the harness:**
  `test_the_harness_hands_item_clusters_and_t8_resamples_items`. The labels
  are opaque, in first-appearance order, and never exported.

## Real paid calls and cost

None: 0 Codex calls, 0 OpenRouter calls, $0. The task needed no external
interface check.

## Files touched

- `docs/reviews/slice-2-t8.md`:
  - "Revision v3", the frozen decision constants and the current hash;
  - the primary rule and the gate;
  - the v2 fakes row labelled as v2;
  - the owner commands and "Reading the report";
  - open question 6 ("Minimum data"), now resolved.
- `docs/reviews/t8-interval-rule.md` (this file).
- `src/learnloop/field/evaluation.py`: the `clusters` option,
  `ReplayArrays.item_clusters`, and `MIN_CLUSTERS` / `ZERO_SPREAD`.
- `src/learnloop/field/success_head.py`: `PREREGISTRATION` v3.
- `src/learnloop/field/success_head_analysis.py`: the three-way verdict, item
  clusters, the reasons and the report lines.
- `tests/test_success_head.py`, `tests/test_eval_harness.py`,
  `tests/test_success_head_cli.py`.

Not touched: `field/offline_llm.py` (router R0 is changing it), the CLI (its
help snapshot is unchanged), the spec text, config, migrations and the
frontend.

## Gate

Run in this worktree at code commit `06d857b9` (the review commit changes docs only).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 12 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7515 passed**, 0 failed, 0 skipped (202 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **80 passed**, 7435 deselected (56 s) |
| T8 and harness tests (`test_success_head.py`, `test_eval_harness.py`, `test_success_head_cli.py`, `test_zero_data_llm.py`) | 99 passed |

- **`TMPDIR`.** `/tmp` (a 16 GB tmpfs shared with other sessions) was full,
  so both suite runs set `TMPDIR` to the worktree's gitignored
  `fixtures-local/tmp`. The commands are otherwise as given.
- **Not needed:** the frontend and the schema are unchanged, so neither the
  `npm` checks nor the DB reference scripts were run.

## Open questions

1. **The 6-cluster guard.** It goes beyond the task's examples (fewer than 2
   clusters, zero variance), but it is derived from the 95% level, not
   chosen. Without it, 2–5 items could produce a `kill` from an interval that
   can't reach 95% coverage, as the three-item test vault did. Keep it?
2. **An interval wholly inside (0, δ).** By rule order this is
   `embeddings_add_value`, and the reason says the gain is real but below δ.
   The alternatives are to treat it as `kill` (not worth building) or as its
   own label, but the verdict names were to stay fixed. Is the current
   reading right?
3. **Few-cluster coverage.** Above 6 clusters, percentile cluster intervals
   still under-cover somewhat at small G (roughly below 20–30 clusters). The
   report shows G instead of adding another constant. Is that enough?
4. **The nested baseline narrows the interval.** When e* is `tag_logistic`,
   `emb_ridge` differs only by a shrunk embedding block, so Δ is small and the
   interval narrow. A decision can then come early: the fake-vector fixture
   was killed at 53 attempts. That is correct for noise, and no real signal
   was killed in the synthetic grid. But the interval measures the realized
   prequential gain, which includes the period when the embedding block is
   still learning.
5. **Spec §11 wording.** §11 still says that an interval including 0 means no
   value. v3 supersedes it for T8 (recorded under deviation 4 in
   `slice-2-t8.md`). Should the spec text be updated too?
6. **A minor pre-existing quirk.** A gated arm that was not run (for example
   a missing `success_head`) is labelled `interpreted` while the gate is
   open, although it has no verdict. It still closes the gate. Left as is.

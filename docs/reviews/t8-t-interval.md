# T8 t-interval rule: pre-registration v4

**Checkpoint:** branch `fix/t8-t-interval` (worktree `learnanything-t8-t`,
base `main` at `0583648d`).
- **Scope:** offline research code only. There is no serving, scheduling or
  projection effect, so no algorithm successor is needed.
- **Not changed:** no migration, no config knob or default, no frontend.
- **Not done:** nothing was merged or pushed. `field/offline_llm.py` was not
  touched (router R0 changes it next).

**Owner decisions (2026-10-12), in the owner's words:** "For T8: 1. Yes to a
t interval. 2. Yes you can "kill" but log it with our delta value so we can
monitor if delta needs changing in the future as a value."
- They answer open questions 2, 3 and 5 of `t8-interval-rule.md` (v3).

**Amended in review** (`t8-t-interval-codex-review.md`, before merge and
before any owner-data run). `emb_ridge_vs_tag_logistic` now takes the t
interval (F4), a `real_gain_below_delta` kill is provisional (F2), every
verdict carries a numeric `flipping_delta` and its reason never contradicts
the rule at the δ boundary (F3), and router §13 condition 3 reads the lower
bound (router D10, F1). The pre-registration hash changed to
`9f686a23048ea1403b233ee15983c83a93f38f0af75da219f31c53f1f087866b`. Where
this file disagrees with the review, the review wins.
- The rule had run only on fakes, never on owner data, so revising it is
  legitimate. It is recorded as v4 in `docs/reviews/slice-2-t8.md`, the same
  way v2 and v3 were.

## What changed

### The verdict interval (`field/evaluation.py`, `numeric.py`)

`cluster_t_interval(differences, clusters)` is new in the harness. It is
additive: only the T8 analysis calls it.

| Part | Definition |
|---|---|
| Estimate | the attempt-weighted mean Δ̄ of the per-attempt gain Δᵢ = loss(e*)ᵢ − loss(arm)ᵢ |
| Standard error | CR1 cluster-robust over items: se² = G/(G − 1) · Σ_g (Σ_{i∈g} (Δᵢ − Δ̄))² / n² |
| Critical value | Student t, G − 1 degrees of freedom, 95% (`numeric.student_t_quantile`) |
| Interval | Δ̄ ± t · se |
| No interval | only for degenerate inputs: no attempts, one item (df = 0), or item means within 1e-12 nats (zero variance). The reason goes in `degenerate` |

- **No minimum-cluster constant.** With few items, t widens on its own: t =
  12.7 at 2 items, 4.30 at 3, 2.57 at 6, 2.09 at 20.
- **Deterministic.** There is no resampling, so the verdict no longer depends
  on B or the seed. Those still drive the descriptive intervals and are still
  flagged as deviations.
- **Two sanity identities**, both tested:
  - With singleton items it is the ordinary one-sample t interval.
  - With equal-sized items it is the t interval on the item means.
- **The t quantile.** `student_t_quantile(p, df)` inverts the
  incomplete-beta identity P(|T| > t) = I_{df/(df+t²)}(df/2, ½) with the
  existing stdlib `beta_quantile`. It agrees with scipy's `t.ppf` to better
  than 1e-9 up to df = 1e6 (2.5e-9 at 1e7, 1.9e-8 at 1e8; corrected in
  review). T8's df is items − 1. scipy is not a declared dependency (it is
  only transitive), so it isn't used.
- **Output.** The result returns `n`, `clusters`, `mean`, `se`, `df`,
  `t_critical`, `ci95`, `degenerate` and `method = "cluster_robust_t_cr1"`.

### The rule (`field/success_head_analysis.py`)

δ is now checked first, so a real gain below δ is a kill:

| Verdict | Reason code | When |
|---|---|---|
| `kill` | `real_gain_below_delta` | upper bound < δ and lower bound > m: the whole interval is inside (0, δ) |
| `kill` | `upper_bound_below_delta` | upper bound < δ, lower bound ≤ m |
| `embeddings_add_value` | `lower_bound_above_margin` | otherwise, lower bound > m |
| `insufficient_data` | `undecided` | otherwise: the interval reaches both m and δ |
| `insufficient_data` | `no_interval` | no interval: degenerate input, or the arm not run |

- **Verdict names are unchanged, but `kill` now covers a real gain.** As
  first staged, this said the router was safe because the names were. That
  was wrong (review F1): the learned-router trigger
  (`spec_action_router_v1.md` §13, condition 3) asks whether embeddings add
  held-out value at all, and v3 called every such interval
  `embeddings_add_value`. Condition 3 now reads the lower bound:
  `embeddings_add_value` or a `real_gain_below_delta` kill (router D10).
- **The reason code is new.** It is `reason_code` on each verdict and
  `verdict_reason_code` on each gated comparison. The human `reason` stays.
- **The `real_gain_below_delta` reason names the δ that would have flipped
  it,** for example "it would be embeddings_add_value for any δ <= 0.003982".
  That is the number to watch if δ needs revisiting. (Review F3: that figure
  is now rounded down and the bounds printed with enough digits to read on
  the right side of δ, and the number is a field, `flipping_delta`.)
- **The gate is unchanged.** `success_head`, then `success_head+difficulty`,
  use the same rule and interval. Only `embeddings_add_value` opens the gate.
  A `real_gain_below_delta` kill closes it.

### δ is recorded in every report

The owner monitors whether δ itself needs changing. Every T8 report records
the δ in force, with m, n, the item count, the interval and its method.

**In the JSON:**
- **`analyses.t8.decision_rule`:** δ, m, the interval (method, level, unit,
  degrees of freedom) and the three-way rule.
- **`analyses.t8.primary.verdict`:**
  - the decision, `reason_code` and reason;
  - n, `item_clusters`, the mean, `se`, `df`, `t_critical` and `ci95`;
  - the method, m, δ and coverage.
- **Each gated comparison:** its `log_loss_gain` holds the t interval with
  its method, plus `verdict`, `verdict_reason_code` and `verdict_reason`.
- **`manifest.t8`:** `smallest_worthwhile_gain_nats_per_attempt`,
  `margin_nats_per_attempt` and `decision_interval`, next to the
  pre-registration hash.

**In the markdown preamble:** a "δ in force" line, then n and the item count,
the t interval (df, t, standard error), the rule, the decision with its
reason code, and the gated lines. From the fake-vector copy:

> - δ in force: 0.005 nats per attempt (m = 0.0); verdict interval:
>   `cluster_robust_t_cr1`, 95%, df = items - 1.
> - Primary: `emb_ridge` vs best explicit arm `tag_logistic`: n = 53 common
>   attempts in 37 item clusters.
> - Log-loss gain per attempt, loss(e*) − loss(`emb_ridge`): mean -0.002221;
>   95% cluster-robust t interval (CR1 over items, df = 36, t = 2.028)
>   [-0.005297, 0.0008547], standard error 0.001517.
> - **Decision: kill** (`upper_bound_below_delta`): upper bound 0.0008547 <
>   δ = 0.005: any gain is smaller than the smallest worth building; coverage
>   1.000 of ability-scored attempts.

### Which method each interval uses

- **Cluster-robust t (`cluster_robust_t_cr1`):** the primary comparison's
  `log_loss_gain` and verdict, and each gated comparison's `log_loss_gain`.
- **Percentile item bootstrap (`item_bootstrap_percentile`; B = 1000, seed
  0), descriptive only:**
  - the `item_position` and `attempt_position` splits;
  - `emb_ridge_vs_tag_logistic` and the LLM comparisons;
  - report 1 and report 2.

  The owner allowed these to stay.
- **Labels.** Every interval in the analysis carries `method`. Report 1 and
  report 2 are labelled by the manifest: for the item unit (T8 only), it gains
  `interval = "percentile_95"`, and its `scope` now says that an analysis's
  verdict intervals name their own method.
- **The v3 interval stays in the report as a side effect** (as first
  staged; removed in review F4). When e* is `tag_logistic`, the descriptive
  `emb_ridge_vs_tag_logistic` comparison is the primary comparison, so its
  bootstrap was exactly v3's interval. On the fakes copy it read [−0.00586,
  0.00017], next to v4's t interval. It now takes the t interval.

### Other reports are byte-identical

The golden digests recorded on `d154f85e` still hold:
- the learner-field report (`06818d9c…`, with and without
  `bootstrap_unit="attempt"`);
- the families report (`f2f30485…`);
- one attempt-bootstrap result.

The only harness-output change is the item-unit manifest, which only T8 uses.

### Pre-registration v4 (`field/success_head.py`)

- **Version:** `t8-preregistration-v4`, hash as first staged
  `6c7223178ce70c10b83364e356fc5bafea7e7c799c6bed8f60f213fa97717e18`
  (`9f686a23048ea1403b233ee15983c83a93f38f0af75da219f31c53f1f087866b` after
  review). v3 was
  `a2beed27c4ee19db039c55d112e732850c223c2e6cbb277ee6cbdd9278cc1372`.
- **New keys:**
  - `decision_interval`: method, unit, level, estimate, standard error,
    degrees of freedom and scope;
  - the reworded `decision_rule`;
  - `no_interval`: one item, rather than "every resample is the same";
  - `bootstrap.scope = "descriptive intervals only: …"`.
- **Unchanged:** m = 0.0, δ = 0.005, the arms, e*, the priors, the statistic,
  the coverage caveat, and B and the seed.
- **The record:** `docs/reviews/slice-2-t8.md`, "Revision v4", says what
  changed, why, and that no owner-data run happened under v3.

### Spec

`docs/specs/spec_embedding_consumers_v1.md` §11 said that an interval
including 0 at the margin means no added value. It now states the v4 rule:
- the statistic, and the CR1 t interval with items − 1 degrees of freedom;
- m and δ;
- the three verdicts, including `real_gain_below_delta`;
- that an interval including 0 is a kill only below δ;
- that every report records δ.

## Why CR1, not CR2

The task allowed CR2 if justified. For an intercept-only fit, CR2
(Bell–McCaffrey) has a closed form. Each item's squared residual sum is
weighted by 1/(1 − n_g/n) instead of CR1's common G/(G − 1).
- **Equal-sized items:** the two are identical.
- **Unequal sizes:** CR2 adds weight to the large items.

In the synthetic grid below, CR2 covered at most 0.008 better than CR1 (1–8
attempts per item, skewed effects). On the T8-shaped design (mostly
singletons) the difference was at most 0.004. CR1 is the owner's named choice and Stata's
standard factor, and that small gain doesn't justify the extra term. Open
question 2 has the details.

## Coverage evidence (synthetic only)

**Setup.** The true mean gain is 0, and each replication draws:
- a shared effect per item;
- per-attempt noise;
- an item size.

"Fixture" sizes copy the tracked `linear_algebra` fixture: 25 of 37 items
seen once, 9 twice, 2 three times, 1 four times. v3's interval is the
harness's own `paired_bootstrap(..., clusters=…)`, B = 1000.

**The test table** (`test_the_t_interval_covers_where_the_v3_percentile_item_bootstrap_does_not`):
400 replications, normal item effects (sd 0.1), attempt noise sd 0.1, fixture
sizes. It runs in about 6 s.

| Items | v3 percentile bootstrap | v4 cluster-robust t (CR1) |
|---|---|---|
| 3 | 0.720 | 0.938 |
| 6 | 0.863 | 0.940 |
| 20 | 0.923 | 0.945 |

The test asserts:
- t covers at least 0.92 at every item count;
- t covers at least as well as the percentile bootstrap at every item count;
- the percentile bootstrap covers below 0.80 at 3 items and below 0.90 at 6;
- the gap at 3 items is above 0.1.

**The full grid:** 2000 replications per cell (Monte Carlo sd about 0.005
at 0.95), B = 1000, a scratch script not committed.
- **Item effects:** normal (sd 0.1), or skewed (exponential with mean 0.1,
  centred).
- **Attempt noise:** sd 0.1.
- **CR2** is computed by its closed form and shown for comparison.

*T8-shaped item sizes (fixture), coverage (median width):*

| Items | Normal effects: v3 percentile | Normal: CR1 t | Normal: CR2 t | Skewed effects: v3 percentile | Skewed: CR1 t | Skewed: CR2 t |
|---|---|---|---|---|---|---|
| 2 | 0.499 (0.128) | 0.946 (1.518) | 0.947 | 0.492 (0.117) | 0.946 (1.355) | 0.949 |
| 3 | 0.753 (0.212) | 0.946 (0.522) | 0.946 | 0.724 (0.194) | 0.932 (0.474) | 0.933 |
| 4 | 0.789 (0.199) | 0.932 (0.359) | 0.935 | 0.789 (0.184) | 0.924 (0.337) | 0.928 |
| 5 | 0.827 (0.182) | 0.940 (0.283) | 0.944 | 0.805 (0.175) | 0.920 (0.272) | 0.924 |
| 6 | 0.856 (0.180) | 0.943 (0.254) | 0.946 | 0.845 (0.166) | 0.932 (0.234) | 0.934 |
| 8 | 0.897 (0.161) | 0.945 (0.206) | 0.947 | 0.878 (0.151) | 0.939 (0.193) | 0.940 |
| 12 | 0.908 (0.137) | 0.940 (0.161) | 0.942 | 0.908 (0.131) | 0.943 (0.154) | 0.943 |
| 20 | 0.920 (0.112) | 0.941 (0.123) | 0.943 | 0.913 (0.108) | 0.940 (0.118) | 0.942 |
| 37 | 0.934 (0.085) | 0.946 (0.090) | 0.946 | 0.927 (0.082) | 0.939 (0.087) | 0.941 |

*Other item sizes, coverage only (percentile / CR1 t / CR2 t):*

| Items | One attempt per item, normal | One per item, skewed | 1–8 attempts per item, normal | 1–8 per item, skewed |
|---|---|---|---|---|
| 2 | 0.498 / 0.950 / 0.950 | 0.502 / 0.952 / 0.952 | 0.509 / 0.945 / 0.948 | 0.482 / 0.927 / 0.935 |
| 3 | 0.750 / 0.947 / 0.947 | 0.729 / 0.951 / 0.951 | 0.759 / 0.929 / 0.935 | 0.706 / 0.911 / 0.915 |
| 4 | 0.803 / 0.949 / 0.949 | 0.795 / 0.959 / 0.959 | 0.796 / 0.930 / 0.933 | 0.764 / 0.907 / 0.914 |
| 5 | 0.850 / 0.956 / 0.956 | 0.832 / 0.948 / 0.948 | 0.823 / 0.925 / 0.931 | 0.795 / 0.898 / 0.900 |
| 6 | 0.862 / 0.960 / 0.960 | 0.851 / 0.949 / 0.949 | 0.850 / 0.928 / 0.932 | 0.827 / 0.907 / 0.911 |
| 8 | 0.891 / 0.952 / 0.952 | 0.893 / 0.957 / 0.957 | 0.884 / 0.941 / 0.945 | 0.845 / 0.902 / 0.907 |
| 12 | 0.916 / 0.953 / 0.953 | 0.906 / 0.949 / 0.949 | 0.899 / 0.934 / 0.939 | 0.881 / 0.917 / 0.920 |
| 20 | 0.929 / 0.951 / 0.951 | 0.926 / 0.954 / 0.954 | 0.916 / 0.939 / 0.941 | 0.894 / 0.916 / 0.917 |
| 37 | 0.940 / 0.955 / 0.955 | 0.935 / 0.951 / 0.951 | 0.939 / 0.950 / 0.950 | 0.917 / 0.931 / 0.931 |

**Reading it:**
- **The percentile bootstrap under-covers badly with few items:** about 0.50
  at 2 items, 0.71–0.76 at 3, 0.83–0.86 at 6 and 0.89–0.93 at 20. It nears
  nominal only around 37 items. This matches the v3 review's table.
- **CR1 t on T8-shaped data** (fixture sizes) covers 0.93–0.95 with normal
  effects and 0.92–0.95 with skewed effects, at every item count. With one
  attempt per item it is nominal.
- **Where CR1 falls short:** 0.90–0.93 with skewed item effects and 1–8
  attempts per item. That is the known small-G weakness of cluster-robust t
  with unequal clusters. It is still far closer to nominal than the
  percentile bootstrap (0.71 at 3 items).
- **CR2 vs CR1:** at most 0.008 apart anywhere in the grid, and at most 0.004
  on fixture sizes.
- **Width.** The t interval is wider where it has to be: at 3 items, about
  2.5× the percentile width (0.52 vs 0.21). It converges to the bootstrap's
  width as items grow (0.090 vs 0.085 at 37).

## Fakes run on a fixtures-local copy

**Setup.**
- **Copy:** a backup-API copy (`copy_tree_with_databases`) of this
  worktree's tracked `fixtures/linear_algebra`, at
  `fixtures-local/t8t-la-FAKES`.
- **Migration:** `doctor --fix-state`, which exits 1 only for the missing
  `rubrics/` directory.
- **Fakes:** deterministic noise `item/stem` vectors for the 37 seen stems,
  stored directly by a scratch script. They are seeded from the record id and
  content hash.
- **No calls.**

**Commands:**
- `learnloop eval success-head --vault fixtures-local/t8t-la-FAKES --legacy-fallback current_content --dry-run`:
  `t8-preregistration-v4`, 53 of 53 positive-mass attempts with a stem
  vector.
- The same command without `--dry-run`, with `--output fixtures-local/reports/t8t-fakes`.

| | v3 (stage `t8-interval-rule`) | v4 (this stage) |
|---|---|---|
| Attempts, items | 53, 37 | 53, 37 |
| e* | `tag_logistic` | `tag_logistic` |
| Mean gain | −0.002221 | −0.002221 (identical, so the noise vectors coincide) |
| Interval | percentile item bootstrap [−0.00586, 0.00017] | CR1 t, df = 36, t = 2.028: [−0.005297, 0.0008547], se 0.001517 |
| Verdict | `kill` | `kill` (`upper_bound_below_delta`) |
| `success_head` (gate closed) | — | `insufficient_data` (`undecided`), [−0.0463, 0.0131] |

- **Width.** At 37 items the t interval is about as wide as the bootstrap's
  (0.00615 vs 0.00603), so the verdict doesn't move. The numbers carry no
  meaning (noise vectors).
- **Report:** `fixtures-local/reports/t8t-fakes/t8-success-head-8101bfca149f4c5b.{json,md}`.
- **Leak check:** neither file contains any of the vault's item ids or
  prompt texts (198 strings checked).
- **Interval methods:** the JSON holds 4 `cluster_robust_t_cr1` and 13
  `item_bootstrap_percentile` labels.

## Tests (fakes only; written before the code)

**Fail-first evidence.**
- **Before any code change:**
  - `test_numeric.py`, `test_eval_harness.py` and `test_success_head.py` fail
    at collection with an ImportError: `student_t_quantile` and
    `cluster_t_interval` don't exist.
  - The CLI test fails because the 3-item verdict has no `df`. v3's verdict
    there was `kill`, on [−0.173, −0.0001].
- **With only the harness interval added and v3's analysis:** 13 T8 tests
  fail:
  - the kill-rule, large-effect and null-effect tests (no `reason_code`);
  - `real_gain_below_delta`;
  - the no-interval reasons;
  - five items, and three items no longer killed;
  - the report lines;
  - method labels and δ recorded;
  - bootstrap-independence;
  - the v4 hash;
  - the CLI.

**The required tests:**

| Requirement | Test |
|---|---|
| Coverage at 3, 6, 20 items vs v3's percentile interval | `test_eval_harness.py::test_the_t_interval_covers_where_the_v3_percentile_item_bootstrap_does_not` (table above) |
| The 3-item CLI vault no longer decides kill | `test_success_head_cli.py::test_report_runs_all_arms_read_only_and_aggregate_only`: df = 2, the interval reaches both 0 and δ, `insufficient_data` / `undecided`; the markdown shows δ and the t interval. Also `test_three_items_that_v3_killed_are_undecided_under_the_t_interval` (synthetic: v3's bootstrap stays below δ, t does not) |
| An interval inside (0, δ) is kill with that reason | `test_a_real_gain_below_delta_is_kill_with_its_reason`: primary and gated, the gate closes, and the reason names the flipping δ |
| δ is recorded | `test_delta_and_the_interval_are_recorded_in_every_report` (JSON `decision_rule`, verdict and gated fields, markdown lines); the CLI test checks `manifest.t8` |
| Other reports unchanged | `test_the_cluster_option_leaves_every_other_report_byte_identical` (golden digests, unchanged) |

The byte-identical test is a regression guard. It must pass both before and
after the change, so by construction it cannot fail first.

**Also added:**
- `test_cluster_t_interval_is_the_cr1_sandwich_with_items_minus_one_degrees_of_freedom`:
  a hand-computed sandwich.
- `test_cluster_t_interval_reduces_to_the_one_sample_t_interval`: the
  singleton and balanced identities.
- `test_cluster_t_interval_has_no_cluster_minimum_only_degenerate_guards`.
- `test_the_verdict_interval_does_not_depend_on_bootstrap_settings`.
- `test_every_interval_in_the_t8_report_clusters_items_and_names_its_method`.
- `test_student_t_quantile_matches_tables` (df 1, 2, 3, 5, 19, 36, 1000) and
  `test_student_t_quantile_approaches_the_normal_and_rejects_bad_inputs`.

**Updated for v4:**
- the kill-rule, null-effect, no-interval and five-item tests;
- the report-lines and hash tests;
- the few-items test: a 0.2-nat loss still kills at 2, 3 and 5 items, now
  under t.

## Real paid calls and cost

None: 0 Codex calls, 0 OpenRouter calls, $0. No external interface needed
checking, and the fakes run used stored noise vectors. Codex is exhausted
until 2026-10-18, so no Codex review ran in this stage.

## Files touched

- `src/learnloop/numeric.py`: `student_t_quantile`.
- `src/learnloop/field/evaluation.py`: `cluster_t_interval` and
  `CLUSTER_T_METHOD`. The item-unit bootstrap manifest gains `interval` and a
  reworded `scope`.
- `src/learnloop/field/success_head.py`: `PREREGISTRATION` v4.
- `src/learnloop/field/success_head_analysis.py`:
  - the t interval for the decided comparisons;
  - the v4 rule with reason codes;
  - `decision_rule`;
  - method labels;
  - the markdown lines.
- `src/learnloop/cli/success_head.py`: δ, m and the interval method in
  `manifest.t8`. The help text is unchanged.
- Tests: `tests/test_numeric.py`, `tests/test_eval_harness.py`,
  `tests/test_success_head.py` and `tests/test_success_head_cli.py`.
- Docs:
  - `docs/reviews/slice-2-t8.md`: Revision v4, the constants table, the
    primary rule, the interval scope, "Reading the report", the owner-command
    hash, deviation 4, open question 6 and the fakes run under v4;
  - `docs/reviews/t8-interval-rule.md`: a "superseded in part" note;
  - `docs/specs/spec_embedding_consumers_v1.md` §11;
  - this file.

Not touched: `field/offline_llm.py`, config defaults, migrations, schema and
the frontend.

## Gate

Run in this worktree at code commit `1ff2c89d`. The docs commit after it
changes no code.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 12 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7780 passed**, 0 failed, 0 skipped (176 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **84 passed**, 7696 deselected (74 s) |
| Targeted (`test_success_head.py`, `test_eval_harness.py`, `test_success_head_cli.py`, `test_zero_data_llm.py`, `test_numeric.py`) | 135 passed |

- **`TMPDIR`.** `/tmp` is a 16 GB tmpfs shared with other sessions, and it
  had filled up during the previous T8 stage. Both suite runs therefore set
  `TMPDIR` to the worktree's gitignored `fixtures-local/tmp`. The commands
  are otherwise as given.
- **Not needed:** the frontend and the schema are unchanged, so neither the
  `npm` checks nor the DB reference scripts were run.

## Open questions

1. **Descriptive intervals.** The splits and the descriptive comparisons
   (`emb_ridge_vs_tag_logistic`, the LLM arms) keep the percentile item
   bootstrap, as allowed, labelled `item_bootstrap_percentile`. That interval
   under-covers with few items (the table above), so a small split can look
   more certain than it is.
   - Moving the analysis's descriptive comparisons to the t interval is a
     one-line change (`decides=True`).
   - Report 1 and report 2 would need a harness option.

   Should the T8 report use one method throughout?
2. **CR1's small-G shortfall.** With skewed item effects and very unequal
   item sizes, CR1 covers about 0.90–0.93 rather than 0.95 (grid above).
   - CR2 recovers at most 0.008.
   - A Bell–McCaffrey degrees-of-freedom correction would recover more, but
     it is another moving part.

   The owner's real data is mostly singleton items (fixture sizes), where CR1
   covers 0.92–0.95. No change is registered.
3. **Monitoring δ across runs.** Each report records δ, the interval and, for
   a `real_gain_below_delta` kill, the δ at which it would flip. Reports are
   files in the owner's chosen `--output` directory; there is no cross-run
   ledger of verdicts. If the owner wants a running log of (date, δ, interval,
   verdict), it could be built later from the JSON reports'
   `analyses.t8.decision_rule` and `primary.verdict`. It was not built here.
4. **Carried over from v3, unchanged:**
   - the nested-baseline narrowing (v3 open question 4);
   - a gated arm that was not run is labelled `interpreted` while the gate
     is open (v3 open question 6).

# Slice 2 T8 — learner success head (offline research)

**Checkpoint:** built on `slice-2/t8` (worktree `learnanything-t8`, base
`main` at `974c5647`). Offline research only: no live consumer, no serving
change, no activation, no merge or push. The report generates with fakes on a
fixtures-local copy. The owner runs it for real with the commands below, dry
run first.

Spec: `docs/specs/spec_embedding_consumers_v1.md` §11 (with §1 R1–R6, §4, §13),
`docs/specs/spec_learner_field_v1.md` §7.2 (the `learnloop eval` harness) and
`docs/specs/implementation_handoffs.md` §0. The prerequisite "previous track's
report reviewed" is waived (owner, 2026-10-12; `implementation_goal.md` §1a):
tracks are built in parallel and report gates are post-hoc.

## Plan

### Files

- **Add `src/learnloop/field/success_head.py`** (pure; joins the
  `field-predictors-are-pure` import contract). It holds:
  - the frozen per-attempt content index type (item-side content only: the
    stem text the learner saw, KC names, MRL-truncated vectors);
  - one prequential Bayesian logistic head, refit by Newton (MAP) on all past
    observations after each outcome, with fixed a-priori Gaussian priors per
    feature block;
  - its arms `tag_logistic`, `emb_ridge`, `success_head` and
    `success_head+difficulty`;
  - the frozen pre-registration constants;
  - the T8 analysis (kill rule plus the gated and descriptive comparisons).
- **Add `src/learnloop/field/zero_data_llm.py`:** the zero-data LLM probability
  arm (§11 note, 2610.11135) with:
  - a past-only request builder;
  - a cached arm (raw, plus a one-parameter recalibrated arm);
  - spend-capped preparation that writes `judgment_ledger` verdicts and
    model-call receipts, with a cache outside the vault.
- **Add `src/learnloop/field/item_content.py`:** a read-only loader that
  builds the content index from one snapshot.
  - **Text by revision:** `exact` rows use the graded snapshot's prompt;
    `reconstructed_current` rows use the current prompt; `excluded` rows get
    no text.
  - **Vectors:** stored `item/stem` vectors (and `item/skeleton` vectors once
    PF-b registers that recipe), matched by the recipe content hash of that
    exact text. A changed prompt with no vector for the text actually seen
    makes the arm abstain; the current text's vector is never substituted.
- **Add `src/learnloop/cli/success_head.py`:** `learnloop eval success-head`,
  registered on the existing `eval` group beside `families`. It offers:
  - `--dry-run` (plan only: coverage plus the LLM spend estimate);
  - `--llm-cache` / `--prepare-llm` and the spend caps;
  - `--legacy-fallback`, bootstrap and seed options.
  Reports are aggregates only and content-addressed.
- **Small, additive harness changes in `field/evaluation.py`:**
  - an attempt arm may abstain through an optional `covers(features)`;
  - a new `item_position` split (first attempt on a never-seen item vs a
    repeat);
  - an optional `analyses` hook, which receives in-memory arrays and returns
    aggregates;
  - `write_reports` takes optional leading markdown lines.
- **Add `EmbeddingRecipe.content_hash`**, identical to the method Phase 5b adds
  on `slice-a/phase-5b`, so the merge is clean.
- **Tests:** `tests/test_success_head.py`, `tests/test_zero_data_llm.py`,
  `tests/test_success_head_cli.py`.

### Migrations, successors, kill switches

- **Migrations:** none. Vectors, judgments and receipts use existing tables.
- **Successors and kill switches:** none. Nothing is served or activated:
  - every T8 arm reports `calibrated_uncertainty = False` (G11);
  - nothing reads T8 output outside the report.

### Spend and routes

- **Embedding arms make no calls.** They read vectors already stored by
  `learnloop embeddings backfill` (owner-run, spend-capped, its own
  `--dry-run`).
- **The zero-data LLM arm is the only paid step.** It is explicit and off by
  default:
  - **gates:** `field.enabled`, `field.llm_probability_enabled` and the explicit
    route `ai.routing.field_llm_probability`. This is the existing offline
    probability route: it never falls back to a chat provider, and
    `LEARNLOOP_AI_PROVIDER` doesn't override it;
  - **spend controls:** the Phase 1 framework (caps, `--dry-run` estimate).
    Codex runs on the subscription with `estimated_only` cost (Slice A plan §5
    rule 6). A metered route keeps the physical-request bound, and an unknown
    price fails closed.

### `judgment_ledger`

- **Zero-data arm:** one append per paid prediction, with:
  - task `t8_zero_data_probability`;
  - judge `llm`;
  - `left_kind` `offline_prediction`;
  - the input hash.
- **Embedding arms:** no writes.

### Tests (fakes only)

Each of these has a test:
- **Prediction boundary:** no outcome or future content crosses it. Adding
  vectors for future attempts leaves every prediction byte-identical.
- **Replay makes zero calls:** forbidden client, socket and SQLite connect.
- **No LLM-labelled difficulty in T8 arms:**
  - the internal ability filter runs with `b` neutralized;
  - the difficulty arm abstains unless `difficulty_source == "solver_panel"`.
- **Determinism.**
- **Prequential fit:** Newton MAP equals a direct optimizer on synthetic data.
- **Moderation:** it widens toward 0.5 off-support.
- **Revision-exact vector matching:** a changed prompt abstains.
- **Kill-rule arithmetic.**
- **LLM arm:** cache outside the vault, dry run is read-only, caps block before
  the client, ledger and receipts, Codex `estimated_only`, missing cache fails
  closed.
- **CLI end to end:** read-only, and aggregates without item text or ids.

## Pre-registration (fixed 2026-10-12, before any run)

Recorded here before any report run. It is also frozen in code as
`success_head.PREREGISTRATION`, and its hash goes into every report's
manifest. A run that changes the bootstrap settings is flagged as a deviation
in the report.

**Current version: `t8-preregistration-v4`**, hash
`9f686a23048ea1403b233ee15983c83a93f38f0af75da219f31c53f1f087866b`. Three
revisions were made, all before any run on owner data: v2 (the embedding
prior), v3 (the decision rule) and v4 (the verdict interval, and a real gain
below δ). Each is recorded below. v3 was amended in its Codex review before
merge (no item minimum; items resampled in every interval of the report),
which changed its hash; see `docs/reviews/t8-interval-rule-codex-review.md`.
v4 is recorded in `docs/reviews/t8-t-interval.md`, and was amended in its own
review before merge, which changed its hash too; see
`docs/reviews/t8-t-interval-codex-review.md`.

**Question (§11).** For this one learner, does a frozen-embedding predictor of
success add held-out predictive value over explicit learner-state predictors?

**Data.**
- **Rows:** the canonical outcome view (`field.outcomes`), replayed
  prequentially by the shared harness. Every arm predicts each attempt before
  any arm sees its outcome.
- **Revision policy:** the vault's `field.legacy_fallback`, or the explicit
  `--legacy-fallback`. The owner chooses it before running, and the report
  records it.
- **Scored rows:** ability-scored attempts (positive effective mass, or
  hint-replaceable), the same rows as report 1.
- **Coverage:** an embedding arm scores only attempts whose exact seen text has
  a stored vector for the configured model.

**Arms.**
- **Explicit set E** (fixed):
  - `base_rate_lo`;
  - `mastery_ekf` (incumbent);
  - `lo_general`;
  - `tag_logistic`, §11's "tags + base-rate + forgetting logistic": the same
    head and features as `emb_ridge`, minus the embedding block.
- **Primary:** `emb_ridge`, the MAP of the head with the embedding block
  added.
- **Gated:**
  - `success_head`: the same fit with a Laplace-moderated predictive (the §11
    model, in its "Bayesian logistic" form);
  - `success_head+difficulty`: adds the solver-panel difficulty prior. It
    scores only items with `difficulty_source = "solver_panel"`, and is
    reported as `unavailable` when there are none.
- **Descriptive:** `llm_zero_data` (raw) and `llm_zero_data:recalibrated`.

**Fixed constants** (a priori and versioned; never fitted to the owner, field F5).

*Embedding view:*
- the first 32 MRL dimensions of the stored vector, L2-normalized;
- centred on the mean of previously observed attempts' vectors (past only);
- renormalized to unit length.

*Feature blocks and Gaussian priors:*

| Block | Feature | Prior mean | Prior variance |
|---|---|---|---|
| Bias | constant | 0 | 1.0 |
| Ability | logit of a difficulty-neutral (`b = 0`) incumbent EKF | 1 | 0.25 |
| Base rate | logit of the LO's running Beta(1, 1) rate | 0 | 0.25 |
| Practice | log(1 + prior LO attempts) | 0 | 0.25 |
| Forgetting | log(1 + days since the LO); log(1 + days since the item) | 0 | 0.25 each |
| Item history | seen-item flag; last item outcome − 0.5 | 0 | 0.25 each |
| Recency | 1-day half-life recency of all outcomes, shrunk | 0 | 0.25 |
| Flags | primed; warm | 0 | 0.25 each |
| Tags | one-hot LO, capability and variant relation | 0 | 0.25 each |
| Embedding | each stem (and skeleton) dimension | 0 | 0.25 (revision v2; was 1.0) |
| Difficulty | solver-panel `b` | −1 | 0.25 |

*Fitting:*
- observations are weighted by effective mass;
- moderation is MacKay's probit approximation.

*LLM arm:*
- the history window is 25 graded interactions;
- stems are capped at 6000 characters;
- recalibration is a one-parameter logit intercept, MAP under N(0, 1) on past
  predictions only.

*Decision rule (revision v4):*

| Constant | Value |
|---|---|
| Margin m (D9) | 0.0 nats per attempt |
| Smallest worthwhile gain δ | 0.005 nats per attempt, recorded in every report |
| Verdict interval | cluster-robust t over **items**, 95%: the attempt-weighted mean gain ± t(0.975, items − 1) × its CR1 standard error |
| Descriptive intervals | paired percentile item bootstrap, 95%, B = 1000, seed 0 (each drawn item brings all its attempts). Exception: `emb_ridge_vs_tag_logistic` takes the verdict interval, since it is the primary comparison itself whenever e* is `tag_logistic` |
| No interval | no common attempts, one item cluster, or cluster means within 1e-12 nats of each other. There is no minimum item count |
| Coverage caveat | below 80% of ability-scored attempts |

There is no minimum number of attempts or items.

**Revision v2 (2026-10-12, before any run on owner data).**
- **The change:** the embedding block's prior variance per dimension drops
  from 1.0 to 0.25. With unit-norm features, that bounds the block's a-priori
  logit spread at sd 0.5 instead of 1.
- **Why:**
  - Text barely predicts item difficulty (R2: BEA'24, 0.299 vs 0.311 for a
    dummy), so a block sd of 0.5 is still a generous prior.
  - At sd 1, 32 dimensions overfit at n ≈ 600. A synthetic-only check (three
    seeds; no owner data) showed:

    | Signal | Block variance 1.0 | Block variance 0.25 |
    |---|---|---|
    | None | costs 0.025 nats per attempt vs `tag_logistic` | costs 0.007 |
    | Weak | worse than `tag_logistic` | gains 0.005 |
    | Strong | gains 0.047 | gains 0.038 |

- **What else changed:** nothing else. The version is now
  `t8-preregistration-v2`.

**Revision v3 (owner decision, 2026-10-12, before any run on owner data).**
- **No run happened under v2.** The v2 rule ran only on fakes (the synthetic
  tests and the fake-vector fixtures-local copy below). No owner-data report
  exists under v2 or v1, so changing the rule now cannot be fitted to a result.
- **What changed:**
  - **The fixed minimum is gone.** v2 answered `insufficient_data` below 100
    common attempts and decided above it. v3 has no floor: the verdict comes
    from the 95% interval alone.
  - **A three-way rule.** `embeddings_add_value` if the interval's lower bound
    is above m = 0.0; `kill` only if its upper bound is below δ = 0.005 nats
    per attempt; otherwise `insufficient_data`. Under v2, any interval
    reaching m was a kill.
  - **An item-cluster bootstrap.** Each resample draws items, and each drawn
    item brings all its attempts. v2 resampled single attempts.
  - **No-interval guard.** Where every resample gives the same mean (no
    common attempts, one item cluster, or numerically equal cluster means),
    there is no interval; the verdict is `insufficient_data` and the report
    says why. There is no minimum item count (review F2).
  - **The report** shows n, the number of item clusters, the interval, m, δ,
    the verdict and its reason.
- **Why** (owner, 2026-10-12):
  - The 100-attempt floor was hand-picked: the spec doesn't set it and nothing
    derives it.
  - A floor turns small samples above it into false kills: at 150 attempts a
    wide interval that merely reaches 0 was a v2 `kill`.
  - Attempts cluster by item, LO and session, so resampling single attempts
    understates the uncertainty.
- **Where the constants come from:**
  - **δ = 0.005 nats per attempt** is the smallest gain worth building the
    success head for: T8's own "weak signal" scale (the gain at block variance
    0.25 in the v2 table above).
  - **m = 0.0** is unchanged (D9).
  - **No item minimum.** The stage first added a 6-item cutoff, justified by
    a sample-range bound for a population *median*. T8's statistic is an
    attempt-weighted *mean*, so that bound neither forbids an interval below
    6 items nor guarantees coverage above it. Review F2 removed the cutoff.
    Percentile intervals still under-cover with few items, so the report
    shows the item count (see `t8-interval-rule-codex-review.md`).
  - **1e-12 nats** is numerical resolution: cluster means closer than that are
    equal, and every resample gives the same mean.
- **Why items are the cluster unit:** see `docs/reviews/t8-interval-rule.md`.
  In short, the embedding is a function of the item's text, and the §11
  question is about new items. LOs give too few clusters (8 on the tracked
  fixture). Sessions cut across items.
- **Unchanged:** the verdict names (the learned-router trigger in
  `spec_action_router_v1.md` §13 reads them), the arms, e*, the priors, B,
  the seed and the coverage caveat.
- **Version:** `t8-preregistration-v3`, hash
  `a2beed27c4ee19db039c55d112e732850c223c2e6cbb277ee6cbdd9278cc1372` (as amended in review; first staged as
  `e7a174f459e7613857e072a59d00c92b5dd495047e31f7bf01c9729117dc9976`; v2 was
  `746e4938a258896ac884aeaf95d544d3a148e26429a86b9307f83532a1e142ee`).

**Revision v4 (owner decision, 2026-10-12, before any run on owner data).**
- **No run happened under v3.** v3 merged to `main` and ran only on fakes:
  the synthetic tests and the fake-vector `fixtures-local` copies. No
  owner-data report exists under v3, v2 or v1, so the change cannot be fitted
  to a result.
- **What changed:**
  - **A cluster-robust t interval decides.** It replaces the percentile item
    bootstrap for the verdict intervals: the primary `emb_ridge` comparison
    and the gated secondaries.
    - *Estimate:* the attempt-weighted mean of Δᵢ = loss(e*)ᵢ −
      loss(arm)ᵢ, as before.
    - *Standard error:* the cluster-robust sandwich over items with the CR1
      small-sample factor, se² = G/(G − 1) · Σ_g (Σ_{i∈g} (Δᵢ − Δ̄))² / n².
    - *Critical value:* Student t with G − 1 degrees of freedom (G items),
      95%.
  - **No interval only for degenerate inputs:** no common attempts, one item
    (no degrees of freedom), or zero variance across items. The verdict is
    then `insufficient_data` with the reason. There is still no item minimum.
  - **A real gain below δ is `kill`.** An interval wholly inside (m, δ) is
    `kill` with reason code `real_gain_below_delta`. Under v3 it was
    `embeddings_add_value`. The rule now checks δ first: `kill` if the upper
    bound is below δ; otherwise `embeddings_add_value` if the lower bound is
    above m; otherwise `insufficient_data`.
  - **δ is recorded.** Every report records δ, m, n, the item count, the
    interval and its method, in the JSON (`analyses.t8.decision_rule`, each
    verdict, `manifest.t8`) and the markdown preamble. The owner monitors
    whether δ itself needs changing. A `real_gain_below_delta` reason also
    names the largest δ at which the verdict would have been
    `embeddings_add_value`.
  - **The bootstrap stays descriptive.** The splits, the descriptive
    comparisons, report 1 and report 2 keep the percentile item bootstrap.
    Every interval in the analysis names its `method`
    (`cluster_robust_t_cr1` or `item_bootstrap_percentile`).
- **Why** (owner, 2026-10-12):
  - **Coverage with few items.** Percentile cluster intervals under-cover
    with few items: about 75% at 3 items and 86% at 6 on T8-shaped synthetic
    data. Because t has G − 1 degrees of freedom, it widens on its own as
    items run out (about 95% at 3 items), with no minimum-cluster constant.
    See `t8-t-interval.md` for the coverage table.
  - **A gain too small to build on is not worth building**, however
    certain. The owner wants to see such kills, logged with the δ in force.
- **CR1, not CR2.** CR1 is Stata's standard factor and the owner's named
  choice. For the intercept-only fit, CR2 (Bell–McCaffrey) weights each
  item's squared residual sum by 1/(1 − n_g/n) instead of G/(G − 1). The two
  are identical for equal-sized items, and their coverage differed by at most
  0.008 in the synthetic grid (`t8-t-interval.md`). So CR2 doesn't justify the
  extra term.
- **The verdict names are unchanged, but `kill` means more.** It now also
  covers a real gain below δ, which v3 called `embeddings_add_value`. That
  changes what the name means to a downstream consumer: the learned-router
  trigger (`spec_action_router_v1.md` §13, condition 3) asks whether
  embeddings add held-out predictive value at all, and δ is the bar for the
  success head only. Condition 3 therefore reads the lower bound: it is met by
  `embeddings_add_value` or by a `real_gain_below_delta` kill (router D10, a
  recommended default the owner may narrow). A consumer must read
  `reason_code`, not the verdict name alone (review F1).
- **Unchanged:** m, δ, the arms, e*, the priors, the statistic, the gate, the
  coverage caveat, and B and the seed for the descriptive intervals.
- **Amended in review** (`t8-t-interval-codex-review.md`, before merge and
  before any owner-data run):
  - **`emb_ridge_vs_tag_logistic` takes the t interval** (F4). Whenever e* is
    `tag_logistic` it is the primary comparison itself, so the report
    carried the same Δ with two intervals, and the percentile one is
    narrower. It now always uses the verdict's interval. The splits and the
    LLM comparisons stay percentile item bootstraps.
  - **A `real_gain_below_delta` kill is provisional** (F2). The realized
    prequential gain includes the period in which the embedding block is
    still learning, so a real gain grows with data: rerun when the data has
    grown; such a kill is not terminal. The synthetic nested-baseline grid
    was rerun under v4 (see the review).
  - **The δ at which the verdict changes is a field** (F3):
    `flipping_delta`, the upper bound, on every verdict
    (`verdict_flipping_delta` on each gated comparison). The verdict is
    `kill` exactly when δ > `flipping_delta`. The reason prints each bound
    with enough digits to sit on the side of m or δ that the rule says.
- **Version:** `t8-preregistration-v4`, hash
  `9f686a23048ea1403b233ee15983c83a93f38f0af75da219f31c53f1f087866b` as amended in review (first staged as
  `6c7223178ce70c10b83364e356fc5bafea7e7c799c6bed8f60f213fa97717e18`; v3 was
  `a2beed27c4ee19db039c55d112e732850c223c2e6cbb277ee6cbdd9278cc1372`).

**Primary endpoint and decision rule** (spec §11 `emb_ridge`; v4).
- **Common rows:** attempts that `emb_ridge` and every arm in E scored.
- **Baseline:** `e*` is the arm in E with the lowest mean log loss on those
  rows. Choosing it on the same data favours the explicit side, so the
  selection is conservative.
- **Test statistic:** the per-attempt difference
  Δᵢ = loss(e*)ᵢ − loss(`emb_ridge`)ᵢ and its mean.
- **Interval:** a cluster-robust 95% t interval over items: the mean Δ̄ ±
  t(0.975, G − 1) × se, with the CR1 standard error
  se² = G/(G − 1) · Σ_g (Σ_{i∈g} (Δᵢ − Δ̄))² / n² over the G items. It is the
  harness's `cluster_t_interval`. It has no resampling, so it does not depend
  on B or the seed.
- **Margin:** m = 0.0 nats per attempt (D9).
- **Smallest worthwhile gain:** δ = 0.005 nats per attempt.
- **Verdict** (reason codes in brackets):
  - `kill` if the interval's upper bound is below δ: any held-out gain is
    smaller than the smallest worth building, and the GP success head is not
    pursued. If the lower bound is also above m, the gain is real but too
    small (`real_gain_below_delta`); otherwise (`upper_bound_below_delta`).
    A `real_gain_below_delta` kill is provisional: rerun when the data has
    grown.
  - `embeddings_add_value` otherwise, if the interval's lower bound is above
    m (`lower_bound_above_margin`).
  - `insufficient_data` otherwise: the interval reaches both m and δ, so no
    decision (`undecided`). Rerun with more data.
  - `insufficient_data` also when there is no interval (`no_interval`: no
    common attempts, one item cluster, or cluster means within 1e-12 nats),
    with the reason.
  - Coverage below 80% of ability-scored attempts adds a `partial_coverage`
    caveat but does not change the verdict.

**Gated secondary** (hierarchical, so no multiplicity correction is needed).
These are read only if the primary verdict is `embeddings_add_value`:
- `success_head` against e*, with the same three-way rule and interval;
- then `success_head+difficulty` against e*, if available, read only if
  `success_head` was `embeddings_add_value`.

Only `embeddings_add_value` opens the gate; `kill`, `insufficient_data` and an
unavailable arm close it. Gated comparisons are always computed and printed
with their verdict and reason, but labelled `not_interpreted` once the gate
is closed.

**Descriptive only (no decision):**
- `emb_ridge` against `tag_logistic` (the pure embedding increment), with
  the verdict's t interval: it is the primary comparison itself whenever e*
  is `tag_logistic`;
- every comparison split by `item_position` (first attempt on a never-seen
  item vs a repeat) and by `attempt_position` (first unseen LO vs later);
- `llm_zero_data`, raw and recalibrated, against e* and against `emb_ridge`;
- log loss, Brier, AUC and reliability bins for every arm.

Every T8 interval clusters on items, across the whole T8 report, not only
the T8 analysis block. The verdict intervals (primary and gated) and
`emb_ridge_vs_tag_logistic` are the cluster-robust t intervals above. Every
other interval is a paired percentile item bootstrap (B = 1000, seed 0; each
drawn item brings all its attempts):
- the LLM comparisons and the splits in the analysis;
- report 1's log loss and Brier (overall and split) and its comparisons
  against the incumbent, and report 2's miss rates. The harness runs with
  `bootstrap_unit="item"` for these.

Every interval in the analysis names its `method` (`cluster_robust_t_cr1` or
`item_bootstrap_percentile`). The manifest records `bootstrap.unit = "item"`,
the percentile method and its scope. The Wilson intervals are analytic. A
split on a single item, or with equal item means, reports no interval.

## Overlap with router R0 (for the merge)

- **What T8 builds.** The zero-data arm follows §11 and 2610.11135 (JevKT): no
  platform or population data, nothing fitted. It sends:
  - the current item's stem and KC names (LO and facet titles);
  - the learner's own last 25 graded interactions as (opaque item reference,
    KC names, correct / partial / incorrect).
- **Where it overlaps R0.** That is R0's **V2** on the `llm` model (field
  §7.2), except that it sends no difficulty prior. It is not V1: V1 sends no
  history, and JevKT's zero-data condition is knowledge tracing on the
  learner's own history.
- **What it reuses.** The existing offline route
  `ai.routing.field_llm_probability` and its switches; R0's new routes are not
  pre-empted.
- **At merge:**
  - if R0's V2-llm request matches, keep one arm and alias the other;
  - collapse T8's preparation loop onto R0's variant machinery if R0
    generalizes `offline_llm.py`.

  T8 duplicates that loop in its own module on purpose, so as not to edit
  `offline_llm.py` while R0 is changing it.

## What was built

### Arms (`field/success_head.py`, pure)

- **The model.** `LogisticHead` is a prequential Bayesian logistic regression
  over the pre-registered feature blocks.
  - After each observed positive-mass attempt, it refits the MAP by damped
    Newton on all past attempts, weighted by mass, under fixed Gaussian
    priors.
  - The Laplace covariance at the MAP gives the predictive variance.
- **Four arms:**
  - `tag_logistic`: no embedding block;
  - `emb_ridge`: the MAP point;
  - `success_head`: MacKay-moderated, so it shrinks toward 0.5 off-support;
  - `success_head+difficulty`: adds the solver-panel `b`, and abstains on
    every other item.
- **Inputs.** Each arm sees only:
  - `ItemFeatures`;
  - the rows the harness hands it after prediction;
  - a frozen `ContentIndex` lookup for the attempt being predicted.

  A test shows that adding future attempts' content changes no prediction.
- **Ability feature.** It comes from the incumbent EKF run with `a = 1, b = 0`.
  Test: LLM-labelled `b`/`a` leave every T8 prediction bit-identical.
- **Never active.** Every arm has `calibrated_uncertainty = False` and is
  never registered as active.

### Pre-registered analysis (`field/success_head_analysis.py`)

- **What it computes:**
  - the decision rule (v4: three-way, on the cluster-robust t interval over
    items, with a real gain below δ a `kill`), with e* chosen from E;
  - the hierarchical gate;
  - the descriptive comparisons, split by `item_position` and
    `attempt_position`;
  - flags for deviations from the registered bootstrap and seed.
- **Where it lives.** It runs as an `analyses` hook inside the harness, so no
  per-row data leaves `evaluate`.
- **Output:** aggregates only, plus a verdict preamble at the top of the
  markdown report.

### Zero-data LLM arm (`field/zero_data_llm.py`)

- **The request** for each attempt contains:
  - the stem the learner saw (capped at 6000 characters);
  - the KC names (LO and facet titles);
  - the last 25 graded interactions as (opaque `i<sha256[:10]>` reference,
    KC names, correct / partial / incorrect).

  It never contains answers, rationales, hint text or the outcome being
  predicted.
- **Preparation:** explicit, spend-capped and resumable.
  - Each returned verdict, valid or not, appends to `judgment_ledger`.
  - Receipts are recorded under `owner_kind = t8_zero_data_probability`.
  - The cache is checkpointed outside the vault.
- **Replay:** cache only. It fails closed on a missing checkpoint.
- **Two arms:** `llm_zero_data` (raw) and `llm_zero_data:recalibrated`
  (intercept MAP on past predictions only).

### Content loader (`field/item_content.py`)

- **Text** follows the outcome view's revision status (exact snapshot, or
  explicitly reconstructed current content).
- **Vectors** come from that exact text's `item/stem` content hash, as MRL
  first-32 dimensions, L2-normalized.
- **Ambiguous identities:** two attempts sharing (item, `observed_at`) with
  different content are cleared, never guessed.
- **Skeletons:** `item/skeleton` vectors are read only if PF-b registers that
  recipe, and only for attempts that saw the current prompt.
- **`seen_stem_records`** builds canonical `item/stem` records for every
  scored attempt's seen text.

### Command (`learnloop eval success-head`)

- **Modes:**
  - `--dry-run` plans with no calls or writes;
  - `--backfill-seen-stems` and `--prepare-llm` are separate explicit paid
    invocations;
  - `--llm-cache` replays from the cache.
- **Defaults:** bootstrap and seed match the pre-registration.
- **Report files:** named `t8-success-head-<digest>.{json,md}` and
  content-addressed.

### Shared-code changes (additive)

- **`field/evaluation.py`:**
  - optional `covers()` abstention;
  - the `item_position` split, which now appears in every harness report;
  - the `analyses` hook and the `ReplayArrays` type;
  - a `write_reports` preamble.
- **`ops/embedding_backfill.py`:** `records=` takes explicit canonical
  records, validated against the recipe content hash, and the report gains
  `records_source`.
- **`vault/embedding_recipes.py`:** `EmbeddingRecipe.content_hash`, the same
  hunk as on `slice-a/phase-5b`.
- **`pyproject.toml`:** `field.success_head` joins the purity contract.
- **`tests/cli_help_snapshot.json`:** regenerated.

## Deviations from the plan and the spec

1. **The analysis lives in its own module.** `field.evaluation` lazily imports
   `scheduling.fsrs`, so the pure arm module cannot import the harness under
   the purity contract.
2. **New paid step `--backfill-seen-stems`** (plus `records=` on the Phase 1
   backfill).
   - **The problem:** the `item/stem` recipe embeds only current, non-retired
     prompts. On the tracked `linear_algebra` copy, 38 of 70 graded attempts
     are on retired items, so the comparison would have covered a biased 57%
     subset.
   - **The fix:** the step embeds the exact text each scored attempt showed.
   - **Safety:** retrieval consumers (Slice 1 retrieval, family proposals,
     Phase 5b's practice index) read only current content hashes, so these
     extra vectors never enter a live index.
3. **Paid steps load the vault with its settings, as `embeddings backfill`
   does.** Phase 2's offline `eval` loader skips `settings.env`, so the Codex
   route had no checkout path and the first real call failed before sending
   anything.
   - Replay and dry runs stay environment-free.
   - The loaded settings only add process keys and the Codex checkout path,
     which are not in the cache's settings hash.
4. **Pre-registration v2, v3 and v4:** see "Revision v2", "Revision v3" and
   "Revision v4" above. All were made before any run on owner data. v3
   departed from the letter of §11's kill rule ("the interval includes 0 at
   the margin"): an interval that includes 0 is a kill only if it also lies
   below δ (owner, 2026-10-12). v4 makes any interval below δ a kill, a real
   gain included. Spec §11 now states the v4 rule.
5. **The §11 "GP classifier (or Bayesian logistic)" is built as the Bayesian
   logistic.** `success_head` shares `emb_ridge`'s MAP fit and differs only in
   its moderated predictive variance.
   - The "tag kernel" is the one-hot tag block.
   - The "time-decay kernel" is the forgetting and recency features.
   - The "difficulty prior" is the solver-panel block.
6. **Feature notes:**
   - Historical retrievability is never present in the outcome view, so it is
     not a feature.
   - Facets are about 1:1 with LOs, so only LO, capability and relation tags
     are used.
   - Hint-only zero-mass rows are scored but, like the incumbent, don't train
     the heads.
7. **Built while Phase 5a and 5b are in parallel:**
   - The skeleton view and the solver-panel difficulty are wired to the names
     the specs give (`item/skeleton`, `difficulty_source = "solver_panel"`).
   - Neither exists on this base, so both are reported as unavailable now.

## Fakes run on a fixtures-local copy (Done criterion)

**Setup.**
- **Copy:** a backup-API copy (`copy_tree_with_databases`) of this worktree's
  tracked `fixtures/linear_algebra`, at `fixtures-local/t8-linear_algebra`.
  - It was migrated with `doctor --fix-state`.
  - Doctor exits 1 only for vault-layout issues, such as the untracked empty
    `rubrics/` directory.
- **Fakes:**
  - a deterministic hash-seeded embedder, through `--backfill-seen-stems`;
  - a fake Codex client that returns a smoothed history rate, through
    `--prepare-llm`.
- **Configuration:** set on the copy's TOML.
- **Script:** scratch only, not committed.

**Results.**

| Step | Result |
|---|---|
| Data check (`--legacy-fallback current_content`) | 70 graded attempts, 53 ability-scored. Under `exclude`, all 70 are excluded: the tracked log has no exact snapshots |
| Seen-stem dry run, then run | 37 explicit records; 2 batch calls estimated at $0.00012; 37 embedded |
| Coverage | `stem_vector` went from 0 to 53 of 53 |
| LLM dry run | 53 predictions; subscription billing, `estimated_only`; 319,325 planned tokens |
| LLM preparation | 53 fake calls, 53 ledger rows |
| Cache-only replay | Zero calls; the database file is byte-identical before and after |
| Verdict (under v2) | `insufficient_data` (53 common attempts < 100), coverage 1.0 |
| `success_head+difficulty` | `unavailable` (no `solver_panel`) |

- **Report:** `fixtures-local/reports/t8-fakes/t8-success-head-5551a02119de7430.{json,md}`.
- **Leak check:** neither file contains an item id or any prompt text.
- **Numbers carry no meaning:** the fake vectors are noise.

**Do not reuse this copy for real runs.** It now holds fake vectors under the
real model id and fake ledger rows. It was renamed
`fixtures-local/t8-linear_algebra-FAKES` after the run.

**Under v3** (stage `t8-interval-rule`, a fresh fake-vector copy): the same
53 attempts fall in 37 item clusters, and the verdict is `kill`, with interval
[−0.00586, 0.00017] against `tag_logistic`. Noise vectors barely move
`emb_ridge` from its nested baseline, so the interval is narrow. The numbers
still carry no meaning. See `docs/reviews/t8-interval-rule.md`.

**Under v4** (stage `t8-t-interval`, a fresh fake-vector copy): the mean gain
is again −0.002221 over 53 attempts in 37 items (identical, so the noise
vectors coincide). The cluster-robust t interval (df = 36, t = 2.028) is
[−0.005297, 0.0008547], against v3's [−0.00586, 0.00017]. Both are `kill`
(`upper_bound_below_delta`). The numbers still carry no meaning. See
`docs/reviews/t8-t-interval.md`. After the v4 review the descriptive
`emb_ridge_vs_tag_logistic` carries the same t interval, so v3's percentile
interval no longer appears in the report
(`docs/reviews/t8-t-interval-codex-review.md`).

## Real paid calls and cost

| Call | Route | Purpose | Usage and cost |
|---|---|---|---|
| 1 | Codex (`codex` profile, `gpt-5.6-sol`; subscription) | Interface check: one zero-data prediction on the fakes copy, after a dry run | Returned `p_success = 0.78`. Codex reported 16,385 tokens against a planned 3,424; cost `estimated_only`, $0 metered. One judgment row and receipts recorded |
| — | Codex | Attempt before the loading fix (deviation 3) | Refused locally, "Codex checkout path is not configured"; no request sent. A `failed` root receipt was recorded |
| — | OpenRouter | — | 0 calls; $0 |

Codex's reported usage per prediction is about 5× the planned estimate,
because the Codex agent adds its own prompt. On the subscription this only
affects the `estimated_only` figures.

## Owner-run commands (on a backup-API copy; never on the working vaults)

From the main checkout, after merge.

**1. Copy and migrate the copy.** Doctor may exit 1 for vault-layout issues.

```fish
uv run python -c "from pathlib import Path; from learnloop.db.copies import copy_tree_with_databases; copy_tree_with_databases(Path('fixtures/linear_algebra'), Path('fixtures-local/t8-la'))"
uv run learnloop doctor --fix-state --vault fixtures-local/t8-la
```

**2. Edit the copy's `learnloop.toml`.** The working vaults predate Phase 1, so
add:
- **For embeddings:**
  - `routing.embedding = "openrouter_embedding"` under `[ai.routing]`;
  - an `[ai.providers.openrouter_embedding]` profile (type `openai_embedding`,
    `base_url = "https://openrouter.ai/api/v1"`,
    `api_key_env = "OPENROUTER_API_KEY"`);
  - `[embedding]` with `enabled = true` and `backfill_enabled = true`.
- **For the LLM arm:**
  - `[field]` with `enabled = true` and `llm_probability_enabled = true`;
  - `field_llm_probability = "codex"` under `[ai.routing]`.

**3. Plan.** Decide the revision policy before running. On the tracked log,
`exclude` leaves no rows (see open question 1).

```fish
uv run learnloop eval success-head --vault fixtures-local/t8-la --legacy-fallback current_content --dry-run
```

**4. Embed the stems the attempts showed.** Dry run first, then raise the caps
to the planned counts.

```fish
uv run learnloop eval success-head --vault fixtures-local/t8-la --legacy-fallback current_content --backfill-seen-stems --dry-run
uv run learnloop eval success-head --vault fixtures-local/t8-la --legacy-fallback current_content --backfill-seen-stems --max-candidates <records> --max-calls <batches>
```

**5. Optional: the zero-data LLM arm.** One Codex call per scored attempt, on
the subscription. Dry run first.

```fish
uv run learnloop eval success-head --vault fixtures-local/t8-la --legacy-fallback current_content --llm-cache fixtures-local/t8-llm-cache --prepare-llm --dry-run --max-candidates <n> --max-calls <n>
uv run learnloop eval success-head --vault fixtures-local/t8-la --legacy-fallback current_content --llm-cache fixtures-local/t8-llm-cache --prepare-llm --max-candidates <n> --max-calls <n>
```

**6. The report.** Replay makes zero calls. Leave out `--llm-cache` to skip the
LLM arms. The dry run and the report both print the pre-registration; check
that it reads `t8-preregistration-v4` (hash `9f686a23048ea140…`). A copy
prepared under v2 or v3 can be reused: the stored vectors and the LLM cache
don't depend on the decision rule.

```fish
uv run learnloop eval success-head --vault fixtures-local/t8-la --legacy-fallback current_content --llm-cache fixtures-local/t8-llm-cache
```

**Reading the report.** The markdown starts with the pre-registered verdict.
It shows:
- the δ in force (0.005) and m (0.0);
- n and the number of item clusters;
- the 95% cluster-robust t interval of the gain, with its degrees of freedom,
  t value and standard error;
- the verdict, its reason code and its reason.

The verdicts:
- `embeddings_add_value` (lower bound above m, upper bound at or above δ)
  opens the gated heads;
- `kill` (upper bound below δ) means the GP success head is not pursued.
  `real_gain_below_delta` marks a real gain smaller than δ; its reason names
  the δ at which it would have counted. That kill is provisional: rerun when
  the data has grown;
- `insufficient_data` is no decision. Either the interval reaches both m and
  δ, or there is no interval (one item, or no variation). Rerun the same
  command when more attempts exist. The distance from the interval's bounds
  to m and δ shows how far the data is from a decision; there is no fixed
  attempt count to wait for. With few items, t's G − 1 degrees of freedom
  keep the interval wide.

Every verdict also carries `flipping_delta`, its interval's upper bound: the
verdict is `kill` exactly when δ is above it. That is the number to watch if
δ needs revisiting.

The verdict also feeds condition 3 of the learned-router trigger
(`spec_action_router_v1.md` §13). That condition reads the lower bound, not
the verdict name: `embeddings_add_value` or a `real_gain_below_delta` kill
meets it (router D10).

## Migrations

None. Vectors, judgments and receipts use the existing tables, so the DB
reference scripts were not needed.

## Files touched

- `docs/reviews/slice-2-t8.md`
- `pyproject.toml`
- `src/learnloop/cli/evaluation.py`
- `src/learnloop/cli/success_head.py` (new)
- `src/learnloop/field/evaluation.py`
- `src/learnloop/field/item_content.py` (new)
- `src/learnloop/field/success_head.py` (new)
- `src/learnloop/field/success_head_analysis.py` (new)
- `src/learnloop/field/zero_data_llm.py` (new)
- `src/learnloop/ops/embedding_backfill.py`
- `src/learnloop/vault/embedding_recipes.py`
- `tests/cli_help_snapshot.json`
- `tests/test_success_head.py` (new)
- `tests/test_success_head_cli.py` (new)
- `tests/test_zero_data_llm.py` (new)

## Gate

All run in this worktree at the final code commit.

| Check | Result |
|---|---|
| `uv sync --extra dev` (+ `uv pip install pypdfium2`) | ok |
| `uv run lint-imports --no-cache` | 10 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7118 passed**, 0 failed (209 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **66 passed**, 7052 deselected |
| T8 tests (`test_success_head.py`, `test_zero_data_llm.py`, `test_success_head_cli.py`) | 18 + 14 + 10 = 42 passed |

- **Frontend:** unchanged, so no `npm` checks were needed.
- **Schema:** unchanged, so the DB reference scripts were not needed.
- **CLI help snapshot:** regenerated for the new subcommand.

## Open questions

1. **Revision policy for the owner's run.**
   - Under the default `exclude`, the tracked `linear_algebra` log has no
     exact rows: all 70 are excluded.
   - The recommendation is `--legacy-fallback current_content`, the labelled
     reconstruction, decided before the run.
   - The owner's live log may hold more exact rows. Rows written after
     snapshots existed are exact.
2. **Merge with R0.**
   - `llm_zero_data` is R0's V2 on the `llm` model, minus the difficulty
     prior. Keep one and alias the other.
   - Fold T8's preparation loop into R0's variant machinery if R0 generalizes
     `offline_llm.py`.
3. **Phase 2's `eval --prepare-llm` and `field classify-questions`** still load
   without the settings environment. A Codex route therefore fails there
   unless the shell exports `LEARNLOOP_CODEX_CHECKOUT_PATH`. Apply T8's
   paid-step loading to them at integration?
4. **Codex usage estimates.** The planned per-prediction tokens understate
   Codex's reported usage about 5×. This is harmless on the subscription. Use
   generous `--max-tokens` if a metered route is ever used.
5. **Verify at the PF-b / Phase 5a merge:**
   - The `item/skeleton` recipe's `records(loaded)` yields current skeletons
     keyed by item id.
   - Solver-panel items carry exactly `difficulty_source = "solver_panel"`,
     with `b` on the ability scale.

   Both are wired by name here and untested against the real producers.
6. **Minimum data.** Resolved by pre-registrations v3 and v4 (owner,
   2026-10-12): there is no attempt floor and no item minimum. The verdict
   comes from the cluster-robust t interval over items, whose G − 1 degrees
   of freedom widen it with few items. It is `insufficient_data` only while
   the interval reaches both m and δ, or where no interval exists (one item,
   or no variation). The tracked fixture has 53 attempts in 37 items, so it
   can reach a decision.

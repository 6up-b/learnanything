# Slice 2 T8 — learner success head (offline research)

**Checkpoint:** in progress on `slice-2/t8` (worktree `learnanything-t8`, base
`main` at `974c5647`). Offline research only: no live consumer, no serving
change, no activation, no merge or push.

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
| Embedding | each stem (and skeleton) dimension | 0 | 1.0 |
| Difficulty | solver-panel `b` | −1 | 0.25 |

*Fitting:*
- observations are weighted by effective mass;
- moderation is MacKay's probit approximation.

*LLM arm:*
- the history window is 25 graded interactions;
- stems are capped at 6000 characters;
- recalibration is a one-parameter logit intercept, MAP under N(0, 1) on past
  predictions only.

**Primary endpoint and kill rule** (spec §11 `emb_ridge`).
- **Common rows:** attempts that `emb_ridge` and every arm in E scored.
- **Baseline:** `e*` is the arm in E with the lowest mean log loss on those
  rows. Choosing it on the same data favours the explicit side, so the
  selection is conservative.
- **Test statistic:** the per-attempt difference
  Δᵢ = loss(e*)ᵢ − loss(`emb_ridge`)ᵢ, with a paired percentile bootstrap that
  resamples attempts (B = 1000, seed 0, the harness's
  `paired_bootstrap`).
- **Margin:** m = 0.0 nats per attempt (D9).
- **Verdict:**
  - `insufficient_data` if there are fewer than 100 common rows. No decision;
    rerun with more data;
  - otherwise `embeddings_add_value` if the 95% interval's lower bound is
    above m;
  - otherwise `kill`: embeddings add no held-out predictive value, and the GP
    success head is not pursued.
  - Coverage below 80% of ability-scored attempts adds a `partial_coverage`
    caveat but does not change the verdict.

**Gated secondary** (hierarchical, so no multiplicity correction is needed).
These are read only if the primary verdict is `embeddings_add_value`:
- `success_head` against e*, with the same test;
- then `success_head+difficulty` against e*, if available.

They are always computed and printed, but labelled `not_interpreted` when the
gate failed.

**Descriptive only (no decision):**
- `emb_ridge` against `tag_logistic` (the pure embedding increment);
- every comparison split by `item_position` (first attempt on a never-seen
  item vs a repeat) and by `attempt_position` (first unseen LO vs later);
- `llm_zero_data`, raw and recalibrated, against e* and against `emb_ridge`;
- log loss, Brier, AUC and reliability bins for every arm.

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

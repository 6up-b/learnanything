# Adaptive difficulty AD2+AD3: practice in the band, the subject view live

Stage `adaptive-difficulty-ad23` of `docs/specs/spec_adaptive_difficulty_v1.md` (§14 AD2 and AD3,
one algorithm successor), branch `adaptive-difficulty/ad23`, worktree `learnanything-ad1`, base
`29a49b5e6` (the AD1 landing on main: migration head 213, latest successor `mvp-0.27`). Owner
go-ahead 2026-10-18 ("we're implementing ad2 next"). The hints track (RW2b+H3) runs in parallel in
`learnanything-merge4`; this stage stays out of `learnloop/hints/`, `learnloop/workbench/`, the
workbench handlers and screens, and touches `PracticeScreen.tsx` only at narrow call sites.

This stage builds and gates. It does **not** merge: the successor merges only after the owner has
read the AD2/AD3 report on a backup copy (spec §10.4, §14).

## 0. Plan (written before any code or replay)

**What AD2+AD3 is.** One algorithm successor (`mvp-0.30`: built as the next free tag `mvp-0.28` and renumbered after DL2's `mvp-0.29` at the compose round; `mvp-0.28` is never used): AD's own posterior
(§5) in two views (`subject`, `lo:<id>`), practice draws in the band over the slot support of a
planned new-material slot (§6.1-6.2), commission draws and the generation contract (§7.1, §7.4),
the subject view steering live with learned relatedness (§5.10) and reading (§5.11), the readiness
numbers and the router card's AD fields (§9.5, §10.1), the monitoring and the AD report (§10.4).
Outside the successor, in the same stage: the randomized dose offers in the Reader (§5.12).

**Files (new).**
- `src/learnloop/adaptive_difficulty/`:
  - `priors.py` (`ad_priors_v1`, `ad_hyper_v1`, the fixed constants, the feature coding φ);
  - `model.py` (the functional core: a bank of Gaussian filters sharing one event skeleton,
    lazy coordinates, the coupled construction, the joint factor by Gauss-Hermite quadrature,
    linear transitions, predictive quantities `p̄`, `P_band`, `I_c`, the mixture);
  - `outcomes.py` (§5.3's categories, help timing, the censored factor);
  - `relatedness.py` (the proposal job, validation, ledger rows, coupling versions);
  - `replay.py` (the AD replayer: both views from ledgers and receipts, zero model calls; writes
    `ad_state`, `ad_attempt_trace`), `scoring.py` (`item_forecast_scores`);
  - `selection.py` (`ad_select_v1`: support, band / calibrate / overlap, exact propensities,
    seeds; commission candidates `X_c` and ladders `ad_ladder_v1`);
  - `serving.py` (the slot draw in the serve transaction, substitution, displacement, AD
    deferrals, the `ad_threshold@*` receipts);
  - `generation.py` (the generation contract and the re-forecast of landed commissions);
  - `dose.py` (the dose arm: eligibility, the `reading_dose_v1` draw, uptake rows);
  - `readiness.py` (readiness lines with the untested rule, the router card's AD fields);
  - `report.py` (the AD report: prequential metrics, comparators, confidence sequences, auto-flags,
    the honest line, identifiability diagnostics, time to usable, the dose-and-burden analysis,
    self-check calibration) and `arms.py` (the harness arms of §10.4);
  - `successor.py` (the version gate and the six switches).
- `src/learnloop/sim/ad_synthetic.py` (synthetic learners, vaults with known structure, synthetic
  readers; drives the real `model.py` and `selection.py`).
- `src/learnloop/ad_successor_upgrade.py` (`learnloop upgrade --to mvp-0.30`).
- `src/learnloop/db/stores/ad_serving.py` (the only SQL writer of migration 214's tables).
- `migrations/214_adaptive_difficulty_serving.sql`.
- Sidecar: `handlers/adaptive_difficulty.py` (the Reader's dose offer and its uptake; the readiness
  lines), desktop-only.
- Frontend: `screens/practice/WhyThisItem.tsx`, `screens/reader/DoseOffer.tsx`, a readiness line
  component; narrow call sites only.
- Tests (each gate test written first): `tests/test_ad2_model.py`, `test_ad2_sim.py`,
  `test_ad2_serving.py`, `test_ad3_subject_view.py`, `test_ad3_relatedness.py`,
  `test_ad3_reading.py`, `test_ad3_dose_arm.py`, `test_ad3_monitoring.py`, `test_ad23_migration.py`,
  `test_ad23_successor.py`, plus the carve-out test added to `tests/test_salience_firewall.py`.

**Files (changed).** `attempts/salience_firewall.py` (rule text and the one carve-out);
`adaptive_difficulty/reading.py` (the allowlist moves to the firewall module); `serve_inputs.py`
(the loadings in force and the coupling version); `daily_plan/engine.py` and `records.py` (the
slot draw, `item_substituted`, `item_displaced` with `ad_ineligible`, the exclusion set);
`content/authoring/practice_generation.py` (the generation contract under the successor);
`daily_plan/router_card.py` / `router/card.py` (the AD fields); `scheduling/randomization_layer.py`
(the `feature_overlap` and `reading_dose` designs); `config/schema.py`, `config/template.py`,
`params/parameter_registry.py`; `algorithm_versions.py`, `cli/app.py` (`--to mvp-0.30`),
`cli/ad.py` (`ad report`, `ad relatedness`, `ad eval`); `db/table_roles.py`,
`substrate/rebuild_orchestrator.py`; the head fixture `migration_head_213` -> `migration_head_214`
and every path naming it; the spec (Q8 record, amendments) and dated notes in
`spec_knowledge_model.md` §8.3 and `spec_p3_reader_integration.md` §8.2, §15.4.

**Migration 214** (one, only §11.2's AD2/AD3 tables):
- `ad_selections` RAW_LEDGER (append-only): serve and commission draws with their support,
  scores, exact propensities, seed, choice, mode, state hash, versions;
- `ad_commission_results` RECEIPT (append-only): a landed commission's re-forecast;
- `ad_dose_offers` RAW_LEDGER (append-only): the dose arm's draws and their uptake rows;
- `ad_coupling_versions` RECEIPT (append-only): each adopted coupling version per subject (the
  relatedness ledger rows in force), so replay knows which proposal applies to the whole history;
- `ad_state`, `ad_attempt_trace` DERIVED, one replayer (`adaptive_difficulty`);
- `item_forecast_scores` DERIVED, one replayer (`item_forecast_scores`).
- `item_substituted` and `item_displaced` (`ad_ineligible`) are block events in the existing
  `attention_block_events` (free-text kind and detail): no migration.

**Successor and switches.** `mvp-0.30` (renumbered from `mvp-0.28` at the compose round), one upgrade function chained from `mvp-0.29` (from `mvp-0.27` before the compose round; and from
`mvp-0.9`..`mvp-0.27` through the chain), one defaults snapshot. Six switches inside it
(`selection`, `generation_contract`, `promoted_predictor`, `learned_coupling`,
`reading_opportunities`, `reading_self_check`), each false restoring its part exactly, composing as
§11.1 states; `reading_dose_offers` outside it. Below the tag every AD2/AD3 path is off whatever
the switches say, so the predecessor (`mvp-0.29` since the compose round) stays byte-identical.

**Spend caps and model routes.** The relatedness proposal is AD2/AD3's only paid call: on the
field harness's frontier route `ai.routing.llm_probability_llm` (empty: the active provider; Codex
`estimated_only`), through `adaptive_difficulty/sending.py` (`SendGuard`, the fail-closed start
receipt) and `claims.py` (durable claims), inside `adaptive_difficulty.daily_spend_cap_usd` (new
owner kind `ad_relatedness`), `--dry-run` first, background re-proposals on the bounded queue
pattern. It reads no learner data and no held-out text (§5.10). No live or paid call in this stage:
every model-backed path is tested with fakes.

**`judgment_ledger` writes.** Task `ad_relatedness`, prompt version `ad-relatedness-v1`, judge
`llm`: one row per proposed loading (item revision -> facet) or coupling (LO -> LO), strength as
`score`, the rationale, and the `input_hash`.

**Tests.** G-AD2-1..31 and G-AD3-1..15 (each run failing first on the base for its stated reason),
the migration's durability test and FK check, table roles, the coordinated-migrations and tracked
fixture tests, the successor's switch-off byte-identity pins (and a shadow rebuild on a
`fixtures-local` copy), the mobile allowlist pins for the new RPCs, the parameter registry, the
config defaults snapshot, the CLI help snapshot, the desktop RPC contract, `sim/` recovery and
time-to-usable runs, vitest for the new components.

## 1. Pre-registration (fixed before any replay or simulation run)

Spec §10.4: "Each arm's constants, and the thresholds of G-AD2-18, G-AD3-7 and G-AD3-11, are
pre-registered in `docs/reviews/adaptive-difficulty-ad23.md` before the first replay on owner
data." This section is that record. Nothing below was tuned on any run; any later change is
listed in §1.9 as an amendment with its reason.

### 1.1 The model's constants (`ad_priors_v1`, `ad_hyper_v1`)

Exactly §5.5:
- subject level `N(0, σ_G²)`; facet and cell offsets `N(0, (3 - σ_G²)/2)`; capability offsets
  schema_interpretation `N(-0.3, 0.5²)`, procedure_execution `N(-0.5, 0.5²)`, method_selection
  `N(-0.8, 0.5²)`, coordination `N(-1.2, 0.5²)`, retrieval `≡ 0`;
- `β`: complexity steps `N(0.5, 0.3²)` (4), transfer steps `N(0.5, 0.3²)` (3), scaffolding
  cue->none `N(0.5, 0.3²)`, cue->partial `N(-0.5, 0.3²)`, partial->worked `N(-0.5, 0.3²)`, span
  steps `N(0.4, 0.3²)` (3), response recognize `N(-0.7, 0.4²)`, long_constructed `N(0.3, 0.3²)`,
  structured_steps `N(0.3, 0.3²)`, performance `N(0.6, 0.4²)`, tools open_book/references
  `N(-0.4, 0.3²)`; reference tuple: complexity 0, same_context, short_constructed, cue, atomic,
  closed_book;
- `α_llm N(0.2, 0.2²)`, `α_panel N(0.5, 0.3²)`, `α_v1 N(0.2, 0.2²)` (only in `+outside`),
  `α_origin N(0, 0.5²)`; `γ N(0.2, 0.1²)`; `ζ N(1.0, 0.5²)`;
- reading: `γ̄_1 N(0.10, 0.07²)`, `γ̄_2 N(0.20, 0.10²)`, `δ_{κ,1} N(0, 0.07²)`, `δ_{κ,2}
  N(0, 0.10²)` per kind; verdicts `λ_matched`, `λ_missed` `N(0, 0.3²)`;
- `+rating`: `ρ̃ N(log 0.5, 0.5²)`, `c_1 N(-1.0, 0.5²)`, `d̃ N(log 2.5, 0.3²)`; `+timing`:
  `ν N(0, 0.3²)`, `ω̃ N(log 0.15, 0.6²)`;
- fixed: `a = 1`, `λ = 0.02`, `κ = 1.5`, `τ0 = 1.0`, `σ_ℓ = 0.6`, `h_w = 6 h`,
  `σ²_drift = 0.01/day`, at most 3 loadings per item and 3 coupled LOs per LO, `h_1 = 1`,
  `h_2 = 4`;
- `ad_hyper_v1`: `σ_G² ∈ {0.75, 1.5, 2.25}` × `χ_C ∈ {0, 0.25, 0.5, 0.75}` × `χ_Q ∈ {0, 0.25,
  0.5}`, prior 1/36 each; the LO view fixes `σ_G² = 1.5`, no loadings, couplings or reading.
- Quadrature: 32 probabilists' Gauss-Hermite nodes on `η` (the `ε` variance folded in), 5 per link
  coordinate; `I_c` by 24 outer x 24 inner nodes. `F_x⁻¹` by bisection to 1e-12.

### 1.2 Selection constants (`ad_select_v1`, `reading_dose_v1`)

Band `[0.70, 0.80]`, overlap `[0.55, 0.90]`, overlap share `q = 0.10`, near-tie margin 0.05,
calibrate below `max P_band < 0.35`, calibrate near-ties within 5% of the maximum information
(relative). Dose arm: floor 0.10 per feasible variant, base all on `none`, one extra offer per
section, three a day. Seeds: `sha256("ad_select_v1:<block id>:<slot position>")` (serve),
`sha256("ad_commission_v1:<cell>:<decision key>")` (commission),
`sha256("reading_dose_v1:<visit id>:<section id>")` (dose).

### 1.3 The arms (`learnloop ad eval`, and inside `learnloop ad report`)

Scored prequentially, chronologically, on §5.3's event, first-attempt split first:
- `ad_threshold@subject` (base, the live mixture), `@subject_uniform` (its `χ_C = χ_Q = 0`
  points, renormalized), `@lo` (topic-only);
- `@subject:noread` (reading transitions off), `@subject:noverdict` (the verdict term off);
- `@subject:hyper_fixed[σ_G², χ_C, χ_Q]` at each of the 36 points (the uncoupled points at
  `σ_G² = 0.75` and `2.25` are the former split arms);
- `@subject:hyper_fine`: `σ_G² ∈ {0.75, 1.125, 1.5, 1.875, 2.25}`, `χ_C ∈ {0, 0.125, …, 0.75}`
  (7), `χ_Q ∈ {0, 0.125, …, 0.5}` (5), 175 points, uniform prior;
- `+rating`, `+timing`, `+outside` (adds `z_v1` with `α_v1`), in both views;
- `:grid`: a QUEST+-exact grid for the served cell's ability, 241 points on `[-6, 6]`, every other
  coordinate at its posterior mean, `ε` integrated by 32-node Gauss-Hermite;
- `:ts`: Thompson-sampled selection (the decision-level simulation only);
- external comparators `mastery_ekf` and `lo_general` (field's), from their AD1 receipts where a
  presentation has them, else field's own predictors on field's rows.

### 1.4 Scoring, monitoring and flags

- Probabilities are clipped to `[0.005, 0.995]` for log loss; Brier; RPS over fully observed
  categories; reliability by decile and in the band region `[0.6, 0.9]`, whose error is the
  count-weighted mean of |mean prediction - realized rate| over the bins `[0.6, 0.7)`,
  `[0.7, 0.8)`, `[0.8, 0.9]`.
- Field §7.4's rule as a monitor: the bootstrap interval of the attempt-level log-loss difference,
  2000 resamples over presentations, seed `ad-report-v1`, 95%, margin 0 (field D9).
- Confidence sequences on the mean log-loss (or Brier) difference: the two-sided normal-mixture
  boundary for increments bounded by `c` (log loss: `c = log(1/0.005) ≈ 5.30`; Brier: 1),
  `half_width(n) = c·sqrt(2(nρ² + 1)/(n²ρ²) · log(sqrt(nρ² + 1)/α))` with `α = 0.05` and `ρ²`
  tuned to `n0 = 200`. "Helping": the sequence lies below 0; "hurting": above 0; otherwise
  "can't tell yet", always with the count.
- Auto-flags exactly §10.4's table, each recommending its switch: sharing (`@subject` vs `@lo`,
  first attempts at never-seen LOs), coupling (`@subject` vs `@subject_uniform`, same split),
  reading (`@subject` vs `@subject:noread`, first attempts after reading), verdicts (`@subject`
  vs `@subject:noverdict`, first attempts after a verdict), readiness (band-region error > 0.05 in
  two consecutive reports), band missed (realized success outside 0.60-0.88 over 200 AD
  selections), dose burden (of the last 30 delivered extra offers at least 80% dismissed; or a
  cue-density lowering within a visit after an offer, three times in 14 days).
- The "tested by randomized offers" label: the arm's IPW estimate of the offer effect, with its
  anytime-valid 95% confidence sequence excluding 0 and agreeing in sign with the model's curve.
- Dose-and-burden: minutes per event by non-negative least squares of each visit's active minutes
  on its counts per kind plus a constant, bootstrapped (1000 resamples over visits, seed
  `ad-dose-v1`); the useful dose `n*_κ` is the largest `n ∈ 1..10` whose own event's gain per
  minute (posterior median, 400 posterior draws, seed `ad-dose-v1`) is at least the practice
  reference's; its 80% interval from the same draws; "can't tell yet" when that interval spans
  more than 2 events or the kind's minutes are unknown.

### 1.5 G-AD2-18 (time to usable, the owner's target)

- 200 synthetic learners per scenario (`sim/ad_synthetic.py`, seed `g-ad2-18:<scenario>:<i>`).
  True parameters drawn from `ad_priors_v1` at `σ_G² = 1.5`: subject level, facet and cell
  offsets, capability offsets, `β`, `α_origin`, and each learner's own `γ ~ N(0.2, 0.1²)`
  (floored at 0). Items are generated (`z_origin = 1`, no other signal); each item's residual
  `ε ~ N(0, 1)`; no exposures (warmth 0); no help.
- Pools hold 8 items at every point of `X_c` (the default ladder's rungs of the cell's capability
  and their one-step neighbours on a single dimension, clipped to the default trajectory's
  envelope); an item is used once.
- "Band mode engaged at answer t": the draw that served answer t was in band mode. "Band mode
  engages by the 15th answer": the first band-mode draw is at answer 15 or earlier. A band hit:
  the served item's true family-expected success (the learner's true state, `ε` integrated,
  lapse) in `[0.70, 0.80]`. Trivial success: a success on an item whose true family-expected
  success exceeds 0.95.
- **One LO, one cell** (retrieval): 30 answers. Pass: band mode engages by answer 15 for at least
  80% of learners, and the band-hit rate over answers 16-30 is at least 0.35.
- **Wrong prior**: as above with the true subject level fixed at +1.5 for half the learners and
  -1.5 for the other half. Pass: band-hit rate over answers 16-30 at least 0.30.
- **The plan's flow** (the subject view, live): three LOs of one subject, each with one facet and
  two capabilities (retrieval, schema_interpretation), blocks of 5 answers on one LO in rotation
  (LO 1, 2, 3, 1, 2, 3), the block's cell alternating retrieval / schema_interpretation by block,
  30 answers. Comparators on the same learners (common random numbers): the incumbent waypoint
  ladder (`depth_rungs.select_rung`'s band ladder and optimism step on the production mastery EKF,
  uniform among the waypoint's items) and AD with its updates switched off (the prior state
  throughout). Pass: AD's band-hit rate over answers 16-30 at least the incumbent's and at least
  the no-update variant's; AD's trivial-success rate no worse than the incumbent's. Reported for
  seen and never-seen cells separately, with the own answers each never-seen cell needed before
  band mode, and the LO view's figures beside.

### 1.6 G-AD3-7 (related topics adapt faster, unrelated ones are not dragged)

- 200 synthetic learners per scenario, seed `g-ad3-7:<scenario>:<i>`. Vault: 12 LOs in four
  clusters of three (A, B, C), one facet per LO, capability retrieval. True subject level
  `N(0, 1.5)`; true facet and cell offsets `N(0, 0.75)` each, correlated 0.8 within a cluster and
  0 across; true loadings: B's items load 0.5 onto A's facet, C's onto B's (with the true
  implication strength 0.5); true learning `γ ~ N(0.2, 0.1²)`, transferring to cluster mates at
  0.8 of the increment; a true reading effect of 0.3 per section read, transferring the same way.
- Proposals: **correct** (each LO names its two cluster mates at strength 1.0; B's items load 0.5
  onto A's facet and C's onto B's), **noisy** (half the pairs, chosen per seed, replaced by pairs
  across clusters, the loadings likewise), **wrong** (every pair and loading across clusters).
- Flow: 15 answers on cluster 1's A (live selection), then the never-seen mates B and C of cluster
  1, then cluster 2's A (unrelated), each up to 15 own answers. Two more flows: "15 practice
  opportunities on A" is the flow above; "5 sections read on A" replaces A's 15 answers by 5
  section reads (no answer on A) before the mates. Each flow runs under `@subject` (the 36-point
  mixture with the proposal) and under `@subject_uniform`, with common random numbers.
- **Related faster** (correct proposal, both flows): the median own answers before band mode on a
  cluster mate is at least 2 fewer under `@subject` than under `@subject_uniform`, and the mean
  first-attempt log loss on the mates is lower, its 95% bootstrap interval over learners (2000
  resamples) excluding 0.
- **Unrelated not dragged** (all three proposals): on cluster 2's A, mean first-attempt log loss
  no worse than uniform's by more than 0.02, and the band-hit rate over its own answers 1-15 no
  lower than uniform's by more than 0.03.
- **A wrong proposal shrinks**: a separate vault of 70 clusters of three (210 LOs, the wrong
  proposal); 15 answers on one LO, then one first attempt on each never-seen LO in a fixed shuffled
  order at a fixed mid-ladder point. Pass: the posterior weight on `χ_C = 0` reaches 0.5 within 100
  first attempts at never-seen LOs in at least 80% of seeds, and the coupling auto-flag fires
  within 200 in at least 80%. Under the correct proposal (same vault, correct pairs), the flag
  fires in at most 5% of seeds.

### 1.7 G-AD3-11 (which reading helps, how much)

- 200 synthetic readers per scenario, seed `g-ad3-11:<scenario>:<i>`; the subject view at the
  generating hyperparameter point (`hyper_fixed`, no proposal), since the test is about the
  reading curves. A reader works through 1250 LOs, one facet each, four windows per LO: in each
  window it reads (a section read with probability 0.8; tutor exchanges ~ Binomial(3, 0.3); worked
  examples uniform on {0, …, 4}; in-passage questions uniform on {0, …, 3}), the dose arm may offer
  one extra worked example or question at the section boundary (floor 0.10, and separately 0.3;
  taken with probability 0.7), and the window closes with one first-surface answer a day later at
  a calibrate-mode point. An LO's coordinates are marginalized out after its last window (exact for
  a Gaussian, and they are never touched again). True practice learning `γ = 0.2`.
- True curves (coefficients on `b_1`, `b_2`): reading (0.15, 0.10); tutor exchange (0.25, 0)
  (saturates fast); worked example (0, 0.35) (saturates slowly), or (0.5, -0.3) in the downturn
  scenario (maximum near 3); in-passage question (0, 0) (no effect). Minutes per event: reading 6,
  tutor 3, worked example 4, question 2, practice 3.
- Pass (spec): each kind's fitted curve within 2 posterior sd of the true one at doses 1-5 in at
  least 90% of seeds; `n*_κ` within one event of the true one in at least 80%; the no-effect
  kind's full effect with posterior mean below 0.05; the downturn found (the curve's maximum before
  dose 5) in at least 80% of seeds.
- Confounding scenario: no true effect of any kind, and the reader reads more after a failure
  (each count +1 after a failed window). Pass: the randomized estimate of an offer's effect covers
  0 at its nominal rate within ±5 points (its 95% interval covers 0 in 90-100% of seeds), and the
  report never labels that kind's line "tested by randomized offers" (see amendment A3).

### 1.8 Other tolerances the spec leaves to this record

- **G-AD3-6**: synthetic vaults generated at each of the 36 grid points (the G-AD3-7 cluster
  vault, correct proposal, the truth drawn from the model at that point), 25 seeds per point, 300
  first-surface answers over the 12 LOs; "grid neighbours" are the points at Chebyshev distance 1.
  Pass: at least half the posterior weight on the generating point and its neighbours in at least
  80% of the seeds of each point.
- **G-AD3-8** (synthetic part): 200 learners, 2000 windows each as in §1.7 with reading only
  (a section read per window). True rise 0.3 per section: first-attempt log loss after reading
  lower with reading on than off (mean over learners, bootstrap interval excluding 0). No true
  rise: the posterior mean of the reading kind's full effect below 0.05 in at least 90% of seeds,
  and the reading auto-flag fires in at most 5%.
- **G-AD3-9**: 200 synthetic score logs per condition; flags fire when their condition holds (the
  worse model 0.15 nats worse per first attempt, 300 first attempts), and in at least 95% of seeds
  none fires when nothing is worse.
- **G-AD3-15 (6)**: 200 learners, 2000 judged questions each. No signal: |posterior mean| of both
  `λ` at most 0.05 with posterior sd at most 0.1 in at least 90% of seeds. Misses predicting cold
  failure (true `λ_missed = -0.4`): posterior mean of `λ_missed` negative with its 95% interval
  excluding 0 in at least 90%.
- **G-AD2-8**: 200 seeds, 60 answers; "aliased by design": eigenvalue of the data's precision
  contribution below 5% of the prior precision (§5.8).
- **G-AD2-14**: 200 seeds, 60 answers; help with probability `σ(-(true margin) - 1)`, a reveal
  with probability `σ(-(true margin) - 2)`; evaluated on a fixed set of 10 feature points. Pass:
  |predicted - true mean unassisted success| at most 2 posterior sd in at least 90% of seeds; the
  variant that drops assisted attempts overestimates (mean bias over seeds positive, its one-sided
  95% interval excluding 0).

### 1.9 Amendments (each with its reason; none tuned on a result)

- **A1. G-AD2-1's three thresholds are jointly infeasible under the spec's fixed constants**
  (`λ = 0.02`, `τ0 = 1`, `κ = 1.5`), computed before any test: at a cell posterior sd of 0.74
  (§5.9's "usable") a success at demand -3 moves the mean by 0.018 and one at demand 1.0 by 0.21,
  but a failure on the trivial item moves it by only 0.16 (the lapse explains part of it); a move of
  0.5 needs sd >= 1.22, where the trivial success moves 0.06. The test pins the first two at sd
  0.74 (`< 0.02`, `>= 0.2`), the failure at sd 0.74 at `>= 0.15` and at least 8 times the trivial
  success's move, and the failure at the cold-start variance (3.0) at `>= 0.5`. Open question 1.
- **A2. Item-only signals in the base arm**: `z_llm`, `z_panel`, `z_origin` (§10.4: `z_v1` only in
  `+outside`).
- **A3. "Never labels … tested by randomized offers"** (G-AD3-11) cannot hold literally for a
  procedure with a nonzero false-positive rate over 200 seeds; the test requires at most 5% of
  seeds (the sequence's `α`). Open question 2.
- **A4. Pools for the incumbent** (G-AD2-18, plan flow): each cell's pool holds 8 items at every
  point of `X_c` **and at the default trajectory's four waypoint tuples**, so the incumbent
  comparator can serve "uniform among the waypoint's items". Made before the first plan-flow run.
- **A5. G-AD3-11's answer point** is the retrieval entry point `e_retrieval` (demand 0 plus
  `α_origin`), fixed, as G-AD3-7's shrink check fixes its point: the gate tests the reading curves,
  not the selection rule, and a fixed point keeps the doses the only thing varying. Made before
  the first G-AD3-11 run.
- **A6. "The no-effect kind's full effect has posterior mean below 0.05"** (G-AD3-11) is read as
  "in at least 90% of seeds", as G-AD3-8's no-rise condition says. Made before the run.
- **A7. The confidence sequence** (§1.4) is the two-sided normal-mixture boundary on the sum of the
  increments with each increment's **predictable range** (a log-loss difference can take only the
  two values the two forecasts give it, both fixed before the outcome; an offer's IPW term its
  `[0, 1/π]` or `[-1/π, 0]`), so the variance process is `V_n = Σ((b_i - a_i)/2)²` (Hoeffding's
  lemma) and `ρ = V_0/(L + log(1 + L))`, `L = -2 log α`, tuned at `n0 = 200` increments of the mean
  range. `α = 0.05` two-sided, as registered. Reason, computed a priori: with every increment
  bounded by `c = 5.30`, the registered boundary's half-width at `n = 200` is about 1.14 nats per
  attempt (1.0 at 300), so no flag could fire on a realistic difference and G-AD3-9 would fail by
  construction. Made before any simulation run. The null coverage of the new sequence is tested
  (`test_confidence_sequence_is_anytime_valid_under_the_null`, 400 runs, 0-5%).
- **A8. G-AD2-14's design**: the 60 answers are at ladder points drawn uniformly (not AD's draw); help
  is an ordinary hint with no timing marker (a success with it is censored `{0, 1}`, less is 0) and
  the reveal is a primed answer during the presentation (censored); the true mean unassisted success
  at a point is `E_ε[(1 - h(m))(1 - r(m))(1 - λ)σ(m)]`; "within 2 posterior sd" is counted per
  (seed, point) pair. Made before the run.
- **A9. G-AD3-6's design**: the 300 answers are spread over the 12 LOs in a fixed random order at
  ladder points drawn uniformly; every LO's coordinates are created up front in LO order, in the
  truth's bank and the filter's alike, so "drawn from the model at that point" is exactly the
  filter's own joint prior. Made before the run.
- **A10. G-AD3-7's reading flow** (5 sections read on A, no answer on A) is gated on the first-attempt
  log loss and on "unrelated not dragged" only. A priori: with no answer on A, A's coordinates carry
  no information beyond the prior and the reading curve's prior, so the coupled regression cannot
  reduce a mate's predictive variance (§5.10's construction) and band mode cannot engage earlier
  than under uniform sharing; the band-mode median is reported, not gated. Made before the run.
- **A11. G-AD3-9's power**: "the flags fire when their condition holds" is read as "in at least 80% of
  seeds". The worse model is the truth shifted by a constant logit `δ` whose expected excess log
  loss over `p ~ U(0.3, 0.9)` is 0.15 nats (`δ = 1.22`); the null is two equally noisy forecasters
  (logit noise sd 0.3 each); readiness: a forecaster 0.10 too high in the band region, twice;
  band missed: realized 0.50 against 0.75 over 200 selections; dose burden: 90% of 30 dismissed,
  or three density lowerings in 14 days, against 30%. Made before the run.
- **A12. A draw in the simulations is over feature points**, then the point's next unused item: items
  at one point are exchangeable to AD (same features and signals), so this is the item-level rule
  with equal counts per point. Made before any run.
- **A13. G-AD2-8's learner** has true growth (`γ ~ N(0.2, 0.1²)`) and **true `β` drawn from
  `ad_priors_v1`** (a calibration check under the actual policy, §5.8 "simulation recovery"); G-AD2-7's
  learner has `β = 0` ("no feature effect"). Made before the run.
- **A14. G-AD3-11's visit minutes** are `Σ minutes_κ · count_κ + max(N(1, 0.5²), 0)` per window (the
  constant and its noise were not registered). Made before the run.
- **A15. G-AD3-8's synthetic readers** use §1.7's four windows per LO (500 LOs for the 2000 windows);
  "first attempts after reading" is every window's answer (each follows a section read). Made before
  the run.
- **A16. `I_c`'s inner rule** is 24 Gauss-Hermite nodes, as §1.1 registers (the code had used 32);
  the logistic is evaluated as `1/(1 + exp(-clip(x)))`. Both changed before the first full run.

**A17 (a separate, later amendment, made AFTER the results of §3.1 were reported; owner decision
2026-10-19, §3.4).** `calibrate_below` (§1.2, `ad_select_v1`'s band-mode trigger, which is also the
serve-time commission trigger of §6.1) is lowered from 0.35 to **0.25**. **Reason:** G-AD2-18 showed
band mode cannot engage at 0.35 while the learning rate is uncertain (§3.2: the predictive sd floors
near 0.95 logits, and `max P_band >= 0.35` needs about 0.74); the post-hoc diagnostic of §3.2 had
0.25 engaging band mode by answer 15 for 66% of the one-cell learners. This is a change made in the
light of the results, not a pre-registered value: **the results of §3.1 stand as reported at 0.35**,
no other threshold, pass condition, scenario, seed or constant changed, and the gates' pass
conditions are unchanged, so the re-run's figures (§3.4) are reported beside the old ones and every
gate that failed still fails. The code's default, the config default and the defaults snapshots
carry 0.25.

**What ran when.** The exploratory runs before the gate module existed (G-AD2-18's one-cell and
wrong-prior scenarios, a 50-learner G-AD3-7 practice run, G-AD3-11's base and downturn scenarios)
changed nothing registered: A4-A16 were fixed before the runs whose figures §3 reports, all on
`learnloop.sim.ad_gates` at commit `2778e23fe`'s code (A7's sequence included). The diagnostics in
§3.2 were run **after** the gates, are labelled post hoc, and changed nothing. A17 came after all of
them, by owner decision, and its re-run is reported separately (§3.4).

## 2. What was built

Commits on `adaptive-difficulty/ad23` (base `29a49b5e6`): `69bec8228` (plan and
pre-registration), `c57b20577` (the model, both views' replay, the slot draw, the generation
contract, migration 214), `b53128b68` (the `mvp-0.28` successor, the head fixture at 214, the dose
arm, the readiness numbers), `eb8d296d5` (the report, the arms, the dose-and-burden analysis, the
CLI, the re-proposals), `2778e23fe` (every gate test, the simulation gates and the fixes they
found), `1660b0b1e` (the desktop's three call sites), `707c6624e` (the spec's records, the KM and P3
notes, the CLI snapshot, the references), and this file's commit.

- **The model** (`adaptive_difficulty/model.py`, `state.py`, `priors.py`, `outcomes.py`): §5 exactly: a
  bank of Gaussian filters (one per grid point, or learners x points in the simulations) over one
  event skeleton; lazy subject / capability / facet / cell coordinates; the coupled construction by
  regression on the a-priori covariance; the joint factor (32-node Gauss-Hermite on `η` with the
  residual folded in, 5 per link coordinate for `+rating` / `+timing`); learning, reading (four kinds,
  two dose scales, hierarchical `γ̄ + δ`) and verdict (`λ_matched`, `λ_missed`) transitions as linear
  maps; `p̄`, `P_band` (exact through `F_x⁻¹`), `I_c` (24 x 24); §5.3's categories with the explicit
  unknown help timing and the censored factor.
- **The replay** (`replay.py`): both views from the attempt ledger, the frozen serve inputs, the
  reading receipt **only through the firewall's carve-out**, the allowlisted claims at their own time,
  the adopted coupling versions; `ad_state` and `ad_attempt_trace` (DERIVED, one replayer
  `adaptive_difficulty`); `item_forecast_scores` (DERIVED, `scoring.py`, replayer
  `item_forecast_scores`); zero model calls; byte-identical rebuilds; a live cache keyed by a table
  fingerprint.
- **The serving** (`selection.py`, `serving.py`, `daily_plan/ad_slot.py`, `daily_plan/engine.py`,
  `records.py`): the slot support with checks 0-4 re-read at the draw (no exemption for the slot
  item), `ad_select_v1` (band, calibrate, the overlap share, exact propensities, seeds),
  `ad_selections` written before the serve in the serve transaction, `item_substituted` folded into the
  plan record, `item_displaced` with `ad_ineligible` and the AD deferrals in the plan's exclusion set
  (the boundary's context, the projection, a later plan of the day), cleared by the draw's own checks
  at each boundary with the decision recording what it applied and cleared; the commission draw over
  `X_c` (at a serve when the cell pool has no `P_band >= 0.35`, and under the generation contract);
  `ad_commission_results`; the `ad_threshold@subject`, `@subject_uniform` and `@lo` receipts; the
  loadings in force and the coupling version on `item_serve_inputs`; `feature_overlap` and
  `reading_dose` in the randomization layer; the pair propensity `π_router · π_AD` (`π_router = 1`
  for a deterministic chooser).
- **The generation contract** (`generation.py`, `practice_generation.py`): a commissioned `RungTarget`
  (`max` = the point), the band lines and the band check dropped, §7.1's text; the re-forecast of a
  landed commission.
- **The subject view live and readiness** (`readiness.py`, `router/card.py`, `daily_plan/router_card.py`):
  live draws read the subject view with `promoted_predictor` on and the LO's own view with it off; the
  readiness lines with the untested rule; the router card's AD fields (card version `+ad23` only when
  present).
- **Learned relatedness** (`relatedness.py`, `relatedness_jobs.py`, `cli/ad.py`): the proposal on
  `ai.routing.llm_probability_llm` through `SendGuard` and the durable claims, inside the AD day cap
  (owner kind `ad_relatedness`), dry-run first; validation (ids, subject, self, caps); one
  `judgment_ledger` row per loading and coupling; `ad_relatedness_runs` with **per-unit fingerprints, so
  a change re-proposes only the units it touches**; `ad_coupling_versions` (the first adopted applies to
  the whole history; a later one only with `--confirm-reinterpretation` after its in-memory
  `--shadow` report); background re-proposals on the reload, at most 2 subjects a trigger, only for an
  adopted subject; the coupling cap of 3 applied after symmetrizing.
- **Reading** (`attempts/salience_firewall.py`): the rule text names the exception and its four
  limits; `learning_opportunity_events` is the only path, with the allowlist moved there (AD1's sweep
  reads the same list); every existing firewall check and test unchanged.
- **The dose arm** (`dose.py`, sidecar `reader.dose_offer` / `reader.dose_offer_event`, the Reader's
  `DoseOffer`): eligibility, the friction budget, `reading_dose_v1` with exact logged propensities
  before anything is shown, the dose already taken recorded as the moderator, uptake rows; outside the
  successor, switch `reading_dose_offers`.
- **The monitoring and the report** (`monitoring.py`, `arms.py`, `report.py`, `dose_report.py`,
  `learnloop ad report` / `ad eval`): §10.4's arms, field's rule as a monitor, the sequences, the honest
  lines, the seven auto-flags (each naming its switch), identifiability (feature-time correlation,
  aliased directions, contraction, prior sensitivity, the hyperparameter margins, the reading kinds),
  time to usable, trivial successes, commissions, the dose arm, the dose-and-burden analysis (gain per
  event, minutes by NNLS, the practice reference, the useful dose, the randomized offers' effects with
  their dose and level-band moderation, the "helps when" lines, burden, the plain lines), the
  self-check calibration. Read-only, zero model calls.
- **The successor** (`algorithm_versions.py`, `ad_successor_upgrade.py`, `successor.py`, config):
  `mvp-0.28`, `learnloop upgrade --to mvp-0.28` (from `mvp-0.27`, or `mvp-0.9`..`mvp-0.26` through the
  chain; AD's DERIVED state prepared before the rename), the defaults snapshot, the six switches (each
  read only at the tag), the dose arm's switch, every numeric key classified.
- **The simulations** (`sim/ad_synthetic.py`, `sim/ad_gates.py`): synthetic learners, vaults with
  known structure and synthetic readers on the real model and selection rule, the incumbent's ladder on
  the production EKF; every gate's figures (`uv run python -m learnloop.sim.ad_gates [gate ...]`).
- **The desktop** (narrow call sites only): `WhyThisItem` under the practice card's presentation
  (`adaptive_difficulty.why_item`), `DoseOffer` above the Reader's guide rail, `ReadinessLine` on the
  inspector's LO page; four Tauri passthroughs; every new RPC desktop-only.
- **Migration 214**: `ad_selections`, `ad_commission_results`, `ad_dose_offers`, `ad_relatedness_runs`,
  `ad_coupling_versions` (append-only, triggers), `ad_state`, `ad_attempt_trace`, `item_forecast_scores`
  (DERIVED); table roles; the head fixture `migration_head_214` (backup API, rollback mode) and every
  path naming it; the references (head 214, 0 errors).

- **Exam protection (A8), as redesigned on 2026-10-21** (Option B with E1 and E2; record:
  `adaptive-difficulty-ad23-codex-review.md`, "Redesign"). Rounds 8-14 filtered at each reader,
  and every verify found a reader or cache the filter had missed. Now:
  - Every AD entry point runs inside one guarded operation (`operation.py`).
  - While it is open, an SQLite authorizer on every connection to the vault refuses any read of a
    protected table that the material view's rules do not make, any read of the incumbent's derived
    state (except the `mastery_ekf` carve-out), and any write to a table AD does not own.
  - The rules apply one rule over a registry that classifies every column of every protected table
    (`protected_tables.py`).
  - AD and the helpers it calls read a projected vault and document IR, so a held-out block is
    absent, not filtered.
  - One vault-wide protection epoch scopes every artefact and cache computed from that projection.
  - A refusal leaves AD unavailable for that operation, and the incumbent serves.
  - The generator's internals stay governed by the incumbent's exam protection (E1).

### Owner notes (the AD23 redesign)

- **Any protection change resets learned coupling.** Marking or unmarking held-out material, or
  reserving or releasing an exam pool, anywhere in the vault, takes every relatedness run out of
  force. An adopted coupling then has no effect until the subject is proposed and adopted again
  (E2, owner decision 2026-10-21). `learned_coupling` is off by default, so this matters only after
  you adopt a version.
- **Any protection change expires pending background forecasts.** A served item's frozen
  outside-forecast inputs are sent only while protection is unchanged since the serve. After a
  change they are reported `protected` and never sent; the next serve freezes new ones.
- **The same change re-checks items.** At the next trigger, item revisions prepared under the old
  protection are checked again. One already audited and forecast is found current, with no model
  call. One that was protected and is now public is audited and forecast. Still at most 20 visible
  revisions per run; protected ones no longer count towards the 20.
- **Guard denials.** `learnloop ad report` shows `guard.denials`: how many reads or writes the AD
  guard has refused. Each refusal left AD unavailable for that operation, and the incumbent served.
  The details are in `ad_guard_denials.jsonl` beside the vault's database (git-ignored). There is
  no UI notice (owner decision 2026-10-21). Any count above zero is a bug to report.
- **Round 2 (2026-10-21): the reset reaches all of AD's history.** Every AD artefact AD reads back
  now carries the protection epoch it was computed under, and is read only at that epoch. So after
  a protection change:
  - forecast receipts stop feeding scoring and calibration;
  - serve selections leave the report's cohort and windows;
  - frozen serve inputs give way to current-content reconstruction;
  - open commissions close;
  - dose offers stop counting in the budget;
  - reading receipts are swept again at the next serve.

  Rows written before this change carry no epoch, so in a vault where AD has already run none of
  them is ever in force: AD's history there starts afresh.
- **A protection change** now also includes an item moving onto or off held-out material (its
  provenance or canonical exercise), not only marking material and reserving exam pools.

## 3. The gates

### 3.1 Results (all pre-registered conditions; 200 learners or seeds unless stated)

| Gate | Result | Figures |
|---|---|---|
| G-AD2-1..6, 9..13, 15..17 | **pass** | `tests/test_ad2_model.py`, 23 tests |
| G-AD2-7 confound | **pass** | monotone ladder: complexity and transfer labelled confounded in 100% of seeds |
| G-AD2-8 recovery | **pass** | every identified `β` within 2 sd in 91-100% of the seeds where it is identified; the 9 never-varied coordinates prior-dependent in every seed |
| G-AD2-14 censoring | **pass** | within 2 sd in 98.5% of (seed, point) pairs; censored bias -0.0006; dropping assisted attempts +0.021 (one-sided lower bound +0.012) |
| G-AD2-18 one LO, one cell | **FAIL** | band mode by answer 15: **0%** (>= 80%); band hits 16-30: **0.096** (>= 0.35); an oracle bound 0.330 |
| G-AD2-18 wrong prior | **FAIL** | band hits 16-30: **0.093** (>= 0.30); an oracle bound 0.337 |
| G-AD2-18 plan flow | **FAIL (1 of 3)** | band hits 16-30: AD 0.122, incumbent 0.036, no-update 0.122 (both met); trivial successes AD **0.016** > incumbent 0.0 (failed); LO view 0.125 / 0.022; band mode 0% in every arm; an oracle bound 0.325; every cell is first visited in its only block (no seen-cell figures) |
| G-AD2-19..31 | **pass** | `tests/test_ad2_serving.py`, 34 tests |
| G-AD3-1..5, 10, 12..14 | **pass** | `test_ad3_subject_view.py`, `test_ad3_relatedness.py`, `test_ad3_reading.py`, `test_ad3_dose_arm.py`, `test_ad3_monitoring.py`, the carve-out in `test_salience_firewall.py` |
| G-AD3-6 (synthetic part) | **FAIL (24 of 36 points)** | half the weight on the generating point and its neighbours in >= 80% of 25 seeds at 12 points (the `χ_Q = 0.25` column but `2.25/0.75/0.25` and `0.75/0.75/0.25`, and `1.5/0/0`, `1.5/0.5/0`); 0.08-0.76 at the others (edges and corners) |
| G-AD3-7 related faster (practice, correct) | **FAIL (1 of 4)** | mates' first-attempt log loss -0.103 nats against uniform sharing (95% interval -0.130, -0.073: met); unrelated not dragged (met); band mode never engaged on a mate in either arm (the 2-fewer condition failed) |
| G-AD3-7 related faster (reading, correct) | **pass** | mates -0.041 nats (-0.057, -0.025); unrelated -0.010 nats, band hits -0.004 |
| G-AD3-7 unrelated not dragged (noisy, wrong) | **FAIL** | the unrelated LO's first attempt **+0.026** (noisy) and **+0.240** nats (wrong) against uniform (<= 0.02); band hits +0.001 / +0.002 (met) |
| G-AD3-7 a wrong proposal shrinks | **FAIL** | weight on `χ_C = 0` reaches 0.5 within 100 first attempts in **47%** of seeds (>= 80%); the coupling flag within 200 in **0%** (>= 80%); correct proposal: flag in 0% (<= 5%: met) |
| G-AD3-8 (synthetic part) | **FAIL (1 of 3)** | true rise: log loss on - off -0.00098 (interval excludes 0: met); no rise: full effect stays **0.24** (below 0.05 in 0%; >= 90%); flag 0% (met) |
| G-AD3-9 flags | **pass** | fire when worse in 86.5-100% (>= 80%); none fires when nothing is worse in 99% of seeds (>= 95%); each names its switch |
| G-AD3-11 recovery (floor 0.10 and 0.30) | **FAIL** | curves within 2 sd: reading 0.995, tutor 0.90-0.92, worked examples 0.985, **questions 0.725-0.775** (>= 0.90); `n*` within one 99.5-100% (every true `n*` is 0 at the registered minutes); the no-effect kind's full effect below 0.05 in **4.5-6.5%** |
| G-AD3-11 downturn | **FAIL** | downturn found in **0%** (>= 80%); worked-example coverage 0.055 |
| G-AD3-11 confounding (0.10, 0.30) | **pass** | the offer's 95% interval covers 0 in 93-94.5%; "tested" in 0-2% |
| G-AD3-15 (1)-(5) | **pass** | `tests/test_ad3_reading.py` |
| G-AD3-15 (6) | **FAIL (1 of 2)** | misses predicting cold failure: `λ_missed` -0.42, interval excluding 0 in 100% (met); no signal: |mean| 0.07, sd 0.12 (ok in 0%; >= 90%) |

The failing conditions are strict xfails in `tests/test_ad23_sim.py` with these figures, so the
suite stays readable and the marker turns red the day a gate passes. **The successor should not
merge on these results**: the owner decides what changes (§3.3). *(The owner decided on 2026-10-19:
merge with fixes, the failing gates kept as monitors; §3.4.)*

### 3.2 Why (diagnostics run after the gates, post hoc; nothing changed on them)

- **G-AD2-18: band mode cannot engage while the learning rate is uncertain.** `P_band <= 2Φ(w/2s) - 1`
  with `w = F⁻¹(0.80) - F⁻¹(0.70) = 0.671`: band mode (`max P_band >= 0.35`) needs the predictive sd
  `s <= 0.74` at a well-centred point. With `γ` a persistent latent coordinate (prior sd 0.1), the
  uncertainty of the cumulative learning enters as `t²·Var(γ | data)`: the median best-point sd floors
  at 0.93-0.97 after 9-15 answers (0.64 with the learning transition removed). On the same 200
  learners: `γ` known in the filter: band mode by 15 for 36%; `γ` known and the truth's `γ` fixed at
  0.2: 39%; `calibrate_below = 0.25`: 66%; no learning in truth or filter: 30%. Band hits stay
  0.09-0.21 in every variant.
- **G-AD2-18: the registered pools cannot reach most learners' band.** The prior's spread (`θ - α`
  sd 1.8) exceeds `X_c(retrieval)`'s demand range (-0.5 to 1.5 at the prior means): an oracle that
  always served the best pool point would land in the band on only **0.330** of answers 16-30, below
  the 0.35 threshold. §5.9's arithmetic assumed a point in the band always exists.
- **G-AD3-11, G-AD3-8, G-AD3-15 (6): one learner's reading data move the curves little.** After 5000
  windows the posterior sd of a kind's coefficients is 0.07 / 0.12 against the priors' 0.10 / 0.14:
  each window's answer has about 0.12 nats of information about the facet's level, which the LO's own
  offset (variance 1.5) mostly absorbs, and a section read every window is collinear with the practice
  increment. Truths far from the prior means (a no-effect kind, the downturn, a flat verdict term) stay
  near the prior; truths near them pass.
- **G-AD3-7: coupling helps the mates' first attempts but drags an unrelated LO under a wrong
  proposal, and the mixture does not unlearn it fast.** The mates' first attempts improve by 0.10 nats
  with the correct proposal (0.12 noisy, 0.01 wrong). With the wrong proposal the unrelated LO's first
  attempt is 0.24 nats worse; over 100 first attempts the weight on `χ_C = 0` passes 0.5 for only 47%
  of learners, and the mixture's predictions move toward uniform sharing so the arms' difference
  shrinks below what the sequence can separate (the flag never fires).
- **G-AD3-6: one learner identifies the grid's edges weakly.** Interior points pass; corners (where
  "neighbours" are 8 of 36 points) and the `χ_Q = 0.5` / `χ_C = 0.75` edges do not.

### 3.3 Options for the owner (none taken)

1. **Accept the figures as monitoring**: merge with `selection` on (calibrate mode serves acceptable,
   informative items; the incumbent's band hits are lower still, 0.036) and read the AD report.
2. **Give band mode a reachable target**: lower `calibrate_below` (0.25 engaged band mode by answer 15
   for 66% in the one-cell scenario), or treat `Var(γ)` as the §5.9 "fresh noise" approximation
   (a changed `ad_priors_v1`: a successor-level change of persisted meaning).
3. **Widen the commission ladder**: `X_c` from the whole default trajectory's envelope (and scaffolding
   `worked`), so a pool can reach the band for learners far from the prior mean.
4. **Re-pre-register the simulation gates** with figures the model can meet (as a later, separately
   recorded registration; the present results stand as reported).
5. **Coupling safeguards**: a smaller `χ_C` grid cap, or the coupling flag on a sequence with a smaller
   `n0`; or keep `learned_coupling` off until the owner's backfill is spot-checked.

### 3.4 The owner's decision and the re-run at `calibrate_below = 0.25` (2026-10-19)

**Owner decision 2026-10-19:** "Merge with fixes, option 1 + option 2 + option 5 of §3.3. The successor merges with `selection` on, and the failing gates are kept as monitors: their strict xfails stay, with the figures. Lower `calibrate_below` to 0.25. Record it as a NEW, separately recorded pre-registration amendment, made after the reported results, with the reason. The earlier results stand as reported. Re-run `python -m learnloop.sim.ad_gates` and record the new G-AD2-18 figures beside the old ones. Don't change any other threshold. `learned_coupling` defaults to OFF until the owner has spot-checked the relatedness proposal. Update the defaults, the snapshots, the docs and the owner-run commands: show how to turn it on after adopting a coupling version."

**What was done.** The successor keeps `selection` on; every failing condition keeps its strict xfail
in `tests/test_ad23_sim.py`, its reason now citing the figures at 0.25. `calibrate_below` is 0.25
(amendment A17, §1.9) in `SelectionConstants`, the config schema and the 20 defaults snapshots.
`learned_coupling` is `false` by default (option 5); §8 shows how the owner turns it on after
adopting a coupling version. No other threshold changed.

**The re-run** (`uv run python -m learnloop.sim.ad_gates`, every gate but G-AD3-6, which draws ladder
points uniformly and has no selection step; same seeds, 200 learners or seeds). G-AD2-18 beside the
§3.1 figures:

| G-AD2-18 scenario | condition | §3.1 (0.35, as registered) | at 0.25 (A17) | result |
|---|---|---|---|---|
| one LO, one cell | band mode by answer 15 (>= 80%) | 0% | **66.0%** | fail |
| | band hits, answers 16-30 (>= 0.35) | 0.096 | **0.105** | fail |
| | band hits 1-15; band-mode share; trivial successes | not reported | 0.141; 0.211; 0.279 | |
| | oracle bound, 16-30 | 0.330 | 0.330 | |
| wrong prior | band hits, answers 16-30 (>= 0.30) | 0.093 | **0.110** | fail |
| | band mode by answer 15 | not reported | 67.5% | |
| | oracle bound, 16-30 | 0.337 | 0.337 | |
| the plan's flow | AD's band hits 16-30 >= the incumbent's (0.036) | 0.122 | **0.122** | met |
| | AD's >= no-update's (0.122) | 0.122 | **0.122** (0.12200 >= 0.12167) | met |
| | AD's trivial successes <= the incumbent's (0.0) | 0.016 | **0.018** | fail |
| | LO view: band hits; trivial successes | 0.125; 0.022 | 0.123; 0.022 | |
| | band-mode share: subject view; LO view | 0%; 0% | 6.7%; 3.1% | |
| | own answers before band mode (median, per cell) | never | never, but `f2:retrieval` 4 in the subject view | |

Band mode now engages for two thirds of learners, but the band-hit rate barely moves: once engaged,
the predictive sd at the served point is near the 0.74 limit and the registered pools reach the band
for only a third of answers (the oracle bound, unchanged). The other gates keep their pass or fail
(the strict xfails hold); the figures of the gates that run the selection rule moved slightly:
G-AD3-7 practice, correct: mates -0.101 nats (-0.128, -0.073; was -0.103), the 2-fewer condition still
failing (the pooled median is unreached in both arms); noisy: unrelated +0.026 (unchanged); wrong:
unrelated +0.230 (was +0.240); the shrink (47%, 0%), G-AD3-8 (0.24), G-AD3-9 (86.5-100%, 99%) and
G-AD3-15 (6) (-0.42; 0.07, 0.12) figures as in §3.1, and G-AD3-11's conditions pass and fail as there. The full output is the run's JSON lines (20 gates, 7.5 min on a machine shared with another
stage).

The other decisions of the same day (F8 accepted as built, F5's commission expiry, the final
verify's F11, the history fallback) are recorded with their tests and gate in
`adaptive-difficulty-ad23-codex-review.md`, "Final verify and the owner's decisions".

## 4. Deviations (each recorded; the conservative option where the spec and the code disagree)

1. **Eligible attempt types** add `hinted_attempt` and `dont_know` to §5.6's four (the practice screen
   records a hinted answer and an old "I don't know" as such; a hint is then help timing, §5.3).
2. **History needs the field's fallback**: a historical attempt resolves `exact` only where the field
   finds its graded revision; on the committed `linear_algebra` snapshot every one of 62 historical
   attempts is `excluded` unless `field.legacy_fallback = "current_content"` (then 31 eligible). The
   owner decides per vault (open question 4). *Resolved 2026-10-19 (open question 4): AD's own
   `adaptive_difficulty.history_fallback`, `"current_content"` by default; field's default unchanged.*
3. **No Reader surface grades an in-passage answer as an attempt** at this base, so the replay never
   sets the "in place of `γ`" path; the model's path is tested (`test_an_in_passage_answer_graded...`).
4. **`λ` at its prior mean** (G-AD3-15 (1)): a latent `λ ~ N(0, 0.3²)` adds `0.09·D²` of variance even
   at mean 0, so "equal to D20's exactly" holds for the mean and, exactly, with `λ`'s spread at 0; the
   test pins that. With the spread, a verdict widens the prediction slightly (open question 5).
5. **`ad_relatedness_runs` and `ad_coupling_versions`** are tables §11.2 did not list (the run receipt
   with per-unit fingerprints; the adopted versions); §11.2 is amended.
6. **A later coupling version** is refused unless `--confirm-reinterpretation` after its `--shadow`
   report (computed in memory; the playbook's shadow rebuild for a reinterpretation).
7. **Readiness reads the default target**: no goal ladders or exam targets exist before AD4, so
   "Ready for exam level" is "Top level for this goal" on the default ladder (§9.5's last paragraph).
8. **The router card's AD fields** omit "demonstrated level / K" (AD4's).
9. **`dose_floor <= 1/3`** in the config (three feasible variants must keep a distribution); the spec
   says so.
10. **The dose arm's decision point** is a section the Reader marks completed (the Reader's own
    boundary), not a separate boundary event; the cue-density and skim conditions are the Reader's.
11. **Moderators**: the "helps when" lines use the predicted level band, the tutor exchange's answer
    mode and the question's style from the replay's per-subkind doses; the randomized offers moderate
    by level band and dose taken.
12. **The simulations live in `learnloop.sim`** with five justified entries in the frozen-cycles
    contract's ignore list (leaf modules nothing in the runtime imports).

## 5. Fail-first

Run against the base tree (`git archive 29a49b5e6` with the new test files, in its own rootdir,
`-o pythonpath=src`): the nine new test files fail at collection (`cannot import name 'priors' /
'model' / 'replay' ... from 'learnloop.adaptive_difficulty'`: no model, state, replay, serving,
relatedness, dose arm, report or successor existed); in `tests/test_salience_firewall.py` the 5474
carve-out cases and the two new tests fail (`module 'learnloop.attempts.salience_firewall' has no
attribute 'learning_opportunity_events'`) while the **62 existing tests pass unchanged**.

## 6. Gate (this step; owner rule 2026-10-17: no full suite here)

- `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2`; `TMPDIR = fixtures-local/tmp`.
- `uv run lint-imports --no-cache`: **27 kept, 0 broken** (the frozen-cycles contract gains five
  justified ignores for the simulation modules).
- **Targeted pytest** (`uv run pytest -n auto`, 186 files: every new or changed test file, every file
  that names a changed module or function, and the contract pins): **9468 passed, 36 xfailed, 1 failed**
  in 21 min 35 s. The failure (`test_mvp017_route_check_replay.py::test_an_mvp017_vault_replays_its_grades_exactly`:
  a rebuild below the tag wrote `ad_state` rows) was fixed in `f54909bc1` with a test that fails on the
  previous tip (`test_below_the_tag_a_rebuild_writes_no_ad_state`); rerun after the fix:
  `test_mvp017_route_check_replay.py`, `test_ad23_successor.py`, `test_ad2_model.py`,
  `test_ad3_subject_view.py`, `test_ad3_relatedness.py`, `test_rebuild_orchestrator.py`,
  `test_shadow_rebuild.py`: **63 passed**. The 36 xfails are the strict xfails of §3.1. The file list is at
  the end of this file.
- The AD2+AD3 files alone: `test_ad2_model.py` 23, `test_ad2_serving.py` 34, `test_ad23_sim.py` 56
  (20 passed, 36 strict xfails, 5 min at `-n 6`), `test_ad23_successor.py` 11, `test_ad3_dose_arm.py` 12,
  `test_ad3_monitoring.py` 5, `test_ad3_reading.py` 10, `test_ad3_relatedness.py` 7,
  `test_ad3_subject_view.py` 8, `test_ad23_migration.py` 4, `test_salience_firewall.py` 5536 (62 of them
  the unchanged existing tests).
- **Durability lane** (`-m durability`): `test_ad23_migration.py`, `test_ad1_migration.py`,
  `test_approach_maps_schema.py`, `test_help_assists_schema.py`, `test_library_asks_migration.py`:
  **5 passed** (214's FK check and rollback-mode head fixture in `test_ad23_migration.py`).
- **Frontend** (`apps/learnloop-tauri`): `npm install`; `npm run typecheck` clean; vitest on the three
  new files and everything they touch (`src/screens/ReaderScreen*`, `src/screens/PracticeScreen*`,
  `src/components/InspectorOverlay*`, `src/screens/reader`, `src/screens/practice`,
  `src/components/ReadinessLine*`, `src/api`): **67 files, 515 passed**; `npm run frontend:build` ok.
- `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml`: ok (four passthroughs).
- **References**: `db_generate_reference.py` then `db_validate_reference.py`: **0 errors** (head 214,
  341 table notes, 926 configuration leaves; the two prose counts updated).
- CLI help snapshot regenerated (`ad report`, `ad eval`, `ad relatedness`, `upgrade --to mvp-0.28`).
- **Simulations**: `uv run python -m learnloop.sim.ad_gates` and `... G-AD3-6` on the final code: the
  figures of §3.1 (13 min and 4 min on a machine shared with another stage).
- **Model calls: 0.** Every model-backed path is tested with fakes; the copies below ran with every
  route off.

## 7. Files

New: `src/learnloop/sim/ad_synthetic.py`, `src/learnloop/sim/ad_gates.py`; in `adaptive_difficulty/`
`model.py`, `state.py`, `priors.py`, `outcomes.py`, `replay.py`, `scoring.py`, `selection.py`,
`serving.py`, `predict.py`, `generation.py`, `relatedness.py`, `relatedness_jobs.py`, `dose.py`,
`dose_report.py`, `readiness.py`, `monitoring.py`, `report.py`, `arms.py`, `successor.py`;
`src/learnloop/ad_successor_upgrade.py`, `src/learnloop/daily_plan/ad_slot.py`,
`src/learnloop/db/stores/ad_serving.py`, `src/learnloop_sidecar/handlers/adaptive_difficulty.py`,
`migrations/214_adaptive_difficulty_serving.sql`, `fixtures/migration_head_214/` (renamed from 213);
frontend `screens/practice/WhyThisItem.tsx`, `screens/reader/DoseOffer.tsx`,
`components/ReadinessLine.tsx` with their tests; tests `ad23_fakes.py`, `test_ad2_model.py`,
`test_ad2_serving.py`, `test_ad23_sim.py`, `test_ad23_successor.py`, `test_ad23_migration.py`,
`test_ad3_dose_arm.py`, `test_ad3_monitoring.py`, `test_ad3_reading.py`, `test_ad3_relatedness.py`,
`test_ad3_subject_view.py`; the eight new table notes of the references.
Changed: `attempts/salience_firewall.py` (rule text, the carve-out), `adaptive_difficulty/reading.py`
(the list from the firewall, a taken offer's id), `serve.py`, `spend.py`, `backfill.py`;
`daily_plan/engine.py`, `records.py`, `router_card.py`; `router/card.py`;
`content/authoring/practice_generation.py`; `scheduling/randomization_layer.py`;
`algorithm_versions.py`, `config/schema.py`, `config/template.py`, `params/parameter_registry.py`,
`cli/app.py`, `cli/ad.py`, `ai/routing.py`, `ai/disclosures.py`, `db/table_roles.py`,
`substrate/rebuild_orchestrator.py`, `learnloop_sidecar/context.py`, `handlers/__init__.py`;
frontend `api/client.ts`, `api/dto.ts`, `PracticeScreen.tsx` (one line), `ReaderScreen.tsx` (one
block), `InspectorOverlay.tsx` (one line), `src-tauri/src/commands.rs`, `main.rs`; `pyproject.toml`
(contracts); tests `test_salience_firewall.py` (appended), `test_architecture.py`,
`test_mobile_allowlist.py`, `test_ad1_migration.py` and the sibling migration tests, the `mvp-0.10` ..
`mvp-0.24` upgrade tests and others pinning the chain's last link, `cli_help_snapshot.json`; specs
`spec_adaptive_difficulty_v1.md` (§5.9 finding, §11.2 two receipts, §11.4 dose floor, §17 Q8),
`spec_knowledge_model.md` §8.3 and `spec_p3_reader_integration.md` §8.2, §15.4 (dated notes); the
regenerated references.

## 8. Owner-run commands (on a backup copy; dry-run first; never on the working vaults)

From the main checkout after the branch is available, with the vault at `mvp-0.29` (the owner's chain: `--to mvp-0.9`, `--to mvp-0.27`, `--to mvp-0.29`, then this):

```bash
# 0. a backup-API copy of the vault
uv run python -c "from pathlib import Path; from learnloop.db.copies import copy_tree_with_databases as c; c(Path('fixtures/linear_algebra'), Path('fixtures-local/la_ad23'))"
# 1. the successor on the copy (AD's DERIVED state is prepared before the rename; no model call)
uv run learnloop upgrade --vault fixtures-local/la_ad23 --to mvp-0.30
# 2. AD1's reading backfill if not yet run (the report's reading lines need it), dry-run first
uv run learnloop ad backfill --vault fixtures-local/la_ad23 --reading --dry-run --json
uv run learnloop ad backfill --vault fixtures-local/la_ad23 --reading
# 3. the AD2/AD3 report: dry-run first, then the report (read-only, no model call, about a second)
uv run learnloop ad report --vault fixtures-local/la_ad23 --dry-run --json
uv run learnloop ad report --vault fixtures-local/la_ad23
uv run learnloop ad report --vault fixtures-local/la_ad23 --json > ad23-report.json
#    AD reads the history through its own current-content fallback by default (owner decision
#    2026-10-19; adaptive_difficulty.history_fallback); field.legacy_fallback is not needed. To compare
#    without it, on a second copy only, set it to "exclude" and run the report again:
#    uv run python -c "from pathlib import Path; from learnloop.ops.settings_store import apply_config_updates as a; a(Path('fixtures-local/la_ad23_exclude/learnloop.toml'), {('adaptive_difficulty', 'history_fallback'): 'exclude'})"
# 4. the relatedness proposal. learned_coupling is OFF by default (owner decision 2026-10-19) and the
#    proposal runs only with it on, so turn it on in the copy first (tomlkit keeps the file's other keys):
uv run python -c "from pathlib import Path; from learnloop.ops.settings_store import apply_config_updates as a; a(Path('fixtures-local/la_ad23/learnloop.toml'), {('adaptive_difficulty', 'learned_coupling'): True})"
#    dry-run first (one call per subject on ai.routing.ad_relatedness), then the proposal alone,
#    with no adoption: spot-check its loadings and couplings in the JSON (and in judgment_ledger,
#    task ad_relatedness) before adopting
uv run learnloop ad relatedness --vault fixtures-local/la_ad23 --dry-run --json
uv run learnloop ad relatedness --vault fixtures-local/la_ad23 --json > ad23-relatedness.json
# 4b. after the spot-check: adopt the first coupling version
uv run learnloop ad relatedness --vault fixtures-local/la_ad23 --adopt
# 4c. only then turn learned_coupling on in the vault you use (the same one-liner with its own path);
#     until then the subject view stays at its uniform-sharing points and no proposal is ever sent
uv run python -c "from pathlib import Path; from learnloop.ops.settings_store import apply_config_updates as a; a(Path('<vault>/learnloop.toml'), {('adaptive_difficulty', 'learned_coupling'): True})"
# 5. later, a reinterpretation: its shadow report first, then the confirmed adoption
uv run learnloop ad relatedness --vault fixtures-local/la_ad23 --shadow --json
uv run learnloop ad relatedness --vault fixtures-local/la_ad23 --adopt --confirm-reinterpretation
# 6. the playbook's shadow rebuild against the predecessor and with the six switches off
uv run learnloop rebuild --shadow --json --vault fixtures-local/la_ad23 --set algorithms.algorithm_version=mvp-0.29
uv run learnloop rebuild --shadow --json --vault fixtures-local/la_ad23 \
  --set adaptive_difficulty.selection=false --set adaptive_difficulty.generation_contract=false \
  --set adaptive_difficulty.promoted_predictor=false --set adaptive_difficulty.learned_coupling=false \
  --set adaptive_difficulty.reading_opportunities=false --set adaptive_difficulty.reading_self_check=false
# the simulation gates' figures (no vault, no model)
uv run python -m learnloop.sim.ad_gates
```

Running the proposal again with `--adopt` after the spot-check proposes nothing new (only units whose
fingerprint changed are re-proposed) and adopts what is in force. The relatedness proposal is the
stage's only paid call: one per subject on its own route `ai.routing.ad_relatedness` (since the compose
onto T1, C4: the ChatGPT plan's `chatgpt_medium` tier by default; it used to ride the field harness's
`llm_probability_llm`), inside
`adaptive_difficulty.daily_spend_cap_usd` ($0.50); a metered route needs
`adaptive_difficulty.price_per_million` or is refused before sending. After adoption, a reload
re-proposes only the units whose content changed (at most 2 subjects a trigger).

## 9. On a backup copy in this stage (no model call)

A backup-API copy of the worktree's tracked `fixtures/linear_algebra` (the committed snapshot,
`mvp-0.8`, rewritten to `mvp-0.27` for the test) in `fixtures-local/`, every model route off
(`outside_forecasters = []`, `feature_audit = false`, hints' outcome placement and map builds off,
embeddings off, learner-text gaps off), API-key variables unset, empty `HOME` / `CODEX_HOME` /
`LEARNLOOP_CONFIG_DIR`, `LEARNLOOP_AD_MODELS=off`:

- `learnloop upgrade --to mvp-0.28`: ok (82 s on the shared machine).
- **Shadow rebuilds** (`learnloop rebuild --shadow`), live database unchanged in each: the default
  successor, the candidate at `mvp-0.27`, and the six switches off. The learner-state deltas (facet
  recall, mastery, schedule against the copy's pre-upgrade state) are **identical** between `mvp-0.28`
  and `mvp-0.28` with the switches off, and identical to `mvp-0.27`'s once the version stamp is set
  aside (61 semantic changes each, the copy's own drift since August); the AD replayers ran in each.
- `learnloop ad report`: dry run, then the report, about 1 s. Every historical attempt is `excluded`
  (no exact revision on this snapshot); with the field's fallback on the copy, 31 eligible:
  `@subject` log loss 0.544 (first attempts at a new LO 0.538, n 8), `@lo` 0.563 (0.726), `mastery_ekf`
  0.759 (n 28), `lo_general` 0.824; every honest line "can't tell yet"; no flag fires; the split's
  posterior leans to 2.25 (0.51); no reading opportunities (the AD1 backfill not run on the copy).
- The copy was removed afterwards.

## 10. Open questions (default taken in brackets)

1. **The failed simulation gates (§3).** [The successor does not merge on them; the owner picks among
   §3.3's options or re-pre-registers.]
   **Owner decision 2026-10-19:** "Merge with fixes, option 1 + option 2 + option 5 of §3.3. The successor merges with `selection` on, and the failing gates are kept as monitors: their strict xfails stay, with the figures. Lower `calibrate_below` to 0.25. Record it as a NEW, separately recorded pre-registration amendment, made after the reported results, with the reason. The earlier results stand as reported. Re-run `python -m learnloop.sim.ad_gates` and record the new G-AD2-18 figures beside the old ones. Don't change any other threshold. `learned_coupling` defaults to OFF until the owner has spot-checked the relatedness proposal. Update the defaults, the snapshots, the docs and the owner-run commands: show how to turn it on after adopting a coupling version." Done: §3.4 (the re-run's figures), amendment A17 (§1.9), §8 (turning `learned_coupling` on).
2. **A1** (G-AD2-1's thresholds amended before any test, §1.9). [As amended.]
3. **A3** ("never labels tested" at most 5% of seeds). [As amended.]
4. **History through the field's fallback** (deviation 2). [Off: a historical attempt without an exact
   revision is excluded, so AD's state starts from the attempts served since AD1.]
   **Owner decision 2026-10-19:** "History fallback. AD reads historical attempts through the current-content fallback by default, so the owner's vaults start with usable history. First check what `field.legacy_fallback` controls beyond AD. If it affects anything outside AD (the field harness or other projections), DON'T change the field default. Add an AD-scoped setting, e.g. `adaptive_difficulty.history_fallback = "current_content"`, that AD's replay reads, and leave the field's default unchanged. Classify the new key in the parameter registry. Record what it means: historical attempts are read against today's item text where the exact revision wasn't saved." Done: `field.legacy_fallback` also drives the field harness (`learnloop field`,
   `success-head`, `eval`) and field's DERIVED facet-outcome view (`rebuild_outcome_view`), so its
   default stays `"exclude"`. AD has its own key, `adaptive_difficulty.history_fallback`
   (`"current_content"` by default, `"exclude"` to leave such attempts out), read by AD's replay
   (`replay.load_events`) and by the AD report's field comparators (so every arm is scored on the same
   past); AD1's forecast receipts and data check keep field's setting. **What it means:** a historical
   attempt whose exact item revision was not saved is read against today's item text
   (`reconstructed_current`). The key is classified in the parameter registry (decision, constraint).
5. **`λ`'s spread at its prior mean** (deviation 4): a verdict widens the prediction slightly before
   the term is learned. [Kept: the priors are §5.5's; the mean is D20's exactly.]
6. **The dose arm live by default** (D21). [On, with `dose_floor = 0.10`, three a day.]
7. **Background re-proposals after adoption** (§5.10 "When"). [On after the owner's `--adopt`; nothing
   runs before it.]
8. **`promoted_predictor` on by default given G-AD3-7's drag under a wrong proposal.** [On, per D3; the
   coupling only exists after the owner adopts a proposal, and `learned_coupling = false` removes it.]
   Answered by the owner decision of 2026-10-19 under question 1 (option 5): `promoted_predictor` stays
   on and `learned_coupling` is off by default until the owner has spot-checked the proposal.
9. **Readiness on the default target until AD4** (deviation 7). [Default target, labelled "Top level for
   this goal".]

## 11. Friction notes for AD4 and AD5

- **AD4 (levels).** The ladders (`ad_ladder_v1`: `entry_point`, `default_target`, `ladder`,
  `ladder_id`, `feature_level`, `point_key`) live in `adaptive_difficulty/selection.py`; AD4's A11
  contract forbids certification from importing the AD package, so move them to a neutral module
  (beside `curriculum/depth_rungs.py`) first. The readiness lines and the router card's fields read the
  default target and omit "level / K"; AD4 adds both. `S.within_envelope` is the default trajectory's
  envelope, which also bounds `X_c`.
- **AD4 / exam targets.** `t_c` (§9.5) is not built; `readiness.py` and `commission_candidates` take a
  `targets` list ready for it.
- **AD5 (probes).** `q_h` needs the truncated expectation over at most two linear functionals of the
  live view's Gaussian state (`serving.view_for` picks the view; `View.cell_vector`, `point_moments` and
  `cell_information` are the building blocks); the snapshot's `ad_composition` block is not built.
- **Simulation cost.** A 36-point bank over 200 learners is about 7200 rows; the gate module chunks by
  50 learners and computes `I_c` only on the overlap set. Banks are exact under marginalization of
  coordinates no later event reads (`Bank.marginalize`).
- **Time to usable** is the binding finding (§3.2): any AD4/AD5 work that leans on band mode inherits it.

**The targeted run's 186 files:** test_ad1_codex_rereview_fixes.py, test_ad1_codex_review_fixes.py, test_ad1_fix_round4.py, test_ad1_fix_round9.py, test_ad1_migration.py, test_ad1_outside_and_cli.py, test_ad1_reading_opportunities.py, test_ad1_send_guard.py, test_ad23_migration.py, test_ad23_sim.py, test_ad23_successor.py, test_ad2_model.py, test_ad2_serving.py, test_ad3_dose_arm.py, test_ad3_monitoring.py, test_ad3_reading.py, test_ad3_relatedness.py, test_ad3_subject_view.py, test_adaptive_difficulty_ad1.py, test_ai_config.py, test_ai_tool_isolation.py, test_approach_map_replay.py, test_approach_maps_schema.py, test_architecture.py, test_assumed_known.py, test_block_chooser_interface.py, test_card_lineage.py, test_chatgpt_plan_provider.py, test_chatgpt_plan_workspace.py, test_cli_help_snapshot.py, test_config_refactor.py, test_constraint_engine.py, test_contract_commissioning.py, test_coordinated_migrations.py, test_daily_plan_build.py, test_daily_plan_composition.py, test_daily_plan_kill_switch.py, test_daily_plan_owner_decisions.py, test_daily_plan_reentry.py, test_daily_plan_replay.py, test_daily_plan_review_regressions.py, test_daily_plan_rpc.py, test_decider_client.py, test_decider_landing.py, test_desktop_rpc_contract.py, test_diagnosis_context.py, test_diagnosis_history_modes.py, test_diagnosis_input_provenance.py, test_diagnosis_replay.py, test_diagnostic_pack.py, test_difficulty_band_guards.py, test_embedding_store.py, test_eval_harness.py, test_evsi_router_composition.py, test_evsi_staged_binding.py, test_exam_protection_landing.py, test_exam_protection_review.py, test_facet_diagnostics_v03.py, test_facet_identity_actions.py, test_family_memory_projection.py, test_field_config.py, test_forecast_receipts.py, test_forecast_receipts_landing.py, test_goal_scope_material.py, test_grading_cli.py, test_held_grade_composition.py, test_held_grade_evidence.py, test_help_assists_schema.py, test_hint_feedback_widening.py, test_hint_telemetry.py, test_ingest_instrument_gates.py, test_ingest_runner.py, test_intervention_outcomes_replayer.py, test_item_fingerprints.py, test_judge_routes.py, test_kinship_feature.py, test_km2_activation.py, test_learner_pick_proposal.py, test_learner_text_gaps_flow.py, test_learner_text_source_widening.py, test_library_ask.py, test_library_asks_migration.py, test_mcp_c1a_landing.py, test_mcp_c1a_narrow.py, test_mcp_tools.py, test_method_explicit_landing.py, test_method_explicit_upgrade.py, test_migrations.py, test_mobile_allowlist.py, test_mvp010_upgrade.py, test_mvp011_upgrade.py, test_mvp013_upgrade.py, test_mvp014_upgrade.py, test_mvp015_upgrade.py, test_mvp016_upgrade.py, test_mvp017_route_check_replay.py, test_mvp017_upgrade.py, test_mvp018_upgrade.py, test_mvp020_upgrade.py, test_mvp021_upgrade.py, test_mvp022_upgrade.py, test_mvp023_upgrade.py, test_mvp024_upgrade.py, test_mvp09_upgrade.py, test_open_world_gate.py, test_openai_embedding_client.py, test_p0_cutover_mvp08.py, test_p3_journeys.py, test_persona_gate.py, test_pfc_unassessed_readers.py, test_pfc_unverified_unassessed.py, test_plan_determinism.py, test_plan_determinism_landing.py, test_practice_index_dossiers.py, test_practice_item_quality_gates.py, test_practice_leakage.py, test_predictor_interface.py, test_probability_arms.py, test_probability_cli.py, test_probability_prep.py, test_project_cli.py, test_project_experiment_store.py, test_project_probes.py, test_project_report.py, test_randomization_layer.py, test_reader_active_reading.py, test_reader_activity.py, test_reader_authoring.py, test_reader_cues.py, test_reader_dialogue.py, test_reader_formative_texts.py, test_reader_intent.py, test_reader_progression.py, test_reader_recap_review_r3.py, test_reader_reconstruct.py, test_reader_restoration.py, test_reader_workbench_rw2a.py, test_reading_step_switch.py, test_rebuild_orchestrator.py, test_recall_coverage_interventions.py, test_recurrence_commands.py, test_recurrence_live.py, test_recurrence_merge_composition.py, test_registry_audit.py, test_regrade_contract_replay.py, test_regrade_contract_successor.py, test_regrade_contract_upgrade.py, test_required_method_authority.py, test_required_method_grading.py, test_reread_safety_landing.py, test_route_rules_in_grader.py, test_router_card.py, test_router_coldness_covariates.py, test_router_g1_feasibility.py, test_router_g4_restraint.py, test_router_g7_fallback.py, test_router_offer_log.py, test_router_outcomes.py, test_router_presentations.py, test_router_r1_composition.py, test_router_r2a_landing.py, test_router_r2a_serving.py, test_router_r2b_serving.py, test_router_r2c_retrieval.py, test_router_r2c_teach_back.py, test_router_why_copy.py, test_salience_firewall.py, test_sensitivity_certificates.py, test_serve_eligibility.py, test_serve_eligibility_review.py, test_shadow_rebuild.py, test_sidecar_serializer_snapshot.py, test_source_block_fts.py, test_sqlite_wal_lifecycle.py, test_stuck_prompt.py, test_stuck_prompt_replay.py, test_success_head_cli.py, test_table_roles.py, test_tier1_decider.py, test_tracked_fixture_databases.py, test_tutor_promotion_w2.py, test_ux_phase4_feedback.py, test_ux_phase4_landing.py, test_voi_merge_composition.py, test_voi_stopping.py, test_voi_v2.py.


## Compose round (main 558e85ab1)

Before the landing, main (`558e85ab1`: DL2, RW3b, RW4d, RW4e, RW5a, RW7a, RW2c and UX2 since the
branch base `29a49b5e6`) was merged into `adaptive-difficulty/ad23` with `git merge --no-ff main`
(no rebase; merge commit `bf930ea08`), and every conflict was composed so both sides survive.

**The merge.** 521 conflicted paths: 333 generated reference tables and 62 configuration notes
(main's side taken, then regenerated), the head fixtures, 36 tests, 8 source files, 5 desktop-app
files and 3 docs. The source compositions:

- `algorithm_versions.py`: DL2's `INTENT_ALGORITHM_VERSION = "mvp-0.29"`, then AD's
  `ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION = "mvp-0.30"`; the chain ends `..., mvp-0.27, mvp-0.29,
  mvp-0.30` and stays linear; both version sets are kept.
- `config/template.py`: main's note on every defaults snapshot with AD's line ("AD2+AD3's
  `[adaptive_difficulty]` switches and constants move it too"), the mvp-0.29 entry and AD's mvp-0.30
  entry; every fingerprint recomputed from the composed defaults with
  `defaults_fingerprint_for_version` (21 versions, 0 mismatches).
- `daily_plan/staged_frame.py` and `scheduling/frame_constraints.py`: main's `evaluate_mandatory`
  (DL2 moved it to its own module) gains AD's `item_states` reader, passed through from the staged
  frame, so the frame reads AD's item states rather than the repository's own read.
- `daily_plan/engine.py`: the plan view keeps AD's `ad_deferred` and DL2's `intent_views`.
- `ai/routing.py`: main's routes and AD's `ad_relatedness`.
- Desktop app: `commands.rs`, `main.rs` and `client.ts` carry both sides' passthroughs; `dto.ts` both
  sides' types; `PracticeScreen.tsx` AD's "why this item" beside DL2's check-on-your-own locator.

**The successor renumber.** AD2+AD3 lands as `mvp-0.30` with predecessor `mvp-0.29` (orchestrator
decision at the DL2 landing; `mvp-0.28` is never used). `ad_successor_upgrade.upgrade_to_mvp030`
(`PREDECESSOR = INTENT_ALGORITHM_VERSION`) chains earlier versions through DL2's
`upgrade_to_mvp029`. `learnloop upgrade --to mvp-0.30` is the CLI's new default. The help text,
docstrings, `adaptive_difficulty/successor.py`, `config/schema.py`, `ai/disclosures.py`,
`content/authoring/practice_generation.py`, the parameter registry note, every AD test, the
latest-version assertions (`test_intent_codex_rereview`, `test_serve_eligibility_review`,
`test_regrade_contract_upgrade`, `test_recurrence_commands`, the mvp-0.14..0.23 upgrade tests),
`Algorithm Versions and Reproducibility.md` (a `mvp-0.30` row; every successor set reaches it) and
this review's current-state lines and owner commands were all renamed. Historical records in this
review (the round logs, the backup-copy run in §9) keep `mvp-0.28`, which is what ran then.
`test_ad23_successor` gains the owner's chain from `mvp-0.8`: `--to mvp-0.9`, `--to mvp-0.27`,
`--to mvp-0.29`, `--to mvp-0.30`, each exit 0, ending at `mvp-0.30`. It also refuses `mvp-0.8`
directly ("only 'mvp-0.29'"). The CLI help snapshot was regenerated (the `upgrade` help).

**Migration 214 on a head of 217.** The runner is set-based, so main's vaults at 215-217 get 214
after them. `fixtures/migration_head_217` (the name kept) was rebuilt as a backup-API copy of main's
fixture, with only 214 applied through `apply_migrations` under `UPGRADE_SCRATCH_COPY`:
`wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`, header bytes 1/1, `integrity_check` ok,
`foreign_key_check` empty. It was copied into place with the backup API and has no companion files.
It now holds every migration through 217, 214 included. The branch's own `migration_head_213`/`migration_head_214` were removed.

- Its README was composed: main's text, AD's 214 paragraph (now naming `mvp-0.30` on `mvp-0.29`) and
  the rebuild record.
- `test_ad23_migration` points at the composed head and asserts 213-217 present.
- It upgrades 213 to 214 through a directory capped at 214, and gains
  `test_a_vault_at_217_without_214_gets_it`. That test adds exactly `AD23_ADDED_OBJECTS` and alters
  only the two AD1 receipts it stamps.
- Main's migration tests subtract `AD23_ADDED_OBJECTS` beside RW3b/RW5a/RW7a's sets:
  `test_ad1_migration`, `test_approach_maps_schema`, `test_help_assists_schema`,
  `test_library_asks_migration` and `test_route_rules_in_grader`.
- `table_roles` already classified 214's tables. `test_coordinated_migrations`,
  `test_tracked_fixture_databases` and `test_table_roles` pass.
- References were regenerated: 976 configuration leaves in 69 sections, 347 table notes, schema head
  217. `db_validate_reference` reports 0 errors and `validate_vault` passed.

**Classification of what main added (the AD guard's registry).** Main's chain since the branch base
added six tables (migrations 215-217). It altered no classified table: the only classified tables
whose columns changed are AD1's two receipts, which 214 itself changes. Option B applies: a table
that references a reading is READING unless it is attempt evidence. AD reads none of the six. Where
a READING row also carries the incumbent's state or material from other readings, those columns are
`derived_by_position` with an `unread:` treatment. The guard then refuses them in every scope except
`derive`, and the rules never hand them out.

| Table (migration) | Role | READING | References | Derived (unread) | Why |
|---|---|---|---|---|---|
| `passage_links` (215, RW3b) | PROTECTED | yes | `extraction_id` extraction, `span_id` span | `target_kind target_id relation pick_rank ranks_json roles_json target_facets_json state_key` | A reading's passage picked for an incumbent diagnosis target (recurrence group, hypothesis, misconception, gap, demonstrated facet, unchecked claim) and ranked against other passages. |
| `reader_cue_impressions` (215, RW3b) | PROTECTED | yes | `extraction_id`, `span_id` | `kind learning_object_id suppressed_reason propensity p_open p_open_source density` | Per visit and cue. The cue's target, the learner model's open-propensity and the holdout's draw are the incumbent's state. The learner's response is a value. |
| `interactive_figures` (216, RW5a) | PROTECTED | yes | `extraction_id`, `span_ids_json` and `input_span_ids_json` spans | `spec_json verification_report_json` | A model's figure over a reading. A tutor or library figure can send spans from other readings. |
| `figure_predictions` (216, RW5a) | PROTECTED | yes | `extraction_id` | none | The learner's predictions on a figure in the Reader: a reading event, not attempt evidence. |
| `reader_path_sections` (217, RW7a) | PROTECTED | yes | `extraction_id`, `section_id` section, `exercise_span_id` span | `label reason state_key` | The path judge's label per reading, depth and learner-state key. |
| `reader_path_depths` (217, RW7a) | NEUTRAL | no | none (a source id, not a reading) | none | The Guide's depth choice per source. Every column is metadata. |

Every column of every new table is `metadata` or `content` in `column_classes` (free text and
model JSON are content). The completeness, derived-treatment and reading-reference tests in
`test_ad_protected_tables` pass.

The other candidates were judged as follows:

- **Existing tables.** `workbench_sessions`/`workbench_steps`, `help_assists`, `approach_maps`,
  `library_asks`, DL2's commitment/intent tables, `source_objects` and the RW4e proposals existed at
  the branch base. They keep their earlier decisions: unclassified tables are refused in every
  scope; `commitments`, `commitment_*_versions`, `commitment_events` and `submission_intents` are
  DENIED.
- **`source_roles` and T1's grant state** are not tables at `558e85ab1`. T1 is not on main yet.
- **New interaction kinds.** Main's `interaction_events` kind is `reader_action_invoked` (cues,
  workbench, reader authoring). It already matches `READING_EVENT_PREFIXES`, and the cue and
  workbench payloads name their `extraction_id`, so the `reading_payload` rule withholds them with
  their reading. A reader-authoring coach response names no reading; it is a value, as before.
- **New question contexts.** Main adds none. Its new `source_exposure_events` contexts (`library`,
  `tutor_citation`) are judged by their spans, since the table is READING.
- **`judgment_ledger` rows from main's new tasks** stay under the table's PROTECTED rule. The new
  tasks are `figure_author`, `figure_verified`, `passage_cue_judge`, `reading_path_judge`,
  `reading_path_role`, `role_labeller`, `library_organizer`, `instructional_roles`, the workbench
  checks and `hint_fit`.
  - AD's three `judgment_ledger` reads are each filtered to AD's own tasks (`ad_feature_audit`,
    `ad_relatedness`, and the Reader self-check task with `left_kind = 'reader_authored_question'`),
    so these rows are never selected.
  - Their new kinds (`interactive_figure`, `library_ask`, `help_assist`, `source_span`,
    `workbench_step`, `practice_attempt`) are not in `ENTITY_KINDS`, so for a reader they name
    nothing withheld. See open item 2.

**A composition fix the gate found.** On the merged tree, 42 AD tests failed. Among them was
`test_the_ad_pipeline_runs_with_zero_denials`, whose denial was "a read in the incumbent's scope by
another module" from `learnloop.scheduling.frame_constraints`. DL2 moved `evaluate_mandatory` there
from `daily_plan.staged_frame`, a named incumbent reader. The moved module joins
`INCUMBENT_READERS` (the same incumbent constraint code, with a comment), and all 42 pass.

**Gate (memory-capped scopes, at most -n 6, one at a time; no full suite).**

- The full AD file set (`tests/test_ad*.py`, `test_ad_protected_readings`, `test_ad23_contract`,
  `test_span_reanchor`, `test_salience_firewall`): first run 42 failed, all from the moved
  incumbent reader above. After the fix: **6,099 passed, 36 xfailed** (-n 6, 25 min).
- Durability (`--durable-sqlite`) on `test_ad_guard`, `test_ad_epoch`, `test_ad23_migration`,
  `test_ad1_migration`, `test_ad_protected_tables`, `test_ad_protected_readings`,
  `test_coordinated_migrations` and `test_tracked_fixture_databases`: **246 passed**.
- Contract pins and every test file main's side changed (184 files: the defaults-snapshot tests,
  CLI help snapshot, sidecar serializer snapshot, desktop RPC contract, mobile allowlist, vault
  template, table roles, migrations, and main's figures, workbench, reading-path, cue, hint, intent,
  RW2c and UX2 tests).
  - First run: 22 failed, 9,717 passed, 2 skipped. Every failure was a composed expectation:
    - main's chain-shape tests, whose `SUCCESSOR_CHAIN[-N]` indexes, slices and explicit version
      sets end at `mvp-0.29`;
    - the CLI default now reaching `mvp-0.30`;
    - RW3b's "215 alters nothing" diff, measured from 213 and so now crossing 214;
    - RW7a's assertion that the head lacks 214.
  - The fixes: every index was recomputed from the real chain; the slices shift by one; the sets
    gain `mvp-0.30`; RW3b's diff starts at 214; RW7a's head holds 214; DL2's CLI check names
    `--to mvp-0.29`.
  - The 18 affected files then passed (111 + 264 in two runs), as did the 11 remaining files that
    name the chain or the head (267).
- `lint-imports --no-cache`: 30 kept, 0 broken. `npm run typecheck`: ok. `cargo check`: ok. Vitest
  on the composed practice, intent and API files: 20 files, 156 passed.
- `db_validate_reference`: 0 errors. `validate_vault`: passed (1,150 notes).

**Open items (not decided here).**

1. The registry's AD guard tests, not the landing gate's full suite, are what prove the
   classification. The full suite and durability lane run in the landing gate.
2. `ENTITY_KINDS` leaves main's new judgment kinds unmapped (fail open for a reader of
   `judgment_ledger`). No AD reader selects them today. Making an unmapped kind fail closed belongs
   with the post-landing follow-up's L1 (the event-kind and question-context rule failing closed).
3. AD reads none of RW3b's, RW5a's or RW7a's tables. Figure predictions and cue responses are
   candidate reading events for AD3's reading signal (§5.11). Adding them would be a spec decision,
   with their weights learned, and is not part of this merge.


## Compose fix round (intent)

The Opus composition verify of `a84767d65` reopened the compose round with one High and one Medium.
Both arise where DL2's intent controls meet AD for the first time. Both are fixed by construction,
and the Low L4 with them. The verify's three other Lows and its T1 note are recorded as
post-landing follow-ups (`adaptive-difficulty-ad23-codex-review.md`, "AD follow-up
(post-landing)").

**F1 (High): any DL2 choice turned AD's slot draw off.** The staged frame's admission
(`StagedFrame.material`) reaches `frame_constraints.evaluate_mandatory`, then
`controller_snapshot.build_snapshot` / `_commitment_summary`, then `curriculum.commitments`, which
reads `commitment_versions`. That module was not a named incumbent reader, so its read was denied,
the operation poisoned and the planned item served, with no selection written. Behind it,
`controller_snapshot` read `depth_policy_versions` and `depth_envelope_versions`, which were
unclassified. `deferrals_to_clear` failed closed the same way. The AD lanes had no commitments, and
the plan fakes' `requested_practice_item_ids` was a zero-argument lambda that crashed as soon as
intent was active.

**F2 (Medium): AD's candidates ignored DL2's intent rule.** The slot's never-attempted siblings were
checked against neither intent's `withhold_reason` nor anything else the plan's pool asks. The plan
revalidates only unserved planned items, and AD substitutes and serves in one transaction. So with
F1 patched by readers alone, AD would serve a paused, let-go or check-held sibling.

**The fix, by construction.**

- **One shared incumbent check: `scheduler.pool_admission`.** It is `build_due_queue`'s own per-item
  loop question (`admission_reason`, ruling R1), asked of one item outside a build over the same
  reads as `check_admission`; `_outside_build_admission` is now shared by both, and nothing is
  written. The question covers:
  - the routine gate;
  - DL2's intent gate, with intent's view built and its checks split by this admission, as the
    build does it;
  - the build's gates (freshness reserve, placement, cold start, the probe episodes);
  - requests, taken from the build's own request set (DL2's skips and the checks' candidates
    included).

  It reads the item states as AD's material view reads them (fix round 12). AD's candidates are not
  necessarily in the pool, so they are asked the pool's question. A rule the build adds to that
  predicate, as DL2 added intent, then reaches AD with no second list kept in sync.
- **Verdicts only: `ad_slot.incumbent_verdicts`.** This is the one place check 1 enters the
  incumbent's scope. It asks the staged frame's admission and the pool predicate there, and returns
  `IncumbentVerdicts`: `refusals` (constraint refusals with the router on, `pool:<reason>` under
  both settings), `cold_items` and `reserved_items`, as ids and reason strings only.
  `admission_failures` consumes it. That covers both the slot's candidates (inside the serve
  transaction, `engine._ad_slot_serve`'s `atomic()` block, at the draw that substitutes) and
  `deferrals_to_clear`, so a deferral the pool would refuse is never cleared.
- **The registry, from a trace, not by hand.** A trace recorded every read in the incumbent's scope:
  every intent scope and choice under both router settings (the property's cases), the contract
  harness, and the real scheduler through the sidecar RPCs with commitments.

| Table | Role | Columns (content) | Why |
|---|---|---|---|
| `depth_policy_versions` | NEUTRAL | `body_json` | A content-addressed curriculum depth policy: no learner material, nothing derived from answers. |
| `depth_envelope_versions` | NEUTRAL | `bounds_json reviewed_edges_json` | A content-addressed depth envelope, the same. |
| `assumption_decisions` | DENIED | `interval_json config_json inputs_json` | Placement's decisions, from the learner field's predictor over answers. |
| `assumption_returns` | DENIED | none | Placement's returns of those assumptions. |
| `learner_gap_check_advances` | DENIED | none | Learner-text-gap receipts (from answers' text). |
| `learner_gap_commitments` | DENIED | none | The same. |
| `learner_text_gap_reversals` | DENIED | `detail_json` | Gap reversals (diagnosis state). |
| `question_promotions` | DENIED | `attributed_facets_json` | The tutor's promote-to-practice workflow, read for the build's request set. |

New named incumbent readers (`INCUMBENT_READERS`):

- `learnloop.curriculum.commitments` (the snapshot's commitment heads);
- `learnloop.scheduling.intent.resolution` (DL2's resolution);
- `learnloop.scheduling.scheduler` (`pool_admission` and its request set);
- `learnloop.placement.predictor`, `learnloop.learner.facet_state_reader`, `learnloop.learner.mastery`
  and `learnloop.params.fitted_params` (the build gates).

Each answers AD through `IncumbentVerdicts` or the routine exclusions' id sets, never as state. The
commitment tables were already DENIED, and incumbent readers read them only in the incumbent's scope.

**Tests** (`tests/test_ad23_intent_compose.py`; fakes only):

- The verifier's two probes, without their patches:
  - `test_f1_a_commitment_never_turns_the_slot_draw_off`: LO under Learn or Master, both router
    settings; one serve selection and zero denials.
  - `test_f2_ad_never_serves_an_item_intent_withholds`: the siblings paused, let go or under a
    "Check once"; AD's support excludes them, and the served step is never one of them.
- `test_the_incumbent_hands_ad_only_verdicts`: the verdict type's fields are exactly `refusals`,
  `cold_items` and `reserved_items`, with id and string values. `pool:intent_paused` reaches a paused
  sibling. The slot enters the incumbent's scope only in `_exclusions` and `incumbent_verdicts`.
- The property: 30 seeded cases over intent scope (learning_object or practice_item with a random
  item subset), choice (learn, master, pause, let_go, check_once) and router setting. In each:
  - zero guard denials over every operation;
  - no served step is an item intent withholds at that step;
  - `deferrals_to_clear` clears no withheld item.
- `test_the_real_scheduler_lane_with_commitments`: the plan RPCs through the real scheduler (no fake
  pool), five commitment sets under both router settings; zero denials, AD opens its operation, no
  withheld item is served. This lane found the scheduler's own reads, which the fake-pool lanes
  never reached.
- Fail-first: on `a84767d65` (with the fake's signature fixed), 38 of the first 43 failed, every one
  on the F1 denial. All pass now.
- The plan fakes' `requested_practice_item_ids` takes the real signature (`skip_commitment_ids`).
- The fake pools that stand in for the scheduler's due queue are gated by intent as that queue is
  (`ad23_fakes.intent_gated`). With AD off, the ungated fake pool re-planned a paused item: a fake
  artifact, not AD.

**L4.** The kill-switch identity tests now compare against mvp-0.29 (DL2's intent) instead of
mvp-0.27. Those are `selection = false` and the generation contract (`test_ad2_serving`), the switches
below the tag, the fixture-copy identity and the rebuild (`test_ad23_successor`), the projection
parity (`test_ad23_fix_r5`), and the relatedness proposal below the tag (`test_ad3_relatedness`).
Each identity holds with an active commitment, so intent is not inert:

- `test_ad2_serving`: the LO under Master and a sibling paused;
- `test_ad23_fix_r5`: the other LO under Master and one of its items paused;
- the fixture copies: their first LO under Master.

Each asserts that intent acted (the paused item is never served or projected).

**Gate (memory-capped scopes, at most -n 6, one at a time; no full suite).**

- The full AD file set (all `tests/test_ad*.py` with the new `test_ad23_intent_compose`, plus
  `test_span_reanchor` and `test_salience_firewall`): **6,152 passed, 36 xfailed** (-n 6, 19 min).
  - An intermediate run failed one test, `test_ad23_fix_review`'s sidecar commission test. On the
    real scheduler, the scheduler's own read of `question_promotions` was denied.
  - Tracing the real-scheduler lane found it, along with the scheduler reader, and both are
    classified above.
- DL2's intent, commitment and frame files, the daily-plan and router R2a files, and every file that
  uses the plan fakes, `check_admission` or `requested_practice_item_ids` (63 files with the
  scheduler, CLI help, sidecar serializer and mobile allowlist pins): **1,749 passed**.
- Durability (`--durable-sqlite`) on `test_ad_guard`, `test_ad_epoch`, `test_ad_protected_tables`,
  `test_ad_protected_readings`, `test_ad23_intent_compose` and `test_ad23_migration`: **272 passed**.
- `lint-imports --no-cache`: 30 kept, 0 broken.


## Compose fix round 2 (pool membership)

Codex verified `a84767d65..7cf22da4d` and reopened the round with one High and two Mediums:

- **High:** a due "Check once" disabled AD for every slot, even on other LOs and with an empty
  attempt ledger. Intent's view is built inside the incumbent scope (`scheduler.pool_admission`), and
  once a check is due, `scheduling.intent.serving` reads its attempts. That module was not a named
  reader, so the read was refused and the operation poisoned.
- **Medium:** a never-attempted sibling under Keep or Light touch passed `withhold_reason` and the
  per-item predicate, but the plan excludes it from new material it chooses itself
  (`_intent_admission_order`). AD could still substitute it.
- **Medium:** with the router on, AD did not require membership in the scheduler's queue, so it
  could bring back a teach-back that value admission (or the legacy count cap) had removed.

The orchestrator diagnosed one class behind all three: a per-item predicate is not the whole pool.
The build applies set-level stages after it, and the list of named readers had to grow with every
new incumbent path. Both are now fixed by construction.

**(1) Membership, not re-derivation.**

- `engine.new_material_candidates(intent, pool)` is the plan's new-material rule: never-attempted
  new-lane items, in intent's admission order. The plan's build now calls it, and
  `engine.admitted_new_material_ids(env, record, built, released=())` calls it as well, over the
  boundary's pool.
- That pool is `built.pool`, the build this advance made and the plan serves from. It is the
  scheduler's queue after its per-item predicate and its set-level stages (teach-back value admission
  and caps among them), taken within the plan's universe, less what the plan took: planned, skipped,
  held, and AD-deferred unless released. This is `engine._context`'s own pool.
- `ad_slot.incumbent_verdicts` asks it inside the incumbent scope and adds the slot's own planned
  item. It returns the result as `IncumbentVerdicts.pool`, ids only. Construction validates every
  field as frozensets of ids, or tuples of reason strings.
- AD's sibling enumeration (the slot's LO at its capability, never attempted, visible through the
  material view) is no longer the source of truth. `build_request` intersects it with the pool.
- The staged frame's admission and the pool predicate (`pool:<reason>`) are asked only of members,
  in the serve transaction. That re-check catches a choice made since the build.
- `deferrals_to_clear` now takes the plan record and applies the same membership rule, with the
  deferrals released. A deferral outside the pool is never cleared.
- With the router off, the old `not_new_lane` check is subsumed: a member is a never-attempted
  new-lane item.

**Membership reads AD's view of item states (A8).** The full AD set found a problem with taking
membership straight from `built.pool`, through the contract test
(`test_protected_material_is_indistinguishable_from_absent_material`).

The plan classifies lanes from the raw item states. An item whose only history is a withheld answer
(the contract's `P4`) is therefore "repair" with that answer present and "new" with it absent.
Membership taken straight from the pool would make AD's support differ between the contract's
copies. With `P4` in the plan's universe that is 6 violations, across `ad_selections`' support, the
slot's candidates and the report's prior sensitivity.

The fix:

- `engine._classified_pool` takes the advance's own scheduler output and the states to read
  (`scheduled_items`, `item_states`). It never re-runs the scheduler.
- `admitted_new_material_ids(..., item_states=)` re-classifies with AD's view's states, fix round
  12's rule for every incumbent verdict AD receives: 0 violations.
- The contract's base plan and serve queue now hold `P4`. Without it, `P4` sat outside the plan's
  universe and under membership was no candidate at all. Its F20 checks (exposure and recent reveal
  on a withheld history) need it as a candidate.

**Residual, named, not decided here.** The scheduler's queue itself is the incumbent's output, and
its set-level stages can depend on protected material. Teach-back value admission, for example,
values each teach-back by information computed from the learner's raw state. AD now honours the
queue's membership, so such a dependency reaches AD as a membership verdict. That is the same
standing as every incumbent verdict since the AD23 redesign ("a pass or a named refusal per visible
candidate"). The contract fixes the queue (its fakes), so it cannot see a queue-level dependency. If
the owner wants A8 to cover the incumbent's queue too, that is the Opus architecture question: run
the scheduler's build on AD's view, not a point fix.

**One judgment call, which is the orchestrator's to overrule.** I read "admitted pool" as the
candidates the plan's new-material admission decides over, after every stage that removes items. I
did not read it as `admit_new_material`'s output, the few items the plan already planned.
Restricting AD to those planned items would leave nothing to choose: check 2 already excludes an
item planned elsewhere, so AD could never substitute.

The admission's count and load are a budget, not a membership stage. AD swaps one for one within
the slot, and check 4 (no admission load the plan did not grant) keeps that budget. Check 3 (the
block's minutes) does the same for the block. Those two checks are the remaining places where AD
reasons about the plan's budget. Every stage that decides which items may be served is now read,
not re-derived.

**(2) The incumbent scope's readers are derived, not listed.**

- `protected_tables.incumbent_reader(module)` is true for every LearnLoop module except AD's own
  (`AD_MODULES`: `learnloop.adaptive_difficulty`, `learnloop.daily_plan.ad_slot`) and readers outside
  LearnLoop.
- Inside `incumbent_constraints()`, such a reader reads any table, classified or not, including
  content and derived columns. AD's own code, or an unknown reader, reads there as it does outside
  any scope, so round 6's rule still holds (`test_in_the_incumbent_scope_only_its_named_readers_read_content`
  passes unchanged). `INCUMBENT_READERS` is gone.

I chose this over a completeness trace. A trace proves coverage only for the state it generates.
Three rounds in a row, the incumbent's path grew past the traced states: DL2's commitments, then the
scheduler's request set, then intent's due checks.

The guarantee now sits at the scope's boundary rather than on the reader list:

- `daily_plan.ad_slot` enters the scope in exactly two functions, `_exclusions` and
  `incumbent_verdicts`; `test_the_incumbent_hands_ad_only_verdicts` pins this by AST.
- Both call incumbent code alone. The only AD data passed in is the precomputed item-state mapping.
- Both return verdicts alone: `IncumbentVerdicts` (validated) and the routine exclusions' id sets.
- The scope never writes: the write rule is unchanged, so any write outside AD's tables is refused.

So whatever the incumbent reads, only a pass, a named refusal or a membership id reaches AD. A
verdict can depend on the incumbent's own state, including protected material. It always could:
that is the incumbent's admission. AD's material view still withholds protected items on top
(check 0), unconditionally.

The tables classified in the last round keep their classes. They no longer gate the incumbent scope,
but they still govern every other scope.

**(3) Tests** (`tests/test_ad23_pool_membership.py`; fakes only). Each "queue" is the scheduler's
queue after its stages, through the fakes' supplier gated by intent as that queue is. An item left
out of it is exactly what teach-back value admission or a cap does.

- **The High, as a test:** `test_h_a_due_check_once_leaves_ad_drawing`. A "Check once" on another LO
  (LO scope, or one of its items), the clock past its date (`capture.test_me_later_days` + 1), and
  an empty ledger, under both router settings. Asserts that the check is due, that there are zero
  denials, and that AD draws.
- **The first Medium, as a test:** `test_m1_keep_and_light_touch_siblings_get_no_new_material_from_ad`.
  Both siblings under Keep or Light touch, under both settings. They appear in no support, and
  neither is served.
- **The second Medium, as a test:** `test_m2_a_sibling_the_build_left_out_never_returns`. `pi_e1` is
  absent from the queue, under both settings. It appears in no support, and is never served.
- **Fail-first** (7cf22da4d's `src/` checked out over the tests, then restored): 9 of 10 failed,
  namely all four High cases, all four first-Medium cases, and the second Medium with the router on.
  The router-off left-out case already held there, because the legacy path required lane membership.
- **The property:** `test_property_every_ad_choice_is_a_member_of_the_plans_admitted_pool`, 32
  seeded cases. Each case draws a choice (learn, master, keep, light_touch, pause, let_go,
  check_once), with check_once both before and after its date. It draws a random scope (either LO,
  or one to three items across both LOs), and a teach-back sibling either kept or dropped from the
  queue (below the value bar). Both router settings are covered. It serves four steps, answering
  each. Asserts:
  - zero denials;
  - AD drew at least once (a vacuity guard; AD draws 2-4 times in every case);
  - each draw's whole support is in the oracle's allowed set, and so is every substitution and every
    cleared deferral;
  - a dropped sibling is never served and never in a support.

  The oracle is built from independent pieces: the queue, attempts, intent's withhold and its
  Keep/Light tier.
- On 7cf22da4d, 5 property cases failed on those membership assertions: a non-member substituted or
  held in a support. The rest failed on the new `deferrals_to_clear` signature, which is not a
  behaviour signal.
- `test_ad23_intent_compose` follows the interface. The verdict fields gain `pool`. A paused sibling
  is now no member at all, where before it was a member refused `pool:intent_paused`.
  `test_ad_protected_tables` checks the derived reader rule instead of the list.

**Gate (memory-capped scopes, at most -n 6, one at a time; no full suite).**

- The full AD file set (every `tests/test_ad*.py` including both compose files, plus
  `test_span_reanchor` and `test_salience_firewall`): **6,194 passed, 36 xfailed** (-n 6, 26 min).
  - An intermediate run failed one test, the contract's stage-ran check: `P4` was no longer a
    candidate.
  - That failure led to the A8 finding and its fix above.
- DL2's intent, commitment and frame files, the daily-plan and router R2a files, and every file that
  uses the plan fakes, `check_admission`, `requested_practice_item_ids`, `_classified_pool` or
  `admit_new_material` (63 files with the scheduler, CLI help, sidecar serializer and mobile allowlist
  pins): **1,749 passed**.
- Durability (`--durable-sqlite`) on `test_ad_guard`, `test_ad_epoch`, `test_ad_protected_tables`,
  `test_ad_protected_readings`, both compose files and `test_ad23_migration`: **314 passed**.
- `lint-imports --no-cache`: 30 kept, 0 broken.


## Compose fix round 3 (scope boundary)

Codex verified `7cf22da4d..dd35cf5fc` (job `20261023-231423-iIWmX0`) and reopened the round with one
High and one Medium.

- **High:** protected content could escape the incumbent scope through non-AD helpers.
  - The guard judged only the innermost reader module. So a callback planted in `env.now`, and
    invoked inside `incumbent_verdicts`, called `reader.recap._attempts()` and captured
    `WITHHELD_SENTINEL`. The verdict still validated, and the guard recorded zero denials.
  - Anyone could open the scope at runtime (`getattr(operation, "incumbent_constraints")()`).
  - Writes to AD-owned tables were allowed inside it.
- **Medium:** `admitted.add(slot_item_id)` restored the slot's own item to the pool unconditionally.

**The boundary, by construction.**

- **(c) One runtime-enforced entry.** `operation.incumbent_answer(question, request)` is now the only
  way in.
  - It checks the live caller frame against `protected_tables.INCUMBENT_ENTRIES`: `ad_slot._exclusions`
    and `ad_slot.incumbent_verdicts`, matched by module, name, the module's own globals and its file.
  - Entry by `getattr`, by an alias, from another module, or from a function forged with the entry's
    name in `ad_slot`'s namespace is refused. So are `incumbent_constraints()` and `rules('incumbent')`.
    Each refusal poisons the operation.
  - The question must be registered (`INCUMBENT_QUESTIONS`, checked on its code): a function of the new
    incumbent-side module `daily_plan.incumbent_answers`, either `routine_exclusions` or
    `slot_admission`. Only incumbent code runs in the scope, and no AD frame sits between its reads
    and the entry.
- **(b) Data only across the boundary.**
  - The request must be plain, immutable data, per `operation.plain_problem`. That allows scalars,
    dates, datetimes and timedeltas; tuples and frozensets; read-only mappings; and frozen
    dataclasses of an incumbent module, with every field plain.
  - Callables of every kind, generators, mutable containers, AD-owned objects and foreign objects
    are all refused.
  - Each entry builds its request outside the scope, under AD's own rules. `env.now()` is read there,
    so a planted callback runs where the guard refuses its read. The entry deep-freezes the
    scheduler's queue, the item states and the candidates (`ad_slot._frozen`).
  - The question receives the operation's own handles (`IncumbentHandles`: the raw vault and
    repository the operation captured), never an object AD passed.
  - The answer is checked plain. The slot's answer, `SlotAdmission`, becomes `IncumbentVerdicts`,
    which is validated again.
- **(a) The stack rule.** A read inside the scope is refused, and poisons the operation, when any frame
  between it and the scope's entry (`incumbent_answer`'s own frame) is either:
  - AD-owned (`learnloop.adaptive_difficulty.*`, `daily_plan.ad_slot`), or
  - from outside LearnLoop and the Python installation (a test's or a planted callback).

  This is `Guard._scope_violation`. Generated code (dataclass methods) is judged by its module, and
  the verdict is cached per statement site (the preparing frame and its instruction). The derived
  reader rule from round 2 stays.
- **(d) No writes.** The scope refuses every write, AD's own tables included.

**The slot's own item (the Medium).** `engine.admitted_new_material_ids(..., unclaimed=)` no longer
counts the slot's planned item as taken, so the item faces exactly its siblings' rule. If it is not a
member, `build_request` raises `SlotNotAdmitted`, an `AdUnavailable`. AD then draws nothing for the
slot, and the incumbent's own handling serves or displaces the item, exactly as with AD off.

That covers a slot planned as new material and then set to Keep or Light touch, and one that the
queue's stages now leave out (a teach-back that value admission rejects). I applied the conservative
reading: a slot whose own item left the pool is refused even when a sibling is a member. A slot the
plan no longer grants as new material is not AD's to fill. The orchestrator may relax this to "no
admitted candidate".

**Tests** (`tests/test_ad23_scope_boundary.py`; fakes only):

- **Codex's capture probe:** `env.now` as a callback reading whole attempt rows through
  `reader.recap._attempts` while AD runs. The read is refused and nothing is captured.
- **A capture planted inside the scope:** the pool predicate replaced by a callback that reads through
  the same helper and then delegates. It is planted twice: as test code, and as code running in an AD
  module's namespace. Both are refused with the stack rule's reason, the operation is poisoned,
  nothing is captured, and the planned item is served.
- **Dynamic entry:** `getattr(operation, "incumbent_constraints")()`, `getattr(operation,
  "incumbent_answer")`, an alias imported in another module, `rules("incumbent")`, a forged entry, and
  a forged entry with an unregistered question. All are refused, and each poisons the operation.
- **A write in the scope:** an `ad_dose_offers` insert by code in an incumbent module's namespace,
  inside the scope. It is refused, nothing is written, and the planned item is served.
- **The property (40 seeds).** Each seed draws a bad value: a lambda, function, bound method, partial,
  callable object, generator, dict, list, set, an AD-owned frozen dataclass, a foreign frozen
  dataclass, a mutable incumbent object, or a frozen incumbent dataclass carrying a callable. It nests
  the value at a random depth (tuples, read-only mappings, frozen incumbent dataclasses' fields) and
  smuggles it into a random field of the slot's request through the entry's own freezing. Asserts:
  - the validator refuses each value alone;
  - the request is refused before any question runs ("not plain data");
  - no smuggled callable is ever invoked (zero leaked values);
  - nothing is drawn, and the planned item is served.
- **The slot's own item:** Keep, Light touch, and left out of the queue after planning, under both
  router settings. AD draws nothing for the slot, and the served step equals AD off's. A control
  (no change) still draws.
- **Fail-first** (`dd35cf5fc`'s `src/` checked out over the tests, then restored): 56 of 58 failed and
  the 2 controls passed.
  - The probes and the slot cases fail on behaviour: the sentinel captured three times, AD drawing
    six slots, unpoisoned dynamic entries, and the write landing.
  - The 40 property cases fail there because the boundary API did not exist.
- **Updated tests:**
  - Two `test_ad2_serving` doubles that wrapped `StagedFrame.material` (test code running inside the
    scope, which the stack rule now refuses) adjust the verdicts at the boundary instead.
  - The round-6 guard test asserts the refused entry and the poisoned operation.
  - The static AST pin in `test_ad23_intent_compose` gives way to the runtime refusal tests.

**What the boundary cannot do.** It closes every channel through the scope's arguments, its return
value, AD-defined or foreign code running inside it, its entry, and writes. It is still an in-process
boundary. Code that monkeypatches the incumbent's own modules, or the operation's handles, with
builtins alone (a `functools.partial` of a list's `append` set as a repository method, say) runs no
frame for the stack rule to see. Python offers no isolation against that inside one process. If the
owner needs that guarantee, it is the Opus re-eval's question: run the incumbent's answers in a
separate process over a read-only connection.

**Gate (memory-capped scopes, at most -n 6, one at a time; no full suite).**

- The full AD file set (every `tests/test_ad*.py`, including the three compose files, plus
  `test_span_reanchor` and `test_salience_firewall`): **6,252 passed, 36 xfailed** (-n 6, 17 min).
- DL2's intent, commitment and frame files, the daily-plan and router R2a files, and every file that
  uses the plan fakes, `check_admission`, `requested_practice_item_ids`, `_classified_pool`,
  `admit_new_material` or `serving_exclusions` (64 files with the scheduler, CLI help, sidecar
  serializer and mobile allowlist pins): **1,777 passed**.
- Durability (`--durable-sqlite`) on `test_ad_guard`, `test_ad_epoch`, `test_ad_protected_tables`,
  `test_ad_protected_readings`, the three compose files and `test_ad23_migration`: **372 passed**.
- `lint-imports --no-cache`: 30 kept, 0 broken.


## Final round: inversion (owner, 2026-10-24)

The owner decided on 2026-10-24: "just do the inversion as the final round and finish this instead of
wasting time on holding a trivial harmless standard."

Codex verified round 3 (job `20261024-000326-w2R4PR`) and found two Highs and a Low:
- **High 1:** exceptions carried protected content across the boundary. `AdUnavailable(...) from exc`
  kept the incumbent's error, a malformed stored JSON whose `doc` quotes held-out text, and logged it
  with its traceback at WARNING.
- **High 2:** any `rules()` name other than `"incumbent"` (`"view"`, `"derive"` or a typo) granted
  reads unchecked.
- **Low:** the test doubles moved to the boundary.

The Opus re-evaluation (`scratchpad-backup/ad23-boundary-proposal.md`) proposed (C), the inversion, plus
a closed rules boundary (R). The owner said yes to its three questions:
1. The plan answers first and hands AD ids, codes and numbers.
2. The plan discards a pick it would not admit.
3. Boundary log lines show the type and a code, with the traceback at DEBUG only.

R was kept to its cheap part.

**The bar from this round on (orchestrator).** Only two things block landing:
- (a) protected or withheld material can change what AD picks or serves;
- (b) it can reach the learner's screen or logs at the default log level.

Everything else is a Low. The accepted residuals stay:
- the queue-level residual under E1;
- deliberate monkeypatching;
- in-memory channels with no ordinary code path.

**The inversion: four phases in the serve transaction** (`engine._ad_slot_serve`;
`engine._ad_deferrals_cleared` for the deferrals):

1. **AD lists what its view shows.** `ad_slot.open_slot` / `open_deferrals` open an AD operation and
   return `SlotInputs` with:
   - the slot item and its never-attempted visible siblings at its capability (or the deferred items);
   - their LOs and AD's estimates;
   - the view's item states and withheld reveals.

   The view is kept for phase 3.
2. **The plan computes its own verdicts, with no AD operation open and no AD frame on the stack**
   (`daily_plan.slot_facts.for_slot` / `for_deferrals`, incumbent code). It computes:
   - the admitted pool, from round 2's membership with view-state classification (the slot's own item
     judged as its siblings);
   - the staged frame's admission and the pool's per-item predicate for the members;
   - the routine exclusions;
   - checks 2-4's numbers: planned counts, slack, the admission scalars, and the router's decision and
     propensity.

   They are returned as a `SlotFacts` record. Every exception from phase 2 is caught in `engine`
   (`_incumbent_facts`) and logged as its type plus `incumbent_facts_failed`, with the traceback only
   at DEBUG. AD is then unavailable for the slot and the incumbent serves.
3. **AD decides on the decoded facts and its projected vault only** (`ad_slot.decide` /
   `deferrals_cleared`, an AD operation reusing phase 1's view).
   - The facts arrive as canonical JSON and are decoded against `daily_plan.slot_facts_schema` (a
     neutral module importing only the standard library).
   - Unknown or missing keys, wrong types, non-finite numbers and bad timestamps are refused.
   - Every item id is projected onto AD's view, and the slot's LO id onto the LOs phase 1 saw.
   - Every reason maps onto a closed vocabulary: `constraint:<key>` / `pool:<reason>`, with unknown
     ones becoming `…:other`. That vocabulary is cross-checked against the code by a test.

   Checks 0-4 then run from the facts and AD's own view, and `decide_slot` draws.
4. **The plan re-checks AD's pick** (`slot_facts.accept` / `accept_cleared`) inside a savepoint shared
   with phase 3.
   - A substitute must be a member with no refusal, held by no cold check or reserved surface, outside
     the routine exclusions, and planned nowhere else.
   - Every cleared deferral must be such a member.
   - Otherwise `ChoiceRejected` (`ad_choice_rejected`) rolls back AD's `ad_selections` row, and the
     planned item is served.

A slot whose own item left the pool (`slot_admitted: false`, round 3's `SlotNotAdmitted`) returns to the
incumbent before phase 3. AD never receives `env`, the plan record, the pool, the block or the day's
plans, and runs none of the plan's code.

**Deleted** (`32eee1da9..b74c1a38f`): 870 lines of source deleted and 951 added, across 19 files.

- `operation.py` (284 lines deleted): `incumbent_answer`, `incumbent_constraints`, `IncumbentHandles`,
  the pinned-entry and registered-question checks, `plain_problem` / `require_plain`, the incumbent
  stack rule and its cache, the `INCUMBENT` branches of `Guard._read` and `Guard._write`, and the
  scope-entry ContextVars.
- `protected_tables.py` (43): `INCUMBENT`, `INCUMBENT_ENTRIES`, `INCUMBENT_QUESTIONS`, `AD_MODULES`,
  `incumbent_reader`, and `read_verdict`'s incumbent branch.
- `daily_plan/incumbent_answers.py` (129, the whole file).
- `ad_slot.py`'s `IncumbentVerdicts`, `incumbent_verdicts`, `_frozen`, `_exclusions`,
  `admission_failures`, `build_request`, `deferrals_to_clear` and `slot_operation` (358 lines deleted,
  273 added in the phases).

Added:
- `slot_facts_schema.py` (256 lines) and `slot_facts.py` (172);
- `adaptive_difficulty/logs.py` (23);
- the engine's phase orchestration (+116).

Round 1's `scheduler.pool_admission` and round 2's membership (`new_material_candidates`,
`admitted_new_material_ids` with view-state classification) are kept and called directly by the plan.

**R, the cheap part.**

- **A closed scope.** `operation.Scope` is an Enum (`VIEW`, `DERIVE`, `PREDICATE`). `rules()` accepts
  only a member; any other value raises `TypeError` and poisons the operation.
- **A codec at every scope exit.** `operation.scoped(scope, run)` is used by every view reader
  (`_in_rules`), the two DERIVE sites and the two predicate sites.
  - An exception leaving a scope becomes `ViewFailure(kind, type name)`, or `ViewDenied`, which is
    still a denial.
  - It is raised outside the `except` clause, so it has no `__cause__`, no `__context__` and no inner
    frame. (`raise … from None` would still set `__context__`.)
  - The slot phases' own failures are coded the same way (`ad_slot._guarded`), and so is the denial
    in `eligibility_failures`.
- **Default-level logs.** All 23 of AD's `LOG.warning(…, exc_info=True)` lines now go through
  `logs.warn_failure`: the failure's type at WARNING, the traceback only at DEBUG.

**Skipped by the owner's decision, recorded as Lows (post-landing follow-ups):**
- **R-L1:** pinned openers per scope. `rules(Scope.VIEW)` may still be opened by any code inside an
  operation.
- **R-L2:** the per-read stack walk on every rules read. A callback handed to a view reader runs with
  the scope's privilege.
- **R-L3:** `stored()` pinned to its declared table. The `dose.py` lambda remains.
- **R-L4:** `own_write`'s openers pinned, with its reader restricted to `db.stores`.
- **R-L5:** an audit of the `except` clauses around view calls. With the codec they now see
  `ViewFailure`, not the original type. Tests pass, but a clause catching a specific type would no
  longer match.
- **R-L6:** the egress `suspended()` (owner decision E1's boundary): a pinned opener, and the codec at
  `_sending`'s exit.
- **R-L7:** process-level memoization in incumbent modules that AD imports, to be audited.
- **R-L8:** `MaterialView.rows(where=…)` takes free SQL; a WHERE reading a second table is read under
  VIEW.

**Tests.**
- **New file, `tests/test_ad23_inversion.py`** (it replaces `test_ad23_scope_boundary.py`). It holds
  Codex's two Highs, the codec, the incumbent-privilege and schema checks, a buggy-decider property,
  the static check, the vocabulary cross-check, and round 3's slot cases (both scenarios, both routers,
  against AD off).
- **High 1:** a cold retry whose stored context is malformed JSON quoting the sentinel, under both
  router settings. The test searches every log record at INFO and above (message, `exc_info` and
  `exc_text`), including each exception's args, attributes such as `.doc`, cause and context chains,
  and every traceback frame's locals. It asserts:
  - nothing of the sentinel is found;
  - AD's `decide` never runs;
  - the planned item is served;
  - `incumbent_facts_failed` is logged.
- **High 2:** `rules()` with `view`, `derive`, `predicate`, `typo`, `incumbent`, `""` and `VIEW`. Each
  raises and poisons, and the protected row is not read.
- **The codec:** a view delegate fails with the sentinel in its message, `.doc` and locals. It leaves
  as `ViewFailure("error", "Leaky")` with no cause or context, and nothing of the sentinel anywhere in
  its graph.
- **No incumbent privilege:** the plan's routine exclusions, `pool_admission`, and Codex's
  `recap._attempts` probe, each called inside an AD operation, are refused, the operation is poisoned,
  and nothing comes back.
- **The wire:** the valid facts round-trip. A 48-seed fuzz (unknown or missing keys, free-text
  reasons, ids outside the view, NaN, inf, bad timestamps, nested objects, long ids, wrong types, an
  LO id with spaces, non-JSON) is refused or projected, and never carries the sentinel. A sentinel the
  plan plants as a member, a refusal, an exclusion or the slot's LO never reaches AD's decoded facts,
  its rows or the step (both routers).
- **The buggy decider (16 seeds):** phase 3 substitutes a member, a paused non-member, an unknown item
  or the slot itself. The served item is the pick only when the plan's facts admit it; otherwise it is
  the planned item, with no selection row and no substitution.
- **The Low, with real incumbent state** (`ad23_fakes.cold_followup`, `close_followups`,
  `pending_variant`):
  - `test_ad2_serving`'s support test uses a real pending variant request (`pool:rung_variant_hold`)
    and a real open cold retry (`cold_check_reserved`). The reserved surface is a staged-frame double,
    now at the incumbent's own frame in phase 2.
  - Its re-check test uses the same real states for `refused` and `cold_followup`. The deferral
    readmission test uses a real cold retry, consumed later; it is held twice over (both the routine
    exclusions and the frame's cold check).
  - The exam reservation stays a double, of the incumbent's `out_of_timing_serving_exclusions`: a real
    reservation also withholds the item from AD's view, which is a different path.
- **Kept:** round 2's membership property (32 seeds) and its scenarios, and round 1's commitments
  property and real-scheduler lane, are unchanged in behaviour.
- **Updated:**
  - the deferral calls now go through `engine._ad_deferrals_cleared`;
  - the facts test spies on `decode`;
  - the contract's spy moves to `ad_slot._request`;
  - the guard tests use `Scope` members, plant their raw read in phase 3, and expect the `open_slot`
    and `decide` entries.
- **Static:** three new import contracts (the schema is neutral; the plan's facts never import AD;
  AD's slot never imports the plan's internals), and a test that no `ad_slot` function takes `env`,
  `record`, `built`, `block`, `day` or `context`.
- **Fail-first on `32eee1da9`:** `src/` checked out over the new tests, then restored. Nine of the ten
  High tests failed. High 1 failed in both router settings, where the decoder's error escaped as
  `AdUnavailable`'s cause. The codec test failed. High 2 failed for six names; `"incumbent"` was
  already refused in round 3.

**Compose with main `b7e0444b5` (RW5b),** `git merge --no-ff main`:
- `template.py`'s 20 snapshot hunks were composed: RW5b's `[figures]` notes, AD's line, and AD's
  `mvp-0.30` entry. All fingerprints were recomputed: 21 versions, 0 mismatches.
- The references were regenerated: 978 configuration leaves in 69 sections, 347 table notes, schema
  head 217. `db_validate_reference` reports 0 errors, and `validate_vault` passed.
- `classicIsBase.test.ts` is identical to main's (`BASE` `a9ae97e34` + `UX2_LANDED`).
- RW5b brings no migration and no new table.

**Gate (memory-capped scopes, at most -n 6, one at a time; no full suite).**

- The full AD file set (every `tests/test_ad*.py`, including `test_ad23_inversion`, plus
  `test_span_reanchor` and `test_salience_firewall`): **6,290 passed, 36 xfailed** in **17 min 6 s**
  (-n 6). Round 3 took 16 min 36 s, so the inversion is time-neutral: the incumbent stack walk is
  gone, one more operation runs per slot, and the view is reused.
- DL2's intent, commitment and frame files, the daily-plan and router R2a files, RW5b's figure files,
  and every file that uses the plan fakes, `check_admission`, `requested_practice_item_ids`,
  `_classified_pool`, `admit_new_material` or `serving_exclusions` (84 files with the scheduler, CLI
  help, sidecar serializer and mobile allowlist pins): **2,172 passed**.
- Durability (`--durable-sqlite`) on `test_ad_guard`, `test_ad_epoch`, `test_ad_protected_tables`,
  `test_ad_protected_readings`, the three compose files, `test_ad23_migration`,
  `test_coordinated_migrations` and `test_tracked_fixture_databases`: **432 passed**.
- The defaults snapshots, CLI help, table roles and registry tests after the merge passed (729, one
  registry test updated).
- `lint-imports --no-cache`: **33 kept**, 0 broken (30 plus the three new contracts).


## Compose onto T1 (main bd0bb7267)

The final round was verified CLEAN (Codex job `20261024-142301-glI6Tb`). This section records the last
compose: main `bd0bb7267` brings plan-first transport T1 (redesign D, "the offer is the grant"), its
migration 218 (`ingest_batches.origin_method`) and `fixtures/migration_head_218`. The merge is
`da6ccfae1` (`git merge --no-ff main`).

**Conflicts, composed:**
- `src/learnloop/config/template.py`: 20 snapshot hunks. Main's T1 notes were kept, AD's line added to
  each version, and AD's `mvp-0.30` entry kept. Every fingerprint was recomputed from the composed
  defaults: 21 versions, 0 mismatches. The successor chain stays `mvp-0.29 -> mvp-0.30`.
- `fixtures/migration_head_218` (main renamed `migration_head_217`): rebuilt as a backup-API copy of
  main's fixture with only 214 applied, under the scratch-copy allowance.
  - Checks: `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`, header bytes 1/1,
    `integrity_check` ok, `foreign_key_check` empty, no companion files.
  - It holds every migration through 218. Its README was composed: main's text, AD's 214 paragraph,
    and this rebuild's record.
- `tests/test_ad1_migration.py` and `tests/test_reader_rw7a_migration.py`: main's head 218 and T1's
  altered table, with AD's 214 on the way to head. `test_ad23_migration` moves to the composed head,
  and its set-based test becomes `test_a_vault_at_218_without_214_gets_it`: a vault at 218 without 214
  gets exactly AD's objects, and only AD1's two receipts are altered.
- The generated references took main's side and were regenerated: 1,033 configuration leaves in 69
  sections, 347 table notes, schema head 218. `db_validate_reference` reports 0 errors, and
  `validate_vault` passed.

**C4: AD's model routes under T1.**
- **The plan-first route table** (`config.schema.DEFAULT_SERVING_TASK_ROUTES`) gains three entries:

  | Route | Plan tier | Serves |
  |---|---|---|
  | `ad_forecast_llm` | `chatgpt_low` | the `ad_item_forecast` task |
  | `ad_feature_audit` | `chatgpt_low` | the feature audit |
  | `ad_relatedness` | `chatgpt_medium` | the relatedness proposal |

  - The legacy Codex table gets the same three on Codex's tiers. Codex stays refused unless
    `ai.agent_harness_opt_in`.
  - `ad_relatedness` now has its own route key, `ai.routing.ad_relatedness`. It used to ride the field
    harness's opt-in `llm_probability_llm`; `relatedness.ROUTE`, the operation map and the refusal text
    follow.
  - `ad_forecast_decider` stays a decider-only route on its code-default decider profile. A plan
    profile is not a decider; its calls are, as before, held to AD's daily cap.
- **Prices.** T1's `METERED_PRICE_SETTINGS` already priced `ad_forecast_llm` and `ad_feature_audit`
  at `adaptive_difficulty.price_per_million`; `ad_relatedness` gets the same entry. While the price is
  unset, nothing is offered or sent.
- **Quiet background work.** Every AD operation now runs under `plan_fallback.quiet()`
  (`operation._operation`). Inside one:
  - no route raises an OpenRouter offer;
  - no grant serves a route, the paid path's `_granted_provider` included;
  - with the plan unavailable, the call reports unavailable, and AD waits or skips, as T1's background
    builds do.

  This covers preparation, forecasts, relatedness and audits on a request path as well as in the
  background.
- **Tests** (`tests/test_ad23_t1_routes.py`):
  - the table entries, the operation map and the prices;
  - under code defaults each AD route is a plan profile billed as the subscription, and a Codex route is
    refused;
  - inside an AD operation, with the plan paused, OpenRouter set up, every price set and every AD task
    granted to the request: no offer and no grant, the paid route stays on the plan, and nothing is
    sent. The same tasks outside the operation do ask, and the grant would serve them.
  - With `quiet()` replaced by a no-op, the operation test fails.

**Gate (memory-capped scopes, at most -n 6, one at a time; no full suite).**

- The full AD file set (every `tests/test_ad*.py`, including `test_ad23_t1_routes`, plus
  `test_span_reanchor` and `test_salience_firewall`): **6,292 passed, 36 xfailed** (14 min 14 s). One
  more test failed: `test_ad_protected_tables`' column registry, on T1's new
  `ingest_batches.origin_method`. It is now classified as metadata (an RPC method name), and the file
  passes (6 passed).
- The second run covered 164 files: DL2's intent, commitment and frame files, the daily-plan and router
  R2a files, RW5b's figure files, T1's files (`test_plan_first_transport*.py` with the METHOD_REGISTRY
  property and the route-resolution properties, the Codex lockdown files,
  `test_t1_batch_origin_migration`), every file that uses the plan fakes, `check_admission`,
  `requested_practice_item_ids`, `_classified_pool`, `admit_new_material`, `serving_exclusions`, a head
  fixture or `apply_migrations`, and the scheduler, CLI help, sidecar serializer and mobile allowlist
  pins. Result: **3,553 passed, 1 skipped** and one load flake
  (`test_voi_v2::test_at_their_restore_values_the_switches_reproduce_the_branchs_decisions_exactly`),
  which passes alone 3 of 3.
- Durability (`--durable-sqlite`) on the guard, epoch, protected-table and protected-reading files, the
  four compose files, `test_coordinated_migrations`, `test_tracked_fixture_databases` and every
  migration test that reads a head fixture or applies migrations (11 files): **507 passed**.
- `lint-imports --no-cache`: **34 kept**, 0 broken.


## Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/ad23-onto-main`, cut from main `867b97cf1` (T1 at
`bd0bb7267` plus one docs-only commit adding the teacher, learned-parameters and MCP frontend specs). The stage tip is
`84b216398`, unchanged; the final round was verified CLEAN (Codex job `20261024-142301-glI6Tb`) under the owner's
proportionate bar. Main was neither fast-forwarded nor pushed here. Successor **mvp-0.30** (predecessor mvp-0.29), one
migration, **214**, under main's head 218 (the runner is set-based).

### Commits and conflicts

- `0d30eb399`: the `--no-ff` merge of `adaptive-difficulty/ad23`. **No conflicts**: main's only delta since the
  stage's compose onto T1 is three new files under `docs/specs/`.
- `7b090887b`: the owner decisions recorded in the AD spec (§15, D23-D27) and the 2026-10-20 confirmations in the
  Reader spec (§16); §8's owner commands now name the relatedness route `ai.routing.ad_relatedness` (since C4).
- This record.

### The successor chain

On the merged tree:
- `SUCCESSOR_CHAIN` is linear, 21 tags, ending `mvp-0.26 -> mvp-0.27 -> mvp-0.29 -> mvp-0.30`; `mvp-0.28` is in no
  set. `LATEST_ALGORITHM_VERSION` = mvp-0.30, so `learnloop upgrade` with no `--to` goes to mvp-0.30 (parity (b)).
- `ad_successor_upgrade.upgrade_to_mvp030`: predecessor mvp-0.29; mvp-0.9 … mvp-0.27 chain through
  `intent_upgrade.upgrade_to_mvp029`; AD's DERIVED state (`ad_state`, `ad_attempt_trace`, `item_forecast_scores`) is
  prepared before the rename. The CLI's `--to mvp-0.30` branch and its "expected" list are in place.
- `DEFAULTS_SNAPSHOT_BY_ALGORITHM`: with the template `.pyc` cleared, all **21** entries equal
  `defaults_fingerprint_for_version` (**0 mismatches**).
- The projection namespace stays mvp-0.8's (`P0_SUCCESSOR_VERSIONS` is the chain).
- The 58 test files that pin the chain, a snapshot or an upgrade (every test naming `SUCCESSOR_CHAIN`,
  `DEFAULTS_SNAPSHOT_BY_ALGORITHM`, `LATEST_ALGORITHM_VERSION`, `upgrade_to_mvp0*`, `P0_SUCCESSOR_VERSIONS` or a
  namespace; `fixtures-local/chainfiles.txt`): **1,466 passed** before the full suite.

### Regeneration

- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, schema head **218** with
  214's tables (`ad_selections`, `ad_commission_results`, `ad_dose_offers`, `ad_relatedness_runs`,
  `ad_coupling_versions`, `ad_state`, `ad_attempt_trace`, `item_forecast_scores`), **347** table notes, **1,033**
  configuration leaves. The regeneration changed only the `source_commit` labels of 418 notes, so nothing was
  committed.
- **Defaults snapshots**: unchanged (above).
- **CLI help snapshot and RPC pins** (serializer snapshot, desktop RPC contract, mobile allowlist): their tests pass in
  the full suite; no file needed rewriting.
- **`validate_vault.py`**: passes (1,150 notes, 1,148/1,148 reachable).
- **Failing before this stage, not fixed:** `desktop_validate.py` still stops on
  `components/pdfSelection/testing/syntheticBook.ts`; `module_validate.py` reports **1,071** issues (1,005 at the T1
  landing; the new ones are AD's modules without module notes).

### Gate

Setup: `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` (5.14.0), `TMPDIR` = merge2's
`fixtures-local/tmp`, every later command `uv run --no-sync`. Every command ran in a `systemd-run --user --scope`
(pytest lanes 10G/2G with `-n 8` under `flock /tmp/learnloop-fullsuite.lock`; everything else 5G/1G). Gate head
`7b090887b` (code as `0d30eb399`; this record is docs only). Logs: `fixtures-local/ad23-landing-*.log`. **This is the
first full run over AD2+AD3's code.**

| Step | Result |
|---|---|
| `lint-imports --no-cache` | **34 kept**, 0 broken |
| full suite (`pytest -n 8`, 52 min) | **22,019 passed**, 1 failed, 3 skipped, 38 xfailed |
| the one failure, alone, 3 times | `test_plan_first_transport_offer_grants::test_p1_after_a_yes_to_one_method_only_its_requests_and_units_use_openrouter`: **3/3 passed** (48 s each). A load flake: under `-n 8`, beside another stage's pytest and this landing's parity runs, a batch job had not reported (`KeyError` on `harness.seen[batch]`) when the assertion ran. It is T1's test and no AD code is on its path |
| durability (`-m durability`) | **120 passed** |
| `npm install`; `npm run typecheck` | ok; clean |
| `npm test -- --maxWorkers=4` (the whole vitest run) | **206 files, 1,737 tests passed**, no unhandled error |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | finished |
| worktree, tracked fixtures | `git status` clean after every lane; no non-empty `-wal` beside a fixture |

No real failure, so no landing fix.

### Parity (backup-API copies; no model call)

**Setup** (scripts in `fixtures-local/landing-ad23/scripts/`, outputs in `out/`):
- **Copies.** The pre-upgrade backups `fixtures-local/vault-backups-20261024/{linear_algebra,probability}` of the
  main checkout (schema 165, `mvp-0.8`, 0 `model_call_receipts`; probability with its `.learnloop/state.sqlite`) were
  copied once each with `copy_tree_with_databases` into `landing-ad23/orig/`. Every other copy came from `orig/` or a
  copy of it through the same helper. The owner's `fixtures/` vaults were not opened, nor `arxiv_v2`.
- **Code.** Main's code is `git archive 867b97cf1`, the merge's `git archive 0d30eb399` (`src`, `migrations`,
  `pyproject.toml`), each first on `sys.path`.
- **Environment.** Every run went through `env -i` with only `PATH`, `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`,
  `TMPDIR` and `LANG`; `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` were empty directories.
- **Routes.** `neutralize3.py` under each code sent every route (59 on main, 60 on the merge, `ad_relatedness`
  included) to `127.0.0.1:9`: chat routes to an `openai_chat` profile, decider-only routes (`ad_forecast_decider`,
  `tier1_decider`, `hint_chooser`) to a decider profile, both keyed by the unset variable `LL_LANDING_NO_KEY`, so any
  outside request stops before the transport. `ai.active_provider` to that profile, fallback cleared;
  `query_rewrite`, `tutor_query_rewrite`, `tutor_rerank`, `dense`, `[embedding]` and `[learner_text_gaps]` off;
  `build_on_serve` and outcome placement off. A copy neutralized under main's code got the merge's one extra route
  (`ad_relatedness`) before the merge opened it (`neutralize_add.py`). `routes.py` resolved every `AITask` on both
  codes (62 / 63): nothing outside the two loopback profiles except `embedding` (disabled, keyless).
- **Clock.** Every plan, Today and probe run froze the clock at 2026-10-19 09:00 UTC.

**(a) Below the successor**

| Check | linear_algebra | probability |
|---|---|---|
| open (migrate): main's code / the merge's | 165 → 218, 52 migrations / 53 (with 214) | the same |
| schema, main vs merge | **36 objects only on the merge, all 214's**: 8 tables (`ad_selections`, `ad_commission_results`, `ad_dose_offers`, `ad_relatedness_runs`, `ad_coupling_versions`, `ad_state`, `ad_attempt_trace`, `item_forecast_scores`), 5 indexes (`idx_ad_dose_offers_created`, `_draw`, `idx_ad_relatedness_runs_subject`, `idx_ad_selections_block`, `_cell`), 13 autoindexes, 10 append-only triggers (`*_no_update` / `*_no_delete` on the five ledgers). **Two tables' SQL differs, both AD1 receipts altered by 214**: `item_serve_inputs` gains `protection_epoch TEXT`; `ad_reading_opportunities` is rebuilt with `protection_epoch TEXT NOT NULL DEFAULT ''` and its two UNIQUE keys widened by the epoch. Nothing only on main | the same (1,450 → 1,486; LA 1,451 → 1,487) |
| rows of every common table (344), main's columns | **identical** (16,543 rows); the two new columns empty; the eight new tables empty; `schema_migrations`: the merge has 214 extra, common rows differ only in `applied_at` | **identical** (7,641) |
| `foreign_key_check` / `integrity_check` | 0 / ok, both | the same |
| `rebuild --shadow --json` | **0 differences** after normalisation except the replayer list (11 on main, 13 on the merge: AD's `adaptive_difficulty` and `item_forecast_scores`); facet 0, mastery 2, schedule 8, as on main; live database unchanged on both | the same (0 / 1 / 1) |
| `doctor --json` | **0 differences** after normalisation (57 issues, 1 error: as at earlier landings) | **0 differences** (101, 48) |
| at `mvp-0.8`: certification, recipe gaps, curves; the Today queue (no session, a session, greedy); the daily plan | **byte-identical** (cert 132,860 bytes; queue 41; the plan is off below mvp-0.14) | **byte-identical** (cert 17,494; queue 67) |
| to `mvp-0.29` with each code (`--to mvp-0.9`, `--to mvp-0.27`, `--to mvp-0.29`, `rebuild-derived-state` twice) | all rc 0, label mvp-0.29, both codes | the same |
| main's mvp-0.29 copy vs the merge's, rows | after replacing ULIDs and timestamps (each run mints its own), every common table identical except: `parameter_registry` **+9 rows** on the merge (AD's numeric keys registered: `calibrate_below`, `dose_daily_offers`, `dose_floor`, `history_fallback`, `near_tie_margin`, `overlap_band`, `overlap_share`, `practice_band`, `ready_threshold`), so the 20 `parameter_registry_manifests` hash differently; one `attempt_debug_payloads` row whose JSON keys are the run's own hypothesis ULIDs; 214's ledger row. **No pre-existing row differs or is missing** | the same (without the debug-payload row) |
| `rebuild --shadow` / `doctor` at mvp-0.29, either code | **0 / 0 / 0**, live database unchanged; doctor as above | the same |
| main's mvp-0.29 copy opened by each code (`c29`): schema and rows | only 214's 36 objects and the two receipt columns; every row identical | the same |
| at mvp-0.29, main vs merge (main's upgrade, and the merge's own upgrade): certification and curves, Today | **byte-identical** (129,651 bytes; queue 43, 528,665 bytes) | **byte-identical** (17,495; queue 67, 741,269 bytes) |
| the daily plan at mvp-0.29 (read, serve, serve again, read) | identical except `router_decisions.card_hash`, `snapshot_hash` and the card hash inside `detail_json`, which differ between any two runs (DL2's and T1's landings recorded the same three) | the same |

**(b) The upgrade** (the merge's code)

| Check | linear_algebra | probability |
|---|---|---|
| `upgrade --to mvp-0.30` on main's mvp-0.29 copy | rc 0, "mvp-0.29 -> mvp-0.30" | the same |
| bare `upgrade` (the default target) on another copy | rc 0, "mvp-0.29 -> mvp-0.30" | the same |
| rows vs the copy just before (normalised as above) | **no row removed or changed** in any table except: `ad_state` +9 and `ad_attempt_trace` +90 (AD's DERIVED state, prepared before the rename); `facet_capability_evidence` (36) and `facet_recall_state` (76), DERIVED, only the `algorithm_version` stamp; `parameter_registry` +9, `parameter_registry_manifests` +1, `derived_state_rebuilds` +1 | the same (`ad_state` +2, `ad_attempt_trace` +3; 1 and 2 stamped rows) |
| `rebuild --shadow` right after the upgrade | facet 0, **mastery 21**, schedule 0: all 21 the `algorithm_version` stamp of `mastery_state` rows (mvp-0.29 → mvp-0.30), no value differs; live database unchanged | facet 0, mastery 18 (stamp only), schedule 0 |
| after `rebuild-derived-state` twice | `rebuild --shadow` **0 / 0 / 0**; `doctor` as at mvp-0.29 | the same |
| the owner's full chain from mvp-0.8 (`--to mvp-0.9`, `--to mvp-0.27`, `--to mvp-0.29`, `--to mvp-0.30`, `rebuild-derived-state` twice) | all rc 0, label mvp-0.30; shadow **0 / 0 / 0** | the same |

**(c) The kill switch.** Copies of the mvp-0.30 vault, against the merge's code on main's mvp-0.29 copy (`base29`),
same frozen clock:

| Run | Today queue | certification, curves | daily plan (read, serve, serve, read) |
|---|---|---|---|
| `[adaptive_difficulty] selection = false` | **byte-identical** (both vaults) | identical except `label` (the version) | identical except the version stamps (`plan.algorithmVersion` in 4 responses, `router_decisions.algorithm_version`), the run-varying card hashes, and the router card's `card_version` `learner_state_card_v1+ad23`: the card carries AD's readiness fields while `promoted_predictor` is on, which `selection` does not switch. The router's choice and everything served are identical |
| the six switches and `reading_dose_offers` false | **byte-identical** | the same | identical except the version stamps and the run-varying card hashes (`card_version` back to `learner_state_card_v1`) |

The same holds past the plan's first block (the probe in (d)): with `selection = false`, "Done" then "More new material"
serves exactly mvp-0.29's item, writes no `ad_selections` row and no AD block event; the only other difference is AD's
in-process forecast receipts (`ad_threshold@subject`, `@subject_uniform`, `@lo`), which the subject view writes as
predictions, not serving.

**(d) Defaults at mvp-0.30** (selection on, owner decision 2026-10-19).
- **Today's plan, first block:** both vaults open with a block AD does not draw for (a repair block on linear_algebra,
  a maintain block on probability; AD serves only a new-material slot the chooser planned, `serving.slot_applies`).
  The plan, Today and certification equal (c)'s: **no AD draw, substitution or deferral**, 0 `ad_selections`.
- **A new-material slot** (`ad_probe.py`: "Done" with `plan_keep_going stop`, then "More new material" with
  `plan_more_new`, confirmed, then the next item four times, each reopened):
  - **linear_algebra:** one serve draw, mode **calibrate** (`p_band` 0.009, `p̄` 0.25 on
    `lo_what_makes_a_vector_space` / `method_selection`), support of one, so it chose the planned item
    `pi_what_makes_test_strategy_01` with propensity 1 (router propensity 1, pair 1). No substitution: the served
    item is mvp-0.29's. One **commission** draw (calibrate, over the cell's feature points) enqueued a
    `practice_expansion` job, which **failed before sending** ("Environment variable LL_LANDING_NO_KEY is required.").
  - **probability:** the planned first item `pi_exercise_01kyn2kdf7h2kba1fp7wv7t3w5` **failed check 0's `envelope`**
    (its feature point is past the default trajectory's depth envelope): an `empty_support` row and `item_displaced`
    with reason `ad_ineligible`. The plan's rules then served the next new item, `pi_nonuniform_collision_four_categories`,
    by a calibrate draw (propensity 1), plus one commission draw whose job failed before sending, as above. So at
    mvp-0.30 the learner's first "more new" item on probability differs from mvp-0.29's (the deferred item returns
    when the draw's own checks clear it at a later boundary).
  - What the learner sees: `adaptive_difficulty.why_item` answers **"A question to find your level here"** for both
    served items; `adaptive_difficulty.readiness` gives "Top level for this goal: not yet shown · not yet likely (a
    prediction)" on linear_algebra's LO, and "… (a prediction; 1 of 2 parts untested)" on probability's.
- **`learnloop ad report`** (`--dry-run` first: 0 model calls, 0 writes): **`guard.denials` 0** on every copy, before
  and after the probe. After the probe: `serve_draws` 1 (linear_algebra; `modes` calibrate 1) and 2 (probability;
  calibrate 1, empty_support 1); `commissions` `draws` 1, `results` 0, `landed_after_expiry` 0, `off_point` 0,
  `miss_rate_by_point` {} on both; `band_mode_share` 0.0; `protection` available, 15 withheld items on
  linear_algebra, 0 on probability; dose arm 0 eligible draws. Every auto-flag quiet; every "is it helping?" line
  "can't tell yet" (8 first attempts on linear_algebra).
- **No model call by AD**: 0 `model_call_receipts` on every copy; forecast receipts only the in-process ones
  (`mastery_ekf`, `lo_general+composite`, `ad_threshold@*`, all `ok`); the feature audit's `judgment_ledger` rows are
  all verdict **`unavailable`** (60 per probe run on linear_algebra, 35 to 50 on probability); both commission jobs failed before the transport.

**`model_call_receipts`**: **0 rows** in all 42 learner databases under `landing-ad23/`, and in the 7 of two
interrupted runs moved to `fixtures-local/tmp/ad23-cd-old` and `ad23-e-old` (a missing migrate step in the first (c)
script; a session restart during the first probe), none `completed`.

### Owner notes

- **Upgrade.** Back up the vault (a backup-API copy), close the app, the MCP server and the mobile host, then
  `uv run learnloop upgrade --vault <vault> --to mvp-0.30` (your vaults are at mvp-0.29 after the orchestrator's
  upgrade), then `uv run learnloop rebuild-derived-state --vault <vault>`. From mvp-0.8 the chain is `--to mvp-0.9`,
  `--to mvp-0.27`, `--to mvp-0.29`, `--to mvp-0.30`, then `rebuild-derived-state`. Right after the upgrade a shadow
  rebuild shows only `mastery_state`'s version stamp; after `rebuild-derived-state` it is clean.
- **Owner decisions** (recorded in `spec_adaptive_difficulty_v1.md` §15 as D23-D27):
  - **AD1, 2026-10-18:** the outside forecasters and the feature audit stay on.
  - **AD2+AD3, 2026-10-19:** selection on; the failing simulation gates ship as monitors; `calibrate_below = 0.25`;
    `learned_coupling` off until you spot-check relatedness; the current-content history fallback; the report's
    windows; a 7-day commission expiry.
  - **2026-10-21:** A8 ends at AD's commission target plus the egress guard (E1); one vault-wide protection epoch
    (E2); a guard denial fails closed and is counted in `ad report`.
  - **2026-10-23:** Option B (a reading with withheld blocks is absent for reading signals); your books may hold
    held-out units; follow-up D queued (reading credit from visible parts); the "Worked Examples" heading role into the
    shared role classifier.
  - **2026-10-24:** the final round is the inversion, and verification blocks only on realistic harm (the
    proportionate bar).
- **Reader confirmations (2026-10-20, queued since RW1c):** Q1 (no switch), Q44 (a withdrawn check ends honestly), Q45
  (practice ends the check), and RW6a's defaults, now also recorded in `spec_reader_workbench_v1.md` §16 (the review
  records already carried them).
- **What you see.** Under a new-material item AD drew for, one quiet line: "Picked to be challenging but doable for you
  (about a 3 in 4 chance)" (band), "A different kind of question, to keep LearnLoop's picture of you accurate"
  (overlap) or "A question to find your level here" (calibrate). On an LO's inspector page, the subject view's
  readiness line, always labelled a prediction ("not yet shown · likely ready (a prediction)"; "untested" where a
  part has no answer of its own). In the Reader, at most one extra worked example or question per section and three
  a day (the dose arm, at probability 0.10). Repair, maintain and check slots are served as before. Expect calibrate
  draws at first (your estimates are wide), and a commission (a generated item at a chosen feature point) when a cell
  has nothing near the band; it goes through the ChatGPT plan and the generator's usual protections.
- **Kill switches** (`[adaptive_difficulty]` in `learnloop.toml`, each read only at mvp-0.30): `selection` (AD's
  draw; off serves mvp-0.29's items), `generation_contract` (commissioned generation), `promoted_predictor` (the
  subject view, its readiness lines and the router card's AD fields), `learned_coupling` (off by default),
  `reading_opportunities`, `reading_self_check`; `reading_dose_offers` for the dose arm; `forecast_receipts`,
  `outside_forecasters`, `feature_audit`, `rating_tap` from AD1. `learnloop ad report` names the switch behind each
  auto-flag.

### Open items (post-landing)

- **L1-L5** (`adaptive-difficulty-ad23-codex-review.md`, "AD follow-up"): the reading-event rule fails closed (L1,
  with **C3**, the unmapped judgment kinds that fail open, folded in); a hint-equivalent help question in the item-4
  test (L2); `protected_reading_counts` undercounts (L3); one constant for the reading contexts (L4); the oracle's
  `ext:span` keys (L5).
- **C1-C3**: `reader_cue_impressions`' value proxies and `passage_links` (C1); `reader_path_depths` reclassified if a
  reader appears (C2); C3 as above. C4 is done (the compose onto T1).
- **R-L1..R-L8** (the final round's skipped part of R): pinned openers per scope, the per-read stack walk, `stored()`
  pinned to its table (the `dose.py` lambda), `own_write`'s openers, an audit of `except` clauses under the codec, the
  egress `suspended()` (E1), process-level memoization in incumbent modules AD imports, `MaterialView.rows(where=…)`'s
  free SQL.
- **Follow-up D**: reading credit in protected books from their visible parts (exact cited span first, then AD's own
  heading-based sections).
- **The "Worked Examples" heading role** into the shared role classifier.
- **The `learned_coupling` spot-check**: §8 steps 4-4c on a copy; until then the subject view stays at uniform
  sharing and no relatedness proposal is sent.
- **Observations from this landing, not blocking:** (1) `selection = false` alone leaves the router card's AD fields
  (`card_version` `+ad23`), by design (they follow `promoted_predictor`); nothing served differs. (2) On probability
  the first "more new" item was deferred by the `envelope` check, so its learner sees a different first new item
  than at mvp-0.29; worth a look in the first real report (how often check 0 defers an owner-authored item).

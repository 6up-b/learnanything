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

**What AD2+AD3 is.** One algorithm successor (the next free tag, `mvp-0.28`): AD's own posterior
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
- `src/learnloop/ad_successor_upgrade.py` (`learnloop upgrade --to mvp-0.28`).
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
`params/parameter_registry.py`; `algorithm_versions.py`, `cli/app.py` (`--to mvp-0.28`),
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

**Successor and switches.** `mvp-0.28`, one upgrade function chained from `mvp-0.27` (and from
`mvp-0.9`..`mvp-0.26` through the chain), one defaults snapshot. Six switches inside it
(`selection`, `generation_contract`, `promoted_predictor`, `learned_coupling`,
`reading_opportunities`, `reading_self_check`), each false restoring its part exactly, composing as
§11.1 states; `reading_dose_offers` outside it. Below the tag every AD2/AD3 path is off whatever
the switches say, so `mvp-0.27` stays byte-identical.

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

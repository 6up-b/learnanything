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

From the main checkout after the branch is available, with the vault at `mvp-0.27`:

```bash
# 0. a backup-API copy of the vault
uv run python -c "from pathlib import Path; from learnloop.db.copies import copy_tree_with_databases as c; c(Path('fixtures/linear_algebra'), Path('fixtures-local/la_ad23'))"
# 1. the successor on the copy (AD's DERIVED state is prepared before the rename; no model call)
uv run learnloop upgrade --vault fixtures-local/la_ad23 --to mvp-0.28
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
#    dry-run first (one call per subject on ai.routing.llm_probability_llm), then the proposal alone,
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
uv run learnloop rebuild --shadow --json --vault fixtures-local/la_ad23 --set algorithms.algorithm_version=mvp-0.27
uv run learnloop rebuild --shadow --json --vault fixtures-local/la_ad23 \
  --set adaptive_difficulty.selection=false --set adaptive_difficulty.generation_contract=false \
  --set adaptive_difficulty.promoted_predictor=false --set adaptive_difficulty.learned_coupling=false \
  --set adaptive_difficulty.reading_opportunities=false --set adaptive_difficulty.reading_self_check=false
# the simulation gates' figures (no vault, no model)
uv run python -m learnloop.sim.ad_gates
```

Running the proposal again with `--adopt` after the spot-check proposes nothing new (only units whose
fingerprint changed are re-proposed) and adopts what is in force. The relatedness proposal is the
stage's only paid call: one per subject on the field harness's
frontier route (empty: the active provider; Codex `estimated_only`), inside
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

# Learner field: honest placement and a low-dimensional predictor (v1, reshaped)

**Status:** reshaped 2026-10-11 after two independent reviews (a Codex agent and an Opus 5.5 agent), which reached the same verdict. The previous full design is preserved at commit `936813f` and listed in §11, each item with the trigger that would bring it back. That design was a facet-level graph Gaussian process with facet dossiers as kernel text, LLM-adjudicated edges, kernel ensembles, population-fit kernel scalars, and a public-data benchmark.

**Why it was reshaped** (facts checked against the repo):
- **The unit was wrong.** The design assumed "hundreds of facets per vault". The owner's working vaults have 39 facets over 21 LOs (`linear_algebra`), 29 over 18 (`probability`) and 59 over 34 (`arxiv_v2`). That is about 1.5–2 facets per LO, so a facet-level model adds little resolution over an LO-level one.
- **Facet-level outcomes are noisy.**
  - Without criterion→facet weights, a facet's outcome falls back to whole-item correctness (`learner/recall_coverage.py:266-270`).
  - For older and generated items, those weights are guessed lexically (`:832+`).
  - Propagating these outcomes across a graph would spread the attribution error.
- **It conflicted with the knowledge-model spec** (`spec_knowledge_model.md` §8.1, §8.3):
  - "`part_of` MUST NOT propagate mastery".
  - Dense LLM-generated "related" graphs are rejected.
  - Graph priors steer live decisions only after held-out support. The one live consumer was deliberately disabled (`diagnosis/calibration_sessions.py:221-228`).
- **The reports could not decide anything at n=1, and the old switching rule kept the most complex model by default.**
- **The research points the same way.** One learner's data identifies a general level plus a few coarse factors (sweep §11), and text similarity predicts co-performance only weakly.

**Principle.** Nuance lives in text that LLM components read: dossiers, item outlines, attempt analyses. The numeric learner state stays low-dimensional. **The simplest predictor is the incumbent; anything more complex must earn activation, and "can't tell" keeps the simpler one.**

**Relationship to other specs:**
- `spec_slice_a_practice_and_field_v1.md` sequences this spec (Phases 2 and 6).
- Facet dossiers moved to the practice-family track as a retrieval index (`spec_embedding_consumers_v1.md` §5.9).
- The daily-loop track owns intent, the finite plan and re-entry.

---

## 0. What this builds

- **F1, which changes nothing that is served:**
  - the outcome view (§3);
  - `learnloop field data-check`;
  - the evaluation harness (§7.2);
  - the `LearnerPredictor` interface (§4.1);
  - the incumbent `mastery_ekf` (§4.2);
  - the challenger `lo_general` with four extension arms (§4.3);
  - the `idea_hier` arm once practice families exist (§4.3);
  - an explicit **untested** state on the map (§5.1).
- **F2, live behind an algorithm successor and a kill switch:** placement after import, built on calibration sessions (§5.2).
- **Nothing else.** Everything previously specified is in §11 with its trigger.

## 1. Standing constraints

- **F1. Derived and replayable.**
  - Predictor state is rebuilt deterministically from ledgers and vault content.
  - Rebuild and replay make zero LLM or embedding calls.
- **F2. Never evidence.**
  - Predictors write only their own DERIVED and RECEIPT tables.
  - They never touch `grading_evidence`, `facet_recall_state`, `facet_capability_evidence`, mastery, certification, coldness or FSRS state.
- **F3. Live changes go through the playbook.** Each change to what is served:
  - is an algorithm successor under `docs/algorithm-change-playbook.md`;
  - has a kill switch that restores the previous behaviour exactly;
  - writes receipts, including what the old rule would have done where that is cheap to compute.
- **F4. Untested is not known.**
  - No LO or facet without direct evidence is ever reported or treated as known.
  - Inference across LOs may change the *order* of checks. It never skips material (§5.2).
- **F5. No per-learner-fitted hyperparameters.** Priors and constants are set a priori and versioned. Latent state (abilities, offsets) is estimated with uncertainty.
- **F6. Knowledge-model alignment** (`spec_knowledge_model.md` §8.1, §8.3):
  - no propagation along `part_of`, `related`, `analogous_to` or `confusable_with`;
  - no LLM-generated relation graphs;
  - any cross-LO sharing, including the general level, steers a live decision only after the F1 replay shows held-out support (the §7.4 switching rule).
- **F7. Biased sampling is declared.** Every observation records its serving origin. Off-policy claims use only system-chosen observations until a finite, system-ordered plan exists (daily-loop Q9).
- **F8. Never blend.** On the map, nothing inferred changes well depth or the demonstrated beads (owner's well-view contract, `KnowledgeWellView.tsx:7-25`).

## 2. Prerequisites

- **Daily loop.** Fix the dormant/resolved-LO serving bug before F2: the queue checks item status but not LO lifecycle at its main eligibility point (`scheduling/scheduler.py:212`). Q7 (single intent control) lets placement results map onto intent; until then §5.2 uses minimal semantics. Q5 (pre-questions at import) and Q9 (finite plan) refine F2 but don't block it.
- **Embeddings.** Not needed by this spec. The embedding substrate serves the practice-family track (`spec_slice_a_practice_and_field_v1.md` Phase 1).
- **Data.** `learnloop field data-check` reports graded attempts, LOs and facets with direct evidence, separately measured facets per LO, and revision status. The owner runs it on a copy.

---

## 3. The outcome view (F1)

Predictors and diagnostics need, for every graded attempt and every facet it bears on: pass/fail in both directions, its reliability, whether it was cold, the item, and how it came to be served.

**Reused:**
- `derive_facet_outcomes` (`learner/recall_coverage.py:219`): outcome fraction per covered facet from criterion points, criterion→facet weights, error attributions, and `dont_know`.
- `EffectiveObservation` (`attempts/effective_observation.py:118`): attempt-type mass × `assistance_discount` × `familiarity_discount` × epistemic factor, with quarantined/unassessable → 0.
- `grading_evidence` (RAW_LEDGER), with supersession for regrades.
- `practice_item_snapshots` (RECEIPT, migration 164) for the item revision at attempt time.
- The `primed` / `assisted` flags as `facet_evidence_timeline.py` reads them.
- `resolve_item_irt_params` for `(a, b)`.

**Added:** a DERIVED table, `facet_outcome_observations`, with a registered rebuild owner. One row per (attempt, facet) for the latest non-superseded grading epoch:

| Column | Meaning |
|---|---|
| `attempt_id`, `facet_id` (canonical, after `facet_merges`), `practice_item_id`, `item_snapshot_hash`, `revision_status` | Identity and provenance (`exact` \| `reconstructed_current` \| `excluded`) |
| `observed_at` | Attempt completion time |
| `outcome` | `derive_facet_outcomes` value ∈ [0, 1] |
| `facet_share` | This facet's share of the item's coverage, so one attempt's total weight is not multiplied by its facet count |
| `effective_mass` | From `EffectiveObservation` |
| `cold`, `assisted`, `primed` | Flags |
| `surface_group_id` | For independence reporting |
| `serving_origin` | `learner_pick` \| `system_probe` \| `forced_followup` \| `requested` \| `unknown` |
| `serving_propensity` | Nullable. Null for `learner_pick` until Q9 |
| `scheduler_candidate_id` | Nullable link to the offer receipts |

- **Serving origin** is joined from:
  - `submission_intents.scheduler_candidate_id` and `scheduler_offer_receipts` (a list pick when the candidate was on a composed offer);
  - probe presentations (system probes, with their selection telemetry);
  - follow-up insertion receipts (forced).

  Attempts before migration 161 are `unknown`.
- **Authoritative inputs** (revised 2026-10-11 after review). Each row is derived from:
  - the latest non-superseded `grading_evidence` epoch;
  - that epoch's criterion points (`attempts.py:980`);
  - the criterion→facet mapping of the **item and rubric revision that was graded**;
  - the epoch's error attributions;
  - `dont_know`.

  These are exactly the inputs `derive_facet_outcomes` (`recall_coverage.py:219`) needs.
- **Historical revisions.** `practice_item_snapshots` (migration 164) holds only revisions the scheduler scored, not every revision that was answered. So every row carries `revision_status`:
  - `exact`: the graded revision was found by content hash;
  - `reconstructed_current`: the current content was used because no graded revision exists, allowed only when `field.legacy_fallback = "current_content"`;
  - `excluded`: the default when the graded revision is missing.

  Current content is never silently substituted for historical content. Reports state the count of each status.
- **The debug copy is for validation only.** Per-facet outcomes are already persisted inside each attempt's debug payload (`attempts.py:2852`, written at `:2057`). Rows are compared against that copy (a test and a report line), but it is not the ledger: it has no supersession semantics and its shape isn't a contract.
- **What is genuinely new:**
  1. A queryable, rebuildable per-facet outcome table with explicit revision status.
  2. The serving-origin join.
  3. The canonical-facet resolution in one place.
- **Not a new evidence source.** The view is the same arithmetic the projection already uses, reshaped (Plan B: "derived and replayable").

---

**Attempt-level rows.** The item-anchored predictors (§4.3) observe attempts, not facets. Each attempt contributes one row, derived from the same inputs and never stored separately:
- `outcome`: the attempt's rubric fraction;
- `effective_mass`: from `EffectiveObservation`;
- flags: cold, assisted, primed;
- the item's LO, `capability`, `variant_relation` and `family_id`;
- `serving_origin` and `revision_status`.

Per-facet rows feed the `facet_beta` arm and diagnostics.

---

## 4. Predictors

### 4.1 The `LearnerPredictor` interface

Every predictor, incumbent or challenger, implements one contract. It extends the harness `Predictor` contract (§7.2). Consumers (§5) depend only on it (G10).

```
class LearnerPredictor(Protocol):
    name: str; version_hash: str
    def predict_item(item_id) -> ItemPrediction           # p_success, logit variance, region loadings
    def conditional_gain(item_id, chosen: list[item_id], weights: dict[region_id, float]) -> float
    def region_estimates(scope) -> dict[region_id, RegionEstimate]   # mean, variance, n_eff, untested
    def rebuild() / observe(rows)                          # deterministic, zero model calls (F1)
```

- **Eligibility.** Only predictors with calibrated uncertainty (`conditional_gain` plus region variances) can be active (G11). A point-only predictor such as `llm_probability` can never be active.
- **Active predictor.** `field.active_predictor` defaults to `mastery_ekf` (D1). Switching it changes what is served, so it is a successor with a kill switch, decided by §7.4.

### 4.2 Incumbent: `mastery_ekf`

An adapter over the existing per-LO 2PL EKF in `learner/mastery.py`:
- LOs are independent;
- item difficulty comes from `resolve_item_irt_params`.

It is what LearnLoop already believes, and it propagates nothing across LOs, so it satisfies F4 and F6 by construction. Its regions are LOs.

### 4.3 Challengers: `lo_general`, its extension arms, and `idea_hier`

**`lo_general`.** For an attempt on item `i` in LO `L`:

```
logit P(success) = a_i · ( θ_general + θ_L ) − b_i
```

- `θ_general ~ N(m₀, σ_g²)`, one per subject. `m₀` comes from the covering learner claim when one exists (weak); otherwise it is 0.
- `θ_L ~ N(0, σ_L²)`. **LOs are independent beyond the shared general level. No graph coupling** (F6, D2).
- `σ_g² = 0.75` and `σ_L² = 2.25`, so `σ_g² + σ_L² = 3.0`, the per-LO EKF's cold-start prior variance.

**Extension arms.** These are the pieces that were missing for predicting ability. Each is a separate harness arm with a-priori, versioned constants (D3); the composite is scored too.

| Arm | Adds | Prior | Evidence |
|---|---|---|---|
| `lo_general+practice` | Learning from practice: `θ_L` gains `γ` per graded cold opportunity, predicted *before* the outcome is seen | `γ = 0.2` logits per opportunity. A median of ~7 opportunities takes a learner from 50% to 80% | Learning rates are consistent across learners while starting knowledge varies widely (2604.03246) |
| `lo_general+capability` | An offset `δ_cap` per item `capability` (`retrieval`, `schema_interpretation`, `procedure_execution`, `method_selection`, `coordination`), shared across LOs in a subject. Latent state, not a fitted hyperparameter | `N(0, 0.5²)` | Recall, procedure, method choice and transfer are different abilities on the same topic |
| `lo_general+transfer` | An offset by `variant_relation` (PF): `same_target` 0, `isomorph`, `near`, `far` | Means 0 / −0.25 / −0.5, sd 0.5 | Retrieval practice transfers strongly to isomorphs, weakly to near variants, little to far ones (PsyArXiv sj3w7) |
| `lo_general+retrievability` | For items with FSRS state, `β · logit(R_FSRS(t))`, combining ability with forgetting | `β = 0.5`; the report sweeps {0, 0.5, 1} | FSRS and mastery currently predict separately |
| `idea_hier` | Family effects `u_F ~ N(0, σ_F²)`, independent in v1 (practice-family track §5.1–5.2). Available after PF-a | `σ_F² = 0.5` | Families are the finest unit with a shared retrieval target |

**Observation model and inference** (shared by all challengers; the incumbent keeps `mastery.py` as is):
- **Observations.**
  - One 2PL observation per attempt row, using `mastery.py`'s probability-space EKF.
  - Sensitivity `H = a·p(1−p)`; noise `R = base_observation_variance · p(1−p) / w`, with `w = effective_mass`.
  - **Zero-mass rows are skipped**: quarantined, unassessable, or `excluded` revision.
  - **Primed attempts** shift `b` exactly as the attempt path does (`attempts.py:2458`). They are never discounted a second time through mass.
  - `dont_know` is outcome 0 at full mass, and a skip gives no row.
  - Superseded grading epochs are dropped.
- **Item difficulty.**
  - `(a, b)` come from `resolve_item_irt_params`: empirical-Bayes `b`, then solver-panel difficulty (`difficulty_source = "solver_panel"`), then authored, then the LO prior.
  - **LLM-estimated difficulty is never a point value** (ρ = 0.06). Its variance `σ_b² = 1.0` is folded into `R`, which only widens.
- **Inference.**
  - A sequential EKF over the small joint state: general level, LO deviations, plus whichever extension terms the arm has.
  - The state has 1 + #LOs (+ capabilities, relations, families) dimensions, tens rather than hundreds.
  - Fixed ordering (`observed_at`, `attempt_id`); float64; any jitter only adds variance.
- **Time.**
  - Variance grows by the existing drift form (`mastery.py:342-353`).
  - There is no mean decay. Retention timing stays FSRS's job, except for the explicit `+retrievability` covariate.

**Region estimates.**
- Regions are LOs (plus families, capabilities and relations where the arm has them).
- Each region reports `mean`, `variance` and `n_eff` (the information gained, in prior units).
- `untested` is true when the region has **no direct evidence**, whatever the inference says (F4).

---

## 5. Consumers

### 5.1 Map: an explicit untested state (F1; no predictor needed)

- **The fix.** Today a facet with no evidence is drawn at `ready = 0.5` (`learnloop_sidecar/handlers/knowledge_map.py:371-374`), which looks like a half-known skill.
- **The change.** `get_knowledge_map` instead marks such points `untested: true` and omits `ready`. `KnowledgeWellView` draws them as flat and outlined, with a small "untested" label.
- **What stays the same.** Demonstrated beads, ghost rings and decay markers (F8).
- **Version impact.** This is display honesty, not served behaviour, so it needs no successor.
- **Deferred.** Showing a predictor's inferred estimates on the map ("fog") is deferred (§11).

### 5.2 Placement after import (F2; live; successor; kill switch `placement.enabled`)

**Built on what exists.**
- `start_calibration_session(learning_object_ids=…, time_budget_minutes=…)` (`diagnosis/calibration_sessions.py:156`) with `CalibrationScreen`.
- Its plain predictive-rate ordering (§8.3 of the knowledge-model spec) is kept. The active predictor's `conditional_gain` replaces it only when §7.4 has activated a challenger.

**When.**
- **Trigger:** an import or study-map apply that adds ≥ `placement.min_new_los` (default 3) active LOs with eligible items.
- **Eligible items:** imported exercises, or practice-family items published under the PF-b rules. They must be active, unattempted, not exam-reserved and not reveal-burned.
- **No eligible items:** today's per-LO initial probes run unchanged.

**Learner experience.**
1. **Triage, one tap per LO** (or per chapter group): **know / new / unsure**.
   - The answers are recorded as weak learner claims through the existing claim machinery, never as evidence.
   - **"new"** LOs aren't checked; they start normally.
2. **Offer:** "Quick check: up to 4 questions (~6–8 min) so LearnLoop can skip what you already know." Choices: **Start / Later / Skip**. Skipping is never negative evidence.
3. **Adaptive checks.**
   - Each next item maximizes `conditional_gain` over the "know" and "unsure" LOs, weighted toward checks that could actually skip work.
   - The block **stops early** when no remaining candidate could change what happens next, or when the budget runs out.
   - Each question has **"I don't know"** (`dont_know`) and **Skip** (no row), and hints are off.
4. **Answers are revealed at the end of the block.** Every reveal is recorded in `reveal_events`.
5. **Results, in plain language and never as "mastered":**
   - **"Checked: solid, we'll confirm around [date]":** the LO was **directly checked** and `P(θ_L > θ_known) ≥ q` (D6).
   - **"Checked: needs practice":** the LO was directly checked and did not meet that bar.
   - **"Not checked":** everything else, including LOs a predictor *infers* to be strong. Inference never skips material (F4).
6. **Override.** "Actually, I don't know this" moves an LO to **Not checked**. It is a routing preference, appended to `judgment_ledger` (task `placement_override`, judge `owner`).

**Effect.**
- **"Solid" LOs.**
  - No initial probe episode now.
  - One **confirm probe** after `placement.confirm_after_days` (default 10), as a normal cold check.
  - Until then their items are served only through the goal-frontier path, unchanged. Once daily-loop Q7 exists, "solid" maps onto maintain-level intent instead.
- **"Needs practice" LOs** get their initial episode now, first.
- **"Not checked" LOs** keep today's behaviour.
- **Nothing is certified.** A failed confirm probe restores the normal path.
- **Grader risk.** A grader that accepts a wrong answer could produce a false "solid". Confirm probes catch that afterwards, and Slice 1's E1 grader probes measure the grader's error rate (D7).

### 5.3 Not built here

- **Probe targeting by a predictor** (§11).
- **Re-entry after a lapse.** The daily-loop track can reuse the placement block for a few high-information checks after a break.

---

## 6. Persistence

| Table | Role (`db/table_roles.py`) | Contents |
|---|---|---|
| `facet_outcome_observations` | DERIVED (rebuild owner) | §3 |
| `learner_predictor_snapshot` | DERIVED (rebuild owner; only while a non-incumbent predictor is active) | Per region: `mean`, `variance`, `n_eff`, `untested`, `predictor`, `version`, `as_of_observation_id` |
| `placement_decisions` | RECEIPT | `id`, `trigger_ref`, `scope_lo_ids_json`, `triage_json`, `candidate_items_json`, `chosen_json` (item, gain, minutes, stop reason), `conclusions_json` (per LO: label, `p`, interval), `episodes_skipped_json`, `confirm_due_json`, `q_used`, `predictor`, `predictor_version`, `created_at`. Joined to confirm-probe outcomes by report 3 |

- **Config:**
  - `[field]`: `enabled`, `active_predictor` (default `mastery_ekf`), arm constants (D3), `legacy_fallback` (`exclude` \| `current_content`, default `exclude`).
  - `[placement]`: `enabled`, `k` (4), `budget_minutes` (8), `min_new_los`, `confirm_after_days`, thresholds.
- **Algorithm versions:**
  - F1 needs none: derived tables plus a display change.
  - F2 (placement live) is one successor.
  - Activating a challenger predictor is a further successor.

---

## 7. Evaluation

### 7.1 Correctness gates (pass/fail)

| Id | Gate |
|---|---|
| G1 | **Deterministic rebuild:** the same inputs give byte-identical derived tables (hash compared on fixture copies) |
| G2 | **Zero LLM and embedding calls** during rebuild or replay (fakes assert) |
| G3 | **No evidence writes:** an import-linter contract forbids predictor packages from importing evidence writers. Evidence, mastery, facet-recall and certification tables are byte-identical with the field on vs off |
| G4 | **Untested is not known:** no region without direct evidence is reported as known, "solid", or `untested = false`. Neighbour inference never changes episode entry |
| G5 | **Knowledge-model alignment:** no prior or update propagates along `part_of`, `related`, `analogous_to` or `confusable_with`, and no LLM relation edges are read |
| G6 | **Never blend:** with the untested state on vs off, well depth and demonstrated beads are identical except at untested points (vitest) |
| G7 | **Placement skips only what it checked:** only directly checked "solid" LOs lose their initial episode. Nothing is certified |
| G8 | **Placement reproducibility:** selection given a snapshot is deterministic (ties broken by item id), and `placement_decisions` records everything needed to recompute it |
| G9 | **Kill switches:** with `placement.enabled = false`, or the active predictor reverted, episode entry and ordering match the previous version on fixture copies |
| G10 | **Consumers use the interface:** placement and map modules can't import any predictor's internals (import-linter) |
| G11 | **Only calibrated-uncertainty predictors can be active:** config validation rejects the others |
| G12 | **Weight and provenance invariances:**<br>• zero-mass rows leave every posterior byte-identical;<br>• primed handling matches `mastery.py` (at one LO, `lo_general` with `σ_g² → 0` reduces to it);<br>• every outcome row has a `revision_status`, and with `exclude` no current content substitutes for a missing revision |


### 7.2 Evaluation harness: `learnloop eval`

- **Contract.** `observe(row)` and `predict(row) -> p ∈ (0, 1)`, plus `name`, `version_hash` and `granularity` (`attempt` or `facet`).
  - The harness walks rows in a fixed time order and asks every arm to predict **before** it sees the outcome.
  - Arms have no other store access, so leakage is impossible by construction.
  - Facet arms are aggregated to attempt level by `facet_share`.
- **Arms:**

  | Arm | What it is |
  |---|---|
  | `base_rate_lo` | Per-LO running success rate |
  | `facet_beta` | `facet_recall_state` |
  | `mastery_ekf` | The incumbent (§4.2) |
  | `lo_general` and its four extension arms (+ composite) | §4.3 |
  | `idea_hier` | §4.3, after PF-a creates families |
  | `family_memory` (per item / family / LO) | The practice-family idea-identity replay |
  | `llm_probability` | **Optional, off by default** (D8). A frontier model reads recent graded attempts and predicts the next item; one-parameter recalibration on past predictions only; spend-capped; cached outside the vault. It can't be active (G11). It is a one-off offline test of "LLM as sensor", nothing more |

- **Metrics.**
  - Log loss, Brier, a reliability diagram, and AUC at attempt level.
  - Splits: **first attempt on a never-seen LO vs later attempts** (cross-LO prediction only matters for the first), serving origin, revision status and topic.
  - Bootstrap intervals clustered by attempt.
  - A version manifest: arm hashes, algorithm, config hash, data snapshot.
- **Outputs.** JSON plus markdown, aggregates only and never learner text. Written to a path the owner chooses (default `fixtures-local/reports/`).

### 7.3 Reports

1. **Prequential replay (F1).** Every arm on the owner's graded log, with the splits above.
   - **Key question:** does `lo_general` (or an extension) beat `mastery_ekf` on first attempts at never-seen LOs?
   - **Validity:** at n=1 this detects only large differences.
2. **Placement simulation (F1).** For each LO group the owner started historically, simulate up to k checks chosen by §5.2's rule from what was actually answered, then score predictions of the first attempts on the rest.
   - **Reported:** the share that would be "solid", and their **miss rate**.
   - **Named bias:** checks can only be chosen from what was historically answered.
3. **Confirm-probe report (after F2).**
   - **Reported:** the miss rate of "solid" against its confirm probes; the "needs practice" hit rate; placement minutes against the estimated minutes of probing every LO.
   - **Named confounds:** ten days of learning and forgetting, and goal-frontier serving in that window.

### 7.4 Switching rule (simplest is the incumbent)

**How a challenger is activated.**
- **Who can challenge:** `lo_general`, an extension, the composite, or `idea_hier`.
- **Conditions:** it beats `mastery_ekf` on report 1's attempt-level log loss (overall *and* on the first-attempt split), with a bootstrap interval excluding 0 and the margin fixed before the run (D9). Its report-2 miss rate must also be no worse.
- **"Can't tell" keeps the incumbent.**
- **The switch:** activation is a successor with a kill switch.

**What activation enables.** It is also the held-out support that knowledge-model §8.3 requires before cross-LO sharing (the general level) can steer a live decision. Until a challenger is activated, placement ordering uses the plain predictive rate and "solid" uses `mastery_ekf`.

---

## 8. Rollout

| Step | Contents | Needs | Gate |
|---|---|---|---|
| **F0** Prerequisites | The dormant/resolved-LO serving fix; daily-loop Q7 when available (daily-loop track) | — | Blocks F2 only |
| **F1** Predictors, harness, untested state | §3, §4, §5.1, §7.2, reports 1–2, `data-check` | — | G1–G6, G10–G12; owner reviews reports 1–2 once |
| **F2** Placement live | §5.2; successor + kill switch | F0 fix; F1 reports reviewed; eligible items (imported exercises; PF-b published items) | G7–G9; report 3 after several imports |
| **Activation** (optional) | A challenger becomes `active_predictor` | §7.4 rule met | Successor + kill switch |

---

## 9. Tests

- **`test_facet_outcome_view.py`:**
  - one row per (attempt, facet) for the latest epoch;
  - `facet_share` sums to 1;
  - `dont_know` gives 0, and quarantined rows get mass 0;
  - canonical facet resolution;
  - the serving-origin join, including pre-161 attempts;
  - `revision_status` (G12);
  - agreement with the debug-payload copy for `exact` rows;
  - determinism.
- **`test_predictor_interface.py`:**
  - consumers run unchanged against a fake predictor and each real one (G10);
  - activation is rejected without uncertainty (G11);
  - switching is a successor with a working kill switch (G9).
- **`test_lo_general.py`:**
  - it reduces to `mastery.py`'s EKF at one LO with `σ_g² → 0`;
  - zero-mass invariance and primed handling (G12);
  - no propagation along forbidden edge types (G5);
  - each extension arm moves predictions in the documented direction on synthetic data;
  - deterministic rebuild with zero model calls.
- **`test_eval_harness.py`:**
  - no outcome is visible before prediction;
  - arms have no store access;
  - manifests and clustered bootstrap;
  - the first-attempt split;
  - `llm_probability` is off by default and spend-capped (fake client) when on.
- **`test_placement_session.py`:**
  - triage is recorded as claims, not evidence;
  - adaptive selection and the early stop;
  - only directly checked LOs become "solid" (G4, G7);
  - the confirm episode is entered after `confirm_after_days`, and a failed confirm restores the normal path;
  - with no eligible items, today's probes run;
  - G8, plus the kill switch (G9);
  - overrides go to `judgment_ledger`.
- **`test_map_untested.py`** (sidecar RPC + vitest): the untested points; G6.
- **Durability lane:** a rebuild of the derived tables under production pragmas on a fresh vault.

---

## 10. Open decisions

| # | Decision | Recommendation |
|---|---|---|
| D1 | Active predictor at launch | `mastery_ekf`, the existing per-LO filter. Challengers earn activation (§7.4) |
| D2 | Cross-LO structure in `lo_general` | A shared general level only; no graph coupling (knowledge-model §8.1, §8.3). Prerequisite-directed coupling is deferred (§11) |
| D3 | Extension-arm constants | `γ = 0.2`; capability `N(0, 0.5²)`; relation means 0 / −0.25 / −0.5 (sd 0.5); retrievability `β = 0.5` (sweep 0, 0.5, 1). Versioned, never fitted to the owner |
| D4 | Placement block | k ≤ 4, ≤ 8 minutes, adaptive with an early stop |
| D5 | Triage | know / new / unsure, recorded as weak claims; "new" skips checks |
| D6 | "Solid" threshold and confirm delay | `q = 0.8` at `θ_known = logit(0.75)`, or `q = 0.9` if report 2 lacked data; confirm after 10 days. Tune from report 3 |
| D7 | Wait for Slice 1's grader probes before F2? | No, per the owner's live-with-kill-switch preference. Confirm probes are the safety net; review E1 when Slice 1 produces it |
| D8 | `llm_probability` | Off by default; at most a one-off offline test |
| D9 | Switching margin | The attempt-level log-loss improvement's bootstrap interval excludes 0, overall and on first attempts, and the miss rate is no worse. Fixed before running |
| D10 | Revisions missing from snapshots | `exclude` by default; `current_content` only by explicit config, flagged |

---

## 11. Deferred, with triggers

The full design for everything below is preserved at commit `936813f` (`docs/specs/spec_learner_field_v1.md` and the Slice A plan at that commit).

| Deferred | Revisit when |
|---|---|
| **Facet-level graph field:** heat kernel over facets, LLM-adjudicated text edges, the representation experiment (V0–V4), the general factor inside a facet kernel, kernel ensembles, population-fit kernel scalars, the co-performance text projection | `data-check` shows hundreds of active facets with ≥ 3 *separately measured* facets per LO and ≥ 1–2k graded attempts, **and** an activated LO-level predictor still leaves residuals correlated along authored or semantic neighbours |
| **Prerequisite-directed coupling** between LOs | `lo_general` is activated and the replay shows residual correlation along prerequisite edges. It must respect direction (knowledge-model §8.3) |
| **Map fog** (predictor estimates on the map) | A challenger is activated on the first-attempt split (§7.4) |
| **Probe targeting** by the active predictor | A challenger is active, and the daily loop's finite plan (Q9) makes propensities known for evaluation |
| **`idea_hier_llm_prior`**, or any live use of `llm_probability` | The offline test shows calibrated gains over the best LO-level arm on first attempts |
| **Public-data benchmark** (time-to-useful-vault, kernel fits, transfer guard) | A specific question the owner's replay can't answer, such as whether a deferred facet-level design is worth reviving |
| **Learned action router** using dossier embeddings as features | Pipeline plan F/G gates. Prefer an LLM agent reading dossiers as text first (`spec_embedding_consumers_v1.md` §5.9) |
| **Facet dossiers** | Not deferred: **moved** to the practice-family track as the practice index (`spec_embedding_consumers_v1.md` §5.9) |

---

*Related: [[Pipeline Augmentation Plan]] (workstream B) · `spec_knowledge_model.md` §8 · `spec_slice_a_practice_and_field_v1.md` · `spec_embedding_consumers_v1.md` §5 · `learner/mastery.py` · `diagnosis/calibration_sessions.py` · `docs/algorithm-change-playbook.md` · [[Bitter Lesson Research Sweep]]*

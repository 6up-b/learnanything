# Learner field: generous defaults, honest labels, and a low-dimensional predictor (v1, reshaped)

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

**Revised again 2026-10-11 for frictionless defaults** (owner; `docs/specs/daily_loop_frictionless_defaults.md`). The rule is **honest labels, generous defaults.**
- There is no placement ceremony, and no opening probe for every new topic.
- Topics the learner says they know, or that early answers show they likely know, are **assumed known** and checked in their first ordinary review.
- What is *claimed* stays honest: untested, assumed, and demonstrated are always distinguished.

**Principle.** Nuance lives in text that LLM components read: dossiers, item outlines, attempt analyses. The numeric learner state stays low-dimensional. **The simplest predictor is the incumbent; anything more complex must earn activation, and "can't tell" keeps the simpler one.**

**Relationship to other specs:**
- `spec_slice_a_practice_and_field_v1.md` sequences this spec (Phases 2 and 6).
- Facet dossiers moved to the practice-family track as a retrieval index (`spec_embedding_consumers_v1.md` §5.9).
- The daily-loop track owns intent, the finite plan and re-entry.

---

## 0. What this builds

- **F1, which changes nothing that is served:**
  - the outcome view (§3) and interaction signals from your questions and hints (§3.1);
  - `learnloop field data-check`;
  - the evaluation harness (§7.2);
  - the `LearnerPredictor` interface (§4.1);
  - the incumbent `mastery_ekf` (§4.2);
  - the challenger `lo_general` with its extension arms (§4.3), including the interaction-signal arms;
  - the `idea_hier` arm once practice families exist (§4.3);
  - an explicit **untested** state on the map (§5.1).
- **F2, live behind an algorithm successor and a kill switch:** starting new material without ceremony (§5.2):
  - no per-topic opening probes;
  - "assumed known" from self-report, fast-track on early answers, or an activated predictor, checked in the first review;
  - an optional "Check what I already know".
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
- **F4. Honest labels, generous defaults** (revised 2026-10-11).
  - **Skipping is allowed.** Self-reports, early answers and an activated predictor may skip material by marking an LO **assumed known** (§5.2).
  - **Labels stay honest.** They always distinguish **untested**, **assumed (not tested)**, and **demonstrated**.
  - **Assumptions get checked.** Nothing assumed is certified or written as evidence, and every assumption is checked in ordinary review.
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

### 3.1 Interaction signals: what your questions and hints reveal (added 2026-10-11, owner)

**The idea.** These signals replace opening probes as the cheap source of "where you're shaky": what you ask the tutor, when you ask for hints, how you do afterwards, and what you ask after the feedback. They are already logged:

| Source | Where it lives today | What it reveals |
|---|---|---|
| Hints within an attempt | `practice_attempts.hints_used`, including substantive mid-attempt tutor questions folded in as hint equivalents (`hint_equivalents_for_submission`, `handlers/practice.py:499-501`) | How much help the answer needed |
| When help came | `question_events.seconds_into_attempt` | Help **before any work** means you didn't know where to start. Help late in the attempt means you got partway |
| Tutor questions during practice and after feedback | `question_events` (migration 019): `context` (`practice` \| `feedback`), `attempt_id`, `question_type` (`clarification` \| `prerequisite` \| `mechanism` \| `strategy` \| `verification` \| `other`), `facets_json`, `hint_equivalent`, `leak_suspected` | *What* was unclear, and about which facets. A `prerequisite` question points below the item; a post-answer `mechanism` question after a correct answer suggests the answer was procedural rather than understood |
| Questions while reading | Reader-dialogue `interaction_events` and `question_events` with `context = library`, tied to source spans and so to LOs | Confusion about new material **before any practice**. This is free placement |
| What happened next | The graded outcome after hints, and the following attempts | Whether the help repaired the gap |

**Derivation.** One signal row is derived per question or hinted attempt, and never stored separately: LO or facet, signal type, timing, and the subsequent outcome.
- **Mapping.** It uses the logged `question_type` and `facets_json` where present.
- **Classification.** Only questions missing them, such as reader questions without a type, are classified by an LLM, in the Plan B tutor-dialogue-compiler style (LLMKT, 2409.16490). Results are cached in `question_classifications` (WORKFLOW, paid output, never re-run on rebuild).
- **The classification is a proposal.** LLMs are weak at cognitive-skill diagnosis (MathCog, 2504.00843), so its influence is small and capped (below).

**How the signals are used.**
1. **Routing for new material (§5.2), live with F2:**
   - LOs you asked confused questions about while reading, or needed help before starting, are **taught first and never fast-tracked** on early answers alone. "I know this" still works.
   - LOs answered without help and without follow-up questions are the **fast-track** candidates.
2. **As predictor observations** (harness arms §4.3; activated only under §7.4):
   - hint depth and timing turn a binary outcome into a graded one;
   - typed questions become weak observations.

**Guards.**
- **Asking is never penalized in the record.** Signals change routing and predictor state, never evidence, mastery, certification or the demonstrated record (F2). The learner sees the consequence, not a penalty: "We'll revisit conditional independence, since you asked about it." Help is never withheld (intentions §13).
- **No double counting.** Hinted attempts are already dampened as evidence. In the predictor, the hint-depth arm *replaces* that dampening instead of stacking on it.
- **Repeated questions are not repeated evidence** (Plan B). Signal mass per LO per day is capped.
- **Reveals stay honest.** A question flagged `leak_suspected`, or one that revealed the answer, makes the attempt non-cold through the existing reveal ledger.
- **Curiosity is not confusion.** `other` and extension questions after a correct answer carry no negative signal.

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
| `lo_general+hints` | **Graded outcome by help depth** (§3.1). An unassisted correct answer is 1. A correct answer after `k` hints is `1 − 0.2k` (floor 0.2). Help requested before any work caps the outcome at 0.3. This replaces the hinted-attempt dampening inside the predictor; it doesn't stack with it | Constants a priori and versioned (D12) | Hint use is a standard knowledge-tracing feature; LearnLoop already logs it per attempt |
| `lo_general+tutor_signals` | **Typed questions as weak observations** on the mapped LO (§3.1): `prerequisite` → 0 on the prerequisite's LO at mass 0.15; `mechanism` or `clarification` after a correct answer → 0.5 at mass 0.1; `strategy` before attempting → treated as a hint; `verification` and `other` → no observation. Capped per LO per day | Masses a priori and versioned (D12) | Question density marks unresolved uncertainty but is not repeated ability evidence (Plan B tutor-dialogue compiler); interaction traces predict uptake (2609.12600) |
| `lo_general+retrievability` | For items with FSRS state, `β · logit(R_FSRS(t))`, combining ability with forgetting | `β = 0.5`; the report sweeps {0, 0.5, 1} | FSRS and mastery currently predict separately |
| `idea_hier` | Family effects `u_F ~ N(0, σ_F²)`, independent in v1 (practice-family track §5.1–5.2). Available after PF-a | `σ_F² = 0.5` | Families are the finest unit with a shared retrieval target |

**Observation model and inference** (shared by all challengers; the incumbent keeps `mastery.py` as is):
- **Observations.**
  - One 2PL observation per attempt row, using `mastery.py`'s probability-space EKF.
  - Sensitivity `H = a·p(1−p)`; noise `R = base_observation_variance · p(1−p) / w`, with `w = effective_mass`.
  - **Zero-mass rows are skipped**: quarantined, unassessable, or `excluded` revision.
  - **Primed attempts** shift `b` exactly as the attempt path does (`attempts.py:2458`). They are never discounted a second time through mass.
  - `dont_know` is outcome 0 at the configured attempt-type mass (`evidence.attempt_types.dont_know`, 0.7), as §3 says; a skip gives no row. Owner, 2026-10-12: new answers stop producing `dont_know` once "I'm stuck" replaces it (`implementation_handoffs.md` §4); historical rows keep this reading.
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
- **Assumed LOs** (§5.2) are drawn as an outlined bead labelled "assumed (not tested)", distinct from demonstrated beads. Well depth is unchanged (F8).
- **Deferred.** Showing a predictor's continuous inferred estimates on the map ("fog") is deferred (§11).

### 5.2 Starting new material: assumed known, checked in review (F2; live; successor; kill switch `placement.enabled`)

*Revised 2026-10-11 (owner, frictionless defaults; `docs/specs/daily_loop_frictionless_defaults.md` S1–S4).* There is no placement ceremony by default.

**After an import or study-map apply:**
- **No opening probe per topic.**
  - `_enter_initial_probes` (`substrate/state_sync.py:175-211`) no longer opens an initial diagnostic episode for every new LO (`placement.initial_probes = false`).
  - Diagnostic episodes still open when a wrong answer leaves a real choice of repair (existing probe machinery; intentions §11).
- **New material starts as learning.** It is ordered by prerequisites and by the active predictor's predicted difficulty, easiest first within a prerequisite layer. The first practice answers on each LO update the predictor: **practice is the placement.**
- **Your questions are the rest of the placement** (§3.1).
  - LOs you asked confused questions about while reading, or needed help before starting, are taught first and never fast-tracked on early answers alone.
  - LOs you breeze through without help or follow-up questions are fast-track candidates.
  - No probe is needed to find either.
- **Assumed known (not tested).** An LO is marked assumed when any of these holds:
  - **the learner says so:** "I know this" on the LO, its chapter or an item, or "too easy";
  - **fast-track:** its first ≥ 2 cold answers are correct **with no hints, no help before starting, and no confusion questions** (§3.1), and the active predictor gives `P(θ_L > θ_known) ≥ q` (D6);
  - **prediction:** an activated challenger with cross-LO sharing gives `P(θ_L > θ_known) ≥ q` before any attempt. With the incumbent `mastery_ekf` this can't happen; it requires §7.4.
- **What "assumed known" does:**
  - The LO's remaining learning items are not served as new material.
  - The LO enters maintenance with a long first interval (`placement.assumed_first_interval_days`, default 14). **That first review is the check:** a normal cold item. A pass keeps the LO in maintenance, now demonstrated. A failure quietly returns it to learning.
  - The map shows "assumed (not tested)" (§5.1).
  - Nothing assumed is certified or written as evidence (F2).
- **"I don't know this"** on an assumed LO returns it to learning immediately.
- **Optional quick check: "Check what I already know."** It is a button on the import result and on any LO, and is never prompted by default.
  - It opens a calibration session: `start_calibration_session(learning_object_ids=…, time_budget_minutes=…)` (`diagnosis/calibration_sessions.py:156`) with `CalibrationScreen`.
  - It serves up to k = 4 adaptive items with an early stop. Items are chosen by `conditional_gain`, or by plain predictive rate until a challenger is active. Answers are revealed at the end (`reveal_events`).
  - Its results feed the same split between learning and assumed.
- **Receipts.** `assumption_decisions` records every assumed-known decision: LO, source (`self_report` | `fast_track` | `predictor` | `quick_check`), `p` and interval, predictor and version, first-review due date, and the later outcome. Report 3 scores them.
- **Grader risk.** A grader that accepts a wrong answer could fast-track an LO wrongly. The first review catches that, and Slice 1's E1 measures grader error (D7).
- **When daily-loop Q7 exists,** "assumed known" maps onto maintain-level intent.

### 5.3 Not built here

- **Probe targeting by a predictor** (§11).
- **Re-entry after a lapse.** The daily-loop track owns re-entry (defaults P6). It can reuse the quick check for a few high-information checks after a break.

---

## 6. Persistence

| Table | Role (`db/table_roles.py`) | Contents |
|---|---|---|
| `facet_outcome_observations` | DERIVED (rebuild owner) | §3 |
| `learner_predictor_snapshot` | DERIVED (rebuild owner; only while a non-incumbent predictor is active) | Per region: `mean`, `variance`, `n_eff`, `untested`, `predictor`, `version`, `as_of_observation_id` |
| `question_classifications` | WORKFLOW (paid outputs; never re-run on rebuild) | LLM classification of tutor and reader questions missing `question_type` or facets: `question_event_id` / `interaction_event_id`, type, mapped LO and facets, model, prompt version (§3.1) |
| `assumption_decisions` | RECEIPT | `id`, `lo_id`, `source` (`self_report` \| `fast_track` \| `predictor` \| `quick_check`), `trigger_ref`, `p`, interval, `q_used`, `predictor`, `predictor_version`, `first_review_due`, `quick_check_session_id?`, `created_at`. Its outcome is joined from the first review's attempt by report 3, never written back |

- **Config:**
  - `[field]`: `enabled`, `active_predictor` (default `mastery_ekf`), arm constants (D3), `legacy_fallback` (`exclude` \| `current_content`, default `exclude`).
  - `[placement]`: `enabled`, `initial_probes` (default false), `assumed_first_interval_days` (14), `fast_track_min_correct` (2), quick-check `k` (4) and `budget_minutes` (8), thresholds.
- **Algorithm versions:**
  - F1 needs none: derived tables plus a display change.
  - F2 (no opening probes plus assumed known) is one successor.
  - Activating a challenger predictor is a further successor.

---

## 7. Evaluation

### 7.1 Correctness gates (pass/fail)

| Id | Gate |
|---|---|
| G1 | **Deterministic rebuild:** the same inputs give byte-identical derived tables (hash compared on fixture copies) |
| G2 | **Zero LLM and embedding calls** during rebuild or replay (fakes assert) |
| G3 | **No evidence writes:** an import-linter contract forbids predictor packages from importing evidence writers. Evidence, mastery, facet-recall and certification tables are byte-identical with the field on vs off |
| G4 | **Honest labels:** no region is labelled demonstrated or certified without direct evidence. Every assumed LO is labelled "assumed (not tested)" and has a scheduled first review |
| G5 | **Knowledge-model alignment:** no prior or update propagates along `part_of`, `related`, `analogous_to` or `confusable_with`, and no LLM relation edges are read |
| G6 | **Never blend:** with the untested state on vs off, well depth and demonstrated beads are identical except at untested points (vitest) |
| G7 | **Assumptions are reversible and evidence-free:** a failed first review, or "I don't know this", returns the LO to learning. Nothing assumed writes evidence or certification |
| G8 | **Reproducibility:** quick-check selection given a snapshot is deterministic (ties broken by item id). `assumption_decisions` records everything needed to recompute each decision |
| G9 | **Kill switches:** with `placement.enabled = false` (initial probes back on, no assumptions), or the active predictor reverted, episode entry, serving and ordering match the previous version on fixture copies |
| G10 | **Consumers use the interface:** placement and map modules can't import any predictor's internals (import-linter) |
| G11 | **Only calibrated-uncertainty predictors can be active:** config validation rejects the others |
| G12 | **Weight and provenance invariances:**<br>• zero-mass rows leave every posterior byte-identical;<br>• primed handling matches `mastery.py` (at one LO, `lo_general` with `σ_g² → 0` reduces to it);<br>• every outcome row has a `revision_status`, and with `exclude` no current content substitutes for a missing revision |
| G13 | **Asking is never penalized in the record:** with interaction signals on vs off, evidence, mastery, certification and demonstrated beads are byte-identical. Only routing and predictor state may differ. The hint-depth arm replaces, rather than stacks on, hinted-attempt dampening. Signal mass per LO per day respects its cap |


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
  | `llm_probability` V1–V3 | **Optional, off by default** (D8). Three input variants of one sensor, run together as one offline comparison (revised 2026-10-11, owner). Details are below the table |

- **`llm_probability` variants** (added 2026-10-11, owner). They test whether the model predicts better from the learner's rich history than from the item alone. JevKT (2610.11135) fed only a 25-item right/wrong window and found more marks added nothing, but never tested answer text, error traces or diagnoses.
  - **Models: two, each running every variant** (owner, 2026-10-12: see which works best). That makes six arms.
    - **Perplexity Decider v1.1** (`perplexity/pplx-decider-v1.1-27b` via OpenRouter; route `ai.routing.llm_probability_decider`). Its prediction is P(yes) on one `noul` question.
    - **A frontier LLM** (route `ai.routing.llm_probability_llm`; unset falls back to the active provider, and Codex on the owner's subscription is allowed). Its prediction is a verbalized probability, returned through structured output.

    Router spec §6 has the client details. Jev is not used.
  - **The question:** "Will the learner answer this item correctly on this attempt?"
  - **The variants:**

    | Variant | `state` sent to the model |
    |---|---|
    | **V1 item only** | The item stem, its LO and facet names, and its difficulty prior (solver-panel difficulty once Phase 5a lands; otherwise empirical or authored) |
    | **V2 right/wrong window** | V1, plus the learner's last 25 graded interactions as (item, KC names, correct/incorrect). This reproduces JevKT's history format, without its population statistics, which LearnLoop doesn't have |
    | **V3 rich state** | V1, plus a `LearnerStateCardV1`-style rendering restricted to this LO and its prerequisite neighbours: recent answers (excerpts), blind grades, diagnosis hypotheses with evidence, hints and their timing, typed tutor questions, and the active predictor's numbers. Same token budget as the router card (router spec §4) |

  - **Recalibration.** Each variant is reported raw and with one-parameter recalibration fit on past predictions only.
  - **No leakage.** A prediction never includes the outcome being predicted, or any material revealed after the attempt began.
  - **Spend and storage.** Spend-capped, with `--dry-run` first. Responses are cached outside the vault, so replay makes zero calls.
  - **What the result decides.**
    - If V3 clearly beats V2 (bootstrap interval excluding 0 at D9's margin), the rich history carries information the numeric arms miss. That is evidence for the router's card (router spec §4), and for reconsidering `idea_hier_llm_prior` (§11).
    - If V1 ≈ V2 ≈ V3, the models' value lies in judgment, and the numbers keep coming from the explicit arms.
    - The Decider-vs-LLM split within each variant is reported too, as the router's first evidence on which model to weight (router spec §10).
  - **Retired and merged arms** (owner, 2026-10-12, at the router R0 merge).
    - Phase 2's numeric `llm_probability` arm is retired, with its route `ai.routing.field_llm_probability`. `--llm-cache` and `--prepare-llm` now serve only these V1–V3 arms. A vault that still sets the route loads; `learnloop doctor` warns that the value is ignored.
    - Slice 2 T8's zero-data LLM arm is the V2 arm on the LLM judge (`llm_probability/v2/llm`), reported in the T8 report under its pre-registered names (`llm_zero_data`, `llm_zero_data:recalibrated`). One implementation, one cache and one ledger, so the two are comparable and paid for once. T8's registered arm had no difficulty prior; its pre-registration is unchanged and the report records the alias.
    - The comparisons stay pooled. Attempts without a provable start (no scheduler offer or diagnostic presentation) count as they are, with no history shown.
- **Population memory-model arm** (optional; added 2026-10-12).
  - **What it is:** a content-agnostic recall model pretrained on a population. It sees only review timing and grades, like the population sequence models in the public srs-benchmark. Public results favour such models over per-user FSRS fits.
  - **Comparison:** run as an arm against FSRS (fitted weights and `FSRS6_DEFAULT_WEIGHTS`) on retention prediction for graded cold reviews.
  - **Only if usable:** build it only if a usable pretrained model or its training code and data are published with a compatible license. Check first; don't train one here.
  - **Live use:** none. A win would become a separate retention-model successor decision.
  - **Never active** (G11): this is a point predictor.
- **Metrics.**
  - Log loss, Brier, a reliability diagram, and AUC at attempt level.
  - Splits: **first attempt on a never-seen LO vs later attempts** (cross-LO prediction only matters for the first), serving origin, revision status and topic.
  - Bootstrap intervals clustered by attempt.
  - A version manifest: arm hashes, algorithm, config hash, data snapshot.
- **Outputs.** JSON plus markdown, aggregates only and never learner text. Written to a path the owner chooses (default `fixtures-local/reports/`).

### 7.3 Reports

1. **Prequential replay (F1).** Every arm on the owner's graded log, with the splits above.
   - **Key question:** does `lo_general` (or an extension) beat `mastery_ekf` on first attempts at never-seen LOs?
   - **Extra split for the signal arms:** attempts preceded by tutor questions or hints vs those without. This shows whether `+hints` and `+tutor_signals` earn their place.
   - **Validity:** at n=1 this detects only large differences.
2. **Fast-track simulation (F1).** On historical LOs, apply §5.2's fast-track rule to the first answers, then score the later attempts.
   - **Reported:** the share that would have been assumed known, and their **miss rate** (later failures).
   - **Named bias:** history shows only what was actually served.
3. **Assumption report (after F2).**
   - **Reported:**
     - first-review miss rate **by source** (self-report, fast-track, predictor, quick check);
     - returns to learning;
     - learning minutes saved against the estimated minutes of learning every new LO.
   - **Named confounds:** learning and forgetting before the first review, and goal-frontier serving in that window.

### 7.4 Switching rule (simplest is the incumbent)

**How a challenger is activated.**
- **Who can challenge:** `lo_general`, an extension, the composite, or `idea_hier`.
- **Conditions:** it beats `mastery_ekf` on report 1's attempt-level log loss (overall *and* on the first-attempt split), with a bootstrap interval excluding 0 and the margin fixed before the run (D9). Its report-2 miss rate must also be no worse.
- **"Can't tell" keeps the incumbent.**
- **The switch:** activation is a successor with a kill switch.

**What activation enables.** It is also the held-out support that knowledge-model §8.3 requires before cross-LO sharing (the general level) can steer a live decision. Until a challenger is activated, quick-check ordering uses the plain predictive rate, fast-track uses `mastery_ekf`, and nothing is assumed known before an attempt except by self-report.

---

## 8. Rollout

| Step | Contents | Needs | Gate |
|---|---|---|---|
| **F0** Prerequisites | The dormant/resolved-LO serving fix (daily-loop track); Q7 when available | — | Blocks F2 only |
| **F1** Predictors, harness, untested state | §3, §4, §5.1, §7.2, reports 1–2, `data-check` | — | G1–G6, G10–G12; owner reviews reports 1–2 once |
| **F2** Starting new material | §5.2: no opening probes; assumed known by self-report, fast-track or activated predictor, checked in the first review; optional quick check. Successor + kill switch | F0 fix; F1 reports reviewed | G4, G7–G9; report 3 after several imports |
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
- **`test_assumed_known.py`:**
  - no initial episodes for new LOs by default, while error-driven episodes still open;
  - each source (self-report, fast-track, predictor, quick check) marks an LO assumed and schedules its first review;
  - fast-track needs ≥ `fast_track_min_correct` cold correct answers and the threshold;
  - predictor-based assumption is impossible under the incumbent;
  - a failed first review or "I don't know this" returns the LO to learning (G7);
  - no evidence or certification writes;
  - `assumption_decisions` is complete (G8);
  - the kill switch restores initial probes exactly (G9).
- **`test_interaction_signals.py`:**
  - signal derivation from `question_events`, hint counts and timing, and reader questions;
  - LLM classification only when the type is missing, cached, and with zero calls on rebuild;
  - confusion signals block fast-track, while "I know this" still assumes known;
  - curiosity questions carry no negative signal;
  - leak-suspected questions make the attempt non-cold;
  - G13.
- **`test_quick_check.py`:** an optional calibration session with adaptive selection and early stop, reveal at the end, and results feeding the assumed/learning split.
- **`test_map_untested.py`** (sidecar RPC + vitest): untested and assumed points are drawn distinctly from demonstrated ones; G6.
- **Durability lane:** a rebuild of the derived tables under production pragmas on a fresh vault.

---

## 10. Open decisions

| # | Decision | Recommendation |
|---|---|---|
| D1 | Active predictor at launch | `mastery_ekf`, the existing per-LO filter. Challengers earn activation (§7.4) |
| D2 | Cross-LO structure in `lo_general` | A shared general level only; no graph coupling (knowledge-model §8.1, §8.3). Prerequisite-directed coupling is deferred (§11) |
| D3 | Extension-arm constants | `γ = 0.2`; capability `N(0, 0.5²)`; relation means 0 / −0.25 / −0.5 (sd 0.5); retrievability `β = 0.5` (sweep 0, 0.5, 1). Versioned, never fitted to the owner |
| D4 | Quick check | Optional, never prompted; k ≤ 4, ≤ 8 minutes, adaptive with an early stop |
| D5 | Self-report | "I know this" or "too easy" marks an LO assumed known immediately; "I don't know this" returns it to learning immediately. No triage screen |
| D6 | Fast-track and first review | ≥ 2 cold correct first answers and `P(θ_L > θ_known) ≥ q`, with `q = 0.8` at `θ_known = logit(0.75)` (0.9 if report 2 lacked data); first review after 14 days. Tune from report 3 |
| D7 | Wait for Slice 1's grader probes before F2? | No, per the owner's live-with-kill-switch preference. Confirm probes are the safety net; review E1 when Slice 1 produces it |
| D8 | `llm_probability` | Off by default. The V1–V3 comparison (§7.2) runs once, offline, owner-run and spend-capped, on both Perplexity Decider v1.1 (via OpenRouter) and a frontier LLM |
| D9 | Switching margin | The attempt-level log-loss improvement's bootstrap interval excludes 0, overall and on first attempts, and the miss rate is no worse. Fixed before running. *T8 (`spec_embedding_consumers_v1.md` §11) uses only this margin (0), with its own registered interval: a cluster-robust t interval over items, not this bootstrap interval* |
| D10 | Revisions missing from snapshots | `exclude` by default; `current_content` only by explicit config, flagged |
| D12 | Interaction-signal constants | Hint depth: `1 − 0.2k` (floor 0.2), and help before any work caps at 0.3. Typed-question masses: 0.15 (prerequisite), 0.1 (mechanism or clarification after a correct answer); capped per LO per day. A priori and versioned, and the harness reports a sweep. Routing use (§5.2) is live with F2; predictor use waits for §7.4 activation |
| D11 | Opening probes for new LOs | Off by default (`placement.initial_probes = false`). Diagnosis happens when a wrong answer leaves a real choice of repair |

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
| **Learned action router** (frozen or fine-tuned embeddings, LoRA) | The non-learned router is specified in `spec_action_router_v1.md`: Perplexity Decider v1.1 and a frontier LLM competing inside the P4 staged frame, with exact propensities. A learned scorer's trigger is in that spec's §13 |
| **Facet dossiers** | Not deferred: **moved** to the practice-family track as the practice index (`spec_embedding_consumers_v1.md` §5.9) |

---

*Related: [[Pipeline Augmentation Plan]] (workstream B) · `spec_knowledge_model.md` §8 · `spec_slice_a_practice_and_field_v1.md` · `spec_embedding_consumers_v1.md` §5 · `learner/mastery.py` · `diagnosis/calibration_sessions.py` · `docs/algorithm-change-playbook.md` · [[Bitter Lesson Research Sweep]]*

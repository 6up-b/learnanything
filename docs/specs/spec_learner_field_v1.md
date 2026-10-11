# Learner field — placement, probe targeting, and map uncertainty (v1)

**Status:** draft for owner review (2026-10-11). This is the first implementation slice of workstream B ("Learner field + two-projection state communication") in `docs/brainstorming/Pipeline Augmentation Plan.md` (lines 216–277).
- It builds the probabilistic field and three consumers:
  - **(1)** placement after import;
  - **(2)** choosing where to probe next;
  - **(4)** an uncertainty layer on the knowledge map.
- The transfer-gap alarm, feature (3), is out of scope (§1).
- **Implementation order (owner, 2026-10-11):** S0b–S3, S5 and S7 are built as part of Slice A (`spec_slice_a_practice_and_field_v1.md`), ahead of Slice 1. S0b is Slice A Phase 1. There are no shadow stages; each live consumer is a successor with a kill switch.

**Source material:**
- Plan B and its refusal list (the guards in §2 come from there).
- `docs/brainstorming/Bitter Lesson Research Sweep.md` §5: learning rates vary little between learners while starting knowledge varies a lot (2604.03246); LLM difficulty labels correlate at ρ = 0.06 with real difficulty (2609.27063).
- The daily-loop audit and open questions Q0–Q18 (chat, 2026-10-11; not yet answered by the owner).

**Relationship to other documents:**

| Document | Relationship |
|---|---|
| Plan workstream B | This spec implements the field's estimator and three consumers. It inherits B's guards: derived and replayable, density guard, no per-learner-fitted hyperparameters, metric claims only. `RouterStateV1` / `LearnerStateCardV1` and the B0.5 temporal residual are not built here |
| Slice 1 (`spec_blind_grading_diagnosis_split_v1.md`) §9 | Prerequisite 2 pulls its embedding substrate forward on its own: `EmbeddingClient` (OpenRouter `qwen/qwen3-embedding-8b`), `embedding_vectors`, the backfill command, model-change re-embedding. Nothing from the diagnoser is needed |
| Slice 2 (`spec_embedding_consumers_v1.md`) | Uses its `facet/definition` and `concept/definition` record kinds and R2's wrong-tool list. Optional: PF solver-panel difficulty (§5.4) and P12 (the `activity_families` overlap) if placement items need a family |
| `learner/mastery.py` | The field's observation model is the existing 2PL EKF, generalized from one LO to a vector of facets (§5). The module's docstrings cite `spec_irt_difficulty.md`, which is not in `docs/specs/` |
| Daily-loop questions Q5, Q7, Q9, Q11 | Gate placement-live and probe-targeting-live (§2 F7, §9) |

**What exists in the code today (audited 2026-10-11):**
- **Placement means "probe every new topic once".**
  - Every active, unattempted LO that has an active item or is in an active goal's scope gets an initial diagnostic episode (`substrate/state_sync.py:175-211`, `_enter_initial_probes`).
  - One qualifying observation completes it (`config/schema.py:206-208`, `placement_minimum_observations = 1`).
  - Nothing infers one topic from another.
- **Per-LO Bayesian mastery already exists, independent per LO.**
  - `learner/mastery.py` runs a 2PL EKF on a logit-scale state (`logit_mean`, `logit_variance`).
  - Variance grows by drift: `P + sigma2_drift·days`, capped at `p_max` (`:342-353`).
  - Observations are reliability-weighted (`observation_weight`, `:321-339`).
  - Item difficulty is an empirical-Bayes `b` with a strong prior (`resolve_item_irt_params`, `update_item_difficulty`, `:381-447`).
  - Learner claims set the prior (`covering_learner_claim`, `apply_claim_evidence`).
- **Per-facet state is a Beta per facet × capability with no cross-facet smoothing.** It lives in `facet_recall_state` and `facet_capability_evidence` (migration 037; DERIVED). This plus per-LO mastery plus FSRS is the **no-smoothing baseline** (§8.2).
- **Probe machinery:**
  - Re-probing for stale uncertainty uses per-LO `logit_variance ≥ reprobe_stale_uncertainty_variance` (0.6) after 30 days (`diagnosis/probe_episodes.py:528-572`, called from `state_sync.py:156-158`).
  - The queue's probe term is `probe_eig_weight = 0.25` (`config/schema.py:81`).
  - Diagnostic blocks already select several items jointly by greedy expected information gain (EIG) (`plan_precommitted_block`, `probe_episodes.py:1196`).
- **Serving propensities are mostly unknown.**
  - The scheduler computes design propensities (`_selection_propensities`, `scheduling/scheduler.py:1494`).
  - But the queue is a list the learner picks from, so every candidate is logged `propensity_kind = "unavailable_composed_offer"` (`scheduler.py:629, 682`).
  - What was offered, and which candidate was answered, is recorded: `scheduler_offer_receipts` and `submission_intents.scheduler_candidate_id` (migration 161).
  - Probe presentations are chosen by the system and carry selection telemetry.
- **The map draws no inferred state.**
  - `get_knowledge_map` (`learnloop_sidecar/handlers/knowledge_map.py:46`) gives a facet with no recall state `ready = 0.5` and variance 1/12 (`:362-374`).
  - `KnowledgeWellView.tsx` makes well depth `ready · visibility(evidenceMass)`. Demonstrated status is a separate bead channel, never a second depth (`:7-25`).
- **No GP, graph kernel, or embedding code exists** (grep: no `gaussian`, `heat_kernel`, or `matern` in `src/learnloop`).

---

## 0. Thesis

Today LearnLoop knows only the regions it has measured directly. A freshly imported book costs one probe per topic, and every unvisited facet sits at "ready = 0.5", indistinguishable from a facet you've never been near.

The learner field keeps one Gaussian belief over **all** facets jointly. Facets are coupled by a graph that combines authored structure with embedding neighbourhoods. Each graded answer then moves nearby, unmeasured facets a little and shrinks their uncertainty.

This makes three things cheap:
- **Placement.** A few well-chosen questions place you across a whole import. Starting knowledge varies widely between learners while learning rates don't (2604.03246), so placement is where your scarce evidence buys the most.
- **Probe targeting.** Probe where the field is most uncertain about something you care about.
- **Honest maps.** Show "estimated from nearby evidence" separately from "demonstrated", and show "unknown" where nothing is nearby.

**The field is a smoother over the ledger, not a replacement for it.**
- Grades, certification, cold checks, and per-LO mastery are unchanged.
- The field is a DERIVED projection that never writes evidence.
- **Revised 2026-10-11 (owner):** consumers go live without a shadow period.
  - The S2 replay report against the no-smoothing baseline is reviewed once before the first consumer switches on.
  - Each live consumer is its own algorithm successor with a kill switch.
  - Confirm probes and receipts measure the consumers afterwards.

---

## 1. Scope

**In scope:**
- **A1.** Prerequisite 2: the embedding substrate pulled forward, plus embeddings of facet definitions and LO summaries (§4.1).
- **A2.** Prerequisite 3: a symmetric per-facet outcome view (§4.2).
- **A3.** The field: graph, prior, observation model, inference, outputs (§5).
- **A4.** Consumer (4), the map uncertainty layer (§6.1).
- **A5.** Consumer (1), placement: live (§6.2). The shadow stage S4 was dropped on 2026-10-11.
- **A6.** Consumer (2), probe targeting: live (§6.3). The shadow stage S6 was dropped on 2026-10-11.
- **A7.** Replay reports and correctness gates (§8).

**Out of scope:**
- **The transfer-gap alarm**, feature (3). It needs PF variant labels.
- **Retention timing and neighbour credit spreading.** The field never moves a review date, and a success on facet A never counts as a review of B.
- **Grading, evidence, certification, and recurrence.**
- **The B0.5 GRU/SSM residual, cross-vault priors, and `RouterStateV1`.**
- **Capability and representation regions.** v1's region is the facet (§11 D1).

---

## 2. Standing constraints

Inherited: plan invariants 1–15; Slice 1 S6/S7 (no step depends on embeddings for correctness; replay never calls an LLM or the embedding API); Slice 2 R1/R2. In addition, from Plan B:

- **F1. Derived and replayable.**
  - Field state is rebuilt deterministically from ledgers, vault content, and stored vectors.
  - A rebuild makes zero LLM or embedding calls.
  - If vectors are missing, the graph falls back to authored edges only and the snapshot records it.
- **F2. Never evidence.**
  - The field writes only its own DERIVED and RECEIPT tables. It never touches `grading_evidence`, `facet_recall_state`, `facet_capability_evidence`, mastery, certification, or coldness.
  - "Likely known" is a scheduling and display claim, never "demonstrated".
- **F3. Live changes go through the playbook.** *Revised 2026-10-11 (owner): no shadow periods.*
  - Each consumer that changes what is served is its own algorithm successor under `docs/algorithm-change-playbook.md`.
  - Each sits behind a kill switch that restores the previous behaviour exactly.
  - Each logs receipts of what it did and, where cheap, what the old rule would have chosen.
  - The S2 replay report is reviewed once before the first consumer switches on.
- **F4. Density guard.**
  - A facet with too little nearby evidence reports `unknown` and prior variance. It never reports a confident inferred value.
  - Computational shortcuts (kNN sparsification, truncation, variance caps) may only widen reported variance.
- **F5. No per-learner-fitted hyperparameters.**
  - Kernel bandwidth, prior variance, and edge weights are set a priori from interpretable targets (§5.2) and versioned in config.
  - The replay report includes a sensitivity sweep; the field is not tuned on your log.
- **F6. Metric claims only.** The field speaks in distances, neighbourhoods, means, and variances, never in coordinates or "directions" in embedding space. Embeddings never decide difficulty, isomorphism, or prerequisite direction (Slice 2 R2). The graph is undirected for smoothing, and direction-bearing edges keep their authored type.
- **F7. Biased sampling is declared, not ignored.**
  - Raw per-region averages are biased because the scheduler chose what you saw.
  - Every observation records its **serving origin**: learner-picked list row (propensity unknown), system-chosen probe presentation (propensity logged), forced follow-up, or requested.
  - Model-based posteriors are used, not raw means.
  - Off-policy claims in reports use only system-chosen observations until a finite system-ordered plan exists (daily-loop Q9).
- **F8. Never blend.** In the UI, inferred values never change well depth, demonstrated beads, or the "ready" number (owner's well-view contract, `KnowledgeWellView.tsx:7-25`).

---

## 3. Prerequisites and their order

| # | Prerequisite | Built here? | Blocks |
|---|---|---|---|
| **P1** | **Daily-loop decisions and fixes.**<br>• Q7: one intent control the queue reads.<br>• Q11: a new-material policy.<br>• Q9: a finite plan the system orders, which makes propensities known.<br>• Q5: placement or pre-questions at import.<br>• The dormant/resolved-LO serving bug. | No: owner decisions plus daily-loop work | *Revised 2026-10-11:* nothing blocks. Placement uses minimal semantics until Q7/Q11 exist (§6.2). Q9 improves evaluation only (F7) |
| **P2** | **Embedding substrate**, pulled forward from Slice 1 §9 on its own | Yes, as a subset (§4.1) | The graph's embedding edges. Without it the field runs on authored edges only |
| **P3** | **Symmetric per-facet outcome view** | Yes (§4.2) | The field |
| **P4** | **The field**, with its replay report | Yes (§5, §8.2) | All consumers |
| **P5** | **Placement items at import** | Partly. Imported exercises, plus PF-b's published verified items (Slice A Phase 5). With no eligible items, today's per-topic initial probes run | Placement on reader-on imports |

**Order:** P2 → P3 → P4 + replay report → map layer → placement live (+ P5) → probe targeting live (§9). P1 proceeds in parallel and refines placement once it exists.

---

## 4. Prerequisite contracts

### 4.1 Embedding substrate and region text (P2)

- **Pulled forward from Slice 1 §9.1–9.2:**
  - `ai/embedding.py` with the `EmbeddingClient` protocol;
  - the OpenAI-compatible client against OpenRouter (`qwen/qwen3-embedding-8b`, `data_collection = "deny"`);
  - `embedding_vectors` (WORKFLOW);
  - the backfill command;
  - receipts via `model_call(purpose="embedding")`.

  If Slice 1 has not landed migration 166, this slice lands the `embedding_vectors` table at the next free migration number and Slice 1 reuses it.
- **Record kinds and text recipes** (Slice 2 R3: canonical or LLM-written text only):

| `record_kind` / `field` | Text | Source |
|---|---|---|
| `facet/definition` | title + `claim` + `description` + `preconditions` + up to two `positive_examples` | `EvidenceFacet` (`vault/models.py:766+`) |
| `learning_object/summary` (new) | title + `concept` + `summary` | `LearningObject` (`vault/models.py:320+`) |

- **Legacy facets.** A schema-v1 facet with only a title and no claim does not get an embedding edge from its own text, because a title alone is too short to place it. It inherits edges from its LO's summary embedding (§5.1).
- **Content changes.** Vectors are keyed by `content_hash`. An edited facet re-embeds on the next backfill, and the graph rebuild uses the newest vector per record.

### 4.2 The per-facet outcome view (P3)

The field needs, for every graded attempt and every facet it bears on: pass/fail in both directions, its reliability, whether it was cold, the item, and how it came to be served.

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

## 5. The field (P4)

### 5.1 Graph

- **Nodes:** active canonical facets, F of them; hundreds per vault.
- **Weighted undirected adjacency:** `W = W_auth + W_emb`.
  - **`W_auth`** comes from authored structure, lifted to facets:
    - same LO blueprint: `w_bp`;
    - an LO `prerequisites` link or concept `prerequisite` edge between the facets' LOs/concepts: `w_pre`;
    - concept `part_of`: `w_part`;
    - concept `related`: `w_rel`;
    - `confusable_with`: `w_conf`, **0 by default**, because confusables share surface, not ability (D3).
    - Concept edges reach facets through `LearningObject.concept` and blueprint membership. Each lifted edge is scaled by the authored `ConceptEdge.strength`.
  - **`W_emb`:** a symmetric kNN graph (k neighbours) over **mean-centered** `facet/definition` vectors. The weight is `max(0, cos − c₀) / (1 − c₀)`. Legacy facets without a definition vector use their LO's `learning_object/summary` neighbours at a reduced weight, `w_lo`.
- **Normalized Laplacian:** `L = I − D^{-1/2} W D^{-1/2}`.
- **Disconnected facets** (no edges) are their own components and keep prior variance (F4).

### 5.2 Prior

- **Latent ability per facet**, on the logit scale: `θ ∈ ℝ^F`, with `θ ~ N(m₀, K)`.
- **Prior mean `m₀`:**
  - per facet, the covering learner claim when one exists (reusing `covering_learner_claim`; weak);
  - otherwise 0.
- **Covariance:** a heat kernel `K = σ₀² · D_s · exp(−t L) · D_s`, where `D_s` rescales so `diag(K) = σ₀²`.
  - `σ₀² = mastery.cold_start_prior_logit_variance` (3.0), the same prior uncertainty the per-LO EKF starts from.
  - Graph Matérn is an alternative (D2).
- **Hyperparameters are set a priori (F5), from interpretable targets, versioned as `field.kernel_version`:**
  - `t` is chosen so the median prior correlation is ≈ 0.5 for one-hop blueprint neighbours and ≤ 0.1 at three hops;
  - `k = 8`, `c₀ = 0.35`;
  - `w_bp = 1.0`, `w_pre = 0.6`, `w_part = 0.6`, `w_rel = 0.3`, `w_lo = 0.5`, `w_conf = 0`.

  These are starting values, not fits. §8.2 reports a sensitivity sweep around them.

### 5.3 Observation model

- **Each `facet_outcome_observations` row is one 2PL observation:** `y ≈ σ(a(θ_f − b))`, using `mastery.py`'s probability-space EKF.
  - **Sensitivity:** `H = a·p(1−p)`.
  - **Measurement noise:** `R = base_observation_variance · p(1−p) / w`, with weight `w = effective_mass · facet_share`. *Revised 2026-10-11:* there is no weight floor.
    - **Zero-mass rows are skipped.** A row with `w ≤ 1e-9` (quarantined, unassessable, excluded revision) applies no update. Under the previous `max(w, 0.10)` floor, quarantined rows still moved the field.
    - **Per-attempt information budget.** `facet_share` sums to 1 per attempt, so one attempt's total precision `Σ_f w_f / base` equals what a single-facet attempt of the same mass would contribute. Spreading an attempt over more facets dilutes each facet's update rather than multiplying the attempt's influence.
- **Item offset.**
  - `(a, b)` come from `resolve_item_irt_params`: the empirical-Bayes `b` when enabled, otherwise the authored difficulty, otherwise the LO prior, otherwise the default.
  - **LLM-estimated difficulty is never trusted as a point value** (ρ = 0.06). When `difficulty_source ∈ {"llm_estimate", None}`, `b` is treated as uncertain. Its variance `σ_b²` (default 1.0) is folded into noise: `R += a²·p²(1−p)²·σ_b²`. This only widens.
  - PF solver-panel difficulty (`difficulty_source = "solver_panel"`, Slice 2 §5.4) gets the authored treatment when present.
- **Weights.**
  - Cold attempts use full weight.
  - Assisted attempts arrive discounted through `effective_mass`.
  - **Primed attempts** follow `mastery.py` exactly (revised 2026-10-11). The item's `b` is shifted easier by the same primed shift the attempt path applies (`attempts.py:2458`), so a primed success barely moves θ and a primed failure moves it strongly. Primed rows are not discounted a second time through mass.
  - `dont_know` gives outcome 0 at full attempt-type mass, as in `derive_facet_outcomes`.
  - A skip gives no row.
- **Regrades.** Superseded grading epochs are dropped; the latest epoch is used.

### 5.4 Inference and time

- **Sequential EKF over the joint state `(μ, Σ)`, in time order.**
  - Each observation applies a rank-1 update along the facet's column of `Σ`.
  - This is exact linear algebra at F ≤ ~1,000: O(F²) per observation and O(N·F²) for a full rebuild. At ~10³ observations and F = 500 that is about 2.5 × 10⁸ flops, a few seconds in numpy.
  - Laplace or EP batch inference is an alternative with the same outputs (D2).
- **Time.** Between observations Δ days apart, `Σ ← Σ + σ²_drift · Δ · K/σ₀²`, with diagonal entries capped at `p_max`.
  - This is the existing drift form (`mastery.py:342-353`), correlated along the graph.
  - No mean decay: retention timing stays FSRS's job, and the field estimates ability, not today's recall.
- **Numerics.** Σ is kept symmetric positive-definite by a jitter that only adds variance (F4). Exact rebuilds use float64; determinism is enforced by fixed observation ordering (`observed_at`, then `attempt_id`, then `facet_id`).

### 5.5 Outputs (per facet, per snapshot)

| Output | Definition |
|---|---|
| `mean`, `variance` | Posterior `μ_f`, `Σ_ff` |
| `p_available` | `E[σ(θ_f)]`, by probit approximation |
| `interval80` | `σ(μ_f ± 1.2816·√Σ_ff)` |
| `n_eff` | `σ₀²/Σ_ff − 1`: the information gained, in units of the prior |
| `direct_mass` | Σ of `effective_mass · facet_share` of the facet's own rows |
| `inferred` | true when `direct_mass` < `field.direct_threshold` (default 0.5) but `n_eff` ≥ `field.unknown_threshold` (default 0.25) |
| `unknown` | true when `n_eff` < `field.unknown_threshold`, **or** the graph distance to the nearest facet with direct evidence > `field.max_support_hops` (default 3) (F4) |
| `support` | The top 3 facets and attempts contributing to the posterior shift (influence = covariance-weighted innovation), for explanations |

---

## 6. Consumers

### 6.1 (4) Map uncertainty layer

- **RPC.** `get_knowledge_map` gains an optional `field` block per point: `p_available`, `interval80`, `inferred`, `unknown`, `support`, `field_version`. It is computed from the latest snapshot and absent when the field is disabled.
- **Existing fields are unchanged:** `ready`, `ready_ghost`, `ready_variance`, `evidence_mass`, `demonstrated_mass`.
- **Rendering in `KnowledgeWellView`, with an "Estimated from nearby evidence" toggle that is on by default** (revised 2026-10-11) and hides the layer when off:
  - **`inferred` facets:** a stippled fog over the sector. Fog density ∝ `1 − variance/σ₀²`, and its tone encodes `p_available` in a separate fog palette, never the well palette. Well depth stays `ready · visibility(evidenceMass)`, so inferred-but-unmeasured facets stay flat.
  - **`unknown` facets:** no fog and a small `?` glyph. A blank is honest ignorance.
  - **Demonstrated beads, ghost rings, and decay markers are unchanged** (F8).
- **Side panel:** "Estimated 62% (80%: 38–81%) from nearby evidence: [support facets], [n] answers. Not demonstrated."

### 6.2 (1) Placement after import

**When.**
- **Trigger:** an import or study-map apply that adds ≥ `placement.min_new_facets` (default 4) active facets in a goal's or the import's scope.
- **Placement items must exist.**
  - Imports that create items qualify: exercise import, ingest-exam mode, and Quick Add with the reader off.
  - Reader-on imports have no items until sections are read (P5). They qualify once PF-b has published verified items for the imported topics (Slice 2 §5.3–5.4; Slice A Phase 5).
  - With no eligible items, today's per-topic initial probes run unchanged.

**Selection.** Choose a set S of at most `placement.k` items (default 4, within about 8 minutes) from the eligible items `I_new` (active, unattempted, not exam-reserved, not reveal-burned). Greedily maximize:

```
gain(i | S) = Σ_f g_f · ( (Σ_S h_i)_f² / (h_iᵀ Σ_S h_i + R_i) )  −  λ · minutes(i)
```

- `Σ_S` is the covariance after conditioning on the already-picked items. That conditioning is predicted variance reduction only, with no outcome needed, because the linearized variance update doesn't depend on y.
- `h_i` holds the item's facet loadings: `facet_share · a·p(1−p)` at the prior mean.
- `R_i` is its noise at full cold weight.
- `g_f` = 1 for facets in the import or goal scope, and `placement.g_outside` (default 0.2) otherwise.
- `minutes(i)` comes from your own past durations per item type, with a flat 3-minute fallback.

This is the field's analogue of `plan_precommitted_block`'s greedy joint EIG (`probe_episodes.py:1196`), and it reuses that path. Presentations are committed in order, carry `placement_block` telemetry with each pick's gain, and are served as a precommitted block. That makes them system-chosen observations with logged propensities (F7).

**Learner experience.**
1. **Offer:** "Quick placement: 4 questions (~6 min) so LearnLoop can skip what you already know." Choices: **Start / Later / Skip placement**. Skipping is never negative evidence.
2. **Each question** has **"I don't know"** (recorded as `dont_know`) and **Skip** (no row). Hints are off.
3. **Answers are revealed at the end of the block.** Every reveal is recorded in `reveal_events`, so later cold checks on those surfaces stay honest.
4. **Results screen.** Each facet in scope is shown in one of three groups, in plain language and never as "mastered" or "demonstrated":
   - **"Likely known — we'll check again around [date]":** `P(θ_f > θ_known) ≥ q` and not `unknown`.
   - **"Start here":** unknown, or neither threshold met.
   - **"Looks shaky — may depend on [prerequisite]":** `P(θ_f < θ_gap) ≥ q`.
   - The defaults are `θ_known = logit(0.75)`, `θ_gap = logit(0.35)` and `q = 0.8` (D6).
5. **Override:** "Actually, I don't know this" moves a facet to **Start here**. It's a routing preference, never evidence. It appends to `judgment_ledger` (task `placement_override`, judge `owner`; Slice 2 §5.8), so overrides count against the field's "likely known" in report 3.

**Effect (S5, live; algorithm successor; kill switch `placement.enabled`).** *Revised 2026-10-11: no shadow stage, and not gated on Q7/Q11.*
- **The placement block replaces today's per-topic initial probes** for LOs in its scope. LOs outside it keep `_enter_initial_probes` behaviour.
- **"Likely known" LOs** (all in-scope facets likely known):
  - no initial episode is opened now;
  - one **confirm episode** is entered after `placement.confirm_after_days` (default 10), and its first presentation is a normal cold check;
  - until then, their items are served only through the existing goal-frontier path, unchanged.

  This uses only the scheduler's existing cold-start gate (items of unattempted LOs are served via a goal frontier or an open episode). When the daily loop adds a single intent control (Q7) and a new-material policy (Q11), "likely known" maps onto maintain-level intent instead.
- **"Looks shaky" LOs** get their initial episode as today, entered first.
- **"Start here" LOs** get their initial episode as today.
- **Nothing is certified.** A failed confirm probe simply restores the normal path.
- **Thin data.** If report 2 couldn't run on your data, `q` starts at the value report 6 (public benchmark) suggests for a miss rate of ~10%, or at 0.9 if that isn't available, until report 3 has a miss rate.
- **Receipts.** `placement_decisions` records the conclusions and the episodes that were *not* entered. Report 3 scores them against the confirm probes.

### 6.3 (2) Choosing where to probe next

**Score, per LO:**

```
s(LO) = max over facets f in LO of  g_f · Σ_ff / σ₀² · 1 / (1 + n_served_f / n₀)
```

- `n_served_f` is the number of distinct surface groups served that cover f, so rarely-served regions score higher (Plan B's exposure-density amendment).
- `n₀` defaults to 3.
- `unknown` facets score at prior variance. Exploring them is the point, but only for facets with `g_f > 0`.

**Live (S7; algorithm successor; kill switch `field.probe_targeting_enabled`).** *Revised 2026-10-11: no shadow stage, not gated on Q9.*
- **(a) Stale-uncertainty re-probes.** `enter_stale_uncertainty_reprobes` keeps its trigger shape but enters the field's set: LOs with `s(LO)` ≥ `field.reprobe_score` whose last episode is terminal and older than `reprobe_stale_uncertainty_days`. The old variance-threshold set is computed and logged beside it.
- **(b) The queue's probe term.** The per-LO information-gain input to `probe_eig_weight` is replaced by the field's expected variance reduction per candidate item (`field_eig`), with fixed weights as today. The old component stays in the explanation components for comparison.
- **What Q9 changes.** Until a finite, system-ordered plan exists, learner-picked observations have unknown propensity. Report 4 is then model-based, not off-policy (F7). This weakens the evaluation, not the change.

---

## 7. Persistence

All new tables take the next free migration numbers at build time, following the `CLAUDE.md` head-fixture procedure.

| Table | Role (`db/table_roles.py`) | Contents |
|---|---|---|
| `embedding_vectors` | WORKFLOW (Slice 1 §9.2; created here if Slice 1 hasn't) | Vectors for `facet/definition`, `learning_object/summary` |
| `facet_outcome_observations` | DERIVED (rebuild owner) | §4.2 |
| `learner_field_graph` | DERIVED (rebuild owner) | Edges (`facet_a`, `facet_b`, `weight`, `sources_json` listing authored types and embedding cosine), `kernel_version`, `embedding_model_id`, `vectors_missing_count` |
| `learner_field_snapshot` | DERIVED (rebuild owner) | Per facet: §5.5 outputs + `as_of_observation_id`, `field_version`, `kernel_version`. Latest snapshot only; history is reproducible by replay |
| `placement_decisions` | RECEIPT | `id`, `trigger_ref` (import batch or study-map apply), `scope_facet_ids_json`, `candidate_items_json`, `chosen_json` (item, gain, minutes), `conclusions_json` (per facet: group, `p_available`, interval), `episodes_skipped_json`, `confirm_due_json`, `q_used`, `field_version`, `created_at`; later joined to confirm-probe outcomes by report 3 |
| `field_probe_target_receipts` | RECEIPT | `sync_id`, `lo_id`, `score`, `entered`, `variance_rule_would_enter`, `field_version`, `created_at` |

- **Config:**
  - `[field]`: `enabled` (template default false; owner vault true); kernel and threshold values from §5–6; `kernel_version`; `probe_targeting_enabled`; `legacy_fallback` (`exclude` \| `current_content`, default `exclude`).
  - `[placement]`: `enabled`, `k`, `min_new_facets`, `g_outside`, `confirm_after_days`, thresholds.
- **Algorithm versions:**
  - S1–S3 add only DERIVED and RECEIPT tables and a display layer, and change nothing that is served: no successor.
  - S5 (placement live) and S7 (probe targeting live) are separate successors (D11). Each comes with the playbook's upgrade function, a shadow rebuild on a backup-API copy, a head fixture, and a kill switch that restores the previous behaviour exactly.

---

## 8. Evaluation

### 8.1 Correctness gates (pass/fail)

| Id | Gate |
|---|---|
| G1 | **Deterministic rebuild:** the same ledgers, vault, vectors, and config give a byte-identical `learner_field_graph` and `learner_field_snapshot` (hash compared on fixture vaults) |
| G2 | **Zero LLM and embedding calls** during rebuild or replay (fakes assert). Missing vectors → authored-only graph, recorded |
| G3 | **No evidence writes:** an import-linter contract forbids the field package from importing evidence/projection writers. A test asserts that evidence, mastery, facet-recall, and certification tables are byte-identical with the field on vs off |
| G4 | **Density guard:** a disconnected facet, and a facet more than `max_support_hops` from any evidence, report `unknown` with variance = prior variance |
| G5 | **Shortcuts widen:** on small graphs, the kNN-sparsified, capped, and jittered posterior variance is ≥ the exact dense posterior variance for every facet |
| G6 | **Never blend:** the map DTO keeps `field.*` separate. Vitest asserts that well depth and beads are identical with the layer on vs off |
| G7 | **No certification:** placement-live never marks any facet demonstrated or cold-verified; "likely known" changes only episode entry and intent |
| G8 | **Reproducibility:** placement selection given a snapshot is deterministic (ties broken by item id), and `placement_decisions` records everything needed to recompute it |
| G9 | **Model change:** the graph rebuild after an embedding-model change waits for a full re-embed of the affected record kinds (Slice 1 §9.6) |
| G10 | **Weight invariances:**<br>• adding quarantined, unassessable, or `excluded` rows leaves the posterior byte-identical;<br>• splitting one facet's share across two duplicate facets leaves the attempt's total information unchanged;<br>• at F = 1, primed handling matches `mastery.py` |
| G11 | **No silent substitution:** every `facet_outcome_observations` row has a `revision_status`; with `legacy_fallback = "exclude"` no row uses current content for a missing revision. The row count matches the debug-payload copy for `exact` rows (validation) |
| G12 | **Kill switches:** with `placement.enabled = false` or `field.probe_targeting_enabled = false`, episode entry and queue ranking are identical to the previous algorithm version on fixture copies |
| G13 | **No leakage in evaluation:** the harness gives each arm a row's outcome only after that arm has predicted it; arms have no store access; the `llm_probability` arm is unreachable from serving code |

### 8.2 Quality reports (no thresholds; noise floors via bootstrap over attempts)

All reports run on the shared harness (§8.3). None is a one-off script.

**Data prerequisite.** These reports need a few hundred graded attempts spread over many facets (the count query from 2026-10-11). At n=1 they detect only large effects. Intervals are reported, and "can't tell" is a valid outcome.

1. **Prequential replay, S2.**
   - **Setup:** for every graded attempt in time order, each facet outcome is predicted from state built strictly before it.
   - **Compared against the no-smoothing baseline:** per-facet Beta mean (`facet_recall_state`), per-LO mastery EKF, and FSRS retention.
   - **Metrics:** log loss, Brier, and a reliability diagram.
   - **Splits:** facets **with** vs **without** prior direct evidence (the field's value should show in the latter), and observation `serving_origin` (F7).
   - **Sensitivity sweep:** `t` ×{0.5, 1, 2}, `k` ∈ {4, 8, 16}, `c₀` ∈ {0.25, 0.35, 0.45}, and `w_*` ±50%. If the conclusion flips inside the sweep, that is a reason not to promote.
2. **Placement simulation, S2.**
   - **Setup:** for each topic you started with ≥ 6 graded attempts, keep the first k chosen by §6.2's rule from what was actually answered, and predict the first attempt on each other in-scope facet.
   - **Compared against:** prior only, and the baseline.
   - **Reported:** the share of facets that would be "likely known", and the **miss rate** among them (failed when attempted). The miss rate is the safety number.
3. **Confirm-probe scoring, S5** (revised 2026-10-11: live, not shadow).
   - **Miss rate** of "likely known" against its confirm probes. This is the safety number.
   - **"Looks shaky" hit rate** against the initial episodes that ran.
   - **Placement minutes** vs the estimated minutes of probing every topic.
4. **Probe targeting, S7.**
   - **Decision-change rate:** the share of syncs where the field's set differs from the logged variance-rule set.
   - **Realized information** (posterior change) per probe, for the field's probes vs the rule's choices where both ran.
   - **Rank agreement** of `field_eig` with the old information-gain component.
5. **Map layer, S3.** Calibration of `p_available` on `inferred` facets when they are later measured directly. Plus your qualitative note: is the fog legible, and does it help?

**Decision rules (directional, owner-reviewed; revised 2026-10-11).** The consumers ship live after the S2 checkpoint, and the reports decide tuning or reversal:
- **Map layer.** If (1) shows the field *worse* than the baseline on facets without direct evidence, fix the field before relying on the fog.
- **Placement.** If (3)'s miss rate is higher than you accept, raise `q` or `θ_known`. If it stays high, set `placement.enabled = false`.
- **Probe targeting.** If (4) shows the field's probes carry less realized information than the rule's, set `field.probe_targeting_enabled = false`.

### 8.3 Shared evaluation harness: `learnloop eval` (added 2026-10-11)

The harness is how the pivot gets tested. Every predictor, hand-built or learned, is a **registered arm** scored on the same rows with the same rules. A future learned feature is "register an arm, run the report", never a new script.

- **Predictor contract.** `observe(row)` and `predict(row) -> p ∈ (0, 1)`, plus `name`, `version_hash` and `granularity` (`facet` or `attempt`).
  - The harness walks `facet_outcome_observations` in a fixed time order (`observed_at`, `attempt_id`, `facet_id`). For each attempt it asks every arm to predict **before** showing it the outcome.
  - An arm has no other read access to the store, so leakage is impossible by construction.
  - Attempt-level arms are scored against the attempt's rubric fraction. Facet arms are aggregated to attempt level by `facet_share`, so all arms meet on one scale. Facet arms are also scored per facet.
- **Metrics.**
  - Log loss and Brier (fractional targets allowed), a reliability diagram, and AUC at attempt level.
  - Splits by direct-evidence status, `serving_origin`, revision status, and topic.
  - Bootstrap intervals clustered by attempt.
  - A version manifest: arm hashes, algorithm, kernel, embedding model, config hash, data snapshot.
- **Arms at launch:**

  | Arm | What it is |
  |---|---|
  | `base_rate_lo` | Per-topic running success rate |
  | `facet_beta` | `facet_recall_state` |
  | `mastery_ekf` | Per-LO mastery |
  | `fsrs_retrievability` | Item-level, attempt granularity |
  | `field` | The default kernel plus the §8.2 sensitivity variants |
  | `family_memory` (per item / per family / per LO) | Added by PF-a for the idea-identity replay |

- **Optional arm: `llm_probability`.**
  - **What it does:** a frontier model reads the last 25 graded attempts (item excerpt, outcome, timestamp, gap) and the next item, and returns P(correct). It's a config route (`ai.routing.eval_llm_probability`).
  - **Calibration:** a one-parameter temperature fitted prequentially, on past predictions only.
  - **Cost control:** it runs under Slice A's spend caps. Predictions are cached outside the vault, in `fixtures-local/eval-cache.sqlite`, keyed by input hash, model and prompt version, so reruns don't re-pay.
  - **Status:** it never feeds serving. It is the test of "frontier model as sensor" against the hand-built arms (sweep: 2610.11135). A local decision model such as Kev can be added later as one more arm with the same contract.
- **Outputs.** JSON plus markdown, aggregates only and never learner text. Written to a path the owner chooses (default `fixtures-local/reports/`).

### 8.4 Public-data benchmark: time-to-useful-vault (report 6, added 2026-10-11)

Your vault alone may be too small to separate the arms. The benchmark replays **each learner of a public dataset as an independent n=1 vault**, which gives the statistical power your own history can't.

- **Dataset.** One with native item text, a concept or KC hierarchy, and a licence that permits research use. Candidates are listed in `docs/brainstorming/Datasets.md` (for example Eedi NeurIPS 2020 with its subject tree). The Phase 2b agent verifies text availability, structure and licence, recommends one, and stops for the owner (D12).
  - Data lives under gitignored `fixtures-local/benchmarks/<dataset>/` and is never committed.
  - The source, version and licence are recorded in every manifest.
- **Adapter.** Converts the dataset into the harness's row shape, outside any vault:
  - items carry their text;
  - each KC becomes a facet, with an LLM-written definition embedded like `facet/definition`;
  - the hierarchy becomes `part_of` edges;
  - responses become cold, binary rows with `serving_origin = unknown`.

  KC definitions are paid outputs, generated once per dataset version and model under the spend caps, then persisted in the benchmark directory.
- **Report 6.**
  - **(a) Per-learner prequential replay** of every arm. Shown as the distribution across learners (median, interquartile range, share of learners where the field beats each baseline), not only as pooled means.
  - **(b) Time-to-useful-vault** (Plan §D's `K_useful`). For K ∈ {0, 1, 4, 16} placement answers, chosen by §6.2's rule from what each learner actually answered, it reports the log loss on that learner's remaining items and the "likely known" miss rate. `K_useful(ε)` is the smallest K within ε of that learner's mature-history loss, reported at ε ∈ {0.01, 0.02, 0.05} nats.
- **Caveats, stated in the report.**
  - The benchmark validates the machinery, not your effect sizes. School-platform data doesn't transfer to your content (Plan §D transfer gate).
  - Choosing placement items from what a learner happened to answer is a selection bias the report names.
  - The miss-rate curve is used only to set placement's starting `q` (§6.2).

---

## 9. Rollout

| Step | Contents | Needs | Gate to proceed |
|---|---|---|---|
*Revised 2026-10-11: S4 and S6 dropped (owner: no shadow periods). Built as Slice A (`spec_slice_a_practice_and_field_v1.md`).*

| Step | Contents | Needs | Gate to proceed |
|---|---|---|---|
| **S0a** Daily-loop prerequisites | Owner answers to Q5/Q7/Q9/Q11; dormant/resolved serving fix (daily-loop spec, not this one) | — | Refines S5 and S7 when available; blocks nothing |
| **S0b** Embedding substrate | §4.1: client, `embedding_vectors`, backfill of `facet/definition` and `learning_object/summary` (Slice A Phase 1) | — | Client tests; backfill idempotent on a `fixtures-local/` copy |
| **S1** Outcome view | `facet_outcome_observations` with revision status and serving-origin join (§4.2) | — | G1–G3, G11 on the view; spot-check vs mastery traces |
| **S2** Field + replay report | Graph, prior, EKF, snapshot (§5); the shared harness `learnloop eval` with its launch arms and the optional `llm_probability` arm (§8.3); `learnloop field rebuild` / `data-check`; reports 1–2 | S1 (S0b optional; authored-only fallback) | G1–G5, G10, G13; owner reviews the replay report once |
| **S2b** Public-data benchmark | Dataset recommendation → owner pick (D12); adapter; KC definitions; report 6 (§8.4) | S2 harness | Report 6 reviewed with or after S2's; finishes before S5 when possible, without blocking it |
| **S3** Map layer | §6.1, on by default | S2 checkpoint | G6; report 5 after use |
| ~~S4~~ | Dropped; merged into S5 | — | — |
| **S5** Placement live | Algorithm successor + kill switch; trigger, selection, results, episode effects (§6.2) | S2 checkpoint; item supply (exercises; PF-b published items) | G7, G8, G12; report 3 after several imports |
| ~~S6~~ | Dropped; merged into S7 | — | — |
| **S7** Probe targeting live | Algorithm successor + kill switch (§6.3) | S2 checkpoint | G12; report 4 |

---

## 10. Tests

- `test_facet_outcome_view.py`:
  - one row per (attempt, facet) for the latest grading epoch;
  - `facet_share` sums to 1 per attempt;
  - `dont_know` → 0;
  - quarantined → mass 0;
  - canonical facet resolution through `facet_merges`;
  - serving-origin join for list picks, probe presentations, forced follow-ups, and pre-161 attempts;
  - `revision_status`: `exact` via snapshot hash, `excluded` by default when the graded revision is missing, `reconstructed_current` only under the fallback flag (G11);
  - agreement with the debug-payload copy for `exact` rows;
  - rebuild determinism.
- `test_learner_field_graph.py`:
  - authored edges lifted correctly per type and strength;
  - `w_conf = 0`;
  - symmetric kNN over mean-centered vectors;
  - LO-summary fallback for legacy facets;
  - authored-only fallback with no vectors;
  - `kernel_version` hash changes on config change.
- `test_learner_field_inference.py`:
  - a single observation moves neighbours in proportion to prior covariance;
  - a disconnected component is untouched;
  - drift widens variance up to `p_max`;
  - uncertain `b` widens R;
  - equivalence to `mastery.py`'s EKF when F = 1, including primed handling;
  - G10: zero-mass rows leave the posterior byte-identical, and facet-splitting invariance;
  - G4 and G5;
  - float64 determinism.
- `test_placement_selection.py`:
  - greedy gain matches brute force on small instances;
  - conditioning reduces later gains;
  - eligibility excludes reserved and reveal-burned surfaces;
  - G8;
  - the results grouping uses thresholds exactly;
  - an override moves a facet to "start here" and writes no evidence;
  - live effects: no initial episode for likely-known LOs; a confirm episode is entered after `confirm_after_days`; a failed confirm restores the normal path; `q_used` = 0.9 when report 2 had too little data; with no eligible items, today's initial probes run;
  - G12: with `placement.enabled = false`, behaviour is identical to the previous version.
- `test_field_probe_targets.py`:
  - under the successor, the field's set is entered and the variance-rule set is logged beside it;
  - `field_eig` replaces the per-LO information-gain input;
  - G12: the kill switch restores the old ranking exactly.
- `test_field_no_evidence_writes.py` (G3), and an import-linter contract entry.
- `test_eval_harness.py`:
  - **G13:** no arm can read a row's outcome before predicting it, and arms have no store access;
  - deterministic ordering and manifests;
  - bootstrap clustered by attempt;
  - facet→attempt aggregation by `facet_share`;
  - registry version hashes change with config.
- `test_llm_probability_arm.py`:
  - fake client;
  - spend caps checked before requests;
  - temperature fitted only on past predictions;
  - cache hits re-pay nothing;
  - never imported by serving code (import-linter).
- `test_benchmark_adapter.py`:
  - a tiny synthetic dataset, so tests make no network calls;
  - KC→facet and hierarchy→edge mapping;
  - persisted KC definitions are reused;
  - the licence and source are recorded in the manifest;
  - nothing is written under `fixtures/`.
- Sidecar RPC tests for the `field` block in `get_knowledge_map`. Vitest for G6, and for the fog/`?` rendering.
- **Durability lane:** the rebuild under production pragmas on a fresh vault.

---

## 11. Open decisions

| # | Decision | Recommendation |
|---|---|---|
| D1 | Region granularity: facet only, or facet × capability now? | Facet only in v1. Capability-sliced regions multiply F and thin the evidence; add them once the replay report shows facet-level value |
| D2 | Kernel and inference: heat kernel + sequential EKF, or graph Matérn / batch Laplace? | Heat kernel + EKF. One interpretable bandwidth, and it matches `mastery.py`, so F = 1 reduces to today's model. Matérn or Laplace only if the sweep shows heat-kernel conclusions are fragile |
| D3 | Edge types and weights, especially `confusable_with` | `w_conf = 0`. Confusable facets share surface, not ability, and treating them as correlated would hide exactly the confusion you want detected |
| D4 | Where placement items come from | Imported exercises, then PF-b's published verified items. With none, today's initial probes run (revised 2026-10-11: not blocked on Q5) |
| D5 | Placement block size and reveal | k = 4 (≤ ~8 min); reveal answers at block end with `reveal_events`, except reserved surfaces |
| D6 | "Likely known" thresholds and confirm delay | `q = 0.8`, or 0.9 when report 2 lacked data; `θ_known = logit(0.75)`; confirm after 10 days as a normal cold check. Tune from report 3's miss rate |
| D7 | Learner-picked observations (unknown propensity) | Include them in the field, which is model-based. Exclude them from any off-policy claim and report both splits. A Q9 finite plan resolves this |
| D8 | Should the field ever replace per-LO mastery? | No, not in v1. It runs in parallel, and per-LO mastery stays authoritative for everything it feeds today |
| D9 | ~~Show placement results during shadow?~~ | **Obsolete (2026-10-11):** there is no shadow stage, and results are shown |
| D10 | Learner claims as prior mean | Yes, weak, via the existing claim machinery. Never an observation |
| D11 | One algorithm successor for S5 + S7, or separate? | Separate. They're separate consumers with separate kill switches and reports |
| D12 | Which public dataset for report 6? | The Phase 2b agent verifies native item text, KC hierarchy and licence across `Datasets.md` candidates and recommends one. Prefer native text over image-only items, to avoid transcription spend |
| D13 | Run the `llm_probability` arm by default? | Yes, under a spend cap (default $5 per run), cached. It's the cleanest test of frontier-model-as-sensor vs hand-built predictors |
| D14 | `K_useful` tolerance | Report ε ∈ {0.01, 0.02, 0.05} nats; don't pick one until the curves exist |

---

*Related: [[Pipeline Augmentation Plan]] (workstream B) · `spec_blind_grading_diagnosis_split_v1.md` §9 · `spec_embedding_consumers_v1.md` §5 · `learner/mastery.py` · `docs/algorithm-change-playbook.md` · [[Bitter Lesson Research Sweep]]*

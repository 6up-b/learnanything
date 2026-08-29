# LearnLoop MVP Spec Delta — v0.3: Facet-Grained Diagnosis

This file is a narrow delta on `spec_mvp.md` / `spec.md`. It does **not** restate
the pipeline; it changes one thing and follows the consequences: the diagnostic
follow-up objective moves from *"raise the Learning Object's mastery scalar"* to
*"resolve uncertainty about the specific failed facet/claim."*

It is deliberately a Stage-0/Stage-1 move in the sense of `architecture_pivot.md`:
it does not add a learned model class. It restructures the diagnostic target so the
existing EIG plumbing becomes *efficacious* (it currently is not wired into the
follow-up path at all) and so the decision is logged at a grain that
`learning_outcome_labels` can later be regressed against per facet.

Status: implemented in current worktree. Written 2026-05-28; revised 2026-05-28 — corrected the
§1B.2 coverage formula (1/N normalization bug), serialized the facet `hypothesis_marginal`
(§1.4), pinned `learner_confidence` to raw `grading_evidence` (§1.3), made the §2.4 gate
enforce `min_target_facet_overlap` (not just non-empty overlap), reconciled multi-facet
generation (§3.2 / §6), and added a phased rollout (§7). Revised 2026-05-29 — four
consistency fixes against the live code: (1) §1B coverage is wired into the
`observation_weight_override` the live path actually consumes (the `effective_coverage`
argument to `resolve_error_impact`), not the short-circuited `evidence_coverage` term;
(2) added the §1B.2 open-facet restriction so a disjoint attempt is *literally* ≈0, not
merely attenuated under `kappa_uncertain`; (3) the §2.4 eligibility gate keys on a
primary `dominant_target_facet` plus target precision, not Jaccard against the full
failed set (Jaccard 1/N would reject a clean single-facet probe for N ≥ 3); (4) facet
EIG is an importance-weighted sum of
independent per-facet marginals over the grader's per-facet `facet_outcomes`, not one
joint set over the global score bucket. Revised 2026-05-29 (round 2) — removed the
dominant-facet gate circularity (derive `dominant_target_facet` before selection),
replaced attempt-time `covered_facets(item)` with a static
`candidate_facet_support(item)` for selection-time gating/EIG, added `tau_facet_share` /
`min_facet_evidence_mass` so incidental annotation can't count as covered, and called for
a dedicated `facet_expected_information_gain` rather than reusing the global-outcome EIG.
Revised 2026-05-29 (round 3) — added the known-gap honest-UI distinction (§1B.7) and
follow-up candidate-slate logging (§2.6). Revised 2026-05-29 (round 4) — split the
follow-up gate's single `dominant_target_facet` from the generated need's assessed
`target_facets`, and added rationale-driven target enrichment from structured grader
repair-suggestion facets (§2.7 / §3.2). Revised 2026-05-29 (round 5) — reconciled §2.4
against the landed code: the live gate's `_jaccard(candidate_facet_support, {dominant_target_facet})`
is *algebraically* the precision gate evaluated on a singleton reference set, not a rival
metric, so the fix is to feed it a richer reference set, not to change the metric; pinned
the explicit `diagnostic_gate_facets → failed set → {dominant_target_facet}` fallback
chain; retired Jaccard from the gate (its symmetry leaks *recall* into a test that should
be pure precision, which is the real cause of the `1/N` rejection the round-3 note blamed
on "the full failed set"); showed the failed set is a *safe* interim reference under
precision (so §7 Phase 1 need not fall back to the bare singleton); and made the
gate/cap coupling explicit (§2.4 / §2.7). Implemented in the current worktree:
Workstreams 1 / 1B / 2 core landed in `a02b11e` (`facet_uncertainty`,
`facet_expected_information_gain`, `candidate_facet_support`, EIG-ranked
`_choose_intervention_item` + slate logging, known-gap detection, the
`learner_confidence` field), and the remaining §2.4 / §2.7 pieces now land on top:
the enriched-reference `target_precision` gate, structured
`RepairSuggestion.target_evidence_families`, frozen `diagnostic_focus_json`, and the
need-time target/focus scorer.

---

## 0. Motivating failure (the case this spec fixes)

Observed on `lo_spectral_theorem_symmetric_matrices`
(`fixtures/linear_algebra/subjects/symmetric-matrices-and-variance`):

1. Attempt on `pi_symmetric_distinct_eigenvectors_orthogonal` (a proof item,
   difficulty 0.64) scored **1/5**. The learner's prose said, verbatim, *"I'm not
   sure why if the eigenvalues are different and if the matrix is symmetric it
   means the corresponding eigenvectors are orthogonal."* — i.e. explicit
   uncertainty about facets `symmetric_dot_identity` and `distinct_eigenvalue_logic`.
2. The intervention follow-up fired `pi_apply_spectral_theorem` (a classify item,
   difficulty 0.38). Its facets — `symmetry_check`, `spectral_theorem_application`,
   `orthogonal_diagonalizability_conclusion` — have **zero overlap** with the failed
   facets.
3. The learner scored **3/3**, and the LO mastery posterior went **up**.

Three root causes, each addressed by a workstream below:

- **A. The follow-up selector is not information-aware.** The live path is
  `evaluate_attempt_intervention_followup` → `evaluate_intervention_followup` →
  `_choose_intervention_item` (`services/followups.py:438`), which ranks by Jaccard
  facet overlap + a scaffold bonus. The EIG machinery in `services/probes.py`
  (`expected_information_gain`, `conditional_distribution`, `probe_eig_component`)
  is wired only into the main scheduler (`services/scheduler.py:115`) and into the
  **dead** `_choose_followup_item` (`services/followups.py:290`, never called).
  → **Workstream 2.**
- **B. No selection-time overlap gate, and thin-pool generation never triggers.**
  `_choose_intervention_item` picks the single remaining LO item even at overlap 0.
  The `min_target_facet_overlap: 0.5` requirement (`services/followups.py:148`) is
  only stamped onto an intervention *need*, and a need is only created when the
  selector returns `None` — which never happens while ≥1 other item exists. So
  `build_diagnostic_practice_plan` (`services/practice_generation.py:188`), which
  already knows how to generate a facet-targeted probe, is never reached.
  → **Workstream 3.**
- **C. The diagnostic target is the LO, not the facet.** Mastery is one scalar
  latent per LO (`MasteryState.logit_mean`, `services/mastery.py:349`); the probe
  hypothesis set is LO-grained (`build_hypothesis_set`, `services/probes.py:78`).
  So a correct answer on *any* facet lifts the shared latent, and uncertainty about
  one facet is invisible. → **Workstream 1** (diagnosis) and **Workstream 1B** (the
  mastery rise itself).

---

## 1. Workstream 1 — Facets as first-class diagnostic units

### 1.1 What already exists (do not rebuild)

Per-facet belief state is already tracked: `FacetRecallState`
(`db/repositories.py:107`) holds `recall_mean`, `recall_variance`,
`independent_evidence_mass`, `consecutive_failures` keyed by
`(learning_object_id, facet_id, practice_item_id|NULL)`. `resolve_coverage`
(`services/recall_coverage.py:71`) emits `covered_facets` and `facet_outcomes`.
The diagnostic target dataclass already carries `facet_recall_mean_by_facet` and
`facet_recall_variance_by_facet` (`services/practice_generation.py:86`).

The gap is not storage. It is that **diagnosis and intervention decisions read the
LO scalar, not the facet vector.**

### 1.2 Target

Introduce the **facet/claim** as the unit a diagnostic is *about*. v0.3 does not
replace the LO mastery scalar (that is a later pivot stage); it adds a facet-grained
*diagnostic belief* that the follow-up policy reads, and that gates whether an LO
mastery rise is allowed to "count" against an open uncertainty.

Concretely:

- **Failed-facet set** for an attempt = facets with `facet_outcomes[f] < tau_facet_failed`
  (reuse the 0.40 threshold already in `_target_facets_from_debug`,
  `services/followups.py:350`), unioned with facets whose `recall_mean` has high
  `recall_variance` (uncertain, not just wrong).
- **Open facet uncertainty** is a first-class record (see §1.4). Until it is
  resolved, a high score on an item that does **not** cover the failed facet must
  **not** clear it. This is the direct fix for the motivating case: the 3/3 on
  `pi_apply_spectral_theorem` does not touch `symmetric_dot_identity`, so the open
  uncertainty on that facet survives and keeps driving follow-up.

### 1.3 Facet uncertainty signal includes metacognitive hedging

The learner's *"I'm not sure why…"* is the highest-value diagnostic signal in the
motivating case and is currently discarded. v0.3 adds a **hedge signal** to the
grading output:

- The grader (Codex structured grading, `spec.md` §grading) emits, per facet it
  can attribute, a `learner_confidence` ∈ {`confident`, `hedged`, `absent`} derived
  from the answer text ("I'm not sure", "I think", "I guessed", asserting a claim
  while disclaiming the justification). Concretely this is a **new field on
  `CriterionEvidence`** (`codex/schemas.py:190`) — criteria already map to facets via
  `criterion_facet_weights`, so per-criterion is the natural grain and it threads into
  `derive_facet_outcomes`.
- A `hedged`/`absent` confidence on a facet **raises that facet's diagnostic
  uncertainty even when the rubric awarded partial credit.** This is the mechanism
  that prevents "right answer, wrong reason" from being scored as mastery.

This must be stored as **raw grader evidence, not a derived debug payload.** Replay
rebuilds `facet_uncertainty` from `practice_attempts` + `grading_evidence`
(`migrations/001_initial.sql:154`); `attempt_debug_payloads` (migration 007) is
*derived* and therefore replay-invisible. So add a `learner_confidence` column to
`grading_evidence` (alongside `points_awarded` / `evidence`). Only with the raw column
is the signal additive to the grading contract *and* replay-safe under
`algorithm_version` — without it the §1.4 belief is not rebuildable and the §1.4
invariant is violated.

### 1.4 Data model

New table (migration `012_facet_diagnostic_state.sql`), additive:

```sql
CREATE TABLE facet_uncertainty (
  id                   TEXT PRIMARY KEY,
  learning_object_id   TEXT NOT NULL,
  facet_id             TEXT NOT NULL,
  -- diagnostic belief, distinct from FacetRecallState recall belief:
  hypothesis_marginal  TEXT NOT NULL,      -- serialized P(h) over {facet_solid, facet_absent, misconception:E...}; the belief object
  uncertainty          REAL NOT NULL,      -- DERIVED cache: H(hypothesis_marginal), nats (for ranking / UI)
  status               TEXT NOT NULL,      -- 'open' | 'resolving' | 'resolved'
  opened_by_attempt_id TEXT NOT NULL,
  opened_reason        TEXT NOT NULL,      -- 'low_facet_outcome'|'hedged_confidence'|'repeated_facet_failure'
  last_evidence_at     TEXT,
  algorithm_version    TEXT NOT NULL,
  created_at           TEXT NOT NULL,
  updated_at           TEXT NOT NULL,
  UNIQUE (learning_object_id, facet_id)
);
```

**Store the marginal, not just its entropy.** Workstream 2 computes facet EIG from
`P(h)` over the facet hypothesis set and logs a *realized uncertainty drop* in
`decision_features` (§2.5); both are undefined if only the scalar `H` is persisted —
you cannot recover a ≥3-category distribution from one entropy number, so the selector
would have to invent a prior at runtime, exactly the hidden, unlogged constant the
pivot wants gone. So `hypothesis_marginal` is the first-class belief and `uncertainty`
is a denormalized `H()` cache. The **update rule operates on the marginal**: a graded
attempt that probes `f` produces a posterior over `{facet_solid:f, facet_absent:f,
misconception:E...}` under the §2.2 conditional model, and `status`/`uncertainty` are
recomputed from it. This also closes the open→resolving→resolved *dynamics* and gives
`last_evidence_at` a place to drive staleness/decay — all left undefined by a
bare-entropy record.

Like every other derived belief, this is **rebuildable from raw attempts** (it must
appear in `derived_state_rebuilds`, migration 009) so replay determinism holds: the
spec invariant *"store raw attempts forever so the models are replaceable"* applies.

### 1.5 Config (additions to `RecallCoverageConfig` / new `FacetDiagnosticConfig`)

```python
tau_facet_failed: float = 0.40          # facet_outcome below this opens uncertainty
tau_facet_uncertain_variance: float = 0.15  # recall_variance above this also opens it
hedge_uncertainty_floor: float = 0.50   # min facet uncertainty when grader reports `hedged`
facet_resolved_threshold: float = 0.10  # uncertainty below this -> status 'resolved'
```

---

## Workstream 1B — Coverage-weighted mastery observation (the rise itself)

Workstream 1 stops *diagnosis* from being fooled, but on its own it leaves the LO
mastery **scalar** wrong: the motivating 3/3 still raises `MasteryState.logit_mean`
and, worse, shrinks `logit_variance` over a facet that was never tested. Everything
that reads mastery (scheduling priority, forgetting risk, goal reachability, the
"Why now?" surface) is then misled. This workstream fixes the *rise itself* —
**without splitting the LO latent** (see §1B.5 for why).

### 1B.1 The knob already exists; it is just measured against the wrong facets

The EKF already attenuates partial evidence: `observation_weight`
(`services/mastery.py:192`) folds `evidence_coverage` into a reliability weight that
scales `measurement_noise` (`mastery.py:267`), which in turn scales **both** the
μ-step and the variance reduction (`variance_reduction = kalman_gain * sensitivity_h`,
`mastery.py:346`). The defect is the input. **On every live attempt the operative
weight is the override, not the `evidence_coverage` term:** `observation_weight`
returns `observation_weight_override` and short-circuits before the `evidence_coverage`
product (`mastery.py:198`, vs. the term at `mastery.py:202`), and `attempts.py:942`
always sets that override to `error_impact.observation_weight`. That override
(`resolve_error_impact`, `recall_coverage.py:258`) is itself built from
`effective_coverage` — the item's coverage of **its own** facets — which also feeds the
error-sharpening multiplier (`recall_coverage.py:265`). Either way the coverage scaling
the weight is item-self-coverage, so a 3/3 on `pi_apply_spectral_theorem` reads as
near-full coverage even though it exercises **none** of the LO's open facets. §1B.2
fixes *which* coverage; the wiring note there fixes *where* it is injected (the
override, not `evidence_coverage`).

### 1B.2 Target — LO-relative facet coverage

Replace the coverage term fed to the mastery observation with **coverage of the LO's
required facet space, with currently-uncertain facets up-weighted.** Define:

- `required_facets(LO)` = union of `evidence_facets` across the LO's active practice
  items (authored superset; a later explicit LO-level `required_facets` field may
  override).
- `facet_importance(f) = 1 + kappa_uncertain * open_uncertainty(f)`, where
  `open_uncertainty(f)` is the `facet_uncertainty.uncertainty` for `f` (0 if none is
  open). Open/uncertain facets therefore dominate the coverage measure.
- **Per-facet coverage scalar**, invariant to the item's facet count: for each
  required facet `f`,

  ```
  c_f = effective_item_coverage · 1[normalized_weight[f] ≥ tau_facet_share]
  ```

  (optionally quality-weighted by `facet_outcomes[f]` if mere presence is too coarse).
  **The indicator gates on the authored *share* `normalized_weight[f]`, not on the
  `coverage_epsilon` numerical floor.** `coverage_epsilon` (1e-3) exists only to keep
  `covered_facets` divide-safe; using it as the "covered" bar lets a facet authored at
  <1% weight earn *full* per-facet `c_f` credit, so incidental annotation would clear
  mastery confidence. The `tau_facet_share` floor (§1B.4) requires `f` to be a
  non-trivial part of the item before it counts. **Do not feed `resolve_coverage`'s
  `covered_facets[f]` straight in:** those are
  per-item *normalized shares* — `covered_facets[f] = effective_item_coverage ·
  normalized_weight[f]`, with `Σ_f covered_facets[f] = effective_coverage`
  (`recall_coverage.py:91`) — so they conflate "how much of the item is about `f`"
  with "was `f` demonstrated," and each share *shrinks* as the item gains unrelated
  facets. `c_f` is comparable across items regardless of facet count.

- LO-relative coverage of an attempt — an importance-weighted mean over the required
  facets, with **numerator and denominator in the same per-facet units**:

  ```
  lo_relative_coverage = Σ_{f ∈ required} facet_importance(f) · c_f
                         ──────────────────────────────────────────
                              Σ_{f ∈ required} facet_importance(f)
  ```

  Full breadth + full coverage → 1; an attempt covering zero required facets → 0;
  partial coverage interpolates. **Why the earlier draft was wrong (normalization
  bug):** it put the normalized shares `covered_facets[f]` (numerator total ≈
  `effective_coverage` ≈ 1) over an unnormalized `Σ facet_importance ≈ N`, so a
  *perfect* full-breadth attempt topped out at ≈ `effective_coverage / N`, not
  `effective_coverage`. That collapses the whole scale by 1/N and would crush
  `observation_weight` on **all** legitimate multi-facet evidence — the
  disjoint-vs-full ordering survives but the magnitude becomes meaningless (the
  estimator looks frozen). The count-invariant `c_f` above removes the mismatch.

**Open-facet restriction (the literal-≈0 guarantee).** The importance up-weight
`facet_importance(f)` changes the *denominator*, not the numerator, so it attenuates an
off-target attempt but does **not** zero it. Worked through on the motivating LO with
`kappa_uncertain = 2.0`: a 3/3 covering the item's three non-open facets contributes
numerator ≈ `3 · 1 · effective_coverage` and zero from the two open facets it misses,
over a denominator ≈ `3·1 + 2·(1 + 2u) ≈ 9` (open-facet uncertainty `u ≈ 1` nat) — so
`lo_relative_coverage ≈ 0.3`, not ≈0. A 0.3 weight still moves μ. To make "does not
count against open gaps" *literal*: **when ≥1 `facet_uncertainty` row is open for the
LO, restrict the required set in both numerator and denominator to the open facet set**
(equivalently, gate `lo_relative_coverage` by the open-facet coverage fraction). Then an
attempt covering none of the open facets has numerator 0 → `lo_relative_coverage = 0`
exactly, and only an attempt that touches an open facet earns weight. When no
uncertainty is open (a cold or settled LO), fall back to the full required set so the
attempt is weighted by ordinary breadth. This is what makes the §4 step-5 / §5 "≈0"
claims true rather than aspirational; without it they hold only approximately and depend
on `kappa_uncertain` being large.

**Wiring — inject at the override, not `evidence_coverage`.** The naive move (set
`MasteryObservation.evidence_coverage = lo_relative_coverage`) is a **no-op on the live
path**: `observation_weight` returns `observation_weight_override` and short-circuits
before the `evidence_coverage` product (`mastery.py:198`), and the override is always
set on live attempts (`attempts.py:942`). The override is computed by
`resolve_error_impact` as `before_sharpening = effective_coverage · observation_reliability`
(`recall_coverage.py:258`), with the *same* `effective_coverage` folded into error
sharpening (`recall_coverage.py:265`). **So the fix is to replace the
`effective_coverage` argument passed into `resolve_error_impact` (`attempts.py:919`)
with `lo_relative_coverage`** — that is the term the live weight actually consumes. Be
deliberate that this also makes **error-sharpening LO-relative** (an error on a facet
the attempt barely covered should sharpen less): that is intended, but it is a coupled
effect of the same substitution, not a separate knob — call it out so it is not silent.
A 3/3 covering zero open facets then has `lo_relative_coverage = 0` (open-facet
restriction above) → override weight ≈ 0 → **μ barely moves**, while a genuinely broad
attempt scores near 1 and moves μ normally. Both the EKF and legacy update paths consume
the override, so the single substitution covers both; `evidence_coverage` /
`MasteryObservation.effective_coverage` (`mastery.py:27`) remain only for the
override-free fallback (e.g. observations with no resolved error impact), where
`observation_weight`'s product form still reads them.

### 1B.3 Gate variance by coverage breadth (the important half)

The damage in the motivating case was less the μ rise than the **variance drop** —
the system became *confident* about the LO over an untested facet. §1B.2 already
throttles this (lower weight → higher `measurement_noise` → smaller
`variance_reduction`), and that is the primary intended effect. Make it structural as
well, so repeated easy hits on the same facet can't manufacture confidence:

- Track `covered_required_fraction(LO)` = (# required facets with
  `independent_evidence_mass > min_facet_evidence_mass`) / `|required_facets|`, where
  `min_facet_evidence_mass` (§1B.4) is a *meaningful* evidence bar, **not** the
  `coverage_epsilon` numerical floor — otherwise a single barely-touched attempt marks a
  facet "covered" and lets breadth (and thus the variance floor) be satisfied without
  real evidence, the same incidental-credit hole as the `c_f` indicator above. (Undefined
  when an LO has no required facets → treat as `1.0`, i.e. floor inert, so facet-less LOs
  are never penalized.)
- Floor the post-update variance: `logit_variance = max(logit_variance, variance_floor(c))`.

**Default curve (committed; to be fit later — see §1B.5):** linear, with the floor
going fully inert at complete breadth:

```
variance_floor(c) = variance_floor_at_full_coverage
                  + (variance_floor_at_zero_coverage − variance_floor_at_full_coverage) · (1 − c)
```

with `variance_floor_at_zero_coverage = 0.5` and `variance_floor_at_full_coverage = 0.0`.
Chosen against the existing scale (cold-start `logit_variance = 1.0`,
`variance_convergence_threshold = 0.10` is the "confident" line):

| `c` (covered fraction) | variance floor | confident (≤0.10)? |
|---|---|---|
| 0.00 | 0.500 | no |
| 0.50 | 0.250 | no |
| 0.75 | 0.125 | no |
| 0.80 | 0.100 | at the line |
| 1.00 | 0.000 | floor inert — normal convergence |

So an LO becomes *eligible* to cross the confident line only once ~80% of its required
facets carry independent evidence; at full breadth the floor imposes nothing and the
EKF converges as usual. Linear is deliberate: trivial to reason about and to swap for a
fitted curve once there is attempt data.

In words: *the LO does not get to be "sure" until the learner has actually been seen
doing the whole LO.* Re-hitting `symmetry_check` ten times cannot drive LO variance
down while `symmetric_dot_identity` remains unexamined.

### 1B.4 Config (additions)

```python
kappa_uncertain: float = 2.0                   # strength of the open-uncertainty up-weight in coverage
coverage_epsilon: float = 1e-3                 # numerical floor only (divide-safety); NOT the "covered" bar
tau_facet_share: float = 0.10                  # min authored normalized_weight for a facet to count in c_f (§1B.2)
min_facet_evidence_mass: float = 0.50          # meaningful independent_evidence_mass bar for the §1B.3 breadth count
variance_floor_at_zero_coverage: float = 0.5   # logit_variance floor at covered_required_fraction = 0
variance_floor_at_full_coverage: float = 0.0   # floor inert at full breadth; EKF converges normally
# variance_floor(c) interpolates linearly between the two as breadth c -> 1 (see §1B.3).
# Placeholder curve: refit against learning_outcome_labels once attempt data exists.
```

### 1B.5 Why this and not a per-facet latent

Deliberately **one scalar per LO**, coverage-weighted — not a vector of per-facet
EKFs — because:

- **Cold-start.** Splitting one starved latent into N facet latents divides the
  evidence per latent; variance stays wide and estimates get noisier, not truer.
  Pooling is the point.
- **Bitter Lesson.** `evidence_facets` are authored annotations — the row
  `architecture_pivot.md` §2 wants to *demote*. Used here as a soft observation
  *weight*, not as the belief primitive, so a wrong/incomplete facet taxonomy
  degrades gracefully instead of structurally.
- **Stage-2 compatibility.** `lo_relative_coverage` is exactly the kind of
  observation feature the eventual knowledge-tracing model (pivot Stage 2) would
  consume; nothing here is wasted when the learned estimator subsumes the EKF.

Where an LO's facets are *so* separable that mastery of one says nothing about the
others, the right fix is usually **splitting the LO in authoring**, not modeling
around coarse content. Coverage-weighting handles legitimate bundling; LO-splitting
handles mis-cut LOs. (Tracked as an open authoring question, not built in v0.3.)

### 1B.6 Replay / determinism

`required_facets`, `lo_relative_coverage`, and the variance floor are pure functions
of `(vault, facet_uncertainty, attempt)` — all rebuildable from raw attempts and
versioned under `algorithm_version`. No new replay invariants.

### 1B.7 Derived honest-UI view — "LO 0.8, facet X unexamined"

A read-model (no belief-state change) that, per LO, surfaces `mastery_mean` **next
to** the required facets that are either unexamined (no independent evidence) or carry
an open `facet_uncertainty`. The UI must never display a bare high mastery number
over an untested facet — it annotates it ("0.8 overall · `symmetric_dot_identity`
unexamined"). Source: `required_facets(LO)` minus covered, unioned with open
`facet_uncertainty` rows. This is the interpretability guard `architecture_pivot.md`
§5 demands ("don't let 'Why now?' die") and the human-readable counterpart to the
coverage gate above.

**Known-gap distinction.** The read-model must not collapse every non-solid facet into
"uncertain." It derives a per-facet display state from `required_facets`, independent
evidence mass, and the top hypothesis in `facet_uncertainty.hypothesis_marginal`:

- `unexamined`: required facet has not reached `min_facet_evidence_mass` and has no
  open diagnostic row.
- `uncertain`: `facet_uncertainty.status IN ('open', 'resolving')` or the resolved
  marginal is still diffuse.
- `known_gap`: `facet_uncertainty.status = 'resolved'` **and** the top hypothesis is
  `facet_absent:f` or `misconception:E`, i.e. diagnosis succeeded by finding the gap,
  not by clearing it.
- `solid`: resolved top hypothesis is `facet_solid:f` and breadth evidence is present.

Only `solid` removes the warning. `known_gap` stays visible next to the LO mastery
number and routes the learner to repair / guided reconstruction, while `uncertain`
routes to diagnostic probes. This prevents a resolved diagnosis from being mistaken for
a repaired learner state.

---

## 2. Workstream 2 — A facet-targeted diagnostic objective, wired to EIG

### 2.1 The reframe

Today the probe hypothesis set is *"is this LO mastered / unfamiliar / one of these
LO misconceptions?"* (`build_hypothesis_set`, `services/probes.py:78`). v0.3 adds a
**facet-scoped hypothesis set** built from the open `facet_uncertainty` rows for the
attempt's LO:

For each open facet `f`, hypotheses are at minimum:
`facet_solid:f`, `facet_absent:f`, and any `misconception:E` whose error type's
`related_concepts` (already used in `self_tag_weight`, `services/probes.py:268`)
attach to `f`. The objective is to **maximize expected information gain over the
facet hypothesis marginal**, not over the LO mastery latent.

**One marginal per facet; EIG sums over them — not one joint set.** The data model
stores one `hypothesis_marginal` per `(LO, facet)` row (§1.4), so the facet objective is
a set of *independent per-facet marginals*, **not** a single joint hypothesis set over
all open facets. Total facet EIG for a candidate item is the **importance-weighted sum
of the per-facet information gains**:

```
facet_probe_eig(item) = Σ_{f ∈ open} facet_importance(f) · EIG_f(item)
```

where `EIG_f` is the expected entropy drop of facet `f`'s marginal *alone* and
`facet_importance(f)` reuses §1B.2's open-uncertainty up-weight. Independent marginals
(rather than one joint set) is the same pooling-vs-splitting stance as §1B.5 and, with
the per-facet outcome space in §2.2, keeps a low score on a multi-facet item from being
read as evidence against *every* open facet at once: each facet updates only from
outcomes that actually probe it.

### 2.2 Make `conditional_distribution` facet-aware (the EIG efficacy fix)

The reason EIG would not have caught the motivating case even if it had been wired
in: `conditional_distribution` (`services/probes.py:384`) keys an item's
diagnosticity on whether the item's **fatal-error ids** match a hypothesis's
`error_type` (`probes.py:413`). It has no notion of *which facet an item exercises*.
So `pi_apply_spectral_theorem` looks diagnostic for the LO while exercising none of
the failed facets.

v0.3 generalizes the `probes_item` predicate:

> A candidate item probes hypothesis `h` about facet `f` iff
> `f ∈ candidate_facet_support(item)` **and**, for `misconception:E` hypotheses,
> additionally `E ∈ fatal_error_ids(item)`.

where `candidate_facet_support(item) = set(item.repair_targets or item.evidence_facets)`
is the **static** facet support available at *selection time*. This is deliberate:
`resolve_coverage`'s `covered_facets` is attempt-dependent — it needs answer text, hints,
and attempt type (`recall_coverage.py:71`) — so it is **not computable for an unattempted
candidate**, and the live selector only has static item metadata (`followups.py:457`
already ranks on `repair_targets or evidence_facets`). Reserve `covered_facets` /
`facet_outcomes` for the **graded attempt** that *updates* `facet_uncertainty`; use
`candidate_facet_support` everywhere a candidate is ranked or gated.

So `(low, f)` becomes the diagnostic outcome that confirms `facet_absent:f`, and an
item covering none of the open facets has **near-zero EIG** for the facet hypothesis
set — exactly the signal that should have suppressed the bad follow-up. This is a
minimal, interpretable extension of the existing graded-IRT conditional model
(`spec.md` §5); the `θ_mastered`/`θ_unfamiliar` anchoring and graded marginals are
unchanged.

**Per-facet outcome space (don't over-interpret one global low score).** The existing
conditional model's outcome is the *global* `(score_bucket, error_type)` (`Outcome`,
`probes.py:409`) — one bucket for the whole item. For the facet objective the diagnostic
outcome for facet `f` must be **per-facet**: bucket the grader's `facet_outcomes[f]`
(already emitted by `resolve_coverage` and threaded through `derive_facet_outcomes`)
into the same `low/mid/high`, and overlay the `misconception:E` error channel only when
`f ∈ candidate_facet_support(item)` **and** `E ∈ fatal_error_ids(item)` (the
`probes_item` predicate above). Then `EIG_f` is taken over facet `f`'s **own** outcome
variable, so a
low *global* item score updates only the facets that actually scored low. Without this
per-facet outcome, a single low item score would confirm `facet_absent` for **every**
open facet at once — the over-interpretation this workstream exists to prevent, and the
mirror image of the §1B mastery-rise bug on the diagnosis side.

### 2.3 Wire EIG into the follow-up path; delete the dead path

- `_choose_intervention_item` (`services/followups.py:438`) gains an EIG branch that
  mirrors the now-dead `_choose_followup_item` (`services/followups.py:290`):
  rank candidates by
  `familiarity.independent_evidence_discount * facet_probe_eig_component(...)`,
  where `facet_probe_eig_component` computes §2.1's importance-weighted sum of per-facet
  marginals via a **new `facet_expected_information_gain`**. This is *not* a reuse of the
  existing `expected_information_gain` (`services/probes.py:452`): that function is
  hardwired to the global `(score_bucket, error_type)` outcome and returns a single LO-EIG.
  The new function takes §2.2's per-facet outcome space (`facet_outcomes[f]` bucketed
  `low/mid/high` plus the per-facet error overlay) and returns a per-facet marginal EIG;
  `expected_information_gain` is the *template* for the IRT conditional math, but the
  outcome variable, the candidate-support input (`candidate_facet_support`, not
  `covered_facets`), and the return shape all change. Do not call the global-outcome
  `expected_information_gain` for the per-facet marginals.
- Delete `_choose_followup_item` once its logic is folded in (no caller; confirmed
  by grep). Do not leave two selectors.
- The overlap-Jaccard ranker survives **only** as the tie-break / fallback when no
  facet hypothesis set exists (cold LO with no open uncertainty), preserving current
  behavior on the cold path.

### 2.4 Selection-time hard gate

Add the gate that `min_target_facet_overlap` only documented before — and **enforce
the configured threshold, not merely a non-empty intersection.** A candidate is
**ineligible** as a diagnostic unless its facet overlap meets `min_target_facet_overlap`,
regardless of EIG ranking. A non-empty-only gate would still admit a *noisy* item — one
target facet buried among many unrelated ones, Jaccard ≈ `1/(1+k) ≪ 0.5` — which is
exactly the off-target probe this workstream exists to stop.

**Measure overlap against a pre-derived diagnostic gate target, with static candidate
support.** The gate is

```
dominant_target_facet ∈ candidate_facet_support(item)
AND
target_precision(candidate_facet_support(item), diagnostic_gate_facets)
  ≥ min_target_facet_overlap

where target_precision = |candidate_facet_support ∩ diagnostic_gate_facets|
                         / |candidate_facet_support|
```

and **all operands are computable at selection, before any need exists** — closing the
circularity the earlier draft had (it keyed the gate on "the current need's target"
while the need was created only *after* the gate):

- `dominant_target_facet` is derived *ahead of* selection by ranking the open
  `facet_uncertainty` rows by the §3.2 / §2.7 target score and taking the top facet. It
  is the **primary gate facet**: a candidate that does not exercise it is not a
  diagnostic follow-up for this need.
- `diagnostic_gate_facets` is the **best available reference set**, resolved by a strict
  fallback chain so the gate is well-defined at every rollout phase:
  1. the enriched, **capped, grader-attested** assessed target set from §2.7 / §3.2
     (failed facets ∪ grader error-attribution targets ∪ structured repair-suggestion
     targets, scored and capped per the §2.7 builder) — the Phase-C reference;
  2. failing that (pre-Phase-C, no enrichment yet), the raw **failed facet set**
     (`_target_facets_from_debug`, `services/followups.py:328`) — a *safe* interim under
     a precision metric (see "Reconciling the live gate" below);
  3. failing that (cold LO, no failed/target metadata), the singleton
     `{dominant_target_facet}`.
  Rung 3 is exactly what the live code measures against unconditionally today; rungs 1–2
  are the enrichment this section adds.
- `candidate_facet_support(item)` is the **static** support from §2.2
  (`repair_targets or evidence_facets`), never the attempt-time `covered_facets`.

This is a precision gate, not a Jaccard gate over the whole failed set. A clean
single-facet probe supporting `{f}` passes even when the broader diagnostic context is
`{f, g, h}`; a generated two-facet probe supporting `{f, g}` also passes if both facets
are in the enriched target; a noisy `{f, x, y, ...}` fails because most of its support is
unrelated. The extra `dominant_target_facet ∈ support` requirement keeps the primary
repair focus from being dropped just because a candidate covers some adjacent rationale
facet — and it is **not** redundant with the precision threshold: precision `≥ θ` can be
met by *other* gate facets while the primary is absent (`diagnostic_gate_facets = {f, g}`,
support `= {g}` → precision `1.0` but `dominant = f ∉ support`), which would serve a probe
that misses the actual focus. Read the gate as **full recall on the primary, precision on
the rest**.

**Reconciling the live `_jaccard` gate.** The landed selector computes
`_jaccard(candidate_facet_support(item), {dominant_target_facet})`
(`services/followups.py:471`). This is **not a different metric** — for a one-element
right operand, `_jaccard(S, {d})` equals `target_precision(S, {d})` exactly: when
`d ∈ S` both reduce to `1/|S|`, and when `d ∉ S` both are `0` (the union/denominator
difference only appears for `d ∉ S`, where the numerator is already `0`). So the live
gate *is* this section's precision gate evaluated on the impoverished singleton reference
set (rung 3). The fix is therefore to **feed the richer reference set (rungs 1–2), not to
change the metric** — and the singleton path is preserved as the exact current behavior,
making the change additive and backward-compatible.

But once the reference set has more than one element, **drop `_jaccard` and use
`target_precision`** — Jaccard is symmetric, so it leaks *recall* into a gate that should
be pure precision:

| `candidate_facet_support` | `diagnostic_gate_facets` | `_jaccard` | `target_precision` |
|---|---|---|---|
| `{f}` | `{f, g, h}` | 0.33 — **wrongly fails** | 1.00 ✓ |
| `{f, g}` (both targeted) | `{f, g, h}` | 0.67 | 1.00 ✓ |
| `{f, g, h}` (all targeted) | `{f, g, h}` | 1.00 | 1.00 ✓ |
| `{f, x, y}` (one targeted) | `{f, g, h}` | 0.20 | 0.33 — both reject ✓ |

Covering *every* open facet is not one probe's job (that is what multiple needs are for,
§3.2), so the gate must not penalize a focused probe for low recall against the target
set — exactly what the `{f}`-vs-`{f,g,h}` row shows Jaccard doing. This also corrects the
round-3 diagnosis: the `Jaccard = 1/N` rejection it attributed to "measuring against the
full failed set" is really an artifact of the *metric*, not the *reference set*.
`target_precision` against the full failed set does **not** reject a clean single-facet
probe (`{f}` vs `{f, g, h}` → `1.0`). So the failed set is a safe rung-2 reference under
precision, and §7 Phase 1 does not need to retreat to the bare singleton to dodge `1/N`.

The diagnostic *target set* the §2.2 EIG ranker sums over may still be the full open set
(§2.1). The *eligibility gate* uses the primary facet plus precision against the enriched
gate facets. This preserves the non-circular generation path while allowing rationale
text to expand the assessed facets when the learner-facing remediation genuinely points
at an adjacent mechanism.

The eligibility threshold needs a single source of truth: the gate reads
`min_target_facet_overlap`, and EIG (§2.2–2.3) does fine-ranking *above* it. Either
honor the configured value everywhere or delete the knob — do not ship a documented
threshold that nothing enforces (its state today: stamped only onto a need at
`followups.py:148`, never checked at selection).

**The gate and the cap are one decision.** A precision gate is only as sound as the
reference set is tight: an off-target facet that sneaks into `diagnostic_gate_facets`
stops counting as noise and starts *helping* a candidate clear the threshold. This is why
the gate's correctness is bounded by the §2.7 capping rule, and why the two must ship
together. The bound applies specifically to **rung-1 enrichment beyond the failed set**
(error-attribution and repair-suggestion targets, adjacent mechanisms): those admit
facets the learner did not necessarily fail, so they must be *grader-attested and capped*
(`max_diagnostic_target_facets`) before entering the reference. The **failed set itself
(rung 2) is self-justifying** — every facet in it is one the learner actually scored low
on, so covering it is signal by definition; it needs no cap for gate purposes. So: cap
hard on the enrichment, not on the failures.

**Derive `dominant_target_facet` from the same scorer that builds the reference.** The
primary gate facet must be `argmax` of the §2.7 facet score (restricted to failed/open
facets), so the primary and the reference set never disagree about what matters most. The
landed code's interim heuristic (`max` over open `facet_uncertainty` by
`uncertainty × severity`, `services/followups.py:458`) is acceptable until the scorer
lands, but converge them then — this is what round-2's "derive the dominant facet before
selection" was protecting.

**Design tension, to set deliberately:** a stricter threshold trips Workstream 3
generation more often, leaning harder on in-session Codex availability
(`runtime.ready`). Pick the value with the generation-trigger rate and the §3.2
fallback in mind; `0.5` is a starting point, not a derived constant — flag for refit
against `learning_outcome_labels`.

If the gate eliminates every existing item, fall through to Workstream 3 (generation)
rather than serving a sub-threshold item. This rule makes the motivating follow-up
impossible.

### 2.5 Connection to the architecture pivot

This keeps the decision **interpretable and loggable at the facet grain**: the
chosen follow-up's `decision_features` (migration 011) gain the facet hypothesis
prior, the per-facet EIG, and the realized facet-uncertainty drop. That is the
substrate for `architecture_pivot.md` §3 — regressing the §15.7-style constants and,
later, a learned selection policy directly onto `learning_outcome_labels` **per
facet** instead of per LO. v0.3 ships the hand-built facet EIG as the teacher policy
and fallback under the existing `eig_reliability` ramp.

### 2.6 Follow-up candidate-slate logging

Every intervention follow-up decision should log the **full candidate slate**, not just
the chosen item. This is low-risk instrumentation and high-value training data: the
future learner policy needs to know which candidates were available, which were filtered,
and why generation or fallback was triggered.

Log one slate per `evaluate_intervention_followup` call, keyed by `attempt_id` and
`decision_type = 'followup'` (extend `decision_features.decision_type` or add
`followup_candidate_slates` / `followup_candidate_slate_items` if row-shaped storage is
cleaner). The logged payload must include, for each existing LO candidate considered:

- `practice_item_id`, `candidate_facet_support`, `dominant_target_facet`, and the open
  facet set used by EIG.
- `target_precision`, `min_target_facet_overlap`, `gate_passed`, and `filtered_reason`
  (`subthreshold_overlap`, `bad_item_suspicion`, `excluded_source_item`, etc.). Log it as
  `target_precision`, not the landed `target_overlap` field name (`services/followups.py`):
  the value is `target_precision(support, diagnostic_gate_facets)` (§2.4), and naming it
  "overlap" invites the Jaccard reading the gate explicitly rejects. Also log the resolved
  `diagnostic_gate_facets` and the fallback rung used (enriched / failed-set / singleton),
  so the reference set the precision was taken against is auditable.
- `facet_eig_by_facet`, `total_facet_eig`, familiarity discount, bad-item suspicion,
  scaffold / intent bonus, final rank, and `selected`.
- Decision outcome: `queued_diagnostic`, `created_need_for_generation`,
  `queued_non_diagnostic_review`, or `suppressed`, plus the chosen `need_id` or
  fallback item if applicable.

Record **filtered candidates too**. Otherwise the training log cannot learn the
threshold, diagnose overly strict gates, or explain why the thin-pool generation path
fired. When no candidate passes the gate, the slate still records the rejected options
and the generated need records both `dominant_target_facet` and the enriched
`target_facets` so the generate/accept loop is auditable at the same facet grain as the
selector and the authored probe's metadata.

### 2.7 Grader remediation intent is lossy at the facet grain (structural note)

The facet id is the **only** handle that survives the chain diagnosis → need →
authoring → decision log. But the grader's actual remediation intent is richer than
the facet id and lives as free text in
`attempt_feedback_metadata.repair_suggestions[].rationale` — the same text already
surfaced to the learner as the diagnostic need. Two records key on the facet alone: the
`intervention_need` (`target_facets_json`, `services/followups.py:150`) and the
follow-up `decision_features` (§2.5/§2.6: facet-keyed prior, per-facet EIG, realized
drop). So a generated probe can be **perfectly on-facet yet miss the grader's intent**,
and — worse for the pivot — the training log cannot *see* that mismatch. The off-policy
reward is blind to intent fidelity, which is exactly the signal a per-facet
`learning_outcome_labels` regression (§2.5, `architecture_pivot.md` §3) would want.

Observed instance (adjacent to the §0 case): a real run whose UI diagnostic need read
*"contrast symmetric (`Aᵀ=A`) vs orthogonal (`Aᵀ=A⁻¹`) matrices, then derive
`(Au)·v = u·(Av)`"* drove an authoring call that saw only
`target_facets = ["orthogonality_definition"]` and returned a generic
orthogonality-*definition* probe — on-facet, but not the mechanism the grader flagged.

This is fixed in four independently shippable, reversible phases. The invariant across
all of them: **`target_facets` remains the authoritative assessment contract, but it is
derived from the same remediation signals the learner saw.** The §2.4 gate keeps a
single `dominant_target_facet` as the primary hard requirement, while `target_facets`
may include one or two supporting facets when the rationale explicitly targets them.
`evidence_facets == target_facets` remains the authoring invariant; the change is how
`target_facets` is chosen before authoring.

- **Phase A — plan-time steering (shipped).** `build_diagnostic_practice_plan`
  (`services/practice_generation.py:188`) joins the source attempt's
  `repair_suggestions` via `fetch_attempt_feedback_metadata`, carries them as
  `repair_rationales` on `DiagnosticPracticeTarget`, and
  `_diagnostic_practice_instructions` tells Codex to *frame* the probe around them
  (choosing among several) while keeping `evidence_facets == target_facets`. This patches
  the **authoring prompt** only. It does **not** fix the records: the rationale is
  reconstructed at plan time, so it drifts if the attempt is regraded between need
  creation and authoring, and the decision log still cannot see which intent drove the
  need.

- **Phase B — structured facet targets on repair suggestions.** Extend
  `RepairSuggestion` with `target_evidence_families: list[str] = []`. The grader already
  emits `ErrorAttribution.target_evidence_families`; repair suggestions need the same
  narrow facet handle so a learner-facing sentence like *"contrast symmetric
  (`A^T = A`) vs orthogonal (`A^T = A^{-1}`), then derive `(Au) dot v = u dot (Av)`"*
  carries `["symmetric_dot_identity"]` (and, only if directly assessed, an adjacent
  facet such as `orthogonality_definition`). Validation canonicalizes these ids through
  `vault.canonical_facet_id`, drops unknown facets with a manual-review reason just like
  error attributions, and preserves the free-text `rationale` for the UI.

- **Phase C — enrich and freeze the need target.** At need creation
  (`evaluate_intervention_followup` → `upsert_intervention_need`,
  `services/followups.py:134`), compute `target_facets` with a need-time target builder
  instead of copying only `selection.dominant_target_facet`:

  1. Add failed attempt facets from `_target_facets_from_debug`.
  2. Add each `error_events[*].repair_plan.target_evidence_families`, weighted by error
     severity.
  3. Add each `repair_suggestions[*].target_evidence_families`, weighted as remediation
     intent and linked to its `rationale` / `practice_mode`.
  4. Seed with `dominant_target_facet` if the scored set is empty.
  5. Sort by score, keep the primary `dominant_target_facet`, and cap the assessed set
     with `max_diagnostic_target_facets` (default 2; hard maximum 3 only when every facet
     is explicitly targeted by grader metadata).

  Store the enriched set in `intervention_needs.target_facets_json`. Snapshot the
  rationale(s), facet-source scores, and `primary_target_facet` into a dedicated nullable
  `diagnostic_focus_json` column on `intervention_needs` rather than overloading
  `candidate_requirements_json`; the latter is consumed as a hard gate spec and focus
  metadata must stay auditable rather than silently changing acceptance semantics. Echo
  the same snapshot into `decision_features.context`. Backward compatibility: needs
  created before Phase C have no frozen focus, so `build_diagnostic_practice_plan` keeps
  the Phase-A join as a fallback when `diagnostic_focus_json` is null. This removes
  regrade drift and lets rationale text influence `target_facets` before authoring.

- **Phase D — first-class diagnostic focus.** Promote the snapshot from "free text
  reverse-engineered from `repair_suggestions`" to a typed object the **grader emits
  directly** alongside per-facet `facet_outcomes` (e.g. `{facet_id, remediation_kind,
  target_mechanism_ref?, rationale}`), and extend the §2.6 EIG/selection logging to key on
  `(facet_id, diagnostic_focus)` rather than `facet_id` alone — the substrate for a
  fidelity-aware learned policy. Migration is cheap *because* Phase C already added
  `diagnostic_focus_json`: Phase D only (a) swaps the **producer** (grader emits instead
  of `practice_generation` deriving), and (b) adds focus to the logging/EIG key. The
  free-text `rationale` field persists, so Phase-C rows stay readable; the structured
  fields are additive and nullable.

Why not jump straight to Phase D: the free-text rationale **already exists and is
validated by being learner-facing**, and the narrow facet ids needed for Phase B mirror
`ErrorAttribution.target_evidence_families`. That is enough to fix the current
target-facet lossiness. The richer diagnostic-focus schema should be designed against the
recurring fields seen in real frozen rationales rather than guessed up front — the same
"ship the placeholder, refit against data once it exists" stance as the §1B.4
variance-floor curve.

---

## 3. Workstream 3 — Generation when the item pool is thin

### 3.1 The trigger gap

`build_diagnostic_practice_plan` (`services/practice_generation.py:188`) already
turns pending intervention *needs* into facet-targeted generation proposals carrying
`target_facets`, `facet_recall_mean_by_facet`, and a
`recommended_difficulty_band`. It is simply never reached, because a need is only
created when `_choose_intervention_item` returns `None`, and the LO always had a
second item to return. v0.3 changes the trigger from *"no item physically exists"* to
*"the §2.4 eligibility gate left no candidate"* (see §3.2).

### 3.2 Target

Generation must be triggered by **facet coverage of the open uncertainty**, not by
"is there literally any other item":

1. **Derive the diagnostic gate target *before* the gate** (§2.4 / §2.7): score the open
   `facet_uncertainty` rows, failed attempt facets, grader error-attribution targets, and
   structured repair-suggestion targets. The top scored facet is
   `dominant_target_facet`; the capped scored set is `diagnostic_gate_facets`. These
   values drive the §2.4 eligibility gate now and become the generated need's
   `diagnostic_focus_json.primary_target_facet` and `target_facets` later — derived
   once, reused, never recomputed from a need that does not yet exist. If, after the gate,
   **no eligible item** meets `min_target_facet_overlap`, create the intervention need now
   (today's `upsert_intervention_need` path, `services/followups.py:134`) with
   `desired_intent` from `_choose_intent`, `target_facets = diagnostic_gate_facets`, and
   the frozen `diagnostic_focus_json` snapshot from §2.7 Phase C. **One need = one
   remediation intent with one primary gate facet**; `target_facets` may include a small
   number of supporting assessed facets when the learner-facing rationale explicitly
   targets them. Emit additional needs for lower-ranked *primary* facets only up to
   `max_interventions_per_lo_per_session` — in v0.3 typically just the single top
   primary facet.
2. The need's `candidate_requirements.min_target_facet_overlap` is enforced *both*
   at generation-acceptance time and at any future selection, so a generated probe
   that drifts off the target facets is rejected. Because the gate requires the primary
   facet and measures support precision against the enriched target set (§2.4), a probe
   that cleanly isolates the primary facet or covers only primary+supporting target
   facets passes; one that drifts onto unrelated facets is rejected — so the
   generate→accept loop terminates even when many facets are open.
3. **Synchronous thin-pool path:** when the pool is thin *and* the session is live,
   prefer generating a single targeted probe over deferring to a batch job, subject
   to the existing per-LO/session intervention cap
   (`max_interventions_per_lo_per_session`, `services/followups.py:111`) and
   `available_minutes`. Generation latency is bounded by reusing the existing
   `generate_diagnostic_practice_proposal` (`services/practice_generation.py:248`);
   if it cannot return within budget, queue the need and surface the LO's best
   *partial-overlap* item as a non-diagnostic review item, clearly logged as such
   (not counted as diagnostic evidence).

### 3.3 Generation instructions are facet-scoped

`_diagnostic_practice_instructions` (`services/practice_generation.py:360`) must
pin the generated item to the enriched target facets and their source claim. For the
motivating case the primary target is `symmetric_dot_identity`, so the generated probe is
something like *"Why does symmetry give `(Au)·v = u·(Av)`?"*; when the frozen rationale
also explicitly asks for a contrast with orthogonal matrices, the same item may carry a
supporting assessed facet and ask the learner to distinguish `A^T = A` from
`A^T = A^{-1}`. The point is to isolate the failed mechanism, not the already-mastered
classification statement.

The instructions also carry the grader's `repair_rationales` as **framing** (Phase A,
§2.7) and, after Phase C, the frozen `diagnostic_focus_json` as the reason those
`target_facets` were selected. `evidence_facets == target_facets` keeps the diagnostic
state measured by the probe aligned with the learner-facing remediation rather than with
the old single-facet fallback.

### 3.4 Cold-start / Bitter-Lesson alignment

Generation stays **Codex-forward** (consistent with `spec_mvp.md` scope: "Codex
grading", "Codex-generated proposals"); it does not introduce the excluded
simulator-generated items in the automatic scheduler. The authored item pool remains
the cold-start prior; generation fills facet gaps the pool cannot cover, exactly the
"human knowledge as prior, computation fills the long tail" stance of
`architecture_pivot.md` §4.

---

## 4. End-to-end trace on the motivating case (acceptance narrative)

1. Attempt scores 1/5; grader attributes `facet_outcomes` with
   `symmetric_dot_identity ≈ 0`, `distinct_eigenvalue_logic ≈ 0`, and
   `learner_confidence = hedged` on both. → two `facet_uncertainty` rows open
   (§1.4).
2. Facet hypothesis set built over those two facets (§2.1).
3. `pi_apply_spectral_theorem` covers neither failed facet → eligibility gate
   removes it (§2.4); its facet EIG is ≈0 anyway (§2.2).
4. No eligible existing item → the open set `{symmetric_dot_identity,
   distinct_eigenvalue_logic}` drives EIG, while the enriched target builder (§2.7 /
   §3.2) selects `symmetric_dot_identity` as the primary facet and adds any
   rationale-targeted supporting facets. `build_diagnostic_practice_plan` generates a
   probe on the symmetry⇒dot-identity mechanism (§3.3); `distinct_eigenvalue_logic`
   follows as a second primary-facet need if session budget allows.
5. Had `pi_apply_spectral_theorem` been attempted anyway, its `lo_relative_coverage`
   is ≈0 against the open facets (§1B.2), so the 3/3 barely moves `logit_mean` and the
   variance floor (§1B.3) forbids the LO from becoming "confident" while
   `symmetric_dot_identity` is unexamined. The diagnostic clearing rule (§1.2) and the
   coverage-weighted update (§1B) agree: the gap stays visible.
6. The learner answers the *targeted* probe; the facet-uncertainty belief updates, and
   now the mastery update *does* carry weight because the attempt covers the open
   facet.
7. The "Why now?" / mastery view shows "spectral-theorem LO · `symmetric_dot_identity`
   unexamined" until step 6 resolves it (§1B.7), so the number is never silently wrong.

Mastery no longer inflates over an unexamined gap, the displayed number is honest, and
the follow-up interrogates the thing the learner actually flagged.

---

## 5. Acceptance criteria

- [ ] A sub-`min_target_facet_overlap` item is never served as a diagnostic
      follow-up — including a *noisy* item with one matching facet among many unrelated
      ones (regression test built from the motivating case fixture).
- [ ] The eligibility gate derives `dominant_target_facet` and
      `diagnostic_gate_facets` *before* selection, requires the dominant facet in
      candidate support, and measures target precision against the enriched set; a clean
      single-facet probe is admitted even with ≥3 open facets (the `Jaccard = 1/N`
      rejection against the full failed set never occurs), and the generate→accept loop
      terminates.
- [ ] The gate uses `target_precision`, not `_jaccard`, against a multi-facet reference
      set: a probe supporting `{f}` passes against `diagnostic_gate_facets = {f, g, h}`
      (precision `1.0`, where Jaccard would give `0.33` and reject), a probe supporting
      `{f, g}` against `{f, g, h}` passes, and a noisy `{f, x, y}` fails. The reference set
      resolves by the rung chain (enriched → failed set → singleton), and on a singleton
      reference the new gate reproduces the landed `_jaccard(support, {dominant})` value
      exactly (additive-change regression test).
- [ ] Candidate ranking and gating use the static `candidate_facet_support(item)`
      (`repair_targets or evidence_facets`); selection never calls the attempt-dependent
      `resolve_coverage` / reads `covered_facets` for an unattempted candidate.
- [ ] A facet authored below `tau_facet_share` contributes 0 to `c_f`, and a facet below
      `min_facet_evidence_mass` does not count toward `covered_required_fraction` — so
      incidental annotation neither earns coverage weight nor satisfies the variance-floor
      breadth test.
- [ ] A correct attempt on a facet disjoint from an open `facet_uncertainty` does
      not resolve that uncertainty and does not, by itself, clear the follow-up.
- [ ] A high-scoring attempt whose `lo_relative_coverage` of the LO's required/open
      facets is ≈0 moves `logit_mean` negligibly (regression from the motivating case).
- [ ] `lo_relative_coverage` is injected at the `effective_coverage` argument into
      `resolve_error_impact` (the `observation_weight_override` the live path consumes),
      **not** the `evidence_coverage` term `observation_weight` short-circuits past; a
      unit test asserts a live attempt's weight changes when `lo_relative_coverage`
      changes (guards against the no-op wiring).
- [ ] With ≥1 open facet uncertainty, an attempt covering none of the open facets
      yields `lo_relative_coverage == 0` *exactly* (open-facet restriction), not merely
      a small `kappa_uncertain`-dependent value.
- [ ] `logit_variance` cannot fall below `variance_floor(covered_required_fraction)`;
      repeated hits on one facet do not manufacture LO confidence while another
      required facet is unexamined.
- [ ] The mastery view exposes, per LO, required facets that are unexamined or carry
      open `facet_uncertainty` alongside `mastery_mean` (no bare high number over an
      untested facet).
- [ ] The mastery view distinguishes `unexamined`, `uncertain`, `known_gap`, and
      `solid`; a resolved posterior whose top hypothesis is `facet_absent` or
      `misconception:E` remains visible as a known gap and routes to repair rather than
      disappearing as if the facet were mastered.
- [ ] `_choose_followup_item` is deleted; the live follow-up path computes facet EIG.
- [ ] `conditional_distribution` returns ≈0 EIG for the facet hypothesis set on an
      item covering none of the open facets, and high EIG on one that isolates a
      single open facet.
- [ ] Facet EIG is the importance-weighted sum of independent per-facet marginal
      information gains, each computed over the grader's per-facet `facet_outcomes[f]`
      (not the global `(score_bucket, error_type)`); a low *global* score on a
      multi-facet item updates only the facets that actually scored low, never every
      open facet at once.
- [ ] The per-facet marginals are computed by a dedicated `facet_expected_information_gain`
      over the §2.2 per-facet outcome space; the global-outcome `expected_information_gain`
      (`probes.py:452`) is not called for the facet objective.
- [ ] When no eligible item exists, an intervention need with the correct
      `target_facets` is created and reaches `build_diagnostic_practice_plan`.
- [ ] Diagnostic generation carries the source attempt's grader `repair_rationales`
      into the authoring instructions as framing (§2.7 Phase A), with blanks dropped and
      `practice_mode` preserved; free-text rationale framing does not directly override
      `target_facets` without structured facet targets.
- [ ] `RepairSuggestion.target_evidence_families` is validated/canonicalized and the
      need-time target builder uses it, along with error-attribution repair targets, to
      enrich `intervention_needs.target_facets_json` before authoring (§2.7 Phase B/C).
- [ ] `diagnostic_focus_json` freezes the selected rationale(s), facet-source scores,
      and `primary_target_facet` onto the need and is echoed into `decision_features`
      so plan-time authoring never has to infer intent from a later regrade.
- [ ] `learner_confidence = hedged` raises facet uncertainty above
      `hedge_uncertainty_floor` even at partial rubric credit.
- [ ] `facet_uncertainty` is fully rebuildable from raw attempts (replay parity test;
      appears in `derived_state_rebuilds`).
- [ ] `decision_features` for a follow-up records the facet hypothesis prior,
      per-facet EIG, and realized facet-uncertainty drop.
- [ ] Each follow-up decision logs a candidate slate including filtered candidates,
      candidate facet support, dominant target facet, overlap/gate result, per-facet EIG,
      selected/fallback outcome, and generation need id when no eligible item exists.
- [ ] `facet_uncertainty` persists the full `hypothesis_marginal`; facet EIG and the
      realized uncertainty drop are computed from it (not a re-invented prior), and
      `uncertainty == H(hypothesis_marginal)`.
- [ ] `learner_confidence` is a raw `grading_evidence` field; `facet_uncertainty`
      rebuilds from `practice_attempts` + `grading_evidence` alone (no dependence on
      derived `attempt_debug_payloads`).
- [ ] A full-breadth, fully-covering multi-facet attempt yields `lo_relative_coverage`
      ≈ 1 (not ≈ 1/N) and moves `logit_mean` normally — the coverage term does not
      collapse legitimate broad evidence (unit test on the §1B.2 formula).
- [ ] Generation creates one need per remediation intent with one primary gate facet;
      `target_facets` may include a small rationale-targeted supporting set, and the
      generated item's `evidence_facets` / `repair_targets` exactly match that set.

## 6. Out of scope for v0.3 (kept for later pivot stages)

- Replacing the LO mastery scalar with a per-facet latent or a learned
  knowledge-tracing model (pivot Stage 2). v0.3 instead **coverage-weights the single
  scalar** and floors its variance by coverage breadth (Workstream 1B); the latent is
  not split.
- Splitting mis-cut LOs into finer LOs in authoring (raised in §1B.5 as the right fix
  when facets are genuinely independent; tracked as an authoring question, not built).
- Learned/searched selection policy or MCTS lookahead over the facet objective
  (pivot Stage 3); v0.3 ships the myopic facet EIG as teacher + fallback.
- Embeddings-derived facet inference from raw item text (pivot Stage 4); facets
  remain authored `evidence_facets` for now. The forward-looking design — facets as
  coordinates, intent as a vector, supervised by outcome transfer — is written up in §8
  so the §2.7 Phase A→B→C→D migration aims at it, but none of it ships in v0.3.
- Open-ended multi-intent generation. v0.3 allows a need's `target_facets` to include a
  small supporting set when one frozen rationale targets those facets, but it does not ask
  one generated item to repair unrelated diagnostic intents. Additional primary facets
  become additional needs.
- A learned, first-class structured **diagnostic focus** and intent-aware EIG key
  (`(facet_id, diagnostic_focus)`, §2.7 Phase D). v0.3 ships the narrower structured
  repair-suggestion facet targets and frozen focus snapshot; the learned focus vector is a
  later pivot-stage feature.

---

## 7. Rollout sequencing (ship order — each phase independently valuable)

The workstreams are separable; the highest-ROI fixes need **no schema and no Codex**.
Ship in phases so the visible bug dies long before the Codex-dependent work lands.

**Phase 1 — kill the visible bug; no migration, no grader change.**
- **Selection-time hard gate (§2.4):** filter `_choose_intervention_item`
  (`followups.py:438`) candidates by `target_precision(candidate_facet_support,
  diagnostic_gate_facets) ≥ min_target_facet_overlap`, with `dominant_target_facet ∈
  support` as the primary floor. On the no-grader-change path the reference set is the
  **failed facet set** (`_target_facets_from_debug`, rung 2), *not* the bare singleton:
  under a precision metric the failed set does not trigger the `1/N` rejection that round
  3 feared (that was a Jaccard artifact — §2.4), and it correctly rewards a probe that
  covers a *second* failed facet instead of treating it as noise. The landed code already
  computes the equivalent singleton precision via `_jaccard(support, {dominant})`
  (`followups.py:471`); this phase swaps the reference set (and renames the metric to
  `target_precision`), which is additive — it reduces to the current behavior whenever the
  failed set is a singleton. A few lines; alone it makes the motivating 0-overlap follow-up
  impossible without rejecting clean single- or multi-facet probes when many facets are open.
- **Create-need-when-no-*eligible*-item (§3.1 / §3.2):** change the need trigger from
  "`_choose_intervention_item` returned `None`" (no item *exists*) to "the eligibility
  gate left no candidate," so generation is actually reached.
- **Delete the dead `_choose_followup_item`** (`followups.py:290`, no caller — confirmed
  by grep). Do not leave two selectors.
- **Honest-UI read-model (§1B.7):** pure read model, no belief-state change — ship it
  *first of all*. It surfaces "0.8 overall · `symmetric_dot_identity` unexamined" and
  fixes the trust problem at zero risk, even before the belief math changes.

**Phase 2 — belief reframe; one migration (`012_facet_diagnostic_state.sql`).**
- `facet_uncertainty` with the serialized `hypothesis_marginal` (§1.4), registered in
  `derived_state_rebuilds`.
- Corrected LO-relative coverage (§1B.2) wired into the **`effective_coverage` argument
  of `resolve_error_impact`** — the override the live path actually consumes — **not**
  the `evidence_coverage` term, which `observation_weight` short-circuits past on every
  live attempt (§1B.1–1B.2). Wiring it into `evidence_coverage` ships a **no-op**; this
  is the single most load-bearing line of the phase. Includes the open-facet restriction
  (§1B.2) so a disjoint attempt is literally ≈0, plus the variance floor (§1B.3).
- This phase is what makes the §3.2 "serve a partial-overlap review item" fallback
  *safe*: only once 1B is in place does a non-diagnostic review item stop re-inflating
  mastery. **Sequencing dependency** — Phase 2 must precede any reliance on that
  fallback.

**Phase 3 — facet EIG.**
- Facet-aware `conditional_distribution` (§2.2) over a **per-facet outcome space**
  (`facet_outcomes[f]`, not the global score bucket) + facet-EIG ranking (§2.3) as the
  **importance-weighted sum of independent per-facet marginals** (§2.1), folded into the
  live selector; the Jaccard ranker survives only as the cold-path fallback.
- Follow-up candidate-slate logging (§2.6): log selected and filtered candidates with
  gate/EIG features so `min_target_facet_overlap`, generation triggers, and future
  learned policies can be evaluated from the replay log.

**Phase 4 — Codex-dependent (riskiest, longest pole).**
- `learner_confidence` hedge signal (§1.3): new raw `grading_evidence` field + schema +
  prompt changes; **zero presence in the codebase today.**
- `RepairSuggestion.target_evidence_families` (§2.7 Phase B): schema + prompt +
  validation changes so learner-facing remediation text carries the facets it is meant to
  repair.
- Enriched need targets and frozen focus (§2.7 Phase C): compute
  `diagnostic_gate_facets` / `target_facets` from failed facets, error-attribution
  targets, and repair-suggestion targets; persist `diagnostic_focus_json` and echo it into
  decision logs.
- Synchronous in-session generation (§3.2), gated on `runtime.ready` with the
  documented queue-and-fallback path. Availability and latency are real risks; neither
  blocks Phases 1–3.

The **durable** investment across all phases is the per-facet `decision_features`
logging (§2.5), which survives the architecture pivot. The hand-tuned constants
(`kappa_uncertain`, the variance-floor curve, `min_target_facet_overlap`, the EIG
anchors) are explicitly *disposable* teacher-policy parameters — refit them against
`learning_outcome_labels` rather than over-investing in tuning them now.

---

## 8. Stage 4 design — facets as coordinates, intent as a vector (forward-looking)

This is where §2.7's Phase D ("first-class diagnostic focus") evolves once transfer data
accrues, and is the concrete design for the `architecture_pivot.md` Stage 4 item that §6
lists as out of scope for v0.3. **Nothing here ships in v0.3.** It is written down now so
the Phase A→B→C→D migration (§2.7) is aimed at the right destination — in particular so
Phase C's frozen `(item, intent, target_facets, outcome)` tuples are collected in a shape
the embedding can actually consume.

### 8.1 The reframe: a facet is a region, not a point

A discrete facet id (`orthogonality_definition`) is a single point, so it cannot separate
*"state the definition of orthogonal"* from *"derive `(Au)·v = u·(Av)` from symmetry"* —
both collapse onto one id though they are different competencies (the §2.7 lossiness, at
its root). Stage 4 represents each **item** and each **diagnostic intent** as a vector in
a facet space where **distance means "exercises the same underlying competence."** The
discrete id becomes a *labeled region* over that space, not the unit of representation;
the grader's rationale and a generated probe become nearby points.

Representation: an **anchored residual embedding**, `intent = anchor(facet) + δ(intent)`.
The authored discrete facets remain labeled anchor points — this preserves the §1B.7
honest-UI story (a region still has a name) and keeps the §2.4 gate / §2.2 EIG machinery
working unchanged on the anchors. The learned residual `δ` carries the intent refinement
the discrete id throws away. **When `δ = 0` the system is bit-for-bit the discrete-facet
system**, so Stage 4 is additive and reversible. (Interpretable-axis variants — recovering
the dimensions as latent factors of the outcome covariance via multidimensional IRT /
factor analysis, or a sparse dictionary basis — are the aspirational form of the same
object; not required for the first cut.)

### 8.2 The metric is the whole design: transfer, not text

Two candidate geometries, and conflating them is the trap:

- **Text/semantic similarity** (off-the-shelf encoder over prompt + rationale): available
  with zero behavioral data, but semantic adjacency ≠ diagnostic equivalence. "Define
  orthogonal" and "derive symmetry ⇒ dot-identity" are semantically close yet test
  different skills; two differently-worded items can test the identical skill. Text is a
  **prior**, never the target.
- **Outcome-transfer geometry**: distance = how much performance on one item predicts
  performance on another *after removing global ability*. This is the structure the pivot
  optimizes (`learning_outcome_labels` per facet) and the **target** the embedding is
  trained to.

### 8.3 Data sources (the skeleton already exists)

1. **Behavioral transfer — the target signal, already logged.** `learning_outcome_labels`
   records transfer pairs: `(source_attempt → outcome_attempt, label_type, label_value,
   elapsed_seconds, intervening_attempt_count)` with both attempts' full metadata. This is
   the supervised label set: train so embedding distance predicts `label_value`,
   residualized for ability via `learner_theta` / mastery. `evidence_facet_recall_state`
   (per-`(facet, item)` Beta posteriors) is the co-movement substrate for factor-analyzing
   latent axes. Ground truth, but data-hungry — currently single-digit rows.
2. **Grader structured outputs — dense, cheap, per attempt.** `grading_evidence`
   (`points_awarded` per criterion → per-facet outcome vectors via the criterion→facet
   map; `learner_confidence`; free-text `evidence`) plus `repair_suggestions`. Dense
   intent descriptions without waiting for transfer data — but they encode the *grader's*
   ontology, so they must be corrected by signal (1) to avoid learning grader bias.
3. **LLM-as-annotator bootstrap — synthetic cold-start pairs.** Codex emits cheap pairwise
   judgments ("does probe X measure the same competence as intent Y?", "rank these by
   transfer") to seed the metric before behavioral data exists; signal (1) then overrides
   pairs that do not behave. Same "human-knowledge prior, computation fills the tail"
   stance as the rest of the pivot.

### 8.4 Implementation plan

Each step is independently shippable, offline-first, and gated behind a reliability ramp
before it touches live selection — mirroring how §2.3/§2.5 stage the facet EIG.

- **Step 0 — prerequisite (§2.7 Phase C).** Freeze diagnostic intent onto the need
  (`diagnostic_focus_json`) and echo it into `decision_features.context`. Without this the
  `(item, intent, target_facets, outcome)` tuple is unrecoverable and there is no corpus.
  *This is the gating dependency for all of Stage 4 and the reason Phase C is worth doing
  even though Phase A already fixes the visible authoring bug.*
- **Step 1 — assemble the corpus (offline, no runtime change).** A batch job joins
  `learning_outcome_labels` ⨝ `practice_attempts` ⨝ `grading_evidence` ⨝ frozen focus into
  training rows: `(item_text, intent_text, anchor_facets, per_facet_outcomes,
  transfer_label, ability_residual)`. Materialize to a versioned artifact (not live state);
  no schema change beyond Step 0.
- **Step 2 — text-prior embedding (shadow, additive).** Encode `prompt + expected_answer +
  frozen rationale` with an off-the-shelf encoder; store a coordinate per item in a new
  nullable sidecar (`facet_embedding(item_id, vector, model_version, fit_id)` or a
  `practice_item` column). Pure metadata — **read by nothing in the live path yet.**
- **Step 3 — transfer-supervised refinement (offline fit).** Metric/contrastive learning
  so distance predicts `label_value` (ability-residualized), anchored to the discrete
  facets as fixed points and learning only the residual `δ`. Versioned by `fit_id`;
  reproducible from the Step-1 corpus so it lands in `derived_state_rebuilds` discipline.
- **Step 4 — shadow influence on selection, behind a ramp.** Add an embedding proximity
  term (intent vector → open-uncertainty centroid) as an *additional* ranking feature in
  `_choose_intervention_item` / facet EIG, **activated only when held-out transfer
  prediction beats the discrete-overlap baseline** (an `eig_reliability`-style gate). The
  §2.4 hard gate keeps keying on discrete `dominant_target_facet` — the embedding informs
  *ranking*, never the hard constraint, so a bad fit degrades gracefully to today's
  behavior.
- **Step 5 — discrete labeling for the UI.** Nearest-anchor / clustering over the space so
  the §1B.7 read-model can still say "`symmetric_dot_identity` region · unexamined." The
  embedding is the internal metric; the labels stay the surface.

### 8.5 Validation and guardrails

- **Earn-its-place gate:** the embedding influences live selection only after held-out
  transfer AUC (or rank correlation against `label_value`) **beats the discrete-facet
  overlap baseline** on a replay split — same disposable-teacher discipline as §7's closing
  note. Until then it is shadow-logged for evaluation only.
- **Identifiability floor:** latent transfer structure needs cross-item and (ideally)
  cross-learner density; below a minimum tuple count Step 3 is suppressed and the system
  runs on the Step-2 text prior, because a thin corpus fits *text*, not transfer. Single-
  user cold start is the genuinely hard regime — text + LLM priors (8.3.2–8.3.3) carry it.
- **Circularity guard:** when both grader-derived (8.3.2) and behavioral (8.3.1) signals
  are present, the fit must weight behavioral transfer dominant; an embedding trained only
  on grader/text signals re-learns the authoring ontology rather than learning structure.
  Behavioral transfer is the only signal exogenous to authoring/grading.
- **Reversibility invariant:** discrete facets stay authoritative in the gate at every
  step; dropping the embedding term reverts to the exact discrete-facet behavior (`δ = 0`).

# Spec: Causal Learner Model (measurement-first, n=1-honest)

Status: draft for review — no code changes yet
Date: 2026-07-21
Origin: distilled from an external design analysis grounded in Kun Zhang's
causal-representation research (CMU; RLCD, measurement-perspective CRL,
natural counterfactuals, individualized transition models) and Andy
Matuschak's product constraints, cross-checked against the actual codebase.
Every "already exists" claim below was verified against source on 2026-07-21.

Related specs: `spec_new_improvements_v2.md` (umbrella charter / north star),
`spec_p0_measurement_correctness.md`, `spec_probe_eig_redesign.md`,
`spec_misconception_diagnostics.md`, `GRAPH_EDITOR_DESIGN.md`,
`spec_knowledge_model.md` (§5.2 contracts, §7.2 blueprints, §9.6 grid).

---

## 1. Core design decision

**Do not turn the concept graph into a causal graph by adding a generic
`causes` edge to `ConceptEdge`.** The semantic graph
(`prerequisite | confusable_with | part_of | related`) stays a
navigation/geometry layer. Causal claims about the *learner* live in
separate typed layers underneath it.

Two invariants, stated once and enforced everywhere:

1. **Evidence may flow backward through a task model; learning effects flow
   forward through time.** Success on a composite item may raise *predicted*
   ability on its components; it never creates *demonstration credit* for a
   component the assessment contract did not observe at the required
   capability level.
2. **Prediction can propagate; certification cannot.** This is the existing
   Ready-vs-Demonstrated dual axis, promoted to a named invariant for all
   causal machinery. (Ready = projected performance, may use model
   propagation; Demonstrated = evidence-ledger only. See
   `services/exam_readiness.py`, `services/certification.py`,
   `services/goal_certification.py`.)

### The honest framing (this paragraph governs everything below)

Kun Zhang's identifiability results assume population-scale samples, dense
multi-environment data, and rank conditions. LearnLoop is one learner,
local-first, generating dozens of adaptively-selected (= maximally
confounded) graded attempts per week. Therefore:

> At n=1, the causal formalism buys **discipline in what we claim**, not
> **inferential power**. The inference engine in practice is an LLM making
> structured judgments shaped by a good ontology, the recipe structure, and
> first-error traces. Every surface must present its numbers as what they
> are: priors and structured judgments, occasionally sharpened by a
> within-learner randomized contrast — never as identified posteriors.

Consequences: no `doubly_robust` / `hierarchical_bayesian` estimation
machinery, no pooled-population evidence grades (there is no fleet), no
posterior intervals in the data model until data exists that could fill
them. Deferred, not rejected — see §9.

---

## 2. Relationship ontology — the actual gap

"Prerequisite" conflates at least six relationships:

| # | Relationship | Meaning | Status in LearnLoop |
|---|---|---|---|
| 1 | Semantic | Explanation of B refers to A | EXISTS — `ConceptEdge` |
| 2 | Constitutive / task requirement | A valid method for B uses A | EXISTS — blueprint recipes: `all_of`, `any_of`, `integration` (`vault/models.py` `BlueprintRecipe`) |
| 3 | Epistemic implication | Success on B is evidence about A | EXISTS — Ready axis + criterion targets; bounded by invariant 2 |
| 4 | Instructional order | Teaching A first is more tractable | EXISTS — `RequirementModality = "instructional_order"` (also `hard`, `path_specific`, `facilitating`) |
| 5 | Acquisition causality | Improving A causes faster/more reliable acquisition of B | **MISSING** |
| 6 | Transfer causality | Practicing A improves future cold performance on B | **MISSING** |

So the ontology work is narrower than "build five graphs": rows 1–4 are
shipped. The new work is rows 5–6 as *time-indexed, typed, evidence-graded
hypotheses* (§7), plus honest labeling wherever temporal association is
currently at risk of reading as causal (§6, W0).

Time-indexing matters: `K_A,t → K_B,t+1` and `K_B,t → K_A,t+1` can both be
true without an instantaneous cycle. Mutually reinforcing skills are
expected, not a graph error.

Deterministic/logical relations (proof steps, algebraic equivalence,
conjunctive recipe requirements, representation transformations) are **not**
causal edges and must never be auto-oriented as such. They stay in the
blueprint/recipe layer or as explicit `deterministic_transformation` /
`definitionally_equivalent` relation kinds if ever needed.

---

## 3. The layered model (what exists vs. what's new)

| Layer | Answers | Status |
|---|---|---|
| A. Semantic concept graph | what relates to what; navigation | EXISTS — `ConceptEdge`; semantic kinds carry zero belief effect (`services/calibration_sessions.py`); even the prerequisite graph-prior is shadow-only, no live consumer |
| B. Performance-requirement hypergraph | what latent components a task uses; AND/OR recipes; integration factor | EXISTS — blueprints/recipes, `vault/models.py` |
| C. Measurement graph | which criterion measures which facet×capability; cross-loading; nuisance | LARGELY EXISTS as data (`CriterionTarget` with `role`, `depends_on`, `correlation_group`; content-addressed contracts in `services/assessment_contracts.py`; migration 050 capability residual + identifiability) — MISSING as a *health report* (W1) |
| D. Learner-state transition graph | does A facilitate/transfer to B, at what lag, in what context | **NEW** — `TransitionHypothesis` (§7, W4) |
| E. Intervention layer | which action moves which latent state, vs. what comparator, on what horizon | PARTIALLY EXISTS — randomization layer U-024 logs seed + true propensity pre-selection (`services/randomization_layer.py`, migration 098); MISSING lightweight intervention contracts (§7) |
| F. Domain-mechanism graph | causal claims *inside the subject* (insulin→glucose) | OUT OF SCOPE here; belongs to source ingestion (§8); never an edge in the learner model |

Causal variables live at **facet × capability**, not at concepts or LOs.
That substrate exists: canonical facet state (migration 037) + capability
ledger, surfaced via `services/capability_grid.py`; depth is the separate
rung axis (`services/depth_rungs.py`), deliberately not a difficulty scalar.

---

## 4. Verified inventory (what the roadmap can lean on)

Confirmed present, 2026-07-21:

- `ConceptEdge` with exactly the four semantic kinds; sidecar geometry uses
  `prerequisite|related|part_of`, treats `confusable_with` as adversarial
  neighbors (`learnloop_sidecar` knowledge_map).
- Blueprint recipes: `all_of` / `any_of` / `integration: RecipeComponent`,
  four requirement modalities. Flat `evidence_facets` is derived, never the
  source of readiness math.
- Immutable content-addressed assessment contracts freezing item/rubric,
  criterion maxima, dependency DAG, correlation groups.
- Grading pipeline records per-criterion evidence
  (`ValidatedCriterionEvidence`, `criterion_facet_weights`); error taxonomy;
  first-error localization (`services/probe_blocks.py`
  `first_error_step_or_claim`, `localize_error` tutor move); misconception
  promotion gated on first-error trace confidence ≥ 0.9.
- EIG/EVSI probe selection (`services/predictive_eig.py`, `services/evsi.py`,
  probe_targeting / staged_policy / selection_rewards).
- Randomization layer logging seed + true propensity before selection so
  off-policy IPS/DR joins stay valid; experimental unit = commitment;
  experimental vs. hypothesis grade labels (migration 098).
- Append-only event log + projections ("rows never mutate",
  `db/repositories.py`); versioned vault YAML with schema_version + content
  hashes.
- v-next north star already commits to the loop: measure → diagnose → teach
  → **verify the boundary moved on cold reassessment**; corrigibility
  principle: diagnoses inspectable and contestable, learner counter-explanation
  is bounded-trust evidence (`spec_new_improvements_v2.md` §1, "Corrigibility
  over confidence").
- Graph editor direction-resolution cards with attempt-ordering stats
  (success on B-items before vs. after first success on A-items) —
  `services/graph_edit_proposals.py`, ordering stat in `db/repositories.py`.

Implication: of the original analysis's P0 list, "experiment
instrumentation" is shipped, "measurement graph" is shipped-as-data, and
"relationship ontology" is two-thirds shipped. The roadmap below reflects
that.

---

## 5. Product principles (UX constraints)

- **Label every relationship.** An edge surface states kind, mechanism,
  applicability, what it does *not* imply, and its evidence — never a bare
  `A ──0.73──> B`. (Matuschak: prefer labeled associations.)
- **The graph answers learner questions**, it is not a graph-management app.
  Default verbs: *Why am I stuck? What does this unlock? What should I test
  next? What would have fixed my answer?* The full inspector is an advanced
  surface.
- **Learner stays in the loop.** "That's not why I failed / I lost track of
  notation / the item was ambiguous / I used a different valid method" are
  bounded evidence, per the existing corrigibility principle.
- **Two distinct downstream views, never blended:** structural unlocks
  ("used in 6 recipes") is deterministic curriculum structure; estimated
  causal unlock ("improving this now is predicted to help X") depends on
  current learner state — practicing an already-strong prerequisite has
  little marginal causal value regardless of structural importance.
- **Choose probes by expected decision value, not curiosity.** If every
  hypothesis implies the same next action, don't spend learner time
  distinguishing them. (Extends existing EIG/EVSI direction.)

---

## 6. Workstreams, in order

### W0 — Associational honesty in the direction card (hours)

The direction-resolution card's before/after-first-success stat is useful
descriptive evidence but currently reads as directional support. Relabel:

```text
Temporal association
  Success on B increased after first success on A.
Causal confidence
  Low — A is normally taught first; item difficulty drifted; the
  scheduler selects A when B is weak (selection bias).
Possible explanations
  A facilitated B · both improved with practice · easier B items
  appeared later · scheduler selection
Action
  Test direction with a matched contrast (W4).
```

Touch: `graph_edit_proposals.py` notice payload + card copy. No schema
change. Low-stakes today (no live readiness consumer) but prevents the
worst failure mode: temporal stats hardening into causal beliefs.

### W1 — Measurement-health report (days)

The highest-ROI item: a causal model on weak measurements just gives weak
measurements a more authoritative-looking graph. Mostly *queries over
existing tables* (criterion targets, roles, `depends_on`,
`correlation_group`, migration-050 residuals, item surface metadata).

Per facet × capability, report:

- independent indicator count; distinct surface families; distinct
  representations
- clean primary criteria vs. criteria with major cross-loading
- downstream-contamination exposure (criterion sits after a `depends_on`
  step that often fails)
- negative controls: does the suspected misconception ever get tested where
  it should *not* apply?
- direct vs. only-indirect evidence; grader-reliability flag

Emit warnings (cue dependence, representation dependence, cross-loading,
no-clean-negative-control, no-direct-indicator, item confounding via
alternate recipe). Surface in the maintenance feed alongside existing
notices. This also produces the **contrast-set completeness** view per
facet/misconception: positives, negatives, boundary cases, non-applicable
controls, confusables, representation changes, application + production
tasks. Authoring principle: a facet is identified by chosen contrasts, not
by many homogeneous items.

Acceptance: for one real vault (probability or linear algebra), the report
flags at least the known-weak facets, and every warning links to the items
that triggered it.

### W2 — Vertical slice: causal bottleneck card + natural counterfactual repair (the main event)

Scope to ONE composite task family (e.g. "solve and interpret an
eigenvector equation") with explicit latent components: algebra execution,
matrix-order reasoning, eigenvector semantics, method selection,
integration.

Pieces (leaning on existing machinery everywhere possible):

1. Criterion→facet×capability loadings: already expressible via
   `CriterionTarget`; audit/complete them for the family.
2. First-error localization: exists (`probe_blocks`); reuse.
3. 3–5 named failure hypotheses per family (coordination failure,
   matrix-order misconception, semantics gap, method-selection gap,
   item/grading artifact) with per-hypothesis likelihood sketches — LLM +
   ontology, honestly presented (§1).
4. Matched-probe generator: one short contrast that best *distinguishes*
   the top hypotheses (decision-value rule from §5).
5. Natural counterfactual repair: "smallest plausible change to your
   reasoning that would have produced the correct result" — change the
   earliest wrong decision, preserve the learner's later valid work, render
   your-path vs. minimal-corrected-path side by side with the first
   divergent step marked. Pure LLM + rendering feature; **no new schema**.
   This is the most immediately-felt learner value in the whole spec.
6. Intervention menu with contracts-lite (§7): contrastive example, worked
   example completion, conceptual visualization, isolated prerequisite
   review, integration reconstruction.
7. Outcome logging at the **next spaced cold review** (unfamiliar surface,
   no source), not end-of-session — hooks into existing cold-reassessment
   direction and the randomization layer's commitment-level unit.
8. A causal receipt after the decision (what we believed, why, what would
   change our mind, what remains unverified).
9. Contestability verbs on the card: *Test this explanation / Show the
   evidence / Offer my own explanation / Mark item ambiguous / Different
   intervention.*

Card sketch:

```text
Likely cause
  Coordination failure between basis-change meaning and
  multiplication order.
Why LearnLoop thinks this
  Both component operations demonstrated separately; first
  divergence at choosing which side receives Q⁻¹.
Best next action
  Reconstruct one matched change-of-basis example (~3 min).
Alternative explanation
  Matrix-order misconception — test it first? (~2 min)
```

Post-repair honesty: "intervention improved guided performance; cold
transfer to a new matrix/notation remains unverified; next check tomorrow."

### W3 — Synthetic learner suite (co-requisite of W2, not after it)

At n=1 with no ground truth, simulation is the *only* way to validate the
diagnosis policy (precedent: the sim-sweep that exposed inert scheduler
weights). Synthetic learners defined by: latent states with initial levels,
a measurement model (items → parent states + slip/grader-confusion/fatigue
nuisance), intervention effects with true sizes, moderators.

Evaluate whether the W2 policy: identifies the true bottleneck;
distinguishes measurement failure from knowledge failure; avoids blaming
every prerequisite after a composite failure; picks the intervention with
the highest true *delayed* effect; stops probing when hypotheses converge
on one action; stays calibrated under grader error.

Include adversarial cases: A,B correlate only via shared practice-time; A
always taught first but causally inert; A helps immediate-B but not
delayed-B; A helps only symbolically; B-practice improves A (reversed
direction); unobserved integration factor faking A→B.

Acceptance: W2 ships only with a sim scorecard over these cases.

### W4 — Transition hypotheses + causal source assertions

Only after W2/W3 prove the slice. Adds the row-5/6 entities (§7), the
**Test this relationship** flow (clean A task → matched B task → targeted A
intervention → delayed unfamiliar B task, with the four-outcome
interpretation grid), and ingestion-side causal assertions (§8).

---

## 7. Data model (minimal, deferral-honest)

New vault-side typed entities — NOT fields on `ConceptEdge`:

```python
class TransitionHypothesis:
    cause: FacetCapabilityRef
    effect: FacetCapabilityRef
    kind: Literal[
        "facilitates_acquisition",   # row 5
        "positive_transfer",         # row 6
        "negative_transfer",
        "interference",
        "coordination_dependency",
    ]
    lag: str                          # e.g. "24-72h"
    applicability: str                # context predicate, prose-first
    mechanism: str                    # required — no unlabeled edges
    direction_status: Literal["directed", "direction_unresolved",
                              "equivalence_class"]
    structural_status: Literal["source_claimed", "expert_reviewed",
                               "learner_proposed"]
    falsification_signatures: list[str]
    source_refs: list[SourceRef]
```

```python
class InterventionContractLite:
    activity_pattern_id: str
    target_states: list[FacetCapabilityRef]
    comparator: str                   # "vs. source review", never vs. nothing
    proximal_outcome: str
    cold_outcome: str                 # the one that counts
    outcome_horizon: str              # "next spaced cold review"
    eligibility: str
```

Rides on the existing randomization layer (propensities, commitment unit)
— no new experiment infrastructure.

Estimand discipline without estimation machinery: effects are described as
full estimands ("one completion-style worked example, vs. source review, on
an unfamiliar constructed-response item 24–72h later, for method-selection
gaps in intro linear algebra"), never as `worked_example → mastery +0.2`.
But we store the estimand *string* and an evidence grade — not a posterior.

**Explicitly deferred** (§9): `CausalEffectEstimate` with
posterior_mean/intervals/method enums; `MeasurementLoading` as a separate
entity (CriterionTarget already carries loadings; W1 reports over it).

Placement: semantic contracts (TransitionHypothesis) in versioned vault
YAML with content hashes, like existing entities; dynamic evidence in
SQLite projections over append-only events, like everything else.

### Evidence lifecycle (truncated to what n=1 can reach)

```text
source_claimed → expert_reviewed → observationally_consistent(this learner)
              → contrast_supported(within-learner randomized contrast)
```

plus terminal/annotation states: `contested`, `context_specific`,
`direction_unresolved`, `unsupported`, `retired`. A source claim and a
randomized contrast are different *kinds* of evidence, not two values on a
numeric scale; receipts always show them separately. The original
analysis's "randomized pooled support" and "hierarchical personalized"
rungs are removed — there is no population to pool.

---

## 8. Ingestion: causal assertions in SourceUnitInventory (with W4)

The canonical-source layering (source → interpretation → curriculum →
learning; lower layers never silently rewrite higher ones) is already the
right containment. Extend inventory with three assertion kinds:

- `domain_causal_claims` — mechanisms inside the subject (layer F), with
  conditions, mechanism, span_ids. These are things to *learn*, never
  edges in the learner model.
- `learning_dependency_hints` — "this explanation assumes composition
  order" → candidate `TransitionHypothesis(structural_status=
  "source_claimed")`, surfaced for review, never auto-promoted.
- `counterfactual_cases` — worked contrasts in the source (changed
  variable, predicted difference, spans) — direct fuel for W2's repair
  rendering.

Interpretation layer preserves disagreement ("Source A says necessary;
Source B treats it as presentation order; Source C bypasses it") without
reconciliation; curriculum layer resolves per-recipe; learner evidence
never rewrites source claims and source claims never masquerade as
learner evidence.

---

## 9. Deferred (P2+), with the reason attached

| Item | Why deferred |
|---|---|
| RLCD-style residual missing-factor proposals | Population-scale assumptions absent at n=1; ship later as an *offline audit* generating reviewable proposals ("possible missing integration factor; validation: 1 bridge problem + 1 teach-back + 1 non-applicable control"), labeled as LLM pattern-matching over migration-050 residuals — 5 unexplained composite failures are equally consistent with fatigue/item defects/grader error |
| Environment-matched probe batteries (notation/representation/modality/ timed/tooling contrasts) | Right idea (multi-environment invariance separates notation-mapping vs. representation-transfer vs. method-selection vs. scaffold-dependence vs. core gap); needs W1 surface-family metadata first; fold the cheap version into W2's matched-probe generator |
| Intervention-response profiles ("worked examples: strong acquisition, weak delayed transfer unless followed by construction") | Requires accumulated contrast data; conditional on domain/state/representation/horizon; start as authored priors only |
| `CausalEffectEstimate` + DR/hierarchical estimation | No data regime to fill it; revisit only if multi-learner ever happens |
| Causal policy learning | Only after randomized support and W1-healthy measurements |
| Automated falsification sweeps | After W4 hypotheses exist in volume |

---

## 10. Anti-goals (things this spec commits to NOT claiming)

- No "the algorithm discovered the learner's true causal graph."
- No numeric strength on unlabeled edges, anywhere in UX.
- No certification via propagation (invariant 2).
- No causal language on temporal-ordering stats (W0).
- No pretending LLM hypothesis scores are identified posteriors.
- No auto-orientation of deterministic/logical relations as causal.
- No pooled-population evidence grades while there is one learner.

---

## 11. Open questions for review

1. W2 task family: eigenvector equation (matches the running example) or a
   family from the probability vault (more real usage data)?
2. Does the bottleneck card live inside the existing run-workspace attempt
   flow, or as a post-attempt sheet? (Touches the interactive run
   workspace shipped July 20.)
3. `TransitionHypothesis` as new vault file type vs. extension of the
   existing relations file with new `relation_type` values gated behind a
   schema_version bump? (Spec leans new file type — keeps `ConceptEdge`
   untouched per §1 — but the writer/hash plumbing cost is real.)
4. Counterfactual-repair rendering: text-only side-by-side first, or
   invest in the animated first-divergence visualization immediately?
5. Should W1's warnings block anything (e.g., causal claims about a facet
   with `measurement_health: weak`), or stay advisory in the maintenance
   feed for now?
6. Sim harness: extend the existing sim-sweep infrastructure or a separate
   synthetic-learner suite under `tests/`?

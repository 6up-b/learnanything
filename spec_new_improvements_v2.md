# LearnLoop v-next: layered improvement plan (living document)

**Status:** draft, actively evolving. This document is the working synthesis of
`spec_new_improvements.md` (brainstorm + three agent runs) and design discussion.
Edit freely; record reversals in the change log at the bottom.

---

## 1. North star

LearnLoop is not a scheduler of flashcards. It:

1. runs small experiments to infer the structure of the learner's current world
   model (measure),
2. finds the nearest consequential boundary in that model (diagnose),
3. selects experiences expected to move that boundary (teach),
4. and later verifies the boundary actually moved (cold reassessment).

The learner enters through jobs ("learn this", "fix this", "use this", "return
to this"), not through implementation nouns (vaults, facets, LOs).

**Product thesis:** LearnLoop is a learner-owned system for directing
recurring attention around things a person cares about. It measures only when
measurement changes the next action, supplies experiences suited to the
reason for difficulty, and later verifies performance on cold, unfamiliar
tasks.

**Two nested loops.** `measure → diagnose → teach → verify` is the
*controller's* loop, never the learner's. The experiential loop is
**notice → commit → reconnect → deepen → apply/reflect**, with the controller
adapting beneath it. This is framing and UI, not a new machinery layer — but
it binds the UI: surfaces speak the learner's loop; the controller's loop is
inspectable, not ambient.

**Primary success metric:** delayed performance on unseen goal-relevant tasks
per learner-minute — guarded by false-certification rate, probe calibration,
intervention regret, review burden, retirement/affect signals, commitment
survival, and first-weeks retention. Optimize durable usefulness, never
activity volume.

**Document status labels.** This file is the architecture umbrella; entries
are one of: **invariant** (architectural commitment), **hypothesis** (product
bet, falsifiable), or **provisional policy** (numeric default awaiting
calibration). Every numeric constant in spec or code carries a calibration
status: `heuristic` | `simulation_validated` | `live_calibrated` — the
defaults in `config.py` currently violate this and get labeled during P0.
Implementation splits into per-phase specs at drafting time (§8a).

**Ownership ledger (spec governance, D7).** Umbrella commitments carry stable
lineage+revision IDs (`U-NNN@vK`, append-only — see
`spec_ownership_ledger.md`). Each phase spec pins the revisions it implements
and names what it defers; a per-phase lint checks claims against the *pinned*
revision (semantic successors re-enter triage, editorial ones never
invalidate pins), and a global head-delta report of unowned semantic
revisions must be empty or explicitly parked before implementation of any
phase begins. A phase spec may drop an umbrella commitment only by naming it
in its deferral block.

### Standing principles (carried from existing design + brainstorm)

- **Evidence, not mastery.** Certification derives from the observation ledger,
  never from model confidence. Prediction models (EKF) are calibration
  residuals only.
- **Functional friction vs clerical friction.** The interpretive acts —
  deciding what an idea means to you, formulating a question, judging what is
  worth keeping — are where encoding happens; keep them in the learner's hands.
  Everything mechanical (facet mapping, weights, rubrics, provenance,
  scheduling) is LearnLoop's job.
- **Deletion is healthy model maintenance,** not failure. Retiring an
  instrument never deletes learner state, facet evidence, source
  relationships, or goals.
- **Corrigibility over confidence.** Any diagnosis the system makes must be
  inspectable and contestable by the learner, and the learner's counter-
  explanation is evidence (bounded trust), not noise.
- **No uncalibrated knobs — two tiers.** Sim-sweep found existing scheduler
  weights inert. Tier 1 (mechanism): every new selection signal, threshold, or
  weight ships with a planted-learner simulation demonstrating it changes
  decisions, correctly. Tier 2 (authority): simulation proves a mechanism
  reacts, not that its numbers match real learners — decision policies earn
  live authority only via **held-out real outcomes** (the `intent_planner.py`
  discipline: shadow-only until held-out gains). Amendment: shadow logs
  against a deterministic incumbent support **predictive calibration** claims
  only — counterfactual outcomes are unobserved, so **policy efficacy** ("the
  other action would have taught better") additionally requires a causal
  design — one **randomization layer** (U-024): micro-randomized reversible,
  near-equivalent decisions plus ε tie-breaking within the feasible set,
  propensities logged; proximal outcomes defined at the **next spaced cold
  review**, never end-of-session, where desirable difficulties invert the
  ranking for exactly the interventions worth testing; **commitment-level
  parallel randomization** preferred for durable interventions (at n=1 the
  experimental unit is the commitment, not time); explicit carryover models
  otherwise, or the claim stays hypothesis-grade; or opt-in pooled
  experiments. Predictive components (retrievability, expected success,
  expected duration) earn authority separately via prequential held-out
  scoring — the scored selector decomposes into promotable predictors feeding
  a transparent decision rule; monolithic action-chooser promotion is
  deferred indefinitely at n=1 (U-025). Intervention regret is not observable
  from deterministic logs alone. **Registry lifecycle (U-022):** parameters
  are `active` (tunable, decision-claimed, shipped with a sensitivity
  certificate showing where in the plausible range decisions flip), `dormant`
  (frozen at default, excluded from tuning and decision claims, retained as a
  guardrail **with bind-event logging** — an unmonitored guardrail is dead
  code), or `deleted` (only after coverage demonstrates semantic redundancy).
  The rule is class-asymmetric: inert *shaping weights* are deletion
  candidates; inert *constraint parameters* default to
  dormant-with-monitoring — the sim-sweep found weights inert while
  membership and caps did the work.
- **Learner-authorized depth, not a difficulty treadmill.** Reaching any stated
  milestone remains success. The learner chooses `hold_at_target`,
  `suggest_next`, or `auto_within_envelope` and confirms a visible, versioned
  multidimensional depth envelope. The controller may advance automatically
  only along reviewed, evidence-gated edges inside that envelope. "Too easy"
  alone never expands it; a step outside it is an invitation requiring explicit
  confirmation.
- **Silent caps are lies.** Anything bounded (probe budget, candidate counts,
  synthesis scope) is surfaced, not hidden.

---

## 2. Architecture: three planes, two unifications

### The planes

| Plane | Contents | Status |
|---|---|---|
| **Knowledge** — source assertions + reviewed domain model | sources, revisions, spans/blocks, **source assertions** (span-cited, per-source), facets, LOs, blueprint recipes `(facet, capability, modality)`. "Canonical" = reviewed, versioned reconciliation — alternate formulations and conflicts are preserved, never erased | mostly exists; source-assertion layer new |
| **Learner** — what is true of this learner | **practice commitments** (new — see below), facet×capability evidence grid, attempts/exposure ledger, **hypothesis cards + posteriors** (L4), **annotations** (L3), **boundary view** (L2) | half exists |
| **Activity** — what to do next | **activity families** minting instances (L1), staged-policy **controller** (shadow-scored) | exists for probes only |

### The durable learner object: the commitment *(invariant)*

The thing the learner cares about must exist independently of its prompts
(Matuschak's central insight, made structural). Named **commitment** — not
"practice commitment"; it covers one-time delayed tests, reference-only
dispositions, projects, assessment, and instruction, and "practice" would
leak assumptions into schema and UX. Hierarchy:

```
Commitment
├── learner intent, purpose, depth policy + envelope, goal link,
│   personal interpretation
├── knowledge targets (source assertions · canonical facets/LOs · annotations)
└── activity families (diagnostic · instructional · practice · assessment)
    └── card (stable contract)  →  surface  →  administration  →  observation
```

Vocabulary kept sharp: a **goal** describes desired terminal performance and
constraints; a **commitment** records what the learner cares about, why, and
how much attention it deserves; a **facet** is an assessable semantic atom; a
**card** is a stable executable contract; a **surface** is one concrete
presentation; an **administration** records presentation conditions; an
**observation** records what happened.

A commitment might be "understand eigenvectors," "be good at tasks like
exercise 6.3," a poem, or a technique. Cards and surfaces retire freely
without deleting intent, annotations, evidence, or the connection to the
underlying thing. Commitments are created by **commit-class actions only**
(help-me-remember, test-me-later, exercise selection, quest creation) — never
by mere highlighting. Commitment-level dispositions (stop testing /
reference-only / reduce depth / pause-until-project-returns) are distinct
from activity-level retirement (L0).

### Depth is a learner-authorized program, not a scalar *(invariant)*

Each ongoing commitment has an immutable, append-only **DepthPolicyVersion**:
`hold_at_target`, `suggest_next`, or `auto_within_envelope`, plus a confirmed
**DepthEnvelopeVersion**. The envelope is expressed over the same task contract
the system can inspect: allowed capabilities and target support; maximum
complexity, span, and transfer; permitted representation/response transitions;
scaffold fade; tool/open-book/time conditions; and a cumulative burden ceiling.
The coarse presets in §6.7 create understandable starting envelopes; they are
not the authoritative state.

Automatic escalation follows an ordered, reviewed depth-milestone graph.
**Edge authoring is two-level, like all authoring in this system:** the owner
curates a small set of reusable edge *templates* per domain/pattern (what a
legitimate deeper step looks like structurally); **LLMs author concrete edge
instances** from those templates as part of blueprint synthesis — friction
reduction, not a review bypass. Instances are admitted by **deterministic
gates** (well-formed successor contract, delta strictly inside the envelope,
defined exit gate, fresh-proof route, admitted activity path, leakage checks),
never by model judgment. For inside-envelope edges, the confirmed envelope
*is* the learner's review, amortized; per-edge learner confirmation is
reserved for `suggest_next` renders and outside-envelope invitations. An edge
generator whose instances repeatedly produce non-positive-value transitions or
negative affect is demoted to `suggest_next`.

**Auto-depth ships as one package with its dead-man switch, or not at all**
*(D8, U-018)*. Deferred together: LLM edge-instance generation from
templates, `auto_within_envelope` activation authority, and the
affect-downgrade *enforcement point* (U-011/U-016). Live from the first cut:
curated edge instances, `suggest_next` rendering, the envelope objects
themselves (P1 — they are the review-amortization substrate), and full
commitment-level affect-tap semantics (pause / retire / burden edits) — which
generate and calibrate the very signal stream the package's dead-man switch
depends on. Deferring signal capture until auto mode shipped would mean
shipping automation guarded by an untested kill switch.

A transition is eligible only after its predecessor's exit evidence is
satisfied, the next edge is wholly inside the active envelope, an admitted
activity path and fresh proof route exist, and robust value remains positive
under the burden budget. One decision commits at most one edge and then
replans; there is no recursive eager climb. The receipt records the envelope
version, milestone edge, evidence, target-contract head, burden, and rejected
alternatives.

Depth never mutates a card or erases success. A material task/capability change
forks a new card lineage with an evidence-informed prior but no inherited FSRS
stability or certification. If the terminal support changes, P0 appends an
`authorized_depth_step` goal-contract successor and any deeper certification
uses a new fresh assessment reserve. The earlier milestone and certification
remain true for the exact version demonstrated. `depth_milestone_reached` is
separate from commitment disposition, so an ongoing auto-deepening commitment
can record success without calling the prior target unfinished. Pausing,
shrinking, or disabling the envelope affects the next uncommitted decision;
crossing it always requires learner confirmation. **Affect bounds quality
where the burden ceiling bounds quantity:** repeated negative affect
(`felt rote`, `not worth my attention`) on a commitment's families
auto-downgrades `auto_within_envelope` to `suggest_next` pending
re-confirmation — automation must not keep climbing merely because the
learner is too polite to pause it.

### Events are authoritative; all state is a projection *(invariant)*

The observation ledger is the source of truth. Scheduling state, readiness,
hypothesis posteriors, familiarity, certification, and the boundary view are
all reproducible projections under a **named algorithm version** (the
existing 037 projection already works this way — extend the pattern, don't
break it). Assessment-contract snapshots extend into three artifacts:
`card_contract_hash` (semantic target, response contract, rubric semantics,
task regime), `surface_hash` (exact wording, parameters, media), and the
**administration snapshot** (fully resolved artifact + context + policy
versions). Corrections and regrades **append superseding events, never mutate
old observations**.

### Keystone unification A — shared substrate, purpose-typed families, no role transitions *(resolved, see §9 D1)*

Families are minted for distinct purposes and never transition between roles.
**Four immutable authoring purposes:**

- **Diagnostic** — discriminate learner states. Attached to hypothesis cards /
  episode targets. Surfaces are **single-use**: once attempted, burned —
  retained for replay/audit ("Why this diagnosis?"), never re-administered,
  never recycled into practice.
- **Instructional** — change learner state. Worked-example study, alternative
  explanations, comparisons, completions. **May have a formative outcome
  (completion steps have right/wrong answers) but never produces unassisted
  certification credit** — failure means scaffolding or explanation is still
  needed: log exposure and path, no lapse, no certification.
- **Practice** — strengthen or generalize. Expected-success targets are
  stage-specific, not universal: completion tasks may target very high
  success; independent repair ~70–85%; nothing applies to instructional or
  diagnostic work. Instances re-presentable per card-level scheduling.
- **Assessment** — estimate terminal performance. Held-out, leakage-protected
  (`practice_leakage.py` / `exam_profile.py` machinery), sampled from the
  goal's frozen target task distribution even when predicted success is low.
  **Transfer/assessment surfaces are consumable** (Matuschak's "boss fight"):
  non-fungible by definition — success burns the surface permanently; failure
  *cools* it (long-delay requeue, betting on forgetting). A boss fight is the
  natural capstone of an unfolding arc or level. Third lifecycle alongside
  diagnostic (single-use-forever) and practice (lazy rotation).

**Administration context is recorded independently of purpose:** cold,
scaffolded, hinted, feedback-exposed, timed, tools-available, collaborative.
"Cold" is defined relative to the goal's terminal contract (open-book analysis
may legitimately include the book) — it means *without unintended learning
cues*, not universally closed-book.

**Purpose-specific failure semantics** *(invariant — a universal "incorrect
response" pipeline corrupts both scheduling and evidence)*: diagnostic
failure = information about hypotheses (updates only the committed episode;
burns the surface); instructional failure = scaffolding still needed
(exposure/path only); practice failure = a learning event conditioned on
expected difficulty and context (cautious scheduling + evidence update);
assessment failure = terminal performance not demonstrated (evidence
recorded; feedback burns pristine status).

**Cards generalize beyond assessment shape.** The card contract is a generic
**ActivityContract**: cognitive operation (retrieve / discriminate / generate
/ compare / explain / set-up / apply / reflect / create), outcome schema
(binary / ordinal / continuous / artifact / self-report), completion
semantics, feedback policy, evidence eligibility, context/tool contract,
duration + burden estimate. AssessmentContract is a restricted subtype.
*(Artifact and self-report schemas are post-P2 scope.)*

**Two additional invariants:**
- **No opportunistic diagnostic evidence.** A cold practice review may
  contribute facet evidence, but it must **not** update a diagnostic episode
  posterior unless it was selected and committed as an instrument against
  that episode's frozen hypothesis set — otherwise ordinary reviews get
  reinterpreted as diagnostic evidence, invalidating selection assumptions.
- **Assessment burn on feedback.** Once feedback is revealed, a failed
  assessment surface is no longer held out: it may cool and return as
  *practice*, but it never again mints pristine terminal-assessment credit.
  Fresh assessment requires a fresh surface. (Corrects the earlier
  boss-fight cooling rule, which requeued failures as assessment.)

What they share is the **substrate** underneath (the probe machinery,
`probe_family_templates → instrument_cards → surface-varied instances`,
migrations 028+, generalized): one instance store with the
versioning/immutability-at-presentation contract, one quality-gate +
rubric-minting pipeline, one retirement flow, and — non-negotiably — **one
fingerprint/familiarity ledger**. Both kinds consume the same scarce
resource: unburned surfaces for this learner. Separate ledgers would let
practice minting burn a surface a future cold re-probe needed pristine, and
would double-count evidence across near-clone surfaces.

**Mode is a property of the administration event, not the object.** Ordinary
Today-queue review is already cold-with-full-credit (measure-flavored) on
practice instances. Three administration contexts share the substrate:

- **diagnostic:** EIG-selected, cold, single-use instrument, updates
  hypothesis posteriors;
- **cold review:** schedule-selected, cold, full evidence weight;
- **scaffolded repair:** gradient-selected, adaptive, evidence caveated
  (scaffolding recorded, reduced/no unassisted-demonstration credit).

Cross-purpose linkage is **family-level only**: a diagnostic family that
localizes a gap points to `candidate_practice_families`; the probe itself is
never one of the practice items. A hand-authored PI is a **pinned instance**
of a practice family (see L3 authoring path).

**Authoring-time contract (diagnostic side): cards ahead-of-time and gated;
surfaces just-in-time and constrained.**

- The **instrument card** (discriminative structure, per-hypothesis outcome
  distributions, rubric template, surface-variation bounds) is the expensive,
  reusable, validated object. Cards are authored off the hot path — at
  synthesis time (from confusables/known misconception structure), or at L4
  expansion time between episodes — and must pass identifiability +
  likelihood-sensitivity gates before use. Never invent cards mid-block:
  a JIT card is an instrument with unvalidated psychometrics driving a
  posterior update, and mutates the model class mid-measurement.
- The **surface instance** is minted just-in-time at episode open /
  prefetched during the prior attempt: conditioned on the episode (parameter
  collision avoidance, transfer-distance knobs, fatigue budget), constrained
  within card-declared bounds so the outcome distribution EIG ranked against
  still holds. Single-use; burned on administration.
- **Calibration accrues at the card level:** every spent surface is an
  outcome datapoint for its card — the only path from LLM-elicited to
  observed likelihoods. Single-use-forever is conservative (familiarity
  decays) but re-administration machinery costs more than fresh minting;
  keep the clean rule.
- **One JIT-card exception:** Journey 8 — learner contests a diagnosis and a
  discriminating probe is wanted immediately. Author the instrument marked
  `provisional` and temper the evidence it produces (same bounded-trust
  treatment as the learner-supplied hypothesis itself).

**Card/surface on the practice side.** The same split: a **practice card**
(knowledge target, assessment contract, rubric template, FSRS state) with
rotating **surfaces**. FSRS and evidence attach to the card, never the
surface. "PI" dissolves into practice card + surface.

- **Minting: anchored isomorphs at schedule time, warmth-triggered.** When a
  due card's current surface is warm (recency-weighted exposure over
  threshold), the Today-queue build (async, off the hot path) mints a small
  candidate batch **anchored on the existing surface**, gates comparatively
  (rank difficulty, reject outliers, card rubric must fit each candidate
  verbatim), keeps one, caches a spare. **Never prompt for absolute
  difficulty** — anchor + invariants + comparative judgment only. Cards
  retired before going warm never pay a rotation token. Parametric template
  generators: optional zero-token optimization for high-volume quantitative
  cards, not required machinery (anchored isomorphs subsume them).
- **Lazy cadence:** a surface serves ~2–3 administrations across growing
  intervals before rotation. Early same-surface reps are consolidation;
  script-replay risk grows with rep count.
- **Rubric-forced derivations do not obviate rotation.** A memorized
  derivation *trace* passes the rubric — executed-procedure and
  replayed-script produce identical artifacts, and replayed scripts feel
  maximally fluent. Changing parameters is the cheapest discriminator.
- **Practice vs proof.** Re-serving a familiar surface is allowed
  (consolidation is real learning), but familiarity-discounted toward zero
  evidence. Fresh-surface demonstrations mint certification-relevant
  evidence; familiar-surface reps are practice. Evidence-not-mastery, at
  surface granularity.
- **Surface policy per card:** `rotating` (default: procedural, short-answer,
  discrimination) | `fixed` (verbatim targets where the surface *is* the
  content; learner-pinned surfaces — sibling cards carry the transfer check;
  long-form explanation cards, where memorizing the explanation is itself
  elaborative and rubrics grade content, not wording).
- **Sim admission gate:** planted-learner sims with surface-difficulty jitter
  at plausible σ decide whether a rotation policy's noise flips scheduling or
  certification decisions (no-uncalibrated-knobs).

**Three kinds of state, never conflated:**

- **Target readiness** — learner state per commitment × facet × capability /
  task regime. FSRS is the trace model for stable literal-recall contracts;
  variable conceptual/complex-skill families graduate to a readiness/survival
  model conditioned on task features (post-MVP). Performance on one rotating
  surface is never interpreted as retention of every sibling.
- **Card psychometrics** — difficulty, discrimination, validity, rubric
  calibration. Accrues across that card's surfaces.
- **Surface familiarity** — recency, exact-script exposure, kinship, burn
  state. Global namespace across all families.

**Card lineage.** A durable `card_lineage_id` separate from immutable card
versions. Scheduling state **survives** surface-preserving edits (wording,
formatting, parameter pool, equivalent diagrams, generator bug fixes, minor
rubric clarification); it **forks** when the contract changes (different
facet/capability, materially different response contract, major
difficulty/depth change, open-book↔closed, component→whole-task, changed
rubric semantics) — accumulated stability must not transfer to a harder skill.

**Post-lapse and retry policy** (Matuschak's Orbit data — empirical, not
theoretical): lapsed cards are re-reviewed the **next day** *(provisional
policy, from his data — not an architectural constant)*; post-lapse expansion
factors **contract**; **retry outcomes are retrievability signal** —
same-session retries are *linked observations in a lapse episode* that may
change the derived retrievability estimate but never mutate the original
attempt (events-authoritative, §2). Retries don't penalize until "give up"
(Execute Program). Cue-masking warning: high in-context accuracy can mask
forgetting (QC data) — more empirical backing for familiarity discounting.
Material type (conceptual vs declarative) enters as a **hierarchical
covariate** in scheduling fits, not separate sparse per-user fits.

**Surface mint gates** (every generated surface, all purposes): contract
equivalence, solvability, rubric applicability, leakage, novelty
(fingerprint), task-feature conformance, difficulty range. "Rotate after ~2–3
administrations" is a *provisional policy* — persist exposure data and let
measured replay/familiarity risk eventually set rotation.

**Implementation gaps this layer must close (verified):** the "global"
familiarity path currently scopes to same-LO attempts and compares
`surface_family` (`recall_coverage.py:274`); `surface_group_id` returns the
first nonempty fingerprint field, un-namespaced
(`canonical_projection.py:54`) → implement permanent exact-exposure events,
namespaced hard correlation groups, and a separate composite soft-kinship
kernel. The attempt path updates item-level FSRS without consulting activity
purpose (`attempts.py:1455`), and content changes preserve all FSRS state
indiscriminately (`state_sync.py:35`, an acknowledged MVP placeholder) →
card lineage + state-survival rules land **before** surfaces rotate.

**The pattern language** *(invariant — the "higher-level language" from
Matuschak's ACT-R note, formalized)*: an **ActivityPattern** is a curated,
calibrated instructional protocol — allowed purposes, cognitive operation,
applicable target types, surface variation axes, expected outcome schema,
feedback strategies, evidence semantics. `ActivityFamily = commitment target
× activity pattern × progression policy`. **LLMs render bounded surfaces from
patterns; they never invent the instructional protocol per generation** (the
practice-side twin of "cards gated, surfaces JIT"). The small structural
formats, move-spotting, cue-direction reversal, near-confusable comparison,
flawed-explanation repair, etc. are pattern instances in the registry.

**Angle coverage, not just variation.** Families maintain an explicit **angle
inventory** (cue direction, response form, representation, cognitive
operation, context, task scale, transfer distance, scaffolding degree) —
multi-angle encoding is a *coverage* problem, not unlimited generation.
Rules: cosmetic paraphrase = same card lineage; a genuinely different
cognitive angle = sibling card / family branch; success propagates to related
angles only through a strongly-shrunk correlation model; failure raises
commitment-level uncertainty without resetting siblings; the next activity is
normally a **delayed orthogonal angle**, never a near-clone while the answer
is in working memory; **context deliberately fades** (acquire in the original
narrative → later probe with altered/stripped context → restore source after
the cold attempt — the answer to QC's cue-masking).

**Rigor-pack addition — move-spotting families:** when a proof/derivation
attempt fails on a missed *move* (a method-selection miss), the family mints
analogous-move problems in different contexts until the learner reliably
notices when the move applies. Companion capture type: **negative knowledge**
("what didn't work and why") as commitment content.

**One administration updates three systems differently:** scheduling (was the
trace retrieved? a hinted attempt may shorten the interval), evidence ledger
(what did this demonstrate, under what assistance/familiarity — the same
hinted attempt earns little or no cold credit), and surface familiarity
(this wording is now warm). Scheduling and certification serve different
purposes; divergence is correct, not contradictory. Ambiguous, misgraded, or
out-of-band surfaces are **quarantined** and don't materially update card
state. Cross-card effects flow only through shared facet/capability evidence,
temporary familiarity suppression of near siblings, and the family's stage
estimate — never by pretending siblings were reviewed. Rule: **surfaces vary;
cards remain semantically stable; families grow** (a card never mutates from
recall into transfer — the family mints a successor card with an
evidence-informed prior but no inherited certification).

### Keystone unification B — one two-level controller *(decision pending, §9 D2)*

Today three selectors exist (Today-queue scheduler, probe EIG, repair
sequencing) — and the live scheduler is already a weighted sum with hand-set
gains (`scheduler.py:645`, `selection_rewards.py:260`), which the sim-sweep
found inert. **Do not ship another weighted sum and call it a controller.**
The live controller is a **transparent staged policy** (a constrained state
machine); the scored selector runs in **shadow mode** until it beats the
state machine on held-out real outcomes (tier-2 authority, §1). The eventual
common currency for all modes: *expected goal-weighted delayed unseen
performance gained or preserved per minute.*

The staged policy:

```
if uncertainty changes what we would do next:   measure  (robust EVSI > cost)
elif target knowledge not yet acquired:         instruct (example / explain)
elif capability fragile / scaffold-dependent:   practice (completion → repair)
elif components present but whole task fails:   practice (integration)
elif terminal performance not yet shown cold:   assess   (unseen target-like)
elif auto-depth edge is authorized and valuable:
                                                practice (depth_progression)
elif retention approaching its limit:           maintain
else:                                           stop, or propose an envelope change
```

**Failure-reason triage gates entry to diagnosis** (Matuschak: "choice of
intervention must depend on reason for failure"). Most failures don't need an
EIG episode — a cheap post-attempt classification routes them first: pure
memory lapse → answer + next-day review; conceptual hole → explanation /
elaboration; procedural failure → usually when/where/why (method selection),
not the procedure; explicit false belief or ambiguous cause → *now* open a
diagnostic episode. Protects probe budget; prevents over-diagnosis.

**Canonical live action taxonomy:** `measure_diagnostic · instruct · practice
· assess_terminal · maintain · expand_model · stop`. Repair and integration
and depth progression are practice *subtypes*, not competing top-level modes.

**Constraints are constraints, not reward terms.** Same-facet dispersion,
held-out protection, fatigue limits, learner intent/depth envelope, and
interleaving determine the **feasible set**; scores rank only within it. Hard
rules never get traded off inside a weighted sum.

**Decision costs run on a constrained hierarchy** *(2026-07-17, U-023)*:
(1) correctness, safety, and learner-intent constraints define the feasible
set; (2) among feasible actions, minimize **expected wasted learner-minutes**
— time spent on an ineffective intervention plus delay to the effective one.
Minutes are the cost numéraire, so `λ_time ≡ 1` and burden is measured (from
logged attempt durations), not weighted; the EVSI loss table `L(h,a)` becomes
*derivable* from triage-route structure and activity duration estimates
rather than elicited. (3) Non-time harms stay ordinal and enter only through
defined entry points — constraint thresholds (e.g. a misgrade-risk ceiling
per certification claim), a dominance filter, or a documented tie-break order
— never as informal weights; "kept qualitative" is where weights hide.
Route-table entries carry their expected-minutes derivation and constraint
set as registered, inspectable objects under the same sensitivity machinery
as any constant. The learner's burden budget remains the one genuinely free
parameter, and it is learner-authored.

**Session planning is two-level:** first choose a coherent 5–15 minute
**attention block** (a commitment neighborhood + intent), then select
activities within it under spacing/familiarity/fatigue/goal constraints.
Per-item value-per-minute ignores context-switching and session-start
overhead; the block is the unit the learner experiences (and the codebase's
session intents already point this way).

Mode taxonomy for the shadow-scored selector:

| Mode | When it wins | Within-mode value function |
|---|---|---|
| **measure** | uncertainty about the learner blocks a decision | expected information gain |
| **teach** | boundary known; move it | expected boundary movement toward goal-weighted frontier cells |
| **maintain** | decay pressure | FSRS / decay |
| **expand** | open-set mass says model class is wrong | expansion value (L4) |
| **stop** | marginal value < cost (time, fatigue, burden) | — |

Symmetry: EIG = expected information *about* learner state; learning gradient =
expected *movement of* learner state toward goal frontier. Both computed from
the same family metadata. Quests (L5) enter as weights on which frontier cells
matter. **No MCTS**: six macro-actions and a 1–2 block horizon is a scored
one-step lookahead. MCTS is future work only if the myopic controller
measurably leaves value on the table.

**Within measure contexts, selection is greedy and one-step** (adaptive
elicitation, arXiv:2504.04204), with the objective chosen by what the episode
is for — all **burden-normalized** (`score = value / (expected seconds +
burden)`; the codebase already runs predictive-EIG-per-expected-second as the
default, `probe_families.py` policy `probe_episode_v2`):

- **Robust EVSI preferred when hypotheses map to different repairs** —
  expected reduction in downstream decision loss, not raw entropy: raw EIG
  values distinctions even when every surviving hypothesis implies the same
  intervention. The staged policy's enumerable actions are what make the loss
  function computable.
- **Hypothesis EIG** where naming the distinction matters for inspectability
  (Journey 8 needs named, contestable hypotheses).
- **Predictive EIG** for coverage assessments — cold-start baseline (Journey
  1), hiatus re-entry (Journey 11), exam readiness — computed against a
  **frozen goal-conditioned target distribution** (required capabilities,
  task complexity, transfer distances, representations, source/exam weights,
  unseen surface groups), *not* the first eligible instruments in ID order
  (fixes `probe_episodes.py:449`).
- **Robustness rule:** rank by expected value or a conservative bound across
  plausible likelihood matrices; if the winner flips under small credible
  perturbations, abstain or author a stronger instrument.
- **Ranking vs stopping are different formulas.** Per-second normalization is
  for *ranking* only; the *stop* rule is net value:
  `LCB(EVSI(q)) ≤ λ_time·t_q + C_burden` → stop (`λ_time ≡ 1` under the
  minutes numéraire, U-023). The observation model is
  explicitly H → Z → G (learner state → true response class → grader
  classification), updated through the calibrated grader channel (L0).
- "Two to four probes" is a visible cap and initial heuristic *(provisional
  policy)*, not a quota.

Two deltas from the paper: (1) its greedy guarantee assumes a meta-trained
predictive simulator close to the real response distribution — LearnLoop
substitutes hand-authored/prompted likelihoods, so greedy selection is a
heuristic, not a theorem; meta-training is the upgrade path once the §8
corpus matures. (2) The paper has no stop rule or cost model — the staged
policy supplies it (stop when no candidate has positive robust value, all
plausible states imply the same action, fatigue caps hit, or the episode
needs open-set expansion). Pure information value never goes negative, so an
EIG loop alone never chooses to teach.

### The jagged boundary is a view, not a table

"Can compute λI / cannot interpret (A−λI)v=0 as Av=λv" is the frontier surface
through `facet_capability_evidence` (migration 037): which cells are
demonstrated, dark, decayed, or contested by an active hypothesis. No new
storage; a read-model + UI (L2).

---

## 3. Layer 0 — Trust the measurements *(foundation; first)*

The entire diagnostic edifice updates posteriors from **LLM-graded open-ended
answers**. A misgrade doesn't cost one item; it corrupts the posterior and
sends the episode down the wrong branch. Nothing downstream is trustworthy
until this is.

**Scope:**
- **Asymmetric grader confusion channels.** Model H (learner state) → Z (true
  response class) → G (observed grade) explicitly. The current channel is a
  fixed symmetric reliability (0.90/0.80, `probe_families.py:56`); real
  grading error is asymmetric (partial-success↔success confusions dominate).
  Calibrate confusion models per grader version × rubric type × domain ×
  response length. Store raw grade, calibrated distribution over Z,
  calibration-model version, adjudications. High-influence or low-confidence
  responses get a second grade or a learner clarification.
- **Reliability flows everywhere evidence flows.** Three verified gaps: the
  probe submission path obtains likelihoods without per-attempt grader
  confidence (`probe_episodes.py:1418`); canonical certification projection
  computes evidence mass without consuming grader reliability
  (`canonical_projection.py:265`); and its ledger query doesn't even select
  `grader_confidence` (`repositories.py:3153`). All fixed before open-world
  diagnosis gets more authority.
- **Authority before calibration exists: bounded heuristic authority, not a
  block.** *(invariant)* The calibration label **is a prior width, not a
  permission flag**: `heuristic` channels enter the hierarchical model with
  wide credible intervals, and since consequential decisions already use
  robust LCB rules, heuristic authority bounds itself — probes whose ranking
  flips under perturbation abstain, episodes stop earlier ("couldn't reliably
  distinguish" is an honest outcome), the action-relevance gate does more
  work, and certification needs more independent demonstrations because
  discounted reliability yields less evidence mass per observation. Authority
  expands *continuously* as calibration narrows intervals; no blocked→allowed
  cliff. Rationale: (1) hard-blocking deadlocks — anchor data comes from live
  use (adjudication queue, prospective predictions), so blocking starves the
  pipeline that would unblock it; (2) events-authoritative replay means
  certifications are projections that self-correct when the grader model
  upgrades — wrong provisional conclusions are recoverable by design;
  (3) blocking kills the P2 golden path's ability to teach us anything
  (reduce automation before reducing the experience). One carve-out, phrasing
  not function: under `heuristic` channels the system never asserts
  diagnoses or readiness as fact — best-supported hypotheses with named
  alternatives, calibration label visible on every claim.
- **Authority-grade calibration sources** (self-calibration from own
  posteriors is exploratory EM only): human/adjudicated anchor responses;
  planted-learner sims (mechanism validation); precommitted prospective
  predictions on held-out probes; independent confirmation before instruction
  changes the learner; grader rechecks + learner clarification; prequential
  log-loss/Brier scoring under the policy that actually selected the probe.
  Every constant gets a status label: `heuristic` | `simulation_validated` |
  `live_calibrated` (§1) — starting with the defaults in `config.py`.
- **Three calibration streams, never conflated** *(2026-07-17,
  U-020/U-021)*: the `misgraded`/`ambiguous` affect tap is **error intake** —
  missing-not-at-random by construction (conspicuous errors get reported;
  ordinary correct grades are never confirmed), so it discovers failure modes
  and feeds adjudication but never supplies a calibration denominator. The
  **calibration stream** is stratified random adjudication with logged
  inclusion probabilities: oversample low-confidence, high-influence, and
  partial-credit-boundary attempts, reweight by inverse probability for
  unbiased confusion estimates — influence prioritization is the
  stratification design, not a separate stream. **Structured learner
  corrections** are authority-grade individual anchors. Bootstrap: one
  retrospective owner-adjudication session over a stratified sample of the
  existing attempt history, sampling frame logged so it composes with the
  ongoing stream. **Abstention budget:** "diagnostician abstains ≤ X% of
  episodes" is a registered, monitored parameter — sims choose prior
  concentrations to meet it, and live abstention above budget raises an
  alarm instead of surfacing as ambient timidity.
- **Likelihoods are weak priors, not point truth.** The ordinal vocabulary's
  fixed numbers (0.60/0.25/0.10, pseudo-count 8, `probe_families.py:28`)
  become a hierarchical model: family-level prior → card residual →
  surface/task-feature residual → grader channel, with uncertainty intervals.
  Self-calibration from the model's own posteriors (`probe_families.py:1624`)
  is EM-style exploration only — authority-grade calibration needs audited
  anchor episodes, prospective confirmation, or held-out evaluation. P0 adds
  a perturbation axis over the hand-authored `P(Z|H)` tables to the robust
  ensemble; that is **robustness analysis, not calibration** — it does not
  discharge this commitment. The hierarchical model itself is deferred with a
  named resume path: card-level outcome counts (logged per spent surface) are
  its training data, and events-authoritative replay makes the upgrade
  retroactive (U-014).
- **Grader calibration harness.** Extend the planted-learner sim to misgrade
  scenarios: does episode conclusion flip under plausible grading error? Audit
  loop: does grader confidence predict agreement with human/owner spot checks?
- **Coarse outcome spaces.** Probe outcomes are
  `success / signature-error / other` (3–4 outcomes), not fine distributions —
  less to elicit, less to be wrong about.
- **Retirement as first-class maintenance** (independent, ships immediately).
  Retirement record with reason taxonomy: too easy, ambiguous, missing
  context, duplicate surface, wrong granularity, no longer relevant, bad
  underlying explanation, superseded by better activity, "should be reference
  not memorized", "I don't care enough to retain this". Architecture already
  guarantees evidence survival (facet-level evidence, immutable ledger) — this
  layer is the record, the replacement-proposal hook, and UX that *shows* the
  evidence surviving. Feedback affordance: "I knew the prompt, not the
  concept."

- **Affect tap — typed validity constraints, not a reward function.** One
  optional touch on any activity, with signal-specific semantics: `cue gave
  it away` → substantial certification-evidence discount; `ambiguous /
  misgraded` → quarantine the surface, latest projection reversible;
  repeated `felt rote` → retire or redesign the *family* (not just lower
  priority); `not worth my attention` → edits the commitment/burden contract,
  never interpreted as low ability; `meaningful connection` / `wanted more
  depth` → salience + depth-preset signals. Emotional signals are the
  *leading* indicator of abandonment; they gate validity and learner intent —
  never optimize them as a reward. Never required, never interrupts.

**Acceptance:** Journey 12 (repair/retire a bad prompt). Sim: planted misgrade
does not silently flip a diagnosis.

---

## 4. Layer 1 — Activity Family substrate

**Scope:**
- Generalize probe minting machinery into the shared instance substrate with
  **purpose-typed families** (unification A): diagnostic families
  (single-use, discrimination-optimized) and practice families
  (re-presentable, gradient-optimized) over one instance store and one
  familiarity ledger. Family = generator scoped to recipe components + depth
  coverage; instance = immutable administered artifact with rubric minted and
  quality-gated at instance-mint time (never at presentation).
- **Capability stays closed; task features are a separate vector.**
  *(Corrects an earlier claim: the capability vocabulary is a closed
  five-value set — retrieval / schema_interpretation / procedure_execution /
  method_selection / coordination, `models.py:414` — and
  `RecipeComponent.modality` means requirement strength
  (hard/path_specific/facilitating/instructional_order, `models.py:233`),
  not task conditions.)* Cognitive complexity, transfer distance,
  representation, response form, scaffolding/cue availability, time pressure,
  and tools live as a structured **task-feature vector on cards and
  surfaces** — consumed by the familiarity/transfer kernel, the frozen
  predictive-target distribution, and goal-anchored selection. The "depth
  ladder" survives as a *policy trajectory* through capability × task-feature
  space, not an enum. Domain rigor packs (proof reconstruction, assumption
  perturbation, ablation interpretation, decreasing-measure) are family
  generators over that space, not new machinery.
- **Small structural activity formats** (fills the gap between full-effort
  desk tasks and rote recall; the natural inventory for short/mobile
  sessions):
  - **`setup_only`** — set up the problem, don't solve it (write the
    integral, form the equation, choose the method). Isolates the
    method-selection capability with the highest signal-per-second of any
    format; the native activity for the three-minute session (L5).
  - **`example_comparison`** — two worked examples side by side, "what is
    structurally common?" (analogical encoding; Gentner). The
    schema-formation activity for the acquisition rung (§8b.1) — repeated
    solving and single-example study both fail to induce schemas. Surface
    pairs come free from the isomorph machinery: two surfaces of one card
    *are* a structure-mapping exercise.
  - **`example_completion`** — complete the missing step of a worked example
    (§8b.1).
- **Span as a family-generator parameter** (chunk-growth ladder, orthogonal
  to the depth ladder): same capability, growing coordinated span — proof
  step → lemma → whole argument; line → function → algorithm; couplet →
  stanza. The graded path up to whole-proof reconstruction, which otherwise
  exists only as a summit. Depth varies *what kind* of thinking; span varies
  *how much is coordinated at once*.
- **Familiarity discounting:** extend `EvidenceFingerprint` from binary dedup
  to kinship distance within a family; discount evidence mass accordingly.
  **Family-level evidence caps** so minting variants cannot inflate
  certification.
- **Coordination without a conjunction ledger** *(D3 resolved — dissolved)*:
  no facet×facet evidence dimension. Coordination is served by (a) an
  **integration component** on blueprints — a whole-task capability whose
  evidence can only come from whole-task cards (synthesis lint: multi-
  component LOs must include one), and (b) **hypothesis cards** naming the
  specific broken link when diagnosis finds it. A standing pairwise ledger is
  quadratic, hopelessly sparse for one learner, and its cells duplicate what
  cards say better. Time-pressure/load is a **task-feature** on cards/surfaces
  (not a `modality` value — that field means requirement strength).
- Pre-mint instances ahead of sessions (latency); generation quality gates
  reuse §8.7-style gates.

**Acceptance:** Journey 6 (recall→transfer progression); a family emits
retrieve→teach instances over time with familiarity-discounted evidence;
sim shows variant-minting cannot certify a goal by itself.

---

## 5. Layer 2 — The boundary made visible

Mostly rendering over existing data; disproportionate product payoff — this
*is* the differentiated identity.

**Scope:**
- **Jagged boundary view / capability profile** per LO-neighborhood:
  demonstrated / developing / untested / weak / contested cells; visible
  learning arc (retrieve → explain → distinguish → vary → apply → coordinate →
  teach/create). **Framed as relationship, never deficit** (§1 nested loops):
  the view leads with *what do I care about here, how has my relationship
  deepened, what can I now do, what worthwhile direction is next* — gaps are
  available directions, not a red dashboard of deficiencies.
- **"Why this diagnosis?"** — render locked hypothesis set, probes used,
  per-response evidence contributions, surviving alternatives, grader
  assumptions. (Episodes already log all of this; rendering problem.)
- Post-attempt **cold-then-restore contract**: cold attempt first, then
  restoration of source neighborhood including the learner's own annotations
  (once L3 exists) and the originating tutor exchange (provenance-linked,
  hidden during cold attempt).

**Acceptance:** journeys 5/6 (recurring-error diagnosis, recall-to-transfer);
learner-facing outcome statements ("the missing link was X; you demonstrated
it on a new example").

---

## 6. Layer 3 — The peritextual reader: reading-first ingest

**The reader is the front door, not a capture widget.** Inversion of the
ingest flow: today it's batch (pick source → select scope → synthesize map →
practice). Reading-first means the learner opens the source and starts
reading; the learner's *behavior* — questions asked, spans highlighted,
confusions marked, "help me remember this" — progressively steers extraction,
inventory, and proposed study structure in the background.

### 6.1 Demand-paged synthesis

Synthesis is already sharded per source unit. Reading-first ingest = running
inventory/synthesis shards **on demand** for the neighborhood being read,
prioritized by reading signals, instead of (or in addition to) eager
whole-scope synthesis. Both entries remain first-class:

- **"Build me a path"** — existing batch study-map flow, unchanged.
- **"I'm reading"** — background per-unit inventory of the current
  neighborhood; proposals accumulate quietly and are reviewed as exceptions,
  never as modal interruptions to reading.

### 6.2 Reading modes → product surface

- **skim:** first pass produces unit inventory (claims, terms, figures) +
  learner's own flagged questions; cheap, mostly background.
- **anchor reading:** deep processing of one important section — full action
  palette, annotations, authoring.
- **incremental reading:** spans marked confusing/valuable flow into the
  maintenance feed for resurfacing; refine-or-release on each revisit. (The
  cheap 80% of SuperMemo IR; no separate reading queue system.)
- **syntopic view:** deferred (see §10). The multi-source facet attachment
  underneath already exists; the comparison UI is v2.

### 6.3 Action palette = three primitives

Nine actions, three mechanisms (UI shows three — Ask, Practice, Mark — with
presets underneath):
1. **Ask-with-preset** (existing tutor + span context): Ask / worked example /
   alternative explanation / why does this matter. Exchange retained as
   provenance, hidden during cold attempts.
2. **Commit** (creates/extends a practice commitment via quick_add), with
   distinct semantics: **test me later** = one delayed cold check, not
   permanent review; **help me remember** = ongoing commitment; **connect it**
   = learner-authored proposed relationship — never a silent canonical graph
   edge.
3. **Disposition** (annotation state): **mark confusing** seeds a question /
   provisional hypothesis (never evidence of inability); **not worth
   remembering** suppresses future proposals for this learner (never deletes
   the source assertion).

All record span-anchored **annotations** (new persistence; today only passive
`source_exposure_events` exist).

**Capture contract:** the selection and the learner's text are saved locally
*before* any AI call; capture is acknowledged immediately; background
synthesis never blocks it. Demand-paged jobs are idempotent, keyed by (source
revision, span/window, action, schema, model version), with visible caps and
token use; only the necessary neighborhood is sent to the model.

### 6.4 Annotation schema

Anchor = block locator **plus sub-block selector**: local character offsets,
exact selected quote, prefix/suffix context, page geometry where available,
and reanchoring status — a block ID alone preserves the neighborhood but
cannot recover the exact highlighted phrase after re-extraction. Content =
type (highlight / question / confusion / interpretation / disposition) + free
text + optional **"what I think is going on"** field.
That field is the **learner-supplied hypothesis seed** consumed by L4's
expansion pipeline with bounded trust — the reader is a hypothesis-discovery
channel. Annotations are preserved verbatim (personal voice matters), mapped
to canonical facets without being replaced by them, and restored after cold
attempts (L2 contract).

### 6.5 Reading signals as salience priors

"Which parts are already understood and which facts are most salient" — the
brainstorm's core algorithmic ask — is fed by reading behavior:

- **Salience:** highlights, questions, dwell, re-visits → priority weights on
  which facets get families generated at all, proposal ordering, and coverage
  depth (lightly-encoded microvolumes vs shored-up areas).
- **Prior knowledge:** skim-past-familiar, "not worth remembering",
  self-reported "I already know this" → weak priors for measure mode (cheap
  hypotheses to confirm with one cold probe, not assumed).
- **Hard rule: salience signals are missing-not-at-random and are never
  learner evidence.** Dwell, skipping, and highlights inform proposal
  priority only — certification never.
- These signals are logged to the ledger as first-class events (→ §8 corpus).
- **Reading creates captures and proposals — never automatic knowledge
  objects.** Annotations and commitments materialize immediately; canonical
  mappings are proposals; new facets/LOs only when existing objects genuinely
  cannot represent the target; cards only once purpose and contract are
  clear. The graph must not become a transcript of everything clicked.
  **Source objects** (generalizing source assertions — span-cited,
  per-source, with authorial role and salience) become the durable layer
  between unit inventories and canonical facets. Types: claim/definition,
  **procedure, worked example, problem, proof move, motif/passage, artifact**
  — proposition-only ingestion can't represent what the exemplar-driven MVP
  practices (problems and examples are first-class). Synthesized facets stay
  *proposed* until accepted; claim-cluster relations
  (supports/contradicts/refines/alternate-definition/unresolved) give the
  deferred syntopic view its data model now. **Authorship provenance is
  stored and displayed** — author-authored / learner-authored /
  expert-curated / AI-rendered; an AI-generated question must never
  impersonate the author's editorial intent ("this is important").
- **Active-learning episodes as sources** *(post-MVP class, architecturally
  cheap)*: the learner's own problem-solving artifacts — failed attempts,
  debugging traces, diffs, notebook derivations, corrected explanations,
  proof decision points — ingest as sources; practice then targets
  recognition and selection ("why did this approach fail?", "what clue
  suggested method X?", "compare the failed and successful paths"). Pairs
  with negative-knowledge capture (L1) and Journey 8.

### 6.6 The learner authoring path (formulation as learning)

Writing the question/answer **is** the encoding act; LearnLoop must never
automate it away — it automates everything around it.

- **Flow:** learner writes Q + A (optionally from a span). LearnLoop fills in
  all machinery: facet mapping (link or propose-new), evidence weights,
  capability/modality assignment, grading rubric, fingerprint, source span
  links, family attachment. One confirmation; `quick_add` is the transport.
- **Authored PI = pinned instance** of a family. The learner's surface is
  preserved and scheduled as written; the family around it can still mint
  siblings (measure-mode transfer checks that the learner *didn't* author —
  which is exactly what tests them beyond their own wording).
- **Formulation coach — a scale, not a gate.** Novice: scaffolded prompts
  (what is the atomic claim? what would prove understanding rather than
  wording-recognition? what mistake would reveal a shallow model? produce or
  discriminate? worth long-term review?). **Middle rung — starter templates**:
  a partial prompt for the selected passage that the learner adapts and
  completes — the interpretive act without the blank page. Expert: freeform
  with post-hoc lint (ambiguity, duplicate surface via fingerprint,
  granularity, missing context). Coaching is **non-blocking**: it never
  prevents acceptance; it's lint, not grading.
- **Fluid maintenance from within review** (reader-agency requirement): while
  reviewing, the learner can edit wording, refactor one-to-many / merge
  many-to-one (with lineage), or spawn a new prompt without leaving the
  session — maintenance verbs must be available in the moment of irritation.
  Ownership framing throughout: the collection is *yours*, AI/author
  provenance is an affordance, never a separate untouchable place.
- **Exhaust is expected.** Early learner-authored cards are often exhaust from
  forming an understanding. Track `learner_authored` provenance; expect higher
  retirement churn; the retirement flow (L0) frames the cull as the
  understanding having matured, not the card having failed.
- Authoring telemetry (edits to AI-proposed candidates, coach-prompt
  responses, later survival) feeds the corpus (§8) — this is where a future
  taste model would learn from, but no learned policy now.

### 6.7 Unfolding arcs and priming

- **A capture schedules a plan, not an item.** When the learner captures an
  insight (§6.3/§6.6), LearnLoop lays out a short **visible arc** — e.g.
  retrieve in 2 days, explain in a week, apply in two — that the scheduler
  honors (subject to dispersion, §8b.2). Mostly presentation of existing
  machinery (family + ladder + scheduler), but it changes the capture
  contract from "we made you a flashcard" to "this idea will unfold over the
  next two weeks" — the emotional promise that distinguishes the system, made
  visible at the moment of capture.
- **Arcs run on two clocks.** Memory time (decay, retrievability, readiness)
  and **arc time** (intended progression: comprehend → complete → retrieve →
  discriminate → integrate → transfer → revisit from a new perspective). An
  arc is a versioned program/state machine over the family's patterns, not a
  set of due dates; arc transitions are gated by evidence, paced by memory
  time, and never hard-gate reading (§8b.7).
- **Depth presets** — the learner sets coarse depth per section or
  commitment: `keep in touch · remember key ideas · work fluently · master
  tasks like these` — and chooses `hold`, `suggest`, or `auto within this
  envelope` once, instead of approving individual prompts (Matuschak: readers
  prefer choosing depth for passages). A preset expands into a visible
  multidimensional envelope, ordered reviewed milestones, and a burden budget.
  Evidence may advance an arc automatically inside it; the affect tap's
  `wanted_more_depth` advances when already authorized or proposes a versioned
  envelope successor when it is not.
- **Pretest-as-prime.** Questions the learner asked while reading section N
  (already captured as annotations) are replayed as primes before section
  N+1; a cheap pretest before an anchor read serves double duty — priming
  encoding (forward adjunct-question effect, §8b.6) and eliciting
  measure-mode priors from the same interaction. Dual-use evidence is
  tempered like scaffolded work; the measure/teach separation protects
  evidence honesty, not ritual purity.

### 6.8 Capture channels

v1: in-app reader selection + paste + command palette. Browser extension /
share sheet: fast-follow after the capture pipeline proves out.

**Reader format** *(D4 resolved)*: marker-converted markdown (LaTeX via
KaTeX; marker embeds extracted figure images natively). Two hard
requirements:
- **Annotations anchor to block locators, never markdown offsets.** Display
  layer = marker markdown; anchor layer = canonical `source_document_blocks`
  spans, with a markdown↔block crosswalk maintained at extraction time —
  annotations survive marker re-extraction, and "Open in source" works from
  the reader.
- **Per-block extraction-health flags drive fallback.** Fallback = original
  PDF region crop rendered via existing span geometry (not a whole-PDF
  fallback): failed figures and low-confidence equations (marker's weak spot)
  show the crop; every block gets a "view original" affordance. A learner
  never silently studies a mis-OCR'd equation. (Gap: the IR currently models
  health at page level only, `ingest/ir.py:117` — block-level health is new
  work.) Terminology kept honest: the immutable **bytes are authoritative**;
  the extracted IR is a **versioned derived representation** (it can contain
  OCR errors); the converted markdown is a **view**; "canonical" is reserved
  for the reviewed domain model.

**Dependencies:** source layer (exists). Does **not** depend on L1 — capture
can flow through quick_add to ordinary PIs now, upgrading to family-pinned
instances when L1 lands. Can proceed **in parallel with L1**.

**Acceptance:** Journey 2 (quick insight capture: highlight → interpretation →
1–2 accepted activities → **visible unfolding arc** → cold retrieval →
source+annotation restore, under a minute of admin); Journey 1 (first useful
session, reading-first variant); Journey 7 (tutor exchange → durable
knowledge).

---

## 7. Layer 4 — Open-world diagnosis

The probe-EIG expansion design, with simplifications.

**Scope:**
- **Hypothesis cards**, versioned; **immutable hypothesis-set snapshots** per
  episode; successor sets via lineage (central invariant: sets are immutable
  measurement snapshots; the ontology evolves through versioned successors).
- **Simplified governance:** two scopes (LO-local, facet-level), three
  statuses (provisional / active / retired). Domain templates are *authored*
  vault content like confusables, not earned via recurrence machinery.
- **Expansion triggers — model-misspecification driven, not just open-set
  mass:** open-set posterior mass (τ validated in sim; the generic `other`
  row is an **alarm state, not a diagnosis**); low posterior-predictive
  probability / repeated surprise; repeated unexplained error signature
  across independent surfaces; **N repair failures on varied surfaces
  regardless of attributed cause** (don't attribute blame you don't act on
  differently); learner-supplied explanation (from Journey-8 flow *and* reader
  annotations, §6.4); new semantic information; **systematic grader
  disagreement** (persistent grade/confidence mismatch on one signature
  suggests the outcome space, not the learner, is misspecified).
- **Retrieve → generate → validate pipeline** with gates ranked: action
  relevance ≥ identifiability > novelty/falsifiability. Identifiability checks
  run against coarse outcome spaces (L0) with ±0.15 likelihood-perturbation
  sensitivity — fragile probe plans fail admission.
- **Discovery/confirmation separation:** discovery evidence ranks candidates
  and conservatively splits only `other_or_unknown` mass (tempered, small τ);
  cards require prospective confirmation (2 confirmations, 2 independent
  surface groups) before status: active.
- **Bounded episodes:** stop when one hypothesis dominates, remaining
  hypotheses imply the same intervention, next-probe EIG is low, or
  fatigue/cost exceeds discrimination value.
- **Measurement/learning segment separation:** practice closes the diagnostic
  segment; old posterior is a diagnosis of the pre-instruction state; cold
  probes later test whether the boundary moved.
- **Journey 8 disagreement flow:** "Why this diagnosis?" (L2) + "propose
  another explanation" → bounded-trust candidate → discriminating probe →
  revised diagnosis.
- Storage: `hypothesis_cards`, `hypothesis_card_versions`,
  `hypothesis_set_members`, `hypothesis_set_lineage`,
  `hypothesis_authoring_runs`, `hypothesis_discovery_evidence`,
  `hypothesis_validation_results`; typed `OpenSetTransition` from the existing
  `open_set_misconception_review` need (`probe_blocks.py:40`).

**Dependencies:** L0 (grader noise, coarse outcomes), L1 (cards reference
`candidate_practice_families`), L2 (inspectability UI).

**Acceptance:** probe-EIG journeys 1–4, 6, 8 (math/probability/ML-paper/
recursion domains); planted-learner sims incl. misgrade and
likelihood-perturbation scenarios; the eigenvector "rule without equivalence
model" worked example end-to-end.

---

## 8. Layer 5 — Direction

- **Quest = Goal extension**, not a new entity — and the Goal grows a
  **versioned terminal contract** (today it's little beyond facet scope +
  recall threshold + deadline, `models.py:46`): kind (exam / project /
  fluency / understanding), optional due date, free-text **purpose**, target
  exemplars, required capabilities, task complexity + span, transfer-distance
  range, representations + response formats, tool/open-book/time conditions,
  relative task weights, held-out vs practice eligibility, acceptable
  performance + burden bounds. **Freeze semantics — versioned with
  per-consumer pinning, no single global freeze:** exemplar confirmation
  mints v1 (before that it's a draft); every material edit mints an
  append-only successor version, never in-place. A reviewed edge inside a
  learner-confirmed `auto_within_envelope` policy is already authorized and may
  append one `authorized_depth_step`; "too easy" alone and every
  outside-envelope change remain non-pinnable proposals until confirmation. Each
  consumer pins at its own commitment point: **probe episodes** pin the
  contract version at episode open (in the episode snapshot, beside
  hypothesis-set/likelihood/policy versions — mid-episode edits apply next
  episode); **assessment reserves** pin at reservation, and certifications
  cite the version they were demonstrated against — if an edit changes the
  distribution's *support* (exemplars, capabilities, task types,
  administration conditions), the reserve is flagged unrepresentative and
  must be refreshed before terminal claims about the new version; minor
  re-weighting edits keep certifications valid (mirrors card-lineage
  fork-vs-retain rules). Earlier milestone certification remains valid for its
  cited version after any deeper successor. **Practice progression** pins
  nothing and tracks the head version. Purpose threads into synthesis briefs and
  family generation; quest weighting selects which boundary-frontier cells
  matter to the controller (unification B). Project outcomes (implement / write / explain /
  reproduce / analyze / present / perform) recordable as application evidence
  with honest caveats (scaffolded, tools available, not a cold test) + later
  cold transfer probe. The "why" is never shown as a cue during cold attempts.
- **Hiatus re-entry** (Journey 11): a measure-mode episode wearing recovery
  UX. No red backlog count; goal triage; small re-entry assessment sampled
  over high-value concepts, previously demonstrated capabilities, historical
  weaknesses; three groups (retained / recoverable / weak); low-value prompts
  retired or deferred via L0 flow; 7-day re-entry plan. Largely parallelizable
  with earlier layers.
- **Three-minute session** (Journey 10): scheduler already accepts
  minutes/energy (`scheduler.py:40-41,799-811`); this is a home-screen entry +
  "one item is a completed session" framing rule. Ship with the first UI work.
  Its native inventory is the small structural formats from L1 (`setup_only`,
  `example_completion`, `example_comparison`) — short sessions serve
  structurally meaningful work, not leftover flashcards.
- **Journeys home screen** (Continue / Learn / Repair / Apply / Review):
  target information architecture; ship *after* flagship journeys have real
  screens behind them.
- **Data corpus:** event taxonomy logged from L0 onward (highlight+intent →
  candidates → accept/edit/reject → prompt revisions → attempts+error
  patterns → retirement+reason → delayed unseen transfer → self-reported
  authentic use). *(Corrected: this does **not** fit `content_events` — that
  table is a closed, CHECK-constrained content-mutation audit stream,
  migration 036.)* New typed `interaction_events` envelope, alongside the
  specialized high-value tables (scheduler slates, observations). **Log now,
  model later** — no learned taste models until volume exists. Exception: review-burden accounting
  (attempt durations) is computable immediately and feeds stop-mode cost.

**Acceptance:** journeys 8 (project-linked), 10, 11; a quest measurably
re-weights family generation and controller frontier without appearing as a
retrieval cue.

---

## 8a. The MVP vertical slice: "I want to become good at tasks like this"

Rather than drafting layers in sequence, the next MVP cuts **one vertical
slice through all layers**, organized around end-of-chapter exercises as
target exemplars. Core promise:

> Choose the kinds of problems you want to become good at. LearnLoop finds
> your current boundary with the fewest useful questions, gives you practice
> that grows from that boundary toward those problems, and maintains each
> stable ability without teaching you to memorize surfaces.

**The loop:** select exercises → derive a goal-conditioned **task blueprint**
(rubric, solution recipes, required facets/capabilities, task-feature vector,
common errors, "tasks like this" invariants; several exercises = a target
task distribution) → short adaptive probe episode (2–4 questions: top-down —
start with a representative target task, adaptive-group-testing style;
predictive EIG for boundary mapping, hypothesis-EIG/EVSI after a localized
failure) → staged policy teaches/practices the nearest gap → durable cards
scheduled, surfaces rotate → **unseen** target-like cold assessment → source
neighborhood + annotations restored → record the achieved milestone, then
maintain, stop, suggest the next edge, or automatically activate one reviewed
edge inside the confirmed depth envelope. The selected exercise itself is a
familiar anchor for generation and explanation — unseen isomorphs and
held-out items provide the proof. Exam papers follow the same contract:
blueprint-only / practice / genuinely held-out, with solutions feeding
rubrics but never leaking into held-out surfaces.

**Delivery order (P0–P4).** Narrowing principle: **reduce automation before
reducing the end-to-end experience** — manually authored/reviewed families
and surfaces first, prove the learner journey works, then automate generation
and selection.

- **P0 — measurement correctness:** grader confusion distributions,
  reliability propagation into posteriors *and* certification, frozen target
  snapshots, authorized depth-successor semantics, assessment burn rules,
  calibration-status labels on all constants; the three-stream calibration
  design with a retrospective owner-adjudication bootstrap (U-020), the
  abstention budget (U-021), the registry lifecycle (U-022), full affect-tap
  capture (U-010), the retirement record with CLI-level Journey 12 (U-012),
  the `interaction_events` envelope (U-013 — unlogged data is the one
  irreversible loss), and a heuristic `P(Z|H)` robustness axis labeled as
  robustness analysis, not calibration (U-014).
  **Spec of record: `spec_p0_measurement_correctness.md`** (also
  pulls the minimum final activity substrate forward from P1 so burn/lineage
  never land on temporary exam-only tables).
- **P1 — shared substrate:** commitment, purpose-typed family, card
  lineage/version, depth policy/envelope/milestones, surface, administration,
  exposure, observation adapters; the card-psychometrics event-sufficiency
  gate (U-015 — accrual is a deferred projection, so administrations and
  observations must carry card version, outcome, and administration context);
  old PracticeItem + probe histories preserved through compatibility views.
  **Spec of record: `spec_p1_shared_substrate.md`.**
- **P2 — narrow golden path:** one chapter, one exercise family, reviewed
  task blueprints, pre-authored gated probe cards, reason-based repair with a
  specified triage mechanism (U-027: deterministic route table where evidence
  is decisive, otherwise a provisional proposed distribution presented as a
  decision aid with overrides logged as anchors — a registered `heuristic`
  channel), rotating practice surfaces with named pool provenance (U-028: LLM
  drafts within admitted cards, owner review), one fresh held-out assessment,
  and `suggest_next` depth invitations only — automatic activation defers to
  the auto-depth package (D8/U-018). **Spec of record:
  `spec_p2_narrow_golden_path.md`.**
- **P3 — reader integration:** annotations, source assertions, demand-paged
  synthesis, visible depth authorization/arcs, restoration, fluid in-review
  editing. **Spec of record:
  `spec_p3_reader_integration.md`.**
- **P4 — controller and scale:** staged-policy controller under the
  constrained decision-cost hierarchy (U-023); predictive-component promotion
  via prequential scoring — the action chooser stays the staged policy and
  monolithic scorer promotion is deferred (U-025); one randomization layer
  for dispersion/interleaving experiments (U-024); soft-kinship as an
  LLM-judged heuristic feature behind a sim gate, learned weights deferred
  (U-026); depth-envelope constraint enforcement; robust EVSI; open-world
  hypothesis expansion only after all of the above. **Spec of record:
  `spec_p4_controller_and_scale.md`.**

**Slice scope (in):** chapter reader; exercise identification + selection;
blueprint generation + review; goal-conditioned probes; instructional →
completion → practice stages; durable card-level scheduling with rotating
surfaces; cold reassessment + restoration; boundary view; activity and
commitment retirement; evidence-gated automatic depth progression inside a
learner-confirmed envelope.

**Slice scope (out):** syntopic UI; MCTS; learned live controller;
mid-episode hypothesis generation; population-level promotion; unbounded,
cross-family, or outside-envelope automatic escalation; whole-library eager
synthesis.

**Migration:** backfill each existing PracticeItem as a fixed surface under a
one-card family; copy `practice_item_state` into card-level state; keep
materializing generated surfaces as PracticeItem-compatible snapshots so the
attempt/grading pipeline survives; split the content hash into a card
semantic-contract hash + surface hash; preserve old IDs and replay under
existing algorithm versions. New durable objects: `commitments`,
`target_exemplars`, `activity_families`, `practice_cards` (+versions,
+lineage, +state), `activity_surfaces`, `activity_administrations`, shared
fingerprints/exposures, `source_annotations`, `source_assertions`,
`interaction_events`.

## 8b. Evidence-informed policies (Matuschak notes + cited literature)

Adopted from `spec_andymatusnotes.md` review. LearnLoop's architecture is
independently convergent with the "idea-centric memory system" sketch (LO/facet
= the idea; families = activity generation; identifiability gates answer his
chunk-size problem; shared facet state answers his cross-angle scheduling
problem) — these are *policies*, not architecture changes:

1. **Acquisition rung below "retrieve"** (L1 + controller). For
   high-element-interactivity LOs (integration components, many prereq
   facets): teach-mode `example_study` and `example_completion` activity
   types served pre-acquisition, faded to problem solving as boundary
   evidence accrues (worked-example effect + expertise reversal; Sweller &
   Cooper 1985; Ruitenburg 2025). Isolated facts skip straight to retrieval.
2. **Within-session same-facet dispersion** (scheduler; confirmed missing).
   Minimum spacing between same-facet administrations — back-to-back angles
   are answered from working memory (diminished reinforcement) and feel like
   busywork. Families make this failure *more* likely, not less; guard it.
3. **Interleaving** (scheduler; confirmed missing). Mixed-topic session
   composition for transfer-oriented goals (Samani & Pan 2021: markedly
   better delayed transfer). **Stage-dependent:** valuable for discrimination
   and transfer practice; inappropriate during initial worked-example
   acquisition (blocked practice wins there).
4. **Goal-anchored task complexity** (controller / quest weighting). Practice
   rung selected from the goal's target complexity
   (transfer-appropriate processing; Agarwal 2019: factual practice ≈
   no practice for higher-order tests). Lower rungs are diagnostic/remedial
   tools, never a mandatory bottom-up sequence.
5. **Elaborated retrieval default** for conceptual cards: answer-plus-why,
   not bare recall (Pan & Rickard 2018: elaboration moderates transfer).
   Calibration note: rephrased-question effects are modest (d≈0.1–0.2) —
   surface rotation buys honest measurement, not turbocharged learning.
6. **Inline adjunct questions in the reader, opt-in** (L3). High-level
   comprehension checks served during reading (Hamaker 1986; Cerdán 2009 —
   high-level ≫ low-level for transfer), plus cheap pretesting before anchor
   sections. Density default ~1 per 1000–1500 words (Rothkopf / Quantum
   Country practice). Evidence heavily caveated (immediate, primed). Opt-in
   because embedded-prompt knowledge is brittle and interruption risks
   busywork.
7. **Onboarding critical mass + steady stream** (L5 / Journey 1). Habit
   adoption requires the first weeks' collection to outweigh practice
   overhead, and "review sessions become boring and detached without a steady
   stream of new prompts" — reading-first ingest is structurally the steady
   stream, which is a retention argument for L3's priority. Caution (Execute
   Program): efficient review scheduling is in tension with gated sequences —
   arcs sequence *activities*, never hard-gate *reading*.

Two default-emphasis rules: **capture never requires formulation** (authoring
is an invited upgrade, not the main path — transformation-into-prompts is the
documented alienation point); and **retirement offers idea-level actions**
("stop testing this idea", "less depth here") distinct from instrument-level
retirement (L0 taxonomy).

Not adopted: response-congruency machinery (confounded coding; capability
ladder already varies response type); ACT-R-style production modeling (family
generators are the higher-level language); designing around "testing effect
disappears with complexity" (contested — the acquisition rung handles its
defensible core).

## 9. Open decisions

- **D1 — Probe/PI unification (keystone A).** **Resolved 2026-07-16:** shared
  substrate, purpose-typed families, no role transitions. Probes never become
  PIs; diagnostic instances are single-use; probe↔practice linkage is
  family-level only (`candidate_practice_families`). Shared: instance store,
  immutability contract, fingerprint/familiarity ledger (single namespace),
  quality gates + rubric minting, retirement. Not shared: generation
  objectives, selection functions, instance lifecycle.
- **D2 — Controller unification (keystone B).** **Resolved 2026-07-16:**
  greedy one-step EIG (arXiv:2504.04204) for all within-measure selection —
  hypothesis EIG in diagnostic episodes, predictive EIG for
  baseline/re-entry/readiness assessments. The outer mode selector survives
  but shrinks: a thin scored rule whose main jobs are the stop condition
  (max EIG < cost, fatigue, burden — absent from the paper) and the
  measure/teach/maintain choice greedy EIG structurally cannot make. No
  lookahead anywhere.
- **D3 — Conjunction evidence.** **Resolved 2026-07-16: dissolved.** No
  pairwise evidence dimension; integration components on blueprints
  (whole-task evidence only) + hypothesis cards for specific broken links.
  Revisit only if cross-LO coordination discovery becomes a goal (L4+).
- **D4 — Reader v1 format.** **Resolved 2026-07-16:** marker-converted
  markdown with KaTeX; block-locator anchoring for annotations (never
  markdown offsets); extraction-health-driven fallback to PDF region crops
  for figures and suspect equations.
- **D5 — Spec packaging.** **Resolved 2026-07-16:** this file is the
  umbrella; the first implementation spec is the §8a vertical slice
  (exemplar-driven MVP), which cuts through all layers; remaining layer work
  ships as follow-on specs.
- **D6 — Demand-paged synthesis proposal handling.** **Resolved 2026-07-16:**
  proposals accumulate for exception review; nothing is silently applied
  while reading; capture is acknowledged immediately and never blocked by
  synthesis.
- **D7 — Spec governance.** **Resolved 2026-07-17:** version-aware ownership
  ledger (`spec_ownership_ledger.md`): stable lineage+revision IDs
  (`U-NNN@vK`), phase specs pin revisions and claim implements/defers,
  per-phase lint against the *pinned* revision, and a global head-delta
  report of unowned semantic revisions that must be empty or parked before
  any phase implementation. Semantic vs editorial revision classes mirror
  card-lineage fork-vs-survive.
- **D8 — Auto-depth package.** **Resolved 2026-07-17:** automatic depth ships
  as one deferred package — LLM edge-instance generation,
  `auto_within_envelope` activation authority, and the affect-downgrade
  enforcement point — while curated edges, `suggest_next` rendering, envelope
  objects, and full commitment-level affect semantics ship live from the
  first cut, generating the calibrated signal stream the package's dead-man
  switch requires. P2's first cut is `suggest_next`-only.

## 10. Deferred / out of scope (v1)

- Syntopic comparison UI; SuperMemo-style incremental-reading queues (the
  maintenance-feed resurfacing covers the valuable 80%).
- Browser extension / OS share sheet capture (fast-follow).
- Timed language production (voice + latency infra) and VOD journeys
  (self-report-only vision; probes not administrable/gradable by the system).
- Learned taste models / targeting policies (corpus first).
- MCTS planner; five-level card scopes; six-state card lifecycle.
- Cross-learner card promotion machinery (single-learner reality).
- Auto-depth package (U-018): LLM edge-instance generation,
  `auto_within_envelope` activation authority, affect-downgrade enforcement —
  one unit, shipped only after the affect stream has live mileage.
- Hierarchical instrument-likelihood updating (U-014) — resume path:
  card-level outcome counts, retroactive via replay.
- Monolithic action-chooser promotion and learned soft-kinship weights
  (U-025/U-026) — no reachable promotion path at n=1.

## 11. Acceptance-journey map

| Journey (source docs) | Layer |
|---|---|
| J12 retire a bad prompt | L0 |
| J6 recall→transfer; family depth progression | L1 |
| J5 recurring-error diagnosis; capability profile | L2 |
| J2 quick insight capture; J1 first session (reading-first); J7 tutor→durable | L3 |
| Probe-EIG J1–4, J6 (domain episodes); J8 disagreement | L4 |
| J8 project-linked; J10 three-minute; J11 hiatus return | L5 |

Maturity claims from agent docs are re-audited against code before each layer
spec is finalized (e.g., held-out exam pools: primitives exist
(`practice_leakage.py`, `exam_profile.py`), v2 exam-seeding workflow still
open).

## 12. Change log

- **2026-07-17 (p)** — Orphan/n=1 consensus folded in. Governance: ownership
  ledger regime (version-aware `U-NNN@vK` IDs, per-phase pin lint +
  head-delta report, semantic/editorial revision classes —
  `spec_ownership_ledger.md`, D7 resolved). Auto-depth package boundary
  narrowed (D8 resolved: deferred = LLM edge generation +
  `auto_within_envelope` authority + downgrade enforcement; live = curated
  edges, `suggest_next`, envelopes, full affect semantics — the dead-man
  switch needs live signal mileage). L0 gains the three-stream calibration
  design (MNAR error intake / stratified-with-logged-propensities
  calibration / correction anchors, plus retrospective bootstrap over
  existing attempts), the abstention budget, and the registry lifecycle
  (active/dormant/deleted, bind-event logging, weights-vs-constraints
  asymmetry). Tier-2 causal designs replaced with one randomization layer
  (MRT + ε tie-breaking, next-cold-review proximal horizons,
  commitment-level parallel randomization; carryover models else
  hypothesis-grade) plus scorer decomposition (predictive components
  promotable prequentially; monolithic promotion deferred at n=1). Keystone B
  gains the constrained decision-cost hierarchy (minutes as cost numéraire
  within constraints, derivable `L(h,a)`, ordinal harms via defined entry
  points only). Weak-priors commitment split honestly: P0's perturbation
  axis is robustness analysis, not calibration; hierarchy deferred with
  card-count resume path. Orphans placed: retirement + `interaction_events`
  → P0; psychometrics event-sufficiency gate → P1; `suggest_next`-only +
  triage mechanism + pool provenance → P2; adjunct-question deferral → P3;
  §7 promotion rewrite + kernel descope → P4.
- **2026-07-17 (o)** — Depth-edge authoring resolved as two-level: owner
  curates edge templates, LLMs author instances via blueprint synthesis,
  deterministic gates admit (envelope = amortized learner review; per-edge
  confirmation only for `suggest_next`/outside-envelope); misbehaving edge
  generators demote to `suggest_next`. Affect-downgrade rule folded in
  (repeated negative affect downgrades `auto_within_envelope` →
  `suggest_next` pending re-confirmation).
- **2026-07-17 (n)** — Depth escalation promoted into the MVP contract across
  P0–P4 and the probe redesign: versioned `DepthPolicy` + multidimensional
  learner-confirmed `DepthEnvelope`; reviewed milestone graph; one evidence-
  gated automatic edge at a time inside the envelope; append-only target
  successors and fresh reserves when terminal support grows; card-lineage forks
  with no FSRS/certification inheritance; prior milestone success preserved;
  outside-envelope progression remains an explicit proposal.
- **2026-07-16 (m)** — Pre-calibration authority resolved: bounded heuristic
  authority (label = prior width, self-bounding via robust LCB rules;
  continuous expansion as intervals narrow), not a hard block — blocking
  deadlocks the anchor pipeline, replay makes provisional conclusions
  recoverable, and a blocked golden path teaches nothing. Carve-out: no
  declarative diagnosis/readiness claims under heuristic channels (hypothesis
  phrasing + visible labels).
- **2026-07-16 (l)** — Goal-contract freeze semantics resolved: versioned
  from exemplar confirmation with append-only successors; per-consumer
  pinning (episodes at open, assessment reserves at reservation with
  support-change flagging, progression tracks head); minor/major edit
  distinction mirrors card lineage.
- **2026-07-16 (k)** — Experiential-layer review folded in: nested loops
  (learner loop vs controller loop) + anti-deficit boundary framing (§1, L2);
  instructional-purpose fix (formative outcomes allowed, no unassisted
  certification) + purpose-specific failure semantics invariant + generic
  ActivityContract with AssessmentContract subtype (keystone A);
  ActivityPattern language (family = target × pattern × progression; LLMs
  render surfaces, never invent protocols) + angle coverage inventory with
  orthogonal-next and context-fading rules (L1); arcs on two clocks + depth
  presets (§6.7); two-level session planning (keystone B); affect tap
  upgraded to typed validity constraints (L0); source assertions generalized
  to SourceObjects with authorship provenance + active-learning episodes as
  post-MVP source class (L3); tier-2 authority amended with
  predictive-calibration vs policy-efficacy distinction (N-of-1 / randomized
  tie-breaking / logged propensities — OPE machinery deferred as n=1
  overkill).
- **2026-07-16 (j)** — Charter-review revisions (all new code claims
  verified): product thesis + primary success metric + document status labels
  (invariant/hypothesis/provisional; constants labeled
  heuristic/simulation_validated/live_calibrated) added to §1;
  practice_commitment renamed **commitment** with sharp vocabulary;
  events-authoritative/projections invariant + three-hash contract added to
  §2; two new keystone-A invariants (no opportunistic diagnostic evidence;
  assessment burn on feedback — corrects boss-fight cooling); keystone B
  gains canonical action taxonomy, constraints-vs-scores rule, LCB net-value
  stop rule (per-second is ranking only), probe-cap-not-quota; L0 gains
  authority-grade calibration sources + third reliability gap
  (`repositories.py:3153`); L1 gains retry-as-linked-observations, surface
  mint gates, verified familiarity/lineage implementation gaps
  (`recall_coverage.py:274`, `canonical_projection.py:54`,
  `attempts.py:1455`, `state_sync.py:35`); interleaving stage-dependence;
  Goal terminal contract field list; corpus moved off `content_events`
  (closed audit stream, migration 036) to typed `interaction_events`;
  bytes-authoritative/IR-derived terminology; §8a restructured into P0–P4
  with reduce-automation-first narrowing. Declined: splitting into three
  documents now (labels first, split at implementation-spec drafting).
- **2026-07-16 (i)** — Second Matuschak-notes batch (operational Orbit/QC
  findings + reader-agency notes): failure-reason triage gates diagnosis
  (keystone B); consumable "boss fight" transfer surfaces as third lifecycle
  (keystone A); post-lapse/retry policy + material-type schedule
  stratification + move-spotting families + negative-knowledge capture (L1);
  starter-template middle rung + fluid in-review maintenance (L3/L6.6);
  adjunct density default + onboarding critical-mass note with
  no-hard-gating-of-reading caution (§8b).
- **2026-07-16 (h)** — Major revision from the code-grounded agent review (all
  code claims verified): **practice commitment** added as the durable
  learner-plane object; family purposes extended to four (diagnostic /
  instructional / practice / assessment) with administration context recorded
  independently; two factual errors corrected (capability vocabulary is the
  closed five-value set — task features become a separate vector on
  cards/surfaces; `modality` means requirement strength, so time-pressure
  moved out of it); keystone B recast as transparent staged policy + shadow-
  scored selector (tier-2 authority principle added to §1); measure-mode
  selection upgraded to burden-normalized robust EVSI/EIG with frozen
  goal-conditioned predictive targets; L0 gains asymmetric grader confusion
  channels, reliability-consuming certification, hierarchical likelihood
  priors, no-self-calibration rule; L1 gains three-state separation
  (readiness/psychometrics/familiarity), card lineage fork rules,
  hinted-attempt scheduling/evidence split, surface quarantine; L3 gains
  capture contract, sub-block annotation selectors, source-assertion claim
  layer, salience-is-never-evidence rule, commit-action semantics; L4 gains
  misspecification-driven triggers incl. grader disagreement; new §8a MVP
  vertical slice (exemplar-driven) resolves D5; D6 resolved
  (exception-review). Learner-intent-bounds-escalation principle added.
- **2026-07-16 (g)** — Six elicited additions embedded in their layers: affect
  tap (L0); `setup_only`, `example_comparison`, `example_completion` formats +
  span parameter (L1); unfolding arcs + pretest-as-prime as new §6.7 (L3, with
  Journey 2 acceptance updated); three-minute session wired to small formats
  (L5).
- **2026-07-16 (f)** — §8b added from Matuschak-notes review: six
  evidence-informed policies (acquisition rung, same-facet dispersion,
  interleaving, goal-anchored complexity, elaborated retrieval, opt-in
  adjunct questions) + capture-never-requires-formulation and idea-level
  retirement defaults. Dispersion and interleaving confirmed absent from
  scheduler by grep.
- **2026-07-16 (e)** — D2/D3/D4 resolved: greedy one-step EIG per
  arXiv:2504.04204 with per-context objectives (hypothesis vs predictive) and
  a thin outer mode selector for stop/teach decisions; conjunction evidence
  dissolved into blueprint integration components + hypothesis cards; reader
  format = marker markdown with block-locator anchoring and health-driven
  PDF-crop fallback. D6 added (demand-paged proposal handling).
- **2026-07-16 (d)** — Practice-side card/surface policy converged: anchored
  isomorphs minted at schedule time (warmth-triggered, comparatively gated,
  never absolute-difficulty prompts), lazy ~2–3-rep cadence, parametric
  generators demoted to optional optimization, practice-vs-proof evidence
  split (familiar-surface reps discounted toward zero evidence), per-card
  surface policy rotating|fixed.
- **2026-07-16 (c)** — Authoring-time contract added to keystone A: instrument
  cards ahead-of-time and gated (calibration accrues at card level), surface
  instances just-in-time within card-declared bounds, single-use; Journey 8 is
  the sole provisional JIT-card exception.
- **2026-07-16 (b)** — D1 resolved after owner pushback: keystone A softened
  from "one object, one generator" to **shared substrate, purpose-typed
  families, no role transitions**. Diagnostic instruments are single-use and
  never recycled into practice; the single familiarity/fingerprint ledger is
  the non-negotiable shared piece; measure/teach recast as three
  administration contexts (diagnostic / cold review / scaffolded repair).
- **2026-07-16** — Initial synthesis: three planes, two keystone unifications,
  L0 grading foundation, MCTS demoted to future work, journeys re-cast as
  acceptance tests. Layer 3 rewritten as reading-first ingest per owner: the
  reader steers synthesis (demand-paged shards), learner authoring path with
  formulation coach (scaffold scale, non-blocking), authored-PI-as-pinned-
  instance, annotations double as hypothesis seeds, exhaust-and-retirement
  framing.

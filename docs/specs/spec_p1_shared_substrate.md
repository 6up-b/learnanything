# P1 implementation spec: shared activity substrate

**Status:** Draft v0.2, code-audited 2026-07-16; depth contract amended
2026-07-17; orphan/n=1 consensus folded in 2026-07-17 (ownership claims below)
**Parent:** `spec_new_improvements_v2.md` (P1 delivery phase; Layers 1 and the
durable-commitment portion of Layer 2)
**Depends on:** `spec_p0_measurement_correctness.md`
**Acceptance focus:** Journey 6, plus lossless legacy PracticeItem and probe
replay

P1 turns the minimum activity spine created in P0 into the one substrate used
by diagnostic, instructional, practice, and assessment work. It adds the
durable learner commitment, a curated pattern language, explicit capability
and task-feature contracts, card-level scheduling, surface rotation, and one
global exposure/familiarity namespace.

P1 does **not** create replacement activity tables. P0 already creates
`activity_families`, immutable family/card versions, `activity_surfaces`,
`activity_administrations`, `activity_exposure_events`, observations, and
surface-lifecycle events. P1 extends those records and cuts live consumers over
to them. The `interaction_events` corpus envelope is likewise created and
owned by P0 (U-013); P1 writers append to it but do not define it.

**Ownership claims** *(ledger pin: 2026-07-17 seed,
`spec_ownership_ledger.md`; updated 2026-07-18)* — implements: U-015@v2, the
card-psychometrics event-sufficiency gate (accrual itself is a deferred
projection; §1, §9.8); U-035@v1 (`learning_process` pattern metadata, §3.5);
the U-033@v1 substrate hooks (`reading_phase` administration context, §3.10;
tutor-answer exposure propagation, §4.1 — the reader product surface itself
is P2/P3).
Defers: U-016@v2 (edge-template authoring and generator demotion) plus the
`auto_within_envelope` activation authority and the affect-downgrade
enforcement point (U-011@v2) to the auto-depth package (U-018@v1; §1.3,
§3.1.1). Cross-reference: U-013@v2 (`interaction_events`) is owned by P0.

---

## 1. Outcome and boundaries

At P1 exit, every new learner-facing activity resolves through this hierarchy;
pre-P1 items remain reachable through the explicitly labeled legacy ownership
adapter until the learner adopts or retires them:

```text
Commitment
  -> commitment target
  -> purpose-typed ActivityFamily × ActivityPattern version
  -> stable card lineage -> immutable card version
  -> concrete surface
  -> administration
  -> response / grade / observation
```

The same administration produces three intentionally different projections:

1. card scheduling and progression;
2. facet × capability evidence and certification eligibility;
3. global surface familiarity and exposure.

A fourth kind of state — **card psychometrics** (difficulty, discrimination,
rubric calibration) — accrues as a *deferred projection* over these same
administration/observation events (U-015): P1 adds no psychometrics schema,
because events-authoritative replay makes the projection retroactive the day
it is built. The same card-level outcome counts are the named resume path for
the umbrella's deferred hierarchical likelihood model (U-014).

Those projections may disagree. A hinted practice response may shorten the
next interval, earn no unassisted certification credit, and still make the
surface maximally familiar.

### 1.1 Non-negotiable invariants

1. **One substrate.** No probe-only, exam-only, instructional-only, or
   PracticeItem-only presentation path may bypass P0 administrations and
   exposure events.
2. **Purpose is immutable.** A family is authored as `diagnostic`,
   `instructional`, `practice`, or `assessment`. It never transitions to
   another purpose. Cross-purpose reuse creates a separately gated family and
   links the families; it never re-labels a card or surface.
3. **Commitment is independent of prompts.** Retiring every family/card under a
   commitment does not delete the learner's intent, targets, annotations, or
   evidence.
4. **Commitment creation is explicit.** Only commit-class actions create one:
   `help_me_remember`, `test_me_later`, `select_exemplar`, or `create_quest`.
   Highlighting, reading, asking, or being shown a proposal never does.
5. **Events remain authoritative.** Scheduling, familiarity, progression,
   disposition, and current-version heads are named projections. Corrections
   append successor events.
6. **Cards are stable; surfaces vary; families grow.** A surface never owns
   FSRS state. A card never silently changes target, capability, response
   contract, task regime, or rubric semantics.
7. **One familiarity namespace.** All purposes and all learning objects write
   exact exposure, hard-correlation membership, and soft-kinship features to
   the same learner-wide ledger.
8. **No opportunistic diagnosis.** Only an administration committed to a
   diagnostic episode and its frozen hypothesis set may update that episode.
9. **Instruction is not proof.** Instructional outcomes may be right or wrong,
   but never mint unassisted certification credit or a practice lapse.
10. **Coordination is blueprint evidence.** There is no conjunction-evidence
    ledger. Whole-task coordination is an integration component on a task
    blueprint; a suspected broken link is a hypothesis card in P4.
11. **Compatibility is lossless.** Historical IDs, timestamps, algorithm
    versions, grades, probe snapshots, and replay outputs remain addressable.
12. **Depth authorization is explicit and bounded.** Automatic progression may
    activate only one reviewed milestone edge wholly inside the active immutable
    DepthEnvelope. It never mutates a card, inherits FSRS/certification across a
    fork, or treats prior milestone success as failure.

### 1.2 In scope

- durable commitments, immutable versions, targets, depth policies/envelopes/
  milestones, and disposition events;
- the closed five-capability vocabulary and versioned task-feature vector;
- curated `ActivityPattern` registry and the family construction rule;
- card lineage, fork-vs-retain classification, and card-level scheduling;
- fixed and rotating surface policies, anchored isomorph candidate minting,
  comparative gates, cache/pre-mint behavior, and pinned surfaces;
- namespaced hard-correlation groups plus a separate soft-kinship feature
  vector and deterministic P1 familiarity projection;
- angle inventories, context fade, family-level evidence caps, and sibling
  propagation rules;
- purpose-specific administration adapters and post-lapse linked retries;
- PracticeItem, probe, exam, attempt, and FSRS compatibility cutovers;
- inspection/authoring services and acceptance tests.

### 1.3 Explicitly out of scope

- automatic multi-chapter family authoring or the P2 end-to-end journey;
- reader annotations and source objects (P3);
- learned familiarity kernels, controller scoring, robust EVSI, interleaving
  experiments, and open-world expansion (P4);
- a learned readiness/survival model for complex skills; P1 records the
  features required for it but keeps the current evidence projection;
- artifact and self-report outcome schemas beyond compatibility ingestion;
- population card promotion or cross-learner calibration;
- MCTS or any learned live controller;
- a fitted card-psychometrics model; P1 guarantees only event sufficiency for
  a later pure-replay projection (U-015, §9.8);
- LLM edge-instance generation from owner-curated templates, edge-generator
  demotion (U-016), live `auto_within_envelope` activation authority, and the
  affect-downgrade enforcement point (U-011) — deferred together to the
  auto-depth package (U-018). P1 ships the objects that package will consume:
  policy/envelope/milestone versions, curated edges, `suggest_next`, and the
  deterministic one-edge transition service (§5.7).

---

## 2. Verified code-truth ledger

This ledger describes the repository before P0/P1 implementation. P1 work is
complete only when a fresh audit can replace each gap with a concrete landed
path or an intentionally retained compatibility seam.

| Area | Verified reality | P1 consequence |
|---|---|---|
| Practice object | `PracticeItem` contains prompt, answer, rubric, evidence targets, surface family, fingerprints, and practice mode in one YAML object (`vault/models.py:342-373`). | Split semantics across existing P0 card versions and surfaces; retain a PracticeItem materialization only as a compatibility DTO. |
| Scheduling state | `practice_item_state` is keyed by PracticeItem and stores FSRS fields (`migrations/001_initial.sql:204-216`). | Introduce authoritative card-lineage scheduling state and project the legacy row during dual-write. |
| Edit behavior | `sync_vault_state` explicitly preserves all FSRS state across any content-hash change (`state_sync.py:35-39,73-83`). | Replace this placeholder with deterministic minor-successor vs fork classification; ambiguous edits default to fork/review. |
| Attempt side effects | The main attempt path applies FSRS to every item at `attempts.py:1455-1463` without consulting immutable activity purpose. | Route through the administration's purpose-specific adapter before any scheduling write. |
| Probe hierarchy | Migration 028 already has versioned probe-family templates, instrument cards, item links, presentations, observations, and calibration rows. | Adapt these objects into P0 families/cards/surfaces; do not discard the mature diagnostic gates or replay snapshots. |
| Probe minting | `probe_instance_generation.py:929-1083` already supports admitted cards, JIT LLM/parametric surfaces, structural gates, review parking, and provenance. | Generalize the mint/gate interface and keep diagnostic objective/lifecycle distinct. |
| Familiarity query | `familiarity_discount` queries only recent attempts for the same learning object and compares item/surface-family/facet overlap (`recall_coverage.py:274-339`). | Replace authority with global activity exposure; preserve this function only for legacy replay. |
| Hard grouping | `surface_group_id` returns the first non-empty fingerprint field without a namespace (`canonical_projection.py:54-72`). | Store every namespaced hard-group membership; never collapse unrelated identifiers or discard secondary groups. |
| Goal vs commitment | `Goal` is described as a measurable commitment but only holds recall scope, deadline, and exam config (`vault/models.py:46-64`). | Add a distinct learner Commitment; a goal remains the terminal-performance contract from P0. |
| Quick add | Current `quick_add` is a one-confirmation source-set ingest/build flow (`quick_add.py:1-22`), not a learner-intent transaction. | Reuse it as transport later, but expose a separate commit service with explicit action semantics. |
| Capability composition | Synthesis already emits facet/capability recipe components and one integration component (`source_set_synthesis.py:630-680`). | Normalize into the closed P1 vocabulary and preserve integration on blueprint versions; do not add pairwise conjunction state. |
| Exposure | P0 requires one activity exposure ledger; current source exposure events record source viewing, not prompt familiarity. | Keep source exposure distinct and connect it only through explicit shared-stimulus fingerprint membership. |

The code locations above are review anchors, not permanent API promises. If
the implementation moves them, the acceptance audit points at the successor
symbols and records the change.

---

## 3. Durable domain contracts

All immutable JSON uses canonical serialization and a content hash. Stable
identities and immutable versions are separate. Current heads are projections,
not mutable truth.

### 3.1 Commitment

`Commitment` records why this learner wants attention spent. It is not a goal,
card, reading mark, or scheduler bucket.

Create stable `commitments` and immutable `commitment_versions`. A version
contains:

- learner-authored intent and optional personal interpretation, preserved
  verbatim;
- optional `goal_id`; when present, the evaluated P0 goal-contract head is
  logged in each progression decision but not globally pinned;
- a coarse depth preset: `keep_in_touch`, `remember_key_ideas`,
  `work_fluently`, or `master_tasks_like_these`;
- active `depth_policy_version_id` and `depth_envelope_version_id`;
- purpose/reason text, attention/burden bounds, and optional due/hiatus hints;
- creation action and provenance;
- target-set hash and version hash;
- predecessor id and change reason.

Create `commitment_events` with at least:

```text
created | version_appended | disposition_changed | depth_policy_changed |
depth_envelope_changed | depth_milestone_reached | depth_transition_committed |
target_added | target_removed | family_attached | family_detached |
paused | resumed | retired
```

The current disposition projection is one of:

```text
active | paused | reference_only | one_check_pending | satisfied | stopped
```

`test_me_later` begins as `one_check_pending`; after one eligible delayed cold
administration it becomes `satisfied`, never an open-ended review obligation.
`reference_only` and `stopped` suppress scheduling but retain evidence and
content. Family/card retirement is recorded separately and cannot change the
commitment disposition implicitly.

#### 3.1.1 DepthPolicy, DepthEnvelope, and milestones

Create immutable `depth_policy_versions`, `depth_envelope_versions`, and
`depth_milestone_versions`, with append-only transition/reach events. Policy is
exactly one of:

```text
hold_at_target | suggest_next | auto_within_envelope
```

An envelope stores the learner-confirmed bounds over required capabilities and
target support, every P1 TaskFeature dimension, allowed scaffold fade and
tool/time tightening, cumulative burden, and an ordered DAG of reviewed
milestone edges. Each edge names predecessor/successor task contracts, eligible
purpose-typed family/pattern paths, observable entry/exit evidence, fresh-proof
requirements, and expected burden. The four coarse presets expand into editable
proposed envelopes; the immutable envelope, not the preset label, is
authoritative.

`hold_at_target` stops or devolves to maintenance at the active milestone;
`suggest_next` may show the next eligible edge but cannot activate it;
`auto_within_envelope` authorizes activation without item-by-item confirmation
only after its evidence gate passes. One decision can commit one edge and must
compare-and-append against the current policy/envelope/head. An edge outside the
envelope, a cross-target-family edge, or an unreviewed edge remains a proposal.

**Package boundary (U-018).** Live in P1: the policy/envelope/milestone
version objects, curated (owner-authored, reviewed) edge instances,
`suggest_next` support, and the deterministic one-edge transition service
(§5.7). Deferred to the auto-depth package: LLM edge-instance generation from
templates and generator demotion (U-016), live `auto_within_envelope`
activation authority, and the affect-downgrade enforcement point (U-011).
Until that package ships, a confirmed `auto_within_envelope` policy records
learner intent but behaves as `suggest_next` in the live product; the
transition service remains fully exercised under acceptance tests (§9.6).

Milestone attainment is separate from commitment disposition. An active
auto-deepening commitment can append `depth_milestone_reached` while preserving
that success and continuing toward a deeper authorized milestone. `satisfied`
still suppresses ongoing scheduling when the learner chooses to end the
commitment; it is never cleared merely because a deeper successor exists.

Repeated commit actions are idempotent on:

```text
learner + normalized target set + action + client idempotency key
```

Without a supplied client key, the service returns a possible existing
commitment for explicit merge; it does not silently merge differently worded
intent.

### 3.2 Commitment targets

Create immutable `commitment_target_versions` and membership rows. P1 supports:

- P0 target exemplar/version;
- canonical facet;
- learning object;
- source revision + block/span locator;
- legacy PracticeItem origin.

P3 later adds source-object and annotation target kinds without migrating the
existing identity. A target stores learner salience, required/optional role,
and provenance, but no mastery value.

A material target change appends a commitment successor. Removing a target
stops future generation for it; it never deletes observations already mapped
to it.

### 3.3 Closed capability vocabulary

Every criterion target, blueprint component, card contract, observation
contribution, and boundary cell uses exactly one of:

```text
retrieval
schema_interpretation
procedure_execution
method_selection
coordination
```

Legacy values are mapped by a versioned `capability_aliases` registry. Unknown
values fail new authoring and remain visible as `legacy_unmapped` only in
historical replay. `coordination` is valid only for a blueprint integration
component or a whole-task criterion that cites one.

### 3.4 TaskFeature vector

Create immutable `task_feature_schema_versions`. Every new card version and
target blueprint names one schema and supplies:

| Dimension | Launch representation |
|---|---|
| complexity | ordered `0..4`, anchored by reviewed examples in the subject |
| transfer | `same_context`, `near`, `far`, `novel_combination` |
| representation | namespaced set such as `symbolic`, `verbal`, `diagram`, `code`, `physical` |
| response | `recognize`, `short_constructed`, `long_constructed`, `structured_steps`, `performance` |
| scaffolding | ordered `none`, `cue`, `partial`, `worked` |
| time | expected-seconds interval plus optional hard limit |
| tools | closed/open-book, calculators, code, references, collaboration |
| span | `atomic`, `single_step`, `multi_step`, `whole_task` |

Depth is a trajectory across these dimensions, not a separate enum stamped on
an item. The commitment's coarse preset proposes a policy/envelope; the
confirmed envelope constrains progression and never overwrites task features.

Feature changes that cross a reviewed anchor or change terminal conditions are
material card-contract changes and therefore forks. Cosmetic metadata changes
are not.

### 3.5 ActivityPattern registry

An `ActivityPattern` is a reviewed instructional protocol, not an LLM prompt.
Create stable `activity_patterns` and immutable
`activity_pattern_versions`. Each version declares:

- allowed immutable purposes;
- cognitive operation: `retrieve`, `discriminate`, `generate`, `compare`,
  `explain`, `set_up`, `apply`, `reflect`, or `create`;
- induced learning process (U-035, closed vocabulary):
  `prior_knowledge_activation`, `comprehension_monitoring`,
  `self_explanation`, `schema_induction`, `procedure_compilation`,
  `memory_fluency`, `method_selection`, `coordination`, `transfer`, or
  `reflection` — controller-side routing metadata stating why this
  experience is served now; **never an evidence or projection input**;
- allowed target kinds and capabilities;
- outcome/completion semantics and response contract;
- progression role and prerequisite evidence;
- feedback and assistance strategies;
- evidence/scheduling semantics by administration context;
- task-feature bounds and permitted surface-variation axes;
- required rubric shape and all mint gates;
- duration/burden model and calibration status;
- pattern implementation/generator version.

P1 ships reviewed launch patterns for at least:

```text
minimal_retrieval
near_confusable_comparison
setup_only
example_study
example_comparison
example_completion
independent_repair
move_spotting
whole_task_integration
cold_target_assessment
```

Existing admitted probe templates become diagnostic-only patterns through an
adapter; their compiled likelihood identity and status remain intact.

LLMs may fill declared slots and variation axes. They may not invent a new
operation, feedback protocol, evidence rule, or progression transition while
rendering a surface. A candidate outside pattern bounds fails closed.

### 3.6 ActivityFamily

The construction rule is normative:

```text
ActivityFamily = commitment target × ActivityPattern version × progression policy
```

Extend P0 family versions with:

- commitment and target-version ids;
- immutable authoring purpose;
- pattern id/version;
- progression-policy id/version and goal contract evaluated at authoring;
- active depth-policy/envelope version and milestone edge(s) the family may
  serve;
- candidate cross-purpose family links;
- explicit angle inventory and coverage targets;
- family evidence-cap policy;
- minting and retirement policy.

Cross-purpose links are typed, for example
`diagnoses_for`, `teaches_for`, `practices_for`, and `assesses_for`. A
diagnostic family may name `candidate_practice_families`; its instruments
never become those practice cards.

### 3.7 Card identity, version, and lineage

A stable card is one executable contract within a family. Add a durable
`card_lineage_id` and append-only lineage edges:

```text
minor_successor | semantic_fork | split_from | merged_from
```

Card versions include P0's `card_contract_hash` plus:

- target/capability and task-feature vector;
- pattern and family-version pins;
- generic ActivityContract;
- rubric template and outcome-schema pin;
- surface policy: `fixed` or `rotating`;
- surface-variation bounds and angle identity;
- generator/gate/policy versions;
- expected duration/burden and calibration metadata.

The lineage classifier compares normalized contract components and returns:

- `surface_preserving`: wording/formatting cleanup, equivalent diagram,
  parameter-pool adjustment inside declared bounds, generator bug fix, or
  rubric clarification that cannot change classification;
- `fork_required`: target/capability change, response-contract change,
  rubric-semantic change, feature-bound crossing, meaningful difficulty/depth
  change, tool/open-book change, component↔whole-task change, or changed
  feedback/evidence eligibility;
- `review_required`: the service cannot prove either case.

`surface_preserving` appends a version inside the lineage and retains
scheduling state. `fork_required` mints a new card and lineage with an
evidence-informed prior but **no inherited certification or stability**.
`review_required` parks the successor; it never defaults to preserving state.
Automatic depth uses this same classifier: a new capability, task regime,
response contract, or reviewed feature-bound crossing forks even when the
transition was learner-authorized. Authorization permits the transition; it
does not make two memory traces identical.

### 3.8 Card scheduling and progression state

Create authoritative `activity_card_state` keyed by learner/card lineage and
scheduler algorithm version. It contains the current FSRS-compatible state,
due time, last eligible review, lapse-episode id, active state, and projection
head.

FSRS is permitted only for stable literal-recall-like contracts for which the
configured model is declared applicable. Other P1 cards still receive a
card-level due/progression projection, but its model is labeled
`provisional_stage_v1`; P1 must not mislabel that value as an FSRS retention
estimate.

Scheduling state changes only from eligible practice observations. Diagnostic,
instructional, and terminal-assessment administrations never apply a practice
FSRS review. Quarantined or out-of-band observations do not update card state.

Minor successor versions resolve to the same lineage state. Forks start a new
state row. A compatibility projection continues to materialize
`practice_item_state` while legacy readers exist.

### 3.9 Surface contract

P0 owns the immutable surface row. P1 adds or requires:

- `surface_policy` inherited from the card;
- generator provenance, anchor surface id, candidate batch id, and seed;
- exact hard-group memberships and soft-kinship features;
- declared angle coordinates and task features;
- gate decision, reviewer, and status;
- `pinned_by_learner` and surface authorship provenance;
- rotation eligibility and cache state.

A learner-authored surface is pinned: it remains available exactly as written
until edited/retired, while sibling cards may provide transfer checks. Editing
it appends a surface/card successor according to the lineage classifier; it
does not mutate an administered artifact.

### 3.10 Purpose-specific administration semantics

The administration's family purpose, not `attempt_type` or UI route, selects
the adapter:

| Purpose | Scheduling | Evidence | Familiarity | Lifecycle after render |
|---|---|---|---|---|
| diagnostic | no practice schedule update | only frozen episode posterior/declared facet evidence; never opportunistic | full exposure | consumed forever for diagnosis |
| instructional | progression-path/exposure only; no lapse | no unassisted certification | full exposure | reusable subject to policy |
| practice | card-level review when observation eligible | context/familiarity/reliability-weighted | full exposure | reusable; rotate lazily |
| assessment | no practice FSRS | terminal distribution/certification only | full exposure | P0 assessment burn rules |

Administration context is independent of purpose and records cold/scaffolded,
hints, feedback exposure, timing, tools, collaboration, source visibility, and
goal-terminal conditions. `cold` means no unintended cue relative to the
pinned terminal contract, not universally closed-book. When an administration
occurs inside a reader session (U-033), the context additionally records
`reading_phase` (`before_section` / `during_section` / `after_section`) —
an owner-placed reading question is an ordinary instructional administration
with `source_visible=true` and a reading phase, not a new activity kind.

---

## 4. Shared exposure and familiarity

### 4.1 Exact exposure and hard correlation

P0's `activity_exposure_events` is authoritative. Add normalized
`surface_fingerprint_memberships` where every membership is:

```text
namespace + value_hash + surface_id + provenance + confidence/status
```

Launch namespaces include:

```text
surface_hash
shared_stimulus
source_example
solution_recipe
parameter_template
verbatim_target
external_artifact
```

Namespaces are never interchangeable. A value `svd-1` in `source_example`
cannot collide with `svd-1` in `solution_recipe`. A surface may belong to many
groups; selecting the first non-empty field is forbidden.

Exact hash or a policy-declared hard group blocks an unseen/independent claim.
Missing fingerprint data yields `unknown`, not `novel`.

Tutor and reader-dialogue answers propagate exposure (U-033): when an AI
explanation is shown, the claims, proof ideas, representations, and examples
it exposed append exposure events against their fingerprint memberships, so a
near-term surface reusing those cues reads as warm rather than cold. An
explanation that cannot be fingerprinted degrades to `unknown` for the
surfaces it plausibly touched — never silently to `novel`.

### 4.2 Soft kinship vector

Store a separate versioned feature vector, never a pre-collapsed group id:

- target/facet overlap;
- source and shared-stimulus proximity;
- solution-recipe overlap;
- representation and answer-structure match;
- parameter/template relationship;
- semantic surface similarity when available;
- angle distance and time since exposure;
- exposure count, feedback reveal, and correctness-independent recency.

P1's `familiarity_projection_v1` is a deterministic, monotone heuristic over
these features. Every coefficient/threshold that can change evidence or
rotation is a P0 decision parameter with visible calibration status. P4 may
fit a kernel, but it consumes the same stored features and never rewrites P1
exposure history.

Familiarity affects:

- evidence independence/discount;
- rotation need and temporary sibling suppression;
- held-out eligibility through hard collisions only;
- learner-facing explanation of why a surface is considered warm.

It does not directly change whether an answer was correct.

### 4.3 Family evidence caps

One family, card lineage, hard group, or tight soft-kinship cluster cannot mint
unbounded independent evidence. A versioned cap policy limits total effective
mass per target × capability × angle neighborhood. Additional administrations
remain useful practice but add zero new independent-group count and diminishing
evidence mass.

Certification requires fresh evidence across the P0 contract's required
independent groups. Variant minting inside one family can never certify by
itself.

---

## 5. Authoring, minting, and progression behavior

### 5.1 Authoring transaction

Family authoring is a staged, idempotent transaction:

1. resolve commitment target and current goal-contract head;
2. resolve the active depth policy/envelope and choose a reviewed
   ActivityPattern version inside it;
3. create a draft family version and required angle inventory;
4. create/gate stable card contracts ahead of use;
5. mint/review initial surfaces;
6. activate family/card versions through append-only events;
7. pre-mint only the bounded cache required by policy.

Failure before activation leaves an inspectable draft and no schedulable
partial object. Activation pins all pattern, schema, gate, calibration, and
decision-parameter versions.

Diagnostic cards remain ahead-of-time instruments and must pass their existing
identifiability/likelihood gates. JIT work normally renders only surfaces
inside admitted bounds. The P4/Journey-8 provisional-card exception remains
explicitly out of the ordinary authoring path.

### 5.2 Surface mint gates

Every generated surface, regardless of purpose, must pass:

1. card-contract equivalence;
2. solvability/answer-key consistency;
3. verbatim rubric applicability;
4. purpose-specific leakage rules;
5. exact and near-clone novelty audit;
6. task-feature conformance;
7. declared difficulty/complexity bounds;
8. content safety and source/provenance validity;
9. comparative check against its anchor when rotating.

Gate results are append-only and include candidate inputs, versions, reviewer,
and failure reasons. A failed candidate is retained for audit but never
servable.

### 5.3 Fixed and rotating policies

`fixed` is appropriate for verbatim targets, learner-pinned surfaces, and
long-form explanation cards whose wording is the authored artifact. Fixed
does not mean fresh: repeated administrations become familiarity-discounted.

`rotating` is the default for procedural, short-answer, discrimination, and
transfer work. P1 launch behavior:

- keep the current admitted surface until the warmth projection or exposure
  cadence requests rotation;
- provisional cadence is about 2–3 administrations, but the exact decision is
  a registered heuristic, not an invariant;
- when warm and due, enqueue an anchored candidate batch off the response hot
  path;
- compare candidates to the existing surface and card constraints rather than
  asking for absolute difficulty;
- retain one admitted next surface and at most one spare by default;
- never spend minting work on an inactive/retired card;
- if no candidate passes, serve familiar practice only when purpose permits,
  disclose reduced evidence, and enqueue review. Never call it fresh.

Rendering and candidate minting are separate transactions. A cache race may
waste a candidate but may not double-administer or manufacture novelty.

### 5.4 Angle inventory and orthogonal-next rule

Each family declares coordinates over cue direction, response form,
representation, operation, context, task span, transfer distance, and
scaffolding. Cosmetic paraphrase remains the same angle/card lineage. A new
cognitive angle creates a sibling card or family branch.

After success, the next growth activity is normally a **delayed orthogonal
angle**, not a near-clone while the answer is in working memory. Context fades
deliberately:

```text
original narrative -> altered/stripped context cold attempt -> source restore
```

Success propagation to sibling angles is strongly shrunk and affects only the
family-stage prior. It never marks a sibling reviewed or grants its independent
surface group. Failure increases commitment-level uncertainty but does not
reset every sibling.

### 5.5 Lapse and retry episodes

A failed eligible practice administration opens a durable lapse episode.
Same-session retries are linked observations; they never overwrite or replace
the original failure. Before `give_up`, retry outcomes may update a derived
retrievability estimate but do not stack independent evidence or repeated
penalties.

The launch post-lapse follow-up is next day and explicitly provisional. It is
recorded as a decision parameter and may be changed only by a versioned policy.
The delayed follow-up should use a fresh/orthogonal surface when available.

### 5.6 Pre-mint jobs

Create durable, idempotent mint requests keyed by:

```text
card version + anchor surface + requested angle + generator version + gate policy
```

States are `pending`, `running`, `candidate_ready`, `admitted`, `rejected`,
`obsolete`, or `failed`. Card/family retirement makes pending work obsolete.
Jobs store token/cost telemetry and never block attempt submission.

### 5.7 Automatic depth-progression substrate

P1 exposes a deterministic transition service; P2/P4 decide when to call it —
and live activation authority ships only with the auto-depth package (U-018;
P2's first cut is `suggest_next`-only).
Given the current commitment, goal-contract head, milestone, evidence receipt,
and budget, it:

1. resolves the single reviewed outgoing edge selected by the caller;
2. verifies policy is `auto_within_envelope` and every successor dimension lies
   inside the active envelope;
3. verifies the predecessor exit gate and fresh-proof requirements;
4. asks P0 to append an `authorized_depth_step` when terminal support changes;
5. activates already reviewed successor families/cards or leaves an
   `authoring_needed` proposal—it never hot-path invents a protocol;
6. applies the lineage classifier and starts new scheduling state for every
   fork, borrowing only an explicitly shrunk family-stage prior;
7. appends milestone/transition events transactionally and returns a receipt.

Failure is non-destructive. No eligible successor means maintain/stop/suggest;
it never mutates the predecessor, fabricates a fresh surface, or recursively
walks a second edge.

---

## 6. Service and read interfaces

Business logic stays in `src/learnloop/services`; repository methods own SQL;
CLI/sidecar/TUI are adapters.

Required service boundaries:

- commitments: create from an explicit commit action, append a version, change
  disposition/depth policy/envelope, attach/detach targets, record milestone
  attainment, and inspect intent history;
- patterns: register/review/activate a version and list compatible patterns;
- families: author/activate/retire, link cross-purpose families, inspect angle
  coverage, resolve progression policy, and commit one authorized depth edge;
- cards: classify a proposed edit, append minor successor, fork contract,
  split/merge lineage, and rebuild card state;
- surfaces: request candidates, run all gates, admit/pin/retire, rotate, and
  explain hard/soft familiarity;
- administrations: open atomically, resolve purpose adapter, append response,
  and project scheduling/evidence/familiarity in one transaction/outbox unit;
- compatibility: resolve PracticeItem/probe/exam ids to P0 identities and
  materialize legacy DTO/state without making it authoritative.

Every “why this activity?” DTO includes:

```text
commitment + target
depth policy + envelope version + current/next milestone
family purpose + pattern version
card lineage/version + angle
surface freshness/hard collisions/soft familiarity
administration context
which systems this result may update
policy/calibration/algorithm versions
```

Minimum CLI parity:

- inspect a commitment and its activity tree;
- explain/fork a card edit;
- audit a surface's full cross-purpose exposure and kinship trace;
- inspect/retry a mint request;
- compare authoritative card state with the PracticeItem compatibility row;
- run a shared-substrate migration/replay audit.

---

## 7. Migration and compatibility

### 7.1 P0 dependency gate

P1 migration refuses to run until P0 schema/projection versions are present.
It verifies that new administrations and exposures can be written and replayed
before adding scheduling authority. No P1 table shadows a missing P0 table.

### 7.2 Legacy PracticeItem backfill

P0 already maps each existing PracticeItem to a default practice family, card
version, and fixed surface. P1 completes that mapping:

1. place each active item under a `legacy_unowned` compatibility container,
   which is not a Commitment and cannot be presented as learner intent;
2. offer an explicit `adopt_legacy_item` keep action that creates the real
   Commitment, or an equally direct retire/reference-only action; never infer
   intent from an active state row;
3. attach the mapped family to the legacy target and a compatibility pattern;
4. assign the closed capability alias and task-feature vector, marking unknown
   dimensions explicitly;
5. create a card lineage and copy `practice_item_state` into authoritative
   card state once;
6. retain the PracticeItem id as an alias to its compatibility surface/card;
7. materialize prompt/answer/rubric DTOs for old callers from the new head;
8. preserve legacy YAML and replay; do not bulk-rewrite user-authored files.

An inactive legacy item remains inactive. Historical content-hash changes are
not retroactively classified as minor; they retain legacy replay and are
marked `legacy_lineage_unknown` for new certification.

### 7.3 Probe and exam adapters

- existing probe-family/card identities and compiled likelihood hashes map to
  diagnostic patterns/families/cards;
- every `probe_presentation` maps to the P0 administration created in P0;
- episode updates still consume the frozen historical instrument snapshot;
- existing exam reservations map to assessment families/surfaces and keep P0
  burn/contract pins;
- the same exact prompt used by multiple adapters shares fingerprint groups
  and exposure, so adapters cannot create false novelty.

### 7.4 Dual-write and cutover

During cutover, attempt submission performs one authoritative P0/P1
administration transaction and then materializes existing attempt/state rows.
New projectors never reconstruct purpose from `practice_mode` when an
administration exists.

Cutover gates, in order:

1. identity mapping coverage is 100% for active items;
2. replay equivalence for historical algorithms passes;
3. new scheduling projections match legacy state for a frozen fixture within
   declared numerical tolerance;
4. purpose-specific side-effect tests pass;
5. the legacy scheduler reads compatibility card state;
6. legacy direct state writes are rejected for new administrations.

Rollback switches read authority back to the last legacy projection but keeps
all new append-only events. It never deletes P1 records.

### 7.5 Failure behavior

- missing commitment for new authoring -> reject activation, preserve draft;
- unknown capability/task schema -> reject new card, preserve legacy replay;
- ambiguous edit -> park for review, do not retain scheduling state;
- missing/unknown fingerprint -> allow ordinary instruction/practice with
  disclosed uncertainty, but grant no unseen/independent claim;
- rotation failure -> familiar practice with discounted evidence or skip;
- purpose mismatch -> reject administration before render;
- partial projection failure -> keep raw events and enqueue deterministic
  rebuild; no half-updated evidence/scheduling state;
- unavailable generator -> current admitted surface remains usable when its
  lifecycle permits; generation is never required to submit a response;
- stale/missing envelope, outside-envelope edge, or unreviewed successor ->
  preserve a suggestion/authoring need and do not activate progression;
- qualifying edge whose required successor family is unavailable -> preserve
  achieved milestone and continue maintenance; never mutate the prior card.

---

## 8. Implementation order

1. Add commitment/version/target/depth-policy/envelope/milestone repositories
   and explicit commit service.
2. Add capability aliases, TaskFeature schema, ActivityPattern registry, and
   compatibility patterns.
3. Extend P0 family/card contracts with commitment, pattern, feature, angle,
   and lineage pins.
4. Implement edit classification, card-lineage state, and PracticeItem state
   projection.
5. Replace purpose-blind attempt side effects with administration adapters.
6. Add namespaced hard groups, soft-kinship feature storage, and global P1
   familiarity projection.
7. Generalize probe mint/gate infrastructure and add fixed/rotating surface
   services plus durable pre-mint jobs.
8. Add angle/family progression, one-edge automatic depth transition service,
   evidence caps, lapse episodes, and linked retry projection.
9. Dual-write active entry points; cut reads over behind explicit projection
   versions.
10. Run migration, replay, planted-learner, and Journey-6 acceptance suites.

Each checkpoint is independently replayable. Do not begin automatic rotation
until lineage-state and global-exposure gates pass.

---

## 9. Test and acceptance contract

### 9.1 Domain invariants

- passive highlight/read/ask cannot create a commitment;
- every commitment creation cites a commit-class action/idempotency key;
- retirement of all activities leaves commitment/evidence intact;
- family purpose cannot change in place;
- a cross-purpose link never reuses the same activity identity;
- invalid/unknown capabilities fail new authoring;
- coordination evidence exists only through a blueprint integration component;
- `auto_within_envelope` can activate only one reviewed inside-envelope edge;
  `hold_at_target` and `suggest_next` cannot auto-activate it;
- an achieved milestone remains achieved when a deeper milestone activates.

### 9.2 Lineage and scheduling

- wording-only successor preserves card state and appends a new surface/version;
- target, rubric-semantic, open-book, feature-bound, or whole-task change forks
  with no stability/certification inheritance;
- ambiguous edit is parked;
- only eligible practice administrations update card scheduling;
- diagnostic, instructional, assessment, quarantined, and out-of-band
  observations leave practice FSRS unchanged;
- same-session retry preserves the original lapse and cannot stack penalties;
- a depth edge that changes capability/task regime forks and inherits neither
  FSRS stability nor certification; a surface-only rotation does not fork.

### 9.3 Exposure and rotation

- an exposure under one LO/purpose is visible under every other LO/purpose;
- equal raw values in different namespaces do not collide;
- all hard memberships are considered, not only the first;
- an exact/near-hard collision cannot mint unseen assessment or independent
  certification credit;
- unfamiliarity is never inferred from a missing fingerprint;
- a rotating card mints only after warmth and does so off the attempt hot path;
- anchored candidates must pass comparative and verbatim-rubric gates;
- retirement cancels/obsoletes queued mint work;
- repeated/familiar surfaces remain useful practice but approach zero new
  evidence mass;
- variants from one family alone cannot satisfy independent-group certification.

### 9.4 Purpose matrix

For the same synthetic response administered once under each purpose, assert
the exact scheduling/evidence/familiarity/lifecycle deltas in §3.10. Also
assert that an ordinary cold practice response cannot update an open probe
episode without a committed diagnostic presentation.

### 9.5 Compatibility and replay

- every active PracticeItem resolves to exactly one default practice
  family/card/surface and stable aliases; it becomes commitment-owned only
  after an explicit adoption action;
- historical probe/exam snapshots replay byte-identically under their recorded
  algorithm versions;
- corrupting `practice_item_state` caches does not alter an authoritative
  card-state rebuild;
- dual-write retry is idempotent and never duplicates administration,
  exposure, attempt, or schedule events;
- rollback preserves P1 append-only history;
- a mixed old/new vault can serve old items while new cards use rotation.

### 9.6 Journey 6

Using a planted learner and one reviewed family:

1. create a commitment from an explicit exemplar or remember action;
2. demonstrate retrieval on one surface;
3. progress through a different capability/angle rather than a cosmetic clone;
4. rotate a warm surface through the anchored gate;
5. lapse, retry without mutation, and receive a next-day fresh follow-up;
6. demonstrate delayed transfer on an independent surface;
7. record the milestone as reached and automatically activate one reviewed
   inside-envelope next edge without another prompt;
8. show the old and new lineage/evidence/familiarity/scheduling traces
   separately, with no FSRS/certification inheritance;
9. retire a bad card without losing the commitment, milestone, or prior evidence.

Acceptance fails if surface generation alone advances certification, if the
same surface is represented as fresh, or if a card fork inherits stability.

### 9.7 Performance and operability

- queue construction performs a bounded global-familiarity query, not one
  query per candidate;
- opening an admitted administration does not call an LLM;
- attempt submission remains usable when mint workers are down;
- replay of 10,000 synthetic activity events is deterministic and reports its
  algorithm/version manifest;
- migration/backfill is idempotent on two consecutive runs.

### 9.8 Event sufficiency for deferred projections (U-015)

- every administration/observation pair carries the card version id, outcome
  class, and full administration context;
- a prototype replay over a synthetic fixture computes per-card outcome
  counts stratified by administration context using only ledger events — no
  live tables — proving the difficulty/discrimination/rubric-calibration
  projections are later buildable with zero schema changes;
- the same replay emits card-level outcome counts in the shape the deferred
  hierarchical likelihood model consumes (U-014 resume path).

---

## 10. Launch defaults and explicit assumptions

- `fixed` remains the compatibility policy for all legacy PracticeItems until
  a reviewer explicitly assigns a rotating pattern/card contract.
- Rotation after roughly 2–3 administrations, next-day post-lapse review,
  kinship coefficients, sibling shrinkage, and family evidence caps are
  decision parameters with `heuristic` launch status.
- P1 uses bounded heuristic authority from P0: uncertain familiarity can
  reduce/withhold evidence and surface claims, but does not hard-block useful
  instructional or practice work.
- “Fresh” means no disqualifying LearnLoop exposure under the named global
  policy; it is not a claim about the learner's entire life.
- Practice progression follows the current P0 goal-contract head at each
  decision and logs it. Probe episodes and assessment reserves keep their own
  P0 commitment-point pins.
- End-of-chapter ongoing commitments launch with a visible recommendation of
  `auto_within_envelope`; the learner confirms or changes it once. Quick
  `test_me_later` remains `hold_at_target`, and other captures default to
  `suggest_next`. No mode permits an outside-envelope transition. While the
  auto-depth package (U-018) is deferred, a confirmed `auto_within_envelope`
  records intent but activates nothing automatically — it behaves as
  `suggest_next` until the package ships.
- Automatic depth commits at most one reviewed edge per decision and replans.
  All numeric evidence/burden thresholds remain registered heuristic decision
  parameters until calibrated.
- P1 is single-learner. Namespacing and event shapes must not assume that a
  learner id can never be added, but no cross-learner model is introduced.

---

## Change log

### 2026-07-20 — amendment: step-9 cutover truthfulness (post-audit A1/A2/A3/A4)

Four adversarial audits found the step-9 completion entry below overstated the
cutover. Surgical corrections (the entry below is left in place for history; this
note is authoritative where they differ):

- **Hot-path eligibility is now genuinely threaded (A1/F2).** `attempts.apply_attempt`
  previously called `hot_path_applies_practice_review` WITHOUT `eligible` (it defaulted
  to `True`), so the §3.8 ineligible divergence on a live mvp-0.8 vault was dead code.
  The hot path now derives the observation's REAL evidence eligibility
  (`activities.evidence_eligibility_for`) and threads it, and the two latent
  else-branch bugs are fixed: a first-ever ineligible observation creates NO memory
  state (never `apply_review(None, …)`), and a retained prior memory keeps its stored
  interval/due_at (no rewrite). An eligible practice attempt stays byte-identical to
  legacy; an ineligible observation leaves card scheduling EXACTLY as it was
  (`test_hot_path_eligibility_cutover`).
- **`submit_administration_response` is NOT called from `attempts.apply_attempt`.** The
  original entry's claim of a "hot-path lineage write … wired into the hot path" was
  inaccurate: `resolve_legacy_item` maps one legacy item to one surface and
  `open_administration` is idempotent per surface, so calling the full lineage write
  per attempt would collapse repeated attempts into a single administration and drop
  later observations (audit F3). Genuine per-attempt substrate administration requires
  surface rotation / per-attempt identity and is out of step-9 scope. The per-attempt
  administration + observation ARE already opened on the hot path by the P0.2 grade
  dual-write (`grade_resolution.record_grade_dual_write`);
  `submit_administration_response` remains the substrate write path exercised by the
  substrate/journey/event-sufficiency suites, not by `apply_attempt`.
- **Raw-event atomicity is now real (A2).** The raw-event lineage (administration +
  folded-in context + rendered/submitted exposures + observation + measurement events)
  is written as ONE transaction (`Repository.write_administration_lineage_atomic`); a
  fault before commit rolls back the whole unit (clean nothing-happened state), and
  ONLY the projection may defer. `rebuild_deferred_projection` re-derives its inputs
  (eligibility from the observation, review/failed from the persisted
  `response_appended` event) FROM THE LEDGER — never caller-supplied evidence — and
  refuses (`NoObservationToRebuild`) when no observation exists. The fault test runs
  the recovery at every boundary and asserts the final card state equals the no-fault
  result.
- **Gates 3 and 6 are enforced, not self-referential (A3).** Gate 3 drives the real
  `PracticeAdapter.apply_scheduling` (persisting card state) and compares it to an
  INDEPENDENT hand-folded FSRS transition. Gate 6 enforces at a service-layer
  chokepoint (`guarded_legacy_scheduling_write`): a direct legacy card-state write for a
  new administration is blocked BEFORE any row is written, asserted by driving it. A
  barrier-failure test forces an early gate to fail and asserts every later gate is
  blocked and unexecuted.
- **`substrate_cutover:PURPOSE_ADAPTERS_LIVE_FROM` is bound to code (A4).** It now names
  a real module constant (`substrate_cutover.PURPOSE_ADAPTERS_LIVE_FROM`) that
  `purpose_adapters_live` reads, rather than a dangling registry entry.

### 2026-07-19 — P1 steps 9–10 complete (final P1 packages)

Steps 9 (dual-write cutover, narrowed) and 10 (replay + Journey 6 + §9.8 event
sufficiency) landed. Full suite green (`uv run pytest -q` -> **1971 passed, 4
skipped**). New: `src/learnloop/services/substrate_cutover.py`,
`src/learnloop/services/card_outcome_replay.py`,
`tests/test_substrate_cutover.py`, `tests/test_event_sufficiency.py`,
`tests/test_journey6.py`; the purpose-adapter path is the LIVE scheduling
authority for mvp-0.8 vaults (`administration_adapters.purpose_adapter_path_live`;
**see the 2026-07-20 amendment — the hot-path eligibility is genuinely threaded and
the divergence is live only after that fix**), legacy vaults keep the
byte-identical purpose-blind path + characterization pins.

**Step-9 six ordered cutover gates (§7.4), narrowed by the 2026-07-19 no-old-vault
decision** — evaluated as a hard sequential barrier
(`substrate_cutover.run_cutover_gates`):

1. *identity mapping coverage 100%* — **N/A (owner decision):** fresh mvp-0.8 vaults
   reinitialize; no legacy PracticeItem backfill to cover. Frozen machinery kept green.
2. *replay equivalence for historical algorithms* — **N/A (owner decision):** a frozen
   legacy characterization (`test_characterization_probe_replay`), not a new-vault
   write-path concern.
3. *new scheduling projections correct* — **LIVE / pass:** reframed from legacy-row
   equivalence to new-substrate write completeness (the card-state projection
   reproduces the FSRS transition over its review stream).
4. *purpose-specific side-effect tests* — **LIVE / pass:** the §9.4 purpose matrix
   (`test_substrate_cutover`, `test_administration_adapters`).
5. *legacy scheduler reads compatibility card state* — **N/A (owner decision):** the
   legacy `practice_item_state` read path is frozen legacy machinery; a fresh mvp-0.8
   vault has no legacy scheduler reader.
6. *legacy direct state writes rejected for new administrations* — **LIVE / pass:**
   on a live vault, new-administration scheduling can only be written through the
   purpose adapter (`reject_legacy_scheduling_write`).

The substrate lineage write (`substrate_cutover.submit_administration_response`;
**NOT a hot-path caller — see the 2026-07-20 amendment**) writes the raw-event lineage
(administration + folded-in context + exposures + observation + measurement events) as
ONE atomic transaction and defers ONLY the adapter-scheduling projection; a
fault-injection test runs the recovery after every boundary and asserts it lands the
no-fault card state (deferred rebuild re-derived from the ledger; §7.5
silent-corruption concern), and dual-write retry is idempotent (§9.5).

**Step 10** — Journey 6 passes end-to-end on a fresh mvp-0.8 vault through the real
services (`test_journey6`, all nine steps + the three acceptance-fail guards). The
§9.8 event-sufficiency prototype (`card_outcome_replay.replay_card_outcome_counts`)
computes per-card outcome counts stratified by administration context from ledger
events ALONE (no live tables), emits them in the U-014 resume shape, and the
10,000-event synthetic replay is deterministic with an algorithm/version manifest
(§9.7). Two new structural params registered at birth
(`substrate_cutover:P1_SCHEDULER_ALGORITHM_VERSION`, `:PURPOSE_ADAPTERS_LIVE_FROM`).

### 2026-07-19 — owner-decision defaults adopted (pending owner confirmation)

The four owner-decision-memo defaults from the P1 implementation design (§A) are
adopted as the working defaults the implementation proceeds on. Each is marked
**pending owner confirmation**:

- **A.1 — P0↔P1 extension mechanism.** Extend the P0 (migration 065) immutable
  family/card/surface version rows via *side tables keyed by the P0 version id*,
  never by ALTERing the immutable rows. Rationale: P0 guarantees the version rows
  are byte-frozen for replay; a side table keyed by the immutable id is additive
  and keeps P0 replay-stable at the cost of one extra join per resolve.
- **A.2 — progression policy is its own object.** Create immutable
  `progression_policy_versions` (the third factor of the family construction rule,
  distinct from DepthPolicy), governing within-family angle order / prerequisite
  evidence / orthogonal-next / sibling-shrinkage / family-stage prior. Rationale: a
  pattern is reusable across families with different progression appetites, and
  folding progression into DepthPolicy would conflate within-family angle order
  with cross-card milestone authorization.
- **A.3 — depth changes force a version bump; milestone-reached does not.** A depth
  *policy* or *envelope* change appends a commitment `version_appended` in the same
  transaction as the typed `depth_policy_changed` / `depth_envelope_changed` event
  (the immutable version stores the active policy/envelope ids and a version hash,
  so changing which is active is a material version change). `depth_milestone_reached`
  and `depth_transition_committed` append only the event (achievement facts over the
  existing envelope), and disposition changes append only an event.
- **A.4 — evidence-cap soft-kinship clustering.** Single-linkage threshold
  clustering scoped to a target × capability × angle neighborhood, using the
  `familiarity_projection_v1` pairwise warmth score and a registered
  `tight_kinship_threshold`. Rationale: transitive connected-components over the
  whole warmth graph would chain distant surfaces and is unstable as history grows;
  a learned kernel is explicitly deferred to P4.

Steps 1–3 land against this change log: migrations `072_commitments.sql`,
`073_activity_patterns_and_features.sql`, `074_activity_contract_extensions.sql`
(P0 hardening + probe cutover consumed 070–071, so P1 starts at 072). A.4 is
recorded here but exercised by step 6/8 (out of the steps 1–3 scope).

### 2026-07-19 — owner decision: no further old-vault migration investment

The owner has decided that migrating existing (pre-mvp-0.8) vaults is not
worth further effort: **mvp-0.8-and-beyond vaults are reinitialized fresh.**
Consequences for this spec, recorded as named scope changes:

- Already-landed backfill/compatibility machinery (P0 §7.1 backfill, the
  mvp-0.6/0.7 compatibility projections, the P0.5 `upgrade_to_mvp08` path)
  is **frozen as-is**: kept green, not extended, no new acceptance work.
- The step-9 dual-write cutover narrows: its purpose was protecting existing
  vault history mid-transition. New vaults write the new substrate natively;
  the six ordered gates apply only to whatever minimal shim keeps legacy
  read paths working in already-initialized dev vaults. §9.7's
  "migration/backfill idempotent" bullet applies to the frozen machinery only.
- §10's "`fixed` remains the compatibility policy for all legacy
  PracticeItems" applies only to vaults that are not reinitialized; the
  golden-path fixture vaults for P2 are expected to be freshly initialized
  mvp-0.8 vaults.
- Characterization tests pinning legacy behavior remain as regression
  anchors while the legacy code paths exist; deleting those paths (and their
  pins) is a future owner decision, not implied by this one.

### 2026-07-20 — learner-owned card lifecycle (reader-control slice)

- PracticeItem gains YAML-owned `status: active|retired` (+ `status_reason`);
  state_sync's `_activatable` deactivates retired items and the reconcile loop
  now flips `active` in BOTH directions (activatability changes are applied even
  when the content hash is unchanged). Scheduler / exam pool / probe selection
  each skip non-active items explicitly.
- `services/item_authoring.py`: author / edit / retire / split, learner-owned
  (no review gate — the proposals machinery reviews SYSTEM changes only).
  Retirement takes the §3.7 typed reason taxonomy and fail-safe-mirrors a
  surface lifecycle `retire` through `resolve_legacy_item` + `retire_with_reason`
  (provenance `learner_action`) so the substrate ledger agrees with the vault.
  Learner-authored cards always embed a correctness rubric (gradable without a
  vault default). Interaction-event kinds widened (migration 103) with the four
  `learner_item_*` lifecycle kinds.
- Surfaces: sidecar `author/edit/retire/split_practice_item` (+ ctx reload so
  deactivation lands before the response), desktop CardControls on Practice
  (prompt-only pre-attempt — no answer leak) and Feedback (full controls),
  CLI `learnloop card write|reword|retire`, and the outstanding-question queue
  (migration 102, `services/question_queue.py`, Today panel,
  `learnloop questions`).

# P0 implementation spec: measurement correctness

**Status:** draft v0.2 — code-audited 2026-07-16; depth contract amended
2026-07-17; orphan/n=1 consensus folded 2026-07-17 (retirement record,
`interaction_events`, affect tap, calibration streams + bootstrap, abstention
budget, registry lifecycle, `P(Z|H)` robustness axis)

**Parent:** `spec_new_improvements_v2.md` §3 and §8a

**Purpose:** make every consequential measurement replayable through the grader
noise that actually produced it, against the target contract and surface state
that actually applied.

This is the first implementation spec for the exemplar-driven vertical slice.
It is normative for P0. Where it conflicts with an older probe, exam, or
knowledge-model spec, this document governs new writes; frozen legacy replay
continues under its recorded algorithm version.

**Ownership claims** (pins `spec_ownership_ledger.md` seed 2026-07-17):

- implements: U-010@v2 (typed affect capture; commitment-level bindings land
  with P1's commitment objects), U-012@v2, U-013@v2, U-014@v2 (robustness
  axis only), U-020@v1, U-021@v1, U-022@v1.
- defers: U-011@v2 (affect auto-downgrade *enforcement point* — to the
  auto-depth package, U-018; signal capture is not deferred); the U-014
  hierarchical instrument-likelihood core (resume path: card-level outcome
  counts logged per spent surface, retroactive via replay).

---

## 1. Outcome and boundaries

P0 is complete when a raw learner response can be followed through:

```text
learner state H
  -> true coarse response class Z
  -> observed grader emission E = (class G, confidence bucket)
  -> versioned calibrated interpretation
  -> diagnostic posterior and/or certification contribution
  -> current projection, with a reproducible historical decision trace
```

and when that measurement also names:

- the confirmed terminal-contract version the consumer pinned;
- the semantic card contract, exact surface, and resolved administration;
- every exposure or feedback event that affects held-out eligibility;
- the calibration model, algorithm version, and decision-parameter metadata
  used by the projection.

### 1.1 Non-negotiable invariants

1. **Raw events are authoritative.** Responses, grader outputs, adjudications,
   exposures, feedback reveals, and lifecycle transitions are append-only.
   Current posteriors and certifications are projections. Legacy summary
   columns may remain as derived compatibility caches but are never replay
   inputs for new-version projections.
2. **Model `H -> Z -> E`, never `H -> G` by scalar discount.** Instrument
   likelihoods model `P(Z | H)`. A grader model supplies `P(G | Z, context)`.
   Its full observed emission is `E = (G, confidence bucket)`. Diagnostic
   likelihoods compose the instrument with `P(E | Z, context)`. The grader's
   self-reported confidence is evidence only through that calibrated joint
   channel; it is never treated as a probability or direct multiplier.
3. **Selection and update use the same pinned model.** An episode cannot rank a
   card with one channel and replay its answer with another. Historical
   decision traces keep their episode pin; current learner-state projections
   may be rebuilt under a newer named calibration/projection version.
4. **Heuristic authority is bounded, not blocked.** `heuristic`,
   `simulation_validated`, and `live_calibrated` control uncertainty width and
   claim language, not a binary permission gate. Wide uncertainty lowers robust
   value, stops fragile episodes earlier, and reduces certification mass.
5. **Targets version at confirmation.** Before exemplar confirmation a terminal
   contract is a draft and cannot be pinned. Confirmation mints v1. Every
   subsequent material edit appends a successor; no confirmed version mutates.
   Each consumer pins independently at its commitment point.
6. **Automatic depth is pre-authorized and versioned.** A controller may append
   a terminal-support successor without another prompt only when the complete
   change lies inside the learner-confirmed DepthEnvelope version and follows a
   reviewed milestone edge. The successor cites that authorization and the
   evidence-gated transition. Anything outside the envelope remains a draft.
7. **Purpose never transitions.** Diagnostic, instructional, practice, and
   assessment family purposes are immutable. A burned assessment may seed a
   linked practice-purpose successor, but the assessment object itself never
   becomes practice.
8. **Exposure is monotone.** Regrades can change certification, never make an
   exposed surface pristine again. A lifecycle projector may change the reason
   a surface is ineligible, but cannot erase an exposure or feedback event.
9. **No terminal claim without lineage.** Terminal certification requires a
   target-contract version, an eligible cold administration, an unambiguous
   surface lineage, and a reliability-aware contribution. Missing lineage may
   support a provisional belief, never pristine terminal credit.
10. **Formative interactions route, never certify.** A learner question is
    never direct ability evidence. A source-visible or primed formative
    answer (reading-time, tutoring) mints at most a replay-derived routing
    prior that the first cold observation on the same target supersedes. An
    AI answer or explanation appends exposure — the surfaces it warms lose
    cold eligibility through the ordinary ledger, never silently. These
    interactions reach projections only through administration context and
    the exposure ledger; they are never posterior or certification inputs.
    (Constrains U-033's P2 wiring; the events land with P2/P3 on the U-013
    envelope — no new P0 tables.)

### 1.2 Scope

P0 includes:

- asymmetric, versioned grader confusion models and calibrated true-outcome
  interpretations;
- raw grade/regrade/adjudication events and replay;
- reliability-aware diagnostic posteriors and canonical certification;
- robust selection/stopping under calibration uncertainty;
- confirmed terminal-contract versions, depth-authorization provenance, and
  per-consumer pins;
- the minimum final activity family/card/surface/administration/exposure
  substrate needed to enforce assessment burn correctly;
- calibration-status coverage for every decision-affecting numeric parameter;
- the retirement record (reason taxonomy, replacement-proposal hook, CLI
  affordance) and the typed `interaction_events` envelope;
- typed affect-tap capture and the three-stream calibration design with its
  retrospective adjudication bootstrap;
- compatibility adapters and deterministic backfill for current PracticeItem,
  probe, and exam histories.

P0 does **not** include automated family generation, the commitment UX, the
instructional/practice progression controller, open-world hypothesis expansion,
retirement UX beyond the CLI affordance (the record itself ships in P0), or
population calibration. It defines and tests the
target-version authorization boundary the later controller must call; P1 builds
the learner-facing depth objects and behavior on these tables rather than
replacing them.

---

## 2. Verified code-truth ledger

These are observations of the current tree, not assumptions. Implementation
must update this table as code disproves or closes an entry.

| Area | Current reality | P0 disposition |
|---|---|---|
| Grader channel | `probe_families.py:28-36,56-62,413-430` uses point ordinal likelihoods, pseudo-count 8, and fixed symmetric 0.90/0.80 channels. | Replace new-version reads with versioned asymmetric Dirichlet channel models; preserve the constants only as heuristic prior means for legacy backfill. |
| Probe submission | `probe_episodes.py:1418` composes likelihoods without the persisted attempt's `grader_confidence`; the observation records policy/source/outcome, not the resolved matrix or model version. | **Done 2026-07-19 (probe robust cutover):** under mvp-0.8 the episode pins a calibration channel at open (`probe_episodes.enter_episode` -> `probe_robust.resolve_episode_channel`, migration 071 columns), snapshots the versioned probe->coarse mapping on the administration raw grade event (§3.1), and persists the decision-time `observed_update` posterior + channel pin (invariant 3). Legacy mvp-0.6/0.7 keep the point path byte-identical. |
| Probe replay | `probe_episodes.py:1169-1201` rebuilds likelihoods from the current `grader_policy` default. A code/config change can therefore reinterpret an old observation without naming that change. | **Done 2026-07-19 (probe robust cutover):** the mvp-0.8 decision-time posterior + robust products are snapshotted (per-observation `features.robust`, per-presentation `channel_pin`) and replay reads the content-addressed pinned channel, never the active head; a newer model is the separate named reinterpretation projection (`p0_projection.record_reinterpretation_if_changed`). Legacy replay stays byte-identical (`test_probe_robust_cutover.py::test_legacy_mvp07_episode_is_byte_identical`). |
| Probe regrades | `probe_audit.py:443-556` records original-vs-regrade agreement. Both labels are grader outputs; neither is adjudicated `Z`. | Keep the pairs as disagreement telemetry. Only adjudicated anchors train authority-grade confusion rows. |
| Probe family calibration | `probe_families.py:1624+` treats posterior-weighted latent labels as `real_learner` fractional counts. | Rename/segregate as exploratory EM. It cannot promote calibration status or narrow authority intervals. |
| Mastery | `attempts.py` resolves observation reliability and passes it into the mastery update. | Preserve this working path; source its reliability from the calibrated interpretation for new writes. |
| Certification | `canonical_projection.py:265` derives mass from attempt type only. `repositories.py:3153-3202` does not select `grader_confidence`, a raw grade event, or calibration lineage. | Feed the projector a resolved effective observation and discount mass by calibrated outcome certainty. |
| Grade history | Grading evidence is append/supersede, but deferred regrade also rewrites grade summary columns on `practice_attempts`; probe posterior rows do not follow that correction. | Make raw grade events authoritative. Treat attempt summary fields as a cache and rebuild every affected projection from current non-superseded interpretations. |
| Assessment contract | `assessment_contracts.py:70-136` hashes prompt, expected answer, rubric semantics, targets, and fingerprint into one object. | Split semantic card contract, exact surface, and administration snapshot hashes. |
| Goal target | `vault/models.py:46+` has mutable facet scope, recall threshold, due date, and exam settings, but no confirmed terminal-contract versions or exemplars. | Add immutable terminal-contract versions; consumers pin version ids, not mutable goal content. |
| Exam freeze | `exam_session.py:99-165` freezes learner predictions at exam start. `exam_pool.py:105-172` reserves by mutable `goal_id`. | Keep prediction snapshots, but separately pin the terminal-contract version at assessment reservation. |
| Assessment burn | Completed exam items are attempted and then released to practice. Attempt history incidentally prevents re-reservation, but there is no explicit surface, feedback, pristine, or burn ledger. | Enforce held-out eligibility from one append-only exposure/lifecycle ledger across purposes. |
| Constant status | Numeric decision defaults are plain TOML/Pydantic/module constants; there is no calibration-status registry. | Classify every production numeric parameter and require calibration metadata for every decision parameter. **Done 2026-07-18 (P0.5):** `services/parameter_registry.py` + migration 069; audit clean over all 298 config numeric leaves + 29 module constants (`tests/test_registry_audit.py`). |

The line numbers above are audit anchors, not durable API references. Tests must
assert behavior; the spec must not rely on line numbers staying fixed.

---

## 3. Durable contracts and storage

All new JSON is canonicalized with sorted keys and content-hashed. Every table
uses ULID identity, UTC timestamps from `clock.py`, and repository-only SQL.
The migration number is allocated from the next free number at implementation
time; do not assume the current uncommitted migration tail is stable.

### 3.1 Coarse outcome schemas

Every card version names an immutable `outcome_schema_id` and version. An
outcome schema contains three or four mutually exclusive true classes and the
same observed-class vocabulary:

- `success`;
- one card-declared `signature_error` class when the card is designed to
  recognize a specific misconception, otherwise `partial_success`;
- `other`;
- optional `unanswered`.

Long-form criterion grading may retain rich criterion evidence, but the grader
channel consumes the coarse class. The deterministic classifier from rich
rubric output to `G` is versioned and snapshotted on the administration.
Unclassifiable output maps to `other`; it never silently maps to failure or
success. A card requiring more than four diagnostically relevant outcomes must
be split or rejected by the card gate.

Certification additionally classifies each graded rubric criterion into the
four-class schema `full`, `partial`, `none`, or `unassessable`. A
multi-criterion response therefore has one coarse response emission for
diagnosis plus one coarse emission per criterion for certification; it does
not create a fine-grained global outcome alphabet. Each schema version defines
the class-to-score-fraction mapping used by `EffectiveObservation`.

### 3.2 Grader identity and calibration model

`grader_identity` is the tuple:

```text
provider + model/revision + grading prompt version + output schema version
```

The calibration context fixed before selection is:

```text
grader_identity x rubric/outcome-schema type x domain x declared response-length bucket
```

The card declares its expected response-length bucket before EIG is computed;
that declared bucket is pinned on the administration so selection and update
cannot silently resolve different channels. The launch buckets are `0`,
`1-50`, `51-200`, and `201+` words. The raw response's exact Unicode word count
is also stored for calibration residuals; a systematic declared-vs-observed
mismatch forces a card successor rather than retroactively switching the
channel. Bucket boundaries are decision parameters with `heuristic` status.
Domain is the canonical subject id; absent or multi-domain content resolves to
`global` and is disclosed in the model scope.

The grader's emitted confidence is bucketed as `unknown`, `low` (`<0.40`),
`medium` (`0.40-0.79`), or `high` (`>=0.80`). These launch boundaries are
registered heuristics. Calibration models store the joint emission
`P(E=(G, confidence_bucket) | Z, context)`; their reported class-confusion
matrix is its marginal `P(G | Z, context)`. Selection integrates over every
possible emission and update conditions on the emission actually observed.

Create immutable `grader_calibration_models` with:

- identity, semantic version, parent model id, and content hash;
- exact scope and ordered backoff chain;
- outcome-schema id/version;
- one Dirichlet alpha row for each `Z`, representing joint
  `P(E | Z, context)`;
- calibration status and uncertainty/provenance metadata;
- disjoint source counts for `heuristic_prior`, `planted_sim`,
  `exploratory_em`, `adjudicated_anchor`, and `held_out_evaluation`;
- prequential log-loss, multiclass Brier, reliability bins, sample counts, and
  the time range used;
- activation and retirement events; model rows themselves never mutate.

Resolution partially pools the most specific available scope toward this fixed
parent order:

```text
global schema prior
  -> grader identity
  -> rubric/outcome schema
  -> domain
  -> response-length bucket
```

Missing children inherit the parent posterior; they do not fall back to a
point estimate. The existing symmetric 0.90/0.80 means seed the corresponding
heuristic grader-identity priors with deliberately wide Dirichlet intervals.
The prior concentration is a registered heuristic parameter and must pass the
planted-misgrade sensitivity suite before it can be labeled
`simulation_validated`.

Status semantics:

- `heuristic`: authored prior, widest intervals, hypothesis claims phrased as
  best-supported alternatives rather than fact;
- `simulation_validated`: planted learners show the mechanism reacts in the
  right direction; interval authority does not narrow from simulation alone;
- `live_calibrated`: a reviewed artifact has adjudicated anchors plus held-out
  prequential scores for its declared scope. Promotion is an explicit
  activation event with an evidence manifest, never an automatic consequence
  of self-fit.

No universal sample count silently grants `live_calibrated`. The evidence
manifest and scores are mandatory, and the reviewer records the scope for which
they are sufficient. A narrower live model may pool toward a heuristic parent;
the resulting interval must expose that parent contribution.

### 3.3 Raw grade, interpretation, and adjudication events

Create these append-only records:

**`raw_grade_events`**

- attempt/response and administration ids;
- role: `primary`, `recheck`, `independent_confirmation`, or `human_grade`;
- grader identity and agent-run/provider provenance;
- exact raw structured output, criterion evidence, observed class `G`, model
  confidence, criterion-level observed classes, and classifier versions;
- context features used for calibration, including exact response length;
- optional predecessor event when correcting malformed ingestion.

**`grade_interpretations`**

- raw grade event id, calibration model id/hash, projection algorithm version;
- channel posterior/snapshot identity;
- calibrated response-level and criterion-level `P(Z | E, context)` values and
  their reference-prior ids;
- certainty discount, credible interval, review/influence flags, and
  quarantine state;
- the current interpretation is selected by append-only activation/supersession
  events, not by deleting an older row.

`P(Z | E)` is stored for certification and explanation. Diagnostic Bayes
updates must **not** feed that posterior back as a likelihood. They always use
the generative channel `P(E | Z)` composed with the card's `P(Z | H)`.

**`grade_adjudications`**

- the set of raw grade events reviewed;
- adjudicator source (`human_owner`, `independent_expert`,
  `learner_clarification`, or `deterministic_key`);
- resolved point class or distribution over `Z`, rationale, and provenance;
- bounded-trust weight for learner clarification;
- superseded adjudication id when corrected.

An adjudication appends a new interpretation and triggers affected projection
rebuilds. It never overwrites the response, raw grader output, earlier
interpretation, exposure, or historical decision trace.

Rechecks are not assumed independent. Until a joint repeated-grade channel is
calibrated, two outputs are stored separately and agreement is telemetry only;
their probabilities are never naively multiplied.

Append grade activation, quarantine, adjudication, model activation, and
reinterpretation transitions to a dedicated `measurement_events` ledger. Do
not extend `content_events` with learner-interaction telemetry. Current
interpretation/model heads are rebuildable projections of this ledger.

### 3.4 Terminal-contract versions

The confirmed terminal contract contains the complete Layer-5 terminal shape:

- kind, purpose, due date, and burden bounds;
- target exemplars and their relative weights;
- required facets/capabilities and task types;
- complexity/span, transfer-distance, representation, and response-form ranges;
- tool, open-book, collaboration, time, and other administration conditions;
- held-out/practice eligibility;
- acceptable performance and evaluation rubric;
- the named baseline depth milestone and, when enabled, the learner-confirmed
  DepthPolicy/DepthEnvelope version governing permitted terminal-support growth.

The depth envelope is multidimensional, not a single difficulty ceiling. Its
canonical snapshot bounds capability/target additions; complexity, span, and
transfer; representation and response changes; scaffold fade; tool/open-book/
time conditions; cumulative burden; and the ordered reviewed milestone edges
that may be activated. P0 validates the snapshot/hash and authorization
provenance. P1 owns the commitment-level objects and P2/P4 decide when an edge's
evidence gate is met.

Before confirmation this is a mutable draft with no version id and no consumer
may pin it. `confirm_goal_contract` validates at least one exemplar and a
reviewed target blueprint, then appends v1.

Create immutable `goal_contract_versions` with goal id, integer version,
predecessor id, canonical contract JSON/hash, `support_hash`, `change_class`,
author/reason, and creation time. Maintain the current head as a projection.
The SQLite version/event ledger is authoritative for confirmed contracts and
consumer pins. `goals.yaml` retains the editable pre-confirmation draft and a
controlled-writer mirror of the confirmed head id for portability; direct YAML
edits never mutate a confirmed version and must be explicitly confirmed as a
successor before a consumer can pin them.
The service, not the caller, computes change class:

- `support_change`: changes exemplars, required capabilities, task types,
  eligible response/representation ranges, or administration conditions;
- `authorized_depth_step`: a `support_change` wholly contained by the active
  learner-confirmed DepthEnvelope and matching exactly one reviewed milestone
  edge; it additionally records envelope version, predecessor milestone,
  triggering evidence/decision receipt, and burden delta;
- `evaluation_change`: changes acceptable performance or rubric semantics
  without changing task support;
- `reweight`: changes only relative weights inside unchanged support;
- `metadata`: changes purpose wording, dates, or burden metadata without
  changing task distribution or evaluation.

Every post-confirmation material edit appends a successor, including metadata.
`support_change` and `authorized_depth_step` mark existing reserves against an
older support hash unrepresentative for claims about the new head. Other
successors keep the old surface sample representative, but certifications always
cite the exact version they evaluated and current goal status is reprojected
rather than silently inherited.

`append_authorized_depth_successor` fails closed unless the predecessor is the
current head, the active envelope version is unchanged, the edge is reviewed,
all changed contract dimensions are inside it, and the cited progression
decision has qualifying evidence. It commits at most one edge. A proposed
outside-envelope or unreviewed change is persisted as a non-pinnable draft and
requires an explicit learner-confirmed envelope/contract successor.

Achievement is version-relative and monotone as history: appending a deeper
head never revokes or relabels a valid certification of an earlier milestone.
The current projection may say that a deeper milestone is now in progress, but
must also expose the exact previously reached milestone and certification.

Consumer pins:

- probe episode: pin exact contract version at episode open;
- assessment reserve: pin exact version and support hash at reservation;
- terminal certification: cite the assessed version;
- practice progression: read head at each decision, log the evaluated version
  in its trace, and hold no cross-decision pin;
- depth transition: compare-and-append one authorized successor against the
  evaluated head/envelope, then require a new reserve for the deeper support.

An edit during an episode or assessment never changes that consumer's pin.

### 3.5 Minimum final activity substrate pulled into P0

P0 creates the final generic substrate now so burn and lineage do not land on
temporary exam-only tables:

- `activity_families` and immutable `activity_family_versions` — stable family
  identity; authoring purpose is one of `diagnostic`, `instructional`,
  `practice`, `assessment` and never changes;
- `activity_cards` and immutable `activity_card_versions` — stable executable
  identity plus generic ActivityContract; lineage records `minor_successor` or
  `fork`, and certification never crosses a fork;
- `activity_surfaces` — exact prompt/parameters/media/answer-key artifact,
  bound to one card version with `surface_hash` and shared evidence fingerprint;
- `activity_administrations` — fully resolved card + surface + context + policy
  snapshot, including target-contract pin, grader-model/selection-policy pins,
  assistance/tool/feedback conditions, and `administration_snapshot_hash`;
- `activity_exposure_events` — rendered, submitted, feedback revealed,
  externally reported exposure, and shared-stimulus exposure;
- `activity_observations` — joins one response/attempt to its raw grade events,
  active interpretation, and purpose-specific evidence eligibility;
- `activity_surface_lifecycle_events` — reserve, release-unseen, expose,
  consume, quarantine, retire, and practice-successor-minted.

Hash boundaries are strict:

- `card_contract_hash`: semantic target, response contract, rubric semantics,
  task regime, feedback policy, and evidence eligibility;
- `surface_hash`: exact visible wording, parameters, media, and surface-specific
  answer material;
- `administration_snapshot_hash`: resolved card + surface plus target version,
  context, and all decision/model versions.

The existing `assessment_contract_versions` table becomes a compatibility
source. New presentations use the split hashes. P1 adds commitment ownership,
practice scheduling state, and general authoring flows without renaming or
replacing these records.

### 3.6 One exposure and fingerprint ledger

Every purpose writes to `activity_exposure_events`. Held-out eligibility checks
the shared ledger, never an exam-only or practice-only history:

1. exact `surface_hash` exposure is a hard collision;
2. shared-stimulus or fingerprint collision is a near-clone collision and
   disqualifies an "unseen" claim;
3. an unresolved leakage-gate finding or quarantine disqualifies assessment;
4. absence of system-recorded exposure means "unseen in LearnLoop," not a
   claim that the learner never encountered it elsewhere.

The eligibility decision and collision reasons are snapshotted at reservation
and checked again atomically before render.

Purpose-specific exposure behavior is enforced from launch: rendering a
diagnostic surface consumes it forever for diagnosis; rendering an assessment
surface consumes its unseen status under §4.5; instructional/practice exposure
does not consume the object but does enter the shared familiarity ledger and
can therefore block a later near-clone assessment claim. Instructional
administrations are categorically ineligible for unassisted certification.

### 3.7 Retirement record

The bare `retire` lifecycle event is not enough. Retiring a card or surface
additionally appends a `retirement_records` row:

- retired object (family/card/surface id + version) and scope;
- reason from the umbrella L0 taxonomy: too easy, ambiguous, missing context,
  duplicate surface, wrong granularity, no longer relevant, bad underlying
  explanation, superseded by better activity, "should be reference not
  memorized", "I don't care enough to retain this", "I knew the prompt, not
  the concept";
- optional replacement-proposal hook (a proposed successor card/surface or a
  family-redesign request; non-binding);
- provenance (learner action, affect-signal escalation, or owner tooling).

Architecture already guarantees evidence survival (facet-level evidence,
immutable ledger); the record makes the reason queryable and feeds
`interaction_events`. Retirement never deletes learner state, facet evidence,
source relationships, or goals.

### 3.8 Interaction-event envelope

P0 creates the typed `interaction_events` envelope (migration + writers) for
the Layer-5 corpus — explicitly **not** an extension of `content_events`,
which stays a closed content-mutation audit stream. Logged from day one:
attempt durations (review-burden accounting, feeding stop-mode cost) and
retirement reasons (§3.7); affect-tap signals (§4.6) also land here. P3 adds
reading-event kinds to the same envelope. Unlogged interaction data is the
one irreversible loss in this plan, so the envelope ships before any consumer
exists ("log now, model later").

---

## 4. Measurement behavior

### 4.1 Grade resolution pipeline

For every graded response:

1. Resolve or create the administration before showing the surface.
2. Append the response/attempt and exposure facts.
3. Append the raw grader event without updating a posterior or certification.
4. Classify rich grader output into observed class `G` using the administration's
   classifier version.
5. Resolve the most specific calibration model and its parent mixture.
6. Append a grade interpretation with `P(Z | E)`, interval, certainty discount,
   and calibration status.
7. Run influence checks. If the conclusion is fragile, request a recheck,
   independent confirmation, or learner clarification; do not force a branch.
8. Rebuild diagnostic/certification projections from the event ledger.
9. Materialize legacy attempt summary fields only as compatibility cache output.

If no scoped calibration model exists, use the global wide heuristic prior and
record the fallback. Missing calibration can reduce authority to nearly zero;
it cannot cause a crash or silently restore the old 0.90 point channel.

### 4.2 Robust diagnostic selection and posterior update

For calibration model draw `m` and observed grader emission `E`:

```text
P_m(E | H) = sum_z P_m(E | Z, context) * P(Z | H, card)
```

Candidate EIG and the observed posterior update use this same composition.
The model's Dirichlet posterior is evaluated with a deterministic ensemble:
posterior mean plus 128 draws seeded from the calibration-model hash and the
decision-context hash. The robust statistic is the empirical 10th percentile.
Draw count and quantile are registered decision parameters, initially
`heuristic`; the planted-learner suite is the mechanism gate for promoting
them to `simulation_validated`.

The ensemble also perturbs the hand-authored instrument tables
`P(Z | H, card)` — a Dirichlet draw around each point row, with concentration
a registered `heuristic` parameter — so robust statistics reflect uncertainty
in the likely larger error source, not grader noise alone. This axis is
**robustness analysis, not calibration**: it does not discharge the
umbrella's weak-priors commitment (U-014). The hierarchical
instrument-likelihood model is deferred with a named resume path — card-level
outcome counts are logged per spent surface, and events-authoritative replay
makes the later upgrade retroactive.

Ranking uses robust EIG per expected second. Stopping uses robust net value,
not the per-second rank:

```text
LCB(EVSI) <= lambda_time * expected_seconds + burden_cost
```

`lambda_time` and `burden_cost` are registered decision parameters:
`lambda_time ≡ 1` under the minutes cost numéraire (U-023) and `burden_cost`
is denominated in minutes.

The winner is robust only when the 10th percentile of its per-second advantage
over the runner-up is positive. Otherwise the selector abstains, asks for a
stronger instrument, or stops with "couldn't reliably distinguish." A
diagnostic action may fire only when the same next action wins in at least 90%
of ensemble projections; this agreement threshold is a registered heuristic
parameter. Abstention itself carries a budget (U-021): "diagnostician
abstains in at most X% of episodes" is a registered, monitored decision
parameter — the planted-learner suite chooses prior concentrations that meet
the budget, and live abstention above it raises an audit alarm instead of
surfacing as ambient timidity. Under a heuristic channel, UI/API claims
expose status, the leading
hypothesis interval, and named alternatives.

The episode stores two products:

- immutable decision-time posterior snapshots using the episode-pinned target,
  card likelihood, grader channel, and selection policy;
- a current reinterpretation projection under a named later model version.

If reinterpretation changes the leading actionable conclusion, append a
`measurement_reinterpretation` event and rebuild current downstream state. Do
not rewrite what the system chose historically.

### 4.3 Reliability-aware certification

Canonical certification consumes an `EffectiveObservation`, not raw attempt
columns. For a coarse outcome distribution `p(z)`, define:

```text
certainty = 1 - H(p) / log(number_of_possible_classes)
```

Use the lower credible bound of certainty across the calibration ensemble.
Deterministic or point-adjudicated outcomes have certainty 1. An uninformative
uniform interpretation has certainty 0 and contributes no certification mass.

For each criterion:

```text
effective_mass = attempt_type_mass
               * assistance_discount
               * familiarity_discount
               * certainty_LCB

positive_mass = effective_mass * E[true_score_fraction]
negative_mass = effective_mass * (1 - E[true_score_fraction])
```

Existing correlation-group budgets, dependency localization, and attempt caps
apply **after** reliability discounting. Reliability never creates mass. An
unassessable criterion contributes neither positive nor negative mass.

`canonical_observation_ledger()` must return administration, active grade
interpretation/adjudication, grader/calibration lineage, target-contract pin,
and quarantine status. Quarantined observations contribute zero until an
append-only resolution activates a new interpretation.

Mastery already consumes an observation-reliability path. New-version writes
feed it the same certainty result so mastery and certification cannot disagree
about grader trust. FSRS remains a predictive scheduling model, not a
certification source; P0 logs its use of the observed grade in the projection
trace and forbids terminal claims derived from FSRS state.

### 4.4 Review, contest, and quarantine

Trigger review when any of these is true:

- grader self-confidence is below the existing 0.40 review threshold;
- the leading diagnosis, next action, or certification threshold changes
  across the robust ensemble;
- two grade events disagree on coarse class;
- the learner marks `ambiguous` or `misgraded`;
- a response would create or revoke terminal certification by itself.

The 0.40 threshold remains `heuristic` until calibrated; the influence tests,
not that scalar alone, govern consequence.

Automatic low-confidence/high-influence review leaves the bounded
interpretation active, but fragile actions fail the robust action gate. A
learner contest or explicit ambiguity immediately appends quarantine events for
the grade interpretation and surface; the observation has zero current
diagnostic/certification authority until adjudicated. The raw history remains
visible.

A same-grader recheck may detect disagreement but cannot narrow intervals by
itself. High-influence disagreement requires an independent grade, a
deterministic key, human adjudication, or bounded-trust learner clarification.

### 4.5 Assessment reservation, burn, and certification

Reservation:

- samples from the pinned target contract's frozen distribution even when
  predicted success is low;
- requires an assessment-purpose family/card/surface;
- records the target version/support hash and eligibility check;
- does not burn an unrendered surface. Cancellation may append
  `release_unseen`, returning it to pristine availability only if no exposure
  event exists.

Render is the atomic burn boundary for unseen status. Immediately before
render, recheck global exposure/fingerprint collisions and target-head support
compatibility. On success append `expose` and create the administration. A
rendered, abandoned, timed-out, or unanswered surface is no longer pristine.

Submission and feedback:

- a successful assessment consumes the surface permanently for terminal
  assessment;
- a failed or unanswered exposed surface also cannot mint fresh/unseen
  terminal credit again;
- feedback revealed before response makes the administration ineligible for
  terminal credit;
- feedback after failure appends a burn event. If useful for practice, P0 may
  append a practice-successor proposal; P1 may mint that linked
  practice-purpose surface/card with an explicit `not_before`. Never change the
  assessment purpose or requeue the original as assessment;
- regrade success-to-failure or failure-to-success changes certification only.
  It never reverses exposure or burn.

Certification cites the pinned target version and administration. If the goal
head has a different support hash, the result may still certify the older
version but must be labeled unrepresentative of the new head; a fresh reserve
is required for a claim about the new support. Reweight/evaluation/metadata
successors are reprojected according to their declared compatibility, with no
silent citation rewrite.

### 4.6 Affect tap

One optional touch on any activity, never required, never interrupting —
typed validity constraints, not a reward function (umbrella L0, U-010). P0
captures the full vocabulary as `interaction_events` and implements the
semantics whose targets P0 owns:

- `cue gave it away` -> substantial certification-evidence discount on that
  observation;
- `ambiguous` / `misgraded` -> quarantine the surface and interpretation
  (§4.4) and enter the error-intake stream (§4.7);
- repeated `felt rote` -> retire or redesign the *family* via the retirement
  record (§3.7), not a priority tweak;
- `not worth my attention` -> a commitment/burden-contract edit — never
  interpreted as low ability;
- `meaningful connection` / `wanted more depth` -> salience and depth-preset
  signals.

Commitment-level actions (pause / burden edit) bind when P1's commitment
objects land; the signals are captured from P0 regardless. The
`auto_within_envelope -> suggest_next` auto-downgrade *enforcement point*
(U-011) is deferred to the auto-depth package (U-018) — capture is live now
precisely so the package's dead-man switch arrives with calibrated signal
mileage. Emotional signals gate validity and learner intent; they are never
optimized as a reward.

### 4.7 Calibration streams and bootstrap

Three streams, never conflated (U-020):

- **Error intake** — the `misgraded`/`ambiguous` tap. Missing-not-at-random
  by construction: conspicuous errors get reported, ordinary correct grades
  are never confirmed. It discovers failure modes and feeds adjudication; it
  never supplies a calibration denominator.
- **Calibration stream** — stratified random adjudication with logged
  inclusion probabilities: oversample low-confidence, high-influence, and
  partial-credit-boundary attempts, then reweight by inverse inclusion
  probability to recover unbiased confusion estimates. Influence
  prioritization is the stratification design of this stream, not a separate
  stream; every attempt keeps a known nonzero inclusion probability.
- **Individual anchors** — structured learner corrections
  (`learner_clarification` adjudications) are authority-grade single
  datapoints under bounded trust.

**Bootstrap (early P0 step):** one retrospective owner-adjudication session
over a stratified sample of the existing attempt history seeds the first
adjudicated-anchor counts. The sampling frame and inclusion probabilities are
logged so the batch composes with the ongoing stream instead of becoming a
differently-biased blob.

---

## 5. Service and read interfaces

Business logic lives in `src/learnloop/services`; SQL remains in
`db/repositories.py`. Sidecar and CLI are thin adapters over the same services.

Required service boundaries:

- terminal contracts: confirm draft, append successor, append/validate one
  authorized depth successor, resolve head, compare support/envelope, and list
  consumer pins;
- activities: resolve legacy item to family/card/surface, reserve surface,
  open administration atomically, append exposure/feedback/lifecycle events,
  and evaluate held-out eligibility;
- grading: append raw grade, classify `G`, resolve calibration model, interpret
  grade, request review, and append adjudication;
- projections: replay an episode under its historical pins, reinterpret under
  an explicit current model, rebuild canonical certification, and emit
  correction events;
- calibration: build model candidate from allowed sources, evaluate held-out
  metrics, activate/retire a version, and audit decision-parameter coverage.

Every diagnostic/assessment read DTO that exposes a conclusion includes:

```text
calibration_status
calibration_model_version_id
projection_algorithm_version
target_contract_version_id (when goal-conditioned)
point estimate + interval
claim_language = provisional | calibrated
review/quarantine state
surface eligibility/burn reason (for assessment)
```

CLI parity required for P0:

- inspect a measurement receipt from response through projection;
- list pending grade reviews and adjudicate one;
- show/compare terminal-contract versions and pinned consumers;
- audit a surface's exposure/burn history;
- retire a card/surface with a taxonomy reason and inspect the surviving
  evidence (Journey 12 at CLI level);
- run calibration/decision-parameter audits and planted-misgrade simulation.

No P0 command directly edits a projection table.

---

## 6. Calibration-status registry

The selected boundary is **decision parameters**, not every numeric literal.
A production numeric value is a decision parameter when changing it with the
same authoritative events can change any of:

- evidence eligibility or mass;
- a posterior, uncertainty interval, or certification result;
- candidate ranking, stopping, routing, or next action;
- surface lifecycle/held-out eligibility;
- a learner-facing diagnostic or readiness claim;
- a calibration admission/promotion/retirement decision.

Mathematical identities, schema validation bounds, enum/version numbers,
serialization constants, display formatting, and test fixtures are not
decision parameters.

Implement a machine-readable registry keyed by stable parameter path. Each
entry contains effective value/hash, source (`default`, `vault_override`,
`fitted`, or `model_artifact`), status, rationale, scope, evidence refs, owner,
and last review time. Numeric config fields and named module-level constants are
explicitly classified as `decision` or `structural`; unclassified candidates in
those two inventories fail the audit. Any inline numeric that meets the
decision-parameter definition must first move to a named registered parameter;
mathematical/structural literals are not individually inventoried. Every
`decision` entry must have registry metadata.

Rules:

- changing a value without matching evidence metadata demotes that effective
  value to `heuristic`;
- simulation can promote only to `simulation_validated`;
- `live_calibrated` requires an activated real-outcome evidence manifest;
- policy/administration snapshots store the ids and effective-value hash of all
  decision parameters they consumed, not a copy of the whole config;
- legacy algorithm versions keep a frozen registry manifest so replay remains
  reproducible.

Lifecycle (U-022 v2): each registered parameter is `active`, `dormant`, or
`deleted`. `active` requires a **sensitivity certificate** — a *coverage*
artifact (descriptive, not pass/fail), keyed to (parameter path, effective
value hash, swept plausible range), documenting where in the range decisions
actually flip. Finding flip points does **not** invalidate it — that is its
purpose; a value change outside the covered hash does (it needs a re-sweep).
Coverage is required for **every** `active` decision parameter regardless of
calibration status; an `active` parameter without valid coverage is
`active_pending_certificate` — enumerated debt (a warning in the ordinary
audit, a failure in the strict release gate), never silently red.
Status promotion beyond `heuristic` is gated separately by **promotion
evidence** (normative): sim evidence — including the `decision_stable` refusal
that declines to promote a knife-edge value — gates `heuristic →
simulation_validated`, and the activated real-outcome evidence manifest gates
`→ live_calibrated`. `dormant` freezes the value at its default, excludes it
from tuning *and from decision claims*, and mandates **bind-event logging** —
an unmonitored guardrail is dead code; dormant parameters need no coverage
certificate (dormancy is the explicit alternative to sweeping). `deleted` is
allowed only after coverage demonstrates the parameter's semantics are
redundant. The rule is class-asymmetric: an inert *shaping weight* is a
deletion candidate; an inert *constraint parameter* defaults to
dormant-with-monitoring — the sim-sweep found weights inert while membership
and caps did the work.

The first audit must cover all `LearnLoopConfig` fields plus point constants in
probe likelihood/channel code. It may explicitly classify excluded structural
values, but it may not ignore them through an open-ended allowlist.

---

## 7. Migration and compatibility

### 7.1 Backfill

Backfill deterministically and idempotently:

1. Each existing PracticeItem becomes one default legacy practice family,
   card/version, and fixed surface. When the same legacy item was used for a
   probe or exam, create a purpose-specific diagnostic or assessment adapter
   card/surface referencing the same legacy source and exact `surface_hash`;
   never change the default object's purpose. The shared exposure ledger keeps
   these adapters from manufacturing novelty.
2. Split every `assessment_contract_versions` row into semantic card and exact
   surface artifacts. Store a mapping from legacy contract id to both new ids.
3. Existing probe family templates/instrument-card snapshots map to
   diagnostic-purpose family/card versions. Probe presentations become
   administrations and exposure events without changing their historical ids.
4. Each historical attempt gets a synthetic administration and exposure at its
   recorded time. When exact historical surface content is unavailable, mark
   `legacy_surface_unverifiable`; preserve its old replay but grant no new
   pristine terminal credit.
5. Convert current attempt/evidence/regrade history into raw grade events and
   interpretations tagged `legacy_summary`. Preserve agent-run provenance when
   present. Never pretend a model-vs-model regrade is an adjudicated anchor.
6. Completed `exam_attempt` surfaces become consumed assessment surfaces.
   Active unrendered exam-pool rows become reservations only when a confirmed
   target contract can be pinned; otherwise keep them as `legacy_provisional`
   and forbid new terminal claims.
7. Seed heuristic calibration models from the old policy means and register all
   old constants with `heuristic` status.

### 7.2 Dual-write and read cutover

During P0, current PracticeItem/probe/exam entry points dual-write the new event
substrate and existing compatibility rows in one transaction. New-version
projectors read only new authoritative events. Existing UI/read paths may read
materialized legacy fields until their DTO cutover.

`practice_attempts.rubric_score`, `correctness`, `grader_confidence`, and
`manual_review*` become documented current-grade caches. Projectors must prove
they can rebuild after those cache values are corrupted in a test. New regrade
code appends events then refreshes caches; it never uses cache mutation as the
correction itself.

Legacy mvp-0.6 replay remains byte-identical. Existing mvp-0.7 history can be
read through a named compatibility projection; activating the P0 projection
creates a `derived_state_rebuilds` record and never rewrites raw history.

### 7.3 Failure behavior

- missing calibration scope -> inherit wide global heuristic model and disclose;
- missing/invalid coarse class -> `other`, review flag, no silent success;
- missing target pin -> no goal-conditioned terminal claim;
- missing/stale depth authorization, unreviewed edge, or envelope crossing ->
  reject automatic successor, preserve proposal as non-pinnable draft;
- authorized depth support change without a fresh deeper reserve -> practice may
  continue, but no terminal claim for the deeper head;
- target support changed after reservation -> mark unrepresentative; do not
  silently retarget or destroy the old reserve;
- exposure collision at render -> refuse assessment administration and replace
  with a fresh eligible surface;
- feedback before response -> retain learning event, zero terminal credit;
- calibration/model activation during episode -> next episode only for
  decision-time behavior;
- disputed/quarantined grade -> zero current authority until resolution;
- projection failure -> leave last good named projection readable, record the
  failed rebuild, and never partially update derived tables.

---

## 8. Implementation order

1. **P0.0 — executable baseline.** Add characterization tests for every row in
   §2, including the already-correct mastery reliability path.
2. **P0.1 — final lineage substrate.** Add activity/target/event schemas,
   contract split, hashes, exposure/lifecycle projector, legacy adapters, the
   retirement record (§3.7), and the `interaction_events` envelope (§3.8).
3. **P0.2 — grader channel.** Add coarse schemas, raw grade/adjudication events,
   asymmetric hierarchical calibration models, and deterministic model
   resolution. Run the retrospective owner-adjudication bootstrap (§4.7) as
   soon as models exist.
4. **P0.3 — authority propagation.** Replace point probe likelihoods with
   pinned robust composition; feed EffectiveObservation into canonical
   certification and mastery; add reinterpretation/rebuild receipts.
5. **P0.4 — target, depth, and assessment enforcement.** Confirm/version target
   versions and depth-envelope snapshots, validate one-edge authorized depth
   successors, pin episodes/reserves, enforce support-change flags, global
   exposure checks, and monotone burn.
6. **P0.5 — calibration discipline.** Land the parameter registry/audit,
   adjudication queue, held-out scoring reports, planted-misgrade harness, and
   compatibility cutover.

Each package ends with focused tests and a replay receipt. Do not defer
reliability propagation until after open-world or controller work.

---

## 9. Test and acceptance contract

### 9.1 Channel and grading

- An asymmetric planted channel where partial success is overcalled as success
  produces the expected non-symmetric matrix and posterior direction.
- Candidate EIG and observed update use the identical pinned channel hash.
- Changing active calibration after an episode leaves its historical replay
  byte-stable and creates a separately named reinterpretation.
- The raw numeric model confidence is never multiplied into evidence; only its
  bucket inside the pinned calibrated joint emission may affect interpretation.
- Same-grader agreement does not narrow authority intervals without a calibrated
  joint channel; adjudicated anchors do.
- Exploratory EM rows cannot promote a model to `live_calibrated`.
- Confusion rows update only from denominator-bearing sources (stratified
  adjudications with logged inclusion probabilities, adjudicated anchors);
  MNAR error-intake taps alone never change a confusion row.

### 9.2 Reliability propagation

- Lower calibrated certainty produces a less decisive robust diagnostic
  envelope and less certification mass than a deterministic/adjudicated grade.
- A uniform `P(Z | E)` yields zero certification mass.
- Canonical ledger/projector tests fail if grader/calibration lineage is omitted.
- Existing correlation caps, dependency localization, assistance, and
  familiarity discounts still bind after the reliability discount.
- Corrupting legacy attempt summary grade fields does not change a rebuilt P0
  projection.
- A corrected adjudication reverses current projection through appended events
  while preserving the historical decision receipt.

### 9.3 Bounded heuristic authority

- Under wide heuristic intervals, a planted misgrade cannot silently flip to a
  different consequential action: the action either stays invariant or the
  episode abstains/stops and requests review.
- Narrowing the same model with adjudicated data continuously increases robust
  value/evidence mass; there is no status-gated discontinuity.
- Heuristic claims include alternatives and calibration status; live-calibrated
  claims may use calibrated wording.

### 9.4 Target versions

- A draft cannot be pinned. Confirmation mints v1 exactly once.
- Every post-confirmation edit appends a successor and leaves prior bytes/hash
  unchanged.
- Episode pin is fixed at open; assessment pin is fixed at reservation;
  progression reads the latest head on every new decision.
- Support change flags old reserves unrepresentative of the new head; a pure
  reweight does not.
- Every terminal certification cites the exact target version demonstrated.
- One reviewed transition wholly inside the active envelope appends exactly one
  `authorized_depth_step` successor with its evidence and authorization receipt.
- An outside-envelope, stale-envelope, multi-edge, or unreviewed transition
  cannot become a confirmed/pinnable head automatically.
- A deeper successor preserves the earlier milestone's certification and cannot
  reuse its reserve as fresh proof of the new support.

### 9.5 Surface and burn lifecycle

- Reserve then cancel before render returns a surface to pristine state only
  when no exposure exists.
- Render then abandon, fail, or succeed makes the assessment surface permanently
  ineligible for fresh terminal assessment.
- Feedback before response produces no terminal credit.
- A failed assessment with feedback can append a practice-successor proposal;
  if P1 later mints it, the original purpose and burn state never change.
- Regrade never reverses burn.
- Exact and near-clone exposures from diagnostic/practice paths block an unseen
  assessment claim through the same ledger.
- Two concurrent render attempts can expose/consume a surface at most once.

### 9.6 Migration, replay, and audit

- Migration/backfill is idempotent on a copy of every fixture vault.
- Frozen mvp-0.6 replay remains byte-identical.
- Existing mvp-0.7 projections either match the compatibility projection or
  produce an explicit, inspectable P0 reinterpretation delta.
- All current probe/exam/practice writers dual-write complete lineage.
- Decision-parameter audit has zero unclassified numeric config fields or
  named numeric constants, no known inline decision knobs, and zero decision
  parameters without status/provenance.
- Full pytest, TypeScript typecheck, Rust check, migration tests, and
  `git diff --check` pass.

### 9.7 Product acceptance

The P0 vertical slice passes when:

1. a planted grader confusion that would flip the current point-estimate
   diagnosis instead causes a robust invariant action or an explicit abstention;
2. a learner-contested grade is quarantined, adjudicated append-only, and all
   current projections self-correct with an inspectable receipt;
3. an assessment sampled from a pinned confirmed target cannot reuse an exposed
   or feedback-burned surface and its certification cites that target version;
4. a qualifying inside-envelope depth step creates an auditable successor and a
   new-reserve requirement while the achieved earlier milestone remains visible;
5. every number that granted, withheld, ranked, or stopped measurement authority
   can be traced to a calibration-status registry entry;
6. a bad prompt can be retired from the CLI with a taxonomy reason, its
   evidence visibly survives, and the retirement reason lands in
   `interaction_events` (Journey 12 at CLI level).

---

## 10. Defaults and explicit assumptions

- P0 uses bounded heuristic authority as resolved in the umbrella; it does not
  hard-block the golden path while live anchors accumulate.
- The minimum final P1 activity substrate is pulled forward into P0. P1 extends
  it; no temporary exam-only burn schema is allowed.
- Calibration status applies to decision-affecting parameters only, under the
  objective definition in §6.
- Target versions begin at exemplar confirmation. Material edits are
  append-only successors. Episodes pin at open, assessment reserves pin at
  reservation, terminal certifications cite the assessed version, and practice
  progression follows head.
- Automatic depth is an authorization mode, not an exemption from versioning:
  one reviewed inside-envelope edge may append one
  `authorized_depth_step`; outside-envelope changes require confirmation, and
  every deeper terminal claim requires a fresh reserve.
- Current single-learner data is not population psychometrics. Every calibration
  scope and claim remains learner-local unless a later, separately consented
  design says otherwise.

---

## Change log

### 2026-07-18 — P0.5 calibration discipline landed (mvp-0.8 cutover)

**(a) Probe-alphabet mapping decision (§3.1).** Probe instrument cards are exactly
the "card designed to recognize a specific misconception" case, so a probe's
native outcome vocabulary (`correct_target_reason`, `confuses_*`, …) maps to a
card-declared coarse `outcome_schema` via a **versioned deterministic mapping**
declared per instrument card and snapshotted on the administration:
`success ↔ correct_target_reason`; `signature_error ↔` the card's
confusion-target outcome; `other ↔` residual; `unanswered` where applicable. This
mapping is the sanctioned route for wiring robust selection/update/stop-abstain
into probe episodes under mvp-0.8 while legacy versions stay byte-identical.
*Disposition:* the mapping **decision** is recorded and sanctioned here; the live
wiring into the probe-episode loop is **still open** (see deferrals below) — the
robust machinery (`services/robust_composition.py`) remains a
library-complete-and-tested dependency the wiring will consume.

**(b) Deferrals closed.** P0.1's presentation-backfill and P0.3's
projection-cutover deferrals are closed by the P0.5 cutover: `upgrade_to_mvp08`
freezes the mvp-0.6/mvp-0.7 registry manifests, flips the default read path to the
mvp-0.8 authority-propagation projection, records a `derived_state_rebuilds`
receipt, and never rewrites raw history. New vaults default to mvp-0.8
(`config.DEFAULT_CONFIG_TEXT`); existing mvp-0.7 vaults upgrade via
`learnloop upgrade --to mvp-0.8`; the version gates in
`attempts/doctor/patches/residual_diagnostics/repositories` now treat mvp-0.8 as a
strict superset of the mvp-0.7 canonical model (`CANONICAL_STATE_VERSIONS`).

**(b′) Probe-episode robust cutover — IMPLEMENTED 2026-07-19.** The live probe-episode
robust cutover is now landed. The versioned deterministic probe-outcome -> coarse-class
mapping (`services/probe_outcome_mapping.py`, `PROBE_COARSE_MAPPING_VERSION`) is derived
mechanically per instrument card and snapshotted on the administration (raw grade event
`raw_output.probe_coarse_mapping` + interpretation coarse class). Under **mvp-0.8 only**,
`services/probe_episodes.py` threads the tested robust library
(`services/robust_composition.py`) via `services/probe_robust.py`: the calibration
channel is resolved and pinned at episode open (migration 071 columns +
content-addressed pinned-channel snapshot), the decision-time `observed_update`
posterior and robust EIG-per-second product are snapshotted (invariant 3: selection and
update consume the identical pinned channel hash), the robust stop rule + 90% agreement
gate surface the explicit `couldnt_reliably_distinguish` abstention outcome (U-021), and
replay reads the snapshot while a newer model is the separate named reinterpretation
projection (`p0_projection.record_reinterpretation_if_changed`). The legacy mvp-0.6/0.7
point path stays byte-identical (all `tests/test_characterization_probe_*` pins green;
new `tests/test_probe_robust_cutover.py`). This closes the one carry-over that remained
open after P0.5.

**(c) Cutover completion date: 2026-07-18** — parameter registry + audit,
sensitivity certificates, U-022 lifecycle (active/dormant/deleted) with bind-event
logging, adjudication-queue CLI, planted-misgrade harness, and the compatibility
cutover landed and green under the full pytest suite.

**Interpretation notes** (audit semantics, §6):
- `active_without_certificate` is a violation only when a parameter *claims*
  calibrated authority (status `simulation_validated`/`live_calibrated`) while
  `active` with no matching certificate. A fresh heuristic-active parameter runs
  under bounded heuristic authority (the P0 premise) and needs no certificate;
  simulation is what promotes it, and promotion is what requires the certificate.
- `dormant` constraint parameters declare a symbolic `bind_site`; a dormant
  constraint with no declared bind site fails the audit ("an unmonitored guardrail
  is dead code").
- `robust_composition:LAMBDA_TIME` carries the landed `# decision parameter`
  breadcrumb but is registered **structural/fixed** (minutes numéraire, U-023,
  fixed at 1); the comment-drift check treats a tagged constant as compliant when
  it has any registered spec, so this reclassification is not drift.

- **2026-07-19 — U-022 revised to v2 (owner decision).** Supersedes the
  `active_without_certificate` interpretation above. The single "sensitivity
  certificate" concept is split into two artifacts: the **sensitivity
  certificate** is now a *coverage* artifact required for every `active` decision
  parameter (flip points do not invalidate it; a value change outside the covered
  hash does), and **promotion evidence** is a separate *normative* gate for status
  beyond `heuristic` (sim evidence — carrying the `decision_stable` refusal —
  gates `simulation_validated`; the real-outcome manifest gates `live_calibrated`).
  An `active_pending_certificate` debt state is added: an `active` decision
  parameter lacking valid coverage enumerates as a warning in the ordinary audit
  and as a failure (with the pending list attached) in the strict release gate, so
  the gate is real and the coverage work-down is visible rather than vacuous.

### 2026-07-19 — owner decision: legacy-vault machinery frozen

Old-vault migration is no longer an investment area (owner decision, recorded
in the P1 spec change log): mvp-0.8+ vaults are reinitialized fresh. The P0
backfill (§7.1), compatibility projections, and `upgrade_to_mvp08` remain
green but frozen — no further acceptance work extends them.

### 2026-07-20 — grade dual-write degradation is no longer silent (audit B2)

- `record_grade_dual_write` mints administration identity FIRST (extracted
  `ensure_administration_identity`, also used by `resolve_grade` step 1-2) and
  threads it into its kwargs, so any later pipeline failure anchors a
  `dual_write_degraded` measurement event on the real administration. A failure
  during the mint itself (no anchor exists) logs a warning; the outer
  `_dual_write_grade_channel` guard in attempts.py logs instead of `pass`.
- Semantics change: a poisoned resolve now leaves a persisted administration +
  observation with ZERO interpretations (visible, replay-recoverable debt)
  rather than nothing (`test_dual_write_failure_never_breaks_legacy_path`,
  `test_dual_write_mint_failure_is_logged_not_silent`).

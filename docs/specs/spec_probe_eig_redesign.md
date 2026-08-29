# Probe and EIG Redesign Specification

Status: Proposed; depth contract aligned 2026-07-17  
Scope: Probe philosophy, diagnostic episodes, EIG modeling, probe authoring, UX, persistence, evaluation, and rollout  
Repository: LearnLoop

## 1. Summary

LearnLoop probes should identify the learner state that matters for the next instructional decision. A probe is not merely a difficult Practice Item or an item with approximately 50% predicted success. It is an observation selected because plausible, actionably different learner hypotheses predict meaningfully different responses to it.

The current implementation has strong foundations—locked hypothesis sets, mutual-information scoring, Bayesian updates, facet diagnostics, misconception records, item familiarity, scheduler telemetry, and structured grading—but its effective behavior is usually scalar ability estimation:

- Cold-start hypothesis sets contain only `mastered` and `unfamiliar`.
- Any Practice Item on an in-probe Learning Object can be treated as a probe.
- Ordinary, hinted, `dont_know`, open-text, and exam attempts can advance a probe.
- A single high score can complete a nominal three-observation probe.
- The main scheduler does not use registry misconception discrimination when calculating probe EIG, although posterior replay does.
- Missing local diagnostic items produce repeated inadequacy events without a durable generation workflow.
- The principal Tauri practice experience does not consistently enforce probe measurement conditions.

The redesign introduces a first-class **adaptive diagnostic episode**. It borrows measurement integrity from an exam—fresh surfaces, controlled assistance, explicit progress, reliable grading, and auditable observations—while retaining adaptive item selection after each response.

Probe quality is owned primarily by a versioned **Probe Family Template**, not by each generated item instance. A family defines a reusable measurement pattern and executable response model; an LO-bound Instrument Card binds that pattern to concrete facets and hypotheses; generated or authored Item Instances provide surfaces; and Observation Traces record what occurred. Calibration pools at the family level, while item-specific estimates shrink toward their family posterior.

## 2. Core Philosophy

### 2.1 Definition

A probe is a question or task chosen near a decision-relevant posterior boundary, where plausible learner states predict observably different responses and imply different next instructional actions.

A probe should answer a question such as:

- Should the next intervention target recall, mechanism, procedure selection, or transfer?
- Is the learner unfamiliar, surface-fluent, structurally competent, or holding a specific misconception?
- Is an observed failure local to one facet or evidence of a broader prerequisite gap?
- Can the learner reproduce a familiar response but not generalize it to a shifted surface?

A probe is not defined by its `practice_mode`, difficulty, length, or use of EIG alone. It is defined by an executable observation contract and its role in a diagnostic episode.

### 2.2 Decision-relative boundary

The target boundary is the boundary between learner states that imply different next actions. It is not merely the scalar point at which predicted correctness is 0.5.

For hypotheses `h1` and `h2`:

- If both predict 50% success, an item can have zero information about which hypothesis holds.
- If `h1` predicts 90% success and `h2` predicts 10% success, an equally balanced mixture can have 50% marginal success while being highly diagnostic.

Probe authoring and selection MUST therefore optimize divergence between predicted observations under competing hypotheses, not marginal difficulty alone. A distinction is decision-relevant only when resolving it can change the next instructional action, required assistance, or stopping decision.

### 2.3 Probing versus practicing

Probe selection and practice selection are distinct objectives:

- Probe selection maximizes the expected value of information for an instructional decision.
- Practice selection maximizes expected learning, retention, transfer, or error repair.
- A single item may serve both objectives, but the system MUST NOT assume that maximal information gain implies maximal learning gain.

After a probe localizes a weakness, the scheduler should explicitly transition to practice targeted at that weakness, normally with feedback and scaffolding enabled.

### 2.4 Predictive validity

Posterior concentration is insufficient evidence of a good diagnosis. A misspecified observation model can become confidently wrong.

Probe quality MUST ultimately be evaluated by improvement in predictions on future, fresh-surface learner behavior and by the value of the resulting instructional decision.

### 2.5 Probes locate a depth frontier; they do not raise it

Every goal-conditioned episode is relative to an exact current depth milestone
and the learner's versioned DepthPolicy/DepthEnvelope. Its feasible downstream
actions may include a reviewed next milestone already authorized by
`auto_within_envelope`; they never include an outside-envelope target. EIG is
therefore computed over distinctions that could change an allowed next action,
not over everything the system could ask about at greater depth.

Probe completion cannot itself expand a goal, envelope, card contract, or arc.
It emits evidence and a typed next-action recommendation. P2/P4 records
milestone attainment and calls the P0/P1 successor service only when the
separate progression gate passes. A committed depth transition closes the old
measurement segment; any diagnostic needed at the deeper milestone is a new
episode with new target/hypothesis pins. Durable learner evidence may inform its
prior, but the old posterior is not relabeled as a diagnosis of the new target.

## 3. Product Modes

LearnLoop should distinguish three interaction contracts.

| Mode | Primary purpose | Feedback during sequence | Selection policy |
|---|---|---|---|
| Exam | Certify broad performance | Delayed | Fixed and held out |
| Probe episode | Identify an actionable learner state | Delayed within a short diagnostic block | Predictive information rate within measurement constraints |
| Tutoring | Change the learner state | Immediate | Expected learning value within pedagogical constraints |

Probe mode SHOULD be exam-like in measurement integrity, but MUST NOT become a conventional fixed exam.

During a probe episode, the learner MUST be able to choose **Stop diagnosing and teach me**. This ends the current measurement block and transitions to tutoring. Responses after instructional help MUST NOT be treated as independent evidence about the pre-intervention learner state.

## 4. Current-State Findings

This section records the repository audit that motivates the redesign. Figures are a point-in-time snapshot of the local fixture databases taken 2026-07-12; regenerate them before citing them elsewhere.

### 4.1 Two-state cold-start model

`build_hypothesis_set()` begins with `mastered` and `unfamiliar` and adds only misconceptions already active when the phase opens (`src/learnloop/services/probes.py`). Initial probes therefore lack hypotheses such as surface-only knowledge, procedure-selection failure, neighbor confusion, or transfer gaps.

In the current local fixture databases:

- All 46 stored hypothesis sets contain exactly two states (arxiv 15, law 21, linear_algebra 4, linear_algebra_legacy 6).
- None contains a misconception.
- Active misconceptions can appear after a two-state probe completes, but no automatic re-probe replaces the stale locked set.

### 4.2 Unqualified candidate pool

Initial probe entry requires only an active local Practice Item. While an LO is in probe state, the scheduler computes probe EIG for every active item on that LO, regardless of whether the item was designed to discriminate the active hypotheses.

### 4.3 Selection/update mismatch for registry misconceptions

The probe service can resolve item-specific misconception sensitivity and specificity through `item_registry_discrimination()`. Posterior replay uses those values. The main scheduler calls `probe_eig_component()` without them, so item selection and posterior updating use different observation models.

### 4.4 Probe advancement is not tied to a diagnostic observation

The attempt pipeline advances an in-progress LO probe after every formal attempt. `record_probe_attempt()` receives only the LO ID; it does not receive the attempt, probe phase, candidate decision, or contamination state. Posterior replay includes every attempt after `entered_at`.

Consequently, ordinary practice, hinted work, `dont_know`, open-text, and exam attempts can complete a probe.

In the current fixture databases, 15 of 20 completed probes ended after one observation. The completing attempt was an ordinary, hinted, `dont_know`, `open_text`, or held-out `exam_attempt` observation in every case — never `diagnostic_probe`. One probe was completed by an `exam_attempt`.

### 4.5 Premature completion

A phase completes when the attempt target is reached, scalar mastery variance falls below a threshold, or the top categorical hypothesis probability exceeds a threshold. With only `mastered` and `unfamiliar`, one high score commonly satisfies the categorical condition even when the item covers only one facet or surface.

### 4.6 Coverage bonuses labeled as information gain

The selection reward supplements categorical EIG with deterministic reductions in mastery and facet variance derived from evidence weights and prior evidence mass. These values do not integrate over possible responses and can reward a broad item even when all hypotheses predict the same response.

These components may be valuable, but they MUST be reported separately as coverage or measurement-opportunity value rather than actual expected information gain.

### 4.7 Missing-item loop

When no local item exists, state sync records `probe_phase_local_pi_inadequate`. There is no durable pending state or automatic ephemeral-generation resolution. The current fixture databases contain 548 such events (441 in the law vault alone), including repeated events for individual LOs.

### 4.8 Inconsistent UX contract

The Textual UI displays a probe badge, but the Tauri practice screen selects the item's normal attempt type and exposes hints and Ask Tutor. Probe progress, measurement restrictions, and a transition-to-tutoring action are not first-class UI concepts.

## 5. Diagnostic Episode Model

### 5.1 New entities

Introduce a first-class `probe_episodes` table.

Required fields:

```text
id
learning_object_id
commitment_id             nullable for non-goal/local episodes
status                    pending_items | in_progress | complete | abandoned | converted_to_tutoring
trigger                   initial | misconception | stale_uncertainty | manual | goal_diagnostic
hypothesis_set_id
active_state_segment_id
goal_contract_version_id  nullable only when not goal-conditioned
depth_policy_version_id   nullable for non-commitment/local episodes
depth_envelope_version_id nullable for non-commitment/local episodes
depth_milestone_id        nullable for non-commitment/local episodes
target_decision_json
required_facets_json
minimum_independent_observations
maximum_observations
entered_at
completed_at
completion_reason
algorithm_version
created_at
updated_at
```

The depth and target references are commitment-point pins. A policy/envelope or
goal-head edit does not retarget an open episode. When a depth edge activates,
all unsubmitted presentations for the predecessor milestone are invalidated and
a later diagnostic opens a new episode; historical replay retains the old pins.

Introduce a first-class `probe_presentations` table between selection and observation. A scheduler candidate is only a ranking-time possibility; a presentation is the durable assignment actually committed and served to the learner.

Required fields:

```text
id
probe_episode_id
practice_item_id
scheduler_candidate_id
state_segment_id
probe_family_template_id
probe_family_template_version
instrument_card_id
instrument_card_version
instrument_card_snapshot_json
target_hypothesis_pairs_json
target_facets_json
posterior_at_selection_json
entropy_at_selection
expected_information_gain
selection_policy_version
status                    selected | served | submitted | ended
end_reason                expired | abandoned | invalidated
served_at
submitted_at
expires_at
ended_at
created_at
updated_at
```

`practice_attempts` MUST gain a nullable `probe_presentation_id`. It is required for attempts submitted as `diagnostic_probe` under the redesigned algorithm version and null for ordinary incidental evidence; frozen legacy attempts retain null. The submission carries the opaque presentation ID; the server validates that the presentation is active, was served for the same episode, item, state segment, and resolved card snapshot, and has not expired or already been consumed. The hypothesis set is locked per episode, so the episode reference implies it; presentations regain an explicit hypothesis-set reference only if versioned mid-episode expansion (§6.3) is ever implemented. `scheduler_candidate_id` identifies the committed slate candidate (a candidate belongs to exactly one slate, so no separate slate reference is stored) and is null for presentations minted outside a scheduler slate, such as dialogue microprobe turns. `created_at` is the commitment timestamp; there is no separate selection timestamp.

The presentation row and its selection-time snapshot MUST be persisted transactionally when the scheduler commits the assignment, before the item is returned to the client. `selected` means committed but not yet confirmed as displayed; `served` means displayed to the learner; `submitted` means consumed by an accepted attempt. An unsubmitted presentation that terminates moves to `ended` with an `end_reason`: leaving or replacing an item records `abandoned`; timeout records `expired`; a learner-state, episode, or intervention boundary that makes an unsubmitted assignment stale records `invalidated`. `ended` presentations never advance the episode but remain available for exposure and selection-policy telemetry.

Introduce a `probe_observations` table.

Required fields:

```text
id
attempt_id
posterior_before_json
posterior_after_json
entropy_before
entropy_after
realized_information_gain
independent_evidence_discount
contamination_json
grader_channel_json
updates_belief
eligible_for_completion
created_at
```

Ownership is strict: the **presentation** holds the assignment and all selection-time state (item, card snapshot, targets, expected EIG, state segment); the **attempt** holds the learner response and interaction data; the **observation** holds the grading result, contamination decision, and posterior transition. A `probe_observations` row is created only when an accepted attempt consumes a presentation. Incidental evidence — ordinary practice, hinted work, exams — never creates an observation row; it updates belief through attempt replay against the appropriate state segment (§5.3). `posterior_before_json` is deliberately not collapsed into the presentation's `posterior_at_selection_json`: incidental evidence may move belief between commitment and submission.

An attempt MUST advance episode budget, coverage, or stopping only when a qualifying observation exists for it. Episode progress is derived, never cached: observation counts and qualifying counts are computed by querying observations joined through attempt → presentation → episode, so a retried submission cannot double-advance an episode. Each presentation may produce at most one accepted diagnostic attempt and at most one probe observation, enforced by a unique index on `practice_attempts.probe_presentation_id` and a unique index on `probe_observations.attempt_id`; an observation reaches its presentation and episode through its attempt. Submission handling MUST be idempotent.

A **state segment** is an opaque ULID minted at episode entry and again at every intervention boundary (tutoring transition, answer or feedback reveal, block end). Segments are ordered per Learning Object; every observation references the segment whose learner state it measures. No dedicated table is required, but the event that opens a segment MUST be persisted so replay reconstructs segment boundaries deterministically.

Dialogue microprobe turns (§8.1) persist through the same pipeline: each turn first receives its own committed presentation, then records a lightweight `practice_attempts` row with attempt type `diagnostic_probe` on the turn's ephemeral generated instance, plus one `probe_observations` row referencing the attempt. `attempt_id` is therefore non-null for every modality; there is no separate dialogue observation path. Turns within one dialogue block share a single bounded task evidence mass per §7.7.

### 5.2 Unique phase identity

Every entry or re-entry MUST receive a unique episode/phase ULID. A deterministic value such as `probe_<learning_object_id>` MUST NOT be reused across phases.

### 5.3 Belief updates versus episode advancement

LearnLoop MUST maintain two distinct accounting paths:

1. **Belief update:** every relevant observation updates the appropriate learner-state segment using a likelihood adjusted for grading reliability, assistance, contamination, and intervention timing.
2. **Episode advancement:** only selected, committed, sufficiently uncontaminated diagnostic observations consume the probe budget, satisfy diagnostic coverage, or trigger stopping.

Incidental or contaminated evidence MUST NOT be discarded merely because it cannot advance the episode. Hinted evidence SHOULD be weakened toward the family bucket-marginal. Evidence after tutoring or answer reveal MUST update a new post-intervention `state_segment_id`, not the pre-intervention diagnostic state.

### 5.4 Observation eligibility

An observation is eligible for probe completion only if all of the following hold:

- The item was selected for this episode and active hypothesis set.
- The attempt references an unconsumed `probe_presentation` committed for the same item, episode, state segment, and resolved Instrument Card snapshot.
- The submitted attempt type is `diagnostic_probe`.
- No answer-revealing hint or substantive tutor help occurred before submission.
- The item is not a held-out exam item or imported exam observation.
- The item and attempt belong to the same active probe episode.
- The grading result comes from an approved diagnostic grading provider (§5.8) and meets a minimum reliability threshold, or is explicitly marked for later regrade.
- The item is not a disallowed repeat of the same surface family.

`dont_know` MAY be a valid diagnostic outcome if the selected probe item belongs to the episode and no contamination occurred. It MUST be represented as an outcome of the selected observation, not counted merely because a `dont_know` attempt occurred on the LO.

### 5.5 Assistance and contamination

Probe mode SHOULD disable:

- authored hints;
- Ask Tutor in practice context;
- worked-example reveal;
- expected-answer reveal;
- correctness feedback within the active micro-block.

If assistance occurs through an escape hatch, the observation MUST be marked contaminated and MUST NOT count toward independent-observation or completion minima. It MAY still update the appropriate learner-state segment through a contamination-adjusted likelihood. The episode may then transition to tutoring.

### 5.6 Feedback timing

The default diagnostic block SHOULD contain two to four short observations. Feedback is delayed until the block completes or the learner exits into tutoring.

If feedback is shown after an individual observation, the learner state has potentially changed. The next response MUST either:

- begin a new post-intervention state segment; or
- be classified as practice/tutoring evidence rather than another observation of the original probe state.

Delayed feedback SHOULD be the configuration default but MAY be disabled per learner. Opting out does not weaken the accounting: each feedback reveal simply closes the current state segment under the rules above, at the cost of fewer qualifying observations per block. The integrity model does not depend on the UX cost.

### 5.7 Block boundary semantics

During an active diagnostic block, per-attempt side effects that could leak feedback or duplicate diagnosis MUST be deferred: intervention follow-up evaluation, follow-up queue insertion, and misconception normalization do not run per attempt. A force-inserted follow-up appearing mid-block reveals that the previous answer was wrong, and it lets the follow-up selector compete with the episode over the same evidence.

At block end, one hook runs in order:

1. release withheld feedback;
2. run misconception normalization over the block's attempts;
3. evaluate the open-set trigger (§6.3);
4. evaluate the completion policy (§11);
5. route to the typed transition (§12.1), the next block, or ordinary practice.

### 5.8 Grading provider requirement

Diagnostic episodes REQUIRE an AI or external grading provider, mirroring the exam rule: self-grading a measurement is not measurement. Under a manual/self-grading provider:

- no qualifying observation may be served or recorded;
- the episode parks in `pending_items` (the pending state covers any missing serving capability — instruments or grading);
- the LO degrades to ordinary practice whose evidence updates belief through the incidental channel (§5.3).

Self-graded attempts on an in-episode LO MAY update durable belief with a damped likelihood but MUST NOT advance the episode.

### 5.9 Episode orchestration, diagnostic budget, and calibration sessions

The preceding sections define one episode; this section governs the fleet. Left unmanaged, entering an episode per never-attempted LO would turn onboarding of a 20-LO vault into 40–80 controlled diagnostic observations before ordinary practice begins.

Requirements:

- A session-level diagnostic planner ranks pending episodes by decision relevance: goal-frontier priority, prerequisite centrality, and disagreement among the graph-propagated prior (§6.4), learner claims, and observed evidence. High-disagreement, high-consequence episodes run first.
- Qualifying diagnostic observations are capped per routine session (configurable; default approximately one block of two to four observations) and interleaved with ordinary practice. Probes MUST NOT consume a routine session by default.
- Fresh-vault onboarding MUST NOT serialize an episode per LO ahead of practice. Time-to-first-ordinary-practice has a configured ceiling; LOs whose episodes have not yet run remain practicable with belief-only updates.
- A **calibration session** is an explicit, learner-initiated wrapper (goal wizard, command palette) that batches multiple episode blocks across a goal's facet scope in one sitting, ordered adaptively by cross-LO predictive information rate, with its own time budget, progress display, and stop control. Calibration sessions are belief-feeding and adaptive — the opposite of a held-out exam — and reuse the same episode/observation machinery and integrity rules; they lift only the per-session cap within their declared budget.
- The planner first filters episodes and candidate distinctions through the
  pinned goal support and DepthEnvelope. It may prioritize uncertainty at the
  next already-authorized milestone, but it MUST NOT spend questions mapping an
  outside-envelope frontier merely because those questions have high entropy.

## 6. Hypothesis Model

### 6.1 Cold-start templates

Implement authored coarse hypothesis templates keyed by relevant context such as domain, knowledge type, practice mode, and evidence facets.

Core templates SHOULD include:

- `unfamiliar`;
- `surface_only`;
- `recall_without_mechanism`;
- `procedure_without_selection`;
- `schema_without_transfer`;
- `confuses_with:<neighbor>`;
- `robust_initial_grasp`.

Only the three to five most plausible hypotheses should be instantiated for one episode.

### 6.2 Hypothesis construction inputs

Hypothesis instantiation SHOULD consider:

- LO knowledge type;
- required evidence facets;
- practice mode;
- learner claims;
- prerequisite and confusable concepts;
- domain/evidence-family profile;
- active and resolving misconceptions;
- recent learner questions;
- recent unexpected errors;
- demonstrated surface-specific success;
- unobserved transfer or procedure-selection facets.

### 6.3 Reserved open-set mass

Every initial hypothesis set SHOULD reserve prior probability for `other_or_unknown` unless the domain is genuinely closed. This hypothesis MUST have an explicit broad observation likelihood, including elevated probability for systematic but unmatched signatures. It MUST NOT be implemented as prior mass with no executable conditional model.

If `other_or_unknown` becomes competitive, the system SHOULD trigger misconception generate–retrieve–rerank or a review proposal. This trigger is evaluated at block end (§5.7), not per attempt. The first implementation MUST keep the episode hypothesis set locked. Versioned expansion may be added later only when the expansion event is persisted with an attempt/observation anchor so deterministic replay knows when the new set became active.

### 6.4 Cross-LO hierarchical priors

Cold-start priors SHOULD incorporate conservative evidence from the concept graph, covering claims, prerequisite state, related facets, and prior family-level behavior.

Propagation MUST be relation-specific and direction-specific:

- prerequisite strength may weakly move the prior mean or reduce uncertainty;
- prerequisite weakness may lower the mean or increase uncertainty;
- same-concept or parallel-surface relations may share more evidence;
- confusable relations MUST NOT propagate mastery as equivalence;
- graph distance and stale evidence MUST rapidly weaken influence.

Disagreement among the graph-propagated prior, learner claims, and direct behavioral evidence SHOULD increase probe priority. Cross-LO priors seed an episode; they MUST NOT substitute for direct evidence on high-stakes facets.

### 6.5 Re-probe triggers

A completed LO MAY re-enter probe mode when:

- a new high-severity misconception is registered;
- repeated prediction errors indicate model misspecification;
- high uncertainty remains across instructionally distinct states;
- fresh-surface performance conflicts with the cached diagnosis;
- the learner manually requests a diagnostic;
- a high-priority goal requires a facet with insufficient evidence;
- an authorized depth transition opens a new milestone whose action-relevant
  facets/hypotheses are not sufficiently localized.

A re-probe MUST create a new episode and hypothesis-set snapshot.

### 6.6 Factorized long-term model

The long-term target SHOULD be a factorized learner state over:

- LO scalar ability;
- facet presence/recall;
- procedure-selection or strategy state;
- transfer/generalization state;
- misconception beliefs;
- nuisance and assistance variables.

A flat categorical hypothesis list remains useful as a temporary decision artifact but SHOULD NOT become the authoritative global learner state.

## 7. Observation and EIG Model

### 7.1 Canonical observation shape

Probe observations SHOULD preserve more than a global score bucket. Depending on item mode, the observation may include:

- committed answer or choice;
- criterion-level outcomes;
- fatal-error or misconception signature;
- answer confidence;
- latency;
- hint/tutor contamination;
- covered facets;
- selected strategy;
- step or subgoal trace;
- first invalid inference;
- self-correction or repair behavior;
- generated explanation features.

The MVP may continue using a discrete analytic model, but MUST use the most diagnostic available factorization instead of collapsing every response immediately to one global 0–4 bucket.

Confidence and latency are logged-only observation features in the MVP: they are persisted for later calibration, and no likelihood term may consume them until a calibrated model exists.

### 7.2 Actual EIG

Actual probe EIG is:

```text
EIG(q) = E_o [ KL(P(H | o, q) || P(H)) ]
```

The conditionals used for candidate scoring MUST be the same conditionals used for the posterior update after observation.

For newly admitted diagnostic families, these conditionals MUST be compiled from the resolved Instrument Card rather than fabricated from shared global constants. Global constants MAY remain only as an explicitly logged legacy fallback.

For registry misconceptions, the scheduler MUST resolve and pass:

- item misconception discrimination rows;
- bridge links from misconception-keyed fatal errors;
- sensitivity and specificity estimates;
- the same fire-channel model used by posterior replay.

The scored observation is the grader output, not an assumed error-free view of the learner response. Candidate scoring and replay MUST compose the family response model with the applicable grader channel.

### 7.3 Separate utility components

Scheduler telemetry and reward SHOULD distinguish:

```text
actual_hypothesis_eig
predictive_eig
coverage_value
expected_learning_value
goal_value
authorized_depth_value
fresh_surface_value
time_cost
cognitive_load_cost
familiarity_discount
quality_penalty
```

These components MUST remain separately inspectable. The default policy MUST NOT combine them into an unrestricted hand-weighted scalar objective. Session intent determines the primary objective; hard eligibility, modality, exposure, quality, and time constraints determine the feasible set; secondary components break near ties or act as explicit constraints. Only response-conditioned entropy reduction may be labeled EIG.

`authorized_depth_value` is nonzero only for a reviewed next milestone already
inside the episode's pinned envelope under `auto_within_envelope`. It is not EIG
and cannot make an outside-envelope candidate eligible. The action/loss model
used for EVSI or decision-relative EIG contains only downstream actions the
learner has authorized.

### 7.4 Predictive EIG

Predictive EIG SHOULD measure how observing a candidate response is expected to improve predictions on a held-out target set, preferably across fresh surface families. In diagnostic mode it is the preferred primary objective when that target set adequately represents the future behavior and instructional decisions that matter.

For goal-conditioned depth work, that held-out target set is frozen to the
episode's current milestone or the single reviewed next milestone already
authorized at episode open. Candidate enumeration, a newly interesting deeper
task, or a later envelope edit cannot change it mid-episode.

Predictive EIG is particularly useful when:

- categorical learner hypotheses are incomplete;
- natural-language answers have many possible forms;
- multiple hypotheses make similar predictions on the current item;
- the system must choose between a short question and a richer dialogue/long-form observation.

Hypothesis EIG remains a fallback and audit signal when the predictive target set is sparse, incomplete, or omits an important latent capability. Predictive and hypothesis EIG MUST NOT be added together as if they were independent benefits.

### 7.5 Information per cost

Within a modality-capable feasible set, diagnostic selection SHOULD rank candidates by information per expected time, using a conservative fixed overhead and a family-level time posterior. Cost SHOULD NOT be a free subtrahend with a tunable coefficient.

Pure information-rate ranking MUST NOT permanently starve long-form instruments. The system SHOULD first determine whether the unresolved capability is observable through microprobes. When planning, coherence, multi-step dependency, epistemic standards, or far transfer remains unresolved, the eligible set MUST include an appropriate long-form family; candidates within that set are then ranked by information rate.

### 7.6 Grader reliability channel

The executable likelihood is:

```text
P(observed_grade | hypothesis, item)
  = sum_true_response P(observed_grade | true_response, family, grader_version)
                      P(true_response | hypothesis, item)
```

Family admission and calibration MUST track grading confusion, regrade agreement, ambiguity/abstention rate, and grader version. Evidence-strength fields MUST either be explicitly post-grader quantities or be composed with this grader channel at runtime.

An LLM-generated synthetic response, LLM signature matcher, and LLM grader SHOULD NOT all rely on the same unvalidated model/prompt path. Independent deterministic checks, formal verifiers, alternative graders, or sampled human review SHOULD be used where practical.

### 7.7 Correlated evidence and task mass

Multiple observations sharing one prompt, context, fatigue state, or first error are not conditionally independent by default. Each task MUST have a bounded total evidence mass allocated across its trace elements:

```text
sum(trace_element_evidence_mass) <= total_task_evidence_mass
```

Downstream steps dependent on the first invalid inference SHOULD be marked unassessable rather than counted as separate failures. Correct prefix steps MAY provide positive evidence. Full evidence mass MAY be assigned to multiple elements only when the family contract establishes that they are independently elicited.

## 8. Probe Modalities

### 8.1 Short adaptive dialogue

Dialogue is appropriate for:

- locating missing prerequisites;
- separating recall from mechanism failure;
- testing predictions under small counterfactual changes;
- eliciting a reason after a committed response;
- discovering previously unmodeled misconceptions;
- high-volume information gathering.

A recommended diagnostic dialogue pattern is:

1. Commit to an answer or prediction.
2. State the decisive reason.
3. Respond to a minimally changed case.
4. Give a counterexample, boundary condition, or failure case.

The tutor MUST avoid revealing the expected reasoning before the learner commits. Dialogue turns within one diagnostic block are correlated observations and MUST NOT be treated as conditionally independent by default.

Short dialogue is a sequence of adaptive microprobes only while the tutor withholds instructional content. Once a turn teaches, hints, reframes toward the answer, or repairs an error, subsequent responses belong to a post-intervention state segment.

Each committed turn persists as a `diagnostic_probe` attempt on its ephemeral generated instance with one probe observation (§5.1), so dialogue evidence flows through the same replay path as every other modality.

### 8.2 Proofs, derivations, and extended cases

Long-form probes are appropriate for:

- planning and subgoal selection;
- maintaining invariants;
- coordinating multiple facets;
- structural understanding;
- far transfer;
- epistemic standards and proof validity;
- identifying the first divergence in a reasoning chain.

Long-form probes SHOULD capture a structured trace rather than only a single rubric total:

- strategy selected;
- intermediate claims;
- justification dependencies;
- first invalid step;
- error family;
- self-detection;
- repair behavior;
- criterion-level outcomes;
- confidence and latency.

The trace MUST preserve the correct prefix, identify the first divergent step or claim when possible, mark dependent downstream obligations unassessable, and divide a fixed task evidence mass across assessable elements. A long-form response is therefore one structured multi-channel instrument, not a bag of independent full-strength attempts.

### 8.3 Recommended adaptive sequence

For most initial episodes:

1. Begin with one or two rapid commitment questions.
2. Branch to an explanation, counterfactual, or contrast question based on the posterior.
3. Use a long-form task only if the remaining ambiguity concerns procedural, structural, integration, or transfer competence.
4. End the diagnostic block.
5. Route immediately to targeted practice or tutoring.

## 9. Probe Family and Instrument Contract

### 9.1 Durable unit hierarchy

The durable unit of probe authoring, admission, and primary calibration MUST be a versioned `ProbeFamilyTemplate`, not an individual Practice Item.

```text
ProbeFamilyTemplate, versioned
  -> LO-bound InstrumentCard
    -> authored or generated ItemInstance
      -> ObservationTrace
```

- The **family template** defines a reusable measurement pattern such as minimal recall, prediction-before-computation, contrast with a confusable, perturbation, minimal counterexample, error diagnosis, or proof skeleton.
- The **Instrument Card** binds template slots to concrete LOs, facets, hypotheses, misconceptions, prerequisites, observation classes, and instructional decisions.
- The **Item Instance** supplies prompt wording, values/entities, representation, expected answer, rubric, surface, generator seed, and generator version.
- The **Observation Trace** records learner behavior, grading, contamination, trace decomposition, and the posterior transition.

Item instances remain the unit of exposure control, surface familiarity, answer leakage, and item-specific defects. They MUST NOT become the primary unit of empirical discrimination estimation when data are sparse.

Minimum persistence SHOULD include:

```text
probe_family_templates
  id
  version
  status                  draft | provisional | trusted | retired
  template_json
  schema_hash
  created_at
  retired_at

probe_instrument_cards
  id
  version
  probe_family_template_id
  probe_family_template_version
  learning_object_id
  hypothesis_scope_json
  card_json
  compiled_likelihood_hash
  created_at
  retired_at

probe_item_family_links
  practice_item_id
  instrument_card_id
  instrument_card_version
  generator_id
  generator_version
  generation_seed
  instance_metadata_json

probe_family_calibrations
  probe_family_template_id
  probe_family_template_version
  generator_version
  grader_version
  evidence_source         synthetic_gate | real_learner | reviewed_human
  parameter_posterior_json
  sample_size
  effective_sample_size
  updated_at
```

Rows MUST be append-versioned or immutable after use. Replay MUST resolve the versions and compiled likelihood hash persisted with the observation, never the newest family or card definition.

### 9.2 Executable family template

A family template MUST declare:

```yaml
probe_family_template:
  id: contrast_confusable
  version: 2
  instrument_kind: contrast
  target_slot: concept_a
  contrast_slots:
    - confusable_b
  applicable_knowledge_types:
    - conceptual
    - procedural
  observation_alphabet:
    - correct_target_reason
    - correct_weak_reason
    - confusable_signature
    - other_systematic_error
    - hedge
    - unanswered
  hypothesis_slots:
    - robust_target
    - confuses_with_neighbor
    - surface_only
    - unfamiliar
    - other_or_unknown
  applicability_conditions: []
  non_applicable_controls: []
  expected_seconds_prior:
    median: 45
  total_task_evidence_mass: 1.0
  allowed_assistance:
    - none
  generator_schema_version: 1
  signature_matcher_version: 1
  grader_policy: diagnostic_microprobe_v1
```

Procedural families MAY additionally declare trigger conditions, faulty operators, first-divergence patterns, applicable item families, and non-applicable controls. Executable malrules SHOULD be used where the domain supports them, but MUST NOT be required for conceptual or interpretive domains where natural-language applicability boundaries are more appropriate.

### 9.3 Executable Instrument Card

The card consolidates existing Practice Item metadata—`evidence_facets`, `evidence_weights`, `criterion_facet_weights`, rubric fatal errors, misconception-consistent answers, difficulty, surface family, and assistance modes—and adds the missing semantic likelihood model.

Required new semantics are:

- competing hypotheses bound to this target;
- expected observable response signatures per hypothesis;
- probability or evidence strength for each outcome class under each hypothesis;
- the instructional action enabled by resolving each important contrast;
- applicability, nuisance, and non-applicability conditions;
- family, generator, matcher, and grader versions.

Example:

```yaml
instrument_card:
  family_template_id: contrast_confusable
  family_template_version: 2
  target_decision: choose_schema_vs_confusable_repair
  bindings:
    target_facet: eigenvector_definition
    confusable_concept: singular_vector
  hypotheses:
    - robust_target
    - confuses_with_neighbor
    - unfamiliar
    - other_or_unknown
  conditional_observations:
    robust_target:
      correct_target_reason: dominant
      correct_weak_reason: occasional
      confusable_signature: negligible
      other_systematic_error: negligible
      hedge: negligible
      unanswered: negligible
    confuses_with_neighbor:
      correct_target_reason: rare
      correct_weak_reason: rare
      confusable_signature: dominant
      other_systematic_error: rare
      hedge: rare
      unanswered: rare
    unfamiliar:
      correct_target_reason: negligible
      correct_weak_reason: negligible
      confusable_signature: negligible
      other_systematic_error: occasional
      hedge: occasional
      unanswered: likely
    other_or_unknown:
      correct_target_reason: negligible
      correct_weak_reason: rare
      confusable_signature: negligible
      other_systematic_error: likely
      hedge: occasional
      unanswered: occasional
  conditional_pseudo_count: 8
  nuisance_requirements:
    - basic_matrix_vocabulary
  expected_seconds: 45
  instructional_actions:
    robust_target: shifted_surface_practice
    confuses_with_neighbor: contrastive_repair
    unfamiliar: foundational_instruction
    other_or_unknown: diagnostic_followup
```

Card conditionals MUST be authored in a small ordinal vocabulary — `dominant | likely | occasional | rare | negligible` — that compiles through a single global table and renormalizes per row. Canonical pre-normalization values are:

```text
dominant    0.60
likely      0.25
occasional  0.10
rare        0.04
negligible  0.01
```

This table is a fixed protocol constant, like the anchor points of a Likert scale. It MUST NOT be tuned per family, card, or domain, MUST NOT be fit against outcome data, and MUST NOT grow variants. Authors and generators express beliefs only by choosing words; the sole numeric authoring knob is the row pseudo-count. Free-form numeric conditionals from a generator MUST be rejected at card validation: LLM-elicited probabilities are miscalibrated at that granularity, and fake precision would let elicitation noise drive EIG rankings and anchor hierarchical calibration on fabricated numbers. Compiled rows are Dirichlet prior means with a declared pseudo-count (default low, for example 8) — priors that real observations can move quickly, not point likelihoods.

All subsequent numeric change happens in exactly one place: the per-family-version Dirichlet posterior, updated by observed outcome counts (§9.7) and audited by predicted-versus-realized outcome calibration. When a compiled row looks wrong, the permitted fixes are changing the ordinal word (a structural edit) or letting calibration move the number (data); editing compiled values directly is prohibited. The sim gate SHOULD include a one-time sensitivity sweep confirming that candidate rankings are stable under moderate perturbation of the canonical table (for example ±30% relative before renormalization); rankings that flip indicate under-separated hypotheses in the family, not a mistuned table.

Compiled conditional rows MUST be normalized and executable. Prose-only predicted signatures are insufficient. The card MUST compile to the same `P(observed_grade | hypothesis, item)` used by candidate EIG and posterior replay. Selected observations MUST persist the resolved card snapshot, including compiled values and pseudo-counts.

### 9.4 Authoring requirements

A high-quality family/card binding MUST satisfy:

- At least two plausible hypotheses predict materially different observable responses.
- The response distinction maps to different instructional actions.
- Wrong responses have interpretable signatures rather than only generic incorrectness.
- Required prerequisites are known, separately modeled, or explicitly listed as nuisance factors.
- Applicability and non-applicability conditions are testable.
- Rubric criteria map to evidence facets.
- The generator can produce surface-varied instances without cueing the hypothesis.
- Expected time, cognitive demand, total task evidence mass, and grading policy are declared.
- The instrument can abstain from diagnosis when a response does not match a supported signature.
- The family version can be retired without changing the meaning of historical observations.

Approximately 50% marginal success MUST NOT be sufficient for diagnostic approval.

### 9.5 Coverage targets

For every important facet/hypothesis distinction, generation coverage SHOULD provide at least two signature-distinct family templates:

- one direct or minimal instrument;
- one contrast, perturbation, counterexample, shifted-surface, or transfer instrument.

An integrative or long-form family SHOULD exist when the knowledge type requires planning, dependency management, proof standards, multi-step coherence, or far transfer. At least two independent surfaces or representations SHOULD support a high-confidence diagnostic conclusion.

Coverage is a generation-target check over family/card bindings, not a backlog requiring two or three permanently hand-authored items per facet. Parametric families SHOULD generate most recall, prediction, perturbation, contrast, and minimal-counterexample instances. Hand authoring SHOULD be concentrated on families whose quality is difficult to generate reliably, including subtly wrong worked solutions, proof skeletons, and rich cases.

### 9.6 Generated family and instance gate

A family/card version MUST pass admission before its generated instances may affect high-confidence diagnosis. Individual instances MUST also pass cheaper structural and grounding checks.

The family gate SHOULD:

- retain exact canned-answer comparison as a cheap structural first stage;
- generate three to five varied response traces under each declared hypothesis;
- recover the planted hypothesis through the real signature matcher;
- verify that the first divergent step or claim is compatible with the hypothesis;
- grade with the production rubric and grader channel;
- test an expert/clean solver;
- test paraphrased and structurally equivalent transfer surfaces;
- test at least one non-applicable control when the family declares bounded applicability;
- reject families whose declared signatures cannot be reproduced or whose hypotheses answer similarly;
- reject wording tricks, prerequisite confounding, source-grounding failures, and answer leakage.

Synthetic gate outcomes MUST be stored separately from real learner calibration. Passing the gate establishes structural and simulation validity only; it MUST NOT be described as real-learner sensitivity, specificity, or psychometric validation.

### 9.7 Hierarchical calibration and lifecycle

Family and instance parameters SHOULD use a hierarchical model:

```text
content- and domain-informed prior
  -> family-template-version posterior
    -> generator/domain variant posterior
      -> item-instance residual
```

Generated instances inherit the family posterior. Item-specific difficulty, discrimination, timing, signature fire rates, and grader reliability shrink strongly toward the family until sufficient real evidence exists.

Within a local vault with few learners, LearnLoop MUST report wide uncertainty and MUST NOT imply population-level calibration. Hierarchical calibration remains meaningful at one learner per vault — it pools that learner's evidence across items, surfaces, and generator variants within a family — but every estimate is learner-specific, not psychometric. Cross-vault parameter packs or aggregation are on hold while vaults have a single learner; reviving them requires an explicit privacy and provenance policy.

The lifecycle is:

```text
draft family/card
  -> schema and source validation
  -> cycle/applicability/grader gate
  -> provisional family
  -> generated provisional instances
  -> real-outcome hierarchical calibration
  -> trusted | revised version | retired
```

Retirement telemetry SHOULD include predicted-versus-realized EIG, negative realized information, grading disagreement, time calibration error, cross-surface replication, retention prediction, and transfer prediction.

## 10. Missing-Item Workflow

When no existing candidate clears the local diagnostic threshold:

1. Set the episode status to `pending_items`.
2. Create one deduplicated diagnostic-generation need keyed by episode, target hypothesis pair, and missing family capability.
3. Resolve an admitted family/card binding before generating one to three ephemeral instances. If no suitable family exists, create a family-authoring/review need rather than fabricating an unmodeled item.
4. Run instance-level structural, grounding, duplication, exposure, and card-conformance gates.
5. Present reviewed/eligible candidates to the scheduler.
6. If generation fails or is declined, pause the episode and continue without pretending a useful probe occurred.

`pending_items` is expected to be the common cold-start path, not an exception, and it MUST NOT block the learner: the LO remains schedulable for ordinary practice whose evidence updates belief through the incidental channel (§5.3); only episode advancement waits. Instances generated from a `trusted` family version MAY be auto-admitted provisionally after the instance-level structural gates, with post-hoc review; instances from `provisional` families require review before serving. Review throughput MUST NOT be a hard gate on practice.

Repeated vault sync or queue generation MUST NOT create duplicate inadequacy events or needs for the same unresolved episode target.

## 11. Completion Policy

A probe episode MAY complete when all mandatory conditions hold using only observations with `eligible_for_completion = true`:

- `minimum_independent_observations` has been reached;
- required/high-priority facets have adequate diagnostic coverage;
- surface-family diversity requirements are satisfied;
- no unresolved high-cost hypothesis pair remains above its ambiguity threshold;
- posterior or predictive stopping threshold is satisfied;
- qualifying observations are uncontaminated;
- grading reliability is sufficient.

Incidental, hinted, contaminated, and post-intervention observations MAY affect durable belief through adjusted likelihoods but MUST NOT satisfy these completion conditions.

Completion reasons SHOULD include:

```text
decision_stable
predictive_uncertainty_below_threshold
observation_budget_exhausted
no_suitable_candidate
converted_to_tutoring
learner_abandoned
manual_stop
```

A single response MUST NOT complete a multi-facet probe solely because the coarse `mastered` posterior exceeds a fixed threshold, except when an explicit strong prior claim and a highly discriminating cross-facet item satisfy a separately tested fast-path policy.

Completion records its pinned milestone and an action recommendation; it never
records `depth_milestone_reached` or activates the next edge by itself. If the
result supports the same action across hypotheses, the controller may stop
probing and apply that action. If that action is an authorized depth transition,
P0/P1 progression gates still independently require milestone exit evidence,
burden, lineage, successor-family, and fresh-proof checks.

## 12. UX Requirements

The Tauri and Textual surfaces MUST expose the same probe contract.

During a probe episode, show:

- `Diagnostic · observation 1 of up to 4`;
- the broad capability being checked without revealing hypothesis labels;
- that feedback is delayed for measurement integrity;
- whether assistance is unavailable;
- an action to stop diagnosing and start tutoring;
- an action to leave and resume later.

During the active diagnostic block:

- Force the recording attempt type to `diagnostic_probe`.
- Disable hints and practice-context Ask Tutor.
- Do not reveal correctness or expected answers between observations unless the block ends.
- Preserve draft/checkpoint behavior.

At completion, provide a concise, non-overclaiming result:

- observed strengths;
- remaining uncertainty;
- likely gap or misconception when supported;
- the next practice/tutoring action;
- the current milestone and whether a next reviewed edge is already authorized
  (without presenting that edge as a consequence the learner must accept);
- confidence and evidence breadth.

### 12.1 Typed transition

Every completed probe SHOULD persist a typed decision before routing or
generating prose. Tutor-specific fields are nullable unless the chosen action is
instruction/tutoring:

```text
target_facets
diagnosed_gap
first_error_step_or_claim
misconception_id
diagnostic_confidence
recommended_action
tutor_move
instructional_intent
scaffold_level
answer_reveal_budget
expected_learner_action
goal_contract_version_id
depth_policy_version_id
depth_envelope_version_id
depth_milestone_id
recommended_depth_edge_id
source_ref_ids
```

This separates three evaluable decisions: whether the learner state was diagnosed correctly, whether the appropriate instructional move was selected, and whether that move was verbalized well. Tutor moves SHOULD use a stable taxonomy such as elicit reasoning, localize error, minimal hint, state subgoal, contrast cases, counterexample, partial worked step, explanation, worked example, transfer question, or reflection.

## 13. Telemetry and Evaluation

### 13.1 Required logging

Every diagnostic decision MUST log:

- target episode and hypothesis set;
- pinned goal contract, depth policy/envelope, and current/authorized-next
  milestone when commitment-conditioned;
- committed presentation ID, lifecycle status, and selection/serve/submission timestamps;
- candidate pool for the same target;
- posterior and entropy before selection;
- expected EIG per candidate;
- coverage, learning-value, familiarity, quality, and cost components separately;
- selected item;
- family template, Instrument Card, generator, matcher, and grader versions;
- observation outcome;
- posterior and entropy after observation;
- realized information gain;
- contamination state;
- belief-update eligibility, episode-advancement eligibility, and state segment;
- latent response likelihood, grader-channel likelihood, and composed observed likelihood;
- completion decision and reason.

`entropy_before` and the hypothesis-set snapshot MUST not remain null for a routine probe selection.

### 13.2 Primary success metrics

Evaluate probe policies using:

- held-out next-answer log loss;
- held-out Brier score;
- prediction improvement on fresh surface families;
- facet/misconception classification accuracy against later evidence;
- cross-surface replication rate;
- downstream learning and retention after probe-directed practice;
- information gained per minute;
- diagnostic abandonment/frustration rate;
- item exposure concentration and bank utilization;
- calibration of predicted and realized outcomes;
- rate at which probe answers actually change the selected intervention;
- family-level grader agreement and abstention;
- family- and item-level posterior uncertainty under hierarchical shrinkage;
- open-set posterior activation and unmatched-signature rate;
- within-task effective evidence mass.

Posterior entropy reduction alone MUST NOT be a release criterion because an overconfident misspecified model can score well on that measure.

### 13.3 Shadow evaluation

New EIG variants SHOULD first run in shadow mode:

- log alternative rankings;
- compare predictions on future attempts;
- promote a policy only after held-out predictive and downstream-learning gains.

Synthetic admission trials and real learner outcomes MUST be reported separately.

**On hold (single-learner vaults):** near-tie randomization, persisted selection propensities, and doubly robust or other off-policy estimates are deferred until vaults have enough learners for these estimates to be meaningful. Shadow-mode ranking comparison and held-out prediction remain in scope — they work at n = 1. If the on-hold items are revived: randomization begins only inside a predefined safe set with persisted propensities, and off-policy estimates report overlap, effective sample size, maximum importance weight, and uncertainty rather than a single policy-value estimate.

### 13.4 Contextual learner-question evidence

Learner questions remain useful observations, but their generating process depends on tutor moves, interface affordances, warnings, learner goals, and available help. Question evidence MUST therefore be separated into:

- **epistemic signal**, indicating missing or uncertain knowledge;
- **interaction-preference signal**, indicating the learner's requested explanation style, pace, scaffold level, or goal.

The second channel SHOULD change tutor policy rather than mastery belief. Question events SHOULD persist preceding tutor move, scaffold offer/level, warning state, learner-selected mode, question opportunity, hints already used, direct-explanation request, elapsed time, and attempt progress. Until contextual likelihoods are calibrated, preference- or interface-driven questions SHOULD receive a damped mastery likelihood rather than the full global question signal.

## 14. Implementation Plan

### Checkpoint 0: Migration and cutover

1. Version-gate replay: legacy `probe_<lo_id>` phases and their attempts replay through the frozen legacy path forever, keyed by `algorithm_version`; new episodes replay exclusively through `probe_observations`.
2. Close existing `in_progress` phases with completion reason `superseded_by_redesign`; eligible LOs re-enter through new episodes under §5.9 orchestration.
3. Make `lo_probe_state` read-only legacy (or a derived view over episodes); no new writes.
4. Retire legacy configuration: `attempts_target_default`, `attempts_target_with_strong_claim`, `claim_skip_threshold` (the strong-claim path becomes the §11 fast-path policy), and `variance_convergence_threshold` (superseded by the §11 completion policy). Document the mapping.
5. Fixture vaults with pre-redesign probe history MUST replay identically after migration.

### Checkpoint 1: Truthful accounting and interaction integrity

1. Add unique probe episode identity, state segments, and explicit probe-observation persistence.
2. Add first-class probe presentations that durably bind the committed scheduler selection and selection-time snapshot to the served item and submitted attempt.
3. Separate belief updates from episode advancement.
4. Tie budget, coverage, and stopping only to qualifying selected observations.
5. Prevent hinted, ordinary, teach-back, and exam attempts from advancing a probe while preserving their adjusted belief evidence.
6. Force `diagnostic_probe`, delayed feedback, and assistance restrictions in Tauri and Textual.
7. Add `Stop diagnosing and teach me` and start a post-intervention state segment.
8. Separate actual EIG from coverage and variance-shrink bonuses in telemetry.
9. Deduplicate missing-candidate events and generation needs.
10. Require minimum evidence breadth before early completion.
11. Pin goal/depth/milestone context and invalidate predecessor presentations
    when a P1 depth transition commits.

This checkpoint is a prerequisite for every downstream estimate. No calibration or policy comparison is trustworthy before it is complete.

### Checkpoint 2: State and likelihood foundation

1. Add facet-founded cold-start hypothesis templates and reserved `other_or_unknown` mass.
2. Instantiate episode priors from LO type, facets, claims, prerequisites, confusables, and conservative graph propagation.
3. Keep flat hypothesis sets locked and episode-local.
4. Wire existing registry discrimination into main scheduler EIG.
5. Add the grader-confusion channel and require selection/replay likelihood identity.
6. Make predictive EIG per expected time the diagnostic default when target coverage is adequate; retain hypothesis EIG as fallback/audit.
7. Add automatic re-probe triggers for new high-severity misconceptions and predictive failures.

### Checkpoint 3: Family instrumentation and generated microprobes

1. Add versioned Probe Family Templates, LO-bound Instrument Cards, and persisted card snapshots.
2. Compile card conditionals into both candidate scoring and posterior replay.
3. Create a hypothesis-contrast/family coverage report.
4. Add parameterized generation for minimal recall, prediction, perturbation, contrast, and minimal-counterexample families.
5. Extend the diagnostic gate with varied planted traces, reverse matching, clean trials, cross-surface trials, and non-applicable controls.
6. Add first-error localization, correct-prefix preservation, and bounded within-task evidence mass.
7. Add generate–retrieve–rerank misconception matching with abstention and open-set proposals.
8. Concentrate manual authoring on subtly wrong solutions, proof skeletons, and other hard-to-generate families.
9. Extend the sim harness with planted latent hypothesis types (`surface_only`, `confuses_with:<neighbor>`, `schema_without_transfer`, planted misconceptions) and validate the episode policy end to end — selection, stopping, contamination, and typed-transition behavior against planted students — not only per-family instrument gates.

### Checkpoint 4: Empirical pilot and retirement loop

Entry gate: the Checkpoint 3 sim validation meets its thresholds (planted-type classification accuracy within the observation budget, with matching instructional actions) before any real learner uses the new episode UX.

1. Pilot the new accounting and family system on one fixture vault with deterministic replay.
2. Add hierarchical family/generator/item parameter posteriors with strong shrinkage.
3. Measure predicted-versus-realized EIG, negative realized information, time calibration, cross-surface replication, and downstream retention/transfer.
4. Estimate regrade agreement and grading confusion per family and grader version.
5. Keep synthetic admission evidence separate from real learner evidence.
6. Add contextual question-event telemetry and distinguish epistemic questions from interaction-preference signals.
7. Add trusted, revise, and retire transitions for family versions and instances.

### Checkpoint 5: Policy evaluation and advanced models

1. Run alternative selection policies in shadow mode.
2. Add simple redundancy penalties before joint-batch entropy.
3. Add greedy conditional/joint EIG only for probes selected as a committed block before answers are observed.
4. On hold (single-learner vaults): safe near-tie micro-randomization with persisted propensities.
5. On hold (single-learner vaults): off-policy evaluation with support and effective-sample-size diagnostics.
6. Benchmark DAS3H-style forgetting and cognitive-diagnosis alternatives offline; do not automatically replace durable state or facet mappings.
7. Defer versioned posterior expansion, learned scheduling, tutor post-training, and pedagogical RL until checkpoints 1–4 generate credible data.

## 15. Acceptance Criteria

### Integrity

- An ordinary, hinted, teach-back, exam, or unrelated attempt cannot advance a probe episode.
- A relevant contaminated observation can update belief with weakened likelihood without advancing budget, coverage, or stopping.
- Post-tutoring evidence updates a new state segment and cannot rewrite the pre-intervention posterior.
- Every completed observation references its episode, state segment, selected candidate, family/card version, attempt, posterior transition, grader channel, and contamination state.
- Every qualifying diagnostic attempt references a unique, previously committed and served presentation whose episode, item, state segment, and card snapshot match the submission.
- A presentation can produce at most one accepted attempt and one observation; retrying a submission cannot duplicate evidence or episode progress.
- Ended (expired, abandoned, or invalidated), mismatched, or already-consumed presentations cannot produce qualifying observations.
- Probe phase IDs are unique across re-entry.
- Tauri and Textual enforce the same assistance restrictions and attempt type.
- A manual/self-grading provider cannot produce qualifying observations; the episode parks and the LO degrades to belief-only ordinary practice.
- Follow-up evaluation, follow-up queue insertion, and misconception normalization are deferred to block end during an active diagnostic block.

### Migration

- Fixture vaults with pre-redesign probe history replay identically after migration.
- Legacy phases never resolve new-model family, card, or episode definitions.
- Pre-existing `in_progress` phases are closed as `superseded_by_redesign`, never silently reinterpreted.

### Orchestration and burden

- Fresh-vault onboarding reaches ordinary practice within the configured time-to-first-practice ceiling; episodes interleave with practice rather than serializing ahead of it.
- The per-session qualifying-observation cap is enforced outside calibration sessions.
- A `pending_items` episode never blocks ordinary practice or scheduling on its LO.
- A calibration session batches episodes across a goal scope, respects its declared time budget, and lifts only the per-session cap.
- Planted-type sim students are classified at or above the configured accuracy threshold within the observation budget, and the selected instructional action matches the planted gap.
- An episode cannot select an outside-envelope distinction for its information
  value; a new authorized milestone opens a new pinned episode rather than
  retargeting the predecessor posterior.

### Selection consistency

- Registry misconception discrimination affects main scheduler probe EIG.
- Candidate scoring and posterior updating use the same card-compiled, grader-composed observation conditionals.
- An item with identical predicted outcomes across hypotheses receives zero hypothesis EIG even if its marginal success probability is 0.5.
- Coverage opportunity is logged separately from EIG.
- Predictive and hypothesis EIG are not added as independent scalar rewards.
- Long-form families remain eligible when the unresolved target is not observable by microprobes.

### Hypothesis quality

- Cold-start probes can instantiate at least three actionably different hypotheses when LO metadata supports them.
- Initial sets reserve executable `other_or_unknown` mass unless explicitly closed-domain.
- Relation-specific cross-LO priors are deterministic, uncertainty-aware, and do not propagate mastery across confusable edges.
- A newly registered high-severity misconception can trigger a new episode with a new locked set.
- Hypothesis-set size remains bounded and deterministic for the same input snapshot.

### Family and likelihood quality

- Every admitted family version has normalized executable conditionals, a grader policy, an outcome alphabet, applicability metadata, and a bounded task evidence mass.
- Card conditionals use the ordinal vocabulary and compile through the fixed canonical table to Dirichlet prior means with declared pseudo-counts; free-form numeric conditionals are rejected.
- Generated instances reference an admitted family/card version and preserve generator provenance.
- A family whose planted answers do not reproduce its declared signatures is rejected.
- Non-applicable controls reject a simulator that expresses the misconception as generalized incompetence.
- Synthetic admission statistics are never merged with or labeled as real learner calibration.
- Item-level estimates shrink toward family posteriors until real evidence supports deviation.

### Completion

- A narrow single-item success cannot complete a multi-facet episode without satisfying the explicit fast path.
- Completion requires minimum independent evidence and required-facet breadth.
- Completion reason is persisted and inspectable.
- Multiple trace obligations from one task cannot contribute more than the declared total task evidence mass.
- Downstream obligations after a first error are unassessable unless independently recoverable.
- Completion may recommend an authorized next-depth action but cannot mark a
  milestone reached, append a target successor, or activate a card itself.

### Missing candidates

- An inadequate local bank creates one durable pending need per episode target and missing family capability.
- Repeated state sync does not create duplicate events or needs.
- Eligible ephemeral generation can resolve the pending state only through an admitted family/card binding.

### Evaluation

- Every routine probe event records non-null entropy and hypothesis context.
- Expected versus realized information is auditable per observation.
- Grader agreement, open-set activation, family uncertainty, and effective evidence mass are auditable.
- Policy evaluation reports held-out predictive metrics and downstream learning metrics, not only entropy reduction.

## 16. Required Regression Tests

Add integration tests for:

1. Registry discrimination changes the main scheduler's probe ranking.
2. The same card-compiled and grader-composed likelihood drives selection and posterior replay.
3. Ordinary and hinted attempts do not increment qualifying probe progress.
4. A hinted relevant attempt weakly updates durable belief without advancing the episode.
5. `exam_attempt` and `exam_evidence` do not increment probe progress.
6. A selected uncontaminated `diagnostic_probe` creates one probe observation and increments progress exactly once.
7. Retrying the same presentation submission is idempotent and cannot create a second attempt, observation, or progress increment.
8. A submission with an ended (expired, abandoned, or invalidated), already-consumed, or mismatched presentation is rejected as qualifying evidence.
9. One high score cannot complete a multi-facet episode without breadth.
10. Two independent surfaces can complete when the decision posterior is stable.
11. Tutor or hint use marks the observation contaminated and prevents it from satisfying completion minima.
12. `Stop diagnosing and teach me` ends measurement and routes subsequent evidence to a new state segment.
13. Missing local instances create one deduplicated generation need tied to a family capability.
14. Cold-start templates produce actionably distinct states with reserved open-set mass.
15. `other_or_unknown` gains probability for an unmatched systematic signature.
16. A new misconception can trigger a unique re-probe episode.
17. A 50%-success but hypothesis-independent item receives zero hypothesis EIG.
18. A family/card with non-normalized or incomplete conditional rows is rejected.
19. A generated instance cannot enter diagnostic selection without an admitted family/card version.
20. A planted-hypothesis response that fails reverse matching rejects the family version.
21. A non-applicable control catches misconception overapplication.
22. Changing grader reliability changes EIG and posterior strength in the expected direction.
23. Eight dependent proof obligations cannot exceed the task's total evidence mass.
24. A first error preserves correct-prefix evidence and marks dependent downstream steps unassessable.
25. Family version replay remains stable after a newer version is admitted or retired.
26. Item calibration shrinks toward the family posterior under sparse evidence.
27. Telemetry separates hypothesis EIG, predictive EIG, coverage, learning value, cost, and grader reliability.
28. Routine probe logs contain posterior/entropy before and after observation.
29. Sequential one-at-a-time selection conditions on the observed posterior; joint-batch selection is used only for precommitted blocks.
30. Legacy probe history replays identically after migration, resolving only frozen legacy definitions.
31. A `pending_items` episode leaves its LO schedulable for ordinary practice with belief-only updates.
32. A committed dialogue microprobe turn persists as one presentation, one `diagnostic_probe` attempt, and one probe observation, and turns within one block share the task evidence mass.
33. A manual/self-grading provider cannot create qualifying observations and parks the episode.
34. Follow-up evaluation and misconception normalization defer to block end during an active block.
35. A card authored with free-form numeric conditionals is rejected; compiled ordinal rows carry pseudo-counts.
36. The per-session qualifying-observation cap holds during onboarding, and practice interleaves with episodes.
37. A planted `confuses_with` sim student is diagnosed within the observation budget with the matching instructional action.
38. A high-EIG probe whose only downstream use is outside the pinned
    DepthEnvelope is ineligible.
39. Committing an authorized depth edge invalidates unsubmitted predecessor
    presentations and a deeper diagnostic receives a new episode, target pin,
    milestone pin, and hypothesis snapshot.
40. Probe completion alone cannot append a goal/depth successor or transfer the
    old posterior as a diagnosis of the deeper milestone.

## 17. Highest-Leverage Initial Slice

If only one end-to-end implementation slice is undertaken, it should:

1. Introduce explicit probe episodes, committed presentations, state segments, and separate belief-update/completion eligibility.
2. Add one versioned parameterized microprobe family with an executable Instrument Card.
3. Generate at least two distinct surfaces from that family and persist full provenance.
4. Force selected interactions to `diagnostic_probe` and enforce delayed feedback/assistance restrictions.
5. Replace the cold `mastered`/`unfamiliar` set with actionable hypotheses plus `other_or_unknown`.
6. Compile the card and grader channel into both EIG selection and posterior replay.
7. Require two independent surfaces before normal completion.
8. Run planted, clean, cross-surface, non-applicable, and regrade-agreement admission checks.
9. Log predicted and realized EIG while keeping synthetic and real evidence separate.
10. Pin goal/depth/milestone context for goal-conditioned episodes and keep
    depth activation outside the probe service.
11. Apply the Checkpoint 0 replay version gate before the schema work so legacy fixture history stays replayable throughout the slice.

This vertical slice changes probes from ordinary Practice Items with an EIG-derived priority boost into a versioned, auditable measurement system and tests the architecture before bulk family authoring.

## 18. Research Context

- Jimmy Wang, Thomas Zollo, Richard Zemel, and Hongseok Namkoong, [Adaptive Elicitation of Latent Information Using Natural Language](https://arxiv.org/abs/2504.04204), 2025.
- Matthew Finkelman, Wonsuk Kim, Alexander Weissman, and Robert Cook, [Cognitive Diagnostic Models and Computerized Adaptive Testing: Two New Item-Selection Methods That Incorporate Response Times](https://jcatpub.net/index.php/jcat/article/view/43), 2014.
- Chuan-Ju Lin and Hua-Hua Chang, [Item Selection Criteria With Practical Constraints in Cognitive Diagnostic Computerized Adaptive Testing](https://pmc.ncbi.nlm.nih.gov/articles/PMC6425095/), 2019.
- Joshua Mitton et al., [Misconception Diagnosis From Student-Tutor Dialogue: Generate, Retrieve, Rerank](https://arxiv.org/abs/2602.02414), 2026.
- Alexis Ross and Jacob Andreas, [Learning to Make MISTAKEs: Modeling Incorrect Student Thinking And Key Errors](https://arxiv.org/abs/2510.11502), 2025.
- Xinghe Chen, Naiming Liu, and Shashank Sonkar, [MalruleLib: Large-Scale Executable Misconception Reasoning with Step Traces for Modeling Student Thinking in Mathematics](https://arxiv.org/abs/2601.03217), 2026.
- Naiming Liu et al., [Misconception Acquisition Dynamics in Large Language Models](https://arxiv.org/abs/2604.00818), 2026.
- Hyeonsu B. Kang et al., [Stepwise Verification and Remediation of Student Reasoning Errors with Large Language Model Tutors](https://arxiv.org/abs/2407.09136), 2024.
- Rose E. Wang et al., [Bridging the Novice-Expert Gap via Models of Decision-Making: A Case Study on Remediating Math Mistakes](https://arxiv.org/abs/2310.10648), 2023.
- Zhuqian Zhou et al., [Tutor Move Taxonomy: A Theory-Aligned Framework for Analyzing Instructional Moves in Tutoring](https://arxiv.org/abs/2603.05778), 2026.
- Tomohiro Nagashima, Mirella Hladký, and Vera Rief, [Warning About AI Fallibility Increases Help-Seeking in an Intelligent Tutoring System](https://arxiv.org/abs/2606.03822), 2026.
- [Rethinking Scaffolding in LLM Tutors: The Interactional Mismatch Between Benchmarks and Real-World Deployments](https://arxiv.org/abs/2606.15766), 2026.
- Andreas Kirsch et al., [BatchBALD: Efficient and Diverse Batch Acquisition for Deep Bayesian Active Learning](https://arxiv.org/abs/1906.08158), 2019.
- José González-Brenes et al., [DAS3H: Modeling Student Learning and Forgetting for Optimally Scheduling Distributed Practice of Skills](https://arxiv.org/abs/1905.06873), 2019.
- Tianchen Qian et al., [The Micro-Randomized Trial for Developing Digital Interventions: Experimental Design and Data Analysis Considerations](https://arxiv.org/abs/2107.03544), 2021.
- Miroslav Dudík, John Langford, and Lihong Li, [Doubly Robust Policy Evaluation and Learning](https://arxiv.org/abs/1103.4601), 2011.
- Laroche et al., [Safe Policy Improvement with Baseline Bootstrapping](https://arxiv.org/abs/1712.06924), 2017.
- Yawen Ma et al., [A Statistical Framework for Dynamic Cognitive Diagnosis in Digital Learning Environments](https://arxiv.org/abs/2506.14531), 2025.

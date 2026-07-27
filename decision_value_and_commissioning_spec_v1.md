# Decision-valued diagnostics and commissioning — implementation spec (v1)

**Status:** proposed implementation companion, code-audited 2026-07-27.

**Parents and authorities:**

- `spec_causal_attribution_v1.md` remains the authority on causal-state
  ownership, epistemic firewalls, minimal repair, learner contestability, and
  causal P4's learned repair policy.
- `spec_p4_controller_and_scale.md` remains the authority on the staged
  controller, robust EVSI, the constrained decision-cost hierarchy, shadow
  promotion, and the one-randomization-layer rule.
- `spec_measurement_efficiency_v1.md` remains the authority on instrument
  admission, contract-cell reachability, inference, and certification.
- `spec_diagnostic_augmentation_v1.md` remains the authority on diagnostician
  quality measurement, improvement, and the frozen scoreboard.
- `implementation_plan_v1.md` remains the shipping-order authority. This
  document refines its causal-P4 and commissioning work; it does not silently
  reorder completed stages.

**Purpose:** turn the existing causal probe rule, robust-EVSI substrate,
duration telemetry, and contract commissioning queue into two inspectable
decision systems:

1. a causal diagnostic selector that asks a question only when its answer is
   expected to change a downstream repair and repay its learner burden; and
2. a commissioning selector that spends authoring capacity on the instrument
   bundles with the highest expected marginal decision coverage.

Both selectors ship shadow-first. Neither gains evidence, grading,
certification, or learner-facing claim authority.

---

## 0. Decision summary

The intended end state is:

```text
commission the most decision-relevant instruments
    ↓
filter every candidate through hard constraints
    ↓
ask only action-changing, cost-effective diagnostic questions
    ↓
apply the smallest currently justified repair
    ↓
verify independently after spacing
    ↓
learn repair effectiveness and duration
    ↓
improve the next commissioning and diagnostic decision
```

The implementation separates three quantities that are currently easy to
conflate:

| Quantity | Meaning | Learning horizon |
|---|---|---|
| `expected_seconds(q)` | Active learner time for one diagnostic question | Immediate attempt latency |
| repair duration | Active minutes spent receiving/attempting one repair | Immediate remediation episode |
| repair effectiveness | Probability that the repair survives independent cold verification | Delayed cold outcome |

It also separates the two halves of causal P4:

| Causal P4 half | Responsibility | Gate |
|---|---|---|
| **Selection** | `evsi.py`, `action_loss.py`, and staged diagnostic selection rank/stop questions using the current repair model | Likelihood, duration, robustness, and shadow-promotion readiness |
| **Belief formation** | Learn which repair works, for which causal state, at what active-time cost | Repair-linked cold-outcome volume and safe overlap/randomization |

The Stage-4.2 cold-outcome trigger in `implementation_plan_v1.md` gates the
belief-forming half. It does not prohibit wiring and evaluating the selection
half in shadow before those delayed labels have volume.

---

## 1. Outcome and non-goals

### 1.1 Learner-visible outcome

At exit:

- ambiguity alone never forces a diagnostic question;
- plausible causes sharing one optimal first repair route directly to that
  repair;
- when repairs differ, all feasible probes are ranked and the best robust
  value candidate is offered;
- a probe whose robust value does not clear its predicted learner burden is
  skipped in favor of the current optimal repair;
- learner preference (`teach_now`, `not_now`, `no_more_diagnostics`) remains a
  hard constraint;
- missing likelihoods, unstable rankings, missing renderers, and unavailable
  held-out surfaces produce typed abstention/dependency states rather than
  fabricated values;
- later cold evidence supports or contradicts repair effectiveness without
  rewriting the original diagnosis;
- the authoring pipeline preferentially closes decision-pivotal contract gaps
  instead of following identifier order.

### 1.2 Non-goals

This document does **not**:

- replace ordinary practice scheduling with EIG or EVSI;
- reduce measure, teach, practice, assess, maintain, expand, and stop to one
  weighted sum;
- infer response likelihoods from pairwise separability;
- treat model-authored minutes as calibrated measurements;
- let a commissioning score bypass persona, rubric, servability, held-out, or
  review gates;
- grant a learned repair policy live authority from deterministic historical
  logs with no action overlap;
- add MCTS or a multistep rollout;
- claim a per-capability cell posterior exists where the current canonical
  ledger stores only evidence masses and certification credit.

### 1.3 Acceptance journeys

#### Journey A — a short probe prevents the wrong repair

A failed problem leaves two plausible causes with different repair classes:
one needs a short execution retry and the other needs a conceptual
reconstruction. Two probes are feasible: a short contrast question and a
longer multi-step diagnostic.

Expected behavior:

1. machine checks, learner preference, episode ownership, and servability run
   before scoring;
2. the selector integrates the locked prior, candidate likelihood ensembles,
   downstream repair loss, and predicted administration time;
3. the short contrast question is offered only if its robust net value is
   positive;
4. the response updates the locked diagnostic episode and selects one repair,
   not both;
5. a later independent cold outcome updates repair-effectiveness evidence
   without rewriting the original diagnosis.

#### Journey B — ambiguity does not cause interrogation

A failure has several plausible causes, but all imply the same low-cost first
repair.

Expected behavior:

1. action equivalence makes diagnostic EVSI zero;
2. no probe is offered;
3. the learner immediately receives the common minimal repair and retries;
4. later evidence may open a new causal episode if the common repair fails.

The same direct-to-repair outcome occurs when repairs differ but every feasible
probe's robust value is below its learner-time cost.

#### Journey C — authoring closes a pivotal gap

An active goal has several unreachable contract cells. One conjunctive
capstone could close three primary cells and complete a structurally
certifiable recipe; several single-cell requests are also feasible. An
error-hunt request is valid but blocked by a missing desktop renderer.

Expected behavior:

1. the capstone bundle outranks ordinary single-cell coverage within the fixed
   authoring budget;
2. actual run tokens, generated artifacts, admission results, and realized
   reachability delta join back to the request;
3. the renderer-blocked error hunt remains visible as valid latent inventory
   but does not count as reachable or enter a learner queue;
4. after the renderer seed requirement is met, the renderer dependency
   outranks further accumulation of unservable inventory.

---

## 2. Current-state findings

### 2.1 Causal probe decision

`causal_probe_coherence.decide_probe` currently computes:

```text
avoided_overteaching_minutes
× expected_information_gain
× probability_information_changes_repair
```

The orchestrator supplies:

```text
expected_information_gain
    = separable hypothesis pairs / all hypothesis pairs

probability_information_changes_repair
    = action-changing separable pairs / separable hypothesis pairs
```

Their product is therefore the unweighted fraction of all hypothesis pairs
that are both separable and mapped to different repair classes. It is a useful
structural filter, but it is not mutual information or formal EVSI:

- pairs are weighted equally rather than by the locked prior;
- no response emission probabilities are integrated;
- downstream action loss is represented by one avoided-minutes scalar;
- all active candidates are not ranked—the current orchestrator chooses
  `active[0]`;
- teaching every branch minus the uniform mean is assumed as the
  over-teaching baseline.

The existing hard gates around the calculation are correct and survive:

- common low-cost repair;
- action equivalence;
- machine checks first;
- learner preference;
- recent diagnostic burden;
- session budget;
- instrument lifecycle and servability;
- one locked hypothesis set per episode.

### 2.2 Action loss

`action_loss.build_loss_table` implements:

```text
L(h,a) = 0                              if a is route(h)
L(h,a) = minutes(a) + minutes(route(h)) otherwise
```

Without per-intervention duration tags,
`attempt_minutes_by_intervention` assigns every action the same pooled median
`m`. Every off-diagonal cell then equals `2m`.

Let `r_a` be the posterior mass of hypotheses whose effective repair route is
`a`. The expected loss becomes:

```text
loss(a) = 2m(1 - r_a)
```

and the selected action is the modal **repair route**. Formal EVSI reduces to:

```text
2m × [E_e max_a r_a|e - max_a r_a]
```

This still values prior-weighted, response-dependent action changes, but the
loss table contributes no repair-specific cost discrimination.

### 2.3 Timing

The live inputs have three regimes:

- causal repair-class `expected_minutes`: model-reported where present,
  otherwise a heuristic default;
- probe burden: instrument-card `expected_seconds`, otherwise a heuristic
  default;
- formal action loss: pooled attempt median where duration events exist,
  otherwise a heuristic default.

The vault records attempt latency, but existing loss construction cannot group
it by intervention. A number read deterministically from an authored card is
not thereby an empirically determined quantity.

### 2.4 Commissioning

`contract_reachability._queue_sort_key` orders unreachable cells by:

```text
reachability verdict priority
learning-object id
capability rank
capability
facet id
```

`practice_generation.build_practice_expansion_plan` consumes that queue,
selects the first commissioned rung per learning object, and lets queue order
decide which learning objects survive `max_los`.

The queue is structurally honest but not value-aware. It does not ask:

- whether one new item completes a certifiable recipe;
- whether a held-out/cold-assessment decision is blocked;
- whether one conjunctive item can close several cells;
- whether the learning object belongs to an active goal;
- how likely the generated artifact is to pass admission;
- how many authoring tokens or review cycles the request is expected to cost.

Actual token columns exist on `agent_runs`, but a run may create several items
and use repair/retry calls. Per-cell authoring cost is not identified until the
commissioning request, run, artifacts, admission results, and reachability
delta are joined.

---

## 3. Standing invariants

1. **Constraints precede scores.** Purpose, learner intent, safety, held-out
   protection, episode ownership, lifecycle status, renderability, burden, and
   session budget define the feasible set.
2. **Shadow has zero authority.** Shadow output cannot reorder live work,
   expose a surface, stop an episode, select a repair, update a posterior,
   certify, or phrase a learner-facing claim.
3. **Selection and stopping differ.** Per-time value ranks feasible candidates;
   absolute robust net value decides whether to measure.
4. **Action value, not entropy alone, governs probe-versus-repair.** EIG may
   rank or screen under its declared purpose; it cannot force a diagnostic
   question whose answer would not change an action.
5. **No invented likelihoods.** Structural separability is not converted to
   `P(E|H)` through an implicit uniform distribution.
6. **Missing machine data never buys learner effort.** A missing or unstable
   likelihood/cost estimate can license a skip or abstention, never a live
   probe.
7. **Observed time is not zero when missing.** Missing, abandoned, expired,
   and structurally unmeasurable are separate states.
8. **Cold outcomes do not rewrite diagnoses.** They train/validate repair
   effectiveness and downstream policy inputs.
9. **Commissioning operates on bundles.** The candidate unit is an authoring
   request that may target several cells with one item, not necessarily one
   cell.
10. **Current servability and instrument validity are different facts.** A
    valid instrument blocked by a missing renderer is neither live-reachable
    nor defective.
11. **One randomization layer.** Any repair-effectiveness experiment uses the
    P4 registered randomization mechanism among already-safe,
    near-equivalent actions, with propensities logged.
12. **Every learned input is independently promotable.** Duration,
    likelihood, admission-yield, and repair-effectiveness models carry their
    own version, provenance, calibration, and rollback state.

---

## 4. Shared provenance and telemetry contracts

### 4.1 Estimate provenance

Every time, likelihood, loss, and authoring-yield estimate carries one of:

```text
authored_prior
structural_bound
empirical_family
empirical_repair_class
pooled_empirical
heuristic_default
learned_cold_outcome
```

`computed` or `deterministic` may describe how a value was produced, but cannot
substitute for its epistemic source. For example, reading
`expected_seconds=45` from a card is deterministically reproducible and still
an `authored_prior`.

Each estimate receipt includes:

```text
estimate
lower_bound / upper_bound where available
sample_count / effective_sample_size
source
model_or_rule_version
scope
fitted_parameter_set_id
missingness/censoring counts
```

### 4.2 Attempt-duration context

The interaction/attempt lineage must recover, where applicable:

```text
attempt_id
administration_id
surface_id
practice_item_id
instrument_card_id + version
surface_family / independent surface group
attempt_type and purpose
causal_factor_id
probe_candidate_id
remediation_episode_id
repair_class_id
intervention_kind
started_at / submitted_at or duration_ms
outcome arm
```

Prefer an existing append-only event payload plus indexed joins over new
columns. Promote a field to a column only after a demonstrated query or
integrity requirement.

### 4.3 Repair-linked cold outcome

A cold label is eligible to train causal repair effectiveness only when the
following chain is complete and version-pinned:

```text
locked causal hypothesis set and prior
→ causal decision receipt
→ chosen repair class/intervention
→ remediation episode and exposure
→ independent cold follow-up task
→ served or typed non-service outcome
→ cold result
```

Outcome states include at least:

```text
cold_success
cold_failure
right_censored_expired
learner_declined
unmeasurable_no_held_out_surface
unmeasurable_unservable_surface
contaminated_or_assisted
missing_duration
```

Only a task that was scheduled and had a genuine independent serving
opportunity may become ordinary right-censoring. A missing held-out surface is
structural unmeasurability, not evidence that a repair failed.

### 4.4 Commissioning lineage

One commissioning request records:

```text
request_id
candidate cell bundle
requested instrument class and capability/task-feature contract
goal/recipe/held-out obligations it may unlock
selection score components and competing candidates
selection propensity when randomized
agent_run ids
estimated and actual input/output tokens
generated artifact ids
validation/persona/review/servability outcomes
accepted artifact ids
reachability report before and after
cells and recipes actually unlocked
renderer dependencies
```

Cost is attributed to the request/batch. A multi-item run is not divided among
cells by an arbitrary equal split.

---

## 5. Duration and burden estimation

### 5.1 Diagnostic-question duration

The v1 predictor estimates a distribution over active elapsed time:

```text
log T_q =
    global intercept
  + span
  + response format
  + complexity
  + scaffolding
  + transfer distance
  + prompt/expected-response length
  + nonlinear predicted-success term
  + shrunk surface-family effect
  + residual
```

Rules:

- use real attempt latency as the outcome;
- use authored `expected_seconds` only as a cold-start prior;
- use `surface_family` rather than item random effects while item observations
  remain sparse;
- do not add a learner random effect in a single-learner vault—it is absorbed
  into the intercept;
- do not assume monotone duration by capability rung: span and response form
  can make a shallower multi-step item slower than a deeper short response;
- model the ability–difficulty relationship nonlinearly.

The generative interpretation is:

```text
E[T | learner,item]
    = Σ_o P(o | learner,item) × E[T | o,learner,item]
```

where outcome arms distinguish at least fast success, slow struggle,
abandonment/timeout, and ordinary failure when data supports them. Until then,
a robust family median and interval is preferred to an overfit decomposition.

The decision cost uses a declared conservative statistic from the predictive
distribution. The statistic and its quantile are registered decision
parameters; the mean is not silently assumed.

### 5.2 Repair duration

Repair duration is estimated at the remediation-episode/action level, not from
one arbitrary practice item:

```text
active minutes from repair exposure
through the next switch, success opportunity, or censor boundary
```

Estimator precedence:

```text
repair-class empirical estimate with sufficient support
→ intervention-family estimate
→ pooled empirical estimate
→ conservative heuristic fallback
```

Every `DurationEstimate` retains sample count, interval, censoring share, and
source. A pooled estimate remains a valid fallback but cannot be presented as
repair-specific.

### 5.3 Repair effectiveness

Causal P4's learned half estimates:

```text
P(cold success by horizon | causal state, repair, context)
active minutes until cold success, repair switch, or censoring
```

Logged deterministic choices alone identify outcomes under the selected
policy, not counterfactual repair effectiveness. Hypothesis-grade comparative
claims require overlap from:

- naturally occurring, logged support; or
- bounded randomization among safe near-equivalent repairs through the one
  registered P4 randomization layer.

The learned policy proposes inputs to the transparent staged selector. It does
not become a monolithic action chooser.

---

## 6. Causal diagnostic selection

### 6.1 Feasible set

For a causal factor, enumerate every current-contract active candidate. Before
scoring, exclude candidates failing:

- reviewed/active lifecycle;
- current blind-input contract;
- item and stimulus servability;
- purpose and held-out rules;
- episode ownership/locked-set compatibility;
- learner preference;
- machine-check-first obligations;
- session and recent-diagnostic burden limits;
- manipulation/independence/persona gates.

The candidate-count distribution (`0`, `1`, `2+`) is published before ranking
work is promoted. If almost no decision has multiple feasible candidates,
`active[0]` is a correctness defect with little current selection ROI; the
audit must say so.

### 6.2 Observation likelihoods

Formal EVSI consumes a credible ensemble of:

```text
P(E | H,q)
```

composed through the admitted instrument/card likelihood and calibrated grader
channel. Stored posteriors are never reused as likelihoods.

There are three structural arms:

#### A. Calibrated probabilistic card

Use the existing card/family and grader-channel credible ensemble. This arm may
enter formal EVSI.

#### B. Strict deterministic-signature card

An exact noiseless partition is permitted only when:

- every hypothesis declares exactly one usable feature row;
- every row uses the same complete key schema;
- the row is the full declared emission, not one alternative in a list;
- hypotheses with different signatures cannot match the same observation.

The signature block `B=f(H)` then gives:

```text
I(H;B) = H(prior) - Σ_b P(b) H(prior | b)
```

This is an exact EIG for the declared noiseless channel and an upper bound after
adding response/grader noise. It may license a skip when even the upper bound
is too small. Without a calibrated noise channel it cannot license live learner
effort.

#### C. General overlapping/partial blind bundles

Multiple possible rows, partial key sets, or overlapping matches do not define
a deterministic partition. Pairwise separability remains a structural audit,
not a likelihood.

This arm may use:

- candidate-independent expected value of perfect information (EVPI) as a
  universal skip bound; and
- a future support-constrained maximum-information calculation if implemented
  and tested.

No structural upper bound may be presented as realized EIG or used alone to
offer a live probe.

### 6.3 Loss-table regimes

The action space is the finite set of feasible repair classes/interventions
after constraints. Loss remains expected wasted learner-minutes.

Versioned regimes:

1. **Route + heuristic time:** deterministic effective route, conservative
   duration priors.
2. **Route + empirical time:** deterministic effective route,
   repair/family-specific empirical duration distributions.
3. **Learned effectiveness + empirical time:** cold-outcome model supplies
   repair-effectiveness uncertainty and expected waste.

Every decision states its regime. Regime 1 is not represented as learned.

### 6.4 EVSI and stop

For candidate `q`:

```text
current_loss =
    min_a Σ_h p(h) L(h,a)

future_loss(q) =
    Σ_e P(e|q) min_a Σ_h p(h|e,q) L(h,a)

EVSI(q) =
    current_loss - future_loss(q)
```

Compute point, lower, and upper values over the credible likelihood/loss set.

Candidate ranking:

```text
rank(q) =
    LCB_or_declared_robust_value(q)
    / [expected_minutes(q) + administration_burden_minutes(q)]
```

Stop:

```text
LCB(EVSI(best_q))
    <= expected_minutes(best_q) + burden_margin
```

The precise burden decomposition must avoid charging the same active time in
both denominator terms. Non-time harms remain constraints, dominance rules, or
documented tie-breaks—not minute-equivalent vibes.

### 6.5 Result translation

The staged result maps to the causal path:

| Verdict | Causal behavior |
|---|---|
| `measure` | Offer the selected probe, preserving learner `teach_now` / `not_now` choices |
| `stop` with common action | Apply the shared minimal repair |
| `stop` with current optimal action | Apply that repair under the receipt's declared uncertainty |
| `abstain` from likelihood/ranking instability | Hold branch-specific repair; route to stronger-instrument/review path |
| no feasible candidate | Typed `no_discriminating_instrument`, never an invented hot-path question |

### 6.6 Required shadow baselines

Every shadow decision compares:

1. current P2 pairwise proxy;
2. formal EVSI with the current loss regime;
3. equal-cost/modal-route EVSI;
4. perfect-information skip bound;
5. no-measure/common-repair baseline where applicable.

For equal off-diagonal loss `c=2m`, the modal-route baseline is:

```text
EVSI_equal_cost(q)
    = c × [E_e max_a r_a|e - max_a r_a]
```

Comparing (2) with (1) measures the value of prior weighting, response
likelihoods, ranking, and stopping. Comparing (2) with (3) isolates the value
of repair-specific action costs.

---

## 7. Commissioning selection

### 7.1 Candidate unit

A candidate is an authoring request:

```text
S = {
  learning object,
  one or more target (facet, capability, role) cells,
  intended instrument class,
  task-feature/depth contract,
  held-out/surface requirements,
  recipe/goal obligations
}
```

This permits a conjunctive/capstone item to receive credit for several primary
targets. The post-authoring authority for cells actually observed remains the
compiled rubric target path used by canonical projection and
`exam_pool._item_components`.

### 7.2 Feasibility and dependencies

Before scoring:

- the target capability must be authorable or have a typed dependency;
- blueprint components must be valid and role-correct;
- the requested class must have an admission/persona path;
- off-contract targets are rejected;
- dominance/blueprint-repair dispositions remain typed non-authoring remedies;
- held-out requirements cannot reuse burned surfaces.

Servability state is two-axis:

```text
instrument_validity:
    valid | invalid | unknown

deployment_readiness:
    servable | blocked_on_renderer | blocked_on_surface | unknown
```

Only `valid + servable` counts toward live reachability. A valid
renderer-blocked item remains visible as latent inventory and a renderer
dependency.

### 7.3 V1 structural value

Authoring spends a fixed token budget. It does not require converting tokens
into learner minutes to rank within that budget.

V1 uses an inspectable lexicographic value class, then yield-adjusted marginal
coverage per expected token:

```text
value_class(S), descending:
    1. completes an otherwise structurally certifiable recipe
    2. unblocks held-out/cold-assessment coverage
    3. closes an active-goal decision gap
    4. adds ordinary marginal contract coverage

roi_within_class(S) =
    P(valid_and_admitted | S)
    × marginal_unique_cells_or_surfaces(S)
    / E[actual authoring tokens | S]
```

Tie-breaks, in order:

1. more recipes/held-out obligations unlocked;
2. more unique primary contract cells;
3. a new independent surface family;
4. lower expected token cost;
5. current structural queue order for deterministic stability.

This is deliberately called **expected marginal commissioning value**, not
literal EVSI. Authoring creates future measurement capacity; it does not itself
sample the learner state.

### 7.4 Admission yield

At cold start, `P(valid_and_admitted | S)` is a conservative prior grouped by
instrument class, capability, and authoring route. It updates only from joined
commissioning outcomes:

```text
generated
→ schema-valid
→ persona/admission-valid
→ accepted/reviewed
→ actually closes intended cells
```

An artifact that merely exists is not a successful commission.

### 7.5 Multi-cell diminishing returns

Selection is greedy over the remaining backlog. After each chosen request, its
expected cells/surfaces are removed or discounted before the next pick so two
requests cannot both claim full value for the same obligation.

No `(1-1/e)` guarantee is claimed until the objective is shown to be monotone
submodular under the real bundle/admission model.

### 7.6 Capability-cell posterior

V1 does not use `P(cell below theta)` as a commissioning multiplier:

- the current capability ledger has certification credit and positive/negative
  masses, not a sanctioned posterior over mastery for each capability cell;
- a likely-mastered but unmeasurable cell may still be the highest-priority
  certification gap;
- the relevant authoring quantity is decision pivotality, not only probability
  of learner weakness.

A later probabilistic cell model may enter only after the measurement spec's
inference/posterior authority lands and is calibrated.

### 7.7 Renderer-blocked classes

Error-hunt and laddered-stem items blocked by a missing desktop renderer are not
assigned zero instrument validity.

Policy:

1. permit a small, registered seed/audit inventory sufficient to build and test
   the renderer;
2. exclude that inventory from live reachable-cell counts;
3. after the seed requirement is met, further requests in the blocked class
   defer behind the renderer dependency;
4. delete the dependency arm when the renderer lands and the normal serving
   contract passes.

The seed amount is a registered operational parameter chosen from renderer/test
requirements, not an implicit magic number.

---

## 8. Implementation sequence

### Stage 0 — Documentation and static readiness audit

1. Amend `implementation_plan_v1.md` status language to distinguish causal
   P4 selection from learned repair belief formation.
2. Add a causal-selection readiness report containing:
   - feasible active candidate count distribution;
   - likelihood regime counts;
   - pooled/default/repair-specific duration shares;
   - number of distinct duration estimates per loss table;
   - current P2 versus equal-cost EVSI decision-conversion counts;
   - repair-linked cold outcome and censoring availability.
3. Add a commissioning-readiness report containing:
   - authorable candidate bundles;
   - recipe/held-out/active-goal unlock counts;
   - renderer-blocked obligations;
   - current queue versus proposed value-order conversions;
   - metered versus unmetered authoring runs.

**Exit:** the reports run over both live fixtures, use explicit unavailable
arms, and demonstrate whether each proposed rule can change any decision.

### Stage 1 — Capture and provenance

1. Correct authored time provenance labels.
2. Attach diagnostic and repair context to duration events/receipts.
3. Attach commissioning request lineage to agent runs and artifact outcomes.
4. Preserve censoring, missing duration, and structural unmeasurability as
   separate states.

**Exit:** new attempts and authoring runs are joinable end to end; no historical
value is fabricated or backfilled beyond what immutable records support.

### Stage 2 — Duration estimators and action-loss v2

1. Implement diagnostic family/task-feature duration estimates.
2. Implement remediation episode/repair-family duration estimates.
3. Make `action_loss` consume the estimator hierarchy and intervals.
4. Persist regime/source/sample counts on every shadow loss table.

**Exit:** at least one repair table can carry different empirical duration
estimates when data supports them; otherwise it explicitly remains pooled.

### Stage 3 — Commissioning shadow selector

1. Construct bundle candidates and dependency states.
2. Score them under the v1 structural value policy.
3. Persist competing candidates, score components, token predictions, and the
   incumbent queue winner.
4. Join realized artifacts and reachability deltas when runs complete.

**Exit:** shadow output changes no authoring order; the report can calculate
cells/recipes unlocked per run and per token for incumbent and counterfactual
ordering.

### Stage 4 — Causal EVSI shadow integration

1. Enumerate all feasible active candidates.
2. Build calibrated likelihood ensembles or typed structural-bound arms.
3. Adapt the locked causal factor into `DiagnosticSelector`.
4. Run the existing staged EVSI selector without live authority.
5. Persist all baselines from §6.6 and would-change fields.

**Exit:** replay is deterministic from pinned inputs; arbitrary shadow output
cannot alter the live causal journey.

### Stage 5 — Evidence-based live cutovers

Commissioning and causal selection promote independently.

Commissioning cutover changes only which already-feasible authoring requests
consume a fixed budget.

Causal cutover replaces the P2 proxy only within the feasible diagnostic set;
all P2 firewalls and learner choices remain.

**Exit:** promotion manifests satisfy §9; rollback restores the incumbent policy
without losing telemetry.

### Stage 6 — Causal P4 learned repair effectiveness

1. Accrue repair-linked cold outcomes.
2. Publish overlap, censoring, servability, duration, and effective-sample-size
   readiness.
3. Use the one randomization layer only among safe near-equivalent repairs.
4. Train and prequentially evaluate effectiveness/duration inputs.
5. Promote learned inputs independently into the transparent selector.

**Exit:** a learned input changes no live decision until its own promotion
manifest passes; original causal receipts remain immutable.

---

## 9. Promotion and rollback gates

### 9.1 Causal selection readiness

All are required:

- nonzero volume of decisions with a formal likelihood ensemble;
- candidate multiplicity reported; if ranking is claimed, meaningful `2+`
  candidate volume;
- robust interval-width viability inside the registered abstention budget;
- duration-capture completeness reported and no missing-as-zero path;
- deterministic replay from pinned prior, candidates, likelihoods, loss table,
  and parameter manifest;
- shadow firewall test proves zero live authority.

### 9.2 Causal value tests

Two comparisons are distinct:

#### A. Formal selector versus current P2 proxy

Measures the combined effect of:

- prior weighting;
- response likelihoods;
- candidate ranking;
- time normalization;
- absolute EVSI stopping.

Promotion requires a pre-registered nontrivial decision-conversion rate and
better held-out/prequential decision quality or bounded live evidence.

#### B. Full loss versus equal-cost/modal-route EVSI

Measures only whether repair-specific costs add decision information.

If the full selector never differs from the equal-cost baseline, the
nonuniform loss model remains shadow/dormant. Nonzero divergence is necessary,
not sufficient: estimates must also calibrate and improve downstream regret or
cold outcomes.

### 9.3 Commissioning promotion

Required:

- request→run→artifact→admission→reachability lineage coverage reported;
- metered cost coverage above a registered threshold;
- no invalid/unservable artifact counted as live reachability;
- shadow ordering converts a nontrivial number of requests;
- on replay or prospective shadow, no worse accepted/servable yield and better
  at least one of:
  - recipes made structurally certifiable per run;
  - held-out obligations unlocked per run;
  - reachable primary cells per run;
  - reachable primary cells per actual token;
- renderer-blocked inventory remains capped and visible.

### 9.4 Learned repair policy promotion

Required:

- repair-linked independent cold outcomes, not certification-only outcomes
  lacking the causal/repair chain;
- effective sample size by relevant repair/state slice;
- explicit right-censor and structural-unmeasurability rates;
- logged action propensities and overlap for comparative claims;
- prequential cold-success calibration;
- duration calibration;
- no regression in:
  - `problems_to_cold_success`;
  - `learner_minutes_to_cold_success`;
  - `harmful_write_rate`;
  - diagnostic burden/probes per resolved episode.

No numeric threshold is invented in this document. Each threshold is
registered with sensitivity coverage and a promotion manifest before it binds.

---

## 10. Metrics and receipts

### 10.1 Causal shadow receipt

```text
schema/version
factor id + locked hypothesis-set id/version
prior
feasible candidate ids and exclusion reasons
likelihood regime + ensemble refs
loss-table regime/hash
duration estimates + provenance
incumbent P2 decision
formal EVSI verdict and best candidate
equal-cost baseline verdict
EVPI skip bound
point/LCB/UCB values
per-emission downstream actions
winner/action flip flags
would_change_candidate
would_change_measure_vs_repair
would_change_repair
parameter manifest
```

### 10.2 Commissioning shadow receipt

```text
schema/version
reachability-report hash
candidate request bundles
hard exclusions/dependencies
value class
admission-yield estimate + provenance
marginal cells/surfaces/recipes
expected tokens + provenance
incumbent queue winner
shadow winner
would_change_order
selection propensity
realized run/artifact/admission/reachability outcome refs
```

### 10.3 Aggregate metrics

Add or extend:

- feasible causal candidates per factor (`0/1/2+`);
- formal-likelihood availability rate;
- P2→EVSI measure/stop conversion rate;
- P2→EVSI candidate-change rate;
- full-loss→equal-cost decision divergence;
- duration source shares and interval coverage;
- diagnostic duration prediction error/calibration;
- repair duration prediction error/calibration;
- cold-outcome structural-unmeasurability/censoring rates;
- commissioning order-conversion rate;
- accepted-and-servable artifacts per authoring run;
- reachable primary cells per actual authoring token;
- recipes/held-out obligations unlocked per authoring run;
- renderer-blocked valid inventory count.

Every empty denominator returns an unavailable arm, never a favorable zero.

---

## 11. Test and validation matrix

### 11.1 Causal selector

- all hypotheses map to one repair → EVSI/action value zero and common repair;
- skewed prior with tail-only separation → lower value than unweighted pair
  proxy;
- two candidates with different likelihoods and times → correct robust winner;
- informative but too-slow candidate → stop;
- likelihood/action winner flips across credible members → abstain;
- no formal likelihood → no live probe licensed;
- strict deterministic-signature card → exact partition EIG;
- multiple/partial/overlapping rows → partition arm rejected;
- EVPI below burden → universal skip;
- equal durations → modal-repair baseline formula;
- nonuniform tagged durations → loss table can change candidate/repair;
- missing duration never becomes zero;
- shadow selector mutation injection changes no live state.

### 11.2 Timing

- authored prior used with zero observations and labelled correctly;
- family estimate shrinks sparse observations;
- repair-class estimate outranks pooled only with declared support;
- timeout/abandonment and missing duration remain distinct;
- no learner random-effect claim at one learner;
- replay reproduces estimates from immutable events and pinned versions.

### 11.3 Commissioning

- recipe-completing bundle outranks ordinary coverage within feasibility;
- one multi-cell item receives marginal credit once, not once per duplicate
  request;
- actual compiled primary targets, not model promises, determine realized
  closure;
- rejected artifact yields no reachability gain;
- valid renderer-blocked item is not live-reachable and not marked invalid;
- renderer-blocked seed cap converts later requests to dependency deferrals;
- dominance and blueprint-repair rows never enter the authoring feasible set;
- actual batch tokens stay attached to the batch;
- shadow commissioning cannot launch an agent run or mutate content;
- ordering/replay is deterministic under equal score components.

### 11.4 Learned repair policy

- cold success/failure joins only through a complete pinned chain;
- no held-out surface reports structural unmeasurability, not failure/censor;
- expired genuinely servable task reports right censoring;
- assisted/contaminated cold attempt is excluded;
- deterministic policy with no overlap refuses comparative causal promotion;
- one-randomization-layer propensities replay exactly;
- learned effectiveness changes an input receipt, never an old diagnosis.

---

## 12. Change surface

Expected existing consumers:

- `services/causal_orchestrator.py`
- `services/causal_probe_coherence.py`
- `services/action_loss.py`
- `services/evsi.py`
- `services/staged_policy.py`
- `services/probe_robust.py`
- `services/probe_episodes.py`
- `services/contract_reachability.py`
- `services/contract_commissioning.py`
- `services/practice_generation.py`
- `services/instrument_serving.py`
- `services/scoreboard.py`
- agent-run/proposal and interaction-event repository paths
- CLI/sidecar measurement and causal-audit surfaces

Likely new bounded modules:

- `services/causal_selection_audit.py` — readiness and baseline comparisons;
- `services/duration_estimation.py` — versioned diagnostic/repair duration
  estimates;
- `services/causal_diagnostic_selector.py` — causal-factor adapter into the
  existing staged EVSI selector;
- `services/commissioning_value.py` — candidate bundles, dependencies, shadow
  value policy, and receipts.

Schema growth is conditional:

- prefer append-only payloads and existing lineage tables for first capture;
- add indexes/columns only for demonstrated query or integrity needs;
- any new durable shadow receipt is append-only and carries input hashes;
- no migration backfills unavailable historical duration, propensities, or
  cold-outcome links.

---

## 13. Work packages

| Package | Deliverable | Depends on | Learner authority |
|---|---|---|---|
| WP0 | P4 split clarification + readiness audits | none | none |
| WP1 | Timing/commissioning lineage + provenance correction | WP0 | none |
| WP2 | Duration estimators + action-loss regimes | WP1 | none |
| WP3 | Commissioning bundle/value shadow selector | WP0–WP1 | none |
| WP4 | Causal likelihood adapter + all-candidate enumeration | WP0–WP2 | none |
| WP5 | Causal staged-EVSI shadow integration + receipts | WP4 | none |
| WP6 | Independent commissioning cutover | WP3 promotion gate | authoring order only |
| WP7 | Independent causal-selection cutover | WP5 promotion gate | feasible diagnostic selection/stop only |
| WP8 | Repair-linked cold corpus + readiness manifest | WP1 and Stage-4.2 flow | none |
| WP9 | Learned repair-effectiveness inputs | WP8 + overlap gate | shadow input only |
| WP10 | Learned-input promotion | WP9 promotion gate | input to transparent selector |

Recommended implementation order:

```text
WP0
→ WP1
→ WP2 and WP3
→ WP4
→ WP5
→ independent WP6/WP7 decisions
→ WP8–WP10 when cold volume permits
```

Commissioning and causal selection intentionally do not block each other after
the shared capture substrate.

---

## 14. Resolved decisions and remaining questions

### 14.1 Resolved here

1. Formal causal probe-versus-repair uses EVSI, not EIG alone.
2. EIG retains hypothesis-naming and predictive-coverage roles.
3. The present pairwise product is a structural incumbent/baseline, not formal
   information gain.
4. `active[0]` is replaced by feasible all-candidate enumeration, but its
   realized ROI is measured by the `2+` candidate precheck.
5. Authored time is a prior, real duration is the outcome, and missing is not
   zero.
6. Learner random effects are not fit in a single-learner vault; sparse item
   effects shrink at surface-family grain.
7. Commissioning ranks authoring bundles under a fixed token budget.
8. V1 commissioning uses structural decision pivotality, not an invented
   capability-cell posterior.
9. Renderer-blocked valid instruments form a typed dependency backlog and do
   not count as reachable.
10. Cold outcomes learn repair effectiveness; they never rewrite the original
    diagnosis.

### 14.2 To resolve from readiness evidence

1. Which conservative duration statistic binds the live stop rule.
2. Minimum support for repair-class duration to outrank family/pooled estimates.
3. Whether enough causal factors have multiple active candidates to justify
   live ranking now.
4. Whether existing instrument-card/grader ensembles cover enough causal
   candidates for formal EVSI.
5. Renderer seed requirements for each blocked instrument class.
6. Commissioning promotion thresholds after baseline replay.
7. Repair-effectiveness minimum effective sample size and overlap requirements.

These become registered decision parameters only after the Stage-0/Stage-1
reports expose their sensitivity ranges. They are not guessed in advance.

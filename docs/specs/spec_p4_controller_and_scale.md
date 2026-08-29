# P4 implementation spec: controller, scale, and open-world diagnosis

**Status:** Draft v0.2, code-audited 2026-07-16; depth contract amended
2026-07-17; orphan/n=1 consensus folded in 2026-07-17
**Parent:** `spec_new_improvements_v2.md` (P4 delivery phase, controller
unification B, and Layer 4)
**Depends on:** P0 measurement correctness, P1 shared substrate, the P2 golden
path, and P3 hypothesis-seed/interaction contracts
**Acceptance focus:** global staged-policy control, shadow evaluation, robust
EVSI, dispersion/interleaving, and Journey 8
**Ownership claims** (`spec_ownership_ledger.md`, pinned at the 2026-07-17
seed): implements U-023@v1 (constrained decision-cost hierarchy), U-024@v1
(one randomization layer), U-025@v1 (scorer decomposition; monolithic
promotion deferred), U-026@v1 (kernel as heuristic LLM-judged feature;
learned weights deferred); defers U-011 (affect auto-downgrade enforcement)
behind the auto-depth package (U-018). Updated 2026-07-18: owns the U-017@v3
shadow path — reader-question timing/pattern-choice policies learn only in
shadow, scored against next-spaced-cold-outcome horizons (§7.1).

P4 generalizes the proven P2 loop across commitments without handing live
authority to an unvalidated score. The live controller is a transparent
two-level staged policy over a constraint-filtered feasible set. Shadow work
decomposes into promotable *predictive components* and a permanently
transparent action chooser (§7). P4 also evaluates the global familiarity
kernel as a heuristic LLM-judged feature, runs all policy experimentation
through one randomization layer, and—only after those foundations pass—adds
versioned open-world hypothesis expansion.

No component in this phase performs MCTS. No shadow output changes the learner's
live activity, evidence, posterior, surface lifecycle, or claim.

---

## 1. Outcome and boundaries

At P4 exit:

- every live choice belongs to the canonical action taxonomy and has an
  inspectable staged-policy trace;
- the controller first chooses a coherent 5–15 minute attention block, then an
  activity inside it;
- an achieved milestone can automatically activate one reviewed next-depth edge
  inside the current learner-confirmed envelope, with a complete successor and
  lineage receipt;
- held-out protection, learner intent, purpose, fatigue, familiarity,
  same-facet dispersion, and stage-aware interleaving are feasible-set
  constraints—not weighted suggestions;
- diagnostic selection can use robust expected value of sample information
  (EVSI), with hypothesis/predictive EIG retained for their proper purposes;
- the scored controller and soft-familiarity kernel produce versioned shadow
  predictions with propensities/outcome joins;
- repeated model misspecification can produce a provisional HypothesisCard and
  immutable successor hypothesis set without mutating an open episode;
- the learner can inspect and contest a diagnosis, propose another explanation,
  receive a bounded-trust discriminating probe, and see the successor result;
- short-session and hiatus/re-entry contexts use the same controller contracts
  without requiring the deferred journeys home screen.

### 1.1 Canonical action taxonomy

Every live decision uses exactly one top-level action:

```text
measure_diagnostic
instruct
practice
assess_terminal
maintain
expand_model
stop
```

Repair, completion, transfer, integration, and `depth_progression` are
`practice` subtypes.
Baseline/readiness/re-entry measurement may use predictive EIG but remains
`measure_diagnostic`. Open-world authoring/validation is `expand_model`; it is
not disguised as more measurement.

### 1.2 Non-negotiable invariants

1. **Constraints precede scores.** A score can rank only candidates already
   allowed by purpose, held-out, intent, burden, fatigue, exposure,
   dispersion/interleaving, and administration-context rules.
2. **Live policy is staged and inspectable.** It does not reduce measure,
   teach, practice, assessment, maintenance, and stop to one weighted sum.
3. **Shadow means zero authority.** A shadow scorer/kernel cannot reorder,
   select, stop, expose, reserve, grade, update, or phrase a live claim.
4. **One-step only.** Within-measure selection is greedy. The outer scorer has
   at most a one-block horizon. No rollout tree, MCTS, or hidden multistep
   optimizer is permitted.
5. **Ranking and stopping differ.** Burden-normalized value ranks candidates;
   positive robust net value is required to continue measuring.
6. **Goal-conditioned prediction is frozen.** Predictive EIG evaluates the
   pinned target distribution, never an ID-ordered slice of currently eligible
   probes.
7. **Measurement closes before learning.** Instruction/practice ends the
   current diagnostic segment. Later cold evidence opens a new segment.
8. **Hypothesis sets are immutable snapshots.** Expansion creates a successor
   set and normally a successor episode; it never inserts into an open set.
9. **`other_or_unknown` is an alarm, not a diagnosis.** It can trigger model
   review but can never be named as the learner's misconception.
10. **Discovery is not confirmation.** Candidate-generation evidence may move
    only a bounded share of open-set mass. Active status needs prospective,
    independent confirmation.
11. **Global exposure stays global.** Hard collisions remain deterministic P1
    authority. A learned soft kernel can never make a hard collision fresh.
12. **Affect/reading signals are constraints/intent/salience, not reward.** The
    controller does not optimize engagement, valence, or dwell.
13. **Learner authorization bounds escalation.** The staged controller may
    automatically select `practice(depth_progression)` only along one reviewed,
    evidence-gated edge wholly inside the current DepthEnvelope. No score,
    shadow model, or future learned controller may widen/cross that envelope,
    recursively climb, or erase prior milestone attainment.
14. **Calibration status remains operative.** Heuristic intervals widen robust
    bounds and temper language; no categorical claim is manufactured by the
    controller.

### 1.3 In scope

- global two-level staged controller and event-backed decision traces;
- canonical failure-reason triage integration;
- feasible-set constraint engine and coherent attention blocks;
- robust EVSI, correct EIG roles, burden ranking, and stop rules;
- goal weighting through P0 target contracts and P1 commitment priority;
- live enforcement of P1 depth policy/envelopes and one-edge automatic
  progression through P0/P1 successor services;
- one global soft-familiarity kernel as a versioned heuristic LLM-judged
  kinship feature behind a sim admission gate (learned weight training
  deferred, U-026);
- stage-aware same-facet dispersion and interleaving via one randomization
  layer (U-024);
- versioned shadow predictive components (retrievability, expected success,
  expected duration), logging, prequential evaluation, and their promotion
  contract; monolithic action-chooser promotion explicitly deferred (U-025);
- open-world HypothesisCards, immutable set successors, triggers,
  retrieve→generate→validate, confirmation, retirement, and disagreement UI;
- re-entry/three-minute adapters and full sim/replay/operability tests.

### 1.4 Explicitly out of scope

- making any learned/scored action chooser live — monolithic promotion has no
  reachable evidence path at n=1 and is deferred indefinitely (U-025);
- learned taste/salience/engagement optimization;
- MCTS or any planner beyond one attention block;
- cross-learner card/hypothesis promotion;
- more than two hypothesis scopes (`lo_local`, `facet`);
- five-level scopes, six-state hypothesis lifecycles, or ontology-wide
  automatic restructuring;
- synthetic recurrence-based domain-template promotion;
- syntopic reader UI, browser capture, voice, VOD, or the final journeys home
  information architecture;
- unbounded, unreviewed, cross-commitment, or outside-envelope automatic depth
  expansion; inside-envelope `authorized_depth_step` successors are in scope;
- causal claims from underpowered single-learner experiments.

---

## 2. Verified code-truth ledger

| Area | Verified reality | P4 consequence |
|---|---|---|
| Live queue | `scheduler._priority` is a weighted sum of forgetting risk, goal frontier, recent error, and probe EIG (`scheduler.py:645-651`); `score_selection_reward` adds more hand-weighted components by intent (`selection_rewards.py:113-206`). | Replace live cross-mode authority with a staged feasible-set controller; retain old ranking as a logged compatibility comparator. |
| Queue composition | The current scheduler sorts selection reward, then layers exploration, caps, goal/request floors, same-day item rotation, follow-ups, and probe commitment (`scheduler.py:281-420`). | Preserve useful eligibility/commitment seams but make constraint order explicit and event-versioned. |
| Session context | `SchedulerSession` has available minutes and energy (`scheduler.py:37-42`). | Extend into a controller snapshot and attention-block budget rather than creating another session identity. |
| Existing shadow | `intent_planner.py` is explicitly shadow-only and classifies six legacy intents from an already-built live queue (`intent_planner.py:1-18,29-107`). | Migrate telemetry into the canonical action taxonomy; do not accidentally promote its fixed priority order. |
| Slate telemetry | Scheduler slates already record considered candidates, propensities, config, selection policy, and shadow intent. | Reuse/extend for off-policy evaluation and exact live-vs-shadow joins. |
| Limited spacing | `_rotate_same_day_frontier_repeats` only moves an item attempted today behind other frontier items (`scheduler.py:509-543`). | Add facet/capability/kinship-aware dispersion; preserve lapse-retry exemptions explicitly. |
| Interleaving | No stage-aware interleaving constraint exists. | Add as a feasible-set/session-composition policy with experiments, not a reward coefficient. |
| Predictive targets | Probe predictive EIG currently sorts eligible instruments by item id and caps that pool (`probe_episodes.py:449-466`). | Build the target set from the pinned goal-contract distribution and held-out target cards. |
| Within-probe ranking | Probe candidates already compute predictive information per expected second, hypothesis EIG fallback, and a separate redundancy penalty (`probe_episodes.py:467-510`). | Reuse this calculation, add calibrated grader channel/robust likelihood sets and the distinct net-value stop rule. |
| Open set | Current episodes reserve `other_or_unknown`; block end only creates a deduplicated `open_set_misconception_review` generation need while keeping the set locked (`probe_blocks.py:97-135`). | Preserve the trigger/immutability, then implement typed transition, candidate authoring, successor sets, and validation. |
| Hypothesis storage | Existing `hypothesis_sets` stores hypotheses/prior as JSON with no normalized versioned HypothesisCard membership/lineage (`migrations/001_initial.sql:276-286`). | Normalize additively; adapt historical JSON snapshots without rewriting them. |
| Reprobe triggers | Repeated negative predictive surprise and stale uncertainty already reopen episodes (`probe_episodes.py:256-348`). | Feed typed expansion triggers, but stop treating every misspecification signal as merely “probe again with the same model.” |
| Residual analysis | `residual_diagnostics.py` deterministically reports missing-factor, integration, context-divergence, and identifiability suggestions but mutates nothing. | Use reviewed findings as expansion discovery evidence, never automatic hypothesis creation. |
| Grader disagreement | Regrades/audits record disagreement and P0 makes grades append-only/calibrated. | Add a systematic disagreement trigger over P0 true-class interpretations, not raw score changes alone. |
| Re-entry | `reentry_summary.py` compares FSRS-style facet projections before/after a hiatus and excludes held-flat facets, but does not run a target-distribution assessment. | Keep its humane summary; add bounded predictive-EIG re-entry measurement under the controller. |

---

## 3. Controller snapshots and durable decisions

### 3.1 ControllerSnapshot

Build one immutable, content-hashed snapshot per decision from:

- active commitments, versions, dispositions, depth preset, policy/envelope
  versions, current/reached/next milestones, and burden bounds;
- current P0 goal-contract heads and any consumer pins;
- target-boundary cells, intervals, contest/quarantine state;
- P1 family/card progression, due state, angle coverage, and activity purpose;
- current/open diagnostic segments and hypothesis-set pins;
- assessment reserves and global exposure/freshness state;
- surface familiarity/kinship projections available **before** selection;
- recent failure-triage and lapse/follow-up events;
- session id, available minutes, energy, accumulated fatigue/burden;
- in-flight committed administration/attention block;
- policy, calibration, decision-parameter, and projection versions.

The snapshot contains no cold-answer material. Reads are bulk/bounded; the
controller may not issue one database query per candidate.

### 3.2 Persistence

Create/extend:

- `controller_snapshots` — immutable canonical input/hash;
- `controller_decisions` — live action/block/activity, stage reason, policy
  version, expected head, and outcome linkage;
- `controller_candidates` — every considered candidate with feasibility,
  exclusion reasons, within-mode metrics, and selected flag;
- `attention_blocks` and append-only block events;
- `controller_shadow_predictions` — scorer/kernel output with no authority;
- `controller_outcome_windows` — delayed unseen outcomes joined at declared
  horizons;
- `policy_experiment_assignments` — safe randomized variant and propensity;
- `controller_projection_heads` — rebuildable current heads only.

Decision, administration-open, and scheduler-slate/outbox writes share one
idempotent transaction boundary. A retry cannot select a different candidate
after the first is committed.

### 3.3 Trace contract

Every decision receipt contains:

```text
live action and subtype
attention-block commitment/intent
staged rule that fired
constraints applied and excluded alternatives
goal-contract version(s) evaluated
depth-policy/envelope version and current/next milestone edge
selected family/card/surface and familiarity
expected time/burden and remaining budget
measurement/value model versions when applicable
shadow disagreement, shown only in debug/research surfaces
stop/continue alternatives
```

Learner-facing “why” copy comes from the staged reason and commitment—not the
largest opaque score term.

---

## 4. Live two-level staged policy

### 4.1 Level one: attention block

Choose one coherent 5–15 minute block defined by:

```text
commitment neighborhood + canonical action + subtype + budget + exit rules
```

Block candidates include explicit learner continuation, active P2/arc work,
bounded diagnosis, source-grounded instruction, practice/repair/integration,
terminal assessment, maintenance, re-entry, and stop. Context-switch cost is
handled here, not charged independently to every item.

An already served administration wins over replanning. An explicit learner
choice within constraints wins over autonomous ranking and is logged as such.
One activity may be a complete three-minute block.

### 4.2 Global staged rule

After continuation/explicit-choice handling, apply:

```text
if a valid failure triage already determines the next repair:
    choose that instruct/practice block
elif current model misspecification prevents an action-safe conclusion:
    expand_model, or stop/pause with a safe common intervention
elif decision-relevant uncertainty has positive robust sampling value:
    measure_diagnostic
elif target knowledge is not acquired:
    instruct
elif capability is scaffold-dependent or fragile:
    practice(completion_or_repair)
elif components are present but whole-task integration fails:
    practice(integration)
elif terminal performance is required but not shown and a valid reserve exists:
    assess_terminal
elif the current milestone is reached, policy is `auto_within_envelope`, and
     one reviewed next edge is feasible and has positive robust continuation value:
    practice(depth_progression)
elif retention is approaching its contract limit:
    maintain
else:
    stop or propose a depth-envelope successor
```

`practice(depth_progression)` first records the predecessor milestone as
reached, then calls the P1 one-edge transition service. Under
`auto_within_envelope` it may activate the edge. Under `suggest_next` or
`hold_at_target`, the automatic action is infeasible; the fallback may render a
proposal or stop/maintain. A terminal-support delta is committed through P0 as
`authorized_depth_step` with a distinct fresh-reserve requirement. The
controller replans before another edge and never treats “too easy” alone as
authorization.

Live `auto_within_envelope` authority arrives only with the auto-depth
package (U-018); until that package ships, `suggest_next` proposals are the
live depth behavior. When it ships, P4 owns live enforcement of the affect
auto-downgrade (U-011): repeated negative affect (`felt_rote`,
`not_worth_my_attention`) on a commitment's families downgrades
`auto_within_envelope` to `suggest_next` pending re-confirmation, evaluated
before any depth edge is committed. The signal stream is live from P0
(U-010), so the dead-man switch launches calibrated, not untested.

“Expand model” is chosen only when the available hypotheses cannot support the
decision, not merely because another interesting explanation could be named.
Expansion work usually happens off the learner hot path; the immediate block
may stop, ask a clarification, or use an intervention valid across candidates.

### 4.3 Failure-reason gate

Before opening a diagnostic episode for a miss, consume P2's canonical triage:

- memory lapse -> reveal/reconstruct + next-day practice;
- missing knowledge -> instruct;
- conceptual hole -> explain/compare;
- procedure execution -> completion/faded repair;
- method selection -> setup/move spotting;
- coordination -> integration practice;
- false belief/ambiguous actionable cause -> measure;
- bad surface/grade -> quarantine/adjudicate;
- model misspecification -> expand.

Diagnosis is not the default punishment for failure. A triage correction
appends a successor and reprojects the next decision; it never rewrites the
attempt.

### 4.4 Level two: within-block selection

Within the chosen block:

1. enumerate P1 purpose-compatible cards/surfaces;
2. apply all hard/soft feasibility constraints;
3. use the block-specific transparent selector (due order, stage contract,
   robust EVSI/EIG, target-distribution sampling, or P1 progression);
4. commit one administration or a small precommitted diagnostic block;
5. stop/replan on block exit, fatigue, changed state, or learner action.

No score can trade a held-out collision against high goal weight or a
same-facet spacing violation against expected gain.

### 4.5 Stop behavior

`stop` is a successful action with typed reasons:

```text
goal_satisfied
goal_satisfied_no_authorized_depth
no_positive_robust_value
same_action_across_hypotheses
burden_or_fatigue_cap
waiting_for_delay_or_fresh_surface
model_expansion_needed
learner_paused_or_stopped
no_feasible_activity
```

It may offer one optional next step, but never a guilt-inducing backlog. “One
item completed” is a valid session completion.

---

## 5. Feasible-set constraints

Implement a versioned constraint engine whose output for every candidate is
`eligible` or a typed list of exclusion/defer reasons.

Launch constraints:

- immutable purpose and administration-context compatibility;
- P0 target-contract/assessment reservation and leakage/burn rules;
- P1 commitment disposition, depth policy/envelope/current milestone, and
  burden bounds;
- card/family active status, lineage, gate, quarantine, and outcome-schema
  validity;
- global exact/hard exposure collision and declared soft-familiarity ceiling;
- no opportunistic diagnostic episode update;
- task-feature/goal-support coverage;
- same-facet/capability/kinship dispersion;
- stage-aware interleaving/block coherence;
- fatigue, remaining minutes, expected duration, and answer-reveal budget;
- source/annotation cue suppression during cold work;
- pending grade/adjudication or model-expansion dependency;
- explicit learner accessibility/tool constraints.

Depth constraints are evaluated structurally before ranking: the candidate edge
must be reviewed, originate at the current reached milestone, lie wholly inside
every capability/TaskFeature/support bound, fit remaining burden, have admitted
successor activities, and satisfy fresh-proof prerequisites. Missing or stale
authorization excludes the candidate. A high estimated gain cannot compensate
for any violation.

Constraint versions and parameter manifests are snapshotted on decisions and
administrations. Missing data fails according to the underlying contract:
unknown freshness blocks unseen claims but not ordinary instruction; unknown
duration may fit only when conservative upper bound fits the budget.

---

## 6. Robust measurement value

### 6.1 Observation model

P4 uses P0's generative chain:

```text
H (learner hypothesis) -> Z (true coarse outcome) -> E=(G, confidence bucket)
```

Candidate calculations integrate over calibrated `P(E | Z)` and the card's
uncertain `P(Z | H)`. They never substitute stored `P(Z | E)` as a likelihood
or multiply correlated regrades.

### 6.2 Action loss

For a frozen hypothesis set, define a reviewed loss table
`L(hypothesis, downstream_action)` over the finite feasible interventions,
under the constrained decision-cost hierarchy (U-023): correctness, safety,
and learner-intent constraints define feasibility first; among feasible
interventions, loss is **expected wasted learner-minutes** — time spent on an
ineffective intervention plus delay until the effective one — when the
hypothesis is true. Entries are *derived* from triage-route structure and
activity duration estimates (durations from logged attempts), never elicited
as free constants. `lambda_time ≡ 1` because minutes are the cost numéraire;
burden is measured in minutes, not weighted. Non-time harms enter only as
constraint thresholds (e.g. a misgrade-risk ceiling per certification claim),
a dominance filter, or a documented tie-break order — never as informal
weights. Each route/loss entry is versioned, scoped, calibration-labeled,
registered, and inspectable, with its expected-minutes derivation attached.

If every plausible hypothesis maps to the same optimal action, measurement
has no action value and the controller uses that common action. "Same optimal
action within tolerance" is defined in decision space — the argmin action set
is identical across the credible loss/likelihood draws — never as closeness
of loss values.

### 6.3 EVSI

For candidate question `q` and current belief `p(h)`:

```text
current_loss = min_a sum_h p(h) L(h,a)

future_loss(q) =
  sum_e P(e | q) min_a sum_h p(h | e,q) L(h,a)

EVSI(q) = current_loss - future_loss(q)
```

Compute EVSI over a credible set of grader and instrument likelihood matrices.
Persist point estimate, lower/upper bounds, matrices/model ids sampled, and
which action would be selected for each emission.

Default selection preference inside a decision-changing diagnostic episode:

1. robust EVSI when hypotheses imply different interventions;
2. hypothesis EIG when naming the distinction is itself required for a
   contestable explanation/Journey 8;
3. predictive EIG for coverage/baseline/re-entry/readiness against a frozen
   target distribution;
4. no measurement when none has positive robust net value.

### 6.4 Ranking vs stop

Ranking metric:

```text
rank(q) = robust_value(q) / (expected_seconds(q) + burden_equivalent_seconds(q))
```

The selected robust value may be the expected value or conservative bound as
the policy declares. Stop condition is not that ratio:

```text
LCB(EVSI(q)) <= lambda_time * expected_seconds(q) + burden_cost(q)
```

for the best feasible `q`, or any other typed stop condition in §4.5.
`lambda_time ≡ 1` under the minutes numéraire (U-023) and `burden_cost(q)` is
measured in minutes from logged attempt durations; remaining thresholds are
decision parameters. A zero/positive EIG cannot by itself force another
question.

### 6.5 Robustness and abstention

At minimum evaluate:

- P0 credible intervals for the grader channel;
- card/family likelihood credible intervals;
- a bounded ±0.15 probability perturbation stress test, renormalized per row,
  for open-world admission/comparison;
- plausible response-duration/burden bounds.

If candidate rank or downstream action flips across credible/stress matrices,
abstain, choose a robustly dominant candidate, or author a stronger instrument.
Log the flip; never hide it behind a mean score.

### 6.6 Goal-conditioned predictive EIG

Build predictive targets from the exact P0 contract version pinned for the
measurement context:

- target exemplar/blueprint distribution and weights;
- required capabilities/task-feature cells;
- terminal representation/response/tool/time conditions;
- held-out target cards/surfaces or calibrated abstract target emissions;
- unseen surface-group constraints.

Do not use candidate enumeration/ID order as the target distribution. Exclude
the candidate being considered from its own target set. Store the target-set
hash and coverage gaps on the selection trace.

---

## 7. Shadow predictive components and the deferred scored selector

### 7.1 Role and output

The scored selector decomposes into two parts with different fates (U-025):

- **Predictive components** — retrievability, expected success, and expected
  duration models. Each is individually promotable via prequential held-out
  scoring (log-loss/Brier on live predictions made under the policy that
  actually selected the work). A promoted component feeds the staged policy's
  *inputs*; it never chooses actions.
- **The action chooser** — stays the transparent staged policy indefinitely.
  Monolithic action-chooser promotion has no reachable evidence path at n=1:
  the live incumbent is deterministic, so propensities are degenerate and
  off-policy support is near-empty outside the randomization layer (§9.3).
  It is deferred, not pending.

In shadow, the composed selector receives the same controller snapshot and
feasible set, then predicts for each action/block candidate:

```text
expected goal-weighted delayed unseen performance gained or preserved
---------------------------------------------------------------------
                 expected learner minutes + burden
```

It may produce one-step rankings for `measure`, `teach`, `maintain`, `expand`,
and `stop`, plus uncertainty and feature attribution. It never gets access to
future outcomes or post-selection features at prediction time.

The same predictive-component discipline covers reader-question policy
(U-017@v3): models of when to ask during reading, which pattern to serve,
and how much interruption this learner tolerates are individually promotable
predictive components scored prequentially against the **next spaced cold
outcome on the questioned target — never immediate answer success** — using
the live U-033/P3 reader events (presented / skipped / answered / disposition
/ per-question controls). The live insertion policy stays owner-placed static
placement until a component earns promotion; even then it feeds the staged
policy's inputs and never inserts questions on its own authority.

The selector sees only depth candidates already admitted by the structural
envelope constraint. It may rank an eligible `practice(depth_progression)`
against maintenance/stop, but may not propose a new milestone, widen an
envelope, change policy, or score an outside-envelope action as a live
alternative. Shadow telemetry retains the exclusion even when the model would
have preferred the forbidden action.

The canonical live action taxonomy maps to shadow modes as:

| Live action | Shadow mode |
|---|---|
| measure_diagnostic / assess_terminal | measure |
| instruct / practice | teach |
| maintain | maintain |
| expand_model | expand |
| stop | stop |

Assessment remains purpose-distinct even though its predictive objective is
measurement.

### 7.2 Data and leakage discipline

For each live decision, record:

- identical predecision snapshot hash;
- full feasible candidate set and live propensity;
- live staged action and shadow action/ranking;
- prediction uncertainty/model version;
- delayed outcomes at predeclared horizons, especially fresh target-like
  performance, retention, burden, and stop/abandonment;
- missingness/censoring and whether instruction changed the target before
  outcome measurement.

Never train/evaluate on the assessment surface text or outcome before its
decision. Split by time and target family to prevent near-clone leakage; a
surface-group split is deferred until the outcome window carries a surface-group
key (it is not faked from absent state — see §18). Reading/affect signals may
describe intent/burden but cannot be a proxy reward for correctness.

### 7.3 Offline comparison

Use direct held-out prediction plus propensity-aware IPS/doubly robust
estimates where support exists. Because the live policy is deterministic,
nontrivial propensity support exists only inside the §9.3 randomization
layer; expect and report near-empty support elsewhere rather than
extrapolating. Compare at the attention-block policy level and within-mode
selection separately. Prequential component reports (calibration of
retrievability / expected-success / duration predictions) are the primary
product; the composed-selector comparison is secondary telemetry.

Minimum reports:

- calibration/error of delayed-performance and burden predictions;
- live-vs-shadow disagreement matrix by action/reason;
- estimated outcome difference with interval and effective sample size;
- constraint-violation audit (must be zero even in shadow output);
- subgroup/scope breakdown by goal/task family, capability, calibration
  status, and session length;
- abstention rate and consequence-weighted error.

### 7.4 Promotion contract (not executed by P4)

Promotion is per predictive component, never for an action chooser (U-025).
A later explicit spec/review may let an immutable component version feed the
staged policy's inputs only if it:

1. beats the incumbent estimate (FSRS projection, heuristic duration, current
   expected-success rule) on prequential held-out scoring — log-loss/Brier at
   predeclared horizons with a predeclared margin and uncertainty bound;
2. remains better under temporal, family, and hard-surface holdouts;
3. passes planted-learner/sensitivity/adversarial tests;
4. has interpretable abstention and rollback behavior;
5. is activated by a reviewed event for a declared scope;
6. feeds only declared staged-policy inputs and is technically unable to
   reorder actions directly or alter learner depth policy/envelopes,
   target/card lineage, or successor semantics.

There is no promotion path for the composed action chooser: "beats the staged
policy on held-out delayed unseen outcomes" is unsatisfiable at n=1
(deterministic incumbent → degenerate propensities → near-empty off-policy
support), and any future revival requires a new reviewed spec with a causal
design (§9.3) or pooled opt-in data. No sample count or shadow agreement rate
automatically promotes anything. P4 ships the evidence machinery and keeps
everything shadow.

---

## 8. Global familiarity kernel

### 8.1 Authority split

P1 remains authoritative for:

- exact exposure events;
- namespaced hard-correlation groups;
- hard unseen/independence disqualification;
- deterministic conservative launch discount.

P4 adds a versioned soft-kinship model. It can estimate familiarity/replay risk
among surfaces that do not hard-collide. It can never override a hard collision
or invent missing exposure.

### 8.2 Model artifact

The P4 kernel is a **heuristic LLM-judged kinship feature**, not a fitted
model (U-026): an LLM scores soft kinship between non-hard-colliding surfaces
within card-declared bounds, the scores are cached as versioned features, and
admission is gated by planted-learner simulation (repeat-vs-fresh scenarios
must show the feature moves familiarity discounts in the right direction
without flipping scheduling or certification decisions). Learned weight
training is deferred — delayed fresh-sibling pairs at one learner's volume
are too sparse to fit against (the same n=1 economics as §7.4).

Create immutable `familiarity_kernel_models` with:

- model/version/parent/content hash and activation status;
- exact P1 feature schema and preprocessing/embedding versions;
- training/evaluation manifests split by time/card/family/hard group;
- learner-local scope and privacy/consent metadata;
- predicted outputs and calibrated intervals;
- evaluation metrics, sample/effective-sample counts, and calibration status;
- shadow/activation/retirement events.

Outputs are:

```text
P(script_or_answer_replay materially aided response)
independent-evidence discount interval
rotation-benefit estimate
```

They are conditioned only on information available before administration:
exposure history, time, kinship features, angle/task features, and surface
provenance. The learner's correctness on the current response is not an input.

### 8.3 Training/evaluation labels (deferred learned path)

If learned weights are eventually revived, use paired/triangulated evidence
such as:

- familiar-surface performance followed by delayed fresh sibling performance;
- exact/near vs orthogonal surface differences under comparable card state;
- “cue gave it away” validity signals;
- controlled rotation/dispersion assignments;
- repeat-vs-fresh planted-learner simulations for mechanism validation.

Correct for selection propensity where support exists. Do not label every
correct repeat “memorized” or every fresh miss “not familiar.” Separate
surface difficulty/card readiness residuals and report uncertainty. Until
revival, this taxonomy defines the *evaluation* labels for the heuristic
feature's sim gate and shadow audits, not a training corpus.

### 8.4 Launch authority

The heuristic LLM-judged feature runs shadow after passing its sim admission
gate; there is no fitted kernel in P4. P1 conservative discount remains live.
An explicit activation may later grant bounded soft-discount/rotation authority
only for a reviewed scope with held-out paired evidence. Simulation can promote
status only to `simulation_validated`; it cannot narrow live authority by
itself. Unknown/out-of-scope features fall back to P1, never zero familiarity.

---

## 9. Dispersion and interleaving

### 9.1 Same-facet dispersion

Define a versioned dispersion policy over target facet × capability, card
lineage, hard group, and high soft kinship. It considers:

- elapsed time;
- number and diversity of intervening administrations;
- current attention block/stage;
- working-memory/feedback exposure;
- lapse-retry linkage;
- assessment/diagnostic purpose.

Launch behavior:

- two fresh-evidence administrations on the same facet/capability/near-kin
  cannot be back-to-back;
- a same-session lapse retry may occur inside its linked episode but grants no
  new independent evidence and does not satisfy dispersion;
- acquisition/example completion may stay blocked/coherent by design, with
  scaffolded semantics recorded;
- diagnostic precommitted blocks may include related instruments only when
  their card independence/episode policy permits it;
- if no candidate satisfies spacing, wait, switch commitment/angle, offer
  source work, or stop—never trade the constraint against priority.

Exact gap/window parameters launch as registered heuristics and are experiment
variants, not literals in queue code.

### 9.2 Stage-aware interleaving

- initial worked-example acquisition: blocked/coherent within one target
  neighborhood;
- faded completion/repair: begin mixing only after the relevant component is
  stable enough to avoid overload;
- discrimination/method selection/transfer: interleave confusable/related task
  families so selection cues must be read rather than inferred from block;
- maintenance: mix commitments subject to attention-block coherence and due
  pressure;
- terminal assessment: follow the frozen target distribution, not a pedagogic
  interleaving heuristic.

Interleaving does not mean random topic switching. The block planner chooses a
coherent neighborhood; the within-block policy varies tasks at the stage where
discrimination/transfer is the objective.

### 9.3 One randomization layer

All policy experimentation runs through a single randomization layer (U-024):
micro-randomized decisions among *reversible, near-equivalent* candidates
already feasible — including ε tie-breaking when top candidates fall within a
declared margin — with assignment and true propensity persisted before
selection. There is no separate crossover machinery.

Proximal outcomes are defined at the **next spaced cold review** of the
affected cards, never end-of-session: desirable difficulties invert
end-of-session rankings for exactly the interventions worth testing
(interleaving-class effects look worse immediately and better delayed).
Burden is a co-primary outcome; immediate accuracy is secondary telemetry.

For durable interventions whose effects are themselves persistent state
changes (no meaningful washout), prefer **commitment-level parallel
randomization**: at n=1 the experimental unit is the commitment, not time —
matched commitments/neighborhoods are assigned to variants, with
contamination through shared facets bounded by the strongly-shrunk
correlation model. Interventions that fit neither design — not reversible, no
credible commitment-level unit, no explicit carryover model — remain
hypothesis-grade regardless of how much data accumulates.

Experiments begin shadow/simulation, then learner-local bounded live comparison
only through explicit consent/config and review. Underpowered results remain
uncertain; no global causal claim is made from one learner.

---

## 10. Open-world HypothesisCards

`HypothesisCard` is a versioned learner-model explanation. It is **not** a P1
ActivityCard. A diagnostic ActivityCard may test distinctions among
HypothesisCards.

### 10.1 Storage

Create the umbrella-required records:

- `hypothesis_cards` — stable identity and scope;
- immutable `hypothesis_card_versions`;
- `hypothesis_set_members` — normalized membership/prior for one immutable set;
- `hypothesis_set_lineage` — predecessor/successor and transition reason;
- `hypothesis_authoring_runs` — retrieve/generate context, versions, cost;
- `hypothesis_discovery_evidence` — typed candidate-ranking evidence;
- `hypothesis_validation_results` — gate/confirmation outcomes;
- `open_set_transitions` — typed trigger → expansion → successor trace;
- append-only status/version/retirement events and rebuildable heads.

Keep existing `hypothesis_sets` rows immutable. Backfilled membership rows point
to their labels through legacy-adapter HypothesisCard versions; original JSON
and priors remain replay authority for historical algorithms.

### 10.2 Card contract

A HypothesisCard version contains:

- scope: `lo_local` or `facet` and exact ids;
- learner-facing neutral statement and internal mechanism description;
- predicted coarse error signature/outcomes under declared task features;
- distinctions from nearest active alternatives;
- downstream intervention mapping/action relevance;
- source: expert/domain template, learner seed, residual finding, model
  generation, grader-disagreement review, or legacy label;
- evidence/provenance refs and bounded-trust prior;
- compatible diagnostic pattern/card requirements;
- status `provisional`, `active`, or `retired` via events;
- author/model/schema/policy versions and content hash.

Descriptions are relational and contextual (“this rule may be applied without
checking equivalence”) rather than trait labels (“learner lacks…”).

### 10.3 Expansion triggers

Append a typed trigger when one or more hold:

1. open-set posterior mass crosses a validated threshold;
2. low posterior-predictive probability/repeated negative surprise;
3. the same unexplained signature occurs on independent surface groups;
4. `N` repair failures occur on varied surfaces regardless of attributed cause;
5. learner proposes an explanation in Journey 8 or a P3 annotation;
6. new reviewed semantic/source information changes plausible mechanisms;
7. systematic P0 grader disagreement/confidence mismatch suggests the outcome
   space or rubric is misspecified;
8. reviewed residual/identifiability analysis recommends model expansion.

Triggers dedupe by scope + evidence window + trigger type. A trigger is not a
candidate/card and does not change the current posterior.

### 10.4 Retrieve → generate → validate

**Retrieve**

- query active/provisional cards at the two allowed scopes;
- retrieve authored domain templates, confusables, source objects, learner
  seeds, prior retired alternatives, and reviewed residual findings;
- preserve provenance/trust and avoid duplicating semantically equivalent
  cards.

**Generate**

- generate a small bounded candidate set against the frozen current set and
  observed unexplained signatures;
- require predicted differentiating outcomes and a distinct downstream action;
- never include cold held-out answer content in authoring context;
- persist all candidates/rejections and exact model/prompt/schema context.

**Validate**, in this order:

1. **action relevance:** candidate can change a feasible intervention or is
   explicitly required for named contestability;
2. **identifiability:** admitted diagnostic cards can distinguish it from
   current alternatives under P0 coarse outcomes and grader/likelihood
   uncertainty;
3. **novelty/falsifiability:** not a paraphrase, predicts an observable
   difference, and states what would count against it;
4. semantic/source/provenance and learner-facing language review;
5. P1 diagnostic-card gate and ±0.15 likelihood-perturbation sensitivity.

Failure at a higher gate stops lower-cost authoring. A fascinating but
action-equivalent distinction stays a note/provisional explanation, not a
reason to spend more probes.

### 10.5 Discovery mass

Discovery evidence can rank candidates and conservatively redistribute only
`other_or_unknown` mass. It may not steal probability from named hypotheses or
create active status.

For a versioned tempering factor `tau_discovery`:

```text
candidate_mass_total <= tau_discovery * prior_other_mass
remaining_other = prior_other_mass - candidate_mass_total
```

Allocation among candidates is normalized from discovery scores with wide
intervals. `tau_discovery` is a heuristic decision parameter. Learner-supplied
seeds receive bounded trust and the same prospective validation requirement.

### 10.6 Prospective confirmation and status

A provisional card becomes `active` only after at least:

- two qualifying confirmations;
- across two independent P1 hard surface groups;
- in measurement segments not contaminated by instruction/source reveal;
- with P0 reliability-weighted evidence and no unresolved quarantine;
- while distinguishing the card from its declared alternatives.

Two grades of one response, two near-clone surfaces, a discovery observation,
or a same-session retry do not satisfy this rule. Two confirmations across two
independent hard surface groups are the P4 structural minimum. A versioned
policy may demand stricter evidence mass or more groups, but cannot weaken the
2/2 floor within this spec.

Contradictory evidence may keep the card provisional or retire it through an
append-only event. Retirement removes it from future set heads but never
rewrites episodes that pinned it.

### 10.7 Immutable successor sets and episode boundaries

An open episode keeps its exact set/prior/likelihood/policy pins. When expansion
is needed:

1. append `OpenSetTransition` and complete/stop the segment with
   `model_expansion_needed` (or preserve its existing terminal reason plus
   transition link);
2. author/validate provisional cards off the frozen evidence;
3. create an immutable successor set with normalized membership and lineage;
4. open a successor episode/segment that pins the new set;
5. use only new committed diagnostic administrations to confirm it.

Journey 8's immediate exception may author one provisional diagnostic
ActivityCard and successor set promptly, with tempered evidence and visible
status. It still opens a successor episode; it never mutates the contested
episode.

### 10.8 Bounded episode and learning separation

Stop a diagnostic segment when:

- one hypothesis robustly dominates for an action;
- all plausible hypotheses imply the same intervention;
- no feasible probe has positive robust net value;
- fatigue/burden/cap is reached;
- stronger instrument/model expansion is needed;
- learner stops/opens source;
- grade/surface validity requires review.

Starting instruction closes the segment. Its posterior describes the
pre-instruction state and remains inspectable. Later cold work tests a new
state; it does not “continue” the old posterior.

---

## 11. Journey 8: inspect and contest

The “Why this diagnosis?” view shows:

- exact target/task context and pre-instruction segment;
- best-supported HypothesisCard plus named alternatives/open-set mass;
- calibration status, interval, grader review/quarantine, and claim language;
- which observations/surface groups contributed and their effective weights;
- why each instrument was selected and why the episode stopped;
- mapped intervention and which distinctions would not change it;
- source/learner/AI/expert provenance for every hypothesis statement.

The learner may choose “propose another explanation,” preserving their words
as P3 annotation/hypothesis seed. The system:

1. stores the seed locally first;
2. checks for an existing equivalent card;
3. runs action-relevance/identifiability/novelty gates;
4. explains rejection/merge/provisional status;
5. if admissible and within burden, opens a successor set/episode and serves a
   discriminating fresh probe;
6. presents the revised best-supported alternatives without claiming the
   learner was wrong to contest.

The eigenvector acceptance fixture is “uses a rule without checking the
equivalence model”: distinguish rote equation manipulation, schema
interpretation, method selection, and a learner-proposed alternative using
coarse outcomes and two independent surface groups.

---

## 12. Re-entry and short-session adapters

### 12.1 Hiatus re-entry

After a configured hiatus, create an optional measure-mode attention block:

- no red backlog/streak language;
- pin the current confirmed target contract for the episode;
- sample high-value previously demonstrated, historically fragile, and target-
  frontier cells using goal-conditioned predictive EIG;
- keep a small visible cap and robust stop rule;
- report `retained`, `recoverable`, and `needs_attention` with intervals and
  context, not deficit labels;
- propose a seven-day plan bounded by commitment dispositions and retire/defer
  low-value activities through P0/P1 flows.

Current `reentry_summary` remains a non-diagnostic welcome-back view. It may
seed candidates but cannot substitute for the cold episode.

### 12.2 Three-minute session

Use the same block planner with `available_minutes=3`. Prefer admitted short
P1 patterns (`setup_only`, `example_completion`, `example_comparison`) whose
conservative duration fits. One completed activity completes the session. If
no meaningful candidate fits, return `stop:no_feasible_activity`; do not fill
time with low-value leftovers.

The deferred journeys home screen is not required; existing Today/continue
entry points may expose these adapters.

---

## 13. Service and read interfaces

Required service boundaries:

- build/hash a ControllerSnapshot and enumerate candidate attention blocks;
- apply constraint engine and return typed exclusion trace;
- choose/commit live staged block/action/activity idempotently;
- evaluate, suggest, or commit one P1 depth edge and request the P0 authorized
  target successor/fresh reserve when terminal support changes;
- compute/log shadow action rankings without an authority callback;
- attach delayed outcome windows and run offline comparison reports;
- compute action loss, robust EVSI, hypothesis EIG, and goal-conditioned
  predictive EIG with exact model/target pins;
- score/evaluate/activate/retire a soft familiarity-kernel feature version
  under the authority contract (no fitting in P4, U-026);
- assign/project dispersion/interleaving policy/experiment variants;
- append/dedupe expansion trigger and run retrieve/generate/validate;
- create/version/retire HypothesisCards and immutable successor sets;
- open successor episode, apply tempered discovery prior, and project
  confirmation status;
- build “Why this diagnosis?” and learner-contest receipts;
- start re-entry/three-minute blocks.

Minimum CLI/debug parity:

- explain live controller snapshot/decision and every exclusion;
- compare live and shadow plans for one historical decision;
- recompute robust EVSI across stored credible matrices;
- audit predictive target-set construction against goal contract;
- inspect global hard/soft familiarity and kernel shadow output;
- simulate dispersion/interleaving variants;
- list expansion triggers/authoring runs/cards/set lineage/validation;
- replay a contested episode and successor;
- run planted-learner and policy-evaluation reports.

No debug command mutates live authority unless it calls an explicit reviewed
activation/version service.

---

## 14. Migration, rollout, and failure behavior

### 14.1 Dependency gate

Open-world expansion remains disabled until:

1. P0 calibrated-event/reliability and robust-bound APIs pass;
2. P1 global exposure/hard groups/card lineage/purpose adapters pass;
3. P2 end-to-end held-out journey passes;
4. P3 local hypothesis-seed/provenance path passes;
5. controller constraint/staged policy, target-distribution EIG, and shadow
   logging pass;
6. dispersion/interleaving and kernel shadow audits pass.

The schema may land earlier, but no expansion worker or successor-set UI is
enabled before this gate.

### 14.2 Controller cutover

1. run the new constraint/staged controller fully shadow beside the existing
   scheduler and compare feasible-set membership;
2. fix every unexplained constraint disagreement;
3. make staged policy live for P2 runs while old scheduler still composes
   unrelated Today work;
4. expand live staged block selection across commitments behind a rollbackable
   policy version;
5. keep old weighted queue output as comparator, not fallback authority inside
   a partially committed decision;
6. only then collect/evaluate the new scored shadow selector.

Rollback applies to the next uncommitted decision and preserves all event
history. An in-flight administration/block completes under its pinned policy.

### 14.3 Hypothesis migration

- retain every existing `hypothesis_sets` JSON row unchanged;
- create normalized membership and legacy-card adapter rows deterministically;
- preserve label, prior, algorithm version, phase/episode linkage, and creation
  order;
- map current `other_or_unknown` generation needs into `OpenSetTransition`
  trigger records without pretending expansion already occurred;
- import authored misconception/confusable templates as authored cards with
  reviewed/provisional status matching their real gate history;
- never promote a current learner-state belief into an active HypothesisCard
  merely because its posterior is high.

### 14.4 Failure behavior

- controller snapshot incomplete -> use only decisions robust under missing
  data or stop; never fill missing freshness/readiness with confidence;
- no feasible candidate -> typed stop, not lowest-score rule bypass;
- decision commit conflict -> return standing committed decision;
- shadow scorer/kernel fails -> live behavior unchanged;
- EVSI model/target missing -> use admitted deterministic stage action or stop,
  disclose no robust value;
- likelihood/action winner flips -> abstain/stronger instrument/common action;
- target contract changed -> new episode uses head; pinned episode/reserve
  remains unchanged and labeled;
- depth policy/envelope changed or edge became stale -> invalidate the
  uncommitted progression candidate and replan; preserve reached milestones;
- inside-envelope edge lacks an admitted successor or fresh reserve -> maintain/
  suggest/stop, never hot-path author or reuse predecessor scheduling/proof;
- expansion trigger without admissible candidate -> retain alarm/trigger and
  choose safe action; do not diagnose `other`;
- authoring/model outage -> current set remains immutable; resume run once;
- candidate fails action relevance/identifiability -> preserve rejection
  receipt, spend no confirmation probes;
- learner seed conflicts with source/system -> preserve it as learner-authored
  alternative; do not overwrite or auto-activate;
- grade quarantine/disagreement -> withhold consequential confirmation and
  route P0 review;
- experiment support/censoring failure -> report inconclusive; no promotion.

---

## 15. Implementation order

1. Add controller snapshot/decision/candidate/block events and typed constraint
   engine in full shadow.
2. Implement the canonical staged policy, depth-envelope constraints/one-edge
   transition, and failure-triage integration; cut P2 then global live block
   selection over behind policy versions.
3. Replace ID-ordered predictive targets with exact goal-contract target
   snapshots and add robust EVSI/net-value stopping.
4. Add same-facet dispersion and stage-aware interleaving policies plus safe
   experiment logging.
5. Add the heuristic LLM-judged kinship feature, its sim admission gate, and
   shadow audits; keep P1 hard/conservative policy live (learned kernel
   training deferred, U-026).
6. Add shadow predictive components (retrievability, expected success,
   duration), outcome windows, and prequential held-out reports;
   composed-selector telemetry is secondary and time-boxed — there is no
   monolithic promotion path (U-025).
7. Pass all controller, leakage, replay, planted-learner, and P2/P3 regression
   gates.
8. Add HypothesisCard/version/set-lineage/discovery/validation schema and
   legacy adapters, still disabled.
9. Implement typed triggers and retrieve→generate→validate with no live set
   mutation.
10. Enable successor episodes, confirmation/retirement, and Journey-8 UI only
    after the dependency gate in §14.1.
11. Add re-entry/three-minute adapters and final scale/operability suites.

Open-world expansion is intentionally last. More hypotheses amplify every
measurement, exposure, and controller error below them.

---

## 16. Test and acceptance contract

### 16.1 Controller and constraints

- each canonical planted state selects the expected action/subtype;
- every live decision points to one staged rule and complete exclusion trace;
- a high shadow/live score cannot admit a held-out collision, wrong purpose,
  intent violation, fatigue overflow, or dispersion violation;
- explicit learner choice is honored when feasible and explained when not;
- `auto_within_envelope` selects one reviewed evidence-gated
  `practice(depth_progression)` edge and replans; `hold_at_target` and
  `suggest_next` cannot auto-activate it;
- with the auto-depth package (U-018) enabled, repeated negative affect on a
  commitment's families downgrades `auto_within_envelope` to `suggest_next`
  before the next edge commits, and the downgrade is a versioned policy event
  pending re-confirmation (U-011);
- outside/stale envelope, unreviewed/multi-edge, over-budget, missing-successor,
  and missing-fresh-proof candidates are excluded before scoring;
- activating a material edge preserves predecessor attainment and forks card
  state with no FSRS/certification inheritance;
- context-switching is handled at block level;
- one three-minute activity completes a session;
- corrupt projection caches rebuild to the same decision from events;
- retry after every commit boundary yields one block/decision/administration.

### 16.2 Shadow firewall

Inject arbitrary/failing/extreme shadow scorer and kernel outputs. Assert zero
change to live order/action, stop, administration, exposure, posterior,
evidence, schedule, certification, and learner-facing claim. Shadow records
must still join to the exact predecision snapshot/outcomes or be marked
unusable.

### 16.3 Robust EVSI/EIG

- EVSI is zero when all hypotheses share one optimal action;
- an informative question separating different repairs has positive EVSI;
- adding burden can make net value non-positive without making EIG negative;
- ranking uses per-time value while stop uses absolute net value;
- grader-channel asymmetry changes emission integration correctly;
- no `P(Z|E)` likelihood feedback/double-count occurs;
- ±0.15/credible perturbation winner flip causes abstention/stronger-card
  route;
- hypothesis EIG is used for named contestability and predictive EIG for a
  frozen target distribution;
- predictive target construction is invariant to candidate/item insertion/ID
  order and changes only with its pinned contract/support;
- candidate cannot predict itself as a held-out target;
- loss-table entries carry an expected-minutes derivation from route/duration
  data; a free-constant entry without a derivation fails registration
  (U-023);
- interval-width viability: with `heuristic`-width grader and likelihood
  channels, measure how often robust EVSI is unusable (the stop rule fires
  immediately or the winner flips); the resulting measure-mode abstention
  rate must stay inside the registered P0 abstention budget (U-021), and a
  breach raises the budget alarm rather than silently widening tolerances.

### 16.4 Familiarity/dispersion/interleaving

- every purpose/LO exposure contributes to global features;
- kernel cannot override an exact/hard collision;
- missing/out-of-scope kernel falls back to conservative P1 policy;
- current correctness is unavailable as a predecision feature;
- same-facet near-kin fresh-evidence activities are not back-to-back;
- linked retry exception earns no independent evidence;
- acquisition remains coherently blocked while transfer/discrimination is
  interleaved;
- assessment follows frozen distribution rather than pedagogic mixing;
- experiments assign/log only among feasible candidates and report
  underpowered/support failures as inconclusive.

### 16.5 Expansion triggers and immutability

For each trigger type in §10.3, assert one deduplicated transition and no
posterior/set mutation. Assert non-trigger for one ordinary wrong answer or one
reading confusion mark alone. Existing episode replay remains byte-identical
after new cards/sets are authored.

### 16.6 Candidate validation

- action-equivalent candidate fails/parks before expensive probes unless named
  contestability is explicitly required;
- indistinguishable candidate fails identifiability under coarse outcomes;
- paraphrase/non-falsifiable candidate fails novelty/falsifiability;
- sensitivity winner flip fails admission;
- learner seed remains verbatim/provenance-labeled and bounded-trust;
- source/AI/expert authorship never changes silently;
- no held-out answer leaks into authoring context.

### 16.7 Discovery and confirmation

- discovery moves only bounded `other` mass and named priors remain unchanged;
- discovery alone never activates a card;
- two observations in one hard/near group do not confirm;
- two independent reliability-eligible prospective confirmations can activate;
- regrades/same-session retries do not fake independent confirmation;
- contradictory/quarantined evidence blocks or retires via append-only event;
- retired card remains in historical episode snapshots;
- instruction closes segment and later cold work opens a new one.

### 16.8 Journey 8 disagreement

1. produce a provisional best-supported eigenvector diagnosis with visible
   alternatives/calibration;
2. open “Why this diagnosis?” and trace cards, observations, surfaces, grades,
   selection, and stopping;
3. learner proposes “I may be applying the rule without checking equivalence”;
4. seed persists locally and is either matched or passes gates as provisional;
5. current set remains immutable;
6. successor set/episode serves a fresh discriminating instrument;
7. revised view reports the new best-supported alternatives and intervention;
8. two independent confirmations are required before active status;
9. no screen presents `other_or_unknown` or a heuristic hypothesis as fact.

Repeat with planted misgrade and likelihood perturbation. A grader error must
route review/uncertainty rather than silently activate the new hypothesis.

### 16.9 Re-entry and short session

- re-entry pins target distribution, caps questions, and reports retained/
  recoverable/needs-attention without backlog shame;
- the welcome-back FSRS summary alone makes no diagnostic claim;
- three-minute block chooses structurally meaningful work that fits a
  conservative duration bound or stops honestly;
- both adapters may continue or activate a reviewed edge already authorized by
  `auto_within_envelope`; neither can widen the envelope or cross the goal/task
  family, and a short session stops if the transition cannot fit safely.

### 16.10 Performance and replay

- one controller snapshot enumerates candidates through bounded bulk reads;
- 100k exposure and controller events remain queryable through indexed
  learner/time/surface/commitment paths;
- live selection opens no model call when admitted candidates/snapshots exist;
- kernel/scorer/expansion workers may be down without losing attempt
  submission, event replay, or current staged policy;
- all projections rebuild deterministically with version manifests;
- migrations and legacy-set normalization are idempotent;
- P0–P3 acceptance suites remain green.

---

## 17. Launch defaults and explicit assumptions

- The staged controller is live; the scored selector is shadow for all P4.
- The fitted soft-familiarity kernel begins shadow; P1 hard collisions and
  conservative heuristic remain live. Any later bounded activation is an
  explicit reviewed event outside automatic P4 rollout.
- Five-to-fifteen-minute blocks, dispersion gaps, interleaving stage gates,
  EVSI costs, discovery tempering, trigger thresholds, and any confirmation
  requirements stricter than the structural 2/2 floor are decision parameters
  with explicit calibration status.
- Structural rules—immutable set snapshots, purpose separation, hard exposure,
  independent confirmation groups, local-first learner seeds, and shadow zero
  authority—are not tunable reward terms.
- Goal weights come only from the evaluated P0 contract/commitment; the “why”
  is never rendered as a cold cue.
- P2's first cut issues `suggest_next` invitations only;
  `auto_within_envelope` authority arrives with the auto-depth package
  (U-018), together with the affect auto-downgrade it enforces (U-011). When
  commitments carry that policy, P4 treats it as a hard versioned
  feasible-set boundary, not a reward feature. It commits at most one edge
  per decision and replans before any later transition.
- P4 remains single-learner and does not claim population psychometrics or
  causal generality.
- Open-world expansion may produce “no admissible explanation/instrument yet.”
  That is a valid honest result, not a reason to invent finer outcomes or keep
  probing indefinitely.

---

## 18. Change log

### 2026-07-21 — P4 audit fix wave (dual-authority sweep, dead abstention, accuracy amendments)

The consolidated P4 adversarial-audit fixes. Highlights and the spec-accuracy amendments
they imply:

- **Dual-authority ownership exclusion (§14.2 step 3) now covers EVERY administration
  surface.** The staged-owned exclusion, previously wired only into the legacy queue, is a
  shared helper (`controller_ownership.staged_owned_refs` /
  `staged_owned_practice_item_ids` / `is_learning_object_staged_owned`) consulted by the
  sidecar probe path (`probe_episodes.eligible_instruments` drops owned items and refuses a
  wholly staged-owned LO) and the held-out exam (`exam_pool._candidates` excludes owned
  items; `reserve_exam_pool` / `assign_p2_run` assert exam-reservation ⟂ staged-ownership).
- **Action-flip abstention (§6.5) is live.** EVSI flip detection now keys off
  member-dependent decision quantities (per-emission `argmin_by_emission` across ensemble
  members, and stressed-vs-nominal argmin under the ±0.15 perturbation), not the prior-only
  `current_action`. The stop rule carries each candidate's own burden (§6.4).
- **Prequential splits (§7.3):** the report splits by TIME and TARGET FAMILY. The
  surface-group split named earlier is DEFERRED — the outcome window carries no
  surface-group key, and the report does not synthesize one from absent state.
- **Composed-selector telemetry retirement (§7.4 time-box)** is wired into the runtime
  maintenance path (`state_sync`), so an expired horizon actually retires.
- **Affect/failure-triage signals on the ControllerSnapshot (§3.1) are DEFERRED (U-011):**
  the `affect_by_commitment` slot is not loaded and is not part of the snapshot hash body.
- **Same-facet dispersion (§9.1)** disperses on near-kin surface (fingerprint) in
  production; the finer facet/capability/lineage/hard-group dimensions await a facet-join
  that populates them on the snapshot (named TODO in `services/dispersion.py`).

### 2026-07-21 — §15 step 11: re-entry / short-session adapters landed; §16 sweep complete

Landed the final unimplemented step of the P4 order — the §12 re-entry and short-session
block-planner adapters and the closing scale/operability coverage. Both formerly-DEFERRED
§16 acceptance rows are now green. The §16 acceptance sweep is complete.

- **Short-session adapter (§12.2) — `services/short_session.py`.** The SAME staged block
  planner (`staged_policy.decide`) run with a small `available_minutes` (down to ~3). When
  the available minutes fall below the 5-minute attention-block lower bound the block is
  planned to COMPLETE within them: `staged_policy.is_short_session` +
  `_as_short_block` set the budget to the available minutes (a documented exception that
  COMPOSES the registered 5–15 min bounds, never clamped UP to 5) and a single completing
  exit rule `session_complete_on_one_activity`. The constraint engine's fatigue/budget gate
  keeps only candidates whose conservative duration fits (real durations, the minutes
  machinery); the within-block selector prefers the admitted short P1 patterns
  (`setup_only`/`example_completion`/`example_comparison`). One completed activity completes
  the session; nothing meaningful that fits ⇒ `stop:no_feasible_activity` (never filled with
  leftovers). A reviewed `auto_within_envelope` edge activates ONLY when the transition fits
  safely — the depth-edge fit guard in `decide` stops honestly otherwise (§16.9 bullet 4).
- **Re-entry adapter (§12.1) — `services/reentry_adapter.py`.** Returning after a hiatus is
  NOT a diagnosis. The adapter (1) opens the existing non-diagnostic `reentry_summary`
  welcome-back FSRS diff first (`welcome_back_is_diagnostic = False`; it may seed candidates
  but makes no claim); (2) pins the confirmed goal-contract target distribution for the
  episode — the frozen `predictive_targets.TargetSet` (never an ID-ordered slice, §6.6);
  (3) classifies decayed state into `retained` / `recoverable` / `needs_attention` with
  Ready intervals and context, never deficit labels and never backlog/streak language —
  still-solid and held-flat cells are TRUSTED (not re-checked), the fragile / target-frontier
  cells are the re-check candidates; (4) samples those cells under a small visible cap
  (`REENTRY_QUESTION_CAP`) and runs an optional measure-mode attention block on the normal
  decision trace with the staged policy's robust stop rule. Neither adapter widens the
  envelope or crosses the goal/task family — inherited from the staged feasible-set
  constraints, not re-implemented.
- **Formerly-DEFERRED §16 rows → green.** §16.1 "one three-minute activity completes a
  session" and the §16.9 re-entry/short-session items are covered by
  `tests/test_reentry_short_session.py` (`test_three_minute_activity_completes_a_session`,
  `test_short_session_stops_honestly_when_nothing_fits`,
  `test_short_session_prefers_admitted_short_p1_patterns`,
  `test_short_session_depth_edge_stops_if_it_cannot_fit`,
  `test_reentry_pins_target_caps_and_reports_without_backlog`,
  `test_reentry_welcome_back_makes_no_diagnostic_claim`,
  `test_reentry_classifies_retained_recoverable_needs_attention`,
  `test_short_session_retry_after_commit_is_idempotent` for the §16.10 retry-idempotency
  scale check on the new path).
- **Params registered at birth.** `staged_policy:SHORT_SESSION_MAX_MINUTES`,
  `reentry_adapter:REENTRY_QUESTION_CAP`, `reentry_adapter:REENTRY_RECOVERABLE_BAND`
  (heuristic decision parameters; each an active pool/reporting bound that never orders —
  the within-block robust-EVSI selector orders and the robust stop rule stops).
  `SHORT_SESSION_PREFERRED_PATTERNS` is structural P1 vocabulary, not a tunable.

### 2026-07-21 — descoped steps 5–6 + the open-world §14.1 dependency gate landed

Landed the final P4 substrates as descoped, firewall-gated shadow features, plus the
open-world dependency gate as an executable check (open-world itself remains deferred,
strictly last per §10/§15). Migration `100_kinship_kernel_and_shadow_components.sql`.

- **Step 5 — heuristic LLM-judged soft-kinship FEATURE (U-026, descoped).** No fitted
  kernel, no learned weights (deferred at n=1). `services/kinship_feature.py` composes
  P1's `familiarity` soft-kinship feature vectors; an LLM judge (deterministic stub for
  tests) renders a U-034-shaped artifact within owner-reviewed bounds, producing
  `P(replay materially aided response)`, an independent-evidence discount interval, and a
  rotation-benefit estimate — conditioned ONLY on pre-administration information (current
  correctness is never an input, §8.2/16.4). Scores cache as versioned features in
  `familiarity_kernel_features`; the model artifact is `familiarity_kernel_models` (§8.2).
  **Firewall (enforced + tested):** the feature is computed + logged but consulted by
  NOTHING. `consulted_discount` returns P1's conservative discount unchanged throughout
  P4 — passing the sim admission gate reaches only `simulation_validated` (still shadow,
  §8.4); live soft-discount authority is a separate explicit reviewed activation held
  OUTSIDE automatic P4 rollout (`LIVE_ACTIVATION_ENABLED = False`, mirroring the U-018
  dead-man switch). Admission = a repeat-vs-fresh planted-learner sim
  (`sim/kinship_admission.py`) demonstrating the feature moves the discount correctly
  without flipping a scheduling/certification decision; the P0.5 sweep machinery produces
  the certificate and `run_admission_gate` emits the U-022 promotion-evidence artifact
  through the existing registry machinery (`sensitivity_certificates.promote`).
- **Step 6 — shadow predictive components + prequential reports (U-025, descoped).**
  `services/shadow_components.py` + `services/prequential.py`: retrievability /
  expected-success / expected-duration are logged as ZERO-authority shadow predictions
  (`controller_shadow_predictions.authority CHECK IN ('none')`), scored PREQUENTIALLY
  (log-loss/Brier) against the delayed **next-spaced-cold-review** outcome
  (`controller_outcome_windows`), split by time/family/surface-group. Components are
  promotable INDIVIDUALLY (feeding staged-policy INPUTS only) and promotion emits a
  U-022 promotion-evidence artifact; the composed-selector telemetry is SECONDARY and
  TIME-BOXED (`composed_selector_telemetry_horizons`, registered horizon → retirement);
  the monolithic action chooser has NO reachable promotion path at n=1 —
  `promote_action_chooser` is a structural guard that always refuses (§7.4).
- **Open-world §14.1 dependency GATE — gate only.** `services/open_world_gate.py`
  implements the six conditions as executable, queryable predicates over the landed
  state and reports each truthfully; `learnloop controller open-world-gate` runs the
  check (exit non-zero while NOT MET). Open-world expansion itself (HypothesisCard
  schema, triggers, retrieve/generate/validate, successor episodes, Journey 8) is **NOT
  implemented** — strictly last, behind the gate (§10, §15 steps 8–10). Current
  evaluation: **NOT MET.** Conditions 1–5 (the landed P0–P4 substrates) evaluate MET;
  condition 6's kernel-shadow audit is NOT MET because the descoped soft-kinship feature
  is deliberately kept behind its admission gate (firewall — un-admitted on the landed
  vault), and the open-world substrate schema is absent. Enabling any expansion worker
  or successor-set UI stays blocked until every condition passes.
- **Deferred (unchanged):** open-world HypothesisCard expansion (§10, §15 steps 8–10),
  the §12 re-entry / three-minute adapters + final scale suites (§15 step 11), U-018
  auto-activation (OFF), and the learned soft-kinship kernel (U-026 training path, n=1).

### 2026-07-21 — §14.2 dual-controller cutover (step-3 coexistence window) landed

Landed the P4 §14.2 step-3 coexistence window: the staged policy is LIVE for P2
golden-path commitments while the legacy scheduler composes all other Today work,
both sharing the ONE `activity_exposure_events` ledger.

- **Adopted (working default, pending owner confirmation) — the §A owner-memo
  arbitration** (design `p4_design.md` §A): (1) the ledger stays shared and
  unpartitioned (§A.1, invariant 11); (2) **commitment-scoped ownership** with a
  deterministic tie-break (§A.2) — a commitment (and its P2 run) is owned by exactly
  ONE controller; the staged policy owns P2 golden-path commitments (confirmed goal
  contract + depth policy + envelope), legacy owns everything else; (3) **serialized
  commit-time exposure reservation** through the P0 `open_administration_atomic`
  in-lock recheck (§A.3) — the loser DEFERS (waits/rotates/stops), never drops, and
  never trades the constraint against priority; (4) one randomization layer spans both
  (§A.4); (5) rollback applies to the next uncommitted decision, in-flight
  administrations complete under their pinned controller (§A.5). Owner confirmation is
  still open on: commitment- vs surface-scoped ownership; defer-vs-drop for the
  collision loser (adopted: DEFER); and whether legacy maintenance of a staged-owned
  commitment's decayed cards is legacy's or staged's job (adopted: staged owns all
  purposes for an owned commitment).
- **Ownership** — migration `099_controller_ownership.sql`: append-only
  `controller_ownership_events` (durable receipts) + a rebuildable `controller_ownership`
  head. Service `controller_ownership.py`: assign/resolve/transition, the P2-run
  assignment predicate, the legacy-scheduler exclusion resolver, and the single-switch
  rollback. The legacy scheduler (`scheduler.build_due_queue`) now EXCLUDES staged-owned
  commitments' items (a no-op on a pre-cutover vault); the staged policy REFUSES items it
  does not own in live mode.
- **Live wiring** — `state_signals.py` derives the staged policy's decision signals
  deterministically from real state (misspecification, robust value, target-acquired,
  retention-limit, terminal-reserve). `controller_cutover.py` provides the live P2
  next-action bridge (decision-equivalent to the pre-cutover static policy unless the
  trace names a constraint/EVSI reason), the six ordered step-3 gates as a hard
  sequential barrier, and the rollback switch. `staged_policy.decide` gained a `mode`
  ('shadow'|'live') and an ownership refusal.
- **Gate dispositions** (design §C, all green): (a) shadow parity baseline — PASS;
  (b) ownership assignment for P2 runs — PASS; (c) staged policy live for owned
  commitments, decision-equivalent — PASS; (d) cross-seam exposure integrity (exactly
  one wins, loser defers, no double exposure, reserves not poached) — PASS; (e) affect
  check + one-edge discipline under live mode (U-011 ordering, U-018 inert) — PASS;
  (f) rollback returns owned commitments to legacy atomically with a receipt — PASS.
- **Deferred (unchanged):** §14.2 step 4 (expand live staged block selection across
  commitments behind a rollbackable policy-version head) and step 6 (scored shadow
  selector) remain future work; U-018 auto-activation stays gated OFF.

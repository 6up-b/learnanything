# G2 design: the router decides whether to probe

The build sheet for refactor step G2 ("The router decides"). A read-only design pass by a Codex worker (gpt-6-astra) at main `0f309a8687` (after `mvp-0.61`), 2026-11-19, filed as written apart from path clean-up. It lists every site that today answers "should a probe be asked after this miss?", the shape after G2 (the probe as a candidate of the router's post-miss decision, priced in two stages over the locked hypotheses), what changes at the tag `mvp-0.62` and what a vault below it keeps, seven steps (three structural, one unserved evaluator, the comparison report, the behaviour landing alone, the record), the report the owner reads before it lands, the risks, and four owner decisions. Nothing was run to produce it; every line it cites is re-checked by the step that uses it.

---

Verified against `0f309a8687a66ab1f082eeb4c91f45de0a1b620a1b620a`? Correction: the checkout is **`0f309a8687a66ab1f082eeb4c91f45de0a1b620a`**. No files changed. No tests, vaults, databases, network requests, or model calls were run.

Below, **verified** describes this checkout; **proposed** describes the implementation; **inferred** identifies a dependency that needs a test or measurement.

## 1. TODAY, EXACTLY

The historical “six sites” is not a reliable count of current functions. Some were overlapping questions, some were callers, and G1 already removed FG1’s fake verdict. The current inventory is below.

“Held” means the miss’s answer, causes, and repair have not been released. A grade or criterion result can already be visible. “Router decision” means the post-miss action decision, not the causal gate’s receipt.

### Decision inventory

| Site, verified | Reads and decides | Timing | Record and learner visibility | Classification |
|---|---|---|---|---|
| **A. Lane existence:** `src/learnloop/followup_run/lanes.py:28`, `:59` | Counts distinct concrete rivals, excluding the open arm. At least two selects the probe lane; otherwise practice. | Before FG1’s router decision, while feedback is held. | Workflow progression records the resulting lane/state; the learner sees a question or released feedback, not the count test. Worker consumes the choice at `src/learnloop/followup_run/jobs.py:347`. | **Fact. Stays.** It establishes which lane exists, not whether probing pays. |
| **B. Causal repair gate:** `src/learnloop/diagnosis/causal_orchestrator.py:625`, `:923`; derived verdict at `src/learnloop/diagnosis/probe_facts.py:141` | Repair mapping, common cover, bundle separability, chance of changing repair, estimated burden/avoided teaching, preferences, machine checks, recent diagnostic count, optional session budget. Returns probe/skip/defer; determines whether to offer a probe or permit repair. Earlier class/mapping branches also decide at `causal_orchestrator.py:757`, `:777`, `:808`. | On a repair request or feedback status request; generally after feedback release. Also called by the post-diagnosis common-repair consultation, before the feedback surface consumes its result. It is **not** downstream of a shared post-miss router decision on the learner lane. | `causal_probe_decision_receipts`, including inputs, parameter manifests and provenance: `causal_orchestrator.py:677`, `:956`. Returned `RepairStatus` exposes decision/reason/offer: `:711`. | **Mixed.** Class/likelihood/burden facts and genuine constraints stay; worth verdicts move. |
| **C. Repair entry’s hold:** `src/learnloop/diagnosis/remediation.py:131`, `:152`, `:162` | Calls causal status; raises `RemediationBlocked` when no repair episode is allowed. | After the learner requests repair; no router draw currently adjudicates this hold. | Sidecar returns a normal result with `episode: null` and `repair_status`, rather than an error: `src/learnloop_sidecar/handlers/remediation.py:114`. Learner sees the hold and available actions. | **Consumer of B**, not an independent valuation formula. Its worth-based veto goes; ambiguity becomes candidate context. |
| **D. FG1 hard refusals:** `src/learnloop/followup_run/router.py:95` | Preference, pending factor/LO machine checks, foreign episode with observations. | Before the draw; checked again on retries and after authoring: `router.py:246`, `jobs.py:437`. Feedback is ordinarily still held. | Refusal enters the follow-up decision/workflow and `followup_gate` record: `router.py:320`, `:368`. Learner sees release/fallback, not necessarily every internal reason. | **Hard stops. Stay.** |
| **E. FG1 observation-only class verdict:** `src/learnloop/followup_run/router.py:127` | Repair-class need. Logs `skip_common_repair`/class-equivalence only when classes settle it; otherwise `decide_probe_absent: no_instrument_before_authoring`. | Before the router draw, held. | `observational` in router detail: `router.py:328`. Card context is built at `:158`. Does **not** control serving. | Already **not a decider**. Preserve facts; stop presenting a diagnostic worth verdict as a second authority. |
| **F. Post-miss router:** `src/learnloop/followup_run/router.py:203`; `src/learnloop/daily_plan/objective_chooser.py:1422` | Plan/rest, wait feasibility, policy readiness, lesson offer, numeric/LLM policies. Chooses insert, wait, none, or lesson where supported. No-plan/router-off paths ask deterministically; no room to wait normally forces insert, except the lesson contest: `router.py:213`, `:222`; `objective_chooser.py:1133`, `:1429`. | Before generation and feedback release. WAIT releases feedback afterward: `jobs.py:423`. | `router_decisions` as `plan_interrupt`, objective trace, decision-state receipt, workflow binding: `router.py:279`. No-plan has a workflow choice and gate record but no router row: `:294`. Learner sees the resulting next action/why. | **The authority to retain and extend.** |
| **G. General follow-up suppression:** `src/learnloop/diagnosis/followups.py:254`, `:335`, `:350`, `:395` | Trigger/severity/surprise conditions, confidence, available time, old count cap, eligible intervention slate and `voi_stopping` value. Suppresses insertion or chooses a different slate member. Manual request can override value suppression: `:427`. | Before a candidate reaches later plan restraint. It runs in ordinary post-attempt processing; FG1’s practice/fallback lane invokes insertion after releasing its hold: `src/learnloop/followup_run/lanes.py:73`. Inside a diagnostic block it is deferred: `followups.py:647`. | `attempt_surprise` gate diagnostics; immutable `followup_value_decisions`; `followup_value` decision record; optional `voi_forecasts`: `followups.py:412`, `:2573`. Learner can see the absence/offer and gate diagnostics; this is not a router propensity. | **Worth judgments move for post-miss probe candidates.** Evidence-integrity and actual administration constraints stay. |
| **H. Scheduler admission disguised as score:** `src/learnloop/scheduling/scheduler.py:3219`, `:3304` | Episode posterior, eligible instruments, surfaces, EIG and episode VOI. VOI rejection zeroes/withholds probe score; `probe_gate` rejects nonpositive EIG. | During pool construction, before a new action draw; may run after the original miss’s feedback and decision. | Scheduler components include `voi_stop`, value/cost and surface exclusion. These travel through scheduler/prefilter/decision capture; not every evaluation becomes its own router decision. Learner sees availability/ranking consequences. | **Split it.** Eligibility remains; EIG ranking remains; EIG/value-as-admission goes for G2 candidates. |
| **I. Serve-time probe admission:** `src/learnloop/diagnosis/probe_presentations.py:391`, `:428` | Routine session/onboarding counts; effective episode posterior and eligible instruments; VOI admits/rejects the opened item. | After selection, immediately before presentation commitment. Usually after the original miss’s feedback. FG1’s existing committed presentation bypasses the new VOI admission at the sidecar door. | Accepted VOI is stored in presentation selection components. Sidecar rejection writes `probe_value`: `src/learnloop_sidecar/handlers/practice.py:625`. TUI rejection simply returns: `src/learnloop/tui/screens/practice.py:137`. Learner receives inactive/reason or ordinary-practice behavior. | **Worth veto moves.** Provider readiness, ownership, exposure and presentation validity stay. |
| **J. Continuation inside a diagnostic block:** `src/learnloop/diagnosis/probe_blocks.py:119` | Effective qualifying observations, posterior, eligible instruments, calibration status, then `voi.probe_episode_decision`. Ends block when another observation does not pay. | After a probe answer, before block feedback is released; after the initial post-miss decision, before another observation. FG1’s single-question block ends directly at `:87`. | Helper returns a Boolean, without its own router draw. Completion subsequently records a stop where applicable. Learner sees the block end and feedback release. | **Worth decision moves.** FG1 one-question boundary stays. |
| **K. Episode completion/continuation:** `src/learnloop/diagnosis/probe_completion.py:69`, `:617` | Effective observations, count budget, posterior stability/breadth, action equivalence, robust distinguishability, eligible pool and VOI. Can complete, park, or continue. | After observations; after the initial router decision. | Completion reason/detail, plus optional `probe_episode_value_decision` forecast: `:584`. Learner sees the resulting continuation or release. | **Split it.** Worth-based action equivalence/robust/value stops move. Evidence/completion facts, empty-pool parking and administrative terminal states remain separately named. |

The common episode value implementation is `src/learnloop/diagnosis/voi_stopping.py:2167`. Its **four callers** are scheduler `:3307`, presentation admission `:463`, block continuation `:146`, and completion `:645`. It is not enough to remove only the completion call.

Its current calculation is another policy: robust EVSI against a loss table, otherwise EIG converted to minutes, compared with cost; it can add lookahead. See `src/learnloop/diagnosis/voi_stopping.py:987`, especially `:1073` and `:1132`. It is not the router objective in different packaging.

Two important non-deciders:

- `accept_probe_offer` commits an already selected/requested instrument, checks eligibility and episode ownership, and pins it. Its selection components distinguish `decision_receipt_id` from `router_decision_id`: `src/learnloop/diagnosis/probe_offer.py:216`, `:275`. Do not mistake acceptance for a new value draw.
- `instructional/valuation` computes proposal valuations; `instructional/practice` proposes under caller constraints. They are not additional automatic post-miss action routers. Their protection rules remain: `src/learnloop/instructional/valuation.py:208`, `:233`; `src/learnloop/instructional/practice.py:58`, `:78`; `src/learnloop/instructional/policy.py:33`.

### One miss on the automatic repair/follow-up lane

1. Diagnosis supplies the miss’s factor. **A** selects probe versus practice. Failed/pending diagnosis and changed reserved causes have workflow fallback handling.  
   `src/learnloop/followup_run/jobs.py:328`.
2. With rivals, the worker enters the probe lane. Feedback remains held. **E** observes class facts; **D** checks hard refusals; **F** decides once.  
   `src/learnloop/followup_run/jobs.py:377`; `src/learnloop/followup_run/router.py:246`.
3. None/refusal releases; lesson wins release and defer generation; WAIT releases and marks exposure. Insert keeps the hold.  
   `src/learnloop/followup_run/jobs.py:400`.
4. Only then is the item authored, rechecked, commissioned, admitted and pinned.  
   `src/learnloop/followup_run/jobs.py:432`; `src/learnloop/followup_run/admission.py:376`.
5. The plan places that already-decided probe; it does not redraw its worth. Next serves it.  
   `src/learnloop/daily_plan/engine.py:4692`; `src/learnloop/followup_run/serving.py:152`.
6. The committed-presentation path validates and serves it, bypassing **I**’s fresh VOI admission. After its answer, FG1 ends the single-question block; evidence/completion processing follows.  
   `src/learnloop_sidecar/handlers/practice.py:564`, `:592`; `src/learnloop/diagnosis/probe_blocks.py:87`.

If **A** selects practice or the workflow falls back, ordinary insertion resumes through **G**. That is why changing only FG1’s router is insufficient.

### One miss on the learner feedback/repair lane

1. Feedback exposes a divergent or incompletely mapped cause set. `FeedbackScreen` fetches causal repair status.  
   `apps/learnloop-tauri/src/screens/FeedbackScreen.tsx:1975`, `:1991`.
2. The status RPC invokes **B**, with `start_repair=False`; it nevertheless writes a new causal decision receipt. There is no shared router draw.  
   `src/learnloop_sidecar/handlers/remediation.py:159`.
3. The learner sees the status and, when offered, “Take the quick check,” “Teach me now,” and “Not now.” The component displays the gate decision/reason.  
   `apps/learnloop-tauri/src/components/CausalAttribution.tsx:480`, `:495`.
4. Quick check calls `accept_probe_offer`, which enters/retargets an episode and commits a presentation. Not now persists a preference; teach-now explicitly authorizes repair under ambiguity.  
   `CausalAttribution.tsx:525`; `src/learnloop_sidecar/handlers/remediation.py:186`, `:203`, `:216`.
5. Later scheduling or fresh presentation/continuation can encounter **H–K**. A valid already-committed presentation is served without a new value gate.  
   `src/learnloop_sidecar/handlers/practice.py:592`.

An explicit “start repair” reaches **C → B** instead of the feedback effect. It exposes the same competing causal authority.

## 2. THE SHAPE AFTER G2

### 2a. Candidate and constraints

**Proposed:** reuse action kind `PROBE`; add a typed, immutable diagnostic payload. Do not introduce another action-kind registry. `Action` already has probe, sequence, repair and declined branches at `src/learnloop/router_objective/types.py:131`; the completeness guard is `tests/test_action_kinds_complete.py:1`.

Separate a repository-reading adapter from a pure constructor:

```python
# diagnostic shell: reads only; never judges worth
gather_probe_proposal(context, *, as_of) -> ProbeProposal | ProbeUnavailable

# pure constructor/validator
build_probe_candidate(proposal, hard_stops) -> CandidateBuild

# objective leaf values, without repository or diagnosis imports
Action(..., kind=PROBE, diagnostic=DiagnosticProbe(...))
```

The names are proposed, not existing APIs.

The payload must contain:

| Field | Consumer |
|---|---|
| Source attempt, factor, workflow/episode, candidate/item, decision origin and as-of time | Identity, deduplication, execution and record |
| Locked hypothesis IDs/order/versions, prior or effective posterior, prior basis; include `H_OTHER` | Numeric value and record |
| Outcome alphabet and complete `P(result \| hypothesis)` rows, or a typed missing-channel state; channel version/hash and uncertainty provenance | Numeric value and record |
| Hypothesis → executable repair mapping; repair coverage, targets, duration distribution and effect-model source | Numeric value and record |
| Probe duration distribution; known exposure for each timing arm | Numeric value and record |
| G1 `ProbeFacts` | Card and record; burden also feeds numeric duration |
| Availability/hard-stop reasons and source IDs | Support construction and exclusions record |
| Learner statements/marks, with provenance; separately represented routing weights | Card now; future LI4 branch weights |

Keep G1’s fields exactly identifiable: repair classes, common cover, different repairs, action relevance, separability share, repair-change share, expected avoided minutes, burden, recent count, machine-check IDs and three flags. Their definitions are at `src/learnloop/diagnosis/probe_facts.py:27`.

**Do not use G1’s scalar product as G2 utility.** Its “expected_information_gain” is a fraction of separable pairs, **not entropy**, and its avoided-minutes number already multiplies two proxies. These are explanatory facts, not substitutes for a likelihood channel (`probe_facts.py:35`, `:94`).

For FG1 before authoring, instrument-dependent facts are absent. Use an optional `ProbeFacts` plus explicit missing fields; do not call it with invented zeros. G1 already records this distinction at `src/learnloop/followup_run/router.py:122`.

Remove unavailable candidates from **support**, while retaining their exclusions in the decision material:

- **Learner refusal:** `probe_hard_stops.learner_preference`, including not-now, teach-now and no-more-diagnostics. `src/learnloop/diagnosis/probe_hard_stops.py:77`.
- **Pending machine checks:** `pending_machine_checks_for_factor`, including LO-wide checks. Existing shared use: `src/learnloop/followup_run/router.py:108`.
- **Foreign episode already measured:** `probe_episode_conflict` → `episode_conflict_reason`. Empty foreign episodes may be retargeted atomically; measured ones may not. `probe_hard_stops.py:111`, `:137`; `probe_offer.py:315`.
- **Unresolved executable-contract problems:** missing/unreviewed instrument, invalid mapping required to administer it, stale hypothesis/contract versions. Existing causal gate: `causal_orchestrator.py:777`, `:841`; acceptance: `probe_offer.py:156`.
- **Administration eligibility:** inactive/dormant LO or item, ownership conflict, reserved/closed generated item, consumed or previously seen surface, unrenderable stimulus, missing executable instrument binding. `src/learnloop/diagnosis/probe_episodes.py:821`.
- **Presentation validity and grading readiness:** correct item/session/pin, approved grading provider, no intervening display of that instrument’s answer. `src/learnloop_sidecar/handlers/practice.py:574`, `:592`.
- **An actual explicit administration budget**, where one exists. G1’s `session_budget_short` remains a fact; ordinary plan time is priced rather than converted into a new hidden cap. The optional causal budget is passed at `causal_orchestrator.py:931`; G1 reports no production caller supplying it (`docs/reviews/refactor-g1.md:318`).
- **Generation impossibility/failure:** retry exhaustion and failed admission are execution outcomes, not low utility. `src/learnloop/followup_run/jobs.py:387`, `:454`.

Recheck mutable hard stops at commitment. A later refusal appends an outcome; it must not silently replace the recorded draw.

**Exposure distinction:** a displayed instrument answer can make that instrument ineligible. Released feedback about the original miss makes the follow-up non-independent. The latter does not cancel “Show anyway”; it removes diagnostic benefit and later evidence updates. `src/learnloop/followup_run/serving.py:251`; `src/learnloop/diagnosis/probe_episodes.py:1320`.

### 2b. Price the complete two-stage policy

Verified current shortcomings:

- `_observe` models a binary ability result, not a causal result: `src/learnloop/router_objective/rollouts.py:565`.
- `_probe` compares one generic repair against none after success/miss: `rollouts.py:1070`, `:1102`.
- `objective_inputs._step` strips a probe’s repair; sequence `_do` executes segments without `_probe`. Lesson-decline execution also uses `_do`. Merely attaching hypothesis data to `Action` will therefore not fix the served comparison.  
  `src/learnloop/daily_plan/objective_inputs.py:683`, `:795`, `:807`; `rollouts.py:954`, `:1025`.
- Without a lesson competitor, FG1’s stand-in is still ordinary repair practice; with a lesson it is annotated as a probe.  
  `src/learnloop/daily_plan/objective_chooser.py:1469`, `:1479`.

**Proposed numeric policy**

For posterior `p(h)` and channel `L(r,h)`:

```text
p(r)      = Σh p(h)L(r,h)
p(h | r)  = p(h)L(r,h) / p(r)

a*(r) = argmax over feasible repair actions and “no repair”
        E[continuation utility | r, action]

Q(probe) = Eθ Σh p(h) Σr L(r,h)
           Qpath(probe, result r, a*(r), remaining block, tail | h, θ)
```

The repair policy sees the **result**, not the hidden true hypothesis. Do not compute `Σh p(h) max_a Q(a,h)`: that gives the learner clairvoyance.

Each hypothesis affects the result distribution **and** the usefulness of each repair. Deduplicate repair actions shared by hypotheses; retain every hypothesis and its probability. Include the open arm, with a safe no-repair/general-repair option rather than inventing a named diagnosis.

Use the existing objective without a new information bonus:

```text
Q = crossed_date_reward + undated_reward
    - kappa_integral + after
```

`after` already includes tail and terminal reward minus their costs. Probe time, branch-specific repair time, delayed dates and changed future ability therefore affect the existing terms. Do not add EIG, avoided-teaching minutes or EVSI again. Verified ledger: `src/learnloop/router_objective/objective.py:58`, `:86`, `:145`.

Proposed internal signatures:

```python
_Model._diagnostic_probe(action, continuation, state, ledger, streams)
    -> PathResult

_Model._repair_policy(probe, result, posterior, continuation)
    -> RepairPolicyResult

_Model._execute_steps(steps, state, ledger, streams)
    -> PathResult
```

Requirements:

- The new executor handles a diagnostic probe at any position in a sequence and in a lesson’s declined branch.
- It appends the remaining block and tail **once**.
- Preserve the current executor for predecessor behavior and ordinary actions.
- Keep public `evaluate(inputs, actions, *, draws, seed, ...)` unchanged unless a purely additive value parameter is necessary. Its current boundary is `src/learnloop/router_objective/rollouts.py:1151`.
- Use common random numbers across alternatives, deterministic hypothesis/result ordering, and separate streams for simulated truth and policy evaluation.
- Do not also apply the current independent binary ability observation to the same causal result without a defined joint observation model. Otherwise one answer earns two information effects.

There are two real data-model gaps:

1. **Unauthored FG1 probe.** The decision precedes authoring (`jobs.py:399`, `:432`). No realized instrument channel exists then.
2. **Repair effects.** A class mapping and duration do not provide a calibrated class-by-hypothesis learning effect. Existing duration sources are authored estimates, pooled latency, then a heuristic; class-specific empirical durations are explicitly unavailable. `src/learnloop/diagnosis/causal_diagnostic_selector.py:31`. Current rollout repair gain is generic/cause-class based: `rollouts.py:515`.

Recommended launch contract:

- For an existing instrument, read its actual complete channel using the same slot mapping and pinned-channel provenance used by episode valuation (`voi_stopping.py:2195`).
- For an unauthored instrument, use a versioned **generation-channel prior**, if owner-approved. Otherwise record `channel_status=unavailable` and price **zero diagnostic information**, retaining burden and any independently justified practice effect. This is a conservative model, not a diagnostic eligibility threshold.
- Do not convert blind-bundle pair separation into calibrated likelihoods. The existing causal adapter produces a noiseless partition only in a restricted regime, otherwise reports structural/missing likelihoods; it also excludes `H_OTHER`. It cannot be reused unchanged.  
  `src/learnloop/instructional/valuation.py:233`, `:724`.
- For repair effects, make the conditional model explicit and versioned. A defensible initial model uses the existing gap/slip/unknown effect priors for a repair covering `h`, with an explicitly seeded effect prior for an uncovered repair. The uncovered-effect prior is an owner decision; do not disguise zero effectiveness as a machine fact.

**Draw and propensity**

`π_Q` remains the objective’s argmax with paired-SE tie handling (`objective.py:170`). The outer router mixes numeric, LLM and staged components, applies the exploration floor, then draws once. Log the marginal probability of the served action, not `p(h)`, `p(r)`, the selected component’s weight, or the chance that generation succeeds.

The block chooser is pure today (`src/learnloop/router_objective/choose.py:148`), but post-miss `_mixed` still assembles/draws inline (`objective_chooser.py:1199`). Extract its pure choice seam before G2. Preserve draw ordering and existing record bytes in that extraction.

With no LLM card/answer, numeric evaluation still runs and receives failure-share redistribution under the existing mixture rules. It must price the same diagnostic payload. Current numeric-before-LLM behavior is at `objective_chooser.py:1161`; redistribution/draw at `:1199`. A missing LLM is not permission to return to `decide_probe`.

**Cost, already measured—not measured for this design**

G1 measured, at eight draws:

- Whole current probe value: median **227 ms**, range 58–294.
- One result-policy branch: **77 ms**.
- One true-path repair branch: **38 ms**.
- Belief-world construction: **1.3 ms**.
- Estimated hypothesis expansion: **379 ms at H=3 / 607 ms at H=6** with shared result policies; **681 / 1,362 ms** if each hypothesis needs a whole rollout.
- Sixteen draws added 3–8% in that measurement.

These are per candidate per batch, not end-to-end Next latency. More outcomes and more distinct repairs can exceed those bounds. Source: `docs/reviews/refactor-g1.md:199`.

### 2c. What goes, and what replaces it

For G2-owned post-miss decisions and their continuation:

| Old authority | Replacement |
|---|---|
| `decide_probe`/`probe_verdict` worth result | Diagnostic proposal plus router utility/draw. Keep predecessor implementation reachable below tag. |
| Common-cover/action-equivalence **skip verdict** | Same repair policy across results naturally gives zero repair-selection information benefit. Facts remain on card. |
| Minimum EIG and minimum action-change thresholds | Nothing. Complete result-conditioned utility replaces them. |
| Avoided-teaching proxy minus burden plus margin | Actual branch duration/effect inside `Q`; no additive proxy and no margin. |
| `recent_diagnostic_limit = 2` | Nothing as an admission rule. Existing session attention price already charges spent time. Retain count as observed context. Any extra fatigue effect must be a learned quantity with a seeded prior, not a renamed cap. |
| Follow-up value suppression and probe-intent worth prefilters | Candidate proposal into the same action decision. Preserve general non-probe intervention behavior outside G2 scope. |
| Scheduler EIG/value veto | Eligibility independently determined; EIG ranks the staged proposal. |
| Serve-time VOI veto | Validate the recorded router selection and current hard stops; no fresh valuation. |
| Block/completion VOI and worth-based action-equivalence/robust stop | One continuation router decision, reused by block release, scheduling and serving. |
| Repair’s “probe first because worth says so” hold | Ambiguity and possible repair benefit support the probe candidate; they do not impose a second policy. |

The unfitted defaults are verified at `src/learnloop/diagnosis/causal_probe_coherence.py:95`; the resolver’s own documentation says nothing currently fits that scope (`:403`).

Do not remove the entire `voi_stopping` module. It also serves other sites. Dispatch by **tag plus explicit decision origin**, not a global “all probes” test. Causal origin is already parseable through `src/learnloop/diagnosis/probe_hard_stops.py:104`; additionally carry the source miss/workflow for post-miss interventions without a causal-origin episode.

Old configuration flags must not reactivate a second worth gate for a G2-owned decision. Router/model unavailability selects the router’s recorded fallback; it does not select the predecessor causal policy.

### 2d. What stays, including the screen

- Rival count stays as lane existence.
- EIG stays as staged ranking.
- Insert stays at **that post-miss Next**, with feedback held.
- WAIT still releases feedback. Its numeric diagnostic information value is zero under the exposed-answer rule.
- FG1’s single-use reservation, protected authoring and single-question release stay.
- A router no-intervention result is a decision for this boundary, not proof that the factor is resolved.
- Diagnosis belief updates, the two existing locks and discriminating-observation semantics do not become G4 under this change.

**Proposed learner-lane change at mvp-0.64:**

1. `causal_repair_status` becomes a facts/status read for this path. It must not independently mint a new worth verdict or reroll on component remount.
2. Return the existing status payload plus a router-owned disposition:
   ```text
   router_decision_id
   router_state: pending | selected | not_selected | unavailable
   probe_offered: true only for an executable, selected probe
   candidate_id / presentation_id where bound
   hard_stop_reasons
   ```
   Do not put a router ID in `decision_receipt_id`; they are different identities today (`handlers/remediation.py:150`).
3. Feedback renders the existing panel without an autonomous “quick check” recommendation. A selected probe is reached through the existing Next/offer mechanism. No new hypothesis picker or screen redesign.
4. An old/stale `causal_probe_offer_action` request at the new tag may consume an existing compatible selection, but may not create an independent automatic offer. Return a normal typed result such as `accepted:false, reason:router_decision_required` with current disposition.
5. “Not now” remains a durable refusal; “Teach me now” remains explicit learner authorization.
6. Below the tag, preserve the present status/offer flow exactly.

An explicit repair request without a plan needs a minimal router context and a durable decision; no-plan currently asks without a router row. Generalize the existing follow-up record builder, which already permits nullable plan/block fields (`src/learnloop/router/plan_log.py:717`), rather than fabricate a plan.

**LI compatibility:** the accepted spec is `docs/specs/spec_learner_input_after_miss_v1.md`. Keep a settlement seam before diagnostic proposal/draw so LI1 can defer diagnosis and start its clock after the learner’s response. LI1–LI3 must not depend on G2. Provide a separately versioned routing-weight input for LI4; its positive reweighting preserves all locked members and must not alter belief/certification. Do not implement LI4 learning or its new UI in G2. The dependency is explicit at that spec’s `:219` and `:229`.

## 3. PERSISTED MEANING AND THE TAG

**Proposed tag:** one `PROBE_ROUTER_ALGORITHM_VERSION = "mvp-0.64"` constant, appended to `SUCCESSOR_CHAIN`, with one tag predicate. Existing chain/head mechanics are at `src/learnloop/algorithm_versions.py:947`, `:1007`, `:1075`.

**No kill switch.** The Nov 16 playbook supersedes G2’s older switch language: `docs/algorithm-change-playbook.md:156`.

### At mvp-0.64

New decisions may change:

- Whether/when a probe is offered.
- Whether a repair or lesson wins instead.
- Continuation after a probe answer.
- Support, numeric values, LLM card, mixture probabilities, selected arm and subsequent execution rows.
- Decision-state/trace material and policy/generator identities.

New records must freeze:

- Proposal and exclusions.
- Full numeric inputs/actions, without receipt rounding.
- Locked set, effective posterior/as-of, channel and repair-model versions/values.
- Known exposure by arm.
- Numeric seed/draw count, policy results, support order, mixture seed/uniforms, distribution and chosen propensity.
- Execution binding and later refusal/exposure/failure separately.

Use existing `router_decisions`, `router_objective_traces`, `decision_state_receipts`, decision records and bindings where possible. If a separate snapshot table is necessary, classify it as an immutable `RECEIPT`; the playbook requires table roles and rebuild ownership (`docs/algorithm-change-playbook.md:33`).

### Below mvp-0.64

Keep the predecessor’s:

- Gate ordering, thresholds, count rules and manual overrides.
- No-room/no-plan behavior.
- Prompts/cards, seeds, support ordering, numeric implementation.
- Records and omission behavior, including G1’s absent-instrument marker.
- Completion and serving paths.

“Below tag” must mean the actual predecessor branches, not “new value with a large penalty.”

### Upgrade action

**Recommendation: `Link(PROBE_ROUTER_ALGORITHM_VERSION, idempotent_projection)`, not a whole-vault rebuild.**

G2 changes future decisions, not the interpretation of already-recorded answers or historical decisions. Existing beliefs retain the predecessor's (mvp-0.63's) semantics. The standard projection activation is still an upgrade action; “no rebuild” here means **no whole-vault evidence replay**. See `src/learnloop/ops/upgrades.py:101`.

This depends on a required test: historical completion/episode reconstruction must not newly run G2 policy during replay. If implementation changes what replay derives from old observations, this recommendation becomes false: select `whole_vault_rebuild` and document the additional semantic change before landing.

Do not rewrite old causal decisions, probe observations, locks, presentations or completed episodes.

### Identity pins

Verified registry: `tests/identity_pins_helpers.py:1561`.

Expected head-default movements from advancing the tag:

- `A1–A4.manifest_hash.init`
- `C3.boundary.init`
- `C3b.chooser`
- `C3b.start_key`
- `C5.init`
- `C6.init`

The preceding tag landing documents this family of movements; G2 must explain its actual diff, not blindly accept regenerated pins.

Deliberate new identities:

- Post-miss boundary identity includes diagnostic proposal/channel/repair-model hash, effective posterior, exposure state and policy version.
- Add a production-path identity pin for that boundary; `C3b` currently pins the ordinary block boundary, not this entire new contract.
- Make the learned-tail generator distinguish the new rollout policy. `C5` names that grouping/change point (`identity_pins_helpers.py:1593`).

Must not move at fixed predecessor inputs:

- `C3m.seed`: the mixing RNG algorithm.
- `C3.router_settings.init` and `C4` settings/switch snapshots merely to introduce a new switch.
- Legacy synthesis identities.
- Instrument/card/lock identity algorithms, grading identities, substrate identities and unrelated prompts.
- `OBJECTIVE_VERSION`/`TERMINAL_VERSION` merely because probe transition dynamics change. Prefer a scoped probe-policy version.

Default-tag movements and a changed function at a fixed tag are separate assertions. Add explicit mvp-0.63 pins/replay cases so head-default regeneration cannot hide predecessor drift.

### Proof without a switch

On identical stored history:

1. Base checkout at mvp-0.63 versus implementation at mvp-0.63: identical served values and records under fixed inputs, clocks, IDs, model answers and draws.
2. Implementation at mvp-0.63 versus mvp-0.64: only approved behavior differences.
3. Rebuild each tag twice; compare semantic projections and immutable receipts.
4. P-draw reproduces recorded component distributions, support order, seed, chosen arm and propensity. Full numeric replay additionally needs the newly frozen input snapshot.
5. Upgrade interruption/recovery/idempotence tests run through the new `EXPECTED_ACTIVATIONS` row: `tests/test_upgrades.py:59`.

## 4. THE STEPS

All test execution below is for the implementer; none was run for this design.

| Step | Files/functions and first proof | Expected movement | Size / stop rule |
|---|---|---|---|
| **1. Characterize every door** | Add `test_probe_router_authority` coverage for A–K, both surfaces, no plan, no wait, lesson, manual request, retry and existing presentation. Extend `tests/diagnosis_journey_helpers.py:467`; pin old behavior before editing. | No production, golden or identity changes. New tests may add new baseline cases. | **S.** Stop if a supposedly reached gate has no demonstrated caller; resolve the path first. |
| **2. Extract pure post-miss choice** | Move `_mixed`’s policy-status/weight/component/draw assembly into a pure value function near `router_objective/choose.py`. Keep shell ID allocation, timing and writes in `objective_chooser.py`. First test: serialized old/new choice and record equality for every readiness/failure/support combination and fixed uniforms. | Existing P-draw, cards, traces, goldens and pins identical. | **M, structural.** Stop on any changed RNG consumption, prompt, propensity or fallback. |
| **3. Extract diagnostic proposal reads** | Factor `_status_for_factor` gathers into a value object; old verdict consumes the same values. Reuse `ProbeFacts`; separate missing-channel status from numeric zeros. Files: `causal_orchestrator.py`, `probe_facts.py`, channel/repair adapters. First test: old receipt inputs, parameter manifests and resulting status identical. | All old persisted output identical. New constructor-only tests, no new live receipts. | **M, structural.** Stop if extraction changes query-time availability, lock selection or prior normalization. |
| **4. Build the pure successor evaluator, unserved** | Add diagnostic payload and pure branch evaluator; retain old `Action` serialization/behavior when payload absent. Tests first: informative channel changes preferred repair; flat channel does not; open arm retained; no clairvoyance; duration charged once; sequence/lesson-decline parity; exposure gives no information; missing channel explicit. Extend `test_action_kinds_complete.py`. | Existing goldens/pins identical. New isolated tests only. No production shadow computation, which could alter deadline behavior. | **M.** Stop until channel and conditional repair-effect contracts are explicit; do not invent probabilities during adapter coding. |
| **5. Prepare the comparison and landing report** | Add a read-only replay/report driver consuming copied ledgers or exported frozen inputs. Capture real successor snapshots on controlled copies with fixed model outputs. Implement coverage classifications in §5. | No served behavior changes. Report artifacts only. | **M.** Stop on future leakage, fabricated missing inputs, or a report unable to distinguish exact from reconstructed rows. |
| **6. G2 behavior landing, alone** | Add mvp-0.64 constant, upgrade row/test row; wire candidate gathering, new evaluator, router-owned continuation, sidecar disposition and no-plan logging. Remove A–K’s competing worth control **only at the tag and G2 origin**. Update `router.py`, `jobs.py`, `admission.py`, `serving.py`, objective inputs/chooser/card/trace, followups, scheduler, presentations/blocks/completion, remediation handlers and Feedback component DTOs. | Approved successor journey rows/cards/values/support/propensities and head defaults/pins move. Predecessor snapshots remain identical. | **L.** Stop on any remaining worth veto, duplicate draw, feedback leak, unsupported likelihood, predecessor difference, or unread owner report. |
| **7. Landing verification record** | Record both-tags results, copy rebuild results, report coverage, latency distributions, changed identities and owner rulings. No additional policy cleanup in this commit. | Documentation only. | **S.** Stop rather than declare success with missing parity or unclassified deltas. |

Step 6 must include the whole authority transfer. Do not land “router decides” while leaving follow-up suppression, scheduler zero-EIG admission or continuation VOI active.

The existing journey golden records **all registered tables**, stage by stage, and compares two different ID streams while retaining meaningful fixed-input hashes: `tests/diagnosis_journey_helpers.py:28`, `:39`, `:88`; `tests/test_diagnosis_journey_golden.py:19`. Extend that proof rather than replacing it with outcome-only assertions.

Required successor journeys:

- Insert with held feedback; WAIT; none; lesson accepted/declined.
- Common repair and different repairs.
- Missing versus flat versus discriminating channel.
- Machine check, not-now, measured foreign episode, stale pin.
- No plan, no room to wait, absent LLM, failed numeric.
- Learner status reread and double acceptance.
- Show-anyway before answer.
- Continuation accepted/declined, with exactly one decision.
- Upgrade while pending, decided, authored, served and answered.

Apply the strategy’s cost rule to the structural work; do not let a broad action-framework rewrite consume G2. The E6 result already favors focused dispatch and guard coverage over a universal action registry (`docs/reviews/refactor-e6.md`).

## 5. THE REPORT THE OWNER READS BEFORE IT LANDS

The report’s unit is **a decision opportunity**, not merely an answered probe. Include suppressed opportunities, hard refusals, no-plan choices, learner offers and continuation decisions.

For every recorded opportunity, produce:

```text
vault-copy / source miss / factor / workflow / episode / decision time
surface and decision origin
predecessor:
  hard exclusions, gate answer, router support/draw, final offered action
successor:
  hard exclusions, channel/effect provenance, support,
  Q terms, π_Q, mixture distribution, fixed-draw action
difference:
  candidate absent/present; ask/wait/none/lesson/repair; timing/exposure;
  which removed authority caused the difference
replay quality:
  exact | reconstructed-as-of | controlled synthetic | not computable
cost:
  gather, channel build, branch-policy evaluation, rollout, record;
  completed draws; hypothesis/result/repair counts
```

Report both:

- **Policy disagreement:** predecessor’s final probe answer versus successor’s numeric recommendation and overall action distribution.
- **Coupled-draw disagreement:** same recorded random uniforms where applicable. A changed candidate set can change the sampled result even when the top choice agrees.

A learner’s acceptance is not a randomized router selection. Do not invent its propensity.

### Stored inputs available today

| Rows | What they support |
|---|---|
| `causal_probe_decision_receipts` | Exact replay of many old causal verdicts: classes, burden, proxy values, preferences/count/budget, parameters and provenance. Writer: `src/learnloop/diagnosis/causal_orchestrator.py:677`, `:956`. |
| `router_decisions`, cards/payloads, `router_decision_bindings` | Served support, mixture components/uniforms, selected action/propensity and later generated-item binding. `src/learnloop/router/plan_log.py:717`; `src/learnloop/followup_run/router.py:320`. |
| `router_objective_traces` | Candidate values/terms, policy answers, numeric precision, sensor sources, mixture and versions. `src/learnloop/router_objective/trace_assembly.py:231`. |
| `decision_state_receipts` | Selected item/LO state, posterior readings, goals, active time and versions. Optional/best-effort and partially rounded. `src/learnloop/router_objective/decision_state.py:295`. |
| `followup_value_decisions`, `attempt_surprise`, `decision_records`, `voi_forecasts` | Suppression, old slate/value decision, manual override and some refusal provenance. `src/learnloop/diagnosis/followups.py:2573`; `src/learnloop/diagnosis/chain_records.py:217`, `:260`. |
| Workflow rows, presentations, hypothesis sets, candidates, blind bundles, observations and preferences | Timing/exposure, locked membership and priors, actual later instrument, selected posterior, result and constraints. Pin writer: `src/learnloop/diagnosis/probe_offer.py:266`; effective evidence reader: `src/learnloop/diagnosis/probe_episodes.py:1341`. |
| Episode completion detail | Old terminal value-stop reason and forecast; not every continue evaluation. `src/learnloop/diagnosis/probe_completion.py:584`. |

### Missing today

- A full unrounded `Inputs` plus complete `Action` tree for every post-miss valuation. The current decision-state receipt is not that snapshot.
- The generated instrument’s channel **at a decision made before generation**.
- A calibrated generation-channel prior and class-by-hypothesis repair effects.
- An exact record of every continuation “continue” evaluation and every TUI refusal.
- A router row for current no-plan FG1 decisions.
- A successor LLM distribution for a changed card.
- Reliable historical end-to-end latency for every door.

Therefore:

- Replay old thresholds and old outer draws exactly where their receipts suffice.
- Reconstruct as-of inputs only from rows available at that time; label reconstruction.
- Never use a later generated instrument as if known before authoring.
- Freeze old LLM outputs only for a **controlled numeric comparison**, not a claim about the successor LLM policy.
- Report missingness and denominators by path. “Zero differences” with zero computable cases is not evidence.

Run on **fresh backup-API copies**, with no live mutation, model calls or authoring during replay. The G3 review found October-derived copies missed November probe activity entirely (`docs/reviews/refactor-g3.md:35`).

Synthetic journeys must supply complete snapshots and cover all cases in step 6. Report median/p95/max per decision and by hypothesis/result/repair count; separate cold/warm measurements and numeric runtime from authoring/model wait.

## 6. RISKS AND WHAT COULD BE WRONG

1. **Post-miss Next can become slow.** The current restraint path runs numeric evaluation before awaiting the LLM; rollout deadlines are checked between candidates, not inside every expensive branch. `src/learnloop/daily_plan/objective_chooser.py:1167`; `src/learnloop/router_objective/rollouts.py:1186`. Measure end-to-end latency and deadline overshoot. Share result-policy computations and use complete batches; never publish a candidate comparison with one candidate evaluated more deeply without recording that design.

2. **A hypothesis map is not a probability model.** Blind-bundle separability does not supply a calibrated full channel. The existing causal valuation adapter excludes the open arm and can refuse likelihood construction (`instructional/valuation.py:243`, `:729`). A wrong mapping can make the router confidently buy useless questions.

3. **Flat probes must have zero diagnostic benefit.** If `L(r,h)` is identical across hypotheses, posterior and repair policy remain unchanged. The numeric router should ordinarily prefer the equivalent immediate repair/continuation without the extra probe burden. It must not award binary-ability information merely because the item has kind `PROBE`. The outer mixture can still explore or follow another component; log that honestly. The mvp-0.61 work needed an injected discriminating instrument because its generated test instrument was flat; this does not establish that every real generated probe is flat (`docs/reviews/algorithm-mvp-0.61.md`).

4. **Double counting.** Counting avoided teaching, EIG, the adaptive repair and its tail separately would exaggerate benefit. The successor must accumulate one path ledger and one tail. Current sequences and lesson-decline paths are the likely implementation trap (`objective_inputs.py:807`; `rollouts.py:1025`).

5. **Exposure is stronger than contamination damping.** At mvp-0.61 an exposed probe answer updates no episode belief, has discount zero and qualifies nothing. G1’s older suggestion of reduced weight is obsolete. Read `effective_posterior_as_of`; do not use raw stored after-posteriors as current truth. `src/learnloop/diagnosis/probe_episodes.py:1341`, `:1426`. Known WAIT exposure belongs in value; later show-anyway exposure belongs in evidence admission and execution outcome.

6. **G3 did not validate interchangeable beliefs.** Its fresh data had four paired answers, three exposure refusals, no competing named-cause resolutions, and equal lock membership but different IDs. The other two vaults had no probes. That is weak evidence for G4, not permission to merge channels in G2 (`docs/reviews/refactor-g3.md:27`).

7. **IH shares this boundary.** Preserve one draw including the eligible lesson offer. A lesson win releases feedback and avoids unnecessary probe generation. Decline retains the follow-up opportunity, but after released feedback its diagnostic value changes. Preserve separate offer-decline and probe-refusal meanings. Current support and declined branch: `src/learnloop/daily_plan/objective_chooser.py:1422`, `:1481`; execution: `src/learnloop/followup_run/jobs.py:413`.

8. **No-room support is a substantive change.** Today no room to wait can force a probe, or restrict the contest to probe/lesson. Letting the router decide whether to probe requires a meaningful no-probe alternative. Recommend `{probe-now, no-intervention, eligible lesson/repair}` when WAIT is infeasible. This must be visible in the owner report, not smuggled in as structural work.

9. **Sessions open across upgrade.** A recorded decision keeps its old support, propensity and execution contract. Do not redraw a decided workflow because the vault tag changed. An undecided workflow takes the new policy; existing pins and evidence remain readable. Prefetch reuse must include the new policy/input identity. For old committed learner offers, preserve consumption of the old receipt while rechecking current hard stops. Existing idempotency mechanisms: `router.py:313`; `probe_offer.py:246`.

10. **Stopping probing is not resolving the cause.** A boundary’s no-intervention result should defer further probing, not forge `decision_stable`, a discriminating match or a resolved factor. Keep epistemic completion separate from router disposition.

## 7. OWNER DECISIONS

These are the decisions the code and recorded history do not settle.

1. **What prior prices an unauthored probe?**  
   **Recommendation:** ship the typed missing-channel case conservatively, with no diagnostic information credit, unless the owner approves a versioned prior predictive model for generation quality. Preserve decision-before-authoring.  
   **Changes:** how often numeric policy selects newly generated probes when the LLM is absent. Authoring first would change FG1/IH timing and paid work and needs an explicit different decision.

2. **What is the initial conditional repair-effect model?**  
   **Recommendation:** reuse existing cause-class effect priors where a repair covers a hypothesis; explicitly choose and record the uncovered-repair prior. Do not treat repair-class membership as measured effectiveness.  
   **Changes:** the value of distinguishing causes, especially where competing repairs target the same LO. Existing receipts do not identify these effects well enough to fit them automatically.

3. **Allow no intervention when WAIT is infeasible?**  
   **Recommendation:** yes. A time-placement constraint should remove WAIT, not force a probe.  
   **Changes:** the current deterministic insert and probe-versus-lesson-only cases. This is required for the strongest reading of “the router decides whether.”

4. **Accept the measured launch tradeoff?**  
   **Recommendation:** decide from the fresh-copy report: disagreement rates, missing-channel coverage, flat-channel behavior and measured Next latency. The owner has already accepted somewhat slower simulation; no new arbitrary speed cutoff is needed.  
   **Changes:** whether this concrete model is ready to serve, not the agreed architecture.

Already settled and not reopened: mvp-0.64, no new kill switch, held post-miss Next, no hand-set worth margins, no shrinking locked sets, no new hypothesis-list UI, and exposed answers contributing no belief update.

## 8. WHAT READING COULD NOT SETTLE

Each item has one bounded verification.

- **Does the current IH probe lose its repair branch in every sequence shape?**  
  One production `build → evaluate` test comparing standalone probe, probe-first sequence, probe-last sequence and lesson decline.

- **Can replay call completion policy in a way that changes old episode state?**  
  One same-history mvp-0.63/mvp-0.64 rebuild test with a stored value-stopped episode. This settles the upgrade activation choice.

- **Can every planless door persist an idempotent router decision using the generalized builder?**  
  One no-plan repair/status/retry journey, including crash between decision and binding.

- **Does a selected candidate survive all downstream worth gates?**  
  One sentinel test that makes every legacy worth function raise, then serves and continues a mvp-0.64 post-miss probe through scheduler, sidecar and TUI.

- **How much real history is exactly replayable?**  
  One read-only coverage report on fresh copies, grouped by the row sources in §5.

- **How often are actual complete channels flat, missing, or incompatible with the causal lock?**  
  One as-of channel audit, retaining `H_OTHER` and reporting source/version rather than coercing missing rows.

- **Are the proposed repair branches executable and distinguishable in the current utility model?**  
  One two-hypothesis/two-repair fixture where only the channel changes; verify that informative evidence changes repair choice and utility, while identical repairs do not.

- **What does hypothesis branching cost at the real boundary?**  
  One benchmark over recorded complete inputs at H=2–6, with outcome and repair counts reported; include full Next latency and deadline overshoot.

- **Do old committed offers and prefetch jobs survive upgrade correctly?**  
  One interrupted-session matrix covering pending, decided, generated, committed and served states.

- **Can LI settlement precede proposal construction without consuming the FG1 wait budget?**  
  One fake-clock integration test that delays learner-input settlement, then verifies diagnosis, draw and hold timing.

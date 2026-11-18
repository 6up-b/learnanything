# Adaptive difficulty, memory and families (ADM): repeats train the model, and decay is learned

**Status:** draft, Nov 16 2026, for the owner's review. Revised on 2026-11-17 after two independent reviews against main `88b10fb90d`. Not queued. The owner decided Q2 on Nov 17 (§4.3). Evaluated in `docs/reviews/refactor-strategy-v3-audit-2026-11-16.md` §4.1.

**Depends on:** RE2 (one retrievability function; landed). L4's review for adaptive difficulty (refactor strategy §2.18), so the update can be called with plain values (ADM1). From `spec_evidence_packets_v1.md`: nothing for ADM0 and ADM1; EPp's repeat receipts for ADM2a's prospective comparison (strongly wanted, not required, so EPp should start now); EP0's attempt facts (hint depth and timing, reveals, delay source) for ADM3 and ADM4. ADM1's memory fold names its time policy with EP0t's preset when EP0t has landed.

**Amends:** `spec_adaptive_difficulty_v1.md` D10 (for measurement only) and §5.5's fixed `h_w`. It builds on `spec_learned_parameters_v1.md` §4.6 and `spec_recognition_and_effort_v1.md` RE8 rather than adding a second memory model, and changes RE8's first consumers (owner, Nov 17; dated note in RE8).

## 1. The owner's words (Nov 16 2026, verbatim)

> adaptive difficulty should have repeated surface families train the predictive posterior. Repeated successes can primarily update item memory or family proficiency when the explanations fit. delayed performance can teach the model about retention, novel family performance can better distinguish transferable knowledge from familiarity, shared latent family/item effects account for dependence. Another change I want to make in AD is to change the fixed 6 hour warmth delay to a learned decay, and missing item/family memory within AD to an exposure dependent memory states with adaptive retention (the former can perhaps be some sort of LTC-adjacent formulation such as dm/dt = −m/τ(m,z)

Standing rules that bind this spec: no point-fitted or hand-set hyperparameters; every effect that weighs an observation is latent state with an a-priori, versioned prior and a stated basis (AD's A5; owner, Oct 24). AD is derived and replayable with no model call (A1) and never writes evidence, mastery, FSRS state or certification credit (A2). A change to what AD computes is a successor under the playbook: one tag, one upgrade row, one test row, and no kill switch unless the owner asks (owner, Nov 16; playbook rule of 2026-11-16); the predecessor stays as a replay arm with a pinned state hash. Learner data stays local; only aggregate results reach a tracked file.

## 2. In plain words

Today adaptive difficulty learns only from the first time you meet each kind of question. Every repeat is thrown away, it has no forgetting, and it treats "you practised this topic recently" with one fixed six-hour constant.

After this spec:

1. **Every graded repeat that measures something updates the model's measurement.** The credit for practice that transfers to unseen questions is still given once per family, so drilling one item cannot inflate readiness.
2. **The model has three places to put what an answer shows:** your transferable ability on the topic, your familiarity with this family of questions, and your memory of this exact item. A success on something you've drilled mostly moves the last two. A success on a family you've never seen moves ability.
3. **Memory fades along the curve the scheduler already uses.** AD reads it through the one retrievability function. Later, AD alone learns how you differ from that curve, and a report shows whether the rest of LearnLoop should too.
4. **The six hours becomes a learned weighting over a few time scales,** in its own step so its effect can be seen apart.

What the learner sees: nothing new on a screen. Predictions for practised material stop being blind, the 70-80% band is drawn with better numbers, and "ready on unseen questions" is separated from "good at the ones you've drilled".

## 3. What the model does today (checked against the code at `88b10fb90d`)

| Fact | Where |
|---|---|
| The predictor: `η = Σ_f w̃ θ_{f,k} − β·φ(x) − α·z − ε_i + ζ·w`, a graded logistic with a guess floor and a lapse; warmth enters as the `zeta` coordinate inside the projection | spec §5.4; `adaptive_difficulty/model.py:68`; `state.py:109-163` |
| After each eligible attempt, `View.learn` adds `weight·γ` to every measured cell, and to coupled cells in the subject view, whatever the outcome. `γ` is a latent coordinate with prior N(0.2, 0.01) | `state.py:275-316`; `replay.py:754-768`; `priors.py:142` |
| Trains only on the first graded attempt per surface group; a repeat is excluded with reason `repeat_surface`. As coded, the surface is taken before the eligibility checks run, so an ineligible first attempt still uses it up | `replay.py:466-476`; D10: "repeats stay FSRS's" |
| A surface group is the first of `shared_stimulus_id`, `source_family`, `solution_recipe_family`, `surface_family`, else the item (`item:<id>`) | `replay.py:263-272` |
| The item residual `ε_i ~ N(0, τ₀²)`, `τ₀ = 1`, is never stored. It is integrated out, as `(A·τ₀)²`, in the update, the predictive success, `F_x` and its cached inverse, `P_band` and cell information | `priors.py:36`; `model.py:102`, `:177`, `:525`, `:578`, `:593`, `:702` |
| The bank is a full-covariance Gaussian per grid point that creates coordinates lazily; `marginalize` exists only for simulations | `model.py:343`, `:421-432` |
| No forgetting of the mean; cell variance drifts 0.01 a day | `model.py:479`; spec: "forgetting stays with FSRS" |
| Warmth: `w = exp(−Δh / 6)` over the last exposure to the learning object (attempt or reveal, through the material view), `ζ` learned with prior N(1.0, 0.25), the 6 is `WARMTH_HOURS` | `replay.py:296-320`; `priors.py:38`, `:143` |
| Hyperparameters are a grid posterior: 36 points with coupling on, the uniform points otherwise. LO views use one fixed point (`LO_VIEW_POINT`) | spec §5.6; `replay.py:614-639`; `priors.py:91` |
| Reading dose uses two fixed scales with learned weights | `priors.py:42` |
| Serve inputs (`item_serve_inputs`) and the `ad_threshold@*` receipts are written only for a never-attempted item. A repeat would resolve historical inputs: no `z_v1` or panel signals, and `pre_exposed` read as false | `serve.py:109-128`; `replay.py:435-446`, `:497`, `:518-520` |
| Outcome categories: help before work scores 0; a primed attempt is censored if bound to a presentation and excluded (`primed_unbound`) if not; pre-exposed is excluded. A retry within a routine answer display's coverage (about 25 hours) is primed | `outcomes.py:60-104`; `reveal_coverage.py:44-53` |
| The forecast scorer scores only eligible attempts; an item-scoped receipt binds to the revision's first presentation | `scoring.py:45-110` |
| The router's combiner: `logit P = a0 + aA·η + aR·(logit R − η)·[practiced]`, a labelled seed prior (0, 1, 0.5), variances 0.25, fitted on frozen sensor values joined from traces | `router_objective/memory.py:1-20`, `:45-46` |
| The retrievability curve is FSRS-6's, `R = (1 + f·t/S)^(−d)`, `d = weights[20]`, read through one function for every caller but FSRS itself | `scheduling/fsrs.py:58-95`; `tests/test_one_retrievability.py` |
| FSRS fits `rating != AGAIN`; AD predicts unassisted success, category 2 | `fsrs_fitting.py:79-93`; `outcomes.py:107` |
| Item FSRS state is current-only: "the live path never freezes them per attempt" | `scheduling/review_log.py:3-9` |
| `family_memory_state` holds only authored-family rows (foreign key to `activity_families`), current state only, from cold memory-eligible reviews, with a retrospective `current_content` fallback, written only by a rebuild replayer. The class behind it supports item, family and LO keys | `migrations/168_activity_family_membership.sql:37-46`; `substrate/family_memory.py:1-60`; `scheduling/family_memory_model.py:43` |
| AD's protection guard denies `practice_item_state` and `fitted_parameters`, and refuses unclassified tables such as `family_memory_state` | `adaptive_difficulty/protected_tables.py:102`, `:178` |
| Fitted FSRS weights keep their history: each fit inserts a row, the previous one is deactivated with a time | `db/repositories.py:7222-7262` |
| The events fingerprint hashes the replay's inputs; `ItemSpec` has no family key; the state hash hashes the banks | `replay.py:842-866`; `state.py:38-52`; `model.py:622` |

So three of the owner's phrases need restating before the design. The six hours is a decay scale on a covariate, not a delay or a window. AD doesn't have a gap where item and family memory should be: it has a rule (D10) that keeps repeats out. And the family FSRS projection that exists is retrospective and keyed to authored families, so it cannot serve a historical replay.

## 4. Design

### 4.1 What a repeat is, and three eligibilities

Today one answer decides everything. The successor asks three questions of each attempt, each returning its reason:

| Eligible to | Rule |
|---|---|
| **score** (a forecast receipt for it is scored) | every eligible plan presentation with inputs frozen at that presentation and a defined outcome category |
| **measure** (update the measurement posterior) | the predecessor's chain without `repeat_surface`: attempt type, held, unassessed, zero mass, pre-exposed, primed unbound, inputs excluded; plus `primed_repeat` (below) |
| **learn** (apply the transferable increment `γ`) | the predecessor's rule exactly: the first graded attempt of a surface group takes the surface, and it gets `γ` only if it is also measurement-eligible |

**Why `γ` keeps the one-opportunity rule.** Under the first draft every repeat would add `weight·γ` before reading its outcome: five drills of one item would raise the cell by about one logit at the prior, into the unseen-item prediction the band draw and the router's `η_L` read. A learned alternative (a repeat-transfer coefficient with a zero-centred prior) is possible, but with about 19 same-item repeats in the largest vault it would sit at its prior for months and make transfer from drilling a fitted quantity with nothing to fit it. It is an alternative for after ADM2a's report (§6).

**What a repeat is, as an observation:**
- **Inputs frozen at every presentation.** From ADM2a, `item_serve_inputs` is written at every eligible plan presentation, repeats included, with `pre_exposed` and the memory context (§4.3). Before ADM2a, EPp records the predecessor's repeat inputs in evaluation receipts (`spec_evidence_packets_v1.md` §7.7). Historical repeats without frozen inputs resolve by today's historical path, are marked `inputs: historical`, and form their own report stratum; whether ADM2a reads EPp's captured inputs for repeats served between the two steps is its step 0's call.
- **An auto-primed repeat** (a retry within the display coverage of this item's own answer) is not measured (`primed_repeat`), since the display was of the very answer being asked for. It is counted. A primed first surface keeps the predecessor's treatment.
- **Help before work** still scores 0 (ADM4 is where help becomes covariates).

This cannot land alone: if a repeat measured and the model were otherwise today's, five successes on one item would count as five independent measurements of ability. §4.2 and §4.4 land with §4.1 as one successor.

### 4.2 Family and item effects, as coordinates of the bank

The residual that today is integrated out and forgotten becomes two stored effects:

```
ε_i  →  −(e_F + e_i)
e_F ~ N(0, ρ·τ₀²)        one per surface group, shared by its items
e_i ~ N(0, (1−ρ)·τ₀²)    one per item
```

Positive means easier for this learner than the shared terms say. Their prior variances sum to today's `τ₀²`.

**The update is the bank's own.** `e_F` and `e_i` are coordinates appended lazily to each view's bank at the first attempt on the family or item, with zero prior covariance with the rest. Each attempt's projection `u` gains −1 on the item's two coordinates, and the bank's existing update runs over the joint Gaussian, keeping every covariance. That is exact within the Gaussian projection AD already makes per attempt; nothing is dropped between updates. The first draft's variance-proportional split dropped the cross-covariance after each update, which treats every repeat as fresh information and lets ability's variance fall without a floor. Under the joint update, repeats of one item pin the sum and leave ability's variance floored near `v_s·v_e/(v_s+v_e)`.

**The fixed residual becomes a per-prediction one.** The six `(A·τ₀)²` sites take the residual variance of what is not yet in the state: `τ₀²` for a new item of a new family and for a generation point with no item (as today), `(1−ρ)τ₀²` for a new item of a practised family, 0 for a practised item. `F_x`'s cached inverse is keyed by that variance.

**Cost.** The bank grows by one coordinate per attempted item and one per family, so each update costs more. At today's sizes this is expected to be cheap; ADM0 measures cold rebuild, cache-hit input construction and Next latency. If it is not, an approximation is allowed only after it is tested against this exact joint as the reference (§9).

**The rules that complete it:**
- **The split `ρ`** joins the subject view's hyperparameter grid, its support the smallest set the planted simulation tells apart (ADM0), from uniform weights. LO views take one pre-registered value, as they do for their other hyperparameters (`LO_VIEW_POINT`).
- **A singleton group** (`item:<id>`, where the surface group is the item) gets one effect, `e_i ~ N(0, τ₀²)`, and no family term; the report keeps these apart.
- **Drift.** Both effects take the cells' variance drift per day since their last update, so familiarity absorbed during massed practice does not stay certain forever. No new constant.
- **Both views** carry their own effect coordinates.

**What this does, with no further rule:**
- A novel family: both effects are at their priors, so the shared state takes the share it takes today. This is the clean measurement of transferable ability.
- A repeat by a learner whose ability is well measured: the effects take most of the update. This is the owner's "repeated successes can primarily update item memory or family proficiency when the explanations fit".
- A repeat predicted to succeed moves little anywhere.
- Answers on one item share `e_i` and those on one family share `e_F`, which is the dependence.

### 4.3 Memory: one curve, learned by one owner

**The owner's equation has a closed form, and FSRS is one of its members.** With `τ(m, z) = T(z)·m^(−κ)`:

```
dm/dt = −m / τ(m, z)      ⇒      m(t) = m₀ · (1 + κ·t·m₀^κ / T(z))^(−1/κ)
```

It is exponential as `κ → 0` and a power law otherwise. The curve this codebase uses, `R = (1 + f·t/S)^(−d)`, is the member with `m₀ = 1`, `κ = 1/d` and `T = S/(f·d)`. So the learned decay is not a new memory state: it is the one retrievability function, read at an effective stability.

**At ADM2a, memory is plain FSRS.** `m_I` and `m_F` are `retrievability(S, t, weights)` through RE2's function, with `S` from a pure fold:

- `memory_fold(attempts, weights)`: FSRS's own `apply_review`, with the live rating rule (`fsrs_rating_for_attempt`), over the graded attempts AD's material view admits, keyed by item and by surface group. For each serve it returns the state from reviews that happened strictly before the serve, with today's corrections (AD's own time policy, EP0t's `ad_replay` preset). It runs inside `load_events`, so the events fingerprint covers it.
- **Weights:** the FSRS-6 defaults, their digest in `ad_state`'s versions. AD's guard denies `fitted_parameters`, a refit would otherwise change AD's state with no tag, and a fit over every review is a global aggregate whose protection has not been argued. Reading the vault's fitted set is ADM3's question.
- `family_memory_state` is left as it is: it is retrospective, keyed to authored families and rebuilt only, so it cannot give retrievability as of a historical serve.

**At ADM3 (owner, Nov 17 2026):** "AD alone at ADM3. AD's calls pass S_eff to RE2's one function and every other caller keeps regular S. After ADM3's report we can see if plain FSRS stability vs S_eff is better for the scheduler, router's rollouts, or delayed checks." So:

| | ADM3 |
|---|---|
| What is learned | the weights `w` in `S_eff = S·exp(wᵀu)` (`spec_learned_parameters_v1.md` §4.6), latent with prior N(0, s²), the width `s` a grid posterior on LP's support |
| By whom | RE8's model, the one owner of the fit. It is a pure function over reviews: RE8's replayer runs it for its own state, and AD's fold runs the same function over the reviews AD's material view admits, so AD reads no table it is denied |
| From which likelihood | the review outcome FSRS itself fits (`rating != AGAIN`), prequentially: each review is predicted from the state before it, then updates `w` |
| Inputs `u` | RE8's (lesson exposure, the confidence tap or hedge, surprise, effort) and, from EP0's attempt facts, the highest hint level, whether the answer was shown, help before or after work. The first draft's other two inputs are dropped: the gap and the success count are what FSRS already sees, and a count is unbounded inside an exponential |
| What stays plain | FSRS's own state, updates, due dates and fitted weights (RE8 item 1); the shape `d`, which stays FSRS's weight 20, so the read curve has the shape FSRS's update uses; every caller of the retrievability function but AD |
| Who reads `S_eff` | AD alone: its calls pass `S_eff` into the one function (no second read function; `tests/test_one_retrievability.py` still holds the line) |
| The report | for each of the scheduler, the router's rollouts and the lesson's delayed checks, plain `S` against `S_eff` on the outcomes each predicts, beside AD's own; the owner decides the wider reach from it |

**No outcome is its own feature.** For each attempt: predict from the state before it; update AD; then append the review to the fold (and to RE8's fit) for the next attempt.

**Exposure without an answer** (a reveal, a reading or lesson opportunity) doesn't update an FSRS state today and doesn't here. It stays in warmth (§4.5) and the reading dose curves.

### 4.4 How memory enters the predictor

```
η = [shared terms, as today] + e_F + e_i + ζ_I·x_I + ζ_F·x_F + [warmth]
x_K = logit(m_K) − m̂      for a practised key K, else 0
```

- `m̂` is AD's own predictive mean logit for the item without the memory terms, frozen at the serve. With `ζ_I = 1` the prediction sits at FSRS's `logit R`; with `ζ_I = 0` at AD's novel-item prediction. This is the router combiner's form (`aR·(logit R − η)`), so the two can be compared directly, and it avoids adding `logit R` on top of ability and `e_i`, which both already summarize the item's history. Because `m̂` is a number fixed at the serve, the predictor stays linear in the state and the filter doesn't change.
- `ζ_I` and `ζ_F` are latent coordinates of each view, like `ζ` today.
- **Priors** (versioned, `ad_priors_v2`):
  - `ζ_I ~ N(0.5, 0.25)`. Basis: the router combiner's labelled seed for how far FSRS memory moves a prediction (`router_objective/memory.py:45-46`), so AD and the router start from the same assumption. ADM0 reports sensitivity at a quarter and four times the variance.
  - `ζ_F ~ N(0, 0.25)`. Basis: no published value says how much a family's memory carries to its other items; zero-centred shrinkage, same width.
  - A singleton group has no `x_F`: its family memory is its item memory.
- **Delayed performance teaches retention** through `ζ_I` and `ζ_F` (how much memory matters to the prediction) at ADM2a, and through `w` (how fast it fades) at ADM3.

### 4.5 Warmth as a learned basis (its own step, ADM2b)

A decay constant can't be a coordinate of a linear filter. AD's answer for reading dose is a basis: fixed scales, learned weights.

```
ζ·exp(−Δh/6)   →   Σ_k ζ_k·exp(−Δh/h_k)
```

- **Scales:** a short geometric ladder containing 6 hours; ADM0 picks span and count as the smallest set the planted simulation recovers.
- **Priors:** the 6-hour weight keeps today's N(1.0, 0.25); the others N(0, 0.25). Signed weights are intended: a recent exposure may help or interfere, and the report shows the implied curve rather than forcing it monotone.
- **Not equal to today at the prior.** The means are equal, but each added scale contributes `0.25·w_k²` to the predictive variance on a recently exposed learning object, so `p̄`, `P_band` and the update gain change from the first day, for novel items too. ADM0's prior-predictive check computes that change for a fresh item on a recently exposed topic; the shadow report shows it.
- **Separate from repeats.** This changes first-surface predictions on its own, so it is its own successor (ADM2b), after ADM2a, so each effect can be attributed.
- **Scope:** warmth stays the short-term effect of any recent exposure to the learning object; item and family memory are separate terms, so a repeat no longer leans on warmth.

### 4.6 What is predicted, and for whom

| Question | Answer | Read by |
|---|---|---|
| An unseen item of an unseen family, or a generation point | The shared terms alone (`p̄`), residual `τ₀²`, as today | The band draw, the generation contract, the router's objective (`η_L`), readiness |
| An unseen item of a practised family | Shared terms, `e_F`, `ζ_F·x_F`, residual `(1−ρ)τ₀²` | The band draw, when it draws from a practised family |
| A practised item | All terms, no residual | A forecast receipt for the repeat; the stratified report (§9) |

Each holds in both views. AD still serves only never-attempted items. The router's objective still reads the unseen-item prediction, so its target (cold performance at the goal date on questions you haven't drilled) stays the transferable part. Repeats now move that prediction only through measurement, never through extra `γ`.

### 4.7 The owner's mechanisms, and where each lives

| The owner's words | In this design |
|---|---|
| "repeated surface families train the predictive posterior" | §4.1: repeats measure |
| "repeated successes can primarily update item memory or family proficiency when the explanations fit" | §4.2's joint update, with §4.4 making a practised success unsurprising |
| "delayed performance can teach the model about retention" | §4.4's `ζ_I`, `ζ_F`; §4.3's `w` at ADM3 |
| "novel family performance can better distinguish transferable knowledge from familiarity" | §4.2: a novel family's effects are at their priors, so ability takes the update; §4.6 makes the gap a number |
| "shared latent family/item effects account for dependence" | §4.2's `e_F`, `e_i` |
| "the fixed 6 hour warmth delay to a learned decay" | §4.5 |
| "exposure dependent memory states with adaptive retention" | §4.3: FSRS states per item and family from the fold; `S_eff` from how each exposure went |
| "dm/dt = −m/τ(m,z)" | §4.3's curve; FSRS-6 is the member it starts from |

## 5. Data and identifiability

State this plainly in the as-built notes.

- The largest vault holds on the order of a hundred graded attempts (near 110 once rebuild copies are removed, by the rebuild fix's counts of Nov 15), and RE8 counted at most 19 same-item repeats. Every new term will sit near its prior for months. The priors are therefore the design.
- `ρ` and the width `s` are grid posteriors; with little data their weights stay near uniform, and the report says so rather than naming a winner. Prior sensitivity is reported for every new prior.
- `e_F` and `e_i` are separable only where a family has more than one attempted item; elsewhere the split is the prior's.
- `ζ_F` needs attempts on unseen items of practised families. The band draw produces those only by chance (Q5). One novel answer cannot establish separation for one learner; the report gives effective counts of distinct siblings and delays.
- At long delays both memory terms tend to zero while the effects and transferable learning persist, so a late success has several explanations. The report labels the retention fit observational, except on randomized checks (RO5), whose delay source is recorded (EP0's `delay_source`) and reported apart.

## 6. Alternatives considered, not chosen

- **A memory state owned by AD** (a decaying trace per item and family, its own time constants on the grid). The owner's equation most literally; the fifth forgetting model in the system, with no population prior and too little data.
- **Keeping D10 and reading only FSRS for repeats.** The cheapest. It leaves AD blind to most of a returning learner's data and can't separate transfer from familiarity.
- **The first draft's variance-proportional split with covariance dropped.** No variance floor; drilling would make ability overconfident, only slowly (§4.2).
- **`γ` on every repeat, or a learned repeat-transfer coefficient.** The first inflates readiness from drilling; the second has nothing to fit it yet (§4.1). Reconsider after ADM2a's report.
- **`logit R` added straight to the predictor.** Stacks FSRS's item history on ability and `e_i`, which already carry it (§4.4).
- **Reading or re-keying `family_memory_state`.** It is retrospective and keyed to authored families; a fold as of each serve is what a replay needs.
- **A decaying item effect.** Mixes what is stably easy about an item with what was recently practised, with no curve to start from.
- **Learning `h_w` on the grid** instead of a basis. Each grid dimension multiplies every replay's cost, and the grid gains `ρ`.
- **A neural liquid-time-constant cell.** Dropped by the owner on Oct 24 (LP6).

## 7. Build order

| Step | What | Track |
|---|---|---|
| **ADM0** | Read-only, in this order. (1) A pre-registration, committed before any vault copy is read: the priors and their bases, `ρ`'s support and the warmth ladder as candidates, the event, the strata of §9, the metrics (prequential log loss, Brier, calibration, interval coverage), the baselines (plain FSRS `R` on repeats, a running success rate from a versioned seeded prior over past outcomes only, the last outcome, the predecessor, `mastery_ekf`), the time boundary and the label-closure date with the resolver's version. (2) The planted simulation (`sim/ad_synthetic`) gains repeats, families, delays, a planted retention curve and the `γ` rule; it fixes the grid supports, runs the prior-predictive check of §4.5, checks any approximation against the exact joint and the variance floor, and measures replay and Next-path cost. (3) On backup-API copies, counts of repeats by stratum and by today's eligibility outcome (`repeat_surface`, primed, primed unbound, pre-exposed, held). The pre-registration and simulation results are tracked; the vault counts stay in a gitignored local report. | none |
| **ADM1** | Structure. L4 for AD: the per-attempt update callable with plain values, returning its record (L6). Eligibility as a pure function returning the three answers of §4.1 with reasons (the predecessor's values: measure and learn both follow D10). `memory_fold` as a pure function with its tests, not yet read by replay. No value changes (AST identity, the gate). | structure |
| **ADM2a** | The successor: §4.1, §4.2, §4.4 with plain FSRS memory at default weights; the fold inside `load_events`; `item_serve_inputs` at every presentation; repeat receipts with the three category probabilities beside EPp's predecessor receipts. One tag. | behaviour, lands alone, no kill switch |
| **ADM2b** | §4.5's warmth basis. One tag. After ADM2a's report. | behaviour, lands alone, no kill switch |
| **ADM3** | §4.3's `S_eff`, read by AD alone, under RE8's tag; needs RE8's model and EP0's facts; whether AD's fold reads the vault's fitted weights is decided here with the protection argument for `fitted_parameters`. | behaviour, lands alone; no switch unless the owner asks (RE8's text predates the Nov 16 rule) |
| **ADM4** | Help as an effect: the outcome category's "any help before work is a 0" becomes covariates with learned effects, separating forecasting before help from reading an answer after it. Only if the owner wants it after ADM2a's report. | behaviour |

**Can start now:** ADM0, beginning with the pre-registration, and ADM1, beside the refactor's other lanes. EPp (in the evidence-packets spec) should start now too, so ADM2a has prospective predecessor repeats to compare against. ADM2a waits for ADM1 and the owner's read of ADM0.

## 8. Persisted meaning

- **ADM2a** changes `ad_state`, `ad_attempt_trace` and every number read from them (the band draw's support, forecasts, readiness labels' inputs, the router's `η_L`), and which repeats `item_forecast_scores` scores (the score's interpretation version goes in its detail). A successor under the playbook: a new tag, a row in `ops/upgrades.py` (`whole_vault_rebuild`), a test row; priors `ad_priors_v2`, hyperparameters `ad_hyper_v2`. No kill switch (owner, Nov 16). The predecessor stays a replay arm at its tag, its state hash pinned on the head fixture; undoing the successor after an upgrade is a follow-up successor.
- **No new table.** The effects are bank coordinates, so they are in the state hash; `ad_state` may gain a summary part per view in its existing `(view, part)` rows (`replay.py:929-938`), and each trace row's `detail_json` records the three eligibilities with reasons and the memory inputs.
- **Identities.** The events fingerprint covers the fold and its weights digest; `ItemSpec` gains the surface-group key and its source, versioned; selection receipts' state hashes change. K0's pins move deliberately in the landing commit.
- **The router's combiner** joins frozen `η` values from traces across the tag, so its rows mix two definitions of `η`. ADM2a's step 0 decides, with the router's owner, whether the fit uses post-tag rows only or carries the AD tag as a covariate, and the shadow report shows both.
- **Cost and upgrade.** Cold rebuild, cache-hit input construction, storage growth and Next latency are benchmarked at step 0. The landing tests a predecessor-to-successor upgrade and a second, idempotent rebuild including `item_forecast_scores`.
- **A2 holds:** nothing here writes evidence, mastery, facet recall, FSRS state or certification. AD reads no new table at ADM2a: the fold reads attempts through the material view and uses default weights.
- **The shadow rebuild's report before landing** (playbook): on each owner copy, the deltas in the band draw's support, in `p̄` per learning object, in readiness labels and in the router's chosen block at recorded decisions, with numeric policies compared on frozen candidates and seeds. A shadow rebuild cannot say what a model would have answered on a changed packet; the report says so.
- **ADM2b** and **ADM3** are their own successors, each with its tag, upgrade row and test row.

## 9. Tests and the report

**Tests** (with fakes and the planted simulation; no vault):
- With no repeat in the ledger and no warmth change (ADM2a), every prediction for a novel item of a novel family equals the predecessor's in mean and variance. At ADM2b, means are equal and the variance changes by exactly the computed amount.
- The predecessor arm: `ad_state` and `ad_attempt_trace` from the predecessor replay arm equal the pinned predecessor state on the head fixture.
- **`γ`:** many predictable repeats of one item, successes and failures, leave untouched cells and novel families' predictions where they were, apart from the measurement update; the number of `γ` increments equals the number of distinct surface groups first met.
- **Variance floor:** over long same-item runs, ability's variance stays at or above the joint model's floor, and an unseen sibling's variance shrinks only with family evidence.
- **Any approximation** of §4.2 agrees with the exact joint on same-item, sibling and novel-family sequences in predictive loss and interval coverage.
- **Planted recovery:** a learner with high ability and no memory, and one with low ability and heavy drilling, produce the same repeat successes; the model separates them once each answers a novel family.
- **The fold:** identical outputs when protected reviews are removed entirely, and when a review is appended after the cutoff; the weights digest is recorded.
- An auto-primed repeat is not measured and is counted; help before work scores 0.
- Upgrade from the predecessor, then a second rebuild, is byte-identical.
- A2's guard: no AD module writes a table outside its own.

**The report** (`learnloop ad report`, extended; read before ADM2a, ADM2b and ADM3 land, and monthly after). Prequential log loss, calibration and interval coverage, predecessor beside successor, against the pre-registered baselines, in both views, with counts of eligible, issued, answered, resolved, missing, unbound and censored rows, by stratum:

| Stratum | What it shows |
|---|---|
| First surface | No worse than today |
| Repeat, same item (frozen, historical inputs apart) | The case AD couldn't predict at all, against plain FSRS and the running rate |
| Unseen item, practised family; singleton groups apart | Whether a family effect exists |
| Novel family after drilling another | Transfer against familiarity |
| By delay bucket, natural and randomized checks apart | Retention; plain `S` beside `S_eff` at ADM3 |
| By help facts | Input to ADM4 |

No gate rides on it (owner, Oct 24). Only aggregate results reach a tracked file.

## 10. Rules this amends

- **D10** ("first graded attempt per surface group only; repeats stay FSRS's"): reversed for measurement; kept for the transferable increment. FSRS keeps scheduling repeats.
- **§5.5's `h_w`:** becomes a basis with learned weights (ADM2b).
- **§5.6's "no mean decay; forgetting stays with FSRS":** still true of the shared state. Forgetting enters through a term that reads FSRS's curve.
- **A3's kill switch:** superseded for these successors by the owner's rule of Nov 16; the predecessor is a replay arm instead.
- **RE8:** its first consumer becomes AD alone, through the one function; the scheduler, rollouts and delayed checks keep plain `S` until ADM3's report (owner, Nov 17; noted in RE8). Its "it learns from same-item reviews, so it doesn't speak to transfer" is why §4.2 exists beside it.
- **The open item on AD's unbounded learning increment** (strategy decision 13) is untouched, and §4.1's learn rule keeps repeats from making it worse.

## 11. Decisions for the owner

**Decided:** Q2, the reach of `S_eff` (owner, Nov 17 2026): AD alone at ADM3, through the one function; every other caller keeps plain `S`; ADM3's report compares the two for the scheduler, the router's rollouts and the delayed checks, and the owner decides the wider reach from it (§4.3).

**Open:**

| # | Question | Recommendation |
|---|---|---|
| Q1 | Reverse D10 for measurement, keeping the transferable increment once per family (§4.1)? | Yes. It is what you asked for, without drilling inflating readiness. |
| Q3 | `ζ_F` centred at 0, so a family's memory carries nothing to its other items until the data show it? | Yes. |
| Q4 | Which "family" do the effects and the memory fold use: AD's surface group, or the authored `family_id`? | AD's surface group, versioned and resolved per revision, for both; `family_memory_state` left as it is. |
| Q5 | Should the band draw prefer an unseen item of a practised family when that prediction is most uncertain? | Not in this spec; after ADM2a's report, as a randomized draw with a logged propensity. |
| Q6 | ADM4 (help as a learned effect, not a 0)? | Decide after ADM2a's report by help facts. |
| Q7 | An auto-primed repeat (within the display coverage of its own answer) is not measured (§4.1)? | Yes: the display was of the very answer asked for. |
| Q8 | The warmth basis as its own successor after ADM2a (§4.5)? | Yes, so each change's effect can be seen. |

## 12. Checked, and not checked

**Checked by me at main `88b10fb90d` (2026-11-17):** every path:line in §3, including the learning transition and its prior, the eligibility chain and where the surface is taken, the six residual sites, the bank's lazy coordinates, the projection's warmth coordinate, the LO views' fixed point, the serve hook's never-attempted gate and `p_categories: None`, the outcome categories and reveal coverage, the scorer, the combiner's form and prior, the one retrievability function, FSRS's fit target, `review_log.py`'s header, `family_memory_state`'s schema and its rebuild-only writer, AD's denials of `practice_item_state` and `fitted_parameters`, the fitted weights' kept history, the events fingerprint and `ItemSpec`; RE8, LP §4.6 and the playbook's rules of 2026-11-04 and 2026-11-16.

**Not checked:**
- The update's cost with effect coordinates and the larger grid; the router's speed target is unmet (refactor F2), and ADM0 measures.
- That the joint update's variance floor and the warmth basis's variance change hold numerically as derived here; ADM0's simulation is their check.
- The plan engine's hook reaching repeats served by the ordinary plan (`daily_plan/engine.py:5984`), from a review, not re-read.
- `sim/ad_synthetic`'s present contents.
- The vault counts (110 attempts, 19 repeats), which are earlier steps' figures; ADM0 recounts them.
- No test was run and no vault was read.

# Adaptive difficulty, memory and families (ADM): repeats train the model, and decay is learned

**Status:** draft, Nov 16 2026, for the owner's review. Not queued. Evaluated in `docs/reviews/refactor-strategy-v3-audit-2026-11-16.md` §4.1.

**Depends on:** RE2 (one retrievability function; landed). L4's review for adaptive difficulty (refactor strategy §2.18), so the update can be called with plain values. `spec_evidence_packets_v1.md` §3 (attempt facts) for ADM4 only.

**Amends:** `spec_adaptive_difficulty_v1.md` D10 and §5.5's fixed `h_w`. It builds `spec_learned_parameters_v1.md` §4.6 and `spec_recognition_and_effort_v1.md` RE8 rather than adding a second memory model beside them.

## 1. The owner's words (Nov 16 2026, verbatim)

> adaptive difficulty should have repeated surface families train the predictive posterior. Repeated successes can primarily update item memory or family proficiency when the explanations fit. delayed performance can teach the model about retention, novel family performance can better distinguish transferable knowledge from familiarity, shared latent family/item effects account for dependence. Another change I want to make in AD is to change the fixed 6 hour warmth delay to a learned decay, and missing item/family memory within AD to an exposure dependent memory states with adaptive retention (the former can perhaps be some sort of LTC-adjacent formulation such as dm/dt = −m/τ(m,z)

Standing rules that bind this spec: no point-fitted or hand-set hyperparameters, and every effect that weighs an observation is latent state with an a-priori, versioned prior (AD's A5; owner, Oct 24). AD is derived and replayable with no model call (A1) and never writes evidence, mastery, FSRS state or certification credit (A2). A change to what AD computes is a successor with a kill switch that restores the predecessor exactly (A3, the playbook).

## 2. In plain words

Today adaptive difficulty learns only from the first time you meet each kind of question. Every repeat is thrown away, it has no forgetting, and it treats "you practised this topic recently" with one fixed six-hour constant.

After this spec:

1. **Every graded attempt trains the model**, first or repeat.
2. **The model has three places to put what an answer shows:** your transferable ability on the topic, your familiarity with this family of questions, and your memory of this exact item. A success on something you've drilled mostly moves the last two. A success on a family you've never seen moves ability.
3. **Memory fades along one learned curve.** It starts as the curve the scheduler already uses and learns how you differ from it. Delayed answers are what teach it.
4. **The six hours is learned** as a weighting over a few time scales.

What the learner sees: nothing new on a screen. Predictions for practised material stop being blind, the 70-80% band is drawn with better numbers, and "ready on unseen questions" is separated from "good at the ones you've drilled".

## 3. What the model does today (checked against the code)

| Fact | Where |
|---|---|
| The predictor: `η = Σ_f w̃ θ_{f,k} − β·φ(x) − α·z − ε_i + ζ·w`, a graded logistic with a guess floor and a lapse | spec §5.4; `adaptive_difficulty/model.py:68`, `state.py:109` |
| Trains only on the first graded attempt per surface group; a repeat is excluded with reason `repeat_surface` | `replay.py:466-476`; D10: "repeats stay FSRS's" |
| A surface group is the first of `shared_stimulus_id`, `source_family`, `solution_recipe_family`, `surface_family`, else the item | `replay.py:263` |
| The item residual `ε_i ~ N(0, τ₀²)`, `τ₀ = 1`, is integrated out inside each attempt's update and never stored | `priors.py:36`; spec §5.6 |
| No forgetting of the mean; variance drifts 0.01 a day | `model.py:479`; spec: "forgetting stays with FSRS" |
| Warmth: `w = exp(−Δh / 6)`, Δh the hours since the last exposure to the learning object (an attempt, a reveal, a reading or lesson opportunity), 0 with none. Nothing inside six hours is dropped. `ζ` is learned, prior N(1.0, 0.25); the 6 is `WARMTH_HOURS`, fixed | `replay.py:306`, `serving.py:132`, `priors.py:38`, `:143` |
| Nonlinear hyperparameters are learned as a grid posterior: 36 points mixed by marginal likelihood | spec §5.6 (`W_t(ξ) ∝ W_{t−1}(ξ)·Z_t(ξ)`) |
| Reading dose uses two fixed scales with learned weights: "a basis, not a shape" | `priors.py:41` |
| AD serves only never-attempted items | `serve_inputs.py:62` |
| The router's objective combines AD's prediction for an unseen item with FSRS retrievability: `logit P = a0 + aA·η + aR·(logit R − η)·[practiced]`, fitted | `router_objective/memory.py:12` |
| The retrievability curve is FSRS-6's, `R = (1 + f·t/S)^(−d)`, `d = weights[20]`, `f` set so `R(S) = 0.9` | `scheduling/fsrs.py:58-64` |
| An FSRS state per item, family and learning object is already projected and nothing serves from it | `scheduling/family_memory_model.py:43` ("a point predictor, never active"); table `family_memory_state` |
| Help changes the outcome category, never the eligibility; pre-exposed attempts are excluded | `outcomes.py:87` |

So three of the owner's phrases need restating before the design. The six hours is a decay scale on a covariate, not a delay or a window. AD doesn't have a gap where item and family memory should be: it has a rule (D10) that keeps repeats out. And a family memory does exist, unused, keyed differently from AD's surface group (§11 Q4).

## 4. Design

### 4.1 Every graded attempt trains (D10 reversed)

The `repeat_surface` exclusion goes. Every other exclusion stays: attempt type, held grades, unassessed grades, zero mass, pre-exposure, missing frozen inputs. The outcome categories and the forecast event (`unassisted_success`) are unchanged.

This can't land alone. If a repeat trains and the model is otherwise as today, the item residual is integrated out afresh each time, so five successes on one familiar item count as five independent measurements of ability and the posterior becomes overconfident. §4.2 and §4.3 are what make §4.1 safe, and the three land as one successor.

### 4.2 Family and item effects

The residual that today is integrated out and forgotten becomes two stored effects:

```
ε_i  →  −(e_F + e_i)
e_F ~ N(0, ρ·τ₀²)        one per surface group, shared by its items
e_i ~ N(0, (1−ρ)·τ₀²)    one per item
```

Positive means easier for this learner than the model's shared terms say. Their prior variances sum to today's `τ₀²`, so the prediction for a never-seen item of a never-seen family is exactly today's.

**The split `ρ`** isn't set. It joins the hyperparameter grid, whose support is the smallest set the planted simulation can tell apart (step ADM0 measures it), from uniform weights.

**The update.** For an attempt on item `i` of family `F`, with the shared part `s ~ N(μ_s, v_s)` from the filter bank and the two effects at `N(m_F, v_F)` and `N(m_i, v_i)`:

1. The total is `η ~ N(μ_s + m_F + m_i + M, v_s + v_F + v_i)`, with `M` the memory and warmth terms of §4.4 and §4.5.
2. The existing quadrature gives the posterior mean and variance of `η`.
3. Each part takes its share of the shift in proportion to its variance: part `c` moves its mean by `(v_c / v)·Δμ` and its variance to `v_c − (v_c/v)²·(v − v′)`.

For the shared state this is today's update with one change: where it integrated out `τ₀²` around zero, it integrates out the two effects' current variances around their current means. The effects are stored per grid point in a DERIVED table rebuilt by AD's replayer. Covariance between an effect and the shared state is dropped after each update; that approximation is stated in the record and measured by the simulation.

**What this does, with no further rule:**
- A novel family: both effects are at their priors, so the shared state takes the share it takes today. This is the clean measurement of transferable ability.
- A repeat by a learner whose ability is already well measured: `v_s` is small beside `v_F + v_i`, so the family and item effects take most of the update. This is the owner's "repeated successes can primarily update item memory or family proficiency when the explanations fit".
- A repeat that was predicted to succeed moves little anywhere, because the surprise is small.
- Repeated answers on one item share `e_i` and those on one family share `e_F`, which is the dependence.

### 4.3 Memory: one curve, learned

**The owner's equation has a closed form, and FSRS is one of its members.** With `τ(m, z) = T(z)·m^(−κ)`:

```
dm/dt = −m / τ(m, z)      ⇒      m(t) = m₀ · (1 + κ·t·m₀^κ / T(z))^(−1/κ)
```

It is exponential as `κ → 0` and a power law otherwise: the time constant grows as the trace fades, which is what makes old memories fade slowly. The curve this codebase already uses, `R = (1 + f·t/S)^(−d)`, is the member with `m₀ = 1`, `κ = 1/d` and `T = S/(f·d)`.

So the learned decay isn't a new memory state. It is the one retrievability function (RE2), given two things to learn:

| Learned | Form | Starts at |
|---|---|---|
| The shape `d` | already FSRS-6's weight 20 | the vault's fitted or default weight |
| The time constant's dependence on how the memory was made | `T(z) = S·exp(wᵀz) / (f·d)`: `S_eff = S·exp(wᵀz)` | `w = 0`, which is plain FSRS |

The second row is `spec_learned_parameters_v1.md` §4.6 ("liquid stability") and RE8, unchanged in form: the weights `w` are latent with prior N(0, s²), and the width `s` is a grid posterior. This spec adds to RE8 only its inputs `z` (below) and its first reader (AD).

**Inputs `z`, each derived from ledgers at the review that set the state** (RE8 item 3; none is a judgment):
- how the last answer was produced, from the attempt facts of `spec_evidence_packets_v1.md` §3: the highest hint level, whether the answer was revealed, help before or after work;
- the gap since the previous exposure, as retrievability at that review (the spacing effect);
- the count of earlier unassisted successes on the key;
- RE8's own inputs (lesson exposure, the confidence tap, surprise, effort) as RE8 adds them.

**Keys.** The curve is read for the item and for its family. The family state comes from the existing projection (`family_memory_state`), which this spec makes read rather than idle.

**Exposure without an answer** (a reveal, a reading or lesson opportunity on the learning object) doesn't update an FSRS state today and doesn't here. It stays where AD already has it: warmth (§4.5) and the reading dose curves.

**Read side only** (RE8 item 1). FSRS's own states, updates and due dates don't change. Whether the scheduler and the router's rollouts move to `S_eff` is a later decision with its own replay report (§11 Q2).

### 4.4 How memory enters the predictor

```
η = [shared terms, as today] + e_F + e_i + ζ_I·m_I + ζ_F·m_F + Σ_k ζ_k·w_k
```

- `m_I` and `m_F` are the retrievability of the item's and the family's memory state at the serve, from §4.3's curve, and 0 for a key never practised.
- `ζ_I` and `ζ_F` are latent coordinates of the filter, like `ζ` today. The predictor stays linear in its state, so the filter doesn't change.
- **Priors** (versioned, `ad_priors_v2`):
  - `ζ_I` is centred so that, for a learner at even odds on a novel item, a repeat at retrievability 0.9 is predicted at 0.9. The basis is published: it is what FSRS's `R` means. Its variance is wide.
  - `ζ_F` is centred at 0 with the same variance. No published value says how much a family's memory carries to its other items, so the data must show it.
  - ADM0 computes both numbers and records them; nothing is hand-set per item, topic or family.

**Delayed performance teaches retention** through two routes: `ζ_I` and `ζ_F` (how much memory matters to the prediction) are updated by every repeat, and `d` and `w` (how fast it fades) by the prequential fit of §4.3. A repeat after a long delay that succeeds where the curve said it would fail is the evidence for a longer time constant.

### 4.5 Warmth as a learned basis

A decay constant can't be a coordinate of a linear filter. AD's own answer for reading dose is a basis: fixed scales, learned weights.

```
ζ·exp(−Δh/6)   →   Σ_k ζ_k·exp(−Δh/h_k)
```

A weighted sum of exponentials at spaced scales is a learned decay curve, and it can take a power-law shape if the data ask for one.

- **Scales:** a short geometric ladder containing 6 hours. ADM0 picks its span and count as the smallest set the planted simulation recovers.
- **Priors:** the 6-hour weight keeps today's N(1.0, 0.25). The others are centred at 0 with the same variance. At the prior this is today's model exactly.
- **Scope:** warmth stays what it is, the short-term effect of any recent exposure to the learning object, another item's included. Item and family memory (§4.4) are separate terms, so a repeat no longer leans on warmth to explain itself.

### 4.6 What is predicted, and for whom

| Question | Answer | Read by |
|---|---|---|
| An unseen item of an unseen family | The shared terms alone (`p̄`), as today | The band draw, the generation contract, the router's objective (`η_L`), readiness |
| An unseen item of a practised family | Shared terms, `e_F`, `ζ_F·m_F` | The band draw, when it draws from a practised family |
| A practised item | All terms | A forecast receipt for the repeat; the stratified report (§9) |

AD still serves only never-attempted items. The router's objective still reads the unseen-item prediction, so its target (cold performance at the goal date on questions you haven't drilled) is the transferable part by construction. Its combiner's `aR` term and §4.4 now both describe how FSRS memory moves a prediction; the report shows them side by side, and merging them is Q2.

### 4.7 The owner's mechanisms, and where each lives

| The owner's words | In this design |
|---|---|
| "repeated surface families train the predictive posterior" | §4.1 |
| "repeated successes can primarily update item memory or family proficiency when the explanations fit" | §4.2's variance-proportional split, with §4.4 making a practised success unsurprising |
| "delayed performance can teach the model about retention" | §4.3's `d` and `w`; §4.4's `ζ_I`, `ζ_F` |
| "novel family performance can better distinguish transferable knowledge from familiarity" | §4.2: a novel family's effects are at their priors, so ability takes the update; §4.6's three predictions make the gap a number |
| "shared latent family/item effects account for dependence" | §4.2's `e_F`, `e_i` |
| "the fixed 6 hour warmth delay to a learned decay" | §4.5 |
| "exposure dependent memory states with adaptive retention" | §4.3: FSRS states per item and family, with `S_eff` depending on how each exposure went |
| "dm/dt = −m/τ(m,z)" | §4.3's curve; FSRS-6 is the member it starts from |

## 5. Data and identifiability

State this plainly in the as-built notes.

- The largest vault holds on the order of a hundred graded attempts (the rebuild fix's counts of Nov 15 put it near 110 once rebuild copies are removed), and RE8 counted at most 19 same-item repeats. ADM0 counts them properly. Every new term will sit near its prior for months. The priors are therefore the design, and §4.2-§4.5 choose each one so that the prior is today's model (effects, warmth) or plain FSRS (the curve).
- `ρ`, `d` and the width `s` are grid posteriors. With little data their weights stay near uniform, and the report says so rather than naming a winner.
- `e_F` and `e_i` are separable only where a family has more than one attempted item. Elsewhere the split is the prior's.
- `ζ_F` needs attempts on unseen items of practised families. AD's band draw produces those only when it draws from a practised family, which today is by chance. Nothing here steers serving to produce them (Q5).
- Nothing randomizes delay. The retention fit is observational: items that come back late differ from items that come back early. The report labels it so.

## 6. Alternatives considered, not chosen

- **A memory state owned by AD** (a decaying trace per item and family, with its own time constants on the grid). It follows the owner's equation most literally. It would be the fifth forgetting model in the system (FSRS per item, per family, facet recall, the router's combiner), with no population prior behind it and too little data to fit one.
- **Keeping D10 and reading only FSRS for repeats.** The cheapest. It leaves AD blind to most of a returning learner's data and can't separate transfer from familiarity, which is the point.
- **A decaying item effect** (let `e_i`'s mean fade). It mixes two things, what is stably easy about this item for this learner and what was recently practised, and gives the fade no curve to start from.
- **Learning `h_w` on the grid** instead of a basis. Each grid dimension multiplies the cost of every replay, and the grid already gains `ρ`.
- **A neural liquid-time-constant cell.** Dropped by the owner on Oct 24 (`spec_learned_parameters_v1.md` LP6); nothing here revives it.

## 7. Build order

| Step | What | Track |
|---|---|---|
| **ADM0** | Read-only. The planted simulation (`sim/ad_synthetic`) gains repeats, families, delays and a planted retention curve. It measures the grid support for `ρ`, the warmth ladder, the prior centres of §4.4, and the cost of a replay at the new grid size. On backup-API copies it counts repeats per vault by stratum (same item, same family, delay bucket). One document; no `src` change. | none |
| **ADM1** | Structure. L4 for AD: the per-attempt update callable with plain values and returning its record (which parts took what share: L6). Eligibility as a pure function that returns its reason. No value changes. | structure |
| **ADM2** | The successor: §4.1, §4.2, §4.4 with plain FSRS retrievability (`w = 0`, `d` as the vault holds it), §4.5. One tag. Its switch is now the owner's call: on Nov 16 the owner decided a new successor ships without a kill switch unless asked (strategy §2.20), and this one changes every AD number, so it is the kind a switch would monitor. | behaviour, lands alone |
| **ADM3** | §4.3's learning: RE8's `S_eff` with this spec's inputs, read by AD first. One tag (RE8's), its switch `scheduling.liquid_stability.enabled`. | behaviour, lands alone |
| **ADM4** | Help as an effect: with attempt facts in place, the outcome category's "any help before work is a 0" becomes covariates with learned effects. Its own successor; only if the owner wants it after reading ADM2's report. | behaviour |

ADM0 and ADM1 can run beside the refactor's other lanes. ADM2 waits for ADM1 and for the owner's read of ADM0.

## 8. Persisted meaning

- **ADM2** changes `ad_state`, `ad_attempt_trace` and every number read from them (the band draw's support, forecasts, readiness labels' inputs, the router's `η_L`). It is a successor under the playbook: a new tag, a row in `ops/upgrades.py` (`whole_vault_rebuild`), a test row, and a kill switch `adaptive_difficulty.repeats_train` that restores the predecessor exactly (the exclusion back, the effects integrated out at `τ₀²`, one warmth scale). Priors `ad_priors_v2`, hyperparameters `ad_hyper_v2`.
- **New table:** the effects per grid point, DERIVED, with AD's replayer as its one replayer; classified in `db/table_roles.py` and in AD's two guard lists.
- **Forecast receipts** gain repeats. Their kind stays `item_unassisted_success`; the receipt already stores the item and the serve, so a repeat is distinguishable without a new kind.
- **A2 holds:** nothing here writes evidence, mastery, facet recall, FSRS state or certification. AD reads `family_memory_state` and the item's FSRS state; reading them is new and is a firewall question only if a rule I haven't found bars it (§12).
- **The shadow rebuild's report before landing** (playbook): on each owner copy, the deltas in the band draw's support, in `p̄` per learning object, in readiness labels and in the router's chosen block at recorded decisions.

## 9. Tests and the report

**Tests** (with fakes and the planted simulation; no vault):
- At the prior and with no repeat in the ledger, every prediction equals the predecessor's (the property §4.2-§4.5 were chosen for).
- With the switch off, `ad_state` and `ad_attempt_trace` are byte-equal to the predecessor's on the head fixture.
- Planted recovery: a learner with high ability and no memory, and one with low ability and heavy drilling, produce the same repeat successes; the model separates them once each answers a novel family.
- Five successes on one item move ability less than five successes on five families, by a margin the simulation fixes.
- The update's shares sum to the total shift; a share is never negative.
- A2's guard: no AD module writes a table outside its own.

**The report** (`learnloop ad report`, extended; the acceptance for ADM2 and ADM3). Prequential log loss and calibration, predecessor beside successor, by stratum:

| Stratum | What it shows |
|---|---|
| First surface | No worse than today: the successor must not cost the case AD already handles |
| Repeat, same item | The case AD couldn't predict at all |
| Unseen item, practised family | Whether a family effect exists |
| Novel family after drilling another | Transfer against familiarity |
| By delay bucket | Retention; plain FSRS beside `S_eff` |
| By help facts | Input to ADM4 |

No gate rides on it (owner, Oct 24): it is read before landing, and it runs monthly after.

## 10. Rules this amends

- **D10** ("first graded attempt per surface group only; repeats stay FSRS's"): reversed for training. FSRS keeps scheduling repeats.
- **§5.5's `h_w`** ("a fixed, versioned constant swept by the harness"): becomes a basis with learned weights.
- **§5.6's "no mean decay; forgetting stays with FSRS":** still true of the shared state. Forgetting enters through a term that reads FSRS's curve.
- **RE8:** gains inputs and a first reader. Its "it learns from same-item reviews, so it doesn't speak to transfer" is why §4.2 exists beside it.
- **The open item on AD's unbounded learning increment** (strategy decision 13) is untouched and still needs its own successor.

## 11. Decisions for the owner

| # | Question | Recommendation |
|---|---|---|
| Q1 | Reverse D10 as §4.1 describes? | Yes: it is what you asked for, and §4.2 is what makes it safe. |
| Q2 | Does `S_eff` reach the scheduler and the router's rollouts, or stay read by AD alone? | AD alone at ADM3. Decide the rest after its report, with the combiner's `aR` beside it. |
| Q3 | `ζ_F`'s prior centred at 0, so a family's memory carries nothing to its other items until the data show it? | Yes. |
| Q4 | Two definitions of "family" exist: AD's surface group, and the memory projection's `family_id` with a `same_target` or `isomorph` relation. Which one do the effects and the family memory use? | AD's surface group for both, with the projection re-keyed. It is unread today, so re-keying it costs a rebuild. |
| Q5 | Should the band draw be allowed to prefer an unseen item of a practised family when that prediction is the most uncertain? | Not in this spec. It would be the first time AD serves to learn about its own model; raise it after ADM2's report. |
| Q6 | ADM4 (help as a learned effect, not a 0)? | Decide after ADM2's report by help facts. |

## 12. Checked, and not checked

**Checked by me at main `250b0e16fe`:** `priors.py`'s constants; `replay.py`'s warmth and eligibility; `outcomes.py`'s categories; `router_objective/memory.py`'s combiner; `fsrs.py`'s curve; `family_memory_model.py`'s docstring; D10 and A1-A12 in the AD spec; §4.6 and RE8.

**From a read-only mapper, not re-read by me:** the filter's update order and quadrature (spec §5.6, `model.py`, `state.py`), where the 36-point grid is mixed, what `serve_inputs.py` freezes, the test names.

**Not checked:**
- Whether any firewall rule beyond A2 bars AD from reading FSRS state. A2 bars writing. ADM0 reads the whole of §3's rule table against §4.4.
- The cost of a replay with a larger grid and per-point effects. The router's speed target is unmet (refactor F2), and AD's state is read on that path from a cache keyed by the event fingerprint; ADM0 measures it.
- How `family_memory_state` is rebuilt and how stale it can be at a serve.
- The algebra of §4.2's split against a full joint update, beyond the standard result for a sum of independent Gaussians; the simulation is its check.
- No test was run and no vault was read.

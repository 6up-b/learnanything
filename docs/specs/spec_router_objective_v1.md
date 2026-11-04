# Router objective (RO): one objective, two policies, a dataset that can test it

**Status:** final for implementation, 2026-11-04, after independent reviews by Fable agents and an Astra Codex agent (job `20261104-044635-xuAd5U`) and an offline mechanism check (T1). Nothing here is built yet; the owner runs implementation through the queue orchestrator. No stage waits on data, calibration or sample size. Code references are to main at `9780ca3baf`. Evidence and reasoning: `reports/LearnLoop router optimization research.md` and `research_notes/LearnLoop router optimization research/` (both untracked; "the report" below). Forecasts of what a stage will do are untested unless a section says otherwise.

## 1. The owner's decisions

Verbatim, Nov 3-4 2026:

> the action router machinery should be an objective function with the LLM as a sensor. In this way, we include EIG, EVSI, VOI, etc within the larger objective function that can improve over time and can be interpretable. I think within logs we should be able to see each individual value within the action router (each sensor), the associated objective function and the ultimate output.

> I think the objective is to maximize cold performance at the goal date (with no explicit time budget, but we should penalize policies requiring long sessions for no outstanding additional marginal gain in performance).

> Some goals/quests can be broader scoped and learnloop can be a permanent instrument of habit in someone's life to broaden their forntier of knowledge.

> Definitely agree about removing the interval multiplier (include this in the spec). Spec the combined logging step, the LLM forecaster,and the revised action router form.

> Only thing is that the kill rules are too strict given our insufficient dataset. We should just fully implement the spec without any blockers like that or gates.

Agreed recommendations, Nov 4:

- **Misconception picks** (§9, item 6): a pick keeps resolving its factor, stops counting as validated evidence, and a small randomized share stays open.
- **The plan's minutes become a soft limit at RO4** (§8.2): stop is available at every reversible block boundary as an offer the learner can override, and a block with outstanding gain can run past the remembered minutes.
- **`κ` counts session minutes,** not day minutes (§8.6).
- **Undated uses** are a constant daily density per topic from enrollment, with no end. Each decision compares its actions at one shared cutoff, and a dated goal's weight is stated per topic (§3.1, §8.5).
- **The undated density** `c` is "in a config file or initialized upon goal" (owner's words): a config default copied into the goal when it's created (§8.5).
- **Embedded checks** are "something in the config" and "the check_rate default" (owner's words): randomized cold checks replace an ordinary question rather than adding one (§9, item 2).
- **Two policies, not one selector** (§8.3): a rich-history frontier LLM policy and a numeric expected-value policy, mixed by a learned weight that starts in the LLM's favor. Either can keep its influence: nothing requires the numeric policy to take over. This replaces the earlier "LLM as sensor only" and "fixed fourth component" forms. The LLM supplies both a policy proposal and calibrated forecasts, evaluated separately.

**What that last decision means here.** No stage is held back, and nothing is switched off automatically, because of an evidence threshold. Everything runs with seeded priors and learns as outcomes arrive; reports show how it's doing; kill switches are manual. "Tests" sections below are ordinary software checks (correctness, protection, predecessor behavior), not evidence gates.

Standing rules this spec follows: learned parameters with seeded priors (no made-up constants; guardrails marked `keep`); live changes behind kill switches rather than shadow stages; evidence is not mastery; design free of volume assumptions; volume doesn't replace randomization for effects.

## 2. Stages

Build in this order. Migration numbers and successor tags are claimed at landing, because FG1 and A7 are ahead in the queue. "Uses" names a code dependency, never a wait for data.

| Stage | What | Serving change? | Tag? | Learner minutes | Uses |
|---|---|---|---|---|---|
| **RO0** | Logging what is being lost (§4) | No | No, as data capture's A1 | None | - |
| **RO1** | Remove the FSRS interval multiplier; add availability time; a pick stops counting as validated evidence (§5) | Yes | Successor | None | - |
| **RO2** | Frontier LLM full-history forecaster (§6) | No | No, as AD1 | None | RO1's `received_at` |
| **RO3** | T1: the extended offline mechanism check. Ran Nov 4 (§7) | No | No | None | - |
| **RO4** | The objective, the two policies with a learned mixture, and the trace, live (§8) | Yes | Successor | Through the mixture | RO0, RO2's card, RO3's seeds |
| **RO5** | Stop coin, return model, calibration reads (§9) | Yes | Successor | Randomized offers and checks | RO0, RO4; `policy_experiment_assignments` |
| **RO6** | Learned tail, when calibration earns it (§10) | Yes | Successor | None beyond RO5 | RO0's snapshots; RO5's contrasts as they arrive |

A sensor that's missing or has failed on a decision contributes nothing to that decision's value (§8.4).

## 3. The objective

### 3.1 Three layers

| Layer | What it does | Here |
|---|---|---|
| **Objective `J`** | Defines what counts as success | Cold performance at valued uses, minus effort. Authoritative for every policy |
| **Value estimator `Q̂`** | Predicts an action's contribution to `J` | Memory models, forecasts, effect estimates, a continuation |
| **Policy** | Chooses the action | The LLM policy, the numeric policy, and the learned mix of them (§8.3) |

The objective knows nothing about learning effects. Explicit arithmetic gives an estimator no authority, and evidence decides how much each policy is followed.

### 3.2 The form

**The operational criterion is a finite, receding-horizon approximation.** At each decision, the router values actions up to one cutoff. A lifelong objective with a constant use density has infinite gross value, and subtracting a baseline doesn't repair that, so no lifelong optimum is claimed. A continuing criterion can be defined separately later (§11).

```
x_t  = (b_t, m, session state, active goals and dates, availability, pending reports)   an approximate belief state
b_t  ≈ P(z_t, θ | events with received_at ≤ t)
C    = max(t + H, latest active goal date)       fixed at the decision and carried through its rollouts
σ    = min(t + τ, C)

R(t,σ] = −∫ κ(u) du over the active minutes before σ
         + Σ_{(g,L): D_g in (t,σ]} ω_{g,L} · P(perform_{g,L} | path)     dated uses, scored at the date
         + Σ_L c_L ∫_(t,σ] P(perform_{L,s} | path) ds                    undated uses

Q^π_t(x,a; C) = E[ R(t,σ] + (V^π_σ(x′; C) if σ < C, else T_C(x′)) | x, a ]
V^π_u(x; C)   = Σ_a π(a|x) Q^π_u(x,a; C)
advantage_t(a) = Q^π_t(x,a; C) − V^π_t(x; C)
```

- `m` is active minutes in the current session.
- An action still running at `C` keeps its commitment in `x′`, and `T_C` accounts for its remaining cost and effects, so cost past `C` is neither lost nor counted twice.
- The expectation covers outcomes, durations, uptake and return, computed branch by branch, because cost and value are nonlinear in them (§8.1).
- Advantage is an interpretation: subtracting `V` doesn't change the ranking. A positive advantage doesn't mean better than stopping, which is `Q(a) − Q(stop)`, so the trace shows both.

**Which continuation.** The value estimator's `π` is the tail policy (§8.1), a model-based stand-in. It can't be the live router, since rollouts can't make LLM calls at decision time. The empirical comparison (§8.7) measures something different: **take this recommendation now, then follow the evolving live router.** RO6 learns the gap between the two from logged outcomes. Neither is a claim about running one policy indefinitely.

### 3.3 The terms

All values are in **use-equivalents**: `ω` per dated event, `c` per day, `κ` per active minute.

| Term | Meaning | Where it comes from | Learned from |
|---|---|---|---|
| `ω_{g,L}` | Weight of a dated goal's use of topic `L` at `D_g`, stated per topic | Goal contract (§8.5) | Preference: not learnable from outcomes |
| `c_L` | Daily density of undated uses of `L`, from enrollment on, with no end | Config, copied into the goal (§8.5) | Preference |
| `H` | How far undated uses are counted at a decision: at least `H`, and to the latest goal date if that's further | Config seed | **Not purely computational.** With a constant density, a lasting gain's credit grows with `H` unless `T_C` carries the rest, so changing `H` changes effective value |
| `T_C(x)` | Net continuation value past the cutoff, in use-equivalents: future valued uses, minus future study cost, and any unfinished action. The same function for every action, differing through `x′` | §8.1 | RO6 |
| `P(perform | path)` | Cold performance on the use's assessment distribution, given what the learner saw | Memory model and sensors (§8.4) | Cold outcomes |
| `κ(u)` | Attention price, rising with minutes in the session. The owner's penalty | §8.6 | Preference: frontier choices and randomized stop offers |
| `τ`, `m_a` | Elapsed time and active minutes, two clocks never blended | A3's fields; predicted per candidate (§4, row 13) | Logged durations |
| `b_t` | Belief over learner state and dynamics. `occurred_at` enters the likelihood; `received_at` sets what could be known. Today's bundle of models, not a joint Bayesian model | Mastery, FSRS, AD subject view, hypothesis posteriors | Per component |

**Why this shape for undated uses.** Lags counted from "now" would give each action a different set of uses and no single objective. Lags from a fixed date would make knowledge worthless after the last lag, the opposite of a permanent habit. A constant density fixed in calendar time counts the same uses for every action and never ends. One carried cutoff stops a stop from earning extra days of use over a block. A 7/30/90-day approximation of the integral needs weights in days, so that a constant `p` reproduces `c·H·p`.

### 3.4 What the form rules out

- **No separate term for stop, EIG, EVSI, VOI or a thoughtful question.** Information counts through what the continuation does with it. EIG and EVSI stay as sensors and in the trace. The trace may show `learning` and `information = E_o[V(b⁺)] − V(b⁻)` as parts of one value, never added twice.
- **No charge on calendar time.** Before a date, tonight's minutes displace nothing if the learner returns tomorrow anyway, so a long-run rate is a reporting benchmark, not a price.
- **Crossed dates are rewards.** A date crossed during an action is scored at the date, in `r`. Regression test: stop on the eve of an exam must not lose the exam's whole value. Cramming that adds .01 to exam performance at a block price of .02 has a continue-vs-stop advantage of −.010, not +.780.
- **The return effect sits in stop's transition,** as a distribution of return time given session minutes and availability. There is no separate additive return term. The trace shows its difference as "return effect".
- **`T_C` is not a no-study forecast, or a performance forecast.** A no-study terminal overspends (report) and gives information about dynamics no credit past the cutoff. A performance forecast leaves out future effort.

### 3.5 What it does not require

- **No learner-choice model in π for estimating `Q` from logs.** A question or hint during a block is downstream of the router's action, so the logger's `Q` (RO6) is identified from randomized decisions. Rollouts do need an emission model where a term depends on one, and §8.1 states it per action. This concerns estimating action values; the LLM policy (§8.3) is a separate role. Offer-type actions keep their uptake inside the transition.
- **No item difficulty variable.** `P(y | z, item)` must depend on the item, but nothing in the form needs a scalar difficulty. Retiring the label from the mastery path is deferred (§11).

## 4. RO0: logging

Additive receipts and columns at every version, behind `[router_objective] receipts` (default true). With the switch off nothing is written. A receipt never blocks a plan or an answer: refused, it rolls back alone with a warning, as A1's does.

**Readers.** Nothing serving, scheduling or certification reads these. One offline reader exists: populating `hints_used_before` changes the input to the offline probability arms' card (`field/probability_states.py:514`, `:574`; `cli/probability_arms.py`), and the arms' card version records it. New values go only to the fields this table names.

Data capture already records the prefilter (`data_capture/prefilter.py`), frozen objectives, reading-exposure labels and the time metric. This stage adds only what the head schema lacks.

| # | Add | Where | Why it can't wait |
|---|---|---|---|
| 1 | **Disclosure state at ask**: reveal sum on the item, whether an answer or worked solution has been disclosed, hint level reached, attempt state. Computed by the server at insertion, before the model call (`tutor/tutor_qa.py:956`). "Ever disclosed" and "visible now" are separate fields, and the second is client-sent or `unknown`, since the server can't see the screen | `question_events` (new `reveal_state_json`) | Today only `context = 'feedback'` or a timestamp join separates a question typed with the solution in view. Old rows can be approximated by join |
| 2 | **Generating-process fields**: `hints_used_before`, `scaffold_level`, `preceding_tutor_move`, `learner_mode`. Computed by the server from `help_assists` where it can; sent by clients where only they know | `tutor/tutor_qa.py:978` already persists them; the sidecar accepts them (`handlers/tutor_qa.py:277`). `AskOverlay.tsx:613-640` sends only `attemptProgress` | Lost for every question asked |
| 3 | **Question opportunity**: whether Ask was available, per presentation and Reader visit. `plan_presentations` is append-only with one row per block and item, so `ask_available` records the state at serve; a later change is an impression event | `plan_presentations.ask_available` (new), the visit event's payload (add to the allowlist, `reader/reader_inquiry.py:144`), `question_events.question_opportunity` (exists) | Without it, "no question" can't be read as anything. Lost |
| 4 | **Exposure initiator**: `learner`, `plan`, `tutor_citation`, `dose_offer`, `lesson`, with block, session and visit ids. A new field, not a new row: existing coldness readers count rows, and `context` keeps its meaning | `source_exposure_events`, through the writer's column list (`db/repositories.py:4552`); Reader visit events (`origin` is hard-coded, `reader/reader_inquiry.py:396`) | Separates what the learner chose from what the plan sent. Lost |
| 5 | `log_interaction_event` passes `occurred_at` and `received_at` where the caller knows them | `substrate/activities.py:934`; `append_interaction_event` accepts them (`db/repositories.py:12734`) | Offline and phone captures lose the gap |
| 6 | **Hypothesis-list exposure**: attempt, factor, hypothesis versions shown, order **as displayed**, surface, time. A probe answered later is a later linked receipt, never a change to this row. Written by a sidecar RPC from the client's display event. *Built by FG1c (Nov 4, 2026; migration 242) behind `followup.hypothesis_marks`, not `[router_objective] receipts`, since it shares that stage's panel and order. Surfaces: the marks panel, `why?`, the causal feedback, the unresolved-cause card and the inspector, on the desktop* | `hypothesis_list_exposures` (RECEIPT), with the later link in `hypothesis_exposure_probe_links` (RECEIPT). FG1c's marks are their own RAW_LEDGER table, `hypothesis_marks` | A list can state the misconception outright, and only `ClaimSurface` writes `presented` today. Lost |
| 7 | **Session end reason**: `offered_stop_accepted`, `offered_stop_overridden`, `unprompted_stop`, `app_closed`, `foreground_lost`, `external_interruption`, `rule`, `unknown`, each marked `explicit` or `inferred`. A process can't report its own crash, so a crash is inferred at recovery. Holds the plan, block and stop decision in force | New RECEIPT table keyed by session. `daily_plans.stop_reason` stays | The stop model needs it. Lost |
| 8 | **Availability before the session**: minutes offered and their source, local time and time zone, device, and a nullable external window for a later m1nty bridge (no integration exists in this repo). Missing is recorded as missing | Same table, stamped before the first block. A later stop decision reads the row, plus its own snapshot | The main confounder of session length, and gone afterward |
| 9 | **Decision-time belief**: per candidate item, FSRS S, D, R and due (they are per item); per candidate LO, mastery mean and variance, AD `p̄` and `P_band`, open factors and hypothesis posteriors; `ad_state.state_hash`; goal ids, contract versions and dates in force; model and config versions | A new immutable RECEIPT table for the numbers. Bulky text stays in `router_decision_payloads`, which is WORKFLOW, age-pruned (`router/plan_log.py:428`) and restricted to five kinds by a CHECK | Belief tables hold current values only, and the report's toy found FQE's hidden bias nearly vanishes with a belief filter. Lost |
| 10 | **Cold-check timing**: extend the existing chain with how the target delay was chosen and typed non-service reasons. Dates, states and picks already live in `decision_measurement_events`, `cold_measurement_opportunity_decisions`, `lesson_checks` and commitments (`daily_plan/measurement.py:283`, `teacher/delayed.py:240`). `delayed_checks.py` is the picker and has no table | Those tables | Needed by RO5's lag calibration |
| 11 | **Goal lifecycle**: created, date changed, paused, abandoned, completed, removed, with reason. Contract history covers versioned contract edits and has no pause or abandon class; status also lives in the vault's YAML (`vault/models.py:78`), so a change is detected at load | New RECEIPT table for what contracts don't cover | A changed goal is a competing event, and an abandoned goal counts against a policy |
| 12 | **Decision-to-next-state links**: decision to action, uptake or rejection, next decision, and return time, with censoring. A plain view where the ids exist; add only missing ids | Audit `router_decisions`, `plan_presentations`, `decision_objectives` first | RO4-RO6 need the trajectory, not only snapshots |
| 13 | **At each decision**: session and day active minutes, each candidate's predicted minutes and predicted-minute source, pending reports, offered-stop rejected values, and for a pick the VOI verdict in force | Row 9's table | The price needs the forecast and its error. Lost |

**`learnloop data-capture report`** gains coverage per row and measured bytes per day. Size is measured, not assumed.

**Gate.** Serving is byte-identical with the switch on and off apart from the new rows and columns (`tests/test_data_capture_successor.py`'s method). No display order changes in this stage. Receipts hold ids and numbers, no protected text. `db_generate_reference.py` and `db_validate_reference.py` rerun, new tables classified in `table_roles.py`.

## 5. RO1: remove the interval multiplier

### 5.1 The change

`attempts/attempts.py:4646` today:

```python
interval_days = interval_for_retention(next_memory.stability, weights=fsrs_weights) * surprise.fsrs_interval_factor
```

At the successor the factor is not applied.

**Why.** FSRS already rewards a success that looked unlikely: stability gain rises with `1 − R` (`next_recall_stability`, `scheduling/fsrs.py:95`). The multiplier adds a second correction from a different model, uses hand-set constants (`alpha_interval = .3`, clamped to `[.5, 1.5]`, `config/schema.py:24`), reads the LLM difficulty label through `b`, and has no evidence behind it.

### 5.2 What stays and what moves

- **Unchanged:** the FSRS rating (score bins plus the hint cap), stability and D. The factor is applied after `apply_review` and never fed them.
- **Unchanged:** surprise itself and its other consumers: the follow-up gate, the re-probe trigger, `diagnosis/signal_quantiles.py`, the TUI's display.
- **Changed directly:** the stored `due_at`.
- **Changed through `due_at`:** recall targets scale the stored interval (`scheduling/intent/recall_targets.py:124`), the due gate reads it (`scheduling/scheduler.py:2947`), and admission's future review load reads it (`daily_plan/admission.py:124`). So **queues and new-material admission can shift.**
- **Not changed:** delayed-check dating (`delayed_checks.py:158`) and reading paths (`source_retrieval/deliverable_path.py:874`, `instructional/reader_followups.py:588`), which read stability directly.
- **`attempt_surprise.fsrs_interval_factor`** records what was applied. The table is DERIVED and replayed, so replay writes 1.0 under the same gate. The row keeps the residual's inputs, so the old value stays computable.
- **`scheduler.surprise.alpha_interval`, `f_min`, `f_max`** stay in config so vaults below the tag replay. A note says they do nothing at or above it.
- **Docs and code comments:** `recall_targets.py:11` ("keeps the surprise factor already folded into `due_at`"), the config template, `sim/default_sweep.yaml`.

### 5.3 Availability time

New column `practice_attempts.received_at`, nullable, set where `created_at` isn't the write time (`goals/exam_seeding.py`), and wired through the attempt insert list (`db/repositories.py:18655`). A helper: `available_at(row) = coalesce(received_at, created_at)`. The migration backfills imported exam rows from the attempt's ULID time (`exam_seeding.py:377` mints it at write; `ids.py:35`), marked `inferred`, and leaves invalid ids null. Replay keeps the column. It lands here because other stages rely on it, whatever RO0's switch says.

| Reads | Clock | Why |
|---|---|---|
| **Decision-time** reads: `daily_plan/router_card.py:205`, RO2's cards, RO0's snapshots, RO6's features | `available_at` | What the router could know |
| **Outcomes** (`router/outcomes.py:410`), FSRS, mastery | `created_at` | An exam sat on its date was a real exposure then. Reading it at import time would call a warm answer cold |

Filtering by availability doesn't reconstruct what a grade said at the time. Field's `as_of` is an attempt-completion cutoff in which the latest grading epoch stands (`field/outcomes.py:724`), and it isn't relabelled point-in-time. Historical grader knowledge comes from frozen serve-time inputs or grading-epoch dates.

### 5.4 A self-report isn't validated evidence

`record_unresolved_cause_self_report` passes `resolution_observation_ids=[observation_id]` (`diagnosis/causal_attribution.py:3665`), and `diagnosis/split/history.py:912` counts those ids as `validated_evidence_count` for the diagnoser. At the tag, an id of the form `learner_report:*` isn't counted. The diagnoser still sees the pick as the learner's attributed opinion. The factor's status and `resolution_observation_ids_json` don't change. The implementer audits the column's other readers (`diagnosis/causal_orchestrator.py:2735`, `db/repositories.py:17902`) for other counts.

### 5.5 Version and switches

- **Successor** in `SUCCESSOR_CHAIN`, with an upgrade function and a defaults snapshot, per `docs/algorithm-change-playbook.md`. The factor gets its own version gate at `attempts.py:4646`: `hot_path_applies_practice_review` decides whether a review applies, not the factor.
- **Kill switches:** `[scheduler.surprise] remove_interval_factor`, `[router_objective] available_at_reads` and `[router_objective] self_report_not_validated`, default true. False, or below the tag, restores the predecessor.
- **A switch change on the schedule is a projection change.** Rebuild re-derives due dates under the vault's config (`substrate/replay.py`, `attempts/attempts.py:4640`), so flipping `remove_interval_factor` alone leaves persisted due dates as they were until the next review. No hook republishes a projection on a config change, so a flip takes effect on persisted due dates at the next derived-state rebuild or upgrade. The projection's defaults snapshot records the switch's value, `doctor` warns when config and snapshot disagree, and predecessor equivalence is tested after that rebuild.
- **Visible at upgrade:** existing due dates shift within the old factor's range. The playbook's shadow rebuild reports item and activity-card due dates (`substrate/shadow_rebuild.py:145`) and the admission and queue differences on a copy, as the upgrade's report.

### 5.6 Tests

Below the tag and with each switch off, after the projection change, due dates and the diagnoser's context are byte-identical. At the tag: `due_at` follows `interval_for_retention(S)` on every eligible review; held and ineligible attempts are unchanged; surprise values and follow-up triggers match the predecessor; a second rebuild is identical. All switch combinations are tested. Tests to revisit: `test_surprise.py`, `test_irt_end_to_end.py`, `test_intent_recall_targets.py`, `test_causal_repair_sidecar_rpcs.py`, `test_cli_generate_practice.py`, `test_ad23_fix_r5.py`, `test_ad3_subject_view.py`.

## 6. RO2: the frontier LLM forecaster

The bitter-lesson baseline: can a frontier model reading the learner's whole history beat the numeric arms on what the router cares about, and do questions, hints and reading add anything? From RO4 its forecasts feed `Q̄` through a learned slope with a seeded prior (§8.4).

### 6.1 Where it sits

A new outside forecaster, `llm_history_v1`, beside `llm_v3:llm` in `adaptive_difficulty/outside.py`, using the same machinery:

- inputs frozen in the serve transaction (`freeze_presentation_inputs`), sent afterward in the background exactly as frozen, and refused if the content became protected (`sending.SendGuard`);
- `forecast_receipts` with `inputs_as_of`, `received_at`, model and prompt versions; `item_forecast_payloads` for raw text; `judgment_ledger` for accepted verdicts;
- route `ai.routing.ad_forecast_llm`, on the existing spend cap, and on the plan's usage pauses. A forecast skipped for any reason is censored with its reason, never imputed.

It never writes evidence, mastery, FSRS or certification (A2, A12). RO4's sensor layer reads the receipts. `help_assists` and any other new table must first be registered for AD's reads (`adaptive_difficulty/operation.py:200` refuses unclassified tables).

### 6.2 What it is asked

Probabilities strictly in (0, 1):

```
p_now     P(unassisted success on this presentation)                     kind item_unassisted_success (exists)
p_cold_L  P(unassisted success on an unseen item of this LO, L days      kind lo_cold_success (new)
          after this block, if the learner has no exposure to the LO     L in 1, 7, 30
          in between)
```

Plus at most three sentences of rationale citing evidence ids, unvalidated and shown only in the trace. The lags are measurement points, `keep`: nothing weights them.

**Label.** A completed, unassisted attempt on an unseen item, at the board's existing success threshold; A4's other states (help, exclusions, censoring) stay distinct. **Two clocks per receipt:** time since the forecast block and delay since the latest exposure.

**A versioned resolver gives two bindings:**

| Binding | Counts | Read for |
|---|---|---|
| **Per protocol** | The first qualifying outcome, only if no exposure to the LO fell between the block and the outcome. Otherwise censored `intervening_exposure` | Calibration: it's the event the forecast describes |
| **Intention to treat** | The first qualifying outcome, whatever happened, with intervening exposures, help and exclusions recorded | The paired comparison between forecasters, on the same outcomes |

Scored at the realized lag by interpolating in log time. Past 30 days is censored `beyond_measured_lag` until a longer lag is added.

Natural first checks are selected: whether and when one happens depends on the policy, the learner and returning at all. **Reports label these reads as conditional on observation,** and the intended lag estimand comes from RO5's randomized checks.

### 6.3 What it reads

Card `ad-forecast-state-v3`, built through AD's material view and `learner_protection`: no reference solution, key or rubric, no stem of an unattempted item beyond the served item's own, no exam or held-out material. Personal notes only if already linked and allowlisted. Every entry carries an evidence id and days before the serve. Only events with `available_at ≤ served_at`, where `available_at = coalesce(received_at, created_at)` per table, and a table with no `received_at` uses `created_at`. Retrieval is bounded by row limits before any trimming, so the serve transaction's work is bounded and not only the prompt. A token budget (`keep`) then trims oldest first within each rung and states what it left out.

| Rung | Adds | Tests |
|---|---|---|
| **H0** | `llm_v3`'s card **without its incumbent number**: LO and prerequisites, up to 25 attempts, answer excerpts. A separate call | Baseline for the ladder. `llm_v3` itself continues unchanged |
| **H1** | Whole answers; ordered help from `help_assists` (kind, level, strategy, timing, text); questions on the LO with disclosure state; reveals; confidence taps and hedges | Assistance and reasoning |
| **H2** | Reader: exposures, open inquiries and their text, self-check verdicts, digests | Reading and asking |
| **H3** | Other LOs by shared facets and recency; teach-backs; gaps; exam sittings and imports; goals and dates | Whole history |

**Draw.** H3 on every eligible presentation, plus one of H0, H1 or H2 by a seeded draw with a logged propensity, for paired differences at bounded cost. This compares packages of history and doesn't isolate each section. A missing pair is reported, never imputed. Skipped under the spend cap or a plan pause: recorded per rung.

### 6.4 Scoring and reports

Extend `adaptive_difficulty/scoring.py` and `learnloop ad report`, against `mastery_ekf`, `lo_general+composite` and `llm_v3`, on the same presentations: log loss and calibration on field's first-attempt split (primary, D17), repeats, and delayed cold.

Owner-run `learnloop ad forecast-audit`, paid, on frozen inputs while the model is available: a **permuted-history** run (shuffle the history between items of a similar level) and a **prior-strength sweep** (report T8).

The report shows each comparison's interval, including H3 against the lower rungs and permuted against real history, labelled as exploratory. Nothing stops automatically: a rung or the forecaster keeps running until the owner turns it off with `adaptive_difficulty.outside_forecasters`. An interval covering zero isn't read as "no difference".

Reports run on whatever has resolved, with no minimum sample. Slopes are per model and prompt version, and a new version starts from a hierarchical prior, not from the old slope.

### 6.5 Tests

With the forecaster off, no row and no call. Protection tests on every rung, including content marked held out after the serve. A leak test: no event with `available_at > served_at` reaches a card, with a backdated import as the case. Resolver tests for both bindings, with an intervening lesson as the case. The serve transaction's added cost is measured and reported on a copy, as R6's was. Ad-hoc runs follow `env -i` isolation.

## 7. RO3: T1, the extended mechanism check

**Ran Nov 4, 2026:** `research_notes/LearnLoop router optimization research/t1/` (`REPORT.md`, `method.md`, raw results). A Sol Codex worker, no model calls, no learner data, about 85 minutes of compute. These are mechanism checks on invented dynamics, and the run used the earlier weights (`ω = 1`, `c = 1` per day). The orchestrator doesn't rebuild it unless the owner asks.

| Finding | What the spec does |
|---|---|
| Flat load doesn't tie across the models; no tested policy wins everywhere | No allocator work ends here. The tail stays a config seed |
| The cost-aware no-later rule often scores higher, but by **studying less and doing worse**: first-exam performance .710 to .638, 9.4 to 7.3 minutes a day (FSRS-fast). Its gain depends on the attention-price scale | The tail stays flat load. T1 proposed no-later, but that trades away the owner's primary outcome at a price nothing has measured |
| More rollout precision helps by about as much as anything else tested (+.967 ± .333 dated U on four trial IDs), and noisy maximization selects errors | `π_Q` uses common random numbers across candidates and reports its precision (§8.3) |
| The gridded dual and the approximate two-step check often lose badly, and the dual hits guards | Neither is built |
| A rising price beats a linear one on the rising-cost score in all eight cells, but doesn't dominate a flat budget or guarantee reasonable sessions: one rising-price run reached 105 active minutes, and the main tables' approximate planners hit the emergency guard 34 times | Keep rising `κ`, add a price floor against numerical collapse and a `keep` runaway guard (§8.6) |
| `T` and `H` matter: results move with them, except where the continuation makes `H` algebraically irrelevant | `T_C` is net continuation value; no-study and zero terminals are rejected |
| A heuristic tail can react badly to information, giving a probe negative measured value; an exact mini-case gives EVSI .210 only because the posterior changes which repair wins | Probes are scored through observation-dependent repair branches (§8.1) |
| Crossed dates count once; the eve-of-exam regression holds (`Q(stop) = .780`, `Q(block) = .770`, continue minus stop −.010) | The form stands |

## 8. RO4: the objective, live

### 8.1 Seeds and action interfaces

Each is a versioned config seed shown in the trace. The tail and terminal below are what `π_Q` uses to value actions.

- **Tail:** flat total load at the remembered minutes per day, one session a day, with **topic allocation adaptive to the belief** inside the rollout, so that information can matter.
- **`H`:** 90 days. **`T_C(x)`:** the net value of continuing that same tail past `C`: valued uses at the memory forecast under its maintenance, minus its attention cost, over a further `H`, evaluated once and not recursively. So the effective horizon for undated uses is `C + H`. It depends on the posterior and any unfinished action.
- **Sampling:** `N_θ` parameter draws (`[router_objective] rollout_theta_draws`, 8, more until the deadline), each shared across all candidates, with common random numbers for outcomes, durations, uptake and return. `Q̄` is the mean over draws, and the trace reports the paired standard error of the top two candidates' difference.

`E[V(x′)]` needs one interface per admitted action. FSRS and AD supply predictions, so these seeds assemble them from what exists:

| Action | Effect on `P(perform)` | Duration | What it observes | Next state |
|---|---|---|---|---|
| **Review** | FSRS `apply_review`, over the rating distribution from AD's predictive | `answer_minutes` distribution (`daily_plan/estimates.py`) | Graded attempt | FSRS and AD update |
| **New practice** | AD's learning increment `γ`; FSRS first-review state; prerequisite and transfer through AD's shared terms | `answer_minutes` distribution | Graded attempt | Same |
| **Reading** | AD's dose curve for its kind (`adaptive_difficulty/model.py:709`); no FSRS effect (firewall) | The block's estimate | Exposure only | Dose and warmth |
| **Probe, scored as a bundle** | Probe → on each result, the repair or no repair, whichever `Q̄` on the updated posterior prefers → tail. Nothing direct. The branch's choice is in the trace | `voi_forecasts` minutes, plus the repair's | Posterior over hypotheses, through the grader channel | Posterior update, then the branch's repair |
| **Repair, follow-up** | `repair_class_cold_rate` where a class has one, else AD's `γ` | `answer_minutes` distribution | Graded attempt | Same as practice; reveal rules apply |
| **Teach-back** | As practice, at its evidence mass | Its own estimate | Graded transcript | Same as practice |
| **Lesson** | `learner/lesson_weight.py`'s learned mass | The suggestion's estimate | Its checks | Lesson-check update |
| **Offer-type actions** | Value accepted and declined **as branches**: `Q = p·E[R+V | accepted] + (1−p)·E[R+V | declined]`, with `p` from `lesson_suggestion` or `ad_dose_offers` | The accepted branch's | Uptake | Each branch's own |
| **Stop offer** | A branch for accepted (return time given session minutes and availability, seeded from this learner's own return gaps, or next day with no history) and for overridden (the tail's next non-stop block at the same session minutes, so the value isn't defined in terms of itself). `p_accept` starts Beta(1,1), updated from §4 row 7 | 0 active minutes if accepted | Accept or override | Each branch's own |

Durations are sampled, not averaged: with a quadratic cost, `E[C(m,D)] = C(m,E[D]) + κ0/(2m̄)·Var(D)`, so the mean alone understates effort.

### 8.2 The frame

Hard constraints stay in code: safety, protection, admission, irreversible rule-only choices, explicit availability constraints and learner overrides.

**The soft-budget parts open, owner's decision.** Today candidates over the remaining plan or lane minutes are removed (`daily_plan/engine.py:2525`, `lanes.py:520`), and stop is offered only under five minutes left or with nothing feasible (`router_chooser.py:402`). "Minutes left" means budget minus planned minutes (`records.py:269`), not active minutes. So at this tag:

- Stop is supported at every reversible block boundary, and session minutes count active minutes.
- Remembered minutes exclude no continuation; `κ` prices them. `feasible` no longer filters on plan or lane minutes (`engine.py:2525-2532`), and `minutes_left` may go negative and shows as minutes past the plan. Its readers (`items_left`, the displayed list, `support_order`'s `unspent_share`) are updated.
- **Lane shares stop excluding candidates.** The repair and maintain caps were hand-set; `lane_minutes_left` is still computed for ordering, display and staged's fallback order.
- **A drawn stop is an offer the learner can override.** The floor could otherwise end a session at minute 10. An override is logged (§4, row 7).
- Today's copy changes accordingly: the plan's minutes are a suggestion. Frictionless defaults and the plan's finite list as first shown stay.

The top-k support keeps staged's ordering, so that ordering still limits what both policies see. Below the tag or with the switch off, the predecessor frame stands.

### 8.3 Two policies and a learned mix

Served distribution, computed and logged exactly (G3):

```
μ_i(a) = (1 − k·ε) · [ w_i·π_L^op(a) + (1 − w_i)·π_Q^op(a) ] + ε
```

**The LLM policy `π_L`.** New, on the existing `router_llm` route with request schema `router_llm_choice_v3`: one request per decision over the candidate set. It reads a decision-level variant of RO2's H3 card, over the union of the candidates' LOs with one shared token budget, built in the prefetch job rather than a serve transaction and frozen with the boundary key, plus the goals, dates, weights and the declared objective. It returns a probability per option (every option positive), per-option forecasts (§8.4), and up to three sentences of rationale with evidence ids. The tail's next action is sent as a non-choosable reference row, so it gets a forecast too. The prefetch budget applies, and the first-day report measures this policy's timeout rate, since a whole-history card may strain it. The older `llm` chooser and its limited card stop being served. Its proposal and its forecasts are scored separately: a model can rank well and predict poorly.

**The numeric policy `π_Q`.** Plain expected-value maximization:

```
Q̄_i(a) = E_{θ|data}[ Q^{π_tail, θ}(x, a; C) ]        π_Q(a) = 1[a = argmax Q̄_i]
```

Ties: candidates whose `Q̄` are within the reported paired precision of the maximum are broken by support order, staged's pick first. There's no best-share sampling inside it. Exploration lives in the mix and the floor. It can still choose a probe. It runs as a third job inside the prefetch (`_block_job`), with the prefetch's remaining budget as its deadline. A serving step that finds it unfinished treats it as a timeout, logged like a model failure, and the trace reports precision, because noisy maximization selects errors (§7).

**The staged rule and the Decider.** Their recommendations stay logged as advice and comparators and get no serving share. Staged remains the failure fallback. Hard rules aren't weighted.

**Failure.** `π_L^op` is `π_L` if the request completes validly in time, else `π_S`, and likewise for `π_Q^op`. Each failure moves only that policy's share. With both failed, `μ_i = (1 − k·ε)·π_S + ε`, drawn and logged like any other decision, so the existing floor is kept (Q7). A deterministic staged choice happens only where the code already makes one: an irreversible staged pick, a single-option support, or a refused follow-up. The logged probability describes the distribution actually used, after redistribution. Both "successful LLM calls" and "the deployed policy with its fallbacks" are reported, since dropping failures would flatter it.

**The weight.**

```
w_i = ℓ_L + (1 − ℓ_L − ℓ_Q) · p_i          p_i = P(Δ > 0 | evidence)
```

`Δ` is the LLM's recommendation's value minus the numeric one's, under the live continuation (§8.7). Config seeds, chosen by judgment and not measured: `w` starts at 0.8, `ℓ_L = ℓ_Q = 0.1`. The minimums are declared prices for information; they give disagreements support beyond what the floor provides. This is **posterior probability matching at the policy level, an exploration rule.** It isn't the optimizer of expected value, and it has no learning rate. One global `w` to start; a contextual form waits for evidence that context matters.

**Mid-block follow-ups (`plan_interrupt`)** use the same two-policy mix over `{insert_now, continue_current}`: `π_L` from the LLM policy's `intervene_now` probability on the restraint card, and `π_Q` from `Q̄` of the two candidates `RestraintGate._state` already builds, valued as a repair block and as the current block's remaining questions with the follow-up at the next boundary. The Decider's `P(yes)` is logged as advice. `wait_feasible = False` and refusals stay deterministic as today. Their scores enter the same posterior.

**Kill switch** `[router_objective] enabled`, default true at the tag. False serves the predecessor's mixture and frame exactly. Below the tag, nothing is computed. It requires `receipts`: with receipts off, the objective serves and no comparison score is formed.

### 8.4 Sensors and the memory model

`P(perform | path)` for a candidate combines a memory forecast and sensors:

- **Memory forecast:** FSRS R at the use's lag for practiced items, and AD's predictive for the LO's cell. AD's readiness numbers already reach the card (`daily_plan/router_card.py:549`).
- **Combination:** Bayesian logistic regression of realized cold outcome on frozen sensor values, so predictions stay in `[0,1]`. A richer kernel must beat it on prequential score first (report T7).
- **Parameter draws vs outcome noise.** Only parameter uncertainty enters `θ`: AD's posterior, slope posteriors, the `κ0` posterior. A known success probability of .7 still has noisy outcomes, and that noise isn't uncertainty about the value.
- **Forecast vs effect.** Forecast slopes can use resolved outcomes, read as §6.2 labels them. **Effect slopes**, `ΔG = α_v + β_v·f(a)` on the logit scale, train only on randomized assignments. `f(a)` is the LLM's forecast for `a` minus its forecast for the **tail's next action**, the named reference. The regression target is the logit residual of the realized cold outcome against the memory rollout's forecast for the taken action, and `ΔG` is added to that forecast on the logit scale. So it's a **correction to the memory rollout's learning effect**, never a replacement, and a gain isn't counted twice. The correction applies only when every candidate and the reference have a forecast; a missing one drops it for that decision. Prior `β_v ~ N(0.2, 0.04)` (variance), as AD gives its item-only LLM signal (`alpha:z_v1`, `adaptive_difficulty/priors.py`), with `α_v` centered on zero. It's learned, never a fixed strength: a fixed-strength LLM prior caused real harm in a live recommender test (report). `[router_objective] sensors_in_value` turns it off by hand.
- **EIG, EVSI, VOI:** read from `voi_forecasts` and A1's `upstream` part into the **trace only**. A probe's value comes from its bundle's branches (§8.1), so nothing is added twice, and EVSI minutes aren't converted to a price.
- **Card v3:** `render_text` renders each candidate's goals and days to date, which the typed card holds (`router_card.py:248-251`) and the models don't see today. Scoring reads the goal contract directly.

### 8.5 Goals and uses

- **Dated goal:** `ω_{g,L}` per LO in the goal's scope, at `due_at`, default 1, asked once at goal creation and adjustable later. A new contract field `use_weight` (`goals/goal_contracts.py`, whose canonicalization at `:194` currently drops unknown fields). It's in the content hash and out of the support hash, a new change class, with a stated default for a goal with no confirmed contract and no rewriting of old hashes. `Goal.priority` stays a tie-break.
- **Undated use:** `c_L` per day per LO, from enrollment (A3's definition) with no end, for LOs in scope of a quest or kept in retention. **A config default, `[router_objective] undated_use_density`, `1/90`, copied into the goal contract at creation** and adjustable per goal, so a config change doesn't rewrite history or replay. Topics outside any goal read the config.
- **What the default means.** One exam date on a topic is worth about 90 days of ongoing use. A lower `c` favors dates, a higher one lasting knowledge. It's a preference, labelled as a seed, and `c` stays fixed when `H` changes.
- **One goal's date is scored once.** Retained knowledge can still earn through undated uses and later goals, which are different outcomes.
- **Pass thresholds** aren't used. A goal that truly has one may add `ω·1[G ≥ θ]` later.
- **Reading candidates** still follow the nearest active goal (`daily_plan/engine.py:275`). With two dated goals, the policies can only choose among what's offered. Deferred with a trigger (§11).

### 8.6 The attention price

```
κ(x) = κ0 · x / m̄         x = active minutes in this session
∫[m, m+d] κ(u) du = κ0 · ((m+d)² − m²) / (2 m̄)
```

- **Session minutes,** owner's decision. Two 25-minute sessions cost less than one 50-minute session. **A session ends after a gap of at least `[router_objective] session_gap_minutes`, `keep`, default 60,** so short restarts can't reset the price. A new session starts at zero. A carry from a recent session is added only if RO5's data shows it matters. The seed tail uses one session a day.
- `m̄` is the plan's remembered minutes (`daily_plan/engine.py:863`). It can be the learner's choice, a carried value, or a first-run default, and the trace records which.
- **Seed:** until the posterior holds randomized stop-offer evidence (RO5), `κ0`'s prior is re-centred each day on that day's forecast marginal gain per minute at `m̄`, so one unusual day doesn't set the price. At the day's first decision, with `d̄` one block's predicted minutes: `κ0 = (G(m̄ + d̄) − G(m̄)) / d̄` from the tail rollout. Until RO5, **`κ` is the seed,** and the trace says so; in practice `m̄` acts as a soft budget. With no frontier on a day it carries the last value; with none ever, it starts from the seed tail's average marginal gain per minute. A vanishing forecast gain can't collapse it: the price is floored at the last positive value.
- **Runaway guard.** T1's rising-price runs still reached 105 minutes. A stop offer is forced into the support past `[router_objective] session_guard_minutes`, `keep`, default `3·m̄`, and every crossing is reported. It's a numerical safeguard, not a budget, and the learner can continue.
- **Learning:** a grid posterior with a stated likelihood: a logistic choice between continuing and stopping given the forecast gain and the price, from frontier choices and randomized stop offers in both directions, with availability as a covariate. Voluntary stops enter as censored inequalities, and their selection term isn't identified before RO5. Each stop says only that the model's forecast gain was below the price, so `κ` is labelled preference plus model error.
- **Frontier display:** optional, one tap, never blocking: "25 minutes: predicted 78. 40 minutes: predicted 81." Numbers are labelled predictions.

### 8.7 Learning the weight

**One common return, frozen before the draw.** A policy that picks strong topics must not score well for that alone, so both arms are measured on the same uses, which don't depend on the candidates:

- **Uses.** `𝒰_i` is the set of topic-days `(L, d)` with `L` in scope of any active goal or retention commitment at `t_i`, and `d` in the evaluation window `(t_i, t_i + B_i]`, plus any dated use `(g, L)` with `D_g` in the window. It's frozen in the trace. `B_i` is `[router_objective] evaluation_window_days`, 14.
- **Weights.** `v_i(L,d) = c_L` from `L`'s contract, and `v_i(g,L) = ω_{g,L}`.
- **Outcomes.** `Y_{L,d}` is a randomized cold check of `L` on day `d` (§9 item 2), scored by §6.2's label. A dated use's `Y` is the imported result on the goal's date (`goals/exam_seeding.py`) with `r = 1`, since the sitting happens whatever the router did. A missing import is censored `no_result`.
- **Baselines.** `m⁰_iu` is the §8.4 memory forecast of `P(perform_u)` from the pre-action belief, under the tail: the same number the pre-action `V` uses, logged per use. `C⁰_i` is `B_i` times the learner's mean daily attention cost over the preceding `B_i` days, or the tail's cost at `m̄` in the first week.
- **Cost.** `C_i` is the realized attention cost over the window, at the `κ0` in force each day.

**The comparison score.** With `d_i(a) = π_L,i(a) − π_Q,i(a)`:

```
D̂_i = (d_i(A_i) / μ_i(A_i)) · [ Σ_u v_iu · (R_iu / r_iu) · (Y_iu − m⁰_iu) − (C_i − C⁰_i) ]
```

- `R/r` corrects for which outcomes were observed, and `d/μ` for which action was taken. They do different jobs.
- `Σ_a d_i(a) = 0`, so `m⁰` and `C⁰` only reduce variance and don't change the target. The score is unbiased for `Δ_i` when `μ_i > 0` wherever `d_i ≠ 0` (the floor guarantees it), `r` is known, and observation is independent of `Y` given the action and state.
- **No action-specific model prediction enters this score.** `π_Q` maximizes `Q̄`, so scoring with `Q̄` would make it win by construction. An unchecked use contributes nothing, so a model-filled outcome is never evidence for the model that filled it.
- `A_i` is always the drawn action. A learner pick, a stop override or a plan interruption after it is part of the outcome under the live continuation.
- `Y` is a check at its own lag on a sampled item, so it's a proxy for the use until RO5's calibration exists. Weights stay fixed and are never renormalized over the checks that completed.

**What carries no score.**
- A decision whose window holds no valued use with `r_iu > 0`: its effort alone would measure only cost and would favor whichever policy recommends less study. **So until RO5's checks exist, `w` stays at its prior,** and the trace says so.
- A decision where either policy fell back to `π_S`: it compares the LLM with staged, and gets its own row in the report.
- Decisions where the policies agree: `d = 0`.

**Observation probabilities.** `r` is known for RO5's randomized checks, whose inclusion is fixed before the action draw and doesn't depend on it (§9, item 2). `r_iu` = the assignment probability × the learner's running completion rate for randomized checks, pooled and never conditioned on the action. The completion gap and the uncorrected estimate are reported beside it, since a check needs the learner to return, and an action can affect that. **Natural checks never enter the posterior that sets `w`.** Whether they happen depends on the policy and on returning, so they go to §8.9's forecast evaluation and a separate, labelled `Δ̂_natural`. Checks are also learning exposures, and their effect belongs to the live continuation.

**The posterior over `Δ`.** One global Gaussian with prior `N(m₀, s₀²)`, where `p₀ = (0.8 − ℓ_L)/(1 − ℓ_L − ℓ_Q) = 0.875`, `m₀ = Φ⁻¹(p₀)·s₀`, and `s₀` is a config seed, 0.01 use-equivalents, about one block's effect on `B` days of undated use at the default `c`.

A score is formed when its window has closed; until then it's pending, and censored ones are recorded by reason. Scores aren't grouped by shared check, since each stays unbiased for its own `Δ_i`, so sharing affects only the variance:

```
Δ̄  = mean_i D̂_i                                          over every closed score
V̂  = Σ_g (Σ_{i in g} (D̂_i − Δ̄))² / n²                    g = consecutive 2B-day bins by decision time
posterior precision = 1/s₀² + 1/V̂
posterior mean      = (m₀/s₀² + Δ̄/V̂) / posterior precision
p_i = Φ(posterior mean / posterior sd)
```

With fewer than two bins holding scores, `V̂` isn't defined and the posterior stays at its prior. `w_i` for a decision at `t_i` uses only scores whose windows closed before `t_i`, so `μ_i` never depends on outcomes inside its own window. That's what keeps `D̂_i` conditionally unbiased while `w` moves. Evidence is counted honestly in the report, where one check counts once.

**This will be slow and noisy, by design.** In a toy with stipulated values (`research_notes/LearnLoop router optimization research/t1/dhat_sim.py`; only the ratios are meaningful), per-decision noise was hundreds of times the plausible `Δ`, because one outcome is multiplied by about `1/(r·μ)`. With this prior, **`w` is expected to stay near 0.8 for the first years.** Movement before the posterior sd falls below `s₀` is mostly noise, and the report shows the posterior mean, sd and `n` beside `w`. This follows from not grading the numeric policy with its own model and not trusting self-selected checks. A faster weight needs more randomized checks, not a looser estimator: variance scales with `1/r`. Embedded checks are the cheap way to get them (§9, item 2), and `embedded_checks_per_day` raises the rate further. The speedup hasn't been simulated.

### 8.8 The trace

The owner's requirement: each sensor, the objective and the output, visible.

A new immutable RECEIPT table, `router_objective_traces`, one per decision, holding per-candidate numbers and referencing §4 row 9's row by id; only bulky text goes to payloads:

```
for each candidate:
  sensors     each value, quantiles, model and prompt version, slope version, receipt id, whether it reached Q̄
  terms       crossed-date reward, undated reward, κ integral, E[V(x′)], T_C, Q̄, Q̄ − V, Q̄ − Q̄(stop), precision
  split       learning, information, return effect (display only; not added)
  filter      if it was filtered: the gate and reason (A1's receipt, by id)
policies:     π_L and its rationale, a_Q, availability, latency, spend, staged and Decider advice
mixing:       posterior mean, sd and n, p_i, ℓ, w_i, weights after fallback, final μ, seed, chosen, which draw chose it
evaluation:   𝒰_i, B_i, m⁰, C⁰, objective version
frontier:     G against minutes for the day's support
versions:     objective, tail, H and T, memory model, κ posterior and regime, ω and c contract versions, snapshot id
```

`learnloop router trace <decision>` prints it, and the "why" surface offers it on demand in plain words (frictionless by default, glass box on request).

### 8.9 The report

No evaluation here gates anything. R3's router report keeps these apart, and none stands in for another:

| Evaluation | Question |
|---|---|
| **Forecast** | Did the models predict observed outcomes? |
| **Action value** | Did predicted differences between actions match randomized outcome differences? |
| **Recommendation value** | Did one policy's next recommendation produce more of the common return, under the live continuation? |
| **Whole policy** | Not estimated from logs. Sequential DR stays out (report), and T1-style simulation isn't evidence about a learner |

Counts are shown separately: decisions evaluated, **unique completed assessments**, decisions informed, pending, censored by reason, model-supported value, closed scores, and the posterior mean and sd of `Δ`, so a reader can see whether `w` moved on evidence. Observed outcomes, proxies and projected tail value are labelled apart, and a projected tail is never evidence that the policy producing it is better. Comparators are versioned: a new provider model, prompt, card or objective version starts a new row, so a stronger LLM isn't mistaken for learning.

### 8.10 Tests

- **Predecessor:** switch off or below the tag, blocks and rows are byte-identical apart from RO0's receipts.
- **Propensities:** G3 recomputes `μ` from logged values, including on each failure path and for `plan_interrupt`; the seed reproduces the draw; streams are independent; `ℓ_L ≤ w ≤ 1 − ℓ_Q`.
- **Form:** `V` recomputed from logged per-candidate `Q` equals the stored `V`, to float tolerance. The eve-of-exam regression holds. A date inside a long action is scored at the date. An action crossing `C` is handled by `σ` with its commitment carried. Every step of a rollout uses one `C`. The same `θ` draw is used across candidates. Offer branches match a hand-computed case, including `κ0/(2m̄)·p(1−p)d²`.
- **Evaluation:** `Σ d = 0` makes `D̂` invariant to the levels of `m⁰` and `C⁰`. `D̂`'s mean matches a planted `Δ` on a synthetic log, and is zero under a planted null. A fallback, an agreeing decision and a window with no `r > 0` form no score. `w_i` reads no score from a window still open at `t_i`. `π_Q` gets no advantage from any action-specific model term, on a planted case where the critic is wrong. A check linked to ten decisions counts as one unique assessment in the report.
- **Protection:** the card's rules hold on v3 and on the LLM policy's card. A failed policy's share goes to `staged`.
- **First day:** on a copy with no outcomes, the report shows stop's share at each boundary, session length, and each policy's share, against the predecessor, as the upgrade's report. It doesn't hold the upgrade.
- **Latency:** the deadlines hold on a copy.

## 9. RO5: return and calibration

A7 isn't landed. `experiment_id` exists in `policy_experiment_assignments` and measurement records (`daily_plan/measurement.py:302`, `scheduling/randomization_layer.py:242`), which is a place to integrate, not a generic experiment. Each arm below records its own assignment with an exact logged probability in `policy_experiment_assignments`, and doesn't wait for A7. Probabilities are declared prices for information, not statistical facts. Their seeds are in §12, and the report shows what they cost in minutes.

1. **Stop coin.** At a reversible block boundary: randomize offering stop against presenting the next block, in both directions, with availability logged first. The randomized action is the **offer**, so acceptance and overrides stay inside the outcome; it identifies the effect of offering stop, not of forcing one. It trains stop's return distribution and `κ`, and it ends the daily re-centring. The observational form is rejected (report T9). The trace shows the return effect; if attendance proves near-deterministic for this learner, the return model drops out of `V`.
2. **Randomized checks, embedded by default.** Long-lag accuracy can only come from long lags, and each check resets the delay (A4), so checks are rationed. `[router_objective] check_rate` defaults to `"embedded"`: **a check replaces one ordinary question, so it adds almost no minutes and needs no new UI.** `embedded_checks_per_day` sets how many (default 1, in the day's first session). A number instead of `"embedded"` selects extra checks at that rate per valued topic per day, the design for wanting more data than practice can carry; `"off"` schedules none.

   **The draw.** At the start of each calendar day, a seeded draw picks a topic uniformly from the `N_d` valued topics that have an eligible item that day: unseen, unrevealed, unassisted so far, and not exam-reserved or protected. So `r_L = 1/N_d` is exact, and a topic with no eligible item has `r_L = 0` that day, recorded as such, and raises a generation need through the existing path. **The draw is fixed before any action draw and doesn't depend on it,** which §8.7's `r` requires.

   **Serving.** The frame places the check at the session's first practice slot, outside the two-policy mix: it's neither policy's action and isn't in `μ`. Its minutes count toward the session and `κ` as usual. It's an ordinary independent attempt under the existing evidence rules, and §6.2's label reads it, so help makes it a non-success. The learner sees a normal question with no special label. A session with no practice slot leaves it unadministered with a reason.

   **Recording.** Assignment, administration, completion and reasons for noncompletion are separate, in `policy_experiment_assignments` with the exact probability. A day with no session counts toward the completion gap (§8.7), since an action can affect returning. The check displaces one more targeted question, and the report shows how often, with what it costs in generation.

   **Tests.** Same seed, same draw; the draw doesn't change with the action or either policy's output. `r_L` matches the eligible count. No protected or exam-reserved item is ever drawn. `"off"` and the predecessor serve identically. The replaced item returns to the pool.
3. **Goal-date read.** The date's outcome is observed at most once per goal, so it needs a stand-in with two stages, both logged as versioned sensors:
   - pool forecast at lag L, calibrated by (2);
   - pool-to-goal transfer: a slope per goal type, wide prior, from imported exam results (`goals/exam_seeding.py`) and optional sittings.

   "Am I ready?" stays a button, and its reads are flagged as self-selected. A read near the date counts as an exposure.
4. **`S = 0.75 R_cold + 0.25 R_next`** (`router/outcomes.py:6`): `α` gets labelled provisional, like the one-day coldness rule. Learned coldness (router §15.2) reads the same covariates.
5. **Cold read before repair and a leave-alone arm** (report: repair overwrites the evidence about whether the earlier reading would have held). A7's continue arm is close, and FG1's probe before held feedback is close to the cold read. A leave-alone arm conflicts with FG1's serve-at-once, so it's an owner decision (§12).
6. **Testing misconception picks.** Owner's decision, Nov 4. A pick that today resolves its factor (a concrete candidate the trace doesn't contradict) keeps doing so by default. A small seeded share, assigned atomically with the report and reused on retries, stays open instead: the report is recorded and passed on as attributed opinion, no provisional belief opens, and the factor stays open.

   **What this identifies.** The effect of leaving a pick open, including on repair targeting, since no provisional belief forms. Agreement between picks and probes is conditional: open factors are probe targets only under further restrictions, such as open-set coverage and divergent repair classes (`diagnosis/probe_targeting.py:383`, `:429`), and the VOI gate may decline (`scheduling/staged_policy.py:595`). So easy picks stay unprobed and ambiguous ones get probed. `learnloop data-capture report` records assignment, eligibility, gate reasons, administration, completion and intervening instruction separately, and labels agreement as conditional on being probed. Agreement against delayed performance is reported for all picks, labelled self-selected. Seeing the list can itself change later performance, which RO0's exposure rows make visible.

   FG1c's marks stay separate: on the probe lane they replace the tap and resolve nothing.

## 10. RO6: a learned tail

Fitted Q evaluation of a **frozen logger version** on low-dimensional belief features from RO0's snapshots, days to go, and pending reports. Text goes to sensors, not features. Freezing version `k`, including its mix and `w` at each decision, is what makes this an evaluation of one policy, and version `k+1` uses the result.

The backup uses the target's next-action distribution, and the reward is **this objective's `R`**, not `S = 0.75 R_cold + 0.25 R_next`, which is a different objective:

```
y_i = R_i + Σ_{a′} π_ref(a′ | x′_i) Q̂(x′_i, a′)        with the time and terminal handling of §3.2
```

**Its claim is narrow:** the logger's value plus one small improvement step. A coin followed by the logger tests `Q^{π_b}(a) − Q^{π_b}(a′)`. More data doesn't lift this.

**How it enters.** As a residual on RO4's tail, inside `π_Q`'s value: `Ṽ = V_tail + ŵ·V_residual`, with `ŵ` a learned weight starting at zero and moved by how well frozen predicted contrasts match realized randomized ones, by slope and rank (report T10). So it phases in on its own, with no promotion step, and the trace shows `ŵ`. `Ṽ` is an approximate critic, not the exact value of any policy. Never fitted to TD loss alone. Refit after every mixture change, with generator versions as change points. Partial-history weights are reported beside it as the cross-check near the logger.

**No improvement guarantee is claimed.** A `2δ` per-decision bound needs a uniform `Q` error bound and an expected-value update whose feasible set contains the baseline. Calibration slopes and rank agreement don't establish those, so the report keeps showing §8.9's evaluations.

## 11. Not in this spec

| Item | Why | Trigger |
|---|---|---|
| The surprise source: AD's item-conditioned predictive instead of the label's `b` (`P(y | z, item)`), and label removal from the mastery path (`mastery.irt.difficulty_from_prior`) | Agreed in principle; AD writing to surprise crosses the firewall (A2, A12) | A four-way replay on a copy, on the owner's go-ahead |
| `z_v1` against `z_llm` inside AD; the label's mixed reference populations | Separate AD change | The same replay |
| Learned signal masses (`field/signals.py`), reveal state as covariate, the post-reveal `facet_solid` likelihood | Prediction work that RO0's fields unblock | After RO0 |
| Scoring question-driven targeting and fast-track | Same | After RO0 |
| Small defects: the `exam_readiness` `count`/`n` overlay; clarification's inconsistent help status; `attempt_id IS NULL` questions in AD replay and router outcomes | Worth fixing, unrelated to the objective | A follow-ups batch |
| Shuffling the displayed hypothesis order | A serving change, with stable hypothesis identities; FG1 §7 owns it. *Built by FG1c on the marks panel, seed logged; `why?`, the causal feedback and the unresolved-cause card keep their order, and their receipts record it* | FG1c |
| Reading candidates per active goal | Candidate generation, not scoring | Two dated goals active at once |
| A contextual weight, `logit w = α + θ·φ(h)` | One global weight first | Evidence that context matters |
| The LLM-prior-and-correction form, `π ∝ π_L·exp(β·Â)` | An alternative to the mix, not an addition | Action values useful enough to reweight single candidates |
| A lifelong continuing criterion | RO4 is a finite approximation (§3.2) | Stated separately when it would change a decision |
| Weights under topic splits and merges | Per-topic defaults change total utility when topics change | A split or merge that moves a goal's total noticeably |
| Periodic corpus analyst | Report: persona moved support 34-66 points. Hypotheses only, never evidence | T11 on a copy |

**Deliberately not built:** a learned sequence encoder or joint latent model; deep rollouts or MPPI; POSMDP solvers; Memorize's closed form; whole-policy sequential DR; minimax regret as a live criterion; a time-indexed dual or two-step check (T1); an average-rate `ρ`; reward terms for information or good questions; a learner-choice model in π.

## 12. Defaults and open decisions

**Config seeds the build ships with, chosen by judgment and not measured.** Each is shown in the trace and changeable without a code change: `w` starts at 0.8; `ℓ_L = ℓ_Q = 0.1`; `s₀ = 0.01`; `c = 1/90` per day; `ω = 1`; `H = 90`; `B = 14` days; flat-load tail; `β_v ~ N(0.2, 0.04)`; `rollout_theta_draws = 8`; `session_gap_minutes = 60`; `session_guard_minutes = 3·m̄`; `stop_coin = 0.05` per reversible boundary in each direction; `check_rate = "embedded"`; `embedded_checks_per_day = 1`.

| # | Open decision | Default |
|---|---|---|
| D1 | Leave-alone arm (§9, item 5), given FG1's serve-at-once | Not built; A7's continue arm first |
| D2 | Stage order against FG1 and A7 | The orchestrator's queue decides. No RO stage needs either to land |

## 13. Specs amended at landing

`spec_action_router_v1.md` §7.3 (the two-policy mix, stop eligibility; §15.2 unchanged), `plan_router_r2_v1.md`, `spec_daily_loop_v1.md` (minutes as a soft limit and lane shares no longer excluding, RO4), `daily_loop_frictionless_defaults.md` if its plan wording changes, overview §9.2 and its finite-plan wording, `spec_adaptive_difficulty_v1.md` §8 (the new forecaster and kind), `spec_followup_generate_serve_v1.md` §7 (shared exposure table), `docs/algorithm-change-playbook.md` (RO1's recorded effect on `due_at`).

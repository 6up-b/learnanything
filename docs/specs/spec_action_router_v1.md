# Action router: decision models inside a deterministic frame (v1)

**Status:** draft for owner review (2026-10-11).

**Owner decisions (2026-10-11 and 2026-10-12):**
- **Two judgment models compete; the evidence picks the winner** (2026-10-12):
  - **Perplexity Decider v1.1** (`perplexity/pplx-decider-v1.1-27b`), a decision model that returns typed probabilities;
  - **a frontier LLM** (`ai.routing.router_llm`), returning a probability distribution plus a rationale.

  Both answer every decision. Selection samples from a mixture, so the replay can score the staged policy, the Decider and the LLM on the same decisions (§7.3, §10). Neither Jev nor a fine-tuned local model is used.
- **The Decider is called through OpenRouter** (2026-10-12), with the existing `OPENROUTER_API_KEY`, not Perplexity's direct API.
- **Both models also serve the learner field's `llm_probability` harness arms** (`spec_learner_field_v1.md` §7.2).
- **Earlier decisions do not block this on their own.** Where this spec revises one, it says which and argues from the merits. The main revision: P4 §7.1 kept the action chooser transparent "indefinitely" because a deterministic incumbent leaves no off-policy evidence path at n=1. This spec supplies that path (§7).
- **A learned or LoRA-tuned router is deferred, with a trigger** (§13). A review on 2026-10-11 found that the Qwen-LoRA proposal (`docs/brainstorming/Agent's qwen LoRA for action router.md`) can't be trained or evaluated on about 10³ decisions a year without logged propensities.

**Sources:**
- `docs/brainstorming/Pipeline Augmentation Plan.md`:
  - §B, `RouterStateV1` and `LearnerStateCardV1`;
  - the unified action object;
  - the outcome `S`;
  - Plans F and G.
- `docs/specs/spec_p4_controller_and_scale.md`:
  - §3, snapshots;
  - §4, the staged policy;
  - §5, constraints;
  - §6, EVSI;
  - §7, the shadow predictive components;
  - §9.3, the randomization layer.
- `docs/brainstorming/Bitter Lesson Research Sweep.md` §4 (the router).
- `docs/specs/daily_loop_frictionless_defaults.md`.
- `docs/specs/spec_learner_field_v1.md`.

---

## 0. Thesis

At n=1, LearnLoop makes about 10³ routing decisions a year. That is too few to train a router, but plenty to **evaluate** one, provided every decision is logged with its candidate set and true propensities. So the router is split by job:

| Job | Who does it | Why |
|---|---|---|
| **Hard rules**: feasibility, cold reserves, blind grading, LO lifecycle, budget, depth envelope | Code (the P4 constraint engine) | Never negotiable, and never offered to a model |
| **Numbers**: P(correct), retention, information value, cost | Explicit models fit on the learner's own data: the `LearnerPredictor` (field §4), FSRS, EVSI (`scheduling/evsi.py`) | Few parameters, honest uncertainty, they learn from n=1 |
| **Judgment**: what is going on, whether to intervene now, which block fits | The Decider and a frontier LLM, each reading the learner's history as text. Both answer, and a logged mixture decides which choice is served (§7.3) | A frontier-scale model is the best available pretrained "learner encoder". At ~10³ events a year a topic's filtered history fits in context. Which kind of model routes better is an empirical question; the replay answers it (§10) |
| **Restraint**: don't interrupt, "let them continue" | Code, as a deterministic gate, plus "continue" as a scored candidate | LLM tutors over-intervene, and prompting doesn't fix it (2607.21306). Scoring the no-op is what worked in DICE (2610.04825) |

**Why two models.**
- **The Decider returns typed probabilities instead of prose:** `noul` P(yes); `choice`, a probability for each of up to 255 named options; and `score`, an ordinal rubric. That makes it a sensor whose outputs can be scored, and a stochastic chooser whose distribution comes straight from the model. It gives no rationale.
- **A frontier LLM reasons in text and can explain itself,** but its probabilities are verbalized: asked for, not read from the model. It is the obvious alternative.
- **Both are cheap at ~10³ decisions a year,** so both answer every decision.

**Why exact propensities matter.** The served choice is sampled from a known mixture of the staged policy and the two models, so every propensity is exact. A propensity only has to be the distribution actually sampled from; it doesn't need to be calibrated. Exact propensities make all three policies evaluable by off-policy replay on the same decisions. That is the piece that was missing and kept P4's chooser deterministic.

**Evidence shape.** In the best real-learner result in the sweep, an explicit belief state and planner made the decisions and the LLM supplied observations: an RCT with 770 students, +0.15 SD (2608.16907). This design keeps that shape, and also lets the model choose wherever the planner can't separate the candidates.

---

## 1. Scope

**In scope:**
- **The learner state card,** generated deterministically from the ledger.
- **Retrieval of similar past decisions,** with their outcomes.
- **The Decider and LLM clients.**
- **Router sensors and a block chooser** inside the P4 staged frame.
- **Three router modes** behind a kill switch.
- **Decision logging** with full candidate sets and propensities.
- **Outcome joins and the replay report.**
- **Live authority over the daily plan's block choice.**

**Not in scope:**
- **Item selection within a block.** It stays with P4 §4.4's transparent selectors and `find_practice` (Slice 2 §5.9).
- **Grading.** It stays blind; the card never reaches the grader.
- **Placement thresholds** (field §5.2).
- **Training any model.**

---

## 2. Code truth (audited 2026-10-11)

- **Today's queue** comes from the legacy scheduler's weighted priority (`scheduling/scheduler.py` `_priority`; `selection_rewards.score_selection_reward`, intents `probe | practice | repair | review | transfer`).
  - Composed offers record `propensity_kind = UNAVAILABLE` (`scheduler.py:642`).
  - ε-exploration excludes probes (`scheduler.py:1544-1551`), so probe decisions always log propensity 1 or 0.
- **The P4 staged policy** (`scheduling/staged_policy.py`) chooses one 5–15 minute attention block and then one activity, through an explicit if/elif ladder. It is live only for staged-owned P2 golden-path runs (`controller_cutover.py:46`, `STAGED_POLICY_LIVE_FOR_P2`). Everywhere else it is shadow.
- **The feasible set** comes from `constraint_engine.feasible_set`:
  - active;
  - stimulus renderable;
  - purpose;
  - hard exposure;
  - assessment reservation;
  - fatigue budget;
  - same-facet dispersion;
  - stage interleaving.
- **Snapshots.** `controller_snapshot` builds one content-hashed snapshot per decision, with no cold-answer material.
- **Randomization.** `randomization_layer` admits exactly three designs (`mrt_reversible`, `epsilon_tiebreak`, `commitment_parallel`) and logs the seed and true propensity before selection.
- **Signals.** `state_signals.derive_signals` turns snapshots into rule-derived booleans for the ladder.
- **What doesn't exist:** `RouterStateV1` and `LearnerStateCardV1` are designs only (Pipeline plan §B). Slice 1's `DiagnosisContext` is the nearest prototype of the card.
- **The canonical actions** are `measure_diagnostic`, `instruct`, `practice` (with subtypes), `assess_terminal`, `maintain`, `expand_model` and `stop` (`controller_actions.py`).

---

## 3. Architecture

```
daily plan request (minutes, intent)            ← daily loop P1–P3
        │
        ▼
ControllerSnapshot ──► constraint engine ──► feasible block candidates (incl. continue, stop)
        │                                              │
        │                         planner values per candidate: staged-rule eligibility,
        │                         robust EVSI, predicted gain/cost from LearnerPredictor + FSRS
        │                                              │
        ├──► LearnerStateCardV1 (§4) ──┐               ▼
        ├──► similar past decisions (§5) ──► Decider + LLM requests (§6): sensors + choose_block
        │                                              │
        │                                              ▼
        │                       selection (§7): deterministic, or sampled with a logged propensity
        │                                              │
        └────────────────────────────► router_decisions receipt (§9) ──► within-block selection (P4 §4.4)
                                                       │
                                     outcomes join later: R_next, R_cold (§10)
```

Decisions are made at **block boundaries**, not per item. That means about 3–6 per study session, and the next block is computed while the learner reads feedback (§8).

---

## 4. `LearnerStateCardV1`

This is the canonical text and JSON rendering of the learner for one decision. It is **regenerated from the ledger and never edited by a model** (Pipeline plan §B).

**Typed fields** (JSON, the `RouterStateV1` subset that is cheap now):
- `as_of_event_id`, the snapshot hash, and schema and algorithm versions;
- **the session:** minutes left in today's plan, the streak, the time since the last session, and whether this is re-entry;
- **for each candidate's LOs:**
  - the active predictor's P(success) mean and interval;
  - `untested` / `assumed` / `demonstrated` status;
  - FSRS retrievability for the due cards;
  - the evidence summary (demonstrated capabilities vs assisted-only);
- **interaction signals in the last 7 days** (field §3.1): hints used, help requested before starting, typed tutor questions;
- **intent:** commitments, goals and deadlines, as the daily loop defines them (Q7).

**Text sections:**
- **Recent work:** up to N graded attempts on the candidates' LOs and their prerequisite neighbours. For each, the item stem, the learner's answer (excerpt), the blind grade, and the diagnosis hypothesis, with event ids.
- **Open hypotheses:** each with its evidence for and against, and the repairs already tried with their delayed outcomes.
- **Retention risks and explicit unknowns:** "never tested", "assumed (not tested)".
- **Learner preferences and recent self-reports:** "too easy", "I don't know this", "not now".

**Rules:**
- **No cold-answer material,** and nothing from a reserved assessment surface (P4 leakage rule).
- **Never sent to the blind grader.**
- **Tense comes from validity intervals,** for example "confuses X since June; resolved Aug 3" (Pipeline plan §A).
- **Size budget:** `router.card_token_budget`, default 16K tokens. If over budget, older successes are dropped first, then older text excerpts. Typed fields are never dropped.
- **Hashed:** the card's hash and rendered text are stored with the decision (§9).

---

## 5. Similar past decisions (in-context learning without training)

This is a new embedding record kind, `decision/context`, using the Phase 1 substrate. Its recipe embeds a canonical rendering of the decision's typed state: the candidates' LOs and their statuses, the error families present, the session phase, and re-entry.

**Retrieval** takes the top `router.similar_k` past decisions (default 6), by mean-centered cosine, subject to three filters:
- **Matured outcomes only.** Only decisions whose `R_next` (and, if available, `R_cold`) was observed **before** the current decision time. There is no leakage by construction.
- **Different session.** Decisions from the current session are excluded.
- **Within the learner's own history** (n=1).

Each retrieved decision is shown to both models with its candidate set, the chosen block, the propensity, and its outcomes. Embeddings only choose *which* past decisions to show (Slice 2 R1/R4). They decide nothing.

**Evaluation discipline.** Retrieval earns its place only if the replay (§10) shows that the models with similar decisions beat the models without them (MemDelta discipline, Pipeline plan §A).

---

## 6. The judgment models

### 6.1 Decider facts relied on (Perplexity docs and announcements, checked 2026-10-11 and 2026-10-12)

- **Model.** `pplx-decider-v1.1-27b`, released 2026-10-06. On OpenRouter it is `perplexity/pplx-decider-v1.1-27b`. A third-party report found the v1 slug returning 404 there on 2026-10-10, and v1.1 returning 200.
- **Endpoints.**
  - **OpenRouter (owner's choice):** base URL `https://openrouter.ai/api`, with `OPENROUTER_API_KEY`. OpenRouter lists it at $0.02 per million input tokens and $0 output. The model doesn't appear in OpenRouter's public `/api/v1/models` chat list (checked 2026-10-12). Third-party sources describe it as reachable through OpenRouter's decision ("System One") interface rather than chat completions.
  - **The exact path and body on OpenRouter are unverified.** R0's first task is to confirm them from OpenRouter's docs and pin them in the client.
  - **Perplexity's direct endpoint** (`POST https://api.perplexity.ai/v1/decisions`) is the documented reference for the request shape only. The owner's route is OpenRouter (D4).
- **Request.**
  - `model`;
  - `state`: a string, an object, or an array (text plus base64 images);
  - `questions`: a map of 1–128 named questions. Each has a `type`, `instructions`, and `criteria` or options.
  - Unknown fields return 400. There is no `temperature` or `seed`.
- **Answer types.**
  - `noul` returns P(yes).
  - `choice` takes 1–255 named options, each with a description, and returns the choice, per-option probabilities, and a self-reported `confidence`. The docs make no calibration claim.
  - `score` takes an ordinal rubric of up to 10 levels and returns a score, probabilities, and confidence.
- **No rationale field.** The model explains nothing.
- **Determinism.** Identical requests usually return identical numbers, but they can differ in the second decimal place.
- **Limits.**
  - Input under 262,144 tokens; body up to 32 MiB.
  - 10 requests per second per organization.
  - Latency under 2 s for a few hundred tokens, and about 23 s near the input limit.
- **Price.** $0.02 per million input tokens; output is free. A 20K-token decision costs about $0.0004, so a year of decisions costs well under a dollar.
- **Weights.** Open weights are reported on Hugging Face (one listing says Apache 2.0). **Unverified.**

These facts are pinned per receipt by model id. If Perplexity changes the API, the client fails closed.

### 6.2 Providers and routes

- **The Decider.**
  - **Provider type and profile.** A new type, `decider`, in `ai/providers/`. Profile `openrouter_decider`: base URL `https://openrouter.ai/api`, `api_key_env = "OPENROUTER_API_KEY"`, model `perplexity/pplx-decider-v1.1-27b`. A `perplexity_direct` profile can switch to Perplexity's endpoint (D4).
  - **Interface.** `DecisionClient.decide(state, questions) -> DecisionResult`, with typed question classes.
  - **Routes:** `ai.routing.router_decider` and `ai.routing.llm_probability_decider`.
  - **Fallback.** Neither route falls back to a chat provider, because the interface differs. `LEARNLOOP_AI_PROVIDER` doesn't override them, the same rule as `ai.routing.embedding`.
  - **Provider routing.** Don't set OpenRouter's `data_collection: "deny"` unless OpenRouter lists a compliant provider for this model. Otherwise every request fails. D6 covers the privacy side.
- **The LLM.**
  - **Routes:** `ai.routing.router_llm` and `ai.routing.llm_probability_llm`, using existing chat providers with structured output. An unset route falls back to the active provider, and receipts record the resolved model (handoff rule 6).
  - **Transport.** Any chat transport, including Codex on the owner's ChatGPT subscription (owner, 2026-10-12). Codex's cost is estimated from reported token usage, with no physical-request bound (Slice A plan §5 rule 6).
- **Readiness** checks keys and model reachability for both.
- **Settings** shows a privacy disclosure for each provider that receives learner text.
- **Receipts.** `model_call(purpose = "router_decision" | "llm_probability", judge = "decider" | "llm")` records tokens, cost, model id, the question-set version and the state-card hash.
- **Spend controls.** Slice A's §5.6 framework applies, with a daily cap (`router.max_daily_cost_usd`, default $1.00, mostly the LLM) and `--dry-run` on every batch command.
- **A later option** (D5): local hosting of the Decider's open weights. A 27B model fits a 32 GB GPU only quantized (estimate), and quantization changes outputs, so a local model would get its own model id and its own evaluation.

### 6.3 One request per model per decision

Each model gets the same `state`: the card from §4, the similar decisions from §5, and the candidate list.
- **The Decider** gets the named questions below (question-set version `router_qs_v1`).
- **The LLM** gets the same questions as one structured-output request (`router_llm_v1`). Its JSON schema returns:
  - `choose_block`: a probability for every candidate id, renormalized by the client;
  - `intervene_now`, `teach_first_<lo>` and `will_pass_next_<lo>`, each as probabilities;
  - `rationale`: at most 3 sentences;
  - `evidence_ids`: the card event ids the rationale relies on, validated against the card.

The questions:

| Question | Type | Feeds | Prequential ground truth |
|---|---|---|---|
| `choose_block` | `choice` over the top `router.k` feasible candidates (default 6), always including `continue_current` (when a block is in progress) and `stop_for_today` (when feasible) | Selection (§7) | DR value of `S` (§10) |
| `intervene_now` | `noul`: "Would interrupting the learner's current block to help or diagnose do more good than letting them continue?" | The deterministic restraint gate's tie input (§7.2). Its source is `router.sensor_source` (default `decider`); both answers are scored | `R_next` after continue vs after intervene, DR |
| `teach_first_<lo>` (≤ 3 LOs) | `noul`: "Does the evidence show a misunderstanding that should be taught before more practice?" | The staged rule's "target knowledge not acquired" branch, as a sensor beside `state_signals` | Failure on the next attempt on that LO |
| `will_pass_next_<lo>` (≤ 3) | `noul` | Logged only (the harness §7.2 V3 arm, in decision context) | The next graded attempt on that LO |

**Instructions.** Written in plain language, versioned, and stored with the question set. Options carry short descriptions: the action, the LOs, minutes, the planner's estimated gain, and why the block is feasible.

**What neither model can do:**
- add candidates;
- see infeasible ones;
- see cold-answer material;
- see item answer keys for unattempted reserved items.

---

## 7. Selection: who decides what

### 7.1 Hard and irreversible things stay deterministic

These are chosen only by the staged rule, and never sampled:
- `assess_terminal`;
- `practice(depth_progression)` edges;
- anything that burns a reserved surface;
- `expand_model`.

They appear in `choose_block` only as context. The models' probabilities for them are logged but can't select them.

### 7.2 Restraint gate

Mid-block interruptions (a probe or diagnosis during practice) open only when the staged rule's measurement condition holds. Where the rule is indifferent, "continue" is the default.
- `intervene_now` can **block** an interruption the rule would allow, when P(yes) < 0.3.
- It can never **force** one.

This asymmetry is deliberate (2607.21306).

### 7.3 Modes (`router.mode`; kill switch `router.enabled`)

| Mode | Selection among reversible feasible candidates | Propensity |
|---|---|---|
| `staged` | The P4 staged rule chooses. Ties within margin δ go through `epsilon_tiebreak` (existing). Both models still answer, for logging and sensor scoring | From the randomization layer |
| `mixture` | Sample from **π = w_s · staged-argmax + w_d · Decider + w_l · LLM** over the top `router.k` reversible candidates, with a per-candidate floor ε_min = 0.02. If `router.ties_only = true`, the mixture applies only when the top candidates are within margin δ by planner value; otherwise the staged choice stands | Exact. The logged propensity is π(chosen); each component's distribution is stored |

- **A new randomization design.** `mixture` registers `model_mixture` as a fourth admissible design in `randomization_layer` (a revision of P4 §9.3). It applies to reversible candidates only, logs the seed, the component weights and π before selection, and joins proximal outcomes at the next spaced cold review, as for the other designs.
- **Launch** (owner: see what works best; D1): `mixture` with w_s = w_d = w_l = 1/3 and `ties_only = false`. Every policy keeps support, so each one's argmax can be evaluated on every decision.
- **Kill switch.** `router.enabled = false` returns Today to its pre-router version, exactly as before (G8). With the daily loop's `plan.enabled` on, that is the finite plan with its deterministic chooser `lane_quota_v1`. With it off, it is the legacy scheduler's queue (`spec_daily_loop_v1.md` §6.8, switch table).
- **Fallback.** If one model times out or errors, its weight goes to the staged component for that decision. If both fail, the staged choice is used. Both cases are flagged on the receipt (`fallback = decider | llm | both`).
- **The learner's explicit choice always wins** (P4 §4.1). It is logged as `learner_pick` with no propensity.

### 7.4 What the learner sees

The "why" follows whichever component's draw selected the block:
- **staged:** the staged reason (P4 §3.3);
- **the Decider,** which gives no rationale: "LearnLoop's model picked this among N close options", plus the planner's top reason for that candidate;
- **the LLM:** its rationale, labelled as model-written, with its cited evidence ids linking to those attempts.

This follows honest labels: nothing pretends to be an explanation that wasn't computed.

---

## 8. Latency

- **Block boundaries only.** The first block is decided when the plan is built, and later blocks are precomputed while the learner reads feedback on the last item of the current block.
- **Bounded input.** The input target is ≤ 30K tokens per request (card 16K + similar decisions + candidates), which keeps latency in the low seconds.
- **Timeout.** `router.timeout_seconds` (default 8) falls back to the staged choice.

---

## 9. Persistence

| Table | Role | Contents |
|---|---|---|
| `router_decisions` | RAW_LEDGER (append-only decision facts) | Each row records:<br>• decision id, snapshot hash, mode, design, seed;<br>• the candidate set with planner values, feasibility and staged eligibility;<br>• both models' distributions and sensor answers, and the mixture weights;<br>• the chosen candidate and propensity, and the learner-pick and fallback flags;<br>• question-set version, model id, card hash, similar-decision ids;<br>• latency and cost |
| `router_decision_payloads` | WORKFLOW | The rendered card text and both models' raw responses, for audit. Pruned after `router.payload_retention_days` (default 365); hashes stay on the decision |
| `router_outcomes` | DERIVED (one replayer) | `R_next` and `R_cold` per decision, joined from the attempt ledger and reveal ledger under the Pipeline plan's `S` definition. Pending outcomes stay right-censored |

**Replay** reads the persisted model answers and makes zero model calls. A rebuild never re-asks.

---

## 10. Evaluation

1. **Predictive first: the harness.** Before the router goes live, the learner field's `llm_probability` variants V1–V3 (field §7.2), each run on both models, answer two questions: does rich history beat item content, and does the Decider or the LLM predict better. The router still launches either way, because its job is judgment, not prediction. The result decides whether `will_pass_next` ever feeds a live choice.
2. **Sensors.** Each sensor is scored prequentially against its declared ground truth (§6.3), on log loss, Brier and reliability. A sensor that is no better than base rate after 100 resolved cases is dropped from the question set.
3. **Policy: the router replay report.** Run with `learnloop router report`, after every 200 decisions.
   - **Doubly-robust estimates** of mean `S` for staged-argmax, Decider-argmax, LLM-argmax and the logged mixture. The outcome model is the active `LearnerPredictor`.
   - **A head-to-head** of Decider vs LLM on the decisions where their argmaxes differ.
   - **Also:** false-remediation rate, minutes per unit of `S`, skips, "not now" and "too easy" rates, and plan completion.
   - **Effective sample size** per comparison.
   - **Split by** re-entry vs normal sessions and by block type.
4. **Switching rule** (in the style of field §7.4). Use the margin fixed before the run (D2) and a bootstrap interval that excludes 0.
   - **A winner.** If one policy beats both others on DR mean `S`, and its false-remediation rate is no worse, its weight rises to 0.8. The other two keep 0.1 each, so evaluation stays possible.
   - **A clear loser.** A policy that loses to both others drops to the floor weight.
   - **Can't tell.** Equal weights stay until 600 decisions. Then the weights go to staged 0.6, Decider 0.2 and LLM 0.2.
   - Each switch is an algorithm successor with the kill switch above.
5. **Sensors.** `router.sensor_source` switches to whichever model's `intervene_now` scores better (log loss) after 100 resolved cases.

---

## 11. Rollout

| Phase | Builds | Needs | Gate |
|---|---|---|---|
| **R0: model clients and harness variants** | The `decider` provider over OpenRouter (exact path confirmed first), the `router_llm` / `llm_probability_*` routes, readiness and receipts; field §7.2 `llm_probability` V1–V3 on both models | Slice A Phase 2 merged | Harness report on the owner's replay (owner-run, spend-capped) |
| **R1: decision logging on today's paths** | Full candidate sets and propensities on the legacy Today queue and the staged P2 path; "continue" logged as a candidate; probe near-ties admitted to `epsilon_tiebreak` with logged propensity (closing `scheduler.py:1544-1551`) | R0; after Slice A Phase 6 merges (same files) | Logging tests; no serving change except the probe tie admission (successor + kill switch) |
| **R2: router live for the daily plan** | `LearnerStateCardV1`; `decision/context` embeddings and retrieval; both model requests; the two modes and `model_mixture`; `router_decisions` / payloads / outcomes; the staged frame composing Today's plan blocks (the P4 cutover extended from P2 runs to Today); the learner-facing "why" | The daily loop's finite plan (P1–P3, Q9); R1 | Algorithm successor with kill switch `router.enabled`; G1–G9 (§12) |
| **R3: first replay report** | `learnloop router report`; switching per §10.4 | 200 decisions | Owner reads the report once |

---

## 12. Gates and tests

| # | Gate |
|---|---|
| G1 | **Hard rules hold:** no sampled or model-chosen candidate is ever infeasible. A fake Decider or LLM that puts all its mass on an infeasible id cannot select it |
| G2 | **Irreversible actions are never sampled** (§7.1), asserted on a fixture with a terminal-assessment candidate |
| G3 | **Propensities are exact:** the logged propensity equals π(chosen) under the logged weights and component distributions, seeds reproduce draws, every candidate in `mixture` has at least ε_min, and a failed component's weight moves to staged |
| G4 | **Restraint asymmetry:** `intervene_now` can block but never force an interruption |
| G5 | **No leakage:** the card has no cold-answer or reserved-surface material, and similar decisions include only outcomes matured before the decision |
| G6 | **Replay:** zero model calls on rebuild; `router_outcomes` rebuilds deterministically |
| G7 | **Fallback:** timeouts, errors and spend caps fall back to the staged choice, flagged on the receipt |
| G8 | **Kill switch:** with `router.enabled = false`, Today matches the pre-router version on fixture copies |
| G9 | **Learner pick wins**, and is logged without a propensity |

**Tests:**
- the Decider client against a fake endpoint (request shape, the 400 on unknown fields, typed parsing);
- the LLM client's structured output: renormalization, unknown candidate ids rejected, evidence ids validated against the card;
- card determinism and budget truncation;
- the retrieval maturity filter;
- each mode's sampling;
- the DR estimator on a synthetic logged policy with known value.

---

## 13. Deferred, with triggers

| Deferred | Revisit when |
|---|---|
| **A learned action scorer** (frozen or fine-tuned embeddings, LoRA; the Qwen-LoRA proposal) | All four hold:<br>1. R2 is live with exact propensities;<br>2. ≥ 500 decisions with matured `R_cold`, and ≥ 50 randomized observations for each of ≥ 3 block types;<br>3. Slice 2 T8 shows embeddings add held-out predictive value: the primary verdict's 95% interval has its lower bound above m. That is `embeddings_add_value`, or `kill` with reason code `real_gain_below_delta` (D10). Read `reason_code`, not the verdict name alone: since T8 v4, `kill` also covers a real gain below the success head's δ;<br>4. The better of Decider-argmax and LLM-argmax beats staged on DR `S`, so a cheaper learned version has a measured gap to close |
| **Item-level routing by a model** (within a block) | R3 shows block-level gains and the within-block transparent selectors are the measured bottleneck |
| **Affect sensors** (fatigue, frustration) | P4 U-011's affect stream is wired into the snapshot |

---

## 14. Open decisions

| # | Decision | Recommendation |
|---|---|---|
| D1 | Launch mode | `mixture` with equal weights (1/3 each), `ties_only = false` (owner, 2026-10-12: see what works best) |
| D2 | Switching margin for §10.4 | Fixed before the first report at 0.03 in mean `S` |
| D3 | `router.k` (candidates shown) | 6 |
| D4 | Route: Perplexity direct or OpenRouter | **Decided (owner, 2026-10-12): OpenRouter, `perplexity/pplx-decider-v1.1-27b`** |
| D5 | Local hosting of the open weights | Not now. Revisit if API cost or availability becomes a problem; it would be evaluated as its own model id |
| D6 | Privacy | Learner text goes to Perplexity (via OpenRouter) and to the LLM route's provider. The owner accepts text leaving the machine, and checks retention terms before R2 |
| D7 | Label when a model chose | "LearnLoop's model picked this among N close options" (Decider), or the labelled rationale (LLM) |
| D8 | Card budget | 16K tokens; revisit after the harness V3 results |
| D9 | Which LLM for `router_llm` | The configured frontier route; Codex on the owner's subscription is allowed (owner, 2026-10-12). Pin the model id per receipt |
| D10 | Which T8 outcomes meet §13 condition 3 | The primary verdict's lower bound above m: `embeddings_add_value`, or `kill` / `real_gain_below_delta`. T8's δ (0.005 nats per attempt) is the bar for building the *success head*, not for a learned action scorer, which conditions 2 and 4 gate on their own. Before T8 v4 every interval with its lower bound above m was `embeddings_add_value`, so this keeps condition 3's meaning. The owner may narrow it to `embeddings_add_value` only (recorded 2026-10-12, T8 v4 review F1) |


---

## 15. Owner direction (2026-10-12, after R0/R1)

### 15.1 Teach-back is an information-rich probe

Keep teach-back items in R1's probe tie-break. Don't exclude them.

A learner's teach-back dialogue is among the most informative evidence LearnLoop collects, especially once the learner has some domain knowledge. The pathway:
- the blind grader grades the dialogue;
- an LLM summarizer condenses it (what was explained correctly, what was missing or wrong, in the learner's own words);
- the summary enters `LearnerStateCardV1` (§4) as typed evidence with its source attempt.

That makes teach-back a first-class probe for the router. Its cost (one long task, one paid grading call) belongs in the candidate's cost term (§7), not in an exclusion rule.

### 15.2 Coldness is learned, not hard-coded

R1's `router_outcomes` defines `R_cold` provisionally as "≥ 1 day since any attempt or reveal on the LO". The owner's direction: cold retrieval is the point at which we'd expect the learner to have forgotten. That can come after a few other questions, after a day or after a week, and FSRS models it. So:
- **Log the covariates, not just the flag.** For each outcome, `router_outcomes` (or a sibling view) records:
  - time since the last exposure to the item, its facets and its LO (attempt, reveal, reading, tutor);
  - the number of intervening attempts;
  - the FSRS-predicted retrievability at attempt time;
  - the reveal-ledger amount since the last attempt.

  The 1-day flag stays as a provisional label.
- **Fit coldness in R3.** Score outcomes by how much they tell us about long-term retention: weight success by `1 − R_pred` (a correct answer when forgetting was likely is the signal) instead of a binary cold/warm cut. Validate against certified cold measurements (`coldness_receipts`) where they exist.
- **Flag the data problem.** Cold outcomes arrive days to weeks after the decision, and cold retrieval is part of what the router optimizes. So:
  - the router needs **surrogate outcomes** to learn at a useful speed: `R_next` plus the FSRS-predicted retention gain;
  - each surrogate is checked against the true delayed outcomes as they mature;
  - pending outcomes stay right-censored, never failures (R1).

### 15.3 Canonical sources as a retrieval tool for the router (deferred)

The owner's proposal: let the router's LLM query the canonical source vault in natural language for questions and explanations that match what the learner needs, in place of choosing only among items that already exist.

Design sketch (orchestrator additions in *italics*):
- **One retrieval surface:**
  - `search_sources(query)`: Slice 2 T6's hybrid retrieval plus verification over source blocks;
  - `find_practice(query)`: Phase 5b's practice index over items and dossiers;
  - *`facet_lookup(query)`, so a gap named in learner text resolves to the registry.*

  Each returns typed hits with provenance. The router LLM (and the tutor) call these as tools.
- **Uses:**
  - *probe choice: "items that discriminate misconception X from Y";*
  - explanation blocks: the canonical passage for a repair, under T6's exclusion of the item being practised;
  - *reading blocks in the daily plan: the next section, ranked against open gaps;*
  - *the tutor's "Practice this": offer a retrieved item that targets the question just asked (DL3's "Practice on…").*
- **When nothing fits,** *the router asks Phase 5a's source-anchored generation path for a verified item grounded in the retrieved spans. Nothing unverified is served.*
- **Guardrails:**
  - retrieval results are context only, and the choice still passes the staged frame and the constraint engine (§7);
  - *retrieved candidates join the logged candidate set, so propensities stay exact and off-policy evaluation still works (R1/R3);*
  - retrieved spans keep T6's answer-leak exclusions.
- **Trigger:** after R2 is live and T6's re-evaluation (2026-10-12, stronger model) settles hybrid vs dense. *Start with the tutor's "Practice this", which has the shortest path to value; it needs only `find_practice` and T6.*

### 15.4 Decisions recorded

| # | Decision | Owner, 2026-10-12 |
|---|---|---|
| D11 | Teach-back in the probe tie-break | Keep it. It is an information-rich probe, and its dialogue summary feeds the card (§15.1) |
| D12 | `R_cold` | Learned from logged covariates in R3. The 1-day rule is provisional (§15.2) |
| D13 | Staged P2 bridge wiring | Deferred to R2's cutover (R1 open question) |

---

*Related: `spec_p4_controller_and_scale.md` (§4, §7.1 revised here, §9.3 extended here) · `spec_learner_field_v1.md` §7.2 · `daily_loop_frictionless_defaults.md` · Pipeline Augmentation Plan §B · Bitter Lesson Research Sweep §4*

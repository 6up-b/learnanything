# Action router: a decision model inside a deterministic frame (v1)

**Status:** draft for owner review (2026-10-11).

**Owner decisions (2026-10-11):**
- **The router's model is Perplexity Decider v1.1** (`pplx-decider-v1.1-27b`), not Jev or a fine-tuned local model. It also serves the learner field's `llm_probability` harness arms (`spec_learner_field_v1.md` §7.2).
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
| **Judgment**: what is going on, whether to intervene now, which block fits | The Decider, reading the learner's history as text | A frontier-scale model is the best available pretrained "learner encoder". At ~10³ events a year a topic's filtered history fits in context |
| **Restraint**: don't interrupt, "let them continue" | Code, as a deterministic gate, plus "continue" as a scored candidate | LLM tutors over-intervene, and prompting doesn't fix it (2607.21306). Scoring the no-op is what worked in DICE (2610.04825) |

**Why the Decider specifically.** It returns **typed probabilities instead of prose**:
- `noul`: P(yes);
- `choice`: a probability for each of up to 255 named options;
- `score`: an ordinal rubric.

That makes it a sensor whose outputs can be scored, and a stochastic chooser whose propensities are known exactly. Known propensities make the router evaluable by off-policy replay, which is the missing piece that kept P4's chooser deterministic.

**Evidence shape.** In the best real-learner result in the sweep, an explicit belief state and planner made the decisions and the LLM supplied observations: an RCT with 770 students, +0.15 SD (2608.16907). This design keeps that shape, and also lets the model choose wherever the planner can't separate the candidates.

---

## 1. Scope

**In scope:**
- **The learner state card,** generated deterministically from the ledger.
- **Retrieval of similar past decisions,** with their outcomes.
- **The Decider provider and client.**
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
        ├──► similar past decisions (§5) ──► Decider request (§6): sensors + choose_block
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

Each retrieved decision is shown to the Decider with its candidate set, the chosen block, the propensity, and its outcomes. Embeddings only choose *which* past decisions to show (Slice 2 R1/R4). They decide nothing.

**Evaluation discipline.** Retrieval earns its place only if the replay (§10) shows that the Decider with similar decisions beats the Decider without them (MemDelta discipline, Pipeline plan §A).

---

## 6. The Decider

### 6.1 Facts relied on (Perplexity docs and announcements, checked 2026-10-11)

- **Model.** `pplx-decider-v1.1-27b`, released 2026-10-06. `pplx-decider-v1-27b` is also available.
- **Endpoint.** `POST https://api.perplexity.ai/v1/decisions`, with `Authorization: Bearer <PERPLEXITY_API_KEY>`.
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
- **OpenRouter.** It lists the model (announced 2026-10-07). Whether it exposes the typed answers is **unverified**.
- **Weights.** Open weights are reported on Hugging Face (one listing says Apache 2.0). **Unverified.**

These facts are pinned per receipt by model id. If Perplexity changes the API, the client fails closed.

### 6.2 Provider and routes

- **Provider type.** A new type, `perplexity_decisions`, in `ai/providers/`, with profile `perplexity_decider` (`api_key_env = "PERPLEXITY_API_KEY"`, model `pplx-decider-v1.1-27b`).
- **Interface.** `DecisionClient.decide(state, questions) -> DecisionResult`, using typed question classes.
- **Routes:**
  - `ai.routing.router_decider`;
  - `ai.routing.llm_probability` (field §7.2).
- **No fallback.** Neither route falls back to a chat provider, because the interface differs. `LEARNLOOP_AI_PROVIDER` doesn't override them, the same rule as `ai.routing.embedding`.
- **Readiness** checks the key and that the model is reachable.
- **Settings** shows a privacy disclosure: learner text goes to Perplexity. The owner accepts text leaving the machine, but must check Perplexity's retention terms (D6).
- **Receipts.** `model_call(purpose = "router_decision" | "llm_probability")` records tokens, cost, model id, the question-set version and the state-card hash.
- **Spend controls.** Slice A's §5.6 framework applies, with a daily cap (`router.max_daily_cost_usd`, default $0.25) and `--dry-run` on every batch command.
- **Later options** (D4, D5): an OpenRouter route, if it exposes typed answers; local hosting of the open weights. A 27B model fits a 32 GB GPU only quantized (estimate), and quantization changes outputs, so a local model gets its own model id and its own evaluation.

### 6.3 One request per decision

One request carries the `state` (the card from §4, the similar decisions from §5, and the candidate list) and these named questions (question-set version `router_qs_v1`):

| Question | Type | Feeds | Prequential ground truth |
|---|---|---|---|
| `choose_block` | `choice` over the top `router.k` feasible candidates (default 6), always including `continue_current` (when a block is in progress) and `stop_for_today` (when feasible) | Selection (§7) | DR value of `S` (§10) |
| `intervene_now` | `noul`: "Would interrupting the learner's current block to help or diagnose do more good than letting them continue?" | The deterministic restraint gate's tie input (§7.2) | `R_next` after continue vs after intervene, DR |
| `teach_first_<lo>` (≤ 3 LOs) | `noul`: "Does the evidence show a misunderstanding that should be taught before more practice?" | The staged rule's "target knowledge not acquired" branch, as a sensor beside `state_signals` | Failure on the next attempt on that LO |
| `will_pass_next_<lo>` (≤ 3) | `noul` | Logged only (the harness §7.2 V3 arm, in decision context) | The next graded attempt on that LO |

**Instructions.** Written in plain language, versioned, and stored with the question set. Options carry short descriptions: the action, the LOs, minutes, the planner's estimated gain, and why the block is feasible.

**What the Decider can't do:**
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

They appear in `choose_block` only as context. The Decider's probability for them is logged but can't select them.

### 7.2 Restraint gate

Mid-block interruptions (a probe or diagnosis during practice) open only when the staged rule's measurement condition holds. Where the rule is indifferent, "continue" is the default.
- `intervene_now` can **block** an interruption the rule would allow, when P(yes) < 0.3.
- It can never **force** one.

This asymmetry is deliberate (2607.21306).

### 7.3 Modes (`router.mode`; kill switch `router.enabled`)

| Mode | Selection among reversible feasible candidates | Propensity |
|---|---|---|
| `staged` | The P4 staged rule chooses. Ties within margin δ go through `epsilon_tiebreak` (existing). The Decider runs only for logging and sensors | From the randomization layer |
| `decider_ties` | Staged, except when the top candidates are within margin δ by planner value: then sample among them from the Decider's `choose_block` probabilities | Exact |
| `decider_router` | Sample from π = (1 − λ) · Decider + λ · staged-argmax over the top `router.k` reversible candidates, with a per-candidate floor ε_min = 0.02 | Exact |

- **A new randomization design.** These modes register `decider_mixture` as a fourth admissible design in `randomization_layer` (a revision of P4 §9.3). It applies to reversible candidates only, logs the seed and propensity before selection, and joins proximal outcomes at the next spaced cold review, as for the other designs.
- **Launch mode** (owner preference: decisive live change, D1): `decider_router` with λ = 0.5. Half the probability mass stays on the staged choice, so both policies keep support for evaluation.
- **Kill switch.** `router.enabled = false` returns Today to the legacy scheduler, exactly as before.
- **Fallback.** On a timeout or error, the staged choice is used (`fallback = true` on the receipt).
- **The learner's explicit choice always wins** (P4 §4.1). It is logged as `learner_pick` with no propensity.

### 7.4 What the learner sees

The Decider gives no rationale. So the "why" is:
- the staged reason (P4 §3.3), when the staged choice stood;
- otherwise, "LearnLoop's model picked this among N close options", plus the planner's top reason for that candidate.

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
| `router_decisions` | RAW_LEDGER (append-only decision facts) | Each row records:<br>• decision id, snapshot hash, mode, design, seed;<br>• the candidate set with planner values, feasibility and staged eligibility;<br>• Decider probabilities and sensor answers;<br>• the chosen candidate and propensity, and the learner-pick and fallback flags;<br>• question-set version, model id, card hash, similar-decision ids;<br>• latency and cost |
| `router_decision_payloads` | WORKFLOW | The rendered card text and the raw Decider response, for audit. Pruned after `router.payload_retention_days` (default 365); hashes stay on the decision |
| `router_outcomes` | DERIVED (one replayer) | `R_next` and `R_cold` per decision, joined from the attempt ledger and reveal ledger under the Pipeline plan's `S` definition. Pending outcomes stay right-censored |

**Replay** reads the persisted Decider answers and makes zero model calls. A rebuild never re-asks.

---

## 10. Evaluation

1. **Predictive first: the harness.** Before the router goes live, the learner field's `llm_probability` variants V1–V3 (field §7.2) answer whether the Decider predicts better from rich history than from item content alone. The router still launches either way, because its job is judgment, not prediction. The result decides whether `will_pass_next` ever feeds a live choice.
2. **Sensors.** Each sensor is scored prequentially against its declared ground truth (§6.3), on log loss, Brier and reliability. A sensor that is no better than base rate after 100 resolved cases is dropped from the question set.
3. **Policy: the router replay report.** Run with `learnloop router report`, after every 200 decisions.
   - **Doubly-robust estimates** of mean `S` for staged-argmax, Decider-argmax, and the logged mixture. The outcome model is the active `LearnerPredictor`.
   - **Also:** false-remediation rate, minutes per unit of `S`, skips, "not now" and "too easy" rates, and plan completion.
   - **Effective sample size** per comparison.
   - **Split by** re-entry vs normal sessions and by block type.
4. **Switching rule** (in the style of field §7.4):
   - If Decider-argmax beats staged-argmax on DR mean `S`, with a bootstrap interval excluding 0 at a margin fixed before the run (D2), and its false-remediation rate is no worse, λ drops to 0.1. The floor keeps evaluation possible.
   - If staged wins, the mode becomes `decider_ties`.
   - "Can't tell" keeps the mixture until 600 decisions, then defaults to `decider_ties`.
   - Each switch is an algorithm successor with the kill switch above.

---

## 11. Rollout

| Phase | Builds | Needs | Gate |
|---|---|---|---|
| **R0: Decider client and harness variants** | The `perplexity_decisions` provider, routes, readiness and receipts; field §7.2 `llm_probability` V1–V3 | Slice A Phase 2 merged | Harness report on the owner's replay (owner-run, spend-capped) |
| **R1: decision logging on today's paths** | Full candidate sets and propensities on the legacy Today queue and the staged P2 path; "continue" logged as a candidate; probe near-ties admitted to `epsilon_tiebreak` with logged propensity (closing `scheduler.py:1544-1551`) | R0; after Slice A Phase 6 merges (same files) | Logging tests; no serving change except the probe tie admission (successor + kill switch) |
| **R2: router live for the daily plan** | `LearnerStateCardV1`; `decision/context` embeddings and retrieval; the Decider request; the three modes and `decider_mixture`; `router_decisions` / payloads / outcomes; the staged frame composing Today's plan blocks (the P4 cutover extended from P2 runs to Today); the learner-facing "why" | The daily loop's finite plan (P1–P3, Q9); R1 | Algorithm successor with kill switch `router.enabled`; G1–G9 (§12) |
| **R3: first replay report** | `learnloop router report`; switching per §10.4 | 200 decisions | Owner reads the report once |

---

## 12. Gates and tests

| # | Gate |
|---|---|
| G1 | **Hard rules hold:** no sampled or Decider-chosen candidate is ever infeasible. A fake Decider that puts all its mass on an infeasible id cannot select it |
| G2 | **Irreversible actions are never sampled** (§7.1), asserted on a fixture with a terminal-assessment candidate |
| G3 | **Propensities are exact:** the logged propensity equals the sampling distribution, seeds reproduce draws, and every candidate in `decider_router` has at least ε_min |
| G4 | **Restraint asymmetry:** `intervene_now` can block but never force an interruption |
| G5 | **No leakage:** the card has no cold-answer or reserved-surface material, and similar decisions include only outcomes matured before the decision |
| G6 | **Replay:** zero Decider calls on rebuild; `router_outcomes` rebuilds deterministically |
| G7 | **Fallback:** timeouts, errors and spend caps fall back to the staged choice, flagged on the receipt |
| G8 | **Kill switch:** with `router.enabled = false`, Today matches the pre-router version on fixture copies |
| G9 | **Learner pick wins**, and is logged without a propensity |

**Tests:**
- the client against a fake Decisions endpoint (request shape, the 400 on unknown fields, typed parsing);
- card determinism and budget truncation;
- the retrieval maturity filter;
- each mode's sampling;
- the DR estimator on a synthetic logged policy with known value.

---

## 13. Deferred, with triggers

| Deferred | Revisit when |
|---|---|
| **A learned action scorer** (frozen or fine-tuned embeddings, LoRA; the Qwen-LoRA proposal) | All four hold:<br>1. R2 is live with exact propensities;<br>2. ≥ 500 decisions with matured `R_cold`, and ≥ 50 randomized observations for each of ≥ 3 block types;<br>3. Slice 2 T8 shows embeddings add held-out predictive value;<br>4. Decider-argmax beats staged on DR `S`, so a cheaper learned version has a measured gap to close |
| **Item-level routing by the Decider** (within a block) | R3 shows block-level gains and the within-block transparent selectors are the measured bottleneck |
| **Affect sensors** (fatigue, frustration) | P4 U-011's affect stream is wired into the snapshot |

---

## 14. Open decisions

| # | Decision | Recommendation |
|---|---|---|
| D1 | Launch mode | `decider_router` with λ = 0.5 (live; both policies keep support) |
| D2 | Switching margin for §10.4 | Fixed before the first report at 0.03 in mean `S` |
| D3 | `router.k` (candidates shown) | 6 |
| D4 | Route: Perplexity direct or OpenRouter | Direct, until OpenRouter's typed-answer support is verified |
| D5 | Local hosting of the open weights | Not now. Revisit if API cost or availability becomes a problem; it would be evaluated as its own model id |
| D6 | Privacy | Learner text goes to Perplexity. The owner checks the retention terms before R2 |
| D7 | Label when the Decider chose | "LearnLoop's model picked this among N close options" |
| D8 | Card budget | 16K tokens; revisit after the harness V3 results |

---

*Related: `spec_p4_controller_and_scale.md` (§4, §7.1 revised here, §9.3 extended here) · `spec_learner_field_v1.md` §7.2 · `daily_loop_frictionless_defaults.md` · Pipeline Augmentation Plan §B · Bitter Lesson Research Sweep §4*

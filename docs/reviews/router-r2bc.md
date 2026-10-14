# Router R2b + R2c: both models live, the mixture, restraint, sensors, retrieval

**Stage:** router R2, sub-stages B and C together (`docs/specs/plan_router_r2_v1.md` §9: R2c "lands with R2b under one successor"), owner-directed 2026-10-13.
**Branch:** `router/r2bc`, base main `28c6040ca` (R2a landed as `mvp-0.23`, migration 202). Main has since moved to `56579d271` (RW3a); this branch was not merged with it.
**Successor:** `mvp-0.24` (placeholder, relabelled at its merge), chained after `mvp-0.23` with the chain's notes passed through (T1's guard advisory).
**Migration:** none. Every column R2b and R2c write was reserved by R1 (migration 181), and R2a's rebuild already admitted `plan_interrupt`.
**Kill switches:** `router.mode = "staged"` (R2a exactly, no model asked), `router.restraint = false` (a follow-up always joins the current block), `router.enabled = false` (`mvp-0.22`'s plan).
**Pause:** the owner paused this stage on 2026-10-14 (about 02:20 to 09:00) part-way through the implementation; it resumed from the uncommitted work, which was kept and finished.
**Codex review (2026-10-14):** eight findings (two High), all fixed: `docs/reviews/router-r2bc-codex-review.md`. The statements below that the fixes changed are corrected in place and marked "(review F*n*)".

## Summary

R2b and R2c make the router's two models live on Today, behind one logged mixture:

1. **The mixture** (`model_mixture`, `router_mixture_v1`). At each plan boundary the staged rule's pick (R2a's `staged_v1`), the Decider's `choose_block` distribution and the router LLM's distribution are mixed over the top-k reversible candidates with a floor for each: π = (1 − kε)(w_s·δ_staged + w_d·p_decider + w_l·p_llm) + ε. The draw is two-stage and seeded, its propensity is exact and recomputable from the row (G3), and a model that times out, fails, answers outside its contract or is refused for spend gives its weight to the rule, with `fallback` recorded (G7). The floor stays on a full fallback (owner Q7).
2. **Off the hot path.** The models are asked in background threads, keyed by the boundary's state. A read (Today's open, the feedback after a block's last answer) never waits: the plan says the block is being chosen and the view polls. A serving step (Begin, Continue) waits at most `router.timeout_seconds` (8 s), then the rule takes the missing shares. The models have `router.prefetch_timeout_seconds` (45 s) from the first prefetch.
3. **Spend.** A $5/day guard on metered router spend (owner, 2026-10-13), admitting every physical request (a retry, a JSON repair and the query embedding included) in its own start receipt (review F3-F5); Codex on the subscription is uncapped. The router LLM's output room is the shared output-budget policy and never below 16,384 tokens (owner).
4. **What is kept.** Both models' requests and raw answers are stored beside the decision with the card; the row carries the weights, both distributions, the sensors, the model ids, latency and cost.
5. **The why.** Plain words by the component that drew: the rule's own sentence; "LearnLoop's model picked this among N close options." for the Decider; the LLM's own rationale, marked ◇, only when the guard passes (plain words, at most three sentences, no probabilities, every cited answer on the card) and the drawn block is the one the LLM favours, which its rationale explains (review F7); "Picked to vary the order today." for the floor. The details line says who drew, which model didn't answer and why, the chance, and the receipt (`learnloop router log --decision`).
6. **R2c.** A placeable mid-block follow-up is a `plan_interrupt` decision (join now or wait for the next block) from each model's `intervene_now` P(yes), with no hand-set threshold, after the P4 constraint engine has checked it. Both models' `teach_first` and `will_pass_next` sensors are logged only. Graded teach-back dialogues are summarized into the card's typed evidence after grading. Similar past decisions (`decision/context` embeddings) are retrieved for every decision when embeddings are on, matured and from another session only, and shown to the models on a logged random half.

The fail-first tests failed on the base and pass now (§Fail-first). The gate is green (§Gate). The manual runs and the live session are in §Manual runs and §Live session.

## Owner decisions built to

| Decision | Where |
|---|---|
| D6 recorded (2026-10-13): Perplexity's terms accepted, the Decider may see card text | disclosures go live at `mvp-0.24` (`ai/disclosures.py`); R2b's merge precondition met |
| Router LLM output room at least 16,384 tokens (the shared output-budget policy; never below) | `router_runtime._llm_budget` = max(16,384, `output_budget(config, "router_llm")`); a truncation retries once at double, admitted like the first |
| The router LLM route resolves to the active provider (Codex on the subscription) by default (Q4) | `router_llm` left unset: `provider_for_task` resolves the active provider; on the owner's vaults that is `codex` (`codex_sdk`) |
| Staged mode stays deterministic; exploration only from the mixture's floor (R2a open question 1) | `router.mode = "staged"` is R2a's `staged_v1` exactly and asks no model |
| One shared successor for R2b + R2c (Q3), placeholder label, chained after `mvp-0.23`, notes passed through, T1 guard advisory; `router.enabled` and `router.mode` with `mixture` the new default | `ROUTER_MIXTURE_ALGORITHM_VERSION = "mvp-0.24"`, `router_mixture_upgrade.upgrade_to_mvp024`, `RouterConfig.mode` default `"mixture"` (dormant below `mvp-0.24`) |
| $5/day metered router guard; subscription routes uncapped; the OpenRouter key limit as the backstop | `router.max_daily_cost_usd = 5.0`, `RouterSpend` |
| Exploration copy: "Picked to vary the order today" (Q12) | `router/why.py::PICKED_TO_VARY` |
| Restraint as a logged mixture, no 0.3 threshold; the floor kept on a full fallback (Q7) | `RestraintGate` |
| Retrieval with a logged 50% inclusion coin (Q8) | `router_retrieval.include_coin` |
| The first block decided at Today's open (Q9) | `TodayScreen` prefetch (below) |
| Run the constraint engine on follow-ups inside the restraint decision (R2a open question 2) | `RestraintGate.refusals`, mid-block and (new here) the end-of-block forced path |
| Frictionless plain copy, no jargon | the why and details copy pass the deny-list (`test_every_mixture_why_is_plain`, `test_every_details_line_is_plain`) |

## Code truth at stage start

The base is main `28c6040ca` with R2a landed. The plan's seams held:
- `decide()` still runs the chooser before the block's transaction opens (`daily_plan/engine.py::decide`, `:1313`), and the `plan_block` logger writes in the block's own transaction (`router/plan_log.py`).
- R2a's `BlockChoice.router_record` carries the chooser's record to the logger; R2b fills it (no chooser ever writes).
- `router_decisions` already had every R2 column (`mixture_weights_json`, `model_distributions_json`, `sensor_answers_json`, `question_set_version`, `model_ids_json`, `similar_decision_ids_json`, `latency_ms`, `cost_usd`) and a `decision_kind` CHECK admitting `plan_interrupt` (R2a's rebuild). No migration was needed.
- `_insert_followups` (`engine.py:2071`) is still the plan's one mid-block interruption.
- `ai/decisions.py` (the typed `ChoiceQuestion` / `NoulQuestion` contract, strict parsing) and `ai/providers/decider.py` (no chat fallback, `/alpha/decisions`, a 30 s default timeout) were as R0 and the Decider migration left them.

## What was built

### Requests (`router/requests.py`)

- **Decider, `router_qs_v1`:** `choose_block` as a `ChoiceQuestion` over the options (the top-k reversible candidates, plus `stop for today` when the plan offers it). Each option is one plain sentence: the rule's reason, kind, item count, minutes and topics; never a stem.
- **`router_qs_v2` (R2c):** adds `teach_first_<lo>` and `will_pass_next_<lo>` `NoulQuestion`s for at most three learning objects of the options (`router.sensors`). Logged only.
- **Restraint, `router_restraint_v1`:** one `intervene_now` noul.
- **LLM, `router_llm_v1` / `v2` / `router_llm_restraint_v1`:** one structured answer: a probability per option id (renormalized; a missing id is 0), at most three plain sentences of rationale, and the evidence ids it relies on (the card's recent attempts and teach-back summaries, listed with plain labels). The prompt names the copy rules.
- **Strict parsing** (`RouterResponseInvalid`): an option id that was not asked, a repeated id, a probability that is not finite in [0, 1], no mass, a sensor for a topic not asked. The model's share then goes to the rule (G1/G7). The rationale is judged by the why guard, not the parser.
- The state both models read is the stored card's text plus the options, the similar decisions when the coin says so, and the citable answers.
- Import-linter: `learnloop.router` may not import `learnloop.ai`; two exceptions are scoped to `router.requests`: `ai.decisions` (pure dataclasses) and `ai.schemas` (the pure-pydantic `WireModel` base the structured transports require). No router module reaches a client, so replay still cannot.

### The mixture (`router/mixture.py`, `scheduling/randomization_layer.py`)

- A leaf module: `effective_weights` (normalized; a failed model's weight to staged), `component_distributions`, `mixture` (π), the seeded two-stage `draw` (first uniform: the floor branch with probability kε, else a component by weight; second: a candidate from that component, in support order), and `recompute` (G3 from the row alone).
- `model_mixture` is the randomization layer's fourth admissible design (`ADMISSIBLE_DESIGNS`) and is in the ledger's `ROUTER_DESIGNS`. Its floor is `router.epsilon_min`; the dormant 0.05 `PROPENSITY_FLOOR` never clips it.
- The row's `design` and `seed` are set when the propensity is exact; candidates outside the support (or irreversible) are logged with propensity 0, the support's candidates with their exact π.

### The chooser (`daily_plan/router_chooser.py::RouterChooser`)

1. It starts from R2a's staged rule (`StagedChooser`, unchanged).
2. **Irreversible first** (G2): an irreversible staged pick is chosen deterministically, no model asked (`decided_by = irreversible`).
3. **Top-k** (`router.k = 6`) in the plan's deterministic order: the rule's pick, each lane's best remaining, the rest by the lane-quota key, then `stop for today` when offered. `router.ties_only` keeps only the rule's lane.
4. **Readiness:** with no model set up the rule chooses deterministically (`decided_by = not_ready`); nothing is explored without a model. One option: `single_option`.
5. **The boundary key**: a hash of the plan, the state the chooser saw, the support (each candidate's logged row), the staged pick, the newest attempt, the version, the router settings and which models are ready. The prefetch is cached per key (`RouterRuntime`, 64 entries).
6. **The draw**, seeded by `seed_for(key, decision id)`; the decision id is the row's id.
7. **The record**: the mixture's support, staged pick, k, ε, effective and configured weights, uniforms, π, each model's status / model / latency / cost / error, the similar-decision record, the rationale and its guard result, the sensors, the payloads and the card. The `block_chosen` receipt carries a summary (`decided_by`, `drawn_component`, `option_count`, `fallback`, `fallback_reasons`, `rationale_hidden`, `evidence_labels`).

### The runtime (`daily_plan/router_runtime.py`)

- `RouterRuntime` (process-wide in the sidecar): the prefetch cache, the model source and the spend guard. Each decision's models run in daemon threads (the Decider and the LLM in parallel); `inline` runs them on the caller's thread (tests, scripted runs).
- **Timing.** A chooser built for a read (`serve = false`) raises `DecisionPending` while its models are out; the engine leaves the boundary open (`build_plan`, `advance_with_context`), and the view says `deciding`. A serving step waits up to `router.timeout_seconds`. After `router.prefetch_timeout_seconds` from the first prefetch a model still out is a timeout. A late answer is ignored.
- **Readiness** (`RouteModels.readiness`): a route whose provider is not set up is `not_ready` and never asked. The Decider's endpoint is confirmed by OpenRouter's free model listing once per process (an hour's cache) before its first paid call; an unlisted endpoint is `unreachable`. `LEARNLOOP_ROUTER_MODELS=off` makes both routes not ready (the test suite's default, set in `conftest.py`).
- **Spend** (`RouterSpend.metered`, corrected by review F3-F5): every router model call runs under the shared request gate, which prices EACH physical request (a transport retry and a JSON repair included, and the prefetch's query embedding); its start receipt is written with the estimate (`budget_json.router_reserved_usd`) in one write transaction that checks today's (UTC) guarded receipts plus the estimate against `router.max_daily_cost_usd`. Past it the request is refused before it is sent and the model's share goes to the rule (`spend`). A receipt that reported no usage counts its reservation. A subscription request is never capped (its tokens are estimated on the receipt). The Decider's estimate is its input-only price ($0.02 per million input tokens) on the whole request body; the LLM's is prompt plus output room at the route's price.
- **Receipts:** every request is a `model_call` owned by `router_decision` (`router_teach_back_summary` for summaries), labelled `judge`, `question_set_version` and `state_hash` (the card's hash).
- The Decider client takes a per-call `timeout_seconds` (the decision's remaining budget) instead of its 30 s profile default.
- **The Decider never falls back to a chat model**: its route accepts only decision profiles (`ai.routing.DECIDER_TASKS`), and the router asks it through its own route only; its failure moves weight to the rule (`test_the_deciders_route_never_resolves_to_a_chat_model`, `test_a_failed_decider_is_never_answered_by_the_llm_in_its_place`).

### The restraint (`RestraintGate`, R2c)

At `_insert_followups`, for each pending follow-up of the current session:
1. **Placement first.** Only a follow-up DL1's rules would place now (`_displacement_plan` finds room) is decided at all; the models can make waiting likelier, never force an interruption the rules would not place (G4). Pending follow-ups are decided one at a time, each against the plan the earlier decisions left, and every logged decision is exactly the placement written (review F6).
2. **The constraint engine** (R2a open question 2): the staged frame's material for the item. A refused follow-up is declined deterministically (`decline`, named reasons in `exclusions_json.named`), logged once, and never placed in that plan.
3. **The mixture** over `insert_now` (the rule's choice) and `continue_current` (wait: the follow-up is forced into the next block), from each model's `intervene_now` P(yes), with the same weights and floor. No threshold. Waiting is offered only when the boundary keeps room for the follow-up after the current block; otherwise it joins now with no model asked (`no_room_to_wait`). A waiting follow-up's minutes and item slot are kept for it and it is placed first at the boundary, in that room (review F8).
4. **The row** (`plan_interrupt`): candidates `insert_now`, `continue_current`, `decline` with their propensities; `chosen_practice_item_id` only when it joins now. The follow-up's `item_planned` event carries the decision's id. A deferred or refused one is a `followup_deferred` / `followup_refused` event on the block.
5. **No model ready:** a placeable follow-up joins deterministically (`policy = staged_v1`).
6. **Added in this resume** (commit `569fd62a0`): a follow-up that appears when no block is current (the answer that ended a block produced it, or a reading block is current) used to be forced into the next block without the constraint check. Now a refused one is declined by name on the block whose answer produced it, once.

`router.restraint = false` removes the gate: DL1's follow-up rules alone (`test_with_the_restraint_off_a_follow_up_joins_as_in_r2b`).

### Sensors (R2c)

`teach_first_<lo>` and `will_pass_next_<lo>` for at most three learning objects of the options, asked of both models (`router_qs_v2` / `router_llm_v2`), stored in `sensor_answers_json`, never used to select (`test_the_sensors_are_logged_and_never_select`). `router.sensor_source = "decider"` names the restraint's sensor of record. The agreement adapter reports them as `router_teach_first` / `router_will_pass_next` tasks.

### Teach-back summaries into the card (`daily_plan/router_teach_back.py`, R2c, spec §15.1)

- After the teach-back RPC records the graded dialogue, a daemon thread summarizes it on the router LLM's route: what was explained correctly, what was missing or wrong, a few of the learner's words. Inputs are the transcript, the topic and the grade's result word; never a rubric, reference answer or source text. Exam or reserved material is never summarized (the card's own withholding rule).
- A grade held for review is never summarized, and a summary is read into a card only while its attempt is not held and its grading revision is current (review F2).
- Stored once per attempt and grading revision in `model_work_checkpoints` (WORKFLOW; key `router_teach_back_summary:v1:<attempt>:<revision>`); replay never reads it.
- The card gathers the summaries for its learning objects made before the decision into `evidence_sections.teach_back_summaries` (R2a's typed-evidence hook) and renders them; the LLM may cite them as evidence.
- Under the router's daily guard (owner `router_teach_back_summary`); acts only where the mixture serves (`router.teach_back_summary`, on).

### Retrieval (`daily_plan/router_retrieval.py`, R2c)

- **The record** `decision/context`: a canonical rendering of the decision's typed state read from the card it stored (plan kind, re-entry, time-left and absence buckets, each option's kind, topics, reason and reversibility, each topic's status and bucketed predictions, the open problems). No ids, no times.
- **When it embeds:** the current decision's context is embedded in its prefetch job (it is also the query), admitted by the daily guard like the models' requests (review F3), and the vector is written after the decision, in the block's transaction (its own savepoint). `learnloop router embed-decisions` backfills decisions without one through the shared embedding backfill, under its enforced caps and both embedding switches (`--dry-run` prices the run and sends nothing; review F3).
- **What may be shown** (G5): a past decision made before this one, in another session and another plan, whose R_next or R_cold attempt was made before this decision. Outcomes are derived on the fly (`derive_router_outcomes`, the `router log` derivation), never read from the `router_outcomes` cache.
- **Ranking:** mean-centred cosine (`embedding_vectors.retrieve`) among the matured candidates, top `router.similar_k` (6).
- **The coin:** seeded by the boundary key; with probability `router.similar_include_rate` (0.5) the models see the similar decisions (one plain line each: the options count, what was chosen, with what chance, and what followed); otherwise they are retrieved and logged but withheld. The row's `similar_decision_ids_json` holds the ids shown.
- **Gating:** `embedding.enabled` and `router.similar_decisions`; otherwise a logged no-op (`similar.status = disabled`). An embedding failure is logged (`unavailable`) and never blocks.
- **Replay never needs a vector** (G6): the ids are on the row.

### The agreement adapter (`router/agreement.py`)

`learnloop decider agreement` adds the router's decisions from the vault's `router_decisions` as ledger-shaped rows: `router_choose_block` (each model's argmax with its distribution), the sensors and `router_intervene_now` (yes at P ≥ 0.5). A Decider that did not answer is an `unavailable` / `refused` / `failed` row, so the report's fallback counts apply. Nothing is duplicated into `judgment_ledger`.

### Disclosures, readiness, health

- `ai/disclosures.py`: the router routes' text says what is sent from `mvp-0.24` in `mixture` mode (the card, the options, similar decisions on about half the choices, the teach-back summarizer) and what never is.
- The Settings health chip counts `router_decider` / `router_llm` (as resolved) once the mixture serves and models are not switched off (`learnloop_sidecar/context.py::_settings_ready`).

### Frontend (`apps/learnloop-tauri`, one behaviour change)

- `DailyPlanBodyDto.deciding` and `step: PlanStepDto | null`.
- `TodayScreen`: while the plan says its next block is being chosen, Today reads the plan again every 1.5 s (at most 40 reads), so the chosen block appears without a click. Opening Today is the first block's prefetch (the plan read starts it).
- `DailyPlanView`: "Choosing the next block…" with a Begin button, which serves at once (waiting at most 8 s for the models).

### Versioning, config and CLI

- `mvp-0.24` in `SUCCESSOR_CHAIN`, `ROUTER_MIXTURE_VERSIONS`; `upgrade_to_mvp024` (from `mvp-0.23`, or `mvp-0.9`–`mvp-0.22` through `upgrade_to_mvp023`, notes passed through, refusals prefixed). `learnloop upgrade` defaults to it; new vaults start at it.
- `[router]` modelled keys (out of the template): `weights` (⅓ each), `k` 6, `epsilon_min` 0.02, `ties_only` false, `timeout_seconds` 8, `prefetch_timeout_seconds` 45, `max_daily_cost_usd` 5.0, `sensors` true, `sensor_source` decider, `restraint` true, `similar_decisions` true, `similar_k` 6, `similar_include_rate` 0.5, `teach_back_summary` true; `k · epsilon_min < 1` is validated. Parameter-registry rules classify the weights, k, ε and the coin rate as decision shaping weights and the budgets as operational.
- All sixteen defaults snapshots recomputed (template `.pyc` cleared); the CLI help snapshot regenerated.
- `learnloop router log --decision ID` prints one decision's receipt in full (candidates, weights, both distributions, sensors, similar ids, seed, the stored payload kinds); `learnloop router embed-decisions [--dry-run] [--limit]`.

## Deviations from the plan, and decisions made here

1. **Budgets (owner overrides).** The plan's Q5 (4,096 output tokens) and Q6 ($1/day) were overridden: the LLM's output room is never below 16,384 tokens and the guard is $5/day.
2. **Where the chooser lives.** The plan named `router/chooser.py`; the chooser and its runtime live in `daily_plan/router_chooser.py` and `daily_plan/router_runtime.py`, because `learnloop.router` is a leaf package forbidden from importing `learnloop.ai` (import-linter). The pure parts (`router/requests.py`, `router/mixture.py`, `router/agreement.py`, `router/why.py`) stay in `router`.
3. **`staged` mode asks no model.** Plan §3.3 item 8 had `staged` mode still asking both models for logging. That is a shadow ask (the owner's principle, and spend for nothing served), and the owner kept staged deterministic: `staged` is R2a exactly.
4. **No exploration without a model.** With neither model set up the rule's pick is deterministic (p = 1), not π = (1 − kε)δ + ε. The floor is kept when models are set up but fail (Q7). Exploration exists to compare the models; with none, a random draw would only perturb DL1's order.
5. **Reads never wait.** The plan had Begin waiting 8 s for the first decision. Here every read leaves the decision open (`DecisionPending`) and Today polls; only a serving step waits. A read that finds the models answered decides the block (and writes it) in that read.
6. **Spend reservation (superseded by review F3-F5).** This stage first kept the reservation in memory. It now follows the plan's pointer, the reader's atomic reservation in the start-receipt observer: each physical request's estimate is written in its start receipt in the transaction that checks the cap, so a restart or a lost finish never frees it. Late answers after a timeout are still paid and counted in the guard.
7. **Retrieval derives every decision's outcome.** The plan derived outcomes for the shortlisted decisions only; `_matured` derives them for the vault (as `router log` does) and filters. It runs in the prefetch thread; its cost is measured below.
8. **Teach-back summaries need no migration:** `model_work_checkpoints` holds them.
9. **The restraint's forced path** (item 6 of the restraint section) closes a gap the mid-block check left.

## Found and fixed in this resume (review, manual runs, live session)

| Commit | Finding | Fix |
|---|---|---|
| `bf51a51a9` | The details line cites `learnloop router log --decision ID`, which did not exist | `router log --decision` prints the one decision's receipt in full (`test_router_log_shows_one_decisions_receipt_in_full`) |
| `569fd62a0` | With the restraint on, a follow-up appearing when no block is current (the answer that ended a block produced it, or a reading block is current) was forced into the next block without the constraint check the mid-block path runs | a refused one is declined by name once, on the block whose answer produced it, and never placed or rechecked in that plan (`test_a_refused_follow_up_is_never_forced_into_the_next_block`) |
| `8d1340b77` | Live session: every real LLM call failed before sending, because the answer models were not `WireModel`s (the strict schema every structured transport sends); the fakes never built that schema | the answer models and `TeachBackSummary` are `WireModel`s; the fake LLM builds the strict schema; a test checks every router answer model |
| `d2f1dc0ab` | The teach-back summarizer read the learner's dialogue in a non-isolated turn, unlike the grader reading the same transcript | isolated, like the router LLM; both pinned by tests |
| `5f9b73939` | Live session: "Next: What Makes a Vector Space?." | a title's own ? or ! ends the sentence |

## Fail-first (plan §9 R2b, R2c)

Written first (commit `ac4edf73f`) and re-run in this resume against the base's source (`git archive 28c6040ca src`, first on `PYTHONPATH`, pytest's `pythonpath` cleared):

| # | Test | On the base | Now |
|---|---|---|---|
| 1 | `test_router_r2b_requests.py::test_a_fake_llm_naming_an_unknown_block_is_rejected_at_parse` (and the file) | collection error: `cannot import name 'requests' from 'learnloop.router'` (no parser exists) | rejected at parse; through the chooser it is a fallback and never chosen |
| 2 | `test_router_g3_propensity.py::test_the_logged_propensity_is_reproducible_from_the_logged_components` | collection error: no `learnloop.router.mixture` | π(chosen) recomputed from the row equals the logged propensity; the seed reproduces the draw; every option ≥ ε |
| 3 | `test_router_g7_fallback.py::test_a_timeout_reaches_the_staged_rule_with_fallback_llm` | collection error: no `ROUTER_MIXTURE_ALGORITHM_VERSION` | the slow LLM's share goes to the rule, `fallback = llm`, the propensity still exact |
| 4 | `test_router_g4_restraint.py::test_a_follow_up_joins_the_current_block_today_and_waits_with_a_decider_near_zero` | collection error (the import); its first half (a follow-up joins the current block at `mvp-0.23`) is DL1's behaviour | with a fake Decider P(yes) = 0 the follow-up waits for the boundary: `continue_current` with propensity 1 − ε = 0.98 exact, and it opens the next block |

The four files hold 23 tests on the branch; all pass.

## Tests added and changed

**New:**

| File | Covers |
|---|---|
| `tests/router_model_fakes.py`, `tests/router_mixture_helpers.py` | fake Decider / LLM / embeddings (recording, gated, failing on demand), the fake model source and runtime; a routed plan env at the successor |
| `tests/test_router_r2b_requests.py` | fail-first 1; every router answer model (and the summary) has the strict schema the transports send; renormalization and missing ids; malformed distributions fail closed; the Decider's typed questions and a body with no unknown field; sensors name only asked topics; the LLM prompt's options and copy rules |
| `tests/test_router_g3_propensity.py` | fail-first 2; a failed model's weight to the rule; the two-stage marginal equals π |
| `tests/test_router_g7_fallback.py` | fail-first 3; an error or an invalid answer falls back |
| `tests/test_router_g4_restraint.py` | fail-first 4; restraint off equals R2b; models agreeing to interrupt (the decision id on the `item_planned` event); the models never force a follow-up the rules would not place; a refused follow-up declined by name, mid-block and (new) after a block's last answer; no model set up joins deterministically |
| `tests/test_router_r2b_serving.py` | G1 (a Decider naming an option not asked), G2 (an irreversible block is never an option), G9 under the mixture; payloads (card, both requests, both raw answers); `router log --decision`; the router LLM asked in an isolated turn; sensors logged only; `router_qs_v1` without sensors; staged mode at the successor is R2a and asks no model; no model set up; the suite's routes ask no model; a read leaves the decision open and a serve decides it; a serve waits at most the timeout; the Decider never resolves to or falls back to a chat model; the daily guard refuses metered calls and never a subscription call, and counts today's router receipts; every why and details line plain; the rationale guard; a drawn LLM pick showing its rationale and cited answers; G8 at the successor on backup copies of the three working fixtures |
| `tests/test_router_r2b_agreement.py` | the router's decisions feed the agreement report; a failed Decider is a fallback there; replay never asks a model |
| `tests/test_router_r2c_retrieval.py` | G5 maturity (only matured, another session and plan); the coin seeded, logged and at its rate; disabled is a logged no-op; each decision embeds after the decision and logs the coin; the context text has no ids or times; G6 replay never needs a vector; the backfill dry-runs then embeds what is missing; a matured decision from an earlier day is shown |
| `tests/test_router_r2c_teach_back.py` | a graded teach-back summarized into the next card in an isolated turn; the summarizer never sees a rubric or reference answer; exam or reserved work never summarized; summaries only where the mixture serves |
| `tests/test_mvp024_upgrade.py` | the successor's chain, gates and switches, the restraint's own switch, upgrade paths and notes, refusals, the CLI default, new vaults, fingerprints, the floor validation, the head-fixture path |

**Changed:** the earlier successors' vocabulary tests (`mvp-0.24` is the latest); `conftest.py` (`LEARNLOOP_ROUTER_MODELS=off`); the disclosure assertions in `test_judge_routes.py` and `test_tier1_decider.py`; `test_recurrence_commands.py` and `test_route_rules_in_grader.py` (latest-version pins); `test_router_why_copy.py` (a title's own mark); the CLI help snapshot; the frontend's `DailyPlanView.test.tsx` (the being-chosen state and its Begin).

## Migrations

None.

## Manual runs (backup-API copies under `fixtures-local/r2bc/`)

**Setup.** Backup-API copies (`copy_tree_with_databases`) of this worktree's tracked `linear_algebra`, `probability` and `arxiv_v2` (all at `mvp-0.8`) were made under `fixtures-local/r2bc/base/`, migrated on open (to 202), and upgraded `mvp-0.8` → `mvp-0.9` → `mvp-0.23` (`upgrade_to_mvp023` through the chain; four advisory-guard notes each; about 990 s each under the machine's load). Every arm below is a further backup copy of a base. The fake-model runs used an empty `LEARNLOOP_CONFIG_DIR`. No tracked fixture was opened except to copy it, and `git status fixtures/` is clean. The scripts are in the stage's scratchpad (`r2bc/prep.py`, `sessions.py`, `shadow3.sh`, `shadow_summary.py`, `retrieval_check.py`, `live.py`).

### 1. Upgrade, then `rebuild --shadow` (playbook item 7)

On `linear_algebra`: `rebuild-derived-state` three times to the fixed point at `mvp-0.23`, then shadowed; `learnloop upgrade` (the default target) to `mvp-0.24`, shadowed again.

| | Facet | Mastery | Schedule |
|---|---:|---:|---:|
| `rebuild --shadow` at `mvp-0.23` | 0 | 0 | 0 |
| `rebuild --shadow` at `mvp-0.24` | 0 | 21 | 0 |

The 21 mastery rows differ only in `algorithm_version` (`mvp-0.23` → `mvp-0.24`), as at every successor: no delta beyond the version labels. `learnloop doctor --json` at `mvp-0.24`: 106 issues, one error (the fixture's missing `rubrics` directory, as at R2a), none about the router or the plan.

### 2. Twenty seeded sessions per fixture and arm

**Arms** (each its own copy of the base):
- **A**: `mvp-0.23` (R2a);
- **S**: `mvp-0.24` with `router.mode = "staged"` (the kill switch);
- **M**: `mvp-0.24` with the mixture and fake models: a Decider putting 0.6 on the last option and P(intervene now) = 0.3; an LLM favouring the second option, citing the first answer it may cite, P(intervene now) = 0.6; deterministic fake embeddings with `embedding.enabled` on.

**The sessions.** One a day from 2026-10-15, through the sidecar RPCs (`next_plan_item` serving with a fixed session id; the real scheduler build and plan engine), with deterministic synthetic answers (70% correct) written as raw attempt rows bound to their presentations, and no grading model. After a wrong answer, one cold-retry follow-up per session was seeded on the same topic, as remediation would, so the restraint meets real follow-ups.

| Fixture | Blocks A / S | Sessions identical, A and S | M: mixture decisions (deterministic: irreversible, one option) | M: drawn staged / Decider / LLM / floor | M: G3 max error | M: options below ε | M: restraint (join / wait / decline) |
|---|---|---:|---|---|---:|---:|---|
| linear algebra | 105 / 105 | 20 / 20 | 70 (19, 17) | 18 / 29 / 19 / 4 | 0.0 | 0 | 3 / 1 / 0 |
| probability | 115 / 115 | 20 / 20 | 79 (20, 23) | 18 / 31 / 23 / 7 | 0.0 | 0 | 0 / 1 / 1 |
| arxiv v2 | 185 / 185 | 20 / 20 | 168 (0, 17) | 50 / 51 / 56 / 11 | 0.0 | 0 | none seeded |
| **total** | **405 / 405** | **60 / 60** | **317** (39, 57) | 86 / 111 / 98 / 22 | **0.0** | **0** | 3 / 2 / 1 |

- **Kill switch:** `router.mode = "staged"` at `mvp-0.24` served `mvp-0.23`'s block sequences exactly, in every session, follow-ups included.
- **G3 on real data:** every mixture row's propensity was recomputed from the row alone (support, staged pick, ε, effective weights, both distributions): 317 / 317 exact, maximum error 0.0. Every support candidate's logged propensity was at least ε.
- **The decline** on `probability` was a seeded follow-up the constraint engine refused under `active_status` (`card_inactive`): logged by name, nothing asked of a model.
- **The why** when the LLM drew: its rationale was shown 98 / 98 times (the fake's text passes the guard), with its cited answer as a label.
- **The inclusion coin:** shown on 147 of 317 decisions (46%), withheld on 170.
- **Serving latency** (`next_plan_item` with serve, inline fake models, so no network): p50 0.61 / 0.56 / 0.76 s on M against 0.56 / 0.46 / 0.55 s on S; p90 1.03 / 0.92 / 1.13 s against 0.95 / 0.76 / 0.70 s. The difference is the card's build, the requests and retrieval.
- **Payload sizes** (`linear_algebra`): the card's text and JSON median 21.8k characters, the Decider's request 12.3k, the LLM's 11.0k.
- No follow-up could be seeded on `arxiv_v2` (no unattempted active item on the same topic).

### 3. Fallback on real data (arm F)

`linear_algebra`, six sessions, `timeout_seconds = prefetch_timeout_seconds = 1`, the models in background threads, the fake LLM 2.5 s slow on every third call: 20 mixture decisions, 7 with `fallback = llm` (the slow calls), G3 exact on all 20, no option below ε, 3 restraint decisions.

### 4. Retrieval maturity on real data (G5), no model call

In the M arms no past decision ever matured: the synthetic answers carry the column default `evidence_origin = 'unknown'` (so do the fixtures' own 70 older attempts), and router outcomes count only human-origin attempts. Retrieval correctly showed nothing, but that left the maturity filter unexercised. So on each M copy and the live copy (below) the simulated learner's answers were marked human-origin, and retrieval was rerun for every logged decision against its own stored context vector (`retrieval_check.py`):

| Copy | Decisions with a vector | With similar decisions | Similar decisions returned | Violations (not earlier, same session, same plan) |
|---|---:|---:|---:|---:|
| M linear algebra | 70 | 65 | 371 | 0 |
| M probability | 79 | 76 | 448 | 0 |
| M arxiv v2 | 168 | 166 | 945 | 0 |
| live copy (real `qwen3-embedding-8b` vectors) | 51 | 45 | 253 | 0 |

Retrieval itself (the on-the-fly outcome derivation, the filter and the ranking) took a median 0.011 s (max 0.064 s) on the largest copy.

## Live session

**Copies.** Two backup copies of the `linear_algebra` base at `mvp-0.24` (`fixtures-local/r2bc/live/` and `live-dry/`), each with eight history sessions (2026-10-05 to 2026-10-12) played with fake models (47 and 48 plan decisions with stored cards), then `router.max_daily_cost_usd = 2.0` and embeddings turned on with the owner's profile (`routing.embedding = "openrouter_embedding"`, the `openai_embedding` profile on OpenRouter, `[embedding] enabled` and `backfill_enabled`). The app loaded its own keys; no settings file was read here.

**Dry run first** (on `live-dry`, nothing sent):
- routes as the app resolves them: `router_decider` → `openrouter_decider` (ready), `router_llm` → `codex` (the active provider, ready), `embedding` → `openrouter_embedding` (ready);
- the Decider's free endpoint listing: reachable (Perplexity, 262,144 context), $0.02 per million input tokens;
- one boundary's requests, captured by fakes that fail every call: the Decider's state about 4,944 tokens with 7 questions (`choose_block` and six sensors), estimated $0.0001; the LLM's prompt 13,099 characters (about 3,300 tokens);
- `learnloop router embed-decisions --dry-run`: 47 decisions pending, about 9,600 tokens.

**Backfill:** 47 and 48 vectors, two calls per copy (8,655 and 9,023 tokens, $0.00009 each).

**Attempt 1** (`s_live`, the app as built): every Codex call failed before it was sent: `TypeError: RouterLLMAnswerV2 is not a WireModel`. The real structured transports send the result model's strict schema, which only a `WireModel` has; the fakes never built it. Fixed in `8d1340b77` (the answer models and `TeachBackSummary` are `WireModel`s, and the fake LLM now builds the strict schema, so the suite enforces it). The Decider answered every decision (0.7–1.6 s); the LLM's share went to the rule (`fallback = llm`).

**Attempt 2** (`s_live2`, after the fix): Codex failed in 0.4–0.7 s with `AIProviderUnavailable: Codex process closed stdout. stderr_tail=Error: invalid transport in mcp_servers.code-review`. A trivial probe on the same route confirmed it is the machine's Codex setup, not the router: a non-isolated turn answered in 7.0 s, an isolated turn failed in 0.4 s. An isolated turn disables every configured MCP server by name, and this host's Codex rejects that override for its `code-review` server. The blind grader uses the same isolated turns (open question 1). The router fell back to the Decider and the rule, as designed. The teach-back summary, then not isolated, succeeded (9.9 s); `d2f1dc0ab` makes it isolated like the grader.

**Attempt 3** (`s_live3`, on `live-dry`, a fresh day's plan). The shipped configuration (isolated turns) did not pass this session on this machine: the router LLM answered only under the override below (open question 1). **Measurement override:** the scratch script switched isolated turns off (`router_runtime._supports_isolation`), only to measure Codex inside the mixture; the product asks for isolated turns. Today's flow: a read starts the prefetch, reads poll every 1.5 s as the frontend does, the block is decided by the read that finds both models answered, then items are served and answered.

| Decision | Decider | Codex | Query embedding | Decided after the prefetch began | Metered cost | Drawn (propensity) | The learner's why |
|---|---|---|---|---|---|---|---|
| block 1 | 1.75 s | 11.3 s | 0.59 s | 12.9 s | $0.00052 | the floor (0.18) | "Picked to vary the order today. What Makes a Vector Space? and Prove Vector Identities from Scalar Laws again, before it slips." |
| block 2 | 1.53 s | 11.3 s | 0.43 s | 13.2 s | $0.00047 | the LLM (0.63) | "◇ You have answered several recent questions on this idea correctly, but an earlier miss suggests one subtle point is still worth clearing up. Revisiting it now should strengthen the foundation for what comes next." (guard passed; four cited answers, all on the card) |
| follow-up (`plan_interrupt`) | 0.56 s | 5.1 s | n/a | the serve step waited 5.3 s | $0.00008 | the LLM: join now (0.80) | none (it joined) |
| block 3 | 0.96 s | 10.0 s | 0.99 s | 11.5 s | $0.00021 | the Decider (0.62) | "LearnLoop's model picked this among 3 close options. Next: What Makes a Vector Space?." (the doubled mark is fixed in `5f9b73939`) |
| stop | | | | | | the rule | "That's today's time." |

- **Serving steps** took 0.32–0.55 s, except the one that waited for the follow-up's decision (5.3 s, under the 8 s budget).
- **The teach-back summary** (Codex): 6.2 s, stored, and read into the next card.
- **Similar decisions:** the coin showed them on blocks 1 and 3 and withheld them on block 2; none had matured (`evidence_origin`, §Manual runs 4).
- **Cost per decision.** The Decider billed 8,900–27,600 input tokens per block decision ($0.00018–0.00055): the six sensor questions roughly quadruple it, and the pre-call estimate (the state alone) is about 4× low (open question 2). Codex used about 21,000 input and 200–450 output tokens per decision on the subscription (unmetered). A query embedding cost about $0.000003.
- **Latency.** Codex takes 10–11 s per block decision, more than the 8 s a blocking step waits. On Today's prefetch path both models were in by 11.5–13.2 s, inside the 45 s budget, so no fallback; a Begin pressed within about 11 s of opening Today would fall back for the LLM (open question 5).

## Paid calls and spend

All on the backup copies, inside the copies' $2 router guard (the guard's spent-today read $0.0016 and $0.0013 at the end):

| Calls | Count | Tokens | Cost |
|---|---:|---|---:|
| Decider (`openrouter_decider`), block and follow-up decisions | 9 | 4,101–27,640 input each | $0.00282 |
| Embeddings (`qwen3-embedding-8b`): backfills | 4 | 17,678 | $0.00018 |
| Embeddings: query vectors at prefetch | 8 | 1,465 | $0.00002 |
| **Metered total** | | | **$0.0030** |
| Codex (subscription, unmetered): router decisions answered | 4 | about 21,000 input each | n/a |
| Codex: failed before or at launch (attempts 1 and 2) | 5 | none | n/a |
| Codex: teach-back summaries | 2 | about 18,400 input each | n/a |
| Codex: the transport probe (isolated vs not) | 2 | trivial | n/a |

No call was made against a tracked fixture.

## Gate

- **Install:** `uv sync --extra dev --extra mobile` (163 packages) and `uv pip install pypdfium2` (5.14.0). `TMPDIR` was the worktree's `fixtures-local/tmp`.
- **`uv run lint-imports --no-cache`:** 17 contracts kept, 0 broken (rerun after the `router.requests -> ai.schemas` exception: 17 kept).
- **`flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`:**
  - **10872 passed**, 0 failed, 48 warnings (12 min 44 s), on `d1d76645b`, the final code.
  - The run before it, on `5f9b73939`, had 10871 passed and 1 failed: `test_reading_step_switch.py::test_the_reading_step_is_not_a_successor_tag`, a successor-chain pin (the latest is now `mvp-0.24`), moved in `d1d76645b`.
- **`flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`:** **100 passed**, 10772 deselected, 1 warning (1 min 47 s), on `5f9b73939` (the only later change is that test pin, which the lane does not select).
- **Frontend** (`apps/learnloop-tauri`, at `bf51a51a9`; nothing under `apps/` changed after):
  - `npm install`: clean, no lockfile change;
  - `npm run typecheck`: clean;
  - `npm test`: **75 files, 524 tests passed**;
  - `npm run frontend:build`: built (the existing chunk-size warning only).
- **`cargo check`:** not required; nothing under `src-tauri` changed.
- **References:** no schema change. The config gained 16 `[router]` leaves, so `db_generate_reference.py` was rerun and `db_validate_reference.py` reports `errors: []` (321 table notes, 834 effective config leaves; the two prose counts moved from 818 to 834). The CLI help snapshot was regenerated (`router log --decision`, `router embed-decisions`, the upgrade target). All sixteen defaults snapshots (`mvp-0.9` to `mvp-0.24`) equal a fresh `defaults_fingerprint_for_version` with the template `.pyc` cleared.
- **RPC pins** (`tests/test_mobile_allowlist.py`): no RPC was added or changed; unchanged.
- **Targeted runs:** the daily-plan and router files, 368 passed; the four fail-first files, 23 passed (and collection errors on the base's source).

## Open questions

1. **Isolated Codex turns fail on this machine** (`invalid transport in mcp_servers.code-review`; §Live session, attempt 2). An isolated turn disables each configured MCP server by name, and this host's Codex rejects that override for its `code-review` server. It stops the router LLM and the teach-back summaries here (the router then runs on the Decider and the rule, `fallback = llm`, logged), and the blind grader's isolated turns use the same path. It is an owner fix on the machine (the Codex MCP config) or in the shared Codex provider's isolated launch; this stage changed neither.
2. **The Decider's pre-call estimate is about 4× low.** It prices the state once, but the Decider billed 20–28k input tokens for a block decision with the six sensor questions (8.9k–10.5k with fewer). The guard sums the real receipts, so it stays correct after each call; only the in-flight reservation is low. At $0.0002–0.0006 a decision against $5 a day it does not matter. Recommended: leave it, or scale the estimate by the question count if the guard ever binds.
3. **Old attempts never mature as router outcomes.** Router outcomes count only human-origin attempts, and the fixtures' older attempts carry `evidence_origin = 'unknown'`. So on the owner's vaults similar-decision retrieval shows nothing until new answers (recorded as human) mature. Recommended: accept; it fills as the router runs.
4. **The sensors quadruple the Decider's cost** (seven questions instead of one: about $0.0005 against $0.0002 per decision). Recommended: keep them on (the owner's default; the cost is negligible), and let R3 judge their value.
5. **Codex is slower than the blocking budget** (10–11 s per block decision against 8 s). On Today's prefetch path the decision was ready 11.5–13.2 s after the prefetch began, with no fallback. A Begin pressed within about 11 s of opening Today, or a Continue straight after a block's last answer, falls back for the LLM. Owner Q4 says revisit above about 20% LLM fallback; R3's report should show the rate.
6. **Labels at the merge.** `mvp-0.24` is a placeholder. Main has moved to `56579d271` (RW3a); the landing must check which label is free and relabel.
7. **The restraint's follow-up decline** writes a `plan_interrupt` row on the block whose answer produced the follow-up, which may already have ended. Its receipt key names that block and the item, so it stays unique; R3 should read `decline` rows as constraint refusals, not choices.

## Landing onto main

**Branch:** `merge/r2bc-onto-main` (worktree `learnanything-merge2`), from main `bffe086ec` (`mvp-0.23` LATEST; RW3a, the tutor delivery fixes and GLM-OCR landed since this branch's base `28c6040ca`; migration head 202, head fixture `fixtures/migration_head_202`, fifteen defaults snapshots). Merge `5a678eb37`, a real `--no-ff` merge of `router/r2bc` (`6f0b16254`, unchanged), then this record. Not pushed. Owner-directed, 2026-10-14, single phase. The sections above and `router-r2bc-codex-review.md` describe the branch as built and keep its placeholder wording.

**Main since the base, none of it a successor:**
- **RW3a:** Reader hooks, margin cues (`[cues]`), three RPCs; "check me" goes through R2a's `plan_learner_pick` and binds to the learner pick's own presentation.
- **The tutor delivery fixes:** `tutor/context_delivery.py`; whole blocks under budgets (`tutor_qa.context_token_budget`, `source_retrieval.passage_token_budget`); reference resolution; the automatic source-vector backfill (`embedding.backfill_sources_on_extract`, `embedding.source_backfill_max_cost_usd`); doctor's dense-coverage line.
- **GLM-OCR:** the primary extractor, `[ingest.pdf.glm_ocr]`, `set_text_recognition_api_key`; keep-local retired.

**Paid calls:** none ($0.00); no network, no key read. **Migration:** none (head 202 is main's). **`src-tauri`:** identical to main's, so no `cargo check`; the frontend changed (Today's first-block prefetch, the why/details line), so the frontend gate ran.

| Commit | What |
|---|---|
| `5a678eb37` | the merge, with the relabel comments, the composed template, the recomputed snapshots, the regenerated references, the docs and the landing tests |
| (this commit) | this section |

### Conflicts

| File | Resolution |
|---|---|
| `src/learnloop/config/template.py` (15 hunks, the only source conflict) | The `DEFAULTS_SNAPSHOT_BY_ALGORITHM` block. Main's RW3a, tutor-delivery and GLM-OCR notes kept and the branch's added: its full R2b + R2c note after GLM-OCR's in `mvp-0.9` (now "all sixteen ... on its branch, and all sixteen again when it landed on main after RW3a, the tutor delivery fixes and GLM-OCR"), its "moves it too" line after main's three in `mvp-0.10`..`mvp-0.22`, the composed `mvp-0.23` entry ("New vaults started here ... until mvp-0.24 merged", main's three lines, the branch's line) and the branch's `mvp-0.24` entry. All sixteen hashes recomputed (below). |
| 374 notes under `Reference/` | Taken from main, then regenerated. |
| Auto-merged, both sides kept | `pyproject.toml` (GLM-OCR's `glm-ocr` extra and import-linter ignores beside R2b's `router.requests` exceptions; main's removed `tutor_qa -> reader.span_view` edge stays removed), `cli/app.py` (the `--to mvp-0.24` branch and help text), `config/schema.py` (`[cues]`, the delivery keys and `[ingest.pdf.glm_ocr]` beside the `[router]` keys), `params/parameter_registry.py` (the delivery fixes' rule beside the router's), `apps/learnloop-tauri/src/api/dto.ts`, `tests/cli_help_snapshot.json` |

### The successor: `mvp-0.24`, kept

The branch's one placeholder is the string `"mvp-0.24"` (`ROUTER_MIXTURE_ALGORITHM_VERSION`). Main's LATEST is `mvp-0.23` and nothing on main took 0.24 (none of the three landings is a successor), so the label stays; nothing was renamed.
- **The chain.** `SUCCESSOR_CHAIN` ends `mvp-0.23`, `mvp-0.24`; `LATEST_ALGORITHM_VERSION` is `mvp-0.24`. `upgrade_to_mvp024` accepts `mvp-0.23`, or `mvp-0.9`..`mvp-0.22` through main's `router_staged_upgrade.upgrade_to_mvp023`, passes the chained notes through with `chained_notes = list(chained.notes or [])` (a refusal's included) and an earlier step's refusal unprefixed. T1's guard stays advisory. `learnloop upgrade` defaults to `mvp-0.24`; `--to mvp-0.10`..`--to mvp-0.23` still reach those tags.
- **Added at the landing:** `test_mvp024_upgrade.py::test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required`. With `config="[recurrence]\nrequire_guard = true"`, an `mvp-0.10` vault refuses at the `mvp-0.12` step: every problem starts with `mvp-0.12 step refused: ` through both later links, and the version is unchanged. After `_pass_guard`, the whole chain runs to `mvp-0.24` (the last 14 activations, `mvp-0.11`..`mvp-0.24`).
- **Comments.** "A placeholder label, relabelled at its merge" became "kept its label at its landing" in `algorithm_versions.py`, `router_mixture_upgrade.py`, the template and `test_mvp024_upgrade.py`.
- **Docs.** `Version Registry.md`: algorithm `mvp-0.24`; the projection base through `mvp-0.24`; the decision log's R2b + R2c additions; outcomes v2's `plan_interrupt` binding; a new row for the router's request, schema, why, summary and recipe versions. `Algorithm Versions and Reproducibility.md`: an `mvp-0.24` row; every version set through `mvp-0.24` and `ROUTER_MIXTURE_VERSIONS`; LATEST and the default target `mvp-0.24`. The R2 plan's status line records the landing.

### Compositions

1. **RW3a's "check me" under the mixture.** `plan_learner_pick` is a read (`_require` without `serve`), and `engine.learner_pick` never asks the chooser. It logs the learner's own block decision (`chosen_by = "learner_pick"`, no propensity) in the block's transaction, or none: a planned item is served by its block, a closed plan gives an open-list pick. R2b changed `_serve` to bind a presentation to `item.decision_ref or block.decision_ref` (review F1). A learner pick's item carries no `decision_ref`, so its presentation names the pick's own decision. New tests at mvp-0.24, with fake models that draw (the Decider takes the draw), in `tests/test_router_r2bc_landing.py`:
   - for the three RW3a cases, exactly one new presentation;
   - a new pick block gets exactly one new decision (`learner_pick = 1`, `propensity NULL`, `propensity_kind = none`);
   - a planned item gets no new decision, and its block's decision is the mixture's (`router_mixture_v1`, exact propensity);
   - a closed plan gets none;
   - no `receipt_key` repeats, and the delivery and `proposalPick.routerDecisionId` name the decision;
   - the answer binds by the presentation (`action_binding = presentation`, `taken`).

   **A composition only the mixture creates:** "check me" while Today's first block is still being chosen. A read leaves the decision open, with the models gated. The pick is then its own one-item block: one decision, one presentation, the answer bound by it. Once the models answer, the next serving step draws the mixture's block as a separate decision with its own presentation, and the pick's row is unchanged.

   RW3a's own landing test now takes a `version` (`_world(..., version=)`, default `mvp-0.23`), and its tests pass unchanged at `mvp-0.23`.
2. **The tutor delivery fixes vs R2c's retrieval and teach-back summaries.** R2b + R2c touch none of the tutor paths (`tutor/`, `source_retrieval/`, `reader/`, `ops/`, `ai/spend.py`: an empty diff from the base). No router module reads source passages (`span_view`, `context_delivery`, `build_cross_source_spans`, `span_context`, `source_document_blocks`: no match).
   - The `decision/context` text is a canonical rendering of the stored card: plan kind, time left, the options' kinds and topics, statuses, open problems. It contains no source text.
   - The card carries item stems, the learner's results, open problems and teach-back summaries, never source passages, under `router.card_token_budget` (16,000).
   - The two 240-character limits on the branch are not source cuts. `router_teach_back.POINT_LIMIT` bounds each model-written summary point (the card's budget), and `router/requests.OPTION_LIMIT` bounds an option's one-line description.
   - New test: the summarizer receives a teach-back dialogue of more than 2,400 characters whole (its last words included), and only the model's own point is clipped to 240.
3. **Spend: R2c's embeddings and the automatic source backfill.** Both use the embedding route (one model), and each goes through spend admission under its own guard.
   - **R2c's query embedding at prefetch** runs inside `RouterSpend.metered` (owner `router_decision`). The router's request gate prices it, and its start receipt is admitted against `router.max_daily_cost_usd` (review F3); the decision's vector is written from that same embedding, never bought again. `learnloop router embed-decisions` goes through `ops.embedding_backfill` with its own `SpendCaps` (receipts owned by `embedding_backfill`).
   - **The source backfill** (an ingest job) goes through the same `ops.embedding_backfill` with `SpendCaps` bounded by `embedding.source_backfill_max_cost_usd` per run (receipts owned by `embedding_backfill`).
   - **No double count.** The router's guard sums only `GUARDED_OWNERS` (`router_decision`, `router_teach_back_summary`). A backfill's `SpendBudget` counts only its own run's requests. Main's ingest daily total (`spent_today_usd`) counts every receipt once, as it always has.
   - **No bypass.** Both observers and gates are `ContextVar`s (`ai/execution.py`), so neither reaches the other's thread or context. The two backfills share the vault's advisory lock: a concurrent `router embed-decisions` reports `invalid` ("Another embedding backfill is running", `BackfillLockBusy`, a `ValueError`) and sends nothing.
   - **New test, one vault, one embedder:**
     - router decisions write `router_decision` embedding receipts, and an import's source backfill completes with `embedding_backfill` receipts;
     - `charged.calls` equals the embedder's calls during the import only;
     - `RouterSpend.spent_today` equals exactly the router receipts' sum, while the backfill's receipts are priced (> $0) and excluded;
     - with the router's cap set to what it has spent, the next day's decisions log `similar = unavailable (spend)` and their spend stays put, while a re-extraction's backfill still completes;
     - with the router's cap raised and `source_backfill_max_cost_usd = 0`, the router embeds again while a third extraction's backfill fails `over_budget`.
4. **GLM-OCR.** No shared code with the router: GLM-OCR changes extraction and its Settings key; R2b + R2c change Today, the card, the router's routes and the teach-back finish. `set_text_recognition_api_key` was already pinned desktop-only on main, and the branch added no RPC.
5. **The Pipeline Map** (`Maps/LearnLoop Pipeline Map.md`): R2b and R2c are live, no longer planned.
   - The end-to-end router node names the R2a frame, the R2b mixture and R2c's restraint, sensors and retrieval; the dashed "R2b / R2c model routing, planned" node is gone (MCP stays planned).
   - The daily-plan diagram adds the mixture (staged rule, Decider, router LLM; exact propensity and floor), R2c's context (teach-back summaries, similar decisions) feeding it, the payloads on the ledger, and the `plan_interrupt` restraint on follow-ups.
   - The text replaces "R2b and R2c are planned" with what is live and its kill switches. The AI section names the router's routes and their daily guard. The links list the R2b + R2c review. `implementation_version: mvp-0.24`; six router modules added to `source_paths`.
   - `validate_vault.py`: passed, 1,105 notes.

### Defaults, CLI help and references

- All sixteen `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries (`mvp-0.9`..`mvp-0.24`) were recomputed with `defaults_fingerprint_for_version` from the composed defaults, with the template `.pyc` deleted before and after and the file touched. Every one moved: the branch's lacked `[cues]`, the delivery keys and `[ingest.pdf.glm_ocr]`, and main's lacked the 16 `[router]` leaves and the `mixture` default. A fresh process confirms all sixteen.
- `python tests/test_cli_help_snapshot.py --write`: no change (the auto-merged snapshot was already exact).
- `db_generate_reference.py`: schema head 202, 321 table notes. `db_validate_reference.py` reports `errors: []` once `Configuration.md` and `Database.md` read 853 leaves (main's 837 plus the 16 `[router]` leaves; 50 sections).
- `tests/test_mobile_allowlist.py`: unchanged. The branch adds no RPC and no parameter (`next_plan_item`'s `serve` already existed).

### Gate

Run in this worktree at `5a678eb37` with `TMPDIR=<worktree>/fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` · `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **11,076 passed**, 0 failed, 48 warnings (13 min 34 s). Main's known flake (`test_reader_rw3a_landing.py::test_check_me_goes_through_the_plan_path_and_is_logged_once[planned]`, about 1 in 6, being fixed on `fix/plan-determinism`) did not show here. It did show once in a targeted run before the gate (2 of 6 when rerun alone, unchanged code at `mvp-0.23`: the block's `chosen_practice_item_id` is not always the check's item). The new mixture tests assert no block item order and passed 10 of 10 in a row. The reading-sweep thread warning is not in the captured summary |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability -n auto` | **100 passed**, 0 failed (24 s) |
| `npm install` · `npm run typecheck` · `npm test` · `npm run frontend:build` | up to date (281 packages) · clean · **81 files, 577 tests passed** · built, with the existing chunk-size notice |
| `cargo check` | not needed: `src-tauri` is identical to main's |
| Defaults · CLI help · references · vault | above |

The first full-suite attempt never ran: it was still waiting for the lock when the session restarted. It was relaunched detached, as were the parity jobs (below).

Targeted runs before the gate: the new landing file, RW3a's landing file and the `mvp-0.23` and `mvp-0.24` upgrade files (38 passed), then the CLI help, allowlist, config, reading-step, router, daily-plan, upgrade-chain, RW3a, cues, delivery, source-backfill, table-roles, Tier 1, judge-route, route-rules and recurrence files (998: 997 passed, plus the known flake above).

### Parity

Backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of this worktree's tracked `fixtures/linear_algebra` and `fixtures/probability` (`mvp-0.8`), in `fixtures-local/r2bc-parity`: one pristine copy each, then a copy per side and per check. Each copy was migrated by its own code (`migration_coordinator.migrate_vault`):
- main `bffe086ec`, exported with `git archive`, first on `sys.path` (`python -I`; the probe printed the archive's `learnloop/__init__.py`);
- the merge's own code.

Both sides applied 47 migrations to 202. On each copy, `learnloop rebuild --shadow --json` and `learnloop doctor --json`, with `LEARNLOOP_CONFIG_DIR` an empty directory and main's code on `PYTHONPATH` for main's side. Compared after setting aside ULIDs, timestamps, ids, hashes and paths.

**At `mvp-0.23`** (the check asked for). A copy per side and fixture was taken through `learnloop upgrade --to mvp-0.9`, then `--to mvp-0.23`, by its own code (the chain's advisory-guard notes printed), then `learnloop rebuild-derived-state` twice to its fixed point. **0 differences** on all four comparisons (7,054 lines):

| Fixture | Replayed attempts | Shadow (facet / mastery / schedule) | Doctor issues | Errors | `criterion:unknown_dependency` | Router or plan issues |
|---|---:|---|---:|---:|---:|---:|
| linear algebra | 70 | 0 / 0 / 0 | 56 | 1 | none | none |
| probability | 2 | 0 / 0 / 0 | 98 | 49 | 46 | none |

**At the fixtures' own `mvp-0.8`** (as earlier landings ran it): also **0 differences** on all four (7,817 lines). Linear algebra shadows 22 / 6 / 47 (facet / mastery / schedule) with 106 doctor issues and 1 error; probability shadows 2 / 1 / 1 with 134 issues and 49 errors (46 `criterion:unknown_dependency`). These are the fixtures' existing drift at `mvp-0.8`, the same on both sides and the same as at the GLM-OCR landing.

`live_database.unchanged` is true on every shadow, and each copy's `state.sqlite` hash is identical before and after its shadow and doctor. Doctor exits 1 on both sides, as on main.

**The `mvp-0.23` → `mvp-0.24` upgrade, shadowed** (playbook item 7). The merge's `mvp-0.23` copies were taken through `learnloop upgrade` (the default target: "Upgraded vault: mvp-0.23 -> mvp-0.24"), then shadowed and doctored again.

| Fixture | Replayed | Shadow at mvp-0.23 | Shadow at mvp-0.24 | What differs at mvp-0.24 | Doctor at mvp-0.24 |
|---|---:|---|---|---|---|
| linear algebra | 70 | 0 / 0 / 0 | 0 / 21 / 0 | `algorithm_version` only (`mvp-0.23` → `mvp-0.24`), on all 21 mastery rows; no other column on any row | identical to mvp-0.23's (56 issues, 1 error), no router or plan issue |
| probability | 2 | 0 / 0 / 0 | 0 / 18 / 0 | `algorithm_version` only, on all 18 mastery rows | identical to mvp-0.23's (98 issues, 49 errors), no router or plan issue |

Outside those rows, the shadow reports differ only in the version labels themselves: `baseline_algorithm_version`, `candidate_algorithm_version` and `rebuild.algorithm_version`. So the successor adds no delta beyond the version label, as at R2a's landing (the same 21 and 18 rows).

The tracked fixtures were only copied: `git status fixtures/` is clean.

### Safety

- No paid call, no subscription call, no network. No key, credential, `.env` or `settings.env` file was read, nor `~/.config/learnloop/` or `~/.codex/auth.json`.
- The main checkout was not touched. Its working vaults were never opened. This worktree's tracked `linear_algebra` and `probability` were opened only by the backup API, and `arxiv_v2` not at all.
- Nothing was pushed, rebased or stashed. `router/r2bc` and its worktree `learnanything-merge4` were not modified.

### Open questions for the owner (defaults applied)

1. **Isolated Codex turns** (open question 1 above). Resolved by the owner on 2026-10-14: the Codex `code-review` MCP server is turned off, so isolated turns should no longer fail with "invalid transport in mcp_servers.code-review". This covers the router LLM, the teach-back summaries and the blind grader's isolated turns. The landing made no subscription or paid call, so this was not re-run. If an isolated turn still fails, the router keeps its fallback: the Decider and the rule take the LLM's share, and the decision logs `fallback = llm` with the reason.
2. **The Decider's pre-call estimate is about 4× low** (open question 2). Default: **leave it**. The guard sums the real receipts after each call, so only the in-flight reservation is low ($0.0002–0.0006 a decision against $5 a day). If the guard ever binds, scale the estimate by the question count.
3. **Similar-decision retrieval is empty on the owner's vaults** until new human-origin answers mature (open question 3). **Accepted.** It fills as the router runs.
4. **The sensors stay on** (open question 4; the owner's default, about $0.0003 more a decision). R3 judges their value.
5. **The LLM fallback rate** (open question 5: Codex took 10–11 s against the 8 s serving wait). **R3's report shows the rate**; owner Q4 revisits above about 20%.
6. **Labels** (open question 6): resolved. `mvp-0.24` kept, no migration.
7. **Decline rows** (open question 7): R3 reads `plan_interrupt` `decline` rows as constraint refusals, not choices.

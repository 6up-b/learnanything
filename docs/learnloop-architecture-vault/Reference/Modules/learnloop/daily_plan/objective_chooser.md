---
title: "learnloop.daily_plan.objective_chooser"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/objective_chooser.py"
source_paths:
  - "src/learnloop/daily_plan/objective_chooser.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.objective_chooser module"
  - "src/learnloop/daily_plan/objective_chooser.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.objective_chooser`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.objective_chooser` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Router objective RO4 (spec_router_objective_v1 §8.2-§8.3, §8.6-§8.8): the objective chooser on Today.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py) |
| Source lines | 1673 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `objective_settings(config: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 116) — The settings a prefetch boundary key names, the follow-up batch's switches as they serve among them (landing ruling R12, ``followup_switch_snapshot``), so a flip between a prefetch and its serve starts a new job.
- `day_price(repository: Any, inputs: OT.Inputs, *, local_date: str, draws: int, seed: str, config: Any=None) -> tuple[P.Seeded, dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 327) — κ0 for this decision (§8.6): the day's first decision computes the seed from the gain curve, later ones carry it.
- `current_weight(repository: Any, config: Any, *, at: str) -> tuple[float, dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 385) — ``w_i`` (§8.7) from the scores whose windows closed before ``at``; with no randomized check, none forms.
- `generator_now(config: Any, objective: str | None=None) -> str` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 437) — RO6: the generator version a decision made now is logged under (``tail_data.generator`` over its trace).
- `run_numeric(vault: Any, repository: Any, *, state: PlanState, support: Sequence[str], candidates: Mapping[str, BlockCandidate], now_iso: str, seed: str, deadline: float | None, keep_going: Any=None, forecasts: Any=None, clock: Any=time.monotonic, publish: Any=None, sequences: Mapping[str, Sequence[BlockCandidate]] | None=None, learned_tail: bool=False, tail_snapshot: Mapping[str, Any] | None=None, carried_valuation: bool=True, defer_carried: Callable[[Callable[[], dict[str, Any]]], None] | None=None) -> NumericPolicy` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 484) — π_Q end to end: the frozen inputs, the day's price, ``Q̄`` with common random numbers (more draws while ``keep_going()``), then, once the LLM policy's forecasts are in (``forecasts()``: None while out), the effect correction; the argmax with the tie rule; the evaluation's baseli…
- `class ObjectiveChooser(RouterChooser)` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 800) — ``router_objective_v1``: the two policies' learned mix over the staged frame's support.
  - `choose(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> BlockChoice` (line 805; public)
  - `_tail_snapshot(self, now_iso: str) -> Mapping[str, Any] | None` (line 894; internal) — RO6: the residual's mutable inputs read now, in the decision's own thread at its moment (F4); None below the tag or with the switch off (nothing read, the predecessor's path), or when it cannot be read (the residual is then left out and the trace says so).
  - `_start_objective(self, key: str, state: PlanState, feasible: Sequence[BlockCandidate], support: Sequence[str], by_id: Mapping[str, BlockCandidate], ready: tuple[str, ...], now_iso: str, *, numeric_seed: str) -> Prefetch` (line 911; internal)
  - `_decide_objective(self, entry: Any, state: PlanState, staged: BlockChoice, staged_ref: str, record: dict[str, Any], support: Sequence[str], by_id: Mapping[str, BlockCandidate], feasible: Sequence[BlockCandidate], readiness: Mapping[str, str | None], settings: Mapping[str, Any], now_iso: str) -> BlockChoice` (line 933; internal) — The boundary's decision in three parts: the reads gathered into ``ChoiceInputs``, the choice (:func:`learnloop.router_objective.choose.choose`, pure), then what the decision writes from it (its trace, the router's record, its decision record and the served block).
  - `_session_minutes(self, now_iso: str) -> float | None` (line 1068; internal) — The objective session's active minutes at ``now_iso`` on the serving clock (``price.session_active_minutes``, the price's own construction), or None where they cannot be read (the coin is then not drawn).
  - `_availability(self, state: PlanState, numeric: 'NumericPolicy | None') -> dict[str, Any]` (line 1082; internal) — RO5 §9 item 1: what the learner had when the coin was drawn, read before its uniform: the session's active minutes, the plan's remembered, budgeted and remaining minutes, and the session's availability receipt (RO0 row 8: the minutes offered and their source).
- `class ObjectiveRestraintGate(RestraintGate)` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 1113) — §8.3's mid-block follow-ups: the same two-policy mix over ``{insert_now, continue_current}``.
  - `decide(self, record: Any, current: Any, item: Any, *, wait_feasible: bool=True, offer: Any=None) -> RestraintOutcome` (line 1119; public) — ``offer`` (IH2, spec_instruct_handoff_v1 §5 item 3): the lesson offer this decision may hold (``offer.candidate`` None: none available, and ``offer.record`` says why).
  - `_decide_with_lesson(self, record: Any, current: Any, item: Any, state: PlanState, candidates: list[BlockCandidate], lesson: BlockCandidate, *, wait_feasible: bool) -> RestraintOutcome` (line 1154; internal) — The need path's arms with the offer among them: a probability per option, the follow-up valued as its item says (a probe's bundle, or a repair), the offer's "Not now" leading to the follow-up, which stays available.
  - `_no_room(self, state: PlanState, candidates: list[BlockCandidate]) -> RestraintOutcome` (line 1190; internal) — ``wait_feasible = False``: waiting would drop the follow-up from today's plan, so it joins now, deterministically, and no model is asked (Codex review F8's rule, kept by §8.3).
  - `_mixed(self, state: PlanState, candidates: list[BlockCandidate], *, key: str, seed: str, readiness: Mapping[str, Any], ready: tuple[str, ...], topic: str, options: Sequence[Any], extra: Sequence[str], valued: Mapping[str, BlockCandidate] | None=None, support: Sequence[str]=(INSERT_NOW, CONTINUE_CURRENT), sequences: Mapping[str, Sequence[BlockCandidate]] | None=None, start: Any=None, llm_schema: str=rq.LLM_POLICY_RESTRAINT_SCHEMA, staged_ref: str=INSERT_NOW) -> RestraintOutcome` (line 1199; internal) — The two-policy mix over ``support`` (§8.3; by default ``{insert_now, continue_current}``), drawn and traced.
  - `_numeric_restraint(self, state: PlanState, insert: BlockCandidate, cont: BlockCandidate, now_iso: str, seed: str) -> NumericPolicy` (line 1316; internal) — π_Q on the two orders, each an ordered sequence of the two blocks (the follow-up, then the remaining questions; or the reverse), every step valued with its own kind, duration, observation and effect on one clock; one cutoff, the same draws, each step its own noise in either orde…
  - `_policy_state(self, card: Any, options: Sequence[Any], extra: Sequence[str], state_text: str, candidates: Sequence[Any]=()) -> str` (line 1329; internal) — The LLM policy's state on a mid-block decision: the shared state, plus (IH4, §7 item 6) the learner's own statements and (slip or gap SG1, §3 item 3) the last miss's cause on the follow-up's and any offer's topic (``candidates``), for the LLM alone: the Decider's request keeps `…
  - `_start_policy(self, key: str, state: PlanState, candidates: list[BlockCandidate], topic: str, options: Sequence[Any], extra: Sequence[str], ready: tuple[str, ...], offers: Sequence[BlockCandidate]=()) -> Prefetch` (line 1359; internal) — The two models' prefetch: the Decider's R2c restraint request (advice) and the LLM policy's v3 one.
  - `_start_choice(self, key: str, state: PlanState, candidates: list[BlockCandidate], topic: str, options: Sequence[Any], extra: Sequence[str], ready: tuple[str, ...], offers: Sequence[BlockCandidate]=()) -> Prefetch` (line 1403; internal) — The two models' prefetch for the three arms: the Decider's R2c restraint request (advice, ``P(yes)``) and the LLM policy's ``router_llm_choice_v3`` (a probability per option; the reference row is the current block's rest, the continuation ``π_Q``'s tail assumes).
- `class ObjectiveFollowupGate(ObjectiveRestraintGate, FollowupGate)` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 1464) — §8.3 for FG1's generated probe at RO5's tag: the follow-up's ``plan_interrupt`` decision, made before its item exists, on the same two-policy mix as every mid-block follow-up, with its trace and ``μ`` recomputable (``mix.recompute``).
  - `decide_followup(self, record: Any, current: Any, workflow: Mapping[str, Any], *, wait_feasible: bool, facts: Sequence[str]=(), offer: Any=None) -> RestraintOutcome` (line 1479; public) — ``offer`` (IH2, spec_instruct_handoff_v1 §5 item 3): the lesson offer this decision may hold; with one, the support gains it, and no room to wait no longer makes the decision deterministic: ``{insert_now, lesson}``, a real draw, before anything is generated.
  - `_decide_unwritten_probe(self, record: Any, current: Any, workflow: Mapping[str, Any], state: PlanState, candidates: list[BlockCandidate], *, wait_feasible: bool, facts: Sequence[str], offer: Any) -> RestraintOutcome` (line 1553; internal) — The probe router's tag (``probe_router_on``): the probe is not written yet, so the router cannot value its answer pattern and it earns no information credit (G2 design decision 1); it is no option of either policy, now or after the block.
  - `_followup_minutes(self, workflow: Mapping[str, Any], current: Any) -> float` (line 1645; internal) — The generated question's minutes for ``π_Q``: the missed question's own estimate (the probe is written on its LO, after it), else the mean of the LO's items', else the current block's mean question.

### Module constants

- `LOG` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 107)
- `MODE` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 109)
- `KEY_VERSION` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 110)
- `WHY_VERSION` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 111)
- `_FAILURES` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 113)
- `FOLLOWUP_PLACEHOLDER_PREFIX` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 1460)

### Explicit exports

`__all__` declares:

- `FOLLOWUP_PLACEHOLDER_PREFIX`
- `NUMERIC`
- `NumericPolicy`
- `ObjectiveChooser`
- `ObjectiveFollowupGate`
- `ObjectiveRestraintGate`
- `current_weight`
- `day_price`
- `objective_settings`
- `run_numeric`

## Internal implementation anchors

- `_miss_cause_mark(repository: Any, config: Any, candidates: Sequence[Any], now_iso: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 152) — Slip or gap: what a boundary's identity names so a change in a candidate topic's miss sensor (a diagnosis landing, a probe answered) starts a new job (``miss_cause.mark``).
- `_preference_mark(repository: Any, config: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 171) — IH4: what a boundary's identity names so a new preference starts a new job (``preferences.mark``), read on the caller's connection, which a read-only prefetch can do.
- `_local_date(now_iso: str) -> str` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 181)
- `_merged(config: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 189) — The follow-up batch's item 3 (Codex review F2): the rollouts' merged tail sessions serve only at the batch's tag with ``[router_objective] merged_sessions``.
- `_consistent_draw(config: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 202) — The follow-up batch's landing ruling R1: the rollouts draw a practised topic's practice outcome from the memory model's own ``P(perform)`` (``value.REVIEW_DRAW_VERSION``) only at the batch's tag with ``[router_objective] consistent_review_draw``; below the tag, or off, mvp-0.49'…
- `_held_link(config: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 214) — Router speed, item 1 (Codex review F1): R9's link values held per role in the rollouts (``value.Inputs.ad_link``'s ``held_ad_link``) only at the follow-up batch's tag with ``[router_objective] held_ad_link``; off, the batch's landing code (the same values per draw, at the landin…
- `_rollout_options(config: Any) -> dict[str, bool]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 227) — The rollouts' serving options, for every rollout of one decision (its evaluation and refinement, the correction, the carried valuation, the baselines and the day's gain curve) or for none: one place.
- `_evaluator(config: Any) -> Callable[..., OBJ.Evaluation]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 240) — Which evaluation values a decision's candidates: at the committed-check credit's tag (mvp-0.62) the check-credit path, which prices a lesson's typed checks (delivered, on a return, at their minutes) and values every action without typed checks exactly as the rollouts do; below i…
- `_replay_payload(inputs: OT.Inputs, actions: Sequence[OT.Action], evaluation: OBJ.Evaluation, *, seed: str, first_draws: int, max_draws: int, now_iso: str, options: Mapping[str, Any], config: Any, candidates: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 255) — The lossless replay payload of an answer whose candidates carry typed committed checks (mvp-0.62 or later): what a later report needs to recompute its values exactly under both pricings (``router_objective.check_replay``).
- `_frontier(inputs: OT.Inputs, *, draws: int, seed: str, **rollout: bool) -> tuple[dict[float, float], dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 287)
- `_posterior_price(repository: Any, inputs: OT.Inputs, config: Any, *, local_date: str, draws: int, seed: str) -> tuple[P.Seeded, dict[str, Any]] | None` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 298) — RO5 §9 item 1: once a randomized stop offer has a response, κ0 is the posterior the seed is folded into (:mod:`learnloop.router_objective.stop_coin`) and the daily re-centring ends; the frontier is still drawn once a day, for display.
- `_randomized_checks_exist(repository: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 367) — Whether any RO5 randomized cold check was ever assigned (none before RO5).
- `_seed_record(seeds: W.Seeds) -> dict[str, float]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 380)
- `_preferences_move(record: Mapping[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 456)
- `_preference_record(repository: Any, config: Any, *, state: PlanState, support: Sequence[str], candidates: Mapping[str, BlockCandidate], now_iso: str) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 462) — IH4: a ``plan_block`` decision's choice-model sensor and ``w_pref``, from each candidate's kind.
- `_reference_description(action: OT.Action, titles: Mapping[str, str]) -> str` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 704)
- `_policy_request(vault: Any, repository: Any, entry: Prefetch) -> rq.PolicyRequest` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 710) — The LLM policy's request for one boundary, built on its job's thread (:mod:`learnloop.daily_plan.objective_job`) inside the job's reads: the decision card over the support, the tail's next action as the reference row.
- `_offer_option(candidate: BlockCandidate, titles: Mapping[str, str]) -> rq.BlockOption` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 746) — Teacher TE3b: the lesson offer as one more option of the LLM policy's existing request (and the Decider's advice): its target, its reason, its minutes and ``P(accept)`` (spec §15.1a; no new request).
- `_built_record(choice: C.Choice, inputs: C.ChoiceInputs, question_set_version: Any) -> tuple[Any, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 758) — The decision's own record (:func:`learnloop.router_objective.choose.decision_record`), or, when it cannot be built, None and a failure record for the boundary's children.
- `_is_contest(candidate: BlockCandidate) -> bool` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 778)
- `_option_facts(candidate: BlockCandidate) -> C.OptionFacts` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 782) — What the choice's rule sentence reads of a candidate (``router_chooser._rule_sentence``'s annotations).
- `_contest_option(candidate: BlockCandidate, titles: Mapping[str, str]) -> rq.BlockOption` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 790) — IH2 (spec_instruct_handoff_v1 §5 item 2): the boundary's follow-ups, as the LLM policy reads them beside the offer.
- `_with_offer_record(outcome: RestraintOutcome, offer: Any) -> RestraintOutcome` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 1448) — IH2: the boundary's offer on the decision's record: its sensors, or why there was none (a ceiling bind logged).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `current_weight`; statically calls `current_weight`
- [[Reference/Modules/learnloop/daily_plan/learner_probe|learnloop.daily_plan.learner_probe]] — imports `module`; statically calls `_local_date`, `current_weight`, `day_price`, `numeric_seed`, `rollout_options`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `ObjectiveChooser`, `ObjectiveRestraintGate`; statically calls `ObjectiveChooser`, `ObjectiveRestraintGate`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `ObjectiveFollowupGate`

### Repository tooling consumers

- [scripts/check_credit_report.py](../../../../../../scripts/check_credit_report.py); calls `rollout_options`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `committed_check_delivery_on`, `probe_router_on`; calls `committed_check_delivery_on`, `probe_router_on`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `card`; calls `card`
- [[Reference/Modules/learnloop/daily_plan/objective_card|learnloop.daily_plan.objective_card]] — imports `decision_card`, `miss_cause_lines`, `statement_lines`; calls `decision_card`, `miss_cause_lines`, `statement_lines`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; calls `_lessons_on`, `build`
- [[Reference/Modules/learnloop/daily_plan/objective_job|learnloop.daily_plan.objective_job]] — imports `NUMERIC`, `NumericPolicy`, `module`; calls `NumericPolicy`, `answer_without_models`, `await_job`, `carried_for`, `carry_on`, `defer_carry`, `job_answers`, `start_job`
- [[Reference/Modules/learnloop/daily_plan/objective_seeds|learnloop.daily_plan.objective_seeds]] — imports `mix_seed`, `numeric_seed`; calls `mix_seed`, `numeric_seed`
- [[Reference/Modules/learnloop/daily_plan/plan_records|learnloop.daily_plan.plan_records]] — imports `module`; calls `step_failure`
- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `FollowupGate`, `INSERT_NOW`, `NO_INTERVENTION`, `RestraintGate`, `RestraintOutcome`, `RouterChooser`, `_NoModels`, `_await`, `_build_card`, `_card_fields`, `_hash`, `_latest_attempt`, `_option`, `_payloads`, `_rule_sentence`, `_run_components`, `router_settings`, `support_order`; calls `RestraintOutcome`, `_NoModels`, `_await`, `_build_card`, `_card_fields`, `_hash`, `_latest_attempt`, `_option`, `_payloads`, `_rule_sentence`, `_run_components`, `router_settings`, `support_order`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `ANSWERED`, `ComponentResult`, `DECIDER`, `FAILED`, `INVALID`, `LLM`, `NOT_READY`, `Prefetch`, `RECEIPT_OWNER`, `TIMEOUT`, `seen`; calls `ComponentResult`, `seen`
- [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]] — imports `StagedChooser`; calls `StagedChooser`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `BlockCandidate`, `BlockChoice`, `CONTINUE_CURRENT`, `DecisionPending`, `FOLLOWUP_CONTEST_NOTE`, `PlanState`, `STOP_FOR_TODAY`, `STOP_OFFER_MINUTES`; calls `BlockChoice`, `DecisionPending`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `session_receipt`, `table_present`, `traces`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `module`; calls `current_trace`
- [[Reference/Modules/learnloop/router/requests|learnloop.router.requests]] — imports `module`; calls `BlockOption`, `PolicyRequest`, `RestraintRequest`, `evidence_from_card`, `lesson_offer_description`, `parse_decider_restraint`, `parse_llm_policy`, `parse_llm_policy_restraint`, `state_text`
- [[Reference/Modules/learnloop/router/why|learnloop.router.why]] — imports `module`; calls `objective_why`, `rationale_guard`
- [[Reference/Modules/learnloop/router_objective/check_replay|learnloop.router_objective.check_replay]] — imports `module`; calls `carries_typed_checks`, `record`
- [[Reference/Modules/learnloop/router_objective/check_value|learnloop.router_objective.check_value]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/choose|learnloop.router_objective.choose]] — imports `module`; calls `ChoiceInputs`, `OptionFacts`, `PostMissInputs`, `choose`, `coin_applies`, `coin_reads_minutes`, `decision_record`, `post_miss_choice`
- [[Reference/Modules/learnloop/router_objective/miss_cause|learnloop.router_objective.miss_cause]] — imports `module`; calls `ledger_mark`, `mark`, `sensor`
- [[Reference/Modules/learnloop/router_objective/mix|learnloop.router_objective.mix]] — imports `module`; calls `fallback_label`
- [[Reference/Modules/learnloop/router_objective/objective|learnloop.router_objective.objective]] — imports `module`; calls `numeric_choice`
- [[Reference/Modules/learnloop/router_objective/preferences|learnloop.router_objective.preferences]] — imports `mark`, `module`, `moves_the_value`; calls `kind_of`, `mark`, `moves_the_value`, `record`, `shifted`
- [[Reference/Modules/learnloop/router_objective/price|learnloop.router_objective.price]] — imports `module`; calls `Seeded`, `seed_from_gain`, `session_active_minutes`
- [[Reference/Modules/learnloop/router_objective/probe_coin|learnloop.router_objective.probe_coin]] — imports `module`; calls `applies`, `flip`, `pending_assignment`, `seed_for`, `served_distribution`, `share`
- [[Reference/Modules/learnloop/router_objective/rollouts|learnloop.router_objective.rollouts]] — imports `module`; calls `_Model`, `baselines`, `gain`
- [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] — imports `module`; calls `scores`
- [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]] — imports `module`; calls `handed_over`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `module`; calls `features_version`, `generator_key`, `generator_payload`, `objective_hash`, `scope_extension_on`
- [[Reference/Modules/learnloop/router_objective/tail_serve|learnloop.router_objective.tail_serve]] — imports `module`; calls `carried_cutoff`, `measurable`, `not_on_the_serving_path`, `pending_after_the_answer`, `residual`, `shifted`, `snapshot`, `with_carried_values`
- [[Reference/Modules/learnloop/router_objective/trace_assembly|learnloop.router_objective.trace_assembly]] — imports `module`; calls `decision_trace`, `failure_rule_field`, `objective_trace`
- [[Reference/Modules/learnloop/router_objective/types|learnloop.router_objective.types]] — imports `module`; calls `EffectSlope`, `is_offer_subtype`
- [[Reference/Modules/learnloop/router_objective/weight|learnloop.router_objective.weight]] — imports `module`; calls `Scored`, `posterior`, `unique_assessments`, `weight`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `calibrated_weight_on`, `failure_share_to_other_policy_on`, `followup_generator_switches`, `followup_on`, `followup_switch_snapshot`, `learned_tail_on`, `lessons_compete_with_followups_on`, `miss_cause_in_value_on`, `miss_cause_sensor_on`, `objective_scores_on`, `preferences_inform_router_on`, `stop_coin_rate`; calls `calibrated_weight_on`, `failure_share_to_other_policy_on`, `followup_generator_switches`, `followup_on`, `followup_switch_snapshot`, `learned_tail_on`, `lessons_compete_with_followups_on`, `miss_cause_in_value_on`, `miss_cause_sensor_on`, `objective_scores_on`, `preferences_inform_router_on`, `stop_coin_rate`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `functools`, `json`, `logging`, `math`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]], [[Reference/Modules/learnloop/daily_plan/learner_probe|learnloop.daily_plan.learner_probe]], [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]], [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/ih2_lessons_compete_helpers.py](../../../../../../tests/ih2_lessons_compete_helpers.py) — direct import
- [tests/ih4_preferences_inform_router_helpers.py](../../../../../../tests/ih4_preferences_inform_router_helpers.py) — direct import
- [tests/ih_numeric_seed_helpers.py](../../../../../../tests/ih_numeric_seed_helpers.py) — direct import
- [tests/router_model_fakes.py](../../../../../../tests/router_model_fakes.py) — direct import
- [tests/test_check_credit_activation.py](../../../../../../tests/test_check_credit_activation.py) — direct import
  - `test_the_tag`
- [tests/test_check_credit_characterization.py](../../../../../../tests/test_check_credit_characterization.py) — direct import
  - `test_both_tags_an_offer_with_no_eligible_question`
- [tests/test_ih2_lessons_compete.py](../../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_the_switch_defaults_on_is_classified_and_names_itself_in_the_prefetch_key`
  - `test_with_no_room_to_wait_a_lesson_makes_it_a_real_draw_and_with_none_it_stays_deterministic`
- [tests/test_ih2_one_open_offer.py](../../../../../../tests/test_ih2_one_open_offer.py) — direct import
  - `test_a_job_that_draws_the_followup_leaves_the_read_offer_alone`
  - `test_a_need_decision_replacing_an_interrupting_offer_keeps_its_place_and_what_it_beat`
  - `test_at_most_one_open_offer_across_read_and_job_interleavings`
- [tests/test_ih4_preferences_inform_router.py](../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
  - `test_a_new_preference_starts_a_new_job_and_moves_no_seed`
  - `test_the_key_names_the_switch_only_while_it_serves_and_the_seed_never`
  - `test_the_mid_block_request_carries_them_for_the_llm_alone`
  - `test_the_start_only_prefetch_and_its_serve_compute_one_key_with_preferences_on_record`
  - `test_w_itself_never_reads_a_preference_or_a_pick`
- [tests/test_ih5_successor.py](../../../../../../tests/test_ih5_successor.py) — direct import
  - `test_the_prefetch_key_names_the_switch_as_it_serves`
- [tests/test_ih6_workbench_open_item.py](../../../../../../tests/test_ih6_workbench_open_item.py) — direct import
  - `test_the_switch_is_not_in_the_prefetch_key_so_it_moves_no_seed`
- [tests/test_ih_lesson_candidate_after_cold_miss.py](../../../../../../tests/test_ih_lesson_candidate_after_cold_miss.py) — direct import
  - `test_the_switch_is_not_in_the_prefetch_key_and_moves_no_seed_by_itself`
- [tests/test_ih_numeric_seed.py](../../../../../../tests/test_ih_numeric_seed.py) — direct import
  - `test_an_offer_changes_the_identity_and_so_the_seed`
  - `test_the_serve_without_a_prefetch_starts_the_same_job_the_prefetch_would`
  - `test_the_start_only_prefetch_and_its_serve_compute_one_key_and_one_seed`
  - `test_the_workflows_arm_with_no_room_to_wait_seeds_from_its_identity`
- [tests/test_objective_refinement.py](../../../../../../tests/test_objective_refinement.py) — direct import
  - `test_refinement_runs_another_batch_while_the_llm_is_out_and_stops_when_it_answers`
  - `test_refinement_stops_at_the_deadline_with_the_llm_still_out`
- [tests/test_pinned_draws.py](../../../../../../tests/test_pinned_draws.py) — direct import
  - `test_the_numeric_policy_runs_one_batch`
- [tests/test_post_miss_choice.py](../../../../../../tests/test_post_miss_choice.py) — direct import
- [tests/test_probe_router.py](../../../../../../tests/test_probe_router.py) — direct import
- [tests/test_probe_router_authority.py](../../../../../../tests/test_probe_router_authority.py) — direct import
  - `test_f_the_mid_block_restraint_forces_now_with_no_room_and_draws_two_arms_otherwise`
- [tests/test_probe_router_decision_integrity.py](../../../../../../tests/test_probe_router_decision_integrity.py) — direct import
  - `test_r15_the_valuation_runs_under_the_choosers_options_and_freezes_what_it_valued`
- [tests/test_ro4_codex_review.py](../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f1_the_numeric_answer_is_published_before_any_wait_on_the_llm`
  - `test_f5_mid_block_alternatives_are_ordered_sequences_of_their_own_blocks`
- [tests/test_ro4_objective_serving.py](../../../../../../tests/test_ro4_objective_serving.py) — direct import
  - `test_a_numeric_timeout_is_a_failure_and_both_failed_keeps_the_floor`
- [tests/test_ro5_codex_review.py](../../../../../../tests/test_ro5_codex_review.py) — direct import
  - `test_f5_the_check_arm_off_restores_ro4s_weight_after_scores_accumulated`
  - `test_f7_the_trace_freezes_every_dated_goals_forecast_beyond_the_window`
- [tests/test_ro5_stop_coin.py](../../../../../../tests/test_ro5_stop_coin.py) — direct import
  - `test_every_arm_off_at_the_tag_is_mvp_047_exactly`
- [tests/test_ro6_landing.py](../../../../../../tests/test_ro6_landing.py) — direct import
  - `test_r12_with_the_carried_evaluation_blocked_the_choosers_wait_returns`
  - `test_r3_the_no_model_branch_answers_within_the_first_pass_and_censors_the_carried_backup`
- [tests/test_ro6_serving.py](../../../../../../tests/test_ro6_serving.py) — direct import
- [tests/test_ro6_tail_data.py](../../../../../../tests/test_ro6_tail_data.py) — direct import
  - `test_refitting_on_a_later_version_does_not_change_version_ks_evaluation`
- [tests/test_rofu_ad_link.py](../../../../../../tests/test_rofu_ad_link.py) — direct import
  - `test_the_numeric_policy_reads_ads_own_predictive_only_with_its_switch`
- [tests/test_rofu_carried.py](../../../../../../tests/test_rofu_carried.py) — direct import
  - `test_an_early_publication_served_keeps_its_carried_valuation`
- [tests/test_rofu_review_draw.py](../../../../../../tests/test_rofu_review_draw.py) — direct import
  - `test_the_numeric_policy_draws_consistently_only_with_its_switch`
- [tests/test_rofu_speed.py](../../../../../../tests/test_rofu_speed.py) — direct import
  - `test_the_numeric_policy_merges_only_with_its_switch`
- [tests/test_rofu_switch_key.py](../../../../../../tests/test_rofu_switch_key.py) — direct import
  - `test_a_served_cached_answer_names_the_generator_that_produced_it`
  - `test_the_key_names_the_switches_at_every_tag_a_vault_can_hold`
- [tests/test_rospeed2_connections.py](../../../../../../tests/test_rospeed2_connections.py) — direct import
  - `test_r2_the_numeric_seed_is_mains_whatever_the_speed_switches`
  - `test_the_pool_completes_more_draws_by_one_deadline_and_switched_off_is_mains`
- [tests/test_rospeed_ad_link.py](../../../../../../tests/test_rospeed_ad_link.py) — direct import
  - `test_the_switch_reaches_every_rollout_from_the_config`
- [tests/test_rospeed_join.py](../../../../../../tests/test_rospeed_join.py) — direct import
  - `test_the_prefetch_job_reads_the_fit_again_only_after_a_commit`
- [tests/test_router_sampling_points.py](../../../../../../tests/test_router_sampling_points.py) — direct import
- [tests/test_sg_slip_vs_gap.py](../../../../../../tests/test_sg_slip_vs_gap.py) — direct import
  - `test_the_seed_ignores_the_switches_the_mark_and_the_offers_sensor`
- [tests/test_sg_successor.py](../../../../../../tests/test_sg_successor.py) — direct import
  - `test_the_prefetch_key_names_both_switches_as_they_serve`

## Modification guidance

- Make changes here when the responsibility remains objective chooser within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

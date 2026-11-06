---
title: "learnloop.daily_plan.objective_chooser"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/objective_chooser.py"
source_paths:
  - "src/learnloop/daily_plan/objective_chooser.py"
source_commit: "e66f62e6f15ef1402f451cf6b22ed472ba5b1aba"
source_commit_timestamp: "2026-11-06T09:45:38-05:00"
source_worktree_state: "clean"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.objective_chooser` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Router objective RO4 (spec_router_objective_v1 §8.2-§8.3, §8.6-§8.8): the objective chooser on Today.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py) |
| Source lines | 1725 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e66f62e6f15ef1402f451cf6b22ed472ba5b1aba` |
| Commit timestamp | `2026-11-06T09:45:38-05:00` |

## Public API

- `objective_settings(config: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 115) — The settings a prefetch boundary key names.
- `day_price(repository: Any, inputs: V.Inputs, *, local_date: str, draws: int, seed: str, config: Any=None) -> tuple[P.Seeded, dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 239) — κ0 for this decision (§8.6): the day's first decision computes the seed from the gain curve, later ones carry it.
- `current_weight(repository: Any, config: Any, *, at: str) -> tuple[float, dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 297) — ``w_i`` (§8.7) from the scores whose windows closed before ``at``; with no randomized check, none forms.
- `class NumericPolicy` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 350) — What π_Q computed for one decision (its status, choice, evaluation and the trace's sections).
- `generator_now(config: Any, objective: str | None=None) -> str` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 381) — RO6: the generator version a decision made now is logged under (``tail_data.generator`` over its trace).
- `run_numeric(vault: Any, repository: Any, *, state: PlanState, support: Sequence[str], candidates: Mapping[str, BlockCandidate], now_iso: str, seed: str, deadline: float | None, keep_going: Any=None, forecasts: Any=None, clock: Any=time.monotonic, publish: Any=None, sequences: Mapping[str, Sequence[BlockCandidate]] | None=None, learned_tail: bool=False, tail_snapshot: Mapping[str, Any] | None=None, carried_valuation: bool=True, defer_carried: Callable[[Callable[[], dict[str, Any]]], None] | None=None) -> NumericPolicy` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 398) — π_Q end to end: the frozen inputs, the day's price, ``Q̄`` with common random numbers (more draws while ``keep_going()``), then, once the LLM policy's forecasts are in (``forecasts()``: None while out), the effect correction; the argmax with the tie rule; the evaluation's baseli…
- `class ObjectiveChooser(RouterChooser)` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 1053) — ``router_objective_v1``: the two policies' learned mix over the staged frame's support.
  - `_seed(self, key: str, decision_id: str) -> str` (line 1058; internal)
  - `choose(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> BlockChoice` (line 1061; public)
  - `_defer_carry(self, numeric: 'NumericPolicy', entry: Any, decision_id: str) -> 'NumericPolicy'` (line 1124; internal) — The follow-up batch's item 4 (RO6's open items 1 and 3): a decision served before its carried valuation existed hands it to the next boundary's prefetch (the no-model branch, which has none, to a thread of its own started after this decision), off the serving path; a later decis…
  - `_tail_snapshot(self, now_iso: str) -> Mapping[str, Any] | None` (line 1151; internal) — RO6: the residual's mutable inputs read now, in the decision's own thread at its moment (F4); None below the tag or with the switch off (nothing read, the predecessor's path), or when it cannot be read (the residual is then left out and the trace says so).
  - `_start_objective(self, key: str, state: PlanState, feasible: Sequence[BlockCandidate], support: Sequence[str], by_id: Mapping[str, BlockCandidate], ready: tuple[str, ...], now_iso: str) -> Prefetch` (line 1168; internal)
  - `_decide_objective(self, entry: Any, state: PlanState, staged: BlockChoice, staged_ref: str, record: dict[str, Any], support: Sequence[str], by_id: Mapping[str, BlockCandidate], feasible: Sequence[BlockCandidate], readiness: Mapping[str, str | None], settings: Mapping[str, Any], now_iso: str) -> BlockChoice` (line 1192; internal)
  - `_session_minutes(self, now_iso: str) -> float | None` (line 1353; internal) — The objective session's active minutes at ``now_iso`` on the serving clock (``price.session_active_minutes``, the price's own construction), or None where they cannot be read (the coin is then not drawn).
  - `_availability(self, state: PlanState, numeric: 'NumericPolicy | None') -> dict[str, Any]` (line 1366; internal) — RO5 §9 item 1: what the learner had when the coin was drawn, read before its uniform: the session's active minutes, the plan's remembered, budgeted and remaining minutes, and the session's availability receipt (RO0 row 8: the minutes offered and their source).
- `class ObjectiveRestraintGate(RestraintGate)` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 1397) — §8.3's mid-block follow-ups: the same two-policy mix over ``{insert_now, continue_current}``.
  - `decide(self, record: Any, current: Any, item: Any, *, wait_feasible: bool=True) -> RestraintOutcome` (line 1403; public)
  - `_no_room(self, state: PlanState, candidates: list[BlockCandidate]) -> RestraintOutcome` (line 1426; internal) — ``wait_feasible = False``: waiting would drop the follow-up from today's plan, so it joins now, deterministically, and no model is asked (Codex review F8's rule, kept by §8.3).
  - `_mixed(self, state: PlanState, candidates: list[BlockCandidate], *, key: str, readiness: Mapping[str, Any], ready: tuple[str, ...], topic: str, options: Sequence[Any], extra: Sequence[str], valued: Mapping[str, BlockCandidate] | None=None, support: Sequence[str]=(INSERT_NOW, CONTINUE_CURRENT), sequences: Mapping[str, Sequence[BlockCandidate]] | None=None, start: Any=None, llm_schema: str=rq.LLM_POLICY_RESTRAINT_SCHEMA) -> RestraintOutcome` (line 1435; internal) — The two-policy mix over ``support`` (§8.3; by default ``{insert_now, continue_current}``), drawn and traced.
  - `_numeric_restraint(self, state: PlanState, insert: BlockCandidate, cont: BlockCandidate, now_iso: str, key: str) -> NumericPolicy` (line 1533; internal) — π_Q on the two orders, each an ordered sequence of the two blocks (the follow-up, then the remaining questions; or the reverse), every step valued with its own kind, duration, observation and effect on one clock; one cutoff, the same draws, each step its own noise in either orde…
  - `_start_policy(self, key: str, state: PlanState, candidates: list[BlockCandidate], topic: str, options: Sequence[Any], extra: Sequence[str], ready: tuple[str, ...]) -> Prefetch` (line 1546; internal) — The two models' prefetch: the Decider's R2c restraint request (advice) and the LLM policy's v3 one.
- `class ObjectiveFollowupGate(ObjectiveRestraintGate, FollowupGate)` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 1596) — §8.3 for FG1's generated probe at RO5's tag: the follow-up's ``plan_interrupt`` decision, made before its item exists, on the same two-policy mix as every mid-block follow-up, with its trace and ``μ`` recomputable (``mix.recompute``).
  - `decide_followup(self, record: Any, current: Any, workflow: Mapping[str, Any], *, wait_feasible: bool, facts: Sequence[str]=()) -> RestraintOutcome` (line 1611; public)
  - `_start_choice(self, key: str, state: PlanState, candidates: list[BlockCandidate], topic: str, options: Sequence[Any], extra: Sequence[str], ready: tuple[str, ...]) -> Prefetch` (line 1655; internal) — The two models' prefetch for the three arms: the Decider's R2c restraint request (advice, ``P(yes)``) and the LLM policy's ``router_llm_choice_v3`` (a probability per option; the reference row is the current block's rest, the continuation ``π_Q``'s tail assumes).
  - `_followup_minutes(self, workflow: Mapping[str, Any], current: Any) -> float` (line 1697; internal) — The generated question's minutes for ``π_Q``: the missed question's own estimate (the probe is written on its LO, after it), else the mean of the LO's items', else the current block's mean question.

### Module constants

- `LOG` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 91)
- `NUMERIC` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 93)
- `PUBLISHED` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 96)
- `CARRIED` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 99)
- `CARRY_LIMIT` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 105)
- `_CARRY_LOCK` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 106)
- `_CARRY` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 107)
- `MODE` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 108)
- `KEY_VERSION` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 109)
- `WHY_VERSION` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 110)
- `_FAILURES` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 112)
- `FOLLOWUP_PLACEHOLDER_PREFIX` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 1592)

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

- `_local_date(now_iso: str) -> str` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 135)
- `_merged(config: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 143) — The follow-up batch's item 3 (Codex review F2): the rollouts' merged tail sessions serve only at the batch's tag with ``[router_objective] merged_sessions``.
- `_consistent_draw(config: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 156) — The follow-up batch's landing ruling R1: the rollouts draw a practised topic's practice outcome from the memory model's own ``P(perform)`` (``value.REVIEW_DRAW_VERSION``) only at the batch's tag with ``[router_objective] consistent_review_draw``; below the tag, or off, mvp-0.49'…
- `_held_link(config: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 168) — Router speed, item 1 (Codex review F1): R9's link values held per role in the rollouts (``value.Inputs.ad_link``'s ``held_ad_link``) only at the follow-up batch's tag with ``[router_objective] held_ad_link``; off, the batch's landing code (the same values per draw, at the landin…
- `_serving_switches(config: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 181) — The trace's ``versions.serving_switches`` (landing ruling R8), or nothing below the batch's tag.
- `_rollout_options(config: Any) -> dict[str, bool]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 190) — The rollouts' serving options, for every rollout of one decision (its evaluation and refinement, the correction, the carried valuation, the baselines and the day's gain curve) or for none: one place.
- `_frontier(inputs: V.Inputs, *, draws: int, seed: str, **rollout: bool) -> tuple[dict[float, float], dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 198)
- `_posterior_price(repository: Any, inputs: V.Inputs, config: Any, *, local_date: str, draws: int, seed: str) -> tuple[P.Seeded, dict[str, Any]] | None` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 209) — RO5 §9 item 1: once a randomized stop offer has a response, κ0 is the posterior the seed is folded into (:mod:`learnloop.router_objective.stop_coin`) and the daily re-centring ends; the frontier is still drawn once a day, for display.
- `_randomized_checks_exist(repository: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 279) — Whether any RO5 randomized cold check was ever assigned (none before RO5).
- `_seed_record(seeds: W.Seeds) -> dict[str, float]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 292)
- `_reference_description(action: V.Action, titles: Mapping[str, str]) -> str` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 595)
- `_llm_forecasts(entry: Prefetch) -> Any` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 601) — The numeric job's view of the LLM policy's forecasts: None while it is out, else ``(per option, reference)`` (both None when it failed).
- `_objective_job(entry: Prefetch, *, runtime: RouterRuntime, vault: Any, sqlite_path: Any, session_id: str | None, plan_id: str | None) -> None` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 616)
- `_with_carried(numeric: 'NumericPolicy | None', entry: Any) -> 'NumericPolicy | None'` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 733) — Landing ruling R12: the served answer's residual with the carried valuation if the job had it before this serve (``CARRIED``), else marked valued too late (``not_valued_before_the_serve``: the backup into this decision is censored ``cutoff_unmatched``).
- `_carry_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 754)
- `_register_carry(sqlite_path: Any, decision_id: str, compute: Callable[[], dict[str, Any]]) -> None` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 761) — The follow-up batch's item 4: a decision served before its carried valuation existed leaves the valuation (its own frozen inputs, in ``compute``) to the next boundary's prefetch.
- `_drain_carry(sqlite_path: Any, *, deadline: float | None=None) -> int` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 771) — Run every deferred carried valuation of this database not yet run (a prefetch job's, after its own answer released the serve's wait; the no-model branch's thread, after its serve), each by ``deadline`` (the runner's own).
- `_carried_for(repository: Any, decision_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 795) — The deferred carried valuations ready to be recorded in this decision's trace (``carried_for``).
- `_wait_llm(entry: Prefetch, runtime: RouterRuntime) -> Any` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 831)
- `_support_labels(support: Sequence[str], by_id: Mapping[str, BlockCandidate], titles: Mapping[str, str]) -> dict[str, str]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 841)
- `_score_note(config: Any) -> str` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 854)
- `_goal_dates(numeric: 'NumericPolicy | None') -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 863) — RO5 §9 item 3's sensor input: each active dated goal's uses with the memory model's frozen forecast at the goal's date (``m⁰``, from the pre-action belief under the tail, the same number the policy comparison logs) and the goal's absolute ``due_at``, for every dated goal the rol…
- `_trace(*, support: Sequence[str], by_id: Mapping[str, BlockCandidate], feasible: Sequence[BlockCandidate], titles: Mapping[str, str], numeric: NumericPolicy | None, llm: ComponentResult | None, decider: ComponentResult | None, staged_ref: str, weight: tuple[float, Mapping[str, Any]], effective: Mapping[str, float], pi: Mapping[str, float], drawn: Any, seed: str, config: Any, now_iso: str, guard: Mapping[str, Any], stop_in_support: bool, card_version: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 884)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `current_weight`; statically calls `current_weight`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `ObjectiveChooser`, `ObjectiveRestraintGate`; statically calls `ObjectiveChooser`, `ObjectiveRestraintGate`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `ObjectiveFollowupGate`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/daily_plan/objective_card|learnloop.daily_plan.objective_card]] — imports `decision_card`; calls `decision_card`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; calls `build`, `decision_reads`
- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `FollowupGate`, `INSERT_NOW`, `MODE`, `NO_INTERVENTION`, `RestraintGate`, `RestraintOutcome`, `RouterChooser`, `_NoModels`, `_await`, `_build_card`, `_card_fields`, `_hash`, `_latest_attempt`, `_option`, `_payloads`, `_rule_sentence`, `_run_components`, `router_settings`, `support_order`; calls `RestraintOutcome`, `_NoModels`, `_await`, `_build_card`, `_card_fields`, `_hash`, `_latest_attempt`, `_option`, `_payloads`, `_rule_sentence`, `_run_components`, `router_settings`, `support_order`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `ANSWERED`, `ComponentResult`, `DECIDER`, `FAILED`, `INVALID`, `LLM`, `NOT_READY`, `Prefetch`, `RECEIPT_OWNER`, `RouterRuntime`, `TIMEOUT`, `call_decider`, `call_llm`; calls `ComponentResult`
- [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]] — imports `StagedChooser`; calls `StagedChooser`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `BlockCandidate`, `BlockChoice`, `CONTINUE_CURRENT`, `PlanState`, `STOP_FOR_TODAY`, `STOP_OFFER_MINUTES`; calls `BlockChoice`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `session_receipt`, `table_present`, `traces`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/router/requests|learnloop.router.requests]] — imports `module`; calls `BlockOption`, `BoundaryRequest`, `PolicyRequest`, `RestraintRequest`, `evidence_from_card`, `parse_decider_restraint`, `parse_llm_policy`, `parse_llm_policy_restraint`, `state_text`
- [[Reference/Modules/learnloop/router/why|learnloop.router.why]] — imports `module`; calls `objective_why`, `rationale_guard`, `sentence`
- [[Reference/Modules/learnloop/router_objective/mix|learnloop.router_objective.mix]] — imports `module`; calls `components`, `draw`, `effective_weights`, `fallback_label`, `seed_for`
- [[Reference/Modules/learnloop/router_objective/price|learnloop.router_objective.price]] — imports `module`; calls `Seeded`, `guard_minutes`, `seed_from_gain`, `session_active_minutes`
- [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] — imports `module`; calls `scores`
- [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]] — imports `module`; calls `eligible`, `flip`, `handed_over`, `pending_assignment`, `served_distribution`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `module`; calls `carried_in_prefetch_on`, `generator_key`, `generator_payload`, `objective_hash`, `scope_extension_on`
- [[Reference/Modules/learnloop/router_objective/tail_serve|learnloop.router_objective.tail_serve]] — imports `module`; calls `candidate_terms`, `carried_cutoff`, `is_pending`, `measurable`, `not_before_the_serve`, `not_on_the_serving_path`, `pending_after_the_answer`, `residual`, `shifted`, `snapshot`, `with_carried_values`
- [[Reference/Modules/learnloop/router_objective/value|learnloop.router_objective.value]] — imports `module`; calls `EffectSlope`, `_Model`, `baselines`, `evaluate`, `gain`, `numeric_choice`, `paired_standard_error`
- [[Reference/Modules/learnloop/router_objective/weight|learnloop.router_objective.weight]] — imports `module`; calls `Scored`, `posterior`, `unique_assessments`, `weight`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `CHECKS_OFF`, `calibrated_weight_on`, `calibration_tag`, `check_mode`, `followup_generator_switches`, `followup_on`, `followup_switch_snapshot`, `learned_tail_on`, `objective_scores_on`, `stop_coin_rate`; calls `calibrated_weight_on`, `calibration_tag`, `check_mode`, `followup_generator_switches`, `followup_on`, `followup_switch_snapshot`, `learned_tail_on`, `objective_scores_on`, `stop_coin_rate`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextvars`, `dataclasses`, `datetime`, `functools`, `hashlib`, `json`, `logging`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]], [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]], [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

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
- [tests/test_ro6_codex_review.py](../../../../../../tests/test_ro6_codex_review.py) — direct import
  - `test_f4_a_diagnosis_queued_after_the_decisions_moment_never_enters_its_features`
- [tests/test_ro6_landing.py](../../../../../../tests/test_ro6_landing.py) — direct import
  - `test_r12_with_the_carried_evaluation_blocked_the_choosers_wait_returns`
  - `test_r3_the_no_model_branch_answers_within_the_first_pass_and_censors_the_carried_backup`
- [tests/test_ro6_serving.py](../../../../../../tests/test_ro6_serving.py) — direct import
- [tests/test_ro6_tail_data.py](../../../../../../tests/test_ro6_tail_data.py) — direct import
  - `test_refitting_on_a_later_version_does_not_change_version_ks_evaluation`
- [tests/test_rofu_ad_link.py](../../../../../../tests/test_rofu_ad_link.py) — direct import
  - `test_the_numeric_policy_reads_ads_own_predictive_only_at_the_tag_with_its_switch`
- [tests/test_rofu_carried.py](../../../../../../tests/test_rofu_carried.py) — direct import
  - `test_an_early_publication_served_keeps_its_carried_valuation`
  - `test_the_no_model_branch_defers_its_carried_valuation_off_the_serving_path`
  - `test_with_models_the_wait_returns_and_the_next_prefetch_runs_it`
- [tests/test_rofu_review_draw.py](../../../../../../tests/test_rofu_review_draw.py) — direct import
  - `test_the_numeric_policy_draws_consistently_only_at_the_tag_with_its_switch`
- [tests/test_rofu_speed.py](../../../../../../tests/test_rofu_speed.py) — direct import
  - `test_the_numeric_policy_merges_only_at_the_tag_with_its_switch`
- [tests/test_rofu_switch_key.py](../../../../../../tests/test_rofu_switch_key.py) — direct import
  - `test_a_served_cached_answer_names_the_generator_that_produced_it`
  - `test_below_the_tag_the_key_names_no_switch`
- [tests/test_rospeed_ad_link.py](../../../../../../tests/test_rospeed_ad_link.py) — direct import
  - `test_the_switch_reaches_every_rollout_from_the_config`
- [tests/test_rospeed_join.py](../../../../../../tests/test_rospeed_join.py) — direct import
  - `test_the_prefetch_job_reads_the_fit_again_only_after_a_commit`

## Modification guidance

- Make changes here when the responsibility remains objective chooser within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.daily_plan.objective_chooser"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/objective_chooser.py"
source_paths:
  - "src/learnloop/daily_plan/objective_chooser.py"
source_commit: "940190f3d6efca88c388e1832ce8bce90ae2ae3d"
source_commit_timestamp: "2026-11-05T11:55:22-05:00"
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
| Source lines | 1276 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `940190f3d6efca88c388e1832ce8bce90ae2ae3d` |
| Commit timestamp | `2026-11-05T11:55:22-05:00` |

## Public API

- `objective_settings(config: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 104)
- `day_price(repository: Any, inputs: V.Inputs, *, local_date: str, draws: int, seed: str, config: Any=None) -> tuple[P.Seeded, dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 162) — κ0 for this decision (§8.6): the day's first decision computes the seed from the gain curve, later ones carry it.
- `current_weight(repository: Any, config: Any, *, at: str) -> tuple[float, dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 220) — ``w_i`` (§8.7) from the scores whose windows closed before ``at``; with no randomized check, none forms.
- `class NumericPolicy` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 273) — What π_Q computed for one decision (its status, choice, evaluation and the trace's sections).
- `run_numeric(vault: Any, repository: Any, *, state: PlanState, support: Sequence[str], candidates: Mapping[str, BlockCandidate], now_iso: str, seed: str, deadline: float | None, keep_going: Any=None, forecasts: Any=None, clock: Any=time.monotonic, publish: Any=None, sequences: Mapping[str, Sequence[BlockCandidate]] | None=None) -> NumericPolicy` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 294) — π_Q end to end: the frozen inputs, the day's price, ``Q̄`` with common random numbers (more draws while ``keep_going()``), then, once the LLM policy's forecasts are in (``forecasts()``: None while out), the effect correction; the argmax with the tie rule; the evaluation's baseli…
- `class ObjectiveChooser(RouterChooser)` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 670) — ``router_objective_v1``: the two policies' learned mix over the staged frame's support.
  - `_seed(self, key: str, decision_id: str) -> str` (line 675; internal)
  - `choose(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> BlockChoice` (line 678; public)
  - `_start_objective(self, key: str, state: PlanState, feasible: Sequence[BlockCandidate], support: Sequence[str], by_id: Mapping[str, BlockCandidate], ready: tuple[str, ...], now_iso: str) -> Prefetch` (line 732; internal)
  - `_decide_objective(self, entry: Any, state: PlanState, staged: BlockChoice, staged_ref: str, record: dict[str, Any], support: Sequence[str], by_id: Mapping[str, BlockCandidate], feasible: Sequence[BlockCandidate], readiness: Mapping[str, str | None], settings: Mapping[str, Any], now_iso: str) -> BlockChoice` (line 753; internal)
  - `_session_minutes(self, now_iso: str) -> float | None` (line 904; internal) — The objective session's active minutes at ``now_iso`` on the serving clock (``price.session_active_minutes``, the price's own construction), or None where they cannot be read (the coin is then not drawn).
  - `_availability(self, state: PlanState, numeric: 'NumericPolicy | None') -> dict[str, Any]` (line 917; internal) — RO5 §9 item 1: what the learner had when the coin was drawn, read before its uniform: the session's active minutes, the plan's remembered, budgeted and remaining minutes, and the session's availability receipt (RO0 row 8: the minutes offered and their source).
- `class ObjectiveRestraintGate(RestraintGate)` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 948) — §8.3's mid-block follow-ups: the same two-policy mix over ``{insert_now, continue_current}``.
  - `decide(self, record: Any, current: Any, item: Any, *, wait_feasible: bool=True) -> RestraintOutcome` (line 954; public)
  - `_no_room(self, state: PlanState, candidates: list[BlockCandidate]) -> RestraintOutcome` (line 977; internal) — ``wait_feasible = False``: waiting would drop the follow-up from today's plan, so it joins now, deterministically, and no model is asked (Codex review F8's rule, kept by §8.3).
  - `_mixed(self, state: PlanState, candidates: list[BlockCandidate], *, key: str, readiness: Mapping[str, Any], ready: tuple[str, ...], topic: str, options: Sequence[Any], extra: Sequence[str], valued: Mapping[str, BlockCandidate] | None=None, support: Sequence[str]=(INSERT_NOW, CONTINUE_CURRENT), sequences: Mapping[str, Sequence[BlockCandidate]] | None=None, start: Any=None, llm_schema: str=rq.LLM_POLICY_RESTRAINT_SCHEMA) -> RestraintOutcome` (line 986; internal) — The two-policy mix over ``support`` (§8.3; by default ``{insert_now, continue_current}``), drawn and traced.
  - `_numeric_restraint(self, state: PlanState, insert: BlockCandidate, cont: BlockCandidate, now_iso: str, key: str) -> NumericPolicy` (line 1084; internal) — π_Q on the two orders, each an ordered sequence of the two blocks (the follow-up, then the remaining questions; or the reverse), every step valued with its own kind, duration, observation and effect on one clock; one cutoff, the same draws, each step its own noise in either orde…
  - `_start_policy(self, key: str, state: PlanState, candidates: list[BlockCandidate], topic: str, options: Sequence[Any], extra: Sequence[str], ready: tuple[str, ...]) -> Prefetch` (line 1097; internal) — The two models' prefetch: the Decider's R2c restraint request (advice) and the LLM policy's v3 one.
- `class ObjectiveFollowupGate(ObjectiveRestraintGate, FollowupGate)` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 1147) — §8.3 for FG1's generated probe at RO5's tag: the follow-up's ``plan_interrupt`` decision, made before its item exists, on the same two-policy mix as every mid-block follow-up, with its trace and ``μ`` recomputable (``mix.recompute``).
  - `decide_followup(self, record: Any, current: Any, workflow: Mapping[str, Any], *, wait_feasible: bool, facts: Sequence[str]=()) -> RestraintOutcome` (line 1162; public)
  - `_start_choice(self, key: str, state: PlanState, candidates: list[BlockCandidate], topic: str, options: Sequence[Any], extra: Sequence[str], ready: tuple[str, ...]) -> Prefetch` (line 1206; internal) — The two models' prefetch for the three arms: the Decider's R2c restraint request (advice, ``P(yes)``) and the LLM policy's ``router_llm_choice_v3`` (a probability per option; the reference row is the current block's rest, the continuation ``π_Q``'s tail assumes).
  - `_followup_minutes(self, workflow: Mapping[str, Any], current: Any) -> float` (line 1248; internal) — The generated question's minutes for ``π_Q``: the missed question's own estimate (the probe is written on its LO, after it), else the mean of the LO's items', else the current block's mean question.

### Module constants

- `LOG` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 91)
- `NUMERIC` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 93)
- `PUBLISHED` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 96)
- `MODE` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 97)
- `KEY_VERSION` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 98)
- `WHY_VERSION` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 99)
- `_FAILURES` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 101)
- `FOLLOWUP_PLACEHOLDER_PREFIX` ([src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 1143)

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

- `_local_date(now_iso: str) -> str` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 114)
- `_frontier(inputs: V.Inputs, *, draws: int, seed: str) -> tuple[dict[float, float], dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 122)
- `_posterior_price(repository: Any, inputs: V.Inputs, config: Any, *, local_date: str, draws: int, seed: str) -> tuple[P.Seeded, dict[str, Any]] | None` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 132) — RO5 §9 item 1: once a randomized stop offer has a response, κ0 is the posterior the seed is folded into (:mod:`learnloop.router_objective.stop_coin`) and the daily re-centring ends; the frontier is still drawn once a day, for display.
- `_randomized_checks_exist(repository: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 202) — Whether any RO5 randomized cold check was ever assigned (none before RO5).
- `_seed_record(seeds: W.Seeds) -> dict[str, float]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 215)
- `_reference_description(action: V.Action, titles: Mapping[str, str]) -> str` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 368)
- `_llm_forecasts(entry: Prefetch) -> Any` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 374) — The numeric job's view of the LLM policy's forecasts: None while it is out, else ``(per option, reference)`` (both None when it failed).
- `_objective_job(entry: Prefetch, *, runtime: RouterRuntime, vault: Any, sqlite_path: Any, session_id: str | None, plan_id: str | None) -> None` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 389)
- `_wait_llm(entry: Prefetch, runtime: RouterRuntime) -> Any` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 483)
- `_support_labels(support: Sequence[str], by_id: Mapping[str, BlockCandidate], titles: Mapping[str, str]) -> dict[str, str]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 493)
- `_score_note(config: Any) -> str` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 506)
- `_goal_dates(numeric: 'NumericPolicy | None') -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 515) — RO5 §9 item 3's sensor input: each active dated goal's uses with the memory model's frozen forecast at the goal's date (``m⁰``, from the pre-action belief under the tail, the same number the policy comparison logs) and the goal's absolute ``due_at``, for every dated goal the rol…
- `_trace(*, support: Sequence[str], by_id: Mapping[str, BlockCandidate], feasible: Sequence[BlockCandidate], titles: Mapping[str, str], numeric: NumericPolicy | None, llm: ComponentResult | None, decider: ComponentResult | None, staged_ref: str, weight: tuple[float, Mapping[str, Any]], effective: Mapping[str, float], pi: Mapping[str, float], drawn: Any, seed: str, config: Any, now_iso: str, guard: Mapping[str, Any], stop_in_support: bool, card_version: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_chooser.py), line 536)

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
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; calls `build`
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
- [[Reference/Modules/learnloop/router_objective/value|learnloop.router_objective.value]] — imports `module`; calls `EffectSlope`, `_Model`, `baselines`, `evaluate`, `gain`, `numeric_choice`, `paired_standard_error`
- [[Reference/Modules/learnloop/router_objective/weight|learnloop.router_objective.weight]] — imports `module`; calls `Scored`, `posterior`, `unique_assessments`, `weight`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `CHECKS_OFF`, `calibrated_weight_on`, `calibration_tag`, `check_mode`, `objective_scores_on`, `stop_coin_rate`; calls `calibrated_weight_on`, `calibration_tag`, `check_mode`, `objective_scores_on`, `stop_coin_rate`

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

## Modification guidance

- Make changes here when the responsibility remains objective chooser within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/objective_chooser.py](../../../../../../src/learnloop/daily_plan/objective_chooser.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

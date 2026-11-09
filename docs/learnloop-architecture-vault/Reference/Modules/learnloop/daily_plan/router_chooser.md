---
title: "learnloop.daily_plan.router_chooser"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/router_chooser.py"
source_paths:
  - "src/learnloop/daily_plan/router_chooser.py"
source_commit: "2908b71c8db6ae7290ccecd559d58b3b14f5597c"
source_commit_timestamp: "2026-11-08T19:18:24-05:00"
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
  - "learnloop.daily_plan.router_chooser module"
  - "src/learnloop/daily_plan/router_chooser.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.router_chooser`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.router_chooser` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Router R2b + R2c: the mixture chooser and the restraint gate on Today.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/router_chooser.py](../../../../../../src/learnloop/daily_plan/router_chooser.py) |
| Source lines | 980 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2908b71c8db6ae7290ccecd559d58b3b14f5597c` |
| Commit timestamp | `2026-11-08T19:18:24-05:00` |

## Public API

- `router_settings(config: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 103) — The router settings a decision's key and record carry.
- `support_order(state: PlanState, candidates: Sequence[BlockCandidate], staged_id: str, *, k: int, stop_offered: bool, ties_only: bool) -> list[str]` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 127) — The top-k options in the deterministic order of plan §3.3 item 3.
- `favoured_option(distribution: Mapping[str, float] | None) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 167) — The one option a model's distribution puts the most on (None on a tie at the top).
- `class RouterChooser` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 371) — ``router_mixture_v1``: the logged model mixture over the staged frame's candidates.
  - `scope(self) -> str` (line 389; public)
  - `_now_iso(self) -> str` (line 392; internal)
  - `choose(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> BlockChoice` (line 397; public)
  - `_freeze_objective(self, record: dict[str, Any], staged: BlockChoice, feasible: Sequence[BlockCandidate], support: Sequence[str]) -> None` (line 451; internal) — Data capture A2: the objective the arms are evaluated on, frozen from pre-draw inputs only, just before the draw (a read whose models are still out reaches neither).
  - `_start(self, key: str, state: PlanState, feasible: Sequence[BlockCandidate], support: Sequence[str], by_id: Mapping[str, BlockCandidate], ready: tuple[str, ...]) -> Prefetch` (line 462; internal)
  - `_decide(self, entry: Prefetch, state: PlanState, staged: BlockChoice, record: dict[str, Any], support: Sequence[str], by_id: Mapping[str, BlockCandidate], readiness: Mapping[str, str | None], settings: Mapping[str, Any], *, decided_by: str='mixture') -> BlockChoice` (line 491; internal)
- `class RestraintOutcome` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 598) — A follow-up's ``plan_interrupt`` decision, made outside any write.
  - `insert(self) -> bool` (line 611; public)
  - `wait(self) -> bool` (line 615; public)
- `class RestraintGate` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 620) — ``plan_interrupt``: insert a placeable mid-block follow-up now, or let it wait.
  - `scope(self) -> str` (line 633; public)
  - `refusals(self, item: Any) -> tuple[dict[str, Any], ...]` (line 636; public) — The P4 constraint engine's named refusals of one follow-up (none: placeable).
  - `declined(refusals: Sequence[Mapping[str, Any]]) -> RestraintOutcome` (line 642; public) — A refused follow-up's deterministic ``decline`` (no model is asked).
  - `_refusals(self, item: Any) -> tuple[dict[str, Any], ...]` (line 652; internal)
  - `decide(self, record: Any, current: Any, item: Any, *, wait_feasible: bool=True) -> RestraintOutcome` (line 662; public) — The decision for one follow-up the rules would place now (raises :class:`DecisionPending` on a read whose models are still out).
  - `_state(self, record: Any, current: Any, item: Any) -> tuple[PlanState, list[BlockCandidate]]` (line 754; internal)
  - `_start(self, key: str, state: PlanState, candidates: list[BlockCandidate], item: Any, ready: tuple[str, ...]) -> Prefetch` (line 779; internal)
- `class FollowupGate(RestraintGate)` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 833) — FG1 §5: whether and when, before any item exists.
  - `_support(self, *, wait_feasible: bool) -> list[str]` (line 842; internal)
  - `_followup_state(self, record: Any, current: Any, workflow: Mapping[str, Any]) -> tuple[PlanState, list[BlockCandidate]]` (line 845; internal)
  - `decide_followup(self, record: Any, current: Any, workflow: Mapping[str, Any], *, wait_feasible: bool, facts: Sequence[str]=()) -> RestraintOutcome` (line 871; public) — The draw; raises nothing: failed models give their weight to the staged rule.
  - `_start_followup(self, key: str, state: PlanState, candidates: list[BlockCandidate], workflow: Mapping[str, Any], ready: tuple[str, ...], support: Sequence[str], facts: Sequence[str]) -> Prefetch` (line 938; internal)

### Module constants

- `LOG` ([src/learnloop/daily_plan/router_chooser.py](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 87)
- `CHOOSER_NAME` ([src/learnloop/daily_plan/router_chooser.py](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 89)
- `MODE` ([src/learnloop/daily_plan/router_chooser.py](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 90)
- `KEY_VERSION` ([src/learnloop/daily_plan/router_chooser.py](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 91)
- `INSERT_NOW` ([src/learnloop/daily_plan/router_chooser.py](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 92)
- `NO_INTERVENTION` ([src/learnloop/daily_plan/router_chooser.py](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 810)

### Explicit exports

`__all__` declares:

- `CHOOSER_NAME`
- `FollowupGate`
- `INSERT_NOW`
- `NO_INTERVENTION`
- `MODE`
- `RestraintGate`
- `RestraintOutcome`
- `RouterChooser`
- `router_settings`
- `support_order`

## Internal implementation anchors

- `_canonical(value: Any) -> str` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 95)
- `_hash(value: Any) -> str` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 99)
- `_latest_attempt(repository: Any) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 119)
- `_rule_sentence(candidate: BlockCandidate | None, state: PlanState) -> tuple[str, str]` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 177)
- `_option(candidate: BlockCandidate, titles: Mapping[str, str]) -> rq.BlockOption` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 186)
- `_run_components(runtime: RouterRuntime, entry: Prefetch, vault: Any, repository: Any, request: Any, parse: Mapping[str, Any], card_hash: str | None) -> None` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 202) — Ask every component of ``entry`` (the Decider on this thread, the LLM on its own).
- `_block_job(entry: Prefetch, *, runtime: RouterRuntime, vault: Any, sqlite_path: Any, session_id: str | None, plan_id: str | None) -> None` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 248)
- `_restraint_job(entry: Prefetch, *, runtime: RouterRuntime, vault: Any, sqlite_path: Any) -> None` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 281)
- `_await(runtime: RouterRuntime, entry: Prefetch, *, may_defer: bool, timeout: float) -> None` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 300)
- `_results(entry: Prefetch, readiness: Mapping[str, str | None]) -> dict[str, ComponentResult]` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 309)
- `_payloads(results: Mapping[str, ComponentResult]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 317)
- `class _Card` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 328)
- `_build_card(builder: CardBuilder | None, state: PlanState, feasible: Sequence[BlockCandidate]) -> _Card` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 337)
- `_card_fields(card: _Card) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 350)
- `class _NoModels` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 357) — A decision no model is asked about: the prefetch's shape with no job (data capture A5).
- `_followup_job(entry: Prefetch, *, runtime: RouterRuntime, vault: Any, sqlite_path: Any) -> None` ([source](../../../../../../src/learnloop/daily_plan/router_chooser.py), line 813)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `FollowupGate`, `INSERT_NOW`, `MODE`, `NO_INTERVENTION`, `RestraintGate`, `RestraintOutcome`, `RouterChooser`, `_NoModels`, `_await`, `_build_card`, `_card_fields`, `_hash`, `_latest_attempt`, `_option`, `_payloads`, `_rule_sentence`, `_run_components`, `router_settings`, `support_order`; statically calls `RestraintOutcome`, `_NoModels`, `_await`, `_build_card`, `_card_fields`, `_hash`, `_latest_attempt`, `_option`, `_payloads`, `_rule_sentence`, `_run_components`, `router_settings`, `support_order`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `RestraintGate`, `RouterChooser`; statically calls `RestraintGate`, `RouterChooser`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `FollowupGate`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/daily_plan/chooser|learnloop.daily_plan.chooser]] — imports `LaneQuotaChooser`, `unspent_share`; calls `unspent_share`
- [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]] — imports `module`; calls `freeze`
- [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]] — imports `module`; calls `prepare`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `ANSWERED`, `ComponentResult`, `DECIDER`, `INVALID`, `LLM`, `NOT_READY`, `Prefetch`, `RECEIPT_OWNER`, `RouterRuntime`, `call_decider`, `call_llm`; calls `ComponentResult`
- [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]] — imports `CardBuilder`, `StagedChooser`; calls `StagedChooser`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `BlockCandidate`, `BlockChoice`, `CONTINUE_CURRENT`, `DecisionPending`, `LANES`, `PlanState`, `STOP_FOR_TODAY`, `STOP_OFFER_MINUTES`; calls `BlockCandidate`, `BlockChoice`, `DecisionPending`, `PlanState`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `serving_on`; calls `serving_on`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/router/mixture|learnloop.router.mixture]] — imports `module`; calls `component_distributions`, `draw`, `effective_weights`, `fallback_label`
- [[Reference/Modules/learnloop/router/plan_log|learnloop.router.plan_log]] — imports `module`
- [[Reference/Modules/learnloop/router/requests|learnloop.router.requests]] — imports `module`; calls `BlockOption`, `BoundaryRequest`, `RestraintRequest`, `SensorTopic`, `evidence_from_card`, `option_description`, `parse_decider_restraint`, `parse_llm_restraint`, `state_text`
- [[Reference/Modules/learnloop/router/why|learnloop.router.why]] — imports `module`; calls `model_why`, `rationale_guard`, `sentence`, `stop_code`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextvars`, `dataclasses`, `functools`, `hashlib`, `json`, `logging`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]], [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_data_capture_a5_not_ready_floor.py](../../../../../../tests/test_data_capture_a5_not_ready_floor.py) — direct import
  - `test_the_restraint_keeps_the_floor_on_not_ready_too`
- [tests/test_followup_router.py](../../../../../../tests/test_followup_router.py) — direct import
  - `test_data_captures_objective_is_frozen_for_every_arm`
  - `test_no_intervention_sits_in_the_mixture_with_its_floor`
  - `test_outcome_joins_follow_the_binding`
  - `test_the_binding_is_appended_and_the_row_stays_as_it_was`
  - `test_the_decision_line_says_what_the_screen_should`
  - `test_the_decision_row_is_itemless_and_names_the_workflow`
  - `test_waiting_is_out_of_the_support_when_there_is_no_room`
  - `test_with_no_binding_a_decision_has_no_action_to_follow`
- [tests/test_ih2_lessons_compete.py](../../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_a_lesson_win_after_a_miss_generates_nothing_and_the_offer_page_opens_from_next`
  - `test_a_probe_whose_decision_already_beat_the_lesson_is_not_contested_twice`
  - `test_a_probe_win_after_a_miss_generates_and_serves_as_before`
  - `test_a_question_not_yet_written_takes_the_probe_interface_only_with_the_lesson_in_the_support`
  - `test_no_lesson_available_the_followup_decision_is_the_predecessors`
  - `test_not_now_after_a_miss_goes_back_to_a_new_decision_and_the_block_resumes`
  - `test_off_or_below_the_tag_the_followup_decision_is_the_predecessors`
  - `test_the_followup_decision_values_the_unwritten_probe_with_the_probe_interface`
  - `test_the_journey_on_a_real_miss_lesson_then_not_now_then_the_question`
  - `test_the_need_paths_mid_block_decision_gains_the_lesson_arm`
  - `test_with_no_room_to_wait_a_lesson_makes_it_a_real_draw_and_with_none_it_stays_deterministic`
- [tests/test_ih_numeric_seed.py](../../../../../../tests/test_ih_numeric_seed.py) — direct import
  - `test_the_need_paths_decision_with_no_lesson_seeds_from_its_identity`
  - `test_the_workflows_arm_with_no_room_to_wait_seeds_from_its_identity`
  - `test_the_workflows_decision_with_no_lesson_keeps_the_predecessors_identity`
- [tests/test_mvp024_upgrade.py](../../../../../../tests/test_mvp024_upgrade.py) — direct import
  - `test_the_mixture_serves_only_at_the_successor_in_mixture_mode`
- [tests/test_ro0_codex_review.py](../../../../../../tests/test_ro0_codex_review.py) — direct import
- [tests/test_ro5_landing.py](../../../../../../tests/test_ro5_landing.py) — direct import
  - `test_r5_1_at_the_tag_fg1s_gate_is_the_two_policy_mix_with_its_trace`
  - `test_r5_1_below_the_tag_and_with_the_objective_off_fg1s_gate_is_unchanged`
  - `test_r5_1_no_room_to_wait_asks_now_deterministically_and_asks_no_model`
  - `test_r8_each_arm_can_be_drawn_with_its_logged_probability_and_no_intervention_serves_no_probe`

## Modification guidance

- Make changes here when the responsibility remains router chooser within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/router_chooser.py](../../../../../../src/learnloop/daily_plan/router_chooser.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

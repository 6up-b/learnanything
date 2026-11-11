---
title: "learnloop.daily_plan.measurement"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/measurement.py"
source_paths:
  - "src/learnloop/daily_plan/measurement.py"
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
  - "learnloop.daily_plan.measurement module"
  - "src/learnloop/daily_plan/measurement.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.measurement`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.measurement` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: A2: outcomes for reading, wait and stop arms: the objective frozen, the measurement arranged.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py) |
| Source lines | 623 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class FrozenObjective` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 119) — What a decision's arms are evaluated on, from pre-draw inputs only.
  - `as_dict(self) -> dict[str, Any]` (line 130; public)
  - `from_dict(cls, row: Mapping[str, Any]) -> 'FrozenObjective'` (line 134; public)
- `freeze(vault: Any, repository: Any, *, staged_ref: str | None, candidates: Sequence[Any], support: Sequence[str], stop_ref: str) -> FrozenObjective` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 141) — The block decision's objective, from the staged pick, the candidates and the support: nothing the draw decides.
- `freeze_followup(learning_object_id: str, *, support: Sequence[str]) -> FrozenObjective` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 179) — A follow-up's now-or-wait decision: its own LO, whichever arm is drawn.
- `with_last_block(frozen: FrozenObjective, learning_object_id: str | None) -> FrozenObjective` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 188) — A stop with no candidate to name its objective: what the plan last worked on (pre-draw too).
- `applies(frozen: FrozenObjective | None, arm: str) -> bool` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 197) — A decision has an objective when an arm of its support, or the drawn one, has no action.
- `record(vault: Any, repository: Any, connection: Any, *, decision_id: str, decision_kind: str, frozen: FrozenObjective, arm: str, exclude: Iterable[str]=(), experiment_id: str | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 310) — Freeze ``frozen`` for a committed decision and arrange its measurement, on the decision's transaction.
- `plan_slots(intent: Any, checks: Sequence[Any], maintain_load: float) -> tuple[list[dict[str, Any]], float]` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 349) — The first block's measurement checks and the maintain-lane minutes they replace.
- `settle(vault: Any, repository: Any, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 436) — Write the measurement states the ledgers now show.

### Module constants

- `OBJECTIVE_VERSION` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 72)
- `VIA` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 74)
- `CHECK_DEPTH_PRESET` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 76)
- `ARM_READING` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 77)
- `ARM_WAIT` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 78)
- `ARM_STOP` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 79)
- `ARM_PRACTICE` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 80)
- `ARM_INSERT` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 81)
- `ARM_NO_INTERVENTION` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 83)
- `ACTIONLESS_ARMS` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 85)
- `ARRANGED` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 87)
- `SHARED` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 88)
- `NATURAL` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 89)
- `UNAVAILABLE` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 90)
- `SOURCE_READING` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 92)
- `SOURCE_STAGED` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 93)
- `SOURCE_SUPPORT` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 94)
- `SOURCE_LAST_BLOCK` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 95)
- `SOURCE_FOLLOWUP` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 96)
- `SOURCE_NONE` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 97)
- `NO_LEARNING_OBJECT` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 100)
- `NO_QUESTION` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 101)
- `CHECKS_OFF` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 102)
- `ARRANGE_FAILED` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 103)
- `COMMITMENT_CLOSED` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 104)
- `CHECK_REPLACED` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 105)
- `ANSWER_NOT_DELAYED` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 107)
- `ANSWER_OTHER_OBJECTIVE` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 109)
- `_UNREAD_ANSWERS` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 111)
- `REPLACEMENT` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 113)
- `SATISFIED_EPISODE` ([src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py), line 115)

### Explicit exports

`__all__` declares:

- `ACTIONLESS_ARMS`
- `ANSWER_NOT_DELAYED`
- `ANSWER_OTHER_OBJECTIVE`
- `ARM_INSERT`
- `ARM_PRACTICE`
- `ARM_READING`
- `ARM_STOP`
- `ARM_WAIT`
- `ARRANGED`
- `FrozenObjective`
- `NATURAL`
- `OBJECTIVE_VERSION`
- `REPLACEMENT`
- `SHARED`
- `UNAVAILABLE`
- `VIA`
- `applies`
- `freeze`
- `freeze_followup`
- `plan_slots`
- `reading_learning_objects`
- `record`
- `settle`
- `with_last_block`

## Internal implementation anchors

- `_window_opens(now: datetime) -> datetime` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 203) — When an answer can first be a delayed retrieval of a decision taken at ``now``: the outcome contract's delay.
- `_due_iso(now: datetime, days: float) -> str` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 209) — The check's date.
- `_pending_checks(serving: Any, item_ids: set[str]) -> list[Any]` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 219) — The pending checks on any item of the objective's LO.
- `_measures_objective(check: Any, item_ids: set[str]) -> bool` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 228) — Every answer that could satisfy this check is on the objective's LO, so it may be shared (landing review F11).
- `class _Arrangement` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 235)
- `_arrange(vault: Any, repository: Any, frozen: FrozenObjective, *, decision_id: str, exclude: Iterable[str], clock: Clock | None) -> _Arrangement` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 245) — The check that measures ``frozen``, on the decision's transaction (its savepoint).
- `_new_check(vault: Any, repository: Any, lo: str, lo_items: Sequence[Any], *, exclude: Iterable[str], decision_id: str, idempotency_key: str, now: datetime, clock: Clock | None) -> _Arrangement` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 273)
- `_replacement_check(vault: Any, repository: Any, decision_id: str, learning_object_id: str | None, *, answered_item: Any, serving: Any, now: datetime, clock: Clock | None, fresh: dict[str, _Arrangement]) -> _Arrangement` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 368) — The duty an unread answer left: one check on the objective that opens past the window from now.
- `_answer_missed_window(connection: Any, attempt_id: str, decided_at: str | None, reader_exposures: Iterable[tuple[str, str]]) -> bool` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 400) — Whether the decision's outcome cannot read this answer because it was warm or exposed (a held or unscorable answer is still an answer: its outcome says why it is not read).
- `_replacement_detail(connection: Any, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 414) — The early answer's event of this decision's measurement, if it had one.
- `_unplanned_reasons(connection: Any, today: str) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 423) — Today's plans' reasons a due check was not planned, by commitment.
- `_local_day(at: str) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 551) — A UTC stamp's local day (the plan's, ``engine.local_date``).
- `_lost(connection: Any, decision_id: str, prefix: str, reason: str, *, at: str, typed: bool=False) -> int` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 558) — The check cannot be offered, in the episode its newest ``due`` or ``offered`` opened: the same reason again only counts after availability came back.
- `_event(connection: Any, decision_id: str, state: str, *, at: str, reason: str='', practice_item_id: str | None=None, attempt_id: str | None=None, detail: Mapping[str, Any] | None=None, episode: str='', typed: bool=False, delay: str | None=None) -> int` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 566)
- `_satisfied_by(connection: Any, commitment_id: str) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 578)
- `_offers(connection: Any, check: Any, row: Mapping[str, Any], *, since: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/measurement.py), line 586) — The check's presentations at or after it came due (its item, or any it decides), oldest first.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `applies`, `freeze`, `freeze_followup`, `plan_slots`, `record`, `with_last_block`
- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `module`; statically calls `freeze`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `module`; statically calls `freeze_followup`, `record`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `module`; statically calls `settle`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `create_commitment`, `resolve_disposition`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `objective_receipts_on`, `serving_on`; calls `objective_receipts_on`, `serving_on`
- [[Reference/Modules/learnloop/data_capture/reading_exposures|learnloop.data_capture.reading_exposures]] — imports `module`, `reading_learning_objects`; calls `read_for_answer`, `reading_learning_objects`, `sweep_quietly`
- [[Reference/Modules/learnloop/db/stores/daily_plans|learnloop.db.stores.daily_plans]] — imports `module`; calls `plans_for_date`
- [[Reference/Modules/learnloop/db/stores/data_capture|learnloop.db.stores.data_capture]] — imports `module`; calls `due_recorded`, `insert_measurement_event`, `insert_objective`, `latest_episode`, `objectives_present`
- [[Reference/Modules/learnloop/delayed_checks|learnloop.delayed_checks]] — imports `module`; calls `attempted_items`, `candidates`, `due_days`, `pick_with_receipt`, `revealed_items`
- [[Reference/Modules/learnloop/delayed_completion|learnloop.delayed_completion]] — imports `module`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `withheld_items`; calls `withheld_items`
- [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]] — imports `answer_completion`; calls `answer_completion`
- [[Reference/Modules/learnloop/router_objective/cold_timing|learnloop.router_objective.cold_timing]] — imports `module`; calls `delay_receipt`, `non_service_type`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `intent_serving`; calls `intent_serving`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]], [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]], [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/data_capture_a2_measurement_helpers.py](../../../../../../tests/data_capture_a2_measurement_helpers.py) — direct import
- [tests/data_capture_codex_review_helpers.py](../../../../../../tests/data_capture_codex_review_helpers.py) — direct import
- [tests/test_data_capture_a2_measurement.py](../../../../../../tests/test_data_capture_a2_measurement.py) — direct import
  - `test_a7s_interface_takes_any_decision_with_an_experiment_id`
  - `test_a_block_of_only_measurement_checks_is_no_learner_pick_and_says_so`
  - `test_a_check_another_commitment_replaced_is_unavailable_with_why`
  - `test_a_due_check_the_plan_could_not_hold_is_unavailable_with_its_reason`
  - `test_a_read_whose_models_are_still_out_freezes_nothing_and_draws_nothing`
  - `test_a_reading_arm_gets_a_real_outcome_instead_of_not_applicable`
  - `test_a_stop_drawn_with_work_feasible_is_measured_on_what_it_gave_up`
  - `test_a_stop_with_nothing_else_feasible_keeps_its_objective_and_spends_no_question`
  - `test_a_wait_arm_gets_a_real_outcome_and_a_measurement`
  - `test_an_arrangement_that_fails_never_takes_the_decision_with_it`
  - `test_freeze_reads_the_reading_section_then_the_staged_pick_then_the_support`
  - `test_no_question_to_ask_is_recorded_unavailable_and_visible_on_the_outcome`
  - `test_one_check_per_lo_while_one_is_pending`
  - `test_plan_slots_counts_only_measurements_and_never_more_than_the_load`
  - `test_settle_is_a_no_op_with_the_switch_off`
  - `test_the_insert_arm_of_the_same_decision_has_the_same_objective_on_its_own_outcome`
  - `test_the_measurement_is_an_ordinary_check_once_with_the_teachers_rule_and_dates`
  - `test_the_objective_is_frozen_before_the_draw_the_same_for_every_arm`
  - `test_the_plan_charges_a_measurement_to_the_maintain_lane`
  - `test_the_routers_copy_of_the_actionless_arms_is_the_measurements`
  - `test_the_states_are_recorded_due_then_offered_then_answered`
- [tests/test_data_capture_codex_rereview.py](../../../../../../tests/test_data_capture_codex_rereview.py) — direct import
  - `test_f10_a_check_answered_between_settles_keeps_one_due_and_is_terminal`
  - `test_f10_a_check_answered_between_settles_reads_the_same_whatever_the_wall_clock`
  - `test_f10_a_check_satisfied_before_any_settlement_saw_it_due_gets_its_one_due_at_the_answer`
  - `test_f10_a_postponed_check_comes_due_again_as_its_own_transition`
  - `test_f10_an_offer_after_a_postponement_and_a_lost_plan_restores_it`
  - `test_f10_an_offer_today_outranks_todays_unplanned_reason`
  - `test_f10_settling_again_writes_nothing_new`
  - `test_f10_the_same_reason_after_another_offer_is_a_new_transition`
  - `test_f1_a_completed_section_is_an_exposure_with_ad_off`
  - `test_f1_a_failed_sweep_never_stops_the_states`
  - `test_f1_reading_long_before_the_answer_leaves_it_delayed`
  - `test_f1_the_check_answered_after_reading_is_not_the_measurement`
  - `test_f1_the_report_counts_the_exposures_on_record`
  - `test_f9_a_later_settlement_reads_the_pending_replacement_from_serving`
  - `test_f9_a_pending_check_due_too_soon_is_not_the_replacement`
  - `test_f9_the_one_replacement_answered_cold_measures_both`
  - `test_f9_two_decisions_on_one_warm_check_share_one_replacement`
- [tests/test_data_capture_codex_review.py](../../../../../../tests/test_data_capture_codex_review.py) — direct import
  - `test_f2_a_check_already_due_is_not_shared_with_a_decision_it_cannot_measure`
  - `test_f2_a_check_due_after_the_window_opens_is_still_shared`
  - `test_f2_a_cold_answer_is_answered_as_before`
  - `test_f2_a_warm_answer_consumes_the_check_but_keeps_the_measurement_duty`
  - `test_f2_the_date_is_never_before_the_delay_whatever_truncation_does`
  - `test_f2_the_replacement_answered_cold_completes_the_measurement`
  - `test_f7_the_report_counts_a_replaced_check_as_unavailable`
- [tests/test_data_capture_landing_review.py](../../../../../../tests/test_data_capture_landing_review.py) — direct import
  - `test_f11_a_check_wholly_on_the_objective_is_still_shared`
  - `test_f11_a_new_decision_never_shares_a_check_that_b_can_answer`
  - `test_f11_a_warm_answers_replacement_never_shares_a_check_that_b_can_answer`
  - `test_f11_an_answer_on_another_objective_never_records_answered_and_the_duty_stays`
  - `test_f1_an_answer_waits_when_the_read_cannot_judge_it`
  - `test_f1_settle_judges_the_answer_by_the_read_when_the_sweep_failed`
- [tests/test_data_capture_phone.py](../../../../../../tests/test_data_capture_phone.py) — direct import
- [tests/test_ro0_codex_verify.py](../../../../../../tests/test_ro0_codex_verify.py) — direct import
  - `test_r1_an_unserved_check_keeps_its_state_whatever_its_type_meets`
- [tests/test_ro0_row10_cold_timing.py](../../../../../../tests/test_ro0_row10_cold_timing.py) — direct import
  - `test_every_reason_the_measurement_writes_is_typed`
  - `test_no_question_to_ask_is_typed_structural`

## Modification guidance

- Make changes here when the responsibility remains measurement within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/measurement.py](../../../../../../src/learnloop/daily_plan/measurement.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

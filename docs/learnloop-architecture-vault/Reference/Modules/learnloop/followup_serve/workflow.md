---
title: "learnloop.followup_serve.workflow"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_serve/workflow.py"
source_paths:
  - "src/learnloop/followup_serve/workflow.py"
source_commit: "98ecc0dca01b7a869e5544bec341618560243ba1"
source_commit_timestamp: "2026-11-06T19:52:14-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.followup_serve"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.followup_serve.workflow module"
  - "src/learnloop/followup_serve/workflow.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-followup-serve"
---

# `learnloop.followup_serve.workflow`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_serve.workflow` exists within [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] to own the behavior summarized by its module contract: The durable workflow that owns one follow-up intervention (spec §5 item 1, §3.1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py) |
| Source lines | 521 |
| Owning package | [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `98ecc0dca01b7a869e5544bec341618560243ba1` |
| Commit timestamp | `2026-11-06T19:52:14-05:00` |

## Public API

- `workflow_id_for(attempt_id: str, revision_key: str) -> str` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 70) — Stable across retry and crash recovery: the attempt and its grade revision.
- `open_for_attempt(vault: Any, repository: Repository, *, result: Any, surface: str | None, session_id: str | None, grade: tuple[bool, str] | None, origin: str='practice', hold_feedback: bool=True, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 81) — Open (or find) the attempt's workflow on the caller's transaction, or None.
- `owns_attempt(repository: Repository, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 130) — The attempt's open workflow, or None.
- `attempt_workflow(repository: Repository, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 140)
- `workflow_of_item(repository: Repository, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 147)
- `get(repository: Repository, workflow_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 154)
- `move(repository: Repository, workflow_id: str, *, to_state: str, reason: str, from_states: tuple[str, ...]=tuple(store.OPEN_STATES), release: str | None=None, detail: Mapping[str, Any] | None=None, clock: Clock | None=None, **fields: Any) -> bool` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 165) — A move between open states; False when it lost the race.
- `finish(repository: Repository, workflow_id: str, *, to_state: str, reason: str, from_states: tuple[str, ...]=tuple(store.OPEN_STATES), release: str | None=None, detail: Mapping[str, Any] | None=None, answered_item: str | None=None, clock: Clock | None=None, **fields: Any) -> bool` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 185) — The one move to a terminal state, and the closing of what the workflow prepared, in one commit: nothing recovers a terminal workflow, so a crash between them would leave a probe live with nothing to withdraw it.
- `note(repository: Repository, workflow_id: str, *, reason: str, detail: Mapping[str, Any], clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 246) — An event on the workflow with no move: what a retry needs to read back after a crash.
- `noted(repository: Repository, workflow_id: str, *, reason: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 256) — The latest such note's detail, or nothing.
- `release_feedback(repository: Repository, workflow_id: str, *, reason: str, exposed: bool=False, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 265) — Release what is held; ``exposed`` labels a later probe's answer (§6.0).
- `set_fields(repository: Repository, workflow_id: str, *, clock: Clock | None=None, **fields: Any) -> None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 283)
- `superseded(repository: Repository, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 288) — A newer grade revision came after this workflow: it adds nothing.
- `probe_answer_exposed(repository: Repository, presentation_id: str, *, answered_at: str | None=None) -> str | None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 328) — Why a generated probe's answer is not independent, or None.
- `session_rows(repository: Repository, session_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 351) — Workflows with something to place: ready, or waiting for a boundary.
- `desktop_waiting_count(repository: Repository) -> int` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 361) — Generated probes the desktop will serve: what a phone says is waiting there (§10).
- `waiting_still_valid(repository: Repository, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 370) — §5 item 3, before serving: the factor is still open and the pin's hypotheses current.
- `close_probe(repository: Repository, row: Mapping[str, Any], *, reason: str, answered_item: str | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 391) — What a workflow prepared and nobody will answer is closed: its probe and anything an interrupted run left unbound are withdrawn, and an episode it pinned one on doesn't stay open on the topic if it measured nothing.
- `retire_waiting(repository: Repository, row: Mapping[str, Any], *, reason: str, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 441) — A wait that can't be served now: its probe retires, unused, and nothing else follows.
- `probe_answered(repository: Repository, practice_item_id: str, *, attempt_id: str, clock: Clock | None=None, link_exposures: bool=False) -> bool` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 448) — The probe's answer settles the workflow, and §6.0's hold ends, by the item whichever way it was answered: a contract that could not stand (no grading route at the serve) must not strand what was held.
- `settle_open_when_off(vault: Any, repository: Repository, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 483) — §10: with the switch off, open workflows settle as skipped and burns persist.
- `diagnosis_ended(vault: Any, repository: Repository, *, attempt_id: str, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 502) — The diagnosis worker's one hook: the workflow's job runs on its own slot, so a later diagnosis is never delayed by generation.

### Module constants

- `WORKFLOW_OWNS_REASON` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 38)
- `PENDING` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 40)
- `READY` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 41)
- `WAITING` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 42)
- `REFUSED` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 43)
- `FAILED` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 44)
- `SKIPPED` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 45)
- `SETTLED` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 46)
- `OPEN_STATES` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 47)
- `LANE_PROBE` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 49)
- `LANE_PRACTICE` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 50)
- `RELEASE_PROBE_ANSWERED` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 53)
- `RELEASE_NO_INTERVENTION` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 54)
- `RELEASE_PRACTICE_LANE` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 55)
- `RELEASE_CONTINUE_WITHOUT` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 56)
- `RELEASE_GENERATION_FAILED` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 57)
- `RELEASE_WAIT` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 58)
- `RELEASE_SHOW_ANYWAY` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 59)
- `RELEASE_REFUSED` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 60)
- `RELEASE_FALLBACK` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 61)
- `RELEASE_SWITCH_OFF` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 62)
- `CAUSES_SHOWN_BEFORE_PROBE` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 64)
- `CAUSE_EXPOSURES_UNREADABLE` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 65)
- `FACTOR_DECLINED` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 67)

### Explicit exports

`__all__` declares:

- `CAUSES_SHOWN_BEFORE_PROBE`
- `CAUSE_EXPOSURES_UNREADABLE`
- `FAILED`
- `OPEN_STATES`
- `PENDING`
- `READY`
- `REFUSED`
- `SETTLED`
- `SKIPPED`
- `WAITING`
- `WORKFLOW_OWNS_REASON`
- `attempt_workflow`
- `close_probe`
- `desktop_waiting_count`
- `diagnosis_ended`
- `finish`
- `get`
- `move`
- `open_for_attempt`
- `probe_answer_exposed`
- `probe_answered`
- `release_feedback`
- `retire_waiting`
- `session_rows`
- `waiting_still_valid`
- `owns_attempt`
- `settle_open_when_off`
- `superseded`
- `workflow_id_for`
- `workflow_of_item`

## Internal implementation anchors

- `_now(clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 77)
- `_release_fields(row: Mapping[str, Any], reason: str, at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 159)
- `_apply_move(repository: Repository, workflow_id: str, *, to_state: str, reason: str, from_states: tuple[str, ...], release: str | None, detail: Mapping[str, Any] | None, clock: Clock | None, **fields: Any) -> bool` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 217) — One state move, with its release of held feedback; False when it lost the race.
- `_instant(value: Any) -> Any` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 297)
- `_causes_shown_before(repository: Repository, row: Mapping[str, Any], answered_at: str | None) -> str | None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 304) — A recorded display of the workflow's causes before the answer, from any surface, held or not (R1).
- `_close_declined_factor(repository: Repository, row: Mapping[str, Any], *, reason: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 415) — R9: the factor this lane opened for its question goes when the question won't be asked: left open, it would hold the topic in the plan's repair lane with no repair to serve.
- `_abandon_if_empty(repository: Repository, episode_id: str, *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 428) — An open episode with no observation, and no presentation left that could make one.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `WORKFLOW_OWNS_REASON`, `open_for_attempt`, `probe_answered`; statically calls `open_for_attempt`, `probe_answered`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `move`, `retire_waiting`, `session_rows`, `waiting_still_valid`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `probe_answer_exposed`; statically calls `probe_answer_exposed`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `diagnosis_ended`; statically calls `diagnosis_ended`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `module`; statically calls `close_probe`, `finish`, `get`, `move`, `note`, `noted`, `release_feedback`, `set_fields`, `superseded`
- [[Reference/Modules/learnloop/followup_run/lanes|learnloop.followup_run.lanes]] — imports `module`; statically calls `finish`
- [[Reference/Modules/learnloop/followup_run/marks|learnloop.followup_run.marks]] — imports `module`; statically calls `attempt_workflow`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `module`; statically calls `set_fields`
- [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]] — imports `module`; statically calls `attempt_workflow`, `finish`, `get`, `retire_waiting`, `set_fields`, `waiting_still_valid`, `workflow_of_item`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `settle_open_when_off`; statically calls `settle_open_when_off`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnosis_card|learnloop_sidecar.handlers.diagnosis_card]] — imports `attempt_workflow`; statically calls `attempt_workflow`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `attempt_workflow`, `set_fields`; statically calls `attempt_workflow`, `set_fields`
- [[Reference/Modules/learnloop_sidecar/handlers/followup|learnloop_sidecar.handlers.followup]] — imports `attempt_workflow`; statically calls `attempt_workflow`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `workflow_of_item`; statically calls `workflow_of_item`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `desktop_waiting_count`, `module`; statically calls `desktop_waiting_count`, `session_rows`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `module`; statically calls `retire_waiting`, `waiting_still_valid`, `workflow_of_item`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/followup_serve|learnloop.db.stores.followup_serve]] — imports `module`; calls `append_binding`, `cancel_generation_jobs`, `episodes_pinned_by_workflow`, `insert_event`, `insert_workflow`, `move_workflow`, `open_workflows`, `present`, `update_workflow`, `workflow`, `workflow_events`, `workflow_for_attempt`, `workflow_for_item`, `workflow_for_presentation`
- [[Reference/Modules/learnloop/db/stores/hypothesis_marks|learnloop.db.stores.hypothesis_marks]] — imports `module`; calls `exposures_of_causes`, `link_probe_answer`, `present`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `RIVAL_CAUSES_FACTOR_VERSION`, `WORKFLOW_SURFACES`, `generate_and_serve_on`; calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `module`; calls `is_generated_probe`, `retire_unbound`, `withdraw`
- [[Reference/Modules/learnloop/followup_serve/queue|learnloop.followup_serve.queue]] — imports `enqueue_workflow`; calls `enqueue_workflow`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `logging`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]], [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] and 11 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f10_a_failed_workflow_withdraws_what_its_last_run_left`
  - `test_f10_an_interrupted_withdrawal_is_redone_whole`
  - `test_f2_details_leave_out_the_held_causes_until_they_are_released`
  - `test_f3_a_crash_after_the_pin_ends_the_pin_with_the_retired_item`
  - `test_f3_a_failed_file_write_serves_nothing_and_the_retry_goes_on`
  - `test_f3_the_retry_retires_the_orphan_and_serves_its_own_question`
  - `test_f4_next_doesnt_offer_a_served_probe_whose_presentation_ended`
  - `test_f5_a_check_waiting_on_the_item_doesnt_stop_the_probe_lane`
  - `test_f6_a_crash_after_the_diagnosis_ended_is_recovered_by_next`
  - `test_f6_a_crash_right_after_a_probe_answer_has_settled_its_workflow`
  - `test_f6_a_crash_right_after_completion_still_has_the_job`
  - `test_f6_a_job_that_ended_with_its_workflow_pending_says_it_failed`
  - `test_f6_startup_recovery_needs_no_click`
  - `test_f7_a_prepared_probe_closes_with_the_switch`
  - `test_f7_a_standing_plan_doesnt_strand_next_on_a_switched_off_probe`
  - `test_f7_next_through_the_sidecar_after_the_switch`
  - `test_f7_rereview_a_crash_in_cleanup_leaves_the_workflow_open_for_recovery`
  - `test_f7_rereview_a_startup_crash_doesnt_leave_a_standing_plan_holding_the_item`
  - `test_f7_rereview_continue_without_commits_its_preference_and_outcome_with_the_move`
  - `test_f7_rereview_skipping_a_workflows_probe_through_the_sidecar_closes_it`
  - `test_f7_verify_a_crash_in_the_exit_leaves_all_of_it_open_for_the_next_run`
  - `test_f7_verify_a_late_generator_closes_the_episode_it_pinned`
  - `test_f7_verify_an_answer_keeps_its_own_question_and_closes_only_the_leftovers`
  - `test_f7_verify_an_episode_another_presentation_still_holds_stays_open`
  - `test_f7_verify_every_exit_closes_what_an_interrupted_run_prepared`
  - `test_f7_verify_move_refuses_a_terminal_state_and_finish_refuses_any_other`
  - `test_f8_a_crash_after_the_decision_keeps_it_through_the_lease_recovery`
  - `test_f8_a_duplicate_receipt_resolves_to_the_decision_logged`
  - `test_f8_a_no_plan_decision_is_kept_too`
  - `test_f8_a_transport_failure_retries_under_the_decision_it_drew`
  - `test_f8_naming_the_decision_commits_with_it`
  - `test_f9_a_no_plan_retry_is_refused_too`
  - `test_f9_a_refusal_that_arrives_during_authoring_stops_the_offer`
  - `test_f9_a_refused_retry_doesnt_leave_what_the_crash_pinned`
  - `test_f9_a_retry_rechecks_the_hard_refusals_and_keeps_the_draw`
  - `test_f9_verify_a_check_on_another_object_or_of_a_non_blocking_kind_refuses_nothing`
  - `test_f9_verify_a_check_on_the_object_that_arrives_during_authoring_stops_the_offer`
  - `test_f9_verify_a_retry_is_refused_by_a_check_on_the_whole_learning_object`
- [tests/test_followup_fg1c_codex_review.py](../../../../../../tests/test_followup_fg1c_codex_review.py) — direct import
- [tests/test_followup_fg1c_r1_exposure_independence.py](../../../../../../tests/test_followup_fg1c_r1_exposure_independence.py) — direct import
  - `test_a_door_on_a_held_screen_keeps_the_causes_held`
  - `test_a_time_that_cant_be_placed_counts_as_before`
  - `test_an_exposure_after_the_answer_leaves_it_independent`
  - `test_an_exposure_on_another_attempts_factor_leaves_it_independent`
  - `test_an_exposure_recorded_before_marks_went_off_still_counts`
  - `test_an_exposure_while_held_is_recorded_and_counts`
  - `test_an_unreadable_table_doesnt_cost_the_answer`
  - `test_an_unreadable_table_is_not_independent_and_raises_nothing`
  - `test_codexs_reproduction_an_exam_origin_exposure_at_noon_and_an_answer_at_two`
  - `test_fg1s_two_labels_still_come_first`
  - `test_the_inspector_on_a_held_attempt_is_a_recorded_exposure`
  - `test_the_panel_on_the_answers_own_feedback_doesnt_relabel_the_answer`
  - `test_the_same_door_with_nothing_held_returns_the_whole_bundle`
  - `test_the_workflows_attempt_or_its_factor_is_enough`
  - `test_through_the_doors_the_answers_observation_is_not_independent_and_closes_nothing`
- [tests/test_followup_fg1d_panel_read.py](../../../../../../tests/test_followup_fg1d_panel_read.py) — direct import
  - `test_a_held_miss_still_shows_no_panel`
- [tests/test_followup_fg1d_probe_shadow.py](../../../../../../tests/test_followup_fg1d_probe_shadow.py) — direct import
  - `test_a_generated_probes_answer_on_its_presentation_reads_zero_in_the_shadow`
- [tests/test_followup_generate_e2e.py](../../../../../../tests/test_followup_generate_e2e.py) — direct import
  - `test_a_failed_lanes_need_is_deduplicated_and_cancelled_when_the_factor_closes`
  - `test_a_late_generator_adds_nothing_after_a_skip`
  - `test_a_miss_with_two_rivals_generates_one_pinned_probe`
  - `test_a_transport_failure_retries_once_and_then_fails_with_next_working`
  - `test_predictions_that_do_not_separate_the_rivals_serve_nothing`
  - `test_protected_and_reserved_items_never_reach_the_prompt`
  - `test_protection_that_cannot_be_read_sends_no_prompt`
- [tests/test_followup_journey.py](../../../../../../tests/test_followup_journey.py) — direct import
  - `test_a_generation_failure_says_so_and_next_works`
  - `test_a_lost_response_counts_as_burned_and_rebuild_keeps_the_one_submission`
  - `test_a_probe_whose_hypotheses_closed_first_is_retired_unused`
  - `test_a_reserved_probe_refuses_every_door_until_its_workflow_is_ready`
  - `test_a_routine_selection_cannot_supersede_a_workflows_pin`
  - `test_a_wait_releases_now_labels_the_probe_exposed_and_its_answer_cant_close_the_factor`
  - `test_continue_without_it_closes_the_episode_that_measured_nothing`
  - `test_continue_without_it_retires_the_probe_and_next_goes_on`
  - `test_no_intervention_generates_nothing_and_releases_what_was_held`
  - `test_opening_held_feedback_charges_nothing_until_it_is_released`
  - `test_show_anyway_doesnt_cancel_the_probe_and_its_answer_cant_close_the_factor`
  - `test_the_probes_feedback_points_back_at_what_was_held`
  - `test_the_whole_journey_and_never_again`
  - `test_with_no_plan_a_ready_probe_heads_todays_queue`
- [tests/test_followup_live_shape.py](../../../../../../tests/test_followup_live_shape.py) — direct import
  - `test_audit_an_item_with_task_features_passes_the_audit_and_reaches_ready`
  - `test_h_other_a_live_diagnosis_leaves_a_factor_without_its_arm_and_the_lane_restores_it`
- [tests/test_followup_next_matrix.py](../../../../../../tests/test_followup_next_matrix.py) — direct import
  - `test_a_queue_miss_with_a_plan_open_opens_the_probe_and_the_plan_doesnt_serve_it_again`
  - `test_a_wait_outlasting_its_plan_is_served_by_a_later_plan_with_its_answer_labelled`
  - `test_r13_next_and_placement_read_one_predicate`
  - `test_the_matrix`
- [tests/test_followup_reserved_only.py](../../../../../../tests/test_followup_reserved_only.py) — direct import
  - `test_a_cause_quoting_a_reserved_question_takes_the_practice_lane`
  - `test_a_check_waiting_holds_nothing_here`
  - `test_a_generated_question_may_share_a_topic_with_a_reserved_one`
  - `test_a_past_exam_answer_on_a_question_no_longer_reserved_can_inform_a_cause`
  - `test_a_vault_with_exam_attempts_and_incomplete_records_reaches_the_probe_lane`
  - `test_an_authored_question_echoing_a_reserved_one_is_refused_with_nothing_served`
  - `test_an_exam_sittings_miss_reaches_the_probe_lane_after_the_sitting`
  - `test_f20_a_need_job_has_the_same_limit`
  - `test_f20_what_a_crashed_run_pinned_closes_with_the_exhausted_job`
  - `test_protection_that_cant_be_read_fails_closed`
  - `test_r10_a_match_gets_one_retry_naming_only_the_authors_own_phrase`
  - `test_r10_a_second_match_takes_the_practice_lane`
  - `test_r10_the_retry_is_the_workflows_one_so_no_third_call`
  - `test_the_admission_receipt_says_what_the_causes_records_covered`
- [tests/test_followup_rival_factor.py](../../../../../../tests/test_followup_rival_factor.py) — direct import
  - `test_a_cause_matching_a_reserved_question_closes_the_factor_this_lane_opened`
  - `test_a_later_miss_on_the_topic_runs_with_this_factor_open`
  - `test_a_sweep_queues_no_mapping_this_factor_doesnt_need_and_a_retry_still_asks`
  - `test_an_answered_probe_moves_the_same_measurement_with_or_without_a_mapped_repair`
  - `test_continue_without_it_closes_it_and_a_failure_keeps_it_for_its_need`
  - `test_each_shape_opens_a_factor_serves_a_question_and_its_answer_closes_it`
  - `test_no_intervention_declines_it_and_leaves_no_open_factor_behind`
  - `test_one_concrete_cause_stays_as_it_was`
  - `test_what_the_learner_sees_when_no_repair_exists`
- [tests/test_followup_router.py](../../../../../../tests/test_followup_router.py) — direct import
  - `test_a_closed_factor_retires_a_waiting_probe_at_the_boundary`
  - `test_a_hard_refusal_needs_no_model_and_spends_nothing`
  - `test_a_wait_keeps_its_room_and_next_continues_the_block`
  - `test_no_plan_asks_now_with_no_draw`
  - `test_the_decision_row_is_itemless_and_names_the_workflow`
  - `test_the_value_checks_are_on_the_record_and_decide_nothing`
- [tests/test_followup_workflow.py](../../../../../../tests/test_followup_workflow.py) — direct import
  - `test_a_miss_at_the_tag_opens_one_workflow_and_withholds_the_predecessors_insertion`
  - `test_a_practice_lane_fallback_runs_the_predecessors_chooser_once`
  - `test_a_settled_workflow_takes_nothing_more`
  - `test_the_identity_is_stable_and_a_resumed_completion_reuses_it`
  - `test_the_switch_off_settles_open_workflows_as_skipped`
- [tests/test_hypothesis_marks.py](../../../../../../tests/test_hypothesis_marks.py) — direct import
  - `test_a_live_diagnosis_is_stored_by_its_id`
  - `test_a_practice_lane_miss_keeps_the_cards_tap`
  - `test_a_refused_link_never_blocks_the_probes_answer`
  - `test_an_exposure_records_the_order_as_displayed_not_the_servers`
  - `test_marks_are_never_forwarded_to_the_self_report_channel`
  - `test_the_blind_grader_never_sees_marks_and_the_diagnoser_does`
  - `test_the_diagnoser_reads_only_marks_made_before_the_attempt_it_is_on`
  - `test_the_switch_off_keeps_the_diagnosers_context_as_it_was_whatever_rows_exist`
  - `test_with_no_probe_the_list_is_on_the_feedback_screen`
- [tests/test_hypothesis_marks_context.py](../../../../../../tests/test_hypothesis_marks_context.py) — direct import
- [tests/test_mobile_v2_followup.py](../../../../../../tests/test_mobile_v2_followup.py) — direct import
  - `test_f3_a_phone_miss_opens_its_workflow_held_under_the_phones_surface`
  - `test_f3_a_ready_question_says_on_the_phone_that_it_waits_for_the_desktop_and_no_phone_door_opens_it`

## Modification guidance

- Make changes here when the responsibility remains workflow within learnloop.followup_serve; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

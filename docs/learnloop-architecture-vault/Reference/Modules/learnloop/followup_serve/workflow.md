---
title: "learnloop.followup_serve.workflow"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_serve/workflow.py"
source_paths:
  - "src/learnloop/followup_serve/workflow.py"
source_commit: "workspace/uncommitted @ HEAD efd894886714472c5495a6a6b87e97e8a774701a"
source_commit_timestamp: "2026-11-04T00:19:09-05:00"
source_worktree_state: "modified"
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
| Source lines | 366 |
| Owning package | [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD efd894886714472c5495a6a6b87e97e8a774701a` |
| Commit timestamp | `2026-11-04T00:19:09-05:00` |

## Public API

- `workflow_id_for(attempt_id: str, revision_key: str) -> str` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 58) — Stable across retry and crash recovery: the attempt and its grade revision.
- `open_for_attempt(vault: Any, repository: Repository, *, result: Any, surface: str | None, session_id: str | None, grade: tuple[bool, str] | None, origin: str='practice', hold_feedback: bool=True, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 69) — Open (or find) the attempt's workflow on the caller's transaction, or None.
- `owns_attempt(repository: Repository, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 118) — The attempt's open workflow, or None.
- `attempt_workflow(repository: Repository, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 128)
- `workflow_of_item(repository: Repository, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 135)
- `get(repository: Repository, workflow_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 142)
- `move(repository: Repository, workflow_id: str, *, to_state: str, reason: str, from_states: tuple[str, ...]=tuple(store.OPEN_STATES), release: str | None=None, detail: Mapping[str, Any] | None=None, clock: Clock | None=None, **fields: Any) -> bool` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 153) — One state move, with its release of held feedback; False when it lost the race.
- `release_feedback(repository: Repository, workflow_id: str, *, reason: str, exposed: bool=False, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 182) — Release what is held; ``exposed`` labels a later probe's answer (§6.0).
- `set_fields(repository: Repository, workflow_id: str, *, clock: Clock | None=None, **fields: Any) -> None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 200)
- `superseded(repository: Repository, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 205) — A newer grade revision came after this workflow: it adds nothing.
- `probe_answer_exposed(repository: Repository, presentation_id: str) -> str | None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 214) — Why a generated probe's answer is not independent, or None: FG1's two labels.
- `session_rows(repository: Repository, session_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 235) — Workflows with something to place: ready, or waiting for a boundary.
- `desktop_waiting_count(repository: Repository) -> int` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 245) — Generated probes the desktop will serve: what a phone says is waiting there (§10).
- `waiting_still_valid(repository: Repository, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 254) — §5 item 3, before serving: the factor is still open and the pin's hypotheses current.
- `close_probe(repository: Repository, row: Mapping[str, Any], *, reason: str, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 275) — A workflow's probe that will not be answered: it retires, its presentation ends, and its own episode, if it measured nothing, doesn't stay open on the topic.
- `retire_waiting(repository: Repository, row: Mapping[str, Any], *, reason: str, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 297) — A wait that can't be served now: its probe retires, unused, and nothing else follows.
- `probe_answered(repository: Repository, practice_item_id: str, *, attempt_id: str, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 305) — The probe's answer settles the workflow, and §6.0's hold ends, by the item whichever way it was answered: a contract that could not stand (no grading route at the serve) must not strand what was held.
- `settle_open_when_off(vault: Any, repository: Repository, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 328) — §10: with the switch off, open workflows settle as skipped and burns persist.
- `diagnosis_ended(vault: Any, repository: Repository, *, attempt_id: str, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 348) — The diagnosis worker's one hook: the workflow's job runs on its own slot, so a later diagnosis is never delayed by generation.

### Module constants

- `WORKFLOW_OWNS_REASON` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 32)
- `PENDING` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 34)
- `READY` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 35)
- `WAITING` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 36)
- `REFUSED` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 37)
- `FAILED` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 38)
- `SKIPPED` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 39)
- `SETTLED` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 40)
- `LANE_PROBE` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 42)
- `LANE_PRACTICE` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 43)
- `RELEASE_PROBE_ANSWERED` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 46)
- `RELEASE_NO_INTERVENTION` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 47)
- `RELEASE_PRACTICE_LANE` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 48)
- `RELEASE_CONTINUE_WITHOUT` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 49)
- `RELEASE_GENERATION_FAILED` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 50)
- `RELEASE_WAIT` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 51)
- `RELEASE_SHOW_ANYWAY` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 52)
- `RELEASE_REFUSED` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 53)
- `RELEASE_FALLBACK` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 54)
- `RELEASE_SWITCH_OFF` ([src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py), line 55)

### Explicit exports

`__all__` declares:

- `FAILED`
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

- `_now(clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 65)
- `_release_fields(row: Mapping[str, Any], reason: str, at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/followup_serve/workflow.py), line 147)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `WORKFLOW_OWNS_REASON`, `open_for_attempt`, `probe_answered`; statically calls `open_for_attempt`, `probe_answered`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `move`, `retire_waiting`, `session_rows`, `waiting_still_valid`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `probe_answer_exposed`; statically calls `probe_answer_exposed`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `diagnosis_ended`; statically calls `diagnosis_ended`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `module`; statically calls `get`, `move`, `release_feedback`, `set_fields`, `superseded`
- [[Reference/Modules/learnloop/followup_run/lanes|learnloop.followup_run.lanes]] — imports `module`; statically calls `move`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `module`; statically calls `set_fields`
- [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]] — imports `module`; statically calls `attempt_workflow`, `close_probe`, `get`, `move`, `retire_waiting`, `set_fields`, `waiting_still_valid`, `workflow_of_item`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `settle_open_when_off`; statically calls `settle_open_when_off`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnosis_card|learnloop_sidecar.handlers.diagnosis_card]] — imports `attempt_workflow`; statically calls `attempt_workflow`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `attempt_workflow`, `set_fields`; statically calls `attempt_workflow`, `set_fields`
- [[Reference/Modules/learnloop_sidecar/handlers/followup|learnloop_sidecar.handlers.followup]] — imports `attempt_workflow`; statically calls `attempt_workflow`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `workflow_of_item`; statically calls `workflow_of_item`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `desktop_waiting_count`, `module`; statically calls `desktop_waiting_count`, `session_rows`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `module`; statically calls `retire_waiting`, `waiting_still_valid`, `workflow_of_item`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/followup_serve|learnloop.db.stores.followup_serve]] — imports `module`; calls `append_binding`, `cancel_generation_jobs`, `insert_workflow`, `move_workflow`, `open_workflows`, `present`, `update_workflow`, `workflow`, `workflow_for_attempt`, `workflow_for_item`, `workflow_for_presentation`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `SERVING_SURFACE`, `generate_and_serve_on`; calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `module`; calls `is_generated_probe`, `retire`
- [[Reference/Modules/learnloop/followup_serve/queue|learnloop.followup_serve.queue]] — imports `enqueue_workflow`; calls `enqueue_workflow`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]], [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] and 10 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f2_details_leave_out_the_held_causes_until_they_are_released`
  - `test_f3_a_crash_after_the_pin_ends_the_pin_with_the_retired_item`
  - `test_f3_a_failed_file_write_serves_nothing_and_the_retry_goes_on`
  - `test_f3_the_retry_retires_the_orphan_and_serves_its_own_question`
  - `test_f4_next_doesnt_offer_a_served_probe_whose_presentation_ended`
  - `test_f5_a_cause_written_from_exam_work_reaches_neither_request`
  - `test_f5_a_check_waiting_on_the_item_doesnt_stop_the_probe_lane`
  - `test_f5_exam_attempt_work_is_exam_material_whatever_its_item`
  - `test_f5_the_author_builder_itself_refuses_them_for_entry_and_need_work`
  - `test_f5_what_the_writer_recorded_reading_counts`
  - `test_f6_a_crash_after_the_diagnosis_ended_is_recovered_by_next`
  - `test_f6_a_crash_right_after_a_probe_answer_has_settled_its_workflow`
  - `test_f6_a_crash_right_after_completion_still_has_the_job`
  - `test_f6_a_job_that_ended_with_its_workflow_pending_says_it_failed`
  - `test_f6_startup_recovery_needs_no_click`
  - `test_f7_a_prepared_probe_closes_with_the_switch`
  - `test_f7_a_standing_plan_doesnt_strand_next_on_a_switched_off_probe`
  - `test_f7_next_through_the_sidecar_after_the_switch`
  - `test_f8_a_crash_after_the_decision_keeps_it_through_the_lease_recovery`
  - `test_f8_a_duplicate_receipt_resolves_to_the_decision_logged`
  - `test_f8_a_no_plan_decision_is_kept_too`
  - `test_f8_a_transport_failure_retries_under_the_decision_it_drew`
  - `test_f8_naming_the_decision_commits_with_it`
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

## Modification guidance

- Make changes here when the responsibility remains workflow within learnloop.followup_serve; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_serve/workflow.py](../../../../../../src/learnloop/followup_serve/workflow.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

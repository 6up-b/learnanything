---
title: "learnloop.provenance"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/provenance.py"
source_paths:
  - "src/learnloop/provenance.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.provenance module"
  - "src/learnloop/provenance.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.provenance`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.provenance` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Why x and not y: the decision record, the trace id, and the one read (ADR-017).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py) |
| Source lines | 468 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `is_code(value: Any) -> bool` ([source](../../../../../src/learnloop/provenance.py), line 71) — Whether ``value`` is a string :func:`write` keeps (an id, a rule name, a version).
- `class DecisionRecord` ([source](../../../../../src/learnloop/provenance.py), line 94) — One decision at a meaningful boundary: what won, what lost and why, as of then.
  - `as_dict(self) -> dict[str, Any]` (line 120; public)
- `current_trace() -> str | None` ([source](../../../../../src/learnloop/provenance.py), line 134) — The trace this code runs under, or ``None`` outside every entry point.
- `new_record_id() -> str` ([source](../../../../../src/learnloop/provenance.py), line 145) — A new record id (a ULID), from the records' own stream; a builder that names its record's id ahead uses it.
- `new_trace_id() -> str` ([source](../../../../../src/learnloop/provenance.py), line 151)
- `trace_scope(trace_id: str | None=None) -> Iterator[str]` ([source](../../../../../src/learnloop/provenance.py), line 156) — Run the block under ``trace_id``, or under a new trace when it is ``None``.
- `current_cause() -> str | None` ([source](../../../../../src/learnloop/provenance.py), line 176) — The record that caused the work running now (a queued job's ``job_enqueued``), or ``None``.
- `continue_trace(trace_id: str | None, *, cause: str | None=None) -> str | None` ([source](../../../../../src/learnloop/provenance.py), line 182) — Continue earlier work's trace for the rest of the innermost :func:`trace_scope`; the trace now current.
- `where(exc: BaseException) -> str | None` ([source](../../../../../src/learnloop/provenance.py), line 205) — ``module:function:line`` of the frame that raised ``exc``: the record's ``error_where``.
- `cap_alternatives(alternatives: Sequence[Mapping[str, Any]], *, limit: int=MAX_ALTERNATIVES) -> tuple[list[dict[str, Any]], dict[str, int]]` ([source](../../../../../src/learnloop/provenance.py), line 222) — The first ``limit`` alternatives, and how many more lost by each rule.
- `check_no_prose(record: DecisionRecord) -> list[str]` ([source](../../../../../src/learnloop/provenance.py), line 235) — Paths of the record's values that are not an id, a number or a code constant (empty when clean).
- `write(connection: Any, record: DecisionRecord) -> str | None` ([source](../../../../../src/learnloop/provenance.py), line 289) — Insert ``record`` on the caller's connection; its id, or ``None`` when it was not written.
- `write_through(repository: Any, record: DecisionRecord) -> str | None` ([source](../../../../../src/learnloop/provenance.py), line 345) — Write ``record`` through ``repository``'s connection; its id, or ``None`` when it was not written.
- `read(connection: Any, target: str='latest', *, kind: str | None=None, limit: int=500) -> list[DecisionRecord]` ([source](../../../../../src/learnloop/provenance.py), line 383) — The records ``target`` names, oldest first; empty when none (or the vault is below migration 253).
- `read_children(connection: Any, parent_ids: Sequence[str], *, limit: int=500) -> list[DecisionRecord]` ([source](../../../../../src/learnloop/provenance.py), line 434) — The records whose ``parent_id`` is one of ``parent_ids`` (what happened next, in any trace), oldest first.
- `read_kind(connection: Any, kind: str, *, limit: int=5000) -> list[DecisionRecord]` ([source](../../../../../src/learnloop/provenance.py), line 443) — Every record of ``kind`` across traces, oldest first (``why --first-build`` walks them in order).
- `read_naming(connection: Any, ref: str, *, kind: str | None=None, limit: int=5) -> list[DecisionRecord]` ([source](../../../../../src/learnloop/provenance.py), line 449) — The newest records (of ``kind``) that name ``ref`` as what won, an alternative or a fact; newest first.

### Module constants

- `LOG` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 47)
- `TABLE` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 49)
- `STATUSES` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 52)
- `SUBJECT_KINDS` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 58)
- `MAX_ALTERNATIVES` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 63)
- `_TOKEN` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 68)
- `_COLUMNS` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 80)
- `_TRACE` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 86)
- `_SCOPE` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 88)
- `_CAUSE` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 90)
- `_RECORD_IDS` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 142)

## Internal implementation anchors

- `_completed(record: DecisionRecord) -> DecisionRecord` ([source](../../../../../src/learnloop/provenance.py), line 274)
- `_record(row: Sequence[Any]) -> DecisionRecord` ([source](../../../../../src/learnloop/provenance.py), line 370)
- `_select(connection: Any, where: str, args: Sequence[Any], *, limit: int) -> list[DecisionRecord]` ([source](../../../../../src/learnloop/provenance.py), line 422)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `current_trace`; statically calls `current_trace`
- [[Reference/Modules/learnloop/attempts/grade_records|learnloop.attempts.grade_records]] — imports `module`; statically calls `DecisionRecord`, `current_cause`, `current_trace`, `is_code`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `module`; statically calls `get`, `trace_scope`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `module`; statically calls `DecisionRecord`, `current_trace`, `is_code`, `trace_scope`
- [[Reference/Modules/learnloop/daily_plan/boundary_records|learnloop.daily_plan.boundary_records]] — imports `DecisionRecord`, `module`; statically calls `DecisionRecord`, `current_trace`, `is_code`, `new_record_id`, `new_trace_id`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `current_trace`, `read`, `where`, `write`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `module`; statically calls `current_trace`, `read`, `write`
- [[Reference/Modules/learnloop/daily_plan/plan_records|learnloop.daily_plan.plan_records]] — imports `DecisionRecord`, `module`; statically calls `DecisionRecord`, `is_code`, `new_record_id`, `where`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `current_trace`; statically calls `current_trace`
- [[Reference/Modules/learnloop/db/stores/provenance|learnloop.db.stores.provenance]] — imports `module`; statically calls `DecisionRecord`, `continue_trace`, `current_cause`, `current_trace`, `is_code`, `write`, `write_through`
- [[Reference/Modules/learnloop/diagnosis/chain_records|learnloop.diagnosis.chain_records]] — imports `module`; statically calls `DecisionRecord`, `current_cause`, `current_trace`, `is_code`, `where`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `current_trace`, `trace_scope`, `write`
- [[Reference/Modules/learnloop/figures/records|learnloop.figures.records]] — imports `module`; statically calls `DecisionRecord`, `check_no_prose`, `current_trace`, `new_trace_id`, `where`
- [[Reference/Modules/learnloop/refusal_records|learnloop.refusal_records]] — imports `DecisionRecord`, `module`; statically calls `DecisionRecord`, `current_cause`, `current_trace`, `is_code`, `where`, `write`, `write_through`
- [[Reference/Modules/learnloop/router/decisions|learnloop.router.decisions]] — imports `DecisionRecord`, `is_code`, `where`; statically calls `DecisionRecord`, `is_code`, `where`
- [[Reference/Modules/learnloop/scheduling/slate_record|learnloop.scheduling.slate_record]] — imports `DecisionRecord`, `current_trace`, `is_code`; statically calls `DecisionRecord`, `current_trace`, `is_code`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `module`; statically calls `DecisionRecord`, `current_trace`, `is_code`, `where`
- [[Reference/Modules/learnloop/why/reader|learnloop.why.reader]] — imports `module`; statically calls `is_code`, `read`, `read_children`, `read_kind`, `read_naming`, `where`
- [[Reference/Modules/learnloop/why/reconstructed|learnloop.why.reconstructed]] — imports `module`; statically calls `cap_alternatives`, `is_code`
- [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] — imports `module`; statically calls `current_trace`, `trace_scope`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `module`; statically calls `current_trace`, `read`
- [[Reference/Modules/learnloop_sidecar/logging|learnloop_sidecar.logging]] — imports `current_trace`; statically calls `current_trace`
- [[Reference/Modules/learnloop_sidecar/post_attempt_worker|learnloop_sidecar.post_attempt_worker]] — imports `module`; statically calls `trace_scope`
- [[Reference/Modules/learnloop_sidecar/prefetch_runtime|learnloop_sidecar.prefetch_runtime]] — imports `module`; statically calls `current_trace`, `trace_scope`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `module`; statically calls `trace_scope`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `module`; calls `UlidStream`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `dataclasses`, `datetime`, `json`, `logging`, `math`, `re`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]], [[Reference/Modules/learnloop/attempts/grade_records|learnloop.attempts.grade_records]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/daily_plan/boundary_records|learnloop.daily_plan.boundary_records]] and 20 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_contract_helpers.py](../../../../../tests/ad23_contract_helpers.py) — direct import
- [tests/hint_telemetry_helpers.py](../../../../../tests/hint_telemetry_helpers.py) — direct import
- [tests/test_arcb_close_fixes.py](../../../../../tests/test_arcb_close_fixes.py) — direct import
  - `test_a_plan_block_names_the_attempt_its_chooser_saw_not_one_committed_while_it_waited`
  - `test_a_record_under_a_pin_with_nothing_open_commits_alone`
  - `test_a_record_written_under_a_pin_never_commits_the_callers_work`
  - `test_a_refused_router_request_is_refused_at_once_while_a_reader_holds_a_snapshot`
  - `test_a_refused_router_request_still_leaves_its_record_when_nothing_holds_a_lock`
  - `test_an_async_hints_receipts_and_records_share_the_requests_trace`
  - `test_each_queued_figure_trigger_runs_under_the_trace_that_queued_it`
  - `test_the_record_stream_is_monotonic_and_apart_from_the_shared_one`
  - `test_why_lesson_finds_the_record_the_real_lesson_budget_builder_writes`
  - `test_why_shows_an_attempt_completed_after_the_last_rebuild`
- [tests/test_attempt_chain_records.py](../../../../../tests/test_attempt_chain_records.py) — direct import
  - `test_a_failed_forecast_and_a_failed_post_diagnosis_step_leave_records`
  - `test_a_grading_call_with_records_present_sees_none_of_them`
  - `test_a_held_grade_gets_a_record_when_the_hold_first_applies`
  - `test_a_job_with_no_enqueue_record_keeps_a_trace_of_its_own`
  - `test_a_live_held_attempt_writes_its_hold_record_in_the_attempt_step`
  - `test_a_record_that_cannot_be_written_changes_no_grade`
  - `test_a_rejected_probe_value_and_a_learner_lane_offer_are_recorded`
  - `test_continue_trace_switches_the_scope_in_place_and_its_exit_restores`
  - `test_forecast_failure_is_recorded_when_the_forecast_runs`
  - `test_grade_records_hold_no_prose`
  - `test_the_grades_trace_carries_through_the_diagnosis_to_the_follow_up`
  - `test_the_sidecar_records_a_rejected_probe_value`
- [tests/test_figure_decision_records.py](../../../../../tests/test_figure_decision_records.py) — direct import
  - `test_a_refused_build_leaves_a_refused_record`
- [tests/test_figure_rich_job.py](../../../../../tests/test_figure_rich_job.py) — direct import
  - `test_the_rich_job_continues_the_press_trace`
- [tests/test_figure_wait_estimate.py](../../../../../tests/test_figure_wait_estimate.py) — direct import
  - `test_at_the_tag_the_rows_say_v2_and_the_records_carry_ws_basis`
- [tests/test_forced_withdrawal_records.py](../../../../../tests/test_forced_withdrawal_records.py) — direct import
  - `test_a_withdrawal_names_the_forced_probe_its_workflow_and_the_next_decision_points_to_it`
  - `test_the_builders_keep_ids_numbers_and_codes_only`
- [tests/test_provenance.py](../../../../../tests/test_provenance.py) — direct import
  - `test_a_model_calls_receipt_carries_the_trace_it_started_under`
  - `test_a_phone_request_births_its_trace_and_hands_it_to_the_sidecar`
  - `test_a_rebuild_never_calls_the_record_and_keeps_its_rows`
  - `test_a_record_is_written_with_its_id_trace_and_time_filled_in`
  - `test_a_record_outside_every_trace_gets_a_trace_of_its_own`
  - `test_a_record_that_fails_a_check_is_dropped_with_a_warning_never_raised`
  - `test_a_trace_scope_births_nests_and_restores`
  - `test_a_write_joins_the_callers_transaction_and_its_failure_does_not_undo_the_callers_work`
  - `test_a_write_never_raises_on_a_vault_below_253_and_leaves_the_callers_transaction`
  - `test_a_write_on_a_read_only_connection_is_dropped`
  - `test_alternatives_are_capped_with_the_overflow_counted_per_rule`
  - `test_each_cli_command_runs_under_a_trace_that_ends_with_it`
  - `test_each_mcp_tool_call_runs_under_a_trace_of_its_own`
  - `test_each_post_attempt_job_gets_a_trace_of_its_own`
  - `test_each_sidecar_rpc_runs_under_a_trace_of_its_own`
  - `test_item_text_planted_from_the_head_fixture_is_refused`
  - `test_read_finds_latest_a_trace_a_record_a_subject_and_filters_by_kind`
  - `test_records_are_append_only`
  - `test_sidecar_log_events_carry_the_trace`
  - `test_the_store_write_takes_its_own_transaction_or_joins_the_repositorys`
  - `test_threads_in_a_copied_context_inherit_the_trace_and_bare_threads_do_not`
  - `test_where_names_the_raising_frame_and_never_the_message`
  - `test_why_answers_a_trace_from_its_records_and_its_calls_without_payloads`
- [tests/test_refusal_records.py](../../../../../tests/test_refusal_records.py) — direct import
  - `test_a_disabled_judgment_leaves_a_record_where_it_left_no_row`
  - `test_a_failed_call_keeps_its_class_and_frame_but_never_its_message`
  - `test_a_record_that_cannot_be_built_changes_no_judgment`
  - `test_a_refused_router_request_leaves_a_record_though_no_call_row_exists`
  - `test_a_row_the_ledger_refuses_leaves_a_record_and_the_callers_work_commits`
  - `test_an_answered_judgment_writes_no_record`
  - `test_every_record_here_passes_the_prose_check_with_item_text_planted`
  - `test_no_decider_routed_and_a_spend_cap_each_name_their_rule`
  - `test_the_figure_gate_records_its_first_refusal_once`
  - `test_the_follow_up_gates_decision_names_its_rule_arms_and_components`
- [tests/test_remaining_decision_records.py](../../../../../tests/test_remaining_decision_records.py) — direct import
  - `test_a_commission_job_that_generated_nothing_says_why`
  - `test_a_follow_up_interrupts_logger_that_raises_leaves_a_record`
  - `test_a_lesson_closed_with_budget_names_the_request_and_the_limit`
  - `test_a_plan_logger_that_raises_leaves_a_record_on_the_block_and_serves_the_same`
  - `test_a_shared_daily_caps_refusal_names_its_cap_and_leaves_a_record`
  - `test_an_fsrs_summary_with_a_non_finite_number_keeps_the_grade_record`
  - `test_every_b8_builder_passes_the_prose_check_with_learner_text_planted`
  - `test_the_daily_re_judgment_records_what_it_decided_and_nothing_for_none_or_fresh`
- [tests/test_router_failure_records.py](../../../../../tests/test_router_failure_records.py) — direct import
  - `test_a_chooser_crash_writes_a_fallback_record_with_the_error_and_each_models_answer`
  - `test_a_component_timeout_writes_a_model_answer_with_the_configured_wait`
  - `test_a_late_answer_is_listed_as_discarded`
  - `test_a_prefetch_whose_key_changed_before_the_serve_leaves_unclaimed_calls`
  - `test_a_prefetched_decision_names_the_prefetching_and_the_serving_trace`
  - `test_a_record_that_cannot_be_built_never_blocks_the_block`
  - `test_records_hold_codes_only_and_an_id_that_is_not_a_code_is_hashed`
  - `test_the_crash_is_logged_with_its_trace_and_never_its_message`
- [tests/test_slate_record.py](../../../../../tests/test_slate_record.py) — direct import
  - `test_a_persisting_build_writes_one_slate_record_with_its_exclusions`
  - `test_a_record_that_cannot_be_written_changes_nothing_served`
  - `test_the_rule_that_put_the_head_first`
- [tests/test_why_cases.py](../../../../../tests/test_why_cases.py) — direct import
  - `test_case_3_a_figure_stored_failed_has_one_author_record_per_attempt_with_typed_codes`
- [tests/test_why_reader.py](../../../../../tests/test_why_reader.py) — direct import
  - `test_a_follow_up_gate_call_that_answered_after_the_gate_is_discarded`
  - `test_case_3_aged_the_failed_figure_its_typed_codes_and_its_author_calls`
  - `test_why_resolves_goal_and_lesson_subjects`
- [tests/test_why_real_cases.py](../../../../../tests/test_why_real_cases.py) — direct import
  - `test_case_3_the_figure_stored_failed`
- [tests/why_cases_helpers.py](../../../../../tests/why_cases_helpers.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains provenance within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

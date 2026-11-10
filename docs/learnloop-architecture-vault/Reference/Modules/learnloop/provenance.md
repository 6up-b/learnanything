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
| Source lines | 373 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `is_code(value: Any) -> bool` ([source](../../../../../src/learnloop/provenance.py), line 70) — Whether ``value`` is a string :func:`write` keeps (an id, a rule name, a version).
- `class DecisionRecord` ([source](../../../../../src/learnloop/provenance.py), line 89) — One decision at a meaningful boundary: what won, what lost and why, as of then.
  - `as_dict(self) -> dict[str, Any]` (line 115; public)
- `current_trace() -> str | None` ([source](../../../../../src/learnloop/provenance.py), line 129) — The trace this code runs under, or ``None`` outside every entry point.
- `new_trace_id() -> str` ([source](../../../../../src/learnloop/provenance.py), line 135)
- `trace_scope(trace_id: str | None=None) -> Iterator[str]` ([source](../../../../../src/learnloop/provenance.py), line 140) — Run the block under ``trace_id``, or under a new trace when it is ``None``.
- `where(exc: BaseException) -> str | None` ([source](../../../../../src/learnloop/provenance.py), line 159) — ``module:function:line`` of the frame that raised ``exc``: the record's ``error_where``.
- `cap_alternatives(alternatives: Sequence[Mapping[str, Any]], *, limit: int=MAX_ALTERNATIVES) -> tuple[list[dict[str, Any]], dict[str, int]]` ([source](../../../../../src/learnloop/provenance.py), line 176) — The first ``limit`` alternatives, and how many more lost by each rule.
- `check_no_prose(record: DecisionRecord) -> list[str]` ([source](../../../../../src/learnloop/provenance.py), line 189) — Paths of the record's values that are not an id, a number or a code constant (empty when clean).
- `write(connection: Any, record: DecisionRecord) -> str | None` ([source](../../../../../src/learnloop/provenance.py), line 243) — Insert ``record`` on the caller's connection; its id, or ``None`` when it was not written.
- `read(connection: Any, target: str='latest', *, kind: str | None=None, limit: int=500) -> list[DecisionRecord]` ([source](../../../../../src/learnloop/provenance.py), line 315) — The records ``target`` names, oldest first; empty when none (or the vault is below migration 253).
- `read_naming(connection: Any, ref: str, *, kind: str | None=None, limit: int=5) -> list[DecisionRecord]` ([source](../../../../../src/learnloop/provenance.py), line 354) — The newest records (of ``kind``) that name ``ref`` as what won, an alternative or a fact; newest first.

### Module constants

- `LOG` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 47)
- `TABLE` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 49)
- `STATUSES` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 52)
- `SUBJECT_KINDS` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 58)
- `MAX_ALTERNATIVES` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 62)
- `_TOKEN` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 67)
- `_COLUMNS` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 79)
- `_TRACE` ([src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py), line 85)

## Internal implementation anchors

- `_completed(record: DecisionRecord) -> DecisionRecord` ([source](../../../../../src/learnloop/provenance.py), line 228)
- `_record(row: Sequence[Any]) -> DecisionRecord` ([source](../../../../../src/learnloop/provenance.py), line 302)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `current_trace`; statically calls `current_trace`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `module`; statically calls `get`, `read`, `read_naming`, `trace_scope`
- [[Reference/Modules/learnloop/daily_plan/boundary_records|learnloop.daily_plan.boundary_records]] — imports `DecisionRecord`, `module`; statically calls `DecisionRecord`, `current_trace`, `is_code`, `new_trace_id`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `current_trace`, `where`, `write`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `current_trace`; statically calls `current_trace`
- [[Reference/Modules/learnloop/db/stores/provenance|learnloop.db.stores.provenance]] — imports `module`; statically calls `current_trace`, `write`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `current_trace`, `trace_scope`, `write`
- [[Reference/Modules/learnloop/figures/records|learnloop.figures.records]] — imports `module`; statically calls `DecisionRecord`, `check_no_prose`, `current_trace`, `new_trace_id`, `where`
- [[Reference/Modules/learnloop/refusal_records|learnloop.refusal_records]] — imports `DecisionRecord`, `module`; statically calls `DecisionRecord`, `current_trace`, `is_code`, `where`, `write`
- [[Reference/Modules/learnloop/scheduling/slate_record|learnloop.scheduling.slate_record]] — imports `DecisionRecord`, `current_trace`, `is_code`; statically calls `DecisionRecord`, `current_trace`, `is_code`
- [[Reference/Modules/learnloop_sidecar/logging|learnloop_sidecar.logging]] — imports `current_trace`; statically calls `current_trace`
- [[Reference/Modules/learnloop_sidecar/post_attempt_worker|learnloop_sidecar.post_attempt_worker]] — imports `module`; statically calls `trace_scope`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `module`; statically calls `trace_scope`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `module`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `dataclasses`, `datetime`, `json`, `logging`, `math`, `re`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/daily_plan/boundary_records|learnloop.daily_plan.boundary_records]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] and 8 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_decision_records.py](../../../../../tests/test_figure_decision_records.py) — direct import
  - `test_a_refused_build_leaves_a_refused_record`
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

## Modification guidance

- Make changes here when the responsibility remains provenance within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/provenance.py](../../../../../src/learnloop/provenance.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

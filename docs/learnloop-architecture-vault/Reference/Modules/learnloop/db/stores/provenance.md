---
title: "learnloop.db.stores.provenance"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/provenance.py"
source_paths:
  - "src/learnloop/db/stores/provenance.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.provenance module"
  - "src/learnloop/db/stores/provenance.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.provenance`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.provenance` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The decision records' store (migration 253, ADR-017): a write with its own short transaction, and a trace's calls.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/provenance.py](../../../../../../../src/learnloop/db/stores/provenance.py) |
| Source lines | 295 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `write_decision(repository: Any, record: provenance.DecisionRecord) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 33) — Write ``record`` through ``repository``; its id, or ``None`` when it was not written.
- `write_decision_without_waiting(repository: Any, record: provenance.DecisionRecord) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 43) — Write ``record`` in a short transaction on a connection of its own that never waits for a lock; its id, or ``None``.
- `prune_decision_payloads(connection: Any, *, before: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 78) — Clear ``alternatives_json`` and ``facts_json`` on records created before ``before`` (``router.payload_retention_days``, as ``db.stores.router.prune_router_payloads`` does for the router's payloads); the row, its identity and its pointers stay.
- `prune_old_decision_payloads(repository: Any, *, retention_days: int, now: datetime | None=None) -> int` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 100) — The maintenance pass: clear the payloads of records older than ``retention_days``, in one short transaction.
- `trace_model_calls(connection: Any, trace_ids: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 117) — Model calls made under any of ``trace_ids``, oldest first (empty below migration 253).
- `time_precision_ms(*values: Any) -> int | None` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 156) — The coarsest precision, in ms, among ISO times (``1000`` for whole seconds, ``1`` for ms or finer): the precision of a difference between them, e.g.
- `discarded_calls(records: Iterable[provenance.DecisionRecord], calls: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 170) — The calls each decision discarded: started before it under its own or its prefetch's trace, for its boundary key when it names one, and finished after it (``late_ms``) or not at all (``late_ms`` None).
- `unclaimed_calls(connection: Any, records: Iterable[provenance.DecisionRecord], calls: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 207) — Router calls whose boundary key no decision names: neither a shown record nor any logged router decision.
- `job_enqueued_record(*, queue: str, job_id: str, job_kind: str, rule: str | None=None, facts: Mapping[str, Any] | None=None) -> provenance.DecisionRecord` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 239) — The record of one queued job (pure).
- `record_job_enqueued(connection: Any, *, queue: str, job_id: str | None, job_kind: str, rule: str | None=None, facts: Mapping[str, Any] | None=None) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 254) — Write a queued job's record on the enqueuing connection, in its transaction; its id, or None.
- `continue_job_trace(repository: Any, job_id: str) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 272) — Continue the trace that queued ``job_id`` for the rest of the worker's scope; the trace now current.

### Module constants

- `LOG` ([src/learnloop/db/stores/provenance.py](../../../../../../../src/learnloop/db/stores/provenance.py), line 23)
- `TRACE_CALL_COLUMNS` ([src/learnloop/db/stores/provenance.py](../../../../../../../src/learnloop/db/stores/provenance.py), line 27)
- `PRUNED_ALTERNATIVES` ([src/learnloop/db/stores/provenance.py](../../../../../../../src/learnloop/db/stores/provenance.py), line 74)
- `PRUNED_FACTS` ([src/learnloop/db/stores/provenance.py](../../../../../../../src/learnloop/db/stores/provenance.py), line 75)
- `LATE_ANSWER_KINDS` ([src/learnloop/db/stores/provenance.py](../../../../../../../src/learnloop/db/stores/provenance.py), line 140)
- `_FRACTION` ([src/learnloop/db/stores/provenance.py](../../../../../../../src/learnloop/db/stores/provenance.py), line 153)
- `ROUTER_OWNER` ([src/learnloop/db/stores/provenance.py](../../../../../../../src/learnloop/db/stores/provenance.py), line 204)
- `JOB_ENQUEUED` ([src/learnloop/db/stores/provenance.py](../../../../../../../src/learnloop/db/stores/provenance.py), line 236)

## Internal implementation anchors

- `_moment(value: Any) -> datetime | None` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 143)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/grade_records|learnloop.attempts.grade_records]] — imports `module`; statically calls `write_decision`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `write_decision`; statically calls `write_decision`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `write_decision`; statically calls `write_decision`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `write_decision_without_waiting`; statically calls `write_decision_without_waiting`
- [[Reference/Modules/learnloop/db/stores/diagnoses|learnloop.db.stores.diagnoses]] — imports `module`; statically calls `record_job_enqueued`
- [[Reference/Modules/learnloop/db/stores/followup_serve|learnloop.db.stores.followup_serve]] — imports `module`; statically calls `record_job_enqueued`
- [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] — imports `module`; statically calls `record_job_enqueued`
- [[Reference/Modules/learnloop/diagnosis/chain_records|learnloop.diagnosis.chain_records]] — imports `module`; statically calls `write_decision`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `module`; statically calls `continue_job_trace`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `module`; statically calls `continue_job_trace`
- [[Reference/Modules/learnloop/figures/records|learnloop.figures.records]] — imports `write_decision`; statically calls `write_decision`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `module`; statically calls `continue_job_trace`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `prune_old_decision_payloads`; statically calls `prune_old_decision_payloads`
- [[Reference/Modules/learnloop/scheduling/slate_record|learnloop.scheduling.slate_record]] — imports `module`; statically calls `write_decision`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `write_decision`
- [[Reference/Modules/learnloop/why/reader|learnloop.why.reader]] — imports `discarded_calls`, `trace_model_calls`, `unclaimed_calls`; statically calls `discarded_calls`, `trace_model_calls`, `unclaimed_calls`
- [[Reference/Modules/learnloop/why/reconstructed|learnloop.why.reconstructed]] — imports `time_precision_ms`; statically calls `time_precision_ms`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `write_decision`; statically calls `write_decision`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `module`; calls `DecisionRecord`, `continue_trace`, `current_cause`, `current_trace`, `is_code`, `write`, `write_through`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `logging`, `re`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/grade_records|learnloop.attempts.grade_records]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]], [[Reference/Modules/learnloop/db/stores/diagnoses|learnloop.db.stores.diagnoses]] and 13 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_arcb_close_fixes.py](../../../../../../../tests/test_arcb_close_fixes.py) — direct import
  - `test_a_record_under_a_pin_with_nothing_open_commits_alone`
  - `test_a_record_written_under_a_pin_never_commits_the_callers_work`
  - `test_late_ms_names_its_precision_and_a_mix_names_where_its_chances_come_from`
- [tests/test_attempt_chain_records.py](../../../../../../../tests/test_attempt_chain_records.py) — direct import
  - `test_a_grading_call_with_records_present_sees_none_of_them`
  - `test_a_job_with_no_enqueue_record_keeps_a_trace_of_its_own`
  - `test_no_grader_context_can_read_decision_records`
  - `test_the_grades_trace_carries_through_the_diagnosis_to_the_follow_up`
- [tests/test_decision_records_retention.py](../../../../../../../tests/test_decision_records_retention.py) — direct import
  - `test_an_identity_column_is_still_refused_even_beside_a_placeholder`
  - `test_anything_but_the_placeholders_a_young_row_and_a_delete_are_still_refused`
  - `test_below_254_pruning_clears_nothing_and_never_raises`
  - `test_pruning_clears_the_payloads_of_old_rows_only_and_keeps_every_identity_column`
  - `test_startup_maintenance_runs_the_retention_pass`
- [tests/test_provenance.py](../../../../../../../tests/test_provenance.py) — direct import
  - `test_a_rebuild_never_calls_the_record_and_keeps_its_rows`
  - `test_the_store_write_takes_its_own_transaction_or_joins_the_repositorys`
- [tests/test_refusal_records.py](../../../../../../../tests/test_refusal_records.py) — direct import
- [tests/test_router_failure_records.py](../../../../../../../tests/test_router_failure_records.py) — direct import
  - `test_the_store_names_the_routers_receipt_owner`
- [tests/test_slate_record.py](../../../../../../../tests/test_slate_record.py) — direct import
  - `test_a_record_that_cannot_be_written_changes_nothing_served`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/provenance.py](../../../../../../../src/learnloop/db/stores/provenance.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

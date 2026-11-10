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
| Source lines | 134 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `write_decision(repository: Any, record: provenance.DecisionRecord) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 32) — Write ``record`` through ``repository``; its id, or ``None`` when it was not written.
- `trace_model_calls(connection: Any, trace_ids: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 44) — Model calls made under any of ``trace_ids``, oldest first (empty below migration 253).
- `discarded_calls(records: Iterable[provenance.DecisionRecord], calls: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 78) — The calls each decision discarded: started before it under its own or its prefetch's trace, for its boundary key when it names one, and finished after it (``late_ms``) or not at all (``late_ms`` None).
- `unclaimed_calls(connection: Any, records: Iterable[provenance.DecisionRecord], calls: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 112) — Router calls whose boundary key no decision names: neither a shown record nor any logged router decision.

### Module constants

- `LOG` ([src/learnloop/db/stores/provenance.py](../../../../../../../src/learnloop/db/stores/provenance.py), line 22)
- `TRACE_CALL_COLUMNS` ([src/learnloop/db/stores/provenance.py](../../../../../../../src/learnloop/db/stores/provenance.py), line 26)
- `LATE_ANSWER_KINDS` ([src/learnloop/db/stores/provenance.py](../../../../../../../src/learnloop/db/stores/provenance.py), line 65)
- `ROUTER_OWNER` ([src/learnloop/db/stores/provenance.py](../../../../../../../src/learnloop/db/stores/provenance.py), line 109)

## Internal implementation anchors

- `_moment(value: Any) -> datetime | None` ([source](../../../../../../../src/learnloop/db/stores/provenance.py), line 68)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `discarded_calls`, `trace_model_calls`, `unclaimed_calls`; statically calls `discarded_calls`, `trace_model_calls`, `unclaimed_calls`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `write_decision`; statically calls `write_decision`
- [[Reference/Modules/learnloop/figures/records|learnloop.figures.records]] — imports `write_decision`; statically calls `write_decision`
- [[Reference/Modules/learnloop/scheduling/slate_record|learnloop.scheduling.slate_record]] — imports `module`; statically calls `write_decision`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `write_decision`; statically calls `write_decision`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `module`; calls `current_trace`, `write`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `logging`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/figures/records|learnloop.figures.records]], [[Reference/Modules/learnloop/scheduling/slate_record|learnloop.scheduling.slate_record]], [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_provenance.py](../../../../../../../tests/test_provenance.py) — direct import
  - `test_a_rebuild_never_calls_the_record_and_keeps_its_rows`
  - `test_the_store_write_takes_its_own_transaction_or_joins_the_repositorys`
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

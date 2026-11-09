---
title: "learnloop.db.stores.workbench"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/workbench.py"
source_paths:
  - "src/learnloop/db/stores/workbench.py"
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
  - "learnloop.db.stores.workbench module"
  - "src/learnloop/db/stores/workbench.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.workbench`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.workbench` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Reader workbench RW2a: ``workbench_sessions`` and ``workbench_steps`` (migration 207).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/workbench.py](../../../../../../../src/learnloop/db/stores/workbench.py) |
| Source lines | 206 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `handed_submission_ids(connection: sqlite3.Connection, session_ids: Iterable[str]) -> dict[str, set[str]]` ([source](../../../../../../../src/learnloop/db/stores/workbench.py), line 49) — The answer-box draft keys handed into each of ``session_ids`` (:data:`DRAFT_HANDOFF_EVENT`); a session with none is left out.
- `session_ids_for_item(connection: sqlite3.Connection, practice_item_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/workbench.py), line 77) — Every workbench session of the item, whatever its status.
- `insert_session(connection: sqlite3.Connection, values: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/workbench.py), line 88)
- `update_session(connection: sqlite3.Connection, session_id: str, values: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/workbench.py), line 99)
- `fetch_session(connection: sqlite3.Connection, session_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/workbench.py), line 112)
- `session_by_key(connection: sqlite3.Connection, key: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/workbench.py), line 116)
- `open_session_for_item(connection: sqlite3.Connection, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/workbench.py), line 122)
- `open_session_for_selection(connection: sqlite3.Connection, *, extraction_id: str, span_ids_json: str, stem_md: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/workbench.py), line 130)
- `session_for_attempt(connection: sqlite3.Connection, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/workbench.py), line 140)
- `sessions_where(connection: sqlite3.Connection, *, column: str, value: str, statuses: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/workbench.py), line 146)
- `open_sessions(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/workbench.py), line 160) — UX Phase 3 (Today's threads): every open problem worked on a source, newest first.
- `steps_for_session(connection: sqlite3.Connection, session_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/workbench.py), line 171)
- `steps_for_sessions(connection: sqlite3.Connection, session_ids: Iterable[str]) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/db/stores/workbench.py), line 178)
- `step_by_key(connection: sqlite3.Connection, session_id: str, key: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/workbench.py), line 192)
- `insert_step(connection: sqlite3.Connection, values: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/workbench.py), line 198)

### Module constants

- `SESSIONS` ([src/learnloop/db/stores/workbench.py](../../../../../../../src/learnloop/db/stores/workbench.py), line 17)
- `STEPS` ([src/learnloop/db/stores/workbench.py](../../../../../../../src/learnloop/db/stores/workbench.py), line 18)
- `SESSION_COLUMNS` ([src/learnloop/db/stores/workbench.py](../../../../../../../src/learnloop/db/stores/workbench.py), line 20)
- `MUTABLE_SESSION_COLUMNS` ([src/learnloop/db/stores/workbench.py](../../../../../../../src/learnloop/db/stores/workbench.py), line 31)
- `STEP_COLUMNS` ([src/learnloop/db/stores/workbench.py](../../../../../../../src/learnloop/db/stores/workbench.py), line 33)
- `SUBJECT_TYPE` ([src/learnloop/db/stores/workbench.py](../../../../../../../src/learnloop/db/stores/workbench.py), line 40)
- `DRAFT_HANDOFF_EVENT` ([src/learnloop/db/stores/workbench.py](../../../../../../../src/learnloop/db/stores/workbench.py), line 46)

## Internal implementation anchors

- `_row(row: sqlite3.Row | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/workbench.py), line 84)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `module`; statically calls `fetch_session`, `handed_submission_ids`, `insert_session`, `insert_step`, `open_session_for_item`, `open_session_for_selection`, `open_sessions`, `session_by_key`, `session_for_attempt`, `session_ids_for_item`, `sessions_where`, `step_by_key`, `steps_for_session`, `steps_for_sessions`, `update_session`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `module`; statically calls `session_for_attempt`, `steps_for_session`
- [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]] — imports `module`; statically calls `steps_for_session`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `module`; statically calls `session_by_key`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `module`; statically calls `session_for_attempt`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]], [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]], [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]], [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_ca2_astra_handoff_recovery.py](../../../../../../../tests/test_reader_ca2_astra_handoff_recovery.py) — direct import
  - `test_an_unreadable_handoff_refuses_the_ask_and_makes_no_model_call`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/workbench.py](../../../../../../../src/learnloop/db/stores/workbench.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

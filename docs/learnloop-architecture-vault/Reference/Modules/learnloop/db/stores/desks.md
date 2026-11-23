---
title: "learnloop.db.stores.desks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/desks.py"
source_paths:
  - "src/learnloop/db/stores/desks.py"
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
  - "learnloop.db.stores.desks module"
  - "src/learnloop/db/stores/desks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.desks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.desks` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The only SQL writer for the workbench's desks and windows (migration 262): ``desks`` and ``desk_windows``, both WORKFLOW.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/desks.py](../../../../../../../src/learnloop/db/stores/desks.py) |
| Source lines | 89 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `desk(connection: sqlite3.Connection, desk_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/desks.py), line 22)
- `open_desks(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/desks.py), line 27) — Every desk not archived, in strip order (position, then id: equal keys never tie).
- `insert_desk(connection: sqlite3.Connection, *, desk_id: str, title: str, position: str, goal_id: str | None, companion_dock: str, now: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/desks.py), line 33)
- `update_desk(connection: sqlite3.Connection, desk_id: str, fields: Mapping[str, Any], now: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/desks.py), line 42) — Set ``fields`` on one desk and count the op in its version; returns the new version.
- `window(connection: sqlite3.Connection, window_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/desks.py), line 56)
- `open_windows(connection: sqlite3.Connection, desk_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/desks.py), line 61) — A desk's open windows in strip order (slot, then pane).
- `insert_window(connection: sqlite3.Connection, *, window_id: str, desk_id: str, slot: int, kind: str, spec: Mapping[str, Any], view: Mapping[str, Any], now: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/desks.py), line 68)
- `update_window(connection: sqlite3.Connection, window_id: str, fields: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/desks.py), line 78)

### Module constants

- `_DESK_FIELDS` ([src/learnloop/db/stores/desks.py](../../../../../../../src/learnloop/db/stores/desks.py), line 11)
- `_WINDOW_FIELDS` ([src/learnloop/db/stores/desks.py](../../../../../../../src/learnloop/db/stores/desks.py), line 13)

### Explicit exports

`__all__` declares:

- `desk`
- `insert_desk`
- `insert_window`
- `open_desks`
- `open_windows`
- `update_desk`
- `update_window`
- `window`

## Internal implementation anchors

- `_rows(connection: sqlite3.Connection, sql: str, params: Iterable[Any]=()) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/desks.py), line 16)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/companion/asks|learnloop.companion.asks]] — imports `module`; statically calls `desk`, `window`
- [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]] — imports `module`; statically calls `desk`, `insert_desk`, `insert_window`, `open_desks`, `open_windows`, `update_desk`, `update_window`, `window`
- [[Reference/Modules/learnloop_sidecar/handlers/search|learnloop_sidecar.handlers.search]] — imports `module`; statically calls `desk`

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

Static participation evidence comes from [[Reference/Modules/learnloop/companion/asks|learnloop.companion.asks]], [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]], [[Reference/Modules/learnloop_sidecar/handlers/search|learnloop_sidecar.handlers.search]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_reader_rd3a_companion_ask.py](../../../../../../../tests/test_reader_rd3a_companion_ask.py) — imports consumer [[Reference/Modules/learnloop/companion/asks|learnloop.companion.asks]]
- [tests/desk_helpers.py](../../../../../../../tests/desk_helpers.py) — imports consumer [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]]
- [tests/test_reader_rd0_protocol.py](../../../../../../../tests/test_reader_rd0_protocol.py) — imports consumer [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]]
- [tests/test_reader_rd1_model_parity.py](../../../../../../../tests/test_reader_rd1_model_parity.py) — imports consumer [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]]
- [tests/test_mobile_allowlist.py](../../../../../../../tests/test_mobile_allowlist.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/search|learnloop_sidecar.handlers.search]]
- [tests/test_reader_rd3a_search.py](../../../../../../../tests/test_reader_rd3a_search.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/search|learnloop_sidecar.handlers.search]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/desks.py](../../../../../../../src/learnloop/db/stores/desks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

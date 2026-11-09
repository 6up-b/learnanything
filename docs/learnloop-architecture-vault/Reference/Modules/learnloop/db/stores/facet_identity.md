---
title: "learnloop.db.stores.facet_identity"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/facet_identity.py"
source_paths:
  - "src/learnloop/db/stores/facet_identity.py"
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
  - "learnloop.db.stores.facet_identity module"
  - "src/learnloop/db/stores/facet_identity.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.facet_identity`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.facet_identity` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Facet-identity action rows (migrations 183, 196), Library save intents (197), and facet_merges rows.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/facet_identity.py](../../../../../../../src/learnloop/db/stores/facet_identity.py) |
| Source lines | 327 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `insert_action(connection: sqlite3.Connection, record: Mapping[str, Any], *, created_at: str) -> str` ([source](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 62)
- `action_by_id(connection: sqlite3.Connection, action_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 95)
- `list_actions(connection: sqlite3.Connection, *, run_id: str | None=None, status: str | None=None, limit: int | None=200, survivor_facet_id: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 100)
- `set_status(connection: sqlite3.Connection, action_id: str, status: str, *, applied_at: str | None=None, undone_at: str | None=None, undo_detail: Mapping[str, Any] | None=None) -> None` ([source](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 125) — Move an action along its lifecycle (applying -> applied -> undoing -> undone).
- `update_action(connection: sqlite3.Connection, action_id: str, *, status: str | None=None, judge: str | None=None, before: Mapping[str, Any] | None=None, after: Mapping[str, Any] | None=None, detail: Mapping[str, Any] | None=None, undo_detail: Mapping[str, Any] | None=None) -> None` ([source](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 151) — Rewrite a pending reword confirm as the owner confirms it (proposed -> applying, or back).
- `insert_registry_save(connection: sqlite3.Connection, *, save_id: str, created_at: str, facets: Mapping[str, Any], judgment_ids: Mapping[str, str], action_ids: Sequence[str]) -> str` ([source](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 206) — Record a Library save's write-ahead intent (``applying``).
- `registry_save_by_id(connection: sqlite3.Connection, save_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 222)
- `registry_saves(connection: sqlite3.Connection, *, status: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 227) — Library saves in ``status``, oldest first (none before migration 197).
- `settle_registry_save(connection: sqlite3.Connection, save_id: str, status: str, *, at: str, settle_detail: Mapping[str, Any] | None=None) -> None` ([source](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 240) — Move an ``applying`` save to ``applied`` or ``abandoned`` (a settled save stays as it is).
- `graded_contract_version_ids(connection: sqlite3.Connection) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 254) — Every assessment contract version a live grading row was written against.
- `settled_merge_rows(connection: sqlite3.Connection) -> list[tuple[str, str]]` ([source](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 272) — ``facet_merges`` rows, minus those of a facet-identity action still in flight.
- `delete_merge_rows(connection: sqlite3.Connection, rows: Iterable[Sequence[str]]) -> int` ([source](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 305) — Remove exactly the ``facet_merges`` rows an action inserted (its undo).

### Module constants

- `ACTION_COLUMNS` ([src/learnloop/db/stores/facet_identity.py](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 30)
- `_JSON_COLUMNS` ([src/learnloop/db/stores/facet_identity.py](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 36)
- `_SAVE_JSON_COLUMNS` ([src/learnloop/db/stores/facet_identity.py](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 187)

### Explicit exports

`__all__` declares:

- `ACTION_COLUMNS`
- `action_by_id`
- `delete_merge_rows`
- `graded_contract_version_ids`
- `insert_action`
- `list_actions`
- `set_status`
- `settled_merge_rows`
- `update_action`

## Internal implementation anchors

- `_dump(value: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 47)
- `_decode(row: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 51)
- `_decode_save(row: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/facet_identity.py), line 195)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `module`; statically calls `action_by_id`, `delete_merge_rows`, `graded_contract_version_ids`, `insert_action`, `insert_registry_save`, `list_actions`, `registry_save_by_id`, `registry_saves`, `set_status`, `settle_registry_save`, `update_action`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `settled_merge_rows`; statically calls `settled_merge_rows`
- [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]] — imports `settled_merge_rows`; statically calls `settled_merge_rows`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `settled_merge_rows`; statically calls `settled_merge_rows`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]], [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_facet_authority_rereview.py](../../../../../../../tests/test_facet_authority_rereview.py) — direct import
  - `test_a_save_intent_has_a_closed_lifecycle`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/facet_identity.py](../../../../../../../src/learnloop/db/stores/facet_identity.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

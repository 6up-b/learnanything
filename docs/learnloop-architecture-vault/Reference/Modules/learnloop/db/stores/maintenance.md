---
title: "learnloop.db.stores.maintenance"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/maintenance.py"
source_paths:
  - "src/learnloop/db/stores/maintenance.py"
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
  - "learnloop.db.stores.maintenance module"
  - "src/learnloop/db/stores/maintenance.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.maintenance`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.maintenance` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Maintenance notices and the parameter registry.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/maintenance.py](../../../../../../../src/learnloop/db/stores/maintenance.py) |
| Source lines | 328 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class MaintenanceStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/maintenance.py), line 22)
  - `upsert_parameter_registry_entry(self, *, entry: dict[str, Any], clock: Clock | None=None) -> None` (line 29; public)
  - `parameter_registry_entry(self, path: str) -> dict[str, Any] | None` (line 80; public)
  - `parameter_registry_entries(self) -> list[dict[str, Any]]` (line 87; public)
  - `insert_parameter_registry_manifest(self, *, algorithm_version: str, manifest_hash: str, entries: dict[str, Any], clock: Clock | None=None) -> str | None` (line 94; public) — Freeze one immutable manifest per algorithm version.
  - `parameter_registry_manifest(self, algorithm_version: str) -> dict[str, Any] | None` (line 125; public)
  - `insert_sensitivity_certificate(self, *, certificate: dict[str, Any], clock: Clock | None=None) -> str` (line 133; public)
  - `sensitivity_certificates_for_path(self, path: str) -> list[dict[str, Any]]` (line 159; public)
  - `record_parameter_bind_event(self, *, path: str, bound_context: dict[str, Any], observation_ref: str | None=None, clock: Clock | None=None) -> str` (line 167; public)
  - `parameter_bind_events_for_path(self, path: str) -> list[dict[str, Any]]` (line 189; public)
  - `upsert_maintenance_notice(self, *, notice_type: str, dedup_key: str, title: str, action: Mapping[str, Any], aging_policy: str, severity: str='info', subject_id: str | None=None, entity_type: str | None=None, entity_id: str | None=None, detail: Any=None, clock: Clock | None=None) -> str` (line 199; public) — Insert or refresh a notice (idempotent on ``(notice_type, dedup_key)``).
  - `maintenance_notices(self, *, subject_id: str | None=None, include_hidden: bool=False) -> list[dict[str, Any]]` (line 257; public)
  - `maintenance_notice(self, notice_id: str) -> dict[str, Any] | None` (line 275; public)
  - `set_maintenance_notice_status(self, notice_id: str, *, status: str, snoozed_until: str | None=None, bump_snooze: bool=False, clock: Clock | None=None) -> None` (line 282; public)
  - `resolve_maintenance_notice_if_detail(self, notice_id: str, *, detail_key: str, expected: Any, clock: Clock | None=None) -> bool` (line 305; public) — Resolve a live notice only while its stored ``detail[detail_key]`` is still ``expected`` (one guarded statement: a write that changed the detail since the caller read it keeps the notice).

## Internal implementation anchors

- `_decode_maintenance_notice(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/maintenance.py), line 15)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `MaintenanceStoreMixin`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_json`, `_loads`; calls `_json`, `_loads`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad1_codex_rereview_fixes_helpers.py](../../../../../../../tests/ad1_codex_rereview_fixes_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad1_reading_opportunities_helpers.py](../../../../../../../tests/ad1_reading_opportunities_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad23_fakes.py](../../../../../../../tests/ad23_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad23_fix_r8_helpers.py](../../../../../../../tests/ad23_fix_r8_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad2_serving_helpers.py](../../../../../../../tests/ad2_serving_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad_ingest_fakes.py](../../../../../../../tests/ad_ingest_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad_projection_helpers.py](../../../../../../../tests/ad_projection_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/apply_write_ahead_helpers.py](../../../../../../../tests/apply_write_ahead_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/approach_map_fakes.py](../../../../../../../tests/approach_map_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/assumed_known_helpers.py](../../../../../../../tests/assumed_known_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/canonical_facet_helpers.py](../../../../../../../tests/canonical_facet_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/maintenance.py](../../../../../../../src/learnloop/db/stores/maintenance.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

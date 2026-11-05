---
title: "learnloop.db.stores.ad_receipts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/ad_receipts.py"
source_paths:
  - "src/learnloop/db/stores/ad_receipts.py"
source_commit: "f44a2201c4ba1360ab15ba2f003266c04b175356"
source_commit_timestamp: "2026-11-04T21:18:14-05:00"
source_worktree_state: "clean"
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
  - "learnloop.db.stores.ad_receipts module"
  - "src/learnloop/db/stores/ad_receipts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.ad_receipts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.ad_receipts` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Adaptive difficulty AD1's receipts: the only SQL writer of migration 213's tables.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/ad_receipts.py](../../../../../../../src/learnloop/db/stores/ad_receipts.py) |
| Source lines | 278 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `f44a2201c4ba1360ab15ba2f003266c04b175356` |
| Commit timestamp | `2026-11-04T21:18:14-05:00` |

## Public API

- `has_table(connection: sqlite3.Connection, table: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 67)
- `insert_serve_inputs(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 76) — Append one serve-input receipt; None when its receipt key already exists.
- `serve_inputs(connection: sqlite3.Connection, *, practice_item_id: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 106) — Every serve-input receipt (decoded), oldest first; ``[]`` without the table.
- `reading_opportunity_exists(connection: sqlite3.Connection, *, opportunity_key: str | None=None, identity: tuple[str, str, str, str, str] | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 121)
- `source_recorded(connection: sqlite3.Connection, *, kind: str, subkind: str, source_table: str, source_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 135) — Whether an earlier sweep already recorded this source row (for any LO).
- `insert_reading_opportunity(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 145) — Append one opportunity; None when its key or its (kind, source, LO) exists.
- `reading_opportunities(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 166) — Every opportunity (decoded), in replay order: by source write time.
- `latest_source_written_at(connection: sqlite3.Connection) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 180)
- `insert_item_snapshot(connection: sqlite3.Connection, *, content_hash_value: str, practice_item_id: str, item_json: str, created_at: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 187) — The served revision in ``practice_item_snapshots`` (migration 164), once per hash.
- `content_hash(content: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 201)
- `insert_payload(connection: sqlite3.Connection, *, owner_key: str, forecaster: str, kind: str, content: Any, created_at: str) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 205) — Store one raw request or response (once per owner and kind).
- `insert_history_draw(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 218) — Append one ``ad_history_forecast_draws`` row (once per draw key); the caller owns the transaction.
- `prune_payloads(connection: sqlite3.Connection, *, before: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 234) — Delete payloads stored before ``before`` (``router.payload_retention_days``).
- `payloads(connection: sqlite3.Connection, owner_keys: Iterable[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 243)

### Module constants

- `SERVE_INPUTS` ([src/learnloop/db/stores/ad_receipts.py](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 28)
- `READING` ([src/learnloop/db/stores/ad_receipts.py](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 29)
- `PAYLOADS` ([src/learnloop/db/stores/ad_receipts.py](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 30)
- `HISTORY_DRAWS` ([src/learnloop/db/stores/ad_receipts.py](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 32)
- `HISTORY_DRAW_COLUMNS` ([src/learnloop/db/stores/ad_receipts.py](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 33)
- `SERVE_INPUT_COLUMNS` ([src/learnloop/db/stores/ad_receipts.py](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 39)
- `READING_COLUMNS` ([src/learnloop/db/stores/ad_receipts.py](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 47)

### Explicit exports

`__all__` declares:

- `HISTORY_DRAWS`
- `HISTORY_DRAW_COLUMNS`
- `PAYLOADS`
- `READING`
- `SERVE_INPUTS`
- `content_hash`
- `has_table`
- `insert_history_draw`
- `insert_item_snapshot`
- `insert_payload`
- `insert_reading_opportunity`
- `insert_serve_inputs`
- `latest_source_written_at`
- `payloads`
- `prune_payloads`
- `reading_opportunities`
- `reading_opportunity_exists`
- `serve_inputs`
- `source_recorded`

## Internal implementation anchors

- `_dumps(value: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 54)
- `_loads(value: Any, default: Any) -> Any` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 58)
- `_decode_serve_inputs(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/ad_receipts.py), line 97)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `module`; statically calls `insert_item_snapshot`, `insert_payload`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]] — imports `module`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `module`; statically calls `has_table`, `insert_history_draw`, `insert_payload`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `module`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `module`; statically calls `insert_payload`, `prune_payloads`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `module`; statically calls `has_table`, `insert_reading_opportunity`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; statically calls `_loads`, `has_table`
- [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] — imports `module`; statically calls `has_table`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]] — imports `module`; statically calls `has_table`, `insert_serve_inputs`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve_inputs|learnloop.adaptive_difficulty.serve_inputs]] — imports `module`; statically calls `has_table`, `insert_item_snapshot`
- [[Reference/Modules/learnloop/reading_sources|learnloop.reading_sources]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]], [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] and 6 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_contract.py](../../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_a_tutor_exchange_on_a_protected_canonical_note_enters_no_prediction`
  - `test_a_tutor_exchange_whose_recorded_context_quotes_a_protected_span_enters_no_prediction`
  - `test_with_no_protection_a_frozen_dose_on_an_absent_facet_stands`
- [tests/test_ad23_fix_r8.py](../../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_a_reading_receipt_whose_source_is_held_out_now_is_not_replayed`
  - `test_the_dose_moderator_window_closes_only_at_a_visible_graded_attempt`
- [tests/test_ad3_reading.py](../../../../../../../tests/test_ad3_reading.py) — direct import
- [tests/test_ad_guard.py](../../../../../../../tests/test_ad_guard.py) — direct import
  - `test_a_write_then_a_swallowed_denial_then_an_early_return_keeps_no_ad_rows`
- [tests/test_data_capture_codex_review.py](../../../../../../../tests/test_data_capture_codex_review.py) — direct import
- [tests/test_learner_blindness_relax.py](../../../../../../../tests/test_learner_blindness_relax.py) — direct import
  - `test_the_frozen_state_version_follows_the_switch`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/ad_receipts.py](../../../../../../../src/learnloop/db/stores/ad_receipts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

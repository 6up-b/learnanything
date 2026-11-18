---
title: "learnloop.db.stores.reading_requests"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/reading_requests.py"
source_paths:
  - "src/learnloop/db/stores/reading_requests.py"
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
  - "learnloop.db.stores.reading_requests module"
  - "src/learnloop/db/stores/reading_requests.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.reading_requests`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.reading_requests` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The Reader's newest position to keep one chapter ahead, with revisioned retries.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/reading_requests.py](../../../../../../../src/learnloop/db/stores/reading_requests.py) |
| Source lines | 206 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class ReadingRequestStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/reading_requests.py), line 29)
  - `record_reading_request(self, source_id: str, extraction_id: str, section_id: str, *, clock: Clock | None=None) -> int` (line 47; public) — Record the Reader's newest position as the book's reading request (it replaces a pending one: a new revision, no failed attempts, due at once).
  - `_record_reading_request_for_extraction(cls, connection: sqlite3.Connection, extraction_id: str, section_id: str, now: str) -> None` (line 77; internal) — The same request, recorded inside the caller's transaction for the source an extraction belongs to (nothing when it has none).
  - `pending_reading_request(self, source_id: str) -> dict[str, Any] | None` (line 98; public) — The book's reading request still to act on, or ``None``.
  - `settle_reading_request(self, source_id: str, revision: int, *, clock: Clock | None=None) -> bool` (line 108; public) — The request at ``revision`` was acted on (a build queued, or nothing to do): forget it, unless a newer one replaced it.
  - `fail_reading_request(self, source_id: str, revision: int, *, attempts: int, retry_at: str | None, clock: Clock | None=None) -> bool` (line 126; public) — Acting on the request at ``revision`` failed: count it and set when the reading sweep acts on it next (``None``: due at once).
  - `defer_reading_request(self, source_id: str, revision: int, *, retry_at: str, clock: Clock | None=None) -> bool` (line 145; public) — The request at ``revision`` waits behind its book's own work: not a failure, so its failed attempts are forgotten (the Reader stops asking again) and it is due from ``retry_at``, for the reading sweep to act on once that work ends.
  - `pending_reading_requests(self) -> list[dict[str, Any]]` (line 164; public) — Every book's pending reading request, due first (reading-hardening, part 1): the reading sweep's one query per pass.
  - `due_reading_requests(self, now: str) -> list[dict[str, Any]]` (line 181; public) — The pending requests due at ``now`` (ISO UTC): a retry time passed, or none.
  - `reading_request_unsettled(self, extraction_id: str) -> bool` (line 190; public) — Whether the book this extraction belongs to has a request whose last attempt failed: the Reader's next report asks again (F8).

## Internal implementation anchors

- `_reading_request(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/reading_requests.py), line 15) — A book's pending reading request (``source_auto_build_state``, migration 199).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ReadingRequestStoreMixin`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`

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

1. Modify [src/learnloop/db/stores/reading_requests.py](../../../../../../../src/learnloop/db/stores/reading_requests.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

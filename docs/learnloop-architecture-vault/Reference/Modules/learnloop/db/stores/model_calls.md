---
title: "learnloop.db.stores.model_calls"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/model_calls.py"
source_paths:
  - "src/learnloop/db/stores/model_calls.py"
source_commit: "workspace/uncommitted @ HEAD 79532f7149b554db05a40c2ae1dbde68d9efec5a"
source_commit_timestamp: "2026-11-09T16:01:49-05:00"
source_worktree_state: "modified"
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
  - "learnloop.db.stores.model_calls module"
  - "src/learnloop/db/stores/model_calls.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.model_calls`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.model_calls` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Short transactions for call receipts and validated ingestion checkpoints.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/model_calls.py](../../../../../../../src/learnloop/db/stores/model_calls.py) |
| Source lines | 160 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 79532f7149b554db05a40c2ae1dbde68d9efec5a` |
| Commit timestamp | `2026-11-09T16:01:49-05:00` |

## Public API

- `finish_receipt(connection: Any, event: dict[str, Any], *, owner_kind: str, owner_id: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/model_calls.py), line 20) — Finalize a started receipt on the caller's connection (the caller owns the transaction).
- `insert_checkpoint(connection: Any, cache_key: str, *, purpose: str, result: dict[str, Any], usage: dict[str, Any] | None=None) -> None` ([source](../../../../../../../src/learnloop/db/stores/model_calls.py), line 29) — Write a checkpoint once on the caller's connection (the caller owns the transaction).
- `delete_checkpoint(connection: Any, cache_key: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/model_calls.py), line 38) — Delete one checkpoint on the caller's connection (the caller owns the transaction).
- `class ModelCallStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/model_calls.py), line 44)
  - `record_model_event(self, action: str, event: dict[str, Any], *, owner_kind: str, owner_id: str) -> None` (line 45; public)
  - `model_call_roots_since(self, *, owner_kind: str, since: str) -> int` (line 78; public) — Logical model calls (root receipts) of one owner kind started at or after ``since`` -- failed and unfinished calls included, since a receipt is written before its request is sent.
  - `model_call_spend_rows(self, *, started_since: str | None=None, owner_kind: str | None=None, owner_ids: Any=None) -> list[dict[str, Any]]` (line 91; public) — Usage rows for spend accounting: every receipt (usage lands on the innermost one), optionally since an ISO time and for some owners.
  - `model_route_receipts(self) -> list[dict[str, Any]]` (line 122; public) — Root receipts, oldest first, for the doctor's route health.
  - `model_checkpoint(self, cache_key: str) -> dict[str, Any] | None` (line 140; public)
  - `save_model_checkpoint(self, cache_key: str, *, purpose: str, result: dict[str, Any], usage: dict[str, Any] | None=None) -> None` (line 145; public)
  - `discard_model_checkpoint(self, cache_key: str) -> None` (line 152; public) — Delete a checkpoint whose stored result no longer validates.

### Module constants

- `LABEL_FIELDS` ([src/learnloop/db/stores/model_calls.py](../../../../../../../src/learnloop/db/stores/model_calls.py), line 14)
- `_FINISH_FIELDS` ([src/learnloop/db/stores/model_calls.py](../../../../../../../src/learnloop/db/stores/model_calls.py), line 17)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/claims|learnloop.adaptive_difficulty.claims]] — imports `delete_checkpoint`, `insert_checkpoint`; statically calls `delete_checkpoint`, `insert_checkpoint`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ModelCallStoreMixin`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `delete_checkpoint`, `finish_receipt`, `insert_checkpoint`; statically calls `delete_checkpoint`, `finish_receipt`, `insert_checkpoint`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `allow_late_model_records`; calls `allow_late_model_records`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `ReservationReleased`, `released_reservations`; calls `ReservationReleased`, `released_reservations`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/claims|learnloop.adaptive_difficulty.claims]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_contract.py](../../../../../../../tests/test_ad23_contract.py) — direct import
- [tests/test_practice_index_dossiers.py](../../../../../../../tests/test_practice_index_dossiers.py) — direct import
  - `test_a_paid_answer_whose_checkpoint_failed_is_recovered_from_its_receipt`
  - `test_a_receipt_for_another_request_or_an_invalid_answer_is_not_recovered`
- [tests/test_practice_index_evaluation.py](../../../../../../../tests/test_practice_index_evaluation.py) — direct import
  - `test_paid_labels_and_queries_whose_checkpoint_failed_are_recovered_from_receipts`
- [tests/test_practice_index_find.py](../../../../../../../tests/test_practice_index_find.py) — direct import
  - `test_a_rerank_whose_checkpoint_failed_is_recovered_from_its_receipt`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/model_calls.py](../../../../../../../src/learnloop/db/stores/model_calls.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

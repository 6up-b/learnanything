---
title: "learnloop.db.stores.collection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/collection.py"
source_paths:
  - "src/learnloop/db/stores/collection.py"
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
  - "learnloop.db.stores.collection module"
  - "src/learnloop/db/stores/collection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.collection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.collection` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Immutable entry-point provenance for versioned local data collection.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/collection.py](../../../../../../../src/learnloop/db/stores/collection.py) |
| Source lines | 227 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class CollectionStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/collection.py), line 53)
  - `finalize_scheduler_offer(self, slate_id: str | None, candidate_ids: list[str], *, entry_surface: str='desktop_queue', router_decision: Mapping[str, Any] | None=None, decision_receipt: Callable[[Any], Any] | None=None) -> None` (line 54; public) — Publish the offer; router R1's decision row commits with it.
  - `record_false_remediation(self, *, attempt_id: str, value: bool, evidence_refs: list[dict[str, str]], author_kind: str, verifier_version: str) -> str` (line 93; public)
  - `scheduler_offer_open(self, *, scheduler_candidate_id: str, session_id: str, practice_item_id: str) -> bool` (line 110; public) — Whether an offer is still an unanswered offer of this item in this session: the check :meth:`bind_submission_offer` makes, read-only.
  - `scheduler_offer_answered(self, *, scheduler_candidate_id: str, session_id: str, practice_item_id: str) -> bool` (line 117; public) — Whether an offer is a real offer of this item in this session that an attempt has already answered (stale, not foreign): read-only.
  - `submission_offer_answered_elsewhere(self, *, submission_id: str, session_id: str, practice_item_id: str) -> str | None` (line 129; public) — The attempt that answered this submission's bound offer, when that attempt is another submission's (else None): read-only.
  - `bind_submission_offer(self, *, submission_id: str | None, session_id: str, practice_item_id: str, scheduler_candidate_id: str | None, entry_surface: str='desktop_practice', record_pick: bool=True) -> str | None` (line 157; public) — Return the scheduler offer a submission answers, binding it on first use.

### Module constants

- `_EVIDENCE_ROLES` ([src/learnloop/db/stores/collection.py](../../../../../../../src/learnloop/db/stores/collection.py), line 16)

## Internal implementation anchors

- `_single_primary_key(connection: sqlite3.Connection, table: str) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/collection.py), line 19) — The table's one primary-key column, or None for rowid or composite keys.
- `_check_evidence_reference(connection: sqlite3.Connection, reference: object) -> None` ([source](../../../../../../../src/learnloop/db/stores/collection.py), line 26)
- `_offer_open(connection, candidate_id: str, session_id: str, practice_item_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/collection.py), line 46)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `CollectionStoreMixin`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] — imports `append_router_decision`, `record_learner_pick`; calls `append_router_decision`, `record_learner_pick`
- [[Reference/Modules/learnloop/db/table_roles|learnloop.db.table_roles]] — imports `TABLE_ROLES`, `TableRole`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `COLLECTION_VERSION`, `LABEL_VERSION`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `logging`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_collection_dataset.py](../../../../../../../tests/test_collection_dataset.py) — direct import
  - `test_writers_stamp_the_current_collection_version`
- [tests/test_router_offer_log.py](../../../../../../../tests/test_router_offer_log.py) — direct import
  - `test_a_learner_pick_that_cannot_be_logged_never_fails_the_bind`
- [tests/test_table_roles.py](../../../../../../../tests/test_table_roles.py) — direct import
  - `test_the_role_consumers_treat_compat_and_workflow_alike`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/collection.py](../../../../../../../src/learnloop/db/stores/collection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.db.stores.answered_revision"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/answered_revision.py"
source_paths:
  - "src/learnloop/db/stores/answered_revision.py"
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
  - "learnloop.db.stores.answered_revision module"
  - "src/learnloop/db/stores/answered_revision.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.answered_revision`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.answered_revision` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Which revision of its item an attempt answered, from the stored facts, for every reader.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/answered_revision.py](../../../../../../../src/learnloop/db/stores/answered_revision.py) |
| Source lines | 124 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `contract_revision(connection: sqlite3.Connection, contract_version_id: Any) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/answered_revision.py), line 32) — The full revision a contract cites (from mvp-0.74), or None.
- `presentation_revision(connection: sqlite3.Connection, plan_presentation_id: Any) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/answered_revision.py), line 42) — The revision a plan presentation froze when it was served, or None.
- `selection_revision(connection: sqlite3.Connection, scheduler_candidate_id: Any, answered_at: Any) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/answered_revision.py), line 52) — The revision the scheduler's selection scored for the attempt's candidate, recorded by the answer, or None.
- `draft_revisions(connection: sqlite3.Connection, *, contract_version_id: Any=None, plan_presentation_id: Any=None, scheduler_candidate_id: Any=None, answered_at: Any=None) -> tuple[str, ...]` ([source](../../../../../../../src/learnloop/db/stores/answered_revision.py), line 64) — The revisions an answer not yet stored names, in precedence order (facts 1-3).
- `all_answered_revisions(connection: sqlite3.Connection) -> dict[str, tuple[str, ...]]` ([source](../../../../../../../src/learnloop/db/stores/answered_revision.py), line 84) — Every stored attempt's answered revisions (facts 1-4), in precedence order, one pass per fact.

### Module constants

- `GRADE_RECEIPT_KIND` ([src/learnloop/db/stores/answered_revision.py](../../../../../../../src/learnloop/db/stores/answered_revision.py), line 24)

### Explicit exports

`__all__` declares:

- `all_answered_revisions`
- `contract_revision`
- `draft_revisions`
- `presentation_revision`
- `selection_revision`

## Internal implementation anchors

- `_table(connection: sqlite3.Connection, name: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/answered_revision.py), line 27)
- `_receipt_revision(versions_json: Any, practice_item_id: Any, item_content_hash: Any) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/answered_revision.py), line 73)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `all_answered_revisions`, `draft_revisions`; statically calls `all_answered_revisions`, `draft_revisions`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/ad23_fakes.py](../../../../../../../tests/ad23_fakes.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad23_contract.py](../../../../../../../tests/test_ad23_contract.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad23_fix_r7.py](../../../../../../../tests/test_ad23_fix_r7.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad23_fix_r8.py](../../../../../../../tests/test_ad23_fix_r8.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad23_fix_r9.py](../../../../../../../tests/test_ad23_fix_r9.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad23_fix_review.py](../../../../../../../tests/test_ad23_fix_review.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad23_inversion.py](../../../../../../../tests/test_ad23_inversion.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad2_serving.py](../../../../../../../tests/test_ad2_serving.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad3_subject_view.py](../../../../../../../tests/test_ad3_subject_view.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad_epoch.py](../../../../../../../tests/test_ad_epoch.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]
- [tests/test_ad_guard.py](../../../../../../../tests/test_ad_guard.py) — imports consumer [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/answered_revision.py](../../../../../../../src/learnloop/db/stores/answered_revision.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

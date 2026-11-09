---
title: "learnloop.db.stores.families"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/families.py"
source_paths:
  - "src/learnloop/db/stores/families.py"
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
  - "learnloop.db.stores.families module"
  - "src/learnloop/db/stores/families.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.families`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.families` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Persistence for authored family revisions and append-only membership.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/families.py](../../../../../../../src/learnloop/db/stores/families.py) |
| Source lines | 127 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `restore_proposal(connection: sqlite3.Connection, *, proposal_id: str, family_id: str, state: str, plan_json: str, created_at: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/families.py), line 10) — Replace only the mutable workflow cache from an authoritative ledger plan.
- `ensure_authored_identity(connection: sqlite3.Connection, *, family_id: str, title: str, created_at: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/families.py), line 21)
- `create_proposal(connection: sqlite3.Connection, *, proposal_id: str, family_id: str, plan_json: str, created_at: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/families.py), line 30)
- `update_proposal_state(connection: sqlite3.Connection, *, proposal_id: str, state: str, plan_json: str | None=None) -> None` ([source](../../../../../../../src/learnloop/db/stores/families.py), line 36)
- `validate_authored_identity(connection: sqlite3.Connection, family_id: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/families.py), line 45)
- `record_revision(connection: sqlite3.Connection, *, family_id: str, spec_json: str, title: str, created_at: str) -> str` ([source](../../../../../../../src/learnloop/db/stores/families.py), line 59)
- `append_membership(connection: sqlite3.Connection, *, family_id: str, member: dict[str, Any], action: str, proposal_id: str, judgment_id: str, created_at: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/families.py), line 76)
- `current_memberships(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/families.py), line 103) — Latest event wins; removals do not fall back to an older addition.
- `family_judge_models(connection: sqlite3.Connection) -> dict[str, tuple[str, ...]]` ([source](../../../../../../../src/learnloop/db/stores/families.py), line 112) — Resolved producer IDs from immutable accept plans, never workflow caches.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `family_judge_models`; statically calls `family_judge_models`
- [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]] — imports `append_membership`; statically calls `append_membership`
- [[Reference/Modules/learnloop/substrate/families|learnloop.substrate.families]] — imports `append_membership`, `create_proposal`, `ensure_authored_identity`, `record_revision`, `restore_proposal`, `update_proposal_state`, `validate_authored_identity`; statically calls `append_membership`, `create_proposal`, `ensure_authored_identity`, `record_revision`, `restore_proposal`, `update_proposal_state`, `validate_authored_identity`
- [[Reference/Modules/learnloop/substrate/family_memory|learnloop.substrate.family_memory]] — imports `record_revision`; statically calls `record_revision`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `sqlite3`, `typing`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]], [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]], [[Reference/Modules/learnloop/substrate/families|learnloop.substrate.families]], [[Reference/Modules/learnloop/substrate/family_memory|learnloop.substrate.family_memory]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_activity_families.py](../../../../../../../tests/test_activity_families.py) — direct import
  - `test_apply_undo_preserves_cards_and_owner_edits`
  - `test_authored_identity_cannot_claim_legacy_family`
  - `test_auto_family_rechecks_judged_content_from_disk`
  - `test_auto_family_requires_both_independent_passes`
  - `test_interrupted_apply_can_abort_after_owner_edit`
  - `test_recovery_after_partial_vault_write`
  - `test_undo_recovery_after_membership_file_write`
  - `test_undo_uses_immutable_plan_not_workflow`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/families.py](../../../../../../../src/learnloop/db/stores/families.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

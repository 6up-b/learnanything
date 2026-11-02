---
title: "learnloop.db.stores.held_out_signals"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/held_out_signals.py"
source_paths:
  - "src/learnloop/db/stores/held_out_signals.py"
source_commit: "1ef2f14ebf6f15de8b60736f60650017d40712d3"
source_commit_timestamp: "2026-10-15T12:39:41-04:00"
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
  - "learnloop.db.stores.held_out_signals module"
  - "src/learnloop/db/stores/held_out_signals.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.held_out_signals`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.held_out_signals` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The held-out signal ledger's exam qualification (migration 204; Codex review of exam protection by extraction identity, F3).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/held_out_signals.py](../../../../../../../src/learnloop/db/stores/held_out_signals.py) |
| Source lines | 117 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1ef2f14ebf6f15de8b60736f60650017d40712d3` |
| Commit timestamp | `2026-10-15T12:39:41-04:00` |

## Public API

- `is_exam_role(role: object) -> bool` ([source](../../../../../../../src/learnloop/db/stores/held_out_signals.py), line 39)
- `exam_member_sources(members: Iterable[object]) -> set[str]` ([source](../../../../../../../src/learnloop/db/stores/held_out_signals.py), line 48) — The books a source set's members (``source_sets.yaml`` entries, as read) make exam material: an exam default role, or a scope entry overridden to an exam role (``content.sources.exam_material``'s rule 1 and rule 2, read the same way).
- `pending_unrecorded_sources(connection: sqlite3.Connection) -> set[str]` ([source](../../../../../../../src/learnloop/db/stores/held_out_signals.py), line 65) — The books with a role-unrecorded held-out signal not yet recorded as exam material (none before migration 204).
- `unqualified_signal_count(connection: sqlite3.Connection, source_ids: Iterable[str]) -> int` ([source](../../../../../../../src/learnloop/db/stores/held_out_signals.py), line 77) — How many role-unrecorded held-out signals these books have (0 before migration 204).
- `qualify_unrecorded_signals(connection: sqlite3.Connection, source_ids: Iterable[str], *, created_at: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/held_out_signals.py), line 89) — Record these books' role-unrecorded held-out signals as made as exam material (an appended copy each, idempotent), in the caller's transaction; the number of rows appended.

### Module constants

- `EXAM_ROLES` ([src/learnloop/db/stores/held_out_signals.py](../../../../../../../src/learnloop/db/stores/held_out_signals.py), line 32)
- `QUALIFIED_ROLE` ([src/learnloop/db/stores/held_out_signals.py](../../../../../../../src/learnloop/db/stores/held_out_signals.py), line 34)
- `_LEDGER` ([src/learnloop/db/stores/held_out_signals.py](../../../../../../../src/learnloop/db/stores/held_out_signals.py), line 36)

### Explicit exports

`__all__` declares:

- `EXAM_ROLES`
- `QUALIFIED_ROLE`
- `exam_member_sources`
- `is_exam_role`
- `pending_unrecorded_sources`
- `qualify_unrecorded_signals`
- `unqualified_signal_count`

## Internal implementation anchors

- `_has_ledger(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/held_out_signals.py), line 43)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `is_exam_role`, `qualify_unrecorded_signals`; statically calls `is_exam_role`, `qualify_unrecorded_signals`
- [[Reference/Modules/learnloop/migration_coordinator|learnloop.migration_coordinator]] — imports `exam_member_sources`, `pending_unrecorded_sources`, `qualify_unrecorded_signals`; statically calls `exam_member_sources`, `pending_unrecorded_sources`, `qualify_unrecorded_signals`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `exam_member_sources`, `qualify_unrecorded_signals`, `unqualified_signal_count`; statically calls `exam_member_sources`, `qualify_unrecorded_signals`, `unqualified_signal_count`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `sqlite3`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/migration_coordinator|learnloop.migration_coordinator]], [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_exam_protection_identity.py](../../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_the_ledgers_exam_roles_are_the_role_authoritys`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/held_out_signals.py](../../../../../../../src/learnloop/db/stores/held_out_signals.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

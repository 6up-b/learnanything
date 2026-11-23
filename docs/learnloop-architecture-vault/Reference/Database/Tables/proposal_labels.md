---
title: "proposal_labels"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite proposal_labels"
  - "table proposal_labels"
table_name: "proposal_labels"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "266_reader_workbench_pads.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/266_reader_workbench_pads.sql"
  - "src/learnloop/db/stores/pad_ledgers.py"
  - "src/learnloop/db/stores/pad_reads.py"
  - "src/learnloop/pads/proposals.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `proposal_labels`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives proposal label a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `label_id`, `proposal_id`, `proposal_kind`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> What the learner did with a proposal: a pad proposal's marker, or (from the menus' stage) a promoted row. label_id is client-minted, so a retried label is written once.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/266_reader_workbench_pads.sql`.
- **Schema touched by:** `266_reader_workbench_pads.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `label_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `proposal_kind` | `TEXT` | yes | — | — | Stored value |
| `proposal_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `label` | `TEXT` | yes | — | — | Stored value |
| `at` | `TEXT` | yes | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_proposal_labels_proposal` on `proposal_kind`, `proposal_id`, `at`.
- `sqlite_autoindex_proposal_labels_1` on `label_id` (unique).

Database triggers:

- `proposal_labels_no_delete` — schema-enforced lifecycle or immutability constraint.
- `proposal_labels_no_replace` — schema-enforced lifecycle or immutability constraint.
- `proposal_labels_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/pad_reads.py`

### Direct SQL writers

- `src/learnloop/db/stores/pad_ledgers.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/reader_rd4_migration_helpers.py`
- `tests/test_reader_rd4_migration.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE proposal_labels (
  label_id TEXT PRIMARY KEY,
  proposal_kind TEXT NOT NULL CHECK (proposal_kind IN ('pad_proposal', 'promoted_row')),
  proposal_id TEXT NOT NULL,
  label TEXT NOT NULL CHECK (label IN ('opened', 'not_this', 'dismiss', 'ignored')),
  at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

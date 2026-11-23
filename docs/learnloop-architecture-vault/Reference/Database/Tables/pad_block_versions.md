---
title: "pad_block_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite pad_block_versions"
  - "table pad_block_versions"
table_name: "pad_block_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "262_reader_workbench_foundations.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/262_reader_workbench_foundations.sql"
  - "src/learnloop/db/stores/pad_reads.py"
  - "src/learnloop/db/stores/pads.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `pad_block_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of pad block so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `version_id`, `block_id`, `supersedes_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Every version of every block. A block's versions form one chain: its first version supersedes nothing, each later one supersedes exactly the head before it, and no version has two children (the two unique indexes), so there is never a branching head. A removal is a tombstone version. Never updated or deleted.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/262_reader_workbench_foundations.sql`.
- **Schema touched by:** `262_reader_workbench_foundations.sql`, `264_reader_workbench_guards.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `version_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `block_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `supersedes_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/pad_block_versions\|pad_block_versions.version_id]] | Stored value |
| `pad_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/pads\|pads.pad_id]] | Stored value |
| `position_key` | `TEXT` | yes | — | — | Stored value |
| `day` | `TEXT` | no | — | — | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `body_md` | `TEXT` | yes | `''` | — | Stored value |
| `payload_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `provenance` | `TEXT` | yes | — | — | Stored value |
| `tombstone` | `INTEGER` | yes | `0` | — | Stored value |
| `client_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `pad_id` → [[Reference/Database/Tables/pads|`pads.pad_id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `supersedes_id` → [[Reference/Database/Tables/pad_block_versions|`pad_block_versions.version_id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_pad_block_versions_pad` on `pad_id`, `block_id`.
- `idx_pad_block_versions_one_root` on `block_id` (unique).
- `idx_pad_block_versions_one_child` on `supersedes_id` (unique).
- `sqlite_autoindex_pad_block_versions_1` on `version_id` (unique).

Database triggers:

- `pad_block_versions_no_delete` — schema-enforced lifecycle or immutability constraint.
- `pad_block_versions_no_replace` — schema-enforced lifecycle or immutability constraint.
- `pad_block_versions_no_update` — schema-enforced lifecycle or immutability constraint.
- `pad_block_versions_same_block` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/pad_reads.py`

### Direct SQL writers

- `src/learnloop/db/stores/pads.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/reader_rd0_migration_helpers.py`
- `tests/test_reader_rd0_guards_migration.py`
- `tests/test_reader_rd0_migration.py`
- `tests/test_reader_rd0_protocol.py`

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
CREATE TABLE pad_block_versions (
  version_id TEXT PRIMARY KEY,
  block_id TEXT NOT NULL,
  supersedes_id TEXT REFERENCES pad_block_versions(version_id),
  pad_id TEXT NOT NULL REFERENCES pads(pad_id),
  position_key TEXT NOT NULL,
  day TEXT,
  kind TEXT NOT NULL CHECK (kind IN (
    'text', 'note', 'source_quote', 'source_piece', 'tutor_quote', 'figure', 'sketch', 'cell', 'ink',
    'lifted', 'check_cell'
  )),
  body_md TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  provenance TEXT NOT NULL CHECK (provenance IN (
    'learner', 'source', 'tutor', 'learnloop', 'ink_transcription', 'learner_correction'
  )),
  tombstone INTEGER NOT NULL DEFAULT 0 CHECK (tombstone IN (0, 1)),
  client_id TEXT,
  created_at TEXT NOT NULL,
  CHECK (supersedes_id IS NULL OR supersedes_id != version_id)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

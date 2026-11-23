---
title: "pad_block_submissions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite pad_block_submissions"
  - "table pad_block_submissions"
table_name: "pad_block_submissions"
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
  - "src/learnloop/pads/submission.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `pad_block_submissions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives pad block submission a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `submission_id`, `block_id`, `version_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> 1. The five tables ------------------------------------------------------------------------------------------------ An explicit submission of one block version as an attempt or a teach-back. submission_id is client-minted, so a retried submission finds its row instead of handing the text over twice; request_hash tells a retry from the same id reused for something else. attempt_id is the attempt the entry point recorded; teach_back_id the conversation a teach-back opened (the attempt that finishes it carries the same id as its agent run).

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
| `submission_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `block_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/pad_block_versions\|pad_block_versions.version_id]] | Stored value |
| `pad_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/pads\|pads.pad_id]] | Stored value |
| `submitted_as` | `TEXT` | yes | — | — | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `session_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `teach_back_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `request_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `pad_id` → [[Reference/Database/Tables/pads|`pads.pad_id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `version_id` → [[Reference/Database/Tables/pad_block_versions|`pad_block_versions.version_id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_pad_block_submissions_block` on `block_id`, `created_at`.
- `sqlite_autoindex_pad_block_submissions_1` on `submission_id` (unique).

Database triggers:

- `pad_block_submissions_no_delete` — schema-enforced lifecycle or immutability constraint.
- `pad_block_submissions_no_replace` — schema-enforced lifecycle or immutability constraint.
- `pad_block_submissions_no_update` — schema-enforced lifecycle or immutability constraint.

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
- `tests/test_reader_rd4_submission.py`

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
CREATE TABLE pad_block_submissions (
  submission_id TEXT PRIMARY KEY,
  block_id TEXT NOT NULL,
  version_id TEXT NOT NULL REFERENCES pad_block_versions(version_id),
  pad_id TEXT NOT NULL REFERENCES pads(pad_id),
  submitted_as TEXT NOT NULL CHECK (submitted_as IN ('attempt', 'teach_back')),
  practice_item_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  attempt_id TEXT,
  teach_back_id TEXT,
  request_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK ((submitted_as = 'attempt' AND attempt_id IS NOT NULL)
         OR (submitted_as = 'teach_back' AND teach_back_id IS NOT NULL))
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

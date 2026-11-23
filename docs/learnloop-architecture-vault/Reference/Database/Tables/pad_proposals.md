---
title: "pad_proposals"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite pad_proposals"
  - "table pad_proposals"
table_name: "pad_proposals"
table_role: "receipt"
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
  - "src/learnloop/passage_union/elsewhere.py"
  - "src/learnloop_sidecar/handlers/pads.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `pad_proposals`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives pad proposal a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `proposal_id`, `block_version_id`, `block_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> A connection LearnLoop suggested for one committed block version: target_spec_json is the content reference it opens (with its target passage), reason_md the one line the marker's card shows, quote the target's words, judgment_ref the judgment it rests on, found_by the machinery that found it (spec §10.6: passage links, search, correspondents). One per block version: the marker density is at most one per block.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/266_reader_workbench_pads.sql`.
- **Schema touched by:** `266_reader_workbench_pads.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `proposal_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `block_version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/pad_block_versions\|pad_block_versions.version_id]] | Stored value |
| `block_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `pad_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/pads\|pads.pad_id]] | Stored value |
| `found_by` | `TEXT` | yes | — | — | Stored value |
| `target_spec_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `reason_md` | `TEXT` | yes | — | — | Stored value |
| `quote` | `TEXT` | yes | `''` | — | Stored value |
| `judgment_ref` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `pad_id` → [[Reference/Database/Tables/pads|`pads.pad_id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `block_version_id` → [[Reference/Database/Tables/pad_block_versions|`pad_block_versions.version_id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_pad_proposals_pad` on `pad_id`, `block_id`.
- `sqlite_autoindex_pad_proposals_2` on `block_version_id` (unique).
- `sqlite_autoindex_pad_proposals_1` on `proposal_id` (unique).

Database triggers:

- `pad_proposals_no_delete` — schema-enforced lifecycle or immutability constraint.
- `pad_proposals_no_replace` — schema-enforced lifecycle or immutability constraint.
- `pad_proposals_no_update` — schema-enforced lifecycle or immutability constraint.

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
- `tests/test_menu_elsewhere_and_proposals.py`
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
CREATE TABLE pad_proposals (
  proposal_id TEXT PRIMARY KEY,
  block_version_id TEXT NOT NULL UNIQUE REFERENCES pad_block_versions(version_id),
  block_id TEXT NOT NULL,
  pad_id TEXT NOT NULL REFERENCES pads(pad_id),
  found_by TEXT NOT NULL CHECK (found_by IN ('passage_link', 'search', 'correspondent')),
  target_spec_json TEXT NOT NULL,
  reason_md TEXT NOT NULL,
  quote TEXT NOT NULL DEFAULT '',
  judgment_ref TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

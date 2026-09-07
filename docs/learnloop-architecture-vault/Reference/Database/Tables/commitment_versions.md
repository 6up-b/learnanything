---
title: "commitment_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite commitment_versions"
  - "table commitment_versions"
schema_head: 157
table_name: "commitment_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "072_commitments.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/072_commitments.sql"
  - "src/learnloop/curriculum/commitments.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/authoring/rung_variants.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `commitment_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of commitment so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `commitment_id`, `predecessor_version_id`, `goal_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/072_commitments.sql`.
- **Schema touched by:** `072_commitments.sql`, `082_golden_path_runs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `commitment_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/commitments\|commitments.id]] | Stored value |
| `version` | `INTEGER` | yes | — | — | Stored value |
| `predecessor_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/commitment_versions\|commitment_versions.id]] | Stored value |
| `intent_text` | `TEXT` | yes | — | — | Stored value |
| `interpretation_text` | `TEXT` | no | — | — | Stored value |
| `goal_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `depth_preset` | `TEXT` | yes | — | — | Stored value |
| `depth_policy_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/depth_policy_versions\|depth_policy_versions.id]] | Stored value |
| `depth_envelope_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/depth_envelope_versions\|depth_envelope_versions.id]] | Stored value |
| `attention_bounds_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `due_hint` | `TEXT` | no | — | — | Stored value |
| `hiatus_hint` | `TEXT` | no | — | — | Stored value |
| `reason` | `TEXT` | no | — | — | Stored value |
| `provenance_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `target_set_hash` | `TEXT` | yes | — | — | Stored value |
| `version_hash` | `TEXT` | yes | — | — | Stored value |
| `change_reason` | `TEXT` | no | — | — | Stored value |
| `author` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `depth_envelope_version_id` → [[Reference/Database/Tables/depth_envelope_versions|`depth_envelope_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `depth_policy_version_id` → [[Reference/Database/Tables/depth_policy_versions|`depth_policy_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `predecessor_version_id` → [[Reference/Database/Tables/commitment_versions|`commitment_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `commitment_id` → [[Reference/Database/Tables/commitments|`commitments.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_commitment_versions_commitment` on `commitment_id`, `version`.
- `sqlite_autoindex_commitment_versions_3` on `commitment_id`, `version_hash` (unique).
- `sqlite_autoindex_commitment_versions_2` on `commitment_id`, `version` (unique).
- `sqlite_autoindex_commitment_versions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._insert_commitment_version_rows()`
- `Repository.commitment_head()`
- `Repository.commitment_versions_for()`
- `Repository.commitments_targeting()`
- `Repository.find_commitment_by_idempotency()`
- `Repository.find_commitment_candidate()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/authoring/rung_variants.py`
- `src/learnloop/curriculum/commitments.py`
- `src/learnloop/db/repositories.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_golden_path_confirm.py`
- `tests/test_commitments.py`

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
CREATE TABLE commitment_versions (
  id TEXT PRIMARY KEY,
  commitment_id TEXT NOT NULL REFERENCES commitments(id) ON DELETE CASCADE,
  version INTEGER NOT NULL CHECK (version >= 1),
  predecessor_version_id TEXT REFERENCES commitment_versions(id),
  intent_text TEXT NOT NULL,
  interpretation_text TEXT,
  goal_id TEXT,                                   -- vault-owned, bare TEXT
  depth_preset TEXT NOT NULL CHECK (depth_preset IN
    ('keep_in_touch', 'remember_key_ideas', 'work_fluently', 'master_tasks_like_these')),
  depth_policy_version_id TEXT REFERENCES depth_policy_versions(id),
  depth_envelope_version_id TEXT REFERENCES depth_envelope_versions(id),
  attention_bounds_json TEXT,
  due_hint TEXT,
  hiatus_hint TEXT,
  reason TEXT,
  provenance_json TEXT,
  target_set_hash TEXT NOT NULL,
  version_hash TEXT NOT NULL,
  change_reason TEXT,
  author TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(commitment_id, version),
  UNIQUE(commitment_id, version_hash)
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

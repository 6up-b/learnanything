---
title: "depth_policy_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite depth_policy_versions"
  - "table depth_policy_versions"
schema_head: 156
table_name: "depth_policy_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "072_commitments.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/072_commitments.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/curriculum/commitment_arcs.py"
  - "src/learnloop/curriculum/commitments.py"
  - "src/learnloop/curriculum/depth_transition.py"
  - "src/learnloop/curriculum/golden_path_confirm.py"
  - "src/learnloop/scheduling/controller_snapshot.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `depth_policy_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of depth policy so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `content_hash`, `policy`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> P1 step 1 (spec_p1_shared_substrate §3.1, §3.2): durable learner commitments, immutable commitment versions + targets, and the commitment-level depth objects (policy / envelope / milestone) that P0's goal_contracts envelope validation plugs into. Net-new; commitments are SQLite-owned so they DO carry FKs among themselves. Vault-owned ids (goal_id, target_ref) stay bare TEXT.  Migration numbering: highest applied on disk = 071 (probe robust cutover); P1 starts at 072. Never edit applied migrations 065-071.  Depth objects are declared before commitment_versions because commitment_versions FK-references them (connect() runs PRAGMA foreign_keys = ON; DDL forward refs are harmless but referenced rows must exist before any INSERT).

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/072_commitments.sql`.
- **Schema touched by:** `072_commitments.sql`, `074_activity_contract_extensions.sql`, `082_golden_path_runs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `policy` | `TEXT` | yes | — | — | Stored value |
| `body_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_depth_policy_versions_2` on `content_hash` (unique).
- `sqlite_autoindex_depth_policy_versions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.depth_policy_version()`
- `Repository.ensure_depth_policy_version()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/commitment_arcs.py`
- `src/learnloop/curriculum/commitments.py`
- `src/learnloop/curriculum/depth_transition.py`
- `src/learnloop/curriculum/golden_path_confirm.py`
- `src/learnloop/scheduling/controller_snapshot.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

No table-specific test contains the table name or a detected repository method call. The schema/role invariants are still pinned by `tests/test_migrations.py` and `tests/test_table_roles.py`.

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
CREATE TABLE depth_policy_versions (
  id TEXT PRIMARY KEY,
  policy TEXT NOT NULL CHECK (policy IN
    ('hold_at_target', 'suggest_next', 'auto_within_envelope')),
  body_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(content_hash)
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

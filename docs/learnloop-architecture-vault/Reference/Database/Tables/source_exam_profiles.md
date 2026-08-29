---
title: "source_exam_profiles"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite source_exam_profiles"
  - "table source_exam_profiles"
schema_head: 156
table_name: "source_exam_profiles"
table_role: "compat"
functionality_status: "dormant-owner-gated"
domain_family: "sources-and-ingest"
introduced_in: "041_source_unit_inventories.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/041_source_unit_inventories.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/ops/doctor.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/compat"
  - "learnloop/status/dormant-owner-gated"
  - "learnloop/domain/sources-and-ingest"
---

# `source_exam_profiles`

> [!warning] Dormant Owner Gated
> No live caller was established; telemetry and owner review gate any retirement.

## Why it exists

Retains a dormant proposed cache of aggregated exam profiles; retirement remains owner-gated. It keeps an older vault or replay contract readable while new writes use the refactored path. Rows bind `scope_id`, `scope_kind`, `profile_hash`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Deterministic exam profile aggregate (§7 exam profile; §4.2 use modes). A pure function over the exam-unit inventories in scope produces aggregate task-family/capability/representation/format counts + point/time emphasis (1k-3k tokens) that M6 synthesis consumes. Its own table because the profile is a materialized deterministic view collapsing same-syllabus-family near-duplicate papers into ONE alignment vote — it is not 1:1 with any single inventory row. `profile_hash` keys the deterministic identity of the inputs.

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Compat]].

## Persistence and lifecycle contract

- **Role:** `compat` — Frozen compatibility state retained for old vaults or an incomplete replacement seam.
- **Functionality status:** `dormant-owner-gated`.
- **Introduced by:** `migrations/041_source_unit_inventories.sql`.
- **Schema touched by:** `041_source_unit_inventories.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `scope_kind` | `TEXT` | yes | — | — | Stored value |
| `scope_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `profile_hash` | `TEXT` | yes | — | — | Stored value |
| `profile_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_source_exam_profiles_scope` on `scope_kind`, `scope_id`.
- `sqlite_autoindex_source_exam_profiles_2` on `scope_kind`, `scope_id`, `profile_hash` (unique).
- `sqlite_autoindex_source_exam_profiles_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.get_exam_profile()`
- `Repository.upsert_exam_profile()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_doctor.py`
- `tests/test_source_layer.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.
5. Compatibility retirement requires production-vault telemetry and an explicit owner decision; code detachment and schema changes are separate gates.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE source_exam_profiles (
  id TEXT PRIMARY KEY,
  scope_kind TEXT NOT NULL,               -- source_set | source_revision (app-validated)
  scope_id TEXT NOT NULL,
  profile_hash TEXT NOT NULL,
  profile_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(scope_kind, scope_id, profile_hash)
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Compat|compat policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

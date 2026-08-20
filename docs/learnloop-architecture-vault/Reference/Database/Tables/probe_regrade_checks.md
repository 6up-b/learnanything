---
title: "probe_regrade_checks"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite probe_regrade_checks"
  - "table probe_regrade_checks"
schema_head: 156
table_name: "probe_regrade_checks"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "030_probe_pilot_and_policy.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/030_probe_pilot_and_policy.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/probe_audit.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `probe_regrade_checks`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives probe regrade check a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `attempt_id`, `probe_family_template_id`, `probe_family_template_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §7.6/§13.2 (Checkpoint 4.4): regrade agreement and grading confusion per family version and grader version. One row per regrade check of a probe observation's grader output; agreement compares outcome classes, and the (original, regrade) pair is the grading confusion cell.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/030_probe_pilot_and_policy.sql`.
- **Schema touched by:** `030_probe_pilot_and_policy.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `probe_family_template_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `probe_family_template_version` | `INTEGER` | yes | — | — | Stored value |
| `grader_version` | `TEXT` | no | — | — | Stored value |
| `original_outcome` | `TEXT` | yes | — | — | Stored value |
| `regrade_outcome` | `TEXT` | yes | — | — | Stored value |
| `agreement` | `INTEGER` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_probe_regrade_checks_attempt` on `attempt_id`.
- `idx_probe_regrade_checks_family` on `probe_family_template_id`, `probe_family_template_version`.
- `sqlite_autoindex_probe_regrade_checks_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.insert_probe_regrade_check()`
- `Repository.probe_regrade_checks()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/probe_audit.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_characterization_probe_regrade.py`
- `tests/test_probe_lifecycle.py`

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
CREATE TABLE probe_regrade_checks (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  probe_family_template_id TEXT NOT NULL,
  probe_family_template_version INTEGER NOT NULL,
  grader_version TEXT,
  original_outcome TEXT NOT NULL,
  regrade_outcome TEXT NOT NULL,
  agreement INTEGER NOT NULL CHECK (agreement IN (0, 1)),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

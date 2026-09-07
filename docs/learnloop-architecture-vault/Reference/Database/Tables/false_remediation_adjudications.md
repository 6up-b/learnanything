---
title: "false_remediation_adjudications"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0395ae32f9e2e40d1cb98b38402631299a94003f"
source_commit_timestamp: "2026-09-07T12:49:13-04:00"
last_verified: "2026-09-07"
aliases:
  - "state.sqlite false_remediation_adjudications"
  - "table false_remediation_adjudications"
schema_head: 163
table_name: "false_remediation_adjudications"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "162_false_remediation_adjudications.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/162_false_remediation_adjudications.sql"
  - "src/learnloop/db/stores/collection.py"
  - "src/learnloop/substrate/data_quality.py"
  - "src/learnloop/substrate/dataset.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `false_remediation_adjudications`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records append-only human or machine false-remediation labels with retained evidence references and verifier versions; corrections append another adjudication. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `author_kind`, `verifier_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> F is an explicit evidence-backed adjudication, never inferred from a later successful answer. Corrections append a new adjudication and dataset version.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/162_false_remediation_adjudications.sql`.
- **Schema touched by:** `162_false_remediation_adjudications.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `label_value` | `INTEGER` | yes | — | — | Stored value |
| `evidence_refs_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `author_kind` | `TEXT` | yes | — | — | Stored value |
| `verifier_version` | `TEXT` | yes | — | — | Stored value |
| `label_version` | `TEXT` | yes | — | — | Stored value |
| `collection_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_false_remediation_attempt` on `attempt_id`, `created_at`, `id`.
- `sqlite_autoindex_false_remediation_adjudications_1` on `id` (unique).

Database triggers:

- `false_remediation_no_delete` — schema-enforced lifecycle or immutability constraint.
- `false_remediation_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

None found by exact static reference scan.

### Direct SQL writers

- `src/learnloop/db/stores/collection.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

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
CREATE TABLE false_remediation_adjudications (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
  label_value INTEGER NOT NULL CHECK(label_value IN (0,1)),
  evidence_refs_json TEXT NOT NULL,
  author_kind TEXT NOT NULL CHECK(author_kind IN ('human','machine')),
  verifier_version TEXT NOT NULL,
  label_version TEXT NOT NULL,
  collection_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

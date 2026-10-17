---
title: "text_write_provenance"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "c1ec76c7d4c02699f34e4baad881bef10250a9d7"
source_commit_timestamp: "2026-10-17T18:29:57-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite text_write_provenance"
  - "table text_write_provenance"
schema_head: 208
table_name: "text_write_provenance"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "205_write_provenance.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/205_write_provenance.sql"
  - "src/learnloop/db/stores/write_provenance.py"
  - "src/learnloop/learner_context.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `text_write_provenance`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives text write provenance a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `record_id`, `provenance_version`, `kind`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/205_write_provenance.sql`.
- **Schema touched by:** `205_write_provenance.sql`, `206_forecast_receipts.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `record_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `text_sha256` | `TEXT` | no | — | — | Stored value |
| `writer` | `TEXT` | yes | — | — | Stored value |
| `complete` | `INTEGER` | yes | — | — | Stored value |
| `incomplete_reasons_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `inputs_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `derived_from_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `provenance_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_text_write_provenance_record` on `kind`, `record_id`, `created_at`, `id`.
- `sqlite_autoindex_text_write_provenance_1` on `id` (unique).

Database triggers:

- `text_write_provenance_no_delete` — schema-enforced lifecycle or immutability constraint.
- `text_write_provenance_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/write_provenance.py`

### Direct SQL writers

- `src/learnloop/db/stores/write_provenance.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_chatgpt_plan_landing.py`
- `tests/test_diagnosis_input_provenance.py`
- `tests/test_diagnosis_input_provenance_landing.py`
- `tests/test_diagnostic_augmentation.py`
- `tests/test_forecast_receipts_landing.py`
- `tests/test_reader_formative_texts.py`
- `tests/test_regrade_contract_successor.py`
- `tests/test_ux_phase4_landing.py`

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
CREATE TABLE text_write_provenance (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN (
    'diagnosis', 'grading', 'hypothesis', 'candidate', 'misconception',
    'misconception_correction', 'learner_text_gap', 'learning_object',
    'practice_item'
  )),
  record_id TEXT NOT NULL,
  text_sha256 TEXT,
  writer TEXT NOT NULL,
  complete INTEGER NOT NULL CHECK (complete IN (0, 1)),
  incomplete_reasons_json TEXT NOT NULL DEFAULT '[]',
  inputs_json TEXT NOT NULL,
  derived_from_json TEXT NOT NULL DEFAULT '[]',
  provenance_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

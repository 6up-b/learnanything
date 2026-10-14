---
title: "reference_key_checks"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "e7bda6662d5d4fb000d01967059c09754168c239"
source_commit_timestamp: "2026-10-14T01:25:18-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite reference_key_checks"
  - "table reference_key_checks"
schema_head: 202
table_name: "reference_key_checks"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "188_source_exercise_imports.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/188_source_exercise_imports.sql"
  - "src/learnloop/content/authoring/source_exercise_import.py"
  - "src/learnloop/db/stores/source_service.py"
  - "src/learnloop/instructional/harvest.py"
  - "src/learnloop/ops/pf_publish.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `reference_key_checks`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Appends one row per answer-key check of an imported exercise (canonical sources S1): the rung (book solution, panel and symbolic check), the label it earned, its evidence refs and the reference_content_hash of the stem, key and rubric it verified, so an edit leaves the current content unverified. Read by the certification gate (practice_attempts.reference_status) and the key label shown to the learner. It supplies replay-stable input rather than a disposable cache. Rows bind `practice_item_id`, `import_id`, `key_status`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Captured verifier output: one append-only row per ladder run, bound to the exact content it checked (reference_content_hash over the prompt, the expected answer and the grading rubric). Never updated, never re-run on rebuild. The attempt gate and the value intents read only this table.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/188_source_exercise_imports.sql`.
- **Schema touched by:** `188_source_exercise_imports.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `import_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `key_status` | `TEXT` | yes | — | — | Stored value |
| `rung` | `TEXT` | yes | — | — | Stored value |
| `verification_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `ledger_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `trigger` | `TEXT` | yes | — | — | Stored value |
| `started_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_reference_key_checks_item` on `practice_item_id`, `created_at`.
- `sqlite_autoindex_reference_key_checks_1` on `id` (unique).

Database triggers:

- `reference_key_checks_no_delete` — schema-enforced lifecycle or immutability constraint.
- `reference_key_checks_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/content/authoring/source_exercise_import.py`
- `src/learnloop/db/stores/source_service.py`
- `src/learnloop/ops/pf_publish.py`

### Direct SQL writers

- `src/learnloop/db/stores/source_service.py`

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
CREATE TABLE reference_key_checks (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL,
  import_id TEXT,
  content_hash TEXT NOT NULL,
  key_status TEXT NOT NULL CHECK (key_status IN (
    'book_solution', 'checked', 'panel_agrees', 'panel_agrees_unconfirmed',
    'model_answer', 'disputed'
  )),
  rung TEXT NOT NULL,
  verification_json TEXT NOT NULL DEFAULT '{}',
  ledger_ids_json TEXT NOT NULL DEFAULT '[]',
  trigger TEXT NOT NULL CHECK (trigger IN ('import', 'background', 'edit', 'verify')),
  started_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

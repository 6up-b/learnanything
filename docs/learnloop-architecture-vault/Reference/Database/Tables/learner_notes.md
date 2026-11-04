---
title: "learner_notes"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0ed947a2c0b030671b4fbd264957e0ca13fa010f"
source_commit_timestamp: "2026-11-04T11:05:42-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite learner_notes"
  - "table learner_notes"
schema_head: 242
table_name: "learner_notes"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "229_learner_notes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/229_learner_notes.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/db/stores/learner_notes.py"
  - "src/learnloop/source_retrieval/note_gaps.py"
  - "src/learnloop/source_retrieval/note_links.py"
  - "src/learnloop/teacher/notes.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `learner_notes`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives learner note a stable database identity so learner-facing mastery and capability decisions use a reproducible evidence projection. It supplies replay-stable input rather than a disposable cache. Rows bind `vault_ref_id`, `vault_ref_kind`, `content_hash`, making the operational relationship explicit. ^table-purpose

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/229_learner_notes.sql`.
- **Schema touched by:** `229_learner_notes.sql`, `231_learner_note_source_kind.sql`, `233_learner_notes_vault_origin.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `note_key` | `TEXT` | yes | — | — | Stored value |
| `path` | `TEXT` | no | — | — | Stored value |
| `heading_path` | `TEXT` | yes | `''` | — | Stored value |
| `line` | `INTEGER` | no | — | — | Stored value |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `title` | `TEXT` | yes | — | — | Stored value |
| `heading` | `TEXT` | yes | `''` | — | Stored value |
| `captured_on` | `TEXT` | no | — | — | Stored value |
| `origin` | `TEXT` | yes | — | — | Stored value |
| `text_md` | `TEXT` | yes | — | — | Stored value |
| `truncated` | `INTEGER` | yes | `0` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `vault_ref_kind` | `TEXT` | no | — | — | Stored value |
| `vault_ref_id` | `TEXT` | no | — | — | Application-validated soft reference |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_learner_notes_key` on `note_key`, `created_at`.
- `sqlite_autoindex_learner_notes_2` on `note_key`, `content_hash` (unique).
- `sqlite_autoindex_learner_notes_1` on `id` (unique).

Database triggers:

- `learner_notes_no_delete` — schema-enforced lifecycle or immutability constraint.
- `learner_notes_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/learner_notes.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_architecture.py`
- `tests/test_followups_batch5_recap_dependencies.py`
- `tests/test_followups_batch7_note_titles.py`
- `tests/test_help_assist_figures_migration.py`
- `tests/test_help_assist_work_md_migration.py`
- `tests/test_learner_note_source_kind_migration.py`
- `tests/test_learner_notes_migration.py`
- `tests/test_learner_notes_vault_origin_migration.py`
- `tests/test_notes_as_learner_text.py`
- `tests/test_notes_c2b_review5.py`
- `tests/test_notes_linked.py`
- `tests/test_notes_never_read.py`

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
CREATE TABLE "learner_notes" (
  id TEXT PRIMARY KEY,
  note_key TEXT NOT NULL,
  path TEXT,
  heading_path TEXT NOT NULL DEFAULT '',
  line INTEGER CHECK (line IS NULL OR line >= 1),
  content_hash TEXT NOT NULL,
  title TEXT NOT NULL,
  heading TEXT NOT NULL DEFAULT '',
  captured_on TEXT,
  origin TEXT NOT NULL CHECK (origin IN ('tend', 'pocket_notes', 'vault')),
  text_md TEXT NOT NULL,
  truncated INTEGER NOT NULL DEFAULT 0 CHECK (truncated IN (0, 1)),
  created_at TEXT NOT NULL,
  vault_ref_kind TEXT CHECK (vault_ref_kind IS NULL OR vault_ref_kind IN ('annotation', 'capture')),
  vault_ref_id TEXT,
  CHECK (origin <> 'vault' OR (vault_ref_kind IS NOT NULL AND vault_ref_id IS NOT NULL)),
  CHECK (origin = 'vault' OR (path IS NOT NULL AND line IS NOT NULL)),
  UNIQUE (note_key, content_hash)
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

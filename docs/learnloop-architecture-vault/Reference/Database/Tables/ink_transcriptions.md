---
title: "ink_transcriptions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite ink_transcriptions"
  - "table ink_transcriptions"
table_name: "ink_transcriptions"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "267_reader_workbench_ink.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/267_reader_workbench_ink.sql"
  - "src/learnloop/db/stores/ink_strokes.py"
  - "src/learnloop/pads/ink_transcribe.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `ink_transcriptions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives ink transcription a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `transcription_id`, `owner_id`, `owner_kind`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> What one owner's standing strokes were read as. content_hash is the sha256 of the standing strokes' canonical JSON (the image sent was rendered from exactly those); latex_md is the reading (Markdown with LaTeX), confidence_label what the learner is told about it ('may_be_wrong': a model's reading, never checked; 'nothing_read': the model read no writing). task, provider and model name the route that read it; prompt_version the request's wording.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/267_reader_workbench_ink.sql`.
- **Schema touched by:** `267_reader_workbench_ink.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `transcription_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `owner_kind` | `TEXT` | yes | — | — | Stored value |
| `owner_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `latex_md` | `TEXT` | yes | — | — | Stored value |
| `confidence_label` | `TEXT` | yes | — | — | Stored value |
| `task` | `TEXT` | yes | — | — | Stored value |
| `provider` | `TEXT` | no | — | — | Stored value |
| `model` | `TEXT` | no | — | — | Stored value |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_ink_transcriptions_2` on `owner_kind`, `owner_id`, `content_hash` (unique).
- `sqlite_autoindex_ink_transcriptions_1` on `transcription_id` (unique).

Database triggers:

- `ink_transcriptions_no_delete` — schema-enforced lifecycle or immutability constraint.
- `ink_transcriptions_no_replace` — schema-enforced lifecycle or immutability constraint.
- `ink_transcriptions_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/ink_strokes.py`

### Direct SQL writers

- `src/learnloop/db/stores/ink_strokes.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/identity_pins_helpers.py`
- `tests/reader_rd8a_migration_helpers.py`
- `tests/test_reader_rd8a_migration.py`
- `tests/test_reader_rd8a_transcribe.py`

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
CREATE TABLE ink_transcriptions (
  transcription_id TEXT PRIMARY KEY,
  owner_kind TEXT NOT NULL CHECK (owner_kind IN ('block', 'annotation')),
  owner_id TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  latex_md TEXT NOT NULL,
  confidence_label TEXT NOT NULL CHECK (confidence_label IN ('may_be_wrong', 'nothing_read')),
  task TEXT NOT NULL,
  provider TEXT,
  model TEXT,
  prompt_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (owner_kind, owner_id, content_hash)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

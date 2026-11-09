---
title: "learner_note_links"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "c8ed55f10b84fdce46fada919c39e9004aabff65"
source_commit_timestamp: "2026-11-09T12:16:08-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite learner_note_links"
  - "table learner_note_links"
schema_head: 251
table_name: "learner_note_links"
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
  - "src/learnloop/source_retrieval/note_links.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `learner_note_links`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves explicit relationship edges for learner note so learner-facing mastery and capability decisions use a reproducible evidence projection. It supplies replay-stable input rather than a disposable cache. Rows bind `note_id`, `learning_object_id`, `extraction_id`, making the operational relationship explicit. ^table-purpose

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
| `note_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/learner_notes\|learner_notes.id]] | Stored value |
| `note_key` | `TEXT` | yes | — | — | Stored value |
| `target_kind` | `TEXT` | yes | — | — | Stored value |
| `target_key` | `TEXT` | yes | — | — | Stored value |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `extraction_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `section_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `span_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `goal_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `authorship` | `TEXT` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `how` | `TEXT` | no | — | — | Stored value |
| `how_line` | `TEXT` | no | — | — | Stored value |
| `state_key` | `TEXT` | no | — | — | Stored value |
| `ledger_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/judgment_ledger\|judgment_ledger.id]] | Stored value |
| `model` | `TEXT` | no | — | — | Stored value |
| `prompt_version` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `ledger_id` → [[Reference/Database/Tables/judgment_ledger|`judgment_ledger.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `note_id` → [[Reference/Database/Tables/learner_notes|`learner_notes.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_learner_note_links_reading` on `extraction_id`, `section_id`.
- `idx_learner_note_links_lo` on `learning_object_id`, `created_at`.
- `idx_learner_note_links_note` on `note_key`, `created_at`.
- `sqlite_autoindex_learner_note_links_1` on `id` (unique).

Database triggers:

- `learner_note_links_no_delete` — schema-enforced lifecycle or immutability constraint.
- `learner_note_links_no_update` — schema-enforced lifecycle or immutability constraint.

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
- `tests/test_curriculum_c3_exam_scoping.py`
- `tests/test_learner_note_source_kind_migration.py`
- `tests/test_learner_notes_migration.py`
- `tests/test_learner_notes_vault_origin_migration.py`
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
CREATE TABLE learner_note_links (
  id TEXT PRIMARY KEY,
  note_id TEXT NOT NULL REFERENCES learner_notes(id),
  note_key TEXT NOT NULL,
  target_kind TEXT NOT NULL CHECK (target_kind IN ('passage', 'learning_object')),
  target_key TEXT NOT NULL,
  learning_object_id TEXT,
  extraction_id TEXT,
  section_id TEXT,
  span_id TEXT,
  goal_id TEXT,
  authorship TEXT NOT NULL CHECK (authorship IN ('ai', 'learner')),
  status TEXT NOT NULL CHECK (status IN ('proposed', 'accepted', 'rejected')),
  how TEXT CHECK (how IS NULL OR how IN ('restates', 'questions', 'disagrees', 'applies', 'worked_it')),
  how_line TEXT,
  state_key TEXT,
  ledger_id TEXT REFERENCES judgment_ledger(id),
  model TEXT,
  prompt_version TEXT,
  created_at TEXT NOT NULL,
  CHECK (target_kind <> 'passage' OR (extraction_id IS NOT NULL AND (section_id IS NOT NULL OR span_id IS NOT NULL))),
  CHECK (target_kind <> 'learning_object' OR learning_object_id IS NOT NULL),
  CHECK (authorship <> 'ai' OR (status = 'proposed' AND learning_object_id IS NOT NULL AND state_key IS NOT NULL
                                AND model IS NOT NULL AND prompt_version IS NOT NULL AND ledger_id IS NOT NULL)),
  CHECK (authorship <> 'learner' OR status IN ('accepted', 'rejected'))
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

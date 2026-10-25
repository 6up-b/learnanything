---
title: "passage_links"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "a5c36443023a87678721d241d47d6fe4b45fc108"
source_commit_timestamp: "2026-10-25T17:00:22-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite passage_links"
  - "table passage_links"
schema_head: 222
table_name: "passage_links"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "215_reader_discovered_cues.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/215_reader_discovered_cues.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/db/stores/reader_cue_links.py"
  - "src/learnloop/reader/reader_report.py"
  - "src/learnloop/source_retrieval/passage_cues.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `passage_links`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves explicit relationship edges for passage so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `extraction_id`, `span_id`, `target_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/215_reader_discovered_cues.sql`.
- **Schema touched by:** `215_reader_discovered_cues.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `extraction_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `span_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `target_kind` | `TEXT` | yes | — | — | Stored value |
| `target_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `relation` | `TEXT` | yes | — | — | Stored value |
| `quote` | `TEXT` | yes | — | — | Stored value |
| `pick_rank` | `INTEGER` | yes | — | — | Stored value |
| `ranks_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `roles_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `target_facets_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `ledger_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/judgment_ledger\|judgment_ledger.id]] | Stored value |
| `state_key` | `TEXT` | yes | — | — | Stored value |
| `model` | `TEXT` | yes | — | — | Stored value |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `ledger_id` → [[Reference/Database/Tables/judgment_ledger|`judgment_ledger.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_passage_links_target` on `target_kind`, `target_id`.
- `idx_passage_links_extraction` on `extraction_id`, `state_key`.
- `sqlite_autoindex_passage_links_2` on `extraction_id`, `target_kind`, `target_id`, `state_key`, `span_id` (unique).
- `sqlite_autoindex_passage_links_1` on `id` (unique).

Database triggers:

- `passage_links_no_delete` — schema-enforced lifecycle or immutability constraint.
- `passage_links_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/reader_cue_links.py`
- `src/learnloop/reader/reader_report.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_architecture.py`
- `tests/test_reader_cues_cli_report.py`
- `tests/test_reader_rw3b_migration.py`
- `tests/test_reader_rw3b_protection.py`
- `tests/test_reader_rw3b_review_fixes.py`
- `tests/test_salience_firewall.py`

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
CREATE TABLE passage_links (
  id TEXT PRIMARY KEY,
  extraction_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  target_kind TEXT NOT NULL CHECK (target_kind IN (
    'recurrence_group', 'hypothesis', 'misconception', 'learner_text_gap', 'demonstrated_facet', 'unchecked_claim'
  )),
  target_id TEXT NOT NULL,
  relation TEXT NOT NULL CHECK (relation IN (
    'clarifies_distinction', 'new_application', 'prerequisite_for', 'try_first'
  )),
  quote TEXT NOT NULL,
  pick_rank INTEGER NOT NULL CHECK (pick_rank >= 1),
  ranks_json TEXT NOT NULL DEFAULT '{}',
  roles_json TEXT NOT NULL DEFAULT '[]',
  target_facets_json TEXT NOT NULL DEFAULT '[]',
  ledger_id TEXT NOT NULL REFERENCES judgment_ledger(id),
  state_key TEXT NOT NULL,
  model TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (extraction_id, target_kind, target_id, state_key, span_id)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

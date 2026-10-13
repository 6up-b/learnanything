---
title: "item_skeletons"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "68408145bb52bb64c16da3809dfeea6bd592b1bf"
source_commit_timestamp: "2026-10-13T14:48:55-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite item_skeletons"
  - "table item_skeletons"
schema_head: 197
table_name: "item_skeletons"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "174_pf_generation.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/174_pf_generation.sql"
  - "src/learnloop/db/stores/pf.py"
  - "src/learnloop/ops/pf_generation.py"
  - "src/learnloop/substrate/item_fingerprints.py"
  - "src/learnloop/vault/embedding_recipes.py"
  - "src/learnloop/vault/hashes.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `item_skeletons`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives item skeleton a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `subject_id`, `model_id`, `subject_kind`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> WORKFLOW: LLM-written solution skeletons (technique sequence + operation graph), keyed by the described item text's content hash. Paid output: never regenerated on rebuild.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/174_pf_generation.sql`.
- **Schema touched by:** `174_pf_generation.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `subject_kind` | `TEXT` | yes | — | — | Stored value |
| `subject_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `model_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `techniques_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `operations_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `checkpoints_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `skeleton_text` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_item_skeletons_hash` on `content_hash`.
- `sqlite_autoindex_item_skeletons_2` on `content_hash`, `model_id`, `prompt_version` (unique).
- `sqlite_autoindex_item_skeletons_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/pf.py`
- `src/learnloop/vault/embedding_recipes.py`

### Direct SQL writers

- `src/learnloop/db/stores/pf.py`

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
CREATE TABLE item_skeletons (
  id TEXT PRIMARY KEY,
  content_hash TEXT NOT NULL,
  subject_kind TEXT NOT NULL CHECK (subject_kind IN ('practice_item', 'pf_candidate')),
  subject_id TEXT NOT NULL,
  model_id TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  techniques_json TEXT NOT NULL,
  operations_json TEXT NOT NULL,
  checkpoints_json TEXT NOT NULL,
  skeleton_text TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(content_hash, model_id, prompt_version)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

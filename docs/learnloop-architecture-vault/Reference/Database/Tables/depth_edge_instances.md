---
title: "depth_edge_instances"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite depth_edge_instances"
  - "table depth_edge_instances"
schema_head: 156
table_name: "depth_edge_instances"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "107_depth_edge_templates.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/107_depth_edge_templates.sql"
  - "src/learnloop/ai/routing.py"
  - "src/learnloop/curriculum/depth_edge_authoring.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/cli/depth.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `depth_edge_instances`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives depth edge instance a stable database identity so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `template_version_id`, `commitment_id`, `edge_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/107_depth_edge_templates.sql`.
- **Schema touched by:** `107_depth_edge_templates.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `template_version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/depth_edge_template_versions\|depth_edge_template_versions.id]] | Stored value |
| `commitment_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `edge_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `predecessor_milestone` | `TEXT` | yes | — | — | Stored value |
| `successor_milestone_slug` | `TEXT` | yes | — | — | Stored value |
| `successor_task_contract_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `entry_evidence_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `exit_evidence_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `fresh_proof_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `expected_burden_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `activity_path_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | `'proposed'` | — | Stored value |
| `admission_report_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `pinned_envelope_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/depth_envelope_versions\|depth_envelope_versions.id]] | Stored value |
| `receipt_key` | `TEXT` | no | — | — | Stored value |
| `author` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `pinned_envelope_version_id` → [[Reference/Database/Tables/depth_envelope_versions|`depth_envelope_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `template_version_id` → [[Reference/Database/Tables/depth_edge_template_versions|`depth_edge_template_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_depth_edge_instances_commitment` on `commitment_id`, `status`.
- `sqlite_autoindex_depth_edge_instances_2` on `receipt_key` (unique).
- `sqlite_autoindex_depth_edge_instances_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.depth_edge_instance()`
- `Repository.depth_edge_instances_for()`
- `Repository.insert_depth_edge_instance()`
- `Repository.update_depth_edge_instance_status()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/curriculum/depth_edge_authoring.py`
- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/depth.py`
- `src/learnloop/curriculum/depth_edge_authoring.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/structured_ai.py`
- `tests/test_openai_chat_client.py`
- `tests/test_structured_transport_parity.py`

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
CREATE TABLE depth_edge_instances (
  id TEXT PRIMARY KEY,
  template_version_id TEXT NOT NULL REFERENCES depth_edge_template_versions(id),
  commitment_id TEXT NOT NULL,
  edge_id TEXT NOT NULL,
  predecessor_milestone TEXT NOT NULL,
  successor_milestone_slug TEXT NOT NULL,
  successor_task_contract_json TEXT NOT NULL,
  entry_evidence_json TEXT,
  exit_evidence_json TEXT,
  fresh_proof_json TEXT,
  expected_burden_json TEXT,
  activity_path_json TEXT,
  status TEXT NOT NULL DEFAULT 'proposed' CHECK (
    status IN ('proposed', 'admitted', 'rejected', 'confirmed', 'pinned')
  ),
  admission_report_json TEXT,
  pinned_envelope_version_id TEXT REFERENCES depth_envelope_versions(id),
  receipt_key TEXT UNIQUE,
  author TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

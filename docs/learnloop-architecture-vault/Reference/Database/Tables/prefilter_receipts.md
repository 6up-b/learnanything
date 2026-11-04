---
title: "prefilter_receipts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "094836387e8580ee3996941f4e181b109942c8dc"
source_commit_timestamp: "2026-11-04T11:35:15-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite prefilter_receipts"
  - "table prefilter_receipts"
schema_head: 242
table_name: "prefilter_receipts"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "240_data_capture.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/240_data_capture.sql"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/db/stores/data_capture.py"
  - "src/learnloop/ops/capture_report.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `prefilter_receipts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Freezes the inputs and outcome of each prefilter decision so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `decision_id`, `decision_kind`, `receipt_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/240_data_capture.sql`.
- **Schema touched by:** `240_data_capture.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `decision_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/router_decisions\|router_decisions.id]] | Stored value |
| `decision_kind` | `TEXT` | yes | — | — | Stored value |
| `surface` | `TEXT` | yes | — | — | Stored value |
| `receipt_version` | `TEXT` | yes | — | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `code_revision` | `TEXT` | yes | — | — | Stored value |
| `config_hash` | `TEXT` | yes | — | — | Stored value |
| `versions_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `session_present` | `INTEGER` | yes | — | — | Stored value |
| `scheduler_trace` | `INTEGER` | yes | — | — | Stored value |
| `considered_count` | `INTEGER` | yes | — | — | Stored value |
| `admitted_count` | `INTEGER` | yes | — | — | Stored value |
| `refused_count` | `INTEGER` | yes | — | — | Stored value |
| `gates_hash` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/prefilter_payloads\|prefilter_payloads.content_hash]] | Stored value |
| `classification_hash` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/prefilter_payloads\|prefilter_payloads.content_hash]] | Stored value |
| `upstream_hash` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/prefilter_payloads\|prefilter_payloads.content_hash]] | Stored value |
| `inputs_hash` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/prefilter_payloads\|prefilter_payloads.content_hash]] | Stored value |
| `config_payload_hash` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/prefilter_payloads\|prefilter_payloads.content_hash]] | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `config_payload_hash` → [[Reference/Database/Tables/prefilter_payloads|`prefilter_payloads.content_hash`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `inputs_hash` → [[Reference/Database/Tables/prefilter_payloads|`prefilter_payloads.content_hash`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `upstream_hash` → [[Reference/Database/Tables/prefilter_payloads|`prefilter_payloads.content_hash`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `classification_hash` → [[Reference/Database/Tables/prefilter_payloads|`prefilter_payloads.content_hash`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `gates_hash` → [[Reference/Database/Tables/prefilter_payloads|`prefilter_payloads.content_hash`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `decision_id` → [[Reference/Database/Tables/router_decisions|`router_decisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `prefilter_receipts_created` on `created_at`.
- `sqlite_autoindex_prefilter_receipts_2` on `decision_id` (unique).
- `sqlite_autoindex_prefilter_receipts_1` on `id` (unique).

Database triggers:

- `prefilter_receipts_no_delete` — schema-enforced lifecycle or immutability constraint.
- `prefilter_receipts_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/data_capture.py`
- `src/learnloop/ops/capture_report.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_data_capture_a1_prefilter.py`
- `tests/test_data_capture_migration.py`
- `tests/test_data_capture_phone.py`
- `tests/test_data_capture_report.py`

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
CREATE TABLE prefilter_receipts (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL UNIQUE REFERENCES router_decisions(id),
  decision_kind TEXT NOT NULL,
  surface TEXT NOT NULL,
  receipt_version TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  code_revision TEXT NOT NULL,
  config_hash TEXT NOT NULL,
  versions_json TEXT NOT NULL,
  session_present INTEGER NOT NULL CHECK (session_present IN (0, 1)),
  scheduler_trace INTEGER NOT NULL CHECK (scheduler_trace IN (0, 1)),
  considered_count INTEGER NOT NULL CHECK (considered_count >= 0),
  admitted_count INTEGER NOT NULL CHECK (admitted_count >= 0),
  refused_count INTEGER NOT NULL CHECK (refused_count >= 0),
  gates_hash TEXT NOT NULL REFERENCES prefilter_payloads(content_hash),
  classification_hash TEXT NOT NULL REFERENCES prefilter_payloads(content_hash),
  upstream_hash TEXT NOT NULL REFERENCES prefilter_payloads(content_hash),
  inputs_hash TEXT NOT NULL REFERENCES prefilter_payloads(content_hash),
  config_payload_hash TEXT NOT NULL REFERENCES prefilter_payloads(content_hash),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

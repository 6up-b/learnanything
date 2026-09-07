---
title: "shadow_component_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite shadow_component_events"
  - "table shadow_component_events"
schema_head: 157
table_name: "shadow_component_events"
table_role: "receipt"
functionality_status: "dormant-shadow"
domain_family: "scheduling"
introduced_in: "100_kinship_kernel_and_shadow_components.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/100_kinship_kernel_and_shadow_components.sql"
  - "src/learnloop/scheduling/shadow_components.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/dormant-shadow"
  - "learnloop/domain/scheduling"
---

# `shadow_component_events`

> [!warning] Dormant Shadow
> Deliberately firewalled component lifecycle telemetry.

## Why it exists

Records the lifecycle of deliberately firewalled shadow scoring components. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `promotion_evidence_id`, `event_kind`, `component`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Append-only predictive-component lifecycle events (shadow / promotion). Promotion feeds the staged policy's INPUTS only and emits a U-022 promotion-evidence artifact (parameter_sensitivity_certificates id); the monolithic action chooser is NEVER a promotable target here (structural guard refuses it, U-025 §7.4).

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `dormant-shadow`.
- **Introduced by:** `migrations/100_kinship_kernel_and_shadow_components.sql`.
- **Schema touched by:** `100_kinship_kernel_and_shadow_components.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `component` | `TEXT` | yes | — | — | Stored value |
| `event_ordinal` | `INTEGER` | yes | — | — | Stored value |
| `event_kind` | `TEXT` | yes | — | — | Stored value |
| `promotion_evidence_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `detail_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_shadow_component_events_component` on `component`, `event_ordinal`.
- `sqlite_autoindex_shadow_component_events_2` on `component`, `event_ordinal` (unique).
- `sqlite_autoindex_shadow_component_events_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/scheduling/shadow_components.py`

### Direct SQL writers

- `src/learnloop/scheduling/shadow_components.py`

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
CREATE TABLE shadow_component_events (
  id TEXT PRIMARY KEY,
  component TEXT NOT NULL,
  event_ordinal INTEGER NOT NULL,
  event_kind TEXT NOT NULL CHECK (event_kind IN ('shadow', 'promotion')),
  promotion_evidence_id TEXT,
  detail_json TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(component, event_ordinal)
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

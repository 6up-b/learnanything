---
title: "facet_registry_saves"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "118fba8a89256015a4a65336742998e3ff284be0"
source_commit_timestamp: "2026-10-13T16:47:23-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite facet_registry_saves"
  - "table facet_registry_saves"
schema_head: 197
table_name: "facet_registry_saves"
table_role: "workflow"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "197_facet_registry_saves.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/197_facet_registry_saves.sql"
  - "src/learnloop/content/facet_identity/actions.py"
  - "src/learnloop/db/stores/facet_identity.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `facet_registry_saves`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives facet registry save a stable database identity so learner-facing mastery and capability decisions use a reproducible evidence projection. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `status`, `abandoned_at`, making the operational relationship explicit. ^table-purpose

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/197_facet_registry_saves.sql`.
- **Schema touched by:** `197_facet_registry_saves.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `status` | `TEXT` | yes | — | — | Stored value |
| `facets_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `judgment_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `action_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `applied_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `abandoned_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `settle_detail_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `facet_registry_saves_status` on `status`, `created_at`.
- `sqlite_autoindex_facet_registry_saves_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/facet_identity.py`

### Direct SQL writers

- `src/learnloop/db/stores/facet_identity.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_facet_authority_rereview.py`
- `tests/test_facet_reword_confirm.py`

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
CREATE TABLE facet_registry_saves (
    -- The save id the owner's verdicts carry (rationale.save_id).
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('applying', 'applied', 'abandoned')),
    -- {facet_id: {"before": wording key or null for a new facet,
    --             "after": wording key, "fields": [...]}}: the facets whose
    -- meaning the save changes; a wording key is the verdict's right_id.
    facets_json TEXT NOT NULL,
    -- {facet_id: judgment_ledger id}: the owner's granted verdict for each.
    judgment_ids_json TEXT NOT NULL,
    -- The reword actions (facet versions) the save recorded, if any.
    action_ids_json TEXT NOT NULL DEFAULT '[]',
    applied_at TEXT,
    abandoned_at TEXT,
    -- Why an abandoned save never landed, and the verdicts withdrawn.
    settle_detail_json TEXT
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

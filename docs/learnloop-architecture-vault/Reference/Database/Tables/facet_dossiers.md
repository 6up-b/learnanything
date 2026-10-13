---
title: "facet_dossiers"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "724bca0f4f0b8eefe58a93785cbdc7db7f64bc73"
source_commit_timestamp: "2026-10-13T08:02:15-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite facet_dossiers"
  - "table facet_dossiers"
schema_head: 190
table_name: "facet_dossiers"
table_role: "workflow"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "169_practice_index.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/169_practice_index.sql"
  - "src/learnloop/db/stores/practice_index.py"
  - "src/learnloop/vault/embedding_recipes.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `facet_dossiers`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives facet dossier a stable database identity so learner-facing mastery and capability decisions use a reproducible evidence projection. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `facet_id`, `model_id`, `run_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Slice A Phase 5b: the practice index (spec_embedding_consumers_v1.md §5.9). Paid outputs and receipts only. Nothing here is evidence, nothing is derived, and replay never clears or regenerates any of it. One LLM-written dossier per facet revision, source revision, model and prompt. A row is a paid input: regenerated only when the facet or its grounding sources change (a new key), never on rebuild.

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/169_practice_index.sql`.
- **Schema touched by:** `169_practice_index.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `facet_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `facet_content_hash` | `TEXT` | yes | — | — | Stored value |
| `source_hash` | `TEXT` | yes | — | — | Stored value |
| `model_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `scope` | `TEXT` | yes | — | — | Stored value |
| `moves` | `TEXT` | yes | — | — | Stored value |
| `errors` | `TEXT` | yes | — | — | Stored value |
| `contrast` | `TEXT` | yes | — | — | Stored value |
| `draft_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `grounding_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `input_hash` | `TEXT` | yes | — | — | Stored value |
| `provider` | `TEXT` | no | — | — | Stored value |
| `billing` | `TEXT` | yes | — | — | Stored value |
| `run_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `facet_dossiers_facet` on `facet_id`, `created_at`.
- `sqlite_autoindex_facet_dossiers_2` on `facet_id`, `facet_content_hash`, `source_hash`, `model_id`, `prompt_version` (unique).
- `sqlite_autoindex_facet_dossiers_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/practice_index.py`

### Direct SQL writers

- `src/learnloop/db/stores/practice_index.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_practice_index_adapters.py`
- `tests/test_practice_index_dossiers.py`

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
CREATE TABLE facet_dossiers (
    id TEXT PRIMARY KEY,
    facet_id TEXT NOT NULL,
    facet_content_hash TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    model_id TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(length(trim(scope)) > 0),
    moves TEXT NOT NULL CHECK(length(trim(moves)) > 0),
    errors TEXT NOT NULL,
    contrast TEXT NOT NULL,
    draft_json TEXT NOT NULL,
    grounding_json TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    provider TEXT,
    billing TEXT NOT NULL CHECK(billing IN ('subscription', 'metered')),
    run_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(facet_id, facet_content_hash, source_hash, model_id, prompt_version)
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

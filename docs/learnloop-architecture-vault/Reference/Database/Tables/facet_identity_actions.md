---
title: "facet_identity_actions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "d9f2d70b989eb23b3330dd5c98bac1b146551d21"
source_commit_timestamp: "2026-10-18T04:29:05-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite facet_identity_actions"
  - "table facet_identity_actions"
schema_head: 211
table_name: "facet_identity_actions"
table_role: "workflow"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "183_facet_identity_actions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/183_facet_identity_actions.sql"
  - "src/learnloop/content/synthesis/source_append.py"
  - "src/learnloop/content/synthesis/source_set_synthesis.py"
  - "src/learnloop/db/stores/facet_identity.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/substrate/dataset.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `facet_identity_actions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives facet identity action a stable database identity so learner-facing mastery and capability decisions use a reproducible evidence projection. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `run_id`, `proposal_id`, `survivor_facet_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Facet identity (handoff §4): every merge or absorb a judge applied, with the facets.yaml entries before and after it, so a one-tap undo restores them exactly. Lifecycle state, never cleared by replay: proposed (an ingest action riding on its proposal), applying and undoing (write-ahead intents committed before facets.yaml is written; recovery finishes them), applied, undone, and abandoned (an intent withdrawn before its file write). The verdicts live in judgment_ledger (task same_facet), including the owner's on undo.

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/183_facet_identity_actions.sql`.
- **Schema touched by:** `183_facet_identity_actions.sql`, `196_facet_identity_rewords.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `origin` | `TEXT` | yes | — | — | Stored value |
| `scope` | `TEXT` | yes | — | — | Stored value |
| `run_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `proposal_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `action` | `TEXT` | yes | — | — | Stored value |
| `survivor_facet_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `retired_facet_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `before_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `after_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `merge_rows_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `judgment_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `judge` | `TEXT` | yes | — | — | Stored value |
| `judge_model` | `TEXT` | no | — | — | Stored value |
| `prompt_version` | `TEXT` | no | — | — | Stored value |
| `detail_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | — | — | Stored value |
| `applied_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `undone_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `undo_detail_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `facet_identity_actions_survivor` on `survivor_facet_id`, `status`.
- `facet_identity_actions_run` on `run_id`, `created_at`.
- `sqlite_autoindex_facet_identity_actions_1` on `id` (unique).

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

- `tests/test_facet_identity_actions.py`
- `tests/test_facet_rewords_migration.py`

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
CREATE TABLE "facet_identity_actions" (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    -- ingest (bootstrap synthesis), append, dedupe, proposal (a reword
    -- applied from a proposal) or registry (an owner-requested merge).
    origin TEXT NOT NULL CHECK (origin IN ('ingest', 'append', 'dedupe', 'proposal', 'registry')),
    -- in_run: candidates of one run; attach: a candidate into a registered
    -- facet; vault: registered facets (a merge, or one facet's reword).
    scope TEXT NOT NULL CHECK (scope IN ('in_run', 'attach', 'vault')),
    run_id TEXT NOT NULL,
    proposal_id TEXT,
    action TEXT NOT NULL CHECK (action IN ('merge', 'absorb', 'reword')),
    survivor_facet_id TEXT NOT NULL,
    retired_facet_ids_json TEXT NOT NULL,
    -- {facet_id: entry or null}: the facets.yaml entries the action replaced.
    before_json TEXT NOT NULL,
    -- {facet_id: entry or null}: the entries it wrote.
    after_json TEXT NOT NULL,
    -- [[retired, survivor], ...] facet_merges rows the action inserted.
    merge_rows_json TEXT NOT NULL DEFAULT '[]',
    judgment_ids_json TEXT NOT NULL DEFAULT '[]',
    judge TEXT NOT NULL,
    judge_model TEXT,
    prompt_version TEXT,
    detail_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL CHECK (
        status IN ('proposed', 'applying', 'applied', 'undoing', 'undone', 'abandoned')
    ),
    applied_at TEXT,
    undone_at TEXT,
    undo_detail_json TEXT
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

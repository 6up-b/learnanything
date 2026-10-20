---
title: "practice_index_proposals"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "d32c471d591f407360b8823fc8e62c9bdd37c999"
source_commit_timestamp: "2026-10-20T14:45:55-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite practice_index_proposals"
  - "table practice_index_proposals"
schema_head: 213
table_name: "practice_index_proposals"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "169_practice_index.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/169_practice_index.sql"
  - "src/learnloop/db/stores/practice_index.py"
  - "src/learnloop/instructional/interventions.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `practice_index_proposals`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives practice index proposal a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `query_id`, `rerank_status`, `algorithm_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> What each find_practice call proposed. It proposes and never serves; the row is the join key for later usage signals (judgment_ledger task practice_usage).

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/169_practice_index.sql`.
- **Schema touched by:** `169_practice_index.sql`, `187_source_service_callers.sql`, `190_source_valuations.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `origin` | `TEXT` | yes | — | — | Stored value |
| `query_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `query_text` | `TEXT` | yes | — | — | Stored value |
| `constraints_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `path` | `TEXT` | yes | — | — | Stored value |
| `path_reason` | `TEXT` | yes | — | — | Stored value |
| `signals_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `reranked` | `INTEGER` | yes | — | — | Stored value |
| `rerank_status` | `TEXT` | yes | — | — | Stored value |
| `rerank_model` | `TEXT` | no | — | — | Stored value |
| `proposed_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `exclusions_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `manifest_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `caller` | `TEXT` | no | — | — | Stored value |
| `caller_ref` | `TEXT` | no | — | — | Stored value |
| `intent` | `TEXT` | no | — | — | Stored value |
| `valuation_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `provisional_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `practice_index_proposals_created` on `created_at`.
- `sqlite_autoindex_practice_index_proposals_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/practice_index.py`
- `src/learnloop/instructional/interventions.py`

### Direct SQL writers

- `src/learnloop/db/stores/practice_index.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_discriminating_search.py`
- `tests/test_exercise_arm.py`
- `tests/test_hypothesis_reference_contract.py`
- `tests/test_practice_availability.py`
- `tests/test_practice_index_find.py`
- `tests/test_practice_proposal_caller_columns.py`
- `tests/test_source_first_needs.py`
- `tests/test_tutor_practice_request.py`

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
CREATE TABLE practice_index_proposals (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    origin TEXT NOT NULL CHECK(origin IN ('rpc', 'cli', 'tool', 'api')),
    query_id TEXT NOT NULL,
    query_text TEXT NOT NULL,
    constraints_json TEXT NOT NULL,
    path TEXT NOT NULL CHECK(path IN ('dossier', 'direct')),
    path_reason TEXT NOT NULL,
    signals_json TEXT NOT NULL,
    reranked INTEGER NOT NULL CHECK(reranked IN (0, 1)),
    rerank_status TEXT NOT NULL,
    rerank_model TEXT,
    proposed_json TEXT NOT NULL,
    exclusions_json TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    algorithm_version TEXT NOT NULL
, caller TEXT, caller_ref TEXT, intent TEXT, valuation_json TEXT, provisional_json TEXT);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

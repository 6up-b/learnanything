---
title: "retrieval_fusion_posteriors"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "c05eae57933f963158a782836b8d6b88af5d80a2"
source_commit_timestamp: "2026-10-24T15:05:22-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite retrieval_fusion_posteriors"
  - "table retrieval_fusion_posteriors"
schema_head: 219
table_name: "retrieval_fusion_posteriors"
table_role: "derived"
functionality_status: "active"
domain_family: "operations"
introduced_in: "219_retrieval_spaces.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/219_retrieval_spaces.sql"
  - "src/learnloop/db/stores/retrieval_spaces.py"
  - "src/learnloop/local_embeddings/fusion.py"
  - "src/learnloop/source_retrieval/feedback.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `retrieval_fusion_posteriors`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives retrieval fusion posterior a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `query_kind`, `fit_version`, `context_key`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> DERIVED: the fusion posterior per context (the global context and each consumer x query kind), recomputed from retrieval_feedback in order by its one replayer (substrate/rebuild_orchestrator.py, retrieval_fusion_posteriors). Deterministic: the fit has no random step and fitted_at is the newest input row's time, so a replay is byte-identical.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/219_retrieval_spaces.sql`.
- **Schema touched by:** `219_retrieval_spaces.sql`.
- **Rebuild owner:** `retrieval_fusion_posteriors`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `context_key` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `consumer` | `TEXT` | yes | — | — | Stored value |
| `query_kind` | `TEXT` | yes | — | — | Stored value |
| `lists_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `mean_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `covariance_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `intercepts_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `examination_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `rrf_k` | `REAL` | yes | — | — | Stored value |
| `observations` | `INTEGER` | yes | — | — | Stored value |
| `signals` | `INTEGER` | yes | — | — | Stored value |
| `prior_basis_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `fit_version` | `TEXT` | yes | — | — | Stored value |
| `input_digest` | `TEXT` | yes | — | — | Stored value |
| `fitted_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_retrieval_fusion_posteriors_1` on `context_key` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/retrieval_spaces.py`
- `src/learnloop/source_retrieval/feedback.py`

### Direct SQL writers

- `src/learnloop/db/stores/retrieval_spaces.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_retrieval_spaces_migration.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.
5. Update the single owner in `DERIVED_STATE_REPLAYERS`, then prove same-version rebuild equivalence and shadow isolation.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE retrieval_fusion_posteriors (
  context_key TEXT PRIMARY KEY,
  consumer TEXT NOT NULL,
  query_kind TEXT NOT NULL,
  lists_json TEXT NOT NULL,
  mean_json TEXT NOT NULL,
  covariance_json TEXT NOT NULL,
  intercepts_json TEXT NOT NULL,
  examination_json TEXT NOT NULL,
  rrf_k REAL NOT NULL,
  observations INTEGER NOT NULL,
  signals INTEGER NOT NULL,
  prior_basis_json TEXT NOT NULL,
  fit_version TEXT NOT NULL,
  input_digest TEXT NOT NULL,
  fitted_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

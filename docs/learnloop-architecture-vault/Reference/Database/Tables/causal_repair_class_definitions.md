---
title: "causal_repair_class_definitions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite causal_repair_class_definitions"
  - "table causal_repair_class_definitions"
schema_head: 157
table_name: "causal_repair_class_definitions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "133_causal_mechanism_repair_key.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/133_causal_mechanism_repair_key.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_diagnostic_selector.py"
  - "src/learnloop/diagnosis/causal_selection_audit.py"
  - "src/learnloop/diagnosis/remediation.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `causal_repair_class_definitions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives causal repair class definition a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `repair_class_id`, `repair_equivalence_id`, `episode_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/133_causal_mechanism_repair_key.sql`.
- **Schema touched by:** `133_causal_mechanism_repair_key.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `repair_class_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `repair_equivalence_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `episode_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `operator` | `TEXT` | yes | — | — | Stored value |
| `repair_policy_version` | `TEXT` | yes | — | — | Stored value |
| `target_refs_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `preserve_refs_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `expected_minutes` | `REAL` | no | — | — | Stored value |
| `answer_reveal_budget` | `REAL` | yes | `0.0` | — | Stored value |
| `definition_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_causal_repair_class_equivalence` on `repair_equivalence_id`, `created_at`, `repair_class_id`.
- `sqlite_autoindex_causal_repair_class_definitions_1` on `repair_class_id` (unique).

Database triggers:

- `causal_repair_class_definitions_no_delete` — schema-enforced lifecycle or immutability constraint.
- `causal_repair_class_definitions_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.causal_repair_class_definitions()`
- `Repository.record_causal_repair_class_definitions()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_diagnostic_selector.py`
- `src/learnloop/diagnosis/causal_selection_audit.py`
- `src/learnloop/diagnosis/remediation.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_attribution_p1.py`
- `tests/test_causal_factor_deferral.py`
- `tests/test_causal_shadow_selection.py`

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
CREATE TABLE causal_repair_class_definitions (
  repair_class_id TEXT PRIMARY KEY,
  -- Cross-episode "same help" relation. NOT unique: many episode-scoped repair
  -- classes share one equivalence id, which is exactly the collapse A2 wants.
  repair_equivalence_id TEXT NOT NULL,
  -- The episode the class was minted for, kept for provenance. It is part of
  -- `repair_class_id`'s hash and deliberately NOT part of the equivalence id.
  episode_id TEXT NOT NULL,
  operator TEXT NOT NULL,
  repair_policy_version TEXT NOT NULL,
  target_refs_json TEXT NOT NULL,
  preserve_refs_json TEXT NOT NULL,
  -- Model self-reports, recorded because A1's receipts consume them as
  -- tie-breakers; never part of either id.
  expected_minutes REAL,
  answer_reveal_budget REAL NOT NULL DEFAULT 0.0,
  definition_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

---
title: "learner_theta"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite learner_theta"
  - "table learner_theta"
schema_head: 157
table_name: "learner_theta"
table_role: "compat"
functionality_status: "dormant-owner-gated"
domain_family: "learner-state"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/ops/debug_time.py"
  - "src/learnloop/ops/doctor.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/compat"
  - "learnloop/status/dormant-owner-gated"
  - "learnloop/domain/learner-state"
---

# `learner_theta`

> [!warning] Dormant Owner Gated
> Legacy state is retained pending decisive production-vault telemetry.

## Why it exists

Retains the legacy IRT theta table for compatibility and telemetry; it is not the canonical learner projection. It keeps an older vault or replay contract readable while new writes use the refactored path. Rows bind `algorithm_version`, `domain`, `evidence_family`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Display values mastery_mean = sigmoid(logit_mean) and mastery_variance = (m * (1 - m))^2 * logit_variance are computed on read in services/mastery.py; they are not stored.

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Compat]].

## Persistence and lifecycle contract

- **Role:** `compat` — Frozen compatibility state retained for old vaults or an incomplete replacement seam.
- **Functionality status:** `dormant-owner-gated`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `domain` | `TEXT` | yes | — | — | Stored value |
| `evidence_family` | `TEXT` | yes | — | — | Stored value |
| `practice_mode` | `TEXT` | no | — | — | Stored value |
| `theta_mean` | `REAL` | yes | — | — | Stored value |
| `theta_variance` | `REAL` | yes | — | — | Stored value |
| `evidence_count` | `INTEGER` | yes | `0` | — | Stored value |
| `prior_pseudo_count` | `REAL` | yes | `0.0` | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_learner_theta_unique` on `domain`, `evidence_family` (unique).
- `sqlite_autoindex_learner_theta_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

None found by exact static reference scan.

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_doctor.py`
- `tests/test_table_roles.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.
5. Compatibility retirement requires production-vault telemetry and an explicit owner decision; code detachment and schema changes are separate gates.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE learner_theta (
  id TEXT PRIMARY KEY,
  domain TEXT NOT NULL,
  evidence_family TEXT NOT NULL,
  practice_mode TEXT,
  theta_mean REAL NOT NULL,
  theta_variance REAL NOT NULL CHECK (theta_variance >= 0.0),
  evidence_count INTEGER NOT NULL DEFAULT 0 CHECK (evidence_count >= 0),
  prior_pseudo_count REAL NOT NULL DEFAULT 0.0 CHECK (prior_pseudo_count >= 0.0),
  algorithm_version TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Compat|compat policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

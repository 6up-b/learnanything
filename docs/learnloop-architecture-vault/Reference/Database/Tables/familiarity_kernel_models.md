---
title: "familiarity_kernel_models"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite familiarity_kernel_models"
  - "table familiarity_kernel_models"
schema_head: 156
table_name: "familiarity_kernel_models"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "100_kinship_kernel_and_shadow_components.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/100_kinship_kernel_and_shadow_components.sql"
  - "src/learnloop/scheduling/kinship_feature.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `familiarity_kernel_models`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives familiarity kernel model a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It supplies replay-stable input rather than a disposable cache. Rows bind `parent_id`, `admission_evidence_id`, `model_kind`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/100_kinship_kernel_and_shadow_components.sql`.
- **Schema touched by:** `100_kinship_kernel_and_shadow_components.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `model_kind` | `TEXT` | yes | `'heuristic_llm_judged'` | — | Stored value |
| `version` | `TEXT` | yes | — | — | Stored value |
| `parent_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/familiarity_kernel_models\|familiarity_kernel_models.id]] | Stored value |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | `'shadow'` | — | Stored value |
| `feature_schema_version` | `TEXT` | yes | — | — | Stored value |
| `preprocessing_version` | `TEXT` | no | — | — | Stored value |
| `manifests_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `scope_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `consent_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `metrics_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `calibration_status` | `TEXT` | no | — | — | Stored value |
| `admission_evidence_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `parent_id` → [[Reference/Database/Tables/familiarity_kernel_models|`familiarity_kernel_models.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_familiarity_kernel_models_status` on `status`.
- `sqlite_autoindex_familiarity_kernel_models_2` on `version` (unique).
- `sqlite_autoindex_familiarity_kernel_models_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/scheduling/kinship_feature.py`

### Direct SQL writers

- `src/learnloop/scheduling/kinship_feature.py`

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
CREATE TABLE familiarity_kernel_models (
  id TEXT PRIMARY KEY,
  model_kind TEXT NOT NULL DEFAULT 'heuristic_llm_judged'
    CHECK (model_kind IN ('heuristic_llm_judged')),
  version TEXT NOT NULL,
  parent_id TEXT REFERENCES familiarity_kernel_models(id),
  content_hash TEXT NOT NULL,
  -- Admission status. 'shadow' = computed + logged, consulted by NOTHING (firewall).
  -- 'simulation_validated' = the planted-learner sim admission gate certified it (the
  -- ONLY status a sim can grant, §8.4). 'retired' via a retirement event.
  status TEXT NOT NULL DEFAULT 'shadow'
    CHECK (status IN ('shadow', 'simulation_validated', 'retired')),
  -- Exact P1 feature schema + preprocessing/embedding versions consumed (§8.2).
  feature_schema_version TEXT NOT NULL,
  preprocessing_version TEXT,
  -- Training/evaluation manifests split by time/card/family/hard-group (§8.2). For the
  -- heuristic feature these are the sim EVALUATION manifests, not a training corpus.
  manifests_json TEXT,
  -- Learner-local scope + privacy/consent metadata (§8.2).
  scope_json TEXT,
  consent_json TEXT,
  -- Evaluation metrics + sample/effective-sample counts + calibration status (§8.2).
  metrics_json TEXT,
  calibration_status TEXT,
  -- The admission-gate promotion-evidence artifact (parameter_sensitivity_certificates
  -- row id) that granted 'simulation_validated' (U-022 through the registry machinery).
  admission_evidence_id TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(version)
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

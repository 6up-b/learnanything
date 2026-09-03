---
title: "activity_pattern_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite activity_pattern_versions"
  - "table activity_pattern_versions"
schema_head: 157
table_name: "activity_pattern_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "073_activity_patterns_and_features.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/073_activity_patterns_and_features.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/substrate/activity_patterns.py"
  - "src/learnloop/curriculum/depth_edge_authoring.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `activity_pattern_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of activity pattern so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `pattern_id`, `calibration_status`, `generator_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/073_activity_patterns_and_features.sql`.
- **Schema touched by:** `073_activity_patterns_and_features.sql`, `074_activity_contract_extensions.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `pattern_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_patterns\|activity_patterns.id]] | Stored value |
| `version` | `INTEGER` | yes | — | — | Stored value |
| `allowed_purposes_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `operation` | `TEXT` | yes | — | — | Stored value |
| `learning_process` | `TEXT` | yes | — | — | Stored value |
| `allowed_target_kinds_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `allowed_capabilities_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `completion_semantics_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `response_contract_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `progression_role` | `TEXT` | no | — | — | Stored value |
| `prerequisite_evidence_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `feedback_strategy_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `assistance_strategy_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `evidence_semantics_by_context_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `task_feature_bounds_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `variation_axes_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `rubric_shape_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `mint_gates_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `burden_model_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `calibration_status` | `TEXT` | yes | — | — | Stored value |
| `generator_version` | `TEXT` | no | — | — | Stored value |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `pattern_id` → [[Reference/Database/Tables/activity_patterns|`activity_patterns.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_apv_pattern_status` on `pattern_id`, `status`.
- `sqlite_autoindex_activity_pattern_versions_3` on `pattern_id`, `content_hash` (unique).
- `sqlite_autoindex_activity_pattern_versions_2` on `pattern_id`, `version` (unique).
- `sqlite_autoindex_activity_pattern_versions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._existing()`
- `Repository.activity_pattern_version()`
- `Repository.activity_pattern_version_by_slug()`
- `Repository.activity_pattern_versions()`
- `Repository.ensure_activity_pattern_version()`
- `Repository.set_activity_pattern_version_status()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/depth_edge_authoring.py`
- `src/learnloop/substrate/activity_patterns.py`

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
CREATE TABLE activity_pattern_versions (
  id TEXT PRIMARY KEY,
  pattern_id TEXT NOT NULL REFERENCES activity_patterns(id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  allowed_purposes_json TEXT NOT NULL,   -- subset of diagnostic/instructional/practice/assessment
  operation TEXT NOT NULL CHECK (operation IN (
    'retrieve', 'discriminate', 'generate', 'compare', 'explain',
    'set_up', 'apply', 'reflect', 'create')),
  -- U-035 induced learning process: closed vocabulary, ROUTING-ONLY.
  learning_process TEXT NOT NULL CHECK (learning_process IN (
    'prior_knowledge_activation', 'comprehension_monitoring', 'self_explanation',
    'schema_induction', 'procedure_compilation', 'memory_fluency', 'method_selection',
    'coordination', 'transfer', 'reflection')),
  allowed_target_kinds_json TEXT NOT NULL,
  allowed_capabilities_json TEXT NOT NULL,
  completion_semantics_json TEXT NOT NULL,
  response_contract_json TEXT NOT NULL,
  progression_role TEXT,
  prerequisite_evidence_json TEXT,
  feedback_strategy_json TEXT,
  assistance_strategy_json TEXT,
  evidence_semantics_by_context_json TEXT NOT NULL,
  task_feature_bounds_json TEXT NOT NULL,
  variation_axes_json TEXT NOT NULL,
  rubric_shape_json TEXT NOT NULL,
  mint_gates_json TEXT NOT NULL,
  burden_model_json TEXT,
  calibration_status TEXT NOT NULL CHECK (calibration_status IN (
    'heuristic', 'simulation_validated', 'live_calibrated')),
  generator_version TEXT,
  content_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('draft', 'reviewed', 'active', 'retired')),
  created_at TEXT NOT NULL,
  UNIQUE(pattern_id, version),
  UNIQUE(pattern_id, content_hash)
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

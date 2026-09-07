---
title: "controller_prequential_reports"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite controller_prequential_reports"
  - "table controller_prequential_reports"
schema_head: 157
table_name: "controller_prequential_reports"
table_role: "receipt"
functionality_status: "dormant-shadow"
domain_family: "scheduling"
introduced_in: "100_kinship_kernel_and_shadow_components.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/100_kinship_kernel_and_shadow_components.sql"
  - "src/learnloop/scheduling/prequential.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/dormant-shadow"
  - "learnloop/domain/scheduling"
---

# `controller_prequential_reports`

> [!warning] Dormant Shadow
> Evaluation over shadow telemetry; it has no live selection authority.

## Why it exists

Stores delayed evaluation reports over controller shadow predictions. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `target_kind`, `horizon_kind`, `report_hash`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> --------------------------------------------------------------------------- Step 6: prequential held-out reports (§7.3 "primary product") for shadow predictive components, plus the time-box registration for the SECONDARY composed-selector telemetry. Reports are rebuildable snapshots keyed by content. ---------------------------------------------------------------------------

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `dormant-shadow`.
- **Introduced by:** `migrations/100_kinship_kernel_and_shadow_components.sql`.
- **Schema touched by:** `100_kinship_kernel_and_shadow_components.sql`, `101_dual_authority_and_kinship_dedup.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `target_kind` | `TEXT` | yes | — | — | Stored value |
| `component` | `TEXT` | no | — | — | Stored value |
| `horizon_kind` | `TEXT` | yes | `'next_spaced_cold_review'` | — | Stored value |
| `metrics_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `splits_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `sample_count` | `INTEGER` | yes | `0` | — | Stored value |
| `report_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_controller_prequential_reports_hash` on `report_hash` (unique).
- `idx_controller_prequential_reports_target` on `target_kind`, `component`.
- `sqlite_autoindex_controller_prequential_reports_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/scheduling/prequential.py`

### Direct SQL writers

- `src/learnloop/scheduling/prequential.py`

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
CREATE TABLE controller_prequential_reports (
  id TEXT PRIMARY KEY,
  -- 'predictive_component:<name>' (primary) or 'composed_selector' (secondary).
  target_kind TEXT NOT NULL,
  component TEXT,
  -- The predeclared horizon these delayed outcomes resolved at (next spaced cold
  -- review, §9.3); a report never scores on immediate answer success.
  horizon_kind TEXT NOT NULL DEFAULT 'next_spaced_cold_review'
    CHECK (horizon_kind IN ('next_spaced_cold_review')),
  -- Prequential scores (log-loss / Brier) + n + effective sample, and the by-split
  -- breakdown (time / target family) that stops near-clone leakage (§7.2). A
  -- surface-group split is deferred until the outcome window carries a surface-group key.
  metrics_json TEXT NOT NULL,
  splits_json TEXT,
  sample_count INTEGER NOT NULL DEFAULT 0,
  report_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

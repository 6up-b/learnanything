---
title: "failure_triage_routes"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite failure_triage_routes"
  - "table failure_triage_routes"
schema_head: 156
table_name: "failure_triage_routes"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "tutor-and-remediation"
introduced_in: "083_diagnostic_pack_and_triage.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/083_diagnostic_pack_and_triage.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_diagnostic_selector.py"
  - "src/learnloop/diagnosis/failure_triage.py"
  - "src/learnloop/diagnosis/probe_episodes.py"
  - "src/learnloop/diagnosis/probe_hypotheses.py"
  - "src/learnloop/scheduling/action_loss.py"
  - "src/learnloop/diagnosis/causal_probe_coherence.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/tutor-and-remediation"
---

# `failure_triage_routes`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives failure triage route a stable database identity so tutor and repair work can be resumed, reviewed, and connected to subsequent evidence. It supplies replay-stable input rather than a disposable cache. Rows bind `route_id`, `route_version`, `reason`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> --------------------------------------------------------------------------- §6 Two-tier failure-reason triage (U-027). --------------------------------------------------------------------------- Versioned, reviewable route table (§6.2), REGISTERED AS DATA not code so owner edits/overrides are auditable. Maps each of the ten failure reasons to its first intervention, required cold follow-up, and the run-state-machine ladder entry stage the route names. `reopens_diagnostic` marks the only two reasons that may open/continue a diagnostic episode (§6.1).

It belongs to the **tutor and remediation** navigation family. The family context lives in [[Database Catalog#Tutor And Remediation]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/083_diagnostic_pack_and_triage.sql`.
- **Schema touched by:** `083_diagnostic_pack_and_triage.sql`, `084_pattern_ladder.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `route_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `route_version` | `INTEGER` | yes | `1` | — | Stored value |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `first_intervention` | `TEXT` | yes | — | — | Stored value |
| `cold_follow_up` | `TEXT` | yes | — | — | Stored value |
| `ladder_entry_stage` | `TEXT` | yes | — | — | Stored value |
| `reopens_diagnostic` | `INTEGER` | yes | `0` | — | Stored value |
| `active` | `INTEGER` | yes | `1` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_triage_routes_reason` on `reason`, `active`.
- `sqlite_autoindex_failure_triage_routes_2` on `route_id`, `route_version` (unique).
- `sqlite_autoindex_failure_triage_routes_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.failure_triage_route_for_reason()`
- `Repository.failure_triage_routes()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/causal_probe_coherence.py`
- `src/learnloop/diagnosis/failure_triage.py`
- `src/learnloop/diagnosis/probe_episodes.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_failure_triage.py`

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
CREATE TABLE failure_triage_routes (
  id TEXT PRIMARY KEY,
  route_id TEXT NOT NULL,
  route_version INTEGER NOT NULL DEFAULT 1,
  reason TEXT NOT NULL CHECK (reason IN (
    'memory_lapse', 'unfamiliar_or_missing_knowledge', 'schema_or_conceptual_hole',
    'false_belief_or_confusion', 'procedure_execution', 'method_selection',
    'coordination_or_integration', 'task_interpretation', 'surface_or_grading_fault',
    'unknown_or_ambiguous')),
  first_intervention TEXT NOT NULL,
  cold_follow_up TEXT NOT NULL,
  ladder_entry_stage TEXT NOT NULL,
  reopens_diagnostic INTEGER NOT NULL DEFAULT 0,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  UNIQUE(route_id, route_version)
);
```

## Related notes

- [[Database Catalog#Tutor And Remediation|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

---
title: "surface_mint_requests"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite surface_mint_requests"
  - "table surface_mint_requests"
schema_head: 156
table_name: "surface_mint_requests"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "078_surface_mint_jobs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/078_surface_mint_jobs.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/substrate/surface_mint.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `surface_mint_requests`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Queues a durable, retryable request for surface mint so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `card_version_id`, `anchor_surface_id`, `candidate_surface_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> P1 step 7 (spec_p1_shared_substrate §5.2, §5.3, §5.6): durable pre-mint jobs + the fixed/rotating surface mint/gate. Modeled on migration 033 (ingest_jobs): exactly one worker drains at a time via a lease, and an expired running lease is recovered. Jobs NEVER block attempt submission (§5.6, §9.7); opening an admitted administration calls no generator/LLM. Card/family retirement makes pending work 'obsolete'. A failed candidate is retained for audit but is never servable.  Rendering and candidate minting are SEPARATE transactions (§5.3): a cache race may waste a candidate but may not double-administer or manufacture novelty.  Migration numbering: highest applied on disk = 077 (familiarity namespace); P1 step 7 starts at 078. Never edit applied migrations 065-077.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/078_surface_mint_jobs.sql`.
- **Schema touched by:** `078_surface_mint_jobs.sql`, `080_mint_fencing_and_commitment_idempotency.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `card_version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_card_versions\|activity_card_versions.id]] | Stored value |
| `anchor_surface_id` | `TEXT` | yes | `''` | — | Application-validated soft reference |
| `requested_angle_json` | `TEXT` | yes | `''` | — | JSON-encoded structured payload |
| `generator_version` | `TEXT` | yes | — | — | Stored value |
| `gate_policy_version` | `TEXT` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | `'pending'` | — | Stored value |
| `lease_owner` | `TEXT` | no | — | — | Stored value |
| `lease_expires_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `lease_epoch` | `INTEGER` | yes | `0` | — | Stored value |
| `candidate_surface_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_surfaces\|activity_surfaces.id]] | Stored value |
| `gate_results_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `token_cost_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `failure_reason` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `candidate_surface_id` → [[Reference/Database/Tables/activity_surfaces|`activity_surfaces.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `card_version_id` → [[Reference/Database/Tables/activity_card_versions|`activity_card_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_smr_card_version` on `card_version_id`.
- `idx_smr_status` on `status`.
- `sqlite_autoindex_surface_mint_requests_2` on `card_version_id`, `anchor_surface_id`, `requested_angle_json`, `generator_version`, `gate_policy_version` (unique).
- `sqlite_autoindex_surface_mint_requests_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._existing()`
- `Repository.claim_next_surface_mint_request()`
- `Repository.enqueue_surface_mint_request()`
- `Repository.obsolete_surface_mint_requests_for_card_versions()`
- `Repository.resolve_surface_mint_request()`
- `Repository.set_surface_mint_candidate()`
- `Repository.surface_mint_request()`
- `Repository.surface_mint_requests_for_card_version()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/substrate/surface_mint.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_surface_mint.py`

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
CREATE TABLE "surface_mint_requests" (
  id TEXT PRIMARY KEY,
  card_version_id TEXT NOT NULL REFERENCES activity_card_versions(id),
  anchor_surface_id TEXT NOT NULL DEFAULT '',
  requested_angle_json TEXT NOT NULL DEFAULT '',
  generator_version TEXT NOT NULL,
  gate_policy_version TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
    'pending', 'running', 'candidate_ready', 'admitted', 'rejected', 'obsolete', 'failed')),
  lease_owner TEXT,
  lease_expires_at TEXT,
  lease_epoch INTEGER NOT NULL DEFAULT 0,
  candidate_surface_id TEXT REFERENCES activity_surfaces(id),
  gate_results_json TEXT,
  token_cost_json TEXT,
  failure_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(card_version_id, anchor_surface_id, requested_angle_json,
         generator_version, gate_policy_version)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

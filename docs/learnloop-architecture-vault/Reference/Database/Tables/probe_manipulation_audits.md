---
title: "probe_manipulation_audits"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite probe_manipulation_audits"
  - "table probe_manipulation_audits"
schema_head: 156
table_name: "probe_manipulation_audits"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "121_causal_probe_coherence.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/121_causal_probe_coherence.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_probe_coherence.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `probe_manipulation_audits`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives probe manipulation audit a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `source_item_id`, `candidate_item_id`, `generation_agent_run_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/121_causal_probe_coherence.sql`.
- **Schema touched by:** `121_causal_probe_coherence.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `source_kind` | `TEXT` | yes | — | — | Stored value |
| `source_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `candidate_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `contract_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `structural_diff_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `adversarial_review_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | — | — | Stored value |
| `generation_agent_run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `reviewer_agent_run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_probe_manipulation_audit_candidate` on `candidate_item_id`, `created_at`, `id`.
- `sqlite_autoindex_probe_manipulation_audits_1` on `id` (unique).

Database triggers:

- `probe_manipulation_audits_no_delete` — schema-enforced lifecycle or immutability constraint.
- `probe_manipulation_audits_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.insert_probe_manipulation_audit()`
- `Repository.probe_manipulation_audit()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_probe_coherence.py`

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
CREATE TABLE probe_manipulation_audits (
  id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL CHECK (
    source_kind IN ('causal_probe', 'rung_variant')
  ),
  source_item_id TEXT NOT NULL,
  candidate_item_id TEXT NOT NULL,
  contract_json TEXT NOT NULL,
  structural_diff_json TEXT NOT NULL,
  adversarial_review_json TEXT,
  status TEXT NOT NULL CHECK (
    status IN ('passed', 'rejected', 'pending_adversarial_review')
  ),
  generation_agent_run_id TEXT,
  reviewer_agent_run_id TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

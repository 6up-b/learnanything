---
title: "pf_candidates"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0eacfc61d71cd41a55913483b978e76a109fd4b0"
source_commit_timestamp: "2026-10-14T20:03:37-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite pf_candidates"
  - "table pf_candidates"
schema_head: 202
table_name: "pf_candidates"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "174_pf_generation.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/174_pf_generation.sql"
  - "src/learnloop/db/stores/pf.py"
  - "src/learnloop/ops/pf_generation.py"
  - "src/learnloop/ops/pf_publish.py"
  - "src/learnloop/ops/pf_reports.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `pf_candidates`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Holds candidates for pf while policy selects or reviews one so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `run_id`, `mint_request_id`, `family_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Slice A Phase 5a (PF-b, spec_embedding_consumers_v1 §5.3-§5.4, §12): generated candidates, LLM-written solution skeletons and deterministic item fingerprints. Generation jobs reuse surface_mint_requests (078); fingerprint keys reuse the 077 namespaces. Verdicts live in judgment_ledger (166). WORKFLOW: pipeline state for one generated candidate (filters, verification, difficulty, selection, publication, cost). Never evidence; never re-run on rebuild. An unverified candidate is never published (P9).

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/174_pf_generation.sql`.
- **Schema touched by:** `174_pf_generation.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `run_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `mint_request_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/surface_mint_requests\|surface_mint_requests.id]] | Stored value |
| `round` | `TEXT` | yes | — | — | Stored value |
| `tier` | `TEXT` | no | — | — | Stored value |
| `family_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `parent_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `generation_path` | `TEXT` | yes | — | — | Stored value |
| `declared_relation` | `TEXT` | yes | — | — | Stored value |
| `final_relation` | `TEXT` | no | — | — | Stored value |
| `proposer_model` | `TEXT` | no | — | — | Stored value |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `payload_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `verification` | `TEXT` | yes | `'unverified'` | — | Stored value |
| `verification_check` | `TEXT` | no | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `rejection_filter` | `TEXT` | no | — | — | Stored value |
| `filters_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `difficulty` | `REAL` | no | — | — | Stored value |
| `difficulty_source` | `TEXT` | no | — | — | Stored value |
| `panel_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `selection_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `cost_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `judged_inputs_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `published_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `published_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `mint_request_id` → [[Reference/Database/Tables/surface_mint_requests|`surface_mint_requests.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_pf_candidates_published` on `published_at`.
- `idx_pf_candidates_family` on `family_id`, `round`.
- `idx_pf_candidates_request` on `mint_request_id`.
- `sqlite_autoindex_pf_candidates_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/pf.py`
- `src/learnloop/ops/pf_generation.py`

### Direct SQL writers

- `src/learnloop/db/stores/pf.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_pf_reports.py`

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
CREATE TABLE pf_candidates (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  mint_request_id TEXT REFERENCES surface_mint_requests(id),
  round TEXT NOT NULL,
  tier TEXT,
  family_id TEXT NOT NULL,
  parent_item_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  generation_path TEXT NOT NULL
    CHECK (generation_path IN ('generator', 'ensemble', 'source_anchored', 'single_shot')),
  declared_relation TEXT NOT NULL
    CHECK (declared_relation IN ('same_target', 'isomorph', 'near', 'far')),
  final_relation TEXT
    CHECK (final_relation IS NULL OR final_relation IN ('same_target', 'isomorph', 'near', 'far')),
  proposer_model TEXT,
  prompt_version TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  verification TEXT NOT NULL DEFAULT 'unverified'
    CHECK (verification IN ('verified', 'unverified')),
  verification_check TEXT,
  status TEXT NOT NULL CHECK (status IN (
    'generated', 'rejected', 'survivor', 'selected', 'not_selected',
    'published', 'baseline')),
  rejection_filter TEXT,
  filters_json TEXT NOT NULL DEFAULT '{}',
  difficulty REAL CHECK (difficulty IS NULL OR (difficulty >= 0 AND difficulty <= 1)),
  difficulty_source TEXT CHECK (difficulty_source IS NULL OR difficulty_source = 'solver_panel'),
  panel_json TEXT,
  selection_json TEXT,
  cost_json TEXT NOT NULL DEFAULT '{}',
  -- The parent/family revisions and effective rubric the judges saw;
  -- publication revalidates them and refuses a stale selection.
  judged_inputs_json TEXT NOT NULL DEFAULT '{}',
  published_item_id TEXT,
  published_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  -- Publication requires a verified reference (P9).
  CHECK (status <> 'published' OR (verification = 'verified' AND published_item_id IS NOT NULL))
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

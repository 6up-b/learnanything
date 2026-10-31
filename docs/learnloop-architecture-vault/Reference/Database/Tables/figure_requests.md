---
title: "figure_requests"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "4267e5ab7ca7767b6b9189c144cd9294163536e7"
source_commit_timestamp: "2026-10-31T14:03:09-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite figure_requests"
  - "table figure_requests"
schema_head: 226
table_name: "figure_requests"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "224_figure_requests.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/224_figure_requests.sql"
  - "src/learnloop/db/stores/figures.py"
  - "src/learnloop/diagnosis/text_gaps/sources.py"
  - "src/learnloop/figure_admission.py"
  - "src/learnloop/figures/service.py"
  - "src/learnloop/reader/reader_report.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `figure_requests`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Queues a durable, retryable request for figure so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `prefetch_decision_id`, `figure_id`, `caller_kind`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/224_figure_requests.sql`.
- **Schema touched by:** `224_figure_requests.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `origin` | `TEXT` | yes | — | — | Stored value |
| `goal_text` | `TEXT` | no | — | — | Stored value |
| `goal_author` | `TEXT` | no | — | — | Stored value |
| `anchor_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `reading_at_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `host_ref_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `policy` | `TEXT` | yes | — | — | Stored value |
| `caller_kind` | `TEXT` | yes | — | — | Stored value |
| `policy_derived_from` | `TEXT` | no | — | — | Stored value |
| `grounding` | `TEXT` | yes | — | — | Stored value |
| `grounding_manifest_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `build_mode` | `TEXT` | yes | `'pressed'` | — | Stored value |
| `tiers_allowed_json` | `TEXT` | yes | `'["grammar"]'` | — | JSON-encoded structured payload |
| `prefetch_decision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `figure_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/interactive_figures\|interactive_figures.id]] | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `figure_id` → [[Reference/Database/Tables/interactive_figures|`interactive_figures.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_figure_requests_created` on `created_at`.
- `idx_figure_requests_figure` on `figure_id`.
- `sqlite_autoindex_figure_requests_1` on `id` (unique).

Database triggers:

- `figure_requests_figure_once` — schema-enforced lifecycle or immutability constraint.
- `figure_requests_no_delete` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/figures.py`
- `src/learnloop/diagnosis/text_gaps/sources.py`
- `src/learnloop/figure_admission.py`
- `src/learnloop/reader/reader_report.py`

### Direct SQL writers

- `src/learnloop/db/stores/figures.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_figure_requests_migration.py`
- `tests/test_figures_show_me.py`
- `tests/test_figures_show_me_codex_review.py`

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
CREATE TABLE figure_requests (
  id TEXT PRIMARY KEY,
  origin TEXT NOT NULL CHECK (origin IN ('selection', 'library', 'tutor', 'show_me', 'ask', 'teacher', 'prefetch')),
  goal_text TEXT,
  goal_author TEXT CHECK (goal_author IS NULL OR goal_author IN ('learner', 'tutor', 'teacher', 'prefetch')),
  anchor_json TEXT,
  reading_at_json TEXT,
  host_ref_json TEXT NOT NULL DEFAULT '{}',
  policy TEXT NOT NULL,
  caller_kind TEXT NOT NULL,
  policy_derived_from TEXT,
  grounding TEXT NOT NULL CHECK (grounding IN ('anchor', 'retrieved', 'none')),
  grounding_manifest_json TEXT NOT NULL DEFAULT '{}',
  build_mode TEXT NOT NULL DEFAULT 'pressed' CHECK (build_mode IN ('pressed', 'prefetch')),
  tiers_allowed_json TEXT NOT NULL DEFAULT '["grammar"]',
  prefetch_decision_id TEXT,
  figure_id TEXT REFERENCES interactive_figures(id),
  created_at TEXT NOT NULL,
  CHECK (goal_text IS NULL OR goal_author IS NOT NULL),
  CHECK (goal_text IS NOT NULL OR anchor_json IS NOT NULL)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

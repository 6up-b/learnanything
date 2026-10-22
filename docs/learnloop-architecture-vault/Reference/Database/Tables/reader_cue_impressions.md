---
title: "reader_cue_impressions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "55faad94d8888466c57a8bc083e6b766d4230234"
source_commit_timestamp: "2026-10-22T17:07:32-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite reader_cue_impressions"
  - "table reader_cue_impressions"
schema_head: 217
table_name: "reader_cue_impressions"
table_role: "receipt"
functionality_status: "active"
domain_family: "reader"
introduced_in: "215_reader_discovered_cues.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/215_reader_discovered_cues.sql"
  - "src/learnloop/db/stores/reader_cue_links.py"
  - "src/learnloop/reader/reader_report.py"
  - "src/learnloop_sidecar/handlers/reader_cue_discovery.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/reader"
---

# `reader_cue_impressions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives reader cue impression a stable database identity so reader interactions remain anchored to durable source content as extraction and rendering evolve. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `cue_id`, `link_id`, `extraction_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **reader** navigation family. The family context lives in [[Database Catalog#Reader]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/215_reader_discovered_cues.sql`.
- **Schema touched by:** `215_reader_discovered_cues.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `cue_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `link_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/passage_links\|passage_links.id]] | Stored value |
| `extraction_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `span_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `visit_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `shown` | `INTEGER` | yes | — | — | Stored value |
| `suppressed_reason` | `TEXT` | no | — | — | Stored value |
| `propensity` | `REAL` | no | — | — | Stored value |
| `seed` | `TEXT` | no | — | — | Stored value |
| `p_open` | `REAL` | no | — | — | Stored value |
| `p_open_source` | `TEXT` | no | — | — | Stored value |
| `density` | `TEXT` | yes | — | — | Stored value |
| `response` | `TEXT` | yes | `'none'` | — | Stored value |
| `response_text_hash` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `responded_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `link_id` → [[Reference/Database/Tables/passage_links|`passage_links.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_reader_cue_impressions_created` on `extraction_id`, `created_at`.
- `idx_reader_cue_impressions_link` on `link_id`.
- `sqlite_autoindex_reader_cue_impressions_2` on `visit_id`, `cue_id` (unique).
- `sqlite_autoindex_reader_cue_impressions_1` on `id` (unique).

Database triggers:

- `reader_cue_impressions_no_delete` — schema-enforced lifecycle or immutability constraint.
- `reader_cue_impressions_response_once` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/reader_cue_links.py`
- `src/learnloop/reader/reader_report.py`

### Direct SQL writers

- `src/learnloop/db/stores/reader_cue_links.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_architecture.py`
- `tests/test_reader_cues_cli_report.py`
- `tests/test_reader_rw3b_migration.py`
- `tests/test_reader_rw3b_protection.py`
- `tests/test_reader_rw3b_review_fixes.py`
- `tests/test_salience_firewall.py`

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
CREATE TABLE reader_cue_impressions (
  id TEXT PRIMARY KEY,
  cue_id TEXT NOT NULL,
  link_id TEXT REFERENCES passage_links(id),
  extraction_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  -- The learning object the cue is about: the holdout's estimate reads the
  -- next attempt on it (shown vs held out, weighted by the propensity).
  learning_object_id TEXT,
  kind TEXT NOT NULL CHECK (kind IN ('revisit', 'distinction', 'application', 'prerequisite', 'try_first')),
  visit_id TEXT NOT NULL,
  shown INTEGER NOT NULL CHECK (shown IN (0, 1)),
  suppressed_reason TEXT CHECK (suppressed_reason IS NULL OR suppressed_reason IN (
    'holdout', 'density', 'spacing', 'restored_line'
  )),
  -- The probability of the arm the holdout drew (shown: 1 - rate; held out:
  -- rate); null for a Guide cue, which is never drawn.
  propensity REAL CHECK (propensity IS NULL OR (propensity > 0 AND propensity <= 1)),
  seed TEXT,
  p_open REAL CHECK (p_open IS NULL OR (p_open >= 0 AND p_open <= 1)),
  p_open_source TEXT,
  density TEXT NOT NULL CHECK (density IN ('off', 'fewer', 'normal', 'more')),
  response TEXT NOT NULL DEFAULT 'none' CHECK (response IN (
    'opened', 'check_me', 'try_first', 'not_relevant', 'fewer', 'none'
  )),
  response_text_hash TEXT,
  created_at TEXT NOT NULL,
  responded_at TEXT,
  CHECK ((shown = 1) = (suppressed_reason IS NULL)),
  CHECK ((suppressed_reason = 'holdout') <= (link_id IS NOT NULL)),
  CHECK ((response = 'none') = (responded_at IS NULL)),
  UNIQUE (visit_id, cue_id)
);
```

## Related notes

- [[Database Catalog#Reader|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

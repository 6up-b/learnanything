---
title: "router_suggestion_responses"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "a21f088b16f700d0b88634b19f64720fc58016ff"
source_commit_timestamp: "2026-11-06T03:32:49-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite router_suggestion_responses"
  - "table router_suggestion_responses"
schema_head: 248
table_name: "router_suggestion_responses"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "236_router_lesson_suggestions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/236_router_lesson_suggestions.sql"
  - "src/learnloop/algorithm_versions.py"
  - "src/learnloop/config/template.py"
  - "src/learnloop/daily_plan/lesson_suggestion.py"
  - "src/learnloop/db/stores/router_suggestions.py"
  - "src/learnloop/lesson_suggestions_upgrade.py"
  - "src/learnloop/router/lesson_suggestions.py"
  - "src/learnloop/router/outcomes.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `router_suggestion_responses`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Appends the learner's one response to a shown lesson suggestion (teacher TE1b, spec_teacher_v1 §15.1): accepted (Start), chose_alternative (one of the card's alternatives), declined ("Not now") or ignored (unanswered by the end of its day), the candidate and its learning objects, and the lesson id a Start reserved; and at most one release of a Start whose lesson never opened (released: "Not now" on the pending card; expired: it can no longer open on the current vault; landing ruling R2), nothing deleted. The acceptance model and the decline recovery replay it on every read (no derived table). It supplies replay-stable input rather than a disposable cache. Rows bind `decision_id`, `lesson_id`, `session_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/236_router_lesson_suggestions.sql`.
- **Schema touched by:** `236_router_lesson_suggestions.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `decision_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/router_decisions\|router_decisions.id]] | Stored value |
| `response` | `TEXT` | yes | — | — | Stored value |
| `candidate_ref` | `TEXT` | yes | — | — | Stored value |
| `learning_object_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `lesson_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `responded_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `detail_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `decision_id` → [[Reference/Database/Tables/router_decisions|`router_decisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_router_suggestion_responses_one_release` on `decision_id` (unique).
- `idx_router_suggestion_responses_one_response` on `decision_id` (unique).
- `idx_router_suggestion_responses_at` on `responded_at`.
- `sqlite_autoindex_router_suggestion_responses_1` on `id` (unique).

Database triggers:

- `router_suggestion_responses_no_delete` — schema-enforced lifecycle or immutability constraint.
- `router_suggestion_responses_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/router_suggestions.py`
- `src/learnloop/router/outcomes.py`

### Direct SQL writers

- `src/learnloop/db/stores/router_suggestions.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_followups_batch6_te1b_card.py`
- `tests/test_teacher_te1b_landing_r2.py`
- `tests/test_teacher_te1b_migration.py`
- `tests/test_teacher_te1b_suggestions.py`

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
CREATE TABLE router_suggestion_responses (
  id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL REFERENCES router_decisions(id),
  response TEXT NOT NULL CHECK (
    response IN ('accepted', 'chose_alternative', 'declined', 'ignored', 'released', 'expired')
  ),
  -- The candidate the response is about: the card's suggestion (accepted,
  -- declined, ignored) or the alternative the learner picked.
  candidate_ref TEXT NOT NULL,
  learning_object_ids_json TEXT NOT NULL,
  -- The lesson id a Start reserved (accepted or chose_alternative); a
  -- release names the reservation's lesson id in detail_json.
  lesson_id TEXT,
  session_id TEXT,
  responded_at TEXT NOT NULL,
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  CHECK (lesson_id IS NULL OR response IN ('accepted', 'chose_alternative'))
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

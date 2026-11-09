---
title: "router_learner_preferences"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "85131fc655b46e81b93e56ad2675a957e2448838"
source_commit_timestamp: "2026-11-09T05:06:18-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite router_learner_preferences"
  - "table router_learner_preferences"
schema_head: 251
table_name: "router_learner_preferences"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "251_router_learner_preferences.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/251_router_learner_preferences.sql"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/db/stores/router.py"
  - "src/learnloop/router/lesson_suggestions.py"
  - "src/learnloop/router_objective/preferences.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `router_learner_preferences`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives router learner preference a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It supplies replay-stable input rather than a disposable cache. Rows bind `decision_id`, `attempt_id`, `session_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/251_router_learner_preferences.sql`.
- **Schema touched by:** `251_router_learner_preferences.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `decision_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/router_decisions\|router_decisions.id]] | Stored value |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `surface` | `TEXT` | yes | — | — | Stored value |
| `offered_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `chosen_kind` | `TEXT` | yes | — | — | Stored value |
| `chosen_ref` | `TEXT` | yes | — | — | Stored value |
| `note_md` | `TEXT` | no | — | — | Stored value |
| `served_decision_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/router_decisions\|router_decisions.id]] | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `served_decision_id` → [[Reference/Database/Tables/router_decisions|`router_decisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `decision_id` → [[Reference/Database/Tables/router_decisions|`router_decisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `router_learner_preferences_served` on `served_decision_id`.
- `router_learner_preferences_session` on `session_id`, `created_at`, `id`.
- `router_learner_preferences_decision` on `decision_id`.
- `sqlite_autoindex_router_learner_preferences_1` on `id` (unique).

Database triggers:

- `router_learner_preferences_no_delete` — schema-enforced lifecycle or immutability constraint.
- `router_learner_preferences_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/router.py`
- `src/learnloop/router_objective/preferences.py`

### Direct SQL writers

- `src/learnloop/db/stores/router.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ih3_learner_preferences.py`
- `tests/test_ih3_migration.py`
- `tests/test_ih4_preferences_inform_router.py`

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
CREATE TABLE router_learner_preferences (
  id TEXT PRIMARY KEY,
  decision_id TEXT REFERENCES router_decisions(id),
  attempt_id TEXT,
  session_id TEXT,
  -- Where the link was used: feedback | offer_page | today, with the phone's prefixed (phone_feedback, phone_today).
  surface TEXT NOT NULL,
  offered_json TEXT NOT NULL CHECK (json_valid(offered_json)),
  chosen_kind TEXT NOT NULL,
  chosen_ref TEXT NOT NULL,
  note_md TEXT,
  served_decision_id TEXT REFERENCES router_decisions(id),
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

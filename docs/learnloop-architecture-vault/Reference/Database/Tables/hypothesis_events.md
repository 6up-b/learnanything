---
title: "hypothesis_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite hypothesis_events"
  - "table hypothesis_events"
schema_head: 156
table_name: "hypothesis_events"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "055_hypothesis_events.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/055_hypothesis_events.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/scoreboard.py"
  - "src/learnloop/learner/surfaced_beliefs.py"
  - "src/learnloop/learner/hypothesis_claims.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `hypothesis_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of hypothesis so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `presentation_id`, `session_id`, `visit_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Typed learner-facing claim presentations and raw response telemetry. Presentation rows are append-only; response/dismissal rows point back to the exact presentation whose rendered value the learner saw.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/055_hypothesis_events.sql`.
- **Schema touched by:** `055_hypothesis_events.sql`, `132_surfaced_belief_corrections.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `presentation_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/hypothesis_events\|hypothesis_events.id]] | Stored value |
| `event_type` | `TEXT` | yes | — | — | Stored value |
| `claim_class` | `TEXT` | yes | — | — | Stored value |
| `claim_type` | `TEXT` | yes | — | — | Stored value |
| `claim_ref` | `TEXT` | yes | — | — | Stored value |
| `claim_version` | `TEXT` | yes | — | — | Stored value |
| `producer_version` | `TEXT` | yes | — | — | Stored value |
| `surface` | `TEXT` | yes | — | — | Stored value |
| `temperature` | `TEXT` | yes | — | — | Stored value |
| `visible_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `suppression_reason` | `TEXT` | no | — | — | Stored value |
| `response_payload_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `visit_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `surfaced_to_learner` | `INTEGER` | yes | `0` | — | Stored value |
| `claim_text_as_shown` | `TEXT` | no | — | — | Stored value |
| `belief_kind` | `TEXT` | no | — | — | Stored value |
| `belief_id` | `TEXT` | no | — | — | Application-validated soft reference |

## Relationships and access paths

Declared SQLite foreign keys:

- `presentation_id` → [[Reference/Database/Tables/hypothesis_events|`hypothesis_events.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_hypothesis_events_surfaced_belief` on `belief_kind`, `belief_id`, `created_at`, `id`.
- `idx_hypothesis_events_visit` on `visit_id`, `event_type`, `created_at`.
- `idx_hypothesis_events_session` on `session_id`, `event_type`, `created_at`.
- `idx_hypothesis_events_claim` on `claim_ref`, `claim_version`, `surface`, `created_at`.
- `idx_hypothesis_events_presentation` on `presentation_id`, `created_at`.
- `sqlite_autoindex_hypothesis_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.cold_hypothesis_count_for_visit()`
- `Repository.find_hypothesis_presentation()`
- `Repository.hypothesis_event()`
- `Repository.insert_hypothesis_event()`
- `Repository.last_hypothesis_response_at()`
- `Repository.list_hypothesis_events()`
- `Repository.mark_hypothesis_visible()`
- `Repository.purge_hypothesis_events()`
- `Repository.record_surfaced_belief_presentation()`
- `Repository.soliciting_hypothesis_count()`
- `Repository.surfaced_belief_withdrawals()`
- `Repository.surfaced_beliefs()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/scoreboard.py`
- `src/learnloop/learner/hypothesis_claims.py`
- `src/learnloop/learner/surfaced_beliefs.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_common_repair_delivery.py`
- `tests/test_hypothesis_claim_dispatcher.py`
- `tests/test_surfaced_belief_corrections.py`

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
CREATE TABLE hypothesis_events (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  presentation_id TEXT REFERENCES hypothesis_events(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL CHECK (event_type IN ('presented', 'responded', 'dismissed')),
  claim_class TEXT NOT NULL CHECK (claim_class IN ('estimate', 'diagnosis', 'policy', 'ledger_fact')),
  claim_type TEXT NOT NULL,
  claim_ref TEXT NOT NULL,
  claim_version TEXT NOT NULL,
  producer_version TEXT NOT NULL,
  surface TEXT NOT NULL,
  temperature TEXT NOT NULL CHECK (temperature IN ('hot', 'cold')),
  visible_at TEXT,
  suppression_reason TEXT,
  response_payload_json TEXT,
  session_id TEXT,
  visit_id TEXT, surfaced_to_learner INTEGER NOT NULL DEFAULT 0, claim_text_as_shown TEXT, belief_kind TEXT, belief_id TEXT,
  CHECK (
    (event_type = 'presented' AND presentation_id IS NULL)
    OR (event_type IN ('responded', 'dismissed') AND presentation_id IS NOT NULL)
  ),
  CHECK (event_type = 'responded' OR response_payload_json IS NULL)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

---
title: "activity_family_membership_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "b9fcaf1212bd14cc71ad07193b427043d618cecf"
source_commit_timestamp: "2026-10-15T05:55:23-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite activity_family_membership_events"
  - "table activity_family_membership_events"
schema_head: 203
table_name: "activity_family_membership_events"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "168_activity_family_membership.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/168_activity_family_membership.sql"
  - "src/learnloop/db/stores/families.py"
  - "src/learnloop/substrate/families.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `activity_family_membership_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of activity family membership so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `family_id`, `card_id`, `practice_item_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/168_activity_family_membership.sql`.
- **Schema touched by:** `168_activity_family_membership.sql`, `175_decider_judgments_and_receipt_labels.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `seq` | `INTEGER` | no | — | PRIMARY KEY | Stored value |
| `id` | `TEXT` | yes | — | — | Stored value |
| `family_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_families\|activity_families.id]] | Stored value |
| `card_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_cards\|activity_cards.id]] | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `variant_relation` | `TEXT` | yes | — | — | Stored value |
| `action` | `TEXT` | yes | — | — | Stored value |
| `proposal_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `judgment_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/judgment_ledger\|judgment_ledger.id]] | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `judgment_id` → [[Reference/Database/Tables/judgment_ledger|`judgment_ledger.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `card_id` → [[Reference/Database/Tables/activity_cards|`activity_cards.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `family_id` → [[Reference/Database/Tables/activity_families|`activity_families.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_family_membership_card` on `card_id`, `seq`.
- `sqlite_autoindex_activity_family_membership_events_2` on `proposal_id`, `card_id`, `action` (unique).
- `sqlite_autoindex_activity_family_membership_events_1` on `id` (unique).

Database triggers:

- `family_membership_no_delete` — schema-enforced lifecycle or immutability constraint.
- `family_membership_no_replace` — schema-enforced lifecycle or immutability constraint.
- `family_membership_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/families.py`
- `src/learnloop/substrate/families.py`

### Direct SQL writers

- `src/learnloop/db/stores/families.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_activity_families.py`
- `tests/test_attach_to_family.py`
- `tests/test_family_proposals.py`
- `tests/test_judge_routes.py`
- `tests/test_pf_generation.py`

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
CREATE TABLE activity_family_membership_events (
  -- Deletion is forbidden, so ordinary rowid allocation is monotone without
  -- introducing sqlite_sequence into every formerly unchanged no-family vault.
  seq INTEGER PRIMARY KEY,
  id TEXT NOT NULL UNIQUE,
  family_id TEXT NOT NULL REFERENCES activity_families(id),
  card_id TEXT NOT NULL REFERENCES activity_cards(id),
  practice_item_id TEXT NOT NULL,
  variant_relation TEXT NOT NULL CHECK(variant_relation IN ('same_target','isomorph','near','far')),
  action TEXT NOT NULL CHECK(action IN ('add','remove')),
  proposal_id TEXT NOT NULL,
  judgment_id TEXT NOT NULL REFERENCES judgment_ledger(id),
  created_at TEXT NOT NULL,
  UNIQUE(proposal_id,card_id,action)
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

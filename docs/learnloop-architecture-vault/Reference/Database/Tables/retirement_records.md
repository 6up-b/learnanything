---
title: "retirement_records"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite retirement_records"
  - "table retirement_records"
schema_head: 156
table_name: "retirement_records"
table_role: "receipt"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "065_activity_lineage_substrate.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/065_activity_lineage_substrate.sql"
  - "src/learnloop/cli/surfaces.py"
  - "src/learnloop/content/authoring/item_authoring.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/substrate/activities.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `retirement_records`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives retirement record a stable database identity so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `family_id`, `card_version_id`, `surface_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- Retirement records (§3.7): richer than the bare 'retire' lifecycle event. reason is drawn from the fixed umbrella-L0 taxonomy; provenance names the signal source; replacement_proposal_json is a non-binding successor hook. ----------------------------------------------------------------------------

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/065_activity_lineage_substrate.sql`.
- **Schema touched by:** `065_activity_lineage_substrate.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `scope` | `TEXT` | yes | — | — | Stored value |
| `family_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_families\|activity_families.id]] | Stored value |
| `card_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_card_versions\|activity_card_versions.id]] | Stored value |
| `surface_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_surfaces\|activity_surfaces.id]] | Stored value |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `provenance` | `TEXT` | yes | — | — | Stored value |
| `replacement_proposal_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `lifecycle_event_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_surface_lifecycle_events\|activity_surface_lifecycle_events.id]] | Stored value |
| `interaction_event_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/interaction_events\|interaction_events.id]] | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `interaction_event_id` → [[Reference/Database/Tables/interaction_events|`interaction_events.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `lifecycle_event_id` → [[Reference/Database/Tables/activity_surface_lifecycle_events|`activity_surface_lifecycle_events.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `surface_id` → [[Reference/Database/Tables/activity_surfaces|`activity_surfaces.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `card_version_id` → [[Reference/Database/Tables/activity_card_versions|`activity_card_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `family_id` → [[Reference/Database/Tables/activity_families|`activity_families.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_retirement_records_surface` on `surface_id`.
- `idx_retirement_records_family` on `family_id`.
- `sqlite_autoindex_retirement_records_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.insert_retirement_record()`
- `Repository.retirement_records_for_card_version()`
- `Repository.retirement_records_for_surface()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/substrate/activities.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_activity_substrate.py`
- `tests/test_grading_cli.py`

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
CREATE TABLE retirement_records (
  id TEXT PRIMARY KEY,
  scope TEXT NOT NULL CHECK (scope IN ('family', 'card', 'surface')),
  family_id TEXT REFERENCES activity_families(id),
  card_version_id TEXT REFERENCES activity_card_versions(id),
  surface_id TEXT REFERENCES activity_surfaces(id),
  reason TEXT NOT NULL CHECK (reason IN (
    'too_easy', 'ambiguous', 'missing_context', 'duplicate_surface',
    'wrong_granularity', 'no_longer_relevant', 'bad_underlying_explanation',
    'superseded_by_better_activity', 'should_be_reference_not_memorized',
    'dont_care_enough_to_retain', 'knew_prompt_not_concept'
  )),
  provenance TEXT NOT NULL
    CHECK (provenance IN ('learner_action', 'affect_signal_escalation', 'owner_tooling')),
  replacement_proposal_json TEXT,
  lifecycle_event_id TEXT REFERENCES activity_surface_lifecycle_events(id),
  interaction_event_id TEXT REFERENCES interaction_events(id),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

---
title: "ad_reading_opportunities"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "5e7822bbd91a4aa92ab55de75978d433456c186e"
source_commit_timestamp: "2026-10-23T15:27:59-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite ad_reading_opportunities"
  - "table ad_reading_opportunities"
schema_head: 217
table_name: "ad_reading_opportunities"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "213_adaptive_difficulty_receipts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/213_adaptive_difficulty_receipts.sql"
  - "src/learnloop/adaptive_difficulty/data_check.py"
  - "src/learnloop/adaptive_difficulty/reading.py"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/db/stores/ad_receipts.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `ad_reading_opportunities`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records the denominator of available opportunities for ad reading so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `source_id`, `learning_object_id`, `dose_offer_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §5.11 (D20, D22): reading and other learning opportunities, frozen in a receipt. One row per (opportunity, LO), of one of four kinds, from the listed sources only, with the facets and doses the mapping resolved at the sweep; plus one verdict row per judged in-passage question (subkind `self_check:matched` / `self_check:missed`, from the question's first judgment_ledger verdict). No magnitude field exists: no dwell, scroll, highlight, skip, visibility, active time or answer value. Authority class `salience_only`: nothing reads these rows until the AD2+AD3 stage adds the reading-signal firewall's carve-out, and they never pass the evidence chokepoint. A source row deleted later (its extraction removed) leaves its receipts.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/213_adaptive_difficulty_receipts.sql`.
- **Schema touched by:** `213_adaptive_difficulty_receipts.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `opportunity_key` | `TEXT` | yes | — | — | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `subkind` | `TEXT` | yes | — | — | Stored value |
| `source_table` | `TEXT` | yes | — | — | Stored value |
| `source_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `source_written_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `facet_doses_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `dose_offer_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `mapping_version` | `TEXT` | yes | — | — | Stored value |
| `authority_class` | `TEXT` | yes | `'salience_only'` | — | Stored value |
| `sweep` | `TEXT` | yes | — | — | Stored value |
| `sweep_ref` | `TEXT` | no | — | — | Stored value |
| `swept_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_ad_reading_opportunities_written` on `source_written_at`, `id`.
- `idx_ad_reading_opportunities_lo` on `learning_object_id`, `source_written_at`.
- `sqlite_autoindex_ad_reading_opportunities_3` on `kind`, `subkind`, `source_table`, `source_id`, `learning_object_id` (unique).
- `sqlite_autoindex_ad_reading_opportunities_2` on `opportunity_key` (unique).
- `sqlite_autoindex_ad_reading_opportunities_1` on `id` (unique).

Database triggers:

- `ad_reading_opportunities_no_delete` — schema-enforced lifecycle or immutability constraint.
- `ad_reading_opportunities_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/adaptive_difficulty/data_check.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/ad_fakes.py`
- `tests/test_ad1_codex_review_fixes.py`
- `tests/test_ad1_migration.py`
- `tests/test_ad1_reading_opportunities.py`
- `tests/test_adaptive_difficulty_ad1.py`
- `tests/test_architecture.py`
- `tests/test_figure_predictions.py`

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
CREATE TABLE ad_reading_opportunities (
  id TEXT PRIMARY KEY,
  -- The opportunity's identity inside its cap (a section once per section and
  -- LO; passage views one per LO per day; tutor exchanges three per LO per day;
  -- a worked example once; a question once; a verdict once per question).
  opportunity_key TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL
    CHECK (kind IN ('reading', 'reader_tutor_exchange', 'worked_example', 'in_passage_question')),
  subkind TEXT NOT NULL,
  source_table TEXT NOT NULL,
  source_id TEXT NOT NULL,
  -- The source row's write time: replay orders opportunities by it.
  source_written_at TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  -- {facet id: dose in [0, 1]}, as resolved at the sweep.
  facet_doses_json TEXT NOT NULL,
  -- ad_dose_offers.id when a randomized offer produced it (AD2+AD3; null here).
  dose_offer_id TEXT,
  mapping_version TEXT NOT NULL,
  authority_class TEXT NOT NULL DEFAULT 'salience_only' CHECK (authority_class = 'salience_only'),
  -- Which sweep recorded it: a serve's (in its transaction, before its
  -- forecasts) or the one-time history backfill.
  sweep TEXT NOT NULL CHECK (sweep IN ('serve', 'backfill')),
  sweep_ref TEXT,
  swept_at TEXT NOT NULL,
  UNIQUE (kind, subkind, source_table, source_id, learning_object_id)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

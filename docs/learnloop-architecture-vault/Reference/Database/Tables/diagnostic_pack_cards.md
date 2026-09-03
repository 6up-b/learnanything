---
title: "diagnostic_pack_cards"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite diagnostic_pack_cards"
  - "table diagnostic_pack_cards"
schema_head: 157
table_name: "diagnostic_pack_cards"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "083_diagnostic_pack_and_triage.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/083_diagnostic_pack_and_triage.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/diagnostic_pack.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `diagnostic_pack_cards`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives diagnostic pack card a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `pack_id`, `admission_status`, `content_hash`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Pack cards: reviewed diagnostic-purpose P1 cards, each declaring the target distribution cell(s) it covers (§3.3). `admission_status` is the U-028 owner gate -- nothing serves as an instrument until 'admitted'.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/083_diagnostic_pack_and_triage.sql`.
- **Schema touched by:** `083_diagnostic_pack_and_triage.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `pack_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/diagnostic_packs\|diagnostic_packs.id]] | Stored value |
| `card_slug` | `TEXT` | yes | — | — | Stored value |
| `purpose` | `TEXT` | yes | `'diagnostic'` | — | Stored value |
| `coverage_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `instrument_ref` | `TEXT` | no | — | — | Stored value |
| `admission_status` | `TEXT` | yes | `'candidate'` | — | Stored value |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `pack_id` → [[Reference/Database/Tables/diagnostic_packs|`diagnostic_packs.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_diag_pack_cards_pack` on `pack_id`.
- `sqlite_autoindex_diagnostic_pack_cards_2` on `pack_id`, `card_slug` (unique).
- `sqlite_autoindex_diagnostic_pack_cards_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.diagnostic_pack_cards_for()`
- `Repository.register_diagnostic_pack_card()`
- `Repository.set_diagnostic_pack_card_admission()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/diagnostic_pack.py`

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
CREATE TABLE diagnostic_pack_cards (
  id TEXT PRIMARY KEY,
  pack_id TEXT NOT NULL REFERENCES diagnostic_packs(id) ON DELETE CASCADE,
  card_slug TEXT NOT NULL,
  purpose TEXT NOT NULL DEFAULT 'diagnostic'
    CHECK (purpose = 'diagnostic'),
  coverage_json TEXT NOT NULL,
  instrument_ref TEXT,
  admission_status TEXT NOT NULL DEFAULT 'candidate'
    CHECK (admission_status IN ('candidate', 'admitted', 'rejected')),
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(pack_id, card_slug)
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

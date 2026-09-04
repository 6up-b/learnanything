---
title: "probe_item_family_links"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite probe_item_family_links"
  - "table probe_item_family_links"
schema_head: 157
table_name: "probe_item_family_links"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "028_probe_episodes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/028_probe_episodes.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
  - "src/learnloop/diagnosis/causal_probe_coherence.py"
  - "src/learnloop/diagnosis/probe_episodes.py"
  - "src/learnloop/diagnosis/probe_instance_generation.py"
  - "src/learnloop/diagnosis/probe_lifecycle.py"
  - "src/learnloop/diagnosis/probe_coverage.py"
  - "src/learnloop/diagnosis/probe_dialogue.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `probe_item_family_links`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves explicit relationship edges for probe item family so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `practice_item_id`, `instrument_card_id`, `generator_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/028_probe_episodes.sql`.
- **Schema touched by:** `028_probe_episodes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `practice_item_id` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `instrument_card_id` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `instrument_card_version` | `INTEGER` | yes | — | PRIMARY KEY | Stored value |
| `generator_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `generator_version` | `TEXT` | no | — | — | Stored value |
| `generation_seed` | `TEXT` | no | — | — | Stored value |
| `instance_metadata_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_probe_item_family_links_1` on `practice_item_id`, `instrument_card_id`, `instrument_card_version` (unique).

## Who calls it

### Repository access surface

- `Repository.link_probe_item_family()`
- `Repository.probe_instance_ids_with_review_status()`
- `Repository.probe_item_family_links()`
- `Repository.probe_items_for_card()`
- `Repository.update_probe_item_family_metadata()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/causal_probe_coherence.py`
- `src/learnloop/diagnosis/probe_coverage.py`
- `src/learnloop/diagnosis/probe_dialogue.py`
- `src/learnloop/diagnosis/probe_episodes.py`
- `src/learnloop/diagnosis/probe_instance_generation.py`
- `src/learnloop/diagnosis/probe_lifecycle.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_probe_dialogue.py`
- `tests/test_probe_instance_generation.py`
- `tests/test_probe_lifecycle.py`
- `tests/test_probe_llm_instances.py`
- `tests/test_probe_surface_mint.py`
- `tests/helpers.py`
- `tests/test_p2_acceptance.py`
- `tests/test_p2_leakage_suite.py`
- `tests/test_probe_longform_families.py`

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
CREATE TABLE probe_item_family_links (
  practice_item_id TEXT NOT NULL,
  instrument_card_id TEXT NOT NULL,
  instrument_card_version INTEGER NOT NULL,
  generator_id TEXT,
  generator_version TEXT,
  generation_seed TEXT,
  instance_metadata_json TEXT,
  created_at TEXT NOT NULL,
  PRIMARY KEY (practice_item_id, instrument_card_id, instrument_card_version)
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

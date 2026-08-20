---
title: "persona_realism_runs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite persona_realism_runs"
  - "table persona_realism_runs"
schema_head: 156
table_name: "persona_realism_runs"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "144_diagnostic_augmentation.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/144_diagnostic_augmentation.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/authoring/persona_gate.py"
  - "src/learnloop/content/authoring/persona_realism.py"
  - "src/learnloop/diagnosis/diagnostic_augmentation.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `persona_realism_runs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Tracks one execution, input identity, and result for persona realism so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `matcher_version`, `corpus_hash`, `persona_corpus_hash`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Diagnostic augmentation Stage 7 (spec_diagnostic_augmentation_v1.md §§3-4).  Synthetic traces are evaluation artifacts, never learner attempts.  Keeping them in dedicated append-only tables makes the non-interference guarantee structural: no foreign key or write path reaches practice_attempts, error_events, grading_evidence, or a learner-state projection.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/144_diagnostic_augmentation.sql`.
- **Schema touched by:** `144_diagnostic_augmentation.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `matcher_version` | `TEXT` | yes | — | — | Stored value |
| `corpus_hash` | `TEXT` | yes | — | — | Stored value |
| `persona_corpus_hash` | `TEXT` | yes | — | — | Stored value |
| `real_corpus_hash` | `TEXT` | yes | — | — | Stored value |
| `persona_source` | `TEXT` | yes | — | — | Stored value |
| `generator_provider` | `TEXT` | no | — | — | Stored value |
| `generator_model` | `TEXT` | no | — | — | Stored value |
| `generator_family` | `TEXT` | no | — | — | Stored value |
| `persona_count` | `INTEGER` | yes | — | — | Stored value |
| `real_count` | `INTEGER` | yes | — | — | Stored value |
| `folds` | `INTEGER` | yes | — | — | Stored value |
| `matcher_correct` | `INTEGER` | yes | — | — | Stored value |
| `matcher_total` | `INTEGER` | yes | — | — | Stored value |
| `balanced_accuracy` | `REAL` | no | — | — | Stored value |
| `separation_threshold` | `REAL` | yes | — | — | Stored value |
| `verdict` | `TEXT` | yes | — | — | Stored value |
| `feature_manifest_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_persona_realism_family_created` on `generator_family`, `created_at`, `id`.
- `sqlite_autoindex_persona_realism_runs_1` on `id` (unique).

Database triggers:

- `persona_realism_runs_no_delete` — schema-enforced lifecycle or immutability constraint.
- `persona_realism_runs_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.insert_persona_realism_run()`
- `Repository.persona_realism_run_rows()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/authoring/persona_gate.py`
- `src/learnloop/content/authoring/persona_realism.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/diagnostic_augmentation.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_diagnostic_augmentation.py`
- `tests/test_persona_gate.py`

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
CREATE TABLE persona_realism_runs (
  id TEXT PRIMARY KEY,
  matcher_version TEXT NOT NULL,
  corpus_hash TEXT NOT NULL,
  persona_corpus_hash TEXT NOT NULL,
  real_corpus_hash TEXT NOT NULL,
  persona_source TEXT NOT NULL,
  generator_provider TEXT,
  generator_model TEXT,
  generator_family TEXT,
  persona_count INTEGER NOT NULL CHECK (persona_count >= 0),
  real_count INTEGER NOT NULL CHECK (real_count >= 0),
  folds INTEGER NOT NULL CHECK (folds >= 0),
  matcher_correct INTEGER NOT NULL CHECK (matcher_correct >= 0),
  matcher_total INTEGER NOT NULL CHECK (matcher_total >= 0),
  balanced_accuracy REAL,
  separation_threshold REAL NOT NULL
    CHECK (separation_threshold >= 0.5 AND separation_threshold <= 1.0),
  verdict TEXT NOT NULL CHECK (verdict IN (
    'indistinguishable', 'separable', 'insufficient_data'
  )),
  feature_manifest_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (
    (verdict = 'insufficient_data' AND balanced_accuracy IS NULL)
    OR
    (verdict != 'insufficient_data'
      AND balanced_accuracy >= 0.0 AND balanced_accuracy <= 1.0)
  )
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

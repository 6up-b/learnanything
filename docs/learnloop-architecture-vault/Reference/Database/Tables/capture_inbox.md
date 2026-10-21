---
title: "capture_inbox"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "4a54bff2446abc14f190bc13a997b80a58ed90a4"
source_commit_timestamp: "2026-10-20T20:47:05-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite capture_inbox"
  - "table capture_inbox"
schema_head: 216
table_name: "capture_inbox"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "171_mobile_capture.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/171_mobile_capture.sql"
  - "src/learnloop/capture/inbox.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `capture_inbox`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives capture inbox a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `client_capture_id`, `device_id`, `kind`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/171_mobile_capture.sql`.
- **Schema touched by:** `171_mobile_capture.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `client_capture_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `device_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/mobile_devices\|mobile_devices.id]] | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `text` | `TEXT` | no | — | — | Stored value |
| `url` | `TEXT` | no | — | — | Stored value |
| `note` | `TEXT` | no | — | — | Stored value |
| `media_sha256` | `TEXT` | no | — | — | Stored value |
| `media_mime` | `TEXT` | no | — | — | Stored value |
| `source_app` | `TEXT` | no | — | — | Stored value |
| `request_sha256` | `TEXT` | yes | — | — | Stored value |
| `captured_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `received_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `purged_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `device_id` → [[Reference/Database/Tables/mobile_devices|`mobile_devices.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `capture_inbox_media` on `media_sha256`.
- `capture_inbox_received` on `received_at`, `id`.
- `sqlite_autoindex_capture_inbox_2` on `client_capture_id` (unique).
- `sqlite_autoindex_capture_inbox_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/capture/inbox.py`

### Direct SQL writers

- `src/learnloop/capture/inbox.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_capture_domain.py`
- `tests/test_mobile_host_auth.py`
- `tests/test_mobile_host_coexistence.py`

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
CREATE TABLE capture_inbox (
    id TEXT PRIMARY KEY,
    client_capture_id TEXT NOT NULL UNIQUE,
    device_id TEXT REFERENCES mobile_devices(id),
    kind TEXT NOT NULL CHECK (kind IN ('text', 'url', 'image')),
    text TEXT,
    url TEXT,
    note TEXT,
    media_sha256 TEXT,
    media_mime TEXT,
    source_app TEXT,
    request_sha256 TEXT NOT NULL,
    captured_at TEXT,
    received_at TEXT NOT NULL,
    purged_at TEXT
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

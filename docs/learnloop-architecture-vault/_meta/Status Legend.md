---
title: Status Legend
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-18
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/db/table_roles.py
  - REFACTOR_PROPOSAL.md
tags:
  - learnloop/docs
  - learnloop/meta
  - learnloop/status
---

# Status Legend

## Documentation status

| Status | Meaning |
|---|---|
| `active` | reflects current executable behavior |
| `current` | generated/reference spelling for a note verified against the current tree |
| `generated` | current machine-derived reference; edit the generator/source, not repetitive fields |
| `compat` | maintained for old vaults but not extended |
| `dormant` | retained seam with no primary current workflow |
| `historical` | context only; not current authority |
| `proposed` | not yet executable behavior |
| `needs-owner-input` | blocked on an explicit product/data decision |

## Module/refactor status

- **ACTIVE** — called by a current adapter, domain workflow, startup/replay path, or test-defined supported behavior.
- **COMPAT** — deliberately frozen compatibility path, especially `substrate/compat`.
- **DORMANT** — retained but not exercised by the primary product path.
- **EVALUATION** — simulation/audit code that measures policy rather than serving learners directly.

## Table lifecycle role

The authoritative role registry is [[Database Catalog]] / `learnloop.db.table_roles`:

- `RAW_LEDGER` — authoritative authored/captured/observed input; never clear during rebuild.
- `DERIVED` — clearable and exactly reproducible from ledgers.
- `RECEIPT` — append-only decision/audit output; never rebuilt in place.
- `WORKFLOW` — mutable queue/session/lease lifecycle.
- `COMPAT` — frozen historical state.

> [!warning] “Derived-looking” is not `DERIVED`
> A cache-like table is classified as raw when it contains reviewed or otherwise non-reconstructible state. The registry encodes losslessness, not naming style.

## Table functionality status

Role answers how data behaves during rebuild; functionality status answers whether the product still uses the table:

- `active` — participates in a current persistence, audit, projection, or workflow contract;
- `active-historical-seam` — still used, but at an acknowledged predecessor/successor boundary;
- `dormant-owner-gated` — retained until production-vault telemetry and an owner decision permit retirement;
- `dormant-shadow` — retained only for decision-inert shadow/evaluation data;
- `legacy-preserved` — old-vault history remains readable, while new behavior uses another owner.

See [[Database Catalog#Role indexes]] to filter by role and [[Database Catalog#How to use this catalog]] to combine role with lifecycle status.

## Configuration-field status

- **ACTIVE** — canonical typed policy used by the refactored runtime;
- **DORMANT** — implemented but default-inert, shadow-only, or firewalled from live decisions;
- **COMPAT** — an accepted one-way legacy spelling or translation, never the runtime authority;
- **LEGACY** — still consumed only by a frozen historical path.

The exact 487-leaf inventory and status counts live in [[Configuration Field Catalog]].

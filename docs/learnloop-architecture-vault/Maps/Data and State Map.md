---
title: Data and State Map
aliases:
  - Persistence MOC
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-09-23
source_commit: 0622ea164f76ad7e1d62a00afda51473dbcd992e
source_commit_timestamp: "2026-09-23T13:06:55-04:00"
source_paths:
  - src/learnloop/db/table_roles.py
  - src/learnloop/substrate/rebuild_orchestrator.py
  - src/learnloop/vault
tags:
  - learnloop/persistence
  - moc
---

# Data and State Map

## Authority map

```mermaid
flowchart TD
    CFG[learnloop.toml<br/>policy and provider config]
    YAML[Markdown/YAML<br/>authored knowledge and goals]
    SRC[Source artifacts + immutable revisions]
    RAW[(Raw ledgers<br/>attempts, observations, authored/captured rows)]
    DER[(Derived state<br/>10 rebuild-owned tables)]
    REC[(Receipts<br/>audit and decisions)]
    WF[(Workflow state<br/>queues, sessions, leases)]
    YAML --> RAW
    SRC --> RAW
    CFG --> ALG[Versioned algorithms]
    RAW --> ALG
    ALG --> DER
    ALG --> REC
    WF --> ALG
    DER --> SELECT[Views, readiness, scheduling]
    SELECT --> RAW
```

Authored files and captured observations are authorities. Derived state can be destroyed and reconstructed; receipts and workflow state cannot. The selection loop creates a new observation rather than rewriting the old one.

^authority-map

## Navigate by concern

- [[Vault Lifecycle]] — filesystem creation/open modes and migrations.
- [[State and Persistence]] — transactions, roles, stores, replay, shadow rebuild.
- [[Database Catalog]] — one note per `state.sqlite` table.
- [[Configuration]] — every current `learnloop.toml` field and default.
- [[Evidence and Measurement]] — what an observation is licensed to mean.
- [[Algorithm Versions and Reproducibility]] — version bumps, fingerprints, upgrades.
- [[ADR-003 Explicit table roles govern rebuild]] — why naming is not enough.
- [[ADR-007 Immutable evidence and append-only correction]] — historical meaning.
- [[ADR-014 SQLite stays in DELETE journal mode]] — why the store keeps rollback journaling for now.
- [[Collection and Dataset Contract]] — offer provenance, labels, splits, and the dataset export.

## Status counts at migration head 164

| Role | Tables | Rebuild behavior |
|---|---:|---|
| RAW_LEDGER | 129 | preserved |
| DERIVED | 10 | clear + exact owner replay |
| RECEIPT | 54 | append-only |
| WORKFLOW | 56 | preserved mutable lifecycle |
| COMPAT | 10 | frozen |

See [[Database Catalog#Role indexes]] for the actual table lists.


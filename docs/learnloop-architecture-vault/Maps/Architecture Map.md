---
title: Architecture Map
aliases:
  - Architecture MOC
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - ARCHITECTURE.md
  - pyproject.toml
tags:
  - learnloop/architecture
  - moc
---

# Architecture Map

## Read top down

```mermaid
flowchart TB
    U[User / desktop UI / shell] --> A[Adapters<br/>CLI · TUI · sidecar]
    A --> APP[Application coordinators<br/>bootstrap · app_launch · migration coordinator]
    APP --> D[Domain packages<br/>attempts · learner · scheduling · goals · diagnosis<br/>curriculum · substrate · content · reader · tutor · ops · params]
    D --> I[Infrastructure<br/>config · vault · db · ingest · ai]
    I --> P[Primitives<br/>clock · ids · numeric · attempt_types]
    D -. feature-owned request contracts .-> AI[AI transport and routing]
    DB[(state.sqlite)] --- I
    FS[(Markdown / YAML / source artifacts)] --- I
```

The arrows show allowed dependency direction, not the temporal learning workflow. Adapters translate inputs; domains own behavior; infrastructure supplies persistence/provider mechanics; primitives remain dependency-free. See [[Package Boundaries#Enforced dependency rules]].

## Primary notes

- [[Architecture Overview]] — system shape and runtime composition.
- [[Package Boundaries]] — what belongs in each layer and what is forbidden.
- [[Adapter Architecture]] — CLI, TUI, sidecar, and neutral launch coordination.
- [[Desktop Architecture]] — React/Tauri layers and the typed bridge into the sidecar.
- [[AI Architecture]] — task routing and structured provider calls.
- [[State and Persistence]] — write ownership, roles, transactions, replay.
- [[Content Pipeline]] — acquisition through canonical map synthesis.
- [[Privacy and Trust Boundaries]] — local authority, provider/source egress, and validation gates.
- [[Vault Lifecycle]] — create, open, migrate, inspect, rebuild, upgrade.
- [[Testing and Invariants]] — executable architectural constraints.

## Package lookup

Use [[Module Catalog]] for Python modules and [[Desktop Module Catalog]] for TypeScript/TSX/Rust modules. Important package MOCs include `attempts`, `learner`, `scheduling`, `diagnosis`, `content`, `db`, `ai`, `learnloop_sidecar`, and the desktop screen/component/native-host areas.

## Why these boundaries exist

See [[Design Decision Index]], especially [[ADR-001 Domain ownership replaces generic services]], [[ADR-002 Feature-owned structured AI contracts]], and [[ADR-005 Independent adapters]].

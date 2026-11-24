---
title: Home
aliases:
  - LearnLoop Documentation Home
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
last_reviewed: 2026-11-23
source_commit: 86f29b0d390ed2ecdbb0347d98ccb1175ac52728
source_commit_timestamp: "2026-11-23T23:12:28-05:00"
source_paths:
  - docs/specs/ARCHITECTURE.md
  - README.md
tags:
  - learnloop/home
  - moc
---

# Home

LearnLoop is a local-first adaptive learning system. Authored knowledge lives in a vault; immutable observations record what happened; projections estimate what the learner can do; the scheduler ranks eligible items and Today's router can draw a block from a seeded policy mixture; optional AI performs bounded, schema-validated authoring and grading work.

For a spatial overview, open the [LearnLoop System canvas](Maps/LearnLoop%20System.canvas) in Obsidian.

> [!tip] Choose a route
> - **New user:** [[Initialize a Vault]] → [[Import Canonical Sources]] → [[Start a Learning Cycle]].
> - **Understand the product:** [[Learning System]] → [[Canonical Knowledge Model]] → [[Scheduling and Selection]].
> - **Understand the code:** [[Architecture Overview]] → [[Package Boundaries]] → [[Module Catalog]].
> - **Understand stored data:** [[Vault Lifecycle]] → [[State and Persistence]] → [[Database Catalog]].
> - **Change behavior safely:** [[Developer Map]] → [[Testing and Invariants]] → [[Algorithm Versions and Reproducibility]].

## Maps of content

| Map | Use it when… |
|---|---|
| [[Architecture Map]] | you need package boundaries, adapters, or dependency direction |
| [[LearnLoop Pipeline Map]] | you want the current end-to-end learning loop, stage diagrams, and source links |
| [[User Journey Map]] | you want an executable end-to-end path |
| [[Data and State Map]] | you need authority, table roles, migrations, replay, or rebuild |
| [[Developer Map]] | you need the correct modification point and test oracle |
| [[Module Catalog]] | you know a package/module name and want callers/dependencies/tests |
| [[Desktop Module Catalog]] | you know a TypeScript, TSX, or Rust desktop source file and want its role and edges |
| [[Database Catalog]] | you know a table name and want its function/status/owner |
| [[Design Decision Index]] | you want the reasoning behind a boundary or compatibility choice, such as [[ADR-015 SQLite runs in WAL mode with synchronous FULL]] |
| [[Documentation Dashboard]] | you want live status/version tracking and review queues |

## Core system notes

- [[Learning System]] — intent, feedback loop, belief layers, and safety boundaries.
- [[AI Architecture]] — routing, transports, feature contracts, manual mode, provenance.
- [[Concepts/Figures|Figures]] — Show me illustrations, simulations and explanation videos, protection, reuse and background builds.
- [[State and Persistence]] — SQLite roles, write authority, rebuild, shadow evaluation.
- [[Collection and Dataset Contract]] — offer provenance, collection versions, outcome labels, splits, adjudications, and the dataset export.
- [[Learner State and Projections]] — the measured, inferred, claimed, predictive, and memory views exposed from evidence.
- [[Content Pipeline]] — source acquisition, immutable revisions, IR, inventory, synthesis.
- [[Adapter Architecture]] — CLI, optional Textual TUI, and JSON-RPC sidecar.
- [[Desktop Architecture]] — React/Tauri composition, RPC bridge, process lifecycle, watcher, and desktop module map.
- [[Configuration]] — `learnloop.toml`, defaults, compatibility normalization.
- [[Parameter Governance and Evaluation]] — decision knobs, sensitivity, simulation, and promotion evidence.

## Reader workbench

- [[Concepts/Reader workbench|Reader workbench]] — desks, pad writes, the companion, the goal lens, ink, lessons, notebooks and video.
- [[Workbench protection]] — exam and held-out passage checks, due-check masking and its open gaps.
- [[Add a window kind to the workbench]] and [[Add a menu verb]] — change the desktop and sidecar together.
- [[Debug a workbench write]] — trace an edit from the outbox to its receipt and the saved heads.
- [[ADR-020 Keep notebook session files on the host]], [[ADR-021 Keep both conflicting pad edits]] and [[ADR-022 Scope polled jobs to vault and epoch]] — the workbench's runtime and write decisions.

## Lookup and vault maintenance

- [[Example Index]] — copyable new-user, learning, inspection, recovery, and provider sessions.
- [[Glossary]] — canonical terminology without duplicating the concept notes.
- [[Version Registry]] — package, algorithm, config, schema, and documentation version axes.
- [[Tag Taxonomy]] — the tag families used by the sidebar, graph, and searches.
- [[Documentation Conventions]] — authority, metadata, link, callout, and freshness rules.

## Refactor status

The generic `learnloop.services` and provider-specific `learnloop.codex` namespaces are gone. Behavior is owned by domain packages, adapters are independent, AI contracts live with features, and architecture is enforced by import and AST tests. See [[Refactor Status]] and [[ADR-001 Domain ownership replaces generic services]].

> [!warning] Production-vault telemetry gate
> Table retirement needs an explicit decision and a migration that protects existing data. The first approved group was removed behind an empty-table guard in migration 260. The [[Database Catalog]] describes the current schema. See [[ADR-010 Production telemetry before retirement]].

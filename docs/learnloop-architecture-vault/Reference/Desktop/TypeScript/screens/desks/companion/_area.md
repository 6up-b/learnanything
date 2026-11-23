---
title: "Desktop area · TypeScript/screens/desks/companion"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/companion"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks/companion

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks/companion](../../../../../../../../apps/learnloop-tauri/src/screens/desks/companion)

## Responsibility

The app-wide companion: its docks, summon, dissolve, hand-off and pill (geometry and state machine), its questions as polled companion.ask jobs, the panel with the desk's thread and the history, and previewed diffs.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/companion/Companion|Companion.tsx]] | `ACTIVE` | Implements the `Companion` routed desktop screen and coordinates its learner-facing workflow state. | 8 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/companion/DiffProposal|DiffProposal.tsx]] | `ACTIVE` | Implements the `DiffProposal` routed desktop screen and coordinates its learner-facing workflow state. | 0 | 2 |
| [[Reference/Desktop/TypeScript/screens/desks/companion/asks|asks.ts]] | `ACTIVE` | Provides `CompanionApi`, `ExchangeStatus`, `CompanionExchange`, `DeskWritesSettled` and related exports within the desktop's TypeScript/screens/desks/companion ownership area. | 2 | 2 |
| [[Reference/Desktop/TypeScript/screens/desks/companion/model|model.ts]] | `ACTIVE` | Provides `COMPANION_SIZES`, `DOCKS`, `dockRect`, `anchoredRect` and related exports within the desktop's TypeScript/screens/desks/companion ownership area. | 2 | 2 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

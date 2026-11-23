---
title: "Desktop area · TypeScript/screens/desks/overview"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/overview"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks/overview

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks/overview](../../../../../../../../apps/learnloop-tauri/src/screens/desks/overview)

## Responsibility

The desks' overview: the zoom engine (layout, camera, frame function, spring, wheel), its one frame writer, cards, curved links, gather and live miniatures.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/overview/Card|Card.tsx]] | `ACTIVE` | Implements the `Card` routed desktop screen and coordinates its learner-facing workflow state. | 2 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/overview/controller|controller.ts]] | `ACTIVE` | Provides `SlotElements`, `ZoomPlan`, `ZoomTargets`, `FrameClock` and related exports within the desktop's TypeScript/screens/desks/overview ownership area. | 2 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/overview/engine|engine.ts]] | `ACTIVE` | Provides `OVERVIEW`, `Camera`, `IDENTITY`, `OverviewLayout` and related exports within the desktop's TypeScript/screens/desks/overview ownership area. | 1 | 2 |
| [[Reference/Desktop/TypeScript/screens/desks/overview/links|links.ts]] | `ACTIVE` | Provides `Relation`, `DRAWN_RELATIONS`, `openedBeside`, `relationsOf` and related exports within the desktop's TypeScript/screens/desks/overview ownership area. | 3 | 2 |
| [[Reference/Desktop/TypeScript/screens/desks/overview/miniature|miniature.ts]] | `ACTIVE` | Provides `cloneForMiniature`, `MiniatureBook` within the desktop's TypeScript/screens/desks/overview ownership area. | 0 | 1 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

---
title: "Desktop area · TypeScript/screens/desks/goal"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/goal"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks/goal

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks/goal](../../../../../../../../apps/learnloop-tauri/src/screens/desks/goal)

## Responsibility

The goal lens on the desks: the goal band under the top bar, criticality marks with their why card, dimming, section callouts, a pad stack's goal line and the path view, all read from goal.band and goal.lens.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/goal/GoalBand|GoalBand.tsx]] | `ACTIVE` | Implements the `GoalBand` routed desktop screen and coordinates its learner-facing workflow state. | 2 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/goal/GoalLayer|GoalLayer.tsx]] | `ACTIVE` | Implements the `GoalLayer` routed desktop screen and coordinates its learner-facing workflow state. | 10 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/goal/PathView|PathView.tsx]] | `ACTIVE` | Implements the `PathView` routed desktop screen and coordinates its learner-facing workflow state. | 2 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/goal/controller|controller.ts]] | `ACTIVE` | Provides `GoalTransport`, `LIVE_GOAL_TRANSPORT`, `BAND_RECHECK_MS`, `watchStateChanges` and related exports within the desktop's TypeScript/screens/desks/goal ownership area. | 6 | 3 |
| [[Reference/Desktop/TypeScript/screens/desks/goal/marks|marks.tsx]] | `ACTIVE` | Implements the `marks` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/goal/model|model.ts]] | `ACTIVE` | Provides `LensLevel`, `LEVEL_LABEL`, `MarkKind`, `markKind` and related exports within the desktop's TypeScript/screens/desks/goal ownership area. | 1 | 5 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

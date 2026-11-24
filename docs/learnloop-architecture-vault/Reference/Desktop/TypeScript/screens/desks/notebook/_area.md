---
title: "Desktop area · TypeScript/screens/desks/notebook"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/notebook"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks/notebook

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks/notebook](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook)

## Responsibility

A marimo notebook in a window: the frame served by the sidecar's sandboxed session, its honest states, the window lifecycle, the bridge's four messages checked by source, origin and shape, and a pad's marimo cells with their one live framed group.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/notebook/LessonNotebook|LessonNotebook.tsx]] | `ACTIVE` | Implements the `LessonNotebook` routed desktop screen and coordinates its learner-facing workflow state. | 3 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/notebook/NotebookFrame|NotebookFrame.tsx]] | `ACTIVE` | Implements the `NotebookFrame` routed desktop screen and coordinates its learner-facing workflow state. | 4 | 4 |
| [[Reference/Desktop/TypeScript/screens/desks/notebook/PadCell|PadCell.tsx]] | `ACTIVE` | Implements the `PadCell` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/notebook/bridge|bridge.ts]] | `ACTIVE` | Provides `BridgeKind`, `BridgeRect`, `BridgeMessage`, `BRIDGE_TEXT_MAX` and related exports within the desktop's TypeScript/screens/desks/notebook ownership area. | 0 | 4 |
| [[Reference/Desktop/TypeScript/screens/desks/notebook/menuBridge|menuBridge.ts]] | `ACTIVE` | Provides `MARIMO_CELL_INSERT`, `MARIMO_CELL_ROW`, `NotebookMenuRequest`, `notebookMenuRequest` and related exports within the desktop's TypeScript/screens/desks/notebook ownership area. | 2 | 3 |
| [[Reference/Desktop/TypeScript/screens/desks/notebook/padNotebooks|padNotebooks.ts]] | `ACTIVE` | Provides `PadNotebook`, `padNotebook`, `subscribePadNotebooks`, `cellShape` and related exports within the desktop's TypeScript/screens/desks/notebook ownership area. | 1 | 1 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

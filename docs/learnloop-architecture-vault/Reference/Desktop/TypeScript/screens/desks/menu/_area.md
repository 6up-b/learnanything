---
title: "Desktop area · TypeScript/screens/desks/menu"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/menu"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks/menu

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks/menu](../../../../../../../../apps/learnloop-tauri/src/screens/desks/menu)

## Responsibility

The context-aware right-click: one menu and one listener for passages, cues, highlights, margin notes, window headers and pad lines, its promoted rows (passage.promoted and the judged job on the poller, labelled per row), the verbs wired to their server entries, and What this knows.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/menu/ContextMenu|ContextMenu.tsx]] | `ACTIVE` | Implements the `ContextMenu` routed desktop screen and coordinates its learner-facing workflow state. | 4 | 3 |
| [[Reference/Desktop/TypeScript/screens/desks/menu/KnowsPanel|KnowsPanel.tsx]] | `ACTIVE` | Implements the `KnowsPanel` routed desktop screen and coordinates its learner-facing workflow state. | 1 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/menu/model|model.ts]] | `ACTIVE` | Provides `MenuObjectKind`, `MenuObject`, `objectInput`, `headerLine` and related exports within the desktop's TypeScript/screens/desks/menu ownership area. | 2 | 4 |
| [[Reference/Desktop/TypeScript/screens/desks/menu/verbs|verbs.ts]] | `ACTIVE` | Provides `MenuApi`, `MenuContext`, `promotedRef`, `runVerb` and related exports within the desktop's TypeScript/screens/desks/menu ownership area. | 3 | 1 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

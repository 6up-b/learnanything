---
title: "Desktop area · TypeScript/screens/desks/windows"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/windows"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks/windows

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks/windows](../../../../../../../../apps/learnloop-tauri/src/screens/desks/windows)

## Responsibility

Desk windows: the Reader's source pane as a scoped source or video window, thread windows, and the panel windows hosting v1 Reader surfaces.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/windows/PanelWindow|PanelWindow.tsx]] | `ACTIVE` | Implements the `PanelWindow` routed desktop screen and coordinates its learner-facing workflow state. | 6 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|SourceWindow.tsx]] | `ACTIVE` | Implements the `SourceWindow` routed desktop screen and coordinates its learner-facing workflow state. | 3 | 2 |
| [[Reference/Desktop/TypeScript/screens/desks/windows/ThreadWindow|ThreadWindow.tsx]] | `ACTIVE` | Implements the `ThreadWindow` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

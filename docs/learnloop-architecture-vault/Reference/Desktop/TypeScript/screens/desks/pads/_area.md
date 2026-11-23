---
title: "Desktop area · TypeScript/screens/desks/pads"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/pads"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks/pads

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks/pads](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads)

## Responsibility

The scratchpads: pad stack windows (sticky tabs, the running pad, the live editor writing through pad.apply), provenance, gutter marks and hover cards, the pad menu, arrange and split, sketch blocks, submitting a block, passage marks for links and carried questions, and the desk drain.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/pads/DrainPanel|DrainPanel.tsx]] | `ACTIVE` | Implements the `DrainPanel` routed desktop screen and coordinates its learner-facing workflow state. | 2 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/pads/PadOverlays|PadOverlays.tsx]] | `ACTIVE` | Implements the `PadOverlays` routed desktop screen and coordinates its learner-facing workflow state. | 7 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|PadStackWindow.tsx]] | `ACTIVE` | Implements the `PadStackWindow` routed desktop screen and coordinates its learner-facing workflow state. | 12 | 2 |
| [[Reference/Desktop/TypeScript/screens/desks/pads/PassageMarks|PassageMarks.tsx]] | `ACTIVE` | Implements the `PassageMarks` routed desktop screen and coordinates its learner-facing workflow state. | 2 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/pads/SketchCanvas|SketchCanvas.tsx]] | `ACTIVE` | Implements the `SketchCanvas` routed desktop screen and coordinates its learner-facing workflow state. | 0 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/pads/host|host.ts]] | `ACTIVE` | Provides `PadsApi`, `SourcePiece`, `PadsHost`, `PadStackHandle` and related exports within the desktop's TypeScript/screens/desks/pads ownership area. | 5 | 4 |
| [[Reference/Desktop/TypeScript/screens/desks/pads/model|model.ts]] | `ACTIVE` | Provides `EDITABLE_KINDS`, `PadState`, `Pads`, `PadOpRefusal` and related exports within the desktop's TypeScript/screens/desks/pads ownership area. | 1 | 5 |
| [[Reference/Desktop/TypeScript/screens/desks/pads/stickyTabs|stickyTabs.ts]] | `ACTIVE` | Provides `TAB_SIZES`, `TabGrade`, `PadGeometry`, `stuckTop` and related exports within the desktop's TypeScript/screens/desks/pads ownership area. | 0 | 1 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

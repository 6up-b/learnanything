---
title: "Desktop area · TypeScript/screens/desks/pen"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/pen"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks/pen

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks/pen](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen)

## Responsibility

Pen and ink on sources: pen input (pressure, tilt, the barrel eraser, palm rejection), the recognizer (underline, bracket, margin note, lasso, strike), the ink layer inside a source window's scroller, the annotations each mark becomes, ink saved in the one write sequence, the margin note's transcription, and ink pads (lined or dotted paper, ink lines and their readings through the central poller, the learner's corrections).

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/pen/InkLine|InkLine.tsx]] | `ACTIVE` | Implements the `InkLine` routed desktop screen and coordinates its learner-facing workflow state. | 6 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/pen/PenLayer|PenLayer.tsx]] | `ACTIVE` | Implements the `PenLayer` routed desktop screen and coordinates its learner-facing workflow state. | 8 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/pen/geometry|geometry.ts]] | `ACTIVE` | Provides `PASSAGE`, `LocalRect`, `caretAt`, `passages` and related exports within the desktop's TypeScript/screens/desks/pen ownership area. | 1 | 2 |
| [[Reference/Desktop/TypeScript/screens/desks/pen/host|host.ts]] | `ACTIVE` | Provides `PenApi`, `PenHost`, `PenHostContext`, `usePenHost` within the desktop's TypeScript/screens/desks/pen ownership area. | 4 | 5 |
| [[Reference/Desktop/TypeScript/screens/desks/pen/inkCache|inkCache.ts]] | `ACTIVE` | Provides `InkCacheApi`, `inkRefusal`, `ReadingStatus`, `LineReading` and related exports within the desktop's TypeScript/screens/desks/pen ownership area. | 2 | 3 |
| [[Reference/Desktop/TypeScript/screens/desks/pen/input|input.ts]] | `ACTIVE` | Provides `PointerLike`, `Sample`, `FinishedStroke`, `DownOutcome` and related exports within the desktop's TypeScript/screens/desks/pen ownership area. | 0 | 2 |
| [[Reference/Desktop/TypeScript/screens/desks/pen/live|live.ts]] | `ACTIVE` | Provides `LIVE_PEN_API` within the desktop's TypeScript/screens/desks/pen ownership area. | 2 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/pen/recognizer|recognizer.ts]] | `ACTIVE` | Provides `Point`, `Box`, `LineBox`, `RecognizerPage` and related exports within the desktop's TypeScript/screens/desks/pen ownership area. | 0 | 2 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

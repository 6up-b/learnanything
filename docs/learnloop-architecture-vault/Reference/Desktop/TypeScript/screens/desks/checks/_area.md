---
title: "Desktop area · TypeScript/screens/desks/checks"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/checks"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks/checks

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks/checks](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks)

## Responsibility

Inline cold checks on the desks: a due check's closed marker before its host passage (no cues), check now with what is visible, the server's veils laid on the page with their pills and show it anyway (check.expose at once), check.protect_more for what comes into view, the card at the host passage or centred near the top, submit and its reason in plain words, not now, and restart.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/checks/CheckCard|CheckCard.tsx]] | `ACTIVE` | Implements the `CheckCard` routed desktop screen and coordinates its learner-facing workflow state. | 7 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/checks/VeilLayer|VeilLayer.tsx]] | `ACTIVE` | Implements the `VeilLayer` routed desktop screen and coordinates its learner-facing workflow state. | 4 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/checks/controller|controller.ts]] | `ACTIVE` | Provides `CheckTransport`, `LIVE_CHECK_TRANSPORT`, `DueCheck`, `OpenCheck` and related exports within the desktop's TypeScript/screens/desks/checks ownership area. | 3 | 5 |
| [[Reference/Desktop/TypeScript/screens/desks/checks/hold|hold.ts]] | `ACTIVE` | Provides `SAFE_ATTR`, `PASSAGE_TEXT_ATTR`, `REGION_ATTR`, `QUIET_ATTR` and related exports within the desktop's TypeScript/screens/desks/checks ownership area. | 2 | 3 |
| [[Reference/Desktop/TypeScript/screens/desks/checks/holdContext|holdContext.ts]] | `ACTIVE` | Provides `CheckHoldContext`, `useCheckHeld` within the desktop's TypeScript/screens/desks/checks ownership area. | 0 | 2 |
| [[Reference/Desktop/TypeScript/screens/desks/checks/model|model.ts]] | `ACTIVE` | Provides `VEIL_LABEL`, `SHOW_ANYWAY_COST`, `SHOW_NOTE_COST`, `SHOW_UNMEASURED_COST` and related exports within the desktop's TypeScript/screens/desks/checks ownership area. | 1 | 5 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

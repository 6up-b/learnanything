---
title: "Desktop area · TypeScript/screens/desks/keys"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/keys"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks/keys

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks/keys](../../../../../../../../apps/learnloop-tauri/src/screens/desks/keys)

## Responsibility

The desks' key router (the scope and precedence matrix, the bare-Alt hold rule) and the one listener router for every window.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/keys/listeners|listeners.ts]] | `ACTIVE` | Provides `RouterHooks`, `WINDOW_ATTRIBUTE`, `windowOfTarget`, `DeskListenerRouter` within the desktop's TypeScript/screens/desks/keys ownership area. | 1 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/keys/router|router.ts]] | `ACTIVE` | Provides `DeskScope`, `SCOPE_ORDER`, `DeskAction`, `Chord` and related exports within the desktop's TypeScript/screens/desks/keys ownership area. | 0 | 3 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

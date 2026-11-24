---
title: "Desktop area · TypeScript/screens/desks/sideBySide"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/sideBySide"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks/sideBySide

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks/sideBySide](../../../../../../../../apps/learnloop-tauri/src/screens/desks/sideBySide)

## Responsibility

Side by side on the desks as paired windows: the pair a book opens in, which window leads, follow along between the two, and the way back.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/sideBySide/pairs|pairs.ts]] | `ACTIVE` | Provides `Pair`, `PairWindow`, `PairDeps`, `keptPairsFor` and related exports within the desktop's TypeScript/screens/desks/sideBySide ownership area. | 2 | 1 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

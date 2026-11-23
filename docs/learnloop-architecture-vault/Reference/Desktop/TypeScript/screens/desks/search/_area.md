---
title: "Desktop area · TypeScript/screens/desks/search"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/search"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks/search

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks/search](../../../../../../../../apps/learnloop-tauri/src/screens/desks/search)

## Responsibility

Search in context: the groups of search.everything with the client's open-on-this-desk group, the meaning job, insert mode and the panel.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/search/SearchPanel|SearchPanel.tsx]] | `ACTIVE` | Implements the `SearchPanel` routed desktop screen and coordinates its learner-facing workflow state. | 4 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/search/model|model.ts]] | `ACTIVE` | Provides `ROWS_PER_GROUP`, `GROUP_ORDER`, `OpenWindow`, `SearchRow` and related exports within the desktop's TypeScript/screens/desks/search ownership area. | 1 | 3 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

---
title: "Desktop area · TypeScript/components/graphedit"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/components/graphedit"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/components/graphedit

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/components/graphedit](../../../../../../../apps/learnloop-tauri/src/components/graphedit)

## Responsibility

Study-map editing widgets, pending edits, and geometry previews.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/components/graphedit/EditPopovers|EditPopovers.tsx]] | `ACTIVE` | Provides the reusable `EditPopovers` interaction surface used by one or more desktop workflows. | 2 | 1 |
| [[Reference/Desktop/TypeScript/components/graphedit/GeometryPreview|GeometryPreview.tsx]] | `ACTIVE` | Provides the reusable `GeometryPreview` interaction surface used by one or more desktop workflows. | 2 | 1 |
| [[Reference/Desktop/TypeScript/components/graphedit/PendingStrip|PendingStrip.tsx]] | `ACTIVE` | Provides the reusable `PendingStrip` interaction surface used by one or more desktop workflows. | 2 | 1 |
| [[Reference/Desktop/TypeScript/components/graphedit/SyllabusColumn|SyllabusColumn.tsx]] | `ACTIVE` | Provides the reusable `SyllabusColumn` interaction surface used by one or more desktop workflows. | 3 | 1 |
| [[Reference/Desktop/TypeScript/components/graphedit/pending|pending.ts]] | `ACTIVE` | Provides shared `pending` state or utility behavior for desktop components. | 1 | 4 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

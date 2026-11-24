---
title: "Desktop area · TypeScript/screens/desks/source"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/source"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks/source

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks/source](../../../../../../../../apps/learnloop-tauri/src/screens/desks/source)

## Responsibility

The scoped source: everything a source window mounts (the book's open and identity, selection and capture, inquiry, the PDF, text and video bodies, cues, figures, notes, the lens, pen and windowing seams) and its contracts; the standalone Reader screen mounts the same source with its own branches.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/source/ScopedSource|ScopedSource.tsx]] | `ACTIVE` | Implements the `ScopedSource` routed desktop screen and coordinates its learner-facing workflow state. | 82 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/source/types|types.ts]] | `ACTIVE` | Provides `ReaderOpenSource`, `ReaderWindowing`, `WindowInquiry`, `ReaderLens` and related exports within the desktop's TypeScript/screens/desks/source ownership area. | 11 | 9 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

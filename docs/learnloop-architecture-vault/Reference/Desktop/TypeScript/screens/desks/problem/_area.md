---
title: "Desktop area · TypeScript/screens/desks/problem"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/problem"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks/problem

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks/problem](../../../../../../../../apps/learnloop-tauri/src/screens/desks/problem)

## Responsibility

RW2 problems on the desks: one problem pad per workbench session (its id derived from the session's), found from any view of the desks, with the workbench's steps, help ladder, checks and submit.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/problem/ProblemPad|ProblemPad.tsx]] | `ACTIVE` | Implements the `ProblemPad` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 3 |
| [[Reference/Desktop/TypeScript/screens/desks/problem/problemPads|problemPads.ts]] | `ACTIVE` | Provides `ProblemHandoff`, `problemPadId`, `problemsVersion`, `subscribeProblems` and related exports within the desktop's TypeScript/screens/desks/problem ownership area. | 1 | 4 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

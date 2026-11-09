---
title: "Desktop area · TypeScript/screens/workbench"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/workbench"
source_commit: "86021e6b79512c86957d2bb83a488e23a3818a2f"
source_commit_timestamp: "2026-11-09T03:09:29-05:00"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/workbench

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/workbench](../../../../../../../apps/learnloop-tauri/src/screens/workbench)

## Responsibility

The Reader workbench: steps, Check my work, the help ladder, step hints, and the session state behind them.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/workbench/BookPassage|BookPassage.tsx]] | `ACTIVE` | Implements the `BookPassage` routed desktop screen and coordinates its learner-facing workflow state. | 7 | 1 |
| [[Reference/Desktop/TypeScript/screens/workbench/CheckColumn|CheckColumn.tsx]] | `ACTIVE` | Implements the `CheckColumn` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/workbench/HelpLadder|HelpLadder.tsx]] | `ACTIVE` | Implements the `HelpLadder` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/workbench/HelpStyleControl|HelpStyleControl.tsx]] | `ACTIVE` | Implements the `HelpStyleControl` routed desktop screen and coordinates its learner-facing workflow state. | 3 | 1 |
| [[Reference/Desktop/TypeScript/screens/workbench/RouteExample|RouteExample.tsx]] | `ACTIVE` | Implements the `RouteExample` routed desktop screen and coordinates its learner-facing workflow state. | 6 | 1 |
| [[Reference/Desktop/TypeScript/screens/workbench/StepHints|StepHints.tsx]] | `ACTIVE` | Implements the `StepHints` routed desktop screen and coordinates its learner-facing workflow state. | 10 | 1 |
| [[Reference/Desktop/TypeScript/screens/workbench/WhereThisGoes|WhereThisGoes.tsx]] | `ACTIVE` | Implements the `WhereThisGoes` routed desktop screen and coordinates its learner-facing workflow state. | 3 | 2 |
| [[Reference/Desktop/TypeScript/screens/workbench/Workbench|Workbench.tsx]] | `ACTIVE` | Implements the `Workbench` routed desktop screen and coordinates its learner-facing workflow state. | 22 | 2 |
| [[Reference/Desktop/TypeScript/screens/workbench/helpModel|helpModel.ts]] | `ACTIVE` | Provides `HELP_COPY`, `STYLE_OPTIONS`, `WORKBENCH_SHORTCUTS`, `WHERE_THIS_GOES` and related exports within the desktop's TypeScript/screens/workbench ownership area. | 1 | 8 |
| [[Reference/Desktop/TypeScript/screens/workbench/splitWidth|splitWidth.ts]] | `ACTIVE` | Provides `MIN_WORKBENCH_WIDTH`, `MIN_SOURCE_WIDTH`, `NARROW_BREAKPOINT`, `SPLIT_WIDTH_KEY` and related exports within the desktop's TypeScript/screens/workbench ownership area. | 0 | 4 |
| [[Reference/Desktop/TypeScript/screens/workbench/stepModel|stepModel.ts]] | `ACTIVE` | Provides `BOOK_OPEN_ENTRIES`, `defaultBookVisible`, `LocalStep`, `fromServer` and related exports within the desktop's TypeScript/screens/workbench ownership area. | 1 | 4 |
| [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchHelp|useWorkbenchHelp.ts]] | `ACTIVE` | Provides `UNSAVED_HELP`, `LadderState`, `HelpNotice`, `BridgeState` and related exports within the desktop's TypeScript/screens/workbench ownership area. | 4 | 4 |
| [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchSession|useWorkbenchSession.ts]] | `ACTIVE` | Provides `EDIT_DEBOUNCE_MS`, `leaveHeldNote`, `leftUnsavedNote`, `notSavedError` and related exports within the desktop's TypeScript/screens/workbench ownership area. | 8 | 1 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

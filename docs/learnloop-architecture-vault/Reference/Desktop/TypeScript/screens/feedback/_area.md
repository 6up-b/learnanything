---
title: "Desktop area · TypeScript/screens/feedback"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/feedback"
source_commit: "8f3748c8efff33dd23b54316db44d6c1af5ceb87"
source_commit_timestamp: "2026-10-25T16:16:44-04:00"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/feedback

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/feedback](../../../../../../../apps/learnloop-tauri/src/screens/feedback)

## Responsibility

The post-answer feedback surface: answer exposure, method comparison, and its exposure contract.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/feedback/CompareMethods|CompareMethods.tsx]] | `ACTIVE` | Implements the `CompareMethods` routed desktop screen and coordinates its learner-facing workflow state. | 7 | 1 |
| [[Reference/Desktop/TypeScript/screens/feedback/FeedbackSurface|FeedbackSurface.tsx]] | `ACTIVE` | Implements the `FeedbackSurface` routed desktop screen and coordinates its learner-facing workflow state. | 8 | 2 |
| [[Reference/Desktop/TypeScript/screens/feedback/answerExposure|answerExposure.ts]] | `ACTIVE` | Provides `EXPOSURE`, `DisplayReceipt`, `RecordDisplay`, `ExposureStatus` and related exports within the desktop's TypeScript/screens/feedback ownership area. | 0 | 2 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

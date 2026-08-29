---
title: "Desktop area · TypeScript/screens"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens"
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

# TypeScript/screens

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens](../../../../../../apps/learnloop-tauri/src/screens)

## Responsibility

Top-level routed workflow screens in the desktop shell.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

- [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] — Reader request-state coordination extracted from the main reader screen.
- [[Reference/Desktop/TypeScript/screens/startBackdrops/_area|TypeScript/screens/startBackdrops]] — Canvas/SVG simulations and workers used as the start-screen visual backdrop.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/CalibrationScreen|CalibrationScreen.tsx]] | `ACTIVE` | Implements the `CalibrationScreen` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|DiagnosticReviewScreen.tsx]] | `ACTIVE` | Implements the `DiagnosticReviewScreen` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/ExamScreen|ExamScreen.tsx]] | `ACTIVE` | Implements the `ExamScreen` routed desktop screen and coordinates its learner-facing workflow state. | 9 | 1 |
| [[Reference/Desktop/TypeScript/screens/FeedbackScreen|FeedbackScreen.tsx]] | `ACTIVE` | Implements the `FeedbackScreen` routed desktop screen and coordinates its learner-facing workflow state. | 13 | 1 |
| [[Reference/Desktop/TypeScript/screens/GoldenPathScreen|GoldenPathScreen.tsx]] | `ACTIVE` | Implements the `GoldenPathScreen` routed desktop screen and coordinates its learner-facing workflow state. | 8 | 1 |
| [[Reference/Desktop/TypeScript/screens/GraphScreen|GraphScreen.tsx]] | `ACTIVE` | Implements the `GraphScreen` routed desktop screen and coordinates its learner-facing workflow state. | 11 | 1 |
| [[Reference/Desktop/TypeScript/screens/IngestScreen|IngestScreen.tsx]] | `ACTIVE` | Implements the `IngestScreen` routed desktop screen and coordinates its learner-facing workflow state. | 11 | 1 |
| [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|KnowledgeMapScreen.tsx]] | `ACTIVE` | Implements the `KnowledgeMapScreen` routed desktop screen and coordinates its learner-facing workflow state. | 10 | 1 |
| [[Reference/Desktop/TypeScript/screens/KnowledgeStrataView|KnowledgeStrataView.tsx]] | `ACTIVE` | Implements the `KnowledgeStrataView` routed desktop screen and coordinates its learner-facing workflow state. | 3 | 1 |
| [[Reference/Desktop/TypeScript/screens/KnowledgeTerrainView|KnowledgeTerrainView.tsx]] | `ACTIVE` | Implements the `KnowledgeTerrainView` routed desktop screen and coordinates its learner-facing workflow state. | 3 | 1 |
| [[Reference/Desktop/TypeScript/screens/KnowledgeWellView|KnowledgeWellView.tsx]] | `ACTIVE` | Implements the `KnowledgeWellView` routed desktop screen and coordinates its learner-facing workflow state. | 4 | 1 |
| [[Reference/Desktop/TypeScript/screens/LibraryScreen|LibraryScreen.tsx]] | `ACTIVE` | Implements the `LibraryScreen` routed desktop screen and coordinates its learner-facing workflow state. | 7 | 1 |
| [[Reference/Desktop/TypeScript/screens/MaintenanceScreen|MaintenanceScreen.tsx]] | `ACTIVE` | Implements the `MaintenanceScreen` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/PracticeScreen|PracticeScreen.tsx]] | `ACTIVE` | Implements the `PracticeScreen` routed desktop screen and coordinates its learner-facing workflow state. | 11 | 1 |
| [[Reference/Desktop/TypeScript/screens/ProposalsScreen|ProposalsScreen.tsx]] | `ACTIVE` | Implements the `ProposalsScreen` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/ReaderScreen|ReaderScreen.tsx]] | `ACTIVE` | Implements the `ReaderScreen` routed desktop screen and coordinates its learner-facing workflow state. | 11 | 2 |
| [[Reference/Desktop/TypeScript/screens/RegistryReviewScreen|RegistryReviewScreen.tsx]] | `ACTIVE` | Implements the `RegistryReviewScreen` routed desktop screen and coordinates its learner-facing workflow state. | 4 | 1 |
| [[Reference/Desktop/TypeScript/screens/RepairScreen|RepairScreen.tsx]] | `ACTIVE` | Implements the `RepairScreen` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/ReviewScreen|ReviewScreen.tsx]] | `ACTIVE` | Implements the `ReviewScreen` routed desktop screen and coordinates its learner-facing workflow state. | 6 | 1 |
| [[Reference/Desktop/TypeScript/screens/SettingsScreen|SettingsScreen.tsx]] | `ACTIVE` | Implements the `SettingsScreen` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/SqliteBrowser|SqliteBrowser.tsx]] | `ACTIVE` | Implements the `SqliteBrowser` routed desktop screen and coordinates its learner-facing workflow state. | 3 | 1 |
| [[Reference/Desktop/TypeScript/screens/StartScreen|StartScreen.tsx]] | `ACTIVE` | Implements the `StartScreen` routed desktop screen and coordinates its learner-facing workflow state. | 11 | 1 |
| [[Reference/Desktop/TypeScript/screens/TodayScreen|TodayScreen.tsx]] | `ACTIVE` | Implements the `TodayScreen` routed desktop screen and coordinates its learner-facing workflow state. | 15 | 1 |
| [[Reference/Desktop/TypeScript/screens/scrollZoom|scrollZoom.ts]] | `ACTIVE` | Provides `SCROLL_ZOOM`, `ScrollZoomOptions`, `ScrollZoom`, `useScrollZoom` within the desktop's TypeScript/screens ownership area. | 0 | 1 |
| [[Reference/Desktop/TypeScript/screens/wire3d|wire3d.ts]] | `ACTIVE` | Provides `Cam`, `Viewport`, `Projected`, `project` and related exports within the desktop's TypeScript/screens ownership area. | 0 | 3 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

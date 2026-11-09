---
title: "Desktop area · TypeScript/screens/today"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/today"
source_commit: "workspace/uncommitted @ c8ed55f10b84fdce46fada919c39e9004aabff65"
source_commit_timestamp: "2026-11-09T12:16:08-05:00"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/today

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/today](../../../../../../../apps/learnloop-tauri/src/screens/today)

## Responsibility

The Today place: the daily plan view and re-entry after time away.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/today/ContinueLessonCard|ContinueLessonCard.tsx]] | `ACTIVE` | Implements the `ContinueLessonCard` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/today/DailyPlanView|DailyPlanView.tsx]] | `ACTIVE` | Implements the `DailyPlanView` routed desktop screen and coordinates its learner-facing workflow state. | 9 | 2 |
| [[Reference/Desktop/TypeScript/screens/today/LessonOfferBlock|LessonOfferBlock.tsx]] | `ACTIVE` | Implements the `LessonOfferBlock` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 3 |
| [[Reference/Desktop/TypeScript/screens/today/LessonOfferPage|LessonOfferPage.tsx]] | `ACTIVE` | Implements the `LessonOfferPage` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/today/LessonSuggestionCard|LessonSuggestionCard.tsx]] | `ACTIVE` | Implements the `LessonSuggestionCard` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 2 |
| [[Reference/Desktop/TypeScript/screens/today/QuestionInProgress|QuestionInProgress.tsx]] | `ACTIVE` | Implements the `QuestionInProgress` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 2 |
| [[Reference/Desktop/TypeScript/screens/today/SomethingElse|SomethingElse.tsx]] | `ACTIVE` | Implements the `SomethingElse` routed desktop screen and coordinates its learner-facing workflow state. | 6 | 6 |
| [[Reference/Desktop/TypeScript/screens/today/TodayPlace|TodayPlace.tsx]] | `ACTIVE` | Implements the `TodayPlace` routed desktop screen and coordinates its learner-facing workflow state. | 21 | 1 |
| [[Reference/Desktop/TypeScript/screens/today/reentry|reentry.ts]] | `ACTIVE` | Provides `reentryRefreshers`, `reentryRefresherLine` within the desktop's TypeScript/screens/today ownership area. | 1 | 1 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

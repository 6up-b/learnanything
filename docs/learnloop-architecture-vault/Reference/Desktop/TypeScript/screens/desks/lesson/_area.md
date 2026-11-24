---
title: "Desktop area · TypeScript/screens/desks/lesson"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/lesson"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks/lesson

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks/lesson](../../../../../../../../apps/learnloop-tauri/src/screens/desks/lesson)

## Responsibility

Teacher lessons as windows and stack tabs: the lesson's paper with its modes (review, your additions), LessonView in its window frame, the additions pad, openings in flight, and the path view's Teacher lesson row, read from lesson.view and lesson.list.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/lesson/LessonPaper|LessonPaper.tsx]] | `ACTIVE` | Implements the `LessonPaper` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/lesson/PathLessonRow|PathLessonRow.tsx]] | `ACTIVE` | Implements the `PathLessonRow` routed desktop screen and coordinates its learner-facing workflow state. | 2 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/lesson/host|host.ts]] | `ACTIVE` | Provides `LessonsTransport`, `LIVE_LESSONS_TRANSPORT`, `Opening`, `LessonDesk` and related exports within the desktop's TypeScript/screens/desks/lesson ownership area. | 4 | 4 |
| [[Reference/Desktop/TypeScript/screens/desks/lesson/model|model.ts]] | `ACTIVE` | Provides `LESSON_KEY`, `OPENING_KEY`, `lessonKey`, `lessonOfKey` and related exports within the desktop's TypeScript/screens/desks/lesson ownership area. | 2 | 5 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]

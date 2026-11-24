---
title: "Desktop module · src/screens/desks/lesson/host.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.lesson.host"
language: "TypeScript"
area: "TypeScript/screens/desks/lesson"
source_path: "apps/learnloop-tauri/src/screens/desks/lesson/host.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/lesson/host.ts"
activation_kind: "entry-reachable build graph"
activation_evidence: "A static TypeScript import path reaches this file from the Vite entry src/main.tsx."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/screens/desks/lesson/host.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/lesson/_area|TypeScript/screens/desks/lesson]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `LessonsTransport`, `LIVE_LESSONS_TRANSPORT`, `Opening`, `LessonDesk` and related exports within the desktop's TypeScript/screens/desks/lesson ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/lesson/host.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/lesson/host.ts) |
| Source lines | 270 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/lesson/_area|TypeScript/screens/desks/lesson]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/lesson/host|src/screens/desks/lesson/host.ts]]

## Public API

- `export interface LessonsTransport` — interface, line 10
- `export const LIVE_LESSONS_TRANSPORT: LessonsTransport =` — const, line 14
- `export interface Opening` — interface, line 19
- `export class LessonDesk` — class, line 28
- `export interface LessonsHost` — interface, line 257

## Internal implementation anchors

- `const known = this.summaries.get(lessonId)` — const, line 63
- `const fresh = lessonIds.filter((id)` — const, line 78
- `const wanted = [...this.queued]` — const, line 86
- `const own = this.additions.get(lessonId)` — const, line 115
- `const known = this.summaries.get(lessonId)` — const, line 142
- `const key = `$` — const, line 151
- `const before = this.openings.length` — const, line 166
- `const opening = this.openings.find((each)` — const, line 174
- `const known = this.openingTurns.get(key)` — const, line 186
- `const turn = send().then((view)` — const, line 188
- `const before = this.openings.length` — const, line 201
- `const lessonId = lessonOfKey(key)` — const, line 210
- `const lessonId = lessonOfKey(key)` — const, line 217
- `const entry = this.openings.find((opening)` — const, line 223
- `const key = this.reveals.get(windowId)` — const, line 238

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `LIVE_LESSONS_TRANSPORT`, `LessonDesk`, `LessonsHost`, `LessonsTransport`, `Opening`; references `LIVE_LESSONS_TRANSPORT`, `LessonDesk`, `LessonsHost`, `LessonsTransport`, `Opening`
- [[Reference/Desktop/TypeScript/screens/desks/lesson/LessonPaper|src/screens/desks/lesson/LessonPaper.tsx]] — import-or-re-export: `LessonsHost`; references `LessonsHost`
- [[Reference/Desktop/TypeScript/screens/desks/lesson/PathLessonRow|src/screens/desks/lesson/PathLessonRow.tsx]] — import-or-re-export: `LessonDesk`; references `LessonDesk`
- [[Reference/Desktop/TypeScript/screens/desks/pads/host|src/screens/desks/pads/host.ts]] — import-or-re-export: `LessonsHost`; references `LessonsHost`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `LessonSummaryDto`, `LessonViewDto`
- [[Reference/Desktop/TypeScript/screens/LessonView|src/screens/LessonView.tsx]] — import-or-re-export; imports `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/desks/lesson/model|src/screens/desks/lesson/model.ts]] — import-or-re-export; imports `OPENING_KEY`, `lessonKey`, `lessonOfKey`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/lesson/model.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/lesson/model.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/lesson/lessonWindows.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/lesson/lessonWindows.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/lesson/host.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/lesson/host.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

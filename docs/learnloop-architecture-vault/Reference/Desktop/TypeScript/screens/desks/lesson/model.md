---
title: "Desktop module · src/screens/desks/lesson/model.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.lesson.model"
language: "TypeScript"
area: "TypeScript/screens/desks/lesson"
source_path: "apps/learnloop-tauri/src/screens/desks/lesson/model.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/lesson/model.ts"
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

# `src/screens/desks/lesson/model.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/lesson/_area|TypeScript/screens/desks/lesson]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `LESSON_KEY`, `OPENING_KEY`, `lessonKey`, `lessonOfKey` and related exports within the desktop's TypeScript/screens/desks/lesson ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/lesson/model.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/lesson/model.ts) |
| Source lines | 122 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/lesson/_area|TypeScript/screens/desks/lesson]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/lesson/model|src/screens/desks/lesson/model.ts]]

## Public API

- `export const LESSON_KEY = "lesson:"` — const, line 10
- `export const OPENING_KEY = "lesson-opening:"` — const, line 11
- `export function lessonKey(lessonId: string): string` — function, line 13
- `export function lessonOfKey(key: string): string | null` — function, line 18
- `export function isLessonItem(key: string): boolean` — function, line 22
- `export function stackItemKeys(stack: PadStackEntryDto[], view: Record<string, unknown> | undefined, openings: readonly string[] = []): string[]` — function, line 28
- `export function lessonTabTitle(topic: string | null | undefined): string` — function, line 36
- `export function lessonTabMeta(summary: Pick<LessonSummaryDto, "openedAt" | "madeFrom"> | null): string` — function, line 56
- `export type LessonMode = "lesson" | "additions"` — type, line 62
- `export function modeButtons(closed: boolean): Array<` — function, line 66
- `export function modeLine(mode: LessonMode, closed: boolean): string` — function, line 70
- `export function lessonMedium(view: Pick<LessonViewDto, "medium"> | null): "notebook" | "lesson"` — function, line 76
- `export function findLesson(ws: Workspace, deskId: string, lessonId: string):` — function, line 81
- `export function stackWindowOf(ws: Workspace, deskId: string): string | null` — function, line 96
- `export function addLessonToStack(ws: Workspace, deskId: string, windowId: string, lessonId: string, options:` — function, line 108
- `export function lessonStack(content: Extract<ContentRefDto,` — function, line 120

## Internal implementation anchors

- `const own = stack.map((entry)` — const, line 29
- `const added = Array.isArray(view?.addedPads) ? (view?.addedPads as unknown[]).filter((id): id is string` — const, line 30
- `const shown = [...own, ...added.filter((id)` — const, line 31
- `const words = (topic ?? "").trim()` — const, line 37
- `const MADE_FROM: Record<LessonSummaryDto["madeFrom"], string> =` — const, line 41
- `function shortDay(iso: string | null | undefined): string` — function, line 49
- `const date = new Date(iso.length === 10 ? `$` — const, line 51
- `const day = shortDay(summary.openedAt)` — const, line 58
- `const desk = deskById(ws, deskId)` — const, line 82
- `const window = ws.windows[windowId]` — const, line 85
- `const window = ws.windows[windowId]` — const, line 89
- `const desk = deskById(ws, deskId)` — const, line 97
- `function pushOp(step: Step, op: DeskOpDto): Step` — function, line 101
- `const next = restampOp(step.ws, op)` — const, line 102
- `let step: Step =` — let, line 109
- `const window = ws.windows[windowId]` — const, line 110
- `const focus = setFocus(step.ws, deskId, windowId)` — const, line 115

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `addLessonToStack`, `findLesson`, `lessonKey`, `lessonStack`, `lessonTabTitle`, `stackWindowOf`; references `addLessonToStack`, `findLesson`, `lessonKey`, `lessonStack`, `lessonTabTitle`, `stackWindowOf`
- [[Reference/Desktop/TypeScript/screens/desks/lesson/LessonPaper|src/screens/desks/lesson/LessonPaper.tsx]] — import-or-re-export: `LessonMode`, `lessonMedium`, `modeButtons`, `modeLine`; references `LessonMode`, `lessonMedium`, `modeButtons`, `modeLine`
- [[Reference/Desktop/TypeScript/screens/desks/lesson/PathLessonRow|src/screens/desks/lesson/PathLessonRow.tsx]] — import-or-re-export: `lessonTabMeta`; references `lessonTabMeta`
- [[Reference/Desktop/TypeScript/screens/desks/lesson/host|src/screens/desks/lesson/host.ts]] — import-or-re-export: `OPENING_KEY`, `lessonKey`, `lessonOfKey`; references `OPENING_KEY`, `lessonKey`, `lessonOfKey`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] — import-or-re-export: `isLessonItem`, `lessonOfKey`, `lessonTabMeta`, `lessonTabTitle`, `stackItemKeys`; references `isLessonItem`, `lessonOfKey`, `lessonTabMeta`, `lessonTabTitle`, `stackItemKeys`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ContentRefDto`, `DeskOpDto`, `LessonSummaryDto`, `LessonViewDto`, `PadStackEntryDto`
- [[Reference/Desktop/TypeScript/screens/desks/model/workspace|src/screens/desks/model/workspace.ts]] — import-or-re-export; imports `Step`, `Workspace`, `deskById`, `restampOp`, `setFocus`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/lesson/model.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/lesson/model.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/lesson/model.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/lesson/model.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

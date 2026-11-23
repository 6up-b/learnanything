---
title: "Desktop module · src/screens/desks/notebook/LessonNotebook.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.notebook.LessonNotebook"
language: "TypeScript"
area: "TypeScript/screens/desks/notebook"
source_path: "apps/learnloop-tauri/src/screens/desks/notebook/LessonNotebook.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/notebook/LessonNotebook.tsx"
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

# `src/screens/desks/notebook/LessonNotebook.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/notebook/_area|TypeScript/screens/desks/notebook]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `LessonNotebook` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/notebook/LessonNotebook.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/LessonNotebook.tsx) |
| Source lines | 88 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/notebook/_area|TypeScript/screens/desks/notebook]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/notebook/LessonNotebook|src/screens/desks/notebook/LessonNotebook.tsx]]

## Public API

- `export const COMMIT_POLL_MS = 750` — const, line 17
- `export interface LessonNotebookApi extends NotebookApi` — interface, line 19
- `export function lessonReleases(session: NotebookSessionDto | null): string[]` — function, line 24
- `export function waitingOnCommit(session: NotebookSessionDto | null): boolean` — function, line 32
- `export interface LessonNotebookProps` — interface, line 37
- `export function LessonNotebook(` — function, line 44
- `export function lessonNotebookFrame(lessonId: string, view: LessonViewDto)` — function, line 86

## Internal implementation anchors

- `const lesson = session?.lesson` — const, line 25
- `const released = new Set(lesson.released)` — const, line 27
- `const lesson = session?.lesson` — const, line 33
- `const inFlight = useRef(new Set<string>())` — const, line 46
- `const onSession = useCallback((next: NotebookSessionDto)` — const, line 48
- `const cells = lessonReleases(next).filter((name)` — const, line 49
- `const message = reason && typeof reason === "object" && "message" in reason ? String((reason as` — const, line 55
- `const review = view.closed` — const, line 63
- `function commitPoll(session: NotebookSessionDto): number | undefined` — function, line 81

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `lessonNotebookFrame`; references `lessonNotebookFrame`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `LessonViewDto`, `NotebookSessionDto`
- [[Reference/Desktop/TypeScript/screens/desks/notebook/NotebookFrame|src/screens/desks/notebook/NotebookFrame.tsx]] — import-or-re-export; imports `NotebookApi`, `NotebookFrame`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/notebook/LessonNotebook.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/LessonNotebook.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/notebook/LessonNotebook.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/LessonNotebook.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/screens/desks/problem/problemPads.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.problem.problemPads"
language: "TypeScript"
area: "TypeScript/screens/desks/problem"
source_path: "apps/learnloop-tauri/src/screens/desks/problem/problemPads.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/problem/problemPads.ts"
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

# `src/screens/desks/problem/problemPads.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/problem/_area|TypeScript/screens/desks/problem]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `ProblemHandoff`, `problemPadId`, `problemsVersion`, `subscribeProblems` and related exports within the desktop's TypeScript/screens/desks/problem ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/problem/problemPads.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/problem/problemPads.ts) |
| Source lines | 71 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/problem/_area|TypeScript/screens/desks/problem]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/problem/problemPads|src/screens/desks/problem/problemPads.ts]]

## Public API

- `export interface ProblemHandoff` — interface, line 8
- `export function problemPadId(sessionId: string): string` — function, line 25
- `export function problemsVersion(): number` — function, line 39
- `export function subscribeProblems(listener: ()` — function, line 43
- `export function problemOf(sessionId: string): ProblemHandoff | null` — function, line 49
- `export function handOver(handoff: ProblemHandoff): void` — function, line 54
- `export function noteProblem(sessionId: string, change: Partial<ProblemHandoff>): void` — function, line 60
- `export function resetProblemsForTests(): void` — function, line 68

## Internal implementation anchors

- `const handed = new Map<string, ProblemHandoff>()` — const, line 29
- `const listeners = new Set<()` — const, line 30
- `let version = 0` — let, line 31
- `function emit(): void` — function, line 33
- `const now = handed.get(sessionId)` — const, line 61

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `ProblemHandoff`, `handOver`, `problemPadId`; references `ProblemHandoff`, `handOver`, `problemPadId`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] — import-or-re-export: `problemOf`, `problemsVersion`, `subscribeProblems`; references `problemOf`, `problemsVersion`, `subscribeProblems`
- [[Reference/Desktop/TypeScript/screens/desks/problem/ProblemPad|src/screens/desks/problem/ProblemPad.tsx]] — import-or-re-export: `handOver`, `noteProblem`, `problemOf`, `subscribeProblems`; references `handOver`, `noteProblem`, `problemOf`, `subscribeProblems`
- [[Reference/Desktop/TypeScript/screens/desks/source/types|src/screens/desks/source/types.ts]] — import-or-re-export: `ProblemHandoff`; references `ProblemHandoff`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `SourceLibraryCard`, `WorkbenchSessionDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/problem/ProblemPad.ink.desk.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/problem/ProblemPad.ink.desk.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/problem/ProblemPad.desk.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/problem/ProblemPad.desk.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/App.desks.test.tsx](../../../../../../../../apps/learnloop-tauri/src/app/App.desks.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/problem/problemPads.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/problem/problemPads.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

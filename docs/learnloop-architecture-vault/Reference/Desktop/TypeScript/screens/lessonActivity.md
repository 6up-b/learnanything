---
title: "Desktop module · src/screens/lessonActivity.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.lessonActivity"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/lessonActivity.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/lessonActivity.ts"
source_commit: "c2c40773f3e02619cc3a42916453f0cc2edf54f1"
source_commit_timestamp: "2026-11-05T23:17:29-05:00"
source_worktree_state: "clean"
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

# `src/screens/lessonActivity.ts`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `LessonActivityBatch`, `LessonActivityTracker`, `createLessonActivity` within the desktop's TypeScript/screens ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/lessonActivity.ts](../../../../../../apps/learnloop-tauri/src/screens/lessonActivity.ts) |
| Source lines | 147 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `c2c40773f3e02619cc3a42916453f0cc2edf54f1` |
| Commit timestamp | `2026-11-05T23:17:29-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/lessonActivity|src/screens/lessonActivity.ts]]

## Public API

- `export interface LessonActivityBatch` — interface, line 17
- `export interface LessonActivityTracker` — interface, line 23
- `export function createLessonActivity(options:` — function, line 44

## Internal implementation anchors

- `type Kind = "active" | "idle" | "hidden"` — type, line 34
- `function newSessionId(): string` — function, line 36
- `const now = options.now ?? (()` — const, line 51
- `const session = options.screenSession ?? newSessionId()` — const, line 52
- `let seq = 0` — let, line 53
- `let stopped = false` — let, line 54
- `let sending = false` — let, line 55
- `let pending: LessonActivityIntervalDto[] = []` — let, line 56
- `let start = now()` — let, line 57
- `let kind: Kind = options.foreground === false ? "hidden" : "active"` — let, line 58
- `let lastInput = start` — let, line 59
- `function emit(from: number, to: number, foreground: boolean): void` — function, line 61
- `function settle(at: number): void` — function, line 69
- `const last = Math.max(start, lastInput)` — const, line 71
- `function cut(at: number): void` — function, line 79
- `function send(): void` — function, line 84
- `const batch = pending` — const, line 86
- `let request: Promise<unknown>` — let, line 89
- `const at = now()` — const, line 109
- `const at = now()` — const, line 119
- `const at = now()` — const, line 133
- `const at = now()` — const, line 140

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] — import-or-re-export: `LessonActivityTracker`, `createLessonActivity`; references `LessonActivityTracker`, `createLessonActivity`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `LessonActivityIntervalDto`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderVisit|src/screens/reader/useReaderVisit.ts]] — import-or-re-export; imports `VISIT_IDLE_MS`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/lessonActivity.test.ts](../../../../../../apps/learnloop-tauri/src/screens/lessonActivity.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/lessonActivity.ts](../../../../../../apps/learnloop-tauri/src/screens/lessonActivity.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

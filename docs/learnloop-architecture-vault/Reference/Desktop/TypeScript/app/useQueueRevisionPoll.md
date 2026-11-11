---
title: "Desktop module · src/app/useQueueRevisionPoll.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.useQueueRevisionPoll"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/useQueueRevisionPoll.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/useQueueRevisionPoll.ts"
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

# `src/app/useQueueRevisionPoll.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `REVISION_POLL_MS`, `RevisionPollView`, `revisionPollHeld`, `QueueRevisionPollOptions` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/useQueueRevisionPoll.ts](../../../../../../apps/learnloop-tauri/src/app/useQueueRevisionPoll.ts) |
| Source lines | 186 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/useQueueRevisionPoll|src/app/useQueueRevisionPoll.ts]]

## Public API

- `export const REVISION_POLL_MS = 3000` — const, line 43
- `export interface RevisionPollView` — interface, line 48
- `export function revisionPollHeld(view: RevisionPollView): boolean` — function, line 63
- `export interface QueueRevisionPollOptions` — interface, line 69
- `export function useQueueRevisionPoll(` — function, line 80

## Internal implementation anchors

- `const onToday = view.tab === "today" || (view.simple && view.tab === "start")` — const, line 64
- `const overToday = view.examOpen || view.calibrationOpen || view.lessonOpen` — const, line 65
- `const sessionIdRef = useRef(sessionId)` — const, line 81
- `const quietRef = useRef(quiet)` — const, line 83
- `const pendingRef = useRef(false)` — const, line 85
- `const tickRef = useRef<(()` — const, line 86
- `let disposed = false` — let, line 97
- `let inFlight = false` — let, line 98
- `let seen: number | null = null` — let, line 99
- `let windowBack = false` — let, line 101
- `let sessionReadOwed = false` — let, line 104
- `const readOpenSession = async (): Promise<boolean>` — const, line 107
- `const id = sessionIdRef.current` — const, line 108
- `const snapshot = await api.getSession(id)` — const, line 111
- `const tick = async ()` — const, line 121
- `let answered = false` — let, line 126
- `const heldRead = quietRef.current` — const, line 127
- `const snapshot = await api.getQueueRevision(heldRead ?` — const, line 129
- `const back = windowBack` — const, line 134
- `const changed = seen !== null && seen !== snapshot.revision` — const, line 136
- `const onWindowBack = ()` — const, line 157
- `const interval = window.setInterval(()` — const, line 164
- `const wasQuietRef = useRef(quiet)` — const, line 180
- `const wasQuiet = wasQuietRef.current` — const, line 182

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `revisionPollHeld`, `useQueueRevisionPoll`; references `revisionPollHeld`, `useQueueRevisionPoll`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `SessionSnapshot`
- [[Reference/Desktop/TypeScript/app/sessionMoved|src/app/sessionMoved.ts]] — import-or-re-export; imports `SessionMoved`, `const`, `sessionMovedFrom`, `setSessionMoved`, `useSessionMoved`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export; imports `notifyQueueChanged`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/app/useQueueRevisionPoll.test.tsx](../../../../../../apps/learnloop-tauri/src/app/useQueueRevisionPoll.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/App.queueRevision.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.queueRevision.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/useQueueRevisionPoll.ts](../../../../../../apps/learnloop-tauri/src/app/useQueueRevisionPoll.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

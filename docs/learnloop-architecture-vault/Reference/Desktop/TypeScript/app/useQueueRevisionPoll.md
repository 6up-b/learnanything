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
source_commit: "da3182176a0bb372a0759299ba54df0c4ab145ef"
source_commit_timestamp: "2026-11-03T04:42:27-05:00"
source_worktree_state: "staged-or-mixed"
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

Provides `REVISION_POLL_MS`, `SessionMoved`, `sessionMovedFrom`, `useSessionMoved` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/useQueueRevisionPoll.ts](../../../../../../apps/learnloop-tauri/src/app/useQueueRevisionPoll.ts) |
| Source lines | 211 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `staged-or-mixed` |
| Source commit | `da3182176a0bb372a0759299ba54df0c4ab145ef` |
| Commit timestamp | `2026-11-03T04:42:27-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/useQueueRevisionPoll|src/app/useQueueRevisionPoll.ts]]

## Public API

- `export const REVISION_POLL_MS = 3000` — const, line 38
- `export interface SessionMoved` — interface, line 40
- `export function sessionMovedFrom(snapshot: SessionSnapshot): SessionMoved | null` — function, line 49
- `export function useSessionMoved(): SessionMoved | null` — function, line 71
- `export interface RevisionPollView` — interface, line 76
- `export function revisionPollHeld(view: RevisionPollView): boolean` — function, line 92
- `export interface QueueRevisionPollOptions` — interface, line 98
- `export function useQueueRevisionPoll(` — function, line 107

## Internal implementation anchors

- `const ownership =` — const, line 50
- `let moved: SessionMoved | null = null` — let, line 56
- `const movedListeners = new Set<()` — const, line 57
- `function setSessionMoved(next: SessionMoved | null): void` — function, line 59
- `function subscribeSessionMoved(listener: ()` — function, line 65
- `const onToday = view.tab === "today" || (view.simple && view.tab === "start")` — const, line 93
- `const overToday = view.examOpen || view.calibrationOpen || view.lessonOpen || view.goldenRunOpen` — const, line 94
- `const sessionIdRef = useRef(sessionId)` — const, line 108
- `const quietRef = useRef(quiet)` — const, line 110
- `const pendingRef = useRef(false)` — const, line 112
- `const tickRef = useRef<(()` — const, line 113
- `let disposed = false` — let, line 122
- `let inFlight = false` — let, line 123
- `let seen: number | null = null` — let, line 124
- `let windowBack = false` — let, line 126
- `let sessionReadOwed = false` — let, line 129
- `const readOpenSession = async (): Promise<boolean>` — const, line 132
- `const id = sessionIdRef.current` — const, line 133
- `const snapshot = await api.getSession(id)` — const, line 136
- `const tick = async ()` — const, line 146
- `let answered = false` — let, line 151
- `const heldRead = quietRef.current` — const, line 152
- `const snapshot = await api.getQueueRevision(heldRead ?` — const, line 154
- `const back = windowBack` — const, line 159
- `const changed = seen !== null && seen !== snapshot.revision` — const, line 161
- `const onWindowBack = ()` — const, line 182
- `const interval = window.setInterval(()` — const, line 189
- `const wasQuietRef = useRef(quiet)` — const, line 205
- `const wasQuiet = wasQuietRef.current` — const, line 207

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `revisionPollHeld`, `useQueueRevisionPoll`; references `revisionPollHeld`, `useQueueRevisionPoll`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `SessionSnapshot`
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

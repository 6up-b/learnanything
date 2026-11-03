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
source_commit: "a500c7fab899f7060bd00510419477e514bb07c8"
source_commit_timestamp: "2026-11-03T01:49:39-05:00"
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
| Source lines | 153 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `a500c7fab899f7060bd00510419477e514bb07c8` |
| Commit timestamp | `2026-11-03T01:49:39-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/useQueueRevisionPoll|src/app/useQueueRevisionPoll.ts]]

## Public API

- `export const REVISION_POLL_MS = 3000` — const, line 26
- `export interface SessionMoved` — interface, line 28
- `export function sessionMovedFrom(snapshot: SessionSnapshot): SessionMoved | null` — function, line 37
- `export function useSessionMoved(): SessionMoved | null` — function, line 59
- `export interface QueueRevisionPollOptions` — interface, line 63
- `export function useQueueRevisionPoll(` — function, line 72

## Internal implementation anchors

- `const ownership =` — const, line 38
- `let moved: SessionMoved | null = null` — let, line 44
- `const movedListeners = new Set<()` — const, line 45
- `function setSessionMoved(next: SessionMoved | null): void` — function, line 47
- `function subscribeSessionMoved(listener: ()` — function, line 53
- `const sessionIdRef = useRef(sessionId)` — const, line 73
- `const quietRef = useRef(quiet)` — const, line 75
- `const pendingRef = useRef(false)` — const, line 77
- `let disposed = false` — let, line 86
- `let inFlight = false` — let, line 87
- `let seen: number | null = null` — let, line 88
- `let rereadSession = false` — let, line 89
- `const readOpenSession = async ()` — const, line 91
- `const id = sessionIdRef.current` — const, line 92
- `const snapshot = await api.getSession(id)` — const, line 95
- `const tick = async ()` — const, line 102
- `const reread = rereadSession` — const, line 107
- `const snapshot = await api.getQueueRevision()` — const, line 110
- `const changed = seen !== null && seen !== snapshot.revision` — const, line 112
- `const onWindowBack = ()` — const, line 127
- `const interval = window.setInterval(()` — const, line 134

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `useQueueRevisionPoll`; references `useQueueRevisionPoll`

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

---
title: "Desktop module · src/screens/attemptClock.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.attemptClock"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/attemptClock.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/attemptClock.ts"
source_commit: "workspace/uncommitted @ 79532f7149b554db05a40c2ae1dbde68d9efec5a"
source_commit_timestamp: "2026-11-09T16:01:49-05:00"
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

# `src/screens/attemptClock.ts`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `openAttemptClock`, `touchAttempt`, `attemptActiveSeconds`, `ActiveStorage` and related exports within the desktop's TypeScript/screens ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/attemptClock.ts](../../../../../../apps/learnloop-tauri/src/screens/attemptClock.ts) |
| Source lines | 85 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `staged-or-mixed` |
| Source commit | `workspace/uncommitted @ 79532f7149b554db05a40c2ae1dbde68d9efec5a` |
| Commit timestamp | `2026-11-09T16:01:49-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/useAttemptClock|src/screens/useAttemptClock.ts]] → [[Reference/Desktop/TypeScript/screens/attemptClock|src/screens/attemptClock.ts]]

## Public API

- `export function openAttemptClock(now: number, carriedMs = 0): VisitClock` — function, line 17
- `export function touchAttempt(clock: VisitClock, now: number): void` — function, line 22
- `export function attemptActiveSeconds(clock: VisitClock, now: number): number` — function, line 27
- `export type ActiveStorage = Pick<Storage, "getItem" | "setItem" | "removeItem">` — type, line 32
- `export function carriedActiveMs(storage: ActiveStorage | null, key: string): number` — function, line 35
- `export function keepActiveMs(storage: ActiveStorage | null, key: string, ms: number): void` — function, line 45
- `export function forgetActiveMs(storage: ActiveStorage | null, key: string): void` — function, line 54
- `export function forgetActiveMsWithPrefix(storage: ActiveStorage | null, prefix: string): void` — function, line 64
- `export function defaultActiveStorage(): ActiveStorage | null` — function, line 79

## Internal implementation anchors

- `const KEY_PREFIX = "learnloop.activeMs."` — const, line 14
- `const value = Number(storage.getItem(KEY_PREFIX + key))` — const, line 38
- `const store = storage as Storage` — const, line 67
- `const doomed: string[] = []` — const, line 68
- `const key = store.key(i)` — const, line 70

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/useAttemptClock|src/screens/useAttemptClock.ts]] — import-or-re-export: `ActiveStorage`, `attemptActiveSeconds`, `carriedActiveMs`, `defaultActiveStorage`, `forgetActiveMs`, `keepActiveMs`, `openAttemptClock`, `touchAttempt`; references `ActiveStorage`, `attemptActiveSeconds`, `carriedActiveMs`, `defaultActiveStorage`, `forgetActiveMs`, `keepActiveMs`, `openAttemptClock`, `touchAttempt`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/reader/visitClock|src/screens/reader/visitClock.ts]] — import-or-re-export; imports `VisitClock`, `accrueVisit`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/attemptClock.test.ts](../../../../../../apps/learnloop-tauri/src/screens/attemptClock.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/attemptClock.ts](../../../../../../apps/learnloop-tauri/src/screens/attemptClock.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

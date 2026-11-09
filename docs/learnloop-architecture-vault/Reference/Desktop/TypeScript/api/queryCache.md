---
title: "Desktop module · src/api/queryCache.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.api.queryCache"
language: "TypeScript"
area: "TypeScript/api"
source_path: "apps/learnloop-tauri/src/api/queryCache.ts"
source_paths:
  - "apps/learnloop-tauri/src/api/queryCache.ts"
source_commit: "c684fc493228fc3bdff4b5f6ebcd73d8bf236322"
source_commit_timestamp: "2026-10-12T02:16:24-04:00"
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

# `src/api/queryCache.ts`

Area: [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `QueryKey`, `QueryTag`, `QueryState`, `FetchOptions` and related exports within the desktop's TypeScript/api ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/api/queryCache.ts](../../../../../../apps/learnloop-tauri/src/api/queryCache.ts) |
| Source lines | 295 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `c684fc493228fc3bdff4b5f6ebcd73d8bf236322` |
| Commit timestamp | `2026-10-12T02:16:24-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]]

## Public API

- `export type QueryKey = readonly [command: string, ...args: unknown[]]` — type, line 22
- `export type QueryTag = string` — type, line 23
- `export interface QueryState<T>` — interface, line 25
- `export interface FetchOptions` — interface, line 35
- `export type InvalidateTarget = |` — type, line 47
- `export const EMPTY_STATE: QueryState<never> = Object.freeze(` — const, line 66
- `export function hashKey(key: QueryKey): string` — function, line 88
- `export function isStale(state: QueryState<unknown>, staleAfterMs = 0, now = Date.now()): boolean` — function, line 93
- `export function peek<T>(key: QueryKey): QueryState<T>` — function, line 162
- `export function getOrFetch<T>(key: QueryKey, fetcher: ()` — function, line 171
- `export function setQueryData<T>(key: QueryKey, data: T, tags: readonly QueryTag[] = []): void` — function, line 231
- `export function invalidate(target: InvalidateTarget): void` — function, line 251
- `export function invalidateAll(): void` — function, line 269
- `export function clear(): void` — function, line 275
- `export function subscribe(key: QueryKey, listener: ()` — function, line 289

## Internal implementation anchors

- `interface Entry` — interface, line 52
- `const MAX_ENTRIES = 200` — const, line 64
- `const entries = new Map<string, Entry>()` — const, line 74
- `let generation = 0` — let, line 75
- `function stableStringify(value: unknown): string` — function, line 77
- `const record = value as Record<string, unknown>` — const, line 81
- `const keys = Object.keys(record) .filter((key)` — const, line 82
- `function ensure(key: QueryKey): Entry` — function, line 100
- `const hash = hashKey(key)` — const, line 101
- `let entry = entries.get(hash)` — let, line 102
- `function evictIdleEntries(): void` — function, line 121
- `const idle = [...entries.values()] .filter((entry)` — const, line 123
- `function setState(entry: Entry, next: QueryState<unknown>): void` — function, line 132
- `function sameJson(a: unknown, b: unknown): boolean` — function, line 137
- `function toCommandError(error: unknown): CommandError` — function, line 146
- `function staleStamp(entry: Entry, now: number): number` — function, line 155
- `const inFlight = entry.promise !== null ? entry.promiseStartedAt + 1 : 0` — const, line 157
- `const entry = entries.get(hashKey(key))` — const, line 163
- `const entry = ensure(key)` — const, line 172
- `const state = entry.state as QueryState<T>` — const, line 175
- `const startedAt = Math.max(Date.now(), state.invalidatedAt)` — const, line 181
- `const startedIn = generation` — const, line 182
- `const promise: Promise<T> = fetcher() .then( (result)` — const, line 184
- `const current = entry.state as QueryState<T>` — const, line 190
- `const keepReference = entry.listeners.size > 0 && current.data !== undefined && sameJson(current.data, result)` — const, line 193
- `const data = keepReference ? (current.data as T) : result` — const, line 195
- `const followUp = current.invalidatedAt > startedAt` — const, line 201
- `const entry = ensure(key)` — const, line 232
- `function markStale(entry: Entry, now: number): void` — function, line 243
- `const now = Date.now()` — const, line 252
- `const matches = (entry: Entry): boolean` — const, line 253
- `const now = Date.now()` — const, line 270
- `const now = Date.now()` — const, line 277
- `const entry = ensure(key)` — const, line 290

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export: `QueryTag`, `invalidate`, `invalidateAll`, `setQueryData`; references `QueryTag`, `invalidate`, `invalidateAll`, `setQueryData`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export: `EMPTY_STATE`, `FetchOptions`, `QueryKey`, `QueryState`, `QueryTag`, `getOrFetch`, `hashKey`, `isStale`, `peek`, `subscribe`; references `EMPTY_STATE`, `FetchOptions`, `QueryKey`, `QueryState`, `QueryTag`, `getOrFetch`, `hashKey`, `isStale`, `peek`, `subscribe`
- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `clearQueryCache`, `invalidateAllQueries`; references `clearQueryCache`, `invalidateAllQueries`
- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export: `QueryKey`, `getOrFetch`, `hashKey`, `isStale`, `peek`; references `QueryKey`, `getOrFetch`, `hashKey`, `isStale`, `peek`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export: `QueryKey`, `getOrFetch`, `hashKey`, `invalidate`, `isStale`, `peek`; references `QueryKey`, `getOrFetch`, `hashKey`, `invalidate`, `isStale`, `peek`
- [[Reference/Desktop/TypeScript/components/DiagnosisCard|src/components/DiagnosisCard.tsx]] — import-or-re-export: `invalidate`; references `invalidate`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export: `invalidate`; references `invalidate`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `setQueryData`; references `setQueryData`
- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `peek`; references `peek`
- [[Reference/Desktop/TypeScript/screens/reader/NotesGapsSettings|src/screens/reader/NotesGapsSettings.tsx]] — import-or-re-export: `invalidate`; references `invalidate`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderCorrespondenceSettings|src/screens/reader/ReaderCorrespondenceSettings.tsx]] — import-or-re-export: `invalidate`; references `invalidate`
- [[Reference/Desktop/TypeScript/screens/reader/guidePlan|src/screens/reader/guidePlan.ts]] — import-or-re-export: `QueryKey`, `peek`; references `QueryKey`, `peek`
- [[Reference/Desktop/TypeScript/screens/reader/readerCache|src/screens/reader/readerCache.ts]] — import-or-re-export: `QueryKey`, `QueryTag`, `getOrFetch`; references `QueryKey`, `QueryTag`, `getOrFetch`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`, `getCommandError`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Adapter Architecture#Sidecar structure|sidecar structure]] — owns the four-layer RPC contract.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/today/SomethingElse.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/today/SomethingElse.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/retryWiring.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/retryWiring.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/guidePlan.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/guidePlan.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/feedback/HypothesisMarks.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/feedback/HypothesisMarks.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/classicErrors.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/classicErrors.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/TodayScreen.suggestion.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/TodayScreen.suggestion.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/TodayScreen.plan.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/TodayScreen.plan.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Add or change an RPC in all four layers: DTO, client facade, Rust command/registration, and Python sidecar handler/registry.
- Preserve camelCase wire names and typed error behavior; exercise `tests/test_desktop_rpc_contract.py` plus the feature's sidecar tests.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/api/queryCache.ts](../../../../../../apps/learnloop-tauri/src/api/queryCache.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

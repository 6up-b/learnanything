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
source_commit: "79969fe3eace6b6fb77d673b17b32ab85b49ad7f"
source_commit_timestamp: "2026-09-03T10:56:04-07:00"
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
| Source lines | 279 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `79969fe3eace6b6fb77d673b17b32ab85b49ad7f` |
| Commit timestamp | `2026-09-03T10:56:04-07:00` |

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
- `export const EMPTY_STATE: QueryState<never> = Object.freeze(` — const, line 64
- `export function hashKey(key: QueryKey): string` — function, line 86
- `export function isStale(state: QueryState<unknown>, staleAfterMs = 0, now = Date.now()): boolean` — function, line 91
- `export function peek<T>(key: QueryKey): QueryState<T>` — function, line 153
- `export function getOrFetch<T>(key: QueryKey, fetcher: ()` — function, line 162
- `export function setQueryData<T>(key: QueryKey, data: T, tags: readonly QueryTag[] = []): void` — function, line 215
- `export function invalidate(target: InvalidateTarget): void` — function, line 235
- `export function invalidateAll(): void` — function, line 253
- `export function clear(): void` — function, line 259
- `export function subscribe(key: QueryKey, listener: ()` — function, line 273

## Internal implementation anchors

- `interface Entry` — interface, line 52
- `const MAX_ENTRIES = 200` — const, line 62
- `const entries = new Map<string, Entry>()` — const, line 72
- `let generation = 0` — let, line 73
- `function stableStringify(value: unknown): string` — function, line 75
- `const record = value as Record<string, unknown>` — const, line 79
- `const keys = Object.keys(record) .filter((key)` — const, line 80
- `function ensure(key: QueryKey): Entry` — function, line 98
- `const hash = hashKey(key)` — const, line 99
- `let entry = entries.get(hash)` — let, line 100
- `function evictIdleEntries(): void` — function, line 118
- `const idle = [...entries.values()] .filter((entry)` — const, line 120
- `function setState(entry: Entry, next: QueryState<unknown>): void` — function, line 129
- `function sameJson(a: unknown, b: unknown): boolean` — function, line 134
- `function toCommandError(error: unknown): CommandError` — function, line 143
- `function staleStamp(state: QueryState<unknown>, now: number): number` — function, line 148
- `const entry = entries.get(hashKey(key))` — const, line 154
- `const entry = ensure(key)` — const, line 163
- `const state = entry.state as QueryState<T>` — const, line 166
- `const startedAt = Date.now()` — const, line 170
- `const startedIn = generation` — const, line 171
- `const promise: Promise<T> = fetcher() .then( (result)` — const, line 173
- `const current = entry.state as QueryState<T>` — const, line 179
- `const keepReference = entry.listeners.size > 0 && current.data !== undefined && sameJson(current.data, result)` — const, line 182
- `const data = keepReference ? (current.data as T) : result` — const, line 184
- `const entry = ensure(key)` — const, line 216
- `function markStale(entry: Entry, now: number): void` — function, line 227
- `const now = Date.now()` — const, line 236
- `const matches = (entry: Entry): boolean` — const, line 237
- `const now = Date.now()` — const, line 254
- `const now = Date.now()` — const, line 261
- `const entry = ensure(key)` — const, line 274

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export: `QueryTag`, `invalidate`, `invalidateAll`, `setQueryData`; references `QueryTag`, `invalidate`, `invalidateAll`, `setQueryData`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export: `EMPTY_STATE`, `FetchOptions`, `QueryKey`, `QueryState`, `QueryTag`, `getOrFetch`, `hashKey`, `isStale`, `peek`, `subscribe`; references `EMPTY_STATE`, `FetchOptions`, `QueryKey`, `QueryState`, `QueryTag`, `getOrFetch`, `hashKey`, `isStale`, `peek`, `subscribe`
- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `clearQueryCache`, `invalidateAllQueries`; references `clearQueryCache`, `invalidateAllQueries`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export: `invalidate`; references `invalidate`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `QueryKey`, `getOrFetch`; references `QueryKey`, `getOrFetch`

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

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck`, `npm test` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Add or change an RPC in all four layers: DTO, client facade, Rust command/registration, and Python sidecar handler/registry.
- Preserve camelCase wire names and typed error behavior; exercise `tests/test_desktop_rpc_contract.py` plus the feature's sidecar tests.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/api/queryCache.ts](../../../../../../apps/learnloop-tauri/src/api/queryCache.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

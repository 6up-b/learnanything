---
title: "Desktop module · src/api/useCachedQuery.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.api.useCachedQuery"
language: "TypeScript"
area: "TypeScript/api"
source_path: "apps/learnloop-tauri/src/api/useCachedQuery.ts"
source_paths:
  - "apps/learnloop-tauri/src/api/useCachedQuery.ts"
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

# `src/api/useCachedQuery.ts`

Area: [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `CachedQuery`, `CachedQueryOptions`, `useCachedQuery`, `useReportQueryError` within the desktop's TypeScript/api ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/api/useCachedQuery.ts](../../../../../../apps/learnloop-tauri/src/api/useCachedQuery.ts) |
| Source lines | 162 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] → [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]]

## Public API

- `export interface CachedQuery<T>` — interface, line 17
- `export interface CachedQueryOptions` — interface, line 52
- `export function useCachedQuery<T>( key: QueryKey | null, fetcher: ()` — function, line 69
- `export function useReportQueryError( query: Pick<CachedQuery<unknown>, "error" | "retryReport">, onError: (message: string, report?: ErrorReport)` — function, line 147

## Internal implementation anchors

- `type FetchOptions, type QueryKey, type QueryState, type QueryTag } from "./queryCache"` — type, line 11
- `type QueryKey, type QueryState, type QueryTag } from "./queryCache"` — type, line 12
- `type QueryState, type QueryTag } from "./queryCache"` — type, line 13
- `type QueryTag } from "./queryCache"` — type, line 14
- `const enabled = options.enabled ?? true` — const, line 74
- `const hash = key ? hashKey(key) : null` — const, line 75
- `const keyRef = useRef(key)` — const, line 76
- `const fetcherRef = useRef(fetcher)` — const, line 78
- `const optionsRef = useRef(options)` — const, line 80
- `const enabledRef = useRef(enabled)` — const, line 82
- `const subscribeToKey = useCallback( (listener: ()` — const, line 85
- `const getSnapshot = useCallback( (): QueryState<T>` — const, line 89
- `const state = useSyncExternalStore(subscribeToKey, getSnapshot)` — const, line 93
- `const start = useCallback( (force: boolean): Promise<T | undefined>` — const, line 95
- `const current = keyRef.current` — const, line 97
- `const fetchOptions: FetchOptions =` — const, line 101
- `const refetch = useCallback(()` — const, line 121
- `const retryReport = useCallback(():` — const, line 122
- `const failedKey = keyRef.current` — const, line 123
- `const fetcherNow = fetcherRef.current` — const, line 125
- `const loading = enabled && hash !== null && state.data === undefined && state.error === null` — const, line 133
- `const stale = state.data !== undefined && (state.fetching || isStale(state, optionsRef.current.staleAfterMs))` — const, line 134
- `const refreshing = state.data !== undefined && state.fetching && state.invalidatedAt > state.updatedAt` — const, line 135
- `const queryRef = useRef(query)` — const, line 154
- `const error = query.error` — const, line 156
- `const report = queryRef.current.retryReport()` — const, line 159

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/components/SourceLibrarySidebar|src/components/SourceLibrarySidebar.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export: `useCachedQuery`, `useReportQueryError`; references `useCachedQuery`, `useReportQueryError`
- [[Reference/Desktop/TypeScript/screens/LibraryPlace|src/screens/LibraryPlace.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] — import-or-re-export: `useCachedQuery`, `useReportQueryError`; references `useCachedQuery`, `useReportQueryError`
- [[Reference/Desktop/TypeScript/screens/MaintenanceScreen|src/screens/MaintenanceScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/RegistryReviewScreen|src/screens/RegistryReviewScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/underhood/tools|src/screens/underhood/tools.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export; imports `EMPTY_STATE`, `FetchOptions`, `QueryKey`, `QueryState`, `QueryTag`, `getOrFetch`, `hashKey`, `isStale`, `peek`, `subscribe`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `ErrorReport`, `NoticeRetry`, `RETRY_RAN`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Adapter Architecture#Sidecar structure|sidecar structure]] — owns the four-layer RPC contract.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/api/useCachedQuery.test.tsx](../../../../../../apps/learnloop-tauri/src/api/useCachedQuery.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Add or change an RPC in all four layers: DTO, client facade, Rust command/registration, and Python sidecar handler/registry.
- Preserve camelCase wire names and typed error behavior; exercise `tests/test_desktop_rpc_contract.py` plus the feature's sidecar tests.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/api/useCachedQuery.ts](../../../../../../apps/learnloop-tauri/src/api/useCachedQuery.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

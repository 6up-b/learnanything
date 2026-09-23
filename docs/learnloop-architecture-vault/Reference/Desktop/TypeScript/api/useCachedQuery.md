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

# `src/api/useCachedQuery.ts`

Area: [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `CachedQuery`, `CachedQueryOptions`, `useCachedQuery` within the desktop's TypeScript/api ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/api/useCachedQuery.ts](../../../../../../apps/learnloop-tauri/src/api/useCachedQuery.ts) |
| Source lines | 104 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] → [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]]

## Public API

- `export interface CachedQuery<T>` — interface, line 16
- `export interface CachedQueryOptions` — interface, line 33
- `export function useCachedQuery<T>( key: QueryKey | null, fetcher: ()` — function, line 50

## Internal implementation anchors

- `type FetchOptions, type QueryKey, type QueryState, type QueryTag } from "./queryCache"` — type, line 10
- `type QueryKey, type QueryState, type QueryTag } from "./queryCache"` — type, line 11
- `type QueryState, type QueryTag } from "./queryCache"` — type, line 12
- `type QueryTag } from "./queryCache"` — type, line 13
- `const enabled = options.enabled ?? true` — const, line 55
- `const hash = key ? hashKey(key) : null` — const, line 56
- `const keyRef = useRef(key)` — const, line 57
- `const fetcherRef = useRef(fetcher)` — const, line 59
- `const optionsRef = useRef(options)` — const, line 61
- `const subscribeToKey = useCallback( (listener: ()` — const, line 64
- `const getSnapshot = useCallback( (): QueryState<T>` — const, line 68
- `const state = useSyncExternalStore(subscribeToKey, getSnapshot)` — const, line 72
- `const start = useCallback( (force: boolean): Promise<T>` — const, line 74
- `const current = keyRef.current` — const, line 76
- `const fetchOptions: FetchOptions =` — const, line 78
- `const refetch = useCallback(()` — const, line 98
- `const loading = enabled && hash !== null && state.data === undefined && state.error === null` — const, line 100
- `const stale = state.data !== undefined && (state.fetching || isStale(state, optionsRef.current.staleAfterMs))` — const, line 101
- `const refreshing = state.data !== undefined && state.fetching && state.invalidatedAt > state.updatedAt` — const, line 102

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/SourceLibrarySidebar|src/components/SourceLibrarySidebar.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/MaintenanceScreen|src/screens/MaintenanceScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/RegistryReviewScreen|src/screens/RegistryReviewScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `useCachedQuery`; references `useCachedQuery`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export; imports `EMPTY_STATE`, `FetchOptions`, `QueryKey`, `QueryState`, `QueryTag`, `getOrFetch`, `hashKey`, `isStale`, `peek`, `subscribe`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

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

1. Modify [apps/learnloop-tauri/src/api/useCachedQuery.ts](../../../../../../apps/learnloop-tauri/src/api/useCachedQuery.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

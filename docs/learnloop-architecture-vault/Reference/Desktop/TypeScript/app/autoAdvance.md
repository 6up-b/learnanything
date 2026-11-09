---
title: "Desktop module · src/app/autoAdvance.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.autoAdvance"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/autoAdvance.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/autoAdvance.ts"
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

# `src/app/autoAdvance.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `todayQueueInput`, `todayQueueKey`, `queueHead`, `NextQueueItem` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/autoAdvance.ts](../../../../../../apps/learnloop-tauri/src/app/autoAdvance.ts) |
| Source lines | 97 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]]

## Public API

- `export function todayQueueInput(session: SessionSnapshot | null): QueueInput` — function, line 20
- `export function todayQueueKey(input: QueueInput): QueryKey` — function, line 28
- `export function queueHead(snapshot: QueueSnapshot | null | undefined): ScheduledItemDto | null` — function, line 33
- `export interface NextQueueItem` — interface, line 40
- `export function useNextQueueItem(input: QueueInput | null, prefetch: boolean): NextQueueItem` — function, line 59

## Internal implementation anchors

- `const MAX_HEAD_READS = 4` — const, line 17
- `const hash = input ? hashKey(todayQueueKey(input)) : null` — const, line 61
- `const key = useMemo(()` — const, line 63
- `const query = useCachedQuery<QueueSnapshot>( prefetch ? key : null, ()` — const, line 64
- `const current = query.data !== undefined && !query.refreshing` — const, line 70
- `const head = current ? queueHead(query.data) : null` — const, line 71
- `const empty = current && head === null` — const, line 72
- `const resolve = useCallback(async (): Promise<ScheduledItemDto | null>` — const, line 74
- `const snapshot = await getOrFetch<QueueSnapshot>(key, ()` — const, line 83
- `const state = peek<QueueSnapshot>(key)` — const, line 87

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `todayQueueInput`; references `todayQueueInput`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `useNextQueueItem`; references `useNextQueueItem`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `todayQueueInput`; references `todayQueueInput`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `todayQueueInput`; references `todayQueueInput`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `QueueInput`, `QueueSnapshot`, `ScheduledItemDto`, `SessionSnapshot`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export; imports `QueryKey`, `getOrFetch`, `hashKey`, `isStale`, `peek`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/app/autoAdvance.test.tsx](../../../../../../apps/learnloop-tauri/src/app/autoAdvance.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/autoAdvance.ts](../../../../../../apps/learnloop-tauri/src/app/autoAdvance.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

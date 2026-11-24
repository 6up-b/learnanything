---
title: "Desktop module · src/screens/reader/useCueDiscovery.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.useCueDiscovery"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/useCueDiscovery.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/useCueDiscovery.ts"
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

# `src/screens/reader/useCueDiscovery.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `DISCOVERY_POLL_MS`, `DISCOVERY_MAX_READS`, `DISCOVERY_MAX_REASKS`, `TARGETS_PENDING_POLL_MS` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useCueDiscovery.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useCueDiscovery.ts) |
| Source lines | 198 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/source/types|src/screens/desks/source/types.ts]] → [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] → [[Reference/Desktop/TypeScript/screens/reader/useCueDiscovery|src/screens/reader/useCueDiscovery.ts]]

## Public API

- `export const DISCOVERY_POLL_MS: readonly number[] = [1_500, 3_000, 5_000, 10_000]` — const, line 44
- `export const DISCOVERY_MAX_READS = 60` — const, line 46
- `export const DISCOVERY_MAX_REASKS = 3` — const, line 48
- `export const TARGETS_PENDING_POLL_MS = 4_000` — const, line 50
- `export const TARGETS_PENDING_POLL_MAX_MS = 60_000` — const, line 51
- `export interface CueDiscoveryInput` — interface, line 53
- `export function useCueDiscovery(` — function, line 71

## Internal implementation anchors

- `function foundSomething(job: ReaderCueDiscoveryJobDto): boolean` — function, line 67
- `const whenLive = useWhenLive()` — const, line 72
- `const askedRef = useRef<Map<string, string>>(new Map())` — const, line 74
- `const reasksRef = useRef<Map<string, number>>(new Map())` — const, line 76
- `const reloadRef = useRef(reloadGuidePlan)` — const, line 78
- `const targetsKey = discovery?.targetsKey ?? null` — const, line 80
- `const targetsPending = Boolean(discovery?.targetsPending)` — const, line 81
- `const openKey = openKeyInput === undefined ? extractionId : openKeyInput` — const, line 82
- `const openRef = useRef<` — const, line 85
- `const openId = openRef.current?.id ?? null` — const, line 91
- `const paused = openId !== null && !extractionId` — const, line 93
- `const pausedRef = useRef(paused)` — const, line 94
- `const runningRef = useRef<Set<()` — const, line 98
- `const running = runningRef.current` — const, line 100
- `let cancelled = false` — let, line 111
- `let done = false` — let, line 112
- `let timer: ReturnType<typeof setTimeout> | null = null` — let, line 113
- `const stop = ()` — const, line 114
- `const finish = (job: ReaderCueDiscoveryJobDto)` — const, line 120
- `const answered = job.result?.targetsKey ?? null` — const, line 126
- `const stale = job.result?.status === "cancelled" || (answered !== null && answered !== targetsKey)` — const, line 127
- `const key = `$` — const, line 128
- `const asked = reasksRef.current.get(key) ?? 0` — const, line 129
- `const read = (jobId: string, reads: number)` — const, line 136
- `const pause = DISCOVERY_POLL_MS[Math.min(reads, DISCOVERY_POLL_MS.length - 1)]` — const, line 141
- `let cancelled = false` — let, line 178
- `let delay = TARGETS_PENDING_POLL_MS` — let, line 179
- `let timer: ReturnType<typeof setTimeout> | null = null` — let, line 180
- `const poll = ()` — const, line 181

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] — import-or-re-export: `useCueDiscovery`; references `useCueDiscovery`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderCueDiscoveryDto`, `ReaderCueDiscoveryJobDto`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export; imports `newActivityId`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/rw3bReview.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/rw3bReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/pausedProducers.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/pausedProducers.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/useCueDiscovery.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useCueDiscovery.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

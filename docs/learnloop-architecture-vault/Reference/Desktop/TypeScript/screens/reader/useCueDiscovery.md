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
source_commit: "1455cbf292f09ea73c24f9a2b8519d39570bf336"
source_commit_timestamp: "2026-10-20T15:48:24-04:00"
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
| Source lines | 138 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `1455cbf292f09ea73c24f9a2b8519d39570bf336` |
| Commit timestamp | `2026-10-20T15:48:24-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] → [[Reference/Desktop/TypeScript/screens/reader/useCueDiscovery|src/screens/reader/useCueDiscovery.ts]]

## Public API

- `export const DISCOVERY_POLL_MS: readonly number[] = [1_500, 3_000, 5_000, 10_000]` — const, line 33
- `export const DISCOVERY_MAX_READS = 60` — const, line 35
- `export const DISCOVERY_MAX_REASKS = 3` — const, line 37
- `export const TARGETS_PENDING_POLL_MS = 4_000` — const, line 39
- `export const TARGETS_PENDING_POLL_MAX_MS = 60_000` — const, line 40
- `export interface CueDiscoveryInput` — interface, line 42
- `export function useCueDiscovery(` — function, line 54

## Internal implementation anchors

- `function foundSomething(job: ReaderCueDiscoveryJobDto): boolean` — function, line 50
- `const askedRef = useRef<Map<string, string>>(new Map())` — const, line 56
- `const reasksRef = useRef<Map<string, number>>(new Map())` — const, line 58
- `const reloadRef = useRef(reloadGuidePlan)` — const, line 60
- `const targetsKey = discovery?.targetsKey ?? null` — const, line 62
- `const targetsPending = Boolean(discovery?.targetsPending)` — const, line 63
- `const openRef = useRef<` — const, line 65
- `let cancelled = false` — let, line 74
- `let done = false` — let, line 75
- `let timer: ReturnType<typeof setTimeout> | null = null` — let, line 76
- `const finish = (job: ReaderCueDiscoveryJobDto)` — const, line 77
- `const answered = job.result?.targetsKey ?? null` — const, line 82
- `const stale = job.result?.status === "cancelled" || (answered !== null && answered !== targetsKey)` — const, line 83
- `const key = `$` — const, line 84
- `const asked = reasksRef.current.get(key) ?? 0` — const, line 85
- `const read = (jobId: string, reads: number)` — const, line 92
- `const pause = DISCOVERY_POLL_MS[Math.min(reads, DISCOVERY_POLL_MS.length - 1)]` — const, line 94
- `const sourceOpenId = openRef.current?.id ?? `copen_$` — const, line 102
- `let cancelled = false` — let, line 119
- `let delay = TARGETS_PENDING_POLL_MS` — let, line 120
- `let timer: ReturnType<typeof setTimeout> | null = null` — let, line 121
- `const poll = ()` — const, line 122

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] — import-or-re-export: `useCueDiscovery`; references `useCueDiscovery`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderCueDiscoveryDto`, `ReaderCueDiscoveryJobDto`
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

---
title: "Desktop module · src/screens/reader/useActiveReading.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.useActiveReading"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/useActiveReading.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/useActiveReading.ts"
source_commit: "0e255d2058e29d8da9f7b21dee8d80e7a7889dbe"
source_commit_timestamp: "2026-11-01T08:39:53-05:00"
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

# `src/screens/reader/useActiveReading.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `AnotherWayHit`, `ActiveReadingState`, `AnotherWayState`, `UNDONE_EARLIER` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useActiveReading.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useActiveReading.ts) |
| Source lines | 345 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `0e255d2058e29d8da9f7b21dee8d80e7a7889dbe` |
| Commit timestamp | `2026-11-01T08:39:53-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useActiveReading|src/screens/reader/useActiveReading.ts]]

## Public API

- `export interface AnotherWayHit` — interface, line 30
- `export interface ActiveReadingState` — interface, line 40
- `export interface AnotherWayState` — interface, line 61
- `export const UNDONE_EARLIER = "You undid this reconstruction earlier, so it won't be asked."` — const, line 72
- `export function anotherWayOutcome(status: unknown):` — function, line 77
- `export function useActiveReading(` — function, line 92
- `export type ActiveReadingController = ReturnType<typeof useActiveReading>` — type, line 345

## Internal implementation anchors

- `const POLL_MS = 2000` — const, line 28
- `const NO_RECONSTRUCT =` — const, line 70
- `const NO_PRACTICE =` — const, line 71
- `const value = typeof status === "string" ? status : "ok"` — const, line 78
- `const why = value.includes(":") ? value.slice(value.indexOf(":") + 1).trim() : value` — const, line 80
- `function failureLine(code: string | null | undefined, message: string | null | undefined): string` — function, line 86
- `const keyRef = useRef(0)` — const, line 112
- `const activeRef = useRef<ActiveReadingState | null>(null)` — const, line 113
- `const anotherRef = useRef<AnotherWayState | null>(null)` — const, line 115
- `const update = useCallback((key: number, patch: Partial<ActiveReadingState>)` — const, line 118
- `const commitReconstruct = useCallback(async (key: number, question: ReaderActiveQuestionDto)` — const, line 122
- `const made = await api.readerReconstruct(` — const, line 134
- `const code = getCommandError(error)?.code` — const, line 137
- `const landed = useCallback((key: number, question: ReaderActiveQuestionDto)` — const, line 153
- `const start = useCallback(async (style: ReaderActiveStyle, spanIds: string[], localFold: string[])` — const, line 159
- `const key = ++keyRef.current` — const, line 161
- `const asked = await api.readerActiveQuestion(` — const, line 170
- `const code = getCommandError(error)?.code` — const, line 178
- `const pendingKey = active && active.phase === "pending" && active.batchId ? active.key : null` — const, line 185
- `const current = activeRef.current` — const, line 187
- `const timer = window.setTimeout(async ()` — const, line 190
- `const read = await api.readerActiveQuestionStatus(` — const, line 192
- `const code = read.job.errorCode ?? null` — const, line 199
- `const act = useCallback(async (input:` — const, line 214
- `const current = activeRef.current` — const, line 215
- `const key = current.key` — const, line 217
- `const result = await api.readerActiveQuestionAction(` — const, line 220
- `const answer = useCallback((response: string)` — const, line 234
- `const showMe = useCallback(()` — const, line 235
- `const selfCheck = useCallback((value: InquirySelfCheck)` — const, line 236
- `const dismiss = useCallback(()` — const, line 237
- `const unfold = useCallback(()` — const, line 241
- `const current = activeRef.current` — const, line 242
- `const close = useCallback(()` — const, line 245
- `const retry = useCallback(()` — const, line 249
- `const current = activeRef.current` — const, line 250
- `const addToPractice = useCallback(async ()` — const, line 255
- `const current = activeRef.current` — const, line 256
- `const question = current?.question` — const, line 257
- `const key = current.key` — const, line 259
- `const made = await api.readerEscalateAuthoredQuestion(` — const, line 262
- `const undoReconstruct = useCallback(async ()` — const, line 273
- `const current = activeRef.current` — const, line 274
- `const key = current.key` — const, line 276
- `const undone = await api.readerReconstructUndo(` — const, line 278
- `const anotherWay = useCallback(async (quote: string, spanIds: string[])` — const, line 286
- `const key = ++keyRef.current` — const, line 288
- `const found = await api.findSources(` — const, line 293
- `const outcome = anotherWayOutcome(found.status)` — const, line 298
- `const hits = ((found.hits as Array<Record<string, unknown>> | undefined) ?? []).slice(0, 2).map((hit)` — const, line 303
- `const retryAnother = useCallback(()` — const, line 314
- `const current = anotherRef.current` — const, line 315
- `const closeAnother = useCallback(()` — const, line 319
- `const readingKey = openKey === undefined ? extractionId : openKey` — const, line 326
- `const setDraft = useCallback((text: string)` — const, line 333
- `const current = activeRef.current` — const, line 334
- `const folded = new Set(active && !active.foldOpen ? active.foldedSpanIds : [])` — const, line 338

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `useActiveReading`; references `useActiveReading`
- [[Reference/Desktop/TypeScript/screens/reader/ActiveReadingCard|src/screens/reader/ActiveReadingCard.tsx]] — import-or-re-export: `ActiveReadingController`; references `ActiveReadingController`
- [[Reference/Desktop/TypeScript/screens/reader/useSidePane|src/screens/reader/useSidePane.ts]] — import-or-re-export: `useActiveReading`; references `useActiveReading`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `InquirySelfCheck`, `ReaderActiveQuestionDto`, `ReaderActiveStyle`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/reader/ModelActionState|src/screens/reader/ModelActionState.tsx]] — import-or-re-export; imports `ModelActionPhase`, `phaseForError`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `passageKeys`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

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

1. Modify [apps/learnloop-tauri/src/screens/reader/useActiveReading.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useActiveReading.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/screens/reader/useSideBySide.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.useSideBySide"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/useSideBySide.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/useSideBySide.ts"
source_commit: "952a54d9d4963ef00dd1d49410b4a92eba28f51d"
source_commit_timestamp: "2026-10-31T22:15:39-04:00"
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

# `src/screens/reader/useSideBySide.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `SIDE_BY_SIDE_COPY`, `SIDE_BY_SIDE_SCROLL_KEYS`, `MainPane`, `CurrentEntry` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useSideBySide.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useSideBySide.ts) |
| Source lines | 530 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `952a54d9d4963ef00dd1d49410b4a92eba28f51d` |
| Commit timestamp | `2026-10-31T22:15:39-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useSideBySide|src/screens/reader/useSideBySide.ts]]

## Public API

- `export const SIDE_BY_SIDE_COPY =` — const, line 38
- `export const SIDE_BY_SIDE_SCROLL_KEYS: ReadonlySet<string> = new Set(["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " "])` — const, line 56
- `export interface MainPane` — interface, line 59
- `export interface CurrentEntry` — interface, line 67
- `export interface SideBySideInput` — interface, line 76
- `export type SideBySideVia = "find_list" | "also_list" | "peek" | "key"` — type, line 95
- `export interface SideBySide` — interface, line 121
- `export function useSideBySide(` — function, line 164

## Internal implementation anchors

- `type EndedBy = "close" | "walked_off" | "replaced" | "source" | "switch_off"` — type, line 97
- `interface Pair` — interface, line 99
- `interface LastFollow` — interface, line 113
- `function useNarrow(active: boolean): boolean` — function, line 152
- `const onResize = ()` — const, line 156
- `const narrow = useNarrow(enabled)` — const, line 167
- `const pairRef = useRef<Pair | null>(null)` — const, line 179
- `const setPair = useCallback((next: Pair | null)` — const, line 180
- `const leaderRef = useRef<Pane>("main")` — const, line 184
- `const mainRef = useRef<MainPane | null>(main)` — const, line 186
- `const enabledRef = useRef(enabled)` — const, line 188
- `const sectionRef = useRef<SideBySideSectionDto | null>(null)` — const, line 190
- `const currentEntryRef = useRef<CurrentEntry | null>(currentEntry)` — const, line 192
- `const visitRef = useRef(visitPayload)` — const, line 194
- `const loadToken = useRef(0)` — const, line 196
- `const crossing = useRef(0)` — const, line 197
- `const opening = useRef(0)` — const, line 199
- `const pendingOpen = useRef(0)` — const, line 201
- `const narrowRef = useRef(narrow)` — const, line 202
- `const lastFollow = useRef<LastFollow | null>(null)` — const, line 204
- `const sideScroll = useRef<` — const, line 206
- `const visit = ()` — const, line 208
- `const load = useCallback((target: PaneTarget)` — const, line 210
- `const mine = ++loadToken.current` — const, line 211
- `const logEnded = useCallback((ended: Pair, via: EndedBy)` — const, line 226
- `const reset = useCallback((via: EndedBy)` — const, line 235
- `const ended = pairRef.current` — const, line 236
- `const start = useCallback((target: PaneTarget, entryId: string | null, sheet: boolean, mainSourceId: string): Pair` — const, line 253
- `const previous = pairRef.current` — const, line 254
- `const next: Pair =` — const, line 260
- `const open = useCallback((target: PaneTarget, via: SideBySideVia)` — const, line 271
- `const here = mainRef.current` — const, line 272
- `const sheet = narrowRef.current` — const, line 276
- `const label = crumbLabel(target)` — const, line 277
- `const current = pairRef.current` — const, line 278
- `let entryId: string | null = null` — let, line 279
- `const onItsCrumb = current && !current.sheet && current.entryId && current.entryId === currentEntryRef.current?.id` — const, line 283
- `const opened = start(target, entryId, sheet, here.sourceId)` — const, line 288
- `const close = useCallback(()` — const, line 304
- `const current = pairRef.current` — const, line 305
- `const openFirst = useCallback(async ()` — const, line 311
- `const here = mainRef.current` — const, line 312
- `const mine = ++pendingOpen.current` — const, line 314
- `let view: CorrespondentsDto` — let, line 315
- `const first = firstCorrespondent(view)` — const, line 326
- `const touch = useCallback((pane: Pane)` — const, line 334
- `const followFrom = useCallback(async (from: Pane, extractionId: string, sectionId: string)` — const, line 348
- `const current = pairRef.current` — const, line 349
- `const here = mainRef.current` — const, line 350
- `const mine = ++crossing.current` — const, line 352
- `const openedAs = opening.current` — const, line 353
- `const followerSource = from === "main" ? current.target.sourceId : here.sourceId` — const, line 354
- `let view: CorrespondentsDto | null = null` — let, line 355
- `const now = pairRef.current` — const, line 365
- `const hit = firstJudgedIn(view, followerSource)` — const, line 367
- `const follower: Pane = from === "main" ? "side" : "main"` — const, line 368
- `const target = targetOf(hit)` — const, line 373
- `let fromSectionId: string | null` — let, line 374
- `const noteManualMove = useCallback((pane: Pane, sectionId: string)` — const, line 405
- `const moved = lastFollow.current` — const, line 406
- `const lastMainSection = useRef<string | null>(main?.sectionId ?? null)` — const, line 418
- `const sectionId = main?.sectionId ?? null` — const, line 420
- `const previous = lastMainSection.current` — const, line 421
- `const goSide = useCallback((sectionId: string)` — const, line 430
- `const current = pairRef.current` — const, line 431
- `const target: PaneTarget =` — const, line 435
- `const toggleFollow = useCallback(()` — const, line 442
- `const mainSource = main?.sourceId ?? null` — const, line 452
- `const current = pairRef.current` — const, line 454
- `const entryId = currentEntry?.id ?? null` — const, line 455
- `const target = currentEntry?.kind === "side_by_side" ? currentEntry.sideBySide ?? null : null` — const, line 457
- `const onCrumb = Boolean(target && entryId && enabled && !narrow && mainSource && currentEntry?.sourceId === mainSource)` — const, line 458
- `const opened = start(target as PaneTarget, entryId, false, mainSource as string)` — const, line 461
- `const here = mainRef.current` — const, line 462
- `const current = pairRef.current` — const, line 480
- `const rememberScroll = useCallback((key: string, top: number)` — const, line 496
- `const scrollFor = useCallback((key: string)` — const, line 499
- `const shownTarget: PaneTarget | null = pair ?` — const, line 502
- `const live = Boolean(enabled && pair)` — const, line 506

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `SIDE_BY_SIDE_COPY`, `SIDE_BY_SIDE_SCROLL_KEYS`, `useSideBySide`; references `SIDE_BY_SIDE_COPY`, `SIDE_BY_SIDE_SCROLL_KEYS`, `useSideBySide`
- [[Reference/Desktop/TypeScript/screens/reader/SideBySidePane|src/screens/reader/SideBySidePane.tsx]] — import-or-re-export: `SIDE_BY_SIDE_COPY`, `SIDE_BY_SIDE_SCROLL_KEYS`, `SideBySide`; references `SIDE_BY_SIDE_COPY`, `SIDE_BY_SIDE_SCROLL_KEYS`, `SideBySide`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CorrespondentsDto`, `SideBySideSectionDto`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export; imports `logReaderAction`, `newActivityId`
- [[Reference/Desktop/TypeScript/screens/reader/correspondenceEvents|src/screens/reader/correspondenceEvents.ts]] — import-or-re-export; imports `logCorrespondentAct`
- [[Reference/Desktop/TypeScript/screens/reader/sideBySide|src/screens/reader/sideBySide.ts]] — import-or-re-export; imports `Pane`, `PaneTarget`, `crumbLabel`, `firstCorrespondent`, `firstJudgedIn`, `isNarrowWindow`, `targetOf`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/useSideBySide.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/useSideBySide.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/sideBySideReader.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/sideBySideCorrespondence.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideCorrespondence.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/useSideBySide.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useSideBySide.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

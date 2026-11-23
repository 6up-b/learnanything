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

Provides `SidePaneDraft`, `SIDE_BY_SIDE_COPY`, `SIDE_BY_SIDE_SCROLL_KEYS`, `MainPane` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useSideBySide.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useSideBySide.ts) |
| Source lines | 552 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useSideBySide|src/screens/reader/useSideBySide.ts]]

## Public API

- `export interface SidePaneDraft` — interface, line 44
- `export const SIDE_BY_SIDE_COPY =` — const, line 50
- `export const SIDE_BY_SIDE_SCROLL_KEYS: ReadonlySet<string> = new Set(["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " "])` — const, line 68
- `export interface MainPane` — interface, line 71
- `export interface CurrentEntry` — interface, line 79
- `export interface SideBySideInput` — interface, line 88
- `export type SideBySideVia = "find_list" | "also_list" | "peek" | "key"` — type, line 107
- `export interface SideBySide` — interface, line 133
- `export function useSideBySide(` — function, line 179

## Internal implementation anchors

- `type EndedBy = "close" | "walked_off" | "replaced" | "source" | "switch_off"` — type, line 109
- `interface Pair` — interface, line 111
- `interface LastFollow` — interface, line 125
- `function useNarrow(active: boolean): boolean` — function, line 167
- `const hub = useListenerHub()` — const, line 169
- `const onResize = ()` — const, line 172
- `const narrow = useNarrow(enabled)` — const, line 182
- `const pairRef = useRef<Pair | null>(null)` — const, line 194
- `const setPair = useCallback((next: Pair | null)` — const, line 195
- `const leaderRef = useRef<Pane>("main")` — const, line 199
- `const mainRef = useRef<MainPane | null>(main)` — const, line 201
- `const enabledRef = useRef(enabled)` — const, line 203
- `const sectionRef = useRef<SideBySideSectionDto | null>(null)` — const, line 205
- `const currentEntryRef = useRef<CurrentEntry | null>(currentEntry)` — const, line 207
- `const visitRef = useRef(visitPayload)` — const, line 209
- `const loadToken = useRef(0)` — const, line 211
- `const crossing = useRef(0)` — const, line 212
- `const opening = useRef(0)` — const, line 214
- `const pendingOpen = useRef(0)` — const, line 216
- `const narrowRef = useRef(narrow)` — const, line 217
- `const lastFollow = useRef<LastFollow | null>(null)` — const, line 219
- `const sideScroll = useRef<` — const, line 221
- `const setDraft = useCallback((update: (current: SidePaneDraft | null)` — const, line 223
- `const visit = ()` — const, line 227
- `const load = useCallback((target: PaneTarget)` — const, line 229
- `const mine = ++loadToken.current` — const, line 230
- `const logEnded = useCallback((ended: Pair, via: EndedBy)` — const, line 245
- `const reset = useCallback((via: EndedBy)` — const, line 254
- `const ended = pairRef.current` — const, line 255
- `const start = useCallback((target: PaneTarget, entryId: string | null, sheet: boolean, mainSourceId: string): Pair` — const, line 273
- `const previous = pairRef.current` — const, line 274
- `const next: Pair =` — const, line 280
- `const open = useCallback((target: PaneTarget, via: SideBySideVia)` — const, line 291
- `const here = mainRef.current` — const, line 292
- `const sheet = narrowRef.current` — const, line 296
- `const label = crumbLabel(target)` — const, line 297
- `const current = pairRef.current` — const, line 298
- `let entryId: string | null = null` — let, line 299
- `const onItsCrumb = current && !current.sheet && current.entryId && current.entryId === currentEntryRef.current?.id` — const, line 303
- `const opened = start(target, entryId, sheet, here.sourceId)` — const, line 308
- `const close = useCallback(()` — const, line 324
- `const current = pairRef.current` — const, line 325
- `const openFirst = useCallback(async ()` — const, line 331
- `const here = mainRef.current` — const, line 332
- `const mine = ++pendingOpen.current` — const, line 334
- `let view: CorrespondentsDto` — let, line 335
- `const first = firstCorrespondent(view)` — const, line 346
- `const touch = useCallback((pane: Pane)` — const, line 354
- `const followFrom = useCallback(async (from: Pane, extractionId: string, sectionId: string)` — const, line 368
- `const current = pairRef.current` — const, line 369
- `const here = mainRef.current` — const, line 370
- `const mine = ++crossing.current` — const, line 372
- `const openedAs = opening.current` — const, line 373
- `const followerSource = from === "main" ? current.target.sourceId : here.sourceId` — const, line 374
- `let view: CorrespondentsDto | null = null` — let, line 375
- `const now = pairRef.current` — const, line 385
- `const hit = firstJudgedIn(view, followerSource)` — const, line 387
- `const follower: Pane = from === "main" ? "side" : "main"` — const, line 388
- `const target = targetOf(hit)` — const, line 393
- `let fromSectionId: string | null` — let, line 394
- `const noteManualMove = useCallback((pane: Pane, sectionId: string)` — const, line 425
- `const moved = lastFollow.current` — const, line 426
- `const lastMainSection = useRef<string | null>(main?.sectionId ?? null)` — const, line 438
- `const sectionId = main?.sectionId ?? null` — const, line 440
- `const previous = lastMainSection.current` — const, line 441
- `const goSide = useCallback((sectionId: string)` — const, line 450
- `const current = pairRef.current` — const, line 451
- `const target: PaneTarget =` — const, line 455
- `const toggleFollow = useCallback(()` — const, line 462
- `const mainSource = main?.sourceId ?? null` — const, line 472
- `const current = pairRef.current` — const, line 474
- `const entryId = currentEntry?.id ?? null` — const, line 475
- `const target = currentEntry?.kind === "side_by_side" ? currentEntry.sideBySide ?? null : null` — const, line 477
- `const onCrumb = Boolean(target && entryId && enabled && !narrow && mainSource && currentEntry?.sourceId === mainSource)` — const, line 478
- `const opened = start(target as PaneTarget, entryId, false, mainSource as string)` — const, line 481
- `const here = mainRef.current` — const, line 482
- `const current = pairRef.current` — const, line 500
- `const rememberScroll = useCallback((key: string, top: number)` — const, line 516
- `const scrollFor = useCallback((key: string)` — const, line 519
- `const shownTarget: PaneTarget | null = pair ?` — const, line 522
- `const live = Boolean(enabled && pair)` — const, line 526

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
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useListenerHub`
- [[Reference/Desktop/TypeScript/screens/reader/SideBySidePane|src/screens/reader/SideBySidePane.tsx]] — import-or-re-export; imports `PaneSelection`
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
- [apps/learnloop-tauri/src/screens/reader/sideBySideIntent.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideIntent.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

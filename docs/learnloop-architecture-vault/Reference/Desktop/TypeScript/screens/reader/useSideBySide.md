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
source_commit: "47cec5279eec7c2738ab839c558ebcbd603f4b6a"
source_commit_timestamp: "2026-11-01T04:24:32-05:00"
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

Provides `SidePaneDraft`, `SIDE_BY_SIDE_COPY`, `SIDE_BY_SIDE_SCROLL_KEYS`, `MainPane` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useSideBySide.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useSideBySide.ts) |
| Source lines | 551 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `47cec5279eec7c2738ab839c558ebcbd603f4b6a` |
| Commit timestamp | `2026-11-01T04:24:32-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useSideBySide|src/screens/reader/useSideBySide.ts]]

## Public API

- `export interface SidePaneDraft` — interface, line 43
- `export const SIDE_BY_SIDE_COPY =` — const, line 49
- `export const SIDE_BY_SIDE_SCROLL_KEYS: ReadonlySet<string> = new Set(["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " "])` — const, line 67
- `export interface MainPane` — interface, line 70
- `export interface CurrentEntry` — interface, line 78
- `export interface SideBySideInput` — interface, line 87
- `export type SideBySideVia = "find_list" | "also_list" | "peek" | "key"` — type, line 106
- `export interface SideBySide` — interface, line 132
- `export function useSideBySide(` — function, line 178

## Internal implementation anchors

- `type EndedBy = "close" | "walked_off" | "replaced" | "source" | "switch_off"` — type, line 108
- `interface Pair` — interface, line 110
- `interface LastFollow` — interface, line 124
- `function useNarrow(active: boolean): boolean` — function, line 166
- `const onResize = ()` — const, line 170
- `const narrow = useNarrow(enabled)` — const, line 181
- `const pairRef = useRef<Pair | null>(null)` — const, line 193
- `const setPair = useCallback((next: Pair | null)` — const, line 194
- `const leaderRef = useRef<Pane>("main")` — const, line 198
- `const mainRef = useRef<MainPane | null>(main)` — const, line 200
- `const enabledRef = useRef(enabled)` — const, line 202
- `const sectionRef = useRef<SideBySideSectionDto | null>(null)` — const, line 204
- `const currentEntryRef = useRef<CurrentEntry | null>(currentEntry)` — const, line 206
- `const visitRef = useRef(visitPayload)` — const, line 208
- `const loadToken = useRef(0)` — const, line 210
- `const crossing = useRef(0)` — const, line 211
- `const opening = useRef(0)` — const, line 213
- `const pendingOpen = useRef(0)` — const, line 215
- `const narrowRef = useRef(narrow)` — const, line 216
- `const lastFollow = useRef<LastFollow | null>(null)` — const, line 218
- `const sideScroll = useRef<` — const, line 220
- `const setDraft = useCallback((update: (current: SidePaneDraft | null)` — const, line 222
- `const visit = ()` — const, line 226
- `const load = useCallback((target: PaneTarget)` — const, line 228
- `const mine = ++loadToken.current` — const, line 229
- `const logEnded = useCallback((ended: Pair, via: EndedBy)` — const, line 244
- `const reset = useCallback((via: EndedBy)` — const, line 253
- `const ended = pairRef.current` — const, line 254
- `const start = useCallback((target: PaneTarget, entryId: string | null, sheet: boolean, mainSourceId: string): Pair` — const, line 272
- `const previous = pairRef.current` — const, line 273
- `const next: Pair =` — const, line 279
- `const open = useCallback((target: PaneTarget, via: SideBySideVia)` — const, line 290
- `const here = mainRef.current` — const, line 291
- `const sheet = narrowRef.current` — const, line 295
- `const label = crumbLabel(target)` — const, line 296
- `const current = pairRef.current` — const, line 297
- `let entryId: string | null = null` — let, line 298
- `const onItsCrumb = current && !current.sheet && current.entryId && current.entryId === currentEntryRef.current?.id` — const, line 302
- `const opened = start(target, entryId, sheet, here.sourceId)` — const, line 307
- `const close = useCallback(()` — const, line 323
- `const current = pairRef.current` — const, line 324
- `const openFirst = useCallback(async ()` — const, line 330
- `const here = mainRef.current` — const, line 331
- `const mine = ++pendingOpen.current` — const, line 333
- `let view: CorrespondentsDto` — let, line 334
- `const first = firstCorrespondent(view)` — const, line 345
- `const touch = useCallback((pane: Pane)` — const, line 353
- `const followFrom = useCallback(async (from: Pane, extractionId: string, sectionId: string)` — const, line 367
- `const current = pairRef.current` — const, line 368
- `const here = mainRef.current` — const, line 369
- `const mine = ++crossing.current` — const, line 371
- `const openedAs = opening.current` — const, line 372
- `const followerSource = from === "main" ? current.target.sourceId : here.sourceId` — const, line 373
- `let view: CorrespondentsDto | null = null` — let, line 374
- `const now = pairRef.current` — const, line 384
- `const hit = firstJudgedIn(view, followerSource)` — const, line 386
- `const follower: Pane = from === "main" ? "side" : "main"` — const, line 387
- `const target = targetOf(hit)` — const, line 392
- `let fromSectionId: string | null` — let, line 393
- `const noteManualMove = useCallback((pane: Pane, sectionId: string)` — const, line 424
- `const moved = lastFollow.current` — const, line 425
- `const lastMainSection = useRef<string | null>(main?.sectionId ?? null)` — const, line 437
- `const sectionId = main?.sectionId ?? null` — const, line 439
- `const previous = lastMainSection.current` — const, line 440
- `const goSide = useCallback((sectionId: string)` — const, line 449
- `const current = pairRef.current` — const, line 450
- `const target: PaneTarget =` — const, line 454
- `const toggleFollow = useCallback(()` — const, line 461
- `const mainSource = main?.sourceId ?? null` — const, line 471
- `const current = pairRef.current` — const, line 473
- `const entryId = currentEntry?.id ?? null` — const, line 474
- `const target = currentEntry?.kind === "side_by_side" ? currentEntry.sideBySide ?? null : null` — const, line 476
- `const onCrumb = Boolean(target && entryId && enabled && !narrow && mainSource && currentEntry?.sourceId === mainSource)` — const, line 477
- `const opened = start(target as PaneTarget, entryId, false, mainSource as string)` — const, line 480
- `const here = mainRef.current` — const, line 481
- `const current = pairRef.current` — const, line 499
- `const rememberScroll = useCallback((key: string, top: number)` — const, line 515
- `const scrollFor = useCallback((key: string)` — const, line 518
- `const shownTarget: PaneTarget | null = pair ?` — const, line 521
- `const live = Boolean(enabled && pair)` — const, line 525

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

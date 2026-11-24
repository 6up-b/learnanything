---
title: "Desktop module · src/screens/reader/useReadingProgress.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.useReadingProgress"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/useReadingProgress.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/useReadingProgress.ts"
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

# `src/screens/reader/useReadingProgress.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `SEEN_SETTLE_MS`, `READING_MARKER`, `observedPassages`, `readingPositionKey` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useReadingProgress.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReadingProgress.ts) |
| Source lines | 1289 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] → [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]]

## Public API

- `export const SEEN_SETTLE_MS = 1500` — const, line 54
- `export const READING_MARKER = 0.7` — const, line 59
- `export function observedPassages(input:` — function, line 74
- `export function readingPositionKey(sourceId: string): string` — function, line 91
- `export interface SavedReadingPlace` — interface, line 97
- `export function encodeReadingPlace(extractionId: string, spanId: string): string` — function, line 105
- `export function decodeReadingPlace(value: string | null): SavedReadingPlace | null` — function, line 109
- `export interface OpenedReading` — interface, line 124
- `export function placeIsOnReading(saved: SavedReadingPlace, reading: OpenedReading | undefined): boolean` — function, line 138
- `export interface WatchSeekHandle` — interface, line 145
- `export type SectionFinish = "writing" | "waiting" | "done"` — type, line 150
- `export function finishOf(result: ReaderMarkProgressResultDto | null): SectionFinish | null` — function, line 152
- `export interface ReadingProgressInput` — interface, line 157
- `export interface ReadingProgress` — interface, line 188
- `export function useReadingProgress(input: ReadingProgressInput): ReadingProgress` — function, line 285

## Internal implementation anchors

- `type Dispatch, type MutableRefObject, type RefObject, type SetStateAction, } from "react"` — type, line 18
- `type MutableRefObject, type RefObject, type SetStateAction, } from "react"` — type, line 19
- `type RefObject, type SetStateAction, } from "react"` — type, line 20
- `type SetStateAction, } from "react"` — type, line 21
- `type ReadingPosition, type SectionHistory, } from "./readingPosition"` — type, line 46
- `type SectionHistory, } from "./readingPosition"` — type, line 47
- `const PAGE_READ_THROUGH = 0.85` — const, line 60
- `const USER_SCROLL_MS = 1200` — const, line 64
- `const SCROLL_KEYS = new Set(["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " ", "Spacebar"])` — const, line 65
- `const observed = left && left !== spanId ? [left] : []` — const, line 82
- `const page = pageSpans.find((entry)` — const, line 84
- `const onPage = page === undefined ? [] : pageSpans.filter((entry)` — const, line 85
- `const index = onPage.findIndex((entry)` — const, line 86
- `const parsed = JSON.parse(value) as` — const, line 113
- `const activityRef = useReadingActivityRef()` — const, line 295
- `const paused = useWindowPaused()` — const, line 296
- `const markerPassageRef = useRef<` — const, line 311
- `const startViewRef = useRef<` — const, line 315
- `const movedRef = useRef(false)` — const, line 328
- `const setMoved = useCallback((moved: boolean)` — const, line 329
- `const userScrollAtRef = useRef(0)` — const, line 333
- `const movedPendingRef = useRef(false)` — const, line 336
- `const historyResumeRef = useRef(false)` — const, line 340
- `const placeRequestRef = useRef(0)` — const, line 349
- `const authorRequestedRef = useRef<Set<string>>(new Set())` — const, line 375
- `const authoringRef = useRef<string[]>([])` — const, line 379
- `const failedChecks = guidePlan?.checkFailedSectionIds` — const, line 383
- `const failedCheckSections = useMemo(()` — const, line 384
- `const shownTimedOutSections = useMemo( ()` — const, line 385
- `const handoffRef = useRef<ReadingPosition | null>(null)` — const, line 391
- `const jumpGuardRef = useRef(0)` — const, line 394
- `const readingRafRef = useRef<number | null>(null)` — const, line 395
- `const settleUntilRef = useRef(0)` — const, line 400
- `const seenSavesRef = useRef(new Map<string, SeenSave>())` — const, line 407
- `const activeSeenRef = useRef<string | null>(null)` — const, line 409
- `const noteFinished = useCallback((sectionId: string, result: ReaderMarkProgressResultDto | null)` — const, line 417
- `const finish = finishOf(result)` — const, line 418
- `const noteProgressSaved = useCallback((extractionId: string, sectionId: string, result: ReaderMarkProgressResultDto | null)` — const, line 426
- `const lastReadRef = useRef<` — const, line 431
- `const pageModeRef = useRef(false)` — const, line 432
- `const pageSpansRef = useRef<Array<` — const, line 433
- `const lastPlaybackSpanRef = useRef<string | null>(null)` — const, line 435
- `const resetProgress = useCallback(()` — const, line 445
- `const settleOpening = useCallback(()` — const, line 484
- `const placeAtOpen = useCallback(( sourceId: string, jumpSpan: string | undefined, handoff: ReadingPosition | null, reading?: OpenedReading, jumpReading?: string | null, )` — const, line 488
- `let placed = Boolean(handoff)` — let, line 492
- `let translating = false` — let, line 493
- `const translate = (place: SavedReadingPlace, kind: "saved" | "found")` — const, line 501
- `const request = ++placeRequestRef.current` — const, line 503
- `const openReading = reading?.extractionId ?? null` — const, line 504
- `const here = !openReading || landed.extractionId === openReading` — const, line 511
- `const jump: SavedReadingPlace | null = jumpSpan ?` — const, line 527
- `const jumpHere = jump !== null && (!jump.extractionId || placeIsOnReading(jump, reading))` — const, line 528
- `const saved = decodeReadingPlace(window.localStorage.getItem(readingPositionKey(sourceId)))` — const, line 530
- `const hydrateProgress = useCallback((extractionId: string, progress: ReaderProgressListDto)` — const, line 556
- `const seen: Record<string, number> =` — const, line 558
- `const acknowledged = seenSaveFor(seenSavesRef.current, extractionId).acknowledged` — const, line 560
- `const next =` — const, line 563
- `const pageSpans = useMemo( ()` — const, line 582
- `const pageMode = Boolean(pdfView && surface === "pdf" && !offline && pageSpans.length > 0)` — const, line 586
- `const boundaryChecksAvailable = mode === "anchor" && sectionPromptsEnabled` — const, line 590
- `const guideSectionBySpan = useMemo(()` — const, line 592
- `const map = new Map<string, ReaderGuideSectionDto>()` — const, line 593
- `const guideSectionByEnd = useMemo( ()` — const, line 599
- `const notePassages = useCallback((observed: string[])` — const, line 607
- `let next = current` — let, line 612
- `const section = guideSectionBySpan.get(spanId)` — const, line 614
- `const ended = observed.flatMap((spanId)` — const, line 621
- `const section = guideSectionBySpan.get(spanId)` — const, line 622
- `const notePassagesRef = useRef(notePassages)` — const, line 630
- `const watching = Boolean(watch || watchLoading)` — const, line 634
- `const viewNowRef = useRef<()` — const, line 635
- `const currentGuideSection = useMemo(()` — const, line 637
- `const positioned = guideSectionBySpan.get(readingSpan ?? activeSpan ?? "")` — const, line 638
- `const currentSectionProgress = useMemo(()` — const, line 641
- `const at = currentGuideSection.spanIds.indexOf(readingSpan ?? activeSpan ?? "")` — const, line 643
- `const withinPassage = pageMode && readingOffset !== null ? readingOffset : 1` — const, line 645
- `const currentSectionRead = useMemo(()` — const, line 655
- `const count = Math.max(1, currentGuideSection.spanIds.length)` — const, line 658
- `const pdfSurfaceActive = Boolean(pdfView && surface === "pdf" && !offline)` — const, line 665
- `const pdfSurfaceLoading = Boolean(!pdfView && pdfViewPending && surface === "pdf" && !offline)` — const, line 670
- `const pageBySpan = useMemo(()` — const, line 671
- `const pages = new Map<string, number>()` — const, line 672
- `const atLastPage = useMemo(()` — const, line 679
- `const here = pageBySpan.get(readingSpan ?? activeSpan ?? "")` — const, line 681
- `const last = pageBySpan.get(currentGuideSection.endSpanId)` — const, line 682
- `const checkSurface: CheckSurface = watch || watchLoading ? "watch" : pdfSurfaceActive ? "pdf" : pdfSurfaceLoading ? "loading" : "text"` — const, line 689
- `const offeredCheckSections = useMemo(()` — const, line 702
- `const sections = guidePlan?.sections ?? []` — const, line 703
- `const currentIndex = sections.findIndex((section)` — const, line 704
- `const offered = new Set<string>()` — const, line 705
- `const decision = checkOffer(` — const, line 707
- `const unpinned = [...offeredCheckSections].filter((id)` — const, line 732
- `const openQuestionSections = useMemo( ()` — const, line 739
- `const pendingQuickCheckCount = boundaryChecksAvailable ? openQuestionSections.filter((section)` — const, line 745
- `const section = currentGuideSection` — const, line 760
- `const offered = (offeredCheckSections.has(section.id) && section.question?.readingPhase === "after_section") || section.suggestedPassages.length > 0` — const, line 762
- `const currentQuestionOpen = useMemo( ()` — const, line 767
- `const pdfOfferSection = useMemo(()` — const, line 773
- `const sections = guidePlan?.sections ?? []` — const, line 775
- `const currentIndex = sections.findIndex((section)` — const, line 776
- `const offered = openQuestionSections.filter((section)` — const, line 777
- `const index = sections.findIndex((entry)` — const, line 778
- `const readingProgress = useMemo(()` — const, line 783
- `const at = blocks.findIndex((block)` — const, line 785
- `const sections = guidePlan?.sections ?? []` — const, line 795
- `const index = sections.findIndex((section)` — const, line 796
- `const at = currentGuideSection.spanIds.indexOf(readingSpan ?? "")` — const, line 797
- `const last = lastReadRef.current` — const, line 798
- `const marker = markerPassageRef.current` — const, line 800
- `const forward = marker !== null && (marker.sectionIndex < index || (marker.sectionIndex === index && marker.spanIndex < at))` — const, line 806
- `const count = currentGuideSection.spanIds.length` — const, line 812
- `const seenHere = pageMode ? at + ((readingOffset ?? 0) >= PAGE_READ_THROUGH ? 1 : 0) : at + 1` — const, line 813
- `const next =` — const, line 815
- `let changed = false` — let, line 816
- `const raise = (id: string, value: number)` — const, line 817
- `const extractionId = render.extractionId` — const, line 840
- `const saves = seenSavesRef.current` — const, line 841
- `const save = seenSaveFor(saves, extractionId)` — const, line 842
- `const counts = new Map((guidePlan?.sections ?? []).map((section)` — const, line 843
- `const spanCount = counts.get(sectionId)` — const, line 845
- `const kept = (save.passages[sectionId] ??= new Set())` — const, line 851
- `const timer = window.setTimeout(()` — const, line 856
- `const saves = seenSavesRef.current` — const, line 860
- `const section = currentGuideSection` — const, line 876
- `const extractionId = render.extractionId` — const, line 885
- `const result = await api.readerAuthorSectionQuestion(` — const, line 888
- `const retryQuickCheck = useCallback( (sectionId: string)` — const, line 899
- `const extractionId = render.extractionId` — const, line 904
- `const openQuickCheck = useCallback((sectionId: string)` — const, line 917
- `const frame = window.requestAnimationFrame(()` — const, line 926
- `const card = railRef.current?.querySelector(`[data-quick-check="$` — const, line 927
- `const extractionId = render.extractionId` — const, line 937
- `let attempts = 0` — let, line 938
- `const timer = window.setInterval(()` — const, line 939
- `const stalled = authoringRef.current` — const, line 942
- `const failed = new Set(plan.checkFailedSectionIds ?? [])` — const, line 959
- `const refreshGuidePlan = useCallback((plan: ReaderGuidePlanDto)` — const, line 975
- `const updateReadingPosition = useCallback(()` — const, line 980
- `const container = bodyRef.current` — const, line 981
- `const position = pagePositionAt(container, READING_MARKER)` — const, line 986
- `const spanId = position ? spanOnPage(pageSpansRef.current, position) : null` — const, line 987
- `const containerRect = container.getBoundingClientRect()` — const, line 994
- `const markerY = containerRect.top + containerRect.height * READING_MARKER` — const, line 995
- `const nodes = Array.from(container.querySelectorAll<HTMLElement>("[data-span-id]"))` — const, line 996
- `const last = nodes[nodes.length - 1]` — const, line 997
- `const lastRect = last?.getBoundingClientRect()` — const, line 998
- `let best: HTMLElement | null = null` — let, line 1002
- `let bestDistance = Number.POSITIVE_INFINITY` — let, line 1003
- `const rect = node.getBoundingClientRect()` — const, line 1005
- `const distance = Math.abs(Math.min(Math.max(markerY, rect.top), rect.bottom) - markerY)` — const, line 1007
- `const onReadingScroll = useCallback(()` — const, line 1016
- `const now = Date.now()` — const, line 1017
- `const own = movedPendingRef.current || movedRef.current` — const, line 1023
- `const start = startViewRef.current` — const, line 1036
- `const fresh = start !== null && Date.now() - start.at < USER_SCROLL_MS` — const, line 1038
- `const frame = window.requestAnimationFrame(updateReadingPosition)` — const, line 1044
- `const revealSection = useCallback( (sectionId: string)` — const, line 1052
- `const completeSection = useCallback( (sectionId: string, by?: "check_closed" | "idea_chosen"): Promise<ReaderMarkProgressResultDto | null>` — const, line 1067
- `const revealSegment = useCallback((page: number, spanId: string, align: PassageAlign = "center")` — const, line 1090
- `const jumpToSpan = useCallback( (spanId: string, align: PassageAlign = "center")` — const, line 1094
- `const geometry = pdfView.blocks.find((block)` — const, line 1110
- `const page = pageBySpan.get(spanId)` — const, line 1117
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1124
- `const reduced = typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches` — const, line 1128
- `const noteFoundApproximate = useCallback((approximate: boolean)` — const, line 1134
- `const notePlacement = useCallback(()` — const, line 1136
- `const spanId = resumeSpanFromHistory(guidePlan.sections, readingHistory)` — const, line 1152
- `const noteMovementStart = useCallback(()` — const, line 1172
- `const now = Date.now()` — const, line 1173
- `const start = startViewRef.current` — const, line 1175
- `const kept = start !== null && now - start.at < USER_SCROLL_MS ? start.spanIds : []` — const, line 1176
- `const noteUserScroll = useCallback(()` — const, line 1179
- `const onPlaybackSpan = useCallback((spanId: string | null, advancing: boolean)` — const, line 1190
- `const last = lastPlaybackSpanRef.current` — const, line 1191
- `const onPlaybackSeek = useCallback((spanId: string | null)` — const, line 1207
- `const hub = useListenerHub()` — const, line 1215
- `const onKey = (event: KeyboardEvent)` — const, line 1218
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 1220
- `const frame = window.requestAnimationFrame(()` — const, line 1237
- `const geometry = pdfView.blocks.find((block)` — const, line 1239
- `const page = (pdfView.pageSpans ?? []).find((entry)` — const, line 1245
- `const element = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1249
- `const position = handoffRef.current` — const, line 1262
- `const spanId = spanAtPosition(pdfView.blocks, position) ?? spanOnPage(pdfView.pageSpans ?? [], position)` — const, line 1265
- `const noteRestored = useCallback((spanId: string | null)` — const, line 1274

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/source/ScopedSource|src/screens/desks/source/ScopedSource.tsx]] — import-or-re-export: `useReadingProgress`; references `useReadingProgress`
- [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]] — import-or-re-export: `SEEN_SETTLE_MS`; references `SEEN_SETTLE_MS`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `encodeReadingPlace`, `readingPositionKey`; references `encodeReadingPlace`, `readingPositionKey`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderGuidePlanDto`, `ReaderGuideSectionDto`, `ReaderMarkProgressResultDto`, `ReaderPdfViewDto`, `ReaderProgressListDto`, `ReaderRenderBlockDto`, `ReaderRenderViewDto`, `ReaderWatchPlanDto`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export; imports `PassageAlign`, `PdfReaderPaneHandle`
- [[Reference/Desktop/TypeScript/components/scrollWithin|src/components/scrollWithin.ts]] — import-or-re-export; imports `scrollIntoViewWithin`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useListenerHub`, `useReadingActivityRef`, `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/reader/checkOffer|src/screens/reader/checkOffer.ts]] — import-or-re-export; imports `CheckSurface`, `checkOffer`
- [[Reference/Desktop/TypeScript/screens/reader/guidePlan|src/screens/reader/guidePlan.ts]] — import-or-re-export; imports `useGuideDiagnosisRefresh`
- [[Reference/Desktop/TypeScript/screens/reader/readingPosition|src/screens/reader/readingPosition.ts]] — import-or-re-export; imports `ReadingPosition`, `SectionHistory`, `pagePositionAt`, `passagesInView`, `resumeSpanFromHistory`, `spanAtPosition`, `spanOnPage`
- [[Reference/Desktop/TypeScript/screens/reader/readingReports|src/screens/reader/readingReports.ts]] — import-or-re-export; imports `SEEN_REPORT_MS`, `SeenSave`, `const`, `releaseSeenSaves`, `seenSaveFor`, `sendSeenCounts`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/seenViewport.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/seenViewport.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/seenPassages.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/seenPassages.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/sectionEnd.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sectionEnd.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/readingPathsRefresh.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readingPathsRefresh.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/readerHooks.parity.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readerHooks.parity.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/ReadingPathCard.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/ReadingPathCard.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/source/ScopedSource.review.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/source/ScopedSource.review.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/source/ScopedSource.preparing.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/source/ScopedSource.preparing.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/useReadingProgress.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReadingProgress.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

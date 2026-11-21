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

Provides `SEEN_SETTLE_MS`, `SEEN_REPORT_MS`, `READING_MARKER`, `observedPassages` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useReadingProgress.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReadingProgress.ts) |
| Source lines | 1309 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]]

## Public API

- `export const SEEN_SETTLE_MS = 1500` — const, line 52
- `export const SEEN_REPORT_MS = 1500` — const, line 53
- `export const READING_MARKER = 0.7` — const, line 59
- `export function observedPassages(input:` — function, line 161
- `export function readingPositionKey(sourceId: string): string` — function, line 178
- `export interface SavedReadingPlace` — interface, line 184
- `export function encodeReadingPlace(extractionId: string, spanId: string): string` — function, line 192
- `export function decodeReadingPlace(value: string | null): SavedReadingPlace | null` — function, line 196
- `export interface OpenedReading` — interface, line 211
- `export function placeIsOnReading(saved: SavedReadingPlace, reading: OpenedReading | undefined): boolean` — function, line 225
- `export interface WatchSeekHandle` — interface, line 232
- `export interface ReadingProgressInput` — interface, line 236
- `export interface ReadingProgress` — interface, line 267
- `export function useReadingProgress(input: ReadingProgressInput): ReadingProgress` — function, line 355

## Internal implementation anchors

- `type Dispatch, type MutableRefObject, type RefObject, type SetStateAction, } from "react"` — type, line 18
- `type MutableRefObject, type RefObject, type SetStateAction, } from "react"` — type, line 19
- `type RefObject, type SetStateAction, } from "react"` — type, line 20
- `type SetStateAction, } from "react"` — type, line 21
- `type ReadingPosition, type SectionHistory, } from "./readingPosition"` — type, line 45
- `type SectionHistory, } from "./readingPosition"` — type, line 46
- `const SEEN_RETRY_LIMIT = 3` — const, line 55
- `const PAGE_READ_THROUGH = 0.85` — const, line 60
- `const USER_SCROLL_MS = 1200` — const, line 64
- `const SCROLL_KEYS = new Set(["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " ", "Spacebar"])` — const, line 65
- `interface SeenSave` — interface, line 71
- `function seenSaveFor(saves: Map<string, SeenSave>, extractionId: string): SeenSave` — function, line 89
- `let save = saves.get(extractionId)` — let, line 90
- `function sendSeenCounts( saves: Map<string, SeenSave>, extractionId: string, onSaved?: (extractionId: string)` — function, line 108
- `const save = saves.get(extractionId)` — const, line 111
- `const sectionIds = new Set([...Object.keys(save.wanted), ...Object.keys(save.passages), ...save.ends])` — const, line 113
- `const counts = save.wanted[sectionId]` — const, line 115
- `const countNew = counts !== undefined && counts.spansSeen > Math.max(save.acknowledged[sectionId] ?? 0, save.sending[sectionId] ?? 0)` — const, line 116
- `const passages = [...(save.passages[sectionId] ?? [])] .filter((spanId)` — const, line 118
- `const end = save.ends.has(sectionId) && !save.acknowledgedEnds.has(sectionId) && !save.sendingEnds.has(sectionId)` — const, line 120
- `const observed = left && left !== spanId ? [left] : []` — const, line 169
- `const page = pageSpans.find((entry)` — const, line 171
- `const onPage = page === undefined ? [] : pageSpans.filter((entry)` — const, line 172
- `const index = onPage.findIndex((entry)` — const, line 173
- `const parsed = JSON.parse(value) as` — const, line 200
- `const markerPassageRef = useRef<` — const, line 377
- `const startViewRef = useRef<` — const, line 381
- `const movedRef = useRef(false)` — const, line 394
- `const setMoved = useCallback((moved: boolean)` — const, line 395
- `const userScrollAtRef = useRef(0)` — const, line 399
- `const movedPendingRef = useRef(false)` — const, line 402
- `const historyResumeRef = useRef(false)` — const, line 406
- `const placeRequestRef = useRef(0)` — const, line 415
- `const authorRequestedRef = useRef<Set<string>>(new Set())` — const, line 436
- `const authoringRef = useRef<string[]>([])` — const, line 440
- `const failedChecks = guidePlan?.checkFailedSectionIds` — const, line 444
- `const failedCheckSections = useMemo(()` — const, line 445
- `const shownTimedOutSections = useMemo( ()` — const, line 446
- `const handoffRef = useRef<ReadingPosition | null>(null)` — const, line 452
- `const jumpGuardRef = useRef(0)` — const, line 455
- `const readingRafRef = useRef<number | null>(null)` — const, line 456
- `const settleUntilRef = useRef(0)` — const, line 461
- `const seenSavesRef = useRef(new Map<string, SeenSave>())` — const, line 468
- `const activeSeenRef = useRef<string | null>(null)` — const, line 470
- `const noteProgressSaved = useCallback((extractionId: string)` — const, line 475
- `const lastReadRef = useRef<` — const, line 478
- `const pageModeRef = useRef(false)` — const, line 479
- `const pageSpansRef = useRef<Array<` — const, line 480
- `const lastPlaybackSpanRef = useRef<string | null>(null)` — const, line 482
- `const resetProgress = useCallback(()` — const, line 492
- `const settleOpening = useCallback(()` — const, line 528
- `const placeAtOpen = useCallback(( sourceId: string, jumpSpan: string | undefined, handoff: ReadingPosition | null, reading?: OpenedReading, jumpReading?: string | null, )` — const, line 532
- `let placed = Boolean(handoff)` — let, line 536
- `let translating = false` — let, line 537
- `const translate = (place: SavedReadingPlace, kind: "saved" | "found")` — const, line 545
- `const request = ++placeRequestRef.current` — const, line 547
- `const openReading = reading?.extractionId ?? null` — const, line 548
- `const here = !openReading || landed.extractionId === openReading` — const, line 555
- `const jump: SavedReadingPlace | null = jumpSpan ?` — const, line 571
- `const jumpHere = jump !== null && (!jump.extractionId || placeIsOnReading(jump, reading))` — const, line 572
- `const saved = decodeReadingPlace(window.localStorage.getItem(readingPositionKey(sourceId)))` — const, line 574
- `const hydrateProgress = useCallback((extractionId: string, progress: ReaderProgressListDto)` — const, line 600
- `const seen: Record<string, number> =` — const, line 602
- `const acknowledged = seenSaveFor(seenSavesRef.current, extractionId).acknowledged` — const, line 604
- `const next =` — const, line 607
- `const pageSpans = useMemo( ()` — const, line 623
- `const pageMode = Boolean(pdfView && surface === "pdf" && !offline && pageSpans.length > 0)` — const, line 627
- `const boundaryChecksAvailable = mode === "anchor" && sectionPromptsEnabled` — const, line 631
- `const guideSectionBySpan = useMemo(()` — const, line 633
- `const map = new Map<string, ReaderGuideSectionDto>()` — const, line 634
- `const guideSectionByEnd = useMemo( ()` — const, line 640
- `const notePassages = useCallback((observed: string[])` — const, line 648
- `let next = current` — let, line 653
- `const section = guideSectionBySpan.get(spanId)` — const, line 655
- `const ended = observed.flatMap((spanId)` — const, line 662
- `const section = guideSectionBySpan.get(spanId)` — const, line 663
- `const notePassagesRef = useRef(notePassages)` — const, line 671
- `const watching = Boolean(watch || watchLoading)` — const, line 675
- `const viewNowRef = useRef<()` — const, line 676
- `const currentGuideSection = useMemo(()` — const, line 678
- `const positioned = guideSectionBySpan.get(readingSpan ?? activeSpan ?? "")` — const, line 679
- `const currentSectionProgress = useMemo(()` — const, line 682
- `const at = currentGuideSection.spanIds.indexOf(readingSpan ?? activeSpan ?? "")` — const, line 684
- `const withinPassage = pageMode && readingOffset !== null ? readingOffset : 1` — const, line 686
- `const currentSectionRead = useMemo(()` — const, line 692
- `const count = Math.max(1, currentGuideSection.spanIds.length)` — const, line 695
- `const pdfSurfaceActive = Boolean(pdfView && surface === "pdf" && !offline)` — const, line 702
- `const pdfSurfaceLoading = Boolean(!pdfView && pdfViewPending && surface === "pdf" && !offline)` — const, line 707
- `const pageBySpan = useMemo(()` — const, line 708
- `const pages = new Map<string, number>()` — const, line 709
- `const atLastPage = useMemo(()` — const, line 716
- `const here = pageBySpan.get(readingSpan ?? activeSpan ?? "")` — const, line 718
- `const last = pageBySpan.get(currentGuideSection.endSpanId)` — const, line 719
- `const checkSurface: CheckSurface = watch || watchLoading ? "watch" : pdfSurfaceActive ? "pdf" : pdfSurfaceLoading ? "loading" : "text"` — const, line 726
- `const offeredCheckSections = useMemo(()` — const, line 739
- `const sections = guidePlan?.sections ?? []` — const, line 740
- `const currentIndex = sections.findIndex((section)` — const, line 741
- `const offered = new Set<string>()` — const, line 742
- `const decision = checkOffer(` — const, line 744
- `const unpinned = [...offeredCheckSections].filter((id)` — const, line 766
- `const openQuestionSections = useMemo( ()` — const, line 773
- `const pendingQuickCheckCount = boundaryChecksAvailable ? openQuestionSections.filter((section)` — const, line 779
- `const section = currentGuideSection` — const, line 794
- `const offered = (offeredCheckSections.has(section.id) && section.question?.readingPhase === "after_section") || section.suggestedPassages.length > 0` — const, line 796
- `const currentQuestionOpen = useMemo( ()` — const, line 801
- `const pdfOfferSection = useMemo(()` — const, line 807
- `const sections = guidePlan?.sections ?? []` — const, line 809
- `const currentIndex = sections.findIndex((section)` — const, line 810
- `const offered = openQuestionSections.filter((section)` — const, line 811
- `const index = sections.findIndex((entry)` — const, line 812
- `const readingProgress = useMemo(()` — const, line 817
- `const at = blocks.findIndex((block)` — const, line 818
- `const sections = guidePlan?.sections ?? []` — const, line 828
- `const index = sections.findIndex((section)` — const, line 829
- `const at = currentGuideSection.spanIds.indexOf(readingSpan ?? "")` — const, line 830
- `const last = lastReadRef.current` — const, line 831
- `const marker = markerPassageRef.current` — const, line 833
- `const forward = marker !== null && (marker.sectionIndex < index || (marker.sectionIndex === index && marker.spanIndex < at))` — const, line 839
- `const count = currentGuideSection.spanIds.length` — const, line 845
- `const seenHere = pageMode ? at + ((readingOffset ?? 0) >= PAGE_READ_THROUGH ? 1 : 0) : at + 1` — const, line 846
- `const next =` — const, line 848
- `let changed = false` — let, line 849
- `const raise = (id: string, value: number)` — const, line 850
- `const extractionId = render.extractionId` — const, line 873
- `const saves = seenSavesRef.current` — const, line 874
- `const save = seenSaveFor(saves, extractionId)` — const, line 875
- `const counts = new Map((guidePlan?.sections ?? []).map((section)` — const, line 876
- `const spanCount = counts.get(sectionId)` — const, line 878
- `const kept = (save.passages[sectionId] ??= new Set())` — const, line 884
- `const timer = window.setTimeout(()` — const, line 889
- `const saves = seenSavesRef.current` — const, line 893
- `const section = currentGuideSection` — const, line 907
- `const extractionId = render.extractionId` — const, line 916
- `const result = await api.readerAuthorSectionQuestion(` — const, line 919
- `const retryQuickCheck = useCallback( (sectionId: string)` — const, line 930
- `const extractionId = render.extractionId` — const, line 935
- `const openQuickCheck = useCallback((sectionId: string)` — const, line 948
- `const frame = window.requestAnimationFrame(()` — const, line 957
- `const card = railRef.current?.querySelector(`[data-quick-check="$` — const, line 958
- `const extractionId = render.extractionId` — const, line 968
- `let attempts = 0` — let, line 969
- `const timer = window.setInterval(()` — const, line 970
- `const stalled = authoringRef.current` — const, line 973
- `const failed = new Set(plan.checkFailedSectionIds ?? [])` — const, line 990
- `const refreshGuidePlan = useCallback((plan: ReaderGuidePlanDto)` — const, line 1006
- `const updateReadingPosition = useCallback(()` — const, line 1011
- `const container = bodyRef.current` — const, line 1012
- `const position = pagePositionAt(container, READING_MARKER)` — const, line 1016
- `const spanId = position ? spanOnPage(pageSpansRef.current, position) : null` — const, line 1017
- `const containerRect = container.getBoundingClientRect()` — const, line 1024
- `const markerY = containerRect.top + containerRect.height * READING_MARKER` — const, line 1025
- `const nodes = Array.from(container.querySelectorAll<HTMLElement>("[data-span-id]"))` — const, line 1026
- `let best: HTMLElement | null = null` — let, line 1027
- `let bestDistance = Number.POSITIVE_INFINITY` — let, line 1028
- `const rect = node.getBoundingClientRect()` — const, line 1030
- `const distance = Math.abs(Math.min(Math.max(markerY, rect.top), rect.bottom) - markerY)` — const, line 1032
- `const onReadingScroll = useCallback(()` — const, line 1041
- `const now = Date.now()` — const, line 1042
- `const own = movedPendingRef.current || movedRef.current` — const, line 1048
- `const start = startViewRef.current` — const, line 1061
- `const fresh = start !== null && Date.now() - start.at < USER_SCROLL_MS` — const, line 1063
- `const frame = window.requestAnimationFrame(updateReadingPosition)` — const, line 1069
- `const revealSection = useCallback( (sectionId: string)` — const, line 1077
- `const completeSection = useCallback( (sectionId: string): Promise<ReaderMarkProgressResultDto | null>` — const, line 1094
- `const revealSegment = useCallback((page: number, spanId: string, align: PassageAlign = "center")` — const, line 1112
- `const jumpToSpan = useCallback( (spanId: string, align: PassageAlign = "center")` — const, line 1116
- `const geometry = pdfView.blocks.find((block)` — const, line 1132
- `const page = pageBySpan.get(spanId)` — const, line 1139
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1146
- `const reduced = typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches` — const, line 1150
- `const noteFoundApproximate = useCallback((approximate: boolean)` — const, line 1156
- `const notePlacement = useCallback(()` — const, line 1158
- `const spanId = resumeSpanFromHistory(guidePlan.sections, readingHistory)` — const, line 1174
- `const noteMovementStart = useCallback(()` — const, line 1194
- `const now = Date.now()` — const, line 1195
- `const start = startViewRef.current` — const, line 1197
- `const kept = start !== null && now - start.at < USER_SCROLL_MS ? start.spanIds : []` — const, line 1198
- `const noteUserScroll = useCallback(()` — const, line 1201
- `const onPlaybackSpan = useCallback((spanId: string | null, advancing: boolean)` — const, line 1210
- `const last = lastPlaybackSpanRef.current` — const, line 1211
- `const onPlaybackSeek = useCallback((spanId: string | null)` — const, line 1227
- `const onKey = (event: KeyboardEvent)` — const, line 1237
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 1239
- `const frame = window.requestAnimationFrame(()` — const, line 1257
- `const geometry = pdfView.blocks.find((block)` — const, line 1259
- `const page = (pdfView.pageSpans ?? []).find((entry)` — const, line 1265
- `const element = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1269
- `const position = handoffRef.current` — const, line 1282
- `const spanId = spanAtPosition(pdfView.blocks, position) ?? spanOnPage(pdfView.pageSpans ?? [], position)` — const, line 1285
- `const noteRestored = useCallback((spanId: string | null)` — const, line 1294

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `useReadingProgress`; references `useReadingProgress`
- [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]] — import-or-re-export: `SEEN_SETTLE_MS`; references `SEEN_SETTLE_MS`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `encodeReadingPlace`, `readingPositionKey`; references `encodeReadingPlace`, `readingPositionKey`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderGuidePlanDto`, `ReaderGuideSectionDto`, `ReaderMarkProgressResultDto`, `ReaderPdfViewDto`, `ReaderProgressListDto`, `ReaderRenderBlockDto`, `ReaderRenderViewDto`, `ReaderWatchPlanDto`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export; imports `PassageAlign`, `PdfReaderPaneHandle`
- [[Reference/Desktop/TypeScript/components/scrollWithin|src/components/scrollWithin.ts]] — import-or-re-export; imports `scrollIntoViewWithin`
- [[Reference/Desktop/TypeScript/screens/reader/checkOffer|src/screens/reader/checkOffer.ts]] — import-or-re-export; imports `CheckSurface`, `checkOffer`
- [[Reference/Desktop/TypeScript/screens/reader/guidePlan|src/screens/reader/guidePlan.ts]] — import-or-re-export; imports `useGuideDiagnosisRefresh`
- [[Reference/Desktop/TypeScript/screens/reader/readingPosition|src/screens/reader/readingPosition.ts]] — import-or-re-export; imports `ReadingPosition`, `SectionHistory`, `pagePositionAt`, `passagesInView`, `resumeSpanFromHistory`, `spanAtPosition`, `spanOnPage`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/sideBySideIntent.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideIntent.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/seenViewport.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/seenViewport.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/seenPassages.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/seenPassages.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/readingPathsRefresh.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readingPathsRefresh.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/readerHooks.parity.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readerHooks.parity.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/ReadingPathCard.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/ReadingPathCard.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/ReaderScreen.review.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/ReaderScreen.review.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/ReaderScreen.preparing.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/ReaderScreen.preparing.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

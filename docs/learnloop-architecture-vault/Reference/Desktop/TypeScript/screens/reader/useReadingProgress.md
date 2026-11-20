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

Provides `SEEN_SETTLE_MS`, `SEEN_REPORT_MS`, `READING_MARKER`, `readingPositionKey` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useReadingProgress.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReadingProgress.ts) |
| Source lines | 1133 |
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

- `export const SEEN_SETTLE_MS = 1500` — const, line 50
- `export const SEEN_REPORT_MS = 1500` — const, line 51
- `export const READING_MARKER = 0.7` — const, line 57
- `export function readingPositionKey(sourceId: string): string` — function, line 120
- `export interface SavedReadingPlace` — interface, line 126
- `export function encodeReadingPlace(extractionId: string, spanId: string): string` — function, line 134
- `export function decodeReadingPlace(value: string | null): SavedReadingPlace | null` — function, line 138
- `export interface OpenedReading` — interface, line 153
- `export function placeIsOnReading(saved: SavedReadingPlace, reading: OpenedReading | undefined): boolean` — function, line 167
- `export interface WatchSeekHandle` — interface, line 174
- `export interface ReadingProgressInput` — interface, line 178
- `export interface ReadingProgress` — interface, line 209
- `export function useReadingProgress(input: ReadingProgressInput): ReadingProgress` — function, line 297

## Internal implementation anchors

- `type Dispatch, type MutableRefObject, type RefObject, type SetStateAction, } from "react"` — type, line 18
- `type MutableRefObject, type RefObject, type SetStateAction, } from "react"` — type, line 19
- `type RefObject, type SetStateAction, } from "react"` — type, line 20
- `type SetStateAction, } from "react"` — type, line 21
- `type ReadingPosition, type SectionHistory, } from "./readingPosition"` — type, line 43
- `type SectionHistory, } from "./readingPosition"` — type, line 44
- `const SEEN_RETRY_LIMIT = 3` — const, line 53
- `const PAGE_READ_THROUGH = 0.85` — const, line 58
- `const USER_SCROLL_MS = 1200` — const, line 62
- `const SCROLL_KEYS = new Set(["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " ", "Spacebar"])` — const, line 63
- `interface SeenSave` — interface, line 69
- `function seenSaveFor(saves: Map<string, SeenSave>, extractionId: string): SeenSave` — function, line 77
- `let save = saves.get(extractionId)` — let, line 78
- `function sendSeenCounts( saves: Map<string, SeenSave>, extractionId: string, onSaved?: (extractionId: string)` — function, line 92
- `const save = saves.get(extractionId)` — const, line 95
- `const parsed = JSON.parse(value) as` — const, line 142
- `const userScrollAtRef = useRef(0)` — const, line 322
- `const movedPendingRef = useRef(false)` — const, line 325
- `const historyResumeRef = useRef(false)` — const, line 329
- `const placeRequestRef = useRef(0)` — const, line 338
- `const authorRequestedRef = useRef<Set<string>>(new Set())` — const, line 359
- `const authoringRef = useRef<string[]>([])` — const, line 363
- `const handoffRef = useRef<ReadingPosition | null>(null)` — const, line 367
- `const jumpGuardRef = useRef(0)` — const, line 370
- `const readingRafRef = useRef<number | null>(null)` — const, line 371
- `const settleUntilRef = useRef(0)` — const, line 376
- `const seenSavesRef = useRef(new Map<string, SeenSave>())` — const, line 383
- `const activeSeenRef = useRef<string | null>(null)` — const, line 385
- `const noteProgressSaved = useCallback((extractionId: string)` — const, line 390
- `const lastReadRef = useRef<` — const, line 393
- `const pageModeRef = useRef(false)` — const, line 394
- `const pageSpansRef = useRef<Array<` — const, line 395
- `const lastPlaybackSpanRef = useRef<string | null>(null)` — const, line 397
- `const resetProgress = useCallback(()` — const, line 407
- `const settleOpening = useCallback(()` — const, line 439
- `const placeAtOpen = useCallback(( sourceId: string, jumpSpan: string | undefined, handoff: ReadingPosition | null, reading?: OpenedReading, jumpReading?: string | null, )` — const, line 443
- `let placed = Boolean(handoff)` — let, line 447
- `let translating = false` — let, line 448
- `const translate = (place: SavedReadingPlace, kind: "saved" | "found")` — const, line 456
- `const request = ++placeRequestRef.current` — const, line 458
- `const openReading = reading?.extractionId ?? null` — const, line 459
- `const here = !openReading || landed.extractionId === openReading` — const, line 466
- `const jump: SavedReadingPlace | null = jumpSpan ?` — const, line 482
- `const jumpHere = jump !== null && (!jump.extractionId || placeIsOnReading(jump, reading))` — const, line 483
- `const saved = decodeReadingPlace(window.localStorage.getItem(readingPositionKey(sourceId)))` — const, line 485
- `const hydrateProgress = useCallback((extractionId: string, progress: ReaderProgressListDto)` — const, line 511
- `const seen: Record<string, number> =` — const, line 513
- `const acknowledged = seenSaveFor(seenSavesRef.current, extractionId).acknowledged` — const, line 515
- `const next =` — const, line 518
- `const pageSpans = useMemo( ()` — const, line 534
- `const pageMode = Boolean(pdfView && surface === "pdf" && !offline && pageSpans.length > 0)` — const, line 538
- `const boundaryChecksAvailable = mode === "anchor" && sectionPromptsEnabled` — const, line 542
- `const guideSectionBySpan = useMemo(()` — const, line 544
- `const map = new Map<string, ReaderGuideSectionDto>()` — const, line 545
- `const guideSectionByEnd = useMemo( ()` — const, line 551
- `const currentGuideSection = useMemo(()` — const, line 555
- `const positioned = guideSectionBySpan.get(readingSpan ?? activeSpan ?? "")` — const, line 556
- `const currentSectionProgress = useMemo(()` — const, line 559
- `const at = currentGuideSection.spanIds.indexOf(readingSpan ?? activeSpan ?? "")` — const, line 561
- `const withinPassage = pageMode && readingOffset !== null ? readingOffset : 1` — const, line 563
- `const currentSectionRead = useMemo(()` — const, line 569
- `const count = Math.max(1, currentGuideSection.spanIds.length)` — const, line 572
- `const pdfSurfaceActive = Boolean(pdfView && surface === "pdf" && !offline)` — const, line 579
- `const pdfSurfaceLoading = Boolean(!pdfView && pdfViewPending && surface === "pdf" && !offline)` — const, line 584
- `const pageBySpan = useMemo(()` — const, line 585
- `const pages = new Map<string, number>()` — const, line 586
- `const atLastPage = useMemo(()` — const, line 593
- `const here = pageBySpan.get(readingSpan ?? activeSpan ?? "")` — const, line 595
- `const last = pageBySpan.get(currentGuideSection.endSpanId)` — const, line 596
- `const checkSurface: CheckSurface = watch || watchLoading ? "watch" : pdfSurfaceActive ? "pdf" : pdfSurfaceLoading ? "loading" : "text"` — const, line 603
- `const offeredCheckSections = useMemo(()` — const, line 616
- `const sections = guidePlan?.sections ?? []` — const, line 617
- `const currentIndex = sections.findIndex((section)` — const, line 618
- `const offered = new Set<string>()` — const, line 619
- `const decision = checkOffer(` — const, line 621
- `const unpinned = [...offeredCheckSections].filter((id)` — const, line 643
- `const openQuestionSections = useMemo( ()` — const, line 650
- `const pendingQuickCheckCount = boundaryChecksAvailable ? openQuestionSections.filter((section)` — const, line 656
- `const section = currentGuideSection` — const, line 671
- `const offered = (offeredCheckSections.has(section.id) && section.question?.readingPhase === "after_section") || section.suggestedPassages.length > 0` — const, line 673
- `const currentQuestionOpen = useMemo( ()` — const, line 678
- `const pdfOfferSection = useMemo(()` — const, line 684
- `const sections = guidePlan?.sections ?? []` — const, line 686
- `const currentIndex = sections.findIndex((section)` — const, line 687
- `const offered = openQuestionSections.filter((section)` — const, line 688
- `const index = sections.findIndex((entry)` — const, line 689
- `const readingProgress = useMemo(()` — const, line 694
- `const at = blocks.findIndex((block)` — const, line 695
- `const sections = guidePlan?.sections ?? []` — const, line 705
- `const index = sections.findIndex((section)` — const, line 706
- `const at = currentGuideSection.spanIds.indexOf(readingSpan ?? "")` — const, line 707
- `const last = lastReadRef.current` — const, line 708
- `const count = currentGuideSection.spanIds.length` — const, line 711
- `const seenHere = pageMode ? at + ((readingOffset ?? 0) >= PAGE_READ_THROUGH ? 1 : 0) : at + 1` — const, line 712
- `const next =` — const, line 714
- `let changed = false` — let, line 715
- `const raise = (id: string, value: number)` — const, line 716
- `const extractionId = render.extractionId` — const, line 738
- `const saves = seenSavesRef.current` — const, line 739
- `const save = seenSaveFor(saves, extractionId)` — const, line 740
- `const counts = new Map((guidePlan?.sections ?? []).map((section)` — const, line 741
- `const spanCount = counts.get(sectionId)` — const, line 743
- `const timer = window.setTimeout(()` — const, line 748
- `const saves = seenSavesRef.current` — const, line 752
- `const section = currentGuideSection` — const, line 766
- `const extractionId = render.extractionId` — const, line 773
- `const result = await api.readerAuthorSectionQuestion(` — const, line 776
- `const retryQuickCheck = useCallback( (sectionId: string)` — const, line 787
- `const extractionId = render.extractionId` — const, line 792
- `const openQuickCheck = useCallback((sectionId: string)` — const, line 805
- `const frame = window.requestAnimationFrame(()` — const, line 814
- `const card = railRef.current?.querySelector(`[data-quick-check="$` — const, line 815
- `const extractionId = render.extractionId` — const, line 825
- `let attempts = 0` — let, line 826
- `const timer = window.setInterval(()` — const, line 827
- `const stalled = authoringRef.current` — const, line 830
- `const refreshGuidePlan = useCallback((plan: ReaderGuidePlanDto)` — const, line 861
- `const updateReadingPosition = useCallback(()` — const, line 866
- `const container = bodyRef.current` — const, line 867
- `const position = pagePositionAt(container, READING_MARKER)` — const, line 871
- `const spanId = position ? spanOnPage(pageSpansRef.current, position) : null` — const, line 872
- `const containerRect = container.getBoundingClientRect()` — const, line 879
- `const markerY = containerRect.top + containerRect.height * READING_MARKER` — const, line 880
- `const nodes = Array.from(container.querySelectorAll<HTMLElement>("[data-span-id]"))` — const, line 881
- `let best: HTMLElement | null = null` — let, line 882
- `let bestDistance = Number.POSITIVE_INFINITY` — let, line 883
- `const rect = node.getBoundingClientRect()` — const, line 885
- `const distance = Math.abs(Math.min(Math.max(markerY, rect.top), rect.bottom) - markerY)` — const, line 887
- `const onReadingScroll = useCallback(()` — const, line 896
- `const now = Date.now()` — const, line 897
- `const frame = window.requestAnimationFrame(updateReadingPosition)` — const, line 915
- `const revealSection = useCallback( (sectionId: string)` — const, line 923
- `const completeSection = useCallback( (sectionId: string)` — const, line 937
- `const revealSegment = useCallback((page: number, spanId: string, align: PassageAlign = "center")` — const, line 956
- `const jumpToSpan = useCallback( (spanId: string, align: PassageAlign = "center")` — const, line 960
- `const geometry = pdfView.blocks.find((block)` — const, line 975
- `const page = pageBySpan.get(spanId)` — const, line 982
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 989
- `const reduced = typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches` — const, line 993
- `const noteFoundApproximate = useCallback((approximate: boolean)` — const, line 999
- `const notePlacement = useCallback(()` — const, line 1001
- `const spanId = resumeSpanFromHistory(guidePlan.sections, readingHistory)` — const, line 1016
- `const noteUserScroll = useCallback(()` — const, line 1034
- `const onPlaybackSpan = useCallback((spanId: string | null, advancing: boolean)` — const, line 1042
- `const last = lastPlaybackSpanRef.current` — const, line 1043
- `const onPlaybackSeek = useCallback((spanId: string | null)` — const, line 1054
- `const onKey = (event: KeyboardEvent)` — const, line 1063
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 1065
- `const frame = window.requestAnimationFrame(()` — const, line 1081
- `const geometry = pdfView.blocks.find((block)` — const, line 1083
- `const page = (pdfView.pageSpans ?? []).find((entry)` — const, line 1089
- `const element = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1093
- `const position = handoffRef.current` — const, line 1106
- `const spanId = spanAtPosition(pdfView.blocks, position) ?? spanOnPage(pdfView.pageSpans ?? [], position)` — const, line 1109
- `const noteRestored = useCallback((spanId: string | null)` — const, line 1118

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `useReadingProgress`; references `useReadingProgress`
- [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]] — import-or-re-export: `SEEN_SETTLE_MS`; references `SEEN_SETTLE_MS`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `encodeReadingPlace`, `readingPositionKey`; references `encodeReadingPlace`, `readingPositionKey`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderGuidePlanDto`, `ReaderGuideSectionDto`, `ReaderPdfViewDto`, `ReaderProgressListDto`, `ReaderRenderBlockDto`, `ReaderRenderViewDto`, `ReaderWatchPlanDto`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export; imports `PassageAlign`, `PdfReaderPaneHandle`
- [[Reference/Desktop/TypeScript/components/scrollWithin|src/components/scrollWithin.ts]] — import-or-re-export; imports `scrollIntoViewWithin`
- [[Reference/Desktop/TypeScript/screens/reader/checkOffer|src/screens/reader/checkOffer.ts]] — import-or-re-export; imports `CheckSurface`, `checkOffer`
- [[Reference/Desktop/TypeScript/screens/reader/guidePlan|src/screens/reader/guidePlan.ts]] — import-or-re-export; imports `useGuideDiagnosisRefresh`
- [[Reference/Desktop/TypeScript/screens/reader/readingPosition|src/screens/reader/readingPosition.ts]] — import-or-re-export; imports `ReadingPosition`, `SectionHistory`, `pagePositionAt`, `resumeSpanFromHistory`, `spanAtPosition`, `spanOnPage`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/sideBySideIntent.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideIntent.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

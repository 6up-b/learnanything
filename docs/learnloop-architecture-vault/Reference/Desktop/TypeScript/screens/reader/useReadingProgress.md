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
| Source lines | 1136 |
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

- `export const SEEN_SETTLE_MS = 1500` — const, line 51
- `export const SEEN_REPORT_MS = 1500` — const, line 52
- `export const READING_MARKER = 0.7` — const, line 58
- `export function readingPositionKey(sourceId: string): string` — function, line 121
- `export interface SavedReadingPlace` — interface, line 127
- `export function encodeReadingPlace(extractionId: string, spanId: string): string` — function, line 135
- `export function decodeReadingPlace(value: string | null): SavedReadingPlace | null` — function, line 139
- `export interface OpenedReading` — interface, line 154
- `export function placeIsOnReading(saved: SavedReadingPlace, reading: OpenedReading | undefined): boolean` — function, line 168
- `export interface WatchSeekHandle` — interface, line 175
- `export interface ReadingProgressInput` — interface, line 179
- `export interface ReadingProgress` — interface, line 210
- `export function useReadingProgress(input: ReadingProgressInput): ReadingProgress` — function, line 298

## Internal implementation anchors

- `type Dispatch, type MutableRefObject, type RefObject, type SetStateAction, } from "react"` — type, line 18
- `type MutableRefObject, type RefObject, type SetStateAction, } from "react"` — type, line 19
- `type RefObject, type SetStateAction, } from "react"` — type, line 20
- `type SetStateAction, } from "react"` — type, line 21
- `type ReadingPosition, type SectionHistory, } from "./readingPosition"` — type, line 44
- `type SectionHistory, } from "./readingPosition"` — type, line 45
- `const SEEN_RETRY_LIMIT = 3` — const, line 54
- `const PAGE_READ_THROUGH = 0.85` — const, line 59
- `const USER_SCROLL_MS = 1200` — const, line 63
- `const SCROLL_KEYS = new Set(["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " ", "Spacebar"])` — const, line 64
- `interface SeenSave` — interface, line 70
- `function seenSaveFor(saves: Map<string, SeenSave>, extractionId: string): SeenSave` — function, line 78
- `let save = saves.get(extractionId)` — let, line 79
- `function sendSeenCounts( saves: Map<string, SeenSave>, extractionId: string, onSaved?: (extractionId: string)` — function, line 93
- `const save = saves.get(extractionId)` — const, line 96
- `const parsed = JSON.parse(value) as` — const, line 143
- `const userScrollAtRef = useRef(0)` — const, line 323
- `const movedPendingRef = useRef(false)` — const, line 326
- `const historyResumeRef = useRef(false)` — const, line 330
- `const placeRequestRef = useRef(0)` — const, line 339
- `const authorRequestedRef = useRef<Set<string>>(new Set())` — const, line 360
- `const authoringRef = useRef<string[]>([])` — const, line 364
- `const handoffRef = useRef<ReadingPosition | null>(null)` — const, line 368
- `const jumpGuardRef = useRef(0)` — const, line 371
- `const readingRafRef = useRef<number | null>(null)` — const, line 372
- `const settleUntilRef = useRef(0)` — const, line 377
- `const seenSavesRef = useRef(new Map<string, SeenSave>())` — const, line 384
- `const activeSeenRef = useRef<string | null>(null)` — const, line 386
- `const noteProgressSaved = useCallback((extractionId: string)` — const, line 391
- `const lastReadRef = useRef<` — const, line 394
- `const pageModeRef = useRef(false)` — const, line 395
- `const pageSpansRef = useRef<Array<` — const, line 396
- `const lastPlaybackSpanRef = useRef<string | null>(null)` — const, line 398
- `const resetProgress = useCallback(()` — const, line 408
- `const settleOpening = useCallback(()` — const, line 440
- `const placeAtOpen = useCallback(( sourceId: string, jumpSpan: string | undefined, handoff: ReadingPosition | null, reading?: OpenedReading, jumpReading?: string | null, )` — const, line 444
- `let placed = Boolean(handoff)` — let, line 448
- `let translating = false` — let, line 449
- `const translate = (place: SavedReadingPlace, kind: "saved" | "found")` — const, line 457
- `const request = ++placeRequestRef.current` — const, line 459
- `const openReading = reading?.extractionId ?? null` — const, line 460
- `const here = !openReading || landed.extractionId === openReading` — const, line 467
- `const jump: SavedReadingPlace | null = jumpSpan ?` — const, line 483
- `const jumpHere = jump !== null && (!jump.extractionId || placeIsOnReading(jump, reading))` — const, line 484
- `const saved = decodeReadingPlace(window.localStorage.getItem(readingPositionKey(sourceId)))` — const, line 486
- `const hydrateProgress = useCallback((extractionId: string, progress: ReaderProgressListDto)` — const, line 512
- `const seen: Record<string, number> =` — const, line 514
- `const acknowledged = seenSaveFor(seenSavesRef.current, extractionId).acknowledged` — const, line 516
- `const next =` — const, line 519
- `const pageSpans = useMemo( ()` — const, line 535
- `const pageMode = Boolean(pdfView && surface === "pdf" && !offline && pageSpans.length > 0)` — const, line 539
- `const boundaryChecksAvailable = mode === "anchor" && sectionPromptsEnabled` — const, line 543
- `const guideSectionBySpan = useMemo(()` — const, line 545
- `const map = new Map<string, ReaderGuideSectionDto>()` — const, line 546
- `const guideSectionByEnd = useMemo( ()` — const, line 552
- `const currentGuideSection = useMemo(()` — const, line 556
- `const positioned = guideSectionBySpan.get(readingSpan ?? activeSpan ?? "")` — const, line 557
- `const currentSectionProgress = useMemo(()` — const, line 560
- `const at = currentGuideSection.spanIds.indexOf(readingSpan ?? activeSpan ?? "")` — const, line 562
- `const withinPassage = pageMode && readingOffset !== null ? readingOffset : 1` — const, line 564
- `const currentSectionRead = useMemo(()` — const, line 570
- `const count = Math.max(1, currentGuideSection.spanIds.length)` — const, line 573
- `const pdfSurfaceActive = Boolean(pdfView && surface === "pdf" && !offline)` — const, line 580
- `const pdfSurfaceLoading = Boolean(!pdfView && pdfViewPending && surface === "pdf" && !offline)` — const, line 585
- `const pageBySpan = useMemo(()` — const, line 586
- `const pages = new Map<string, number>()` — const, line 587
- `const atLastPage = useMemo(()` — const, line 594
- `const here = pageBySpan.get(readingSpan ?? activeSpan ?? "")` — const, line 596
- `const last = pageBySpan.get(currentGuideSection.endSpanId)` — const, line 597
- `const checkSurface: CheckSurface = watch || watchLoading ? "watch" : pdfSurfaceActive ? "pdf" : pdfSurfaceLoading ? "loading" : "text"` — const, line 604
- `const offeredCheckSections = useMemo(()` — const, line 617
- `const sections = guidePlan?.sections ?? []` — const, line 618
- `const currentIndex = sections.findIndex((section)` — const, line 619
- `const offered = new Set<string>()` — const, line 620
- `const decision = checkOffer(` — const, line 622
- `const unpinned = [...offeredCheckSections].filter((id)` — const, line 644
- `const openQuestionSections = useMemo( ()` — const, line 651
- `const pendingQuickCheckCount = boundaryChecksAvailable ? openQuestionSections.filter((section)` — const, line 657
- `const section = currentGuideSection` — const, line 672
- `const offered = (offeredCheckSections.has(section.id) && section.question?.readingPhase === "after_section") || section.suggestedPassages.length > 0` — const, line 674
- `const currentQuestionOpen = useMemo( ()` — const, line 679
- `const pdfOfferSection = useMemo(()` — const, line 685
- `const sections = guidePlan?.sections ?? []` — const, line 687
- `const currentIndex = sections.findIndex((section)` — const, line 688
- `const offered = openQuestionSections.filter((section)` — const, line 689
- `const index = sections.findIndex((entry)` — const, line 690
- `const readingProgress = useMemo(()` — const, line 695
- `const at = blocks.findIndex((block)` — const, line 696
- `const sections = guidePlan?.sections ?? []` — const, line 706
- `const index = sections.findIndex((section)` — const, line 707
- `const at = currentGuideSection.spanIds.indexOf(readingSpan ?? "")` — const, line 708
- `const last = lastReadRef.current` — const, line 709
- `const count = currentGuideSection.spanIds.length` — const, line 712
- `const seenHere = pageMode ? at + ((readingOffset ?? 0) >= PAGE_READ_THROUGH ? 1 : 0) : at + 1` — const, line 713
- `const next =` — const, line 715
- `let changed = false` — let, line 716
- `const raise = (id: string, value: number)` — const, line 717
- `const extractionId = render.extractionId` — const, line 739
- `const saves = seenSavesRef.current` — const, line 740
- `const save = seenSaveFor(saves, extractionId)` — const, line 741
- `const counts = new Map((guidePlan?.sections ?? []).map((section)` — const, line 742
- `const spanCount = counts.get(sectionId)` — const, line 744
- `const timer = window.setTimeout(()` — const, line 749
- `const saves = seenSavesRef.current` — const, line 753
- `const section = currentGuideSection` — const, line 767
- `const extractionId = render.extractionId` — const, line 774
- `const result = await api.readerAuthorSectionQuestion(` — const, line 777
- `const retryQuickCheck = useCallback( (sectionId: string)` — const, line 788
- `const extractionId = render.extractionId` — const, line 793
- `const openQuickCheck = useCallback((sectionId: string)` — const, line 806
- `const frame = window.requestAnimationFrame(()` — const, line 815
- `const card = railRef.current?.querySelector(`[data-quick-check="$` — const, line 816
- `const extractionId = render.extractionId` — const, line 826
- `let attempts = 0` — let, line 827
- `const timer = window.setInterval(()` — const, line 828
- `const stalled = authoringRef.current` — const, line 831
- `const refreshGuidePlan = useCallback((plan: ReaderGuidePlanDto)` — const, line 862
- `const updateReadingPosition = useCallback(()` — const, line 867
- `const container = bodyRef.current` — const, line 868
- `const position = pagePositionAt(container, READING_MARKER)` — const, line 872
- `const spanId = position ? spanOnPage(pageSpansRef.current, position) : null` — const, line 873
- `const containerRect = container.getBoundingClientRect()` — const, line 880
- `const markerY = containerRect.top + containerRect.height * READING_MARKER` — const, line 881
- `const nodes = Array.from(container.querySelectorAll<HTMLElement>("[data-span-id]"))` — const, line 882
- `let best: HTMLElement | null = null` — let, line 883
- `let bestDistance = Number.POSITIVE_INFINITY` — let, line 884
- `const rect = node.getBoundingClientRect()` — const, line 886
- `const distance = Math.abs(Math.min(Math.max(markerY, rect.top), rect.bottom) - markerY)` — const, line 888
- `const onReadingScroll = useCallback(()` — const, line 897
- `const now = Date.now()` — const, line 898
- `const frame = window.requestAnimationFrame(updateReadingPosition)` — const, line 916
- `const revealSection = useCallback( (sectionId: string)` — const, line 924
- `const completeSection = useCallback( (sectionId: string): Promise<ReaderMarkProgressResultDto | null>` — const, line 941
- `const revealSegment = useCallback((page: number, spanId: string, align: PassageAlign = "center")` — const, line 959
- `const jumpToSpan = useCallback( (spanId: string, align: PassageAlign = "center")` — const, line 963
- `const geometry = pdfView.blocks.find((block)` — const, line 978
- `const page = pageBySpan.get(spanId)` — const, line 985
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 992
- `const reduced = typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches` — const, line 996
- `const noteFoundApproximate = useCallback((approximate: boolean)` — const, line 1002
- `const notePlacement = useCallback(()` — const, line 1004
- `const spanId = resumeSpanFromHistory(guidePlan.sections, readingHistory)` — const, line 1019
- `const noteUserScroll = useCallback(()` — const, line 1037
- `const onPlaybackSpan = useCallback((spanId: string | null, advancing: boolean)` — const, line 1045
- `const last = lastPlaybackSpanRef.current` — const, line 1046
- `const onPlaybackSeek = useCallback((spanId: string | null)` — const, line 1057
- `const onKey = (event: KeyboardEvent)` — const, line 1066
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 1068
- `const frame = window.requestAnimationFrame(()` — const, line 1084
- `const geometry = pdfView.blocks.find((block)` — const, line 1086
- `const page = (pdfView.pageSpans ?? []).find((entry)` — const, line 1092
- `const element = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1096
- `const position = handoffRef.current` — const, line 1109
- `const spanId = spanAtPosition(pdfView.blocks, position) ?? spanOnPage(pdfView.pageSpans ?? [], position)` — const, line 1112
- `const noteRestored = useCallback((spanId: string | null)` — const, line 1121

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

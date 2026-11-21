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
| Source lines | 1148 |
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
- `const failedChecks = guidePlan?.checkFailedSectionIds` — const, line 368
- `const failedCheckSections = useMemo(()` — const, line 369
- `const shownTimedOutSections = useMemo( ()` — const, line 370
- `const handoffRef = useRef<ReadingPosition | null>(null)` — const, line 376
- `const jumpGuardRef = useRef(0)` — const, line 379
- `const readingRafRef = useRef<number | null>(null)` — const, line 380
- `const settleUntilRef = useRef(0)` — const, line 385
- `const seenSavesRef = useRef(new Map<string, SeenSave>())` — const, line 392
- `const activeSeenRef = useRef<string | null>(null)` — const, line 394
- `const noteProgressSaved = useCallback((extractionId: string)` — const, line 399
- `const lastReadRef = useRef<` — const, line 402
- `const pageModeRef = useRef(false)` — const, line 403
- `const pageSpansRef = useRef<Array<` — const, line 404
- `const lastPlaybackSpanRef = useRef<string | null>(null)` — const, line 406
- `const resetProgress = useCallback(()` — const, line 416
- `const settleOpening = useCallback(()` — const, line 448
- `const placeAtOpen = useCallback(( sourceId: string, jumpSpan: string | undefined, handoff: ReadingPosition | null, reading?: OpenedReading, jumpReading?: string | null, )` — const, line 452
- `let placed = Boolean(handoff)` — let, line 456
- `let translating = false` — let, line 457
- `const translate = (place: SavedReadingPlace, kind: "saved" | "found")` — const, line 465
- `const request = ++placeRequestRef.current` — const, line 467
- `const openReading = reading?.extractionId ?? null` — const, line 468
- `const here = !openReading || landed.extractionId === openReading` — const, line 475
- `const jump: SavedReadingPlace | null = jumpSpan ?` — const, line 491
- `const jumpHere = jump !== null && (!jump.extractionId || placeIsOnReading(jump, reading))` — const, line 492
- `const saved = decodeReadingPlace(window.localStorage.getItem(readingPositionKey(sourceId)))` — const, line 494
- `const hydrateProgress = useCallback((extractionId: string, progress: ReaderProgressListDto)` — const, line 520
- `const seen: Record<string, number> =` — const, line 522
- `const acknowledged = seenSaveFor(seenSavesRef.current, extractionId).acknowledged` — const, line 524
- `const next =` — const, line 527
- `const pageSpans = useMemo( ()` — const, line 543
- `const pageMode = Boolean(pdfView && surface === "pdf" && !offline && pageSpans.length > 0)` — const, line 547
- `const boundaryChecksAvailable = mode === "anchor" && sectionPromptsEnabled` — const, line 551
- `const guideSectionBySpan = useMemo(()` — const, line 553
- `const map = new Map<string, ReaderGuideSectionDto>()` — const, line 554
- `const guideSectionByEnd = useMemo( ()` — const, line 560
- `const currentGuideSection = useMemo(()` — const, line 564
- `const positioned = guideSectionBySpan.get(readingSpan ?? activeSpan ?? "")` — const, line 565
- `const currentSectionProgress = useMemo(()` — const, line 568
- `const at = currentGuideSection.spanIds.indexOf(readingSpan ?? activeSpan ?? "")` — const, line 570
- `const withinPassage = pageMode && readingOffset !== null ? readingOffset : 1` — const, line 572
- `const currentSectionRead = useMemo(()` — const, line 578
- `const count = Math.max(1, currentGuideSection.spanIds.length)` — const, line 581
- `const pdfSurfaceActive = Boolean(pdfView && surface === "pdf" && !offline)` — const, line 588
- `const pdfSurfaceLoading = Boolean(!pdfView && pdfViewPending && surface === "pdf" && !offline)` — const, line 593
- `const pageBySpan = useMemo(()` — const, line 594
- `const pages = new Map<string, number>()` — const, line 595
- `const atLastPage = useMemo(()` — const, line 602
- `const here = pageBySpan.get(readingSpan ?? activeSpan ?? "")` — const, line 604
- `const last = pageBySpan.get(currentGuideSection.endSpanId)` — const, line 605
- `const checkSurface: CheckSurface = watch || watchLoading ? "watch" : pdfSurfaceActive ? "pdf" : pdfSurfaceLoading ? "loading" : "text"` — const, line 612
- `const offeredCheckSections = useMemo(()` — const, line 625
- `const sections = guidePlan?.sections ?? []` — const, line 626
- `const currentIndex = sections.findIndex((section)` — const, line 627
- `const offered = new Set<string>()` — const, line 628
- `const decision = checkOffer(` — const, line 630
- `const unpinned = [...offeredCheckSections].filter((id)` — const, line 652
- `const openQuestionSections = useMemo( ()` — const, line 659
- `const pendingQuickCheckCount = boundaryChecksAvailable ? openQuestionSections.filter((section)` — const, line 665
- `const section = currentGuideSection` — const, line 680
- `const offered = (offeredCheckSections.has(section.id) && section.question?.readingPhase === "after_section") || section.suggestedPassages.length > 0` — const, line 682
- `const currentQuestionOpen = useMemo( ()` — const, line 687
- `const pdfOfferSection = useMemo(()` — const, line 693
- `const sections = guidePlan?.sections ?? []` — const, line 695
- `const currentIndex = sections.findIndex((section)` — const, line 696
- `const offered = openQuestionSections.filter((section)` — const, line 697
- `const index = sections.findIndex((entry)` — const, line 698
- `const readingProgress = useMemo(()` — const, line 703
- `const at = blocks.findIndex((block)` — const, line 704
- `const sections = guidePlan?.sections ?? []` — const, line 714
- `const index = sections.findIndex((section)` — const, line 715
- `const at = currentGuideSection.spanIds.indexOf(readingSpan ?? "")` — const, line 716
- `const last = lastReadRef.current` — const, line 717
- `const count = currentGuideSection.spanIds.length` — const, line 720
- `const seenHere = pageMode ? at + ((readingOffset ?? 0) >= PAGE_READ_THROUGH ? 1 : 0) : at + 1` — const, line 721
- `const next =` — const, line 723
- `let changed = false` — let, line 724
- `const raise = (id: string, value: number)` — const, line 725
- `const extractionId = render.extractionId` — const, line 747
- `const saves = seenSavesRef.current` — const, line 748
- `const save = seenSaveFor(saves, extractionId)` — const, line 749
- `const counts = new Map((guidePlan?.sections ?? []).map((section)` — const, line 750
- `const spanCount = counts.get(sectionId)` — const, line 752
- `const timer = window.setTimeout(()` — const, line 757
- `const saves = seenSavesRef.current` — const, line 761
- `const section = currentGuideSection` — const, line 775
- `const extractionId = render.extractionId` — const, line 784
- `const result = await api.readerAuthorSectionQuestion(` — const, line 787
- `const retryQuickCheck = useCallback( (sectionId: string)` — const, line 798
- `const extractionId = render.extractionId` — const, line 803
- `const openQuickCheck = useCallback((sectionId: string)` — const, line 816
- `const frame = window.requestAnimationFrame(()` — const, line 825
- `const card = railRef.current?.querySelector(`[data-quick-check="$` — const, line 826
- `const extractionId = render.extractionId` — const, line 836
- `let attempts = 0` — let, line 837
- `const timer = window.setInterval(()` — const, line 838
- `const stalled = authoringRef.current` — const, line 841
- `const failed = new Set(plan.checkFailedSectionIds ?? [])` — const, line 858
- `const refreshGuidePlan = useCallback((plan: ReaderGuidePlanDto)` — const, line 874
- `const updateReadingPosition = useCallback(()` — const, line 879
- `const container = bodyRef.current` — const, line 880
- `const position = pagePositionAt(container, READING_MARKER)` — const, line 884
- `const spanId = position ? spanOnPage(pageSpansRef.current, position) : null` — const, line 885
- `const containerRect = container.getBoundingClientRect()` — const, line 892
- `const markerY = containerRect.top + containerRect.height * READING_MARKER` — const, line 893
- `const nodes = Array.from(container.querySelectorAll<HTMLElement>("[data-span-id]"))` — const, line 894
- `let best: HTMLElement | null = null` — let, line 895
- `let bestDistance = Number.POSITIVE_INFINITY` — let, line 896
- `const rect = node.getBoundingClientRect()` — const, line 898
- `const distance = Math.abs(Math.min(Math.max(markerY, rect.top), rect.bottom) - markerY)` — const, line 900
- `const onReadingScroll = useCallback(()` — const, line 909
- `const now = Date.now()` — const, line 910
- `const frame = window.requestAnimationFrame(updateReadingPosition)` — const, line 928
- `const revealSection = useCallback( (sectionId: string)` — const, line 936
- `const completeSection = useCallback( (sectionId: string): Promise<ReaderMarkProgressResultDto | null>` — const, line 953
- `const revealSegment = useCallback((page: number, spanId: string, align: PassageAlign = "center")` — const, line 971
- `const jumpToSpan = useCallback( (spanId: string, align: PassageAlign = "center")` — const, line 975
- `const geometry = pdfView.blocks.find((block)` — const, line 990
- `const page = pageBySpan.get(spanId)` — const, line 997
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1004
- `const reduced = typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches` — const, line 1008
- `const noteFoundApproximate = useCallback((approximate: boolean)` — const, line 1014
- `const notePlacement = useCallback(()` — const, line 1016
- `const spanId = resumeSpanFromHistory(guidePlan.sections, readingHistory)` — const, line 1031
- `const noteUserScroll = useCallback(()` — const, line 1049
- `const onPlaybackSpan = useCallback((spanId: string | null, advancing: boolean)` — const, line 1057
- `const last = lastPlaybackSpanRef.current` — const, line 1058
- `const onPlaybackSeek = useCallback((spanId: string | null)` — const, line 1069
- `const onKey = (event: KeyboardEvent)` — const, line 1078
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 1080
- `const frame = window.requestAnimationFrame(()` — const, line 1096
- `const geometry = pdfView.blocks.find((block)` — const, line 1098
- `const page = (pdfView.pageSpans ?? []).find((entry)` — const, line 1104
- `const element = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1108
- `const position = handoffRef.current` — const, line 1121
- `const spanId = spanAtPosition(pdfView.blocks, position) ?? spanOnPage(pdfView.pageSpans ?? [], position)` — const, line 1124
- `const noteRestored = useCallback((spanId: string | null)` — const, line 1133

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

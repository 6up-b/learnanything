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
| Source lines | 1254 |
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
- `export function observedPassages(input:` — function, line 159
- `export function readingPositionKey(sourceId: string): string` — function, line 176
- `export interface SavedReadingPlace` — interface, line 182
- `export function encodeReadingPlace(extractionId: string, spanId: string): string` — function, line 190
- `export function decodeReadingPlace(value: string | null): SavedReadingPlace | null` — function, line 194
- `export interface OpenedReading` — interface, line 209
- `export function placeIsOnReading(saved: SavedReadingPlace, reading: OpenedReading | undefined): boolean` — function, line 223
- `export interface WatchSeekHandle` — interface, line 230
- `export interface ReadingProgressInput` — interface, line 234
- `export interface ReadingProgress` — interface, line 265
- `export function useReadingProgress(input: ReadingProgressInput): ReadingProgress` — function, line 353

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
- `function seenSaveFor(saves: Map<string, SeenSave>, extractionId: string): SeenSave` — function, line 88
- `let save = saves.get(extractionId)` — let, line 89
- `function sendSeenCounts( saves: Map<string, SeenSave>, extractionId: string, onSaved?: (extractionId: string)` — function, line 107
- `const save = saves.get(extractionId)` — const, line 110
- `const sectionIds = new Set([...Object.keys(save.wanted), ...Object.keys(save.passages), ...save.ends])` — const, line 112
- `const counts = save.wanted[sectionId]` — const, line 114
- `const countNew = counts !== undefined && counts.spansSeen > Math.max(save.acknowledged[sectionId] ?? 0, save.sending[sectionId] ?? 0)` — const, line 115
- `const passages = [...(save.passages[sectionId] ?? [])] .filter((spanId)` — const, line 117
- `const end = save.ends.has(sectionId) && !save.acknowledgedEnds.has(sectionId) && !save.sendingEnds.has(sectionId)` — const, line 119
- `const observed = left && left !== spanId ? [left] : []` — const, line 167
- `const page = pageSpans.find((entry)` — const, line 169
- `const onPage = page === undefined ? [] : pageSpans.filter((entry)` — const, line 170
- `const index = onPage.findIndex((entry)` — const, line 171
- `const parsed = JSON.parse(value) as` — const, line 198
- `const markerPassageRef = useRef<` — const, line 375
- `const userScrollAtRef = useRef(0)` — const, line 386
- `const movedPendingRef = useRef(false)` — const, line 389
- `const historyResumeRef = useRef(false)` — const, line 393
- `const placeRequestRef = useRef(0)` — const, line 402
- `const authorRequestedRef = useRef<Set<string>>(new Set())` — const, line 423
- `const authoringRef = useRef<string[]>([])` — const, line 427
- `const failedChecks = guidePlan?.checkFailedSectionIds` — const, line 431
- `const failedCheckSections = useMemo(()` — const, line 432
- `const shownTimedOutSections = useMemo( ()` — const, line 433
- `const handoffRef = useRef<ReadingPosition | null>(null)` — const, line 439
- `const jumpGuardRef = useRef(0)` — const, line 442
- `const readingRafRef = useRef<number | null>(null)` — const, line 443
- `const settleUntilRef = useRef(0)` — const, line 448
- `const seenSavesRef = useRef(new Map<string, SeenSave>())` — const, line 455
- `const activeSeenRef = useRef<string | null>(null)` — const, line 457
- `const noteProgressSaved = useCallback((extractionId: string)` — const, line 462
- `const lastReadRef = useRef<` — const, line 465
- `const pageModeRef = useRef(false)` — const, line 466
- `const pageSpansRef = useRef<Array<` — const, line 467
- `const lastPlaybackSpanRef = useRef<string | null>(null)` — const, line 469
- `const resetProgress = useCallback(()` — const, line 479
- `const settleOpening = useCallback(()` — const, line 514
- `const placeAtOpen = useCallback(( sourceId: string, jumpSpan: string | undefined, handoff: ReadingPosition | null, reading?: OpenedReading, jumpReading?: string | null, )` — const, line 518
- `let placed = Boolean(handoff)` — let, line 522
- `let translating = false` — let, line 523
- `const translate = (place: SavedReadingPlace, kind: "saved" | "found")` — const, line 531
- `const request = ++placeRequestRef.current` — const, line 533
- `const openReading = reading?.extractionId ?? null` — const, line 534
- `const here = !openReading || landed.extractionId === openReading` — const, line 541
- `const jump: SavedReadingPlace | null = jumpSpan ?` — const, line 557
- `const jumpHere = jump !== null && (!jump.extractionId || placeIsOnReading(jump, reading))` — const, line 558
- `const saved = decodeReadingPlace(window.localStorage.getItem(readingPositionKey(sourceId)))` — const, line 560
- `const hydrateProgress = useCallback((extractionId: string, progress: ReaderProgressListDto)` — const, line 586
- `const seen: Record<string, number> =` — const, line 588
- `const acknowledged = seenSaveFor(seenSavesRef.current, extractionId).acknowledged` — const, line 590
- `const next =` — const, line 593
- `const pageSpans = useMemo( ()` — const, line 609
- `const pageMode = Boolean(pdfView && surface === "pdf" && !offline && pageSpans.length > 0)` — const, line 613
- `const boundaryChecksAvailable = mode === "anchor" && sectionPromptsEnabled` — const, line 617
- `const guideSectionBySpan = useMemo(()` — const, line 619
- `const map = new Map<string, ReaderGuideSectionDto>()` — const, line 620
- `const guideSectionByEnd = useMemo( ()` — const, line 626
- `const currentGuideSection = useMemo(()` — const, line 630
- `const positioned = guideSectionBySpan.get(readingSpan ?? activeSpan ?? "")` — const, line 631
- `const currentSectionProgress = useMemo(()` — const, line 634
- `const at = currentGuideSection.spanIds.indexOf(readingSpan ?? activeSpan ?? "")` — const, line 636
- `const withinPassage = pageMode && readingOffset !== null ? readingOffset : 1` — const, line 638
- `const currentSectionRead = useMemo(()` — const, line 644
- `const count = Math.max(1, currentGuideSection.spanIds.length)` — const, line 647
- `const pdfSurfaceActive = Boolean(pdfView && surface === "pdf" && !offline)` — const, line 654
- `const pdfSurfaceLoading = Boolean(!pdfView && pdfViewPending && surface === "pdf" && !offline)` — const, line 659
- `const pageBySpan = useMemo(()` — const, line 660
- `const pages = new Map<string, number>()` — const, line 661
- `const atLastPage = useMemo(()` — const, line 668
- `const here = pageBySpan.get(readingSpan ?? activeSpan ?? "")` — const, line 670
- `const last = pageBySpan.get(currentGuideSection.endSpanId)` — const, line 671
- `const checkSurface: CheckSurface = watch || watchLoading ? "watch" : pdfSurfaceActive ? "pdf" : pdfSurfaceLoading ? "loading" : "text"` — const, line 678
- `const offeredCheckSections = useMemo(()` — const, line 691
- `const sections = guidePlan?.sections ?? []` — const, line 692
- `const currentIndex = sections.findIndex((section)` — const, line 693
- `const offered = new Set<string>()` — const, line 694
- `const decision = checkOffer(` — const, line 696
- `const unpinned = [...offeredCheckSections].filter((id)` — const, line 718
- `const openQuestionSections = useMemo( ()` — const, line 725
- `const pendingQuickCheckCount = boundaryChecksAvailable ? openQuestionSections.filter((section)` — const, line 731
- `const section = currentGuideSection` — const, line 746
- `const offered = (offeredCheckSections.has(section.id) && section.question?.readingPhase === "after_section") || section.suggestedPassages.length > 0` — const, line 748
- `const currentQuestionOpen = useMemo( ()` — const, line 753
- `const pdfOfferSection = useMemo(()` — const, line 759
- `const sections = guidePlan?.sections ?? []` — const, line 761
- `const currentIndex = sections.findIndex((section)` — const, line 762
- `const offered = openQuestionSections.filter((section)` — const, line 763
- `const index = sections.findIndex((entry)` — const, line 764
- `const readingProgress = useMemo(()` — const, line 769
- `const at = blocks.findIndex((block)` — const, line 770
- `const sections = guidePlan?.sections ?? []` — const, line 780
- `const index = sections.findIndex((section)` — const, line 781
- `const at = currentGuideSection.spanIds.indexOf(readingSpan ?? "")` — const, line 782
- `const last = lastReadRef.current` — const, line 783
- `const marker = markerPassageRef.current` — const, line 785
- `const forward = marker !== null && (marker.sectionIndex < index || (marker.sectionIndex === index && marker.spanIndex < at))` — const, line 793
- `const observed = observedPassages(` — const, line 795
- `let next = current` — let, line 800
- `const section = guideSectionBySpan.get(spanId)` — const, line 802
- `const ended = observed.flatMap((spanId)` — const, line 811
- `const section = guideSectionBySpan.get(spanId)` — const, line 812
- `const count = currentGuideSection.spanIds.length` — const, line 819
- `const seenHere = pageMode ? at + ((readingOffset ?? 0) >= PAGE_READ_THROUGH ? 1 : 0) : at + 1` — const, line 820
- `const next =` — const, line 822
- `let changed = false` — let, line 823
- `const raise = (id: string, value: number)` — const, line 824
- `const extractionId = render.extractionId` — const, line 847
- `const saves = seenSavesRef.current` — const, line 848
- `const save = seenSaveFor(saves, extractionId)` — const, line 849
- `const counts = new Map((guidePlan?.sections ?? []).map((section)` — const, line 850
- `const spanCount = counts.get(sectionId)` — const, line 852
- `const kept = (save.passages[sectionId] ??= new Set())` — const, line 858
- `const timer = window.setTimeout(()` — const, line 863
- `const saves = seenSavesRef.current` — const, line 867
- `const section = currentGuideSection` — const, line 881
- `const extractionId = render.extractionId` — const, line 890
- `const result = await api.readerAuthorSectionQuestion(` — const, line 893
- `const retryQuickCheck = useCallback( (sectionId: string)` — const, line 904
- `const extractionId = render.extractionId` — const, line 909
- `const openQuickCheck = useCallback((sectionId: string)` — const, line 922
- `const frame = window.requestAnimationFrame(()` — const, line 931
- `const card = railRef.current?.querySelector(`[data-quick-check="$` — const, line 932
- `const extractionId = render.extractionId` — const, line 942
- `let attempts = 0` — let, line 943
- `const timer = window.setInterval(()` — const, line 944
- `const stalled = authoringRef.current` — const, line 947
- `const failed = new Set(plan.checkFailedSectionIds ?? [])` — const, line 964
- `const refreshGuidePlan = useCallback((plan: ReaderGuidePlanDto)` — const, line 980
- `const updateReadingPosition = useCallback(()` — const, line 985
- `const container = bodyRef.current` — const, line 986
- `const position = pagePositionAt(container, READING_MARKER)` — const, line 990
- `const spanId = position ? spanOnPage(pageSpansRef.current, position) : null` — const, line 991
- `const containerRect = container.getBoundingClientRect()` — const, line 998
- `const markerY = containerRect.top + containerRect.height * READING_MARKER` — const, line 999
- `const nodes = Array.from(container.querySelectorAll<HTMLElement>("[data-span-id]"))` — const, line 1000
- `let best: HTMLElement | null = null` — let, line 1001
- `let bestDistance = Number.POSITIVE_INFINITY` — let, line 1002
- `const rect = node.getBoundingClientRect()` — const, line 1004
- `const distance = Math.abs(Math.min(Math.max(markerY, rect.top), rect.bottom) - markerY)` — const, line 1006
- `const onReadingScroll = useCallback(()` — const, line 1015
- `const now = Date.now()` — const, line 1016
- `const frame = window.requestAnimationFrame(updateReadingPosition)` — const, line 1034
- `const revealSection = useCallback( (sectionId: string)` — const, line 1042
- `const completeSection = useCallback( (sectionId: string): Promise<ReaderMarkProgressResultDto | null>` — const, line 1059
- `const revealSegment = useCallback((page: number, spanId: string, align: PassageAlign = "center")` — const, line 1077
- `const jumpToSpan = useCallback( (spanId: string, align: PassageAlign = "center")` — const, line 1081
- `const geometry = pdfView.blocks.find((block)` — const, line 1096
- `const page = pageBySpan.get(spanId)` — const, line 1103
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1110
- `const reduced = typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches` — const, line 1114
- `const noteFoundApproximate = useCallback((approximate: boolean)` — const, line 1120
- `const notePlacement = useCallback(()` — const, line 1122
- `const spanId = resumeSpanFromHistory(guidePlan.sections, readingHistory)` — const, line 1137
- `const noteUserScroll = useCallback(()` — const, line 1155
- `const onPlaybackSpan = useCallback((spanId: string | null, advancing: boolean)` — const, line 1163
- `const last = lastPlaybackSpanRef.current` — const, line 1164
- `const onPlaybackSeek = useCallback((spanId: string | null)` — const, line 1175
- `const onKey = (event: KeyboardEvent)` — const, line 1184
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 1186
- `const frame = window.requestAnimationFrame(()` — const, line 1202
- `const geometry = pdfView.blocks.find((block)` — const, line 1204
- `const page = (pdfView.pageSpans ?? []).find((entry)` — const, line 1210
- `const element = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1214
- `const position = handoffRef.current` — const, line 1227
- `const spanId = spanAtPosition(pdfView.blocks, position) ?? spanOnPage(pdfView.pageSpans ?? [], position)` — const, line 1230
- `const noteRestored = useCallback((spanId: string | null)` — const, line 1239

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

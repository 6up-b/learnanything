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
| Source lines | 1379 |
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

- `export const SEEN_SETTLE_MS = 1500` — const, line 53
- `export const SEEN_REPORT_MS = 1500` — const, line 54
- `export const READING_MARKER = 0.7` — const, line 60
- `export function observedPassages(input:` — function, line 166
- `export function readingPositionKey(sourceId: string): string` — function, line 183
- `export interface SavedReadingPlace` — interface, line 189
- `export function encodeReadingPlace(extractionId: string, spanId: string): string` — function, line 197
- `export function decodeReadingPlace(value: string | null): SavedReadingPlace | null` — function, line 201
- `export interface OpenedReading` — interface, line 216
- `export function placeIsOnReading(saved: SavedReadingPlace, reading: OpenedReading | undefined): boolean` — function, line 230
- `export interface WatchSeekHandle` — interface, line 237
- `export type SectionFinish = "writing" | "waiting" | "done"` — type, line 242
- `export function finishOf(result: ReaderMarkProgressResultDto | null): SectionFinish | null` — function, line 244
- `export interface ReadingProgressInput` — interface, line 249
- `export interface ReadingProgress` — interface, line 280
- `export function useReadingProgress(input: ReadingProgressInput): ReadingProgress` — function, line 377

## Internal implementation anchors

- `type Dispatch, type MutableRefObject, type RefObject, type SetStateAction, } from "react"` — type, line 18
- `type MutableRefObject, type RefObject, type SetStateAction, } from "react"` — type, line 19
- `type RefObject, type SetStateAction, } from "react"` — type, line 20
- `type SetStateAction, } from "react"` — type, line 21
- `type ReadingPosition, type SectionHistory, } from "./readingPosition"` — type, line 45
- `type SectionHistory, } from "./readingPosition"` — type, line 46
- `const SEEN_RETRY_LIMIT = 3` — const, line 56
- `const PAGE_READ_THROUGH = 0.85` — const, line 61
- `const USER_SCROLL_MS = 1200` — const, line 65
- `const SCROLL_KEYS = new Set(["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " ", "Spacebar"])` — const, line 66
- `interface SeenSave` — interface, line 72
- `function seenSaveFor(saves: Map<string, SeenSave>, extractionId: string): SeenSave` — function, line 90
- `let save = saves.get(extractionId)` — let, line 91
- `type SeenSaved = (extractionId: string, sectionId: string, result: ReaderMarkProgressResultDto | null)` — type, line 105
- `function sendSeenCounts( saves: Map<string, SeenSave>, extractionId: string, onSaved?: SeenSaved, ): void` — function, line 113
- `const save = saves.get(extractionId)` — const, line 116
- `const sectionIds = new Set([...Object.keys(save.wanted), ...Object.keys(save.passages), ...save.ends])` — const, line 118
- `const counts = save.wanted[sectionId]` — const, line 120
- `const countNew = counts !== undefined && counts.spansSeen > Math.max(save.acknowledged[sectionId] ?? 0, save.sending[sectionId] ?? 0)` — const, line 121
- `const passages = [...(save.passages[sectionId] ?? [])] .filter((spanId)` — const, line 123
- `const end = save.ends.has(sectionId) && !save.acknowledgedEnds.has(sectionId) && !save.sendingEnds.has(sectionId)` — const, line 125
- `const observed = left && left !== spanId ? [left] : []` — const, line 174
- `const page = pageSpans.find((entry)` — const, line 176
- `const onPage = page === undefined ? [] : pageSpans.filter((entry)` — const, line 177
- `const index = onPage.findIndex((entry)` — const, line 178
- `const parsed = JSON.parse(value) as` — const, line 205
- `const activityRef = useReadingActivityRef()` — const, line 387
- `const paused = useWindowPaused()` — const, line 388
- `const markerPassageRef = useRef<` — const, line 403
- `const startViewRef = useRef<` — const, line 407
- `const movedRef = useRef(false)` — const, line 420
- `const setMoved = useCallback((moved: boolean)` — const, line 421
- `const userScrollAtRef = useRef(0)` — const, line 425
- `const movedPendingRef = useRef(false)` — const, line 428
- `const historyResumeRef = useRef(false)` — const, line 432
- `const placeRequestRef = useRef(0)` — const, line 441
- `const authorRequestedRef = useRef<Set<string>>(new Set())` — const, line 467
- `const authoringRef = useRef<string[]>([])` — const, line 471
- `const failedChecks = guidePlan?.checkFailedSectionIds` — const, line 475
- `const failedCheckSections = useMemo(()` — const, line 476
- `const shownTimedOutSections = useMemo( ()` — const, line 477
- `const handoffRef = useRef<ReadingPosition | null>(null)` — const, line 483
- `const jumpGuardRef = useRef(0)` — const, line 486
- `const readingRafRef = useRef<number | null>(null)` — const, line 487
- `const settleUntilRef = useRef(0)` — const, line 492
- `const seenSavesRef = useRef(new Map<string, SeenSave>())` — const, line 499
- `const activeSeenRef = useRef<string | null>(null)` — const, line 501
- `const noteFinished = useCallback((sectionId: string, result: ReaderMarkProgressResultDto | null)` — const, line 509
- `const finish = finishOf(result)` — const, line 510
- `const noteProgressSaved = useCallback((extractionId: string, sectionId: string, result: ReaderMarkProgressResultDto | null)` — const, line 518
- `const lastReadRef = useRef<` — const, line 523
- `const pageModeRef = useRef(false)` — const, line 524
- `const pageSpansRef = useRef<Array<` — const, line 525
- `const lastPlaybackSpanRef = useRef<string | null>(null)` — const, line 527
- `const resetProgress = useCallback(()` — const, line 537
- `const settleOpening = useCallback(()` — const, line 576
- `const placeAtOpen = useCallback(( sourceId: string, jumpSpan: string | undefined, handoff: ReadingPosition | null, reading?: OpenedReading, jumpReading?: string | null, )` — const, line 580
- `let placed = Boolean(handoff)` — let, line 584
- `let translating = false` — let, line 585
- `const translate = (place: SavedReadingPlace, kind: "saved" | "found")` — const, line 593
- `const request = ++placeRequestRef.current` — const, line 595
- `const openReading = reading?.extractionId ?? null` — const, line 596
- `const here = !openReading || landed.extractionId === openReading` — const, line 603
- `const jump: SavedReadingPlace | null = jumpSpan ?` — const, line 619
- `const jumpHere = jump !== null && (!jump.extractionId || placeIsOnReading(jump, reading))` — const, line 620
- `const saved = decodeReadingPlace(window.localStorage.getItem(readingPositionKey(sourceId)))` — const, line 622
- `const hydrateProgress = useCallback((extractionId: string, progress: ReaderProgressListDto)` — const, line 648
- `const seen: Record<string, number> =` — const, line 650
- `const acknowledged = seenSaveFor(seenSavesRef.current, extractionId).acknowledged` — const, line 652
- `const next =` — const, line 655
- `const pageSpans = useMemo( ()` — const, line 674
- `const pageMode = Boolean(pdfView && surface === "pdf" && !offline && pageSpans.length > 0)` — const, line 678
- `const boundaryChecksAvailable = mode === "anchor" && sectionPromptsEnabled` — const, line 682
- `const guideSectionBySpan = useMemo(()` — const, line 684
- `const map = new Map<string, ReaderGuideSectionDto>()` — const, line 685
- `const guideSectionByEnd = useMemo( ()` — const, line 691
- `const notePassages = useCallback((observed: string[])` — const, line 699
- `let next = current` — let, line 704
- `const section = guideSectionBySpan.get(spanId)` — const, line 706
- `const ended = observed.flatMap((spanId)` — const, line 713
- `const section = guideSectionBySpan.get(spanId)` — const, line 714
- `const notePassagesRef = useRef(notePassages)` — const, line 722
- `const watching = Boolean(watch || watchLoading)` — const, line 726
- `const viewNowRef = useRef<()` — const, line 727
- `const currentGuideSection = useMemo(()` — const, line 729
- `const positioned = guideSectionBySpan.get(readingSpan ?? activeSpan ?? "")` — const, line 730
- `const currentSectionProgress = useMemo(()` — const, line 733
- `const at = currentGuideSection.spanIds.indexOf(readingSpan ?? activeSpan ?? "")` — const, line 735
- `const withinPassage = pageMode && readingOffset !== null ? readingOffset : 1` — const, line 737
- `const currentSectionRead = useMemo(()` — const, line 747
- `const count = Math.max(1, currentGuideSection.spanIds.length)` — const, line 750
- `const pdfSurfaceActive = Boolean(pdfView && surface === "pdf" && !offline)` — const, line 757
- `const pdfSurfaceLoading = Boolean(!pdfView && pdfViewPending && surface === "pdf" && !offline)` — const, line 762
- `const pageBySpan = useMemo(()` — const, line 763
- `const pages = new Map<string, number>()` — const, line 764
- `const atLastPage = useMemo(()` — const, line 771
- `const here = pageBySpan.get(readingSpan ?? activeSpan ?? "")` — const, line 773
- `const last = pageBySpan.get(currentGuideSection.endSpanId)` — const, line 774
- `const checkSurface: CheckSurface = watch || watchLoading ? "watch" : pdfSurfaceActive ? "pdf" : pdfSurfaceLoading ? "loading" : "text"` — const, line 781
- `const offeredCheckSections = useMemo(()` — const, line 794
- `const sections = guidePlan?.sections ?? []` — const, line 795
- `const currentIndex = sections.findIndex((section)` — const, line 796
- `const offered = new Set<string>()` — const, line 797
- `const decision = checkOffer(` — const, line 799
- `const unpinned = [...offeredCheckSections].filter((id)` — const, line 824
- `const openQuestionSections = useMemo( ()` — const, line 831
- `const pendingQuickCheckCount = boundaryChecksAvailable ? openQuestionSections.filter((section)` — const, line 837
- `const section = currentGuideSection` — const, line 852
- `const offered = (offeredCheckSections.has(section.id) && section.question?.readingPhase === "after_section") || section.suggestedPassages.length > 0` — const, line 854
- `const currentQuestionOpen = useMemo( ()` — const, line 859
- `const pdfOfferSection = useMemo(()` — const, line 865
- `const sections = guidePlan?.sections ?? []` — const, line 867
- `const currentIndex = sections.findIndex((section)` — const, line 868
- `const offered = openQuestionSections.filter((section)` — const, line 869
- `const index = sections.findIndex((entry)` — const, line 870
- `const readingProgress = useMemo(()` — const, line 875
- `const at = blocks.findIndex((block)` — const, line 877
- `const sections = guidePlan?.sections ?? []` — const, line 887
- `const index = sections.findIndex((section)` — const, line 888
- `const at = currentGuideSection.spanIds.indexOf(readingSpan ?? "")` — const, line 889
- `const last = lastReadRef.current` — const, line 890
- `const marker = markerPassageRef.current` — const, line 892
- `const forward = marker !== null && (marker.sectionIndex < index || (marker.sectionIndex === index && marker.spanIndex < at))` — const, line 898
- `const count = currentGuideSection.spanIds.length` — const, line 904
- `const seenHere = pageMode ? at + ((readingOffset ?? 0) >= PAGE_READ_THROUGH ? 1 : 0) : at + 1` — const, line 905
- `const next =` — const, line 907
- `let changed = false` — let, line 908
- `const raise = (id: string, value: number)` — const, line 909
- `const extractionId = render.extractionId` — const, line 932
- `const saves = seenSavesRef.current` — const, line 933
- `const save = seenSaveFor(saves, extractionId)` — const, line 934
- `const counts = new Map((guidePlan?.sections ?? []).map((section)` — const, line 935
- `const spanCount = counts.get(sectionId)` — const, line 937
- `const kept = (save.passages[sectionId] ??= new Set())` — const, line 943
- `const timer = window.setTimeout(()` — const, line 948
- `const saves = seenSavesRef.current` — const, line 952
- `const section = currentGuideSection` — const, line 966
- `const extractionId = render.extractionId` — const, line 975
- `const result = await api.readerAuthorSectionQuestion(` — const, line 978
- `const retryQuickCheck = useCallback( (sectionId: string)` — const, line 989
- `const extractionId = render.extractionId` — const, line 994
- `const openQuickCheck = useCallback((sectionId: string)` — const, line 1007
- `const frame = window.requestAnimationFrame(()` — const, line 1016
- `const card = railRef.current?.querySelector(`[data-quick-check="$` — const, line 1017
- `const extractionId = render.extractionId` — const, line 1027
- `let attempts = 0` — let, line 1028
- `const timer = window.setInterval(()` — const, line 1029
- `const stalled = authoringRef.current` — const, line 1032
- `const failed = new Set(plan.checkFailedSectionIds ?? [])` — const, line 1049
- `const refreshGuidePlan = useCallback((plan: ReaderGuidePlanDto)` — const, line 1065
- `const updateReadingPosition = useCallback(()` — const, line 1070
- `const container = bodyRef.current` — const, line 1071
- `const position = pagePositionAt(container, READING_MARKER)` — const, line 1076
- `const spanId = position ? spanOnPage(pageSpansRef.current, position) : null` — const, line 1077
- `const containerRect = container.getBoundingClientRect()` — const, line 1084
- `const markerY = containerRect.top + containerRect.height * READING_MARKER` — const, line 1085
- `const nodes = Array.from(container.querySelectorAll<HTMLElement>("[data-span-id]"))` — const, line 1086
- `const last = nodes[nodes.length - 1]` — const, line 1087
- `const lastRect = last?.getBoundingClientRect()` — const, line 1088
- `let best: HTMLElement | null = null` — let, line 1092
- `let bestDistance = Number.POSITIVE_INFINITY` — let, line 1093
- `const rect = node.getBoundingClientRect()` — const, line 1095
- `const distance = Math.abs(Math.min(Math.max(markerY, rect.top), rect.bottom) - markerY)` — const, line 1097
- `const onReadingScroll = useCallback(()` — const, line 1106
- `const now = Date.now()` — const, line 1107
- `const own = movedPendingRef.current || movedRef.current` — const, line 1113
- `const start = startViewRef.current` — const, line 1126
- `const fresh = start !== null && Date.now() - start.at < USER_SCROLL_MS` — const, line 1128
- `const frame = window.requestAnimationFrame(updateReadingPosition)` — const, line 1134
- `const revealSection = useCallback( (sectionId: string)` — const, line 1142
- `const completeSection = useCallback( (sectionId: string, by?: "check_closed" | "idea_chosen"): Promise<ReaderMarkProgressResultDto | null>` — const, line 1157
- `const revealSegment = useCallback((page: number, spanId: string, align: PassageAlign = "center")` — const, line 1180
- `const jumpToSpan = useCallback( (spanId: string, align: PassageAlign = "center")` — const, line 1184
- `const geometry = pdfView.blocks.find((block)` — const, line 1200
- `const page = pageBySpan.get(spanId)` — const, line 1207
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1214
- `const reduced = typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches` — const, line 1218
- `const noteFoundApproximate = useCallback((approximate: boolean)` — const, line 1224
- `const notePlacement = useCallback(()` — const, line 1226
- `const spanId = resumeSpanFromHistory(guidePlan.sections, readingHistory)` — const, line 1242
- `const noteMovementStart = useCallback(()` — const, line 1262
- `const now = Date.now()` — const, line 1263
- `const start = startViewRef.current` — const, line 1265
- `const kept = start !== null && now - start.at < USER_SCROLL_MS ? start.spanIds : []` — const, line 1266
- `const noteUserScroll = useCallback(()` — const, line 1269
- `const onPlaybackSpan = useCallback((spanId: string | null, advancing: boolean)` — const, line 1280
- `const last = lastPlaybackSpanRef.current` — const, line 1281
- `const onPlaybackSeek = useCallback((spanId: string | null)` — const, line 1297
- `const hub = useListenerHub()` — const, line 1305
- `const onKey = (event: KeyboardEvent)` — const, line 1308
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 1310
- `const frame = window.requestAnimationFrame(()` — const, line 1327
- `const geometry = pdfView.blocks.find((block)` — const, line 1329
- `const page = (pdfView.pageSpans ?? []).find((entry)` — const, line 1335
- `const element = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1339
- `const position = handoffRef.current` — const, line 1352
- `const spanId = spanAtPosition(pdfView.blocks, position) ?? spanOnPage(pdfView.pageSpans ?? [], position)` — const, line 1355
- `const noteRestored = useCallback((spanId: string | null)` — const, line 1364

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
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useListenerHub`, `useReadingActivityRef`, `useWindowPaused`
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
- [apps/learnloop-tauri/src/screens/reader/sectionEnd.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sectionEnd.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/readingPathsRefresh.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readingPathsRefresh.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/readerHooks.parity.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readerHooks.parity.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/ReadingPathCard.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/ReadingPathCard.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/ReaderScreen.review.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/ReaderScreen.review.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

---
title: "Desktop module · src/screens/ReaderScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.ReaderScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/ReaderScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/ReaderScreen.tsx"
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

# `src/screens/ReaderScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `ReaderScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/ReaderScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/ReaderScreen.tsx) |
| Source lines | 4705 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]]

## Public API

- `export interface ReaderOpenSource` — interface, line 237
- `export interface ReaderCheckMeRequest extends CueCheckMeRequest` — interface, line 253
- `export type ReaderExerciseRequest = ReaderWorkbenchExercise &` — type, line 266
- `export const SIDE_PATH_COPY =` — const, line 270
- `export function ReaderScreen(` — function, line 292

## Internal implementation anchors

- `type AnnotationSegment, type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 142
- `type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 143
- `type ReaderSelection, } from "./reader/readerShared"` — type, line 144
- `const NO_SECTIONS: never[] = []` — const, line 148
- `const READER_MODE_OPTIONS = [` — const, line 149
- `const TAG_ACTIONS: Array<` — const, line 159
- `const WHOLE_BLOCK_QUOTE = "(whole block)"` — const, line 167
- `type ReaderRailTab = "guide" | "ask" | "notes"` — type, line 169
- `const HEALTH_COLOR: Record<string, "green" | "amber" | "pink" | "slate"> =` — const, line 171
- `const FIGURE_PAGE_NOT_OPENED = "That page couldn't be opened."` — const, line 179
- `type OpenOutcome = "opened" | "preparing" | "not_opened"` — type, line 182
- `interface OfferedPress` — interface, line 186
- `const OFFER_OUTCOME: Record<FigureRequestOutcome, ExplorableOutcome> =` — const, line 197
- `const BADGED_HEALTH = new Set(["suspect", "failed"])` — const, line 203
- `interface RemovedAnnotation` — interface, line 207
- `const UNDO_REMOVE_MS = 10_000` — const, line 217
- `function newKey(): string` — function, line 219
- `function identityOf(view: Pick<ReaderRenderViewDto, "sourceId" | "revisionId" | "extractionId">): SourceIdentity` — function, line 228
- `function sectionIdentity(section:` — function, line 233
- `const mainPaneOwnsCueKey = (event: KeyboardEvent): boolean` — const, line 277
- `interface IntentPane` — interface, line 282
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 342
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 346
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 355
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 356
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 357
- `const openingRef = useRef<string | null>(null)` — const, line 363
- `const askPanelOn = algoConfig().ask !== null` — const, line 384
- `const storedStyle = useStoredHelpStyle()` — const, line 385
- `const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen` — const, line 386
- `const pdfViewRequestRef = useRef(0)` — const, line 408
- `const sourceEpochRef = useRef(0)` — const, line 439
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 450
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 451
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 452
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 453
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 454
- `const modeSaveVersionRef = useRef(0)` — const, line 455
- `const answerModeSaveVersionRef = useRef(0)` — const, line 456
- `const enabled = contract?.readerEnabled ?? true` — const, line 472
- `const inquiry = contract?.inquiryEnabled === true` — const, line 475
- `const muted = inquiry && mode === "skim"` — const, line 478
- `const intentContract = inquiry && !offline ? contract?.intent ?? null : null` — const, line 481
- `const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading)` — const, line 482
- `const openFigureSource = useRef<((extractionId: string, spanId: string)` — const, line 486
- `const figureOpenSource = useCallback((extractionId: string, spanId: string)` — const, line 487
- `const figuresCtl = useFigures(` — const, line 488
- `const figureOffersOn = Boolean(contract?.figures?.offers) && !offline` — const, line 494
- `const showMeOn = Boolean(contract?.figures?.showMe) && !offline` — const, line 498
- `const waitingOfferRef = useRef<OfferedPress | null>(null)` — const, line 504
- `const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome)` — const, line 509
- `const press = offeredFigure` — const, line 516
- `const open = render?.extractionId ?? null` — const, line 518
- `const readerTutor = contract?.readerTutor ?? null` — const, line 541
- `const askWorkbenchSessionRef = useRef<string | null>(null)` — const, line 543
- `const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true` — const, line 548
- `const askPersonalizedRef = useRef<boolean | null>(null)` — const, line 549
- `const askComposerAnchorRef = useRef<AskAnchor | null>(null)` — const, line 554
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 560
- `const renderBlocksBySpan = useMemo( ()` — const, line 564
- `const visit = useReaderVisit(` — const, line 570
- `const showGuideRail = useCallback(()` — const, line 576
- `const progress = useReadingProgress(` — const, line 580
- `const doseVisitId = useCallback(()` — const, line 597
- `const refreshAnnotations = useCallback(async ()` — const, line 599
- `const epoch = sourceEpochRef.current` — const, line 601
- `const result = await cachedSourceRead( render.sourceId, ["reader_source_annotations", render.sourceId, render.extractionId], ()` — const, line 605
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 612
- `const version = (r.version as Record<string, unknown>) ??` — const, line 615
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 616
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 617
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 618
- `const placement = r.placement as ReaderAnnotationPlacementDto | undefined` — const, line 619
- `let page: number | null = null` — let, line 629
- `let bbox: number[] | null = null` — let, line 630
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 632
- `const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?:` — const, line 650
- `const openCardRef = useRef<SourceLibraryCard | null>(null)` — const, line 675
- `const openExtractionRef = useRef<string | null>(null)` — const, line 677
- `const reloadGuidePlan = useCallback(async ()` — const, line 679
- `const extractionId = render.extractionId` — const, line 681
- `const plan = await readGuidePlan(render.sourceId, extractionId,` — const, line 683
- `const spanOrder = useMemo( ()` — const, line 696
- `const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none"` — const, line 700
- `const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 703
- `const card = openCardRef.current` — const, line 704
- `const wbProps = useMemo<ReaderWorkbenchProps | undefined>(()` — const, line 714
- `const submitted = workbench?.onSubmitted` — const, line 715
- `const trail = besideTrail(returnStackRef.current)` — const, line 720
- `const wbCtl = useReaderWorkbench(` — const, line 725
- `const working = wbCtl.active !== null` — const, line 732
- `const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline` — const, line 736
- `const alsoHidden = alsoPrefs ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId)) : Boolean(contract?.correspondence?.hiddenEverywhere) || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.so…` — const, line 741
- `const peekCrumbShown = alsoPeek ?? findPeek` — const, line 751
- `const pathRefreshKey = readingPathRefreshKey(` — const, line 766
- `const tryFirstRef = useRef<((spanId: string)` — const, line 780
- `const cueCtl = useReaderCues(` — const, line 781
- `const recapCtl = useReaderRecap(` — const, line 796
- `const recapShown = Boolean(recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working)` — const, line 810
- `const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip")` — const, line 821
- `const root = history.find((entry)` — const, line 822
- `const recapRevisited = useCallback((rootId: string)` — const, line 835
- `const root = history.find((entry)` — const, line 836
- `const recapRevisit = useCallback(async (rootId: string)` — const, line 839
- `const root = history.find((entry)` — const, line 840
- `const recapOpenInquiry = useCallback((rootId: string, spanId: string)` — const, line 846
- `const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch")` — const, line 849
- `const cueMarksFor = (markSurface: "pdf" | "watch")` — const, line 869
- `let cancelled = false` — let, line 878
- `const scroller = railRef.current` — const, line 911
- `const clamp = ()` — const, line 913
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 914
- `const observer = new ResizeObserver(clamp)` — const, line 917
- `const query = librarySearch.trim()` — const, line 928
- `let cancelled = false` — let, line 935
- `const timer = window.setTimeout(()` — const, line 938
- `const resetSourceState = useCallback(()` — const, line 961
- `const openSource = useCallback( async ( card: SourceLibraryCard, jumpSpan?: string, // jumpReading: the reading jumpSpan was found on (a search hit, a // return)` — const, line 1010
- `const handoff = options.handoff ?? null` — const, line 1020
- `const view = options.view ?? await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 1038
- `const pdfRequest = ++pdfViewRequestRef.current` — const, line 1085
- `const current = ()` — const, line 1086
- `const openFixture = useCallback(()` — const, line 1121
- `const backToLibrary = useCallback(()` — const, line 1129
- `const spanId = readingSpan ?? activeSpan` — const, line 1133
- `const section = guidePlan?.sections.find((candidate)` — const, line 1134
- `const resumedRef = useRef(false)` — const, line 1152
- `const trail = initialSource.besideTrail ?? null` — const, line 1156
- `const activeBlock = useMemo(()` — const, line 1170
- `const pdfHighlights: PdfHighlight[] = useMemo(()` — const, line 1179
- `const list: PdfHighlight[] = []` — const, line 1180
- `const base =` — const, line 1183
- `const placed = highlightFromPlacement(base, a.placement)` — const, line 1185
- `const segments = a.segments.flatMap((s)` — const, line 1190
- `const annotatedSpans = useMemo( ()` — const, line 1197
- `const boundaryBlock = useMemo(()` — const, line 1201
- `const revealedPassages = useMemo(()` — const, line 1203
- `const revealed = new Set(revealedSections)` — const, line 1204
- `const map = new Map<string,` — const, line 1205
- `const revealedGuidanceSpans = useMemo(()` — const, line 1214
- `const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null` — const, line 1219
- `const protectedSelection = selectionProtected(protection, selection)` — const, line 1220
- `const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1221
- `const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan))` — const, line 1225
- `const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1226
- `const editCaptureText = useCallback((text: string)` — const, line 1231
- `const resetCaptureText = useCallback(()` — const, line 1234
- `const saveAnnotationEdit = useCallback(async ()` — const, line 1246
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 1268
- `const result = await api.readerReanchor(` — const, line 1272
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1289
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1312
- `const target = annotations.find((a)` — const, line 1313
- `const reading = render ?` — const, line 1314
- `const epoch = sourceEpochRef.current` — const, line 1315
- `const undoRemove = useCallback(async ()` — const, line 1330
- `const last = removed` — const, line 1331
- `const epoch = sourceEpochRef.current` — const, line 1337
- `const result = await api.readerRestoreAnnotation(` — const, line 1339
- `const timer = window.setTimeout(()` — const, line 1352
- `const onKey = (event: KeyboardEvent)` — const, line 1358
- `const target = event.target` — const, line 1361
- `const openAnnotationNote = useCallback((annotationId: string)` — const, line 1370
- `const target = annotations.find((a)` — const, line 1371
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1383
- `const sel = window.getSelection()` — const, line 1384
- `const container = bodyRef.current` — const, line 1385
- `const range = sel.getRangeAt(0)` — const, line 1387
- `const nodes: Array<` — const, line 1388
- `const seen = new Set<string>()` — const, line 1389
- `const spanId = el.dataset.spanId` — const, line 1391
- `let intersects = false` — let, line 1393
- `const sub = document.createRange()` — const, line 1400
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1408
- `const block = renderBlocksBySpan.get(spanId)` — const, line 1413
- `const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1423
- `const cancelIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1424
- `const selectionSpanIds = useMemo( ()` — const, line 1425
- `const intentBox = useIntentBox(` — const, line 1429
- `const openActiveRail = useCallback(()` — const, line 1443
- `const activeCtl = useActiveReading(` — const, line 1447
- `const libraryCtl = useLibraryAsk(` — const, line 1456
- `const keptCtl = useKeptComparisons(` — const, line 1458
- `const notesCtl = useNoteMarks(` — const, line 1460
- `const pdfMarks = (): ReadonlyMap<string, ReactNode> | null` — const, line 1465
- `const cues = cueMarksFor("pdf")` — const, line 1466
- `const merged = new Map<string, ReactNode>(cues ?? [])` — const, line 1468
- `const cue = merged.get(spanId)` — const, line 1470
- `const before = merged.get(spanId)` — const, line 1475
- `const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null)` — const, line 1481
- `const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint)` — const, line 1483
- `const sbs = useSideBySide(` — const, line 1485
- `const node = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1493
- `const sbsPanes = sbs.panes && !comparing` — const, line 1506
- `const sbsPanesRef = useRef(false)` — const, line 1507
- `const sbsShownRef = useRef(false)` — const, line 1512
- `const sbsRef = useRef(sbs)` — const, line 1514
- `const sbsEscBusyRef = useRef(false)` — const, line 1517
- `const sbsPaneRef = useRef<HTMLDivElement | null>(null)` — const, line 1519
- `const runSideIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1524
- `const cancelSideIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1525
- `const sbsSection = sbs.section && sbs.target && sbs.section.sectionId === sbs.target.sectionId ? sbs.section : null` — const, line 1526
- `type BesideRun = |` — type, line 1541
- `const besideSeq = useRef(0)` — const, line 1550
- `const besideRunRef = useRef<(run: BesideRun)` — const, line 1553
- `const besideDroppedRef = useRef<(run: BesideRun)` — const, line 1554
- `const openBesideRef = useRef<(hit:` — const, line 1555
- `const snapshotBesideRef = useRef<(spanId: string)` — const, line 1562
- `const shown = sbsRef.current.target` — const, line 1564
- `const takeBesideBook = useCallback((book: SourceIdentity, spanId: string, run: BesideRun)` — const, line 1568
- `const id = ++besideSeq.current` — const, line 1570
- `const sideExtractionRef = useRef<string | null>(null)` — const, line 1582
- `const checkMeFromSideCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 1583
- `const side = useSidePane(` — const, line 1588
- `const besideRanRef = useRef(0)` — const, line 1617
- `const handoff = besideHandoff` — const, line 1619
- `const card = openCardRef.current` — const, line 1634
- `const trail = besideTrail(returnStackRef.current)` — const, line 1636
- `const work = handoff.run` — const, line 1645
- `const openComposer = useCallback((anchor: AskAnchor | null)` — const, line 1659
- `const sbsRowRef = useRef<HTMLDivElement | null>(null)` — const, line 1677
- `const startSbsResize = (event: ReactPointerEvent<HTMLDivElement>)` — const, line 1678
- `const row = sbsRowRef.current` — const, line 1679
- `const rect = row.getBoundingClientRect()` — const, line 1682
- `const move = (moved: PointerEvent)` — const, line 1683
- `const up = ()` — const, line 1686
- `const touchMain = ()` — const, line 1698
- `const onKey = (event: KeyboardEvent)` — const, line 1707
- `const target = event.target` — const, line 1709
- `const ctl = sbsRef.current` — const, line 1711
- `const open = ctl.panes || ctl.sheet` — const, line 1712
- `const shown = sbsShownRef.current` — const, line 1713
- `const mod = event.ctrlKey || event.metaKey` — const, line 1714
- `const side = sbsPaneRef.current` — const, line 1724
- `const inSide = target instanceof Element && Boolean(target.closest("[data-side-by-side-pane]"))` — const, line 1725
- `const inMain = target instanceof Node && Boolean(bodyRef.current?.contains(target))` — const, line 1731
- `const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false, anchor?: SourceIdentity)` — const, line 1741
- `const identity = anchor ?? identityOf(render)` — const, line 1748
- `const request =` — const, line 1749
- `const closeLibrary = useCallback(()` — const, line 1754
- `const onKey = (event: KeyboardEvent)` — const, line 1761
- `const onMouseUp = useCallback(()` — const, line 1772
- `const sel = window.getSelection()` — const, line 1773
- `const quote = sel.toString().replace(/\s+/g, " ").trim()` — const, line 1775
- `const nodes = collectSelectionNodes()` — const, line 1777
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1806
- `const domDragRef = useRef<` — const, line 1807
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1809
- `const host = bodyRef.current` — const, line 1810
- `const rect = host.getBoundingClientRect()` — const, line 1812
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1816
- `const target = event.target as Node` — const, line 1820
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1822
- `const domDrafting = domDraft !== null` — const, line 1834
- `const rectFrom = (drag:` — const, line 1837
- `const onMove = (event: MouseEvent)` — const, line 1843
- `const drag = domDragRef.current` — const, line 1844
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1846
- `const onUp = (event: MouseEvent)` — const, line 1849
- `const drag = domDragRef.current` — const, line 1850
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1854
- `const rect = rectFrom(drag, point)` — const, line 1856
- `const next = [...domBoxesRef.current, rect]` — const, line 1859
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1876
- `const host = bodyRef.current` — const, line 1877
- `const hostRect = host.getBoundingClientRect()` — const, line 1879
- `const clientBoxes = boxes.map((b)` — const, line 1880
- `const nodes: Array<` — const, line 1886
- `const seen = new Set<string>()` — const, line 1887
- `const spanId = el.dataset.spanId` — const, line 1889
- `const elRect = el.getBoundingClientRect()` — const, line 1891
- `const touches = clientBoxes.some( (b)` — const, line 1892
- `const words: string[] = []` — const, line 1896
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 1897
- `const text = node as Text` — const, line 1899
- `const wordPattern = /\S+/g` — const, line 1900
- `let match: RegExpExecArray | null` — let, line 1901
- `const range = document.createRange()` — const, line 1903
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 1906
- `const cx = (Math.min(...rects.map((r)` — const, line 1908
- `const cy = (Math.min(...rects.map((r)` — const, line 1909
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 1913
- `const commitDomBoxes = useCallback(()` — const, line 1922
- `const boxes = domBoxesRef.current` — const, line 1923
- `const nodes = resolveDomBoxes(boxes)` — const, line 1925
- `const quote = nodes.map((n)` — const, line 1931
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 1940
- `const clearDomBoxes = ()` — const, line 1948
- `const onKeyDown = (event: KeyboardEvent)` — const, line 1954
- `const onKeyUp = (event: KeyboardEvent)` — const, line 1959
- `const onBlur = ()` — const, line 1965
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 1987
- `const point = domPointFromClient(request.x, request.y)` — const, line 1989
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 1990
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 2011
- `const retryRequest = useCallback(async (requestId: string)` — const, line 2024
- `const optimisticSegments = useCallback( (nodes: string | Array<string |` — const, line 2038
- `const list = Array.isArray(nodes) ? nodes : [nodes]` — const, line 2040
- `const spanId = typeof node === "string" ? node : node.spanId` — const, line 2042
- `const geometry = pdfView?.blocks.find((b)` — const, line 2043
- `const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number" ?` — const, line 2044
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 2056
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 2060
- `const quotedNodes = (()` — const, line 2065
- `const multi = collectSelectionNodes()` — const, line 2068
- `const optimisticIds = quotedNodes ?? [target.spanId]` — const, line 2071
- `const nodes = quotedNodes ?? [` — const, line 2081
- `const receipt = await api.readerCapture(` — const, line 2082
- `const handler = (event: KeyboardEvent)` — const, line 2109
- `const clearSelection = useCallback(()` — const, line 2121
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 2133
- `const segment = a.segments.find((s)` — const, line 2135
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 2142
- `const alsoKeyRef = useRef<()` — const, line 2152
- `const onKey = (event: KeyboardEvent)` — const, line 2160
- `const target = event.target` — const, line 2163
- `const tabs: ReaderRailTab[] = ["guide", "ask", "notes"]` — const, line 2165
- `const askRequestSeen = useRef(askRequest)` — const, line 2203
- `const revealAskRef = useRef<()` — const, line 2205
- `const startCompareRef = useRef<(request: CompareRequest)` — const, line 2230
- `const sideAnchor = Boolean(side.extractionId) && side.extractionId === request.extractionId` — const, line 2233
- `const request = compareWaitsForWork` — const, line 2240
- `const sideMarksChanged = side.marksChanged` — const, line 2250
- `const captureIn = useCallback(async (target: PaneCaptureTarget, what:` — const, line 2251
- `const common =` — const, line 2256
- `const receipt: ReaderPresetReceiptDto = "preset" in what ? await api.readerInvokePreset(` — const, line 2261
- `const drained = await api.readerDrainOutbox()` — const, line 2272
- `const invokePreset = useCallback( // RW1b: the intent box passes its own words as the annotation's learner // text, and names the intention and entry in the funnel event. // Reader CA6b: `target` is side by side's second pane (its book, revision, // reading a…` — const, line 2293
- `const note_ = learnerTextOverride ?? note` — const, line 2301
- `const nodes = selectionNodes(selection)` — const, line 2302
- `const editedText = selection.editedText?.trim()` — const, line 2303
- `const receipt = await api.readerInvokePreset(` — const, line 2315
- `const drained = await api.readerDrainOutbox()` — const, line 2339
- `const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>, target?: PaneCaptureTarget): Promise<string | null>` — const, line 2362
- `const note_ = learnerTextOverride ?? note` — const, line 2366
- `const nodes = selectionNodes(selection)` — const, line 2367
- `const receipt = await api.readerCapture(` — const, line 2379
- `const pauseArc = useCallback(async ()` — const, line 2407
- `const next = await api.readerArc(` — const, line 2411
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 2418
- `const next = await api.readerArc(` — const, line 2423
- `const importJobRef = useRef<` — const, line 2435
- `const importExercise = useCallback(async (target?: PaneCaptureTarget): Promise<string | null>` — const, line 2438
- `const nodes = target ? target.nodes : selectionNodes(selection!)` — const, line 2440
- `const editedText = target ? undefined : selection!.editedText?.trim()` — const, line 2441
- `const receipt = await api.readerImportExercise(target ?` — const, line 2444
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 2492
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 2493
- `const timer = setInterval(async ()` — const, line 2497
- `const status = await api.readerExerciseImportStatus(` — const, line 2499
- `const job = importJobRef.current` — const, line 2500
- `const waited = Date.now() - job.startedAt` — const, line 2503
- `const saveOwnQuestion = useCallback(async ()` — const, line 2530
- `const saved = await api.readerAuthorQA(` — const, line 2538
- `const runCoach = useCallback(async ()` — const, line 2559
- `const lint = await api.readerCoachLint(` — const, line 2562
- `const changeMode = useCallback( async (next: string)` — const, line 2573
- `const previous = mode` — const, line 2575
- `const version = ++modeSaveVersionRef.current` — const, line 2578
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 2589
- `const answerModeNext = next as ReaderAnswerMode` — const, line 2591
- `const previous = answerMode` — const, line 2592
- `const version = ++answerModeSaveVersionRef.current` — const, line 2595
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 2611
- `const renderInquiryTop = useCallback((root: ReaderExchange)` — const, line 2626
- `const line = reconnect && reconnect.rootId === root.id && !muted ? ( <ReconnectLine placement="rail" question=` — const, line 2629
- `const check = inquiryChecks[root.id]` — const, line 2639
- `const inlineReconnect = reconnect && reconnect.inline && !muted ? ( <ReconnectLine placement="inline" question=` — const, line 2667
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 2678
- `const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, pinned?: ReaderRenderViewDto): Promise<OpenOutcome>` — const, line 2697
- `const card = (library ?? []).find((candidate)` — const, line 2702
- `const spanId = readingSpan ?? activeSpan` — const, line 2705
- `const onOriginal = pdfView && surface === "pdf" && !offline` — const, line 2731
- `const epoch = sourceEpochRef.current` — const, line 2744
- `const sameBook = Boolean(render && sourceId === render.sourceId)` — const, line 2747
- `const card = (library ?? []).find((candidate)` — const, line 2748
- `const landed = await api.readerSavedPlace(` — const, line 2753
- `const landing = await api.readerRenderView(` — const, line 2767
- `const openFollowedFigure = (figure: CorrespondentFigureDto, hit: CorrespondentSectionDto)` — const, line 2777
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2779
- `const compareFoundSection = (hit: CorrespondentSectionDto)` — const, line 2794
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2796
- `const hideAlsoInBooks = (scope: "book" | "everywhere")` — const, line 2819
- `const before = alsoPrefs ??` — const, line 2821
- `const base = contract` — const, line 2828
- `const makeExplorable = (target: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, origin: "library" | "tutor", offerRef: string): Promise<ExplorableOutcome>` — const, line 2845
- `let settle: (outcome: ExplorableOutcome)` — let, line 2852
- `const settled = new Promise<ExplorableOutcome>((resolve)` — const, line 2853
- `const press: OfferedPress =` — const, line 2854
- `const peekWorkbenchPassage = (spanId: string, target?: PassageTarget)` — const, line 2873
- `const exerciseSettings = libraryCtl.enabled ? contract?.libraryExercises ?? null : null` — const, line 2884
- `const exerciseCard = (sourceId: string | null)` — const, line 2885
- `const useExercise = (candidate: ExerciseCandidate)` — const, line 2889
- `const card = exerciseCard(candidate.sourceId ?? render?.sourceId ?? null)` — const, line 2890
- `const openExerciseInBook = (candidate: ExerciseCandidate)` — const, line 2899
- `const sourceId = candidate.sourceId ?? render?.sourceId ?? null` — const, line 2900
- `const exerciseProps: LibraryExercisesProps | null = exerciseSettings ?` — const, line 2903
- `const pickLibraryPagePractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 2917
- `const hit = libraryCtl.state?.ask.value?.hits[0]` — const, line 2918
- `const card = hit ? (library ?? []).find((candidate)` — const, line 2919
- `const readySources = library ?? []` — const, line 2962
- `const useShelf = Boolean(shelf) && !sidecarDown` — const, line 2964
- `const card = (library ?? []).find((candidate)` — const, line 3022
- `const card = (library ?? []).find((c)` — const, line 3043
- `const receiptId = searchResults.retrievalReceiptId` — const, line 3049
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 3094
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 3095
- `const wbActive = wbCtl.active` — const, line 3138
- `const wbStacked = working && wbCtl.narrow` — const, line 3139
- `const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible)` — const, line 3142
- `const wbSourceShown = !wbStacked || wbCtl.sheetOpen` — const, line 3143
- `const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry)` — const, line 3144
- `const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>()` — const, line 3145
- `const first = entry.spanIds[0]` — const, line 3147
- `const wbLabel = (stem: string)` — const, line 3150
- `const title = problemTitle(stem)` — const, line 3151
- `const tryPathExercise = (exercise: ReadingPathExerciseDto)` — const, line 3156
- `const workThroughSelection = ()` — const, line 3164
- `const nodes = selectionNodes(selection)` — const, line 3166
- `const editedText = selection.editedText?.trim()` — const, line 3167
- `const foldBlocks = contract?.activeReading?.foldBlocks ?? 3` — const, line 3184
- `const localFold = (spanIds: string[]): string[]` — const, line 3185
- `const positions = spanIds.map((spanId)` — const, line 3186
- `const last = Math.max(...positions)` — const, line 3188
- `const mainPane: IntentPane =` — const, line 3197
- `const sidePane: IntentPane | null = side.extractionId ?` — const, line 3206
- `const sideMeta = (pane: IntentPane): Record<string, string>` — const, line 3216
- `const runIntentIn = (pane: IntentPane, action: ReaderIntentActionDto, text: string, how: IntentRunHow): Promise<IntentRunHandle | null> | void` — const, line 3218
- `const meta =` — const, line 3219
- `const effect = action.effect` — const, line 3220
- `const sideSection = pane.side?.section ?? null` — const, line 3221
- `const anchor: AskAnchor =` — const, line 3227
- `const target = pane.side.target` — const, line 3268
- `const target = pane.side.target` — const, line 3274
- `const target = pane.side.target` — const, line 3280
- `const target = pane.side.target` — const, line 3290
- `const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null` — const, line 3335
- `const request: CompareRequest =` — const, line 3336
- `const region = pane.region` — const, line 3368
- `const words = text?.trim()` — const, line 3369
- `const sideShows = (extractionId: string, spanId: string): boolean` — const, line 3390
- `const checkBeside = (book: SourceIdentity, spanId: string, practiceItemId: string, proposalId: string | null)` — const, line 3393
- `const workThroughImported = (item:` — const, line 3398
- `const imported = exerciseImport` — const, line 3399
- `const spanIds = imported?.spanIds ?? (activeSpan ? [activeSpan] : [])` — const, line 3400
- `const settleShowMeLine = (key: string, patch: Partial<ShowMeLine>)` — const, line 3408
- `const requestShowMe = (ctl: FiguresCtl, run: Extract<BesideRun,` — const, line 3411
- `const key = run.lineKey` — const, line 3412
- `const runOnBook = (about: AskAbout, run: Extract<BesideRun,` — const, line 3424
- `const showMeFromAsk = ()` — const, line 3449
- `const goal = question.trim()` — const, line 3450
- `const about = parentExchange ? parentExchange.about ?? null : askComposerAnchor?.about ?? null` — const, line 3451
- `const home = parentExchange?.spanId ?? (about ? askComposerAnchor?.spanId : undefined) ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan` — const, line 3452
- `const key = `show_me:$` — const, line 3455
- `const run =` — const, line 3458
- `const cancelIntentIn = (pane: IntentPane, cancel: IntentCancel)` — const, line 3467
- `const kind = cancel.action.effect.kind` — const, line 3468
- `const annotationId = handle.annotationId` — const, line 3475
- `const batchId = handle.importBatchId` — const, line 3492
- `const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number)` — const, line 3506
- `const spanId = wbCtl.close(session,` — const, line 3508
- `const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3514
- `const card = openCardRef.current` — const, line 3515
- `const asked = libraryCtl.state?.request` — const, line 3519
- `const resumeMark = (spanId: string | null | undefined)` — const, line 3527
- `const entry = spanId ? wbResumeBySpan.get(spanId) : undefined` — const, line 3528
- `const verb = entry.status === "abandoned" ? "Reopen" : "Resume"` — const, line 3530
- `const target = event.target` — const, line 3657
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 3832
- `const active = activeSpan === block.spanId` — const, line 3833
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 3834
- `const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null` — const, line 3835
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 3836
- `const endQuestionAvailable = Boolean(endSection && endSection.question?.readingPhase === "after_section" && offeredCheckSections.has(endSection.id))` — const, line 3838
- `const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId))` — const, line 3842
- `const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""))` — const, line 3843
- `const offerSection = endSection && !muted && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 3844
- `const sel = window.getSelection()` — const, line 3863
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 3864
- `const cue = side.cues.markOn(spanId)` — const, line 3954
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 3982
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 4005
- `const active = railTab === tab` — const, line 4118
- `const waiting = tab === "guide" && pendingQuickCheckCount > 0` — const, line 4122
- `const marked = tab === "ask" && askTabMarked && !active` — const, line 4123
- `const params = (action.params ??` — const, line 4270
- `const run =` — const, line 4542
- `const book = exchange?.about ?? render` — const, line 4551

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`; references `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CorrespondentFigureDto`, `CorrespondentSectionDto`, `FigurePassageDto`, `FigureViewDto`, `LibraryAskEntry`, `LibraryHitDto`, `PassageTarget`, `ProposedItemDto`, `ReaderAnnotationPlacementDto`, `ReaderAnswerMode`, `ReaderArcDto`, `ReaderCoachLintDto`, `ReaderCueDto`, `ReaderDisposition`, `ReaderGuidePlanDto`, `ReaderGuideSectionDto`, `ReaderImportExerciseInput`, `ReaderIntentActionDto`, `ReaderPdfViewDto`, `ReaderPresetReceiptDto`, `ReaderPromptContractDto`, `ReaderRenderBlockDto`, `ReaderRenderViewDto`, `ReaderSourceSearchDto`, `ReaderWatchPlanDto`, `ReadingPathExerciseDto`, `SourceIdentity`, `SourceLibraryCard`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export; imports `setQueryData`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export; imports `PdfReaderPane`, `PdfReaderPaneHandle`, `TagMenuRequest`
- [[Reference/Desktop/TypeScript/components/RectUnionOverlay|src/components/RectUnionOverlay.tsx]] — import-or-re-export; imports `RectUnionOverlay`
- [[Reference/Desktop/TypeScript/components/askPanel|src/components/askPanel.tsx]] — import-or-re-export; imports `STYLE_ANSWER_MODE`, `StoredHelpStyle`, `useStoredHelpStyle`
- [[Reference/Desktop/TypeScript/components/goldenpath/shared|src/components/goldenpath/shared.tsx]] — import-or-re-export; imports `SecondaryButton`
- [[Reference/Desktop/TypeScript/components/pdfSelection/highlights|src/components/pdfSelection/highlights.ts]] — import-or-re-export; imports `PdfHighlight`, `highlightFromPlacement`, `kindLabel`
- [[Reference/Desktop/TypeScript/components/pdfSelection/model|src/components/pdfSelection/model.ts]] — import-or-re-export; imports `exactNode`
- [[Reference/Desktop/TypeScript/components/sourceTail|src/components/sourceTail.ts]] — import-or-re-export; imports `youtubeVideoId`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `TermSelect`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `SPAN_MISMATCH_COPY`, `errorMessage`
- [[Reference/Desktop/TypeScript/fixtures/readerRenderView|src/fixtures/readerRenderView.ts]] — import-or-re-export; imports `readerRenderViewFixture`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/render/mathMacros|src/render/mathMacros.tsx]] — import-or-re-export; imports `MathMacrosProvider`
- [[Reference/Desktop/TypeScript/render/readerBlockPolicy|src/render/readerBlockPolicy.ts]] — import-or-re-export; imports `readerDisplaysBlock`
- [[Reference/Desktop/TypeScript/screens/reader/ActiveReadingCard|src/screens/reader/ActiveReadingCard.tsx]] — import-or-re-export; imports `ActiveReadingCard`, `NextStepFoldLine`
- [[Reference/Desktop/TypeScript/screens/reader/AlsoInBooks|src/screens/reader/AlsoInBooks.tsx]] — import-or-re-export; imports `ALSO_COPY`, `AlsoInBooks`, `AlsoPeekCrumb`
- [[Reference/Desktop/TypeScript/screens/reader/AskRail|src/screens/reader/AskRail.tsx]] — import-or-re-export; imports `AskRail`
- [[Reference/Desktop/TypeScript/screens/reader/DeliverableSliceCard|src/screens/reader/DeliverableSliceCard.tsx]] — import-or-re-export; imports `GuidePathSlot`
- [[Reference/Desktop/TypeScript/screens/reader/DetourStrip|src/screens/reader/DetourStrip.tsx]] — import-or-re-export; imports `DetourStrip`
- [[Reference/Desktop/TypeScript/screens/reader/DoseOffer|src/screens/reader/DoseOffer.tsx]] — import-or-re-export; imports `DoseOffer`
- [[Reference/Desktop/TypeScript/screens/reader/FindSection|src/screens/reader/FindSection.tsx]] — import-or-re-export; imports `FindSection`
- [[Reference/Desktop/TypeScript/screens/reader/GuideRail|src/screens/reader/GuideRail.tsx]] — import-or-re-export; imports `GuideRail`, `SectionBoundaryOffer`
- [[Reference/Desktop/TypeScript/screens/reader/InquiryQuickCheck|src/screens/reader/InquiryQuickCheck.tsx]] — import-or-re-export; imports `InquiryQuickCheck`
- [[Reference/Desktop/TypeScript/screens/reader/IntentBox|src/screens/reader/IntentBox.tsx]] — import-or-re-export; imports `IntentBox`
- [[Reference/Desktop/TypeScript/screens/reader/KeptMark|src/screens/reader/KeptMark.tsx]] — import-or-re-export; imports `KeptMark`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]] — import-or-re-export; imports `ExplorableOutcome`, `LibraryAnswer`, `LibraryExercisesProps`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryPane|src/screens/reader/LibraryPane.tsx]] — import-or-re-export; imports `LibraryPane`, `useComparingStacked`
- [[Reference/Desktop/TypeScript/screens/reader/MarginMark|src/screens/reader/MarginMark.tsx]] — import-or-re-export; imports `CueFooter`, `MarginMark`
- [[Reference/Desktop/TypeScript/screens/reader/NotesRail|src/screens/reader/NotesRail.tsx]] — import-or-re-export; imports `ExerciseImportState`, `NotesRail`
- [[Reference/Desktop/TypeScript/screens/reader/PreparingView|src/screens/reader/PreparingView.tsx]] — import-or-re-export; imports `PreparingView`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderAskBranches|src/screens/reader/ReaderAskBranches.tsx]] — import-or-re-export; imports `AskAbout`, `ReaderExchange`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderNotes|src/screens/reader/ReaderNotes.tsx]] — import-or-re-export; imports `NOTES_COPY`, `NoteLinkPicker`, `NoteMarkButton`, `useNoteMarks`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderWorkingPosture|src/screens/reader/ReaderWorkingPosture.tsx]] — import-or-re-export; imports `ReaderWorkingPosture`
- [[Reference/Desktop/TypeScript/screens/reader/ReadingPathCard|src/screens/reader/ReadingPathCard.tsx]] — import-or-re-export; imports `ReadingPathCard`
- [[Reference/Desktop/TypeScript/screens/reader/RecapCard|src/screens/reader/RecapCard.tsx]] — import-or-re-export; imports `RecapCard`
- [[Reference/Desktop/TypeScript/screens/reader/ReconnectLine|src/screens/reader/ReconnectLine.tsx]] — import-or-re-export; imports `ReconnectLine`
- [[Reference/Desktop/TypeScript/screens/reader/ScopeFromPassage|src/screens/reader/ScopeFromPassage.tsx]] — import-or-re-export; imports `ScopeFromPassage`
- [[Reference/Desktop/TypeScript/screens/reader/SideBySidePane|src/screens/reader/SideBySidePane.tsx]] — import-or-re-export; imports `SideBySidePane`
- [[Reference/Desktop/TypeScript/screens/reader/TutorOffers|src/screens/reader/TutorOffers.tsx]] — import-or-re-export; imports `createTutorOfferStore`
- [[Reference/Desktop/TypeScript/screens/reader/WrapUpPanel|src/screens/reader/WrapUpPanel.tsx]] — import-or-re-export; imports `WrapUpPanel`
- [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]] — import-or-re-export; imports `WatchPanelHandle`, `YouTubeWatchPanel`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export; imports `activitySince`, `learnerActivitySnapshot`, `logReaderAction`, `logReaderActivity`, `newActivityId`
- [[Reference/Desktop/TypeScript/screens/reader/authoredQuestion|src/screens/reader/authoredQuestion.ts]] — import-or-re-export; imports `AuthoredQuestionStatus`
- [[Reference/Desktop/TypeScript/screens/reader/bareAlt|src/screens/reader/bareAlt.ts]] — import-or-re-export; imports `useBareAltClear`
- [[Reference/Desktop/TypeScript/screens/reader/compareKeepContext|src/screens/reader/compareKeepContext.ts]] — import-or-re-export; imports `CompareKeepContext`
- [[Reference/Desktop/TypeScript/screens/reader/cues|src/screens/reader/cues.ts]] — import-or-re-export; imports `CUE_COPY`, `PdfPageLayout`
- [[Reference/Desktop/TypeScript/screens/reader/exerciseCandidates (ts)|src/screens/reader/exerciseCandidates.ts]] — import-or-re-export; imports `ExerciseCandidate`, `ReaderWorkbenchExercise`, `exerciseOpenRequest`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export; imports `FiguresUnder`
- [[Reference/Desktop/TypeScript/screens/reader/figures/showMe|src/screens/reader/figures/showMe.ts]] — import-or-re-export; imports `ShowMeLine`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export; imports `FigureRequestOutcome`, `FiguresCtl`, `useFigures`
- [[Reference/Desktop/TypeScript/screens/reader/guidePlan|src/screens/reader/guidePlan.ts]] — import-or-re-export; imports `readGuidePlan`
- [[Reference/Desktop/TypeScript/screens/reader/notesContext|src/screens/reader/notesContext.ts]] — import-or-re-export; imports `NotesContext`
- [[Reference/Desktop/TypeScript/screens/reader/readerCache|src/screens/reader/readerCache.ts]] — import-or-re-export; imports `cachedSourceRead`
- [[Reference/Desktop/TypeScript/screens/reader/readerKeys|src/screens/reader/readerKeys.ts]] — import-or-re-export; imports `readerKeyBarKeys`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `AnnotationSegment`, `MarginAnnotation`, `ReaderSelection`, `askGroundingSpans`, `clip`, `groundingProtected`, `passageKeys`, `placedSpanIds`, `selectionNodes`, `selectionProtected`
- [[Reference/Desktop/TypeScript/screens/reader/readingPath|src/screens/reader/readingPath.ts]] — import-or-re-export; imports `readingPathRefreshKey`
- [[Reference/Desktop/TypeScript/screens/reader/readingPosition|src/screens/reader/readingPosition.ts]] — import-or-re-export; imports `ReadingPosition`
- [[Reference/Desktop/TypeScript/screens/reader/recapCopy|src/screens/reader/recapCopy.ts]] — import-or-re-export; imports `RECAP_COPY`
- [[Reference/Desktop/TypeScript/screens/reader/returnStack|src/screens/reader/returnStack.ts]] — import-or-re-export; imports `ReturnStack`, `besideTrail`, `stackGoTo`
- [[Reference/Desktop/TypeScript/screens/reader/searchBasis|src/screens/reader/searchBasis.ts]] — import-or-re-export; imports `searchBasisLabel`
- [[Reference/Desktop/TypeScript/screens/reader/sideBySide|src/screens/reader/sideBySide.ts]] — import-or-re-export; imports `clampSplit`, `crumbLabel`, `readSplit`, `sideBySideTarget`, `writeSplit`
- [[Reference/Desktop/TypeScript/screens/reader/useActiveReading|src/screens/reader/useActiveReading.ts]] — import-or-re-export; imports `useActiveReading`
- [[Reference/Desktop/TypeScript/screens/reader/useIntentBox|src/screens/reader/useIntentBox.ts]] — import-or-re-export; imports `IntentCancel`, `IntentRunHandle`, `IntentRunHow`, `useIntentBox`
- [[Reference/Desktop/TypeScript/screens/reader/useKeptComparisons|src/screens/reader/useKeptComparisons.ts]] — import-or-re-export; imports `useKeptComparisons`
- [[Reference/Desktop/TypeScript/screens/reader/useLibraryAsk|src/screens/reader/useLibraryAsk.ts]] — import-or-re-export; imports `CompareRequest`, `SCOPE_COPY`, `useLibraryAsk`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] — import-or-re-export; imports `CueCheckMeRequest`, `CueRequestOrigin`, `useReaderCues`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export; imports `AskAnchor`, `useReaderInquiry`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderRecap|src/screens/reader/useReaderRecap.ts]] — import-or-re-export; imports `useReaderRecap`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderRequests|src/screens/reader/useReaderRequests.ts]] — import-or-re-export; imports `useReaderRequests`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderVisit|src/screens/reader/useReaderVisit.ts]] — import-or-re-export; imports `useReaderVisit`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderWorkbench|src/screens/reader/useReaderWorkbench.ts]] — import-or-re-export; imports `ReaderWorkbenchProps`, `useReaderWorkbench`
- [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]] — import-or-re-export; imports `useReadingProgress`
- [[Reference/Desktop/TypeScript/screens/reader/useSideBySide|src/screens/reader/useSideBySide.ts]] — import-or-re-export; imports `SIDE_BY_SIDE_COPY`, `SIDE_BY_SIDE_SCROLL_KEYS`, `useSideBySide`
- [[Reference/Desktop/TypeScript/screens/reader/useSidePane|src/screens/reader/useSidePane.ts]] — import-or-re-export; imports `PaneCaptureTarget`, `SidePane`, `inSidePane`, `useSidePane`
- [[Reference/Desktop/TypeScript/screens/workbench/stepModel|src/screens/workbench/stepModel.ts]] — import-or-re-export; imports `WORKBENCH_COPY`, `problemTitle`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `@tauri-apps/api/core`, `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/workbench/switchOff.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/workbench/switchOff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/tutorSwitchOff.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/tutorSwitchOff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/tutorReader.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/tutorReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/tutorExercises.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/tutorExercises.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/tutorBoundAsk.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/tutorBoundAsk.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/sideBySideReader.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/sideBySideIntent.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideIntent.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/sideBySideCorrespondence.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideCorrespondence.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/ReaderScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/ReaderScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

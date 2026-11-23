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
| Source lines | 4974 |
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

- `export interface ReaderOpenSource` — interface, line 251
- `export interface ReaderWindowing` — interface, line 274
- `export interface ReaderLens` — interface, line 299
- `export interface PenSurface` — interface, line 312
- `export interface ReaderCheckMeRequest extends CueCheckMeRequest` — interface, line 322
- `export type ReaderExerciseRequest = ReaderWorkbenchExercise &` — type, line 335
- `export const SIDE_PATH_COPY =` — const, line 339
- `export function ReaderScreen(` — function, line 361

## Internal implementation anchors

- `type AnnotationSegment, type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 148
- `type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 149
- `type ReaderSelection, } from "./reader/readerShared"` — type, line 150
- `const NO_SECTIONS: never[] = []` — const, line 154
- `const READER_MODE_OPTIONS = [` — const, line 155
- `const TAG_ACTIONS: Array<` — const, line 165
- `const WHOLE_BLOCK_QUOTE = "(whole block)"` — const, line 173
- `type ReaderRailTab = "guide" | "ask" | "notes"` — type, line 175
- `const HEALTH_COLOR: Record<string, "green" | "amber" | "pink" | "slate"> =` — const, line 177
- `const FIGURE_PAGE_NOT_OPENED = "That page couldn't be opened."` — const, line 185
- `type OpenOutcome = "opened" | "preparing" | "not_opened"` — type, line 188
- `interface OfferedPress` — interface, line 192
- `const OFFER_OUTCOME: Record<FigureRequestOutcome, ExplorableOutcome> =` — const, line 203
- `const BADGED_HEALTH = new Set(["suspect", "failed"])` — const, line 209
- `interface RemovedAnnotation` — interface, line 213
- `const UNDO_REMOVE_MS = 10_000` — const, line 223
- `interface SelectionHighlight` — interface, line 226
- `function newKey(): string` — function, line 233
- `function identityOf(view: Pick<ReaderRenderViewDto, "sourceId" | "revisionId" | "extractionId">): SourceIdentity` — function, line 242
- `function sectionIdentity(section:` — function, line 247
- `function RailScope(` — function, line 266
- `const lifecycle = useWindowLifecycle()` — const, line 267
- `const mainPaneOwnsCueKey = (event: KeyboardEvent): boolean` — const, line 346
- `interface IntentPane` — interface, line 351
- `const hub = useListenerHub()` — const, line 419
- `const windowPaused = useWindowPaused()` — const, line 421
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 425
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 429
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 438
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 439
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 440
- `const openingRef = useRef<string | null>(null)` — const, line 446
- `const savingHighlightNote = useRef(false)` — const, line 458
- `const askPanelOn = algoConfig().ask !== null` — const, line 472
- `const storedStyle = useStoredHelpStyle()` — const, line 473
- `const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen` — const, line 474
- `const pdfViewRequestRef = useRef(0)` — const, line 496
- `const sourceEpochRef = useRef(0)` — const, line 527
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 538
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 539
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 540
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 541
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 542
- `const modeSaveVersionRef = useRef(0)` — const, line 543
- `const answerModeSaveVersionRef = useRef(0)` — const, line 544
- `const enabled = contract?.readerEnabled ?? true` — const, line 560
- `const inquiry = contract?.inquiryEnabled === true` — const, line 563
- `const muted = inquiry && mode === "skim"` — const, line 566
- `const intentContract = inquiry && !offline ? contract?.intent ?? null : null` — const, line 569
- `const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading)` — const, line 570
- `const openFigureSource = useRef<((extractionId: string, spanId: string)` — const, line 574
- `const figureOpenSource = useCallback((extractionId: string, spanId: string)` — const, line 575
- `const figuresCtl = useFigures(` — const, line 576
- `const figureOffersOn = Boolean(contract?.figures?.offers) && !offline` — const, line 582
- `const showMeOn = Boolean(contract?.figures?.showMe) && !offline` — const, line 586
- `const waitingOfferRef = useRef<OfferedPress | null>(null)` — const, line 592
- `const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome)` — const, line 597
- `const press = offeredFigure` — const, line 604
- `const open = render?.extractionId ?? null` — const, line 606
- `const readerTutor = contract?.readerTutor ?? null` — const, line 629
- `const askWorkbenchSessionRef = useRef<string | null>(null)` — const, line 631
- `const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true` — const, line 636
- `const askPersonalizedRef = useRef<boolean | null>(null)` — const, line 637
- `const askComposerAnchorRef = useRef<AskAnchor | null>(null)` — const, line 642
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 648
- `const renderBlocksBySpan = useMemo( ()` — const, line 652
- `const visit = useReaderVisit(` — const, line 658
- `const showGuideRail = useCallback(()` — const, line 664
- `const progress = useReadingProgress(` — const, line 668
- `const doseVisitId = useCallback(()` — const, line 685
- `const refreshAnnotations = useCallback(async ()` — const, line 687
- `const epoch = sourceEpochRef.current` — const, line 689
- `const result = await cachedSourceRead( render.sourceId, ["reader_source_annotations", render.sourceId, render.extractionId], ()` — const, line 693
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 700
- `const version = (r.version as Record<string, unknown>) ??` — const, line 703
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 704
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 705
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 706
- `const placement = r.placement as ReaderAnnotationPlacementDto | undefined` — const, line 707
- `let page: number | null = null` — let, line 717
- `let bbox: number[] | null = null` — let, line 718
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 720
- `const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?:` — const, line 738
- `const openCardRef = useRef<SourceLibraryCard | null>(null)` — const, line 763
- `const openExtractionRef = useRef<string | null>(null)` — const, line 765
- `const reloadGuidePlan = useCallback(async ()` — const, line 767
- `const extractionId = render.extractionId` — const, line 769
- `const plan = await readGuidePlan(render.sourceId, extractionId,` — const, line 771
- `const spanOrder = useMemo( ()` — const, line 784
- `const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none"` — const, line 788
- `const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 791
- `const card = openCardRef.current` — const, line 792
- `const wbProps = useMemo<ReaderWorkbenchProps | undefined>(()` — const, line 802
- `const submitted = workbench?.onSubmitted` — const, line 803
- `const trail = besideTrail(returnStackRef.current)` — const, line 808
- `const wbCtl = useReaderWorkbench(` — const, line 813
- `const working = wbCtl.active !== null` — const, line 820
- `const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline` — const, line 824
- `const alsoHidden = alsoPrefs ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId)) : Boolean(contract?.correspondence?.hiddenEverywhere) || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.so…` — const, line 829
- `const peekCrumbShown = alsoPeek ?? findPeek` — const, line 839
- `const pathRefreshKey = readingPathRefreshKey(` — const, line 854
- `const tryFirstRef = useRef<((spanId: string)` — const, line 868
- `const cueCtl = useReaderCues(` — const, line 869
- `const recapCtl = useReaderRecap(` — const, line 884
- `const sourceLifecycleState = useWindowLifecycle().state` — const, line 900
- `const railOnScreen = windowed ? Boolean(windowed.railHost) && !isPaused(windowed.railHost?.lifecycle.state ?? "hidden") : !isPaused(sourceLifecycleState)` — const, line 901
- `const recapShown = Boolean(railOnScreen && recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working)` — const, line 904
- `const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip")` — const, line 915
- `const root = history.find((entry)` — const, line 916
- `const recapRevisited = useCallback((rootId: string)` — const, line 929
- `const root = history.find((entry)` — const, line 930
- `const recapRevisit = useCallback(async (rootId: string)` — const, line 933
- `const root = history.find((entry)` — const, line 934
- `const recapOpenInquiry = useCallback((rootId: string, spanId: string)` — const, line 940
- `const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch")` — const, line 943
- `const cueMarksFor = (markSurface: "pdf" | "watch")` — const, line 963
- `let cancelled = false` — let, line 972
- `const scroller = railRef.current` — const, line 1005
- `const clamp = ()` — const, line 1007
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 1008
- `const observer = new ResizeObserver(clamp)` — const, line 1011
- `const query = librarySearch.trim()` — const, line 1022
- `let cancelled = false` — let, line 1029
- `const timer = window.setTimeout(()` — const, line 1032
- `const resetSourceState = useCallback(()` — const, line 1055
- `const openSource = useCallback( async ( card: SourceLibraryCard, jumpSpan?: string, // jumpReading: the reading jumpSpan was found on (a search hit, a // return)` — const, line 1104
- `const handoff = options.handoff ?? null` — const, line 1114
- `const view = options.view ?? await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 1132
- `const pdfRequest = ++pdfViewRequestRef.current` — const, line 1179
- `const current = ()` — const, line 1180
- `const openFixture = useCallback(()` — const, line 1215
- `const backToLibrary = useCallback(()` — const, line 1223
- `const spanId = readingSpan ?? activeSpan` — const, line 1227
- `const section = guidePlan?.sections.find((candidate)` — const, line 1228
- `const resumedRef = useRef(false)` — const, line 1246
- `const trail = initialSource.besideTrail ?? null` — const, line 1250
- `const activeBlock = useMemo(()` — const, line 1264
- `const pdfHighlights: PdfHighlight[] = useMemo(()` — const, line 1273
- `const list: PdfHighlight[] = []` — const, line 1274
- `const base =` — const, line 1277
- `const placed = highlightFromPlacement(base, a.placement)` — const, line 1279
- `const segments = a.segments.flatMap((s)` — const, line 1284
- `const annotatedSpans = useMemo( ()` — const, line 1291
- `const annotationBySpan = useMemo(()` — const, line 1296
- `const map = new Map<string, MarginAnnotation>()` — const, line 1297
- `const before = map.get(spanId)` — const, line 1301
- `const boundaryBlock = useMemo(()` — const, line 1307
- `const revealedPassages = useMemo(()` — const, line 1309
- `const revealed = new Set(revealedSections)` — const, line 1310
- `const map = new Map<string,` — const, line 1311
- `const revealedGuidanceSpans = useMemo(()` — const, line 1320
- `const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null` — const, line 1325
- `const protectedSelection = selectionProtected(protection, selection)` — const, line 1326
- `const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1327
- `const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan))` — const, line 1331
- `const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1332
- `const editCaptureText = useCallback((text: string)` — const, line 1337
- `const resetCaptureText = useCallback(()` — const, line 1340
- `const saveAnnotationEdit = useCallback(async ()` — const, line 1352
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 1374
- `const result = await api.readerReanchor(` — const, line 1378
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1395
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1418
- `const target = annotations.find((a)` — const, line 1419
- `const reading = render ?` — const, line 1420
- `const epoch = sourceEpochRef.current` — const, line 1421
- `const undoRemove = useCallback(async ()` — const, line 1436
- `const last = removed` — const, line 1437
- `const epoch = sourceEpochRef.current` — const, line 1443
- `const result = await api.readerRestoreAnnotation(` — const, line 1445
- `const timer = window.setTimeout(()` — const, line 1458
- `const onKey = (event: KeyboardEvent)` — const, line 1464
- `const target = event.target` — const, line 1467
- `const openAnnotationNote = useCallback((annotationId: string)` — const, line 1475
- `const target = annotations.find((a)` — const, line 1476
- `const nodesForRange = useCallback((range: Range): Array<` — const, line 1489
- `const container = bodyRef.current` — const, line 1490
- `const nodes: Array<` — const, line 1492
- `const seen = new Set<string>()` — const, line 1493
- `const spanId = el.dataset.spanId` — const, line 1495
- `let intersects = false` — let, line 1497
- `const sub = document.createRange()` — const, line 1504
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1512
- `const block = renderBlocksBySpan.get(spanId)` — const, line 1517
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1523
- `const sel = window.getSelection()` — const, line 1524
- `const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1532
- `const cancelIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1533
- `const selectionSpanIds = useMemo( ()` — const, line 1534
- `const intentBox = useIntentBox(` — const, line 1538
- `const openActiveRail = useCallback(()` — const, line 1552
- `const activeCtl = useActiveReading(` — const, line 1556
- `const libraryCtl = useLibraryAsk(` — const, line 1565
- `const keptCtl = useKeptComparisons(` — const, line 1567
- `const notesCtl = useNoteMarks(` — const, line 1569
- `const windowActive = useWindowLifecycle().state === "active"` — const, line 1575
- `const pdfMarks = (): ReadonlyMap<string, ReactNode> | null` — const, line 1584
- `const cues = cueMarksFor("pdf")` — const, line 1585
- `const merged = new Map<string, ReactNode>(cues ?? [])` — const, line 1587
- `const cue = merged.get(spanId)` — const, line 1589
- `const before = merged.get(spanId)` — const, line 1594
- `const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null)` — const, line 1600
- `const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint)` — const, line 1602
- `const sbs = useSideBySide(` — const, line 1604
- `const node = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1612
- `const sbsPanes = sbs.panes && !comparing` — const, line 1625
- `const sbsPanesRef = useRef(false)` — const, line 1626
- `const sbsShownRef = useRef(false)` — const, line 1631
- `const sbsRef = useRef(sbs)` — const, line 1633
- `const sbsEscBusyRef = useRef(false)` — const, line 1636
- `const sbsPaneRef = useRef<HTMLDivElement | null>(null)` — const, line 1638
- `const runSideIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1643
- `const cancelSideIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1644
- `const sbsSection = sbs.section && sbs.target && sbs.section.sectionId === sbs.target.sectionId ? sbs.section : null` — const, line 1645
- `type BesideRun = |` — type, line 1660
- `const besideSeq = useRef(0)` — const, line 1669
- `const besideRunRef = useRef<(run: BesideRun)` — const, line 1672
- `const besideDroppedRef = useRef<(run: BesideRun)` — const, line 1673
- `const openBesideRef = useRef<(hit:` — const, line 1674
- `const snapshotBesideRef = useRef<(spanId: string)` — const, line 1681
- `const shown = sbsRef.current.target` — const, line 1683
- `const takeBesideBook = useCallback((book: SourceIdentity, spanId: string, run: BesideRun)` — const, line 1687
- `const id = ++besideSeq.current` — const, line 1689
- `const sideExtractionRef = useRef<string | null>(null)` — const, line 1701
- `const checkMeFromSideCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 1702
- `const side = useSidePane(` — const, line 1707
- `const besideRanRef = useRef(0)` — const, line 1736
- `const handoff = besideHandoff` — const, line 1738
- `const card = openCardRef.current` — const, line 1753
- `const trail = besideTrail(returnStackRef.current)` — const, line 1755
- `const work = handoff.run` — const, line 1764
- `const openComposer = useCallback((anchor: AskAnchor | null)` — const, line 1778
- `const sbsRowRef = useRef<HTMLDivElement | null>(null)` — const, line 1796
- `const startSbsResize = (event: ReactPointerEvent<HTMLDivElement>)` — const, line 1797
- `const row = sbsRowRef.current` — const, line 1798
- `const rect = row.getBoundingClientRect()` — const, line 1801
- `const move = (moved: PointerEvent)` — const, line 1802
- `const offs: Array<()` — const, line 1805
- `const up = ()` — const, line 1806
- `const touchMain = ()` — const, line 1816
- `const onKey = (event: KeyboardEvent)` — const, line 1825
- `const target = event.target` — const, line 1827
- `const ctl = sbsRef.current` — const, line 1829
- `const open = ctl.panes || ctl.sheet` — const, line 1830
- `const shown = sbsShownRef.current` — const, line 1831
- `const mod = event.ctrlKey || event.metaKey` — const, line 1832
- `const side = sbsPaneRef.current` — const, line 1842
- `const inSide = target instanceof Element && Boolean(target.closest("[data-side-by-side-pane]"))` — const, line 1843
- `const inMain = target instanceof Node && Boolean(bodyRef.current?.contains(target))` — const, line 1849
- `const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false, anchor?: SourceIdentity)` — const, line 1858
- `const identity = anchor ?? identityOf(render)` — const, line 1865
- `const request =` — const, line 1866
- `const closeLibrary = useCallback(()` — const, line 1871
- `const onKey = (event: KeyboardEvent)` — const, line 1878
- `const onMouseUp = useCallback(()` — const, line 1888
- `const sel = window.getSelection()` — const, line 1889
- `const quote = selectionQuote(sel.getRangeAt(0), sel.toString()).replace(/\s+/g, " ").trim()` — const, line 1893
- `const nodes = collectSelectionNodes()` — const, line 1895
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1924
- `const domDragRef = useRef<` — const, line 1925
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1927
- `const host = bodyRef.current` — const, line 1928
- `const rect = host.getBoundingClientRect()` — const, line 1930
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1934
- `const target = event.target as Node` — const, line 1938
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1940
- `const domDrafting = domDraft !== null` — const, line 1952
- `const rectFrom = (drag:` — const, line 1955
- `const onMove = (event: MouseEvent)` — const, line 1961
- `const drag = domDragRef.current` — const, line 1962
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1964
- `const onUp = (event: MouseEvent)` — const, line 1967
- `const drag = domDragRef.current` — const, line 1968
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1972
- `const rect = rectFrom(drag, point)` — const, line 1974
- `const next = [...domBoxesRef.current, rect]` — const, line 1977
- `const offs = [hub.listen("window", "mousemove", onMove), hub.listen("window", "mouseup", onUp)]` — const, line 1983
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1990
- `const host = bodyRef.current` — const, line 1991
- `const hostRect = host.getBoundingClientRect()` — const, line 1993
- `const clientBoxes = boxes.map((b)` — const, line 1994
- `const nodes: Array<` — const, line 2000
- `const seen = new Set<string>()` — const, line 2001
- `const spanId = el.dataset.spanId` — const, line 2003
- `const elRect = el.getBoundingClientRect()` — const, line 2005
- `const touches = clientBoxes.some( (b)` — const, line 2006
- `const words: string[] = []` — const, line 2010
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 2011
- `const text = node as Text` — const, line 2013
- `const wordPattern = /\S+/g` — const, line 2014
- `let match: RegExpExecArray | null` — let, line 2015
- `const range = document.createRange()` — const, line 2017
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 2020
- `const cx = (Math.min(...rects.map((r)` — const, line 2022
- `const cy = (Math.min(...rects.map((r)` — const, line 2023
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 2027
- `const commitDomBoxes = useCallback(()` — const, line 2036
- `const boxes = domBoxesRef.current` — const, line 2037
- `const nodes = resolveDomBoxes(boxes)` — const, line 2039
- `const quote = nodes.map((n)` — const, line 2045
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 2054
- `const clearDomBoxes = ()` — const, line 2062
- `const onKeyDown = (event: KeyboardEvent)` — const, line 2068
- `const onKeyUp = (event: KeyboardEvent)` — const, line 2073
- `const onBlur = ()` — const, line 2079
- `const offs = [ hub.listen("window", "keydown", onKeyDown), hub.listen("window", "keyup", onKeyUp), hub.listen("window", "blur", onBlur), ]` — const, line 2080
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 2099
- `const point = domPointFromClient(request.x, request.y)` — const, line 2101
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 2102
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 2123
- `const retryRequest = useCallback(async (requestId: string)` — const, line 2136
- `const optimisticSegments = useCallback( (nodes: string | Array<string |` — const, line 2150
- `const list = Array.isArray(nodes) ? nodes : [nodes]` — const, line 2152
- `const spanId = typeof node === "string" ? node : node.spanId` — const, line 2154
- `const geometry = pdfView?.blocks.find((b)` — const, line 2155
- `const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number" ?` — const, line 2156
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 2168
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 2172
- `const quotedNodes = (()` — const, line 2177
- `const multi = collectSelectionNodes()` — const, line 2180
- `const optimisticIds = quotedNodes ?? [target.spanId]` — const, line 2183
- `const nodes = quotedNodes ?? [` — const, line 2193
- `const receipt = await api.readerCapture(` — const, line 2194
- `const handler = (event: KeyboardEvent)` — const, line 2221
- `const clearSelection = useCallback(()` — const, line 2232
- `const railHostTab = windowed?.railHost?.tab ?? null` — const, line 2244
- `const windowExtraction = render?.extractionId ?? null` — const, line 2245
- `const onWindowTitle = windowed?.onTitle` — const, line 2250
- `const onWindowStatus = windowed?.onStatus` — const, line 2254
- `const windowWhere = currentGuideSection ? sectionWords(currentGuideSection.label) : null` — const, line 2255
- `const onWindowMediaReady = windowed?.onMediaReady` — const, line 2259
- `const onWindowJumpReady = windowed?.onJumpReady` — const, line 2265
- `const onWindowPenSurface = windowed?.onPenSurface` — const, line 2271
- `const penTextShown = Boolean(render) && !(pdfView && surface === "pdf")` — const, line 2272
- `const body = bodyRef.current` — const, line 2274
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 2290
- `const segment = a.segments.find((s)` — const, line 2292
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 2299
- `const alsoKeyRef = useRef<()` — const, line 2309
- `const onKey = (event: KeyboardEvent)` — const, line 2317
- `const target = event.target` — const, line 2320
- `const tabs: ReaderRailTab[] = ["guide", "ask", "notes"]` — const, line 2322
- `const askRequestSeen = useRef(askRequest)` — const, line 2359
- `const revealAskRef = useRef<()` — const, line 2361
- `const startCompareRef = useRef<(request: CompareRequest)` — const, line 2386
- `const sideAnchor = Boolean(side.extractionId) && side.extractionId === request.extractionId` — const, line 2389
- `const request = compareWaitsForWork` — const, line 2396
- `const sideMarksChanged = side.marksChanged` — const, line 2406
- `const captureIn = useCallback(async (target: PaneCaptureTarget, what:` — const, line 2407
- `const common =` — const, line 2412
- `const receipt: ReaderPresetReceiptDto = "preset" in what ? await api.readerInvokePreset(` — const, line 2417
- `const drained = await api.readerDrainOutbox()` — const, line 2428
- `const invokePreset = useCallback( // RW1b: the intent box passes its own words as the annotation's learner // text, and names the intention and entry in the funnel event. // Reader CA6b: `target` is side by side's second pane (its book, revision, // reading a…` — const, line 2449
- `const note_ = learnerTextOverride ?? note` — const, line 2457
- `const nodes = selectionNodes(selection)` — const, line 2458
- `const editedText = selection.editedText?.trim()` — const, line 2459
- `const receipt = await api.readerInvokePreset(` — const, line 2471
- `const drained = await api.readerDrainOutbox()` — const, line 2495
- `const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>, target?: PaneCaptureTarget): Promise<string | null>` — const, line 2518
- `const note_ = learnerTextOverride ?? note` — const, line 2522
- `const nodes = selectionNodes(selection)` — const, line 2523
- `const receipt = await api.readerCapture(` — const, line 2536
- `const currentHighlight = selection && selectionHighlight && selectionActions.includes("highlight") && selectionHighlight.spanId === selection.spanId && selectionHighlight.quote === selection.quote ? selectionHighlight : null` — const, line 2566
- `const saveHighlightNote = useCallback(async ()` — const, line 2571
- `const target = currentHighlight` — const, line 2572
- `const words = note.trim()` — const, line 2573
- `const learnerText = target.saved.trim() ? `$` — const, line 2575
- `const typed = note` — const, line 2576
- `const kept = ()` — const, line 2577
- `const annotationId = target.annotationId` — const, line 2588
- `const pauseArc = useCallback(async ()` — const, line 2605
- `const next = await api.readerArc(` — const, line 2609
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 2616
- `const next = await api.readerArc(` — const, line 2621
- `const importJobRef = useRef<` — const, line 2633
- `const importExercise = useCallback(async (target?: PaneCaptureTarget): Promise<string | null>` — const, line 2636
- `const nodes = target ? target.nodes : selectionNodes(selection!)` — const, line 2638
- `const editedText = target ? undefined : selection!.editedText?.trim()` — const, line 2639
- `const receipt = await api.readerImportExercise(target ?` — const, line 2642
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 2690
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 2691
- `const timer = setInterval(async ()` — const, line 2695
- `const status = await api.readerExerciseImportStatus(` — const, line 2697
- `const job = importJobRef.current` — const, line 2698
- `const waited = Date.now() - job.startedAt` — const, line 2701
- `const saveOwnQuestion = useCallback(async ()` — const, line 2728
- `const saved = await api.readerAuthorQA(` — const, line 2736
- `const runCoach = useCallback(async ()` — const, line 2757
- `const lint = await api.readerCoachLint(` — const, line 2760
- `const changeMode = useCallback( async (next: string)` — const, line 2771
- `const previous = mode` — const, line 2773
- `const version = ++modeSaveVersionRef.current` — const, line 2776
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 2787
- `const answerModeNext = next as ReaderAnswerMode` — const, line 2789
- `const previous = answerMode` — const, line 2790
- `const version = ++answerModeSaveVersionRef.current` — const, line 2793
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 2809
- `const renderInquiryTop = useCallback((root: ReaderExchange)` — const, line 2824
- `const line = reconnect && reconnect.rootId === root.id && !muted ? ( <ReconnectLine placement="rail" question=` — const, line 2827
- `const check = inquiryChecks[root.id]` — const, line 2837
- `const inlineReconnect = reconnect && reconnect.inline && !muted ? ( <ReconnectLine placement="inline" question=` — const, line 2865
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 2876
- `const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, pinned?: ReaderRenderViewDto): Promise<OpenOutcome>` — const, line 2895
- `const card = (library ?? []).find((candidate)` — const, line 2900
- `const spanId = readingSpan ?? activeSpan` — const, line 2903
- `const onOriginal = pdfView && surface === "pdf" && !offline` — const, line 2929
- `const epoch = sourceEpochRef.current` — const, line 2942
- `const sameBook = Boolean(render && sourceId === render.sourceId)` — const, line 2945
- `const card = (library ?? []).find((candidate)` — const, line 2946
- `const landed = await api.readerSavedPlace(` — const, line 2951
- `const landing = await api.readerRenderView(` — const, line 2965
- `const openFollowedFigure = (figure: CorrespondentFigureDto, hit: CorrespondentSectionDto)` — const, line 2975
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2977
- `const compareFoundSection = (hit: CorrespondentSectionDto)` — const, line 2992
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2994
- `const hideAlsoInBooks = (scope: "book" | "everywhere")` — const, line 3017
- `const before = alsoPrefs ??` — const, line 3019
- `const base = contract` — const, line 3026
- `const makeExplorable = (target: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, origin: "library" | "tutor", offerRef: string): Promise<ExplorableOutcome>` — const, line 3043
- `let settle: (outcome: ExplorableOutcome)` — let, line 3050
- `const settled = new Promise<ExplorableOutcome>((resolve)` — const, line 3051
- `const press: OfferedPress =` — const, line 3052
- `const peekWorkbenchPassage = (spanId: string, target?: PassageTarget)` — const, line 3071
- `const exerciseSettings = libraryCtl.enabled ? contract?.libraryExercises ?? null : null` — const, line 3082
- `const exerciseCard = (sourceId: string | null)` — const, line 3083
- `const useExercise = (candidate: ExerciseCandidate)` — const, line 3087
- `const card = exerciseCard(candidate.sourceId ?? render?.sourceId ?? null)` — const, line 3088
- `const openExerciseInBook = (candidate: ExerciseCandidate)` — const, line 3097
- `const sourceId = candidate.sourceId ?? render?.sourceId ?? null` — const, line 3098
- `const exerciseProps: LibraryExercisesProps | null = exerciseSettings ?` — const, line 3101
- `const pickLibraryPagePractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3115
- `const hit = libraryCtl.state?.ask.value?.hits[0]` — const, line 3116
- `const card = hit ? (library ?? []).find((candidate)` — const, line 3117
- `const readySources = library ?? []` — const, line 3169
- `const useShelf = Boolean(shelf) && !sidecarDown` — const, line 3171
- `const card = (library ?? []).find((candidate)` — const, line 3229
- `const card = (library ?? []).find((c)` — const, line 3250
- `const receiptId = searchResults.retrievalReceiptId` — const, line 3256
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 3301
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 3302
- `const wbActive = wbCtl.active` — const, line 3345
- `const wbStacked = working && wbCtl.narrow` — const, line 3346
- `const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible)` — const, line 3349
- `const wbSourceShown = !wbStacked || wbCtl.sheetOpen` — const, line 3350
- `const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry)` — const, line 3351
- `const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>()` — const, line 3352
- `const first = entry.spanIds[0]` — const, line 3354
- `const wbLabel = (stem: string)` — const, line 3357
- `const title = problemTitle(stem)` — const, line 3358
- `const tryPathExercise = (exercise: ReadingPathExerciseDto)` — const, line 3363
- `const workThroughSelection = ()` — const, line 3371
- `const nodes = selectionNodes(selection)` — const, line 3373
- `const editedText = selection.editedText?.trim()` — const, line 3374
- `const foldBlocks = contract?.activeReading?.foldBlocks ?? 3` — const, line 3391
- `const localFold = (spanIds: string[]): string[]` — const, line 3392
- `const positions = spanIds.map((spanId)` — const, line 3393
- `const last = Math.max(...positions)` — const, line 3395
- `const mainPane: IntentPane =` — const, line 3404
- `const sidePane: IntentPane | null = side.extractionId ?` — const, line 3413
- `const sideMeta = (pane: IntentPane): Record<string, string>` — const, line 3423
- `const runIntentIn = (pane: IntentPane, action: ReaderIntentActionDto, text: string, how: IntentRunHow): Promise<IntentRunHandle | null> | void` — const, line 3425
- `const meta =` — const, line 3426
- `const effect = action.effect` — const, line 3427
- `const noteText = !action.model && intentContract && onlyNamesAnAction(text, [...intentContract.palette, ...intentContract.notesPalette]) ? "" : text` — const, line 3431
- `const sideSection = pane.side?.section ?? null` — const, line 3433
- `const anchor: AskAnchor =` — const, line 3439
- `const target = pane.side.target` — const, line 3480
- `const target = pane.side.target` — const, line 3486
- `const target = pane.side.target` — const, line 3492
- `const target = pane.side.target` — const, line 3502
- `const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null` — const, line 3547
- `const request: CompareRequest =` — const, line 3548
- `const region = pane.region` — const, line 3580
- `const words = text?.trim()` — const, line 3581
- `const sideShows = (extractionId: string, spanId: string): boolean` — const, line 3602
- `const checkBeside = (book: SourceIdentity, spanId: string, practiceItemId: string, proposalId: string | null)` — const, line 3605
- `const workThroughImported = (item:` — const, line 3610
- `const imported = exerciseImport` — const, line 3611
- `const spanIds = imported?.spanIds ?? (activeSpan ? [activeSpan] : [])` — const, line 3612
- `const settleShowMeLine = (key: string, patch: Partial<ShowMeLine>)` — const, line 3620
- `const requestShowMe = (ctl: FiguresCtl, run: Extract<BesideRun,` — const, line 3623
- `const key = run.lineKey` — const, line 3624
- `const runOnBook = (about: AskAbout, run: Extract<BesideRun,` — const, line 3636
- `const showMeFromAsk = ()` — const, line 3661
- `const goal = question.trim()` — const, line 3662
- `const about = parentExchange ? parentExchange.about ?? null : askComposerAnchor?.about ?? null` — const, line 3663
- `const home = parentExchange?.spanId ?? (about ? askComposerAnchor?.spanId : undefined) ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan` — const, line 3664
- `const key = `show_me:$` — const, line 3667
- `const run =` — const, line 3670
- `const cancelIntentIn = (pane: IntentPane, cancel: IntentCancel)` — const, line 3679
- `const kind = cancel.action.effect.kind` — const, line 3680
- `const annotationId = handle.annotationId` — const, line 3687
- `const batchId = handle.importBatchId` — const, line 3704
- `const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number)` — const, line 3718
- `const spanId = wbCtl.close(session,` — const, line 3720
- `const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3726
- `const card = openCardRef.current` — const, line 3727
- `const asked = libraryCtl.state?.request` — const, line 3731
- `const resumeMark = (spanId: string | null | undefined)` — const, line 3739
- `const entry = spanId ? wbResumeBySpan.get(spanId) : undefined` — const, line 3740
- `const verb = entry.status === "abandoned" ? "Reopen" : "Resume"` — const, line 3742
- `const placeRail = (rail: ReactNode): ReactNode` — const, line 3761
- `const host = windowed.railHost` — const, line 3763
- `const overDesk = (menu: ReactNode): ReactNode` — const, line 3772
- `const target = event.target` — const, line 3908
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 4085
- `const active = activeSpan === block.spanId` — const, line 4086
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 4087
- `const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null` — const, line 4088
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 4089
- `const endQuestionAvailable = Boolean(endSection && endSection.question?.readingPhase === "after_section" && offeredCheckSections.has(endSection.id))` — const, line 4091
- `const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId))` — const, line 4095
- `const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""))` — const, line 4096
- `const offerSection = endSection && !muted && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 4097
- `const sel = window.getSelection()` — const, line 4122
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 4123
- `const cue = side.cues.markOn(spanId)` — const, line 4214
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 4242
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 4265
- `const active = railTab === tab` — const, line 4380
- `const waiting = tab === "guide" && pendingQuickCheckCount > 0` — const, line 4384
- `const marked = tab === "ask" && askTabMarked && !active` — const, line 4385
- `const params = (action.params ??` — const, line 4536
- `const run =` — const, line 4810
- `const book = exchange?.about ?? render` — const, line 4819

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`; references `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`
- [[Reference/Desktop/TypeScript/screens/desks/goal/GoalLayer|src/screens/desks/goal/GoalLayer.tsx]] — import-or-re-export: `ReaderLens`; references `ReaderLens`
- [[Reference/Desktop/TypeScript/screens/desks/goal/marks|src/screens/desks/goal/marks.tsx]] — import-or-re-export: `ReaderLens`; references `ReaderLens`
- [[Reference/Desktop/TypeScript/screens/desks/pen/PenLayer|src/screens/desks/pen/PenLayer.tsx]] — import-or-re-export: `PenSurface`; references `PenSurface`
- [[Reference/Desktop/TypeScript/screens/desks/video/followLens|src/screens/desks/video/followLens.ts]] — import-or-re-export: `ReaderLens`; references `ReaderLens`
- [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] — import-or-re-export: `PenSurface`, `ReaderLens`, `ReaderScreen`, `ReaderWindowing`; references `PenSurface`, `ReaderLens`, `ReaderScreen`, `ReaderWindowing`

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
- [[Reference/Desktop/TypeScript/components/scrollWithin|src/components/scrollWithin.ts]] — import-or-re-export; imports `scrollIntoViewWithin`
- [[Reference/Desktop/TypeScript/components/sourceTail|src/components/sourceTail.ts]] — import-or-re-export; imports `youtubeVideoId`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `TermSelect`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `SPAN_MISMATCH_COPY`, `errorMessage`
- [[Reference/Desktop/TypeScript/fixtures/readerRenderView|src/fixtures/readerRenderView.ts]] — import-or-re-export; imports `readerRenderViewFixture`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/render/mathMacros|src/render/mathMacros.tsx]] — import-or-re-export; imports `MathMacrosProvider`
- [[Reference/Desktop/TypeScript/render/mathSnippet|src/render/mathSnippet.ts]] — import-or-re-export; imports `selectionQuote`
- [[Reference/Desktop/TypeScript/render/readerBlockPolicy|src/render/readerBlockPolicy.ts]] — import-or-re-export; imports `readerDisplaysBlock`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `ListenerHub`, `ScopeClaims`, `WindowLifecycle`, `WindowScope`, `isPaused`, `useListenerHub`, `useScopeClaim`, `useWindowLifecycle`, `useWindowPaused`
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
- [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]] — import-or-re-export; imports `VideoExtras`, `WatchLens`, `WatchPanelHandle`, `YouTubeWatchPanel`
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
- [[Reference/Desktop/TypeScript/screens/reader/intentPalette|src/screens/reader/intentPalette.ts]] — import-or-re-export; imports `onlyNamesAnAction`
- [[Reference/Desktop/TypeScript/screens/reader/notesContext|src/screens/reader/notesContext.ts]] — import-or-re-export; imports `NotesContext`
- [[Reference/Desktop/TypeScript/screens/reader/readerCache|src/screens/reader/readerCache.ts]] — import-or-re-export; imports `cachedSourceRead`
- [[Reference/Desktop/TypeScript/screens/reader/readerKeys|src/screens/reader/readerKeys.ts]] — import-or-re-export; imports `readerKeyBarKeys`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `AnnotationSegment`, `MarginAnnotation`, `ReaderSelection`, `askGroundingSpans`, `clip`, `groundingProtected`, `passageKeys`, `placedSpanIds`, `sectionWords`, `selectionNodes`, `selectionProtected`
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

- Imported packages/crates: `@tauri-apps/api/core`, `react`, `react-dom`

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

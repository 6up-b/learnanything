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
| Source lines | 4971 |
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
- `export interface ReaderLens` — interface, line 297
- `export interface PenSurface` — interface, line 310
- `export interface ReaderCheckMeRequest extends CueCheckMeRequest` — interface, line 320
- `export type ReaderExerciseRequest = ReaderWorkbenchExercise &` — type, line 333
- `export const SIDE_PATH_COPY =` — const, line 337
- `export function ReaderScreen(` — function, line 359

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
- `const mainPaneOwnsCueKey = (event: KeyboardEvent): boolean` — const, line 344
- `interface IntentPane` — interface, line 349
- `const hub = useListenerHub()` — const, line 417
- `const windowPaused = useWindowPaused()` — const, line 419
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 423
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 427
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 436
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 437
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 438
- `const openingRef = useRef<string | null>(null)` — const, line 444
- `const savingHighlightNote = useRef(false)` — const, line 456
- `const askPanelOn = algoConfig().ask !== null` — const, line 470
- `const storedStyle = useStoredHelpStyle()` — const, line 471
- `const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen` — const, line 472
- `const pdfViewRequestRef = useRef(0)` — const, line 494
- `const sourceEpochRef = useRef(0)` — const, line 525
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 536
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 537
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 538
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 539
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 540
- `const modeSaveVersionRef = useRef(0)` — const, line 541
- `const answerModeSaveVersionRef = useRef(0)` — const, line 542
- `const enabled = contract?.readerEnabled ?? true` — const, line 558
- `const inquiry = contract?.inquiryEnabled === true` — const, line 561
- `const muted = inquiry && mode === "skim"` — const, line 564
- `const intentContract = inquiry && !offline ? contract?.intent ?? null : null` — const, line 567
- `const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading)` — const, line 568
- `const openFigureSource = useRef<((extractionId: string, spanId: string)` — const, line 572
- `const figureOpenSource = useCallback((extractionId: string, spanId: string)` — const, line 573
- `const figuresCtl = useFigures(` — const, line 574
- `const figureOffersOn = Boolean(contract?.figures?.offers) && !offline` — const, line 580
- `const showMeOn = Boolean(contract?.figures?.showMe) && !offline` — const, line 584
- `const waitingOfferRef = useRef<OfferedPress | null>(null)` — const, line 590
- `const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome)` — const, line 595
- `const press = offeredFigure` — const, line 602
- `const open = render?.extractionId ?? null` — const, line 604
- `const readerTutor = contract?.readerTutor ?? null` — const, line 627
- `const askWorkbenchSessionRef = useRef<string | null>(null)` — const, line 629
- `const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true` — const, line 634
- `const askPersonalizedRef = useRef<boolean | null>(null)` — const, line 635
- `const askComposerAnchorRef = useRef<AskAnchor | null>(null)` — const, line 640
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 646
- `const renderBlocksBySpan = useMemo( ()` — const, line 650
- `const visit = useReaderVisit(` — const, line 656
- `const showGuideRail = useCallback(()` — const, line 662
- `const progress = useReadingProgress(` — const, line 666
- `const doseVisitId = useCallback(()` — const, line 683
- `const refreshAnnotations = useCallback(async ()` — const, line 685
- `const epoch = sourceEpochRef.current` — const, line 687
- `const result = await cachedSourceRead( render.sourceId, ["reader_source_annotations", render.sourceId, render.extractionId], ()` — const, line 691
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 698
- `const version = (r.version as Record<string, unknown>) ??` — const, line 701
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 702
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 703
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 704
- `const placement = r.placement as ReaderAnnotationPlacementDto | undefined` — const, line 705
- `let page: number | null = null` — let, line 715
- `let bbox: number[] | null = null` — let, line 716
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 718
- `const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?:` — const, line 736
- `const openCardRef = useRef<SourceLibraryCard | null>(null)` — const, line 761
- `const openExtractionRef = useRef<string | null>(null)` — const, line 763
- `const reloadGuidePlan = useCallback(async ()` — const, line 765
- `const extractionId = render.extractionId` — const, line 767
- `const plan = await readGuidePlan(render.sourceId, extractionId,` — const, line 769
- `const spanOrder = useMemo( ()` — const, line 782
- `const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none"` — const, line 786
- `const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 789
- `const card = openCardRef.current` — const, line 790
- `const wbProps = useMemo<ReaderWorkbenchProps | undefined>(()` — const, line 800
- `const submitted = workbench?.onSubmitted` — const, line 801
- `const trail = besideTrail(returnStackRef.current)` — const, line 806
- `const wbCtl = useReaderWorkbench(` — const, line 811
- `const working = wbCtl.active !== null` — const, line 818
- `const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline` — const, line 822
- `const alsoHidden = alsoPrefs ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId)) : Boolean(contract?.correspondence?.hiddenEverywhere) || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.so…` — const, line 827
- `const peekCrumbShown = alsoPeek ?? findPeek` — const, line 837
- `const pathRefreshKey = readingPathRefreshKey(` — const, line 852
- `const tryFirstRef = useRef<((spanId: string)` — const, line 866
- `const cueCtl = useReaderCues(` — const, line 867
- `const recapCtl = useReaderRecap(` — const, line 882
- `const sourceLifecycleState = useWindowLifecycle().state` — const, line 898
- `const railOnScreen = windowed ? Boolean(windowed.railHost) && !isPaused(windowed.railHost?.lifecycle.state ?? "hidden") : !isPaused(sourceLifecycleState)` — const, line 899
- `const recapShown = Boolean(railOnScreen && recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working)` — const, line 902
- `const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip")` — const, line 913
- `const root = history.find((entry)` — const, line 914
- `const recapRevisited = useCallback((rootId: string)` — const, line 927
- `const root = history.find((entry)` — const, line 928
- `const recapRevisit = useCallback(async (rootId: string)` — const, line 931
- `const root = history.find((entry)` — const, line 932
- `const recapOpenInquiry = useCallback((rootId: string, spanId: string)` — const, line 938
- `const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch")` — const, line 941
- `const cueMarksFor = (markSurface: "pdf" | "watch")` — const, line 961
- `let cancelled = false` — let, line 970
- `const scroller = railRef.current` — const, line 1003
- `const clamp = ()` — const, line 1005
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 1006
- `const observer = new ResizeObserver(clamp)` — const, line 1009
- `const query = librarySearch.trim()` — const, line 1020
- `let cancelled = false` — let, line 1027
- `const timer = window.setTimeout(()` — const, line 1030
- `const resetSourceState = useCallback(()` — const, line 1053
- `const openSource = useCallback( async ( card: SourceLibraryCard, jumpSpan?: string, // jumpReading: the reading jumpSpan was found on (a search hit, a // return)` — const, line 1102
- `const handoff = options.handoff ?? null` — const, line 1112
- `const view = options.view ?? await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 1130
- `const pdfRequest = ++pdfViewRequestRef.current` — const, line 1177
- `const current = ()` — const, line 1178
- `const openFixture = useCallback(()` — const, line 1213
- `const backToLibrary = useCallback(()` — const, line 1221
- `const spanId = readingSpan ?? activeSpan` — const, line 1225
- `const section = guidePlan?.sections.find((candidate)` — const, line 1226
- `const resumedRef = useRef(false)` — const, line 1244
- `const trail = initialSource.besideTrail ?? null` — const, line 1248
- `const activeBlock = useMemo(()` — const, line 1262
- `const pdfHighlights: PdfHighlight[] = useMemo(()` — const, line 1271
- `const list: PdfHighlight[] = []` — const, line 1272
- `const base =` — const, line 1275
- `const placed = highlightFromPlacement(base, a.placement)` — const, line 1277
- `const segments = a.segments.flatMap((s)` — const, line 1282
- `const annotatedSpans = useMemo( ()` — const, line 1289
- `const annotationBySpan = useMemo(()` — const, line 1294
- `const map = new Map<string, MarginAnnotation>()` — const, line 1295
- `const before = map.get(spanId)` — const, line 1299
- `const boundaryBlock = useMemo(()` — const, line 1305
- `const revealedPassages = useMemo(()` — const, line 1307
- `const revealed = new Set(revealedSections)` — const, line 1308
- `const map = new Map<string,` — const, line 1309
- `const revealedGuidanceSpans = useMemo(()` — const, line 1318
- `const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null` — const, line 1323
- `const protectedSelection = selectionProtected(protection, selection)` — const, line 1324
- `const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1325
- `const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan))` — const, line 1329
- `const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1330
- `const editCaptureText = useCallback((text: string)` — const, line 1335
- `const resetCaptureText = useCallback(()` — const, line 1338
- `const saveAnnotationEdit = useCallback(async ()` — const, line 1350
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 1372
- `const result = await api.readerReanchor(` — const, line 1376
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1393
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1416
- `const target = annotations.find((a)` — const, line 1417
- `const reading = render ?` — const, line 1418
- `const epoch = sourceEpochRef.current` — const, line 1419
- `const undoRemove = useCallback(async ()` — const, line 1434
- `const last = removed` — const, line 1435
- `const epoch = sourceEpochRef.current` — const, line 1441
- `const result = await api.readerRestoreAnnotation(` — const, line 1443
- `const timer = window.setTimeout(()` — const, line 1456
- `const onKey = (event: KeyboardEvent)` — const, line 1462
- `const target = event.target` — const, line 1465
- `const openAnnotationNote = useCallback((annotationId: string)` — const, line 1473
- `const target = annotations.find((a)` — const, line 1474
- `const nodesForRange = useCallback((range: Range): Array<` — const, line 1487
- `const container = bodyRef.current` — const, line 1488
- `const nodes: Array<` — const, line 1490
- `const seen = new Set<string>()` — const, line 1491
- `const spanId = el.dataset.spanId` — const, line 1493
- `let intersects = false` — let, line 1495
- `const sub = document.createRange()` — const, line 1502
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1510
- `const block = renderBlocksBySpan.get(spanId)` — const, line 1515
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1521
- `const sel = window.getSelection()` — const, line 1522
- `const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1530
- `const cancelIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1531
- `const selectionSpanIds = useMemo( ()` — const, line 1532
- `const intentBox = useIntentBox(` — const, line 1536
- `const openActiveRail = useCallback(()` — const, line 1550
- `const activeCtl = useActiveReading(` — const, line 1554
- `const libraryCtl = useLibraryAsk(` — const, line 1563
- `const keptCtl = useKeptComparisons(` — const, line 1565
- `const notesCtl = useNoteMarks(` — const, line 1567
- `const windowActive = useWindowLifecycle().state === "active"` — const, line 1573
- `const pdfMarks = (): ReadonlyMap<string, ReactNode> | null` — const, line 1582
- `const cues = cueMarksFor("pdf")` — const, line 1583
- `const merged = new Map<string, ReactNode>(cues ?? [])` — const, line 1585
- `const cue = merged.get(spanId)` — const, line 1587
- `const before = merged.get(spanId)` — const, line 1592
- `const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null)` — const, line 1598
- `const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint)` — const, line 1600
- `const sbs = useSideBySide(` — const, line 1602
- `const node = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1610
- `const sbsPanes = sbs.panes && !comparing` — const, line 1623
- `const sbsPanesRef = useRef(false)` — const, line 1624
- `const sbsShownRef = useRef(false)` — const, line 1629
- `const sbsRef = useRef(sbs)` — const, line 1631
- `const sbsEscBusyRef = useRef(false)` — const, line 1634
- `const sbsPaneRef = useRef<HTMLDivElement | null>(null)` — const, line 1636
- `const runSideIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1641
- `const cancelSideIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1642
- `const sbsSection = sbs.section && sbs.target && sbs.section.sectionId === sbs.target.sectionId ? sbs.section : null` — const, line 1643
- `type BesideRun = |` — type, line 1658
- `const besideSeq = useRef(0)` — const, line 1667
- `const besideRunRef = useRef<(run: BesideRun)` — const, line 1670
- `const besideDroppedRef = useRef<(run: BesideRun)` — const, line 1671
- `const openBesideRef = useRef<(hit:` — const, line 1672
- `const snapshotBesideRef = useRef<(spanId: string)` — const, line 1679
- `const shown = sbsRef.current.target` — const, line 1681
- `const takeBesideBook = useCallback((book: SourceIdentity, spanId: string, run: BesideRun)` — const, line 1685
- `const id = ++besideSeq.current` — const, line 1687
- `const sideExtractionRef = useRef<string | null>(null)` — const, line 1699
- `const checkMeFromSideCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 1700
- `const side = useSidePane(` — const, line 1705
- `const besideRanRef = useRef(0)` — const, line 1734
- `const handoff = besideHandoff` — const, line 1736
- `const card = openCardRef.current` — const, line 1751
- `const trail = besideTrail(returnStackRef.current)` — const, line 1753
- `const work = handoff.run` — const, line 1762
- `const openComposer = useCallback((anchor: AskAnchor | null)` — const, line 1776
- `const sbsRowRef = useRef<HTMLDivElement | null>(null)` — const, line 1794
- `const startSbsResize = (event: ReactPointerEvent<HTMLDivElement>)` — const, line 1795
- `const row = sbsRowRef.current` — const, line 1796
- `const rect = row.getBoundingClientRect()` — const, line 1799
- `const move = (moved: PointerEvent)` — const, line 1800
- `const offs: Array<()` — const, line 1803
- `const up = ()` — const, line 1804
- `const touchMain = ()` — const, line 1814
- `const onKey = (event: KeyboardEvent)` — const, line 1823
- `const target = event.target` — const, line 1825
- `const ctl = sbsRef.current` — const, line 1827
- `const open = ctl.panes || ctl.sheet` — const, line 1828
- `const shown = sbsShownRef.current` — const, line 1829
- `const mod = event.ctrlKey || event.metaKey` — const, line 1830
- `const side = sbsPaneRef.current` — const, line 1840
- `const inSide = target instanceof Element && Boolean(target.closest("[data-side-by-side-pane]"))` — const, line 1841
- `const inMain = target instanceof Node && Boolean(bodyRef.current?.contains(target))` — const, line 1847
- `const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false, anchor?: SourceIdentity)` — const, line 1856
- `const identity = anchor ?? identityOf(render)` — const, line 1863
- `const request =` — const, line 1864
- `const closeLibrary = useCallback(()` — const, line 1869
- `const onKey = (event: KeyboardEvent)` — const, line 1876
- `const onMouseUp = useCallback(()` — const, line 1886
- `const sel = window.getSelection()` — const, line 1887
- `const quote = selectionQuote(sel.getRangeAt(0), sel.toString()).replace(/\s+/g, " ").trim()` — const, line 1891
- `const nodes = collectSelectionNodes()` — const, line 1893
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1922
- `const domDragRef = useRef<` — const, line 1923
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1925
- `const host = bodyRef.current` — const, line 1926
- `const rect = host.getBoundingClientRect()` — const, line 1928
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1932
- `const target = event.target as Node` — const, line 1936
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1938
- `const domDrafting = domDraft !== null` — const, line 1950
- `const rectFrom = (drag:` — const, line 1953
- `const onMove = (event: MouseEvent)` — const, line 1959
- `const drag = domDragRef.current` — const, line 1960
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1962
- `const onUp = (event: MouseEvent)` — const, line 1965
- `const drag = domDragRef.current` — const, line 1966
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1970
- `const rect = rectFrom(drag, point)` — const, line 1972
- `const next = [...domBoxesRef.current, rect]` — const, line 1975
- `const offs = [hub.listen("window", "mousemove", onMove), hub.listen("window", "mouseup", onUp)]` — const, line 1981
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1988
- `const host = bodyRef.current` — const, line 1989
- `const hostRect = host.getBoundingClientRect()` — const, line 1991
- `const clientBoxes = boxes.map((b)` — const, line 1992
- `const nodes: Array<` — const, line 1998
- `const seen = new Set<string>()` — const, line 1999
- `const spanId = el.dataset.spanId` — const, line 2001
- `const elRect = el.getBoundingClientRect()` — const, line 2003
- `const touches = clientBoxes.some( (b)` — const, line 2004
- `const words: string[] = []` — const, line 2008
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 2009
- `const text = node as Text` — const, line 2011
- `const wordPattern = /\S+/g` — const, line 2012
- `let match: RegExpExecArray | null` — let, line 2013
- `const range = document.createRange()` — const, line 2015
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 2018
- `const cx = (Math.min(...rects.map((r)` — const, line 2020
- `const cy = (Math.min(...rects.map((r)` — const, line 2021
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 2025
- `const commitDomBoxes = useCallback(()` — const, line 2034
- `const boxes = domBoxesRef.current` — const, line 2035
- `const nodes = resolveDomBoxes(boxes)` — const, line 2037
- `const quote = nodes.map((n)` — const, line 2043
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 2052
- `const clearDomBoxes = ()` — const, line 2060
- `const onKeyDown = (event: KeyboardEvent)` — const, line 2066
- `const onKeyUp = (event: KeyboardEvent)` — const, line 2071
- `const onBlur = ()` — const, line 2077
- `const offs = [ hub.listen("window", "keydown", onKeyDown), hub.listen("window", "keyup", onKeyUp), hub.listen("window", "blur", onBlur), ]` — const, line 2078
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 2097
- `const point = domPointFromClient(request.x, request.y)` — const, line 2099
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 2100
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 2121
- `const retryRequest = useCallback(async (requestId: string)` — const, line 2134
- `const optimisticSegments = useCallback( (nodes: string | Array<string |` — const, line 2148
- `const list = Array.isArray(nodes) ? nodes : [nodes]` — const, line 2150
- `const spanId = typeof node === "string" ? node : node.spanId` — const, line 2152
- `const geometry = pdfView?.blocks.find((b)` — const, line 2153
- `const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number" ?` — const, line 2154
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 2166
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 2170
- `const quotedNodes = (()` — const, line 2175
- `const multi = collectSelectionNodes()` — const, line 2178
- `const optimisticIds = quotedNodes ?? [target.spanId]` — const, line 2181
- `const nodes = quotedNodes ?? [` — const, line 2191
- `const receipt = await api.readerCapture(` — const, line 2192
- `const handler = (event: KeyboardEvent)` — const, line 2219
- `const clearSelection = useCallback(()` — const, line 2230
- `const railHostTab = windowed?.railHost?.tab ?? null` — const, line 2242
- `const windowExtraction = render?.extractionId ?? null` — const, line 2243
- `const onWindowTitle = windowed?.onTitle` — const, line 2248
- `const onWindowStatus = windowed?.onStatus` — const, line 2252
- `const windowWhere = currentGuideSection ? sectionWords(currentGuideSection.label) : null` — const, line 2253
- `const onWindowMediaReady = windowed?.onMediaReady` — const, line 2257
- `const onWindowJumpReady = windowed?.onJumpReady` — const, line 2263
- `const onWindowPenSurface = windowed?.onPenSurface` — const, line 2269
- `const penTextShown = Boolean(render) && !(pdfView && surface === "pdf")` — const, line 2270
- `const body = bodyRef.current` — const, line 2272
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 2288
- `const segment = a.segments.find((s)` — const, line 2290
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 2297
- `const alsoKeyRef = useRef<()` — const, line 2307
- `const onKey = (event: KeyboardEvent)` — const, line 2315
- `const target = event.target` — const, line 2318
- `const tabs: ReaderRailTab[] = ["guide", "ask", "notes"]` — const, line 2320
- `const askRequestSeen = useRef(askRequest)` — const, line 2357
- `const revealAskRef = useRef<()` — const, line 2359
- `const startCompareRef = useRef<(request: CompareRequest)` — const, line 2384
- `const sideAnchor = Boolean(side.extractionId) && side.extractionId === request.extractionId` — const, line 2387
- `const request = compareWaitsForWork` — const, line 2394
- `const sideMarksChanged = side.marksChanged` — const, line 2404
- `const captureIn = useCallback(async (target: PaneCaptureTarget, what:` — const, line 2405
- `const common =` — const, line 2410
- `const receipt: ReaderPresetReceiptDto = "preset" in what ? await api.readerInvokePreset(` — const, line 2415
- `const drained = await api.readerDrainOutbox()` — const, line 2426
- `const invokePreset = useCallback( // RW1b: the intent box passes its own words as the annotation's learner // text, and names the intention and entry in the funnel event. // Reader CA6b: `target` is side by side's second pane (its book, revision, // reading a…` — const, line 2447
- `const note_ = learnerTextOverride ?? note` — const, line 2455
- `const nodes = selectionNodes(selection)` — const, line 2456
- `const editedText = selection.editedText?.trim()` — const, line 2457
- `const receipt = await api.readerInvokePreset(` — const, line 2469
- `const drained = await api.readerDrainOutbox()` — const, line 2493
- `const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>, target?: PaneCaptureTarget): Promise<string | null>` — const, line 2516
- `const note_ = learnerTextOverride ?? note` — const, line 2520
- `const nodes = selectionNodes(selection)` — const, line 2521
- `const receipt = await api.readerCapture(` — const, line 2534
- `const currentHighlight = selection && selectionHighlight && selectionActions.includes("highlight") && selectionHighlight.spanId === selection.spanId && selectionHighlight.quote === selection.quote ? selectionHighlight : null` — const, line 2564
- `const saveHighlightNote = useCallback(async ()` — const, line 2569
- `const target = currentHighlight` — const, line 2570
- `const words = note.trim()` — const, line 2571
- `const learnerText = target.saved.trim() ? `$` — const, line 2573
- `const typed = note` — const, line 2574
- `const kept = ()` — const, line 2575
- `const annotationId = target.annotationId` — const, line 2586
- `const pauseArc = useCallback(async ()` — const, line 2603
- `const next = await api.readerArc(` — const, line 2607
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 2614
- `const next = await api.readerArc(` — const, line 2619
- `const importJobRef = useRef<` — const, line 2631
- `const importExercise = useCallback(async (target?: PaneCaptureTarget): Promise<string | null>` — const, line 2634
- `const nodes = target ? target.nodes : selectionNodes(selection!)` — const, line 2636
- `const editedText = target ? undefined : selection!.editedText?.trim()` — const, line 2637
- `const receipt = await api.readerImportExercise(target ?` — const, line 2640
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 2688
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 2689
- `const timer = setInterval(async ()` — const, line 2693
- `const status = await api.readerExerciseImportStatus(` — const, line 2695
- `const job = importJobRef.current` — const, line 2696
- `const waited = Date.now() - job.startedAt` — const, line 2699
- `const saveOwnQuestion = useCallback(async ()` — const, line 2726
- `const saved = await api.readerAuthorQA(` — const, line 2734
- `const runCoach = useCallback(async ()` — const, line 2755
- `const lint = await api.readerCoachLint(` — const, line 2758
- `const changeMode = useCallback( async (next: string)` — const, line 2769
- `const previous = mode` — const, line 2771
- `const version = ++modeSaveVersionRef.current` — const, line 2774
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 2785
- `const answerModeNext = next as ReaderAnswerMode` — const, line 2787
- `const previous = answerMode` — const, line 2788
- `const version = ++answerModeSaveVersionRef.current` — const, line 2791
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 2807
- `const renderInquiryTop = useCallback((root: ReaderExchange)` — const, line 2822
- `const line = reconnect && reconnect.rootId === root.id && !muted ? ( <ReconnectLine placement="rail" question=` — const, line 2825
- `const check = inquiryChecks[root.id]` — const, line 2835
- `const inlineReconnect = reconnect && reconnect.inline && !muted ? ( <ReconnectLine placement="inline" question=` — const, line 2863
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 2874
- `const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, pinned?: ReaderRenderViewDto): Promise<OpenOutcome>` — const, line 2893
- `const card = (library ?? []).find((candidate)` — const, line 2898
- `const spanId = readingSpan ?? activeSpan` — const, line 2901
- `const onOriginal = pdfView && surface === "pdf" && !offline` — const, line 2927
- `const epoch = sourceEpochRef.current` — const, line 2940
- `const sameBook = Boolean(render && sourceId === render.sourceId)` — const, line 2943
- `const card = (library ?? []).find((candidate)` — const, line 2944
- `const landed = await api.readerSavedPlace(` — const, line 2949
- `const landing = await api.readerRenderView(` — const, line 2963
- `const openFollowedFigure = (figure: CorrespondentFigureDto, hit: CorrespondentSectionDto)` — const, line 2973
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2975
- `const compareFoundSection = (hit: CorrespondentSectionDto)` — const, line 2990
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2992
- `const hideAlsoInBooks = (scope: "book" | "everywhere")` — const, line 3015
- `const before = alsoPrefs ??` — const, line 3017
- `const base = contract` — const, line 3024
- `const makeExplorable = (target: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, origin: "library" | "tutor", offerRef: string): Promise<ExplorableOutcome>` — const, line 3041
- `let settle: (outcome: ExplorableOutcome)` — let, line 3048
- `const settled = new Promise<ExplorableOutcome>((resolve)` — const, line 3049
- `const press: OfferedPress =` — const, line 3050
- `const peekWorkbenchPassage = (spanId: string, target?: PassageTarget)` — const, line 3069
- `const exerciseSettings = libraryCtl.enabled ? contract?.libraryExercises ?? null : null` — const, line 3080
- `const exerciseCard = (sourceId: string | null)` — const, line 3081
- `const useExercise = (candidate: ExerciseCandidate)` — const, line 3085
- `const card = exerciseCard(candidate.sourceId ?? render?.sourceId ?? null)` — const, line 3086
- `const openExerciseInBook = (candidate: ExerciseCandidate)` — const, line 3095
- `const sourceId = candidate.sourceId ?? render?.sourceId ?? null` — const, line 3096
- `const exerciseProps: LibraryExercisesProps | null = exerciseSettings ?` — const, line 3099
- `const pickLibraryPagePractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3113
- `const hit = libraryCtl.state?.ask.value?.hits[0]` — const, line 3114
- `const card = hit ? (library ?? []).find((candidate)` — const, line 3115
- `const readySources = library ?? []` — const, line 3167
- `const useShelf = Boolean(shelf) && !sidecarDown` — const, line 3169
- `const card = (library ?? []).find((candidate)` — const, line 3227
- `const card = (library ?? []).find((c)` — const, line 3248
- `const receiptId = searchResults.retrievalReceiptId` — const, line 3254
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 3299
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 3300
- `const wbActive = wbCtl.active` — const, line 3343
- `const wbStacked = working && wbCtl.narrow` — const, line 3344
- `const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible)` — const, line 3347
- `const wbSourceShown = !wbStacked || wbCtl.sheetOpen` — const, line 3348
- `const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry)` — const, line 3349
- `const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>()` — const, line 3350
- `const first = entry.spanIds[0]` — const, line 3352
- `const wbLabel = (stem: string)` — const, line 3355
- `const title = problemTitle(stem)` — const, line 3356
- `const tryPathExercise = (exercise: ReadingPathExerciseDto)` — const, line 3361
- `const workThroughSelection = ()` — const, line 3369
- `const nodes = selectionNodes(selection)` — const, line 3371
- `const editedText = selection.editedText?.trim()` — const, line 3372
- `const foldBlocks = contract?.activeReading?.foldBlocks ?? 3` — const, line 3389
- `const localFold = (spanIds: string[]): string[]` — const, line 3390
- `const positions = spanIds.map((spanId)` — const, line 3391
- `const last = Math.max(...positions)` — const, line 3393
- `const mainPane: IntentPane =` — const, line 3402
- `const sidePane: IntentPane | null = side.extractionId ?` — const, line 3411
- `const sideMeta = (pane: IntentPane): Record<string, string>` — const, line 3421
- `const runIntentIn = (pane: IntentPane, action: ReaderIntentActionDto, text: string, how: IntentRunHow): Promise<IntentRunHandle | null> | void` — const, line 3423
- `const meta =` — const, line 3424
- `const effect = action.effect` — const, line 3425
- `const noteText = !action.model && intentContract && onlyNamesAnAction(text, [...intentContract.palette, ...intentContract.notesPalette]) ? "" : text` — const, line 3429
- `const sideSection = pane.side?.section ?? null` — const, line 3431
- `const anchor: AskAnchor =` — const, line 3437
- `const target = pane.side.target` — const, line 3478
- `const target = pane.side.target` — const, line 3484
- `const target = pane.side.target` — const, line 3490
- `const target = pane.side.target` — const, line 3500
- `const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null` — const, line 3545
- `const request: CompareRequest =` — const, line 3546
- `const region = pane.region` — const, line 3578
- `const words = text?.trim()` — const, line 3579
- `const sideShows = (extractionId: string, spanId: string): boolean` — const, line 3600
- `const checkBeside = (book: SourceIdentity, spanId: string, practiceItemId: string, proposalId: string | null)` — const, line 3603
- `const workThroughImported = (item:` — const, line 3608
- `const imported = exerciseImport` — const, line 3609
- `const spanIds = imported?.spanIds ?? (activeSpan ? [activeSpan] : [])` — const, line 3610
- `const settleShowMeLine = (key: string, patch: Partial<ShowMeLine>)` — const, line 3618
- `const requestShowMe = (ctl: FiguresCtl, run: Extract<BesideRun,` — const, line 3621
- `const key = run.lineKey` — const, line 3622
- `const runOnBook = (about: AskAbout, run: Extract<BesideRun,` — const, line 3634
- `const showMeFromAsk = ()` — const, line 3659
- `const goal = question.trim()` — const, line 3660
- `const about = parentExchange ? parentExchange.about ?? null : askComposerAnchor?.about ?? null` — const, line 3661
- `const home = parentExchange?.spanId ?? (about ? askComposerAnchor?.spanId : undefined) ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan` — const, line 3662
- `const key = `show_me:$` — const, line 3665
- `const run =` — const, line 3668
- `const cancelIntentIn = (pane: IntentPane, cancel: IntentCancel)` — const, line 3677
- `const kind = cancel.action.effect.kind` — const, line 3678
- `const annotationId = handle.annotationId` — const, line 3685
- `const batchId = handle.importBatchId` — const, line 3702
- `const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number)` — const, line 3716
- `const spanId = wbCtl.close(session,` — const, line 3718
- `const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3724
- `const card = openCardRef.current` — const, line 3725
- `const asked = libraryCtl.state?.request` — const, line 3729
- `const resumeMark = (spanId: string | null | undefined)` — const, line 3737
- `const entry = spanId ? wbResumeBySpan.get(spanId) : undefined` — const, line 3738
- `const verb = entry.status === "abandoned" ? "Reopen" : "Resume"` — const, line 3740
- `const placeRail = (rail: ReactNode): ReactNode` — const, line 3759
- `const host = windowed.railHost` — const, line 3761
- `const overDesk = (menu: ReactNode): ReactNode` — const, line 3770
- `const target = event.target` — const, line 3906
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 4082
- `const active = activeSpan === block.spanId` — const, line 4083
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 4084
- `const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null` — const, line 4085
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 4086
- `const endQuestionAvailable = Boolean(endSection && endSection.question?.readingPhase === "after_section" && offeredCheckSections.has(endSection.id))` — const, line 4088
- `const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId))` — const, line 4092
- `const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""))` — const, line 4093
- `const offerSection = endSection && !muted && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 4094
- `const sel = window.getSelection()` — const, line 4119
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 4120
- `const cue = side.cues.markOn(spanId)` — const, line 4211
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 4239
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 4262
- `const active = railTab === tab` — const, line 4377
- `const waiting = tab === "guide" && pendingQuickCheckCount > 0` — const, line 4381
- `const marked = tab === "ask" && askTabMarked && !active` — const, line 4382
- `const params = (action.params ??` — const, line 4533
- `const run =` — const, line 4807
- `const book = exchange?.about ?? render` — const, line 4816

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`; references `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`
- [[Reference/Desktop/TypeScript/screens/desks/goal/GoalLayer|src/screens/desks/goal/GoalLayer.tsx]] — import-or-re-export: `ReaderLens`; references `ReaderLens`
- [[Reference/Desktop/TypeScript/screens/desks/goal/marks|src/screens/desks/goal/marks.tsx]] — import-or-re-export: `ReaderLens`; references `ReaderLens`
- [[Reference/Desktop/TypeScript/screens/desks/pen/PenLayer|src/screens/desks/pen/PenLayer.tsx]] — import-or-re-export: `PenSurface`; references `PenSurface`
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
- [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]] — import-or-re-export; imports `WatchLens`, `WatchPanelHandle`, `YouTubeWatchPanel`
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

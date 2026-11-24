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
| Source lines | 5366 |
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

- `export interface ReaderOpenSource` — interface, line 252
- `export interface ReaderWindowing` — interface, line 275
- `export interface WindowInquiry` — interface, line 326
- `export interface ReaderLens` — interface, line 341
- `export interface PenSurface` — interface, line 354
- `export interface ReaderCheckMeRequest extends CueCheckMeRequest` — interface, line 364
- `export type ReaderExerciseRequest = ReaderWorkbenchExercise &` — type, line 377
- `export const SIDE_PATH_COPY =` — const, line 381
- `export function ReaderScreen(` — function, line 403

## Internal implementation anchors

- `type AnnotationSegment, type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 149
- `type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 150
- `type ReaderSelection, } from "./reader/readerShared"` — type, line 151
- `const NO_SECTIONS: never[] = []` — const, line 155
- `const READER_MODE_OPTIONS = [` — const, line 156
- `const TAG_ACTIONS: Array<` — const, line 166
- `const WHOLE_BLOCK_QUOTE = "(whole block)"` — const, line 174
- `type ReaderRailTab = "guide" | "ask" | "notes"` — type, line 176
- `const HEALTH_COLOR: Record<string, "green" | "amber" | "pink" | "slate"> =` — const, line 178
- `const FIGURE_PAGE_NOT_OPENED = "That page couldn't be opened."` — const, line 186
- `type OpenOutcome = "opened" | "preparing" | "not_opened"` — type, line 189
- `interface OfferedPress` — interface, line 193
- `const OFFER_OUTCOME: Record<FigureRequestOutcome, ExplorableOutcome> =` — const, line 204
- `const BADGED_HEALTH = new Set(["suspect", "failed"])` — const, line 210
- `interface RemovedAnnotation` — interface, line 214
- `const UNDO_REMOVE_MS = 10_000` — const, line 224
- `interface SelectionHighlight` — interface, line 227
- `function newKey(): string` — function, line 234
- `function identityOf(view: Pick<ReaderRenderViewDto, "sourceId" | "revisionId" | "extractionId">): SourceIdentity` — function, line 243
- `function sectionIdentity(section:` — function, line 248
- `function RailScope(` — function, line 267
- `const lifecycle = useWindowLifecycle()` — const, line 268
- `const mainPaneOwnsCueKey = (event: KeyboardEvent): boolean` — const, line 388
- `interface IntentPane` — interface, line 393
- `const hub = useListenerHub()` — const, line 461
- `const windowPaused = useWindowPaused()` — const, line 463
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 467
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 471
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 480
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 481
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 482
- `const openingRef = useRef<string | null>(null)` — const, line 488
- `const savingHighlightNote = useRef(false)` — const, line 500
- `const askPanelOn = algoConfig().ask !== null` — const, line 514
- `const storedStyle = useStoredHelpStyle()` — const, line 515
- `const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen` — const, line 516
- `const pdfViewRequestRef = useRef(0)` — const, line 538
- `const sourceEpochRef = useRef(0)` — const, line 569
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 580
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 581
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 582
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 583
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 584
- `const modeSaveVersionRef = useRef(0)` — const, line 585
- `const answerModeSaveVersionRef = useRef(0)` — const, line 586
- `const enabled = contract?.readerEnabled ?? true` — const, line 602
- `const inquiry = contract?.inquiryEnabled === true` — const, line 605
- `const muted = inquiry && mode === "skim"` — const, line 608
- `const intentContract = inquiry && !offline ? contract?.intent ?? null : null` — const, line 611
- `const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading)` — const, line 612
- `const openFigureSource = useRef<((extractionId: string, spanId: string)` — const, line 616
- `const figureOpenSource = useCallback((extractionId: string, spanId: string)` — const, line 617
- `const figuresCtl = useFigures(` — const, line 618
- `const figureOffersOn = Boolean(contract?.figures?.offers) && !offline` — const, line 624
- `const showMeOn = Boolean(contract?.figures?.showMe) && !offline` — const, line 628
- `const waitingOfferRef = useRef<OfferedPress | null>(null)` — const, line 634
- `const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome)` — const, line 639
- `const press = offeredFigure` — const, line 646
- `const open = render?.extractionId ?? null` — const, line 648
- `const readerTutor = contract?.readerTutor ?? null` — const, line 671
- `const askWorkbenchSessionRef = useRef<string | null>(null)` — const, line 673
- `const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true` — const, line 678
- `const askPersonalizedRef = useRef<boolean | null>(null)` — const, line 679
- `const askComposerAnchorRef = useRef<AskAnchor | null>(null)` — const, line 684
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 690
- `const renderBlocksBySpan = useMemo( ()` — const, line 694
- `const visit = useReaderVisit(` — const, line 700
- `const showGuideRail = useCallback(()` — const, line 706
- `const progress = useReadingProgress(` — const, line 710
- `const doseVisitId = useCallback(()` — const, line 727
- `const refreshAnnotations = useCallback(async ()` — const, line 729
- `const epoch = sourceEpochRef.current` — const, line 731
- `const result = await cachedSourceRead( render.sourceId, ["reader_source_annotations", render.sourceId, render.extractionId], ()` — const, line 735
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 742
- `const version = (r.version as Record<string, unknown>) ??` — const, line 745
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 746
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 747
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 748
- `const placement = r.placement as ReaderAnnotationPlacementDto | undefined` — const, line 749
- `let page: number | null = null` — let, line 759
- `let bbox: number[] | null = null` — let, line 760
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 762
- `const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?:` — const, line 780
- `const openCardRef = useRef<SourceLibraryCard | null>(null)` — const, line 806
- `const openExtractionRef = useRef<string | null>(null)` — const, line 808
- `const reloadGuidePlan = useCallback(async ()` — const, line 810
- `const extractionId = render.extractionId` — const, line 812
- `const plan = await readGuidePlan(render.sourceId, extractionId,` — const, line 814
- `const spanOrder = useMemo( ()` — const, line 827
- `const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none"` — const, line 831
- `const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 834
- `const card = openCardRef.current` — const, line 835
- `const wbProps = useMemo<ReaderWorkbenchProps | undefined>(()` — const, line 845
- `const submitted = workbench?.onSubmitted` — const, line 846
- `const trail = besideTrail(returnStackRef.current)` — const, line 851
- `const wbCtl = useReaderWorkbench(` — const, line 856
- `const workOnPad = windowed?.onWorkOnPad ?? null` — const, line 865
- `const active = wbCtl.active` — const, line 867
- `const working = wbCtl.active !== null && !workOnPad` — const, line 876
- `const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline` — const, line 880
- `const alsoHidden = alsoPrefs ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId)) : Boolean(contract?.correspondence?.hiddenEverywhere) || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.so…` — const, line 885
- `const peekCrumbShown = alsoPeek ?? findPeek` — const, line 895
- `const pathRefreshKey = readingPathRefreshKey(` — const, line 910
- `const tryFirstRef = useRef<((spanId: string)` — const, line 924
- `const cueCtl = useReaderCues(` — const, line 925
- `const recapCtl = useReaderRecap(` — const, line 940
- `const sourceLifecycleState = useWindowLifecycle().state` — const, line 956
- `const railOnScreen = windowed ? Boolean(windowed.railHost) && !isPaused(windowed.railHost?.lifecycle.state ?? "hidden") : !isPaused(sourceLifecycleState)` — const, line 957
- `const guideOnScreen = railOnScreen && railTab === "guide"` — const, line 961
- `const recapInWindow = Boolean(windowed) && !guideOnScreen` — const, line 962
- `const recapShown = Boolean(railOnScreen && recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working) || Boolean(recapInWindow && recapCtl.recap && !recapCtl.collapsed && !muted && !working && !isPaused(…` — const, line 963
- `const drainHost = windowed?.drainHost ?? null` — const, line 971
- `const wrapUpForDrain = useRef(false)` — const, line 972
- `const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip")` — const, line 988
- `const root = history.find((entry)` — const, line 989
- `const recapRevisited = useCallback((rootId: string)` — const, line 1002
- `const root = history.find((entry)` — const, line 1003
- `const recapRevisit = useCallback(async (rootId: string)` — const, line 1006
- `const root = history.find((entry)` — const, line 1007
- `const recapOpenInquiry = useCallback((rootId: string, spanId: string)` — const, line 1013
- `const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch")` — const, line 1016
- `const cueMarksFor = (markSurface: "pdf" | "watch")` — const, line 1036
- `let cancelled = false` — let, line 1045
- `const scroller = railRef.current` — const, line 1078
- `const clamp = ()` — const, line 1080
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 1081
- `const observer = new ResizeObserver(clamp)` — const, line 1084
- `const query = librarySearch.trim()` — const, line 1095
- `let cancelled = false` — let, line 1102
- `const timer = window.setTimeout(()` — const, line 1105
- `const resetSourceState = useCallback(()` — const, line 1128
- `const openSource = useCallback( async ( card: SourceLibraryCard, jumpSpan?: string, // jumpReading: the reading jumpSpan was found on (a search hit, a // return)` — const, line 1177
- `const handoff = options.handoff ?? null` — const, line 1187
- `const view = options.view ?? await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 1205
- `const pdfRequest = ++pdfViewRequestRef.current` — const, line 1252
- `const current = ()` — const, line 1253
- `const openFixture = useCallback(()` — const, line 1288
- `const backToLibrary = useCallback(()` — const, line 1296
- `const spanId = readingSpan ?? activeSpan` — const, line 1300
- `const section = guidePlan?.sections.find((candidate)` — const, line 1301
- `const resumedRef = useRef(false)` — const, line 1319
- `const trail = initialSource.besideTrail ?? null` — const, line 1323
- `const activeBlock = useMemo(()` — const, line 1337
- `const pdfHighlights: PdfHighlight[] = useMemo(()` — const, line 1346
- `const list: PdfHighlight[] = []` — const, line 1347
- `const base =` — const, line 1350
- `const placed = highlightFromPlacement(base, a.placement)` — const, line 1352
- `const segments = a.segments.flatMap((s)` — const, line 1357
- `const annotatedSpans = useMemo( ()` — const, line 1364
- `const annotationBySpan = useMemo(()` — const, line 1369
- `const map = new Map<string, MarginAnnotation>()` — const, line 1370
- `const before = map.get(spanId)` — const, line 1374
- `const boundaryBlock = useMemo(()` — const, line 1380
- `const revealedPassages = useMemo(()` — const, line 1382
- `const revealed = new Set(revealedSections)` — const, line 1383
- `const map = new Map<string,` — const, line 1384
- `const revealedGuidanceSpans = useMemo(()` — const, line 1393
- `const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null` — const, line 1398
- `const protectedSelection = selectionProtected(protection, selection)` — const, line 1399
- `const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1400
- `const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan))` — const, line 1404
- `const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1405
- `const editCaptureText = useCallback((text: string)` — const, line 1410
- `const resetCaptureText = useCallback(()` — const, line 1413
- `const saveAnnotationEdit = useCallback(async ()` — const, line 1425
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 1447
- `const result = await api.readerReanchor(` — const, line 1451
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1468
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1491
- `const target = annotations.find((a)` — const, line 1492
- `const reading = render ?` — const, line 1493
- `const epoch = sourceEpochRef.current` — const, line 1494
- `const undoRemove = useCallback(async ()` — const, line 1509
- `const last = removed` — const, line 1510
- `const epoch = sourceEpochRef.current` — const, line 1516
- `const result = await api.readerRestoreAnnotation(` — const, line 1518
- `const timer = window.setTimeout(()` — const, line 1531
- `const onKey = (event: KeyboardEvent)` — const, line 1537
- `const target = event.target` — const, line 1540
- `const openAnnotationNote = useCallback((annotationId: string)` — const, line 1548
- `const target = annotations.find((a)` — const, line 1549
- `const windowNotesOnRef = useRef(false)` — const, line 1560
- `const windowOpenNote = windowed?.openNote ?? null` — const, line 1562
- `const openedNote = useRef<string | null>(null)` — const, line 1563
- `const nodesForRange = useCallback((range: Range): Array<` — const, line 1576
- `const container = bodyRef.current` — const, line 1577
- `const nodes: Array<` — const, line 1579
- `const seen = new Set<string>()` — const, line 1580
- `const spanId = el.dataset.spanId` — const, line 1582
- `let intersects = false` — let, line 1584
- `const sub = document.createRange()` — const, line 1591
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1599
- `const block = renderBlocksBySpan.get(spanId)` — const, line 1604
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1610
- `const sel = window.getSelection()` — const, line 1611
- `const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1619
- `const cancelIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1620
- `const selectionSpanIds = useMemo( ()` — const, line 1621
- `const intentBox = useIntentBox(` — const, line 1625
- `const openActiveRail = useCallback(()` — const, line 1639
- `const activeCtl = useActiveReading(` — const, line 1643
- `const libraryCtl = useLibraryAsk(` — const, line 1652
- `const keptCtl = useKeptComparisons(` — const, line 1654
- `const notesCtl = useNoteMarks(` — const, line 1656
- `const windowActive = useWindowLifecycle().state === "active"` — const, line 1662
- `const pdfMarks = (): ReadonlyMap<string, ReactNode> | null` — const, line 1671
- `const cues = cueMarksFor("pdf")` — const, line 1672
- `const merged = new Map<string, ReactNode>(cues ?? [])` — const, line 1674
- `const cue = merged.get(spanId)` — const, line 1676
- `const before = merged.get(spanId)` — const, line 1681
- `const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null)` — const, line 1687
- `const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint)` — const, line 1689
- `const sbs = useSideBySide(` — const, line 1691
- `const node = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1699
- `const sectionInView = render && currentGuideSection ? `$` — const, line 1711
- `const onSectionRef = useRef(windowed?.onSection)` — const, line 1712
- `const sbsPanes = sbs.panes && !comparing` — const, line 1722
- `const sbsPanesRef = useRef(false)` — const, line 1723
- `const sbsShownRef = useRef(false)` — const, line 1728
- `const sbsRef = useRef(sbs)` — const, line 1730
- `const sbsEscBusyRef = useRef(false)` — const, line 1733
- `const sbsPaneRef = useRef<HTMLDivElement | null>(null)` — const, line 1735
- `const runSideIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1740
- `const cancelSideIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1741
- `const sbsSection = sbs.section && sbs.target && sbs.section.sectionId === sbs.target.sectionId ? sbs.section : null` — const, line 1742
- `type BesideRun = |` — type, line 1757
- `const besideSeq = useRef(0)` — const, line 1766
- `const besideRunRef = useRef<(run: BesideRun)` — const, line 1769
- `const besideDroppedRef = useRef<(run: BesideRun)` — const, line 1770
- `const openBesideRef = useRef<(hit:` — const, line 1771
- `const snapshotBesideRef = useRef<(spanId: string)` — const, line 1778
- `const shown = sbsRef.current.target` — const, line 1780
- `const takeBesideBook = useCallback((book: SourceIdentity, spanId: string, run: BesideRun)` — const, line 1784
- `const id = ++besideSeq.current` — const, line 1786
- `const sideExtractionRef = useRef<string | null>(null)` — const, line 1798
- `const checkMeFromSideCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 1799
- `const side = useSidePane(` — const, line 1804
- `const besideRanRef = useRef(0)` — const, line 1833
- `const handoff = besideHandoff` — const, line 1835
- `const card = openCardRef.current` — const, line 1850
- `const trail = besideTrail(returnStackRef.current)` — const, line 1852
- `const work = handoff.run` — const, line 1861
- `const openComposer = useCallback((anchor: AskAnchor | null)` — const, line 1875
- `const sbsRowRef = useRef<HTMLDivElement | null>(null)` — const, line 1893
- `const startSbsResize = (event: ReactPointerEvent<HTMLDivElement>)` — const, line 1894
- `const row = sbsRowRef.current` — const, line 1895
- `const rect = row.getBoundingClientRect()` — const, line 1898
- `const move = (moved: PointerEvent)` — const, line 1899
- `const offs: Array<()` — const, line 1902
- `const up = ()` — const, line 1903
- `const touchMain = ()` — const, line 1913
- `const touchedRef = useRef(windowed?.onTouched)` — const, line 1918
- `const pairKeyRef = useRef(windowed?.onPairKey)` — const, line 1920
- `const onKey = (event: KeyboardEvent)` — const, line 1928
- `const target = event.target` — const, line 1930
- `const ctl = sbsRef.current` — const, line 1932
- `const open = ctl.panes || ctl.sheet` — const, line 1933
- `const shown = sbsShownRef.current` — const, line 1934
- `const mod = event.ctrlKey || event.metaKey` — const, line 1935
- `const side = sbsPaneRef.current` — const, line 1952
- `const inSide = target instanceof Element && Boolean(target.closest("[data-side-by-side-pane]"))` — const, line 1953
- `const inMain = target instanceof Node && Boolean(bodyRef.current?.contains(target))` — const, line 1959
- `const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false, anchor?: SourceIdentity)` — const, line 1968
- `const identity = anchor ?? identityOf(render)` — const, line 1975
- `const request =` — const, line 1976
- `const closeLibrary = useCallback(()` — const, line 1981
- `const onKey = (event: KeyboardEvent)` — const, line 1988
- `const onMouseUp = useCallback(()` — const, line 1998
- `const sel = window.getSelection()` — const, line 1999
- `const quote = selectionQuote(sel.getRangeAt(0), sel.toString()).replace(/\s+/g, " ").trim()` — const, line 2003
- `const nodes = collectSelectionNodes()` — const, line 2005
- `const domBoxesRef = useRef<number[][]>([])` — const, line 2034
- `const domDragRef = useRef<` — const, line 2035
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 2037
- `const host = bodyRef.current` — const, line 2038
- `const rect = host.getBoundingClientRect()` — const, line 2040
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 2044
- `const target = event.target as Node` — const, line 2048
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 2050
- `const domDrafting = domDraft !== null` — const, line 2062
- `const rectFrom = (drag:` — const, line 2065
- `const onMove = (event: MouseEvent)` — const, line 2071
- `const drag = domDragRef.current` — const, line 2072
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 2074
- `const onUp = (event: MouseEvent)` — const, line 2077
- `const drag = domDragRef.current` — const, line 2078
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 2082
- `const rect = rectFrom(drag, point)` — const, line 2084
- `const next = [...domBoxesRef.current, rect]` — const, line 2087
- `const offs = [hub.listen("window", "mousemove", onMove), hub.listen("window", "mouseup", onUp)]` — const, line 2093
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 2100
- `const host = bodyRef.current` — const, line 2101
- `const hostRect = host.getBoundingClientRect()` — const, line 2103
- `const clientBoxes = boxes.map((b)` — const, line 2104
- `const nodes: Array<` — const, line 2110
- `const seen = new Set<string>()` — const, line 2111
- `const spanId = el.dataset.spanId` — const, line 2113
- `const elRect = el.getBoundingClientRect()` — const, line 2115
- `const touches = clientBoxes.some( (b)` — const, line 2116
- `const words: string[] = []` — const, line 2120
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 2121
- `const text = node as Text` — const, line 2123
- `const wordPattern = /\S+/g` — const, line 2124
- `let match: RegExpExecArray | null` — let, line 2125
- `const range = document.createRange()` — const, line 2127
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 2130
- `const cx = (Math.min(...rects.map((r)` — const, line 2132
- `const cy = (Math.min(...rects.map((r)` — const, line 2133
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 2137
- `const commitDomBoxes = useCallback(()` — const, line 2146
- `const boxes = domBoxesRef.current` — const, line 2147
- `const nodes = resolveDomBoxes(boxes)` — const, line 2149
- `const quote = nodes.map((n)` — const, line 2155
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 2164
- `const clearDomBoxes = ()` — const, line 2172
- `const onKeyDown = (event: KeyboardEvent)` — const, line 2178
- `const onKeyUp = (event: KeyboardEvent)` — const, line 2183
- `const onBlur = ()` — const, line 2189
- `const offs = [ hub.listen("window", "keydown", onKeyDown), hub.listen("window", "keyup", onKeyUp), hub.listen("window", "blur", onBlur), ]` — const, line 2190
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 2209
- `const point = domPointFromClient(request.x, request.y)` — const, line 2211
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 2212
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 2233
- `const retryRequest = useCallback(async (requestId: string)` — const, line 2246
- `const optimisticSegments = useCallback( (nodes: string | Array<string |` — const, line 2260
- `const list = Array.isArray(nodes) ? nodes : [nodes]` — const, line 2262
- `const spanId = typeof node === "string" ? node : node.spanId` — const, line 2264
- `const geometry = pdfView?.blocks.find((b)` — const, line 2265
- `const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number" ?` — const, line 2266
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 2278
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 2282
- `const quotedNodes = (()` — const, line 2287
- `const multi = collectSelectionNodes()` — const, line 2290
- `const optimisticIds = quotedNodes ?? [target.spanId]` — const, line 2293
- `const nodes = quotedNodes ?? [` — const, line 2303
- `const receipt = await api.readerCapture(` — const, line 2304
- `const handler = (event: KeyboardEvent)` — const, line 2331
- `const clearSelection = useCallback(()` — const, line 2342
- `const railHostTab = windowed?.railHost?.tab ?? null` — const, line 2354
- `const windowExtraction = render?.extractionId ?? null` — const, line 2355
- `const onWindowTitle = windowed?.onTitle` — const, line 2360
- `const onWindowStatus = windowed?.onStatus` — const, line 2364
- `const windowWhere = currentGuideSection ? sectionWords(currentGuideSection.label) : null` — const, line 2365
- `const onWindowMediaReady = windowed?.onMediaReady` — const, line 2369
- `const onWindowJumpReady = windowed?.onJumpReady` — const, line 2375
- `const readingPathsOn = (Boolean(contract?.readingPaths) || Boolean(guidePlan?.sections.length)) && !offline` — const, line 2385
- `const onKey = (event: KeyboardEvent)` — const, line 2389
- `const onWindowInquiryReady = windowed?.onInquiryReady` — const, line 2397
- `const onWindowPenSurface = windowed?.onPenSurface` — const, line 2421
- `const penTextShown = Boolean(render) && !(pdfView && surface === "pdf")` — const, line 2422
- `const body = bodyRef.current` — const, line 2424
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 2440
- `const segment = a.segments.find((s)` — const, line 2442
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 2449
- `const alsoKeyRef = useRef<()` — const, line 2459
- `const onKey = (event: KeyboardEvent)` — const, line 2467
- `const target = event.target` — const, line 2470
- `const tabs: ReaderRailTab[] = ["guide", "ask", "notes"]` — const, line 2472
- `const askRequestSeen = useRef(askRequest)` — const, line 2509
- `const revealAskRef = useRef<()` — const, line 2511
- `const startCompareRef = useRef<(request: CompareRequest)` — const, line 2536
- `const sideAnchor = Boolean(side.extractionId) && side.extractionId === request.extractionId` — const, line 2539
- `const request = compareWaitsForWork` — const, line 2546
- `const sideMarksChanged = side.marksChanged` — const, line 2556
- `const captureIn = useCallback(async (target: PaneCaptureTarget, what:` — const, line 2557
- `const common =` — const, line 2562
- `const receipt: ReaderPresetReceiptDto = "preset" in what ? await api.readerInvokePreset(` — const, line 2567
- `const drained = await api.readerDrainOutbox()` — const, line 2578
- `const invokePreset = useCallback( // RW1b: the intent box passes its own words as the annotation's learner // text, and names the intention and entry in the funnel event. // Reader CA6b: `target` is side by side's second pane (its book, revision, // reading a…` — const, line 2599
- `const note_ = learnerTextOverride ?? note` — const, line 2607
- `const nodes = selectionNodes(selection)` — const, line 2608
- `const editedText = selection.editedText?.trim()` — const, line 2609
- `const receipt = await api.readerInvokePreset(` — const, line 2621
- `const drained = await api.readerDrainOutbox()` — const, line 2645
- `const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>, target?: PaneCaptureTarget): Promise<string | null>` — const, line 2668
- `const note_ = learnerTextOverride ?? note` — const, line 2672
- `const nodes = selectionNodes(selection)` — const, line 2673
- `const receipt = await api.readerCapture(` — const, line 2686
- `const currentHighlight = selection && selectionHighlight && selectionActions.includes("highlight") && selectionHighlight.spanId === selection.spanId && selectionHighlight.quote === selection.quote ? selectionHighlight : null` — const, line 2716
- `const saveHighlightNote = useCallback(async ()` — const, line 2721
- `const target = currentHighlight` — const, line 2722
- `const words = note.trim()` — const, line 2723
- `const learnerText = target.saved.trim() ? `$` — const, line 2725
- `const typed = note` — const, line 2726
- `const kept = ()` — const, line 2727
- `const annotationId = target.annotationId` — const, line 2738
- `const pauseArc = useCallback(async ()` — const, line 2755
- `const next = await api.readerArc(` — const, line 2759
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 2766
- `const next = await api.readerArc(` — const, line 2771
- `const importJobRef = useRef<` — const, line 2783
- `const importExercise = useCallback(async (target?: PaneCaptureTarget): Promise<string | null>` — const, line 2786
- `const nodes = target ? target.nodes : selectionNodes(selection!)` — const, line 2788
- `const editedText = target ? undefined : selection!.editedText?.trim()` — const, line 2789
- `const receipt = await api.readerImportExercise(target ?` — const, line 2792
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 2840
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 2841
- `const timer = setInterval(async ()` — const, line 2845
- `const status = await api.readerExerciseImportStatus(` — const, line 2847
- `const job = importJobRef.current` — const, line 2848
- `const waited = Date.now() - job.startedAt` — const, line 2851
- `const saveOwnQuestion = useCallback(async ()` — const, line 2878
- `const saved = await api.readerAuthorQA(` — const, line 2886
- `const runCoach = useCallback(async ()` — const, line 2907
- `const lint = await api.readerCoachLint(` — const, line 2910
- `const changeMode = useCallback( async (next: string)` — const, line 2921
- `const previous = mode` — const, line 2923
- `const version = ++modeSaveVersionRef.current` — const, line 2926
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 2937
- `const answerModeNext = next as ReaderAnswerMode` — const, line 2939
- `const previous = answerMode` — const, line 2940
- `const version = ++answerModeSaveVersionRef.current` — const, line 2943
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 2959
- `const renderInquiryTop = useCallback((root: ReaderExchange)` — const, line 2974
- `const line = reconnect && reconnect.rootId === root.id && !muted ? ( <ReconnectLine placement="rail" question=` — const, line 2977
- `const check = inquiryChecks[root.id]` — const, line 2987
- `const inlineReconnect = reconnect && reconnect.inline && !muted ? ( <ReconnectLine placement="inline" question=` — const, line 3015
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 3026
- `const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, pinned?: ReaderRenderViewDto): Promise<OpenOutcome>` — const, line 3045
- `const card = (library ?? []).find((candidate)` — const, line 3055
- `const spanId = readingSpan ?? activeSpan` — const, line 3058
- `const onOriginal = pdfView && surface === "pdf" && !offline` — const, line 3084
- `const epoch = sourceEpochRef.current` — const, line 3097
- `const sameBook = Boolean(render && sourceId === render.sourceId)` — const, line 3100
- `const card = (library ?? []).find((candidate)` — const, line 3101
- `const landed = await api.readerSavedPlace(` — const, line 3106
- `const landing = await api.readerRenderView(` — const, line 3120
- `const openFollowedFigure = (figure: CorrespondentFigureDto, hit: CorrespondentSectionDto)` — const, line 3130
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 3132
- `const compareFoundSection = (hit: CorrespondentSectionDto)` — const, line 3147
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 3149
- `const hideAlsoInBooks = (scope: "book" | "everywhere")` — const, line 3172
- `const before = alsoPrefs ??` — const, line 3174
- `const base = contract` — const, line 3181
- `const makeExplorable = (target: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, origin: "library" | "tutor", offerRef: string): Promise<ExplorableOutcome>` — const, line 3198
- `let settle: (outcome: ExplorableOutcome)` — let, line 3205
- `const settled = new Promise<ExplorableOutcome>((resolve)` — const, line 3206
- `const press: OfferedPress =` — const, line 3207
- `const peekWorkbenchPassage = (spanId: string, target?: PassageTarget)` — const, line 3226
- `const exerciseSettings = libraryCtl.enabled ? contract?.libraryExercises ?? null : null` — const, line 3237
- `const exerciseCard = (sourceId: string | null)` — const, line 3238
- `const useExercise = (candidate: ExerciseCandidate)` — const, line 3242
- `const card = exerciseCard(candidate.sourceId ?? render?.sourceId ?? null)` — const, line 3243
- `const openExerciseInBook = (candidate: ExerciseCandidate)` — const, line 3252
- `const sourceId = candidate.sourceId ?? render?.sourceId ?? null` — const, line 3253
- `const exerciseProps: LibraryExercisesProps | null = exerciseSettings ?` — const, line 3256
- `const pickLibraryPagePractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3270
- `const hit = libraryCtl.state?.ask.value?.hits[0]` — const, line 3271
- `const card = hit ? (library ?? []).find((candidate)` — const, line 3272
- `const readySources = library ?? []` — const, line 3324
- `const useShelf = Boolean(shelf) && !sidecarDown` — const, line 3326
- `const card = (library ?? []).find((candidate)` — const, line 3384
- `const card = (library ?? []).find((c)` — const, line 3405
- `const receiptId = searchResults.retrievalReceiptId` — const, line 3411
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 3456
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 3457
- `const wbActive = wbCtl.active` — const, line 3500
- `const wbStacked = working && wbCtl.narrow` — const, line 3501
- `const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible)` — const, line 3504
- `const wbSourceShown = !wbStacked || wbCtl.sheetOpen` — const, line 3505
- `const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry)` — const, line 3506
- `const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>()` — const, line 3507
- `const first = entry.spanIds[0]` — const, line 3509
- `const wbLabel = (stem: string)` — const, line 3512
- `const title = problemTitle(stem)` — const, line 3513
- `const tryPathExercise = (exercise: ReadingPathExerciseDto)` — const, line 3518
- `const workThroughSelection = ()` — const, line 3526
- `const nodes = selectionNodes(selection)` — const, line 3528
- `const editedText = selection.editedText?.trim()` — const, line 3529
- `const foldBlocks = contract?.activeReading?.foldBlocks ?? 3` — const, line 3546
- `const localFold = (spanIds: string[]): string[]` — const, line 3547
- `const positions = spanIds.map((spanId)` — const, line 3548
- `const last = Math.max(...positions)` — const, line 3550
- `const mainPane: IntentPane =` — const, line 3559
- `const sidePane: IntentPane | null = side.extractionId ?` — const, line 3568
- `const sideMeta = (pane: IntentPane): Record<string, string>` — const, line 3578
- `const runIntentIn = (pane: IntentPane, action: ReaderIntentActionDto, text: string, how: IntentRunHow): Promise<IntentRunHandle | null> | void` — const, line 3580
- `const meta =` — const, line 3581
- `const effect = action.effect` — const, line 3582
- `const noteText = !action.model && intentContract && onlyNamesAnAction(text, [...intentContract.palette, ...intentContract.notesPalette]) ? "" : text` — const, line 3586
- `const sideSection = pane.side?.section ?? null` — const, line 3588
- `const anchor: AskAnchor =` — const, line 3594
- `const spanId = pane.spanIds[0] ?? activeSpan ?? readingSpan` — const, line 3622
- `const target = pane.side.target` — const, line 3647
- `const target = pane.side.target` — const, line 3653
- `const target = pane.side.target` — const, line 3659
- `const target = pane.side.target` — const, line 3669
- `const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null` — const, line 3714
- `const request: CompareRequest =` — const, line 3715
- `const region = pane.region` — const, line 3752
- `const words = text?.trim()` — const, line 3753
- `const sideShows = (extractionId: string, spanId: string): boolean` — const, line 3774
- `const checkBeside = (book: SourceIdentity, spanId: string, practiceItemId: string, proposalId: string | null)` — const, line 3777
- `const workThroughImported = (item:` — const, line 3782
- `const imported = exerciseImport` — const, line 3783
- `const spanIds = imported?.spanIds ?? (activeSpan ? [activeSpan] : [])` — const, line 3784
- `const settleShowMeLine = (key: string, patch: Partial<ShowMeLine>)` — const, line 3792
- `const requestShowMe = (ctl: FiguresCtl, run: Extract<BesideRun,` — const, line 3795
- `const key = run.lineKey` — const, line 3796
- `const runOnBook = (about: AskAbout, run: Extract<BesideRun,` — const, line 3808
- `const showMeFromAsk = ()` — const, line 3833
- `const goal = question.trim()` — const, line 3834
- `const about = parentExchange ? parentExchange.about ?? null : askComposerAnchor?.about ?? null` — const, line 3835
- `const home = parentExchange?.spanId ?? (about ? askComposerAnchor?.spanId : undefined) ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan` — const, line 3836
- `const key = `show_me:$` — const, line 3839
- `const run =` — const, line 3842
- `const cancelIntentIn = (pane: IntentPane, cancel: IntentCancel)` — const, line 3851
- `const kind = cancel.action.effect.kind` — const, line 3852
- `const annotationId = handle.annotationId` — const, line 3859
- `const batchId = handle.importBatchId` — const, line 3876
- `const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number)` — const, line 3890
- `const spanId = wbCtl.close(session,` — const, line 3892
- `const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3898
- `const card = openCardRef.current` — const, line 3899
- `const asked = libraryCtl.state?.request` — const, line 3903
- `const resumeMark = (spanId: string | null | undefined)` — const, line 3911
- `const entry = spanId ? wbResumeBySpan.get(spanId) : undefined` — const, line 3912
- `const verb = entry.status === "abandoned" ? "Reopen" : "Resume"` — const, line 3914
- `const placeRail = (rail: ReactNode): ReactNode` — const, line 3933
- `const host = windowed.railHost` — const, line 3935
- `const overDesk = (menu: ReactNode): ReactNode` — const, line 3944
- `const wrapUpNode = recapCtl.wrapUpOpen ? ( <WrapUpPanel wrapUp=` — const, line 3947
- `const params = (action.params ??` — const, line 3959
- `const recapCardNode = recapCtl.recap ? ( <RecapCard recap=` — const, line 3968
- `const windowNotesOn = Boolean(windowed) && !(railOnScreen && railTab === "notes") && !offline` — const, line 3993
- `const annotationsBySpan = new Map<string, MarginAnnotation[]>()` — const, line 3995
- `const spanId = annotation.annotationId ? placedSpanIds(annotation)[0] : undefined` — const, line 3998
- `const windowNotesList = windowNotesSpan ? annotationsBySpan.get(windowNotesSpan) ?? [] : []` — const, line 4002
- `const windowNotesCard = windowNotesOn && windowNotesSpan && windowNotesList.length ? ( <div role="group" aria-label="your notes on this passage" data-window-notes="" style=` — const, line 4003
- `const windowNoteMark = (spanId: string | null | undefined): ReactNode` — const, line 4029
- `const windowActiveCard = windowed && activeReadingOn && (activeCtl.active || activeCtl.another) && !(railOnScreen && railTab === "notes") ? ( <div data-window-active-reading="" style=` — const, line 4048
- `const windowActiveSpans = activeCtl.another ? activeCtl.another.spanIds : activeCtl.active?.anchorSpanIds ?? []` — const, line 4053
- `const windowActiveSpan = windowActiveCard ? windowActiveSpans[windowActiveSpans.length - 1] ?? null : null` — const, line 4054
- `const windowChecksOn = Boolean(windowed) && !guideOnScreen && boundaryChecksAvailable && !working && !windowPathOpen` — const, line 4060
- `const openCheckIds = new Set(openQuestionSections.map((section)` — const, line 4061
- `const windowCheckAt = new Map<string, ReaderGuideSectionDto>()` — const, line 4062
- `const windowChecks = (spanId: string | null | undefined): ReactNode` — const, line 4069
- `const section = spanId ? windowCheckAt.get(spanId) : undefined` — const, line 4070
- `const windowAuthoringCard = Boolean(windowed) && authoringOpen && authoringSpanId && !(railOnScreen && railTab === "notes") && !offline ? ( <div role="group" aria-label="your own question" data-window-authoring="" style=` — const, line 4090
- `const windowPathShown = Boolean(windowed && windowPathOpen && readingPathsOn && render && !working && !guideOnScreen)` — const, line 4112
- `const windowTopShown = windowPathShown || Boolean(recapInWindow && !working && ((recapCtl.wrapUpOpen && !drainHost) || (recapCtl.recap && !muted)))` — const, line 4113
- `const windowInlineNotes = [ ...(windowActiveCard && windowActiveSpan ? [` — const, line 4114
- `const guideHeader = (!windowed || guideOnScreen) && ((recapCtl.wrapUpOpen && !drainHost) || (recapCtl.recap && !muted)) ? ( <>` — const, line 4125
- `const guideFooter = cueCtl.cues ? ( <CueFooter density=` — const, line 4131
- `const guideRail = (visible: boolean, inWindow: boolean): ReactNode` — const, line 4141
- `const target = event.target` — const, line 4392
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 4596
- `const active = activeSpan === block.spanId` — const, line 4597
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 4598
- `const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null` — const, line 4599
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 4600
- `const endQuestionAvailable = Boolean(endSection && endSection.question?.readingPhase === "after_section" && offeredCheckSections.has(endSection.id))` — const, line 4602
- `const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId))` — const, line 4606
- `const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""))` — const, line 4607
- `const offerSection = endSection && !muted && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 4608
- `const sel = window.getSelection()` — const, line 4633
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 4634
- `const cue = side.cues.markOn(spanId)` — const, line 4760
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 4788
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 4811
- `const active = railTab === tab` — const, line 4926
- `const waiting = tab === "guide" && pendingQuickCheckCount > 0` — const, line 4930
- `const marked = tab === "ask" && askTabMarked && !active` — const, line 4931
- `const run =` — const, line 5195
- `const book = exchange?.about ?? render` — const, line 5204

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`; references `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `WindowInquiry`; references `WindowInquiry`
- [[Reference/Desktop/TypeScript/screens/desks/checks/CheckCard|src/screens/desks/checks/CheckCard.tsx]] — import-or-re-export: `ReaderLens`; references `ReaderLens`
- [[Reference/Desktop/TypeScript/screens/desks/goal/GoalLayer|src/screens/desks/goal/GoalLayer.tsx]] — import-or-re-export: `ReaderLens`; references `ReaderLens`
- [[Reference/Desktop/TypeScript/screens/desks/goal/marks|src/screens/desks/goal/marks.tsx]] — import-or-re-export: `ReaderLens`; references `ReaderLens`
- [[Reference/Desktop/TypeScript/screens/desks/pen/PenLayer|src/screens/desks/pen/PenLayer.tsx]] — import-or-re-export: `PenSurface`; references `PenSurface`
- [[Reference/Desktop/TypeScript/screens/desks/video/followLens|src/screens/desks/video/followLens.ts]] — import-or-re-export: `ReaderLens`; references `ReaderLens`
- [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] — import-or-re-export: `PenSurface`, `ReaderLens`, `ReaderScreen`, `ReaderWindowing`, `WindowInquiry`; references `PenSurface`, `ReaderLens`, `ReaderScreen`, `ReaderWindowing`, `WindowInquiry`

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
- [[Reference/Desktop/TypeScript/screens/desks/problem/problemPads|src/screens/desks/problem/problemPads.ts]] — import-or-re-export; imports `ProblemHandoff`
- [[Reference/Desktop/TypeScript/screens/reader/ActiveReadingCard|src/screens/reader/ActiveReadingCard.tsx]] — import-or-re-export; imports `ActiveReadingCard`, `NextStepFoldLine`
- [[Reference/Desktop/TypeScript/screens/reader/AlsoInBooks|src/screens/reader/AlsoInBooks.tsx]] — import-or-re-export; imports `ALSO_COPY`, `AlsoInBooks`, `AlsoPeekCrumb`
- [[Reference/Desktop/TypeScript/screens/reader/AskRail|src/screens/reader/AskRail.tsx]] — import-or-re-export; imports `AskRail`
- [[Reference/Desktop/TypeScript/screens/reader/DeliverableSliceCard|src/screens/reader/DeliverableSliceCard.tsx]] — import-or-re-export; imports `GuidePathSlot`
- [[Reference/Desktop/TypeScript/screens/reader/DetourStrip|src/screens/reader/DetourStrip.tsx]] — import-or-re-export; imports `DetourStrip`
- [[Reference/Desktop/TypeScript/screens/reader/DoseOffer|src/screens/reader/DoseOffer.tsx]] — import-or-re-export; imports `DoseOffer`
- [[Reference/Desktop/TypeScript/screens/reader/FindSection|src/screens/reader/FindSection.tsx]] — import-or-re-export; imports `FindSection`
- [[Reference/Desktop/TypeScript/screens/reader/GuideRail|src/screens/reader/GuideRail.tsx]] — import-or-re-export; imports `GuideRail`, `QuickChecks`, `SectionBoundaryOffer`
- [[Reference/Desktop/TypeScript/screens/reader/InquiryQuickCheck|src/screens/reader/InquiryQuickCheck.tsx]] — import-or-re-export; imports `InquiryQuickCheck`
- [[Reference/Desktop/TypeScript/screens/reader/IntentBox|src/screens/reader/IntentBox.tsx]] — import-or-re-export; imports `IntentBox`
- [[Reference/Desktop/TypeScript/screens/reader/KeptMark|src/screens/reader/KeptMark.tsx]] — import-or-re-export; imports `KeptMark`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]] — import-or-re-export; imports `ExplorableOutcome`, `LibraryAnswer`, `LibraryExercisesProps`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryPane|src/screens/reader/LibraryPane.tsx]] — import-or-re-export; imports `LibraryPane`, `useComparingStacked`
- [[Reference/Desktop/TypeScript/screens/reader/MarginMark|src/screens/reader/MarginMark.tsx]] — import-or-re-export; imports `CueFooter`, `CueReceipts`, `MarginMark`
- [[Reference/Desktop/TypeScript/screens/reader/NotesRail|src/screens/reader/NotesRail.tsx]] — import-or-re-export; imports `AnnotationCard`, `AuthoringCard`, `ExerciseImportState`, `NotesRail`
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
- [[Reference/Desktop/TypeScript/screens/reader/sideBySide|src/screens/reader/sideBySide.ts]] — import-or-re-export; imports `PaneTarget`, `clampSplit`, `crumbLabel`, `readSplit`, `sideBySideTarget`, `writeSplit`
- [[Reference/Desktop/TypeScript/screens/reader/useActiveReading|src/screens/reader/useActiveReading.ts]] — import-or-re-export; imports `useActiveReading`
- [[Reference/Desktop/TypeScript/screens/reader/useIntentBox|src/screens/reader/useIntentBox.ts]] — import-or-re-export; imports `IntentCancel`, `IntentRunHandle`, `IntentRunHow`, `useIntentBox`
- [[Reference/Desktop/TypeScript/screens/reader/useKeptComparisons|src/screens/reader/useKeptComparisons.ts]] — import-or-re-export; imports `useKeptComparisons`
- [[Reference/Desktop/TypeScript/screens/reader/useLibraryAsk|src/screens/reader/useLibraryAsk.ts]] — import-or-re-export; imports `CompareRequest`, `SCOPE_COPY`, `useLibraryAsk`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] — import-or-re-export; imports `CueCheckMeRequest`, `CueRequestOrigin`, `useReaderCues`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export; imports `AskAnchor`, `WindowAsk`, `WindowExchange`, `useReaderInquiry`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderRecap|src/screens/reader/useReaderRecap.ts]] — import-or-re-export; imports `useReaderRecap`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderRequests|src/screens/reader/useReaderRequests.ts]] — import-or-re-export; imports `useReaderRequests`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderVisit|src/screens/reader/useReaderVisit.ts]] — import-or-re-export; imports `useReaderVisit`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderWorkbench|src/screens/reader/useReaderWorkbench.ts]] — import-or-re-export; imports `ReaderWorkbenchProps`, `useReaderWorkbench`
- [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]] — import-or-re-export; imports `useReadingProgress`
- [[Reference/Desktop/TypeScript/screens/reader/useSideBySide|src/screens/reader/useSideBySide.ts]] — import-or-re-export; imports `SIDE_BY_SIDE_COPY`, `SIDE_BY_SIDE_SCROLL_KEYS`, `SideBySideVia`, `useSideBySide`
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

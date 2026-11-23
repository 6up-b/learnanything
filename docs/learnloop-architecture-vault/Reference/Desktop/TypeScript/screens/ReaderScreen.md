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
| Source lines | 4903 |
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
- `export interface ReaderCheckMeRequest extends CueCheckMeRequest` — interface, line 292
- `export type ReaderExerciseRequest = ReaderWorkbenchExercise &` — type, line 305
- `export const SIDE_PATH_COPY =` — const, line 309
- `export function ReaderScreen(` — function, line 331

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
- `const mainPaneOwnsCueKey = (event: KeyboardEvent): boolean` — const, line 316
- `interface IntentPane` — interface, line 321
- `const hub = useListenerHub()` — const, line 389
- `const windowPaused = useWindowPaused()` — const, line 391
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 395
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 399
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 408
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 409
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 410
- `const openingRef = useRef<string | null>(null)` — const, line 416
- `const savingHighlightNote = useRef(false)` — const, line 428
- `const askPanelOn = algoConfig().ask !== null` — const, line 442
- `const storedStyle = useStoredHelpStyle()` — const, line 443
- `const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen` — const, line 444
- `const pdfViewRequestRef = useRef(0)` — const, line 466
- `const sourceEpochRef = useRef(0)` — const, line 497
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 508
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 509
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 510
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 511
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 512
- `const modeSaveVersionRef = useRef(0)` — const, line 513
- `const answerModeSaveVersionRef = useRef(0)` — const, line 514
- `const enabled = contract?.readerEnabled ?? true` — const, line 530
- `const inquiry = contract?.inquiryEnabled === true` — const, line 533
- `const muted = inquiry && mode === "skim"` — const, line 536
- `const intentContract = inquiry && !offline ? contract?.intent ?? null : null` — const, line 539
- `const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading)` — const, line 540
- `const openFigureSource = useRef<((extractionId: string, spanId: string)` — const, line 544
- `const figureOpenSource = useCallback((extractionId: string, spanId: string)` — const, line 545
- `const figuresCtl = useFigures(` — const, line 546
- `const figureOffersOn = Boolean(contract?.figures?.offers) && !offline` — const, line 552
- `const showMeOn = Boolean(contract?.figures?.showMe) && !offline` — const, line 556
- `const waitingOfferRef = useRef<OfferedPress | null>(null)` — const, line 562
- `const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome)` — const, line 567
- `const press = offeredFigure` — const, line 574
- `const open = render?.extractionId ?? null` — const, line 576
- `const readerTutor = contract?.readerTutor ?? null` — const, line 599
- `const askWorkbenchSessionRef = useRef<string | null>(null)` — const, line 601
- `const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true` — const, line 606
- `const askPersonalizedRef = useRef<boolean | null>(null)` — const, line 607
- `const askComposerAnchorRef = useRef<AskAnchor | null>(null)` — const, line 612
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 618
- `const renderBlocksBySpan = useMemo( ()` — const, line 622
- `const visit = useReaderVisit(` — const, line 628
- `const showGuideRail = useCallback(()` — const, line 634
- `const progress = useReadingProgress(` — const, line 638
- `const doseVisitId = useCallback(()` — const, line 655
- `const refreshAnnotations = useCallback(async ()` — const, line 657
- `const epoch = sourceEpochRef.current` — const, line 659
- `const result = await cachedSourceRead( render.sourceId, ["reader_source_annotations", render.sourceId, render.extractionId], ()` — const, line 663
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 670
- `const version = (r.version as Record<string, unknown>) ??` — const, line 673
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 674
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 675
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 676
- `const placement = r.placement as ReaderAnnotationPlacementDto | undefined` — const, line 677
- `let page: number | null = null` — let, line 687
- `let bbox: number[] | null = null` — let, line 688
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 690
- `const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?:` — const, line 708
- `const openCardRef = useRef<SourceLibraryCard | null>(null)` — const, line 733
- `const openExtractionRef = useRef<string | null>(null)` — const, line 735
- `const reloadGuidePlan = useCallback(async ()` — const, line 737
- `const extractionId = render.extractionId` — const, line 739
- `const plan = await readGuidePlan(render.sourceId, extractionId,` — const, line 741
- `const spanOrder = useMemo( ()` — const, line 754
- `const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none"` — const, line 758
- `const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 761
- `const card = openCardRef.current` — const, line 762
- `const wbProps = useMemo<ReaderWorkbenchProps | undefined>(()` — const, line 772
- `const submitted = workbench?.onSubmitted` — const, line 773
- `const trail = besideTrail(returnStackRef.current)` — const, line 778
- `const wbCtl = useReaderWorkbench(` — const, line 783
- `const working = wbCtl.active !== null` — const, line 790
- `const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline` — const, line 794
- `const alsoHidden = alsoPrefs ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId)) : Boolean(contract?.correspondence?.hiddenEverywhere) || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.so…` — const, line 799
- `const peekCrumbShown = alsoPeek ?? findPeek` — const, line 809
- `const pathRefreshKey = readingPathRefreshKey(` — const, line 824
- `const tryFirstRef = useRef<((spanId: string)` — const, line 838
- `const cueCtl = useReaderCues(` — const, line 839
- `const recapCtl = useReaderRecap(` — const, line 854
- `const sourceLifecycleState = useWindowLifecycle().state` — const, line 870
- `const railOnScreen = windowed ? Boolean(windowed.railHost) && !isPaused(windowed.railHost?.lifecycle.state ?? "hidden") : !isPaused(sourceLifecycleState)` — const, line 871
- `const recapShown = Boolean(railOnScreen && recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working)` — const, line 874
- `const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip")` — const, line 885
- `const root = history.find((entry)` — const, line 886
- `const recapRevisited = useCallback((rootId: string)` — const, line 899
- `const root = history.find((entry)` — const, line 900
- `const recapRevisit = useCallback(async (rootId: string)` — const, line 903
- `const root = history.find((entry)` — const, line 904
- `const recapOpenInquiry = useCallback((rootId: string, spanId: string)` — const, line 910
- `const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch")` — const, line 913
- `const cueMarksFor = (markSurface: "pdf" | "watch")` — const, line 933
- `let cancelled = false` — let, line 942
- `const scroller = railRef.current` — const, line 975
- `const clamp = ()` — const, line 977
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 978
- `const observer = new ResizeObserver(clamp)` — const, line 981
- `const query = librarySearch.trim()` — const, line 992
- `let cancelled = false` — let, line 999
- `const timer = window.setTimeout(()` — const, line 1002
- `const resetSourceState = useCallback(()` — const, line 1025
- `const openSource = useCallback( async ( card: SourceLibraryCard, jumpSpan?: string, // jumpReading: the reading jumpSpan was found on (a search hit, a // return)` — const, line 1074
- `const handoff = options.handoff ?? null` — const, line 1084
- `const view = options.view ?? await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 1102
- `const pdfRequest = ++pdfViewRequestRef.current` — const, line 1149
- `const current = ()` — const, line 1150
- `const openFixture = useCallback(()` — const, line 1185
- `const backToLibrary = useCallback(()` — const, line 1193
- `const spanId = readingSpan ?? activeSpan` — const, line 1197
- `const section = guidePlan?.sections.find((candidate)` — const, line 1198
- `const resumedRef = useRef(false)` — const, line 1216
- `const trail = initialSource.besideTrail ?? null` — const, line 1220
- `const activeBlock = useMemo(()` — const, line 1234
- `const pdfHighlights: PdfHighlight[] = useMemo(()` — const, line 1243
- `const list: PdfHighlight[] = []` — const, line 1244
- `const base =` — const, line 1247
- `const placed = highlightFromPlacement(base, a.placement)` — const, line 1249
- `const segments = a.segments.flatMap((s)` — const, line 1254
- `const annotatedSpans = useMemo( ()` — const, line 1261
- `const boundaryBlock = useMemo(()` — const, line 1265
- `const revealedPassages = useMemo(()` — const, line 1267
- `const revealed = new Set(revealedSections)` — const, line 1268
- `const map = new Map<string,` — const, line 1269
- `const revealedGuidanceSpans = useMemo(()` — const, line 1278
- `const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null` — const, line 1283
- `const protectedSelection = selectionProtected(protection, selection)` — const, line 1284
- `const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1285
- `const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan))` — const, line 1289
- `const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1290
- `const editCaptureText = useCallback((text: string)` — const, line 1295
- `const resetCaptureText = useCallback(()` — const, line 1298
- `const saveAnnotationEdit = useCallback(async ()` — const, line 1310
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 1332
- `const result = await api.readerReanchor(` — const, line 1336
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1353
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1376
- `const target = annotations.find((a)` — const, line 1377
- `const reading = render ?` — const, line 1378
- `const epoch = sourceEpochRef.current` — const, line 1379
- `const undoRemove = useCallback(async ()` — const, line 1394
- `const last = removed` — const, line 1395
- `const epoch = sourceEpochRef.current` — const, line 1401
- `const result = await api.readerRestoreAnnotation(` — const, line 1403
- `const timer = window.setTimeout(()` — const, line 1416
- `const onKey = (event: KeyboardEvent)` — const, line 1422
- `const target = event.target` — const, line 1425
- `const openAnnotationNote = useCallback((annotationId: string)` — const, line 1433
- `const target = annotations.find((a)` — const, line 1434
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1446
- `const sel = window.getSelection()` — const, line 1447
- `const container = bodyRef.current` — const, line 1448
- `const range = sel.getRangeAt(0)` — const, line 1450
- `const nodes: Array<` — const, line 1451
- `const seen = new Set<string>()` — const, line 1452
- `const spanId = el.dataset.spanId` — const, line 1454
- `let intersects = false` — let, line 1456
- `const sub = document.createRange()` — const, line 1463
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1471
- `const block = renderBlocksBySpan.get(spanId)` — const, line 1476
- `const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1486
- `const cancelIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1487
- `const selectionSpanIds = useMemo( ()` — const, line 1488
- `const intentBox = useIntentBox(` — const, line 1492
- `const openActiveRail = useCallback(()` — const, line 1506
- `const activeCtl = useActiveReading(` — const, line 1510
- `const libraryCtl = useLibraryAsk(` — const, line 1519
- `const keptCtl = useKeptComparisons(` — const, line 1521
- `const notesCtl = useNoteMarks(` — const, line 1523
- `const windowActive = useWindowLifecycle().state === "active"` — const, line 1529
- `const pdfMarks = (): ReadonlyMap<string, ReactNode> | null` — const, line 1538
- `const cues = cueMarksFor("pdf")` — const, line 1539
- `const merged = new Map<string, ReactNode>(cues ?? [])` — const, line 1541
- `const cue = merged.get(spanId)` — const, line 1543
- `const before = merged.get(spanId)` — const, line 1548
- `const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null)` — const, line 1554
- `const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint)` — const, line 1556
- `const sbs = useSideBySide(` — const, line 1558
- `const node = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1566
- `const sbsPanes = sbs.panes && !comparing` — const, line 1579
- `const sbsPanesRef = useRef(false)` — const, line 1580
- `const sbsShownRef = useRef(false)` — const, line 1585
- `const sbsRef = useRef(sbs)` — const, line 1587
- `const sbsEscBusyRef = useRef(false)` — const, line 1590
- `const sbsPaneRef = useRef<HTMLDivElement | null>(null)` — const, line 1592
- `const runSideIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1597
- `const cancelSideIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1598
- `const sbsSection = sbs.section && sbs.target && sbs.section.sectionId === sbs.target.sectionId ? sbs.section : null` — const, line 1599
- `type BesideRun = |` — type, line 1614
- `const besideSeq = useRef(0)` — const, line 1623
- `const besideRunRef = useRef<(run: BesideRun)` — const, line 1626
- `const besideDroppedRef = useRef<(run: BesideRun)` — const, line 1627
- `const openBesideRef = useRef<(hit:` — const, line 1628
- `const snapshotBesideRef = useRef<(spanId: string)` — const, line 1635
- `const shown = sbsRef.current.target` — const, line 1637
- `const takeBesideBook = useCallback((book: SourceIdentity, spanId: string, run: BesideRun)` — const, line 1641
- `const id = ++besideSeq.current` — const, line 1643
- `const sideExtractionRef = useRef<string | null>(null)` — const, line 1655
- `const checkMeFromSideCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 1656
- `const side = useSidePane(` — const, line 1661
- `const besideRanRef = useRef(0)` — const, line 1690
- `const handoff = besideHandoff` — const, line 1692
- `const card = openCardRef.current` — const, line 1707
- `const trail = besideTrail(returnStackRef.current)` — const, line 1709
- `const work = handoff.run` — const, line 1718
- `const openComposer = useCallback((anchor: AskAnchor | null)` — const, line 1732
- `const sbsRowRef = useRef<HTMLDivElement | null>(null)` — const, line 1750
- `const startSbsResize = (event: ReactPointerEvent<HTMLDivElement>)` — const, line 1751
- `const row = sbsRowRef.current` — const, line 1752
- `const rect = row.getBoundingClientRect()` — const, line 1755
- `const move = (moved: PointerEvent)` — const, line 1756
- `const offs: Array<()` — const, line 1759
- `const up = ()` — const, line 1760
- `const touchMain = ()` — const, line 1770
- `const onKey = (event: KeyboardEvent)` — const, line 1779
- `const target = event.target` — const, line 1781
- `const ctl = sbsRef.current` — const, line 1783
- `const open = ctl.panes || ctl.sheet` — const, line 1784
- `const shown = sbsShownRef.current` — const, line 1785
- `const mod = event.ctrlKey || event.metaKey` — const, line 1786
- `const side = sbsPaneRef.current` — const, line 1796
- `const inSide = target instanceof Element && Boolean(target.closest("[data-side-by-side-pane]"))` — const, line 1797
- `const inMain = target instanceof Node && Boolean(bodyRef.current?.contains(target))` — const, line 1803
- `const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false, anchor?: SourceIdentity)` — const, line 1812
- `const identity = anchor ?? identityOf(render)` — const, line 1819
- `const request =` — const, line 1820
- `const closeLibrary = useCallback(()` — const, line 1825
- `const onKey = (event: KeyboardEvent)` — const, line 1832
- `const onMouseUp = useCallback(()` — const, line 1842
- `const sel = window.getSelection()` — const, line 1843
- `const quote = selectionQuote(sel.getRangeAt(0), sel.toString()).replace(/\s+/g, " ").trim()` — const, line 1847
- `const nodes = collectSelectionNodes()` — const, line 1849
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1878
- `const domDragRef = useRef<` — const, line 1879
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1881
- `const host = bodyRef.current` — const, line 1882
- `const rect = host.getBoundingClientRect()` — const, line 1884
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1888
- `const target = event.target as Node` — const, line 1892
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1894
- `const domDrafting = domDraft !== null` — const, line 1906
- `const rectFrom = (drag:` — const, line 1909
- `const onMove = (event: MouseEvent)` — const, line 1915
- `const drag = domDragRef.current` — const, line 1916
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1918
- `const onUp = (event: MouseEvent)` — const, line 1921
- `const drag = domDragRef.current` — const, line 1922
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1926
- `const rect = rectFrom(drag, point)` — const, line 1928
- `const next = [...domBoxesRef.current, rect]` — const, line 1931
- `const offs = [hub.listen("window", "mousemove", onMove), hub.listen("window", "mouseup", onUp)]` — const, line 1937
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1944
- `const host = bodyRef.current` — const, line 1945
- `const hostRect = host.getBoundingClientRect()` — const, line 1947
- `const clientBoxes = boxes.map((b)` — const, line 1948
- `const nodes: Array<` — const, line 1954
- `const seen = new Set<string>()` — const, line 1955
- `const spanId = el.dataset.spanId` — const, line 1957
- `const elRect = el.getBoundingClientRect()` — const, line 1959
- `const touches = clientBoxes.some( (b)` — const, line 1960
- `const words: string[] = []` — const, line 1964
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 1965
- `const text = node as Text` — const, line 1967
- `const wordPattern = /\S+/g` — const, line 1968
- `let match: RegExpExecArray | null` — let, line 1969
- `const range = document.createRange()` — const, line 1971
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 1974
- `const cx = (Math.min(...rects.map((r)` — const, line 1976
- `const cy = (Math.min(...rects.map((r)` — const, line 1977
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 1981
- `const commitDomBoxes = useCallback(()` — const, line 1990
- `const boxes = domBoxesRef.current` — const, line 1991
- `const nodes = resolveDomBoxes(boxes)` — const, line 1993
- `const quote = nodes.map((n)` — const, line 1999
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 2008
- `const clearDomBoxes = ()` — const, line 2016
- `const onKeyDown = (event: KeyboardEvent)` — const, line 2022
- `const onKeyUp = (event: KeyboardEvent)` — const, line 2027
- `const onBlur = ()` — const, line 2033
- `const offs = [ hub.listen("window", "keydown", onKeyDown), hub.listen("window", "keyup", onKeyUp), hub.listen("window", "blur", onBlur), ]` — const, line 2034
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 2053
- `const point = domPointFromClient(request.x, request.y)` — const, line 2055
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 2056
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 2077
- `const retryRequest = useCallback(async (requestId: string)` — const, line 2090
- `const optimisticSegments = useCallback( (nodes: string | Array<string |` — const, line 2104
- `const list = Array.isArray(nodes) ? nodes : [nodes]` — const, line 2106
- `const spanId = typeof node === "string" ? node : node.spanId` — const, line 2108
- `const geometry = pdfView?.blocks.find((b)` — const, line 2109
- `const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number" ?` — const, line 2110
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 2122
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 2126
- `const quotedNodes = (()` — const, line 2131
- `const multi = collectSelectionNodes()` — const, line 2134
- `const optimisticIds = quotedNodes ?? [target.spanId]` — const, line 2137
- `const nodes = quotedNodes ?? [` — const, line 2147
- `const receipt = await api.readerCapture(` — const, line 2148
- `const handler = (event: KeyboardEvent)` — const, line 2175
- `const clearSelection = useCallback(()` — const, line 2186
- `const railHostTab = windowed?.railHost?.tab ?? null` — const, line 2198
- `const windowExtraction = render?.extractionId ?? null` — const, line 2199
- `const onWindowTitle = windowed?.onTitle` — const, line 2204
- `const onWindowStatus = windowed?.onStatus` — const, line 2208
- `const windowWhere = currentGuideSection ? sectionWords(currentGuideSection.label) : null` — const, line 2209
- `const onWindowMediaReady = windowed?.onMediaReady` — const, line 2213
- `const onWindowJumpReady = windowed?.onJumpReady` — const, line 2219
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 2228
- `const segment = a.segments.find((s)` — const, line 2230
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 2237
- `const alsoKeyRef = useRef<()` — const, line 2247
- `const onKey = (event: KeyboardEvent)` — const, line 2255
- `const target = event.target` — const, line 2258
- `const tabs: ReaderRailTab[] = ["guide", "ask", "notes"]` — const, line 2260
- `const askRequestSeen = useRef(askRequest)` — const, line 2297
- `const revealAskRef = useRef<()` — const, line 2299
- `const startCompareRef = useRef<(request: CompareRequest)` — const, line 2324
- `const sideAnchor = Boolean(side.extractionId) && side.extractionId === request.extractionId` — const, line 2327
- `const request = compareWaitsForWork` — const, line 2334
- `const sideMarksChanged = side.marksChanged` — const, line 2344
- `const captureIn = useCallback(async (target: PaneCaptureTarget, what:` — const, line 2345
- `const common =` — const, line 2350
- `const receipt: ReaderPresetReceiptDto = "preset" in what ? await api.readerInvokePreset(` — const, line 2355
- `const drained = await api.readerDrainOutbox()` — const, line 2366
- `const invokePreset = useCallback( // RW1b: the intent box passes its own words as the annotation's learner // text, and names the intention and entry in the funnel event. // Reader CA6b: `target` is side by side's second pane (its book, revision, // reading a…` — const, line 2387
- `const note_ = learnerTextOverride ?? note` — const, line 2395
- `const nodes = selectionNodes(selection)` — const, line 2396
- `const editedText = selection.editedText?.trim()` — const, line 2397
- `const receipt = await api.readerInvokePreset(` — const, line 2409
- `const drained = await api.readerDrainOutbox()` — const, line 2433
- `const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>, target?: PaneCaptureTarget): Promise<string | null>` — const, line 2456
- `const note_ = learnerTextOverride ?? note` — const, line 2460
- `const nodes = selectionNodes(selection)` — const, line 2461
- `const receipt = await api.readerCapture(` — const, line 2474
- `const currentHighlight = selection && selectionHighlight && selectionActions.includes("highlight") && selectionHighlight.spanId === selection.spanId && selectionHighlight.quote === selection.quote ? selectionHighlight : null` — const, line 2504
- `const saveHighlightNote = useCallback(async ()` — const, line 2509
- `const target = currentHighlight` — const, line 2510
- `const words = note.trim()` — const, line 2511
- `const learnerText = target.saved.trim() ? `$` — const, line 2513
- `const typed = note` — const, line 2514
- `const kept = ()` — const, line 2515
- `const annotationId = target.annotationId` — const, line 2526
- `const pauseArc = useCallback(async ()` — const, line 2543
- `const next = await api.readerArc(` — const, line 2547
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 2554
- `const next = await api.readerArc(` — const, line 2559
- `const importJobRef = useRef<` — const, line 2571
- `const importExercise = useCallback(async (target?: PaneCaptureTarget): Promise<string | null>` — const, line 2574
- `const nodes = target ? target.nodes : selectionNodes(selection!)` — const, line 2576
- `const editedText = target ? undefined : selection!.editedText?.trim()` — const, line 2577
- `const receipt = await api.readerImportExercise(target ?` — const, line 2580
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 2628
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 2629
- `const timer = setInterval(async ()` — const, line 2633
- `const status = await api.readerExerciseImportStatus(` — const, line 2635
- `const job = importJobRef.current` — const, line 2636
- `const waited = Date.now() - job.startedAt` — const, line 2639
- `const saveOwnQuestion = useCallback(async ()` — const, line 2666
- `const saved = await api.readerAuthorQA(` — const, line 2674
- `const runCoach = useCallback(async ()` — const, line 2695
- `const lint = await api.readerCoachLint(` — const, line 2698
- `const changeMode = useCallback( async (next: string)` — const, line 2709
- `const previous = mode` — const, line 2711
- `const version = ++modeSaveVersionRef.current` — const, line 2714
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 2725
- `const answerModeNext = next as ReaderAnswerMode` — const, line 2727
- `const previous = answerMode` — const, line 2728
- `const version = ++answerModeSaveVersionRef.current` — const, line 2731
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 2747
- `const renderInquiryTop = useCallback((root: ReaderExchange)` — const, line 2762
- `const line = reconnect && reconnect.rootId === root.id && !muted ? ( <ReconnectLine placement="rail" question=` — const, line 2765
- `const check = inquiryChecks[root.id]` — const, line 2775
- `const inlineReconnect = reconnect && reconnect.inline && !muted ? ( <ReconnectLine placement="inline" question=` — const, line 2803
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 2814
- `const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, pinned?: ReaderRenderViewDto): Promise<OpenOutcome>` — const, line 2833
- `const card = (library ?? []).find((candidate)` — const, line 2838
- `const spanId = readingSpan ?? activeSpan` — const, line 2841
- `const onOriginal = pdfView && surface === "pdf" && !offline` — const, line 2867
- `const epoch = sourceEpochRef.current` — const, line 2880
- `const sameBook = Boolean(render && sourceId === render.sourceId)` — const, line 2883
- `const card = (library ?? []).find((candidate)` — const, line 2884
- `const landed = await api.readerSavedPlace(` — const, line 2889
- `const landing = await api.readerRenderView(` — const, line 2903
- `const openFollowedFigure = (figure: CorrespondentFigureDto, hit: CorrespondentSectionDto)` — const, line 2913
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2915
- `const compareFoundSection = (hit: CorrespondentSectionDto)` — const, line 2930
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2932
- `const hideAlsoInBooks = (scope: "book" | "everywhere")` — const, line 2955
- `const before = alsoPrefs ??` — const, line 2957
- `const base = contract` — const, line 2964
- `const makeExplorable = (target: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, origin: "library" | "tutor", offerRef: string): Promise<ExplorableOutcome>` — const, line 2981
- `let settle: (outcome: ExplorableOutcome)` — let, line 2988
- `const settled = new Promise<ExplorableOutcome>((resolve)` — const, line 2989
- `const press: OfferedPress =` — const, line 2990
- `const peekWorkbenchPassage = (spanId: string, target?: PassageTarget)` — const, line 3009
- `const exerciseSettings = libraryCtl.enabled ? contract?.libraryExercises ?? null : null` — const, line 3020
- `const exerciseCard = (sourceId: string | null)` — const, line 3021
- `const useExercise = (candidate: ExerciseCandidate)` — const, line 3025
- `const card = exerciseCard(candidate.sourceId ?? render?.sourceId ?? null)` — const, line 3026
- `const openExerciseInBook = (candidate: ExerciseCandidate)` — const, line 3035
- `const sourceId = candidate.sourceId ?? render?.sourceId ?? null` — const, line 3036
- `const exerciseProps: LibraryExercisesProps | null = exerciseSettings ?` — const, line 3039
- `const pickLibraryPagePractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3053
- `const hit = libraryCtl.state?.ask.value?.hits[0]` — const, line 3054
- `const card = hit ? (library ?? []).find((candidate)` — const, line 3055
- `const readySources = library ?? []` — const, line 3107
- `const useShelf = Boolean(shelf) && !sidecarDown` — const, line 3109
- `const card = (library ?? []).find((candidate)` — const, line 3167
- `const card = (library ?? []).find((c)` — const, line 3188
- `const receiptId = searchResults.retrievalReceiptId` — const, line 3194
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 3239
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 3240
- `const wbActive = wbCtl.active` — const, line 3283
- `const wbStacked = working && wbCtl.narrow` — const, line 3284
- `const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible)` — const, line 3287
- `const wbSourceShown = !wbStacked || wbCtl.sheetOpen` — const, line 3288
- `const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry)` — const, line 3289
- `const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>()` — const, line 3290
- `const first = entry.spanIds[0]` — const, line 3292
- `const wbLabel = (stem: string)` — const, line 3295
- `const title = problemTitle(stem)` — const, line 3296
- `const tryPathExercise = (exercise: ReadingPathExerciseDto)` — const, line 3301
- `const workThroughSelection = ()` — const, line 3309
- `const nodes = selectionNodes(selection)` — const, line 3311
- `const editedText = selection.editedText?.trim()` — const, line 3312
- `const foldBlocks = contract?.activeReading?.foldBlocks ?? 3` — const, line 3329
- `const localFold = (spanIds: string[]): string[]` — const, line 3330
- `const positions = spanIds.map((spanId)` — const, line 3331
- `const last = Math.max(...positions)` — const, line 3333
- `const mainPane: IntentPane =` — const, line 3342
- `const sidePane: IntentPane | null = side.extractionId ?` — const, line 3351
- `const sideMeta = (pane: IntentPane): Record<string, string>` — const, line 3361
- `const runIntentIn = (pane: IntentPane, action: ReaderIntentActionDto, text: string, how: IntentRunHow): Promise<IntentRunHandle | null> | void` — const, line 3363
- `const meta =` — const, line 3364
- `const effect = action.effect` — const, line 3365
- `const noteText = !action.model && intentContract && onlyNamesAnAction(text, [...intentContract.palette, ...intentContract.notesPalette]) ? "" : text` — const, line 3369
- `const sideSection = pane.side?.section ?? null` — const, line 3371
- `const anchor: AskAnchor =` — const, line 3377
- `const target = pane.side.target` — const, line 3418
- `const target = pane.side.target` — const, line 3424
- `const target = pane.side.target` — const, line 3430
- `const target = pane.side.target` — const, line 3440
- `const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null` — const, line 3485
- `const request: CompareRequest =` — const, line 3486
- `const region = pane.region` — const, line 3518
- `const words = text?.trim()` — const, line 3519
- `const sideShows = (extractionId: string, spanId: string): boolean` — const, line 3540
- `const checkBeside = (book: SourceIdentity, spanId: string, practiceItemId: string, proposalId: string | null)` — const, line 3543
- `const workThroughImported = (item:` — const, line 3548
- `const imported = exerciseImport` — const, line 3549
- `const spanIds = imported?.spanIds ?? (activeSpan ? [activeSpan] : [])` — const, line 3550
- `const settleShowMeLine = (key: string, patch: Partial<ShowMeLine>)` — const, line 3558
- `const requestShowMe = (ctl: FiguresCtl, run: Extract<BesideRun,` — const, line 3561
- `const key = run.lineKey` — const, line 3562
- `const runOnBook = (about: AskAbout, run: Extract<BesideRun,` — const, line 3574
- `const showMeFromAsk = ()` — const, line 3599
- `const goal = question.trim()` — const, line 3600
- `const about = parentExchange ? parentExchange.about ?? null : askComposerAnchor?.about ?? null` — const, line 3601
- `const home = parentExchange?.spanId ?? (about ? askComposerAnchor?.spanId : undefined) ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan` — const, line 3602
- `const key = `show_me:$` — const, line 3605
- `const run =` — const, line 3608
- `const cancelIntentIn = (pane: IntentPane, cancel: IntentCancel)` — const, line 3617
- `const kind = cancel.action.effect.kind` — const, line 3618
- `const annotationId = handle.annotationId` — const, line 3625
- `const batchId = handle.importBatchId` — const, line 3642
- `const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number)` — const, line 3656
- `const spanId = wbCtl.close(session,` — const, line 3658
- `const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3664
- `const card = openCardRef.current` — const, line 3665
- `const asked = libraryCtl.state?.request` — const, line 3669
- `const resumeMark = (spanId: string | null | undefined)` — const, line 3677
- `const entry = spanId ? wbResumeBySpan.get(spanId) : undefined` — const, line 3678
- `const verb = entry.status === "abandoned" ? "Reopen" : "Resume"` — const, line 3680
- `const placeRail = (rail: ReactNode): ReactNode` — const, line 3699
- `const host = windowed.railHost` — const, line 3701
- `const overDesk = (menu: ReactNode): ReactNode` — const, line 3710
- `const target = event.target` — const, line 3846
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 4021
- `const active = activeSpan === block.spanId` — const, line 4022
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 4023
- `const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null` — const, line 4024
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 4025
- `const endQuestionAvailable = Boolean(endSection && endSection.question?.readingPhase === "after_section" && offeredCheckSections.has(endSection.id))` — const, line 4027
- `const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId))` — const, line 4031
- `const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""))` — const, line 4032
- `const offerSection = endSection && !muted && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 4033
- `const sel = window.getSelection()` — const, line 4052
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 4053
- `const cue = side.cues.markOn(spanId)` — const, line 4143
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 4171
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 4194
- `const active = railTab === tab` — const, line 4309
- `const waiting = tab === "guide" && pendingQuickCheckCount > 0` — const, line 4313
- `const marked = tab === "ask" && askTabMarked && !active` — const, line 4314
- `const params = (action.params ??` — const, line 4465
- `const run =` — const, line 4739
- `const book = exchange?.about ?? render` — const, line 4748

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`; references `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`
- [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] — import-or-re-export: `ReaderScreen`, `ReaderWindowing`; references `ReaderScreen`, `ReaderWindowing`

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

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
| Source lines | 4710 |
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

- `export interface ReaderOpenSource` — interface, line 240
- `export interface ReaderCheckMeRequest extends CueCheckMeRequest` — interface, line 256
- `export type ReaderExerciseRequest = ReaderWorkbenchExercise &` — type, line 269
- `export const SIDE_PATH_COPY =` — const, line 273
- `export function ReaderScreen(` — function, line 295

## Internal implementation anchors

- `type AnnotationSegment, type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 145
- `type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 146
- `type ReaderSelection, } from "./reader/readerShared"` — type, line 147
- `const NO_SECTIONS: never[] = []` — const, line 151
- `const READER_MODE_OPTIONS = [` — const, line 152
- `const TAG_ACTIONS: Array<` — const, line 162
- `const WHOLE_BLOCK_QUOTE = "(whole block)"` — const, line 170
- `type ReaderRailTab = "guide" | "ask" | "notes"` — type, line 172
- `const HEALTH_COLOR: Record<string, "green" | "amber" | "pink" | "slate"> =` — const, line 174
- `const FIGURE_PAGE_NOT_OPENED = "That page couldn't be opened."` — const, line 182
- `type OpenOutcome = "opened" | "preparing" | "not_opened"` — type, line 185
- `interface OfferedPress` — interface, line 189
- `const OFFER_OUTCOME: Record<FigureRequestOutcome, ExplorableOutcome> =` — const, line 200
- `const BADGED_HEALTH = new Set(["suspect", "failed"])` — const, line 206
- `interface RemovedAnnotation` — interface, line 210
- `const UNDO_REMOVE_MS = 10_000` — const, line 220
- `function newKey(): string` — function, line 222
- `function identityOf(view: Pick<ReaderRenderViewDto, "sourceId" | "revisionId" | "extractionId">): SourceIdentity` — function, line 231
- `function sectionIdentity(section:` — function, line 236
- `const mainPaneOwnsCueKey = (event: KeyboardEvent): boolean` — const, line 280
- `interface IntentPane` — interface, line 285
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 345
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 349
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 358
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 359
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 360
- `const openingRef = useRef<string | null>(null)` — const, line 366
- `const askPanelOn = algoConfig().ask !== null` — const, line 387
- `const storedStyle = useStoredHelpStyle()` — const, line 388
- `const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen` — const, line 389
- `const pdfViewRequestRef = useRef(0)` — const, line 411
- `const sourceEpochRef = useRef(0)` — const, line 442
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 453
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 454
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 455
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 456
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 457
- `const modeSaveVersionRef = useRef(0)` — const, line 458
- `const answerModeSaveVersionRef = useRef(0)` — const, line 459
- `const enabled = contract?.readerEnabled ?? true` — const, line 475
- `const inquiry = contract?.inquiryEnabled === true` — const, line 478
- `const muted = inquiry && mode === "skim"` — const, line 481
- `const intentContract = inquiry && !offline ? contract?.intent ?? null : null` — const, line 484
- `const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading)` — const, line 485
- `const openFigureSource = useRef<((extractionId: string, spanId: string)` — const, line 489
- `const figureOpenSource = useCallback((extractionId: string, spanId: string)` — const, line 490
- `const figuresCtl = useFigures(` — const, line 491
- `const figureOffersOn = Boolean(contract?.figures?.offers) && !offline` — const, line 497
- `const showMeOn = Boolean(contract?.figures?.showMe) && !offline` — const, line 501
- `const waitingOfferRef = useRef<OfferedPress | null>(null)` — const, line 507
- `const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome)` — const, line 512
- `const press = offeredFigure` — const, line 519
- `const open = render?.extractionId ?? null` — const, line 521
- `const readerTutor = contract?.readerTutor ?? null` — const, line 544
- `const askWorkbenchSessionRef = useRef<string | null>(null)` — const, line 546
- `const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true` — const, line 551
- `const askPersonalizedRef = useRef<boolean | null>(null)` — const, line 552
- `const askComposerAnchorRef = useRef<AskAnchor | null>(null)` — const, line 557
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 563
- `const renderBlocksBySpan = useMemo( ()` — const, line 567
- `const visit = useReaderVisit(` — const, line 573
- `const showGuideRail = useCallback(()` — const, line 579
- `const progress = useReadingProgress(` — const, line 583
- `const doseVisitId = useCallback(()` — const, line 600
- `const refreshAnnotations = useCallback(async ()` — const, line 602
- `const epoch = sourceEpochRef.current` — const, line 604
- `const result = await cachedSourceRead( render.sourceId, ["reader_source_annotations", render.sourceId, render.extractionId], ()` — const, line 608
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 615
- `const version = (r.version as Record<string, unknown>) ??` — const, line 618
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 619
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 620
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 621
- `const placement = r.placement as ReaderAnnotationPlacementDto | undefined` — const, line 622
- `let page: number | null = null` — let, line 632
- `let bbox: number[] | null = null` — let, line 633
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 635
- `const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?:` — const, line 653
- `const openCardRef = useRef<SourceLibraryCard | null>(null)` — const, line 678
- `const openExtractionRef = useRef<string | null>(null)` — const, line 680
- `const reloadGuidePlan = useCallback(async ()` — const, line 682
- `const extractionId = render.extractionId` — const, line 684
- `const plan = await readGuidePlan(render.sourceId, extractionId,` — const, line 686
- `const spanOrder = useMemo( ()` — const, line 699
- `const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none"` — const, line 703
- `const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 706
- `const card = openCardRef.current` — const, line 707
- `const wbProps = useMemo<ReaderWorkbenchProps | undefined>(()` — const, line 717
- `const submitted = workbench?.onSubmitted` — const, line 718
- `const trail = besideTrail(returnStackRef.current)` — const, line 723
- `const wbCtl = useReaderWorkbench(` — const, line 728
- `const working = wbCtl.active !== null` — const, line 735
- `const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline` — const, line 739
- `const alsoHidden = alsoPrefs ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId)) : Boolean(contract?.correspondence?.hiddenEverywhere) || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.so…` — const, line 744
- `const peekCrumbShown = alsoPeek ?? findPeek` — const, line 754
- `const pathRefreshKey = readingPathRefreshKey(` — const, line 769
- `const tryFirstRef = useRef<((spanId: string)` — const, line 783
- `const cueCtl = useReaderCues(` — const, line 784
- `const recapCtl = useReaderRecap(` — const, line 799
- `const recapShown = Boolean(recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working)` — const, line 813
- `const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip")` — const, line 824
- `const root = history.find((entry)` — const, line 825
- `const recapRevisited = useCallback((rootId: string)` — const, line 838
- `const root = history.find((entry)` — const, line 839
- `const recapRevisit = useCallback(async (rootId: string)` — const, line 842
- `const root = history.find((entry)` — const, line 843
- `const recapOpenInquiry = useCallback((rootId: string, spanId: string)` — const, line 849
- `const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch")` — const, line 852
- `const cueMarksFor = (markSurface: "pdf" | "watch")` — const, line 872
- `let cancelled = false` — let, line 881
- `const scroller = railRef.current` — const, line 914
- `const clamp = ()` — const, line 916
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 917
- `const observer = new ResizeObserver(clamp)` — const, line 920
- `const query = librarySearch.trim()` — const, line 931
- `let cancelled = false` — let, line 938
- `const timer = window.setTimeout(()` — const, line 941
- `const resetSourceState = useCallback(()` — const, line 964
- `const openSource = useCallback( async ( card: SourceLibraryCard, jumpSpan?: string, // jumpReading: the reading jumpSpan was found on (a search hit, a // return)` — const, line 1013
- `const handoff = options.handoff ?? null` — const, line 1023
- `const view = options.view ?? await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 1041
- `const pdfRequest = ++pdfViewRequestRef.current` — const, line 1088
- `const current = ()` — const, line 1089
- `const openFixture = useCallback(()` — const, line 1124
- `const backToLibrary = useCallback(()` — const, line 1132
- `const spanId = readingSpan ?? activeSpan` — const, line 1136
- `const section = guidePlan?.sections.find((candidate)` — const, line 1137
- `const resumedRef = useRef(false)` — const, line 1155
- `const trail = initialSource.besideTrail ?? null` — const, line 1159
- `const activeBlock = useMemo(()` — const, line 1173
- `const pdfHighlights: PdfHighlight[] = useMemo(()` — const, line 1182
- `const list: PdfHighlight[] = []` — const, line 1183
- `const base =` — const, line 1186
- `const placed = highlightFromPlacement(base, a.placement)` — const, line 1188
- `const segments = a.segments.flatMap((s)` — const, line 1193
- `const annotatedSpans = useMemo( ()` — const, line 1200
- `const boundaryBlock = useMemo(()` — const, line 1204
- `const revealedPassages = useMemo(()` — const, line 1206
- `const revealed = new Set(revealedSections)` — const, line 1207
- `const map = new Map<string,` — const, line 1208
- `const revealedGuidanceSpans = useMemo(()` — const, line 1217
- `const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null` — const, line 1222
- `const protectedSelection = selectionProtected(protection, selection)` — const, line 1223
- `const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1224
- `const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan))` — const, line 1228
- `const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1229
- `const editCaptureText = useCallback((text: string)` — const, line 1234
- `const resetCaptureText = useCallback(()` — const, line 1237
- `const saveAnnotationEdit = useCallback(async ()` — const, line 1249
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 1271
- `const result = await api.readerReanchor(` — const, line 1275
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1292
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1315
- `const target = annotations.find((a)` — const, line 1316
- `const reading = render ?` — const, line 1317
- `const epoch = sourceEpochRef.current` — const, line 1318
- `const undoRemove = useCallback(async ()` — const, line 1333
- `const last = removed` — const, line 1334
- `const epoch = sourceEpochRef.current` — const, line 1340
- `const result = await api.readerRestoreAnnotation(` — const, line 1342
- `const timer = window.setTimeout(()` — const, line 1355
- `const onKey = (event: KeyboardEvent)` — const, line 1361
- `const target = event.target` — const, line 1364
- `const openAnnotationNote = useCallback((annotationId: string)` — const, line 1373
- `const target = annotations.find((a)` — const, line 1374
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1386
- `const sel = window.getSelection()` — const, line 1387
- `const container = bodyRef.current` — const, line 1388
- `const range = sel.getRangeAt(0)` — const, line 1390
- `const nodes: Array<` — const, line 1391
- `const seen = new Set<string>()` — const, line 1392
- `const spanId = el.dataset.spanId` — const, line 1394
- `let intersects = false` — let, line 1396
- `const sub = document.createRange()` — const, line 1403
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1411
- `const block = renderBlocksBySpan.get(spanId)` — const, line 1416
- `const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1426
- `const cancelIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1427
- `const selectionSpanIds = useMemo( ()` — const, line 1428
- `const intentBox = useIntentBox(` — const, line 1432
- `const openActiveRail = useCallback(()` — const, line 1446
- `const activeCtl = useActiveReading(` — const, line 1450
- `const libraryCtl = useLibraryAsk(` — const, line 1459
- `const keptCtl = useKeptComparisons(` — const, line 1461
- `const notesCtl = useNoteMarks(` — const, line 1463
- `const pdfMarks = (): ReadonlyMap<string, ReactNode> | null` — const, line 1468
- `const cues = cueMarksFor("pdf")` — const, line 1469
- `const merged = new Map<string, ReactNode>(cues ?? [])` — const, line 1471
- `const cue = merged.get(spanId)` — const, line 1473
- `const before = merged.get(spanId)` — const, line 1478
- `const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null)` — const, line 1484
- `const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint)` — const, line 1486
- `const sbs = useSideBySide(` — const, line 1488
- `const node = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1496
- `const sbsPanes = sbs.panes && !comparing` — const, line 1509
- `const sbsPanesRef = useRef(false)` — const, line 1510
- `const sbsShownRef = useRef(false)` — const, line 1515
- `const sbsRef = useRef(sbs)` — const, line 1517
- `const sbsEscBusyRef = useRef(false)` — const, line 1520
- `const sbsPaneRef = useRef<HTMLDivElement | null>(null)` — const, line 1522
- `const runSideIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1527
- `const cancelSideIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1528
- `const sbsSection = sbs.section && sbs.target && sbs.section.sectionId === sbs.target.sectionId ? sbs.section : null` — const, line 1529
- `type BesideRun = |` — type, line 1544
- `const besideSeq = useRef(0)` — const, line 1553
- `const besideRunRef = useRef<(run: BesideRun)` — const, line 1556
- `const besideDroppedRef = useRef<(run: BesideRun)` — const, line 1557
- `const openBesideRef = useRef<(hit:` — const, line 1558
- `const snapshotBesideRef = useRef<(spanId: string)` — const, line 1565
- `const shown = sbsRef.current.target` — const, line 1567
- `const takeBesideBook = useCallback((book: SourceIdentity, spanId: string, run: BesideRun)` — const, line 1571
- `const id = ++besideSeq.current` — const, line 1573
- `const sideExtractionRef = useRef<string | null>(null)` — const, line 1585
- `const checkMeFromSideCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 1586
- `const side = useSidePane(` — const, line 1591
- `const besideRanRef = useRef(0)` — const, line 1620
- `const handoff = besideHandoff` — const, line 1622
- `const card = openCardRef.current` — const, line 1637
- `const trail = besideTrail(returnStackRef.current)` — const, line 1639
- `const work = handoff.run` — const, line 1648
- `const openComposer = useCallback((anchor: AskAnchor | null)` — const, line 1662
- `const sbsRowRef = useRef<HTMLDivElement | null>(null)` — const, line 1680
- `const startSbsResize = (event: ReactPointerEvent<HTMLDivElement>)` — const, line 1681
- `const row = sbsRowRef.current` — const, line 1682
- `const rect = row.getBoundingClientRect()` — const, line 1685
- `const move = (moved: PointerEvent)` — const, line 1686
- `const up = ()` — const, line 1689
- `const touchMain = ()` — const, line 1701
- `const onKey = (event: KeyboardEvent)` — const, line 1710
- `const target = event.target` — const, line 1712
- `const ctl = sbsRef.current` — const, line 1714
- `const open = ctl.panes || ctl.sheet` — const, line 1715
- `const shown = sbsShownRef.current` — const, line 1716
- `const mod = event.ctrlKey || event.metaKey` — const, line 1717
- `const side = sbsPaneRef.current` — const, line 1727
- `const inSide = target instanceof Element && Boolean(target.closest("[data-side-by-side-pane]"))` — const, line 1728
- `const inMain = target instanceof Node && Boolean(bodyRef.current?.contains(target))` — const, line 1734
- `const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false, anchor?: SourceIdentity)` — const, line 1744
- `const identity = anchor ?? identityOf(render)` — const, line 1751
- `const request =` — const, line 1752
- `const closeLibrary = useCallback(()` — const, line 1757
- `const onKey = (event: KeyboardEvent)` — const, line 1764
- `const onMouseUp = useCallback(()` — const, line 1775
- `const sel = window.getSelection()` — const, line 1776
- `const quote = selectionQuote(sel.getRangeAt(0), sel.toString()).replace(/\s+/g, " ").trim()` — const, line 1780
- `const nodes = collectSelectionNodes()` — const, line 1782
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1811
- `const domDragRef = useRef<` — const, line 1812
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1814
- `const host = bodyRef.current` — const, line 1815
- `const rect = host.getBoundingClientRect()` — const, line 1817
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1821
- `const target = event.target as Node` — const, line 1825
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1827
- `const domDrafting = domDraft !== null` — const, line 1839
- `const rectFrom = (drag:` — const, line 1842
- `const onMove = (event: MouseEvent)` — const, line 1848
- `const drag = domDragRef.current` — const, line 1849
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1851
- `const onUp = (event: MouseEvent)` — const, line 1854
- `const drag = domDragRef.current` — const, line 1855
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1859
- `const rect = rectFrom(drag, point)` — const, line 1861
- `const next = [...domBoxesRef.current, rect]` — const, line 1864
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1881
- `const host = bodyRef.current` — const, line 1882
- `const hostRect = host.getBoundingClientRect()` — const, line 1884
- `const clientBoxes = boxes.map((b)` — const, line 1885
- `const nodes: Array<` — const, line 1891
- `const seen = new Set<string>()` — const, line 1892
- `const spanId = el.dataset.spanId` — const, line 1894
- `const elRect = el.getBoundingClientRect()` — const, line 1896
- `const touches = clientBoxes.some( (b)` — const, line 1897
- `const words: string[] = []` — const, line 1901
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 1902
- `const text = node as Text` — const, line 1904
- `const wordPattern = /\S+/g` — const, line 1905
- `let match: RegExpExecArray | null` — let, line 1906
- `const range = document.createRange()` — const, line 1908
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 1911
- `const cx = (Math.min(...rects.map((r)` — const, line 1913
- `const cy = (Math.min(...rects.map((r)` — const, line 1914
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 1918
- `const commitDomBoxes = useCallback(()` — const, line 1927
- `const boxes = domBoxesRef.current` — const, line 1928
- `const nodes = resolveDomBoxes(boxes)` — const, line 1930
- `const quote = nodes.map((n)` — const, line 1936
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 1945
- `const clearDomBoxes = ()` — const, line 1953
- `const onKeyDown = (event: KeyboardEvent)` — const, line 1959
- `const onKeyUp = (event: KeyboardEvent)` — const, line 1964
- `const onBlur = ()` — const, line 1970
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 1992
- `const point = domPointFromClient(request.x, request.y)` — const, line 1994
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 1995
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 2016
- `const retryRequest = useCallback(async (requestId: string)` — const, line 2029
- `const optimisticSegments = useCallback( (nodes: string | Array<string |` — const, line 2043
- `const list = Array.isArray(nodes) ? nodes : [nodes]` — const, line 2045
- `const spanId = typeof node === "string" ? node : node.spanId` — const, line 2047
- `const geometry = pdfView?.blocks.find((b)` — const, line 2048
- `const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number" ?` — const, line 2049
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 2061
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 2065
- `const quotedNodes = (()` — const, line 2070
- `const multi = collectSelectionNodes()` — const, line 2073
- `const optimisticIds = quotedNodes ?? [target.spanId]` — const, line 2076
- `const nodes = quotedNodes ?? [` — const, line 2086
- `const receipt = await api.readerCapture(` — const, line 2087
- `const handler = (event: KeyboardEvent)` — const, line 2114
- `const clearSelection = useCallback(()` — const, line 2126
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 2138
- `const segment = a.segments.find((s)` — const, line 2140
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 2147
- `const alsoKeyRef = useRef<()` — const, line 2157
- `const onKey = (event: KeyboardEvent)` — const, line 2165
- `const target = event.target` — const, line 2168
- `const tabs: ReaderRailTab[] = ["guide", "ask", "notes"]` — const, line 2170
- `const askRequestSeen = useRef(askRequest)` — const, line 2208
- `const revealAskRef = useRef<()` — const, line 2210
- `const startCompareRef = useRef<(request: CompareRequest)` — const, line 2235
- `const sideAnchor = Boolean(side.extractionId) && side.extractionId === request.extractionId` — const, line 2238
- `const request = compareWaitsForWork` — const, line 2245
- `const sideMarksChanged = side.marksChanged` — const, line 2255
- `const captureIn = useCallback(async (target: PaneCaptureTarget, what:` — const, line 2256
- `const common =` — const, line 2261
- `const receipt: ReaderPresetReceiptDto = "preset" in what ? await api.readerInvokePreset(` — const, line 2266
- `const drained = await api.readerDrainOutbox()` — const, line 2277
- `const invokePreset = useCallback( // RW1b: the intent box passes its own words as the annotation's learner // text, and names the intention and entry in the funnel event. // Reader CA6b: `target` is side by side's second pane (its book, revision, // reading a…` — const, line 2298
- `const note_ = learnerTextOverride ?? note` — const, line 2306
- `const nodes = selectionNodes(selection)` — const, line 2307
- `const editedText = selection.editedText?.trim()` — const, line 2308
- `const receipt = await api.readerInvokePreset(` — const, line 2320
- `const drained = await api.readerDrainOutbox()` — const, line 2344
- `const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>, target?: PaneCaptureTarget): Promise<string | null>` — const, line 2367
- `const note_ = learnerTextOverride ?? note` — const, line 2371
- `const nodes = selectionNodes(selection)` — const, line 2372
- `const receipt = await api.readerCapture(` — const, line 2384
- `const pauseArc = useCallback(async ()` — const, line 2412
- `const next = await api.readerArc(` — const, line 2416
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 2423
- `const next = await api.readerArc(` — const, line 2428
- `const importJobRef = useRef<` — const, line 2440
- `const importExercise = useCallback(async (target?: PaneCaptureTarget): Promise<string | null>` — const, line 2443
- `const nodes = target ? target.nodes : selectionNodes(selection!)` — const, line 2445
- `const editedText = target ? undefined : selection!.editedText?.trim()` — const, line 2446
- `const receipt = await api.readerImportExercise(target ?` — const, line 2449
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 2497
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 2498
- `const timer = setInterval(async ()` — const, line 2502
- `const status = await api.readerExerciseImportStatus(` — const, line 2504
- `const job = importJobRef.current` — const, line 2505
- `const waited = Date.now() - job.startedAt` — const, line 2508
- `const saveOwnQuestion = useCallback(async ()` — const, line 2535
- `const saved = await api.readerAuthorQA(` — const, line 2543
- `const runCoach = useCallback(async ()` — const, line 2564
- `const lint = await api.readerCoachLint(` — const, line 2567
- `const changeMode = useCallback( async (next: string)` — const, line 2578
- `const previous = mode` — const, line 2580
- `const version = ++modeSaveVersionRef.current` — const, line 2583
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 2594
- `const answerModeNext = next as ReaderAnswerMode` — const, line 2596
- `const previous = answerMode` — const, line 2597
- `const version = ++answerModeSaveVersionRef.current` — const, line 2600
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 2616
- `const renderInquiryTop = useCallback((root: ReaderExchange)` — const, line 2631
- `const line = reconnect && reconnect.rootId === root.id && !muted ? ( <ReconnectLine placement="rail" question=` — const, line 2634
- `const check = inquiryChecks[root.id]` — const, line 2644
- `const inlineReconnect = reconnect && reconnect.inline && !muted ? ( <ReconnectLine placement="inline" question=` — const, line 2672
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 2683
- `const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, pinned?: ReaderRenderViewDto): Promise<OpenOutcome>` — const, line 2702
- `const card = (library ?? []).find((candidate)` — const, line 2707
- `const spanId = readingSpan ?? activeSpan` — const, line 2710
- `const onOriginal = pdfView && surface === "pdf" && !offline` — const, line 2736
- `const epoch = sourceEpochRef.current` — const, line 2749
- `const sameBook = Boolean(render && sourceId === render.sourceId)` — const, line 2752
- `const card = (library ?? []).find((candidate)` — const, line 2753
- `const landed = await api.readerSavedPlace(` — const, line 2758
- `const landing = await api.readerRenderView(` — const, line 2772
- `const openFollowedFigure = (figure: CorrespondentFigureDto, hit: CorrespondentSectionDto)` — const, line 2782
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2784
- `const compareFoundSection = (hit: CorrespondentSectionDto)` — const, line 2799
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2801
- `const hideAlsoInBooks = (scope: "book" | "everywhere")` — const, line 2824
- `const before = alsoPrefs ??` — const, line 2826
- `const base = contract` — const, line 2833
- `const makeExplorable = (target: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, origin: "library" | "tutor", offerRef: string): Promise<ExplorableOutcome>` — const, line 2850
- `let settle: (outcome: ExplorableOutcome)` — let, line 2857
- `const settled = new Promise<ExplorableOutcome>((resolve)` — const, line 2858
- `const press: OfferedPress =` — const, line 2859
- `const peekWorkbenchPassage = (spanId: string, target?: PassageTarget)` — const, line 2878
- `const exerciseSettings = libraryCtl.enabled ? contract?.libraryExercises ?? null : null` — const, line 2889
- `const exerciseCard = (sourceId: string | null)` — const, line 2890
- `const useExercise = (candidate: ExerciseCandidate)` — const, line 2894
- `const card = exerciseCard(candidate.sourceId ?? render?.sourceId ?? null)` — const, line 2895
- `const openExerciseInBook = (candidate: ExerciseCandidate)` — const, line 2904
- `const sourceId = candidate.sourceId ?? render?.sourceId ?? null` — const, line 2905
- `const exerciseProps: LibraryExercisesProps | null = exerciseSettings ?` — const, line 2908
- `const pickLibraryPagePractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 2922
- `const hit = libraryCtl.state?.ask.value?.hits[0]` — const, line 2923
- `const card = hit ? (library ?? []).find((candidate)` — const, line 2924
- `const readySources = library ?? []` — const, line 2967
- `const useShelf = Boolean(shelf) && !sidecarDown` — const, line 2969
- `const card = (library ?? []).find((candidate)` — const, line 3027
- `const card = (library ?? []).find((c)` — const, line 3048
- `const receiptId = searchResults.retrievalReceiptId` — const, line 3054
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 3099
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 3100
- `const wbActive = wbCtl.active` — const, line 3143
- `const wbStacked = working && wbCtl.narrow` — const, line 3144
- `const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible)` — const, line 3147
- `const wbSourceShown = !wbStacked || wbCtl.sheetOpen` — const, line 3148
- `const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry)` — const, line 3149
- `const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>()` — const, line 3150
- `const first = entry.spanIds[0]` — const, line 3152
- `const wbLabel = (stem: string)` — const, line 3155
- `const title = problemTitle(stem)` — const, line 3156
- `const tryPathExercise = (exercise: ReadingPathExerciseDto)` — const, line 3161
- `const workThroughSelection = ()` — const, line 3169
- `const nodes = selectionNodes(selection)` — const, line 3171
- `const editedText = selection.editedText?.trim()` — const, line 3172
- `const foldBlocks = contract?.activeReading?.foldBlocks ?? 3` — const, line 3189
- `const localFold = (spanIds: string[]): string[]` — const, line 3190
- `const positions = spanIds.map((spanId)` — const, line 3191
- `const last = Math.max(...positions)` — const, line 3193
- `const mainPane: IntentPane =` — const, line 3202
- `const sidePane: IntentPane | null = side.extractionId ?` — const, line 3211
- `const sideMeta = (pane: IntentPane): Record<string, string>` — const, line 3221
- `const runIntentIn = (pane: IntentPane, action: ReaderIntentActionDto, text: string, how: IntentRunHow): Promise<IntentRunHandle | null> | void` — const, line 3223
- `const meta =` — const, line 3224
- `const effect = action.effect` — const, line 3225
- `const sideSection = pane.side?.section ?? null` — const, line 3226
- `const anchor: AskAnchor =` — const, line 3232
- `const target = pane.side.target` — const, line 3273
- `const target = pane.side.target` — const, line 3279
- `const target = pane.side.target` — const, line 3285
- `const target = pane.side.target` — const, line 3295
- `const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null` — const, line 3340
- `const request: CompareRequest =` — const, line 3341
- `const region = pane.region` — const, line 3373
- `const words = text?.trim()` — const, line 3374
- `const sideShows = (extractionId: string, spanId: string): boolean` — const, line 3395
- `const checkBeside = (book: SourceIdentity, spanId: string, practiceItemId: string, proposalId: string | null)` — const, line 3398
- `const workThroughImported = (item:` — const, line 3403
- `const imported = exerciseImport` — const, line 3404
- `const spanIds = imported?.spanIds ?? (activeSpan ? [activeSpan] : [])` — const, line 3405
- `const settleShowMeLine = (key: string, patch: Partial<ShowMeLine>)` — const, line 3413
- `const requestShowMe = (ctl: FiguresCtl, run: Extract<BesideRun,` — const, line 3416
- `const key = run.lineKey` — const, line 3417
- `const runOnBook = (about: AskAbout, run: Extract<BesideRun,` — const, line 3429
- `const showMeFromAsk = ()` — const, line 3454
- `const goal = question.trim()` — const, line 3455
- `const about = parentExchange ? parentExchange.about ?? null : askComposerAnchor?.about ?? null` — const, line 3456
- `const home = parentExchange?.spanId ?? (about ? askComposerAnchor?.spanId : undefined) ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan` — const, line 3457
- `const key = `show_me:$` — const, line 3460
- `const run =` — const, line 3463
- `const cancelIntentIn = (pane: IntentPane, cancel: IntentCancel)` — const, line 3472
- `const kind = cancel.action.effect.kind` — const, line 3473
- `const annotationId = handle.annotationId` — const, line 3480
- `const batchId = handle.importBatchId` — const, line 3497
- `const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number)` — const, line 3511
- `const spanId = wbCtl.close(session,` — const, line 3513
- `const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3519
- `const card = openCardRef.current` — const, line 3520
- `const asked = libraryCtl.state?.request` — const, line 3524
- `const resumeMark = (spanId: string | null | undefined)` — const, line 3532
- `const entry = spanId ? wbResumeBySpan.get(spanId) : undefined` — const, line 3533
- `const verb = entry.status === "abandoned" ? "Reopen" : "Resume"` — const, line 3535
- `const target = event.target` — const, line 3662
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 3837
- `const active = activeSpan === block.spanId` — const, line 3838
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 3839
- `const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null` — const, line 3840
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 3841
- `const endQuestionAvailable = Boolean(endSection && endSection.question?.readingPhase === "after_section" && offeredCheckSections.has(endSection.id))` — const, line 3843
- `const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId))` — const, line 3847
- `const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""))` — const, line 3848
- `const offerSection = endSection && !muted && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 3849
- `const sel = window.getSelection()` — const, line 3868
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 3869
- `const cue = side.cues.markOn(spanId)` — const, line 3959
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 3987
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 4010
- `const active = railTab === tab` — const, line 4123
- `const waiting = tab === "guide" && pendingQuickCheckCount > 0` — const, line 4127
- `const marked = tab === "ask" && askTabMarked && !active` — const, line 4128
- `const params = (action.params ??` — const, line 4275
- `const run =` — const, line 4547
- `const book = exchange?.about ?? render` — const, line 4556

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
- [[Reference/Desktop/TypeScript/components/scrollWithin|src/components/scrollWithin.ts]] — import-or-re-export; imports `scrollIntoViewWithin`
- [[Reference/Desktop/TypeScript/components/sourceTail|src/components/sourceTail.ts]] — import-or-re-export; imports `youtubeVideoId`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `TermSelect`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `SPAN_MISMATCH_COPY`, `errorMessage`
- [[Reference/Desktop/TypeScript/fixtures/readerRenderView|src/fixtures/readerRenderView.ts]] — import-or-re-export; imports `readerRenderViewFixture`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/render/mathMacros|src/render/mathMacros.tsx]] — import-or-re-export; imports `MathMacrosProvider`
- [[Reference/Desktop/TypeScript/render/mathSnippet|src/render/mathSnippet.ts]] — import-or-re-export; imports `selectionQuote`
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

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
source_commit: "2bac2d18efb2dbf7ca9e3f0474532abf324ca58a"
source_commit_timestamp: "2026-11-01T19:16:35-05:00"
source_worktree_state: "clean"
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
| Source lines | 4606 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `2bac2d18efb2dbf7ca9e3f0474532abf324ca58a` |
| Commit timestamp | `2026-11-01T19:16:35-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]]

## Public API

- `export interface ReaderOpenSource` — interface, line 235
- `export interface ReaderCheckMeRequest extends CueCheckMeRequest` — interface, line 251
- `export type ReaderExerciseRequest = ReaderWorkbenchExercise &` — type, line 264
- `export const SIDE_PATH_COPY =` — const, line 268
- `export function ReaderScreen(` — function, line 290

## Internal implementation anchors

- `type AnnotationSegment, type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 139
- `type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 140
- `type ReaderSelection, } from "./reader/readerShared"` — type, line 141
- `const NO_SECTIONS: never[] = []` — const, line 145
- `const READER_MODE_OPTIONS = [` — const, line 146
- `const TAG_ACTIONS: Array<` — const, line 156
- `const WHOLE_BLOCK_QUOTE = "(whole block)"` — const, line 164
- `type ReaderRailTab = "guide" | "ask" | "notes"` — type, line 166
- `const HEALTH_COLOR: Record<string, "green" | "amber" | "pink" | "slate"> =` — const, line 168
- `const FURNITURE_BLOCK_TYPES = new Set(["PageHeader", "PageFooter", "TableOfContents"])` — const, line 177
- `type OpenOutcome = "opened" | "preparing" | "not_opened"` — type, line 180
- `interface OfferedPress` — interface, line 184
- `const OFFER_OUTCOME: Record<FigureRequestOutcome, ExplorableOutcome> =` — const, line 195
- `const BADGED_HEALTH = new Set(["suspect", "failed"])` — const, line 201
- `interface RemovedAnnotation` — interface, line 205
- `const UNDO_REMOVE_MS = 10_000` — const, line 215
- `function newKey(): string` — function, line 217
- `function identityOf(view: Pick<ReaderRenderViewDto, "sourceId" | "revisionId" | "extractionId">): SourceIdentity` — function, line 226
- `function sectionIdentity(section:` — function, line 231
- `const mainPaneOwnsCueKey = (event: KeyboardEvent): boolean` — const, line 275
- `interface IntentPane` — interface, line 280
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 333
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 337
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 346
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 347
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 348
- `const openingRef = useRef<string | null>(null)` — const, line 354
- `const askPanelOn = algoConfig().ask !== null` — const, line 375
- `const storedStyle = useStoredHelpStyle()` — const, line 376
- `const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen` — const, line 377
- `const pdfViewRequestRef = useRef(0)` — const, line 399
- `const sourceEpochRef = useRef(0)` — const, line 430
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 441
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 442
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 443
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 444
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 445
- `const modeSaveVersionRef = useRef(0)` — const, line 446
- `const answerModeSaveVersionRef = useRef(0)` — const, line 447
- `const enabled = contract?.readerEnabled ?? true` — const, line 463
- `const inquiry = contract?.inquiryEnabled === true` — const, line 466
- `const muted = inquiry && mode === "skim"` — const, line 469
- `const intentContract = inquiry && !offline ? contract?.intent ?? null : null` — const, line 472
- `const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading)` — const, line 473
- `const figuresCtl = useFigures(` — const, line 475
- `const figureOffersOn = Boolean(contract?.figures?.offers) && !offline` — const, line 480
- `const showMeOn = Boolean(contract?.figures?.showMe) && !offline` — const, line 484
- `const waitingOfferRef = useRef<OfferedPress | null>(null)` — const, line 490
- `const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome)` — const, line 495
- `const press = offeredFigure` — const, line 502
- `const open = render?.extractionId ?? null` — const, line 504
- `const readerTutor = contract?.readerTutor ?? null` — const, line 527
- `const askWorkbenchSessionRef = useRef<string | null>(null)` — const, line 529
- `const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true` — const, line 534
- `const askPersonalizedRef = useRef<boolean | null>(null)` — const, line 535
- `const askComposerAnchorRef = useRef<AskAnchor | null>(null)` — const, line 540
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 546
- `const renderBlocksBySpan = useMemo( ()` — const, line 550
- `const visit = useReaderVisit(` — const, line 556
- `const showGuideRail = useCallback(()` — const, line 562
- `const progress = useReadingProgress(` — const, line 566
- `const doseVisitId = useCallback(()` — const, line 583
- `const refreshAnnotations = useCallback(async ()` — const, line 585
- `const epoch = sourceEpochRef.current` — const, line 587
- `const result = await cachedSourceRead( render.sourceId, ["reader_source_annotations", render.sourceId, render.extractionId], ()` — const, line 591
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 598
- `const version = (r.version as Record<string, unknown>) ??` — const, line 601
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 602
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 603
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 604
- `const placement = r.placement as ReaderAnnotationPlacementDto | undefined` — const, line 605
- `let page: number | null = null` — let, line 615
- `let bbox: number[] | null = null` — let, line 616
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 618
- `const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?:` — const, line 636
- `const openCardRef = useRef<SourceLibraryCard | null>(null)` — const, line 661
- `const openExtractionRef = useRef<string | null>(null)` — const, line 663
- `const reloadGuidePlan = useCallback(async ()` — const, line 665
- `const extractionId = render.extractionId` — const, line 667
- `const plan = await readGuidePlan(render.sourceId, extractionId,` — const, line 669
- `const spanOrder = useMemo( ()` — const, line 682
- `const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none"` — const, line 686
- `const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 689
- `const card = openCardRef.current` — const, line 690
- `const wbProps = useMemo<ReaderWorkbenchProps | undefined>(()` — const, line 700
- `const submitted = workbench?.onSubmitted` — const, line 701
- `const trail = besideTrail(returnStackRef.current)` — const, line 706
- `const wbCtl = useReaderWorkbench(` — const, line 711
- `const working = wbCtl.active !== null` — const, line 718
- `const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline` — const, line 722
- `const alsoHidden = alsoPrefs ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId)) : Boolean(contract?.correspondence?.hiddenEverywhere) || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.so…` — const, line 727
- `const peekCrumbShown = alsoPeek ?? findPeek` — const, line 737
- `const pathRefreshKey = readingPathRefreshKey(` — const, line 752
- `const tryFirstRef = useRef<((spanId: string)` — const, line 766
- `const cueCtl = useReaderCues(` — const, line 767
- `const recapCtl = useReaderRecap(` — const, line 782
- `const recapShown = Boolean(recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working)` — const, line 796
- `const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip")` — const, line 807
- `const root = history.find((entry)` — const, line 808
- `const recapRevisited = useCallback((rootId: string)` — const, line 821
- `const root = history.find((entry)` — const, line 822
- `const recapRevisit = useCallback(async (rootId: string)` — const, line 825
- `const root = history.find((entry)` — const, line 826
- `const recapOpenInquiry = useCallback((rootId: string, spanId: string)` — const, line 832
- `const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch")` — const, line 835
- `const cueMarksFor = (markSurface: "pdf" | "watch")` — const, line 855
- `let cancelled = false` — let, line 864
- `const scroller = railRef.current` — const, line 897
- `const clamp = ()` — const, line 899
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 900
- `const observer = new ResizeObserver(clamp)` — const, line 903
- `const query = librarySearch.trim()` — const, line 914
- `let cancelled = false` — let, line 921
- `const timer = window.setTimeout(()` — const, line 924
- `const resetSourceState = useCallback(()` — const, line 947
- `const openSource = useCallback( async ( card: SourceLibraryCard, jumpSpan?: string, // jumpReading: the reading jumpSpan was found on (a search hit, a // return)` — const, line 996
- `const handoff = options.handoff ?? null` — const, line 1005
- `const view = await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 1023
- `const pdfRequest = ++pdfViewRequestRef.current` — const, line 1070
- `const current = ()` — const, line 1071
- `const openFixture = useCallback(()` — const, line 1106
- `const backToLibrary = useCallback(()` — const, line 1114
- `const spanId = readingSpan ?? activeSpan` — const, line 1118
- `const section = guidePlan?.sections.find((candidate)` — const, line 1119
- `const resumedRef = useRef(false)` — const, line 1137
- `const trail = initialSource.besideTrail ?? null` — const, line 1141
- `const activeBlock = useMemo(()` — const, line 1155
- `const pdfHighlights: PdfHighlight[] = useMemo(()` — const, line 1164
- `const list: PdfHighlight[] = []` — const, line 1165
- `const base =` — const, line 1168
- `const placed = highlightFromPlacement(base, a.placement)` — const, line 1170
- `const segments = a.segments.flatMap((s)` — const, line 1175
- `const annotatedSpans = useMemo( ()` — const, line 1182
- `const boundaryBlock = useMemo(()` — const, line 1186
- `const revealedPassages = useMemo(()` — const, line 1188
- `const revealed = new Set(revealedSections)` — const, line 1189
- `const map = new Map<string,` — const, line 1190
- `const revealedGuidanceSpans = useMemo(()` — const, line 1199
- `const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null` — const, line 1204
- `const protectedSelection = selectionProtected(protection, selection)` — const, line 1205
- `const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1206
- `const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan))` — const, line 1210
- `const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1211
- `const editCaptureText = useCallback((text: string)` — const, line 1216
- `const resetCaptureText = useCallback(()` — const, line 1219
- `const saveAnnotationEdit = useCallback(async ()` — const, line 1231
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 1253
- `const result = await api.readerReanchor(` — const, line 1257
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1274
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1297
- `const target = annotations.find((a)` — const, line 1298
- `const reading = render ?` — const, line 1299
- `const epoch = sourceEpochRef.current` — const, line 1300
- `const undoRemove = useCallback(async ()` — const, line 1315
- `const last = removed` — const, line 1316
- `const epoch = sourceEpochRef.current` — const, line 1322
- `const result = await api.readerRestoreAnnotation(` — const, line 1324
- `const timer = window.setTimeout(()` — const, line 1337
- `const onKey = (event: KeyboardEvent)` — const, line 1343
- `const target = event.target` — const, line 1346
- `const openAnnotationNote = useCallback((annotationId: string)` — const, line 1355
- `const target = annotations.find((a)` — const, line 1356
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1368
- `const sel = window.getSelection()` — const, line 1369
- `const container = bodyRef.current` — const, line 1370
- `const range = sel.getRangeAt(0)` — const, line 1372
- `const nodes: Array<` — const, line 1373
- `const seen = new Set<string>()` — const, line 1374
- `const spanId = el.dataset.spanId` — const, line 1376
- `let intersects = false` — let, line 1378
- `const sub = document.createRange()` — const, line 1385
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1393
- `const block = renderBlocksBySpan.get(spanId)` — const, line 1398
- `const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1408
- `const cancelIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1409
- `const selectionSpanIds = useMemo( ()` — const, line 1410
- `const intentBox = useIntentBox(` — const, line 1414
- `const openActiveRail = useCallback(()` — const, line 1428
- `const activeCtl = useActiveReading(` — const, line 1432
- `const libraryCtl = useLibraryAsk(` — const, line 1441
- `const keptCtl = useKeptComparisons(` — const, line 1443
- `const notesCtl = useNoteMarks(` — const, line 1445
- `const pdfMarks = (): ReadonlyMap<string, ReactNode> | null` — const, line 1450
- `const cues = cueMarksFor("pdf")` — const, line 1451
- `const merged = new Map<string, ReactNode>(cues ?? [])` — const, line 1453
- `const cue = merged.get(spanId)` — const, line 1455
- `const before = merged.get(spanId)` — const, line 1460
- `const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null)` — const, line 1466
- `const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint)` — const, line 1468
- `const sbs = useSideBySide(` — const, line 1470
- `const node = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1478
- `const sbsPanes = sbs.panes && !comparing` — const, line 1491
- `const sbsPanesRef = useRef(false)` — const, line 1492
- `const sbsShownRef = useRef(false)` — const, line 1497
- `const sbsRef = useRef(sbs)` — const, line 1499
- `const sbsEscBusyRef = useRef(false)` — const, line 1502
- `const sbsPaneRef = useRef<HTMLDivElement | null>(null)` — const, line 1504
- `const runSideIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1509
- `const cancelSideIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1510
- `const sbsSection = sbs.section && sbs.target && sbs.section.sectionId === sbs.target.sectionId ? sbs.section : null` — const, line 1511
- `type BesideRun = |` — type, line 1526
- `const besideSeq = useRef(0)` — const, line 1535
- `const besideRunRef = useRef<(run: BesideRun)` — const, line 1538
- `const besideDroppedRef = useRef<(run: BesideRun)` — const, line 1539
- `const openBesideRef = useRef<(hit:` — const, line 1540
- `const snapshotBesideRef = useRef<(spanId: string)` — const, line 1547
- `const shown = sbsRef.current.target` — const, line 1549
- `const takeBesideBook = useCallback((book: SourceIdentity, spanId: string, run: BesideRun)` — const, line 1553
- `const id = ++besideSeq.current` — const, line 1555
- `const sideExtractionRef = useRef<string | null>(null)` — const, line 1567
- `const checkMeFromSideCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 1568
- `const side = useSidePane(` — const, line 1573
- `const besideRanRef = useRef(0)` — const, line 1602
- `const handoff = besideHandoff` — const, line 1604
- `const card = openCardRef.current` — const, line 1619
- `const trail = besideTrail(returnStackRef.current)` — const, line 1621
- `const work = handoff.run` — const, line 1630
- `const openComposer = useCallback((anchor: AskAnchor | null)` — const, line 1644
- `const sbsRowRef = useRef<HTMLDivElement | null>(null)` — const, line 1662
- `const startSbsResize = (event: ReactPointerEvent<HTMLDivElement>)` — const, line 1663
- `const row = sbsRowRef.current` — const, line 1664
- `const rect = row.getBoundingClientRect()` — const, line 1667
- `const move = (moved: PointerEvent)` — const, line 1668
- `const up = ()` — const, line 1671
- `const touchMain = ()` — const, line 1683
- `const onKey = (event: KeyboardEvent)` — const, line 1692
- `const target = event.target` — const, line 1694
- `const ctl = sbsRef.current` — const, line 1696
- `const open = ctl.panes || ctl.sheet` — const, line 1697
- `const shown = sbsShownRef.current` — const, line 1698
- `const mod = event.ctrlKey || event.metaKey` — const, line 1699
- `const side = sbsPaneRef.current` — const, line 1709
- `const inSide = target instanceof Element && Boolean(target.closest("[data-side-by-side-pane]"))` — const, line 1710
- `const inMain = target instanceof Node && Boolean(bodyRef.current?.contains(target))` — const, line 1716
- `const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false, anchor?: SourceIdentity)` — const, line 1726
- `const identity = anchor ?? identityOf(render)` — const, line 1733
- `const request =` — const, line 1734
- `const closeLibrary = useCallback(()` — const, line 1739
- `const onKey = (event: KeyboardEvent)` — const, line 1746
- `const onMouseUp = useCallback(()` — const, line 1757
- `const sel = window.getSelection()` — const, line 1758
- `const quote = sel.toString().replace(/\s+/g, " ").trim()` — const, line 1760
- `const nodes = collectSelectionNodes()` — const, line 1762
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1791
- `const domDragRef = useRef<` — const, line 1792
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1794
- `const host = bodyRef.current` — const, line 1795
- `const rect = host.getBoundingClientRect()` — const, line 1797
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1801
- `const target = event.target as Node` — const, line 1805
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1807
- `const domDrafting = domDraft !== null` — const, line 1819
- `const rectFrom = (drag:` — const, line 1822
- `const onMove = (event: MouseEvent)` — const, line 1828
- `const drag = domDragRef.current` — const, line 1829
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1831
- `const onUp = (event: MouseEvent)` — const, line 1834
- `const drag = domDragRef.current` — const, line 1835
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1839
- `const rect = rectFrom(drag, point)` — const, line 1841
- `const next = [...domBoxesRef.current, rect]` — const, line 1844
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1861
- `const host = bodyRef.current` — const, line 1862
- `const hostRect = host.getBoundingClientRect()` — const, line 1864
- `const clientBoxes = boxes.map((b)` — const, line 1865
- `const nodes: Array<` — const, line 1871
- `const seen = new Set<string>()` — const, line 1872
- `const spanId = el.dataset.spanId` — const, line 1874
- `const elRect = el.getBoundingClientRect()` — const, line 1876
- `const touches = clientBoxes.some( (b)` — const, line 1877
- `const words: string[] = []` — const, line 1881
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 1882
- `const text = node as Text` — const, line 1884
- `const wordPattern = /\S+/g` — const, line 1885
- `let match: RegExpExecArray | null` — let, line 1886
- `const range = document.createRange()` — const, line 1888
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 1891
- `const cx = (Math.min(...rects.map((r)` — const, line 1893
- `const cy = (Math.min(...rects.map((r)` — const, line 1894
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 1898
- `const commitDomBoxes = useCallback(()` — const, line 1907
- `const boxes = domBoxesRef.current` — const, line 1908
- `const nodes = resolveDomBoxes(boxes)` — const, line 1910
- `const quote = nodes.map((n)` — const, line 1916
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 1925
- `const clearDomBoxes = ()` — const, line 1933
- `const onKeyDown = (event: KeyboardEvent)` — const, line 1939
- `const onKeyUp = (event: KeyboardEvent)` — const, line 1944
- `const onBlur = ()` — const, line 1950
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 1972
- `const point = domPointFromClient(request.x, request.y)` — const, line 1974
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 1975
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 1996
- `const retryRequest = useCallback(async (requestId: string)` — const, line 2009
- `const optimisticSegments = useCallback( (nodes: string | Array<string |` — const, line 2023
- `const list = Array.isArray(nodes) ? nodes : [nodes]` — const, line 2025
- `const spanId = typeof node === "string" ? node : node.spanId` — const, line 2027
- `const geometry = pdfView?.blocks.find((b)` — const, line 2028
- `const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number" ?` — const, line 2029
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 2041
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 2045
- `const quotedNodes = (()` — const, line 2050
- `const multi = collectSelectionNodes()` — const, line 2053
- `const optimisticIds = quotedNodes ?? [target.spanId]` — const, line 2056
- `const nodes = quotedNodes ?? [` — const, line 2066
- `const receipt = await api.readerCapture(` — const, line 2067
- `const handler = (event: KeyboardEvent)` — const, line 2094
- `const clearSelection = useCallback(()` — const, line 2106
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 2118
- `const segment = a.segments.find((s)` — const, line 2120
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 2127
- `const alsoKeyRef = useRef<()` — const, line 2137
- `const onKey = (event: KeyboardEvent)` — const, line 2145
- `const target = event.target` — const, line 2148
- `const tabs: ReaderRailTab[] = ["guide", "ask", "notes"]` — const, line 2150
- `const askRequestSeen = useRef(askRequest)` — const, line 2188
- `const revealAskRef = useRef<()` — const, line 2190
- `const startCompareRef = useRef<(request: CompareRequest)` — const, line 2215
- `const sideAnchor = Boolean(side.extractionId) && side.extractionId === request.extractionId` — const, line 2218
- `const request = compareWaitsForWork` — const, line 2225
- `const sideMarksChanged = side.marksChanged` — const, line 2235
- `const captureIn = useCallback(async (target: PaneCaptureTarget, what:` — const, line 2236
- `const common =` — const, line 2241
- `const receipt: ReaderPresetReceiptDto = "preset" in what ? await api.readerInvokePreset(` — const, line 2246
- `const drained = await api.readerDrainOutbox()` — const, line 2257
- `const invokePreset = useCallback( // RW1b: the intent box passes its own words as the annotation's learner // text, and names the intention and entry in the funnel event. // Reader CA6b: `target` is side by side's second pane (its book, revision, // reading a…` — const, line 2278
- `const note_ = learnerTextOverride ?? note` — const, line 2286
- `const nodes = selectionNodes(selection)` — const, line 2287
- `const editedText = selection.editedText?.trim()` — const, line 2288
- `const receipt = await api.readerInvokePreset(` — const, line 2300
- `const drained = await api.readerDrainOutbox()` — const, line 2324
- `const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>, target?: PaneCaptureTarget): Promise<string | null>` — const, line 2347
- `const note_ = learnerTextOverride ?? note` — const, line 2351
- `const nodes = selectionNodes(selection)` — const, line 2352
- `const receipt = await api.readerCapture(` — const, line 2364
- `const pauseArc = useCallback(async ()` — const, line 2392
- `const next = await api.readerArc(` — const, line 2396
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 2403
- `const next = await api.readerArc(` — const, line 2408
- `const importJobRef = useRef<` — const, line 2420
- `const importExercise = useCallback(async (target?: PaneCaptureTarget): Promise<string | null>` — const, line 2423
- `const nodes = target ? target.nodes : selectionNodes(selection!)` — const, line 2425
- `const editedText = target ? undefined : selection!.editedText?.trim()` — const, line 2426
- `const receipt = await api.readerImportExercise(target ?` — const, line 2429
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 2477
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 2478
- `const timer = setInterval(async ()` — const, line 2482
- `const status = await api.readerExerciseImportStatus(` — const, line 2484
- `const job = importJobRef.current` — const, line 2485
- `const waited = Date.now() - job.startedAt` — const, line 2488
- `const saveOwnQuestion = useCallback(async ()` — const, line 2515
- `const saved = await api.readerAuthorQA(` — const, line 2523
- `const runCoach = useCallback(async ()` — const, line 2544
- `const lint = await api.readerCoachLint(` — const, line 2547
- `const changeMode = useCallback( async (next: string)` — const, line 2558
- `const previous = mode` — const, line 2560
- `const version = ++modeSaveVersionRef.current` — const, line 2563
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 2574
- `const answerModeNext = next as ReaderAnswerMode` — const, line 2576
- `const previous = answerMode` — const, line 2577
- `const version = ++answerModeSaveVersionRef.current` — const, line 2580
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 2596
- `const renderInquiryTop = useCallback((root: ReaderExchange)` — const, line 2611
- `const line = reconnect && reconnect.rootId === root.id && !muted ? ( <ReconnectLine placement="rail" question=` — const, line 2614
- `const check = inquiryChecks[root.id]` — const, line 2624
- `const inlineReconnect = reconnect && reconnect.inline && !muted ? ( <ReconnectLine placement="inline" question=` — const, line 2652
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 2663
- `const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">): Promise<OpenOutcome>` — const, line 2681
- `const card = (library ?? []).find((candidate)` — const, line 2686
- `const spanId = readingSpan ?? activeSpan` — const, line 2689
- `const compareFoundSection = (hit: CorrespondentSectionDto)` — const, line 2704
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2706
- `const hideAlsoInBooks = (scope: "book" | "everywhere")` — const, line 2729
- `const before = alsoPrefs ??` — const, line 2731
- `const base = contract` — const, line 2738
- `const makeExplorable = (target: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, origin: "library" | "tutor", offerRef: string): Promise<ExplorableOutcome>` — const, line 2755
- `let settle: (outcome: ExplorableOutcome)` — let, line 2762
- `const settled = new Promise<ExplorableOutcome>((resolve)` — const, line 2763
- `const press: OfferedPress =` — const, line 2764
- `const peekWorkbenchPassage = (spanId: string, target?: PassageTarget)` — const, line 2783
- `const exerciseSettings = libraryCtl.enabled ? contract?.libraryExercises ?? null : null` — const, line 2794
- `const exerciseCard = (sourceId: string | null)` — const, line 2795
- `const useExercise = (candidate: ExerciseCandidate)` — const, line 2799
- `const card = exerciseCard(candidate.sourceId ?? render?.sourceId ?? null)` — const, line 2800
- `const openExerciseInBook = (candidate: ExerciseCandidate)` — const, line 2809
- `const sourceId = candidate.sourceId ?? render?.sourceId ?? null` — const, line 2810
- `const exerciseProps: LibraryExercisesProps | null = exerciseSettings ?` — const, line 2813
- `const pickLibraryPagePractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 2827
- `const hit = libraryCtl.state?.ask.value?.hits[0]` — const, line 2828
- `const card = hit ? (library ?? []).find((candidate)` — const, line 2829
- `const readySources = library ?? []` — const, line 2872
- `const useShelf = Boolean(shelf) && !sidecarDown` — const, line 2874
- `const card = (library ?? []).find((candidate)` — const, line 2932
- `const card = (library ?? []).find((c)` — const, line 2953
- `const receiptId = searchResults.retrievalReceiptId` — const, line 2959
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 3004
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 3005
- `const wbActive = wbCtl.active` — const, line 3048
- `const wbStacked = working && wbCtl.narrow` — const, line 3049
- `const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible)` — const, line 3052
- `const wbSourceShown = !wbStacked || wbCtl.sheetOpen` — const, line 3053
- `const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry)` — const, line 3054
- `const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>()` — const, line 3055
- `const first = entry.spanIds[0]` — const, line 3057
- `const wbLabel = (stem: string)` — const, line 3060
- `const title = problemTitle(stem)` — const, line 3061
- `const tryPathExercise = (exercise: ReadingPathExerciseDto)` — const, line 3066
- `const workThroughSelection = ()` — const, line 3074
- `const nodes = selectionNodes(selection)` — const, line 3076
- `const editedText = selection.editedText?.trim()` — const, line 3077
- `const foldBlocks = contract?.activeReading?.foldBlocks ?? 3` — const, line 3094
- `const localFold = (spanIds: string[]): string[]` — const, line 3095
- `const positions = spanIds.map((spanId)` — const, line 3096
- `const last = Math.max(...positions)` — const, line 3098
- `const mainPane: IntentPane =` — const, line 3107
- `const sidePane: IntentPane | null = side.extractionId ?` — const, line 3116
- `const sideMeta = (pane: IntentPane): Record<string, string>` — const, line 3126
- `const runIntentIn = (pane: IntentPane, action: ReaderIntentActionDto, text: string, how: IntentRunHow): Promise<IntentRunHandle | null> | void` — const, line 3128
- `const meta =` — const, line 3129
- `const effect = action.effect` — const, line 3130
- `const sideSection = pane.side?.section ?? null` — const, line 3131
- `const anchor: AskAnchor =` — const, line 3137
- `const target = pane.side.target` — const, line 3178
- `const target = pane.side.target` — const, line 3184
- `const target = pane.side.target` — const, line 3190
- `const target = pane.side.target` — const, line 3200
- `const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null` — const, line 3245
- `const request: CompareRequest =` — const, line 3246
- `const region = pane.region` — const, line 3278
- `const words = text?.trim()` — const, line 3279
- `const sideShows = (extractionId: string, spanId: string): boolean` — const, line 3300
- `const checkBeside = (book: SourceIdentity, spanId: string, practiceItemId: string, proposalId: string | null)` — const, line 3303
- `const workThroughImported = (item:` — const, line 3308
- `const imported = exerciseImport` — const, line 3309
- `const spanIds = imported?.spanIds ?? (activeSpan ? [activeSpan] : [])` — const, line 3310
- `const settleShowMeLine = (key: string, patch: Partial<ShowMeLine>)` — const, line 3318
- `const requestShowMe = (ctl: FiguresCtl, run: Extract<BesideRun,` — const, line 3321
- `const key = run.lineKey` — const, line 3322
- `const runOnBook = (about: AskAbout, run: Extract<BesideRun,` — const, line 3334
- `const showMeFromAsk = ()` — const, line 3359
- `const goal = question.trim()` — const, line 3360
- `const about = parentExchange ? parentExchange.about ?? null : askComposerAnchor?.about ?? null` — const, line 3361
- `const home = parentExchange?.spanId ?? (about ? askComposerAnchor?.spanId : undefined) ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan` — const, line 3362
- `const key = `show_me:$` — const, line 3365
- `const run =` — const, line 3368
- `const cancelIntentIn = (pane: IntentPane, cancel: IntentCancel)` — const, line 3377
- `const kind = cancel.action.effect.kind` — const, line 3378
- `const annotationId = handle.annotationId` — const, line 3385
- `const batchId = handle.importBatchId` — const, line 3402
- `const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number)` — const, line 3416
- `const spanId = wbCtl.close(session,` — const, line 3418
- `const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3424
- `const card = openCardRef.current` — const, line 3425
- `const asked = libraryCtl.state?.request` — const, line 3429
- `const resumeMark = (spanId: string | null | undefined)` — const, line 3437
- `const entry = spanId ? wbResumeBySpan.get(spanId) : undefined` — const, line 3438
- `const verb = entry.status === "abandoned" ? "Reopen" : "Resume"` — const, line 3440
- `const target = event.target` — const, line 3564
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 3738
- `const active = activeSpan === block.spanId` — const, line 3739
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 3740
- `const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null` — const, line 3741
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 3742
- `const endQuestionAvailable = Boolean(endSection && endSection.question?.readingPhase === "after_section" && offeredCheckSections.has(endSection.id))` — const, line 3744
- `const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId))` — const, line 3748
- `const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""))` — const, line 3749
- `const offerSection = endSection && !muted && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 3750
- `const sel = window.getSelection()` — const, line 3769
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 3770
- `const cue = side.cues.markOn(spanId)` — const, line 3860
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 3888
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 3911
- `const active = railTab === tab` — const, line 4024
- `const waiting = tab === "guide" && pendingQuickCheckCount > 0` — const, line 4028
- `const marked = tab === "ask" && askTabMarked && !active` — const, line 4029
- `const params = (action.params ??` — const, line 4176
- `const run =` — const, line 4444
- `const book = exchange?.about ?? render` — const, line 4453

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`; references `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CorrespondentSectionDto`, `FigurePassageDto`, `FigureViewDto`, `LibraryAskEntry`, `LibraryHitDto`, `PassageTarget`, `ProposedItemDto`, `ReaderAnnotationPlacementDto`, `ReaderAnswerMode`, `ReaderArcDto`, `ReaderCoachLintDto`, `ReaderCueDto`, `ReaderDisposition`, `ReaderGuidePlanDto`, `ReaderGuideSectionDto`, `ReaderImportExerciseInput`, `ReaderIntentActionDto`, `ReaderPdfViewDto`, `ReaderPresetReceiptDto`, `ReaderPromptContractDto`, `ReaderRenderBlockDto`, `ReaderRenderViewDto`, `ReaderSourceSearchDto`, `ReaderWatchPlanDto`, `ReadingPathExerciseDto`, `SourceIdentity`, `SourceLibraryCard`
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
- [[Reference/Desktop/TypeScript/screens/reader/ActiveReadingCard|src/screens/reader/ActiveReadingCard.tsx]] — import-or-re-export; imports `ActiveReadingCard`, `NextStepFoldLine`
- [[Reference/Desktop/TypeScript/screens/reader/AlsoInBooks|src/screens/reader/AlsoInBooks.tsx]] — import-or-re-export; imports `AlsoInBooks`, `AlsoPeekCrumb`
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

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
source_commit: "47cec5279eec7c2738ab839c558ebcbd603f4b6a"
source_commit_timestamp: "2026-11-01T04:24:32-05:00"
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
| Source lines | 4557 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `47cec5279eec7c2738ab839c558ebcbd603f4b6a` |
| Commit timestamp | `2026-11-01T04:24:32-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]]

## Public API

- `export interface ReaderOpenSource` — interface, line 231
- `export interface ReaderCheckMeRequest extends CueCheckMeRequest` — interface, line 247
- `export type ReaderExerciseRequest = ReaderWorkbenchExercise &` — type, line 260
- `export const SIDE_PATH_COPY =` — const, line 264
- `export function ReaderScreen(` — function, line 286

## Internal implementation anchors

- `type AnnotationSegment, type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 135
- `type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 136
- `type ReaderSelection, } from "./reader/readerShared"` — type, line 137
- `const NO_SECTIONS: never[] = []` — const, line 141
- `const READER_MODE_OPTIONS = [` — const, line 142
- `const TAG_ACTIONS: Array<` — const, line 152
- `const WHOLE_BLOCK_QUOTE = "(whole block)"` — const, line 160
- `type ReaderRailTab = "guide" | "ask" | "notes"` — type, line 162
- `const HEALTH_COLOR: Record<string, "green" | "amber" | "pink" | "slate"> =` — const, line 164
- `const FURNITURE_BLOCK_TYPES = new Set(["PageHeader", "PageFooter", "TableOfContents"])` — const, line 173
- `type OpenOutcome = "opened" | "preparing" | "not_opened"` — type, line 176
- `interface OfferedPress` — interface, line 180
- `const OFFER_OUTCOME: Record<FigureRequestOutcome, ExplorableOutcome> =` — const, line 191
- `const BADGED_HEALTH = new Set(["suspect", "failed"])` — const, line 197
- `interface RemovedAnnotation` — interface, line 201
- `const UNDO_REMOVE_MS = 10_000` — const, line 211
- `function newKey(): string` — function, line 213
- `function identityOf(view: Pick<ReaderRenderViewDto, "sourceId" | "revisionId" | "extractionId">): SourceIdentity` — function, line 222
- `function sectionIdentity(section:` — function, line 227
- `const mainPaneOwnsCueKey = (event: KeyboardEvent): boolean` — const, line 271
- `interface IntentPane` — interface, line 276
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 329
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 333
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 342
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 343
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 344
- `const openingRef = useRef<string | null>(null)` — const, line 350
- `const askPanelOn = algoConfig().ask !== null` — const, line 371
- `const storedStyle = useStoredHelpStyle()` — const, line 372
- `const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen` — const, line 373
- `const pdfViewRequestRef = useRef(0)` — const, line 395
- `const sourceEpochRef = useRef(0)` — const, line 426
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 437
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 438
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 439
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 440
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 441
- `const modeSaveVersionRef = useRef(0)` — const, line 442
- `const answerModeSaveVersionRef = useRef(0)` — const, line 443
- `const enabled = contract?.readerEnabled ?? true` — const, line 459
- `const inquiry = contract?.inquiryEnabled === true` — const, line 462
- `const muted = inquiry && mode === "skim"` — const, line 465
- `const intentContract = inquiry && !offline ? contract?.intent ?? null : null` — const, line 468
- `const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading)` — const, line 469
- `const figuresCtl = useFigures(` — const, line 471
- `const figureOffersOn = Boolean(contract?.figures?.offers) && !offline` — const, line 476
- `const showMeOn = Boolean(contract?.figures?.showMe) && !offline` — const, line 480
- `const waitingOfferRef = useRef<OfferedPress | null>(null)` — const, line 486
- `const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome)` — const, line 491
- `const press = offeredFigure` — const, line 498
- `const open = render?.extractionId ?? null` — const, line 500
- `const readerTutor = contract?.readerTutor ?? null` — const, line 523
- `const askWorkbenchSessionRef = useRef<string | null>(null)` — const, line 525
- `const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true` — const, line 530
- `const askPersonalizedRef = useRef<boolean | null>(null)` — const, line 531
- `const askComposerAnchorRef = useRef<AskAnchor | null>(null)` — const, line 536
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 542
- `const renderBlocksBySpan = useMemo( ()` — const, line 546
- `const visit = useReaderVisit(` — const, line 552
- `const showGuideRail = useCallback(()` — const, line 558
- `const progress = useReadingProgress(` — const, line 562
- `const doseVisitId = useCallback(()` — const, line 579
- `const refreshAnnotations = useCallback(async ()` — const, line 581
- `const epoch = sourceEpochRef.current` — const, line 583
- `const result = await cachedSourceRead( render.sourceId, ["reader_source_annotations", render.sourceId, render.extractionId], ()` — const, line 587
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 594
- `const version = (r.version as Record<string, unknown>) ??` — const, line 597
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 598
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 599
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 600
- `const placement = r.placement as ReaderAnnotationPlacementDto | undefined` — const, line 601
- `let page: number | null = null` — let, line 611
- `let bbox: number[] | null = null` — let, line 612
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 614
- `const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?:` — const, line 632
- `const openCardRef = useRef<SourceLibraryCard | null>(null)` — const, line 657
- `const openExtractionRef = useRef<string | null>(null)` — const, line 659
- `const reloadGuidePlan = useCallback(async ()` — const, line 661
- `const extractionId = render.extractionId` — const, line 663
- `const plan = await readGuidePlan(render.sourceId, extractionId,` — const, line 665
- `const spanOrder = useMemo( ()` — const, line 678
- `const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none"` — const, line 682
- `const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 685
- `const card = openCardRef.current` — const, line 686
- `const wbProps = useMemo<ReaderWorkbenchProps | undefined>(()` — const, line 696
- `const submitted = workbench?.onSubmitted` — const, line 697
- `const trail = besideTrail(returnStackRef.current)` — const, line 702
- `const wbCtl = useReaderWorkbench(` — const, line 707
- `const working = wbCtl.active !== null` — const, line 714
- `const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline` — const, line 718
- `const alsoHidden = alsoPrefs ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId)) : Boolean(contract?.correspondence?.hiddenEverywhere) || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.so…` — const, line 723
- `const peekCrumbShown = alsoPeek ?? findPeek` — const, line 733
- `const pathRefreshKey = readingPathRefreshKey(` — const, line 748
- `const tryFirstRef = useRef<((spanId: string)` — const, line 762
- `const cueCtl = useReaderCues(` — const, line 763
- `const recapCtl = useReaderRecap(` — const, line 778
- `const recapShown = Boolean(recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working)` — const, line 792
- `const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip")` — const, line 803
- `const root = history.find((entry)` — const, line 804
- `const recapRevisited = useCallback((rootId: string)` — const, line 817
- `const root = history.find((entry)` — const, line 818
- `const recapRevisit = useCallback(async (rootId: string)` — const, line 821
- `const root = history.find((entry)` — const, line 822
- `const recapOpenInquiry = useCallback((rootId: string, spanId: string)` — const, line 828
- `const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch")` — const, line 831
- `const cueMarksFor = (markSurface: "pdf" | "watch")` — const, line 851
- `let cancelled = false` — let, line 860
- `const scroller = railRef.current` — const, line 893
- `const clamp = ()` — const, line 895
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 896
- `const observer = new ResizeObserver(clamp)` — const, line 899
- `const query = librarySearch.trim()` — const, line 910
- `let cancelled = false` — let, line 917
- `const timer = window.setTimeout(()` — const, line 920
- `const resetSourceState = useCallback(()` — const, line 943
- `const openSource = useCallback( async ( card: SourceLibraryCard, jumpSpan?: string, // jumpReading: the reading jumpSpan was found on (a search hit, a // return)` — const, line 992
- `const handoff = options.handoff ?? null` — const, line 1001
- `const view = await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 1019
- `const pdfRequest = ++pdfViewRequestRef.current` — const, line 1066
- `const current = ()` — const, line 1067
- `const openFixture = useCallback(()` — const, line 1102
- `const backToLibrary = useCallback(()` — const, line 1110
- `const spanId = readingSpan ?? activeSpan` — const, line 1114
- `const section = guidePlan?.sections.find((candidate)` — const, line 1115
- `const resumedRef = useRef(false)` — const, line 1133
- `const trail = initialSource.besideTrail ?? null` — const, line 1137
- `const activeBlock = useMemo(()` — const, line 1151
- `const pdfHighlights: PdfHighlight[] = useMemo(()` — const, line 1160
- `const list: PdfHighlight[] = []` — const, line 1161
- `const base =` — const, line 1164
- `const placed = highlightFromPlacement(base, a.placement)` — const, line 1166
- `const segments = a.segments.flatMap((s)` — const, line 1171
- `const annotatedSpans = useMemo( ()` — const, line 1178
- `const boundaryBlock = useMemo(()` — const, line 1182
- `const revealedPassages = useMemo(()` — const, line 1184
- `const revealed = new Set(revealedSections)` — const, line 1185
- `const map = new Map<string,` — const, line 1186
- `const revealedGuidanceSpans = useMemo(()` — const, line 1195
- `const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null` — const, line 1200
- `const protectedSelection = selectionProtected(protection, selection)` — const, line 1201
- `const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1202
- `const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan))` — const, line 1206
- `const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1207
- `const editCaptureText = useCallback((text: string)` — const, line 1212
- `const resetCaptureText = useCallback(()` — const, line 1215
- `const saveAnnotationEdit = useCallback(async ()` — const, line 1227
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 1249
- `const result = await api.readerReanchor(` — const, line 1253
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1270
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1293
- `const target = annotations.find((a)` — const, line 1294
- `const reading = render ?` — const, line 1295
- `const epoch = sourceEpochRef.current` — const, line 1296
- `const undoRemove = useCallback(async ()` — const, line 1311
- `const last = removed` — const, line 1312
- `const epoch = sourceEpochRef.current` — const, line 1318
- `const result = await api.readerRestoreAnnotation(` — const, line 1320
- `const timer = window.setTimeout(()` — const, line 1333
- `const onKey = (event: KeyboardEvent)` — const, line 1339
- `const target = event.target` — const, line 1342
- `const openAnnotationNote = useCallback((annotationId: string)` — const, line 1351
- `const target = annotations.find((a)` — const, line 1352
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1364
- `const sel = window.getSelection()` — const, line 1365
- `const container = bodyRef.current` — const, line 1366
- `const range = sel.getRangeAt(0)` — const, line 1368
- `const nodes: Array<` — const, line 1369
- `const seen = new Set<string>()` — const, line 1370
- `const spanId = el.dataset.spanId` — const, line 1372
- `let intersects = false` — let, line 1374
- `const sub = document.createRange()` — const, line 1381
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1389
- `const block = renderBlocksBySpan.get(spanId)` — const, line 1394
- `const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1404
- `const cancelIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1405
- `const selectionSpanIds = useMemo( ()` — const, line 1406
- `const intentBox = useIntentBox(` — const, line 1410
- `const openActiveRail = useCallback(()` — const, line 1424
- `const activeCtl = useActiveReading(` — const, line 1428
- `const libraryCtl = useLibraryAsk(` — const, line 1437
- `const keptCtl = useKeptComparisons(` — const, line 1439
- `const pdfMarks = (): ReadonlyMap<string, ReactNode> | null` — const, line 1443
- `const cues = cueMarksFor("pdf")` — const, line 1444
- `const merged = new Map<string, ReactNode>(cues ?? [])` — const, line 1446
- `const cue = merged.get(spanId)` — const, line 1448
- `const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null)` — const, line 1454
- `const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint)` — const, line 1456
- `const sbs = useSideBySide(` — const, line 1458
- `const node = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1466
- `const sbsPanes = sbs.panes && !comparing` — const, line 1479
- `const sbsPanesRef = useRef(false)` — const, line 1480
- `const sbsShownRef = useRef(false)` — const, line 1485
- `const sbsRef = useRef(sbs)` — const, line 1487
- `const sbsEscBusyRef = useRef(false)` — const, line 1490
- `const sbsPaneRef = useRef<HTMLDivElement | null>(null)` — const, line 1492
- `const runSideIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1497
- `const cancelSideIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1498
- `const sbsSection = sbs.section && sbs.target && sbs.section.sectionId === sbs.target.sectionId ? sbs.section : null` — const, line 1499
- `type BesideRun = |` — type, line 1514
- `const besideSeq = useRef(0)` — const, line 1523
- `const besideRunRef = useRef<(run: BesideRun)` — const, line 1526
- `const besideDroppedRef = useRef<(run: BesideRun)` — const, line 1527
- `const openBesideRef = useRef<(hit:` — const, line 1528
- `const snapshotBesideRef = useRef<(spanId: string)` — const, line 1535
- `const shown = sbsRef.current.target` — const, line 1537
- `const takeBesideBook = useCallback((book: SourceIdentity, spanId: string, run: BesideRun)` — const, line 1541
- `const id = ++besideSeq.current` — const, line 1543
- `const sideExtractionRef = useRef<string | null>(null)` — const, line 1555
- `const checkMeFromSideCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 1556
- `const side = useSidePane(` — const, line 1561
- `const besideRanRef = useRef(0)` — const, line 1590
- `const handoff = besideHandoff` — const, line 1592
- `const card = openCardRef.current` — const, line 1607
- `const trail = besideTrail(returnStackRef.current)` — const, line 1609
- `const work = handoff.run` — const, line 1618
- `const openComposer = useCallback((anchor: AskAnchor | null)` — const, line 1632
- `const sbsRowRef = useRef<HTMLDivElement | null>(null)` — const, line 1650
- `const startSbsResize = (event: ReactPointerEvent<HTMLDivElement>)` — const, line 1651
- `const row = sbsRowRef.current` — const, line 1652
- `const rect = row.getBoundingClientRect()` — const, line 1655
- `const move = (moved: PointerEvent)` — const, line 1656
- `const up = ()` — const, line 1659
- `const touchMain = ()` — const, line 1671
- `const onKey = (event: KeyboardEvent)` — const, line 1680
- `const target = event.target` — const, line 1682
- `const ctl = sbsRef.current` — const, line 1684
- `const open = ctl.panes || ctl.sheet` — const, line 1685
- `const shown = sbsShownRef.current` — const, line 1686
- `const mod = event.ctrlKey || event.metaKey` — const, line 1687
- `const side = sbsPaneRef.current` — const, line 1697
- `const inSide = target instanceof Element && Boolean(target.closest("[data-side-by-side-pane]"))` — const, line 1698
- `const inMain = target instanceof Node && Boolean(bodyRef.current?.contains(target))` — const, line 1704
- `const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false, anchor?: SourceIdentity)` — const, line 1714
- `const identity = anchor ?? identityOf(render)` — const, line 1721
- `const request =` — const, line 1722
- `const closeLibrary = useCallback(()` — const, line 1727
- `const onKey = (event: KeyboardEvent)` — const, line 1734
- `const onMouseUp = useCallback(()` — const, line 1745
- `const sel = window.getSelection()` — const, line 1746
- `const quote = sel.toString().replace(/\s+/g, " ").trim()` — const, line 1748
- `const nodes = collectSelectionNodes()` — const, line 1750
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1779
- `const domDragRef = useRef<` — const, line 1780
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1782
- `const host = bodyRef.current` — const, line 1783
- `const rect = host.getBoundingClientRect()` — const, line 1785
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1789
- `const target = event.target as Node` — const, line 1793
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1795
- `const domDrafting = domDraft !== null` — const, line 1807
- `const rectFrom = (drag:` — const, line 1810
- `const onMove = (event: MouseEvent)` — const, line 1816
- `const drag = domDragRef.current` — const, line 1817
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1819
- `const onUp = (event: MouseEvent)` — const, line 1822
- `const drag = domDragRef.current` — const, line 1823
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1827
- `const rect = rectFrom(drag, point)` — const, line 1829
- `const next = [...domBoxesRef.current, rect]` — const, line 1832
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1849
- `const host = bodyRef.current` — const, line 1850
- `const hostRect = host.getBoundingClientRect()` — const, line 1852
- `const clientBoxes = boxes.map((b)` — const, line 1853
- `const nodes: Array<` — const, line 1859
- `const seen = new Set<string>()` — const, line 1860
- `const spanId = el.dataset.spanId` — const, line 1862
- `const elRect = el.getBoundingClientRect()` — const, line 1864
- `const touches = clientBoxes.some( (b)` — const, line 1865
- `const words: string[] = []` — const, line 1869
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 1870
- `const text = node as Text` — const, line 1872
- `const wordPattern = /\S+/g` — const, line 1873
- `let match: RegExpExecArray | null` — let, line 1874
- `const range = document.createRange()` — const, line 1876
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 1879
- `const cx = (Math.min(...rects.map((r)` — const, line 1881
- `const cy = (Math.min(...rects.map((r)` — const, line 1882
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 1886
- `const commitDomBoxes = useCallback(()` — const, line 1895
- `const boxes = domBoxesRef.current` — const, line 1896
- `const nodes = resolveDomBoxes(boxes)` — const, line 1898
- `const quote = nodes.map((n)` — const, line 1904
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 1913
- `const clearDomBoxes = ()` — const, line 1921
- `const onKeyDown = (event: KeyboardEvent)` — const, line 1927
- `const onKeyUp = (event: KeyboardEvent)` — const, line 1932
- `const onBlur = ()` — const, line 1938
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 1960
- `const point = domPointFromClient(request.x, request.y)` — const, line 1962
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 1963
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 1984
- `const retryRequest = useCallback(async (requestId: string)` — const, line 1997
- `const optimisticSegments = useCallback( (nodes: string | Array<string |` — const, line 2011
- `const list = Array.isArray(nodes) ? nodes : [nodes]` — const, line 2013
- `const spanId = typeof node === "string" ? node : node.spanId` — const, line 2015
- `const geometry = pdfView?.blocks.find((b)` — const, line 2016
- `const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number" ?` — const, line 2017
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 2029
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 2033
- `const quotedNodes = (()` — const, line 2038
- `const multi = collectSelectionNodes()` — const, line 2041
- `const optimisticIds = quotedNodes ?? [target.spanId]` — const, line 2044
- `const nodes = quotedNodes ?? [` — const, line 2054
- `const receipt = await api.readerCapture(` — const, line 2055
- `const handler = (event: KeyboardEvent)` — const, line 2082
- `const clearSelection = useCallback(()` — const, line 2094
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 2106
- `const segment = a.segments.find((s)` — const, line 2108
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 2115
- `const alsoKeyRef = useRef<()` — const, line 2125
- `const onKey = (event: KeyboardEvent)` — const, line 2133
- `const target = event.target` — const, line 2136
- `const tabs: ReaderRailTab[] = ["guide", "ask", "notes"]` — const, line 2138
- `const askRequestSeen = useRef(askRequest)` — const, line 2176
- `const revealAskRef = useRef<()` — const, line 2178
- `const startCompareRef = useRef<(request: CompareRequest)` — const, line 2203
- `const sideAnchor = Boolean(side.extractionId) && side.extractionId === request.extractionId` — const, line 2206
- `const request = compareWaitsForWork` — const, line 2213
- `const sideMarksChanged = side.marksChanged` — const, line 2223
- `const captureIn = useCallback(async (target: PaneCaptureTarget, what:` — const, line 2224
- `const common =` — const, line 2229
- `const receipt: ReaderPresetReceiptDto = "preset" in what ? await api.readerInvokePreset(` — const, line 2234
- `const drained = await api.readerDrainOutbox()` — const, line 2245
- `const invokePreset = useCallback( // RW1b: the intent box passes its own words as the annotation's learner // text, and names the intention and entry in the funnel event. // Reader CA6b: `target` is side by side's second pane (its book, revision, // reading a…` — const, line 2266
- `const note_ = learnerTextOverride ?? note` — const, line 2274
- `const nodes = selectionNodes(selection)` — const, line 2275
- `const editedText = selection.editedText?.trim()` — const, line 2276
- `const receipt = await api.readerInvokePreset(` — const, line 2288
- `const drained = await api.readerDrainOutbox()` — const, line 2312
- `const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>, target?: PaneCaptureTarget): Promise<string | null>` — const, line 2335
- `const note_ = learnerTextOverride ?? note` — const, line 2339
- `const nodes = selectionNodes(selection)` — const, line 2340
- `const receipt = await api.readerCapture(` — const, line 2352
- `const pauseArc = useCallback(async ()` — const, line 2380
- `const next = await api.readerArc(` — const, line 2384
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 2391
- `const next = await api.readerArc(` — const, line 2396
- `const importJobRef = useRef<` — const, line 2408
- `const importExercise = useCallback(async (target?: PaneCaptureTarget): Promise<string | null>` — const, line 2411
- `const nodes = target ? target.nodes : selectionNodes(selection!)` — const, line 2413
- `const editedText = target ? undefined : selection!.editedText?.trim()` — const, line 2414
- `const receipt = await api.readerImportExercise(target ?` — const, line 2417
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 2465
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 2466
- `const timer = setInterval(async ()` — const, line 2470
- `const status = await api.readerExerciseImportStatus(` — const, line 2472
- `const job = importJobRef.current` — const, line 2473
- `const waited = Date.now() - job.startedAt` — const, line 2476
- `const saveOwnQuestion = useCallback(async ()` — const, line 2503
- `const saved = await api.readerAuthorQA(` — const, line 2511
- `const runCoach = useCallback(async ()` — const, line 2532
- `const lint = await api.readerCoachLint(` — const, line 2535
- `const changeMode = useCallback( async (next: string)` — const, line 2546
- `const previous = mode` — const, line 2548
- `const version = ++modeSaveVersionRef.current` — const, line 2551
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 2562
- `const answerModeNext = next as ReaderAnswerMode` — const, line 2564
- `const previous = answerMode` — const, line 2565
- `const version = ++answerModeSaveVersionRef.current` — const, line 2568
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 2583
- `const renderInquiryTop = useCallback((root: ReaderExchange)` — const, line 2598
- `const line = reconnect && reconnect.rootId === root.id && !muted ? ( <ReconnectLine placement="rail" question=` — const, line 2601
- `const check = inquiryChecks[root.id]` — const, line 2611
- `const inlineReconnect = reconnect && reconnect.inline && !muted ? ( <ReconnectLine placement="inline" question=` — const, line 2639
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 2650
- `const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">): Promise<OpenOutcome>` — const, line 2668
- `const card = (library ?? []).find((candidate)` — const, line 2673
- `const spanId = readingSpan ?? activeSpan` — const, line 2676
- `const compareFoundSection = (hit: CorrespondentSectionDto)` — const, line 2691
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2693
- `const hideAlsoInBooks = (scope: "book" | "everywhere")` — const, line 2716
- `const before = alsoPrefs ??` — const, line 2718
- `const base = contract` — const, line 2725
- `const makeExplorable = (target: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, origin: "library" | "tutor", offerRef: string): Promise<ExplorableOutcome>` — const, line 2742
- `let settle: (outcome: ExplorableOutcome)` — let, line 2749
- `const settled = new Promise<ExplorableOutcome>((resolve)` — const, line 2750
- `const press: OfferedPress =` — const, line 2751
- `const peekWorkbenchPassage = (spanId: string, target?: PassageTarget)` — const, line 2770
- `const exerciseSettings = libraryCtl.enabled ? contract?.libraryExercises ?? null : null` — const, line 2781
- `const exerciseCard = (sourceId: string | null)` — const, line 2782
- `const useExercise = (candidate: ExerciseCandidate)` — const, line 2786
- `const card = exerciseCard(candidate.sourceId ?? render?.sourceId ?? null)` — const, line 2787
- `const openExerciseInBook = (candidate: ExerciseCandidate)` — const, line 2796
- `const sourceId = candidate.sourceId ?? render?.sourceId ?? null` — const, line 2797
- `const exerciseProps: LibraryExercisesProps | null = exerciseSettings ?` — const, line 2800
- `const pickLibraryPagePractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 2814
- `const hit = libraryCtl.state?.ask.value?.hits[0]` — const, line 2815
- `const card = hit ? (library ?? []).find((candidate)` — const, line 2816
- `const readySources = library ?? []` — const, line 2859
- `const useShelf = Boolean(shelf) && !sidecarDown` — const, line 2861
- `const card = (library ?? []).find((candidate)` — const, line 2917
- `const card = (library ?? []).find((c)` — const, line 2937
- `const receiptId = searchResults.retrievalReceiptId` — const, line 2943
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 2988
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 2989
- `const wbActive = wbCtl.active` — const, line 3032
- `const wbStacked = working && wbCtl.narrow` — const, line 3033
- `const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible)` — const, line 3036
- `const wbSourceShown = !wbStacked || wbCtl.sheetOpen` — const, line 3037
- `const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry)` — const, line 3038
- `const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>()` — const, line 3039
- `const first = entry.spanIds[0]` — const, line 3041
- `const wbLabel = (stem: string)` — const, line 3044
- `const title = problemTitle(stem)` — const, line 3045
- `const tryPathExercise = (exercise: ReadingPathExerciseDto)` — const, line 3050
- `const workThroughSelection = ()` — const, line 3058
- `const nodes = selectionNodes(selection)` — const, line 3060
- `const editedText = selection.editedText?.trim()` — const, line 3061
- `const foldBlocks = contract?.activeReading?.foldBlocks ?? 3` — const, line 3078
- `const localFold = (spanIds: string[]): string[]` — const, line 3079
- `const positions = spanIds.map((spanId)` — const, line 3080
- `const last = Math.max(...positions)` — const, line 3082
- `const mainPane: IntentPane =` — const, line 3091
- `const sidePane: IntentPane | null = side.extractionId ?` — const, line 3100
- `const sideMeta = (pane: IntentPane): Record<string, string>` — const, line 3110
- `const runIntentIn = (pane: IntentPane, action: ReaderIntentActionDto, text: string, how: IntentRunHow): Promise<IntentRunHandle | null> | void` — const, line 3112
- `const meta =` — const, line 3113
- `const effect = action.effect` — const, line 3114
- `const sideSection = pane.side?.section ?? null` — const, line 3115
- `const anchor: AskAnchor =` — const, line 3121
- `const target = pane.side.target` — const, line 3162
- `const target = pane.side.target` — const, line 3168
- `const target = pane.side.target` — const, line 3174
- `const target = pane.side.target` — const, line 3184
- `const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null` — const, line 3229
- `const request: CompareRequest =` — const, line 3230
- `const region = pane.region` — const, line 3262
- `const words = text?.trim()` — const, line 3263
- `const sideShows = (extractionId: string, spanId: string): boolean` — const, line 3284
- `const checkBeside = (book: SourceIdentity, spanId: string, practiceItemId: string, proposalId: string | null)` — const, line 3287
- `const workThroughImported = (item:` — const, line 3292
- `const imported = exerciseImport` — const, line 3293
- `const spanIds = imported?.spanIds ?? (activeSpan ? [activeSpan] : [])` — const, line 3294
- `const settleShowMeLine = (key: string, patch: Partial<ShowMeLine>)` — const, line 3302
- `const requestShowMe = (ctl: FiguresCtl, run: Extract<BesideRun,` — const, line 3305
- `const key = run.lineKey` — const, line 3306
- `const runOnBook = (about: AskAbout, run: Extract<BesideRun,` — const, line 3318
- `const showMeFromAsk = ()` — const, line 3343
- `const goal = question.trim()` — const, line 3344
- `const about = parentExchange ? parentExchange.about ?? null : askComposerAnchor?.about ?? null` — const, line 3345
- `const home = parentExchange?.spanId ?? (about ? askComposerAnchor?.spanId : undefined) ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan` — const, line 3346
- `const key = `show_me:$` — const, line 3349
- `const run =` — const, line 3352
- `const cancelIntentIn = (pane: IntentPane, cancel: IntentCancel)` — const, line 3361
- `const kind = cancel.action.effect.kind` — const, line 3362
- `const annotationId = handle.annotationId` — const, line 3369
- `const batchId = handle.importBatchId` — const, line 3386
- `const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number)` — const, line 3400
- `const spanId = wbCtl.close(session,` — const, line 3402
- `const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3408
- `const card = openCardRef.current` — const, line 3409
- `const asked = libraryCtl.state?.request` — const, line 3413
- `const resumeMark = (spanId: string | null | undefined)` — const, line 3421
- `const entry = spanId ? wbResumeBySpan.get(spanId) : undefined` — const, line 3422
- `const verb = entry.status === "abandoned" ? "Reopen" : "Resume"` — const, line 3424
- `const target = event.target` — const, line 3547
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 3721
- `const active = activeSpan === block.spanId` — const, line 3722
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 3723
- `const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null` — const, line 3724
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 3725
- `const endQuestionAvailable = Boolean(endSection && endSection.question?.readingPhase === "after_section" && offeredCheckSections.has(endSection.id))` — const, line 3727
- `const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId))` — const, line 3731
- `const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""))` — const, line 3732
- `const offerSection = endSection && !muted && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 3733
- `const sel = window.getSelection()` — const, line 3752
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 3753
- `const cue = side.cues.markOn(spanId)` — const, line 3842
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 3870
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 3893
- `const active = railTab === tab` — const, line 4006
- `const waiting = tab === "guide" && pendingQuickCheckCount > 0` — const, line 4010
- `const marked = tab === "ask" && askTabMarked && !active` — const, line 4011
- `const params = (action.params ??` — const, line 4158
- `const run =` — const, line 4417
- `const book = exchange?.about ?? render` — const, line 4426

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
- [[Reference/Desktop/TypeScript/screens/reader/ReaderWorkingPosture|src/screens/reader/ReaderWorkingPosture.tsx]] — import-or-re-export; imports `ReaderWorkingPosture`
- [[Reference/Desktop/TypeScript/screens/reader/ReadingPathCard|src/screens/reader/ReadingPathCard.tsx]] — import-or-re-export; imports `ReadingPathCard`
- [[Reference/Desktop/TypeScript/screens/reader/RecapCard|src/screens/reader/RecapCard.tsx]] — import-or-re-export; imports `RecapCard`
- [[Reference/Desktop/TypeScript/screens/reader/ReconnectLine|src/screens/reader/ReconnectLine.tsx]] — import-or-re-export; imports `ReconnectLine`
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
- [[Reference/Desktop/TypeScript/screens/reader/readerCache|src/screens/reader/readerCache.ts]] — import-or-re-export; imports `cachedSourceRead`
- [[Reference/Desktop/TypeScript/screens/reader/readerKeys|src/screens/reader/readerKeys.ts]] — import-or-re-export; imports `readerKeyBarKeys`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `AnnotationSegment`, `MarginAnnotation`, `ReaderSelection`, `askGroundingSpans`, `clip`, `groundingProtected`, `placedSpanIds`, `selectionNodes`, `selectionProtected`
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

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
| Source lines | 4774 |
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

- `export interface ReaderOpenSource` — interface, line 249
- `export interface ReaderCheckMeRequest extends CueCheckMeRequest` — interface, line 265
- `export type ReaderExerciseRequest = ReaderWorkbenchExercise &` — type, line 278
- `export const SIDE_PATH_COPY =` — const, line 282
- `export function ReaderScreen(` — function, line 304

## Internal implementation anchors

- `type AnnotationSegment, type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 146
- `type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 147
- `type ReaderSelection, } from "./reader/readerShared"` — type, line 148
- `const NO_SECTIONS: never[] = []` — const, line 152
- `const READER_MODE_OPTIONS = [` — const, line 153
- `const TAG_ACTIONS: Array<` — const, line 163
- `const WHOLE_BLOCK_QUOTE = "(whole block)"` — const, line 171
- `type ReaderRailTab = "guide" | "ask" | "notes"` — type, line 173
- `const HEALTH_COLOR: Record<string, "green" | "amber" | "pink" | "slate"> =` — const, line 175
- `const FIGURE_PAGE_NOT_OPENED = "That page couldn't be opened."` — const, line 183
- `type OpenOutcome = "opened" | "preparing" | "not_opened"` — type, line 186
- `interface OfferedPress` — interface, line 190
- `const OFFER_OUTCOME: Record<FigureRequestOutcome, ExplorableOutcome> =` — const, line 201
- `const BADGED_HEALTH = new Set(["suspect", "failed"])` — const, line 207
- `interface RemovedAnnotation` — interface, line 211
- `const UNDO_REMOVE_MS = 10_000` — const, line 221
- `interface SelectionHighlight` — interface, line 224
- `function newKey(): string` — function, line 231
- `function identityOf(view: Pick<ReaderRenderViewDto, "sourceId" | "revisionId" | "extractionId">): SourceIdentity` — function, line 240
- `function sectionIdentity(section:` — function, line 245
- `const mainPaneOwnsCueKey = (event: KeyboardEvent): boolean` — const, line 289
- `interface IntentPane` — interface, line 294
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 354
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 358
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 367
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 368
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 369
- `const openingRef = useRef<string | null>(null)` — const, line 375
- `const savingHighlightNote = useRef(false)` — const, line 387
- `const askPanelOn = algoConfig().ask !== null` — const, line 401
- `const storedStyle = useStoredHelpStyle()` — const, line 402
- `const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen` — const, line 403
- `const pdfViewRequestRef = useRef(0)` — const, line 425
- `const sourceEpochRef = useRef(0)` — const, line 456
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 467
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 468
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 469
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 470
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 471
- `const modeSaveVersionRef = useRef(0)` — const, line 472
- `const answerModeSaveVersionRef = useRef(0)` — const, line 473
- `const enabled = contract?.readerEnabled ?? true` — const, line 489
- `const inquiry = contract?.inquiryEnabled === true` — const, line 492
- `const muted = inquiry && mode === "skim"` — const, line 495
- `const intentContract = inquiry && !offline ? contract?.intent ?? null : null` — const, line 498
- `const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading)` — const, line 499
- `const openFigureSource = useRef<((extractionId: string, spanId: string)` — const, line 503
- `const figureOpenSource = useCallback((extractionId: string, spanId: string)` — const, line 504
- `const figuresCtl = useFigures(` — const, line 505
- `const figureOffersOn = Boolean(contract?.figures?.offers) && !offline` — const, line 511
- `const showMeOn = Boolean(contract?.figures?.showMe) && !offline` — const, line 515
- `const waitingOfferRef = useRef<OfferedPress | null>(null)` — const, line 521
- `const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome)` — const, line 526
- `const press = offeredFigure` — const, line 533
- `const open = render?.extractionId ?? null` — const, line 535
- `const readerTutor = contract?.readerTutor ?? null` — const, line 558
- `const askWorkbenchSessionRef = useRef<string | null>(null)` — const, line 560
- `const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true` — const, line 565
- `const askPersonalizedRef = useRef<boolean | null>(null)` — const, line 566
- `const askComposerAnchorRef = useRef<AskAnchor | null>(null)` — const, line 571
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 577
- `const renderBlocksBySpan = useMemo( ()` — const, line 581
- `const visit = useReaderVisit(` — const, line 587
- `const showGuideRail = useCallback(()` — const, line 593
- `const progress = useReadingProgress(` — const, line 597
- `const doseVisitId = useCallback(()` — const, line 614
- `const refreshAnnotations = useCallback(async ()` — const, line 616
- `const epoch = sourceEpochRef.current` — const, line 618
- `const result = await cachedSourceRead( render.sourceId, ["reader_source_annotations", render.sourceId, render.extractionId], ()` — const, line 622
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 629
- `const version = (r.version as Record<string, unknown>) ??` — const, line 632
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 633
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 634
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 635
- `const placement = r.placement as ReaderAnnotationPlacementDto | undefined` — const, line 636
- `let page: number | null = null` — let, line 646
- `let bbox: number[] | null = null` — let, line 647
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 649
- `const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?:` — const, line 667
- `const openCardRef = useRef<SourceLibraryCard | null>(null)` — const, line 692
- `const openExtractionRef = useRef<string | null>(null)` — const, line 694
- `const reloadGuidePlan = useCallback(async ()` — const, line 696
- `const extractionId = render.extractionId` — const, line 698
- `const plan = await readGuidePlan(render.sourceId, extractionId,` — const, line 700
- `const spanOrder = useMemo( ()` — const, line 713
- `const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none"` — const, line 717
- `const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 720
- `const card = openCardRef.current` — const, line 721
- `const wbProps = useMemo<ReaderWorkbenchProps | undefined>(()` — const, line 731
- `const submitted = workbench?.onSubmitted` — const, line 732
- `const trail = besideTrail(returnStackRef.current)` — const, line 737
- `const wbCtl = useReaderWorkbench(` — const, line 742
- `const working = wbCtl.active !== null` — const, line 749
- `const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline` — const, line 753
- `const alsoHidden = alsoPrefs ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId)) : Boolean(contract?.correspondence?.hiddenEverywhere) || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.so…` — const, line 758
- `const peekCrumbShown = alsoPeek ?? findPeek` — const, line 768
- `const pathRefreshKey = readingPathRefreshKey(` — const, line 783
- `const tryFirstRef = useRef<((spanId: string)` — const, line 797
- `const cueCtl = useReaderCues(` — const, line 798
- `const recapCtl = useReaderRecap(` — const, line 813
- `const recapShown = Boolean(recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working)` — const, line 827
- `const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip")` — const, line 838
- `const root = history.find((entry)` — const, line 839
- `const recapRevisited = useCallback((rootId: string)` — const, line 852
- `const root = history.find((entry)` — const, line 853
- `const recapRevisit = useCallback(async (rootId: string)` — const, line 856
- `const root = history.find((entry)` — const, line 857
- `const recapOpenInquiry = useCallback((rootId: string, spanId: string)` — const, line 863
- `const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch")` — const, line 866
- `const cueMarksFor = (markSurface: "pdf" | "watch")` — const, line 886
- `let cancelled = false` — let, line 895
- `const scroller = railRef.current` — const, line 928
- `const clamp = ()` — const, line 930
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 931
- `const observer = new ResizeObserver(clamp)` — const, line 934
- `const query = librarySearch.trim()` — const, line 945
- `let cancelled = false` — let, line 952
- `const timer = window.setTimeout(()` — const, line 955
- `const resetSourceState = useCallback(()` — const, line 978
- `const openSource = useCallback( async ( card: SourceLibraryCard, jumpSpan?: string, // jumpReading: the reading jumpSpan was found on (a search hit, a // return)` — const, line 1027
- `const handoff = options.handoff ?? null` — const, line 1037
- `const view = options.view ?? await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 1055
- `const pdfRequest = ++pdfViewRequestRef.current` — const, line 1102
- `const current = ()` — const, line 1103
- `const openFixture = useCallback(()` — const, line 1138
- `const backToLibrary = useCallback(()` — const, line 1146
- `const spanId = readingSpan ?? activeSpan` — const, line 1150
- `const section = guidePlan?.sections.find((candidate)` — const, line 1151
- `const resumedRef = useRef(false)` — const, line 1169
- `const trail = initialSource.besideTrail ?? null` — const, line 1173
- `const activeBlock = useMemo(()` — const, line 1187
- `const pdfHighlights: PdfHighlight[] = useMemo(()` — const, line 1196
- `const list: PdfHighlight[] = []` — const, line 1197
- `const base =` — const, line 1200
- `const placed = highlightFromPlacement(base, a.placement)` — const, line 1202
- `const segments = a.segments.flatMap((s)` — const, line 1207
- `const annotatedSpans = useMemo( ()` — const, line 1214
- `const boundaryBlock = useMemo(()` — const, line 1218
- `const revealedPassages = useMemo(()` — const, line 1220
- `const revealed = new Set(revealedSections)` — const, line 1221
- `const map = new Map<string,` — const, line 1222
- `const revealedGuidanceSpans = useMemo(()` — const, line 1231
- `const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null` — const, line 1236
- `const protectedSelection = selectionProtected(protection, selection)` — const, line 1237
- `const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1238
- `const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan))` — const, line 1242
- `const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1243
- `const editCaptureText = useCallback((text: string)` — const, line 1248
- `const resetCaptureText = useCallback(()` — const, line 1251
- `const saveAnnotationEdit = useCallback(async ()` — const, line 1263
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 1285
- `const result = await api.readerReanchor(` — const, line 1289
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1306
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1329
- `const target = annotations.find((a)` — const, line 1330
- `const reading = render ?` — const, line 1331
- `const epoch = sourceEpochRef.current` — const, line 1332
- `const undoRemove = useCallback(async ()` — const, line 1347
- `const last = removed` — const, line 1348
- `const epoch = sourceEpochRef.current` — const, line 1354
- `const result = await api.readerRestoreAnnotation(` — const, line 1356
- `const timer = window.setTimeout(()` — const, line 1369
- `const onKey = (event: KeyboardEvent)` — const, line 1375
- `const target = event.target` — const, line 1378
- `const openAnnotationNote = useCallback((annotationId: string)` — const, line 1387
- `const target = annotations.find((a)` — const, line 1388
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1400
- `const sel = window.getSelection()` — const, line 1401
- `const container = bodyRef.current` — const, line 1402
- `const range = sel.getRangeAt(0)` — const, line 1404
- `const nodes: Array<` — const, line 1405
- `const seen = new Set<string>()` — const, line 1406
- `const spanId = el.dataset.spanId` — const, line 1408
- `let intersects = false` — let, line 1410
- `const sub = document.createRange()` — const, line 1417
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1425
- `const block = renderBlocksBySpan.get(spanId)` — const, line 1430
- `const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1440
- `const cancelIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1441
- `const selectionSpanIds = useMemo( ()` — const, line 1442
- `const intentBox = useIntentBox(` — const, line 1446
- `const openActiveRail = useCallback(()` — const, line 1460
- `const activeCtl = useActiveReading(` — const, line 1464
- `const libraryCtl = useLibraryAsk(` — const, line 1473
- `const keptCtl = useKeptComparisons(` — const, line 1475
- `const notesCtl = useNoteMarks(` — const, line 1477
- `const pdfMarks = (): ReadonlyMap<string, ReactNode> | null` — const, line 1482
- `const cues = cueMarksFor("pdf")` — const, line 1483
- `const merged = new Map<string, ReactNode>(cues ?? [])` — const, line 1485
- `const cue = merged.get(spanId)` — const, line 1487
- `const before = merged.get(spanId)` — const, line 1492
- `const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null)` — const, line 1498
- `const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint)` — const, line 1500
- `const sbs = useSideBySide(` — const, line 1502
- `const node = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1510
- `const sbsPanes = sbs.panes && !comparing` — const, line 1523
- `const sbsPanesRef = useRef(false)` — const, line 1524
- `const sbsShownRef = useRef(false)` — const, line 1529
- `const sbsRef = useRef(sbs)` — const, line 1531
- `const sbsEscBusyRef = useRef(false)` — const, line 1534
- `const sbsPaneRef = useRef<HTMLDivElement | null>(null)` — const, line 1536
- `const runSideIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1541
- `const cancelSideIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1542
- `const sbsSection = sbs.section && sbs.target && sbs.section.sectionId === sbs.target.sectionId ? sbs.section : null` — const, line 1543
- `type BesideRun = |` — type, line 1558
- `const besideSeq = useRef(0)` — const, line 1567
- `const besideRunRef = useRef<(run: BesideRun)` — const, line 1570
- `const besideDroppedRef = useRef<(run: BesideRun)` — const, line 1571
- `const openBesideRef = useRef<(hit:` — const, line 1572
- `const snapshotBesideRef = useRef<(spanId: string)` — const, line 1579
- `const shown = sbsRef.current.target` — const, line 1581
- `const takeBesideBook = useCallback((book: SourceIdentity, spanId: string, run: BesideRun)` — const, line 1585
- `const id = ++besideSeq.current` — const, line 1587
- `const sideExtractionRef = useRef<string | null>(null)` — const, line 1599
- `const checkMeFromSideCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 1600
- `const side = useSidePane(` — const, line 1605
- `const besideRanRef = useRef(0)` — const, line 1634
- `const handoff = besideHandoff` — const, line 1636
- `const card = openCardRef.current` — const, line 1651
- `const trail = besideTrail(returnStackRef.current)` — const, line 1653
- `const work = handoff.run` — const, line 1662
- `const openComposer = useCallback((anchor: AskAnchor | null)` — const, line 1676
- `const sbsRowRef = useRef<HTMLDivElement | null>(null)` — const, line 1694
- `const startSbsResize = (event: ReactPointerEvent<HTMLDivElement>)` — const, line 1695
- `const row = sbsRowRef.current` — const, line 1696
- `const rect = row.getBoundingClientRect()` — const, line 1699
- `const move = (moved: PointerEvent)` — const, line 1700
- `const up = ()` — const, line 1703
- `const touchMain = ()` — const, line 1715
- `const onKey = (event: KeyboardEvent)` — const, line 1724
- `const target = event.target` — const, line 1726
- `const ctl = sbsRef.current` — const, line 1728
- `const open = ctl.panes || ctl.sheet` — const, line 1729
- `const shown = sbsShownRef.current` — const, line 1730
- `const mod = event.ctrlKey || event.metaKey` — const, line 1731
- `const side = sbsPaneRef.current` — const, line 1741
- `const inSide = target instanceof Element && Boolean(target.closest("[data-side-by-side-pane]"))` — const, line 1742
- `const inMain = target instanceof Node && Boolean(bodyRef.current?.contains(target))` — const, line 1748
- `const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false, anchor?: SourceIdentity)` — const, line 1758
- `const identity = anchor ?? identityOf(render)` — const, line 1765
- `const request =` — const, line 1766
- `const closeLibrary = useCallback(()` — const, line 1771
- `const onKey = (event: KeyboardEvent)` — const, line 1778
- `const onMouseUp = useCallback(()` — const, line 1789
- `const sel = window.getSelection()` — const, line 1790
- `const quote = selectionQuote(sel.getRangeAt(0), sel.toString()).replace(/\s+/g, " ").trim()` — const, line 1794
- `const nodes = collectSelectionNodes()` — const, line 1796
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1825
- `const domDragRef = useRef<` — const, line 1826
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1828
- `const host = bodyRef.current` — const, line 1829
- `const rect = host.getBoundingClientRect()` — const, line 1831
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1835
- `const target = event.target as Node` — const, line 1839
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1841
- `const domDrafting = domDraft !== null` — const, line 1853
- `const rectFrom = (drag:` — const, line 1856
- `const onMove = (event: MouseEvent)` — const, line 1862
- `const drag = domDragRef.current` — const, line 1863
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1865
- `const onUp = (event: MouseEvent)` — const, line 1868
- `const drag = domDragRef.current` — const, line 1869
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1873
- `const rect = rectFrom(drag, point)` — const, line 1875
- `const next = [...domBoxesRef.current, rect]` — const, line 1878
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1895
- `const host = bodyRef.current` — const, line 1896
- `const hostRect = host.getBoundingClientRect()` — const, line 1898
- `const clientBoxes = boxes.map((b)` — const, line 1899
- `const nodes: Array<` — const, line 1905
- `const seen = new Set<string>()` — const, line 1906
- `const spanId = el.dataset.spanId` — const, line 1908
- `const elRect = el.getBoundingClientRect()` — const, line 1910
- `const touches = clientBoxes.some( (b)` — const, line 1911
- `const words: string[] = []` — const, line 1915
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 1916
- `const text = node as Text` — const, line 1918
- `const wordPattern = /\S+/g` — const, line 1919
- `let match: RegExpExecArray | null` — let, line 1920
- `const range = document.createRange()` — const, line 1922
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 1925
- `const cx = (Math.min(...rects.map((r)` — const, line 1927
- `const cy = (Math.min(...rects.map((r)` — const, line 1928
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 1932
- `const commitDomBoxes = useCallback(()` — const, line 1941
- `const boxes = domBoxesRef.current` — const, line 1942
- `const nodes = resolveDomBoxes(boxes)` — const, line 1944
- `const quote = nodes.map((n)` — const, line 1950
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 1959
- `const clearDomBoxes = ()` — const, line 1967
- `const onKeyDown = (event: KeyboardEvent)` — const, line 1973
- `const onKeyUp = (event: KeyboardEvent)` — const, line 1978
- `const onBlur = ()` — const, line 1984
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 2006
- `const point = domPointFromClient(request.x, request.y)` — const, line 2008
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 2009
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 2030
- `const retryRequest = useCallback(async (requestId: string)` — const, line 2043
- `const optimisticSegments = useCallback( (nodes: string | Array<string |` — const, line 2057
- `const list = Array.isArray(nodes) ? nodes : [nodes]` — const, line 2059
- `const spanId = typeof node === "string" ? node : node.spanId` — const, line 2061
- `const geometry = pdfView?.blocks.find((b)` — const, line 2062
- `const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number" ?` — const, line 2063
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 2075
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 2079
- `const quotedNodes = (()` — const, line 2084
- `const multi = collectSelectionNodes()` — const, line 2087
- `const optimisticIds = quotedNodes ?? [target.spanId]` — const, line 2090
- `const nodes = quotedNodes ?? [` — const, line 2100
- `const receipt = await api.readerCapture(` — const, line 2101
- `const handler = (event: KeyboardEvent)` — const, line 2128
- `const clearSelection = useCallback(()` — const, line 2140
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 2152
- `const segment = a.segments.find((s)` — const, line 2154
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 2161
- `const alsoKeyRef = useRef<()` — const, line 2171
- `const onKey = (event: KeyboardEvent)` — const, line 2179
- `const target = event.target` — const, line 2182
- `const tabs: ReaderRailTab[] = ["guide", "ask", "notes"]` — const, line 2184
- `const askRequestSeen = useRef(askRequest)` — const, line 2222
- `const revealAskRef = useRef<()` — const, line 2224
- `const startCompareRef = useRef<(request: CompareRequest)` — const, line 2249
- `const sideAnchor = Boolean(side.extractionId) && side.extractionId === request.extractionId` — const, line 2252
- `const request = compareWaitsForWork` — const, line 2259
- `const sideMarksChanged = side.marksChanged` — const, line 2269
- `const captureIn = useCallback(async (target: PaneCaptureTarget, what:` — const, line 2270
- `const common =` — const, line 2275
- `const receipt: ReaderPresetReceiptDto = "preset" in what ? await api.readerInvokePreset(` — const, line 2280
- `const drained = await api.readerDrainOutbox()` — const, line 2291
- `const invokePreset = useCallback( // RW1b: the intent box passes its own words as the annotation's learner // text, and names the intention and entry in the funnel event. // Reader CA6b: `target` is side by side's second pane (its book, revision, // reading a…` — const, line 2312
- `const note_ = learnerTextOverride ?? note` — const, line 2320
- `const nodes = selectionNodes(selection)` — const, line 2321
- `const editedText = selection.editedText?.trim()` — const, line 2322
- `const receipt = await api.readerInvokePreset(` — const, line 2334
- `const drained = await api.readerDrainOutbox()` — const, line 2358
- `const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>, target?: PaneCaptureTarget): Promise<string | null>` — const, line 2381
- `const note_ = learnerTextOverride ?? note` — const, line 2385
- `const nodes = selectionNodes(selection)` — const, line 2386
- `const receipt = await api.readerCapture(` — const, line 2399
- `const currentHighlight = selection && selectionHighlight && selectionActions.includes("highlight") && selectionHighlight.spanId === selection.spanId && selectionHighlight.quote === selection.quote ? selectionHighlight : null` — const, line 2429
- `const saveHighlightNote = useCallback(async ()` — const, line 2434
- `const target = currentHighlight` — const, line 2435
- `const words = note.trim()` — const, line 2436
- `const learnerText = target.saved.trim() ? `$` — const, line 2438
- `const typed = note` — const, line 2439
- `const kept = ()` — const, line 2440
- `const annotationId = target.annotationId` — const, line 2451
- `const pauseArc = useCallback(async ()` — const, line 2468
- `const next = await api.readerArc(` — const, line 2472
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 2479
- `const next = await api.readerArc(` — const, line 2484
- `const importJobRef = useRef<` — const, line 2496
- `const importExercise = useCallback(async (target?: PaneCaptureTarget): Promise<string | null>` — const, line 2499
- `const nodes = target ? target.nodes : selectionNodes(selection!)` — const, line 2501
- `const editedText = target ? undefined : selection!.editedText?.trim()` — const, line 2502
- `const receipt = await api.readerImportExercise(target ?` — const, line 2505
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 2553
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 2554
- `const timer = setInterval(async ()` — const, line 2558
- `const status = await api.readerExerciseImportStatus(` — const, line 2560
- `const job = importJobRef.current` — const, line 2561
- `const waited = Date.now() - job.startedAt` — const, line 2564
- `const saveOwnQuestion = useCallback(async ()` — const, line 2591
- `const saved = await api.readerAuthorQA(` — const, line 2599
- `const runCoach = useCallback(async ()` — const, line 2620
- `const lint = await api.readerCoachLint(` — const, line 2623
- `const changeMode = useCallback( async (next: string)` — const, line 2634
- `const previous = mode` — const, line 2636
- `const version = ++modeSaveVersionRef.current` — const, line 2639
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 2650
- `const answerModeNext = next as ReaderAnswerMode` — const, line 2652
- `const previous = answerMode` — const, line 2653
- `const version = ++answerModeSaveVersionRef.current` — const, line 2656
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 2672
- `const renderInquiryTop = useCallback((root: ReaderExchange)` — const, line 2687
- `const line = reconnect && reconnect.rootId === root.id && !muted ? ( <ReconnectLine placement="rail" question=` — const, line 2690
- `const check = inquiryChecks[root.id]` — const, line 2700
- `const inlineReconnect = reconnect && reconnect.inline && !muted ? ( <ReconnectLine placement="inline" question=` — const, line 2728
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 2739
- `const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, pinned?: ReaderRenderViewDto): Promise<OpenOutcome>` — const, line 2758
- `const card = (library ?? []).find((candidate)` — const, line 2763
- `const spanId = readingSpan ?? activeSpan` — const, line 2766
- `const onOriginal = pdfView && surface === "pdf" && !offline` — const, line 2792
- `const epoch = sourceEpochRef.current` — const, line 2805
- `const sameBook = Boolean(render && sourceId === render.sourceId)` — const, line 2808
- `const card = (library ?? []).find((candidate)` — const, line 2809
- `const landed = await api.readerSavedPlace(` — const, line 2814
- `const landing = await api.readerRenderView(` — const, line 2828
- `const openFollowedFigure = (figure: CorrespondentFigureDto, hit: CorrespondentSectionDto)` — const, line 2838
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2840
- `const compareFoundSection = (hit: CorrespondentSectionDto)` — const, line 2855
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2857
- `const hideAlsoInBooks = (scope: "book" | "everywhere")` — const, line 2880
- `const before = alsoPrefs ??` — const, line 2882
- `const base = contract` — const, line 2889
- `const makeExplorable = (target: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, origin: "library" | "tutor", offerRef: string): Promise<ExplorableOutcome>` — const, line 2906
- `let settle: (outcome: ExplorableOutcome)` — let, line 2913
- `const settled = new Promise<ExplorableOutcome>((resolve)` — const, line 2914
- `const press: OfferedPress =` — const, line 2915
- `const peekWorkbenchPassage = (spanId: string, target?: PassageTarget)` — const, line 2934
- `const exerciseSettings = libraryCtl.enabled ? contract?.libraryExercises ?? null : null` — const, line 2945
- `const exerciseCard = (sourceId: string | null)` — const, line 2946
- `const useExercise = (candidate: ExerciseCandidate)` — const, line 2950
- `const card = exerciseCard(candidate.sourceId ?? render?.sourceId ?? null)` — const, line 2951
- `const openExerciseInBook = (candidate: ExerciseCandidate)` — const, line 2960
- `const sourceId = candidate.sourceId ?? render?.sourceId ?? null` — const, line 2961
- `const exerciseProps: LibraryExercisesProps | null = exerciseSettings ?` — const, line 2964
- `const pickLibraryPagePractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 2978
- `const hit = libraryCtl.state?.ask.value?.hits[0]` — const, line 2979
- `const card = hit ? (library ?? []).find((candidate)` — const, line 2980
- `const readySources = library ?? []` — const, line 3023
- `const useShelf = Boolean(shelf) && !sidecarDown` — const, line 3025
- `const card = (library ?? []).find((candidate)` — const, line 3083
- `const card = (library ?? []).find((c)` — const, line 3104
- `const receiptId = searchResults.retrievalReceiptId` — const, line 3110
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 3155
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 3156
- `const wbActive = wbCtl.active` — const, line 3199
- `const wbStacked = working && wbCtl.narrow` — const, line 3200
- `const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible)` — const, line 3203
- `const wbSourceShown = !wbStacked || wbCtl.sheetOpen` — const, line 3204
- `const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry)` — const, line 3205
- `const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>()` — const, line 3206
- `const first = entry.spanIds[0]` — const, line 3208
- `const wbLabel = (stem: string)` — const, line 3211
- `const title = problemTitle(stem)` — const, line 3212
- `const tryPathExercise = (exercise: ReadingPathExerciseDto)` — const, line 3217
- `const workThroughSelection = ()` — const, line 3225
- `const nodes = selectionNodes(selection)` — const, line 3227
- `const editedText = selection.editedText?.trim()` — const, line 3228
- `const foldBlocks = contract?.activeReading?.foldBlocks ?? 3` — const, line 3245
- `const localFold = (spanIds: string[]): string[]` — const, line 3246
- `const positions = spanIds.map((spanId)` — const, line 3247
- `const last = Math.max(...positions)` — const, line 3249
- `const mainPane: IntentPane =` — const, line 3258
- `const sidePane: IntentPane | null = side.extractionId ?` — const, line 3267
- `const sideMeta = (pane: IntentPane): Record<string, string>` — const, line 3277
- `const runIntentIn = (pane: IntentPane, action: ReaderIntentActionDto, text: string, how: IntentRunHow): Promise<IntentRunHandle | null> | void` — const, line 3279
- `const meta =` — const, line 3280
- `const effect = action.effect` — const, line 3281
- `const noteText = !action.model && intentContract && onlyNamesAnAction(text, [...intentContract.palette, ...intentContract.notesPalette]) ? "" : text` — const, line 3285
- `const sideSection = pane.side?.section ?? null` — const, line 3287
- `const anchor: AskAnchor =` — const, line 3293
- `const target = pane.side.target` — const, line 3334
- `const target = pane.side.target` — const, line 3340
- `const target = pane.side.target` — const, line 3346
- `const target = pane.side.target` — const, line 3356
- `const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null` — const, line 3401
- `const request: CompareRequest =` — const, line 3402
- `const region = pane.region` — const, line 3434
- `const words = text?.trim()` — const, line 3435
- `const sideShows = (extractionId: string, spanId: string): boolean` — const, line 3456
- `const checkBeside = (book: SourceIdentity, spanId: string, practiceItemId: string, proposalId: string | null)` — const, line 3459
- `const workThroughImported = (item:` — const, line 3464
- `const imported = exerciseImport` — const, line 3465
- `const spanIds = imported?.spanIds ?? (activeSpan ? [activeSpan] : [])` — const, line 3466
- `const settleShowMeLine = (key: string, patch: Partial<ShowMeLine>)` — const, line 3474
- `const requestShowMe = (ctl: FiguresCtl, run: Extract<BesideRun,` — const, line 3477
- `const key = run.lineKey` — const, line 3478
- `const runOnBook = (about: AskAbout, run: Extract<BesideRun,` — const, line 3490
- `const showMeFromAsk = ()` — const, line 3515
- `const goal = question.trim()` — const, line 3516
- `const about = parentExchange ? parentExchange.about ?? null : askComposerAnchor?.about ?? null` — const, line 3517
- `const home = parentExchange?.spanId ?? (about ? askComposerAnchor?.spanId : undefined) ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan` — const, line 3518
- `const key = `show_me:$` — const, line 3521
- `const run =` — const, line 3524
- `const cancelIntentIn = (pane: IntentPane, cancel: IntentCancel)` — const, line 3533
- `const kind = cancel.action.effect.kind` — const, line 3534
- `const annotationId = handle.annotationId` — const, line 3541
- `const batchId = handle.importBatchId` — const, line 3558
- `const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number)` — const, line 3572
- `const spanId = wbCtl.close(session,` — const, line 3574
- `const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3580
- `const card = openCardRef.current` — const, line 3581
- `const asked = libraryCtl.state?.request` — const, line 3585
- `const resumeMark = (spanId: string | null | undefined)` — const, line 3593
- `const entry = spanId ? wbResumeBySpan.get(spanId) : undefined` — const, line 3594
- `const verb = entry.status === "abandoned" ? "Reopen" : "Resume"` — const, line 3596
- `const target = event.target` — const, line 3723
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 3898
- `const active = activeSpan === block.spanId` — const, line 3899
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 3900
- `const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null` — const, line 3901
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 3902
- `const endQuestionAvailable = Boolean(endSection && endSection.question?.readingPhase === "after_section" && offeredCheckSections.has(endSection.id))` — const, line 3904
- `const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId))` — const, line 3908
- `const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""))` — const, line 3909
- `const offerSection = endSection && !muted && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 3910
- `const sel = window.getSelection()` — const, line 3929
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 3930
- `const cue = side.cues.markOn(spanId)` — const, line 4020
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 4048
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 4071
- `const active = railTab === tab` — const, line 4184
- `const waiting = tab === "guide" && pendingQuickCheckCount > 0` — const, line 4188
- `const marked = tab === "ask" && askTabMarked && !active` — const, line 4189
- `const params = (action.params ??` — const, line 4337
- `const run =` — const, line 4611
- `const book = exchange?.about ?? render` — const, line 4620

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

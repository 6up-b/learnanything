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
source_commit: "2ce89d4f4134f634f37b200cae73c52ac7a9cec0"
source_commit_timestamp: "2026-10-31T19:42:55-04:00"
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
| Source lines | 3763 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `2ce89d4f4134f634f37b200cae73c52ac7a9cec0` |
| Commit timestamp | `2026-10-31T19:42:55-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]]

## Public API

- `export interface ReaderOpenSource` — interface, line 214
- `export interface ReaderCheckMeRequest extends CueCheckMeRequest` — interface, line 225
- `export type ReaderExerciseRequest = ReaderWorkbenchExercise &` — type, line 235
- `export function ReaderScreen(` — function, line 237

## Internal implementation anchors

- `type AnnotationSegment, type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 128
- `type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 129
- `type ReaderSelection, } from "./reader/readerShared"` — type, line 130
- `const NO_SECTIONS: never[] = []` — const, line 134
- `const READER_MODE_OPTIONS = [` — const, line 135
- `const TAG_ACTIONS: Array<` — const, line 145
- `const WHOLE_BLOCK_QUOTE = "(whole block)"` — const, line 153
- `type ReaderRailTab = "guide" | "ask" | "notes"` — type, line 155
- `const HEALTH_COLOR: Record<string, "green" | "amber" | "pink" | "slate"> =` — const, line 157
- `const FURNITURE_BLOCK_TYPES = new Set(["PageHeader", "PageFooter", "TableOfContents"])` — const, line 166
- `type OpenOutcome = "opened" | "preparing" | "not_opened"` — type, line 169
- `interface OfferedPress` — interface, line 173
- `const OFFER_OUTCOME: Record<FigureRequestOutcome, ExplorableOutcome> =` — const, line 184
- `const BADGED_HEALTH = new Set(["suspect", "failed"])` — const, line 190
- `interface RemovedAnnotation` — interface, line 194
- `const UNDO_REMOVE_MS = 10_000` — const, line 204
- `function newKey(): string` — function, line 206
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 280
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 284
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 293
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 294
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 295
- `const openingRef = useRef<string | null>(null)` — const, line 301
- `const askPanelOn = algoConfig().ask !== null` — const, line 322
- `const storedStyle = useStoredHelpStyle()` — const, line 323
- `const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen` — const, line 324
- `const pdfViewRequestRef = useRef(0)` — const, line 346
- `const sourceEpochRef = useRef(0)` — const, line 377
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 388
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 389
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 390
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 391
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 392
- `const modeSaveVersionRef = useRef(0)` — const, line 393
- `const answerModeSaveVersionRef = useRef(0)` — const, line 394
- `const enabled = contract?.readerEnabled ?? true` — const, line 410
- `const inquiry = contract?.inquiryEnabled === true` — const, line 413
- `const muted = inquiry && mode === "skim"` — const, line 416
- `const intentContract = inquiry && !offline ? contract?.intent ?? null : null` — const, line 419
- `const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading)` — const, line 420
- `const figuresCtl = useFigures(` — const, line 422
- `const figureOffersOn = Boolean(contract?.figures?.offers) && !offline` — const, line 427
- `const showMeOn = Boolean(contract?.figures?.showMe) && !offline` — const, line 431
- `const waitingOfferRef = useRef<OfferedPress | null>(null)` — const, line 437
- `const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome)` — const, line 442
- `const press = offeredFigure` — const, line 449
- `const open = render?.extractionId ?? null` — const, line 451
- `const readerTutor = contract?.readerTutor ?? null` — const, line 474
- `const askWorkbenchSessionRef = useRef<string | null>(null)` — const, line 476
- `const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true` — const, line 481
- `const askPersonalizedRef = useRef<boolean | null>(null)` — const, line 482
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 488
- `const renderBlocksBySpan = useMemo( ()` — const, line 492
- `const visit = useReaderVisit(` — const, line 498
- `const showGuideRail = useCallback(()` — const, line 504
- `const progress = useReadingProgress(` — const, line 508
- `const doseVisitId = useCallback(()` — const, line 525
- `const refreshAnnotations = useCallback(async ()` — const, line 527
- `const epoch = sourceEpochRef.current` — const, line 529
- `const result = await cachedSourceRead( render.sourceId, ["reader_source_annotations", render.sourceId, render.extractionId], ()` — const, line 533
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 540
- `const version = (r.version as Record<string, unknown>) ??` — const, line 543
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 544
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 545
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 546
- `const placement = r.placement as ReaderAnnotationPlacementDto | undefined` — const, line 547
- `let page: number | null = null` — let, line 557
- `let bbox: number[] | null = null` — let, line 558
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 560
- `const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?:` — const, line 578
- `const openCardRef = useRef<SourceLibraryCard | null>(null)` — const, line 602
- `const openExtractionRef = useRef<string | null>(null)` — const, line 604
- `const reloadGuidePlan = useCallback(async ()` — const, line 606
- `const extractionId = render.extractionId` — const, line 608
- `const plan = await readGuidePlan(render.sourceId, extractionId,` — const, line 610
- `const spanOrder = useMemo( ()` — const, line 623
- `const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none"` — const, line 627
- `const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 630
- `const card = openCardRef.current` — const, line 631
- `const wbCtl = useReaderWorkbench(` — const, line 637
- `const working = wbCtl.active !== null` — const, line 644
- `const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline` — const, line 648
- `const alsoHidden = alsoPrefs ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId)) : Boolean(contract?.correspondence?.hiddenEverywhere) || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.so…` — const, line 653
- `const peekCrumbShown = alsoPeek ?? findPeek` — const, line 663
- `const pathRefreshKey = readingPathRefreshKey(` — const, line 678
- `const tryFirstRef = useRef<((spanId: string)` — const, line 692
- `const cueCtl = useReaderCues(` — const, line 693
- `const recapCtl = useReaderRecap(` — const, line 705
- `const recapShown = Boolean(recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working)` — const, line 719
- `const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip")` — const, line 730
- `const root = history.find((entry)` — const, line 731
- `const recapRevisited = useCallback((rootId: string)` — const, line 744
- `const root = history.find((entry)` — const, line 745
- `const recapRevisit = useCallback(async (rootId: string)` — const, line 748
- `const root = history.find((entry)` — const, line 749
- `const recapOpenInquiry = useCallback((rootId: string, spanId: string)` — const, line 755
- `const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch")` — const, line 758
- `const cueMarksFor = (markSurface: "pdf" | "watch")` — const, line 778
- `let cancelled = false` — let, line 787
- `const scroller = railRef.current` — const, line 820
- `const clamp = ()` — const, line 822
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 823
- `const observer = new ResizeObserver(clamp)` — const, line 826
- `const query = librarySearch.trim()` — const, line 837
- `let cancelled = false` — let, line 844
- `const timer = window.setTimeout(()` — const, line 847
- `const resetSourceState = useCallback(()` — const, line 870
- `const openSource = useCallback( async ( card: SourceLibraryCard, jumpSpan?: string, // jumpReading: the reading jumpSpan was found on (a search hit, a // return)` — const, line 919
- `const handoff = options.handoff ?? null` — const, line 928
- `const view = await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 946
- `const pdfRequest = ++pdfViewRequestRef.current` — const, line 993
- `const current = ()` — const, line 994
- `const openFixture = useCallback(()` — const, line 1029
- `const backToLibrary = useCallback(()` — const, line 1037
- `const spanId = readingSpan ?? activeSpan` — const, line 1041
- `const section = guidePlan?.sections.find((candidate)` — const, line 1042
- `const resumedRef = useRef(false)` — const, line 1060
- `const activeBlock = useMemo(()` — const, line 1072
- `const pdfHighlights: PdfHighlight[] = useMemo(()` — const, line 1081
- `const list: PdfHighlight[] = []` — const, line 1082
- `const base =` — const, line 1085
- `const placed = highlightFromPlacement(base, a.placement)` — const, line 1087
- `const segments = a.segments.flatMap((s)` — const, line 1092
- `const annotatedSpans = useMemo( ()` — const, line 1099
- `const boundaryBlock = useMemo(()` — const, line 1103
- `const revealedPassages = useMemo(()` — const, line 1105
- `const revealed = new Set(revealedSections)` — const, line 1106
- `const map = new Map<string,` — const, line 1107
- `const revealedGuidanceSpans = useMemo(()` — const, line 1116
- `const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null` — const, line 1121
- `const protectedSelection = selectionProtected(protection, selection)` — const, line 1122
- `const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1123
- `const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan))` — const, line 1127
- `const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1128
- `const editCaptureText = useCallback((text: string)` — const, line 1133
- `const resetCaptureText = useCallback(()` — const, line 1136
- `const saveAnnotationEdit = useCallback(async ()` — const, line 1148
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 1170
- `const result = await api.readerReanchor(` — const, line 1174
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1191
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1214
- `const target = annotations.find((a)` — const, line 1215
- `const reading = render ?` — const, line 1216
- `const epoch = sourceEpochRef.current` — const, line 1217
- `const undoRemove = useCallback(async ()` — const, line 1232
- `const last = removed` — const, line 1233
- `const epoch = sourceEpochRef.current` — const, line 1239
- `const result = await api.readerRestoreAnnotation(` — const, line 1241
- `const timer = window.setTimeout(()` — const, line 1254
- `const onKey = (event: KeyboardEvent)` — const, line 1260
- `const target = event.target` — const, line 1263
- `const openAnnotationNote = useCallback((annotationId: string)` — const, line 1272
- `const target = annotations.find((a)` — const, line 1273
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1285
- `const sel = window.getSelection()` — const, line 1286
- `const container = bodyRef.current` — const, line 1287
- `const range = sel.getRangeAt(0)` — const, line 1289
- `const nodes: Array<` — const, line 1290
- `const seen = new Set<string>()` — const, line 1291
- `const spanId = el.dataset.spanId` — const, line 1293
- `let intersects = false` — let, line 1295
- `const sub = document.createRange()` — const, line 1302
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1310
- `const block = renderBlocksBySpan.get(spanId)` — const, line 1315
- `const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1325
- `const cancelIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1326
- `const selectionSpanIds = useMemo( ()` — const, line 1327
- `const intentBox = useIntentBox(` — const, line 1331
- `const openActiveRail = useCallback(()` — const, line 1345
- `const activeCtl = useActiveReading(` — const, line 1349
- `const libraryCtl = useLibraryAsk(` — const, line 1358
- `const keptCtl = useKeptComparisons(` — const, line 1360
- `const pdfMarks = (): ReadonlyMap<string, ReactNode> | null` — const, line 1364
- `const cues = cueMarksFor("pdf")` — const, line 1365
- `const merged = new Map<string, ReactNode>(cues ?? [])` — const, line 1367
- `const cue = merged.get(spanId)` — const, line 1369
- `const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null)` — const, line 1375
- `const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint)` — const, line 1377
- `const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false)` — const, line 1378
- `const closeLibrary = useCallback(()` — const, line 1385
- `const onKey = (event: KeyboardEvent)` — const, line 1392
- `const onMouseUp = useCallback(()` — const, line 1403
- `const sel = window.getSelection()` — const, line 1404
- `const quote = sel.toString().replace(/\s+/g, " ").trim()` — const, line 1406
- `const nodes = collectSelectionNodes()` — const, line 1408
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1437
- `const domDragRef = useRef<` — const, line 1438
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1440
- `const host = bodyRef.current` — const, line 1441
- `const rect = host.getBoundingClientRect()` — const, line 1443
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1447
- `const target = event.target as Node` — const, line 1451
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1453
- `const domDrafting = domDraft !== null` — const, line 1465
- `const rectFrom = (drag:` — const, line 1468
- `const onMove = (event: MouseEvent)` — const, line 1474
- `const drag = domDragRef.current` — const, line 1475
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1477
- `const onUp = (event: MouseEvent)` — const, line 1480
- `const drag = domDragRef.current` — const, line 1481
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1485
- `const rect = rectFrom(drag, point)` — const, line 1487
- `const next = [...domBoxesRef.current, rect]` — const, line 1490
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1507
- `const host = bodyRef.current` — const, line 1508
- `const hostRect = host.getBoundingClientRect()` — const, line 1510
- `const clientBoxes = boxes.map((b)` — const, line 1511
- `const nodes: Array<` — const, line 1517
- `const seen = new Set<string>()` — const, line 1518
- `const spanId = el.dataset.spanId` — const, line 1520
- `const elRect = el.getBoundingClientRect()` — const, line 1522
- `const touches = clientBoxes.some( (b)` — const, line 1523
- `const words: string[] = []` — const, line 1527
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 1528
- `const text = node as Text` — const, line 1530
- `const wordPattern = /\S+/g` — const, line 1531
- `let match: RegExpExecArray | null` — let, line 1532
- `const range = document.createRange()` — const, line 1534
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 1537
- `const cx = (Math.min(...rects.map((r)` — const, line 1539
- `const cy = (Math.min(...rects.map((r)` — const, line 1540
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 1544
- `const commitDomBoxes = useCallback(()` — const, line 1553
- `const boxes = domBoxesRef.current` — const, line 1554
- `const nodes = resolveDomBoxes(boxes)` — const, line 1556
- `const quote = nodes.map((n)` — const, line 1562
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 1571
- `const clearDomBoxes = ()` — const, line 1579
- `const onKeyDown = (event: KeyboardEvent)` — const, line 1585
- `const onKeyUp = (event: KeyboardEvent)` — const, line 1590
- `const onBlur = ()` — const, line 1596
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 1618
- `const point = domPointFromClient(request.x, request.y)` — const, line 1620
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 1621
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 1642
- `const retryRequest = useCallback(async (requestId: string)` — const, line 1655
- `const optimisticSegments = useCallback( (nodes: string | Array<string |` — const, line 1669
- `const list = Array.isArray(nodes) ? nodes : [nodes]` — const, line 1671
- `const spanId = typeof node === "string" ? node : node.spanId` — const, line 1673
- `const geometry = pdfView?.blocks.find((b)` — const, line 1674
- `const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number" ?` — const, line 1675
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 1687
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 1691
- `const quotedNodes = (()` — const, line 1696
- `const multi = collectSelectionNodes()` — const, line 1699
- `const optimisticIds = quotedNodes ?? [target.spanId]` — const, line 1702
- `const nodes = quotedNodes ?? [` — const, line 1712
- `const receipt = await api.readerCapture(` — const, line 1713
- `const handler = (event: KeyboardEvent)` — const, line 1740
- `const clearSelection = useCallback(()` — const, line 1752
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 1764
- `const segment = a.segments.find((s)` — const, line 1766
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1773
- `const alsoKeyRef = useRef<()` — const, line 1783
- `const onKey = (event: KeyboardEvent)` — const, line 1791
- `const target = event.target` — const, line 1794
- `const tabs: ReaderRailTab[] = ["guide", "ask", "notes"]` — const, line 1796
- `const askRequestSeen = useRef(askRequest)` — const, line 1830
- `const revealAskRef = useRef<()` — const, line 1832
- `const startCompareRef = useRef<(request: CompareRequest)` — const, line 1857
- `const request = compareWaitsForWork` — const, line 1865
- `const invokePreset = useCallback( // RW1b: the intent box passes its own words as the annotation's learner // text, and names the intention and entry in the funnel event. async (preset: string, learnerTextOverride?: string, meta?: Record<string, unknown>): Pr…` — const, line 1872
- `const note_ = learnerTextOverride ?? note` — const, line 1877
- `const nodes = selectionNodes(selection)` — const, line 1878
- `const editedText = selection.editedText?.trim()` — const, line 1879
- `const receipt = await api.readerInvokePreset(` — const, line 1891
- `const drained = await api.readerDrainOutbox()` — const, line 1915
- `const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>): Promise<string | null>` — const, line 1938
- `const note_ = learnerTextOverride ?? note` — const, line 1940
- `const nodes = selectionNodes(selection)` — const, line 1941
- `const receipt = await api.readerCapture(` — const, line 1953
- `const pauseArc = useCallback(async ()` — const, line 1981
- `const next = await api.readerArc(` — const, line 1985
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 1992
- `const next = await api.readerArc(` — const, line 1997
- `const importJobRef = useRef<` — const, line 2009
- `const importExercise = useCallback(async (): Promise<string | null>` — const, line 2010
- `const nodes = selectionNodes(selection)` — const, line 2012
- `const editedText = selection.editedText?.trim()` — const, line 2013
- `const receipt = await api.readerImportExercise(` — const, line 2016
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 2049
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 2050
- `const timer = setInterval(async ()` — const, line 2054
- `const status = await api.readerExerciseImportStatus(` — const, line 2056
- `const job = importJobRef.current` — const, line 2057
- `const waited = Date.now() - job.startedAt` — const, line 2060
- `const saveOwnQuestion = useCallback(async ()` — const, line 2087
- `const saved = await api.readerAuthorQA(` — const, line 2095
- `const runCoach = useCallback(async ()` — const, line 2116
- `const lint = await api.readerCoachLint(` — const, line 2119
- `const changeMode = useCallback( async (next: string)` — const, line 2130
- `const previous = mode` — const, line 2132
- `const version = ++modeSaveVersionRef.current` — const, line 2135
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 2146
- `const answerModeNext = next as ReaderAnswerMode` — const, line 2148
- `const previous = answerMode` — const, line 2149
- `const version = ++answerModeSaveVersionRef.current` — const, line 2152
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 2167
- `const renderInquiryTop = useCallback((root: ReaderExchange)` — const, line 2182
- `const line = reconnect && reconnect.rootId === root.id && !muted ? ( <ReconnectLine placement="rail" question=` — const, line 2185
- `const check = inquiryChecks[root.id]` — const, line 2195
- `const inlineReconnect = reconnect && reconnect.inline && !muted ? ( <ReconnectLine placement="inline" question=` — const, line 2223
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 2234
- `const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">): Promise<OpenOutcome>` — const, line 2252
- `const card = (library ?? []).find((candidate)` — const, line 2257
- `const spanId = readingSpan ?? activeSpan` — const, line 2260
- `const compareFoundSection = (hit: CorrespondentSectionDto)` — const, line 2274
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2276
- `const hideAlsoInBooks = (scope: "book" | "everywhere")` — const, line 2298
- `const before = alsoPrefs ??` — const, line 2300
- `const base = contract` — const, line 2307
- `const makeExplorable = (target: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, origin: "library" | "tutor", offerRef: string): Promise<ExplorableOutcome>` — const, line 2324
- `let settle: (outcome: ExplorableOutcome)` — let, line 2331
- `const settled = new Promise<ExplorableOutcome>((resolve)` — const, line 2332
- `const press: OfferedPress =` — const, line 2333
- `const peekWorkbenchPassage = (spanId: string, target?: PassageTarget)` — const, line 2352
- `const exerciseSettings = libraryCtl.enabled ? contract?.libraryExercises ?? null : null` — const, line 2363
- `const exerciseCard = (sourceId: string | null)` — const, line 2364
- `const useExercise = (candidate: ExerciseCandidate)` — const, line 2368
- `const card = exerciseCard(candidate.sourceId ?? render?.sourceId ?? null)` — const, line 2369
- `const openExerciseInBook = (candidate: ExerciseCandidate)` — const, line 2378
- `const sourceId = candidate.sourceId ?? render?.sourceId ?? null` — const, line 2379
- `const exerciseProps: LibraryExercisesProps | null = exerciseSettings ?` — const, line 2382
- `const pickLibraryPagePractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 2396
- `const hit = libraryCtl.state?.ask.value?.hits[0]` — const, line 2397
- `const card = hit ? (library ?? []).find((candidate)` — const, line 2398
- `const readySources = library ?? []` — const, line 2439
- `const useShelf = Boolean(shelf) && !sidecarDown` — const, line 2441
- `const card = (library ?? []).find((candidate)` — const, line 2497
- `const card = (library ?? []).find((c)` — const, line 2517
- `const receiptId = searchResults.retrievalReceiptId` — const, line 2523
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 2568
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 2569
- `const wbActive = wbCtl.active` — const, line 2612
- `const wbStacked = working && wbCtl.narrow` — const, line 2613
- `const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible)` — const, line 2616
- `const wbSourceShown = !wbStacked || wbCtl.sheetOpen` — const, line 2617
- `const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry)` — const, line 2618
- `const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>()` — const, line 2619
- `const first = entry.spanIds[0]` — const, line 2621
- `const wbLabel = (stem: string)` — const, line 2624
- `const title = problemTitle(stem)` — const, line 2625
- `const tryPathExercise = (exercise: ReadingPathExerciseDto)` — const, line 2630
- `const workThroughSelection = ()` — const, line 2638
- `const nodes = selectionNodes(selection)` — const, line 2640
- `const editedText = selection.editedText?.trim()` — const, line 2641
- `const foldBlocks = contract?.activeReading?.foldBlocks ?? 3` — const, line 2658
- `const localFold = (spanIds: string[]): string[]` — const, line 2659
- `const positions = spanIds.map((spanId)` — const, line 2660
- `const last = Math.max(...positions)` — const, line 2662
- `const meta =` — const, line 2668
- `const effect = action.effect` — const, line 2669
- `const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null` — const, line 2715
- `const request: CompareRequest =` — const, line 2716
- `const region = selection?.region ?` — const, line 2739
- `const words = text?.trim()` — const, line 2740
- `const showMeFromAsk = ()` — const, line 2754
- `const goal = question.trim()` — const, line 2755
- `const home = parentExchange?.spanId ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan` — const, line 2756
- `const key = `show_me:$` — const, line 2758
- `const settle = (patch: Partial<ShowMeLine>)` — const, line 2761
- `const kind = cancel.action.effect.kind` — const, line 2778
- `const annotationId = handle.annotationId` — const, line 2785
- `const batchId = handle.importBatchId` — const, line 2797
- `const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number)` — const, line 2807
- `const spanId = wbCtl.close(session,` — const, line 2809
- `const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 2815
- `const card = openCardRef.current` — const, line 2816
- `const resumeMark = (spanId: string | null | undefined)` — const, line 2820
- `const entry = spanId ? wbResumeBySpan.get(spanId) : undefined` — const, line 2821
- `const verb = entry.status === "abandoned" ? "Reopen" : "Resume"` — const, line 2823
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 3084
- `const active = activeSpan === block.spanId` — const, line 3085
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 3086
- `const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null` — const, line 3087
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 3088
- `const endQuestionAvailable = Boolean(endSection && endSection.question?.readingPhase === "after_section" && offeredCheckSections.has(endSection.id))` — const, line 3090
- `const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId))` — const, line 3094
- `const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""))` — const, line 3095
- `const offerSection = endSection && !muted && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 3096
- `const sel = window.getSelection()` — const, line 3115
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 3116
- `const active = railTab === tab` — const, line 3249
- `const waiting = tab === "guide" && pendingQuickCheckCount > 0` — const, line 3253
- `const marked = tab === "ask" && askTabMarked && !active` — const, line 3254
- `const params = (action.params ??` — const, line 3396

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`; references `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CorrespondentSectionDto`, `FigurePassageDto`, `FigureViewDto`, `LibraryAskEntry`, `LibraryHitDto`, `PassageTarget`, `ProposedItemDto`, `ReaderAnnotationPlacementDto`, `ReaderAnswerMode`, `ReaderArcDto`, `ReaderCoachLintDto`, `ReaderCueDto`, `ReaderDisposition`, `ReaderGuidePlanDto`, `ReaderGuideSectionDto`, `ReaderIntentActionDto`, `ReaderPdfViewDto`, `ReaderPromptContractDto`, `ReaderRenderBlockDto`, `ReaderRenderViewDto`, `ReaderSourceSearchDto`, `ReaderWatchPlanDto`, `ReadingPathExerciseDto`, `SourceLibraryCard`
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
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
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
- [[Reference/Desktop/TypeScript/screens/reader/ReaderAskBranches|src/screens/reader/ReaderAskBranches.tsx]] — import-or-re-export; imports `ReaderExchange`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderWorkingPosture|src/screens/reader/ReaderWorkingPosture.tsx]] — import-or-re-export; imports `ReaderWorkingPosture`
- [[Reference/Desktop/TypeScript/screens/reader/ReadingPathCard|src/screens/reader/ReadingPathCard.tsx]] — import-or-re-export; imports `ReadingPathCard`
- [[Reference/Desktop/TypeScript/screens/reader/RecapCard|src/screens/reader/RecapCard.tsx]] — import-or-re-export; imports `RecapCard`
- [[Reference/Desktop/TypeScript/screens/reader/ReconnectLine|src/screens/reader/ReconnectLine.tsx]] — import-or-re-export; imports `ReconnectLine`
- [[Reference/Desktop/TypeScript/screens/reader/TutorOffers|src/screens/reader/TutorOffers.tsx]] — import-or-re-export; imports `createTutorOfferStore`
- [[Reference/Desktop/TypeScript/screens/reader/WrapUpPanel|src/screens/reader/WrapUpPanel.tsx]] — import-or-re-export; imports `WrapUpPanel`
- [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]] — import-or-re-export; imports `WatchPanelHandle`, `YouTubeWatchPanel`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export; imports `activitySince`, `learnerActivitySnapshot`, `logReaderAction`, `logReaderActivity`, `newActivityId`
- [[Reference/Desktop/TypeScript/screens/reader/authoredQuestion|src/screens/reader/authoredQuestion.ts]] — import-or-re-export; imports `AuthoredQuestionStatus`
- [[Reference/Desktop/TypeScript/screens/reader/bareAlt|src/screens/reader/bareAlt.ts]] — import-or-re-export; imports `useBareAltClear`
- [[Reference/Desktop/TypeScript/screens/reader/compareKeepContext|src/screens/reader/compareKeepContext.ts]] — import-or-re-export; imports `CompareKeepContext`
- [[Reference/Desktop/TypeScript/screens/reader/cues|src/screens/reader/cues.ts]] — import-or-re-export; imports `PdfPageLayout`
- [[Reference/Desktop/TypeScript/screens/reader/exerciseCandidates (ts)|src/screens/reader/exerciseCandidates.ts]] — import-or-re-export; imports `ExerciseCandidate`, `ReaderWorkbenchExercise`, `exerciseOpenRequest`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export; imports `FiguresUnder`
- [[Reference/Desktop/TypeScript/screens/reader/figures/showMe|src/screens/reader/figures/showMe.ts]] — import-or-re-export; imports `ShowMeLine`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export; imports `FigureRequestOutcome`, `useFigures`
- [[Reference/Desktop/TypeScript/screens/reader/guidePlan|src/screens/reader/guidePlan.ts]] — import-or-re-export; imports `readGuidePlan`
- [[Reference/Desktop/TypeScript/screens/reader/readerCache|src/screens/reader/readerCache.ts]] — import-or-re-export; imports `cachedSourceRead`
- [[Reference/Desktop/TypeScript/screens/reader/readerKeys|src/screens/reader/readerKeys.ts]] — import-or-re-export; imports `readerKeyBarKeys`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `AnnotationSegment`, `MarginAnnotation`, `ReaderSelection`, `askGroundingSpans`, `clip`, `groundingProtected`, `placedSpanIds`, `selectionNodes`, `selectionProtected`
- [[Reference/Desktop/TypeScript/screens/reader/readingPath|src/screens/reader/readingPath.ts]] — import-or-re-export; imports `readingPathRefreshKey`
- [[Reference/Desktop/TypeScript/screens/reader/readingPosition|src/screens/reader/readingPosition.ts]] — import-or-re-export; imports `ReadingPosition`
- [[Reference/Desktop/TypeScript/screens/reader/recapCopy|src/screens/reader/recapCopy.ts]] — import-or-re-export; imports `RECAP_COPY`
- [[Reference/Desktop/TypeScript/screens/reader/returnStack|src/screens/reader/returnStack.ts]] — import-or-re-export; imports `stackGoTo`
- [[Reference/Desktop/TypeScript/screens/reader/searchBasis|src/screens/reader/searchBasis.ts]] — import-or-re-export; imports `searchBasisLabel`
- [[Reference/Desktop/TypeScript/screens/reader/useActiveReading|src/screens/reader/useActiveReading.ts]] — import-or-re-export; imports `useActiveReading`
- [[Reference/Desktop/TypeScript/screens/reader/useIntentBox|src/screens/reader/useIntentBox.ts]] — import-or-re-export; imports `IntentCancel`, `IntentRunHandle`, `IntentRunHow`, `useIntentBox`
- [[Reference/Desktop/TypeScript/screens/reader/useKeptComparisons|src/screens/reader/useKeptComparisons.ts]] — import-or-re-export; imports `useKeptComparisons`
- [[Reference/Desktop/TypeScript/screens/reader/useLibraryAsk|src/screens/reader/useLibraryAsk.ts]] — import-or-re-export; imports `CompareRequest`, `SCOPE_COPY`, `useLibraryAsk`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] — import-or-re-export; imports `CueCheckMeRequest`, `CueRequestOrigin`, `useReaderCues`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export; imports `useReaderInquiry`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderRecap|src/screens/reader/useReaderRecap.ts]] — import-or-re-export; imports `useReaderRecap`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderRequests|src/screens/reader/useReaderRequests.ts]] — import-or-re-export; imports `useReaderRequests`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderVisit|src/screens/reader/useReaderVisit.ts]] — import-or-re-export; imports `useReaderVisit`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderWorkbench|src/screens/reader/useReaderWorkbench.ts]] — import-or-re-export; imports `ReaderWorkbenchProps`, `useReaderWorkbench`
- [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]] — import-or-re-export; imports `useReadingProgress`
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
- [apps/learnloop-tauri/src/screens/reader/rw1bReview.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/rw1bReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/recapSwitchOff.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/recapSwitchOff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/readingPathsSwitchOff.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/readingPathsSwitchOff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

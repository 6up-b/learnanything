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
source_commit: "1bcb185da0d178c96a5d6f4a6a3cb2bfe50f6c1e"
source_commit_timestamp: "2026-11-01T00:05:01-04:00"
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
| Source lines | 3963 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `1bcb185da0d178c96a5d6f4a6a3cb2bfe50f6c1e` |
| Commit timestamp | `2026-11-01T00:05:01-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]]

## Public API

- `export interface ReaderOpenSource` — interface, line 217
- `export interface ReaderCheckMeRequest extends CueCheckMeRequest` — interface, line 228
- `export type ReaderExerciseRequest = ReaderWorkbenchExercise &` — type, line 238
- `export function ReaderScreen(` — function, line 240

## Internal implementation anchors

- `type AnnotationSegment, type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 131
- `type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 132
- `type ReaderSelection, } from "./reader/readerShared"` — type, line 133
- `const NO_SECTIONS: never[] = []` — const, line 137
- `const READER_MODE_OPTIONS = [` — const, line 138
- `const TAG_ACTIONS: Array<` — const, line 148
- `const WHOLE_BLOCK_QUOTE = "(whole block)"` — const, line 156
- `type ReaderRailTab = "guide" | "ask" | "notes"` — type, line 158
- `const HEALTH_COLOR: Record<string, "green" | "amber" | "pink" | "slate"> =` — const, line 160
- `const FURNITURE_BLOCK_TYPES = new Set(["PageHeader", "PageFooter", "TableOfContents"])` — const, line 169
- `type OpenOutcome = "opened" | "preparing" | "not_opened"` — type, line 172
- `interface OfferedPress` — interface, line 176
- `const OFFER_OUTCOME: Record<FigureRequestOutcome, ExplorableOutcome> =` — const, line 187
- `const BADGED_HEALTH = new Set(["suspect", "failed"])` — const, line 193
- `interface RemovedAnnotation` — interface, line 197
- `const UNDO_REMOVE_MS = 10_000` — const, line 207
- `function newKey(): string` — function, line 209
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 283
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 287
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 296
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 297
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 298
- `const openingRef = useRef<string | null>(null)` — const, line 304
- `const askPanelOn = algoConfig().ask !== null` — const, line 325
- `const storedStyle = useStoredHelpStyle()` — const, line 326
- `const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen` — const, line 327
- `const pdfViewRequestRef = useRef(0)` — const, line 349
- `const sourceEpochRef = useRef(0)` — const, line 380
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 391
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 392
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 393
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 394
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 395
- `const modeSaveVersionRef = useRef(0)` — const, line 396
- `const answerModeSaveVersionRef = useRef(0)` — const, line 397
- `const enabled = contract?.readerEnabled ?? true` — const, line 413
- `const inquiry = contract?.inquiryEnabled === true` — const, line 416
- `const muted = inquiry && mode === "skim"` — const, line 419
- `const intentContract = inquiry && !offline ? contract?.intent ?? null : null` — const, line 422
- `const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading)` — const, line 423
- `const figuresCtl = useFigures(` — const, line 425
- `const figureOffersOn = Boolean(contract?.figures?.offers) && !offline` — const, line 430
- `const showMeOn = Boolean(contract?.figures?.showMe) && !offline` — const, line 434
- `const waitingOfferRef = useRef<OfferedPress | null>(null)` — const, line 440
- `const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome)` — const, line 445
- `const press = offeredFigure` — const, line 452
- `const open = render?.extractionId ?? null` — const, line 454
- `const readerTutor = contract?.readerTutor ?? null` — const, line 477
- `const askWorkbenchSessionRef = useRef<string | null>(null)` — const, line 479
- `const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true` — const, line 484
- `const askPersonalizedRef = useRef<boolean | null>(null)` — const, line 485
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 491
- `const renderBlocksBySpan = useMemo( ()` — const, line 495
- `const visit = useReaderVisit(` — const, line 501
- `const showGuideRail = useCallback(()` — const, line 507
- `const progress = useReadingProgress(` — const, line 511
- `const doseVisitId = useCallback(()` — const, line 528
- `const refreshAnnotations = useCallback(async ()` — const, line 530
- `const epoch = sourceEpochRef.current` — const, line 532
- `const result = await cachedSourceRead( render.sourceId, ["reader_source_annotations", render.sourceId, render.extractionId], ()` — const, line 536
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 543
- `const version = (r.version as Record<string, unknown>) ??` — const, line 546
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 547
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 548
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 549
- `const placement = r.placement as ReaderAnnotationPlacementDto | undefined` — const, line 550
- `let page: number | null = null` — let, line 560
- `let bbox: number[] | null = null` — let, line 561
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 563
- `const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?:` — const, line 581
- `const openCardRef = useRef<SourceLibraryCard | null>(null)` — const, line 605
- `const openExtractionRef = useRef<string | null>(null)` — const, line 607
- `const reloadGuidePlan = useCallback(async ()` — const, line 609
- `const extractionId = render.extractionId` — const, line 611
- `const plan = await readGuidePlan(render.sourceId, extractionId,` — const, line 613
- `const spanOrder = useMemo( ()` — const, line 626
- `const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none"` — const, line 630
- `const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 633
- `const card = openCardRef.current` — const, line 634
- `const wbCtl = useReaderWorkbench(` — const, line 640
- `const working = wbCtl.active !== null` — const, line 647
- `const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline` — const, line 651
- `const alsoHidden = alsoPrefs ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId)) : Boolean(contract?.correspondence?.hiddenEverywhere) || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.so…` — const, line 656
- `const peekCrumbShown = alsoPeek ?? findPeek` — const, line 666
- `const pathRefreshKey = readingPathRefreshKey(` — const, line 681
- `const tryFirstRef = useRef<((spanId: string)` — const, line 695
- `const cueCtl = useReaderCues(` — const, line 696
- `const recapCtl = useReaderRecap(` — const, line 708
- `const recapShown = Boolean(recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working)` — const, line 722
- `const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip")` — const, line 733
- `const root = history.find((entry)` — const, line 734
- `const recapRevisited = useCallback((rootId: string)` — const, line 747
- `const root = history.find((entry)` — const, line 748
- `const recapRevisit = useCallback(async (rootId: string)` — const, line 751
- `const root = history.find((entry)` — const, line 752
- `const recapOpenInquiry = useCallback((rootId: string, spanId: string)` — const, line 758
- `const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch")` — const, line 761
- `const cueMarksFor = (markSurface: "pdf" | "watch")` — const, line 781
- `let cancelled = false` — let, line 790
- `const scroller = railRef.current` — const, line 823
- `const clamp = ()` — const, line 825
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 826
- `const observer = new ResizeObserver(clamp)` — const, line 829
- `const query = librarySearch.trim()` — const, line 840
- `let cancelled = false` — let, line 847
- `const timer = window.setTimeout(()` — const, line 850
- `const resetSourceState = useCallback(()` — const, line 873
- `const openSource = useCallback( async ( card: SourceLibraryCard, jumpSpan?: string, // jumpReading: the reading jumpSpan was found on (a search hit, a // return)` — const, line 922
- `const handoff = options.handoff ?? null` — const, line 931
- `const view = await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 949
- `const pdfRequest = ++pdfViewRequestRef.current` — const, line 996
- `const current = ()` — const, line 997
- `const openFixture = useCallback(()` — const, line 1032
- `const backToLibrary = useCallback(()` — const, line 1040
- `const spanId = readingSpan ?? activeSpan` — const, line 1044
- `const section = guidePlan?.sections.find((candidate)` — const, line 1045
- `const resumedRef = useRef(false)` — const, line 1063
- `const activeBlock = useMemo(()` — const, line 1075
- `const pdfHighlights: PdfHighlight[] = useMemo(()` — const, line 1084
- `const list: PdfHighlight[] = []` — const, line 1085
- `const base =` — const, line 1088
- `const placed = highlightFromPlacement(base, a.placement)` — const, line 1090
- `const segments = a.segments.flatMap((s)` — const, line 1095
- `const annotatedSpans = useMemo( ()` — const, line 1102
- `const boundaryBlock = useMemo(()` — const, line 1106
- `const revealedPassages = useMemo(()` — const, line 1108
- `const revealed = new Set(revealedSections)` — const, line 1109
- `const map = new Map<string,` — const, line 1110
- `const revealedGuidanceSpans = useMemo(()` — const, line 1119
- `const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null` — const, line 1124
- `const protectedSelection = selectionProtected(protection, selection)` — const, line 1125
- `const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1126
- `const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan))` — const, line 1130
- `const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1131
- `const editCaptureText = useCallback((text: string)` — const, line 1136
- `const resetCaptureText = useCallback(()` — const, line 1139
- `const saveAnnotationEdit = useCallback(async ()` — const, line 1151
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 1173
- `const result = await api.readerReanchor(` — const, line 1177
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1194
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1217
- `const target = annotations.find((a)` — const, line 1218
- `const reading = render ?` — const, line 1219
- `const epoch = sourceEpochRef.current` — const, line 1220
- `const undoRemove = useCallback(async ()` — const, line 1235
- `const last = removed` — const, line 1236
- `const epoch = sourceEpochRef.current` — const, line 1242
- `const result = await api.readerRestoreAnnotation(` — const, line 1244
- `const timer = window.setTimeout(()` — const, line 1257
- `const onKey = (event: KeyboardEvent)` — const, line 1263
- `const target = event.target` — const, line 1266
- `const openAnnotationNote = useCallback((annotationId: string)` — const, line 1275
- `const target = annotations.find((a)` — const, line 1276
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1288
- `const sel = window.getSelection()` — const, line 1289
- `const container = bodyRef.current` — const, line 1290
- `const range = sel.getRangeAt(0)` — const, line 1292
- `const nodes: Array<` — const, line 1293
- `const seen = new Set<string>()` — const, line 1294
- `const spanId = el.dataset.spanId` — const, line 1296
- `let intersects = false` — let, line 1298
- `const sub = document.createRange()` — const, line 1305
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1313
- `const block = renderBlocksBySpan.get(spanId)` — const, line 1318
- `const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1328
- `const cancelIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1329
- `const selectionSpanIds = useMemo( ()` — const, line 1330
- `const intentBox = useIntentBox(` — const, line 1334
- `const openActiveRail = useCallback(()` — const, line 1348
- `const activeCtl = useActiveReading(` — const, line 1352
- `const libraryCtl = useLibraryAsk(` — const, line 1361
- `const keptCtl = useKeptComparisons(` — const, line 1363
- `const pdfMarks = (): ReadonlyMap<string, ReactNode> | null` — const, line 1367
- `const cues = cueMarksFor("pdf")` — const, line 1368
- `const merged = new Map<string, ReactNode>(cues ?? [])` — const, line 1370
- `const cue = merged.get(spanId)` — const, line 1372
- `const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null)` — const, line 1378
- `const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint)` — const, line 1380
- `const sbs = useSideBySide(` — const, line 1382
- `const node = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1390
- `const sbsPanes = sbs.panes && !comparing` — const, line 1403
- `const sbsPanesRef = useRef(false)` — const, line 1404
- `const sbsShownRef = useRef(false)` — const, line 1409
- `const sbsRef = useRef(sbs)` — const, line 1411
- `const sbsEscBusyRef = useRef(false)` — const, line 1414
- `const sbsPaneRef = useRef<HTMLDivElement | null>(null)` — const, line 1416
- `const sbsRowRef = useRef<HTMLDivElement | null>(null)` — const, line 1422
- `const startSbsResize = (event: ReactPointerEvent<HTMLDivElement>)` — const, line 1423
- `const row = sbsRowRef.current` — const, line 1424
- `const rect = row.getBoundingClientRect()` — const, line 1427
- `const move = (moved: PointerEvent)` — const, line 1428
- `const up = ()` — const, line 1431
- `const touchMain = ()` — const, line 1443
- `const onKey = (event: KeyboardEvent)` — const, line 1452
- `const target = event.target` — const, line 1454
- `const ctl = sbsRef.current` — const, line 1456
- `const open = ctl.panes || ctl.sheet` — const, line 1457
- `const shown = sbsShownRef.current` — const, line 1458
- `const mod = event.ctrlKey || event.metaKey` — const, line 1459
- `const side = sbsPaneRef.current` — const, line 1469
- `const inSide = target instanceof Element && Boolean(target.closest("[data-side-by-side-pane]"))` — const, line 1470
- `const inMain = target instanceof Node && Boolean(bodyRef.current?.contains(target))` — const, line 1476
- `const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false)` — const, line 1486
- `const closeLibrary = useCallback(()` — const, line 1493
- `const onKey = (event: KeyboardEvent)` — const, line 1500
- `const onMouseUp = useCallback(()` — const, line 1511
- `const sel = window.getSelection()` — const, line 1512
- `const quote = sel.toString().replace(/\s+/g, " ").trim()` — const, line 1514
- `const nodes = collectSelectionNodes()` — const, line 1516
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1545
- `const domDragRef = useRef<` — const, line 1546
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1548
- `const host = bodyRef.current` — const, line 1549
- `const rect = host.getBoundingClientRect()` — const, line 1551
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1555
- `const target = event.target as Node` — const, line 1559
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1561
- `const domDrafting = domDraft !== null` — const, line 1573
- `const rectFrom = (drag:` — const, line 1576
- `const onMove = (event: MouseEvent)` — const, line 1582
- `const drag = domDragRef.current` — const, line 1583
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1585
- `const onUp = (event: MouseEvent)` — const, line 1588
- `const drag = domDragRef.current` — const, line 1589
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1593
- `const rect = rectFrom(drag, point)` — const, line 1595
- `const next = [...domBoxesRef.current, rect]` — const, line 1598
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1615
- `const host = bodyRef.current` — const, line 1616
- `const hostRect = host.getBoundingClientRect()` — const, line 1618
- `const clientBoxes = boxes.map((b)` — const, line 1619
- `const nodes: Array<` — const, line 1625
- `const seen = new Set<string>()` — const, line 1626
- `const spanId = el.dataset.spanId` — const, line 1628
- `const elRect = el.getBoundingClientRect()` — const, line 1630
- `const touches = clientBoxes.some( (b)` — const, line 1631
- `const words: string[] = []` — const, line 1635
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 1636
- `const text = node as Text` — const, line 1638
- `const wordPattern = /\S+/g` — const, line 1639
- `let match: RegExpExecArray | null` — let, line 1640
- `const range = document.createRange()` — const, line 1642
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 1645
- `const cx = (Math.min(...rects.map((r)` — const, line 1647
- `const cy = (Math.min(...rects.map((r)` — const, line 1648
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 1652
- `const commitDomBoxes = useCallback(()` — const, line 1661
- `const boxes = domBoxesRef.current` — const, line 1662
- `const nodes = resolveDomBoxes(boxes)` — const, line 1664
- `const quote = nodes.map((n)` — const, line 1670
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 1679
- `const clearDomBoxes = ()` — const, line 1687
- `const onKeyDown = (event: KeyboardEvent)` — const, line 1693
- `const onKeyUp = (event: KeyboardEvent)` — const, line 1698
- `const onBlur = ()` — const, line 1704
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 1726
- `const point = domPointFromClient(request.x, request.y)` — const, line 1728
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 1729
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 1750
- `const retryRequest = useCallback(async (requestId: string)` — const, line 1763
- `const optimisticSegments = useCallback( (nodes: string | Array<string |` — const, line 1777
- `const list = Array.isArray(nodes) ? nodes : [nodes]` — const, line 1779
- `const spanId = typeof node === "string" ? node : node.spanId` — const, line 1781
- `const geometry = pdfView?.blocks.find((b)` — const, line 1782
- `const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number" ?` — const, line 1783
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 1795
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 1799
- `const quotedNodes = (()` — const, line 1804
- `const multi = collectSelectionNodes()` — const, line 1807
- `const optimisticIds = quotedNodes ?? [target.spanId]` — const, line 1810
- `const nodes = quotedNodes ?? [` — const, line 1820
- `const receipt = await api.readerCapture(` — const, line 1821
- `const handler = (event: KeyboardEvent)` — const, line 1848
- `const clearSelection = useCallback(()` — const, line 1860
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 1872
- `const segment = a.segments.find((s)` — const, line 1874
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1881
- `const alsoKeyRef = useRef<()` — const, line 1891
- `const onKey = (event: KeyboardEvent)` — const, line 1899
- `const target = event.target` — const, line 1902
- `const tabs: ReaderRailTab[] = ["guide", "ask", "notes"]` — const, line 1904
- `const askRequestSeen = useRef(askRequest)` — const, line 1942
- `const revealAskRef = useRef<()` — const, line 1944
- `const startCompareRef = useRef<(request: CompareRequest)` — const, line 1969
- `const request = compareWaitsForWork` — const, line 1977
- `const invokePreset = useCallback( // RW1b: the intent box passes its own words as the annotation's learner // text, and names the intention and entry in the funnel event. async (preset: string, learnerTextOverride?: string, meta?: Record<string, unknown>): Pr…` — const, line 1984
- `const note_ = learnerTextOverride ?? note` — const, line 1989
- `const nodes = selectionNodes(selection)` — const, line 1990
- `const editedText = selection.editedText?.trim()` — const, line 1991
- `const receipt = await api.readerInvokePreset(` — const, line 2003
- `const drained = await api.readerDrainOutbox()` — const, line 2027
- `const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>): Promise<string | null>` — const, line 2050
- `const note_ = learnerTextOverride ?? note` — const, line 2052
- `const nodes = selectionNodes(selection)` — const, line 2053
- `const receipt = await api.readerCapture(` — const, line 2065
- `const pauseArc = useCallback(async ()` — const, line 2093
- `const next = await api.readerArc(` — const, line 2097
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 2104
- `const next = await api.readerArc(` — const, line 2109
- `const importJobRef = useRef<` — const, line 2121
- `const importExercise = useCallback(async (): Promise<string | null>` — const, line 2122
- `const nodes = selectionNodes(selection)` — const, line 2124
- `const editedText = selection.editedText?.trim()` — const, line 2125
- `const receipt = await api.readerImportExercise(` — const, line 2128
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 2161
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 2162
- `const timer = setInterval(async ()` — const, line 2166
- `const status = await api.readerExerciseImportStatus(` — const, line 2168
- `const job = importJobRef.current` — const, line 2169
- `const waited = Date.now() - job.startedAt` — const, line 2172
- `const saveOwnQuestion = useCallback(async ()` — const, line 2199
- `const saved = await api.readerAuthorQA(` — const, line 2207
- `const runCoach = useCallback(async ()` — const, line 2228
- `const lint = await api.readerCoachLint(` — const, line 2231
- `const changeMode = useCallback( async (next: string)` — const, line 2242
- `const previous = mode` — const, line 2244
- `const version = ++modeSaveVersionRef.current` — const, line 2247
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 2258
- `const answerModeNext = next as ReaderAnswerMode` — const, line 2260
- `const previous = answerMode` — const, line 2261
- `const version = ++answerModeSaveVersionRef.current` — const, line 2264
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 2279
- `const renderInquiryTop = useCallback((root: ReaderExchange)` — const, line 2294
- `const line = reconnect && reconnect.rootId === root.id && !muted ? ( <ReconnectLine placement="rail" question=` — const, line 2297
- `const check = inquiryChecks[root.id]` — const, line 2307
- `const inlineReconnect = reconnect && reconnect.inline && !muted ? ( <ReconnectLine placement="inline" question=` — const, line 2335
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 2346
- `const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">): Promise<OpenOutcome>` — const, line 2364
- `const card = (library ?? []).find((candidate)` — const, line 2369
- `const spanId = readingSpan ?? activeSpan` — const, line 2372
- `const compareFoundSection = (hit: CorrespondentSectionDto)` — const, line 2386
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2388
- `const hideAlsoInBooks = (scope: "book" | "everywhere")` — const, line 2410
- `const before = alsoPrefs ??` — const, line 2412
- `const base = contract` — const, line 2419
- `const makeExplorable = (target: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, origin: "library" | "tutor", offerRef: string): Promise<ExplorableOutcome>` — const, line 2436
- `let settle: (outcome: ExplorableOutcome)` — let, line 2443
- `const settled = new Promise<ExplorableOutcome>((resolve)` — const, line 2444
- `const press: OfferedPress =` — const, line 2445
- `const peekWorkbenchPassage = (spanId: string, target?: PassageTarget)` — const, line 2464
- `const exerciseSettings = libraryCtl.enabled ? contract?.libraryExercises ?? null : null` — const, line 2475
- `const exerciseCard = (sourceId: string | null)` — const, line 2476
- `const useExercise = (candidate: ExerciseCandidate)` — const, line 2480
- `const card = exerciseCard(candidate.sourceId ?? render?.sourceId ?? null)` — const, line 2481
- `const openExerciseInBook = (candidate: ExerciseCandidate)` — const, line 2490
- `const sourceId = candidate.sourceId ?? render?.sourceId ?? null` — const, line 2491
- `const exerciseProps: LibraryExercisesProps | null = exerciseSettings ?` — const, line 2494
- `const pickLibraryPagePractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 2508
- `const hit = libraryCtl.state?.ask.value?.hits[0]` — const, line 2509
- `const card = hit ? (library ?? []).find((candidate)` — const, line 2510
- `const readySources = library ?? []` — const, line 2551
- `const useShelf = Boolean(shelf) && !sidecarDown` — const, line 2553
- `const card = (library ?? []).find((candidate)` — const, line 2609
- `const card = (library ?? []).find((c)` — const, line 2629
- `const receiptId = searchResults.retrievalReceiptId` — const, line 2635
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 2680
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 2681
- `const wbActive = wbCtl.active` — const, line 2724
- `const wbStacked = working && wbCtl.narrow` — const, line 2725
- `const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible)` — const, line 2728
- `const wbSourceShown = !wbStacked || wbCtl.sheetOpen` — const, line 2729
- `const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry)` — const, line 2730
- `const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>()` — const, line 2731
- `const first = entry.spanIds[0]` — const, line 2733
- `const wbLabel = (stem: string)` — const, line 2736
- `const title = problemTitle(stem)` — const, line 2737
- `const tryPathExercise = (exercise: ReadingPathExerciseDto)` — const, line 2742
- `const workThroughSelection = ()` — const, line 2750
- `const nodes = selectionNodes(selection)` — const, line 2752
- `const editedText = selection.editedText?.trim()` — const, line 2753
- `const foldBlocks = contract?.activeReading?.foldBlocks ?? 3` — const, line 2770
- `const localFold = (spanIds: string[]): string[]` — const, line 2771
- `const positions = spanIds.map((spanId)` — const, line 2772
- `const last = Math.max(...positions)` — const, line 2774
- `const meta =` — const, line 2780
- `const effect = action.effect` — const, line 2781
- `const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null` — const, line 2827
- `const request: CompareRequest =` — const, line 2828
- `const region = selection?.region ?` — const, line 2853
- `const words = text?.trim()` — const, line 2854
- `const showMeFromAsk = ()` — const, line 2868
- `const goal = question.trim()` — const, line 2869
- `const home = parentExchange?.spanId ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan` — const, line 2870
- `const key = `show_me:$` — const, line 2872
- `const settle = (patch: Partial<ShowMeLine>)` — const, line 2875
- `const kind = cancel.action.effect.kind` — const, line 2892
- `const annotationId = handle.annotationId` — const, line 2899
- `const batchId = handle.importBatchId` — const, line 2911
- `const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number)` — const, line 2921
- `const spanId = wbCtl.close(session,` — const, line 2923
- `const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 2929
- `const card = openCardRef.current` — const, line 2930
- `const resumeMark = (spanId: string | null | undefined)` — const, line 2934
- `const entry = spanId ? wbResumeBySpan.get(spanId) : undefined` — const, line 2935
- `const verb = entry.status === "abandoned" ? "Reopen" : "Resume"` — const, line 2937
- `const target = event.target` — const, line 3060
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 3234
- `const active = activeSpan === block.spanId` — const, line 3235
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 3236
- `const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null` — const, line 3237
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 3238
- `const endQuestionAvailable = Boolean(endSection && endSection.question?.readingPhase === "after_section" && offeredCheckSections.has(endSection.id))` — const, line 3240
- `const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId))` — const, line 3244
- `const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""))` — const, line 3245
- `const offerSection = endSection && !muted && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 3246
- `const sel = window.getSelection()` — const, line 3265
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 3266
- `const active = railTab === tab` — const, line 3437
- `const waiting = tab === "guide" && pendingQuickCheckCount > 0` — const, line 3441
- `const marked = tab === "ask" && askTabMarked && !active` — const, line 3442
- `const params = (action.params ??` — const, line 3589

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
- [[Reference/Desktop/TypeScript/screens/reader/SideBySidePane|src/screens/reader/SideBySidePane.tsx]] — import-or-re-export; imports `SideBySidePane`
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
- [[Reference/Desktop/TypeScript/screens/reader/sideBySide|src/screens/reader/sideBySide.ts]] — import-or-re-export; imports `clampSplit`, `readSplit`, `sideBySideTarget`, `writeSplit`
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
- [[Reference/Desktop/TypeScript/screens/reader/useSideBySide|src/screens/reader/useSideBySide.ts]] — import-or-re-export; imports `SIDE_BY_SIDE_COPY`, `SIDE_BY_SIDE_SCROLL_KEYS`, `useSideBySide`
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
- [apps/learnloop-tauri/src/screens/reader/sideBySideCorrespondence.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideCorrespondence.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/rw1bReview.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/rw1bReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

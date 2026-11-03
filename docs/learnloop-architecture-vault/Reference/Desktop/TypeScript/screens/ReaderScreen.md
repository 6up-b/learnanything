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
source_commit: "7fd12e25ec8d644a7f73bd03a530e9a4ee9585d0"
source_commit_timestamp: "2026-11-02T19:40:18-05:00"
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
| Source lines | 4640 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `7fd12e25ec8d644a7f73bd03a530e9a4ee9585d0` |
| Commit timestamp | `2026-11-02T19:40:18-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]]

## Public API

- `export interface ReaderOpenSource` — interface, line 236
- `export interface ReaderCheckMeRequest extends CueCheckMeRequest` — interface, line 252
- `export type ReaderExerciseRequest = ReaderWorkbenchExercise &` — type, line 265
- `export const SIDE_PATH_COPY =` — const, line 269
- `export function ReaderScreen(` — function, line 291

## Internal implementation anchors

- `type AnnotationSegment, type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 140
- `type MarginAnnotation, type ReaderSelection, } from "./reader/readerShared"` — type, line 141
- `type ReaderSelection, } from "./reader/readerShared"` — type, line 142
- `const NO_SECTIONS: never[] = []` — const, line 146
- `const READER_MODE_OPTIONS = [` — const, line 147
- `const TAG_ACTIONS: Array<` — const, line 157
- `const WHOLE_BLOCK_QUOTE = "(whole block)"` — const, line 165
- `type ReaderRailTab = "guide" | "ask" | "notes"` — type, line 167
- `const HEALTH_COLOR: Record<string, "green" | "amber" | "pink" | "slate"> =` — const, line 169
- `const FURNITURE_BLOCK_TYPES = new Set(["PageHeader", "PageFooter", "TableOfContents"])` — const, line 178
- `type OpenOutcome = "opened" | "preparing" | "not_opened"` — type, line 181
- `interface OfferedPress` — interface, line 185
- `const OFFER_OUTCOME: Record<FigureRequestOutcome, ExplorableOutcome> =` — const, line 196
- `const BADGED_HEALTH = new Set(["suspect", "failed"])` — const, line 202
- `interface RemovedAnnotation` — interface, line 206
- `const UNDO_REMOVE_MS = 10_000` — const, line 216
- `function newKey(): string` — function, line 218
- `function identityOf(view: Pick<ReaderRenderViewDto, "sourceId" | "revisionId" | "extractionId">): SourceIdentity` — function, line 227
- `function sectionIdentity(section:` — function, line 232
- `const mainPaneOwnsCueKey = (event: KeyboardEvent): boolean` — const, line 276
- `interface IntentPane` — interface, line 281
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 337
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 341
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 350
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 351
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 352
- `const openingRef = useRef<string | null>(null)` — const, line 358
- `const askPanelOn = algoConfig().ask !== null` — const, line 379
- `const storedStyle = useStoredHelpStyle()` — const, line 380
- `const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen` — const, line 381
- `const pdfViewRequestRef = useRef(0)` — const, line 403
- `const sourceEpochRef = useRef(0)` — const, line 434
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 445
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 446
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 447
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 448
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 449
- `const modeSaveVersionRef = useRef(0)` — const, line 450
- `const answerModeSaveVersionRef = useRef(0)` — const, line 451
- `const enabled = contract?.readerEnabled ?? true` — const, line 467
- `const inquiry = contract?.inquiryEnabled === true` — const, line 470
- `const muted = inquiry && mode === "skim"` — const, line 473
- `const intentContract = inquiry && !offline ? contract?.intent ?? null : null` — const, line 476
- `const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading)` — const, line 477
- `const openFigureSource = useRef<((extractionId: string, spanId: string)` — const, line 481
- `const figureOpenSource = useCallback((extractionId: string, spanId: string)` — const, line 482
- `const figuresCtl = useFigures(` — const, line 483
- `const figureOffersOn = Boolean(contract?.figures?.offers) && !offline` — const, line 489
- `const showMeOn = Boolean(contract?.figures?.showMe) && !offline` — const, line 493
- `const waitingOfferRef = useRef<OfferedPress | null>(null)` — const, line 499
- `const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome)` — const, line 504
- `const press = offeredFigure` — const, line 511
- `const open = render?.extractionId ?? null` — const, line 513
- `const readerTutor = contract?.readerTutor ?? null` — const, line 536
- `const askWorkbenchSessionRef = useRef<string | null>(null)` — const, line 538
- `const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true` — const, line 543
- `const askPersonalizedRef = useRef<boolean | null>(null)` — const, line 544
- `const askComposerAnchorRef = useRef<AskAnchor | null>(null)` — const, line 549
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 555
- `const renderBlocksBySpan = useMemo( ()` — const, line 559
- `const visit = useReaderVisit(` — const, line 565
- `const showGuideRail = useCallback(()` — const, line 571
- `const progress = useReadingProgress(` — const, line 575
- `const doseVisitId = useCallback(()` — const, line 592
- `const refreshAnnotations = useCallback(async ()` — const, line 594
- `const epoch = sourceEpochRef.current` — const, line 596
- `const result = await cachedSourceRead( render.sourceId, ["reader_source_annotations", render.sourceId, render.extractionId], ()` — const, line 600
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 607
- `const version = (r.version as Record<string, unknown>) ??` — const, line 610
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 611
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 612
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 613
- `const placement = r.placement as ReaderAnnotationPlacementDto | undefined` — const, line 614
- `let page: number | null = null` — let, line 624
- `let bbox: number[] | null = null` — let, line 625
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 627
- `const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?:` — const, line 645
- `const openCardRef = useRef<SourceLibraryCard | null>(null)` — const, line 670
- `const openExtractionRef = useRef<string | null>(null)` — const, line 672
- `const reloadGuidePlan = useCallback(async ()` — const, line 674
- `const extractionId = render.extractionId` — const, line 676
- `const plan = await readGuidePlan(render.sourceId, extractionId,` — const, line 678
- `const spanOrder = useMemo( ()` — const, line 691
- `const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none"` — const, line 695
- `const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 698
- `const card = openCardRef.current` — const, line 699
- `const wbProps = useMemo<ReaderWorkbenchProps | undefined>(()` — const, line 709
- `const submitted = workbench?.onSubmitted` — const, line 710
- `const trail = besideTrail(returnStackRef.current)` — const, line 715
- `const wbCtl = useReaderWorkbench(` — const, line 720
- `const working = wbCtl.active !== null` — const, line 727
- `const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline` — const, line 731
- `const alsoHidden = alsoPrefs ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId)) : Boolean(contract?.correspondence?.hiddenEverywhere) || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.so…` — const, line 736
- `const peekCrumbShown = alsoPeek ?? findPeek` — const, line 746
- `const pathRefreshKey = readingPathRefreshKey(` — const, line 761
- `const tryFirstRef = useRef<((spanId: string)` — const, line 775
- `const cueCtl = useReaderCues(` — const, line 776
- `const recapCtl = useReaderRecap(` — const, line 791
- `const recapShown = Boolean(recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working)` — const, line 805
- `const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip")` — const, line 816
- `const root = history.find((entry)` — const, line 817
- `const recapRevisited = useCallback((rootId: string)` — const, line 830
- `const root = history.find((entry)` — const, line 831
- `const recapRevisit = useCallback(async (rootId: string)` — const, line 834
- `const root = history.find((entry)` — const, line 835
- `const recapOpenInquiry = useCallback((rootId: string, spanId: string)` — const, line 841
- `const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch")` — const, line 844
- `const cueMarksFor = (markSurface: "pdf" | "watch")` — const, line 864
- `let cancelled = false` — let, line 873
- `const scroller = railRef.current` — const, line 906
- `const clamp = ()` — const, line 908
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 909
- `const observer = new ResizeObserver(clamp)` — const, line 912
- `const query = librarySearch.trim()` — const, line 923
- `let cancelled = false` — let, line 930
- `const timer = window.setTimeout(()` — const, line 933
- `const resetSourceState = useCallback(()` — const, line 956
- `const openSource = useCallback( async ( card: SourceLibraryCard, jumpSpan?: string, // jumpReading: the reading jumpSpan was found on (a search hit, a // return)` — const, line 1005
- `const handoff = options.handoff ?? null` — const, line 1014
- `const view = await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 1032
- `const pdfRequest = ++pdfViewRequestRef.current` — const, line 1079
- `const current = ()` — const, line 1080
- `const openFixture = useCallback(()` — const, line 1115
- `const backToLibrary = useCallback(()` — const, line 1123
- `const spanId = readingSpan ?? activeSpan` — const, line 1127
- `const section = guidePlan?.sections.find((candidate)` — const, line 1128
- `const resumedRef = useRef(false)` — const, line 1146
- `const trail = initialSource.besideTrail ?? null` — const, line 1150
- `const activeBlock = useMemo(()` — const, line 1164
- `const pdfHighlights: PdfHighlight[] = useMemo(()` — const, line 1173
- `const list: PdfHighlight[] = []` — const, line 1174
- `const base =` — const, line 1177
- `const placed = highlightFromPlacement(base, a.placement)` — const, line 1179
- `const segments = a.segments.flatMap((s)` — const, line 1184
- `const annotatedSpans = useMemo( ()` — const, line 1191
- `const boundaryBlock = useMemo(()` — const, line 1195
- `const revealedPassages = useMemo(()` — const, line 1197
- `const revealed = new Set(revealedSections)` — const, line 1198
- `const map = new Map<string,` — const, line 1199
- `const revealedGuidanceSpans = useMemo(()` — const, line 1208
- `const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null` — const, line 1213
- `const protectedSelection = selectionProtected(protection, selection)` — const, line 1214
- `const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1215
- `const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan))` — const, line 1219
- `const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1220
- `const editCaptureText = useCallback((text: string)` — const, line 1225
- `const resetCaptureText = useCallback(()` — const, line 1228
- `const saveAnnotationEdit = useCallback(async ()` — const, line 1240
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 1262
- `const result = await api.readerReanchor(` — const, line 1266
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1283
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1306
- `const target = annotations.find((a)` — const, line 1307
- `const reading = render ?` — const, line 1308
- `const epoch = sourceEpochRef.current` — const, line 1309
- `const undoRemove = useCallback(async ()` — const, line 1324
- `const last = removed` — const, line 1325
- `const epoch = sourceEpochRef.current` — const, line 1331
- `const result = await api.readerRestoreAnnotation(` — const, line 1333
- `const timer = window.setTimeout(()` — const, line 1346
- `const onKey = (event: KeyboardEvent)` — const, line 1352
- `const target = event.target` — const, line 1355
- `const openAnnotationNote = useCallback((annotationId: string)` — const, line 1364
- `const target = annotations.find((a)` — const, line 1365
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1377
- `const sel = window.getSelection()` — const, line 1378
- `const container = bodyRef.current` — const, line 1379
- `const range = sel.getRangeAt(0)` — const, line 1381
- `const nodes: Array<` — const, line 1382
- `const seen = new Set<string>()` — const, line 1383
- `const spanId = el.dataset.spanId` — const, line 1385
- `let intersects = false` — let, line 1387
- `const sub = document.createRange()` — const, line 1394
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1402
- `const block = renderBlocksBySpan.get(spanId)` — const, line 1407
- `const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1417
- `const cancelIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1418
- `const selectionSpanIds = useMemo( ()` — const, line 1419
- `const intentBox = useIntentBox(` — const, line 1423
- `const openActiveRail = useCallback(()` — const, line 1437
- `const activeCtl = useActiveReading(` — const, line 1441
- `const libraryCtl = useLibraryAsk(` — const, line 1450
- `const keptCtl = useKeptComparisons(` — const, line 1452
- `const notesCtl = useNoteMarks(` — const, line 1454
- `const pdfMarks = (): ReadonlyMap<string, ReactNode> | null` — const, line 1459
- `const cues = cueMarksFor("pdf")` — const, line 1460
- `const merged = new Map<string, ReactNode>(cues ?? [])` — const, line 1462
- `const cue = merged.get(spanId)` — const, line 1464
- `const before = merged.get(spanId)` — const, line 1469
- `const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null)` — const, line 1475
- `const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint)` — const, line 1477
- `const sbs = useSideBySide(` — const, line 1479
- `const node = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1487
- `const sbsPanes = sbs.panes && !comparing` — const, line 1500
- `const sbsPanesRef = useRef(false)` — const, line 1501
- `const sbsShownRef = useRef(false)` — const, line 1506
- `const sbsRef = useRef(sbs)` — const, line 1508
- `const sbsEscBusyRef = useRef(false)` — const, line 1511
- `const sbsPaneRef = useRef<HTMLDivElement | null>(null)` — const, line 1513
- `const runSideIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1518
- `const cancelSideIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1519
- `const sbsSection = sbs.section && sbs.target && sbs.section.sectionId === sbs.target.sectionId ? sbs.section : null` — const, line 1520
- `type BesideRun = |` — type, line 1535
- `const besideSeq = useRef(0)` — const, line 1544
- `const besideRunRef = useRef<(run: BesideRun)` — const, line 1547
- `const besideDroppedRef = useRef<(run: BesideRun)` — const, line 1548
- `const openBesideRef = useRef<(hit:` — const, line 1549
- `const snapshotBesideRef = useRef<(spanId: string)` — const, line 1556
- `const shown = sbsRef.current.target` — const, line 1558
- `const takeBesideBook = useCallback((book: SourceIdentity, spanId: string, run: BesideRun)` — const, line 1562
- `const id = ++besideSeq.current` — const, line 1564
- `const sideExtractionRef = useRef<string | null>(null)` — const, line 1576
- `const checkMeFromSideCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 1577
- `const side = useSidePane(` — const, line 1582
- `const besideRanRef = useRef(0)` — const, line 1611
- `const handoff = besideHandoff` — const, line 1613
- `const card = openCardRef.current` — const, line 1628
- `const trail = besideTrail(returnStackRef.current)` — const, line 1630
- `const work = handoff.run` — const, line 1639
- `const openComposer = useCallback((anchor: AskAnchor | null)` — const, line 1653
- `const sbsRowRef = useRef<HTMLDivElement | null>(null)` — const, line 1671
- `const startSbsResize = (event: ReactPointerEvent<HTMLDivElement>)` — const, line 1672
- `const row = sbsRowRef.current` — const, line 1673
- `const rect = row.getBoundingClientRect()` — const, line 1676
- `const move = (moved: PointerEvent)` — const, line 1677
- `const up = ()` — const, line 1680
- `const touchMain = ()` — const, line 1692
- `const onKey = (event: KeyboardEvent)` — const, line 1701
- `const target = event.target` — const, line 1703
- `const ctl = sbsRef.current` — const, line 1705
- `const open = ctl.panes || ctl.sheet` — const, line 1706
- `const shown = sbsShownRef.current` — const, line 1707
- `const mod = event.ctrlKey || event.metaKey` — const, line 1708
- `const side = sbsPaneRef.current` — const, line 1718
- `const inSide = target instanceof Element && Boolean(target.closest("[data-side-by-side-pane]"))` — const, line 1719
- `const inMain = target instanceof Node && Boolean(bodyRef.current?.contains(target))` — const, line 1725
- `const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false, anchor?: SourceIdentity)` — const, line 1735
- `const identity = anchor ?? identityOf(render)` — const, line 1742
- `const request =` — const, line 1743
- `const closeLibrary = useCallback(()` — const, line 1748
- `const onKey = (event: KeyboardEvent)` — const, line 1755
- `const onMouseUp = useCallback(()` — const, line 1766
- `const sel = window.getSelection()` — const, line 1767
- `const quote = sel.toString().replace(/\s+/g, " ").trim()` — const, line 1769
- `const nodes = collectSelectionNodes()` — const, line 1771
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1800
- `const domDragRef = useRef<` — const, line 1801
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1803
- `const host = bodyRef.current` — const, line 1804
- `const rect = host.getBoundingClientRect()` — const, line 1806
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1810
- `const target = event.target as Node` — const, line 1814
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1816
- `const domDrafting = domDraft !== null` — const, line 1828
- `const rectFrom = (drag:` — const, line 1831
- `const onMove = (event: MouseEvent)` — const, line 1837
- `const drag = domDragRef.current` — const, line 1838
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1840
- `const onUp = (event: MouseEvent)` — const, line 1843
- `const drag = domDragRef.current` — const, line 1844
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1848
- `const rect = rectFrom(drag, point)` — const, line 1850
- `const next = [...domBoxesRef.current, rect]` — const, line 1853
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1870
- `const host = bodyRef.current` — const, line 1871
- `const hostRect = host.getBoundingClientRect()` — const, line 1873
- `const clientBoxes = boxes.map((b)` — const, line 1874
- `const nodes: Array<` — const, line 1880
- `const seen = new Set<string>()` — const, line 1881
- `const spanId = el.dataset.spanId` — const, line 1883
- `const elRect = el.getBoundingClientRect()` — const, line 1885
- `const touches = clientBoxes.some( (b)` — const, line 1886
- `const words: string[] = []` — const, line 1890
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 1891
- `const text = node as Text` — const, line 1893
- `const wordPattern = /\S+/g` — const, line 1894
- `let match: RegExpExecArray | null` — let, line 1895
- `const range = document.createRange()` — const, line 1897
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 1900
- `const cx = (Math.min(...rects.map((r)` — const, line 1902
- `const cy = (Math.min(...rects.map((r)` — const, line 1903
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 1907
- `const commitDomBoxes = useCallback(()` — const, line 1916
- `const boxes = domBoxesRef.current` — const, line 1917
- `const nodes = resolveDomBoxes(boxes)` — const, line 1919
- `const quote = nodes.map((n)` — const, line 1925
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 1934
- `const clearDomBoxes = ()` — const, line 1942
- `const onKeyDown = (event: KeyboardEvent)` — const, line 1948
- `const onKeyUp = (event: KeyboardEvent)` — const, line 1953
- `const onBlur = ()` — const, line 1959
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 1981
- `const point = domPointFromClient(request.x, request.y)` — const, line 1983
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 1984
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 2005
- `const retryRequest = useCallback(async (requestId: string)` — const, line 2018
- `const optimisticSegments = useCallback( (nodes: string | Array<string |` — const, line 2032
- `const list = Array.isArray(nodes) ? nodes : [nodes]` — const, line 2034
- `const spanId = typeof node === "string" ? node : node.spanId` — const, line 2036
- `const geometry = pdfView?.blocks.find((b)` — const, line 2037
- `const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number" ?` — const, line 2038
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 2050
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 2054
- `const quotedNodes = (()` — const, line 2059
- `const multi = collectSelectionNodes()` — const, line 2062
- `const optimisticIds = quotedNodes ?? [target.spanId]` — const, line 2065
- `const nodes = quotedNodes ?? [` — const, line 2075
- `const receipt = await api.readerCapture(` — const, line 2076
- `const handler = (event: KeyboardEvent)` — const, line 2103
- `const clearSelection = useCallback(()` — const, line 2115
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 2127
- `const segment = a.segments.find((s)` — const, line 2129
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 2136
- `const alsoKeyRef = useRef<()` — const, line 2146
- `const onKey = (event: KeyboardEvent)` — const, line 2154
- `const target = event.target` — const, line 2157
- `const tabs: ReaderRailTab[] = ["guide", "ask", "notes"]` — const, line 2159
- `const askRequestSeen = useRef(askRequest)` — const, line 2197
- `const revealAskRef = useRef<()` — const, line 2199
- `const startCompareRef = useRef<(request: CompareRequest)` — const, line 2224
- `const sideAnchor = Boolean(side.extractionId) && side.extractionId === request.extractionId` — const, line 2227
- `const request = compareWaitsForWork` — const, line 2234
- `const sideMarksChanged = side.marksChanged` — const, line 2244
- `const captureIn = useCallback(async (target: PaneCaptureTarget, what:` — const, line 2245
- `const common =` — const, line 2250
- `const receipt: ReaderPresetReceiptDto = "preset" in what ? await api.readerInvokePreset(` — const, line 2255
- `const drained = await api.readerDrainOutbox()` — const, line 2266
- `const invokePreset = useCallback( // RW1b: the intent box passes its own words as the annotation's learner // text, and names the intention and entry in the funnel event. // Reader CA6b: `target` is side by side's second pane (its book, revision, // reading a…` — const, line 2287
- `const note_ = learnerTextOverride ?? note` — const, line 2295
- `const nodes = selectionNodes(selection)` — const, line 2296
- `const editedText = selection.editedText?.trim()` — const, line 2297
- `const receipt = await api.readerInvokePreset(` — const, line 2309
- `const drained = await api.readerDrainOutbox()` — const, line 2333
- `const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>, target?: PaneCaptureTarget): Promise<string | null>` — const, line 2356
- `const note_ = learnerTextOverride ?? note` — const, line 2360
- `const nodes = selectionNodes(selection)` — const, line 2361
- `const receipt = await api.readerCapture(` — const, line 2373
- `const pauseArc = useCallback(async ()` — const, line 2401
- `const next = await api.readerArc(` — const, line 2405
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 2412
- `const next = await api.readerArc(` — const, line 2417
- `const importJobRef = useRef<` — const, line 2429
- `const importExercise = useCallback(async (target?: PaneCaptureTarget): Promise<string | null>` — const, line 2432
- `const nodes = target ? target.nodes : selectionNodes(selection!)` — const, line 2434
- `const editedText = target ? undefined : selection!.editedText?.trim()` — const, line 2435
- `const receipt = await api.readerImportExercise(target ?` — const, line 2438
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 2486
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 2487
- `const timer = setInterval(async ()` — const, line 2491
- `const status = await api.readerExerciseImportStatus(` — const, line 2493
- `const job = importJobRef.current` — const, line 2494
- `const waited = Date.now() - job.startedAt` — const, line 2497
- `const saveOwnQuestion = useCallback(async ()` — const, line 2524
- `const saved = await api.readerAuthorQA(` — const, line 2532
- `const runCoach = useCallback(async ()` — const, line 2553
- `const lint = await api.readerCoachLint(` — const, line 2556
- `const changeMode = useCallback( async (next: string)` — const, line 2567
- `const previous = mode` — const, line 2569
- `const version = ++modeSaveVersionRef.current` — const, line 2572
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 2583
- `const answerModeNext = next as ReaderAnswerMode` — const, line 2585
- `const previous = answerMode` — const, line 2586
- `const version = ++answerModeSaveVersionRef.current` — const, line 2589
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 2605
- `const renderInquiryTop = useCallback((root: ReaderExchange)` — const, line 2620
- `const line = reconnect && reconnect.rootId === root.id && !muted ? ( <ReconnectLine placement="rail" question=` — const, line 2623
- `const check = inquiryChecks[root.id]` — const, line 2633
- `const inlineReconnect = reconnect && reconnect.inline && !muted ? ( <ReconnectLine placement="inline" question=` — const, line 2661
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 2672
- `const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">): Promise<OpenOutcome>` — const, line 2690
- `const card = (library ?? []).find((candidate)` — const, line 2695
- `const spanId = readingSpan ?? activeSpan` — const, line 2698
- `const openFollowedFigure = (figure: CorrespondentFigureDto, hit: CorrespondentSectionDto)` — const, line 2716
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2718
- `const compareFoundSection = (hit: CorrespondentSectionDto)` — const, line 2733
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2735
- `const hideAlsoInBooks = (scope: "book" | "everywhere")` — const, line 2758
- `const before = alsoPrefs ??` — const, line 2760
- `const base = contract` — const, line 2767
- `const makeExplorable = (target: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, origin: "library" | "tutor", offerRef: string): Promise<ExplorableOutcome>` — const, line 2784
- `let settle: (outcome: ExplorableOutcome)` — let, line 2791
- `const settled = new Promise<ExplorableOutcome>((resolve)` — const, line 2792
- `const press: OfferedPress =` — const, line 2793
- `const peekWorkbenchPassage = (spanId: string, target?: PassageTarget)` — const, line 2812
- `const exerciseSettings = libraryCtl.enabled ? contract?.libraryExercises ?? null : null` — const, line 2823
- `const exerciseCard = (sourceId: string | null)` — const, line 2824
- `const useExercise = (candidate: ExerciseCandidate)` — const, line 2828
- `const card = exerciseCard(candidate.sourceId ?? render?.sourceId ?? null)` — const, line 2829
- `const openExerciseInBook = (candidate: ExerciseCandidate)` — const, line 2838
- `const sourceId = candidate.sourceId ?? render?.sourceId ?? null` — const, line 2839
- `const exerciseProps: LibraryExercisesProps | null = exerciseSettings ?` — const, line 2842
- `const pickLibraryPagePractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 2856
- `const hit = libraryCtl.state?.ask.value?.hits[0]` — const, line 2857
- `const card = hit ? (library ?? []).find((candidate)` — const, line 2858
- `const readySources = library ?? []` — const, line 2901
- `const useShelf = Boolean(shelf) && !sidecarDown` — const, line 2903
- `const card = (library ?? []).find((candidate)` — const, line 2961
- `const card = (library ?? []).find((c)` — const, line 2982
- `const receiptId = searchResults.retrievalReceiptId` — const, line 2988
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 3033
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 3034
- `const wbActive = wbCtl.active` — const, line 3077
- `const wbStacked = working && wbCtl.narrow` — const, line 3078
- `const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible)` — const, line 3081
- `const wbSourceShown = !wbStacked || wbCtl.sheetOpen` — const, line 3082
- `const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry)` — const, line 3083
- `const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>()` — const, line 3084
- `const first = entry.spanIds[0]` — const, line 3086
- `const wbLabel = (stem: string)` — const, line 3089
- `const title = problemTitle(stem)` — const, line 3090
- `const tryPathExercise = (exercise: ReadingPathExerciseDto)` — const, line 3095
- `const workThroughSelection = ()` — const, line 3103
- `const nodes = selectionNodes(selection)` — const, line 3105
- `const editedText = selection.editedText?.trim()` — const, line 3106
- `const foldBlocks = contract?.activeReading?.foldBlocks ?? 3` — const, line 3123
- `const localFold = (spanIds: string[]): string[]` — const, line 3124
- `const positions = spanIds.map((spanId)` — const, line 3125
- `const last = Math.max(...positions)` — const, line 3127
- `const mainPane: IntentPane =` — const, line 3136
- `const sidePane: IntentPane | null = side.extractionId ?` — const, line 3145
- `const sideMeta = (pane: IntentPane): Record<string, string>` — const, line 3155
- `const runIntentIn = (pane: IntentPane, action: ReaderIntentActionDto, text: string, how: IntentRunHow): Promise<IntentRunHandle | null> | void` — const, line 3157
- `const meta =` — const, line 3158
- `const effect = action.effect` — const, line 3159
- `const sideSection = pane.side?.section ?? null` — const, line 3160
- `const anchor: AskAnchor =` — const, line 3166
- `const target = pane.side.target` — const, line 3207
- `const target = pane.side.target` — const, line 3213
- `const target = pane.side.target` — const, line 3219
- `const target = pane.side.target` — const, line 3229
- `const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null` — const, line 3274
- `const request: CompareRequest =` — const, line 3275
- `const region = pane.region` — const, line 3307
- `const words = text?.trim()` — const, line 3308
- `const sideShows = (extractionId: string, spanId: string): boolean` — const, line 3329
- `const checkBeside = (book: SourceIdentity, spanId: string, practiceItemId: string, proposalId: string | null)` — const, line 3332
- `const workThroughImported = (item:` — const, line 3337
- `const imported = exerciseImport` — const, line 3338
- `const spanIds = imported?.spanIds ?? (activeSpan ? [activeSpan] : [])` — const, line 3339
- `const settleShowMeLine = (key: string, patch: Partial<ShowMeLine>)` — const, line 3347
- `const requestShowMe = (ctl: FiguresCtl, run: Extract<BesideRun,` — const, line 3350
- `const key = run.lineKey` — const, line 3351
- `const runOnBook = (about: AskAbout, run: Extract<BesideRun,` — const, line 3363
- `const showMeFromAsk = ()` — const, line 3388
- `const goal = question.trim()` — const, line 3389
- `const about = parentExchange ? parentExchange.about ?? null : askComposerAnchor?.about ?? null` — const, line 3390
- `const home = parentExchange?.spanId ?? (about ? askComposerAnchor?.spanId : undefined) ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan` — const, line 3391
- `const key = `show_me:$` — const, line 3394
- `const run =` — const, line 3397
- `const cancelIntentIn = (pane: IntentPane, cancel: IntentCancel)` — const, line 3406
- `const kind = cancel.action.effect.kind` — const, line 3407
- `const annotationId = handle.annotationId` — const, line 3414
- `const batchId = handle.importBatchId` — const, line 3431
- `const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number)` — const, line 3445
- `const spanId = wbCtl.close(session,` — const, line 3447
- `const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3453
- `const card = openCardRef.current` — const, line 3454
- `const asked = libraryCtl.state?.request` — const, line 3458
- `const resumeMark = (spanId: string | null | undefined)` — const, line 3466
- `const entry = spanId ? wbResumeBySpan.get(spanId) : undefined` — const, line 3467
- `const verb = entry.status === "abandoned" ? "Reopen" : "Resume"` — const, line 3469
- `const target = event.target` — const, line 3593
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 3768
- `const active = activeSpan === block.spanId` — const, line 3769
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 3770
- `const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null` — const, line 3771
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 3772
- `const endQuestionAvailable = Boolean(endSection && endSection.question?.readingPhase === "after_section" && offeredCheckSections.has(endSection.id))` — const, line 3774
- `const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId))` — const, line 3778
- `const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""))` — const, line 3779
- `const offerSection = endSection && !muted && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 3780
- `const sel = window.getSelection()` — const, line 3799
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 3800
- `const cue = side.cues.markOn(spanId)` — const, line 3890
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 3918
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 3941
- `const active = railTab === tab` — const, line 4054
- `const waiting = tab === "guide" && pendingQuickCheckCount > 0` — const, line 4058
- `const marked = tab === "ask" && askTabMarked && !active` — const, line 4059
- `const params = (action.params ??` — const, line 4206
- `const run =` — const, line 4478
- `const book = exchange?.about ?? render` — const, line 4487

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
- [[Reference/Desktop/TypeScript/components/sourceTail|src/components/sourceTail.ts]] — import-or-re-export; imports `youtubeVideoId`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `TermSelect`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `SPAN_MISMATCH_COPY`, `errorMessage`
- [[Reference/Desktop/TypeScript/fixtures/readerRenderView|src/fixtures/readerRenderView.ts]] — import-or-re-export; imports `readerRenderViewFixture`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
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

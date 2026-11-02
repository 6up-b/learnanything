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
source_commit: "20c6c3ad3806f7951982f4768478fe77272f4c3a"
source_commit_timestamp: "2026-11-01T23:26:02-05:00"
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
| Source lines | 4629 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `20c6c3ad3806f7951982f4768478fe77272f4c3a` |
| Commit timestamp | `2026-11-01T23:26:02-05:00` |

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
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 334
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 338
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 347
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 348
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 349
- `const openingRef = useRef<string | null>(null)` — const, line 355
- `const askPanelOn = algoConfig().ask !== null` — const, line 376
- `const storedStyle = useStoredHelpStyle()` — const, line 377
- `const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen` — const, line 378
- `const pdfViewRequestRef = useRef(0)` — const, line 400
- `const sourceEpochRef = useRef(0)` — const, line 431
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 442
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 443
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 444
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 445
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 446
- `const modeSaveVersionRef = useRef(0)` — const, line 447
- `const answerModeSaveVersionRef = useRef(0)` — const, line 448
- `const enabled = contract?.readerEnabled ?? true` — const, line 464
- `const inquiry = contract?.inquiryEnabled === true` — const, line 467
- `const muted = inquiry && mode === "skim"` — const, line 470
- `const intentContract = inquiry && !offline ? contract?.intent ?? null : null` — const, line 473
- `const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading)` — const, line 474
- `const figuresCtl = useFigures(` — const, line 477
- `const figureOffersOn = Boolean(contract?.figures?.offers) && !offline` — const, line 483
- `const showMeOn = Boolean(contract?.figures?.showMe) && !offline` — const, line 487
- `const waitingOfferRef = useRef<OfferedPress | null>(null)` — const, line 493
- `const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome)` — const, line 498
- `const press = offeredFigure` — const, line 505
- `const open = render?.extractionId ?? null` — const, line 507
- `const readerTutor = contract?.readerTutor ?? null` — const, line 530
- `const askWorkbenchSessionRef = useRef<string | null>(null)` — const, line 532
- `const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true` — const, line 537
- `const askPersonalizedRef = useRef<boolean | null>(null)` — const, line 538
- `const askComposerAnchorRef = useRef<AskAnchor | null>(null)` — const, line 543
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 549
- `const renderBlocksBySpan = useMemo( ()` — const, line 553
- `const visit = useReaderVisit(` — const, line 559
- `const showGuideRail = useCallback(()` — const, line 565
- `const progress = useReadingProgress(` — const, line 569
- `const doseVisitId = useCallback(()` — const, line 586
- `const refreshAnnotations = useCallback(async ()` — const, line 588
- `const epoch = sourceEpochRef.current` — const, line 590
- `const result = await cachedSourceRead( render.sourceId, ["reader_source_annotations", render.sourceId, render.extractionId], ()` — const, line 594
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 601
- `const version = (r.version as Record<string, unknown>) ??` — const, line 604
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 605
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 606
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 607
- `const placement = r.placement as ReaderAnnotationPlacementDto | undefined` — const, line 608
- `let page: number | null = null` — let, line 618
- `let bbox: number[] | null = null` — let, line 619
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 621
- `const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?:` — const, line 639
- `const openCardRef = useRef<SourceLibraryCard | null>(null)` — const, line 664
- `const openExtractionRef = useRef<string | null>(null)` — const, line 666
- `const reloadGuidePlan = useCallback(async ()` — const, line 668
- `const extractionId = render.extractionId` — const, line 670
- `const plan = await readGuidePlan(render.sourceId, extractionId,` — const, line 672
- `const spanOrder = useMemo( ()` — const, line 685
- `const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none"` — const, line 689
- `const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 692
- `const card = openCardRef.current` — const, line 693
- `const wbProps = useMemo<ReaderWorkbenchProps | undefined>(()` — const, line 703
- `const submitted = workbench?.onSubmitted` — const, line 704
- `const trail = besideTrail(returnStackRef.current)` — const, line 709
- `const wbCtl = useReaderWorkbench(` — const, line 714
- `const working = wbCtl.active !== null` — const, line 721
- `const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline` — const, line 725
- `const alsoHidden = alsoPrefs ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId)) : Boolean(contract?.correspondence?.hiddenEverywhere) || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.so…` — const, line 730
- `const peekCrumbShown = alsoPeek ?? findPeek` — const, line 740
- `const pathRefreshKey = readingPathRefreshKey(` — const, line 755
- `const tryFirstRef = useRef<((spanId: string)` — const, line 769
- `const cueCtl = useReaderCues(` — const, line 770
- `const recapCtl = useReaderRecap(` — const, line 785
- `const recapShown = Boolean(recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working)` — const, line 799
- `const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip")` — const, line 810
- `const root = history.find((entry)` — const, line 811
- `const recapRevisited = useCallback((rootId: string)` — const, line 824
- `const root = history.find((entry)` — const, line 825
- `const recapRevisit = useCallback(async (rootId: string)` — const, line 828
- `const root = history.find((entry)` — const, line 829
- `const recapOpenInquiry = useCallback((rootId: string, spanId: string)` — const, line 835
- `const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch")` — const, line 838
- `const cueMarksFor = (markSurface: "pdf" | "watch")` — const, line 858
- `let cancelled = false` — let, line 867
- `const scroller = railRef.current` — const, line 900
- `const clamp = ()` — const, line 902
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 903
- `const observer = new ResizeObserver(clamp)` — const, line 906
- `const query = librarySearch.trim()` — const, line 917
- `let cancelled = false` — let, line 924
- `const timer = window.setTimeout(()` — const, line 927
- `const resetSourceState = useCallback(()` — const, line 950
- `const openSource = useCallback( async ( card: SourceLibraryCard, jumpSpan?: string, // jumpReading: the reading jumpSpan was found on (a search hit, a // return)` — const, line 999
- `const handoff = options.handoff ?? null` — const, line 1008
- `const view = await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 1026
- `const pdfRequest = ++pdfViewRequestRef.current` — const, line 1073
- `const current = ()` — const, line 1074
- `const openFixture = useCallback(()` — const, line 1109
- `const backToLibrary = useCallback(()` — const, line 1117
- `const spanId = readingSpan ?? activeSpan` — const, line 1121
- `const section = guidePlan?.sections.find((candidate)` — const, line 1122
- `const resumedRef = useRef(false)` — const, line 1140
- `const trail = initialSource.besideTrail ?? null` — const, line 1144
- `const activeBlock = useMemo(()` — const, line 1158
- `const pdfHighlights: PdfHighlight[] = useMemo(()` — const, line 1167
- `const list: PdfHighlight[] = []` — const, line 1168
- `const base =` — const, line 1171
- `const placed = highlightFromPlacement(base, a.placement)` — const, line 1173
- `const segments = a.segments.flatMap((s)` — const, line 1178
- `const annotatedSpans = useMemo( ()` — const, line 1185
- `const boundaryBlock = useMemo(()` — const, line 1189
- `const revealedPassages = useMemo(()` — const, line 1191
- `const revealed = new Set(revealedSections)` — const, line 1192
- `const map = new Map<string,` — const, line 1193
- `const revealedGuidanceSpans = useMemo(()` — const, line 1202
- `const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null` — const, line 1207
- `const protectedSelection = selectionProtected(protection, selection)` — const, line 1208
- `const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1209
- `const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan))` — const, line 1213
- `const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1214
- `const editCaptureText = useCallback((text: string)` — const, line 1219
- `const resetCaptureText = useCallback(()` — const, line 1222
- `const saveAnnotationEdit = useCallback(async ()` — const, line 1234
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 1256
- `const result = await api.readerReanchor(` — const, line 1260
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1277
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1300
- `const target = annotations.find((a)` — const, line 1301
- `const reading = render ?` — const, line 1302
- `const epoch = sourceEpochRef.current` — const, line 1303
- `const undoRemove = useCallback(async ()` — const, line 1318
- `const last = removed` — const, line 1319
- `const epoch = sourceEpochRef.current` — const, line 1325
- `const result = await api.readerRestoreAnnotation(` — const, line 1327
- `const timer = window.setTimeout(()` — const, line 1340
- `const onKey = (event: KeyboardEvent)` — const, line 1346
- `const target = event.target` — const, line 1349
- `const openAnnotationNote = useCallback((annotationId: string)` — const, line 1358
- `const target = annotations.find((a)` — const, line 1359
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1371
- `const sel = window.getSelection()` — const, line 1372
- `const container = bodyRef.current` — const, line 1373
- `const range = sel.getRangeAt(0)` — const, line 1375
- `const nodes: Array<` — const, line 1376
- `const seen = new Set<string>()` — const, line 1377
- `const spanId = el.dataset.spanId` — const, line 1379
- `let intersects = false` — let, line 1381
- `const sub = document.createRange()` — const, line 1388
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1396
- `const block = renderBlocksBySpan.get(spanId)` — const, line 1401
- `const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1411
- `const cancelIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1412
- `const selectionSpanIds = useMemo( ()` — const, line 1413
- `const intentBox = useIntentBox(` — const, line 1417
- `const openActiveRail = useCallback(()` — const, line 1431
- `const activeCtl = useActiveReading(` — const, line 1435
- `const libraryCtl = useLibraryAsk(` — const, line 1444
- `const keptCtl = useKeptComparisons(` — const, line 1446
- `const notesCtl = useNoteMarks(` — const, line 1448
- `const pdfMarks = (): ReadonlyMap<string, ReactNode> | null` — const, line 1453
- `const cues = cueMarksFor("pdf")` — const, line 1454
- `const merged = new Map<string, ReactNode>(cues ?? [])` — const, line 1456
- `const cue = merged.get(spanId)` — const, line 1458
- `const before = merged.get(spanId)` — const, line 1463
- `const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null)` — const, line 1469
- `const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint)` — const, line 1471
- `const sbs = useSideBySide(` — const, line 1473
- `const node = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1481
- `const sbsPanes = sbs.panes && !comparing` — const, line 1494
- `const sbsPanesRef = useRef(false)` — const, line 1495
- `const sbsShownRef = useRef(false)` — const, line 1500
- `const sbsRef = useRef(sbs)` — const, line 1502
- `const sbsEscBusyRef = useRef(false)` — const, line 1505
- `const sbsPaneRef = useRef<HTMLDivElement | null>(null)` — const, line 1507
- `const runSideIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1512
- `const cancelSideIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1513
- `const sbsSection = sbs.section && sbs.target && sbs.section.sectionId === sbs.target.sectionId ? sbs.section : null` — const, line 1514
- `type BesideRun = |` — type, line 1529
- `const besideSeq = useRef(0)` — const, line 1538
- `const besideRunRef = useRef<(run: BesideRun)` — const, line 1541
- `const besideDroppedRef = useRef<(run: BesideRun)` — const, line 1542
- `const openBesideRef = useRef<(hit:` — const, line 1543
- `const snapshotBesideRef = useRef<(spanId: string)` — const, line 1550
- `const shown = sbsRef.current.target` — const, line 1552
- `const takeBesideBook = useCallback((book: SourceIdentity, spanId: string, run: BesideRun)` — const, line 1556
- `const id = ++besideSeq.current` — const, line 1558
- `const sideExtractionRef = useRef<string | null>(null)` — const, line 1570
- `const checkMeFromSideCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 1571
- `const side = useSidePane(` — const, line 1576
- `const besideRanRef = useRef(0)` — const, line 1605
- `const handoff = besideHandoff` — const, line 1607
- `const card = openCardRef.current` — const, line 1622
- `const trail = besideTrail(returnStackRef.current)` — const, line 1624
- `const work = handoff.run` — const, line 1633
- `const openComposer = useCallback((anchor: AskAnchor | null)` — const, line 1647
- `const sbsRowRef = useRef<HTMLDivElement | null>(null)` — const, line 1665
- `const startSbsResize = (event: ReactPointerEvent<HTMLDivElement>)` — const, line 1666
- `const row = sbsRowRef.current` — const, line 1667
- `const rect = row.getBoundingClientRect()` — const, line 1670
- `const move = (moved: PointerEvent)` — const, line 1671
- `const up = ()` — const, line 1674
- `const touchMain = ()` — const, line 1686
- `const onKey = (event: KeyboardEvent)` — const, line 1695
- `const target = event.target` — const, line 1697
- `const ctl = sbsRef.current` — const, line 1699
- `const open = ctl.panes || ctl.sheet` — const, line 1700
- `const shown = sbsShownRef.current` — const, line 1701
- `const mod = event.ctrlKey || event.metaKey` — const, line 1702
- `const side = sbsPaneRef.current` — const, line 1712
- `const inSide = target instanceof Element && Boolean(target.closest("[data-side-by-side-pane]"))` — const, line 1713
- `const inMain = target instanceof Node && Boolean(bodyRef.current?.contains(target))` — const, line 1719
- `const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false, anchor?: SourceIdentity)` — const, line 1729
- `const identity = anchor ?? identityOf(render)` — const, line 1736
- `const request =` — const, line 1737
- `const closeLibrary = useCallback(()` — const, line 1742
- `const onKey = (event: KeyboardEvent)` — const, line 1749
- `const onMouseUp = useCallback(()` — const, line 1760
- `const sel = window.getSelection()` — const, line 1761
- `const quote = sel.toString().replace(/\s+/g, " ").trim()` — const, line 1763
- `const nodes = collectSelectionNodes()` — const, line 1765
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1794
- `const domDragRef = useRef<` — const, line 1795
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1797
- `const host = bodyRef.current` — const, line 1798
- `const rect = host.getBoundingClientRect()` — const, line 1800
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1804
- `const target = event.target as Node` — const, line 1808
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1810
- `const domDrafting = domDraft !== null` — const, line 1822
- `const rectFrom = (drag:` — const, line 1825
- `const onMove = (event: MouseEvent)` — const, line 1831
- `const drag = domDragRef.current` — const, line 1832
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1834
- `const onUp = (event: MouseEvent)` — const, line 1837
- `const drag = domDragRef.current` — const, line 1838
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1842
- `const rect = rectFrom(drag, point)` — const, line 1844
- `const next = [...domBoxesRef.current, rect]` — const, line 1847
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1864
- `const host = bodyRef.current` — const, line 1865
- `const hostRect = host.getBoundingClientRect()` — const, line 1867
- `const clientBoxes = boxes.map((b)` — const, line 1868
- `const nodes: Array<` — const, line 1874
- `const seen = new Set<string>()` — const, line 1875
- `const spanId = el.dataset.spanId` — const, line 1877
- `const elRect = el.getBoundingClientRect()` — const, line 1879
- `const touches = clientBoxes.some( (b)` — const, line 1880
- `const words: string[] = []` — const, line 1884
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 1885
- `const text = node as Text` — const, line 1887
- `const wordPattern = /\S+/g` — const, line 1888
- `let match: RegExpExecArray | null` — let, line 1889
- `const range = document.createRange()` — const, line 1891
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 1894
- `const cx = (Math.min(...rects.map((r)` — const, line 1896
- `const cy = (Math.min(...rects.map((r)` — const, line 1897
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 1901
- `const commitDomBoxes = useCallback(()` — const, line 1910
- `const boxes = domBoxesRef.current` — const, line 1911
- `const nodes = resolveDomBoxes(boxes)` — const, line 1913
- `const quote = nodes.map((n)` — const, line 1919
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 1928
- `const clearDomBoxes = ()` — const, line 1936
- `const onKeyDown = (event: KeyboardEvent)` — const, line 1942
- `const onKeyUp = (event: KeyboardEvent)` — const, line 1947
- `const onBlur = ()` — const, line 1953
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 1975
- `const point = domPointFromClient(request.x, request.y)` — const, line 1977
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 1978
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 1999
- `const retryRequest = useCallback(async (requestId: string)` — const, line 2012
- `const optimisticSegments = useCallback( (nodes: string | Array<string |` — const, line 2026
- `const list = Array.isArray(nodes) ? nodes : [nodes]` — const, line 2028
- `const spanId = typeof node === "string" ? node : node.spanId` — const, line 2030
- `const geometry = pdfView?.blocks.find((b)` — const, line 2031
- `const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number" ?` — const, line 2032
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 2044
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 2048
- `const quotedNodes = (()` — const, line 2053
- `const multi = collectSelectionNodes()` — const, line 2056
- `const optimisticIds = quotedNodes ?? [target.spanId]` — const, line 2059
- `const nodes = quotedNodes ?? [` — const, line 2069
- `const receipt = await api.readerCapture(` — const, line 2070
- `const handler = (event: KeyboardEvent)` — const, line 2097
- `const clearSelection = useCallback(()` — const, line 2109
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 2121
- `const segment = a.segments.find((s)` — const, line 2123
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 2130
- `const alsoKeyRef = useRef<()` — const, line 2140
- `const onKey = (event: KeyboardEvent)` — const, line 2148
- `const target = event.target` — const, line 2151
- `const tabs: ReaderRailTab[] = ["guide", "ask", "notes"]` — const, line 2153
- `const askRequestSeen = useRef(askRequest)` — const, line 2191
- `const revealAskRef = useRef<()` — const, line 2193
- `const startCompareRef = useRef<(request: CompareRequest)` — const, line 2218
- `const sideAnchor = Boolean(side.extractionId) && side.extractionId === request.extractionId` — const, line 2221
- `const request = compareWaitsForWork` — const, line 2228
- `const sideMarksChanged = side.marksChanged` — const, line 2238
- `const captureIn = useCallback(async (target: PaneCaptureTarget, what:` — const, line 2239
- `const common =` — const, line 2244
- `const receipt: ReaderPresetReceiptDto = "preset" in what ? await api.readerInvokePreset(` — const, line 2249
- `const drained = await api.readerDrainOutbox()` — const, line 2260
- `const invokePreset = useCallback( // RW1b: the intent box passes its own words as the annotation's learner // text, and names the intention and entry in the funnel event. // Reader CA6b: `target` is side by side's second pane (its book, revision, // reading a…` — const, line 2281
- `const note_ = learnerTextOverride ?? note` — const, line 2289
- `const nodes = selectionNodes(selection)` — const, line 2290
- `const editedText = selection.editedText?.trim()` — const, line 2291
- `const receipt = await api.readerInvokePreset(` — const, line 2303
- `const drained = await api.readerDrainOutbox()` — const, line 2327
- `const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>, target?: PaneCaptureTarget): Promise<string | null>` — const, line 2350
- `const note_ = learnerTextOverride ?? note` — const, line 2354
- `const nodes = selectionNodes(selection)` — const, line 2355
- `const receipt = await api.readerCapture(` — const, line 2367
- `const pauseArc = useCallback(async ()` — const, line 2395
- `const next = await api.readerArc(` — const, line 2399
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 2406
- `const next = await api.readerArc(` — const, line 2411
- `const importJobRef = useRef<` — const, line 2423
- `const importExercise = useCallback(async (target?: PaneCaptureTarget): Promise<string | null>` — const, line 2426
- `const nodes = target ? target.nodes : selectionNodes(selection!)` — const, line 2428
- `const editedText = target ? undefined : selection!.editedText?.trim()` — const, line 2429
- `const receipt = await api.readerImportExercise(target ?` — const, line 2432
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 2480
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 2481
- `const timer = setInterval(async ()` — const, line 2485
- `const status = await api.readerExerciseImportStatus(` — const, line 2487
- `const job = importJobRef.current` — const, line 2488
- `const waited = Date.now() - job.startedAt` — const, line 2491
- `const saveOwnQuestion = useCallback(async ()` — const, line 2518
- `const saved = await api.readerAuthorQA(` — const, line 2526
- `const runCoach = useCallback(async ()` — const, line 2547
- `const lint = await api.readerCoachLint(` — const, line 2550
- `const changeMode = useCallback( async (next: string)` — const, line 2561
- `const previous = mode` — const, line 2563
- `const version = ++modeSaveVersionRef.current` — const, line 2566
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 2577
- `const answerModeNext = next as ReaderAnswerMode` — const, line 2579
- `const previous = answerMode` — const, line 2580
- `const version = ++answerModeSaveVersionRef.current` — const, line 2583
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 2599
- `const renderInquiryTop = useCallback((root: ReaderExchange)` — const, line 2614
- `const line = reconnect && reconnect.rootId === root.id && !muted ? ( <ReconnectLine placement="rail" question=` — const, line 2617
- `const check = inquiryChecks[root.id]` — const, line 2627
- `const inlineReconnect = reconnect && reconnect.inline && !muted ? ( <ReconnectLine placement="inline" question=` — const, line 2655
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 2666
- `const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">): Promise<OpenOutcome>` — const, line 2684
- `const card = (library ?? []).find((candidate)` — const, line 2689
- `const spanId = readingSpan ?? activeSpan` — const, line 2692
- `const openFollowedFigure = (figure: CorrespondentFigureDto, hit: CorrespondentSectionDto)` — const, line 2707
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2709
- `const compareFoundSection = (hit: CorrespondentSectionDto)` — const, line 2724
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2726
- `const hideAlsoInBooks = (scope: "book" | "everywhere")` — const, line 2749
- `const before = alsoPrefs ??` — const, line 2751
- `const base = contract` — const, line 2758
- `const makeExplorable = (target: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, origin: "library" | "tutor", offerRef: string): Promise<ExplorableOutcome>` — const, line 2775
- `let settle: (outcome: ExplorableOutcome)` — let, line 2782
- `const settled = new Promise<ExplorableOutcome>((resolve)` — const, line 2783
- `const press: OfferedPress =` — const, line 2784
- `const peekWorkbenchPassage = (spanId: string, target?: PassageTarget)` — const, line 2803
- `const exerciseSettings = libraryCtl.enabled ? contract?.libraryExercises ?? null : null` — const, line 2814
- `const exerciseCard = (sourceId: string | null)` — const, line 2815
- `const useExercise = (candidate: ExerciseCandidate)` — const, line 2819
- `const card = exerciseCard(candidate.sourceId ?? render?.sourceId ?? null)` — const, line 2820
- `const openExerciseInBook = (candidate: ExerciseCandidate)` — const, line 2829
- `const sourceId = candidate.sourceId ?? render?.sourceId ?? null` — const, line 2830
- `const exerciseProps: LibraryExercisesProps | null = exerciseSettings ?` — const, line 2833
- `const pickLibraryPagePractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 2847
- `const hit = libraryCtl.state?.ask.value?.hits[0]` — const, line 2848
- `const card = hit ? (library ?? []).find((candidate)` — const, line 2849
- `const readySources = library ?? []` — const, line 2892
- `const useShelf = Boolean(shelf) && !sidecarDown` — const, line 2894
- `const card = (library ?? []).find((candidate)` — const, line 2952
- `const card = (library ?? []).find((c)` — const, line 2973
- `const receiptId = searchResults.retrievalReceiptId` — const, line 2979
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 3024
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 3025
- `const wbActive = wbCtl.active` — const, line 3068
- `const wbStacked = working && wbCtl.narrow` — const, line 3069
- `const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible)` — const, line 3072
- `const wbSourceShown = !wbStacked || wbCtl.sheetOpen` — const, line 3073
- `const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry)` — const, line 3074
- `const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>()` — const, line 3075
- `const first = entry.spanIds[0]` — const, line 3077
- `const wbLabel = (stem: string)` — const, line 3080
- `const title = problemTitle(stem)` — const, line 3081
- `const tryPathExercise = (exercise: ReadingPathExerciseDto)` — const, line 3086
- `const workThroughSelection = ()` — const, line 3094
- `const nodes = selectionNodes(selection)` — const, line 3096
- `const editedText = selection.editedText?.trim()` — const, line 3097
- `const foldBlocks = contract?.activeReading?.foldBlocks ?? 3` — const, line 3114
- `const localFold = (spanIds: string[]): string[]` — const, line 3115
- `const positions = spanIds.map((spanId)` — const, line 3116
- `const last = Math.max(...positions)` — const, line 3118
- `const mainPane: IntentPane =` — const, line 3127
- `const sidePane: IntentPane | null = side.extractionId ?` — const, line 3136
- `const sideMeta = (pane: IntentPane): Record<string, string>` — const, line 3146
- `const runIntentIn = (pane: IntentPane, action: ReaderIntentActionDto, text: string, how: IntentRunHow): Promise<IntentRunHandle | null> | void` — const, line 3148
- `const meta =` — const, line 3149
- `const effect = action.effect` — const, line 3150
- `const sideSection = pane.side?.section ?? null` — const, line 3151
- `const anchor: AskAnchor =` — const, line 3157
- `const target = pane.side.target` — const, line 3198
- `const target = pane.side.target` — const, line 3204
- `const target = pane.side.target` — const, line 3210
- `const target = pane.side.target` — const, line 3220
- `const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null` — const, line 3265
- `const request: CompareRequest =` — const, line 3266
- `const region = pane.region` — const, line 3298
- `const words = text?.trim()` — const, line 3299
- `const sideShows = (extractionId: string, spanId: string): boolean` — const, line 3320
- `const checkBeside = (book: SourceIdentity, spanId: string, practiceItemId: string, proposalId: string | null)` — const, line 3323
- `const workThroughImported = (item:` — const, line 3328
- `const imported = exerciseImport` — const, line 3329
- `const spanIds = imported?.spanIds ?? (activeSpan ? [activeSpan] : [])` — const, line 3330
- `const settleShowMeLine = (key: string, patch: Partial<ShowMeLine>)` — const, line 3338
- `const requestShowMe = (ctl: FiguresCtl, run: Extract<BesideRun,` — const, line 3341
- `const key = run.lineKey` — const, line 3342
- `const runOnBook = (about: AskAbout, run: Extract<BesideRun,` — const, line 3354
- `const showMeFromAsk = ()` — const, line 3379
- `const goal = question.trim()` — const, line 3380
- `const about = parentExchange ? parentExchange.about ?? null : askComposerAnchor?.about ?? null` — const, line 3381
- `const home = parentExchange?.spanId ?? (about ? askComposerAnchor?.spanId : undefined) ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan` — const, line 3382
- `const key = `show_me:$` — const, line 3385
- `const run =` — const, line 3388
- `const cancelIntentIn = (pane: IntentPane, cancel: IntentCancel)` — const, line 3397
- `const kind = cancel.action.effect.kind` — const, line 3398
- `const annotationId = handle.annotationId` — const, line 3405
- `const batchId = handle.importBatchId` — const, line 3422
- `const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number)` — const, line 3436
- `const spanId = wbCtl.close(session,` — const, line 3438
- `const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3444
- `const card = openCardRef.current` — const, line 3445
- `const asked = libraryCtl.state?.request` — const, line 3449
- `const resumeMark = (spanId: string | null | undefined)` — const, line 3457
- `const entry = spanId ? wbResumeBySpan.get(spanId) : undefined` — const, line 3458
- `const verb = entry.status === "abandoned" ? "Reopen" : "Resume"` — const, line 3460
- `const target = event.target` — const, line 3584
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 3759
- `const active = activeSpan === block.spanId` — const, line 3760
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 3761
- `const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null` — const, line 3762
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 3763
- `const endQuestionAvailable = Boolean(endSection && endSection.question?.readingPhase === "after_section" && offeredCheckSections.has(endSection.id))` — const, line 3765
- `const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId))` — const, line 3769
- `const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""))` — const, line 3770
- `const offerSection = endSection && !muted && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 3771
- `const sel = window.getSelection()` — const, line 3790
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 3791
- `const cue = side.cues.markOn(spanId)` — const, line 3881
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 3909
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 3932
- `const active = railTab === tab` — const, line 4045
- `const waiting = tab === "guide" && pendingQuickCheckCount > 0` — const, line 4049
- `const marked = tab === "ask" && askTabMarked && !active` — const, line 4050
- `const params = (action.params ??` — const, line 4197
- `const run =` — const, line 4467
- `const book = exchange?.about ?? render` — const, line 4476

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

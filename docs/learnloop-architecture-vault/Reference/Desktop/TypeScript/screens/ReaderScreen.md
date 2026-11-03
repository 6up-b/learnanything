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
source_commit: "63aafe919913aeb354b178e53e55ecb4d57b7c47"
source_commit_timestamp: "2026-11-02T21:23:47-05:00"
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
| Source lines | 4657 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `63aafe919913aeb354b178e53e55ecb4d57b7c47` |
| Commit timestamp | `2026-11-02T21:23:47-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]]

## Public API

- `export interface ReaderOpenSource` — interface, line 239
- `export interface ReaderCheckMeRequest extends CueCheckMeRequest` — interface, line 255
- `export type ReaderExerciseRequest = ReaderWorkbenchExercise &` — type, line 268
- `export const SIDE_PATH_COPY =` — const, line 272
- `export function ReaderScreen(` — function, line 294

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
- `const FIGURE_PAGE_NOT_OPENED = "That page couldn't be opened."` — const, line 181
- `type OpenOutcome = "opened" | "preparing" | "not_opened"` — type, line 184
- `interface OfferedPress` — interface, line 188
- `const OFFER_OUTCOME: Record<FigureRequestOutcome, ExplorableOutcome> =` — const, line 199
- `const BADGED_HEALTH = new Set(["suspect", "failed"])` — const, line 205
- `interface RemovedAnnotation` — interface, line 209
- `const UNDO_REMOVE_MS = 10_000` — const, line 219
- `function newKey(): string` — function, line 221
- `function identityOf(view: Pick<ReaderRenderViewDto, "sourceId" | "revisionId" | "extractionId">): SourceIdentity` — function, line 230
- `function sectionIdentity(section:` — function, line 235
- `const mainPaneOwnsCueKey = (event: KeyboardEvent): boolean` — const, line 279
- `interface IntentPane` — interface, line 284
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 340
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 344
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 353
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 354
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 355
- `const openingRef = useRef<string | null>(null)` — const, line 361
- `const askPanelOn = algoConfig().ask !== null` — const, line 382
- `const storedStyle = useStoredHelpStyle()` — const, line 383
- `const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen` — const, line 384
- `const pdfViewRequestRef = useRef(0)` — const, line 406
- `const sourceEpochRef = useRef(0)` — const, line 437
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 448
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 449
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 450
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 451
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 452
- `const modeSaveVersionRef = useRef(0)` — const, line 453
- `const answerModeSaveVersionRef = useRef(0)` — const, line 454
- `const enabled = contract?.readerEnabled ?? true` — const, line 470
- `const inquiry = contract?.inquiryEnabled === true` — const, line 473
- `const muted = inquiry && mode === "skim"` — const, line 476
- `const intentContract = inquiry && !offline ? contract?.intent ?? null : null` — const, line 479
- `const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading)` — const, line 480
- `const openFigureSource = useRef<((extractionId: string, spanId: string)` — const, line 484
- `const figureOpenSource = useCallback((extractionId: string, spanId: string)` — const, line 485
- `const figuresCtl = useFigures(` — const, line 486
- `const figureOffersOn = Boolean(contract?.figures?.offers) && !offline` — const, line 492
- `const showMeOn = Boolean(contract?.figures?.showMe) && !offline` — const, line 496
- `const waitingOfferRef = useRef<OfferedPress | null>(null)` — const, line 502
- `const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome)` — const, line 507
- `const press = offeredFigure` — const, line 514
- `const open = render?.extractionId ?? null` — const, line 516
- `const readerTutor = contract?.readerTutor ?? null` — const, line 539
- `const askWorkbenchSessionRef = useRef<string | null>(null)` — const, line 541
- `const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true` — const, line 546
- `const askPersonalizedRef = useRef<boolean | null>(null)` — const, line 547
- `const askComposerAnchorRef = useRef<AskAnchor | null>(null)` — const, line 552
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 558
- `const renderBlocksBySpan = useMemo( ()` — const, line 562
- `const visit = useReaderVisit(` — const, line 568
- `const showGuideRail = useCallback(()` — const, line 574
- `const progress = useReadingProgress(` — const, line 578
- `const doseVisitId = useCallback(()` — const, line 595
- `const refreshAnnotations = useCallback(async ()` — const, line 597
- `const epoch = sourceEpochRef.current` — const, line 599
- `const result = await cachedSourceRead( render.sourceId, ["reader_source_annotations", render.sourceId, render.extractionId], ()` — const, line 603
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 610
- `const version = (r.version as Record<string, unknown>) ??` — const, line 613
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 614
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 615
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 616
- `const placement = r.placement as ReaderAnnotationPlacementDto | undefined` — const, line 617
- `let page: number | null = null` — let, line 627
- `let bbox: number[] | null = null` — let, line 628
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 630
- `const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?:` — const, line 648
- `const openCardRef = useRef<SourceLibraryCard | null>(null)` — const, line 673
- `const openExtractionRef = useRef<string | null>(null)` — const, line 675
- `const reloadGuidePlan = useCallback(async ()` — const, line 677
- `const extractionId = render.extractionId` — const, line 679
- `const plan = await readGuidePlan(render.sourceId, extractionId,` — const, line 681
- `const spanOrder = useMemo( ()` — const, line 694
- `const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none"` — const, line 698
- `const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 701
- `const card = openCardRef.current` — const, line 702
- `const wbProps = useMemo<ReaderWorkbenchProps | undefined>(()` — const, line 712
- `const submitted = workbench?.onSubmitted` — const, line 713
- `const trail = besideTrail(returnStackRef.current)` — const, line 718
- `const wbCtl = useReaderWorkbench(` — const, line 723
- `const working = wbCtl.active !== null` — const, line 730
- `const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline` — const, line 734
- `const alsoHidden = alsoPrefs ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId)) : Boolean(contract?.correspondence?.hiddenEverywhere) || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.so…` — const, line 739
- `const peekCrumbShown = alsoPeek ?? findPeek` — const, line 749
- `const pathRefreshKey = readingPathRefreshKey(` — const, line 764
- `const tryFirstRef = useRef<((spanId: string)` — const, line 778
- `const cueCtl = useReaderCues(` — const, line 779
- `const recapCtl = useReaderRecap(` — const, line 794
- `const recapShown = Boolean(recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working)` — const, line 808
- `const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip")` — const, line 819
- `const root = history.find((entry)` — const, line 820
- `const recapRevisited = useCallback((rootId: string)` — const, line 833
- `const root = history.find((entry)` — const, line 834
- `const recapRevisit = useCallback(async (rootId: string)` — const, line 837
- `const root = history.find((entry)` — const, line 838
- `const recapOpenInquiry = useCallback((rootId: string, spanId: string)` — const, line 844
- `const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch")` — const, line 847
- `const cueMarksFor = (markSurface: "pdf" | "watch")` — const, line 867
- `let cancelled = false` — let, line 876
- `const scroller = railRef.current` — const, line 909
- `const clamp = ()` — const, line 911
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 912
- `const observer = new ResizeObserver(clamp)` — const, line 915
- `const query = librarySearch.trim()` — const, line 926
- `let cancelled = false` — let, line 933
- `const timer = window.setTimeout(()` — const, line 936
- `const resetSourceState = useCallback(()` — const, line 959
- `const openSource = useCallback( async ( card: SourceLibraryCard, jumpSpan?: string, // jumpReading: the reading jumpSpan was found on (a search hit, a // return)` — const, line 1008
- `const handoff = options.handoff ?? null` — const, line 1017
- `const view = await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 1035
- `const pdfRequest = ++pdfViewRequestRef.current` — const, line 1082
- `const current = ()` — const, line 1083
- `const openFixture = useCallback(()` — const, line 1118
- `const backToLibrary = useCallback(()` — const, line 1126
- `const spanId = readingSpan ?? activeSpan` — const, line 1130
- `const section = guidePlan?.sections.find((candidate)` — const, line 1131
- `const resumedRef = useRef(false)` — const, line 1149
- `const trail = initialSource.besideTrail ?? null` — const, line 1153
- `const activeBlock = useMemo(()` — const, line 1167
- `const pdfHighlights: PdfHighlight[] = useMemo(()` — const, line 1176
- `const list: PdfHighlight[] = []` — const, line 1177
- `const base =` — const, line 1180
- `const placed = highlightFromPlacement(base, a.placement)` — const, line 1182
- `const segments = a.segments.flatMap((s)` — const, line 1187
- `const annotatedSpans = useMemo( ()` — const, line 1194
- `const boundaryBlock = useMemo(()` — const, line 1198
- `const revealedPassages = useMemo(()` — const, line 1200
- `const revealed = new Set(revealedSections)` — const, line 1201
- `const map = new Map<string,` — const, line 1202
- `const revealedGuidanceSpans = useMemo(()` — const, line 1211
- `const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null` — const, line 1216
- `const protectedSelection = selectionProtected(protection, selection)` — const, line 1217
- `const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1218
- `const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan))` — const, line 1222
- `const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1223
- `const editCaptureText = useCallback((text: string)` — const, line 1228
- `const resetCaptureText = useCallback(()` — const, line 1231
- `const saveAnnotationEdit = useCallback(async ()` — const, line 1243
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 1265
- `const result = await api.readerReanchor(` — const, line 1269
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1286
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1309
- `const target = annotations.find((a)` — const, line 1310
- `const reading = render ?` — const, line 1311
- `const epoch = sourceEpochRef.current` — const, line 1312
- `const undoRemove = useCallback(async ()` — const, line 1327
- `const last = removed` — const, line 1328
- `const epoch = sourceEpochRef.current` — const, line 1334
- `const result = await api.readerRestoreAnnotation(` — const, line 1336
- `const timer = window.setTimeout(()` — const, line 1349
- `const onKey = (event: KeyboardEvent)` — const, line 1355
- `const target = event.target` — const, line 1358
- `const openAnnotationNote = useCallback((annotationId: string)` — const, line 1367
- `const target = annotations.find((a)` — const, line 1368
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1380
- `const sel = window.getSelection()` — const, line 1381
- `const container = bodyRef.current` — const, line 1382
- `const range = sel.getRangeAt(0)` — const, line 1384
- `const nodes: Array<` — const, line 1385
- `const seen = new Set<string>()` — const, line 1386
- `const spanId = el.dataset.spanId` — const, line 1388
- `let intersects = false` — let, line 1390
- `const sub = document.createRange()` — const, line 1397
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1405
- `const block = renderBlocksBySpan.get(spanId)` — const, line 1410
- `const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1420
- `const cancelIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1421
- `const selectionSpanIds = useMemo( ()` — const, line 1422
- `const intentBox = useIntentBox(` — const, line 1426
- `const openActiveRail = useCallback(()` — const, line 1440
- `const activeCtl = useActiveReading(` — const, line 1444
- `const libraryCtl = useLibraryAsk(` — const, line 1453
- `const keptCtl = useKeptComparisons(` — const, line 1455
- `const notesCtl = useNoteMarks(` — const, line 1457
- `const pdfMarks = (): ReadonlyMap<string, ReactNode> | null` — const, line 1462
- `const cues = cueMarksFor("pdf")` — const, line 1463
- `const merged = new Map<string, ReactNode>(cues ?? [])` — const, line 1465
- `const cue = merged.get(spanId)` — const, line 1467
- `const before = merged.get(spanId)` — const, line 1472
- `const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null)` — const, line 1478
- `const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint)` — const, line 1480
- `const sbs = useSideBySide(` — const, line 1482
- `const node = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1490
- `const sbsPanes = sbs.panes && !comparing` — const, line 1503
- `const sbsPanesRef = useRef(false)` — const, line 1504
- `const sbsShownRef = useRef(false)` — const, line 1509
- `const sbsRef = useRef(sbs)` — const, line 1511
- `const sbsEscBusyRef = useRef(false)` — const, line 1514
- `const sbsPaneRef = useRef<HTMLDivElement | null>(null)` — const, line 1516
- `const runSideIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1521
- `const cancelSideIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1522
- `const sbsSection = sbs.section && sbs.target && sbs.section.sectionId === sbs.target.sectionId ? sbs.section : null` — const, line 1523
- `type BesideRun = |` — type, line 1538
- `const besideSeq = useRef(0)` — const, line 1547
- `const besideRunRef = useRef<(run: BesideRun)` — const, line 1550
- `const besideDroppedRef = useRef<(run: BesideRun)` — const, line 1551
- `const openBesideRef = useRef<(hit:` — const, line 1552
- `const snapshotBesideRef = useRef<(spanId: string)` — const, line 1559
- `const shown = sbsRef.current.target` — const, line 1561
- `const takeBesideBook = useCallback((book: SourceIdentity, spanId: string, run: BesideRun)` — const, line 1565
- `const id = ++besideSeq.current` — const, line 1567
- `const sideExtractionRef = useRef<string | null>(null)` — const, line 1579
- `const checkMeFromSideCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 1580
- `const side = useSidePane(` — const, line 1585
- `const besideRanRef = useRef(0)` — const, line 1614
- `const handoff = besideHandoff` — const, line 1616
- `const card = openCardRef.current` — const, line 1631
- `const trail = besideTrail(returnStackRef.current)` — const, line 1633
- `const work = handoff.run` — const, line 1642
- `const openComposer = useCallback((anchor: AskAnchor | null)` — const, line 1656
- `const sbsRowRef = useRef<HTMLDivElement | null>(null)` — const, line 1674
- `const startSbsResize = (event: ReactPointerEvent<HTMLDivElement>)` — const, line 1675
- `const row = sbsRowRef.current` — const, line 1676
- `const rect = row.getBoundingClientRect()` — const, line 1679
- `const move = (moved: PointerEvent)` — const, line 1680
- `const up = ()` — const, line 1683
- `const touchMain = ()` — const, line 1695
- `const onKey = (event: KeyboardEvent)` — const, line 1704
- `const target = event.target` — const, line 1706
- `const ctl = sbsRef.current` — const, line 1708
- `const open = ctl.panes || ctl.sheet` — const, line 1709
- `const shown = sbsShownRef.current` — const, line 1710
- `const mod = event.ctrlKey || event.metaKey` — const, line 1711
- `const side = sbsPaneRef.current` — const, line 1721
- `const inSide = target instanceof Element && Boolean(target.closest("[data-side-by-side-pane]"))` — const, line 1722
- `const inMain = target instanceof Node && Boolean(bodyRef.current?.contains(target))` — const, line 1728
- `const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false, anchor?: SourceIdentity)` — const, line 1738
- `const identity = anchor ?? identityOf(render)` — const, line 1745
- `const request =` — const, line 1746
- `const closeLibrary = useCallback(()` — const, line 1751
- `const onKey = (event: KeyboardEvent)` — const, line 1758
- `const onMouseUp = useCallback(()` — const, line 1769
- `const sel = window.getSelection()` — const, line 1770
- `const quote = sel.toString().replace(/\s+/g, " ").trim()` — const, line 1772
- `const nodes = collectSelectionNodes()` — const, line 1774
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1803
- `const domDragRef = useRef<` — const, line 1804
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1806
- `const host = bodyRef.current` — const, line 1807
- `const rect = host.getBoundingClientRect()` — const, line 1809
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1813
- `const target = event.target as Node` — const, line 1817
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1819
- `const domDrafting = domDraft !== null` — const, line 1831
- `const rectFrom = (drag:` — const, line 1834
- `const onMove = (event: MouseEvent)` — const, line 1840
- `const drag = domDragRef.current` — const, line 1841
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1843
- `const onUp = (event: MouseEvent)` — const, line 1846
- `const drag = domDragRef.current` — const, line 1847
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1851
- `const rect = rectFrom(drag, point)` — const, line 1853
- `const next = [...domBoxesRef.current, rect]` — const, line 1856
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1873
- `const host = bodyRef.current` — const, line 1874
- `const hostRect = host.getBoundingClientRect()` — const, line 1876
- `const clientBoxes = boxes.map((b)` — const, line 1877
- `const nodes: Array<` — const, line 1883
- `const seen = new Set<string>()` — const, line 1884
- `const spanId = el.dataset.spanId` — const, line 1886
- `const elRect = el.getBoundingClientRect()` — const, line 1888
- `const touches = clientBoxes.some( (b)` — const, line 1889
- `const words: string[] = []` — const, line 1893
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 1894
- `const text = node as Text` — const, line 1896
- `const wordPattern = /\S+/g` — const, line 1897
- `let match: RegExpExecArray | null` — let, line 1898
- `const range = document.createRange()` — const, line 1900
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 1903
- `const cx = (Math.min(...rects.map((r)` — const, line 1905
- `const cy = (Math.min(...rects.map((r)` — const, line 1906
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 1910
- `const commitDomBoxes = useCallback(()` — const, line 1919
- `const boxes = domBoxesRef.current` — const, line 1920
- `const nodes = resolveDomBoxes(boxes)` — const, line 1922
- `const quote = nodes.map((n)` — const, line 1928
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 1937
- `const clearDomBoxes = ()` — const, line 1945
- `const onKeyDown = (event: KeyboardEvent)` — const, line 1951
- `const onKeyUp = (event: KeyboardEvent)` — const, line 1956
- `const onBlur = ()` — const, line 1962
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 1984
- `const point = domPointFromClient(request.x, request.y)` — const, line 1986
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 1987
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 2008
- `const retryRequest = useCallback(async (requestId: string)` — const, line 2021
- `const optimisticSegments = useCallback( (nodes: string | Array<string |` — const, line 2035
- `const list = Array.isArray(nodes) ? nodes : [nodes]` — const, line 2037
- `const spanId = typeof node === "string" ? node : node.spanId` — const, line 2039
- `const geometry = pdfView?.blocks.find((b)` — const, line 2040
- `const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number" ?` — const, line 2041
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 2053
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 2057
- `const quotedNodes = (()` — const, line 2062
- `const multi = collectSelectionNodes()` — const, line 2065
- `const optimisticIds = quotedNodes ?? [target.spanId]` — const, line 2068
- `const nodes = quotedNodes ?? [` — const, line 2078
- `const receipt = await api.readerCapture(` — const, line 2079
- `const handler = (event: KeyboardEvent)` — const, line 2106
- `const clearSelection = useCallback(()` — const, line 2118
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 2130
- `const segment = a.segments.find((s)` — const, line 2132
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 2139
- `const alsoKeyRef = useRef<()` — const, line 2149
- `const onKey = (event: KeyboardEvent)` — const, line 2157
- `const target = event.target` — const, line 2160
- `const tabs: ReaderRailTab[] = ["guide", "ask", "notes"]` — const, line 2162
- `const askRequestSeen = useRef(askRequest)` — const, line 2200
- `const revealAskRef = useRef<()` — const, line 2202
- `const startCompareRef = useRef<(request: CompareRequest)` — const, line 2227
- `const sideAnchor = Boolean(side.extractionId) && side.extractionId === request.extractionId` — const, line 2230
- `const request = compareWaitsForWork` — const, line 2237
- `const sideMarksChanged = side.marksChanged` — const, line 2247
- `const captureIn = useCallback(async (target: PaneCaptureTarget, what:` — const, line 2248
- `const common =` — const, line 2253
- `const receipt: ReaderPresetReceiptDto = "preset" in what ? await api.readerInvokePreset(` — const, line 2258
- `const drained = await api.readerDrainOutbox()` — const, line 2269
- `const invokePreset = useCallback( // RW1b: the intent box passes its own words as the annotation's learner // text, and names the intention and entry in the funnel event. // Reader CA6b: `target` is side by side's second pane (its book, revision, // reading a…` — const, line 2290
- `const note_ = learnerTextOverride ?? note` — const, line 2298
- `const nodes = selectionNodes(selection)` — const, line 2299
- `const editedText = selection.editedText?.trim()` — const, line 2300
- `const receipt = await api.readerInvokePreset(` — const, line 2312
- `const drained = await api.readerDrainOutbox()` — const, line 2336
- `const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>, target?: PaneCaptureTarget): Promise<string | null>` — const, line 2359
- `const note_ = learnerTextOverride ?? note` — const, line 2363
- `const nodes = selectionNodes(selection)` — const, line 2364
- `const receipt = await api.readerCapture(` — const, line 2376
- `const pauseArc = useCallback(async ()` — const, line 2404
- `const next = await api.readerArc(` — const, line 2408
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 2415
- `const next = await api.readerArc(` — const, line 2420
- `const importJobRef = useRef<` — const, line 2432
- `const importExercise = useCallback(async (target?: PaneCaptureTarget): Promise<string | null>` — const, line 2435
- `const nodes = target ? target.nodes : selectionNodes(selection!)` — const, line 2437
- `const editedText = target ? undefined : selection!.editedText?.trim()` — const, line 2438
- `const receipt = await api.readerImportExercise(target ?` — const, line 2441
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 2489
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 2490
- `const timer = setInterval(async ()` — const, line 2494
- `const status = await api.readerExerciseImportStatus(` — const, line 2496
- `const job = importJobRef.current` — const, line 2497
- `const waited = Date.now() - job.startedAt` — const, line 2500
- `const saveOwnQuestion = useCallback(async ()` — const, line 2527
- `const saved = await api.readerAuthorQA(` — const, line 2535
- `const runCoach = useCallback(async ()` — const, line 2556
- `const lint = await api.readerCoachLint(` — const, line 2559
- `const changeMode = useCallback( async (next: string)` — const, line 2570
- `const previous = mode` — const, line 2572
- `const version = ++modeSaveVersionRef.current` — const, line 2575
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 2586
- `const answerModeNext = next as ReaderAnswerMode` — const, line 2588
- `const previous = answerMode` — const, line 2589
- `const version = ++answerModeSaveVersionRef.current` — const, line 2592
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 2608
- `const renderInquiryTop = useCallback((root: ReaderExchange)` — const, line 2623
- `const line = reconnect && reconnect.rootId === root.id && !muted ? ( <ReconnectLine placement="rail" question=` — const, line 2626
- `const check = inquiryChecks[root.id]` — const, line 2636
- `const inlineReconnect = reconnect && reconnect.inline && !muted ? ( <ReconnectLine placement="inline" question=` — const, line 2664
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 2675
- `const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">): Promise<OpenOutcome>` — const, line 2693
- `const card = (library ?? []).find((candidate)` — const, line 2698
- `const spanId = readingSpan ?? activeSpan` — const, line 2701
- `const card = (library ?? []).find((candidate)` — const, line 2727
- `const openFollowedFigure = (figure: CorrespondentFigureDto, hit: CorrespondentSectionDto)` — const, line 2733
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2735
- `const compareFoundSection = (hit: CorrespondentSectionDto)` — const, line 2750
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2752
- `const hideAlsoInBooks = (scope: "book" | "everywhere")` — const, line 2775
- `const before = alsoPrefs ??` — const, line 2777
- `const base = contract` — const, line 2784
- `const makeExplorable = (target: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, origin: "library" | "tutor", offerRef: string): Promise<ExplorableOutcome>` — const, line 2801
- `let settle: (outcome: ExplorableOutcome)` — let, line 2808
- `const settled = new Promise<ExplorableOutcome>((resolve)` — const, line 2809
- `const press: OfferedPress =` — const, line 2810
- `const peekWorkbenchPassage = (spanId: string, target?: PassageTarget)` — const, line 2829
- `const exerciseSettings = libraryCtl.enabled ? contract?.libraryExercises ?? null : null` — const, line 2840
- `const exerciseCard = (sourceId: string | null)` — const, line 2841
- `const useExercise = (candidate: ExerciseCandidate)` — const, line 2845
- `const card = exerciseCard(candidate.sourceId ?? render?.sourceId ?? null)` — const, line 2846
- `const openExerciseInBook = (candidate: ExerciseCandidate)` — const, line 2855
- `const sourceId = candidate.sourceId ?? render?.sourceId ?? null` — const, line 2856
- `const exerciseProps: LibraryExercisesProps | null = exerciseSettings ?` — const, line 2859
- `const pickLibraryPagePractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 2873
- `const hit = libraryCtl.state?.ask.value?.hits[0]` — const, line 2874
- `const card = hit ? (library ?? []).find((candidate)` — const, line 2875
- `const readySources = library ?? []` — const, line 2918
- `const useShelf = Boolean(shelf) && !sidecarDown` — const, line 2920
- `const card = (library ?? []).find((candidate)` — const, line 2978
- `const card = (library ?? []).find((c)` — const, line 2999
- `const receiptId = searchResults.retrievalReceiptId` — const, line 3005
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 3050
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 3051
- `const wbActive = wbCtl.active` — const, line 3094
- `const wbStacked = working && wbCtl.narrow` — const, line 3095
- `const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible)` — const, line 3098
- `const wbSourceShown = !wbStacked || wbCtl.sheetOpen` — const, line 3099
- `const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry)` — const, line 3100
- `const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>()` — const, line 3101
- `const first = entry.spanIds[0]` — const, line 3103
- `const wbLabel = (stem: string)` — const, line 3106
- `const title = problemTitle(stem)` — const, line 3107
- `const tryPathExercise = (exercise: ReadingPathExerciseDto)` — const, line 3112
- `const workThroughSelection = ()` — const, line 3120
- `const nodes = selectionNodes(selection)` — const, line 3122
- `const editedText = selection.editedText?.trim()` — const, line 3123
- `const foldBlocks = contract?.activeReading?.foldBlocks ?? 3` — const, line 3140
- `const localFold = (spanIds: string[]): string[]` — const, line 3141
- `const positions = spanIds.map((spanId)` — const, line 3142
- `const last = Math.max(...positions)` — const, line 3144
- `const mainPane: IntentPane =` — const, line 3153
- `const sidePane: IntentPane | null = side.extractionId ?` — const, line 3162
- `const sideMeta = (pane: IntentPane): Record<string, string>` — const, line 3172
- `const runIntentIn = (pane: IntentPane, action: ReaderIntentActionDto, text: string, how: IntentRunHow): Promise<IntentRunHandle | null> | void` — const, line 3174
- `const meta =` — const, line 3175
- `const effect = action.effect` — const, line 3176
- `const sideSection = pane.side?.section ?? null` — const, line 3177
- `const anchor: AskAnchor =` — const, line 3183
- `const target = pane.side.target` — const, line 3224
- `const target = pane.side.target` — const, line 3230
- `const target = pane.side.target` — const, line 3236
- `const target = pane.side.target` — const, line 3246
- `const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null` — const, line 3291
- `const request: CompareRequest =` — const, line 3292
- `const region = pane.region` — const, line 3324
- `const words = text?.trim()` — const, line 3325
- `const sideShows = (extractionId: string, spanId: string): boolean` — const, line 3346
- `const checkBeside = (book: SourceIdentity, spanId: string, practiceItemId: string, proposalId: string | null)` — const, line 3349
- `const workThroughImported = (item:` — const, line 3354
- `const imported = exerciseImport` — const, line 3355
- `const spanIds = imported?.spanIds ?? (activeSpan ? [activeSpan] : [])` — const, line 3356
- `const settleShowMeLine = (key: string, patch: Partial<ShowMeLine>)` — const, line 3364
- `const requestShowMe = (ctl: FiguresCtl, run: Extract<BesideRun,` — const, line 3367
- `const key = run.lineKey` — const, line 3368
- `const runOnBook = (about: AskAbout, run: Extract<BesideRun,` — const, line 3380
- `const showMeFromAsk = ()` — const, line 3405
- `const goal = question.trim()` — const, line 3406
- `const about = parentExchange ? parentExchange.about ?? null : askComposerAnchor?.about ?? null` — const, line 3407
- `const home = parentExchange?.spanId ?? (about ? askComposerAnchor?.spanId : undefined) ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan` — const, line 3408
- `const key = `show_me:$` — const, line 3411
- `const run =` — const, line 3414
- `const cancelIntentIn = (pane: IntentPane, cancel: IntentCancel)` — const, line 3423
- `const kind = cancel.action.effect.kind` — const, line 3424
- `const annotationId = handle.annotationId` — const, line 3431
- `const batchId = handle.importBatchId` — const, line 3448
- `const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number)` — const, line 3462
- `const spanId = wbCtl.close(session,` — const, line 3464
- `const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3470
- `const card = openCardRef.current` — const, line 3471
- `const asked = libraryCtl.state?.request` — const, line 3475
- `const resumeMark = (spanId: string | null | undefined)` — const, line 3483
- `const entry = spanId ? wbResumeBySpan.get(spanId) : undefined` — const, line 3484
- `const verb = entry.status === "abandoned" ? "Reopen" : "Resume"` — const, line 3486
- `const target = event.target` — const, line 3610
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 3785
- `const active = activeSpan === block.spanId` — const, line 3786
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 3787
- `const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null` — const, line 3788
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 3789
- `const endQuestionAvailable = Boolean(endSection && endSection.question?.readingPhase === "after_section" && offeredCheckSections.has(endSection.id))` — const, line 3791
- `const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId))` — const, line 3795
- `const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""))` — const, line 3796
- `const offerSection = endSection && !muted && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 3797
- `const sel = window.getSelection()` — const, line 3816
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 3817
- `const cue = side.cues.markOn(spanId)` — const, line 3907
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 3935
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 3958
- `const active = railTab === tab` — const, line 4071
- `const waiting = tab === "guide" && pendingQuickCheckCount > 0` — const, line 4075
- `const marked = tab === "ask" && askTabMarked && !active` — const, line 4076
- `const params = (action.params ??` — const, line 4223
- `const run =` — const, line 4495
- `const book = exchange?.about ?? render` — const, line 4504

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

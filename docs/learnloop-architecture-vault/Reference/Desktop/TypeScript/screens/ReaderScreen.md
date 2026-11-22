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
| Source lines | 4780 |
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
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 357
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 361
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 370
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 371
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 372
- `const openingRef = useRef<string | null>(null)` — const, line 378
- `const savingHighlightNote = useRef(false)` — const, line 390
- `const askPanelOn = algoConfig().ask !== null` — const, line 404
- `const storedStyle = useStoredHelpStyle()` — const, line 405
- `const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen` — const, line 406
- `const pdfViewRequestRef = useRef(0)` — const, line 428
- `const sourceEpochRef = useRef(0)` — const, line 459
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 470
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 471
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 472
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 473
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 474
- `const modeSaveVersionRef = useRef(0)` — const, line 475
- `const answerModeSaveVersionRef = useRef(0)` — const, line 476
- `const enabled = contract?.readerEnabled ?? true` — const, line 492
- `const inquiry = contract?.inquiryEnabled === true` — const, line 495
- `const muted = inquiry && mode === "skim"` — const, line 498
- `const intentContract = inquiry && !offline ? contract?.intent ?? null : null` — const, line 501
- `const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading)` — const, line 502
- `const openFigureSource = useRef<((extractionId: string, spanId: string)` — const, line 506
- `const figureOpenSource = useCallback((extractionId: string, spanId: string)` — const, line 507
- `const figuresCtl = useFigures(` — const, line 508
- `const figureOffersOn = Boolean(contract?.figures?.offers) && !offline` — const, line 514
- `const showMeOn = Boolean(contract?.figures?.showMe) && !offline` — const, line 518
- `const waitingOfferRef = useRef<OfferedPress | null>(null)` — const, line 524
- `const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome)` — const, line 529
- `const press = offeredFigure` — const, line 536
- `const open = render?.extractionId ?? null` — const, line 538
- `const readerTutor = contract?.readerTutor ?? null` — const, line 561
- `const askWorkbenchSessionRef = useRef<string | null>(null)` — const, line 563
- `const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true` — const, line 568
- `const askPersonalizedRef = useRef<boolean | null>(null)` — const, line 569
- `const askComposerAnchorRef = useRef<AskAnchor | null>(null)` — const, line 574
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 580
- `const renderBlocksBySpan = useMemo( ()` — const, line 584
- `const visit = useReaderVisit(` — const, line 590
- `const showGuideRail = useCallback(()` — const, line 596
- `const progress = useReadingProgress(` — const, line 600
- `const doseVisitId = useCallback(()` — const, line 617
- `const refreshAnnotations = useCallback(async ()` — const, line 619
- `const epoch = sourceEpochRef.current` — const, line 621
- `const result = await cachedSourceRead( render.sourceId, ["reader_source_annotations", render.sourceId, render.extractionId], ()` — const, line 625
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 632
- `const version = (r.version as Record<string, unknown>) ??` — const, line 635
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 636
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 637
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 638
- `const placement = r.placement as ReaderAnnotationPlacementDto | undefined` — const, line 639
- `let page: number | null = null` — let, line 649
- `let bbox: number[] | null = null` — let, line 650
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 652
- `const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?:` — const, line 670
- `const openCardRef = useRef<SourceLibraryCard | null>(null)` — const, line 695
- `const openExtractionRef = useRef<string | null>(null)` — const, line 697
- `const reloadGuidePlan = useCallback(async ()` — const, line 699
- `const extractionId = render.extractionId` — const, line 701
- `const plan = await readGuidePlan(render.sourceId, extractionId,` — const, line 703
- `const spanOrder = useMemo( ()` — const, line 716
- `const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none"` — const, line 720
- `const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 723
- `const card = openCardRef.current` — const, line 724
- `const wbProps = useMemo<ReaderWorkbenchProps | undefined>(()` — const, line 734
- `const submitted = workbench?.onSubmitted` — const, line 735
- `const trail = besideTrail(returnStackRef.current)` — const, line 740
- `const wbCtl = useReaderWorkbench(` — const, line 745
- `const working = wbCtl.active !== null` — const, line 752
- `const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline` — const, line 756
- `const alsoHidden = alsoPrefs ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId)) : Boolean(contract?.correspondence?.hiddenEverywhere) || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.so…` — const, line 761
- `const peekCrumbShown = alsoPeek ?? findPeek` — const, line 771
- `const pathRefreshKey = readingPathRefreshKey(` — const, line 786
- `const tryFirstRef = useRef<((spanId: string)` — const, line 800
- `const cueCtl = useReaderCues(` — const, line 801
- `const recapCtl = useReaderRecap(` — const, line 816
- `const recapShown = Boolean(recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working)` — const, line 830
- `const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip")` — const, line 841
- `const root = history.find((entry)` — const, line 842
- `const recapRevisited = useCallback((rootId: string)` — const, line 855
- `const root = history.find((entry)` — const, line 856
- `const recapRevisit = useCallback(async (rootId: string)` — const, line 859
- `const root = history.find((entry)` — const, line 860
- `const recapOpenInquiry = useCallback((rootId: string, spanId: string)` — const, line 866
- `const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch")` — const, line 869
- `const cueMarksFor = (markSurface: "pdf" | "watch")` — const, line 889
- `let cancelled = false` — let, line 898
- `const scroller = railRef.current` — const, line 931
- `const clamp = ()` — const, line 933
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 934
- `const observer = new ResizeObserver(clamp)` — const, line 937
- `const query = librarySearch.trim()` — const, line 948
- `let cancelled = false` — let, line 955
- `const timer = window.setTimeout(()` — const, line 958
- `const resetSourceState = useCallback(()` — const, line 981
- `const openSource = useCallback( async ( card: SourceLibraryCard, jumpSpan?: string, // jumpReading: the reading jumpSpan was found on (a search hit, a // return)` — const, line 1030
- `const handoff = options.handoff ?? null` — const, line 1040
- `const view = options.view ?? await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 1058
- `const pdfRequest = ++pdfViewRequestRef.current` — const, line 1105
- `const current = ()` — const, line 1106
- `const openFixture = useCallback(()` — const, line 1141
- `const backToLibrary = useCallback(()` — const, line 1149
- `const spanId = readingSpan ?? activeSpan` — const, line 1153
- `const section = guidePlan?.sections.find((candidate)` — const, line 1154
- `const resumedRef = useRef(false)` — const, line 1172
- `const trail = initialSource.besideTrail ?? null` — const, line 1176
- `const activeBlock = useMemo(()` — const, line 1190
- `const pdfHighlights: PdfHighlight[] = useMemo(()` — const, line 1199
- `const list: PdfHighlight[] = []` — const, line 1200
- `const base =` — const, line 1203
- `const placed = highlightFromPlacement(base, a.placement)` — const, line 1205
- `const segments = a.segments.flatMap((s)` — const, line 1210
- `const annotatedSpans = useMemo( ()` — const, line 1217
- `const boundaryBlock = useMemo(()` — const, line 1221
- `const revealedPassages = useMemo(()` — const, line 1223
- `const revealed = new Set(revealedSections)` — const, line 1224
- `const map = new Map<string,` — const, line 1225
- `const revealedGuidanceSpans = useMemo(()` — const, line 1234
- `const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null` — const, line 1239
- `const protectedSelection = selectionProtected(protection, selection)` — const, line 1240
- `const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1241
- `const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan))` — const, line 1245
- `const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1246
- `const editCaptureText = useCallback((text: string)` — const, line 1251
- `const resetCaptureText = useCallback(()` — const, line 1254
- `const saveAnnotationEdit = useCallback(async ()` — const, line 1266
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 1288
- `const result = await api.readerReanchor(` — const, line 1292
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1309
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1332
- `const target = annotations.find((a)` — const, line 1333
- `const reading = render ?` — const, line 1334
- `const epoch = sourceEpochRef.current` — const, line 1335
- `const undoRemove = useCallback(async ()` — const, line 1350
- `const last = removed` — const, line 1351
- `const epoch = sourceEpochRef.current` — const, line 1357
- `const result = await api.readerRestoreAnnotation(` — const, line 1359
- `const timer = window.setTimeout(()` — const, line 1372
- `const onKey = (event: KeyboardEvent)` — const, line 1378
- `const target = event.target` — const, line 1381
- `const openAnnotationNote = useCallback((annotationId: string)` — const, line 1390
- `const target = annotations.find((a)` — const, line 1391
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1403
- `const sel = window.getSelection()` — const, line 1404
- `const container = bodyRef.current` — const, line 1405
- `const range = sel.getRangeAt(0)` — const, line 1407
- `const nodes: Array<` — const, line 1408
- `const seen = new Set<string>()` — const, line 1409
- `const spanId = el.dataset.spanId` — const, line 1411
- `let intersects = false` — let, line 1413
- `const sub = document.createRange()` — const, line 1420
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1428
- `const block = renderBlocksBySpan.get(spanId)` — const, line 1433
- `const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1443
- `const cancelIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1444
- `const selectionSpanIds = useMemo( ()` — const, line 1445
- `const intentBox = useIntentBox(` — const, line 1449
- `const openActiveRail = useCallback(()` — const, line 1463
- `const activeCtl = useActiveReading(` — const, line 1467
- `const libraryCtl = useLibraryAsk(` — const, line 1476
- `const keptCtl = useKeptComparisons(` — const, line 1478
- `const notesCtl = useNoteMarks(` — const, line 1480
- `const pdfMarks = (): ReadonlyMap<string, ReactNode> | null` — const, line 1485
- `const cues = cueMarksFor("pdf")` — const, line 1486
- `const merged = new Map<string, ReactNode>(cues ?? [])` — const, line 1488
- `const cue = merged.get(spanId)` — const, line 1490
- `const before = merged.get(spanId)` — const, line 1495
- `const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null)` — const, line 1501
- `const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint)` — const, line 1503
- `const sbs = useSideBySide(` — const, line 1505
- `const node = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1513
- `const sbsPanes = sbs.panes && !comparing` — const, line 1526
- `const sbsPanesRef = useRef(false)` — const, line 1527
- `const sbsShownRef = useRef(false)` — const, line 1532
- `const sbsRef = useRef(sbs)` — const, line 1534
- `const sbsEscBusyRef = useRef(false)` — const, line 1537
- `const sbsPaneRef = useRef<HTMLDivElement | null>(null)` — const, line 1539
- `const runSideIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1544
- `const cancelSideIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1545
- `const sbsSection = sbs.section && sbs.target && sbs.section.sectionId === sbs.target.sectionId ? sbs.section : null` — const, line 1546
- `type BesideRun = |` — type, line 1561
- `const besideSeq = useRef(0)` — const, line 1570
- `const besideRunRef = useRef<(run: BesideRun)` — const, line 1573
- `const besideDroppedRef = useRef<(run: BesideRun)` — const, line 1574
- `const openBesideRef = useRef<(hit:` — const, line 1575
- `const snapshotBesideRef = useRef<(spanId: string)` — const, line 1582
- `const shown = sbsRef.current.target` — const, line 1584
- `const takeBesideBook = useCallback((book: SourceIdentity, spanId: string, run: BesideRun)` — const, line 1588
- `const id = ++besideSeq.current` — const, line 1590
- `const sideExtractionRef = useRef<string | null>(null)` — const, line 1602
- `const checkMeFromSideCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 1603
- `const side = useSidePane(` — const, line 1608
- `const besideRanRef = useRef(0)` — const, line 1637
- `const handoff = besideHandoff` — const, line 1639
- `const card = openCardRef.current` — const, line 1654
- `const trail = besideTrail(returnStackRef.current)` — const, line 1656
- `const work = handoff.run` — const, line 1665
- `const openComposer = useCallback((anchor: AskAnchor | null)` — const, line 1679
- `const sbsRowRef = useRef<HTMLDivElement | null>(null)` — const, line 1697
- `const startSbsResize = (event: ReactPointerEvent<HTMLDivElement>)` — const, line 1698
- `const row = sbsRowRef.current` — const, line 1699
- `const rect = row.getBoundingClientRect()` — const, line 1702
- `const move = (moved: PointerEvent)` — const, line 1703
- `const up = ()` — const, line 1706
- `const touchMain = ()` — const, line 1718
- `const onKey = (event: KeyboardEvent)` — const, line 1727
- `const target = event.target` — const, line 1729
- `const ctl = sbsRef.current` — const, line 1731
- `const open = ctl.panes || ctl.sheet` — const, line 1732
- `const shown = sbsShownRef.current` — const, line 1733
- `const mod = event.ctrlKey || event.metaKey` — const, line 1734
- `const side = sbsPaneRef.current` — const, line 1744
- `const inSide = target instanceof Element && Boolean(target.closest("[data-side-by-side-pane]"))` — const, line 1745
- `const inMain = target instanceof Node && Boolean(bodyRef.current?.contains(target))` — const, line 1751
- `const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false, anchor?: SourceIdentity)` — const, line 1761
- `const identity = anchor ?? identityOf(render)` — const, line 1768
- `const request =` — const, line 1769
- `const closeLibrary = useCallback(()` — const, line 1774
- `const onKey = (event: KeyboardEvent)` — const, line 1781
- `const onMouseUp = useCallback(()` — const, line 1792
- `const sel = window.getSelection()` — const, line 1793
- `const quote = selectionQuote(sel.getRangeAt(0), sel.toString()).replace(/\s+/g, " ").trim()` — const, line 1797
- `const nodes = collectSelectionNodes()` — const, line 1799
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1828
- `const domDragRef = useRef<` — const, line 1829
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1831
- `const host = bodyRef.current` — const, line 1832
- `const rect = host.getBoundingClientRect()` — const, line 1834
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1838
- `const target = event.target as Node` — const, line 1842
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1844
- `const domDrafting = domDraft !== null` — const, line 1856
- `const rectFrom = (drag:` — const, line 1859
- `const onMove = (event: MouseEvent)` — const, line 1865
- `const drag = domDragRef.current` — const, line 1866
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1868
- `const onUp = (event: MouseEvent)` — const, line 1871
- `const drag = domDragRef.current` — const, line 1872
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1876
- `const rect = rectFrom(drag, point)` — const, line 1878
- `const next = [...domBoxesRef.current, rect]` — const, line 1881
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1898
- `const host = bodyRef.current` — const, line 1899
- `const hostRect = host.getBoundingClientRect()` — const, line 1901
- `const clientBoxes = boxes.map((b)` — const, line 1902
- `const nodes: Array<` — const, line 1908
- `const seen = new Set<string>()` — const, line 1909
- `const spanId = el.dataset.spanId` — const, line 1911
- `const elRect = el.getBoundingClientRect()` — const, line 1913
- `const touches = clientBoxes.some( (b)` — const, line 1914
- `const words: string[] = []` — const, line 1918
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 1919
- `const text = node as Text` — const, line 1921
- `const wordPattern = /\S+/g` — const, line 1922
- `let match: RegExpExecArray | null` — let, line 1923
- `const range = document.createRange()` — const, line 1925
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 1928
- `const cx = (Math.min(...rects.map((r)` — const, line 1930
- `const cy = (Math.min(...rects.map((r)` — const, line 1931
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 1935
- `const commitDomBoxes = useCallback(()` — const, line 1944
- `const boxes = domBoxesRef.current` — const, line 1945
- `const nodes = resolveDomBoxes(boxes)` — const, line 1947
- `const quote = nodes.map((n)` — const, line 1953
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 1962
- `const clearDomBoxes = ()` — const, line 1970
- `const onKeyDown = (event: KeyboardEvent)` — const, line 1976
- `const onKeyUp = (event: KeyboardEvent)` — const, line 1981
- `const onBlur = ()` — const, line 1987
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 2009
- `const point = domPointFromClient(request.x, request.y)` — const, line 2011
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 2012
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 2033
- `const retryRequest = useCallback(async (requestId: string)` — const, line 2046
- `const optimisticSegments = useCallback( (nodes: string | Array<string |` — const, line 2060
- `const list = Array.isArray(nodes) ? nodes : [nodes]` — const, line 2062
- `const spanId = typeof node === "string" ? node : node.spanId` — const, line 2064
- `const geometry = pdfView?.blocks.find((b)` — const, line 2065
- `const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number" ?` — const, line 2066
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 2078
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 2082
- `const quotedNodes = (()` — const, line 2087
- `const multi = collectSelectionNodes()` — const, line 2090
- `const optimisticIds = quotedNodes ?? [target.spanId]` — const, line 2093
- `const nodes = quotedNodes ?? [` — const, line 2103
- `const receipt = await api.readerCapture(` — const, line 2104
- `const handler = (event: KeyboardEvent)` — const, line 2131
- `const clearSelection = useCallback(()` — const, line 2143
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 2155
- `const segment = a.segments.find((s)` — const, line 2157
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 2164
- `const alsoKeyRef = useRef<()` — const, line 2174
- `const onKey = (event: KeyboardEvent)` — const, line 2182
- `const target = event.target` — const, line 2185
- `const tabs: ReaderRailTab[] = ["guide", "ask", "notes"]` — const, line 2187
- `const askRequestSeen = useRef(askRequest)` — const, line 2225
- `const revealAskRef = useRef<()` — const, line 2227
- `const startCompareRef = useRef<(request: CompareRequest)` — const, line 2252
- `const sideAnchor = Boolean(side.extractionId) && side.extractionId === request.extractionId` — const, line 2255
- `const request = compareWaitsForWork` — const, line 2262
- `const sideMarksChanged = side.marksChanged` — const, line 2272
- `const captureIn = useCallback(async (target: PaneCaptureTarget, what:` — const, line 2273
- `const common =` — const, line 2278
- `const receipt: ReaderPresetReceiptDto = "preset" in what ? await api.readerInvokePreset(` — const, line 2283
- `const drained = await api.readerDrainOutbox()` — const, line 2294
- `const invokePreset = useCallback( // RW1b: the intent box passes its own words as the annotation's learner // text, and names the intention and entry in the funnel event. // Reader CA6b: `target` is side by side's second pane (its book, revision, // reading a…` — const, line 2315
- `const note_ = learnerTextOverride ?? note` — const, line 2323
- `const nodes = selectionNodes(selection)` — const, line 2324
- `const editedText = selection.editedText?.trim()` — const, line 2325
- `const receipt = await api.readerInvokePreset(` — const, line 2337
- `const drained = await api.readerDrainOutbox()` — const, line 2361
- `const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>, target?: PaneCaptureTarget): Promise<string | null>` — const, line 2384
- `const note_ = learnerTextOverride ?? note` — const, line 2388
- `const nodes = selectionNodes(selection)` — const, line 2389
- `const receipt = await api.readerCapture(` — const, line 2402
- `const currentHighlight = selection && selectionHighlight && selectionActions.includes("highlight") && selectionHighlight.spanId === selection.spanId && selectionHighlight.quote === selection.quote ? selectionHighlight : null` — const, line 2432
- `const saveHighlightNote = useCallback(async ()` — const, line 2437
- `const target = currentHighlight` — const, line 2438
- `const words = note.trim()` — const, line 2439
- `const learnerText = target.saved.trim() ? `$` — const, line 2441
- `const typed = note` — const, line 2442
- `const kept = ()` — const, line 2443
- `const annotationId = target.annotationId` — const, line 2454
- `const pauseArc = useCallback(async ()` — const, line 2471
- `const next = await api.readerArc(` — const, line 2475
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 2482
- `const next = await api.readerArc(` — const, line 2487
- `const importJobRef = useRef<` — const, line 2499
- `const importExercise = useCallback(async (target?: PaneCaptureTarget): Promise<string | null>` — const, line 2502
- `const nodes = target ? target.nodes : selectionNodes(selection!)` — const, line 2504
- `const editedText = target ? undefined : selection!.editedText?.trim()` — const, line 2505
- `const receipt = await api.readerImportExercise(target ?` — const, line 2508
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 2556
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 2557
- `const timer = setInterval(async ()` — const, line 2561
- `const status = await api.readerExerciseImportStatus(` — const, line 2563
- `const job = importJobRef.current` — const, line 2564
- `const waited = Date.now() - job.startedAt` — const, line 2567
- `const saveOwnQuestion = useCallback(async ()` — const, line 2594
- `const saved = await api.readerAuthorQA(` — const, line 2602
- `const runCoach = useCallback(async ()` — const, line 2623
- `const lint = await api.readerCoachLint(` — const, line 2626
- `const changeMode = useCallback( async (next: string)` — const, line 2637
- `const previous = mode` — const, line 2639
- `const version = ++modeSaveVersionRef.current` — const, line 2642
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 2653
- `const answerModeNext = next as ReaderAnswerMode` — const, line 2655
- `const previous = answerMode` — const, line 2656
- `const version = ++answerModeSaveVersionRef.current` — const, line 2659
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 2675
- `const renderInquiryTop = useCallback((root: ReaderExchange)` — const, line 2690
- `const line = reconnect && reconnect.rootId === root.id && !muted ? ( <ReconnectLine placement="rail" question=` — const, line 2693
- `const check = inquiryChecks[root.id]` — const, line 2703
- `const inlineReconnect = reconnect && reconnect.inline && !muted ? ( <ReconnectLine placement="inline" question=` — const, line 2731
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 2742
- `const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, pinned?: ReaderRenderViewDto): Promise<OpenOutcome>` — const, line 2761
- `const card = (library ?? []).find((candidate)` — const, line 2766
- `const spanId = readingSpan ?? activeSpan` — const, line 2769
- `const onOriginal = pdfView && surface === "pdf" && !offline` — const, line 2795
- `const epoch = sourceEpochRef.current` — const, line 2808
- `const sameBook = Boolean(render && sourceId === render.sourceId)` — const, line 2811
- `const card = (library ?? []).find((candidate)` — const, line 2812
- `const landed = await api.readerSavedPlace(` — const, line 2817
- `const landing = await api.readerRenderView(` — const, line 2831
- `const openFollowedFigure = (figure: CorrespondentFigureDto, hit: CorrespondentSectionDto)` — const, line 2841
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2843
- `const compareFoundSection = (hit: CorrespondentSectionDto)` — const, line 2858
- `const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId` — const, line 2860
- `const hideAlsoInBooks = (scope: "book" | "everywhere")` — const, line 2883
- `const before = alsoPrefs ??` — const, line 2885
- `const base = contract` — const, line 2892
- `const makeExplorable = (target: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, origin: "library" | "tutor", offerRef: string): Promise<ExplorableOutcome>` — const, line 2909
- `let settle: (outcome: ExplorableOutcome)` — let, line 2916
- `const settled = new Promise<ExplorableOutcome>((resolve)` — const, line 2917
- `const press: OfferedPress =` — const, line 2918
- `const peekWorkbenchPassage = (spanId: string, target?: PassageTarget)` — const, line 2937
- `const exerciseSettings = libraryCtl.enabled ? contract?.libraryExercises ?? null : null` — const, line 2948
- `const exerciseCard = (sourceId: string | null)` — const, line 2949
- `const useExercise = (candidate: ExerciseCandidate)` — const, line 2953
- `const card = exerciseCard(candidate.sourceId ?? render?.sourceId ?? null)` — const, line 2954
- `const openExerciseInBook = (candidate: ExerciseCandidate)` — const, line 2963
- `const sourceId = candidate.sourceId ?? render?.sourceId ?? null` — const, line 2964
- `const exerciseProps: LibraryExercisesProps | null = exerciseSettings ?` — const, line 2967
- `const pickLibraryPagePractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 2981
- `const hit = libraryCtl.state?.ask.value?.hits[0]` — const, line 2982
- `const card = hit ? (library ?? []).find((candidate)` — const, line 2983
- `const readySources = library ?? []` — const, line 3026
- `const useShelf = Boolean(shelf) && !sidecarDown` — const, line 3028
- `const card = (library ?? []).find((candidate)` — const, line 3086
- `const card = (library ?? []).find((c)` — const, line 3107
- `const receiptId = searchResults.retrievalReceiptId` — const, line 3113
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 3158
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 3159
- `const wbActive = wbCtl.active` — const, line 3202
- `const wbStacked = working && wbCtl.narrow` — const, line 3203
- `const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible)` — const, line 3206
- `const wbSourceShown = !wbStacked || wbCtl.sheetOpen` — const, line 3207
- `const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry)` — const, line 3208
- `const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>()` — const, line 3209
- `const first = entry.spanIds[0]` — const, line 3211
- `const wbLabel = (stem: string)` — const, line 3214
- `const title = problemTitle(stem)` — const, line 3215
- `const tryPathExercise = (exercise: ReadingPathExerciseDto)` — const, line 3220
- `const workThroughSelection = ()` — const, line 3228
- `const nodes = selectionNodes(selection)` — const, line 3230
- `const editedText = selection.editedText?.trim()` — const, line 3231
- `const foldBlocks = contract?.activeReading?.foldBlocks ?? 3` — const, line 3248
- `const localFold = (spanIds: string[]): string[]` — const, line 3249
- `const positions = spanIds.map((spanId)` — const, line 3250
- `const last = Math.max(...positions)` — const, line 3252
- `const mainPane: IntentPane =` — const, line 3261
- `const sidePane: IntentPane | null = side.extractionId ?` — const, line 3270
- `const sideMeta = (pane: IntentPane): Record<string, string>` — const, line 3280
- `const runIntentIn = (pane: IntentPane, action: ReaderIntentActionDto, text: string, how: IntentRunHow): Promise<IntentRunHandle | null> | void` — const, line 3282
- `const meta =` — const, line 3283
- `const effect = action.effect` — const, line 3284
- `const noteText = !action.model && intentContract && onlyNamesAnAction(text, [...intentContract.palette, ...intentContract.notesPalette]) ? "" : text` — const, line 3288
- `const sideSection = pane.side?.section ?? null` — const, line 3290
- `const anchor: AskAnchor =` — const, line 3296
- `const target = pane.side.target` — const, line 3337
- `const target = pane.side.target` — const, line 3343
- `const target = pane.side.target` — const, line 3349
- `const target = pane.side.target` — const, line 3359
- `const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null` — const, line 3404
- `const request: CompareRequest =` — const, line 3405
- `const region = pane.region` — const, line 3437
- `const words = text?.trim()` — const, line 3438
- `const sideShows = (extractionId: string, spanId: string): boolean` — const, line 3459
- `const checkBeside = (book: SourceIdentity, spanId: string, practiceItemId: string, proposalId: string | null)` — const, line 3462
- `const workThroughImported = (item:` — const, line 3467
- `const imported = exerciseImport` — const, line 3468
- `const spanIds = imported?.spanIds ?? (activeSpan ? [activeSpan] : [])` — const, line 3469
- `const settleShowMeLine = (key: string, patch: Partial<ShowMeLine>)` — const, line 3477
- `const requestShowMe = (ctl: FiguresCtl, run: Extract<BesideRun,` — const, line 3480
- `const key = run.lineKey` — const, line 3481
- `const runOnBook = (about: AskAbout, run: Extract<BesideRun,` — const, line 3493
- `const showMeFromAsk = ()` — const, line 3518
- `const goal = question.trim()` — const, line 3519
- `const about = parentExchange ? parentExchange.about ?? null : askComposerAnchor?.about ?? null` — const, line 3520
- `const home = parentExchange?.spanId ?? (about ? askComposerAnchor?.spanId : undefined) ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan` — const, line 3521
- `const key = `show_me:$` — const, line 3524
- `const run =` — const, line 3527
- `const cancelIntentIn = (pane: IntentPane, cancel: IntentCancel)` — const, line 3536
- `const kind = cancel.action.effect.kind` — const, line 3537
- `const annotationId = handle.annotationId` — const, line 3544
- `const batchId = handle.importBatchId` — const, line 3561
- `const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number)` — const, line 3575
- `const spanId = wbCtl.close(session,` — const, line 3577
- `const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3583
- `const card = openCardRef.current` — const, line 3584
- `const asked = libraryCtl.state?.request` — const, line 3588
- `const resumeMark = (spanId: string | null | undefined)` — const, line 3596
- `const entry = spanId ? wbResumeBySpan.get(spanId) : undefined` — const, line 3597
- `const verb = entry.status === "abandoned" ? "Reopen" : "Resume"` — const, line 3599
- `const target = event.target` — const, line 3726
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 3901
- `const active = activeSpan === block.spanId` — const, line 3902
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 3903
- `const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null` — const, line 3904
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 3905
- `const endQuestionAvailable = Boolean(endSection && endSection.question?.readingPhase === "after_section" && offeredCheckSections.has(endSection.id))` — const, line 3907
- `const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId))` — const, line 3911
- `const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""))` — const, line 3912
- `const offerSection = endSection && !muted && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 3913
- `const sel = window.getSelection()` — const, line 3932
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 3933
- `const cue = side.cues.markOn(spanId)` — const, line 4023
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 4051
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 4074
- `const active = railTab === tab` — const, line 4187
- `const waiting = tab === "guide" && pendingQuickCheckCount > 0` — const, line 4191
- `const marked = tab === "ask" && askTabMarked && !active` — const, line 4192
- `const params = (action.params ??` — const, line 4343
- `const run =` — const, line 4617
- `const book = exchange?.about ?? render` — const, line 4626

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

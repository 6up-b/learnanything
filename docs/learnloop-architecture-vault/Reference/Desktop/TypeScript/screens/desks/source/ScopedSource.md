---
title: "Desktop module · src/screens/desks/source/ScopedSource.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.source.ScopedSource"
language: "TypeScript"
area: "TypeScript/screens/desks/source"
source_path: "apps/learnloop-tauri/src/screens/desks/source/ScopedSource.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/source/ScopedSource.tsx"
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

# `src/screens/desks/source/ScopedSource.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/source/_area|TypeScript/screens/desks/source]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `ScopedSource` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/source/ScopedSource.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/source/ScopedSource.tsx) |
| Source lines | 4792 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/source/_area|TypeScript/screens/desks/source]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/source/ScopedSource|src/screens/desks/source/ScopedSource.tsx]]

## Public API

- `export const READER_MODE_OPTIONS = [` — const, line 103
- `export const SIDE_PATH_COPY =` — const, line 189
- `export function ScopedSource(` — function, line 210

## Internal implementation anchors

- `const NO_SECTIONS: never[] = []` — const, line 102
- `const TAG_ACTIONS: Array<` — const, line 112
- `const WHOLE_BLOCK_QUOTE = "(whole block)"` — const, line 119
- `type ReaderRailTab = "guide" | "ask" | "notes"` — type, line 120
- `const HEALTH_COLOR: Record<string, "green" | "amber" | "pink" | "slate"> =` — const, line 121
- `const FIGURE_PAGE_NOT_OPENED = "That page couldn't be opened."` — const, line 128
- `type OpenOutcome = "opened" | "preparing" | "not_opened"` — type, line 130
- `interface OfferedPress` — interface, line 133
- `const OFFER_OUTCOME: Record<FigureRequestOutcome, ExplorableOutcome> =` — const, line 143
- `const BADGED_HEALTH = new Set(["suspect", "failed"])` — const, line 148
- `interface RemovedAnnotation` — interface, line 151
- `const UNDO_REMOVE_MS = 10_000` — const, line 160
- `interface SelectionHighlight` — interface, line 162
- `function newKey(): string` — function, line 168
- `function identityOf(view: Pick<ReaderRenderViewDto, "sourceId" | "revisionId" | "extractionId">): SourceIdentity` — function, line 176
- `function sectionIdentity(section:` — function, line 180
- `function RailScope(` — function, line 184
- `const lifecycle = useWindowLifecycle()` — const, line 185
- `const mainPaneOwnsCueKey = (event: KeyboardEvent): boolean` — const, line 195
- `interface IntentPane` — interface, line 199
- `const hub = useListenerHub()` — const, line 243
- `const windowPaused = useWindowPaused()` — const, line 245
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 249
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 253
- `const offline = false` — const, line 259
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 264
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 265
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 266
- `const openingRef = useRef<string | null>(null)` — const, line 272
- `const savingHighlightNote = useRef(false)` — const, line 284
- `const hostedRailTab = useRef<"guide" | "notes" | null>(windowed?.railHost?.tab ?? null)` — const, line 291
- `const askPanelOn = algoConfig().ask !== null` — const, line 302
- `const storedStyle = useStoredHelpStyle()` — const, line 303
- `const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen` — const, line 304
- `const pdfViewRequestRef = useRef(0)` — const, line 326
- `const sourceEpochRef = useRef(0)` — const, line 350
- `const railCollapsed = false` — const, line 357
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 358
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 359
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 360
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 361
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 362
- `const modeSaveVersionRef = useRef(0)` — const, line 363
- `const answerModeSaveVersionRef = useRef(0)` — const, line 364
- `const enabled = contract?.readerEnabled ?? true` — const, line 380
- `const inquiry = contract?.inquiryEnabled === true` — const, line 383
- `const muted = inquiry && mode === "skim"` — const, line 386
- `const intentContract = inquiry && !offline ? contract?.intent ?? null : null` — const, line 389
- `const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading)` — const, line 390
- `const openFigureSource = useRef<((extractionId: string, spanId: string)` — const, line 394
- `const figureOpenSource = useCallback((extractionId: string, spanId: string)` — const, line 395
- `const figuresCtl = useFigures(` — const, line 396
- `const figureOffersOn = Boolean(contract?.figures?.offers) && !offline` — const, line 402
- `const showMeOn = Boolean(contract?.figures?.showMe) && !offline` — const, line 406
- `const waitingOfferRef = useRef<OfferedPress | null>(null)` — const, line 412
- `const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome)` — const, line 417
- `const press = offeredFigure` — const, line 424
- `const open = render?.extractionId ?? null` — const, line 426
- `const readerTutor = contract?.readerTutor ?? null` — const, line 449
- `const askWorkbenchSessionRef = useRef<string | null>(null)` — const, line 451
- `const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true` — const, line 456
- `const askPersonalizedRef = useRef<boolean | null>(null)` — const, line 457
- `const askComposerAnchorRef = useRef<AskAnchor | null>(null)` — const, line 462
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 468
- `const renderBlocksBySpan = useMemo( ()` — const, line 472
- `const visit = useReaderVisit(` — const, line 478
- `const showGuideRail = useCallback(()` — const, line 484
- `const progress = useReadingProgress(` — const, line 487
- `const doseVisitId = useCallback(()` — const, line 504
- `const refreshAnnotations = useCallback(async ()` — const, line 506
- `const epoch = sourceEpochRef.current` — const, line 508
- `const result = await cachedSourceRead( render.sourceId, ["reader_source_annotations", render.sourceId, render.extractionId], ()` — const, line 512
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 519
- `const version = (r.version as Record<string, unknown>) ??` — const, line 522
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 523
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 524
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 525
- `const placement = r.placement as ReaderAnnotationPlacementDto | undefined` — const, line 526
- `let page: number | null = null` — let, line 536
- `let bbox: number[] | null = null` — let, line 537
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 539
- `const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?:` — const, line 557
- `const openCardRef = useRef<SourceLibraryCard | null>(null)` — const, line 583
- `const openExtractionRef = useRef<string | null>(null)` — const, line 585
- `const reloadGuidePlan = useCallback(async ()` — const, line 587
- `const extractionId = render.extractionId` — const, line 589
- `const plan = await readGuidePlan(render.sourceId, extractionId,` — const, line 591
- `const spanOrder = useMemo( ()` — const, line 604
- `const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none"` — const, line 608
- `const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 611
- `const card = openCardRef.current` — const, line 612
- `const wbProps = useMemo<ReaderWorkbenchProps | undefined>(()` — const, line 622
- `const submitted = workbench?.onSubmitted` — const, line 623
- `const trail = besideTrail(returnStackRef.current)` — const, line 628
- `const wbCtl = useReaderWorkbench(` — const, line 633
- `const workOnPad = windowed?.onWorkOnPad ?? null` — const, line 642
- `const active = wbCtl.active` — const, line 644
- `const working = wbCtl.active !== null && !workOnPad` — const, line 653
- `const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline` — const, line 657
- `const alsoHidden = alsoPrefs ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId)) : Boolean(contract?.correspondence?.hiddenEverywhere) || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.so…` — const, line 662
- `const peekCrumbShown = alsoPeek ?? findPeek` — const, line 672
- `const pathRefreshKey = readingPathRefreshKey(` — const, line 687
- `const tryFirstRef = useRef<((spanId: string)` — const, line 701
- `const cueCtl = useReaderCues(` — const, line 702
- `const recapCtl = useReaderRecap(` — const, line 717
- `const sourceLifecycleState = useWindowLifecycle().state` — const, line 733
- `const railOnScreen = windowed ? Boolean(windowed.railHost) && !isPaused(windowed.railHost?.lifecycle.state ?? "hidden") : !isPaused(sourceLifecycleState)` — const, line 734
- `const guideOnScreen = railOnScreen && railTab === "guide"` — const, line 738
- `const recapInWindow = Boolean(windowed) && !guideOnScreen` — const, line 739
- `const recapShown = Boolean(railOnScreen && recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working) || Boolean(recapInWindow && recapCtl.recap && !recapCtl.collapsed && !muted && !working && !isPaused(…` — const, line 740
- `const drainHost = windowed?.drainHost ?? null` — const, line 748
- `const wrapUpForDrain = useRef(false)` — const, line 749
- `const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip")` — const, line 765
- `const root = history.find((entry)` — const, line 766
- `const recapRevisited = useCallback((rootId: string)` — const, line 779
- `const root = history.find((entry)` — const, line 780
- `const recapRevisit = useCallback(async (rootId: string)` — const, line 783
- `const root = history.find((entry)` — const, line 784
- `const recapOpenInquiry = useCallback((rootId: string, spanId: string)` — const, line 790
- `const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch")` — const, line 793
- `const cueMarksFor = (markSurface: "pdf" | "watch")` — const, line 813
- `let cancelled = false` — let, line 822
- `const scroller = railRef.current` — const, line 855
- `const clamp = ()` — const, line 857
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 858
- `const observer = new ResizeObserver(clamp)` — const, line 861
- `const resetSourceState = useCallback(()` — const, line 870
- `const openSource = useCallback( async ( card: SourceLibraryCard, jumpSpan?: string, // jumpReading: the reading jumpSpan was found on (a search hit, a // return)` — const, line 919
- `const handoff = options.handoff ?? null` — const, line 929
- `const view = options.view ?? await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 946
- `const pdfRequest = ++pdfViewRequestRef.current` — const, line 991
- `const current = ()` — const, line 992
- `const resumedRef = useRef(false)` — const, line 1029
- `const trail = initialSource.besideTrail ?? null` — const, line 1033
- `const activeBlock = useMemo(()` — const, line 1050
- `const pdfHighlights: PdfHighlight[] = useMemo(()` — const, line 1059
- `const list: PdfHighlight[] = []` — const, line 1060
- `const base =` — const, line 1063
- `const placed = highlightFromPlacement(base, a.placement)` — const, line 1065
- `const segments = a.segments.flatMap((s)` — const, line 1070
- `const annotatedSpans = useMemo( ()` — const, line 1077
- `const annotationBySpan = useMemo(()` — const, line 1082
- `const map = new Map<string, MarginAnnotation>()` — const, line 1083
- `const before = map.get(spanId)` — const, line 1087
- `const boundaryBlock = useMemo(()` — const, line 1093
- `const revealedPassages = useMemo(()` — const, line 1095
- `const revealed = new Set(revealedSections)` — const, line 1096
- `const map = new Map<string,` — const, line 1097
- `const revealedGuidanceSpans = useMemo(()` — const, line 1106
- `const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null` — const, line 1111
- `const protectedSelection = selectionProtected(protection, selection)` — const, line 1112
- `const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1113
- `const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan))` — const, line 1117
- `const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null` — const, line 1118
- `const editCaptureText = useCallback((text: string)` — const, line 1123
- `const resetCaptureText = useCallback(()` — const, line 1126
- `const saveAnnotationEdit = useCallback(async ()` — const, line 1138
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 1160
- `const result = await api.readerReanchor(` — const, line 1164
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1181
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1204
- `const target = annotations.find((a)` — const, line 1205
- `const reading = render ?` — const, line 1206
- `const epoch = sourceEpochRef.current` — const, line 1207
- `const undoRemove = useCallback(async ()` — const, line 1222
- `const last = removed` — const, line 1223
- `const epoch = sourceEpochRef.current` — const, line 1229
- `const result = await api.readerRestoreAnnotation(` — const, line 1231
- `const timer = window.setTimeout(()` — const, line 1244
- `const onKey = (event: KeyboardEvent)` — const, line 1250
- `const target = event.target` — const, line 1253
- `const openAnnotationNote = useCallback((annotationId: string)` — const, line 1261
- `const target = annotations.find((a)` — const, line 1262
- `const windowNotesOnRef = useRef(false)` — const, line 1272
- `const windowOpenNote = windowed?.openNote ?? null` — const, line 1274
- `const windowOpenNoteRequest = windowed?.openNoteRequest ?? 0` — const, line 1275
- `const openedNote = useRef<string | null>(null)` — const, line 1276
- `const asked = windowOpenNote ? `$` — const, line 1278
- `const nodesForRange = useCallback((range: Range): Array<` — const, line 1290
- `const container = bodyRef.current` — const, line 1291
- `const nodes: Array<` — const, line 1293
- `const seen = new Set<string>()` — const, line 1294
- `const spanId = el.dataset.spanId` — const, line 1296
- `let intersects = false` — let, line 1298
- `const sub = document.createRange()` — const, line 1305
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1313
- `const block = renderBlocksBySpan.get(spanId)` — const, line 1318
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1324
- `const sel = window.getSelection()` — const, line 1325
- `const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1333
- `const cancelIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1334
- `const selectionSpanIds = useMemo( ()` — const, line 1335
- `const intentBox = useIntentBox(` — const, line 1339
- `const openActiveRail = useCallback(()` — const, line 1353
- `const activeCtl = useActiveReading(` — const, line 1356
- `const libraryCtl = useLibraryAsk(` — const, line 1365
- `const keptCtl = useKeptComparisons(` — const, line 1367
- `const notesCtl = useNoteMarks(` — const, line 1369
- `const windowActive = useWindowLifecycle().state === "active"` — const, line 1375
- `const pdfMarks = (): ReadonlyMap<string, ReactNode> | null` — const, line 1384
- `const cues = cueMarksFor("pdf")` — const, line 1385
- `const merged = new Map<string, ReactNode>(cues ?? [])` — const, line 1387
- `const cue = merged.get(spanId)` — const, line 1389
- `const before = merged.get(spanId)` — const, line 1394
- `const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null)` — const, line 1400
- `const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint)` — const, line 1402
- `const sbs = useSideBySide(` — const, line 1404
- `const node = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1412
- `const sectionInView = render && currentGuideSection ? `$` — const, line 1424
- `const onSectionRef = useRef(windowed?.onSection)` — const, line 1425
- `const sbsPanes = sbs.panes && !comparing` — const, line 1435
- `const sbsPanesRef = useRef(false)` — const, line 1436
- `const sbsShownRef = useRef(false)` — const, line 1441
- `const sbsRef = useRef(sbs)` — const, line 1443
- `const sbsEscBusyRef = useRef(false)` — const, line 1446
- `const sbsPaneRef = useRef<HTMLDivElement | null>(null)` — const, line 1448
- `const runSideIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow)` — const, line 1453
- `const cancelSideIntentRunRef = useRef<(cancel: IntentCancel)` — const, line 1454
- `const sbsSection = sbs.section && sbs.target && sbs.section.sectionId === sbs.target.sectionId ? sbs.section : null` — const, line 1455
- `type BesideRun = |` — type, line 1470
- `const besideSeq = useRef(0)` — const, line 1479
- `const besideRunRef = useRef<(run: BesideRun)` — const, line 1482
- `const besideDroppedRef = useRef<(run: BesideRun)` — const, line 1483
- `const openBesideRef = useRef<(hit:` — const, line 1484
- `const snapshotBesideRef = useRef<(spanId: string)` — const, line 1491
- `const shown = sbsRef.current.target` — const, line 1493
- `const takeBesideBook = useCallback((book: SourceIdentity, spanId: string, run: BesideRun)` — const, line 1497
- `const id = ++besideSeq.current` — const, line 1499
- `const sideExtractionRef = useRef<string | null>(null)` — const, line 1511
- `const checkMeFromSideCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin)` — const, line 1512
- `const side = useSidePane(` — const, line 1517
- `const besideRanRef = useRef(0)` — const, line 1546
- `const handoff = besideHandoff` — const, line 1548
- `const card = openCardRef.current` — const, line 1563
- `const trail = besideTrail(returnStackRef.current)` — const, line 1565
- `const work = handoff.run` — const, line 1574
- `const openComposer = useCallback((anchor: AskAnchor | null)` — const, line 1588
- `const sbsRowRef = useRef<HTMLDivElement | null>(null)` — const, line 1606
- `const startSbsResize = (event: ReactPointerEvent<HTMLDivElement>)` — const, line 1607
- `const row = sbsRowRef.current` — const, line 1608
- `const rect = row.getBoundingClientRect()` — const, line 1611
- `const move = (moved: PointerEvent)` — const, line 1612
- `const offs: Array<()` — const, line 1615
- `const up = ()` — const, line 1616
- `const touchMain = ()` — const, line 1626
- `const touchedRef = useRef(windowed?.onTouched)` — const, line 1631
- `const pairKeyRef = useRef(windowed?.onPairKey)` — const, line 1633
- `const onKey = (event: KeyboardEvent)` — const, line 1641
- `const target = event.target` — const, line 1643
- `const ctl = sbsRef.current` — const, line 1645
- `const open = ctl.panes || ctl.sheet` — const, line 1646
- `const shown = sbsShownRef.current` — const, line 1647
- `const mod = event.ctrlKey || event.metaKey` — const, line 1648
- `const side = sbsPaneRef.current` — const, line 1665
- `const inSide = target instanceof Element && Boolean(target.closest("[data-side-by-side-pane]"))` — const, line 1666
- `const inMain = target instanceof Node && Boolean(bodyRef.current?.contains(target))` — const, line 1672
- `const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false, anchor?: SourceIdentity)` — const, line 1681
- `const identity = anchor ?? identityOf(render)` — const, line 1688
- `const request =` — const, line 1689
- `const closeLibrary = useCallback(()` — const, line 1694
- `const onKey = (event: KeyboardEvent)` — const, line 1701
- `const onMouseUp = useCallback(()` — const, line 1711
- `const sel = window.getSelection()` — const, line 1712
- `const quote = selectionQuote(sel.getRangeAt(0), sel.toString()).replace(/\s+/g, " ").trim()` — const, line 1716
- `const nodes = collectSelectionNodes()` — const, line 1718
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1747
- `const domDragRef = useRef<` — const, line 1748
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1750
- `const host = bodyRef.current` — const, line 1751
- `const rect = host.getBoundingClientRect()` — const, line 1753
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1757
- `const target = event.target as Node` — const, line 1761
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1763
- `const domDrafting = domDraft !== null` — const, line 1775
- `const rectFrom = (drag:` — const, line 1778
- `const onMove = (event: MouseEvent)` — const, line 1784
- `const drag = domDragRef.current` — const, line 1785
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1787
- `const onUp = (event: MouseEvent)` — const, line 1790
- `const drag = domDragRef.current` — const, line 1791
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1795
- `const rect = rectFrom(drag, point)` — const, line 1797
- `const next = [...domBoxesRef.current, rect]` — const, line 1800
- `const offs = [hub.listen("window", "mousemove", onMove), hub.listen("window", "mouseup", onUp)]` — const, line 1806
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1813
- `const host = bodyRef.current` — const, line 1814
- `const hostRect = host.getBoundingClientRect()` — const, line 1816
- `const clientBoxes = boxes.map((b)` — const, line 1817
- `const nodes: Array<` — const, line 1823
- `const seen = new Set<string>()` — const, line 1824
- `const spanId = el.dataset.spanId` — const, line 1826
- `const elRect = el.getBoundingClientRect()` — const, line 1828
- `const touches = clientBoxes.some( (b)` — const, line 1829
- `const words: string[] = []` — const, line 1833
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 1834
- `const text = node as Text` — const, line 1836
- `const wordPattern = /\S+/g` — const, line 1837
- `let match: RegExpExecArray | null` — let, line 1838
- `const range = document.createRange()` — const, line 1840
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 1843
- `const cx = (Math.min(...rects.map((r)` — const, line 1845
- `const cy = (Math.min(...rects.map((r)` — const, line 1846
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 1850
- `const commitDomBoxes = useCallback(()` — const, line 1859
- `const boxes = domBoxesRef.current` — const, line 1860
- `const nodes = resolveDomBoxes(boxes)` — const, line 1862
- `const quote = nodes.map((n)` — const, line 1868
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 1877
- `const clearDomBoxes = ()` — const, line 1885
- `const onKeyDown = (event: KeyboardEvent)` — const, line 1891
- `const onKeyUp = (event: KeyboardEvent)` — const, line 1896
- `const onBlur = ()` — const, line 1902
- `const offs = [ hub.listen("window", "keydown", onKeyDown), hub.listen("window", "keyup", onKeyUp), hub.listen("window", "blur", onBlur), ]` — const, line 1903
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 1922
- `const point = domPointFromClient(request.x, request.y)` — const, line 1924
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 1925
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 1946
- `const retryRequest = useCallback(async (requestId: string)` — const, line 1959
- `const optimisticSegments = useCallback( (nodes: string | Array<string |` — const, line 1973
- `const list = Array.isArray(nodes) ? nodes : [nodes]` — const, line 1975
- `const spanId = typeof node === "string" ? node : node.spanId` — const, line 1977
- `const geometry = pdfView?.blocks.find((b)` — const, line 1978
- `const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number" ?` — const, line 1979
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 1991
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 1995
- `const quotedNodes = (()` — const, line 2000
- `const multi = collectSelectionNodes()` — const, line 2003
- `const optimisticIds = quotedNodes ?? [target.spanId]` — const, line 2006
- `const nodes = quotedNodes ?? [` — const, line 2016
- `const receipt = await api.readerCapture(` — const, line 2017
- `const handler = (event: KeyboardEvent)` — const, line 2044
- `const clearSelection = useCallback(()` — const, line 2055
- `const railHostTab = windowed?.railHost?.tab ?? null` — const, line 2067
- `const windowExtraction = render?.extractionId ?? null` — const, line 2068
- `const onWindowTitle = windowed?.onTitle` — const, line 2073
- `const onWindowStatus = windowed?.onStatus` — const, line 2077
- `const windowWhere = currentGuideSection ? sectionWords(currentGuideSection.label) : null` — const, line 2078
- `const onWindowMediaReady = windowed?.onMediaReady` — const, line 2082
- `const onWindowJumpReady = windowed?.onJumpReady` — const, line 2088
- `const readingPathsOn = (Boolean(contract?.readingPaths) || Boolean(guidePlan?.sections.length)) && !offline` — const, line 2098
- `const onKey = (event: KeyboardEvent)` — const, line 2102
- `const onWindowInquiryReady = windowed?.onInquiryReady` — const, line 2110
- `const onWindowPenSurface = windowed?.onPenSurface` — const, line 2134
- `const penTextShown = Boolean(render) && !(pdfView && surface === "pdf")` — const, line 2135
- `const body = bodyRef.current` — const, line 2137
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 2153
- `const segment = a.segments.find((s)` — const, line 2155
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 2162
- `const alsoKeyRef = useRef<()` — const, line 2172
- `const onKey = (event: KeyboardEvent)` — const, line 2180
- `const target = event.target` — const, line 2183
- `const tabs: ReaderRailTab[] = ["guide", "ask", "notes"]` — const, line 2185
- `const startCompareRef = useRef<(request: CompareRequest)` — const, line 2211
- `const sideAnchor = Boolean(side.extractionId) && side.extractionId === request.extractionId` — const, line 2214
- `const request = compareWaitsForWork` — const, line 2221
- `const sideMarksChanged = side.marksChanged` — const, line 2231
- `const captureIn = useCallback(async (target: PaneCaptureTarget, what:` — const, line 2232
- `const common =` — const, line 2237
- `const receipt: ReaderPresetReceiptDto = "preset" in what ? await api.readerInvokePreset(` — const, line 2242
- `const drained = await api.readerDrainOutbox()` — const, line 2253
- `const invokePreset = useCallback( // RW1b: the intent box passes its own words as the annotation's learner // text, and names the intention and entry in the funnel event. // Reader CA6b: `target` is side by side's second pane (its book, revision, // reading a…` — const, line 2274
- `const note_ = learnerTextOverride ?? note` — const, line 2282
- `const nodes = selectionNodes(selection)` — const, line 2283
- `const editedText = selection.editedText?.trim()` — const, line 2284
- `const receipt = await api.readerInvokePreset(` — const, line 2296
- `const drained = await api.readerDrainOutbox()` — const, line 2320
- `const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>, target?: PaneCaptureTarget): Promise<string | null>` — const, line 2343
- `const note_ = learnerTextOverride ?? note` — const, line 2347
- `const nodes = selectionNodes(selection)` — const, line 2348
- `const receipt = await api.readerCapture(` — const, line 2361
- `const currentHighlight = selection && selectionHighlight && selectionActions.includes("highlight") && selectionHighlight.spanId === selection.spanId && selectionHighlight.quote === selection.quote ? selectionHighlight : null` — const, line 2391
- `const saveHighlightNote = useCallback(async ()` — const, line 2396
- `const target = currentHighlight` — const, line 2397
- `const words = note.trim()` — const, line 2398
- `const learnerText = target.saved.trim() ? `$` — const, line 2400
- `const typed = note` — const, line 2401
- `const kept = ()` — const, line 2402
- `const annotationId = target.annotationId` — const, line 2413
- `const pauseArc = useCallback(async ()` — const, line 2430
- `const next = await api.readerArc(` — const, line 2434
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 2441
- `const next = await api.readerArc(` — const, line 2446
- `const importJobRef = useRef<` — const, line 2458
- `const importExercise = useCallback(async (target?: PaneCaptureTarget): Promise<string | null>` — const, line 2461
- `const nodes = target ? target.nodes : selectionNodes(selection!)` — const, line 2463
- `const editedText = target ? undefined : selection!.editedText?.trim()` — const, line 2464
- `const receipt = await api.readerImportExercise(target ?` — const, line 2467
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 2515
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 2516
- `const timer = setInterval(async ()` — const, line 2520
- `const status = await api.readerExerciseImportStatus(` — const, line 2522
- `const job = importJobRef.current` — const, line 2523
- `const waited = Date.now() - job.startedAt` — const, line 2526
- `const saveOwnQuestion = useCallback(async ()` — const, line 2553
- `const saved = await api.readerAuthorQA(` — const, line 2561
- `const runCoach = useCallback(async ()` — const, line 2582
- `const lint = await api.readerCoachLint(` — const, line 2585
- `const changeMode = useCallback( async (next: string)` — const, line 2596
- `const previous = mode` — const, line 2598
- `const version = ++modeSaveVersionRef.current` — const, line 2601
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 2612
- `const answerModeNext = next as ReaderAnswerMode` — const, line 2614
- `const previous = answerMode` — const, line 2615
- `const version = ++answerModeSaveVersionRef.current` — const, line 2618
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 2634
- `const renderInquiryTop = useCallback((root: ReaderExchange)` — const, line 2649
- `const line = reconnect && reconnect.rootId === root.id && !muted ? ( <ReconnectLine placement="rail" question=` — const, line 2652
- `const check = inquiryChecks[root.id]` — const, line 2662
- `const inlineCheckSpans = useRef(new Map<string, string>())` — const, line 2692
- `const inlineReconnect = reconnect && reconnect.inline && !muted ? ( <ReconnectLine placement="inline" question=` — const, line 2693
- `const inlineCheckRoot = windowed && !windowed.railHost ? [...inlineCheckSpans.current.keys()].find((rootId)` — const, line 2706
- `const inlineCheck = inlineCheckRoot ? (()` — const, line 2709
- `const check = inquiryChecks[inlineCheckRoot]` — const, line 2710
- `const inlineInquiry = inlineReconnect && reconnect ?` — const, line 2735
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 2737
- `const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, pinned?: ReaderRenderViewDto): Promise<OpenOutcome>` — const, line 2756
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
- `const wbActive = wbCtl.active` — const, line 3004
- `const wbStacked = working && wbCtl.narrow` — const, line 3005
- `const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible)` — const, line 3008
- `const wbSourceShown = !wbStacked || wbCtl.sheetOpen` — const, line 3009
- `const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry)` — const, line 3010
- `const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>()` — const, line 3011
- `const first = entry.spanIds[0]` — const, line 3013
- `const wbLabel = (stem: string)` — const, line 3016
- `const title = problemTitle(stem)` — const, line 3017
- `const tryPathExercise = (exercise: ReadingPathExerciseDto)` — const, line 3022
- `const workThroughSelection = ()` — const, line 3030
- `const nodes = selectionNodes(selection)` — const, line 3032
- `const editedText = selection.editedText?.trim()` — const, line 3033
- `const foldBlocks = contract?.activeReading?.foldBlocks ?? 3` — const, line 3050
- `const localFold = (spanIds: string[]): string[]` — const, line 3051
- `const positions = spanIds.map((spanId)` — const, line 3052
- `const last = Math.max(...positions)` — const, line 3054
- `const mainPane: IntentPane =` — const, line 3063
- `const sidePane: IntentPane | null = side.extractionId ?` — const, line 3072
- `const sideMeta = (pane: IntentPane): Record<string, string>` — const, line 3082
- `const runIntentIn = (pane: IntentPane, action: ReaderIntentActionDto, text: string, how: IntentRunHow): Promise<IntentRunHandle | null> | void` — const, line 3084
- `const meta =` — const, line 3085
- `const effect = action.effect` — const, line 3086
- `const noteText = !action.model && intentContract && onlyNamesAnAction(text, [...intentContract.palette, ...intentContract.notesPalette]) ? "" : text` — const, line 3090
- `const sideSection = pane.side?.section ?? null` — const, line 3092
- `const anchor: AskAnchor =` — const, line 3098
- `const spanId = pane.spanIds[0] ?? activeSpan ?? readingSpan` — const, line 3126
- `const target = pane.side.target` — const, line 3150
- `const target = pane.side.target` — const, line 3156
- `const target = pane.side.target` — const, line 3162
- `const target = pane.side.target` — const, line 3172
- `const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null` — const, line 3217
- `const request: CompareRequest =` — const, line 3218
- `const region = pane.region` — const, line 3254
- `const words = text?.trim()` — const, line 3255
- `const sideShows = (extractionId: string, spanId: string): boolean` — const, line 3276
- `const checkBeside = (book: SourceIdentity, spanId: string, practiceItemId: string, proposalId: string | null)` — const, line 3279
- `const workThroughImported = (item:` — const, line 3284
- `const imported = exerciseImport` — const, line 3285
- `const spanIds = imported?.spanIds ?? (activeSpan ? [activeSpan] : [])` — const, line 3286
- `const settleShowMeLine = (key: string, patch: Partial<ShowMeLine>)` — const, line 3294
- `const requestShowMe = (ctl: FiguresCtl, run: Extract<BesideRun,` — const, line 3297
- `const key = run.lineKey` — const, line 3298
- `const runOnBook = (about: AskAbout, run: Extract<BesideRun,` — const, line 3310
- `const showMeFromAsk = ()` — const, line 3335
- `const goal = question.trim()` — const, line 3336
- `const about = parentExchange ? parentExchange.about ?? null : askComposerAnchor?.about ?? null` — const, line 3337
- `const home = parentExchange?.spanId ?? (about ? askComposerAnchor?.spanId : undefined) ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan` — const, line 3338
- `const key = `show_me:$` — const, line 3341
- `const run =` — const, line 3344
- `const cancelIntentIn = (pane: IntentPane, cancel: IntentCancel)` — const, line 3353
- `const kind = cancel.action.effect.kind` — const, line 3354
- `const annotationId = handle.annotationId` — const, line 3361
- `const batchId = handle.importBatchId` — const, line 3378
- `const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number)` — const, line 3392
- `const spanId = wbCtl.close(session,` — const, line 3394
- `const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 3400
- `const card = openCardRef.current` — const, line 3401
- `const asked = libraryCtl.state?.request` — const, line 3405
- `const resumeMark = (spanId: string | null | undefined)` — const, line 3413
- `const entry = spanId ? wbResumeBySpan.get(spanId) : undefined` — const, line 3414
- `const verb = entry.status === "abandoned" ? "Reopen" : "Resume"` — const, line 3416
- `const placeRail = (rail: ReactNode): ReactNode` — const, line 3435
- `const host = windowed.railHost` — const, line 3437
- `const overDesk = (menu: ReactNode): ReactNode` — const, line 3446
- `const doseOfferNode = render ? ( <DoseOffer extractionId=` — const, line 3449
- `const wrapUpNode = recapCtl.wrapUpOpen ? ( <WrapUpPanel wrapUp=` — const, line 3468
- `const params = (action.params ??` — const, line 3480
- `const recapCardNode = recapCtl.recap ? ( <RecapCard recap=` — const, line 3489
- `const windowNotesOn = Boolean(windowed) && !(railOnScreen && railTab === "notes") && !offline` — const, line 3514
- `const annotationsBySpan = new Map<string, MarginAnnotation[]>()` — const, line 3516
- `const spanId = annotation.annotationId ? placedSpanIds(annotation)[0] : undefined` — const, line 3519
- `const windowNotesList = windowNotesSpan ? annotationsBySpan.get(windowNotesSpan) ?? [] : []` — const, line 3523
- `const windowNotesCard = windowNotesOn && windowNotesSpan && windowNotesList.length ? ( <div role="group" aria-label="your notes on this passage" data-window-notes="" style=` — const, line 3524
- `const windowNoteMark = (spanId: string | null | undefined): ReactNode` — const, line 3550
- `const windowActiveCard = windowed && activeReadingOn && (activeCtl.active || activeCtl.another) && !(railOnScreen && railTab === "notes") ? ( <div data-window-active-reading="" style=` — const, line 3569
- `const windowActiveSpans = activeCtl.another ? activeCtl.another.spanIds : activeCtl.active?.anchorSpanIds ?? []` — const, line 3574
- `const windowActiveSpan = windowActiveCard ? windowActiveSpans[windowActiveSpans.length - 1] ?? null : null` — const, line 3575
- `const windowChecksOn = Boolean(windowed) && !guideOnScreen && boundaryChecksAvailable && !working && !windowPathOpen` — const, line 3581
- `const openCheckIds = new Set(openQuestionSections.map((section)` — const, line 3582
- `const windowCheckAt = new Map<string, ReaderGuideSectionDto>()` — const, line 3583
- `const windowChecks = (spanId: string | null | undefined): ReactNode` — const, line 3590
- `const section = spanId ? windowCheckAt.get(spanId) : undefined` — const, line 3591
- `const windowAuthoringCard = Boolean(windowed) && authoringOpen && authoringSpanId && !(railOnScreen && railTab === "notes") && !offline ? ( <div role="group" aria-label="your own question" data-window-authoring="" style=` — const, line 3611
- `const windowPathShown = Boolean(windowed && windowPathOpen && readingPathsOn && render && !working && !guideOnScreen)` — const, line 3633
- `const windowTopShown = windowPathShown || Boolean(recapInWindow && !working && ((recapCtl.wrapUpOpen && !drainHost) || (recapCtl.recap && !muted)))` — const, line 3634
- `const windowInlineNotes = [ ...(windowActiveCard && windowActiveSpan ? [` — const, line 3635
- `const guideHeader = (!windowed || guideOnScreen) && ((recapCtl.wrapUpOpen && !drainHost) || (recapCtl.recap && !muted)) ? ( <>` — const, line 3646
- `const guideFooter = cueCtl.cues ? ( <CueFooter density=` — const, line 3652
- `const guideRail = (visible: boolean, inWindow: boolean): ReactNode` — const, line 3662
- `const target = event.target` — const, line 3863
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 4068
- `const active = activeSpan === block.spanId` — const, line 4069
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 4070
- `const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null` — const, line 4071
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 4072
- `const endQuestionAvailable = Boolean(endSection && endSection.question?.readingPhase === "after_section" && offeredCheckSections.has(endSection.id))` — const, line 4074
- `const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId))` — const, line 4078
- `const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""))` — const, line 4079
- `const offerSection = endSection && !muted && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 4080
- `const sel = window.getSelection()` — const, line 4105
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 4106
- `const cue = side.cues.markOn(spanId)` — const, line 4232
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 4260
- `const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="$` — const, line 4283
- `const active = railTab === tab` — const, line 4386
- `const waiting = tab === "guide" && pendingQuickCheckCount > 0` — const, line 4390
- `const marked = tab === "ask" && askTabMarked && !active` — const, line 4391
- `const run =` — const, line 4642
- `const book = exchange?.about ?? render` — const, line 4651

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] — import-or-re-export: `ScopedSource`; references `ScopedSource`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CorrespondentFigureDto`, `CorrespondentSectionDto`, `FigurePassageDto`, `FigureViewDto`, `LibraryAskEntry`, `LibraryHitDto`, `PassageTarget`, `ProposedItemDto`, `ReaderAnnotationPlacementDto`, `ReaderAnswerMode`, `ReaderArcDto`, `ReaderCoachLintDto`, `ReaderCueDto`, `ReaderDisposition`, `ReaderGuidePlanDto`, `ReaderGuideSectionDto`, `ReaderImportExerciseInput`, `ReaderIntentActionDto`, `ReaderPdfViewDto`, `ReaderPresetReceiptDto`, `ReaderPromptContractDto`, `ReaderRenderBlockDto`, `ReaderRenderViewDto`, `ReaderWatchPlanDto`, `ReadingPathExerciseDto`, `SourceIdentity`, `SourceLibraryCard`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export; imports `setQueryData`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export; imports `PdfReaderPane`, `PdfReaderPaneHandle`, `TagMenuRequest`
- [[Reference/Desktop/TypeScript/components/RectUnionOverlay|src/components/RectUnionOverlay.tsx]] — import-or-re-export; imports `RectUnionOverlay`
- [[Reference/Desktop/TypeScript/components/askPanel|src/components/askPanel.tsx]] — import-or-re-export; imports `STYLE_ANSWER_MODE`, `StoredHelpStyle`, `useStoredHelpStyle`
- [[Reference/Desktop/TypeScript/components/pdfSelection/highlights|src/components/pdfSelection/highlights.ts]] — import-or-re-export; imports `PdfHighlight`, `highlightFromPlacement`, `kindLabel`
- [[Reference/Desktop/TypeScript/components/pdfSelection/model|src/components/pdfSelection/model.ts]] — import-or-re-export; imports `exactNode`
- [[Reference/Desktop/TypeScript/components/scrollWithin|src/components/scrollWithin.ts]] — import-or-re-export; imports `scrollIntoViewWithin`
- [[Reference/Desktop/TypeScript/components/sourceTail|src/components/sourceTail.ts]] — import-or-re-export; imports `youtubeVideoId`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `FONT_MONO`, `Faint`, `Pill`, `TermSelect`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `SPAN_MISMATCH_COPY`, `errorMessage`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/render/mathMacros|src/render/mathMacros.tsx]] — import-or-re-export; imports `MathMacrosProvider`
- [[Reference/Desktop/TypeScript/render/mathSnippet|src/render/mathSnippet.ts]] — import-or-re-export; imports `selectionQuote`
- [[Reference/Desktop/TypeScript/render/readerBlockPolicy|src/render/readerBlockPolicy.ts]] — import-or-re-export; imports `readerDisplaysBlock`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `WindowScope`, `isPaused`, `useListenerHub`, `useScopeClaim`, `useWindowLifecycle`, `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/desks/source/types|src/screens/desks/source/types.ts]] — import-or-re-export; imports `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`, `ReaderWindowing`
- [[Reference/Desktop/TypeScript/screens/reader/ActiveReadingCard|src/screens/reader/ActiveReadingCard.tsx]] — import-or-re-export; imports `ActiveReadingCard`, `NextStepFoldLine`
- [[Reference/Desktop/TypeScript/screens/reader/AlsoInBooks|src/screens/reader/AlsoInBooks.tsx]] — import-or-re-export; imports `ALSO_COPY`, `AlsoInBooks`, `AlsoPeekCrumb`
- [[Reference/Desktop/TypeScript/screens/reader/AskRail|src/screens/reader/AskRail.tsx]] — import-or-re-export; imports `AskRail`
- [[Reference/Desktop/TypeScript/screens/reader/DeliverableSliceCard|src/screens/reader/DeliverableSliceCard.tsx]] — import-or-re-export; imports `GuidePathSlot`
- [[Reference/Desktop/TypeScript/screens/reader/DetourStrip|src/screens/reader/DetourStrip.tsx]] — import-or-re-export; imports `DetourStrip`
- [[Reference/Desktop/TypeScript/screens/reader/DoseOffer|src/screens/reader/DoseOffer.tsx]] — import-or-re-export; imports `DoseOffer`
- [[Reference/Desktop/TypeScript/screens/reader/FindSection|src/screens/reader/FindSection.tsx]] — import-or-re-export; imports `FindSection`
- [[Reference/Desktop/TypeScript/screens/reader/GuideRail|src/screens/reader/GuideRail.tsx]] — import-or-re-export; imports `GuideRail`, `QuickChecks`, `SectionBoundaryOffer`
- [[Reference/Desktop/TypeScript/screens/reader/InquiryQuickCheck|src/screens/reader/InquiryQuickCheck.tsx]] — import-or-re-export; imports `InquiryQuickCheck`
- [[Reference/Desktop/TypeScript/screens/reader/IntentBox|src/screens/reader/IntentBox.tsx]] — import-or-re-export; imports `IntentBox`
- [[Reference/Desktop/TypeScript/screens/reader/KeptMark|src/screens/reader/KeptMark.tsx]] — import-or-re-export; imports `KeptMark`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]] — import-or-re-export; imports `ExplorableOutcome`, `LibraryExercisesProps`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryPane|src/screens/reader/LibraryPane.tsx]] — import-or-re-export; imports `LibraryPane`, `useComparingStacked`
- [[Reference/Desktop/TypeScript/screens/reader/MarginMark|src/screens/reader/MarginMark.tsx]] — import-or-re-export; imports `CueFooter`, `CueReceipts`, `MarginMark`
- [[Reference/Desktop/TypeScript/screens/reader/NotesRail|src/screens/reader/NotesRail.tsx]] — import-or-re-export; imports `AnnotationCard`, `AuthoringCard`, `ExerciseImportState`, `NotesRail`
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
- [[Reference/Desktop/TypeScript/screens/reader/exerciseCandidates (ts)|src/screens/reader/exerciseCandidates.ts]] — import-or-re-export; imports `ExerciseCandidate`, `exerciseOpenRequest`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export; imports `FiguresUnder`
- [[Reference/Desktop/TypeScript/screens/reader/figures/showMe|src/screens/reader/figures/showMe.ts]] — import-or-re-export; imports `ShowMeLine`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export; imports `FigureRequestOutcome`, `FiguresCtl`, `useFigures`
- [[Reference/Desktop/TypeScript/screens/reader/guidePlan|src/screens/reader/guidePlan.ts]] — import-or-re-export; imports `readGuidePlan`
- [[Reference/Desktop/TypeScript/screens/reader/intentPalette|src/screens/reader/intentPalette.ts]] — import-or-re-export; imports `onlyNamesAnAction`
- [[Reference/Desktop/TypeScript/screens/reader/notesContext|src/screens/reader/notesContext.ts]] — import-or-re-export; imports `NotesContext`
- [[Reference/Desktop/TypeScript/screens/reader/readerCache|src/screens/reader/readerCache.ts]] — import-or-re-export; imports `cachedSourceRead`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `AnnotationSegment`, `MarginAnnotation`, `ReaderSelection`, `askGroundingSpans`, `clip`, `groundingProtected`, `passageKeys`, `placedSpanIds`, `sectionWords`, `selectionNodes`, `selectionProtected`
- [[Reference/Desktop/TypeScript/screens/reader/readingPath|src/screens/reader/readingPath.ts]] — import-or-re-export; imports `readingPathRefreshKey`
- [[Reference/Desktop/TypeScript/screens/reader/readingPosition|src/screens/reader/readingPosition.ts]] — import-or-re-export; imports `ReadingPosition`
- [[Reference/Desktop/TypeScript/screens/reader/recapCopy|src/screens/reader/recapCopy.ts]] — import-or-re-export; imports `RECAP_COPY`
- [[Reference/Desktop/TypeScript/screens/reader/returnStack|src/screens/reader/returnStack.ts]] — import-or-re-export; imports `besideTrail`, `stackGoTo`
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

- Imported packages/crates: `@tauri-apps/api/core`, `react`, `react-dom`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Import Canonical Sources|Import Canonical Sources]] — owns import sequencing.
- [[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]] — owns pipeline persistence semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/workbench/switchOff.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/workbench/switchOff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/tutorSwitchOff.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/tutorSwitchOff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/tutorReader.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/tutorReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/tutorExercises.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/tutorExercises.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/tutorBoundAsk.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/tutorBoundAsk.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/sideBySideReader.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/sideBySideIntent.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideIntent.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/sideBySideCorrespondence.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideCorrespondence.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_ingest_m3.py](../../../../../../../../tests/test_sidecar_ingest_m3.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_source_ingestion.py](../../../../../../../../tests/test_source_ingestion.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_ingest_runner.py](../../../../../../../../tests/test_ingest_runner.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_init.py](../../../../../../../../tests/test_init.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/source/ScopedSource.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/source/ScopedSource.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

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
source_commit: "79969fe3eace6b6fb77d673b17b32ab85b49ad7f"
source_commit_timestamp: "2026-09-03T10:56:04-07:00"
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
| Source lines | 3974 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `79969fe3eace6b6fb77d673b17b32ab85b49ad7f` |
| Commit timestamp | `2026-09-03T10:56:04-07:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]]

## Public API

- `export interface SelectionNode` — interface, line 126
- `export interface AnnotationTrail` — interface, line 187
- `export interface ReaderOpenSource` — interface, line 220
- `export function ReaderScreen(` — function, line 225
- `export interface WatchPanelHandle` — interface, line 3614

## Internal implementation anchors

- `const ANSWER_MODE_OPTIONS = [` — const, line 53
- `const READER_MODE_OPTIONS = [` — const, line 59
- `const PALETTE: Array<` — const, line 70
- `const QUESTION_CONTROLS: Array<` — const, line 97
- `const TAG_ACTIONS: Array<` — const, line 109
- `const WHOLE_BLOCK_QUOTE = "(whole block)"` — const, line 117
- `function clip(text: string, max: number): string` — function, line 119
- `function selectionNodes(sel:` — function, line 136
- `interface ReaderExchange` — interface, line 144
- `type ReaderRailTab = "guide" | "ask" | "notes"` — type, line 153
- `const HEALTH_COLOR: Record<string, "green" | "amber" | "pink" | "slate"> =` — const, line 155
- `const FURNITURE_BLOCK_TYPES = new Set(["PageHeader", "PageFooter", "TableOfContents"])` — const, line 164
- `const BADGED_HEALTH = new Set(["suspect", "failed"])` — const, line 168
- `interface AnnotationSegment` — interface, line 170
- `interface MarginAnnotation` — interface, line 176
- `function newKey(): string` — function, line 195
- `function readingPositionKey(sourceId: string): string` — function, line 203
- `const READER_CACHE_MS = 10 * 60_000` — const, line 214
- `function cachedSourceRead<T>(sourceId: string, key: QueryKey, fetcher: ()` — function, line 216
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 238
- `const contract: ReaderPromptContractDto | null = contractQuery.data ?? null` — const, line 242
- `const libraryQuery = useCachedQuery(["get_source_library"], ()` — const, line 251
- `const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null` — const, line 252
- `const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null)` — const, line 253
- `const authorRequestedRef = useRef<Set<string>>(new Set())` — const, line 348
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 349
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 350
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 351
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 352
- `const askFindInputRef = useRef<HTMLInputElement | null>(null)` — const, line 353
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 354
- `const readingRafRef = useRef<number | null>(null)` — const, line 355
- `const modeSaveVersionRef = useRef(0)` — const, line 356
- `const answerModeSaveVersionRef = useRef(0)` — const, line 357
- `let cancelled = false` — let, line 374
- `const scroller = railRef.current` — const, line 407
- `const clamp = ()` — const, line 409
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 410
- `const observer = new ResizeObserver(clamp)` — const, line 413
- `const query = librarySearch.trim()` — const, line 424
- `let cancelled = false` — let, line 431
- `const timer = window.setTimeout(()` — const, line 434
- `const resetSourceState = useCallback(()` — const, line 465
- `const openSource = useCallback( async (card: SourceLibraryCard, jumpSpan?: string)` — const, line 512
- `const view = await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], ()` — const, line 517
- `const savedSpan = window.localStorage.getItem(readingPositionKey(view.sourceId))` — const, line 529
- `const openFixture = useCallback(()` — const, line 589
- `const backToLibrary = useCallback(()` — const, line 597
- `const resumedRef = useRef(false)` — const, line 607
- `const enabled = contract?.readerEnabled ?? false` — const, line 615
- `const boundaryChecksAvailable = mode === "anchor" && sectionPromptsEnabled` — const, line 616
- `let cancelled = false` — let, line 623
- `const restored: ReaderExchange[] = result.exchanges.map((exchange)` — const, line 629
- `const live = new Map(current.map((exchange)` — const, line 638
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 652
- `const activeBlock = useMemo(()` — const, line 656
- `const trails: AnnotationTrail[] = useMemo(()` — const, line 661
- `const list: AnnotationTrail[] = []` — const, line 662
- `const annotatedSpans = useMemo( ()` — const, line 673
- `const boundaryBlock = useMemo(()` — const, line 677
- `const guideSectionBySpan = useMemo(()` — const, line 679
- `const map = new Map<string, ReaderGuideSectionDto>()` — const, line 680
- `const guideSectionByEnd = useMemo( ()` — const, line 686
- `const currentGuideSection = useMemo(()` — const, line 690
- `const positioned = guideSectionBySpan.get(readingSpan ?? activeSpan ?? "")` — const, line 691
- `const currentSectionProgress = useMemo(()` — const, line 694
- `const at = currentGuideSection.spanIds.indexOf(readingSpan ?? activeSpan ?? "")` — const, line 696
- `const currentQuestionDue = useMemo(()` — const, line 699
- `const phase = currentGuideSection?.question?.readingPhase` — const, line 700
- `const firstSpan = 1 / Math.max(1, currentGuideSection?.spanIds.length ?? 1)` — const, line 703
- `const sectionId = currentGuideSection.id` — const, line 714
- `const openQuestionSections = useMemo(()` — const, line 727
- `const sections = guidePlan?.sections ?? []` — const, line 728
- `const currentIndex = sections.findIndex((section)` — const, line 729
- `const pendingQuickCheckCount = boundaryChecksAvailable ? openQuestionSections.length : 0` — const, line 742
- `const currentQuestionOpen = useMemo( ()` — const, line 743
- `const readingProgress = useMemo(()` — const, line 747
- `const at = blocks.findIndex((block)` — const, line 748
- `const section = currentGuideSection` — const, line 768
- `const extractionId = render.extractionId` — const, line 773
- `const result = await api.readerAuthorSectionQuestion(` — const, line 776
- `const extractionId = render.extractionId` — const, line 790
- `let attempts = 0` — let, line 791
- `const timer = window.setInterval(()` — const, line 792
- `const revealedPassages = useMemo(()` — const, line 819
- `const revealed = new Set(revealedSections)` — const, line 820
- `const map = new Map<string,` — const, line 821
- `const revealedGuidanceSpans = useMemo(()` — const, line 830
- `const selectedSpanSet = useMemo( ()` — const, line 833
- `const editCaptureText = useCallback((text: string)` — const, line 841
- `const resetCaptureText = useCallback(()` — const, line 844
- `const updateReadingPosition = useCallback(()` — const, line 852
- `const container = bodyRef.current` — const, line 853
- `const containerRect = container.getBoundingClientRect()` — const, line 855
- `const markerY = containerRect.top + containerRect.height * 0.7` — const, line 856
- `const nodes = Array.from(container.querySelectorAll<HTMLElement>("[data-span-id]"))` — const, line 857
- `let best: HTMLElement | null = null` — let, line 858
- `let bestDistance = Number.POSITIVE_INFINITY` — let, line 859
- `const rect = node.getBoundingClientRect()` — const, line 861
- `const distance = Math.abs(Math.min(Math.max(markerY, rect.top), rect.bottom) - markerY)` — const, line 863
- `const onReadingScroll = useCallback(()` — const, line 872
- `const frame = window.requestAnimationFrame(updateReadingPosition)` — const, line 881
- `const revealSection = useCallback( (sectionId: string)` — const, line 889
- `const completeSection = useCallback( (sectionId: string)` — const, line 903
- `const refreshAnnotations = useCallback(async ()` — const, line 915
- `const result = await cachedSourceRead(render.sourceId, ["reader_source_annotations", render.sourceId], ()` — const, line 918
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 921
- `const version = (r.version as Record<string, unknown>) ??` — const, line 924
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 925
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 926
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 927
- `let page: number | null = null` — let, line 936
- `let bbox: number[] | null = null` — let, line 937
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 939
- `const saveAnnotationEdit = useCallback(async ()` — const, line 959
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 981
- `const result = await api.readerReanchor(` — const, line 985
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 1002
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 1023
- `const collectSelectionNodes = useCallback((): Array<` — const, line 1040
- `const sel = window.getSelection()` — const, line 1041
- `const container = bodyRef.current` — const, line 1042
- `const range = sel.getRangeAt(0)` — const, line 1044
- `const nodes: Array<` — const, line 1045
- `const seen = new Set<string>()` — const, line 1046
- `const spanId = el.dataset.spanId` — const, line 1048
- `let intersects = false` — let, line 1050
- `const sub = document.createRange()` — const, line 1057
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1065
- `const onMouseUp = useCallback(()` — const, line 1074
- `const sel = window.getSelection()` — const, line 1075
- `const quote = sel.toString().replace(/\s+/g, " ").trim()` — const, line 1077
- `const nodes = collectSelectionNodes()` — const, line 1079
- `const pdfSurfaceActive = Boolean(pdfView && surface === "pdf" && !offline)` — const, line 1102
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1106
- `const domDragRef = useRef<` — const, line 1107
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1109
- `const host = bodyRef.current` — const, line 1110
- `const rect = host.getBoundingClientRect()` — const, line 1112
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1116
- `const target = event.target as Node` — const, line 1120
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1122
- `const domDrafting = domDraft !== null` — const, line 1134
- `const rectFrom = (drag:` — const, line 1137
- `const onMove = (event: MouseEvent)` — const, line 1143
- `const drag = domDragRef.current` — const, line 1144
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1146
- `const onUp = (event: MouseEvent)` — const, line 1149
- `const drag = domDragRef.current` — const, line 1150
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1154
- `const rect = rectFrom(drag, point)` — const, line 1156
- `const next = [...domBoxesRef.current, rect]` — const, line 1159
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1176
- `const host = bodyRef.current` — const, line 1177
- `const hostRect = host.getBoundingClientRect()` — const, line 1179
- `const clientBoxes = boxes.map((b)` — const, line 1180
- `const nodes: Array<` — const, line 1186
- `const seen = new Set<string>()` — const, line 1187
- `const spanId = el.dataset.spanId` — const, line 1189
- `const elRect = el.getBoundingClientRect()` — const, line 1191
- `const touches = clientBoxes.some( (b)` — const, line 1192
- `const words: string[] = []` — const, line 1196
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 1197
- `const text = node as Text` — const, line 1199
- `const wordPattern = /\S+/g` — const, line 1200
- `let match: RegExpExecArray | null` — let, line 1201
- `const range = document.createRange()` — const, line 1203
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 1206
- `const cx = (Math.min(...rects.map((r)` — const, line 1208
- `const cy = (Math.min(...rects.map((r)` — const, line 1209
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 1213
- `const commitDomBoxes = useCallback(()` — const, line 1222
- `const boxes = domBoxesRef.current` — const, line 1223
- `const nodes = resolveDomBoxes(boxes)` — const, line 1225
- `const quote = nodes.map((n)` — const, line 1231
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 1238
- `const clearDomBoxes = ()` — const, line 1246
- `const onKeyDown = (event: KeyboardEvent)` — const, line 1252
- `const onKeyUp = (event: KeyboardEvent)` — const, line 1256
- `const onBlur = ()` — const, line 1262
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 1284
- `const point = domPointFromClient(request.x, request.y)` — const, line 1286
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 1287
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 1308
- `const retryRequest = useCallback(async (requestId: string)` — const, line 1321
- `const optimisticSegments = useCallback( (spanIds: string | string[]): AnnotationSegment[]` — const, line 1333
- `const ids = Array.isArray(spanIds) ? spanIds : [spanIds]` — const, line 1335
- `const geometry = pdfView?.blocks.find((b)` — const, line 1337
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 1347
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 1351
- `const quotedNodes = (()` — const, line 1356
- `const multi = collectSelectionNodes()` — const, line 1359
- `const optimisticIds = quotedNodes ? quotedNodes.map((n)` — const, line 1362
- `const nodes = quotedNodes ?? [` — const, line 1372
- `const receipt = await api.readerCapture(` — const, line 1373
- `const handler = (event: KeyboardEvent)` — const, line 1400
- `const clearSelection = useCallback(()` — const, line 1410
- `const onAltClear = (event: KeyboardEvent)` — const, line 1418
- `const target = event.target` — const, line 1420
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 1433
- `const segment = a.segments.find((s)` — const, line 1435
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1442
- `const jumpToSpan = useCallback( (spanId: string)` — const, line 1448
- `const geometry = pdfView.blocks.find((block)` — const, line 1456
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1462
- `const frame = window.requestAnimationFrame(()` — const, line 1472
- `const geometry = pdfView.blocks.find((block)` — const, line 1474
- `const element = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1478
- `const invokePreset = useCallback( async (preset: string)` — const, line 1489
- `const nodes = selectionNodes(selection)` — const, line 1492
- `const editedText = selection.editedText?.trim()` — const, line 1493
- `const nodeSpanIds = nodes.map((n)` — const, line 1494
- `const receipt = await api.readerInvokePreset(` — const, line 1506
- `const drained = await api.readerDrainOutbox()` — const, line 1529
- `const captureHighlight = useCallback(async ()` — const, line 1550
- `const nodes = selectionNodes(selection)` — const, line 1552
- `const nodeSpanIds = nodes.map((n)` — const, line 1553
- `const receipt = await api.readerCapture(` — const, line 1565
- `const pauseArc = useCallback(async ()` — const, line 1590
- `const next = await api.readerArc(` — const, line 1594
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 1601
- `const next = await api.readerArc(` — const, line 1606
- `const importExercise = useCallback(async ()` — const, line 1618
- `const nodes = selectionNodes(selection)` — const, line 1620
- `const editedText = selection.editedText?.trim()` — const, line 1621
- `const receipt = await api.readerImportExercise(` — const, line 1624
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 1649
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 1650
- `const timer = setInterval(async ()` — const, line 1654
- `const status = await api.readerExerciseImportStatus(` — const, line 1656
- `const saveOwnQuestion = useCallback(async ()` — const, line 1674
- `const saved = await api.readerAuthorQA(` — const, line 1681
- `const runCoach = useCallback(async ()` — const, line 1701
- `const lint = await api.readerCoachLint(` — const, line 1704
- `const changeMode = useCallback( async (next: string)` — const, line 1715
- `const previous = mode` — const, line 1717
- `const version = ++modeSaveVersionRef.current` — const, line 1720
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 1731
- `const answerModeNext = next as ReaderAnswerMode` — const, line 1733
- `const previous = answerMode` — const, line 1734
- `const version = ++answerModeSaveVersionRef.current` — const, line 1737
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 1752
- `const ask = useCallback(async ()` — const, line 1765
- `const groundingSpan = selection?.spanId ?? activeSpan` — const, line 1768
- `const asked = question.trim()` — const, line 1770
- `const answer = await api.readerAsk(` — const, line 1773
- `const exchange: ReaderExchange =` — const, line 1783
- `const next = new Set(ids)` — const, line 1793
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 1810
- `const normalizedAskFind = askFindQuery.trim().toLowerCase()` — const, line 1823
- `const visibleAskHistory = useMemo( ()` — const, line 1824
- `const onFind = (event: KeyboardEvent)` — const, line 1837
- `const readySources = (library ?? []).filter((c)` — const, line 1854
- `const pendingCount = (library ?? []).length - readySources.length` — const, line 1855
- `const card = (library ?? []).find((c)` — const, line 1894
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 1936
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 1937
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 2123
- `const active = activeSpan === block.spanId` — const, line 2124
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 2125
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 2126
- `const endQuestionAvailable = boundaryChecksAvailable && endSection?.question?.readingPhase === "after_section"` — const, line 2127
- `const offerSection = endSection && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 2129
- `const sel = window.getSelection()` — const, line 2141
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 2142
- `const active = railTab === tab` — const, line 2221
- `const guideAlert = tab === "guide" && pendingQuickCheckCount > 0` — const, line 2222
- `const currentIndex = guidePlan!.sections.findIndex((s)` — const, line 2308
- `const state = index < currentIndex ? "read" : index === currentIndex ? "current" : "upcoming"` — const, line 2309
- `const glyph = state === "read" ? "✓" : state === "current" ? "◐" : "·"` — const, line 2310
- `const spanId = selection?.spanId ?? activeSpan` — const, line 2574
- `const requestError = parseRequestError(request.errorJson)` — const, line 2681
- `const result = sourceObjectId ? synthesizedObjects.get(sourceObjectId) : undefined` — const, line 2682
- `const expanded = expandedRequests.has(request.id)` — const, line 2683
- `const proposalOpen = proposalId !== null && openProposalIds.has(proposalId)` — const, line 2684
- `const next = new Set(ids)` — const, line 2703
- `const expanded = normalizedAskFind.length > 0 || !collapsedAskIds.has(exchange.id)` — const, line 3029
- `const next = new Set(ids)` — const, line 3035
- `function SectionBoundaryOffer(` — function, line 3153
- `function AuthoredQuestionCard(` — function, line 3190
- `const question = section.question` — const, line 3203
- `const questionId = question?.authoredQuestionId ?? null` — const, line 3210
- `const sourceSpan = question?.spanIds?.[0] ?? null` — const, line 3211
- `const submit = useCallback(async ()` — const, line 3213
- `const dismissForever = useCallback(async ()` — const, line 3226
- `const escalate = useCallback(async ()` — const, line 3239
- `const result = await api.readerEscalateAuthoredQuestion(` — const, line 3243
- `function SectionQuestionCard(` — function, line 3333
- `const question = section.question` — const, line 3350
- `const begin = useCallback(async ()` — const, line 3358
- `const opened = await api.readerPresentQuestion(` — const, line 3362
- `const submit = useCallback(async ()` — const, line 3376
- `const skip = useCallback(async ()` — const, line 3394
- `const control = useCallback(async (value: string)` — const, line 3412
- `const choose = useCallback(async (next: ReaderDisposition)` — const, line 3445
- `const YT_ORIGIN = "https://www.youtube-nocookie.com"` — const, line 3551
- `function parseTimeLocator(value?: string | null): [number, number] | null` — function, line 3553
- `const match = /^t=(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$/.exec(value.trim())` — const, line 3555
- `function formatClock(seconds: number): string` — function, line 3559
- `const total = Math.max(0, Math.floor(seconds))` — const, line 3560
- `const h = Math.floor(total / 3600)` — const, line 3561
- `const m = Math.floor((total % 3600) / 60)` — const, line 3562
- `const sec = total % 60` — const, line 3563
- `interface TranscriptCue` — interface, line 3567
- `interface TranscriptSection` — interface, line 3573
- `function groupTranscriptCues(cues: TranscriptCue[]): TranscriptSection[]` — function, line 3583
- `const sections: TranscriptSection[] = []` — const, line 3584
- `const textLength = cue.block.markdown.trim().length` — const, line 3586
- `const current = sections[sections.length - 1]` — const, line 3587
- `const previous = current.cues[current.cues.length - 1]` — const, line 3593
- `const gap = cue.start - previous.end` — const, line 3594
- `const projectedDuration = Math.max(current.end, cue.end) - current.start` — const, line 3595
- `const previousEndsSentence = /[.!?]["')\]]?$/.test(previous.block.markdown.trim())` — const, line 3596
- `const shouldStartSection = gap >= 3 || projectedDuration > 18 || current.characters + textLength + 1 > 260 || (previous.end - current.start >= 10 && previousEndsSentence)` — const, line 3597
- `const YouTubeWatchPanel = forwardRef<WatchPanelHandle,` — const, line 3619
- `const iframeRef = useRef<HTMLIFrameElement | null>(null)` — const, line 3640
- `const transcriptRef = useRef<HTMLDivElement | null>(null)` — const, line 3641
- `const resumeSpanRef = useRef(resumeSpan)` — const, line 3645
- `const findInputRef = useRef<HTMLInputElement | null>(null)` — const, line 3650
- `const transcriptCues = useMemo<TranscriptCue[]>(()` — const, line 3652
- `const cues: TranscriptCue[] = []` — const, line 3653
- `const range = parseTimeLocator(block.extractorBlockId)` — const, line 3655
- `const transcriptSections = useMemo(()` — const, line 3662
- `const activeCue = useMemo(()` — const, line 3664
- `let active: TranscriptCue | null = null` — let, line 3665
- `const post = useCallback((func: string, args: unknown[] = [])` — const, line 3677
- `const handshake = useCallback(()` — const, line 3683
- `const resumeCue = transcriptCues.find((cue)` — const, line 3685
- `const onMessage = (event: MessageEvent)` — const, line 3694
- `let data:` — let, line 3696
- `const spanId = activeCue?.block.spanId ?? null` — const, line 3716
- `const scroller = transcriptRef.current` — const, line 3719
- `const cue = scroller?.querySelector(`[data-transcript-span="$` — const, line 3720
- `const scrollerRect = scroller.getBoundingClientRect()` — const, line 3727
- `const cueRect = cue.getBoundingClientRect()` — const, line 3728
- `const top = scroller.scrollTop + cueRect.top - scrollerRect.top - (scroller.clientHeight - cueRect.height) / 2` — const, line 3729
- `const pauseAndAsk = useCallback(()` — const, line 3735
- `let best: string | null = null` — let, line 3737
- `const range = parseTimeLocator(block.extractorBlockId)` — const, line 3739
- `const seekToCue = useCallback((cue: TranscriptCue)` — const, line 3747
- `const selection = window.getSelection()` — const, line 3748
- `const findNeedle = findQuery.trim().toLowerCase()` — const, line 3757
- `const findMatches = useMemo(()` — const, line 3758
- `const scrollToFindMatch = useCallback((index: number)` — const, line 3769
- `const cue = findMatches[index]` — const, line 3770
- `const scroller = transcriptRef.current` — const, line 3771
- `const el = scroller.querySelector(`[data-transcript-span="$` — const, line 3776
- `const scrollerRect = scroller.getBoundingClientRect()` — const, line 3778
- `const rect = el.getBoundingClientRect()` — const, line 3779
- `const top = scroller.scrollTop + rect.top - scrollerRect.top - (scroller.clientHeight - rect.height) / 2` — const, line 3780
- `const gotoFindMatch = useCallback((delta: number)` — const, line 3784
- `const openFind = useCallback(()` — const, line 3793
- `const closeFind = useCallback(()` — const, line 3798
- `const handler = (event: KeyboardEvent)` — const, line 3805
- `const cue = transcriptCues.find((c)` — const, line 3821
- `const activeSpanId = activeCue?.block.spanId` — const, line 3916
- `const active = section.cues.some((cue)` — const, line 3917
- `const annotated = section.cues.some((cue)` — const, line 3918
- `const guided = section.cues.some((cue)` — const, line 3919
- `const sectionKey = section.cues[0].block.spanId ?? `t-$` — const, line 3920
- `const spanId = cue.block.spanId ?? ""` — const, line 3930
- `const cueActive = activeSpanId === spanId` — const, line 3931
- `const cueAnnotated = annotatedSpans.has(spanId)` — const, line 3932
- `const cueGuided = guidanceSpans.has(spanId)` — const, line 3933
- `const cueFindHit = findOpen && findNeedle.length >= 2 && (cue.block.markdown ?? "").toLowerCase().includes(findNeedle)` — const, line 3934
- `const cueCurrentFind = cueFindHit && findMatches[matchIdx]?.block.spanId === spanId` — const, line 3936
- `const sel = window.getSelection()` — const, line 3945
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 3946

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: `ReaderOpenSource`; references `ReaderOpenSource`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export: `AnnotationTrail`; references `AnnotationTrail`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderAnswerMode`, `ReaderArcDto`, `ReaderCoachLintDto`, `ReaderDisposition`, `ReaderExerciseImportResult`, `ReaderGuidePlanDto`, `ReaderGuideSectionDto`, `ReaderPdfViewDto`, `ReaderPromptContractDto`, `ReaderRenderBlockDto`, `ReaderRenderViewDto`, `ReaderSourceSearchDto`, `ReaderWatchPlanDto`, `SourceLibraryCard`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export; imports `QueryKey`, `getOrFetch`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`, `readerTag`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export; imports `PdfReaderPane`, `PdfReaderPaneHandle`, `TagMenuRequest`
- [[Reference/Desktop/TypeScript/components/RectUnionOverlay|src/components/RectUnionOverlay.tsx]] — import-or-re-export; imports `RectUnionOverlay`
- [[Reference/Desktop/TypeScript/components/goldenpath/shared|src/components/goldenpath/shared.tsx]] — import-or-re-export; imports `AffectTap`, `DispositionPicker`, `PrimaryButton`, `SecondaryButton`
- [[Reference/Desktop/TypeScript/components/sourceTail|src/components/sourceTail.ts]] — import-or-re-export; imports `youtubeVideoId`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `SectionHeader`, `TermSelect`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/fixtures/readerRenderView|src/fixtures/readerRenderView.ts]] — import-or-re-export; imports `readerRenderViewFixture`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderRequests|src/screens/reader/useReaderRequests.ts]] — import-or-re-export; imports `parseRequestError`, `parseRequestResult`, `useReaderRequests`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `@tauri-apps/api/core`, `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

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

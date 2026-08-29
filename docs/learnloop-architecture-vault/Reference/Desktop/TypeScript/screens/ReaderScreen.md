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
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
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
| Source lines | 3922 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]]

## Public API

- `export interface SelectionNode` — interface, line 123
- `export interface AnnotationTrail` — interface, line 184
- `export function ReaderScreen(` — function, line 204
- `export interface WatchPanelHandle` — interface, line 3562

## Internal implementation anchors

- `const ANSWER_MODE_OPTIONS = [` — const, line 50
- `const READER_MODE_OPTIONS = [` — const, line 56
- `const PALETTE: Array<` — const, line 67
- `const QUESTION_CONTROLS: Array<` — const, line 94
- `const TAG_ACTIONS: Array<` — const, line 106
- `const WHOLE_BLOCK_QUOTE = "(whole block)"` — const, line 114
- `function clip(text: string, max: number): string` — function, line 116
- `function selectionNodes(sel:` — function, line 133
- `interface ReaderExchange` — interface, line 141
- `type ReaderRailTab = "guide" | "ask" | "notes"` — type, line 150
- `const HEALTH_COLOR: Record<string, "green" | "amber" | "pink" | "slate"> =` — const, line 152
- `const FURNITURE_BLOCK_TYPES = new Set(["PageHeader", "PageFooter", "TableOfContents"])` — const, line 161
- `const BADGED_HEALTH = new Set(["suspect", "failed"])` — const, line 165
- `interface AnnotationSegment` — interface, line 167
- `interface MarginAnnotation` — interface, line 173
- `function newKey(): string` — function, line 192
- `function readingPositionKey(sourceId: string): string` — function, line 200
- `const authorRequestedRef = useRef<Set<string>>(new Set())` — const, line 308
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 309
- `const railRef = useRef<HTMLDivElement | null>(null)` — const, line 310
- `const paneRef = useRef<PdfReaderPaneHandle | null>(null)` — const, line 311
- `const watchRef = useRef<WatchPanelHandle | null>(null)` — const, line 312
- `const askFindInputRef = useRef<HTMLInputElement | null>(null)` — const, line 313
- `const askComposerRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 314
- `const readingRafRef = useRef<number | null>(null)` — const, line 315
- `const modeSaveVersionRef = useRef(0)` — const, line 316
- `const answerModeSaveVersionRef = useRef(0)` — const, line 317
- `let cancelled = false` — let, line 334
- `const scroller = railRef.current` — const, line 367
- `const clamp = ()` — const, line 369
- `const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight)` — const, line 370
- `const observer = new ResizeObserver(clamp)` — const, line 373
- `const query = librarySearch.trim()` — const, line 384
- `let cancelled = false` — let, line 391
- `const timer = window.setTimeout(()` — const, line 394
- `const resetSourceState = useCallback(()` — const, line 441
- `const openSource = useCallback( async (card: SourceLibraryCard, jumpSpan?: string)` — const, line 488
- `const view = await api.readerRenderView(` — const, line 493
- `const savedSpan = window.localStorage.getItem(readingPositionKey(view.sourceId))` — const, line 499
- `const openFixture = useCallback(()` — const, line 552
- `const backToLibrary = useCallback(()` — const, line 559
- `const enabled = contract?.readerEnabled ?? false` — const, line 566
- `const boundaryChecksAvailable = mode === "anchor" && sectionPromptsEnabled` — const, line 567
- `let cancelled = false` — let, line 574
- `const restored: ReaderExchange[] = result.exchanges.map((exchange)` — const, line 579
- `const live = new Map(current.map((exchange)` — const, line 588
- `const blocks: ReaderRenderBlockDto[] = useMemo( ()` — const, line 602
- `const activeBlock = useMemo(()` — const, line 606
- `const trails: AnnotationTrail[] = useMemo(()` — const, line 611
- `const list: AnnotationTrail[] = []` — const, line 612
- `const annotatedSpans = useMemo( ()` — const, line 623
- `const boundaryBlock = useMemo(()` — const, line 627
- `const guideSectionBySpan = useMemo(()` — const, line 629
- `const map = new Map<string, ReaderGuideSectionDto>()` — const, line 630
- `const guideSectionByEnd = useMemo( ()` — const, line 636
- `const currentGuideSection = useMemo(()` — const, line 640
- `const positioned = guideSectionBySpan.get(readingSpan ?? activeSpan ?? "")` — const, line 641
- `const currentSectionProgress = useMemo(()` — const, line 644
- `const at = currentGuideSection.spanIds.indexOf(readingSpan ?? activeSpan ?? "")` — const, line 646
- `const currentQuestionDue = useMemo(()` — const, line 649
- `const phase = currentGuideSection?.question?.readingPhase` — const, line 650
- `const firstSpan = 1 / Math.max(1, currentGuideSection?.spanIds.length ?? 1)` — const, line 653
- `const sectionId = currentGuideSection.id` — const, line 664
- `const openQuestionSections = useMemo(()` — const, line 677
- `const sections = guidePlan?.sections ?? []` — const, line 678
- `const currentIndex = sections.findIndex((section)` — const, line 679
- `const pendingQuickCheckCount = boundaryChecksAvailable ? openQuestionSections.length : 0` — const, line 692
- `const currentQuestionOpen = useMemo( ()` — const, line 693
- `const readingProgress = useMemo(()` — const, line 697
- `const at = blocks.findIndex((block)` — const, line 698
- `const section = currentGuideSection` — const, line 718
- `const extractionId = render.extractionId` — const, line 723
- `const result = await api.readerAuthorSectionQuestion(` — const, line 726
- `const extractionId = render.extractionId` — const, line 740
- `let attempts = 0` — let, line 741
- `const timer = window.setInterval(()` — const, line 742
- `const revealedPassages = useMemo(()` — const, line 769
- `const revealed = new Set(revealedSections)` — const, line 770
- `const map = new Map<string,` — const, line 771
- `const revealedGuidanceSpans = useMemo(()` — const, line 780
- `const selectedSpanSet = useMemo( ()` — const, line 783
- `const editCaptureText = useCallback((text: string)` — const, line 791
- `const resetCaptureText = useCallback(()` — const, line 794
- `const updateReadingPosition = useCallback(()` — const, line 802
- `const container = bodyRef.current` — const, line 803
- `const containerRect = container.getBoundingClientRect()` — const, line 805
- `const markerY = containerRect.top + containerRect.height * 0.7` — const, line 806
- `const nodes = Array.from(container.querySelectorAll<HTMLElement>("[data-span-id]"))` — const, line 807
- `let best: HTMLElement | null = null` — let, line 808
- `let bestDistance = Number.POSITIVE_INFINITY` — let, line 809
- `const rect = node.getBoundingClientRect()` — const, line 811
- `const distance = Math.abs(Math.min(Math.max(markerY, rect.top), rect.bottom) - markerY)` — const, line 813
- `const onReadingScroll = useCallback(()` — const, line 822
- `const frame = window.requestAnimationFrame(updateReadingPosition)` — const, line 831
- `const revealSection = useCallback( (sectionId: string)` — const, line 839
- `const completeSection = useCallback( (sectionId: string)` — const, line 853
- `const refreshAnnotations = useCallback(async ()` — const, line 865
- `const result = await api.readerSourceAnnotations(` — const, line 868
- `const rows = (result.annotations as Array<Record<string, unknown>>) ?? []` — const, line 869
- `const version = (r.version as Record<string, unknown>) ??` — const, line 872
- `const segments = (r.segments as Array<Record<string, unknown>>) ?? []` — const, line 873
- `const anchor = (r.anchor as Record<string, unknown>) ??` — const, line 874
- `const annotation = (r.annotation as Record<string, unknown>) ??` — const, line 875
- `let page: number | null = null` — let, line 884
- `let bbox: number[] | null = null` — let, line 885
- `const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as` — const, line 887
- `const saveAnnotationEdit = useCallback(async ()` — const, line 907
- `const reanchorAnnotation = useCallback(async (annotationId: string)` — const, line 929
- `const result = await api.readerReanchor(` — const, line 933
- `const manualAnchorToSelection = useCallback(async (annotationId: string)` — const, line 950
- `const deleteAnnotation = useCallback(async (annotationId: string)` — const, line 971
- `const collectSelectionNodes = useCallback((): Array<` — const, line 988
- `const sel = window.getSelection()` — const, line 989
- `const container = bodyRef.current` — const, line 990
- `const range = sel.getRangeAt(0)` — const, line 992
- `const nodes: Array<` — const, line 993
- `const seen = new Set<string>()` — const, line 994
- `const spanId = el.dataset.spanId` — const, line 996
- `let intersects = false` — let, line 998
- `const sub = document.createRange()` — const, line 1005
- `const quote = sub.toString().replace(/\s+/g, " ").trim()` — const, line 1013
- `const onMouseUp = useCallback(()` — const, line 1022
- `const sel = window.getSelection()` — const, line 1023
- `const quote = sel.toString().replace(/\s+/g, " ").trim()` — const, line 1025
- `const nodes = collectSelectionNodes()` — const, line 1027
- `const pdfSurfaceActive = Boolean(pdfView && surface === "pdf" && !offline)` — const, line 1050
- `const domBoxesRef = useRef<number[][]>([])` — const, line 1054
- `const domDragRef = useRef<` — const, line 1055
- `const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null` — const, line 1057
- `const host = bodyRef.current` — const, line 1058
- `const rect = host.getBoundingClientRect()` — const, line 1060
- `const onBodyMouseDown = useCallback( (event: React.MouseEvent)` — const, line 1064
- `const target = event.target as Node` — const, line 1068
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1070
- `const domDrafting = domDraft !== null` — const, line 1082
- `const rectFrom = (drag:` — const, line 1085
- `const onMove = (event: MouseEvent)` — const, line 1091
- `const drag = domDragRef.current` — const, line 1092
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1094
- `const onUp = (event: MouseEvent)` — const, line 1097
- `const drag = domDragRef.current` — const, line 1098
- `const point = domPointFromClient(event.clientX, event.clientY)` — const, line 1102
- `const rect = rectFrom(drag, point)` — const, line 1104
- `const next = [...domBoxesRef.current, rect]` — const, line 1107
- `const resolveDomBoxes = useCallback((boxes: number[][]): Array<` — const, line 1124
- `const host = bodyRef.current` — const, line 1125
- `const hostRect = host.getBoundingClientRect()` — const, line 1127
- `const clientBoxes = boxes.map((b)` — const, line 1128
- `const nodes: Array<` — const, line 1134
- `const seen = new Set<string>()` — const, line 1135
- `const spanId = el.dataset.spanId` — const, line 1137
- `const elRect = el.getBoundingClientRect()` — const, line 1139
- `const touches = clientBoxes.some( (b)` — const, line 1140
- `const words: string[] = []` — const, line 1144
- `const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)` — const, line 1145
- `const text = node as Text` — const, line 1147
- `const wordPattern = /\S+/g` — const, line 1148
- `let match: RegExpExecArray | null` — let, line 1149
- `const range = document.createRange()` — const, line 1151
- `const rects = Array.from(range.getClientRects()).filter((r)` — const, line 1154
- `const cx = (Math.min(...rects.map((r)` — const, line 1156
- `const cy = (Math.min(...rects.map((r)` — const, line 1157
- `const quote = words.join(" ").replace(/\s+/g, " ").trim()` — const, line 1161
- `const commitDomBoxes = useCallback(()` — const, line 1170
- `const boxes = domBoxesRef.current` — const, line 1171
- `const nodes = resolveDomBoxes(boxes)` — const, line 1173
- `const quote = nodes.map((n)` — const, line 1179
- `const commitDomBoxesRef = useRef(commitDomBoxes)` — const, line 1186
- `const clearDomBoxes = ()` — const, line 1194
- `const onKeyDown = (event: KeyboardEvent)` — const, line 1200
- `const onKeyUp = (event: KeyboardEvent)` — const, line 1204
- `const onBlur = ()` — const, line 1210
- `const openDomTagMenu = useCallback( (request: TagMenuRequest)` — const, line 1232
- `const point = domPointFromClient(request.x, request.y)` — const, line 1234
- `const insideCommittedBox = point !== null && domBoxesRef.current.some( (box)` — const, line 1235
- `const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject")` — const, line 1256
- `const retryRequest = useCallback(async (requestId: string)` — const, line 1269
- `const optimisticSegments = useCallback( (spanIds: string | string[]): AnnotationSegment[]` — const, line 1281
- `const ids = Array.isArray(spanIds) ? spanIds : [spanIds]` — const, line 1283
- `const geometry = pdfView?.blocks.find((b)` — const, line 1285
- `const tagCapture = useCallback( async (action: string, target: TagMenuRequest)` — const, line 1295
- `const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE` — const, line 1299
- `const quotedNodes = (()` — const, line 1304
- `const multi = collectSelectionNodes()` — const, line 1307
- `const optimisticIds = quotedNodes ? quotedNodes.map((n)` — const, line 1310
- `const nodes = quotedNodes ?? [` — const, line 1320
- `const receipt = await api.readerCapture(` — const, line 1321
- `const handler = (event: KeyboardEvent)` — const, line 1348
- `const clearSelection = useCallback(()` — const, line 1358
- `const onAltClear = (event: KeyboardEvent)` — const, line 1366
- `const target = event.target` — const, line 1368
- `const jumpToAnnotation = useCallback( (a: MarginAnnotation)` — const, line 1381
- `const segment = a.segments.find((s)` — const, line 1383
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1390
- `const jumpToSpan = useCallback( (spanId: string)` — const, line 1396
- `const geometry = pdfView.blocks.find((block)` — const, line 1404
- `const el = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1410
- `const frame = window.requestAnimationFrame(()` — const, line 1420
- `const geometry = pdfView.blocks.find((block)` — const, line 1422
- `const element = bodyRef.current?.querySelector(`[data-span-id="$` — const, line 1426
- `const invokePreset = useCallback( async (preset: string)` — const, line 1437
- `const nodes = selectionNodes(selection)` — const, line 1440
- `const editedText = selection.editedText?.trim()` — const, line 1441
- `const nodeSpanIds = nodes.map((n)` — const, line 1442
- `const receipt = await api.readerInvokePreset(` — const, line 1454
- `const drained = await api.readerDrainOutbox()` — const, line 1477
- `const captureHighlight = useCallback(async ()` — const, line 1498
- `const nodes = selectionNodes(selection)` — const, line 1500
- `const nodeSpanIds = nodes.map((n)` — const, line 1501
- `const receipt = await api.readerCapture(` — const, line 1513
- `const pauseArc = useCallback(async ()` — const, line 1538
- `const next = await api.readerArc(` — const, line 1542
- `const setArcPolicy = useCallback( async (policy: string)` — const, line 1549
- `const next = await api.readerArc(` — const, line 1554
- `const importExercise = useCallback(async ()` — const, line 1566
- `const nodes = selectionNodes(selection)` — const, line 1568
- `const editedText = selection.editedText?.trim()` — const, line 1569
- `const receipt = await api.readerImportExercise(` — const, line 1572
- `const exerciseImportBatchId = exerciseImport?.batchId ?? null` — const, line 1597
- `const exerciseImportActive = exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status)` — const, line 1598
- `const timer = setInterval(async ()` — const, line 1602
- `const status = await api.readerExerciseImportStatus(` — const, line 1604
- `const saveOwnQuestion = useCallback(async ()` — const, line 1622
- `const saved = await api.readerAuthorQA(` — const, line 1629
- `const runCoach = useCallback(async ()` — const, line 1649
- `const lint = await api.readerCoachLint(` — const, line 1652
- `const changeMode = useCallback( async (next: string)` — const, line 1663
- `const previous = mode` — const, line 1665
- `const version = ++modeSaveVersionRef.current` — const, line 1668
- `const changeAnswerMode = useCallback( async (next: string)` — const, line 1679
- `const answerModeNext = next as ReaderAnswerMode` — const, line 1681
- `const previous = answerMode` — const, line 1682
- `const version = ++answerModeSaveVersionRef.current` — const, line 1685
- `const sendQuestionControl = useCallback( async (control: string)` — const, line 1700
- `const ask = useCallback(async ()` — const, line 1713
- `const groundingSpan = selection?.spanId ?? activeSpan` — const, line 1716
- `const asked = question.trim()` — const, line 1718
- `const answer = await api.readerAsk(` — const, line 1721
- `const exchange: ReaderExchange =` — const, line 1731
- `const next = new Set(ids)` — const, line 1741
- `const chooseDisposition = useCallback( async (d: ReaderDisposition)` — const, line 1758
- `const normalizedAskFind = askFindQuery.trim().toLowerCase()` — const, line 1771
- `const visibleAskHistory = useMemo( ()` — const, line 1772
- `const onFind = (event: KeyboardEvent)` — const, line 1785
- `const readySources = (library ?? []).filter((c)` — const, line 1802
- `const pendingCount = (library ?? []).length - readySources.length` — const, line 1803
- `const card = (library ?? []).find((c)` — const, line 1842
- `const cardOpenable = enabled && card.readerEnabled !== false` — const, line 1884
- `const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null` — const, line 1885
- `const isSection = (block.blockType ?? "") === "Section"` — const, line 2071
- `const active = activeSpan === block.spanId` — const, line 2072
- `const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined` — const, line 2073
- `const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined` — const, line 2074
- `const endQuestionAvailable = boundaryChecksAvailable && endSection?.question?.readingPhase === "after_section"` — const, line 2075
- `const offerSection = endSection && !dismissedSections.includes(endSection.id) && !completedSections.includes(endSection.id) && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0)` — const, line 2077
- `const sel = window.getSelection()` — const, line 2089
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 2090
- `const active = railTab === tab` — const, line 2169
- `const guideAlert = tab === "guide" && pendingQuickCheckCount > 0` — const, line 2170
- `const currentIndex = guidePlan!.sections.findIndex((s)` — const, line 2256
- `const state = index < currentIndex ? "read" : index === currentIndex ? "current" : "upcoming"` — const, line 2257
- `const glyph = state === "read" ? "✓" : state === "current" ? "◐" : "·"` — const, line 2258
- `const spanId = selection?.spanId ?? activeSpan` — const, line 2522
- `const requestError = parseRequestError(request.errorJson)` — const, line 2629
- `const result = sourceObjectId ? synthesizedObjects.get(sourceObjectId) : undefined` — const, line 2630
- `const expanded = expandedRequests.has(request.id)` — const, line 2631
- `const proposalOpen = proposalId !== null && openProposalIds.has(proposalId)` — const, line 2632
- `const next = new Set(ids)` — const, line 2651
- `const expanded = normalizedAskFind.length > 0 || !collapsedAskIds.has(exchange.id)` — const, line 2977
- `const next = new Set(ids)` — const, line 2983
- `function SectionBoundaryOffer(` — function, line 3101
- `function AuthoredQuestionCard(` — function, line 3138
- `const question = section.question` — const, line 3151
- `const questionId = question?.authoredQuestionId ?? null` — const, line 3158
- `const sourceSpan = question?.spanIds?.[0] ?? null` — const, line 3159
- `const submit = useCallback(async ()` — const, line 3161
- `const dismissForever = useCallback(async ()` — const, line 3174
- `const escalate = useCallback(async ()` — const, line 3187
- `const result = await api.readerEscalateAuthoredQuestion(` — const, line 3191
- `function SectionQuestionCard(` — function, line 3281
- `const question = section.question` — const, line 3298
- `const begin = useCallback(async ()` — const, line 3306
- `const opened = await api.readerPresentQuestion(` — const, line 3310
- `const submit = useCallback(async ()` — const, line 3324
- `const skip = useCallback(async ()` — const, line 3342
- `const control = useCallback(async (value: string)` — const, line 3360
- `const choose = useCallback(async (next: ReaderDisposition)` — const, line 3393
- `const YT_ORIGIN = "https://www.youtube-nocookie.com"` — const, line 3499
- `function parseTimeLocator(value?: string | null): [number, number] | null` — function, line 3501
- `const match = /^t=(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$/.exec(value.trim())` — const, line 3503
- `function formatClock(seconds: number): string` — function, line 3507
- `const total = Math.max(0, Math.floor(seconds))` — const, line 3508
- `const h = Math.floor(total / 3600)` — const, line 3509
- `const m = Math.floor((total % 3600) / 60)` — const, line 3510
- `const sec = total % 60` — const, line 3511
- `interface TranscriptCue` — interface, line 3515
- `interface TranscriptSection` — interface, line 3521
- `function groupTranscriptCues(cues: TranscriptCue[]): TranscriptSection[]` — function, line 3531
- `const sections: TranscriptSection[] = []` — const, line 3532
- `const textLength = cue.block.markdown.trim().length` — const, line 3534
- `const current = sections[sections.length - 1]` — const, line 3535
- `const previous = current.cues[current.cues.length - 1]` — const, line 3541
- `const gap = cue.start - previous.end` — const, line 3542
- `const projectedDuration = Math.max(current.end, cue.end) - current.start` — const, line 3543
- `const previousEndsSentence = /[.!?]["')\]]?$/.test(previous.block.markdown.trim())` — const, line 3544
- `const shouldStartSection = gap >= 3 || projectedDuration > 18 || current.characters + textLength + 1 > 260 || (previous.end - current.start >= 10 && previousEndsSentence)` — const, line 3545
- `const YouTubeWatchPanel = forwardRef<WatchPanelHandle,` — const, line 3567
- `const iframeRef = useRef<HTMLIFrameElement | null>(null)` — const, line 3588
- `const transcriptRef = useRef<HTMLDivElement | null>(null)` — const, line 3589
- `const resumeSpanRef = useRef(resumeSpan)` — const, line 3593
- `const findInputRef = useRef<HTMLInputElement | null>(null)` — const, line 3598
- `const transcriptCues = useMemo<TranscriptCue[]>(()` — const, line 3600
- `const cues: TranscriptCue[] = []` — const, line 3601
- `const range = parseTimeLocator(block.extractorBlockId)` — const, line 3603
- `const transcriptSections = useMemo(()` — const, line 3610
- `const activeCue = useMemo(()` — const, line 3612
- `let active: TranscriptCue | null = null` — let, line 3613
- `const post = useCallback((func: string, args: unknown[] = [])` — const, line 3625
- `const handshake = useCallback(()` — const, line 3631
- `const resumeCue = transcriptCues.find((cue)` — const, line 3633
- `const onMessage = (event: MessageEvent)` — const, line 3642
- `let data:` — let, line 3644
- `const spanId = activeCue?.block.spanId ?? null` — const, line 3664
- `const scroller = transcriptRef.current` — const, line 3667
- `const cue = scroller?.querySelector(`[data-transcript-span="$` — const, line 3668
- `const scrollerRect = scroller.getBoundingClientRect()` — const, line 3675
- `const cueRect = cue.getBoundingClientRect()` — const, line 3676
- `const top = scroller.scrollTop + cueRect.top - scrollerRect.top - (scroller.clientHeight - cueRect.height) / 2` — const, line 3677
- `const pauseAndAsk = useCallback(()` — const, line 3683
- `let best: string | null = null` — let, line 3685
- `const range = parseTimeLocator(block.extractorBlockId)` — const, line 3687
- `const seekToCue = useCallback((cue: TranscriptCue)` — const, line 3695
- `const selection = window.getSelection()` — const, line 3696
- `const findNeedle = findQuery.trim().toLowerCase()` — const, line 3705
- `const findMatches = useMemo(()` — const, line 3706
- `const scrollToFindMatch = useCallback((index: number)` — const, line 3717
- `const cue = findMatches[index]` — const, line 3718
- `const scroller = transcriptRef.current` — const, line 3719
- `const el = scroller.querySelector(`[data-transcript-span="$` — const, line 3724
- `const scrollerRect = scroller.getBoundingClientRect()` — const, line 3726
- `const rect = el.getBoundingClientRect()` — const, line 3727
- `const top = scroller.scrollTop + rect.top - scrollerRect.top - (scroller.clientHeight - rect.height) / 2` — const, line 3728
- `const gotoFindMatch = useCallback((delta: number)` — const, line 3732
- `const openFind = useCallback(()` — const, line 3741
- `const closeFind = useCallback(()` — const, line 3746
- `const handler = (event: KeyboardEvent)` — const, line 3753
- `const cue = transcriptCues.find((c)` — const, line 3769
- `const activeSpanId = activeCue?.block.spanId` — const, line 3864
- `const active = section.cues.some((cue)` — const, line 3865
- `const annotated = section.cues.some((cue)` — const, line 3866
- `const guided = section.cues.some((cue)` — const, line 3867
- `const sectionKey = section.cues[0].block.spanId ?? `t-$` — const, line 3868
- `const spanId = cue.block.spanId ?? ""` — const, line 3878
- `const cueActive = activeSpanId === spanId` — const, line 3879
- `const cueAnnotated = annotatedSpans.has(spanId)` — const, line 3880
- `const cueGuided = guidanceSpans.has(spanId)` — const, line 3881
- `const cueFindHit = findOpen && findNeedle.length >= 2 && (cue.block.markdown ?? "").toLowerCase().includes(findNeedle)` — const, line 3882
- `const cueCurrentFind = cueFindHit && findMatches[matchIdx]?.block.spanId === spanId` — const, line 3884
- `const sel = window.getSelection()` — const, line 3893
- `const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : ""` — const, line 3894

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `ReaderScreen`; references `ReaderScreen`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export: `AnnotationTrail`; references `AnnotationTrail`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderAnswerMode`, `ReaderArcDto`, `ReaderCoachLintDto`, `ReaderDisposition`, `ReaderExerciseImportResult`, `ReaderGuidePlanDto`, `ReaderGuideSectionDto`, `ReaderPdfViewDto`, `ReaderPromptContractDto`, `ReaderRenderBlockDto`, `ReaderRenderViewDto`, `ReaderSourceSearchDto`, `ReaderWatchPlanDto`, `SourceLibraryCard`
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
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/ReaderScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/ReaderScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

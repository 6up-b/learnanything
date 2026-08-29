---
title: "Desktop module · src/components/PdfReaderPane.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.PdfReaderPane"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/PdfReaderPane.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/PdfReaderPane.tsx"
source_commit: "0e91c7ba1b7ff32d5d093dd62826890b70445d3f"
source_commit_timestamp: "2026-08-03T22:04:38-04:00"
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

# `src/components/PdfReaderPane.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `PdfReaderPane` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/PdfReaderPane.tsx](../../../../../../apps/learnloop-tauri/src/components/PdfReaderPane.tsx) |
| Source lines | 1338 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `0e91c7ba1b7ff32d5d093dd62826890b70445d3f` |
| Commit timestamp | `2026-08-03T22:04:38-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]]

## Public API

- `export interface TagMenuRequest` — interface, line 79
- `export interface PdfReaderPaneHandle` — interface, line 91
- `export const PdfReaderPane = forwardRef<PdfReaderPaneHandle, PdfReaderPaneProps>(function PdfReaderPane(` — const, line 118

## Internal implementation anchors

- `interface PageGeometry` — interface, line 34
- `const TRAIL_COLORS: Record<string,` — const, line 41
- `const FURNITURE_TYPES = new Set(["PageHeader", "PageFooter", "TableOfContents"])` — const, line 48
- `function isSelectable(block: ReaderPdfBlockDto): boolean` — function, line 50
- `interface MarqueeBox` — interface, line 57
- `const MARQUEE_MIN_EXTENT_PTS = 4` — const, line 63
- `function rectOverlap(a: number[], b: number[]): number` — function, line 65
- `const w = Math.min(a[2], b[2]) - Math.max(a[0], b[0])` — const, line 66
- `const h = Math.min(a[3], b[3]) - Math.max(a[1], b[1])` — const, line 67
- `function rectArea(r: number[]): number` — function, line 71
- `const EMPTY_SPANS = new Set<string>()` — const, line 75
- `interface PdfReaderPaneProps` — interface, line 95
- `interface FindMatch` — interface, line 113
- `const containerRef = useRef<HTMLDivElement | null>(null)` — const, line 125
- `const pageTextsRef = useRef<Map<number, string>>(new Map())` — const, line 133
- `const findInputRef = useRef<HTMLInputElement | null>(null)` — const, line 134
- `const clampZoom = (value: number)` — const, line 136
- `const zoomIn = useCallback(()` — const, line 137
- `const zoomOut = useCallback(()` — const, line 138
- `const openFind = useCallback(()` — const, line 140
- `const closeFind = useCallback(()` — const, line 144
- `const coveredPages = useMemo( ()` — const, line 151
- `const blocksByPage = useMemo(()` — const, line 155
- `const map = new Map<number, ReaderPdfBlockDto[]>()` — const, line 156
- `const list = map.get(block.page) ?? []` — const, line 158
- `const trailsByPage = useMemo(()` — const, line 164
- `const map = new Map<number, AnnotationTrail[]>()` — const, line 165
- `const list = map.get(trail.page) ?? []` — const, line 167
- `let cancelled = false` — let, line 175
- `let task: ReturnType<typeof pdfjs.getDocument> | null = null` — let, line 176
- `const response = await fetch(fileUrl)` — const, line 179
- `const data = new Uint8Array(await response.arrayBuffer())` — const, line 181
- `const loaded = await task.promise` — const, line 183
- `const node = containerRef.current` — const, line 197
- `const observer = new ResizeObserver(()` — const, line 199
- `let cancelled = false` — let, line 217
- `const timer = setTimeout(async ()` — const, line 218
- `const query = findQuery.trim().toLowerCase()` — const, line 219
- `const found: FindMatch[] = []` — const, line 220
- `let text = pageTextsRef.current.get(page)` — let, line 222
- `const pdfPage = await doc.getPage(page + 1)` — const, line 225
- `const content = await pdfPage.getTextContent()` — const, line 226
- `let from = 0` — let, line 238
- `let ordinal = 0` — let, line 239
- `const at = text.indexOf(query, from)` — const, line 241
- `const scrollToMatch = useCallback((match: FindMatch)` — const, line 259
- `const pageEl = containerRef.current?.querySelector(`[data-pdf-page="$` — const, line 260
- `const hits = pageEl.querySelectorAll(".ll-find-hit")` — const, line 263
- `const target = hits[Math.min(match.ordinal, Math.max(0, hits.length - 1))]` — const, line 264
- `const current = matches[matchIdx]` — const, line 269
- `const gotoMatch = useCallback( (delta: number)` — const, line 273
- `const handler = (event: KeyboardEvent)` — const, line 282
- `const modifier = event.ctrlKey || event.metaKey` — const, line 283
- `const editing = event.target instanceof HTMLElement && ["INPUT", "TEXTAREA"].includes(event.target.tagName)` — const, line 289
- `const node = containerRef.current` — const, line 308
- `const onWheel = (event: WheelEvent)` — const, line 310
- `const scrollToSegment = useCallback((page: number, spanId?: string | null)` — const, line 319
- `const pageEl = containerRef.current?.querySelector(`[data-pdf-page="$` — const, line 320
- `const target = spanId ? pageEl.querySelector(`[data-span-id="$` — const, line 324
- `const blockAtPoint = useCallback( (pageEl: HTMLElement, clientX: number, clientY: number): ReaderPdfBlockDto | null` — const, line 331
- `const page = Number(pageEl.dataset.pdfPage)` — const, line 333
- `const widthPoints = Number(pageEl.dataset.widthPoints)` — const, line 334
- `const rect = pageEl.getBoundingClientRect()` — const, line 335
- `const scale = rect.width / widthPoints` — const, line 337
- `const x = (clientX - rect.left) / scale` — const, line 338
- `const y = (clientY - rect.top) / scale` — const, line 339
- `const candidates = (blocksByPage.get(page) ?? []).filter( (b)` — const, line 340
- `const pageElFor = (node: Node | null): HTMLElement | null` — const, line 354
- `let current: Node | null = node` — let, line 355
- `const indexBySpan = useMemo(()` — const, line 366
- `const blockBySpan = useMemo(()` — const, line 367
- `const blockNearPoint = useCallback( (pageEl: HTMLElement, clientX: number, clientY: number): ReaderPdfBlockDto | null` — const, line 371
- `const direct = blockAtPoint(pageEl, clientX, clientY)` — const, line 373
- `const page = Number(pageEl.dataset.pdfPage)` — const, line 375
- `const widthPoints = Number(pageEl.dataset.widthPoints)` — const, line 376
- `const rect = pageEl.getBoundingClientRect()` — const, line 377
- `const scale = rect.width / widthPoints` — const, line 379
- `const x = (clientX - rect.left) / scale` — const, line 380
- `const y = (clientY - rect.top) / scale` — const, line 381
- `let best: ReaderPdfBlockDto | null = null` — let, line 382
- `let bestDistance = Infinity` — let, line 383
- `const dx = x < block.bbox[0] ? block.bbox[0] - x : x > block.bbox[2] ? x - block.bbox[2] : 0` — const, line 386
- `const dy = y < block.bbox[1] ? block.bbox[1] - y : y > block.bbox[3] ? y - block.bbox[3] : 0` — const, line 387
- `const distance = dy * 4 + dx` — const, line 388
- `const sweepRef = useRef<` — const, line 400
- `const lastPointRef = useRef<` — const, line 401
- `const sweeping = sweep !== null` — const, line 402
- `const marqueeBoxesRef = useRef<MarqueeBox[]>([])` — const, line 409
- `const marqueeDragRef = useRef<` — const, line 410
- `const clearMarquee = useCallback(()` — const, line 411
- `const sweepSpans = useMemo(()` — const, line 418
- `const lo = Math.min(sweep.anchor, sweep.head)` — const, line 420
- `const hi = Math.max(sweep.anchor, sweep.head)` — const, line 421
- `const onSweepMouseDown = useCallback( (event: React.MouseEvent)` — const, line 425
- `const target = event.target as Node` — const, line 431
- `const pageEl = pageElFor(target)` — const, line 433
- `const block = blockNearPoint(pageEl, event.clientX, event.clientY)` — const, line 435
- `const idx = block ? indexBySpan.get(block.spanId) : undefined` — const, line 436
- `const updateHead = (clientX: number, clientY: number)` — const, line 453
- `const state = sweepRef.current` — const, line 454
- `const pageEl = pageElFor(document.elementFromPoint(clientX, clientY))` — const, line 456
- `const block = blockNearPoint(pageEl, clientX, clientY)` — const, line 458
- `const idx = block ? indexBySpan.get(block.spanId) : undefined` — const, line 459
- `const onMove = (event: MouseEvent)` — const, line 465
- `const state = sweepRef.current` — const, line 466
- `const onUp = ()` — const, line 472
- `const state = sweepRef.current` — const, line 473
- `const lo = Math.min(state.anchor, state.head)` — const, line 477
- `const hi = Math.max(state.anchor, state.head)` — const, line 478
- `const covered = blocks.slice(lo, hi + 1).filter(isSelectable)` — const, line 479
- `const nodes = covered.map((b)` — const, line 485
- `const display = nodes.map((n)` — const, line 486
- `const scroller = (()` — const, line 491
- `let node: HTMLElement | null = containerRef.current?.parentElement ?? null` — let, line 492
- `const style = window.getComputedStyle(node)` — const, line 494
- `const timer = window.setInterval(()` — const, line 500
- `const point = lastPointRef.current` — const, line 501
- `const rect = scroller.getBoundingClientRect()` — const, line 503
- `const zone = 48` — const, line 504
- `const delta = point.y < rect.top + zone ? -Math.ceil((rect.top + zone - point.y) / 3) : point.y > rect.bottom - zone ? Math.ceil((point.y - (rect.bottom - zone)) / 3) : 0` — const, line 505
- `const pdfPointFromClient = (pageEl: HTMLElement, clientX: number, clientY: number): [number, number] | null` — const, line 532
- `const widthPoints = Number(pageEl.dataset.widthPoints)` — const, line 533
- `const rect = pageEl.getBoundingClientRect()` — const, line 534
- `const scale = rect.width / widthPoints` — const, line 536
- `const x = Math.min(Math.max((clientX - rect.left) / scale, 0), widthPoints)` — const, line 537
- `const y = Math.min(Math.max((clientY - rect.top) / scale, 0), rect.height / scale)` — const, line 538
- `const blockForRect = useCallback( (page: number, rect: number[]): ReaderPdfBlockDto | null` — const, line 542
- `let best: ReaderPdfBlockDto | null = null` — let, line 544
- `let bestArea = 0` — let, line 545
- `const w = Math.min(rect[2], block.bbox[2]) - Math.max(rect[0], block.bbox[0])` — const, line 548
- `const h = Math.min(rect[3], block.bbox[3]) - Math.max(rect[1], block.bbox[1])` — const, line 549
- `const onMarqueeMouseDown = useCallback((event: React.MouseEvent): boolean` — const, line 560
- `const target = event.target as Node` — const, line 562
- `const pageEl = pageElFor(target)` — const, line 564
- `const point = pdfPointFromClient(pageEl, event.clientX, event.clientY)` — const, line 566
- `const page = Number(pageEl.dataset.pdfPage)` — const, line 572
- `const marqueeDrafting = marqueeDraft !== null` — const, line 581
- `const draftRect = (drag:` — const, line 584
- `const onMove = (event: MouseEvent)` — const, line 590
- `const drag = marqueeDragRef.current` — const, line 591
- `const point = pdfPointFromClient(drag.pageEl, event.clientX, event.clientY)` — const, line 593
- `const onUp = (event: MouseEvent)` — const, line 596
- `const drag = marqueeDragRef.current` — const, line 597
- `const point = pdfPointFromClient(drag.pageEl, event.clientX, event.clientY)` — const, line 601
- `const rect = draftRect(drag, point)` — const, line 603
- `const next = [...marqueeBoxesRef.current,` — const, line 605
- `const resolveMarquee = useCallback( (boxes: MarqueeBox[]): Array<` — const, line 623
- `const container = containerRef.current` — const, line 625
- `interface Gather` — interface, line 627
- `const gathered = new Map<string, Gather>()` — const, line 634
- `const entryFor = (block: ReaderPdfBlockDto): Gather` — const, line 635
- `let entry = gathered.get(block.spanId)` — let, line 636
- `const pages = [...new Set(boxes.map((b)` — const, line 649
- `let order = 0` — let, line 650
- `const pageBoxes = boxes.filter((b)` — const, line 652
- `const pageEl = container.querySelector(`[data-pdf-page="$` — const, line 653
- `const overlap = rectOverlap(rect, block.bbox)` — const, line 660
- `const widthPoints = Number(pageEl.dataset.widthPoints)` — const, line 668
- `const pageRect = pageEl.getBoundingClientRect()` — const, line 669
- `const layer = pageEl.querySelector(".textLayer")` — const, line 670
- `const scale = pageRect.width / widthPoints` — const, line 672
- `const walker = document.createTreeWalker(layer, NodeFilter.SHOW_TEXT)` — const, line 673
- `const text = node as Text` — const, line 675
- `const wordPattern = /\S+/g` — const, line 676
- `let match: RegExpExecArray | null` — let, line 677
- `const wordRange = document.createRange()` — const, line 679
- `const rects = Array.from(wordRange.getClientRects()).filter((r)` — const, line 682
- `const union = rects.reduce( (acc, r)` — const, line 684
- `const cx = (union[0] + union[2]) / 2` — const, line 693
- `const cy = (union[1] + union[3]) / 2` — const, line 694
- `const hit = pageBoxes.some( (rect)` — const, line 695
- `const block = blockForRect(page, union)` — const, line 701
- `const entry = entryFor(block)` — const, line 703
- `const commitMarquee = useCallback(()` — const, line 728
- `const boxes = marqueeBoxesRef.current` — const, line 729
- `const nodes = resolveMarquee(boxes)` — const, line 731
- `const display = nodes.map((n)` — const, line 736
- `const commitMarqueeRef = useRef(commitMarquee)` — const, line 739
- `const onKeyDown = (event: KeyboardEvent)` — const, line 747
- `const onKeyUp = (event: KeyboardEvent)` — const, line 751
- `const onBlur = ()` — const, line 757
- `const marqueeByPage = useMemo(()` — const, line 775
- `const map = new Map<number, number[][]>()` — const, line 776
- `const list = map.get(box.page) ?? []` — const, line 778
- `const onPaneMouseDown = useCallback( (event: React.MouseEvent)` — const, line 787
- `const resolveSelection = useCallback(():` — const, line 804
- `const selection = window.getSelection()` — const, line 809
- `const quote = selection.toString().replace(/\s+/g, " ").trim()` — const, line 811
- `const range = selection.getRangeAt(0)` — const, line 813
- `const root = range.commonAncestorContainer` — const, line 816
- `const textNodes: Node[] = []` — const, line 817
- `const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)` — const, line 821
- `const segments: Array<` — const, line 830
- `const bySpan = new Map<string,` — const, line 831
- `const append = (spanId: string, text: string)` — const, line 832
- `let segment = bySpan.get(spanId)` — let, line 833
- `const sub = document.createRange()` — const, line 842
- `const text = sub.toString().replace(/\s+/g, " ")` — const, line 846
- `const pageEl = pageElFor(node)` — const, line 848
- `const page = Number(pageEl.dataset.pdfPage)` — const, line 850
- `const widthPoints = Number(pageEl.dataset.widthPoints)` — const, line 851
- `const pageRect = pageEl.getBoundingClientRect()` — const, line 852
- `const scale = pageRect.width / widthPoints` — const, line 854
- `const overlaps = new Map<string, number>()` — const, line 855
- `const x0 = (rect.left - pageRect.left) / scale` — const, line 857
- `const x1 = (rect.right - pageRect.left) / scale` — const, line 858
- `const y0 = (rect.top - pageRect.top) / scale` — const, line 859
- `const y1 = (rect.bottom - pageRect.top) / scale` — const, line 860
- `const w = Math.min(x1, block.bbox[2]) - Math.max(x0, block.bbox[0])` — const, line 865
- `const h = Math.min(y1, block.bbox[3]) - Math.max(y0, block.bbox[1])` — const, line 866
- `const best = [...overlaps.entries()].sort((a, b)` — const, line 870
- `const nodes = segments .map((segment)` — const, line 877
- `const block = blockBySpan.get(segment.spanId)` — const, line 879
- `const primary = [...nodes].sort((a, b)` — const, line 891
- `const onMouseUp = useCallback(()` — const, line 895
- `const resolved = resolveSelection()` — const, line 896
- `const onContextMenu = useCallback( (event: React.MouseEvent)` — const, line 906
- `const resolved = resolveSelection()` — const, line 908
- `const pageEl = pageElFor(event.target as Node)` — const, line 923
- `const point = pageEl ? pdfPointFromClient(pageEl, event.clientX, event.clientY) : null` — const, line 924
- `const page = pageEl ? Number(pageEl.dataset.pdfPage) : null` — const, line 927
- `const onCommittedBox = point !== null && page !== null && marqueeBoxesRef.current.some( (box)` — const, line 928
- `const nodes = resolveMarquee(marqueeBoxesRef.current)` — const, line 937
- `const block = blockAtPoint(pageEl, event.clientX, event.clientY)` — const, line 951
- `const pageWidth = Math.max(320, containerWidth - 2) * zoom` — const, line 967
- `function ZoomButton(` — function, line 1064
- `function PdfPage(` — function, line 1089
- `const wrapperRef = useRef<HTMLDivElement | null>(null)` — const, line 1118
- `const canvasRef = useRef<HTMLCanvasElement | null>(null)` — const, line 1119
- `const textRef = useRef<HTMLDivElement | null>(null)` — const, line 1120
- `const renderedKeyRef = useRef<string | null>(null)` — const, line 1123
- `const node = wrapperRef.current` — const, line 1126
- `const observer = new IntersectionObserver( (entries)` — const, line 1128
- `const renderKey = `$` — const, line 1138
- `let cancelled = false` — let, line 1140
- `const page = await doc.getPage(pageIndex + 1)` — const, line 1143
- `const base = page.getViewport(` — const, line 1144
- `const scale = widthPx / base.width` — const, line 1145
- `const viewport = page.getViewport(` — const, line 1146
- `const canvas = canvasRef.current` — const, line 1147
- `const textDiv = textRef.current` — const, line 1148
- `const dpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 1150
- `const context = canvas.getContext("2d")` — const, line 1153
- `const textLayer = new pdfjs.TextLayer(` — const, line 1163
- `const textDiv = textRef.current` — const, line 1185
- `const query = findQuery.toLowerCase()` — const, line 1187
- `const hit = query.length > 0 && (span.textContent ?? "").toLowerCase().includes(query)` — const, line 1189
- `const aspect = geometry ? geometry.heightPoints / geometry.widthPoints : 1.294` — const, line 1194
- `const scale = geometry ? widthPx / geometry.widthPoints : 1` — const, line 1195
- `const color = TRAIL_COLORS[t.kind] ?? TRAIL_COLORS.other` — const, line 1216
- `const swept = sweepSpans?.has(b.spanId) ?? false` — const, line 1243
- `const selected = selectedSpans.has(b.spanId)` — const, line 1244
- `const active = activeSpan === b.spanId` — const, line 1245
- `const guided = guidanceSpans.has(b.spanId)` — const, line 1246
- `const border = swept ? `2px solid $` — const, line 1247
- `const background = swept ? "rgba(245, 166, 35, 0.20)" : selected ? "rgba(245, 166, 35, 0.13)" : active ? "rgba(245, 166, 35, 0.08)" : guided ? "rgba(90, 77, 138, 0.10)" : "transparent"` — const, line 1256

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `PdfReaderPane`, `PdfReaderPaneHandle`, `TagMenuRequest`; references `PdfReaderPane`, `PdfReaderPaneHandle`, `TagMenuRequest`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderPdfBlockDto`
- [[Reference/Desktop/TypeScript/components/RectUnionOverlay|src/components/RectUnionOverlay.tsx]] — import-or-re-export; imports `RectUnionOverlay`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export; imports `AnnotationTrail`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `pdfjs-dist`, `pdfjs-dist/build/pdf.worker.min.mjs?url`, `pdfjs-dist/web/pdf_viewer.css`, `react`

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

1. Modify [apps/learnloop-tauri/src/components/PdfReaderPane.tsx](../../../../../../apps/learnloop-tauri/src/components/PdfReaderPane.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

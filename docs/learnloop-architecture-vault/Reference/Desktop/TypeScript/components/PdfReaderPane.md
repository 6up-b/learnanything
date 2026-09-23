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
source_commit: "a679159b2a895789ac8568f7cfa50361df73b7f2"
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
| Source lines | 1332 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `a679159b2a895789ac8568f7cfa50361df73b7f2` |
| Commit timestamp | `2026-09-03T10:56:04-07:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]]

## Public API

- `export interface TagMenuRequest` — interface, line 80
- `export interface PdfReaderPaneHandle` — interface, line 92
- `export const PdfReaderPane = forwardRef<PdfReaderPaneHandle, PdfReaderPaneProps>(function PdfReaderPane(` — const, line 119

## Internal implementation anchors

- `interface PageGeometry` — interface, line 35
- `const TRAIL_COLORS: Record<string,` — const, line 42
- `const FURNITURE_TYPES = new Set(["PageHeader", "PageFooter", "TableOfContents"])` — const, line 49
- `function isSelectable(block: ReaderPdfBlockDto): boolean` — function, line 51
- `interface MarqueeBox` — interface, line 58
- `const MARQUEE_MIN_EXTENT_PTS = 4` — const, line 64
- `function rectOverlap(a: number[], b: number[]): number` — function, line 66
- `const w = Math.min(a[2], b[2]) - Math.max(a[0], b[0])` — const, line 67
- `const h = Math.min(a[3], b[3]) - Math.max(a[1], b[1])` — const, line 68
- `function rectArea(r: number[]): number` — function, line 72
- `const EMPTY_SPANS = new Set<string>()` — const, line 76
- `interface PdfReaderPaneProps` — interface, line 96
- `interface FindMatch` — interface, line 114
- `const containerRef = useRef<HTMLDivElement | null>(null)` — const, line 126
- `const pageTextsRef = useRef<Map<number, string>>(new Map())` — const, line 134
- `const findInputRef = useRef<HTMLInputElement | null>(null)` — const, line 135
- `const clampZoom = (value: number)` — const, line 137
- `const zoomIn = useCallback(()` — const, line 138
- `const zoomOut = useCallback(()` — const, line 139
- `const openFind = useCallback(()` — const, line 141
- `const closeFind = useCallback(()` — const, line 145
- `const coveredPages = useMemo( ()` — const, line 152
- `const blocksByPage = useMemo(()` — const, line 156
- `const map = new Map<number, ReaderPdfBlockDto[]>()` — const, line 157
- `const list = map.get(block.page) ?? []` — const, line 159
- `const trailsByPage = useMemo(()` — const, line 165
- `const map = new Map<number, AnnotationTrail[]>()` — const, line 166
- `const list = map.get(trail.page) ?? []` — const, line 168
- `let cancelled = false` — let, line 179
- `const node = containerRef.current` — const, line 196
- `const observer = new ResizeObserver(()` — const, line 198
- `let cancelled = false` — let, line 211
- `const timer = setTimeout(async ()` — const, line 212
- `const query = findQuery.trim().toLowerCase()` — const, line 213
- `const found: FindMatch[] = []` — const, line 214
- `let text = pageTextsRef.current.get(page)` — let, line 216
- `const pdfPage = await doc.getPage(page + 1)` — const, line 219
- `const content = await pdfPage.getTextContent()` — const, line 220
- `let from = 0` — let, line 232
- `let ordinal = 0` — let, line 233
- `const at = text.indexOf(query, from)` — const, line 235
- `const scrollToMatch = useCallback((match: FindMatch)` — const, line 253
- `const pageEl = containerRef.current?.querySelector(`[data-pdf-page="$` — const, line 254
- `const hits = pageEl.querySelectorAll(".ll-find-hit")` — const, line 257
- `const target = hits[Math.min(match.ordinal, Math.max(0, hits.length - 1))]` — const, line 258
- `const current = matches[matchIdx]` — const, line 263
- `const gotoMatch = useCallback( (delta: number)` — const, line 267
- `const handler = (event: KeyboardEvent)` — const, line 276
- `const modifier = event.ctrlKey || event.metaKey` — const, line 277
- `const editing = event.target instanceof HTMLElement && ["INPUT", "TEXTAREA"].includes(event.target.tagName)` — const, line 283
- `const node = containerRef.current` — const, line 302
- `const onWheel = (event: WheelEvent)` — const, line 304
- `const scrollToSegment = useCallback((page: number, spanId?: string | null)` — const, line 313
- `const pageEl = containerRef.current?.querySelector(`[data-pdf-page="$` — const, line 314
- `const target = spanId ? pageEl.querySelector(`[data-span-id="$` — const, line 318
- `const blockAtPoint = useCallback( (pageEl: HTMLElement, clientX: number, clientY: number): ReaderPdfBlockDto | null` — const, line 325
- `const page = Number(pageEl.dataset.pdfPage)` — const, line 327
- `const widthPoints = Number(pageEl.dataset.widthPoints)` — const, line 328
- `const rect = pageEl.getBoundingClientRect()` — const, line 329
- `const scale = rect.width / widthPoints` — const, line 331
- `const x = (clientX - rect.left) / scale` — const, line 332
- `const y = (clientY - rect.top) / scale` — const, line 333
- `const candidates = (blocksByPage.get(page) ?? []).filter( (b)` — const, line 334
- `const pageElFor = (node: Node | null): HTMLElement | null` — const, line 348
- `let current: Node | null = node` — let, line 349
- `const indexBySpan = useMemo(()` — const, line 360
- `const blockBySpan = useMemo(()` — const, line 361
- `const blockNearPoint = useCallback( (pageEl: HTMLElement, clientX: number, clientY: number): ReaderPdfBlockDto | null` — const, line 365
- `const direct = blockAtPoint(pageEl, clientX, clientY)` — const, line 367
- `const page = Number(pageEl.dataset.pdfPage)` — const, line 369
- `const widthPoints = Number(pageEl.dataset.widthPoints)` — const, line 370
- `const rect = pageEl.getBoundingClientRect()` — const, line 371
- `const scale = rect.width / widthPoints` — const, line 373
- `const x = (clientX - rect.left) / scale` — const, line 374
- `const y = (clientY - rect.top) / scale` — const, line 375
- `let best: ReaderPdfBlockDto | null = null` — let, line 376
- `let bestDistance = Infinity` — let, line 377
- `const dx = x < block.bbox[0] ? block.bbox[0] - x : x > block.bbox[2] ? x - block.bbox[2] : 0` — const, line 380
- `const dy = y < block.bbox[1] ? block.bbox[1] - y : y > block.bbox[3] ? y - block.bbox[3] : 0` — const, line 381
- `const distance = dy * 4 + dx` — const, line 382
- `const sweepRef = useRef<` — const, line 394
- `const lastPointRef = useRef<` — const, line 395
- `const sweeping = sweep !== null` — const, line 396
- `const marqueeBoxesRef = useRef<MarqueeBox[]>([])` — const, line 403
- `const marqueeDragRef = useRef<` — const, line 404
- `const clearMarquee = useCallback(()` — const, line 405
- `const sweepSpans = useMemo(()` — const, line 412
- `const lo = Math.min(sweep.anchor, sweep.head)` — const, line 414
- `const hi = Math.max(sweep.anchor, sweep.head)` — const, line 415
- `const onSweepMouseDown = useCallback( (event: React.MouseEvent)` — const, line 419
- `const target = event.target as Node` — const, line 425
- `const pageEl = pageElFor(target)` — const, line 427
- `const block = blockNearPoint(pageEl, event.clientX, event.clientY)` — const, line 429
- `const idx = block ? indexBySpan.get(block.spanId) : undefined` — const, line 430
- `const updateHead = (clientX: number, clientY: number)` — const, line 447
- `const state = sweepRef.current` — const, line 448
- `const pageEl = pageElFor(document.elementFromPoint(clientX, clientY))` — const, line 450
- `const block = blockNearPoint(pageEl, clientX, clientY)` — const, line 452
- `const idx = block ? indexBySpan.get(block.spanId) : undefined` — const, line 453
- `const onMove = (event: MouseEvent)` — const, line 459
- `const state = sweepRef.current` — const, line 460
- `const onUp = ()` — const, line 466
- `const state = sweepRef.current` — const, line 467
- `const lo = Math.min(state.anchor, state.head)` — const, line 471
- `const hi = Math.max(state.anchor, state.head)` — const, line 472
- `const covered = blocks.slice(lo, hi + 1).filter(isSelectable)` — const, line 473
- `const nodes = covered.map((b)` — const, line 479
- `const display = nodes.map((n)` — const, line 480
- `const scroller = (()` — const, line 485
- `let node: HTMLElement | null = containerRef.current?.parentElement ?? null` — let, line 486
- `const style = window.getComputedStyle(node)` — const, line 488
- `const timer = window.setInterval(()` — const, line 494
- `const point = lastPointRef.current` — const, line 495
- `const rect = scroller.getBoundingClientRect()` — const, line 497
- `const zone = 48` — const, line 498
- `const delta = point.y < rect.top + zone ? -Math.ceil((rect.top + zone - point.y) / 3) : point.y > rect.bottom - zone ? Math.ceil((point.y - (rect.bottom - zone)) / 3) : 0` — const, line 499
- `const pdfPointFromClient = (pageEl: HTMLElement, clientX: number, clientY: number): [number, number] | null` — const, line 526
- `const widthPoints = Number(pageEl.dataset.widthPoints)` — const, line 527
- `const rect = pageEl.getBoundingClientRect()` — const, line 528
- `const scale = rect.width / widthPoints` — const, line 530
- `const x = Math.min(Math.max((clientX - rect.left) / scale, 0), widthPoints)` — const, line 531
- `const y = Math.min(Math.max((clientY - rect.top) / scale, 0), rect.height / scale)` — const, line 532
- `const blockForRect = useCallback( (page: number, rect: number[]): ReaderPdfBlockDto | null` — const, line 536
- `let best: ReaderPdfBlockDto | null = null` — let, line 538
- `let bestArea = 0` — let, line 539
- `const w = Math.min(rect[2], block.bbox[2]) - Math.max(rect[0], block.bbox[0])` — const, line 542
- `const h = Math.min(rect[3], block.bbox[3]) - Math.max(rect[1], block.bbox[1])` — const, line 543
- `const onMarqueeMouseDown = useCallback((event: React.MouseEvent): boolean` — const, line 554
- `const target = event.target as Node` — const, line 556
- `const pageEl = pageElFor(target)` — const, line 558
- `const point = pdfPointFromClient(pageEl, event.clientX, event.clientY)` — const, line 560
- `const page = Number(pageEl.dataset.pdfPage)` — const, line 566
- `const marqueeDrafting = marqueeDraft !== null` — const, line 575
- `const draftRect = (drag:` — const, line 578
- `const onMove = (event: MouseEvent)` — const, line 584
- `const drag = marqueeDragRef.current` — const, line 585
- `const point = pdfPointFromClient(drag.pageEl, event.clientX, event.clientY)` — const, line 587
- `const onUp = (event: MouseEvent)` — const, line 590
- `const drag = marqueeDragRef.current` — const, line 591
- `const point = pdfPointFromClient(drag.pageEl, event.clientX, event.clientY)` — const, line 595
- `const rect = draftRect(drag, point)` — const, line 597
- `const next = [...marqueeBoxesRef.current,` — const, line 599
- `const resolveMarquee = useCallback( (boxes: MarqueeBox[]): Array<` — const, line 617
- `const container = containerRef.current` — const, line 619
- `interface Gather` — interface, line 621
- `const gathered = new Map<string, Gather>()` — const, line 628
- `const entryFor = (block: ReaderPdfBlockDto): Gather` — const, line 629
- `let entry = gathered.get(block.spanId)` — let, line 630
- `const pages = [...new Set(boxes.map((b)` — const, line 643
- `let order = 0` — let, line 644
- `const pageBoxes = boxes.filter((b)` — const, line 646
- `const pageEl = container.querySelector(`[data-pdf-page="$` — const, line 647
- `const overlap = rectOverlap(rect, block.bbox)` — const, line 654
- `const widthPoints = Number(pageEl.dataset.widthPoints)` — const, line 662
- `const pageRect = pageEl.getBoundingClientRect()` — const, line 663
- `const layer = pageEl.querySelector(".textLayer")` — const, line 664
- `const scale = pageRect.width / widthPoints` — const, line 666
- `const walker = document.createTreeWalker(layer, NodeFilter.SHOW_TEXT)` — const, line 667
- `const text = node as Text` — const, line 669
- `const wordPattern = /\S+/g` — const, line 670
- `let match: RegExpExecArray | null` — let, line 671
- `const wordRange = document.createRange()` — const, line 673
- `const rects = Array.from(wordRange.getClientRects()).filter((r)` — const, line 676
- `const union = rects.reduce( (acc, r)` — const, line 678
- `const cx = (union[0] + union[2]) / 2` — const, line 687
- `const cy = (union[1] + union[3]) / 2` — const, line 688
- `const hit = pageBoxes.some( (rect)` — const, line 689
- `const block = blockForRect(page, union)` — const, line 695
- `const entry = entryFor(block)` — const, line 697
- `const commitMarquee = useCallback(()` — const, line 722
- `const boxes = marqueeBoxesRef.current` — const, line 723
- `const nodes = resolveMarquee(boxes)` — const, line 725
- `const display = nodes.map((n)` — const, line 730
- `const commitMarqueeRef = useRef(commitMarquee)` — const, line 733
- `const onKeyDown = (event: KeyboardEvent)` — const, line 741
- `const onKeyUp = (event: KeyboardEvent)` — const, line 745
- `const onBlur = ()` — const, line 751
- `const marqueeByPage = useMemo(()` — const, line 769
- `const map = new Map<number, number[][]>()` — const, line 770
- `const list = map.get(box.page) ?? []` — const, line 772
- `const onPaneMouseDown = useCallback( (event: React.MouseEvent)` — const, line 781
- `const resolveSelection = useCallback(():` — const, line 798
- `const selection = window.getSelection()` — const, line 803
- `const quote = selection.toString().replace(/\s+/g, " ").trim()` — const, line 805
- `const range = selection.getRangeAt(0)` — const, line 807
- `const root = range.commonAncestorContainer` — const, line 810
- `const textNodes: Node[] = []` — const, line 811
- `const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)` — const, line 815
- `const segments: Array<` — const, line 824
- `const bySpan = new Map<string,` — const, line 825
- `const append = (spanId: string, text: string)` — const, line 826
- `let segment = bySpan.get(spanId)` — let, line 827
- `const sub = document.createRange()` — const, line 836
- `const text = sub.toString().replace(/\s+/g, " ")` — const, line 840
- `const pageEl = pageElFor(node)` — const, line 842
- `const page = Number(pageEl.dataset.pdfPage)` — const, line 844
- `const widthPoints = Number(pageEl.dataset.widthPoints)` — const, line 845
- `const pageRect = pageEl.getBoundingClientRect()` — const, line 846
- `const scale = pageRect.width / widthPoints` — const, line 848
- `const overlaps = new Map<string, number>()` — const, line 849
- `const x0 = (rect.left - pageRect.left) / scale` — const, line 851
- `const x1 = (rect.right - pageRect.left) / scale` — const, line 852
- `const y0 = (rect.top - pageRect.top) / scale` — const, line 853
- `const y1 = (rect.bottom - pageRect.top) / scale` — const, line 854
- `const w = Math.min(x1, block.bbox[2]) - Math.max(x0, block.bbox[0])` — const, line 859
- `const h = Math.min(y1, block.bbox[3]) - Math.max(y0, block.bbox[1])` — const, line 860
- `const best = [...overlaps.entries()].sort((a, b)` — const, line 864
- `const nodes = segments .map((segment)` — const, line 871
- `const block = blockBySpan.get(segment.spanId)` — const, line 873
- `const primary = [...nodes].sort((a, b)` — const, line 885
- `const onMouseUp = useCallback(()` — const, line 889
- `const resolved = resolveSelection()` — const, line 890
- `const onContextMenu = useCallback( (event: React.MouseEvent)` — const, line 900
- `const resolved = resolveSelection()` — const, line 902
- `const pageEl = pageElFor(event.target as Node)` — const, line 917
- `const point = pageEl ? pdfPointFromClient(pageEl, event.clientX, event.clientY) : null` — const, line 918
- `const page = pageEl ? Number(pageEl.dataset.pdfPage) : null` — const, line 921
- `const onCommittedBox = point !== null && page !== null && marqueeBoxesRef.current.some( (box)` — const, line 922
- `const nodes = resolveMarquee(marqueeBoxesRef.current)` — const, line 931
- `const block = blockAtPoint(pageEl, event.clientX, event.clientY)` — const, line 945
- `const pageWidth = Math.max(320, containerWidth - 2) * zoom` — const, line 961
- `function ZoomButton(` — function, line 1058
- `function PdfPage(` — function, line 1083
- `const wrapperRef = useRef<HTMLDivElement | null>(null)` — const, line 1112
- `const canvasRef = useRef<HTMLCanvasElement | null>(null)` — const, line 1113
- `const textRef = useRef<HTMLDivElement | null>(null)` — const, line 1114
- `const renderedKeyRef = useRef<string | null>(null)` — const, line 1117
- `const node = wrapperRef.current` — const, line 1120
- `const observer = new IntersectionObserver( (entries)` — const, line 1122
- `const renderKey = `$` — const, line 1132
- `let cancelled = false` — let, line 1134
- `const page = await doc.getPage(pageIndex + 1)` — const, line 1137
- `const base = page.getViewport(` — const, line 1138
- `const scale = widthPx / base.width` — const, line 1139
- `const viewport = page.getViewport(` — const, line 1140
- `const canvas = canvasRef.current` — const, line 1141
- `const textDiv = textRef.current` — const, line 1142
- `const dpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 1144
- `const context = canvas.getContext("2d")` — const, line 1147
- `const textLayer = new pdfjs.TextLayer(` — const, line 1157
- `const textDiv = textRef.current` — const, line 1179
- `const query = findQuery.toLowerCase()` — const, line 1181
- `const hit = query.length > 0 && (span.textContent ?? "").toLowerCase().includes(query)` — const, line 1183
- `const aspect = geometry ? geometry.heightPoints / geometry.widthPoints : 1.294` — const, line 1188
- `const scale = geometry ? widthPx / geometry.widthPoints : 1` — const, line 1189
- `const color = TRAIL_COLORS[t.kind] ?? TRAIL_COLORS.other` — const, line 1210
- `const swept = sweepSpans?.has(b.spanId) ?? false` — const, line 1237
- `const selected = selectedSpans.has(b.spanId)` — const, line 1238
- `const active = activeSpan === b.spanId` — const, line 1239
- `const guided = guidanceSpans.has(b.spanId)` — const, line 1240
- `const border = swept ? `2px solid $` — const, line 1241
- `const background = swept ? "rgba(245, 166, 35, 0.20)" : selected ? "rgba(245, 166, 35, 0.13)" : active ? "rgba(245, 166, 35, 0.08)" : guided ? "rgba(90, 77, 138, 0.10)" : "transparent"` — const, line 1250

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `PdfReaderPane`, `PdfReaderPaneHandle`, `TagMenuRequest`; references `PdfReaderPane`, `PdfReaderPaneHandle`, `TagMenuRequest`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderPdfBlockDto`
- [[Reference/Desktop/TypeScript/components/RectUnionOverlay|src/components/RectUnionOverlay.tsx]] — import-or-re-export; imports `RectUnionOverlay`
- [[Reference/Desktop/TypeScript/components/pdfDocumentCache|src/components/pdfDocumentCache.ts]] — import-or-re-export; imports `acquirePdfDocument`
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
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/PdfReaderPane.tsx](../../../../../../apps/learnloop-tauri/src/components/PdfReaderPane.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

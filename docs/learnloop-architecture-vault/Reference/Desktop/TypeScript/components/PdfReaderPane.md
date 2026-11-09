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
| Source lines | 1425 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]]

## Public API

- `export interface TagMenuRequest` — interface, line 63
- `export type PassageAlign = "center" | "start"` — type, line 76
- `export interface PdfReaderPaneHandle` — interface, line 79
- `export const PdfReaderPane = forwardRef<PdfReaderPaneHandle, PdfReaderPaneProps>(function PdfReaderPane(` — const, line 162

## Internal implementation anchors

- `interface PageGeometry` — interface, line 44
- `const NO_HIGHLIGHTS: PdfHighlight[] = []` — const, line 49
- `const NO_BOXES: Box[] = []` — const, line 50
- `const NO_PAGE_HIGHLIGHTS: HighlightOnPage[] = []` — const, line 51
- `const NO_MARQUEE: number[][] = []` — const, line 52
- `const NEAR_VIEW_MARGIN = "1200px 0px"` — const, line 56
- `const BETWEEN_PAGES_PX = 48` — const, line 59
- `const PASSAGE_TOP_MARGIN_PX = 56` — const, line 88
- `function alignPassage(box: HTMLElement, align: PassageAlign, smooth: boolean)` — function, line 90
- `interface PdfReaderPaneProps` — interface, line 95
- `interface FindMatch` — interface, line 136
- `function sameBoxes(a: readonly Box[], b: readonly Box[]): boolean` — function, line 142
- `const x = a[i]` — const, line 146
- `const y = b[i]` — const, line 147
- `function samePageHighlights(a: readonly HighlightOnPage[], b: readonly HighlightOnPage[]): boolean` — function, line 153
- `const FIGURE_BLOCK_TYPES = new Set(["Figure", "FigureGroup", "Picture", "PictureGroup"])` — const, line 160
- `const containerRef = useRef<HTMLDivElement | null>(null)` — const, line 188
- `const pageTextsRef = useRef<Map<number, string>>(new Map())` — const, line 196
- `const findInputRef = useRef<HTMLInputElement | null>(null)` — const, line 197
- `const clampZoom = (value: number)` — const, line 199
- `const zoomIn = useCallback(()` — const, line 200
- `const zoomOut = useCallback(()` — const, line 201
- `const openFind = useCallback(()` — const, line 203
- `const closeFind = useCallback(()` — const, line 207
- `const coveredPages = useMemo(()` — const, line 214
- `const blocksByPage = useMemo(()` — const, line 215
- `const map = new Map<number, ReaderPdfBlockDto[]>()` — const, line 216
- `const list = map.get(block.page) ?? []` — const, line 218
- `let cancelled = false` — let, line 229
- `const hasBoxes = blocks.length > 0` — const, line 252
- `let cancelled = false` — let, line 255
- `const base = (await doc.getPage(page + 1)).getViewport(` — const, line 258
- `const sizes = pageSizes && pageSizes.doc === doc ? pageSizes.sizes : null` — const, line 272
- `const node = containerRef.current` — const, line 275
- `const observer = new ResizeObserver(()` — const, line 277
- `let cancelled = false` — let, line 290
- `const timer = setTimeout(async ()` — const, line 291
- `const query = findQuery.trim().toLowerCase()` — const, line 292
- `const found: FindMatch[] = []` — const, line 293
- `let text = pageTextsRef.current.get(page)` — let, line 295
- `const pdfPage = await doc.getPage(page + 1)` — const, line 298
- `const content = await pdfPage.getTextContent()` — const, line 299
- `let from = 0` — let, line 311
- `let ordinal = 0` — let, line 312
- `const at = text.indexOf(query, from)` — const, line 314
- `const scrollToMatch = useCallback((match: FindMatch)` — const, line 332
- `const pageEl = containerRef.current?.querySelector(`[data-pdf-page="$` — const, line 333
- `const hits = pageEl.querySelectorAll(".ll-find-hit")` — const, line 336
- `const target = hits[Math.min(match.ordinal, Math.max(0, hits.length - 1))]` — const, line 337
- `const current = matches[matchIdx]` — const, line 342
- `const gotoMatch = useCallback( (delta: number)` — const, line 346
- `const handler = (event: KeyboardEvent)` — const, line 355
- `const modifier = event.ctrlKey || event.metaKey` — const, line 357
- `const editing = event.target instanceof HTMLElement && ["INPUT", "TEXTAREA"].includes(event.target.tagName)` — const, line 363
- `const node = containerRef.current` — const, line 382
- `const onWheel = (event: WheelEvent)` — const, line 384
- `const onTouch = ()` — const, line 393
- `const pendingTargetRef = useRef<` — const, line 412
- `const applyPageScroll = useCallback((page: number, offset: number): boolean` — const, line 421
- `const container = containerRef.current` — const, line 422
- `const pageEl = container?.querySelector(`[data-pdf-page="$` — const, line 423
- `const pageRect = pageEl.getBoundingClientRect()` — const, line 425
- `let scroller: HTMLElement | null = container?.parentElement ?? null` — let, line 427
- `const passageBox = useCallback((page: number, spanId: string): HTMLElement | null` — const, line 439
- `const pageEl = containerRef.current?.querySelector(`[data-pdf-page="$` — const, line 440
- `const box = Array.from(pageEl.querySelectorAll<HTMLElement>("[data-span-id]")).find( (element)` — const, line 442
- `const applyTarget = useCallback( (target:` — const, line 447
- `const box = passageBox(target.page, target.spanId)` — const, line 450
- `const keepTarget = useCallback( (page: number, offset: number, spanId: string | null, align: PassageAlign = "center")` — const, line 461
- `const target =` — const, line 463
- `const scrollToSegment = useCallback( (page: number, spanId?: string | null, align: PassageAlign = "center")` — const, line 474
- `const box = spanId ? passageBox(page, spanId) : null` — const, line 477
- `const scrollToPage = useCallback( (page: number, offset = 0)` — const, line 489
- `const timer = window.setInterval(()` — const, line 495
- `const pending = pendingTargetRef.current` — const, line 496
- `const model = useMemo(()` — const, line 515
- `const onPageText = useCallback( (page: number, items: readonly GlyphItem[], transform: readonly number[], styles?: TextStyles | null)` — const, line 517
- `const onPageGlyphs = useCallback( (page: number, words: readonly GlyphWord[])` — const, line 527
- `const nearPagesRef = useRef<ReadonlySet<number>>(nearPages)` — const, line 538
- `const pageEls = useRef(new Map<number, HTMLElement>())` — const, line 540
- `const registerPage = useCallback((page: number, element: HTMLElement | null)` — const, line 541
- `const onNearChange = useCallback((page: number, near: boolean)` — const, line 545
- `const next = new Set(current)` — const, line 548
- `const pointAt = useCallback((clientX: number, clientY: number): PagePoint | null` — const, line 557
- `const near = nearPagesRef.current` — const, line 558
- `const candidates = near.size ? [...near] : [...pageEls.current.keys()]` — const, line 559
- `let best:` — let, line 560
- `const element = pageEls.current.get(page)` — const, line 562
- `const rect = element.getBoundingClientRect()` — const, line 564
- `const distance = clientY < rect.top ? rect.top - clientY : clientY > rect.bottom ? clientY - rect.bottom : 0` — const, line 566
- `const widthPoints = Number(best.element.dataset.widthPoints)` — const, line 570
- `const scale = best.rect.width / widthPoints` — const, line 572
- `const placed = useMemo(()` — const, line 581
- `const details = useMemo(()` — const, line 582
- `const activeId = activeHighlight?.id ?? null` — const, line 587
- `const onHighlightClick = useCallback((id: string | null, point?: PagePoint)` — const, line 593
- `const onHighlightFocus = useCallback((id: string | null, page: number)` — const, line 596
- `const pageHighlightsRef = useRef(new Map<number, HighlightOnPage[]>())` — const, line 602
- `const pageHighlights = useMemo(()` — const, line 603
- `const next = new Map<number, HighlightOnPage[]>()` — const, line 605
- `const fresh = highlightsOnPage(model, placed, page)` — const, line 607
- `const previous = pageHighlightsRef.current.get(page)` — const, line 608
- `const highlightAtPoint = useCallback( (point: PagePoint): string | null` — const, line 615
- `const firstShownPage = useCallback((): number | null` — const, line 623
- `const top = containerRef.current?.parentElement?.getBoundingClientRect().top ?? 0` — const, line 624
- `let best:` — let, line 625
- `const rect = pageEls.current.get(page)?.getBoundingClientRect()` — const, line 627
- `const revealBlock = useCallback( (index: number)` — const, line 635
- `const block = model.blocks[index]` — const, line 637
- `const box = passageBox(block.page, block.spanId)` — const, line 639
- `const regionAt = useCallback( (box:` — const, line 648
- `const cx = (box.rect[0] + box.rect[2]) / 2` — const, line 651
- `const cy = (box.rect[1] + box.rect[3]) / 2` — const, line 652
- `const figure = blocks.find((block)` — const, line 653
- `const text = figure?.text ?? ""` — const, line 656
- `const sel = usePdfSelection(` — const, line 662
- `const selectionRectsRef = useRef(new Map<number, Box[]>())` — const, line 679
- `const selectionRects = useMemo(()` — const, line 680
- `const next = new Map<number, Box[]>()` — const, line 682
- `const fresh = rangeRects(model, sel.painted, page)` — const, line 685
- `const previous = selectionRectsRef.current.get(page)` — const, line 687
- `const framedSpan = useMemo(()` — const, line 697
- `const block = model.blockIndex(activeSpan)` — const, line 699
- `const covered = sel.painted.some((range)` — const, line 701
- `const lo = Math.min(range.anchor.block, range.head.block)` — const, line 702
- `const hi = Math.max(range.anchor.block, range.head.block)` — const, line 703
- `const caret = useMemo(():` — const, line 709
- `const box = model.geometry(sel.caret.block).boxes[sel.caret.unit]?.[0]` — const, line 712
- `const marqueeByPage = useMemo(()` — const, line 716
- `const map = new Map<number, number[][]>()` — const, line 717
- `const list = map.get(box.page) ?? []` — const, line 719
- `const onPagesMouseMove = useCallback( (event: React.MouseEvent)` — const, line 729
- `const target = event.target as HTMLElement` — const, line 732
- `const point = target.closest?.("[data-pdf-page]") ? pointAt(event.clientX, event.clientY) : null` — const, line 734
- `const hovered = point ? highlightAtPoint(point) : null` — const, line 735
- `let next = "default"` — let, line 737
- `const block = blockAt(model, point.page, point.x, point.y)` — const, line 740
- `const inside = block !== null && (()` — const, line 741
- `const highlightActions = useRef(` — const, line 754
- `const removeHighlight = useCallback((id: string)` — const, line 756
- `const openHighlight = useCallback((id: string)` — const, line 763
- `const onPagesKeyDown = useCallback( (event: React.KeyboardEvent)` — const, line 765
- `const target = event.target as HTMLElement` — const, line 767
- `const editing = target.isContentEditable || Boolean(target.closest?.("input, textarea, select"))` — const, line 768
- `const onContextMenu = useCallback( (event: React.MouseEvent)` — const, line 793
- `const target = event.target as HTMLElement` — const, line 795
- `const point = pointAt(event.clientX, event.clientY)` — const, line 797
- `const under = sel.selectionUnder(point)` — const, line 799
- `const block = blockAt(model, point.page, point.x, point.y)` — const, line 805
- `const reportedWidth = Math.max(320, containerWidth - 2) * zoom` — const, line 818
- `const pages = coveredPages.flatMap((page, index)` — const, line 821
- `const size = sizes.get(page)` — const, line 822
- `const pageWidth = Math.max(320, containerWidth - 2) * zoom` — const, line 838
- `const busy = sel.pressing || sel.sweeping` — const, line 839
- `const onPage = pageHighlights.get(page) ?? NO_PAGE_HIGHLIGHTS` — const, line 915
- `const NO_BLOCKS: ReaderPdfBlockDto[] = []` — const, line 962
- `const VISUALLY_HIDDEN =` — const, line 964
- `function ZoomButton(` — function, line 973
- `const FONT_WAIT_MS = 3_000` — const, line 999
- `async function paintedWords( page:` — function, line 1004
- `const ops = (pdfjs as` — const, line 1009
- `const annotationMode = (pdfjs as` — const, line 1011
- `const opList = await page.getOperatorList(annotationMode === undefined ? undefined :` — const, line 1012
- `const objects = page.commonObjs as |` — const, line 1013
- `const fonts = new Map<string, PdfFontInfo | null>()` — const, line 1016
- `const name = String((opList.argsArray[index] as unknown[] | undefined)?.[0] ?? "")` — const, line 1019
- `let font: unknown = null` — let, line 1021
- `interface ActiveHighlight` — interface, line 1040
- `function isGlyphItem(item: unknown): item is GlyphItem` — function, line 1046
- `function isCancelled(error: unknown): boolean` — function, line 1050
- `interface PdfPageProps` — interface, line 1054
- `const PdfPage = memo(function PdfPage(` — const, line 1087
- `const wrapperRef = useRef<HTMLDivElement | null>(null)` — const, line 1118
- `const canvasRef = useRef<HTMLCanvasElement | null>(null)` — const, line 1119
- `const textRef = useRef<HTMLDivElement | null>(null)` — const, line 1120
- `const renderedKeyRef = useRef<string | null>(null)` — const, line 1126
- `const setWrapper = useCallback( (element: HTMLDivElement | null)` — const, line 1128
- `const node = wrapperRef.current` — const, line 1138
- `const observer = new IntersectionObserver( (entries)` — const, line 1140
- `const renderKey = `$` — const, line 1154
- `let cancelled = false` — let, line 1156
- `let task:` — let, line 1157
- `const page = await doc.getPage(pageIndex + 1)` — const, line 1160
- `const base = page.getViewport(` — const, line 1161
- `let content: Awaited<ReturnType<typeof page.getTextContent>> | null = null` — let, line 1164
- `const items: GlyphItem[] = []` — const, line 1173
- `const scale = widthPx / base.width` — const, line 1180
- `const viewport = page.getViewport(` — const, line 1181
- `const canvas = canvasRef.current` — const, line 1182
- `const textDiv = textRef.current` — const, line 1183
- `const dpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 1185
- `const context = canvas.getContext("2d")` — const, line 1188
- `const textLayer = new pdfjs.TextLayer(` — const, line 1199
- `const words = await paintedWords(page, base.transform)` — const, line 1222
- `const wasDrawn = renderedKeyRef.current !== null` — const, line 1243
- `const canvas = canvasRef.current` — const, line 1244
- `const textDiv = textRef.current` — const, line 1266
- `const query = findQuery.toLowerCase()` — const, line 1268
- `const hit = query.length > 0 && (span.textContent ?? "").toLowerCase().includes(query)` — const, line 1270
- `const known = measured ?? size` — const, line 1277
- `const aspect = known ? known.heightPoints / known.widthPoints : 1.294` — const, line 1278
- `const scale = known ? widthPx / known.widthPoints : 1` — const, line 1279
- `const active = activeSpan === b.spanId` — const, line 1303
- `const guided = guidanceSpans.has(b.spanId)` — const, line 1304
- `const covered = Boolean(coveredSpans?.has(b.spanId))` — const, line 1307

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `PdfReaderPane`, `PdfReaderPaneHandle`, `TagMenuRequest`; references `PdfReaderPane`, `PdfReaderPaneHandle`, `TagMenuRequest`
- [[Reference/Desktop/TypeScript/screens/reader/GuideRail|src/screens/reader/GuideRail.tsx]] — import-or-re-export: `PassageAlign`; references `PassageAlign`
- [[Reference/Desktop/TypeScript/screens/reader/PreparingView|src/screens/reader/PreparingView.tsx]] — import-or-re-export: `PdfReaderPane`; references `PdfReaderPane`
- [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]] — import-or-re-export: `TagMenuRequest`; references `TagMenuRequest`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `PassageAlign`; references `PassageAlign`
- [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]] — import-or-re-export: `PassageAlign`, `PdfReaderPaneHandle`; references `PassageAlign`, `PdfReaderPaneHandle`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderPdfBlockDto`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/pdfDocumentCache|src/components/pdfDocumentCache.ts]] — import-or-re-export; imports `acquirePdfDocument`
- [[Reference/Desktop/TypeScript/components/pdfPages|src/components/pdfPages.ts]] — import-or-re-export; imports `pagesLeftOutLabel`, `pagesShownLabel`, `pagesToShow`
- [[Reference/Desktop/TypeScript/components/pdfSelection/PdfSelectionLayer|src/components/pdfSelection/PdfSelectionLayer.tsx]] — import-or-re-export; imports `PdfSelectionLayer`
- [[Reference/Desktop/TypeScript/components/pdfSelection/geometry|src/components/pdfSelection/geometry.ts]] — import-or-re-export; imports `PdfFontInfo`, `operatorWords`
- [[Reference/Desktop/TypeScript/components/pdfSelection/highlights|src/components/pdfSelection/highlights.ts]] — import-or-re-export; imports `HighlightOnPage`, `PdfHighlight`, `highlightAt`, `highlightsOnPage`, `placeHighlights`
- [[Reference/Desktop/TypeScript/components/pdfSelection/model|src/components/pdfSelection/model.ts]] — import-or-re-export; imports `Box`, `GlyphItem`, `GlyphWord`, `SelectionModel`, `SelectionPayload`, `TextStyles`, `blockAt`, `rangeRects`
- [[Reference/Desktop/TypeScript/components/pdfSelection/usePdfSelection|src/components/pdfSelection/usePdfSelection.ts]] — import-or-re-export; imports `HeldSelection`, `PagePoint`, `usePdfSelection`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/screens/reader/cues|src/screens/reader/cues.ts]] — import-or-re-export; imports `PdfPageLayout`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `pdfjs-dist`, `pdfjs-dist/build/pdf.worker.min.mjs?url`, `pdfjs-dist/web/pdf_viewer.css`, `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/PdfReaderPane.selection.test.tsx](../../../../../../apps/learnloop-tauri/src/components/PdfReaderPane.selection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/PdfReaderPane.scroll.test.tsx](../../../../../../apps/learnloop-tauri/src/components/PdfReaderPane.scroll.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/PdfReaderPane.marks.test.tsx](../../../../../../apps/learnloop-tauri/src/components/PdfReaderPane.marks.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

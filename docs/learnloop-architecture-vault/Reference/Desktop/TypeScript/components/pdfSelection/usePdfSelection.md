---
title: "Desktop module · src/components/pdfSelection/usePdfSelection.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.pdfSelection.usePdfSelection"
language: "TypeScript"
area: "TypeScript/components/pdfSelection"
source_path: "apps/learnloop-tauri/src/components/pdfSelection/usePdfSelection.ts"
source_paths:
  - "apps/learnloop-tauri/src/components/pdfSelection/usePdfSelection.ts"
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

# `src/components/pdfSelection/usePdfSelection.ts`

Area: [[Reference/Desktop/TypeScript/components/pdfSelection/_area|TypeScript/components/pdfSelection]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides shared `usePdfSelection` state or utility behavior for desktop components.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/pdfSelection/usePdfSelection.ts](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/usePdfSelection.ts) |
| Source lines | 682 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/pdfSelection/_area|TypeScript/components/pdfSelection]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] → [[Reference/Desktop/TypeScript/components/pdfSelection/usePdfSelection|src/components/pdfSelection/usePdfSelection.ts]]

## Public API

- `export const SELECTION_SETTLE_MS = 150` — const, line 45
- `export interface HeldSelection` — interface, line 48
- `export interface MarqueeBox` — interface, line 54
- `export interface PagePoint` — interface, line 73
- `export interface PdfSelectionOptions` — interface, line 80
- `export function usePdfSelection(options: PdfSelectionOptions)` — function, line 112

## Internal implementation anchors

- `type HeadMove, type Pos, type SelRange, type SelectionModel, type SelectionPayload, } from "./model"` — type, line 36
- `type Pos, type SelRange, type SelectionModel, type SelectionPayload, } from "./model"` — type, line 37
- `type SelRange, type SelectionModel, type SelectionPayload, } from "./model"` — type, line 38
- `type SelectionModel, type SelectionPayload, } from "./model"` — type, line 39
- `type SelectionPayload, } from "./model"` — type, line 40
- `const MARQUEE_MIN_EXTENT_PTS = 4` — const, line 60
- `const DRAG_THRESHOLD_PX = 3` — const, line 62
- `const KEY_MOVES: Record<string, HeadMove> =` — const, line 64
- `function editable(target: EventTarget | null): boolean` — function, line 104
- `function isUi(target: EventTarget | null): boolean` — function, line 108
- `const pressRef = useRef<` — const, line 114
- `const liveRef = useRef<SelRange[] | null>(null)` — const, line 127
- `const caretRef = useRef<Pos | null>(null)` — const, line 129
- `const goalXRef = useRef<number | null>(null)` — const, line 130
- `const settleRef = useRef<number | null>(null)` — const, line 132
- `const committedRef = useRef<` — const, line 134
- `const callbacks = useRef(` — const, line 135
- `const held = useMemo<SelRange[]>(()` — const, line 138
- `const committed = committedRef.current` — const, line 140
- `const painted = live ?? held` — const, line 145
- `const paintedRef = useRef(painted)` — const, line 146
- `const showLive = useCallback((ranges: SelRange[] | null)` — const, line 149
- `const placeCaret = useCallback((pos: Pos | null)` — const, line 154
- `const cancelSettle = useCallback(()` — const, line 159
- `const settle = useCallback( (ranges: SelRange[])` — const, line 167
- `const payload = selectionPayload(model, ranges)` — const, line 172
- `const words = payload.quote.split(/\s+/).filter(Boolean)` — const, line 175
- `const clear = useCallback( (notify = true)` — const, line 184
- `const had = paintedRef.current.length > 0` — const, line 187
- `const lastPointRef = useRef<` — const, line 207
- `const frameRef = useRef<number | null>(null)` — const, line 208
- `const sweepRef = useRef<` — const, line 210
- `const cancelGesture = useCallback((): boolean` — const, line 216
- `const active = pressRef.current !== null || sweepRef.current !== null` — const, line 217
- `const extendTo = useCallback( (anchor: Pos, clientX: number, clientY: number)` — const, line 230
- `const point = callbacks.current.pointAt(clientX, clientY)` — const, line 232
- `const head = hitTest(model, point.page, point.x, point.y)` — const, line 234
- `const current = liveRef.current?.[0]` — const, line 236
- `const onPlainMouseDown = useCallback( (event: React.MouseEvent): boolean` — const, line 243
- `const point = callbacks.current.pointAt(event.clientX, event.clientY)` — const, line 246
- `const pos = hitTest(model, point.page, point.x, point.y)` — const, line 254
- `const from = caretRef.current ?? (paintedRef.current.length ? paintedRef.current[paintedRef.current.length - 1].anchor : null)` — const, line 256
- `const flushMove = ()` — const, line 282
- `const press = pressRef.current` — const, line 284
- `const point = lastPointRef.current` — const, line 285
- `const onMove = (event: MouseEvent)` — const, line 289
- `const press = pressRef.current` — const, line 290
- `const point = callbacks.current.pointAt(event.clientX, event.clientY)` — const, line 298
- `const onUp = ()` — const, line 307
- `const press = pressRef.current` — const, line 308
- `const ranges = liveRef.current` — const, line 318
- `const pos = press.pos` — const, line 323
- `const range = blockRange(model, pos.block)` — const, line 325
- `const range =` — const, line 331
- `const range =` — const, line 342
- `const scroller = (()` — const, line 355
- `let node: HTMLElement | null = containerRef.current?.parentElement ?? null` — let, line 356
- `const timer = window.setInterval(()` — const, line 363
- `const point = lastPointRef.current` — const, line 364
- `const press = pressRef.current` — const, line 365
- `const rect = scroller.getBoundingClientRect()` — const, line 367
- `const zone = 48` — const, line 368
- `const delta = point.y < rect.top + zone ? -Math.ceil((rect.top + zone - point.y) / 3) : point.y > rect.bottom - zone ? Math.ceil((point.y - (rect.bottom - zone)) / 3) : 0` — const, line 369
- `const onSweepMouseDown = useCallback( (event: React.MouseEvent): boolean` — const, line 387
- `const point = callbacks.current.pointAt(event.clientX, event.clientY)` — const, line 390
- `const block = blockAt(model, point.page, point.x, point.y)` — const, line 392
- `const range =` — const, line 399
- `const onMove = (event: MouseEvent)` — const, line 409
- `const sweep = sweepRef.current` — const, line 410
- `const point = callbacks.current.pointAt(event.clientX, event.clientY)` — const, line 412
- `const block = blockAt(model, point.page, point.x, point.y)` — const, line 414
- `const lo = Math.min(sweep.anchor, block)` — const, line 416
- `const hi = Math.max(sweep.anchor, block)` — const, line 417
- `const onUp = ()` — const, line 420
- `const ranges = liveRef.current` — const, line 425
- `const marqueeBoxesRef = useRef<MarqueeBox[]>([])` — const, line 441
- `const marqueeDragRef = useRef<` — const, line 442
- `const clearMarquee = useCallback(()` — const, line 443
- `const commitMarquee = useCallback(()` — const, line 450
- `const boxes = marqueeBoxesRef.current` — const, line 451
- `const region = boxes.length === 1 ? callbacks.current.regionAt?.(boxes[0]) ?? null : null` — const, line 455
- `const box = boxes[0]` — const, line 457
- `const ranges = marqueeRanges(model, boxes)` — const, line 470
- `const commitMarqueeRef = useRef(commitMarquee)` — const, line 475
- `const onMarqueeMouseDown = useCallback( (event: React.MouseEvent): boolean` — const, line 478
- `const point = callbacks.current.pointAt(event.clientX, event.clientY)` — const, line 481
- `const marqueeDrafting = marqueeDraft !== null` — const, line 494
- `const toPage = (drag:` — const, line 497
- `const widthPoints = Number(drag.pageEl.dataset.widthPoints)` — const, line 498
- `const rect = drag.pageEl.getBoundingClientRect()` — const, line 499
- `const scale = rect.width / widthPoints` — const, line 501
- `const draft = (drag:` — const, line 504
- `const onMove = (event: MouseEvent)` — const, line 510
- `const drag = marqueeDragRef.current` — const, line 511
- `const point = toPage(drag, event.clientX, event.clientY)` — const, line 513
- `const onUp = (event: MouseEvent)` — const, line 516
- `const drag = marqueeDragRef.current` — const, line 517
- `const point = toPage(drag, event.clientX, event.clientY)` — const, line 521
- `const rect = draft(drag, point)` — const, line 523
- `const next = [...marqueeBoxesRef.current,` — const, line 525
- `const onKeyDown = (event: KeyboardEvent)` — const, line 541
- `const onKeyUp = (event: KeyboardEvent)` — const, line 546
- `const onBlur = ()` — const, line 551
- `const keyboardStart = useCallback((): Pos | null` — const, line 564
- `const active = activeSpan ? model.blockIndex(activeSpan) : undefined` — const, line 566
- `const page = callbacks.current.firstShownPage?.() ?? null` — const, line 568
- `const onPage = page !== null ? model.blocksOnPage(page) : []` — const, line 569
- `const first = onPage.find((block)` — const, line 570
- `const onEscape = (event: KeyboardEvent)` — const, line 579
- `const onKeyDown = useCallback( (event: React.KeyboardEvent)` — const, line 591
- `const gesture = cancelGesture()` — const, line 595
- `const move = KEY_MOVES[event.key]` — const, line 602
- `const current = caretRef.current ? [] : paintedRef.current` — const, line 607
- `const last = current[current.length - 1]` — const, line 608
- `const anchor = last ? last.anchor : keyboardStart()` — const, line 609
- `const vertical = move === "up" || move === "down"` — const, line 611
- `let head: Pos` — let, line 612
- `const moved = moveHead(model, last ? last.head : anchor, move, vertical ? goalXRef.current : null)` — const, line 619
- `const ranges = [` — const, line 623
- `const onCopy = (event: ClipboardEvent)` — const, line 635
- `const ranges = paintedRef.current` — const, line 636
- `const native = window.getSelection()` — const, line 638
- `const payload = selectionPayload(model, ranges)` — const, line 640
- `const selectionUnder = useCallback( (point: PagePoint): SelectionPayload | null` — const, line 650
- `const ranges = paintedRef.current` — const, line 652
- `const onMouseDown = useCallback( (event: React.MouseEvent)` — const, line 659

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export: `HeldSelection`, `PagePoint`, `usePdfSelection`; references `HeldSelection`, `PagePoint`, `usePdfSelection`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/pdfSelection/model|src/components/pdfSelection/model.ts]] — import-or-re-export; imports `HeadMove`, `Pos`, `SelRange`, `SelectionModel`, `SelectionPayload`, `blockAt`, `blockRange`, `hitTest`, `marqueeRanges`, `moveHead`, `onRanges`, `rangesFromNodes`, `samePos`, `selectionPayload`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/PdfReaderPane.selection.test.tsx](../../../../../../../apps/learnloop-tauri/src/components/PdfReaderPane.selection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/pdfSelection/usePdfSelection.ts](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/usePdfSelection.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

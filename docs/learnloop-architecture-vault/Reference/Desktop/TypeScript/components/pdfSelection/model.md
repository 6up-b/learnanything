---
title: "Desktop module · src/components/pdfSelection/model.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.pdfSelection.model"
language: "TypeScript"
area: "TypeScript/components/pdfSelection"
source_path: "apps/learnloop-tauri/src/components/pdfSelection/model.ts"
source_paths:
  - "apps/learnloop-tauri/src/components/pdfSelection/model.ts"
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

# `src/components/pdfSelection/model.ts`

Area: [[Reference/Desktop/TypeScript/components/pdfSelection/_area|TypeScript/components/pdfSelection]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides shared `model` state or utility behavior for desktop components.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/pdfSelection/model.ts](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/model.ts) |
| Source lines | 635 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/pdfSelection/_area|TypeScript/components/pdfSelection]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/components/pdfSelection/model|src/components/pdfSelection/model.ts]]

## Public API

- `export interface SelBlock` — interface, line 41
- `export interface Pos` — interface, line 52
- `export interface SelRange` — interface, line 58
- `export interface SpanNode` — interface, line 65
- `export interface SelectionPayload` — interface, line 74
- `export class SelectionModel` — class, line 93
- `export function comparePos(a: Pos, b: Pos): number` — function, line 226
- `export function ordered(range: SelRange): [Pos, Pos]` — function, line 230
- `export function samePos(a: Pos | null | undefined, b: Pos | null | undefined): boolean` — function, line 234
- `export function blockRange(model: SelectionModel, block: number): SelRange` — function, line 238
- `export function step(model: SelectionModel, pos: Pos, delta: 1 | -1): Pos` — function, line 243
- `export type HeadMove = "left" | "right" | "up" | "down" | "lineStart" | "lineEnd"` — type, line 281
- `export function moveHead(model: SelectionModel, head: Pos, move: HeadMove, goalX?: number | null):` — function, line 285
- `export function lineRange(model: SelectionModel, pos: Pos): SelRange` — function, line 313
- `export function blockAt(model: SelectionModel, page: number, x: number, y: number): number | null` — function, line 326
- `export function hitTest(model: SelectionModel, page: number, x: number, y: number): Pos | null` — function, line 358
- `export function selectionNodes(model: SelectionModel, ranges: readonly SelRange[]): SpanNode[]` — function, line 396
- `export function selectionText(model: SelectionModel, ranges: readonly SelRange[]): string` — function, line 427
- `export function selectionPayload(model: SelectionModel, ranges: readonly SelRange[]): SelectionPayload | null` — function, line 449
- `export function anchorRange(model: SelectionModel, spanId: string, start: number, end: number): SelRange | null` — function, line 465
- `export function exactNode<T extends` — function, line 496
- `export function rangesFromNodes( model: SelectionModel, nodes: ReadonlyArray<` — function, line 528
- `export function rangeRects(model: SelectionModel, ranges: readonly SelRange[], page: number): Box[]` — function, line 550
- `export function marqueeRanges(model: SelectionModel, boxes: ReadonlyArray<` — function, line 593
- `export function onRanges(model: SelectionModel, ranges: readonly SelRange[], page: number, x: number, y: number): boolean` — function, line 633

## Internal implementation anchors

- `type BlockGeometry, type Box, type GlyphItem, type GlyphWord, type TextStyles, } from "./geometry"` — type, line 31
- `type Box, type GlyphItem, type GlyphWord, type TextStyles, } from "./geometry"` — type, line 32
- `type GlyphItem, type GlyphWord, type TextStyles, } from "./geometry"` — type, line 33
- `type GlyphWord, type TextStyles, } from "./geometry"` — type, line 34
- `type TextStyles, } from "./geometry"` — type, line 35
- `function isSelectable(block: ReaderPdfBlockDto): boolean` — function, line 84
- `const bbox = dto.bbox as Box` — const, line 111
- `const boxes = this.allBoxes.get(dto.page) ?? []` — const, line 112
- `const index = this.blocks.length` — const, line 118
- `const list = this.onPage.get(dto.page) ?? []` — const, line 131
- `const boxes = this.allBoxes.get(page) ?? []` — const, line 148
- `let tokens = this.tokenCache.get(block)` — let, line 155
- `const entry = this.blocks[block]` — const, line 157
- `const assigned = assignWords(words, this.allBoxes.get(page) ?? [])` — const, line 196
- `const geometry = new Map<number, BlockGeometry>()` — const, line 197
- `const block = this.blocks[index]` — const, line 199
- `const entry = this.blocks[block]` — const, line 212
- `const fromPage = this.pageGeometry.get(entry.page)?.get(block)` — const, line 213
- `let estimate = this.estimated.get(block)` — let, line 215
- `const count = model.unitCount(block)` — const, line 253
- `function unitCenterX(model: SelectionModel, pos: Pos): number` — function, line 259
- `const box = model.geometry(pos.block).boxes[pos.unit]?.[0]` — const, line 260
- `function nearestOnLine(model: SelectionModel, block: number, line: number, x: number): Pos` — function, line 264
- `const geometry = model.geometry(block)` — const, line 265
- `const units = geometry.lines[line]?.units ?? []` — const, line 266
- `let best = units[0] ?? 0` — let, line 267
- `let bestDistance = Infinity` — let, line 268
- `const distance = x < box[0] ? box[0] - x : x > box[2] ? x - box[2] : 0` — const, line 271
- `const geometry = model.geometry(head.block)` — const, line 288
- `const line = geometry.line[head.unit] ?? 0` — const, line 289
- `const units = geometry.lines[line]?.units ?? [head.unit]` — const, line 291
- `const x = goalX ?? unitCenterX(model, head)` — const, line 294
- `const last = model.geometry(block).lines.length - 1` — const, line 305
- `const geometry = model.geometry(pos.block)` — const, line 314
- `const units = geometry.lines[geometry.line[pos.unit] ?? 0]?.units ?? [pos.unit]` — const, line 315
- `function inside(box: Box, x: number, y: number, tolerance = 0): boolean` — function, line 321
- `const candidates = model.blocksOnPage(page)` — const, line 327
- `let best: number | null = null` — let, line 329
- `let bestArea = Infinity` — let, line 330
- `const box = model.blocks[index].bbox` — const, line 332
- `const area = (box[2] - box[0]) * (box[3] - box[1])` — const, line 334
- `let bestDistance = Infinity` — let, line 341
- `const box = model.blocks[index].bbox` — const, line 343
- `const dx = x < box[0] ? box[0] - x : x > box[2] ? x - box[2] : 0` — const, line 344
- `const dy = y < box[1] ? box[1] - y : y > box[3] ? y - box[3] : 0` — const, line 345
- `const distance = dy * 3 + dx` — const, line 348
- `const block = blockAt(model, page, x, y)` — const, line 362
- `const geometry = model.geometry(block)` — const, line 365
- `let line = 0` — let, line 367
- `let lineDistance = Infinity` — let, line 368
- `const distance = y < entry.y0 ? entry.y0 - y : y > entry.y1 ? y - entry.y1 : 0` — const, line 370
- `let best: number | null = null` — let, line 377
- `let bestDistance = Infinity` — let, line 378
- `const distance = x < box[0] ? box[0] - x : x > box[2] ? x - box[2] : 0` — const, line 382
- `const nodes: SpanNode[] = []` — const, line 397
- `const sorted = [...ranges].map(ordered).sort((a, b)` — const, line 398
- `const units = model.units(block)` — const, line 401
- `const first = block === lo.block ? Math.min(lo.unit, units.length - 1) : 0` — const, line 403
- `const last = block === hi.block ? Math.min(hi.unit, units.length - 1) : units.length - 1` — const, line 404
- `const text = model.blocks[block].text` — const, line 406
- `const start = units[first].start` — const, line 407
- `const end = units[last].end` — const, line 408
- `const SENTENCE_END = /[.!?:` — const, line 420
- `const PROSE_TYPES: ReadonlySet<string> = new Set(["Text", "TextInlineMath"])` — const, line 422
- `const nodes = selectionNodes(model, ranges)` — const, line 428
- `let out = ""` — let, line 429
- `let previousType = ""` — let, line 430
- `const block = model.blocks[model.blockIndex(node.spanId) ?? 0]` — const, line 432
- `const piece = cleanText(node.quote, block.blockType)` — const, line 433
- `const runsOn = PROSE_TYPES.has(previousType) && PROSE_TYPES.has(block.blockType) && !SENTENCE_END.test(out.trimEnd()) && /^[\p` — const, line 436
- `const nodes = selectionNodes(model, ranges).filter((node)` — const, line 450
- `const primary = [...nodes].sort((a, b)` — const, line 452
- `const quote = nodes .map((node)` — const, line 453
- `const block = model.blocks[model.blockIndex(node.spanId) ?? 0]` — const, line 455
- `const block = model.blockIndex(spanId)` — const, line 466
- `const units = model.units(block)` — const, line 468
- `const text = model.blocks[block].text` — const, line 470
- `const from = fromCodepoint(text, Math.max(0, start))` — const, line 471
- `const to = fromCodepoint(text, Math.max(start, end))` — const, line 472
- `let first = -1` — let, line 473
- `let last = -1` — let, line 474
- `const overlaps = unit.end > from && unit.start < to` — const, line 476
- `function escapeRegExp(text: string): string` — function, line 486
- `const text = blockText ?? ""` — const, line 500
- `const quote = node.quote.trim()` — const, line 501
- `let at = -1` — let, line 503
- `let length = 0` — let, line 504
- `const first = text.indexOf(quote)` — const, line 505
- `const pattern = new RegExp(quote.split(/\s+/).map(escapeRegExp).join("\\s+"), "gu")` — const, line 511
- `const matches = [...text.matchAll(pattern)]` — const, line 512
- `const ranges: SelRange[] = []` — const, line 532
- `const block = model.blockIndex(node.spanId)` — const, line 534
- `const range = typeof node.start === "number" && typeof node.end === "number" ? anchorRange(model, node.spanId, node.start, node.end) : blockRange(model, block)` — const, line 536
- `const rects: Box[] = []` — const, line 551
- `const onPage = model.blocksOnPage(page)` — const, line 552
- `const first = onPage[0]` — const, line 554
- `const last = onPage[onPage.length - 1]` — const, line 555
- `const count = model.unitCount(block)` — const, line 561
- `const geometry = model.geometry(block)` — const, line 567
- `const from = block === lo.block ? lo.unit : 0` — const, line 568
- `const to = block === hi.block ? hi.unit : count - 1` — const, line 569
- `const perLine = new Map<number, Box>()` — const, line 572
- `const line = geometry.boxLines[unit]?.[piece] ?? geometry.line[unit] ?? 0` — const, line 575
- `const current = perLine.get(line)` — const, line 576
- `const picked: Pos[] = []` — const, line 594
- `const pages = [...new Set(boxes.map((box)` — const, line 595
- `const rects = boxes.filter((box)` — const, line 597
- `const entry = model.blocks[block]` — const, line 599
- `const area = (entry.bbox[2] - entry.bbox[0]) * (entry.bbox[3] - entry.bbox[1])` — const, line 601
- `const covered = rects.some((rect)` — const, line 602
- `const w = Math.min(rect[2], entry.bbox[2]) - Math.max(rect[0], entry.bbox[0])` — const, line 603
- `const h = Math.min(rect[3], entry.bbox[3]) - Math.max(rect[1], entry.bbox[1])` — const, line 604
- `const rectArea = (rect[2] - rect[0]) * (rect[3] - rect[1])` — const, line 605
- `const geometry = model.geometry(block)` — const, line 611
- `const hit = unitBoxes.some((box)` — const, line 613
- `const cx = (box[0] + box[2]) / 2` — const, line 614
- `const cy = (box[1] + box[3]) / 2` — const, line 615
- `const ranges: SelRange[] = []` — const, line 623
- `const last = ranges[ranges.length - 1]` — const, line 625

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export: `Box`, `GlyphItem`, `GlyphWord`, `SelectionModel`, `SelectionPayload`, `TextStyles`, `blockAt`, `rangeRects`; references `Box`, `GlyphItem`, `GlyphWord`, `SelectionModel`, `SelectionPayload`, `TextStyles`, `blockAt`, `rangeRects`
- [[Reference/Desktop/TypeScript/components/pdfSelection/PdfSelectionLayer|src/components/pdfSelection/PdfSelectionLayer.tsx]] — import-or-re-export: `Box`; references `Box`
- [[Reference/Desktop/TypeScript/components/pdfSelection/highlights|src/components/pdfSelection/highlights.ts]] — import-or-re-export: `Box`, `SelRange`, `SelectionModel`, `anchorRange`, `rangeRects`; references `Box`, `SelRange`, `SelectionModel`, `anchorRange`, `rangeRects`
- [[Reference/Desktop/TypeScript/components/pdfSelection/usePdfSelection|src/components/pdfSelection/usePdfSelection.ts]] — import-or-re-export: `HeadMove`, `Pos`, `SelRange`, `SelectionModel`, `SelectionPayload`, `blockAt`, `blockRange`, `hitTest`, `marqueeRanges`, `moveHead`, `onRanges`, `rangesFromNodes`, `samePos`, `selectionPayload`; references `HeadMove`, `Pos`, `SelRange`, `SelectionModel`, `SelectionPayload`, `blockAt`, `blockRange`, `hitTest`, `marqueeRanges`, `moveHead`, `onRanges`, `rangesFromNodes`, `samePos`, `selectionPayload`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `exactNode`; references `exactNode`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderPdfBlockDto`
- [[Reference/Desktop/TypeScript/components/pdfSelection/geometry|src/components/pdfSelection/geometry.ts]] — import-or-re-export; imports `BlockGeometry`, `Box`, `GlyphItem`, `GlyphWord`, `TextStyles`, `assignWords`, `estimatedGeometry`, `glyphWords`, `regionGeometry`, `textLayerGeometry`
- [[Reference/Desktop/TypeScript/components/pdfSelection/tokens|src/components/pdfSelection/tokens.ts]] — import-or-re-export; imports `FURNITURE_TYPES`, `Token`, `cleanText`, `fromCodepoint`, `isAtomicType`, `keyOf`, `toCodepoint`, `tokenize`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/pdfSelection/perf.test.ts](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/perf.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/pdfSelection/model.test.ts](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/model.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/pdfSelection/fonts.test.ts](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/fonts.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/pdfSelection/arxiv.test.ts](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/arxiv.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/PdfReaderPane.selection.test.tsx](../../../../../../../apps/learnloop-tauri/src/components/PdfReaderPane.selection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/pdfSelection/model.ts](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/model.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

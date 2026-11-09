---
title: "Desktop module · src/components/pdfSelection/geometry.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.pdfSelection.geometry"
language: "TypeScript"
area: "TypeScript/components/pdfSelection"
source_path: "apps/learnloop-tauri/src/components/pdfSelection/geometry.ts"
source_paths:
  - "apps/learnloop-tauri/src/components/pdfSelection/geometry.ts"
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

# `src/components/pdfSelection/geometry.ts`

Area: [[Reference/Desktop/TypeScript/components/pdfSelection/_area|TypeScript/components/pdfSelection]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides shared `geometry` state or utility behavior for desktop components.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/pdfSelection/geometry.ts](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/geometry.ts) |
| Source lines | 843 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/pdfSelection/_area|TypeScript/components/pdfSelection]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] → [[Reference/Desktop/TypeScript/components/pdfSelection/geometry|src/components/pdfSelection/geometry.ts]]

## Public API

- `export type Box = [number, number, number, number]` — type, line 24
- `export interface GlyphItem` — interface, line 27
- `export type TextStyles = Readonly<Record<string,` — type, line 39
- `export interface GlyphWord` — interface, line 42
- `export interface BlockLine` — interface, line 48
- `export interface BlockGeometry` — interface, line 55
- `export function glyphWords( items: readonly GlyphItem[], viewportTransform: readonly number[], styles?: TextStyles | null, ): GlyphWord[]` — function, line 147
- `export interface OperatorListLike` — interface, line 219
- `export interface PdfFontInfo` — interface, line 226
- `export type OpsTable = Readonly<Record<string, number>>` — type, line 234
- `export function operatorWords( opList: OperatorListLike, ops: OpsTable, fontOf: (name: string)` — function, line 283
- `export function intoLines(words: readonly GlyphWord[]): Line[]` — function, line 516
- `export function alignKeys(tokens: readonly string[], glyphs: readonly string[]): Array<[number, number]>` — function, line 594
- `export function regionGeometry(bbox: Box): BlockGeometry` — function, line 710
- `export function estimatedGeometry(tokens: readonly Token[], bbox: Box): BlockGeometry` — function, line 718
- `export function textLayerGeometry(tokens: readonly Token[], words: readonly GlyphWord[], bbox: Box): BlockGeometry` — function, line 760
- `export function assignWords( words: readonly GlyphWord[], blocks: ReadonlyArray<` — function, line 818

## Internal implementation anchors

- `const HELVETICA: Record<string, number> = (()` — const, line 75
- `const table: Record<string, number> =` — const, line 76
- `const rows: Array<[string, number]> = [ [" ", 278], ["!", 278], ['"', 355], ["#", 556], ["$", 556], ["%", 889], ["&", 667], ["'", 191], ["(", 333], [")", 333], ["*", 389], ["+", 584], [",", 278], ["-", 333], [".", 278], ["/", 278], [":", 278], ["` — const, line 77
- `const TIMES: Record<string, number> = (()` — const, line 94
- `const table: Record<string, number> =` — const, line 95
- `const rows: Array<[string, number]> = [ [" ", 250], ["!", 333], ['"', 408], ["#", 500], ["$", 500], ["%", 833], ["&", 778], ["'", 180], ["(", 333], [")", 333], ["*", 500], ["+", 564], [",", 250], ["-", 333], [".", 250], ["/", 278], [":", 278], ["` — const, line 96
- `type Advance = (ch: string)` — type, line 113
- `const SANS_ADVANCE: Advance = (ch)` — const, line 114
- `const SERIF_ADVANCE: Advance = (ch)` — const, line 115
- `const MONO_ADVANCE: Advance = ()` — const, line 116
- `function advanceFor(item: GlyphItem, styles: TextStyles | null | undefined): Advance` — function, line 119
- `const family = (item.fontName && styles?.[item.fontName]?.fontFamily) || ""` — const, line 120
- `function multiply(m1: number[], m2: number[]): number[]` — function, line 126
- `const ASCENT = 0.8` — const, line 137
- `const DESCENT = 0.2` — const, line 138
- `const words: GlyphWord[] = []` — const, line 152
- `const state:` — const, line 153
- `const flush = ()` — const, line 154
- `const xScale = Math.hypot(viewportTransform[0], viewportTransform[1]) || 1` — const, line 158
- `const tx = multiply(viewportTransform as number[], item.transform)` — const, line 164
- `const height = Math.hypot(tx[2], tx[3]) || item.height || 0` — const, line 169
- `const width = item.width * xScale` — const, line 170
- `const left = tx[4]` — const, line 172
- `const top = tx[5] - height * ASCENT` — const, line 173
- `const bottom = tx[5] + height * DESCENT` — const, line 174
- `const chars = Array.from(item.str)` — const, line 175
- `const advance = advanceFor(item, styles)` — const, line 176
- `const total = chars.reduce((sum, ch)` — const, line 177
- `const open = state.open` — const, line 179
- `const touches = open !== null && !/\s/.test(chars[0] ?? " ") && Math.abs(left - open.box[2]) <= 0.25 * Math.max(height, open.height) && top < open.box[3] && bottom > open.box[1]` — const, line 180
- `let cursor = 0` — let, line 187
- `const x0 = left + (cursor / total) * width` — const, line 189
- `const x1 = left + (cursor / total) * width` — const, line 191
- `const current = state.open` — const, line 196
- `interface PaintState` — interface, line 236
- `const IDENTITY = [1, 0, 0, 1, 0, 0]` — const, line 253
- `const FONT_IDENTITY = [0.001, 0, 0, 0.001, 0, 0]` — const, line 254
- `const SPACE_GAP_EM = 0.102` — const, line 257
- `const BACK_GAP_EM = 0.2` — const, line 258
- `function matrixOf(value: unknown): number[] | null` — function, line 260
- `const matrix = Array.from(value as ArrayLike<number>, Number).slice(0, 6)` — const, line 262
- `function numberArg(args: unknown, index = 0): number` — function, line 266
- `const value = Array.isArray(args) ? Number(args[index]) : NaN` — const, line 267
- `function apply(m: readonly number[], x: number, y: number): [number, number]` — function, line 271
- `const words: GlyphWord[] = []` — const, line 289
- `let open:` — let, line 290
- `let pen: [number, number] | null = null` — let, line 292
- `const flush = ()` — const, line 293
- `let state: PaintState =` — let, line 297
- `const stack: PaintState[] = []` — const, line 301
- `const save = ()` — const, line 302
- `const restore = ()` — const, line 303
- `const previous = stack.pop()` — const, line 304
- `const moveText = (x: number, y: number)` — const, line 307
- `let inAnnotation = 0` — let, line 313
- `const showText = (glyphs: unknown)` — const, line 315
- `const font = state.font ??` — const, line 317
- `const fontSize = state.fontSize` — const, line 318
- `const type3 = Boolean(font.isType3Font)` — const, line 320
- `const fontMatrix = matrixOf(font.fontMatrix) ?? FONT_IDENTITY` — const, line 321
- `const hs = state.hScale * state.fontDirection` — const, line 322
- `const m = multiply(viewportTransform as number[], multiply(state.ctm, state.textMatrix))` — const, line 323
- `const upright = Math.abs(Math.atan2(m[1], m[0])) <= 0.02 && !font.vertical && inAnnotation === 0` — const, line 324
- `let em = fontSize` — let, line 327
- `const bbox = Array.from(font.bbox ?? [], Number)` — const, line 329
- `const glyphHeight = bbox.length >= 4 ? bbox[3] - bbox[1] : 0` — const, line 330
- `const height = Math.abs(em) * Math.hypot(m[2], m[3])` — const, line 333
- `const baseline = state.y + state.rise` — const, line 334
- `let x = 0` — let, line 335
- `const entry = glyph as` — const, line 342
- `const width = Number(entry.width) || 0` — const, line 343
- `const isSpaceGlyph = entry.isSpace === true` — const, line 344
- `const spacing = (isSpaceGlyph ? state.wordSpacing : 0) + state.charSpacing` — const, line 345
- `const painted = type3 ? (width * fontMatrix[0] + fontMatrix[4]) * fontSize : width * fontSize * fontMatrix[0]` — const, line 346
- `const advance = painted + (type3 ? spacing : spacing * state.fontDirection)` — const, line 347
- `const text = typeof entry.unicode === "string" ? entry.unicode : ""` — const, line 348
- `const next = apply(m, state.x + (x + advance) * hs, baseline)` — const, line 357
- `const box: Box = [Math.min(x0, x1), y0 - height * ASCENT, Math.max(x0, x1), y0 + height * DESCENT]` — const, line 364
- `const current = open as` — const, line 365
- `let joins = false` — let, line 366
- `const tolerance = Math.max(height, current.height)` — const, line 368
- `const direction = x1 >= x0 ? 1 : -1` — const, line 369
- `const gap = (x0 - pen[0]) * direction` — const, line 370
- `const fn = fnArray[index]` — const, line 393
- `const args = argsArray[index] as unknown[] | null | undefined` — const, line 394
- `const matrix = matrixOf(args)` — const, line 403
- `const matrix = matrixOf(Array.isArray(args) ? args[0] : null)` — const, line 409
- `const group = Array.isArray(args) ? (args[0] as` — const, line 418
- `const matrix = matrixOf(group?.matrix)` — const, line 419
- `const name = Array.isArray(args) ? String(args[0] ?? "") : ""` — const, line 450
- `let size = numberArg(args, 1)` — let, line 451
- `const matrix = matrixOf(Array.isArray(args) && args.length === 1 ? args[0] : args)` — const, line 469
- `interface Line` — interface, line 502
- `function center(box: Box): [number, number]` — function, line 510
- `const sorted = [...words].sort((a, b)` — const, line 517
- `const lines: Line[] = []` — const, line 518
- `const height = word.box[3] - word.box[1]` — const, line 521
- `const last = lines[lines.length - 1]` — const, line 522
- `const HYPHENS = /[-­‐‑]$/` — const, line 537
- `interface Piece` — interface, line 539
- `interface GlyphToken` — interface, line 545
- `function glyphTokens(lines: Line[], tokenKeys: ReadonlySet<string>): GlyphToken[]` — function, line 555
- `const out: GlyphToken[] = []` — const, line 556
- `let carry: GlyphToken | null = null` — let, line 557
- `const line = lines[lineIndex]` — const, line 559
- `const word = line.words[wordIndex]` — const, line 561
- `const glyphs = Math.max(1, Array.from(word.text).length)` — const, line 562
- `const piece: Piece =` — const, line 563
- `const held: GlyphToken = carry` — const, line 565
- `const lineEnd = wordIndex === line.words.length - 1 && lineIndex < lines.length - 1` — const, line 573
- `const stem = keyOf(word.text.replace(HYPHENS, ""))` — const, line 574
- `const LOOKAHEAD = 12` — const, line 588
- `const pairs: Array<[number, number]> = []` — const, line 595
- `let i = 0` — let, line 596
- `let j = 0` — let, line 597
- `let skipGlyphs = -1` — let, line 605
- `let skipTokens = -1` — let, line 606
- `function spread(weights: readonly number[], pieces: ReadonlyArray<Piece>): Piece[][]` — function, line 638
- `const widths = pieces.map((piece)` — const, line 639
- `const totalWidth = widths.reduce((a, b)` — const, line 640
- `const totalWeight = weights.reduce((a, b)` — const, line 641
- `const locate = (at: number): Piece` — const, line 642
- `let cumulative = 0` — let, line 643
- `const piece = pieces[index]` — const, line 646
- `const x = Math.min(piece.box[2], piece.box[0] + Math.max(0, at - cumulative))` — const, line 647
- `const piece = pieces[pieces.length - 1]` — const, line 652
- `const out: Piece[][] = []` — const, line 655
- `let from = 0` — let, line 656
- `const to = from + (weight / totalWeight) * totalWidth` — const, line 658
- `const parts: Piece[] = []` — const, line 659
- `let cumulative = 0` — let, line 660
- `const a = cumulative` — const, line 662
- `const lo = Math.max(a, from)` — const, line 664
- `const hi = Math.min(cumulative, to)` — const, line 665
- `const x0 = piece.box[0] + (lo - a)` — const, line 667
- `const x1 = piece.box[0] + (hi - a)` — const, line 668
- `const last = parts[parts.length - 1]` — const, line 669
- `function finalize(source: BlockGeometry["source"], parts: Piece[][], extents: ReadonlyArray<` — function, line 687
- `const used = [...new Set(parts.map((pieces)` — const, line 688
- `const renumber = new Map(used.map((raw, index)` — const, line 689
- `const lines: BlockLine[] = used.map((raw)` — const, line 690
- `const line = parts.map((pieces)` — const, line 695
- `const entry = lines[line[unit]]` — const, line 697
- `const target = lines[renumber.get(piece.line) ?? line[unit]]` — const, line 700
- `const boxLines = parts.map((pieces, unit)` — const, line 705
- `const width = Math.max(1, bbox[2] - bbox[0])` — const, line 719
- `const height = Math.max(1, bbox[3] - bbox[1])` — const, line 720
- `const weights = tokens.map((token)` — const, line 722
- `const totalGlyphs = weights.reduce((a, b)` — const, line 723
- `const em = Math.sqrt((width * height) / (0.6 * totalGlyphs))` — const, line 725
- `const lineCount = Math.max(1, Math.min(tokens.length, Math.round(height / (1.2 * em))))` — const, line 726
- `const perLine = totalGlyphs / lineCount` — const, line 727
- `const lineOf: number[] = []` — const, line 728
- `let cumulative = 0` — let, line 729
- `const lineHeight = height / lineCount` — const, line 734
- `const parts: Piece[][] = tokens.map(()` — const, line 735
- `const averageGlyph = width / perLine` — const, line 736
- `const members = lineOf.flatMap((value, unit)` — const, line 738
- `const lineWeight = members.reduce((sum, unit)` — const, line 740
- `const last = lineIndex === lineCount - 1 && lineCount > 1` — const, line 741
- `const glyphWidth = last ? Math.min(averageGlyph, width / lineWeight) : width / lineWeight` — const, line 742
- `const y0 = bbox[1] + lineIndex * lineHeight` — const, line 743
- `let x = bbox[0]` — let, line 744
- `const w = Math.max(0.5, (weights[unit] - 1) * glyphWidth)` — const, line 746
- `const extents = Array.from(` — const, line 751
- `const lines = intoLines(words)` — const, line 763
- `const glyphs = glyphTokens(lines, new Set(tokens.map((token)` — const, line 764
- `const pairs = alignKeys(tokens.map((token)` — const, line 765
- `const laid = spread(tokens.map((token)` — const, line 769
- `const parts: Piece[][] = tokens.map(()` — const, line 772
- `const matchedGlyphs = pairs.map(([, j])` — const, line 774
- `const glyphWidth = (()` — const, line 775
- `const w = matchedGlyphs.reduce((sum, glyph)` — const, line 776
- `const n = matchedGlyphs.reduce((sum, glyph)` — const, line 777
- `const anchors: Array<[number, number]> = [[-1, -1], ...pairs, [tokens.length, glyphs.length]]` — const, line 781
- `const gap = Array.from(` — const, line 785
- `const gapPieces = glyphs.slice(j0 + 1, j1).flatMap((glyph)` — const, line 787
- `const laid = spread(gap.map((unit)` — const, line 789
- `const before = i0 >= 0 ? parts[i0][parts[i0].length - 1] : null` — const, line 797
- `const after = i1 < tokens.length ? parts[i1][0] : null` — const, line 798
- `const host = (before ?? after) as Piece` — const, line 799
- `const total = gap.reduce((sum, unit)` — const, line 800
- `let x = before ? before.box[2] + glyphWidth * 0.3 : host.box[0] - total` — let, line 801
- `const room = before && after && after.line === before.line ? Math.max(0, after.box[0] - x) : Infinity` — const, line 802
- `const squeeze = room < total ? room / total : 1` — const, line 803
- `const w = Math.max(0.5, tokens[unit].glyphs * glyphWidth * squeeze)` — const, line 805
- `const x0 = Math.max(bbox[0], Math.min(x, bbox[2] - 0.5))` — const, line 806
- `const out = new Map<number, GlyphWord[]>()` — const, line 822
- `const height = word.box[3] - word.box[1]` — const, line 825
- `let best:` — let, line 826
- `const tolX = 2` — const, line 828
- `const tolY = Math.min(4, height * 0.3)` — const, line 829
- `const area = (block.bbox[2] - block.bbox[0]) * (block.bbox[3] - block.bbox[1])` — const, line 833
- `const list = out.get(best.index) ?? []` — const, line 837

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export: `PdfFontInfo`, `operatorWords`; references `PdfFontInfo`, `operatorWords`
- [[Reference/Desktop/TypeScript/components/pdfSelection/model|src/components/pdfSelection/model.ts]] — import-or-re-export: `BlockGeometry`, `Box`, `GlyphItem`, `GlyphWord`, `TextStyles`, `assignWords`, `estimatedGeometry`, `glyphWords`, `regionGeometry`, `textLayerGeometry`; references `BlockGeometry`, `Box`, `GlyphItem`, `GlyphWord`, `TextStyles`, `assignWords`, `estimatedGeometry`, `glyphWords`, `regionGeometry`, `textLayerGeometry`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/components/pdfSelection/tokens|src/components/pdfSelection/tokens.ts]] — import-or-re-export; imports `Token`, `keyOf`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/pdfSelection/fonts.test.ts](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/fonts.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/pdfSelection/geometry.ts](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/geometry.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

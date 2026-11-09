---
title: "Desktop module · src/screens/reader/figures/AdvancedPanels.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.AdvancedPanels"
language: "TypeScript"
area: "TypeScript/screens/reader/figures"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/AdvancedPanels.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/AdvancedPanels.tsx"
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

# `src/screens/reader/figures/AdvancedPanels.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `AdvancedPanels` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/AdvancedPanels.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/AdvancedPanels.tsx) |
| Source lines | 290 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigurePanels|src/screens/reader/figures/FigurePanels.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/AdvancedPanels|src/screens/reader/figures/AdvancedPanels.tsx]]

## Public API

- `export const ADVANCED_COPY =` — const, line 29
- `export function contourSegments(grid: HeatmapGridData, level: number): Array<[[number, number], [number, number]]>` — function, line 86
- `export function HeatmapPanelView(` — function, line 171
- `export function VectorFieldPanelView(` — function, line 187
- `export function PathPanelView(` — function, line 239

## Internal implementation anchors

- `const W = 600` — const, line 19
- `const H = 300` — const, line 20
- `const PAD =` — const, line 21
- `const TABLE_SIDE = 12` — const, line 22
- `const svgStyle: CSSProperties =` — const, line 24
- `const tableStyle: CSSProperties =` — const, line 25
- `const cellStyle: CSSProperties =` — const, line 26
- `const noteStyle: CSSProperties =` — const, line 27
- `function scaler(domain: [number, number], range: [number, number]): (value: number)` — function, line 36
- `const span = d1 - d0 || 1` — const, line 39
- `function finiteRange(values: Array<number | null>): [number, number] | null` — function, line 43
- `let low = Infinity` — let, line 44
- `let high = -Infinity` — let, line 45
- `function sampled(length: number, side = TABLE_SIDE): number[]` — function, line 55
- `const step = Math.max(1, Math.ceil(length / side))` — const, line 57
- `const out: number[] = []` — const, line 58
- `function GridAxes(` — function, line 64
- `function frame(xs: number[], ys: number[])` — function, line 79
- `const xDomain: [number, number] = [xs[0], xs[xs.length - 1]]` — const, line 80
- `const yDomain: [number, number] = [ys[0], ys[ys.length - 1]]` — const, line 81
- `const segments: Array<[[number, number], [number, number]]> = []` — const, line 87
- `const cross = (x0: number, y0: number, v0: number, x1: number, y1: number, v1: number): [number, number]` — const, line 89
- `const t = v1 === v0 ? 0.5 : (level - v0) / (v1 - v0)` — const, line 90
- `const corners = [z[j][i], z[j][i + 1], z[j + 1][i + 1], z[j + 1][i]]` — const, line 95
- `const points: Array<[number, number]> = []` — const, line 98
- `const edges: Array<[number, number, number, number, number, number]> = [ [xs[i], ys[j], a, xs[i + 1], ys[j], b], [xs[i + 1], ys[j], b, xs[i + 1], ys[j + 1], c], [xs[i + 1], ys[j + 1], c, xs[i], ys[j + 1], d], [xs[i], ys[j + 1], d, xs[i], ys[j], a], ]` — const, line 99
- `function HeatCells(` — function, line 115
- `const range = finiteRange(grid.z.flat())` — const, line 116
- `const span = high - low || 1` — const, line 119
- `const halfX = (index: number)` — const, line 120
- `const halfY = (index: number)` — const, line 121
- `const left = x(Math.max(grid.x[0], grid.x[i] - halfX(i)))` — const, line 126
- `const right = x(Math.min(grid.x[grid.x.length - 1], grid.x[i] + halfX(i)))` — const, line 127
- `const top = y(Math.min(grid.y[grid.y.length - 1], grid.y[j] + halfY(j)))` — const, line 128
- `const bottom = y(Math.max(grid.y[0], grid.y[j] - halfY(j)))` — const, line 129
- `function HeatLegend(` — function, line 143
- `const range = finiteRange(grid.z.flat())` — const, line 144
- `function ValuesGrid(` — function, line 154
- `const columns = sampled(xs.length)` — const, line 155
- `const rows = sampled(ys.length)` — const, line 156
- `const labels = useFigureLabels()` — const, line 173
- `const plain = (id: string)` — const, line 174
- `let longest = 0` — let, line 189
- `const v = data.v[j][i]` — const, line 191
- `const stepX = data.x.length > 1 ? Math.abs(x(data.x[1]) - x(data.x[0])) : W` — const, line 194
- `const stepY = data.y.length > 1 ? Math.abs(y(data.y[1]) - y(data.y[0])) : H` — const, line 195
- `const reach = 0.85 * Math.min(stepX, stepY)` — const, line 196
- `const labels = useFigureLabels()` — const, line 197
- `const plain = (id: string)` — const, line 198
- `const v = data.v[j][i]` — const, line 211
- `const scale = reach / longest` — const, line 213
- `const x0 = x(data.x[i])` — const, line 214
- `const y0 = y(data.y[j])` — const, line 215
- `const dx = u * scale` — const, line 216
- `const dy = -v * scale` — const, line 217
- `function pathWindow(range:` — function, line 234
- `const pad = (range.max - range.min) * ESCAPE_MARGIN` — const, line 235
- `const trajectory = data.kind === "trajectory_2d"` — const, line 240
- `const xDomain = axes ? pathWindow(axes.x) : (finiteRange(data.x) ?? [0, 1])` — const, line 241
- `const yDomain = axes ? pathWindow(axes.y) : (finiteRange(data.y) ?? [0, 1])` — const, line 242
- `const x = scaler(xDomain, [PAD.left, W - PAD.right])` — const, line 243
- `const y = scaler(yDomain, [H - PAD.bottom, PAD.top])` — const, line 244
- `const steps = trajectory ? (data as TrajectoryData).t : (data as IterateData).k` — const, line 245
- `const d = data.x.map((xv, index)` — const, line 246
- `const stoppedLine = data.stopped === "left_plot" ? ADVANCED_COPY.leftPlot : data.stopped === "not_finite" ? ADVANCED_COPY.notFinite : data.stopped === "starts_outside" ? ADVANCED_COPY.startsOutside : null` — const, line 247
- `const last = data.x.length - 1` — const, line 250
- `const labels = useFigureLabels()` — const, line 251
- `const plain = (id: string)` — const, line 252

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/figures/FigurePanels|src/screens/reader/figures/FigurePanels.tsx]] — import-or-re-export: `HeatmapPanelView`, `PathPanelView`, `VectorFieldPanelView`; references `HeatmapPanelView`, `PathPanelView`, `VectorFieldPanelView`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigurePanels|src/screens/reader/figures/FigurePanels.tsx]] — import-or-re-export; imports `formatValue`
- [[Reference/Desktop/TypeScript/screens/reader/figures/figureLabels|src/screens/reader/figures/figureLabels.tsx]] — import-or-re-export; imports `LabelText`, `useFigureLabels`
- [[Reference/Desktop/TypeScript/screens/reader/figures/figureSpec|src/screens/reader/figures/figureSpec.ts]] — import-or-re-export; imports `ESCAPE_MARGIN`, `HeatmapGridData`, `IterateData`, `TrajectoryData`, `VectorFieldData`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/AdvancedPanels.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/AdvancedPanels.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

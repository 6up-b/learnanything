---
title: "Desktop module · src/screens/reader/figures/FigurePanels.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.FigurePanels"
language: "TypeScript"
area: "TypeScript/screens/reader/figures"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/FigurePanels.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/FigurePanels.tsx"
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

# `src/screens/reader/figures/FigurePanels.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `FigurePanels` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/FigurePanels.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/FigurePanels.tsx) |
| Source lines | 277 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigurePanels|src/screens/reader/figures/FigurePanels.tsx]]

## Public API

- `export function formatValue(value: number | null, format: "number" | "percent" = "number"): string` — function, line 23
- `export function FigurePanel(` — function, line 265

## Internal implementation anchors

- `const W = 600` — const, line 17
- `const H = 220` — const, line 18
- `const PAD =` — const, line 19
- `const DASHES = ["", "6 4", "2 3", "10 3 2 3"]` — const, line 20
- `const SHADE_FILLS = ["var(--wash-amber)", "var(--wash-cyan)", "var(--wash-purple)", "var(--wash-green)"]` — const, line 21
- `const scaled = value * 100` — const, line 27
- `function extent(values: Array<number | null>, include: number[] = []): [number, number]` — function, line 34
- `const finite = [...values.filter((value): value is number` — const, line 35
- `let low = Math.min(...finite)` — let, line 37
- `let high = Math.max(...finite)` — let, line 38
- `const pad = (high - low) * 0.05` — const, line 43
- `function scaler(domain: [number, number], range: [number, number]): (value: number)` — function, line 47
- `const svgStyle: CSSProperties =` — const, line 53
- `const tableStyle: CSSProperties =` — const, line 54
- `const cellStyle: CSSProperties =` — const, line 55
- `function Axes(` — function, line 57
- `const zeroY = yDomain[0] <= 0 && yDomain[1] >= 0 ? y(0) : H - PAD.bottom` — const, line 58
- `function FunctionPlot(` — function, line 73
- `const labels = useFigureLabels()` — const, line 75
- `const plain = (id: string)` — const, line 76
- `const xDomain: [number, number] = [data.x[0], data.x[data.x.length - 1]]` — const, line 77
- `const yDomain = extent(data.series.flatMap((series)` — const, line 78
- `const x = scaler(xDomain, [PAD.left, W - PAD.right])` — const, line 79
- `const y = scaler(yDomain, [H - PAD.bottom, PAD.top])` — const, line 80
- `const path = (ys: Array<number | null>)` — const, line 81
- `let d = ""` — let, line 82
- `let pen = false` — let, line 83
- `const shadePath = (shade: FunctionPlotData["shades"][number])` — const, line 94
- `const series = data.series.find((item)` — const, line 95
- `const points: Array<[number, number]> = []` — const, line 98
- `const yv = series.y[index]` — const, line 100
- `const base = y(Math.max(yDomain[0], Math.min(0, yDomain[1])))` — const, line 104
- `function FunctionTable(` — function, line 149
- `const rows = data.x.map((xv, index)` — const, line 150
- `function PmfBars(` — function, line 176
- `const labels = useFigureLabels()` — const, line 177
- `const plain = (id: string)` — const, line 178
- `const ks = data.k` — const, line 179
- `const yDomain = extent(data.series.flatMap((series)` — const, line 180
- `const x = scaler([ks[0] - 0.5, ks[ks.length - 1] + 0.5], [PAD.left, W - PAD.right])` — const, line 181
- `const y = scaler(yDomain, [H - PAD.bottom, PAD.top])` — const, line 182
- `const width = Math.max(1, (x(1) - x(0)) * 0.7 / Math.max(1, data.series.length))` — const, line 183
- `const inHighlight = (k: number)` — const, line 184
- `function LinearMap(` — function, line 218
- `const labels = useFigureLabels()` — const, line 219
- `const spoken = labels && label ? labels.plain(label) : label` — const, line 220
- `const points = data.square.filter((point): point is [number, number]` — const, line 221
- `const all = [...points, [0, 0], [1, 0], [1, 1], [0, 1]] as Array<[number, number]>` — const, line 222
- `const reach = Math.max(1.2, ...all.map(([px, py])` — const, line 223
- `const size = H - PAD.top - PAD.bottom` — const, line 224
- `const left = (W - size) / 2` — const, line 225
- `const x = scaler([-reach, reach], [left, left + size])` — const, line 226
- `const y = scaler([-reach, reach], [H - PAD.bottom, PAD.top])` — const, line 227
- `const polygon = (corners: Array<[number, number]>)` — const, line 228
- `function Readout(` — function, line 257
- `const axes = model && (model.kind === "trajectory_2d" || model.kind === "iterate_2d") ?` — const, line 273

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/figures/AdvancedPanels|src/screens/reader/figures/AdvancedPanels.tsx]] — import-or-re-export: `formatValue`; references `formatValue`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export: `FigurePanel`, `formatValue`; references `FigurePanel`, `formatValue`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] — import-or-re-export: `formatValue`; references `formatValue`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/reader/figures/AdvancedPanels|src/screens/reader/figures/AdvancedPanels.tsx]] — import-or-re-export; imports `HeatmapPanelView`, `PathPanelView`, `VectorFieldPanelView`
- [[Reference/Desktop/TypeScript/screens/reader/figures/figureLabels|src/screens/reader/figures/figureLabels.tsx]] — import-or-re-export; imports `LabelSuffix`, `LabelText`, `useFigureLabels`
- [[Reference/Desktop/TypeScript/screens/reader/figures/figureSpec|src/screens/reader/figures/figureSpec.ts]] — import-or-re-export; imports `FigurePanelModel`, `FunctionPlotData`, `LinearMapData`, `PanelData`, `PmfBarsData`, `ReadoutData`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/figureDisplayCorpus.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figureDisplayCorpus.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/FigureInline.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/FigureInline.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/FigurePanels.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/FigurePanels.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

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
source_commit: "48d0a951e8e97d7b377caf0db9c7f40db14ce349"
source_commit_timestamp: "2026-10-23T11:08:36-04:00"
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
| Source lines | 269 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `48d0a951e8e97d7b377caf0db9c7f40db14ce349` |
| Commit timestamp | `2026-10-23T11:08:36-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigurePanels|src/screens/reader/figures/FigurePanels.tsx]]

## Public API

- `export function formatValue(value: number | null, format: "number" | "percent" = "number"): string` — function, line 22
- `export function FigurePanel(` — function, line 257

## Internal implementation anchors

- `const W = 600` — const, line 16
- `const H = 220` — const, line 17
- `const PAD =` — const, line 18
- `const DASHES = ["", "6 4", "2 3", "10 3 2 3"]` — const, line 19
- `const SHADE_FILLS = ["var(--wash-amber)", "var(--wash-cyan)", "var(--wash-purple)", "var(--wash-green)"]` — const, line 20
- `const scaled = value * 100` — const, line 26
- `function extent(values: Array<number | null>, include: number[] = []): [number, number]` — function, line 33
- `const finite = [...values.filter((value): value is number` — const, line 34
- `let low = Math.min(...finite)` — let, line 36
- `let high = Math.max(...finite)` — let, line 37
- `const pad = (high - low) * 0.05` — const, line 42
- `function scaler(domain: [number, number], range: [number, number]): (value: number)` — function, line 46
- `const svgStyle: CSSProperties =` — const, line 52
- `const tableStyle: CSSProperties =` — const, line 53
- `const cellStyle: CSSProperties =` — const, line 54
- `function Axes(` — function, line 56
- `const zeroY = yDomain[0] <= 0 && yDomain[1] >= 0 ? y(0) : H - PAD.bottom` — const, line 57
- `function FunctionPlot(` — function, line 72
- `const xDomain: [number, number] = [data.x[0], data.x[data.x.length - 1]]` — const, line 73
- `const yDomain = extent(data.series.flatMap((series)` — const, line 74
- `const x = scaler(xDomain, [PAD.left, W - PAD.right])` — const, line 75
- `const y = scaler(yDomain, [H - PAD.bottom, PAD.top])` — const, line 76
- `const path = (ys: Array<number | null>)` — const, line 77
- `let d = ""` — let, line 78
- `let pen = false` — let, line 79
- `const shadePath = (shade: FunctionPlotData["shades"][number])` — const, line 90
- `const series = data.series.find((item)` — const, line 91
- `const points: Array<[number, number]> = []` — const, line 94
- `const yv = series.y[index]` — const, line 96
- `const base = y(Math.max(yDomain[0], Math.min(0, yDomain[1])))` — const, line 100
- `function FunctionTable(` — function, line 145
- `const rows = data.x.map((xv, index)` — const, line 146
- `function PmfBars(` — function, line 172
- `const ks = data.k` — const, line 173
- `const yDomain = extent(data.series.flatMap((series)` — const, line 174
- `const x = scaler([ks[0] - 0.5, ks[ks.length - 1] + 0.5], [PAD.left, W - PAD.right])` — const, line 175
- `const y = scaler(yDomain, [H - PAD.bottom, PAD.top])` — const, line 176
- `const width = Math.max(1, (x(1) - x(0)) * 0.7 / Math.max(1, data.series.length))` — const, line 177
- `const inHighlight = (k: number)` — const, line 178
- `function LinearMap(` — function, line 212
- `const points = data.square.filter((point): point is [number, number]` — const, line 213
- `const all = [...points, [0, 0], [1, 0], [1, 1], [0, 1]] as Array<[number, number]>` — const, line 214
- `const reach = Math.max(1.2, ...all.map(([px, py])` — const, line 215
- `const size = H - PAD.top - PAD.bottom` — const, line 216
- `const left = (W - size) / 2` — const, line 217
- `const x = scaler([-reach, reach], [left, left + size])` — const, line 218
- `const y = scaler([-reach, reach], [H - PAD.bottom, PAD.top])` — const, line 219
- `const polygon = (corners: Array<[number, number]>)` — const, line 220
- `function Readout(` — function, line 249
- `const axes = model && (model.kind === "trajectory_2d" || model.kind === "iterate_2d") ?` — const, line 265

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

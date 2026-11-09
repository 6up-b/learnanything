---
title: "Desktop module · src/screens/reader/figures/figureSpec.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.figureSpec"
language: "TypeScript"
area: "TypeScript/screens/reader/figures"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/figureSpec.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/figureSpec.ts"
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

# `src/screens/reader/figures/figureSpec.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `SPEC_VERSION`, `SAMPLES`, `DIRECTIONS`, `SAME_TOLERANCE` and related exports within the desktop's TypeScript/screens/reader/figures ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/figureSpec.ts](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figureSpec.ts) |
| Source lines | 811 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/figureSpec|src/screens/reader/figures/figureSpec.ts]]

## Public API

- `export const SPEC_VERSION = "ifs-v1"` — const, line 37
- `export const SAMPLES = 120` — const, line 38
- `export const DIRECTIONS = ["rises", "falls", "same"] as const` — const, line 39
- `export const SAME_TOLERANCE = 1e-6` — const, line 40
- `export const MAX_BARS = 200` — const, line 42
- `export const MAX_DOMAIN_SPAN = 1e12` — const, line 44
- `export const ADVANCED_KINDS = ["heatmap_2d", "vector_field_2d", "trajectory_2d", "iterate_2d"] as const` — const, line 46
- `export const MAX_HEATMAP_CELLS = 40` — const, line 47
- `export const DEFAULT_HEATMAP_CELLS = 40` — const, line 48
- `export const MAX_FIELD_CELLS = 20` — const, line 49
- `export const DEFAULT_FIELD_CELLS = 12` — const, line 50
- `export const MAX_TRAJECTORY_STEPS = 2000` — const, line 51
- `export const DEFAULT_TRAJECTORY_STEPS = 400` — const, line 52
- `export const MAX_ITERATIONS = 500` — const, line 53
- `export const DEFAULT_ITERATIONS = 50` — const, line 54
- `export const MAX_CONTOURS = 8` — const, line 55
- `export const MAX_PANEL_WORK = 250000` — const, line 56
- `export const ESCAPE_MARGIN = 0.25` — const, line 57
- `export const STOP_LEFT = "left_plot"` — const, line 58
- `export const STOP_NOT_FINITE = "not_finite"` — const, line 59
- `export const STOP_OUTSIDE = "starts_outside"` — const, line 60
- `export interface FigureParameter` — interface, line 62
- `export interface FigureAxis` — interface, line 63
- `export interface FigureSeries` — interface, line 64
- `export interface FigureShade` — interface, line 65
- `export interface FigureMarker` — interface, line 66
- `export interface FunctionPlotPanel` — interface, line 67
- `export interface PmfBarsPanel` — interface, line 68
- `export interface LinearMapPanel` — interface, line 69
- `export interface ReadoutPanel` — interface, line 70
- `export interface GridAxis extends FigureAxis` — interface, line 71
- `export interface HeatmapPanel` — interface, line 72
- `export interface FieldHeatmap` — interface, line 73
- `export interface VectorFieldPanel` — interface, line 74
- `export interface TrajectoryPanel` — interface, line 75
- `export interface IteratePanel` — interface, line 76
- `export type AdvancedPanel = HeatmapPanel | VectorFieldPanel | TrajectoryPanel | IteratePanel` — type, line 77
- `export type FigurePanel = FunctionPlotPanel | PmfBarsPanel | LinearMapPanel | ReadoutPanel | AdvancedPanel` — type, line 78
- `export function isAdvancedKind(kind: unknown): kind is AdvancedPanel["kind"]` — function, line 80
- `export interface FigureInvariant` — interface, line 83
- `export interface FigurePrediction` — interface, line 84
- `export interface FigureSpec` — interface, line 86
- `export interface CompiledPanel` — interface, line 101
- `export interface CompiledFigure` — interface, line 103
- `export class FigureSpecError extends Error` — class, line 112
- `export function defaults(compiled: CompiledFigure): Env` — function, line 118
- `export function expandedFree(node: FigureNode, defs: Definitions, bound: Set<string> = new Set(), seen: string[] = []): Set<string>` — function, line 125
- `export function compileSpec(raw: FigureSpec | string): CompiledFigure` — function, line 151
- `export function advancedExpressions(panel: AdvancedPanel): string[]` — function, line 318
- `export function advancedKinds(spec: FigureSpec): string[]` — function, line 329
- `export function expressionWork(node: FigureNode, defs: Definitions, parameters: FigureParameter[], ranges: Ranges, seen: string[] = []): number` — function, line 369
- `export function plotXs(axis: FigureAxis): number[]` — function, line 511
- `export function barKs(axis: FigureAxis): number[]` — function, line 516
- `export function shadeValue(compiled: CompiledFigure, panel: CompiledPanel, shadeIndex: number, env: Env): [number, number, number]` — function, line 524
- `export interface FunctionPlotData` — interface, line 560
- `export interface PmfBarsData` — interface, line 561
- `export interface LinearMapData` — interface, line 562
- `export interface ReadoutData` — interface, line 563
- `export interface HeatmapGridData` — interface, line 564
- `export interface HeatmapData extends HeatmapGridData` — interface, line 565
- `export interface VectorFieldData` — interface, line 566
- `export type PathStop = typeof STOP_LEFT | typeof STOP_NOT_FINITE | typeof STOP_OUTSIDE | null` — type, line 567
- `export interface TrajectoryData` — interface, line 568
- `export interface IterateData` — interface, line 569
- `export type PanelData = FunctionPlotData | PmfBarsData | LinearMapData | ReadoutData | HeatmapData | VectorFieldData | TrajectoryData | IterateData` — type, line 570
- `export function gridPoints(axis: FigureAxis, cells: number): number[]` — function, line 573
- `export function escapeBox(axis: FigureAxis): [number, number]` — function, line 594
- `export interface DerivedBounds` — interface, line 700
- `export function derivedBounds(compiled: CompiledFigure, panelIndex: number, kind: "shade" | "highlight" | "integral" | "sum", index: number, env: Env): DerivedBounds` — function, line 707
- `export function evaluatePanel(compiled: CompiledFigure, panel: CompiledPanel, env: Env): PanelData` — function, line 732
- `export interface FigureData` — interface, line 796
- `export function evaluateFigure(compiled: CompiledFigure, params: Env =` — function, line 799
- `export function observedValue(compiled: CompiledFigure, index: number, params: Env =` — function, line 805

## Internal implementation anchors

- `type Definitions, type Env, type FigureNode, } from "./figureGrammar"` — type, line 32
- `type Env, type FigureNode, } from "./figureGrammar"` — type, line 33
- `type FigureNode, } from "./figureGrammar"` — type, line 34
- `const env: Env = newEnv()` — const, line 119
- `const found = new Set<string>()` — const, line 126
- `const stack: Array<[FigureNode, Set<string>, string[]]> = [[node, bound, seen]]` — const, line 127
- `const name = current.text` — const, line 131
- `function boundVariables(node: FigureNode): string[]` — function, line 146
- `function compileChecked(raw: FigureSpec | string): CompiledFigure` — function, line 162
- `const spec: FigureSpec = typeof raw === "string" ? (JSON.parse(raw) as FigureSpec) : raw` — const, line 163
- `const problems: string[] = []` — const, line 164
- `const problem = (text: string)` — const, line 165
- `const parameters = spec.parameters ?? []` — const, line 171
- `const params = new Set(parameters.map((parameter)` — const, line 172
- `const parse = (where: string, source: string): FigureNode | null` — const, line 173
- `const values = [parameter.min, parameter.max, parameter.step, parameter.default]` — const, line 183
- `const variables = new Set<string>()` — const, line 190
- `const advanced = panel as AdvancedPanel` — const, line 195
- `const parsedDefs: Array<[string, FigureNode | null]> = (spec.definitions ?? []).map((definition)` — const, line 202
- `const node = parse(`definition $` — const, line 203
- `const node = parse("expression", source)` — const, line 208
- `const definitions: Definitions = new Map()` — const, line 217
- `const needs = (where: string, node: FigureNode | null, allowed: Set<string>): FigureNode | null` — const, line 218
- `const missing = [...expandedFree(node, definitions)].filter((name)` — const, line 226
- `const checked = needs(`definition $` — const, line 238
- `const expr = (where: string, source: string, allowed: Set<string>)` — const, line 241
- `const advanced = new AdvancedCompiler(problem, expr, parameters, definitions, params)` — const, line 242
- `const panels: CompiledPanel[] = spec.panels.map((panel, index)` — const, line 243
- `const where = `panel $` — const, line 244
- `let nodes: Record<string, unknown> =` — let, line 245
- `const axis = panel.kind === "function_plot" ? panel.x : panel.k` — const, line 249
- `const allowed = new Set([...params, axis.var])` — const, line 259
- `const labels = panel.series.map((series)` — const, line 260
- `const readout = panel as ReadoutPanel` — const, line 274
- `const predictions = (spec.predictions ?? []).map((prediction, index)` — const, line 283
- `function allExpressions(spec: FigureSpec): string[]` — function, line 291
- `const sources: string[] = []` — const, line 292
- `const overlay = panel.heatmap ? [panel.heatmap.expr, ...(panel.heatmap.contours ?? [])] : []` — const, line 321
- `type Ranges = Map<string, [number, number]>` — type, line 333
- `function cellsOf(panel: HeatmapPanel | VectorFieldPanel, axis: GridAxis): number` — function, line 335
- `const heat = panel.kind === "heatmap_2d"` — const, line 336
- `const fallback = heat ? DEFAULT_HEATMAP_CELLS : DEFAULT_FIELD_CELLS` — const, line 337
- `const cap = heat ? MAX_HEATMAP_CELLS : MAX_FIELD_CELLS` — const, line 338
- `function overlayCells(overlay: FieldHeatmap): number` — function, line 342
- `function boundRange(node: FigureNode, parameters: FigureParameter[], ranges: Ranges): [number, number] | null` — function, line 346
- `const parameter = parameters.find((item)` — const, line 350
- `const range = ranges.get(node.text)` — const, line 352
- `function sumTerms(node: FigureNode, parameters: FigureParameter[], ranges: Ranges): number | null` — function, line 359
- `const lower = boundRange(node.args[1], parameters, ranges)` — const, line 360
- `const upper = boundRange(node.args[2], parameters, ranges)` — const, line 361
- `const low = Math.ceil(lower[0] - 1e-9)` — const, line 363
- `const high = Math.floor(upper[1] + 1e-9)` — const, line 364
- `const terms = sumTerms(node, parameters, ranges) ?? 0` — const, line 374
- `let total = 1` — let, line 379
- `const integerIn = (value: unknown, low: number, high: number): boolean` — const, line 384
- `class AdvancedCompiler` — class, line 387
- `const cellsOk = (value: unknown)` — const, line 408
- `const contours = panel.kind === "heatmap_2d" ? panel.contours : panel.heatmap?.contours` — const, line 411
- `const node = this.expr(where, source, allowed)` — const, line 423
- `const params = this.params` — const, line 444
- `const grid = new Set([panel.x.var, panel.y.var])` — const, line 446
- `const withGrid = new Set([...params, ...grid])` — const, line 447
- `const nodes: Record<string, unknown> =` — const, line 448
- `let work = 0` — let, line 449
- `const ranges: Ranges = new Map([[panel.x.var, [panel.x.min, panel.x.max]], [panel.y.var, [panel.y.min, panel.y.max]]])` — const, line 456
- `const points = (cellsOf(panel, panel.x) + 1) * (cellsOf(panel, panel.y) + 1)` — const, line 457
- `const side = overlayCells(panel.heatmap)` — const, line 467
- `const state = new Set(grid)` — const, line 474
- `const withState = new Set([...params, ...state])` — const, line 479
- `const none: Ranges = new Map()` — const, line 480
- `const num = (value: number): number | null` — const, line 508
- `const value = (node: FigureNode | null | undefined, env: Env, defs: Definitions): number` — const, line 509
- `const low = Math.trunc(axis.min)` — const, line 517
- `const count = Math.max(0, Math.min(Math.trunc(axis.max) - low + 1, MAX_BARS))` — const, line 518
- `const ks: number[] = []` — const, line 519
- `const model = panel.model as FunctionPlotPanel` — const, line 525
- `const shade = (model.shade ?? [])[shadeIndex]` — const, line 526
- `let lower = value(lowerNode, env, compiled.definitions)` — let, line 528
- `let upper = value(upperNode, env, compiled.definitions)` — let, line 529
- `const seriesIndex = model.series.map((series)` — const, line 532
- `const node = (panel.nodes.series as Array<FigureNode | null>)[seriesIndex]` — const, line 533
- `const variable = model.x.var` — const, line 534
- `const scope: Env = newEnv(env)` — const, line 535
- `const at = (t: number): number` — const, line 536
- `function highlightValue(compiled: CompiledFigure, panel: CompiledPanel, env: Env): [number, number, number]` — function, line 543
- `const model = panel.model as PmfBarsPanel` — const, line 544
- `let lower = value(lowerNode, env, compiled.definitions)` — let, line 546
- `let upper = value(upperNode, env, compiled.definitions)` — let, line 547
- `const node = (panel.nodes.series as Array<FigureNode | null>)[0]` — const, line 548
- `const variable = model.k.var` — const, line 549
- `const scope: Env = newEnv(env)` — const, line 550
- `const at = (k: number): number` — const, line 551
- `function gridValues(node: FigureNode | null, xs: number[], ys: number[], xv: string, yv: string, env: Env, defs: Definitions): Array<Array<number | null>>` — function, line 578
- `const scope: Env = newEnv(env)` — const, line 579
- `function heatmapData(node: FigureNode | null, contours: Array<FigureNode | null>, xs: number[], ys: number[], xv: string, yv: string, label: string, env: Env, defs: Definitions): HeatmapGridData` — function, line 589
- `const pad = (axis.max - axis.min) * ESCAPE_MARGIN` — const, line 595
- `function pathData(model: TrajectoryPanel | IteratePanel, nodes: Record<string, unknown>, env: Env, defs: Definitions): TrajectoryData | IterateData` — function, line 600
- `const xv = model.x.var` — const, line 601
- `const yv = model.y.var` — const, line 602
- `const trajectory = model.kind === "trajectory_2d"` — const, line 605
- `const time = model.kind === "trajectory_2d" ? model.time ?? null : null` — const, line 606
- `const scope: Env = newEnv(env)` — const, line 607
- `const xs: number[] = []` — const, line 608
- `const ys: number[] = []` — const, line 609
- `const steps: number[] = []` — const, line 610
- `let x = value(nodes.x0 as FigureNode | null, env, defs)` — let, line 611
- `let y = value(nodes.y0 as FigureNode | null, env, defs)` — let, line 612
- `const label = model.label ?? ""` — const, line 613
- `const done = (stopped: PathStop): TrajectoryData | IterateData` — const, line 614
- `const rates = (px: number, py: number, pt: number, first: FigureNode | null, second: FigureNode | null): [number, number]` — const, line 622
- `const dx = nodes.dx as FigureNode | null` — const, line 629
- `const dy = nodes.dy as FigureNode | null` — const, line 630
- `const count = Math.trunc(model.steps ?? DEFAULT_TRAJECTORY_STEPS)` — const, line 631
- `const h = value(nodes.t_max as FigureNode | null, env, defs) / count` — const, line 632
- `const half = h / 2` — const, line 634
- `let t = 0` — let, line 635
- `const nx = x + (h / 6) * (k1x + 2 * k2x + 2 * k3x + k4x)` — const, line 641
- `const ny = y + (h / 6) * (k1y + 2 * k2y + 2 * k3y + k4y)` — const, line 642
- `const fx = nodes.fx as FigureNode | null` — const, line 654
- `const fy = nodes.fy as FigureNode | null` — const, line 655
- `const count = Math.trunc(model.n ?? DEFAULT_ITERATIONS)` — const, line 656
- `function evaluateAdvanced(panel: CompiledPanel, env: Env, defs: Definitions): PanelData` — function, line 670
- `const model = panel.model as AdvancedPanel` — const, line 671
- `const nodes = panel.nodes` — const, line 672
- `const xs = gridPoints(model.x, cellsOf(model, model.x))` — const, line 674
- `const ys = gridPoints(model.y, cellsOf(model, model.y))` — const, line 675
- `const xs = gridPoints(model.x, cellsOf(model, model.x))` — const, line 679
- `const ys = gridPoints(model.y, cellsOf(model, model.y))` — const, line 680
- `let overlay: HeatmapGridData | null = null` — let, line 681
- `const side = overlayCells(model.heatmap)` — const, line 683
- `function sumIntegers(low: number, high: number): [number, number] | null` — function, line 702
- `const panel = compiled.panels[panelIndex]` — const, line 708
- `const defs = compiled.definitions` — const, line 709
- `const low = value(lowerNode, env, defs)` — const, line 712
- `const high = value(upperNode, env, defs)` — const, line 713
- `const clipped = (Number.isFinite(low) && low !== clampedLow) || (Number.isFinite(high) && high !== clampedHigh)` — const, line 715
- `const low = value(lowerNode, env, defs)` — const, line 720
- `const high = value(upperNode, env, defs)` — const, line 721
- `const clipped = (Number.isFinite(low) && low !== clampedLow) || (Number.isFinite(high) && high !== clampedHigh)` — const, line 723
- `const node = panel.nodes.expr as FigureNode` — const, line 726
- `const low = value(node.args[1], env, defs)` — const, line 727
- `const high = value(node.args[2], env, defs)` — const, line 728
- `const defs = compiled.definitions` — const, line 733
- `const model = panel.model as FunctionPlotPanel` — const, line 736
- `const xs = plotXs(model.x)` — const, line 737
- `const series = model.series.map((item, index)` — const, line 738
- `const node = (panel.nodes.series as Array<FigureNode | null>)[index]` — const, line 739
- `const scope: Env = newEnv(env)` — const, line 740
- `const shades = (model.shade ?? []).map((shade, index)` — const, line 749
- `const markers = (model.markers ?? []).map((marker, index)` — const, line 753
- `const model = panel.model as PmfBarsPanel` — const, line 760
- `const ks = barKs(model.k)` — const, line 761
- `const series = model.series.map((item, index)` — const, line 762
- `const node = (panel.nodes.series as Array<FigureNode | null>)[index]` — const, line 763
- `const scope: Env = newEnv(env)` — const, line 764
- `let highlight: PmfBarsData["highlight"] = null` — let, line 773
- `const m = (panel.nodes.matrix as Array<Array<FigureNode | null>>).map((row)` — const, line 781
- `const corners: Array<[number, number]> = [[0, 0], [a, c], [a + b, c + d], [b, d]]` — const, line 784
- `const model = panel.model as ReadoutPanel` — const, line 792
- `const env = defaults(compiled)` — const, line 800
- `const env = defaults(compiled)` — const, line 806

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/figures/AdvancedPanels|src/screens/reader/figures/AdvancedPanels.tsx]] — import-or-re-export: `ESCAPE_MARGIN`, `HeatmapGridData`, `IterateData`, `TrajectoryData`, `VectorFieldData`; references `ESCAPE_MARGIN`, `HeatmapGridData`, `IterateData`, `TrajectoryData`, `VectorFieldData`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export: `CompiledFigure`, `FigureParameter`, `compileSpec`, `evaluateFigure`; references `CompiledFigure`, `FigureParameter`, `compileSpec`, `evaluateFigure`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigurePanels|src/screens/reader/figures/FigurePanels.tsx]] — import-or-re-export: `FigurePanelModel`, `FunctionPlotData`, `LinearMapData`, `PanelData`, `PmfBarsData`, `ReadoutData`; references `FigurePanelModel`, `FunctionPlotData`, `LinearMapData`, `PanelData`, `PmfBarsData`, `ReadoutData`
- [[Reference/Desktop/TypeScript/screens/reader/figures/figureLabels|src/screens/reader/figures/figureLabels.tsx]] — import-or-re-export: `CompiledFigure`, `DerivedBounds`, `defaults`, `derivedBounds`; references `CompiledFigure`, `DerivedBounds`, `defaults`, `derivedBounds`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/reader/figures/figureGrammar|src/screens/reader/figures/figureGrammar.ts]] — import-or-re-export; imports `CONSTANTS`, `Definitions`, `Env`, `FigureGrammarError`, `FigureNode`, `MAX_SAFE_INTEGER`, `MAX_SUM_TERMS`, `RESERVED`, `adaptiveSimpson`, `canonical`, `checkNames`, `evaluate`, `exactSum`, `expansion`, `isName`, `newEnv`, `parseExpression`, `walk`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/figures/richFigure.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/richFigure.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/figuresFollowSection.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figuresFollowSection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/figurePanels.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figurePanels.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/figureGrammar.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figureGrammar.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/figureDisplayCorpus.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figureDisplayCorpus.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/FigureInline.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/FigureInline.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_figure_panels.py](../../../../../../../../tests/test_figure_panels.py) — cross-boundary name contract: references uniquely owned exported names `ADVANCED_KINDS`, `MAX_FIELD_CELLS`, `MAX_HEATMAP_CELLS`, `MAX_ITERATIONS`; it does **not** directly execute this source module.
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

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/figureSpec.ts](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figureSpec.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

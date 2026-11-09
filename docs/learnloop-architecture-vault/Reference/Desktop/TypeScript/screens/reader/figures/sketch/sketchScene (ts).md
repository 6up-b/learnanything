---
title: "Desktop module · src/screens/reader/figures/sketch/sketchScene.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.sketch.sketchScene"
language: "TypeScript"
area: "TypeScript/screens/reader/figures/sketch"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchScene.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchScene.ts"
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

# `src/screens/reader/figures/sketch/sketchScene.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `SKETCH_MAX_ELEMENTS`, `SKETCH_MAX_POINTS`, `SKETCH_MAX_CELLS`, `SKETCH_MAX_SERIES` and related exports within the desktop's TypeScript/screens/reader/figures/sketch ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchScene.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchScene.ts) |
| Source lines | 374 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchScene (ts)|src/screens/reader/figures/sketch/sketchScene.ts]]

## Public API

- `export const SKETCH_MAX_ELEMENTS = 4_000` — const, line 13
- `export const SKETCH_MAX_POINTS = 40_000` — const, line 14
- `export const SKETCH_MAX_CELLS = 4_096` — const, line 15
- `export const SKETCH_MAX_SERIES = 4_000` — const, line 16
- `export const MAX_LABEL = 80` — const, line 17
- `export const MAX_VIEWPORT_SPAN = 1e12` — const, line 18
- `export const COLORS = ["series0", "series1", "series2", "series3", "muted", "accent"] as const` — const, line 19
- `export const ELEMENT_KINDS = ["polyline", "polygon", "points", "segment", "arrow", "circle", "rect", "text", "heat_cells", "handle"] as const` — const, line 20
- `export const CHECK_WORDS = ["check", "verif", "learnloop", "sandbox", "book", "tested", "proof", "correct"] as const` — const, line 22
- `export type SketchColor = (typeof COLORS)[number]` — type, line 25
- `export type SketchStyle =` — type, line 26
- `export type SketchElement = |` — type, line 27
- `export type Scene =` — type, line 36
- `export type SketchParameter =` — type, line 42
- `export type SketchProbe =` — type, line 43
- `export type SketchPrediction =` — type, line 44
- `export type SketchProgram =` — type, line 49
- `export function parseProgram(specJson: string | null | undefined): SketchProgram | null` — function, line 62
- `export function clockSteps(program: SketchProgram): number` — function, line 74
- `export const SKETCH_TIME_SAMPLES = 9` — const, line 81
- `export function tickSteps(total: number): number[]` — function, line 84
- `export function sampleSteps(total: number): number[]` — function, line 94
- `export function predictionStep(program: SketchProgram, index: number): number` — function, line 102
- `export function readSchedule(program: SketchProgram): number[]` — function, line 116
- `export function usableSchedule(steps: unknown, program: SketchProgram): number[] | null` — function, line 124
- `export function impersonates(name: string): boolean` — function, line 133
- `export function sceneProblems(scene: unknown, parameters: readonly string[] = []): string[]` — function, line 201
- `export function probeProblems(values: unknown, probes: readonly SketchProbe[]): string[]` — function, line 348

## Internal implementation anchors

- `const ID = /^[A-Za-z][A-Za-z0-9_-]` — const, line 23
- `const data = JSON.parse(specJson) as SketchProgram` — const, line 65
- `const clock = program.clock` — const, line 75
- `const per = Math.max(1, Math.ceil(total / PLAY_TICKS))` — const, line 86
- `const steps: number[] = []` — const, line 87
- `const steps = new Set<number>()` — const, line 96
- `const total = clockSteps(program)` — const, line 103
- `const change = program.predictions?.[index]?.change ??` — const, line 104
- `const keys = Object.keys(change)` — const, line 105
- `const total = clockSteps(program)` — const, line 117
- `const steps = new Set<number>([...tickSteps(total), ...sampleSteps(total)])` — const, line 118
- `const total = clockSteps(program)` — const, line 125
- `const folded = String(name).toLowerCase()` — const, line 134
- `function finite(value: unknown): value is number` — function, line 138
- `function describe(value: unknown): string` — function, line 142
- `function isPlainObject(value: unknown): value is Record<string, unknown>` — function, line 152
- `function keys(value: Record<string, unknown>): string[]` — function, line 156
- `class Problems` — class, line 160
- `function numbers(problems: Problems, where: string, value: unknown, limit: number): number[] | null` — function, line 167
- `const STYLE_KEYS = new Set(["color", "dash", "width", "fill", "opacity"])` — const, line 185
- `const COMMON = ["type", "id", "style"]` — const, line 186
- `const ELEMENT_KEYS: Record<string, Set<string>> =` — const, line 187
- `const problems = new Problems()` — const, line 202
- `const extra = keys(scene).filter((key)` — const, line 204
- `const viewport = scene.viewport` — const, line 206
- `const pair = numbers(problems, `viewport.$` — const, line 211
- `const axes = scene.axes` — const, line 217
- `const elements = scene.elements` — const, line 227
- `const known = new Set(parameters)` — const, line 236
- `const ids = new Set<string>()` — const, line 237
- `let points = 0` — let, line 238
- `const element = elements[index]` — const, line 241
- `let where = `element $` — let, line 242
- `const kind = element.type` — const, line 247
- `const extraKeys = keys(element).filter((key)` — const, line 253
- `const id = element.id` — const, line 258
- `const style = element.style` — const, line 268
- `const need = (...names: string[])` — const, line 281
- `const xs = numbers(problems, `$` — const, line 287
- `const ys = numbers(problems, `$` — const, line 288
- `const text = element.text` — const, line 309
- `const pair = numbers(problems, `$` — const, line 314
- `const cols = element.cols` — const, line 317
- `const rows = element.rows` — const, line 318
- `const values = numbers(problems, `$` — const, line 323
- `const binds = element.binds` — const, line 329
- `const problems = new Problems()` — const, line 349
- `const value = values[probe.name]` — const, line 356
- `const pair = value[index]` — const, line 365

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export: `parseProgram`; references `parseProgram`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] — import-or-re-export: `Scene`, `SketchParameter`, `SketchProbe`, `SketchProgram`, `clockSteps`, `probeProblems`, `readSchedule`, `sceneProblems`, `usableSchedule`; references `Scene`, `SketchParameter`, `SketchProbe`, `SketchProgram`, `clockSteps`, `probeProblems`, `readSchedule`, `sceneProblems`, `usableSchedule`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchScene (tsx)|src/screens/reader/figures/sketch/SketchScene.tsx]] — import-or-re-export: `Scene`, `SketchColor`, `SketchElement`, `SketchStyle`; references `Scene`, `SketchColor`, `SketchElement`, `SketchStyle`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchEngine|src/screens/reader/figures/sketch/sketchEngine.ts]] — import-or-re-export; imports `PLAY_TICKS`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchScene.test.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchScene.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchSandboxReview.test.tsx](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchSandboxReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.test.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sketch_verify.py](../../../../../../../../../tests/test_sketch_verify.py) — cross-boundary name contract: references uniquely owned exported names `SKETCH_MAX_ELEMENTS`, `SKETCH_MAX_POINTS`, `SKETCH_MAX_SERIES`; it does **not** directly execute this source module.
- [tests/test_sidecar_reader.py](../../../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchScene.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchScene.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

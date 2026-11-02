---
title: "Desktop module · src/screens/reader/figures/sketch/SketchScene.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.sketch.SketchScene"
language: "TypeScript"
area: "TypeScript/screens/reader/figures/sketch"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchScene.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchScene.tsx"
source_commit: "8427228c2d6ecbf8bf612e57a5e1d5d0c0d7fb6b"
source_commit_timestamp: "2026-10-31T14:41:14-04:00"
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

# `src/screens/reader/figures/sketch/SketchScene.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `SketchScene` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchScene.tsx](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchScene.tsx) |
| Source lines | 188 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `8427228c2d6ecbf8bf612e57a5e1d5d0c0d7fb6b` |
| Commit timestamp | `2026-10-31T14:41:14-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchScene (tsx)|src/screens/reader/figures/sketch/SketchScene.tsx]]

## Public API

- `export const SCENE_W = 600` — const, line 14
- `export const SCENE_H = 300` — const, line 15
- `export type Scale =` — type, line 27
- `export function sceneScale(scene: Scene): Scale` — function, line 29
- `export function SketchSceneView(` — function, line 130

## Internal implementation anchors

- `const PAD =` — const, line 16
- `const PALETTE: Record<SketchColor, string> =` — const, line 18
- `const width = SCENE_W - PAD.left - PAD.right` — const, line 32
- `const height = SCENE_H - PAD.top - PAD.bottom` — const, line 33
- `function stroke(style: SketchStyle | undefined, fallback: SketchColor = "series0")` — function, line 41
- `const color = PALETTE[style?.color ?? fallback] ?? PALETTE[fallback]` — const, line 42
- `function cellColor(value: number, low: number, high: number): string` — function, line 51
- `const share = high > low ? (value - low) / (high - low) : 0.5` — const, line 52
- `const percent = Math.round(Math.min(1, Math.max(0, share)) * 100)` — const, line 53
- `function Element(` — function, line 57
- `const key = element.type === "handle" ? element.id : `$` — const, line 58
- `const points = element.x.map((x, i)` — const, line 62
- `const paint = stroke(element.style)` — const, line 63
- `const paint = stroke(element.style)` — const, line 71
- `const r = element.r ?? 2` — const, line 72
- `const rx = Math.abs(scale.x(element.cx + element.r) - scale.x(element.cx))` — const, line 85
- `const ry = Math.abs(scale.y(element.cy + element.r) - scale.y(element.cy))` — const, line 86
- `const paint = stroke(element.style)` — const, line 87
- `const left = scale.x(element.x)` — const, line 92
- `const right = scale.x(element.x + element.w)` — const, line 93
- `const top = scale.y(element.y + element.h)` — const, line 94
- `const bottom = scale.y(element.y)` — const, line 95
- `const paint = stroke(element.style, "muted")` — const, line 96
- `const low = Math.min(...element.values)` — const, line 106
- `const high = Math.max(...element.values)` — const, line 107
- `const cw = (element.x[1] - element.x[0]) / element.cols` — const, line 108
- `const ch = (element.y[1] - element.y[0]) / element.rows` — const, line 109
- `const col = i % element.cols` — const, line 113
- `const row = Math.floor(i / element.cols)` — const, line 114
- `const x = element.x[0] + col * cw` — const, line 115
- `const y = element.y[1] - (row + 1) * ch` — const, line 116
- `const left = scale.x(x)` — const, line 117
- `const top = scale.y(y + ch)` — const, line 118
- `const scale = sceneScale(scene)` — const, line 140
- `const svg = useRef<SVGSVGElement | null>(null)` — const, line 141
- `const dragging = useRef<string | null>(null)` — const, line 142
- `const toData = (event: PointerEvent<SVGElement>): [number, number] | null` — const, line 143
- `const node = svg.current` — const, line 144
- `const box = node.getBoundingClientRect()` — const, line 146
- `const px = box.width ? ((event.clientX - box.left) / box.width) * SCENE_W : event.clientX` — const, line 147
- `const py = box.height ? ((event.clientY - box.top) / box.height) * SCENE_H : event.clientY` — const, line 148
- `const svgStyle: CSSProperties =` — const, line 151
- `const handles = scene.elements.filter((element): element is Extract<SketchElement,` — const, line 152
- `const point = toData(event)` — const, line 157

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] — import-or-re-export: `SketchSceneView`; references `SketchSceneView`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchScene (ts)|src/screens/reader/figures/sketch/sketchScene.ts]] — import-or-re-export; imports `Scene`, `SketchColor`, `SketchElement`, `SketchStyle`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

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

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchScene.tsx](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchScene.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

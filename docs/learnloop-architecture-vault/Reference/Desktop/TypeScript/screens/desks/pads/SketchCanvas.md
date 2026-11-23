---
title: "Desktop module · src/screens/desks/pads/SketchCanvas.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.pads.SketchCanvas"
language: "TypeScript"
area: "TypeScript/screens/desks/pads"
source_path: "apps/learnloop-tauri/src/screens/desks/pads/SketchCanvas.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/pads/SketchCanvas.tsx"
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

# `src/screens/desks/pads/SketchCanvas.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `SketchCanvas` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/pads/SketchCanvas.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/SketchCanvas.tsx) |
| Source lines | 197 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pads/SketchCanvas|src/screens/desks/pads/SketchCanvas.tsx]]

## Public API

- `export type SketchTool = "pen" | "line" | "arrow" | "box" | "text" | "eraser"` — type, line 7
- `export type SketchItem = |` — type, line 9
- `export interface SketchPayload` — interface, line 15
- `export const SKETCH_SIZES =` — const, line 21
- `export const SKETCH_TOOLS: Array<` — const, line 23
- `export function readSketch(payload: Record<string, unknown>): SketchPayload` — function, line 32
- `export function smoothPath(points: Array<` — function, line 42
- `export function hits(item: SketchItem, x: number, y: number, within = 8): boolean` — function, line 59
- `export function SketchCanvas(` — function, line 81

## Internal implementation anchors

- `const items = Array.isArray(payload.items) ? (payload.items as SketchItem[]) : []` — const, line 33
- `let d = `M$` — let, line 45
- `const mid =` — const, line 47
- `const last = points[points.length - 1]` — const, line 50
- `function round(value: number): number` — function, line 54
- `const dx = item.x2 - item.x1` — const, line 67
- `const dy = item.y2 - item.y1` — const, line 68
- `const length = dx * dx + dy * dy || 1` — const, line 69
- `const t = Math.max(0, Math.min(1, ((x - item.x1) * dx + (y - item.y1) * dy) / length))` — const, line 70
- `const numbers = item.d.match(/-?\d+(\.\d+)?/g)?.map(Number) ?? []` — const, line 74
- `const sketch = readSketch(payload)` — const, line 88
- `const points = useRef<Array<` — const, line 92
- `const start = useRef<` — const, line 93
- `const svgRef = useRef<SVGSVGElement | null>(null)` — const, line 94
- `const pressure = useRef(1)` — const, line 95
- `const at = (event: React.PointerEvent):` — const, line 99
- `const box = svgRef.current?.getBoundingClientRect()` — const, line 100
- `const scale = box && box.width > 0 && box.height > 0 ? Math.min(box.width / sketch.width, box.height / height) : 1` — const, line 101
- `const grow = (y: number)` — const, line 104
- `const commit = (items: SketchItem[], nextHeight = height)` — const, line 107
- `const onDown = (event: React.PointerEvent<SVGSVGElement>)` — const, line 109
- `const p = at(event)` — const, line 111
- `const kept = sketch.items.filter((item)` — const, line 115
- `const text = onTextPrompt ? onTextPrompt() : typeof window !== "undefined" ? window.prompt("text") : null` — const, line 120
- `const onMove = (event: React.PointerEvent<SVGSVGElement>)` — const, line 127
- `const s = start.current` — const, line 128
- `const p = at(event)` — const, line 130
- `const onUp = ()` — const, line 141
- `const drawn = draft ? [...sketch.items, draft] : sketch.items` — const, line 148

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] — import-or-re-export: `SketchCanvas`; references `SketchCanvas`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/pads/SketchCanvas.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/SketchCanvas.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/pads/SketchCanvas.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/SketchCanvas.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

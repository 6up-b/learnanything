---
title: "Desktop module · src/screens/desks/pen/InkLine.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.pen.InkLine"
language: "TypeScript"
area: "TypeScript/screens/desks/pen"
source_path: "apps/learnloop-tauri/src/screens/desks/pen/InkLine.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/pen/InkLine.tsx"
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

# `src/screens/desks/pen/InkLine.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/pen/_area|TypeScript/screens/desks/pen]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `InkLine` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/pen/InkLine.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/InkLine.tsx) |
| Source lines | 292 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/pen/_area|TypeScript/screens/desks/pen]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pen/InkLine|src/screens/desks/pen/InkLine.tsx]]

## Public API

- `export const RULE_PX = 52` — const, line 18
- `export function surfaceHeight(strokes: ReadonlyArray<` — function, line 33
- `export interface InkBlockProps` — interface, line 148
- `export function InkBlock(` — function, line 159
- `export function InkJot(` — function, line 264

## Internal implementation anchors

- `const PEN_WIDTH = 2.2` — const, line 20
- `type Point6 = [number, number, number, number, number, number]` — type, line 22
- `function round(value: number): number` — function, line 24
- `function pathOf(points: ReadonlyArray<readonly number[]>): string` — function, line 28
- `const bottom = Math.max(0, ...strokes.flatMap((stroke)` — const, line 34
- `interface SurfaceProps` — interface, line 38
- `function InkSurface(` — function, line 51
- `const hostRef = useRef(host)` — const, line 52
- `const input = useMemo(()` — const, line 54
- `const ref = useRef<HTMLDivElement | null>(null)` — const, line 55
- `const drew = useRef(false)` — const, line 58
- `const erased = useRef(new Set<string>())` — const, line 61
- `const local = (samples: Sample[]): Point6[]` — const, line 62
- `const box = ref.current?.getBoundingClientRect() ??` — const, line 63
- `const height = surfaceHeight([...strokes, ...(live ? [` — const, line 73
- `const outcome = input.down(event.nativeEvent as unknown as PointerLike, hostRef.current.on)` — const, line 83
- `const samples = input.move(event.nativeEvent as unknown as PointerLike)` — const, line 103
- `const hit = new Set<string>()` — const, line 106
- `const stroke = input.up(event.nativeEvent as unknown as PointerLike)` — const, line 120
- `function pointerMeta(pointerType: "pen" | "mouse")` — function, line 144
- `const host = usePenHost()` — const, line 160
- `function InkBlockOn(` — function, line 165
- `const cache = host.ink` — const, line 166
- `const pad = cache.pad(padId)` — const, line 168
- `const line = pad.lines[block.blockId]` — const, line 169
- `const reading = pad.readings[block.blockId]` — const, line 170
- `const strokes = line?.strokes ?? []` — const, line 172
- `const words = block.bodyMd.trim()` — const, line 173
- `const corrected = block.provenance === "learner_correction"` — const, line 174
- `const keep = (text: string)` — const, line 176
- `let status: ReactNode = null` — let, line 183
- `const offered = reading.result.latexMd` — const, line 191
- `const inkId = host.mintId("ink")` — const, line 209
- `const all = (cache.pad(padId).lines[block.blockId]?.strokes ?? []).every((stroke)` — const, line 217
- `const read = block.provenance === "ink_transcription" && (words !== "" || "ink_transcription" in block.payload)` — const, line 218
- `const op: PadOpDto =` — const, line 219
- `const host = usePenHost()` — const, line 272
- `const blockId = newLine()` — const, line 281
- `const inkId = host.mintId("ink")` — const, line 283

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] — import-or-re-export: `InkBlock`, `InkJot`; references `InkBlock`, `InkJot`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `InkStrokeDto`, `PadBlockDto`, `PadOpDto`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/desks/fitMath|src/screens/desks/fitMath.tsx]] — import-or-re-export; imports `FitMath`
- [[Reference/Desktop/TypeScript/screens/desks/pen/geometry|src/screens/desks/pen/geometry.ts]] — import-or-re-export; imports `distanceToPolyline`
- [[Reference/Desktop/TypeScript/screens/desks/pen/host|src/screens/desks/pen/host.ts]] — import-or-re-export; imports `PenHost`, `usePenHost`
- [[Reference/Desktop/TypeScript/screens/desks/pen/input|src/screens/desks/pen/input.ts]] — import-or-re-export; imports `PenInput`, `PointerLike`, `Sample`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck`, `npm test` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/pen/InkLine.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/InkLine.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

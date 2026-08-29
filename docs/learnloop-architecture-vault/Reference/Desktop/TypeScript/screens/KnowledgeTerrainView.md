---
title: "Desktop module · src/screens/KnowledgeTerrainView.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.KnowledgeTerrainView"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/KnowledgeTerrainView.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/KnowledgeTerrainView.tsx"
source_commit: "971d7c274e09873d726d43578cd080e4d8865571"
source_commit_timestamp: "2026-07-27T06:01:19-04:00"
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

# `src/screens/KnowledgeTerrainView.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `KnowledgeTerrainView` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/KnowledgeTerrainView.tsx](../../../../../../apps/learnloop-tauri/src/screens/KnowledgeTerrainView.tsx) |
| Source lines | 437 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `971d7c274e09873d726d43578cd080e4d8865571` |
| Commit timestamp | `2026-07-27T06:01:19-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/KnowledgeTerrainView|src/screens/KnowledgeTerrainView.tsx]]

## Public API

- `export function KnowledgeTerrainView(` — function, line 235

## Internal implementation anchors

- `const DEFAULT_W = 860` — const, line 18
- `const DEFAULT_H = 600` — const, line 19
- `const CENTER_DROP = 0.07` — const, line 20
- `const SCALE_W = 0.2767` — const, line 21
- `const SCALE_H = 0.3967` — const, line 22
- `const GX = 38` — const, line 24
- `const GY = 27` — const, line 25
- `const TAU = 0.72` — const, line 26
- `const DEMO_DEPTH = 0.56` — const, line 27
- `const READY_OFFSET = 0.3` — const, line 28
- `const READY_DEPTH = 0.24` — const, line 29
- `type MassKey = "demonstratedMass" | "ready"` — type, line 31
- `interface Cell` — interface, line 33
- `interface Segment` — interface, line 40
- `const clamp01 = (value: number)` — const, line 50
- `function diffuse(field: KnowledgeFacetField, key: MassKey): Map<string, number>` — function, line 52
- `const pointById = new Map(field.points.map((point)` — const, line 53
- `const neighbors = new Map<string, Array<` — const, line 54
- `const mass = new Map<string, number>()` — const, line 60
- `const point = pointById.get(node)` — const, line 62
- `let values = new Map(mass)` — let, line 65
- `const next = new Map<string, number>()` — const, line 68
- `const links = neighbors.get(node) ?? []` — const, line 70
- `const degree = links.reduce((sum, link)` — const, line 71
- `const neighborMass = links.reduce( (sum, link)` — const, line 72
- `function buildCells(field: KnowledgeFacetField): Cell[][]` — function, line 83
- `const visible = field.points.filter((point)` — const, line 84
- `const demoPotential = diffuse(field, "demonstratedMass")` — const, line 85
- `const readyPotential = diffuse(field, "ready")` — const, line 86
- `const rows: Cell[][] = []` — const, line 87
- `let maxDemo = 0` — let, line 88
- `let maxReady = 0` — let, line 89
- `const y = -1 + (2 * gy) / GY` — const, line 91
- `const row: Cell[] = []` — const, line 92
- `const x = -1 + (2 * gx) / GX` — const, line 94
- `let demo = 0` — let, line 95
- `let ready = 0` — let, line 96
- `let confidenceWeight = 0` — let, line 97
- `let confidence = 0` — let, line 98
- `let nearest = Number.POSITIVE_INFINITY` — let, line 99
- `const d2 = (point.x - x) ** 2 + (point.y - y) ** 2` — const, line 101
- `const distance = Math.sqrt(d2)` — const, line 106
- `const weight = 1 / (distance + 0.075)` — const, line 107
- `const evidenceConfidence = (point.evidenceMass / (point.evidenceMass + 1)) * (1 / (1 + 18 * point.readyVariance))` — const, line 108
- `const presence = visible.length ? clamp01(1 - Math.sqrt(nearest) / 1.15) : 0` — const, line 118
- `const maxPotential = Math.max(maxDemo, maxReady)` — const, line 131
- `function sample(cells: Cell[][], x: number, y: number): Cell` — function, line 141
- `const fx = clamp01((x + 1) / 2) * GX` — const, line 142
- `const fy = clamp01((y + 1) / 2) * GY` — const, line 143
- `const gx = Math.min(GX - 1, Math.floor(fx))` — const, line 144
- `const gy = Math.min(GY - 1, Math.floor(fy))` — const, line 145
- `const tx = fx - gx` — const, line 146
- `const ty = fy - gy` — const, line 147
- `const mix = (key: keyof Cell)` — const, line 148
- `const top = cells[gy][gx][key] * (1 - tx) + cells[gy][gx + 1][key] * tx` — const, line 149
- `const bottom = cells[gy + 1][gx][key] * (1 - tx) + cells[gy + 1][gx + 1][key] * tx` — const, line 150
- `function sheetZ(cell: Cell)` — function, line 156
- `const demo = -DEMO_DEPTH * cell.demo` — const, line 157
- `const predicted = READY_OFFSET - READY_DEPTH * cell.ready` — const, line 158
- `function meshSegments(cells: Cell[][], sheet: "demo" | "ready"): Segment[]` — function, line 162
- `const out: Segment[] = []` — const, line 163
- `const world = (gx: number, gy: number)` — const, line 164
- `const push = (ax: number, ay: number, bx: number, by: number)` — const, line 165
- `const a = cells[ay][ax]` — const, line 166
- `const b = cells[by][bx]` — const, line 167
- `const pa = world(ax, ay)` — const, line 169
- `const pb = world(bx, by)` — const, line 170
- `function arcPath(cx: number, cy: number, radius: number, index: number): string` — function, line 186
- `const start = -Math.PI / 2 + (index * Math.PI * 2) / 5 + 0.08` — const, line 187
- `const end = -Math.PI / 2 + ((index + 1) * Math.PI * 2) / 5 - 0.08` — const, line 188
- `function arcStyle(status: CapabilityArcStatus):` — function, line 192
- `function gapGlyph(kind: NonNullable<KnowledgeFacetField["nextGap"]>["kind"], x: number, y: number)` — function, line 198
- `function FlatTopology(` — function, line 205
- `const byId = new Map(field.points.map((point)` — const, line 213
- `const SCALE = Math.min(W * SCALE_W, H * SCALE_H)` — const, line 214
- `const sx = (x: number)` — const, line 215
- `const sy = (y: number)` — const, line 216
- `const a = byId.get(edge.source)` — const, line 221
- `const b = byId.get(edge.target)` — const, line 222
- `const W = width && width > 0 ? width : DEFAULT_W` — const, line 251
- `const H = height && height > 0 ? height : DEFAULT_H` — const, line 252
- `const CX = W / 2` — const, line 253
- `const CY = H / 2 + H * CENTER_DROP` — const, line 254
- `const SCALE = Math.min(W * SCALE_W, H * SCALE_H)` — const, line 255
- `const cells = useMemo(()` — const, line 258
- `const demo = useMemo(()` — const, line 259
- `const ready = useMemo(()` — const, line 260
- `const view =` — const, line 261
- `const proj = (x: number, y: number, z: number)` — const, line 262
- `const groupSheet = (segments: Segment[], prediction: boolean)` — const, line 264
- `const groups = new Map<string,` — const, line 265
- `const a = proj(segment.ax, segment.ay, segment.az)` — const, line 267
- `const b = proj(segment.bx, segment.by, segment.bz)` — const, line 268
- `const depth = Math.max(0, Math.min(2, Math.floor(depthFade((a.depth + b.depth) / 2, 0, 1) * 3)))` — const, line 269
- `const certainty = prediction ? Math.max(0, Math.min(3, Math.floor(segment.confidence * 4))) : 3` — const, line 270
- `const key = `$` — const, line 271
- `const opacity = prediction ? (0.08 + certainty * 0.08) * (0.7 + depth * 0.13) : 0.34 * (0.72 + depth * 0.14)` — const, line 272
- `const group = groups.get(key) ??` — const, line 275
- `const demoGroups = groupSheet(demo, false)` — const, line 282
- `const readyGroups = groupSheet(ready, true)` — const, line 283
- `const pointById = new Map(field.points.map((point)` — const, line 284
- `const pins = field.points .map((point)` — const, line 285
- `const z = sheetZ(sample(cells, point.x, point.y))` — const, line 287
- `const pathPoints = (field.nextGap?.pathFacetIds ?? []) .map((id)` — const, line 292
- `const z = sheetZ(sample(cells, point.x, point.y)).demo - 0.008` — const, line 296
- `const pathD = pathPoints.length > 1 ? `M $` — const, line 299
- `const floor = [proj(-1, -1, 0), proj(1, -1, 0), proj(1, 1, 0), proj(-1, 1, 0)]` — const, line 303
- `const floorD = `M $` — const, line 304
- `const active = point.id === selected` — const, line 340
- `const fade = depthFade(demoPoint.depth, 0.58, 1)` — const, line 341
- `const radius = active ? 10 : 8` — const, line 342
- `const tooltip = `$` — const, line 343
- `const style = arcStyle(arc.status)` — const, line 372
- `const candidatePoint = pointById.get(candidate)` — const, line 386
- `const candidateZ = sheetZ(sample(cells, candidatePoint.x, candidatePoint.y)).demo` — const, line 388
- `const ghost = proj(candidatePoint.x, candidatePoint.y, candidateZ - 0.012 - index * 0.002)` — const, line 389
- `const ghost = proj(point.x, point.y, READY_OFFSET - READY_DEPTH * point.readyGhost)` — const, line 404
- `const point = pointById.get(field.nextGap.facetId)` — const, line 419
- `const base = proj(point.x, point.y, sheetZ(sample(cells, point.x, point.y)).demo - 0.035)` — const, line 421

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export: `KnowledgeTerrainView`; references `KnowledgeTerrainView`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CapabilityArcStatus`, `KnowledgeFacetField`, `KnowledgeFacetPoint`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/wire3d|src/screens/wire3d.ts]] — import-or-re-export; imports `depthFade`, `project`, `useOrbitCamera`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Build a Study Map|Build a Study Map]] — owns the map-building journey.
- [[Concepts/Canonical Knowledge Model#Core entities|canonical knowledge entities]] — owns graph meaning.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_sidecar_knowledge_model.py](../../../../../../tests/test_sidecar_knowledge_model.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_graph_edit_proposals.py](../../../../../../tests/test_graph_edit_proposals.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_build_study_map_routing.py](../../../../../../tests/test_build_study_map_routing.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/KnowledgeTerrainView.tsx](../../../../../../apps/learnloop-tauri/src/screens/KnowledgeTerrainView.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

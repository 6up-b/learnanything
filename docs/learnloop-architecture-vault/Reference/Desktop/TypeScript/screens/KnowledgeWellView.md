---
title: "Desktop module · src/screens/KnowledgeWellView.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.KnowledgeWellView"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/KnowledgeWellView.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/KnowledgeWellView.tsx"
source_commit: "d0f25b2598a77dcc5236118dad9e1af2422d8682"
source_commit_timestamp: "2026-08-16T20:45:34-04:00"
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

# `src/screens/KnowledgeWellView.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `KnowledgeWellView` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/KnowledgeWellView.tsx](../../../../../../apps/learnloop-tauri/src/screens/KnowledgeWellView.tsx) |
| Source lines | 727 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `d0f25b2598a77dcc5236118dad9e1af2422d8682` |
| Commit timestamp | `2026-08-16T20:45:34-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/KnowledgeWellView|src/screens/KnowledgeWellView.tsx]]

## Public API

- `export function KnowledgeWellView(` — function, line 271

## Internal implementation anchors

- `const DEFAULT_W = 860` — const, line 31
- `const DEFAULT_H = 640` — const, line 32
- `const CENTER_LIFT = 0.047` — const, line 33
- `const SCALE_W = 0.273` — const, line 34
- `const SCALE_H = 0.42` — const, line 35
- `const DEPTH = 0.9` — const, line 37
- `const CENTER_BLEND = 0.28` — const, line 38
- `const PROFILE_POW = 1.55` — const, line 39
- `const EVIDENCE_K = 1.2` — const, line 40
- `const DEMO_THRESHOLD = 0.5` — const, line 41
- `const DEEP_LEVEL = 0.4` — const, line 42
- `const SHALLOW_LEVEL = 0.12` — const, line 43
- `const BEAD_R = 0.52` — const, line 44
- `const RING_RS = [0.14, 0.28, 0.42, 0.56, 0.7, 0.84, 1]` — const, line 45
- `const CONTOUR_QS = [0.12, 0.24, 0.36, 0.48, 0.6, 0.72]` — const, line 46
- `const SPOKE_STEPS = 26` — const, line 47
- `const EASE = "stroke 0.22s ease, fill 0.22s ease, opacity 0.22s ease, stroke-width 0.22s ease"` — const, line 48
- `const clamp01 = (value: number)` — const, line 50
- `const smooth = (t: number)` — const, line 51
- `const visibility = (evidenceMass: number)` — const, line 52
- `type V3 =` — type, line 54
- `function labelLines(facetId: string, maxChars = 20): string[]` — function, line 57
- `const words = facetId.split("_")` — const, line 58
- `const lines: string[] = []` — const, line 59
- `let current = ""` — let, line 60
- `const candidate = current ? `$` — const, line 62
- `interface FacetState` — interface, line 76
- `function decayByFacet(decay: DecayPressureDto | null | undefined): Map<string,` — function, line 97
- `const out = new Map<string,` — const, line 98
- `const prev = out.get(row.facetId)` — const, line 100
- `const crosses = [prev?.crossesInDays, row.crossesInDays].filter((v): v is number` — const, line 101
- `function buildStates(field: KnowledgeFacetField, decay: DecayPressureDto | null | undefined): FacetState[]` — function, line 110
- `const points = [...field.points].sort((a, b)` — const, line 113
- `const N = points.length` — const, line 114
- `const decayMap = decayByFacet(decay)` — const, line 115
- `const vis = visibility(point.evidenceMass)` — const, line 117
- `const wellDepth = clamp01(point.ready) * vis` — const, line 118
- `const ghostDepth = clamp01(point.readyGhost) * vis` — const, line 119
- `const absent = !point.hasBlueprints` — const, line 120
- `const entry = decayMap.get(point.id)` — const, line 121
- `const noHistory = entry != null && !entry.hasHistory` — const, line 125
- `const demonstrated = point.demonstratedMass >= DEMO_THRESHOLD` — const, line 126
- `interface WellGeometry` — interface, line 148
- `function buildGeometry(states: FacetState[]): WellGeometry` — function, line 157
- `const N = states.length` — const, line 158
- `const meanDepth = states.reduce((sum, s)` — const, line 159
- `const depthAtAngle = (theta: number): number` — const, line 163
- `const u = (((theta + Math.PI / 2) / (2 * Math.PI)) * N) % N` — const, line 164
- `const uu = u < 0 ? u + N : u` — const, line 165
- `const i0 = Math.floor(uu) % N` — const, line 166
- `const t = uu - Math.floor(uu)` — const, line 167
- `const d0 = states[i0].effectiveDepth` — const, line 168
- `const d1 = states[(i0 + 1) % N].effectiveDepth` — const, line 169
- `const s = (1 - Math.cos(t * Math.PI)) / 2` — const, line 170
- `const surfaceZ = (theta: number, r: number): number` — const, line 174
- `const blend = smooth(clamp01(r / CENTER_BLEND))` — const, line 175
- `const d = meanDepth + (depthAtAngle(theta) - meanDepth) * blend` — const, line 176
- `const polar = (theta: number, r: number, lift = 0): V3` — const, line 180
- `const ASAMP = Math.max(96, Math.min(168, N * 12))` — const, line 186
- `const thetaAt = (s: number)` — const, line 187
- `const rings = RING_RS.map((r)` — const, line 189
- `const pts: V3[] = []` — const, line 190
- `const spokeAt = (theta: number): V3[]` — const, line 195
- `const pts: V3[] = []` — const, line 196
- `const spokes = states.map((s)` — const, line 200
- `const RFINE = 110` — const, line 205
- `const contours = CONTOUR_QS.map((q)` — const, line 206
- `const zL = -DEPTH * q` — const, line 207
- `const runs: V3[][] = []` — const, line 208
- `let run: V3[] = []` — let, line 209
- `const theta = thetaAt(s)` — const, line 211
- `let hit: number | null = null` — let, line 212
- `let prevR = 1` — let, line 213
- `let prevZ = surfaceZ(theta, 1)` — let, line 214
- `const r = 1 - f / RFINE` — const, line 216
- `const z = surfaceZ(theta, r)` — const, line 217
- `const t = prevZ === z ? 0.5 : (zL - prevZ) / (z - prevZ)` — const, line 219
- `const beads = states.map((s)` — const, line 237
- `const ghosts = states.map((s)` — const, line 238
- `const labels = states.map((s)` — const, line 248
- `function depthRuns(points: Projected[]): Array<` — function, line 255
- `const bucketOf = (depth: number)` — const, line 256
- `const runs: Array<` — const, line 257
- `let start = 0` — let, line 258
- `let bucket = points.length > 1 ? bucketOf((points[0].depth + points[1].depth) / 2) : 0` — let, line 259
- `const b = i + 1 < points.length ? bucketOf((points[i].depth + points[i + 1].depth) / 2) : bucket` — const, line 261
- `const W = width && width > 0 ? width : DEFAULT_W` — const, line 293
- `const H = height && height > 0 ? height : DEFAULT_H` — const, line 294
- `const CX = W / 2` — const, line 295
- `const CY = H / 2 - H * CENTER_LIFT` — const, line 296
- `const SCALE = Math.min(W * SCALE_W, H * SCALE_H)` — const, line 297
- `const zoom = useScrollZoom(` — const, line 303
- `const states = useMemo(()` — const, line 304
- `const geometry = useMemo(()` — const, line 305
- `const view =` — const, line 307
- `const proj = (p: V3)` — const, line 308
- `const beadOrder = useMemo(()` — const, line 313
- `const summary = useMemo(()` — const, line 322
- `let deep = 0` — let, line 323
- `let anchored = 0` — let, line 324
- `let shallow = 0` — let, line 325
- `let flat = 0` — let, line 326
- `let held = 0` — let, line 327
- `let debt = 0` — let, line 328
- `let instructed = 0` — let, line 329
- `const ariaLabel = `Knowledge well, $` — const, line 345
- `const sortedIds = states.map((s)` — const, line 357
- `const pin = onPin ?? onSelect` — const, line 363
- `const onKeyDown = (event: React.KeyboardEvent<SVGSVGElement>)` — const, line 367
- `const idx = selected ? sortedIds.indexOf(selected) : -1` — const, line 369
- `const lo = states[idx].point.learningObjectIds[0]` — const, line 387
- `const isRim = RING_RS[ri] === 1` — const, line 456
- `const s = states[i]` — const, line 473
- `const isActive = s.point.id === selected` — const, line 474
- `const s = states[i]` — const, line 530
- `const p = proj(geometry.beads[i])` — const, line 531
- `const isActive = s.point.id === selected` — const, line 532
- `const fade = depthFade(p.depth, 0.6, 1)` — const, line 533
- `const size = (isActive ? 5 : 3.8) * p.k * zoom.markerScale` — const, line 534
- `const hit = 11 * zoom.markerScale` — const, line 535
- `const tooltip = `$` — const, line 536
- `const onEnter = ()` — const, line 546
- `const onClick = (event: React.MouseEvent)` — const, line 550
- `const lo = s.point.learningObjectIds[0]` — const, line 555
- `const d = size + 1.2` — const, line 572
- `const s = states[i]` — const, line 644
- `const p = proj(pos)` — const, line 645
- `const isActive = s.point.id === selected` — const, line 646
- `const anchor = Math.abs(p.x - CX) < 14 ? "middle" : p.x > CX ? "start" : "end"` — const, line 647
- `const lines = labelLines(s.point.id)` — const, line 648
- `const LINE_H = 12` — const, line 649
- `const blockShift = p.y > CY + 10 ? 4 : -((lines.length - 1) * LINE_H) / 2` — const, line 650
- `const fade = depthFade(p.depth, 0.55, 1)` — const, line 651
- `const x = sx > 0 ? W - 10 : 10` — const, line 706
- `const y = sy > 0 ? H - 10 : 10` — const, line 707

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export: `KnowledgeWellView`; references `KnowledgeWellView`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DecayPressureDto`, `KnowledgeFacetField`, `KnowledgeFacetPoint`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/scrollZoom|src/screens/scrollZoom.ts]] — import-or-re-export; imports `useScrollZoom`
- [[Reference/Desktop/TypeScript/screens/wire3d|src/screens/wire3d.ts]] — import-or-re-export; imports `Projected`, `depthFade`, `polyPath`, `project`, `useOrbitCamera`

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

1. Modify [apps/learnloop-tauri/src/screens/KnowledgeWellView.tsx](../../../../../../apps/learnloop-tauri/src/screens/KnowledgeWellView.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

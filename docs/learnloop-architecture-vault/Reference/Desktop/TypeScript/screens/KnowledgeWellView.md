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
source_commit: "3fa780b50a46ea4a95ff64fad57ff6e27e904dbd"
source_commit_timestamp: "2026-10-13T02:46:02-04:00"
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
| Source lines | 765 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `3fa780b50a46ea4a95ff64fad57ff6e27e904dbd` |
| Commit timestamp | `2026-10-13T02:46:02-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/KnowledgeWellView|src/screens/KnowledgeWellView.tsx]]

## Public API

- `export function buildStates(field: KnowledgeFacetField, decay: DecayPressureDto | null | undefined): FacetState[]` — function, line 121
- `export function buildGeometry(states: FacetState[]): WellGeometry` — function, line 169
- `export function KnowledgeWellView(` — function, line 283

## Internal implementation anchors

- `const DEFAULT_W = 860` — const, line 32
- `const DEFAULT_H = 640` — const, line 33
- `const CENTER_LIFT = 0.047` — const, line 34
- `const SCALE_W = 0.273` — const, line 35
- `const SCALE_H = 0.42` — const, line 36
- `const DEPTH = 0.9` — const, line 38
- `const CENTER_BLEND = 0.28` — const, line 39
- `const PROFILE_POW = 1.55` — const, line 40
- `const EVIDENCE_K = 1.2` — const, line 41
- `const DEMO_THRESHOLD = 0.5` — const, line 42
- `const DEEP_LEVEL = 0.4` — const, line 43
- `const SHALLOW_LEVEL = 0.12` — const, line 44
- `const BEAD_R = 0.52` — const, line 45
- `const RING_RS = [0.14, 0.28, 0.42, 0.56, 0.7, 0.84, 1]` — const, line 46
- `const CONTOUR_QS = [0.12, 0.24, 0.36, 0.48, 0.6, 0.72]` — const, line 47
- `const SPOKE_STEPS = 26` — const, line 48
- `const EASE = "stroke 0.22s ease, fill 0.22s ease, opacity 0.22s ease, stroke-width 0.22s ease"` — const, line 49
- `const ASSUMED_NOTE = "assumed known, not tested: its first review is the check"` — const, line 54
- `const ASSUMED_DASH = "1.6 1.8"` — const, line 55
- `const clamp01 = (value: number)` — const, line 57
- `const smooth = (t: number)` — const, line 58
- `const visibility = (evidenceMass: number)` — const, line 59
- `type V3 =` — type, line 61
- `function labelLines(facetId: string, maxChars = 20): string[]` — function, line 64
- `const words = facetId.split("_")` — const, line 65
- `const lines: string[] = []` — const, line 66
- `let current = ""` — let, line 67
- `const candidate = current ? `$` — const, line 69
- `interface FacetState` — interface, line 83
- `function decayByFacet(decay: DecayPressureDto | null | undefined): Map<string,` — function, line 108
- `const out = new Map<string,` — const, line 109
- `const prev = out.get(row.facetId)` — const, line 111
- `const crosses = [prev?.crossesInDays, row.crossesInDays].filter((v): v is number` — const, line 112
- `const points = [...field.points].sort((a, b)` — const, line 124
- `const N = points.length` — const, line 125
- `const decayMap = decayByFacet(decay)` — const, line 126
- `const vis = visibility(point.evidenceMass)` — const, line 128
- `const wellDepth = point.untested ? 0 : clamp01(point.ready) * vis` — const, line 129
- `const ghostDepth = point.untested ? 0 : clamp01(point.readyGhost) * vis` — const, line 130
- `const absent = !point.hasBlueprints` — const, line 131
- `const entry = decayMap.get(point.id)` — const, line 132
- `const noHistory = entry != null && !entry.hasHistory` — const, line 136
- `const demonstrated = point.demonstratedMass >= DEMO_THRESHOLD` — const, line 137
- `interface WellGeometry` — interface, line 160
- `const N = states.length` — const, line 170
- `const meanDepth = states.reduce((sum, s)` — const, line 171
- `const depthAtAngle = (theta: number): number` — const, line 175
- `const u = (((theta + Math.PI / 2) / (2 * Math.PI)) * N) % N` — const, line 176
- `const uu = u < 0 ? u + N : u` — const, line 177
- `const i0 = Math.floor(uu) % N` — const, line 178
- `const t = uu - Math.floor(uu)` — const, line 179
- `const d0 = states[i0].effectiveDepth` — const, line 180
- `const d1 = states[(i0 + 1) % N].effectiveDepth` — const, line 181
- `const s = (1 - Math.cos(t * Math.PI)) / 2` — const, line 182
- `const surfaceZ = (theta: number, r: number): number` — const, line 186
- `const blend = smooth(clamp01(r / CENTER_BLEND))` — const, line 187
- `const d = meanDepth + (depthAtAngle(theta) - meanDepth) * blend` — const, line 188
- `const polar = (theta: number, r: number, lift = 0): V3` — const, line 192
- `const ASAMP = Math.max(96, Math.min(168, N * 12))` — const, line 198
- `const thetaAt = (s: number)` — const, line 199
- `const rings = RING_RS.map((r)` — const, line 201
- `const pts: V3[] = []` — const, line 202
- `const spokeAt = (theta: number): V3[]` — const, line 207
- `const pts: V3[] = []` — const, line 208
- `const spokes = states.map((s)` — const, line 212
- `const RFINE = 110` — const, line 217
- `const contours = CONTOUR_QS.map((q)` — const, line 218
- `const zL = -DEPTH * q` — const, line 219
- `const runs: V3[][] = []` — const, line 220
- `let run: V3[] = []` — let, line 221
- `const theta = thetaAt(s)` — const, line 223
- `let hit: number | null = null` — let, line 224
- `let prevR = 1` — let, line 225
- `let prevZ = surfaceZ(theta, 1)` — let, line 226
- `const r = 1 - f / RFINE` — const, line 228
- `const z = surfaceZ(theta, r)` — const, line 229
- `const t = prevZ === z ? 0.5 : (zL - prevZ) / (z - prevZ)` — const, line 231
- `const beads = states.map((s)` — const, line 249
- `const ghosts = states.map((s)` — const, line 250
- `const labels = states.map((s)` — const, line 260
- `function depthRuns(points: Projected[]): Array<` — function, line 267
- `const bucketOf = (depth: number)` — const, line 268
- `const runs: Array<` — const, line 269
- `let start = 0` — let, line 270
- `let bucket = points.length > 1 ? bucketOf((points[0].depth + points[1].depth) / 2) : 0` — let, line 271
- `const b = i + 1 < points.length ? bucketOf((points[i].depth + points[i + 1].depth) / 2) : bucket` — const, line 273
- `const W = width && width > 0 ? width : DEFAULT_W` — const, line 305
- `const H = height && height > 0 ? height : DEFAULT_H` — const, line 306
- `const CX = W / 2` — const, line 307
- `const CY = H / 2 - H * CENTER_LIFT` — const, line 308
- `const SCALE = Math.min(W * SCALE_W, H * SCALE_H)` — const, line 309
- `const zoom = useScrollZoom(` — const, line 315
- `const states = useMemo(()` — const, line 316
- `const geometry = useMemo(()` — const, line 317
- `const view =` — const, line 319
- `const proj = (p: V3)` — const, line 320
- `const beadOrder = useMemo(()` — const, line 325
- `const summary = useMemo(()` — const, line 334
- `let deep = 0` — let, line 335
- `let anchored = 0` — let, line 336
- `let shallow = 0` — let, line 337
- `let flat = 0` — let, line 338
- `let held = 0` — let, line 339
- `let debt = 0` — let, line 340
- `let instructed = 0` — let, line 341
- `const ariaLabel = `Knowledge well, $` — const, line 357
- `const sortedIds = states.map((s)` — const, line 369
- `const pin = onPin ?? onSelect` — const, line 375
- `const onKeyDown = (event: React.KeyboardEvent<SVGSVGElement>)` — const, line 379
- `const idx = selected ? sortedIds.indexOf(selected) : -1` — const, line 381
- `const lo = states[idx].point.learningObjectIds[0]` — const, line 399
- `const isRim = RING_RS[ri] === 1` — const, line 468
- `const s = states[i]` — const, line 485
- `const isActive = s.point.id === selected` — const, line 486
- `const point = states[i].point` — const, line 518
- `const s = states[i]` — const, line 543
- `const p = proj(geometry.beads[i])` — const, line 544
- `const isActive = s.point.id === selected` — const, line 545
- `const fade = depthFade(p.depth, 0.6, 1)` — const, line 546
- `const size = (isActive ? 5 : 3.8) * p.k * zoom.markerScale` — const, line 547
- `const hit = 11 * zoom.markerScale` — const, line 548
- `const tooltip = `$` — const, line 549
- `const onEnter = ()` — const, line 564
- `const onClick = (event: React.MouseEvent)` — const, line 568
- `const lo = s.point.learningObjectIds[0]` — const, line 573
- `const d = size + 1.2` — const, line 609
- `const s = states[i]` — const, line 682
- `const p = proj(pos)` — const, line 683
- `const isActive = s.point.id === selected` — const, line 684
- `const anchor = Math.abs(p.x - CX) < 14 ? "middle" : p.x > CX ? "start" : "end"` — const, line 685
- `const lines = labelLines(s.point.id)` — const, line 686
- `const LINE_H = 12` — const, line 687
- `const blockShift = p.y > CY + 10 ? 4 : -((lines.length - 1) * LINE_H) / 2` — const, line 688
- `const fade = depthFade(p.depth, 0.55, 1)` — const, line 689
- `const x = sx > 0 ? W - 10 : 10` — const, line 744
- `const y = sy > 0 ? H - 10 : 10` — const, line 745

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export: `ASSUMED_LABEL`, `KnowledgeWellView`; references `ASSUMED_LABEL`, `KnowledgeWellView`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DecayPressureDto`, `KnowledgeFacetField`, `KnowledgeFacetPoint`
- [[Reference/Desktop/TypeScript/components/PlacementControls|src/components/PlacementControls.tsx]] — import-or-re-export; imports `ASSUMED_LABEL`
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

- [apps/learnloop-tauri/src/screens/KnowledgeWellView.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/KnowledgeWellView.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_knowledge_model.py](../../../../../../tests/test_sidecar_knowledge_model.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_graph_edit_proposals.py](../../../../../../tests/test_graph_edit_proposals.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_build_study_map_routing.py](../../../../../../tests/test_build_study_map_routing.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/KnowledgeWellView.tsx](../../../../../../apps/learnloop-tauri/src/screens/KnowledgeWellView.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

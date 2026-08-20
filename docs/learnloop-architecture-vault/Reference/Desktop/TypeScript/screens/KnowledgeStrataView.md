---
title: "Desktop module · src/screens/KnowledgeStrataView.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.KnowledgeStrataView"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/KnowledgeStrataView.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/KnowledgeStrataView.tsx"
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

# `src/screens/KnowledgeStrataView.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `KnowledgeStrataView` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/KnowledgeStrataView.tsx](../../../../../../apps/learnloop-tauri/src/screens/KnowledgeStrataView.tsx) |
| Source lines | 579 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/KnowledgeStrataView|src/screens/KnowledgeStrataView.tsx]]

## Public API

- `export function KnowledgeStrataView(` — function, line 204

## Internal implementation anchors

- `const DEFAULT_W = 860` — const, line 22
- `const LABEL_W = 168` — const, line 23
- `const STAT_W = 84` — const, line 24
- `const PLOT_X = LABEL_W` — const, line 25
- `const AGG_H = 64` — const, line 26
- `const AXIS_H = 18` — const, line 27
- `const ROW_H = 20` — const, line 28
- `const CONCEPT_H = 18` — const, line 29
- `const FRONTIER_LEVEL = 0.7` — const, line 30
- `const AGG_SAMPLES = 140` — const, line 31
- `const dateLabel = (tMs: number)` — const, line 33
- `function correctnessTone(correctness: number | null): string` — function, line 35
- `interface LoRow` — interface, line 42
- `interface StrataData` — interface, line 56
- `function buildStrata(points: KnowledgeMapPoint[], history: KnowledgeMapHistory, nowMs: number): StrataData` — function, line 66
- `const pointById = new Map(points.map((p)` — const, line 67
- `const rowByLo = new Map<string, LoRow>()` — const, line 70
- `let row = rowByLo.get(point.learningObjectId)` — let, line 72
- `const row = rowByLo.get(lo.id)` — const, line 94
- `const attemptCount = new Map<string, number>()` — const, line 102
- `const tMs = Date.parse(attempt.t)` — const, line 104
- `const row = rowByLo.get(attempt.learningObjectId)` — const, line 106
- `const point = pointById.get(attempt.practiceItemId)` — const, line 108
- `const rows = [...rowByLo.values()]` — const, line 120
- `let best = row.points[0]` — let, line 125
- `const centroids = rows.map((row)` — const, line 134
- `const cx = row.points.reduce((s, p)` — const, line 135
- `const cy = row.points.reduce((s, p)` — const, line 136
- `const mx = centroids.reduce((s, c)` — const, line 139
- `const my = centroids.reduce((s, c)` — const, line 140
- `let cxx = 0` — let, line 141
- `let cyy = 0` — let, line 142
- `let cxy = 0` — let, line 143
- `const angle = 0.5 * Math.atan2(2 * cxy, cxx - cyy)` — const, line 149
- `const ux = Math.cos(angle)` — const, line 150
- `const uy = Math.sin(angle)` — const, line 151
- `const byConcept = new Map<string | null, LoRow[]>()` — const, line 156
- `const bucket = byConcept.get(row.conceptId) ?? []` — const, line 158
- `const groups = [...byConcept.entries()].map(([conceptId, members])` — const, line 162
- `const mean = members.reduce((s, r)` — const, line 164
- `const times: number[] = []` — const, line 169
- `const hasHistory = times.length > 0` — const, line 174
- `const startMs = hasHistory ? Math.min(...times) : nowMs - 24 * 3600 * 1000` — const, line 175
- `const endMs = Math.max(nowMs, hasHistory ? Math.max(...times) : nowMs)` — const, line 176
- `const spanMs = Math.max(endMs - startMs, 60 * 60 * 1000)` — const, line 177
- `function masteryAt(series: LoRow["series"], tMs: number): number | null` — function, line 190
- `let value = series[0].mastery` — let, line 192
- `function shortenId(id: string, max: number): string` — function, line 200
- `const W = width && width > 0 ? width : DEFAULT_W` — const, line 222
- `const PLOT_W = W - LABEL_W - STAT_W` — const, line 223
- `const nowMs = useMemo(()` — const, line 224
- `const data = useMemo(()` — const, line 225
- `const svgRef = useRef<SVGSVGElement | null>(null)` — const, line 226
- `const tx = (tMs: number)` — const, line 229
- `const layout = useMemo(()` — const, line 232
- `let y = AGG_H + 12 + AXIS_H` — let, line 233
- `const headers: Array<` — const, line 234
- `const rowY = new Map<string, number>()` — const, line 235
- `const aggregate = useMemo(()` — const, line 251
- `const total = data.rows.length` — const, line 252
- `const stacks: number[][] = []` — const, line 254
- `const t = data.startMs + (i / AGG_SAMPLES) * data.spanMs` — const, line 256
- `let strong = 0` — let, line 257
- `let developing = 0` — let, line 258
- `let weak = 0` — let, line 259
- `const m = masteryAt(row.series, t)` — const, line 261
- `const yTop = 8` — const, line 269
- `const yOf = (count: number)` — const, line 270
- `const bands = ["strong", "developing", "weak", "untried"] as const` — const, line 271
- `const paths: Record<(typeof bands)[number], string> =` — const, line 272
- `const lower: string[] = []` — const, line 274
- `const upper: string[] = []` — const, line 275
- `const x = PLOT_X + (i / AGG_SAMPLES) * PLOT_W` — const, line 277
- `const below = stacks[i].slice(0, bi).reduce((s, v)` — const, line 278
- `const gridTimes = useMemo(()` — const, line 287
- `const ticks: number[] = []` — const, line 288
- `const n = 5` — const, line 289
- `const selectedLo = selected ? points.find((p)` — const, line 294
- `const onMove = (event: React.MouseEvent<SVGSVGElement>)` — const, line 296
- `const rect = svgRef.current?.getBoundingClientRect()` — const, line 297
- `const x = ((event.clientX - rect.left) / rect.width) * W` — const, line 299
- `const height = layout.height` — const, line 307
- `const axisY = AGG_H + 12 + AXIS_H - 6` — const, line 308
- `const x = tx(t)` — const, line 341
- `const y = layout.rowY.get(row.loId)` — const, line 377
- `const baseY = y + ROW_H - 4` — const, line 379
- `const topPad = 3` — const, line 380
- `const mY = (m: number)` — const, line 381
- `const isSelectedRow = selectedLo === row.loId` — const, line 382
- `const untried = row.series.length === 0` — const, line 383
- `const stepSegs: Array<` — const, line 387
- `const s = row.series[i]` — const, line 389
- `const next = row.series[i + 1]` — const, line 390
- `const crossings: number[] = []` — const, line 395
- `const prev = i === 0 ? 0 : row.series[i - 1].mastery` — const, line 397
- `const tone = row.currentMastery != null ? masteryTone(row.currentMastery, COLOR) : COLOR.textFaint` — const, line 401
- `const hoverM = hoverT != null ? masteryAt(row.series, hoverT) : null` — const, line 402
- `const segTone = masteryTone(seg.m, COLOR)` — const, line 458
- `const x = tx(attempt.tMs)` — const, line 501
- `const c = correctnessTone(attempt.correctness)` — const, line 502

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export: `KnowledgeStrataView`; references `KnowledgeStrataView`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `KnowledgeMapHistory`, `KnowledgeMapPoint`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `masteryTone`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`

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

1. Modify [apps/learnloop-tauri/src/screens/KnowledgeStrataView.tsx](../../../../../../apps/learnloop-tauri/src/screens/KnowledgeStrataView.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

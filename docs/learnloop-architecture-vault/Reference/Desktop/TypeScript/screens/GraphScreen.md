---
title: "Desktop module · src/screens/GraphScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.GraphScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/GraphScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/GraphScreen.tsx"
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

# `src/screens/GraphScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `GraphScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/GraphScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/GraphScreen.tsx) |
| Source lines | 1121 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]]

## Public API

- `export function GraphScreen(` — function, line 158

## Internal implementation anchors

- `type PendingEdit } from "../components/graphedit/pending"` — type, line 26
- `const NODE_W = 200` — const, line 34
- `const NODE_H = 36` — const, line 35
- `const COL_GAP = 80` — const, line 36
- `const ROW_GAP = 24` — const, line 37
- `const PAD = 24` — const, line 38
- `type Relation = "prerequisite" | "confusable_with" | "related" | "part_of"` — type, line 40
- `const RELATION_STYLE: Record<Relation,` — const, line 42
- `function relationStyle(relation: string)` — function, line 49
- `function conceptPillColor(type: string): PillColor` — function, line 53
- `function masteryColor(mastery: number): string` — function, line 57
- `type Position =` — type, line 61
- `function layoutConcepts(concepts: ConceptGraphNode[], edges: ConceptGraphEdge[]):` — function, line 65
- `const depth: Record<string, number> =` — const, line 70
- `const prereq = edges.filter((edge)` — const, line 74
- `let changed = false` — let, line 76
- `const byColumn = new Map<number, ConceptGraphNode[]>()` — const, line 86
- `const col = depth[concept.id] ?? 0` — const, line 88
- `const bucket = byColumn.get(col) ?? []` — const, line 89
- `const positions: Record<string, Position> =` — const, line 94
- `const placed = Object.values(positions)` — const, line 111
- `const minX = Math.min(...placed.map((p)` — const, line 115
- `const minY = Math.min(...placed.map((p)` — const, line 116
- `let maxX = 0` — let, line 117
- `let maxY = 0` — let, line 118
- `const x = positions[id].x - minX + PAD` — const, line 120
- `const y = positions[id].y - minY + PAD` — const, line 121
- `function edgePath(source: Position, target: Position): string` — function, line 132
- `const sy = source.y + NODE_H / 2` — const, line 133
- `const ty = target.y + NODE_H / 2` — const, line 134
- `const sx = source.x` — const, line 136
- `const tx = target.x + NODE_W` — const, line 137
- `const mid = (sx + tx) / 2` — const, line 138
- `const sx = source.x + NODE_W` — const, line 141
- `const tx = target.x` — const, line 142
- `const mid = (sx + tx) / 2` — const, line 143
- `function edgeMidpoint(source: Position, target: Position): Position` — function, line 149
- `type GraphView = "map" | "knowledge"` — type, line 156
- `const graphQuery = useCachedQuery(["get_concept_graph"], ()` — const, line 164
- `const snapshot: ConceptGraphSnapshot | null = graphQuery.data ?? null` — const, line 168
- `const cancelGesture = ()` — const, line 200
- `const stageEdit = (edit: PendingEdit)` — const, line 208
- `const filtered = prev.filter((p)` — const, line 212
- `const removePending = (pid: string)` — const, line 217
- `const clearPending = ()` — const, line 218
- `let cancelled = false` — let, line 228
- `const active = snap.goals.find((g)` — const, line 234
- `const order = useMemo(()` — const, line 261
- `const layout = useMemo( ()` — const, line 262
- `const resolved = useMemo(()` — const, line 269
- `const syllabusOrder = useMemo(()` — const, line 270
- `const conceptTitle = useMemo(()` — const, line 275
- `const map = new Map((snapshot?.concepts ?? []).map((c)` — const, line 276
- `const fileEdits = ()` — const, line 283
- `const batch = [...pending]` — const, line 288
- `const invalid = result.items.filter((item)` — const, line 292
- `const map = new Map<string, string[]>()` — const, line 294
- `const pid = batch[index]?.pid` — const, line 296
- `const runGeometryPreview = ()` — const, line 313
- `const handleReorderDrop = (movedId: string, fromIndex: number, toIndex: number)` — const, line 325
- `const confirmReorder = ()` — const, line 338
- `const goalScope = useMemo(()` — const, line 350
- `const scopeConcepts = new Set(goal.facetScope.concepts)` — const, line 352
- `const atRiskLos = new Set( (goalReport?.report.atRisk ?? []).filter((f)` — const, line 353
- `const status = new Map<string, "atRisk" | "onTrack">()` — const, line 356
- `let atRiskCount = 0` — let, line 357
- `const risky = concept.learningObjects.some((lo)` — const, line 359
- `const inScope = scopeConcepts.has(concept.id) || risky` — const, line 360
- `const onKey = (event: KeyboardEvent)` — const, line 370
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 372
- `const index = selected ? order.indexOf(selected) : -1` — const, line 376
- `const next = event.shiftKey ? (index - 1 + order.length) % order.length : (index + 1) % order.length` — const, line 377
- `const onEsc = (event: KeyboardEvent)` — const, line 387
- `const viewToggle = ( <div style=` — const, line 399
- `const conceptById = new Map(snapshot.concepts.map((concept)` — const, line 475
- `const selectedConcept = selected ? conceptById.get(selected) ?? null : null` — const, line 476
- `const fill = id === "arrow-red" ? COLOR.red : id === "arrow-cyan" ? COLOR.cyan : id === "arrow-green" ? COLOR.green : COLOR.amber` — const, line 587
- `const source = layout.positions[edge.source]` — const, line 597
- `const target = layout.positions[edge.target]` — const, line 598
- `const style = relationStyle(edge.relationType)` — const, line 600
- `const incidentHover = hovered != null && (edge.source === hovered || edge.target === hovered)` — const, line 601
- `const incidentSelected = selected != null && (edge.source === selected || edge.target === selected)` — const, line 602
- `const incident = incidentHover || incidentSelected` — const, line 603
- `const isRetired = resolved.deletedById.has(edge.id)` — const, line 606
- `const isUpdated = resolved.updatedById.has(edge.id)` — const, line 607
- `const touched = isRetired || isUpdated` — const, line 608
- `const source = layout.positions[edge.source]` — const, line 630
- `const target = layout.positions[edge.target]` — const, line 631
- `const mid = edgeMidpoint(source, target)` — const, line 633
- `const source = layout.positions[up.source]` — const, line 654
- `const target = layout.positions[up.target]` — const, line 655
- `const style = relationStyle(up.relationType)` — const, line 657
- `const source = layout.positions[create.source]` — const, line 675
- `const target = layout.positions[create.target]` — const, line 676
- `const style = relationStyle(create.relationType)` — const, line 678
- `const source = layout.positions[edge.source]` — const, line 698
- `const target = layout.positions[edge.target]` — const, line 699
- `const mid = edgeMidpoint(source, target)` — const, line 711
- `const pos = layout.positions[concept.id]` — const, line 722
- `const isMisc = concept.type === "misconception"` — const, line 724
- `const isSelected = selected === concept.id` — const, line 725
- `const isHovered = hovered === concept.id` — const, line 726
- `const hoverAccent = isMisc ? "rgba(224,126,126,0.6)" : "rgba(255, 161, 67, 0.6)"` — const, line 727
- `const gstat = goalScope?.status.get(concept.id) ?? null` — const, line 730
- `const dimmed = goalScope != null && gstat == null` — const, line 731
- `const isArmed = armedSource === concept.id` — const, line 732
- `const goalRing = gstat === "atRisk" ? `0 0 0 2px $` — const, line 733
- `const armedRing = isArmed ? `0 0 0 2px $` — const, line 737
- `const boxShadow = [isSelected ? `0 0 0 1px $` — const, line 742
- `const onNodeClick = ()` — const, line 744
- `const edge = edgePopover.edge` — const, line 831
- `const edge = edgePopover.edge` — const, line 844
- `const edge = edgePopover.edge` — const, line 857
- `function Legend(` — function, line 942
- `const style = RELATION_STYLE[relation]` — const, line 959
- `const DETAIL_WIDTH_KEY = "ll.graph.detailWidth"` — const, line 977
- `const DETAIL_WIDTH_MIN = 240` — const, line 978
- `const DETAIL_WIDTH_MAX = 720` — const, line 979
- `function ConceptDetail(` — function, line 981
- `const saved = Number(window.localStorage.getItem(DETAIL_WIDTH_KEY))` — const, line 991
- `const dragStart = useRef<` — const, line 994
- `const onHandlePointerDown = useCallback( (event: ReactPointerEvent<HTMLDivElement>)` — const, line 996
- `const onHandlePointerMove = useCallback((event: ReactPointerEvent<HTMLDivElement>)` — const, line 1004
- `const start = dragStart.current` — const, line 1005
- `const next = Math.min(DETAIL_WIDTH_MAX, Math.max(DETAIL_WIDTH_MIN, start.width + (start.x - event.clientX)))` — const, line 1007
- `const onHandlePointerUp = useCallback((event: ReactPointerEvent<HTMLDivElement>)` — const, line 1010
- `const resizeHandle = ( <div onPointerDown=` — const, line 1020
- `const incoming = edges.filter((edge)` — const, line 1045
- `const outgoing = edges.filter((edge)` — const, line 1046

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: dynamic import; no named call claim

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`, `ConceptGraphEdge`, `ConceptGraphNode`, `ConceptGraphSnapshot`, `GoalDto`, `GoalReportSnapshot`, `KnowledgeMapPreviewDto`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `masteryTone`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/graphedit/EditPopovers|src/components/graphedit/EditPopovers.tsx]] — import-or-re-export; imports `EdgePopover`, `RelationPicker`
- [[Reference/Desktop/TypeScript/components/graphedit/GeometryPreview|src/components/graphedit/GeometryPreview.tsx]] — import-or-re-export; imports `GeometryPreview`
- [[Reference/Desktop/TypeScript/components/graphedit/PendingStrip|src/components/graphedit/PendingStrip.tsx]] — import-or-re-export; imports `PendingStrip`
- [[Reference/Desktop/TypeScript/components/graphedit/SyllabusColumn|src/components/graphedit/SyllabusColumn.tsx]] — import-or-re-export; imports `ReorderPrompt`, `SyllabusColumn`
- [[Reference/Desktop/TypeScript/components/graphedit/pending|src/components/graphedit/pending.ts]] — import-or-re-export; imports `PendingEdit`, `compileEdits`, `effectivePrereqEdges`, `inferReorderEdits`, `newPid`, `previewInput`, `resolvePending`, `topoOrder`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `BlockBar`, `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `PillColor`, `SectionHeader`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EntityLink`
- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export; imports `KnowledgeMapView`

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
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/GraphScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/GraphScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

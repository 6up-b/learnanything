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
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
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
| Source lines | 1117 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]]

## Public API

- `export function GraphScreen(` — function, line 155

## Internal implementation anchors

- `type PendingEdit } from "../components/graphedit/pending"` — type, line 24
- `const NODE_W = 200` — const, line 31
- `const NODE_H = 36` — const, line 32
- `const COL_GAP = 80` — const, line 33
- `const ROW_GAP = 24` — const, line 34
- `const PAD = 24` — const, line 35
- `type Relation = "prerequisite" | "confusable_with" | "related" | "part_of"` — type, line 37
- `const RELATION_STYLE: Record<Relation,` — const, line 39
- `function relationStyle(relation: string)` — function, line 46
- `function conceptPillColor(type: string): PillColor` — function, line 50
- `function masteryColor(mastery: number): string` — function, line 54
- `type Position =` — type, line 58
- `function layoutConcepts(concepts: ConceptGraphNode[], edges: ConceptGraphEdge[]):` — function, line 62
- `const depth: Record<string, number> =` — const, line 67
- `const prereq = edges.filter((edge)` — const, line 71
- `let changed = false` — let, line 73
- `const byColumn = new Map<number, ConceptGraphNode[]>()` — const, line 83
- `const col = depth[concept.id] ?? 0` — const, line 85
- `const bucket = byColumn.get(col) ?? []` — const, line 86
- `const positions: Record<string, Position> =` — const, line 91
- `const placed = Object.values(positions)` — const, line 108
- `const minX = Math.min(...placed.map((p)` — const, line 112
- `const minY = Math.min(...placed.map((p)` — const, line 113
- `let maxX = 0` — let, line 114
- `let maxY = 0` — let, line 115
- `const x = positions[id].x - minX + PAD` — const, line 117
- `const y = positions[id].y - minY + PAD` — const, line 118
- `function edgePath(source: Position, target: Position): string` — function, line 129
- `const sy = source.y + NODE_H / 2` — const, line 130
- `const ty = target.y + NODE_H / 2` — const, line 131
- `const sx = source.x` — const, line 133
- `const tx = target.x + NODE_W` — const, line 134
- `const mid = (sx + tx) / 2` — const, line 135
- `const sx = source.x + NODE_W` — const, line 138
- `const tx = target.x` — const, line 139
- `const mid = (sx + tx) / 2` — const, line 140
- `function edgeMidpoint(source: Position, target: Position): Position` — function, line 146
- `type GraphView = "map" | "knowledge"` — type, line 153
- `const cancelGesture = ()` — const, line 189
- `const stageEdit = (edit: PendingEdit)` — const, line 197
- `const filtered = prev.filter((p)` — const, line 201
- `const removePending = (pid: string)` — const, line 206
- `const clearPending = ()` — const, line 207
- `let cancelled = false` — let, line 217
- `const active = snap.goals.find((g)` — const, line 223
- `let cancelled = false` — let, line 243
- `const order = useMemo(()` — const, line 259
- `const layout = useMemo( ()` — const, line 260
- `const resolved = useMemo(()` — const, line 267
- `const syllabusOrder = useMemo(()` — const, line 268
- `const conceptTitle = useMemo(()` — const, line 273
- `const map = new Map((snapshot?.concepts ?? []).map((c)` — const, line 274
- `const fileEdits = ()` — const, line 281
- `const batch = [...pending]` — const, line 286
- `const invalid = result.items.filter((item)` — const, line 290
- `const map = new Map<string, string[]>()` — const, line 292
- `const pid = batch[index]?.pid` — const, line 294
- `const runGeometryPreview = ()` — const, line 311
- `const handleReorderDrop = (movedId: string, fromIndex: number, toIndex: number)` — const, line 323
- `const confirmReorder = ()` — const, line 336
- `const goalScope = useMemo(()` — const, line 348
- `const scopeConcepts = new Set(goal.facetScope.concepts)` — const, line 350
- `const atRiskLos = new Set( (goalReport?.report.atRisk ?? []).filter((f)` — const, line 351
- `const status = new Map<string, "atRisk" | "onTrack">()` — const, line 354
- `let atRiskCount = 0` — let, line 355
- `const risky = concept.learningObjects.some((lo)` — const, line 357
- `const inScope = scopeConcepts.has(concept.id) || risky` — const, line 358
- `const onKey = (event: KeyboardEvent)` — const, line 368
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 369
- `const index = selected ? order.indexOf(selected) : -1` — const, line 373
- `const next = event.shiftKey ? (index - 1 + order.length) % order.length : (index + 1) % order.length` — const, line 374
- `const onEsc = (event: KeyboardEvent)` — const, line 384
- `const viewToggle = ( <div style=` — const, line 395
- `const conceptById = new Map(snapshot.concepts.map((concept)` — const, line 471
- `const selectedConcept = selected ? conceptById.get(selected) ?? null : null` — const, line 472
- `const fill = id === "arrow-red" ? COLOR.red : id === "arrow-cyan" ? COLOR.cyan : id === "arrow-green" ? COLOR.green : COLOR.amber` — const, line 583
- `const source = layout.positions[edge.source]` — const, line 593
- `const target = layout.positions[edge.target]` — const, line 594
- `const style = relationStyle(edge.relationType)` — const, line 596
- `const incidentHover = hovered != null && (edge.source === hovered || edge.target === hovered)` — const, line 597
- `const incidentSelected = selected != null && (edge.source === selected || edge.target === selected)` — const, line 598
- `const incident = incidentHover || incidentSelected` — const, line 599
- `const isRetired = resolved.deletedById.has(edge.id)` — const, line 602
- `const isUpdated = resolved.updatedById.has(edge.id)` — const, line 603
- `const touched = isRetired || isUpdated` — const, line 604
- `const source = layout.positions[edge.source]` — const, line 626
- `const target = layout.positions[edge.target]` — const, line 627
- `const mid = edgeMidpoint(source, target)` — const, line 629
- `const source = layout.positions[up.source]` — const, line 650
- `const target = layout.positions[up.target]` — const, line 651
- `const style = relationStyle(up.relationType)` — const, line 653
- `const source = layout.positions[create.source]` — const, line 671
- `const target = layout.positions[create.target]` — const, line 672
- `const style = relationStyle(create.relationType)` — const, line 674
- `const source = layout.positions[edge.source]` — const, line 694
- `const target = layout.positions[edge.target]` — const, line 695
- `const mid = edgeMidpoint(source, target)` — const, line 707
- `const pos = layout.positions[concept.id]` — const, line 718
- `const isMisc = concept.type === "misconception"` — const, line 720
- `const isSelected = selected === concept.id` — const, line 721
- `const isHovered = hovered === concept.id` — const, line 722
- `const hoverAccent = isMisc ? "rgba(224,126,126,0.6)" : "rgba(255, 161, 67, 0.6)"` — const, line 723
- `const gstat = goalScope?.status.get(concept.id) ?? null` — const, line 726
- `const dimmed = goalScope != null && gstat == null` — const, line 727
- `const isArmed = armedSource === concept.id` — const, line 728
- `const goalRing = gstat === "atRisk" ? `0 0 0 2px $` — const, line 729
- `const armedRing = isArmed ? `0 0 0 2px $` — const, line 733
- `const boxShadow = [isSelected ? `0 0 0 1px $` — const, line 738
- `const onNodeClick = ()` — const, line 740
- `const edge = edgePopover.edge` — const, line 827
- `const edge = edgePopover.edge` — const, line 840
- `const edge = edgePopover.edge` — const, line 853
- `function Legend(` — function, line 938
- `const style = RELATION_STYLE[relation]` — const, line 955
- `const DETAIL_WIDTH_KEY = "ll.graph.detailWidth"` — const, line 973
- `const DETAIL_WIDTH_MIN = 240` — const, line 974
- `const DETAIL_WIDTH_MAX = 720` — const, line 975
- `function ConceptDetail(` — function, line 977
- `const saved = Number(window.localStorage.getItem(DETAIL_WIDTH_KEY))` — const, line 987
- `const dragStart = useRef<` — const, line 990
- `const onHandlePointerDown = useCallback( (event: ReactPointerEvent<HTMLDivElement>)` — const, line 992
- `const onHandlePointerMove = useCallback((event: ReactPointerEvent<HTMLDivElement>)` — const, line 1000
- `const start = dragStart.current` — const, line 1001
- `const next = Math.min(DETAIL_WIDTH_MAX, Math.max(DETAIL_WIDTH_MIN, start.width + (start.x - event.clientX)))` — const, line 1003
- `const onHandlePointerUp = useCallback((event: ReactPointerEvent<HTMLDivElement>)` — const, line 1006
- `const resizeHandle = ( <div onPointerDown=` — const, line 1016
- `const incoming = edges.filter((edge)` — const, line 1041
- `const outgoing = edges.filter((edge)` — const, line 1042

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `GraphScreen`; references `GraphScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`, `ConceptGraphEdge`, `ConceptGraphNode`, `ConceptGraphSnapshot`, `GoalDto`, `GoalReportSnapshot`, `KnowledgeMapPreviewDto`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `masteryTone`
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
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/GraphScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/GraphScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

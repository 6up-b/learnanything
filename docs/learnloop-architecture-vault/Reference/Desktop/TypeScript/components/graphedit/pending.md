---
title: "Desktop module · src/components/graphedit/pending.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.graphedit.pending"
language: "TypeScript"
area: "TypeScript/components/graphedit"
source_path: "apps/learnloop-tauri/src/components/graphedit/pending.ts"
source_paths:
  - "apps/learnloop-tauri/src/components/graphedit/pending.ts"
source_commit: "0cdf509e3186d78939189f5a6ad5a390198da908"
source_commit_timestamp: "2026-07-14T17:11:41-04:00"
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

# `src/components/graphedit/pending.ts`

Area: [[Reference/Desktop/TypeScript/components/graphedit/_area|TypeScript/components/graphedit]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides shared `pending` state or utility behavior for desktop components.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/graphedit/pending.ts](../../../../../../../apps/learnloop-tauri/src/components/graphedit/pending.ts) |
| Source lines | 274 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/graphedit/_area|TypeScript/components/graphedit]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `0cdf509e3186d78939189f5a6ad5a390198da908` |
| Commit timestamp | `2026-07-14T17:11:41-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] → [[Reference/Desktop/TypeScript/components/graphedit/pending|src/components/graphedit/pending.ts]]

## Public API

- `export type Relation = "prerequisite" | "confusable_with" | "related" | "part_of"` — type, line 14
- `export const RELATIONS: Relation[] = ["prerequisite", "related", "part_of", "confusable_with"]` — const, line 17
- `export const HONESTY_CAPTION = "prerequisite edges order the curriculum and shape the map` — const, line 20
- `export type PendingEdit = |` — type, line 27
- `export function newPid(): string` — function, line 41
- `export function compileEdits(pending: PendingEdit[]): GraphEditInput[]` — function, line 51
- `export interface ResolvedPending` — interface, line 80
- `export function resolvePending(pending: PendingEdit[]): ResolvedPending` — function, line 86
- `export function previewInput(pending: PendingEdit[]): PreviewKnowledgeMapInput` — function, line 100
- `export interface OrderEdge` — interface, line 116
- `export function effectivePrereqEdges(edges: ConceptGraphEdge[], pending: PendingEdit[]): OrderEdge[]` — function, line 123
- `export function topoOrder(concepts: ConceptGraphNode[], prereq: OrderEdge[]): string[]` — function, line 144
- `export function hasCycle(prereq: OrderEdge[]): boolean` — function, line 172
- `export function inferReorderEdits(params:` — function, line 200

## Internal implementation anchors

- `let pidCounter = 0` — let, line 40
- `const updatedById = new Map<string, Extract<PendingEdit,` — const, line 87
- `const deletedById = new Map<string, Extract<PendingEdit,` — const, line 88
- `const creates: Extract<PendingEdit,` — const, line 89
- `const addedEdges: PreviewKnowledgeMapInput["addedEdges"] = []` — const, line 101
- `const removedEdgeIds: string[] = []` — const, line 102
- `const out: OrderEdge[] = []` — const, line 125
- `const up = updatedById.get(e.id)` — const, line 128
- `const depth: Record<string, number> =` — const, line 145
- `const valid = prereq.filter((e)` — const, line 149
- `let changed = false` — let, line 151
- `const title = new Map(concepts.map((c)` — const, line 160
- `const da = depth[a] ?? 0` — const, line 164
- `const db = depth[b] ?? 0` — const, line 165
- `const adj = new Map<string, string[]>()` — const, line 173
- `const bucket = adj.get(e.source) ?? []` — const, line 175
- `const state = new Map<string, 0 | 1 | 2>()` — const, line 179
- `const visit = (node: string): boolean` — const, line 180
- `const s = state.get(next) ?? 0` — const, line 183
- `const committedPrereq = new Map<string, ConceptGraphEdge>()` — const, line 214
- `const effective = effectivePrereqEdges(edges, pending)` — const, line 222
- `const effectiveSet = new Set(effective.map((e)` — const, line 223
- `const movingEarlier = toIndex < fromIndex` — const, line 225
- `const crossed = movingEarlier ? ordered.slice(toIndex, fromIndex) : ordered.slice(fromIndex + 1, toIndex + 1)` — const, line 226
- `const edits: PendingEdit[] = []` — const, line 230
- `const staged = new Set<string>()` — const, line 231
- `const wantSource = movingEarlier ? movedId : other` — const, line 237
- `const wantTarget = movingEarlier ? other : movedId` — const, line 238
- `const wantKey = `$` — const, line 239
- `const oppositeKey = `$` — const, line 240
- `const contradicting = committedPrereq.get(oppositeKey)` — const, line 244
- `const resulting = effectivePrereqEdges(edges, [...pending, ...edits])` — const, line 269

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/graphedit/EditPopovers|src/components/graphedit/EditPopovers.tsx]] — import-or-re-export: `HONESTY_CAPTION`, `RELATIONS`, `Relation`; references `HONESTY_CAPTION`, `RELATIONS`, `Relation`
- [[Reference/Desktop/TypeScript/components/graphedit/PendingStrip|src/components/graphedit/PendingStrip.tsx]] — import-or-re-export: `PendingEdit`, `Relation`; references `PendingEdit`, `Relation`
- [[Reference/Desktop/TypeScript/components/graphedit/SyllabusColumn|src/components/graphedit/SyllabusColumn.tsx]] — import-or-re-export: `PendingEdit`; references `PendingEdit`
- [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] — import-or-re-export: `PendingEdit`, `compileEdits`, `effectivePrereqEdges`, `inferReorderEdits`, `newPid`, `previewInput`, `resolvePending`, `topoOrder`; references `PendingEdit`, `compileEdits`, `effectivePrereqEdges`, `inferReorderEdits`, `newPid`, `previewInput`, `resolvePending`, `topoOrder`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ConceptGraphEdge`, `ConceptGraphNode`, `GraphEditInput`, `PreviewKnowledgeMapInput`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Build a Study Map|Build a Study Map]] — owns the map-building journey.
- [[Concepts/Canonical Knowledge Model#Core entities|canonical knowledge entities]] — owns graph meaning.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_sidecar_knowledge_model.py](../../../../../../../tests/test_sidecar_knowledge_model.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_graph_editor_reads.py](../../../../../../../tests/test_graph_editor_reads.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_graph_edit_proposals.py](../../../../../../../tests/test_graph_edit_proposals.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_build_study_map_routing.py](../../../../../../../tests/test_build_study_map_routing.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/graphedit/pending.ts](../../../../../../../apps/learnloop-tauri/src/components/graphedit/pending.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

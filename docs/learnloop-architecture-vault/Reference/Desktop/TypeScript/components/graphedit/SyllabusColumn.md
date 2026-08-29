---
title: "Desktop module · src/components/graphedit/SyllabusColumn.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.graphedit.SyllabusColumn"
language: "TypeScript"
area: "TypeScript/components/graphedit"
source_path: "apps/learnloop-tauri/src/components/graphedit/SyllabusColumn.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/graphedit/SyllabusColumn.tsx"
source_commit: "96eb5c906aa28df898ce8a4485b0817efcf154bd"
source_commit_timestamp: "2026-07-14T23:16:00-04:00"
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

# `src/components/graphedit/SyllabusColumn.tsx`

Area: [[Reference/Desktop/TypeScript/components/graphedit/_area|TypeScript/components/graphedit]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `SyllabusColumn` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/graphedit/SyllabusColumn.tsx](../../../../../../../apps/learnloop-tauri/src/components/graphedit/SyllabusColumn.tsx) |
| Source lines | 224 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/graphedit/_area|TypeScript/components/graphedit]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `96eb5c906aa28df898ce8a4485b0817efcf154bd` |
| Commit timestamp | `2026-07-14T23:16:00-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] → [[Reference/Desktop/TypeScript/components/graphedit/SyllabusColumn|src/components/graphedit/SyllabusColumn.tsx]]

## Public API

- `export interface ReorderPrompt` — interface, line 12
- `export function SyllabusColumn(` — function, line 18

## Internal implementation anchors

- `const byId = new Map(concepts.map((c)` — const, line 41
- `const concept = byId.get(id)` — const, line 165
- `const isOver = overIndex === index && dragIndex !== null && dragIndex !== index` — const, line 167
- `const movedId = e.dataTransfer.getData("text/plain") || (dragIndex === null ? "" : ordered[dragIndex])` — const, line 190
- `const fromIndex = ordered.indexOf(movedId)` — const, line 191

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] — import-or-re-export: `ReorderPrompt`, `SyllabusColumn`; references `ReorderPrompt`, `SyllabusColumn`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ConceptGraphNode`
- [[Reference/Desktop/TypeScript/components/graphedit/pending|src/components/graphedit/pending.ts]] — import-or-re-export; imports `PendingEdit`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

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

1. Modify [apps/learnloop-tauri/src/components/graphedit/SyllabusColumn.tsx](../../../../../../../apps/learnloop-tauri/src/components/graphedit/SyllabusColumn.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

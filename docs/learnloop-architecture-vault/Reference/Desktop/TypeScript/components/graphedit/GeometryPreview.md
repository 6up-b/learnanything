---
title: "Desktop module · src/components/graphedit/GeometryPreview.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.graphedit.GeometryPreview"
language: "TypeScript"
area: "TypeScript/components/graphedit"
source_path: "apps/learnloop-tauri/src/components/graphedit/GeometryPreview.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/graphedit/GeometryPreview.tsx"
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

# `src/components/graphedit/GeometryPreview.tsx`

Area: [[Reference/Desktop/TypeScript/components/graphedit/_area|TypeScript/components/graphedit]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `GeometryPreview` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/graphedit/GeometryPreview.tsx](../../../../../../../apps/learnloop-tauri/src/components/graphedit/GeometryPreview.tsx) |
| Source lines | 143 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] → [[Reference/Desktop/TypeScript/components/graphedit/GeometryPreview|src/components/graphedit/GeometryPreview.tsx]]

## Public API

- `export function GeometryPreview(` — function, line 14

## Internal implementation anchors

- `const PANEL_W = 320` — const, line 10
- `const PLOT = 240` — const, line 11
- `const EPS = 0.012` — const, line 12
- `const frame = useMemo(()` — const, line 27
- `const all = [...preview.baseline.points, ...preview.points]` — const, line 29
- `const xs = all.map((p)` — const, line 31
- `const ys = all.map((p)` — const, line 32
- `const minX = Math.min(...xs)` — const, line 33
- `const maxX = Math.max(...xs)` — const, line 34
- `const minY = Math.min(...ys)` — const, line 35
- `const maxY = Math.max(...ys)` — const, line 36
- `const spanX = maxX - minX || 1` — const, line 37
- `const spanY = maxY - minY || 1` — const, line 38
- `const span = Math.max(spanX, spanY)` — const, line 39
- `const norm = (x: number, y: number)` — const, line 40
- `const newById = new Map(preview.points.map((p)` — const, line 44
- `const moves = preview.baseline.points .map((base)` — const, line 45
- `const next = newById.get(base.id)` — const, line 47
- `const b = norm(base.x, base.y)` — const, line 49
- `const n = norm(next.x, next.y)` — const, line 50
- `const dist = Math.hypot(n.nx - b.nx, n.ny - b.ny)` — const, line 51
- `const px = (v: number)` — const, line 58

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] — import-or-re-export: `GeometryPreview`; references `GeometryPreview`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `KnowledgeMapPreviewDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.
- [[Workflows/Build a Study Map|Build a Study Map]] — owns the map-building journey.
- [[Concepts/Canonical Knowledge Model#Core entities|canonical knowledge entities]] — owns graph meaning.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_sidecar_knowledge_model.py](../../../../../../../tests/test_sidecar_knowledge_model.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_graph_editor_reads.py](../../../../../../../tests/test_graph_editor_reads.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_graph_edit_proposals.py](../../../../../../../tests/test_graph_edit_proposals.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_build_study_map_routing.py](../../../../../../../tests/test_build_study_map_routing.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_review_log.py](../../../../../../../tests/test_review_log.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_learner_review_system_entries.py](../../../../../../../tests/test_learner_review_system_entries.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/graphedit/GeometryPreview.tsx](../../../../../../../apps/learnloop-tauri/src/components/graphedit/GeometryPreview.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

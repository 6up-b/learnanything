---
title: "Desktop module · src/screens/KnowledgeMapScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.KnowledgeMapScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/KnowledgeMapScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/KnowledgeMapScreen.tsx"
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

# `src/screens/KnowledgeMapScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `KnowledgeMapScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/KnowledgeMapScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/KnowledgeMapScreen.tsx) |
| Source lines | 589 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]]

## Public API

- `export function KnowledgeMapView(` — function, line 32
- `export function FacetFieldDetail(` — function, line 343

## Internal implementation anchors

- `const FRONTIER_LEVEL = 0.7` — const, line 30
- `const snapshotQuery = useCachedQuery(["get_knowledge_map"], ()` — const, line 37
- `const snapshot: KnowledgeMapSnapshot | null = snapshotQuery.data ?? null` — const, line 41
- `const historyQuery = useCachedQuery(["get_knowledge_map_history"], ()` — const, line 54
- `const history: KnowledgeMapHistory | null = historyQuery.data ?? null` — const, line 59
- `const decayQuery = useCachedQuery(["get_decay_pressure", null], ()` — const, line 63
- `const decay: DecayPressureDto | null = decayQuery.data?.pressure ?? null` — const, line 68
- `const canvas = useElementSize<HTMLDivElement>()` — const, line 74
- `const simple = simpleShell()` — const, line 81
- `const loadError = snapshotQuery.error ?? historyQuery.error ?? decayQuery.error` — const, line 86
- `const candidates = mode === "strata" ? snapshot.points : snapshot.facetField.points` — const, line 97
- `const points = snapshot?.points ?? []` — const, line 105
- `const pointById = new Map(points.map((point)` — const, line 111
- `const facetById = new Map(snapshot.facetField.points.map((point)` — const, line 112
- `const active = selected ? pointById.get(selected) ?? null : null` — const, line 113
- `const activeFacet = selected ? facetById.get(selected) ?? null : null` — const, line 114
- `const stat = (label: string, value: string, color?: string)` — const, line 370
- `const facetActionButton: CSSProperties =` — const, line 450
- `function PointDetail(` — function, line 461
- `const tone = point.mastery != null ? masteryTone(point.mastery, COLOR) : COLOR.textFaint` — const, line 481
- `const stat = (label: string, value: string | null, color?: string)` — const, line 482

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: dynamic import; no named call claim
- [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] — import-or-re-export: `KnowledgeMapView`; references `KnowledgeMapView`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DecayPressureDto`, `KnowledgeFacetPoint`, `KnowledgeItemTextNeighbors`, `KnowledgeMapHistory`, `KnowledgeMapPoint`, `KnowledgeMapSnapshot`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`, `useReportQueryError`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `masteryTone`
- [[Reference/Desktop/TypeScript/app/shell|src/app/shell.ts]] — import-or-re-export; imports `simpleShell`
- [[Reference/Desktop/TypeScript/components/FacetInspector|src/components/FacetInspector.tsx]] — import-or-re-export; imports `FacetInspector`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `SectionHeader`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EntityLink`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `ReportError`
- [[Reference/Desktop/TypeScript/screens/KnowledgeStrataView|src/screens/KnowledgeStrataView.tsx]] — import-or-re-export; imports `KnowledgeStrataView`
- [[Reference/Desktop/TypeScript/screens/KnowledgeTerrainView|src/screens/KnowledgeTerrainView.tsx]] — import-or-re-export; imports `KnowledgeTerrainView`
- [[Reference/Desktop/TypeScript/screens/KnowledgeWellView|src/screens/KnowledgeWellView.tsx]] — import-or-re-export; imports `ASSUMED_LABEL`, `KnowledgeWellView`
- [[Reference/Desktop/TypeScript/screens/knowledgeNeighbors|src/screens/knowledgeNeighbors.ts]] — import-or-re-export; imports `neighborCaption`
- [[Reference/Desktop/TypeScript/screens/wire3d|src/screens/wire3d.ts]] — import-or-re-export; imports `useElementSize`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Build a Study Map|Build a Study Map]] — owns the map-building journey.
- [[Concepts/Canonical Knowledge Model#Core entities|canonical knowledge entities]] — owns graph meaning.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/retryWiring.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/retryWiring.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/classicErrors.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/classicErrors.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/KnowledgeMapScreen.retry.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/KnowledgeMapScreen.retry.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/KnowledgeMapScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/KnowledgeMapScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/components/FacetIdentityPanel.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.FacetIdentityPanel"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/FacetIdentityPanel.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/FacetIdentityPanel.tsx"
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

# `src/components/FacetIdentityPanel.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `FacetIdentityPanel` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/FacetIdentityPanel.tsx](../../../../../../apps/learnloop-tauri/src/components/FacetIdentityPanel.tsx) |
| Source lines | 176 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] → [[Reference/Desktop/TypeScript/components/IngestActivity|src/components/IngestActivity.tsx]] → [[Reference/Desktop/TypeScript/components/FacetIdentityPanel|src/components/FacetIdentityPanel.tsx]]

## Public API

- `export function evidenceLabel(action: FacetIdentityActionDto): string | null` — function, line 27
- `export function FacetIdentityPanel(` — function, line 75
- `export function facetIdentityOf(result: Record<string, unknown> | null | undefined): FacetIdentitySummaryDto | null` — function, line 173

## Internal implementation anchors

- `const MAX_CLAIM = 110` — const, line 14
- `function short(text: string): string` — function, line 16
- `function verb(action: FacetIdentityActionDto): string` — function, line 20
- `const evidenced = action.evidencedFacets ?? []` — const, line 28
- `function describeLine(action: FacetIdentityActionDto)` — function, line 40
- `function skippedNote(summary: FacetIdentitySummaryDto): string | null` — function, line 57
- `function stateLabel(action: FacetIdentityActionDto): string | null` — function, line 65
- `const mounted = useRef(true)` — const, line 84
- `const runId = summary.runId ?? summary.actions?.[0]?.runId ?? null` — const, line 85
- `const note = skippedNote(summary)` — const, line 86
- `const refresh = useCallback(async ()` — const, line 88
- `const live = await api.listFacetIdentityActions(runId)` — const, line 91
- `async function undo(action: FacetIdentityActionDto)` — function, line 108
- `const result = await api.undoFacetIdentityAction(action.id)` — const, line 112
- `const updated = result.action ??` — const, line 113
- `const state = stateLabel(action)` — const, line 130
- `const evidence = evidenceLabel(action)` — const, line 131
- `const details = [ action.note, action.status === "applying" || action.status === "undoing" ? "finish it with learnloop doctor --fix-state" : null, evidence, action.contractNote, action.undoable && action.action !== "reword" ? "undo restores the facets` — const, line 132
- `const block = result?.facetIdentity as FacetIdentitySummaryDto | null | undefined` — const, line 174

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/IngestActivity|src/components/IngestActivity.tsx]] — import-or-re-export: `FacetIdentityPanel`, `facetIdentityOf`; references `FacetIdentityPanel`, `facetIdentityOf`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`, `FacetIdentityActionDto`, `FacetIdentitySummaryDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Build a Study Map|Build a Study Map]] — owns the map-building journey.
- [[Concepts/Canonical Knowledge Model#Core entities|canonical knowledge entities]] — owns graph meaning.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/FacetIdentityPanel.test.tsx](../../../../../../apps/learnloop-tauri/src/components/FacetIdentityPanel.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/components/FacetIdentityPanel.tsx](../../../../../../apps/learnloop-tauri/src/components/FacetIdentityPanel.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

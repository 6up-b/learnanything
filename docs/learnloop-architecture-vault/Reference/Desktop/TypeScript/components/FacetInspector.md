---
title: "Desktop module · src/components/FacetInspector.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.FacetInspector"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/FacetInspector.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/FacetInspector.tsx"
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

# `src/components/FacetInspector.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `FacetInspector` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/FacetInspector.tsx](../../../../../../apps/learnloop-tauri/src/components/FacetInspector.tsx) |
| Source lines | 852 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `971d7c274e09873d726d43578cd080e4d8865571` |
| Commit timestamp | `2026-07-27T06:01:19-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] → [[Reference/Desktop/TypeScript/components/FacetInspector|src/components/FacetInspector.tsx]]

## Public API

- `export function FacetInspector(` — function, line 30

## Internal implementation anchors

- `const LOCK_GLYPH = "\u` — const, line 28
- `let cancelled = false` — let, line 46
- `const message = err instanceof Error ? err.message : String(err)` — const, line 60
- `const onKey = (event: KeyboardEvent)` — const, line 71
- `function FacetBody(` — function, line 132
- `const locked = lock.locked` — const, line 142
- `function LockSection(` — function, line 258
- `function RestructureActions(` — function, line 287
- `function MergeFlow(` — function, line 322
- `let cancelled = false` — let, line 351
- `const subs = snap.vault?.subjects ?? []` — const, line 356
- `const pickOther = (summary: FacetSummaryDto)` — const, line 368
- `const eitherLocked = selfLocked || other?.locked === true || otherDetail?.lock.locked === true` — const, line 387
- `const submitMerge = async ()` — const, line 389
- `const retiredFacetId = survivor === "self" ? other.id : facetId` — const, line 391
- `const survivingFacetId = survivor === "self" ? facetId : other.id` — const, line 392
- `const res = await api.proposeFacetMerge(` — const, line 396
- `const submitRestructure = async ()` — const, line 410
- `const facetIds = other ? [facetId, other.id] : [facetId]` — const, line 414
- `const res = await api.queueRestructureRequest(` — const, line 415
- `function SplitFlow(` — function, line 529
- `const submit = async ()` — const, line 555
- `const res = await api.queueRestructureRequest(` — const, line 559
- `function LockReasonList(` — function, line 603
- `function ContractCompare(` — function, line 621
- `const rows: Array<` — const, line 632
- `const l = left.detail?.facet` — const, line 633
- `const r = rightDetail?.facet` — const, line 634
- `function CompareCol(` — function, line 664
- `function FacetAutocomplete(` — function, line 677
- `let cancelled = false` — let, line 692
- `const matches = useMemo(()` — const, line 706
- `const q = query.trim().toLowerCase()` — const, line 708
- `const pool = q ? all.filter((f)` — const, line 709
- `function StatCell(` — function, line 767
- `function ListBlock(` — function, line 776
- `const fmt = (value: number | null)` — const, line 790
- `const btnStyle: CSSProperties =` — const, line 792
- `const panelStyle: CSSProperties =` — const, line 802
- `const inputStyle: CSSProperties =` — const, line 809
- `const textareaStyle: CSSProperties =` — const, line 821
- `const radioLabel: CSSProperties =` — const, line 836
- `const ledgerRowStyle: CSSProperties =` — const, line 844

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export: `FacetInspector`; references `FacetInspector`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `FacetDetailDto`, `FacetSummaryDto`, `RestructureRequestDto`
- [[Reference/Desktop/TypeScript/components/KnowledgeModel|src/components/KnowledgeModel.tsx]] — import-or-re-export; imports `FacetEvidenceReceipt`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `Meta`, `Pill`, `SectionHeader`, `TermSelect`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EntityLink`

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

1. Modify [apps/learnloop-tauri/src/components/FacetInspector.tsx](../../../../../../apps/learnloop-tauri/src/components/FacetInspector.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

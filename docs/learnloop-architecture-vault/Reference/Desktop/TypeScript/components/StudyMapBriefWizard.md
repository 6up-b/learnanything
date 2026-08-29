---
title: "Desktop module · src/components/StudyMapBriefWizard.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.StudyMapBriefWizard"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/StudyMapBriefWizard.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/StudyMapBriefWizard.tsx"
source_commit: "0e91c7ba1b7ff32d5d093dd62826890b70445d3f"
source_commit_timestamp: "2026-08-03T22:04:38-04:00"
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

# `src/components/StudyMapBriefWizard.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `StudyMapBriefWizard` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/StudyMapBriefWizard.tsx](../../../../../../apps/learnloop-tauri/src/components/StudyMapBriefWizard.tsx) |
| Source lines | 458 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `0e91c7ba1b7ff32d5d093dd62826890b70445d3f` |
| Commit timestamp | `2026-08-03T22:04:38-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]] → [[Reference/Desktop/TypeScript/components/StudyMapBriefWizard|src/components/StudyMapBriefWizard.tsx]]

## Public API

- `export const STARTING_LEVELS:` — const, line 10
- `export function StudyMapBriefWizard(` — function, line 30

## Internal implementation anchors

- `type Outcome = "general_learning" | "reference_mastery" | "exam_prep"` — type, line 17
- `type PracticeItemsMode = "upfront" | "as_you_read"` — type, line 18
- `const OUTCOMES:` — const, line 19
- `const DEPTHS = ["intro", "standard", "deep"]` — const, line 24
- `const PRACTICE_ITEM_MODES:` — const, line 25
- `const steps = useMemo( ()` — const, line 63
- `const isLast = step === steps.length - 1` — const, line 67
- `const build = (): StudyMapBriefDto` — const, line 69
- `const brief: StudyMapBriefDto =` — const, line 70
- `const advance = ()` — const, line 92
- `const handler = (e: KeyboardEvent)` — const, line 101
- `const tag = (e.target as HTMLElement)?.tagName` — const, line 106
- `const current = steps[step]` — const, line 116
- `function ChipInput(` — function, line 321
- `const add = ()` — const, line 323
- `const value = draft.trim()` — const, line 324
- `function Label(` — function, line 372
- `const backdropStyle: CSSProperties =` — const, line 380
- `const modalStyle: CSSProperties =` — const, line 392
- `const headerStyle: CSSProperties =` — const, line 404
- `const footerStyle: CSSProperties =` — const, line 413
- `const inputStyle: CSSProperties =` — const, line 422
- `const primaryBtn: CSSProperties =` — const, line 433
- `const ghostBtn: CSSProperties =` — const, line 443
- `const segBtn: CSSProperties =` — const, line 453

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]] — import-or-re-export: `STARTING_LEVELS`; references `STARTING_LEVELS`
- [[Reference/Desktop/TypeScript/components/QuickAddDialog|src/components/QuickAddDialog.tsx]] — import-or-re-export: `StudyMapBriefWizard`; references `StudyMapBriefWizard`
- [[Reference/Desktop/TypeScript/components/SourceLibrarySidebar|src/components/SourceLibrarySidebar.tsx]] — import-or-re-export: `StudyMapBriefWizard`; references `StudyMapBriefWizard`
- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export: `STARTING_LEVELS`; references `STARTING_LEVELS`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `StartingLevel`, `StudyMapBriefDto`
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

1. Modify [apps/learnloop-tauri/src/components/StudyMapBriefWizard.tsx](../../../../../../apps/learnloop-tauri/src/components/StudyMapBriefWizard.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

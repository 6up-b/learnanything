---
title: "Desktop module · src/screens/desks/windows/PanelWindow.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.windows.PanelWindow"
language: "TypeScript"
area: "TypeScript/screens/desks/windows"
source_path: "apps/learnloop-tauri/src/screens/desks/windows/PanelWindow.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/windows/PanelWindow.tsx"
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

# `src/screens/desks/windows/PanelWindow.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/windows/_area|TypeScript/screens/desks/windows]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `PanelWindow` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/windows/PanelWindow.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/windows/PanelWindow.tsx) |
| Source lines | 166 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/windows/_area|TypeScript/screens/desks/windows]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/windows/PanelWindow|src/screens/desks/windows/PanelWindow.tsx]]

## Public API

- `export const PANEL_TITLES: Record<PanelContent["panel"], string> =` — const, line 27
- `export function RailHostPanel(` — function, line 35
- `export function LibraryPanel(` — function, line 66

## Internal implementation anchors

- `type PanelContent = Extract<ContentRefDto,` — type, line 25
- `const contractQuery = useCachedQuery(["reader_prompt_contract"], ()` — const, line 85
- `const contract = contractQuery.data ?? null` — const, line 86
- `const ctl = useLibraryAsk(` — const, line 87
- `const kept = useKeptComparisons(` — const, line 90
- `const notes = useNoteMarks(` — const, line 91
- `const cardOf = (sourceId: string | null | undefined)` — const, line 92
- `const pickPractice = (item: ProposedItemDto, proposalId: string | null)` — const, line 95
- `const asked = ctl.state?.request` — const, line 96
- `const hit = ctl.state?.ask.value?.hits[0]` — const, line 97
- `const at = asked?.identity ?` — const, line 98
- `const card = cardOf(at?.sourceId)` — const, line 101
- `const useExercise = (candidate: ExerciseCandidate)` — const, line 110
- `const card = cardOf(candidate.sourceId)` — const, line 111
- `const exerciseSettings = ctl.enabled ? contract?.libraryExercises ?? null : null` — const, line 118
- `const exercises: LibraryExercisesProps | null = exerciseSettings ?` — const, line 119
- `const ask = useCallback((text: string)` — const, line 130

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `LibraryPanel`, `PANEL_TITLES`, `RailHostPanel`; references `LibraryPanel`, `PANEL_TITLES`, `RailHostPanel`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ContentRefDto`, `LibraryHitDto`, `ProposedItemDto`, `SourceLibraryCard`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`
- [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] — import-or-re-export; imports `ReaderPassThrough`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryPane|src/screens/reader/LibraryPane.tsx]] — import-or-re-export; imports `LibraryPane`
- [[Reference/Desktop/TypeScript/screens/reader/ProposalExercises|src/screens/reader/ProposalExercises.tsx]] — import-or-re-export; imports `LibraryExercisesProps`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderNotes|src/screens/reader/ReaderNotes.tsx]] — import-or-re-export; imports `useNoteMarks`
- [[Reference/Desktop/TypeScript/screens/reader/compareKeepContext|src/screens/reader/compareKeepContext.ts]] — import-or-re-export; imports `CompareKeepContext`
- [[Reference/Desktop/TypeScript/screens/reader/exerciseCandidates (ts)|src/screens/reader/exerciseCandidates.ts]] — import-or-re-export; imports `ExerciseCandidate`, `exerciseOpenRequest`
- [[Reference/Desktop/TypeScript/screens/reader/notesContext|src/screens/reader/notesContext.ts]] — import-or-re-export; imports `NotesContext`
- [[Reference/Desktop/TypeScript/screens/reader/useKeptComparisons|src/screens/reader/useKeptComparisons.ts]] — import-or-re-export; imports `useKeptComparisons`
- [[Reference/Desktop/TypeScript/screens/reader/useLibraryAsk|src/screens/reader/useLibraryAsk.ts]] — import-or-re-export; imports `useLibraryAsk`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/windows/LibraryPanel.compare.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/windows/LibraryPanel.compare.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/windows/PanelWindow.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/windows/PanelWindow.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/components/AddToCollection.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.AddToCollection"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/AddToCollection.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/AddToCollection.tsx"
source_commit: "64d39668a1d275c2910f98388ac612ae5391d694"
source_commit_timestamp: "2026-07-27T19:00:47-05:00"
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

# `src/components/AddToCollection.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `AddToCollection` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/AddToCollection.tsx](../../../../../../apps/learnloop-tauri/src/components/AddToCollection.tsx) |
| Source lines | 250 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `64d39668a1d275c2910f98388ac612ae5391d694` |
| Commit timestamp | `2026-07-27T19:00:47-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] → [[Reference/Desktop/TypeScript/components/OutlineAndPlan|src/components/OutlineAndPlan.tsx]] → [[Reference/Desktop/TypeScript/components/AddToCollection|src/components/AddToCollection.tsx]]

## Public API

- `export function AddToCollectionPanel(` — function, line 33

## Internal implementation anchors

- `const SOURCE_ROLES = [ "primary_textbook", "lecture", "paper", "reference", "alternate_explanation", "problem_set", "exam", "notes" ] as const` — const, line 15
- `function kebab(value: string): string` — function, line 26
- `let cancelled = false` — let, line 62
- `const list = setsSnap.sourceSets ?? []` — const, line 66
- `const confirm = useCallback(async ()` — const, line 82
- `const member =` — const, line 87
- `let payload: SourceSetDto` — let, line 97
- `let title: string` — let, line 98
- `const members = [ ...sourceSet.members.filter((m)` — const, line 107
- `const id = kebab(newName)` — const, line 114
- `const scopeLabel = scopeUnitIds.length > 0 ? `$` — const, line 138
- `function ModeChip(` — function, line 233

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/OutlineAndPlan|src/components/OutlineAndPlan.tsx]] — import-or-re-export: `AddToCollectionPanel`; references `AddToCollectionPanel`
- [[Reference/Desktop/TypeScript/components/SourceLibrarySidebar|src/components/SourceLibrarySidebar.tsx]] — import-or-re-export: `AddToCollectionPanel`; references `AddToCollectionPanel`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`, `SourceSetDto`, `SourceSetSummaryDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `TermSelect`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/AddToCollection.tsx](../../../../../../apps/learnloop-tauri/src/components/AddToCollection.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

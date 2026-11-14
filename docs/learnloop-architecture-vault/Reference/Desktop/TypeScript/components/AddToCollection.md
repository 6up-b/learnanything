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
| Source lines | 276 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] → [[Reference/Desktop/TypeScript/components/OutlineAndPlan|src/components/OutlineAndPlan.tsx]] → [[Reference/Desktop/TypeScript/components/AddToCollection|src/components/AddToCollection.tsx]]

## Public API

- `export const SYLLABUS_ROLE_HINT = "syllabus: used only to scope what your deliverables need — never taught from, never practice, never protected (don't give it the exam role, or LearnLoop hides it whole)"` — const, line 30
- `export function AddToCollectionPanel(` — function, line 40

## Internal implementation anchors

- `const SOURCE_ROLES = [ "primary_textbook", "lecture", "paper", "reference", "alternate_explanation", "problem_set", "exam", "notes", "syllabus" ] as const` — const, line 16
- `function kebab(value: string): string` — function, line 33
- `let cancelled = false` — let, line 73
- `const list = setsSnap.sourceSets ?? []` — const, line 77
- `const confirm = useCallback(async ()` — const, line 93
- `const member =` — const, line 98
- `let payload: SourceSetDto` — let, line 109
- `let title: string` — let, line 110
- `const members = [ ...sourceSet.members.filter((m)` — const, line 119
- `const id = kebab(newName)` — const, line 126
- `const scopeLabel = scopeUnitIds.length > 0 ? `$` — const, line 150
- `function ModeChip(` — function, line 259

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/OutlineAndPlan|src/components/OutlineAndPlan.tsx]] — import-or-re-export: `AddToCollectionPanel`, `SYLLABUS_ROLE_HINT`; references `AddToCollectionPanel`, `SYLLABUS_ROLE_HINT`
- [[Reference/Desktop/TypeScript/components/SourceLibrarySidebar|src/components/SourceLibrarySidebar.tsx]] — import-or-re-export: `AddToCollectionPanel`; references `AddToCollectionPanel`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`, `SourceSetDto`, `SourceSetSummaryDto`
- [[Reference/Desktop/TypeScript/components/NewSubjectControl|src/components/NewSubjectControl.tsx]] — import-or-re-export; imports `NewSubjectControl`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `TermSelect`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/syllabusRole.test.tsx](../../../../../../apps/learnloop-tauri/src/components/syllabusRole.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/AddToCollection.test.tsx](../../../../../../apps/learnloop-tauri/src/components/AddToCollection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/AddToCollection.tsx](../../../../../../apps/learnloop-tauri/src/components/AddToCollection.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

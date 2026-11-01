---
title: "Desktop module · src/components/IntentControl.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.IntentControl"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/IntentControl.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/IntentControl.tsx"
source_commit: "462f02eaf8f6af6eb47ce6b7a895e21b04be309a"
source_commit_timestamp: "2026-10-19T23:41:22-04:00"
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

# `src/components/IntentControl.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `IntentControl` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/IntentControl.tsx](../../../../../../apps/learnloop-tauri/src/components/IntentControl.tsx) |
| Source lines | 219 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `462f02eaf8f6af6eb47ce6b7a895e21b04be309a` |
| Commit timestamp | `2026-10-19T23:41:22-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] → [[Reference/Desktop/TypeScript/components/IntentControl|src/components/IntentControl.tsx]]

## Public API

- `export function previewLine(preview: IntentChoicePreviewDto): string` — function, line 37
- `export function IntentControl(` — function, line 41
- `export function SubjectIntent(` — function, line 184

## Internal implementation anchors

- `const GROUPS: IntentChoice[][] = [ ["master", "learn", "keep", "light_touch"], ["check_once", "reference", "pause", "let_go"] ]` — const, line 21
- `const segment = (on: boolean, previewing: boolean)` — const, line 26
- `let live = true` — let, line 61
- `const current = view.current` — const, line 81
- `const byChoice = new Map(view.choices.map((choice)` — const, line 82
- `const shown = previewing ? byChoice.get(previewing) : current.choice !== "uncommitted" ? byChoice.get(current.choice) : null` — const, line 83
- `const choose = async (choice: IntentChoice)` — const, line 85
- `const saveDeadline = async ()` — const, line 99
- `const preview = byChoice.get(choice)` — const, line 126
- `const on = current.choice === choice` — const, line 128

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/BookCard|src/components/BookCard.tsx]] — import-or-re-export: `IntentControl`; references `IntentControl`
- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export: `IntentControl`, `SubjectIntent`; references `IntentControl`, `SubjectIntent`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`, `IntentChoice`, `IntentChoicePreviewDto`, `IntentScopeKind`, `IntentViewDto`
- [[Reference/Desktop/TypeScript/components/PlainParts|src/components/PlainParts.tsx]] — import-or-re-export; imports `quietLine`, `quietLink`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `SectionHeader`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/IntentControl.test.tsx](../../../../../../apps/learnloop-tauri/src/components/IntentControl.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/IntentControl.tsx](../../../../../../apps/learnloop-tauri/src/components/IntentControl.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

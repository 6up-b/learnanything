---
title: "Desktop module · src/components/CommandOverlayFrame.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.CommandOverlayFrame"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/CommandOverlayFrame.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/CommandOverlayFrame.tsx"
source_commit: "fa517c8bc9765da6c71430b15a4c41f3897c0736"
source_commit_timestamp: "2026-07-24T10:35:21-04:00"
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

# `src/components/CommandOverlayFrame.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `CommandOverlayFrame` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/CommandOverlayFrame.tsx](../../../../../../apps/learnloop-tauri/src/components/CommandOverlayFrame.tsx) |
| Source lines | 184 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `fa517c8bc9765da6c71430b15a4c41f3897c0736` |
| Commit timestamp | `2026-07-24T10:35:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/AdjudicationOverlay|src/components/AdjudicationOverlay.tsx]] → [[Reference/Desktop/TypeScript/components/CommandOverlayFrame|src/components/CommandOverlayFrame.tsx]]

## Public API

- `export const learnloopShowOverlayWidth = "min(1120px, 100%)"` — const, line 4
- `export function CommandOverlayFrame(` — function, line 11
- `export const commandOverlayActionStyle: CSSProperties =` — const, line 133

## Internal implementation anchors

- `const modalRef = useRef<HTMLElement | null>(null)` — const, line 40
- `const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null` — const, line 44
- `const focusable = Array.from( modalRef.current?.querySelectorAll<HTMLElement>( 'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])' ) ?? [] )` — const, line 68
- `const first = focusable[0]` — const, line 73
- `const last = focusable[focusable.length - 1]` — const, line 74
- `const commandOverlayBackdropStyle: CSSProperties =` — const, line 143
- `const commandOverlayModalStyle: CSSProperties =` — const, line 155
- `const commandOverlayHeaderStyle: CSSProperties =` — const, line 166
- `const commandOverlayFooterStyle: CSSProperties =` — const, line 175

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/AdjudicationOverlay|src/components/AdjudicationOverlay.tsx]] — import-or-re-export: `CommandOverlayFrame`, `commandOverlayActionStyle`; references `CommandOverlayFrame`, `commandOverlayActionStyle`
- [[Reference/Desktop/TypeScript/components/GoalWizard|src/components/GoalWizard.tsx]] — import-or-re-export: `CommandOverlayFrame`; references `CommandOverlayFrame`
- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export: `CommandOverlayFrame`, `commandOverlayActionStyle`, `learnloopShowOverlayWidth`; references `CommandOverlayFrame`, `commandOverlayActionStyle`, `learnloopShowOverlayWidth`
- [[Reference/Desktop/TypeScript/components/KnowledgeModel|src/components/KnowledgeModel.tsx]] — import-or-re-export: `CommandOverlayFrame`, `learnloopShowOverlayWidth`; references `CommandOverlayFrame`, `learnloopShowOverlayWidth`
- [[Reference/Desktop/TypeScript/components/WhyDiagnosisOverlay|src/components/WhyDiagnosisOverlay.tsx]] — import-or-re-export: `CommandOverlayFrame`; references `CommandOverlayFrame`
- [[Reference/Desktop/TypeScript/screens/ReviewScreen|src/screens/ReviewScreen.tsx]] — import-or-re-export: `CommandOverlayFrame`; references `CommandOverlayFrame`
- [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]] — import-or-re-export: `CommandOverlayFrame`; references `CommandOverlayFrame`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`

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

1. Modify [apps/learnloop-tauri/src/components/CommandOverlayFrame.tsx](../../../../../../apps/learnloop-tauri/src/components/CommandOverlayFrame.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

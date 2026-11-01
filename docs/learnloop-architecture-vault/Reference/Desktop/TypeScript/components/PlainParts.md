---
title: "Desktop module · src/components/PlainParts.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.PlainParts"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/PlainParts.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/PlainParts.tsx"
source_commit: "4475283b410b088e584ccba139204056a3c207e4"
source_commit_timestamp: "2026-10-15T16:18:02-04:00"
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

# `src/components/PlainParts.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `PlainParts` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/PlainParts.tsx](../../../../../../apps/learnloop-tauri/src/components/PlainParts.tsx) |
| Source lines | 108 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `4475283b410b088e584ccba139204056a3c207e4` |
| Commit timestamp | `2026-10-15T16:18:02-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/SessionFinishHud|src/components/SessionFinishHud.tsx]] → [[Reference/Desktop/TypeScript/components/PlainParts|src/components/PlainParts.tsx]]

## Public API

- `export function DetailsToggle(` — function, line 8
- `export function PrimaryAction(` — function, line 32
- `export function QuietAction(` — function, line 54
- `export function VoicePanel(` — function, line 73
- `export const quietLink: CSSProperties =` — const, line 92
- `export const quietLine: CSSProperties =` — const, line 104

## Internal implementation anchors

No non-exported declaration anchor was detected by the static extractor.

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/ClaimCheckFeedback|src/components/ClaimCheckFeedback.tsx]] — import-or-re-export: `quietLine`; references `quietLine`
- [[Reference/Desktop/TypeScript/components/IntentCheckFeedback|src/components/IntentCheckFeedback.tsx]] — import-or-re-export: `quietLine`, `quietLink`; references `quietLine`, `quietLink`
- [[Reference/Desktop/TypeScript/components/IntentControl|src/components/IntentControl.tsx]] — import-or-re-export: `quietLine`, `quietLink`; references `quietLine`, `quietLink`
- [[Reference/Desktop/TypeScript/components/SessionFinishHud|src/components/SessionFinishHud.tsx]] — import-or-re-export: `PrimaryAction`, `quietLine`; references `PrimaryAction`, `quietLine`
- [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]] — import-or-re-export: `DetailsToggle`, `PrimaryAction`, `quietLine`; references `DetailsToggle`, `PrimaryAction`, `quietLine`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `PrimaryAction`, `QuietAction`; references `PrimaryAction`, `QuietAction`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `DetailsToggle`, `PrimaryAction`, `QuietAction`, `VoicePanel`, `quietLine`, `quietLink`; references `DetailsToggle`, `PrimaryAction`, `QuietAction`, `VoicePanel`, `quietLine`, `quietLink`
- [[Reference/Desktop/TypeScript/screens/RepairScreen|src/screens/RepairScreen.tsx]] — import-or-re-export: `DetailsToggle`, `PrimaryAction`, `quietLine`; references `DetailsToggle`, `PrimaryAction`, `quietLine`
- [[Reference/Desktop/TypeScript/screens/feedback/CompareMethods|src/screens/feedback/CompareMethods.tsx]] — import-or-re-export: `quietLine`, `quietLink`; references `quietLine`, `quietLink`
- [[Reference/Desktop/TypeScript/screens/feedback/FeedbackSurface|src/screens/feedback/FeedbackSurface.tsx]] — import-or-re-export: `DetailsToggle`, `PrimaryAction`, `QuietAction`, `VoicePanel`, `quietLine`, `quietLink`; references `DetailsToggle`, `PrimaryAction`, `QuietAction`, `VoicePanel`, `quietLine`, `quietLink`
- [[Reference/Desktop/TypeScript/screens/practice/HintPanel|src/screens/practice/HintPanel.tsx]] — import-or-re-export: `quietLine`, `quietLink`; references `quietLine`, `quietLink`
- [[Reference/Desktop/TypeScript/screens/workbench/HelpLadder|src/screens/workbench/HelpLadder.tsx]] — import-or-re-export: `quietLink`; references `quietLink`
- [[Reference/Desktop/TypeScript/screens/workbench/RouteExample|src/screens/workbench/RouteExample.tsx]] — import-or-re-export: `quietLine`, `quietLink`; references `quietLine`, `quietLink`
- [[Reference/Desktop/TypeScript/screens/workbench/StepHints|src/screens/workbench/StepHints.tsx]] — import-or-re-export: `quietLine`, `quietLink`; references `quietLine`, `quietLink`
- [[Reference/Desktop/TypeScript/screens/workbench/WhereThisGoes|src/screens/workbench/WhereThisGoes.tsx]] — import-or-re-export: `quietLink`; references `quietLink`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck`, `npm test` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/PlainParts.tsx](../../../../../../apps/learnloop-tauri/src/components/PlainParts.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

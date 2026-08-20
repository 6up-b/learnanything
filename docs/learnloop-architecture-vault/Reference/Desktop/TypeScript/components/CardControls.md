---
title: "Desktop module · src/components/CardControls.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.CardControls"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/CardControls.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/CardControls.tsx"
source_commit: "6fb2c13944c0431c70d3dba01553c23f93db883d"
source_commit_timestamp: "2026-07-28T01:49:30-04:00"
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

# `src/components/CardControls.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `CardControls` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/CardControls.tsx](../../../../../../apps/learnloop-tauri/src/components/CardControls.tsx) |
| Source lines | 483 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `6fb2c13944c0431c70d3dba01553c23f93db883d` |
| Commit timestamp | `2026-07-28T01:49:30-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] → [[Reference/Desktop/TypeScript/components/CardControls|src/components/CardControls.tsx]]

## Public API

- `export function RungVariantActions(` — function, line 33
- `export function ProbeRemintAction(` — function, line 133
- `export function TeachBackAction(` — function, line 221
- `export function CardControls(` — function, line 266

## Internal implementation anchors

- `const REASON_LABEL: Record<RetirementReason, string> =` — const, line 13
- `type Panel = "reword" | "split" | "retire" | null` — type, line 27
- `const pollRef = useRef<number | null>(null)` — const, line 48
- `const request = async (direction: "easier" | "harder")` — const, line 57
- `const result = await api.requestRungVariant(` — const, line 62
- `const requestId = result.requestId` — const, line 64
- `const inactive = busy || disabled` — const, line 94
- `const linkStyle =` — const, line 95
- `let cancelled = false` — let, line 160
- `const keep = async ()` — const, line 176
- `const result = await api.remintDiagnosticProbe(` — const, line 180
- `const command = error as CommandError` — const, line 184
- `const inactive = busy || disabled || notice !== null` — const, line 195
- `const request = async ()` — const, line 234
- `const result = await api.requestTeachBack(` — const, line 238
- `const inactive = disabled || busy` — const, line 246
- `const run = async (fn: ()` — const, line 302
- `const reword = ()` — const, line 313
- `const input:` — const, line 315
- `const split = ()` — const, line 329
- `const result = await api.splitPracticeItem(` — const, line 331
- `const retire = ()` — const, line 341
- `const link = (label: string, target: Panel)` — const, line 351
- `const textarea = (value: string, set: (v: string)` — const, line 371
- `const action = (label: string, onClick: ()` — const, line 390

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export: `RungVariantActions`; references `RungVariantActions`
- [[Reference/Desktop/TypeScript/components/ProbeBlockResult|src/components/ProbeBlockResult.tsx]] — import-or-re-export: `ProbeRemintAction`; references `ProbeRemintAction`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `CardControls`, `ProbeRemintAction`; references `CardControls`, `ProbeRemintAction`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `CardControls`; references `CardControls`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`, `RETIREMENT_REASONS`, `RetirementReason`
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

1. Modify [apps/learnloop-tauri/src/components/CardControls.tsx](../../../../../../apps/learnloop-tauri/src/components/CardControls.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

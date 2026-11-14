---
title: "Desktop module · src/screens/CalibrationScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.CalibrationScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/CalibrationScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/CalibrationScreen.tsx"
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

# `src/screens/CalibrationScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `CalibrationScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/CalibrationScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/CalibrationScreen.tsx) |
| Source lines | 463 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/CalibrationScreen|src/screens/CalibrationScreen.tsx]]

## Public API

- `export function CalibrationScreen(` — function, line 43

## Internal implementation anchors

- `const SESSION_TONE: Record<string, string> =` — const, line 25
- `const EPISODE_TONE: Record<string, string> =` — const, line 32
- `function minutes(value: number): string` — function, line 39
- `const refresh = useCallback(()` — const, line 75
- `const onFocus = ()` — const, line 89
- `const nextTarget = progress?.status === "active" ? progress.nextTarget : null` — const, line 94
- `const stop = useCallback(async ()` — const, line 96
- `const quickCheck = progress?.quickCheck ?? null` — const, line 108
- `const onKey = (event: KeyboardEvent)` — const, line 112
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 114
- `const budgetFraction = progress.timeBudgetMinutes > 0 ? Math.min(progress.elapsedMinutes / progress.timeBudgetMinutes, 1) : 0` — const, line 191
- `const VERDICT: Record<QuickCheckResultDto["verdict"],` — const, line 340
- `function QuickCheckView(` — function, line 353
- `const nextTarget = progress.status === "active" ? progress.nextTarget : null` — const, line 372
- `const verdict = VERDICT[result.verdict]` — const, line 414

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `CalibrationScreen`; references `CalibrationScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CalibrationSessionProgressDto`, `CommandError`, `GuidedRedoDto`, `QuickCheckProgressDto`, `QuickCheckResultDto`
- [[Reference/Desktop/TypeScript/app/checkHandoff|src/app/checkHandoff.ts]] — import-or-re-export; imports `CheckHandoff`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/DialogueProbe|src/components/DialogueProbe.tsx]] — import-or-re-export; imports `DialogueProbePanel`
- [[Reference/Desktop/TypeScript/components/PlacementControls|src/components/PlacementControls.tsx]] — import-or-re-export; imports `ASSUMED_LABEL`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `BlockBar`, `COLOR`, `FONT_MONO`, `Faint`, `KeyBar`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `Card`, `Pill`, `SectionHeader`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/CalibrationScreen.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/CalibrationScreen.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/checkHandoff.test.tsx](../../../../../../apps/learnloop-tauri/src/app/checkHandoff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_calibration_sessions.py](../../../../../../tests/test_calibration_sessions.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_exam_calibration.py](../../../../../../tests/test_exam_calibration.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_answer_calibration_duel.py](../../../../../../tests/test_answer_calibration_duel.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/CalibrationScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/CalibrationScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

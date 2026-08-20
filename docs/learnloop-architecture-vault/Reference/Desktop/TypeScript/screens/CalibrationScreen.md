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
source_commit: "a6c3391bee0c4732249b52d238aa1660b1a3042e"
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
| Source lines | 300 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `a6c3391bee0c4732249b52d238aa1660b1a3042e` |
| Commit timestamp | `2026-07-28T01:49:30-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/CalibrationScreen|src/screens/CalibrationScreen.tsx]]

## Public API

- `export function CalibrationScreen(` — function, line 34

## Internal implementation anchors

- `const SESSION_TONE: Record<string, string> =` — const, line 16
- `const EPISODE_TONE: Record<string, string> =` — const, line 23
- `function minutes(value: number): string` — function, line 30
- `const refresh = useCallback(()` — const, line 57
- `const onFocus = ()` — const, line 71
- `const nextTarget = progress?.status === "active" ? progress.nextTarget : null` — const, line 76
- `const stop = useCallback(async ()` — const, line 78
- `const onKey = (event: KeyboardEvent)` — const, line 92
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 93
- `const budgetFraction = progress.timeBudgetMinutes > 0 ? Math.min(progress.elapsedMinutes / progress.timeBudgetMinutes, 1) : 0` — const, line 168

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `CalibrationScreen`; references `CalibrationScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CalibrationSessionProgressDto`, `CommandError`, `GuidedRedoDto`
- [[Reference/Desktop/TypeScript/components/DialogueProbe|src/components/DialogueProbe.tsx]] — import-or-re-export; imports `DialogueProbePanel`
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

- [tests/test_calibration_sessions.py](../../../../../../tests/test_calibration_sessions.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_exam_calibration.py](../../../../../../tests/test_exam_calibration.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_answer_calibration_duel.py](../../../../../../tests/test_answer_calibration_duel.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/CalibrationScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/CalibrationScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

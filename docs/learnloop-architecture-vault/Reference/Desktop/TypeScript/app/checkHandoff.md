---
title: "Desktop module · src/app/checkHandoff.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.checkHandoff"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/checkHandoff.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/checkHandoff.ts"
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

# `src/app/checkHandoff.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `CheckHandoff`, `STOP_AND_TEACH_LABEL`, `TEACH_AFTER_CHECK_LABEL`, `TUTOR_AFTER_CHECK_LABEL` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/checkHandoff.ts](../../../../../../apps/learnloop-tauri/src/app/checkHandoff.ts) |
| Source lines | 55 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/checkHandoff|src/app/checkHandoff.ts]]

## Public API

- `export interface CheckHandoff` — interface, line 10
- `export const STOP_AND_TEACH_LABEL = "Stop diagnosing and teach me"` — const, line 19
- `export const TEACH_AFTER_CHECK_LABEL = "Teach me this"` — const, line 20
- `export const TUTOR_AFTER_CHECK_LABEL = "Learn it with the tutor"` — const, line 21
- `export function handoffOpensLesson(onTeachFromCheck: ((handoff: CheckHandoff)` — function, line 24
- `export function useCheckHandoff(openLesson: (entry: LessonEntry | null)` — function, line 31

## Internal implementation anchors

- `const fallbackRef = useRef<(()` — const, line 33
- `const teachFromCheck = useCallback((handoff: CheckHandoff)` — const, line 37
- `const openFailed = useCallback((message: string)` — const, line 47
- `const fallback = fallbackRef.current` — const, line 48

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `useCheckHandoff`; references `useCheckHandoff`
- [[Reference/Desktop/TypeScript/components/DialogueProbe|src/components/DialogueProbe.tsx]] — import-or-re-export: `CheckHandoff`, `STOP_AND_TEACH_LABEL`; references `CheckHandoff`, `STOP_AND_TEACH_LABEL`
- [[Reference/Desktop/TypeScript/screens/CalibrationScreen|src/screens/CalibrationScreen.tsx]] — import-or-re-export: `CheckHandoff`; references `CheckHandoff`
- [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]] — import-or-re-export: `CheckHandoff`, `TEACH_AFTER_CHECK_LABEL`, `TUTOR_AFTER_CHECK_LABEL`, `handoffOpensLesson`; references `CheckHandoff`, `TEACH_AFTER_CHECK_LABEL`, `TUTOR_AFTER_CHECK_LABEL`, `handoffOpensLesson`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `CheckHandoff`, `STOP_AND_TEACH_LABEL`, `handoffOpensLesson`; references `CheckHandoff`, `STOP_AND_TEACH_LABEL`, `handoffOpensLesson`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`
- [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] — import-or-re-export; imports `LessonEntry`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/app/checkHandoff.test.tsx](../../../../../../apps/learnloop-tauri/src/app/checkHandoff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/checkHandoff.ts](../../../../../../apps/learnloop-tauri/src/app/checkHandoff.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

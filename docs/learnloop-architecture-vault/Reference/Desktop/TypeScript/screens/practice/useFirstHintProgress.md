---
title: "Desktop module · src/screens/practice/useFirstHintProgress.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.practice.useFirstHintProgress"
language: "TypeScript"
area: "TypeScript/screens/practice"
source_path: "apps/learnloop-tauri/src/screens/practice/useFirstHintProgress.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/practice/useFirstHintProgress.ts"
source_commit: "d03b6bba09389c9eb2b610b4500f5d31341ffa9e"
source_commit_timestamp: "2026-10-18T17:30:53-04:00"
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

# `src/screens/practice/useFirstHintProgress.ts`

Area: [[Reference/Desktop/TypeScript/screens/practice/_area|TypeScript/screens/practice]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `FirstHintProgressMarker`, `useFirstHintProgress` within the desktop's TypeScript/screens/practice ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/practice/useFirstHintProgress.ts](../../../../../../../apps/learnloop-tauri/src/screens/practice/useFirstHintProgress.ts) |
| Source lines | 58 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/practice/_area|TypeScript/screens/practice]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `d03b6bba09389c9eb2b610b4500f5d31341ffa9e` |
| Commit timestamp | `2026-10-18T17:30:53-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/practice/useFirstHintProgress|src/screens/practice/useFirstHintProgress.ts]]

## Public API

- `export interface FirstHintProgressMarker` — interface, line 23
- `export function useFirstHintProgress(options:` — function, line 33

## Internal implementation anchors

- `const initial = options.enabled ? options.restored ?? null : null` — const, line 40
- `const claimed = useRef<FirstHintProgress | null>(initial)` — const, line 43
- `const unknown = useRef(false)` — const, line 46
- `const enabled = options.enabled` — const, line 48
- `const mark = useCallback((progress: FirstHintProgress)` — const, line 49
- `const noteUntimedHint = useCallback(()` — const, line 54

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `useFirstHintProgress`; references `useFirstHintProgress`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `FirstHintProgress`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/practice/useFirstHintProgress.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/practice/useFirstHintProgress.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/practice/DifficultyRatingTap.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/practice/DifficultyRatingTap.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_large_practice_flow.py](../../../../../../../tests/test_large_practice_flow.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_practice_information.py](../../../../../../../tests/test_practice_information.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_diagnostic.py](../../../../../../../tests/test_sidecar_diagnostic.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/practice/useFirstHintProgress.ts](../../../../../../../apps/learnloop-tauri/src/screens/practice/useFirstHintProgress.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

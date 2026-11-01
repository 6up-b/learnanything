---
title: "Desktop module · src/screens/practice/hintCopy.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.practice.hintCopy"
language: "TypeScript"
area: "TypeScript/screens/practice"
source_path: "apps/learnloop-tauri/src/screens/practice/hintCopy.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/practice/hintCopy.ts"
source_commit: "0fdf8f931f685d718d6e467c5b8d59f9879c021d"
source_commit_timestamp: "2026-10-18T09:29:06-04:00"
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

# `src/screens/practice/hintCopy.ts`

Area: [[Reference/Desktop/TypeScript/screens/practice/_area|TypeScript/screens/practice]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `HINT_COPY`, `SHORTCUT_COPY`, `HELP_STYLE_COPY`, `FORBIDDEN_WORDING` within the desktop's TypeScript/screens/practice ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/practice/hintCopy.ts](../../../../../../../apps/learnloop-tauri/src/screens/practice/hintCopy.ts) |
| Source lines | 62 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/practice/_area|TypeScript/screens/practice]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `0fdf8f931f685d718d6e467c5b8d59f9879c021d` |
| Commit timestamp | `2026-10-18T09:29:06-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/practice/HintPanel|src/screens/practice/HintPanel.tsx]] → [[Reference/Desktop/TypeScript/screens/practice/hintCopy|src/screens/practice/hintCopy.ts]]

## Public API

- `export const HINT_COPY =` — const, line 8
- `export const SHORTCUT_COPY: ReadonlyArray<` — const, line 30
- `export const HELP_STYLE_COPY: ReadonlyArray<` — const, line 54
- `export const FORBIDDEN_WORDING = ["you don't understand", "you struggle", "weak"] as const` — const, line 62

## Internal implementation anchors

No non-exported declaration anchor was detected by the static extractor.

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/practice/HelpStyleSettings|src/screens/practice/HelpStyleSettings.tsx]] — import-or-re-export: `HELP_STYLE_COPY`, `HINT_COPY`; references `HELP_STYLE_COPY`, `HINT_COPY`
- [[Reference/Desktop/TypeScript/screens/practice/HintPanel|src/screens/practice/HintPanel.tsx]] — import-or-re-export: `HELP_STYLE_COPY`, `HINT_COPY`, `SHORTCUT_COPY`; references `HELP_STYLE_COPY`, `HINT_COPY`, `SHORTCUT_COPY`
- [[Reference/Desktop/TypeScript/screens/practice/useAdaptiveHints|src/screens/practice/useAdaptiveHints.ts]] — import-or-re-export: `HINT_COPY`; references `HINT_COPY`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `HelpStyle`, `HintShortcut`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/practice/hintCopy.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/practice/hintCopy.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/practice/hintCopy.ts](../../../../../../../apps/learnloop-tauri/src/screens/practice/hintCopy.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

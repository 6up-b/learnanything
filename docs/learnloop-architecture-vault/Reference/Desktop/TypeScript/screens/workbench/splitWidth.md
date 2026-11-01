---
title: "Desktop module · src/screens/workbench/splitWidth.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.workbench.splitWidth"
language: "TypeScript"
area: "TypeScript/screens/workbench"
source_path: "apps/learnloop-tauri/src/screens/workbench/splitWidth.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/workbench/splitWidth.ts"
source_commit: "e6fd14844aad42f2dab12ad7edd02e250c033734"
source_commit_timestamp: "2026-10-17T05:11:36-04:00"
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

# `src/screens/workbench/splitWidth.ts`

Area: [[Reference/Desktop/TypeScript/screens/workbench/_area|TypeScript/screens/workbench]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `MIN_WORKBENCH_WIDTH`, `MIN_SOURCE_WIDTH`, `NARROW_BREAKPOINT`, `SPLIT_WIDTH_KEY` and related exports within the desktop's TypeScript/screens/workbench ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/workbench/splitWidth.ts](../../../../../../../apps/learnloop-tauri/src/screens/workbench/splitWidth.ts) |
| Source lines | 43 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/workbench/_area|TypeScript/screens/workbench]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `e6fd14844aad42f2dab12ad7edd02e250c033734` |
| Commit timestamp | `2026-10-17T05:11:36-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useReaderWorkbench|src/screens/reader/useReaderWorkbench.ts]] → [[Reference/Desktop/TypeScript/screens/workbench/splitWidth|src/screens/workbench/splitWidth.ts]]

## Public API

- `export const MIN_WORKBENCH_WIDTH = 480` — const, line 6
- `export const MIN_SOURCE_WIDTH = 360` — const, line 8
- `export const NARROW_BREAKPOINT = 1040` — const, line 9
- `export const SPLIT_WIDTH_KEY = "ll.workbench.splitWidth"` — const, line 10
- `export const SPLIT_STEP = 24` — const, line 11
- `export function defaultSplitWidth(windowWidth: number): number` — function, line 13
- `export function clampSplitWidth(width: number, windowWidth: number): number` — function, line 17
- `export function isNarrow(windowWidth: number): boolean` — function, line 22
- `export function readSplitWidth(): number | null` — function, line 27
- `export function writeSplitWidth(width: number): void` — function, line 37

## Internal implementation anchors

- `const max = Math.max(MIN_WORKBENCH_WIDTH, windowWidth - MIN_SOURCE_WIDTH)` — const, line 18
- `const raw = window.localStorage.getItem(SPLIT_WIDTH_KEY)` — const, line 29
- `const value = raw === null ? Number.NaN : Number(raw)` — const, line 30

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/LibraryPane|src/screens/reader/LibraryPane.tsx]] — import-or-re-export: `MIN_WORKBENCH_WIDTH`, `SPLIT_STEP`, `clampSplitWidth`, `isNarrow`; references `MIN_WORKBENCH_WIDTH`, `SPLIT_STEP`, `clampSplitWidth`, `isNarrow`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderWorkingPosture|src/screens/reader/ReaderWorkingPosture.tsx]] — import-or-re-export: `MIN_WORKBENCH_WIDTH`, `SPLIT_STEP`, `clampSplitWidth`; references `MIN_WORKBENCH_WIDTH`, `SPLIT_STEP`, `clampSplitWidth`
- [[Reference/Desktop/TypeScript/screens/reader/comparePoints|src/screens/reader/comparePoints.ts]] — import-or-re-export: `NARROW_BREAKPOINT`; references `NARROW_BREAKPOINT`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderWorkbench|src/screens/reader/useReaderWorkbench.ts]] — import-or-re-export: `SPLIT_STEP`, `clampSplitWidth`, `defaultSplitWidth`, `isNarrow`, `readSplitWidth`, `writeSplitWidth`; references `SPLIT_STEP`, `clampSplitWidth`, `defaultSplitWidth`, `isNarrow`, `readSplitWidth`, `writeSplitWidth`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/workbench/stepModel.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/workbench/stepModel.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/workbench/splitWidth.ts](../../../../../../../apps/learnloop-tauri/src/screens/workbench/splitWidth.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

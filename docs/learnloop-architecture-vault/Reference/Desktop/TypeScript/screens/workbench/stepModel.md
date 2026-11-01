---
title: "Desktop module · src/screens/workbench/stepModel.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.workbench.stepModel"
language: "TypeScript"
area: "TypeScript/screens/workbench"
source_path: "apps/learnloop-tauri/src/screens/workbench/stepModel.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/workbench/stepModel.ts"
source_commit: "1e38affc9a6f8d6442cc80af734467b685b637ed"
source_commit_timestamp: "2026-10-18T15:49:25-04:00"
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

# `src/screens/workbench/stepModel.ts`

Area: [[Reference/Desktop/TypeScript/screens/workbench/_area|TypeScript/screens/workbench]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `BOOK_OPEN_ENTRIES`, `defaultBookVisible`, `LocalStep`, `fromServer` and related exports within the desktop's TypeScript/screens/workbench ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/workbench/stepModel.ts](../../../../../../../apps/learnloop-tauri/src/screens/workbench/stepModel.ts) |
| Source lines | 112 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/workbench/_area|TypeScript/screens/workbench]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `1e38affc9a6f8d6442cc80af734467b685b637ed` |
| Commit timestamp | `2026-10-18T15:49:25-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/workbench/stepModel|src/screens/workbench/stepModel.ts]]

## Public API

- `export const BOOK_OPEN_ENTRIES: ReadonlySet<WorkbenchEntry> = new Set<WorkbenchEntry>(["work_through", "resume", "path_exercise"])` — const, line 8
- `export function defaultBookVisible(entry: WorkbenchEntry, origin: WorkbenchOrigin): boolean` — function, line 10
- `export interface LocalStep` — interface, line 14
- `export function fromServer(steps: readonly WorkbenchStepDto[]): LocalStep[]` — function, line 29
- `export function insertAfter(steps: readonly LocalStep[], afterKey: string | null, step:` — function, line 36
- `export function updateLocal(steps: readonly LocalStep[], key: string, patch: Partial<LocalStep>): LocalStep[]` — function, line 43
- `export function deleteLocal(steps: readonly LocalStep[], key: string): LocalStep[]` — function, line 47
- `export function restoreLocal(steps: readonly LocalStep[], key: string): LocalStep[]` — function, line 51
- `export function liveSteps(steps: readonly LocalStep[]): LocalStep[]` — function, line 55
- `export function stepChain(step: LocalStep): string | null` — function, line 60
- `export function problemTitle(stem: string): string` — function, line 65
- `export type SaveState = "saved" | "saving" | "retrying" | "offline" | "rejected"` — type, line 70
- `export interface SaveStatus` — interface, line 73
- `export const WORKBENCH_COPY =` — const, line 80
- `export function savedLabel(status: SaveStatus, nowMs: number = Date.now()): string` — function, line 103

## Internal implementation anchors

- `const entry: LocalStep =` — const, line 37
- `const index = afterKey === null ? -1 : steps.findIndex((existing)` — const, line 38
- `const match = /^\s*(Exercise|Problem|Question|Example)\s+([0-9]+(?:\.[0-9]+)*[a-z]?)/i.exec(stem)` — const, line 66
- `const at = status.savedAt ? Date.parse(status.savedAt) : Number.NaN` — const, line 108
- `const minutes = Math.floor((nowMs - at) / 60000)` — const, line 110

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `WORKBENCH_COPY`, `problemTitle`; references `WORKBENCH_COPY`, `problemTitle`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderWorkingPosture|src/screens/reader/ReaderWorkingPosture.tsx]] — import-or-re-export: `WORKBENCH_COPY`; references `WORKBENCH_COPY`
- [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] — import-or-re-export: `WORKBENCH_COPY`, `liveSteps`, `problemTitle`, `savedLabel`, `stepChain`; references `WORKBENCH_COPY`, `liveSteps`, `problemTitle`, `savedLabel`, `stepChain`
- [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchSession|src/screens/workbench/useWorkbenchSession.ts]] — import-or-re-export: `LocalStep`, `SaveStatus`, `deleteLocal`, `fromServer`, `insertAfter`, `restoreLocal`, `updateLocal`; references `LocalStep`, `SaveStatus`, `deleteLocal`, `fromServer`, `insertAfter`, `restoreLocal`, `updateLocal`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `WorkbenchEntry`, `WorkbenchOrigin`, `WorkbenchStepDto`, `WorkbenchStepKind`, `WorkbenchStepVersionDto`

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

1. Modify [apps/learnloop-tauri/src/screens/workbench/stepModel.ts](../../../../../../../apps/learnloop-tauri/src/screens/workbench/stepModel.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

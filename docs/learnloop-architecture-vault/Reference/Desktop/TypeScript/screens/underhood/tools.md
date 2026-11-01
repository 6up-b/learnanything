---
title: "Desktop module · src/screens/underhood/tools.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.underhood.tools"
language: "TypeScript"
area: "TypeScript/screens/underhood"
source_path: "apps/learnloop-tauri/src/screens/underhood/tools.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/underhood/tools.tsx"
source_commit: "05f21f30203369be5da256b6b776c87f47a9c50b"
source_commit_timestamp: "2026-10-21T11:29:39-04:00"
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

# `src/screens/underhood/tools.tsx`

Area: [[Reference/Desktop/TypeScript/screens/underhood/_area|TypeScript/screens/underhood]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `tools` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/underhood/tools.tsx](../../../../../../../apps/learnloop-tauri/src/screens/underhood/tools.tsx) |
| Source lines | 147 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/underhood/_area|TypeScript/screens/underhood]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `05f21f30203369be5da256b6b776c87f47a9c50b` |
| Commit timestamp | `2026-10-21T11:29:39-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/underhood/tools|src/screens/underhood/tools.tsx]]

## Public API

- `export function stateDatabasePath(nodes: VaultTreeNode[]): string | null` — function, line 20
- `export function DataTool(` — function, line 38
- `export function InspectorTool(` — function, line 49
- `export function CalibrationTool(` — function, line 88
- `export function MistakesTool(` — function, line 124
- `export function SpendTool(` — function, line 136

## Internal implementation anchors

- `const SqliteBrowser = lazy(()` — const, line 13
- `function ToolNote(` — function, line 15
- `let fallback: string | null = null` — let, line 21
- `const walk = (list: VaultTreeNode[]): string | null` — const, line 22
- `const nested = walk(node.children)` — const, line 27
- `const tree = useCachedQuery(["get_vault_tree"], ()` — const, line 39
- `const path = stateDatabasePath(tree.data.tree)` — const, line 43
- `const open = (value: string)` — const, line 51
- `const trimmed = value.trim()` — const, line 52

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `CalibrationTool`, `DataTool`, `InspectorTool`, `MistakesTool`, `SpendTool`; references `CalibrationTool`, `DataTool`, `InspectorTool`, `MistakesTool`, `SpendTool`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `SessionSnapshot`, `VaultTreeNode`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/SqliteBrowser|src/screens/SqliteBrowser.tsx]] — dynamic import

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/SqliteBrowser.readOnly.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/SqliteBrowser.readOnly.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/underhood/tools.tsx](../../../../../../../apps/learnloop-tauri/src/screens/underhood/tools.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

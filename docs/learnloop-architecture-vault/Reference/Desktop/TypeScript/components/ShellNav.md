---
title: "Desktop module · src/components/ShellNav.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.ShellNav"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/ShellNav.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/ShellNav.tsx"
source_commit: "725ef0e14d3ada9d88baaebc51a3273fc88226d0"
source_commit_timestamp: "2026-10-22T17:25:40-04:00"
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

# `src/components/ShellNav.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `ShellNav` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/ShellNav.tsx](../../../../../../apps/learnloop-tauri/src/components/ShellNav.tsx) |
| Source lines | 225 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `725ef0e14d3ada9d88baaebc51a3273fc88226d0` |
| Commit timestamp | `2026-10-22T17:25:40-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] → [[Reference/Desktop/TypeScript/components/ShellNav|src/components/ShellNav.tsx]]

## Public API

- `export interface SimpleNavProps` — interface, line 17
- `export function SimpleNav(` — function, line 31

## Internal implementation anchors

- `const current = place.id === active` — const, line 52
- `function MoreMenu(` — function, line 97
- `const wrapRef = useRef<HTMLDivElement | null>(null)` — const, line 115
- `const buttonRef = useRef<HTMLButtonElement | null>(null)` — const, line 116
- `const recents = useMemo(()` — const, line 119
- `const list = listRecentVaults()` — const, line 121
- `const labelFor = useMemo(()` — const, line 125
- `const counts = new Map<string, number>()` — const, line 126
- `const onDocMouseDown = (event: MouseEvent)` — const, line 133
- `const choose = (action: ()` — const, line 140
- `const openAnother = async ()` — const, line 146
- `const selected = await openDialog(` — const, line 148
- `const current = vaultRoot ? samePath(path, vaultRoot) : false` — const, line 193

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export: `SimpleNav`, `SimpleNavProps`; references `SimpleNav`, `SimpleNavProps`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/app/recentVaults|src/app/recentVaults.ts]] — import-or-re-export; imports `listRecentVaults`, `samePath`, `vaultName`, `vaultNameWithParent`
- [[Reference/Desktop/TypeScript/app/shell|src/app/shell.ts]] — import-or-re-export; imports `PLACES`, `Place`
- [[Reference/Desktop/TypeScript/components/frameFocus|src/components/frameFocus.ts]] — import-or-re-export; imports `releaseFocusAfterPointer`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `@tauri-apps/plugin-dialog`, `react`

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

1. Modify [apps/learnloop-tauri/src/components/ShellNav.tsx](../../../../../../apps/learnloop-tauri/src/components/ShellNav.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

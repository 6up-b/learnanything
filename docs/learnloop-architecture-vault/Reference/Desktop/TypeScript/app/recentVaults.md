---
title: "Desktop module · src/app/recentVaults.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.recentVaults"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/recentVaults.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/recentVaults.ts"
source_commit: "e3c6871bd2ed939ab9dcdf98d0ae9bdb19ded1ec"
source_commit_timestamp: "2026-07-23T15:53:16-05:00"
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

# `src/app/recentVaults.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Persists and normalizes the renderer's recent-vault list.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/recentVaults.ts](../../../../../../apps/learnloop-tauri/src/app/recentVaults.ts) |
| Source lines | 61 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `e3c6871bd2ed939ab9dcdf98d0ae9bdb19ded1ec` |
| Commit timestamp | `2026-07-23T15:53:16-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/recentVaults|src/app/recentVaults.ts]]

## Public API

- `export function samePath(a: string, b: string): boolean` — function, line 15
- `export function vaultName(path: string): string` — function, line 21
- `export function vaultNameWithParent(path: string): string` — function, line 27
- `export function listRecentVaults(): string[]` — function, line 33
- `export function recordRecentVault(path: string): void` — function, line 45
- `export function removeRecentVault(path: string): void` — function, line 54

## Internal implementation anchors

- `const KEY = "learnloop.recentVaults"` — const, line 5
- `const MAX = 8` — const, line 6
- `function pathKey(path: string): string` — function, line 11
- `const parts = path.replace(/\\/g, "/").split("/").filter(Boolean)` — const, line 22
- `const parts = path.replace(/\\/g, "/").split("/").filter(Boolean)` — const, line 28
- `const raw = localStorage.getItem(KEY)` — const, line 35
- `const parsed = JSON.parse(raw)` — const, line 37
- `const next = [path, ...listRecentVaults().filter((p)` — const, line 47
- `const next = listRecentVaults().filter((p)` — const, line 56

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `recordRecentVault`, `removeRecentVault`; references `recordRecentVault`, `removeRecentVault`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export: `listRecentVaults`, `samePath`, `vaultName`, `vaultNameWithParent`; references `listRecentVaults`, `samePath`, `vaultName`, `vaultNameWithParent`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/recentVaults.ts](../../../../../../apps/learnloop-tauri/src/app/recentVaults.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/app/vaultTransition.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.vaultTransition"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/vaultTransition.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/vaultTransition.ts"
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

# `src/app/vaultTransition.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `vaultKey`, `noteActiveVault`, `onVaultActive`, `registerVaultDraft` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/vaultTransition.ts](../../../../../../apps/learnloop-tauri/src/app/vaultTransition.ts) |
| Source lines | 64 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/vaultTransition|src/app/vaultTransition.ts]]

## Public API

- `export function vaultKey(): string | null` — function, line 21
- `export function noteActiveVault(root: string | null | undefined): void` — function, line 26
- `export function onVaultActive(listener: (key: string)` — function, line 33
- `export function registerVaultDraft(owner: DraftOwner): ()` — function, line 38
- `export async function selectWithDraftFlush<T>(select: ()` — function, line 44

## Internal implementation anchors

- `type DraftOwner =` — type, line 1
- `const drafts = new Set<DraftOwner>()` — const, line 7
- `let selecting = false` — let, line 8
- `let noted = ""` — let, line 16
- `let between = false` — let, line 17
- `const activeListeners = new Set<(key: string)` — const, line 18
- `const owners = [...drafts]` — const, line 47
- `const results = await Promise.allSettled(owners.map((owner)` — const, line 50
- `const failed = results.find((result)` — const, line 51

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `noteActiveVault`, `selectWithDraftFlush`; references `noteActiveVault`, `selectWithDraftFlush`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `registerVaultDraft`; references `registerVaultDraft`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export: `registerVaultDraft`, `vaultKey`; references `registerVaultDraft`, `vaultKey`
- [[Reference/Desktop/TypeScript/screens/reader/readingReports|src/screens/reader/readingReports.ts]] — import-or-re-export: `onVaultActive`, `registerVaultDraft`, `vaultKey`; references `onVaultActive`, `registerVaultDraft`, `vaultKey`
- [[Reference/Desktop/TypeScript/screens/reader/useCueImpressions|src/screens/reader/useCueImpressions.ts]] — import-or-re-export: `registerVaultDraft`, `vaultKey`; references `registerVaultDraft`, `vaultKey`
- [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchSession|src/screens/workbench/useWorkbenchSession.ts]] — import-or-re-export: `registerVaultDraft`; references `registerVaultDraft`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/source/ScopedSource.followsLearner.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/desks/source/ScopedSource.followsLearner.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/PracticeScreen.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/vaultTransition.ts](../../../../../../apps/learnloop-tauri/src/app/vaultTransition.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

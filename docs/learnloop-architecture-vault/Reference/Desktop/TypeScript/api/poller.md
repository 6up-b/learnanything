---
title: "Desktop module · src/api/poller.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.api.poller"
language: "TypeScript"
area: "TypeScript/api"
source_path: "apps/learnloop-tauri/src/api/poller.ts"
source_paths:
  - "apps/learnloop-tauri/src/api/poller.ts"
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

# `src/api/poller.ts`

Area: [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `PollResult`, `PollRegistration`, `PollerOptions`, `Poller` and related exports within the desktop's TypeScript/api ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/api/poller.ts](../../../../../../apps/learnloop-tauri/src/api/poller.ts) |
| Source lines | 141 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/api/poller|src/api/poller.ts]]

## Public API

- `export interface PollResult` — interface, line 10
- `export interface PollRegistration<T>` — interface, line 15
- `export interface PollerOptions` — interface, line 34
- `export class Poller` — class, line 41
- `export const poller = new Poller()` — const, line 141

## Internal implementation anchors

- `interface Entry` — interface, line 24
- `const reg = registration as unknown as PollRegistration<unknown>` — const, line 59
- `let entry = this.entries.get(registration.key)` — let, line 60
- `const work: Promise<void>[] = []` — const, line 85
- `const live = [...entry.listeners].filter((listener)` — const, line 88
- `let done = false` — let, line 100
- `const result = listener.onResult(value)` — const, line 102
- `const entry = this.entries.get(key)` — const, line 121

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `Poller`, `appPoller`; references `Poller`, `appPoller`
- [[Reference/Desktop/TypeScript/screens/desks/companion/asks|src/screens/desks/companion/asks.ts]] — import-or-re-export: `Poller`; references `Poller`
- [[Reference/Desktop/TypeScript/screens/desks/menu/ContextMenu|src/screens/desks/menu/ContextMenu.tsx]] — import-or-re-export: `Poller`; references `Poller`
- [[Reference/Desktop/TypeScript/screens/desks/menu/ExerciseSheet|src/screens/desks/menu/ExerciseSheet.tsx]] — import-or-re-export: `Poller`; references `Poller`
- [[Reference/Desktop/TypeScript/screens/desks/pads/host|src/screens/desks/pads/host.ts]] — import-or-re-export: `Poller`; references `Poller`
- [[Reference/Desktop/TypeScript/screens/desks/pen/host|src/screens/desks/pen/host.ts]] — import-or-re-export: `Poller`; references `Poller`
- [[Reference/Desktop/TypeScript/screens/desks/pen/inkCache|src/screens/desks/pen/inkCache.ts]] — import-or-re-export: `Poller`; references `Poller`
- [[Reference/Desktop/TypeScript/screens/desks/search/SearchPanel|src/screens/desks/search/SearchPanel.tsx]] — import-or-re-export: `Poller`; references `Poller`
- [[Reference/Desktop/TypeScript/screens/desks/video/ChaptersPanel|src/screens/desks/video/ChaptersPanel.tsx]] — import-or-re-export: `Poller`; references `Poller`
- [[Reference/Desktop/TypeScript/screens/desks/video/VideoWindow|src/screens/desks/video/VideoWindow.tsx]] — import-or-re-export: `Poller`; references `Poller`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Adapter Architecture#Sidecar structure|sidecar structure]] — owns the four-layer RPC contract.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/video/video.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/desks/video/video.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/video/protection.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/desks/video/protection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/search/SearchPanel.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/desks/search/SearchPanel.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/pen/inkPad.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/desks/pen/inkPad.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/pen/inkCache.test.ts](../../../../../../apps/learnloop-tauri/src/screens/desks/pen/inkCache.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/pen/PenLayer.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/desks/pen/PenLayer.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/menu/ExerciseSheet.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/desks/menu/ExerciseSheet.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Add or change an RPC in all four layers: DTO, client facade, Rust command/registration, and Python sidecar handler/registry.
- Preserve camelCase wire names and typed error behavior; exercise `tests/test_desktop_rpc_contract.py` plus the feature's sidecar tests.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/api/poller.ts](../../../../../../apps/learnloop-tauri/src/api/poller.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

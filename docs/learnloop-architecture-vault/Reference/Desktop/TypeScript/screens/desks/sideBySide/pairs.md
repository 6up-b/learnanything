---
title: "Desktop module · src/screens/desks/sideBySide/pairs.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.sideBySide.pairs"
language: "TypeScript"
area: "TypeScript/screens/desks/sideBySide"
source_path: "apps/learnloop-tauri/src/screens/desks/sideBySide/pairs.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/sideBySide/pairs.ts"
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

# `src/screens/desks/sideBySide/pairs.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/sideBySide/_area|TypeScript/screens/desks/sideBySide]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `Pair`, `PairWindow`, `PairDeps`, `keptPairsFor` and related exports within the desktop's TypeScript/screens/desks/sideBySide ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/sideBySide/pairs.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/sideBySide/pairs.ts) |
| Source lines | 181 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/sideBySide/_area|TypeScript/screens/desks/sideBySide]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/sideBySide/pairs|src/screens/desks/sideBySide/pairs.ts]]

## Public API

- `export interface Pair` — interface, line 18
- `export interface PairWindow` — interface, line 30
- `export interface PairDeps` — interface, line 35
- `export function keptPairsFor(vaultKey: string): Map<string, Pair>` — function, line 50
- `export const PAIR_COPY =` — const, line 59
- `export class DeskPairs` — class, line 65

## Internal implementation anchors

- `const keptPairs = new Map<string, Map<string, Pair>>()` — const, line 48
- `let kept = keptPairs.get(vaultKey)` — let, line 51
- `const pair: Pair =` — const, line 86
- `const pair = this.live(windowId)` — const, line 92
- `const pair = this.live(windowId)` — const, line 103
- `const pair = this.live(windowId)` — const, line 113
- `const before = this.sections.get(windowId)` — const, line 124
- `const pair = this.live(windowId)` — const, line 127
- `const caused = pair.moved.get(windowId)` — const, line 129
- `const partner = this.partnerOf(windowId)` — const, line 134
- `const book = partner ? this.deps.windowOf(partner) : null` — const, line 135
- `const mine = ++pair.seq` — const, line 137
- `let view: CorrespondentsDto` — let, line 139
- `const hit = firstJudgedIn(view, book.sourceId)` — const, line 149
- `const target = targetOf(hit)` — const, line 154
- `const pair = this.byWindow.get(windowId)` — const, line 166
- `const pair = this.byWindow.get(windowId)` — const, line 177

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `DeskPairs`, `keptPairsFor`; references `DeskPairs`, `keptPairsFor`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CorrespondentsDto`
- [[Reference/Desktop/TypeScript/screens/reader/sideBySide|src/screens/reader/sideBySide.ts]] — import-or-re-export; imports `firstJudgedIn`, `targetOf`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

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

1. Modify [apps/learnloop-tauri/src/screens/desks/sideBySide/pairs.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/sideBySide/pairs.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

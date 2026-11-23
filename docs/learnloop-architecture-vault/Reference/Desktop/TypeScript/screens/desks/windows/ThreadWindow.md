---
title: "Desktop module · src/screens/desks/windows/ThreadWindow.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.windows.ThreadWindow"
language: "TypeScript"
area: "TypeScript/screens/desks/windows"
source_path: "apps/learnloop-tauri/src/screens/desks/windows/ThreadWindow.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/windows/ThreadWindow.tsx"
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

# `src/screens/desks/windows/ThreadWindow.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/windows/_area|TypeScript/screens/desks/windows]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `ThreadWindow` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/windows/ThreadWindow.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/windows/ThreadWindow.tsx) |
| Source lines | 77 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/windows/_area|TypeScript/screens/desks/windows]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/windows/ThreadWindow|src/screens/desks/windows/ThreadWindow.tsx]]

## Public API

- `export function threadExchanges(exchanges: ReaderAskHistoryExchangeDto[], rootExchangeId: string): ReaderAskHistoryExchangeDto[]` — function, line 11
- `export function ThreadWindow(` — function, line 26

## Internal implementation anchors

- `const byId = new Map(exchanges.map((exchange)` — const, line 12
- `const rootOf = (exchange: ReaderAskHistoryExchangeDto): string` — const, line 13
- `let current = exchange` — let, line 14
- `const named = byId.get(rootExchangeId)` — const, line 21
- `const root = named ? rootOf(named) : rootExchangeId` — const, line 22
- `const paused = useWindowPaused()` — const, line 31
- `let live = true` — let, line 37

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `ThreadWindow`; references `ThreadWindow`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderAskHistoryExchangeDto`, `TutorCitationDto`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useWindowPaused`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/companion/Companion.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/companion/Companion.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/windows/ThreadWindow.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/windows/ThreadWindow.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

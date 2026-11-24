---
title: "Desktop module · src/screens/desks/companion/companionFigures.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.companion.companionFigures"
language: "TypeScript"
area: "TypeScript/screens/desks/companion"
source_path: "apps/learnloop-tauri/src/screens/desks/companion/companionFigures.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/companion/companionFigures.tsx"
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

# `src/screens/desks/companion/companionFigures.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/companion/_area|TypeScript/screens/desks/companion]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `companionFigures` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/companion/companionFigures.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/companion/companionFigures.tsx) |
| Source lines | 176 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/companion/_area|TypeScript/screens/desks/companion]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/companion/companionFigures|src/screens/desks/companion/companionFigures.tsx]]

## Public API

- `export const COMPANION_FIGURE_COPY =` — const, line 14
- `export interface CompanionFigure` — interface, line 25
- `export function companionFigures(scope: string): CompanionFigure[]` — function, line 48
- `export function useCompanionFigures(scope: string): CompanionFigure[]` — function, line 53
- `export function showInCompanion(scope: string, entry: CompanionFigure): void` — function, line 58
- `export function removeCompanionFigure(scope: string, key: string): void` — function, line 63
- `export function resetCompanionFiguresForTests(): void` — function, line 69
- `export function figureForLine(entry: CompanionFigure): string` — function, line 75
- `export interface CompanionFigureHost` — interface, line 82
- `export function CompanionFigures(` — function, line 168

## Internal implementation anchors

- `const byScope = new Map<string, CompanionFigure[]>()` — const, line 35
- `const listeners = new Set<()` — const, line 36
- `const NONE: CompanionFigure[] = []` — const, line 37
- `function emit(): void` — function, line 39
- `function subscribe(listener: ()` — function, line 43
- `const passage = entry.figure.passages?.[0] ?? null` — const, line 76
- `const source = passage?.sourceTitle || entry.sourceTitle || "this passage"` — const, line 77
- `const page = passage?.page` — const, line 78
- `const CONTRACT: FiguresContract =` — const, line 89
- `function pretty(specJson: string | null | undefined): string | null` — function, line 91
- `function CompanionFigureItem(` — function, line 100
- `const ctl = useMemo<FiguresCtl>(()` — const, line 105
- `const patch = (found:` — const, line 106
- `const found = await api.readerFigurePredict(` — const, line 114
- `const found = await api.readerFigureExplain(` — const, line 120
- `const code = pretty(figure.specJson)` — const, line 130
- `const entries = useCompanionFigures(scope)` — const, line 169

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `CompanionFigureHost`, `CompanionFigures`, `showInCompanion`, `useCompanionFigures`; references `CompanionFigureHost`, `CompanionFigures`, `showInCompanion`, `useCompanionFigures`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `FigureViewDto`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export; imports `logReaderAction`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export; imports `FigureInline`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export; imports `FiguresContract`, `FiguresCtl`, `figurePlacementKey`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/companion/Companion.showMe.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/companion/Companion.showMe.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/DeskShell.menu.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/DeskShell.menu.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/companion/companionFigures.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/companion/companionFigures.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

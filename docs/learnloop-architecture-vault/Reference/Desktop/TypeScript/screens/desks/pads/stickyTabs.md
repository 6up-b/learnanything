---
title: "Desktop module · src/screens/desks/pads/stickyTabs.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.pads.stickyTabs"
language: "TypeScript"
area: "TypeScript/screens/desks/pads"
source_path: "apps/learnloop-tauri/src/screens/desks/pads/stickyTabs.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/pads/stickyTabs.ts"
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

# `src/screens/desks/pads/stickyTabs.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `TAB_SIZES`, `TabGrade`, `PadGeometry`, `stuckTop` and related exports within the desktop's TypeScript/screens/desks/pads ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/pads/stickyTabs.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/stickyTabs.ts) |
| Source lines | 77 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pads/stickyTabs|src/screens/desks/pads/stickyTabs.ts]]

## Public API

- `export const TAB_SIZES =` — const, line 6
- `export type TabGrade = "flat" | "order" | "distance"` — type, line 8
- `export interface PadGeometry` — interface, line 10
- `export function stuckTop(i: number, n: number, natural: number, viewport: number): number` — function, line 19
- `export function paperMinHeight(viewport: number, n: number): number` — function, line 26
- `export function activePad(pads: PadGeometry[], scrollTop: number, viewport: number, scrollHeight: number): number` — function, line 31
- `export function fractionalOpen(pads: PadGeometry[], scrollTop: number, viewport: number, scrollHeight: number): number` — function, line 42
- `export function mergeAmount(i: number, pads: PadGeometry[], scrollTop: number, viewport: number): number` — function, line 52
- `export function tabMargin(grade: TabGrade, i: number, open: number): number` — function, line 67
- `export function scrollTargetFor(i: number, pads: PadGeometry[]): number` — function, line 74

## Internal implementation anchors

- `const top = i * TAB_SIZES.tab` — const, line 20
- `const bottom = viewport - (n - i) * TAB_SIZES.tab` — const, line 21
- `const line = scrollTop + viewport / 3` — const, line 34
- `const i = activePad(pads, scrollTop, viewport, scrollHeight)` — const, line 43
- `const pad = pads[i]` — const, line 45
- `const span = Math.max(1, pad.paperBottom - pad.tabTop)` — const, line 46
- `const into = Math.max(0, Math.min(1, (scrollTop + viewport / 3 - pad.tabTop) / span))` — const, line 47
- `const pad = pads[i]` — const, line 53
- `const tabY = stuckTop(i, pads.length, pad.tabTop - scrollTop, viewport)` — const, line 55
- `const from = tabY + TAB_SIZES.tab` — const, line 56
- `const to = from + TAB_SIZES.mergeOver` — const, line 57
- `const visibleTop = Math.max(pad.paperTop - scrollTop, (i + 1) * TAB_SIZES.tab)` — const, line 59
- `const visibleBottom = Math.min(pad.paperBottom - scrollTop, viewport - (pads.length - 1 - i) * TAB_SIZES.tab)` — const, line 60
- `const overlap = Math.max(0, Math.min(to, visibleBottom) - Math.max(from, visibleTop))` — const, line 61
- `const pad = pads[i]` — const, line 75

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] — import-or-re-export: `PadGeometry`, `TabGrade`, `activePad`, `fractionalOpen`, `mergeAmount`, `paperMinHeight`, `scrollTargetFor`, `tabMargin`; references `PadGeometry`, `TabGrade`, `activePad`, `fractionalOpen`, `mergeAmount`, `paperMinHeight`, `scrollTargetFor`, `tabMargin`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/pads/stickyTabs.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/stickyTabs.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/pads/stickyTabs.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/stickyTabs.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

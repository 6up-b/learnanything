---
title: "Desktop module · src/screens/desks/overview/links.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.overview.links"
language: "TypeScript"
area: "TypeScript/screens/desks/overview"
source_path: "apps/learnloop-tauri/src/screens/desks/overview/links.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/overview/links.ts"
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

# `src/screens/desks/overview/links.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/overview/_area|TypeScript/screens/desks/overview]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `Relation`, `DRAWN_RELATIONS`, `openedBeside`, `relationsOf` and related exports within the desktop's TypeScript/screens/desks/overview ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/overview/links.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/overview/links.ts) |
| Source lines | 132 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/overview/_area|TypeScript/screens/desks/overview]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/overview/links|src/screens/desks/overview/links.ts]]

## Public API

- `export interface Relation` — interface, line 11
- `export const DRAWN_RELATIONS = 4` — const, line 18
- `export function openedBeside(view: Record<string, unknown> | undefined): string | null` — function, line 34
- `export function relationsOf(ws: Workspace, windowId: string): Relation[]` — function, line 40
- `export interface CurvedLink` — interface, line 66
- `export function curvedLinks(from: Rect, targets: Array<` — function, line 86
- `export function gatherOrder(slots: string[][], focusId: string, related: Relation[], limit = DRAWN_RELATIONS):` — function, line 118

## Internal implementation anchors

- `function sourceOf(content: ContentRefDto | null): string | null` — function, line 20
- `function extractionOf(content: ContentRefDto | null): string | null` — function, line 26
- `const value = view?.openedBeside` — const, line 35
- `const self = ws.windows[windowId]` — const, line 41
- `const out = new Map<string, Relation>()` — const, line 43
- `const add = (id: string, weight: Relation["weight"], label: string)` — const, line 44
- `const known = out.get(id)` — const, line 46
- `const mySource = sourceOf(self.content)` — const, line 49
- `const myExtraction = extractionOf(self.content)` — const, line 50
- `const beside = openedBeside(self.view)` — const, line 51
- `const theirExtraction = extractionOf(other.content)` — const, line 56
- `const panelPair = (self.content?.kind === "panel") !== (other.content?.kind === "panel")` — const, line 57
- `const LINK_SPREAD = 26` — const, line 77
- `function cubicAt(p0: number, p1: number, p2: number, p3: number, u: number): number` — function, line 79
- `const v = 1 - u` — const, line 80
- `const offset = (index - (targets.length - 1) / 2) * LINK_SPREAD` — const, line 88
- `const x0 = from.x + from.w / 2 + offset` — const, line 89
- `const y0 = from.y + from.h` — const, line 90
- `const x3 = rect.x + rect.w / 2 + offset` — const, line 91
- `const y3 = rect.y + rect.h` — const, line 92
- `let c1: [number, number]` — let, line 93
- `let c2: [number, number]` — let, line 94
- `const dip = 120 + Math.abs(x3 - x0) * 0.12 + Math.abs(offset)` — const, line 96
- `const mid = (y0 + y3) / 2` — const, line 100
- `const u = 0.82` — const, line 104
- `const focusIndex = slots.findIndex((slot)` — const, line 119
- `const slotOf = (id: string)` — const, line 121
- `const linkedSlots: number[] = []` — const, line 122
- `const index = slotOf(relation.windowId)` — const, line 124
- `const moving = linkedSlots.slice(0, limit)` — const, line 127
- `const before = slots.map((_, index)` — const, line 128
- `const rest = slots.map((_, index)` — const, line 129
- `const order = [...before, focusIndex, ...moving, ...rest].map((index)` — const, line 130

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `DRAWN_RELATIONS`, `Relation`, `curvedLinks`, `gatherOrder`, `relationsOf`; references `DRAWN_RELATIONS`, `Relation`, `curvedLinks`, `gatherOrder`, `relationsOf`
- [[Reference/Desktop/TypeScript/screens/desks/overview/Card|src/screens/desks/overview/Card.tsx]] — import-or-re-export: `CurvedLink`; references `CurvedLink`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ContentRefDto`
- [[Reference/Desktop/TypeScript/screens/desks/geometry|src/screens/desks/geometry.ts]] — import-or-re-export; imports `Rect`
- [[Reference/Desktop/TypeScript/screens/desks/model/workspace|src/screens/desks/model/workspace.ts]] — import-or-re-export; imports `Workspace`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/overview/links.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/overview/links.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/overview/links.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/overview/links.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

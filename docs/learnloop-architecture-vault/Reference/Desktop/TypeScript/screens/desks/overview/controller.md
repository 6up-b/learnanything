---
title: "Desktop module · src/screens/desks/overview/controller.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.overview.controller"
language: "TypeScript"
area: "TypeScript/screens/desks/overview"
source_path: "apps/learnloop-tauri/src/screens/desks/overview/controller.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/overview/controller.ts"
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

# `src/screens/desks/overview/controller.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/overview/_area|TypeScript/screens/desks/overview]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `SlotElements`, `ZoomPlan`, `ZoomTargets`, `FrameClock` and related exports within the desktop's TypeScript/screens/desks/overview ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/overview/controller.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/overview/controller.ts) |
| Source lines | 242 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/overview/_area|TypeScript/screens/desks/overview]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/overview/controller|src/screens/desks/overview/controller.ts]]

## Public API

- `export interface SlotElements` — interface, line 8
- `export interface ZoomPlan` — interface, line 15
- `export interface ZoomTargets` — interface, line 25
- `export interface FrameClock` — interface, line 34
- `export const ANIMATION_FRAMES: FrameClock =` — const, line 39
- `export function focusEdge(q: number): string` — function, line 46
- `export function cameraTransform(camera: Camera): string` — function, line 51
- `export class ZoomController` — class, line 55

## Internal implementation anchors

- `const edge = Math.max(0, 1 - 3 * q)` — const, line 47
- `const slot = targets.slots.get(item.key)` — const, line 95
- `const targets = this.targets` — const, line 144
- `const plan = this.plan` — const, line 183
- `const dt = this.last ? (now - this.last) / 1000 : 1 / 60` — const, line 185
- `const plan = this.plan` — const, line 203
- `const plan = this.plan` — const, line 213
- `const targets = this.targets` — const, line 214
- `const slot = targets.slots.get(item.key)` — const, line 219
- `const values = frame.items[index]` — const, line 220
- `const element = targets.rings?.get(ring.key)` — const, line 232
- `const q = frame.q` — const, line 234
- `const r =` — const, line 235

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `ANIMATION_FRAMES`, `FrameClock`, `SlotElements`, `ZoomController`, `ZoomPlan`, `cameraTransform`; references `ANIMATION_FRAMES`, `FrameClock`, `SlotElements`, `ZoomController`, `ZoomPlan`, `cameraTransform`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/desks/geometry|src/screens/desks/geometry.ts]] — import-or-re-export; imports `Rect`
- [[Reference/Desktop/TypeScript/screens/desks/overview/engine|src/screens/desks/overview/engine.ts]] — import-or-re-export; imports `Camera`, `Frame`, `Motion`, `ZoomItem`, `frameAt`, `release`, `settleNow`, `step`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/overview/controller.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/overview/controller.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/overview/controller.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/overview/controller.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

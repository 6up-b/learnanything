---
title: "Desktop module · src/screens/desks/geometry.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.geometry"
language: "TypeScript"
area: "TypeScript/screens/desks"
source_path: "apps/learnloop-tauri/src/screens/desks/geometry.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/geometry.ts"
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

# `src/screens/desks/geometry.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/_area|TypeScript/screens/desks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `DESK_SIZES`, `Rect`, `Stage`, `slotWidth` and related exports within the desktop's TypeScript/screens/desks ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/geometry.ts](../../../../../../../apps/learnloop-tauri/src/screens/desks/geometry.ts) |
| Source lines | 189 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/_area|TypeScript/screens/desks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/geometry|src/screens/desks/geometry.ts]]

## Public API

- `export const DESK_SIZES =` — const, line 6
- `export interface Rect` — interface, line 26
- `export interface Stage` — interface, line 33
- `export function slotWidth(stage: Stage): number` — function, line 42
- `export function slotRects(slotCount: number, stage: Stage): Rect[]` — function, line 47
- `export function paneRects(slot: Rect, panes: number): Rect[]` — function, line 59
- `export function stripWidth(slotCount: number, stage: Stage): number` — function, line 69
- `export function rowTop(rowIndex: number, stage: Stage): number` — function, line 77
- `export function ensureVisible(camX: number, index: number, slotCount: number, stage: Stage, withPrevious = false): number` — function, line 87
- `export interface SlotVisibility` — interface, line 104
- `export function slotVisibility(camX: number, slotCount: number, stage: Stage): SlotVisibility[]` — function, line 115
- `export function slotsInView(camX: number, slotCount: number, stage: Stage): number[]` — function, line 131
- `export function sliverSlots(camX: number, slotCount: number, stage: Stage):` — function, line 136
- `export function softCropMask(visibility: SlotVisibility, width: number): string | null` — function, line 146
- `export const FOCUS_MEASURE: Record<string, number> =` — const, line 161
- `export const DOC_ZOOM =` — const, line 169
- `export function focusRect(viewport: Stage): Rect` — function, line 172
- `export function stepZoom(zoom: number, direction: -1 | 0 | 1): number` — function, line 176
- `export function stageFor(viewport: Stage): Stage` — function, line 183

## Internal implementation anchors

- `const w = slotWidth(stage)` — const, line 48
- `const h = Math.max(0, stage.height - 2 * DESK_SIZES.inset)` — const, line 49
- `const half = (slot.h - DESK_SIZES.pairDivider) / 2` — const, line 61
- `const rects = slotRects(slotCount, stage)` — const, line 71
- `const last = rects[rects.length - 1]` — const, line 72
- `function clampCam(camX: number, slotCount: number, stage: Stage): number` — function, line 81
- `const rects = slotRects(slotCount, stage)` — const, line 89
- `const rect = rects[index]` — const, line 90
- `const right = stage.width - DESK_SIZES.side` — const, line 91
- `let next = camX` — let, line 92
- `const left = rect.x - camX` — const, line 117
- `const right = left + rect.w` — const, line 118
- `const shown = slotsInView(camX, slotCount, stage)` — const, line 137
- `const first = shown[0]` — const, line 139
- `const last = shown[shown.length - 1]` — const, line 140
- `const fade = DESK_SIZES.cropFade` — const, line 148
- `const dim = `rgba(0,0,0,$` — const, line 149
- `const leftEdge = Math.min(width, visibility.cutLeft)` — const, line 150
- `const rightEdge = Math.max(0, width - visibility.cutRight)` — const, line 151
- `const stops: string[] = []` — const, line 152
- `const next = Math.round((zoom + direction * DOC_ZOOM.step) * 10) / 10` — const, line 178
- `const shelf = viewport.width < DESK_SIZES.shelfFoldBelow ? DESK_SIZES.shelfRail : DESK_SIZES.shelf` — const, line 184

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `DESK_SIZES`, `FOCUS_MEASURE`, `Rect`, `Stage`, `ensureVisible`, `paneRects`, `rowTop`, `sliverSlots`, `slotRects`, `slotVisibility`, `slotWidth`, `softCropMask`, `stepZoom`; references `DESK_SIZES`, `FOCUS_MEASURE`, `Rect`, `Stage`, `ensureVisible`, `paneRects`, `rowTop`, `sliverSlots`, `slotRects`, `slotVisibility`, `slotWidth`, `softCropMask`, `stepZoom`
- [[Reference/Desktop/TypeScript/screens/desks/companion/Companion|src/screens/desks/companion/Companion.tsx]] — import-or-re-export: `Rect`, `Stage`; references `Rect`, `Stage`
- [[Reference/Desktop/TypeScript/screens/desks/companion/model|src/screens/desks/companion/model.ts]] — import-or-re-export: `Rect`, `Stage`; references `Rect`, `Stage`
- [[Reference/Desktop/TypeScript/screens/desks/overview/Card|src/screens/desks/overview/Card.tsx]] — import-or-re-export: `Rect`; references `Rect`
- [[Reference/Desktop/TypeScript/screens/desks/overview/controller|src/screens/desks/overview/controller.ts]] — import-or-re-export: `Rect`; references `Rect`
- [[Reference/Desktop/TypeScript/screens/desks/overview/engine|src/screens/desks/overview/engine.ts]] — import-or-re-export: `DESK_SIZES`, `Rect`, `Stage`; references `DESK_SIZES`, `Rect`, `Stage`
- [[Reference/Desktop/TypeScript/screens/desks/overview/links|src/screens/desks/overview/links.ts]] — import-or-re-export: `Rect`; references `Rect`
- [[Reference/Desktop/TypeScript/screens/desks/selection|src/screens/desks/selection.ts]] — import-or-re-export: `Rect`; references `Rect`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/overview/engine.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/desks/overview/engine.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/geometry.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/desks/geometry.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/geometry.ts](../../../../../../../apps/learnloop-tauri/src/screens/desks/geometry.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

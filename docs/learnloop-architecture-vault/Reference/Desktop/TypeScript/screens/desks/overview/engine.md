---
title: "Desktop module · src/screens/desks/overview/engine.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.overview.engine"
language: "TypeScript"
area: "TypeScript/screens/desks/overview"
source_path: "apps/learnloop-tauri/src/screens/desks/overview/engine.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/overview/engine.ts"
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

# `src/screens/desks/overview/engine.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/overview/_area|TypeScript/screens/desks/overview]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `OVERVIEW`, `Camera`, `IDENTITY`, `OverviewLayout` and related exports within the desktop's TypeScript/screens/desks/overview ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/overview/engine.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/overview/engine.ts) |
| Source lines | 419 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/overview/_area|TypeScript/screens/desks/overview]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/overview/engine|src/screens/desks/overview/engine.ts]]

## Public API

- `export const OVERVIEW =` — const, line 14
- `export interface Camera` — interface, line 55
- `export const IDENTITY: Camera =` — const, line 61
- `export interface OverviewLayout` — interface, line 65
- `export function overviewLayout(slotCounts: number[], slotWidth: number, stage: Stage): OverviewLayout` — function, line 76
- `export function onStage(rect: Rect, camera: Camera): Rect` — function, line 91
- `export function followSelection(from: Camera, selected: Rect, stage: Stage): Camera` — function, line 97
- `export function enteringCamera(selected: Rect | null, stage: Stage): Camera` — function, line 110
- `export interface ZoomItem` — interface, line 117
- `export interface ItemFrame` — interface, line 129
- `export interface Frame` — interface, line 145
- `export function frameAt(p: number, A: Camera, B: Camera, items: ZoomItem[]): Frame` — function, line 167
- `export function transformed(base: Rect, item: Pick<ItemFrame, "tx" | "ty" | "sx" | "sy">): Rect` — function, line 206
- `export interface Motion` — interface, line 212
- `export function step(motion: Motion, dt: number):` — function, line 225
- `export function release(base: 0 | 1, target: number, v: number): 0 | 1` — function, line 249
- `export function settleNow(base: 0 | 1, motion: Motion): 0 | 1` — function, line 256
- `export interface WheelLike` — interface, line 263
- `export function normalizedDelta(event: Pick<WheelLike, "deltaX" | "deltaY" | "deltaMode">, stageHeight: number):` — function, line 273
- `export type WheelKind = "pan" | "zoom" | "scroll"` — type, line 278
- `export type ZoomSource = "touch" | "pinch" | "notch"` — type, line 279
- `export function classifyWheel(event: WheelLike, mods:` — function, line 284
- `export interface ZoomGesture` — interface, line 307
- `export type ZoomStep = |` — type, line 317
- `export function newZoomGesture(source: ZoomSource, now: number): ZoomGesture` — function, line 323
- `export function zoomWheel( gesture: ZoomGesture, dy: number, now: number, state:` — function, line 329
- `export function dragProgress(base: 0 | 1, dy: number): number` — function, line 367
- `export interface Selection` — interface, line 373
- `export function moveSelection(layout: OverviewLayout, from: Selection, direction: "left" | "right" | "up" | "down"): Selection` — function, line 379
- `export function dropTarget(layout: OverviewLayout, point:` — function, line 406

## Internal implementation anchors

- `const rowHeight = stage.height * OVERVIEW.rowShare` — const, line 77
- `const pitch = rowHeight + OVERVIEW.rowGap` — const, line 78
- `const x0 = DESK_SIZES.side + OVERVIEW.gutter` — const, line 79
- `const w = Math.max(slotWidth, OVERVIEW.cardMin)` — const, line 80
- `const cards = slotCounts.map((count, row)` — const, line 81
- `const r = onStage(selected, from)` — const, line 98
- `const away = (delta: number)` — const, line 100
- `const start: Camera =` — const, line 111
- `const clamp01 = (x: number)` — const, line 158
- `const lerp = (a: number, b: number, t: number)` — const, line 159
- `function ramp(q: number, [from, to]: readonly [number, number]): number` — function, line 161
- `const s = A.s * Math.pow(B.s / A.s, p)` — const, line 168
- `const q = A.s === B.s ? p : (A.s - s) / (A.s - B.s)` — const, line 169
- `const camera =` — const, line 170
- `const fade = ramp(q, OVERVIEW.contentFade)` — const, line 171
- `const late = ramp(q, OVERVIEW.lateFade)` — const, line 172
- `const rect =` — const, line 181
- `const sx = rect.w / item.base.w` — const, line 187
- `const sy = rect.h / item.base.h` — const, line 188
- `const t = Math.min(0.05, Math.max(0.001, dt))` — const, line 226
- `let p = motion.p + (motion.target - motion.p) * (1 - Math.exp(-t / OVERVIEW.tau))` — let, line 228
- `const w = OVERVIEW.omega` — const, line 232
- `const x0 = motion.p - motion.goal` — const, line 233
- `const c = motion.v + w * x0` — const, line 234
- `const k = Math.exp(-w * t)` — const, line 235
- `const x = (x0 + c * t) * k` — const, line 236
- `let v = (c - w * (x0 + c * t)) * k` — let, line 237
- `let p = motion.goal + x` — let, line 238
- `const projected = target + v * OVERVIEW.project` — const, line 250
- `const unit = event.deltaMode === 1 ? 40 : event.deltaMode === 2 ? stageHeight : 1` — const, line 274
- `const alt = mods.alt || event.altKey` — const, line 286
- `const ctrlEvent = event.ctrlKey || mods.ctrl` — const, line 287
- `const pinch = event.ctrlKey && !mods.ctrl` — const, line 290
- `function zoomSource(event: WheelLike, dy: number): ZoomSource` — function, line 301
- `const sign = Math.sign(dy)` — const, line 335
- `const g =` — const, line 336
- `const dp = dy / (g.source === "pinch" ? OVERVIEW.pinchTravel : OVERVIEW.touchTravel)` — const, line 353
- `const dt = Math.max(0.004, (now - g.t) / 1000)` — const, line 354
- `const base = state.active ? state.target : state.inOverview ? 1 : 0` — const, line 357
- `const target = clamp01(base + dp)` — const, line 358
- `const rows = layout.cards` — const, line 380
- `const current = rows[from.row]?.[from.slot]` — const, line 381
- `const slot = from.slot + (direction === "left" ? -1 : 1)` — const, line 384
- `const step = direction === "up" ? -1 : 1` — const, line 387
- `const centre = current.x + current.w / 2` — const, line 390
- `let best = 0` — let, line 391
- `let distance = Infinity` — let, line 392
- `const d = Math.abs(card.x + card.w / 2 - centre)` — const, line 394
- `const pitch = layout.rowHeight + OVERVIEW.rowGap` — const, line 407
- `const row = Math.floor((point.y + OVERVIEW.rowGap / 2) / pitch)` — const, line 408
- `const cards = layout.cards[row]` — const, line 410
- `let slot = cards.length` — let, line 411

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `Camera`, `IDENTITY`, `OVERVIEW`, `ZoomGesture`, `ZoomSource`, `classifyWheel`, `dragProgress`, `dropTarget`, `enteringCamera`, `followSelection`, `moveSelection`, `newZoomGesture`, `normalizedDelta`, `overviewLayout`, `zoomWheel`; references `Camera`, `IDENTITY`, `OVERVIEW`, `ZoomGesture`, `ZoomSource`, `classifyWheel`, `dragProgress`, `dropTarget`, `enteringCamera`, `followSelection`, `moveSelection`, `newZoomGesture`, `normalizedDelta`, `overviewLayout`, `zoomWheel`
- [[Reference/Desktop/TypeScript/screens/desks/overview/controller|src/screens/desks/overview/controller.ts]] — import-or-re-export: `Camera`, `Frame`, `Motion`, `ZoomItem`, `frameAt`, `release`, `settleNow`, `step`; references `Camera`, `Frame`, `Motion`, `ZoomItem`, `frameAt`, `release`, `settleNow`, `step`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/desks/geometry|src/screens/desks/geometry.ts]] — import-or-re-export; imports `DESK_SIZES`, `Rect`, `Stage`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/overview/engine.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/overview/engine.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/overview/controller.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/overview/controller.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_common_repair_delivery.py](../../../../../../../../tests/test_common_repair_delivery.py) — cross-boundary name contract: references uniquely owned exported name `Selection`; it does **not** directly execute this source module.
- [tests/test_decision_records_retention.py](../../../../../../../../tests/test_decision_records_retention.py) — cross-boundary name contract: references uniquely owned exported name `IDENTITY`; it does **not** directly execute this source module.
- [tests/test_e0_delivery.py](../../../../../../../../tests/test_e0_delivery.py) — cross-boundary name contract: references uniquely owned exported name `Selection`; it does **not** directly execute this source module.
- [tests/test_e0_review_round1.py](../../../../../../../../tests/test_e0_review_round1.py) — cross-boundary name contract: references uniquely owned exported name `Selection`; it does **not** directly execute this source module.
- [tests/test_e0_review_round2.py](../../../../../../../../tests/test_e0_review_round2.py) — cross-boundary name contract: references uniquely owned exported name `Selection`; it does **not** directly execute this source module.
- [tests/test_e0_review_round4.py](../../../../../../../../tests/test_e0_review_round4.py) — cross-boundary name contract: references uniquely owned exported name `Selection`; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/overview/engine.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/overview/engine.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

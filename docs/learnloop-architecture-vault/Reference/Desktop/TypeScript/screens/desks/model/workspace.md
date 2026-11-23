---
title: "Desktop module · src/screens/desks/model/workspace.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.model.workspace"
language: "TypeScript"
area: "TypeScript/screens/desks/model"
source_path: "apps/learnloop-tauri/src/screens/desks/model/workspace.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/model/workspace.ts"
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

# `src/screens/desks/model/workspace.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/model/_area|TypeScript/screens/desks/model]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `PAIR_SIZE`, `DeskWindow`, `Desk`, `ClosedWindow` and related exports within the desktop's TypeScript/screens/desks/model ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/model/workspace.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/model/workspace.ts) |
| Source lines | 658 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/model/_area|TypeScript/screens/desks/model]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/model/workspace|src/screens/desks/model/workspace.ts]]

## Public API

- `export const PAIR_SIZE = 2` — const, line 18
- `export interface DeskWindow` — interface, line 20
- `export interface Desk` — interface, line 31
- `export interface ClosedWindow` — interface, line 43
- `export interface Workspace` — interface, line 48
- `export const EMPTY_WORKSPACE: Workspace =` — const, line 56
- `export function fromDeskState(state: DeskStateDto): Workspace` — function, line 62
- `export function deskById(ws: Workspace, deskId: string | null | undefined): Desk | null` — function, line 95
- `export function slotIndexOf(desk: Desk, windowId: string | null | undefined): number` — function, line 99
- `export function focusedWindowId(ws: Workspace, desk: Desk | null): string | null` — function, line 105
- `export function focusedSlot(ws: Workspace, desk: Desk | null): number` — function, line 113
- `export function contentKey(content: ContentRefDto | null, stack?: PadStackEntryDto[] | null): string` — function, line 119
- `export function rangeCovers( content: ContentRefDto | null, spanId: string | null | undefined, order?: (spanId: string)` — function, line 143
- `export function findDuplicate( ws: Workspace, desk: Desk, content: ContentRefDto, spanId?: string | null, order?: (spanId: string)` — function, line 159
- `export class OpRefusal extends Error` — class, line 178
- `export function applyDeskOp(ws: Workspace, op: DeskOpDto): Workspace` — function, line 225
- `export interface Step` — interface, line 388
- `export const PAIR_COPY =` — const, line 395
- `export function restampOp(ws: Workspace, op: DeskOpDto):` — function, line 414
- `export function setFocus(ws: Workspace, deskId: string, windowId: string): Step` — function, line 423
- `export function openBeside( ws: Workspace, deskId: string, content: ContentRefDto, mintId: ()` — function, line 436
- `export function openStackBeside(ws: Workspace, deskId: string, padIds: string[], mintId: ()` — function, line 463
- `export function closeWindow(ws: Workspace, deskId: string, windowId: string): Step` — function, line 481
- `export function undoClose(ws: Workspace, deskId: string): Step` — function, line 497
- `export function moveFocused(ws: Workspace, deskId: string, direction: -1 | 1): Step` — function, line 508
- `export function moveWindowTo(ws: Workspace, deskId: string, windowId: string, toSlot: number): Step` — function, line 518
- `export function pairFocused(ws: Workspace, deskId: string): Step` — function, line 526
- `export function unpairFocused(ws: Workspace, deskId: string): Step` — function, line 538
- `export function focusAlong(ws: Workspace, deskId: string, direction: -1 | 1): Step` — function, line 549
- `export function focusPane(ws: Workspace, deskId: string, direction: -1 | 1): Step | null` — function, line 560
- `export function positionAfter(ws: Workspace): string` — function, line 573
- `export function createDesk(ws: Workspace, deskId: string, title: string): Step` — function, line 578
- `export function renameDesk(ws: Workspace, deskId: string, title: string): Step` — function, line 582
- `export function setCompanionDock(ws: Workspace, deskId: string, dock: Desk["companion"]["dock"]): Step` — function, line 587
- `export function setCompanionShown(ws: Workspace, deskId: string, shown: boolean): Step` — function, line 594
- `export function setView(ws: Workspace, deskId: string, windowId: string, view: Record<string, unknown>): Step` — function, line 600
- `export function swapInView(ws: Workspace, deskId: string, otherSlot: number): Step` — function, line 607
- `export function reorderSlots(ws: Workspace, deskId: string, order: string[][]): Step` — function, line 617
- `export function moveToDeskAt(ws: Workspace, deskId: string, windowId: string, toDeskId: string, toIndex: number): Step` — function, line 631
- `export function moveToDesk(ws: Workspace, deskId: string, windowId: string, toDeskId: string, afterWindowId: string | null): Step` — function, line 645

## Internal implementation anchors

- `function orderDesks(desks: Desk[]): Desk[]` — function, line 58
- `const windows: Record<string, DeskWindow> =` — const, line 63
- `const desks: Desk[] = state.desks.map((desk)` — const, line 64
- `const slots = [...desk.slots].sort((a, b)` — const, line 65
- `const first = desk.slots[0]` — const, line 108
- `const at = order(spanId)` — const, line 152
- `const from = order(fromSpanId)` — const, line 153
- `const to = order(toSpanId)` — const, line 154
- `const key = contentKey(content)` — const, line 166
- `const window = ws.windows[id]` — const, line 169
- `function replaceDesk(ws: Workspace, next: Desk): Workspace` — function, line 184
- `function normalizeActive(ws: Workspace, desk: Desk, activeIds: Set<string>): Record<string, DeskWindow>` — function, line 190
- `const windows =` — const, line 191
- `const window = windows[id]` — const, line 196
- `function activeSet(ws: Workspace, desk: Desk): Set<string>` — function, line 203
- `function requireDesk(ws: Workspace, deskId: string): Desk` — function, line 207
- `const desk = deskById(ws, deskId)` — const, line 208
- `function requireOpen(desk: Desk, windowId: string): number` — function, line 213
- `const index = slotIndexOf(desk, windowId)` — const, line 214
- `function bump(desk: Desk, fields: Partial<Desk> =` — function, line 219
- `const desk: Desk =` — const, line 229
- `const desk = requireDesk(ws, op.deskId)` — const, line 250
- `const desk = requireDesk(ws, op.deskId)` — const, line 254
- `const desk = requireDesk(ws, op.deskId)` — const, line 260
- `const desk = requireDesk(ws, op.deskId)` — const, line 265
- `const at = op.afterWindowId ? requireOpen(desk, op.afterWindowId) + 1 : desk.slots.length` — const, line 267
- `const slots = desk.slots.map((slot)` — const, line 268
- `const window: DeskWindow =` — const, line 270
- `const next = bump(desk,` — const, line 279
- `const withWindow =` — const, line 280
- `const desk = requireDesk(ws, op.deskId)` — const, line 284
- `const index = requireOpen(desk, op.windowId)` — const, line 285
- `const slots = desk.slots.map((slot)` — const, line 286
- `const active = activeSet(ws, desk)` — const, line 287
- `const next = bump(desk,` — const, line 289
- `const closedWindow = ws.windows[op.windowId]` — const, line 290
- `const windows = normalizeActive(ws, next, active)` — const, line 291
- `const closed =` — const, line 293
- `const desk = requireDesk(ws, op.deskId)` — const, line 297
- `const list = ws.closed[desk.deskId] ?? []` — const, line 298
- `const entry = list.find((closed)` — const, line 301
- `const at = Math.min(op.slot ?? desk.slots.length, desk.slots.length)` — const, line 303
- `const slots = desk.slots.map((slot)` — const, line 304
- `const next = bump(desk,` — const, line 306
- `const withWindow =` — const, line 307
- `const desk = requireDesk(ws, op.deskId)` — const, line 315
- `const index = requireOpen(desk, op.windowId)` — const, line 316
- `const slots = desk.slots.map((slot)` — const, line 317
- `const from = requireDesk(ws, op.deskId)` — const, line 323
- `const to = requireDesk(ws, op.toDeskId)` — const, line 325
- `const fromActive = activeSet(ws, from)` — const, line 327
- `const fromNext = bump(from,` — const, line 328
- `const at = op.afterWindowId ? requireOpen(to, op.afterWindowId) + 1 : to.slots.length` — const, line 332
- `const toSlots = to.slots.map((slot)` — const, line 333
- `const toNext = bump(to,` — const, line 335
- `let next = replaceDesk(replaceDesk(ws, fromNext), toNext)` — let, line 336
- `const toActive = activeSet(next, toNext)` — const, line 338
- `const desk = requireDesk(ws, op.deskId)` — const, line 343
- `const index = requireOpen(desk, op.windowId)` — const, line 344
- `const slots = desk.slots.map((slot)` — const, line 348
- `const active = activeSet(ws, desk)` — const, line 351
- `const next = bump(desk,` — const, line 354
- `const desk = requireDesk(ws, op.deskId)` — const, line 358
- `const index = requireOpen(desk, op.windowId)` — const, line 359
- `const slots = desk.slots.map((slot)` — const, line 361
- `const next = bump(desk,` — const, line 364
- `const desk = requireDesk(ws, op.deskId)` — const, line 368
- `const index = requireOpen(desk, op.windowId)` — const, line 369
- `const active = activeSet(ws, desk)` — const, line 371
- `const next = bump(desk)` — const, line 374
- `const desk = requireDesk(ws, op.deskId)` — const, line 378
- `const window = ws.windows[op.windowId]` — const, line 380
- `function push(step: Step, op: DeskOpDto): Step` — function, line 401
- `const versioned: DeskOpDto =` — const, line 402
- `const step = push(` — const, line 415
- `function start(ws: Workspace): Step` — function, line 419
- `const desk = requireDesk(ws, deskId)` — const, line 424
- `let step = start(ws)` — let, line 425
- `const index = slotIndexOf(desk, windowId)` — const, line 426
- `const desk = requireDesk(ws, deskId)` — const, line 443
- `const duplicate = findDuplicate(ws, desk, content, options.spanId ?? null, options.order)` — const, line 444
- `const windowId = mintId()` — const, line 446
- `const focus = focusedWindowId(ws, desk)` — const, line 447
- `let step = push(start(ws),` — let, line 448
- `const desk = requireDesk(ws, deskId)` — const, line 464
- `const windowId = mintId()` — const, line 465
- `const focus = focusedWindowId(ws, desk)` — const, line 466
- `let step = push(start(ws),` — let, line 467
- `function lastOfSlot(desk: Desk, windowId: string): string` — function, line 475
- `const slot = desk.slots[slotIndexOf(desk, windowId)]` — const, line 476
- `const desk = requireDesk(ws, deskId)` — const, line 482
- `const index = slotIndexOf(desk, windowId)` — const, line 483
- `const wasFocus = focusedWindowId(ws, desk) === windowId` — const, line 485
- `let step = push(start(ws),` — let, line 486
- `const after = requireDesk(step.ws, deskId)` — const, line 488
- `const at = Math.min(index, after.slots.length - 1)` — const, line 489
- `const next = at >= 0 ? (after.slots[at].find((id)` — const, line 490
- `const list = ws.closed[deskId] ?? []` — const, line 498
- `const entry = list[list.length - 1]` — const, line 499
- `let step = push(start(ws),` — let, line 502
- `const desk = requireDesk(ws, deskId)` — const, line 509
- `const id = focusedWindowId(ws, desk)` — const, line 510
- `const index = slotIndexOf(desk, id)` — const, line 511
- `const to = index + direction` — const, line 512
- `const desk = requireDesk(ws, deskId)` — const, line 519
- `const index = slotIndexOf(desk, windowId)` — const, line 520
- `const desk = requireDesk(ws, deskId)` — const, line 527
- `const id = focusedWindowId(ws, desk)` — const, line 528
- `const index = slotIndexOf(desk, id)` — const, line 529
- `const desk = requireDesk(ws, deskId)` — const, line 539
- `const id = focusedWindowId(ws, desk)` — const, line 540
- `const index = slotIndexOf(desk, id)` — const, line 541
- `let step = push(start(ws),` — let, line 543
- `const desk = requireDesk(ws, deskId)` — const, line 550
- `const index = focusedSlot(ws, desk)` — const, line 551
- `const to = index + direction` — const, line 552
- `const target = desk.slots[to].find((id)` — const, line 554
- `const desk = requireDesk(ws, deskId)` — const, line 561
- `const id = focusedWindowId(ws, desk)` — const, line 562
- `const index = slotIndexOf(desk, id)` — const, line 563
- `const slot = desk.slots[index]` — const, line 565
- `const pane = slot.indexOf(id)` — const, line 566
- `const to = pane + direction` — const, line 567
- `const last = ws.desks[ws.desks.length - 1]?.position ?? ""` — const, line 574
- `const desk = requireDesk(ws, deskId)` — const, line 588
- `const desk = requireDesk(ws, deskId)` — const, line 595
- `const desk = requireDesk(ws, deskId)` — const, line 601
- `const desk = requireDesk(ws, deskId)` — const, line 608
- `const id = focusedWindowId(ws, desk)` — const, line 609
- `const index = slotIndexOf(desk, id)` — const, line 610
- `let step = start(ws)` — let, line 618
- `const desk = requireDesk(step.ws, deskId)` — const, line 620
- `const at = slotIndexOf(desk, slot[0])` — const, line 621
- `const to = requireDesk(ws, toDeskId)` — const, line 632
- `const at = Math.max(0, Math.min(toIndex, to.slots.length))` — const, line 633
- `const afterSlot = to.slots[at - 1]` — const, line 634
- `let step = moveToDesk(ws, deskId, windowId, toDeskId, afterSlot ? afterSlot[afterSlot.length - 1] : null)` — let, line 635
- `const landed = requireDesk(step.ws, toDeskId)` — const, line 637
- `const desk = requireDesk(ws, deskId)` — const, line 646
- `const index = slotIndexOf(desk, windowId)` — const, line 648
- `const wasFocus = focusedWindowId(ws, desk) === windowId` — const, line 649
- `let step = push(start(ws),` — let, line 650
- `const after = requireDesk(step.ws, deskId)` — const, line 652
- `const at = Math.min(index, after.slots.length - 1)` — const, line 653
- `const next = at >= 0 ? after.slots[at][0] : null` — const, line 654

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/workspace|src/fixtures/desks/workspace.ts]] — import-or-re-export: `OpRefusal`, `Workspace`, `applyDeskOp`, `deskById`, `fromDeskState`; references `OpRefusal`, `Workspace`, `applyDeskOp`, `deskById`, `fromDeskState`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `DeskWindow`, `Step`, `Workspace`, `closeWindow`, `createDesk`, `deskById`, `focusAlong`, `focusPane`, `focusedSlot`, `focusedWindowId`, `moveFocused`, `moveToDesk`, `moveToDeskAt`, `moveWindowTo`, `openBeside`, `openStackBeside`, `pairFocused`, `renameDesk`, `reorderSlots`, `setCompanionDock`, `setCompanionShown`, `setFocus`, `setView`, `slotIndexOf`, `swapInView`, `undoClose`, `unpairFocused`; references `DeskWindow`, `Step`, `Workspace`, `closeWindow`, `createDesk`, `deskById`, `focusAlong`, `focusPane`, `focusedSlot`, `focusedWindowId`, `moveFocused`, `moveToDesk`, `moveToDeskAt`, `moveWindowTo`, `openBeside`, `openStackBeside`, `pairFocused`, `renameDesk`, `reorderSlots`, `setCompanionDock`, `setCompanionShown`, `setFocus`, `setView`, `slotIndexOf`, `swapInView`, `undoClose`, `unpairFocused`
- [[Reference/Desktop/TypeScript/screens/desks/overview/links|src/screens/desks/overview/links.ts]] — import-or-re-export: `Workspace`; references `Workspace`
- [[Reference/Desktop/TypeScript/screens/desks/store|src/screens/desks/store.ts]] — import-or-re-export: `EMPTY_WORKSPACE`, `OpRefusal`, `Step`, `Workspace`, `fromDeskState`, `restampOp`; references `EMPTY_WORKSPACE`, `OpRefusal`, `Step`, `Workspace`, `fromDeskState`, `restampOp`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ContentRefDto`, `DeskDto`, `DeskOpDto`, `DeskStateDto`, `DeskWindowKind`, `PadStackEntryDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/store.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/store.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/overview/links.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/overview/links.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/model/workspace.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/model/workspace.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_reader_rd1_model_parity.py](../../../../../../../../tests/test_reader_rd1_model_parity.py) — direct source contract: references the exact source path.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/model/workspace.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/model/workspace.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

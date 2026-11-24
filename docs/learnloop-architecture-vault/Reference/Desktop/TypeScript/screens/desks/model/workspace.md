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
| Source lines | 755 |
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
- `export const EMPTY_WORKSPACE: Workspace =` — const, line 58
- `export function fromDeskState(state: DeskStateDto): Workspace` — function, line 64
- `export function deskById(ws: Workspace, deskId: string | null | undefined): Desk | null` — function, line 97
- `export function slotIndexOf(desk: Desk, windowId: string | null | undefined): number` — function, line 101
- `export function focusedWindowId(ws: Workspace, desk: Desk | null): string | null` — function, line 107
- `export function focusedSlot(ws: Workspace, desk: Desk | null): number` — function, line 115
- `export function contentKey(content: ContentRefDto | null, stack?: PadStackEntryDto[] | null): string` — function, line 121
- `export function rangeCovers( content: ContentRefDto | null, spanId: string | null | undefined, order?: (spanId: string)` — function, line 145
- `export function findDuplicate( ws: Workspace, desk: Desk, content: ContentRefDto, spanId?: string | null, order?: (spanId: string)` — function, line 161
- `export class OpRefusal extends Error` — class, line 180
- `export function applyDeskOp(ws: Workspace, op: DeskOpDto): Workspace` — function, line 231
- `export interface Step` — interface, line 431
- `export const PAIR_COPY =` — const, line 438
- `export function restampOp(ws: Workspace, op: DeskOpDto):` — function, line 457
- `export function setFocus(ws: Workspace, deskId: string, windowId: string): Step` — function, line 466
- `export function openBeside( ws: Workspace, deskId: string, content: ContentRefDto, mintId: ()` — function, line 479
- `export function openPaired( ws: Workspace, deskId: string, originId: string, content: ContentRefDto, mintId: ()` — function, line 509
- `export function addToStack(ws: Workspace, deskId: string, windowId: string, padId: string): Step` — function, line 533
- `export function ensureRunningPad(ws: Workspace, deskId: string, mintPad: ()` — function, line 541
- `export function hasRunningPad(ws: Workspace, deskId: string): boolean` — function, line 546
- `export function openStackBeside(ws: Workspace, deskId: string, padIds: string[], mintId: ()` — function, line 553
- `export function closeWindow(ws: Workspace, deskId: string, windowId: string): Step` — function, line 571
- `export function undoClose(ws: Workspace, deskId: string): Step` — function, line 587
- `export function moveFocused(ws: Workspace, deskId: string, direction: -1 | 1): Step` — function, line 598
- `export function moveWindowTo(ws: Workspace, deskId: string, windowId: string, toSlot: number): Step` — function, line 608
- `export function pairFocused(ws: Workspace, deskId: string): Step` — function, line 616
- `export function unpairFocused(ws: Workspace, deskId: string): Step` — function, line 628
- `export function focusAlong(ws: Workspace, deskId: string, direction: -1 | 1): Step` — function, line 639
- `export function focusPane(ws: Workspace, deskId: string, direction: -1 | 1): Step | null` — function, line 650
- `export function positionAfter(ws: Workspace): string` — function, line 663
- `export function createDesk(ws: Workspace, deskId: string, title: string): Step` — function, line 668
- `export function renameDesk(ws: Workspace, deskId: string, title: string): Step` — function, line 672
- `export function setCompanionDock(ws: Workspace, deskId: string, dock: Desk["companion"]["dock"]): Step` — function, line 677
- `export function setCompanionShown(ws: Workspace, deskId: string, shown: boolean): Step` — function, line 684
- `export function setGoal(ws: Workspace, deskId: string, goalId: string | null): Step` — function, line 691
- `export function setView(ws: Workspace, deskId: string, windowId: string, view: Record<string, unknown>): Step` — function, line 697
- `export function swapInView(ws: Workspace, deskId: string, otherSlot: number): Step` — function, line 704
- `export function reorderSlots(ws: Workspace, deskId: string, order: string[][]): Step` — function, line 714
- `export function moveToDeskAt(ws: Workspace, deskId: string, windowId: string, toDeskId: string, toIndex: number): Step` — function, line 728
- `export function moveToDesk(ws: Workspace, deskId: string, windowId: string, toDeskId: string, afterWindowId: string | null): Step` — function, line 742

## Internal implementation anchors

- `function orderDesks(desks: Desk[]): Desk[]` — function, line 60
- `const windows: Record<string, DeskWindow> =` — const, line 65
- `const desks: Desk[] = state.desks.map((desk)` — const, line 66
- `const slots = [...desk.slots].sort((a, b)` — const, line 67
- `const first = desk.slots[0]` — const, line 110
- `const at = order(spanId)` — const, line 154
- `const from = order(fromSpanId)` — const, line 155
- `const to = order(toSpanId)` — const, line 156
- `const key = contentKey(content)` — const, line 168
- `const window = ws.windows[id]` — const, line 171
- `function replaceDesk(ws: Workspace, next: Desk): Workspace` — function, line 186
- `function normalizeActive(ws: Workspace, desk: Desk, activeIds: Set<string>): Record<string, DeskWindow>` — function, line 192
- `const windows =` — const, line 193
- `const window = windows[id]` — const, line 198
- `function activeSet(ws: Workspace, desk: Desk): Set<string>` — function, line 205
- `function requireDesk(ws: Workspace, deskId: string): Desk` — function, line 209
- `const desk = deskById(ws, deskId)` — const, line 210
- `function requireOpen(desk: Desk, windowId: string): number` — function, line 215
- `const index = slotIndexOf(desk, windowId)` — const, line 216
- `function sameEntry(a: PadStackEntryDto, b: PadStackEntryDto): boolean` — function, line 221
- `function bump(desk: Desk, fields: Partial<Desk> =` — function, line 225
- `const desk: Desk =` — const, line 235
- `const desk = requireDesk(ws, op.deskId)` — const, line 256
- `const desk = requireDesk(ws, op.deskId)` — const, line 260
- `const desk = requireDesk(ws, op.deskId)` — const, line 266
- `const desk = requireDesk(ws, op.deskId)` — const, line 271
- `const at = op.afterWindowId ? requireOpen(desk, op.afterWindowId) + 1 : desk.slots.length` — const, line 273
- `const slots = desk.slots.map((slot)` — const, line 274
- `const window: DeskWindow =` — const, line 276
- `const next = bump(desk,` — const, line 285
- `const withWindow =` — const, line 286
- `const desk = requireDesk(ws, op.deskId)` — const, line 290
- `const index = requireOpen(desk, op.windowId)` — const, line 291
- `const slots = desk.slots.map((slot)` — const, line 292
- `const active = activeSet(ws, desk)` — const, line 293
- `const next = bump(desk,` — const, line 295
- `const closedWindow = ws.windows[op.windowId]` — const, line 296
- `const windows = normalizeActive(ws, next, active)` — const, line 297
- `const closed =` — const, line 299
- `const desk = requireDesk(ws, op.deskId)` — const, line 303
- `const list = ws.closed[desk.deskId] ?? []` — const, line 304
- `const entry = list.find((closed)` — const, line 307
- `const at = Math.min(op.slot ?? desk.slots.length, desk.slots.length)` — const, line 309
- `const slots = desk.slots.map((slot)` — const, line 310
- `const next = bump(desk,` — const, line 312
- `const withWindow =` — const, line 313
- `const desk = requireDesk(ws, op.deskId)` — const, line 321
- `const index = requireOpen(desk, op.windowId)` — const, line 322
- `const slots = desk.slots.map((slot)` — const, line 323
- `const from = requireDesk(ws, op.deskId)` — const, line 329
- `const to = requireDesk(ws, op.toDeskId)` — const, line 331
- `const fromActive = activeSet(ws, from)` — const, line 333
- `const fromNext = bump(from,` — const, line 334
- `const at = op.afterWindowId ? requireOpen(to, op.afterWindowId) + 1 : to.slots.length` — const, line 338
- `const toSlots = to.slots.map((slot)` — const, line 339
- `const toNext = bump(to,` — const, line 341
- `let next = replaceDesk(replaceDesk(ws, fromNext), toNext)` — let, line 342
- `const toActive = activeSet(next, toNext)` — const, line 344
- `const desk = requireDesk(ws, op.deskId)` — const, line 349
- `const index = requireOpen(desk, op.windowId)` — const, line 350
- `const slots = desk.slots.map((slot)` — const, line 354
- `const active = activeSet(ws, desk)` — const, line 357
- `const next = bump(desk,` — const, line 360
- `const desk = requireDesk(ws, op.deskId)` — const, line 364
- `const index = requireOpen(desk, op.windowId)` — const, line 365
- `const slots = desk.slots.map((slot)` — const, line 367
- `const next = bump(desk,` — const, line 370
- `const desk = requireDesk(ws, op.deskId)` — const, line 374
- `const index = requireOpen(desk, op.windowId)` — const, line 375
- `const active = activeSet(ws, desk)` — const, line 377
- `const next = bump(desk)` — const, line 380
- `const desk = requireDesk(ws, op.deskId)` — const, line 384
- `const window = ws.windows[op.windowId]` — const, line 386
- `const desk = requireDesk(ws, op.deskId)` — const, line 393
- `const window = ws.windows[op.windowId]` — const, line 394
- `const stack = window.stack ?? []` — const, line 397
- `const present = stack.some((entry)` — const, line 398
- `let next = stack` — let, line 399
- `const desk = requireDesk(ws, op.deskId)` — const, line 409
- `const running = new Set(ws.runningPadIds ?? [])` — const, line 410
- `const stacks = desk.slots.flat().map((id)` — const, line 411
- `const holding = stacks.find((window)` — const, line 412
- `const runningPadIds = [...(ws.runningPadIds ?? []), op.padId]` — const, line 414
- `const entry: PadStackEntryDto =` — const, line 415
- `const first = stacks[0]` — const, line 417
- `const window: DeskWindow =` — const, line 421
- `const next = bump(desk,` — const, line 422
- `const withWindow =` — const, line 423
- `function push(step: Step, op: DeskOpDto): Step` — function, line 444
- `const versioned: DeskOpDto =` — const, line 445
- `const step = push(` — const, line 458
- `function start(ws: Workspace): Step` — function, line 462
- `const desk = requireDesk(ws, deskId)` — const, line 467
- `let step = start(ws)` — let, line 468
- `const index = slotIndexOf(desk, windowId)` — const, line 469
- `const desk = requireDesk(ws, deskId)` — const, line 486
- `const duplicate = findDuplicate(ws, desk, content, options.spanId ?? null, options.order)` — const, line 487
- `const windowId = mintId()` — const, line 489
- `const focus = focusedWindowId(ws, desk)` — const, line 490
- `let step = push(start(ws),` — let, line 491
- `const focused = setFocus(ws, deskId, originId)` — const, line 517
- `const opened = openBeside(focused.ws, deskId, content, mintId, options)` — const, line 518
- `let step: Step =` — let, line 519
- `const desk = requireDesk(step.ws, deskId)` — const, line 521
- `const index = slotIndexOf(desk, originId)` — const, line 522
- `const canPair = index >= 0 && desk.slots[index].length < PAIR_SIZE && desk.slots[index + 1]?.length === 1 && desk.slots[index + 1][0] === opened.windowId` — const, line 523
- `const after = setFocus(step.ws, deskId, opened.windowId)` — const, line 527
- `const window = ws.windows[windowId]` — const, line 534
- `const desk = deskById(ws, deskId)` — const, line 547
- `const running = new Set(ws.runningPadIds ?? [])` — const, line 548
- `const desk = requireDesk(ws, deskId)` — const, line 554
- `const windowId = mintId()` — const, line 555
- `const focus = focusedWindowId(ws, desk)` — const, line 556
- `let step = push(start(ws),` — let, line 557
- `function lastOfSlot(desk: Desk, windowId: string): string` — function, line 565
- `const slot = desk.slots[slotIndexOf(desk, windowId)]` — const, line 566
- `const desk = requireDesk(ws, deskId)` — const, line 572
- `const index = slotIndexOf(desk, windowId)` — const, line 573
- `const wasFocus = focusedWindowId(ws, desk) === windowId` — const, line 575
- `let step = push(start(ws),` — let, line 576
- `const after = requireDesk(step.ws, deskId)` — const, line 578
- `const at = Math.min(index, after.slots.length - 1)` — const, line 579
- `const next = at >= 0 ? (after.slots[at].find((id)` — const, line 580
- `const list = ws.closed[deskId] ?? []` — const, line 588
- `const entry = list[list.length - 1]` — const, line 589
- `let step = push(start(ws),` — let, line 592
- `const desk = requireDesk(ws, deskId)` — const, line 599
- `const id = focusedWindowId(ws, desk)` — const, line 600
- `const index = slotIndexOf(desk, id)` — const, line 601
- `const to = index + direction` — const, line 602
- `const desk = requireDesk(ws, deskId)` — const, line 609
- `const index = slotIndexOf(desk, windowId)` — const, line 610
- `const desk = requireDesk(ws, deskId)` — const, line 617
- `const id = focusedWindowId(ws, desk)` — const, line 618
- `const index = slotIndexOf(desk, id)` — const, line 619
- `const desk = requireDesk(ws, deskId)` — const, line 629
- `const id = focusedWindowId(ws, desk)` — const, line 630
- `const index = slotIndexOf(desk, id)` — const, line 631
- `let step = push(start(ws),` — let, line 633
- `const desk = requireDesk(ws, deskId)` — const, line 640
- `const index = focusedSlot(ws, desk)` — const, line 641
- `const to = index + direction` — const, line 642
- `const target = desk.slots[to].find((id)` — const, line 644
- `const desk = requireDesk(ws, deskId)` — const, line 651
- `const id = focusedWindowId(ws, desk)` — const, line 652
- `const index = slotIndexOf(desk, id)` — const, line 653
- `const slot = desk.slots[index]` — const, line 655
- `const pane = slot.indexOf(id)` — const, line 656
- `const to = pane + direction` — const, line 657
- `const last = ws.desks[ws.desks.length - 1]?.position ?? ""` — const, line 664
- `const desk = requireDesk(ws, deskId)` — const, line 678
- `const desk = requireDesk(ws, deskId)` — const, line 685
- `const desk = requireDesk(ws, deskId)` — const, line 692
- `const desk = requireDesk(ws, deskId)` — const, line 698
- `const desk = requireDesk(ws, deskId)` — const, line 705
- `const id = focusedWindowId(ws, desk)` — const, line 706
- `const index = slotIndexOf(desk, id)` — const, line 707
- `let step = start(ws)` — let, line 715
- `const desk = requireDesk(step.ws, deskId)` — const, line 717
- `const at = slotIndexOf(desk, slot[0])` — const, line 718
- `const to = requireDesk(ws, toDeskId)` — const, line 729
- `const at = Math.max(0, Math.min(toIndex, to.slots.length))` — const, line 730
- `const afterSlot = to.slots[at - 1]` — const, line 731
- `let step = moveToDesk(ws, deskId, windowId, toDeskId, afterSlot ? afterSlot[afterSlot.length - 1] : null)` — let, line 732
- `const landed = requireDesk(step.ws, toDeskId)` — const, line 734
- `const desk = requireDesk(ws, deskId)` — const, line 743
- `const index = slotIndexOf(desk, windowId)` — const, line 745
- `const wasFocus = focusedWindowId(ws, desk) === windowId` — const, line 746
- `let step = push(start(ws),` — let, line 747
- `const after = requireDesk(step.ws, deskId)` — const, line 749
- `const at = Math.min(index, after.slots.length - 1)` — const, line 750
- `const next = at >= 0 ? after.slots[at][0] : null` — const, line 751

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/workspace|src/fixtures/desks/workspace.ts]] — import-or-re-export: `OpRefusal`, `Workspace`, `applyDeskOp`, `deskById`, `fromDeskState`; references `OpRefusal`, `Workspace`, `applyDeskOp`, `deskById`, `fromDeskState`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `DeskWindow`, `Step`, `Workspace`, `addToStack`, `closeWindow`, `createDesk`, `deskById`, `ensureRunningPad`, `focusAlong`, `focusPane`, `focusedSlot`, `focusedWindowId`, `hasRunningPad`, `moveFocused`, `moveToDesk`, `moveToDeskAt`, `moveWindowTo`, `openBeside`, `openPaired`, `openStackBeside`, `pairFocused`, `renameDesk`, `reorderSlots`, `setCompanionDock`, `setCompanionShown`, `setFocus`, `setGoal`, `setView`, `slotIndexOf`, `swapInView`, `undoClose`, `unpairFocused`; references `DeskWindow`, `Step`, `Workspace`, `addToStack`, `closeWindow`, `createDesk`, `deskById`, `ensureRunningPad`, `focusAlong`, `focusPane`, `focusedSlot`, `focusedWindowId`, `hasRunningPad`, `moveFocused`, `moveToDesk`, `moveToDeskAt`, `moveWindowTo`, `openBeside`, `openPaired`, `openStackBeside`, `pairFocused`, `renameDesk`, `reorderSlots`, `setCompanionDock`, `setCompanionShown`, `setFocus`, `setGoal`, `setView`, `slotIndexOf`, `swapInView`, `undoClose`, `unpairFocused`
- [[Reference/Desktop/TypeScript/screens/desks/lesson/model|src/screens/desks/lesson/model.ts]] — import-or-re-export: `Step`, `Workspace`, `deskById`, `restampOp`, `setFocus`; references `Step`, `Workspace`, `deskById`, `restampOp`, `setFocus`
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
- [apps/learnloop-tauri/src/screens/desks/lesson/model.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/lesson/model.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/DeskShell.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/DeskShell.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

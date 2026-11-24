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
| Source lines | 812 |
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
- `export function rangeCovers( content: ContentRefDto | null, spanId: string | null | undefined, order?: (spanId: string)` — function, line 148
- `export function findDuplicate( ws: Workspace, desk: Desk, content: ContentRefDto, spanId?: string | null, order?: (spanId: string)` — function, line 164
- `export class OpRefusal extends Error` — class, line 183
- `export function applyDeskOp(ws: Workspace, op: DeskOpDto): Workspace` — function, line 234
- `export interface Step` — interface, line 434
- `export const PAIR_COPY =` — const, line 441
- `export function restampOp(ws: Workspace, op: DeskOpDto):` — function, line 460
- `export function setFocus(ws: Workspace, deskId: string, windowId: string): Step` — function, line 469
- `export function openBeside( ws: Workspace, deskId: string, content: ContentRefDto, mintId: ()` — function, line 482
- `export function openPaired( ws: Workspace, deskId: string, originId: string, content: ContentRefDto, mintId: ()` — function, line 512
- `export function addToStack(ws: Workspace, deskId: string, windowId: string, padId: string): Step` — function, line 536
- `export function ensureRunningPad(ws: Workspace, deskId: string, mintPad: ()` — function, line 544
- `export function hasRunningPad(ws: Workspace, deskId: string): boolean` — function, line 549
- `export function openStackBeside(ws: Workspace, deskId: string, padIds: string[], mintId: ()` — function, line 556
- `export function closeWindow(ws: Workspace, deskId: string, windowId: string): Step` — function, line 574
- `export function replaceWindow( ws: Workspace, deskId: string, windowId: string, content: ContentRefDto, mintId: ()` — function, line 596
- `export function undoClose(ws: Workspace, deskId: string): Step` — function, line 644
- `export function moveFocused(ws: Workspace, deskId: string, direction: -1 | 1): Step` — function, line 655
- `export function moveWindowTo(ws: Workspace, deskId: string, windowId: string, toSlot: number): Step` — function, line 665
- `export function pairFocused(ws: Workspace, deskId: string): Step` — function, line 673
- `export function unpairFocused(ws: Workspace, deskId: string): Step` — function, line 685
- `export function focusAlong(ws: Workspace, deskId: string, direction: -1 | 1): Step` — function, line 696
- `export function focusPane(ws: Workspace, deskId: string, direction: -1 | 1): Step | null` — function, line 707
- `export function positionAfter(ws: Workspace): string` — function, line 720
- `export function createDesk(ws: Workspace, deskId: string, title: string): Step` — function, line 725
- `export function renameDesk(ws: Workspace, deskId: string, title: string): Step` — function, line 729
- `export function setCompanionDock(ws: Workspace, deskId: string, dock: Desk["companion"]["dock"]): Step` — function, line 734
- `export function setCompanionShown(ws: Workspace, deskId: string, shown: boolean): Step` — function, line 741
- `export function setGoal(ws: Workspace, deskId: string, goalId: string | null): Step` — function, line 748
- `export function setView(ws: Workspace, deskId: string, windowId: string, view: Record<string, unknown>): Step` — function, line 754
- `export function swapInView(ws: Workspace, deskId: string, otherSlot: number): Step` — function, line 761
- `export function reorderSlots(ws: Workspace, deskId: string, order: string[][]): Step` — function, line 771
- `export function moveToDeskAt(ws: Workspace, deskId: string, windowId: string, toDeskId: string, toIndex: number): Step` — function, line 785
- `export function moveToDesk(ws: Workspace, deskId: string, windowId: string, toDeskId: string, afterWindowId: string | null): Step` — function, line 799

## Internal implementation anchors

- `function orderDesks(desks: Desk[]): Desk[]` — function, line 60
- `const windows: Record<string, DeskWindow> =` — const, line 65
- `const desks: Desk[] = state.desks.map((desk)` — const, line 66
- `const slots = [...desk.slots].sort((a, b)` — const, line 67
- `const first = desk.slots[0]` — const, line 110
- `const at = order(spanId)` — const, line 157
- `const from = order(fromSpanId)` — const, line 158
- `const to = order(toSpanId)` — const, line 159
- `const key = contentKey(content)` — const, line 171
- `const window = ws.windows[id]` — const, line 174
- `function replaceDesk(ws: Workspace, next: Desk): Workspace` — function, line 189
- `function normalizeActive(ws: Workspace, desk: Desk, activeIds: Set<string>): Record<string, DeskWindow>` — function, line 195
- `const windows =` — const, line 196
- `const window = windows[id]` — const, line 201
- `function activeSet(ws: Workspace, desk: Desk): Set<string>` — function, line 208
- `function requireDesk(ws: Workspace, deskId: string): Desk` — function, line 212
- `const desk = deskById(ws, deskId)` — const, line 213
- `function requireOpen(desk: Desk, windowId: string): number` — function, line 218
- `const index = slotIndexOf(desk, windowId)` — const, line 219
- `function sameEntry(a: PadStackEntryDto, b: PadStackEntryDto): boolean` — function, line 224
- `function bump(desk: Desk, fields: Partial<Desk> =` — function, line 228
- `const desk: Desk =` — const, line 238
- `const desk = requireDesk(ws, op.deskId)` — const, line 259
- `const desk = requireDesk(ws, op.deskId)` — const, line 263
- `const desk = requireDesk(ws, op.deskId)` — const, line 269
- `const desk = requireDesk(ws, op.deskId)` — const, line 274
- `const at = op.afterWindowId ? requireOpen(desk, op.afterWindowId) + 1 : desk.slots.length` — const, line 276
- `const slots = desk.slots.map((slot)` — const, line 277
- `const window: DeskWindow =` — const, line 279
- `const next = bump(desk,` — const, line 288
- `const withWindow =` — const, line 289
- `const desk = requireDesk(ws, op.deskId)` — const, line 293
- `const index = requireOpen(desk, op.windowId)` — const, line 294
- `const slots = desk.slots.map((slot)` — const, line 295
- `const active = activeSet(ws, desk)` — const, line 296
- `const next = bump(desk,` — const, line 298
- `const closedWindow = ws.windows[op.windowId]` — const, line 299
- `const windows = normalizeActive(ws, next, active)` — const, line 300
- `const closed =` — const, line 302
- `const desk = requireDesk(ws, op.deskId)` — const, line 306
- `const list = ws.closed[desk.deskId] ?? []` — const, line 307
- `const entry = list.find((closed)` — const, line 310
- `const at = Math.min(op.slot ?? desk.slots.length, desk.slots.length)` — const, line 312
- `const slots = desk.slots.map((slot)` — const, line 313
- `const next = bump(desk,` — const, line 315
- `const withWindow =` — const, line 316
- `const desk = requireDesk(ws, op.deskId)` — const, line 324
- `const index = requireOpen(desk, op.windowId)` — const, line 325
- `const slots = desk.slots.map((slot)` — const, line 326
- `const from = requireDesk(ws, op.deskId)` — const, line 332
- `const to = requireDesk(ws, op.toDeskId)` — const, line 334
- `const fromActive = activeSet(ws, from)` — const, line 336
- `const fromNext = bump(from,` — const, line 337
- `const at = op.afterWindowId ? requireOpen(to, op.afterWindowId) + 1 : to.slots.length` — const, line 341
- `const toSlots = to.slots.map((slot)` — const, line 342
- `const toNext = bump(to,` — const, line 344
- `let next = replaceDesk(replaceDesk(ws, fromNext), toNext)` — let, line 345
- `const toActive = activeSet(next, toNext)` — const, line 347
- `const desk = requireDesk(ws, op.deskId)` — const, line 352
- `const index = requireOpen(desk, op.windowId)` — const, line 353
- `const slots = desk.slots.map((slot)` — const, line 357
- `const active = activeSet(ws, desk)` — const, line 360
- `const next = bump(desk,` — const, line 363
- `const desk = requireDesk(ws, op.deskId)` — const, line 367
- `const index = requireOpen(desk, op.windowId)` — const, line 368
- `const slots = desk.slots.map((slot)` — const, line 370
- `const next = bump(desk,` — const, line 373
- `const desk = requireDesk(ws, op.deskId)` — const, line 377
- `const index = requireOpen(desk, op.windowId)` — const, line 378
- `const active = activeSet(ws, desk)` — const, line 380
- `const next = bump(desk)` — const, line 383
- `const desk = requireDesk(ws, op.deskId)` — const, line 387
- `const window = ws.windows[op.windowId]` — const, line 389
- `const desk = requireDesk(ws, op.deskId)` — const, line 396
- `const window = ws.windows[op.windowId]` — const, line 397
- `const stack = window.stack ?? []` — const, line 400
- `const present = stack.some((entry)` — const, line 401
- `let next = stack` — let, line 402
- `const desk = requireDesk(ws, op.deskId)` — const, line 412
- `const running = new Set(ws.runningPadIds ?? [])` — const, line 413
- `const stacks = desk.slots.flat().map((id)` — const, line 414
- `const holding = stacks.find((window)` — const, line 415
- `const runningPadIds = [...(ws.runningPadIds ?? []), op.padId]` — const, line 417
- `const entry: PadStackEntryDto =` — const, line 418
- `const first = stacks[0]` — const, line 420
- `const window: DeskWindow =` — const, line 424
- `const next = bump(desk,` — const, line 425
- `const withWindow =` — const, line 426
- `function push(step: Step, op: DeskOpDto): Step` — function, line 447
- `const versioned: DeskOpDto =` — const, line 448
- `const step = push(` — const, line 461
- `function start(ws: Workspace): Step` — function, line 465
- `const desk = requireDesk(ws, deskId)` — const, line 470
- `let step = start(ws)` — let, line 471
- `const index = slotIndexOf(desk, windowId)` — const, line 472
- `const desk = requireDesk(ws, deskId)` — const, line 489
- `const duplicate = findDuplicate(ws, desk, content, options.spanId ?? null, options.order)` — const, line 490
- `const windowId = mintId()` — const, line 492
- `const focus = focusedWindowId(ws, desk)` — const, line 493
- `let step = push(start(ws),` — let, line 494
- `const focused = setFocus(ws, deskId, originId)` — const, line 520
- `const opened = openBeside(focused.ws, deskId, content, mintId, options)` — const, line 521
- `let step: Step =` — let, line 522
- `const desk = requireDesk(step.ws, deskId)` — const, line 524
- `const index = slotIndexOf(desk, originId)` — const, line 525
- `const canPair = index >= 0 && desk.slots[index].length < PAIR_SIZE && desk.slots[index + 1]?.length === 1 && desk.slots[index + 1][0] === opened.windowId` — const, line 526
- `const after = setFocus(step.ws, deskId, opened.windowId)` — const, line 530
- `const window = ws.windows[windowId]` — const, line 537
- `const desk = deskById(ws, deskId)` — const, line 550
- `const running = new Set(ws.runningPadIds ?? [])` — const, line 551
- `const desk = requireDesk(ws, deskId)` — const, line 557
- `const windowId = mintId()` — const, line 558
- `const focus = focusedWindowId(ws, desk)` — const, line 559
- `let step = push(start(ws),` — let, line 560
- `function lastOfSlot(desk: Desk, windowId: string): string` — function, line 568
- `const slot = desk.slots[slotIndexOf(desk, windowId)]` — const, line 569
- `const desk = requireDesk(ws, deskId)` — const, line 575
- `const index = slotIndexOf(desk, windowId)` — const, line 576
- `const wasFocus = focusedWindowId(ws, desk) === windowId` — const, line 578
- `let step = push(start(ws),` — let, line 579
- `const after = requireDesk(step.ws, deskId)` — const, line 581
- `const at = Math.min(index, after.slots.length - 1)` — const, line 582
- `const next = at >= 0 ? (after.slots[at].find((id)` — const, line 583
- `const desk = requireDesk(ws, deskId)` — const, line 604
- `const index = slotIndexOf(desk, windowId)` — const, line 605
- `const wasFocus = focusedWindowId(ws, desk) === windowId` — const, line 607
- `const pair = desk.slots[index]` — const, line 608
- `const partner = pair.length > 1 ? pair.find((id)` — const, line 609
- `const wasLeft = pair[0] === windowId` — const, line 610
- `const wasActive = ws.windows[windowId]?.active ?? false` — const, line 611
- `const others =` — const, line 612
- `const duplicate = findDuplicate(ws, others, content)` — const, line 613
- `const opened = duplicate ?? mintId()` — const, line 614
- `let step = start(ws)` — let, line 615
- `const relation = ws.windows[windowId]?.view?.openedBeside` — const, line 617
- `const focused = setFocus(step.ws, deskId, opened)` — const, line 636
- `const closed = (step.ws.closed[deskId] ?? []).filter((entry)` — const, line 639
- `const list = ws.closed[deskId] ?? []` — const, line 645
- `const entry = list[list.length - 1]` — const, line 646
- `let step = push(start(ws),` — let, line 649
- `const desk = requireDesk(ws, deskId)` — const, line 656
- `const id = focusedWindowId(ws, desk)` — const, line 657
- `const index = slotIndexOf(desk, id)` — const, line 658
- `const to = index + direction` — const, line 659
- `const desk = requireDesk(ws, deskId)` — const, line 666
- `const index = slotIndexOf(desk, windowId)` — const, line 667
- `const desk = requireDesk(ws, deskId)` — const, line 674
- `const id = focusedWindowId(ws, desk)` — const, line 675
- `const index = slotIndexOf(desk, id)` — const, line 676
- `const desk = requireDesk(ws, deskId)` — const, line 686
- `const id = focusedWindowId(ws, desk)` — const, line 687
- `const index = slotIndexOf(desk, id)` — const, line 688
- `let step = push(start(ws),` — let, line 690
- `const desk = requireDesk(ws, deskId)` — const, line 697
- `const index = focusedSlot(ws, desk)` — const, line 698
- `const to = index + direction` — const, line 699
- `const target = desk.slots[to].find((id)` — const, line 701
- `const desk = requireDesk(ws, deskId)` — const, line 708
- `const id = focusedWindowId(ws, desk)` — const, line 709
- `const index = slotIndexOf(desk, id)` — const, line 710
- `const slot = desk.slots[index]` — const, line 712
- `const pane = slot.indexOf(id)` — const, line 713
- `const to = pane + direction` — const, line 714
- `const last = ws.desks[ws.desks.length - 1]?.position ?? ""` — const, line 721
- `const desk = requireDesk(ws, deskId)` — const, line 735
- `const desk = requireDesk(ws, deskId)` — const, line 742
- `const desk = requireDesk(ws, deskId)` — const, line 749
- `const desk = requireDesk(ws, deskId)` — const, line 755
- `const desk = requireDesk(ws, deskId)` — const, line 762
- `const id = focusedWindowId(ws, desk)` — const, line 763
- `const index = slotIndexOf(desk, id)` — const, line 764
- `let step = start(ws)` — let, line 772
- `const desk = requireDesk(step.ws, deskId)` — const, line 774
- `const at = slotIndexOf(desk, slot[0])` — const, line 775
- `const to = requireDesk(ws, toDeskId)` — const, line 786
- `const at = Math.max(0, Math.min(toIndex, to.slots.length))` — const, line 787
- `const afterSlot = to.slots[at - 1]` — const, line 788
- `let step = moveToDesk(ws, deskId, windowId, toDeskId, afterSlot ? afterSlot[afterSlot.length - 1] : null)` — let, line 789
- `const landed = requireDesk(step.ws, toDeskId)` — const, line 791
- `const desk = requireDesk(ws, deskId)` — const, line 800
- `const index = slotIndexOf(desk, windowId)` — const, line 802
- `const wasFocus = focusedWindowId(ws, desk) === windowId` — const, line 803
- `let step = push(start(ws),` — let, line 804
- `const after = requireDesk(step.ws, deskId)` — const, line 806
- `const at = Math.min(index, after.slots.length - 1)` — const, line 807
- `const next = at >= 0 ? after.slots[at][0] : null` — const, line 808

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/workspace|src/fixtures/desks/workspace.ts]] — import-or-re-export: `OpRefusal`, `Workspace`, `applyDeskOp`, `deskById`, `fromDeskState`; references `OpRefusal`, `Workspace`, `applyDeskOp`, `deskById`, `fromDeskState`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `DeskWindow`, `Step`, `Workspace`, `addToStack`, `closeWindow`, `createDesk`, `deskById`, `ensureRunningPad`, `focusAlong`, `focusPane`, `focusedSlot`, `focusedWindowId`, `hasRunningPad`, `moveFocused`, `moveToDesk`, `moveToDeskAt`, `moveWindowTo`, `openBeside`, `openPaired`, `openStackBeside`, `pairFocused`, `renameDesk`, `reorderSlots`, `replaceWindow`, `setCompanionDock`, `setCompanionShown`, `setFocus`, `setGoal`, `setView`, `slotIndexOf`, `swapInView`, `undoClose`, `unpairFocused`; references `DeskWindow`, `Step`, `Workspace`, `addToStack`, `closeWindow`, `createDesk`, `deskById`, `ensureRunningPad`, `focusAlong`, `focusPane`, `focusedSlot`, `focusedWindowId`, `hasRunningPad`, `moveFocused`, `moveToDesk`, `moveToDeskAt`, `moveWindowTo`, `openBeside`, `openPaired`, `openStackBeside`, `pairFocused`, `renameDesk`, `reorderSlots`, `replaceWindow`, `setCompanionDock`, `setCompanionShown`, `setFocus`, `setGoal`, `setView`, `slotIndexOf`, `swapInView`, `undoClose`, `unpairFocused`
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

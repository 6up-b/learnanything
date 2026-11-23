---
title: "Desktop module · src/screens/desks/DeskShell.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.DeskShell"
language: "TypeScript"
area: "TypeScript/screens/desks"
source_path: "apps/learnloop-tauri/src/screens/desks/DeskShell.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/DeskShell.tsx"
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

# `src/screens/desks/DeskShell.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/_area|TypeScript/screens/desks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `DeskShell` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/DeskShell.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/DeskShell.tsx) |
| Source lines | 2009 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/_area|TypeScript/screens/desks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]]

## Public API

- `export interface DeskTransport extends OutboxTransport` — interface, line 103
- `export const LIVE_DESK_TRANSPORT: DeskTransport =` — const, line 110
- `export interface PaneRenderInput` — interface, line 120
- `export interface DeskDebugHandle` — interface, line 136
- `export const KIND_GLYPH: Record<string, string> =` — const, line 161
- `export interface DeskShellProps` — interface, line 214
- `export function DeskShell(` — function, line 237
- `export function isVideoCard(card: SourceLibraryCard): boolean` — function, line 1889
- `export function contentForCard(card: SourceLibraryCard, extractionId: string): ContentRefDto` — function, line 1893

## Internal implementation anchors

- `type DeskWindow, type Step, type Workspace, } from "./model/workspace"` — type, line 34
- `type Step, type Workspace, } from "./model/workspace"` — type, line 35
- `type Workspace, } from "./model/workspace"` — type, line 36
- `type Rect, type Stage, } from "./geometry"` — type, line 50
- `type Stage, } from "./geometry"` — type, line 51
- `type Camera, type ZoomGesture, type ZoomSource, } from "./overview/engine"` — type, line 66
- `type ZoomGesture, type ZoomSource, } from "./overview/engine"` — type, line 67
- `type ZoomSource, } from "./overview/engine"` — type, line 68
- `type DeskAction, type Timers, } from "./keys/router"` — type, line 81
- `type Timers, } from "./keys/router"` — type, line 82
- `const UNDO_CLOSE_MS = 9_000` — const, line 127
- `const TOAST_MS = 2_200` — const, line 129
- `const VIEW_SAVE_IDLE_MS = 2_000` — const, line 131
- `const MOVED_NOTICE_MS = 6_000` — const, line 133
- `function prefersReducedMotion(): boolean` — function, line 144
- `function slotKey(deskId: string, slot: string[]): string` — function, line 153
- `function intersects(rect: Rect, stage: Stage): boolean` — function, line 157
- `const KIND_WORD: Record<string, string> =` — const, line 173
- `function defaultMintId(prefix: string): string` — function, line 185
- `function shortName(title: string): string` — function, line 193
- `const words = title.split(/\s+/).filter(Boolean)` — const, line 194
- `function readStored(key: string): string | null` — function, line 198
- `function writeStored(key: string, value: string): void` — function, line 206
- `const store = useMemo( ()` — const, line 254
- `const storeWs = useSyncExternalStore(store.subscribe, store.getSnapshot)` — const, line 258
- `const ws: Workspace | null = storeReady ? storeWs : null` — const, line 260
- `const wsRef = useMemo(()` — const, line 261
- `const deskKey = `learnloop.desks.current.$` — const, line 263
- `const stageRef = useRef<HTMLElement | null>(null)` — const, line 278
- `const viewport = initialViewport ??` — const, line 280
- `const shelf = viewport.width < DESK_SIZES.shelfFoldBelow ? DESK_SIZES.shelfRail : DESK_SIZES.shelf` — const, line 281
- `const preOverview = useRef<` — const, line 299
- `const worldRef = useRef<HTMLDivElement | null>(null)` — const, line 300
- `const boxEls = useRef(new Map<string, HTMLElement>())` — const, line 303
- `const innerEls = useRef(new Map<string, HTMLElement>())` — const, line 304
- `const cardEls = useRef(new Map<string, HTMLElement>())` — const, line 305
- `const ringEls = useRef(new Map<string, HTMLElement>())` — const, line 306
- `const slotElements = useCallback((): Map<string, SlotElements>` — const, line 307
- `const out = new Map<string, SlotElements>()` — const, line 308
- `const lateEls = useRef(new Map<string, HTMLElement>())` — const, line 312
- `const sliverEls = useRef(new Map<string, HTMLElement>())` — const, line 313
- `const miniatures = useMemo(()` — const, line 314
- `const miniHosts = useRef(new Map<string, HTMLDivElement>())` — const, line 315
- `const onEndRef = useRef<(goal: 0 | 1, base: 0 | 1)` — const, line 316
- `const controller = useMemo(()` — const, line 317
- `const jumps = useRef(new Map<string, (spanId: string)` — const, line 318
- `const media = useRef(new Map<string, ()` — const, line 319
- `const pendingJump = useRef(new Map<string, string>())` — const, line 320
- `const toastNow = useCallback((text: string)` — const, line 322
- `const handle = timers.set(()` — const, line 325
- `const setCurrentDeskId = useCallback((deskId: string | null)` — const, line 331
- `const commit = useCallback((step: Step)` — const, line 336
- `const total = notice.dropped + notice.lost` — const, line 345
- `const chain = useCallback((first: Step, next: (ws: Workspace)` — const, line 351
- `const second = next(first.ws)` — const, line 352
- `const firstRun = useCallback(async (base: Workspace, cards: SourceLibraryCard[] | null): Promise<Step>` — const, line 356
- `const card = firstSourceId ? cards?.find((entry)` — const, line 357
- `const deskId = mintId("desk")` — const, line 358
- `const created = createDesk(base, deskId, card ? `new desk · $` — const, line 359
- `const extractionId = await transport.resolveExtraction(card.sourceId).catch(()` — const, line 361
- `let live = true` — let, line 367
- `const desk = ws ? deskById(ws, currentDeskId) ?? ws.desks[0] ?? null : null` — const, line 389
- `const deskId = desk?.deskId ?? null` — const, line 390
- `const focusId = ws && desk ? focusedWindowId(ws, desk) : null` — const, line 391
- `const focusSlotIndex = ws && desk ? focusedSlot(ws, desk) : -1` — const, line 392
- `const slotCount = desk?.slots.length ?? 0` — const, line 400
- `const keepPrevious = useRef(false)` — const, line 401
- `const next = ensureVisible(cams[deskId] ?? 0, focusSlotIndex, slotCount, stage, keepPrevious.current)` — const, line 405
- `const node = stageRef.current` — const, line 413
- `const measure = ()` — const, line 414
- `const shell = node?.closest(".desk-shell") as HTMLElement | null` — const, line 417
- `const observer = typeof ResizeObserver === "undefined" || !node ? null : new ResizeObserver(measure)` — const, line 421
- `const cam = deskId ? camX[deskId] ?? 0 : 0` — const, line 430
- `const visibility = useMemo(()` — const, line 431
- `const deskIndex = ws && desk ? ws.desks.indexOf(desk) : 0` — const, line 432
- `const lifecycles = useMemo(()` — const, line 436
- `const out: Record<string, WindowLifecycle> =` — const, line 437
- `const onCurrent = each.deskId === deskId` — const, line 440
- `const activeWindowId = Object.values(lifecycles).find((each)` — const, line 456
- `const held = document.activeElement` — const, line 458
- `const owner = held && held !== document.body ? windowOfTarget(held) : null` — const, line 459
- `const target = activeWindowId ? document.querySelector<HTMLElement>(`[$` — const, line 461
- `const lifecyclesRef = useRef(lifecycles)` — const, line 467
- `const focusIdRef = useRef(focusId)` — const, line 469
- `const focusModeRef = useRef(focusMode)` — const, line 477
- `const switchDesk = useCallback((direction: -1 | 1): boolean` — const, line 480
- `const current = wsRef.current` — const, line 481
- `const index = current.desks.findIndex((each)` — const, line 482
- `const next = current.desks[index + direction]` — const, line 483
- `const deskIdRef = useRef(deskId)` — const, line 488
- `const titleOf = useCallback((window: DeskWindow | undefined): string` — const, line 491
- `const known = status[window.windowId]?.title` — const, line 493
- `const content = window.content` — const, line 495
- `const ovLayout = useMemo(()` — const, line 505
- `const ovLayoutRef = useRef(ovLayout)` — const, line 506
- `const stageNow = useRef(stage)` — const, line 508
- `const camXRef = useRef(camX)` — const, line 510
- `const overviewRef = useRef(overview)` — const, line 512
- `const ovCamRef = useRef(ovCam)` — const, line 514
- `const selectionRef = useRef(selection)` — const, line 516
- `const visitedRef = useRef(visited)` — const, line 518
- `const showRelationsRef = useRef(showRelations)` — const, line 520
- `const reduced = reducedMotion ?? prefersReducedMotion()` — const, line 522
- `const pendingLeave = useRef<` — const, line 523
- `const cardOf = useCallback((windowId: string | null | undefined): Rect | null` — const, line 526
- `const layout = ovLayoutRef.current` — const, line 527
- `const current = wsRef.current` — const, line 528
- `const index = slotIndexOf(each, windowId)` — const, line 531
- `const readingRectOf = useCallback((current: Workspace, row: number, index: number, readingRow: number, cams: Record<string, number>, st: Stage): Rect` — const, line 539
- `const each = current.desks[row]` — const, line 540
- `const rect = slotRects(each.slots.length, st)[index]` — const, line 541
- `const relatedTo = useCallback((windowId: string | null | undefined): Relation[]` — const, line 545
- `const recedes = useCallback((slot: string[], selected: string | null, related: Relation[], relationsOn: boolean): boolean` — const, line 548
- `const planZoom = useCallback((base: 0 | 1, readingDeskId: string, cams: Record<string, number>, selected: string | null, B: Camera): ZoomPlan | null` — const, line 553
- `const current = wsRef.current` — const, line 554
- `const layout = ovLayoutRef.current` — const, line 555
- `const st = stageNow.current` — const, line 556
- `const readingRow = Math.max(0, current.desks.findIndex((each)` — const, line 558
- `const related = relatedTo(selected)` — const, line 559
- `const items: ZoomPlan["items"] = []` — const, line 560
- `const rings: ZoomPlan["rings"] = []` — const, line 561
- `const a = readingRectOf(current, row, index, readingRow, cams, st)` — const, line 563
- `const b = layout.cards[row][index]` — const, line 564
- `const readingPanes = paneRects(a, slot.length)` — const, line 565
- `const cardPanes = paneRects(b, slot.length)` — const, line 566
- `const live = visitedRef.current.has(each.deskId) && each.deskId === readingDeskId && intersects(a, st)` — const, line 567
- `const recede = recedes(slot, selected, related, showRelationsRef.current)` — const, line 568
- `const focus = selected !== null && slot.includes(selected)` — const, line 569
- `const isRelated = showRelationsRef.current && slot.some((id)` — const, line 570
- `const pa = readingPanes[pane]` — const, line 572
- `const pb = cardPanes[pane]` — const, line 573
- `const zoomTargets = useCallback(()` — const, line 581
- `const beginEnter = useCallback((): boolean` — const, line 590
- `const id = deskIdRef.current` — const, line 592
- `const selected = focusIdRef.current` — const, line 595
- `const B = enteringCamera(cardOf(selected), stageNow.current)` — const, line 597
- `const plan = planZoom(0, id, camXRef.current, selected, B)` — const, line 602
- `const beginLeave = useCallback((to:` — const, line 610
- `const target = to ?? preOverview.current ?? (selectionRef.current ?` — const, line 612
- `const deskIdTo = target.deskId` — const, line 614
- `const windowTo = "windowId" in target ? target.windowId : target.focusId` — const, line 615
- `const current = wsRef.current` — const, line 616
- `const each = deskById(current, deskIdTo)` — const, line 617
- `const cams =` — const, line 619
- `const index = windowTo ? slotIndexOf(each, windowTo) : -1` — const, line 620
- `const plan = planZoom(1, deskIdTo, cams, windowTo, ovCamRef.current)` — const, line 622
- `const plan = controller.plan` — const, line 635
- `const leave = pendingLeave.current` — const, line 653
- `const toggleOverview = useCallback((to:` — const, line 673
- `const world = worldRef.current` — const, line 680
- `const id = deskIdRef.current` — const, line 685
- `const target = to ?? (preOverview.current ?` — const, line 693
- `const moveOverviewSelection = useCallback((direction: "left" | "right" | "up" | "down")` — const, line 711
- `const layout = ovLayoutRef.current` — const, line 712
- `const current = wsRef.current` — const, line 713
- `const sel = selectionRef.current` — const, line 714
- `let row = sel ? current.desks.findIndex((each)` — let, line 716
- `let slot = sel ? slotIndexOf(current.desks[row] ?? current.desks[0], sel.windowId) : 0` — let, line 717
- `const next = moveSelection(layout,` — const, line 722
- `const each = current.desks[next.row]` — const, line 723
- `const windowId = each?.slots[next.slot]?.find((id)` — const, line 724
- `const gather = useCallback((toNewDesk: boolean)` — const, line 732
- `const current = wsRef.current` — const, line 733
- `const id = deskIdRef.current` — const, line 734
- `const focus = focusIdRef.current` — const, line 735
- `const each = id ? deskById(current, id) : null` — const, line 736
- `const related = relationsOf(current, focus).filter((relation)` — const, line 743
- `const moving = [focus, ...related.slice(0, DRAWN_RELATIONS).map((relation)` — const, line 756
- `const newDeskId = mintId("desk")` — const, line 757
- `const title = `gathered · $` — const, line 758
- `let step = createDesk(current, newDeskId, title)` — let, line 759
- `let after: string | null = null` — let, line 760
- `const next = moveToDesk(step.ws, id, windowId, newDeskId, after)` — const, line 762
- `const focused = setFocus(step.ws, newDeskId, focus)` — const, line 766
- `const run = useCallback((action: DeskAction): boolean` — const, line 774
- `const current = wsRef.current` — const, line 775
- `const id = deskIdRef.current` — const, line 776
- `const focus = focusIdRef.current` — const, line 778
- `const step = focusPane(current, id, action.direction)` — const, line 784
- `const sel = overviewRef.current ? selectionRef.current : null` — const, line 790
- `const each = deskById(current, sel.deskId)` — const, line 792
- `const index = each ? slotIndexOf(each, sel.windowId) : -1` — const, line 793
- `const sel = selectionRef.current` — const, line 801
- `const row = current.desks.findIndex((each)` — const, line 803
- `const to = current.desks[row + action.direction]` — const, line 804
- `const from = current.desks[row]` — const, line 805
- `const index = slotIndexOf(from, sel.windowId)` — const, line 807
- `const afterSlot = to.slots[Math.min(index, to.slots.length) - 1]` — const, line 808
- `const sel = selectionRef.current` — const, line 820
- `const title = titleOf(current.windows[focus])` — const, line 844
- `const window = current.windows[focus]` — const, line 859
- `const zoom = typeof window?.view?.zoom === "number" ? (window.view.zoom as number) : 1` — const, line 860
- `const next = stepZoom(zoom, action.direction)` — const, line 861
- `const desk = deskById(current, id)` — const, line 867
- `const index = slotIndexOf(desk, focus)` — const, line 869
- `const shown = visibilityRef.current.filter((slot)` — const, line 870
- `const other = shown.find((slot)` — const, line 871
- `const toggle = focus ? media.current.get(focus) : undefined` — const, line 876
- `const visibilityRef = useRef(visibility)` — const, line 885
- `const runRef = useRef(run)` — const, line 887
- `const modifiers = useMemo(()` — const, line 892
- `const altTracker = useMemo( ()` — const, line 893
- `const router = useMemo(()` — const, line 897
- `const current = wsRef.current` — const, line 901
- `const id = deskIdRef.current` — const, line 902
- `const owner = current.windows[windowId]` — const, line 904
- `const outcome = altTracker.release(event)` — const, line 930
- `const open = claimed.current.get(focusIdRef.current ?? "")` — const, line 939
- `const has = (scope: ClaimedScope)` — const, line 940
- `const resolution = resolveKey(event,` — const, line 941
- `const claimed = useRef(new Map<string, Map<ClaimedScope, Set<string>>>())` — const, line 964
- `const claimsByWindow = useRef(new Map<string, ScopeClaims>())` — const, line 965
- `const claimsFor = useCallback((windowId: string): ScopeClaims` — const, line 966
- `let claims = claimsByWindow.current.get(windowId)` — let, line 967
- `const byScope = claimed.current.get(windowId) ?? new Map<ClaimedScope, Set<string>>()` — const, line 971
- `const owners = byScope.get(scope) ?? new Set<string>()` — const, line 972
- `const hubs = useRef(new Map<string, ListenerHub>())` — const, line 983
- `const hubFor = useCallback((windowId: string): ListenerHub` — const, line 984
- `let hub = hubs.current.get(windowId)` — let, line 985
- `const world = worldRef.current` — const, line 997
- `const mainRef = useRef<HTMLElement | null>(null)` — const, line 1002
- `const gesture = useRef<` — const, line 1003
- `const endGesture = useCallback(()` — const, line 1004
- `const g = gesture.current` — const, line 1005
- `const current = wsRef.current` — const, line 1015
- `const id = deskIdRef.current` — const, line 1016
- `const each = id ? deskById(current, id) : null` — const, line 1017
- `const st = stageNow.current` — const, line 1019
- `const rects = slotRects(each.slots.length, st)` — const, line 1020
- `const cam = camXRef.current[id] ?? 0` — const, line 1021
- `let best = 0` — let, line 1022
- `const snapped = ensureVisible(rects[best].x - DESK_SIZES.side, best, each.slots.length, st)` — const, line 1026
- `const target = each.slots[best].find((windowId)` — const, line 1028
- `const main = mainRef.current` — const, line 1034
- `const onWheel = (event: WheelEvent)` — const, line 1036
- `const target = event.target as Element | null` — const, line 1037
- `const st = stageNow.current` — const, line 1039
- `const now = performance.now()` — const, line 1040
- `let g = gesture.current` — let, line 1041
- `const kind = classifyWheel(event, modifiers.read(event), st.height)` — const, line 1043
- `const ovPlain = overviewRef.current && kind.kind !== "zoom"` — const, line 1045
- `const id = deskIdRef.current` — const, line 1071
- `const each = id ? deskById(wsRef.current, id) : null` — const, line 1072
- `const travel = Math.abs(dx) > Math.abs(dy) ? dx : dy` — const, line 1074
- `const max = Math.max(0, slotRects(each.slots.length, st).reduce((end, rect)` — const, line 1075
- `const result = zoomWheel(g.zoom, dy, now,` — const, line 1085
- `const stepped = result.step` — const, line 1087
- `const began = overviewRef.current ? beginLeave(selectionRef.current ?` — const, line 1089
- `const began = stepped.goal === 1 ? beginEnter() : beginLeave(selectionRef.current ?` — const, line 1095
- `const how = g.source === "pinch" ? "pinch" : modifiers.read(event).alt ? "alt + scroll" : "ctrl + scroll"` — const, line 1101
- `const drag = useRef<` — const, line 1115
- `const onStagePointerDown = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1116
- `const target = event.target as Element` — const, line 1117
- `const onCard = target.closest("[data-desk-slot]")` — const, line 1118
- `const inContent = target.closest(".desk-slot-inner, .desk-sliver, button, input, textarea")` — const, line 1119
- `const key = onCard.getAttribute("data-desk-slot-key") ?? undefined` — const, line 1122
- `const windowId = onCard.getAttribute("data-desk-slot-window") ?? undefined` — const, line 1123
- `const deskOf = onCard.getAttribute("data-desk-slot-desk") ?? undefined` — const, line 1124
- `const onStagePointerMove = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1138
- `const d = drag.current` — const, line 1139
- `const dx = event.clientX - d.x` — const, line 1141
- `const dy = event.clientY - d.y` — const, line 1142
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1161
- `const onStagePointerUp = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1167
- `const d = drag.current` — const, line 1168
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1177
- `const layout = ovLayoutRef.current` — const, line 1188
- `const stageBox = (event.currentTarget as HTMLElement).getBoundingClientRect()` — const, line 1189
- `const point =` — const, line 1191
- `const drop = dropTarget(layout, point)` — const, line 1192
- `const current = wsRef.current` — const, line 1193
- `const to = drop ? current.desks[drop.row] : null` — const, line 1194
- `const from = slotIndexOf(to, d.windowId)` — const, line 1197
- `const afterSlot = to.slots[drop.slot - 1]` — const, line 1200
- `const handle = timers.set(()` — const, line 1209
- `const body = [...document.querySelectorAll<HTMLElement>("[data-desk-window]")].find((pane)` — const, line 1211
- `const node = miniatures.get(windowId)` — const, line 1221
- `const node = host.firstElementChild as HTMLElement | null` — const, line 1224
- `const openContent = useCallback((content: ContentRefDto, options:` — const, line 1244
- `const current = wsRef.current` — const, line 1245
- `const id = deskIdRef.current` — const, line 1246
- `const step = openBeside(current, id, content, ()` — const, line 1248
- `const jump = jumps.current.get(step.windowId)` — const, line 1255
- `const handle = timers.set(()` — const, line 1261
- `const next = new Set(now)` — const, line 1264
- `const openHit = useCallback((hit:` — const, line 1274
- `const card = library?.find((entry)` — const, line 1276
- `const kind = card && isVideoCard(card) ? "video" : "source"` — const, line 1277
- `const viewTimers = useRef(new Map<string,` — const, line 1283
- `const shellTimers = useRef(new Set<unknown>())` — const, line 1284
- `const statusFor = useMemo(()` — const, line 1296
- `const onStatusFor = useCallback((windowId: string)` — const, line 1297
- `let handler = statusFor.get(windowId)` — let, line 1298
- `const previous = viewTimers.current.get(windowId)` — const, line 1307
- `const save = ()` — const, line 1309
- `const current = store.ws` — const, line 1310
- `const window = current.windows[windowId]` — const, line 1311
- `const jumpReadyFor = useMemo(()` — const, line 1329
- `const onJumpReadyFor = useCallback((windowId: string)` — const, line 1330
- `let handler = jumpReadyFor.get(windowId)` — let, line 1331
- `const pending = pendingJump.current.get(windowId)` — const, line 1339
- `const mediaReadyFor = useMemo(()` — const, line 1350
- `const onMediaReadyFor = useCallback((windowId: string)` — const, line 1351
- `let handler = mediaReadyFor.get(windowId)` — let, line 1352
- `const railNodeFor = useMemo(()` — const, line 1363
- `const onRailNode = useCallback((windowId: string)` — const, line 1364
- `let handler = railNodeFor.get(windowId)` — let, line 1365
- `const railPanelOf = useCallback((deskOf: string, extractionId: string): string | null` — const, line 1374
- `const desk = deskById(ws, deskOf)` — const, line 1376
- `const panels = desk.slots.flat().filter((id)` — const, line 1378
- `const content = ws.windows[id]?.content` — const, line 1379
- `const claimed = railClaims[`$` — const, line 1382
- `const sourceWindowOf = useCallback((deskOf: string, extractionId: string): string | null` — const, line 1386
- `const desk = deskById(ws, deskOf)` — const, line 1388
- `const content = ws.windows[id]?.content` — const, line 1391
- `const undoShown = undo && undo.deskId === deskId && undo.until > timers.now() && (ws?.closed[undo.deskId] ?? []).some((entry)` — const, line 1399
- `const handle = timers.set(()` — const, line 1403
- `const paneBody = (window: DeskWindow, lifecycle: WindowLifecycle): ReactNode` — const, line 1417
- `const content = window.content` — const, line 1418
- `const card = content && (content.kind === "source" || content.kind === "video") ? library?.find((entry)` — const, line 1419
- `const railPanel = railPanelOf(window.deskId, content.extractionId)` — const, line 1425
- `const railNode = railPanel ? railHosts[railPanel] ?? null : null` — const, line 1426
- `const railContent = railPanel ? ws.windows[railPanel]?.content : null` — const, line 1427
- `const railTab = railContent?.kind === "panel" && railContent.panel === "notes" ? "notes" : "guide"` — const, line 1428
- `const extractionId = content.extractionId ?? ""` — const, line 1446
- `const owner = railPanelOf(window.deskId, extractionId)` — const, line 1447
- `const target = content.extractionId ? sourceWindowOf(window.deskId, content.extractionId) : null` — const, line 1464
- `const jump = jumps.current.get(target)` — const, line 1467
- `const linkedFrom = overview || zooming ? selection?.windowId ?? focusId : null` — const, line 1483
- `const selectedRelations = relatedTo(linkedFrom)` — const, line 1484
- `const linkRects = new Map<string, Rect>()` — const, line 1485
- `const rect = ovLayout?.cards[row]?.[index]` — const, line 1487
- `const fromCard = linkedFrom ? linkRects.get(linkedFrom) ?? null : null` — const, line 1490
- `const links = fromCard ? curvedLinks(fromCard, selectedRelations.filter((relation)` — const, line 1491
- `const ghosts: Array<` — const, line 1494
- `const row = ws.desks.findIndex((each)` — const, line 1496
- `const each = ws.desks[row]` — const, line 1497
- `const sameDesk = selectedRelations.filter((relation)` — const, line 1499
- `const linked = slot.some((id)` — const, line 1503
- `const movedShown = movedNotice && movedNotice.deskId === deskId && movedNotice.until > timers.now() ? movedNotice : null` — const, line 1508
- `const focusWindow = focusId ? ws.windows[focusId] : undefined` — const, line 1509
- `const focusZoom = typeof focusWindow?.view?.zoom === "number" ? (focusWindow.view.zoom as number) : 1` — const, line 1510
- `const windowPlaces = ws.desks.flatMap((each, rowIndex)` — const, line 1513
- `const eachCam = camX[each.deskId] ?? 0` — const, line 1514
- `const rects = slotRects(each.slots.length, stage)` — const, line 1515
- `const top = rowTop(rowIndex, stage) - rowTop(deskIndex, stage)` — const, line 1516
- `const slotReading =` — const, line 1518
- `const slotCard = ovLayout?.cards[rowIndex]?.[index] ?? slotReading` — const, line 1519
- `const readingPanes = paneRects(slotReading, slot.length)` — const, line 1520
- `const cardPanes = paneRects(slotCard, slot.length)` — const, line 1521
- `const window = ws.windows[id]` — const, line 1523
- `const sliverDesk = leaveTarget ? deskById(ws, leaveTarget.deskId) : desk` — const, line 1530
- `const sliverCam = leaveTarget && sliverDesk ? leaveTarget.cams[sliverDesk.deskId] ?? 0 : cam` — const, line 1531
- `const slivers = sliverDesk && !focusMode ? sliverSlots(sliverCam, sliverDesk.slots.length, stage) :` — const, line 1532
- `const shelfRows: ShelfRow[] = desk ? desk.slots.flatMap((slot, index)` — const, line 1533
- `const window = ws.windows[id]` — const, line 1535
- `const kind = window?.kind ?? "source"` — const, line 1536
- `const hints = overview ? [["h j k l", "select"], ["↵ / click", "open"], ["alt+↵", "open in focus"], ["alt+[ ]", "move"], ["alt+shift+j/k", "to a desk"], ["drag", "move a card"], ["b", "relations"], ["g", "hold: gather"], ["o / esc", "back"]] : focusMode ? [["…` — const, line 1550
- `const title = (event.target as HTMLInputElement).value.trim()` — const, line 1571
- `const id = mintId("desk")` — const, line 1597
- `const id = window.windowId` — const, line 1640
- `const onCurrent = each.deskId === deskId` — const, line 1641
- `const opened = visited.has(each.deskId) || onCurrent` — const, line 1642
- `const full = !overview && onCurrent && focusMode && id === focusId` — const, line 1643
- `const hiddenInFocus = !overview && onCurrent && focusMode && !full` — const, line 1644
- `const reading = full ?` — const, line 1645
- `const card = place.card` — const, line 1646
- `const box = overview ? card : reading` — const, line 1647
- `const leavingTo = leaveTarget?.deskId === each.deskId` — const, line 1648
- `const slotCut = leavingTo ? slotVisibility(leaveTarget.cams[each.deskId] ?? 0, each.slots.length, stage)[index] : onCurrent ? visibility[index] : null` — const, line 1649
- `const mask = full || focusMode || !slotCut ? null : leavingTo || (!overview && !zooming && onCurrent) ? softCropMask(slotCut, reading.w) : null` — const, line 1652
- `const lifecycle = lifecycles[id] ??` — const, line 1653
- `const paused = isPaused(lifecycle.state)` — const, line 1654
- `const paired = slot.length > 1` — const, line 1655
- `const selected = overview && selection !== null && slot.includes(selection.windowId)` — const, line 1656
- `const receding = overview && recedes(slot, selection?.windowId ?? null, selectedRelations, showRelations)` — const, line 1657
- `const measure = FOCUS_MEASURE[window.kind] ?? FOCUS_MEASURE.source` — const, line 1658
- `const title = titleOf(window)` — const, line 1712
- `const ringId = linkedFrom` — const, line 1794
- `const isSel = ringId !== null && slot.includes(ringId)` — const, line 1795
- `const isRel = !isSel && showRelations && slot.some((id)` — const, line 1796
- `const rect = ovLayout?.cards[rowIndex]?.[index]` — const, line 1797
- `const key = slotKey(each.deskId, slot)` — const, line 1799
- `function Sliver(` — function, line 1899
- `function WhichKey()` — function, line 1909
- `const groups: Array<` — const, line 1910
- `const rows = DESK_BINDINGS.filter((binding)` — const, line 1921
- `function OpenBeside(` — function, line 1939
- `const words = filter.trim().toLowerCase()` — const, line 1955
- `const sources = (library ?? []).filter((card)` — const, line 1956
- `const book = focus?.content && (focus.content.kind === "source" || focus.content.kind === "video") ? focus.content : null` — const, line 1957

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: dynamic import; no named call claim
- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `DeskDebugHandle`, `DeskShell`; references `DeskDebugHandle`, `DeskShell`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ContentRefDto`, `DeskApplyDto`, `DeskApplyInput`, `DeskStateDto`, `SourceLibraryCard`
- [[Reference/Desktop/TypeScript/api/poller|src/api/poller.ts]] — import-or-re-export; imports `poller`
- [[Reference/Desktop/TypeScript/app/ScreenErrorBoundary|src/app/ScreenErrorBoundary.tsx]] — import-or-re-export; imports `ScreenErrorBoundary`
- [[Reference/Desktop/TypeScript/screens/desks/Shelf|src/screens/desks/Shelf.tsx]] — import-or-re-export; imports `Shelf`, `ShelfRow`
- [[Reference/Desktop/TypeScript/screens/desks/geometry|src/screens/desks/geometry.ts]] — import-or-re-export; imports `DESK_SIZES`, `FOCUS_MEASURE`, `Rect`, `Stage`, `ensureVisible`, `paneRects`, `rowTop`, `sliverSlots`, `slotRects`, `slotVisibility`, `slotWidth`, `softCropMask`, `stepZoom`
- [[Reference/Desktop/TypeScript/screens/desks/keys/listeners|src/screens/desks/keys/listeners.ts]] — import-or-re-export; imports `DeskListenerRouter`, `WINDOW_ATTRIBUTE`, `windowOfTarget`
- [[Reference/Desktop/TypeScript/screens/desks/keys/router|src/screens/desks/keys/router.ts]] — import-or-re-export; imports `BareAltTracker`, `DESK_BINDINGS`, `DeskAction`, `ModifierTracker`, `REAL_TIMERS`, `Timers`, `isTypingTarget`, `resolveKey`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `ClaimedScope`, `ListenerHub`, `ScopeClaims`, `WindowLifecycle`, `WindowScope`, `isPaused`, `windowState`
- [[Reference/Desktop/TypeScript/screens/desks/model/workspace|src/screens/desks/model/workspace.ts]] — import-or-re-export; imports `DeskWindow`, `Step`, `Workspace`, `closeWindow`, `createDesk`, `deskById`, `focusAlong`, `focusPane`, `focusedSlot`, `focusedWindowId`, `moveFocused`, `moveToDesk`, `moveWindowTo`, `openBeside`, `pairFocused`, `renameDesk`, `reorderSlots`, `setFocus`, `setView`, `slotIndexOf`, `swapInView`, `undoClose`, `unpairFocused`
- [[Reference/Desktop/TypeScript/screens/desks/outbox|src/screens/desks/outbox.ts]] — import-or-re-export; imports `OutboxTransport`, `clientIdFor`
- [[Reference/Desktop/TypeScript/screens/desks/overview/Card|src/screens/desks/overview/Card.tsx]] — import-or-re-export; imports `CardFace`, `LinkLayer`
- [[Reference/Desktop/TypeScript/screens/desks/overview/controller|src/screens/desks/overview/controller.ts]] — import-or-re-export; imports `ANIMATION_FRAMES`, `FrameClock`, `SlotElements`, `ZoomController`, `ZoomPlan`, `cameraTransform`
- [[Reference/Desktop/TypeScript/screens/desks/overview/engine|src/screens/desks/overview/engine.ts]] — import-or-re-export; imports `Camera`, `IDENTITY`, `OVERVIEW`, `ZoomGesture`, `ZoomSource`, `classifyWheel`, `dragProgress`, `dropTarget`, `enteringCamera`, `followSelection`, `moveSelection`, `newZoomGesture`, `normalizedDelta`, `overviewLayout`, `zoomWheel`
- [[Reference/Desktop/TypeScript/screens/desks/overview/links|src/screens/desks/overview/links.ts]] — import-or-re-export; imports `DRAWN_RELATIONS`, `Relation`, `curvedLinks`, `gatherOrder`, `relationsOf`
- [[Reference/Desktop/TypeScript/screens/desks/overview/miniature|src/screens/desks/overview/miniature.ts]] — import-or-re-export; imports `MiniatureBook`, `cloneForMiniature`
- [[Reference/Desktop/TypeScript/screens/desks/store|src/screens/desks/store.ts]] — import-or-re-export; imports `deskStoreFor`
- [[Reference/Desktop/TypeScript/screens/desks/windows/PanelWindow|src/screens/desks/windows/PanelWindow.tsx]] — import-or-re-export; imports `LibraryPanel`, `PANEL_TITLES`, `PathPanel`, `RailHostPanel`
- [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] — import-or-re-export; imports `ReaderPassThrough`, `SourceStatus`, `SourceWindow`
- [[Reference/Desktop/TypeScript/screens/reader/readerCache|src/screens/reader/readerCache.ts]] — import-or-re-export; imports `cachedSourceRead`

### Assets, platform, and third-party dependencies

- Local asset: [apps/learnloop-tauri/src/styles/desk.css](../../../../../../../apps/learnloop-tauri/src/styles/desk.css)
- Imported packages/crates: `@fontsource-variable/caveat`, `@fontsource-variable/inter`, `@fontsource-variable/jetbrains-mono`, `@fontsource-variable/literata`, `@fontsource-variable/literata/wght-italic.css`, `@fontsource-variable/source-serif-4`, `@fontsource-variable/source-serif-4/wght-italic.css`, `react`, `react-dom`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/DeskShell.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/DeskShell.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/DeskShell.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/DeskShell.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

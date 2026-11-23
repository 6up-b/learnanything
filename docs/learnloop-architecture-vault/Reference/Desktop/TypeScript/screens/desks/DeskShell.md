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
| Source lines | 2167 |
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

- `export interface DeskTransport extends OutboxTransport` — interface, line 104
- `export const LIVE_DESK_TRANSPORT: DeskTransport =` — const, line 111
- `export interface PaneRenderInput` — interface, line 121
- `export interface DeskDebugHandle` — interface, line 137
- `export const KIND_GLYPH: Record<string, string> =` — const, line 172
- `export interface DeskShellProps` — interface, line 225
- `export function DeskShell(` — function, line 248
- `export function isVideoCard(card: SourceLibraryCard): boolean` — function, line 2047
- `export function contentForCard(card: SourceLibraryCard, extractionId: string): ContentRefDto` — function, line 2051

## Internal implementation anchors

- `type DeskWindow, type Step, type Workspace, } from "./model/workspace"` — type, line 35
- `type Step, type Workspace, } from "./model/workspace"` — type, line 36
- `type Workspace, } from "./model/workspace"` — type, line 37
- `type Rect, type Stage, } from "./geometry"` — type, line 51
- `type Stage, } from "./geometry"` — type, line 52
- `type Camera, type ZoomGesture, type ZoomSource, } from "./overview/engine"` — type, line 67
- `type ZoomGesture, type ZoomSource, } from "./overview/engine"` — type, line 68
- `type ZoomSource, } from "./overview/engine"` — type, line 69
- `type DeskAction, type Timers, } from "./keys/router"` — type, line 82
- `type Timers, } from "./keys/router"` — type, line 83
- `const UNDO_CLOSE_MS = 9_000` — const, line 128
- `const TOAST_MS = 2_200` — const, line 130
- `const VIEW_SAVE_IDLE_MS = 2_000` — const, line 132
- `const MOVED_NOTICE_MS = 6_000` — const, line 134
- `function displayedCamera(world: HTMLElement): Camera | null` — function, line 147
- `const shown = typeof getComputedStyle === "function" ? getComputedStyle(world).transform : ""` — const, line 148
- `const match = /^matrix\(([^)]+)\)$/.exec(shown ?? "")` — const, line 149
- `function prefersReducedMotion(): boolean` — function, line 155
- `function slotKey(deskId: string, slot: string[]): string` — function, line 164
- `function intersects(rect: Rect, stage: Stage): boolean` — function, line 168
- `const KIND_WORD: Record<string, string> =` — const, line 184
- `function defaultMintId(prefix: string): string` — function, line 196
- `function shortName(title: string): string` — function, line 204
- `const words = title.split(/\s+/).filter(Boolean)` — const, line 205
- `function readStored(key: string): string | null` — function, line 209
- `function writeStored(key: string, value: string): void` — function, line 217
- `const store = useMemo( ()` — const, line 265
- `const storeWs = useSyncExternalStore(store.subscribe, store.getSnapshot)` — const, line 269
- `const ws: Workspace | null = storeReady ? storeWs : null` — const, line 271
- `const wsRef = useMemo(()` — const, line 272
- `const deskKey = `learnloop.desks.current.$` — const, line 274
- `const stageRef = useRef<HTMLElement | null>(null)` — const, line 289
- `const viewport = initialViewport ??` — const, line 291
- `const shelf = viewport.width < DESK_SIZES.shelfFoldBelow ? DESK_SIZES.shelfRail : DESK_SIZES.shelf` — const, line 292
- `const preOverview = useRef<` — const, line 312
- `const worldRef = useRef<HTMLDivElement | null>(null)` — const, line 313
- `const boxEls = useRef(new Map<string, HTMLElement>())` — const, line 316
- `const innerEls = useRef(new Map<string, HTMLElement>())` — const, line 317
- `const cardEls = useRef(new Map<string, HTMLElement>())` — const, line 318
- `const ringEls = useRef(new Map<string, HTMLElement>())` — const, line 319
- `const slotElements = useCallback((): Map<string, SlotElements>` — const, line 320
- `const out = new Map<string, SlotElements>()` — const, line 321
- `const lateEls = useRef(new Map<string, HTMLElement>())` — const, line 325
- `const sliverEls = useRef(new Map<string, HTMLElement>())` — const, line 326
- `const miniatures = useMemo(()` — const, line 327
- `const miniHosts = useRef(new Map<string, HTMLDivElement>())` — const, line 328
- `const onEndRef = useRef<(goal: 0 | 1, base: 0 | 1)` — const, line 329
- `const controller = useMemo(()` — const, line 330
- `const jumps = useRef(new Map<string, (spanId: string)` — const, line 331
- `const media = useRef(new Map<string, ()` — const, line 332
- `const pendingJump = useRef(new Map<string, string>())` — const, line 333
- `const toastNow = useCallback((text: string)` — const, line 335
- `const handle = timers.set(()` — const, line 338
- `const setCurrentDeskId = useCallback((deskId: string | null)` — const, line 344
- `const commit = useCallback((step: Step)` — const, line 349
- `const total = notice.dropped + notice.lost` — const, line 358
- `const chain = useCallback((first: Step, next: (ws: Workspace)` — const, line 364
- `const second = next(first.ws)` — const, line 365
- `const firstRun = useCallback(async (base: Workspace, cards: SourceLibraryCard[] | null): Promise<Step>` — const, line 369
- `const card = firstSourceId ? cards?.find((entry)` — const, line 370
- `const deskId = mintId("desk")` — const, line 371
- `const created = createDesk(base, deskId, card ? `new desk · $` — const, line 372
- `const extractionId = await transport.resolveExtraction(card.sourceId).catch(()` — const, line 374
- `let live = true` — let, line 380
- `const desk = ws ? deskById(ws, currentDeskId) ?? ws.desks[0] ?? null : null` — const, line 402
- `const deskId = desk?.deskId ?? null` — const, line 403
- `const focusId = ws && desk ? focusedWindowId(ws, desk) : null` — const, line 404
- `const focusSlotIndex = ws && desk ? focusedSlot(ws, desk) : -1` — const, line 405
- `const slotCount = desk?.slots.length ?? 0` — const, line 413
- `const keepPrevious = useRef(false)` — const, line 414
- `const next = ensureVisible(cams[deskId] ?? 0, focusSlotIndex, slotCount, stage, keepPrevious.current)` — const, line 418
- `const node = stageRef.current` — const, line 426
- `const measure = ()` — const, line 427
- `const next =` — const, line 429
- `const now = stageNow.current` — const, line 430
- `const shell = node?.closest(".desk-shell") as HTMLElement | null` — const, line 437
- `const observer = typeof ResizeObserver === "undefined" || !node ? null : new ResizeObserver(measure)` — const, line 441
- `const cam = deskId ? camX[deskId] ?? 0 : 0` — const, line 450
- `const visibility = useMemo(()` — const, line 451
- `const deskIndex = ws && desk ? ws.desks.indexOf(desk) : 0` — const, line 452
- `const lifecycles = useMemo(()` — const, line 456
- `const out: Record<string, WindowLifecycle> =` — const, line 457
- `const onCurrent = each.deskId === deskId` — const, line 460
- `const activeWindowId = Object.values(lifecycles).find((each)` — const, line 476
- `const held = document.activeElement` — const, line 478
- `const owner = held && held !== document.body ? windowOfTarget(held) : null` — const, line 479
- `const target = activeWindowId ? document.querySelector<HTMLElement>(`[$` — const, line 481
- `const lifecyclesRef = useRef(lifecycles)` — const, line 487
- `const focusIdRef = useRef(focusId)` — const, line 489
- `const focusModeRef = useRef(focusMode)` — const, line 497
- `const switchDesk = useCallback((direction: -1 | 1): boolean` — const, line 500
- `const current = wsRef.current` — const, line 501
- `const index = current.desks.findIndex((each)` — const, line 502
- `const next = current.desks[index + direction]` — const, line 503
- `const deskIdRef = useRef(deskId)` — const, line 508
- `const titleOf = useCallback((window: DeskWindow | undefined): string` — const, line 511
- `const known = status[window.windowId]?.title` — const, line 513
- `const content = window.content` — const, line 515
- `const ovLayout = useMemo(()` — const, line 525
- `const ovLayoutRef = useRef(ovLayout)` — const, line 526
- `const stageNow = useRef(stage)` — const, line 528
- `const camXRef = useRef(camX)` — const, line 530
- `const overviewRef = useRef(overview)` — const, line 532
- `const ovCamRef = useRef(ovCam)` — const, line 534
- `const selectionRef = useRef(selection)` — const, line 536
- `const visitedRef = useRef(visited)` — const, line 538
- `const showRelationsRef = useRef(showRelations)` — const, line 540
- `const reduced = reducedMotion ?? prefersReducedMotion()` — const, line 542
- `const transitionGen = useRef(0)` — const, line 545
- `const panEaseRef = useRef(panEase)` — const, line 546
- `const pendingLeave = useRef<` — const, line 548
- `const cardOf = useCallback((windowId: string | null | undefined): Rect | null` — const, line 551
- `const layout = ovLayoutRef.current` — const, line 552
- `const current = wsRef.current` — const, line 553
- `const index = slotIndexOf(each, windowId)` — const, line 556
- `const readingRectOf = useCallback((current: Workspace, row: number, index: number, readingRow: number, cams: Record<string, number>, st: Stage): Rect` — const, line 564
- `const each = current.desks[row]` — const, line 565
- `const rect = slotRects(each.slots.length, st)[index]` — const, line 566
- `const relatedTo = useCallback((windowId: string | null | undefined): Relation[]` — const, line 570
- `const recedes = useCallback((slot: string[], selected: string | null, related: Relation[], relationsOn: boolean): boolean` — const, line 573
- `const planZoom = useCallback((base: 0 | 1, readingDeskId: string, cams: Record<string, number>, selected: string | null, B: Camera, fullWindowId: string | null = null): ZoomPlan | null` — const, line 578
- `const current = wsRef.current` — const, line 579
- `const layout = ovLayoutRef.current` — const, line 580
- `const st = stageNow.current` — const, line 581
- `const readingRow = Math.max(0, current.desks.findIndex((each)` — const, line 583
- `const related = relatedTo(selected)` — const, line 584
- `const items: ZoomPlan["items"] = []` — const, line 585
- `const rings: ZoomPlan["rings"] = []` — const, line 586
- `const a = readingRectOf(current, row, index, readingRow, cams, st)` — const, line 588
- `const b = layout.cards[row][index]` — const, line 589
- `const readingPanes = paneRects(a, slot.length)` — const, line 590
- `const cardPanes = paneRects(b, slot.length)` — const, line 591
- `const live = visitedRef.current.has(each.deskId) && each.deskId === readingDeskId && intersects(a, st)` — const, line 592
- `const recede = recedes(slot, selected, related, showRelationsRef.current)` — const, line 593
- `const focus = selected !== null && slot.includes(selected)` — const, line 594
- `const isRelated = showRelationsRef.current && slot.some((id)` — const, line 595
- `const pa = id === fullWindowId && each.deskId === readingDeskId ?` — const, line 598
- `const pb = cardPanes[pane]` — const, line 599
- `const zoomTargets = useCallback(()` — const, line 607
- `const crossfade = useCallback((enter: boolean, to:` — const, line 618
- `const world = worldRef.current` — const, line 620
- `const id = deskIdRef.current` — const, line 626
- `const target = to ?? (preOverview.current ?` — const, line 635
- `const beginEnter = useCallback((): boolean` — const, line 646
- `const id = deskIdRef.current` — const, line 648
- `const selected = focusIdRef.current` — const, line 656
- `const B = enteringCamera(cardOf(selected), stageNow.current)` — const, line 658
- `const plan = planZoom(0, id, camXRef.current, selected, B)` — const, line 663
- `const beginLeave = useCallback((to:` — const, line 671
- `const shown = displayedCamera(worldRef.current) ?? ovCamRef.current` — const, line 681
- `const target = to ?? preOverview.current ?? (selectionRef.current ?` — const, line 687
- `const deskIdTo = target.deskId` — const, line 689
- `const windowTo = "windowId" in target ? target.windowId : target.focusId` — const, line 690
- `const current = wsRef.current` — const, line 691
- `const each = deskById(current, deskIdTo)` — const, line 692
- `const fullWindowId = focusAfter && windowTo ? windowTo : null` — const, line 694
- `const node = stageRef.current` — const, line 703
- `const cams =` — const, line 707
- `const index = windowTo ? slotIndexOf(each, windowTo) : -1` — const, line 708
- `const plan = planZoom(1, deskIdTo, cams, windowTo, ovCamRef.current, fullWindowId)` — const, line 710
- `const plan = controller.plan` — const, line 726
- `const leave = pendingLeave.current` — const, line 744
- `const generation = transitionGen.current` — const, line 758
- `const toggleOverview = useCallback((to:` — const, line 767
- `const focusWindow = focusId ? ws.windows[focusId] : null` — const, line 784
- `const first = ws.desks.find((each)` — const, line 789
- `const windowId = first ? first.slots[0].find((id)` — const, line 790
- `const followMoved = useRef(false)` — const, line 794
- `const rect = cardOf(selection.windowId)` — const, line 798
- `const moveOverviewSelection = useCallback((direction: "left" | "right" | "up" | "down")` — const, line 805
- `const layout = ovLayoutRef.current` — const, line 806
- `const current = wsRef.current` — const, line 807
- `const sel = selectionRef.current` — const, line 808
- `let row = sel ? current.desks.findIndex((each)` — let, line 810
- `let slot = sel ? slotIndexOf(current.desks[row] ?? current.desks[0], sel.windowId) : 0` — let, line 811
- `const next = moveSelection(layout,` — const, line 816
- `const each = current.desks[next.row]` — const, line 817
- `const windowId = each?.slots[next.slot]?.find((id)` — const, line 818
- `const gather = useCallback((toNewDesk: boolean)` — const, line 826
- `const current = wsRef.current` — const, line 827
- `const id = deskIdRef.current` — const, line 828
- `const focus = focusIdRef.current` — const, line 829
- `const each = id ? deskById(current, id) : null` — const, line 830
- `const related = relationsOf(current, focus).filter((relation)` — const, line 837
- `const moving = [focus, ...related.slice(0, DRAWN_RELATIONS).map((relation)` — const, line 850
- `const newDeskId = mintId("desk")` — const, line 851
- `const title = `gathered · $` — const, line 852
- `let step = createDesk(current, newDeskId, title)` — let, line 853
- `let after: string | null = null` — let, line 854
- `const next = moveToDesk(step.ws, id, windowId, newDeskId, after)` — const, line 856
- `const focused = setFocus(step.ws, newDeskId, focus)` — const, line 860
- `const run = useCallback((action: DeskAction): boolean` — const, line 868
- `const current = wsRef.current` — const, line 869
- `const id = deskIdRef.current` — const, line 870
- `const focus = focusIdRef.current` — const, line 872
- `const step = focusPane(current, id, action.direction)` — const, line 878
- `const sel = overviewRef.current ? selectionRef.current : null` — const, line 884
- `const each = deskById(current, sel.deskId)` — const, line 886
- `const index = each ? slotIndexOf(each, sel.windowId) : -1` — const, line 887
- `const sel = selectionRef.current` — const, line 898
- `const row = current.desks.findIndex((each)` — const, line 900
- `const to = current.desks[row + action.direction]` — const, line 901
- `const from = current.desks[row]` — const, line 902
- `const index = slotIndexOf(from, sel.windowId)` — const, line 904
- `const sel = selectionRef.current` — const, line 917
- `const title = titleOf(current.windows[focus])` — const, line 941
- `const window = current.windows[focus]` — const, line 956
- `const zoom = typeof window?.view?.zoom === "number" ? (window.view.zoom as number) : 1` — const, line 957
- `const next = stepZoom(zoom, action.direction)` — const, line 958
- `const desk = deskById(current, id)` — const, line 964
- `const index = slotIndexOf(desk, focus)` — const, line 966
- `const shown = visibilityRef.current.filter((slot)` — const, line 967
- `const other = shown.find((slot)` — const, line 968
- `const toggle = focus ? media.current.get(focus) : undefined` — const, line 973
- `const visibilityRef = useRef(visibility)` — const, line 982
- `const runRef = useRef(run)` — const, line 984
- `const modifiers = useMemo(()` — const, line 989
- `const altTracker = useMemo( ()` — const, line 990
- `const router = useMemo(()` — const, line 994
- `const current = wsRef.current` — const, line 999
- `const id = deskIdRef.current` — const, line 1000
- `const owner = current.windows[windowId]` — const, line 1002
- `const outcome = altTracker.release(event)` — const, line 1030
- `const open = claimed.current.get(focusIdRef.current ?? "")` — const, line 1039
- `const has = (scope: ClaimedScope)` — const, line 1040
- `const resolution = resolveKey(event,` — const, line 1041
- `const claimed = useRef(new Map<string, Map<ClaimedScope, Set<string>>>())` — const, line 1064
- `const claimsByWindow = useRef(new Map<string, ScopeClaims>())` — const, line 1065
- `const claimsFor = useCallback((windowId: string): ScopeClaims` — const, line 1066
- `let claims = claimsByWindow.current.get(windowId)` — let, line 1067
- `const byScope = claimed.current.get(windowId) ?? new Map<ClaimedScope, Set<string>>()` — const, line 1071
- `const owners = byScope.get(scope) ?? new Set<string>()` — const, line 1072
- `const hubs = useRef(new Map<string, ListenerHub>())` — const, line 1083
- `const hubFor = useCallback((windowId: string): ListenerHub` — const, line 1084
- `let hub = hubs.current.get(windowId)` — let, line 1085
- `const world = worldRef.current` — const, line 1097
- `const mainRef = useRef<HTMLElement | null>(null)` — const, line 1102
- `const gesture = useRef<` — const, line 1103
- `const endGesture = useCallback(()` — const, line 1104
- `const g = gesture.current` — const, line 1105
- `const current = wsRef.current` — const, line 1115
- `const id = deskIdRef.current` — const, line 1116
- `const each = id ? deskById(current, id) : null` — const, line 1117
- `const st = stageNow.current` — const, line 1119
- `const rects = slotRects(each.slots.length, st)` — const, line 1120
- `const cam = camXRef.current[id] ?? 0` — const, line 1121
- `let best = 0` — let, line 1122
- `const snapped = ensureVisible(rects[best].x - DESK_SIZES.side, best, each.slots.length, st)` — const, line 1126
- `const target = each.slots[best].find((windowId)` — const, line 1128
- `const main = mainRef.current` — const, line 1134
- `const onWheel = (event: WheelEvent)` — const, line 1136
- `const target = event.target as Element | null` — const, line 1137
- `const st = stageNow.current` — const, line 1142
- `const now = performance.now()` — const, line 1143
- `let g = gesture.current` — let, line 1144
- `const kind = classifyWheel(event, modifiers.read(), st.height)` — const, line 1148
- `const ovPlain = overviewRef.current && kind.kind !== "zoom"` — const, line 1150
- `const id = deskIdRef.current` — const, line 1176
- `const each = id ? deskById(wsRef.current, id) : null` — const, line 1177
- `const travel = Math.abs(dx) > Math.abs(dy) ? dx : dy` — const, line 1179
- `const max = Math.max(0, slotRects(each.slots.length, st).reduce((end, rect)` — const, line 1180
- `const result = zoomWheel(g.zoom, dy, now,` — const, line 1190
- `const stepped = result.step` — const, line 1192
- `const began = overviewRef.current ? beginLeave(selectionRef.current ?` — const, line 1194
- `const began = stepped.goal === 1 ? beginEnter() : beginLeave(selectionRef.current ?` — const, line 1200
- `const how = g.source === "pinch" ? "pinch" : modifiers.read(event).alt ? "alt + scroll" : "ctrl + scroll"` — const, line 1206
- `const drag = useRef<` — const, line 1220
- `const onStagePointerDown = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1221
- `const target = event.target as Element` — const, line 1222
- `const onCard = target.closest("[data-desk-slot]")` — const, line 1223
- `const onSliver = target.closest(".desk-sliver") !== null` — const, line 1225
- `const inContent = !onSliver && target.closest(".desk-slot-inner, button, input, textarea") !== null` — const, line 1226
- `const key = onCard.getAttribute("data-desk-slot-key") ?? undefined` — const, line 1229
- `const windowId = onCard.getAttribute("data-desk-slot-window") ?? undefined` — const, line 1230
- `const deskOf = onCard.getAttribute("data-desk-slot-desk") ?? undefined` — const, line 1231
- `const onStagePointerMove = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1245
- `const d = drag.current` — const, line 1246
- `const dx = event.clientX - d.x` — const, line 1248
- `const dy = event.clientY - d.y` — const, line 1249
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1268
- `const cancelDrag = useCallback(()` — const, line 1276
- `const d = drag.current` — const, line 1277
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1285
- `const cancelDragRef = useRef(cancelDrag)` — const, line 1291
- `const scrubbedClick = useRef(false)` — const, line 1294
- `const onStagePointerUp = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1295
- `const d = drag.current` — const, line 1296
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1306
- `const layout = ovLayoutRef.current` — const, line 1317
- `const stageBox = (event.currentTarget as HTMLElement).getBoundingClientRect()` — const, line 1318
- `const point =` — const, line 1320
- `const drop = dropTarget(layout, point)` — const, line 1321
- `const current = wsRef.current` — const, line 1322
- `const to = drop ? current.desks[drop.row] : null` — const, line 1323
- `const from = slotIndexOf(to, d.windowId)` — const, line 1326
- `const world = worldRef.current` — const, line 1337
- `const observer = new MutationObserver((records)` — const, line 1339
- `const node = record.target instanceof Element ? record.target : record.target.parentElement` — const, line 1341
- `const windowId = windowOfTarget(node)` — const, line 1342
- `const handle = timers.set(()` — const, line 1355
- `const body = [...document.querySelectorAll<HTMLElement>("[data-desk-window]")].find((pane)` — const, line 1358
- `const node = miniatures.get(windowId)` — const, line 1368
- `const node = host.firstElementChild as HTMLElement | null` — const, line 1371
- `const openContent = useCallback((content: ContentRefDto, options:` — const, line 1391
- `const current = wsRef.current` — const, line 1392
- `const id = deskIdRef.current` — const, line 1393
- `const step = openBeside(current, id, content, ()` — const, line 1395
- `const jump = jumps.current.get(step.windowId)` — const, line 1402
- `const handle = timers.set(()` — const, line 1408
- `const next = new Set(now)` — const, line 1411
- `const openHit = useCallback((hit:` — const, line 1421
- `const card = library?.find((entry)` — const, line 1423
- `const kind = card && isVideoCard(card) ? "video" : "source"` — const, line 1424
- `const viewTimers = useRef(new Map<string,` — const, line 1430
- `const shellTimers = useRef(new Set<unknown>())` — const, line 1431
- `const statusFor = useMemo(()` — const, line 1443
- `const onStatusFor = useCallback((windowId: string)` — const, line 1444
- `let handler = statusFor.get(windowId)` — let, line 1445
- `const previous = viewTimers.current.get(windowId)` — const, line 1454
- `const save = ()` — const, line 1456
- `const current = store.ws` — const, line 1457
- `const window = current.windows[windowId]` — const, line 1458
- `const jumpReadyFor = useMemo(()` — const, line 1476
- `const onJumpReadyFor = useCallback((windowId: string)` — const, line 1477
- `let handler = jumpReadyFor.get(windowId)` — let, line 1478
- `const pending = pendingJump.current.get(windowId)` — const, line 1486
- `const mediaReadyFor = useMemo(()` — const, line 1497
- `const onMediaReadyFor = useCallback((windowId: string)` — const, line 1498
- `let handler = mediaReadyFor.get(windowId)` — let, line 1499
- `const railNodeFor = useMemo(()` — const, line 1510
- `const onRailNode = useCallback((windowId: string)` — const, line 1511
- `let handler = railNodeFor.get(windowId)` — let, line 1512
- `const railPanelOf = useCallback((deskOf: string, extractionId: string): string | null` — const, line 1521
- `const desk = deskById(ws, deskOf)` — const, line 1523
- `const panels = desk.slots.flat().filter((id)` — const, line 1525
- `const content = ws.windows[id]?.content` — const, line 1526
- `const claimed = railClaims[`$` — const, line 1529
- `const sourceWindowOf = useCallback((deskOf: string, extractionId: string): string | null` — const, line 1533
- `const desk = deskById(ws, deskOf)` — const, line 1535
- `const content = ws.windows[id]?.content` — const, line 1538
- `const undoShown = undo && undo.deskId === deskId && undo.until > timers.now() && (ws?.closed[undo.deskId] ?? []).some((entry)` — const, line 1546
- `const handle = timers.set(()` — const, line 1550
- `const paneBody = (window: DeskWindow, lifecycle: WindowLifecycle): ReactNode` — const, line 1564
- `const content = window.content` — const, line 1565
- `const card = content && (content.kind === "source" || content.kind === "video") ? library?.find((entry)` — const, line 1566
- `const railPanel = railPanelOf(window.deskId, content.extractionId)` — const, line 1572
- `const railNode = railPanel ? railHosts[railPanel] ?? null : null` — const, line 1573
- `const railContent = railPanel ? ws.windows[railPanel]?.content : null` — const, line 1574
- `const railTab = railContent?.kind === "panel" && railContent.panel === "notes" ? "notes" : "guide"` — const, line 1575
- `const extractionId = content.extractionId ?? ""` — const, line 1593
- `const owner = railPanelOf(window.deskId, extractionId)` — const, line 1594
- `const target = content.extractionId ? sourceWindowOf(window.deskId, content.extractionId) : null` — const, line 1611
- `const jump = jumps.current.get(target)` — const, line 1614
- `const linkedFrom = overview || zooming ? selection?.windowId ?? focusId : null` — const, line 1630
- `const selectedRelations = relatedTo(linkedFrom)` — const, line 1631
- `const linkRects = new Map<string, Rect>()` — const, line 1632
- `const rect = ovLayout?.cards[row]?.[index]` — const, line 1634
- `const fromCard = linkedFrom ? linkRects.get(linkedFrom) ?? null : null` — const, line 1637
- `const links = fromCard ? curvedLinks(fromCard, selectedRelations.filter((relation)` — const, line 1638
- `const ghosts: Array<` — const, line 1641
- `const row = ws.desks.findIndex((each)` — const, line 1643
- `const each = ws.desks[row]` — const, line 1644
- `const sameDesk = selectedRelations.filter((relation)` — const, line 1646
- `const linked = slot.some((id)` — const, line 1650
- `const movedShown = movedNotice && movedNotice.deskId === deskId && movedNotice.until > timers.now() ? movedNotice : null` — const, line 1655
- `const focusWindow = focusId ? ws.windows[focusId] : undefined` — const, line 1656
- `const focusZoom = typeof focusWindow?.view?.zoom === "number" ? (focusWindow.view.zoom as number) : 1` — const, line 1657
- `const windowPlaces = ws.desks.flatMap((each, rowIndex)` — const, line 1660
- `const eachCam = camX[each.deskId] ?? 0` — const, line 1661
- `const rects = slotRects(each.slots.length, stage)` — const, line 1662
- `const top = rowTop(rowIndex, stage) - rowTop(deskIndex, stage)` — const, line 1663
- `const slotReading =` — const, line 1665
- `const slotCard = ovLayout?.cards[rowIndex]?.[index] ?? slotReading` — const, line 1666
- `const readingPanes = paneRects(slotReading, slot.length)` — const, line 1667
- `const cardPanes = paneRects(slotCard, slot.length)` — const, line 1668
- `const window = ws.windows[id]` — const, line 1670
- `const sliverDesk = leaveTarget ? deskById(ws, leaveTarget.deskId) : desk` — const, line 1677
- `const sliverCam = leaveTarget && sliverDesk ? leaveTarget.cams[sliverDesk.deskId] ?? 0 : cam` — const, line 1678
- `const slivers = sliverDesk && !focusMode ? sliverSlots(sliverCam, sliverDesk.slots.length, stage) :` — const, line 1679
- `const shelfRows: ShelfRow[] = desk ? desk.slots.flatMap((slot, index)` — const, line 1680
- `const window = ws.windows[id]` — const, line 1682
- `const kind = window?.kind ?? "source"` — const, line 1683
- `const hints = overview ? [["h j k l", "select"], ["↵ / click", "open"], ["alt+↵", "open in focus"], ["alt+[ ]", "move"], ["alt+shift+j/k", "to a desk"], ["drag", "move a card"], ["b", "relations"], ["g", "hold: gather"], ["o / esc", "back"]] : focusMode ? [["…` — const, line 1697
- `const title = (event.target as HTMLInputElement).value.trim()` — const, line 1718
- `const id = mintId("desk")` — const, line 1744
- `const id = window.windowId` — const, line 1798
- `const onCurrent = each.deskId === deskId` — const, line 1799
- `const opened = visited.has(each.deskId) || onCurrent` — const, line 1800
- `const full = (!overview && onCurrent && focusMode && id === focusId) || (leaveTarget?.focusWindowId === id && leaveTarget.deskId === each.deskId)` — const, line 1801
- `const hiddenInFocus = !overview && onCurrent && focusMode && !full` — const, line 1802
- `const reading = full ?` — const, line 1803
- `const card = place.card` — const, line 1804
- `const box = overview ? card : reading` — const, line 1805
- `const leavingTo = leaveTarget?.deskId === each.deskId` — const, line 1806
- `const slotCut = leavingTo ? slotVisibility(leaveTarget.cams[each.deskId] ?? 0, each.slots.length, stage)[index] : onCurrent ? visibility[index] : null` — const, line 1807
- `const mask = full || focusMode || !slotCut ? null : leavingTo || (!overview && !zooming && onCurrent) ? softCropMask(slotCut, reading.w) : null` — const, line 1810
- `const lifecycle = lifecycles[id] ??` — const, line 1811
- `const paused = isPaused(lifecycle.state)` — const, line 1812
- `const paired = slot.length > 1` — const, line 1813
- `const selected = overview && selection !== null && slot.includes(selection.windowId)` — const, line 1814
- `const receding = overview && recedes(slot, selection?.windowId ?? null, selectedRelations, showRelations)` — const, line 1815
- `const measure = FOCUS_MEASURE[window.kind] ?? FOCUS_MEASURE.source` — const, line 1816
- `const title = titleOf(window)` — const, line 1870
- `const ringId = linkedFrom` — const, line 1952
- `const isSel = ringId !== null && slot.includes(ringId)` — const, line 1953
- `const isRel = !isSel && showRelations && slot.some((id)` — const, line 1954
- `const rect = ovLayout?.cards[rowIndex]?.[index]` — const, line 1955
- `const key = slotKey(each.deskId, slot)` — const, line 1957
- `function Sliver(` — function, line 2057
- `function WhichKey()` — function, line 2067
- `const groups: Array<` — const, line 2068
- `const rows = DESK_BINDINGS.filter((binding)` — const, line 2079
- `function OpenBeside(` — function, line 2097
- `const words = filter.trim().toLowerCase()` — const, line 2113
- `const sources = (library ?? []).filter((card)` — const, line 2114
- `const book = focus?.content && (focus.content.kind === "source" || focus.content.kind === "video") ? focus.content : null` — const, line 2115

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
- [[Reference/Desktop/TypeScript/screens/desks/model/workspace|src/screens/desks/model/workspace.ts]] — import-or-re-export; imports `DeskWindow`, `Step`, `Workspace`, `closeWindow`, `createDesk`, `deskById`, `focusAlong`, `focusPane`, `focusedSlot`, `focusedWindowId`, `moveFocused`, `moveToDesk`, `moveToDeskAt`, `moveWindowTo`, `openBeside`, `pairFocused`, `renameDesk`, `reorderSlots`, `setFocus`, `setView`, `slotIndexOf`, `swapInView`, `undoClose`, `unpairFocused`
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

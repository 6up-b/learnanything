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
| Source lines | 1938 |
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
- `export interface DeskDebugHandle` — interface, line 139
- `export const KIND_GLYPH: Record<string, string> =` — const, line 164
- `export interface DeskShellProps` — interface, line 217
- `export function DeskShell(` — function, line 240
- `export function isVideoCard(card: SourceLibraryCard): boolean` — function, line 1818
- `export function contentForCard(card: SourceLibraryCard, extractionId: string): ContentRefDto` — function, line 1822

## Internal implementation anchors

- `type DeskWindow, type Step, type Workspace, } from "./model/workspace"` — type, line 36
- `type Step, type Workspace, } from "./model/workspace"` — type, line 37
- `type Workspace, } from "./model/workspace"` — type, line 38
- `type Rect, type Stage, } from "./geometry"` — type, line 52
- `type Stage, } from "./geometry"` — type, line 53
- `type Camera, type ZoomGesture, type ZoomSource, } from "./overview/engine"` — type, line 68
- `type ZoomGesture, type ZoomSource, } from "./overview/engine"` — type, line 69
- `type ZoomSource, } from "./overview/engine"` — type, line 70
- `type DeskAction, type Timers, } from "./keys/router"` — type, line 83
- `type Timers, } from "./keys/router"` — type, line 84
- `const UNDO_CLOSE_MS = 9_000` — const, line 128
- `const TOAST_MS = 2_200` — const, line 130
- `const FLUSH_IDLE_MS = 250` — const, line 132
- `const VIEW_SAVE_IDLE_MS = 2_000` — const, line 134
- `const MOVED_NOTICE_MS = 6_000` — const, line 136
- `function prefersReducedMotion(): boolean` — function, line 147
- `function slotKey(deskId: string, slot: string[]): string` — function, line 156
- `function intersects(rect: Rect, stage: Stage): boolean` — function, line 160
- `const KIND_WORD: Record<string, string> =` — const, line 176
- `function defaultMintId(prefix: string): string` — function, line 188
- `function shortName(title: string): string` — function, line 196
- `const words = title.split(/\s+/).filter(Boolean)` — const, line 197
- `function readStored(key: string): string | null` — function, line 201
- `function writeStored(key: string, value: string): void` — function, line 209
- `const wsRef = useRef<Workspace>(EMPTY_WORKSPACE)` — const, line 256
- `const deskKey = `learnloop.desks.current.$` — const, line 258
- `const stageRef = useRef<HTMLElement | null>(null)` — const, line 273
- `const viewport = initialViewport ??` — const, line 275
- `const shelf = viewport.width < DESK_SIZES.shelfFoldBelow ? DESK_SIZES.shelfRail : DESK_SIZES.shelf` — const, line 276
- `const preOverview = useRef<` — const, line 294
- `const worldRef = useRef<HTMLDivElement | null>(null)` — const, line 295
- `const boxEls = useRef(new Map<string, HTMLElement>())` — const, line 298
- `const innerEls = useRef(new Map<string, HTMLElement>())` — const, line 299
- `const cardEls = useRef(new Map<string, HTMLElement>())` — const, line 300
- `const ringEls = useRef(new Map<string, HTMLElement>())` — const, line 301
- `const slotElements = useCallback((): Map<string, SlotElements>` — const, line 302
- `const out = new Map<string, SlotElements>()` — const, line 303
- `const lateEls = useRef(new Map<string, HTMLElement>())` — const, line 309
- `const sliverEls = useRef(new Map<string, HTMLElement>())` — const, line 310
- `const miniatures = useMemo(()` — const, line 311
- `const miniHosts = useRef(new Map<string, HTMLDivElement>())` — const, line 312
- `const onEndRef = useRef<(goal: 0 | 1, base: 0 | 1)` — const, line 313
- `const controller = useMemo(()` — const, line 314
- `const jumps = useRef(new Map<string, (spanId: string)` — const, line 315
- `const media = useRef(new Map<string, ()` — const, line 316
- `const pendingJump = useRef(new Map<string, string>())` — const, line 317
- `const outbox = useMemo( ()` — const, line 319
- `const toastNow = useCallback((text: string)` — const, line 324
- `const handle = timers.set(()` — const, line 327
- `const setCurrentDeskId = useCallback((deskId: string | null)` — const, line 333
- `const flushTimer = useRef<unknown>(null)` — const, line 338
- `const reloadRef = useRef<()` — const, line 339
- `const scheduleFlush = useCallback(()` — const, line 340
- `const commit = useCallback((step: Step)` — const, line 351
- `const chain = useCallback((first: Step, next: (ws: Workspace)` — const, line 361
- `const second = next(first.ws)` — const, line 362
- `const firstRun = useCallback(async (base: Workspace, cards: SourceLibraryCard[] | null): Promise<Step>` — const, line 366
- `const card = firstSourceId ? cards?.find((entry)` — const, line 367
- `const deskId = mintId("desk")` — const, line 368
- `const created = createDesk(base, deskId, card ? `new desk · $` — const, line 369
- `const extractionId = await transport.resolveExtraction(card.sourceId).catch(()` — const, line 371
- `const load = useCallback(async ()` — const, line 376
- `const loaded = fromDeskState(state)` — const, line 381
- `const desk = ws ? deskById(ws, currentDeskId) ?? ws.desks[0] ?? null : null` — const, line 402
- `const deskId = desk?.deskId ?? null` — const, line 403
- `const focusId = ws && desk ? focusedWindowId(ws, desk) : null` — const, line 404
- `const focusSlotIndex = ws && desk ? focusedSlot(ws, desk) : -1` — const, line 405
- `const slotCount = desk?.slots.length ?? 0` — const, line 413
- `const keepPrevious = useRef(false)` — const, line 414
- `const next = ensureVisible(cams[deskId] ?? 0, focusSlotIndex, slotCount, stage, keepPrevious.current)` — const, line 418
- `const node = stageRef.current` — const, line 426
- `const measure = ()` — const, line 427
- `const shell = node?.closest(".desk-shell") as HTMLElement | null` — const, line 430
- `const observer = typeof ResizeObserver === "undefined" || !node ? null : new ResizeObserver(measure)` — const, line 434
- `const cam = deskId ? camX[deskId] ?? 0 : 0` — const, line 443
- `const visibility = useMemo(()` — const, line 444
- `const deskIndex = ws && desk ? ws.desks.indexOf(desk) : 0` — const, line 445
- `const lifecycles = useMemo(()` — const, line 449
- `const out: Record<string, WindowLifecycle> =` — const, line 450
- `const onCurrent = each.deskId === deskId` — const, line 453
- `const lifecyclesRef = useRef(lifecycles)` — const, line 466
- `const focusIdRef = useRef(focusId)` — const, line 468
- `const focusModeRef = useRef(focusMode)` — const, line 476
- `const switchDesk = useCallback((direction: -1 | 1): boolean` — const, line 479
- `const current = wsRef.current` — const, line 480
- `const index = current.desks.findIndex((each)` — const, line 481
- `const next = current.desks[index + direction]` — const, line 482
- `const deskIdRef = useRef(deskId)` — const, line 487
- `const titleOf = useCallback((window: DeskWindow | undefined): string` — const, line 490
- `const known = status[window.windowId]?.title` — const, line 492
- `const content = window.content` — const, line 494
- `const ovLayout = useMemo(()` — const, line 504
- `const ovLayoutRef = useRef(ovLayout)` — const, line 505
- `const stageNow = useRef(stage)` — const, line 507
- `const camXRef = useRef(camX)` — const, line 509
- `const overviewRef = useRef(overview)` — const, line 511
- `const ovCamRef = useRef(ovCam)` — const, line 513
- `const selectionRef = useRef(selection)` — const, line 515
- `const visitedRef = useRef(visited)` — const, line 517
- `const showRelationsRef = useRef(showRelations)` — const, line 519
- `const reduced = reducedMotion ?? prefersReducedMotion()` — const, line 521
- `const pendingLeave = useRef<` — const, line 522
- `const cardOf = useCallback((windowId: string | null | undefined): Rect | null` — const, line 525
- `const layout = ovLayoutRef.current` — const, line 526
- `const current = wsRef.current` — const, line 527
- `const index = slotIndexOf(each, windowId)` — const, line 530
- `const readingRectOf = useCallback((current: Workspace, row: number, index: number, readingRow: number, cams: Record<string, number>, st: Stage): Rect` — const, line 538
- `const each = current.desks[row]` — const, line 539
- `const rect = slotRects(each.slots.length, st)[index]` — const, line 540
- `const relatedTo = useCallback((windowId: string | null | undefined): Relation[]` — const, line 544
- `const recedes = useCallback((slot: string[], selected: string | null, related: Relation[], relationsOn: boolean): boolean` — const, line 547
- `const planZoom = useCallback((base: 0 | 1, readingDeskId: string, cams: Record<string, number>, selected: string | null, B: Camera): ZoomPlan | null` — const, line 552
- `const current = wsRef.current` — const, line 553
- `const layout = ovLayoutRef.current` — const, line 554
- `const st = stageNow.current` — const, line 555
- `const readingRow = Math.max(0, current.desks.findIndex((each)` — const, line 557
- `const related = relatedTo(selected)` — const, line 558
- `const items: ZoomPlan["items"] = []` — const, line 559
- `const a = readingRectOf(current, row, index, readingRow, cams, st)` — const, line 561
- `const b = layout.cards[row][index]` — const, line 562
- `const zoomTargets = useCallback(()` — const, line 577
- `const beginEnter = useCallback((): boolean` — const, line 585
- `const id = deskIdRef.current` — const, line 587
- `const selected = focusIdRef.current` — const, line 590
- `const B = enteringCamera(cardOf(selected), stageNow.current)` — const, line 592
- `const plan = planZoom(0, id, camXRef.current, selected, B)` — const, line 597
- `const beginLeave = useCallback((to:` — const, line 605
- `const target = to ?? preOverview.current ?? (selectionRef.current ?` — const, line 607
- `const deskIdTo = target.deskId` — const, line 609
- `const windowTo = "windowId" in target ? target.windowId : target.focusId` — const, line 610
- `const current = wsRef.current` — const, line 611
- `const each = deskById(current, deskIdTo)` — const, line 612
- `const cams =` — const, line 614
- `const index = windowTo ? slotIndexOf(each, windowTo) : -1` — const, line 615
- `const plan = planZoom(1, deskIdTo, cams, windowTo, ovCamRef.current)` — const, line 617
- `const plan = controller.plan` — const, line 630
- `const leave = pendingLeave.current` — const, line 648
- `const toggleOverview = useCallback((to:` — const, line 668
- `const world = worldRef.current` — const, line 675
- `const id = deskIdRef.current` — const, line 680
- `const target = to ?? (preOverview.current ?` — const, line 688
- `const moveOverviewSelection = useCallback((direction: "left" | "right" | "up" | "down")` — const, line 706
- `const layout = ovLayoutRef.current` — const, line 707
- `const current = wsRef.current` — const, line 708
- `const sel = selectionRef.current` — const, line 709
- `let row = sel ? current.desks.findIndex((each)` — let, line 711
- `let slot = sel ? slotIndexOf(current.desks[row] ?? current.desks[0], sel.windowId) : 0` — let, line 712
- `const next = moveSelection(layout,` — const, line 717
- `const each = current.desks[next.row]` — const, line 718
- `const windowId = each?.slots[next.slot]?.find((id)` — const, line 719
- `const gather = useCallback((toNewDesk: boolean)` — const, line 727
- `const current = wsRef.current` — const, line 728
- `const id = deskIdRef.current` — const, line 729
- `const focus = focusIdRef.current` — const, line 730
- `const each = id ? deskById(current, id) : null` — const, line 731
- `const related = relationsOf(current, focus).filter((relation)` — const, line 738
- `const moving = [focus, ...related.slice(0, DRAWN_RELATIONS).map((relation)` — const, line 751
- `const newDeskId = mintId("desk")` — const, line 752
- `const title = `gathered · $` — const, line 753
- `let step = createDesk(current, newDeskId, title)` — let, line 754
- `let after: string | null = null` — let, line 755
- `const next = moveToDesk(step.ws, id, windowId, newDeskId, after)` — const, line 757
- `const focused = setFocus(step.ws, newDeskId, focus)` — const, line 761
- `const run = useCallback((action: DeskAction): boolean` — const, line 769
- `const current = wsRef.current` — const, line 770
- `const id = deskIdRef.current` — const, line 771
- `const focus = focusIdRef.current` — const, line 773
- `const step = focusPane(current, id, action.direction)` — const, line 779
- `const sel = overviewRef.current ? selectionRef.current : null` — const, line 785
- `const each = deskById(current, sel.deskId)` — const, line 787
- `const index = each ? slotIndexOf(each, sel.windowId) : -1` — const, line 788
- `const sel = selectionRef.current` — const, line 796
- `const row = current.desks.findIndex((each)` — const, line 798
- `const to = current.desks[row + action.direction]` — const, line 799
- `const from = current.desks[row]` — const, line 800
- `const index = slotIndexOf(from, sel.windowId)` — const, line 802
- `const afterSlot = to.slots[Math.min(index, to.slots.length) - 1]` — const, line 803
- `const sel = selectionRef.current` — const, line 815
- `const title = titleOf(current.windows[focus])` — const, line 839
- `const window = current.windows[focus]` — const, line 854
- `const zoom = typeof window?.view?.zoom === "number" ? (window.view.zoom as number) : 1` — const, line 855
- `const next = stepZoom(zoom, action.direction)` — const, line 856
- `const desk = deskById(current, id)` — const, line 862
- `const index = slotIndexOf(desk, focus)` — const, line 864
- `const shown = visibilityRef.current.filter((slot)` — const, line 865
- `const other = shown.find((slot)` — const, line 866
- `const toggle = focus ? media.current.get(focus) : undefined` — const, line 871
- `const visibilityRef = useRef(visibility)` — const, line 880
- `const runRef = useRef(run)` — const, line 882
- `const modifiers = useMemo(()` — const, line 887
- `const altTracker = useMemo( ()` — const, line 888
- `const router = useMemo(()` — const, line 892
- `const current = wsRef.current` — const, line 896
- `const id = deskIdRef.current` — const, line 897
- `const owner = current.windows[windowId]` — const, line 899
- `const resolution = resolveKey(event,` — const, line 932
- `const hubs = useRef(new Map<string, ListenerHub>())` — const, line 947
- `const hubFor = useCallback((windowId: string): ListenerHub` — const, line 948
- `let hub = hubs.current.get(windowId)` — let, line 949
- `const world = worldRef.current` — const, line 961
- `const mainRef = useRef<HTMLElement | null>(null)` — const, line 966
- `const gesture = useRef<` — const, line 967
- `const endGesture = useCallback(()` — const, line 968
- `const g = gesture.current` — const, line 969
- `const current = wsRef.current` — const, line 979
- `const id = deskIdRef.current` — const, line 980
- `const each = id ? deskById(current, id) : null` — const, line 981
- `const st = stageNow.current` — const, line 983
- `const rects = slotRects(each.slots.length, st)` — const, line 984
- `const cam = camXRef.current[id] ?? 0` — const, line 985
- `let best = 0` — let, line 986
- `const snapped = ensureVisible(rects[best].x - DESK_SIZES.side, best, each.slots.length, st)` — const, line 990
- `const target = each.slots[best].find((windowId)` — const, line 992
- `const main = mainRef.current` — const, line 998
- `const onWheel = (event: WheelEvent)` — const, line 1000
- `const target = event.target as Element | null` — const, line 1001
- `const st = stageNow.current` — const, line 1003
- `const now = performance.now()` — const, line 1004
- `let g = gesture.current` — let, line 1005
- `const kind = classifyWheel(event, modifiers.read(event), st.height)` — const, line 1007
- `const ovPlain = overviewRef.current && kind.kind !== "zoom"` — const, line 1009
- `const id = deskIdRef.current` — const, line 1035
- `const each = id ? deskById(wsRef.current, id) : null` — const, line 1036
- `const travel = Math.abs(dx) > Math.abs(dy) ? dx : dy` — const, line 1038
- `const max = Math.max(0, slotRects(each.slots.length, st).reduce((end, rect)` — const, line 1039
- `const result = zoomWheel(g.zoom, dy, now,` — const, line 1049
- `const stepped = result.step` — const, line 1051
- `const began = overviewRef.current ? beginLeave(selectionRef.current ?` — const, line 1053
- `const began = stepped.goal === 1 ? beginEnter() : beginLeave(selectionRef.current ?` — const, line 1059
- `const how = g.source === "pinch" ? "pinch" : modifiers.read(event).alt ? "alt + scroll" : "ctrl + scroll"` — const, line 1065
- `const drag = useRef<` — const, line 1079
- `const onStagePointerDown = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1080
- `const target = event.target as Element` — const, line 1081
- `const onCard = target.closest("[data-desk-slot]")` — const, line 1082
- `const inContent = target.closest(".desk-slot-inner, .desk-sliver, button, input, textarea")` — const, line 1083
- `const key = onCard.getAttribute("data-desk-slot-key") ?? undefined` — const, line 1086
- `const windowId = onCard.getAttribute("data-desk-slot-window") ?? undefined` — const, line 1087
- `const deskOf = onCard.getAttribute("data-desk-slot-desk") ?? undefined` — const, line 1088
- `const onStagePointerMove = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1102
- `const d = drag.current` — const, line 1103
- `const dx = event.clientX - d.x` — const, line 1105
- `const dy = event.clientY - d.y` — const, line 1106
- `const element = d.key ? boxEls.current.get(d.key) : null` — const, line 1125
- `const onStagePointerUp = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1131
- `const d = drag.current` — const, line 1132
- `const element = d.key ? boxEls.current.get(d.key) : null` — const, line 1141
- `const layout = ovLayoutRef.current` — const, line 1152
- `const stageBox = (event.currentTarget as HTMLElement).getBoundingClientRect()` — const, line 1153
- `const point =` — const, line 1155
- `const drop = dropTarget(layout, point)` — const, line 1156
- `const current = wsRef.current` — const, line 1157
- `const to = drop ? current.desks[drop.row] : null` — const, line 1158
- `const from = slotIndexOf(to, d.windowId)` — const, line 1161
- `const afterSlot = to.slots[drop.slot - 1]` — const, line 1164
- `const handle = timers.set(()` — const, line 1173
- `const body = [...document.querySelectorAll<HTMLElement>("[data-desk-window]")].find((pane)` — const, line 1175
- `const node = miniatures.get(windowId)` — const, line 1185
- `const node = host.firstElementChild as HTMLElement | null` — const, line 1188
- `const openContent = useCallback((content: ContentRefDto, options:` — const, line 1208
- `const current = wsRef.current` — const, line 1209
- `const id = deskIdRef.current` — const, line 1210
- `const step = openBeside(current, id, content, ()` — const, line 1212
- `const jump = jumps.current.get(step.windowId)` — const, line 1219
- `const next = new Set(now)` — const, line 1226
- `const openHit = useCallback((hit:` — const, line 1234
- `const card = library?.find((entry)` — const, line 1236
- `const kind = card && isVideoCard(card) ? "video" : "source"` — const, line 1237
- `const viewTimers = useRef(new Map<string, unknown>())` — const, line 1243
- `const statusFor = useMemo(()` — const, line 1244
- `const onStatusFor = useCallback((windowId: string)` — const, line 1245
- `let handler = statusFor.get(windowId)` — let, line 1246
- `const previous = viewTimers.current.get(windowId)` — const, line 1255
- `const current = wsRef.current` — const, line 1259
- `const window = current.windows[windowId]` — const, line 1260
- `const jumpReadyFor = useMemo(()` — const, line 1271
- `const onJumpReadyFor = useCallback((windowId: string)` — const, line 1272
- `let handler = jumpReadyFor.get(windowId)` — let, line 1273
- `const pending = pendingJump.current.get(windowId)` — const, line 1281
- `const mediaReadyFor = useMemo(()` — const, line 1292
- `const onMediaReadyFor = useCallback((windowId: string)` — const, line 1293
- `let handler = mediaReadyFor.get(windowId)` — let, line 1294
- `const railNodeFor = useMemo(()` — const, line 1305
- `const onRailNode = useCallback((windowId: string)` — const, line 1306
- `let handler = railNodeFor.get(windowId)` — let, line 1307
- `const railPanelOf = useCallback((deskOf: string, extractionId: string): string | null` — const, line 1316
- `const desk = deskById(ws, deskOf)` — const, line 1318
- `const panels = desk.slots.flat().filter((id)` — const, line 1320
- `const content = ws.windows[id]?.content` — const, line 1321
- `const claimed = railClaims[`$` — const, line 1324
- `const sourceWindowOf = useCallback((deskOf: string, extractionId: string): string | null` — const, line 1328
- `const desk = deskById(ws, deskOf)` — const, line 1330
- `const content = ws.windows[id]?.content` — const, line 1333
- `const undoShown = undo && undo.deskId === deskId && undo.until > timers.now() ? undo : null` — const, line 1340
- `const handle = timers.set(()` — const, line 1343
- `const paneBody = (window: DeskWindow, lifecycle: WindowLifecycle): ReactNode` — const, line 1357
- `const content = window.content` — const, line 1358
- `const card = content && (content.kind === "source" || content.kind === "video") ? library?.find((entry)` — const, line 1359
- `const railPanel = railPanelOf(window.deskId, content.extractionId)` — const, line 1365
- `const railNode = railPanel ? railHosts[railPanel] ?? null : null` — const, line 1366
- `const railContent = railPanel ? ws.windows[railPanel]?.content : null` — const, line 1367
- `const railTab = railContent?.kind === "panel" && railContent.panel === "notes" ? "notes" : "guide"` — const, line 1368
- `const extractionId = content.extractionId ?? ""` — const, line 1386
- `const owner = railPanelOf(window.deskId, extractionId)` — const, line 1387
- `const target = content.extractionId ? sourceWindowOf(window.deskId, content.extractionId) : null` — const, line 1404
- `const jump = jumps.current.get(target)` — const, line 1407
- `const linkedFrom = overview || zooming ? selection?.windowId ?? focusId : null` — const, line 1423
- `const selectedRelations = relatedTo(linkedFrom)` — const, line 1424
- `const linkRects = new Map<string, Rect>()` — const, line 1425
- `const rect = ovLayout?.cards[row]?.[index]` — const, line 1427
- `const fromCard = linkedFrom ? linkRects.get(linkedFrom) ?? null : null` — const, line 1430
- `const links = fromCard ? curvedLinks(fromCard, selectedRelations.filter((relation)` — const, line 1431
- `const ghosts: Array<` — const, line 1434
- `const row = ws.desks.findIndex((each)` — const, line 1436
- `const each = ws.desks[row]` — const, line 1437
- `const sameDesk = selectedRelations.filter((relation)` — const, line 1439
- `const linked = slot.some((id)` — const, line 1443
- `const movedShown = movedNotice && movedNotice.deskId === deskId && movedNotice.until > timers.now() ? movedNotice : null` — const, line 1448
- `const focusWindow = focusId ? ws.windows[focusId] : undefined` — const, line 1449
- `const focusZoom = typeof focusWindow?.view?.zoom === "number" ? (focusWindow.view.zoom as number) : 1` — const, line 1450
- `const sliverDesk = leaveTarget ? deskById(ws, leaveTarget.deskId) : desk` — const, line 1452
- `const sliverCam = leaveTarget && sliverDesk ? leaveTarget.cams[sliverDesk.deskId] ?? 0 : cam` — const, line 1453
- `const slivers = sliverDesk && !focusMode ? sliverSlots(sliverCam, sliverDesk.slots.length, stage) :` — const, line 1454
- `const shelfRows: ShelfRow[] = desk ? desk.slots.flatMap((slot, index)` — const, line 1455
- `const window = ws.windows[id]` — const, line 1457
- `const kind = window?.kind ?? "source"` — const, line 1458
- `const hints = overview ? [["h j k l", "select"], ["↵ / click", "open"], ["alt+↵", "open in focus"], ["alt+[ ]", "move"], ["alt+shift+j/k", "to a desk"], ["drag", "move a card"], ["b", "relations"], ["g", "hold: gather"], ["o / esc", "back"]] : focusMode ? [["…` — const, line 1472
- `const title = (event.target as HTMLInputElement).value.trim()` — const, line 1493
- `const id = mintId("desk")` — const, line 1519
- `const onCurrent = each.deskId === deskId` — const, line 1558
- `const opened = visited.has(each.deskId) || onCurrent` — const, line 1559
- `const eachCam = camX[each.deskId] ?? 0` — const, line 1560
- `const rects = slotRects(each.slots.length, stage)` — const, line 1561
- `const top = rowTop(rowIndex, stage) - rowTop(deskIndex, stage)` — const, line 1562
- `const eachVisibility = onCurrent ? visibility : slotVisibility(eachCam, each.slots.length, stage)` — const, line 1563
- `const rect = rects[index]` — const, line 1565
- `const key = slotKey(each.deskId, slot)` — const, line 1566
- `const full = !overview && onCurrent && focusMode && slot.includes(focusId ?? "")` — const, line 1567
- `const reading = full ?` — const, line 1568
- `const card = ovLayout?.cards[rowIndex]?.[index] ?? reading` — const, line 1571
- `const box = overview ? card : reading` — const, line 1572
- `const leavingTo = leaveTarget?.deskId === each.deskId` — const, line 1573
- `const mask = full || focusMode ? null : leavingTo ? softCropMask(slotVisibility(leaveTarget.cams[each.deskId] ?? 0, each.slots.length, stage)[index], rect.w) : !overview && !zooming && onCurrent ? softCropMask(eachVisibility[index], rect.w) : null` — const, line 1574
- `const slotPaused = slot.every((id)` — const, line 1579
- `const panes = full ? slot.filter((id)` — const, line 1580
- `const first = ws.windows[slot.find((id)` — const, line 1581
- `const selected = overview && selection !== null && slot.includes(selection.windowId)` — const, line 1583
- `const receding = overview && recedes(slot, selection?.windowId ?? null, selectedRelations, showRelations)` — const, line 1584
- `const firstKind = first?.kind ?? "source"` — const, line 1585
- `const window = ws.windows[id]` — const, line 1617
- `const lifecycle = lifecycles[id] ??` — const, line 1619
- `const paired = panes.length > 1` — const, line 1620
- `const measure = FOCUS_MEASURE[window.kind] ?? FOCUS_MEASURE.source` — const, line 1621
- `const title = titleOf(window)` — const, line 1644
- `const ringId = linkedFrom` — const, line 1723
- `const isSel = ringId !== null && slot.includes(ringId)` — const, line 1724
- `const isRel = !isSel && showRelations && slot.some((id)` — const, line 1725
- `const rect = ovLayout?.cards[rowIndex]?.[index]` — const, line 1726
- `const key = slotKey(each.deskId, slot)` — const, line 1728
- `function Sliver(` — function, line 1828
- `function WhichKey()` — function, line 1838
- `const groups: Array<` — const, line 1839
- `const rows = DESK_BINDINGS.filter((binding)` — const, line 1850
- `function OpenBeside(` — function, line 1868
- `const words = filter.trim().toLowerCase()` — const, line 1884
- `const sources = (library ?? []).filter((card)` — const, line 1885
- `const book = focus?.content && (focus.content.kind === "source" || focus.content.kind === "video") ? focus.content : null` — const, line 1886

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
- [[Reference/Desktop/TypeScript/screens/desks/keys/listeners|src/screens/desks/keys/listeners.ts]] — import-or-re-export; imports `DeskListenerRouter`, `WINDOW_ATTRIBUTE`
- [[Reference/Desktop/TypeScript/screens/desks/keys/router|src/screens/desks/keys/router.ts]] — import-or-re-export; imports `BareAltTracker`, `DESK_BINDINGS`, `DeskAction`, `ModifierTracker`, `REAL_TIMERS`, `Timers`, `isTypingTarget`, `resolveKey`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `ListenerHub`, `WindowLifecycle`, `WindowScope`, `isPaused`, `windowState`
- [[Reference/Desktop/TypeScript/screens/desks/model/workspace|src/screens/desks/model/workspace.ts]] — import-or-re-export; imports `DeskWindow`, `EMPTY_WORKSPACE`, `Step`, `Workspace`, `closeWindow`, `createDesk`, `deskById`, `focusAlong`, `focusPane`, `focusedSlot`, `focusedWindowId`, `fromDeskState`, `moveFocused`, `moveToDesk`, `moveWindowTo`, `openBeside`, `pairFocused`, `renameDesk`, `reorderSlots`, `setFocus`, `setView`, `slotIndexOf`, `swapInView`, `undoClose`, `unpairFocused`
- [[Reference/Desktop/TypeScript/screens/desks/outbox|src/screens/desks/outbox.ts]] — import-or-re-export; imports `DeskOutbox`, `OutboxTransport`, `clientIdFor`
- [[Reference/Desktop/TypeScript/screens/desks/overview/Card|src/screens/desks/overview/Card.tsx]] — import-or-re-export; imports `CardFace`, `LinkLayer`
- [[Reference/Desktop/TypeScript/screens/desks/overview/controller|src/screens/desks/overview/controller.ts]] — import-or-re-export; imports `ANIMATION_FRAMES`, `FrameClock`, `SlotElements`, `ZoomController`, `ZoomPlan`, `cameraTransform`
- [[Reference/Desktop/TypeScript/screens/desks/overview/engine|src/screens/desks/overview/engine.ts]] — import-or-re-export; imports `Camera`, `IDENTITY`, `OVERVIEW`, `ZoomGesture`, `ZoomSource`, `classifyWheel`, `dragProgress`, `dropTarget`, `enteringCamera`, `followSelection`, `moveSelection`, `newZoomGesture`, `normalizedDelta`, `overviewLayout`, `zoomWheel`
- [[Reference/Desktop/TypeScript/screens/desks/overview/links|src/screens/desks/overview/links.ts]] — import-or-re-export; imports `DRAWN_RELATIONS`, `Relation`, `curvedLinks`, `gatherOrder`, `relationsOf`
- [[Reference/Desktop/TypeScript/screens/desks/overview/miniature|src/screens/desks/overview/miniature.ts]] — import-or-re-export; imports `MiniatureBook`, `cloneForMiniature`
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

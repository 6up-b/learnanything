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
| Source lines | 2887 |
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

- `export interface DeskTransport extends OutboxTransport` — interface, line 120
- `export const LIVE_DESK_TRANSPORT: DeskTransport =` — const, line 130
- `export interface PadsTransport extends PadsApi` — interface, line 194
- `export const LIVE_PADS_TRANSPORT: PadsTransport =` — const, line 202
- `export interface CompanionTransport extends CompanionApi, SearchApi` — interface, line 219
- `export const LIVE_COMPANION_TRANSPORT: CompanionTransport =` — const, line 223
- `export interface PaneRenderInput` — interface, line 233
- `export interface DeskDebugHandle` — interface, line 249
- `export const KIND_GLYPH: Record<string, string> =` — const, line 284
- `export interface DeskShellProps` — interface, line 337
- `export function DeskShell(` — function, line 366
- `export function isVideoCard(card: SourceLibraryCard): boolean` — function, line 2767
- `export function contentForCard(card: SourceLibraryCard, extractionId: string): ContentRefDto` — function, line 2771

## Internal implementation anchors

- `type DeskWindow, type Step, type Workspace, } from "./model/workspace"` — type, line 38
- `type Step, type Workspace, } from "./model/workspace"` — type, line 39
- `type Workspace, } from "./model/workspace"` — type, line 40
- `type Rect, type Stage, } from "./geometry"` — type, line 54
- `type Stage, } from "./geometry"` — type, line 55
- `type Camera, type ZoomGesture, type ZoomSource, } from "./overview/engine"` — type, line 70
- `type ZoomGesture, type ZoomSource, } from "./overview/engine"` — type, line 71
- `type ZoomSource, } from "./overview/engine"` — type, line 72
- `type DeskAction, type Timers, } from "./keys/router"` — type, line 85
- `type Timers, } from "./keys/router"` — type, line 86
- `const COMPANION_SIZES_HANDOFF_MS = 250` — const, line 144
- `interface Grounding` — interface, line 147
- `function groundingFor(ws: Workspace, chip:` — function, line 154
- `const content = ws.windows[chip.windowId]?.content` — const, line 156
- `const content = focus?.content` — const, line 161
- `const span = status[focus.windowId]?.readingSpan ?? (typeof focus.view?.spanId === "string" ? (focus.view.spanId as string) : undefined)` — const, line 165
- `function firstVisibleSpan(windowId: string | null): string | null` — function, line 172
- `const host = document.querySelector(`[$` — const, line 174
- `const top = host.getBoundingClientRect().top` — const, line 176
- `const spans = [...host.querySelectorAll<HTMLElement>("[data-span-id], [data-transcript-span]")]` — const, line 177
- `const visible = spans.find((element)` — const, line 178
- `function keyAfterLast(blocks: Array<` — function, line 183
- `function threadTitle(thread: CompanionExchange[]): string` — function, line 187
- `const last = thread[thread.length - 1]` — const, line 188
- `const UNDO_CLOSE_MS = 9_000` — const, line 240
- `const TOAST_MS = 2_200` — const, line 242
- `const VIEW_SAVE_IDLE_MS = 2_000` — const, line 244
- `const MOVED_NOTICE_MS = 6_000` — const, line 246
- `function displayedCamera(world: HTMLElement): Camera | null` — function, line 259
- `const shown = typeof getComputedStyle === "function" ? getComputedStyle(world).transform : ""` — const, line 260
- `const match = /^matrix\(([^)]+)\)$/.exec(shown ?? "")` — const, line 261
- `function prefersReducedMotion(): boolean` — function, line 267
- `function slotKey(deskId: string, slot: string[]): string` — function, line 276
- `function intersects(rect: Rect, stage: Stage): boolean` — function, line 280
- `const KIND_WORD: Record<string, string> =` — const, line 296
- `function defaultMintId(prefix: string): string` — function, line 308
- `function shortName(title: string): string` — function, line 316
- `const words = title.split(/\s+/).filter(Boolean)` — const, line 317
- `function readStored(key: string): string | null` — function, line 321
- `function writeStored(key: string, value: string): void` — function, line 329
- `const store = useMemo( ()` — const, line 386
- `const storeWs = useSyncExternalStore(store.subscribe, store.getSnapshot)` — const, line 390
- `const ws: Workspace | null = storeReady ? storeWs : null` — const, line 394
- `const wsRef = useMemo(()` — const, line 395
- `const deskKey = `learnloop.desks.current.$` — const, line 397
- `const stageRef = useRef<HTMLElement | null>(null)` — const, line 412
- `const viewport = initialViewport ??` — const, line 414
- `const shelf = viewport.width < DESK_SIZES.shelfFoldBelow ? DESK_SIZES.shelfRail : DESK_SIZES.shelf` — const, line 415
- `const padHandles = useRef(new Map<string, PadStackHandle>())` — const, line 441
- `const drainingRef = useRef(false)` — const, line 444
- `const companionRef = useRef<CompanionHandle | null>(null)` — const, line 446
- `const preOverview = useRef<` — const, line 449
- `const worldRef = useRef<HTMLDivElement | null>(null)` — const, line 450
- `const boxEls = useRef(new Map<string, HTMLElement>())` — const, line 453
- `const innerEls = useRef(new Map<string, HTMLElement>())` — const, line 454
- `const cardEls = useRef(new Map<string, HTMLElement>())` — const, line 455
- `const ringEls = useRef(new Map<string, HTMLElement>())` — const, line 456
- `const slotElements = useCallback((): Map<string, SlotElements>` — const, line 457
- `const out = new Map<string, SlotElements>()` — const, line 458
- `const lateEls = useRef(new Map<string, HTMLElement>())` — const, line 462
- `const sliverEls = useRef(new Map<string, HTMLElement>())` — const, line 463
- `const miniatures = useMemo(()` — const, line 464
- `const miniHosts = useRef(new Map<string, HTMLDivElement>())` — const, line 465
- `const onEndRef = useRef<(goal: 0 | 1, base: 0 | 1)` — const, line 466
- `const controller = useMemo(()` — const, line 467
- `const jumps = useRef(new Map<string, (spanId: string)` — const, line 468
- `const media = useRef(new Map<string, ()` — const, line 469
- `const pendingJump = useRef(new Map<string, string>())` — const, line 470
- `const toastNow = useCallback((text: string)` — const, line 472
- `const handle = timers.set(()` — const, line 475
- `const setCurrentDeskId = useCallback((deskId: string | null)` — const, line 481
- `const commit = useCallback((step: Step)` — const, line 486
- `const total = notice.dropped + notice.lost` — const, line 495
- `const chain = useCallback((first: Step, next: (ws: Workspace)` — const, line 501
- `const second = next(first.ws)` — const, line 502
- `const firstRun = useCallback(async (base: Workspace, cards: SourceLibraryCard[] | null): Promise<Step>` — const, line 506
- `const card = firstSourceId ? cards?.find((entry)` — const, line 507
- `const deskId = mintId("desk")` — const, line 508
- `const created = createDesk(base, deskId, card ? `new desk · $` — const, line 509
- `const extractionId = await transport.resolveExtraction(card.sourceId).catch(()` — const, line 511
- `let live = true` — let, line 517
- `const desk = ws ? deskById(ws, currentDeskId) ?? ws.desks[0] ?? null : null` — const, line 539
- `const deskId = desk?.deskId ?? null` — const, line 540
- `const focusId = ws && desk ? focusedWindowId(ws, desk) : null` — const, line 541
- `const focusSlotIndex = ws && desk ? focusedSlot(ws, desk) : -1` — const, line 542
- `const slotCount = desk?.slots.length ?? 0` — const, line 550
- `const keepPrevious = useRef(false)` — const, line 551
- `const next = ensureVisible(cams[deskId] ?? 0, focusSlotIndex, slotCount, stage, keepPrevious.current)` — const, line 555
- `const node = stageRef.current` — const, line 563
- `const measure = ()` — const, line 564
- `const next =` — const, line 566
- `const now = stageNow.current` — const, line 567
- `const shell = node?.closest(".desk-shell") as HTMLElement | null` — const, line 574
- `const observer = typeof ResizeObserver === "undefined" || !node ? null : new ResizeObserver(measure)` — const, line 578
- `const cam = deskId ? camX[deskId] ?? 0 : 0` — const, line 587
- `const visibility = useMemo(()` — const, line 588
- `const deskIndex = ws && desk ? ws.desks.indexOf(desk) : 0` — const, line 589
- `const lifecycles = useMemo(()` — const, line 593
- `const out: Record<string, WindowLifecycle> =` — const, line 594
- `const onCurrent = each.deskId === deskId` — const, line 597
- `const activeWindowId = Object.values(lifecycles).find((each)` — const, line 613
- `const held = document.activeElement` — const, line 615
- `const owner = held && held !== document.body ? windowOfTarget(held) : null` — const, line 616
- `const target = activeWindowId ? document.querySelector<HTMLElement>(`[$` — const, line 618
- `const lifecyclesRef = useRef(lifecycles)` — const, line 624
- `const focusIdRef = useRef(focusId)` — const, line 626
- `const knownOwners = useRef(new Set<string>())` — const, line 630
- `const focusModeRef = useRef(focusMode)` — const, line 642
- `const switchDesk = useCallback((direction: -1 | 1): boolean` — const, line 645
- `const current = wsRef.current` — const, line 646
- `const index = current.desks.findIndex((each)` — const, line 647
- `const next = current.desks[index + direction]` — const, line 648
- `const deskIdRef = useRef(deskId)` — const, line 653
- `const titleOf = useCallback((window: DeskWindow | undefined): string` — const, line 656
- `const known = status[window.windowId]?.title` — const, line 658
- `const content = window.content` — const, line 660
- `const ovLayout = useMemo(()` — const, line 670
- `const ovLayoutRef = useRef(ovLayout)` — const, line 671
- `const stageNow = useRef(stage)` — const, line 673
- `const camXRef = useRef(camX)` — const, line 675
- `const overviewRef = useRef(overview)` — const, line 677
- `const ovCamRef = useRef(ovCam)` — const, line 679
- `const selectionRef = useRef(selection)` — const, line 681
- `const visitedRef = useRef(visited)` — const, line 683
- `const showRelationsRef = useRef(showRelations)` — const, line 685
- `const reduced = reducedMotion ?? prefersReducedMotion()` — const, line 687
- `const transitionGen = useRef(0)` — const, line 690
- `const panEaseRef = useRef(panEase)` — const, line 691
- `const pendingLeave = useRef<` — const, line 693
- `const cardOf = useCallback((windowId: string | null | undefined): Rect | null` — const, line 696
- `const layout = ovLayoutRef.current` — const, line 697
- `const current = wsRef.current` — const, line 698
- `const index = slotIndexOf(each, windowId)` — const, line 701
- `const readingRectOf = useCallback((current: Workspace, row: number, index: number, readingRow: number, cams: Record<string, number>, st: Stage): Rect` — const, line 709
- `const each = current.desks[row]` — const, line 710
- `const rect = slotRects(each.slots.length, st)[index]` — const, line 711
- `const relatedTo = useCallback((windowId: string | null | undefined): Relation[]` — const, line 715
- `const recedes = useCallback((slot: string[], selected: string | null, related: Relation[], relationsOn: boolean): boolean` — const, line 718
- `const planZoom = useCallback((base: 0 | 1, readingDeskId: string, cams: Record<string, number>, selected: string | null, B: Camera, fullWindowId: string | null = null): ZoomPlan | null` — const, line 723
- `const current = wsRef.current` — const, line 724
- `const layout = ovLayoutRef.current` — const, line 725
- `const st = stageNow.current` — const, line 726
- `const readingRow = Math.max(0, current.desks.findIndex((each)` — const, line 728
- `const related = relatedTo(selected)` — const, line 729
- `const items: ZoomPlan["items"] = []` — const, line 730
- `const rings: ZoomPlan["rings"] = []` — const, line 731
- `const a = readingRectOf(current, row, index, readingRow, cams, st)` — const, line 733
- `const b = layout.cards[row][index]` — const, line 734
- `const readingPanes = paneRects(a, slot.length)` — const, line 735
- `const cardPanes = paneRects(b, slot.length)` — const, line 736
- `const live = visitedRef.current.has(each.deskId) && each.deskId === readingDeskId && intersects(a, st)` — const, line 737
- `const recede = recedes(slot, selected, related, showRelationsRef.current)` — const, line 738
- `const focus = selected !== null && slot.includes(selected)` — const, line 739
- `const isRelated = showRelationsRef.current && slot.some((id)` — const, line 740
- `const pa = id === fullWindowId && each.deskId === readingDeskId ?` — const, line 743
- `const pb = cardPanes[pane]` — const, line 744
- `const zoomTargets = useCallback(()` — const, line 752
- `const crossfade = useCallback((enter: boolean, to:` — const, line 764
- `const world = worldRef.current` — const, line 766
- `const id = deskIdRef.current` — const, line 772
- `const target = to ?? (preOverview.current ?` — const, line 781
- `const beginEnter = useCallback((): boolean` — const, line 792
- `const id = deskIdRef.current` — const, line 794
- `const selected = focusIdRef.current` — const, line 802
- `const B = enteringCamera(cardOf(selected), stageNow.current)` — const, line 804
- `const plan = planZoom(0, id, camXRef.current, selected, B)` — const, line 809
- `const beginLeave = useCallback((to:` — const, line 817
- `const shown = displayedCamera(worldRef.current) ?? ovCamRef.current` — const, line 827
- `const target = to ?? preOverview.current ?? (selectionRef.current ?` — const, line 833
- `const deskIdTo = target.deskId` — const, line 835
- `const windowTo = "windowId" in target ? target.windowId : target.focusId` — const, line 836
- `const current = wsRef.current` — const, line 837
- `const each = deskById(current, deskIdTo)` — const, line 838
- `const fullWindowId = focusAfter && windowTo ? windowTo : null` — const, line 840
- `const node = stageRef.current` — const, line 849
- `const cams =` — const, line 853
- `const index = windowTo ? slotIndexOf(each, windowTo) : -1` — const, line 854
- `const plan = planZoom(1, deskIdTo, cams, windowTo, ovCamRef.current, fullWindowId)` — const, line 856
- `const plan = controller.plan` — const, line 872
- `const leave = pendingLeave.current` — const, line 890
- `const generation = transitionGen.current` — const, line 904
- `const toggleOverview = useCallback((to:` — const, line 913
- `const focusWindow = focusId ? ws.windows[focusId] : null` — const, line 930
- `const first = ws.desks.find((each)` — const, line 935
- `const windowId = first ? first.slots[0].find((id)` — const, line 936
- `const followMoved = useRef(false)` — const, line 940
- `const rect = cardOf(selection.windowId)` — const, line 944
- `const moveOverviewSelection = useCallback((direction: "left" | "right" | "up" | "down")` — const, line 951
- `const layout = ovLayoutRef.current` — const, line 952
- `const current = wsRef.current` — const, line 953
- `const sel = selectionRef.current` — const, line 954
- `let row = sel ? current.desks.findIndex((each)` — let, line 956
- `let slot = sel ? slotIndexOf(current.desks[row] ?? current.desks[0], sel.windowId) : 0` — let, line 957
- `const next = moveSelection(layout,` — const, line 962
- `const each = current.desks[next.row]` — const, line 963
- `const windowId = each?.slots[next.slot]?.find((id)` — const, line 964
- `const gather = useCallback((toNewDesk: boolean)` — const, line 972
- `const current = wsRef.current` — const, line 973
- `const id = deskIdRef.current` — const, line 974
- `const focus = focusIdRef.current` — const, line 975
- `const each = id ? deskById(current, id) : null` — const, line 976
- `const related = relationsOf(current, focus).filter((relation)` — const, line 983
- `const moving = [focus, ...related.slice(0, DRAWN_RELATIONS).map((relation)` — const, line 996
- `const newDeskId = mintId("desk")` — const, line 997
- `const title = `gathered · $` — const, line 998
- `let step = createDesk(current, newDeskId, title)` — let, line 999
- `let after: string | null = null` — let, line 1000
- `const next = moveToDesk(step.ws, id, windowId, newDeskId, after)` — const, line 1002
- `const focused = setFocus(step.ws, newDeskId, focus)` — const, line 1006
- `const run = useCallback((action: DeskAction): boolean` — const, line 1014
- `const current = wsRef.current` — const, line 1015
- `const id = deskIdRef.current` — const, line 1016
- `const focus = focusIdRef.current` — const, line 1018
- `const stack = focusedStackRef.current()` — const, line 1025
- `const step = focusPane(current, id, action.direction)` — const, line 1027
- `const sel = overviewRef.current ? selectionRef.current : null` — const, line 1033
- `const each = deskById(current, sel.deskId)` — const, line 1035
- `const index = each ? slotIndexOf(each, sel.windowId) : -1` — const, line 1036
- `const sel = selectionRef.current` — const, line 1047
- `const row = current.desks.findIndex((each)` — const, line 1049
- `const to = current.desks[row + action.direction]` — const, line 1050
- `const from = current.desks[row]` — const, line 1051
- `const index = slotIndexOf(from, sel.windowId)` — const, line 1053
- `const sel = selectionRef.current` — const, line 1066
- `const title = titleOf(current.windows[focus])` — const, line 1090
- `const window = current.windows[focus]` — const, line 1105
- `const zoom = typeof window?.view?.zoom === "number" ? (window.view.zoom as number) : 1` — const, line 1106
- `const next = stepZoom(zoom, action.direction)` — const, line 1107
- `const desk = deskById(current, id)` — const, line 1113
- `const index = slotIndexOf(desk, focus)` — const, line 1115
- `const shown = visibilityRef.current.filter((slot)` — const, line 1116
- `const other = shown.find((slot)` — const, line 1117
- `const toggle = focus ? media.current.get(focus) : undefined` — const, line 1122
- `const stack = focusedStackRef.current()` — const, line 1128
- `const stack = focusedStackRef.current()` — const, line 1134
- `const stack = focusedStackRef.current()` — const, line 1140
- `const stack = focusedStackRef.current()` — const, line 1146
- `const stack = focusedStackRef.current()` — const, line 1153
- `const visibilityRef = useRef(visibility)` — const, line 1169
- `const runRef = useRef(run)` — const, line 1171
- `const modifiers = useMemo(()` — const, line 1176
- `const altTracker = useMemo( ()` — const, line 1177
- `const router = useMemo(()` — const, line 1181
- `const current = wsRef.current` — const, line 1186
- `const id = deskIdRef.current` — const, line 1187
- `const owner = current.windows[windowId]` — const, line 1189
- `const outcome = altTracker.release(event)` — const, line 1217
- `const open = claimed.current.get(focusIdRef.current ?? "")` — const, line 1226
- `const has = (scope: ClaimedScope)` — const, line 1227
- `const resolution = resolveKey(event,` — const, line 1228
- `const claimed = useRef(new Map<string, Map<ClaimedScope, Set<string>>>())` — const, line 1254
- `const claimsByWindow = useRef(new Map<string, ScopeClaims>())` — const, line 1255
- `const claimsFor = useCallback((windowId: string): ScopeClaims` — const, line 1256
- `let claims = claimsByWindow.current.get(windowId)` — let, line 1257
- `const byScope = claimed.current.get(windowId) ?? new Map<ClaimedScope, Set<string>>()` — const, line 1261
- `const owners = byScope.get(scope) ?? new Set<string>()` — const, line 1262
- `const hubs = useRef(new Map<string, ListenerHub>())` — const, line 1273
- `const hubFor = useCallback((windowId: string): ListenerHub` — const, line 1274
- `let hub = hubs.current.get(windowId)` — let, line 1275
- `const world = worldRef.current` — const, line 1287
- `const mainRef = useRef<HTMLElement | null>(null)` — const, line 1292
- `const gesture = useRef<` — const, line 1293
- `const endGesture = useCallback(()` — const, line 1294
- `const g = gesture.current` — const, line 1295
- `const current = wsRef.current` — const, line 1305
- `const id = deskIdRef.current` — const, line 1306
- `const each = id ? deskById(current, id) : null` — const, line 1307
- `const st = stageNow.current` — const, line 1309
- `const rects = slotRects(each.slots.length, st)` — const, line 1310
- `const cam = camXRef.current[id] ?? 0` — const, line 1311
- `let best = 0` — let, line 1312
- `const snapped = ensureVisible(rects[best].x - DESK_SIZES.side, best, each.slots.length, st)` — const, line 1316
- `const target = each.slots[best].find((windowId)` — const, line 1318
- `const main = mainRef.current` — const, line 1324
- `const onWheel = (event: WheelEvent)` — const, line 1326
- `const target = event.target as Element | null` — const, line 1327
- `const st = stageNow.current` — const, line 1332
- `const now = performance.now()` — const, line 1333
- `let g = gesture.current` — let, line 1334
- `const kind = classifyWheel(event, modifiers.read(), st.height)` — const, line 1338
- `const ovPlain = overviewRef.current && kind.kind !== "zoom"` — const, line 1340
- `const id = deskIdRef.current` — const, line 1366
- `const each = id ? deskById(wsRef.current, id) : null` — const, line 1367
- `const travel = Math.abs(dx) > Math.abs(dy) ? dx : dy` — const, line 1369
- `const max = Math.max(0, slotRects(each.slots.length, st).reduce((end, rect)` — const, line 1370
- `const result = zoomWheel(g.zoom, dy, now,` — const, line 1380
- `const stepped = result.step` — const, line 1382
- `const began = overviewRef.current ? beginLeave(selectionRef.current ?` — const, line 1384
- `const began = stepped.goal === 1 ? beginEnter() : beginLeave(selectionRef.current ?` — const, line 1390
- `const how = g.source === "pinch" ? "pinch" : modifiers.read(event).alt ? "alt + scroll" : "ctrl + scroll"` — const, line 1396
- `const drag = useRef<` — const, line 1410
- `const onStagePointerDown = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1411
- `const target = event.target as Element` — const, line 1412
- `const onCard = target.closest("[data-desk-slot]")` — const, line 1413
- `const onSliver = target.closest(".desk-sliver") !== null` — const, line 1415
- `const inContent = !onSliver && target.closest(".desk-slot-inner, button, input, textarea") !== null` — const, line 1416
- `const key = onCard.getAttribute("data-desk-slot-key") ?? undefined` — const, line 1419
- `const windowId = onCard.getAttribute("data-desk-slot-window") ?? undefined` — const, line 1420
- `const deskOf = onCard.getAttribute("data-desk-slot-desk") ?? undefined` — const, line 1421
- `const onStagePointerMove = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1435
- `const d = drag.current` — const, line 1436
- `const dx = event.clientX - d.x` — const, line 1438
- `const dy = event.clientY - d.y` — const, line 1439
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1458
- `const cancelDrag = useCallback(()` — const, line 1466
- `const d = drag.current` — const, line 1467
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1475
- `const cancelDragRef = useRef(cancelDrag)` — const, line 1481
- `const scrubbedClick = useRef(false)` — const, line 1484
- `const onStagePointerUp = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1485
- `const d = drag.current` — const, line 1486
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1496
- `const layout = ovLayoutRef.current` — const, line 1507
- `const stageBox = (event.currentTarget as HTMLElement).getBoundingClientRect()` — const, line 1508
- `const point =` — const, line 1510
- `const drop = dropTarget(layout, point)` — const, line 1511
- `const current = wsRef.current` — const, line 1512
- `const to = drop ? current.desks[drop.row] : null` — const, line 1513
- `const from = slotIndexOf(to, d.windowId)` — const, line 1516
- `const world = worldRef.current` — const, line 1527
- `const observer = new MutationObserver((records)` — const, line 1529
- `const node = record.target instanceof Element ? record.target : record.target.parentElement` — const, line 1531
- `const windowId = windowOfTarget(node)` — const, line 1532
- `const handle = timers.set(()` — const, line 1545
- `const body = [...document.querySelectorAll<HTMLElement>("[data-desk-window]")].find((pane)` — const, line 1548
- `const node = miniatures.get(windowId)` — const, line 1558
- `const node = host.firstElementChild as HTMLElement | null` — const, line 1561
- `const openContent = useCallback((content: ContentRefDto, options:` — const, line 1581
- `const current = wsRef.current` — const, line 1582
- `const id = deskIdRef.current` — const, line 1583
- `const step = openBeside(current, id, content, ()` — const, line 1585
- `const jump = jumps.current.get(step.windowId)` — const, line 1592
- `const handle = timers.set(()` — const, line 1598
- `const next = new Set(now)` — const, line 1601
- `const openHit = useCallback((hit:` — const, line 1611
- `const card = library?.find((entry)` — const, line 1613
- `const kind = card && isVideoCard(card) ? "video" : "source"` — const, line 1614
- `const asks = useMemo( ()` — const, line 1621
- `const shownVault = useRef<` — const, line 1631
- `const before = shownVault.current` — const, line 1633
- `const statusRef = useRef(status)` — const, line 1637
- `const companionStateRef = useRef(companionState)` — const, line 1639
- `const chipRef = useRef(chip)` — const, line 1641
- `const searchOpenRef = useRef(false)` — const, line 1643
- `const anchoredAt = useRef(0)` — const, line 1645
- `const groundingRef = useRef<Grounding>(` — const, line 1646
- `const stepCompanion = useCallback((event: CompanionEvent)` — const, line 1649
- `const before = companionStateRef.current` — const, line 1650
- `const next = companionStep(before, event)` — const, line 1651
- `const id = deskIdRef.current` — const, line 1656
- `const lastPointer = useRef<` — const, line 1661
- `const stageNode = stageRef.current` — const, line 1663
- `const onMove = (event: PointerEvent)` — const, line 1665
- `const box = stageNode.getBoundingClientRect()` — const, line 1666
- `const companionKey = (atDock: boolean)` — const, line 1675
- `let anchor: Rect | null = null` — let, line 1680
- `const id = focusIdRef.current` — const, line 1682
- `const selected: WindowSelection | null = id ? readWindowSelection(id, stageRef.current) : null` — const, line 1683
- `const companionKeyRef = useRef(companionKey)` — const, line 1693
- `const companionInit = useRef(false)` — const, line 1698
- `const opening = deskById(ws, deskId)` — const, line 1701
- `const shown: CompanionState =` — const, line 1706
- `const snapCompanion = useCallback((dock: CompanionDock)` — const, line 1712
- `const id = deskIdRef.current` — const, line 1714
- `const before = companionStateRef.current` — const, line 1716
- `const next: CompanionState =` — const, line 1717
- `const viewKey = `$` — const, line 1725
- `const lastViewKey = useRef(viewKey)` — const, line 1726
- `const stageNode = stageRef.current` — const, line 1735
- `const onScroll = (event: Event)` — const, line 1737
- `const target = event.target instanceof Element ? event.target : null` — const, line 1740
- `const onSelection = ()` — const, line 1750
- `const id = focusIdRef.current` — const, line 1751
- `const panel = companionRef.current?.rect() ?? null` — const, line 1752
- `const selected = readWindowSelection(id, stageRef.current)` — const, line 1757
- `const askCompanion = useCallback((question: string)` — const, line 1764
- `const grounding = groundingRef.current` — const, line 1765
- `const spanId = grounding.spanId ?? firstVisibleSpan(grounding.windowId ?? null)` — const, line 1767
- `const lifecycle = lifecyclesRef.current[grounding.windowId ?? ""]` — const, line 1773
- `const selected = chipRef.current` — const, line 1775
- `const loadHistory = useCallback((query: string, cursor?: string)` — const, line 1790
- `const deskTitle = useCallback((id: string | null)` — const, line 1792
- `const openClaim = useCallback((citation: Pick<TutorCitationDto, "extractionId" | "spanId"> &` — const, line 1795
- `let sourceId = citation.sourceId ?? null` — let, line 1796
- `let kind: "source" | "video" = "source"` — let, line 1797
- `const content = window.content` — const, line 1799
- `const open = (found: string, known: "source" | "video")` — const, line 1806
- `const card = library?.find((entry)` — const, line 1807
- `const shown = card && isVideoCard(card) ? "video" : known` — const, line 1808
- `const openThread = useCallback((exchange: CompanionExchange)` — const, line 1826
- `const root = exchange.answer?.readerAnswerEventId || exchange.answer?.eventId` — const, line 1827
- `const openSearchRow = useCallback((row: SearchRow)` — const, line 1834
- `const id = deskIdRef.current` — const, line 1835
- `const ref = row.ref` — const, line 1840
- `const note = row.raw as` — const, line 1848
- `const target = row.target ??` — const, line 1850
- `const passage = (row.raw as` — const, line 1859
- `const extractionId = passage && (passage.kind === "source" || passage.kind === "video") ? passage.extractionId : null` — const, line 1860
- `const refreshCarried = useCallback(()` — const, line 1869
- `const carryQuestion = useCallback((text: string, origin:` — const, line 1879
- `const openPassage = useCallback((extractionId: string, spanId: string | null, t?: number)` — const, line 1887
- `let found: ContentRefDto | null = null` — let, line 1888
- `const content = window.content` — const, line 1890
- `const ref = found.kind === "video" && t !== undefined ?` — const, line 1900
- `const sourcePieces = useCallback((): SourcePiece[]` — const, line 1906
- `const current = wsRef.current` — const, line 1907
- `const id = deskIdRef.current` — const, line 1908
- `const each = id ? deskById(current, id) : null` — const, line 1909
- `const out: SourcePiece[] = []` — const, line 1911
- `const window = current.windows[windowId]` — const, line 1913
- `const content = window?.content` — const, line 1914
- `const spanId = statusRef.current[windowId]?.readingSpan ?? firstVisibleSpan(windowId)` — const, line 1916
- `const element = document.querySelector(`[$` — const, line 1918
- `const text = (element?.textContent ?? "").replace(/\s+/g, " ").trim().slice(0, 600)` — const, line 1919
- `const title = titleOf(window)` — const, line 1921
- `const padsHost = useMemo<PadsHost>(()` — const, line 1927
- `let job = await padsTransport.figureRequest(` — let, line 1942
- `const figure = job.result?.figure` — const, line 1947
- `const window = wsRef.current.windows[windowId]` — const, line 1954
- `const focusedStack = (): PadStackHandle | null` — const, line 1966
- `const focusedStackRef = useRef(focusedStack)` — const, line 1967
- `const newPadBeside = useCallback(()` — const, line 1971
- `const id = deskIdRef.current` — const, line 1972
- `const selected = focusIdRef.current ? readWindowSelection(focusIdRef.current, stageRef.current) : null` — const, line 1974
- `const padId = mintId("pad")` — const, line 1975
- `const title = selected ? `Scratchpad · “$` — const, line 1976
- `const refused = store.commitPad(padId, [` — const, line 1977
- `const newPadBesideRef = useRef(newPadBeside)` — const, line 1984
- `const deskPadIds = useCallback((id: string | null): string[]` — const, line 1988
- `const runningPadOf = useCallback((id: string | null): string | null` — const, line 1994
- `const answerProposals = useCallback((exchange: CompanionExchange): ProposedDiff[]` — const, line 2001
- `const answer = exchange.answer` — const, line 2002
- `const known = runningPadOf(exchange.deskId)` — const, line 2003
- `const lines = answer.answerMd.split("\n").map((line)` — const, line 2005
- `const padId = runningPadOf(exchange.deskId)` — const, line 2013
- `const now = padId ? store.pads[padId] : null` — const, line 2014
- `const refused = store.commitPad(padId, [` — const, line 2016
- `const drainWrite = useCallback((padId: string, op: "keep" | "unkeep", version: number)` — const, line 2026
- `const refused = store.commitPad(padId, [` — const, line 2028
- `const padLinks = useMemo<PadLink[]>(()` — const, line 2033
- `const surfacedCarried = useRef(new Set<string>())` — const, line 2037
- `const onCarriedSurfaced = useCallback((question: CarriedQuestionDto)` — const, line 2038
- `const viewTimers = useRef(new Map<string,` — const, line 2046
- `const shellTimers = useRef(new Set<unknown>())` — const, line 2047
- `const statusFor = useMemo(()` — const, line 2059
- `const onStatusFor = useCallback((windowId: string)` — const, line 2060
- `let handler = statusFor.get(windowId)` — let, line 2061
- `const previous = viewTimers.current.get(windowId)` — const, line 2070
- `const save = ()` — const, line 2072
- `const current = store.ws` — const, line 2073
- `const window = current.windows[windowId]` — const, line 2074
- `const jumpReadyFor = useMemo(()` — const, line 2092
- `const onJumpReadyFor = useCallback((windowId: string)` — const, line 2093
- `let handler = jumpReadyFor.get(windowId)` — let, line 2094
- `const pending = pendingJump.current.get(windowId)` — const, line 2102
- `const mediaReadyFor = useMemo(()` — const, line 2113
- `const onMediaReadyFor = useCallback((windowId: string)` — const, line 2114
- `let handler = mediaReadyFor.get(windowId)` — let, line 2115
- `const railNodeFor = useMemo(()` — const, line 2126
- `const onRailNode = useCallback((windowId: string)` — const, line 2127
- `let handler = railNodeFor.get(windowId)` — let, line 2128
- `const railPanelOf = useCallback((deskOf: string, extractionId: string): string | null` — const, line 2137
- `const desk = deskById(ws, deskOf)` — const, line 2139
- `const panels = desk.slots.flat().filter((id)` — const, line 2141
- `const content = ws.windows[id]?.content` — const, line 2142
- `const claimed = railClaims[`$` — const, line 2145
- `const sourceWindowOf = useCallback((deskOf: string, extractionId: string): string | null` — const, line 2149
- `const desk = deskById(ws, deskOf)` — const, line 2151
- `const content = ws.windows[id]?.content` — const, line 2154
- `const undoShown = undo && undo.deskId === deskId && undo.until > timers.now() && (ws?.closed[undo.deskId] ?? []).some((entry)` — const, line 2162
- `const handle = timers.set(()` — const, line 2166
- `const paneBody = (window: DeskWindow, lifecycle: WindowLifecycle): ReactNode` — const, line 2180
- `const content = window.content` — const, line 2181
- `const card = content && (content.kind === "source" || content.kind === "video") ? library?.find((entry)` — const, line 2182
- `const stack = window.stack ?? (content?.kind === "pad" ? [` — const, line 2185
- `const railPanel = railPanelOf(window.deskId, content.extractionId)` — const, line 2192
- `const railNode = railPanel ? railHosts[railPanel] ?? null : null` — const, line 2193
- `const railContent = railPanel ? ws.windows[railPanel]?.content : null` — const, line 2194
- `const railTab = railContent?.kind === "panel" && railContent.panel === "notes" ? "notes" : "guide"` — const, line 2195
- `const extractionId = content.extractionId ?? ""` — const, line 2213
- `const owner = railPanelOf(window.deskId, extractionId)` — const, line 2214
- `const target = content.extractionId ? sourceWindowOf(window.deskId, content.extractionId) : null` — const, line 2231
- `const jump = jumps.current.get(target)` — const, line 2234
- `const linkedFrom = overview || zooming ? selection?.windowId ?? focusId : null` — const, line 2258
- `const selectedRelations = relatedTo(linkedFrom)` — const, line 2259
- `const linkRects = new Map<string, Rect>()` — const, line 2260
- `const rect = ovLayout?.cards[row]?.[index]` — const, line 2262
- `const fromCard = linkedFrom ? linkRects.get(linkedFrom) ?? null : null` — const, line 2265
- `const links = fromCard ? curvedLinks(fromCard, selectedRelations.filter((relation)` — const, line 2266
- `const ghosts: Array<` — const, line 2269
- `const row = ws.desks.findIndex((each)` — const, line 2271
- `const each = ws.desks[row]` — const, line 2272
- `const sameDesk = selectedRelations.filter((relation)` — const, line 2274
- `const linked = slot.some((id)` — const, line 2278
- `const movedShown = movedNotice && movedNotice.deskId === deskId && movedNotice.until > timers.now() ? movedNotice : null` — const, line 2283
- `const focusWindow = focusId ? ws.windows[focusId] : undefined` — const, line 2284
- `const thread = asks.thread(deskId)` — const, line 2286
- `const grounding: Grounding = groundingFor(ws, chip, focusWindow, status)` — const, line 2287
- `const focusZoom = typeof focusWindow?.view?.zoom === "number" ? (focusWindow.view.zoom as number) : 1` — const, line 2289
- `const windowPlaces = ws.desks.flatMap((each, rowIndex)` — const, line 2292
- `const eachCam = camX[each.deskId] ?? 0` — const, line 2293
- `const rects = slotRects(each.slots.length, stage)` — const, line 2294
- `const top = rowTop(rowIndex, stage) - rowTop(deskIndex, stage)` — const, line 2295
- `const slotReading =` — const, line 2297
- `const slotCard = ovLayout?.cards[rowIndex]?.[index] ?? slotReading` — const, line 2298
- `const readingPanes = paneRects(slotReading, slot.length)` — const, line 2299
- `const cardPanes = paneRects(slotCard, slot.length)` — const, line 2300
- `const window = ws.windows[id]` — const, line 2302
- `const sliverDesk = leaveTarget ? deskById(ws, leaveTarget.deskId) : desk` — const, line 2309
- `const sliverCam = leaveTarget && sliverDesk ? leaveTarget.cams[sliverDesk.deskId] ?? 0 : cam` — const, line 2310
- `const slivers = sliverDesk && !focusMode ? sliverSlots(sliverCam, sliverDesk.slots.length, stage) :` — const, line 2311
- `const shelfRows: ShelfRow[] = desk ? desk.slots.flatMap((slot, index)` — const, line 2312
- `const window = ws.windows[id]` — const, line 2314
- `const kind = window?.kind ?? "source"` — const, line 2315
- `const hints = overview ? [["h j k l", "select"], ["↵ / click", "open"], ["alt+↵", "open in focus"], ["alt+[ ]", "move"], ["alt+shift+j/k", "to a desk"], ["drag", "move a card"], ["b", "relations"], ["g", "hold: gather"], ["o / esc", "back"]] : focusMode ? [["…` — const, line 2329
- `const title = (event.target as HTMLInputElement).value.trim()` — const, line 2351
- `const id = mintId("desk")` — const, line 2377
- `const id = window.windowId` — const, line 2434
- `const onCurrent = each.deskId === deskId` — const, line 2435
- `const opened = visited.has(each.deskId) || onCurrent` — const, line 2436
- `const full = (!overview && onCurrent && focusMode && id === focusId) || (leaveTarget?.focusWindowId === id && leaveTarget.deskId === each.deskId)` — const, line 2437
- `const hiddenInFocus = !overview && onCurrent && focusMode && !full` — const, line 2438
- `const reading = full ?` — const, line 2439
- `const card = place.card` — const, line 2440
- `const box = overview ? card : reading` — const, line 2441
- `const leavingTo = leaveTarget?.deskId === each.deskId` — const, line 2442
- `const slotCut = leavingTo ? slotVisibility(leaveTarget.cams[each.deskId] ?? 0, each.slots.length, stage)[index] : onCurrent ? visibility[index] : null` — const, line 2443
- `const mask = full || focusMode || !slotCut ? null : leavingTo || (!overview && !zooming && onCurrent) ? softCropMask(slotCut, reading.w) : null` — const, line 2446
- `const lifecycle = lifecycles[id] ??` — const, line 2447
- `const paused = isPaused(lifecycle.state)` — const, line 2448
- `const paired = slot.length > 1` — const, line 2449
- `const selected = overview && selection !== null && slot.includes(selection.windowId)` — const, line 2450
- `const receding = overview && recedes(slot, selection?.windowId ?? null, selectedRelations, showRelations)` — const, line 2451
- `const measure = FOCUS_MEASURE[window.kind] ?? FOCUS_MEASURE.source` — const, line 2452
- `const title = titleOf(window)` — const, line 2506
- `const ringId = linkedFrom` — const, line 2588
- `const isSel = ringId !== null && slot.includes(ringId)` — const, line 2589
- `const isRel = !isSel && showRelations && slot.some((id)` — const, line 2590
- `const rect = ovLayout?.cards[rowIndex]?.[index]` — const, line 2591
- `const key = slotKey(each.deskId, slot)` — const, line 2593
- `const content = ws.windows[id]?.content` — const, line 2635
- `const stackWindow = Object.values(wsRef.current.windows).find((window)` — const, line 2641
- `function Sliver(` — function, line 2777
- `function WhichKey()` — function, line 2787
- `const groups: Array<` — const, line 2788
- `const rows = DESK_BINDINGS.filter((binding)` — const, line 2799
- `function OpenBeside(` — function, line 2817
- `const words = filter.trim().toLowerCase()` — const, line 2833
- `const sources = (library ?? []).filter((card)` — const, line 2834
- `const book = focus?.content && (focus.content.kind === "source" || focus.content.kind === "video") ? focus.content : null` — const, line 2835

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: dynamic import; no named call claim
- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `DeskDebugHandle`, `DeskShell`; references `DeskDebugHandle`, `DeskShell`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — dynamic import; imports `CarriedQuestionDto`, `CompanionDock`, `CompanionHistoryDto`, `ContentRefDto`, `DeskApplyDto`, `DeskApplyInput`, `DeskStateDto`, `PadDrainDto`, `SourceLibraryCard`, `TutorCitationDto`
- [[Reference/Desktop/TypeScript/api/poller|src/api/poller.ts]] — import-or-re-export; imports `Poller`, `appPoller`
- [[Reference/Desktop/TypeScript/app/ScreenErrorBoundary|src/app/ScreenErrorBoundary.tsx]] — import-or-re-export; imports `ScreenErrorBoundary`
- [[Reference/Desktop/TypeScript/screens/desks/Shelf|src/screens/desks/Shelf.tsx]] — import-or-re-export; imports `Shelf`, `ShelfRow`
- [[Reference/Desktop/TypeScript/screens/desks/companion/Companion|src/screens/desks/companion/Companion.tsx]] — import-or-re-export; imports `Companion`, `CompanionHandle`
- [[Reference/Desktop/TypeScript/screens/desks/companion/DiffProposal|src/screens/desks/companion/DiffProposal.tsx]] — import-or-re-export; imports `ProposedDiff`
- [[Reference/Desktop/TypeScript/screens/desks/companion/asks|src/screens/desks/companion/asks.ts]] — import-or-re-export; imports `CompanionApi`, `CompanionAsks`, `CompanionExchange`, `companionAsksFor`, `forgetCompanionAsks`
- [[Reference/Desktop/TypeScript/screens/desks/companion/model|src/screens/desks/companion/model.ts]] — import-or-re-export; imports `CompanionEvent`, `CompanionState`, `HIDDEN`, `avoidOffset`, `companionStep`
- [[Reference/Desktop/TypeScript/screens/desks/geometry|src/screens/desks/geometry.ts]] — import-or-re-export; imports `DESK_SIZES`, `FOCUS_MEASURE`, `Rect`, `Stage`, `ensureVisible`, `paneRects`, `rowTop`, `sliverSlots`, `slotRects`, `slotVisibility`, `slotWidth`, `softCropMask`, `stepZoom`
- [[Reference/Desktop/TypeScript/screens/desks/keys/listeners|src/screens/desks/keys/listeners.ts]] — import-or-re-export; imports `DeskListenerRouter`, `WINDOW_ATTRIBUTE`, `windowOfTarget`
- [[Reference/Desktop/TypeScript/screens/desks/keys/router|src/screens/desks/keys/router.ts]] — import-or-re-export; imports `BareAltTracker`, `DESK_BINDINGS`, `DeskAction`, `ModifierTracker`, `REAL_TIMERS`, `Timers`, `isTypingTarget`, `resolveKey`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `ClaimedScope`, `ListenerHub`, `ScopeClaims`, `WindowLifecycle`, `WindowScope`, `isPaused`, `windowState`
- [[Reference/Desktop/TypeScript/screens/desks/model/workspace|src/screens/desks/model/workspace.ts]] — import-or-re-export; imports `DeskWindow`, `Step`, `Workspace`, `closeWindow`, `createDesk`, `deskById`, `focusAlong`, `focusPane`, `focusedSlot`, `focusedWindowId`, `moveFocused`, `moveToDesk`, `moveToDeskAt`, `moveWindowTo`, `openBeside`, `openStackBeside`, `pairFocused`, `renameDesk`, `reorderSlots`, `setCompanionDock`, `setCompanionShown`, `setFocus`, `setView`, `slotIndexOf`, `swapInView`, `undoClose`, `unpairFocused`
- [[Reference/Desktop/TypeScript/screens/desks/outbox|src/screens/desks/outbox.ts]] — import-or-re-export; imports `OutboxTransport`, `clientIdFor`
- [[Reference/Desktop/TypeScript/screens/desks/overview/Card|src/screens/desks/overview/Card.tsx]] — import-or-re-export; imports `CardFace`, `LinkLayer`
- [[Reference/Desktop/TypeScript/screens/desks/overview/controller|src/screens/desks/overview/controller.ts]] — import-or-re-export; imports `ANIMATION_FRAMES`, `FrameClock`, `SlotElements`, `ZoomController`, `ZoomPlan`, `cameraTransform`
- [[Reference/Desktop/TypeScript/screens/desks/overview/engine|src/screens/desks/overview/engine.ts]] — import-or-re-export; imports `Camera`, `IDENTITY`, `OVERVIEW`, `ZoomGesture`, `ZoomSource`, `classifyWheel`, `dragProgress`, `dropTarget`, `enteringCamera`, `followSelection`, `moveSelection`, `newZoomGesture`, `normalizedDelta`, `overviewLayout`, `zoomWheel`
- [[Reference/Desktop/TypeScript/screens/desks/overview/links|src/screens/desks/overview/links.ts]] — import-or-re-export; imports `DRAWN_RELATIONS`, `Relation`, `curvedLinks`, `gatherOrder`, `relationsOf`
- [[Reference/Desktop/TypeScript/screens/desks/overview/miniature|src/screens/desks/overview/miniature.ts]] — import-or-re-export; imports `MiniatureBook`, `cloneForMiniature`
- [[Reference/Desktop/TypeScript/screens/desks/pads/DrainPanel|src/screens/desks/pads/DrainPanel.tsx]] — import-or-re-export; imports `DrainPanel`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] — import-or-re-export; imports `PadStackWindow`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PassageMarks|src/screens/desks/pads/PassageMarks.tsx]] — import-or-re-export; imports `PadLink`, `PassageMarks`
- [[Reference/Desktop/TypeScript/screens/desks/pads/host|src/screens/desks/pads/host.ts]] — import-or-re-export; imports `PadStackHandle`, `PadsApi`, `PadsHost`, `PadsHostContext`, `SourcePiece`, `localDay`
- [[Reference/Desktop/TypeScript/screens/desks/pads/model|src/screens/desks/pads/model.ts]] — import-or-re-export; imports `keyAfter`
- [[Reference/Desktop/TypeScript/screens/desks/search/SearchPanel|src/screens/desks/search/SearchPanel.tsx]] — import-or-re-export; imports `SearchApi`, `SearchPanel`
- [[Reference/Desktop/TypeScript/screens/desks/search/model|src/screens/desks/search/model.ts]] — import-or-re-export; imports `SearchRow`
- [[Reference/Desktop/TypeScript/screens/desks/selection|src/screens/desks/selection.ts]] — import-or-re-export; imports `WindowSelection`, `clipQuote`, `readWindowSelection`
- [[Reference/Desktop/TypeScript/screens/desks/store|src/screens/desks/store.ts]] — import-or-re-export; imports `deskStoreFor`
- [[Reference/Desktop/TypeScript/screens/desks/windows/PanelWindow|src/screens/desks/windows/PanelWindow.tsx]] — import-or-re-export; imports `LibraryPanel`, `PANEL_TITLES`, `PathPanel`, `RailHostPanel`
- [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] — import-or-re-export; imports `ReaderPassThrough`, `SourceStatus`, `SourceWindow`
- [[Reference/Desktop/TypeScript/screens/desks/windows/ThreadWindow|src/screens/desks/windows/ThreadWindow.tsx]] — import-or-re-export; imports `ThreadWindow`
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

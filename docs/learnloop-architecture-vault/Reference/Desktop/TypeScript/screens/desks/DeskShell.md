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
| Source lines | 2837 |
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
- `export const LIVE_DESK_TRANSPORT: DeskTransport =` — const, line 128
- `export interface PadsTransport extends PadsApi` — interface, line 190
- `export const LIVE_PADS_TRANSPORT: PadsTransport =` — const, line 198
- `export interface CompanionTransport extends CompanionApi, SearchApi` — interface, line 215
- `export const LIVE_COMPANION_TRANSPORT: CompanionTransport =` — const, line 219
- `export interface PaneRenderInput` — interface, line 229
- `export interface DeskDebugHandle` — interface, line 245
- `export const KIND_GLYPH: Record<string, string> =` — const, line 280
- `export interface DeskShellProps` — interface, line 333
- `export function DeskShell(` — function, line 362
- `export function isVideoCard(card: SourceLibraryCard): boolean` — function, line 2717
- `export function contentForCard(card: SourceLibraryCard, extractionId: string): ContentRefDto` — function, line 2721

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
- `const COMPANION_SIZES_HANDOFF_MS = 250` — const, line 140
- `interface Grounding` — interface, line 143
- `function groundingFor(ws: Workspace, chip:` — function, line 150
- `const content = ws.windows[chip.windowId]?.content` — const, line 152
- `const content = focus?.content` — const, line 157
- `const span = status[focus.windowId]?.readingSpan ?? (typeof focus.view?.spanId === "string" ? (focus.view.spanId as string) : undefined)` — const, line 161
- `function firstVisibleSpan(windowId: string | null): string | null` — function, line 168
- `const host = document.querySelector(`[$` — const, line 170
- `const top = host.getBoundingClientRect().top` — const, line 172
- `const spans = [...host.querySelectorAll<HTMLElement>("[data-span-id], [data-transcript-span]")]` — const, line 173
- `const visible = spans.find((element)` — const, line 174
- `function keyAfterLast(blocks: Array<` — function, line 179
- `function threadTitle(thread: CompanionExchange[]): string` — function, line 183
- `const last = thread[thread.length - 1]` — const, line 184
- `const UNDO_CLOSE_MS = 9_000` — const, line 236
- `const TOAST_MS = 2_200` — const, line 238
- `const VIEW_SAVE_IDLE_MS = 2_000` — const, line 240
- `const MOVED_NOTICE_MS = 6_000` — const, line 242
- `function displayedCamera(world: HTMLElement): Camera | null` — function, line 255
- `const shown = typeof getComputedStyle === "function" ? getComputedStyle(world).transform : ""` — const, line 256
- `const match = /^matrix\(([^)]+)\)$/.exec(shown ?? "")` — const, line 257
- `function prefersReducedMotion(): boolean` — function, line 263
- `function slotKey(deskId: string, slot: string[]): string` — function, line 272
- `function intersects(rect: Rect, stage: Stage): boolean` — function, line 276
- `const KIND_WORD: Record<string, string> =` — const, line 292
- `function defaultMintId(prefix: string): string` — function, line 304
- `function shortName(title: string): string` — function, line 312
- `const words = title.split(/\s+/).filter(Boolean)` — const, line 313
- `function readStored(key: string): string | null` — function, line 317
- `function writeStored(key: string, value: string): void` — function, line 325
- `const store = useMemo( ()` — const, line 382
- `const storeWs = useSyncExternalStore(store.subscribe, store.getSnapshot)` — const, line 386
- `const ws: Workspace | null = storeReady ? storeWs : null` — const, line 390
- `const wsRef = useMemo(()` — const, line 391
- `const deskKey = `learnloop.desks.current.$` — const, line 393
- `const stageRef = useRef<HTMLElement | null>(null)` — const, line 408
- `const viewport = initialViewport ??` — const, line 410
- `const shelf = viewport.width < DESK_SIZES.shelfFoldBelow ? DESK_SIZES.shelfRail : DESK_SIZES.shelf` — const, line 411
- `const padHandles = useRef(new Map<string, PadStackHandle>())` — const, line 437
- `const drainingRef = useRef(false)` — const, line 440
- `const companionRef = useRef<CompanionHandle | null>(null)` — const, line 442
- `const preOverview = useRef<` — const, line 445
- `const worldRef = useRef<HTMLDivElement | null>(null)` — const, line 446
- `const boxEls = useRef(new Map<string, HTMLElement>())` — const, line 449
- `const innerEls = useRef(new Map<string, HTMLElement>())` — const, line 450
- `const cardEls = useRef(new Map<string, HTMLElement>())` — const, line 451
- `const ringEls = useRef(new Map<string, HTMLElement>())` — const, line 452
- `const slotElements = useCallback((): Map<string, SlotElements>` — const, line 453
- `const out = new Map<string, SlotElements>()` — const, line 454
- `const lateEls = useRef(new Map<string, HTMLElement>())` — const, line 458
- `const sliverEls = useRef(new Map<string, HTMLElement>())` — const, line 459
- `const miniatures = useMemo(()` — const, line 460
- `const miniHosts = useRef(new Map<string, HTMLDivElement>())` — const, line 461
- `const onEndRef = useRef<(goal: 0 | 1, base: 0 | 1)` — const, line 462
- `const controller = useMemo(()` — const, line 463
- `const jumps = useRef(new Map<string, (spanId: string)` — const, line 464
- `const media = useRef(new Map<string, ()` — const, line 465
- `const pendingJump = useRef(new Map<string, string>())` — const, line 466
- `const toastNow = useCallback((text: string)` — const, line 468
- `const handle = timers.set(()` — const, line 471
- `const setCurrentDeskId = useCallback((deskId: string | null)` — const, line 477
- `const commit = useCallback((step: Step)` — const, line 482
- `const total = notice.dropped + notice.lost` — const, line 491
- `const chain = useCallback((first: Step, next: (ws: Workspace)` — const, line 497
- `const second = next(first.ws)` — const, line 498
- `const firstRun = useCallback(async (base: Workspace, cards: SourceLibraryCard[] | null): Promise<Step>` — const, line 502
- `const card = firstSourceId ? cards?.find((entry)` — const, line 503
- `const deskId = mintId("desk")` — const, line 504
- `const created = createDesk(base, deskId, card ? `new desk · $` — const, line 505
- `const extractionId = await transport.resolveExtraction(card.sourceId).catch(()` — const, line 507
- `let live = true` — let, line 513
- `const desk = ws ? deskById(ws, currentDeskId) ?? ws.desks[0] ?? null : null` — const, line 535
- `const deskId = desk?.deskId ?? null` — const, line 536
- `const focusId = ws && desk ? focusedWindowId(ws, desk) : null` — const, line 537
- `const focusSlotIndex = ws && desk ? focusedSlot(ws, desk) : -1` — const, line 538
- `const slotCount = desk?.slots.length ?? 0` — const, line 546
- `const keepPrevious = useRef(false)` — const, line 547
- `const next = ensureVisible(cams[deskId] ?? 0, focusSlotIndex, slotCount, stage, keepPrevious.current)` — const, line 551
- `const node = stageRef.current` — const, line 559
- `const measure = ()` — const, line 560
- `const next =` — const, line 562
- `const now = stageNow.current` — const, line 563
- `const shell = node?.closest(".desk-shell") as HTMLElement | null` — const, line 570
- `const observer = typeof ResizeObserver === "undefined" || !node ? null : new ResizeObserver(measure)` — const, line 574
- `const cam = deskId ? camX[deskId] ?? 0 : 0` — const, line 583
- `const visibility = useMemo(()` — const, line 584
- `const deskIndex = ws && desk ? ws.desks.indexOf(desk) : 0` — const, line 585
- `const lifecycles = useMemo(()` — const, line 589
- `const out: Record<string, WindowLifecycle> =` — const, line 590
- `const onCurrent = each.deskId === deskId` — const, line 593
- `const activeWindowId = Object.values(lifecycles).find((each)` — const, line 609
- `const held = document.activeElement` — const, line 611
- `const owner = held && held !== document.body ? windowOfTarget(held) : null` — const, line 612
- `const target = activeWindowId ? document.querySelector<HTMLElement>(`[$` — const, line 614
- `const lifecyclesRef = useRef(lifecycles)` — const, line 620
- `const focusIdRef = useRef(focusId)` — const, line 622
- `const focusModeRef = useRef(focusMode)` — const, line 630
- `const switchDesk = useCallback((direction: -1 | 1): boolean` — const, line 633
- `const current = wsRef.current` — const, line 634
- `const index = current.desks.findIndex((each)` — const, line 635
- `const next = current.desks[index + direction]` — const, line 636
- `const deskIdRef = useRef(deskId)` — const, line 641
- `const titleOf = useCallback((window: DeskWindow | undefined): string` — const, line 644
- `const known = status[window.windowId]?.title` — const, line 646
- `const content = window.content` — const, line 648
- `const ovLayout = useMemo(()` — const, line 658
- `const ovLayoutRef = useRef(ovLayout)` — const, line 659
- `const stageNow = useRef(stage)` — const, line 661
- `const camXRef = useRef(camX)` — const, line 663
- `const overviewRef = useRef(overview)` — const, line 665
- `const ovCamRef = useRef(ovCam)` — const, line 667
- `const selectionRef = useRef(selection)` — const, line 669
- `const visitedRef = useRef(visited)` — const, line 671
- `const showRelationsRef = useRef(showRelations)` — const, line 673
- `const reduced = reducedMotion ?? prefersReducedMotion()` — const, line 675
- `const transitionGen = useRef(0)` — const, line 678
- `const panEaseRef = useRef(panEase)` — const, line 679
- `const pendingLeave = useRef<` — const, line 681
- `const cardOf = useCallback((windowId: string | null | undefined): Rect | null` — const, line 684
- `const layout = ovLayoutRef.current` — const, line 685
- `const current = wsRef.current` — const, line 686
- `const index = slotIndexOf(each, windowId)` — const, line 689
- `const readingRectOf = useCallback((current: Workspace, row: number, index: number, readingRow: number, cams: Record<string, number>, st: Stage): Rect` — const, line 697
- `const each = current.desks[row]` — const, line 698
- `const rect = slotRects(each.slots.length, st)[index]` — const, line 699
- `const relatedTo = useCallback((windowId: string | null | undefined): Relation[]` — const, line 703
- `const recedes = useCallback((slot: string[], selected: string | null, related: Relation[], relationsOn: boolean): boolean` — const, line 706
- `const planZoom = useCallback((base: 0 | 1, readingDeskId: string, cams: Record<string, number>, selected: string | null, B: Camera, fullWindowId: string | null = null): ZoomPlan | null` — const, line 711
- `const current = wsRef.current` — const, line 712
- `const layout = ovLayoutRef.current` — const, line 713
- `const st = stageNow.current` — const, line 714
- `const readingRow = Math.max(0, current.desks.findIndex((each)` — const, line 716
- `const related = relatedTo(selected)` — const, line 717
- `const items: ZoomPlan["items"] = []` — const, line 718
- `const rings: ZoomPlan["rings"] = []` — const, line 719
- `const a = readingRectOf(current, row, index, readingRow, cams, st)` — const, line 721
- `const b = layout.cards[row][index]` — const, line 722
- `const readingPanes = paneRects(a, slot.length)` — const, line 723
- `const cardPanes = paneRects(b, slot.length)` — const, line 724
- `const live = visitedRef.current.has(each.deskId) && each.deskId === readingDeskId && intersects(a, st)` — const, line 725
- `const recede = recedes(slot, selected, related, showRelationsRef.current)` — const, line 726
- `const focus = selected !== null && slot.includes(selected)` — const, line 727
- `const isRelated = showRelationsRef.current && slot.some((id)` — const, line 728
- `const pa = id === fullWindowId && each.deskId === readingDeskId ?` — const, line 731
- `const pb = cardPanes[pane]` — const, line 732
- `const zoomTargets = useCallback(()` — const, line 740
- `const crossfade = useCallback((enter: boolean, to:` — const, line 752
- `const world = worldRef.current` — const, line 754
- `const id = deskIdRef.current` — const, line 760
- `const target = to ?? (preOverview.current ?` — const, line 769
- `const beginEnter = useCallback((): boolean` — const, line 780
- `const id = deskIdRef.current` — const, line 782
- `const selected = focusIdRef.current` — const, line 790
- `const B = enteringCamera(cardOf(selected), stageNow.current)` — const, line 792
- `const plan = planZoom(0, id, camXRef.current, selected, B)` — const, line 797
- `const beginLeave = useCallback((to:` — const, line 805
- `const shown = displayedCamera(worldRef.current) ?? ovCamRef.current` — const, line 815
- `const target = to ?? preOverview.current ?? (selectionRef.current ?` — const, line 821
- `const deskIdTo = target.deskId` — const, line 823
- `const windowTo = "windowId" in target ? target.windowId : target.focusId` — const, line 824
- `const current = wsRef.current` — const, line 825
- `const each = deskById(current, deskIdTo)` — const, line 826
- `const fullWindowId = focusAfter && windowTo ? windowTo : null` — const, line 828
- `const node = stageRef.current` — const, line 837
- `const cams =` — const, line 841
- `const index = windowTo ? slotIndexOf(each, windowTo) : -1` — const, line 842
- `const plan = planZoom(1, deskIdTo, cams, windowTo, ovCamRef.current, fullWindowId)` — const, line 844
- `const plan = controller.plan` — const, line 860
- `const leave = pendingLeave.current` — const, line 878
- `const generation = transitionGen.current` — const, line 892
- `const toggleOverview = useCallback((to:` — const, line 901
- `const focusWindow = focusId ? ws.windows[focusId] : null` — const, line 918
- `const first = ws.desks.find((each)` — const, line 923
- `const windowId = first ? first.slots[0].find((id)` — const, line 924
- `const followMoved = useRef(false)` — const, line 928
- `const rect = cardOf(selection.windowId)` — const, line 932
- `const moveOverviewSelection = useCallback((direction: "left" | "right" | "up" | "down")` — const, line 939
- `const layout = ovLayoutRef.current` — const, line 940
- `const current = wsRef.current` — const, line 941
- `const sel = selectionRef.current` — const, line 942
- `let row = sel ? current.desks.findIndex((each)` — let, line 944
- `let slot = sel ? slotIndexOf(current.desks[row] ?? current.desks[0], sel.windowId) : 0` — let, line 945
- `const next = moveSelection(layout,` — const, line 950
- `const each = current.desks[next.row]` — const, line 951
- `const windowId = each?.slots[next.slot]?.find((id)` — const, line 952
- `const gather = useCallback((toNewDesk: boolean)` — const, line 960
- `const current = wsRef.current` — const, line 961
- `const id = deskIdRef.current` — const, line 962
- `const focus = focusIdRef.current` — const, line 963
- `const each = id ? deskById(current, id) : null` — const, line 964
- `const related = relationsOf(current, focus).filter((relation)` — const, line 971
- `const moving = [focus, ...related.slice(0, DRAWN_RELATIONS).map((relation)` — const, line 984
- `const newDeskId = mintId("desk")` — const, line 985
- `const title = `gathered · $` — const, line 986
- `let step = createDesk(current, newDeskId, title)` — let, line 987
- `let after: string | null = null` — let, line 988
- `const next = moveToDesk(step.ws, id, windowId, newDeskId, after)` — const, line 990
- `const focused = setFocus(step.ws, newDeskId, focus)` — const, line 994
- `const run = useCallback((action: DeskAction): boolean` — const, line 1002
- `const current = wsRef.current` — const, line 1003
- `const id = deskIdRef.current` — const, line 1004
- `const focus = focusIdRef.current` — const, line 1006
- `const stack = focusedStackRef.current()` — const, line 1013
- `const step = focusPane(current, id, action.direction)` — const, line 1015
- `const sel = overviewRef.current ? selectionRef.current : null` — const, line 1021
- `const each = deskById(current, sel.deskId)` — const, line 1023
- `const index = each ? slotIndexOf(each, sel.windowId) : -1` — const, line 1024
- `const sel = selectionRef.current` — const, line 1035
- `const row = current.desks.findIndex((each)` — const, line 1037
- `const to = current.desks[row + action.direction]` — const, line 1038
- `const from = current.desks[row]` — const, line 1039
- `const index = slotIndexOf(from, sel.windowId)` — const, line 1041
- `const sel = selectionRef.current` — const, line 1054
- `const title = titleOf(current.windows[focus])` — const, line 1078
- `const window = current.windows[focus]` — const, line 1093
- `const zoom = typeof window?.view?.zoom === "number" ? (window.view.zoom as number) : 1` — const, line 1094
- `const next = stepZoom(zoom, action.direction)` — const, line 1095
- `const desk = deskById(current, id)` — const, line 1101
- `const index = slotIndexOf(desk, focus)` — const, line 1103
- `const shown = visibilityRef.current.filter((slot)` — const, line 1104
- `const other = shown.find((slot)` — const, line 1105
- `const toggle = focus ? media.current.get(focus) : undefined` — const, line 1110
- `const stack = focusedStackRef.current()` — const, line 1116
- `const stack = focusedStackRef.current()` — const, line 1122
- `const stack = focusedStackRef.current()` — const, line 1128
- `const stack = focusedStackRef.current()` — const, line 1134
- `const stack = focusedStackRef.current()` — const, line 1141
- `const visibilityRef = useRef(visibility)` — const, line 1157
- `const runRef = useRef(run)` — const, line 1159
- `const modifiers = useMemo(()` — const, line 1164
- `const altTracker = useMemo( ()` — const, line 1165
- `const router = useMemo(()` — const, line 1169
- `const current = wsRef.current` — const, line 1174
- `const id = deskIdRef.current` — const, line 1175
- `const owner = current.windows[windowId]` — const, line 1177
- `const outcome = altTracker.release(event)` — const, line 1205
- `const open = claimed.current.get(focusIdRef.current ?? "")` — const, line 1214
- `const has = (scope: ClaimedScope)` — const, line 1215
- `const resolution = resolveKey(event,` — const, line 1216
- `const claimed = useRef(new Map<string, Map<ClaimedScope, Set<string>>>())` — const, line 1240
- `const claimsByWindow = useRef(new Map<string, ScopeClaims>())` — const, line 1241
- `const claimsFor = useCallback((windowId: string): ScopeClaims` — const, line 1242
- `let claims = claimsByWindow.current.get(windowId)` — let, line 1243
- `const byScope = claimed.current.get(windowId) ?? new Map<ClaimedScope, Set<string>>()` — const, line 1247
- `const owners = byScope.get(scope) ?? new Set<string>()` — const, line 1248
- `const hubs = useRef(new Map<string, ListenerHub>())` — const, line 1259
- `const hubFor = useCallback((windowId: string): ListenerHub` — const, line 1260
- `let hub = hubs.current.get(windowId)` — let, line 1261
- `const world = worldRef.current` — const, line 1273
- `const mainRef = useRef<HTMLElement | null>(null)` — const, line 1278
- `const gesture = useRef<` — const, line 1279
- `const endGesture = useCallback(()` — const, line 1280
- `const g = gesture.current` — const, line 1281
- `const current = wsRef.current` — const, line 1291
- `const id = deskIdRef.current` — const, line 1292
- `const each = id ? deskById(current, id) : null` — const, line 1293
- `const st = stageNow.current` — const, line 1295
- `const rects = slotRects(each.slots.length, st)` — const, line 1296
- `const cam = camXRef.current[id] ?? 0` — const, line 1297
- `let best = 0` — let, line 1298
- `const snapped = ensureVisible(rects[best].x - DESK_SIZES.side, best, each.slots.length, st)` — const, line 1302
- `const target = each.slots[best].find((windowId)` — const, line 1304
- `const main = mainRef.current` — const, line 1310
- `const onWheel = (event: WheelEvent)` — const, line 1312
- `const target = event.target as Element | null` — const, line 1313
- `const st = stageNow.current` — const, line 1318
- `const now = performance.now()` — const, line 1319
- `let g = gesture.current` — let, line 1320
- `const kind = classifyWheel(event, modifiers.read(), st.height)` — const, line 1324
- `const ovPlain = overviewRef.current && kind.kind !== "zoom"` — const, line 1326
- `const id = deskIdRef.current` — const, line 1352
- `const each = id ? deskById(wsRef.current, id) : null` — const, line 1353
- `const travel = Math.abs(dx) > Math.abs(dy) ? dx : dy` — const, line 1355
- `const max = Math.max(0, slotRects(each.slots.length, st).reduce((end, rect)` — const, line 1356
- `const result = zoomWheel(g.zoom, dy, now,` — const, line 1366
- `const stepped = result.step` — const, line 1368
- `const began = overviewRef.current ? beginLeave(selectionRef.current ?` — const, line 1370
- `const began = stepped.goal === 1 ? beginEnter() : beginLeave(selectionRef.current ?` — const, line 1376
- `const how = g.source === "pinch" ? "pinch" : modifiers.read(event).alt ? "alt + scroll" : "ctrl + scroll"` — const, line 1382
- `const drag = useRef<` — const, line 1396
- `const onStagePointerDown = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1397
- `const target = event.target as Element` — const, line 1398
- `const onCard = target.closest("[data-desk-slot]")` — const, line 1399
- `const onSliver = target.closest(".desk-sliver") !== null` — const, line 1401
- `const inContent = !onSliver && target.closest(".desk-slot-inner, button, input, textarea") !== null` — const, line 1402
- `const key = onCard.getAttribute("data-desk-slot-key") ?? undefined` — const, line 1405
- `const windowId = onCard.getAttribute("data-desk-slot-window") ?? undefined` — const, line 1406
- `const deskOf = onCard.getAttribute("data-desk-slot-desk") ?? undefined` — const, line 1407
- `const onStagePointerMove = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1421
- `const d = drag.current` — const, line 1422
- `const dx = event.clientX - d.x` — const, line 1424
- `const dy = event.clientY - d.y` — const, line 1425
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1444
- `const cancelDrag = useCallback(()` — const, line 1452
- `const d = drag.current` — const, line 1453
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1461
- `const cancelDragRef = useRef(cancelDrag)` — const, line 1467
- `const scrubbedClick = useRef(false)` — const, line 1470
- `const onStagePointerUp = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1471
- `const d = drag.current` — const, line 1472
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1482
- `const layout = ovLayoutRef.current` — const, line 1493
- `const stageBox = (event.currentTarget as HTMLElement).getBoundingClientRect()` — const, line 1494
- `const point =` — const, line 1496
- `const drop = dropTarget(layout, point)` — const, line 1497
- `const current = wsRef.current` — const, line 1498
- `const to = drop ? current.desks[drop.row] : null` — const, line 1499
- `const from = slotIndexOf(to, d.windowId)` — const, line 1502
- `const world = worldRef.current` — const, line 1513
- `const observer = new MutationObserver((records)` — const, line 1515
- `const node = record.target instanceof Element ? record.target : record.target.parentElement` — const, line 1517
- `const windowId = windowOfTarget(node)` — const, line 1518
- `const handle = timers.set(()` — const, line 1531
- `const body = [...document.querySelectorAll<HTMLElement>("[data-desk-window]")].find((pane)` — const, line 1534
- `const node = miniatures.get(windowId)` — const, line 1544
- `const node = host.firstElementChild as HTMLElement | null` — const, line 1547
- `const openContent = useCallback((content: ContentRefDto, options:` — const, line 1567
- `const current = wsRef.current` — const, line 1568
- `const id = deskIdRef.current` — const, line 1569
- `const step = openBeside(current, id, content, ()` — const, line 1571
- `const jump = jumps.current.get(step.windowId)` — const, line 1578
- `const handle = timers.set(()` — const, line 1584
- `const next = new Set(now)` — const, line 1587
- `const openHit = useCallback((hit:` — const, line 1597
- `const card = library?.find((entry)` — const, line 1599
- `const kind = card && isVideoCard(card) ? "video" : "source"` — const, line 1600
- `const asks = useMemo( ()` — const, line 1607
- `const statusRef = useRef(status)` — const, line 1612
- `const companionStateRef = useRef(companionState)` — const, line 1614
- `const chipRef = useRef(chip)` — const, line 1616
- `const searchOpenRef = useRef(false)` — const, line 1618
- `const anchoredAt = useRef(0)` — const, line 1620
- `const groundingRef = useRef<Grounding>(` — const, line 1621
- `const stepCompanion = useCallback((event: CompanionEvent)` — const, line 1624
- `const before = companionStateRef.current` — const, line 1625
- `const next = companionStep(before, event)` — const, line 1626
- `const id = deskIdRef.current` — const, line 1631
- `const lastPointer = useRef<` — const, line 1636
- `const stageNode = stageRef.current` — const, line 1638
- `const onMove = (event: PointerEvent)` — const, line 1640
- `const box = stageNode.getBoundingClientRect()` — const, line 1641
- `const companionKey = (atDock: boolean)` — const, line 1650
- `let anchor: Rect | null = null` — let, line 1655
- `const id = focusIdRef.current` — const, line 1657
- `const selected: WindowSelection | null = id ? readWindowSelection(id, stageRef.current) : null` — const, line 1658
- `const companionKeyRef = useRef(companionKey)` — const, line 1668
- `const companionInit = useRef(false)` — const, line 1673
- `const opening = deskById(ws, deskId)` — const, line 1676
- `const shown: CompanionState =` — const, line 1681
- `const snapCompanion = useCallback((dock: CompanionDock)` — const, line 1687
- `const id = deskIdRef.current` — const, line 1689
- `const before = companionStateRef.current` — const, line 1691
- `const next: CompanionState =` — const, line 1692
- `const viewKey = `$` — const, line 1700
- `const lastViewKey = useRef(viewKey)` — const, line 1701
- `const stageNode = stageRef.current` — const, line 1710
- `const onScroll = (event: Event)` — const, line 1712
- `const target = event.target instanceof Element ? event.target : null` — const, line 1715
- `const onSelection = ()` — const, line 1725
- `const id = focusIdRef.current` — const, line 1726
- `const panel = companionRef.current?.rect() ?? null` — const, line 1727
- `const selected = readWindowSelection(id, stageRef.current)` — const, line 1732
- `const askCompanion = useCallback((question: string)` — const, line 1739
- `const grounding = groundingRef.current` — const, line 1740
- `const spanId = grounding.spanId ?? firstVisibleSpan(grounding.windowId ?? null)` — const, line 1742
- `const lifecycle = lifecyclesRef.current[grounding.windowId ?? ""]` — const, line 1748
- `const selected = chipRef.current` — const, line 1750
- `const loadHistory = useCallback((query: string)` — const, line 1764
- `const deskTitle = useCallback((id: string | null)` — const, line 1766
- `const openClaim = useCallback((citation: Pick<TutorCitationDto, "extractionId" | "spanId"> &` — const, line 1769
- `let sourceId = citation.sourceId ?? null` — let, line 1770
- `let kind: "source" | "video" = "source"` — let, line 1771
- `const content = window.content` — const, line 1773
- `const card = library?.find((entry)` — const, line 1784
- `const openThread = useCallback((exchange: CompanionExchange)` — const, line 1789
- `const root = exchange.answer?.readerAnswerEventId || exchange.answer?.eventId` — const, line 1790
- `const openSearchRow = useCallback((row: SearchRow)` — const, line 1797
- `const id = deskIdRef.current` — const, line 1798
- `const ref = row.ref` — const, line 1803
- `const passage = (row.raw as` — const, line 1809
- `const extractionId = passage && (passage.kind === "source" || passage.kind === "video") ? passage.extractionId : null` — const, line 1810
- `const refreshCarried = useCallback(()` — const, line 1819
- `const carryQuestion = useCallback((text: string, origin:` — const, line 1829
- `const openPassage = useCallback((extractionId: string, spanId: string | null, t?: number)` — const, line 1837
- `let found: ContentRefDto | null = null` — let, line 1838
- `const content = window.content` — const, line 1840
- `const ref = found.kind === "video" && t !== undefined ?` — const, line 1850
- `const sourcePieces = useCallback((): SourcePiece[]` — const, line 1856
- `const current = wsRef.current` — const, line 1857
- `const id = deskIdRef.current` — const, line 1858
- `const each = id ? deskById(current, id) : null` — const, line 1859
- `const out: SourcePiece[] = []` — const, line 1861
- `const window = current.windows[windowId]` — const, line 1863
- `const content = window?.content` — const, line 1864
- `const spanId = statusRef.current[windowId]?.readingSpan ?? firstVisibleSpan(windowId)` — const, line 1866
- `const element = document.querySelector(`[$` — const, line 1868
- `const text = (element?.textContent ?? "").replace(/\s+/g, " ").trim().slice(0, 600)` — const, line 1869
- `const title = titleOf(window)` — const, line 1871
- `const padsHost = useMemo<PadsHost>(()` — const, line 1877
- `let job = await padsTransport.figureRequest(` — let, line 1892
- `const figure = job.result?.figure` — const, line 1897
- `const window = wsRef.current.windows[windowId]` — const, line 1904
- `const focusedStack = (): PadStackHandle | null` — const, line 1916
- `const focusedStackRef = useRef(focusedStack)` — const, line 1917
- `const newPadBeside = useCallback(()` — const, line 1921
- `const id = deskIdRef.current` — const, line 1922
- `const selected = focusIdRef.current ? readWindowSelection(focusIdRef.current, stageRef.current) : null` — const, line 1924
- `const padId = mintId("pad")` — const, line 1925
- `const title = selected ? `Scratchpad · “$` — const, line 1926
- `const refused = store.commitPad(padId, [` — const, line 1927
- `const newPadBesideRef = useRef(newPadBeside)` — const, line 1934
- `const deskPadIds = useCallback((id: string | null): string[]` — const, line 1938
- `const runningPadOf = useCallback((id: string | null): string | null` — const, line 1944
- `const answerProposals = useCallback((exchange: CompanionExchange): ProposedDiff[]` — const, line 1951
- `const answer = exchange.answer` — const, line 1952
- `const known = runningPadOf(exchange.deskId)` — const, line 1953
- `const lines = answer.answerMd.split("\n").map((line)` — const, line 1955
- `const padId = runningPadOf(exchange.deskId)` — const, line 1963
- `const now = padId ? store.pads[padId] : null` — const, line 1964
- `const refused = store.commitPad(padId, [` — const, line 1966
- `const drainWrite = useCallback((padId: string, op: "keep" | "unkeep", version: number)` — const, line 1976
- `const refused = store.commitPad(padId, [` — const, line 1978
- `const padLinks = useMemo<PadLink[]>(()` — const, line 1983
- `const surfacedCarried = useRef(new Set<string>())` — const, line 1987
- `const onCarriedSurfaced = useCallback((question: CarriedQuestionDto)` — const, line 1988
- `const viewTimers = useRef(new Map<string,` — const, line 1996
- `const shellTimers = useRef(new Set<unknown>())` — const, line 1997
- `const statusFor = useMemo(()` — const, line 2009
- `const onStatusFor = useCallback((windowId: string)` — const, line 2010
- `let handler = statusFor.get(windowId)` — let, line 2011
- `const previous = viewTimers.current.get(windowId)` — const, line 2020
- `const save = ()` — const, line 2022
- `const current = store.ws` — const, line 2023
- `const window = current.windows[windowId]` — const, line 2024
- `const jumpReadyFor = useMemo(()` — const, line 2042
- `const onJumpReadyFor = useCallback((windowId: string)` — const, line 2043
- `let handler = jumpReadyFor.get(windowId)` — let, line 2044
- `const pending = pendingJump.current.get(windowId)` — const, line 2052
- `const mediaReadyFor = useMemo(()` — const, line 2063
- `const onMediaReadyFor = useCallback((windowId: string)` — const, line 2064
- `let handler = mediaReadyFor.get(windowId)` — let, line 2065
- `const railNodeFor = useMemo(()` — const, line 2076
- `const onRailNode = useCallback((windowId: string)` — const, line 2077
- `let handler = railNodeFor.get(windowId)` — let, line 2078
- `const railPanelOf = useCallback((deskOf: string, extractionId: string): string | null` — const, line 2087
- `const desk = deskById(ws, deskOf)` — const, line 2089
- `const panels = desk.slots.flat().filter((id)` — const, line 2091
- `const content = ws.windows[id]?.content` — const, line 2092
- `const claimed = railClaims[`$` — const, line 2095
- `const sourceWindowOf = useCallback((deskOf: string, extractionId: string): string | null` — const, line 2099
- `const desk = deskById(ws, deskOf)` — const, line 2101
- `const content = ws.windows[id]?.content` — const, line 2104
- `const undoShown = undo && undo.deskId === deskId && undo.until > timers.now() && (ws?.closed[undo.deskId] ?? []).some((entry)` — const, line 2112
- `const handle = timers.set(()` — const, line 2116
- `const paneBody = (window: DeskWindow, lifecycle: WindowLifecycle): ReactNode` — const, line 2130
- `const content = window.content` — const, line 2131
- `const card = content && (content.kind === "source" || content.kind === "video") ? library?.find((entry)` — const, line 2132
- `const stack = window.stack ?? (content?.kind === "pad" ? [` — const, line 2135
- `const railPanel = railPanelOf(window.deskId, content.extractionId)` — const, line 2142
- `const railNode = railPanel ? railHosts[railPanel] ?? null : null` — const, line 2143
- `const railContent = railPanel ? ws.windows[railPanel]?.content : null` — const, line 2144
- `const railTab = railContent?.kind === "panel" && railContent.panel === "notes" ? "notes" : "guide"` — const, line 2145
- `const extractionId = content.extractionId ?? ""` — const, line 2163
- `const owner = railPanelOf(window.deskId, extractionId)` — const, line 2164
- `const target = content.extractionId ? sourceWindowOf(window.deskId, content.extractionId) : null` — const, line 2181
- `const jump = jumps.current.get(target)` — const, line 2184
- `const linkedFrom = overview || zooming ? selection?.windowId ?? focusId : null` — const, line 2208
- `const selectedRelations = relatedTo(linkedFrom)` — const, line 2209
- `const linkRects = new Map<string, Rect>()` — const, line 2210
- `const rect = ovLayout?.cards[row]?.[index]` — const, line 2212
- `const fromCard = linkedFrom ? linkRects.get(linkedFrom) ?? null : null` — const, line 2215
- `const links = fromCard ? curvedLinks(fromCard, selectedRelations.filter((relation)` — const, line 2216
- `const ghosts: Array<` — const, line 2219
- `const row = ws.desks.findIndex((each)` — const, line 2221
- `const each = ws.desks[row]` — const, line 2222
- `const sameDesk = selectedRelations.filter((relation)` — const, line 2224
- `const linked = slot.some((id)` — const, line 2228
- `const movedShown = movedNotice && movedNotice.deskId === deskId && movedNotice.until > timers.now() ? movedNotice : null` — const, line 2233
- `const focusWindow = focusId ? ws.windows[focusId] : undefined` — const, line 2234
- `const thread = asks.thread(deskId)` — const, line 2236
- `const grounding: Grounding = groundingFor(ws, chip, focusWindow, status)` — const, line 2237
- `const focusZoom = typeof focusWindow?.view?.zoom === "number" ? (focusWindow.view.zoom as number) : 1` — const, line 2239
- `const windowPlaces = ws.desks.flatMap((each, rowIndex)` — const, line 2242
- `const eachCam = camX[each.deskId] ?? 0` — const, line 2243
- `const rects = slotRects(each.slots.length, stage)` — const, line 2244
- `const top = rowTop(rowIndex, stage) - rowTop(deskIndex, stage)` — const, line 2245
- `const slotReading =` — const, line 2247
- `const slotCard = ovLayout?.cards[rowIndex]?.[index] ?? slotReading` — const, line 2248
- `const readingPanes = paneRects(slotReading, slot.length)` — const, line 2249
- `const cardPanes = paneRects(slotCard, slot.length)` — const, line 2250
- `const window = ws.windows[id]` — const, line 2252
- `const sliverDesk = leaveTarget ? deskById(ws, leaveTarget.deskId) : desk` — const, line 2259
- `const sliverCam = leaveTarget && sliverDesk ? leaveTarget.cams[sliverDesk.deskId] ?? 0 : cam` — const, line 2260
- `const slivers = sliverDesk && !focusMode ? sliverSlots(sliverCam, sliverDesk.slots.length, stage) :` — const, line 2261
- `const shelfRows: ShelfRow[] = desk ? desk.slots.flatMap((slot, index)` — const, line 2262
- `const window = ws.windows[id]` — const, line 2264
- `const kind = window?.kind ?? "source"` — const, line 2265
- `const hints = overview ? [["h j k l", "select"], ["↵ / click", "open"], ["alt+↵", "open in focus"], ["alt+[ ]", "move"], ["alt+shift+j/k", "to a desk"], ["drag", "move a card"], ["b", "relations"], ["g", "hold: gather"], ["o / esc", "back"]] : focusMode ? [["…` — const, line 2279
- `const title = (event.target as HTMLInputElement).value.trim()` — const, line 2301
- `const id = mintId("desk")` — const, line 2327
- `const id = window.windowId` — const, line 2384
- `const onCurrent = each.deskId === deskId` — const, line 2385
- `const opened = visited.has(each.deskId) || onCurrent` — const, line 2386
- `const full = (!overview && onCurrent && focusMode && id === focusId) || (leaveTarget?.focusWindowId === id && leaveTarget.deskId === each.deskId)` — const, line 2387
- `const hiddenInFocus = !overview && onCurrent && focusMode && !full` — const, line 2388
- `const reading = full ?` — const, line 2389
- `const card = place.card` — const, line 2390
- `const box = overview ? card : reading` — const, line 2391
- `const leavingTo = leaveTarget?.deskId === each.deskId` — const, line 2392
- `const slotCut = leavingTo ? slotVisibility(leaveTarget.cams[each.deskId] ?? 0, each.slots.length, stage)[index] : onCurrent ? visibility[index] : null` — const, line 2393
- `const mask = full || focusMode || !slotCut ? null : leavingTo || (!overview && !zooming && onCurrent) ? softCropMask(slotCut, reading.w) : null` — const, line 2396
- `const lifecycle = lifecycles[id] ??` — const, line 2397
- `const paused = isPaused(lifecycle.state)` — const, line 2398
- `const paired = slot.length > 1` — const, line 2399
- `const selected = overview && selection !== null && slot.includes(selection.windowId)` — const, line 2400
- `const receding = overview && recedes(slot, selection?.windowId ?? null, selectedRelations, showRelations)` — const, line 2401
- `const measure = FOCUS_MEASURE[window.kind] ?? FOCUS_MEASURE.source` — const, line 2402
- `const title = titleOf(window)` — const, line 2456
- `const ringId = linkedFrom` — const, line 2538
- `const isSel = ringId !== null && slot.includes(ringId)` — const, line 2539
- `const isRel = !isSel && showRelations && slot.some((id)` — const, line 2540
- `const rect = ovLayout?.cards[rowIndex]?.[index]` — const, line 2541
- `const key = slotKey(each.deskId, slot)` — const, line 2543
- `const content = ws.windows[id]?.content` — const, line 2585
- `const stackWindow = Object.values(wsRef.current.windows).find((window)` — const, line 2591
- `function Sliver(` — function, line 2727
- `function WhichKey()` — function, line 2737
- `const groups: Array<` — const, line 2738
- `const rows = DESK_BINDINGS.filter((binding)` — const, line 2749
- `function OpenBeside(` — function, line 2767
- `const words = filter.trim().toLowerCase()` — const, line 2783
- `const sources = (library ?? []).filter((card)` — const, line 2784
- `const book = focus?.content && (focus.content.kind === "source" || focus.content.kind === "video") ? focus.content : null` — const, line 2785

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
- [[Reference/Desktop/TypeScript/screens/desks/companion/asks|src/screens/desks/companion/asks.ts]] — import-or-re-export; imports `CompanionApi`, `CompanionAsks`, `CompanionExchange`, `companionAsksFor`
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
- [[Reference/Desktop/TypeScript/screens/desks/selection|src/screens/desks/selection.ts]] — import-or-re-export; imports `WindowSelection`, `readWindowSelection`
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

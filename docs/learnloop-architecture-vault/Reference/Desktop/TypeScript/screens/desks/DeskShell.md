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
| Source lines | 2532 |
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

- `export interface DeskTransport extends OutboxTransport` — interface, line 113
- `export const LIVE_DESK_TRANSPORT: DeskTransport =` — const, line 120
- `export interface CompanionTransport extends CompanionApi, SearchApi` — interface, line 175
- `export const LIVE_COMPANION_TRANSPORT: CompanionTransport =` — const, line 179
- `export interface PaneRenderInput` — interface, line 189
- `export interface DeskDebugHandle` — interface, line 205
- `export const KIND_GLYPH: Record<string, string> =` — const, line 240
- `export interface DeskShellProps` — interface, line 293
- `export function DeskShell(` — function, line 320
- `export function isVideoCard(card: SourceLibraryCard): boolean` — function, line 2412
- `export function contentForCard(card: SourceLibraryCard, extractionId: string): ContentRefDto` — function, line 2416

## Internal implementation anchors

- `type DeskWindow, type Step, type Workspace, } from "./model/workspace"` — type, line 37
- `type Step, type Workspace, } from "./model/workspace"` — type, line 38
- `type Workspace, } from "./model/workspace"` — type, line 39
- `type Rect, type Stage, } from "./geometry"` — type, line 53
- `type Stage, } from "./geometry"` — type, line 54
- `type Camera, type ZoomGesture, type ZoomSource, } from "./overview/engine"` — type, line 69
- `type ZoomGesture, type ZoomSource, } from "./overview/engine"` — type, line 70
- `type ZoomSource, } from "./overview/engine"` — type, line 71
- `type DeskAction, type Timers, } from "./keys/router"` — type, line 84
- `type Timers, } from "./keys/router"` — type, line 85
- `const COMPANION_SIZES_HANDOFF_MS = 250` — const, line 130
- `interface Grounding` — interface, line 133
- `function groundingFor(ws: Workspace, chip:` — function, line 140
- `const content = ws.windows[chip.windowId]?.content` — const, line 142
- `const content = focus?.content` — const, line 147
- `const span = status[focus.windowId]?.readingSpan ?? (typeof focus.view?.spanId === "string" ? (focus.view.spanId as string) : undefined)` — const, line 151
- `function firstVisibleSpan(windowId: string | null): string | null` — function, line 158
- `const host = document.querySelector(`[$` — const, line 160
- `const top = host.getBoundingClientRect().top` — const, line 162
- `const spans = [...host.querySelectorAll<HTMLElement>("[data-span-id], [data-transcript-span]")]` — const, line 163
- `const visible = spans.find((element)` — const, line 164
- `function threadTitle(thread: CompanionExchange[]): string` — function, line 168
- `const last = thread[thread.length - 1]` — const, line 169
- `const UNDO_CLOSE_MS = 9_000` — const, line 196
- `const TOAST_MS = 2_200` — const, line 198
- `const VIEW_SAVE_IDLE_MS = 2_000` — const, line 200
- `const MOVED_NOTICE_MS = 6_000` — const, line 202
- `function displayedCamera(world: HTMLElement): Camera | null` — function, line 215
- `const shown = typeof getComputedStyle === "function" ? getComputedStyle(world).transform : ""` — const, line 216
- `const match = /^matrix\(([^)]+)\)$/.exec(shown ?? "")` — const, line 217
- `function prefersReducedMotion(): boolean` — function, line 223
- `function slotKey(deskId: string, slot: string[]): string` — function, line 232
- `function intersects(rect: Rect, stage: Stage): boolean` — function, line 236
- `const KIND_WORD: Record<string, string> =` — const, line 252
- `function defaultMintId(prefix: string): string` — function, line 264
- `function shortName(title: string): string` — function, line 272
- `const words = title.split(/\s+/).filter(Boolean)` — const, line 273
- `function readStored(key: string): string | null` — function, line 277
- `function writeStored(key: string, value: string): void` — function, line 285
- `const store = useMemo( ()` — const, line 339
- `const storeWs = useSyncExternalStore(store.subscribe, store.getSnapshot)` — const, line 343
- `const ws: Workspace | null = storeReady ? storeWs : null` — const, line 345
- `const wsRef = useMemo(()` — const, line 346
- `const deskKey = `learnloop.desks.current.$` — const, line 348
- `const stageRef = useRef<HTMLElement | null>(null)` — const, line 363
- `const viewport = initialViewport ??` — const, line 365
- `const shelf = viewport.width < DESK_SIZES.shelfFoldBelow ? DESK_SIZES.shelfRail : DESK_SIZES.shelf` — const, line 366
- `const companionRef = useRef<CompanionHandle | null>(null)` — const, line 391
- `const preOverview = useRef<` — const, line 394
- `const worldRef = useRef<HTMLDivElement | null>(null)` — const, line 395
- `const boxEls = useRef(new Map<string, HTMLElement>())` — const, line 398
- `const innerEls = useRef(new Map<string, HTMLElement>())` — const, line 399
- `const cardEls = useRef(new Map<string, HTMLElement>())` — const, line 400
- `const ringEls = useRef(new Map<string, HTMLElement>())` — const, line 401
- `const slotElements = useCallback((): Map<string, SlotElements>` — const, line 402
- `const out = new Map<string, SlotElements>()` — const, line 403
- `const lateEls = useRef(new Map<string, HTMLElement>())` — const, line 407
- `const sliverEls = useRef(new Map<string, HTMLElement>())` — const, line 408
- `const miniatures = useMemo(()` — const, line 409
- `const miniHosts = useRef(new Map<string, HTMLDivElement>())` — const, line 410
- `const onEndRef = useRef<(goal: 0 | 1, base: 0 | 1)` — const, line 411
- `const controller = useMemo(()` — const, line 412
- `const jumps = useRef(new Map<string, (spanId: string)` — const, line 413
- `const media = useRef(new Map<string, ()` — const, line 414
- `const pendingJump = useRef(new Map<string, string>())` — const, line 415
- `const toastNow = useCallback((text: string)` — const, line 417
- `const handle = timers.set(()` — const, line 420
- `const setCurrentDeskId = useCallback((deskId: string | null)` — const, line 426
- `const commit = useCallback((step: Step)` — const, line 431
- `const total = notice.dropped + notice.lost` — const, line 440
- `const chain = useCallback((first: Step, next: (ws: Workspace)` — const, line 446
- `const second = next(first.ws)` — const, line 447
- `const firstRun = useCallback(async (base: Workspace, cards: SourceLibraryCard[] | null): Promise<Step>` — const, line 451
- `const card = firstSourceId ? cards?.find((entry)` — const, line 452
- `const deskId = mintId("desk")` — const, line 453
- `const created = createDesk(base, deskId, card ? `new desk · $` — const, line 454
- `const extractionId = await transport.resolveExtraction(card.sourceId).catch(()` — const, line 456
- `let live = true` — let, line 462
- `const desk = ws ? deskById(ws, currentDeskId) ?? ws.desks[0] ?? null : null` — const, line 484
- `const deskId = desk?.deskId ?? null` — const, line 485
- `const focusId = ws && desk ? focusedWindowId(ws, desk) : null` — const, line 486
- `const focusSlotIndex = ws && desk ? focusedSlot(ws, desk) : -1` — const, line 487
- `const slotCount = desk?.slots.length ?? 0` — const, line 495
- `const keepPrevious = useRef(false)` — const, line 496
- `const next = ensureVisible(cams[deskId] ?? 0, focusSlotIndex, slotCount, stage, keepPrevious.current)` — const, line 500
- `const node = stageRef.current` — const, line 508
- `const measure = ()` — const, line 509
- `const next =` — const, line 511
- `const now = stageNow.current` — const, line 512
- `const shell = node?.closest(".desk-shell") as HTMLElement | null` — const, line 519
- `const observer = typeof ResizeObserver === "undefined" || !node ? null : new ResizeObserver(measure)` — const, line 523
- `const cam = deskId ? camX[deskId] ?? 0 : 0` — const, line 532
- `const visibility = useMemo(()` — const, line 533
- `const deskIndex = ws && desk ? ws.desks.indexOf(desk) : 0` — const, line 534
- `const lifecycles = useMemo(()` — const, line 538
- `const out: Record<string, WindowLifecycle> =` — const, line 539
- `const onCurrent = each.deskId === deskId` — const, line 542
- `const activeWindowId = Object.values(lifecycles).find((each)` — const, line 558
- `const held = document.activeElement` — const, line 560
- `const owner = held && held !== document.body ? windowOfTarget(held) : null` — const, line 561
- `const target = activeWindowId ? document.querySelector<HTMLElement>(`[$` — const, line 563
- `const lifecyclesRef = useRef(lifecycles)` — const, line 569
- `const focusIdRef = useRef(focusId)` — const, line 571
- `const focusModeRef = useRef(focusMode)` — const, line 579
- `const switchDesk = useCallback((direction: -1 | 1): boolean` — const, line 582
- `const current = wsRef.current` — const, line 583
- `const index = current.desks.findIndex((each)` — const, line 584
- `const next = current.desks[index + direction]` — const, line 585
- `const deskIdRef = useRef(deskId)` — const, line 590
- `const titleOf = useCallback((window: DeskWindow | undefined): string` — const, line 593
- `const known = status[window.windowId]?.title` — const, line 595
- `const content = window.content` — const, line 597
- `const ovLayout = useMemo(()` — const, line 607
- `const ovLayoutRef = useRef(ovLayout)` — const, line 608
- `const stageNow = useRef(stage)` — const, line 610
- `const camXRef = useRef(camX)` — const, line 612
- `const overviewRef = useRef(overview)` — const, line 614
- `const ovCamRef = useRef(ovCam)` — const, line 616
- `const selectionRef = useRef(selection)` — const, line 618
- `const visitedRef = useRef(visited)` — const, line 620
- `const showRelationsRef = useRef(showRelations)` — const, line 622
- `const reduced = reducedMotion ?? prefersReducedMotion()` — const, line 624
- `const transitionGen = useRef(0)` — const, line 627
- `const panEaseRef = useRef(panEase)` — const, line 628
- `const pendingLeave = useRef<` — const, line 630
- `const cardOf = useCallback((windowId: string | null | undefined): Rect | null` — const, line 633
- `const layout = ovLayoutRef.current` — const, line 634
- `const current = wsRef.current` — const, line 635
- `const index = slotIndexOf(each, windowId)` — const, line 638
- `const readingRectOf = useCallback((current: Workspace, row: number, index: number, readingRow: number, cams: Record<string, number>, st: Stage): Rect` — const, line 646
- `const each = current.desks[row]` — const, line 647
- `const rect = slotRects(each.slots.length, st)[index]` — const, line 648
- `const relatedTo = useCallback((windowId: string | null | undefined): Relation[]` — const, line 652
- `const recedes = useCallback((slot: string[], selected: string | null, related: Relation[], relationsOn: boolean): boolean` — const, line 655
- `const planZoom = useCallback((base: 0 | 1, readingDeskId: string, cams: Record<string, number>, selected: string | null, B: Camera, fullWindowId: string | null = null): ZoomPlan | null` — const, line 660
- `const current = wsRef.current` — const, line 661
- `const layout = ovLayoutRef.current` — const, line 662
- `const st = stageNow.current` — const, line 663
- `const readingRow = Math.max(0, current.desks.findIndex((each)` — const, line 665
- `const related = relatedTo(selected)` — const, line 666
- `const items: ZoomPlan["items"] = []` — const, line 667
- `const rings: ZoomPlan["rings"] = []` — const, line 668
- `const a = readingRectOf(current, row, index, readingRow, cams, st)` — const, line 670
- `const b = layout.cards[row][index]` — const, line 671
- `const readingPanes = paneRects(a, slot.length)` — const, line 672
- `const cardPanes = paneRects(b, slot.length)` — const, line 673
- `const live = visitedRef.current.has(each.deskId) && each.deskId === readingDeskId && intersects(a, st)` — const, line 674
- `const recede = recedes(slot, selected, related, showRelationsRef.current)` — const, line 675
- `const focus = selected !== null && slot.includes(selected)` — const, line 676
- `const isRelated = showRelationsRef.current && slot.some((id)` — const, line 677
- `const pa = id === fullWindowId && each.deskId === readingDeskId ?` — const, line 680
- `const pb = cardPanes[pane]` — const, line 681
- `const zoomTargets = useCallback(()` — const, line 689
- `const crossfade = useCallback((enter: boolean, to:` — const, line 701
- `const world = worldRef.current` — const, line 703
- `const id = deskIdRef.current` — const, line 709
- `const target = to ?? (preOverview.current ?` — const, line 718
- `const beginEnter = useCallback((): boolean` — const, line 729
- `const id = deskIdRef.current` — const, line 731
- `const selected = focusIdRef.current` — const, line 739
- `const B = enteringCamera(cardOf(selected), stageNow.current)` — const, line 741
- `const plan = planZoom(0, id, camXRef.current, selected, B)` — const, line 746
- `const beginLeave = useCallback((to:` — const, line 754
- `const shown = displayedCamera(worldRef.current) ?? ovCamRef.current` — const, line 764
- `const target = to ?? preOverview.current ?? (selectionRef.current ?` — const, line 770
- `const deskIdTo = target.deskId` — const, line 772
- `const windowTo = "windowId" in target ? target.windowId : target.focusId` — const, line 773
- `const current = wsRef.current` — const, line 774
- `const each = deskById(current, deskIdTo)` — const, line 775
- `const fullWindowId = focusAfter && windowTo ? windowTo : null` — const, line 777
- `const node = stageRef.current` — const, line 786
- `const cams =` — const, line 790
- `const index = windowTo ? slotIndexOf(each, windowTo) : -1` — const, line 791
- `const plan = planZoom(1, deskIdTo, cams, windowTo, ovCamRef.current, fullWindowId)` — const, line 793
- `const plan = controller.plan` — const, line 809
- `const leave = pendingLeave.current` — const, line 827
- `const generation = transitionGen.current` — const, line 841
- `const toggleOverview = useCallback((to:` — const, line 850
- `const focusWindow = focusId ? ws.windows[focusId] : null` — const, line 867
- `const first = ws.desks.find((each)` — const, line 872
- `const windowId = first ? first.slots[0].find((id)` — const, line 873
- `const followMoved = useRef(false)` — const, line 877
- `const rect = cardOf(selection.windowId)` — const, line 881
- `const moveOverviewSelection = useCallback((direction: "left" | "right" | "up" | "down")` — const, line 888
- `const layout = ovLayoutRef.current` — const, line 889
- `const current = wsRef.current` — const, line 890
- `const sel = selectionRef.current` — const, line 891
- `let row = sel ? current.desks.findIndex((each)` — let, line 893
- `let slot = sel ? slotIndexOf(current.desks[row] ?? current.desks[0], sel.windowId) : 0` — let, line 894
- `const next = moveSelection(layout,` — const, line 899
- `const each = current.desks[next.row]` — const, line 900
- `const windowId = each?.slots[next.slot]?.find((id)` — const, line 901
- `const gather = useCallback((toNewDesk: boolean)` — const, line 909
- `const current = wsRef.current` — const, line 910
- `const id = deskIdRef.current` — const, line 911
- `const focus = focusIdRef.current` — const, line 912
- `const each = id ? deskById(current, id) : null` — const, line 913
- `const related = relationsOf(current, focus).filter((relation)` — const, line 920
- `const moving = [focus, ...related.slice(0, DRAWN_RELATIONS).map((relation)` — const, line 933
- `const newDeskId = mintId("desk")` — const, line 934
- `const title = `gathered · $` — const, line 935
- `let step = createDesk(current, newDeskId, title)` — let, line 936
- `let after: string | null = null` — let, line 937
- `const next = moveToDesk(step.ws, id, windowId, newDeskId, after)` — const, line 939
- `const focused = setFocus(step.ws, newDeskId, focus)` — const, line 943
- `const run = useCallback((action: DeskAction): boolean` — const, line 951
- `const current = wsRef.current` — const, line 952
- `const id = deskIdRef.current` — const, line 953
- `const focus = focusIdRef.current` — const, line 955
- `const step = focusPane(current, id, action.direction)` — const, line 961
- `const sel = overviewRef.current ? selectionRef.current : null` — const, line 967
- `const each = deskById(current, sel.deskId)` — const, line 969
- `const index = each ? slotIndexOf(each, sel.windowId) : -1` — const, line 970
- `const sel = selectionRef.current` — const, line 981
- `const row = current.desks.findIndex((each)` — const, line 983
- `const to = current.desks[row + action.direction]` — const, line 984
- `const from = current.desks[row]` — const, line 985
- `const index = slotIndexOf(from, sel.windowId)` — const, line 987
- `const sel = selectionRef.current` — const, line 1000
- `const title = titleOf(current.windows[focus])` — const, line 1024
- `const window = current.windows[focus]` — const, line 1039
- `const zoom = typeof window?.view?.zoom === "number" ? (window.view.zoom as number) : 1` — const, line 1040
- `const next = stepZoom(zoom, action.direction)` — const, line 1041
- `const desk = deskById(current, id)` — const, line 1047
- `const index = slotIndexOf(desk, focus)` — const, line 1049
- `const shown = visibilityRef.current.filter((slot)` — const, line 1050
- `const other = shown.find((slot)` — const, line 1051
- `const toggle = focus ? media.current.get(focus) : undefined` — const, line 1056
- `const visibilityRef = useRef(visibility)` — const, line 1071
- `const runRef = useRef(run)` — const, line 1073
- `const modifiers = useMemo(()` — const, line 1078
- `const altTracker = useMemo( ()` — const, line 1079
- `const router = useMemo(()` — const, line 1083
- `const current = wsRef.current` — const, line 1088
- `const id = deskIdRef.current` — const, line 1089
- `const owner = current.windows[windowId]` — const, line 1091
- `const outcome = altTracker.release(event)` — const, line 1119
- `const open = claimed.current.get(focusIdRef.current ?? "")` — const, line 1128
- `const has = (scope: ClaimedScope)` — const, line 1129
- `const resolution = resolveKey(event,` — const, line 1130
- `const claimed = useRef(new Map<string, Map<ClaimedScope, Set<string>>>())` — const, line 1154
- `const claimsByWindow = useRef(new Map<string, ScopeClaims>())` — const, line 1155
- `const claimsFor = useCallback((windowId: string): ScopeClaims` — const, line 1156
- `let claims = claimsByWindow.current.get(windowId)` — let, line 1157
- `const byScope = claimed.current.get(windowId) ?? new Map<ClaimedScope, Set<string>>()` — const, line 1161
- `const owners = byScope.get(scope) ?? new Set<string>()` — const, line 1162
- `const hubs = useRef(new Map<string, ListenerHub>())` — const, line 1173
- `const hubFor = useCallback((windowId: string): ListenerHub` — const, line 1174
- `let hub = hubs.current.get(windowId)` — let, line 1175
- `const world = worldRef.current` — const, line 1187
- `const mainRef = useRef<HTMLElement | null>(null)` — const, line 1192
- `const gesture = useRef<` — const, line 1193
- `const endGesture = useCallback(()` — const, line 1194
- `const g = gesture.current` — const, line 1195
- `const current = wsRef.current` — const, line 1205
- `const id = deskIdRef.current` — const, line 1206
- `const each = id ? deskById(current, id) : null` — const, line 1207
- `const st = stageNow.current` — const, line 1209
- `const rects = slotRects(each.slots.length, st)` — const, line 1210
- `const cam = camXRef.current[id] ?? 0` — const, line 1211
- `let best = 0` — let, line 1212
- `const snapped = ensureVisible(rects[best].x - DESK_SIZES.side, best, each.slots.length, st)` — const, line 1216
- `const target = each.slots[best].find((windowId)` — const, line 1218
- `const main = mainRef.current` — const, line 1224
- `const onWheel = (event: WheelEvent)` — const, line 1226
- `const target = event.target as Element | null` — const, line 1227
- `const st = stageNow.current` — const, line 1232
- `const now = performance.now()` — const, line 1233
- `let g = gesture.current` — let, line 1234
- `const kind = classifyWheel(event, modifiers.read(), st.height)` — const, line 1238
- `const ovPlain = overviewRef.current && kind.kind !== "zoom"` — const, line 1240
- `const id = deskIdRef.current` — const, line 1266
- `const each = id ? deskById(wsRef.current, id) : null` — const, line 1267
- `const travel = Math.abs(dx) > Math.abs(dy) ? dx : dy` — const, line 1269
- `const max = Math.max(0, slotRects(each.slots.length, st).reduce((end, rect)` — const, line 1270
- `const result = zoomWheel(g.zoom, dy, now,` — const, line 1280
- `const stepped = result.step` — const, line 1282
- `const began = overviewRef.current ? beginLeave(selectionRef.current ?` — const, line 1284
- `const began = stepped.goal === 1 ? beginEnter() : beginLeave(selectionRef.current ?` — const, line 1290
- `const how = g.source === "pinch" ? "pinch" : modifiers.read(event).alt ? "alt + scroll" : "ctrl + scroll"` — const, line 1296
- `const drag = useRef<` — const, line 1310
- `const onStagePointerDown = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1311
- `const target = event.target as Element` — const, line 1312
- `const onCard = target.closest("[data-desk-slot]")` — const, line 1313
- `const onSliver = target.closest(".desk-sliver") !== null` — const, line 1315
- `const inContent = !onSliver && target.closest(".desk-slot-inner, button, input, textarea") !== null` — const, line 1316
- `const key = onCard.getAttribute("data-desk-slot-key") ?? undefined` — const, line 1319
- `const windowId = onCard.getAttribute("data-desk-slot-window") ?? undefined` — const, line 1320
- `const deskOf = onCard.getAttribute("data-desk-slot-desk") ?? undefined` — const, line 1321
- `const onStagePointerMove = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1335
- `const d = drag.current` — const, line 1336
- `const dx = event.clientX - d.x` — const, line 1338
- `const dy = event.clientY - d.y` — const, line 1339
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1358
- `const cancelDrag = useCallback(()` — const, line 1366
- `const d = drag.current` — const, line 1367
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1375
- `const cancelDragRef = useRef(cancelDrag)` — const, line 1381
- `const scrubbedClick = useRef(false)` — const, line 1384
- `const onStagePointerUp = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1385
- `const d = drag.current` — const, line 1386
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1396
- `const layout = ovLayoutRef.current` — const, line 1407
- `const stageBox = (event.currentTarget as HTMLElement).getBoundingClientRect()` — const, line 1408
- `const point =` — const, line 1410
- `const drop = dropTarget(layout, point)` — const, line 1411
- `const current = wsRef.current` — const, line 1412
- `const to = drop ? current.desks[drop.row] : null` — const, line 1413
- `const from = slotIndexOf(to, d.windowId)` — const, line 1416
- `const world = worldRef.current` — const, line 1427
- `const observer = new MutationObserver((records)` — const, line 1429
- `const node = record.target instanceof Element ? record.target : record.target.parentElement` — const, line 1431
- `const windowId = windowOfTarget(node)` — const, line 1432
- `const handle = timers.set(()` — const, line 1445
- `const body = [...document.querySelectorAll<HTMLElement>("[data-desk-window]")].find((pane)` — const, line 1448
- `const node = miniatures.get(windowId)` — const, line 1458
- `const node = host.firstElementChild as HTMLElement | null` — const, line 1461
- `const openContent = useCallback((content: ContentRefDto, options:` — const, line 1481
- `const current = wsRef.current` — const, line 1482
- `const id = deskIdRef.current` — const, line 1483
- `const step = openBeside(current, id, content, ()` — const, line 1485
- `const jump = jumps.current.get(step.windowId)` — const, line 1492
- `const handle = timers.set(()` — const, line 1498
- `const next = new Set(now)` — const, line 1501
- `const openHit = useCallback((hit:` — const, line 1511
- `const card = library?.find((entry)` — const, line 1513
- `const kind = card && isVideoCard(card) ? "video" : "source"` — const, line 1514
- `const asks = useMemo( ()` — const, line 1521
- `const statusRef = useRef(status)` — const, line 1526
- `const companionStateRef = useRef(companionState)` — const, line 1528
- `const chipRef = useRef(chip)` — const, line 1530
- `const searchOpenRef = useRef(false)` — const, line 1532
- `const anchoredAt = useRef(0)` — const, line 1534
- `const groundingRef = useRef<Grounding>(` — const, line 1535
- `const stepCompanion = useCallback((event: CompanionEvent)` — const, line 1538
- `const before = companionStateRef.current` — const, line 1539
- `const next = companionStep(before, event)` — const, line 1540
- `const id = deskIdRef.current` — const, line 1545
- `const lastPointer = useRef<` — const, line 1550
- `const stageNode = stageRef.current` — const, line 1552
- `const onMove = (event: PointerEvent)` — const, line 1554
- `const box = stageNode.getBoundingClientRect()` — const, line 1555
- `const companionKey = (atDock: boolean)` — const, line 1564
- `let anchor: Rect | null = null` — let, line 1569
- `const id = focusIdRef.current` — const, line 1571
- `const selected: WindowSelection | null = id ? readWindowSelection(id, stageRef.current) : null` — const, line 1572
- `const companionKeyRef = useRef(companionKey)` — const, line 1582
- `const companionInit = useRef(false)` — const, line 1587
- `const opening = deskById(ws, deskId)` — const, line 1590
- `const shown: CompanionState =` — const, line 1595
- `const snapCompanion = useCallback((dock: CompanionDock)` — const, line 1601
- `const id = deskIdRef.current` — const, line 1603
- `const before = companionStateRef.current` — const, line 1605
- `const next: CompanionState =` — const, line 1606
- `const viewKey = `$` — const, line 1614
- `const lastViewKey = useRef(viewKey)` — const, line 1615
- `const stageNode = stageRef.current` — const, line 1624
- `const onScroll = (event: Event)` — const, line 1626
- `const target = event.target instanceof Element ? event.target : null` — const, line 1629
- `const onSelection = ()` — const, line 1639
- `const id = focusIdRef.current` — const, line 1640
- `const panel = companionRef.current?.rect() ?? null` — const, line 1641
- `const selected = readWindowSelection(id, stageRef.current)` — const, line 1646
- `const askCompanion = useCallback((question: string)` — const, line 1653
- `const grounding = groundingRef.current` — const, line 1654
- `const spanId = grounding.spanId ?? firstVisibleSpan(grounding.windowId ?? null)` — const, line 1656
- `const lifecycle = lifecyclesRef.current[grounding.windowId ?? ""]` — const, line 1662
- `const selected = chipRef.current` — const, line 1664
- `const loadHistory = useCallback((query: string)` — const, line 1678
- `const deskTitle = useCallback((id: string | null)` — const, line 1680
- `const openClaim = useCallback((citation: Pick<TutorCitationDto, "extractionId" | "spanId"> &` — const, line 1683
- `let sourceId = citation.sourceId ?? null` — let, line 1684
- `let kind: "source" | "video" = "source"` — let, line 1685
- `const content = window.content` — const, line 1687
- `const card = library?.find((entry)` — const, line 1698
- `const openThread = useCallback((exchange: CompanionExchange)` — const, line 1703
- `const root = exchange.answer?.readerAnswerEventId || exchange.answer?.eventId` — const, line 1704
- `const openSearchRow = useCallback((row: SearchRow)` — const, line 1711
- `const id = deskIdRef.current` — const, line 1712
- `const ref = row.ref` — const, line 1717
- `const passage = (row.raw as` — const, line 1723
- `const extractionId = passage && (passage.kind === "source" || passage.kind === "video") ? passage.extractionId : null` — const, line 1724
- `const viewTimers = useRef(new Map<string,` — const, line 1733
- `const shellTimers = useRef(new Set<unknown>())` — const, line 1734
- `const statusFor = useMemo(()` — const, line 1746
- `const onStatusFor = useCallback((windowId: string)` — const, line 1747
- `let handler = statusFor.get(windowId)` — let, line 1748
- `const previous = viewTimers.current.get(windowId)` — const, line 1757
- `const save = ()` — const, line 1759
- `const current = store.ws` — const, line 1760
- `const window = current.windows[windowId]` — const, line 1761
- `const jumpReadyFor = useMemo(()` — const, line 1779
- `const onJumpReadyFor = useCallback((windowId: string)` — const, line 1780
- `let handler = jumpReadyFor.get(windowId)` — let, line 1781
- `const pending = pendingJump.current.get(windowId)` — const, line 1789
- `const mediaReadyFor = useMemo(()` — const, line 1800
- `const onMediaReadyFor = useCallback((windowId: string)` — const, line 1801
- `let handler = mediaReadyFor.get(windowId)` — let, line 1802
- `const railNodeFor = useMemo(()` — const, line 1813
- `const onRailNode = useCallback((windowId: string)` — const, line 1814
- `let handler = railNodeFor.get(windowId)` — let, line 1815
- `const railPanelOf = useCallback((deskOf: string, extractionId: string): string | null` — const, line 1824
- `const desk = deskById(ws, deskOf)` — const, line 1826
- `const panels = desk.slots.flat().filter((id)` — const, line 1828
- `const content = ws.windows[id]?.content` — const, line 1829
- `const claimed = railClaims[`$` — const, line 1832
- `const sourceWindowOf = useCallback((deskOf: string, extractionId: string): string | null` — const, line 1836
- `const desk = deskById(ws, deskOf)` — const, line 1838
- `const content = ws.windows[id]?.content` — const, line 1841
- `const undoShown = undo && undo.deskId === deskId && undo.until > timers.now() && (ws?.closed[undo.deskId] ?? []).some((entry)` — const, line 1849
- `const handle = timers.set(()` — const, line 1853
- `const paneBody = (window: DeskWindow, lifecycle: WindowLifecycle): ReactNode` — const, line 1867
- `const content = window.content` — const, line 1868
- `const card = content && (content.kind === "source" || content.kind === "video") ? library?.find((entry)` — const, line 1869
- `const railPanel = railPanelOf(window.deskId, content.extractionId)` — const, line 1875
- `const railNode = railPanel ? railHosts[railPanel] ?? null : null` — const, line 1876
- `const railContent = railPanel ? ws.windows[railPanel]?.content : null` — const, line 1877
- `const railTab = railContent?.kind === "panel" && railContent.panel === "notes" ? "notes" : "guide"` — const, line 1878
- `const extractionId = content.extractionId ?? ""` — const, line 1896
- `const owner = railPanelOf(window.deskId, extractionId)` — const, line 1897
- `const target = content.extractionId ? sourceWindowOf(window.deskId, content.extractionId) : null` — const, line 1914
- `const jump = jumps.current.get(target)` — const, line 1917
- `const linkedFrom = overview || zooming ? selection?.windowId ?? focusId : null` — const, line 1941
- `const selectedRelations = relatedTo(linkedFrom)` — const, line 1942
- `const linkRects = new Map<string, Rect>()` — const, line 1943
- `const rect = ovLayout?.cards[row]?.[index]` — const, line 1945
- `const fromCard = linkedFrom ? linkRects.get(linkedFrom) ?? null : null` — const, line 1948
- `const links = fromCard ? curvedLinks(fromCard, selectedRelations.filter((relation)` — const, line 1949
- `const ghosts: Array<` — const, line 1952
- `const row = ws.desks.findIndex((each)` — const, line 1954
- `const each = ws.desks[row]` — const, line 1955
- `const sameDesk = selectedRelations.filter((relation)` — const, line 1957
- `const linked = slot.some((id)` — const, line 1961
- `const movedShown = movedNotice && movedNotice.deskId === deskId && movedNotice.until > timers.now() ? movedNotice : null` — const, line 1966
- `const focusWindow = focusId ? ws.windows[focusId] : undefined` — const, line 1967
- `const thread = asks.thread(deskId)` — const, line 1969
- `const grounding: Grounding = groundingFor(ws, chip, focusWindow, status)` — const, line 1970
- `const focusZoom = typeof focusWindow?.view?.zoom === "number" ? (focusWindow.view.zoom as number) : 1` — const, line 1972
- `const windowPlaces = ws.desks.flatMap((each, rowIndex)` — const, line 1975
- `const eachCam = camX[each.deskId] ?? 0` — const, line 1976
- `const rects = slotRects(each.slots.length, stage)` — const, line 1977
- `const top = rowTop(rowIndex, stage) - rowTop(deskIndex, stage)` — const, line 1978
- `const slotReading =` — const, line 1980
- `const slotCard = ovLayout?.cards[rowIndex]?.[index] ?? slotReading` — const, line 1981
- `const readingPanes = paneRects(slotReading, slot.length)` — const, line 1982
- `const cardPanes = paneRects(slotCard, slot.length)` — const, line 1983
- `const window = ws.windows[id]` — const, line 1985
- `const sliverDesk = leaveTarget ? deskById(ws, leaveTarget.deskId) : desk` — const, line 1992
- `const sliverCam = leaveTarget && sliverDesk ? leaveTarget.cams[sliverDesk.deskId] ?? 0 : cam` — const, line 1993
- `const slivers = sliverDesk && !focusMode ? sliverSlots(sliverCam, sliverDesk.slots.length, stage) :` — const, line 1994
- `const shelfRows: ShelfRow[] = desk ? desk.slots.flatMap((slot, index)` — const, line 1995
- `const window = ws.windows[id]` — const, line 1997
- `const kind = window?.kind ?? "source"` — const, line 1998
- `const hints = overview ? [["h j k l", "select"], ["↵ / click", "open"], ["alt+↵", "open in focus"], ["alt+[ ]", "move"], ["alt+shift+j/k", "to a desk"], ["drag", "move a card"], ["b", "relations"], ["g", "hold: gather"], ["o / esc", "back"]] : focusMode ? [["…` — const, line 2012
- `const title = (event.target as HTMLInputElement).value.trim()` — const, line 2033
- `const id = mintId("desk")` — const, line 2059
- `const id = window.windowId` — const, line 2114
- `const onCurrent = each.deskId === deskId` — const, line 2115
- `const opened = visited.has(each.deskId) || onCurrent` — const, line 2116
- `const full = (!overview && onCurrent && focusMode && id === focusId) || (leaveTarget?.focusWindowId === id && leaveTarget.deskId === each.deskId)` — const, line 2117
- `const hiddenInFocus = !overview && onCurrent && focusMode && !full` — const, line 2118
- `const reading = full ?` — const, line 2119
- `const card = place.card` — const, line 2120
- `const box = overview ? card : reading` — const, line 2121
- `const leavingTo = leaveTarget?.deskId === each.deskId` — const, line 2122
- `const slotCut = leavingTo ? slotVisibility(leaveTarget.cams[each.deskId] ?? 0, each.slots.length, stage)[index] : onCurrent ? visibility[index] : null` — const, line 2123
- `const mask = full || focusMode || !slotCut ? null : leavingTo || (!overview && !zooming && onCurrent) ? softCropMask(slotCut, reading.w) : null` — const, line 2126
- `const lifecycle = lifecycles[id] ??` — const, line 2127
- `const paused = isPaused(lifecycle.state)` — const, line 2128
- `const paired = slot.length > 1` — const, line 2129
- `const selected = overview && selection !== null && slot.includes(selection.windowId)` — const, line 2130
- `const receding = overview && recedes(slot, selection?.windowId ?? null, selectedRelations, showRelations)` — const, line 2131
- `const measure = FOCUS_MEASURE[window.kind] ?? FOCUS_MEASURE.source` — const, line 2132
- `const title = titleOf(window)` — const, line 2186
- `const ringId = linkedFrom` — const, line 2268
- `const isSel = ringId !== null && slot.includes(ringId)` — const, line 2269
- `const isRel = !isSel && showRelations && slot.some((id)` — const, line 2270
- `const rect = ovLayout?.cards[rowIndex]?.[index]` — const, line 2271
- `const key = slotKey(each.deskId, slot)` — const, line 2273
- `function Sliver(` — function, line 2422
- `function WhichKey()` — function, line 2432
- `const groups: Array<` — const, line 2433
- `const rows = DESK_BINDINGS.filter((binding)` — const, line 2444
- `function OpenBeside(` — function, line 2462
- `const words = filter.trim().toLowerCase()` — const, line 2478
- `const sources = (library ?? []).filter((card)` — const, line 2479
- `const book = focus?.content && (focus.content.kind === "source" || focus.content.kind === "video") ? focus.content : null` — const, line 2480

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: dynamic import; no named call claim
- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `DeskDebugHandle`, `DeskShell`; references `DeskDebugHandle`, `DeskShell`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CompanionDock`, `CompanionHistoryDto`, `ContentRefDto`, `DeskApplyDto`, `DeskApplyInput`, `DeskStateDto`, `SourceLibraryCard`, `TutorCitationDto`
- [[Reference/Desktop/TypeScript/api/poller|src/api/poller.ts]] — import-or-re-export; imports `Poller`, `appPoller`
- [[Reference/Desktop/TypeScript/app/ScreenErrorBoundary|src/app/ScreenErrorBoundary.tsx]] — import-or-re-export; imports `ScreenErrorBoundary`
- [[Reference/Desktop/TypeScript/screens/desks/Shelf|src/screens/desks/Shelf.tsx]] — import-or-re-export; imports `Shelf`, `ShelfRow`
- [[Reference/Desktop/TypeScript/screens/desks/companion/Companion|src/screens/desks/companion/Companion.tsx]] — import-or-re-export; imports `Companion`, `CompanionHandle`
- [[Reference/Desktop/TypeScript/screens/desks/companion/asks|src/screens/desks/companion/asks.ts]] — import-or-re-export; imports `CompanionApi`, `CompanionAsks`, `CompanionExchange`, `companionAsksFor`
- [[Reference/Desktop/TypeScript/screens/desks/companion/model|src/screens/desks/companion/model.ts]] — import-or-re-export; imports `CompanionEvent`, `CompanionState`, `HIDDEN`, `avoidOffset`, `companionStep`
- [[Reference/Desktop/TypeScript/screens/desks/geometry|src/screens/desks/geometry.ts]] — import-or-re-export; imports `DESK_SIZES`, `FOCUS_MEASURE`, `Rect`, `Stage`, `ensureVisible`, `paneRects`, `rowTop`, `sliverSlots`, `slotRects`, `slotVisibility`, `slotWidth`, `softCropMask`, `stepZoom`
- [[Reference/Desktop/TypeScript/screens/desks/keys/listeners|src/screens/desks/keys/listeners.ts]] — import-or-re-export; imports `DeskListenerRouter`, `WINDOW_ATTRIBUTE`, `windowOfTarget`
- [[Reference/Desktop/TypeScript/screens/desks/keys/router|src/screens/desks/keys/router.ts]] — import-or-re-export; imports `BareAltTracker`, `DESK_BINDINGS`, `DeskAction`, `ModifierTracker`, `REAL_TIMERS`, `Timers`, `isTypingTarget`, `resolveKey`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `ClaimedScope`, `ListenerHub`, `ScopeClaims`, `WindowLifecycle`, `WindowScope`, `isPaused`, `windowState`
- [[Reference/Desktop/TypeScript/screens/desks/model/workspace|src/screens/desks/model/workspace.ts]] — import-or-re-export; imports `DeskWindow`, `Step`, `Workspace`, `closeWindow`, `createDesk`, `deskById`, `focusAlong`, `focusPane`, `focusedSlot`, `focusedWindowId`, `moveFocused`, `moveToDesk`, `moveToDeskAt`, `moveWindowTo`, `openBeside`, `pairFocused`, `renameDesk`, `reorderSlots`, `setCompanionDock`, `setCompanionShown`, `setFocus`, `setView`, `slotIndexOf`, `swapInView`, `undoClose`, `unpairFocused`
- [[Reference/Desktop/TypeScript/screens/desks/outbox|src/screens/desks/outbox.ts]] — import-or-re-export; imports `OutboxTransport`, `clientIdFor`
- [[Reference/Desktop/TypeScript/screens/desks/overview/Card|src/screens/desks/overview/Card.tsx]] — import-or-re-export; imports `CardFace`, `LinkLayer`
- [[Reference/Desktop/TypeScript/screens/desks/overview/controller|src/screens/desks/overview/controller.ts]] — import-or-re-export; imports `ANIMATION_FRAMES`, `FrameClock`, `SlotElements`, `ZoomController`, `ZoomPlan`, `cameraTransform`
- [[Reference/Desktop/TypeScript/screens/desks/overview/engine|src/screens/desks/overview/engine.ts]] — import-or-re-export; imports `Camera`, `IDENTITY`, `OVERVIEW`, `ZoomGesture`, `ZoomSource`, `classifyWheel`, `dragProgress`, `dropTarget`, `enteringCamera`, `followSelection`, `moveSelection`, `newZoomGesture`, `normalizedDelta`, `overviewLayout`, `zoomWheel`
- [[Reference/Desktop/TypeScript/screens/desks/overview/links|src/screens/desks/overview/links.ts]] — import-or-re-export; imports `DRAWN_RELATIONS`, `Relation`, `curvedLinks`, `gatherOrder`, `relationsOf`
- [[Reference/Desktop/TypeScript/screens/desks/overview/miniature|src/screens/desks/overview/miniature.ts]] — import-or-re-export; imports `MiniatureBook`, `cloneForMiniature`
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

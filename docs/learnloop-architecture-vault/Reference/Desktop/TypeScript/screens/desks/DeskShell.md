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
| Source lines | 3082 |
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

- `export interface DeskTransport extends OutboxTransport` — interface, line 123
- `export const LIVE_DESK_TRANSPORT: DeskTransport =` — const, line 133
- `export interface PadAskContext` — interface, line 162
- `export interface AskChip` — interface, line 169
- `export function groundingFor(ws: Workspace, chip: AskChip | null, focus: DeskWindow | undefined, status: Record<string, SourceStatus>): Grounding` — function, line 176
- `export interface PadsTransport extends PadsApi` — interface, line 248
- `export const LIVE_PADS_TRANSPORT: PadsTransport =` — const, line 256
- `export interface CompanionTransport extends CompanionApi, SearchApi` — interface, line 276
- `export const LIVE_COMPANION_TRANSPORT: CompanionTransport =` — const, line 280
- `export interface PaneRenderInput` — interface, line 290
- `export interface DeskDebugHandle` — interface, line 306
- `export const KIND_GLYPH: Record<string, string> =` — const, line 341
- `export interface DeskShellProps` — interface, line 394
- `export function DeskShell(` — function, line 423
- `export function isVideoCard(card: SourceLibraryCard): boolean` — function, line 2962
- `export function contentForCard(card: SourceLibraryCard, extractionId: string): ContentRefDto` — function, line 2966

## Internal implementation anchors

- `type Step, moveWindowTo, openBeside, pairFocused, renameDesk, reorderSlots, setFocus, setCompanionDock, setCompanionShown, setView, slotIndexOf, swapInView, undoClose, unpairFocused, type DeskWindow, type Workspace, } from "./model/workspace"` — type, line 28
- `type DeskWindow, type Workspace, } from "./model/workspace"` — type, line 42
- `type Workspace, } from "./model/workspace"` — type, line 43
- `type Rect, type Stage, } from "./geometry"` — type, line 57
- `type Stage, } from "./geometry"` — type, line 58
- `type Camera, type ZoomGesture, type ZoomSource, } from "./overview/engine"` — type, line 73
- `type ZoomGesture, type ZoomSource, } from "./overview/engine"` — type, line 74
- `type ZoomSource, } from "./overview/engine"` — type, line 75
- `type DeskAction, type Timers, } from "./keys/router"` — type, line 88
- `type Timers, } from "./keys/router"` — type, line 89
- `const COMPANION_SIZES_HANDOFF_MS = 250` — const, line 147
- `interface Grounding` — interface, line 150
- `const padBlockId = chip.pad.blockId ?? undefined` — const, line 178
- `const deskId = ws.windows[chip.windowId]?.deskId ?? focus?.deskId` — const, line 182
- `const desk = deskId ? ws.desks.find((each)` — const, line 183
- `const window = ws.windows[id]` — const, line 185
- `const content = window?.content` — const, line 186
- `const span = status[id]?.readingSpan ?? (typeof window.view?.spanId === "string" ? (window.view.spanId as string) : undefined)` — const, line 188
- `const content = ws.windows[chip.windowId]?.content` — const, line 195
- `const content = focus?.content` — const, line 200
- `const span = status[focus.windowId]?.readingSpan ?? (typeof focus.view?.spanId === "string" ? (focus.view.spanId as string) : undefined)` — const, line 204
- `function firstVisibleSpan(windowId: string | null): string | null` — function, line 211
- `const host = document.querySelector(`[$` — const, line 213
- `const top = host.getBoundingClientRect().top` — const, line 215
- `const spans = [...host.querySelectorAll<HTMLElement>("[data-span-id], [data-transcript-span]")]` — const, line 216
- `const visible = spans.find((element)` — const, line 217
- `const PENDING_FIGURES = new WeakMap<object, PendingFigures>()` — const, line 221
- `function pendingFiguresFor(store: object): PendingFigures` — function, line 223
- `let figures = PENDING_FIGURES.get(store)` — let, line 224
- `function errorText(error: unknown): string` — function, line 232
- `function keyAfterLast(blocks: Array<` — function, line 237
- `function threadTitle(thread: CompanionExchange[]): string` — function, line 241
- `const last = thread[thread.length - 1]` — const, line 242
- `const UNDO_CLOSE_MS = 9_000` — const, line 297
- `const TOAST_MS = 2_200` — const, line 299
- `const VIEW_SAVE_IDLE_MS = 2_000` — const, line 301
- `const MOVED_NOTICE_MS = 6_000` — const, line 303
- `function displayedCamera(world: HTMLElement): Camera | null` — function, line 316
- `const shown = typeof getComputedStyle === "function" ? getComputedStyle(world).transform : ""` — const, line 317
- `const match = /^matrix\(([^)]+)\)$/.exec(shown ?? "")` — const, line 318
- `function prefersReducedMotion(): boolean` — function, line 324
- `function slotKey(deskId: string, slot: string[]): string` — function, line 333
- `function intersects(rect: Rect, stage: Stage): boolean` — function, line 337
- `const KIND_WORD: Record<string, string> =` — const, line 353
- `function defaultMintId(prefix: string): string` — function, line 365
- `function shortName(title: string): string` — function, line 373
- `const words = title.split(/\s+/).filter(Boolean)` — const, line 374
- `function readStored(key: string): string | null` — function, line 378
- `function writeStored(key: string, value: string): void` — function, line 386
- `const store = useMemo( ()` — const, line 443
- `const storeWs = useSyncExternalStore(store.subscribe, store.getSnapshot)` — const, line 447
- `const ws: Workspace | null = storeReady ? storeWs : null` — const, line 451
- `const wsRef = useMemo(()` — const, line 452
- `const deskKey = `learnloop.desks.current.$` — const, line 454
- `const stageRef = useRef<HTMLElement | null>(null)` — const, line 469
- `const viewport = initialViewport ??` — const, line 471
- `const shelf = viewport.width < DESK_SIZES.shelfFoldBelow ? DESK_SIZES.shelfRail : DESK_SIZES.shelf` — const, line 472
- `const padHandles = useRef(new Map<string, PadStackHandle>())` — const, line 498
- `const drainingRef = useRef(false)` — const, line 502
- `const companionRef = useRef<CompanionHandle | null>(null)` — const, line 504
- `const preOverview = useRef<` — const, line 507
- `const worldRef = useRef<HTMLDivElement | null>(null)` — const, line 508
- `const boxEls = useRef(new Map<string, HTMLElement>())` — const, line 511
- `const innerEls = useRef(new Map<string, HTMLElement>())` — const, line 512
- `const cardEls = useRef(new Map<string, HTMLElement>())` — const, line 513
- `const ringEls = useRef(new Map<string, HTMLElement>())` — const, line 514
- `const slotElements = useCallback((): Map<string, SlotElements>` — const, line 515
- `const out = new Map<string, SlotElements>()` — const, line 516
- `const lateEls = useRef(new Map<string, HTMLElement>())` — const, line 520
- `const sliverEls = useRef(new Map<string, HTMLElement>())` — const, line 521
- `const miniatures = useMemo(()` — const, line 522
- `const miniHosts = useRef(new Map<string, HTMLDivElement>())` — const, line 523
- `const onEndRef = useRef<(goal: 0 | 1, base: 0 | 1)` — const, line 524
- `const controller = useMemo(()` — const, line 525
- `const jumps = useRef(new Map<string, (spanId: string)` — const, line 526
- `const media = useRef(new Map<string, ()` — const, line 527
- `const pendingJump = useRef(new Map<string, string>())` — const, line 528
- `const toastNow = useCallback((text: string)` — const, line 530
- `const handle = timers.set(()` — const, line 533
- `const setCurrentDeskId = useCallback((deskId: string | null)` — const, line 539
- `const commit = useCallback((step: Step)` — const, line 544
- `const total = notice.dropped + notice.lost` — const, line 553
- `const chain = useCallback((first: Step, next: (ws: Workspace)` — const, line 561
- `const second = next(first.ws)` — const, line 562
- `const firstRun = useCallback(async (base: Workspace, cards: SourceLibraryCard[] | null): Promise<Step>` — const, line 566
- `const card = firstSourceId ? cards?.find((entry)` — const, line 567
- `const deskId = mintId("desk")` — const, line 568
- `const created = createDesk(base, deskId, card ? `new desk · $` — const, line 569
- `const extractionId = await transport.resolveExtraction(card.sourceId).catch(()` — const, line 571
- `let live = true` — let, line 577
- `const desk = ws ? deskById(ws, currentDeskId) ?? ws.desks[0] ?? null : null` — const, line 599
- `const deskId = desk?.deskId ?? null` — const, line 600
- `const focusId = ws && desk ? focusedWindowId(ws, desk) : null` — const, line 601
- `const focusSlotIndex = ws && desk ? focusedSlot(ws, desk) : -1` — const, line 602
- `const slotCount = desk?.slots.length ?? 0` — const, line 610
- `const keepPrevious = useRef(false)` — const, line 611
- `const next = ensureVisible(cams[deskId] ?? 0, focusSlotIndex, slotCount, stage, keepPrevious.current)` — const, line 615
- `const node = stageRef.current` — const, line 623
- `const measure = ()` — const, line 624
- `const next =` — const, line 626
- `const now = stageNow.current` — const, line 627
- `const shell = node?.closest(".desk-shell") as HTMLElement | null` — const, line 634
- `const observer = typeof ResizeObserver === "undefined" || !node ? null : new ResizeObserver(measure)` — const, line 638
- `const cam = deskId ? camX[deskId] ?? 0 : 0` — const, line 647
- `const visibility = useMemo(()` — const, line 648
- `const deskIndex = ws && desk ? ws.desks.indexOf(desk) : 0` — const, line 649
- `const lifecycles = useMemo(()` — const, line 653
- `const out: Record<string, WindowLifecycle> =` — const, line 654
- `const onCurrent = each.deskId === deskId` — const, line 657
- `const activeWindowId = Object.values(lifecycles).find((each)` — const, line 673
- `const held = document.activeElement` — const, line 675
- `const owner = held && held !== document.body ? windowOfTarget(held) : null` — const, line 676
- `const target = activeWindowId ? document.querySelector<HTMLElement>(`[$` — const, line 678
- `const lifecyclesRef = useRef(lifecycles)` — const, line 684
- `const focusIdRef = useRef(focusId)` — const, line 686
- `const knownOwners = useRef(new Set<string>())` — const, line 690
- `const focusModeRef = useRef(focusMode)` — const, line 702
- `const switchDesk = useCallback((direction: -1 | 1): boolean` — const, line 705
- `const current = wsRef.current` — const, line 706
- `const index = current.desks.findIndex((each)` — const, line 707
- `const next = current.desks[index + direction]` — const, line 708
- `const deskIdRef = useRef(deskId)` — const, line 713
- `const titleOf = useCallback((window: DeskWindow | undefined): string` — const, line 716
- `const known = status[window.windowId]?.title` — const, line 718
- `const content = window.content` — const, line 720
- `const ovLayout = useMemo(()` — const, line 730
- `const ovLayoutRef = useRef(ovLayout)` — const, line 731
- `const stageNow = useRef(stage)` — const, line 733
- `const camXRef = useRef(camX)` — const, line 735
- `const overviewRef = useRef(overview)` — const, line 737
- `const ovCamRef = useRef(ovCam)` — const, line 739
- `const selectionRef = useRef(selection)` — const, line 741
- `const visitedRef = useRef(visited)` — const, line 743
- `const showRelationsRef = useRef(showRelations)` — const, line 745
- `const reduced = reducedMotion ?? prefersReducedMotion()` — const, line 747
- `const transitionGen = useRef(0)` — const, line 750
- `const panEaseRef = useRef(panEase)` — const, line 751
- `const pendingLeave = useRef<` — const, line 753
- `const cardOf = useCallback((windowId: string | null | undefined): Rect | null` — const, line 756
- `const layout = ovLayoutRef.current` — const, line 757
- `const current = wsRef.current` — const, line 758
- `const index = slotIndexOf(each, windowId)` — const, line 761
- `const readingRectOf = useCallback((current: Workspace, row: number, index: number, readingRow: number, cams: Record<string, number>, st: Stage): Rect` — const, line 769
- `const each = current.desks[row]` — const, line 770
- `const rect = slotRects(each.slots.length, st)[index]` — const, line 771
- `const relatedTo = useCallback((windowId: string | null | undefined): Relation[]` — const, line 775
- `const recedes = useCallback((slot: string[], selected: string | null, related: Relation[], relationsOn: boolean): boolean` — const, line 778
- `const planZoom = useCallback((base: 0 | 1, readingDeskId: string, cams: Record<string, number>, selected: string | null, B: Camera, fullWindowId: string | null = null): ZoomPlan | null` — const, line 783
- `const current = wsRef.current` — const, line 784
- `const layout = ovLayoutRef.current` — const, line 785
- `const st = stageNow.current` — const, line 786
- `const readingRow = Math.max(0, current.desks.findIndex((each)` — const, line 788
- `const related = relatedTo(selected)` — const, line 789
- `const items: ZoomPlan["items"] = []` — const, line 790
- `const rings: ZoomPlan["rings"] = []` — const, line 791
- `const a = readingRectOf(current, row, index, readingRow, cams, st)` — const, line 793
- `const b = layout.cards[row][index]` — const, line 794
- `const readingPanes = paneRects(a, slot.length)` — const, line 795
- `const cardPanes = paneRects(b, slot.length)` — const, line 796
- `const live = visitedRef.current.has(each.deskId) && each.deskId === readingDeskId && intersects(a, st)` — const, line 797
- `const recede = recedes(slot, selected, related, showRelationsRef.current)` — const, line 798
- `const focus = selected !== null && slot.includes(selected)` — const, line 799
- `const isRelated = showRelationsRef.current && slot.some((id)` — const, line 800
- `const pa = id === fullWindowId && each.deskId === readingDeskId ?` — const, line 803
- `const pb = cardPanes[pane]` — const, line 804
- `const zoomTargets = useCallback(()` — const, line 812
- `const crossfade = useCallback((enter: boolean, to:` — const, line 824
- `const world = worldRef.current` — const, line 826
- `const id = deskIdRef.current` — const, line 832
- `const target = to ?? (preOverview.current ?` — const, line 841
- `const beginEnter = useCallback((): boolean` — const, line 852
- `const id = deskIdRef.current` — const, line 854
- `const selected = focusIdRef.current` — const, line 862
- `const B = enteringCamera(cardOf(selected), stageNow.current)` — const, line 864
- `const plan = planZoom(0, id, camXRef.current, selected, B)` — const, line 869
- `const beginLeave = useCallback((to:` — const, line 877
- `const shown = displayedCamera(worldRef.current) ?? ovCamRef.current` — const, line 887
- `const target = to ?? preOverview.current ?? (selectionRef.current ?` — const, line 893
- `const deskIdTo = target.deskId` — const, line 895
- `const windowTo = "windowId" in target ? target.windowId : target.focusId` — const, line 896
- `const current = wsRef.current` — const, line 897
- `const each = deskById(current, deskIdTo)` — const, line 898
- `const fullWindowId = focusAfter && windowTo ? windowTo : null` — const, line 900
- `const node = stageRef.current` — const, line 909
- `const cams =` — const, line 913
- `const index = windowTo ? slotIndexOf(each, windowTo) : -1` — const, line 914
- `const plan = planZoom(1, deskIdTo, cams, windowTo, ovCamRef.current, fullWindowId)` — const, line 916
- `const plan = controller.plan` — const, line 932
- `const leave = pendingLeave.current` — const, line 950
- `const generation = transitionGen.current` — const, line 964
- `const toggleOverview = useCallback((to:` — const, line 973
- `const focusWindow = focusId ? ws.windows[focusId] : null` — const, line 990
- `const first = ws.desks.find((each)` — const, line 995
- `const windowId = first ? first.slots[0].find((id)` — const, line 996
- `const followMoved = useRef(false)` — const, line 1000
- `const rect = cardOf(selection.windowId)` — const, line 1004
- `const moveOverviewSelection = useCallback((direction: "left" | "right" | "up" | "down")` — const, line 1011
- `const layout = ovLayoutRef.current` — const, line 1012
- `const current = wsRef.current` — const, line 1013
- `const sel = selectionRef.current` — const, line 1014
- `let row = sel ? current.desks.findIndex((each)` — let, line 1016
- `let slot = sel ? slotIndexOf(current.desks[row] ?? current.desks[0], sel.windowId) : 0` — let, line 1017
- `const next = moveSelection(layout,` — const, line 1022
- `const each = current.desks[next.row]` — const, line 1023
- `const windowId = each?.slots[next.slot]?.find((id)` — const, line 1024
- `const gather = useCallback((toNewDesk: boolean)` — const, line 1032
- `const current = wsRef.current` — const, line 1033
- `const id = deskIdRef.current` — const, line 1034
- `const focus = focusIdRef.current` — const, line 1035
- `const each = id ? deskById(current, id) : null` — const, line 1036
- `const related = relationsOf(current, focus).filter((relation)` — const, line 1043
- `const moving = [focus, ...related.slice(0, DRAWN_RELATIONS).map((relation)` — const, line 1056
- `const newDeskId = mintId("desk")` — const, line 1057
- `const title = `gathered · $` — const, line 1058
- `let step = createDesk(current, newDeskId, title)` — let, line 1059
- `let after: string | null = null` — let, line 1060
- `const next = moveToDesk(step.ws, id, windowId, newDeskId, after)` — const, line 1062
- `const focused = setFocus(step.ws, newDeskId, focus)` — const, line 1066
- `const run = useCallback((action: DeskAction): boolean` — const, line 1074
- `const current = wsRef.current` — const, line 1075
- `const id = deskIdRef.current` — const, line 1076
- `const focus = focusIdRef.current` — const, line 1078
- `const stack = focusedStackRef.current()` — const, line 1085
- `const step = focusPane(current, id, action.direction)` — const, line 1087
- `const sel = overviewRef.current ? selectionRef.current : null` — const, line 1093
- `const each = deskById(current, sel.deskId)` — const, line 1095
- `const index = each ? slotIndexOf(each, sel.windowId) : -1` — const, line 1096
- `const sel = selectionRef.current` — const, line 1107
- `const row = current.desks.findIndex((each)` — const, line 1109
- `const to = current.desks[row + action.direction]` — const, line 1110
- `const from = current.desks[row]` — const, line 1111
- `const index = slotIndexOf(from, sel.windowId)` — const, line 1113
- `const sel = selectionRef.current` — const, line 1126
- `const title = titleOf(current.windows[focus])` — const, line 1150
- `const window = current.windows[focus]` — const, line 1165
- `const zoom = typeof window?.view?.zoom === "number" ? (window.view.zoom as number) : 1` — const, line 1166
- `const next = stepZoom(zoom, action.direction)` — const, line 1167
- `const desk = deskById(current, id)` — const, line 1173
- `const index = slotIndexOf(desk, focus)` — const, line 1175
- `const shown = visibilityRef.current.filter((slot)` — const, line 1176
- `const other = shown.find((slot)` — const, line 1177
- `const toggle = focus ? media.current.get(focus) : undefined` — const, line 1182
- `const stack = focusedStackRef.current()` — const, line 1188
- `const stack = focusedStackRef.current()` — const, line 1194
- `const stack = focusedStackRef.current()` — const, line 1200
- `const stack = focusedStackRef.current()` — const, line 1206
- `const stack = focusedStackRef.current()` — const, line 1213
- `const visibilityRef = useRef(visibility)` — const, line 1229
- `const runRef = useRef(run)` — const, line 1231
- `const modifiers = useMemo(()` — const, line 1236
- `const altTracker = useMemo( ()` — const, line 1237
- `const router = useMemo(()` — const, line 1241
- `const current = wsRef.current` — const, line 1246
- `const id = deskIdRef.current` — const, line 1247
- `const owner = current.windows[windowId]` — const, line 1249
- `const outcome = altTracker.release(event)` — const, line 1277
- `const open = claimed.current.get(focusIdRef.current ?? "")` — const, line 1286
- `const has = (scope: ClaimedScope)` — const, line 1287
- `const resolution = resolveKey(event,` — const, line 1288
- `const claimed = useRef(new Map<string, Map<ClaimedScope, Set<string>>>())` — const, line 1314
- `const claimsByWindow = useRef(new Map<string, ScopeClaims>())` — const, line 1315
- `const claimsFor = useCallback((windowId: string): ScopeClaims` — const, line 1316
- `let claims = claimsByWindow.current.get(windowId)` — let, line 1317
- `const byScope = claimed.current.get(windowId) ?? new Map<ClaimedScope, Set<string>>()` — const, line 1321
- `const owners = byScope.get(scope) ?? new Set<string>()` — const, line 1322
- `const hubs = useRef(new Map<string, ListenerHub>())` — const, line 1333
- `const hubFor = useCallback((windowId: string): ListenerHub` — const, line 1334
- `let hub = hubs.current.get(windowId)` — let, line 1335
- `const world = worldRef.current` — const, line 1347
- `const mainRef = useRef<HTMLElement | null>(null)` — const, line 1352
- `const gesture = useRef<` — const, line 1353
- `const endGesture = useCallback(()` — const, line 1354
- `const g = gesture.current` — const, line 1355
- `const current = wsRef.current` — const, line 1365
- `const id = deskIdRef.current` — const, line 1366
- `const each = id ? deskById(current, id) : null` — const, line 1367
- `const st = stageNow.current` — const, line 1369
- `const rects = slotRects(each.slots.length, st)` — const, line 1370
- `const cam = camXRef.current[id] ?? 0` — const, line 1371
- `let best = 0` — let, line 1372
- `const snapped = ensureVisible(rects[best].x - DESK_SIZES.side, best, each.slots.length, st)` — const, line 1376
- `const target = each.slots[best].find((windowId)` — const, line 1378
- `const main = mainRef.current` — const, line 1384
- `const onWheel = (event: WheelEvent)` — const, line 1386
- `const target = event.target as Element | null` — const, line 1387
- `const st = stageNow.current` — const, line 1392
- `const now = performance.now()` — const, line 1393
- `let g = gesture.current` — let, line 1394
- `const kind = classifyWheel(event, modifiers.read(), st.height)` — const, line 1398
- `const ovPlain = overviewRef.current && kind.kind !== "zoom"` — const, line 1400
- `const id = deskIdRef.current` — const, line 1426
- `const each = id ? deskById(wsRef.current, id) : null` — const, line 1427
- `const travel = Math.abs(dx) > Math.abs(dy) ? dx : dy` — const, line 1429
- `const max = Math.max(0, slotRects(each.slots.length, st).reduce((end, rect)` — const, line 1430
- `const result = zoomWheel(g.zoom, dy, now,` — const, line 1440
- `const stepped = result.step` — const, line 1442
- `const began = overviewRef.current ? beginLeave(selectionRef.current ?` — const, line 1444
- `const began = stepped.goal === 1 ? beginEnter() : beginLeave(selectionRef.current ?` — const, line 1450
- `const how = g.source === "pinch" ? "pinch" : modifiers.read(event).alt ? "alt + scroll" : "ctrl + scroll"` — const, line 1456
- `const drag = useRef<` — const, line 1470
- `const onStagePointerDown = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1471
- `const target = event.target as Element` — const, line 1472
- `const onCard = target.closest("[data-desk-slot]")` — const, line 1473
- `const onSliver = target.closest(".desk-sliver") !== null` — const, line 1475
- `const inContent = !onSliver && target.closest(".desk-slot-inner, button, input, textarea") !== null` — const, line 1476
- `const key = onCard.getAttribute("data-desk-slot-key") ?? undefined` — const, line 1479
- `const windowId = onCard.getAttribute("data-desk-slot-window") ?? undefined` — const, line 1480
- `const deskOf = onCard.getAttribute("data-desk-slot-desk") ?? undefined` — const, line 1481
- `const onStagePointerMove = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1495
- `const d = drag.current` — const, line 1496
- `const dx = event.clientX - d.x` — const, line 1498
- `const dy = event.clientY - d.y` — const, line 1499
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1518
- `const cancelDrag = useCallback(()` — const, line 1526
- `const d = drag.current` — const, line 1527
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1535
- `const cancelDragRef = useRef(cancelDrag)` — const, line 1541
- `const scrubbedClick = useRef(false)` — const, line 1544
- `const onStagePointerUp = useCallback((event: React.PointerEvent<HTMLElement>)` — const, line 1545
- `const d = drag.current` — const, line 1546
- `const element = d.windowId ? boxEls.current.get(d.windowId) : null` — const, line 1556
- `const layout = ovLayoutRef.current` — const, line 1567
- `const stageBox = (event.currentTarget as HTMLElement).getBoundingClientRect()` — const, line 1568
- `const point =` — const, line 1570
- `const drop = dropTarget(layout, point)` — const, line 1571
- `const current = wsRef.current` — const, line 1572
- `const to = drop ? current.desks[drop.row] : null` — const, line 1573
- `const from = slotIndexOf(to, d.windowId)` — const, line 1576
- `const world = worldRef.current` — const, line 1587
- `const observer = new MutationObserver((records)` — const, line 1589
- `const node = record.target instanceof Element ? record.target : record.target.parentElement` — const, line 1591
- `const windowId = windowOfTarget(node)` — const, line 1592
- `const handle = timers.set(()` — const, line 1605
- `const body = [...document.querySelectorAll<HTMLElement>("[data-desk-window]")].find((pane)` — const, line 1608
- `const node = miniatures.get(windowId)` — const, line 1618
- `const node = host.firstElementChild as HTMLElement | null` — const, line 1621
- `const openContent = useCallback((content: ContentRefDto, options:` — const, line 1641
- `const current = wsRef.current` — const, line 1642
- `const id = deskIdRef.current` — const, line 1643
- `const step = openBeside(current, id, content, ()` — const, line 1645
- `const jump = jumps.current.get(step.windowId)` — const, line 1652
- `const handle = timers.set(()` — const, line 1658
- `const next = new Set(now)` — const, line 1661
- `const openHit = useCallback((hit:` — const, line 1671
- `const card = library?.find((entry)` — const, line 1673
- `const kind = card && isVideoCard(card) ? "video" : "source"` — const, line 1674
- `const asks = useMemo( ()` — const, line 1681
- `const shownVault = useRef<` — const, line 1691
- `const before = shownVault.current` — const, line 1693
- `const statusRef = useRef(status)` — const, line 1697
- `const companionStateRef = useRef(companionState)` — const, line 1699
- `const chipRef = useRef(chip)` — const, line 1701
- `const searchOpenRef = useRef(false)` — const, line 1703
- `const anchoredAt = useRef(0)` — const, line 1705
- `const groundingRef = useRef<Grounding>(` — const, line 1706
- `const stepCompanion = useCallback((event: CompanionEvent)` — const, line 1709
- `const before = companionStateRef.current` — const, line 1710
- `const next = companionStep(before, event)` — const, line 1711
- `const id = deskIdRef.current` — const, line 1716
- `const lastPointer = useRef<` — const, line 1721
- `const stageNode = stageRef.current` — const, line 1723
- `const onMove = (event: PointerEvent)` — const, line 1725
- `const box = stageNode.getBoundingClientRect()` — const, line 1726
- `const companionKey = (atDock: boolean)` — const, line 1735
- `let anchor: Rect | null = null` — let, line 1740
- `const id = focusIdRef.current` — const, line 1742
- `const selected: WindowSelection | null = id ? readWindowSelection(id, stageRef.current) : null` — const, line 1743
- `const companionKeyRef = useRef(companionKey)` — const, line 1753
- `const companionInit = useRef(false)` — const, line 1758
- `const opening = deskById(ws, deskId)` — const, line 1761
- `const shown: CompanionState =` — const, line 1766
- `const snapCompanion = useCallback((dock: CompanionDock)` — const, line 1772
- `const id = deskIdRef.current` — const, line 1774
- `const before = companionStateRef.current` — const, line 1776
- `const next: CompanionState =` — const, line 1777
- `const viewKey = `$` — const, line 1785
- `const lastViewKey = useRef(viewKey)` — const, line 1786
- `const stageNode = stageRef.current` — const, line 1795
- `const onScroll = (event: Event)` — const, line 1797
- `const target = event.target instanceof Element ? event.target : null` — const, line 1800
- `const onSelection = ()` — const, line 1810
- `const id = focusIdRef.current` — const, line 1811
- `const panel = companionRef.current?.rect() ?? null` — const, line 1812
- `const selected = readWindowSelection(id, stageRef.current)` — const, line 1817
- `const askCompanion = useCallback((question: string)` — const, line 1824
- `const grounding = groundingRef.current` — const, line 1825
- `const spanId = grounding.spanId ?? firstVisibleSpan(grounding.spanWindowId ?? grounding.windowId ?? null)` — const, line 1827
- `const lifecycle = lifecyclesRef.current[grounding.windowId ?? ""]` — const, line 1833
- `const selected = chipRef.current` — const, line 1835
- `const padLine = selected?.pad ? selected.quote : null` — const, line 1838
- `const loadHistory = useCallback((query: string, cursor?: string)` — const, line 1854
- `const deskTitle = useCallback((id: string | null)` — const, line 1856
- `const openClaim = useCallback((citation: Pick<TutorCitationDto, "extractionId" | "spanId"> &` — const, line 1862
- `let sourceId = citation.sourceId ?? null` — let, line 1863
- `let kind: "source" | "video" = "source"` — let, line 1864
- `const content = window.content` — const, line 1866
- `const open = (found: string, known: "source" | "video")` — const, line 1873
- `const card = library?.find((entry)` — const, line 1874
- `const shown = card && isVideoCard(card) ? "video" : known` — const, line 1875
- `const ref =` — const, line 1876
- `const openThread = useCallback((exchange: CompanionExchange)` — const, line 1894
- `const root = exchange.answer?.readerAnswerEventId || exchange.answer?.eventId` — const, line 1895
- `const openSearchRow = useCallback((row: SearchRow)` — const, line 1902
- `const id = deskIdRef.current` — const, line 1903
- `const ref = row.ref` — const, line 1908
- `const note = row.raw as` — const, line 1916
- `const target = row.target ??` — const, line 1918
- `const passage = (row.raw as` — const, line 1927
- `const extractionId = passage && (passage.kind === "source" || passage.kind === "video") ? passage.extractionId : null` — const, line 1928
- `const ensuredDesks = useRef(new Set<string>())` — const, line 1940
- `const desk = ws && deskId ? deskById(ws, deskId) : undefined` — const, line 1942
- `const before = new Set(ws.runningPadIds ?? [])` — const, line 1946
- `const step = ensureRunningPad(ws, deskId, ()` — const, line 1947
- `const prefetched = useRef(new Set<string>())` — const, line 1954
- `const migratedStacks = useRef(new Set<string>())` — const, line 1967
- `let next = ws` — let, line 1970
- `const ops: Step["ops"] = []` — const, line 1971
- `const legacy = Array.isArray(window.view?.addedPads) ? (window.view.addedPads as unknown[]).filter((id): id is string` — const, line 1975
- `const step = addToStack(next, window.deskId, window.windowId, padId)` — const, line 1977
- `const refreshCarried = useCallback(()` — const, line 1985
- `const carryQuestion = useCallback((text: string, origin:` — const, line 1996
- `const carried = Promise.resolve().then(()` — const, line 1997
- `const openPassage = useCallback((extractionId: string, spanId: string | null, t?: number, sourceId?: string | null)` — const, line 2006
- `const sourcePieces = useCallback((): SourcePiece[]` — const, line 2013
- `const current = wsRef.current` — const, line 2014
- `const id = deskIdRef.current` — const, line 2015
- `const each = id ? deskById(current, id) : null` — const, line 2016
- `const out: SourcePiece[] = []` — const, line 2018
- `const window = current.windows[windowId]` — const, line 2020
- `const content = window?.content` — const, line 2021
- `const spanId = statusRef.current[windowId]?.readingSpan ?? firstVisibleSpan(windowId)` — const, line 2023
- `const element = document.querySelector(`[$` — const, line 2025
- `const text = (element?.textContent ?? "").replace(/\s+/g, " ").trim().slice(0, 600)` — const, line 2026
- `const title = titleOf(window)` — const, line 2028
- `const pendingFigures = useMemo(()` — const, line 2035
- `const padsHost = useMemo<PadsHost>(()` — const, line 2036
- `const first = await padsTransport.figureRequest(` — const, line 2052
- `const job = first.state !== "pending" ? first : await new Promise<typeof first>((resolve, reject)` — const, line 2053
- `const figure = job.result?.figure` — const, line 2068
- `const window = wsRef.current.windows[windowId]` — const, line 2076
- `const window = wsRef.current.windows[windowId]` — const, line 2081
- `const focusedStack = (): PadStackHandle | null` — const, line 2092
- `const focusedStackRef = useRef(focusedStack)` — const, line 2093
- `const newPadBeside = useCallback(()` — const, line 2097
- `const id = deskIdRef.current` — const, line 2098
- `const selected = focusIdRef.current ? readWindowSelection(focusIdRef.current, stageRef.current) : null` — const, line 2100
- `const padId = mintId("pad")` — const, line 2101
- `const title = selected ? `Scratchpad · “$` — const, line 2102
- `const refused = store.commitPad(padId, [` — const, line 2103
- `const newPadBesideRef = useRef(newPadBeside)` — const, line 2110
- `const deskPadIds = useCallback((id: string | null): string[]` — const, line 2114
- `const runningPadOf = useCallback((id: string | null): string | null` — const, line 2120
- `const answerProposals = useCallback((exchange: CompanionExchange): ProposedDiff[]` — const, line 2127
- `const answer = exchange.answer` — const, line 2128
- `const known = runningPadOf(exchange.deskId)` — const, line 2129
- `const lines = answer.answerMd.split("\n").map((line)` — const, line 2131
- `const padId = runningPadOf(exchange.deskId)` — const, line 2139
- `const now = padId ? store.pads[padId] : null` — const, line 2140
- `const refused = store.commitPad(padId, [` — const, line 2142
- `const drainWrite = useCallback(async (padId: string, op: "keep" | "unkeep", version: number): Promise<void>` — const, line 2153
- `const refused = store.commitPad(padId, [` — const, line 2156
- `const unionKey = useRef<Record<string, string>>(` — const, line 2165
- `const padVersionNow = store.getPadVersion()` — const, line 2166
- `const stage = stageRef.current` — const, line 2168
- `let live = true` — let, line 2170
- `const read = ()` — const, line 2171
- `const desk = deskById(wsRef.current, deskId)` — const, line 2172
- `const content = wsRef.current.windows[id]?.content` — const, line 2174
- `const lifecycle = lifecyclesRef.current[id]` — const, line 2175
- `const range = visibleSpanRange(stage, id)` — const, line 2177
- `const key = `$` — const, line 2179
- `const extractionId = content.extractionId` — const, line 2182
- `const links = union.spans.flatMap((span)` — const, line 2185
- `let frame: ReturnType<typeof setTimeout> | null = null` — let, line 2191
- `const onScroll = ()` — const, line 2192
- `const settle = setTimeout(read, 800)` — const, line 2198
- `const padLinks = useMemo<PadLink[]>(()` — const, line 2208
- `const seen = new Set<string>()` — const, line 2209
- `const out: PadLink[] = []` — const, line 2210
- `const key = `$` — const, line 2213
- `const surfacedCarried = useRef(new Set<string>())` — const, line 2221
- `const onCarriedSurfaced = useCallback((question: CarriedQuestionDto)` — const, line 2222
- `const viewTimers = useRef(new Map<string,` — const, line 2230
- `const shellTimers = useRef(new Set<unknown>())` — const, line 2231
- `const statusFor = useMemo(()` — const, line 2243
- `const onStatusFor = useCallback((windowId: string)` — const, line 2244
- `let handler = statusFor.get(windowId)` — let, line 2245
- `const previous = viewTimers.current.get(windowId)` — const, line 2254
- `const save = ()` — const, line 2256
- `const current = store.ws` — const, line 2257
- `const window = current.windows[windowId]` — const, line 2258
- `const jumpReadyFor = useMemo(()` — const, line 2276
- `const onJumpReadyFor = useCallback((windowId: string)` — const, line 2277
- `let handler = jumpReadyFor.get(windowId)` — let, line 2278
- `const pending = pendingJump.current.get(windowId)` — const, line 2286
- `const mediaReadyFor = useMemo(()` — const, line 2297
- `const onMediaReadyFor = useCallback((windowId: string)` — const, line 2298
- `let handler = mediaReadyFor.get(windowId)` — let, line 2299
- `const railNodeFor = useMemo(()` — const, line 2310
- `const onRailNode = useCallback((windowId: string)` — const, line 2311
- `let handler = railNodeFor.get(windowId)` — let, line 2312
- `const railPanelOf = useCallback((deskOf: string, extractionId: string): string | null` — const, line 2321
- `const desk = deskById(ws, deskOf)` — const, line 2323
- `const panels = desk.slots.flat().filter((id)` — const, line 2325
- `const content = ws.windows[id]?.content` — const, line 2326
- `const claimed = railClaims[`$` — const, line 2329
- `const sourceWindowOf = useCallback((deskOf: string, extractionId: string): string | null` — const, line 2333
- `const desk = deskById(ws, deskOf)` — const, line 2335
- `const content = ws.windows[id]?.content` — const, line 2338
- `const undoShown = undo && undo.deskId === deskId && undo.until > timers.now() && (ws?.closed[undo.deskId] ?? []).some((entry)` — const, line 2346
- `const handle = timers.set(()` — const, line 2350
- `const paneBody = (window: DeskWindow, lifecycle: WindowLifecycle): ReactNode` — const, line 2364
- `const content = window.content` — const, line 2365
- `const card = content && (content.kind === "source" || content.kind === "video") ? library?.find((entry)` — const, line 2366
- `const stack = window.stack ?? (content?.kind === "pad" ? [` — const, line 2369
- `const railPanel = railPanelOf(window.deskId, content.extractionId)` — const, line 2376
- `const railNode = railPanel ? railHosts[railPanel] ?? null : null` — const, line 2377
- `const railContent = railPanel ? ws.windows[railPanel]?.content : null` — const, line 2378
- `const railTab = railContent?.kind === "panel" && railContent.panel === "notes" ? "notes" : "guide"` — const, line 2379
- `const extractionId = content.extractionId ?? ""` — const, line 2397
- `const owner = railPanelOf(window.deskId, extractionId)` — const, line 2398
- `const target = content.extractionId ? sourceWindowOf(window.deskId, content.extractionId) : null` — const, line 2415
- `const jump = jumps.current.get(target)` — const, line 2418
- `const linkedFrom = overview || zooming ? selection?.windowId ?? focusId : null` — const, line 2442
- `const selectedRelations = relatedTo(linkedFrom)` — const, line 2443
- `const linkRects = new Map<string, Rect>()` — const, line 2444
- `const rect = ovLayout?.cards[row]?.[index]` — const, line 2446
- `const fromCard = linkedFrom ? linkRects.get(linkedFrom) ?? null : null` — const, line 2449
- `const links = fromCard ? curvedLinks(fromCard, selectedRelations.filter((relation)` — const, line 2450
- `const ghosts: Array<` — const, line 2453
- `const row = ws.desks.findIndex((each)` — const, line 2455
- `const each = ws.desks[row]` — const, line 2456
- `const sameDesk = selectedRelations.filter((relation)` — const, line 2458
- `const linked = slot.some((id)` — const, line 2462
- `const movedShown = movedNotice && movedNotice.deskId === deskId && movedNotice.until > timers.now() ? movedNotice : null` — const, line 2467
- `const focusWindow = focusId ? ws.windows[focusId] : undefined` — const, line 2468
- `const thread = asks.thread(deskId)` — const, line 2470
- `const grounding: Grounding = groundingFor(ws, chip, focusWindow, status)` — const, line 2471
- `const focusZoom = typeof focusWindow?.view?.zoom === "number" ? (focusWindow.view.zoom as number) : 1` — const, line 2473
- `const windowPlaces = ws.desks.flatMap((each, rowIndex)` — const, line 2476
- `const eachCam = camX[each.deskId] ?? 0` — const, line 2477
- `const rects = slotRects(each.slots.length, stage)` — const, line 2478
- `const top = rowTop(rowIndex, stage) - rowTop(deskIndex, stage)` — const, line 2479
- `const slotReading =` — const, line 2481
- `const slotCard = ovLayout?.cards[rowIndex]?.[index] ?? slotReading` — const, line 2482
- `const readingPanes = paneRects(slotReading, slot.length)` — const, line 2483
- `const cardPanes = paneRects(slotCard, slot.length)` — const, line 2484
- `const window = ws.windows[id]` — const, line 2486
- `const sliverDesk = leaveTarget ? deskById(ws, leaveTarget.deskId) : desk` — const, line 2493
- `const sliverCam = leaveTarget && sliverDesk ? leaveTarget.cams[sliverDesk.deskId] ?? 0 : cam` — const, line 2494
- `const slivers = sliverDesk && !focusMode ? sliverSlots(sliverCam, sliverDesk.slots.length, stage) :` — const, line 2495
- `const shelfRows: ShelfRow[] = desk ? desk.slots.flatMap((slot, index)` — const, line 2496
- `const window = ws.windows[id]` — const, line 2498
- `const kind = window?.kind ?? "source"` — const, line 2499
- `const hints = overview ? [["h j k l", "select"], ["↵ / click", "open"], ["alt+↵", "open in focus"], ["alt+[ ]", "move"], ["alt+shift+j/k", "to a desk"], ["drag", "move a card"], ["b", "relations"], ["g", "hold: gather"], ["o / esc", "back"]] : focusMode ? [["…` — const, line 2513
- `const title = (event.target as HTMLInputElement).value.trim()` — const, line 2535
- `const id = mintId("desk")` — const, line 2561
- `const id = window.windowId` — const, line 2619
- `const onCurrent = each.deskId === deskId` — const, line 2620
- `const opened = visited.has(each.deskId) || onCurrent` — const, line 2621
- `const full = (!overview && onCurrent && focusMode && id === focusId) || (leaveTarget?.focusWindowId === id && leaveTarget.deskId === each.deskId)` — const, line 2622
- `const hiddenInFocus = !overview && onCurrent && focusMode && !full` — const, line 2623
- `const reading = full ?` — const, line 2624
- `const card = place.card` — const, line 2625
- `const box = overview ? card : reading` — const, line 2626
- `const leavingTo = leaveTarget?.deskId === each.deskId` — const, line 2627
- `const slotCut = leavingTo ? slotVisibility(leaveTarget.cams[each.deskId] ?? 0, each.slots.length, stage)[index] : onCurrent ? visibility[index] : null` — const, line 2628
- `const mask = full || focusMode || !slotCut ? null : leavingTo || (!overview && !zooming && onCurrent) ? softCropMask(slotCut, reading.w) : null` — const, line 2631
- `const lifecycle = lifecycles[id] ??` — const, line 2632
- `const paused = isPaused(lifecycle.state)` — const, line 2633
- `const paired = slot.length > 1` — const, line 2634
- `const selected = overview && selection !== null && slot.includes(selection.windowId)` — const, line 2635
- `const receding = overview && recedes(slot, selection?.windowId ?? null, selectedRelations, showRelations)` — const, line 2636
- `const measure = FOCUS_MEASURE[window.kind] ?? FOCUS_MEASURE.source` — const, line 2637
- `const title = titleOf(window)` — const, line 2691
- `const ringId = linkedFrom` — const, line 2773
- `const isSel = ringId !== null && slot.includes(ringId)` — const, line 2774
- `const isRel = !isSel && showRelations && slot.some((id)` — const, line 2775
- `const rect = ovLayout?.cards[rowIndex]?.[index]` — const, line 2776
- `const key = slotKey(each.deskId, slot)` — const, line 2778
- `const content = ws.windows[id]?.content` — const, line 2820
- `const stackWindow = Object.values(wsRef.current.windows).find((window)` — const, line 2826
- `function Sliver(` — function, line 2972
- `function WhichKey()` — function, line 2982
- `const groups: Array<` — const, line 2983
- `const rows = DESK_BINDINGS.filter((binding)` — const, line 2994
- `function OpenBeside(` — function, line 3012
- `const words = filter.trim().toLowerCase()` — const, line 3028
- `const sources = (library ?? []).filter((card)` — const, line 3029
- `const book = focus?.content && (focus.content.kind === "source" || focus.content.kind === "video") ? focus.content : null` — const, line 3030

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
- [[Reference/Desktop/TypeScript/screens/desks/Shelf|src/screens/desks/Shelf.tsx]] — import-or-re-export; imports `CarriedList`, `Shelf`, `ShelfRow`
- [[Reference/Desktop/TypeScript/screens/desks/companion/Companion|src/screens/desks/companion/Companion.tsx]] — import-or-re-export; imports `Companion`, `CompanionHandle`
- [[Reference/Desktop/TypeScript/screens/desks/companion/DiffProposal|src/screens/desks/companion/DiffProposal.tsx]] — import-or-re-export; imports `ProposedDiff`
- [[Reference/Desktop/TypeScript/screens/desks/companion/asks|src/screens/desks/companion/asks.ts]] — import-or-re-export; imports `CompanionApi`, `CompanionAsks`, `CompanionExchange`, `companionAsksFor`, `forgetCompanionAsks`
- [[Reference/Desktop/TypeScript/screens/desks/companion/model|src/screens/desks/companion/model.ts]] — import-or-re-export; imports `CompanionEvent`, `CompanionState`, `HIDDEN`, `avoidOffset`, `companionStep`
- [[Reference/Desktop/TypeScript/screens/desks/geometry|src/screens/desks/geometry.ts]] — import-or-re-export; imports `DESK_SIZES`, `FOCUS_MEASURE`, `Rect`, `Stage`, `ensureVisible`, `paneRects`, `rowTop`, `sliverSlots`, `slotRects`, `slotVisibility`, `slotWidth`, `softCropMask`, `stepZoom`
- [[Reference/Desktop/TypeScript/screens/desks/keys/listeners|src/screens/desks/keys/listeners.ts]] — import-or-re-export; imports `DeskListenerRouter`, `WINDOW_ATTRIBUTE`, `windowOfTarget`
- [[Reference/Desktop/TypeScript/screens/desks/keys/router|src/screens/desks/keys/router.ts]] — import-or-re-export; imports `BareAltTracker`, `DESK_BINDINGS`, `DeskAction`, `ModifierTracker`, `REAL_TIMERS`, `Timers`, `isTypingTarget`, `resolveKey`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `ClaimedScope`, `ListenerHub`, `ScopeClaims`, `WindowLifecycle`, `WindowScope`, `isPaused`, `windowState`
- [[Reference/Desktop/TypeScript/screens/desks/model/workspace|src/screens/desks/model/workspace.ts]] — import-or-re-export; imports `DeskWindow`, `Step`, `Workspace`, `addToStack`, `closeWindow`, `createDesk`, `deskById`, `ensureRunningPad`, `focusAlong`, `focusPane`, `focusedSlot`, `focusedWindowId`, `hasRunningPad`, `moveFocused`, `moveToDesk`, `moveToDeskAt`, `moveWindowTo`, `openBeside`, `openStackBeside`, `pairFocused`, `renameDesk`, `reorderSlots`, `setCompanionDock`, `setCompanionShown`, `setFocus`, `setView`, `slotIndexOf`, `swapInView`, `undoClose`, `unpairFocused`
- [[Reference/Desktop/TypeScript/screens/desks/outbox|src/screens/desks/outbox.ts]] — import-or-re-export; imports `OutboxTransport`, `clientIdFor`
- [[Reference/Desktop/TypeScript/screens/desks/overview/Card|src/screens/desks/overview/Card.tsx]] — import-or-re-export; imports `CardFace`, `LinkLayer`
- [[Reference/Desktop/TypeScript/screens/desks/overview/controller|src/screens/desks/overview/controller.ts]] — import-or-re-export; imports `ANIMATION_FRAMES`, `FrameClock`, `SlotElements`, `ZoomController`, `ZoomPlan`, `cameraTransform`
- [[Reference/Desktop/TypeScript/screens/desks/overview/engine|src/screens/desks/overview/engine.ts]] — import-or-re-export; imports `Camera`, `IDENTITY`, `OVERVIEW`, `ZoomGesture`, `ZoomSource`, `classifyWheel`, `dragProgress`, `dropTarget`, `enteringCamera`, `followSelection`, `moveSelection`, `newZoomGesture`, `normalizedDelta`, `overviewLayout`, `zoomWheel`
- [[Reference/Desktop/TypeScript/screens/desks/overview/links|src/screens/desks/overview/links.ts]] — import-or-re-export; imports `DRAWN_RELATIONS`, `Relation`, `curvedLinks`, `gatherOrder`, `relationsOf`
- [[Reference/Desktop/TypeScript/screens/desks/overview/miniature|src/screens/desks/overview/miniature.ts]] — import-or-re-export; imports `MiniatureBook`, `cloneForMiniature`
- [[Reference/Desktop/TypeScript/screens/desks/pads/DrainPanel|src/screens/desks/pads/DrainPanel.tsx]] — import-or-re-export; imports `DrainPanel`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] — import-or-re-export; imports `PadStackWindow`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PassageMarks|src/screens/desks/pads/PassageMarks.tsx]] — import-or-re-export; imports `PadLink`, `PassageMarks`, `visibleSpanRange`
- [[Reference/Desktop/TypeScript/screens/desks/pads/host|src/screens/desks/pads/host.ts]] — import-or-re-export; imports `PadStackHandle`, `PadsApi`, `PadsHost`, `PadsHostContext`, `PendingFigures`, `SourcePiece`, `localDay`
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

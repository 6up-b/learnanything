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
| Source lines | 1113 |
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

- `export interface DeskTransport extends OutboxTransport` — interface, line 78
- `export const LIVE_DESK_TRANSPORT: DeskTransport =` — const, line 85
- `export interface PaneRenderInput` — interface, line 95
- `export const KIND_GLYPH: Record<string, string> =` — const, line 110
- `export interface DeskShellProps` — interface, line 163
- `export function DeskShell(` — function, line 180
- `export function isVideoCard(card: SourceLibraryCard): boolean` — function, line 993
- `export function contentForCard(card: SourceLibraryCard, extractionId: string): ContentRefDto` — function, line 997

## Internal implementation anchors

- `type DeskWindow, type Step, type Workspace, } from "./model/workspace"` — type, line 33
- `type Step, type Workspace, } from "./model/workspace"` — type, line 34
- `type Workspace, } from "./model/workspace"` — type, line 35
- `type Stage, } from "./geometry"` — type, line 48
- `type DeskAction, type Timers, } from "./keys/router"` — type, line 57
- `type Timers, } from "./keys/router"` — type, line 58
- `const UNDO_CLOSE_MS = 9_000` — const, line 102
- `const TOAST_MS = 2_200` — const, line 104
- `const FLUSH_IDLE_MS = 250` — const, line 106
- `const VIEW_SAVE_IDLE_MS = 2_000` — const, line 108
- `const KIND_WORD: Record<string, string> =` — const, line 122
- `function defaultMintId(prefix: string): string` — function, line 134
- `function shortName(title: string): string` — function, line 142
- `const words = title.split(/\s+/).filter(Boolean)` — const, line 143
- `function readStored(key: string): string | null` — function, line 147
- `function writeStored(key: string, value: string): void` — function, line 155
- `const wsRef = useRef<Workspace>(EMPTY_WORKSPACE)` — const, line 193
- `const deskKey = `learnloop.desks.current.$` — const, line 195
- `const stageRef = useRef<HTMLElement | null>(null)` — const, line 210
- `const viewport = initialViewport ??` — const, line 212
- `const shelf = viewport.width < DESK_SIZES.shelfFoldBelow ? DESK_SIZES.shelfRail : DESK_SIZES.shelf` — const, line 213
- `const jumps = useRef(new Map<string, (spanId: string)` — const, line 217
- `const media = useRef(new Map<string, ()` — const, line 218
- `const pendingJump = useRef(new Map<string, string>())` — const, line 219
- `const outbox = useMemo( ()` — const, line 221
- `const toastNow = useCallback((text: string)` — const, line 226
- `const handle = timers.set(()` — const, line 229
- `const setCurrentDeskId = useCallback((deskId: string | null)` — const, line 235
- `const flushTimer = useRef<unknown>(null)` — const, line 240
- `const reloadRef = useRef<()` — const, line 241
- `const scheduleFlush = useCallback(()` — const, line 242
- `const commit = useCallback((step: Step)` — const, line 253
- `const chain = useCallback((first: Step, next: (ws: Workspace)` — const, line 263
- `const second = next(first.ws)` — const, line 264
- `const firstRun = useCallback(async (base: Workspace, cards: SourceLibraryCard[] | null): Promise<Step>` — const, line 268
- `const card = firstSourceId ? cards?.find((entry)` — const, line 269
- `const deskId = mintId("desk")` — const, line 270
- `const created = createDesk(base, deskId, card ? `new desk · $` — const, line 271
- `const extractionId = await transport.resolveExtraction(card.sourceId).catch(()` — const, line 273
- `const load = useCallback(async ()` — const, line 278
- `const loaded = fromDeskState(state)` — const, line 283
- `const desk = ws ? deskById(ws, currentDeskId) ?? ws.desks[0] ?? null : null` — const, line 304
- `const deskId = desk?.deskId ?? null` — const, line 305
- `const focusId = ws && desk ? focusedWindowId(ws, desk) : null` — const, line 306
- `const focusSlotIndex = ws && desk ? focusedSlot(ws, desk) : -1` — const, line 307
- `const slotCount = desk?.slots.length ?? 0` — const, line 315
- `const keepPrevious = useRef(false)` — const, line 316
- `const next = ensureVisible(cams[deskId] ?? 0, focusSlotIndex, slotCount, stage, keepPrevious.current)` — const, line 320
- `const node = stageRef.current` — const, line 328
- `const measure = ()` — const, line 329
- `const shell = node?.closest(".desk-shell") as HTMLElement | null` — const, line 332
- `const observer = typeof ResizeObserver === "undefined" || !node ? null : new ResizeObserver(measure)` — const, line 336
- `const cam = deskId ? camX[deskId] ?? 0 : 0` — const, line 345
- `const visibility = useMemo(()` — const, line 346
- `const deskIndex = ws && desk ? ws.desks.indexOf(desk) : 0` — const, line 347
- `const lifecycles = useMemo(()` — const, line 351
- `const out: Record<string, WindowLifecycle> =` — const, line 352
- `const onCurrent = each.deskId === deskId` — const, line 355
- `const lifecyclesRef = useRef(lifecycles)` — const, line 367
- `const focusIdRef = useRef(focusId)` — const, line 369
- `const focusModeRef = useRef(focusMode)` — const, line 377
- `const switchDesk = useCallback((direction: -1 | 1): boolean` — const, line 380
- `const current = wsRef.current` — const, line 381
- `const index = current.desks.findIndex((each)` — const, line 382
- `const next = current.desks[index + direction]` — const, line 383
- `const deskIdRef = useRef(deskId)` — const, line 388
- `const titleOf = useCallback((window: DeskWindow | undefined): string` — const, line 391
- `const known = status[window.windowId]?.title` — const, line 393
- `const content = window.content` — const, line 395
- `const run = useCallback((action: DeskAction): boolean` — const, line 403
- `const current = wsRef.current` — const, line 404
- `const id = deskIdRef.current` — const, line 405
- `const focus = focusIdRef.current` — const, line 407
- `const step = focusPane(current, id, action.direction)` — const, line 413
- `const title = titleOf(current.windows[focus])` — const, line 429
- `const window = current.windows[focus]` — const, line 444
- `const zoom = typeof window?.view?.zoom === "number" ? (window.view.zoom as number) : 1` — const, line 445
- `const next = stepZoom(zoom, action.direction)` — const, line 446
- `const desk = deskById(current, id)` — const, line 452
- `const index = slotIndexOf(desk, focus)` — const, line 454
- `const shown = visibilityRef.current.filter((slot)` — const, line 455
- `const other = shown.find((slot)` — const, line 456
- `const toggle = focus ? media.current.get(focus) : undefined` — const, line 461
- `const visibilityRef = useRef(visibility)` — const, line 470
- `const runRef = useRef(run)` — const, line 472
- `const modifiers = useMemo(()` — const, line 477
- `const altTracker = useMemo( ()` — const, line 478
- `const router = useMemo(()` — const, line 482
- `const current = wsRef.current` — const, line 486
- `const id = deskIdRef.current` — const, line 487
- `const owner = current.windows[windowId]` — const, line 489
- `const resolution = resolveKey(event,` — const, line 517
- `const hubs = useRef(new Map<string, ListenerHub>())` — const, line 532
- `const hubFor = useCallback((windowId: string): ListenerHub` — const, line 533
- `let hub = hubs.current.get(windowId)` — let, line 534
- `const openContent = useCallback((content: ContentRefDto, options:` — const, line 544
- `const current = wsRef.current` — const, line 545
- `const id = deskIdRef.current` — const, line 546
- `const step = openBeside(current, id, content, ()` — const, line 548
- `const jump = jumps.current.get(step.windowId)` — const, line 555
- `const next = new Set(now)` — const, line 562
- `const openHit = useCallback((hit:` — const, line 570
- `const card = library?.find((entry)` — const, line 572
- `const kind = card && isVideoCard(card) ? "video" : "source"` — const, line 573
- `const viewTimers = useRef(new Map<string, unknown>())` — const, line 579
- `const statusFor = useMemo(()` — const, line 580
- `const onStatusFor = useCallback((windowId: string)` — const, line 581
- `let handler = statusFor.get(windowId)` — let, line 582
- `const previous = viewTimers.current.get(windowId)` — const, line 589
- `const current = wsRef.current` — const, line 593
- `const window = current.windows[windowId]` — const, line 594
- `const jumpReadyFor = useMemo(()` — const, line 605
- `const onJumpReadyFor = useCallback((windowId: string)` — const, line 606
- `let handler = jumpReadyFor.get(windowId)` — let, line 607
- `const pending = pendingJump.current.get(windowId)` — const, line 615
- `const mediaReadyFor = useMemo(()` — const, line 626
- `const onMediaReadyFor = useCallback((windowId: string)` — const, line 627
- `let handler = mediaReadyFor.get(windowId)` — let, line 628
- `const railNodeFor = useMemo(()` — const, line 639
- `const onRailNode = useCallback((windowId: string)` — const, line 640
- `let handler = railNodeFor.get(windowId)` — let, line 641
- `const railPanelOf = useCallback((deskOf: string, extractionId: string): string | null` — const, line 650
- `const desk = deskById(ws, deskOf)` — const, line 652
- `const panels = desk.slots.flat().filter((id)` — const, line 654
- `const content = ws.windows[id]?.content` — const, line 655
- `const claimed = railClaims[`$` — const, line 658
- `const sourceWindowOf = useCallback((deskOf: string, extractionId: string): string | null` — const, line 662
- `const desk = deskById(ws, deskOf)` — const, line 664
- `const content = ws.windows[id]?.content` — const, line 667
- `const undoShown = undo && undo.deskId === deskId && undo.until > timers.now() ? undo : null` — const, line 674
- `const handle = timers.set(()` — const, line 677
- `const paneBody = (window: DeskWindow, lifecycle: WindowLifecycle): ReactNode` — const, line 691
- `const content = window.content` — const, line 692
- `const card = content && (content.kind === "source" || content.kind === "video") ? library?.find((entry)` — const, line 693
- `const railPanel = railPanelOf(window.deskId, content.extractionId)` — const, line 699
- `const railNode = railPanel ? railHosts[railPanel] ?? null : null` — const, line 700
- `const railContent = railPanel ? ws.windows[railPanel]?.content : null` — const, line 701
- `const railTab = railContent?.kind === "panel" && railContent.panel === "notes" ? "notes" : "guide"` — const, line 702
- `const extractionId = content.extractionId ?? ""` — const, line 720
- `const owner = railPanelOf(window.deskId, extractionId)` — const, line 721
- `const target = content.extractionId ? sourceWindowOf(window.deskId, content.extractionId) : null` — const, line 738
- `const jump = jumps.current.get(target)` — const, line 741
- `const focusWindow = focusId ? ws.windows[focusId] : undefined` — const, line 756
- `const focusZoom = typeof focusWindow?.view?.zoom === "number" ? (focusWindow.view.zoom as number) : 1` — const, line 757
- `const slivers = desk && !focusMode ? sliverSlots(cam, slotCount, stage) :` — const, line 758
- `const shelfRows: ShelfRow[] = desk ? desk.slots.flatMap((slot, index)` — const, line 759
- `const window = ws.windows[id]` — const, line 761
- `const kind = window?.kind ?? "source"` — const, line 762
- `const hints = focusMode ? [["alt+↵ / esc", "leave focus"], ["= − 0", "zoom"], ["alt+h/l", "next window"]] : [["alt+h/l", "window"], ["alt+j/k", "pane · desk"], ["alt+[ ]", "move"], ["alt+, .", "share · own slot"], ["alt+↵", "focus"], ["alt+w", "close"]]` — const, line 776
- `const title = (event.target as HTMLInputElement).value.trim()` — const, line 795
- `const id = mintId("desk")` — const, line 821
- `const onCurrent = each.deskId === deskId` — const, line 847
- `const eachCam = camX[each.deskId] ?? 0` — const, line 848
- `const rects = slotRects(each.slots.length, stage)` — const, line 849
- `const top = rowTop(rowIndex, stage) - rowTop(deskIndex, stage)` — const, line 850
- `const eachVisibility = onCurrent ? visibility : slotVisibility(eachCam, each.slots.length, stage)` — const, line 851
- `const rect = rects[index]` — const, line 853
- `const full = onCurrent && focusMode && slot.includes(focusId ?? "")` — const, line 854
- `const left = full ? 0 : rect.x - eachCam` — const, line 855
- `const style = full ?` — const, line 856
- `const mask = !full && onCurrent && !focusMode ? softCropMask(eachVisibility[index], rect.w) : null` — const, line 859
- `const slotPaused = slot.every((id)` — const, line 860
- `const panes = full ? slot.filter((id)` — const, line 861
- `const window = ws.windows[id]` — const, line 874
- `const lifecycle = lifecycles[id] ??` — const, line 876
- `const paired = panes.length > 1` — const, line 877
- `const measure = FOCUS_MEASURE[window.kind] ?? FOCUS_MEASURE.source` — const, line 878
- `const title = titleOf(window)` — const, line 901
- `function Sliver(` — function, line 1003
- `function WhichKey()` — function, line 1013
- `const groups: Array<` — const, line 1014
- `const rows = DESK_BINDINGS.filter((binding)` — const, line 1025
- `function OpenBeside(` — function, line 1043
- `const words = filter.trim().toLowerCase()` — const, line 1059
- `const sources = (library ?? []).filter((card)` — const, line 1060
- `const book = focus?.content && (focus.content.kind === "source" || focus.content.kind === "video") ? focus.content : null` — const, line 1061

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — dynamic import: dynamic import; no named call claim
- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `DeskShell`; references `DeskShell`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ContentRefDto`, `DeskApplyDto`, `DeskApplyInput`, `DeskStateDto`, `SourceLibraryCard`
- [[Reference/Desktop/TypeScript/api/poller|src/api/poller.ts]] — import-or-re-export; imports `poller`
- [[Reference/Desktop/TypeScript/app/ScreenErrorBoundary|src/app/ScreenErrorBoundary.tsx]] — import-or-re-export; imports `ScreenErrorBoundary`
- [[Reference/Desktop/TypeScript/screens/desks/Shelf|src/screens/desks/Shelf.tsx]] — import-or-re-export; imports `Shelf`, `ShelfRow`
- [[Reference/Desktop/TypeScript/screens/desks/geometry|src/screens/desks/geometry.ts]] — import-or-re-export; imports `DESK_SIZES`, `FOCUS_MEASURE`, `Stage`, `ensureVisible`, `paneRects`, `rowTop`, `sliverSlots`, `slotRects`, `slotVisibility`, `softCropMask`, `stepZoom`
- [[Reference/Desktop/TypeScript/screens/desks/keys/listeners|src/screens/desks/keys/listeners.ts]] — import-or-re-export; imports `DeskListenerRouter`, `WINDOW_ATTRIBUTE`
- [[Reference/Desktop/TypeScript/screens/desks/keys/router|src/screens/desks/keys/router.ts]] — import-or-re-export; imports `BareAltTracker`, `DESK_BINDINGS`, `DeskAction`, `ModifierTracker`, `REAL_TIMERS`, `Timers`, `isTypingTarget`, `resolveKey`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `ListenerHub`, `WindowLifecycle`, `WindowScope`, `isPaused`, `windowState`
- [[Reference/Desktop/TypeScript/screens/desks/model/workspace|src/screens/desks/model/workspace.ts]] — import-or-re-export; imports `DeskWindow`, `EMPTY_WORKSPACE`, `Step`, `Workspace`, `closeWindow`, `createDesk`, `deskById`, `focusAlong`, `focusPane`, `focusedSlot`, `focusedWindowId`, `fromDeskState`, `moveFocused`, `moveWindowTo`, `openBeside`, `pairFocused`, `renameDesk`, `setFocus`, `setView`, `slotIndexOf`, `swapInView`, `undoClose`, `unpairFocused`
- [[Reference/Desktop/TypeScript/screens/desks/outbox|src/screens/desks/outbox.ts]] — import-or-re-export; imports `DeskOutbox`, `OutboxTransport`, `clientIdFor`
- [[Reference/Desktop/TypeScript/screens/desks/windows/PanelWindow|src/screens/desks/windows/PanelWindow.tsx]] — import-or-re-export; imports `LibraryPanel`, `PANEL_TITLES`, `PathPanel`, `RailHostPanel`
- [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] — import-or-re-export; imports `ReaderPassThrough`, `SourceStatus`, `SourceWindow`
- [[Reference/Desktop/TypeScript/screens/reader/readerCache|src/screens/reader/readerCache.ts]] — import-or-re-export; imports `cachedSourceRead`

### Assets, platform, and third-party dependencies

- Local asset: [apps/learnloop-tauri/src/styles/desk.css](../../../../../../../apps/learnloop-tauri/src/styles/desk.css)
- Imported packages/crates: `@fontsource-variable/caveat`, `@fontsource-variable/inter`, `@fontsource-variable/jetbrains-mono`, `@fontsource-variable/literata`, `@fontsource-variable/literata/wght-italic.css`, `@fontsource-variable/source-serif-4`, `@fontsource-variable/source-serif-4/wght-italic.css`, `react`

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

---
title: "Desktop module · src/screens/desks/pads/PadStackWindow.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.pads.PadStackWindow"
language: "TypeScript"
area: "TypeScript/screens/desks/pads"
source_path: "apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.tsx"
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

# `src/screens/desks/pads/PadStackWindow.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `PadStackWindow` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.tsx) |
| Source lines | 1032 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]]

## Public API

- `export const CARD_MS =` — const, line 29
- `export const FLASH_MS = 1800` — const, line 31
- `export function stackPadIds(stack: PadStackEntryDto[], view: Record<string, unknown> | undefined): string[]` — function, line 56
- `export function tabMeta(state: PadState, today: string): string` — function, line 63
- `export function backLink(block: PadBlockDto, anchors: PadAnchorDto[] = []):` — function, line 73
- `export interface PadStackProps` — interface, line 95
- `export const PadStackWindow = forwardRef<PadStackHandle, PadStackProps>(function PadStackWindow(` — const, line 105
- `export function readSplit(view: Record<string, unknown>, padIds: string[]):` — function, line 996
- `export function moveDivider(ratios: number[], index: number, dy: number, total = 600): number[]` — function, line 1006

## Internal implementation anchors

- `const NO_OPENINGS: string[] = []` — const, line 24
- `const noSubscribe = ()` — const, line 25
- `const noVersion = ()` — const, line 26
- `const GRADE_KEY = "learnloop.desks.tabGrade"` — const, line 32
- `function readGrade(): TabGrade` — function, line 34
- `const stored = window.localStorage.getItem(GRADE_KEY)` — const, line 36
- `function shortDate(iso: string | null | undefined): string` — function, line 43
- `const date = new Date(iso.length === 10 ? `$` — const, line 45
- `function clock(seconds: number): string` — function, line 49
- `const s = Math.max(0, Math.floor(seconds))` — const, line 50
- `const own = stack.filter((entry): entry is Extract<PadStackEntryDto,` — const, line 57
- `const added = Array.isArray(view?.addedPads) ? (view?.addedPads as unknown[]).filter((id): id is string` — const, line 58
- `const pad = state.pad` — const, line 64
- `const updated = pad.updatedAt.slice(0, 10)` — const, line 65
- `const p = block.payload as Record<string, unknown>` — const, line 74
- `const link = anchors.find((anchor)` — const, line 76
- `const sourceId = typeof p.source_id === "string" ? p.source_id : link?.sourceId ?? null` — const, line 77
- `const title = typeof p.source_title === "string" ? p.source_title : "the source"` — const, line 78
- `const extractionId = typeof p.extraction_id === "string" ? p.extraction_id : null` — const, line 79
- `const spanId = typeof p.span_id === "string" ? p.span_id : null` — const, line 80
- `const t = typeof p.t === "number" ? p.t : typeof link?.t === "number" ? link.t : undefined` — const, line 81
- `interface Card` — interface, line 86
- `const host = usePadsHost()` — const, line 106
- `const PadStackBody = forwardRef<PadStackHandle, PadStackProps &` — const, line 111
- `const paused = useWindowPaused()` — const, line 114
- `const pausedRef = useRef(paused)` — const, line 115
- `const lessons = host.lessons ?? null` — const, line 119
- `const lessonsVersion = useSyncExternalStore(lessons?.desk.subscribe ?? noSubscribe, lessons?.desk.getVersion ?? noVersion)` — const, line 120
- `const openings = lessons ? lessons.desk.openingsFor(windowId) : NO_OPENINGS` — const, line 121
- `const openingsKey = openings.join("|")` — const, line 122
- `const padIds = useMemo(()` — const, line 124
- `const lessonId = lessonOfKey(padId)` — const, line 132
- `const additions = lessonId ? lessons?.desk.additionsFor(lessonId) : null` — const, line 133
- `const pads = padIds.map((padId)` — const, line 138
- `const today = host.today()` — const, line 139
- `const pen = usePenHost()` — const, line 141
- `const inkPads = pads.filter((state)` — const, line 143
- `const padKey = padIds.join("|")` — const, line 149
- `const scrollerRef = useRef<HTMLDivElement | null>(null)` — const, line 153
- `const rootRef = useRef<HTMLDivElement | null>(null)` — const, line 154
- `const tabEls = useRef(new Map<string, HTMLElement>())` — const, line 155
- `const paperEls = useRef(new Map<string, HTMLElement>())` — const, line 156
- `const blockEls = useRef(new Map<string, HTMLElement>())` — const, line 157
- `const editorRef = useRef<HTMLDivElement | null>(null)` — const, line 163
- `const frame = editorRef.current` — const, line 165
- `const cardTimer = useRef<ReturnType<typeof setTimeout> | null>(null)` — const, line 169
- `const menuOpening = useRef(0)` — const, line 171
- `const info = infoProp ?? infoOwn` — const, line 175
- `const setInfo = (next: boolean | ((now: boolean)` — const, line 176
- `const value = typeof next === "function" ? next(info) : next` — const, line 177
- `const hovered = useRef<` — const, line 183
- `const split = readSplit(view, padIds)` — const, line 184
- `const muted = Array.isArray(view.mutedPads) ? (view.mutedPads as string[]) : []` — const, line 186
- `const geometry = useCallback((): PadGeometry[]` — const, line 193
- `const scroller = scrollerRef.current` — const, line 194
- `const base = scroller.getBoundingClientRect().top - scroller.scrollTop` — const, line 196
- `const tab = tabEls.current.get(padId)` — const, line 198
- `const paper = paperEls.current.get(padId)` — const, line 199
- `const paperTop = paper ? paper.getBoundingClientRect().top - base : 0` — const, line 201
- `const height = paper?.offsetHeight ?? 0` — const, line 202
- `const layoutTabs = useCallback(()` — const, line 207
- `const scroller = scrollerRef.current` — const, line 208
- `const geo = geometry()` — const, line 210
- `const top = scroller.scrollTop` — const, line 211
- `const h = scroller.clientHeight` — const, line 212
- `const now = activePad(geo, top, h, scroller.scrollHeight)` — const, line 213
- `const open = fractionalOpen(geo, top, h, scroller.scrollHeight)` — const, line 214
- `const tab = tabEls.current.get(padId)` — const, line 216
- `const paper = paperEls.current.get(padId)` — const, line 217
- `const m = mergeAmount(i, geo, top, h)` — const, line 218
- `const margin = tabMargin(grade, i, open)` — const, line 219
- `const scroller = scrollerRef.current` — const, line 239
- `let frame = 0` — let, line 241
- `const onScroll = ()` — const, line 242
- `const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(()` — const, line 250
- `const scrollToPad = useCallback((index: number)` — const, line 259
- `const scroller = scrollerRef.current` — const, line 260
- `const target = scrollTargetFor(index, geometry())` — const, line 262
- `const ownLessons = stack.filter((entry)` — const, line 269
- `const key = lessons.desk.takeReveal(windowId, padIds)` — const, line 277
- `const proposalsFor = useCallback((padId: string)` — const, line 282
- `const loadedKey = pads.map((pad)` — const, line 289
- `const write = useCallback((padId: string, ops: Parameters<typeof store.commitPad>[1]): boolean` — const, line 298
- `const refused = store.commitPad(padId, ops)` — const, line 302
- `const insertAfter = useCallback((padId: string, after: string | null, block:` — const, line 310
- `const state = store.pads[padId]` — const, line 311
- `const blockId = host.mintId("blk")` — const, line 313
- `const p = block.payload ??` — const, line 315
- `const link = block.kind === "source_piece" && typeof p.extraction_id === "string" && typeof p.span_id === "string" ? [` — const, line 316
- `const ok = write(padId, [` — const, line 319
- `const commitEdit = useCallback((next?:` — const, line 327
- `const current = next ?? editing` — const, line 328
- `const block = store.pads[current.padId]?.blocks.find((each)` — const, line 330
- `const openEditor = (padId: string, block: PadBlockDto)` — const, line 338
- `const editableNeighbour = (padId: string, blockId: string, direction: -1 | 1): PadBlockDto | null` — const, line 348
- `const blocks = store.pads[padId]?.blocks ?? []` — const, line 349
- `const index = blocks.findIndex((each)` — const, line 350
- `const onEditorKey = (event: React.KeyboardEvent<HTMLTextAreaElement>, info:` — const, line 357
- `const textarea = event.currentTarget` — const, line 359
- `const block = store.pads[editing.padId]?.blocks.find((each)` — const, line 370
- `const block = store.pads[editing.padId]?.blocks.find((each)` — const, line 375
- `const previous = editableNeighbour(editing.padId, editing.blockId, -1)` — const, line 376
- `const neighbour = editableNeighbour(editing.padId, editing.blockId, event.key === "ArrowUp" ? -1 : 1)` — const, line 381
- `const scheduleCard = (next: Card | null)` — const, line 390
- `const cardFor = (padId: string, blockId: string, kind: Card["kind"], mark: HTMLElement)` — const, line 395
- `const scroller = rootRef.current` — const, line 396
- `const box = mark.getBoundingClientRect()` — const, line 398
- `const frame = scroller.getBoundingClientRect()` — const, line 399
- `const below = box.bottom - frame.top + 6` — const, line 400
- `const above = below + 180 > frame.height` — const, line 401
- `const shownProposal = useRef<` — const, line 409
- `const open = card ? (proposals[card.padId] ?? []).find((each)` — const, line 411
- `const was = shownProposal.current` — const, line 412
- `const labelProposal = (proposal: PadProposalDto, label: "opened" | "not_this" | "dismiss" | "ignored")` — const, line 421
- `const lastPad = padIds.length - 1` — const, line 429
- `const impl = useRef<PadStackHandle | null>(null)` — const, line 430
- `const next = paneFocus + direction` — const, line 441
- `const next = active + direction` — const, line 446
- `const padId = host.mintId("pad")` — const, line 452
- `const byHand = Boolean(pen?.on)` — const, line 454
- `const name = byHand ? "Scratchpad · ✎ by hand" : `Scratchpad · $` — const, line 455
- `const padId = padIds[split ? split.pads[paneFocus] ? padIds.indexOf(split.pads[paneFocus]) : active : active]` — const, line 461
- `const state = padId ? store.pads[padId] : null` — const, line 462
- `const at = hovered.current` — const, line 470
- `const index = padIds.indexOf(padId)` — const, line 477
- `const padId = request.lessonId ? lessons?.desk.additionsFor(request.lessonId) ?? `lesson:$` — const, line 483
- `const block = blockId ? store.pads[padId]?.blocks.find((each)` — const, line 489
- `const proxy = useMemo<PadStackHandle>(()` — const, line 495
- `const figureVersion = useSyncExternalStore(host.figures.subscribe, host.figures.getVersion)` — const, line 513
- `const element = blockEls.current.get(event.detail.blockId)` — const, line 526
- `const blockId = event.detail.blockId` — const, line 528
- `const renderBlock = (state: PadState, block: PadBlockDto): ReactNode` — const, line 535
- `const padId = state.pad.padId` — const, line 536
- `const isEditing = editing?.blockId === block.blockId` — const, line 537
- `const proposal = muted.includes(padId) ? null : (proposals[padId] ?? []).find((each)` — const, line 538
- `const editable = EDITABLE_KINDS.has(block.kind) && block.kind !== "sketch" && block.kind !== "cell"` — const, line 539
- `const submission = block.submissions.find((each)` — const, line 540
- `let gutter: ReactNode = null` — let, line 541
- `let body: ReactNode` — let, line 542
- `const markEnter = (kind: Card["kind"])` — const, line 543
- `const markLeave = ()` — const, line 544
- `const markTap = (kind: Card["kind"])` — const, line 545
- `const markEl = event.currentTarget` — const, line 548
- `const next = cardFor(padId, block.blockId, kind, markEl)` — const, line 549
- `const mark = (kind: Card["kind"], glyph: string, className: string)` — const, line 553
- `const link = backLink(block, state.anchors)` — const, line 559
- `const to = String((block.payload as Record<string, unknown>).lifted_to_pad_id ?? "")` — const, line 610
- `const title = store.pads[to]?.pad.title || "its own pad"` — const, line 611
- `const question = block.kind === "text" && block.provenance === "learner" && block.bodyMd.trim().endsWith("?")` — const, line 649
- `const newPadId = host.mintId("pad")` — const, line 684
- `const newBlockId = host.mintId("blk")` — const, line 685
- `const title = firstLine(block.bodyMd).slice(0, 48) || "lifted"` — const, line 686
- `const writeUnderLesson = (lessonId: string, block: Parameters<typeof insertAfter>[2] =` — const, line 700
- `let padId = lessons.desk.additionsFor(lessonId)` — let, line 702
- `const summary = lessons.desk.summary(lessonId)` — const, line 714
- `const topic = summary?.held ? null : summary?.title` — const, line 715
- `const state = store.pads[padId]` — const, line 719
- `const renderLesson = (key: string, index: number, minHeight: number): ReactNode` — const, line 723
- `const lessonId = lessonOfKey(key)` — const, line 724
- `const entry = lessons?.desk.entryFor(key) ?? null` — const, line 725
- `const additionsId = lessonId ? lessons?.desk.additionsFor(lessonId) ?? null : null` — const, line 726
- `const additions = additionsId ? store.pads[additionsId] ?? null : null` — const, line 727
- `const renderPaper = (state: PadState | null, padId: string, index: number, minHeight: number): ReactNode` — const, line 756
- `const failure = store.padFailure(padId)` — const, line 759
- `const days: Array<` — const, line 762
- `const day = state.pad.kind === "running" ? block.day ?? block.createdAt.slice(0, 10) : null` — const, line 764
- `const last = days[days.length - 1]` — const, line 765
- `const byHand = state.pad.kind === "ink"` — const, line 769
- `const look = inkView[padId] ??` — const, line 770
- `const newLine = ()` — const, line 771
- `const tabLabel = (state: PadState | null, padId: string, index: number): ReactNode` — const, line 808
- `const lessonId = lessonOfKey(padId)` — const, line 811
- `const summary = lessonId ? lessons?.desk.summary(lessonId) ?? null : null` — const, line 812
- `const title = state?.pad.title || (state?.pad.kind === "running" ? "running" : "a pad")` — const, line 833
- `const first = state ? plainLine(state.blocks.find((block)` — const, line 834
- `const minHeight = paperMinHeight(viewport, padIds.length)` — const, line 857
- `const learnerWords = pads.some((state)` — const, line 858
- `const cardBlock = card ? store.pads[card.padId]?.blocks.find((block)` — const, line 859
- `const cardProposal = card ? (proposals[card.padId] ?? []).find((each)` — const, line 860
- `const state = store.pads[padId] ?? null` — const, line 874
- `const link = backLink(cardBlock, store.pads[card.padId]?.anchors ?? [])` — const, line 902
- `const target = cardProposal.target as` — const, line 925
- `const extractionId = target.content?.extraction_id ?? target.content?.extractionId` — const, line 926
- `function padContext(padId: string, block: PadBlockDto, anchors: Array<` — function, line 982
- `const p = block.payload as Record<string, unknown>` — const, line 983
- `const own = anchors.find((anchor)` — const, line 984
- `const anchor = own ?` — const, line 985
- `function setRef(map: Map<string, HTMLElement>, key: string, node: HTMLElement | null)` — function, line 990
- `const raw = view.split as` — const, line 997
- `const pads = (raw.pads as unknown[]).filter((id): id is string` — const, line 999
- `const ratios = Array.isArray(raw.ratios) && raw.ratios.length === pads.length ? (raw.ratios as number[]).map((r)` — const, line 1001
- `const sum = ratios.reduce((a, b)` — const, line 1007
- `const px = ratios.map((r)` — const, line 1008
- `const min = 60` — const, line 1009
- `const move = Math.max(min - px[index], Math.min(px[index + 1] - min, dy))` — const, line 1010
- `function Divider(` — function, line 1016
- `const start = useRef<number | null>(null)` — const, line 1017

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `PadStackWindow`; references `PadStackWindow`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `PadStackWindow`; references `PadStackWindow`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `PadAnchorDto`, `PadBlockDto`, `PadProposalDto`, `PadStackEntryDto`
- [[Reference/Desktop/TypeScript/render/LiveMarkdownEditor|src/render/LiveMarkdownEditor.tsx]] — import-or-re-export; imports `LiveMarkdownEditor`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/desks/fitMath|src/screens/desks/fitMath.tsx]] — import-or-re-export; imports `FitMath`
- [[Reference/Desktop/TypeScript/screens/desks/lesson/LessonPaper|src/screens/desks/lesson/LessonPaper.tsx]] — import-or-re-export; imports `LessonPaper`
- [[Reference/Desktop/TypeScript/screens/desks/lesson/model|src/screens/desks/lesson/model.ts]] — import-or-re-export; imports `isLessonItem`, `lessonOfKey`, `lessonTabMeta`, `lessonTabTitle`, `stackItemKeys`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useHubListener`, `useScopeClaim`, `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/desks/notebook/PadCell|src/screens/desks/notebook/PadCell.tsx]] — import-or-re-export; imports `PadCell`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PadOverlays|src/screens/desks/pads/PadOverlays.tsx]] — import-or-re-export; imports `ArrangeOverlay`, `MenuRequest`, `PadMenu`, `SubmitSheet`
- [[Reference/Desktop/TypeScript/screens/desks/pads/SketchCanvas|src/screens/desks/pads/SketchCanvas.tsx]] — import-or-re-export; imports `SketchCanvas`
- [[Reference/Desktop/TypeScript/screens/desks/pads/host|src/screens/desks/pads/host.ts]] — import-or-re-export; imports `PadStackHandle`, `PadsHost`, `dayHeading`, `usePadsHost`
- [[Reference/Desktop/TypeScript/screens/desks/pads/model|src/screens/desks/pads/model.ts]] — import-or-re-export; imports `EDITABLE_KINDS`, `PadState`, `firstLine`, `isLearnersWords`, `keyAfter`, `plainLine`
- [[Reference/Desktop/TypeScript/screens/desks/pads/stickyTabs|src/screens/desks/pads/stickyTabs.ts]] — import-or-re-export; imports `PadGeometry`, `TabGrade`, `activePad`, `fractionalOpen`, `mergeAmount`, `paperMinHeight`, `scrollTargetFor`, `tabMargin`
- [[Reference/Desktop/TypeScript/screens/desks/pen/InkLine|src/screens/desks/pen/InkLine.tsx]] — import-or-re-export; imports `InkBlock`, `InkJot`
- [[Reference/Desktop/TypeScript/screens/desks/pen/host|src/screens/desks/pen/host.ts]] — import-or-re-export; imports `usePenHost`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/pen/inkPad.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/inkPad.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/lesson/lessonWindows.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/lesson/lessonWindows.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/DeskShell.menu.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/DeskShell.menu.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

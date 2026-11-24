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
| Source lines | 1027 |
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
- `export function readSplit(view: Record<string, unknown>, padIds: string[]):` — function, line 991
- `export function moveDivider(ratios: number[], index: number, dy: number, total = 600): number[]` — function, line 1001

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
- `const info = infoProp ?? infoOwn` — const, line 174
- `const setInfo = (next: boolean | ((now: boolean)` — const, line 175
- `const value = typeof next === "function" ? next(info) : next` — const, line 176
- `const hovered = useRef<` — const, line 182
- `const split = readSplit(view, padIds)` — const, line 183
- `const muted = Array.isArray(view.mutedPads) ? (view.mutedPads as string[]) : []` — const, line 185
- `const geometry = useCallback((): PadGeometry[]` — const, line 192
- `const scroller = scrollerRef.current` — const, line 193
- `const base = scroller.getBoundingClientRect().top - scroller.scrollTop` — const, line 195
- `const tab = tabEls.current.get(padId)` — const, line 197
- `const paper = paperEls.current.get(padId)` — const, line 198
- `const paperTop = paper ? paper.getBoundingClientRect().top - base : 0` — const, line 200
- `const height = paper?.offsetHeight ?? 0` — const, line 201
- `const layoutTabs = useCallback(()` — const, line 206
- `const scroller = scrollerRef.current` — const, line 207
- `const geo = geometry()` — const, line 209
- `const top = scroller.scrollTop` — const, line 210
- `const h = scroller.clientHeight` — const, line 211
- `const now = activePad(geo, top, h, scroller.scrollHeight)` — const, line 212
- `const open = fractionalOpen(geo, top, h, scroller.scrollHeight)` — const, line 213
- `const tab = tabEls.current.get(padId)` — const, line 215
- `const paper = paperEls.current.get(padId)` — const, line 216
- `const m = mergeAmount(i, geo, top, h)` — const, line 217
- `const margin = tabMargin(grade, i, open)` — const, line 218
- `const scroller = scrollerRef.current` — const, line 238
- `let frame = 0` — let, line 240
- `const onScroll = ()` — const, line 241
- `const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(()` — const, line 249
- `const scrollToPad = useCallback((index: number)` — const, line 258
- `const scroller = scrollerRef.current` — const, line 259
- `const target = scrollTargetFor(index, geometry())` — const, line 261
- `const ownLessons = stack.filter((entry)` — const, line 268
- `const key = lessons.desk.takeReveal(windowId, padIds)` — const, line 276
- `const proposalsFor = useCallback((padId: string)` — const, line 281
- `const loadedKey = pads.map((pad)` — const, line 288
- `const write = useCallback((padId: string, ops: Parameters<typeof store.commitPad>[1]): boolean` — const, line 297
- `const refused = store.commitPad(padId, ops)` — const, line 301
- `const insertAfter = useCallback((padId: string, after: string | null, block:` — const, line 309
- `const state = store.pads[padId]` — const, line 310
- `const blockId = host.mintId("blk")` — const, line 312
- `const p = block.payload ??` — const, line 314
- `const link = block.kind === "source_piece" && typeof p.extraction_id === "string" && typeof p.span_id === "string" ? [` — const, line 315
- `const ok = write(padId, [` — const, line 318
- `const commitEdit = useCallback((next?:` — const, line 326
- `const current = next ?? editing` — const, line 327
- `const block = store.pads[current.padId]?.blocks.find((each)` — const, line 329
- `const openEditor = (padId: string, block: PadBlockDto)` — const, line 337
- `const editableNeighbour = (padId: string, blockId: string, direction: -1 | 1): PadBlockDto | null` — const, line 347
- `const blocks = store.pads[padId]?.blocks ?? []` — const, line 348
- `const index = blocks.findIndex((each)` — const, line 349
- `const onEditorKey = (event: React.KeyboardEvent<HTMLTextAreaElement>, info:` — const, line 356
- `const textarea = event.currentTarget` — const, line 358
- `const block = store.pads[editing.padId]?.blocks.find((each)` — const, line 369
- `const block = store.pads[editing.padId]?.blocks.find((each)` — const, line 374
- `const previous = editableNeighbour(editing.padId, editing.blockId, -1)` — const, line 375
- `const neighbour = editableNeighbour(editing.padId, editing.blockId, event.key === "ArrowUp" ? -1 : 1)` — const, line 380
- `const scheduleCard = (next: Card | null)` — const, line 389
- `const cardFor = (padId: string, blockId: string, kind: Card["kind"], mark: HTMLElement)` — const, line 394
- `const scroller = rootRef.current` — const, line 395
- `const box = mark.getBoundingClientRect()` — const, line 397
- `const frame = scroller.getBoundingClientRect()` — const, line 398
- `const below = box.bottom - frame.top + 6` — const, line 399
- `const above = below + 180 > frame.height` — const, line 400
- `const shownProposal = useRef<` — const, line 408
- `const open = card ? (proposals[card.padId] ?? []).find((each)` — const, line 410
- `const was = shownProposal.current` — const, line 411
- `const labelProposal = (proposal: PadProposalDto, label: "opened" | "not_this" | "dismiss" | "ignored")` — const, line 420
- `const lastPad = padIds.length - 1` — const, line 428
- `const impl = useRef<PadStackHandle | null>(null)` — const, line 429
- `const next = paneFocus + direction` — const, line 440
- `const next = active + direction` — const, line 445
- `const padId = host.mintId("pad")` — const, line 451
- `const byHand = Boolean(pen?.on)` — const, line 453
- `const name = byHand ? "Scratchpad · ✎ by hand" : `Scratchpad · $` — const, line 454
- `const padId = padIds[split ? split.pads[paneFocus] ? padIds.indexOf(split.pads[paneFocus]) : active : active]` — const, line 460
- `const state = padId ? store.pads[padId] : null` — const, line 461
- `const at = hovered.current` — const, line 469
- `const index = padIds.indexOf(padId)` — const, line 475
- `const padId = request.lessonId ? lessons?.desk.additionsFor(request.lessonId) ?? `lesson:$` — const, line 481
- `const block = blockId ? store.pads[padId]?.blocks.find((each)` — const, line 486
- `const proxy = useMemo<PadStackHandle>(()` — const, line 491
- `const figureVersion = useSyncExternalStore(host.figures.subscribe, host.figures.getVersion)` — const, line 509
- `const element = blockEls.current.get(event.detail.blockId)` — const, line 522
- `const blockId = event.detail.blockId` — const, line 524
- `const renderBlock = (state: PadState, block: PadBlockDto): ReactNode` — const, line 531
- `const padId = state.pad.padId` — const, line 532
- `const isEditing = editing?.blockId === block.blockId` — const, line 533
- `const proposal = muted.includes(padId) ? null : (proposals[padId] ?? []).find((each)` — const, line 534
- `const editable = EDITABLE_KINDS.has(block.kind) && block.kind !== "sketch" && block.kind !== "cell"` — const, line 535
- `const submission = block.submissions.find((each)` — const, line 536
- `let gutter: ReactNode = null` — let, line 537
- `let body: ReactNode` — let, line 538
- `const markEnter = (kind: Card["kind"])` — const, line 539
- `const markLeave = ()` — const, line 540
- `const markTap = (kind: Card["kind"])` — const, line 541
- `const markEl = event.currentTarget` — const, line 544
- `const next = cardFor(padId, block.blockId, kind, markEl)` — const, line 545
- `const mark = (kind: Card["kind"], glyph: string, className: string)` — const, line 549
- `const link = backLink(block, state.anchors)` — const, line 555
- `const to = String((block.payload as Record<string, unknown>).lifted_to_pad_id ?? "")` — const, line 606
- `const title = store.pads[to]?.pad.title || "its own pad"` — const, line 607
- `const question = block.kind === "text" && block.provenance === "learner" && block.bodyMd.trim().endsWith("?")` — const, line 645
- `const newPadId = host.mintId("pad")` — const, line 680
- `const newBlockId = host.mintId("blk")` — const, line 681
- `const title = firstLine(block.bodyMd).slice(0, 48) || "lifted"` — const, line 682
- `const writeUnderLesson = (lessonId: string, block: Parameters<typeof insertAfter>[2] =` — const, line 696
- `let padId = lessons.desk.additionsFor(lessonId)` — let, line 698
- `const summary = lessons.desk.summary(lessonId)` — const, line 710
- `const topic = summary?.held ? null : summary?.title` — const, line 711
- `const state = store.pads[padId]` — const, line 715
- `const renderLesson = (key: string, index: number, minHeight: number): ReactNode` — const, line 719
- `const lessonId = lessonOfKey(key)` — const, line 720
- `const entry = lessons?.desk.entryFor(key) ?? null` — const, line 721
- `const additionsId = lessonId ? lessons?.desk.additionsFor(lessonId) ?? null : null` — const, line 722
- `const additions = additionsId ? store.pads[additionsId] ?? null : null` — const, line 723
- `const renderPaper = (state: PadState | null, padId: string, index: number, minHeight: number): ReactNode` — const, line 752
- `const failure = store.padFailure(padId)` — const, line 755
- `const days: Array<` — const, line 758
- `const day = state.pad.kind === "running" ? block.day ?? block.createdAt.slice(0, 10) : null` — const, line 760
- `const last = days[days.length - 1]` — const, line 761
- `const byHand = state.pad.kind === "ink"` — const, line 765
- `const look = inkView[padId] ??` — const, line 766
- `const newLine = ()` — const, line 767
- `const tabLabel = (state: PadState | null, padId: string, index: number): ReactNode` — const, line 804
- `const lessonId = lessonOfKey(padId)` — const, line 807
- `const summary = lessonId ? lessons?.desk.summary(lessonId) ?? null : null` — const, line 808
- `const title = state?.pad.title || (state?.pad.kind === "running" ? "running" : "a pad")` — const, line 829
- `const first = state ? plainLine(state.blocks.find((block)` — const, line 830
- `const minHeight = paperMinHeight(viewport, padIds.length)` — const, line 853
- `const learnerWords = pads.some((state)` — const, line 854
- `const cardBlock = card ? store.pads[card.padId]?.blocks.find((block)` — const, line 855
- `const cardProposal = card ? (proposals[card.padId] ?? []).find((each)` — const, line 856
- `const state = store.pads[padId] ?? null` — const, line 870
- `const link = backLink(cardBlock, store.pads[card.padId]?.anchors ?? [])` — const, line 898
- `const target = cardProposal.target as` — const, line 921
- `const extractionId = target.content?.extraction_id ?? target.content?.extractionId` — const, line 922
- `function padContext(padId: string, block: PadBlockDto, anchors: Array<` — function, line 977
- `const p = block.payload as Record<string, unknown>` — const, line 978
- `const own = anchors.find((anchor)` — const, line 979
- `const anchor = own ?` — const, line 980
- `function setRef(map: Map<string, HTMLElement>, key: string, node: HTMLElement | null)` — function, line 985
- `const raw = view.split as` — const, line 992
- `const pads = (raw.pads as unknown[]).filter((id): id is string` — const, line 994
- `const ratios = Array.isArray(raw.ratios) && raw.ratios.length === pads.length ? (raw.ratios as number[]).map((r)` — const, line 996
- `const sum = ratios.reduce((a, b)` — const, line 1002
- `const px = ratios.map((r)` — const, line 1003
- `const min = 60` — const, line 1004
- `const move = Math.max(min - px[index], Math.min(px[index + 1] - min, dy))` — const, line 1005
- `function Divider(` — function, line 1011
- `const start = useRef<number | null>(null)` — const, line 1012

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

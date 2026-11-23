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
| Source lines | 878 |
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

- `export const CARD_MS =` — const, line 22
- `export const FLASH_MS = 1800` — const, line 24
- `export function stackPadIds(stack: PadStackEntryDto[], view: Record<string, unknown> | undefined): string[]` — function, line 49
- `export function tabMeta(state: PadState, today: string): string` — function, line 56
- `export function backLink(block: PadBlockDto, anchors: PadAnchorDto[] = []):` — function, line 66
- `export interface PadStackProps` — interface, line 88
- `export const PadStackWindow = forwardRef<PadStackHandle, PadStackProps>(function PadStackWindow(` — const, line 98
- `export function readSplit(view: Record<string, unknown>, padIds: string[]):` — function, line 842
- `export function moveDivider(ratios: number[], index: number, dy: number, total = 600): number[]` — function, line 852

## Internal implementation anchors

- `const GRADE_KEY = "learnloop.desks.tabGrade"` — const, line 25
- `function readGrade(): TabGrade` — function, line 27
- `const stored = window.localStorage.getItem(GRADE_KEY)` — const, line 29
- `function shortDate(iso: string | null | undefined): string` — function, line 36
- `const date = new Date(iso.length === 10 ? `$` — const, line 38
- `function clock(seconds: number): string` — function, line 42
- `const s = Math.max(0, Math.floor(seconds))` — const, line 43
- `const own = stack.filter((entry): entry is Extract<PadStackEntryDto,` — const, line 50
- `const added = Array.isArray(view?.addedPads) ? (view?.addedPads as unknown[]).filter((id): id is string` — const, line 51
- `const pad = state.pad` — const, line 57
- `const updated = pad.updatedAt.slice(0, 10)` — const, line 58
- `const p = block.payload as Record<string, unknown>` — const, line 67
- `const link = anchors.find((anchor)` — const, line 69
- `const sourceId = typeof p.source_id === "string" ? p.source_id : link?.sourceId ?? null` — const, line 70
- `const title = typeof p.source_title === "string" ? p.source_title : "the source"` — const, line 71
- `const extractionId = typeof p.extraction_id === "string" ? p.extraction_id : null` — const, line 72
- `const spanId = typeof p.span_id === "string" ? p.span_id : null` — const, line 73
- `const t = typeof p.t === "number" ? p.t : typeof link?.t === "number" ? link.t : undefined` — const, line 74
- `interface Card` — interface, line 79
- `const host = usePadsHost()` — const, line 99
- `const PadStackBody = forwardRef<PadStackHandle, PadStackProps &` — const, line 104
- `const paused = useWindowPaused()` — const, line 107
- `const pausedRef = useRef(paused)` — const, line 108
- `const padIds = useMemo(()` — const, line 110
- `const pads = padIds.map((padId)` — const, line 115
- `const today = host.today()` — const, line 116
- `const pen = usePenHost()` — const, line 118
- `const inkPads = pads.filter((state)` — const, line 120
- `const padKey = padIds.join("|")` — const, line 125
- `const scrollerRef = useRef<HTMLDivElement | null>(null)` — const, line 129
- `const rootRef = useRef<HTMLDivElement | null>(null)` — const, line 130
- `const tabEls = useRef(new Map<string, HTMLElement>())` — const, line 131
- `const paperEls = useRef(new Map<string, HTMLElement>())` — const, line 132
- `const blockEls = useRef(new Map<string, HTMLElement>())` — const, line 133
- `const editorRef = useRef<HTMLDivElement | null>(null)` — const, line 139
- `const frame = editorRef.current` — const, line 141
- `const cardTimer = useRef<ReturnType<typeof setTimeout> | null>(null)` — const, line 145
- `const info = infoProp ?? infoOwn` — const, line 150
- `const setInfo = (next: boolean | ((now: boolean)` — const, line 151
- `const value = typeof next === "function" ? next(info) : next` — const, line 152
- `const hovered = useRef<` — const, line 158
- `const split = readSplit(view, padIds)` — const, line 159
- `const muted = Array.isArray(view.mutedPads) ? (view.mutedPads as string[]) : []` — const, line 161
- `const geometry = useCallback((): PadGeometry[]` — const, line 168
- `const scroller = scrollerRef.current` — const, line 169
- `const base = scroller.getBoundingClientRect().top - scroller.scrollTop` — const, line 171
- `const tab = tabEls.current.get(padId)` — const, line 173
- `const paper = paperEls.current.get(padId)` — const, line 174
- `const paperTop = paper ? paper.getBoundingClientRect().top - base : 0` — const, line 176
- `const height = paper?.offsetHeight ?? 0` — const, line 177
- `const layoutTabs = useCallback(()` — const, line 182
- `const scroller = scrollerRef.current` — const, line 183
- `const geo = geometry()` — const, line 185
- `const top = scroller.scrollTop` — const, line 186
- `const h = scroller.clientHeight` — const, line 187
- `const now = activePad(geo, top, h, scroller.scrollHeight)` — const, line 188
- `const open = fractionalOpen(geo, top, h, scroller.scrollHeight)` — const, line 189
- `const tab = tabEls.current.get(padId)` — const, line 191
- `const paper = paperEls.current.get(padId)` — const, line 192
- `const m = mergeAmount(i, geo, top, h)` — const, line 193
- `const margin = tabMargin(grade, i, open)` — const, line 194
- `const scroller = scrollerRef.current` — const, line 214
- `let frame = 0` — let, line 216
- `const onScroll = ()` — const, line 217
- `const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(()` — const, line 225
- `const scrollToPad = useCallback((index: number)` — const, line 234
- `const scroller = scrollerRef.current` — const, line 235
- `const target = scrollTargetFor(index, geometry())` — const, line 237
- `const proposalsFor = useCallback((padId: string)` — const, line 244
- `const loadedKey = pads.map((pad)` — const, line 251
- `const write = useCallback((padId: string, ops: Parameters<typeof store.commitPad>[1]): boolean` — const, line 260
- `const refused = store.commitPad(padId, ops)` — const, line 264
- `const insertAfter = useCallback((padId: string, after: string | null, block:` — const, line 272
- `const state = store.pads[padId]` — const, line 273
- `const blockId = host.mintId("blk")` — const, line 275
- `const p = block.payload ??` — const, line 277
- `const link = block.kind === "source_piece" && typeof p.extraction_id === "string" && typeof p.span_id === "string" ? [` — const, line 278
- `const ok = write(padId, [` — const, line 281
- `const commitEdit = useCallback((next?:` — const, line 289
- `const current = next ?? editing` — const, line 290
- `const block = store.pads[current.padId]?.blocks.find((each)` — const, line 292
- `const openEditor = (padId: string, block: PadBlockDto)` — const, line 300
- `const editableNeighbour = (padId: string, blockId: string, direction: -1 | 1): PadBlockDto | null` — const, line 310
- `const blocks = store.pads[padId]?.blocks ?? []` — const, line 311
- `const index = blocks.findIndex((each)` — const, line 312
- `const onEditorKey = (event: React.KeyboardEvent<HTMLTextAreaElement>, info:` — const, line 319
- `const textarea = event.currentTarget` — const, line 321
- `const block = store.pads[editing.padId]?.blocks.find((each)` — const, line 332
- `const block = store.pads[editing.padId]?.blocks.find((each)` — const, line 337
- `const previous = editableNeighbour(editing.padId, editing.blockId, -1)` — const, line 338
- `const neighbour = editableNeighbour(editing.padId, editing.blockId, event.key === "ArrowUp" ? -1 : 1)` — const, line 343
- `const scheduleCard = (next: Card | null)` — const, line 352
- `const cardFor = (padId: string, blockId: string, kind: Card["kind"], mark: HTMLElement)` — const, line 357
- `const scroller = rootRef.current` — const, line 358
- `const box = mark.getBoundingClientRect()` — const, line 360
- `const frame = scroller.getBoundingClientRect()` — const, line 361
- `const below = box.bottom - frame.top + 6` — const, line 362
- `const above = below + 180 > frame.height` — const, line 363
- `const shownProposal = useRef<` — const, line 371
- `const open = card ? (proposals[card.padId] ?? []).find((each)` — const, line 373
- `const was = shownProposal.current` — const, line 374
- `const labelProposal = (proposal: PadProposalDto, label: "opened" | "not_this" | "dismiss" | "ignored")` — const, line 383
- `const lastPad = padIds.length - 1` — const, line 391
- `const impl = useRef<PadStackHandle | null>(null)` — const, line 392
- `const next = paneFocus + direction` — const, line 403
- `const next = active + direction` — const, line 408
- `const padId = host.mintId("pad")` — const, line 414
- `const byHand = Boolean(pen?.on)` — const, line 416
- `const name = byHand ? "Scratchpad · ✎ by hand" : `Scratchpad · $` — const, line 417
- `const padId = padIds[split ? split.pads[paneFocus] ? padIds.indexOf(split.pads[paneFocus]) : active : active]` — const, line 423
- `const state = padId ? store.pads[padId] : null` — const, line 424
- `const at = hovered.current` — const, line 432
- `const index = padIds.indexOf(padId)` — const, line 438
- `const block = blockId ? store.pads[padId]?.blocks.find((each)` — const, line 443
- `const proxy = useMemo<PadStackHandle>(()` — const, line 448
- `const figureVersion = useSyncExternalStore(host.figures.subscribe, host.figures.getVersion)` — const, line 465
- `const element = blockEls.current.get(event.detail.blockId)` — const, line 478
- `const blockId = event.detail.blockId` — const, line 480
- `const renderBlock = (state: PadState, block: PadBlockDto): ReactNode` — const, line 487
- `const padId = state.pad.padId` — const, line 488
- `const isEditing = editing?.blockId === block.blockId` — const, line 489
- `const proposal = muted.includes(padId) ? null : (proposals[padId] ?? []).find((each)` — const, line 490
- `const editable = EDITABLE_KINDS.has(block.kind) && block.kind !== "sketch"` — const, line 491
- `const submission = block.submissions.find((each)` — const, line 492
- `let gutter: ReactNode = null` — let, line 493
- `let body: ReactNode` — let, line 494
- `const markEnter = (kind: Card["kind"])` — const, line 495
- `const markLeave = ()` — const, line 496
- `const markTap = (kind: Card["kind"])` — const, line 497
- `const markEl = event.currentTarget` — const, line 500
- `const next = cardFor(padId, block.blockId, kind, markEl)` — const, line 501
- `const mark = (kind: Card["kind"], glyph: string, className: string)` — const, line 505
- `const link = backLink(block, state.anchors)` — const, line 511
- `const to = String((block.payload as Record<string, unknown>).lifted_to_pad_id ?? "")` — const, line 549
- `const title = store.pads[to]?.pad.title || "its own pad"` — const, line 550
- `const question = block.kind === "text" && block.provenance === "learner" && block.bodyMd.trim().endsWith("?")` — const, line 588
- `const newPadId = host.mintId("pad")` — const, line 623
- `const title = firstLine(block.bodyMd).slice(0, 48) || "lifted"` — const, line 624
- `const renderPaper = (state: PadState | null, padId: string, index: number, minHeight: number): ReactNode` — const, line 634
- `const failure = store.padFailure(padId)` — const, line 636
- `const days: Array<` — const, line 639
- `const day = state.pad.kind === "running" ? block.day ?? block.createdAt.slice(0, 10) : null` — const, line 641
- `const last = days[days.length - 1]` — const, line 642
- `const byHand = state.pad.kind === "ink"` — const, line 646
- `const look = inkView[padId] ??` — const, line 647
- `const newLine = ()` — const, line 648
- `const tabLabel = (state: PadState | null, padId: string, index: number): ReactNode` — const, line 685
- `const title = state?.pad.title || (state?.pad.kind === "running" ? "running" : "a pad")` — const, line 686
- `const first = state ? plainLine(state.blocks.find((block)` — const, line 687
- `const minHeight = paperMinHeight(viewport, padIds.length)` — const, line 710
- `const learnerWords = pads.some((state)` — const, line 711
- `const cardBlock = card ? store.pads[card.padId]?.blocks.find((block)` — const, line 712
- `const cardProposal = card ? (proposals[card.padId] ?? []).find((each)` — const, line 713
- `const state = store.pads[padId] ?? null` — const, line 727
- `const link = backLink(cardBlock, store.pads[card.padId]?.anchors ?? [])` — const, line 754
- `const target = cardProposal.target as` — const, line 777
- `const extractionId = target.content?.extraction_id ?? target.content?.extractionId` — const, line 778
- `function padContext(padId: string, block: PadBlockDto, anchors: Array<` — function, line 828
- `const p = block.payload as Record<string, unknown>` — const, line 829
- `const own = anchors.find((anchor)` — const, line 830
- `const anchor = own ?` — const, line 831
- `function setRef(map: Map<string, HTMLElement>, key: string, node: HTMLElement | null)` — function, line 836
- `const raw = view.split as` — const, line 843
- `const pads = (raw.pads as unknown[]).filter((id): id is string` — const, line 845
- `const ratios = Array.isArray(raw.ratios) && raw.ratios.length === pads.length ? (raw.ratios as number[]).map((r)` — const, line 847
- `const sum = ratios.reduce((a, b)` — const, line 853
- `const px = ratios.map((r)` — const, line 854
- `const min = 60` — const, line 855
- `const move = Math.max(min - px[index], Math.min(px[index + 1] - min, dy))` — const, line 856
- `function Divider(` — function, line 862
- `const start = useRef<number | null>(null)` — const, line 863

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
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useHubListener`, `useScopeClaim`, `useWindowPaused`
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

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

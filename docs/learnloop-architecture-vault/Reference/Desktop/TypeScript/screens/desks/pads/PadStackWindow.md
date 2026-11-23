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
| Source lines | 823 |
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

- `export const CARD_MS =` — const, line 20
- `export const FLASH_MS = 1800` — const, line 22
- `export function stackPadIds(stack: PadStackEntryDto[], view: Record<string, unknown> | undefined): string[]` — function, line 47
- `export function tabMeta(state: PadState, today: string): string` — function, line 54
- `export function backLink(block: PadBlockDto, anchors: PadAnchorDto[] = []):` — function, line 63
- `export interface PadStackProps` — interface, line 85
- `export const PadStackWindow = forwardRef<PadStackHandle, PadStackProps>(function PadStackWindow(` — const, line 91
- `export function readSplit(view: Record<string, unknown>, padIds: string[]):` — function, line 787
- `export function moveDivider(ratios: number[], index: number, dy: number, total = 600): number[]` — function, line 797

## Internal implementation anchors

- `const GRADE_KEY = "learnloop.desks.tabGrade"` — const, line 23
- `function readGrade(): TabGrade` — function, line 25
- `const stored = window.localStorage.getItem(GRADE_KEY)` — const, line 27
- `function shortDate(iso: string | null | undefined): string` — function, line 34
- `const date = new Date(iso.length === 10 ? `$` — const, line 36
- `function clock(seconds: number): string` — function, line 40
- `const s = Math.max(0, Math.floor(seconds))` — const, line 41
- `const own = stack.filter((entry): entry is Extract<PadStackEntryDto,` — const, line 48
- `const added = Array.isArray(view?.addedPads) ? (view?.addedPads as unknown[]).filter((id): id is string` — const, line 49
- `const pad = state.pad` — const, line 55
- `const updated = pad.updatedAt.slice(0, 10)` — const, line 56
- `const p = block.payload as Record<string, unknown>` — const, line 64
- `const link = anchors.find((anchor)` — const, line 66
- `const sourceId = typeof p.source_id === "string" ? p.source_id : link?.sourceId ?? null` — const, line 67
- `const title = typeof p.source_title === "string" ? p.source_title : "the source"` — const, line 68
- `const extractionId = typeof p.extraction_id === "string" ? p.extraction_id : null` — const, line 69
- `const spanId = typeof p.span_id === "string" ? p.span_id : null` — const, line 70
- `const t = typeof p.t === "number" ? p.t : typeof link?.t === "number" ? link.t : undefined` — const, line 71
- `interface Card` — interface, line 76
- `const host = usePadsHost()` — const, line 92
- `const PadStackBody = forwardRef<PadStackHandle, PadStackProps &` — const, line 97
- `const paused = useWindowPaused()` — const, line 100
- `const pausedRef = useRef(paused)` — const, line 101
- `const padIds = useMemo(()` — const, line 103
- `const pads = padIds.map((padId)` — const, line 108
- `const today = host.today()` — const, line 109
- `const scrollerRef = useRef<HTMLDivElement | null>(null)` — const, line 112
- `const rootRef = useRef<HTMLDivElement | null>(null)` — const, line 113
- `const tabEls = useRef(new Map<string, HTMLElement>())` — const, line 114
- `const paperEls = useRef(new Map<string, HTMLElement>())` — const, line 115
- `const blockEls = useRef(new Map<string, HTMLElement>())` — const, line 116
- `const editorRef = useRef<HTMLDivElement | null>(null)` — const, line 122
- `const frame = editorRef.current` — const, line 124
- `const cardTimer = useRef<ReturnType<typeof setTimeout> | null>(null)` — const, line 128
- `const hovered = useRef<` — const, line 135
- `const split = readSplit(view, padIds)` — const, line 136
- `const muted = Array.isArray(view.mutedPads) ? (view.mutedPads as string[]) : []` — const, line 138
- `const geometry = useCallback((): PadGeometry[]` — const, line 145
- `const scroller = scrollerRef.current` — const, line 146
- `const base = scroller.getBoundingClientRect().top - scroller.scrollTop` — const, line 148
- `const tab = tabEls.current.get(padId)` — const, line 150
- `const paper = paperEls.current.get(padId)` — const, line 151
- `const paperTop = paper ? paper.getBoundingClientRect().top - base : 0` — const, line 153
- `const height = paper?.offsetHeight ?? 0` — const, line 154
- `const layoutTabs = useCallback(()` — const, line 159
- `const scroller = scrollerRef.current` — const, line 160
- `const geo = geometry()` — const, line 162
- `const top = scroller.scrollTop` — const, line 163
- `const h = scroller.clientHeight` — const, line 164
- `const now = activePad(geo, top, h, scroller.scrollHeight)` — const, line 165
- `const open = fractionalOpen(geo, top, h, scroller.scrollHeight)` — const, line 166
- `const tab = tabEls.current.get(padId)` — const, line 168
- `const paper = paperEls.current.get(padId)` — const, line 169
- `const m = mergeAmount(i, geo, top, h)` — const, line 170
- `const margin = tabMargin(grade, i, open)` — const, line 171
- `const scroller = scrollerRef.current` — const, line 191
- `let frame = 0` — let, line 193
- `const onScroll = ()` — const, line 194
- `const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(()` — const, line 202
- `const scrollToPad = useCallback((index: number)` — const, line 211
- `const scroller = scrollerRef.current` — const, line 212
- `const target = scrollTargetFor(index, geometry())` — const, line 214
- `const proposalsFor = useCallback((padId: string)` — const, line 221
- `const loadedKey = pads.map((pad)` — const, line 228
- `const write = useCallback((padId: string, ops: Parameters<typeof store.commitPad>[1]): boolean` — const, line 237
- `const refused = store.commitPad(padId, ops)` — const, line 241
- `const insertAfter = useCallback((padId: string, after: string | null, block:` — const, line 249
- `const state = store.pads[padId]` — const, line 250
- `const blockId = host.mintId("blk")` — const, line 252
- `const p = block.payload ??` — const, line 254
- `const link = block.kind === "source_piece" && typeof p.extraction_id === "string" && typeof p.span_id === "string" ? [` — const, line 255
- `const ok = write(padId, [` — const, line 258
- `const commitEdit = useCallback((next?:` — const, line 266
- `const current = next ?? editing` — const, line 267
- `const block = store.pads[current.padId]?.blocks.find((each)` — const, line 269
- `const openEditor = (padId: string, block: PadBlockDto)` — const, line 277
- `const editableNeighbour = (padId: string, blockId: string, direction: -1 | 1): PadBlockDto | null` — const, line 286
- `const blocks = store.pads[padId]?.blocks ?? []` — const, line 287
- `const index = blocks.findIndex((each)` — const, line 288
- `const onEditorKey = (event: React.KeyboardEvent<HTMLTextAreaElement>, info:` — const, line 295
- `const textarea = event.currentTarget` — const, line 297
- `const block = store.pads[editing.padId]?.blocks.find((each)` — const, line 308
- `const block = store.pads[editing.padId]?.blocks.find((each)` — const, line 313
- `const previous = editableNeighbour(editing.padId, editing.blockId, -1)` — const, line 314
- `const neighbour = editableNeighbour(editing.padId, editing.blockId, event.key === "ArrowUp" ? -1 : 1)` — const, line 319
- `const scheduleCard = (next: Card | null)` — const, line 328
- `const cardFor = (padId: string, blockId: string, kind: Card["kind"], mark: HTMLElement)` — const, line 333
- `const scroller = rootRef.current` — const, line 334
- `const box = mark.getBoundingClientRect()` — const, line 336
- `const frame = scroller.getBoundingClientRect()` — const, line 337
- `const below = box.bottom - frame.top + 6` — const, line 338
- `const above = below + 180 > frame.height` — const, line 339
- `const shownProposal = useRef<` — const, line 347
- `const open = card ? (proposals[card.padId] ?? []).find((each)` — const, line 349
- `const was = shownProposal.current` — const, line 350
- `const labelProposal = (proposal: PadProposalDto, label: "opened" | "not_this" | "dismiss" | "ignored")` — const, line 359
- `const lastPad = padIds.length - 1` — const, line 367
- `const impl = useRef<PadStackHandle | null>(null)` — const, line 368
- `const next = paneFocus + direction` — const, line 379
- `const next = active + direction` — const, line 384
- `const padId = host.mintId("pad")` — const, line 390
- `const name = `Scratchpad · $` — const, line 391
- `const padId = padIds[split ? split.pads[paneFocus] ? padIds.indexOf(split.pads[paneFocus]) : active : active]` — const, line 397
- `const state = padId ? store.pads[padId] : null` — const, line 398
- `const at = hovered.current` — const, line 406
- `const proxy = useMemo<PadStackHandle>(()` — const, line 413
- `const figureVersion = useSyncExternalStore(host.figures.subscribe, host.figures.getVersion)` — const, line 428
- `const element = blockEls.current.get(event.detail.blockId)` — const, line 441
- `const blockId = event.detail.blockId` — const, line 443
- `const renderBlock = (state: PadState, block: PadBlockDto): ReactNode` — const, line 450
- `const padId = state.pad.padId` — const, line 451
- `const isEditing = editing?.blockId === block.blockId` — const, line 452
- `const proposal = muted.includes(padId) ? null : (proposals[padId] ?? []).find((each)` — const, line 453
- `const editable = EDITABLE_KINDS.has(block.kind) && block.kind !== "sketch"` — const, line 454
- `const submission = block.submissions.find((each)` — const, line 455
- `let gutter: ReactNode = null` — let, line 456
- `let body: ReactNode` — let, line 457
- `const markEnter = (kind: Card["kind"])` — const, line 458
- `const markLeave = ()` — const, line 459
- `const markTap = (kind: Card["kind"])` — const, line 460
- `const markEl = event.currentTarget` — const, line 463
- `const next = cardFor(padId, block.blockId, kind, markEl)` — const, line 464
- `const mark = (kind: Card["kind"], glyph: string, className: string)` — const, line 468
- `const link = backLink(block, state.anchors)` — const, line 474
- `const to = String((block.payload as Record<string, unknown>).lifted_to_pad_id ?? "")` — const, line 508
- `const title = store.pads[to]?.pad.title || "its own pad"` — const, line 509
- `const question = block.kind === "text" && block.provenance === "learner" && block.bodyMd.trim().endsWith("?")` — const, line 547
- `const selected = window.getSelection?.()?.toString().trim()` — const, line 573
- `const newPadId = host.mintId("pad")` — const, line 587
- `const title = firstLine(block.bodyMd).slice(0, 48) || "lifted"` — const, line 588
- `const renderPaper = (state: PadState | null, padId: string, index: number, minHeight: number): ReactNode` — const, line 598
- `const failure = store.padFailure(padId)` — const, line 600
- `const days: Array<` — const, line 603
- `const day = state.pad.kind === "running" ? block.day ?? block.createdAt.slice(0, 10) : null` — const, line 605
- `const last = days[days.length - 1]` — const, line 606
- `const tabLabel = (state: PadState | null, padId: string, index: number): ReactNode` — const, line 631
- `const title = state?.pad.title || (state?.pad.kind === "running" ? "running" : "a pad")` — const, line 632
- `const first = state ? plainLine(state.blocks.find((block)` — const, line 633
- `const minHeight = paperMinHeight(viewport, padIds.length)` — const, line 656
- `const learnerWords = pads.some((state)` — const, line 657
- `const cardBlock = card ? store.pads[card.padId]?.blocks.find((block)` — const, line 658
- `const cardProposal = card ? (proposals[card.padId] ?? []).find((each)` — const, line 659
- `const state = store.pads[padId] ?? null` — const, line 673
- `const link = backLink(cardBlock, store.pads[card.padId]?.anchors ?? [])` — const, line 700
- `const target = cardProposal.target as` — const, line 723
- `const extractionId = target.content?.extraction_id ?? target.content?.extractionId` — const, line 724
- `function padContext(padId: string, block: PadBlockDto, anchors: Array<` — function, line 773
- `const p = block.payload as Record<string, unknown>` — const, line 774
- `const own = anchors.find((anchor)` — const, line 775
- `const anchor = own ?` — const, line 776
- `function setRef(map: Map<string, HTMLElement>, key: string, node: HTMLElement | null)` — function, line 781
- `const raw = view.split as` — const, line 788
- `const pads = (raw.pads as unknown[]).filter((id): id is string` — const, line 790
- `const ratios = Array.isArray(raw.ratios) && raw.ratios.length === pads.length ? (raw.ratios as number[]).map((r)` — const, line 792
- `const sum = ratios.reduce((a, b)` — const, line 798
- `const px = ratios.map((r)` — const, line 799
- `const min = 60` — const, line 800
- `const move = Math.max(min - px[index], Math.min(px[index + 1] - min, dy))` — const, line 801
- `function Divider(` — function, line 807
- `const start = useRef<number | null>(null)` — const, line 808

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

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

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

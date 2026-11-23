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
| Source lines | 780 |
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
- `export function stackPadIds(stack: PadStackEntryDto[], view: Record<string, unknown> | undefined): string[]` — function, line 46
- `export function tabMeta(state: PadState, today: string): string` — function, line 53
- `export function backLink(block: PadBlockDto):` — function, line 62
- `export interface PadStackProps` — interface, line 80
- `export const PadStackWindow = forwardRef<PadStackHandle, PadStackProps>(function PadStackWindow(` — const, line 86
- `export function readSplit(view: Record<string, unknown>, padIds: string[]):` — function, line 744
- `export function moveDivider(ratios: number[], index: number, dy: number, total = 600): number[]` — function, line 754

## Internal implementation anchors

- `const GRADE_KEY = "learnloop.desks.tabGrade"` — const, line 23
- `function readGrade(): TabGrade` — function, line 25
- `const stored = window.localStorage.getItem(GRADE_KEY)` — const, line 27
- `function shortDate(iso: string | null | undefined): string` — function, line 34
- `const date = new Date(iso.length === 10 ? `$` — const, line 36
- `function clock(seconds: number): string` — function, line 40
- `const s = Math.max(0, Math.floor(seconds))` — const, line 41
- `const own = stack.filter((entry): entry is Extract<PadStackEntryDto,` — const, line 47
- `const added = Array.isArray(view?.addedPads) ? (view?.addedPads as unknown[]).filter((id): id is string` — const, line 48
- `const pad = state.pad` — const, line 54
- `const updated = pad.updatedAt.slice(0, 10)` — const, line 55
- `const p = block.payload as Record<string, unknown>` — const, line 63
- `const title = typeof p.source_title === "string" ? p.source_title : "the source"` — const, line 64
- `const extractionId = typeof p.extraction_id === "string" ? p.extraction_id : null` — const, line 65
- `const spanId = typeof p.span_id === "string" ? p.span_id : null` — const, line 66
- `interface Card` — interface, line 71
- `const host = usePadsHost()` — const, line 87
- `const PadStackBody = forwardRef<PadStackHandle, PadStackProps &` — const, line 92
- `const paused = useWindowPaused()` — const, line 95
- `const padIds = useMemo(()` — const, line 96
- `const pads = padIds.map((padId)` — const, line 101
- `const today = host.today()` — const, line 102
- `const scrollerRef = useRef<HTMLDivElement | null>(null)` — const, line 105
- `const tabEls = useRef(new Map<string, HTMLElement>())` — const, line 106
- `const paperEls = useRef(new Map<string, HTMLElement>())` — const, line 107
- `const blockEls = useRef(new Map<string, HTMLElement>())` — const, line 108
- `const editorRef = useRef<HTMLDivElement | null>(null)` — const, line 114
- `const frame = editorRef.current` — const, line 116
- `const cardTimer = useRef<ReturnType<typeof setTimeout> | null>(null)` — const, line 120
- `const hovered = useRef<` — const, line 127
- `const split = readSplit(view, padIds)` — const, line 128
- `const muted = Array.isArray(view.mutedPads) ? (view.mutedPads as string[]) : []` — const, line 130
- `const geometry = useCallback((): PadGeometry[]` — const, line 137
- `const scroller = scrollerRef.current` — const, line 138
- `const base = scroller.getBoundingClientRect().top - scroller.scrollTop` — const, line 140
- `const tab = tabEls.current.get(padId)` — const, line 142
- `const paper = paperEls.current.get(padId)` — const, line 143
- `const paperTop = paper ? paper.getBoundingClientRect().top - base : 0` — const, line 145
- `const height = paper?.offsetHeight ?? 0` — const, line 146
- `const layoutTabs = useCallback(()` — const, line 151
- `const scroller = scrollerRef.current` — const, line 152
- `const geo = geometry()` — const, line 154
- `const top = scroller.scrollTop` — const, line 155
- `const h = scroller.clientHeight` — const, line 156
- `const now = activePad(geo, top, h, scroller.scrollHeight)` — const, line 157
- `const open = fractionalOpen(geo, top, h, scroller.scrollHeight)` — const, line 158
- `const tab = tabEls.current.get(padId)` — const, line 160
- `const paper = paperEls.current.get(padId)` — const, line 161
- `const m = mergeAmount(i, geo, top, h)` — const, line 162
- `const margin = tabMargin(grade, i, open)` — const, line 163
- `const scroller = scrollerRef.current` — const, line 183
- `let frame = 0` — let, line 185
- `const onScroll = ()` — const, line 186
- `const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(()` — const, line 194
- `const scrollToPad = useCallback((index: number)` — const, line 203
- `const scroller = scrollerRef.current` — const, line 204
- `const target = scrollTargetFor(index, geometry())` — const, line 206
- `const proposalsFor = useCallback((padId: string)` — const, line 213
- `const loadedKey = pads.map((pad)` — const, line 220
- `const write = useCallback((padId: string, ops: Parameters<typeof store.commitPad>[1]): boolean` — const, line 229
- `const refused = store.commitPad(padId, ops)` — const, line 232
- `const insertAfter = useCallback((padId: string, after: string | null, block:` — const, line 240
- `const state = store.pads[padId]` — const, line 241
- `const blockId = host.mintId("blk")` — const, line 243
- `const p = block.payload ??` — const, line 245
- `const link = block.kind === "source_piece" && typeof p.extraction_id === "string" && typeof p.span_id === "string" ? [` — const, line 246
- `const ok = write(padId, [` — const, line 249
- `const commitEdit = useCallback((next?:` — const, line 257
- `const current = next ?? editing` — const, line 258
- `const block = store.pads[current.padId]?.blocks.find((each)` — const, line 260
- `const openEditor = (padId: string, block: PadBlockDto)` — const, line 268
- `const editableNeighbour = (padId: string, blockId: string, direction: -1 | 1): PadBlockDto | null` — const, line 275
- `const blocks = store.pads[padId]?.blocks ?? []` — const, line 276
- `const index = blocks.findIndex((each)` — const, line 277
- `const onEditorKey = (event: React.KeyboardEvent<HTMLTextAreaElement>, info:` — const, line 284
- `const textarea = event.currentTarget` — const, line 286
- `const block = store.pads[editing.padId]?.blocks.find((each)` — const, line 297
- `const block = store.pads[editing.padId]?.blocks.find((each)` — const, line 302
- `const previous = editableNeighbour(editing.padId, editing.blockId, -1)` — const, line 303
- `const neighbour = editableNeighbour(editing.padId, editing.blockId, event.key === "ArrowUp" ? -1 : 1)` — const, line 308
- `const scheduleCard = (next: Card | null)` — const, line 317
- `const cardFor = (padId: string, blockId: string, kind: Card["kind"], mark: HTMLElement)` — const, line 321
- `const scroller = scrollerRef.current` — const, line 322
- `const box = mark.getBoundingClientRect()` — const, line 324
- `const frame = scroller.getBoundingClientRect()` — const, line 325
- `const below = box.bottom - frame.top + 6` — const, line 326
- `const above = below + 180 > frame.height` — const, line 327
- `const shownProposal = useRef<` — const, line 335
- `const open = card ? (proposals[card.padId] ?? []).find((each)` — const, line 337
- `const was = shownProposal.current` — const, line 338
- `const labelProposal = (proposal: PadProposalDto, label: "opened" | "not_this" | "dismiss" | "ignored")` — const, line 347
- `const lastPad = padIds.length - 1` — const, line 355
- `const impl = useRef<PadStackHandle | null>(null)` — const, line 356
- `const next = paneFocus + direction` — const, line 367
- `const next = active + direction` — const, line 372
- `const padId = host.mintId("pad")` — const, line 378
- `const name = `Scratchpad · $` — const, line 379
- `const padId = padIds[split ? split.pads[paneFocus] ? padIds.indexOf(split.pads[paneFocus]) : active : active]` — const, line 385
- `const state = padId ? store.pads[padId] : null` — const, line 386
- `const at = hovered.current` — const, line 394
- `const proxy = useMemo<PadStackHandle>(()` — const, line 401
- `const element = blockEls.current.get(event.detail.blockId)` — const, line 417
- `const blockId = event.detail.blockId` — const, line 419
- `const renderBlock = (state: PadState, block: PadBlockDto): ReactNode` — const, line 426
- `const padId = state.pad.padId` — const, line 427
- `const isEditing = editing?.blockId === block.blockId` — const, line 428
- `const proposal = muted.includes(padId) ? null : (proposals[padId] ?? []).find((each)` — const, line 429
- `const editable = EDITABLE_KINDS.has(block.kind) && block.kind !== "sketch"` — const, line 430
- `const submission = block.submissions.find((each)` — const, line 431
- `let gutter: ReactNode = null` — let, line 432
- `let body: ReactNode` — let, line 433
- `const markEnter = (kind: Card["kind"])` — const, line 434
- `const markLeave = ()` — const, line 435
- `const markTap = (kind: Card["kind"])` — const, line 436
- `const mark = (kind: Card["kind"], glyph: string, className: string)` — const, line 440
- `const link = backLink(block)` — const, line 446
- `const to = String((block.payload as Record<string, unknown>).lifted_to_pad_id ?? "")` — const, line 480
- `const title = store.pads[to]?.pad.title || "its own pad"` — const, line 481
- `const question = block.kind === "text" && block.provenance === "learner" && block.bodyMd.trim().endsWith("?")` — const, line 519
- `const selected = window.getSelection?.()?.toString().trim()` — const, line 544
- `const newPadId = host.mintId("pad")` — const, line 557
- `const title = firstLine(block.bodyMd).slice(0, 48) || "lifted"` — const, line 558
- `const renderPaper = (state: PadState | null, padId: string, index: number, minHeight: number): ReactNode` — const, line 568
- `const failure = store.padFailure(padId)` — const, line 570
- `const days: Array<` — const, line 573
- `const day = state.pad.kind === "running" ? block.day ?? block.createdAt.slice(0, 10) : null` — const, line 575
- `const last = days[days.length - 1]` — const, line 576
- `const tabLabel = (state: PadState | null, padId: string, index: number): ReactNode` — const, line 601
- `const title = state?.pad.title || (state?.pad.kind === "running" ? "running" : "a pad")` — const, line 602
- `const first = state ? plainLine(state.blocks.find((block)` — const, line 603
- `const minHeight = paperMinHeight(viewport, padIds.length)` — const, line 626
- `const learnerWords = pads.some((state)` — const, line 627
- `const cardBlock = card ? store.pads[card.padId]?.blocks.find((block)` — const, line 628
- `const cardProposal = card ? (proposals[card.padId] ?? []).find((each)` — const, line 629
- `const state = store.pads[padId] ?? null` — const, line 643
- `const target = cardProposal.target as` — const, line 690
- `const extractionId = target.content?.extraction_id ?? target.content?.extractionId` — const, line 691
- `function setRef(map: Map<string, HTMLElement>, key: string, node: HTMLElement | null)` — function, line 738
- `const raw = view.split as` — const, line 745
- `const pads = (raw.pads as unknown[]).filter((id): id is string` — const, line 747
- `const ratios = Array.isArray(raw.ratios) && raw.ratios.length === pads.length ? (raw.ratios as number[]).map((r)` — const, line 749
- `const sum = ratios.reduce((a, b)` — const, line 755
- `const px = ratios.map((r)` — const, line 756
- `const min = 60` — const, line 757
- `const move = Math.max(min - px[index], Math.min(px[index + 1] - min, dy))` — const, line 758
- `function Divider(` — function, line 764
- `const start = useRef<number | null>(null)` — const, line 765

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `PadStackWindow`; references `PadStackWindow`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `PadStackWindow`; references `PadStackWindow`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `PadBlockDto`, `PadProposalDto`, `PadStackEntryDto`
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

---
title: "Desktop module · src/screens/reader/ComparePointTable.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.ComparePointTable"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/ComparePointTable.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/ComparePointTable.tsx"
source_commit: "8aaceff1c1d67d468de00bf69fe1ad22c94e630c"
source_commit_timestamp: "2026-10-31T13:59:58-04:00"
source_worktree_state: "staged-or-mixed"
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

# `src/screens/reader/ComparePointTable.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `ComparePointTable` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/ComparePointTable.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/ComparePointTable.tsx) |
| Source lines | 819 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `staged-or-mixed` |
| Source commit | `8aaceff1c1d67d468de00bf69fe1ad22c94e630c` |
| Commit timestamp | `2026-10-31T13:59:58-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/ComparePointTable|src/screens/reader/ComparePointTable.tsx]]

## Public API

- `export const POINT_COPY =` — const, line 41
- `export interface CompareGridActions` — interface, line 71
- `export const CompareGridActionsContext = createContext<CompareGridActions | null>(null)` — const, line 82
- `export function useCompareGridActions(): CompareGridActions` — function, line 84
- `export function ComparePointTable(` — function, line 134

## Internal implementation anchors

- `const linkStyle =` — const, line 88
- `const quietStyle =` — const, line 92
- `const headStyle =` — const, line 93
- `const chipStyle =` — const, line 94
- `const sourceRule =` — const, line 96
- `const modelRule =` — const, line 97
- `const learnerRule =` — const, line 98
- `const CLAMP_CHARS = 140` — const, line 100
- `type Target = "comparison" | string` — type, line 102
- `function useWidth(ref: RefObject<HTMLElement | null>): number | null` — function, line 104
- `const node = ref.current` — const, line 107
- `const measure = ()` — const, line 109
- `const observer = new ResizeObserver(measure)` — const, line 112
- `function useWindowWidth(): number` — function, line 119
- `const onResize = ()` — const, line 122
- `function splitKey(key: string):` — function, line 129
- `const at = key.indexOf(":")` — const, line 130
- `const keepCtx = useCompareKeep()` — const, line 135
- `const actions = useCompareGridActions()` — const, line 136
- `const points = table.points ?? []` — const, line 137
- `const columns = table.rows` — const, line 138
- `const titles = columnTitles(table)` — const, line 139
- `const moved = useRef(false)` — const, line 152
- `const frameRef = useRef<HTMLDivElement | null>(null)` — const, line 153
- `const takeRef = useRef<HTMLInputElement | null>(null)` — const, line 154
- `const paneWidth = useWidth(frameRef)` — const, line 159
- `const windowWidth = useWindowWidth()` — const, line 160
- `const desired = useRef<string[]>(hidden)` — const, line 165
- `const confirmed = useRef<string[]>(hidden)` — const, line 166
- `const queue = useRef<Promise<unknown>>(Promise.resolve())` — const, line 167
- `const hidesWaiting = useRef(0)` — const, line 168
- `const keeping = useRef(false)` — const, line 171
- `const keptNow = useRef<KeptComparisonDto | null>(kept)` — const, line 172
- `const draftsRef = useRef(drafts)` — const, line 173
- `const cards = layout === "by_point" && cardsByPoint(paneWidth, windowWidth)` — const, line 182
- `const canKeep = Boolean(keepCtx && (keepCtx.settings.library || table.kept) && table.status === "ok" && table.comparisonId)` — const, line 184
- `const comparisonId = table.comparisonId` — const, line 185
- `const byBook = layout === "by_book"` — const, line 188
- `const shownPoints = points.filter((point)` — const, line 189
- `const youCard = byBook && Boolean(keepCtx)` — const, line 192
- `const rowCount = byBook ? columns.length + (youCard ? 1 : 0) : points.length` — const, line 193
- `const colsOf = (row: number)` — const, line 194
- `const point = points[row]` — const, line 196
- `const row = Math.min(focus.row, Math.max(rowCount - 1, 0))` — const, line 203
- `const col = Math.min(focus.col, Math.max(colsOf(row) - 1, 0))` — const, line 204
- `const active = document.activeElement` — const, line 206
- `const setLayout = (next: CompareLayout)` — const, line 217
- `const takesOf = (target: Target)` — const, line 222
- `const serial = <T,>(job: ()` — const, line 225
- `const next = queue.current.then(job, job)` — const, line 226
- `const send = async (input:` — const, line 231
- `const result = await api.readerLibraryCompareKeep(` — const, line 236
- `const keep = async ()` — const, line 262
- `const rowsHidden = desired.current` — const, line 267
- `const entries = Object.entries(drafts).filter(([, text])` — const, line 268
- `const sent = entries.filter(([target])` — const, line 269
- `const takes: KeepTakeDto[] = sent.map(([target, text])` — const, line 270
- `const ok = await serial(async ()` — const, line 273
- `const syncHidden = ()` — const, line 287
- `const want = desired.current` — const, line 290
- `const before = confirmed.current` — const, line 298
- `const shownAgain = before.filter((id)` — const, line 304
- `const takes: KeepTakeDto[] = shownAgain.map((id)` — const, line 305
- `const ok = await send(takes.length ?` — const, line 306
- `const remove = async ()` — const, line 314
- `const toggleHidden = (pointId: string)` — const, line 330
- `const base = desired.current` — const, line 331
- `const next = base.includes(pointId) ? base.filter((id)` — const, line 332
- `const openTake = (target: Target)` — const, line 341
- `const submitTake = async (target: Target)` — const, line 347
- `const text = takeText.trim()` — const, line 348
- `const take: KeepTakeDto = target === "comparison" ?` — const, line 354
- `const takeFromNote = async (text: string): Promise<NoteTakeOutcome>` — const, line 369
- `const saved = await serial(()` — const, line 372
- `const toggle = (list: string[], value: string)` — const, line 379
- `const cellAt = (at: CellPosition):` — const, line 382
- `const book = at.col > 0 && at.row < columns.length ? at.row : null` — const, line 384
- `const point = points[at.row] ?? null` — const, line 387
- `const quotedCell = (point: ComparePointDto | null, column: number | null): ComparePointCellDto | null` — const, line 391
- `const cell = point.cells.find((entry)` — const, line 393
- `const onKeyDown = (event: ReactKeyboardEvent<HTMLElement>)` — const, line 397
- `const target = event.target as HTMLElement` — const, line 398
- `const next = moveCell(focus, event.key, rowCount, colsOf)` — const, line 410
- `const cell = quotedCell(point, column)` — const, line 419
- `const handled = ()` — const, line 420
- `const cellProps = (row: number, col: number, label: string)` — const, line 486
- `const question = table.scope?.question ?? table.query ?? null` — const, line 496
- `const firstModelPoint = points.findIndex((point)` — const, line 497
- `const quote = (point: ComparePointDto, cell: ComparePointCellDto)` — const, line 499
- `const open = expanded.includes(`$` — const, line 500
- `const text = cell.quote ?? ""` — const, line 501
- `const long = text.length > CLAMP_CHARS` — const, line 502
- `const bookCell = (point: ComparePointDto, column: number): ReactNode` — const, line 519
- `const cell = point.cells.find((entry)` — const, line 520
- `const cellLabel = (point: ComparePointDto, column: number): string` — const, line 537
- `const title = columns[column].sourceTitle ?? "a source"` — const, line 538
- `const cell = point.cells.find((entry)` — const, line 539
- `const chips = (point: ComparePointDto)` — const, line 546
- `const list = rowChips(point, titles)` — const, line 547
- `const pairs = chipPairs(point)` — const, line 549
- `const open = pairsOpen.includes(point.id)` — const, line 550
- `const pairsBand = (point: ComparePointDto)` — const, line 570
- `const rowHeader = (point: ComparePointDto, index: number)` — const, line 588
- `const learner = point.labelVoice === "learner"` — const, line 589
- `const takeBox = (target: Target, placeholder: string)` — const, line 610
- `const youCell = (target: Target)` — const, line 628
- `const takes = takesOf(target)` — const, line 630
- `const draft = drafts[target]` — const, line 631
- `const youOrAdd = (point: ComparePointDto, empty: ReactNode = null): ReactNode` — const, line 650
- `const hiddenRow = (point: ComparePointDto, row: number)` — const, line 656
- `const grid = ()` — const, line 667
- `const template = `$` — const, line 668
- `const stickyHead =` — const, line 669
- `const cardsView = ()` — const, line 700
- `const byBookView = ()` — const, line 721
- `const unverified = table.unverifiedSources ?? []` — const, line 756

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]] — import-or-re-export: `CompareGridActions`, `CompareGridActionsContext`, `ComparePointTable`, `useCompareGridActions`; references `CompareGridActions`, `CompareGridActionsContext`, `ComparePointTable`, `useCompareGridActions`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ComparePointCellDto`, `ComparePointDto`, `CompareTableDto`, `KeepTakeDto`, `KeptComparisonDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/CompareKeep|src/screens/reader/CompareKeep.tsx]] — import-or-re-export; imports `KEEP_COPY`, `fineLabel`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderNotes|src/screens/reader/ReaderNotes.tsx]] — import-or-re-export; imports `NoteTakeOutcome`, `NotesTakeBand`
- [[Reference/Desktop/TypeScript/screens/reader/compareKeepContext|src/screens/reader/compareKeepContext.ts]] — import-or-re-export; imports `useCompareKeep`
- [[Reference/Desktop/TypeScript/screens/reader/comparePoints|src/screens/reader/comparePoints.ts]] — import-or-re-export; imports `CellPosition`, `CompareLayout`, `POINT_COLUMN_PX`, `READABLE_CELL_PX`, `YOU_COLUMN_PX`, `cardsByPoint`, `chipPairs`, `columnTitles`, `moveCell`, `notFound`, `readLayout`, `rowChips`, `writeLayout`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `MeaningLabel`, `SpokenOnly`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/comparePointTableCodexReview.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/comparePointTableCodexReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/comparePointTable.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/comparePointTable.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/ComparePointTable.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/ComparePointTable.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

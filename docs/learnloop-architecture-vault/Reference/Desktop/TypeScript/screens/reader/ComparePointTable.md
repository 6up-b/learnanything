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
source_worktree_state: "clean"
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
| Source lines | 804 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `8aaceff1c1d67d468de00bf69fe1ad22c94e630c` |
| Commit timestamp | `2026-10-31T13:59:58-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/ComparePointTable|src/screens/reader/ComparePointTable.tsx]]

## Public API

- `export const POINT_COPY =` — const, line 40
- `export interface CompareGridActions` — interface, line 70
- `export const CompareGridActionsContext = createContext<CompareGridActions | null>(null)` — const, line 81
- `export function useCompareGridActions(): CompareGridActions` — function, line 83
- `export function ComparePointTable(` — function, line 133

## Internal implementation anchors

- `const linkStyle =` — const, line 87
- `const quietStyle =` — const, line 91
- `const headStyle =` — const, line 92
- `const chipStyle =` — const, line 93
- `const sourceRule =` — const, line 95
- `const modelRule =` — const, line 96
- `const learnerRule =` — const, line 97
- `const CLAMP_CHARS = 140` — const, line 99
- `type Target = "comparison" | string` — type, line 101
- `function useWidth(ref: RefObject<HTMLElement | null>): number | null` — function, line 103
- `const node = ref.current` — const, line 106
- `const measure = ()` — const, line 108
- `const observer = new ResizeObserver(measure)` — const, line 111
- `function useWindowWidth(): number` — function, line 118
- `const onResize = ()` — const, line 121
- `function splitKey(key: string):` — function, line 128
- `const at = key.indexOf(":")` — const, line 129
- `const keepCtx = useCompareKeep()` — const, line 134
- `const actions = useCompareGridActions()` — const, line 135
- `const points = table.points ?? []` — const, line 136
- `const columns = table.rows` — const, line 137
- `const titles = columnTitles(table)` — const, line 138
- `const moved = useRef(false)` — const, line 151
- `const frameRef = useRef<HTMLDivElement | null>(null)` — const, line 152
- `const takeRef = useRef<HTMLInputElement | null>(null)` — const, line 153
- `const paneWidth = useWidth(frameRef)` — const, line 158
- `const windowWidth = useWindowWidth()` — const, line 159
- `const desired = useRef<string[]>(hidden)` — const, line 164
- `const confirmed = useRef<string[]>(hidden)` — const, line 165
- `const queue = useRef<Promise<unknown>>(Promise.resolve())` — const, line 166
- `const hidesWaiting = useRef(0)` — const, line 167
- `const keeping = useRef(false)` — const, line 170
- `const keptNow = useRef<KeptComparisonDto | null>(kept)` — const, line 171
- `const draftsRef = useRef(drafts)` — const, line 172
- `const cards = layout === "by_point" && cardsByPoint(paneWidth, windowWidth)` — const, line 181
- `const canKeep = Boolean(keepCtx && (keepCtx.settings.library || table.kept) && table.status === "ok" && table.comparisonId)` — const, line 183
- `const comparisonId = table.comparisonId` — const, line 184
- `const byBook = layout === "by_book"` — const, line 187
- `const shownPoints = points.filter((point)` — const, line 188
- `const youCard = byBook && Boolean(keepCtx)` — const, line 191
- `const rowCount = byBook ? columns.length + (youCard ? 1 : 0) : points.length` — const, line 192
- `const colsOf = (row: number)` — const, line 193
- `const point = points[row]` — const, line 195
- `const row = Math.min(focus.row, Math.max(rowCount - 1, 0))` — const, line 202
- `const col = Math.min(focus.col, Math.max(colsOf(row) - 1, 0))` — const, line 203
- `const active = document.activeElement` — const, line 205
- `const setLayout = (next: CompareLayout)` — const, line 216
- `const takesOf = (target: Target)` — const, line 221
- `const serial = <T,>(job: ()` — const, line 224
- `const next = queue.current.then(job, job)` — const, line 225
- `const send = async (input:` — const, line 230
- `const result = await api.readerLibraryCompareKeep(` — const, line 235
- `const keep = async ()` — const, line 261
- `const rowsHidden = desired.current` — const, line 266
- `const entries = Object.entries(drafts).filter(([, text])` — const, line 267
- `const sent = entries.filter(([target])` — const, line 268
- `const takes: KeepTakeDto[] = sent.map(([target, text])` — const, line 269
- `const ok = await serial(async ()` — const, line 272
- `const syncHidden = ()` — const, line 286
- `const want = desired.current` — const, line 289
- `const before = confirmed.current` — const, line 297
- `const shownAgain = before.filter((id)` — const, line 303
- `const takes: KeepTakeDto[] = shownAgain.map((id)` — const, line 304
- `const ok = await send(takes.length ?` — const, line 305
- `const remove = async ()` — const, line 313
- `const toggleHidden = (pointId: string)` — const, line 329
- `const base = desired.current` — const, line 330
- `const next = base.includes(pointId) ? base.filter((id)` — const, line 331
- `const openTake = (target: Target)` — const, line 340
- `const submitTake = async (target: Target)` — const, line 346
- `const text = takeText.trim()` — const, line 347
- `const take: KeepTakeDto = target === "comparison" ?` — const, line 353
- `const toggle = (list: string[], value: string)` — const, line 366
- `const cellAt = (at: CellPosition):` — const, line 369
- `const book = at.col > 0 && at.row < columns.length ? at.row : null` — const, line 371
- `const point = points[at.row] ?? null` — const, line 374
- `const quotedCell = (point: ComparePointDto | null, column: number | null): ComparePointCellDto | null` — const, line 378
- `const cell = point.cells.find((entry)` — const, line 380
- `const onKeyDown = (event: ReactKeyboardEvent<HTMLElement>)` — const, line 384
- `const target = event.target as HTMLElement` — const, line 385
- `const next = moveCell(focus, event.key, rowCount, colsOf)` — const, line 397
- `const cell = quotedCell(point, column)` — const, line 406
- `const handled = ()` — const, line 407
- `const cellProps = (row: number, col: number, label: string)` — const, line 473
- `const question = table.scope?.question ?? table.query ?? null` — const, line 483
- `const firstModelPoint = points.findIndex((point)` — const, line 484
- `const quote = (point: ComparePointDto, cell: ComparePointCellDto)` — const, line 486
- `const open = expanded.includes(`$` — const, line 487
- `const text = cell.quote ?? ""` — const, line 488
- `const long = text.length > CLAMP_CHARS` — const, line 489
- `const bookCell = (point: ComparePointDto, column: number): ReactNode` — const, line 506
- `const cell = point.cells.find((entry)` — const, line 507
- `const cellLabel = (point: ComparePointDto, column: number): string` — const, line 524
- `const title = columns[column].sourceTitle ?? "a source"` — const, line 525
- `const cell = point.cells.find((entry)` — const, line 526
- `const chips = (point: ComparePointDto)` — const, line 533
- `const list = rowChips(point, titles)` — const, line 534
- `const pairs = chipPairs(point)` — const, line 536
- `const open = pairsOpen.includes(point.id)` — const, line 537
- `const pairsBand = (point: ComparePointDto)` — const, line 557
- `const rowHeader = (point: ComparePointDto, index: number)` — const, line 575
- `const learner = point.labelVoice === "learner"` — const, line 576
- `const takeBox = (target: Target, placeholder: string)` — const, line 597
- `const youCell = (target: Target)` — const, line 615
- `const takes = takesOf(target)` — const, line 617
- `const draft = drafts[target]` — const, line 618
- `const youOrAdd = (point: ComparePointDto, empty: ReactNode = null): ReactNode` — const, line 637
- `const hiddenRow = (point: ComparePointDto, row: number)` — const, line 643
- `const grid = ()` — const, line 654
- `const template = `$` — const, line 655
- `const stickyHead =` — const, line 656
- `const cardsView = ()` — const, line 687
- `const byBookView = ()` — const, line 708
- `const unverified = table.unverifiedSources ?? []` — const, line 743

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

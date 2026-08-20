---
title: "Desktop module · src/screens/SqliteBrowser.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.SqliteBrowser"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/SqliteBrowser.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/SqliteBrowser.tsx"
source_commit: "b19e81d9993c28e995049da1aa16f8d316d56d68"
source_commit_timestamp: "2026-07-13T13:41:22-04:00"
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

# `src/screens/SqliteBrowser.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `SqliteBrowser` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/SqliteBrowser.tsx](../../../../../../apps/learnloop-tauri/src/screens/SqliteBrowser.tsx) |
| Source lines | 715 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `b19e81d9993c28e995049da1aa16f8d316d56d68` |
| Commit timestamp | `2026-07-13T13:41:22-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/SqliteBrowser|src/screens/SqliteBrowser.tsx]]

## Public API

- `export function SqliteBrowser(` — function, line 114

## Internal implementation anchors

- `type KeyboardEvent as ReactKeyboardEvent, type RefObject } from "react"` — type, line 7
- `type RefObject } from "react"` — type, line 8
- `const PAGE = 200` — const, line 14
- `type Cell = string | number | boolean | null` — type, line 16
- `type BrowserMode = "nav" | "edit"` — type, line 17
- `type CellPosition =` — type, line 18
- `function CellText(` — function, line 20
- `function GridCell(` — function, line 29
- `const tdStyle =` — const, line 44
- `function ConsoleResult(` — function, line 74
- `const gridRef = useRef<HTMLDivElement>(null)` — const, line 127
- `const editRef = useRef<HTMLTextAreaElement>(null)` — const, line 128
- `const cellRefs = useRef(new Map<string, HTMLTableCellElement>())` — const, line 129
- `const initialFocusPath = useRef<string | null>(null)` — const, line 130
- `const refreshTables = useCallback(async ()` — const, line 132
- `const snapshot = await api.sqliteTables(path)` — const, line 134
- `const loadTable = useCallback( async (table: string, nextOffset: number)` — const, line 155
- `const updateCell = async (rowid: number, column: string, value: string | null): Promise<boolean>` — const, line 191
- `const insertRow = async ()` — const, line 206
- `const deleteRow = async (rowid: number)` — const, line 220
- `const runSql = async ()` — const, line 234
- `const result = await api.sqliteExec(path, sql)` — const, line 238
- `const editable = Boolean(data?.editable)` — const, line 252
- `const rangeEnd = data ? Math.min(offset + (data.rows.length || 0), data.rowCount) : 0` — const, line 253
- `const pkSet = useMemo(()` — const, line 254
- `const selectedValue = activeCell && data ? data.rows[activeCell.row]?.cells[activeCell.column] : undefined` — const, line 255
- `const selectedColumn = activeCell && data ? data.columns[activeCell.column] : undefined` — const, line 256
- `const selectedRow = activeCell && data ? data.rows[activeCell.row] : undefined` — const, line 257
- `const selectedCellEditable = Boolean(editable && selectedRow?.rowid !== null && selectedRow?.rowid !== undefined)` — const, line 258
- `const focusGrid = ()` — const, line 260
- `const selectCell = (position: CellPosition, openInspector = false)` — const, line 262
- `const beginCellEdit = (position: CellPosition | null = activeCell)` — const, line 269
- `const row = data.rows[position.row]` — const, line 271
- `const value = row?.cells[position.column]` — const, line 272
- `const cancelCellEdit = ()` — const, line 281
- `const commitCellEdit = async ()` — const, line 286
- `const saved = await updateCell(selectedRow.rowid, selectedColumn.name, editAsNull ? null : editDraft)` — const, line 288
- `const moveCell = (rowDelta: number, columnDelta: number)` — const, line 295
- `const current = activeCell ??` — const, line 297
- `const onGridKeyDown = (event: ReactKeyboardEvent<HTMLDivElement>)` — const, line 304
- `let handled = true` — let, line 306
- `const key = `$` — const, line 418
- `function CellInspector(` — function, line 501
- `function ActionButton(` — function, line 672
- `const headStyle =` — const, line 694
- `const cellStyle =` — const, line 708

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] — import-or-re-export: `SqliteBrowser`; references `SqliteBrowser`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `SqliteExecResult`, `SqliteTableInfo`, `SqliteTableSnapshot`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `Pill`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Inspect Persistent State|Inspect Persistent State]] — owns safe inspection.
- [[Architecture/State and Persistence#Open modes and migrations|state open modes]] — owns persistence safety.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_maintenance_feed.py](../../../../../../tests/test_maintenance_feed.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_doctor.py](../../../../../../tests/test_doctor.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_desktop_rpc_contract.py](../../../../../../tests/test_desktop_rpc_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/SqliteBrowser.tsx](../../../../../../apps/learnloop-tauri/src/screens/SqliteBrowser.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

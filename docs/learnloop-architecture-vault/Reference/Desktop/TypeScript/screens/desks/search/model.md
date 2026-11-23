---
title: "Desktop module · src/screens/desks/search/model.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.search.model"
language: "TypeScript"
area: "TypeScript/screens/desks/search"
source_path: "apps/learnloop-tauri/src/screens/desks/search/model.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/search/model.ts"
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

# `src/screens/desks/search/model.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/search/_area|TypeScript/screens/desks/search]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `ROWS_PER_GROUP`, `GROUP_ORDER`, `OpenWindow`, `SearchRow` and related exports within the desktop's TypeScript/screens/desks/search ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/search/model.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/search/model.ts) |
| Source lines | 166 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/search/_area|TypeScript/screens/desks/search]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/search/model|src/screens/desks/search/model.ts]]

## Public API

- `export const ROWS_PER_GROUP = 3` — const, line 20
- `export const GROUP_ORDER: readonly SearchScope[] = ["sources", "passages", "notes", "pads", "threads", "exchanges"]` — const, line 22
- `export interface OpenWindow` — interface, line 25
- `export type SearchRow = |` — type, line 30
- `export interface ShownGroup` — interface, line 35
- `export function describeRow(group: SearchScope, raw: SearchGroupDto["rows"][number], deskTitle: (deskId: string | null)` — function, line 60
- `export function shownGroups(input:` — function, line 105
- `export function selectableRows(groups: ShownGroup[]): SearchRow[]` — function, line 156
- `export function meaningNote(words: SearchEverythingDto | null, fromJob: ReadonlyArray<` — function, line 162

## Internal implementation anchors

- `function shortDate(iso: string | null | undefined): string` — function, line 47
- `const date = new Date(iso)` — const, line 49
- `function clip(text: string, length = 140): string` — function, line 54
- `const flat = text.replace(/\s+/g, " ").trim()` — const, line 55
- `const row = raw as SearchSourceRowDto` — const, line 63
- `const kind = row.ref?.kind === "video" ? "video" : "source"` — const, line 64
- `const row = raw as SearchPassageRowDto` — const, line 68
- `const at = row.ref?.kind === "video" && typeof row.target?.t === "number" ? ` ▶ $` — const, line 69
- `const row = raw as SearchNoteRowDto` — const, line 73
- `const row = raw as SearchPadRowDto` — const, line 78
- `const row = raw as SearchThreadRowDto` — const, line 82
- `const row = raw as SearchExchangeRowDto` — const, line 86
- `function clock(seconds: number): string` — function, line 92
- `const s = Math.max(0, Math.floor(seconds))` — const, line 93
- `function rowKey(group: SearchScope, raw: SearchGroupDto["rows"][number], index: number): string` — function, line 97
- `const r = raw as unknown as Record<string, unknown>` — const, line 98
- `const id = r.spanId ?? r.blockId ?? r.noteKey ?? r.gapId ?? r.questionEventId ?? r.sourceId ?? index` — const, line 99
- `const out: ShownGroup[] = []` — const, line 114
- `const q = input.query.trim().toLowerCase()` — const, line 115
- `const openRows: SearchRow[] = input.open .filter((window)` — const, line 116
- `const pendingGroups = new Set(input.meaningPending ? input.words.meaning.groups ?? [] : [])` — const, line 121
- `const words = input.words.groups.find((group)` — const, line 123
- `const meaning = input.meaning.find((group)` — const, line 124
- `const rows: SearchRow[] = []` — const, line 125
- `const seen = new Set<string>()` — const, line 126
- `const key = rowKey(id, raw, index)` — const, line 130
- `const described = describeRow(id, raw, input.deskTitle)` — const, line 133
- `const off = words && words.status !== "ok" ? words.reason ?? "not available" : meaning && meaning.status !== "ok" ? `by meaning: $` — const, line 139
- `function limit(group: ShownGroup, expanded: ReadonlySet<string>): ShownGroup` — function, line 150
- `const reasons = [...new Set([...words.meaning.unavailable, ...fromJob].map((entry)` — const, line 164

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `SearchRow`; references `SearchRow`
- [[Reference/Desktop/TypeScript/screens/desks/pads/host|src/screens/desks/pads/host.ts]] — import-or-re-export: `SearchRow`; references `SearchRow`
- [[Reference/Desktop/TypeScript/screens/desks/search/SearchPanel|src/screens/desks/search/SearchPanel.tsx]] — import-or-re-export: `OpenWindow`, `SearchRow`, `meaningNote`, `selectableRows`, `shownGroups`; references `OpenWindow`, `SearchRow`, `meaningNote`, `selectableRows`, `shownGroups`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ContentRefDto`, `SearchEverythingDto`, `SearchExchangeRowDto`, `SearchGroupDto`, `SearchNoteRowDto`, `SearchPadRowDto`, `SearchPassageRowDto`, `SearchRowBase`, `SearchScope`, `SearchSourceRowDto`, `SearchThreadRowDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/search/model.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/search/model.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_library_ask.py](../../../../../../../../tests/test_library_ask.py) — cross-boundary name contract: references uniquely owned exported name `GROUP_ORDER`; it does **not** directly execute this source module.
- [tests/test_roles_judges.py](../../../../../../../../tests/test_roles_judges.py) — cross-boundary name contract: references uniquely owned exported name `GROUP_ORDER`; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/search/model.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/search/model.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

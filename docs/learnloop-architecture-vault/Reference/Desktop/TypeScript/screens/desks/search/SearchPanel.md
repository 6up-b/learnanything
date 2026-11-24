---
title: "Desktop module · src/screens/desks/search/SearchPanel.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.search.SearchPanel"
language: "TypeScript"
area: "TypeScript/screens/desks/search"
source_path: "apps/learnloop-tauri/src/screens/desks/search/SearchPanel.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/search/SearchPanel.tsx"
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

# `src/screens/desks/search/SearchPanel.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/search/_area|TypeScript/screens/desks/search]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `SearchPanel` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/search/SearchPanel.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/search/SearchPanel.tsx) |
| Source lines | 238 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/search/_area|TypeScript/screens/desks/search]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/search/SearchPanel|src/screens/desks/search/SearchPanel.tsx]]

## Public API

- `export interface SearchApi` — interface, line 13
- `export const SEARCH_DEBOUNCE_MS = 120` — const, line 19
- `export const SEARCH_CLOSE_MS = 140` — const, line 21
- `export interface SearchPanelProps` — interface, line 23
- `export function SearchPanel(` — function, line 40

## Internal implementation anchors

- `const inputRef = useRef<HTMLInputElement | null>(null)` — const, line 52
- `const searchSeq = useRef(0)` — const, line 53
- `const stopMeaning = useRef<(()` — const, line 54
- `const trimmed = query.trim()` — const, line 63
- `const seq = ++searchSeq.current` — const, line 64
- `const handle = timers.set(()` — const, line 78
- `const jobId = found.meaning.jobId` — const, line 86
- `const groups = useMemo( ()` — const, line 123
- `const rows = useMemo(()` — const, line 127
- `const current = rows[Math.min(selected, rows.length - 1)] ?? null` — const, line 128
- `const rowEls = useRef(new Map<string, HTMLElement>())` — const, line 131
- `const listRef = useRef<HTMLDivElement | null>(null)` — const, line 132
- `const element = current ? rowEls.current.get(current.key) : null` — const, line 135
- `const close = ()` — const, line 144
- `const choose = (row: SearchRow | null)` — const, line 154
- `const onKeyDown = (event: React.KeyboardEvent)` — const, line 161
- `const group = groups.find((each)` — const, line 177
- `const note = meaningNote(words, meaningUnavailable)` — const, line 182
- `const motion = reducedMotion ? " still" : ""` — const, line 183
- `const index = rows.findIndex((each)` — const, line 215

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `SearchApi`, `SearchPanel`; references `SearchApi`, `SearchPanel`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `SearchEverythingDto`, `SearchEverythingInput`, `SearchGroupDto`, `SearchJobDto`
- [[Reference/Desktop/TypeScript/api/poller|src/api/poller.ts]] — import-or-re-export; imports `Poller`
- [[Reference/Desktop/TypeScript/screens/desks/keys/router|src/screens/desks/keys/router.ts]] — import-or-re-export; imports `Timers`
- [[Reference/Desktop/TypeScript/screens/desks/search/model|src/screens/desks/search/model.ts]] — import-or-re-export; imports `OpenWindow`, `SearchRow`, `meaningNote`, `selectableRows`, `shownGroups`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/search/SearchPanel.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/search/SearchPanel.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/search/SearchPanel.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/search/SearchPanel.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/screens/reader/CompareScope.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.CompareScope"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/CompareScope.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/CompareScope.tsx"
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

# `src/screens/reader/CompareScope.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `CompareScope` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/CompareScope.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/CompareScope.tsx) |
| Source lines | 507 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/CompareScope|src/screens/reader/CompareScope.tsx]]

## Public API

- `export function shownBooks(chips: ScopeChips, table: CompareTableDto | null): LibraryBookDto[]` — function, line 73
- `export function PeekPanel(` — function, line 91
- `export function AddBook(` — function, line 117
- `export function ScopeLine(` — function, line 195
- `export function RefineBox(` — function, line 243
- `export function CompareScopeView(` — function, line 302
- `export function useCompareControls(ctl: LibraryAskController)` — function, line 333
- `export type CompareControls = ReturnType<typeof useCompareControls>` — type, line 363
- `export function CompareScopeBody(` — function, line 367

## Internal implementation anchors

- `const linkStyle =` — const, line 36
- `const chipStyle =` — const, line 48
- `const headStyle =` — const, line 59
- `function leftOut(dropped: Array<Record<string, unknown>>): Array<[string, number]>` — function, line 62
- `const counts = new Map<string, number>()` — const, line 63
- `const reason = String(pin.reason ?? "not available")` — const, line 65
- `const books: LibraryBookDto[] = []` — const, line 77
- `function clipText(text: string, limit = 700): string` — function, line 85
- `const flat = text.split(/\s+/).join(" ").trim()` — const, line 86
- `const view = peek.view` — const, line 96
- `const inputRef = useRef<HTMLInputElement | null>(null)` — const, line 134
- `const words = text.trim().toLowerCase()` — const, line 139
- `const matches = library .filter((book)` — const, line 140
- `const add = (book: LibraryBookDto | undefined)` — const, line 151
- `const books = shownBooks(chips, table)` — const, line 204
- `const chosen = books.map((book)` — const, line 205
- `const anchorSource = chips.anchored ? table?.rows.find((row)` — const, line 207
- `const offer = library.filter((book)` — const, line 208
- `const inputRef = useRef<HTMLInputElement | null>(null)` — const, line 245
- `const refine = ctl.state?.refine` — const, line 249
- `const limit = ctl.state?.viewLimit ?? null` — const, line 250
- `const controls = useCompareControls(ctl)` — const, line 312
- `const state = ctl.state` — const, line 313
- `const table = ctl.state?.chips ? ctl.state.compare.value : null` — const, line 338
- `const onKeyDown = (event: ReactKeyboardEvent<HTMLElement>)` — const, line 339
- `const target = event.target as HTMLElement` — const, line 340
- `const typing = Boolean(target.closest("input, textarea, select"))` — const, line 341
- `const own = useCompareControls(ctl)` — const, line 380
- `const hosted = controls !== undefined` — const, line 381
- `const state = ctl.state` — const, line 383
- `const table = state.compare.value` — const, line 385
- `const previous = state.previous ?? []` — const, line 386
- `const earlier = previous[previous.length - 1] ?? null` — const, line 387
- `const tutor = state.tutorBasis === "comparison" ? state.tutor : null` — const, line 389
- `const reword = onReword && state.chips.words !== null ? ()` — const, line 390
- `const words = ctl.reword()` — const, line 391

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]] — import-or-re-export: `CompareScopeBody`, `CompareScopeView`, `PeekPanel`; references `CompareScopeBody`, `CompareScopeView`, `PeekPanel`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CompareTableDto`, `LibraryBookDto`, `ProposedItemDto`, `SpanViewDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/reader/CompareKeep|src/screens/reader/CompareKeep.tsx]] — import-or-re-export; imports `CompareKeep`
- [[Reference/Desktop/TypeScript/screens/reader/ModelActionState|src/screens/reader/ModelActionState.tsx]] — import-or-re-export; imports `ModelActionState`
- [[Reference/Desktop/TypeScript/screens/reader/useLibraryAsk|src/screens/reader/useLibraryAsk.ts]] — import-or-re-export; imports `LIBRARY_COPY`, `LibraryAskController`, `SCOPE_COPY`, `ScopeChips`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `MeaningLabel`, `ModelVoice`, `SourceVoice`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

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

1. Modify [apps/learnloop-tauri/src/screens/reader/CompareScope.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/CompareScope.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/screens/reader/FindSection.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.FindSection"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/FindSection.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/FindSection.tsx"
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

# `src/screens/reader/FindSection.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `FindSection` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/FindSection.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/FindSection.tsx) |
| Source lines | 478 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/FindSection|src/screens/reader/FindSection.tsx]]

## Public API

- `export const FIND_COPY =` — const, line 45
- `export interface FindSectionOrigin` — interface, line 71
- `export interface FindSectionProps` — interface, line 78
- `export function sectionShort(title: string): string` — function, line 108
- `export function bookShort(title: string): string` — function, line 115
- `export interface PeekCrumb` — interface, line 121
- `export function peekCrumb(hit: Pick<CorrespondentSectionDto, "sourceTitle" | "title">): PeekCrumb` — function, line 125
- `export function hitKey(hit: Pick<CorrespondentSectionDto, "extractionId" | "sectionId">): string` — function, line 129
- `export function newOperationId(): string` — function, line 134
- `export function FindSection(` — function, line 145

## Internal implementation anchors

- `type Pressed = |` — type, line 96
- `interface Peek` — interface, line 101
- `const trimmed = title.trim().replace(/^(section|chapter|§)\s*/i, "")` — const, line 109
- `const match = /^([0-9]+(?:[.\-–][0-9A-Za-z]+)*|[A-Z](?:\.[0-9]+)+)(?=[\s.:)]|$)/.exec(trimmed)` — const, line 110
- `const head = title.split(/\s[:—–-]\s|:\s/)[0]?.trim() || title.trim()` — const, line 116
- `const id = globalThis.crypto?.randomUUID?.() ?? `$` — const, line 135
- `const LINK: CSSProperties =` — const, line 139
- `const HEAD: CSSProperties =` — const, line 143
- `const sectionId = section?.id ?? null` — const, line 148
- `const lineRefs = useRef<Map<string, HTMLButtonElement>>(new Map())` — const, line 157
- `const token = useRef(0)` — const, line 160
- `const search = useRef(0)` — const, line 161
- `const pendingOps = useRef<Map<string, string>>(new Map())` — const, line 164
- `const mine = ++token.current` — const, line 167
- `const press = useCallback(()` — const, line 190
- `const mine = token.current` — const, line 192
- `const searching = ++search.current` — const, line 193
- `const live = ()` — const, line 194
- `const fold = useCallback(()` — const, line 211
- `const view = pressed?.phase === "landed" ? pressed.view : null` — const, line 218
- `const sources = (view?.search?.sources ?? []).map((source)` — const, line 219
- `const lines = sources.flatMap((source)` — const, line 222
- `const liveLines = lines.filter((hit)` — const, line 223
- `const focusLine = (key: string)` — const, line 225
- `const openPeek = useCallback(async (hit: CorrespondentSectionDto)` — const, line 227
- `const key = hitKey(hit)` — const, line 228
- `const mine = token.current` — const, line 230
- `const closePeek = useCallback(()` — const, line 245
- `const key = peek?.key` — const, line 246
- `const peekChange = useRef(onPeekChange)` — const, line 253
- `const seenClose = useRef(closePeekToken)` — const, line 259
- `const goThere = useCallback((hit: CorrespondentSectionDto)` — const, line 266
- `const sideBySide = useCallback((hit: CorrespondentSectionDto)` — const, line 272
- `const runOperation = useCallback(async (key: string, act: string, request: (operationId: string)` — const, line 280
- `const mine = token.current` — const, line 282
- `const opKey = `$` — const, line 283
- `const operationId = pendingOps.current.get(opKey) ?? newOperationId()` — const, line 284
- `const notAbout = useCallback(async (hit: CorrespondentSectionDto)` — const, line 300
- `const key = hitKey(hit)` — const, line 302
- `let recorded: string | null = null` — let, line 303
- `const operationId = recorded` — const, line 310
- `const undo = useCallback(async (key: string)` — const, line 317
- `const entry = dismissed.get(key)` — const, line 318
- `const next = new Map(current)` — const, line 325
- `const onListKey = (event: KeyboardEvent<HTMLDivElement>)` — const, line 332
- `const target = event.target as HTMLElement` — const, line 335
- `const keyOf = target.closest<HTMLElement>("[data-find-line]")?.dataset.findLine ?? null` — const, line 336
- `const index = keyOf ? liveLines.findIndex((hit)` — const, line 337
- `const hit = index >= 0 && target.dataset.findTitle !== undefined ? liveLines[index] : null` — const, line 340
- `const consume = ()` — const, line 341
- `const next = index < 0 ? 0 : (index + (event.key === "ArrowDown" ? 1 : -1) + liveLines.length) % liveLines.length` — const, line 348
- `const key = hitKey(hit)` — const, line 400
- `const gone = dismissed.get(key)` — const, line 401
- `const peeking = peek?.key === key` — const, line 412

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `FindSection`; references `FindSection`
- [[Reference/Desktop/TypeScript/screens/reader/AlsoInBooks|src/screens/reader/AlsoInBooks.tsx]] — import-or-re-export: `FIND_COPY`, `FindSectionOrigin`, `PeekCrumb`, `bookShort`, `hitKey`, `newOperationId`, `peekCrumb`, `sectionShort`; references `FIND_COPY`, `FindSectionOrigin`, `PeekCrumb`, `bookShort`, `hitKey`, `newOperationId`, `peekCrumb`, `sectionShort`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CorrespondentPeekDto`, `CorrespondentSectionDto`, `CorrespondentsDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/correspondenceEvents|src/screens/reader/correspondenceEvents.ts]] — import-or-re-export; imports `logCorrespondentAct`
- [[Reference/Desktop/TypeScript/screens/reader/correspondentsRead|src/screens/reader/correspondentsRead.ts]] — import-or-re-export; imports `quietCorrespondents`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `clip`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `MeaningLabel`, `SourceVoice`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/sideBySideReader.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/sideBySideCorrespondence.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideCorrespondence.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/findSectionSideBySide.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/findSectionSideBySide.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/findSectionReader.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/findSectionReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/findSectionByPoint.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/findSectionByPoint.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/findSection.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/findSection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/alsoInBooksReader.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/alsoInBooksReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/FindSection.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/FindSection.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

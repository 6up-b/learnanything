---
title: "Desktop module · src/screens/reader/AlsoInBooks.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.AlsoInBooks"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/AlsoInBooks.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/AlsoInBooks.tsx"
source_commit: "952a54d9d4963ef00dd1d49410b4a92eba28f51d"
source_commit_timestamp: "2026-10-31T22:15:39-04:00"
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

# `src/screens/reader/AlsoInBooks.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `AlsoInBooks` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/AlsoInBooks.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/AlsoInBooks.tsx) |
| Source lines | 732 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `952a54d9d4963ef00dd1d49410b4a92eba28f51d` |
| Commit timestamp | `2026-10-31T22:15:39-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/AlsoInBooks|src/screens/reader/AlsoInBooks.tsx]]

## Public API

- `export const ALSO_COPY =` — const, line 44
- `export function keptWords(kept: CorrespondentKeptDto[] | undefined): string | null` — function, line 80
- `export interface AlsoLine` — interface, line 86
- `export interface AlsoGroup` — interface, line 96
- `export function alsoGroups(view: CorrespondentsDto | null): AlsoGroup[]` — function, line 103
- `export function roleWords(roles: string[] | undefined): string | null` — function, line 131
- `export function notAboutAct(line: AlsoLine): string` — function, line 137
- `export function lineNames(lines: AlsoLine[]):` — function, line 142
- `export type AlsoPeekCrumb = PeekCrumb` — type, line 157
- `export interface AlsoInBooksProps` — interface, line 159
- `export function AlsoInBooks(` — function, line 207

## Internal implementation anchors

- `const LINE_CHARS = 46` — const, line 76
- `const relations = [...new Set(kept.flatMap((entry)` — const, line 82
- `const titles = new Map(view.learningObjects.map((group)` — const, line 105
- `const seen = new Set<string>()` — const, line 106
- `const groups: AlsoGroup[] = []` — const, line 107
- `const lines: AlsoLine[] = []` — const, line 109
- `const key = hitKey(hit)` — const, line 114
- `const others = (hit.alsoLearningObjectIds ?? []).filter((id)` — const, line 117
- `const words = [...new Set((roles ?? []).map((role)` — const, line 132
- `const names: string[] = []` — const, line 143
- `let used = 0` — let, line 144
- `const name = `$` — const, line 146
- `const cost = name.length + (names.length > 0 ? 2 : 0)` — const, line 147
- `interface Peek` — interface, line 184
- `interface AlsoAbout` — interface, line 190
- `const LINK: CSSProperties =` — const, line 197
- `const DIM_LINE: CSSProperties =` — const, line 201
- `const HEAD: CSSProperties =` — const, line 205
- `const sectionId = section?.id ?? null` — const, line 211
- `const lineRefs = useRef<Map<string, HTMLButtonElement>>(new Map())` — const, line 223
- `const collapsedRef = useRef<HTMLButtonElement | null>(null)` — const, line 224
- `const token = useRef(0)` — const, line 226
- `const pendingOps = useRef<Map<string, string>>(new Map())` — const, line 227
- `const peekChange = useRef(onPeekChange)` — const, line 228
- `const read = useCallback((mine: number, id: string)` — const, line 231
- `const mine = ++token.current` — const, line 243
- `const view = answer && answer.sectionId === sectionId ? answer.view : null` — const, line 263
- `const groups = useMemo(()` — const, line 264
- `const lines = useMemo(()` — const, line 265
- `const liveLines = lines.filter((line)` — const, line 266
- `const listed = useMemo(()` — const, line 270
- `const orphans = [...gone.entries()].filter(([key])` — const, line 271
- `const visible = Boolean(section) && !hidden && (lines.length > 0 || gone.size > 0)` — const, line 272
- `const available = visible && liveLines.length > 0` — const, line 281
- `const availableChange = useRef(onAvailableChange)` — const, line 282
- `const focusLine = (key: string)` — const, line 289
- `const pendingFocus = useRef<string | null>(null)` — const, line 292
- `const wanted = pendingFocus.current` — const, line 294
- `const node = wanted === "" ? collapsedRef.current : lineRefs.current.get(wanted)` — const, line 296
- `const seenExpand = useRef(expandToken)` — const, line 304
- `const closePeek = useCallback(()` — const, line 315
- `const key = peek?.key` — const, line 316
- `const seenClose = useRef(closePeekToken)` — const, line 321
- `const fold = useCallback(()` — const, line 328
- `const openPeek = useCallback(async (line: AlsoLine)` — const, line 337
- `const mine = token.current` — const, line 340
- `const goThere = useCallback((hit: CorrespondentSectionDto)` — const, line 355
- `const sideBySide = useCallback((hit: CorrespondentSectionDto)` — const, line 361
- `const runOperation = useCallback(async (key: string, act: string, request: (operationId: string)` — const, line 369
- `const mine = token.current` — const, line 371
- `const opKey = `$` — const, line 372
- `const operationId = pendingOps.current.get(opKey) ?? newOperationId()` — const, line 373
- `const notAbout = useCallback(async (line: AlsoLine)` — const, line 391
- `let recorded: string | null = null` — let, line 393
- `const operationId = recorded` — const, line 402
- `const title = groups.find((group)` — const, line 404
- `const undo = useCallback(async (key: string)` — const, line 410
- `const entry = gone.get(key)` — const, line 411
- `const next = new Map(current)` — const, line 418
- `const sendAlsoAbout = useCallback(async (line: AlsoLine, text: string)` — const, line 427
- `const words = text.trim()` — const, line 428
- `const mine = token.current` — const, line 430
- `const result = await api.curriculumAlsoAbout(` — const, line 434
- `const message = result.status === "corrected" ? `$` — const, line 436
- `const onListKey = (event: KeyboardEvent<HTMLDivElement>)` — const, line 451
- `const target = event.target as HTMLElement` — const, line 454
- `const keyOf = target.closest<HTMLElement>("[data-also-line]")?.dataset.alsoLine ?? null` — const, line 455
- `const index = keyOf ? liveLines.findIndex((line)` — const, line 456
- `const line = index >= 0 && target.dataset.alsoTitle !== undefined ? liveLines[index] : null` — const, line 459
- `const consume = ()` — const, line 460
- `const next = index < 0 ? 0 : (index + (event.key === "ArrowDown" ? 1 : -1) + liveLines.length) % liveLines.length` — const, line 467
- `const back = menuKey ?? alsoAbout?.key ?? null` — const, line 485
- `const blockMenuView = blockMenu ? ( <span role="menu" aria-label=` — const, line 496
- `const blockMore = ( <button type="button" aria-label=` — const, line 502
- `const goneRow = (key: string, entry:` — const, line 536
- `const peekRoles = peek ? roleWords(peek.hit.roles) : null` — const, line 547
- `const groupIds = new Set(groups.map((group)` — const, line 548
- `const strayGroups: Array<` — const, line 550
- `let stray = strayGroups.find((group)` — let, line 553
- `const keyHints = [ ALSO_COPY.keys.peek, ALSO_COPY.keys.go, ...(onSideBySide ? [ALSO_COPY.keys.side] : []), ...(onCompare ? [ALSO_COPY.keys.compare] : []), ALSO_COPY.keys.fix, ].join(" · ")` — const, line 561
- `const removed = gone.get(key)` — const, line 584
- `const focused = focusedKey === key` — const, line 586
- `const peeking = peek?.key === key` — const, line 587
- `const kept = keptWords(hit.kept)` — const, line 588
- `const treatment = hit.linkedByYou ? ALSO_COPY.linkedByYou : hit.treatmentWords ?? (hit.treatment ? ALSO_COPY.treatment[hit.treatment] ?? null : null)` — const, line 589
- `const box = alsoAbout?.key === key ? alsoAbout : null` — const, line 591

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `AlsoInBooks`, `AlsoPeekCrumb`; references `AlsoInBooks`, `AlsoPeekCrumb`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CorrespondentKeptDto`, `CorrespondentPeekDto`, `CorrespondentSectionDto`, `CorrespondentsDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/FindSection|src/screens/reader/FindSection.tsx]] — import-or-re-export; imports `FIND_COPY`, `FindSectionOrigin`, `PeekCrumb`, `bookShort`, `hitKey`, `newOperationId`, `peekCrumb`, `sectionShort`
- [[Reference/Desktop/TypeScript/screens/reader/correspondenceEvents|src/screens/reader/correspondenceEvents.ts]] — import-or-re-export; imports `logCorrespondentAct`
- [[Reference/Desktop/TypeScript/screens/reader/correspondentsRead|src/screens/reader/correspondentsRead.ts]] — import-or-re-export; imports `quietCorrespondents`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `clip`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `MeaningLabel`, `SourceVoice`, `SpokenOnly`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/sideBySideCorrespondence.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideCorrespondence.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/alsoInBooksReader.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/alsoInBooksReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/alsoInBooks.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/alsoInBooks.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/AlsoInBooks.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/AlsoInBooks.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

---
title: "Desktop module · src/screens/reader/ReadingPathCard.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.ReadingPathCard"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/ReadingPathCard.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/ReadingPathCard.tsx"
source_commit: "0c5bc9546b622e4d87b7075f53b026c74b9e5462"
source_commit_timestamp: "2026-11-01T02:25:38-05:00"
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

# `src/screens/reader/ReadingPathCard.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `ReadingPathCard` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/ReadingPathCard.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/ReadingPathCard.tsx) |
| Source lines | 268 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `0c5bc9546b622e4d87b7075f53b026c74b9e5462` |
| Commit timestamp | `2026-11-01T02:25:38-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/ReadingPathCard|src/screens/reader/ReadingPathCard.tsx]]

## Public API

- `export interface ReadingPathCardProps` — interface, line 27
- `export function ReadingPathCard(` — function, line 45

## Internal implementation anchors

- `const LINK =` — const, line 22
- `const jump = (spanId: string, sectionId: string)` — const, line 46
- `const shown = useRef(extractionId)` — const, line 51
- `const cardRef = useRef<HTMLDivElement | null>(null)` — const, line 52
- `const read = useCallback(async (params:` — const, line 54
- `const asked = extractionId` — const, line 55
- `const result = await api.readerReadingPath(` — const, line 57
- `const timer = window.setTimeout(()` — const, line 75
- `const refreshedFor = useRef(refreshKey)` — const, line 87
- `const timer = window.setTimeout(()` — const, line 91
- `const chooseDepth = async (depth: ReadingPathDepth)` — const, line 95
- `const result = await api.readerReadingPathSetDepth(` — const, line 98
- `const choose = async (section: ReadingPathSectionDto, choice: ReadingPathChoice)` — const, line 110
- `const result = await api.readerReadingPathOverride(` — const, line 114
- `const askDepth = path.status === "ask_depth" || choosing` — const, line 134
- `const exercises = exercisesWorthTrying(path)` — const, line 135
- `function SectionRow(` — function, line 220
- `const offered = offeredChoice(section)` — const, line 230

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `ReadingPathCard`; references `ReadingPathCard`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReadingPathChoice`, `ReadingPathDepth`, `ReadingPathDto`, `ReadingPathExerciseDto`, `ReadingPathSectionDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `FONT_MONO`, `Faint`, `Pill`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/readingPath|src/screens/reader/readingPath.ts]] — import-or-re-export; imports `COPY`, `READING_PATH_POLL_MS`, `READING_PATH_REFRESH_MS`, `depthSourceLine`, `exercisesWorthTrying`, `offeredChoice`, `pathHeading`, `reasonIsModels`, `shouldPoll`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `MeaningLabel`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/readingPathsRefresh.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readingPathsRefresh.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/ReadingPathCard.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/ReadingPathCard.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/ReadingPathCard.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/ReadingPathCard.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

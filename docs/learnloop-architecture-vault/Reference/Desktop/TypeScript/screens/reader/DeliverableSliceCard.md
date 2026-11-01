---
title: "Desktop module · src/screens/reader/DeliverableSliceCard.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.DeliverableSliceCard"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/DeliverableSliceCard.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/DeliverableSliceCard.tsx"
source_commit: "1bd537ae4527bb8d6bd5360ec8560b6947c7827c"
source_commit_timestamp: "2026-10-31T16:21:48-04:00"
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

# `src/screens/reader/DeliverableSliceCard.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `DeliverableSliceCard` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/DeliverableSliceCard.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/DeliverableSliceCard.tsx) |
| Source lines | 402 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `staged-or-mixed` |
| Source commit | `1bd537ae4527bb8d6bd5360ec8560b6947c7827c` |
| Commit timestamp | `2026-10-31T16:21:48-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/DeliverableSliceCard|src/screens/reader/DeliverableSliceCard.tsx]]

## Public API

- `export interface GuidePathSlotProps` — interface, line 38
- `export function GuidePathSlot(` — function, line 49
- `export interface DeliverableSliceCardProps` — interface, line 127
- `export function DeliverableSliceCard(` — function, line 136

## Internal implementation anchors

- `const LINK =` — const, line 31
- `const QUIET_CODES = new Set(["curriculum_disabled", "reader_disabled"])` — const, line 35
- `const NONE: DeliverableSliceDto =` — const, line 36
- `const shown = useRef(extractionId)` — const, line 53
- `const read = useCallback(async (params:` — const, line 55
- `const asked = extractionId` — const, line 56
- `const result = await api.curriculumGuideSlice(` — const, line 58
- `const code = getCommandError(error)?.code` — const, line 66
- `const timer = window.setTimeout(()` — const, line 80
- `const refreshedFor = useRef(refreshKey)` — const, line 84
- `const timer = window.setTimeout(()` — const, line 88
- `const goalId = slice.goal?.id ?? ""` — const, line 145
- `const pathNotes = usePathNotes(goalId || null, slice.status === "ready" || slice.status === "stale")` — const, line 147
- `const act = async (work: ()` — const, line 149
- `const toggleScope = async ()` — const, line 161
- `const scopeChanged = (next: DeliverableScopeDto)` — const, line 173
- `const chooseDepth = (depth: ReadingPathDepth)` — const, line 178
- `const choose = (line: DeliverableLineDto, choice: DeliverablePathChoice, ref?: string)` — const, line 184
- `const notWhatINeed = (line: DeliverableLineDto, text: string)` — const, line 188
- `const out = await api.curriculumSetScope(` — const, line 189
- `const amIReady = async ()` — const, line 200
- `const out = await api.curriculumReadyCheck(` — const, line 203
- `const askDepth = slice.status === "ask_depth" || choosing` — const, line 219
- `const lines = slice.lines ?? []` — const, line 220
- `const notNeeded = slice.notNeeded ?? []` — const, line 221
- `function LineRow(` — function, line 313
- `const offered = offeredChoices(line)` — const, line 324
- `const onPath = line.effectiveLabel === "core" || line.effectiveLabel === "prerequisite"` — const, line 325
- `const crossed = line.effectiveLabel === "skipped" || line.effectiveLabel === "check_pending"` — const, line 326
- `function ReadyLines(` — function, line 388

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `GuidePathSlot`; references `GuidePathSlot`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DeliverableLineDto`, `DeliverablePathChoice`, `DeliverableReadyDto`, `DeliverableScopeDto`, `DeliverableSliceDto`, `NoteLinkDto`, `ReadingPathDepth`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `FONT_MONO`, `Faint`, `Pill`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/reader/DeliverableScope|src/screens/reader/DeliverableScope.tsx]] — import-or-re-export; imports `DeliverableEntry`, `DeliverableScopePanel`, `scopeNotice`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderNotes|src/screens/reader/ReaderNotes.tsx]] — import-or-re-export; imports `PathLineNotes`, `usePathNotes`
- [[Reference/Desktop/TypeScript/screens/reader/deliverableSlice|src/screens/reader/deliverableSlice.ts]] — import-or-re-export; imports `COPY`, `DELIVERABLE_POLL_MS`, `offeredChoices`, `sectionMarker`, `sectionRef`, `shouldPollSlice`, `sliceHeading`, `sliceShown`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `MeaningLabel`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/DeliverableSliceCard.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/DeliverableSliceCard.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_deliverable_codex_review.py](../../../../../../../tests/test_deliverable_codex_review.py) — cross-boundary name contract: references uniquely owned exported name `DeliverableSliceCard`; it does **not** directly execute this source module.
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

1. Modify [apps/learnloop-tauri/src/screens/reader/DeliverableSliceCard.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/DeliverableSliceCard.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

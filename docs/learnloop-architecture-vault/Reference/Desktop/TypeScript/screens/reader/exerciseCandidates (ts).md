---
title: "Desktop module · src/screens/reader/exerciseCandidates.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.exerciseCandidates"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/exerciseCandidates.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/exerciseCandidates.ts"
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

# `src/screens/reader/exerciseCandidates.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `EXERCISE_COPY`, `ExerciseCandidate`, `ReaderWorkbenchExercise`, `proposalKeys` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/exerciseCandidates.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/exerciseCandidates.ts) |
| Source lines | 208 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/exerciseCandidates (ts)|src/screens/reader/exerciseCandidates.ts]]

## Public API

- `export const EXERCISE_COPY =` — const, line 23
- `export interface ExerciseCandidate` — interface, line 39
- `export interface ReaderWorkbenchExercise` — interface, line 64
- `export function proposalKeys(result: FindPracticeResultDto): Array<` — function, line 80
- `export function fromProposal(result: FindPracticeResultDto, view: ExerciseCandidatesDto | null): ExerciseCandidate[]` — function, line 86
- `export function fromFallback(found: FindExercisesDto | null): ExerciseCandidate[]` — function, line 110
- `export function exerciseLocator(candidate: Pick<ExerciseCandidate, "sourceTitle" | "page" | "label">): string` — function, line 129
- `export function keyStatusLine(keyStatus?: string | null, keyLabel?: string | null): string` — function, line 137
- `export function exerciseOpenRequest(candidate: ExerciseCandidate): ReaderWorkbenchExercise` — function, line 164
- `export function practiceFromToolRun(run: SourceToolRunDto): FindPracticeResultDto` — function, line 186

## Internal implementation anchors

- `const viewed = new Map(view.candidates.map((candidate)` — const, line 88
- `const shown: ExerciseCandidate[] = []` — const, line 89
- `const seen = viewed.get(exercise.key)` — const, line 91
- `const label = candidate.label && !/p\.\s*\d/.test(candidate.label) ? candidate.label : null` — const, line 130
- `const lead = EXERCISE_COPY.verbatim` — const, line 138
- `const entry = candidate.exposure.exposed ? "work_through" : "practice_this"` — const, line 165
- `const base =` — const, line 166

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `ExerciseCandidate`, `ReaderWorkbenchExercise`, `exerciseOpenRequest`; references `ExerciseCandidate`, `ReaderWorkbenchExercise`, `exerciseOpenRequest`
- [[Reference/Desktop/TypeScript/screens/reader/ExerciseCandidates (tsx)|src/screens/reader/ExerciseCandidates.tsx]] — import-or-re-export: `EXERCISE_COPY`, `ExerciseCandidate`, `exerciseLocator`, `keyStatusLine`; references `EXERCISE_COPY`, `ExerciseCandidate`, `exerciseLocator`, `keyStatusLine`
- [[Reference/Desktop/TypeScript/screens/reader/ProposalExercises|src/screens/reader/ProposalExercises.tsx]] — import-or-re-export: `EXERCISE_COPY`, `ExerciseCandidate`; references `EXERCISE_COPY`, `ExerciseCandidate`
- [[Reference/Desktop/TypeScript/screens/reader/TutorOffers|src/screens/reader/TutorOffers.tsx]] — import-or-re-export: `practiceFromToolRun`; references `practiceFromToolRun`
- [[Reference/Desktop/TypeScript/screens/reader/useLibraryExercises|src/screens/reader/useLibraryExercises.ts]] — import-or-re-export: `ExerciseCandidate`, `fromFallback`, `fromProposal`, `proposalKeys`; references `ExerciseCandidate`, `fromFallback`, `fromProposal`, `proposalKeys`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderWorkbench|src/screens/reader/useReaderWorkbench.ts]] — import-or-re-export: `ReaderWorkbenchExercise`; references `ReaderWorkbenchExercise`
- [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] — import-or-re-export: `EXERCISE_COPY`, `keyStatusLine`; references `EXERCISE_COPY`, `keyStatusLine`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ExerciseCandidatesDto`, `ExerciseExposureDto`, `ExercisePickDto`, `FindExercisesDto`, `FindPracticeResultDto`, `ReaderImportExerciseInput`, `SourceToolRunDto`, `WorkbenchEntry`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/tutorExercises.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/tutorExercises.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/readerWorkbenchQueue.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readerWorkbenchQueue.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/readerWorkbenchExercise.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readerWorkbenchExercise.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/exerciseCandidates.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/exerciseCandidates.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/exerciseCandidates.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/exerciseCandidates.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

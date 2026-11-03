---
title: "Desktop module · src/screens/reader/voices.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.voices"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/voices.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/voices.tsx"
source_commit: "84f52bee3bc94c6ecb2c09f8561be166c674c984"
source_commit_timestamp: "2026-10-13T03:43:59-04:00"
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

# `src/screens/reader/voices.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `voices` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/voices.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/voices.tsx) |
| Source lines | 172 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `84f52bee3bc94c6ecb2c09f8561be166c674c984` |
| Commit timestamp | `2026-10-13T03:43:59-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/feedback/CompareMethods|src/screens/feedback/CompareMethods.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]]

## Public API

- `export type ReaderVoice = "source" | "model" | "learner"` — type, line 16
- `export function SpokenOnly(` — function, line 31
- `export function MeaningLabel(` — function, line 36
- `export function SourceVoice(` — function, line 83
- `export function ModelVoice(` — function, line 99
- `export function LearnerVoice(` — function, line 116
- `export function LearnerQuote(` — function, line 121
- `export type EvidenceStatus = "untested" | "with_help" | "demonstrated"` — type, line 133
- `export function EvidenceMarker(` — function, line 142
- `export type CheckStatus = "checked" | "checked_not_following" | "model_reading" | "questionable" | "not_checked"` — type, line 152
- `export function CheckMarker(` — function, line 163

## Internal implementation anchors

- `const VISUALLY_HIDDEN: CSSProperties =` — const, line 18
- `const RULES: Record<ReaderVoice, CSSProperties> =` — const, line 44
- `const GLYPHS: Record<ReaderVoice, string> =` — const, line 50
- `function spokenPrefix(voice: ReaderVoice, locator?: string | null): string` — function, line 52
- `function VoiceBlock(` — function, line 58
- `const label = [source || "from the book", locator].filter(Boolean).join(" · ")` — const, line 94
- `const label = `$` — const, line 111
- `const EVIDENCE: Record<EvidenceStatus,` — const, line 135
- `const marker = EVIDENCE[status]` — const, line 143
- `const CHECKS: Record<CheckStatus,` — const, line 154
- `const marker = CHECKS[status]` — const, line 164

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/feedback/CompareMethods|src/screens/feedback/CompareMethods.tsx]] — import-or-re-export: `LearnerVoice`, `MeaningLabel`, `ModelVoice`, `SourceVoice`; references `LearnerVoice`, `MeaningLabel`, `ModelVoice`, `SourceVoice`
- [[Reference/Desktop/TypeScript/screens/reader/ActiveReadingCard|src/screens/reader/ActiveReadingCard.tsx]] — import-or-re-export: `LearnerVoice`, `MeaningLabel`, `ModelVoice`, `SourceVoice`; references `LearnerVoice`, `MeaningLabel`, `ModelVoice`, `SourceVoice`
- [[Reference/Desktop/TypeScript/screens/reader/AlsoInBooks|src/screens/reader/AlsoInBooks.tsx]] — import-or-re-export: `MeaningLabel`, `SourceVoice`, `SpokenOnly`; references `MeaningLabel`, `SourceVoice`, `SpokenOnly`
- [[Reference/Desktop/TypeScript/screens/reader/AskRail|src/screens/reader/AskRail.tsx]] — import-or-re-export: `LearnerQuote`, `LearnerVoice`, `MeaningLabel`; references `LearnerQuote`, `LearnerVoice`, `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/CompareKeep|src/screens/reader/CompareKeep.tsx]] — import-or-re-export: `LearnerVoice`, `MeaningLabel`, `ModelVoice`; references `LearnerVoice`, `MeaningLabel`, `ModelVoice`
- [[Reference/Desktop/TypeScript/screens/reader/ComparePointTable|src/screens/reader/ComparePointTable.tsx]] — import-or-re-export: `MeaningLabel`, `SpokenOnly`; references `MeaningLabel`, `SpokenOnly`
- [[Reference/Desktop/TypeScript/screens/reader/CompareScope|src/screens/reader/CompareScope.tsx]] — import-or-re-export: `MeaningLabel`, `ModelVoice`, `SourceVoice`; references `MeaningLabel`, `ModelVoice`, `SourceVoice`
- [[Reference/Desktop/TypeScript/screens/reader/DeliverableSliceCard|src/screens/reader/DeliverableSliceCard.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/DigestNarrative|src/screens/reader/DigestNarrative.tsx]] — import-or-re-export: `MeaningLabel`, `ModelVoice`; references `MeaningLabel`, `ModelVoice`
- [[Reference/Desktop/TypeScript/screens/reader/ExerciseCandidates (tsx)|src/screens/reader/ExerciseCandidates.tsx]] — import-or-re-export: `MeaningLabel`, `SourceVoice`; references `MeaningLabel`, `SourceVoice`
- [[Reference/Desktop/TypeScript/screens/reader/FindSection|src/screens/reader/FindSection.tsx]] — import-or-re-export: `MeaningLabel`, `SourceVoice`; references `MeaningLabel`, `SourceVoice`
- [[Reference/Desktop/TypeScript/screens/reader/GuideRail|src/screens/reader/GuideRail.tsx]] — import-or-re-export: `LearnerVoice`, `MeaningLabel`, `ModelVoice`, `SourceVoice`; references `LearnerVoice`, `MeaningLabel`, `ModelVoice`, `SourceVoice`
- [[Reference/Desktop/TypeScript/screens/reader/HiddenNotesSettings|src/screens/reader/HiddenNotesSettings.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/InquiryQuickCheck|src/screens/reader/InquiryQuickCheck.tsx]] — import-or-re-export: `LearnerVoice`, `MeaningLabel`, `ModelVoice`; references `LearnerVoice`, `MeaningLabel`, `ModelVoice`
- [[Reference/Desktop/TypeScript/screens/reader/IntentBox|src/screens/reader/IntentBox.tsx]] — import-or-re-export: `LearnerQuote`, `MeaningLabel`; references `LearnerQuote`, `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]] — import-or-re-export: `EvidenceMarker`, `MeaningLabel`, `ModelVoice`, `SourceVoice`; references `EvidenceMarker`, `MeaningLabel`, `ModelVoice`, `SourceVoice`
- [[Reference/Desktop/TypeScript/screens/reader/MarginMark|src/screens/reader/MarginMark.tsx]] — import-or-re-export: `LearnerVoice`, `MeaningLabel`, `ModelVoice`; references `LearnerVoice`, `MeaningLabel`, `ModelVoice`
- [[Reference/Desktop/TypeScript/screens/reader/ModelActionState|src/screens/reader/ModelActionState.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/NotesGapsSettings|src/screens/reader/NotesGapsSettings.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/NotesRail|src/screens/reader/NotesRail.tsx]] — import-or-re-export: `MeaningLabel`, `ModelVoice`; references `MeaningLabel`, `ModelVoice`
- [[Reference/Desktop/TypeScript/screens/reader/ProposalExercises|src/screens/reader/ProposalExercises.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderAskBranches|src/screens/reader/ReaderAskBranches.tsx]] — import-or-re-export: `LearnerVoice`, `MeaningLabel`, `SourceVoice`; references `LearnerVoice`, `MeaningLabel`, `SourceVoice`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderCorrespondenceSettings|src/screens/reader/ReaderCorrespondenceSettings.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderCueSettings|src/screens/reader/ReaderCueSettings.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderNotes|src/screens/reader/ReaderNotes.tsx]] — import-or-re-export: `LearnerVoice`, `MeaningLabel`; references `LearnerVoice`, `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/ReadingPathCard|src/screens/reader/ReadingPathCard.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/RecapCard|src/screens/reader/RecapCard.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/ReconnectLine|src/screens/reader/ReconnectLine.tsx]] — import-or-re-export: `LearnerQuote`, `MeaningLabel`; references `LearnerQuote`, `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/ScopeFromPassage|src/screens/reader/ScopeFromPassage.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/SideBySidePane|src/screens/reader/SideBySidePane.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/TutorAnswer|src/screens/reader/TutorAnswer.tsx]] — import-or-re-export: `MeaningLabel`, `ModelVoice`, `SourceVoice`; references `MeaningLabel`, `ModelVoice`, `SourceVoice`
- [[Reference/Desktop/TypeScript/screens/reader/TutorOffers|src/screens/reader/TutorOffers.tsx]] — import-or-re-export: `MeaningLabel`, `ModelVoice`, `SourceVoice`; references `MeaningLabel`, `ModelVoice`, `SourceVoice`
- [[Reference/Desktop/TypeScript/screens/reader/WrapUpPanel|src/screens/reader/WrapUpPanel.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export: `LearnerQuote`, `MeaningLabel`, `ModelVoice`, `SourceVoice`; references `LearnerQuote`, `MeaningLabel`, `ModelVoice`, `SourceVoice`
- [[Reference/Desktop/TypeScript/screens/reader/figures/RichFigure|src/screens/reader/figures/RichFigure.tsx]] — import-or-re-export: `MeaningLabel`, `ModelVoice`; references `MeaningLabel`, `ModelVoice`
- [[Reference/Desktop/TypeScript/screens/reader/figures/figureLabels|src/screens/reader/figures/figureLabels.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] — import-or-re-export: `MeaningLabel`, `ModelVoice`, `SourceVoice`; references `MeaningLabel`, `ModelVoice`, `SourceVoice`
- [[Reference/Desktop/TypeScript/screens/workbench/CheckColumn|src/screens/workbench/CheckColumn.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/workbench/HelpLadder|src/screens/workbench/HelpLadder.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/workbench/RouteExample|src/screens/workbench/RouteExample.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/workbench/StepHints|src/screens/workbench/StepHints.tsx]] — import-or-re-export: `MeaningLabel`, `ModelVoice`; references `MeaningLabel`, `ModelVoice`
- [[Reference/Desktop/TypeScript/screens/workbench/WhereThisGoes|src/screens/workbench/WhereThisGoes.tsx]] — import-or-re-export: `MeaningLabel`; references `MeaningLabel`
- [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] — import-or-re-export: `LearnerVoice`, `MeaningLabel`, `SourceVoice`; references `LearnerVoice`, `MeaningLabel`, `SourceVoice`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/voices.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/voices.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/TutorAnswer.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/TutorAnswer.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_architecture.py](../../../../../../../tests/test_architecture.py) — cross-boundary name contract: references uniquely owned exported name `CheckMarker`; it does **not** directly execute this source module.
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

1. Modify [apps/learnloop-tauri/src/screens/reader/voices.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/voices.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

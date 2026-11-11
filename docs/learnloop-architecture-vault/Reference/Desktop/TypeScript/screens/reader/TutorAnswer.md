---
title: "Desktop module · src/screens/reader/TutorAnswer.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.TutorAnswer"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/TutorAnswer.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/TutorAnswer.tsx"
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

# `src/screens/reader/TutorAnswer.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `TutorAnswer` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/TutorAnswer.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/TutorAnswer.tsx) |
| Source lines | 186 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/AskRail|src/screens/reader/AskRail.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/TutorAnswer|src/screens/reader/TutorAnswer.tsx]]

## Public API

- `export const TUTOR_COPY =` — const, line 23
- `export interface TutorPassageRef` — interface, line 39
- `export interface ExchangeOffers` — interface, line 46
- `export interface TutorRailProps` — interface, line 53
- `export function TutorAnswer(` — function, line 84

## Internal implementation anchors

- `const linkStyle =` — const, line 79
- `const view = tutor ? exchange.tutor ?? null : null` — const, line 88
- `const excerpt = view?.excerpt ?? null` — const, line 98
- `const label = view?.retrieval?.label ?? null` — const, line 99

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/AskRail|src/screens/reader/AskRail.tsx]] — import-or-re-export: `TutorAnswer`, `TutorRailProps`; references `TutorAnswer`, `TutorRailProps`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderAskBranches|src/screens/reader/ReaderAskBranches.tsx]] — import-or-re-export: `ExchangeOffers`, `TutorAnswer`, `TutorRailProps`; references `ExchangeOffers`, `TutorAnswer`, `TutorRailProps`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `TUTOR_COPY`; references `TUTOR_COPY`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `PracticeRequestDto`, `ReaderTutorButtonDto`, `SourceToolRequestDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/reader/ProposalExercises|src/screens/reader/ProposalExercises.tsx]] — import-or-re-export; imports `LibraryExercisesProps`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderAskBranches|src/screens/reader/ReaderAskBranches.tsx]] — import-or-re-export; imports `ReaderExchange`
- [[Reference/Desktop/TypeScript/screens/reader/TutorOffers|src/screens/reader/TutorOffers.tsx]] — import-or-re-export; imports `OfferItem`, `TutorOfferStore`, `TutorOffers`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `MeaningLabel`, `ModelVoice`, `SourceVoice`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/tutorReview.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/tutorReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/TutorAnswer.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/TutorAnswer.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_dialogue_causal_join.py](../../../../../../../tests/test_dialogue_causal_join.py) — cross-boundary name contract: references uniquely owned exported name `TutorAnswer`; it does **not** directly execute this source module.
- [tests/test_e0_review_round1.py](../../../../../../../tests/test_e0_review_round1.py) — cross-boundary name contract: references uniquely owned exported name `TutorAnswer`; it does **not** directly execute this source module.
- [tests/test_e0_review_round2.py](../../../../../../../tests/test_e0_review_round2.py) — cross-boundary name contract: references uniquely owned exported name `TutorAnswer`; it does **not** directly execute this source module.
- [tests/test_field_signal_production_paths.py](../../../../../../../tests/test_field_signal_production_paths.py) — cross-boundary name contract: references uniquely owned exported name `TutorAnswer`; it does **not** directly execute this source module.
- [tests/test_placement_signals.py](../../../../../../../tests/test_placement_signals.py) — cross-boundary name contract: references uniquely owned exported name `TutorAnswer`; it does **not** directly execute this source module.
- [tests/test_question_signal.py](../../../../../../../tests/test_question_signal.py) — cross-boundary name contract: references uniquely owned exported name `TutorAnswer`; it does **not** directly execute this source module.
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

1. Modify [apps/learnloop-tauri/src/screens/reader/TutorAnswer.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/TutorAnswer.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

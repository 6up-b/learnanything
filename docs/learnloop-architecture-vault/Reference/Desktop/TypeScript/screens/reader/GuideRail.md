---
title: "Desktop module · src/screens/reader/GuideRail.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.GuideRail"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/GuideRail.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/GuideRail.tsx"
source_commit: "c1642215eb413a66183f89ba6991707422043f6c"
source_commit_timestamp: "2026-10-31T18:28:19-04:00"
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

# `src/screens/reader/GuideRail.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `GuideRail` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/GuideRail.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/GuideRail.tsx) |
| Source lines | 803 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `c1642215eb413a66183f89ba6991707422043f6c` |
| Commit timestamp | `2026-10-31T18:28:19-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/GuideRail|src/screens/reader/GuideRail.tsx]]

## Public API

- `export const QUESTION_CONTROLS: Array<` — const, line 20
- `export interface GuideRailProps` — interface, line 28
- `export function GuideRail(` — function, line 97
- `export function SectionBoundaryOffer(` — function, line 387
- `export function AuthoredQuestionCard(` — function, line 424

## Internal implementation anchors

- `const peek = peekPassage ?? jumpToSpan` — const, line 146
- `const sectionRead = currentSectionRead ?? currentSectionProgress` — const, line 148
- `const readThrough = completedSections.includes(section.id) || (sectionSeen[section.id] ?? 0) >= section.spanIds.length` — const, line 257
- `const state = section.id === currentGuideSection?.id ? "current" : readThrough ? "read" : "upcoming"` — const, line 259
- `const glyph = state === "read" ? "✓" : state === "current" ? "◐" : "·"` — const, line 260
- `const question = section.question` — const, line 443
- `const questionId = question?.authoredQuestionId ?? null` — const, line 450
- `const sourceSpan = question?.spanIds?.[0] ?? null` — const, line 451
- `const submit = useCallback(async ()` — const, line 456
- `const dismissForever = useCallback(async ()` — const, line 470
- `const escalate = useCallback(async ()` — const, line 483
- `const result = await api.readerEscalateAuthoredQuestion(` — const, line 487
- `function SectionQuestionCard(` — function, line 581
- `const question = section.question` — const, line 604
- `const begin = useCallback(async ()` — const, line 612
- `const opened = await api.readerPresentQuestion(` — const, line 616
- `const submit = useCallback(async ()` — const, line 636
- `const skip = useCallback(async ()` — const, line 655
- `const control = useCallback(async (value: string)` — const, line 673
- `const choose = useCallback(async (next: ReaderDisposition)` — const, line 706

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `GuideRail`, `SectionBoundaryOffer`; references `GuideRail`, `SectionBoundaryOffer`
- [[Reference/Desktop/TypeScript/screens/reader/DoseOffer|src/screens/reader/DoseOffer.tsx]] — import-or-re-export: `AuthoredQuestionCard`; references `AuthoredQuestionCard`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderDisposition`, `ReaderGuidePlanDto`, `ReaderGuideSectionDto`, `ReaderRenderBlockDto`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export; imports `PassageAlign`
- [[Reference/Desktop/TypeScript/components/goldenpath/shared|src/components/goldenpath/shared.tsx]] — import-or-re-export; imports `DispositionPicker`, `PrimaryButton`, `SecondaryButton`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `clip`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `LearnerVoice`, `MeaningLabel`, `ModelVoice`, `SourceVoice`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/splitRails.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/splitRails.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/findSection.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/findSection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/GuideRail.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/GuideRail.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

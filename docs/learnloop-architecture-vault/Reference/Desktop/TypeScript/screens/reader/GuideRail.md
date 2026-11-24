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
| Source lines | 1120 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/source/ScopedSource|src/screens/desks/source/ScopedSource.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/GuideRail|src/screens/reader/GuideRail.tsx]]

## Public API

- `export const SECTION_DONE_WRITING = `Writing questions from this section. $` — const, line 29
- `export const SECTION_DONE_FAILED = "Couldn't save that. Try again."` — const, line 31
- `export function sectionDoneWaiting(bookTitle?: string | null): string` — function, line 34
- `export function nearTheEnd(bookTitle?: string | null): string` — function, line 40
- `export const CHECK_COMES_UP = "A quick check on this section is ready. It comes up as you read on, near the end of the section."` — const, line 48
- `export interface ClosedCheck` — interface, line 52
- `export const QUESTION_CONTROLS: Array<` — const, line 60
- `export interface GuideRailProps` — interface, line 68
- `export function GuideRail(` — function, line 149
- `export function SectionBoundaryOffer(` — function, line 471
- `export function AuthoredQuestionCard(` — function, line 610
- `export function QuickChecks(` — function, line 1063

## Internal implementation anchors

- `const book = bookTitle ? `“$` — const, line 35
- `const peek = peekPassage ?? jumpToSpan` — const, line 202
- `const sections = guidePlan?.sections ?? []` — const, line 206
- `const currentIndex = currentGuideSection ? sections.findIndex((section)` — const, line 207
- `const nextSection = currentIndex >= 0 ? sections[currentIndex + 1] ?? null : null` — const, line 208
- `const lastSection = currentIndex >= 0 && nextSection === null` — const, line 210
- `const currentFinished = currentGuideSection ? completedSections.includes(currentGuideSection.id) : false` — const, line 211
- `const sectionRead = currentSectionRead ?? currentSectionProgress` — const, line 213
- `const result = await completeSection(sectionId)` — const, line 317
- `const finish: SectionFinish = result.enqueuedGeneration ? "writing" : result.waitingForBuild ? "waiting" : "done"` — const, line 319
- `const readThrough = completedSections.includes(section.id) || (sectionSeen[section.id] ?? 0) >= section.spanIds.length` — const, line 340
- `const state = section.id === currentGuideSection?.id ? "current" : readThrough ? "read" : "upcoming"` — const, line 342
- `const glyph = state === "read" ? "✓" : state === "current" ? "◐" : "·"` — const, line 343
- `type SectionFinish = "writing" | "waiting" | "done"` — type, line 512
- `function SectionDone(` — function, line 514
- `const finished = completed || finishedHere !== null` — const, line 540
- `const wasFinished = useRef<` — const, line 543
- `const guardUntil = useRef(0)` — const, line 544
- `const before = wasFinished.current` — const, line 545
- `const wayOn = (go: ()` — const, line 550
- `const question = section.question` — const, line 630
- `const questionId = question?.authoredQuestionId ?? null` — const, line 637
- `const sourceSpan = question?.spanIds?.[0] ?? null` — const, line 638
- `const submit = useCallback(async ()` — const, line 643
- `const dismissForever = useCallback(async ()` — const, line 657
- `const escalate = useCallback(async ()` — const, line 670
- `const result = await api.readerEscalateAuthoredQuestion(` — const, line 674
- `function SectionQuestionCard(` — function, line 771
- `const question = section.question` — const, line 799
- `const begin = useCallback(async ()` — const, line 807
- `const opened = await api.readerPresentQuestion(` — const, line 811
- `const submit = useCallback(async ()` — const, line 831
- `const skip = useCallback(async ()` — const, line 850
- `const control = useCallback(async (value: string)` — const, line 868
- `const choose = useCallback(async (next: ReaderDisposition)` — const, line 901
- `function ClosedCheckRecord(` — function, line 1003
- `function CheckActions(` — function, line 1027
- `const ref = useRef<HTMLDivElement>(null)` — const, line 1028
- `const element = ref.current` — const, line 1030
- `const frame = window.requestAnimationFrame(()` — const, line 1032
- `function FocusedButton(` — function, line 1046
- `const ref = useRef<HTMLSpanElement>(null)` — const, line 1047
- `const active = document.activeElement` — const, line 1049
- `const closeCheck = (section: ReaderGuideSectionDto, kept: Omit<ClosedCheck, "sectionId" | "label"> | null)` — const, line 1074
- `const open = new Set(sections.map((section)` — const, line 1079
- `const kept = Object.entries(closedChecks) .filter(([key, check])` — const, line 1080
- `const checks = available ? sections.map((section)` — const, line 1084

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/source/ScopedSource|src/screens/desks/source/ScopedSource.tsx]] — import-or-re-export: `GuideRail`, `QuickChecks`, `SectionBoundaryOffer`; references `GuideRail`, `QuickChecks`, `SectionBoundaryOffer`
- [[Reference/Desktop/TypeScript/screens/reader/DoseOffer|src/screens/reader/DoseOffer.tsx]] — import-or-re-export: `AuthoredQuestionCard`; references `AuthoredQuestionCard`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderDisposition`, `ReaderGuidePlanDto`, `ReaderGuideSectionDto`, `ReaderRenderBlockDto`
- [[Reference/Desktop/TypeScript/app/todayCause|src/app/todayCause.ts]] — import-or-re-export; imports `ON_TODAY`, `QUESTIONS_FROM_READING`, `readableTitle`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export; imports `PassageAlign`
- [[Reference/Desktop/TypeScript/components/Waiting|src/components/Waiting.tsx]] — import-or-re-export; imports `WaitMark`
- [[Reference/Desktop/TypeScript/components/goldenpath/shared|src/components/goldenpath/shared.tsx]] — import-or-re-export; imports `DispositionPicker`, `PrimaryButton`, `SecondaryButton`
- [[Reference/Desktop/TypeScript/components/scrollWithin|src/components/scrollWithin.ts]] — import-or-re-export; imports `scrollIntoViewWithin`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `BACK_TO_TODAY`, `CHECK_DONE`, `END_PRESS_GUARD_MS`, `READ_NEXT_SECTION`, `SECTION_DONE`, `SECTION_DONE_LINE`, `SECTION_ENDED_LINE`, `clip`, `closedCheckSummary`, `sectionWords`
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
- [apps/learnloop-tauri/src/screens/reader/sectionWords.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sectionWords.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/sectionEndRound.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sectionEndRound.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/sectionDone.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sectionDone.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/findSection.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/findSection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/checkControls.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/checkControls.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

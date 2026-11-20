---
title: "Desktop module · src/screens/feedback/FeedbackSurface.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.feedback.FeedbackSurface"
language: "TypeScript"
area: "TypeScript/screens/feedback"
source_path: "apps/learnloop-tauri/src/screens/feedback/FeedbackSurface.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/feedback/FeedbackSurface.tsx"
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

# `src/screens/feedback/FeedbackSurface.tsx`

Area: [[Reference/Desktop/TypeScript/screens/feedback/_area|TypeScript/screens/feedback]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `FeedbackSurface` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/feedback/FeedbackSurface.tsx](../../../../../../../apps/learnloop-tauri/src/screens/feedback/FeedbackSurface.tsx) |
| Source lines | 494 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/feedback/_area|TypeScript/screens/feedback]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/feedback/FeedbackSurface|src/screens/feedback/FeedbackSurface.tsx]]

## Public API

- `export interface FeedbackNextStep` — interface, line 48
- `export interface FeedbackContest` — interface, line 55
- `export interface FeedbackWhy` — interface, line 67
- `export function gradedVersionUnrecorded(f: FeedbackBundle): boolean` — function, line 90
- `export const UNRECORDED_VERSION_LINE = "The version of this question it was graded against wasn't kept."` — const, line 95
- `export const CURRENT_ANSWER_TITLE = "The answer as the question reads now"` — const, line 96
- `export const CURRENT_ANSWER_NOTE = "It may not be the one this was graded against."` — const, line 97
- `export function answeredFullAnswer(f: FeedbackBundle, item: PracticeItemDetail | null): string` — function, line 103
- `export function currentAnswerForUnrecorded(f: FeedbackBundle, item: PracticeItemDetail | null): string` — function, line 111
- `export function answeredCriterionRows(f: FeedbackBundle): CriterionEvidenceRowDto[]` — function, line 118
- `export function answeredMaxPoints(f: FeedbackBundle): number | null` — function, line 133
- `export function scoreOutOf(score: number, max: number | null, digits = 0): string` — function, line 139
- `export function AnswerWaiting(` — function, line 146
- `export function FeedbackSurface(` — function, line 190

## Internal implementation anchors

- `type FeedbackOrigin, HELD_GRADE_LINE, ORIGIN_LABEL, PROVISIONAL_GRADE_LINE, unestablishedRepairCopy, VERDICT_TEXT, type Verdict } from "../../app/practiceFeedback"` — type, line 38
- `type Verdict } from "../../app/practiceFeedback"` — type, line 44
- `function fmtDay(iso: string | null): string` — function, line 79
- `const date = new Date(iso)` — const, line 81
- `const frozen = f.answeredExpectedAnswer` — const, line 105
- `const frozen = f.answeredCriteria` — const, line 119
- `const byId = new Map(frozen.map((criterion)` — const, line 121
- `const criterion = byId.get(row.criterionId)` — const, line 123
- `const points = digits > 0 ? score.toFixed(digits) : String(score)` — const, line 140
- `function honestyLines(f: FeedbackBundle): string[]` — function, line 167
- `const lines: string[] = []` — const, line 168
- `const check = f.coldCheckResult` — const, line 174
- `const when = fmtDay(check.instructedAt)` — const, line 176
- `const held = verdict === "held"` — const, line 237
- `const unrecorded = gradedVersionUnrecorded(f)` — const, line 238
- `const presentation = f.answeredPresentation ?? item?.presentation ?? null` — const, line 239
- `const fullAnswer = answeredFullAnswer(f, item)` — const, line 240
- `const currentAnswer = currentAnswerForUnrecorded(f, item)` — const, line 241
- `const shownAnswer = fullAnswer || currentAnswer` — const, line 242
- `const criteria = answeredCriterionRows(f)` — const, line 243
- `const learnerAnswer = (f.learnerAnswerMd ?? "").trim()` — const, line 244
- `const exposure = useAnswerExposure( f.attemptId, Boolean(shownAnswer) && !answerCovered, recordAnswerDisplay ? (displayId)` — const, line 247
- `const diagnosisSummary = diagnosis.status === "done" && diagnosis.card?.cardEnabled !== false ? diagnosis.card?.summaryMd?.trim() || null : null` — const, line 252
- `const sentence = diagnosisSummary ?? (matchedCorrection ? `You may be mixing two ideas up. $` — const, line 254
- `const prerequisite = diagnosis.status === "done" ? diagnosis.card?.prerequisiteGap ?? null : null` — const, line 257
- `const whyHasContent = why.causes.length > 0 || why.showed.length > 0 || Boolean(why.mechanism) || why.madeBefore.length > 0 || why.onNotRight !== null || why.notRightRecorded` — const, line 258
- `const contestBox = useRef<HTMLInputElement>(null)` — const, line 265
- `const tone = verdict === "right" ? COLOR.green : verdict === "partly" ? COLOR.amber : COLOR.text` — const, line 269
- `const assessed = criterionAssessed(row)` — const, line 396
- `const full = row.pointsAwarded >= row.pointsPossible` — const, line 397
- `const some = row.pointsAwarded > 0` — const, line 398
- `const mark = !assessed ? "·" : full ? "✓" : some ? "◐" : "✗"` — const, line 399
- `const color = !assessed ? COLOR.textFaint : full ? COLOR.green : some ? COLOR.amber : COLOR.red` — const, line 400

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `FeedbackNextStep`, `FeedbackSurface`, `answeredCriterionRows`, `answeredMaxPoints`, `gradedVersionUnrecorded`, `scoreOutOf`; references `FeedbackNextStep`, `FeedbackSurface`, `answeredCriterionRows`, `answeredMaxPoints`, `gradedVersionUnrecorded`, `scoreOutOf`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `AnswerWaiting`; references `AnswerWaiting`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CriterionEvidenceRowDto`, `FeedbackBundle`, `PracticeItemDetail`, `criterionAssessed`
- [[Reference/Desktop/TypeScript/app/practiceFeedback|src/app/practiceFeedback.ts]] — import-or-re-export; imports `FeedbackOrigin`, `HELD_GRADE_LINE`, `ORIGIN_LABEL`, `PROVISIONAL_GRADE_LINE`, `VERDICT_TEXT`, `Verdict`, `expectedAnswerText`, `unestablishedRepairCopy`
- [[Reference/Desktop/TypeScript/components/DiagnosisCard|src/components/DiagnosisCard.tsx]] — import-or-re-export; imports `DiagnosisCardState`
- [[Reference/Desktop/TypeScript/components/ItemPresentation|src/components/ItemPresentation.tsx]] — import-or-re-export; imports `ItemPresentation`
- [[Reference/Desktop/TypeScript/components/PlainParts|src/components/PlainParts.tsx]] — import-or-re-export; imports `DetailsToggle`, `PrimaryAction`, `QuietAction`, `VoicePanel`, `quietLine`, `quietLink`
- [[Reference/Desktop/TypeScript/components/Waiting|src/components/Waiting.tsx]] — import-or-re-export; imports `Waiting`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`
- [[Reference/Desktop/TypeScript/copy/waiting|src/copy/waiting.ts]] — import-or-re-export; imports `WAITING_COPY`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/feedback/answerExposure|src/screens/feedback/answerExposure.ts]] — import-or-re-export; imports `ExposureStatus`, `useAnswerExposure`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_review_log.py](../../../../../../../tests/test_review_log.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_learner_review_system_entries.py](../../../../../../../tests/test_learner_review_system_entries.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_forecast_ledger.py](../../../../../../../tests/test_forecast_ledger.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/feedback/FeedbackSurface.tsx](../../../../../../../apps/learnloop-tauri/src/screens/feedback/FeedbackSurface.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

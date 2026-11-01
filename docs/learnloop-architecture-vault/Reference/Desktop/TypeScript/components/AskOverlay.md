---
title: "Desktop module · src/components/AskOverlay.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.AskOverlay"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/AskOverlay.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/AskOverlay.tsx"
source_commit: "363fc7c1bd806d2f144610c830b8c3fac35e2170"
source_commit_timestamp: "2026-10-25T22:07:58-04:00"
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

# `src/components/AskOverlay.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `AskOverlay` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/AskOverlay.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.tsx) |
| Source lines | 1439 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `363fc7c1bd806d2f144610c830b8c3fac35e2170` |
| Commit timestamp | `2026-10-25T22:07:58-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]]

## Public API

- `export interface AskTarget` — interface, line 65
- `export type AskVariant = "modal" | "docked" | "inline"` — type, line 115
- `export function AskOverlay(` — function, line 227

## Internal implementation anchors

- `async function readerThreadParent(extractionId: string, spanId: string, questionEventId?: string): Promise<string | null>` — function, line 50
- `const history = (api as` — const, line 52
- `const CONTEXT_PILL: Record<TutorQuestionContext, PillColor> =` — const, line 117
- `interface ThreadEntry` — interface, line 124
- `function restoredEntryFields(event: TutorQuestionEventDto): Partial<ThreadEntry>` — function, line 167
- `const context = (event.sourceContext ??` — const, line 168
- `const GAP_POLL_MS = 2000` — const, line 183
- `const GAP_POLL_LIMIT = 45` — const, line 184
- `const REVERSAL_LABEL: Record<LearnerTextGapReversal, string> =` — const, line 186
- `interface SaveNotice` — interface, line 192
- `function promotionChipLabel(promotion: QuestionPromotionDto): string` — function, line 198
- `function promotionRequestLabel(request: QuestionPromotionRequestDto): string` — function, line 215
- `function entityIdOf(target: AskTarget): string` — function, line 223
- `const panelOn = algoConfig().ask !== null` — const, line 258
- `const panel = panelOn && variant !== "modal"` — const, line 259
- `const helpStyle = useStoredHelpStyle()` — const, line 260
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 285
- `const inputRef = useRef<HTMLInputElement | null>(null)` — const, line 286
- `const boxRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 287
- `const saveNoticeTimerRef = useRef<number | null>(null)` — const, line 288
- `const promoteNoticeTimerRef = useRef<number | null>(null)` — const, line 289
- `const routedCaptureRef = useRef<string | null>(null)` — const, line 290
- `const captureNoteRef = useRef<string | null>(null)` — const, line 291
- `const readerParentRef = useRef<string | null | undefined>(undefined)` — const, line 296
- `const gapTimersRef = useRef<number[]>([])` — const, line 297
- `function setEntryGap(eventId: string, gap: LearnerTextGapViewDto | null)` — function, line 307
- `function watchGap(eventId: string, queued: LearnerGapQueuedDto | undefined, attempt = 0)` — function, line 311
- `const timer = window.setTimeout(async ()` — const, line 313
- `const result = await api.getLearnerTextGap(` — const, line 315
- `async function reverseGap(eventId: string, gapId: string, reversal: LearnerTextGapReversal)` — function, line 329
- `const result = await api.reverseLearnerTextGap(` — const, line 331
- `const open = target !== null` — const, line 339
- `function clearSaveNoticeTimer()` — function, line 341
- `function showSaveNotice(notice: SaveNotice)` — function, line 348
- `function clearPromoteNoticeTimer()` — function, line 357
- `function showPromoteNotice(notice: SaveNotice)` — function, line 364
- `function saveNoteLabel(entry: ThreadEntry)` — function, line 373
- `function canSaveNote(entry: ThreadEntry)` — function, line 379
- `let cancelled = false` — let, line 385
- `const entries: ThreadEntry[] = snapshot.events.map((event: TutorQuestionEventDto)` — const, line 432
- `const onKey = (event: KeyboardEvent)` — const, line 507
- `const focusOnLand = variant === "modal" ? thread.length : 0` — const, line 521
- `const node = bodyRef.current` — const, line 527
- `async function send(pinned?:` — function, line 533
- `const text = (pinned?.text ?? question).trim()` — const, line 535
- `let answer:` — let, line 558
- `const readerAnswer = await api.readerAsk(` — const, line 579
- `const input: AskTutorQuestionInput =` — const, line 600
- `const draft = target.readDraft?.() ?? target.workMd ?? ""` — const, line 635
- `const tutorAnswer = await api.askTutorQuestion(input)` — const, line 642
- `const commandError = error as CommandError` — const, line 693
- `async function rate(eventId: string, useful: boolean)` — function, line 708
- `async function saveAsNote(eventId: string)` — function, line 719
- `const result = await api.saveTutorAnswerNote(eventId)` — const, line 722
- `const noteName = result.noteId ? ` $` — const, line 728
- `async function promote(eventId: string, intent: PromotionIntent)` — function, line 740
- `const result = await api.promoteTutorQuestion(eventId, intent)` — const, line 744
- `const cold = Boolean(target.coldCheck) || serverCold` — const, line 765
- `function inlineShows(entry: ThreadEntry): boolean` — function, line 769
- `const hasDraft = target.context === "practice" && Boolean((target.readDraft?.() ?? target.workMd ?? "").trim())` — const, line 776
- `const aboutChips: string[] = target.context === "feedback" ? ["your attempt", "its feedback"] : target.aboutStep ? [`step $` — const, line 777
- `const sentList = [ target.context === "feedback" ? "the attempt you submitted, its grade and feedback" : "the question", ...(hasDraft && !dropDraft ? [target.workbenchSessionId ? "your steps, as you have them now" : "your draft, as it is now"] : []), ...(targ…` — const, line 782
- `const panelHeader = panel ? ( <div style=` — const, line 789
- `const earlierEntry = earlier.find((entry)` — const, line 838
- `const panelFoot = panel && variant === "docked" && !cold && earlier.length > 0 ? ( <div data-testid="ask-earlier" style=` — const, line 839
- `const content = ( <>` — const, line 884
- `const shell = !panel ? ( <div style=` — const, line 1311
- `const dockedStyle: CSSProperties =` — const, line 1354
- `const inlineStyle: CSSProperties =` — const, line 1365
- `const backdropStyle: CSSProperties =` — const, line 1375
- `const modalStyle: CSSProperties =` — const, line 1387
- `const headerStyle: CSSProperties =` — const, line 1400
- `const inputStyle: CSSProperties =` — const, line 1409
- `const footerStyle: CSSProperties =` — const, line 1420
- `const saveNoticeStyle: CSSProperties =` — const, line 1431

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `AskOverlay`, `AskTarget`; references `AskOverlay`, `AskTarget`
- [[Reference/Desktop/TypeScript/components/InboxStrip|src/components/InboxStrip.tsx]] — import-or-re-export: `AskTarget`; references `AskTarget`
- [[Reference/Desktop/TypeScript/components/QuestionQueue|src/components/QuestionQueue.tsx]] — import-or-re-export: `AskTarget`; references `AskTarget`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `AskOverlay`, `AskTarget`; references `AskOverlay`, `AskTarget`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `AskTarget`; references `AskTarget`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderWorkingPosture|src/screens/reader/ReaderWorkingPosture.tsx]] — import-or-re-export: `AskOverlay`; references `AskOverlay`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `AskTarget`; references `AskTarget`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AnswerMode`, `AskTutorQuestionInput`, `AttemptProgress`, `CommandError`, `EarlierThreadDto`, `LearnerGapQueuedDto`, `LearnerTextGapReversal`, `LearnerTextGapViewDto`, `PracticeRequestDto`, `PromotionIntent`, `QuestionPromotionDto`, `QuestionPromotionRequestDto`, `SourceToolRequestDto`, `SuggestedLearningObjectDto`, `TutorCitationDto`, `TutorQuestionContext`, `TutorQuestionEventDto`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/OpenInSource|src/components/OpenInSource.tsx]] — import-or-re-export; imports `OpenInSource`
- [[Reference/Desktop/TypeScript/components/SourceOffers|src/components/SourceOffers.tsx]] — import-or-re-export; imports `SourceOffers`
- [[Reference/Desktop/TypeScript/components/askPanel|src/components/askPanel.tsx]] — import-or-re-export; imports `ANSWER_MODE_LABEL`, `ASK_COPY`, `ONE_QUESTION_MODES`, `STYLE_ANSWER_MODE`, `StoredHelpStyle`, `answerCountLabel`, `shortDate`, `useStoredHelpStyle`
- [[Reference/Desktop/TypeScript/components/askSuggestions|src/components/askSuggestions.ts]] — import-or-re-export; imports `suggestionLine`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export; imports `notifyQueueChanged`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/SourceOffers.test.tsx](../../../../../../apps/learnloop-tauri/src/components/SourceOffers.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/AskOverlay.test.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/AskOverlay.suggestion.test.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.suggestion.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/AskOverlay.steps.test.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.steps.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/AskOverlay.reader.test.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.reader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/AskOverlay.panel.test.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.panel.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/AskOverlay.capture.test.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.capture.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_field_signal_production_paths.py](../../../../../../tests/test_field_signal_production_paths.py) — cross-boundary name contract: references uniquely owned exported name `AskOverlay`; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/AskOverlay.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

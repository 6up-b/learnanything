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
source_commit: "afb17672c627b4f4422c149ac63dd2addef98a9b"
source_commit_timestamp: "2026-11-01T20:23:43-05:00"
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
| Source lines | 1480 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `afb17672c627b4f4422c149ac63dd2addef98a9b` |
| Commit timestamp | `2026-11-01T20:23:43-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]]

## Public API

- `export interface AskTarget` — interface, line 68
- `export type AskVariant = "modal" | "docked" | "inline"` — type, line 118
- `export function AskOverlay(` — function, line 230

## Internal implementation anchors

- `async function readerThreadParent(extractionId: string, spanId: string, questionEventId?: string): Promise<string | null>` — function, line 53
- `const history = (api as` — const, line 55
- `const CONTEXT_PILL: Record<TutorQuestionContext, PillColor> =` — const, line 120
- `interface ThreadEntry` — interface, line 127
- `function restoredEntryFields(event: TutorQuestionEventDto): Partial<ThreadEntry>` — function, line 170
- `const context = (event.sourceContext ??` — const, line 171
- `const GAP_POLL_MS = 2000` — const, line 186
- `const GAP_POLL_LIMIT = 45` — const, line 187
- `const REVERSAL_LABEL: Record<LearnerTextGapReversal, string> =` — const, line 189
- `interface SaveNotice` — interface, line 195
- `function promotionChipLabel(promotion: QuestionPromotionDto): string` — function, line 201
- `function promotionRequestLabel(request: QuestionPromotionRequestDto): string` — function, line 218
- `function entityIdOf(target: AskTarget): string` — function, line 226
- `const panelOn = algoConfig().ask !== null` — const, line 265
- `const panel = panelOn && variant !== "modal"` — const, line 266
- `const helpStyle = useStoredHelpStyle()` — const, line 267
- `const bodyRef = useRef<HTMLDivElement | null>(null)` — const, line 292
- `const inputRef = useRef<HTMLInputElement | null>(null)` — const, line 293
- `const boxRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 294
- `const saveNoticeTimerRef = useRef<number | null>(null)` — const, line 295
- `const promoteNoticeTimerRef = useRef<number | null>(null)` — const, line 296
- `const routedCaptureRef = useRef<string | null>(null)` — const, line 297
- `const captureNoteRef = useRef<string | null>(null)` — const, line 298
- `const readerParentRef = useRef<string | null | undefined>(undefined)` — const, line 303
- `const gapTimersRef = useRef<number[]>([])` — const, line 304
- `const figures = usePanelFigures(panel ? target : null,` — const, line 307
- `function setEntryGap(eventId: string, gap: LearnerTextGapViewDto | null)` — function, line 319
- `function watchGap(eventId: string, queued: LearnerGapQueuedDto | undefined, attempt = 0)` — function, line 323
- `const timer = window.setTimeout(async ()` — const, line 325
- `const result = await api.getLearnerTextGap(` — const, line 327
- `async function reverseGap(eventId: string, gapId: string, reversal: LearnerTextGapReversal)` — function, line 341
- `const result = await api.reverseLearnerTextGap(` — const, line 343
- `const open = target !== null` — const, line 351
- `function clearSaveNoticeTimer()` — function, line 353
- `function showSaveNotice(notice: SaveNotice)` — function, line 360
- `function clearPromoteNoticeTimer()` — function, line 369
- `function showPromoteNotice(notice: SaveNotice)` — function, line 376
- `function saveNoteLabel(entry: ThreadEntry)` — function, line 385
- `function canSaveNote(entry: ThreadEntry)` — function, line 391
- `let cancelled = false` — let, line 397
- `const entries: ThreadEntry[] = snapshot.events.map((event: TutorQuestionEventDto)` — const, line 444
- `const onKey = (event: KeyboardEvent)` — const, line 519
- `const focusOnLand = variant === "modal" ? thread.length : 0` — const, line 533
- `const node = bodyRef.current` — const, line 539
- `async function send(pinned?:` — function, line 545
- `const text = (pinned?.text ?? question).trim()` — const, line 547
- `let answer:` — let, line 570
- `const readerAnswer = await api.readerAsk(` — const, line 591
- `const input: AskTutorQuestionInput =` — const, line 613
- `const draft = target.readDraft?.() ?? target.workMd ?? ""` — const, line 648
- `const tutorAnswer = await api.askTutorQuestion(input)` — const, line 655
- `const commandError = error as CommandError` — const, line 706
- `async function rate(eventId: string, useful: boolean)` — function, line 721
- `async function saveAsNote(eventId: string)` — function, line 732
- `const result = await api.saveTutorAnswerNote(eventId)` — const, line 735
- `const noteName = result.noteId ? ` $` — const, line 741
- `async function promote(eventId: string, intent: PromotionIntent)` — function, line 753
- `const result = await api.promoteTutorQuestion(eventId, intent)` — const, line 757
- `const cold = Boolean(target.coldCheck) || serverCold` — const, line 778
- `function inlineShows(entry: ThreadEntry): boolean` — function, line 782
- `const hasDraft = target.context === "practice" && Boolean((target.readDraft?.() ?? target.workMd ?? "").trim())` — const, line 789
- `const aboutChips: string[] = target.context === "feedback" ? ["your attempt", "its feedback"] : target.aboutStep ? [`step $` — const, line 790
- `const sentList = [ target.context === "feedback" ? "the attempt you submitted, its grade and feedback" : "the question", ...(hasDraft && !dropDraft ? [target.workbenchSessionId ? "your steps, as you have them now" : "your draft, as it is now"] : []), ...(targ…` — const, line 795
- `const panelHeader = panel ? ( <div style=` — const, line 802
- `const earlierEntry = earlier.find((entry)` — const, line 851
- `const panelFoot = panel && variant === "docked" && !cold && earlier.length > 0 ? ( <div data-testid="ask-earlier" style=` — const, line 852
- `const content = ( <>` — const, line 897
- `const goal = question.trim()` — const, line 1244
- `const goal = question.trim()` — const, line 1296
- `const shell = !panel ? ( <div style=` — const, line 1352
- `const dockedStyle: CSSProperties =` — const, line 1395
- `const inlineStyle: CSSProperties =` — const, line 1406
- `const backdropStyle: CSSProperties =` — const, line 1416
- `const modalStyle: CSSProperties =` — const, line 1428
- `const headerStyle: CSSProperties =` — const, line 1441
- `const inputStyle: CSSProperties =` — const, line 1450
- `const footerStyle: CSSProperties =` — const, line 1461
- `const saveNoticeStyle: CSSProperties =` — const, line 1472

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `AskOverlay`, `AskTarget`; references `AskOverlay`, `AskTarget`
- [[Reference/Desktop/TypeScript/components/InboxStrip|src/components/InboxStrip.tsx]] — import-or-re-export: `AskTarget`; references `AskTarget`
- [[Reference/Desktop/TypeScript/components/QuestionQueue|src/components/QuestionQueue.tsx]] — import-or-re-export: `AskTarget`; references `AskTarget`
- [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] — import-or-re-export: `AskTarget`; references `AskTarget`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `AskOverlay`, `AskTarget`; references `AskOverlay`, `AskTarget`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `AskTarget`; references `AskTarget`
- [[Reference/Desktop/TypeScript/screens/practice/HintPanel|src/screens/practice/HintPanel.tsx]] — import-or-re-export: `AskTarget`; references `AskTarget`
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
- [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] — import-or-re-export; imports `PANEL_FIGURE_COPY`, `PanelFigureEvent`, `PanelFigureThreadLine`, `figureCostLine`, `usePanelFigures`
- [[Reference/Desktop/TypeScript/components/askPanel|src/components/askPanel.tsx]] — import-or-re-export; imports `ANSWER_MODE_LABEL`, `ASK_COPY`, `ONE_QUESTION_MODES`, `STYLE_ANSWER_MODE`, `StoredHelpStyle`, `answerCountLabel`, `shortDate`, `useStoredHelpStyle`
- [[Reference/Desktop/TypeScript/components/askSuggestions|src/components/askSuggestions.ts]] — import-or-re-export; imports `suggestionLine`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `PillColor`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export; imports `notifyQueueChanged`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/reader/figures/showMe|src/screens/reader/figures/showMe.ts]] — import-or-re-export; imports `isShowMeKey`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `passageKeys`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/askFigures.test.tsx](../../../../../../apps/learnloop-tauri/src/components/askFigures.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/SourceOffers.test.tsx](../../../../../../apps/learnloop-tauri/src/components/SourceOffers.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/AskOverlay.test.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/AskOverlay.suggestion.test.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.suggestion.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/AskOverlay.steps.test.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.steps.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/AskOverlay.reader.test.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.reader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/AskOverlay.panel.test.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.panel.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/AskOverlay.capture.test.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.capture.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/AskOverlay.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

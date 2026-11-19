---
title: "Desktop module · src/screens/today/TodayPlace.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.today.TodayPlace"
language: "TypeScript"
area: "TypeScript/screens/today"
source_path: "apps/learnloop-tauri/src/screens/today/TodayPlace.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/today/TodayPlace.tsx"
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

# `src/screens/today/TodayPlace.tsx`

Area: [[Reference/Desktop/TypeScript/screens/today/_area|TypeScript/screens/today]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `TodayPlace` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/today/TodayPlace.tsx](../../../../../../../apps/learnloop-tauri/src/screens/today/TodayPlace.tsx) |
| Source lines | 977 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/today/_area|TypeScript/screens/today]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]]

## Public API

- `export interface TodayPlaceProps` — interface, line 74
- `export function TodayPlace(` — function, line 426

## Internal implementation anchors

- `type TodayThread } from "../../app/todayPlan"` — type, line 70
- `const LEFT = Symbol("today-left")` — const, line 107
- `const linkButton: CSSProperties =` — const, line 109
- `const dimLink: CSSProperties =` — const, line 119
- `function actionButton(primary = false): CSSProperties` — function, line 121
- `function MinuteChips(` — function, line 133
- `const selected = minutes === value` — const, line 137
- `function enterOnControl(event: KeyboardEvent): boolean` — function, line 166
- `function stepChoice(choices: number[], current: number | null, delta: number): number | undefined` — function, line 170
- `const index = choices.indexOf(current)` — const, line 172
- `function PlanWhy(` — function, line 177
- `const plan = data.plan` — const, line 178
- `const headline = useCachedQuery(data.headlineEnabled === false ? null : ["get_today_headline"], ()` — const, line 179
- `const rows = todayRows(plan)` — const, line 183
- `const reentry = plan.kind === "reentry" ? reentryWhy(plan) : null` — const, line 184
- `const split = splitWhy(plan)` — const, line 185
- `const line = headline.data?.enabled ? headline.data.line ?? null : null` — const, line 186
- `function Threads(` — function, line 228
- `const questions = useCachedQuery(["list_question_queue", "today-threads"], ()` — const, line 239
- `const problems = useCachedQuery(["workbench_open_problems"], ()` — const, line 240
- `const threads = useMemo( ()` — const, line 243
- `function threadAction(thread: TodayThread):` — function, line 251
- `const citation = thread.question.sourceCitation` — const, line 253
- `const target = targetForDialogue(thread.question)` — const, line 255
- `const shown = more ? threads : threads.slice(0, THREADS_SHOWN)` — const, line 260
- `const act = threadAction(thread)` — const, line 265
- `function CapturesLine(` — function, line 293
- `const summary = useCachedQuery(["get_inbox_summary", "today"], ()` — const, line 294
- `const data = summary.data` — const, line 296
- `const something = Boolean(data && ((data.newCount ?? 0) > 0 || (data.deletePending?.length ?? 0) > 0 || data.vaultMismatch))` — const, line 297
- `function PlainList(` — function, line 311
- `const items = useMemo(()` — const, line 330
- `const minutesOf = useMemo(()` — const, line 331
- `const map = new Map<string, number>()` — const, line 332
- `const onKey = (event: KeyboardEvent)` — const, line 342
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 344
- `const item = items[focus]` — const, line 355
- `const minutes = minutesOf.get(item.practiceItemId)` — const, line 392
- `const cold = onYourOwnWhy(item)` — const, line 393
- `const planQuery = useDailyPlan(session?.sessionId ?? null)` — const, line 444
- `const data: DailyPlanDto | null = planQuery.data ?? null` — const, line 445
- `const planOn = data?.enabled === true && data.plan !== null` — const, line 446
- `const plan = planOn ? data!.plan : null` — const, line 447
- `const planOff = data !== null && !planOn` — const, line 448
- `const now = new Date()` — const, line 458
- `const summary = useCachedQuery(planOff ? ["get_start_summary"] : null, ()` — const, line 461
- `const offMinutes = session?.availableMinutes ?? chosenMinutes ?? summary.data?.rememberedMinutes ?? null` — const, line 463
- `const minutes = plan ? plan.rememberedMinutes : offMinutes` — const, line 464
- `const choices = plan ? plan.minuteChoices : summary.data?.minuteChoices ?? summary.data?.minutesPresets ?? []` — const, line 465
- `const queueInput = useMemo( ()` — const, line 471
- `const queueQuery = useCachedQuery( queueInput && (list || planOff) ? ["get_today_queue", queueInput] : null, ()` — const, line 481
- `const queue = queueQuery.data ?? null` — const, line 486
- `const retryQueue = useCallback(()` — const, line 490
- `const report = queueQuery.retryReport()` — const, line 491
- `const library = useCachedQuery(["get_source_library"], ()` — const, line 495
- `const noBooks = library.data !== undefined && library.data.sources.length === 0 && (library.data.pending?.length ?? 0) === 0` — const, line 496
- `const goals = useCachedQuery(["goals_list"], ()` — const, line 498
- `const primaryGoal: GoalDto | null = useMemo(()` — const, line 499
- `const active = (goals.data?.goals ?? []).filter((goal)` — const, line 500
- `const da = a.dueAt ? Date.parse(a.dueAt) : Infinity` — const, line 502
- `const db = b.dueAt ? Date.parse(b.dueAt) : Infinity` — const, line 503
- `const deciding = plan?.deciding === true && !list` — const, line 511
- `const refetchPlan = planQuery.refetch` — const, line 512
- `let reads = 0` — let, line 515
- `const timer = window.setInterval(()` — const, line 516
- `const waitingUntil = plan?.waiting?.until ?? null` — const, line 526
- `const at = Date.parse(waitingUntil)` — const, line 529
- `const timer = window.setTimeout(()` — const, line 531
- `const alive = useRef(true)` — const, line 539
- `const stay = useCallback(<T,>(value: T): T` — const, line 546
- `const startSession = useCallback( async (minutes: number): Promise<SessionSnapshot>` — const, line 551
- `const started = await onStartSession(minutes)` — const, line 553
- `const run = useCallback( async <T,>(work: ()` — const, line 559
- `const done = plan ? plan.status !== "open" : false` — const, line 575
- `const current = plan?.blocks.find((block)` — const, line 576
- `const waiting = plan && !done && !current && plan.waiting ? plan.waiting : null` — const, line 577
- `const inProgress = plan && !done && !current ? plan.questionInProgress ?? null : null` — const, line 580
- `const openProblems = useCachedQuery(inProgress ? ["workbench_open_problems"] : null, ()` — const, line 581
- `const inProgressProblem = inProgress ? openProblems.data?.problems.find((problem)` — const, line 582
- `const inProgressItem = inProgress?.practiceItemId ?? null` — const, line 583
- `const rows = plan && !done ? todayRows(plan) : []` — const, line 584
- `async function begin()` — function, line 587
- `const begun = await run(async ()` — const, line 591
- `const started = await startSession(Math.round(plan.minutesBudget))` — const, line 592
- `const first = await api.nextPlanItem(` — const, line 593
- `const result = await run(()` — const, line 599
- `const action = planStepAction(result?.step,` — const, line 600
- `function afterSomethingElse(result: SomethingElseChosenDto)` — function, line 607
- `const entry = lessonEntryFor(result)` — const, line 608
- `const action = planStepAction(result.step,` — const, line 617
- `async function beginWithoutPlan()` — function, line 625
- `const opened = await run(async ()` — const, line 627
- `const started = session ?? (await startSession(minutes))` — const, line 628
- `const head = await api.getTodayQueue(todayQueueInput(started))` — const, line 629
- `function chooseMinutes(next: number)` — function, line 637
- `async function keepGoing()` — function, line 646
- `const result = await run(()` — const, line 649
- `async function somethingNew(confirm: boolean)` — function, line 655
- `const result = await run(()` — const, line 657
- `async function finish()` — function, line 661
- `const summaryResult = await run(()` — const, line 664
- `async function skipCurrent()` — function, line 668
- `const next = current.items.find((item)` — const, line 674
- `async function openFromList(item: ScheduledItemDto)` — function, line 685
- `const started = await run(()` — const, line 688
- `const begun = await run(async ()` — const, line 696
- `const started = await startSession(Math.round(plan.minutesBudget))` — const, line 697
- `const result = await api.planLearnerPick(item.practiceItemId, started.sessionId, item.schedulerCandidateId ?? null)` — const, line 698
- `const result = await run(()` — const, line 704
- `const step = result.step` — const, line 706
- `async function practiseGoal()` — function, line 717
- `const input = queueInput ?? todayQueueInput(session)` — const, line 719
- `const snapshot = await run(()` — const, line 720
- `const target = snapshot.sections.flatMap((section)` — const, line 722
- `const onKey = (event: KeyboardEvent)` — const, line 732
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 734
- `const next = stepChoice(choices, minutes, event.key === "ArrowLeft" ? -1 : 1)` — const, line 754
- `const streak = data?.streak ?? snapshotStreak` — const, line 762
- `const streakText = streakLine(streak)` — const, line 763
- `let body: ReactNode` — let, line 766
- `const head = queue?.sections.flatMap((section)` — const, line 803
- `const empty = planWasEmpty(data)` — const, line 817
- `const sentence = plan.kind === "reentry" ? reentrySentence(plan) : planSentence(plan)` — const, line 856
- `function KeepGoingNothing()` — function, line 971

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `TodayPlace`; references `TodayPlace`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DailyPlanDto`, `GoalDto`, `PlanReadingDto`, `PlanStepDto`, `QueueSnapshot`, `ScheduledItemDto`, `SessionEndSummary`, `SessionSnapshot`, `SomethingElseChosenDto`, `StreakSummary`, `WorkbenchOpenProblemDto`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`
- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export; imports `todayQueueInput`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `aboutMinutes`, `planStepAction`, `questionInProgressLine`, `useDailyPlan`, `waitingLine`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `INTERACTIVE_SELECTOR`, `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/todayPlan|src/app/todayPlan.ts]] — import-or-re-export; imports `GOAL_NOTHING_READY`, `KEEP_GOING_NOTHING`, `THREADS_SHOWN`, `TodayThread`, `dayPhrase`, `doneLine`, `fullListWhy`, `onYourOwnWhy`, `planSentence`, `planWasEmpty`, `reentrySentence`, `reentryWhy`, `splitWhy`, `streakLine`, `todayRows`, `todayThreads`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export; imports `AskTarget`
- [[Reference/Desktop/TypeScript/components/GoalCard|src/components/GoalCard.tsx]] — import-or-re-export; imports `GoalCard`
- [[Reference/Desktop/TypeScript/components/GoalWizard|src/components/GoalWizard.tsx]] — import-or-re-export; imports `GoalWizard`
- [[Reference/Desktop/TypeScript/components/InboxStrip|src/components/InboxStrip.tsx]] — import-or-re-export; imports `InboxStrip`
- [[Reference/Desktop/TypeScript/components/QuestionQueue|src/components/QuestionQueue.tsx]] — import-or-re-export; imports `targetForDialogue`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `ErrorReport`, `errorMessage`
- [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] — import-or-re-export; imports `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/today/LessonOfferBlock|src/screens/today/LessonOfferBlock.tsx]] — import-or-re-export; imports `LessonOfferBlock`
- [[Reference/Desktop/TypeScript/screens/today/LessonSuggestionCard|src/screens/today/LessonSuggestionCard.tsx]] — import-or-re-export; imports `LessonSuggestionCard`
- [[Reference/Desktop/TypeScript/screens/today/QuestionInProgress|src/screens/today/QuestionInProgress.tsx]] — import-or-re-export; imports `QuestionInProgress`
- [[Reference/Desktop/TypeScript/screens/today/SomethingElse|src/screens/today/SomethingElse.tsx]] — import-or-re-export; imports `SomethingElse`, `lessonEntryFor`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/today/TodayPlace.tsx](../../../../../../../apps/learnloop-tauri/src/screens/today/TodayPlace.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

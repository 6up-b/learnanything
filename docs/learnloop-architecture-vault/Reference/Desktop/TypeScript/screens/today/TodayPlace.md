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
| Source lines | 1255 |
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

- `export interface TodayPlaceProps` — interface, line 93
- `export function TodayPlace(` — function, line 464

## Internal implementation anchors

- `type TodayThread } from "../../app/todayPlan"` — type, line 75
- `type TodayCause } from "../../app/todayCause"` — type, line 90
- `const LEFT = Symbol("today-left")` — const, line 141
- `const linkButton: CSSProperties =` — const, line 143
- `const dimLink: CSSProperties =` — const, line 153
- `const CAUSE_POLL_MS = 5000` — const, line 157
- `function actionButton(primary = false): CSSProperties` — function, line 159
- `function MinuteChips(` — function, line 171
- `const selected = minutes === value` — const, line 175
- `function enterOnControl(event: KeyboardEvent): boolean` — function, line 204
- `function stepChoice(choices: number[], current: number | null, delta: number): number | undefined` — function, line 208
- `const index = choices.indexOf(current)` — const, line 210
- `function PlanWhy(` — function, line 215
- `const plan = data.plan` — const, line 216
- `const headline = useCachedQuery(data.headlineEnabled === false ? null : ["get_today_headline"], ()` — const, line 217
- `const rows = todayRows(plan)` — const, line 221
- `const reentry = plan.kind === "reentry" ? reentryWhy(plan) : null` — const, line 222
- `const split = splitWhy(plan)` — const, line 223
- `const line = headline.data?.enabled ? headline.data.line ?? null : null` — const, line 224
- `function Threads(` — function, line 266
- `const questions = useCachedQuery(["list_question_queue", "today-threads"], ()` — const, line 277
- `const problems = useCachedQuery(["workbench_open_problems"], ()` — const, line 278
- `const threads = useMemo( ()` — const, line 281
- `function threadAction(thread: TodayThread):` — function, line 289
- `const citation = thread.question.sourceCitation` — const, line 291
- `const target = targetForDialogue(thread.question)` — const, line 293
- `const shown = more ? threads : threads.slice(0, THREADS_SHOWN)` — const, line 298
- `const act = threadAction(thread)` — const, line 303
- `function CapturesLine(` — function, line 331
- `const summary = useCachedQuery(["get_inbox_summary", "today"], ()` — const, line 332
- `const data = summary.data` — const, line 334
- `const something = Boolean(data && ((data.newCount ?? 0) > 0 || (data.deletePending?.length ?? 0) > 0 || data.vaultMismatch))` — const, line 335
- `function PlainList(` — function, line 349
- `const items = useMemo(()` — const, line 368
- `const minutesOf = useMemo(()` — const, line 369
- `const map = new Map<string, number>()` — const, line 370
- `const onKey = (event: KeyboardEvent)` — const, line 380
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 382
- `const item = items[focus]` — const, line 393
- `const minutes = minutesOf.get(item.practiceItemId)` — const, line 430
- `const cold = onYourOwnWhy(item)` — const, line 431
- `const planQuery = useDailyPlan(session?.sessionId ?? null)` — const, line 488
- `const data: DailyPlanDto | null = planQuery.data ?? null` — const, line 489
- `const planOn = data?.enabled === true && data.plan !== null` — const, line 490
- `const plan = planOn ? data!.plan : null` — const, line 491
- `const planOff = data !== null && !planOn` — const, line 492
- `const lineHeld = useRef(false)` — const, line 499
- `const now = new Date()` — const, line 508
- `const summary = useCachedQuery(planOff ? ["get_start_summary"] : null, ()` — const, line 511
- `const offMinutes = session?.availableMinutes ?? chosenMinutes ?? summary.data?.rememberedMinutes ?? null` — const, line 513
- `const minutes = plan ? plan.rememberedMinutes : offMinutes` — const, line 514
- `const choices = plan ? plan.minuteChoices : summary.data?.minuteChoices ?? summary.data?.minutesPresets ?? []` — const, line 515
- `const planDone = plan ? plan.status !== "open" : false` — const, line 520
- `const emptyDay = data !== null && plan !== null && (planDone ? planWasEmpty(data) : todayRows(plan).length === 0 && plan.deciding !== true && !plan.waiting && !plan.questionInProgress)` — const, line 521
- `const queueInput = useMemo( ()` — const, line 532
- `const queueQuery = useCachedQuery( queueInput && (list || planOff || emptyDay || planDone || keptGoingToNothing) ? ["get_today_queue", queueInput] : null, ()` — const, line 542
- `const queue = queueQuery.data ?? null` — const, line 547
- `const retryQueue = useCallback(()` — const, line 551
- `const report = queueQuery.retryReport()` — const, line 552
- `const library = useCachedQuery(["get_source_library"], ()` — const, line 556
- `const noBooks = library.data !== undefined && library.data.sources.length === 0 && (library.data.pending?.length ?? 0) === 0` — const, line 557
- `const listItems = queueQuery.error ? 0 : queue ? queue.sections.reduce((count, section)` — const, line 558
- `const moreLeft: boolean | null = !plan || !planDone ? null : plan.blocks.some((block)` — const, line 562
- `const cause: TodayCause | null = emptyDay || (keptGoingToNothing && planOn) ? todayCause(` — const, line 568
- `const refetchLibrary = library.refetch` — const, line 573
- `const refetchQueue = queueQuery.refetch` — const, line 574
- `const onTheWay = cause?.kind === "on_the_way"` — const, line 575
- `const timer = window.setInterval(()` — const, line 578
- `const goals = useCachedQuery(["goals_list"], ()` — const, line 585
- `const primaryGoal: GoalDto | null = useMemo(()` — const, line 586
- `const active = (goals.data?.goals ?? []).filter((goal)` — const, line 587
- `const da = a.dueAt ? Date.parse(a.dueAt) : Infinity` — const, line 589
- `const db = b.dueAt ? Date.parse(b.dueAt) : Infinity` — const, line 590
- `const deciding = plan?.deciding === true && !list` — const, line 598
- `const refetchPlan = planQuery.refetch` — const, line 599
- `let reads = 0` — let, line 602
- `const timer = window.setInterval(()` — const, line 603
- `const waitingUntil = plan?.waiting?.until ?? null` — const, line 613
- `const at = Date.parse(waitingUntil)` — const, line 616
- `const timer = window.setTimeout(()` — const, line 618
- `const alive = useRef(true)` — const, line 626
- `const stay = useCallback(<T,>(value: T): T` — const, line 633
- `const startSession = useCallback( async (minutes: number): Promise<SessionSnapshot>` — const, line 638
- `const started = await onStartSession(minutes)` — const, line 640
- `const run = useCallback( async <T,>(work: ()` — const, line 646
- `const runSaying = useCallback( async <T,>(line: string, work: ()` — const, line 663
- `const done = plan ? plan.status !== "open" : false` — const, line 676
- `const current = plan?.blocks.find((block)` — const, line 677
- `const waiting = plan && !done && !current && plan.waiting ? plan.waiting : null` — const, line 678
- `const inProgress = plan && !done && !current ? plan.questionInProgress ?? null : null` — const, line 681
- `const openProblems = useCachedQuery(inProgress ? ["workbench_open_problems"] : null, ()` — const, line 682
- `const inProgressProblem = inProgress ? openProblems.data?.problems.find((problem)` — const, line 683
- `const inProgressItem = inProgress?.practiceItemId ?? null` — const, line 684
- `const rows = plan && !done ? todayRows(plan) : []` — const, line 685
- `async function begin()` — function, line 688
- `const begun = await runSaying(WAITING_COPY.choosingNext, async ()` — const, line 692
- `const started = await startSession(Math.round(plan.minutesBudget))` — const, line 693
- `const first = await api.nextPlanItem(` — const, line 694
- `const result = await runSaying(WAITING_COPY.choosingNext, ()` — const, line 700
- `const action = planStepAction(result?.step,` — const, line 705
- `function afterSomethingElse(result: SomethingElseChosenDto)` — function, line 712
- `const entry = lessonEntryFor(result)` — const, line 713
- `const action = planStepAction(result.step,` — const, line 722
- `async function beginWithoutPlan()` — function, line 730
- `const opened = await runSaying(WAITING_COPY.choosingNext, async ()` — const, line 732
- `const started = session ?? (await startSession(minutes))` — const, line 733
- `const head = await api.getTodayQueue(todayQueueInput(started))` — const, line 734
- `function chooseMinutes(next: number)` — function, line 742
- `async function keepGoing()` — function, line 751
- `const result = await runSaying(WAITING_COPY.addingMore, ()` — const, line 754
- `async function somethingNew(confirm: boolean)` — function, line 769
- `const result = await run(()` — const, line 771
- `async function finish()` — function, line 775
- `const summaryResult = await run(()` — const, line 778
- `async function skipCurrent()` — function, line 782
- `const next = current.items.find((item)` — const, line 788
- `async function openFromList(item: ScheduledItemDto, line: string = WAITING_COPY.openingQuestion)` — function, line 799
- `const started = await runSaying(line, ()` — const, line 802
- `const begun = await runSaying(line, async ()` — const, line 810
- `const started = await startSession(Math.round(plan.minutesBudget))` — const, line 811
- `const result = await api.planLearnerPick(item.practiceItemId, started.sessionId, item.schedulerCandidateId ?? null)` — const, line 812
- `const result = await runSaying(line, ()` — const, line 818
- `const step = result.step` — const, line 820
- `async function practiseGoal()` — function, line 831
- `async function practiseGoalHeld()` — function, line 842
- `const input = queueInput ?? todayQueueInput(session)` — const, line 844
- `const snapshot = await runSaying(WAITING_COPY.findingGoalQuestion, ()` — const, line 845
- `const target = snapshot.sections.flatMap((section)` — const, line 847
- `async function retryFromToday(target:` — function, line 858
- `const result = await run(()` — const, line 859
- `function causeAction(shown: TodayCause): (()` — function, line 863
- `const card = shown.card` — const, line 876
- `const causeLine = cause ? ( <CauseLine cause=` — const, line 884
- `const goalHasQuestions = (primaryGoal?.practicableItemCount ?? 0) > 0` — const, line 893
- `const goalCause = goalNothingReady && !goalHasQuestions ? todayCause(` — const, line 894
- `const onKey = (event: KeyboardEvent)` — const, line 899
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 901
- `const next = stepChoice(choices, minutes, event.key === "ArrowLeft" ? -1 : 1)` — const, line 921
- `const streak = data?.streak ?? snapshotStreak` — const, line 929
- `const streakText = streakLine(streak)` — const, line 930
- `let body: ReactNode` — let, line 933
- `const head = queue?.sections.flatMap((section)` — const, line 975
- `const empty = planWasEmpty(data)` — const, line 989
- `const sentence = plan.kind === "reentry" ? reentrySentence(plan) : planSentence(plan)` — const, line 1046
- `function CauseLine(` — function, line 1178
- `const label = causeActionLabel(cause)` — const, line 1197
- `function OpenLessons(` — function, line 1221
- `let cancelled = false` — let, line 1225
- `function KeepGoingNothing()` — function, line 1249

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `TodayPlace`; references `TodayPlace`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AiConnectionDto`, `DailyPlanDto`, `GoalDto`, `OpenLessonDto`, `PlanLessonOfferStepDto`, `PlanReadingDto`, `PlanStepDto`, `QueueSnapshot`, `ScheduledItemDto`, `SessionEndSummary`, `SessionSnapshot`, `SomethingElseChosenDto`, `SourceLibraryCard`, `StreakSummary`, `WorkbenchOpenProblemDto`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`
- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export; imports `todayQueueInput`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `aboutMinutes`, `planStepAction`, `questionInProgressLine`, `useDailyPlan`, `waitingLine`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `INTERACTIVE_SELECTOR`, `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/todayCause|src/app/todayCause.ts]] — import-or-re-export; imports `GOAL_NOT_UP_TODAY`, `KEEP_GOING_NOTHING_LEAD`, `PLAN_FINISHED`, `PLAN_STOPPED_WITH_MORE`, `TodayCause`, `WHATS_SENT`, `causeActionLabel`, `causeSendsPassages`, `causeSentence`, `continueLessonLine`, `goalCauseSentence`, `todayCause`
- [[Reference/Desktop/TypeScript/app/todayPlan|src/app/todayPlan.ts]] — import-or-re-export; imports `GOAL_NOTHING_READY`, `THREADS_SHOWN`, `TodayThread`, `dayPhrase`, `doneLine`, `fullListWhy`, `onYourOwnWhy`, `planSentence`, `planWasEmpty`, `reentrySentence`, `reentryWhy`, `splitWhy`, `streakLine`, `todayRows`, `todayThreads`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export; imports `AskTarget`
- [[Reference/Desktop/TypeScript/components/GoalCard|src/components/GoalCard.tsx]] — import-or-re-export; imports `GoalCard`
- [[Reference/Desktop/TypeScript/components/GoalWizard|src/components/GoalWizard.tsx]] — import-or-re-export; imports `GoalWizard`
- [[Reference/Desktop/TypeScript/components/InboxStrip|src/components/InboxStrip.tsx]] — import-or-re-export; imports `InboxStrip`
- [[Reference/Desktop/TypeScript/components/QuestionQueue|src/components/QuestionQueue.tsx]] — import-or-re-export; imports `targetForDialogue`
- [[Reference/Desktop/TypeScript/components/Waiting|src/components/Waiting.tsx]] — import-or-re-export; imports `Waiting`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/copy/waiting|src/copy/waiting.ts]] — import-or-re-export; imports `WAITING_COPY`
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

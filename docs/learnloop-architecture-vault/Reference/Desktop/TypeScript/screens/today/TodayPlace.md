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
| Source lines | 1459 |
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

- `export interface TodayPlaceProps` — interface, line 106
- `export function TodayPlace(` — function, line 485

## Internal implementation anchors

- `type TodayThread } from "../../app/todayPlan"` — type, line 79
- `type TodayCause } from "../../app/todayCause"` — type, line 103
- `const LEFT = Symbol("today-left")` — const, line 156
- `const linkButton: CSSProperties =` — const, line 158
- `const dimLink: CSSProperties =` — const, line 168
- `const CAUSE_POLL_MS = 5000` — const, line 172
- `function actionButton(primary = false): CSSProperties` — function, line 174
- `function MinuteChips(` — function, line 186
- `const selected = minutes === value` — const, line 190
- `function enterOnControl(event: KeyboardEvent): boolean` — function, line 219
- `function stepChoice(choices: number[], current: number | null, delta: number): number | undefined` — function, line 223
- `const index = choices.indexOf(current)` — const, line 225
- `function PlanWhy(` — function, line 230
- `const plan = data.plan` — const, line 231
- `const headline = useCachedQuery(data.headlineEnabled === false ? null : ["get_today_headline"], ()` — const, line 232
- `const rows = todayRows(plan)` — const, line 236
- `const reentry = plan.kind === "reentry" ? reentryWhy(plan) : null` — const, line 237
- `const split = splitWhy(plan)` — const, line 238
- `const line = headline.data?.enabled ? headline.data.line ?? null : null` — const, line 239
- `function Threads(` — function, line 281
- `const questions = useCachedQuery(["list_question_queue", "today-threads"], ()` — const, line 292
- `const problems = useCachedQuery(["workbench_open_problems"], ()` — const, line 293
- `const threads = useMemo( ()` — const, line 296
- `function threadAction(thread: TodayThread):` — function, line 304
- `const citation = thread.question.sourceCitation` — const, line 306
- `const target = targetForDialogue(thread.question)` — const, line 308
- `const shown = more ? threads : threads.slice(0, THREADS_SHOWN)` — const, line 313
- `const act = threadAction(thread)` — const, line 318
- `function CapturesLine(` — function, line 346
- `const summary = useCachedQuery(["get_inbox_summary", "today"], ()` — const, line 347
- `const data = summary.data` — const, line 349
- `const something = Boolean(data && ((data.newCount ?? 0) > 0 || (data.deletePending?.length ?? 0) > 0 || data.vaultMismatch))` — const, line 350
- `function PlainList(` — function, line 364
- `const items = useMemo(()` — const, line 389
- `const minutesOf = useMemo(()` — const, line 390
- `const map = new Map<string, number>()` — const, line 391
- `const onKey = (event: KeyboardEvent)` — const, line 401
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 403
- `const item = items[focus]` — const, line 414
- `const minutes = minutesOf.get(item.practiceItemId)` — const, line 451
- `const cold = onYourOwnWhy(item)` — const, line 452
- `const planQuery = useDailyPlan(session?.sessionId ?? null)` — const, line 510
- `const data: DailyPlanDto | null = planQuery.data ?? null` — const, line 511
- `const planOn = data?.enabled === true && data.plan !== null` — const, line 512
- `const plan = planOn ? data!.plan : null` — const, line 513
- `const planOff = data !== null && !planOn` — const, line 514
- `const lineHeld = useRef(false)` — const, line 521
- `const now = new Date()` — const, line 530
- `const summary = useCachedQuery(planOff ? ["get_start_summary"] : null, ()` — const, line 533
- `const offMinutes = session?.availableMinutes ?? chosenMinutes ?? summary.data?.rememberedMinutes ?? null` — const, line 535
- `const minutes = plan ? plan.rememberedMinutes : offMinutes` — const, line 536
- `const choices = plan ? plan.minuteChoices : summary.data?.minuteChoices ?? summary.data?.minutesPresets ?? []` — const, line 537
- `const planDone = plan ? plan.status !== "open" : false` — const, line 542
- `const emptyDay = data !== null && plan !== null && (planDone ? planWasEmpty(data) : todayRows(plan).length === 0 && plan.deciding !== true && !plan.waiting && !plan.questionInProgress)` — const, line 543
- `const queueInput = useMemo( ()` — const, line 554
- `const queueQuery = useCachedQuery( queueInput && (list || planOff || emptyDay || planDone || keptGoingToNothing) ? ["get_today_queue", queueInput] : null, ()` — const, line 564
- `const queue = queueQuery.data ?? null` — const, line 569
- `const retryQueue = useCallback(()` — const, line 573
- `const report = queueQuery.retryReport()` — const, line 574
- `const library = useCachedQuery(["get_source_library"], ()` — const, line 578
- `const noBooks = library.data !== undefined && library.data.sources.length === 0 && (library.data.pending?.length ?? 0) === 0` — const, line 579
- `const listItems = queueQuery.error ? 0 : queue ? queue.sections.reduce((count, section)` — const, line 580
- `const listItemIds = useMemo(()` — const, line 581
- `const listWaiting = useMemo(()` — const, line 583
- `const listNotNow = useMemo(()` — const, line 590
- `const listAskable = listItems === null ? null : Math.max(0, listItems - listNotNow.length)` — const, line 591
- `const moreLeft: boolean | null = !plan || !planDone ? null : plan.blocks.some((block)` — const, line 592
- `const cause: TodayCause | null = emptyDay || (keptGoingToNothing && planOn) ? todayCause(` — const, line 598
- `const refetchLibrary = library.refetch` — const, line 603
- `const refetchQueue = queueQuery.refetch` — const, line 604
- `const onTheWay = cause?.kind === "on_the_way" || cause?.kind === "section_writing" || (cause?.kind === "questions_ready_with_section_work" && cause.writing !== null)` — const, line 605
- `const timer = window.setInterval(()` — const, line 609
- `const causeShown = cause !== null` — const, line 619
- `const goals = useCachedQuery(["goals_list"], ()` — const, line 625
- `const primaryGoal: GoalDto | null = useMemo(()` — const, line 626
- `const active = (goals.data?.goals ?? []).filter((goal)` — const, line 627
- `const da = a.dueAt ? Date.parse(a.dueAt) : Infinity` — const, line 629
- `const db = b.dueAt ? Date.parse(b.dueAt) : Infinity` — const, line 630
- `const deciding = plan?.deciding === true && !list` — const, line 638
- `const refetchPlan = planQuery.refetch` — const, line 639
- `let reads = 0` — let, line 642
- `const timer = window.setInterval(()` — const, line 643
- `const nextPractice = useLatestNextPractice(data?.nextPractice)` — const, line 655
- `const waitingUntil = plan?.waiting?.until ?? null` — const, line 657
- `const at = Date.parse(waitingUntil)` — const, line 660
- `const timer = window.setTimeout(()` — const, line 662
- `const alive = useRef(true)` — const, line 670
- `const stay = useCallback(<T,>(value: T): T` — const, line 677
- `const startSession = useCallback( async (minutes: number): Promise<SessionSnapshot>` — const, line 682
- `const started = await onStartSession(minutes)` — const, line 684
- `const run = useCallback( async <T,>(work: ()` — const, line 690
- `const runSaying = useCallback( async <T,>(line: string, work: ()` — const, line 707
- `const done = plan ? plan.status !== "open" : false` — const, line 720
- `const current = plan?.blocks.find((block)` — const, line 721
- `const waiting = plan && !done && !current && plan.waiting ? plan.waiting : null` — const, line 722
- `const inProgress = plan && !done && !current ? plan.questionInProgress ?? null : null` — const, line 725
- `const openProblems = useCachedQuery(inProgress ? ["workbench_open_problems"] : null, ()` — const, line 726
- `const inProgressProblem = inProgress ? openProblems.data?.problems.find((problem)` — const, line 727
- `const inProgressItem = inProgress?.practiceItemId ?? null` — const, line 728
- `const rows = plan && !done ? todayRows(plan) : []` — const, line 729
- `async function begin()` — function, line 732
- `const begun = await runSaying(WAITING_COPY.choosingNext, async ()` — const, line 736
- `const started = await startSession(Math.round(plan.minutesBudget))` — const, line 737
- `const first = await api.nextPlanItem(` — const, line 738
- `const result = await runSaying(WAITING_COPY.choosingNext, ()` — const, line 744
- `const action = planStepAction(result?.step,` — const, line 749
- `function afterSomethingElse(result: SomethingElseChosenDto)` — function, line 756
- `const entry = lessonEntryFor(result)` — const, line 757
- `const action = planStepAction(result.step,` — const, line 766
- `async function beginWithoutPlan()` — function, line 774
- `const opened = await runSaying(WAITING_COPY.choosingNext, async ()` — const, line 776
- `const started = session ?? (await startSession(minutes))` — const, line 777
- `const head = await api.getTodayQueue(todayQueueInput(started))` — const, line 778
- `function chooseMinutes(next: number)` — function, line 786
- `async function keepGoing()` — function, line 795
- `const result = await runSaying(WAITING_COPY.addingMore, ()` — const, line 798
- `async function somethingNew(confirm: boolean)` — function, line 813
- `const result = await run(()` — const, line 815
- `async function finish()` — function, line 819
- `const summaryResult = await run(()` — const, line 822
- `async function skipCurrent()` — function, line 826
- `const next = current.items.find((item)` — const, line 832
- `async function openFromList(item: ScheduledItemDto, line: string = WAITING_COPY.openingQuestion)` — function, line 843
- `const started = await runSaying(line, ()` — const, line 846
- `const begun = await runSaying(line, async ()` — const, line 854
- `const started = await startSession(Math.round(plan.minutesBudget))` — const, line 855
- `const result = await api.planLearnerPick(item.practiceItemId, started.sessionId, item.schedulerCandidateId ?? null)` — const, line 856
- `const result = await runSaying(line, ()` — const, line 862
- `const step = result.step` — const, line 864
- `async function practiseGoal()` — function, line 875
- `async function practiseGoalHeld()` — function, line 886
- `const input = queueInput ?? todayQueueInput(session)` — const, line 888
- `const snapshot = await runSaying(WAITING_COPY.findingGoalQuestion, ()` — const, line 889
- `const target = snapshot.sections.flatMap((section)` — const, line 891
- `async function retryFromToday(target:` — function, line 902
- `const result = await run(()` — const, line 903
- `async function resumeSection(resumeId: string)` — function, line 908
- `const resumed = await run(()` — const, line 909
- `function causeAction(shown: TodayCause): (()` — function, line 913
- `const item = shown.itemId ? queue?.sections.flatMap((section)` — const, line 922
- `const card = shown.card` — const, line 942
- `function causeSecond(shown: TodayCause): (()` — function, line 951
- `const offersQuestions = cause?.kind === "questions_ready" || cause?.kind === "questions_ready_with_section_work"` — const, line 957
- `const offerBegin = cause && offersQuestions ? causeAction(cause) : null` — const, line 958
- `const underway = causeUnderway(cause ?? (list ? todayCause(` — const, line 961
- `const nothingPlanned = underway ? NO_QUESTIONS_YET : "Nothing planned for today."` — const, line 962
- `const held = cause?.kind === "held" ? null : heldLine(library.data?.sources)` — const, line 965
- `const causeLine = cause ? ( <CauseLine cause=` — const, line 967
- `const goalHasQuestions = (primaryGoal?.practicableItemCount ?? 0) > 0` — const, line 983
- `const goalCause = goalNothingReady && !goalHasQuestions ? todayCause(` — const, line 984
- `const onKey = (event: KeyboardEvent)` — const, line 989
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 991
- `const next = stepChoice(choices, minutes, event.key === "ArrowLeft" ? -1 : 1)` — const, line 1013
- `const streak = data?.streak ?? snapshotStreak` — const, line 1021
- `const streakText = streakLine(streak)` — const, line 1022
- `const nextLines = planOn && data && !list && !finishCardShown && (done || emptyDay) ? nextPracticeLines(nextPractice,` — const, line 1025
- `let body: ReactNode` — let, line 1030
- `const head = queue?.sections.flatMap((section)` — const, line 1074
- `const empty = planWasEmpty(data)` — const, line 1088
- `const sentence = plan.kind === "reentry" ? reentrySentence(plan) : planSentence(plan)` — const, line 1147
- `function CauseLine(` — function, line 1292
- `const label = causeActionLabel(cause)` — const, line 1318
- `const second = causeSecondActionLabel(cause)` — const, line 1319
- `const wait = sentence === undefined ? causeWait(cause) : null` — const, line 1320
- `const detail = useWaitWords(wait ? waitDetailOf(cause) : null, "ago")` — const, line 1322
- `const failed = causeTopicsFailed(cause)` — const, line 1329
- `const failed = causeTopicsFailed(cause)` — const, line 1361
- `function OpenLessons(` — function, line 1425
- `let cancelled = false` — let, line 1429
- `function KeepGoingNothing(` — function, line 1453

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `TodayPlace`; references `TodayPlace`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AiConnectionDto`, `DailyPlanDto`, `GoalDto`, `NextPracticeDto`, `OpenLessonDto`, `PlanLessonOfferStepDto`, `PlanReadingDto`, `PlanStepDto`, `QueueSnapshot`, `ScheduledItemDto`, `SessionEndSummary`, `SessionSnapshot`, `SomethingElseChosenDto`, `SourceLibraryCard`, `StreakSummary`, `WorkbenchOpenProblemDto`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`
- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export; imports `todayQueueInput`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `aboutMinutes`, `planStepAction`, `questionInProgressLine`, `useDailyPlan`, `waitingLine`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `INTERACTIVE_SELECTOR`, `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/nextPractice|src/app/nextPractice.ts]] — import-or-re-export; imports `nextPracticeLines`, `useLatestNextPractice`, `useNextDayRefresh`
- [[Reference/Desktop/TypeScript/app/todayCause|src/app/todayCause.ts]] — import-or-re-export; imports `GOAL_NOT_UP_TODAY`, `KEEP_GOING_NOTHING_LEAD`, `NO_QUESTIONS_YET`, `PLAN_FINISHED`, `PLAN_STOPPED_WITH_MORE`, `TodayCause`, `WHATS_SENT`, `causeActionLabel`, `causeSecondActionLabel`, `causeSendsPassages`, `causeSentence`, `causeTopicsFailed`, `causeUnderway`, `causeWait`, `continueLessonLine`, `goalCauseSentence`, `heldLine`, `notAskableOnList`, `readyWithWorkSentence`, `todayCause`, `waitingOnList`
- [[Reference/Desktop/TypeScript/app/todayPlan|src/app/todayPlan.ts]] — import-or-re-export; imports `GOAL_NOTHING_READY`, `THREADS_SHOWN`, `TodayThread`, `dayPhrase`, `doneLine`, `fullListWhy`, `onYourOwnWhy`, `planSentence`, `planWasEmpty`, `reentrySentence`, `reentryWhy`, `splitWhy`, `streakLine`, `todayRows`, `todayThreads`
- [[Reference/Desktop/TypeScript/app/waitDetail|src/app/waitDetail.ts]] — import-or-re-export; imports `WAIT_DETAILS_LABEL`, `useWaitWords`, `waitDetailOf`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export; imports `AskTarget`
- [[Reference/Desktop/TypeScript/components/GoalCard|src/components/GoalCard.tsx]] — import-or-re-export; imports `GoalCard`
- [[Reference/Desktop/TypeScript/components/GoalWizard|src/components/GoalWizard.tsx]] — import-or-re-export; imports `GoalWizard`
- [[Reference/Desktop/TypeScript/components/InboxStrip|src/components/InboxStrip.tsx]] — import-or-re-export; imports `InboxStrip`
- [[Reference/Desktop/TypeScript/components/QuestionQueue|src/components/QuestionQueue.tsx]] — import-or-re-export; imports `targetForDialogue`
- [[Reference/Desktop/TypeScript/components/Waiting|src/components/Waiting.tsx]] — import-or-re-export; imports `Waiting`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/copy/waiting|src/copy/waiting.ts]] — import-or-re-export; imports `WAITING_COPY`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `ErrorReport`, `errorMessage`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export; imports `subscribeQueueChanged`
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

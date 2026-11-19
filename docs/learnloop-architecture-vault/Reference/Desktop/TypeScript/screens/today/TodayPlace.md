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
| Source lines | 1149 |
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

- `export interface TodayPlaceProps` — interface, line 87
- `export function TodayPlace(` — function, line 452

## Internal implementation anchors

- `type TodayThread } from "../../app/todayPlan"` — type, line 71
- `type TodayCause } from "../../app/todayCause"` — type, line 84
- `const LEFT = Symbol("today-left")` — const, line 129
- `const linkButton: CSSProperties =` — const, line 131
- `const dimLink: CSSProperties =` — const, line 141
- `const CAUSE_POLL_MS = 5000` — const, line 145
- `function actionButton(primary = false): CSSProperties` — function, line 147
- `function MinuteChips(` — function, line 159
- `const selected = minutes === value` — const, line 163
- `function enterOnControl(event: KeyboardEvent): boolean` — function, line 192
- `function stepChoice(choices: number[], current: number | null, delta: number): number | undefined` — function, line 196
- `const index = choices.indexOf(current)` — const, line 198
- `function PlanWhy(` — function, line 203
- `const plan = data.plan` — const, line 204
- `const headline = useCachedQuery(data.headlineEnabled === false ? null : ["get_today_headline"], ()` — const, line 205
- `const rows = todayRows(plan)` — const, line 209
- `const reentry = plan.kind === "reentry" ? reentryWhy(plan) : null` — const, line 210
- `const split = splitWhy(plan)` — const, line 211
- `const line = headline.data?.enabled ? headline.data.line ?? null : null` — const, line 212
- `function Threads(` — function, line 254
- `const questions = useCachedQuery(["list_question_queue", "today-threads"], ()` — const, line 265
- `const problems = useCachedQuery(["workbench_open_problems"], ()` — const, line 266
- `const threads = useMemo( ()` — const, line 269
- `function threadAction(thread: TodayThread):` — function, line 277
- `const citation = thread.question.sourceCitation` — const, line 279
- `const target = targetForDialogue(thread.question)` — const, line 281
- `const shown = more ? threads : threads.slice(0, THREADS_SHOWN)` — const, line 286
- `const act = threadAction(thread)` — const, line 291
- `function CapturesLine(` — function, line 319
- `const summary = useCachedQuery(["get_inbox_summary", "today"], ()` — const, line 320
- `const data = summary.data` — const, line 322
- `const something = Boolean(data && ((data.newCount ?? 0) > 0 || (data.deletePending?.length ?? 0) > 0 || data.vaultMismatch))` — const, line 323
- `function PlainList(` — function, line 337
- `const items = useMemo(()` — const, line 356
- `const minutesOf = useMemo(()` — const, line 357
- `const map = new Map<string, number>()` — const, line 358
- `const onKey = (event: KeyboardEvent)` — const, line 368
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 370
- `const item = items[focus]` — const, line 381
- `const minutes = minutesOf.get(item.practiceItemId)` — const, line 418
- `const cold = onYourOwnWhy(item)` — const, line 419
- `const planQuery = useDailyPlan(session?.sessionId ?? null)` — const, line 474
- `const data: DailyPlanDto | null = planQuery.data ?? null` — const, line 475
- `const planOn = data?.enabled === true && data.plan !== null` — const, line 476
- `const plan = planOn ? data!.plan : null` — const, line 477
- `const planOff = data !== null && !planOn` — const, line 478
- `const now = new Date()` — const, line 488
- `const summary = useCachedQuery(planOff ? ["get_start_summary"] : null, ()` — const, line 491
- `const offMinutes = session?.availableMinutes ?? chosenMinutes ?? summary.data?.rememberedMinutes ?? null` — const, line 493
- `const minutes = plan ? plan.rememberedMinutes : offMinutes` — const, line 494
- `const choices = plan ? plan.minuteChoices : summary.data?.minuteChoices ?? summary.data?.minutesPresets ?? []` — const, line 495
- `const planDone = plan ? plan.status !== "open" : false` — const, line 500
- `const emptyDay = data !== null && plan !== null && (planDone ? planWasEmpty(data) : todayRows(plan).length === 0 && plan.deciding !== true && !plan.waiting && !plan.questionInProgress)` — const, line 501
- `const queueInput = useMemo( ()` — const, line 512
- `const queueQuery = useCachedQuery( queueInput && (list || planOff || emptyDay || keptGoingToNothing) ? ["get_today_queue", queueInput] : null, ()` — const, line 522
- `const queue = queueQuery.data ?? null` — const, line 527
- `const retryQueue = useCallback(()` — const, line 531
- `const report = queueQuery.retryReport()` — const, line 532
- `const library = useCachedQuery(["get_source_library"], ()` — const, line 536
- `const noBooks = library.data !== undefined && library.data.sources.length === 0 && (library.data.pending?.length ?? 0) === 0` — const, line 537
- `const listItems = queueQuery.error ? 0 : queue ? queue.sections.reduce((count, section)` — const, line 538
- `const cause: TodayCause | null = emptyDay || (keptGoingToNothing && planOn) ? todayCause(` — const, line 540
- `const refetchLibrary = library.refetch` — const, line 545
- `const refetchQueue = queueQuery.refetch` — const, line 546
- `const onTheWay = cause?.kind === "on_the_way"` — const, line 547
- `const timer = window.setInterval(()` — const, line 550
- `const goals = useCachedQuery(["goals_list"], ()` — const, line 557
- `const primaryGoal: GoalDto | null = useMemo(()` — const, line 558
- `const active = (goals.data?.goals ?? []).filter((goal)` — const, line 559
- `const da = a.dueAt ? Date.parse(a.dueAt) : Infinity` — const, line 561
- `const db = b.dueAt ? Date.parse(b.dueAt) : Infinity` — const, line 562
- `const deciding = plan?.deciding === true && !list` — const, line 570
- `const refetchPlan = planQuery.refetch` — const, line 571
- `let reads = 0` — let, line 574
- `const timer = window.setInterval(()` — const, line 575
- `const waitingUntil = plan?.waiting?.until ?? null` — const, line 585
- `const at = Date.parse(waitingUntil)` — const, line 588
- `const timer = window.setTimeout(()` — const, line 590
- `const alive = useRef(true)` — const, line 598
- `const stay = useCallback(<T,>(value: T): T` — const, line 605
- `const startSession = useCallback( async (minutes: number): Promise<SessionSnapshot>` — const, line 610
- `const started = await onStartSession(minutes)` — const, line 612
- `const run = useCallback( async <T,>(work: ()` — const, line 618
- `const done = plan ? plan.status !== "open" : false` — const, line 634
- `const current = plan?.blocks.find((block)` — const, line 635
- `const waiting = plan && !done && !current && plan.waiting ? plan.waiting : null` — const, line 636
- `const inProgress = plan && !done && !current ? plan.questionInProgress ?? null : null` — const, line 639
- `const openProblems = useCachedQuery(inProgress ? ["workbench_open_problems"] : null, ()` — const, line 640
- `const inProgressProblem = inProgress ? openProblems.data?.problems.find((problem)` — const, line 641
- `const inProgressItem = inProgress?.practiceItemId ?? null` — const, line 642
- `const rows = plan && !done ? todayRows(plan) : []` — const, line 643
- `async function begin()` — function, line 646
- `const begun = await run(async ()` — const, line 650
- `const started = await startSession(Math.round(plan.minutesBudget))` — const, line 651
- `const first = await api.nextPlanItem(` — const, line 652
- `const result = await run(()` — const, line 658
- `const action = planStepAction(result?.step,` — const, line 659
- `function afterSomethingElse(result: SomethingElseChosenDto)` — function, line 666
- `const entry = lessonEntryFor(result)` — const, line 667
- `const action = planStepAction(result.step,` — const, line 676
- `async function beginWithoutPlan()` — function, line 684
- `const opened = await run(async ()` — const, line 686
- `const started = session ?? (await startSession(minutes))` — const, line 687
- `const head = await api.getTodayQueue(todayQueueInput(started))` — const, line 688
- `function chooseMinutes(next: number)` — function, line 696
- `async function keepGoing()` — function, line 705
- `const result = await run(()` — const, line 708
- `async function somethingNew(confirm: boolean)` — function, line 723
- `const result = await run(()` — const, line 725
- `async function finish()` — function, line 729
- `const summaryResult = await run(()` — const, line 732
- `async function skipCurrent()` — function, line 736
- `const next = current.items.find((item)` — const, line 742
- `async function openFromList(item: ScheduledItemDto)` — function, line 753
- `const started = await run(()` — const, line 756
- `const begun = await run(async ()` — const, line 764
- `const started = await startSession(Math.round(plan.minutesBudget))` — const, line 765
- `const result = await api.planLearnerPick(item.practiceItemId, started.sessionId, item.schedulerCandidateId ?? null)` — const, line 766
- `const result = await run(()` — const, line 772
- `const step = result.step` — const, line 774
- `async function practiseGoal()` — function, line 785
- `const input = queueInput ?? todayQueueInput(session)` — const, line 787
- `const snapshot = await run(()` — const, line 788
- `const target = snapshot.sections.flatMap((section)` — const, line 790
- `async function retryFromToday(target:` — function, line 801
- `const result = await run(()` — const, line 802
- `function causeAction(shown: TodayCause): (()` — function, line 806
- `const card = shown.card` — const, line 819
- `const causeLine = cause ? ( <CauseLine cause=` — const, line 827
- `const goalHasQuestions = (primaryGoal?.practicableItemCount ?? 0) > 0` — const, line 836
- `const goalCause = goalNothingReady && !goalHasQuestions ? todayCause(` — const, line 837
- `const onKey = (event: KeyboardEvent)` — const, line 842
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 844
- `const next = stepChoice(choices, minutes, event.key === "ArrowLeft" ? -1 : 1)` — const, line 864
- `const streak = data?.streak ?? snapshotStreak` — const, line 872
- `const streakText = streakLine(streak)` — const, line 873
- `let body: ReactNode` — let, line 876
- `const head = queue?.sections.flatMap((section)` — const, line 913
- `const empty = planWasEmpty(data)` — const, line 927
- `const sentence = plan.kind === "reentry" ? reentrySentence(plan) : planSentence(plan)` — const, line 972
- `function CauseLine(` — function, line 1102
- `const label = causeActionLabel(cause)` — const, line 1121
- `function KeepGoingNothing()` — function, line 1143

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `TodayPlace`; references `TodayPlace`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AiConnectionDto`, `DailyPlanDto`, `GoalDto`, `PlanReadingDto`, `PlanStepDto`, `QueueSnapshot`, `ScheduledItemDto`, `SessionEndSummary`, `SessionSnapshot`, `SomethingElseChosenDto`, `SourceLibraryCard`, `StreakSummary`, `WorkbenchOpenProblemDto`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`
- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export; imports `todayQueueInput`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `aboutMinutes`, `planStepAction`, `questionInProgressLine`, `useDailyPlan`, `waitingLine`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `INTERACTIVE_SELECTOR`, `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/todayCause|src/app/todayCause.ts]] — import-or-re-export; imports `GOAL_NOT_UP_TODAY`, `KEEP_GOING_NOTHING_LEAD`, `PLAN_FINISHED`, `TodayCause`, `WHATS_SENT`, `causeActionLabel`, `causeSendsPassages`, `causeSentence`, `goalCauseSentence`, `todayCause`
- [[Reference/Desktop/TypeScript/app/todayPlan|src/app/todayPlan.ts]] — import-or-re-export; imports `GOAL_NOTHING_READY`, `THREADS_SHOWN`, `TodayThread`, `dayPhrase`, `doneLine`, `fullListWhy`, `onYourOwnWhy`, `planSentence`, `planWasEmpty`, `reentrySentence`, `reentryWhy`, `splitWhy`, `streakLine`, `todayRows`, `todayThreads`
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

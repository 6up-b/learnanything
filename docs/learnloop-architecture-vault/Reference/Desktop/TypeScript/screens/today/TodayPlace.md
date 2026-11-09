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
| Source lines | 947 |
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

- `export interface TodayPlaceProps` — interface, line 72
- `export function TodayPlace(` — function, line 424

## Internal implementation anchors

- `type TodayThread } from "../../app/todayPlan"` — type, line 68
- `const LEFT = Symbol("today-left")` — const, line 105
- `const linkButton: CSSProperties =` — const, line 107
- `const dimLink: CSSProperties =` — const, line 117
- `function actionButton(primary = false): CSSProperties` — function, line 119
- `function MinuteChips(` — function, line 131
- `const selected = minutes === value` — const, line 135
- `function enterOnControl(event: KeyboardEvent): boolean` — function, line 164
- `function stepChoice(choices: number[], current: number | null, delta: number): number | undefined` — function, line 168
- `const index = choices.indexOf(current)` — const, line 170
- `function PlanWhy(` — function, line 175
- `const plan = data.plan` — const, line 176
- `const headline = useCachedQuery(data.headlineEnabled === false ? null : ["get_today_headline"], ()` — const, line 177
- `const rows = todayRows(plan)` — const, line 181
- `const reentry = plan.kind === "reentry" ? reentryWhy(plan) : null` — const, line 182
- `const split = splitWhy(plan)` — const, line 183
- `const line = headline.data?.enabled ? headline.data.line ?? null : null` — const, line 184
- `function Threads(` — function, line 226
- `const questions = useCachedQuery(["list_question_queue", "today-threads"], ()` — const, line 237
- `const problems = useCachedQuery(["workbench_open_problems"], ()` — const, line 238
- `const threads = useMemo( ()` — const, line 241
- `function threadAction(thread: TodayThread):` — function, line 249
- `const citation = thread.question.sourceCitation` — const, line 251
- `const target = targetForDialogue(thread.question)` — const, line 253
- `const shown = more ? threads : threads.slice(0, THREADS_SHOWN)` — const, line 258
- `const act = threadAction(thread)` — const, line 263
- `function CapturesLine(` — function, line 291
- `const summary = useCachedQuery(["get_inbox_summary", "today"], ()` — const, line 292
- `const data = summary.data` — const, line 294
- `const something = Boolean(data && ((data.newCount ?? 0) > 0 || (data.deletePending?.length ?? 0) > 0 || data.vaultMismatch))` — const, line 295
- `function PlainList(` — function, line 309
- `const items = useMemo(()` — const, line 328
- `const minutesOf = useMemo(()` — const, line 329
- `const map = new Map<string, number>()` — const, line 330
- `const onKey = (event: KeyboardEvent)` — const, line 340
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 342
- `const item = items[focus]` — const, line 353
- `const minutes = minutesOf.get(item.practiceItemId)` — const, line 390
- `const cold = onYourOwnWhy(item)` — const, line 391
- `const planQuery = useDailyPlan(session?.sessionId ?? null)` — const, line 442
- `const data: DailyPlanDto | null = planQuery.data ?? null` — const, line 443
- `const planOn = data?.enabled === true && data.plan !== null` — const, line 444
- `const plan = planOn ? data!.plan : null` — const, line 445
- `const planOff = data !== null && !planOn` — const, line 446
- `const now = new Date()` — const, line 452
- `const summary = useCachedQuery(planOff ? ["get_start_summary"] : null, ()` — const, line 455
- `const offMinutes = session?.availableMinutes ?? chosenMinutes ?? summary.data?.rememberedMinutes ?? null` — const, line 457
- `const minutes = plan ? plan.rememberedMinutes : offMinutes` — const, line 458
- `const choices = plan ? plan.minuteChoices : summary.data?.minuteChoices ?? summary.data?.minutesPresets ?? []` — const, line 459
- `const queueInput = useMemo( ()` — const, line 465
- `const queueQuery = useCachedQuery( queueInput && (list || planOff) ? ["get_today_queue", queueInput] : null, ()` — const, line 475
- `const queue = queueQuery.data ?? null` — const, line 480
- `const retryQueue = useCallback(()` — const, line 484
- `const report = queueQuery.retryReport()` — const, line 485
- `const library = useCachedQuery(["get_source_library"], ()` — const, line 489
- `const noBooks = library.data !== undefined && library.data.sources.length === 0 && (library.data.pending?.length ?? 0) === 0` — const, line 490
- `const goals = useCachedQuery(["goals_list"], ()` — const, line 492
- `const primaryGoal: GoalDto | null = useMemo(()` — const, line 493
- `const active = (goals.data?.goals ?? []).filter((goal)` — const, line 494
- `const da = a.dueAt ? Date.parse(a.dueAt) : Infinity` — const, line 496
- `const db = b.dueAt ? Date.parse(b.dueAt) : Infinity` — const, line 497
- `const deciding = plan?.deciding === true && !list` — const, line 505
- `const refetchPlan = planQuery.refetch` — const, line 506
- `let reads = 0` — let, line 509
- `const timer = window.setInterval(()` — const, line 510
- `const waitingUntil = plan?.waiting?.until ?? null` — const, line 520
- `const at = Date.parse(waitingUntil)` — const, line 523
- `const timer = window.setTimeout(()` — const, line 525
- `const alive = useRef(true)` — const, line 533
- `const stay = useCallback(<T,>(value: T): T` — const, line 540
- `const startSession = useCallback( async (minutes: number): Promise<SessionSnapshot>` — const, line 545
- `const started = await onStartSession(minutes)` — const, line 547
- `const run = useCallback( async <T,>(work: ()` — const, line 553
- `const done = plan ? plan.status !== "open" : false` — const, line 569
- `const current = plan?.blocks.find((block)` — const, line 570
- `const waiting = plan && !done && !current && plan.waiting ? plan.waiting : null` — const, line 571
- `const inProgress = plan && !done && !current ? plan.questionInProgress ?? null : null` — const, line 574
- `const openProblems = useCachedQuery(inProgress ? ["workbench_open_problems"] : null, ()` — const, line 575
- `const inProgressProblem = inProgress ? openProblems.data?.problems.find((problem)` — const, line 576
- `const inProgressItem = inProgress?.practiceItemId ?? null` — const, line 577
- `const rows = plan && !done ? todayRows(plan) : []` — const, line 578
- `async function begin()` — function, line 581
- `const begun = await run(async ()` — const, line 585
- `const started = await startSession(Math.round(plan.minutesBudget))` — const, line 586
- `const first = await api.nextPlanItem(` — const, line 587
- `const result = await run(()` — const, line 593
- `const action = planStepAction(result?.step,` — const, line 594
- `function afterSomethingElse(result: SomethingElseChosenDto)` — function, line 601
- `const entry = lessonEntryFor(result)` — const, line 602
- `const action = planStepAction(result.step,` — const, line 611
- `async function beginWithoutPlan()` — function, line 619
- `const opened = await run(async ()` — const, line 621
- `const started = session ?? (await startSession(minutes))` — const, line 622
- `const head = await api.getTodayQueue(todayQueueInput(started))` — const, line 623
- `function chooseMinutes(next: number)` — function, line 631
- `async function keepGoing()` — function, line 640
- `async function somethingNew(confirm: boolean)` — function, line 645
- `const result = await run(()` — const, line 646
- `async function finish()` — function, line 650
- `const summaryResult = await run(()` — const, line 653
- `async function skipCurrent()` — function, line 657
- `const next = current.items.find((item)` — const, line 663
- `async function openFromList(item: ScheduledItemDto)` — function, line 674
- `const started = await run(()` — const, line 677
- `const begun = await run(async ()` — const, line 685
- `const started = await startSession(Math.round(plan.minutesBudget))` — const, line 686
- `const result = await api.planLearnerPick(item.practiceItemId, started.sessionId, item.schedulerCandidateId ?? null)` — const, line 687
- `const result = await run(()` — const, line 693
- `const step = result.step` — const, line 695
- `async function practiseGoal()` — function, line 706
- `const input = queueInput ?? todayQueueInput(session)` — const, line 707
- `const snapshot = await run(()` — const, line 708
- `const target = snapshot?.sections.flatMap((section)` — const, line 709
- `const onKey = (event: KeyboardEvent)` — const, line 718
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 720
- `const next = stepChoice(choices, minutes, event.key === "ArrowLeft" ? -1 : 1)` — const, line 740
- `const streak = data?.streak ?? snapshotStreak` — const, line 748
- `const streakText = streakLine(streak)` — const, line 749
- `let body: ReactNode` — let, line 752
- `const head = queue?.sections.flatMap((section)` — const, line 789
- `const empty = planWasEmpty(data)` — const, line 803
- `const sentence = plan.kind === "reentry" ? reentrySentence(plan) : planSentence(plan)` — const, line 841

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
- [[Reference/Desktop/TypeScript/app/todayPlan|src/app/todayPlan.ts]] — import-or-re-export; imports `THREADS_SHOWN`, `TodayThread`, `dayPhrase`, `doneLine`, `fullListWhy`, `onYourOwnWhy`, `planSentence`, `planWasEmpty`, `reentrySentence`, `reentryWhy`, `splitWhy`, `streakLine`, `todayRows`, `todayThreads`
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

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
source_commit: "86021e6b79512c86957d2bb83a488e23a3818a2f"
source_commit_timestamp: "2026-11-09T03:09:29-05:00"
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
| Source lines | 922 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/today/_area|TypeScript/screens/today]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `86021e6b79512c86957d2bb83a488e23a3818a2f` |
| Commit timestamp | `2026-11-09T03:09:29-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]]

## Public API

- `export interface TodayPlaceProps` — interface, line 70
- `export function TodayPlace(` — function, line 422

## Internal implementation anchors

- `type TodayThread } from "../../app/todayPlan"` — type, line 66
- `const LEFT = Symbol("today-left")` — const, line 103
- `const linkButton: CSSProperties =` — const, line 105
- `const dimLink: CSSProperties =` — const, line 115
- `function actionButton(primary = false): CSSProperties` — function, line 117
- `function MinuteChips(` — function, line 129
- `const selected = minutes === value` — const, line 133
- `function enterOnControl(event: KeyboardEvent): boolean` — function, line 162
- `function stepChoice(choices: number[], current: number | null, delta: number): number | undefined` — function, line 166
- `const index = choices.indexOf(current)` — const, line 168
- `function PlanWhy(` — function, line 173
- `const plan = data.plan` — const, line 174
- `const headline = useCachedQuery(data.headlineEnabled === false ? null : ["get_today_headline"], ()` — const, line 175
- `const rows = todayRows(plan)` — const, line 179
- `const reentry = plan.kind === "reentry" ? reentryWhy(plan) : null` — const, line 180
- `const split = splitWhy(plan)` — const, line 181
- `const line = headline.data?.enabled ? headline.data.line ?? null : null` — const, line 182
- `function Threads(` — function, line 224
- `const questions = useCachedQuery(["list_question_queue", "today-threads"], ()` — const, line 235
- `const problems = useCachedQuery(["workbench_open_problems"], ()` — const, line 236
- `const threads = useMemo( ()` — const, line 239
- `function threadAction(thread: TodayThread):` — function, line 247
- `const citation = thread.question.sourceCitation` — const, line 249
- `const target = targetForDialogue(thread.question)` — const, line 251
- `const shown = more ? threads : threads.slice(0, THREADS_SHOWN)` — const, line 256
- `const act = threadAction(thread)` — const, line 261
- `function CapturesLine(` — function, line 289
- `const summary = useCachedQuery(["get_inbox_summary", "today"], ()` — const, line 290
- `const data = summary.data` — const, line 292
- `const something = Boolean(data && ((data.newCount ?? 0) > 0 || (data.deletePending?.length ?? 0) > 0 || data.vaultMismatch))` — const, line 293
- `function PlainList(` — function, line 307
- `const items = useMemo(()` — const, line 326
- `const minutesOf = useMemo(()` — const, line 327
- `const map = new Map<string, number>()` — const, line 328
- `const onKey = (event: KeyboardEvent)` — const, line 338
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 340
- `const item = items[focus]` — const, line 351
- `const minutes = minutesOf.get(item.practiceItemId)` — const, line 388
- `const cold = onYourOwnWhy(item)` — const, line 389
- `const planQuery = useDailyPlan(session?.sessionId ?? null)` — const, line 440
- `const data: DailyPlanDto | null = planQuery.data ?? null` — const, line 441
- `const planOn = data?.enabled === true && data.plan !== null` — const, line 442
- `const plan = planOn ? data!.plan : null` — const, line 443
- `const planOff = data !== null && !planOn` — const, line 444
- `const now = new Date()` — const, line 450
- `const summary = useCachedQuery(planOff ? ["get_start_summary"] : null, ()` — const, line 453
- `const offMinutes = session?.availableMinutes ?? chosenMinutes ?? summary.data?.rememberedMinutes ?? null` — const, line 455
- `const minutes = plan ? plan.rememberedMinutes : offMinutes` — const, line 456
- `const choices = plan ? plan.minuteChoices : summary.data?.minuteChoices ?? summary.data?.minutesPresets ?? []` — const, line 457
- `const queueInput = useMemo( ()` — const, line 463
- `const queueQuery = useCachedQuery( queueInput && (list || planOff) ? ["get_today_queue", queueInput] : null, ()` — const, line 473
- `const queue = queueQuery.data ?? null` — const, line 478
- `const retryQueue = useCallback(()` — const, line 482
- `const report = queueQuery.retryReport()` — const, line 483
- `const library = useCachedQuery(["get_source_library"], ()` — const, line 487
- `const noBooks = library.data !== undefined && library.data.sources.length === 0 && (library.data.pending?.length ?? 0) === 0` — const, line 488
- `const goals = useCachedQuery(["goals_list"], ()` — const, line 490
- `const primaryGoal: GoalDto | null = useMemo(()` — const, line 491
- `const active = (goals.data?.goals ?? []).filter((goal)` — const, line 492
- `const da = a.dueAt ? Date.parse(a.dueAt) : Infinity` — const, line 494
- `const db = b.dueAt ? Date.parse(b.dueAt) : Infinity` — const, line 495
- `const deciding = plan?.deciding === true && !list` — const, line 503
- `const refetchPlan = planQuery.refetch` — const, line 504
- `let reads = 0` — let, line 507
- `const timer = window.setInterval(()` — const, line 508
- `const waitingUntil = plan?.waiting?.until ?? null` — const, line 518
- `const at = Date.parse(waitingUntil)` — const, line 521
- `const timer = window.setTimeout(()` — const, line 523
- `const alive = useRef(true)` — const, line 531
- `const stay = useCallback(<T,>(value: T): T` — const, line 538
- `const startSession = useCallback( async (minutes: number): Promise<SessionSnapshot>` — const, line 543
- `const started = await onStartSession(minutes)` — const, line 545
- `const run = useCallback( async <T,>(work: ()` — const, line 551
- `const done = plan ? plan.status !== "open" : false` — const, line 567
- `const current = plan?.blocks.find((block)` — const, line 568
- `const waiting = plan && !done && !current && plan.waiting ? plan.waiting : null` — const, line 569
- `const inProgress = plan && !done && !current ? plan.questionInProgress ?? null : null` — const, line 572
- `const openProblems = useCachedQuery(inProgress ? ["workbench_open_problems"] : null, ()` — const, line 573
- `const inProgressProblem = inProgress ? openProblems.data?.problems.find((problem)` — const, line 574
- `const inProgressItem = inProgress?.practiceItemId ?? null` — const, line 575
- `const rows = plan && !done ? todayRows(plan) : []` — const, line 576
- `async function begin()` — function, line 579
- `const begun = await run(async ()` — const, line 583
- `const started = await startSession(Math.round(plan.minutesBudget))` — const, line 584
- `const first = await api.nextPlanItem(` — const, line 585
- `const result = await run(()` — const, line 591
- `const action = planStepAction(result?.step,` — const, line 592
- `async function beginWithoutPlan()` — function, line 599
- `const opened = await run(async ()` — const, line 601
- `const started = session ?? (await startSession(minutes))` — const, line 602
- `const head = await api.getTodayQueue(todayQueueInput(started))` — const, line 603
- `function chooseMinutes(next: number)` — function, line 611
- `async function keepGoing()` — function, line 620
- `async function somethingNew(confirm: boolean)` — function, line 625
- `const result = await run(()` — const, line 626
- `async function finish()` — function, line 630
- `const summaryResult = await run(()` — const, line 633
- `async function skipCurrent()` — function, line 637
- `const next = current.items.find((item)` — const, line 643
- `async function openFromList(item: ScheduledItemDto)` — function, line 654
- `const started = await run(()` — const, line 657
- `const begun = await run(async ()` — const, line 665
- `const started = await startSession(Math.round(plan.minutesBudget))` — const, line 666
- `const result = await api.planLearnerPick(item.practiceItemId, started.sessionId, item.schedulerCandidateId ?? null)` — const, line 667
- `const result = await run(()` — const, line 673
- `const step = result.step` — const, line 675
- `async function practiseGoal()` — function, line 686
- `const input = queueInput ?? todayQueueInput(session)` — const, line 687
- `const snapshot = await run(()` — const, line 688
- `const target = snapshot?.sections.flatMap((section)` — const, line 689
- `const onKey = (event: KeyboardEvent)` — const, line 698
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 700
- `const next = stepChoice(choices, minutes, event.key === "ArrowLeft" ? -1 : 1)` — const, line 720
- `const streak = data?.streak ?? snapshotStreak` — const, line 728
- `const streakText = streakLine(streak)` — const, line 729
- `let body: ReactNode` — let, line 732
- `const head = queue?.sections.flatMap((section)` — const, line 769
- `const empty = planWasEmpty(data)` — const, line 783
- `const sentence = plan.kind === "reentry" ? reentrySentence(plan) : planSentence(plan)` — const, line 821

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `TodayPlace`; references `TodayPlace`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DailyPlanDto`, `GoalDto`, `PlanReadingDto`, `PlanStepDto`, `QueueSnapshot`, `ScheduledItemDto`, `SessionEndSummary`, `SessionSnapshot`, `StreakSummary`, `WorkbenchOpenProblemDto`
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

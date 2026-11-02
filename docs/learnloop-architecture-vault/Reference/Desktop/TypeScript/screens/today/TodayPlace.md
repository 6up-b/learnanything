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
source_commit: "b81f5d14d8754403548d7013038ab7539547bb34"
source_commit_timestamp: "2026-10-25T02:53:03-04:00"
source_worktree_state: "staged-or-mixed"
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
| Source lines | 902 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/today/_area|TypeScript/screens/today]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `staged-or-mixed` |
| Source commit | `b81f5d14d8754403548d7013038ab7539547bb34` |
| Commit timestamp | `2026-10-25T02:53:03-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]]

## Public API

- `export interface TodayPlaceProps` — interface, line 68
- `export function TodayPlace(` — function, line 420

## Internal implementation anchors

- `type TodayThread } from "../../app/todayPlan"` — type, line 64
- `const LEFT = Symbol("today-left")` — const, line 101
- `const linkButton: CSSProperties =` — const, line 103
- `const dimLink: CSSProperties =` — const, line 113
- `function actionButton(primary = false): CSSProperties` — function, line 115
- `function MinuteChips(` — function, line 127
- `const selected = minutes === value` — const, line 131
- `function enterOnControl(event: KeyboardEvent): boolean` — function, line 160
- `function stepChoice(choices: number[], current: number | null, delta: number): number | undefined` — function, line 164
- `const index = choices.indexOf(current)` — const, line 166
- `function PlanWhy(` — function, line 171
- `const plan = data.plan` — const, line 172
- `const headline = useCachedQuery(data.headlineEnabled === false ? null : ["get_today_headline"], ()` — const, line 173
- `const rows = todayRows(plan)` — const, line 177
- `const reentry = plan.kind === "reentry" ? reentryWhy(plan) : null` — const, line 178
- `const split = splitWhy(plan)` — const, line 179
- `const line = headline.data?.enabled ? headline.data.line ?? null : null` — const, line 180
- `function Threads(` — function, line 222
- `const questions = useCachedQuery(["list_question_queue", "today-threads"], ()` — const, line 233
- `const problems = useCachedQuery(["workbench_open_problems"], ()` — const, line 234
- `const threads = useMemo( ()` — const, line 237
- `function threadAction(thread: TodayThread):` — function, line 245
- `const citation = thread.question.sourceCitation` — const, line 247
- `const target = targetForDialogue(thread.question)` — const, line 249
- `const shown = more ? threads : threads.slice(0, THREADS_SHOWN)` — const, line 254
- `const act = threadAction(thread)` — const, line 259
- `function CapturesLine(` — function, line 287
- `const summary = useCachedQuery(["get_inbox_summary", "today"], ()` — const, line 288
- `const data = summary.data` — const, line 290
- `const something = Boolean(data && ((data.newCount ?? 0) > 0 || (data.deletePending?.length ?? 0) > 0 || data.vaultMismatch))` — const, line 291
- `function PlainList(` — function, line 305
- `const items = useMemo(()` — const, line 324
- `const minutesOf = useMemo(()` — const, line 325
- `const map = new Map<string, number>()` — const, line 326
- `const onKey = (event: KeyboardEvent)` — const, line 336
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 338
- `const item = items[focus]` — const, line 349
- `const minutes = minutesOf.get(item.practiceItemId)` — const, line 386
- `const cold = onYourOwnWhy(item)` — const, line 387
- `const planQuery = useDailyPlan(session?.sessionId ?? null)` — const, line 438
- `const data: DailyPlanDto | null = planQuery.data ?? null` — const, line 439
- `const planOn = data?.enabled === true && data.plan !== null` — const, line 440
- `const plan = planOn ? data!.plan : null` — const, line 441
- `const planOff = data !== null && !planOn` — const, line 442
- `const now = new Date()` — const, line 448
- `const summary = useCachedQuery(planOff ? ["get_start_summary"] : null, ()` — const, line 451
- `const offMinutes = session?.availableMinutes ?? chosenMinutes ?? summary.data?.rememberedMinutes ?? null` — const, line 453
- `const minutes = plan ? plan.rememberedMinutes : offMinutes` — const, line 454
- `const choices = plan ? plan.minuteChoices : summary.data?.minuteChoices ?? summary.data?.minutesPresets ?? []` — const, line 455
- `const queueInput = useMemo( ()` — const, line 461
- `const queueQuery = useCachedQuery( queueInput && (list || planOff) ? ["get_today_queue", queueInput] : null, ()` — const, line 471
- `const queue = queueQuery.data ?? null` — const, line 476
- `const retryQueue = useCallback(()` — const, line 480
- `const report = queueQuery.retryReport()` — const, line 481
- `const library = useCachedQuery(["get_source_library"], ()` — const, line 485
- `const noBooks = library.data !== undefined && library.data.sources.length === 0 && (library.data.pending?.length ?? 0) === 0` — const, line 486
- `const goals = useCachedQuery(["goals_list"], ()` — const, line 488
- `const primaryGoal: GoalDto | null = useMemo(()` — const, line 489
- `const active = (goals.data?.goals ?? []).filter((goal)` — const, line 490
- `const da = a.dueAt ? Date.parse(a.dueAt) : Infinity` — const, line 492
- `const db = b.dueAt ? Date.parse(b.dueAt) : Infinity` — const, line 493
- `const deciding = plan?.deciding === true && !list` — const, line 501
- `const refetchPlan = planQuery.refetch` — const, line 502
- `let reads = 0` — let, line 505
- `const timer = window.setInterval(()` — const, line 506
- `const waitingUntil = plan?.waiting?.until ?? null` — const, line 516
- `const at = Date.parse(waitingUntil)` — const, line 519
- `const timer = window.setTimeout(()` — const, line 521
- `const alive = useRef(true)` — const, line 529
- `const stay = useCallback(<T,>(value: T): T` — const, line 536
- `const startSession = useCallback( async (minutes: number): Promise<SessionSnapshot>` — const, line 541
- `const started = await onStartSession(minutes)` — const, line 543
- `const run = useCallback( async <T,>(work: ()` — const, line 549
- `const done = plan ? plan.status !== "open" : false` — const, line 565
- `const current = plan?.blocks.find((block)` — const, line 566
- `const waiting = plan && !done && !current && plan.waiting ? plan.waiting : null` — const, line 567
- `const rows = plan && !done ? todayRows(plan) : []` — const, line 568
- `async function begin()` — function, line 571
- `const begun = await run(async ()` — const, line 575
- `const started = await startSession(Math.round(plan.minutesBudget))` — const, line 576
- `const first = await api.nextPlanItem(` — const, line 577
- `const result = await run(()` — const, line 583
- `const action = planStepAction(result?.step,` — const, line 584
- `async function beginWithoutPlan()` — function, line 591
- `const opened = await run(async ()` — const, line 593
- `const started = session ?? (await startSession(minutes))` — const, line 594
- `const head = await api.getTodayQueue(todayQueueInput(started))` — const, line 595
- `function chooseMinutes(next: number)` — function, line 603
- `async function keepGoing()` — function, line 612
- `async function somethingNew(confirm: boolean)` — function, line 617
- `const result = await run(()` — const, line 618
- `async function finish()` — function, line 622
- `const summaryResult = await run(()` — const, line 625
- `async function skipCurrent()` — function, line 629
- `const next = current.items.find((item)` — const, line 635
- `async function openFromList(item: ScheduledItemDto)` — function, line 646
- `const started = await run(()` — const, line 649
- `const begun = await run(async ()` — const, line 657
- `const started = await startSession(Math.round(plan.minutesBudget))` — const, line 658
- `const result = await api.planLearnerPick(item.practiceItemId, started.sessionId, item.schedulerCandidateId ?? null)` — const, line 659
- `const result = await run(()` — const, line 665
- `const step = result.step` — const, line 667
- `async function practiseGoal()` — function, line 678
- `const input = queueInput ?? todayQueueInput(session)` — const, line 679
- `const snapshot = await run(()` — const, line 680
- `const target = snapshot?.sections.flatMap((section)` — const, line 681
- `const onKey = (event: KeyboardEvent)` — const, line 690
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 692
- `const next = stepChoice(choices, minutes, event.key === "ArrowLeft" ? -1 : 1)` — const, line 712
- `const streak = data?.streak ?? snapshotStreak` — const, line 720
- `const streakText = streakLine(streak)` — const, line 721
- `let body: ReactNode` — let, line 724
- `const head = queue?.sections.flatMap((section)` — const, line 761
- `const empty = planWasEmpty(data)` — const, line 775
- `const sentence = plan.kind === "reentry" ? reentrySentence(plan) : planSentence(plan)` — const, line 813

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
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `aboutMinutes`, `planStepAction`, `useDailyPlan`, `waitingLine`
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
- [[Reference/Desktop/TypeScript/screens/today/LessonSuggestionCard|src/screens/today/LessonSuggestionCard.tsx]] — import-or-re-export; imports `LessonSuggestionCard`

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

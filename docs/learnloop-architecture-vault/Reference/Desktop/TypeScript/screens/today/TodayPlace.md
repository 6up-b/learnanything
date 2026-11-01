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
| Source lines | 891 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/today/_area|TypeScript/screens/today]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `b81f5d14d8754403548d7013038ab7539547bb34` |
| Commit timestamp | `2026-10-25T02:53:03-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]]

## Public API

- `export interface TodayPlaceProps` — interface, line 65
- `export function TodayPlace(` — function, line 415

## Internal implementation anchors

- `type TodayThread } from "../../app/todayPlan"` — type, line 61
- `const LEFT = Symbol("today-left")` — const, line 96
- `const linkButton: CSSProperties =` — const, line 98
- `const dimLink: CSSProperties =` — const, line 108
- `function actionButton(primary = false): CSSProperties` — function, line 110
- `function MinuteChips(` — function, line 122
- `const selected = minutes === value` — const, line 126
- `function enterOnControl(event: KeyboardEvent): boolean` — function, line 155
- `function stepChoice(choices: number[], current: number | null, delta: number): number | undefined` — function, line 159
- `const index = choices.indexOf(current)` — const, line 161
- `function PlanWhy(` — function, line 166
- `const plan = data.plan` — const, line 167
- `const headline = useCachedQuery(data.headlineEnabled === false ? null : ["get_today_headline"], ()` — const, line 168
- `const rows = todayRows(plan)` — const, line 172
- `const reentry = plan.kind === "reentry" ? reentryWhy(plan) : null` — const, line 173
- `const split = splitWhy(plan)` — const, line 174
- `const line = headline.data?.enabled ? headline.data.line ?? null : null` — const, line 175
- `function Threads(` — function, line 217
- `const questions = useCachedQuery(["list_question_queue", "today-threads"], ()` — const, line 228
- `const problems = useCachedQuery(["workbench_open_problems"], ()` — const, line 229
- `const threads = useMemo( ()` — const, line 232
- `function threadAction(thread: TodayThread):` — function, line 240
- `const citation = thread.question.sourceCitation` — const, line 242
- `const target = targetForDialogue(thread.question)` — const, line 244
- `const shown = more ? threads : threads.slice(0, THREADS_SHOWN)` — const, line 249
- `const act = threadAction(thread)` — const, line 254
- `function CapturesLine(` — function, line 282
- `const summary = useCachedQuery(["get_inbox_summary", "today"], ()` — const, line 283
- `const data = summary.data` — const, line 285
- `const something = Boolean(data && ((data.newCount ?? 0) > 0 || (data.deletePending?.length ?? 0) > 0 || data.vaultMismatch))` — const, line 286
- `function PlainList(` — function, line 300
- `const items = useMemo(()` — const, line 319
- `const minutesOf = useMemo(()` — const, line 320
- `const map = new Map<string, number>()` — const, line 321
- `const onKey = (event: KeyboardEvent)` — const, line 331
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 333
- `const item = items[focus]` — const, line 344
- `const minutes = minutesOf.get(item.practiceItemId)` — const, line 381
- `const cold = onYourOwnWhy(item)` — const, line 382
- `const planQuery = useDailyPlan(session?.sessionId ?? null)` — const, line 432
- `const data: DailyPlanDto | null = planQuery.data ?? null` — const, line 433
- `const planOn = data?.enabled === true && data.plan !== null` — const, line 434
- `const plan = planOn ? data!.plan : null` — const, line 435
- `const planOff = data !== null && !planOn` — const, line 436
- `const now = new Date()` — const, line 442
- `const summary = useCachedQuery(planOff ? ["get_start_summary"] : null, ()` — const, line 445
- `const offMinutes = session?.availableMinutes ?? chosenMinutes ?? summary.data?.rememberedMinutes ?? null` — const, line 447
- `const minutes = plan ? plan.rememberedMinutes : offMinutes` — const, line 448
- `const choices = plan ? plan.minuteChoices : summary.data?.minuteChoices ?? summary.data?.minutesPresets ?? []` — const, line 449
- `const queueInput = useMemo( ()` — const, line 455
- `const queueQuery = useCachedQuery( queueInput && (list || planOff) ? ["get_today_queue", queueInput] : null, ()` — const, line 465
- `const queue = queueQuery.data ?? null` — const, line 470
- `const retryQueue = useCallback(()` — const, line 474
- `const report = queueQuery.retryReport()` — const, line 475
- `const library = useCachedQuery(["get_source_library"], ()` — const, line 479
- `const noBooks = library.data !== undefined && library.data.sources.length === 0 && (library.data.pending?.length ?? 0) === 0` — const, line 480
- `const goals = useCachedQuery(["goals_list"], ()` — const, line 482
- `const primaryGoal: GoalDto | null = useMemo(()` — const, line 483
- `const active = (goals.data?.goals ?? []).filter((goal)` — const, line 484
- `const da = a.dueAt ? Date.parse(a.dueAt) : Infinity` — const, line 486
- `const db = b.dueAt ? Date.parse(b.dueAt) : Infinity` — const, line 487
- `const deciding = plan?.deciding === true && !list` — const, line 495
- `const refetchPlan = planQuery.refetch` — const, line 496
- `let reads = 0` — let, line 499
- `const timer = window.setInterval(()` — const, line 500
- `const waitingUntil = plan?.waiting?.until ?? null` — const, line 510
- `const at = Date.parse(waitingUntil)` — const, line 513
- `const timer = window.setTimeout(()` — const, line 515
- `const alive = useRef(true)` — const, line 523
- `const stay = useCallback(<T,>(value: T): T` — const, line 530
- `const startSession = useCallback( async (minutes: number): Promise<SessionSnapshot>` — const, line 535
- `const started = await onStartSession(minutes)` — const, line 537
- `const run = useCallback( async <T,>(work: ()` — const, line 543
- `const done = plan ? plan.status !== "open" : false` — const, line 559
- `const current = plan?.blocks.find((block)` — const, line 560
- `const waiting = plan && !done && !current && plan.waiting ? plan.waiting : null` — const, line 561
- `const rows = plan && !done ? todayRows(plan) : []` — const, line 562
- `async function begin()` — function, line 565
- `const begun = await run(async ()` — const, line 569
- `const started = await startSession(Math.round(plan.minutesBudget))` — const, line 570
- `const first = await api.nextPlanItem(` — const, line 571
- `const result = await run(()` — const, line 577
- `const action = planStepAction(result?.step,` — const, line 578
- `async function beginWithoutPlan()` — function, line 585
- `const opened = await run(async ()` — const, line 587
- `const started = session ?? (await startSession(minutes))` — const, line 588
- `const head = await api.getTodayQueue(todayQueueInput(started))` — const, line 589
- `function chooseMinutes(next: number)` — function, line 597
- `async function keepGoing()` — function, line 606
- `async function somethingNew(confirm: boolean)` — function, line 611
- `const result = await run(()` — const, line 612
- `async function finish()` — function, line 616
- `const summaryResult = await run(()` — const, line 619
- `async function skipCurrent()` — function, line 623
- `const next = current.items.find((item)` — const, line 629
- `async function openFromList(item: ScheduledItemDto)` — function, line 640
- `const started = await run(()` — const, line 643
- `const begun = await run(async ()` — const, line 651
- `const started = await startSession(Math.round(plan.minutesBudget))` — const, line 652
- `const result = await api.planLearnerPick(item.practiceItemId, started.sessionId, item.schedulerCandidateId ?? null)` — const, line 653
- `const result = await run(()` — const, line 659
- `const step = result.step` — const, line 661
- `async function practiseGoal()` — function, line 672
- `const input = queueInput ?? todayQueueInput(session)` — const, line 673
- `const snapshot = await run(()` — const, line 674
- `const target = snapshot?.sections.flatMap((section)` — const, line 675
- `const onKey = (event: KeyboardEvent)` — const, line 684
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 686
- `const next = stepChoice(choices, minutes, event.key === "ArrowLeft" ? -1 : 1)` — const, line 706
- `const streak = data?.streak ?? snapshotStreak` — const, line 714
- `const streakText = streakLine(streak)` — const, line 715
- `let body: ReactNode` — let, line 718
- `const head = queue?.sections.flatMap((section)` — const, line 755
- `const empty = planWasEmpty(data)` — const, line 769
- `const sentence = plan.kind === "reentry" ? reentrySentence(plan) : planSentence(plan)` — const, line 807

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

---
title: "Desktop module · src/screens/TodayScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.TodayScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/TodayScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/TodayScreen.tsx"
source_commit: "3ff403d6b8e867037e05fc2ef5dc0fcfa5141492"
source_commit_timestamp: "2026-10-21T13:01:47-04:00"
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

# `src/screens/TodayScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `TodayScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/TodayScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/TodayScreen.tsx) |
| Source lines | 1945 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `3ff403d6b8e867037e05fc2ef5dc0fcfa5141492` |
| Commit timestamp | `2026-10-21T13:01:47-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]]

## Public API

- `export function TodayScreen(` — function, line 131

## Internal implementation anchors

- `const HOTKEYS = "123456789abcdef"` — const, line 42
- `function fmtDeferredUntil(iso: string): string` — function, line 46
- `function masteryColor(mastery: number): string` — function, line 54
- `function GoalPopulationStrip(` — function, line 58
- `const job = batch.jobs[0]` — const, line 67
- `const active = batch.status === "queued" || batch.status === "running"` — const, line 68
- `const completed = batch.status === "completed"` — const, line 69
- `const failed = batch.status === "failed" || batch.status === "blocked"` — const, line 70
- `const rawCount = job?.result?.appliedCount ?? job?.result?.applied_count` — const, line 71
- `const appliedCount = typeof rawCount === "number" ? rawCount : null` — const, line 72
- `const message = active ? job?.message || "Generating practice for your goal" : completed ? appliedCount === 0 ? "Your goal already has enough practice." : `$` — const, line 73
- `const tone = completed ? COLOR.green : failed ? COLOR.red : COLOR.cyan` — const, line 80
- `const stripActionStyle: CSSProperties =` — const, line 121
- `const queueInput = useMemo( ()` — const, line 194
- `const planQuery = useDailyPlan(session?.sessionId ?? null)` — const, line 202
- `const planData: DailyPlanDto | null = planQuery.data ?? null` — const, line 203
- `const planKnown = planQuery.data !== undefined || planQuery.error !== null` — const, line 204
- `const planEnabled = planData?.enabled === true && planData.plan !== null` — const, line 205
- `const planView = planEnabled && !showFullList` — const, line 207
- `const planDeciding = planView && planData?.plan?.deciding === true` — const, line 212
- `const refetchPlan = planQuery.refetch` — const, line 213
- `let reads = 0` — let, line 216
- `const timer = window.setInterval(()` — const, line 217
- `const planWaitingUntil = planView ? planData?.plan?.waiting?.until ?? null : null` — const, line 229
- `const at = Date.parse(planWaitingUntil)` — const, line 232
- `const timer = window.setTimeout(()` — const, line 234
- `const headlineQuery = useCachedQuery<TodayHeadlineDto>( planEnabled ? ["get_today_headline"] : null, ()` — const, line 239
- `const queueQuery = useCachedQuery( planKnown && !planView ? ["get_today_queue", queueInput] : null, ()` — const, line 247
- `const queue: QueueSnapshot | null = ended ? null : queueQuery.data ?? null` — const, line 255
- `const queueLoading = !ended && (queueQuery.loading || !planKnown)` — const, line 256
- `const goalsQuery = useCachedQuery(["goals_list"], ()` — const, line 260
- `const goals: GoalDto[] | null = goalsQuery.data?.goals ?? null` — const, line 261
- `const now = useNowMinute()` — const, line 270
- `const visitIdRef = useRef<string>(mintVisitId())` — const, line 273
- `const refetchGoals = goalsQuery.refetch` — const, line 275
- `const refreshGoals = useCallback(()` — const, line 276
- `const queueRefreshing = queueQuery.refreshing` — const, line 290
- `const ids = queueItems(queue).map((item)` — const, line 298
- `const activeGoals = useMemo(()` — const, line 303
- `const active = (goals ?? []).filter((g)` — const, line 304
- `const da = a.dueAt ? Date.parse(a.dueAt) : Infinity` — const, line 306
- `const db = b.dueAt ? Date.parse(b.dueAt) : Infinity` — const, line 307
- `const reviewCandidate = useMemo(():` — const, line 314
- `const duePassed = goal.dueAt != null && !Number.isNaN(Date.parse(goal.dueAt)) && Date.parse(goal.dueAt) < Date.now()` — const, line 317
- `const stale = Date.now() - Date.parse(goal.updatedAt) > 7 * 86_400_000` — const, line 318
- `const frontierClear = goal.report != null && goal.report.atRiskCount === 0 && goal.report.total > 0` — const, line 319
- `const items = useMemo(()` — const, line 327
- `const flatIds = useMemo(()` — const, line 328
- `const focusedItem = useMemo( ()` — const, line 329
- `const followup = useMemo(()` — const, line 333
- `const dueCount = useMemo( ()` — const, line 335
- `const probeCount = useMemo(()` — const, line 339
- `const laterCount = useMemo(()` — const, line 340
- `const primaryGoalId = activeGoals[0]?.id ?? null` — const, line 344
- `const goalReportQuery = useCachedQuery( primaryGoalId ? ["get_goal_report", primaryGoalId] : null, ()` — const, line 345
- `const nextGap = useMemo(()` — const, line 350
- `const readiness = goalReportQuery.data?.report.blueprintReadiness ??` — const, line 351
- `let worst:` — let, line 352
- `const b = lo.bottleneck` — const, line 354
- `const hasActiveGoal = activeGoals.length > 0` — const, line 365
- `const overconfidenceQuery = useCachedQuery( primaryGoalId ? ["get_overconfidence_list", primaryGoalId] : null, ()` — const, line 366
- `const overconfidence: OverconfidentFacetDto[] = overconfidenceQuery.data?.facets ?? []` — const, line 371
- `const reentryQuery = useCachedQuery( primaryGoalId ? ["get_reentry_summary", primaryGoalId] : null, ()` — const, line 372
- `const reentry: ReentrySummaryDto | null = reentryQuery.data?.summary.show ? reentryQuery.data.summary : null` — const, line 377
- `const decayQuery = useCachedQuery( !hasActiveGoal && goals != null ? ["get_decay_pressure", null] : null, ()` — const, line 381
- `const decayPressure: DecayPressureDto | null = hasActiveGoal ? null : decayQuery.data?.pressure ?? null` — const, line 386
- `const startOverconfidenceProbe = useCallback( (facet: OverconfidentFacetDto)` — const, line 388
- `const sessionNarrative = useMemo(()` — const, line 400
- `const followups = items.filter((item)` — const, line 401
- `const reps = Math.max(0, items.length - probeCount - followups)` — const, line 402
- `const parts: string[] = []` — const, line 404
- `const gap = nextGap ? ` — next gap: $` — const, line 409
- `const seenQueueRevisionRef = useRef<number | null>(null)` — const, line 419
- `let cancelled = false` — let, line 421
- `const poll = async ()` — const, line 422
- `const snapshot = await api.getQueueRevision()` — const, line 424
- `const previous = seenQueueRevisionRef.current` — const, line 426
- `const interval = window.setInterval(()` — const, line 439
- `const seenBatchStatusRef = useRef<Map<string, string> | null>(null)` — const, line 451
- `let cancelled = false` — let, line 453
- `const poll = async ()` — const, line 454
- `const previous = seenBatchStatusRef.current` — const, line 458
- `const next = new Map(batches.map((batch)` — const, line 459
- `const newlyCompleted = batches.some( (batch)` — const, line 461
- `const latestPopulation = batches.find( (batch)` — const, line 469
- `const interval = window.setInterval(()` — const, line 483
- `const populationStripStale = useMemo(()` — const, line 512
- `const running = goalPopulation.status === "queued" || goalPopulation.status === "running"` — const, line 514
- `const focusedPracticeItemId = focusedItem?.practiceItemId ?? null` — const, line 525
- `const detailQuery = useCachedQuery( focusedPracticeItemId && !ended ? ["open_queue_item", focusedPracticeItemId] : null, ()` — const, line 526
- `const detail: PracticeItemDetail | null = detailQuery.data ?? null` — const, line 531
- `const finishSession = useCallback(async ()` — const, line 536
- `const summary = await api.endSession(session.sessionId)` — const, line 540
- `const openPractice = useCallback( (practiceItemId: string, schedulerCandidateId?: string | null)` — const, line 554
- `const budget = planData?.plan?.minutesBudget` — const, line 561
- `const result = await api.planLearnerPick(practiceItemId, started.sessionId, schedulerCandidateId ?? null)` — const, line 571
- `const step = result.step` — const, line 580
- `const onKey = (event: KeyboardEvent)` — const, line 594
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 599
- `const index = focusedItem ? flatIds.indexOf(focusedItem.practiceItemId) : -1` — const, line 608
- `const target = queueRefreshing ? undefined : flatIds[Number(event.key) - 1]` — const, line 619
- `async function refreshQueue(_options:` — function, line 643
- `function refreshAfterGoalChange()` — function, line 653
- `async function practiceAtRisk()` — function, line 658
- `let target = firstGoalFrontierItem(queue)` — let, line 659
- `async function runPlan<T>(work: ()` — function, line 672
- `async function continuePlan()` — function, line 685
- `const budget = planData?.plan?.minutesBudget` — const, line 690
- `const begun = await runPlan(async ()` — const, line 697
- `const started = await api.startSession(` — const, line 698
- `const first = await api.nextPlanItem(` — const, line 699
- `const result = await runPlan(()` — const, line 705
- `const action = planStepAction(result?.step,` — const, line 706
- `async function skipPlanItem(practiceItemId: string)` — function, line 712
- `async function skipPlanReading()` — function, line 716
- `async function setPlanMinutes(minutes: number)` — function, line 720
- `async function keepGoing()` — function, line 724
- `async function moreNew(confirm: boolean)` — function, line 729
- `const result = await runPlan(()` — const, line 730
- `async function donePlan()` — function, line 734
- `const first = items[0]` — const, line 816
- `const first = items.find((item)` — const, line 821
- `function TodayHero(` — function, line 1026
- `const remainingMinutes = remainingSessionMinutes(rawSession, now)` — const, line 1055
- `const session = rawSession && remainingMinutes != null ?` — const, line 1056
- `const stats: Array<` — const, line 1057
- `const sep = <span style=` — const, line 1063
- `const Stat = (` — const, line 1064
- `function QueueSectionGroup(` — function, line 1163
- `const isProbe = /probe/i.test(section.title)` — const, line 1178
- `const isDue = /due|now|overdue/i.test(section.title)` — const, line 1179
- `const color = isProbe ? COLOR.pink : isDue ? COLOR.amber : COLOR.textDim` — const, line 1180
- `const mark = isProbe ? "◆" : "▸"` — const, line 1181
- `function QueueRow(` — function, line 1210
- `const dueOffset = relativeDue(item, now)` — const, line 1225
- `const overdue = dueOffset.includes("ago")` — const, line 1226
- `const mastery = item.mastery` — const, line 1227
- `const borderLeft = focused || item.isFollowup ? COLOR.amber : item.isProbe ? COLOR.pink : "transparent"` — const, line 1228
- `function SurpriseInsertionBanner(` — function, line 1312
- `const coldProbe = followup.followupKind === "certification_cold_probe"` — const, line 1327
- `const coldRetry = followup.followupKind === "cold_retry"` — const, line 1334
- `const heading = coldProbe ? "validity check - held-out cold probe inserted" : coldRetry ? "unassisted check - answer this one cold" : "intervention gate - diagnostic follow-up inserted"` — const, line 1335
- `const noun = coldProbe ? "cold probe" : coldRetry ? "unassisted check" : "follow-up"` — const, line 1340
- `const WHY_ROWS: Array<` — const, line 1436
- `function WhyRow(` — function, line 1443
- `function QueueDetail(` — function, line 1455
- `const components = detail?.scheduler?.components ?? item.components` — const, line 1498
- `const variance = detail?.mastery?.variance ?? item.masteryVariance ?? 0.1` — const, line 1499
- `const mastery = detail?.mastery?.mean ?? item.mastery` — const, line 1500
- `const evidenceFacetButtonStyle: CSSProperties =` — const, line 1653
- `function QueueRankingStrip(` — function, line 1660
- `function scheduleChoiceClaim(item: ScheduledItemDto, producerVersion: string): ClaimCandidateDto` — function, line 1682
- `function OverconfidenceList(` — function, line 1698
- `const key = `$` — const, line 1729
- `const done = started.has(key)` — const, line 1730
- `function ReentryPanel(` — function, line 1756
- `const named = summary.slippedTop.map((f)` — const, line 1757
- `const sessionLine = reentryRefresherLine(refreshers)` — const, line 1758
- `function NoGoalFallback(` — function, line 1788
- `const action = (label: string, onClick: ()` — const, line 1801
- `const dismiss = ( <button type="button" onClick=` — const, line 1817
- `const dismissBannerButtonStyle: CSSProperties =` — const, line 1875
- `function unique(values: string[]): string[]` — function, line 1886
- `function queueItems(snapshot: QueueSnapshot | null): ScheduledItemDto[]` — function, line 1890
- `function firstGoalFrontierItem(snapshot: QueueSnapshot | null): ScheduledItemDto | null` — function, line 1894
- `function useNowMinute(): Date` — function, line 1898
- `const id = window.setInterval(()` — const, line 1901
- `function remainingSessionMinutes(session: SessionSnapshot | null, now: Date): number | null` — function, line 1907
- `const startedAt = new Date(session.startedAt).getTime()` — const, line 1909
- `const elapsedMinutes = Math.max(0, Math.floor((now.getTime() - startedAt) / 60_000))` — const, line 1911
- `function formatHeroTime(date: Date): string` — function, line 1915
- `function formatSessionNumber(sessionId: string): string` — function, line 1919
- `const matches = sessionId.match(/\d+/g)` — const, line 1920
- `const digits = matches ? matches[matches.length - 1] : undefined` — const, line 1921
- `function relativeDue(item: ScheduledItemDto, now: Date): string` — function, line 1927
- `const due = new Date(item.dueAt).getTime()` — const, line 1930
- `const diffMs = due - now.getTime()` — const, line 1932
- `const past = diffMs < 0` — const, line 1933
- `const minutes = Math.round(Math.abs(diffMs) / 60_000)` — const, line 1934
- `const span = minutes < 1 ? "now" : minutes < 60 ? `$` — const, line 1935

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `TodayScreen`; references `TodayScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ClaimCandidateDto`, `DailyPlanDto`, `DecayPressureDto`, `GoalDto`, `IngestBatchDto`, `OverconfidentFacetDto`, `PlanReadingDto`, `PlanStepDto`, `PracticeItemDetail`, `QueueSection`, `QueueSnapshot`, `ReentrySummaryDto`, `ScheduledItemDto`, `SchedulerComponents`, `SessionEndSummary`, `SessionSnapshot`, `TodayHeadlineDto`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `masteryTone`
- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export; imports `todayQueueInput`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `planStepAction`, `useDailyPlan`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export; imports `AskTarget`
- [[Reference/Desktop/TypeScript/components/ClaimSurface|src/components/ClaimSurface.tsx]] — import-or-re-export; imports `ClaimSurface`, `mintVisitId`
- [[Reference/Desktop/TypeScript/components/GoalBanner|src/components/GoalBanner.tsx]] — import-or-re-export; imports `GoalBanner`
- [[Reference/Desktop/TypeScript/components/GoalReviewCard|src/components/GoalReviewCard.tsx]] — import-or-re-export; imports `GoalReviewCard`, `ReviewReason`
- [[Reference/Desktop/TypeScript/components/GoalWizard|src/components/GoalWizard.tsx]] — import-or-re-export; imports `GoalWizard`
- [[Reference/Desktop/TypeScript/components/InboxStrip|src/components/InboxStrip.tsx]] — import-or-re-export; imports `InboxStrip`
- [[Reference/Desktop/TypeScript/components/ItemPresentation|src/components/ItemPresentation.tsx]] — import-or-re-export; imports `ItemPresentation`
- [[Reference/Desktop/TypeScript/components/KnowledgeModel|src/components/KnowledgeModel.tsx]] — import-or-re-export; imports `FacetEvidenceDrawer`
- [[Reference/Desktop/TypeScript/components/QuestionQueue|src/components/QuestionQueue.tsx]] — import-or-re-export; imports `QuestionQueuePanel`
- [[Reference/Desktop/TypeScript/components/WriteCardDialog|src/components/WriteCardDialog.tsx]] — import-or-re-export; imports `WriteCardDialog`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `BlockBar`, `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `SectionHeader`, `modePillColor`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EmptyPlaceholder`, `EntityLink`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export; imports `notifyQueueChanged`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/today/DailyPlanView|src/screens/today/DailyPlanView.tsx]] — import-or-re-export; imports `DailyPlanView`
- [[Reference/Desktop/TypeScript/screens/today/reentry|src/screens/today/reentry.ts]] — import-or-re-export; imports `reentryRefresherLine`, `reentryRefreshers`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/TodayScreen.plan.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/TodayScreen.plan.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_daily_loop_start_minutes.py](../../../../../../tests/test_daily_loop_start_minutes.py) — cross-boundary name contract: references uniquely owned exported name `TodayScreen`; it does **not** directly execute this source module.
- [tests/test_e2e_tui.py](../../../../../../tests/test_e2e_tui.py) — cross-boundary name contract: references uniquely owned exported name `TodayScreen`; it does **not** directly execute this source module.
- [tests/test_tui_app.py](../../../../../../tests/test_tui_app.py) — cross-boundary name contract: references uniquely owned exported name `TodayScreen`; it does **not** directly execute this source module.
- [tests/test_tui_theme.py](../../../../../../tests/test_tui_theme.py) — cross-boundary name contract: references uniquely owned exported name `TodayScreen`; it does **not** directly execute this source module.
- [tests/test_tui_today.py](../../../../../../tests/test_tui_today.py) — cross-boundary name contract: references uniquely owned exported name `TodayScreen`; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/TodayScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/TodayScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

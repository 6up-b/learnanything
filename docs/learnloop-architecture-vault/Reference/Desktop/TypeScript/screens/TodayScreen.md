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
source_commit: "d8aabd5dfcaa0d09ba16b8c66a2afd5f7416d82c"
source_commit_timestamp: "2026-11-03T22:12:02-05:00"
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
| Source lines | 1937 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `d8aabd5dfcaa0d09ba16b8c66a2afd5f7416d82c` |
| Commit timestamp | `2026-11-03T22:12:02-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]]

## Public API

- `export function TodayScreen(` — function, line 134

## Internal implementation anchors

- `const HOTKEYS = "123456789abcdef"` — const, line 45
- `function fmtDeferredUntil(iso: string): string` — function, line 49
- `function masteryColor(mastery: number): string` — function, line 57
- `function GoalPopulationStrip(` — function, line 61
- `const job = batch.jobs[0]` — const, line 70
- `const active = batch.status === "queued" || batch.status === "running"` — const, line 71
- `const completed = batch.status === "completed"` — const, line 72
- `const failed = batch.status === "failed" || batch.status === "blocked"` — const, line 73
- `const rawCount = job?.result?.appliedCount ?? job?.result?.applied_count` — const, line 74
- `const appliedCount = typeof rawCount === "number" ? rawCount : null` — const, line 75
- `const message = active ? job?.message || "Generating practice for your goal" : completed ? appliedCount === 0 ? "Your goal already has enough practice." : `$` — const, line 76
- `const tone = completed ? COLOR.green : failed ? COLOR.red : COLOR.cyan` — const, line 83
- `const stripActionStyle: CSSProperties =` — const, line 124
- `const queueInput = useMemo( ()` — const, line 200
- `const planQuery = useDailyPlan(session?.sessionId ?? null)` — const, line 208
- `const planData: DailyPlanDto | null = planQuery.data ?? null` — const, line 209
- `const planKnown = planQuery.data !== undefined || planQuery.error !== null` — const, line 210
- `const planEnabled = planData?.enabled === true && planData.plan !== null` — const, line 211
- `const planView = planEnabled && !showFullList` — const, line 213
- `const planDeciding = planView && planData?.plan?.deciding === true` — const, line 218
- `const refetchPlan = planQuery.refetch` — const, line 219
- `let reads = 0` — let, line 222
- `const timer = window.setInterval(()` — const, line 223
- `const planWaitingUntil = planView ? planData?.plan?.waiting?.until ?? null : null` — const, line 235
- `const at = Date.parse(planWaitingUntil)` — const, line 238
- `const timer = window.setTimeout(()` — const, line 240
- `const headlineQuery = useCachedQuery<TodayHeadlineDto>( planEnabled ? ["get_today_headline"] : null, ()` — const, line 245
- `const queueQuery = useCachedQuery( planKnown && !planView ? ["get_today_queue", queueInput] : null, ()` — const, line 253
- `const queue: QueueSnapshot | null = ended ? null : queueQuery.data ?? null` — const, line 261
- `const queueLoading = !ended && (queueQuery.loading || !planKnown)` — const, line 262
- `const goalsQuery = useCachedQuery(["goals_list"], ()` — const, line 266
- `const goals: GoalDto[] | null = goalsQuery.data?.goals ?? null` — const, line 267
- `const now = useNowMinute()` — const, line 276
- `const visitIdRef = useRef<string>(mintVisitId())` — const, line 279
- `const refetchGoals = goalsQuery.refetch` — const, line 281
- `const refreshGoals = useCallback(()` — const, line 282
- `const queueRefreshing = queueQuery.refreshing` — const, line 296
- `const ids = queueItems(queue).map((item)` — const, line 304
- `const activeGoals = useMemo(()` — const, line 309
- `const active = (goals ?? []).filter((g)` — const, line 310
- `const da = a.dueAt ? Date.parse(a.dueAt) : Infinity` — const, line 312
- `const db = b.dueAt ? Date.parse(b.dueAt) : Infinity` — const, line 313
- `const reviewCandidate = useMemo(():` — const, line 320
- `const duePassed = goal.dueAt != null && !Number.isNaN(Date.parse(goal.dueAt)) && Date.parse(goal.dueAt) < Date.now()` — const, line 323
- `const stale = Date.now() - Date.parse(goal.updatedAt) > 7 * 86_400_000` — const, line 324
- `const frontierClear = goal.report != null && goal.report.atRiskCount === 0 && goal.report.total > 0` — const, line 325
- `const items = useMemo(()` — const, line 333
- `const flatIds = useMemo(()` — const, line 334
- `const focusedItem = useMemo( ()` — const, line 335
- `const followup = useMemo(()` — const, line 339
- `const dueCount = useMemo( ()` — const, line 341
- `const probeCount = useMemo(()` — const, line 345
- `const laterCount = useMemo(()` — const, line 346
- `const primaryGoalId = activeGoals[0]?.id ?? null` — const, line 350
- `const goalReportQuery = useCachedQuery( primaryGoalId ? ["get_goal_report", primaryGoalId] : null, ()` — const, line 351
- `const nextGap = useMemo(()` — const, line 356
- `const readiness = goalReportQuery.data?.report.blueprintReadiness ??` — const, line 357
- `let worst:` — let, line 358
- `const b = lo.bottleneck` — const, line 360
- `const hasActiveGoal = activeGoals.length > 0` — const, line 371
- `const overconfidenceQuery = useCachedQuery( primaryGoalId ? ["get_overconfidence_list", primaryGoalId] : null, ()` — const, line 372
- `const overconfidence: OverconfidentFacetDto[] = overconfidenceQuery.data?.facets ?? []` — const, line 377
- `const reentryQuery = useCachedQuery( primaryGoalId ? ["get_reentry_summary", primaryGoalId] : null, ()` — const, line 378
- `const reentry: ReentrySummaryDto | null = reentryQuery.data?.summary.show ? reentryQuery.data.summary : null` — const, line 383
- `const decayQuery = useCachedQuery( !hasActiveGoal && goals != null ? ["get_decay_pressure", null] : null, ()` — const, line 387
- `const decayPressure: DecayPressureDto | null = hasActiveGoal ? null : decayQuery.data?.pressure ?? null` — const, line 392
- `const startOverconfidenceProbe = useCallback( (facet: OverconfidentFacetDto)` — const, line 394
- `const sessionNarrative = useMemo(()` — const, line 406
- `const followups = items.filter((item)` — const, line 407
- `const reps = Math.max(0, items.length - probeCount - followups)` — const, line 408
- `const parts: string[] = []` — const, line 410
- `const gap = nextGap ? ` — next gap: $` — const, line 415
- `const seenBatchStatusRef = useRef<Map<string, string> | null>(null)` — const, line 431
- `let cancelled = false` — let, line 433
- `const poll = async ()` — const, line 434
- `const previous = seenBatchStatusRef.current` — const, line 438
- `const next = new Map(batches.map((batch)` — const, line 439
- `const newlyCompleted = batches.some( (batch)` — const, line 441
- `const latestPopulation = batches.find( (batch)` — const, line 449
- `const interval = window.setInterval(()` — const, line 463
- `const populationStripStale = useMemo(()` — const, line 492
- `const running = goalPopulation.status === "queued" || goalPopulation.status === "running"` — const, line 494
- `const focusedPracticeItemId = focusedItem?.practiceItemId ?? null` — const, line 505
- `const detailQuery = useCachedQuery( focusedPracticeItemId && !ended ? ["open_queue_item", focusedPracticeItemId] : null, ()` — const, line 506
- `const detail: PracticeItemDetail | null = detailQuery.data ?? null` — const, line 511
- `const finishSession = useCallback(async ()` — const, line 516
- `const summary = await api.endSession(session.sessionId)` — const, line 520
- `const openPractice = useCallback( (practiceItemId: string, schedulerCandidateId?: string | null)` — const, line 534
- `const budget = planData?.plan?.minutesBudget` — const, line 541
- `const result = await api.planLearnerPick(practiceItemId, started.sessionId, schedulerCandidateId ?? null)` — const, line 551
- `const step = result.step` — const, line 560
- `const onKey = (event: KeyboardEvent)` — const, line 574
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 579
- `const index = focusedItem ? flatIds.indexOf(focusedItem.practiceItemId) : -1` — const, line 588
- `const target = queueRefreshing ? undefined : flatIds[Number(event.key) - 1]` — const, line 599
- `async function refreshQueue(_options:` — function, line 623
- `function refreshAfterGoalChange()` — function, line 633
- `async function practiceAtRisk()` — function, line 638
- `let target = firstGoalFrontierItem(queue)` — let, line 639
- `async function runPlan<T>(work: ()` — function, line 652
- `async function continuePlan()` — function, line 665
- `const budget = planData?.plan?.minutesBudget` — const, line 670
- `const begun = await runPlan(async ()` — const, line 677
- `const started = await startSessionOrAsk(` — const, line 678
- `const first = await api.nextPlanItem(` — const, line 680
- `const result = await runPlan(()` — const, line 686
- `const action = planStepAction(result?.step,` — const, line 687
- `async function skipPlanItem(practiceItemId: string)` — function, line 693
- `async function skipPlanReading()` — function, line 697
- `async function setPlanMinutes(minutes: number)` — function, line 701
- `async function keepGoing()` — function, line 705
- `async function moreNew(confirm: boolean)` — function, line 710
- `const result = await runPlan(()` — const, line 711
- `async function donePlan()` — function, line 715
- `const suggestionCard = onStartLesson && algoConfig().lessonSuggestions ? <LessonSuggestionCard sessionId=` — const, line 722
- `const first = items[0]` — const, line 808
- `const first = items.find((item)` — const, line 813
- `function TodayHero(` — function, line 1018
- `const remainingMinutes = remainingSessionMinutes(rawSession, now)` — const, line 1047
- `const session = rawSession && remainingMinutes != null ?` — const, line 1048
- `const stats: Array<` — const, line 1049
- `const sep = <span style=` — const, line 1055
- `const Stat = (` — const, line 1056
- `function QueueSectionGroup(` — function, line 1155
- `const isProbe = /probe/i.test(section.title)` — const, line 1170
- `const isDue = /due|now|overdue/i.test(section.title)` — const, line 1171
- `const color = isProbe ? COLOR.pink : isDue ? COLOR.amber : COLOR.textDim` — const, line 1172
- `const mark = isProbe ? "◆" : "▸"` — const, line 1173
- `function QueueRow(` — function, line 1202
- `const dueOffset = relativeDue(item, now)` — const, line 1217
- `const overdue = dueOffset.includes("ago")` — const, line 1218
- `const mastery = item.mastery` — const, line 1219
- `const borderLeft = focused || item.isFollowup ? COLOR.amber : item.isProbe ? COLOR.pink : "transparent"` — const, line 1220
- `function SurpriseInsertionBanner(` — function, line 1304
- `const coldProbe = followup.followupKind === "certification_cold_probe"` — const, line 1319
- `const coldRetry = followup.followupKind === "cold_retry"` — const, line 1326
- `const heading = coldProbe ? "validity check - held-out cold probe inserted" : coldRetry ? "unassisted check - answer this one cold" : "intervention gate - diagnostic follow-up inserted"` — const, line 1327
- `const noun = coldProbe ? "cold probe" : coldRetry ? "unassisted check" : "follow-up"` — const, line 1332
- `const WHY_ROWS: Array<` — const, line 1428
- `function WhyRow(` — function, line 1435
- `function QueueDetail(` — function, line 1447
- `const components = detail?.scheduler?.components ?? item.components` — const, line 1490
- `const variance = detail?.mastery?.variance ?? item.masteryVariance ?? 0.1` — const, line 1491
- `const mastery = detail?.mastery?.mean ?? item.mastery` — const, line 1492
- `const evidenceFacetButtonStyle: CSSProperties =` — const, line 1645
- `function QueueRankingStrip(` — function, line 1652
- `function scheduleChoiceClaim(item: ScheduledItemDto, producerVersion: string): ClaimCandidateDto` — function, line 1674
- `function OverconfidenceList(` — function, line 1690
- `const key = `$` — const, line 1721
- `const done = started.has(key)` — const, line 1722
- `function ReentryPanel(` — function, line 1748
- `const named = summary.slippedTop.map((f)` — const, line 1749
- `const sessionLine = reentryRefresherLine(refreshers)` — const, line 1750
- `function NoGoalFallback(` — function, line 1780
- `const action = (label: string, onClick: ()` — const, line 1793
- `const dismiss = ( <button type="button" onClick=` — const, line 1809
- `const dismissBannerButtonStyle: CSSProperties =` — const, line 1867
- `function unique(values: string[]): string[]` — function, line 1878
- `function queueItems(snapshot: QueueSnapshot | null): ScheduledItemDto[]` — function, line 1882
- `function firstGoalFrontierItem(snapshot: QueueSnapshot | null): ScheduledItemDto | null` — function, line 1886
- `function useNowMinute(): Date` — function, line 1890
- `const id = window.setInterval(()` — const, line 1893
- `function remainingSessionMinutes(session: SessionSnapshot | null, now: Date): number | null` — function, line 1899
- `const startedAt = new Date(session.startedAt).getTime()` — const, line 1901
- `const elapsedMinutes = Math.max(0, Math.floor((now.getTime() - startedAt) / 60_000))` — const, line 1903
- `function formatHeroTime(date: Date): string` — function, line 1907
- `function formatSessionNumber(sessionId: string): string` — function, line 1911
- `const matches = sessionId.match(/\d+/g)` — const, line 1912
- `const digits = matches ? matches[matches.length - 1] : undefined` — const, line 1913
- `function relativeDue(item: ScheduledItemDto, now: Date): string` — function, line 1919
- `const due = new Date(item.dueAt).getTime()` — const, line 1922
- `const diffMs = due - now.getTime()` — const, line 1924
- `const past = diffMs < 0` — const, line 1925
- `const minutes = Math.round(Math.abs(diffMs) / 60_000)` — const, line 1926
- `const span = minutes < 1 ? "now" : minutes < 60 ? `$` — const, line 1927

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
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`, `masteryTone`
- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export; imports `todayQueueInput`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `planStepAction`, `useDailyPlan`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/sessionHandoff|src/app/sessionHandoff.ts]] — import-or-re-export; imports `startSessionOrAsk`
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
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] — import-or-re-export; imports `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/feedback/FollowupPanel|src/screens/feedback/FollowupPanel.tsx]] — import-or-re-export; imports `RouterDecisionLine`
- [[Reference/Desktop/TypeScript/screens/today/DailyPlanView|src/screens/today/DailyPlanView.tsx]] — import-or-re-export; imports `DailyPlanView`
- [[Reference/Desktop/TypeScript/screens/today/LessonSuggestionCard|src/screens/today/LessonSuggestionCard.tsx]] — import-or-re-export; imports `LessonSuggestionCard`
- [[Reference/Desktop/TypeScript/screens/today/reentry|src/screens/today/reentry.ts]] — import-or-re-export; imports `reentryRefresherLine`, `reentryRefreshers`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/TodayScreen.suggestion.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/TodayScreen.suggestion.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

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
source_commit: "0395ae32f9e2e40d1cb98b38402631299a94003f"
source_commit_timestamp: "2026-09-07T12:49:13-04:00"
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
| Source lines | 1698 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `0395ae32f9e2e40d1cb98b38402631299a94003f` |
| Commit timestamp | `2026-09-07T12:49:13-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]]

## Public API

- `export function TodayScreen(` — function, line 123

## Internal implementation anchors

- `const HOTKEYS = "123456789abcdef"` — const, line 34
- `function fmtDeferredUntil(iso: string): string` — function, line 38
- `function masteryColor(mastery: number): string` — function, line 46
- `function GoalPopulationStrip(` — function, line 50
- `const job = batch.jobs[0]` — const, line 59
- `const active = batch.status === "queued" || batch.status === "running"` — const, line 60
- `const completed = batch.status === "completed"` — const, line 61
- `const failed = batch.status === "failed" || batch.status === "blocked"` — const, line 62
- `const rawCount = job?.result?.appliedCount ?? job?.result?.applied_count` — const, line 63
- `const appliedCount = typeof rawCount === "number" ? rawCount : null` — const, line 64
- `const message = active ? job?.message || "Generating practice for your goal" : completed ? appliedCount === 0 ? "Your goal already has enough practice." : `$` — const, line 65
- `const tone = completed ? COLOR.green : failed ? COLOR.red : COLOR.cyan` — const, line 72
- `const stripActionStyle: CSSProperties =` — const, line 113
- `const queueInput = useMemo( ()` — const, line 165
- `const queueQuery = useCachedQuery(["get_today_queue", queueInput], ()` — const, line 173
- `const queue: QueueSnapshot | null = ended ? null : queueQuery.data ?? null` — const, line 179
- `const queueLoading = !ended && queueQuery.loading` — const, line 180
- `const goalsQuery = useCachedQuery(["goals_list"], ()` — const, line 184
- `const goals: GoalDto[] | null = goalsQuery.data?.goals ?? null` — const, line 185
- `const now = useNowMinute()` — const, line 194
- `const visitIdRef = useRef<string>(mintVisitId())` — const, line 197
- `const refetchGoals = goalsQuery.refetch` — const, line 199
- `const refreshGoals = useCallback(()` — const, line 200
- `const queueRefreshing = queueQuery.refreshing` — const, line 214
- `const ids = queueItems(queue).map((item)` — const, line 222
- `const activeGoals = useMemo(()` — const, line 227
- `const active = (goals ?? []).filter((g)` — const, line 228
- `const da = a.dueAt ? Date.parse(a.dueAt) : Infinity` — const, line 230
- `const db = b.dueAt ? Date.parse(b.dueAt) : Infinity` — const, line 231
- `const reviewCandidate = useMemo(():` — const, line 238
- `const duePassed = goal.dueAt != null && !Number.isNaN(Date.parse(goal.dueAt)) && Date.parse(goal.dueAt) < Date.now()` — const, line 241
- `const stale = Date.now() - Date.parse(goal.updatedAt) > 7 * 86_400_000` — const, line 242
- `const frontierClear = goal.report != null && goal.report.atRiskCount === 0 && goal.report.total > 0` — const, line 243
- `const items = useMemo(()` — const, line 251
- `const flatIds = useMemo(()` — const, line 252
- `const focusedItem = useMemo( ()` — const, line 253
- `const followup = useMemo(()` — const, line 257
- `const dueCount = useMemo( ()` — const, line 259
- `const probeCount = useMemo(()` — const, line 263
- `const laterCount = useMemo(()` — const, line 264
- `const primaryGoalId = activeGoals[0]?.id ?? null` — const, line 268
- `const goalReportQuery = useCachedQuery( primaryGoalId ? ["get_goal_report", primaryGoalId] : null, ()` — const, line 269
- `const nextGap = useMemo(()` — const, line 274
- `const readiness = goalReportQuery.data?.report.blueprintReadiness ??` — const, line 275
- `let worst:` — let, line 276
- `const b = lo.bottleneck` — const, line 278
- `const hasActiveGoal = activeGoals.length > 0` — const, line 289
- `const overconfidenceQuery = useCachedQuery( primaryGoalId ? ["get_overconfidence_list", primaryGoalId] : null, ()` — const, line 290
- `const overconfidence: OverconfidentFacetDto[] = overconfidenceQuery.data?.facets ?? []` — const, line 295
- `const reentryQuery = useCachedQuery( primaryGoalId ? ["get_reentry_summary", primaryGoalId] : null, ()` — const, line 296
- `const reentry: ReentrySummaryDto | null = reentryQuery.data?.summary.show ? reentryQuery.data.summary : null` — const, line 301
- `const decayQuery = useCachedQuery( !hasActiveGoal && goals != null ? ["get_decay_pressure", null] : null, ()` — const, line 305
- `const decayPressure: DecayPressureDto | null = hasActiveGoal ? null : decayQuery.data?.pressure ?? null` — const, line 310
- `const startOverconfidenceProbe = useCallback( (facet: OverconfidentFacetDto)` — const, line 312
- `const sessionNarrative = useMemo(()` — const, line 324
- `const followups = items.filter((item)` — const, line 325
- `const reps = Math.max(0, items.length - probeCount - followups)` — const, line 326
- `const parts: string[] = []` — const, line 328
- `const gap = nextGap ? ` — next gap: $` — const, line 333
- `const seenQueueRevisionRef = useRef<number | null>(null)` — const, line 343
- `let cancelled = false` — let, line 345
- `const poll = async ()` — const, line 346
- `const snapshot = await api.getQueueRevision()` — const, line 348
- `const previous = seenQueueRevisionRef.current` — const, line 350
- `const interval = window.setInterval(()` — const, line 363
- `const seenBatchStatusRef = useRef<Map<string, string> | null>(null)` — const, line 375
- `let cancelled = false` — let, line 377
- `const poll = async ()` — const, line 378
- `const previous = seenBatchStatusRef.current` — const, line 382
- `const next = new Map(batches.map((batch)` — const, line 383
- `const newlyCompleted = batches.some( (batch)` — const, line 385
- `const latestPopulation = batches.find( (batch)` — const, line 393
- `const interval = window.setInterval(()` — const, line 407
- `const populationStripStale = useMemo(()` — const, line 436
- `const running = goalPopulation.status === "queued" || goalPopulation.status === "running"` — const, line 438
- `const focusedPracticeItemId = focusedItem?.practiceItemId ?? null` — const, line 449
- `const detailQuery = useCachedQuery( focusedPracticeItemId && !ended ? ["open_queue_item", focusedPracticeItemId] : null, ()` — const, line 450
- `const detail: PracticeItemDetail | null = detailQuery.data ?? null` — const, line 455
- `const finishSession = useCallback(async ()` — const, line 460
- `const summary = await api.endSession(session.sessionId)` — const, line 464
- `const onKey = (event: KeyboardEvent)` — const, line 475
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 476
- `const index = focusedItem ? flatIds.indexOf(focusedItem.practiceItemId) : -1` — const, line 478
- `const target = queueRefreshing ? undefined : flatIds[Number(event.key) - 1]` — const, line 489
- `async function refreshQueue(_options:` — function, line 513
- `function refreshAfterGoalChange()` — function, line 522
- `async function practiceAtRisk()` — function, line 527
- `let target = firstGoalFrontierItem(queue)` — let, line 528
- `const first = items[0]` — const, line 581
- `const first = items.find((item)` — const, line 586
- `function TodayHero(` — function, line 791
- `const remainingMinutes = remainingSessionMinutes(rawSession, now)` — const, line 820
- `const session = rawSession && remainingMinutes != null ?` — const, line 821
- `const stats: Array<` — const, line 822
- `const sep = <span style=` — const, line 828
- `const Stat = (` — const, line 829
- `function QueueSectionGroup(` — function, line 928
- `const isProbe = /probe/i.test(section.title)` — const, line 943
- `const isDue = /due|now|overdue/i.test(section.title)` — const, line 944
- `const color = isProbe ? COLOR.pink : isDue ? COLOR.amber : COLOR.textDim` — const, line 945
- `const mark = isProbe ? "◆" : "▸"` — const, line 946
- `function QueueRow(` — function, line 975
- `const dueOffset = relativeDue(item, now)` — const, line 990
- `const overdue = dueOffset.includes("ago")` — const, line 991
- `const mastery = item.mastery` — const, line 992
- `const borderLeft = focused || item.isFollowup ? COLOR.amber : item.isProbe ? COLOR.pink : "transparent"` — const, line 993
- `function SurpriseInsertionBanner(` — function, line 1077
- `const coldProbe = followup.followupKind === "certification_cold_probe"` — const, line 1092
- `const coldRetry = followup.followupKind === "cold_retry"` — const, line 1099
- `const heading = coldProbe ? "validity check - held-out cold probe inserted" : coldRetry ? "unassisted check - answer this one cold" : "intervention gate - diagnostic follow-up inserted"` — const, line 1100
- `const noun = coldProbe ? "cold probe" : coldRetry ? "unassisted check" : "follow-up"` — const, line 1105
- `const WHY_ROWS: Array<` — const, line 1201
- `function WhyRow(` — function, line 1208
- `function QueueDetail(` — function, line 1220
- `const components = detail?.scheduler?.components ?? item.components` — const, line 1263
- `const variance = detail?.mastery?.variance ?? item.masteryVariance ?? 0.1` — const, line 1264
- `const mastery = detail?.mastery?.mean ?? item.mastery` — const, line 1265
- `const evidenceFacetButtonStyle: CSSProperties =` — const, line 1407
- `function QueueRankingStrip(` — function, line 1414
- `function scheduleChoiceClaim(item: ScheduledItemDto, producerVersion: string): ClaimCandidateDto` — function, line 1436
- `function OverconfidenceList(` — function, line 1452
- `const key = `$` — const, line 1483
- `const done = started.has(key)` — const, line 1484
- `function ReentryPanel(` — function, line 1510
- `const named = summary.slippedTop.map((f)` — const, line 1511
- `function NoGoalFallback(` — function, line 1541
- `const action = (label: string, onClick: ()` — const, line 1554
- `const dismiss = ( <button type="button" onClick=` — const, line 1570
- `const dismissBannerButtonStyle: CSSProperties =` — const, line 1628
- `function unique(values: string[]): string[]` — function, line 1639
- `function queueItems(snapshot: QueueSnapshot | null): ScheduledItemDto[]` — function, line 1643
- `function firstGoalFrontierItem(snapshot: QueueSnapshot | null): ScheduledItemDto | null` — function, line 1647
- `function useNowMinute(): Date` — function, line 1651
- `const id = window.setInterval(()` — const, line 1654
- `function remainingSessionMinutes(session: SessionSnapshot | null, now: Date): number | null` — function, line 1660
- `const startedAt = new Date(session.startedAt).getTime()` — const, line 1662
- `const elapsedMinutes = Math.max(0, Math.floor((now.getTime() - startedAt) / 60_000))` — const, line 1664
- `function formatHeroTime(date: Date): string` — function, line 1668
- `function formatSessionNumber(sessionId: string): string` — function, line 1672
- `const matches = sessionId.match(/\d+/g)` — const, line 1673
- `const digits = matches ? matches[matches.length - 1] : undefined` — const, line 1674
- `function relativeDue(item: ScheduledItemDto, now: Date): string` — function, line 1680
- `const due = new Date(item.dueAt).getTime()` — const, line 1683
- `const diffMs = due - now.getTime()` — const, line 1685
- `const past = diffMs < 0` — const, line 1686
- `const minutes = Math.round(Math.abs(diffMs) / 60_000)` — const, line 1687
- `const span = minutes < 1 ? "now" : minutes < 60 ? `$` — const, line 1688

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `TodayScreen`; references `TodayScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ClaimCandidateDto`, `DecayPressureDto`, `GoalDto`, `IngestBatchDto`, `OverconfidentFacetDto`, `PracticeItemDetail`, `QueueSection`, `QueueSnapshot`, `ReentrySummaryDto`, `ScheduledItemDto`, `SchedulerComponents`, `SessionEndSummary`, `SessionSnapshot`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `masteryTone`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export; imports `AskTarget`
- [[Reference/Desktop/TypeScript/components/ClaimSurface|src/components/ClaimSurface.tsx]] — import-or-re-export; imports `ClaimSurface`, `mintVisitId`
- [[Reference/Desktop/TypeScript/components/GoalBanner|src/components/GoalBanner.tsx]] — import-or-re-export; imports `GoalBanner`
- [[Reference/Desktop/TypeScript/components/GoalReviewCard|src/components/GoalReviewCard.tsx]] — import-or-re-export; imports `GoalReviewCard`, `ReviewReason`
- [[Reference/Desktop/TypeScript/components/GoalWizard|src/components/GoalWizard.tsx]] — import-or-re-export; imports `GoalWizard`
- [[Reference/Desktop/TypeScript/components/KnowledgeModel|src/components/KnowledgeModel.tsx]] — import-or-re-export; imports `FacetEvidenceDrawer`
- [[Reference/Desktop/TypeScript/components/QuestionQueue|src/components/QuestionQueue.tsx]] — import-or-re-export; imports `QuestionQueuePanel`
- [[Reference/Desktop/TypeScript/components/WriteCardDialog|src/components/WriteCardDialog.tsx]] — import-or-re-export; imports `WriteCardDialog`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `BlockBar`, `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `KeyBar`, `Meta`, `Pill`, `SectionHeader`, `modePillColor`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EmptyPlaceholder`, `EntityLink`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export; imports `notifyQueueChanged`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

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

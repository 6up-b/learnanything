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
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
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
| Source lines | 1722 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]]

## Public API

- `export function TodayScreen(` — function, line 121

## Internal implementation anchors

- `const HOTKEYS = "123456789abcdef"` — const, line 32
- `function fmtDeferredUntil(iso: string): string` — function, line 36
- `function masteryColor(mastery: number): string` — function, line 44
- `function GoalPopulationStrip(` — function, line 48
- `const job = batch.jobs[0]` — const, line 57
- `const active = batch.status === "queued" || batch.status === "running"` — const, line 58
- `const completed = batch.status === "completed"` — const, line 59
- `const failed = batch.status === "failed" || batch.status === "blocked"` — const, line 60
- `const rawCount = job?.result?.appliedCount ?? job?.result?.applied_count` — const, line 61
- `const appliedCount = typeof rawCount === "number" ? rawCount : null` — const, line 62
- `const message = active ? job?.message || "Generating practice for your goal" : completed ? appliedCount === 0 ? "Your goal already has enough practice." : `$` — const, line 63
- `const tone = completed ? COLOR.green : failed ? COLOR.red : COLOR.cyan` — const, line 70
- `const stripActionStyle: CSSProperties =` — const, line 111
- `const queueRequestRef = useRef<` — const, line 175
- `const queueRequestSeqRef = useRef(0)` — const, line 176
- `const now = useNowMinute()` — const, line 177
- `const visitIdRef = useRef<string>(mintVisitId())` — const, line 180
- `const refreshGoals = useCallback(()` — const, line 185
- `const activeGoals = useMemo(()` — const, line 197
- `const active = (goals ?? []).filter((g)` — const, line 198
- `const da = a.dueAt ? Date.parse(a.dueAt) : Infinity` — const, line 200
- `const db = b.dueAt ? Date.parse(b.dueAt) : Infinity` — const, line 201
- `const reviewCandidate = useMemo(():` — const, line 208
- `const duePassed = goal.dueAt != null && !Number.isNaN(Date.parse(goal.dueAt)) && Date.parse(goal.dueAt) < Date.now()` — const, line 211
- `const stale = Date.now() - Date.parse(goal.updatedAt) > 7 * 86_400_000` — const, line 212
- `const frontierClear = goal.report != null && goal.report.atRiskCount === 0 && goal.report.total > 0` — const, line 213
- `const items = useMemo(()` — const, line 221
- `const flatIds = useMemo(()` — const, line 222
- `const focusedItem = useMemo( ()` — const, line 223
- `const followup = useMemo(()` — const, line 227
- `const dueCount = useMemo( ()` — const, line 229
- `const probeCount = useMemo(()` — const, line 233
- `const laterCount = useMemo(()` — const, line 234
- `const primaryGoalId = activeGoals[0]?.id ?? null` — const, line 239
- `let alive = true` — let, line 242
- `const readiness = snap.report.blueprintReadiness ??` — const, line 247
- `let worst:` — let, line 248
- `const b = lo.bottleneck` — const, line 250
- `const hasActiveGoal = activeGoals.length > 0` — const, line 263
- `let alive = true` — let, line 270
- `let alive = true` — let, line 287
- `const startOverconfidenceProbe = useCallback( (facet: OverconfidentFacetDto)` — const, line 295
- `const sessionNarrative = useMemo(()` — const, line 307
- `const followups = items.filter((item)` — const, line 308
- `const reps = Math.max(0, items.length - probeCount - followups)` — const, line 309
- `const parts: string[] = []` — const, line 311
- `const gap = nextGap ? ` — next gap: $` — const, line 316
- `const seenQueueRevisionRef = useRef<number | null>(null)` — const, line 335
- `let cancelled = false` — let, line 337
- `const poll = async ()` — const, line 338
- `const snapshot = await api.getQueueRevision()` — const, line 340
- `const previous = seenQueueRevisionRef.current` — const, line 342
- `const interval = window.setInterval(()` — const, line 355
- `const seenBatchStatusRef = useRef<Map<string, string> | null>(null)` — const, line 367
- `let cancelled = false` — let, line 369
- `const poll = async ()` — const, line 370
- `const previous = seenBatchStatusRef.current` — const, line 374
- `const next = new Map(batches.map((batch)` — const, line 375
- `const newlyCompleted = batches.some( (batch)` — const, line 377
- `const latestPopulation = batches.find( (batch)` — const, line 385
- `const interval = window.setInterval(()` — const, line 399
- `const populationStripStale = useMemo(()` — const, line 428
- `const running = goalPopulation.status === "queued" || goalPopulation.status === "running"` — const, line 430
- `let cancelled = false` — let, line 444
- `const finishSession = useCallback(async ()` — const, line 458
- `const summary = await api.endSession(session.sessionId)` — const, line 462
- `const onKey = (event: KeyboardEvent)` — const, line 474
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 475
- `const index = focusedItem ? flatIds.indexOf(focusedItem.practiceItemId) : -1` — const, line 477
- `const target = flatIds[Number(event.key) - 1]` — const, line 488
- `async function refreshQueue(` — function, line 509
- `const input =` — const, line 510
- `const key = JSON.stringify(input)` — const, line 515
- `const inFlight = queueRequestRef.current` — const, line 516
- `const reuse = !force && inFlight?.key === key` — const, line 517
- `const requestId = reuse ? inFlight.id : queueRequestSeqRef.current + 1` — const, line 518
- `const promise = reuse ? inFlight.promise : api.getTodayQueue(input)` — const, line 519
- `const next = await promise` — const, line 527
- `function refreshAfterGoalChange()` — function, line 546
- `async function practiceAtRisk()` — function, line 551
- `let target = firstGoalFrontierItem(queue)` — let, line 552
- `const first = items[0]` — const, line 605
- `const first = items.find((item)` — const, line 610
- `function TodayHero(` — function, line 815
- `const remainingMinutes = remainingSessionMinutes(rawSession, now)` — const, line 844
- `const session = rawSession && remainingMinutes != null ?` — const, line 845
- `const stats: Array<` — const, line 846
- `const sep = <span style=` — const, line 852
- `const Stat = (` — const, line 853
- `function QueueSectionGroup(` — function, line 952
- `const isProbe = /probe/i.test(section.title)` — const, line 967
- `const isDue = /due|now|overdue/i.test(section.title)` — const, line 968
- `const color = isProbe ? COLOR.pink : isDue ? COLOR.amber : COLOR.textDim` — const, line 969
- `const mark = isProbe ? "◆" : "▸"` — const, line 970
- `function QueueRow(` — function, line 999
- `const dueOffset = relativeDue(item, now)` — const, line 1014
- `const overdue = dueOffset.includes("ago")` — const, line 1015
- `const mastery = item.mastery` — const, line 1016
- `const borderLeft = focused || item.isFollowup ? COLOR.amber : item.isProbe ? COLOR.pink : "transparent"` — const, line 1017
- `function SurpriseInsertionBanner(` — function, line 1101
- `const coldProbe = followup.followupKind === "certification_cold_probe"` — const, line 1116
- `const coldRetry = followup.followupKind === "cold_retry"` — const, line 1123
- `const heading = coldProbe ? "validity check - held-out cold probe inserted" : coldRetry ? "unassisted check - answer this one cold" : "intervention gate - diagnostic follow-up inserted"` — const, line 1124
- `const noun = coldProbe ? "cold probe" : coldRetry ? "unassisted check" : "follow-up"` — const, line 1129
- `const WHY_ROWS: Array<` — const, line 1225
- `function WhyRow(` — function, line 1232
- `function QueueDetail(` — function, line 1244
- `const components = detail?.scheduler?.components ?? item.components` — const, line 1287
- `const variance = detail?.mastery?.variance ?? item.masteryVariance ?? 0.1` — const, line 1288
- `const mastery = detail?.mastery?.mean ?? item.mastery` — const, line 1289
- `const evidenceFacetButtonStyle: CSSProperties =` — const, line 1431
- `function QueueRankingStrip(` — function, line 1438
- `function scheduleChoiceClaim(item: ScheduledItemDto, producerVersion: string): ClaimCandidateDto` — function, line 1460
- `function OverconfidenceList(` — function, line 1476
- `const key = `$` — const, line 1507
- `const done = started.has(key)` — const, line 1508
- `function ReentryPanel(` — function, line 1534
- `const named = summary.slippedTop.map((f)` — const, line 1535
- `function NoGoalFallback(` — function, line 1565
- `const action = (label: string, onClick: ()` — const, line 1578
- `const dismiss = ( <button type="button" onClick=` — const, line 1594
- `const dismissBannerButtonStyle: CSSProperties =` — const, line 1652
- `function unique(values: string[]): string[]` — function, line 1663
- `function queueItems(snapshot: QueueSnapshot | null): ScheduledItemDto[]` — function, line 1667
- `function firstGoalFrontierItem(snapshot: QueueSnapshot | null): ScheduledItemDto | null` — function, line 1671
- `function useNowMinute(): Date` — function, line 1675
- `const id = window.setInterval(()` — const, line 1678
- `function remainingSessionMinutes(session: SessionSnapshot | null, now: Date): number | null` — function, line 1684
- `const startedAt = new Date(session.startedAt).getTime()` — const, line 1686
- `const elapsedMinutes = Math.max(0, Math.floor((now.getTime() - startedAt) / 60_000))` — const, line 1688
- `function formatHeroTime(date: Date): string` — function, line 1692
- `function formatSessionNumber(sessionId: string): string` — function, line 1696
- `const matches = sessionId.match(/\d+/g)` — const, line 1697
- `const digits = matches ? matches[matches.length - 1] : undefined` — const, line 1698
- `function relativeDue(item: ScheduledItemDto, now: Date): string` — function, line 1704
- `const due = new Date(item.dueAt).getTime()` — const, line 1707
- `const diffMs = due - now.getTime()` — const, line 1709
- `const past = diffMs < 0` — const, line 1710
- `const minutes = Math.round(Math.abs(diffMs) / 60_000)` — const, line 1711
- `const span = minutes < 1 ? "now" : minutes < 60 ? `$` — const, line 1712

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `TodayScreen`; references `TodayScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ClaimCandidateDto`, `DecayPressureDto`, `GoalDto`, `IngestBatchDto`, `OverconfidentFacetDto`, `PracticeItemDetail`, `QueueSection`, `QueueSnapshot`, `ReentrySummaryDto`, `ScheduledItemDto`, `SchedulerComponents`, `SessionEndSummary`, `SessionSnapshot`
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
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export; imports `notifyQueueChanged`, `subscribeQueueChanged`
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
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/TodayScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/TodayScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

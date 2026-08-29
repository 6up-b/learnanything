---
title: "Desktop module · src/components/GoalBanner.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.GoalBanner"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/GoalBanner.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/GoalBanner.tsx"
source_commit: "4bfee21b99e126a187df694660dbff4f7bb6cbea"
source_commit_timestamp: "2026-07-27T07:17:49-04:00"
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

# `src/components/GoalBanner.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `GoalBanner` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/GoalBanner.tsx](../../../../../../apps/learnloop-tauri/src/components/GoalBanner.tsx) |
| Source lines | 836 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `4bfee21b99e126a187df694660dbff4f7bb6cbea` |
| Commit timestamp | `2026-07-27T07:17:49-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] → [[Reference/Desktop/TypeScript/components/GoalBanner|src/components/GoalBanner.tsx]]

## Public API

- `export function GoalBanner(` — function, line 129

## Internal implementation anchors

- `function daysUntil(dueAt: string | null): number | null` — function, line 19
- `const due = Date.parse(dueAt)` — const, line 21
- `function dueLabel(dueAt: string | null): string` — function, line 26
- `const d = daysUntil(dueAt)` — const, line 27
- `function dueTone(dueAt: string | null): string` — function, line 35
- `const d = daysUntil(dueAt)` — const, line 36
- `function statusOf(attainment: number | null):` — function, line 44
- `const f = attainment ?? 0` — const, line 45
- `function actionOf(label: GoalAtRiskFacetDto["label"]): string` — function, line 51
- `const pct = (value: number | null | undefined): string` — const, line 57
- `const capitalize = (s: string): string` — const, line 60
- `function buildPaceSentence(report: GoalReportSummaryDto, pace: GoalPaceDto, dueAt: string | null): string` — function, line 65
- `const remaining = report.attemptsRemaining ?? pace.attemptsRemaining` — const, line 66
- `const partial = report.attemptsRemainingIsPartial === true` — const, line 67
- `const dLeft = pace.daysLeft` — const, line 68
- `const overdue = (daysUntil(dueAt) ?? 0) < 0` — const, line 69
- `const head = `≈ $` — const, line 78
- `const paceNoun = pace.paceKind === "qualifying" ? "goal pace" : "recent activity"` — const, line 80
- `const allow = dLeft == null ? "the due date is open-ended" : overdue ? `the due date passed $` — const, line 82
- `const days = Math.max(1, Math.ceil(remaining / pace.attemptsPerDay))` — const, line 94
- `const verdict = overdue ? "Behind — past due." : pace.onPace ? "On pace." : `Behind pace — $` — const, line 95
- `function SegmentBar(` — function, line 104
- `const cells = Math.min(width, Math.max(total, 1))` — const, line 116
- `const certCells = Math.round((certified / total) * cells)` — const, line 117
- `const examCells = Math.max(Math.round((examined / total) * cells) - certCells, 0)` — const, line 118
- `const restCells = Math.max(cells - certCells - examCells, 0)` — const, line 119
- `const goal = useMemo(()` — const, line 145
- `const goalId = goal?.id` — const, line 171
- `const report = goal?.report ?? null` — const, line 172
- `let cancelled = false` — let, line 182
- `let cancelled = false` — let, line 209
- `let cancelled = false` — let, line 230
- `const certifiedCount = report?.certifiedCount` — const, line 260
- `const key = `learnloop.goalCertified.$` — const, line 263
- `const previous = Number(window.localStorage.getItem(key) ?? "0")` — const, line 264
- `const hasDualAxis = report?.attainmentFraction !== undefined` — const, line 273
- `const attainment = report?.attainmentFraction ?? report?.onTrackFraction ?? null` — const, line 274
- `const status = statusOf(attainment)` — const, line 275
- `const targetPct = Math.round(goal.targetRecall * 100)` — const, line 276
- `const tone = goal.dueAt ? dueTone(goal.dueAt) : status.color` — const, line 277
- `const lastTwo = series && series.length >= 2 ? series.slice(-2) : null` — const, line 280
- `const certDelta = lastTwo && lastTwo[0].certifiedCount != null && lastTwo[1].certifiedCount != null ? (lastTwo[1].certifiedCount ?? 0) - (lastTwo[0].certifiedCount ?? 0) : null` — const, line 281
- `const attainDelta = lastTwo && lastTwo[0].attainmentFraction != null && lastTwo[1].attainmentFraction != null ? (lastTwo[1].attainmentFraction ?? 0) - (lastTwo[0].attainmentFraction ?? 0) : lastTwo ? (lastTwo[1].onTrackFraction ?? 0) - (lastTwo[0].onTrackFrac…` — const, line 285
- `const pace = report?.pace ?? null` — const, line 292
- `const atRiskCount = report?.atRiskCount ?? 0` — const, line 293
- `const examWanted = Boolean(onTakeExam && goal.exam.enabled && exam && !examStatusFailed)` — const, line 296
- `const showExamButton = Boolean(examWanted && exam && exam.poolItemCount > 0)` — const, line 297
- `const examDeferred = Boolean(examWanted && !showExamButton && exam?.reservationDeferred)` — const, line 298
- `const examUncovered = exam?.uncoveredFacets ?? []` — const, line 299
- `const examUncoveredShown = examUncovered.slice(0, 3)` — const, line 300
- `const paceOverdue = (daysUntil(goal.dueAt) ?? 0) < 0` — const, line 301
- `const paceZero = pace != null && (pace.attemptsLast14d <= 0 || pace.attemptsPerDay <= 0)` — const, line 302
- `const paceRemaining = report?.attemptsRemaining ?? pace?.attemptsRemaining ?? null` — const, line 303
- `const paceTone = paceOverdue ? COLOR.pink : paceZero || paceRemaining == null ? COLOR.textDim : pace?.onPace === false ? COLOR.amber : COLOR.green` — const, line 304
- `const paceForecast = report?.activeForecasts?.pace ?? null` — const, line 316
- `const paceSentence = report && pace ? buildPaceSentence(report, pace, goal.dueAt) : null` — const, line 317
- `async function saveIntent()` — function, line 319
- `const canProject = pace != null && pace.attemptsPerDay > 0 && paceRemaining != null && paceRemaining > 0` — const, line 335
- `async function applyPlanningOverride(daysPerWeek: number)` — function, line 336
- `let pid = presentationId` — let, line 340
- `const candidate: ClaimCandidateDto =` — const, line 342
- `const result = await api.presentClaims([` — const, line 354
- `const rate = pace?.attemptsPerDay ?? 0` — const, line 359
- `const projected = canProject && rate > 0 ? Math.max(1, Math.ceil((paceRemaining as number) / (rate * (daysPerWeek / 7)))) : null` — const, line 360
- `const detail = report.attemptsRemainingDetail` — const, line 566
- `const unreachable = detail?.unreachable ?? (atRisk ? atRisk.filter((f)` — const, line 567
- `const noSupply = detail?.noSupply ?? (atRisk ? atRisk.filter( (f)` — const, line 572
- `const lowerBound = detail?.lowerBound ?? (atRisk ? atRisk.filter((f)` — const, line 581
- `const causes: string[] = []` — const, line 586
- `const message = causes.length > 0 ? `$` — const, line 602
- `const projected = Math.max(1, Math.ceil((paceRemaining as number) / (pace.attemptsPerDay * (scenarioDays / 7))))` — const, line 666
- `function btnStyle(color: string)` — function, line 824

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `GoalBanner`; references `GoalBanner`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ClaimCandidateDto`, `ExamStatusSnapshot`, `GoalAtRiskFacetDto`, `GoalDto`, `GoalPaceDto`, `GoalReportSummaryDto`, `GoalSeriesPointDto`
- [[Reference/Desktop/TypeScript/components/ClaimSurface|src/components/ClaimSurface.tsx]] — import-or-re-export; imports `mintVisitId`
- [[Reference/Desktop/TypeScript/components/GoalTrajectoryChart|src/components/GoalTrajectoryChart.tsx]] — import-or-re-export; imports `GoalTrajectoryChart`
- [[Reference/Desktop/TypeScript/components/TrackRecordView|src/components/TrackRecordView.tsx]] — import-or-re-export; imports `TrackRecordView`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `BlockBar`, `COLOR`, `FONT_MONO`, `Faint`, `Pill`, `measurementStateLabel`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Goals Exams and Certification Workflow|Goals, Exams, and Certification Workflow]] — owns the end-to-end goal path.
- [[Concepts/Goals and Certification|Goals and Certification]] — owns goal and certification semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_sidecar_goals.py](../../../../../../tests/test_sidecar_goals.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_goal_projection.py](../../../../../../tests/test_goal_projection.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_exam_session.py](../../../../../../tests/test_exam_session.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/GoalBanner.tsx](../../../../../../apps/learnloop-tauri/src/components/GoalBanner.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

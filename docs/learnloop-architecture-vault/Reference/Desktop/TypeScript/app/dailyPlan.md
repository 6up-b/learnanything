---
title: "Desktop module · src/app/dailyPlan.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.dailyPlan"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/dailyPlan.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/dailyPlan.ts"
source_commit: "f837a8a7b4070a36aa3288598d59a614f603e47a"
source_commit_timestamp: "2026-11-09T11:20:01-05:00"
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

# `src/app/dailyPlan.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `aboutMinutes`, `minutesPerDay`, `wholeMinutes`, `dailyPlanKey` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/dailyPlan.ts](../../../../../../apps/learnloop-tauri/src/app/dailyPlan.ts) |
| Source lines | 197 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `f837a8a7b4070a36aa3288598d59a614f603e47a` |
| Commit timestamp | `2026-11-09T11:20:01-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]]

## Public API

- `export function aboutMinutes(minutes: number | null | undefined): string` — function, line 17
- `export function minutesPerDay(minutes: number | null | undefined): string` — function, line 26
- `export function wholeMinutes(minutes: number | null | undefined): number` — function, line 34
- `export function dailyPlanKey(sessionId: string | null | undefined): QueryKey` — function, line 38
- `export function useDailyPlan(sessionId: string | null | undefined, enabled = true)` — function, line 43
- `export type PlanStepAction = |` — type, line 53
- `export function planStepAction(step: PlanStepDto | null | undefined,` — function, line 64
- `export function readerTargetForReading( reading: PlanReadingDto, library: SourceLibraryCard[] | null | undefined ):` — function, line 83
- `export async function servedForExplicitStep(sessionId: string, next: PlanStepDto | null): Promise<PlanStepDto | null>` — function, line 98
- `export interface NextPlanStep` — interface, line 110
- `export function useNextPlanStep(sessionId: string | null, prefetch: boolean): NextPlanStep` — function, line 125
- `export function waitingMinutes(until: string, fallback: number, now: number = Date.now()): number` — function, line 157
- `export function waitingLine(waiting:` — function, line 164
- `export function questionInProgressLine(question:` — function, line 171
- `export function rereadPlanAfterWorkbenchClosed(): void` — function, line 181
- `export function nextPlanKeyLabel(advancing: boolean, step: PlanStepDto | null): string` — function, line 186

## Internal implementation anchors

- `const value = Math.max(1, Math.round(minutes ?? 0))` — const, line 18
- `const value = Math.max(0, minutes ?? 0)` — const, line 27
- `const id = sessionId ?? null` — const, line 44
- `const key = useMemo(()` — const, line 46
- `const card = (library ?? []).find((entry)` — const, line 87
- `const served = (await api.nextPlanItem(` — const, line 100
- `const served = await api.nextPlanItem(` — const, line 104
- `const MAX_STEP_READS = 4` — const, line 117
- `const hash = sessionId ? hashKey(["next_plan_item", sessionId]) : null` — const, line 126
- `const key = useMemo<QueryKey | null>(()` — const, line 128
- `const query = useCachedQuery<DailyPlanDto>( prefetch ? key : null, ()` — const, line 129
- `const current = query.data !== undefined && !query.refreshing` — const, line 134
- `const step = current ? query.data?.step ?? null : null` — const, line 135
- `const resolve = useCallback(async (): Promise<PlanStepDto | null>` — const, line 137
- `const snapshot = await getOrFetch<DailyPlanDto>(key, ()` — const, line 140
- `const state = peek<DailyPlanDto>(key)` — const, line 144
- `const at = Date.parse(until)` — const, line 158
- `const minutes = waitingMinutes(waiting.until, waiting.minutes, now)` — const, line 165
- `const what = waiting.learningObjectTitle ? `a question on $` — const, line 166
- `const what = question.learningObjectTitle ? ` on $` — const, line 172

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `planStepAction`, `readerTargetForReading`, `servedForExplicitStep`, `useDailyPlan`; references `planStepAction`, `readerTargetForReading`, `servedForExplicitStep`, `useDailyPlan`
- [[Reference/Desktop/TypeScript/app/todayPlan|src/app/todayPlan.ts]] — import-or-re-export: `aboutMinutes`, `wholeMinutes`; references `aboutMinutes`, `wholeMinutes`
- [[Reference/Desktop/TypeScript/components/PlanReadingBanner|src/components/PlanReadingBanner.tsx]] — import-or-re-export: `aboutMinutes`; references `aboutMinutes`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `nextPlanKeyLabel`, `useNextPlanStep`; references `nextPlanKeyLabel`, `useNextPlanStep`
- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `aboutMinutes`, `useDailyPlan`; references `aboutMinutes`, `useDailyPlan`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `planStepAction`, `useDailyPlan`; references `planStepAction`, `useDailyPlan`
- [[Reference/Desktop/TypeScript/screens/today/DailyPlanView|src/screens/today/DailyPlanView.tsx]] — import-or-re-export: `aboutMinutes`, `minutesPerDay`, `questionInProgressLine`, `waitingLine`, `waitingMinutes`, `wholeMinutes`; references `aboutMinutes`, `minutesPerDay`, `questionInProgressLine`, `waitingLine`, `waitingMinutes`, `wholeMinutes`
- [[Reference/Desktop/TypeScript/screens/today/QuestionInProgress|src/screens/today/QuestionInProgress.tsx]] — import-or-re-export: `rereadPlanAfterWorkbenchClosed`; references `rereadPlanAfterWorkbenchClosed`
- [[Reference/Desktop/TypeScript/screens/today/SomethingElse|src/screens/today/SomethingElse.tsx]] — import-or-re-export: `useDailyPlan`; references `useDailyPlan`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `aboutMinutes`, `planStepAction`, `questionInProgressLine`, `useDailyPlan`, `waitingLine`; references `aboutMinutes`, `planStepAction`, `questionInProgressLine`, `useDailyPlan`, `waitingLine`
- [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchSession|src/screens/workbench/useWorkbenchSession.ts]] — import-or-re-export: `rereadPlanAfterWorkbenchClosed`; references `rereadPlanAfterWorkbenchClosed`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DailyPlanDto`, `PlanItemStepDto`, `PlanReadingDto`, `PlanStepDto`, `SourceLibraryCard`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export; imports `QueryKey`, `getOrFetch`, `hashKey`, `invalidate`, `isStale`, `peek`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/app/dailyPlan.test.tsx](../../../../../../apps/learnloop-tauri/src/app/dailyPlan.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/dailyPlan.ts](../../../../../../apps/learnloop-tauri/src/app/dailyPlan.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

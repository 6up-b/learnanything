---
title: "Desktop module · src/app/todayPlan.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.todayPlan"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/todayPlan.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/todayPlan.ts"
source_commit: "838d8ee1fcee48de3b5b41f59e451f042ec9a690"
source_commit_timestamp: "2026-11-05T04:03:05-05:00"
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

# `src/app/todayPlan.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `dayPhrase`, `TodayRow`, `onYourOwnItem`, `todayRows` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/todayPlan.ts](../../../../../../apps/learnloop-tauri/src/app/todayPlan.ts) |
| Source lines | 358 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `838d8ee1fcee48de3b5b41f59e451f042ec9a690` |
| Commit timestamp | `2026-11-05T04:03:05-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/todayPlan|src/app/todayPlan.ts]]

## Public API

- `export function dayPhrase(now: Date = new Date()): string` — function, line 31
- `export interface TodayRow` — interface, line 92
- `export function onYourOwnItem(item: PlanItemDto): boolean` — function, line 142
- `export function todayRows(plan: Plan): TodayRow[]` — function, line 148
- `export function planSentence(plan: Plan): string | null` — function, line 176
- `export function reentrySentence(plan: Plan): string` — function, line 216
- `export function reentryWhy(plan: Plan): string | null` — function, line 222
- `export function splitWhy(plan: Plan): string[]` — function, line 231
- `export function doneLine(data: DailyPlanDto): string` — function, line 246
- `export function planWasEmpty(data: DailyPlanDto): boolean` — function, line 252
- `export function streakLine(streak: StreakSummary | null | undefined): string | null` — function, line 257
- `export const THREADS_SHOWN = 3` — const, line 265
- `export type TodayThread = |` — type, line 267
- `export function questionThread(row: QuestionQueueRowDto): TodayThread` — function, line 277
- `export function problemThread(problem: WorkbenchOpenProblemDto): TodayThread` — function, line 288
- `export function todayThreads(questionRows: readonly QuestionQueueRowDto[], problems: readonly WorkbenchOpenProblemDto[]): TodayThread[]` — function, line 294
- `export function fullListWhy(item: ScheduledItemDto): string` — function, line 307
- `export function onYourOwnWhy(item: ScheduledItemDto): string | null` — function, line 329
- `export async function implicitSessionMinutes(): Promise<number | null>` — function, line 344

## Internal implementation anchors

- `type Plan = DailyPlanBodyDto` — type, line 28
- `const weekday = now.toLocaleDateString(undefined,` — const, line 32
- `const hour = now.getHours()` — const, line 33
- `const part = hour < 5 ? "night" : hour < 12 ? "morning" : hour < 17 ? "afternoon" : hour < 22 ? "evening" : "night"` — const, line 35
- `function titles(list: readonly string[]): string` — function, line 39
- `const unique = [...new Set(list.filter(Boolean))]` — const, line 40
- `function questions(count: number): string` — function, line 45
- `function lanePhrase(lane: PlanLane | null, itemCount: number, loTitles: readonly string[]): string` — function, line 50
- `const about = titles(loTitles)` — const, line 51
- `function laneRow(lane: PlanLane | null, itemCount: number, loTitles: readonly string[]): string` — function, line 67
- `const about = titles(loTitles)` — const, line 68
- `function readingStarted(block: PlanBlockDto): boolean` — function, line 83
- `function readingTitle(title: string | null | undefined): string` — function, line 87
- `function chosenRow(block: PlanBlockDto, current: boolean): TodayRow` — function, line 107
- `let text: string` — let, line 108
- `const items = block.items.filter((item)` — const, line 114
- `function projectedRow(block: PlanProjectedBlockDto): TodayRow` — function, line 128
- `const text = block.readingTitle ? `Read $` — const, line 129
- `const rows: TodayRow[] = []` — const, line 149
- `function sentencePhrase(row:` — function, line 158
- `function joinPhrases(phrases: string[]): string` — function, line 164
- `function minutesWord(minutes: number): string` — function, line 170
- `const phrases: string[] = []` — const, line 177
- `const begun = plan.blocks.some((block)` — const, line 197
- `const past = Math.round(plan.minutesPastPlan ?? 0)` — const, line 200
- `const suggested = begun ? past > 0 ? `About $` — const, line 201
- `const head = begun ? `About $` — const, line 208
- `const minutes = plan.reentry ? Math.max(1, Math.round(plan.reentry.planMinutes)) : Math.max(1, Math.round(plan.minutesBudget))` — const, line 217
- `const reentry = plan.reentry` — const, line 223
- `const away = `You were away $` — const, line 225
- `const named = reentry.slippedNames.length ? ` Today's catch-up starts with what faded most: $` — const, line 226
- `const words: Record<PlanLane, string> =` — const, line 232
- `const lines = plan.split.lanes .filter((lane)` — const, line 238
- `const minutes = wholeMinutes(data.day?.actualMinutes)` — const, line 247
- `const days = `$` — const, line 259
- `function oneLine(markdown: string, limit = 80): string` — function, line 271
- `const text = markdown.replace(/\s+/g, " ").replace(/[*_`#>]/g, "").trim()` — const, line 272
- `const steps = problem.stepCount === 1 ? "1 step written" : problem.stepCount > 1 ? `$` — const, line 289
- `const open = questionRows.filter((row)` — const, line 295
- `const dated: Array<` — const, line 296
- `const plan = await api.getDailyPlan(null)` — const, line 346
- `const summary = await api.getStartSummary()` — const, line 352

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `implicitSessionMinutes`; references `implicitSessionMinutes`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `THREADS_SHOWN`, `TodayThread`, `dayPhrase`, `doneLine`, `fullListWhy`, `onYourOwnWhy`, `planSentence`, `planWasEmpty`, `reentrySentence`, `reentryWhy`, `splitWhy`, `streakLine`, `todayRows`, `todayThreads`; references `THREADS_SHOWN`, `TodayThread`, `dayPhrase`, `doneLine`, `fullListWhy`, `onYourOwnWhy`, `planSentence`, `planWasEmpty`, `reentrySentence`, `reentryWhy`, `splitWhy`, `streakLine`, `todayRows`, `todayThreads`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DailyPlanBodyDto`, `DailyPlanDto`, `PlanBlockDto`, `PlanItemDto`, `PlanLane`, `PlanProjectedBlockDto`, `QuestionQueueRowDto`, `ScheduledItemDto`, `StreakSummary`, `WorkbenchOpenProblemDto`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `aboutMinutes`, `wholeMinutes`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/app/todayPlan.test.ts](../../../../../../apps/learnloop-tauri/src/app/todayPlan.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/todayPlan.ts](../../../../../../apps/learnloop-tauri/src/app/todayPlan.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

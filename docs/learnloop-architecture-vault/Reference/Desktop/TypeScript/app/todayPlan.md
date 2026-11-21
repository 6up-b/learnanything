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
| Source lines | 413 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/todayPlan|src/app/todayPlan.ts]]

## Public API

- `export function dayPhrase(now: Date = new Date()): string` — function, line 34
- `export interface TodayRow` — interface, line 95
- `export function onYourOwnItem(item: PlanItemDto): boolean` — function, line 148
- `export function todayRows(plan: Plan): TodayRow[]` — function, line 154
- `export function planSentence(plan: Plan): string | null` — function, line 197
- `export function reentrySentence(plan: Plan): string` — function, line 239
- `export function reentryWhy(plan: Plan): string | null` — function, line 245
- `export function splitWhy(plan: Plan): string[]` — function, line 254
- `export function doneLine(data: DailyPlanDto): string` — function, line 273
- `export const GOAL_NOTHING_READY = "Nothing for this goal is ready to practise yet."` — const, line 281
- `export function planWasEmpty(data: DailyPlanDto): boolean` — function, line 284
- `export function streakLine(streak: StreakSummary | null | undefined): string | null` — function, line 289
- `export const THREADS_SHOWN = 3` — const, line 297
- `export type TodayThread = |` — type, line 299
- `export function questionThread(row: QuestionQueueRowDto): TodayThread` — function, line 310
- `export function problemThread(problem: WorkbenchOpenProblemDto): TodayThread` — function, line 321
- `export function todayThreads(questionRows: readonly QuestionQueueRowDto[], problems: readonly WorkbenchOpenProblemDto[]): TodayThread[]` — function, line 327
- `export function fullListWhy(item: ScheduledItemDto, now: number = Date.now(), next?: NextPracticeDto | null): string` — function, line 346
- `export function onYourOwnWhy(item: ScheduledItemDto): string | null` — function, line 384
- `export async function implicitSessionMinutes(): Promise<number | null>` — function, line 399

## Internal implementation anchors

- `type Plan = DailyPlanBodyDto` — type, line 31
- `const weekday = now.toLocaleDateString(undefined,` — const, line 35
- `const hour = now.getHours()` — const, line 36
- `const part = hour < 5 ? "night" : hour < 12 ? "morning" : hour < 17 ? "afternoon" : hour < 22 ? "evening" : "night"` — const, line 38
- `function titles(list: readonly string[]): string` — function, line 42
- `const unique = [...new Set(list.filter(Boolean))]` — const, line 43
- `function questions(count: number): string` — function, line 48
- `function lanePhrase(lane: PlanLane | null, itemCount: number, loTitles: readonly string[]): string` — function, line 53
- `const about = titles(loTitles)` — const, line 54
- `function laneRow(lane: PlanLane | null, itemCount: number, loTitles: readonly string[]): string` — function, line 70
- `const about = titles(loTitles)` — const, line 71
- `function readingStarted(block: PlanBlockDto): boolean` — function, line 86
- `function readingTitle(title: string | null | undefined): string` — function, line 90
- `function chosenRow(block: PlanBlockDto, current: boolean): TodayRow` — function, line 110
- `let text: string` — let, line 111
- `const items = block.items.filter((item)` — const, line 120
- `function projectedRow(block: PlanProjectedBlockDto): TodayRow` — function, line 134
- `const text = block.readingTitle ? `Read $` — const, line 135
- `const rows: TodayRow[] = []` — const, line 155
- `function sentencePhrase(row:` — function, line 164
- `function joinPhrases(phrases: string[]): string` — function, line 171
- `function minutesWord(minutes: number): string` — function, line 177
- `function roomWords(minutesLeft: number): string` — function, line 182
- `const minutes = Math.max(1, Math.round(minutesLeft))` — const, line 183
- `const phrases: string[] = []` — const, line 198
- `const begun = plan.blocks.some((block)` — const, line 219
- `const list = `$` — const, line 220
- `const past = Math.round(plan.minutesPastPlan ?? 0)` — const, line 223
- `const suggested = begun ? past > 0 ? `About $` — const, line 224
- `const head = begun ? `Room for $` — const, line 231
- `const minutes = plan.reentry ? Math.max(1, Math.round(plan.reentry.planMinutes)) : Math.max(1, Math.round(plan.minutesBudget))` — const, line 240
- `const reentry = plan.reentry` — const, line 246
- `const away = `You were away $` — const, line 248
- `const named = reentry.slippedNames.length ? ` Today's catch-up starts with what faded most: $` — const, line 249
- `const words: Record<PlanLane, string> =` — const, line 255
- `const lines = plan.split.lanes .filter((lane)` — const, line 261
- `const minutes = wholeMinutes(data.day?.actualMinutes)` — const, line 274
- `const reading = (data.day?.readingBlocks ?? 0) > 0 ? " and reading" : ""` — const, line 276
- `const days = `$` — const, line 291
- `function oneLine(markdown: string, limit = 80): string` — function, line 304
- `const text = plainMathLine(markdown)` — const, line 305
- `const steps = problem.stepCount === 1 ? "1 step written" : problem.stepCount > 1 ? `$` — const, line 322
- `const open = questionRows.filter((row)` — const, line 328
- `const dated: Array<` — const, line 329
- `function localDay(time: number): string` — function, line 367
- `const date = new Date(time)` — const, line 368
- `function laterWhy(dueAt: string | null, now: number): string` — function, line 372
- `const due = dueAt ? Date.parse(dueAt) : Number.NaN` — const, line 373
- `const today = localDay(now)` — const, line 376
- `const day = localDay(due)` — const, line 377
- `const days = daysFrom(today, day) ?? 0` — const, line 378
- `const plan = await api.getDailyPlan(null)` — const, line 401
- `const summary = await api.getStartSummary()` — const, line 407

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `implicitSessionMinutes`; references `implicitSessionMinutes`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `GOAL_NOTHING_READY`, `THREADS_SHOWN`, `TodayThread`, `dayPhrase`, `doneLine`, `fullListWhy`, `onYourOwnWhy`, `planSentence`, `planWasEmpty`, `reentrySentence`, `reentryWhy`, `splitWhy`, `streakLine`, `todayRows`, `todayThreads`; references `GOAL_NOTHING_READY`, `THREADS_SHOWN`, `TodayThread`, `dayPhrase`, `doneLine`, `fullListWhy`, `onYourOwnWhy`, `planSentence`, `planWasEmpty`, `reentrySentence`, `reentryWhy`, `splitWhy`, `streakLine`, `todayRows`, `todayThreads`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DailyPlanBodyDto`, `DailyPlanDto`, `NextPracticeDto`, `PlanBlockDto`, `PlanItemDto`, `PlanLane`, `PlanProjectedBlockDto`, `QuestionQueueRowDto`, `ScheduledItemDto`, `StreakSummary`, `WorkbenchOpenProblemDto`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `aboutMinutes`, `wholeMinutes`
- [[Reference/Desktop/TypeScript/app/nextPractice|src/app/nextPractice.ts]] — import-or-re-export; imports `dayName`, `daysFrom`, `nextPracticeRowWhy`
- [[Reference/Desktop/TypeScript/render/mathSnippet|src/render/mathSnippet.ts]] — import-or-re-export; imports `plainMathLine`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/today/LessonOfferBlock.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/today/LessonOfferBlock.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/render/sourceMacros.test.tsx](../../../../../../apps/learnloop-tauri/src/render/sourceMacros.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/todayPlan.test.ts](../../../../../../apps/learnloop-tauri/src/app/todayPlan.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/todayPlan.ts](../../../../../../apps/learnloop-tauri/src/app/todayPlan.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

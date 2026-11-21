---
title: "Desktop module · src/app/nextPractice.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.nextPractice"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/nextPractice.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/nextPractice.ts"
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

# `src/app/nextPractice.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `daysFrom`, `dayName`, `NextPracticeWordsOptions`, `nextPracticeLines` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/nextPractice.ts](../../../../../../apps/learnloop-tauri/src/app/nextPractice.ts) |
| Source lines | 161 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/todayPlan|src/app/todayPlan.ts]] → [[Reference/Desktop/TypeScript/app/nextPractice|src/app/nextPractice.ts]]

## Public API

- `export function daysFrom(today: string, date: string): number | null` — function, line 24
- `export function dayName(date: string, today: string): string` — function, line 38
- `export interface NextPracticeWordsOptions` — interface, line 64
- `export function nextPracticeLines(next: NextPracticeDto | null | undefined, options: NextPracticeWordsOptions =` — function, line 79
- `export function nextPracticeRowWhy(next: NextPracticeDto | null | undefined, item: Pick<ScheduledItemDto, "practiceItemId">): string | null` — function, line 124
- `export function useLatestNextPractice(next: NextPracticeDto | null | undefined): NextPracticeDto | null` — function, line 141
- `export function useNextDayRefresh(nextDayStartsAt: string | null | undefined, refresh: ()` — function, line 149

## Internal implementation anchors

- `const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]` — const, line 12
- `const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]` — const, line 13
- `const WEEKDAY_SPAN = 6` — const, line 15
- `function dayNumber(date: string): number | null` — function, line 17
- `const match = /^(\d` — const, line 18
- `const a = dayNumber(today)` — const, line 25
- `const b = dayNumber(date)` — const, line 26
- `function dateWords(date: string, today: string): string` — function, line 30
- `const day = new Date(dayNumber(date)! * 86_400_000)` — const, line 31
- `const year = day.getUTCFullYear()` — const, line 32
- `const sameYear = today.slice(0, 4) === String(year)` — const, line 33
- `const days = daysFrom(today, date)` — const, line 39
- `function onDay(date: string, today: string): string` — function, line 48
- `const days = daysFrom(today, date)` — const, line 49
- `const name = dayName(date, today)` — const, line 50
- `function count(n: number, one: string, many: string): string` — function, line 54
- `function aboutMinutes(minutes: number | null | undefined): string` — function, line 58
- `const whole = Math.max(1, Math.round(minutes))` — const, line 60
- `function groupOn(groups: readonly NextPracticeGroupDto[], date: string): NextPracticeGroupDto | undefined` — function, line 73
- `const lines: string[] = []` — const, line 82
- `const dueToday = groupOn(next.reviews, today)` — const, line 83
- `const dueTomorrow = groupOn(next.reviews, tomorrow)` — const, line 84
- `const writing = options.writing !== false && next.writing.topicCount > 0` — const, line 85
- `const waiting = options.writing !== false ? next.waiting?.sectionCount ?? 0 : 0` — const, line 89
- `const laterCheck = next.checks.find((group)` — const, line 90
- `const checkNow = groupOn(next.checks, today)` — const, line 91
- `const more = dueToday ? "more " : ""` — const, line 96
- `const group = groupOn(next.reviews, next.nextReviewDate)` — const, line 100
- `const one = group?.count === 1` — const, line 101
- `const from = `available from $` — const, line 110
- `const today = next.calendar.today` — const, line 126
- `const check = next.checks.find((group)` — const, line 127
- `const days = daysFrom(today, check.date) ?? 0` — const, line 129
- `const review = next.reviews.find((group)` — const, line 132
- `const days = daysFrom(today, review.date) ?? 0` — const, line 134
- `const latest = useRef<NextPracticeDto | null>(null)` — const, line 142
- `const refreshRef = useRef(refresh)` — const, line 150
- `const at = Date.parse(nextDayStartsAt)` — const, line 154
- `const delay = Math.min(Math.max(at - Date.now(), 0) + 1000, 2_000_000_000)` — const, line 157
- `const timer = window.setTimeout(()` — const, line 158

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/todayPlan|src/app/todayPlan.ts]] — import-or-re-export: `dayName`, `daysFrom`, `nextPracticeRowWhy`; references `dayName`, `daysFrom`, `nextPracticeRowWhy`
- [[Reference/Desktop/TypeScript/components/SessionFinishHud|src/components/SessionFinishHud.tsx]] — import-or-re-export: `nextPracticeLines`; references `nextPracticeLines`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `nextPracticeLines`, `useLatestNextPractice`, `useNextDayRefresh`; references `nextPracticeLines`, `useLatestNextPractice`, `useNextDayRefresh`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `NextPracticeDto`, `NextPracticeGroupDto`, `ScheduledItemDto`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/copy/denyList.test.tsx](../../../../../../apps/learnloop-tauri/src/copy/denyList.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/nextPractice.test.ts](../../../../../../apps/learnloop-tauri/src/app/nextPractice.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_large_practice_flow.py](../../../../../../tests/test_large_practice_flow.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_practice_information.py](../../../../../../tests/test_practice_information.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/nextPractice.ts](../../../../../../apps/learnloop-tauri/src/app/nextPractice.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

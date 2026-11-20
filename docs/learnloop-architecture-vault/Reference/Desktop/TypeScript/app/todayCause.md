---
title: "Desktop module · src/app/todayCause.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.todayCause"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/todayCause.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/todayCause.ts"
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

# `src/app/todayCause.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `CONSENT_ACTION`, `SIDECAR_CONSENT_LABEL`, `readableTitle`, `TodayCause` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/todayCause.ts](../../../../../../apps/learnloop-tauri/src/app/todayCause.ts) |
| Source lines | 368 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/todayCause|src/app/todayCause.ts]]

## Public API

- `export const CONSENT_ACTION = "Give your OK"` — const, line 35
- `export const SIDECAR_CONSENT_LABEL = "Review"` — const, line 38
- `export function readableTitle(title: string): string` — function, line 42
- `export type TodayCause = /** Today's list still has questions: the plan stopped with something left. */ |` — type, line 58
- `export function partName(labels: readonly string[], sectionCount: number): string | null` — function, line 119
- `export function todayCause(input:` — function, line 132
- `export function causeWait(cause: TodayCause):` — function, line 243
- `export function causeSentence(cause: TodayCause): string` — function, line 266
- `export const GOAL_NOTHING_LEAD = "Nothing for this goal is ready to practise yet:"` — const, line 308
- `export const GOAL_NOT_UP_TODAY = "Nothing for this goal is up today. Its questions come back on the days they're due."` — const, line 309
- `export function goalCauseSentence(cause: TodayCause): string` — function, line 311
- `export const PLAN_FINISHED = "Nothing else is needed today."` — const, line 320
- `export const PLAN_STOPPED_WITH_MORE = "The plan stopped here, but there's more for today if you'd like it."` — const, line 323
- `export const KEEP_GOING_NOTHING_LEAD = "Nothing more to plan today."` — const, line 326
- `export function continueLessonLine(title: string): string` — function, line 329
- `export const LESSON_KEPT = "Your lesson is kept. It's on Today when you want it."` — const, line 334
- `export function causeActionLabel(cause: TodayCause): string | null` — function, line 337
- `export function causeSendsPassages(cause: TodayCause): boolean` — function, line 364
- `export const WHATS_SENT = "what's sent"` — const, line 368

## Internal implementation anchors

- `const trimmed = (title || "").trim()` — const, line 43
- `const name = decodeURIComponent(trimmed.split("/").pop() ?? trimmed).replace(/\.[A-Za-z0-9]` — const, line 45
- `const words = name.split(/[_\-.\s]+/).filter(Boolean)` — const, line 46
- `const lower = words.every((word)` — const, line 48
- `const FAILURE_RETRY_LABELS: ReadonlySet<string> = new Set(["Retry", "Try again"])` — const, line 56
- `function shownLine(card: SourceLibraryCard, ai: AiConnectionDto | null): SourceStatusLineDto | null` — function, line 89
- `function questionsOf(card: SourceLibraryCard): ReadingQuestionsDto | null` — function, line 95
- `type Rank = "waiting_ok" | "needs_ai" | "failed" | "section_failed" | "needs_look" | "on_the_way" | "section_writing" | "section_waiting"` — type, line 99
- `const ORDER: readonly Rank[] = ["waiting_ok", "needs_ai", "failed", "section_failed", "needs_look", "on_the_way", "section_writing", "section_waiting"]` — const, line 100
- `function rankOf(line: SourceStatusLineDto | null, ai: AiConnectionDto | null): Rank | null` — function, line 102
- `const action = line.action` — const, line 104
- `const consent = ai ? ai.needs === "consent" || (ai.needs === null && action.label === SIDECAR_CONSENT_LABEL) : action.label === SIDECAR_CONSENT_LABEL` — const, line 107
- `const named = [...new Set(labels.map((label)` — const, line 120
- `const unknown = input.listUnknown === true` — const, line 140
- `const readable = input.cards.filter((card)` — const, line 142
- `const listed = input.listItemIds ?? []` — const, line 145
- `const questions = questionsOf(card)` — const, line 147
- `const own = new Set(questions?.itemIds ?? [])` — const, line 148
- `const mine = listed.filter((id)` — const, line 149
- `const found: Array<` — const, line 156
- `const rank = rankOf(shownLine(card, input.ai), input.ai)` — const, line 158
- `const questions = questionsOf(card)` — const, line 161
- `const rank = rankOf(entry.statusLine, input.ai)` — const, line 167
- `const hits = found.filter((entry)` — const, line 173
- `const first = hits[0]` — const, line 174
- `const line = first.card?.statusLine ?? null` — const, line 176
- `const questions = first.card ? questionsOf(first.card) : null` — const, line 177
- `const stopped = questions?.failed ?? []` — const, line 192
- `const waiting = questions?.waiting?.length ?` — const, line 199
- `const questions = questionsOf(card)` — const, line 211
- `const withQuestions = readable.find((card)` — const, line 214
- `const questions = questionsOf(withQuestions) as ReadingQuestionsDto` — const, line 216
- `const unfinished = readable.find((card)` — const, line 221
- `function questionsWord(count: number): string` — function, line 227
- `function waitingWords(title: string, part: string | null): string` — function, line 232
- `function minutesWords(minutes: number): string` — function, line 238
- `const amount = cause.progress && cause.progress.total > 0 ? ` · $` — const, line 246
- `const usually = cause.minutes !== null ? ` · $` — const, line 247
- `const wait = causeWait(cause) as` — const, line 291
- `const sentence = causeSentence(cause)` — const, line 312
- `const joined = sentence.startsWith("LearnLoop") ? sentence : `$` — const, line 314

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `LESSON_KEPT`; references `LESSON_KEPT`
- [[Reference/Desktop/TypeScript/components/BookCard|src/components/BookCard.tsx]] — import-or-re-export: `CONSENT_ACTION`, `SIDECAR_CONSENT_LABEL`, `readableTitle`; references `CONSENT_ACTION`, `SIDECAR_CONSENT_LABEL`, `readableTitle`
- [[Reference/Desktop/TypeScript/screens/reader/GuideRail|src/screens/reader/GuideRail.tsx]] — import-or-re-export: `readableTitle`; references `readableTitle`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `GOAL_NOT_UP_TODAY`, `KEEP_GOING_NOTHING_LEAD`, `PLAN_FINISHED`, `PLAN_STOPPED_WITH_MORE`, `TodayCause`, `WHATS_SENT`, `causeActionLabel`, `causeSendsPassages`, `causeSentence`, `causeWait`, `continueLessonLine`, `goalCauseSentence`, `todayCause`; references `GOAL_NOT_UP_TODAY`, `KEEP_GOING_NOTHING_LEAD`, `PLAN_FINISHED`, `PLAN_STOPPED_WITH_MORE`, `TodayCause`, `WHATS_SENT`, `causeActionLabel`, `causeSendsPassages`, `causeSentence`, `causeWait`, `continueLessonLine`, `goalCauseSentence`, `todayCause`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AiConnectionDto`, `PendingAddDto`, `ReadingQuestionsDto`, `SourceLibraryCard`, `SourceStatusLineDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/copy/denyList.test.tsx](../../../../../../apps/learnloop-tauri/src/copy/denyList.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/todayCause.test.ts](../../../../../../apps/learnloop-tauri/src/app/todayCause.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/todayCause.ts](../../../../../../apps/learnloop-tauri/src/app/todayCause.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.

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
| Source lines | 345 |
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

- `export const CONSENT_ACTION = "Give your OK"` — const, line 33
- `export const SIDECAR_CONSENT_LABEL = "Review"` — const, line 36
- `export function readableTitle(title: string): string` — function, line 40
- `export type TodayCause = /** Today's list still has questions: the plan stopped with something left. */ |` — type, line 56
- `export function partName(labels: readonly string[], sectionCount: number): string | null` — function, line 114
- `export function todayCause(input:` — function, line 127
- `export function causeWait(cause: TodayCause):` — function, line 225
- `export function causeSentence(cause: TodayCause): string` — function, line 246
- `export const GOAL_NOTHING_LEAD = "Nothing for this goal is ready to practise yet:"` — const, line 286
- `export const GOAL_NOT_UP_TODAY = "Nothing for this goal is up today. Its questions come back on the days they're due."` — const, line 287
- `export function goalCauseSentence(cause: TodayCause): string` — function, line 289
- `export const PLAN_FINISHED = "Nothing else is needed today."` — const, line 298
- `export const PLAN_STOPPED_WITH_MORE = "The plan stopped here, but there's more for today if you'd like it."` — const, line 301
- `export const KEEP_GOING_NOTHING_LEAD = "Nothing more to plan today."` — const, line 304
- `export function continueLessonLine(title: string): string` — function, line 307
- `export const LESSON_KEPT = "Your lesson is kept. It's on Today when you want it."` — const, line 312
- `export function causeActionLabel(cause: TodayCause): string | null` — function, line 315
- `export function causeSendsPassages(cause: TodayCause): boolean` — function, line 341
- `export const WHATS_SENT = "what's sent"` — const, line 345

## Internal implementation anchors

- `const trimmed = (title || "").trim()` — const, line 41
- `const name = decodeURIComponent(trimmed.split("/").pop() ?? trimmed).replace(/\.[A-Za-z0-9]` — const, line 43
- `const words = name.split(/[_\-.\s]+/).filter(Boolean)` — const, line 44
- `const lower = words.every((word)` — const, line 46
- `const FAILURE_RETRY_LABELS: ReadonlySet<string> = new Set(["Retry", "Try again"])` — const, line 54
- `function shownLine(card: SourceLibraryCard, ai: AiConnectionDto | null): SourceStatusLineDto | null` — function, line 84
- `function questionsOf(card: SourceLibraryCard): ReadingQuestionsDto | null` — function, line 90
- `type Rank = "waiting_ok" | "needs_ai" | "failed" | "section_failed" | "needs_look" | "on_the_way" | "section_writing"` — type, line 94
- `const ORDER: readonly Rank[] = ["waiting_ok", "needs_ai", "failed", "section_failed", "needs_look", "on_the_way", "section_writing"]` — const, line 95
- `function rankOf(line: SourceStatusLineDto | null, ai: AiConnectionDto | null): Rank | null` — function, line 97
- `const action = line.action` — const, line 99
- `const consent = ai ? ai.needs === "consent" || (ai.needs === null && action.label === SIDECAR_CONSENT_LABEL) : action.label === SIDECAR_CONSENT_LABEL` — const, line 102
- `const named = [...new Set(labels.map((label)` — const, line 115
- `const unknown = input.listUnknown === true` — const, line 135
- `const readable = input.cards.filter((card)` — const, line 137
- `const listed = input.listItemIds ?? []` — const, line 140
- `const questions = questionsOf(card)` — const, line 142
- `const own = new Set(questions?.itemIds ?? [])` — const, line 143
- `const mine = listed.filter((id)` — const, line 144
- `const found: Array<` — const, line 151
- `const rank = rankOf(shownLine(card, input.ai), input.ai)` — const, line 153
- `const questions = questionsOf(card)` — const, line 156
- `const rank = rankOf(entry.statusLine, input.ai)` — const, line 161
- `const hits = found.filter((entry)` — const, line 167
- `const first = hits[0]` — const, line 168
- `const line = first.card?.statusLine ?? null` — const, line 170
- `const questions = first.card ? questionsOf(first.card) : null` — const, line 171
- `const stopped = questions?.failed ?? []` — const, line 186
- `const questions = questionsOf(card)` — const, line 200
- `const withQuestions = readable.find((card)` — const, line 203
- `const questions = questionsOf(withQuestions) as ReadingQuestionsDto` — const, line 205
- `const unfinished = readable.find((card)` — const, line 210
- `function questionsWord(count: number): string` — function, line 216
- `function minutesWords(minutes: number): string` — function, line 220
- `const amount = cause.progress && cause.progress.total > 0 ? ` · $` — const, line 228
- `const usually = cause.minutes !== null ? ` · $` — const, line 229
- `const wait = causeWait(cause) as` — const, line 269
- `const sentence = causeSentence(cause)` — const, line 290
- `const joined = sentence.startsWith("LearnLoop") ? sentence : `$` — const, line 292

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `LESSON_KEPT`; references `LESSON_KEPT`
- [[Reference/Desktop/TypeScript/components/BookCard|src/components/BookCard.tsx]] — import-or-re-export: `CONSENT_ACTION`, `SIDECAR_CONSENT_LABEL`, `readableTitle`; references `CONSENT_ACTION`, `SIDECAR_CONSENT_LABEL`, `readableTitle`
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

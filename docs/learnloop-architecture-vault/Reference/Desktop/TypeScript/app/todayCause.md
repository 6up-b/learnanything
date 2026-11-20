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
| Source lines | 505 |
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

- `export const CONSENT_ACTION = "Give your OK"` — const, line 41
- `export const SIDECAR_CONSENT_LABEL = "Review"` — const, line 44
- `export function readableTitle(title: string): string` — function, line 48
- `export type TodayCause = /** Today's list still has questions: the plan stopped with something left. */ |` — type, line 66
- `export function partName(labels: readonly string[], sectionCount: number): string | null` — function, line 148
- `export function todayCause(input:` — function, line 197
- `export function causeWait(cause: TodayCause):` — function, line 339
- `export const TOPICS_NOT_WRITTEN = "Not every topic's questions could be written."` — const, line 373
- `export function readyWithWorkSentence(cause: Extract<TodayCause,` — function, line 376
- `export function causeTopicsFailed(cause: TodayCause): string | null` — function, line 387
- `export function causeSentence(cause: TodayCause): string` — function, line 392
- `export const GOAL_NOTHING_LEAD = "Nothing for this goal is ready to practise yet:"` — const, line 438
- `export const GOAL_NOT_UP_TODAY = "Nothing for this goal is up today. Its questions come back on the days they're due."` — const, line 439
- `export function goalCauseSentence(cause: TodayCause): string` — function, line 441
- `export const PLAN_FINISHED = "Nothing else is needed today."` — const, line 450
- `export const PLAN_STOPPED_WITH_MORE = "The plan stopped here, but there's more for today if you'd like it."` — const, line 453
- `export const KEEP_GOING_NOTHING_LEAD = "Nothing more to plan today."` — const, line 456
- `export function continueLessonLine(title: string): string` — function, line 459
- `export const LESSON_KEPT = "Your lesson is kept. It's on Today when you want it."` — const, line 464
- `export function causeActionLabel(cause: TodayCause): string | null` — function, line 467
- `export function causeSecondActionLabel(cause: TodayCause): string | null` — function, line 496
- `export function causeSendsPassages(cause: TodayCause): boolean` — function, line 501
- `export const WHATS_SENT = "what's sent"` — const, line 505

## Internal implementation anchors

- `const trimmed = (title || "").trim()` — const, line 49
- `const name = decodeURIComponent(trimmed.split("/").pop() ?? trimmed).replace(/\.[A-Za-z0-9]` — const, line 51
- `const words = name.split(/[_\-.\s]+/).filter(Boolean)` — const, line 52
- `const lower = words.every((word)` — const, line 54
- `const FAILURE_RETRY_LABELS: ReadonlySet<string> = new Set(["Retry", "Try again"])` — const, line 62
- `type Progress =` — type, line 64
- `function shownLine(card: SourceLibraryCard, ai: AiConnectionDto | null): SourceStatusLineDto | null` — function, line 116
- `function questionsOf(card: SourceLibraryCard): ReadingQuestionsDto | null` — function, line 122
- `type Rank = "waiting_ok" | "needs_ai" | "failed" | "no_topics" | "section_failed" | "needs_look" | "on_the_way" | "section_writing" | "section_waiting"` — type, line 126
- `const ORDER: readonly Rank[] = ["waiting_ok", "needs_ai", "failed", "no_topics", "section_failed", "needs_look", "on_the_way", "section_writing", "section_waiting"]` — const, line 127
- `function rankOf(line: SourceStatusLineDto | null, ai: AiConnectionDto | null): Rank | null` — function, line 129
- `const action = line.action` — const, line 131
- `const consent = ai ? ai.needs === "consent" || (ai.needs === null && action.label === SIDECAR_CONSENT_LABEL) : action.label === SIDECAR_CONSENT_LABEL` — const, line 134
- `const named = [...new Set(labels.map((label)` — const, line 149
- `function stillWriting(entry:` — function, line 157
- `function writingProgress(questions: ReadingQuestionsDto): Progress | null` — function, line 164
- `const progress = questions.progress` — const, line 165
- `const others = questions.sections.some((label)` — const, line 167
- `function readyWithSectionWork(card: SourceLibraryCard, questions: ReadingQuestionsDto, count: number, itemId: string | null): TodayCause | null` — function, line 174
- `const stopped = questions.failed.filter((entry)` — const, line 176
- `const unknown = input.listUnknown === true` — const, line 205
- `const readable = input.cards.filter((card)` — const, line 207
- `const listed = input.listItemIds ?? []` — const, line 210
- `const questions = questionsOf(card)` — const, line 212
- `const own = new Set(questions?.itemIds ?? [])` — const, line 213
- `const mine = listed.filter((id)` — const, line 214
- `const found: Array<` — const, line 223
- `const rank = rankOf(shownLine(card, input.ai), input.ai)` — const, line 225
- `const questions = questionsOf(card)` — const, line 228
- `const rank = rankOf(entry.statusLine, input.ai)` — const, line 234
- `const hits = found.filter((entry)` — const, line 240
- `const first = hits[0]` — const, line 241
- `const line = first.card?.statusLine ?? null` — const, line 243
- `const questions = first.card ? questionsOf(first.card) : null` — const, line 244
- `const written = unknown && questions && questions.count > 0 && first.card ? readyWithSectionWork(first.card, questions, questions.count, null) : null` — const, line 262
- `const stopped = questions?.failed ?? []` — const, line 264
- `const waiting = questions?.waiting?.length ?` — const, line 271
- `const copied = questions?.progress && line?.progress && questions.progress.done === line.progress.done && questions.progress.total === line.progress.total` — const, line 275
- `const firstBuild = Boolean(line?.progress) && !copied && (line?.minutes ?? null) === null` — const, line 277
- `const written = unknown && questions && questions.count > 0 && first.card ? readyWithSectionWork(first.card, questions, questions.count, null) : null` — const, line 282
- `const questions = questionsOf(card)` — const, line 299
- `const withQuestions = readable.find((card)` — const, line 302
- `const questions = questionsOf(withQuestions) as ReadingQuestionsDto` — const, line 304
- `const finishedNone = (card: SourceLibraryCard)` — const, line 310
- `const unfinished = readable.find((card)` — const, line 311
- `const finished = withQuestions ?? readable.find(finishedNone)` — const, line 313
- `function questionsWord(count: number): string` — function, line 318
- `function waitingWords(title: string, part: string | null): string` — function, line 323
- `function minutesWords(minutes: number): string` — function, line 329
- `function topicsDone(progress: Progress): string` — function, line 333
- `const amount = cause.progress && cause.progress.total > 0 ? ` · $` — const, line 342
- `const usually = cause.minutes !== null ? ` · $` — const, line 343
- `const amount = cause.progress && cause.progress.total > 0 ? ` · $` — const, line 353
- `function readySentence(cause:` — function, line 365
- `const progress = cause.writing.progress` — const, line 378
- `const more = `More are being written$` — const, line 379
- `const verb = cause.count === 1 ? "is" : "are"` — const, line 380
- `const failed = causeTopicsFailed(cause)` — const, line 399
- `const wait = causeWait(cause) as` — const, line 421
- `const sentence = causeSentence(cause)` — const, line 442
- `const joined = sentence.startsWith("LearnLoop") ? sentence : `$` — const, line 444

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `LESSON_KEPT`; references `LESSON_KEPT`
- [[Reference/Desktop/TypeScript/components/BookCard|src/components/BookCard.tsx]] — import-or-re-export: `CONSENT_ACTION`, `SIDECAR_CONSENT_LABEL`, `readableTitle`; references `CONSENT_ACTION`, `SIDECAR_CONSENT_LABEL`, `readableTitle`
- [[Reference/Desktop/TypeScript/screens/reader/GuideRail|src/screens/reader/GuideRail.tsx]] — import-or-re-export: `readableTitle`; references `readableTitle`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `GOAL_NOT_UP_TODAY`, `KEEP_GOING_NOTHING_LEAD`, `PLAN_FINISHED`, `PLAN_STOPPED_WITH_MORE`, `TodayCause`, `WHATS_SENT`, `causeActionLabel`, `causeSecondActionLabel`, `causeSendsPassages`, `causeSentence`, `causeTopicsFailed`, `causeWait`, `continueLessonLine`, `goalCauseSentence`, `readyWithWorkSentence`, `todayCause`; references `GOAL_NOT_UP_TODAY`, `KEEP_GOING_NOTHING_LEAD`, `PLAN_FINISHED`, `PLAN_STOPPED_WITH_MORE`, `TodayCause`, `WHATS_SENT`, `causeActionLabel`, `causeSecondActionLabel`, `causeSendsPassages`, `causeSentence`, `causeTopicsFailed`, `causeWait`, `continueLessonLine`, `goalCauseSentence`, `readyWithWorkSentence`, `todayCause`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AiConnectionDto`, `PendingAddDto`, `ReadingQuestionsDto`, `SourceLibraryCard`, `SourceStatusLineDto`
- [[Reference/Desktop/TypeScript/copy/waiting|src/copy/waiting.ts]] — import-or-re-export; imports `WAITING_COPY`

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

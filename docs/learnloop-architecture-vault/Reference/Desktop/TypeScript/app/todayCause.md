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
| Source lines | 596 |
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
- `export function waitingOnList(rows: readonly Pick<ScheduledItemDto, "practiceItemId" | "dueAt" | "dueStatus">[], now: number = Date.now()): string[]` — function, line 145
- `export function partName(labels: readonly string[], sectionCount: number): string | null` — function, line 173
- `export function todayCause(input:` — function, line 232
- `export function askableReadingQuestion( cards: readonly SourceLibraryCard[] | null | undefined, queue: QueueSnapshot | null | undefined, answered: string | null = null, now: number = Date.now() ): ScheduledItemDto | null` — function, line 384
- `export const ONE_BOOK_AT_A_TIME = "LearnLoop gets one book ready at a time."` — const, line 415
- `export function causeWait(cause: TodayCause):` — function, line 423
- `export const TOPICS_NOT_WRITTEN = "Not every topic's questions could be written."` — const, line 461
- `export function readyWithWorkSentence(cause: Extract<TodayCause,` — function, line 464
- `export function causeTopicsFailed(cause: TodayCause): string | null` — function, line 476
- `export function causeSentence(cause: TodayCause): string` — function, line 481
- `export const GOAL_NOTHING_LEAD = "Nothing for this goal is ready to practise yet:"` — const, line 529
- `export const GOAL_NOT_UP_TODAY = "Nothing for this goal is up today. Its questions come back on the days they're due."` — const, line 530
- `export function goalCauseSentence(cause: TodayCause): string` — function, line 532
- `export const PLAN_FINISHED = "Nothing else is needed today."` — const, line 541
- `export const PLAN_STOPPED_WITH_MORE = "The plan stopped here, but there's more for today if you'd like it."` — const, line 544
- `export const KEEP_GOING_NOTHING_LEAD = "Nothing more to plan today."` — const, line 547
- `export function continueLessonLine(title: string): string` — function, line 550
- `export const LESSON_KEPT = "Your lesson is kept. It's on Today when you want it."` — const, line 555
- `export function causeActionLabel(cause: TodayCause): string | null` — function, line 558
- `export function causeSecondActionLabel(cause: TodayCause): string | null` — function, line 587
- `export function causeSendsPassages(cause: TodayCause): boolean` — function, line 592
- `export const WHATS_SENT = "what's sent"` — const, line 596

## Internal implementation anchors

- `const trimmed = (title || "").trim()` — const, line 49
- `const name = decodeURIComponent(trimmed.split("/").pop() ?? trimmed).replace(/\.[A-Za-z0-9]` — const, line 51
- `const words = name.split(/[_\-.\s]+/).filter(Boolean)` — const, line 52
- `const lower = words.every((word)` — const, line 54
- `const FAILURE_RETRY_LABELS: ReadonlySet<string> = new Set(["Retry", "Try again"])` — const, line 62
- `type Progress =` — type, line 64
- `function shownLine(card: SourceLibraryCard, ai: AiConnectionDto | null): SourceStatusLineDto | null` — function, line 121
- `function questionsOf(card: SourceLibraryCard): ReadingQuestionsDto | null` — function, line 127
- `function laterOf(questions: ReadingQuestionsDto): ReadonlySet<string>` — function, line 133
- `function askableWritten(questions: ReadingQuestionsDto): number` — function, line 138
- `type Rank = "waiting_ok" | "needs_ai" | "failed" | "no_topics" | "section_failed" | "needs_look" | "on_the_way" | "section_writing" | "section_waiting"` — type, line 151
- `const ORDER: readonly Rank[] = ["waiting_ok", "needs_ai", "failed", "no_topics", "section_failed", "needs_look", "on_the_way", "section_writing", "section_waiting"]` — const, line 152
- `function rankOf(line: SourceStatusLineDto | null, ai: AiConnectionDto | null): Rank | null` — function, line 154
- `const action = line.action` — const, line 156
- `const consent = ai ? ai.needs === "consent" || (ai.needs === null && action.label === SIDECAR_CONSENT_LABEL) : action.label === SIDECAR_CONSENT_LABEL` — const, line 159
- `const named = [...new Set(labels.map((label)` — const, line 174
- `function stillWriting(entry:` — function, line 182
- `function stoppedEntries(questions: ReadingQuestionsDto): ReadingQuestionsDto["failed"]` — function, line 187
- `function writingProgress(questions: ReadingQuestionsDto): Progress | null` — function, line 194
- `const progress = questions.progress` — const, line 195
- `const others = questions.sections.some((label)` — const, line 197
- `function readyWithSectionWork(card: SourceLibraryCard, questions: ReadingQuestionsDto, count: number, itemId: string | null): TodayCause | null` — function, line 204
- `const stopped = stoppedEntries(questions)` — const, line 206
- `const unknown = input.listUnknown === true` — const, line 241
- `const readable = input.cards.filter((card)` — const, line 243
- `const listed = input.listItemIds ?? []` — const, line 246
- `const waiting = new Set(input.listWaiting ?? [])` — const, line 247
- `const notNow = new Set<string>()` — const, line 249
- `const questions = questionsOf(card)` — const, line 251
- `const own = new Set(questions.itemIds)` — const, line 253
- `const later = laterOf(questions)` — const, line 254
- `const mine = listed.filter((id)` — const, line 256
- `const found: Array<` — const, line 267
- `const rank = rankOf(shownLine(card, input.ai), input.ai)` — const, line 269
- `const questions = questionsOf(card)` — const, line 273
- `const rank = rankOf(entry.statusLine, input.ai)` — const, line 279
- `const hits = found.filter((entry)` — const, line 285
- `const first = hits[0]` — const, line 286
- `const line = first.card?.statusLine ?? null` — const, line 288
- `const questions = first.card ? questionsOf(first.card) : null` — const, line 289
- `const written = unknown && questions && askableWritten(questions) > 0 && first.card ? readyWithSectionWork(first.card, questions, askableWritten(questions), null) : null` — const, line 307
- `const stopped = questions ? stoppedEntries(questions) : []` — const, line 311
- `const waiting = questions?.waiting?.length ?` — const, line 318
- `const copied = questions?.progress && line?.progress && questions.progress.done === line.progress.done && questions.progress.total === line.progress.total` — const, line 322
- `const firstBuild = Boolean(line?.progress) && !copied && (line?.minutes ?? null) === null` — const, line 324
- `const behind = (first.line ?? line)?.waitingBehind ?? null` — const, line 326
- `const queued = hits.slice(1).filter((hit)` — const, line 327
- `const written = unknown && questions && askableWritten(questions) > 0 && first.card ? readyWithSectionWork(first.card, questions, askableWritten(questions), null) : null` — const, line 333
- `const questions = questionsOf(card)` — const, line 353
- `const withQuestions = readable.find((card)` — const, line 356
- `const askable = unknown ? readable.find((card)` — const, line 357
- `const questions = questionsOf(card)` — const, line 359
- `const questions = questionsOf(askable) as ReadingQuestionsDto` — const, line 364
- `const finishedNone = (card: SourceLibraryCard)` — const, line 370
- `const unfinished = readable.find((card)` — const, line 371
- `const finished = withQuestions ?? readable.find(finishedNone)` — const, line 373
- `const rows = queue.sections.flatMap((section)` — const, line 391
- `const cause = todayCause(` — const, line 392
- `function questionsWord(count: number): string` — function, line 399
- `function waitingWords(title: string, part: string | null): string` — function, line 404
- `function minutesWords(minutes: number): string` — function, line 410
- `function topicsDone(progress: Progress): string` — function, line 417
- `const amount = cause.progress && cause.progress.total > 0 ? ` · $` — const, line 429
- `const usually = cause.minutes !== null ? ` · $` — const, line 430
- `const queued = cause.queued?.length ? `$` — const, line 431
- `const amount = cause.progress && cause.progress.total > 0 ? ` · $` — const, line 441
- `function readySentence(cause:` — function, line 453
- `const progress = cause.writing.progress` — const, line 466
- `const more = `More are being written$` — const, line 467
- `const verb = cause.count === 1 ? "is" : "are"` — const, line 468
- `const failed = causeTopicsFailed(cause)` — const, line 488
- `const wait = causeWait(cause) as` — const, line 510
- `const failed = causeTopicsFailed(cause)` — const, line 511
- `const after = failed ? `$` — const, line 512
- `const sentence = causeSentence(cause)` — const, line 533
- `const joined = sentence.startsWith("LearnLoop") ? sentence : `$` — const, line 535

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `LESSON_KEPT`; references `LESSON_KEPT`
- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export: `askableReadingQuestion`; references `askableReadingQuestion`
- [[Reference/Desktop/TypeScript/components/BookCard|src/components/BookCard.tsx]] — import-or-re-export: `CONSENT_ACTION`, `SIDECAR_CONSENT_LABEL`, `readableTitle`; references `CONSENT_ACTION`, `SIDECAR_CONSENT_LABEL`, `readableTitle`
- [[Reference/Desktop/TypeScript/screens/reader/GuideRail|src/screens/reader/GuideRail.tsx]] — import-or-re-export: `readableTitle`; references `readableTitle`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `GOAL_NOT_UP_TODAY`, `KEEP_GOING_NOTHING_LEAD`, `PLAN_FINISHED`, `PLAN_STOPPED_WITH_MORE`, `TodayCause`, `WHATS_SENT`, `causeActionLabel`, `causeSecondActionLabel`, `causeSendsPassages`, `causeSentence`, `causeTopicsFailed`, `causeWait`, `continueLessonLine`, `goalCauseSentence`, `readyWithWorkSentence`, `todayCause`, `waitingOnList`; references `GOAL_NOT_UP_TODAY`, `KEEP_GOING_NOTHING_LEAD`, `PLAN_FINISHED`, `PLAN_STOPPED_WITH_MORE`, `TodayCause`, `WHATS_SENT`, `causeActionLabel`, `causeSecondActionLabel`, `causeSendsPassages`, `causeSentence`, `causeTopicsFailed`, `causeWait`, `continueLessonLine`, `goalCauseSentence`, `readyWithWorkSentence`, `todayCause`, `waitingOnList`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AiConnectionDto`, `PendingAddDto`, `QueueSnapshot`, `ReadingQuestionsDto`, `ScheduledItemDto`, `SourceLibraryCard`, `SourceStatusLineDto`
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

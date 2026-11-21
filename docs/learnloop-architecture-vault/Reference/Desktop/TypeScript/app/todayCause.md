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
| Source lines | 663 |
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

- `export const CONSENT_ACTION = "Give your OK"` — const, line 43
- `export const SIDECAR_CONSENT_LABEL = "Review"` — const, line 46
- `export function readableTitle(title: string): string` — function, line 50
- `export type TodayCause = /** Today's list still has questions: the plan stopped with something left. */ |` — type, line 68
- `export function waitingOnList(rows: readonly Pick<ScheduledItemDto, "practiceItemId" | "dueAt" | "dueStatus">[], now: number = Date.now()): string[]` — function, line 160
- `export function partName(labels: readonly string[], sectionCount: number): string | null` — function, line 188
- `export function todayCause(input:` — function, line 255
- `export function askableReadingQuestion( cards: readonly SourceLibraryCard[] | null | undefined, queue: QueueSnapshot | null | undefined, answered: string | null = null, now: number = Date.now() ): ScheduledItemDto | null` — function, line 425
- `export const ONE_BOOK_AT_A_TIME = "LearnLoop gets one book ready at a time."` — const, line 457
- `export function causeWait(cause: TodayCause):` — function, line 465
- `export const READING_SAVED = "Your reading is saved. Questions will be written when the desktop is running."` — const, line 517
- `export const TOPICS_NOT_WRITTEN = "Not every topic's questions could be written."` — const, line 521
- `export function readyWithWorkSentence(cause: Extract<TodayCause,` — function, line 524
- `export function causeTopicsFailed(cause: TodayCause): string | null` — function, line 537
- `export function causeSentence(cause: TodayCause): string` — function, line 542
- `export const GOAL_NOTHING_LEAD = "Nothing for this goal is ready to practise yet:"` — const, line 594
- `export const GOAL_NOT_UP_TODAY = "Nothing for this goal is up today. Its questions come back on the days they're due."` — const, line 595
- `export function goalCauseSentence(cause: TodayCause): string` — function, line 597
- `export const PLAN_FINISHED = "Nothing else is needed today."` — const, line 606
- `export const PLAN_STOPPED_WITH_MORE = "The plan stopped here, but there's more for today if you'd like it."` — const, line 609
- `export const KEEP_GOING_NOTHING_LEAD = "Nothing more to plan today."` — const, line 612
- `export function continueLessonLine(title: string): string` — function, line 615
- `export const LESSON_KEPT = "Your lesson is kept. It's on Today when you want it."` — const, line 620
- `export function causeActionLabel(cause: TodayCause): string | null` — function, line 623
- `export function causeSecondActionLabel(cause: TodayCause): string | null` — function, line 654
- `export function causeSendsPassages(cause: TodayCause): boolean` — function, line 659
- `export const WHATS_SENT = "what's sent"` — const, line 663

## Internal implementation anchors

- `const trimmed = (title || "").trim()` — const, line 51
- `const name = decodeURIComponent(trimmed.split("/").pop() ?? trimmed).replace(/\.[A-Za-z0-9]` — const, line 53
- `const words = name.split(/[_\-.\s]+/).filter(Boolean)` — const, line 54
- `const lower = words.every((word)` — const, line 56
- `const FAILURE_RETRY_LABELS: ReadonlySet<string> = new Set(["Retry", "Try again"])` — const, line 64
- `type Progress =` — type, line 66
- `function shownLine(card: SourceLibraryCard, ai: AiConnectionDto | null): SourceStatusLineDto | null` — function, line 136
- `function questionsOf(card: SourceLibraryCard): ReadingQuestionsDto | null` — function, line 142
- `function laterOf(questions: ReadingQuestionsDto): ReadonlySet<string>` — function, line 148
- `function askableWritten(questions: ReadingQuestionsDto): number` — function, line 153
- `type Rank = "waiting_ok" | "needs_ai" | "failed" | "no_topics" | "section_failed" | "needs_look" | "on_the_way" | "section_writing" | "section_waiting" | "reading_saved"` — type, line 166
- `const ORDER: readonly Rank[] = ["waiting_ok", "needs_ai", "failed", "no_topics", "section_failed", "needs_look", "on_the_way", "section_writing", "section_waiting", "reading_saved"]` — const, line 167
- `function rankOf(line: SourceStatusLineDto | null, ai: AiConnectionDto | null): Rank | null` — function, line 169
- `const action = line.action` — const, line 171
- `const consent = ai ? ai.needs === "consent" || (ai.needs === null && action.label === SIDECAR_CONSENT_LABEL) : action.label === SIDECAR_CONSENT_LABEL` — const, line 174
- `const named = [...new Set(labels.map((label)` — const, line 189
- `function fromReading(questions: ReadingQuestionsDto, labels: readonly string[]): boolean` — function, line 196
- `const partial = new Set([...(questions.partRead ?? []), ...(questions.owed ?? [])])` — const, line 197
- `function stillWriting(entry:` — function, line 204
- `function stoppedEntries(questions: ReadingQuestionsDto): ReadingQuestionsDto["failed"]` — function, line 209
- `function writingProgress(questions: ReadingQuestionsDto): Progress | null` — function, line 216
- `const progress = questions.progress` — const, line 217
- `const others = questions.sections.some((label)` — const, line 219
- `function readyWithSectionWork(card: SourceLibraryCard, questions: ReadingQuestionsDto, count: number, itemId: string | null): TodayCause | null` — function, line 226
- `const stopped = stoppedEntries(questions)` — const, line 228
- `const unknown = input.listUnknown === true` — const, line 264
- `const readable = input.cards.filter((card)` — const, line 266
- `const listed = input.listItemIds ?? []` — const, line 269
- `const waiting = new Set(input.listWaiting ?? [])` — const, line 270
- `const notNow = new Set<string>()` — const, line 272
- `const questions = questionsOf(card)` — const, line 274
- `const own = new Set(questions.itemIds)` — const, line 276
- `const later = laterOf(questions)` — const, line 277
- `const mine = listed.filter((id)` — const, line 279
- `const found: Array<` — const, line 291
- `const rank = rankOf(shownLine(card, input.ai), input.ai)` — const, line 293
- `const questions = questionsOf(card)` — const, line 297
- `const rank = rankOf(entry.statusLine, input.ai)` — const, line 306
- `const hits = found.filter((entry)` — const, line 312
- `const first = hits[0]` — const, line 313
- `const line = first.card?.statusLine ?? null` — const, line 315
- `const questions = first.card ? questionsOf(first.card) : null` — const, line 316
- `const written = unknown && questions && askableWritten(questions) > 0 && first.card ? readyWithSectionWork(first.card, questions, askableWritten(questions), null) : null` — const, line 334
- `const stopped = questions ? stoppedEntries(questions) : []` — const, line 338
- `const waiting = questions?.waiting?.length ?` — const, line 345
- `const copied = questions?.progress && line?.progress && questions.progress.done === line.progress.done && questions.progress.total === line.progress.total` — const, line 351
- `const firstBuild = Boolean(line?.progress) && !copied && (line?.minutes ?? null) === null` — const, line 353
- `const behind = (first.line ?? line)?.waitingBehind ?? null` — const, line 355
- `const queued = hits.slice(1).filter((hit)` — const, line 356
- `const written = unknown && questions && askableWritten(questions) > 0 && first.card ? readyWithSectionWork(first.card, questions, askableWritten(questions), null) : null` — const, line 362
- `const labels = questions?.writing.length ? questions.writing : questions?.owed ?? []` — const, line 366
- `const finished = questions?.waiting ?? []` — const, line 378
- `const labels = finished.length ? finished : questions?.beforeBuild ?? []` — const, line 379
- `const questions = questionsOf(card)` — const, line 390
- `const withQuestions = readable.find((card)` — const, line 393
- `const askable = unknown ? readable.find((card)` — const, line 394
- `const questions = questionsOf(card)` — const, line 396
- `const questions = questionsOf(askable) as ReadingQuestionsDto` — const, line 401
- `const finishedNone = (card: SourceLibraryCard)` — const, line 408
- `const readSome = readable.find((card)` — const, line 410
- `const unfinished = readable.find((card)` — const, line 412
- `const finished = withQuestions ?? readable.find(finishedNone)` — const, line 414
- `const rows = queue.sections.flatMap((section)` — const, line 432
- `const cause = todayCause(` — const, line 433
- `function questionsWord(count: number): string` — function, line 440
- `function waitingWords(title: string, part: string | null, fromReading = false): string` — function, line 445
- `function minutesWords(minutes: number): string` — function, line 452
- `function topicsDone(progress: Progress): string` — function, line 459
- `const amount = cause.progress && cause.progress.total > 0 ? ` · $` — const, line 471
- `const usually = cause.minutes !== null ? ` · $` — const, line 472
- `const queued = cause.queued?.length ? `$` — const, line 473
- `const amount = cause.progress && cause.progress.total > 0 ? ` · $` — const, line 483
- `function fromWhatYouRead(cause:` — function, line 503
- `function readySentence(cause:` — function, line 507
- `const progress = cause.writing.progress` — const, line 526
- `const more = `More are being written$` — const, line 527
- `const verb = cause.count === 1 ? "is" : "are"` — const, line 528
- `const failed = causeTopicsFailed(cause)` — const, line 549
- `const wait = causeWait(cause) as` — const, line 575
- `const failed = causeTopicsFailed(cause)` — const, line 576
- `const after = failed ? `$` — const, line 577
- `const sentence = causeSentence(cause)` — const, line 598
- `const joined = sentence.startsWith("LearnLoop") ? sentence : `$` — const, line 600

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

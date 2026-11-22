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

Provides `QUESTIONS_FROM_READING`, `MORE_AS_YOU_READ`, `NO_QUESTIONS_YET`, `CONSENT_ACTION` and related exports within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/todayCause.ts](../../../../../../apps/learnloop-tauri/src/app/todayCause.ts) |
| Source lines | 834 |
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

- `export const QUESTIONS_FROM_READING = "Questions are written from the parts you read."` — const, line 45
- `export const MORE_AS_YOU_READ = "More come as you read on."` — const, line 47
- `export const NO_QUESTIONS_YET = "No questions ready yet."` — const, line 51
- `export const CONSENT_ACTION = "Give your OK"` — const, line 56
- `export const SIDECAR_CONSENT_LABEL = "Review"` — const, line 59
- `export function readableTitle(title: string): string` — function, line 63
- `export type TodayCause = /** Today's list still has questions: the plan stopped with something left. */ |` — type, line 84
- `export function waitingOnList(rows: readonly Pick<ScheduledItemDto, "practiceItemId" | "dueAt" | "dueStatus">[], now: number = Date.now()): string[]` — function, line 191
- `export function partName(labels: readonly string[], sectionCount: number): string | null` — function, line 219
- `export function readingItemIds(cards: readonly SourceLibraryCard[] | null | undefined): string[]` — function, line 284
- `export function todayCause(input:` — function, line 321
- `export function askableReadingQuestion( cards: readonly SourceLibraryCard[] | null | undefined, queue: QueueSnapshot | null | undefined, answered: string | null = null, now: number = Date.now() ): ScheduledItemDto | null` — function, line 505
- `export function causeUnderway(cause: TodayCause | null | undefined): boolean` — function, line 526
- `export function heldLine(cards: readonly SourceLibraryCard[] | null | undefined): string | null` — function, line 533
- `export function notAskableOnList(cards: readonly SourceLibraryCard[] | null | undefined, listItemIds: readonly string[], listWaiting: readonly string[]): string[]` — function, line 543
- `export const ONE_BOOK_AT_A_TIME = "LearnLoop gets one book ready at a time."` — const, line 575
- `export function topicCountWords(topics: TopicCount): string` — function, line 587
- `export function allReadWords(title: string): string` — function, line 594
- `export const ON_TODAY = "They'll be on Today."` — const, line 599
- `export const NOTHING_TO_DO = "You don’t need to do anything for them."` — const, line 602
- `export const KEEP_OPEN = "Leave LearnLoop open meanwhile: closing it stops the work until you try again."` — const, line 607
- `export const KEEP_OPEN_ON_DESKTOP = "Leave LearnLoop open on your desktop meanwhile: closing it there stops the work until you try again."` — const, line 609
- `export const OPEN_THE_BOOK = "Open the book"` — const, line 612
- `export function causeWait(cause: TodayCause):` — function, line 623
- `export const READING_SAVED = "Your reading is saved. Questions will be written when the desktop is running."` — const, line 682
- `export const TOPICS_NOT_WRITTEN = "Not every topic's questions could be written."` — const, line 686
- `export function readyWithWorkSentence(cause: Extract<TodayCause,` — function, line 689
- `export function causeTopicsFailed(cause: TodayCause): string | null` — function, line 704
- `export function causeSentence(cause: TodayCause): string` — function, line 709
- `export const GOAL_NOTHING_LEAD = "Nothing for this goal is ready to practise yet:"` — const, line 763
- `export const GOAL_NOT_UP_TODAY = "Nothing for this goal is up today. Its questions come back on the days they're due."` — const, line 764
- `export function goalCauseSentence(cause: TodayCause): string` — function, line 766
- `export const PLAN_FINISHED = "Nothing else is needed today."` — const, line 775
- `export const PLAN_STOPPED_WITH_MORE = "The plan stopped here, but there's more for today if you'd like it."` — const, line 778
- `export const KEEP_GOING_NOTHING_LEAD = "Nothing more to plan today."` — const, line 781
- `export function continueLessonLine(title: string): string` — function, line 784
- `export const LESSON_KEPT = "Your lesson is kept. It's on Today when you want it."` — const, line 789
- `export function causeActionLabel(cause: TodayCause): string | null` — function, line 792
- `export function causeSecondActionLabel(cause: TodayCause): string | null` — function, line 825
- `export function causeSendsPassages(cause: TodayCause): boolean` — function, line 830
- `export const WHATS_SENT = "what's sent"` — const, line 834

## Internal implementation anchors

- `const trimmed = (title || "").trim()` — const, line 64
- `const name = decodeURIComponent(trimmed.split("/").pop() ?? trimmed).replace(/\.[A-Za-z0-9]` — const, line 66
- `const words = name.split(/[_\-.\s]+/).filter(Boolean)` — const, line 67
- `const lower = words.every((word)` — const, line 69
- `const FAILURE_RETRY_LABELS: ReadonlySet<string> = new Set(["Retry", "Try again"])` — const, line 77
- `type Progress =` — type, line 79
- `type TopicCount =` — type, line 82
- `type AllRead =` — type, line 165
- `function shownLine(card: SourceLibraryCard, ai: AiConnectionDto | null): SourceStatusLineDto | null` — function, line 167
- `function questionsOf(card: SourceLibraryCard): ReadingQuestionsDto | null` — function, line 173
- `function laterOf(questions: ReadingQuestionsDto): ReadonlySet<string>` — function, line 179
- `function askableWritten(questions: ReadingQuestionsDto): number` — function, line 184
- `type Rank = "waiting_ok" | "needs_ai" | "failed" | "no_topics" | "section_failed" | "needs_look" | "on_the_way" | "section_writing" | "section_waiting" | "reading_saved"` — type, line 197
- `const ORDER: readonly Rank[] = ["waiting_ok", "needs_ai", "failed", "no_topics", "section_failed", "needs_look", "on_the_way", "section_writing", "section_waiting", "reading_saved"]` — const, line 198
- `function rankOf(line: SourceStatusLineDto | null, ai: AiConnectionDto | null): Rank | null` — function, line 200
- `const action = line.action` — const, line 202
- `const consent = ai ? ai.needs === "consent" || (ai.needs === null && action.label === SIDECAR_CONSENT_LABEL) : action.label === SIDECAR_CONSENT_LABEL` — const, line 205
- `const named = [...new Set(labels.map((label)` — const, line 220
- `function fromReading(questions: ReadingQuestionsDto, labels: readonly string[]): boolean` — function, line 227
- `const partial = new Set([...(questions.partRead ?? []), ...(questions.owed ?? [])])` — const, line 228
- `function stillWriting(entry:` — function, line 235
- `function stoppedEntries(questions: ReadingQuestionsDto): ReadingQuestionsDto["failed"]` — function, line 240
- `function writingProgress(questions: ReadingQuestionsDto): Progress | null` — function, line 247
- `const progress = questions.progress` — const, line 248
- `const others = questions.sections.some((label)` — const, line 250
- `function bookTopics(questions: ReadingQuestionsDto, part: string | null): TopicCount | null` — function, line 259
- `const topics = questions.topics` — const, line 260
- `const own = [...questions.sections, ...questions.writing].every((label)` — const, line 263
- `function placedDetail(detail: WritingDetailDto, topics: TopicCount | null): WritingDetailDto` — function, line 271
- `const topic = detail.topic` — const, line 272
- `function allReadOf(questions: ReadingQuestionsDto | null, phone: boolean): AllRead` — function, line 277
- `function readyWithSectionWork(card: SourceLibraryCard, questions: ReadingQuestionsDto, count: number, itemId: string | null): TodayCause | null` — function, line 290
- `const stopped = stoppedEntries(questions)` — const, line 292
- `const part = partName(questions.sections, questions.sectionCount)` — const, line 293
- `const topics = bookTopics(questions, part)` — const, line 294
- `const unknown = input.listUnknown === true` — const, line 330
- `const readable = input.cards.filter((card)` — const, line 332
- `const listed = input.listItemIds ?? []` — const, line 335
- `const waiting = new Set(input.listWaiting ?? [])` — const, line 336
- `const notNow = new Set<string>()` — const, line 338
- `const questions = questionsOf(card)` — const, line 340
- `const own = new Set(questions.itemIds)` — const, line 342
- `const later = laterOf(questions)` — const, line 343
- `const mine = listed.filter((id)` — const, line 345
- `const found: Array<` — const, line 357
- `const rank = rankOf(shownLine(card, input.ai), input.ai)` — const, line 359
- `const questions = questionsOf(card)` — const, line 363
- `const rank = rankOf(entry.statusLine, input.ai)` — const, line 372
- `const hits = found.filter((entry)` — const, line 378
- `const first = hits[0]` — const, line 379
- `const line = first.card?.statusLine ?? null` — const, line 381
- `const questions = first.card ? questionsOf(first.card) : null` — const, line 382
- `const written = unknown && questions && askableWritten(questions) > 0 && first.card ? readyWithSectionWork(first.card, questions, askableWritten(questions), null) : null` — const, line 400
- `const stopped = questions ? stoppedEntries(questions) : []` — const, line 404
- `const waiting = questions?.waiting?.length ?` — const, line 411
- `const copied = questions?.progress && line?.progress && questions.progress.done === line.progress.done && questions.progress.total === line.progress.total` — const, line 417
- `const firstBuild = Boolean(line?.progress) && !copied && (line?.minutes ?? null) === null` — const, line 419
- `const behind = (first.line ?? line)?.waitingBehind ?? null` — const, line 421
- `const queued = hits.slice(1).filter((hit)` — const, line 422
- `const written = unknown && questions && askableWritten(questions) > 0 && first.card ? readyWithSectionWork(first.card, questions, askableWritten(questions), null) : null` — const, line 429
- `const labels = questions?.writing.length ? questions.writing : questions?.owed ?? []` — const, line 433
- `const part = partName(labels, questions?.sectionCount ?? 0)` — const, line 434
- `const topics = questions ? bookTopics(questions, part) : null` — const, line 435
- `const finished = questions?.waiting ?? []` — const, line 450
- `const labels = finished.length ? finished : questions?.beforeBuild ?? []` — const, line 451
- `const questions = questionsOf(card)` — const, line 463
- `const withQuestions = readable.find((card)` — const, line 468
- `const askable = unknown ? readable.find((card)` — const, line 469
- `const questions = questionsOf(card)` — const, line 471
- `const questions = questionsOf(askable) as ReadingQuestionsDto` — const, line 476
- `const finishedNone = (card: SourceLibraryCard)` — const, line 483
- `const readSome = readable.find((card)` — const, line 485
- `const questions = questionsOf(readSome) as ReadingQuestionsDto` — const, line 487
- `const to = questions.readTo ?? null` — const, line 488
- `const unfinished = readable.find((card)` — const, line 492
- `const finished = withQuestions ?? readable.find(finishedNone)` — const, line 494
- `const rows = queue.sections.flatMap((section)` — const, line 512
- `const cause = todayCause(` — const, line 513
- `function questionsWord(count: number): string` — function, line 520
- `const readable = (cards ?? []).filter((card)` — const, line 534
- `const held = readable.reduce((sum, card)` — const, line 535
- `const more = readable.some((card)` — const, line 537
- `const later = new Set((cards ?? []).flatMap((card)` — const, line 545
- `const waiting = new Set(listWaiting)` — const, line 546
- `function readToSentence(cause: Extract<TodayCause,` — function, line 551
- `const place = cause.place` — const, line 552
- `const book = `“$` — const, line 553
- `function waitingWords(title: string, part: string | null, fromReading = false): string` — function, line 563
- `function minutesWords(minutes: number): string` — function, line 570
- `function topicsDone(progress: Progress): string` — function, line 577
- `function topicsWord(n: number): string` — function, line 581
- `function allReadBlock(cause:` — function, line 616
- `const amount = cause.progress && cause.progress.total > 0 ? ` · $` — const, line 630
- `const usually = cause.minutes !== null ? ` · $` — const, line 631
- `const queued = cause.queued?.length ? `$` — const, line 632
- `const promise = cause.waiting ? waitingWords(cause.title, cause.waiting.part, cause.waiting.fromReading === true) : null` — const, line 633
- `const amount = cause.topics ? ` · $` — const, line 646
- `const after = cause.allRead ? allReadBlock(cause,` — const, line 648
- `function fromWhatYouRead(cause:` — function, line 668
- `function readySentence(cause:` — function, line 672
- `const progress = cause.writing.progress` — const, line 691
- `const more = cause.writing.topics ? `$` — const, line 692
- `const verb = cause.count === 1 ? "is" : "are"` — const, line 695
- `const failed = causeTopicsFailed(cause)` — const, line 716
- `const wait = causeWait(cause) as` — const, line 744
- `const failed = causeTopicsFailed(cause)` — const, line 745
- `const after = failed ? `$` — const, line 746
- `const sentence = causeSentence(cause)` — const, line 767
- `const joined = sentence.startsWith("LearnLoop") ? sentence : `$` — const, line 769

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `LESSON_KEPT`; references `LESSON_KEPT`
- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export: `askableReadingQuestion`; references `askableReadingQuestion`
- [[Reference/Desktop/TypeScript/app/waitDetail|src/app/waitDetail.ts]] — import-or-re-export: `TodayCause`; references `TodayCause`
- [[Reference/Desktop/TypeScript/components/BookCard|src/components/BookCard.tsx]] — import-or-re-export: `CONSENT_ACTION`, `QUESTIONS_FROM_READING`, `SIDECAR_CONSENT_LABEL`, `readableTitle`; references `CONSENT_ACTION`, `QUESTIONS_FROM_READING`, `SIDECAR_CONSENT_LABEL`, `readableTitle`
- [[Reference/Desktop/TypeScript/components/SessionFinishHud|src/components/SessionFinishHud.tsx]] — import-or-re-export: `readingItemIds`; references `readingItemIds`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `readingItemIds`; references `readingItemIds`
- [[Reference/Desktop/TypeScript/screens/reader/GuideRail|src/screens/reader/GuideRail.tsx]] — import-or-re-export: `ON_TODAY`, `QUESTIONS_FROM_READING`, `readableTitle`; references `ON_TODAY`, `QUESTIONS_FROM_READING`, `readableTitle`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `GOAL_NOT_UP_TODAY`, `KEEP_GOING_NOTHING_LEAD`, `NO_QUESTIONS_YET`, `PLAN_FINISHED`, `PLAN_STOPPED_WITH_MORE`, `TodayCause`, `WHATS_SENT`, `causeActionLabel`, `causeSecondActionLabel`, `causeSendsPassages`, `causeSentence`, `causeTopicsFailed`, `causeUnderway`, `causeWait`, `continueLessonLine`, `goalCauseSentence`, `heldLine`, `notAskableOnList`, `readingItemIds`, `readyWithWorkSentence`, `todayCause`, `waitingOnList`; references `GOAL_NOT_UP_TODAY`, `KEEP_GOING_NOTHING_LEAD`, `NO_QUESTIONS_YET`, `PLAN_FINISHED`, `PLAN_STOPPED_WITH_MORE`, `TodayCause`, `WHATS_SENT`, `causeActionLabel`, `causeSecondActionLabel`, `causeSendsPassages`, `causeSentence`, `causeTopicsFailed`, `causeUnderway`, `causeWait`, `continueLessonLine`, `goalCauseSentence`, `heldLine`, `notAskableOnList`, `readingItemIds`, `readyWithWorkSentence`, `todayCause`, `waitingOnList`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AiConnectionDto`, `BuildDetailDto`, `PendingAddDto`, `QueueSnapshot`, `ReadingQuestionsDto`, `ScheduledItemDto`, `SourceLibraryCard`, `SourceStatusLineDto`, `WritingDetailDto`
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
- [apps/learnloop-tauri/src/screens/reader/sectionDone.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/sectionDone.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/LibraryPlace.wholeBook.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/LibraryPlace.wholeBook.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

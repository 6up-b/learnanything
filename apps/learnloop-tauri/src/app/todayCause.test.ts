import { describe, expect, it } from "vitest";
import type { ReadingQuestionsDto, SourceLibraryCard, SourceStatusLineDto } from "../api/dto";
import { findJargon } from "../copy/denyList";
import { WAITING_COPY } from "../copy/waiting";
import {
  allReadWords, causeWait, KEEP_OPEN, KEEP_OPEN_ON_DESKTOP, NOTHING_TO_DO, ON_TODAY, ONE_BOOK_AT_A_TIME, OPEN_THE_BOOK,
  causeActionLabel, causeSentence, causeUnderway, goalCauseSentence, heldLine, MORE_AS_YOU_READ, NO_QUESTIONS_YET, notAskableOnList,
  QUESTIONS_FROM_READING, READING_SAVED, readingItemIds, todayCause, type TodayCause
} from "./todayCause";

describe("the goal's cause line joins the day's cause after a colon", () => {
  it("starts the cause in lower case", () => {
    expect(goalCauseSentence({ kind: "waiting_ok", title: "Variance", others: 0 })).toBe(
      "Nothing for this goal is ready to practise yet: questions for “Variance” are waiting for your OK."
    );
  });

  it("keeps the app's name as it is written", () => {
    expect(goalCauseSentence({ kind: "needs_ai", title: "Variance" })).toBe(
      "Nothing for this goal is ready to practise yet: LearnLoop needs an AI connected to write questions for “Variance”."
    );
    expect(goalCauseSentence({ kind: "no_reading" })).toContain(": LearnLoop writes questions");
  });
});

const PART = "Conditional probability";

function facts(overrides: Partial<ReadingQuestionsDto> = {}): ReadingQuestionsDto {
  return { count: 0, itemIds: [], sections: [], writing: [], waiting: [], failed: [], toLookAt: 0, sectionCount: 4, ...overrides };
}

function card(questions: ReadingQuestionsDto): SourceLibraryCard {
  return {
    sourceId: "src_1", title: "Probability", acquisitionKind: "web", canonicalUri: "https://example.org/p", workId: null,
    currentRevisionId: "rev_1", revisionCount: 1, readiness: "ready", unitCount: 4, blockCount: 40, extractionStatus: "completed",
    suggestedRole: null, readerEnabled: true, updateAvailable: false, kindNoun: "book",
    statusLine: { text: "Questions for Ch. 1 come up as you read", tone: "quiet", action: null, details: null, questions }
  };
}

describe("questions from the part of a section read (the first evening, step 4)", () => {
  it("the desktop offers questions from the part read on today's list as from what you've read", () => {
    const cause = todayCause({ cards: [card(facts({ count: 3, itemIds: ["pi_1", "pi_2", "pi_3"], sections: [PART], partRead: [PART] }))], ai: null,
      listItems: 3, listItemIds: ["pi_1", "pi_2", "pi_3"] });
    expect(cause).toMatchObject({ kind: "questions_ready", count: 3, itemId: "pi_1", fromReading: true });
    expect(causeSentence(cause!)).toBe(`3 questions from what you’ve read of “${PART}” are ready. More come as you read on.`);
    expect(causeActionLabel(cause!)).toBe("Begin ↵");
  });

  it("questions from a finished section and from the part read together are not all 'from what you've read'", () => {
    const cause = todayCause({ cards: [card(facts({ count: 2, itemIds: ["pi_1", "pi_2"], sections: ["Bayes' rule", PART], partRead: [PART] }))], ai: null,
      listItems: 2, listItemIds: ["pi_1", "pi_2"] });
    expect(cause).toMatchObject({ kind: "questions_ready" });
    expect(cause).not.toHaveProperty("fromReading");
  });

  it("qualifying topics not started yet: the desktop says they are being written, the phone that the desktop writes them", () => {
    const books = [card(facts({ owed: [PART] }))];
    const desktop = todayCause({ cards: books, ai: null, listItems: 0 });
    expect(desktop).toMatchObject({ kind: "section_writing", part: PART, fromReading: true });
    expect(causeSentence(desktop!)).toBe(`Writing questions from what you’ve read of “${PART}”… Keep reading meanwhile.`);
    const phone = todayCause({ cards: books, ai: null, listItems: 0, listUnknown: true });
    expect(phone).toMatchObject({ kind: "reading_saved" });
    expect(causeSentence(phone!)).toBe(READING_SAVED);
    expect(READING_SAVED).toBe("Your reading is saved. Questions will be written when the desktop is running.");
  });

  it("the phone names questions written from the part read by how many can be asked now", () => {
    const cause = todayCause({ cards: [card(facts({ count: 2, itemIds: ["pi_1", "pi_2"], sections: [PART], partRead: [PART], laterItemIds: ["pi_2"] }))],
      ai: null, listItems: 0, listUnknown: true });
    expect(cause).toMatchObject({ kind: "questions_ready", count: 1, itemId: null, fromReading: true });
    expect(causeSentence(cause!)).toBe(`1 question from what you’ve read of “${PART}” is ready. More come as you read on.`);
  });

  it("reading that qualifies no topic yet: read a little further, not 'finish a section'", () => {
    const cause = todayCause({ cards: [card(facts({ readFurther: [PART] }))], ai: null, listItems: 0 });
    expect(cause).toMatchObject({ kind: "read_further" });
    expect(causeSentence(cause!)).toBe("Read a little further in “Probability” for your first questions.");
    expect(causeActionLabel(cause!)).toBe("Continue reading");
  });

  it("a book with questions already does not ask to read further for its first ones", () => {
    const cause = todayCause({ cards: [card(facts({ count: 1, itemIds: ["pi_1"], sections: ["Bayes' rule"], readFurther: [PART], laterItemIds: ["pi_1"] }))],
      ai: null, listItems: 0 });
    expect(cause?.kind).toBe("none_up");
  });

  it("read before the book is ready: the promise names what was read, not a finished section", () => {
    const cause = todayCause({ cards: [card(facts({ beforeBuild: [PART] }))], ai: null, listItems: 0 });
    expect(cause).toMatchObject({ kind: "section_waiting", fromReading: true });
    expect(causeSentence(cause!)).toBe("Questions from what you’ve read will follow when “Probability” is ready.");
  });
});

describe("the first evening, step 8: one explanation of where questions come from, where to read to, held questions", () => {
  const rule = (text: string) => !/finish(ed)? (a )?sections?|when you finish|as you finish/i.test(text);

  it("one explanation, said in the same words wherever Today gives it", () => {
    expect(QUESTIONS_FROM_READING).toBe("Questions are written from the parts you read.");
    expect(MORE_AS_YOU_READ).toBe("More come as you read on.");
    const ready = todayCause({ cards: [card(facts({ count: 2, itemIds: ["pi_1", "pi_2"], sections: [PART] }))], ai: null, listItems: 2, listItemIds: ["pi_1", "pi_2"] });
    const fromPart = todayCause({ cards: [card(facts({ count: 2, itemIds: ["pi_1", "pi_2"], sections: [PART], partRead: [PART] }))], ai: null, listItems: 2, listItemIds: ["pi_1", "pi_2"] });
    const noneUp = todayCause({ cards: [card(facts({ count: 1, itemIds: ["pi_1"], sections: [PART], laterItemIds: ["pi_1"] }))], ai: null, listItems: 0 });
    const building = todayCause({ cards: [{ ...card(facts()), statusLine: { text: "Getting Ch. 1 ready for questions", tone: "working", action: null, details: null } }], ai: null, listItems: 0 });
    const unread = todayCause({ cards: [card(facts())], ai: null, listItems: 0 });
    // Questions offered, from a finished section or from the part read, and none up today: more come as you read on.
    for (const cause of [ready, fromPart, noneUp]) expect(causeSentence(cause!)).toContain(MORE_AS_YOU_READ);
    // Before any: the rule itself.
    expect(building?.kind).toBe("on_the_way");
    expect(causeSentence(building!)).toBe(`Getting “Probability” ready for questions. ${QUESTIONS_FROM_READING} Keep reading meanwhile.`);
    expect(unread?.kind).toBe("finish_section");
    expect(causeSentence(unread!)).toBe(`Read “Probability” for your first questions. ${QUESTIONS_FROM_READING}`);
    // Never the other rule.
    for (const cause of [ready, fromPart, noneUp, building, unread]) expect(rule(causeSentence(cause!))).toBe(true);
    const noTopics: TodayCause = { kind: "no_topics", title: "Probability", card: card(facts()), sourceId: "src_1" };
    expect(rule(causeSentence(noTopics))).toBe(true);
  });

  it("where to read to: the heading the place lies under", () => {
    const cause = todayCause({ cards: [card(facts({ readFurther: [PART], readTo: { section: PART, heading: "Variance", words: null, sectionEnd: false } }))], ai: null, listItems: 0 });
    expect(cause).toMatchObject({ kind: "read_further" });
    expect(causeSentence(cause!)).toBe("Read through “Variance” in “Probability” for your first questions.");
  });

  it("where to read to: with no inner heading, the passage's opening words", () => {
    const cause = todayCause({ cards: [card(facts({ readFurther: [PART], readTo: { section: PART, heading: null, words: "Suppose we have a dataset of…", sectionEnd: false } }))], ai: null, listItems: 0 });
    expect(causeSentence(cause!)).toBe("Read as far as the passage that begins “Suppose we have a dataset of…” in “Probability” for your first questions.");
  });

  it("where to read to: the section's last passage is its end (the book's, when it is one section)", () => {
    const place = { section: PART, heading: null, words: null, sectionEnd: true };
    const several = todayCause({ cards: [card(facts({ readFurther: [PART], readTo: place }))], ai: null, listItems: 0 });
    expect(causeSentence(several!)).toBe(`Read to the end of “${PART}” in “Probability” for your first questions.`);
    const one = todayCause({ cards: [card(facts({ readFurther: ["Document"], sectionCount: 1, readTo: { ...place, section: "Document" } }))], ai: null, listItems: 0 });
    expect(causeSentence(one!)).toBe("Read to the end of “Probability” for your first questions.");
  });

  it("where to read to: nothing known, the words say no more than that", () => {
    const cause = todayCause({ cards: [card(facts({ readFurther: [PART] }))], ai: null, listItems: 0 });
    expect(causeSentence(cause!)).toBe("Read a little further in “Probability” for your first questions.");
  });

  it("held questions: one line of their own, counting those an OK would apply, with more beside questions there", () => {
    expect(heldLine([card(facts({ toLookAt: 3, awaitingOk: 2, count: 1, itemIds: ["pi_1"], sections: [PART] }))])).toBe("2 more questions need your OK.");
    expect(heldLine([card(facts({ toLookAt: 1, awaitingOk: 1, count: 1, itemIds: ["pi_1"], sections: [PART] }))])).toBe("1 more question needs your OK.");
    expect(heldLine([card(facts({ toLookAt: 2, awaitingOk: 2 }))])).toBe("2 questions need your OK.");
    // Held rows an OK could not apply (refused, or blocked) are not counted.
    expect(heldLine([card(facts({ toLookAt: 4 }))])).toBeNull();
    expect(heldLine(null)).toBeNull();
    // Across books.
    expect(heldLine([card(facts({ awaitingOk: 2, toLookAt: 2 })), { ...card(facts({ awaitingOk: 1, toLookAt: 1 })), sourceId: "src_2" }])).toBe("3 questions need your OK.");
  });

  it("every question held: the cause says so, with no answer-revealing link (Continue reading)", () => {
    const cause = todayCause({ cards: [card(facts({ toLookAt: 3, awaitingOk: 3, sections: [] }))], ai: null, listItems: 0 });
    expect(cause).toMatchObject({ kind: "held", count: 3 });
    expect(causeSentence(cause!)).toBe("3 questions from what you’ve read in “Probability” need your OK.");
    expect(causeActionLabel(cause!)).toBe("Continue reading");
    // Held rows no OK could apply leave the cause to what the book's reading says.
    expect(todayCause({ cards: [card(facts({ toLookAt: 2 }))], ai: null, listItems: 0 })?.kind).not.toBe("held");
  });

  it("work under way is told by its cause, so the heading above it can say no questions are ready yet", () => {
    expect(NO_QUESTIONS_YET).toBe("No questions ready yet.");
    const kinds = (cause: TodayCause | null) => causeUnderway(cause);
    expect(kinds(todayCause({ cards: [card(facts({ writing: [PART] }))], ai: null, listItems: 0 }))).toBe(true);
    expect(kinds(todayCause({ cards: [card(facts({ beforeBuild: [PART] }))], ai: null, listItems: 0 }))).toBe(true);
    expect(kinds(todayCause({ cards: [card(facts({ readFurther: [PART] }))], ai: null, listItems: 0 }))).toBe(false);
    expect(kinds(todayCause({ cards: [card(facts({ count: 1, itemIds: ["pi_1"], sections: [PART], writing: [PART] }))], ai: null, listItems: 1, listItemIds: ["pi_1"] }))).toBe(false);
    expect(kinds(null)).toBe(false);
  });

  it("what on today's list cannot be asked now: waiting to come back, or a book's question kept for a later check", () => {
    const books = [card(facts({ count: 2, itemIds: ["pi_1", "pi_2"], sections: [PART], laterItemIds: ["pi_2"] }))];
    expect(notAskableOnList(books, ["pi_1", "pi_2", "pi_3"], ["pi_3"]).sort()).toEqual(["pi_2", "pi_3"]);
    expect(notAskableOnList(null, ["pi_1"], [])).toEqual([]);
  });
});

// The live walk partread-3 (2026-11-21): the count restarted with each wave of question writing ("2 of 4 topics done",
// then, after reading on, "0 of 3 topics done"). UX-75: one count for the book, across its waves.
describe("one topic count across the waves of a book's writing (UX-75)", () => {
  const TITLE = "Probability";
  const one = (overrides: Partial<ReadingQuestionsDto>) => card(facts({ sectionCount: 1, ...overrides }));

  it("while the second wave is written: topics written so far and still being written, never a count that restarts", () => {
    const books = [one({ writing: ["Document"], partRead: ["Document"], progress: { done: 0, total: 3 }, topics: { written: 2, writing: 3 } })];
    const cause = todayCause({ cards: books, ai: null, listItems: 0 });
    expect(cause).toMatchObject({ kind: "section_writing", topics: { written: 2, writing: 3 } });
    expect(causeSentence(cause!)).toBe(`Writing questions from what you’ve read in “${TITLE}” · 2 topics written · 3 more being written. Keep reading meanwhile.`);
    expect(causeSentence(cause!)).not.toMatch(/0 of 3|topics done/);
  });

  it("questions ready while the second wave is written: the same count beside the offer", () => {
    const ids = ["pi_4", "pi_5", "pi_6", "pi_7", "pi_8"];
    const books = [one({ count: 5, itemIds: ids, sections: ["Document"], writing: ["Document"], partRead: ["Document"],
      progress: { done: 0, total: 3 }, topics: { written: 3, writing: 3 } })];
    const cause = todayCause({ cards: books, ai: null, listItems: 5, listItemIds: ids });
    expect(causeSentence(cause!)).toBe(`5 questions from what you’ve read in “${TITLE}” are ready. 3 topics written · 3 more being written.`);
  });

  it("before any topic is written, the count says how many are being written", () => {
    const cause = todayCause({ cards: [one({ writing: ["Document"], partRead: ["Document"], progress: { done: 0, total: 4 }, topics: { written: 0, writing: 4 } })], ai: null, listItems: 0 });
    expect(causeSentence(cause!)).toBe(`Writing questions from what you’ve read in “${TITLE}” · 4 topics being written. Keep reading meanwhile.`);
    const single = todayCause({ cards: [one({ writing: ["Document"], partRead: ["Document"], topics: { written: 1, writing: 1 } })], ai: null, listItems: 0 });
    expect(causeSentence(single!)).toContain("· 1 topic written · 1 more being written.");
  });

  it("the detail's topic is placed in the same count: topic 3 of 5, not 1 of 3", () => {
    const writingDetail = { asOf: null, startedAt: null, queued: false, retry: false, topic: { title: "Spectral theorem", index: 1, total: 3 },
      topicStartedAt: null, delivery: null, measured: null };
    const cause = todayCause({ cards: [one({ writing: ["Document"], partRead: ["Document"], topics: { written: 2, writing: 3 }, writingDetail })], ai: null, listItems: 0 });
    expect(cause).toMatchObject({ kind: "section_writing", detail: { topic: { title: "Spectral theorem", index: 3, total: 5 } } });
    // With another job writing beside it (no place), the detail keeps naming the topic alone.
    const unplaced = { ...writingDetail, topic: { title: "Spectral theorem", index: null, total: null } };
    const other = todayCause({ cards: [one({ writing: ["Document"], topics: { written: 2, writing: 3 }, writingDetail: unplaced })], ai: null, listItems: 0 });
    expect(other).toMatchObject({ detail: { topic: { index: null, total: null } } });
  });

  it("a count over several sections is said only where the line names the book, never beside one section's name", () => {
    const books = [card(facts({ sections: ["Bayes' rule"], count: 1, itemIds: ["pi_1"], laterItemIds: ["pi_1"], writing: [PART],
      progress: { done: 0, total: 3 }, topics: { written: 2, writing: 3 } }))];
    const cause = todayCause({ cards: books, ai: null, listItems: 0 });
    expect(cause).toMatchObject({ kind: "section_writing", part: PART });
    expect(causeSentence(cause!)).not.toContain("topics written");
  });

  it("an older sidecar's fact (no count across waves) keeps the wave's own words", () => {
    const cause = todayCause({ cards: [one({ writing: ["Document"], partRead: ["Document"], progress: { done: 0, total: 4 } })], ai: null, listItems: 0 });
    expect(causeSentence(cause!)).toBe(`Writing questions from what you’ve read in “${TITLE}” · 0 of 4 topics done. Keep reading meanwhile.`);
  });

  it("the questions written from the reading, across the books, for a check that keeps one (UX-69)", () => {
    expect(readingItemIds([card(facts({ count: 2, itemIds: ["pi_1", "pi_2"] })), { ...card(facts({ count: 1, itemIds: ["pi_3"] })), sourceId: "src_2" }]))
      .toEqual(["pi_1", "pi_2", "pi_3"]);
    expect(readingItemIds(null)).toEqual([]);
  });
});

// The live walk sectionend-1 (2026-11-21): a student read a one-section chapter to its end while it was still being got
// ready, and Today kept saying "Keep reading meanwhile." with nothing left to read (UX-70); the first build's wait
// told her only to wait, in three scattered lines, and she gave up (UX-82).
describe("a book read to its end while it is got ready or its questions are written (UX-70, UX-82)", () => {
  const BOOK = "Symmetric Matrices and Variance";
  const detail = { asOf: "2026-11-21T18:04:00Z", startedAt: "2026-11-21T18:00:00Z", stage: "planning" as const, retry: false,
    delivery: null, measured: null, synthesis: { part: 1, parts: 1, pass: "plan" as const } };
  function building(questions: ReadingQuestionsDto, line: Partial<SourceStatusLineDto> = {}): SourceLibraryCard {
    return { ...card(questions), title: BOOK, unitCount: 1,
      statusLine: { text: "Getting this article ready for questions", tone: "working", action: null, details: null,
        progress: { done: 1, total: 2 }, minutes: null, buildDetail: detail, questions, ...line } };
  }
  const read = (overrides: Partial<ReadingQuestionsDto> = {}) => facts({ waiting: ["Document"], sectionCount: 1, allRead: true, ...overrides });

  it("the first build: one calm block says it is all read, what comes and that LearnLoop must stay open, never 'keep reading'", () => {
    const cause = todayCause({ cards: [building(read())], ai: null, listItems: 0 });
    expect(cause).toMatchObject({ kind: "on_the_way", firstBuild: true, allRead: true });
    const wait = causeWait(cause!)!;
    expect(wait.line).toBe(`Getting “${BOOK}” ready for questions · 1 of 2 steps done`);
    expect(wait.after).toBe(
      `${allReadWords(BOOK)} Your questions from what you read will be written as soon as “${BOOK}” is ready. ${ON_TODAY} ` +
      `${NOTHING_TO_DO} ${WAITING_COPY.firstBuildLater} ${KEEP_OPEN}`);
    // The first-time sentence is in the block, so the indicator does not say it a second time.
    expect(wait.later).toBeNull();
    expect(allReadWords(BOOK)).toBe(`You’ve read all of “${BOOK}”.`);
    expect(ON_TODAY).toBe("They'll be on Today.");
    expect(NOTHING_TO_DO).toBe("You don’t need to do anything for them.");
    expect(KEEP_OPEN).toBe("Leave LearnLoop open meanwhile: closing it stops the work until you try again.");
    expect(causeSentence(cause!)).not.toMatch(/keep reading/i);
    // Nothing is left to read: the action opens the book, it does not ask to continue reading it.
    expect(causeActionLabel(cause!)).toBe(OPEN_THE_BOOK);
    expect(findJargon(causeSentence(cause!))).toEqual([]);
  });

  it("on the phone the work is the desktop's: the same block, saying where LearnLoop must stay open", () => {
    const cause = todayCause({ cards: [building(read())], ai: null, listItems: 0, listUnknown: true });
    expect(causeSentence(cause!)).toBe(
      `Getting “${BOOK}” ready for questions · 1 of 2 steps done. ${allReadWords(BOOK)} Your questions from what you read will be ` +
      `written as soon as “${BOOK}” is ready. ${ON_TODAY} ${NOTHING_TO_DO} ${WAITING_COPY.firstBuildLater} ${KEEP_OPEN_ON_DESKTOP}`);
    expect(KEEP_OPEN_ON_DESKTOP).toBe("Leave LearnLoop open on your desktop meanwhile: closing it there stops the work until you try again.");
  });

  it("a later build (a time measured here) says it is all read, without the first-time sentence", () => {
    const cause = todayCause({ cards: [building(read(), { minutes: 4 })], ai: null, listItems: 0 });
    const wait = causeWait(cause!)!;
    expect(wait.after).toBe(
      `${allReadWords(BOOK)} Your questions from what you read will be written as soon as “${BOOK}” is ready. ${ON_TODAY} ${NOTHING_TO_DO} ${KEEP_OPEN}`);
    expect(wait.later).toBeNull();
  });

  it("its questions being written: all read, they come to Today, never 'keep reading'", () => {
    const cause = todayCause({ cards: [{ ...card(read({ waiting: [], writing: ["Document"] })), title: BOOK }], ai: null, listItems: 0 });
    expect(cause).toMatchObject({ kind: "section_writing", allRead: true });
    expect(causeSentence(cause!)).toBe(
      `Writing questions from what you read in “${BOOK}”… ${allReadWords(BOOK)} ${ON_TODAY} ${NOTHING_TO_DO} ${KEEP_OPEN}`);
    expect(causeActionLabel(cause!)).toBe(OPEN_THE_BOOK);
  });

  it("waiting its turn behind another book: all read, and no 'keep reading'", () => {
    const cause = todayCause({ cards: [building(read(), { waitingBehind: "Probability" })], ai: null, listItems: 0 });
    expect(causeWait(cause!)?.after).toBe(`${ONE_BOOK_AT_A_TIME} ${allReadWords(BOOK)} ${KEEP_OPEN}`);
  });

  it("with something left to read the words are as before: keep reading meanwhile, and the first-time line under the indicator", () => {
    const cause = todayCause({ cards: [building(facts({ waiting: ["Document"], sectionCount: 1 }))], ai: null, listItems: 0 });
    expect(cause).not.toHaveProperty("allRead");
    const wait = causeWait(cause!)!;
    expect(wait.after).toBe(`Your questions from what you read will be written as soon as “${BOOK}” is ready. Keep reading meanwhile.`);
    expect(wait.later).toBe(WAITING_COPY.firstBuildLater);
    expect(causeActionLabel(cause!)).toBe("Continue reading");
  });
});

import { describe, expect, it } from "vitest";
import type { ReadingQuestionsDto, SourceLibraryCard } from "../api/dto";
import {
  causeActionLabel, causeSentence, causeUnderway, goalCauseSentence, heldLine, MORE_AS_YOU_READ, NO_QUESTIONS_YET, notAskableOnList,
  QUESTIONS_FROM_READING, READING_SAVED, todayCause, type TodayCause
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

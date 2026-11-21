import { describe, expect, it } from "vitest";
import type { ReadingQuestionsDto, SourceLibraryCard } from "../api/dto";
import { causeActionLabel, causeSentence, goalCauseSentence, READING_SAVED, todayCause } from "./todayCause";

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

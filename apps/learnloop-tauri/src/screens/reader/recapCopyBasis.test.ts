// RW1b's formative records in the recap say whose answer the learner's was
// compared with: the book's own lines, or LearnLoop's model's (answer_basis).
import { expect, it } from "vitest";
import { observationLine } from "./recapCopy";

it("a missed answer names whose answer it differed from", () => {
  expect(observationLine("next_step_missed", null, { answerBasis: "source" })).toBe("your next-step guess differed from the book's");
  expect(observationLine("why_step_missed", null, { answerBasis: "model" })).toBe(
    "your answer to why a step holds differed from LearnLoop's model's answer",
  );
  // RW6a's wording when nothing says (no record of the basis).
  expect(observationLine("assumption_missed")).toBe("your answer about the assumptions differed from the book's");
});

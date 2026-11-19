import { describe, expect, it } from "vitest";
import { goalCauseSentence } from "./todayCause";

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

import { expect, it } from "vitest";
import { authoredQuestionMessage } from "./authoredQuestion";

// Daily-loop audit (2026-10-11): after "write my own question" the reader always
// said "It will return as personal practice", even when nothing was scheduled.
// The promise may only appear when the sidecar reports a scheduled Practice Item.
it("promises personal practice only when the card was scheduled", () => {
  const scheduled = authoredQuestionMessage("scheduled");
  expect(scheduled.scheduled).toBe(true);
  expect(scheduled.text).toMatch(/return as personal practice/);

  for (const status of ["reference_only", undefined, "offline_demo"] as const) {
    const outcome = authoredQuestionMessage(status);
    expect(outcome.scheduled).toBe(false);
    expect(outcome.text).not.toMatch(/personal practice/);
  }
});

it("keeps a reference-only card honest about why it is not scheduled", () => {
  expect(authoredQuestionMessage("reference_only").text).toMatch(/not scheduled/);
  expect(authoredQuestionMessage("offline_demo").text).toMatch(/nothing was saved/i);
});

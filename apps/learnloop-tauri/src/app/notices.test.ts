// Notices that ask the learner to do something first stand only until it is
// done (UX Phase 1 usability round 2: "Begin today's plan on Start first." stayed
// over the Reader and Today after the plan had begun).
import { expect, it } from "vitest";
import { NEEDS_SESSION, noticeAfterSessionBegins } from "./notices";

it.each(Object.values(NEEDS_SESSION))("'%s' clears once a session begins", (message) => {
  expect(noticeAfterSessionBegins(message)).toBeNull();
});

it("leaves any other notice, and no notice, as it is", () => {
  expect(noticeAfterSessionBegins("Already in your library — opened where you left off.")).toBe(
    "Already in your library — opened where you left off."
  );
  expect(noticeAfterSessionBegins(null)).toBeNull();
});

it("names every session-first notice the shell shows", () => {
  expect(Object.values(NEEDS_SESSION)).toEqual(
    expect.arrayContaining([
      "Begin today's plan on Start first.",
      "Start a session before opening practice."
    ])
  );
});

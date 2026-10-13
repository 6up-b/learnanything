// Plain failure lines (spec §6.7): a code whose backend message is already a
// plain sentence for the learner is shown as it is, never "Something went
// wrong" (usability round 2: "Read it again with text recognition" ended in
// "Something went wrong. Try again." while the backend said exactly why).
import { expect, it } from "vitest";
import { plainError } from "./ingestErrors";

it("shows the backend's own sentence when text recognition isn't installed", () => {
  const message =
    "Text recognition isn't installed on this computer, so LearnLoop can't read the words of a scan yet. " +
    "To add it, run uv sync --extra pdf in LearnLoop's folder, then restart LearnLoop.";
  const plain = plainError({ code: "text_recognition_unavailable", message, retryable: false });
  expect(plain.line).toBe(message);
  expect(plain.line).not.toMatch(/Something went wrong/);
});

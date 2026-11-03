import { expect, it } from "vitest";
import { phoneAttemptType } from "./attemptType";

it("is an independent attempt wherever that is allowed", () => {
  expect(phoneAttemptType([])).toBe("independent_attempt");
  expect(phoneAttemptType(["hinted_attempt", "independent_attempt"])).toBe("independent_attempt");
  expect(phoneAttemptType(["guided_walkthrough", "hinted_attempt"])).toBe("hinted_attempt");
});

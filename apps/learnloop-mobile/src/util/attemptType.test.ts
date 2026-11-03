import { expect, it } from "vitest";
import { phoneAttemptType } from "./attemptType";

it("is an independent attempt wherever that is allowed", () => {
  expect(phoneAttemptType([])).toBe("independent_attempt");
  expect(phoneAttemptType(["hinted_attempt", "independent_attempt"])).toBe("independent_attempt");
  expect(phoneAttemptType(["guided_walkthrough", "hinted_attempt"])).toBe("hinted_attempt");
});

it("help on a draft is an assisted type where the item allows one, as on the desktop", () => {
  expect(phoneAttemptType(["independent_attempt", "hinted_attempt"], 1)).toBe("hinted_attempt");
  expect(phoneAttemptType([], 1)).toBe("hinted_attempt");
  expect(phoneAttemptType(["independent_attempt"], 1)).toBe("independent_attempt");
  expect(phoneAttemptType(["independent_attempt", "hinted_attempt"], 0)).toBe("independent_attempt");
});

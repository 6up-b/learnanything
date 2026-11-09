// RE0 review: a phone question's carried active time is forgotten wherever its draft is cleared (finish, startup
// recovery, a waiting job's completion, a successful skip all clear the draft), so a later attempt on the same item in
// the same session starts from zero and never inherits submitted seconds.
import { beforeEach, expect, it } from "vitest";
import { carriedActiveMs, defaultActiveStorage, keepActiveMs } from "@desktop/screens/attemptClock";
import { clearQuestionDraft, clearQuestionDrafts, clearSessionCache, phoneClockKey } from "./sessionCache";

beforeEach(() => localStorage.clear());

it("clearing a question's draft forgets its clock, and only that question's", () => {
  const storage = defaultActiveStorage();
  keepActiveMs(storage, phoneClockKey("s1", "i1"), 60_000);
  keepActiveMs(storage, phoneClockKey("s1", "i2"), 9_000);
  clearQuestionDraft("s1", "i1");
  expect(carriedActiveMs(storage, phoneClockKey("s1", "i1"))).toBe(0);
  expect(carriedActiveMs(storage, phoneClockKey("s1", "i2"))).toBe(9_000);
});

it("clearing every draft, or the session cache, forgets every phone clock", () => {
  const storage = defaultActiveStorage();
  keepActiveMs(storage, phoneClockKey("s1", "i1"), 60_000);
  keepActiveMs(storage, "workbench:wb1", 5_000);
  clearQuestionDrafts();
  expect(carriedActiveMs(storage, phoneClockKey("s1", "i1"))).toBe(0);
  expect(carriedActiveMs(storage, "workbench:wb1")).toBe(5_000);
  keepActiveMs(storage, phoneClockKey("s2", "i9"), 1_000);
  clearSessionCache();
  expect(carriedActiveMs(storage, phoneClockKey("s2", "i9"))).toBe(0);
});

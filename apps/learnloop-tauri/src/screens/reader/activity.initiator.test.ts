// RO0 row 4 on the desks: the plan's reading names the reading it opened, so only that reading's visit is the plan's;
// every other window's visit (the desks start one per book window in view) is the learner's own.
import { expect, it } from "vitest";
import { setNextReaderVisitInitiator, takeReaderVisitInitiator } from "./activity";

it("a plan's reading is its own reading's visit, taken once; another window's visit is the learner's", () => {
  setNextReaderVisitInitiator("plan", "ext_plan");
  expect(takeReaderVisitInitiator("ext_other")).toBe("learner");
  expect(takeReaderVisitInitiator("ext_plan")).toBe("plan");
  expect(takeReaderVisitInitiator("ext_plan")).toBe("learner");
});

it("named for no reading (the old screen's single visit), the next visit takes it", () => {
  setNextReaderVisitInitiator("plan");
  expect(takeReaderVisitInitiator("ext_any")).toBe("plan");
  expect(takeReaderVisitInitiator()).toBe("learner");
});

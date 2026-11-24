import { expect, it } from "vitest";
import type { IntentRestorationDto, SourceLibraryCard } from "../api/dto";
import { readerTargetForRestoration } from "./intentCheck";
import { readerTargetForReading } from "./dailyPlan";
import type { PlanReadingDto } from "../api/dto";

const card = { sourceId: "src_1", title: "Probability" } as SourceLibraryCard;
const back: IntentRestorationDto = {
  label: "Back to where you studied this",
  detail: "Mixture CDF → integration bounds",
  inquiryRootEventIds: ["ev_1"],
  anchorSpanIds: ["sp_9", "sp_10"],
  extractionId: "ex_1",
  sourceId: "src_1"
};

// The anchor names the reading it was found on (review fix round, major 7): the desks translate it onto the book's
// current reading rather than take it as a span of that one.
it("opens the reader at the check's first anchor span in its source, on the reading it was named on", () => {
  expect(readerTargetForRestoration(back, [card])).toEqual({ card, spanId: "sp_9", reading: "ex_1" });
});

it("opens nothing when the source is gone or unnamed", () => {
  expect(readerTargetForRestoration(back, [])).toBeNull();
  expect(readerTargetForRestoration({ ...back, sourceId: null }, [card])).toBeNull();
});

it("opens the source at its start when only inquiry roots are known", () => {
  expect(readerTargetForRestoration({ ...back, anchorSpanIds: [] }, [card])).toEqual({ card, spanId: null, reading: "ex_1" });
});

it("a plan reading opens at its start passage, on the reading it was named on (major 7)", () => {
  const reading = { sourceId: "src_1", extractionId: "ex_1", startSpanId: "sp_3" } as PlanReadingDto;
  expect(readerTargetForReading(reading, [card])).toEqual({ card, spanId: "sp_3", reading: "ex_1" });
});

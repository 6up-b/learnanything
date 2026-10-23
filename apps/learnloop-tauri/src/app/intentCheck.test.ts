import { expect, it } from "vitest";
import type { IntentRestorationDto, SourceLibraryCard } from "../api/dto";
import { readerTargetForRestoration } from "./intentCheck";

const card = { sourceId: "src_1", title: "Probability" } as SourceLibraryCard;
const back: IntentRestorationDto = {
  label: "Back to where you studied this",
  detail: "Mixture CDF → integration bounds",
  inquiryRootEventIds: ["ev_1"],
  anchorSpanIds: ["sp_9", "sp_10"],
  extractionId: "ex_1",
  sourceId: "src_1"
};

it("opens the reader at the check's first anchor span in its source", () => {
  expect(readerTargetForRestoration(back, [card])).toEqual({ card, spanId: "sp_9" });
});

it("opens nothing when the source is gone or unnamed", () => {
  expect(readerTargetForRestoration(back, [])).toBeNull();
  expect(readerTargetForRestoration({ ...back, sourceId: null }, [card])).toBeNull();
});

it("opens the source at its start when only inquiry roots are known", () => {
  expect(readerTargetForRestoration({ ...back, anchorSpanIds: [] }, [card])).toEqual({ card, spanId: null });
});

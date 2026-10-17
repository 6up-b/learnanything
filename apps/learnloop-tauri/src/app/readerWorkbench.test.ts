// RW2a's way back (spec §5.1, UX S6): a Reader workbench attempt goes to
// feedback with a way back to its problem; Esc or b from feedback opens the
// Reader at that problem, the submitted session read-only, while Next returns
// to reading at its passage; every other attempt goes back as today.
import { expect, it } from "vitest";
import type { SessionSnapshot, SourceLibraryCard, WorkbenchSubmitDto } from "../api/dto";
import { returnsToReader } from "./readerCheck";
import { readerCheckOffer } from "./readerCheck";
import { readerTargetBack, readerWorkbenchCheck, sessionAfterWorkbenchSubmit, workbenchReturn } from "./readerWorkbench";

const card = { sourceId: "src", title: "Probability" } as SourceLibraryCard;
const result = {
  version: 1,
  attempt: { attemptId: "att_1" },
  session: { sessionId: "wb1", practiceItemId: "pi_514", status: "submitted", attemptId: "att_1" },
  practiceSession: { sessionId: "ps_new" },
} as unknown as WorkbenchSubmitDto;

it("a Reader workbench attempt keeps the way back to its problem", () => {
  const back = workbenchReturn(result, { card, spanId: "b2" });
  expect(back).toEqual({ card, spanId: "b2", practiceItemId: "pi_514", workbenchAttemptId: "att_1" });
  expect(returnsToReader(back, "pi_514")).toBe(true);
  expect(returnsToReader(back, "pi_other")).toBe(false);
});

it("Esc or b opens the submitted problem; Next returns to reading at the passage", () => {
  const back = workbenchReturn(result, { card, spanId: "b2" });
  expect(readerTargetBack(back, { showProblem: true })).toEqual({ source: { card, spanId: "b2" }, initialAttemptId: "att_1" });
  expect(readerTargetBack(back, { showProblem: false })).toEqual({ source: { card, spanId: "b2" }, initialAttemptId: null });
  // A Reader check (RW3a) has no workbench attempt: its passage, as before.
  expect(readerTargetBack({ card, spanId: "b1", practiceItemId: "pi_check" }, { showProblem: true })).toEqual({
    source: { card, spanId: "b1" }, initialAttemptId: null,
  });
});

it("the submit's practice session becomes the app's when it had none or another", () => {
  const app = { sessionId: "ps_app" } as SessionSnapshot;
  const fresh = { sessionId: "ps_new" } as SessionSnapshot;
  expect(sessionAfterWorkbenchSubmit(null, fresh)).toBe(fresh);
  expect(sessionAfterWorkbenchSubmit(app, fresh)).toBe(fresh);
  expect(sessionAfterWorkbenchSubmit(app, { sessionId: "ps_app" } as SessionSnapshot)).toBe(app);
  expect(sessionAfterWorkbenchSubmit(app, null)).toBe(app);
});

// Review F12 (D40): check me stays in the Reader as the pick's own serve.
it("check me with the workbench on opens in the Reader as the pick's serve, plan on or off", () => {
  const request = { practiceItemId: "pi_c", spanId: "b4", card };
  const planOn = readerCheckOffer(
    { enabled: true, step: { kind: "item", practiceItemId: "pi_c", schedulerCandidateId: "cand", presentationId: "pres" } } as never,
    "pi_c", "prop_1",
  );
  expect(readerWorkbenchCheck(request, planOn, "Is A^T A symmetric?")).toEqual({
    practiceItemId: "pi_c", spanId: "b4", sourceId: "src", stemMd: "Is A^T A symmetric?",
    schedulerCandidateId: "cand", planPresentationId: "pres",
  });
  const planOff = readerCheckOffer({ enabled: false, step: null } as never, "pi_c", "prop_1");
  expect(readerWorkbenchCheck(request, planOff, "Q")).toMatchObject({ schedulerCandidateId: null, planPresentationId: null });
});

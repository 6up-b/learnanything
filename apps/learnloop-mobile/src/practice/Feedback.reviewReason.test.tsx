// The phone's feedback never prints a grade's review reason code (phone-3 #10: "valid_alternative_unverified"
// under the score). Every code the sidecar writes there (`practice_attempts.manual_review_reason`) shows the
// words the desktop uses for the same thing, or nothing where the desktop's feedback says nothing; a code it
// does not know shows nothing, never itself.
import { findJargon } from "@desktop/copy/denyList";
import {
  HELD_GRADE_LINE, PROVISIONAL_GRADE_LINE, REVIEW_REASON_CODES, UNASSESSED_ROUTE_LINE, reviewReasonLine
} from "@desktop/app/practiceFeedback";
import { NOT_ASSESSED_LABEL } from "@desktop/api/dto";
import { answers, beginSession, describe, expect, feedback, fireEvent, installFakeHost, it, screen } from "../test/fakeHost";

installFakeHost();

async function feedbackWith(extra: Record<string, unknown>) {
  answers.get_feedback = { ...feedback(), ...extra };
  await beginSession();
  fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
  await screen.findByText("Define it.");
  const editor = screen.getByRole("textbox", { name: "Your answer" });
  editor.textContent = "My answer";
  fireEvent.input(editor);
  fireEvent.click(screen.getByRole("button", { name: "Submit" }));
  await screen.findByText(/^\d+ \/ \d+$/);
  return document.body.textContent ?? "";
}

// Each code with what the phone shows for it: the desktop's own sentence, or nothing.
const EXPECTED: Record<(typeof REVIEW_REASON_CODES)[number], string | null> = {
  valid_alternative_unverified: UNASSESSED_ROUTE_LINE,
  provisional_pending_clarification: `${PROVISIONAL_GRADE_LINE}.`,
  grade_held_for_review: HELD_GRADE_LINE,
  grade_contract_unrecorded: HELD_GRADE_LINE,
  codex_manual_review: null,
  low_grader_confidence: null,
  low_self_confidence: null,
  blank_answer: null,
  unknown_target_evidence_family: null,
  unknown_target_criterion: null,
  unanchored_diagnosis_facet: null,
  attribution_scope: null,
  unknown_error_type: null,
};

describe("UX-23: a review reason in words, never its code", () => {
  it.each([...REVIEW_REASON_CODES])("%s", async (code) => {
    // The codes that carry ids after a colon arrive that way.
    const sent = /^(unknown_|unanchored_|attribution_)/.test(code) ? `${code}:c1,c2` : code;
    const text = await feedbackWith({ manualReviewReason: sent });
    expect(text).not.toContain(code);
    expect(text).not.toMatch(/\b[a-z]+_[a-z_]+\b/);
    const line = screen.queryByTestId("review-reason");
    expect(line?.textContent ?? null).toBe(EXPECTED[code]);
    expect(findJargon(line?.textContent ?? "")).toEqual([]);
  });

  it("a code the phone doesn't know shows nothing, not itself", async () => {
    const text = await feedbackWith({ manualReviewReason: "some_future_reason:x" });
    expect(text).not.toContain("some_future_reason");
    expect(screen.queryByTestId("review-reason")).toBeNull();
    expect(reviewReasonLine("Grader asked for a look")).toBeNull();
  });

  it("no reason, no line (phone-3's other feedback)", async () => {
    await feedbackWith({ manualReviewReason: null });
    expect(screen.queryByTestId("review-reason")).toBeNull();
  });

  it("a criterion a different route didn't use says so, as on the desktop, instead of a lost point", async () => {
    await feedbackWith({
      rubricScore: 4, maxPoints: 4, manualReviewReason: "valid_alternative_unverified",
      criterionEvidence: [
        { criterionId: "c1", criterionDescription: "Sets up the product", pointsAwarded: 1, pointsPossible: 3, notes: null },
        { criterionId: "c2", criterionDescription: "Names the inverse", pointsAwarded: 0, pointsPossible: 1, notes: null, assessed: false },
      ],
    });
    expect(screen.getByText("(1/3)")).toBeTruthy();
    expect(screen.queryByText("(0/1)")).toBeNull();
    expect(screen.getByText(`(${NOT_ASSESSED_LABEL})`)).toBeTruthy();
  });
});

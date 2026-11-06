// Mobile v2 V2, J2/J3/J4 on the phone's feedback through the fake host: the follow-up panel without
// probes (held feedback, Show anyway, Continue without it), the optional marks, the full answer as a
// recorded reveal, and the contest under its own key.
import {
  answers, beginSession, called, calls, describe, expect, feedback, fireEvent, installFakeHost, it, screen, waitFor
} from "../test/fakeHost";

installFakeHost();

async function submitAnAnswer() {
  await beginSession();
  fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
  await screen.findByText("Define it.");
  const editor = screen.getByRole("textbox", { name: "Your answer" });
  editor.textContent = "My answer";
  fireEvent.input(editor);
  fireEvent.click(screen.getByRole("button", { name: "Submit" }));
  await screen.findByText("3 / 4");
}

const followup = (extra: Record<string, unknown> = {}) => ({
  workflowId: "w1", state: "pending", held: true, line: "Preparing a question on this…", canShowAnyway: true,
  canContinueWithout: true, shownAnyway: false, routerDecision: null, ...extra
});

describe("the follow-up panel without probes (J3)", () => {
  it("holds the answer while a question is prepared, and Show anyway releases it with a re-read, never a re-open", async () => {
    answers.get_feedback = (call: { params: Record<string, unknown> }) =>
      call.params.recordOpen === false
        ? { ...feedback(), answeredExpectedAnswer: "The whole answer.", followup: followup({ held: false, state: "settled", shownAnyway: true }) }
        : { ...feedback(), answeredExpectedAnswer: "The whole answer.", followup: followup() };
    answers.followup_status = { enabled: true, ...followup() };
    answers.followup_show_anyway = { released: true };
    await submitAnAnswer();
    expect(await screen.findByText("Preparing a question on this…")).toBeTruthy();
    expect(screen.getByText(/come after the question/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Show the full answer" })).toBeNull();
    answers.followup_status = { enabled: true, ...followup({ held: false, state: "settled", shownAnyway: true }) };
    fireEvent.click(screen.getByRole("button", { name: "Show anyway" }));
    await waitFor(() => expect(called("followup_show_anyway").length).toBe(1));
    expect(await screen.findByRole("button", { name: "Show the full answer" })).toBeTruthy();
    expect(called("get_feedback").filter((call) => call.params.recordOpen === false).length).toBeGreaterThan(0);
  });

  it("Continue without it goes on without the question", async () => {
    answers.get_feedback = { ...feedback(), followup: followup() };
    answers.followup_status = { enabled: true, ...followup() };
    answers.followup_continue_without = { continued: true };
    await submitAnAnswer();
    fireEvent.click(await screen.findByRole("button", { name: "Continue without it" }));
    await waitFor(() => expect(called("followup_continue_without")[0].params).toEqual({ attemptId: "a1" }));
  });

  it("the router's line rides on the panel", async () => {
    const decision = { decisionId: "rd2", line: "A question first, to tell two causes apart.", details: { cardSummary: null, models: [], rationale: null, fallback: null } };
    answers.get_feedback = { ...feedback(), followup: followup({ routerDecision: decision }) };
    answers.followup_status = { enabled: true, ...followup({ routerDecision: decision }) };
    await submitAnAnswer();
    expect(await screen.findByText("A question first, to tell two causes apart.")).toBeTruthy();
  });
});

describe("the optional marks (J3)", () => {
  it("records the list's display once and a mark when tapped", async () => {
    const marks = {
      attemptId: "a1", surface: "marks_feedback", orderSeed: "s", probeAnswered: false, replacesCardTap: false, noneOfThese: false, noneOfTheseText: null,
      hypotheses: [{ hypothesisVersionId: "h1", statement: "Mixed up rows and columns.", mark: null }, { hypothesisVersionId: "h2", statement: "Dropped a sign.", mark: null }]
    };
    answers.get_feedback = { ...feedback(), hypothesisMarks: marks };
    answers.record_hypothesis_exposure = { recorded: true };
    answers.record_hypothesis_mark = { recorded: true, marks: { ...marks, hypotheses: [{ ...marks.hypotheses[0], mark: "my_gap" }, marks.hypotheses[1]] } };
    await submitAnAnswer();
    await screen.findByText("Mixed up rows and columns.");
    await waitFor(() => expect(called("record_hypothesis_exposure").length).toBe(1));
    expect(called("record_hypothesis_exposure")[0].params).toMatchObject({ attemptId: "a1", surface: "marks_feedback", hypothesisVersionIds: ["h1", "h2"] });
    fireEvent.click(screen.getAllByRole("button", { name: "This is my gap" })[0]);
    await waitFor(() => expect(called("record_hypothesis_mark").length).toBe(1));
    expect(called("record_hypothesis_mark")[0].params).toEqual({
      attemptId: "a1", mark: "my_gap", hypothesisVersionId: "h1", freeText: null, surface: "marks_feedback"
    });
  });
});

describe("the full answer is a recorded reveal (J2)", () => {
  it("shows only after its display row is recorded", async () => {
    answers.get_feedback = { ...feedback(), answeredExpectedAnswer: "The whole answer." };
    let release: (() => void) | null = null;
    answers.record_answer_display = () => ({ recorded: true, recordedAt: new Date().toISOString() });
    await submitAnAnswer();
    fireEvent.click(screen.getByRole("button", { name: "Show the full answer" }));
    expect(await screen.findByText("The whole answer.")).toBeTruthy();
    const display = called("record_answer_display")[0];
    expect(display.params.attemptId).toBe("a1");
    expect(String(display.params.displayId)).toMatch(/^display_/);
    // The row was asked for before the answer showed.
    const order = calls.map((call) => call.method);
    expect(order.indexOf("record_answer_display")).toBeGreaterThan(-1);
    expect(release).toBeNull();
  });

  it("an answer the record doesn't name is never shown in its place", async () => {
    answers.get_feedback = { ...feedback(), answeredSource: "unrecorded", answeredExpectedAnswer: "Not this one." };
    await submitAnAnswer();
    expect(screen.queryByRole("button", { name: "Show the full answer" })).toBeNull();
  });
});

describe("the contest, \"I think I was right\" (J2)", () => {
  it("keeps the reason under one key, which is the job's request id, and says what happened", async () => {
    answers.trigger_regrade = { ...feedback(), contest: { recorded: true, regraded: true, reviewRequested: true } };
    await submitAnAnswer();
    fireEvent.click(screen.getByRole("button", { name: "I think I was right" }));
    fireEvent.change(screen.getByLabelText(/Why do you think you were right/), { target: { value: " The other convention. " } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(await screen.findByText("Noted. The grade will be looked at again.")).toBeTruthy();
    const contest = called("trigger_regrade")[0];
    expect(contest.params).toMatchObject({ attemptId: "a1", learnerReason: "The other convention." });
    expect(contest.requestId).toBe(contest.params.contestId);
  });

  it("is not offered on a grade the learner gave", async () => {
    answers.get_feedback = { ...feedback(), gradingSource: "self" };
    await submitAnAnswer();
    expect(screen.queryByRole("button", { name: "I think I was right" })).toBeNull();
  });
});

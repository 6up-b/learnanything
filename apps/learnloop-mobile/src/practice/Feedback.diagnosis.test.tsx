// The diagnosis on the feedback screen (the owner's M2a follow-ups)
// Split out of App.test.tsx (mobile v2 V2, V1's carried item): the cases are unchanged.
import {
  act, answers, App, beforeEach, beginSession, cacheSessionId, called, calls, cleanup, describe, expect, fakeFetch, feedback, fireEvent,
  getAnswers, gets, installFakeHost, it, item, listOutbox, PLAN_OFF, queue, rememberPendingSubmit, render, respond, row, saveCredential,
  screen, session, vi, waitFor, type Call, type RpcAnswer
} from "../test/fakeHost";

installFakeHost();

describe("the diagnosis on the feedback screen", () => {
  const repairs = [
    { practiceMode: "m", learningObjectId: null, rationale: "r", elicitingQuestion: "First question?", expectedResponseContract: "THE EXPECTED ANSWER" },
    { practiceMode: "m", learningObjectId: null, rationale: "no question here" },
    { practiceMode: "m", learningObjectId: null, rationale: "r", elicitingQuestion: "Second question?" }
  ];
  const card = { version: 1, attemptId: "a1", status: "done", cardEnabled: true, responses: [], summaryMd: "You stopped early." };

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

  it("shows the summary and asks each question in turn, under its own index, without its expected answer", async () => {
    answers.get_feedback = { ...feedback(), diagnosisStatus: "done", repairSuggestions: repairs };
    answers.diagnosis_status = card;
    answers.submit_eliciting_response = { admissibleAsIndependent: true, inadmissibilityReason: null };
    await submitAnAnswer();
    await screen.findByText("You stopped early.");
    await screen.findByText("First question?");
    expect(screen.queryByText("Second question?")).toBeNull();
    expect(screen.queryByText("THE EXPECTED ANSWER")).toBeNull();

    fireEvent.change(screen.getByLabelText("Your answer (optional)"), { target: { value: " logits " } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await screen.findByText("Second question?");
    expect(called("submit_eliciting_response")[0].params).toEqual({ attemptId: "a1", suggestionIndex: 0, responseMd: "logits" });
    expect(screen.getByText("Answer recorded. It isn't graded.")).toBeTruthy();

    fireEvent.change(screen.getByLabelText("Your answer (optional)"), { target: { value: "each exponential" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await screen.findByText("That's all of them.");
    expect(called("submit_eliciting_response")[1].params.suggestionIndex).toBe(2);
    expect(screen.getByRole("button", { name: "Next" })).toBeTruthy();
  });

  it("fills in when a pending diagnosis lands", async () => {
    answers.get_feedback = (call: Call) =>
      call.params.recordOpen === false ? { ...feedback(), diagnosisStatus: "done", repairSuggestions: repairs } : { ...feedback(), diagnosisStatus: "pending", repairSuggestions: [] };
    let polls = 0;
    answers.diagnosis_status = () => (++polls > 1 ? card : { ...card, status: "pending" });
    await submitAnAnswer();
    await screen.findByText("Looking into what happened here…");
    await screen.findByText("First question?", undefined, { timeout: 5000 });
    expect(screen.getByText("You stopped early.")).toBeTruthy();
    expect(screen.queryByText("Looking into what happened here…")).toBeNull();
  });

  it("keeps a typed answer when sending fails, and says when an answer can't count as independent", async () => {
    answers.get_feedback = { ...feedback(), diagnosisStatus: "done", repairSuggestions: repairs };
    answers.diagnosis_status = card;
    answers.submit_eliciting_response = {
      status: 400,
      body: { error: { code: "invalid_eliciting_response", message: "attempt has no open causal factor to respond to", retryable: false } }
    };
    await submitAnAnswer();
    await screen.findByText("First question?");
    const box = screen.getByLabelText("Your answer (optional)") as HTMLTextAreaElement;
    fireEvent.change(box, { target: { value: "logits" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await screen.findByText("attempt has no open causal factor to respond to");
    expect(box.value).toBe("logits");
    expect(called("submit_eliciting_response").length).toBe(1);

    answers.submit_eliciting_response = { admissibleAsIndependent: false, inadmissibilityReason: "answer_revealed" };
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await screen.findByText(/won't count as independent evidence/);
  });

  it("shows nothing extra without a diagnosis, and says so when one failed", async () => {
    await submitAnAnswer();
    expect(called("diagnosis_status")).toEqual([]);
    expect(screen.queryByText("Follow-up questions")).toBeNull();
    expect(screen.queryByText("What happened here")).toBeNull();
    cleanup();
    // A fresh app with no session: before V2 this half began a session in the moment before the cached
    // one loaded (a race); Today now reads the plan first, so the cached session is dropped instead.
    cacheSessionId(null);
    answers.get_feedback = { ...feedback(), diagnosisStatus: "failed", repairSuggestions: [] };
    await submitAnAnswer();
    await screen.findByText("The look into this answer didn't finish. Your grade stands.");
  });
});


// Mobile v2 stage V3 (owner decision D3): probes answered on the phone. The active contract the host says the phone
// answers (`phoneAnswers`) is rendered cold (the desktop's line, no Hint, no help of any kind) and its answer names the
// presentation; Next on a miss's feedback asks its follow-up workflow first: it opens the question, waits while it is
// written, or goes on; a host that answers no probe is V2's phone.
import { findJargon } from "@desktop/copy/denyList";
import {
  answers, beginSession, called, describe, expect, feedback, fireEvent, installFakeHost, it, item, screen, waitFor
} from "../test/fakeHost";
import { PROBE_LINE } from "./QuestionScreen";

installFakeHost();

const RESTRICTIONS = {
  hintsDisabled: true, askTutorDisabled: true, workedExampleDisabled: true, answerRevealDisabled: true, feedbackDeferred: true
};
const CONTRACT = {
  version: 1, active: true, phoneAnswers: true, presentationId: "pres_1", forcedAttemptType: "diagnostic_probe",
  restrictions: RESTRICTIONS, followupWhy: "This question comes from your last answer."
};

async function openFirst() {
  await beginSession();
  fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
}

async function answerAndSubmit(text = "My answer") {
  const editor = await screen.findByRole("textbox", { name: "Your answer" });
  editor.textContent = text;
  fireEvent.input(editor);
  fireEvent.click(screen.getByRole("button", { name: "Submit" }));
}

describe("a probe the phone answers (V3)", () => {
  it("is cold: the desktop's line, no Hint, and its answer names its presentation with no help", async () => {
    answers.get_probe_contract = CONTRACT;
    answers.get_practice_item = { ...item(), hints: ["Think of the definition."] };
    await openFirst();
    expect((await screen.findByTestId("probe-line")).textContent).toContain(PROBE_LINE);
    expect(screen.getByText(/This question comes from your last answer\./)).toBeTruthy();
    expect(screen.getByText("Define it.")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Hint" })).toBeNull();
    expect(screen.queryByText(/with help/)).toBeNull();
    expect(screen.queryByText(/Continue it on the desktop/)).toBeNull();
    await answerAndSubmit();
    await screen.findByText("3 / 4");
    expect(called("submit_attempt")[0].params).toMatchObject({
      attemptType: "diagnostic_probe", probePresentationId: "pres_1", hintsUsed: 0, authoredHints: 0, bookCounted: false
    });
    expect(called("practice.record_hint_reveal")).toEqual([]);
  });

  it("an active contract the host doesn't say the phone answers waits for the desktop, as in V2", async () => {
    answers.get_probe_contract = { ...CONTRACT, phoneAnswers: undefined };
    await openFirst();
    await screen.findByText(/This is a diagnostic check\. Continue it on the desktop\./);
    expect(screen.queryByRole("textbox")).toBeNull();
  });

  it("an incomplete contract is an error, never a question with help", async () => {
    answers.get_probe_contract = { ...CONTRACT, restrictions: { ...RESTRICTIONS, hintsDisabled: false } };
    answers.get_practice_item = { ...item(), hints: ["Think of the definition."] };
    await openFirst();
    expect((await screen.findAllByText(/This check's rules didn't come through/)).length).toBeGreaterThan(0);
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(screen.queryByRole("button", { name: "Hint" })).toBeNull();
  });

  it("a single-use question already served on the desktop moves on, as one the phone can't show", async () => {
    answers.get_practice_item = (call: { params: Record<string, unknown> }) =>
      call.params.practiceItemId === "i1"
        ? { status: 409, body: { ok: false, error: { code: "generated_probe_closed", message: "m", retryable: false } } }
        : item("i2");
    await openFirst();
    await waitFor(() => expect(called("get_practice_item").at(-1)?.params.practiceItemId).toBe("i2"));
    expect(called("submit_attempt")).toEqual([]);
  });
});

describe("Next on a miss's feedback (FG1 §6.1 on the phone)", () => {
  const held = {
    ...feedback(),
    followup: { workflowId: "w", state: "ready", held: true, line: "Your next question is ready.", canShowAnyway: true, canContinueWithout: true, shownAnyway: false }
  };

  it("opens the miss's question, answered here under its contract", async () => {
    answers.get_feedback = held;
    answers.followup_status = { enabled: true, ...held.followup };
    answers.followup_next = { version: 1, action: "open", line: null, practiceItemId: "p_gen", presentationId: "pres_1" };
    answers.get_practice_item = (call: { params: Record<string, unknown> }) => item(String(call.params.practiceItemId));
    answers.get_probe_contract = (call: { params: Record<string, unknown> }) =>
      call.params.practiceItemId === "p_gen" ? CONTRACT : { version: 1, active: false };
    await openFirst();
    await answerAndSubmit();
    await screen.findByText("Your next question is ready.");
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await screen.findByTestId("probe-line");
    expect(called("followup_next")[0].params).toEqual({ attemptId: "a1" });
    expect(called("get_practice_item").at(-1)?.params).toEqual({ practiceItemId: "p_gen", sessionId: "s1" });
    // The list was not asked for its next question: this one comes first.
    expect(called("get_today_queue")).toHaveLength(1);
  });

  it("waits on Feedback while the question is being written, and says so", async () => {
    answers.get_feedback = { ...held, followup: { ...held.followup, state: "pending", line: "Preparing a question on this…" } };
    answers.followup_status = { enabled: true, ...held.followup, state: "pending", line: "Preparing a question on this…" };
    answers.followup_next = { version: 1, action: "wait", line: "Preparing a question on this…", practiceItemId: null, presentationId: null };
    await openFirst();
    await answerAndSubmit();
    await screen.findByText("3 / 4");
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect((await screen.findByTestId("followup-wait")).textContent).toBe("Preparing a question on this…");
    expect(screen.getByRole("button", { name: "Continue without it" })).toBeTruthy();
    expect(called("get_today_queue")).toHaveLength(1);
  });

  it("goes on when there is nothing to ask, and with the host's switch off asks no more", async () => {
    answers.followup_next = { status: 409, body: { ok: false, error: { code: "phone_probes_off", message: "off", retryable: false } } };
    await openFirst();
    await answerAndSubmit();
    await screen.findByText("3 / 4");
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() => expect(called("get_today_queue")).toHaveLength(2));
    await screen.findByText("Define it.");
    await answerAndSubmit("Again");
    await screen.findByText("3 / 4");
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() => expect(called("get_today_queue")).toHaveLength(3));
    expect(called("followup_next")).toHaveLength(1);
  });

  it("a probe's answer points back at the feedback it released", async () => {
    answers.get_feedback = (call: { params: Record<string, unknown> }) =>
      call.params.attemptId === "a1"
        ? { ...feedback(), attemptId: "a1", heldFeedbackAttemptId: "a0" }
        : { ...feedback(), attemptId: "a0", learningObjectTitle: "The earlier miss", feedbackMd: "Now you can see it." };
    await openFirst();
    await answerAndSubmit();
    fireEvent.click(await screen.findByRole("button", { name: "See the feedback on your earlier answer" }));
    await screen.findByText("Now you can see it.");
    expect(called("get_feedback").at(-1)?.params.attemptId).toBe("a0");
  });

  it("says nothing from the desktop's deny-list", async () => {
    answers.get_probe_contract = CONTRACT;
    answers.get_feedback = { ...feedback(), heldFeedbackAttemptId: "a0" };
    answers.followup_next = { version: 1, action: "wait", line: "Preparing a question on this…", practiceItemId: null, presentationId: null };
    await openFirst();
    await screen.findByTestId("probe-line");
    const texts = [document.body.textContent ?? ""];
    await answerAndSubmit();
    await screen.findByText("3 / 4");
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await screen.findByTestId("followup-wait");
    texts.push(document.body.textContent ?? "");
    expect(texts.flatMap((text) => findJargon(text))).toEqual([]);
  });
});

// A question: serve, draft, submit, skip
// Split out of App.test.tsx (mobile v2 V2, V1's carried item): the cases are unchanged.
import {
  act, answers, App, beforeEach, beginSession, cacheSessionId, called, calls, cleanup, describe, expect, fakeFetch, feedback, fireEvent,
  getAnswers, gets, installFakeHost, it, item, listOutbox, PLAN_OFF, queue, rememberPendingSubmit, render, respond, row, saveCredential,
  screen, session, vi, waitFor, type Call, type RpcAnswer
} from "../test/fakeHost";

installFakeHost();

describe("a question", () => {
  it("commits the serve, submits under the offer's candidate and shows feedback", async () => {
    await beginSession();
    fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
    await screen.findByText("Define it.");
    expect(called("get_probe_contract")[0].params).toEqual({ practiceItemId: "i1", sessionId: "s1" });
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = "My answer";
    fireEvent.input(editor);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText("3 / 4");
    const submit = called("submit_attempt")[0];
    expect(submit.requestId).toBe(submit.params.submissionId);
    expect(submit.params).toMatchObject({
      sessionId: "s1", practiceItemId: "i1", answerMd: "My answer", attemptType: "independent_attempt",
      schedulerCandidateId: "cand_i1", assessmentContractVersionId: "acv"
    });
    expect(submit.params.selfGrade).toBeUndefined();
    expect(submit.params.probePresentationId).toBeUndefined();
    expect(called("save_practice_draft")[0].params.submissionId).toBe(submit.params.submissionId);
    expect(called("acknowledge_practice_submission")[0].params.submissionId).toBe(submit.params.submissionId);
  });

  it("does not render an active diagnostic check, and moves on without a skip (§6.4)", async () => {
    answers.get_probe_contract = (call: Call) => ({ version: 1, active: call.params.practiceItemId === "i1" });
    await beginSession();
    fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
    await screen.findByText(/This is a diagnostic check\. Continue it on the desktop\./);
    expect(screen.queryByText("Define it.")).toBeNull();
    expect(screen.queryByRole("textbox")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() => expect(called("get_practice_item").at(-1)?.params.practiceItemId).toBe("i2"));
    expect(called("skip_practice_item")).toEqual([]);
    expect(called("submit_attempt")).toEqual([]);
  });

  it("a contract that cannot be read is an error, never ordinary practice", async () => {
    answers.get_probe_contract = { status: 503, body: { ok: false, error: { code: "internal", message: "Could not check this.", retryable: false } } };
    await beginSession();
    fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
    expect(await screen.findAllByText("Could not check this.")).toBeTruthy();
    expect(screen.queryByRole("textbox")).toBeNull();
  });

  it("says grading is down, keeps the answer, and retries the same key", async () => {
    answers.submit_attempt = { status: 409, body: { ok: false, error: { code: "grading_fallback_required", message: "Grade your answer to continue.", retryable: true } } };
    await beginSession();
    fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
    await screen.findByText("Define it.");
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = "My answer";
    fireEvent.input(editor);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    expect(await screen.findByText(/AI grading is unavailable; your answer is saved/)).toBeTruthy();
    expect(screen.queryByText(/Grade your answer/)).toBeNull();
    const first = called("submit_attempt")[0].params.submissionId;
    answers.submit_attempt = { attemptId: "a1", practiceItemId: "i1" };
    getAnswers[`/api/v1/submissions/${String(first)}`] = { state: "failed", error: { code: "grading_fallback_required", message: "m", retryable: true } };
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await screen.findByText("3 / 4");
    // The same request, field for field: the host compares a retry's params (§6.3).
    expect(called("submit_attempt")[1].params).toEqual(called("submit_attempt")[0].params);
    expect(called("submit_attempt")[1].params.submissionId).toBe(first);
  });

  it("an answer edited after a failure is a new request under a new key", async () => {
    answers.submit_attempt = { status: 409, body: { ok: false, error: { code: "grading_fallback_required", message: "m", retryable: true } } };
    await beginSession();
    fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
    await screen.findByText("Define it.");
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = "My answer";
    fireEvent.input(editor);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText(/AI grading is unavailable/);
    const first = called("submit_attempt")[0].params.submissionId;
    getAnswers[`/api/v1/submissions/${String(first)}`] = { state: "failed", error: { code: "grading_fallback_required", message: "m", retryable: true } };
    editor.textContent = "My better answer";
    fireEvent.input(editor);
    answers.submit_attempt = { attemptId: "a1", practiceItemId: "i1" };
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText("3 / 4");
    expect(called("submit_attempt")[1].params.submissionId).not.toBe(first);
  });

  it("a 202 is shown as grading and the job's end as feedback, with the pending job remembered meanwhile", async () => {
    answers.submit_attempt = { status: 202, body: { ok: true, accepted: { job_id: "j1", request_id: "r", state: "accepted" } } };
    getAnswers["/api/v1/jobs/j1"] = { state: "completed", result: { attemptId: "a1", practiceItemId: "i1" } };
    await beginSession();
    fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
    await screen.findByText("Define it.");
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = "My answer";
    fireEvent.input(editor);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText("3 / 4");
    expect(gets).toContain("/api/v1/jobs/j1");
    expect(localStorage.getItem("learnloop.pendingSubmit")).toBeNull();
  });

  it("the symbol bar adds a command", async () => {
    await beginSession();
    fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
    await screen.findByText("Define it.");
    fireEvent.click(screen.getByRole("button", { name: "\\pi" }));
    expect(screen.getByRole("textbox", { name: "Your answer" }).textContent).toContain("\\pi");
  });

  it("Skip uses the skip's own list instead of building another", async () => {
    answers.skip_practice_item = queue([row("i2")], 2);
    await beginSession();
    const builds = called("get_today_queue").length;
    fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
    await screen.findByText("Define it.");
    fireEvent.click(screen.getByRole("button", { name: "Skip" }));
    await screen.findByText("2 items waiting for the desktop");
    expect(called("skip_practice_item")[0].params).toEqual({ sessionId: "s1", practiceItemId: "i1" });
    expect(called("get_today_queue").length).toBeLessThanOrEqual(builds + 1);
  });
});


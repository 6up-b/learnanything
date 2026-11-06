// Handoff between the phone and the desktop (§6.5)
// Split out of App.test.tsx (mobile v2 V2, V1's carried item): the cases are unchanged.
import {
  act, answers, App, beforeEach, beginSession, cacheSessionId, called, calls, cleanup, describe, expect, fakeFetch, feedback, fireEvent,
  getAnswers, gets, installFakeHost, it, item, listOutbox, PLAN_OFF, queue, rememberPendingSubmit, render, respond, row, saveCredential,
  screen, session, vi, waitFor, type Call, type RpcAnswer
} from "../test/fakeHost";

installFakeHost();

describe("handoff (§6.5)", () => {
  const openElsewhere = {
    status: 409,
    body: {
      ok: false,
      error: {
        code: "session_open_elsewhere", message: "m", retryable: false,
        details: { session_id: "s_desk", owner_label: "desktop", owner_generation: 0, has_draft: true, draft_first_line: "a line" }
      }
    }
  };

  it("a start over the desktop's session asks: Cancel changes nothing", async () => {
    answers.start_session = openElsewhere;
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "15 min" }));
    expect(await screen.findByText(/You have a session open on desktop/)).toBeTruthy();
    expect(screen.getByText(/a line/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    await waitFor(() => expect(screen.queryByText(/You have a session open/)).toBeNull());
    expect(called("adopt_session")).toEqual([]);
  });

  it("Continue it here adopts at the generation it read and resumes its checkpoint", async () => {
    answers.start_session = openElsewhere;
    answers.adopt_session = { session_id: "s_desk" };
    answers.get_session = session({ sessionId: "s_desk", ownerGeneration: 1, checkpoint: { currentPracticeItemId: "i1", currentAnswer: "from the desktop", submissionId: "k1", hintsUsed: 0, focusBlockState: null, pendingGradingProposal: null } });
    getAnswers["/api/v1/submissions/k1"] = { state: "unknown" };
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "15 min" }));
    fireEvent.click(await screen.findByRole("button", { name: "Continue it here" }));
    const editor = await screen.findByRole("textbox", { name: "Your answer" });
    await waitFor(() => expect(editor.textContent).toContain("from the desktop"));
    expect(called("adopt_session")[0].params).toEqual({ sessionId: "s_desk", expectedGeneration: 0 });
  });

  it("adopting a checkpoint whose submission finished shows that feedback", async () => {
    answers.start_session = openElsewhere;
    answers.adopt_session = { session_id: "s_desk" };
    answers.get_session = session({ sessionId: "s_desk", checkpoint: { currentPracticeItemId: "i1", currentAnswer: "x", submissionId: "k1", hintsUsed: 0, focusBlockState: null, pendingGradingProposal: null } });
    getAnswers["/api/v1/submissions/k1"] = { state: "completed", result: { attemptId: "a1" } };
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "15 min" }));
    fireEvent.click(await screen.findByRole("button", { name: "Continue it here" }));
    await screen.findByText("3 / 4");
  });

  it("a draft the phone cannot finish is explained and stays with the desktop", async () => {
    answers.start_session = openElsewhere;
    answers.adopt_session = { status: 409, body: { ok: false, error: { code: "current_item_desktop_only", message: "m", retryable: false } } };
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "15 min" }));
    fireEvent.click(await screen.findByRole("button", { name: "Continue it here" }));
    expect(await screen.findByText(/can only be finished on the desktop/)).toBeTruthy();
  });

  it("Start fresh names the session it replaces", async () => {
    let first = true;
    answers.start_session = () => {
      if (first) {
        first = false;
        return openElsewhere;
      }
      return session();
    };
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "15 min" }));
    fireEvent.click(await screen.findByRole("button", { name: "Start fresh" }));
    await screen.findByRole("button", { name: /^Next: Topic i1/ });
    expect(called("start_session")[1].params).toEqual({ availableMinutes: 15, replace: "s_desk" });
  });

  it("session_moved on a write freezes the question and offers it back", async () => {
    const moved = { status: 409, body: { ok: false, error: { code: "session_moved", message: "This session continued on desktop.", retryable: false, details: { session_id: "s1", owner_label: "desktop", owner_generation: 2 } } } };
    answers.submit_attempt = moved;
    answers.adopt_session = { session_id: "s1" };
    await beginSession();
    fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
    await screen.findByText("Define it.");
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = "x";
    fireEvent.input(editor);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    expect(await screen.findByText("This session continued on desktop.")).toBeTruthy();
    expect((screen.getByRole("button", { name: /Try again|Submit/ }) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Take it back" }));
    await waitFor(() => expect(called("adopt_session")[0]?.params).toEqual({ sessionId: "s1", expectedGeneration: 2 }));
  });

  it("opening the app on a session the desktop took back says so, and does not write", async () => {
    cacheSessionId("s1");
    answers.get_session = session({ ownerDeviceId: null, ownerLabel: "desktop", ownerGeneration: 3 });
    render(<App />);
    expect(await screen.findByText("This session continued on desktop.")).toBeTruthy();
    expect(called("save_practice_draft")).toEqual([]);
  });
});


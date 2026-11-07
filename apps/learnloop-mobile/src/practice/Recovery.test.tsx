// Coming back (A4), and a question through what can go wrong (Codex review of M2a, F1-F11)
// Split out of App.test.tsx (mobile v2 V2, V1's carried item): the cases are unchanged.
import {
  act, answers, App, beforeEach, beginSession, cacheSessionId, called, calls, cleanup, describe, expect, fakeFetch, feedback, fireEvent,
  getAnswers, gets, installFakeHost, it, item, listOutbox, PLAN_OFF, queue, rememberPendingSubmit, render, respond, row, saveCredential,
  screen, session, vi, waitFor, type Call, type RpcAnswer
} from "../test/fakeHost";

installFakeHost();

describe("coming back (A4)", () => {
  it("a submit left mid-grade finds its feedback on return", async () => {
    cacheSessionId("s1");
    rememberPendingSubmit({ jobId: "j9", submissionId: "k9", sessionId: "s1", practiceItemId: "i1" });
    getAnswers["/api/v1/jobs/j9"] = { state: "completed", result: { attemptId: "a1", practiceItemId: "i1" } };
    render(<App />);
    await screen.findByText("3 / 4");
    expect(called("acknowledge_practice_submission")[0].params.submissionId).toBe("k9");
    expect(localStorage.getItem("learnloop.pendingSubmit")).toBeNull();
    expect(called("submit_attempt")).toEqual([]);
  });

  it("a saved draft reopens on its question, under its key", async () => {
    cacheSessionId("s1");
    answers.get_session = session({ checkpoint: { currentPracticeItemId: "i1", currentAnswer: "half an answer", submissionId: "k1", hintsUsed: 0, focusBlockState: null, pendingGradingProposal: null } });
    getAnswers["/api/v1/submissions/k1"] = { state: "unknown" };
    render(<App />);
    const editor = await screen.findByRole("textbox", { name: "Your answer" });
    await waitFor(() => expect(editor.textContent).toContain("half an answer"));
  });

  it("an ended session is forgotten", async () => {
    cacheSessionId("s1");
    answers.get_session = session({ endedAt: "t2" });
    render(<App />);
    expect(await screen.findByRole("button", { name: "15 min" })).toBeTruthy();
    expect(localStorage.getItem("learnloop.session")).toBeNull();
  });
});

describe("a question through what can go wrong (Codex review of M2a)", () => {
  const checkpoint = (extra: Record<string, unknown> = {}) => ({
    currentPracticeItemId: "i1", currentAnswer: "from the desktop", submissionId: "k1", hintsUsed: 0, focusBlockState: null, pendingGradingProposal: null, ...extra
  });
  const NOT_OURS = { status: 500, body: "not json we know" };
  const GRADING_FAILED = { status: 409, body: { ok: false, error: { code: "grading_fallback_required", message: "m", retryable: true } } };
  const MOVED = { status: 409, body: { ok: false, error: { code: "session_moved", message: "This session continued on desktop.", retryable: false, details: { session_id: "s1", owner_label: "desktop", owner_generation: 2 } } } };

  async function openAndType(text = "My answer") {
    await beginSession();
    fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
    await screen.findByText("Define it.");
    return typeInto(text);
  }

  function typeInto(text: string) {
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = text;
    fireEvent.input(editor);
    return editor;
  }

  async function adoptAtStart(snapshot: Record<string, unknown>) {
    answers.start_session = { status: 409, body: { ok: false, error: { code: "session_open_elsewhere", message: "m", retryable: false, details: { session_id: "s1", owner_label: "desktop", owner_generation: 0, has_draft: true } } } };
    answers.adopt_session = { session_id: "s1" };
    answers.get_session = session(snapshot);
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "15 min" }));
    fireEvent.click(await screen.findByRole("button", { name: "Continue it here" }));
    return screen.findByRole("textbox", { name: "Your answer" });
  }

  describe("F1: a draft adopted with help keeps it", () => {
    it("saves and submits the count, by the desktop's rule, and so an assisted type", async () => {
      answers.get_practice_item = { ...item(), attemptTypesAllowed: ["independent_attempt", "hinted_attempt"] };
      getAnswers["/api/v1/submissions/k1"] = { state: "unknown" };
      await adoptAtStart({
        ownerGeneration: 1,
        checkpoint: checkpoint({ hintsUsed: 1, pageSeen: true, hintSeen: true, firstHintProgress: "draft_started", planPresentationId: "pres1" })
      });
      await screen.findByText("Define it.");
      typeInto("from the desktop, and more");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      expect(called("save_practice_draft")[0].params).toMatchObject({
        submissionId: "k1", hintsUsed: 1, pageSeen: true, hintSeen: true, firstHintProgress: "draft_started", planPresentationId: "pres1"
      });
      expect(called("submit_attempt")[0].params).toMatchObject({
        submissionId: "k1", attemptType: "hinted_attempt", hintsUsed: 2, authoredHints: 1, bookCounted: true,
        firstHintProgress: "draft_started", planPresentationId: "pres1"
      });
    });

    it("the count stays on an item that allows no assisted type", async () => {
      getAnswers["/api/v1/submissions/k1"] = { state: "unknown" };
      await adoptAtStart({ ownerGeneration: 1, checkpoint: checkpoint({ hintsUsed: 2 }) });
      await screen.findByText("Define it.");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      expect(called("submit_attempt")[0].params).toMatchObject({ attemptType: "independent_attempt", hintsUsed: 2, authoredHints: 2, bookCounted: false });
    });

    it("help with no answer yet still opens the question, and a new key keeps what is under the old one", async () => {
      getAnswers["/api/v1/submissions/k1"] = { state: "failed", error: { code: "item_retired", message: "m", retryable: false } };
      await adoptAtStart({ ownerGeneration: 1, checkpoint: checkpoint({ currentAnswer: "", hintsUsed: 1, pageSeen: true }) });
      await screen.findByText("Define it.");
      typeInto("an answer");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      const submit = called("submit_attempt")[0].params;
      expect(submit.submissionId).not.toBe("k1");
      expect(submit).toMatchObject({ hintsUsed: 2, authoredHints: 1, bookCounted: true });
      expect(called("save_practice_draft").at(-1)?.params).toMatchObject({ submissionId: submit.submissionId, hintsUsed: 1, pageSeen: true });
    });
  });

  describe("F2: a lost response is not a failed submit", () => {
    async function submitLost() {
      answers.submit_attempt = NOT_OURS;
      const editor = await openAndType();
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText(/answered with something unexpected/);
      expect(called("submit_attempt")).toHaveLength(1);
      answers.submit_attempt = { attemptId: "a2", practiceItemId: "i1" };
      return { editor, key: String(called("submit_attempt")[0].params.submissionId) };
    }

    it("an edit after it finds the job still running and waits for it, with no second submit", async () => {
      const { key } = await submitLost();
      getAnswers[`/api/v1/submissions/${key}`] = { state: "running" };
      typeInto("Something else");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText(/being graded/);
      expect(called("submit_attempt")).toHaveLength(1);
      getAnswers[`/api/v1/submissions/${key}`] = { state: "completed", result: { attemptId: "a1", practiceItemId: "i1" } };
      await screen.findByText("3 / 4", undefined, { timeout: 4000 });
      expect(called("submit_attempt")).toHaveLength(1);
      expect(called("acknowledge_practice_submission")[0].params.submissionId).toBe(key);
      expect(localStorage.getItem("learnloop.questionDrafts")).toBe("{}");
    });

    it("an attempt already recorded opens its feedback, and what was typed since is not saved over it", async () => {
      const { key } = await submitLost();
      getAnswers[`/api/v1/submissions/${key}`] = { state: "completed", result: { attemptId: "a1", practiceItemId: "i1" } };
      typeInto("Something else");
      const saves = called("save_practice_draft").length;
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      expect(called("submit_attempt")).toHaveLength(1);
      expect(called("save_practice_draft")).toHaveLength(saves);
    });

    it("the host never got it: the same request again, or the edit under the same key", async () => {
      const { key } = await submitLost();
      getAnswers[`/api/v1/submissions/${key}`] = { state: "unknown" };
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      expect(called("submit_attempt")[1].params).toEqual(called("submit_attempt")[0].params);
    });

    it("the host never got it and the answer changed: a new request, the same key", async () => {
      const { key } = await submitLost();
      getAnswers[`/api/v1/submissions/${key}`] = { state: "unknown" };
      typeInto("Something else");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      expect(called("submit_attempt")[1].params).toMatchObject({ submissionId: key, answerMd: "Something else" });
    });

    it("its job failed and the answer changed: only then a new key", async () => {
      const { key } = await submitLost();
      getAnswers[`/api/v1/submissions/${key}`] = { state: "failed", error: { code: "grading_fallback_required", message: "m", retryable: true } };
      typeInto("Something else");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      expect(called("submit_attempt")[1].params.submissionId).not.toBe(key);
      expect(called("save_practice_draft").at(-1)?.params).toMatchObject({ submissionId: called("submit_attempt")[1].params.submissionId, answerMd: "Something else" });
    });

    it("no answer from the status either: nothing is sent", async () => {
      const { key } = await submitLost();
      const realFetch = globalThis.fetch;
      vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) =>
        String(input) === `/api/v1/submissions/${key}` ? Promise.reject(new TypeError("gone")) : realFetch(input, init)));
      typeInto("Something else");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("The desktop isn't reachable.");
      expect(called("submit_attempt")).toHaveLength(1);
      expect(screen.getByRole("textbox", { name: "Your answer" }).textContent).toContain("Something else");
    });

    it("the transport's own failure, after its retries", async () => {
      answers.submit_attempt = { status: 502, body: {} };
      await openAndType();
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("The desktop isn't reachable.", undefined, { timeout: 6000 });
      const key = String(called("submit_attempt")[0].params.submissionId);
      getAnswers[`/api/v1/submissions/${key}`] = { state: "running" };
      const sent = called("submit_attempt").length;
      fireEvent.click(screen.getByRole("button", { name: "Try again" }));
      await screen.findByText(/being graded/);
      expect(called("submit_attempt")).toHaveLength(sent);
    }, 10000);

    it("the request is on the phone before it is sent", async () => {
      let stored: string | null = null;
      answers.submit_attempt = () => {
        stored = localStorage.getItem("learnloop.questionDrafts");
        return { attemptId: "a1", practiceItemId: "i1" };
      };
      await openAndType();
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      const held = Object.values(JSON.parse(stored ?? "{}")) as Array<{ sentInput: Record<string, unknown>; outcome: string }>;
      expect(held[0].sentInput).toEqual(called("submit_attempt")[0].params);
      expect(held[0].outcome).toBe("unknown");
    });
  });

  describe("F2, re-review: only the host's status frees a key", () => {
    const typed = (status: number, code: string, retryable = false, details: Record<string, unknown> = {}) =>
      ({ status, body: { ok: false, error: { code, message: `said ${code}`, retryable, details } } });
    const statusOf = (key: string) => `/api/v1/submissions/${key}`;
    const asked = (key: string) => gets.filter((url) => url === statusOf(key)).length;

    /** The first submit ends in `answer`, and from here the host would take another. */
    async function submitRefused(answer: unknown, shown: RegExp, timeout = 1000) {
      answers.submit_attempt = answer;
      await openAndType();
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText(shown, undefined, { timeout });
      const sent = called("submit_attempt").length;
      answers.submit_attempt = { attemptId: "a2", practiceItemId: "i1" };
      return { key: String(called("submit_attempt")[0].params.submissionId), sent };
    }

    it("an accepted submit whose response was lost and whose retries met host_busy: an edit waits for the job", async () => {
      const { key, sent } = await submitRefused(typed(503, "host_busy", true), /said host_busy/, 6000);
      expect(sent).toBe(4);
      expect(new Set(called("submit_attempt").map((call) => call.params.submissionId)).size).toBe(1);
      getAnswers[statusOf(key)] = { state: "running" };
      typeInto("Something else");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText(/being graded/);
      expect(asked(key)).toBeGreaterThan(0);
      expect(called("submit_attempt")).toHaveLength(sent);
    }, 10000);

    it("the same, when the job has finished: its attempt opens, and no second one", async () => {
      const { key, sent } = await submitRefused(typed(503, "host_busy", true), /said host_busy/, 6000);
      getAnswers[statusOf(key)] = { state: "completed", result: { attemptId: "a1", practiceItemId: "i1" } };
      typeInto("Something else");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      expect(called("get_feedback")[0].params.attemptId).toBe("a1");
      expect(called("submit_attempt")).toHaveLength(sent);
    }, 10000);

    it.each([
      ["validation_error", 400],
      ["database_locked", 409],
      ["session_ended", 409],
      ["not_found", 404],
      ["submission_committed", 409]
    ])("%s says nothing of the job either", async (code, status) => {
      const { key } = await submitRefused(typed(status, code), new RegExp(`said ${code}`));
      getAnswers[statusOf(key)] = { state: "running" };
      typeInto("Something else");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText(/being graded/);
      expect(asked(key)).toBeGreaterThan(0);
      expect(called("submit_attempt")).toHaveLength(1);
    });

    it("a typed error the host never took a job for: the edit keeps the key", async () => {
      const { key } = await submitRefused(typed(400, "validation_error"), /said validation_error/);
      getAnswers[statusOf(key)] = { state: "unknown" };
      typeInto("Something else");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      expect(called("submit_attempt")[1].params).toMatchObject({ submissionId: key, answerMd: "Something else" });
    });

    it("a grading outage in the response is read back before an edit takes a new key", async () => {
      const { key } = await submitRefused(GRADING_FAILED, /AI grading is unavailable/);
      getAnswers[statusOf(key)] = { state: "failed", error: { code: "grading_fallback_required", message: "m", retryable: true } };
      typeInto("Something else");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      expect(asked(key)).toBe(1);
      expect(called("submit_attempt")[1].params.submissionId).not.toBe(key);
    });

    describe("submission_conflict: the key is another request's", () => {
      const CONFLICT = typed(409, "submission_conflict");

      it("that request still running is waited for", async () => {
        const { key } = await submitRefused(CONFLICT, /said submission_conflict/);
        getAnswers[statusOf(key)] = { state: "running" };
        typeInto("Something else");
        fireEvent.click(screen.getByRole("button", { name: "Submit" }));
        await screen.findByText(/being graded/);
        expect(called("submit_attempt")).toHaveLength(1);
      });

      it("that request finished: its attempt opens", async () => {
        const { key } = await submitRefused(CONFLICT, /said submission_conflict/);
        getAnswers[statusOf(key)] = { state: "completed", result: { attemptId: "a1", practiceItemId: "i1" } };
        fireEvent.click(screen.getByRole("button", { name: "Submit" }));
        await screen.findByText("3 / 4");
        expect(called("submit_attempt")).toHaveLength(1);
      });

      it("that request failed: a new key, even for the same answer, since the same key would only conflict again", async () => {
        const { key } = await submitRefused(CONFLICT, /said submission_conflict/);
        getAnswers[statusOf(key)] = { state: "failed", error: { code: "grading_fallback_required", message: "m", retryable: true } };
        fireEvent.click(screen.getByRole("button", { name: "Submit" }));
        await screen.findByText("3 / 4");
        expect(asked(key)).toBe(1);
        expect(called("submit_attempt")[1].params.submissionId).not.toBe(key);
        expect(called("submit_attempt")[1].params.answerMd).toBe("My answer");
      });
    });

    it("a status read that is itself refused sends nothing, under either key", async () => {
      const { key } = await submitRefused(typed(503, "host_busy", true), /said host_busy/, 6000);
      const sent = called("submit_attempt").length;
      const realFetch = globalThis.fetch;
      vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) =>
        String(input) === statusOf(key)
          ? Promise.resolve(new Response(JSON.stringify(typed(503, "host_busy", true).body), { status: 503 }))
          : realFetch(input, init)));
      typeInto("Something else");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText(/said host_busy/);
      expect(called("submit_attempt")).toHaveLength(sent);
      expect(screen.getByRole("textbox", { name: "Your answer" }).textContent).toContain("Something else");
    }, 10000);

    describe("a skip after a submit nothing has settled", () => {
      async function refusedThenSkip(state: unknown) {
        answers.skip_practice_item = queue([row("i2")]);
        const { key } = await submitRefused(typed(400, "validation_error"), /said validation_error/);
        if (state) getAnswers[statusOf(key)] = state;
        fireEvent.click(screen.getByRole("button", { name: "Skip" }));
        return key;
      }

      it("a job still running is waited for, and nothing is skipped", async () => {
        await refusedThenSkip({ state: "running" });
        await screen.findByText(/being graded/);
        expect(called("skip_practice_item")).toEqual([]);
      });

      it("a recorded attempt opens, and nothing is skipped", async () => {
        await refusedThenSkip({ state: "completed", result: { attemptId: "a1", practiceItemId: "i1" } });
        await screen.findByText("3 / 4");
        expect(called("skip_practice_item")).toEqual([]);
      });

      it("a job the host never took: the skip goes through", async () => {
        await refusedThenSkip({ state: "unknown" });
        await screen.findByRole("button", { name: /^Next: Topic i2/ });
        expect(called("skip_practice_item")).toHaveLength(1);
      });

      it("a status it cannot read: no skip, and the question stays", async () => {
        await refusedThenSkip(null);
        await screen.findByText("no fake");
        expect(called("skip_practice_item")).toEqual([]);
        await waitFor(() => expect((screen.getByRole("button", { name: "Skip" }) as HTMLButtonElement).disabled).toBe(false));
      });
    });

    it("a reopened app holds the question as unsettled too", async () => {
      const { key } = await submitRefused(typed(400, "validation_error"), /said validation_error/);
      const held = Object.values(JSON.parse(localStorage.getItem("learnloop.questionDrafts") ?? "{}")) as Array<{ outcome: string; submissionId: string }>;
      expect(held[0]).toMatchObject({ outcome: "unknown", submissionId: key });
    });
  });

  describe("F2, final: the host's status says what committed (R2)", () => {
    const statusOf = (key: string) => `/api/v1/submissions/${key}`;
    const RECORDED = (attempt = "a1") => ({
      state: "recorded", attempt_id: attempt,
      error: { code: "submission_committed", message: "Your answer is recorded. Its feedback is delayed.", retryable: false, details: { attempt_id: attempt } }
    });
    const keysSent = () => new Set(called("submit_attempt").map((call) => call.params.submissionId));
    const accepted = (jobId: string, key: string) =>
      ({ status: 202, body: { ok: true, accepted: { job_id: jobId, request_id: key, state: "running" } } });

    async function lostSubmit() {
      answers.submit_attempt = NOT_OURS;
      await openAndType();
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText(/answered with something unexpected/);
      answers.submit_attempt = { attemptId: "a2", practiceItemId: "i1" };
      return String(called("submit_attempt")[0].params.submissionId);
    }

    it("a job whose completion stopped reads running, then its feedback, under one key", async () => {
      answers.submit_attempt = (call: Call) => accepted("j1", String(call.requestId));
      getAnswers["/api/v1/jobs/j1"] = { job_id: "j1", state: "running" };
      await openAndType();
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await waitFor(() => expect(gets).toContain("/api/v1/jobs/j1"));
      getAnswers["/api/v1/jobs/j1"] = { job_id: "j1", state: "completed", result: { attemptId: "a1", practiceItemId: "i1" } };
      await screen.findByText("3 / 4", undefined, { timeout: 4000 });
      expect(called("submit_attempt")).toHaveLength(1);
      expect(keysSent().size).toBe(1);
    });

    it("a job that can't finish opens its feedback and acknowledges, with no second submit", async () => {
      answers.submit_attempt = (call: Call) => accepted("j1", String(call.requestId));
      getAnswers["/api/v1/jobs/j1"] = { job_id: "j1", ...RECORDED() };
      await openAndType();
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      expect(called("get_feedback")[0].params.attemptId).toBe("a1");
      expect(called("submit_attempt")).toHaveLength(1);
      expect(called("acknowledge_practice_submission")).toHaveLength(1);
      expect(localStorage.getItem("learnloop.questionDrafts")).toBe("{}");
    });

    it("an edit after a lost response reads recorded: its feedback, and never a new key", async () => {
      const key = await lostSubmit();
      getAnswers[statusOf(key)] = RECORDED();
      typeInto("Something else");
      const saves = called("save_practice_draft").length;
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      expect(called("submit_attempt")).toHaveLength(1);
      expect(called("save_practice_draft")).toHaveLength(saves);
      expect(called("acknowledge_practice_submission")[0].params.submissionId).toBe(key);
    });

    it("the /rpc answer for a recorded key opens the same feedback", async () => {
      answers.submit_attempt = { status: 409, body: { ok: false, error: { code: "submission_committed", message: "m", retryable: false, details: { attempt_id: "a1" } } } };
      await openAndType();
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      expect(called("get_feedback")[0].params.attemptId).toBe("a1");
      expect(called("acknowledge_practice_submission")).toHaveLength(1);
    });

    it("a skip over a recorded key opens the feedback and skips nothing", async () => {
      const key = await lostSubmit();
      answers.skip_practice_item = queue([row("i2")]);
      getAnswers[statusOf(key)] = RECORDED();
      fireEvent.click(screen.getByRole("button", { name: "Skip" }));
      await screen.findByText("3 / 4");
      expect(called("skip_practice_item")).toEqual([]);
    });

    it("a reopened app waiting on a job that comes back recorded opens the feedback", async () => {
      cacheSessionId("s1");
      rememberPendingSubmit({ jobId: "j9", submissionId: "k9", sessionId: "s1", practiceItemId: "i1" });
      getAnswers["/api/v1/jobs/j9"] = { job_id: "j9", ...RECORDED() };
      render(<App />);
      await screen.findByText("3 / 4");
      expect(called("acknowledge_practice_submission")[0].params.submissionId).toBe("k9");
      expect(called("submit_attempt")).toEqual([]);
    });

    it("a reopened app reading the checkpoint's recorded key opens the feedback", async () => {
      cacheSessionId("s1");
      answers.get_session = session({ checkpoint: { currentPracticeItemId: "i1", currentAnswer: "Draft", submissionId: "k9" } });
      getAnswers[statusOf("k9")] = RECORDED();
      render(<App />);
      await screen.findByText("3 / 4");
      expect(called("submit_attempt")).toEqual([]);
      expect(screen.queryByRole("textbox")).toBeNull();
    });

    it("waiting on a key with no job here ends at recorded too", async () => {
      const key = await lostSubmit();
      getAnswers[statusOf(key)] = { state: "running" };
      typeInto("Something else");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText(/being graded/);
      getAnswers[statusOf(key)] = RECORDED();
      await screen.findByText("3 / 4", undefined, { timeout: 4000 });
      expect(called("submit_attempt")).toHaveLength(1);
    });
  });

  describe("F3: a reopened app retries the same request", () => {
    it("resends the first request's fields, candidate and latency included, under its key", async () => {
      answers.submit_attempt = GRADING_FAILED;
      const now = vi.spyOn(Date, "now");
      now.mockReturnValue(1_000_000);
      const first = render(<App />);
      fireEvent.click(await screen.findByRole("button", { name: "15 min" }));
      fireEvent.click(await screen.findByRole("button", { name: /^Next: Topic i1/ }));
      await screen.findByText("Define it.");
      typeInto("My answer");
      now.mockReturnValue(1_042_000);
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText(/AI grading is unavailable/);
      const sent = called("submit_attempt")[0].params;
      expect(sent).toMatchObject({ latencySeconds: 42, schedulerCandidateId: "cand_i1" });
      first.unmount();
      const key = String(sent.submissionId);
      answers.get_session = session({ checkpoint: checkpoint({ currentAnswer: "My answer", submissionId: key }) });
      getAnswers[`/api/v1/submissions/${key}`] = { state: "failed", error: { code: "grading_fallback_required", message: "m", retryable: true } };
      answers.submit_attempt = { attemptId: "a1", practiceItemId: "i1" };
      now.mockReturnValue(1_100_000);
      render(<App />);
      await screen.findByText("Define it.");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      now.mockRestore();
      expect(called("submit_attempt")[1].params).toEqual(sent);
    });

    it("with its copy gone a failed key is not reused for a request it would conflict with", async () => {
      cacheSessionId("s1");
      answers.get_session = session({ checkpoint: checkpoint({ currentAnswer: "half" }) });
      getAnswers["/api/v1/submissions/k1"] = { state: "failed", error: { code: "grading_fallback_required", message: "m", retryable: true } };
      render(<App />);
      await screen.findByText("Define it.");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      expect(called("submit_attempt")[0].params.submissionId).not.toBe("k1");
    });
  });

  describe("F4: taking a session back", () => {
    it("remounts the question on the checkpoint it read, on the same item, with no write from the old one", async () => {
      answers.submit_attempt = MOVED;
      answers.adopt_session = { session_id: "s1" };
      const editor = await openAndType("The phone's old draft");
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("This session continued on desktop.");
      const saves = called("save_practice_draft").length;
      answers.get_session = session({ ownerGeneration: 3, checkpoint: checkpoint({ currentAnswer: "the desktop's newer draft", submissionId: "k_desk", hintsUsed: 1 }) });
      getAnswers["/api/v1/submissions/k_desk"] = { state: "unknown" };
      answers.submit_attempt = { attemptId: "a1", practiceItemId: "i1" };
      fireEvent.click(screen.getByRole("button", { name: "Take it back" }));
      await screen.findByText(/the desktop's newer draft/);
      expect(screen.getByRole("textbox", { name: "Your answer" })).not.toBe(editor);
      expect(screen.getByRole("textbox", { name: "Your answer" }).textContent).not.toContain("The phone's old draft");
      expect(called("save_practice_draft")).toHaveLength(saves);
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      expect(called("submit_attempt").at(-1)?.params).toMatchObject({ submissionId: "k_desk", answerMd: "the desktop's newer draft", hintsUsed: 1 });
    });
  });

  describe("F5: ordinary navigation keeps the draft", () => {
    it("a visit to Capture leaves the open question as it was, with no second serve", async () => {
      await openAndType("Half an answer");
      const serves = called("get_practice_item").length;
      fireEvent.click(screen.getByRole("button", { name: "Capture" }));
      expect(await screen.findByLabelText("A thought, a problem or a link")).toBeTruthy();
      expect(screen.queryByRole("textbox", { name: "Your answer" })).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: "Today" }));
      expect(screen.getByRole("textbox", { name: "Your answer" }).textContent).toContain("Half an answer");
      expect(called("get_practice_item")).toHaveLength(serves);
    });

    it("Back saves at once, and reopening restores the answer and its key", async () => {
      await openAndType("Half an answer");
      expect(called("save_practice_draft")).toEqual([]);
      fireEvent.click(screen.getByRole("button", { name: "Back" }));
      await waitFor(() => expect(called("save_practice_draft")).toHaveLength(1));
      const saved = called("save_practice_draft")[0].params;
      expect(saved.answerMd).toBe("Half an answer");
      fireEvent.click(await screen.findByRole("button", { name: /^Next: Topic i1/ }));
      const editor = await screen.findByRole("textbox", { name: "Your answer" });
      await waitFor(() => expect(editor.textContent).toContain("Half an answer"));
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      expect(called("submit_attempt")[0].params).toMatchObject({ submissionId: saved.submissionId, answerMd: "Half an answer" });
    });

    it("a save that fails on the way out is kept on the phone and sent again", async () => {
      answers.save_practice_draft = { status: 409, body: { ok: false, error: { code: "database_locked", message: "Try again.", retryable: false } } };
      await openAndType("Half an answer");
      fireEvent.click(screen.getByRole("button", { name: "Back" }));
      await waitFor(() => expect(called("save_practice_draft")).toHaveLength(1));
      answers.save_practice_draft = { ok: true };
      fireEvent.click(await screen.findByRole("button", { name: /^Next: Topic i1/ }));
      const editor = await screen.findByRole("textbox", { name: "Your answer" });
      await waitFor(() => expect(editor.textContent).toContain("Half an answer"));
      await waitFor(() => expect(called("save_practice_draft")).toHaveLength(2), { timeout: 2000 });
      expect(called("save_practice_draft")[1].params.answerMd).toBe("Half an answer");
    });

    it("with no copy on the phone, reopening reads the checkpoint", async () => {
      await beginSession();
      answers.get_session = session({ checkpoint: checkpoint({ currentAnswer: "saved on the host", hintsUsed: 1 }) });
      getAnswers["/api/v1/submissions/k1"] = { state: "unknown" };
      fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
      const editor = await screen.findByRole("textbox", { name: "Your answer" });
      await waitFor(() => expect(editor.textContent).toContain("saved on the host"));
      fireEvent.click(screen.getByRole("button", { name: "Submit" }));
      await screen.findByText("3 / 4");
      expect(called("submit_attempt")[0].params).toMatchObject({ submissionId: "k1", authoredHints: 1, schedulerCandidateId: "cand_i1" });
    });

    it("another item's checkpoint opens this one blank", async () => {
      await beginSession();
      answers.get_session = session({ checkpoint: checkpoint({ currentPracticeItemId: "i2", currentAnswer: "the other one" }) });
      fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
      const editor = await screen.findByRole("textbox", { name: "Your answer" });
      expect(editor.textContent).not.toContain("the other one");
    });

    it("a skip ends the draft: no flush on the way out, nothing to restore", async () => {
      answers.skip_practice_item = queue([row("i1"), row("i2")]);
      await openAndType("Half an answer");
      fireEvent.click(screen.getByRole("button", { name: "Skip" }));
      await screen.findByRole("button", { name: /^Next: Topic i1/ });
      expect(called("save_practice_draft")).toEqual([]);
      fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
      const editor = await screen.findByRole("textbox", { name: "Your answer" });
      expect(editor.textContent).not.toContain("Half an answer");
    });

    it("a job that ends in a grading outage while waiting says what the phone can do", async () => {
      cacheSessionId("s1");
      rememberPendingSubmit({ jobId: "j9", submissionId: "k9", sessionId: "s1", practiceItemId: "i1" });
      getAnswers["/api/v1/jobs/j9"] = { state: "failed", error: { code: "grading_fallback_required", message: "Grade your answer to continue.", retryable: true } };
      render(<App />);
      expect(await screen.findByText(/AI grading is unavailable/)).toBeTruthy();
      expect(screen.queryByText(/Grade your answer/)).toBeNull();
    });
  });

  describe("F10: a skip that fails leaves the draft unsaved no longer", () => {
    const SKIP_REFUSED = { status: 409, body: { ok: false, error: { code: "database_locked", message: "Could not skip this.", retryable: false } } };

    it("the answer typed just before it reaches the checkpoint, and stays on screen", async () => {
      answers.skip_practice_item = SKIP_REFUSED;
      await openAndType("Half an answer");
      fireEvent.click(screen.getByRole("button", { name: "Skip" }));
      await screen.findByText("Could not skip this.");
      await waitFor(() => expect(called("save_practice_draft")).toHaveLength(1));
      expect(called("save_practice_draft")[0].params.answerMd).toBe("Half an answer");
      expect(screen.getByRole("textbox", { name: "Your answer" }).textContent).toContain("Half an answer");
      expect((screen.getByRole("button", { name: "Skip" }) as HTMLButtonElement).disabled).toBe(false);
    });

    it("once: leaving afterwards has nothing more to save", async () => {
      answers.skip_practice_item = SKIP_REFUSED;
      await openAndType("Half an answer");
      fireEvent.click(screen.getByRole("button", { name: "Skip" }));
      await waitFor(() => expect(called("save_practice_draft")).toHaveLength(1));
      fireEvent.click(screen.getByRole("button", { name: "Back" }));
      await screen.findByRole("button", { name: /^Next: Topic i1/ });
      expect(called("save_practice_draft")).toHaveLength(1);
    });

    it("if that save fails too, leaving sends it", async () => {
      answers.skip_practice_item = SKIP_REFUSED;
      answers.save_practice_draft = { status: 409, body: { ok: false, error: { code: "database_locked", message: "Try again.", retryable: false } } };
      await openAndType("Half an answer");
      fireEvent.click(screen.getByRole("button", { name: "Skip" }));
      await waitFor(() => expect(called("save_practice_draft")).toHaveLength(1));
      answers.save_practice_draft = { ok: true };
      fireEvent.click(screen.getByRole("button", { name: "Back" }));
      await waitFor(() => expect(called("save_practice_draft")).toHaveLength(2));
      expect(called("save_practice_draft")[1].params.answerMd).toBe("Half an answer");
    });

    it("while a skip is in flight nothing saves, and a skip that succeeds puts nothing back", async () => {
      let release = () => undefined as void;
      const held = new Promise<void>((resolve) => { release = resolve; });
      const realFetch = globalThis.fetch;
      let skips = 0;
      vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        if (String(input) === "/rpc" && JSON.parse(init?.body as string).method === "skip_practice_item") {
          skips += 1;
          await held;
          return new Response(JSON.stringify({ ok: true, result: queue([row("i2")]) }), { status: 200 });
        }
        return realFetch(input, init);
      }));
      await openAndType("Half an answer");
      fireEvent.click(screen.getByRole("button", { name: "Skip" }));
      await waitFor(() => expect((screen.getByRole("button", { name: "Submit" }) as HTMLButtonElement).disabled).toBe(true));
      fireEvent.click(screen.getByRole("button", { name: "Skip" }));
      // Past the draft's debounce.
      await act(async () => { await new Promise((resolve) => setTimeout(resolve, 1000)); });
      expect(called("save_practice_draft")).toEqual([]);
      expect(skips).toBe(1);
      release();
      await screen.findByRole("button", { name: /^Next: Topic i2/ });
      await act(async () => { await new Promise((resolve) => setTimeout(resolve, 20)); });
      expect(called("save_practice_draft")).toEqual([]);
    });
  });

  describe("F11: a skip has three outcomes", () => {
    const HELD = (answer = "Half an answer") => session({ checkpoint: { currentPracticeItemId: "i1", currentAnswer: answer, submissionId: "k9" } });
    const READ_REFUSED = { status: 409, body: { ok: false, error: { code: "database_locked", message: "Can't read it now.", retryable: false } } };
    const settle = () => act(async () => { await new Promise((resolve) => setTimeout(resolve, 1000)); });
    const heldCopy = () => Object.values(JSON.parse(localStorage.getItem("learnloop.questionDrafts") ?? "{}")) as Array<{ answer: string; outcome: string; skipRevision?: number | null }>;

    /** The skip goes out, the host may or may not have done it, and its reply never comes. */
    async function lostSkip(read: unknown = session()) {
      answers.skip_practice_item = NOT_OURS;
      const editor = await openAndType("Half an answer");
      answers.get_session = read;
      fireEvent.click(screen.getByRole("button", { name: "Skip" }));
      await waitFor(() => expect(called("skip_practice_item")).toHaveLength(1));
      return editor;
    }

    it("it landed: no save, the copy is dropped, and Today is next", async () => {
      await lostSkip(session());
      await screen.findByRole("button", { name: /^Next: Topic i1/ });
      await settle();
      expect(called("save_practice_draft")).toEqual([]);
      expect(called("skip_practice_item")).toHaveLength(1);
      expect(heldCopy()).toEqual([]);
    });

    it("the checkpoint moved on to another item: it landed too", async () => {
      await lostSkip(session({ checkpoint: { currentPracticeItemId: "i2", currentAnswer: "other", submissionId: "k8" } }));
      await screen.findByRole("button", { name: /^Next: Topic i1/ });
      await settle();
      expect(called("save_practice_draft")).toEqual([]);
    });

    it("the same when the transport itself failed", async () => {
      const realFetch = globalThis.fetch;
      vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        if (String(input) === "/rpc" && JSON.parse(init?.body as string).method === "skip_practice_item") {
          calls.push({ method: "skip_practice_item", params: {} });
          throw new TypeError("connection lost");
        }
        return realFetch(input, init);
      }));
      await openAndType("Half an answer");
      fireEvent.click(screen.getByRole("button", { name: "Skip" }));
      await screen.findByRole("button", { name: /^Next: Topic i1/ });
      await settle();
      expect(called("save_practice_draft")).toEqual([]);
    });

    it("the host's own internal error says nothing of it either", async () => {
      answers.skip_practice_item = { status: 500, body: { ok: false, error: { code: "internal", message: "Stopped.", retryable: false } } };
      await openAndType("Half an answer");
      fireEvent.click(screen.getByRole("button", { name: "Skip" }));
      await screen.findByRole("button", { name: /^Next: Topic i1/ });
      await settle();
      expect(called("save_practice_draft")).toEqual([]);
    });

    it("the checkpoint still holds this item's draft: it didn't land, and the save goes ahead, once", async () => {
      const editor = await lostSkip(HELD());
      await waitFor(() => expect(called("save_practice_draft")).toHaveLength(1));
      expect(called("save_practice_draft")[0].params.answerMd).toBe("Half an answer");
      expect(editor.textContent).toContain("Half an answer");
      expect(await screen.findByText(/skip didn't reach the desktop/)).toBeTruthy();
      expect((screen.getByRole("button", { name: "Skip" }) as HTMLButtonElement).disabled).toBe(false);
      await settle();
      expect(called("save_practice_draft")).toHaveLength(1);
      expect(heldCopy()[0].skipRevision ?? null).toBeNull();
    });

    describe("and the read fails too", () => {
      it("says the desktop can't be reached, stays, keeps the copy and writes nothing", async () => {
        const editor = await lostSkip(READ_REFUSED);
        expect(await screen.findByText(/desktop can't be reached/)).toBeTruthy();
        expect(editor.textContent).toContain("Half an answer");
        await waitFor(() => expect((screen.getByRole("button", { name: "Skip" }) as HTMLButtonElement).disabled).toBe(false));
        await settle();
        expect(called("save_practice_draft")).toEqual([]);
        expect(heldCopy()[0].answer).toBe("Half an answer");
        expect(typeof heldCopy()[0].skipRevision).toBe("number");
      });

      it("the desktop gone altogether says so, on the shell too", async () => {
        await lostSkip({ status: 502, body: {} });
        expect(await screen.findByText(/desktop can't be reached/, undefined, { timeout: 6000 })).toBeTruthy();
        expect(await screen.findByText(/Desktop offline/)).toBeTruthy();
        expect(called("save_practice_draft")).toEqual([]);
      }, 10000);

      it("Back writes nothing, and reopening reads before it writes", async () => {
        await lostSkip(READ_REFUSED);
        await screen.findByText(/desktop can't be reached/);
        await waitFor(() => expect((screen.getByRole("button", { name: "Back" }) as HTMLButtonElement).disabled).toBe(false));
        fireEvent.click(screen.getByRole("button", { name: "Back" }));
        await screen.findByRole("button", { name: /^Next: Topic i1/ });
        await settle();
        expect(called("save_practice_draft")).toEqual([]);
        answers.get_session = session();
        fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
        await screen.findByRole("textbox", { name: "Your answer" });
        await settle();
        expect(called("save_practice_draft")).toEqual([]);
        expect(heldCopy()).toEqual([]);
        await screen.findByRole("button", { name: /^Next: Topic i1/ });
      });

      it("an edit waits for the read: not landed, that edit is saved", async () => {
        await lostSkip(READ_REFUSED);
        await screen.findByText(/desktop can't be reached/);
        await waitFor(() => expect((screen.getByRole("button", { name: "Skip" }) as HTMLButtonElement).disabled).toBe(false));
        answers.get_session = HELD();
        typeInto("Half an answer, and more");
        await waitFor(() => expect(called("save_practice_draft")).toHaveLength(1), { timeout: 3000 });
        expect(called("save_practice_draft")[0].params.answerMd).toBe("Half an answer, and more");
      });

      it("what is written after the skip outlives it: kept on the phone and saved under a fresh draft", async () => {
        await lostSkip(READ_REFUSED);
        await screen.findByText(/desktop can't be reached/);
        await waitFor(() => expect((screen.getByRole("button", { name: "Skip" }) as HTMLButtonElement).disabled).toBe(false));
        const oldKey = (Object.values(JSON.parse(localStorage.getItem("learnloop.questionDrafts") ?? "{}"))[0] as { submissionId: string }).submissionId;
        typeInto("Half an answer, and more");
        // Still no read: the new text is on the phone and nothing has gone out.
        await settle();
        expect(called("save_practice_draft")).toEqual([]);
        expect(heldCopy()[0].answer).toBe("Half an answer, and more");
        // Connectivity returns with no checkpoint: the skip landed.
        answers.get_session = session();
        typeInto("Half an answer, and more still");
        await waitFor(() => expect(called("save_practice_draft")).toHaveLength(1), { timeout: 3000 });
        const saved = called("save_practice_draft")[0].params;
        expect(saved.answerMd).toBe("Half an answer, and more still");
        expect(saved.submissionId).not.toBe(oldKey);
        // That serve's offer went with the skip.
        expect(saved.schedulerCandidateId ?? null).toBeNull();
        expect(screen.getByRole("textbox", { name: "Your answer" }).textContent).toContain("and more still");
        expect(await screen.findByText(/what you wrote since is kept/)).toBeTruthy();
        expect(heldCopy()[0]).toMatchObject({ answer: "Half an answer, and more still", outcome: "none" });
        expect(heldCopy()[0].skipRevision ?? null).toBeNull();
        expect(called("skip_practice_item")).toHaveLength(1);
      });

      it("that text is submitted under the fresh key, with no read of the old one", async () => {
        await lostSkip(READ_REFUSED);
        await screen.findByText(/desktop can't be reached/);
        await waitFor(() => expect((screen.getByRole("button", { name: "Submit" }) as HTMLButtonElement).disabled).toBe(false));
        const oldKey = (Object.values(JSON.parse(localStorage.getItem("learnloop.questionDrafts") ?? "{}"))[0] as { submissionId: string }).submissionId;
        answers.get_session = READ_REFUSED;
        typeInto("A real answer now");
        answers.get_session = session();
        fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
        await screen.findByText("3 / 4");
        const submit = called("submit_attempt")[0].params;
        expect(submit.answerMd).toBe("A real answer now");
        expect(submit.submissionId).not.toBe(oldKey);
        expect(submit.schedulerCandidateId ?? null).toBeNull();
        expect(called("save_practice_draft")[0].params.submissionId).toBe(submit.submissionId);
      });

      it("the new text survives a closed app too", async () => {
        await lostSkip(READ_REFUSED);
        await screen.findByText(/desktop can't be reached/);
        await waitFor(() => expect((screen.getByRole("button", { name: "Back" }) as HTMLButtonElement).disabled).toBe(false));
        typeInto("Half an answer, and more");
        fireEvent.click(screen.getByRole("button", { name: "Back" }));
        await screen.findByRole("button", { name: /^Next: Topic i1/ });
        expect(called("save_practice_draft")).toEqual([]);
        answers.get_session = session();
        fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
        await waitFor(() => expect(called("save_practice_draft")).toHaveLength(1), { timeout: 3000 });
        expect(called("save_practice_draft")[0].params.answerMd).toBe("Half an answer, and more");
      });

      it("Skip again covers what was written since: it landed, and all of it goes", async () => {
        await lostSkip(READ_REFUSED);
        await screen.findByText(/desktop can't be reached/);
        await waitFor(() => expect((screen.getByRole("button", { name: "Skip" }) as HTMLButtonElement).disabled).toBe(false));
        typeInto("Half an answer, and more");
        answers.get_session = session();
        fireEvent.click(screen.getByRole("button", { name: "Skip" }));
        await screen.findByRole("button", { name: /^Next: Topic i1/ });
        await settle();
        expect(called("save_practice_draft")).toEqual([]);
        expect(called("skip_practice_item")).toHaveLength(1);
        expect(heldCopy()).toEqual([]);
      });

      it("Skip again reads first: landed, no second skip", async () => {
        await lostSkip(READ_REFUSED);
        await screen.findByText(/desktop can't be reached/);
        await waitFor(() => expect((screen.getByRole("button", { name: "Skip" }) as HTMLButtonElement).disabled).toBe(false));
        answers.get_session = session();
        fireEvent.click(screen.getByRole("button", { name: "Skip" }));
        await screen.findByRole("button", { name: /^Next: Topic i1/ });
        expect(called("skip_practice_item")).toHaveLength(1);
      });

      it("Skip again reads first: not landed, it goes out again", async () => {
        await lostSkip(READ_REFUSED);
        await screen.findByText(/desktop can't be reached/);
        await waitFor(() => expect((screen.getByRole("button", { name: "Skip" }) as HTMLButtonElement).disabled).toBe(false));
        answers.get_session = HELD();
        answers.skip_practice_item = queue([row("i2")]);
        fireEvent.click(screen.getByRole("button", { name: "Skip" }));
        await screen.findByRole("button", { name: /^Next: Topic i2/ });
        expect(called("skip_practice_item")).toHaveLength(2);
        expect(called("save_practice_draft")).toEqual([]);
      });

      it("Submit reads first: landed, nothing is graded", async () => {
        await lostSkip(READ_REFUSED);
        await screen.findByText(/desktop can't be reached/);
        await waitFor(() => expect((screen.getByRole("button", { name: "Submit" }) as HTMLButtonElement).disabled).toBe(false));
        answers.get_session = session();
        fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
        await screen.findByRole("button", { name: /^Next: Topic i1/ });
        expect(called("submit_attempt")).toEqual([]);
        expect(called("save_practice_draft")).toEqual([]);
      });

      it("Submit reads first: still unreachable, nothing goes out", async () => {
        await lostSkip(READ_REFUSED);
        await screen.findByText(/desktop can't be reached/);
        await waitFor(() => expect((screen.getByRole("button", { name: "Submit" }) as HTMLButtonElement).disabled).toBe(false));
        fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
        await settle();
        expect(called("submit_attempt")).toEqual([]);
        expect(called("save_practice_draft")).toEqual([]);
        expect(screen.getByText(/desktop can't be reached/)).toBeTruthy();
      });
    });
  });
});


import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { clear as clearQueries } from "@desktop/api/queryCache";
import { App } from "./App";
import { saveCredential } from "./store/credential";
import { cacheSessionId, rememberPendingSubmit } from "./store/sessionCache";
import { listOutbox } from "./store/outbox";

// A fake host: the real App over a fetch that answers as `/rpc` and the status endpoints do.
interface Call { method: string; params: Record<string, unknown>; requestId?: string }
type RpcAnswer = unknown | { status: number; body: unknown };

const session = (extra: Record<string, unknown> = {}) => ({
  version: 1, sessionId: "s1", startedAt: "t", endedAt: null, energy: null, sleepQuality: null, availableMinutes: 15,
  notesMdPath: null, checkpoint: null, ownerDeviceId: "dev", ownerLabel: "Phone", ownerGeneration: 0, ...extra
});
const row = (id: string, candidate = `cand_${id}`) => ({
  practiceItemId: id, schedulerCandidateId: candidate, learningObjectTitle: `Topic ${id}`, dueStatus: "due"
});
const queue = (rows: unknown[], deferred = 0) => ({
  version: 1, generatedAt: "t", sessionId: "s1", sections: rows.length ? [{ title: "Due now", items: rows }] : [], totalItems: rows.length, deviceDeferredCount: deferred
});
const item = (id = "i1") => ({
  id, learningObjectId: "lo", learningObjectTitle: `Topic ${id}`, prompt: "Define it.", attemptTypesAllowed: ["independent_attempt"],
  assessmentContractVersionId: "acv", presentation: { practiceItemId: id, blocks: [{ kind: "prompt", markdown: "Define it.", label: null }] }
});
const feedback = () => ({
  attemptId: "a1", practiceItemId: "i1", learningObjectTitle: "Topic i1", rubricScore: 3, maxPoints: 4, feedbackMd: "Close.",
  criterionEvidence: [{ criterionId: "c", criterionDescription: "Correct", pointsAwarded: 3, pointsPossible: 4, notes: null }], manualReviewReason: null
});

const calls: Call[] = [];
const gets: string[] = [];
let answers: Record<string, RpcAnswer | ((call: Call) => RpcAnswer)>;
let getAnswers: Record<string, unknown>;

function respond(answer: RpcAnswer): Response {
  if (answer && typeof answer === "object" && "status" in answer && "body" in answer) {
    const shaped = answer as { status: number; body: unknown };
    return new Response(JSON.stringify(shaped.body), { status: shaped.status });
  }
  return new Response(JSON.stringify({ ok: true, result: answer }), { status: 200 });
}

function fakeFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const url = String(input);
  if (url === "/rpc") {
    const body = JSON.parse(init?.body as string);
    const call: Call = { method: body.method, params: body.params, requestId: body.request_id };
    calls.push(call);
    if (!(body.method in answers)) return Promise.resolve(new Response(JSON.stringify({ ok: false, error: { code: "not_found", message: `no fake for ${body.method}`, retryable: false } }), { status: 404 }));
    const answer = answers[body.method];
    return Promise.resolve(respond(typeof answer === "function" ? (answer as (call: Call) => RpcAnswer)(call) : answer));
  }
  gets.push(url);
  if (url === "/api/v1/queue-revision") return Promise.resolve(new Response(JSON.stringify({ revision: 1 }), { status: 200 }));
  if (url in getAnswers) return Promise.resolve(new Response(JSON.stringify(getAnswers[url]), { status: 200 }));
  return Promise.resolve(new Response(JSON.stringify({ ok: false, error: { code: "not_found", message: "no fake", retryable: false } }), { status: 404 }));
}

const called = (method: string) => calls.filter((call) => call.method === method);

beforeEach(async () => {
  calls.length = 0;
  gets.length = 0;
  clearQueries();
  getAnswers = {};
  answers = {
    start_session: session(),
    get_session: session(),
    get_today_queue: queue([row("i1"), row("i2")]),
    get_practice_item: item(),
    get_probe_contract: { version: 1, active: false },
    save_practice_draft: { ok: true },
    submit_attempt: { attemptId: "a1", practiceItemId: "i1" },
    acknowledge_practice_submission: { status: "cleared", acknowledged: true },
    get_feedback: feedback(),
    get_grading_clarification: { version: 1, clarification: null },
    end_session: { attemptsRecorded: 1 }
  };
  vi.stubGlobal("fetch", vi.fn(fakeFetch));
  await saveCredential({ token: "tok", deviceId: "dev", scope: "app" });
});

async function beginSession() {
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "15 min" }));
  await screen.findByRole("button", { name: /^Next: Topic i1/ });
}

describe("Today", () => {
  it("serves the allowlisted queue and names no plan RPC", async () => {
    await beginSession();
    expect(called("start_session")[0].params).toEqual({ availableMinutes: 15 });
    expect(called("get_today_queue")[0].params.sessionId).toBe("s1");
    expect(calls.map((call) => call.method).filter((name) => name.includes("plan"))).toEqual([]);
    expect(screen.getByRole("button", { name: "Topic i2" })).toBeTruthy();
  });

  it("says how many wait for the desktop (§6.4, D6)", async () => {
    answers.get_today_queue = queue([row("i1")], 3);
    await beginSession();
    expect(await screen.findByText("3 items waiting for the desktop")).toBeTruthy();
  });

  it("says one item in the singular and nothing for none", async () => {
    answers.get_today_queue = queue([row("i1")], 1);
    await beginSession();
    expect(await screen.findByText("1 item waiting for the desktop")).toBeTruthy();
  });

  it("does not rebuild the queue at an unchanged token", async () => {
    await beginSession();
    const builds = called("get_today_queue").length;
    await act(async () => {
      window.dispatchEvent(new Event("focus"));
      await Promise.resolve();
    });
    await waitFor(() => expect(gets.filter((url) => url === "/api/v1/queue-revision").length).toBeGreaterThan(1));
    expect(called("get_today_queue").length).toBe(builds);
  });
});

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
});

describe("capture and the desktop being away (§7)", () => {
  it("a capture is saved while the desktop is asleep and sent when it wakes", async () => {
    let awake = false;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (!awake) return Promise.reject(new TypeError("asleep"));
      if (String(input) === "/api/v1/capture") return Promise.resolve(new Response("{}", { status: 201 }));
      return fakeFetch(input, init);
    }));
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Capture" }));
    fireEvent.change(screen.getByLabelText("A thought, a problem or a link"), { target: { value: "An idea" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(await screen.findByText("Saved.")).toBeTruthy();
    await waitFor(async () => expect(await listOutbox()).toHaveLength(1));
    expect(await screen.findByText(/Desktop offline/)).toBeTruthy();
    awake = true;
    await act(async () => {
      window.dispatchEvent(new Event("focus"));
      await new Promise((resolve) => setTimeout(resolve, 10));
    });
    await waitFor(async () => expect(await listOutbox()).toEqual([]));
  });

  it("a URL is a url capture", async () => {
    const captured: unknown[] = [];
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input) === "/api/v1/capture") {
        captured.push(JSON.parse(init?.body as string));
        return Promise.resolve(new Response("{}", { status: 201 }));
      }
      return fakeFetch(input, init);
    }));
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Capture" }));
    fireEvent.change(screen.getByLabelText("A thought, a problem or a link"), { target: { value: "https://arxiv.org/abs/2401.00001" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(captured).toHaveLength(1));
    expect(captured[0]).toMatchObject({ kind: "url", url: "https://arxiv.org/abs/2401.00001" });
  });
});

describe("pairing (§4.2)", () => {
  it("an app with no token pairs with the manual code", async () => {
    const { deleteCredential, readCredential } = await import("./store/credential");
    await deleteCredential();
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input) === "/pair") {
        expect(JSON.parse(init?.body as string)).toEqual({ code: "ABCDEFGHJK", device_label: "Phone" });
        return new Response(JSON.stringify({ device_id: "d9", scope: "app", token: "new" }), { status: 200 });
      }
      return fakeFetch(input, init);
    }));
    render(<App />);
    fireEvent.change(await screen.findByLabelText("Manual code"), { target: { value: "ABCDEFGHJK" } });
    fireEvent.click(screen.getByRole("button", { name: "Pair" }));
    expect(await screen.findByRole("button", { name: "15 min" })).toBeTruthy();
    await expect(readCredential()).resolves.toEqual({ token: "new", deviceId: "d9", scope: "app" });
  });

  it("a Shortcut's code is refused with what to do", async () => {
    const { deleteCredential } = await import("./store/credential");
    await deleteCredential();
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ device_id: "d9", scope: "capture", token: "narrow" }), { status: 200 })));
    render(<App />);
    fireEvent.change(await screen.findByLabelText("Manual code"), { target: { value: "ABCDEFGHJK" } });
    fireEvent.click(screen.getByRole("button", { name: "Pair" }));
    expect(await screen.findByText(/for the Shortcut/)).toBeTruthy();
  });

  it("unpaired with captures waiting says how many", async () => {
    const { deleteCredential } = await import("./store/credential");
    const { addToOutbox } = await import("./store/outbox");
    await deleteCredential();
    await addToOutbox({ clientCaptureId: "c", kind: "text", text: "x", capturedAt: "t" });
    render(<App />);
    expect(await screen.findByText("Scan a new token to send 1 capture.")).toBeTruthy();
  });
});

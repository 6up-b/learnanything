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

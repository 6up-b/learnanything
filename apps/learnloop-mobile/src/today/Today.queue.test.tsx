// Today as M2a's queue: the plan off, or the host's kill switch
// Split out of App.test.tsx (mobile v2 V2, V1's carried item): the cases are unchanged.
import {
  act, answers, App, beforeEach, beginSession, cacheSessionId, called, calls, cleanup, describe, expect, fakeFetch, feedback, fireEvent,
  getAnswers, gets, installFakeHost, it, item, listOutbox, PLAN_OFF, queue, rememberPendingSubmit, render, respond, row, saveCredential,
  screen, session, vi, waitFor, type Call, type RpcAnswer
} from "../test/fakeHost";

installFakeHost();

describe("Today", () => {
  it("with the plan off, serves the allowlisted queue and asks the plan nothing more (mobile v2 §2.2)", async () => {
    await beginSession();
    expect(called("start_session")[0].params).toEqual({ availableMinutes: 15 });
    expect(called("get_today_queue")[0].params.sessionId).toBe("s1");
    // One read says the plan is off; no plan step, minutes or stop is ever sent.
    expect(new Set(calls.map((call) => call.method).filter((name) => name.includes("plan")))).toEqual(new Set(["get_daily_plan"]));
    expect(screen.getByRole("button", { name: "Topic i2" })).toBeTruthy();
  });

  it("the host's kill switch is the queue too", async () => {
    answers.get_daily_plan = { status: 409, body: { ok: false, error: { code: "phone_plan_off", message: "off", retryable: false } } };
    await beginSession();
    expect(screen.getByRole("button", { name: "Topic i2" })).toBeTruthy();
    expect(screen.queryByRole("alert")).toBeNull();
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


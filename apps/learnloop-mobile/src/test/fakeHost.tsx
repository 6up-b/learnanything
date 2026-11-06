// The fake host every phone journey test runs against (split out of `App.test.tsx`, mobile v2 V2):
// the real App over a fetch that answers as `/rpc` and the status endpoints do. Each journey's file
// calls `installFakeHost()` once; `answers` and `getAnswers` are filled afresh before each test.
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, vi } from "vitest";
import { clear as clearQueries } from "@desktop/api/queryCache";
import { App } from "../App";
import { saveCredential } from "../store/credential";

export { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
export { beforeEach, describe, expect, it, vi } from "vitest";
export { App } from "../App";
export { saveCredential } from "../store/credential";
export { cacheSessionId, rememberPendingSubmit } from "../store/sessionCache";
export { listOutbox } from "../store/outbox";

// A fake host: the real App over a fetch that answers as `/rpc` and the status endpoints do.
export interface Call { method: string; params: Record<string, unknown>; requestId?: string }
export type RpcAnswer = unknown | { status: number; body: unknown };

export const session = (extra: Record<string, unknown> = {}) => ({
  version: 1, sessionId: "s1", startedAt: "t", endedAt: null, energy: null, sleepQuality: null, availableMinutes: 15,
  notesMdPath: null, checkpoint: null, ownerDeviceId: "dev", ownerLabel: "Phone", ownerGeneration: 0, ...extra
});
export const row = (id: string, candidate = `cand_${id}`) => ({
  practiceItemId: id, schedulerCandidateId: candidate, learningObjectTitle: `Topic ${id}`, dueStatus: "due"
});
export const queue = (rows: unknown[], deferred = 0) => ({
  version: 1, generatedAt: "t", sessionId: "s1", sections: rows.length ? [{ title: "Due now", items: rows }] : [], totalItems: rows.length, deviceDeferredCount: deferred
});
export const item = (id = "i1") => ({
  id, learningObjectId: "lo", learningObjectTitle: `Topic ${id}`, prompt: "Define it.", attemptTypesAllowed: ["independent_attempt"],
  assessmentContractVersionId: "acv", presentation: { practiceItemId: id, blocks: [{ kind: "prompt", markdown: "Define it.", label: null }] }
});
export const feedback = () => ({
  attemptId: "a1", practiceItemId: "i1", learningObjectTitle: "Topic i1", rubricScore: 3, maxPoints: 4, feedbackMd: "Close.",
  criterionEvidence: [{ criterionId: "c", criterionDescription: "Correct", pointsAwarded: 3, pointsPossible: 4, notes: null }], manualReviewReason: null
});


export const calls: Call[] = [];
export const gets: string[] = [];
export const answers: Record<string, RpcAnswer | ((call: Call) => RpcAnswer)> = {};
export const getAnswers: Record<string, unknown> = {};

export function respond(answer: RpcAnswer): Response {
  if (answer && typeof answer === "object" && "status" in answer && "body" in answer) {
    const shaped = answer as { status: number; body: unknown };
    return new Response(JSON.stringify(shaped.body), { status: shaped.status });
  }
  return new Response(JSON.stringify({ ok: true, result: answer }), { status: 200 });
}

export function fakeFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
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

export const called = (method: string) => calls.filter((call) => call.method === method);

// The plan's own journeys (`today/Today.plan.test.tsx`) answer `get_daily_plan` with a plan.
import { PLAN_OFF } from "./planOff";

export { PLAN_OFF };

export function installFakeHost(): void {
  beforeEach(async () => {
    calls.length = 0;
    gets.length = 0;
    clearQueries();
    for (const key of Object.keys(getAnswers)) delete getAnswers[key];
    for (const key of Object.keys(answers)) delete answers[key];
    Object.assign(answers, {
      start_session: session(),
      get_session: session(),
      get_daily_plan: PLAN_OFF,
      get_today_queue: queue([row("i1"), row("i2")]),
      get_practice_item: item(),
      get_probe_contract: { version: 1, active: false },
      save_practice_draft: { ok: true },
      submit_attempt: { attemptId: "a1", practiceItemId: "i1" },
      acknowledge_practice_submission: { status: "cleared", acknowledged: true },
      get_feedback: feedback(),
      get_grading_clarification: { version: 1, clarification: null },
      end_session: { attemptsRecorded: 1 }
    });
    vi.stubGlobal("fetch", vi.fn(fakeFetch));
    await saveCredential({ token: "tok", deviceId: "dev", scope: "app" });
  });
}

export async function beginSession() {
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "15 min" }));
  await screen.findByRole("button", { name: /^Next: Topic i1/ });
}

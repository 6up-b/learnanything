// The companion's questions as polled jobs (the RD3a contract): asked at once, polled through the one
// poller (paused with the window asked from), answered, failed, cancelled (kept or not), interrupted.
import { describe, expect, it, vi } from "vitest";
import type { CompanionAskInput, CompanionAskJobDto, ReaderAnswerDto } from "../../../api/dto";
import { Poller } from "../../../api/poller";
import { CompanionAsks, type CompanionApi } from "./asks";

function job(requestId: string, over: Partial<CompanionAskJobDto> = {}): CompanionAskJobDto {
  return { version: 1, requestId, status: "running", done: false, partialMd: "", citations: [], streamedPieces: 0, questionEventId: null, kept: false, answer: null, error: null, ...over };
}

const ANSWER = { eventId: "ev1", readerAnswerEventId: "ans1", answerMd: "The answer.", answerMode: "answer_directly", citations: [], manifest: {}, warmedSurfaceIds: [], burnedSurfaceIds: [], hintEquivalent: false, remaining: null } as unknown as ReaderAnswerDto;

function setup() {
  const asked: CompanionAskInput[] = [];
  let next: (requestId: string) => CompanionAskJobDto = (id) => job(id);
  const api: CompanionApi & { reads: number } = {
    reads: 0,
    companionAsk: vi.fn(async (input: CompanionAskInput) => {
      asked.push(input);
      return job(input.requestId, { status: "queued" });
    }),
    companionAskJob: vi.fn(async ({ requestId }) => {
      api.reads += 1;
      return next(requestId);
    }),
    companionAskCancel: vi.fn(async ({ requestId }) => job(requestId, { status: "cancelled", done: true, kept: true })),
  };
  const poller = new Poller({ setInterval: () => 1, clearInterval: () => undefined });
  let counter = 0;
  const asks = new CompanionAsks(api, poller, () => `req${++counter}`, () => 1000);
  return { api, poller, asks, asked, setNext: (fn: typeof next) => { next = fn; } };
}

const REQUEST = { deskId: "d1", windowId: "w1", surface: "desk" as const, question: "why e?", extractionId: "ext", spanId: "s1", quote: "the exponential" };

describe("asking", () => {
  it("shows the question at once, then follows its job through the poller to the answer", async () => {
    const { asks, poller, asked, setNext } = setup();
    asks.ask(REQUEST);
    expect(asks.thread("d1").map((exchange) => [exchange.question, exchange.status])).toEqual([["why e?", "asking"]]);
    await Promise.resolve();
    await Promise.resolve();
    expect(asked[0]).toMatchObject({ requestId: "req1", surface: "desk", deskId: "d1", selectionQuote: "the exponential", parentExchangeId: null });
    expect(poller.size).toBe(1);
    setNext((id) => job(id, { status: "running", streamedPieces: 3 }));
    await poller.tick();
    expect(asks.thread("d1")[0]).toMatchObject({ status: "asking", streamedPieces: 3 });
    setNext((id) => job(id, { status: "done", done: true, answer: ANSWER, partialMd: "The answer." }));
    await poller.tick();
    expect(asks.thread("d1")[0]).toMatchObject({ status: "answered", answer: ANSWER });
    expect(poller.size).toBe(0);
  });

  it("a follow-up about the same reading branches from the last answer", async () => {
    const { asks, poller, asked, setNext } = setup();
    setNext((id) => job(id, { status: "done", done: true, answer: ANSWER }));
    asks.ask(REQUEST);
    await Promise.resolve();
    await Promise.resolve();
    await poller.tick();
    asks.ask({ ...REQUEST, question: "and the base?" });
    await Promise.resolve();
    expect(asked[1].parentExchangeId).toBe("ans1");
    asks.ask({ ...REQUEST, extractionId: "other", question: "elsewhere" });
    await Promise.resolve();
    expect(asked[2].parentExchangeId).toBeNull();
  });

  it("a paused window's question is not read until it is back", async () => {
    const { asks, poller, api } = setup();
    asks.ask(REQUEST);
    await Promise.resolve();
    await Promise.resolve();
    poller.setOwnerPaused("w1", true);
    await poller.tick();
    expect(api.reads).toBe(0);
    poller.setOwnerPaused("w1", false);
    await poller.tick();
    expect(api.reads).toBe(1);
  });
});

describe("honest endings", () => {
  it("a refusal at the request is a failure in its own words, with no job", async () => {
    const { asks, api, poller } = setup();
    vi.mocked(api.companionAsk).mockRejectedValueOnce({ code: "waiting_for_ok", message: "LearnLoop needs your OK to use AI.", retryable: false });
    asks.ask(REQUEST);
    await Promise.resolve();
    await Promise.resolve();
    expect(asks.thread("d1")[0]).toMatchObject({ status: "failed", error: { code: "waiting_for_ok", message: "LearnLoop needs your OK to use AI." } });
    expect(poller.size).toBe(0);
  });

  it("a job that fails says why; an interrupted one says it was interrupted and can be asked again", async () => {
    const { asks, poller, setNext, asked } = setup();
    setNext((id) => job(id, { status: "failed", done: true, error: { code: "interrupted", message: "The vault closed while this was being answered.", retryable: true } }));
    const id = asks.ask(REQUEST);
    await Promise.resolve();
    await Promise.resolve();
    await poller.tick();
    expect(asks.thread("d1")[0]).toMatchObject({ status: "interrupted" });
    asks.retry(id);
    expect(asks.thread("d1")).toHaveLength(2);
    await Promise.resolve();
    expect(asked[1].requestId).toBe("req2");
  });

  it("a job the sidecar no longer knows (it restarted) is interrupted, and its poll stops", async () => {
    const { asks, poller, api } = setup();
    vi.mocked(api.companionAskJob).mockRejectedValue({ code: "job_not_found", message: "LearnLoop restarted since it was asked.", retryable: false });
    asks.ask(REQUEST);
    await Promise.resolve();
    await Promise.resolve();
    await poller.tick();
    expect(asks.thread("d1")[0]).toMatchObject({ status: "interrupted", error: { code: "job_not_found" } });
    expect(poller.size).toBe(0);
  });

  it("cancel: the job says cancelled, and whether its answer was kept in the history", async () => {
    const { asks, poller } = setup();
    const id = asks.ask(REQUEST);
    await Promise.resolve();
    await Promise.resolve();
    asks.cancel(id);
    await Promise.resolve();
    await Promise.resolve();
    expect(asks.thread("d1")[0]).toMatchObject({ status: "cancelled", kept: true });
    expect(poller.size).toBe(0);
  });
});

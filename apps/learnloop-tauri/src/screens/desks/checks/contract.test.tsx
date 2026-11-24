// The desks' side of the server's contract for an open check (RD7 fix round; reader-rd7a.md §8.1): the standing
// veil set replaces the desks' own (a lost reply loses no veil), an opening carries one exposure id across retries and
// a failed one keeps its veil, a restart reuses the reserved submission and the kept draft, a lost begin reply's retry
// adopts the open card, a closed request says so, a stale answer is sent again after the standing set, "not now" is
// off while the answer is on its way, and the card is worded from the serve-time eligibility.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { CheckCardDto, CheckSubmitDto, CheckVeilRefDto } from "../../../api/dto";
import { CheckDesk, type CheckTransport, type DraftStore } from "./controller";
import { CheckCardInline } from "./CheckCard";
import { SHOW_UNMEASURED_COST, costOf } from "./model";

vi.mock("../../../api/client", () => ({ api: {} }));
vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
afterEach(cleanup);

const flush = () => act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });

const PAD: CheckVeilRefDto = { group: "pads", kind: "window", window_id: "w_pad", measured: true };
const NEW: CheckVeilRefDto = { group: "lessons", kind: "window", window_id: "w_lesson", measured: false };

function card(over: Partial<CheckCardDto> = {}): CheckCardDto {
  return {
    administrationToken: "cad_1", commitmentId: "cm_1", itemRef: "pi_1", contractHash: "h", cold: true, state: "open",
    protection: { veilSetId: "v", method: "m", veiled: [PAD], opened: [], groups: ["pads"] },
    prompt: { prompt: "Why?" }, submissionId: null, eligibility: null, revision: 1, ...over,
  };
}

function memoryDrafts(seed: Record<string, string> = {}): DraftStore & { values: Map<string, string> } {
  const values = new Map(Object.entries(seed));
  return { values, get: (token) => values.get(token) ?? null, set: (token, text) => { if (text) values.set(token, text); else values.delete(token); } };
}

function fake(over: Partial<CheckTransport> = {}, drafts = memoryDrafts()) {
  const transport: CheckTransport = {
    dueFor: vi.fn(async () => ({ version: 1, checks: [] })),
    begin: vi.fn(async () => card()),
    protectMore: vi.fn(async () => ({ veilAdditions: [], standing: [PAD], revision: 1 })),
    expose: vi.fn(async () => ({ protectionStatus: { exposure: [], coldNow: true, measured: true } })),
    submit: vi.fn(async () => ({ administrationToken: "cad_1", attemptId: "at_1", cold: true, reason: "on_your_own" as const })),
    abandon: vi.fn(async () => ({})),
    openInline: vi.fn(async () => ({ administration: null })),
    ...over,
  };
  let n = 0;
  return { desk: new CheckDesk(transport, (prefix) => `${prefix}_${++n}`, drafts), transport, drafts };
}

describe("the server's contract, from the desks", () => {
  it("replaces the veils with the standing set: a protect reply lost after the server veiled something loses nothing", async () => {
    let lost = true;
    const { desk } = fake({ protectMore: vi.fn(async () => {
      if (lost) {
        lost = false;
        // The server recorded the new window's veil, but the reply never arrived.
        throw { code: "internal", message: "connection reset" };
      }
      // The retry finds the ref already recorded: no additions, but the standing set names it.
      return { veilAdditions: [], standing: [PAD, NEW], revision: 2 };
    }) });
    await desk.begin("cm_1", null, { windows: [] });
    await desk.protectMore({ windows: [{ windowId: "w_lesson", kind: "lesson" }] });
    expect(desk.veils().map((ref) => ref.window_id)).toEqual(["w_pad"]);
    await desk.protectMore({ windows: [{ windowId: "w_lesson", kind: "lesson" }] });
    expect(desk.veils().map((ref) => ref.window_id)).toEqual(["w_pad", "w_lesson"]);
  });

  it("an opening carries one exposure id across a retry, and a failed one keeps its veil", async () => {
    let fail = true;
    const { desk, transport } = fake({ expose: vi.fn(async () => {
      if (fail) throw { code: "internal", message: "offline" };
      return { protectionStatus: { exposure: [], coldNow: true, measured: true } };
    }) });
    await desk.begin("cm_1", null, { windows: [] });
    expect(await desk.expose(PAD)).toBe(false);
    expect(desk.veils()).toEqual([PAD]);
    expect(desk.open()?.error).toContain("it stays hidden");
    fail = false;
    expect(await desk.expose(PAD)).toBe(true);
    const ids = (transport.expose as ReturnType<typeof vi.fn>).mock.calls.map((call) => call[0].exposureId);
    expect(ids).toHaveLength(2);
    expect(ids[0]).toBe(ids[1]);
    expect(desk.veils()).toEqual([]);
  });

  it("after a restart the reserved submission is sent again with the kept draft", async () => {
    const drafts = memoryDrafts({ cad_9: "p_k - [k = y]" });
    const { desk, transport } = fake({ openInline: vi.fn(async () => ({ administration: card({ administrationToken: "cad_9", submissionId: "csub_reserved" }) })) }, drafts);
    desk.recover();
    await flush();
    expect(desk.recovery()).toBe("known");
    expect(desk.open()?.answer).toBe("p_k - [k = y]");
    await desk.submit();
    expect(transport.submit).toHaveBeenCalledWith({ administrationToken: "cad_9", submissionId: "csub_reserved", answerMd: "p_k - [k = y]", veilsRevision: 1 });
    expect(drafts.values.has("cad_9")).toBe(false);
  });

  it("the answer typed is kept by administration (a restart finds it)", async () => {
    const drafts = memoryDrafts();
    const { desk } = fake({}, drafts);
    await desk.begin("cm_1", null, { windows: [] });
    desk.setAnswer("half an answer");
    expect(drafts.values.get("cad_1")).toBe("half an answer");
  });

  it("a lost begin reply's retry adopts the open card; a closed request says so and opens nothing", async () => {
    const replay = fake({ begin: vi.fn(async () => card({ replayed: true })) });
    expect(await replay.desk.begin("cm_1", null, { windows: [{ windowId: "w_book", kind: "source", extractionId: "e", spanIds: ["s1"] }] })).toBe(true);
    // Its veils were judged on an earlier view: this view's passages wait for a protect request.
    expect(replay.desk.passageJudged("w_book", "e", "s1")).toBe(false);
    const closed = fake({ begin: vi.fn(async () => { throw { code: "administration_closed", message: "closed", details: { state: "submitted", outcome: "on_your_own" } }; }) });
    expect(await closed.desk.begin("cm_1", null, { windows: [] })).toBe(false);
    expect(closed.desk.open()).toBeNull();
    expect(closed.desk.notice).toBe("this check is closed already");
  });

  it("another commitment's open administration the desks did not know about is adopted from the restart read", async () => {
    const { desk, transport } = fake({
      begin: vi.fn(async () => { throw { code: "administration_open", message: "open", details: { administrationToken: "cad_7", commitmentId: "cm_7" } }; }),
      openInline: vi.fn(async () => ({ administration: null })),
    });
    desk.recover();
    await flush();
    // Opened meanwhile from another window of the app: the next read finds it.
    (transport.openInline as ReturnType<typeof vi.fn>).mockClear();
    (transport.openInline as ReturnType<typeof vi.fn>).mockImplementation(async () => ({ administration: card({ administrationToken: "cad_7", commitmentId: "cm_7" }) }));
    expect(await desk.begin("cm_1", null, { windows: [] })).toBe(false);
    await flush();
    expect(transport.openInline).toHaveBeenCalledTimes(1);
    expect(desk.open()?.card.administrationToken).toBe("cad_7");
  });

  it("a stale answer is refused, the standing set read again, and the same submission sent with the new revision", async () => {
    let first = true;
    const { desk, transport } = fake({
      protectMore: vi.fn(async () => ({ veilAdditions: [NEW], standing: [PAD, NEW], revision: 3 })),
      submit: vi.fn(async (input) => {
        if (first) {
          first = false;
          throw { code: "veils_stale", message: "stale" };
        }
        return { administrationToken: input.administrationToken, attemptId: "at_1", cold: true, reason: "on_your_own" as const };
      }),
    });
    desk.setVisibleSource(() => ({ windows: [{ windowId: "w_lesson", kind: "lesson" }] }));
    await desk.begin("cm_1", null, { windows: [] });
    desk.setAnswer("x");
    await desk.submit();
    const sent = (transport.submit as ReturnType<typeof vi.fn>).mock.calls.map((call) => call[0]);
    expect(sent.map((input) => [input.submissionId, input.veilsRevision])).toEqual([["csub_2", 1], ["csub_2", 3]]);
    expect(desk.open()?.phase).toBe("answered");
  });

  it("not now is off while the answer is on its way", async () => {
    let release!: () => void;
    const { desk, transport } = fake({ submit: vi.fn(() => new Promise<CheckSubmitDto>((resolve) => { release = () => resolve({ administrationToken: "cad_1", attemptId: "at_1", cold: true, reason: "on_your_own" }); })) });
    await desk.begin("cm_1", null, { windows: [] });
    render(<CheckCardInline desk={desk} />);
    fireEvent.change(screen.getByLabelText("your answer"), { target: { value: "x" } });
    fireEvent.keyDown(screen.getByLabelText("your answer"), { key: "Enter" });
    await flush();
    const notNow = screen.getByRole("button", { name: "not now" }) as HTMLButtonElement;
    expect(notNow.disabled).toBe(true);
    fireEvent.click(notNow);
    expect(transport.abandon).not.toHaveBeenCalled();
    await act(async () => { release(); });
  });

  it("a check that opens not cold never says it is on your own; its blocks are the question as Today shows it", async () => {
    const { desk } = fake({ begin: vi.fn(async () => card({ cold: false, eligibility: "seen_before",
      prompt: { prompt: "Why?", presentation: { practiceItemId: "pi_1", blocks: [
        { kind: "laddered_stem_stimulus", markdown: "Given scores 1, 2, 3.", label: "the setup" }, { kind: "prompt", markdown: "Why?", label: null }] } } })) });
    await desk.begin("cm_1", null, { windows: [] });
    render(<CheckCardInline desk={desk} />);
    const shown = document.querySelector('[data-check-card="inline"]')!.textContent ?? "";
    expect(shown).not.toContain("on-your-own answer settles");
    expect(shown).not.toContain("a cold check · now");
    expect(shown).toContain("you have seen this answer before");
    expect(shown).toContain("Given scores 1, 2, 3.");
  });

  it("an opening the server cannot measure says before it opens that it makes the answer practice", () => {
    expect(costOf(NEW)).toBe(SHOW_UNMEASURED_COST);
    expect(costOf({ group: "this window's other parts", kind: "surface", surface: "window" })).toBe(SHOW_UNMEASURED_COST);
    expect(costOf(PAD)).not.toBe(SHOW_UNMEASURED_COST);
  });
});

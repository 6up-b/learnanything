// Inline cold checks on the desks (spec §12.6 as the owner's decisions corrected it; RD7's frontend half): the pure
// rules (where a veil lands, what is sent as visible, the words), the store (one administration at a time, the server's
// refusals in plain words, protect_more only for a change, exposure at once, a submission minted once, not now,
// restart), the veils in the page (marked again after a re-render, "show it anyway" with its cost, lifted after), and
// the cards (no cues before a check opens; the reason in plain words after).
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useState } from "react";
import type { CheckCardDto, CheckVeilRefDto } from "../../../api/dto";
import { CheckDesk, type CheckTransport } from "./controller";
import { CheckCardInline, CheckCardOverlay, CheckMarker } from "./CheckCard";
import { PRIMED_BY_NOTE_WORDS, REASON_WORDS, SHOW_ANYWAY_COST, SHOW_NOTE_COST, VEIL_LABEL, answeredHead, groupsLine, lookedLine, refKey, veilIsNote, veilSelector, visibleNow } from "./model";
import { VeilLayer, applyVeils } from "./VeilLayer";

vi.mock("../../../api/client", () => ({ api: {} }));
vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
afterEach(cleanup);

const flush = () => act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });

const PAD: CheckVeilRefDto = { group: "pads", kind: "window", window_id: "w_pad", pad_block_ids: ["b1"] };
const SPAN: CheckVeilRefDto = { group: "source passages", kind: "span", window_id: "w_book", extraction_id: "ext_book", span_id: "s2" };
const COMPANION: CheckVeilRefDto = { group: "the companion", kind: "companion", exchange_ids: [] };

function card(over: Partial<CheckCardDto> = {}): CheckCardDto {
  return {
    administrationToken: "cad_1", commitmentId: "cm_1", itemRef: "pi_1", contractHash: "h", cold: true, state: "open",
    protection: { veilSetId: "cvs_1", method: "structural+notes_by_default", veiled: [PAD, SPAN], opened: [], groups: ["pads", "source passages"] },
    prompt: { prompt: "What is $\\partial L/\\partial h_k$?" }, ...over,
  };
}

function fake(over: Partial<CheckTransport> = {}) {
  const calls: Record<string, unknown[]> = {};
  const log = <T,>(name: string, answer: (input: never) => T) => vi.fn(async (input?: unknown) => { (calls[name] ??= []).push(input); return answer(input as never); });
  const transport: CheckTransport = {
    dueFor: log("dueFor", (input: { extractionId: string }) => ({ version: 1, checks: [
      { commitmentId: "cm_1", loId: "lo_1", due: "2026-11-22T00:00:00Z", host: { extractionId: input.extractionId, sectionId: "sec_1", spanId: "s1" }, provenance: {} }] })),
    begin: log("begin", () => card()),
    protectMore: log("protectMore", () => ({ veilAdditions: [COMPANION] })),
    expose: log("expose", () => ({ protectionStatus: { exposure: [], coldNow: false } })),
    submit: log("submit", () => ({ administrationToken: "cad_1", attemptId: "at_1", cold: true, reason: "on_your_own" as const, feedbackMd: "Right." })),
    abandon: log("abandon", () => ({})),
    openInline: log("openInline", () => ({ administration: null })),
    ...over,
  };
  let n = 0;
  const desk = new CheckDesk(transport, (prefix) => `${prefix}_${++n}`);
  return { desk, transport, calls };
}

describe("the pure rules", () => {
  it("land each veil where the server named it, keep the window's head, and say the groups once", () => {
    expect(veilSelector(PAD)).toBe('[data-desk-window="w_pad"] [data-desk-pane-body]');
    expect(veilSelector(SPAN)).toContain('[data-desk-window="w_book"] [data-span-id="s2"]');
    expect(veilSelector({ group: "notes", kind: "note", window_id: "w_book", note_id: "ann_1" })).toBe('[data-desk-window="w_book"] [data-annotation-id="ann_1"]');
    expect(veilSelector({ group: "figures", kind: "figure", window_id: "w_book", figure_id: "f1" })).toBe('[data-desk-window="w_book"] [data-figure="f1"]');
    expect(veilSelector(COMPANION)).toBe("[data-companion-dock] [data-companion-body]");
    expect(veilSelector({ group: "previews", kind: "preview", window_id: "w_pad" })).toBe('[data-desk-card="w_pad"]');
    expect(groupsLine([PAD, SPAN, { ...SPAN, span_id: "s3" }])).toBe("pads · source passages (2)");
    expect(refKey({ ...SPAN, group: "other" })).toBe(refKey(SPAN));
  });

  it("say the reply's reason in plain words and what opening a veil turned out to cost", () => {
    expect(Object.keys(REASON_WORDS).sort()).toEqual(["already_answered", "on_your_own", "practice", "primed", "seen_before", "with_help"]);
    expect(answeredHead(true)).toBe("› your answer · just now · on your own");
    expect(answeredHead(false)).toBe("› your answer · just now · counts as practice");
    expect(lookedLine([], null)).toBeNull();
    expect(lookedLine(["pads"], false)).toBe("you looked at pads first · this answer counts as practice");
    expect(lookedLine(["pads"], true)).toContain("it said nothing of the answer");
    // The cost before opening says it may, not that it always does (the owner's overlap rule).
    expect(SHOW_ANYWAY_COST).toContain("If it shows what the answer says") ;
    expect(SHOW_ANYWAY_COST).toContain("If it doesn't, nothing changes");
  });

  it("send what is on screen: a source window's passages, notes and figures; another window's blocks; the rest by kind", () => {
    const root = document.createElement("div");
    root.innerHTML = `
      <div data-desk-window="w_book"><p data-span-id="s1">one</p><p data-span-id="s2">two</p>
        <span data-annotation-id="ann_1" data-annotation-kind="note">n</span><span data-annotation-id="hl_1" data-annotation-kind="highlight">h</span>
        <div data-figures-under="s2"><figure data-figure="f1"></figure></div></div>
      <div data-desk-window="w_pad"><div data-block="b1"></div><div data-block="b2"></div></div>`;
    const visible = visibleNow(root, [
      { windowId: "w_book", kind: "source", content: { kind: "source", extractionId: "ext_book" } },
      { windowId: "w_pad", kind: "pad_stack", content: null },
      { windowId: "w_far", kind: "lesson", content: { kind: "lesson" } },
    ], { companionOpen: true, companionExchangeIds: ["qe_1"], previewWindowIds: [] });
    expect(visible.windows).toEqual([
      { windowId: "w_book", kind: "source", extractionId: "ext_book", spanIds: ["s1", "s2"], noteIds: ["ann_1"], figures: [{ figureId: "f1", spanId: "s2" }] },
      { windowId: "w_pad", kind: "pad_stack", padBlockIds: ["b1", "b2"] },
      { windowId: "w_far", kind: "lesson" },
    ]);
    expect(visible.companionOpen).toBe(true);
  });
});

describe("the store", () => {
  it("opens one administration with what is visible, refuses a second in plain words, and says the server's refusals", async () => {
    const { desk, calls } = fake();
    desk.readings(["ext_book"]);
    await flush();
    expect(desk.dueAt("ext_book", "s1").map((check) => check.commitmentId)).toEqual(["cm_1"]);
    const visible = { windows: [{ windowId: "w_pad", kind: "pad_stack" }] };
    expect(await desk.begin("cm_1", "s_1", visible)).toBe(true);
    expect(calls.begin).toEqual([{ requestId: "creq_1", commitmentId: "cm_1", sessionId: "s_1", visible }]);
    expect(desk.holding()).toBe(true);
    expect(desk.open()?.host).toEqual({ extractionId: "ext_book", sectionId: "sec_1", spanId: "s1" });
    expect(desk.heldReason()).toBe("after your check · it is open on this desk");
    expect(await desk.begin("cm_2", "s_1", visible)).toBe(false);
    expect(desk.notice).toBe("another check is open · answer it or say not now first");
    expect(calls.begin).toHaveLength(1);
    const refused = fake({ begin: vi.fn(async () => { throw { code: "being_answered_in_today", message: "x" }; }) });
    expect(await refused.desk.begin("cm_1", "s_1", visible)).toBe(false);
    expect(refused.desk.notice).toBe("this check is being answered in Today");
    // With no practice session yet, the server picks one (none is named).
    const fresh = fake();
    expect(await fresh.desk.begin("cm_1", null, visible)).toBe(true);
    expect(fresh.calls.begin).toEqual([{ requestId: "creq_1", commitmentId: "cm_1", visible }]);
  });

  it("asks protect_more only when the view changed, adds the new veils, and records an opened veil at once", async () => {
    const { desk, calls } = fake();
    const visible = { windows: [] };
    await desk.begin("cm_1", "s_1", visible);
    await desk.protectMore(visible);
    expect(calls.protectMore).toBeUndefined();
    await desk.protectMore({ windows: [], companionOpen: true });
    expect(calls.protectMore).toHaveLength(1);
    expect(desk.veils().map((ref) => ref.kind)).toEqual(["window", "span", "companion"]);
    await desk.expose(PAD);
    expect(calls.expose).toEqual([{ administrationToken: "cad_1", ref: PAD, kind: "opened_veil" }]);
    expect(desk.veils().map((ref) => ref.kind)).toEqual(["span", "companion"]);
    expect(desk.open()?.looked).toEqual(["pads"]);
    expect(desk.open()?.coldNow).toBe(false);
  });

  it("submits once per administration (a retry is the same submission), keeps the answer on a failure, and lifts the veils after", async () => {
    let fail = true;
    const { desk, calls } = fake({ submit: vi.fn(async (input) => {
      if (fail) throw { message: "offline" };
      return { administrationToken: input.administrationToken, attemptId: "at_1", cold: false, reason: "primed" as const };
    }) });
    await desk.begin("cm_1", "s_1", { windows: [] });
    desk.setAnswer("p_k - [k = y]");
    await desk.submit();
    expect(desk.open()?.phase).toBe("open");
    expect(desk.open()?.error).toContain("it is kept here");
    expect(desk.open()?.answer).toBe("p_k - [k = y]");
    fail = false;
    await desk.submit();
    expect(desk.open()?.phase).toBe("answered");
    expect(desk.reason()).toBe("primed");
    expect(desk.veils()).toEqual([]);
    expect(desk.holding()).toBe(false);
    void calls;
    desk.close();
    expect(desk.open()).toBeNull();
  });

  it("not now closes with no attempt; a restart reopens the open card; later folds a marker for the session", async () => {
    const { desk, transport } = fake({ openInline: vi.fn(async () => ({ administration: card({ administrationToken: "cad_9" }) })) });
    desk.restart();
    desk.restart();
    await flush();
    expect(transport.openInline).toHaveBeenCalledTimes(1);
    expect(desk.open()?.card.administrationToken).toBe("cad_9");
    await desk.abandon();
    expect(transport.abandon).toHaveBeenCalledWith({ administrationToken: "cad_9" });
    expect(desk.open()).toBeNull();
    desk.defer("cm_1");
    expect(desk.deferred("cm_1")).toBe(true);
  });
});

describe("the veils in the page", () => {
  function page() {
    const root = document.createElement("div");
    root.innerHTML = `<div data-desk-window="w_pad"><div class="desk-pane-head">pad</div><div data-desk-pane-body="" class="desk-pane-body">p_k − 1</div></div>
      <div data-desk-window="w_book"><p data-span-id="s1">plain</p><p data-span-id="s2" class="p">the answer</p></div>`;
    document.body.appendChild(root);
    return root;
  }

  it("mark exactly what is named (not the head), say where each pill goes, and lift what is no longer veiled", () => {
    const root = page();
    const pills = applyVeils(root, [PAD, SPAN]);
    expect(pills.map((pill) => pill.ref.kind)).toEqual(["window", "span"]);
    const body = root.querySelector("[data-desk-pane-body]")!;
    expect(body.className).toContain("veiled");
    expect(body.getAttribute("data-veil")).toBe(VEIL_LABEL);
    expect(root.querySelector(".desk-pane-head")!.className).not.toContain("veiled");
    expect(root.querySelector('[data-span-id="s1"]')!.className).toBe("");
    applyVeils(root, [SPAN]);
    expect(body.className).not.toContain("veiled");
    expect(body.className).toContain("unveil");
    root.remove();
  });

  it("marks again an element a re-render rewrote, and opens a veil only after saying what it can cost", async () => {
    const { desk, transport } = fake();
    await desk.begin("cm_1", "s_1", { windows: [] });
    function Page() {
      const [n, setN] = useState(0);
      return (
        <div>
          <div data-desk-window="w_book"><p data-span-id="s2" className={`p n${n}`}>the answer</p></div>
          <button type="button" onClick={() => setN((value) => value + 1)}>rerender</button>
          <VeilLayer desk={desk} root={document} />
        </div>
      );
    }
    render(<Page />);
    await flush();
    const span = document.querySelector('[data-span-id="s2"]')!;
    expect(span.className).toContain("veiled");
    fireEvent.click(screen.getByText("rerender"));
    await flush();
    expect(span.className).toContain("n1");
    expect(span.className).toContain("veiled");
    const pills = screen.getAllByText(VEIL_LABEL);
    fireEvent.click(pills[0]);
    expect(screen.getByRole("dialog", { name: "show it anyway?" }).textContent).toContain(SHOW_ANYWAY_COST);
    expect(transport.expose).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("keep it hidden"));
    expect(transport.expose).not.toHaveBeenCalled();
    fireEvent.click(screen.getAllByText(VEIL_LABEL)[0]);
    fireEvent.click(screen.getByText("show it"));
    await flush();
    expect(transport.expose).toHaveBeenCalledWith({ administrationToken: "cad_1", ref: SPAN, kind: "opened_veil" });
    expect(span.className).not.toContain("veiled");
  });
});

describe("the cards", () => {
  it("the closed marker says no question, no topic and no provenance; check now and later", async () => {
    const { desk } = fake();
    desk.readings(["ext_book"]);
    await flush();
    const onCheckNow = vi.fn();
    render(<CheckMarker checks={desk.dueAt("ext_book", "s1")} desk={desk} onCheckNow={onCheckNow} />);
    const marker = document.querySelector('[data-check-marker="cm_1"]')!;
    expect(marker.textContent).toContain("a check is due before this page · on your own");
    expect(marker.textContent).not.toContain("lo_1");
    expect(marker.textContent).not.toContain("∂");
    fireEvent.click(screen.getByText("check now"));
    expect(onCheckNow).toHaveBeenCalledWith("cm_1");
    fireEvent.click(screen.getByText("later"));
    expect(document.querySelector("[data-check-folded]")).toBeTruthy();
  });

  it("the open card takes the answer, sends it with ↵, and says the reason in plain words after", async () => {
    const { desk, transport } = fake({ submit: vi.fn(async () => ({ administrationToken: "cad_1", attemptId: "at_1", cold: false, reason: "already_answered" as const })) });
    await desk.begin("cm_1", "s_1", { windows: [] });
    render(<CheckCardInline desk={desk} />);
    expect(document.querySelector('[data-check-card="inline"]')!.textContent).toContain("veiled while you answer · pads · source passages");
    const box = screen.getByLabelText("your answer");
    fireEvent.change(box, { target: { value: "p_k" } });
    fireEvent.keyDown(box, { key: "Enter" });
    await flush();
    expect(transport.submit).toHaveBeenCalledWith({ administrationToken: "cad_1", submissionId: "csub_2", answerMd: "p_k" });
    const answered = document.querySelector('[data-check-phase="answered"]')!;
    expect(answered.textContent).toContain("› your answer · just now · counts as practice");
    expect(document.querySelector('[data-check-reason="already_answered"]')!.textContent).toBe(REASON_WORDS.already_answered);
    expect(answered.textContent).toContain("2 things were veiled while you answered");
  });

  it("the card centred near the top has not now, and closes the administration with it", async () => {
    const { desk, transport } = fake();
    await desk.begin("cm_1", "s_1", { windows: [] });
    render(<CheckCardOverlay desk={desk} />);
    expect(screen.getByRole("dialog", { name: "a check on your own" })).toBeTruthy();
    fireEvent.click(screen.getByText("not now"));
    await flush();
    expect(transport.abandon).toHaveBeenCalled();
    expect(document.querySelector('[data-check-card="overlay"]')).toBeNull();
  });
});

describe("what comes into view during a check", () => {
  it("a window that opens is veiled whole at once, not openable, until the server has judged it", async () => {
    let answer!: (value: { veilAdditions: CheckVeilRefDto[] }) => void;
    const { desk } = fake({ protectMore: vi.fn(() => new Promise<{ veilAdditions: CheckVeilRefDto[] }>((resolve) => { answer = resolve; })) });
    await desk.begin("cm_1", "s_1", { windows: [{ windowId: "w_book", kind: "source", extractionId: "ext_book" }] });
    const asked = desk.protectMore({ windows: [{ windowId: "w_book", kind: "source", extractionId: "ext_book" }, { windowId: "w_new", kind: "lesson" }] });
    const arriving = desk.veils().find((ref) => ref.window_id === "w_new")!;
    expect(arriving).toMatchObject({ kind: "window", group: "just opened" });
    expect(desk.arrivingVeil(arriving)).toBe(true);
    answer({ veilAdditions: [{ group: "lessons", kind: "window", window_id: "w_new" }] });
    await asked;
    expect(desk.veils().filter((ref) => ref.window_id === "w_new").map((ref) => ref.group)).toEqual(["lessons"]);
    // The same window showing another reading is judged again.
    void desk.protectMore({ windows: [{ windowId: "w_book", kind: "source", extractionId: "ext_other" }, { windowId: "w_new", kind: "lesson" }] });
    expect(desk.veils().some((ref) => ref.window_id === "w_book" && ref.group === "just opened")).toBe(true);
  });

  it("after a restart the card finds its host passage once the reading's due checks name it", async () => {
    const { desk } = fake({ openInline: vi.fn(async () => ({ administration: card() })) });
    desk.restart();
    await flush();
    expect(desk.open()?.host).toBeNull();
    desk.readings(["ext_book"]);
    await flush();
    expect(desk.open()?.host).toEqual({ extractionId: "ext_book", sectionId: "sec_1", spanId: "s1" });
  });
});

describe("opening one of your notes", () => {
  const NOTE: CheckVeilRefDto = { group: "notes", kind: "note", window_id: "w_book", note_id: "ann_1" };

  it("says before it opens that a note always makes the answer practice (its words are never read)", async () => {
    const { desk } = fake({ begin: vi.fn(async () => card({ protection: { veilSetId: "v", method: "m", veiled: [NOTE, SPAN], opened: [], groups: ["notes"] } })) });
    await desk.begin("cm_1", "s_1", { windows: [] });
    document.body.innerHTML = `<div data-desk-window="w_book"><span data-annotation-id="ann_1">n</span><p data-span-id="s2">the answer</p></div>`;
    render(<VeilLayer desk={desk} root={document} />);
    await flush();
    const pills = screen.getAllByText(VEIL_LABEL);
    fireEvent.click(pills[0]);
    expect(screen.getByRole("dialog", { name: "show it anyway?" }).textContent).toContain(SHOW_NOTE_COST);
    fireEvent.click(screen.getByText("keep it hidden"));
    fireEvent.click(screen.getAllByText(VEIL_LABEL)[1]);
    expect(screen.getByRole("dialog", { name: "show it anyway?" }).textContent).toContain(SHOW_ANYWAY_COST);
    expect(veilIsNote(NOTE)).toBe(true);
    expect(veilIsNote({ group: "pads", kind: "window", window_id: "w_pad" })).toBe(false);
    expect(veilIsNote({ group: "search results", kind: "search_row", row_kind: "note", ref_id: "n1" })).toBe(true);
  });

  it("the answered card says why in plain words when a note was opened", async () => {
    const { desk } = fake({ submit: vi.fn(async () => ({ administrationToken: "cad_1", attemptId: "at_1", cold: false, reason: "primed" as const, primedBy: "unmeasured_note" as const })) });
    await desk.begin("cm_1", "s_1", { windows: [] });
    render(<CheckCardInline desk={desk} />);
    fireEvent.change(screen.getByLabelText("your answer"), { target: { value: "p_k" } });
    fireEvent.keyDown(screen.getByLabelText("your answer"), { key: "Enter" });
    await flush();
    const line = document.querySelector('[data-check-reason="primed"]')!;
    expect(line.getAttribute("data-check-primed-by")).toBe("unmeasured_note");
    expect(line.textContent).toBe(PRIMED_BY_NOTE_WORDS);
  });
});

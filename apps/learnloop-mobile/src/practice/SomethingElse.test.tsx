// Instruct hand-off IH3 (spec_instruct_handoff_v1 §6) on the phone: one quiet link on feedback and on Today, only where the
// host says so; the options are the plan's own, in plain words; a choice is served (an item opens) or, for a lesson, kept and
// said plainly to wait on the desktop. Nothing here is a modal, and nothing is counted as knowing something.
import { findJargon } from "@desktop/copy/denyList";
import {
  answers, App, called, describe, expect, fireEvent, installFakeHost, it, render, screen, waitFor
} from "../test/fakeHost";

installFakeHost();

const block = {
  id: "b1", ordinal: 1, lane: "maintain", action: "maintain", subtype: null, chosenBy: "lane_quota", why: "These are due today.",
  whyKind: null, whyDetails: null, fallback: false, estMinutes: 5, status: "current", startedAt: null, endedAt: null, outcome: null,
  reading: null, learningObjectTitles: ["Topic i1"], displacedCount: 0,
  items: [{ practiceItemId: "i1", learningObjectId: "lo", learningObjectTitle: "Topic i1", practiceMode: null, promptPreview: "", lane: "maintain",
    estMinutes: 2.5, state: "planned", origin: "chooser", servedAt: null, doneAt: null }]
};
const plan = {
  id: "p1", localDate: "2026-11-08", kind: "normal", status: "open", stopReason: null, parentPlanId: null, minutesBudget: 25, rememberedMinutes: 25,
  minutesSource: "carried", minuteChoices: [10, 25, 40], minutesLeft: 25,
  split: { rule: "r", line: "", lanesAllowed: ["maintain"], requestedMinutes: 0, lanes: [] }, admission: {}, blocks: [block],
  currentBlockId: "b1", deciding: false, waiting: null, projected: [], blockCountEstimate: 1, firstBlock: null, nextStep: null,
  totals: {}, reentry: null, source: "s", chooser: "c", estimatorVersion: "e", algorithmVersion: "a"
};
const reply = (rest: Record<string, unknown> = {}) => ({
  version: 1, enabled: true, headlineEnabled: false, localDate: "2026-11-08", plan,
  day: { plans: 1, kinds: ["normal"], complete: false, actualMinutes: 0, plannedItems: 1, readingBlocks: 0 }, streak: null,
  device: { surface: "phone_plan", deferredCount: 0, readingsWaiting: 0 }, ...rest
});
const itemStep = (id = "i1") => ({
  kind: "item", planId: "p1", blockId: "b1", practiceItemId: id, learningObjectId: "lo", learningObjectTitle: `Topic ${id}`, origin: "chooser",
  schedulerCandidateId: `cand_${id}`, presentationId: `pp_${id}`, boundary: false
});
const OPTIONS = {
  version: 1, enabled: true, drawn: false, decisionId: null, device: "phone",
  options: [
    { kind: "question", ref: "cand_q", label: "Another question", minutes: 5, propensity: null, plansPick: false, servable: true },
    { kind: "review", ref: "cand_r", label: "Review something from earlier", minutes: 4, propensity: null, plansPick: false, servable: true },
    { kind: "lesson", ref: "lesson_offer:lo", label: "Learn Eigenvalues", minutes: 15, propensity: null, plansPick: false, servable: false },
    { kind: "stop", ref: "stop_for_today", label: "Stop for today", minutes: null, propensity: null, plansPick: false, servable: true }
  ]
};

async function toFeedback(flag: boolean) {
  // As the real host: every plan reply says it, the read's and the step's.
  const line = flag ? { somethingElse: true } : {};
  answers.get_daily_plan = reply(line);
  answers.next_plan_item = reply({ step: itemStep(), ...line });
  answers.plan_something_else_options = OPTIONS;
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Begin" }));
  await screen.findByText("Define it.");
  const editor = screen.getByRole("textbox", { name: "Your answer" });
  editor.textContent = "My answer";
  fireEvent.input(editor);
  fireEvent.click(screen.getByRole("button", { name: "Submit" }));
  await screen.findByText("3 / 4");
}

describe("the quiet link on the phone's feedback", () => {
  // Review B1. A plan read at a finished block crosses the boundary and writes its decision (spec_mobile_frontend_v2 §4.5),
  // so the link must take the flag from the plan the phone already holds, whatever the flag says.
  it.each([[true], [false]])("feedback reads no plan (flag %s): the link is decided from the plan already held", async (flag) => {
    answers.get_daily_plan = reply(flag ? { somethingElse: true } : {});
    answers.next_plan_item = reply({ step: itemStep(), ...(flag ? { somethingElse: true } : {}) });
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Begin" }));
    await screen.findByText("Define it.");
    const before = called("get_daily_plan").length;
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = "My answer";
    fireEvent.input(editor);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText("3 / 4");
    await waitFor(() => expect(called("plan_prefetch").length).toBeGreaterThan(0));
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(called("get_daily_plan").length).toBe(before);
    expect(screen.queryByTestId("something-else-link") !== null).toBe(flag);
  });

  it("is absent unless the host says it may show, and the plan is as it was", async () => {
    await toFeedback(false);
    expect(screen.queryByTestId("something-else-link")).toBeNull();
    expect(called("plan_something_else_options")).toEqual([]);
  });

  it("opens in place with the plan's own options in plain words, and writes nothing until one is chosen", async () => {
    await toFeedback(true);
    fireEvent.click(await screen.findByTestId("something-else-link"));
    const panel = await screen.findByTestId("something-else-panel");
    expect(panel.getAttribute("role")).not.toBe("dialog");
    await screen.findByTestId("something-else-option-question");
    expect(screen.getByTestId("something-else-option-review").textContent).toBe("Review something from earlier");
    // a lesson is offered, and plainly marked as the desktop's
    expect(screen.getByTestId("something-else-option-lesson").textContent).toBe("Learn Eigenvalues (on the desktop)");
    expect(called("plan_something_else_options")[0].params).toEqual({ sessionId: "s1" });
    expect(called("plan_something_else")).toEqual([]);
    expect(findJargon(panel.textContent ?? "")).toEqual([]);
    expect(panel.textContent).toContain("It isn't counted as knowing something.");
  });

  it("serves a question the phone can show: the choice, its note and its own key go to the host, and the item opens", async () => {
    await toFeedback(true);
    fireEvent.click(await screen.findByTestId("something-else-link"));
    await screen.findByTestId("something-else-option-question");
    fireEvent.change(screen.getByTestId("something-else-panel").querySelector("textarea") as HTMLTextAreaElement,
      { target: { value: "  a harder one  " } });
    answers.plan_something_else = {
      ...reply({ step: itemStep("i2") }),
      preference: { id: "k", outcome: "served", kind: "question", ref: "cand_q", servedDecisionId: "d1", lesson: null, replayed: false }
    };
    fireEvent.click(screen.getByTestId("something-else-option-question"));
    await waitFor(() => expect(called("plan_something_else")).toHaveLength(1));
    const sent = called("plan_something_else")[0].params;
    expect(sent).toMatchObject({
      sessionId: "s1", kind: "question", ref: "cand_q", surface: "phone_feedback", attemptId: "a1", noteMd: "a harder one"
    });
    expect(String(sent.preferenceId).length).toBeGreaterThan(8);
    await screen.findByText("Define it.");
  });

  it("keeps a lesson pick and says plainly that the lesson waits on the desktop", async () => {
    await toFeedback(true);
    fireEvent.click(await screen.findByTestId("something-else-link"));
    await screen.findByTestId("something-else-option-lesson");
    answers.plan_something_else = {
      ...reply(),
      preference: { id: "k", outcome: "waits_on_desktop", kind: "lesson", ref: "lesson_offer:lo", servedDecisionId: "d1", lesson: null, replayed: false }
    };
    fireEvent.click(screen.getByTestId("something-else-option-lesson"));
    const saved = await screen.findByTestId("something-else-saved");
    expect(saved.textContent).toBe("Learn Eigenvalues is a lesson, and lessons wait on the desktop. Your choice is saved.");
    expect(called("plan_something_else")[0].params).toMatchObject({ kind: "lesson", ref: "lesson_offer:lo", surface: "phone_feedback" });
    // nothing opened: feedback is still here, with its Next
    expect(screen.getByRole("button", { name: "Next" })).toBeTruthy();
    expect(findJargon(saved.textContent ?? "")).toEqual([]);
  });

  it("a failed send keeps the same key, so trying again writes once", async () => {
    await toFeedback(true);
    fireEvent.click(await screen.findByTestId("something-else-link"));
    await screen.findByTestId("something-else-option-question");
    answers.plan_something_else = { status: 500, body: { ok: false, error: { code: "internal", message: "NOT SAVED", retryable: false } } };
    fireEvent.click(screen.getByTestId("something-else-option-question"));
    await waitFor(() => expect(called("plan_something_else")).toHaveLength(1));
    answers.plan_something_else = {
      ...reply({ step: itemStep("i2") }),
      preference: { id: "k", outcome: "served", kind: "question", ref: "cand_q", servedDecisionId: "d1", lesson: null, replayed: false }
    };
    await waitFor(() => expect((screen.getByTestId("something-else-option-question") as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(screen.getByTestId("something-else-option-question"));
    await waitFor(() => expect(called("plan_something_else")).toHaveLength(2));
    const [first, second] = called("plan_something_else");
    expect(second.params.preferenceId).toBe(first.params.preferenceId);
  });

  it("a failed send then a different option is a new act with its own key", async () => {
    await toFeedback(true);
    fireEvent.click(await screen.findByTestId("something-else-link"));
    await screen.findByTestId("something-else-option-question");
    answers.plan_something_else = { status: 500, body: { ok: false, error: { code: "internal", message: "NOT SAVED", retryable: false } } };
    fireEvent.click(screen.getByTestId("something-else-option-question"));
    await waitFor(() => expect(called("plan_something_else")).toHaveLength(1));
    await waitFor(() => expect((screen.getByTestId("something-else-option-question") as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(screen.getByTestId("something-else-option-lesson"));
    await waitFor(() => expect(called("plan_something_else")).toHaveLength(2));
    const [first, second] = called("plan_something_else");
    expect(second.params.kind).toBe("lesson");
    expect(second.params.preferenceId).not.toBe(first.params.preferenceId);
  });
});

describe("the quiet link on the phone's Today", () => {
  it("shows beside Next once a session is open, with the phone_today surface", async () => {
    answers.get_daily_plan = reply({ somethingElse: true });
    answers.next_plan_item = reply({ step: itemStep(), somethingElse: true });
    answers.plan_something_else_options = OPTIONS;
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Begin" }));
    await screen.findByText("Define it.");
    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    const link = await screen.findByTestId("something-else-link");
    expect(link.textContent).toBe("Something else would help");
  });
});

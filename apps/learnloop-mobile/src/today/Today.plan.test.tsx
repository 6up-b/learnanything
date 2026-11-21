// Mobile v2 V2, J1/J4/J5/J6 through the fake host: Today is the shared plan (owner decision D1),
// Next serves the plan's step under the phone's origin, what the phone can't show waits for the
// desktop and is counted, the stop offer goes both ways, and a randomized check offers no help.
import { findJargon } from "@desktop/copy/denyList";
import { MORE_AS_YOU_READ, NO_QUESTIONS_YET, QUESTIONS_FROM_READING } from "@desktop/app/todayCause";
import {
  answers, App, cacheSessionId, called, cleanup, describe, expect, fakeFetch, feedback, fireEvent, getAnswers, installFakeHost, it, item, render,
  screen, session, vi, waitFor
} from "../test/fakeHost";

installFakeHost();

const block = (extra: Record<string, unknown> = {}) => ({
  id: "b1", ordinal: 1, lane: "maintain", action: "maintain", subtype: null, chosenBy: "lane_quota", why: "These are due today.",
  whyKind: null, whyDetails: null, fallback: false, estMinutes: 5, status: "current", startedAt: null, endedAt: null, outcome: null,
  reading: null, learningObjectTitles: ["Topic i1"], displacedCount: 0,
  items: [{ practiceItemId: "i1", learningObjectId: "lo", learningObjectTitle: "Topic i1", practiceMode: null, promptPreview: "", lane: "maintain",
    estMinutes: 2.5, state: "planned", origin: "chooser", servedAt: null, doneAt: null }],
  ...extra
});
const plan = (extra: Record<string, unknown> = {}) => ({
  id: "p1", localDate: "2026-11-06", kind: "normal", status: "open", stopReason: null, parentPlanId: null, minutesBudget: 25, rememberedMinutes: 25,
  minutesSource: "carried", minuteChoices: [10, 25, 40], minutesLeft: 25,
  split: { rule: "r", line: "", lanesAllowed: ["maintain"], requestedMinutes: 0, lanes: [] }, admission: {}, blocks: [block()],
  currentBlockId: "b1", deciding: false, waiting: null, projected: [], blockCountEstimate: 1, firstBlock: null, nextStep: null,
  totals: {}, reentry: null, source: "s", chooser: "c", estimatorVersion: "e", algorithmVersion: "a", ...extra
});
const reply = (planExtra: Record<string, unknown> = {}, rest: Record<string, unknown> = {}) => ({
  version: 1, enabled: true, headlineEnabled: false, localDate: "2026-11-06", plan: plan(planExtra),
  day: { plans: 1, kinds: ["normal"], complete: false, actualMinutes: 0, plannedItems: 1, readingBlocks: 0 }, streak: null,
  device: { surface: "phone_plan", deferredCount: 0, readingsWaiting: 0 }, ...rest
});
const itemStep = (id = "i1", origin = "chooser") => ({
  kind: "item", planId: "p1", blockId: "b1", practiceItemId: id, learningObjectId: "lo", learningObjectTitle: `Topic ${id}`, origin,
  schedulerCandidateId: `cand_${id}`, presentationId: `pp_${id}`, boundary: false
});
const held = (count: number) => ({ kind: "held_for_desktop", planId: "p1", heldCount: count, heldReadings: 0, firstHeldItemId: "i9" });

async function beginPlan() {
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Begin" }));
  await screen.findByText("Define it.");
}

/** Spec_instruct_handoff_v1 §3a: while feedback shows, the next boundary's model calls start, so Next finds their answer. */
describe("the plan's prefetch while feedback shows", () => {
  async function answerOne() {
    answers.get_daily_plan = reply();
    answers.next_plan_item = reply({}, { step: itemStep() });
    await beginPlan();
    expect(called("plan_prefetch")).toEqual([]);
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = "My answer";
    fireEvent.input(editor);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
  }

  it("starts once the grade is on screen, not before, and only names the session", async () => {
    await answerOne();
    await screen.findByText("3 / 4");
    await waitFor(() => expect(called("plan_prefetch")).toHaveLength(1));
    expect(called("plan_prefetch")[0].params).toEqual({ sessionId: "s1" });
    expect(called("next_plan_item")).toHaveLength(1);
  });

  it("ignores a failed call: no error shows, and Next still serves", async () => {
    answers.plan_prefetch = { status: 500, body: { ok: false, error: { code: "internal", message: "PREFETCH BROKE", retryable: false } } };
    await answerOne();
    await screen.findByText("3 / 4");
    await waitFor(() => expect(called("plan_prefetch")).toHaveLength(1));
    expect(screen.queryByText(/PREFETCH BROKE/)).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
    answers.next_plan_item = reply({}, { step: itemStep("i2") });
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() => expect(called("next_plan_item")).toHaveLength(2));
  });

  it("waits for a pending diagnosis: what it finds can change the decision", async () => {
    answers.get_feedback = { ...feedback(), diagnosisStatus: "pending" };
    await answerOne();
    await screen.findByText("3 / 4");
    await screen.findByText(/Looking into what happened here/);
    expect(called("plan_prefetch")).toEqual([]);
  });

  it("stays out while this miss's question is coming: Next isn't a plan boundary then", async () => {
    answers.get_feedback = {
      ...feedback(),
      followup: { workflowId: "w1", state: "pending", held: false, line: "Preparing a question on this…", canShowAnyway: false, canContinueWithout: true, shownAnyway: false }
    };
    await answerOne();
    await screen.findByText("3 / 4");
    await screen.findByText(/Preparing a question on this/);
    expect(called("plan_prefetch")).toEqual([]);
  });
});

describe("a question in progress on the desktop (IH6)", () => {
  it("says so, and the phone's Next still serves: an explicit step decides", async () => {
    cacheSessionId("s1");
    answers.get_session = session();
    answers.get_daily_plan = reply({ blocks: [], currentBlockId: null, projected: [], questionInProgress: { workbenchSessionId: "wb", practiceItemId: "pi", learningObjectTitle: "ReLU" } });
    answers.next_plan_item = reply({}, { step: itemStep() });
    render(<App />);
    const line = await screen.findByTestId("today-in-progress");
    expect(line.textContent).toContain("A question is in progress on the desktop.");
    expect(findJargon(line.textContent ?? "")).toEqual([]);
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() => expect(called("next_plan_item")).toHaveLength(1));
    expect(called("next_plan_item")[0].params).toMatchObject({ sessionId: "s1", serve: true });
  });

  it("shows no such line otherwise", async () => {
    cacheSessionId("s1");
    answers.get_session = session();
    answers.get_daily_plan = reply();
    render(<App />);
    await screen.findByTestId("today-sentence");
    expect(screen.queryByTestId("today-in-progress")).toBeNull();
  });
});

describe("Today is the plan (J1)", () => {
  it("says the plan in one sentence, and Begin starts a session and serves the plan's step", async () => {
    answers.get_daily_plan = reply();
    answers.next_plan_item = reply({}, { step: itemStep() });
    render(<App />);
    expect(await screen.findByText(/^Up to 25 minutes today\. First: 1 short question from earlier days\./)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Begin" }));
    await screen.findByText("Define it.");
    expect(called("start_session")[0].params).toEqual({ availableMinutes: 25 });
    const next = called("next_plan_item")[0];
    expect(next.params).toEqual({ sessionId: "s1", serve: true });
    expect(next.requestId).toBeTruthy();
    expect(called("get_today_queue")).toEqual([]);
  });

  it("binds the answer to the plan's presentation", async () => {
    answers.get_daily_plan = reply();
    answers.next_plan_item = reply({}, { step: itemStep() });
    await beginPlan();
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = "My answer";
    fireEvent.input(editor);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText("3 / 4");
    expect(called("submit_attempt")[0].params.planPresentationId).toBe("pp_i1");
  });

  it("Feedback's Next is the plan's; what waits for the desktop is counted, and Skip skips the first of it", async () => {
    answers.get_daily_plan = reply();
    let steps = 0;
    answers.next_plan_item = () => (++steps === 1 ? reply({}, { step: itemStep() }) : reply({}, { step: held(2), device: { surface: "phone_plan", deferredCount: 2, readingsWaiting: 0 } }));
    await beginPlan();
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = "My answer";
    fireEvent.input(editor);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText("3 / 4");
    // The host's read now says the same: its next step is held (the read never crosses past it).
    answers.get_daily_plan = reply({ nextStep: held(2) }, { device: { surface: "phone_plan", deferredCount: 2, readingsWaiting: 0 } });
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(await screen.findByText("2 questions are waiting for the desktop.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Skip it" }));
    await waitFor(() => expect(called("next_plan_item").length).toBe(3));
    expect(called("next_plan_item")[2].params).toEqual({ sessionId: "s1", serve: true, skipPracticeItemId: "i9" });
  });

  it("Feedback has a back chevron to Today, which serves nothing", async () => {
    answers.get_daily_plan = reply();
    answers.next_plan_item = reply({}, { step: itemStep() });
    await beginPlan();
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = "My answer";
    fireEvent.input(editor);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText("3 / 4");
    const before = called("next_plan_item").length;
    fireEvent.click(screen.getByRole("button", { name: "Back to Today" }));
    await screen.findByRole("button", { name: "Next" });
    expect(called("next_plan_item").length).toBe(before);
  });

  it("a minutes chip re-plans the rest before a session starts", async () => {
    answers.get_daily_plan = reply();
    answers.set_plan_minutes = reply({ minutesBudget: 40, rememberedMinutes: 40 });
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "40 min" }));
    await screen.findByText(/40 minutes today/);
    expect(called("set_plan_minutes")[0].params).toEqual({ minutes: 40, sessionId: null });
  });

  // UX fix stage 4 (audit F9 on the phone; phone-2 #22-54): "About 8 minutes left" read as a countdown and never moved.
  it("F9: a begun plan names its room, not a countdown, and the done line the time spent answering and reading", async () => {
    cacheSessionId("s1");
    answers.get_session = session();
    answers.get_daily_plan = reply({ blocks: [block({ id: "b0", status: "done" }), block()], minutesLeft: 8 });
    render(<App />);
    const sentence = await screen.findByTestId("today-sentence");
    await waitFor(() => expect(sentence.textContent).toMatch(/^Room for about 8 more minutes today\. Next: 1 short question from earlier days\./));
    expect(findJargon(sentence.textContent ?? "")).toEqual([]);
    cleanup();
    answers.get_daily_plan = reply(
      { status: "complete" },
      { day: { plans: 1, kinds: ["normal"], complete: true, actualMinutes: 12, plannedItems: 4, readingBlocks: 1 } }
    );
    render(<App />);
    expect(await screen.findByText("Done for today · 12 minutes spent answering and reading.")).toBeTruthy();
  });
});

describe("the stop offer (J5)", () => {
  it("offers Keep going and Done for today, and Done stops the plan and ends the session", async () => {
    answers.get_daily_plan = reply();
    answers.next_plan_item = reply({ status: "complete", stopReason: "A good place to stop." }, { step: { kind: "done", planId: "p1", status: "complete", stopReason: "A good place to stop." } });
    answers.plan_keep_going = (call: { params: Record<string, unknown> }) =>
      call.params.stop ? reply({ status: "stopped" }) : reply({ kind: "keep_going" });
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Begin" }));
    expect(await screen.findByText("Done for today.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Keep going" }));
    await waitFor(() => expect(called("plan_keep_going").length).toBe(1));
    expect(called("plan_keep_going")[0].params).toEqual({ sessionId: "s1" });
    // Kept going: the extension's plan is Today's now, its Next the primary action.
    expect(await screen.findByRole("button", { name: "Next" })).toBeTruthy();
  });

  it("Done for today sends the stop, then ends the session", async () => {
    answers.get_daily_plan = reply();
    answers.next_plan_item = reply({ status: "complete" }, { step: { kind: "done", planId: "p1", status: "complete", stopReason: "x" } });
    answers.plan_keep_going = reply({ status: "stopped" });
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Begin" }));
    fireEvent.click(await screen.findByRole("button", { name: "Done for today" }));
    await waitFor(() => expect(called("end_session").length).toBe(1));
    expect(called("plan_keep_going")[0].params).toEqual({ sessionId: "s1", stop: true });
  });

  it("a stop drawn while work waits for the desktop is offered too, and Keep going overrides it", async () => {
    // Codex re-review of V2, F7: the plan stays open for the held work; its held step carries the stop.
    const waitingDevice = { device: { surface: "phone_plan", deferredCount: 1, readingsWaiting: 0 } };
    answers.get_daily_plan = reply();
    answers.next_plan_item = reply({}, { step: { ...held(1), stopOffer: { stopReason: "A good place to stop." } }, ...waitingDevice });
    answers.plan_keep_going = reply({ minutesBudget: 35 }, { step: held(1), ...waitingDevice });
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Begin" }));
    expect(await screen.findByText("Done for today.")).toBeTruthy();
    expect(screen.getByText("1 question is waiting for the desktop.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Done for today" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Keep going" }));
    await waitFor(() => expect(called("plan_keep_going").length).toBe(1));
    expect(called("plan_keep_going")[0].params).toEqual({ sessionId: "s1" });
    // Overridden: the plan's Next is the primary action again, and nothing ended the session.
    expect(await screen.findByRole("button", { name: "Next" })).toBeTruthy();
    expect(called("end_session")).toEqual([]);
  });
});

describe("the router's visible decisions (J4)", () => {
  it("shows the plain line, its details in a sheet, and asks how it was chosen only when asked", async () => {
    answers.get_daily_plan = reply(
      { blocks: [block({ objectiveDecisionId: "rd1" })] },
      { routerDecision: { decisionId: "rd1", line: "Chosen to keep what you know fresh.", details: { cardSummary: "Card.", models: [], rationale: null, fallback: null } } }
    );
    answers.router_objective_explain = { version: 1, available: true, decisionId: "rd1", lines: ["The numeric policy chose this."] };
    render(<App />);
    expect(await screen.findByText("Chosen to keep what you know fresh.")).toBeTruthy();
    expect(called("router_objective_explain")).toEqual([]);
    fireEvent.click(screen.getByRole("button", { name: "details" }));
    expect(await screen.findByText("Card.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "how was this chosen?" }));
    expect(await screen.findByText("The numeric policy chose this.")).toBeTruthy();
    expect(called("router_objective_explain")[0].params).toEqual({ decisionId: "rd1" });
  });
});

describe("help on the phone (J16 partial) and the randomized check (J6)", () => {
  it("an item's own hint says what it changes first, is recorded, shown and counted at submit", async () => {
    answers.get_daily_plan = reply();
    answers.next_plan_item = reply({}, { step: itemStep() });
    answers.get_practice_item = { ...item(), hints: ["Think of the definition."] };
    answers["practice.record_hint_reveal"] = { recorded: true, reason: null, assistId: "ha1" };
    await beginPlan();
    fireEvent.click(screen.getByRole("button", { name: "Hint" }));
    expect(await screen.findByText(/counts as answered with help/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Show a hint" }));
    expect(await screen.findByText("Think of the definition.")).toBeTruthy();
    expect(screen.getByText("◌ with help")).toBeTruthy();
    await waitFor(() => expect(called("practice.record_hint_reveal").length).toBe(1));
    expect(called("practice.record_hint_reveal")[0].params).toMatchObject({ sessionId: "s1", practiceItemId: "i1", authoredIndex: 0 });
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = "My answer";
    fireEvent.input(editor);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText("3 / 4");
    expect(called("submit_attempt")[0].params).toMatchObject({ hintsUsed: 1, authoredHints: 1, planPresentationId: "pp_i1" });
  });

  it("the day's randomized check offers no help, and nothing says why", async () => {
    answers.get_daily_plan = reply();
    answers.next_plan_item = reply({}, { step: itemStep("i1", "randomized_check") });
    answers.get_practice_item = { ...item(), hints: ["Think of the definition."] };
    await beginPlan();
    expect(screen.queryByRole("button", { name: "Hint" })).toBeNull();
    expect(screen.queryByText(/check/i)).toBeNull();
  });

  it("a randomized check reopened from its checkpoint (a reload, another device) stays without help (Codex review F5)", async () => {
    cacheSessionId("s1");
    answers.get_daily_plan = reply();
    answers.get_session = session({ checkpoint: { currentPracticeItemId: "i1", currentAnswer: "half an answer", submissionId: "k1", hintsUsed: 0, focusBlockState: null, pendingGradingProposal: null } });
    getAnswers["/api/v1/submissions/k1"] = { state: "unknown" };
    // The serve says it is the day's check; nothing on the restored target does.
    answers.get_practice_item = { ...item(), hints: ["Think of the definition."], noHelp: true };
    render(<App />);
    const editor = await screen.findByRole("textbox", { name: "Your answer" });
    await waitFor(() => expect(editor.textContent).toContain("half an answer"));
    await screen.findByText("Define it.");
    expect(screen.queryByRole("button", { name: "Hint" })).toBeNull();
    expect(screen.queryByText(/check/i)).toBeNull();
    expect(called("practice.record_hint_reveal")).toEqual([]);
  });

  it("an ordinary question reopened from its checkpoint keeps its own hints", async () => {
    cacheSessionId("s1");
    answers.get_daily_plan = reply();
    answers.get_session = session({ checkpoint: { currentPracticeItemId: "i1", currentAnswer: "half an answer", submissionId: "k1", hintsUsed: 0, focusBlockState: null, pendingGradingProposal: null } });
    getAnswers["/api/v1/submissions/k1"] = { state: "unknown" };
    answers.get_practice_item = { ...item(), hints: ["Think of the definition."] };
    render(<App />);
    await screen.findByText("Define it.");
    expect(await screen.findByRole("button", { name: "Hint" })).toBeTruthy();
  });
});

// UX fix stage 4 (audit F19, P9; phone-2 #40-43): the Today tab, tapped from another place while a question was open,
// opened the question, and "Back to Today" opened the plan. The Today tab now always opens the plan, and a draft
// left there waits behind "Resume your answer", which brings it back as it was.
describe("the Today tab always opens the plan (F19)", () => {
  async function halfAnswer(text: string) {
    answers.get_daily_plan = reply();
    answers.next_plan_item = reply({}, { step: itemStep() });
    await beginPlan();
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = text;
    fireEvent.input(editor);
  }

  it("F19: from another place, the Today tab opens the plan with Resume your answer, which brings the draft back", async () => {
    await halfAnswer("Half an answer");
    const serves = called("next_plan_item").length;
    const opens = called("get_practice_item").length;
    fireEvent.click(screen.getByRole("button", { name: "Capture" }));
    await screen.findByLabelText("A thought, a problem or a link");
    fireEvent.click(screen.getByRole("button", { name: "Today" }));
    expect(await screen.findByTestId("today-sentence")).toBeTruthy();
    // The question is kept under the plan, out of sight (and out of reach of a screen reader).
    expect(screen.queryByRole("textbox", { name: "Your answer" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Submit" })).toBeNull();
    // The plan is Today's own screen: the tab bar is there, and no Back covers it.
    expect(screen.getByRole("navigation", { name: "Places" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Back to Today" })).toBeNull();
    const resume = screen.getByRole("button", { name: "Resume your answer" });
    expect(screen.getByRole("button", { name: "Next" })).toBeTruthy();
    expect(findJargon(resume.textContent ?? "")).toEqual([]);
    fireEvent.click(resume);
    await screen.findByText("Define it.");
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    expect(editor.textContent).toBe("Half an answer");
    // Neither leaving nor resuming served anything (M2a's F5: ordinary navigation keeps the draft, with no second serve).
    expect(called("next_plan_item").length).toBe(serves);
    expect(called("get_practice_item").length).toBe(opens);
    // Resumed, the answer goes to the same presentation it was served under.
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText("3 / 4");
    expect(called("submit_attempt")[0].params).toMatchObject({ practiceItemId: "i1", answerMd: "Half an answer", planPresentationId: "pp_i1" });
  });

  it("F19: Back to Today from a question with a draft offers Resume your answer too, which reopens it on the draft", async () => {
    await halfAnswer("Half an answer");
    const serves = called("next_plan_item").length;
    fireEvent.click(screen.getByRole("button", { name: "Back to Today" }));
    // Back saves the draft at once, as before.
    await waitFor(() => expect(called("save_practice_draft").at(-1)?.params).toMatchObject({ practiceItemId: "i1", answerMd: "Half an answer" }));
    fireEvent.click(await screen.findByRole("button", { name: "Resume your answer" }));
    const editor = await screen.findByRole("textbox", { name: "Your answer" });
    await waitFor(() => expect(editor.textContent).toBe("Half an answer"));
    expect(called("next_plan_item").length).toBe(serves);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText("3 / 4");
    expect(called("submit_attempt")[0].params).toMatchObject({ practiceItemId: "i1", answerMd: "Half an answer", planPresentationId: "pp_i1" });
  });

  it("F19: with nothing typed there is no draft to resume: the plan shows its Next only", async () => {
    await halfAnswer("");
    fireEvent.click(screen.getByRole("button", { name: "Capture" }));
    await screen.findByLabelText("A thought, a problem or a link");
    fireEvent.click(screen.getByRole("button", { name: "Today" }));
    expect(await screen.findByRole("button", { name: "Next" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Resume your answer" })).toBeNull();
  });

  it("F19: an answer on its way is not left: the Today tab shows it until its reply lands", async () => {
    await halfAnswer("My answer");
    let release: () => void = () => undefined;
    const held = new Promise<void>((resolve) => {
      release = resolve;
    });
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input) === "/rpc" && JSON.parse(init?.body as string).method === "submit_attempt") await held;
      return fakeFetch(input, init);
    }));
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Back to Today" }).hasAttribute("disabled")).toBe(true));
    fireEvent.click(screen.getByRole("button", { name: "Capture" }));
    await screen.findByLabelText("A thought, a problem or a link");
    fireEvent.click(screen.getByRole("button", { name: "Today" }));
    expect(await screen.findByText("Define it.")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Resume your answer" })).toBeNull();
    release();
    expect(await screen.findByText("3 / 4")).toBeTruthy();
  });
});

describe("plain words (ux §4.1, the desktop's deny-list)", () => {
  it("Today's plan, its held and done states, the hint sheet and the feedback's new parts say nothing from the list", async () => {
    const texts: string[] = [];
    answers.get_daily_plan = reply(
      { blocks: [block({ whyDetails: "Chosen from what is due.", objectiveDecisionId: "rd1" })] },
      { routerDecision: { decisionId: "rd1", line: "Chosen to keep what you know fresh.", details: { cardSummary: null, models: [], rationale: null, fallback: null } },
        device: { surface: "phone_plan", deferredCount: 2, readingsWaiting: 1 } }
    );
    answers.next_plan_item = reply({}, { step: itemStep() });
    answers.get_practice_item = { ...item(), hints: ["Think of the definition."] };
    answers.get_feedback = {
      ...feedback(), answeredExpectedAnswer: "The whole answer.",
      followup: { workflowId: "w", state: "pending", held: true, line: "Preparing a question on this…", canShowAnyway: true, canContinueWithout: true, shownAnyway: false }
    };
    answers.followup_status = { enabled: false };
    render(<App />);
    await screen.findByText(/questions and a reading are waiting for the desktop/);
    texts.push(document.body.textContent ?? "");
    fireEvent.click(screen.getByRole("button", { name: "Begin" }));
    await screen.findByText("Define it.");
    fireEvent.click(screen.getByRole("button", { name: "Hint" }));
    await screen.findByText(/counts as answered with help/);
    texts.push(document.body.textContent ?? "");
    fireEvent.click(screen.getByRole("button", { name: "Show a hint" }));
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = "My answer";
    fireEvent.input(editor);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText("Preparing a question on this…");
    texts.push(document.body.textContent ?? "");
    cleanup();
    answers.get_daily_plan = reply({ status: "complete" });
    render(<App />);
    await screen.findByText("Done for today.");
    texts.push(document.body.textContent ?? "");
    expect(texts.flatMap((text) => findJargon(text))).toEqual([]);
  });
});

describe("first questions arrive (P11): an empty day says why, in the desktop's words", () => {
  const empty = () => reply({ status: "complete", blocks: [], currentBlockId: null },
    { day: { plans: 1, kinds: ["normal"], complete: true, actualMinutes: 0, plannedItems: 0, readingBlocks: 0 } });
  const facts = (extra: Record<string, unknown> = {}) => ({
    count: 0, itemIds: [], sections: [], writing: [], failed: [], toLookAt: 0, sectionCount: 4, ...extra
  });
  const book = (statusLine: Record<string, unknown>) => ({
    sources: [{ sourceId: "src_sym", title: "Symmetric Matrices and Variance", readiness: "ready", readerEnabled: true, extractionId: "ext_1", statusLine }]
  });
  const built = (questions = facts()) => ({ text: "Questions for Ch. 1 come up as you read", tone: "quiet", action: null, details: null, questions });

  it("a built book with no section finished: the rule that brings the first questions, under Nothing planned, and Keep going stays", async () => {
    answers.get_daily_plan = empty();
    answers.get_source_library = book(built());
    render(<App />);
    expect((await screen.findByTestId("today-cause")).textContent).toBe(
      `Read “Symmetric Matrices and Variance” for your first questions. ${QUESTIONS_FROM_READING}`
    );
    expect(screen.getByTestId("today-sentence").textContent).toBe("Nothing planned for today.");
    expect(screen.getByRole("button", { name: "Keep going" })).toBeTruthy();
  });

  it("questions written from the part read: how many, by name, with no Begin of their own", async () => {
    answers.get_daily_plan = empty();
    answers.get_source_library = book(built(facts({ count: 5, itemIds: ["i1"], sections: ["Conditional probability"] })));
    render(<App />);
    expect((await screen.findByTestId("today-cause")).textContent).toBe(
      `5 questions from “Conditional probability”, the part you read. ${MORE_AS_YOU_READ}`
    );
    expect(screen.queryByRole("button", { name: /Begin/ })).toBeNull();
  });

  it("a build under way: how far it is, and keep reading", async () => {
    answers.get_daily_plan = empty();
    answers.get_source_library = book({ text: "Writing questions for Ch. 1", tone: "working", action: null, details: null, progress: { done: 1, total: 2 } });
    render(<App />);
    expect((await screen.findByTestId("today-cause")).textContent).toBe(
      `Getting “Symmetric Matrices and Variance” ready for questions · 1 of 2 steps done. ${QUESTIONS_FROM_READING} Keep reading meanwhile.`
    );
  });

  it("a day with something in it reads no books and says nothing more; a failed read says nothing", async () => {
    answers.get_daily_plan = reply();
    render(<App />);
    await screen.findByRole("button", { name: "Begin" });
    expect(called("get_source_library")).toEqual([]);
    cleanup();
    answers.get_daily_plan = empty();
    delete answers.get_source_library;
    render(<App />);
    expect((await screen.findByTestId("today-sentence")).textContent).toBe("Done for today.");
    await waitFor(() => expect(called("get_source_library").length).toBeGreaterThan(0));
    expect(screen.queryByTestId("today-cause")).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("every line is in plain words", async () => {
    answers.get_daily_plan = empty();
    answers.get_source_library = book(built(facts({ writing: ["Conditional probability"] })));
    render(<App />);
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toBe("Writing questions from “Conditional probability”, the part you read… Keep reading meanwhile.");
    expect(findJargon(cause.textContent ?? "")).toEqual([]);
  });
});

describe("a section finished before its book is ready (UX-31): the phone says the desktop's sentence", () => {
  const empty = () => reply({ status: "complete", blocks: [], currentBlockId: null },
    { day: { plans: 1, kinds: ["normal"], complete: true, actualMinutes: 0, plannedItems: 0, readingBlocks: 0 } });
  const facts = (extra: Record<string, unknown> = {}) => ({
    count: 0, itemIds: [], sections: [], writing: [], waiting: [], failed: [], toLookAt: 0, sectionCount: 4, ...extra
  });
  const book = (statusLine: Record<string, unknown>) => ({
    sources: [{ sourceId: "src_sym", title: "Symmetric Matrices and Variance", readiness: "ready", readerEnabled: true, extractionId: "ext_1", statusLine }]
  });

  it("while the book is being got ready: the wait, then the finished section's questions promised for then", async () => {
    answers.get_daily_plan = empty();
    answers.get_source_library = book({ text: "Writing questions for Ch. 1", tone: "working", action: null, details: null,
      progress: { done: 1, total: 2 }, questions: facts({ waiting: ["Conditional probability"] }) });
    render(<App />);
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toBe(
      "Getting “Symmetric Matrices and Variance” ready for questions · 1 of 2 steps done. "
      + "Your questions from “Conditional probability” will be written as soon as “Symmetric Matrices and Variance” is ready. Keep reading meanwhile."
    );
    expect(findJargon(cause.textContent ?? "")).toEqual([]);
  });

  it("a waiting section on a book whose line says nothing else: the promise, never 'finish a section'", async () => {
    answers.get_daily_plan = empty();
    answers.get_source_library = book({ text: "Questions for Ch. 1 come up as you read", tone: "quiet", action: null, details: null,
      questions: facts({ waiting: ["Document"], sectionCount: 1 }) });
    render(<App />);
    expect((await screen.findByTestId("today-cause")).textContent).toBe(
      "Your questions from what you read will be written as soon as “Symmetric Matrices and Variance” is ready."
    );
  });
});

describe("a book whose build found no topics (UX-43): the phone says the desktop's sentence", () => {
  const empty = () => reply({ status: "complete", blocks: [], currentBlockId: null },
    { day: { plans: 1, kinds: ["normal"], complete: true, actualMinutes: 0, plannedItems: 0, readingBlocks: 0 } });
  const facts = (extra: Record<string, unknown> = {}) => ({
    count: 0, itemIds: [], sections: [], writing: [], waiting: [], failed: [], toLookAt: 0, sectionCount: 1, ...extra
  });
  const book = (statusLine: Record<string, unknown>) => ({
    sources: [{ sourceId: "src_sym", title: "Symmetric Matrices and Variance", readiness: "ready", readerEnabled: true, extractionId: "ext_1", statusLine }]
  });

  it("no topics found: said under 'Nothing planned for today.', never 'finish a section'", async () => {
    answers.get_daily_plan = empty();
    answers.get_source_library = book({ text: "LearnLoop found no topics to practise in this article", tone: "problem",
      action: { kind: "retry", label: "Try again" }, details: null, noTopics: true, questions: facts({ noneNeeded: ["Document"] }) });
    render(<App />);
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toBe(
      "LearnLoop found no topics to practise in “Symmetric Matrices and Variance”. Try again, or keep reading: what you read gets its questions once topics are found."
    );
    expect(findJargon(cause.textContent ?? "")).toEqual([]);
  });

  it("a finished section that had nothing to write: never 'finish a section'", async () => {
    answers.get_daily_plan = empty();
    answers.get_source_library = book({ text: "Questions for this article come up as you read", tone: "quiet", action: null, details: null,
      questions: facts({ noneNeeded: ["Document"] }) });
    render(<App />);
    expect((await screen.findByTestId("today-cause")).textContent).toBe(
      `Nothing from “Symmetric Matrices and Variance” is up today. ${MORE_AS_YOU_READ}`
    );
  });
});

describe("question writing you can follow: the phone says the desktop's sentences on an empty day", () => {
  const empty = () => reply({ status: "complete", blocks: [], currentBlockId: null },
    { day: { plans: 1, kinds: ["normal"], complete: true, actualMinutes: 0, plannedItems: 0, readingBlocks: 0 } });
  const facts = (extra: Record<string, unknown> = {}) => ({
    count: 0, itemIds: [], sections: [], writing: [], waiting: [], failed: [], toLookAt: 0, sectionCount: 4, ...extra
  });
  const book = (questions: Record<string, unknown>) => ({
    sources: [{ sourceId: "src_sym", title: "Symmetric Matrices and Variance", readiness: "ready", readerEnabled: true, extractionId: "ext_1",
      statusLine: { text: "Questions for Ch. 1 come up as you read", tone: "quiet", action: null, details: null, questions } }]
  });
  const FAILED = { label: "Conditional probability: Bayes' rule", resumeId: "batch_sec" };

  async function causeFor(questions: Record<string, unknown>): Promise<string> {
    answers.get_daily_plan = empty();
    answers.get_source_library = book(questions);
    render(<App />);
    const cause = await screen.findByTestId("today-cause");
    const text = cause.textContent ?? "";
    expect(findJargon(text)).toEqual([]);
    // The phone has no action of its own here: Keep going stays the one.
    expect(screen.getByRole("button", { name: "Keep going" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Begin|Try again/ })).toBeNull();
    cleanup();
    return text;
  }

  it("the writing line with how many topics are done", async () => {
    expect(await causeFor(facts({ writing: ["Conditional probability"], progress: { done: 2, total: 8 } }))).toBe(
      "Writing questions from “Conditional probability”, the part you read · 2 of 8 topics done. Keep reading meanwhile."
    );
  });

  it("questions written while more are: how many, and how far", async () => {
    expect(await causeFor(facts({ count: 3, itemIds: ["i1", "i2", "i3"], sections: ["Conditional probability"], writing: ["Conditional probability"], progress: { done: 2, total: 8 } }))).toBe(
      "3 questions from “Conditional probability” are ready. More are being written (2 of 8 topics done)."
    );
  });

  it("questions written, and a topic that could not be", async () => {
    expect(await causeFor(facts({ count: 3, itemIds: ["i1", "i2", "i3"], sections: ["Conditional probability"], failed: [FAILED], progress: { done: 7, total: 8 } }))).toBe(
      `3 questions from “Conditional probability”, the part you read. ${MORE_AS_YOU_READ} Not every topic's questions could be written.`
    );
  });

  it("questions written, more being written, and a topic that could not be", async () => {
    expect(await causeFor(facts({ count: 3, itemIds: ["i1", "i2", "i3"], sections: ["Conditional probability"], writing: ["Conditional probability"], failed: [FAILED], progress: { done: 4, total: 8 } }))).toBe(
      "3 questions from “Conditional probability” are ready. More are being written (4 of 8 topics done). Not every topic's questions could be written."
    );
  });

  it("nothing written and the section stopped: the stopped section's own sentence, unchanged", async () => {
    expect(await causeFor(facts({ failed: [{ label: "Conditional probability", resumeId: "batch_sec" }] }))).toBe(
      "Couldn't write the questions from “Conditional probability”. Try again, or keep reading: nothing is lost."
    );
  });

  it("nothing written yet and a topic failed while the rest are written: the writing, with the failed topic, never 'Couldn't write' (UX-47)", async () => {
    expect(await causeFor(facts({ writing: ["Conditional probability"], failed: [FAILED], progress: { done: 1, total: 8 } }))).toBe(
      "Writing questions from “Conditional probability”, the part you read · 1 of 8 topics done. Not every topic's questions could be written. Keep reading meanwhile."
    );
  });
});

describe("after the first answers (UX-44): the phone counts only what can be asked now", () => {
  const empty = () => reply({ status: "complete", blocks: [], currentBlockId: null },
    { day: { plans: 1, kinds: ["normal"], complete: true, actualMinutes: 0, plannedItems: 0, readingBlocks: 0 } });
  const facts = (extra: Record<string, unknown> = {}) => ({
    count: 0, itemIds: [], sections: ["Document"], writing: [], waiting: [], failed: [], toLookAt: 0, sectionCount: 1, ...extra
  });
  const book = (questions: Record<string, unknown>) => ({
    sources: [{ sourceId: "src_sym", title: "Symmetric Matrices and Variance", readiness: "ready", readerEnabled: true, extractionId: "ext_1",
      statusLine: { text: "Questions for Ch. 1 come up as you read", tone: "quiet", action: null, details: null, questions } }]
  });
  const FIRST_TOPIC = ["i1", "i2", "i3"];

  async function causeFor(questions: Record<string, unknown>): Promise<string> {
    answers.get_daily_plan = empty();
    answers.get_source_library = book(questions);
    render(<App />);
    const text = (await screen.findByTestId("today-cause")).textContent ?? "";
    expect(findJargon(text)).toEqual([]);
    expect(screen.getByRole("button", { name: "Keep going" })).toBeTruthy();
    cleanup();
    return text;
  }

  it("two answered and one kept for a later check, six written since: six ready", async () => {
    expect(await causeFor(facts({
      count: 9, itemIds: [...FIRST_TOPIC, "i4", "i5", "i6", "i7", "i8", "i9"], writing: ["Document"], progress: { done: 3, total: 8 }, laterItemIds: FIRST_TOPIC
    }))).toBe("6 questions from what you read in “Symmetric Matrices and Variance” are ready. More are being written (3 of 8 topics done).");
  });

  it("none left while more are written: the writing line, never 'ready'", async () => {
    expect(await causeFor(facts({ count: 3, itemIds: FIRST_TOPIC, writing: ["Document"], progress: { done: 1, total: 8 }, laterItemIds: FIRST_TOPIC }))).toBe(
      "Writing questions from what you read in “Symmetric Matrices and Variance” · 1 of 8 topics done. Keep reading meanwhile."
    );
  });

  it("none left and nothing being written: none up today, and more come as you read on", async () => {
    expect(await causeFor(facts({ count: 3, itemIds: FIRST_TOPIC, laterItemIds: FIRST_TOPIC }))).toBe(
      `Nothing from “Symmetric Matrices and Variance” is up today. ${MORE_AS_YOU_READ}`
    );
  });
});

describe("the phone's own Today heading agrees with the desktop (UX-52b): no 'Nothing planned' above questions offered", () => {
  const facts = (extra: Record<string, unknown> = {}) => ({
    count: 0, itemIds: [], sections: [], writing: [], waiting: [], failed: [], toLookAt: 0, sectionCount: 4, ...extra
  });
  const book = (questions: Record<string, unknown>) => ({
    sources: [{ sourceId: "src_sym", title: "Symmetric Matrices and Variance", readiness: "ready", readerEnabled: true, extractionId: "ext_1",
      statusLine: { text: "Questions for Ch. 1 come up as you read", tone: "quiet", action: null, details: null, questions } }]
  });
  const doneEmpty = () => reply({ status: "complete", blocks: [], currentBlockId: null },
    { day: { plans: 1, kinds: ["normal"], complete: true, actualMinutes: 0, plannedItems: 0, readingBlocks: 0 } });
  const openEmpty = () => reply({ status: "open", blocks: [], currentBlockId: null },
    { day: { plans: 1, kinds: ["normal"], complete: false, actualMinutes: 0, plannedItems: 0, readingBlocks: 0 } });

  async function headingFor(day: unknown, questions: Record<string, unknown>): Promise<{ heading: string | null; cause: string }> {
    answers.get_daily_plan = day;
    answers.get_source_library = book(questions);
    render(<App />);
    const cause = (await screen.findByTestId("today-cause")).textContent ?? "";
    const heading = screen.queryByTestId("today-sentence")?.textContent ?? null;
    cleanup();
    return { heading, cause };
  }

  it("an empty, finished day with a book's questions written: the offer, and no 'Nothing planned for today.'", async () => {
    const { heading, cause } = await headingFor(doneEmpty(), facts({ count: 3, itemIds: ["i1", "i2", "i3"], sections: ["Conditional probability"] }));
    expect(cause).toBe(`3 questions from “Conditional probability”, the part you read. ${MORE_AS_YOU_READ}`);
    expect(heading ?? "").not.toMatch(/Nothing planned/);
  });

  it("questions written while more are: the same", async () => {
    const { heading, cause } = await headingFor(doneEmpty(), facts({
      count: 3, itemIds: ["i1", "i2", "i3"], sections: ["Conditional probability"], writing: ["Conditional probability"], progress: { done: 2, total: 8 }
    }));
    expect(cause).toContain("are ready");
    expect(heading ?? "").not.toMatch(/Nothing planned/);
  });

  it("an open plan with nothing in it and questions written: the same", async () => {
    const { heading, cause } = await headingFor(openEmpty(), facts({ count: 2, itemIds: ["i1", "i2"], sections: ["Conditional probability"] }));
    expect(cause).toContain("2 questions");
    expect(heading ?? "").not.toMatch(/Nothing planned/);
  });

  it("nothing offered (the writing line): the heading says none are ready yet, as the desktop's (F45)", async () => {
    const { heading } = await headingFor(doneEmpty(), facts({ writing: ["Conditional probability"], progress: { done: 1, total: 8 } }));
    expect(heading).toBe(NO_QUESTIONS_YET);
  });
});

describe("questions from the part of a section read (the first evening, step 4): the phone says the desktop's sentences", () => {
  const empty = () => reply({ status: "complete", blocks: [], currentBlockId: null },
    { day: { plans: 1, kinds: ["normal"], complete: true, actualMinutes: 0, plannedItems: 0, readingBlocks: 0 } });
  const facts = (extra: Record<string, unknown> = {}) => ({
    count: 0, itemIds: [], sections: [], writing: [], waiting: [], failed: [], toLookAt: 0, sectionCount: 4, ...extra
  });
  const book = (questions: Record<string, unknown>) => ({
    sources: [{ sourceId: "src_sym", title: "Symmetric Matrices and Variance", readiness: "ready", readerEnabled: true, extractionId: "ext_1",
      statusLine: { text: "Questions for Ch. 1 come up as you read", tone: "quiet", action: null, details: null, questions } }]
  });

  it("reading on the phone that qualifies topics: saved, and written when the desktop runs", async () => {
    answers.get_daily_plan = empty();
    answers.get_source_library = book(facts({ owed: ["Conditional probability"] }));
    render(<App />);
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toBe("Your reading is saved. Questions will be written when the desktop is running.");
    expect(findJargon(cause.textContent ?? "")).toEqual([]);
  });

  it("questions written from the part read: how many can be asked now, from what you've read, with no Begin of their own", async () => {
    answers.get_daily_plan = empty();
    answers.get_source_library = book(facts({ count: 3, itemIds: ["i1", "i2", "i3"], sections: ["Conditional probability"],
      partRead: ["Conditional probability"], laterItemIds: ["i3"] }));
    render(<App />);
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toBe("2 questions from what you’ve read of “Conditional probability” are ready. More come as you read on.");
    expect(screen.queryByTestId("today-sentence")).toBeNull();  // an offer: no "Nothing planned" above it
    expect(screen.queryByRole("button", { name: /Begin/ })).toBeNull();
  });

  it("reading that qualifies no topic yet: read a little further", async () => {
    answers.get_daily_plan = empty();
    answers.get_source_library = book(facts({ readFurther: ["Conditional probability"] }));
    render(<App />);
    expect((await screen.findByTestId("today-cause")).textContent).toBe(
      "Read a little further in “Symmetric Matrices and Variance” for your first questions.");
  });
});

describe("the first evening, step 7: what comes next, dated, on the phone", () => {
  const NEXT = {
    asOf: "2026-11-06T23:00:00Z",
    calendar: { zone: "EST", today: "2026-11-06", tomorrow: "2026-11-07", nextDayStartsAt: "2099-11-07T05:00:00Z" },
    reviews: [
      { date: "2026-11-07", count: 2, itemIds: ["i1", "i2"], learningObjectIds: ["lo"], minutes: 3 },
      { date: "2026-11-15", count: 1, itemIds: ["i3"], learningObjectIds: ["lo"], minutes: null }
    ],
    checks: [{ date: "2026-11-10", count: 1, itemIds: ["i4"], learningObjectIds: ["lo"], kinds: ["cold_retry"] }],
    nextReviewDate: "2026-11-07",
    writing: { topicCount: 3, learningObjectIds: ["lo_b", "lo_c", "lo_d"] },
    waiting: { sectionCount: 0 },
    held: { topicCount: 0, learningObjectIds: [] }
  };
  const done = (next: unknown = NEXT) => reply({ status: "complete", stopReason: "A good place to stop." }, { nextPractice: next });

  it("a done day says tomorrow's questions and minutes, the check's first day, and what is still being written", async () => {
    answers.get_daily_plan = done();
    render(<App />);
    const next = await screen.findByTestId("today-next");
    expect(next.textContent).toBe(
      "Tomorrow: 2 questions due · about 3 minutes.A check on your own is available from Tuesday.Questions on 3 more topics are still being written."
    );
    expect(findJargon(next.textContent ?? "")).toEqual([]);
  });

  it("nothing due tomorrow names the nearest later day", async () => {
    answers.get_daily_plan = done({ ...NEXT, reviews: NEXT.reviews.slice(1), nextReviewDate: "2026-11-15", checks: [], writing: { topicCount: 0, learningObjectIds: [] } });
    render(<App />);
    expect((await screen.findByTestId("today-next")).textContent).toBe("Nothing is due tomorrow. Your next question is due on 15 November.");
  });

  it("an open plan with a question in it says nothing of tomorrow", async () => {
    answers.get_daily_plan = reply({}, { nextPractice: NEXT });
    render(<App />);
    await screen.findByRole("button", { name: "Begin" });
    expect(screen.queryByTestId("today-next")).toBeNull();
  });

  it("the session's finish says it as read at the end, and Today does not say it twice", async () => {
    answers.get_daily_plan = reply({}, { nextPractice: NEXT });
    answers.next_plan_item = reply({ status: "complete" }, { step: { kind: "done", planId: "p1", status: "complete", stopReason: "x" } });
    answers.plan_keep_going = reply({ status: "stopped" });
    const atEnd = { ...NEXT, reviews: [{ date: "2026-11-06", count: 1, itemIds: ["i9"], learningObjectIds: ["lo"], minutes: null }, ...NEXT.reviews] };
    answers.end_session = { attemptsRecorded: 1, nextPractice: atEnd };
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Begin" }));
    fireEvent.click(await screen.findByRole("button", { name: "Done for today" }));
    const next = await screen.findByTestId("session-next");
    expect(next.textContent).toBe(
      "Still due today: 1 question.Tomorrow: 2 more questions due · about 3 minutes.A check on your own is available from Tuesday.Questions on 3 more topics are still being written."
    );
    expect(screen.queryByTestId("today-next")).toBeNull();
  });

  it("Today is read again when the plan's next day starts", async () => {
    answers.get_daily_plan = done({ ...NEXT, calendar: { ...NEXT.calendar, nextDayStartsAt: new Date(Date.now() - 1000).toISOString() } });
    render(<App />);
    await screen.findByTestId("today-next");
    const reads = called("get_daily_plan").length;
    await waitFor(() => expect(called("get_daily_plan").length).toBeGreaterThan(reads), { timeout: 3000 });
  });
});

describe("the first evening, step 8: the phone says the desktop's one explanation, where to read to, and held questions", () => {
  const empty = () => reply({ status: "complete", blocks: [], currentBlockId: null },
    { day: { plans: 1, kinds: ["normal"], complete: true, actualMinutes: 0, plannedItems: 0, readingBlocks: 0 } });
  const facts = (extra: Record<string, unknown> = {}) => ({
    count: 0, itemIds: [], sections: [], writing: [], waiting: [], failed: [], toLookAt: 0, sectionCount: 4, ...extra
  });
  const book = (statusLine: Record<string, unknown>) => ({
    sources: [{ sourceId: "src_sym", title: "Symmetric Matrices and Variance", readiness: "ready", readerEnabled: true, extractionId: "ext_1", statusLine }]
  });
  const built = (questions = facts()) => ({ text: "Questions for Ch. 1–2 are written from the parts you read", tone: "quiet", action: null, details: null, questions });
  const PART = "Conditional probability";

  it("ready + writing + held: the offer, and the held line apart, which opens nothing", async () => {
    answers.get_daily_plan = empty();
    answers.get_source_library = book(built(facts({ count: 2, itemIds: ["i1", "i2"], sections: [PART], writing: [PART], partRead: [PART], toLookAt: 2, awaitingOk: 2 })));
    render(<App />);
    expect((await screen.findByTestId("today-cause")).textContent).toBe(`2 questions from what you’ve read of “${PART}” are ready. More are being written.`);
    const held = await screen.findByTestId("today-held");
    expect(held.textContent).toBe("2 more questions need your OK.");
    expect(held.querySelectorAll("button, a")).toHaveLength(0);
    expect(document.body.textContent).not.toMatch(/Nothing planned|finish sections|finish a section/);
  });

  it("every question held: the cause says so, with no second held line", async () => {
    answers.get_daily_plan = empty();
    answers.get_source_library = book(built(facts({ toLookAt: 3, awaitingOk: 3 })));
    render(<App />);
    expect((await screen.findByTestId("today-cause")).textContent).toBe("3 questions from what you’ve read in “Symmetric Matrices and Variance” need your OK.");
    expect(screen.queryByTestId("today-held")).toBeNull();
  });

  it("a done day with questions held: the held line under the day's words", async () => {
    answers.get_daily_plan = reply({ status: "complete" });
    answers.get_source_library = book(built(facts({ count: 1, itemIds: ["i1"], sections: [PART], toLookAt: 1, awaitingOk: 1 })));
    render(<App />);
    expect((await screen.findByTestId("today-held")).textContent).toBe("1 more question needs your OK.");
  });

  it("while the book is got ready after reading part of a section: no questions ready yet, and they follow from what was read", async () => {
    answers.get_daily_plan = empty();
    answers.get_source_library = book({ text: "Getting Ch. 1 ready for questions", tone: "working", action: null, details: null,
      progress: { done: 1, total: 2 }, questions: facts({ beforeBuild: [PART] }) });
    render(<App />);
    expect((await screen.findByTestId("today-cause")).textContent).toBe(
      "Getting “Symmetric Matrices and Variance” ready for questions · 1 of 2 steps done. "
      + "Questions from what you’ve read will follow when “Symmetric Matrices and Variance” is ready. Keep reading meanwhile."
    );
    expect(screen.getByTestId("today-sentence").textContent).toBe(NO_QUESTIONS_YET);
  });

  it("read some, none qualifies yet: where to read to", async () => {
    answers.get_daily_plan = empty();
    answers.get_source_library = book(built(facts({ readFurther: [PART], readTo: { section: PART, heading: "Variance", words: null, sectionEnd: false } })));
    render(<App />);
    expect((await screen.findByTestId("today-cause")).textContent).toBe("Read through “Variance” in “Symmetric Matrices and Variance” for your first questions.");
  });

  it("an open plan with questions in it reads no books, so no held line", async () => {
    answers.get_daily_plan = reply();
    answers.get_source_library = book(built(facts({ toLookAt: 2, awaitingOk: 2 })));
    render(<App />);
    await screen.findByRole("button", { name: "Begin" });
    expect(called("get_source_library")).toEqual([]);
    expect(screen.queryByTestId("today-held")).toBeNull();
  });
});

describe("an honest wait (the first evening, step 6): the phone says what is happening now under the sentence", () => {
  const empty = () => reply({ status: "complete", blocks: [], currentBlockId: null },
    { day: { plans: 1, kinds: ["normal"], complete: true, actualMinutes: 0, plannedItems: 0, readingBlocks: 0 } });
  const AS_OF = "2026-11-21T18:10:00Z";
  const ago = (seconds: number) => new Date(Date.parse(AS_OF) - seconds * 1000).toISOString().replace(".000Z", "Z");
  const book = (statusLine: Record<string, unknown>) => ({
    sources: [{ sourceId: "src_sym", title: "Symmetric Matrices and Variance", readiness: "ready", readerEnabled: true, extractionId: "ext_1", statusLine }]
  });
  const writing = (detail: Record<string, unknown> = {}) => ({
    text: "Questions for Ch. 1 come up as you read", tone: "quiet", action: null, details: null,
    questions: { count: 0, itemIds: [], sections: [], writing: ["Document"], waiting: [], failed: [], toLookAt: 0, sectionCount: 1,
      progress: { done: 0, total: 4 }, partRead: ["Document"],
      writingDetail: { asOf: AS_OF, startedAt: ago(200), queued: false, retry: false, topic: { title: "Spectral theorem", index: 1, total: 4 },
        topicStartedAt: ago(75), delivery: { requestSentAt: ago(75), replyReceivedAt: null, outputPieces: 0, lastOutputAt: null }, measured: null, ...detail } }
  });

  async function detailFor(statusLine: Record<string, unknown>): Promise<HTMLElement> {
    answers.get_daily_plan = empty();
    answers.get_source_library = book(statusLine);
    render(<App />);
    return screen.findByTestId("today-cause-detail");
  }

  it("question writing at 0 of 4: the topic, clock times (never ages that would go stale), and the first can take a few minutes", async () => {
    const detail = await detailFor(writing());
    expect(screen.getByTestId("today-cause").textContent).toBe(
      "Writing questions from what you’ve read in “Symmetric Matrices and Variance” · 0 of 4 topics done. Keep reading meanwhile.");
    const text = detail.textContent ?? "";
    expect(text).toContain("Writing topic 1 of 4: “Spectral theorem”");
    expect(text).toMatch(/Started at \d{1,2}:\d{2}(\s?[AP]M)? · asked at \d{1,2}:\d{2}(\s?[AP]M)?, no reply yet/);
    expect(text).toContain("The first questions can take a few minutes.");
    expect(text).not.toMatch(/ago|%|still writing|stall/);
    expect(findJargon(text)).toEqual([]);
    // The one action stays the plan's.
    expect(screen.getByRole("button", { name: "Keep going" })).toBeTruthy();
  });

  it("with this library's measured time per topic, the count it rests on in the collapsed details", async () => {
    const detail = await detailFor(writing({ measured: { minutes: 2.3, samples: 3 } }));
    expect(detail.textContent).toContain("Here a topic's questions have taken about 2 minutes to write.");
    const more = detail.querySelector("details") as HTMLDetailsElement;
    expect(more.open).toBe(false);
    expect(more.textContent).toContain("Measured on the last 3 topics written in this library.");
  });

  it("a book being got ready: its step, a retry said as one, and no measured time claimed", async () => {
    const detail = await detailFor({
      text: "Getting Ch. 1 ready for questions", tone: "working", action: null, details: null, progress: { done: 1, total: 2 },
      buildDetail: { asOf: AS_OF, startedAt: ago(130), stage: "checking", retry: true, measured: null, draftedTopics: 8,
        delivery: { requestSentAt: null, replyReceivedAt: ago(12), outputPieces: 0, lastOutputAt: null } }
    });
    const text = detail.textContent ?? "";
    expect(text).toContain("Trying again · 8 topics drafted · checking them");
    expect(text).toMatch(/Started at \d{1,2}:\d{2}(\s?[AP]M)? · reply received at \d{1,2}:\d{2}/);
    expect(text).toContain("No book has finished getting ready in this library yet, so no time is given.");
    expect(findJargon(text)).toEqual([]);
  });
});

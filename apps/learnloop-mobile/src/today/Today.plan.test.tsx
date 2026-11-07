// Mobile v2 V2, J1/J4/J5/J6 through the fake host: Today is the shared plan (owner decision D1),
// Next serves the plan's step under the phone's origin, what the phone can't show waits for the
// desktop and is counted, the stop offer goes both ways, and a randomized check offers no help.
import { findJargon } from "@desktop/copy/denyList";
import {
  answers, App, cacheSessionId, called, cleanup, describe, expect, feedback, fireEvent, getAnswers, installFakeHost, it, item, render,
  screen, session, waitFor
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

describe("Today is the plan (J1)", () => {
  it("says the plan in one sentence, and Begin starts a session and serves the plan's step", async () => {
    answers.get_daily_plan = reply();
    answers.next_plan_item = reply({}, { step: itemStep() });
    render(<App />);
    expect(await screen.findByText(/25 minutes today: 1 short question from earlier days\./)).toBeTruthy();
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

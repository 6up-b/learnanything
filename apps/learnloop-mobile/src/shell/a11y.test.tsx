// Mobile v2 §4.1 and §4.7 over the phone's own surfaces: plain words (the desktop's jargon
// deny-list, imported, never copied), every control named, and math VoiceOver can read.
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { findJargon } from "@desktop/copy/denyList";
import { MarkdownMath } from "@desktop/render/MarkdownMath";
import { clear as clearQueries } from "@desktop/api/queryCache";
import { App } from "../App";
import { saveCredential } from "../store/credential";
import { CaptureScreen } from "../capture/CaptureScreen";
import { PairScreen } from "../pair/PairScreen";
import { ProgressScreen } from "../progress/ProgressScreen";
import { ReadScreen } from "../read/ReadScreen";
import { GRADING_DOWN } from "../practice/QuestionScreen";
import { ConnectionLine, BUSY_LINE, GRADING_LINE, UPDATED_LINE, offlineLine } from "./ConnectionLine";
import { markGradingDown, markOffline, markReachable, markStale } from "./connection";
import { DbBlockedScreen } from "./DbBlocked";
import { DisplaySheet } from "./DisplaySheet";
import { TabBar } from "./TabBar";
import { PLAN_OFF } from "../test/planOff";

/** No exemptions: every phone surface passes the desktop's list as it stands. */
function jargonOf(text: string): string[] {
  return findJargon(text);
}

/** Every control a learner can reach is named for VoiceOver. */
function unnamedControls(): string[] {
  return [...document.querySelectorAll("button, input, textarea, [contenteditable='true']")]
    .filter((element) => !(element as HTMLElement).hidden)
    .filter((element) => {
      const label = element.getAttribute("aria-label") ?? "";
      const labelled = element.id ? document.querySelector(`label[for="${element.id}"]`) : null;
      return !label.trim() && !(element.textContent ?? "").trim() && !labelled && !element.closest("label");
    })
    .map((element) => element.outerHTML.slice(0, 80));
}

describe("plain words (§4.1)", () => {
  it.each([
    ["the pairing screen", () => render(<PairScreen waiting={2} />)],
    ["capture", () => render(<CaptureScreen onSaved={() => undefined} />)],
    ["read", () => render(<ReadScreen />)],
    ["progress", () => render(<ProgressScreen />)],
    ["the tab bar", () => render(<TabBar current="today" onSelect={() => undefined} />)],
    ["the display sheet", () => render(<DisplaySheet onClose={() => undefined} />)],
    ["an upgrade another tab holds up", () => render(<DbBlockedScreen />)]
  ])("%s", (_name, mount) => {
    mount();
    expect(jargonOf(document.body.textContent ?? "")).toEqual([]);
    expect(unnamedControls()).toEqual([]);
  });

  it("every connection line and the grading message", () => {
    for (const line of [offlineLine(0), offlineLine(3), BUSY_LINE, GRADING_LINE, UPDATED_LINE, GRADING_DOWN]) {
      expect(jargonOf(line), line).toEqual([]);
    }
    render(<ConnectionLine outboxWaiting={1} />);
    for (const mark of [markOffline, () => markReachable(true), markGradingDown, markStale]) {
      act(mark);
      expect(jargonOf(document.body.textContent ?? "")).toEqual([]);
    }
  });
});

describe("today's practice through the shell (§4.1, §4.7)", () => {
  const answers: Record<string, unknown> = {};
  beforeEach(async () => {
    clearQueries();
    const session = { sessionId: "s1", endedAt: null, availableMinutes: 15, checkpoint: null, ownerDeviceId: "dev", ownerLabel: "Phone", ownerGeneration: 0 };
    Object.assign(answers, {
      start_session: session,
      get_session: session,
      get_daily_plan: PLAN_OFF,
      get_today_queue: { sessionId: "s1", sections: [{ title: "Due", items: [{ practiceItemId: "i1", schedulerCandidateId: "c1", learningObjectTitle: "Eigenvalues" }, { practiceItemId: "i2", schedulerCandidateId: "c2", learningObjectTitle: "Bases" }] }], deviceDeferredCount: 2 },
      get_practice_item: { learningObjectTitle: "Eigenvalues", attemptTypesAllowed: ["independent_attempt"], assessmentContractVersionId: "acv", presentation: { blocks: [{ kind: "prompt", markdown: "What is $\\lambda$?", label: null }] } },
      get_probe_contract: { active: false },
      save_practice_draft: { ok: true },
      submit_attempt: { attemptId: "a1" },
      acknowledge_practice_submission: { acknowledged: true },
      get_feedback: {
        learningObjectTitle: "Eigenvalues", rubricScore: 1, maxPoints: 2, feedbackMd: "Close.", manualReviewReason: null, diagnosisStatus: "done",
        criterionEvidence: [{ criterionId: "c", criterionDescription: "Correct value", pointsAwarded: 1, pointsPossible: 2, notes: null }],
        repairSuggestions: [{ practiceMode: "m", learningObjectId: null, rationale: "r", elicitingQuestion: "Which matrix did you start from?" }]
      },
      diagnosis_status: { status: "done", cardEnabled: true, summaryMd: "You stopped one step early." },
      get_grading_clarification: { clarification: { questionMd: "Which reading did you mean?" } }
    });
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/rpc") {
        const method = JSON.parse(init?.body as string).method as string;
        return new Response(JSON.stringify({ ok: true, result: answers[method] ?? {} }), { status: 200 });
      }
      if (url === "/api/v1/queue-revision") return new Response(JSON.stringify({ revision: 1 }), { status: 200 });
      return new Response(JSON.stringify({ ok: false, error: { code: "not_found", message: "m", retryable: false } }), { status: 404 });
    }));
    await saveCredential({ token: "tok", deviceId: "dev", scope: "app" });
  });

  it("Today, a question and its feedback say nothing from the deny-list, and name every control", async () => {
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "15 min" }));
    await screen.findByRole("button", { name: /^Next: Eigenvalues/ });
    await screen.findByText("2 items waiting for the desktop");
    expect(jargonOf(document.body.textContent ?? "")).toEqual([]);
    expect(unnamedControls()).toEqual([]);

    fireEvent.click(screen.getByRole("button", { name: /^Next: Eigenvalues/ }));
    const editor = await screen.findByRole("textbox", { name: "Your answer" });
    expect(jargonOf(document.body.textContent ?? "")).toEqual([]);
    expect(unnamedControls()).toEqual([]);

    editor.textContent = "2";
    fireEvent.input(editor);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText("You stopped one step early.");
    await screen.findByText("Which matrix did you start from?");
    expect(jargonOf(document.body.textContent ?? "")).toEqual([]);
    expect(unnamedControls()).toEqual([]);
  });
});

it("KaTeX renders MathML beside its HTML, so VoiceOver reads the formula (§4.7)", () => {
  const { container } = render(<MarkdownMath value={"Let $\\lambda^2 = 4$."} />);
  const math = container.querySelector("math");
  expect(math).not.toBeNull();
  expect(container.querySelector(".katex-html")).not.toBeNull();
});

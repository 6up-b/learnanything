import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

const { api } = vi.hoisted(() => ({ api: {
  beginProbeDialogue: vi.fn(), nextProbeDialogueTurn: vi.fn(), recordProbeDialogueTurn: vi.fn(),
  endProbeDialogue: vi.fn(), submitAttempt: vi.fn(), submitDontKnow: vi.fn(), stopProbeDiagnosing: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
vi.mock("./ProbeBlockResult", () => ({ ProbeBlockResult: () => null }));

import { setAlgoConfig } from "../app/algoConfig";
import { DialogueProbePanel } from "./DialogueProbe";

const STUCK = "Write what you can, or what's confusing you";
const TURN = {
  kind: "commit", promptMd: "Is A diagonalizable?", practiceItemId: "pi_probe", presentationId: "pres-1",
  turnNumber: 1, plannedTurns: 2
};

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  api.beginProbeDialogue.mockResolvedValue({ dialogueState: "s0" });
  api.nextProbeDialogueTurn.mockResolvedValueOnce({ dialogueState: "s1", turn: TURN });
  api.recordProbeDialogueTurn.mockResolvedValue({ dialogueState: "s2", blockComplete: true });
  api.endProbeDialogue.mockResolvedValue({ blockEnd: null });
  api.submitAttempt.mockResolvedValue({ attemptId: "att" });
  api.submitDontKnow.mockResolvedValue({ attemptId: "att" });
});
afterEach(() => { cleanup(); setAlgoConfig(undefined); });

function renderPanel() {
  return render(
    <DialogueProbePanel learningObjectId="lo" sessionId="session" onDone={vi.fn()} onError={vi.fn()} />
  );
}

it("turns Don't know into I'm stuck: one tap, then an empty answer may be committed", async () => {
  setAlgoConfig({ practice: { stuckPrompt: true } });
  renderPanel();
  const box = await screen.findByPlaceholderText("Commit to a short answer…");
  expect(screen.queryByRole("button", { name: "Don't know" })).toBeNull();
  const commit = screen.getByRole("button", { name: /Commit answer/ }) as HTMLButtonElement;
  expect(commit.disabled).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "I'm stuck" }));
  expect(box.getAttribute("placeholder")).toBe(STUCK);
  expect(screen.getByRole("status", { name: "stuck prompt" }).textContent).toContain(STUCK);
  expect(commit.disabled).toBe(false);
  await act(async () => { fireEvent.click(commit); });
  await waitFor(() => expect(api.submitAttempt).toHaveBeenCalledOnce());
  expect(api.submitAttempt).toHaveBeenCalledWith(expect.objectContaining({
    answerMd: "", attemptType: "diagnostic_probe", probePresentationId: "pres-1", declaredStuck: true
  }));
  expect(Number.isInteger(api.submitAttempt.mock.calls[0][0].activeSeconds)).toBe(true);
  expect(api.submitDontKnow).not.toHaveBeenCalled();
});

it("keeps Don't know where the vault does not offer I'm stuck", async () => {
  renderPanel();
  await screen.findByPlaceholderText("Commit to a short answer…");
  expect(screen.queryByRole("button", { name: "I'm stuck" })).toBeNull();
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Don't know" })); });
  await waitFor(() => expect(api.submitDontKnow).toHaveBeenCalledOnce());
  expect(api.submitAttempt).not.toHaveBeenCalled();
});

it("\"Stop diagnosing and teach me\" ends the block and hands the topic to a lesson with the check's episode (TH-1)", async () => {
  api.stopProbeDiagnosing.mockResolvedValue({ version: 1, stopped: true, decision: {}, episodeId: "ep_3", learningObjectId: "lo" });
  const blockEnd = { episodeId: "ep_3", status: "converted_to_tutoring", releasedFeedback: [], route: "ordinary_practice" };
  api.endProbeDialogue.mockResolvedValue({ blockEnd });
  const onDone = vi.fn();
  const onTeachFromCheck = vi.fn();
  const onAsk = vi.fn();
  render(<DialogueProbePanel learningObjectId="lo" sessionId="session" onDone={onDone} onError={vi.fn()}
                             onTeachFromCheck={onTeachFromCheck} onAsk={onAsk} />);
  await screen.findByPlaceholderText("Commit to a short answer…");
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Stop diagnosing and teach me" })); });
  await waitFor(() => expect(onTeachFromCheck).toHaveBeenCalledOnce());
  expect(api.stopProbeDiagnosing).toHaveBeenCalledWith("pi_probe");
  expect(api.endProbeDialogue).toHaveBeenCalledOnce();
  expect(onTeachFromCheck).toHaveBeenCalledWith(expect.objectContaining({ learningObjectId: "lo", probeEpisodeId: "ep_3" }));
  expect(onDone).toHaveBeenCalledWith(blockEnd);
  expect(onAsk).not.toHaveBeenCalled();
  // The fallback is the tutor's proactive opening on the turn's question.
  onTeachFromCheck.mock.calls[0][0].fallback();
  expect(onAsk).toHaveBeenCalledWith({ context: "practice", practiceItemId: "pi_probe", sessionId: "session", proactiveOpen: true });
});

it("a stop that fails teaches nothing and shows the block's results as before", async () => {
  api.stopProbeDiagnosing.mockRejectedValue({ message: "busy" });
  const onTeachFromCheck = vi.fn();
  const onError = vi.fn();
  render(<DialogueProbePanel learningObjectId="lo" sessionId="session" onDone={vi.fn()} onError={onError}
                             onTeachFromCheck={onTeachFromCheck} />);
  await screen.findByPlaceholderText("Commit to a short answer…");
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Stop diagnosing and teach me" })); });
  await screen.findByText("The dialogue ended without a block result.");
  expect(onError).toHaveBeenCalledWith("busy");
  expect(onTeachFromCheck).not.toHaveBeenCalled();
});

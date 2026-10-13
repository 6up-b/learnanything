import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { SourceOffers } from "./SourceOffers";
import { AskOverlay } from "./AskOverlay";
import type { SourceToolRequestDto } from "../api/dto";

const { api } = vi.hoisted(() => ({ api: {
  runSourceTool: vi.fn(), findPractice: vi.fn(), recordProposalImpressions: vi.fn(), planLearnerPick: vi.fn(),
  importSourceExercise: vi.fn(), getSourceExerciseImport: vi.fn(), recordSourceOfferShown: vi.fn(),
  getTutorTranscript: vi.fn(), askTutorQuestion: vi.fn(), previewTutorOpening: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: () => null }));
vi.mock("./OpenInSource", () => ({ OpenInSource: () => null }));

const PRACTICE_RUN = {
  version: 1, tool: "find_practice", policy: "assisted_practice", toolCallId: "stc_p", runId: "stc_r1",
  result: {
    proposalId: "pp_1",
    items: [{ practiceItemId: "pi_det_2", learningObjectId: "lo", facetIds: [], practiceMode: "short_answer",
              prompt: "What happens to a determinant when two rows are swapped?", difficulty: 0.5,
              expectedMinutes: 2, sourceLabel: null, rationale: "same rule" }],
    sourceExercises: [{ key: "srcex:ext:t7", spanKeys: ["ext:t7"], sourceLabel: "From Matrix Theory, p. 9 · not yet in your practice",
                        page: 9, statement: "Solve 3x + 5 = 20 for x.", rationale: null }]
  }
};
const PASSAGE_RUN = {
  version: 1, tool: "find_sources", policy: "assisted_practice", toolCallId: "stc_s", runId: "stc_r2",
  result: { passages: [{ spanKey: "ext:t3", sourceTitle: "Matrix Theory", section: "Ch 5", page: 7, revisionId: "r",
                         text: "Swapping two rows changes the sign.", label: "source-authored" }] }
};
const REQUESTS: SourceToolRequestDto[] = [
  { toolCallId: "stc_p", tool: "find_practice", reason: "Practise the sign rule", run: "eager", dropped: [], arguments: {} },
  { toolCallId: "stc_s", tool: "find_sources", reason: "See how your book explains it", run: "eager", dropped: [], arguments: {} },
  { toolCallId: "stc_c", tool: "compare_sources", reason: "How do your books treat this?", run: "lazy", dropped: [], arguments: {} }
];

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  api.runSourceTool.mockImplementation((id: string) =>
    Promise.resolve(id === "stc_p" ? PRACTICE_RUN : id === "stc_s" ? PASSAGE_RUN : {
      version: 1, tool: "compare_sources", policy: "reading", toolCallId: "stc_c", runId: "r3",
      result: { status: "ok", sources: [{ ref: "s1", sourceId: "src", sourceTitle: "Matrix Theory", extractionId: "ext",
        spanId: "t3", page: 7, passage: "p", label: "source-authored",
        contributions: [{ contribution: "Uses row operations", perspective: null, quote: "Swapping two rows" }] }],
        labels: { comparison: "LearnLoop's comparison (AI-written)" } }
    }));
  api.recordProposalImpressions.mockResolvedValue({ recorded: 2 });
  api.recordSourceOfferShown.mockResolvedValue({ recorded: true });
  api.planLearnerPick.mockResolvedValue({ version: 1, enabled: true, plan: null, step: { kind: "item" } });
  api.importSourceExercise.mockResolvedValue({ status: "queued", importId: "imp", batchId: "b" });
  api.getSourceExerciseImport.mockResolvedValue({ version: 1, importId: "imp", status: "written",
    practiceItemId: "pi_new", keyStatus: "book_solution", keyLabel: "checked against the book's solution" });
});
afterEach(() => cleanup());

it("runs eager offers, records impressions and picks through the plan", async () => {
  const toast = vi.fn();
  render(<SourceOffers answer={{ eventId: "e1", toolRequests: [...REQUESTS] }} sessionId="s1" onToast={toast} />);
  await screen.findByText("What happens to a determinant when two rows are swapped?");
  // The lazy comparison never runs before it is tapped.
  expect(api.runSourceTool.mock.calls.map((call) => call[0]).sort()).toEqual(["stc_p", "stc_s"]);
  await waitFor(() => expect(api.recordProposalImpressions).toHaveBeenCalledWith({
    proposalId: "pp_1", surface: "tutor_strip", sessionId: "s1",
    keys: [{ kind: "item", practiceItemId: "pi_det_2" },
           { kind: "source_exercise", extractionId: "ext", spanIds: ["t7"] }]
  }));
  fireEvent.click(screen.getByText("❯ practise"));
  await waitFor(() => expect(api.planLearnerPick).toHaveBeenCalledWith("pi_det_2", "s1", null, "pp_1"));
  fireEvent.click(screen.getByText("❯ practise from your book"));
  await waitFor(() => expect(api.importSourceExercise).toHaveBeenCalledWith({
    proposalId: "pp_1", extractionId: "ext", spanIds: ["t7"], sessionId: "s1" }));
});

// Codex sources-build review F6: a pick is followed to delivery, not just enqueued.

function renderOffers(extra: { onOpenPractice?: (id: string) => void; toast?: (message: string) => void } = {}) {
  const toast = extra.toast ?? vi.fn();
  render(<SourceOffers answer={{ eventId: "e1", toolRequests: [REQUESTS[0]] }} sessionId="s1" onToast={toast}
                       onOpenPractice={extra.onOpenPractice} importPollMs={1} />);
  return toast;
}

it("an imported exercise is followed until written, then served through the plan's pick", async () => {
  api.getSourceExerciseImport
    .mockResolvedValueOnce({ version: 1, importId: "imp", status: "authoring" })
    .mockResolvedValueOnce({ version: 1, importId: "imp", status: "checking" });
  const toast = renderOffers();
  fireEvent.click(await screen.findByText("❯ practise from your book"));
  await waitFor(() => expect(api.planLearnerPick).toHaveBeenCalledWith("pi_new", "s1", null, "pp_1", "imp"));
  expect(api.getSourceExerciseImport).toHaveBeenCalledTimes(3);
  await waitFor(() => expect(toast).toHaveBeenCalledWith(
    "Added to today's practice. Answer key: checked against the book's solution."));
  expect(screen.getByText("added")).toBeTruthy();
});

it("a failed import is shown with its reason and never served", async () => {
  api.getSourceExerciseImport.mockResolvedValue({ version: 1, importId: "imp", status: "rejected",
    reason: "the answer key could not be checked" });
  const toast = renderOffers();
  fireEvent.click(await screen.findByText("❯ practise from your book"));
  await screen.findByText("couldn't add: the answer key could not be checked");
  expect(toast).toHaveBeenCalledWith(
    "Couldn't bring this exercise into your practice: the answer key could not be checked");
  expect(api.planLearnerPick).not.toHaveBeenCalled();
  expect(screen.getByText("❯ try again")).toBeTruthy();
});

it("with the plan off, an item pick offers the open-list path instead of claiming it was added", async () => {
  api.planLearnerPick.mockResolvedValue({ version: 1, enabled: false, reason: "plan_disabled", plan: null });
  const open = vi.fn();
  const toast = renderOffers({ onOpenPractice: open });
  fireEvent.click(await screen.findByText("❯ practise"));
  const action = await screen.findByText("❯ open");
  expect(toast).not.toHaveBeenCalledWith("Added to today's practice.");
  expect(toast).toHaveBeenCalledWith("Your daily plan is off: open it from here when you're ready.");
  fireEvent.click(action);
  expect(open).toHaveBeenCalledWith("pi_det_2");
});

it("with the plan off, an imported exercise opens its new item", async () => {
  api.planLearnerPick.mockResolvedValue({ version: 1, enabled: false, reason: "plan_disabled", plan: null });
  const open = vi.fn();
  renderOffers({ onOpenPractice: open });
  fireEvent.click(await screen.findByText("❯ practise from your book"));
  fireEvent.click(await screen.findByText("❯ open"));
  expect(api.planLearnerPick).toHaveBeenCalledWith("pi_new", "s1", null, "pp_1", "imp");
  expect(open).toHaveBeenCalledWith("pi_new");
});

it("a pick the plan refuses is shown, not announced as added", async () => {
  api.planLearnerPick.mockRejectedValue({ message: "That item was not proposed by this proposal" });
  const toast = renderOffers();
  fireEvent.click(await screen.findByText("❯ practise"));
  await screen.findByText("couldn't add: That item was not proposed by this proposal");
  expect(toast).not.toHaveBeenCalledWith("Added to today's practice.");
});

it("records a passage offer only when it is opened, and compares on tap", async () => {
  const explain = vi.fn();
  render(<SourceOffers answer={{ eventId: "e1", toolRequests: [...REQUESTS] }} onToast={vi.fn()}
                       onExplainWithWork={explain} />);
  const open = await screen.findByText("❯ read 1");
  expect(api.recordSourceOfferShown).not.toHaveBeenCalled();
  fireEvent.click(open);
  expect(api.recordSourceOfferShown).toHaveBeenCalledWith({ toolCallId: "stc_s", spanKeys: ["ext:t3"], sessionId: undefined });
  expect(screen.getByText("Swapping two rows changes the sign.")).toBeTruthy();
  fireEvent.click(screen.getByText("❯ explain this with my work"));
  expect(explain).toHaveBeenCalledWith("ext:t3");
  fireEvent.click(screen.getByText("❯ how do your books treat this?"));
  await screen.findByText(/Uses row operations/);
  expect(api.runSourceTool).toHaveBeenCalledWith("stc_c");
});

it("falls back to S0's practice request when the tutor wrote no find_practice request", async () => {
  api.findPractice.mockResolvedValue({ version: 1, status: "ok", proposalId: "pp_0", items: [
    { rank: 1, practiceItemId: "pi_x", learningObjectId: "lo", learningObjectTitle: null, practiceMode: "short_answer",
      prompt: "Expand along a row.", facetIds: [], rationale: null }] });
  render(<SourceOffers answer={{ eventId: "e1", practiceRequest: {
    request: { query: "q", learningObjectIds: [], facetIds: [], excludeItemIds: ["pi_cur"], intent: "practice" },
    caller: { kind: "tutor", ref: "e1" }, version: "tutor_practice_request.v1" } }} onToast={vi.fn()} />);
  await screen.findByText("Expand along a row.");
  expect(api.findPractice).toHaveBeenCalledWith({ query: "q", learningObjectIds: [], facetIds: [],
    excludeItemIds: ["pi_cur"], intent: "practice", caller: { kind: "tutor", ref: "e1" } });
});

it("explain-with-my-work asks a pinned follow-up with the draft", async () => {
  api.getTutorTranscript.mockResolvedValue({ events: [], remaining: 3 });
  const answer = { version: 1, eventId: "event-1", answerMd: "Start here.", questionType: "strategy", facets: [],
                   hintEquivalent: true, leakSuspected: false, citations: [], remaining: 2,
                   practiceRequest: null, toolRequests: [REQUESTS[1]] };
  api.askTutorQuestion.mockResolvedValueOnce(answer)
    .mockResolvedValueOnce({ ...answer, eventId: "event-2", toolRequests: [] });
  render(<AskOverlay target={{ context: "practice", practiceItemId: "pi_cur", sessionId: "s1",
                               attemptProgress: "draft_started", draftMd: "det flips sign" }}
                     onClose={vi.fn()} onToast={vi.fn()} />);
  await waitFor(() => expect(api.getTutorTranscript).toHaveBeenCalledOnce());
  const input = screen.getByPlaceholderText("ask a question — enter sends");
  fireEvent.change(input, { target: { value: "Why the sign?" } });
  fireEvent.keyDown(input, { key: "Enter" });
  fireEvent.click(await screen.findByText("❯ read 1"));
  fireEvent.click(screen.getByText("❯ explain this with my work"));
  await waitFor(() => expect(api.askTutorQuestion).toHaveBeenCalledTimes(2));
  const followUp = api.askTutorQuestion.mock.calls[1][0];
  expect(followUp.pinnedSpanKeys).toEqual(["ext:t3"]);
  expect(followUp.learnerDraftMd).toBe("det flips sign");
});

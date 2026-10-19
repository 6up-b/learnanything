// RW1c's offers under a Reader tutor answer (spec §4.6, D44; gate G59).
// Fetch early, show on press: the practice and passage lookups start when the
// answer lands and render nothing until pressed; the impression and the
// exposure are written only on the press; a comparison makes no call until
// pressed; an empty lookup renders its plain line; a failed one runs again on
// the press.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { PracticeRequestDto, SourceToolRequestDto } from "../../api/dto";
import { defaultTutorOfferStore, OFFER_COPY, TutorOffers } from "./TutorOffers";

const { api } = vi.hoisted(() => ({
  api: { findPractice: vi.fn(), runSourceTool: vi.fn(), recordProposalImpressions: vi.fn(), recordSourceOfferShown: vi.fn() },
}));
vi.mock("../../api/client", () => ({ api }));
afterEach(cleanup);

const PRACTICE: PracticeRequestDto = {
  request: { query: "why?", learningObjectIds: [], facetIds: [], excludeItemIds: [], intent: "practice" },
  caller: { kind: "tutor", ref: "q1" }, version: "tutor_practice_request.v1",
};
const PASSAGES: SourceToolRequestDto = { toolCallId: "stc_p", tool: "find_sources", reason: "Your other book says it differently", run: "eager", dropped: [], arguments: {} };
const COMPARE: SourceToolRequestDto = { toolCallId: "stc_c", tool: "compare_sources", reason: "Your books differ here", run: "lazy", dropped: [], arguments: {} };

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

const practiceResult = { version: 1, status: "ok", proposalId: "prop_1", items: [
  { rank: 1, practiceItemId: "pi_1", learningObjectId: "lo", learningObjectTitle: null, practiceMode: "short_answer", prompt: "Swap two rows of [[1,2],[3,4]].", facetIds: [], rationale: null },
] };
const passageRun = { version: 1, tool: "find_sources", policy: "reading", toolCallId: "stc_p", runId: "r1", result: { passages: [
  { spanKey: "ext_book:s7", sourceTitle: "Linear Algebra Notes", section: "Determinants", page: 1, revisionId: "rev", text: "The determinant changes sign when two rows are swapped.", label: "source-authored" },
] } };
const compareRun = { version: 1, tool: "compare_sources", policy: "reading", toolCallId: "stc_c", runId: "r2", result: { status: "ok", sources: [
  { ref: "s1", sourceId: "src_book", sourceTitle: "Linear Algebra Notes", extractionId: "ext_book", spanId: "s7", page: 1, passage: "x", label: "source-authored", contributions: [{ contribution: "states the sign rule", quote: "changes sign" }] },
] } };

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  // The offers' state is the exchange's (Codex review F6); every test's exchange is "a1".
  defaultTutorOfferStore.clear();
  api.recordProposalImpressions.mockResolvedValue({ recorded: 1 });
  api.recordSourceOfferShown.mockResolvedValue({ interventionId: null, recorded: false });
});

function offers(extra: Partial<Parameters<typeof TutorOffers>[0]> = {}) {
  return <TutorOffers exchangeId="a1" extractionId="ext_text" practiceRequest={PRACTICE} toolRequests={[PASSAGES, COMPARE]} {...extra} />;
}

it("starts the practice and passage lookups when the answer lands and shows nothing until pressed", async () => {
  api.findPractice.mockResolvedValue(practiceResult);
  api.runSourceTool.mockResolvedValue(passageRun);
  render(offers());
  await waitFor(() => expect(api.findPractice).toHaveBeenCalledTimes(1));
  expect(api.findPractice).toHaveBeenCalledWith({ ...PRACTICE.request, caller: PRACTICE.caller });
  expect(api.runSourceTool).toHaveBeenCalledWith("stc_p");
  // The comparison waits for its press.
  expect(api.runSourceTool).not.toHaveBeenCalledWith("stc_c");
  await Promise.resolve();
  expect(screen.queryByText(/Swap two rows/)).toBeNull();
  expect(screen.queryByText(/changes sign when two rows/)).toBeNull();
  expect(api.recordProposalImpressions).not.toHaveBeenCalled();
  expect(api.recordSourceOfferShown).not.toHaveBeenCalled();
  // Buttons, each with the tutor's reason labelled as LearnLoop's.
  expect(screen.getByRole("button", { name: OFFER_COPY.practice })).toBeTruthy();
  expect(screen.getByRole("button", { name: /from your books: Your other book says it differently/ })).toBeTruthy();
  expect(screen.getByRole("button", { name: OFFER_COPY.compare })).toBeTruthy();
  expect(screen.getByText(`${OFFER_COPY.reasonLabel}: Your books differ here`)).toBeTruthy();
});

it("writes the impression and the exposure only on the press", async () => {
  api.findPractice.mockResolvedValue(practiceResult);
  api.runSourceTool.mockResolvedValue(passageRun);
  const pick = vi.fn();
  render(offers({ onPracticePick: pick }));
  await waitFor(() => expect(api.runSourceTool).toHaveBeenCalledTimes(1));
  await Promise.resolve();
  fireEvent.click(screen.getByRole("button", { name: OFFER_COPY.practice }));
  await screen.findByText(/Swap two rows/);
  await waitFor(() => expect(api.recordProposalImpressions).toHaveBeenCalledWith({
    proposalId: "prop_1", surface: "reader", keys: [{ kind: "item", practiceItemId: "pi_1" }],
  }));
  expect(api.recordSourceOfferShown).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: /from your books:/ }));
  await screen.findByText(/changes sign when two rows/);
  await waitFor(() => expect(api.recordSourceOfferShown).toHaveBeenCalledWith({ toolCallId: "stc_p", spanKeys: ["ext_book:s7"] }));
  // Only "practise" serves a proposal.
  fireEvent.click(screen.getByRole("button", { name: `${OFFER_COPY.practise} ▸` }));
  expect(pick).toHaveBeenCalledWith({ practiceItemId: "pi_1", prompt: "Swap two rows of [[1,2],[3,4]]." }, "prop_1");
  expect(api.recordProposalImpressions).toHaveBeenCalledTimes(1);
});

it("pressed before the lookup lands, the button says it is looking, in place", async () => {
  const pending = deferred<typeof practiceResult>();
  api.findPractice.mockReturnValue(pending.promise);
  api.runSourceTool.mockResolvedValue(passageRun);
  render(offers({ toolRequests: [] }));
  fireEvent.click(screen.getByRole("button", { name: OFFER_COPY.practice }));
  expect(screen.getByText(`${OFFER_COPY.looking}…`)).toBeTruthy();
  expect(api.recordProposalImpressions).not.toHaveBeenCalled();
  pending.resolve(practiceResult);
  await screen.findByText(/Swap two rows/);
  await waitFor(() => expect(api.recordProposalImpressions).toHaveBeenCalledTimes(1));
  expect(api.findPractice).toHaveBeenCalledTimes(1);
});

it("runs the comparison only when pressed", async () => {
  api.findPractice.mockResolvedValue(practiceResult);
  const comparing = deferred<typeof compareRun>();
  api.runSourceTool.mockImplementation((id: string) => (id === "stc_c" ? comparing.promise : Promise.resolve(passageRun)));
  render(offers());
  await waitFor(() => expect(api.runSourceTool).toHaveBeenCalledTimes(1));
  expect(api.runSourceTool).not.toHaveBeenCalledWith("stc_c");
  fireEvent.click(screen.getByRole("button", { name: OFFER_COPY.compare }));
  expect(api.runSourceTool).toHaveBeenCalledWith("stc_c");
  expect(screen.getByText(`${OFFER_COPY.comparing}…`)).toBeTruthy();
  comparing.resolve(compareRun);
  await screen.findByText(/states the sign rule/);
  await waitFor(() => expect(api.recordSourceOfferShown).toHaveBeenCalledWith({ toolCallId: "stc_c" }));
});

it("turns a lookup that found nothing into its plain line, with no impression", async () => {
  api.findPractice.mockResolvedValue({ ...practiceResult, items: [] });
  api.runSourceTool.mockResolvedValue({ ...passageRun, result: { passages: [] } });
  render(offers({ toolRequests: [PASSAGES] }));
  await waitFor(() => expect(screen.getAllByText(OFFER_COPY.nothing)).toHaveLength(2));
  expect(screen.queryByRole("button", { name: OFFER_COPY.practice })).toBeNull();
  expect(api.recordProposalImpressions).not.toHaveBeenCalled();
  expect(api.recordSourceOfferShown).not.toHaveBeenCalled();
});

it("keeps a failed lookup's button and runs it again on the press", async () => {
  api.runSourceTool.mockRejectedValueOnce(new Error("timed out")).mockResolvedValueOnce(passageRun);
  render(offers({ practiceRequest: null, toolRequests: [PASSAGES] }));
  await waitFor(() => expect(api.runSourceTool).toHaveBeenCalledTimes(1));
  await Promise.resolve();
  const button = await screen.findByRole("button", { name: /from your books:/ });
  fireEvent.click(button);
  await screen.findByText(/changes sign when two rows/);
  expect(api.runSourceTool).toHaveBeenCalledTimes(2);
  await waitFor(() => expect(api.recordSourceOfferShown).toHaveBeenCalledTimes(1));
});

it("offers the Reader's next step only on a cited line of the open source", async () => {
  const tryNext = vi.fn();
  render(offers({ practiceRequest: null, toolRequests: [], onTryNextStep: tryNext, buttons: [
    { kind: "try_next_step", extractionId: "ext_text", spanId: "t5", label: "try the next step first", role: "worked_example" },
    { kind: "try_next_step", extractionId: "ext_other", spanId: "x1", label: "try the next step first", role: "proof" },
  ] }));
  const buttons = screen.getAllByRole("button", { name: OFFER_COPY.nextStep });
  expect(buttons).toHaveLength(1);
  fireEvent.click(buttons[0]);
  expect(tryNext).toHaveBeenCalledWith("t5");
  expect(api.findPractice).not.toHaveBeenCalled();
  expect(api.runSourceTool).not.toHaveBeenCalled();
});

it("renders nothing without offers", () => {
  const { container } = render(offers({ practiceRequest: null, toolRequests: [] }));
  expect(container.innerHTML).toBe("");
});

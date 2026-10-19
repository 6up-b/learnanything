// RW1c Codex review fixes (docs/reviews/reader-rw1c-codex-review.md), frontend.
//
// F4: the impression names exactly the proposals rendered (at most three).
// F5: a lookup whose books could not be checked is not "nothing fits": it says
//     so, keeps its button and runs again on the press.
// F6: collapsing an answer and opening it again runs none of its lookups again.
// F9: a quoted excerpt and a citation from another book open where they are.
// F10: the tutor's comparison keeps its relations, unchecked sources and
//      missing perspectives (the Reader's own comparison table).
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { PracticeRequestDto, SourceToolRequestDto } from "../../api/dto";
import { ReaderAskBranches, type ReaderExchange } from "./ReaderAskBranches";
import { TutorAnswer, TUTOR_COPY } from "./TutorAnswer";
import { createTutorOfferStore, defaultTutorOfferStore, OFFER_COPY, TutorOffers } from "./TutorOffers";

const { api } = vi.hoisted(() => ({
  api: { findPractice: vi.fn(), runSourceTool: vi.fn(), recordProposalImpressions: vi.fn(), recordSourceOfferShown: vi.fn() },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
afterEach(cleanup);

const PRACTICE: PracticeRequestDto = {
  request: { query: "why?", learningObjectIds: [], facetIds: [], excludeItemIds: [], intent: "practice" },
  caller: { kind: "tutor", ref: "q1" }, version: "tutor_practice_request.v1",
};
const PASSAGES: SourceToolRequestDto = { toolCallId: "stc_p", tool: "find_sources", reason: "Your other book says it differently", run: "eager", dropped: [], arguments: {} };
const COMPARE: SourceToolRequestDto = { toolCallId: "stc_c", tool: "compare_sources", reason: "Your books differ here", run: "lazy", dropped: [], arguments: {} };

const item = (n: number) => ({ rank: n, practiceItemId: `pi_${n}`, learningObjectId: "lo", learningObjectTitle: null,
  practiceMode: "short_answer", prompt: `Problem number ${n}.`, facetIds: [], rationale: null });
const passageRun = { version: 1, tool: "find_sources", policy: "reading", toolCallId: "stc_p", runId: "r1", result: { status: "ok", passages: [
  { spanKey: "ext_book:s7", sourceTitle: "Linear Algebra Notes", section: "Determinants", page: 1, revisionId: "rev", text: "The determinant changes sign when two rows are swapped.", label: "source-authored" },
] } };

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  defaultTutorOfferStore.clear();
  api.recordProposalImpressions.mockResolvedValue({ recorded: 1 });
  api.recordSourceOfferShown.mockResolvedValue({ interventionId: null, recorded: false });
});

it("F4: the impression names exactly the proposals it shows", async () => {
  api.findPractice.mockResolvedValue({ version: 1, status: "ok", proposalId: "prop_1", items: [1, 2, 3, 4, 5].map(item) });
  render(<TutorOffers exchangeId="a1" extractionId="ext_text" practiceRequest={PRACTICE} toolRequests={[]} />);
  await waitFor(() => expect(api.findPractice).toHaveBeenCalledTimes(1));
  await Promise.resolve();
  fireEvent.click(screen.getByRole("button", { name: OFFER_COPY.practice }));
  await screen.findByText(/Problem number 1/);
  expect(screen.getAllByRole("listitem")).toHaveLength(3);
  await waitFor(() => expect(api.recordProposalImpressions).toHaveBeenCalledTimes(1));
  expect(api.recordProposalImpressions.mock.calls[0][0].keys).toEqual(
    [1, 2, 3].map((n) => ({ kind: "item", practiceItemId: `pi_${n}` })));
});

it("F5: a lookup whose books went unchecked says so and runs again on the press", async () => {
  const unchecked = { ...passageRun, result: { status: "unverified: over_budget: the daily cap is spent", passages: [] } };
  api.runSourceTool.mockResolvedValueOnce(unchecked).mockResolvedValueOnce(unchecked).mockResolvedValueOnce(passageRun);
  render(<TutorOffers exchangeId="a1" extractionId="ext_text" practiceRequest={null} toolRequests={[PASSAGES]} />);
  await waitFor(() => expect(api.runSourceTool).toHaveBeenCalledTimes(1));
  await Promise.resolve();
  expect(screen.queryByText(OFFER_COPY.nothing)).toBeNull();
  // The press runs it again (as a failed lookup does); still unchecked, it says so.
  fireEvent.click(screen.getByRole("button", { name: /from your books:/ }));
  expect(await screen.findByText(/couldn't be checked just now \(today's checking budget is used\)/)).toBeTruthy();
  expect(api.runSourceTool).toHaveBeenCalledTimes(2);
  expect(screen.queryByText(OFFER_COPY.nothing)).toBeNull();
  // Its button stays, and the next press runs it again.
  fireEvent.click(screen.getByRole("button", { name: /from your books:/ }));
  await screen.findByText(/changes sign when two rows/);
  expect(api.runSourceTool).toHaveBeenCalledTimes(3);
});

it("F5: an unavailable comparison is not shown as one", async () => {
  api.runSourceTool.mockResolvedValueOnce({ version: 1, tool: "compare_sources", policy: "reading", toolCallId: "stc_c", runId: "r2",
    result: { status: "unavailable: no route", sources: [{ ref: "s1", sourceId: "src_a", sourceTitle: "Book A", extractionId: "ext_a", spanId: "a1", page: 1, passage: "x", label: "source-authored" }] } });
  render(<TutorOffers exchangeId="a1" extractionId="ext_text" practiceRequest={null} toolRequests={[COMPARE]} />);
  fireEvent.click(screen.getByRole("button", { name: OFFER_COPY.compare }));
  expect(await screen.findByText(/couldn't be checked just now \(LearnLoop's model couldn't be reached\)/)).toBeTruthy();
  expect(screen.queryByText(/Book A/)).toBeNull();
  expect(api.recordSourceOfferShown).not.toHaveBeenCalled();
});

function exchange(extra: Partial<ReaderExchange> = {}): ReaderExchange {
  return {
    id: "a1", extractionId: "ext_text", spanId: "t3", question: "why?", answerMd: "Because.", answerMode: "answer_directly",
    citations: [], parentExchangeId: null, createdAt: null, ...extra,
  } as ReaderExchange;
}

const VIEW = {
  modes: ["excerpt", "grounded"] as Array<"excerpt" | "grounded" | "bridge">, bridgeMd: null, abstained: false, abstentionLine: null,
  droppedExcerpt: null, droppedBridge: null, intent: "explain" as const, personalized: true, retrieval: { status: "verified" },
  excerpt: { extractionId: "ext_book", spanId: "s7", quote: "The determinant changes sign.", label: "Linear Algebra Notes · Determinants",
    relation: "retrieved", sourceId: "src_book" },
};

it("F6: collapsing an answer and opening it again runs nothing again", async () => {
  api.findPractice.mockResolvedValue({ version: 1, status: "ok", proposalId: "prop_1", items: [item(1)] });
  api.runSourceTool.mockResolvedValue(passageRun);
  const store = createTutorOfferStore();
  const answer = exchange({ tutor: { ...VIEW, excerpt: null, modes: ["grounded"] },
    offers: { practiceRequest: PRACTICE, toolRequests: [PASSAGES], buttons: [] } });
  const branches = (collapsed: Set<string>) => (
    <ReaderAskBranches exchanges={[answer]} collapsedIds={collapsed} query="" busy={false} onToggle={vi.fn()}
      onFollowUp={vi.fn()} onShowPassage={vi.fn()} tutor={{ anotherWay: false, offers: true, busy: false, offerStore: store }} />
  );
  const { rerender } = render(branches(new Set()));
  await waitFor(() => expect(api.runSourceTool).toHaveBeenCalledTimes(1));
  fireEvent.click(screen.getByRole("button", { name: OFFER_COPY.practice }));
  await screen.findByText(/Problem number 1/);
  await waitFor(() => expect(api.recordProposalImpressions).toHaveBeenCalledTimes(1));
  rerender(branches(new Set(["a1"])));
  expect(screen.queryByText(/Problem number 1/)).toBeNull();
  rerender(branches(new Set()));
  // What was fetched and pressed is still there; nothing ran or was recorded twice.
  expect(await screen.findByText(/Problem number 1/)).toBeTruthy();
  await Promise.resolve();
  expect(api.findPractice).toHaveBeenCalledTimes(1);
  expect(api.runSourceTool).toHaveBeenCalledTimes(1);
  expect(api.recordProposalImpressions).toHaveBeenCalledTimes(1);
});

it("F9: an excerpt from another book opens there, even when it is not among the citations", () => {
  const open = vi.fn();
  render(<TutorAnswer exchange={exchange({ tutor: VIEW })}
    tutor={{ anotherWay: false, offers: false, busy: false, onOpenPassage: open }} />);
  fireEvent.click(screen.getByRole("button", { name: `${TUTOR_COPY.openPassage} ▸` }));
  expect(open).toHaveBeenCalledWith({ extractionId: "ext_book", spanId: "s7", sourceId: "src_book" });
});

it("F9: a citation from another book opens there", () => {
  const open = vi.fn();
  const shown = vi.fn();
  const answer = exchange({ tutor: VIEW, citations: [
    { extractionId: "ext_text", spanId: "t3", label: "this passage" },
    { extractionId: "ext_book", spanId: "s8", label: "Cofactor expansion", sourceId: "src_book" },
  ] });
  render(<ReaderAskBranches exchanges={[answer]} collapsedIds={new Set()} query="" busy={false} onToggle={vi.fn()}
    onShowPassage={shown} onFollowUp={vi.fn()} tutor={{ anotherWay: false, offers: false, busy: false, onOpenPassage: open }} />);
  fireEvent.click(screen.getByRole("button", { name: /source: Cofactor expansion/ }));
  expect(open).toHaveBeenCalledWith({ extractionId: "ext_book", spanId: "s8", sourceId: "src_book" });
  fireEvent.click(screen.getByRole("button", { name: /source: this passage/ }));
  expect(shown).toHaveBeenCalledWith("t3");
});

it("F10: the comparison keeps its relations, unchecked sources and missing perspectives", async () => {
  api.runSourceTool.mockResolvedValueOnce({ version: 1, tool: "compare_sources", policy: "reading", toolCallId: "stc_c", runId: "r2", result: {
    status: "ok",
    sources: [
      { ref: "s1", sourceId: "src_a", sourceTitle: "Book A", extractionId: "ext_a", spanId: "a1", page: 1, passage: "x", label: "source-authored",
        contributions: [{ contribution: "states the sign rule", perspective: null, quote: "changes sign" }] },
      { ref: "s2", sourceId: "src_b", sourceTitle: "Book B", extractionId: "ext_b", spanId: "b1", page: 2, passage: "y", label: "source-authored",
        contributions: [{ contribution: "derives it from permutations", perspective: null, quote: "odd permutation" }] },
    ],
    relations: [
      { leftRef: "s1", rightRef: "s2", relation: "different_assumptions", statement: "A assumes a square matrix; B any permutation", leftQuote: "square", rightQuote: "permutation" },
      { leftRef: "s1", rightRef: "s2", relation: "disagreement", statement: "They disagree on the zero-row case", leftQuote: "zero row", rightQuote: "undefined" },
    ],
    missingPerspectives: ["geometric"],
    unverifiedSources: [{ sourceId: "src_c", sourceTitle: "Book C" }],
  } });
  render(<TutorOffers exchangeId="a1" extractionId="ext_text" practiceRequest={null} toolRequests={[COMPARE]} />);
  fireEvent.click(screen.getByRole("button", { name: OFFER_COPY.compare }));
  await screen.findByText(/states the sign rule/);
  expect(screen.getAllByText("A assumes a square matrix; B any permutation").length).toBe(2);
  expect(screen.getAllByText("They disagree on the zero-row case").length).toBe(2);
  expect(screen.getByText(/Book C · possible match, not checked/)).toBeTruthy();
  expect(screen.getByText(`${OFFER_COPY.notCovered}: geometric`)).toBeTruthy();
  await waitFor(() => expect(api.recordSourceOfferShown).toHaveBeenCalledWith({ toolCallId: "stc_c" }));
});

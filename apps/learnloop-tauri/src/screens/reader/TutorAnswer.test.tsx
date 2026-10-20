// RW1c's three answer modes in the Reader (spec §4.6; UX §4.2, W3): "From
// your books" (the server's quote-verified excerpt, in the source's voice),
// LearnLoop's explanation and "connecting it to your work" (the model's
// voice), the abstention line when the books don't cover it, and "another
// way · that didn't help…" under the answer. Without RW1c's fields the answer
// is exactly the one model voice of before.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { ReaderTutorViewDto } from "../../api/dto";
import type { ReaderExchange } from "./ReaderAskBranches";
import { TUTOR_COPY, TutorAnswer, type TutorRailProps } from "./TutorAnswer";
import { ModelVoice } from "./voices";

vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../api/client", () => ({ api: {} }));
afterEach(cleanup);

const exchange = (tutor?: ReaderTutorViewDto): ReaderExchange => ({
  id: "a1", parentExchangeId: null, extractionId: "ext_text", spanId: "t3", selectionSpanIds: ["t3"],
  selectionQuoteMd: "the sign", question: "why?", answerMd: "Swapping flips the sign.", answerMode: "answer_directly",
  citations: [], createdAt: null, ...(tutor ? { tutor } : {}),
});
const view = (over: Partial<ReaderTutorViewDto> = {}): ReaderTutorViewDto => ({
  modes: ["grounded"], excerpt: null, bridgeMd: null, abstained: false, abstentionLine: null, droppedExcerpt: null,
  droppedBridge: null, intent: "explain", personalized: true, retrieval: { status: "verified" }, ...over,
});
const rail = (over: Partial<TutorRailProps> = {}): TutorRailProps => ({
  anotherWay: true, offers: false, busy: false, onAnotherWay: vi.fn(), onDidntHelp: vi.fn(), ...over,
});

it("is today's single model voice without RW1c's fields", () => {
  const { container } = render(<TutorAnswer exchange={exchange()} tutor={rail()} />);
  const { container: before } = render(<ModelVoice first><div>Swapping flips the sign.</div></ModelVoice>);
  expect(container.innerHTML).toBe(before.innerHTML);
  expect(screen.queryByRole("button", { name: TUTOR_COPY.anotherWay })).toBeNull();
});

it("shows the book's words first, then LearnLoop's explanation, then the bridge", () => {
  const { container } = render(<TutorAnswer exchange={exchange(view({
    modes: ["excerpt", "grounded", "bridge"],
    excerpt: { extractionId: "ext_book", spanId: "s7", quote: "The determinant changes sign.", label: "Linear Algebra Notes · Determinants", relation: "retrieved" },
    bridgeMd: "Your step \"swap rows\" is where it flips.",
  }))} tutor={rail()} />);
  const voices = Array.from(container.querySelectorAll("[data-voice]")).map((node) => node.getAttribute("data-voice"));
  expect(voices).toEqual(["source", "model", "model"]);
  expect(screen.getByText(/from your books · Linear Algebra Notes · Determinants/)).toBeTruthy();
  expect(screen.getByText(`LearnLoop's model · ${TUTOR_COPY.explanation}`, { exact: false })).toBeTruthy();
  expect(screen.getByText(new RegExp(TUTOR_COPY.bridge))).toBeTruthy();
});

it("opens with the abstention line and claims nothing from the books", () => {
  const line = "Your books don't cover this directly — this is LearnLoop's model's explanation";
  const { container } = render(<TutorAnswer exchange={exchange(view({ abstained: true, abstentionLine: line }))} tutor={rail()} />);
  expect(screen.getByText(line)).toBeTruthy();
  expect(container.querySelector("[data-voice='source']")).toBeNull();
  expect(screen.queryByText(new RegExp(TUTOR_COPY.explanation))).toBeNull();
});

it("labels how another way's passages differ", () => {
  render(<TutorAnswer exchange={exchange(view({ intent: "alternative", retrieval: { label: "from a different book" } }))} tutor={rail()} />);
  expect(screen.getByText("from a different book")).toBeTruthy();
});

it("asks another way, and that didn't help with optional text", () => {
  const onAnotherWay = vi.fn();
  const onDidntHelp = vi.fn();
  const target = exchange(view());
  render(<TutorAnswer exchange={target} tutor={rail({ onAnotherWay, onDidntHelp })} />);
  fireEvent.click(screen.getByRole("button", { name: TUTOR_COPY.anotherWay }));
  expect(onAnotherWay).toHaveBeenCalledWith(target);
  fireEvent.click(screen.getByRole("button", { name: TUTOR_COPY.didntHelp }));
  expect(screen.getByText(TUTOR_COPY.unclearPrompt)).toBeTruthy();
  fireEvent.change(screen.getByPlaceholderText(TUTOR_COPY.unclearPlaceholder), { target: { value: "why does a swap matter?" } });
  fireEvent.click(screen.getByRole("button", { name: `${TUTOR_COPY.send} · ctrl+↵` }));
  expect(onDidntHelp).toHaveBeenCalledWith(target, "why does a swap matter?");
  expect(screen.queryByText(TUTOR_COPY.unclearPrompt)).toBeNull();
});

it("has no another way while the contract does not offer it", () => {
  render(<TutorAnswer exchange={exchange(view())} tutor={rail({ anotherWay: false })} />);
  expect(screen.queryByRole("button", { name: TUTOR_COPY.anotherWay })).toBeNull();
  expect(screen.queryByRole("button", { name: TUTOR_COPY.didntHelp })).toBeNull();
});

it("renders no RW1c part of a saved answer while the contract supplies no controls (fix round 5, R4)", () => {
  // Both switches off: the history may still carry a saved RW1c view; the
  // answer is the one model voice of before, with neither excerpt nor bridge.
  const saved = exchange(view({
    modes: ["excerpt", "grounded", "bridge"],
    excerpt: { extractionId: "ext_book", spanId: "s7", quote: "The determinant changes sign.", label: "Linear Algebra Notes", relation: "retrieved" },
    bridgeMd: "Your step \"swap rows\" is where it flips.",
  }));
  const { container } = render(<TutorAnswer exchange={saved} />);
  expect(container.querySelector("[data-excerpt]")).toBeNull();
  expect(screen.queryByText(/swap rows/)).toBeNull();
  expect(screen.queryByText(/The determinant changes sign/)).toBeNull();
  const { container: before } = render(<ModelVoice first><div>Swapping flips the sign.</div></ModelVoice>);
  expect(container.innerHTML).toBe(before.innerHTML);
});

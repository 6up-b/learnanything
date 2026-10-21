// G54, the attention budget (UX §4.12): in reading and working nothing
// LearnLoop starts moves focus, opens a modal or animates. Selecting text and
// an answer landing leave focus where it was; no Reader component carries an
// animation or a transition (a lint over their sources and the Reader's CSS);
// skim mode shows nothing LearnLoop starts.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "./ReaderScreen";
import { readerRenderViewFixture as view } from "../fixtures/readerRenderView";
import type { SourceLibraryCard } from "../api/dto";
import { resetReaderActivityForTests } from "./reader/activity";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
  readerLogActivity: vi.fn(), readerSetMode: vi.fn(),
}));
const guide = vi.hoisted(() => ({ plan: { sections: [] as unknown[] } }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true, inquiryEnabled: true } : { sources: [initialSource.card] }, error: null }) }));
vi.mock("./reader/readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./reader/guidePlan", () => ({ readGuidePlan: () => Promise.resolve(guide.plan), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./reader/useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const initialSource = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };

beforeEach(() => {
  vi.resetAllMocks();
  resetReaderActivityForTests();
  guide.plan = { sections: [] };
  Element.prototype.scrollIntoView = vi.fn();
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerSetMode.mockResolvedValue({ mode: "skim" });
  api.readerAsk.mockResolvedValue({ eventId: "q", readerAnswerEventId: "a", parentExchangeId: null, answerMd: "Landed answer", answerMode: "answer_directly", citations: [], manifest: {} });
});
afterEach(cleanup);

function focusOutside(): HTMLButtonElement {
  const button = document.createElement("button");
  button.textContent = "elsewhere";
  document.body.appendChild(button);
  button.focus();
  return button;
}

it("selecting text leaves focus where it was", async () => {
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  const elsewhere = focusOutside();
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
  await screen.findByText(/^selected ·/);
  expect(document.activeElement).toBe(elsewhere);
  elsewhere.remove();
});

it("an answer landing leaves focus where it was", async () => {
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: "ask" }));
  fireEvent.change(await screen.findByPlaceholderText("ask about this passage…"), { target: { value: "Why?" } });
  const elsewhere = focusOutside();
  fireEvent.click(screen.getByRole("button", { name: "ask · ctrl+↵" }));
  await screen.findByText("Landed answer");
  await new Promise((resolve) => window.requestAnimationFrame(() => resolve(null)));
  expect(document.activeElement).toBe(elsewhere);
  elsewhere.remove();
});

it("skim mode shows no section offer (with inquiry on, skim is the mute button)", async () => {
  guide.plan = { sections: [{
    id: "u1", label: "Symmetric matrices", startSpanId: view.blocks[0].spanId, endSpanId: view.blocks[2].spanId,
    spanIds: view.blocks.map((b) => b.spanId), question: null,
    suggestedPassages: [{ spanId: view.blocks[1].spanId, quote: "q", reason: "r", learningObjectId: "lo", learningObjectTitle: "LO", learnerSignal: "new_material" }],
  }] };
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  expect(await screen.findByText("section break")).toBeTruthy();
  const [modeSelect] = screen.getAllByRole("combobox");
  fireEvent.keyDown(modeSelect, { key: "Enter" });
  fireEvent.mouseDown(await screen.findByRole("option", { name: "skim quickly" }));
  await waitFor(() => expect(screen.queryByText("section break")).toBeNull());
});

const READER_COMPONENTS: Record<string, string> = import.meta.glob(
  // RW2a: the workbench is a Reader posture too (G54). RW5a: the figures (their
  // only motion is a parameter the learner set or played).
  ["./ReaderScreen.tsx", "../components/PdfReaderPane.tsx", "./reader/*.tsx", "!./reader/*.test.tsx", "./workbench/*.tsx", "!./workbench/*.test.tsx",
    "./reader/figures/*.tsx", "!./reader/figures/*.test.tsx"],
  { query: "?raw", import: "default", eager: true },
);

it("lint: no Reader component animates or transitions", () => {
  const offenders: string[] = [];
  expect(Object.keys(READER_COMPONENTS).length).toBeGreaterThan(5);
  for (const [file, source] of Object.entries(READER_COMPONENTS)) {
    for (const pattern of [/\banimation\s*:/, /\btransition\s*:/, /ll-qc-blink|ll-reader-guide-alert|ll-reader-qc-strip/]) {
      if (pattern.test(source)) offenders.push(`${file}: ${pattern}`);
    }
  }
  expect(offenders).toEqual([]);
});

it("lint: the Reader's CSS has no keyframes, animations or transitions", () => {
  // vitest turns CSS imports into empty modules, so read the file itself.
  const css = readFileSync(join(__dirname, "..", "styles", "app.css"), "utf8");
  const rules = css.split("}").filter((rule: string) => /\.ll-(reader|qc|marquee|block-sweeping)/.test(rule));
  expect(rules.length).toBeGreaterThan(0);
  for (const rule of rules) expect(rule).not.toMatch(/animation|transition|@keyframes/);
  expect(css).not.toMatch(/ll-reader-quick-check-signal|ll-qc-blink/);
});

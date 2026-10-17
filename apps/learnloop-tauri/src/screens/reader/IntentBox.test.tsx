// RW1b's intent box on the Reader (spec §4.2; UX §4.1, W2, S3, S4; gates G3, G57):
// selecting text shows a small box under the selection that does NOT take
// focus (scroll keys still scroll); the first printable key focuses it and is
// typed into it; Tab opens the palette grouped by intention; Esc closes it;
// selecting never switches the rail tab. Routing starts once typing pauses
// (~600 ms) and Enter takes the routing already in flight; an empty Enter asks
// with no model call; a routed action makes exactly the palette's call.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../fixtures/readerIntentContract";
import type { SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerRouteIntent: vi.fn(), readerIntentRouting: vi.fn(), readerIntentOutcome: vi.fn(),
    readerInvokePreset: vi.fn(), readerCapture: vi.fn(), readerActiveQuestion: vi.fn(), readerActiveQuestionStatus: vi.fn(),
  },
  contract: { value: {} as Record<string, unknown> },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? contract.value : { sources: [source.card] }, error: null }) }));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };
const BOX = "What do you want to do with this?";

function routed(action: string, extra: Record<string, unknown> = {}) {
  const found = intent.palette.flatMap((g) => g.actions).find((a) => a.id === action)!;
  return {
    state: "done", routingId: `r_${action}`, speculative: false, action, status: "routed", reason: null,
    intention: found.intention, group: found.group, label: found.label, effect: found.effect, latencyMs: 900, ...extra,
  };
}

function select(block: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
}

async function openBox() {
  const result = render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  select(block);
  const box = await screen.findByRole("textbox", { name: BOX });
  return { result, block, box: box as HTMLInputElement };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  contract.value = { readerEnabled: true, inquiryEnabled: true, intent, activeReading: { foldBlocks: 3 } };
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerIntentOutcome.mockResolvedValue({ routingId: "r", recorded: true });
  api.readerInvokePreset.mockResolvedValue({ annotationId: "ann_1", anchorStatus: "exact", arc: null });
  api.readerAsk.mockResolvedValue({ eventId: "q", readerAnswerEventId: "a", parentExchangeId: null, answerMd: "Landed answer", answerMode: "help_me_reason", citations: [], manifest: {} });
});
afterEach(() => { cleanup(); vi.useRealTimers(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

it("a selection shows the box unfocused, and the rail does not switch tabs", async () => {
  const elsewhere = document.createElement("button");
  document.body.appendChild(elsewhere);
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  elsewhere.focus();
  select(block);
  const box = await screen.findByRole("textbox", { name: BOX });
  expect(document.activeElement).toBe(elsewhere);
  expect(document.activeElement).not.toBe(box);
  expect(screen.getByText("↵ ask · tab actions · esc")).toBeTruthy();
  // The rail stays where it was (the Guide); Notes' capture is not opened.
  expect(screen.queryByText(/^selected ·/)).toBeNull();
  elsewhere.remove();
});

it("scroll and copy keys keep their meaning while the box shows", async () => {
  const { box } = await openBox();
  for (const key of ["PageDown", "ArrowDown", "PageUp", " "]) {
    const event = new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true });
    window.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(false);
  }
  const copy = new KeyboardEvent("keydown", { key: "c", ctrlKey: true, bubbles: true, cancelable: true });
  window.dispatchEvent(copy);
  expect(copy.defaultPrevented).toBe(false);
  expect(document.activeElement).not.toBe(box);
});

it("the first printable key focuses the box and is typed into it, and single-key shortcuts are off", async () => {
  const { box } = await openBox();
  fireEvent.keyDown(window, { key: "w" });
  expect(document.activeElement).toBe(box);
  expect(box.value).toBe("w");
  // `w` (wrap up) did not run: the rail did not change.
  expect(screen.queryByText(/wrap up/i)).toBeNull();
});

it("? focuses the box without typing; Tab opens the palette grouped by intention; Esc closes it", async () => {
  const { box } = await openBox();
  fireEvent.keyDown(window, { key: "?" });
  expect(document.activeElement).toBe(box);
  expect(box.value).toBe("");
  fireEvent.keyDown(box, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  const headings = within(palette).getAllByRole("heading").map((h) => h.textContent);
  expect(headings).toEqual(["Understand", "Apply", "Consolidate", "Transfer", "Mark"]);
  expect(within(palette).getByRole("button", { name: "let me try the next step" })).toBeTruthy();
  fireEvent.keyDown(box, { key: "Escape" });
  await waitFor(() => expect(screen.queryByRole("textbox", { name: BOX })).toBeNull());
  expect(api.readerRouteIntent).not.toHaveBeenCalled();
});

it("an empty Enter asks with no model call: the Ask tab opens on the selection", async () => {
  const { box } = await openBox();
  fireEvent.keyDown(window, { key: "Enter" });
  expect(api.readerRouteIntent).not.toHaveBeenCalled();
  expect(await screen.findByPlaceholderText("ask about this passage…")).toBeTruthy();
  expect(api.readerAsk).not.toHaveBeenCalled();
  void box;
});

it("routing starts when typing pauses, and Enter takes the routing already made", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  api.readerRouteIntent.mockResolvedValue(routed("test_me_later", { speculative: true }));
  const { box } = await openBox();
  fireEvent.change(box, { target: { value: "quiz me on this later" } });
  expect(api.readerRouteIntent).not.toHaveBeenCalled();
  await act(async () => { vi.advanceTimersByTime(650); });
  await waitFor(() => expect(api.readerRouteIntent).toHaveBeenCalledTimes(1));
  expect(api.readerRouteIntent.mock.calls[0][0]).toMatchObject({ text: "quiz me on this later", speculative: true, extractionId: view.extractionId });
  fireEvent.keyDown(box, { key: "Enter" });
  await waitFor(() => expect(api.readerInvokePreset).toHaveBeenCalledTimes(1));
  expect(api.readerRouteIntent).toHaveBeenCalledTimes(1); // reused, not routed again
  expect(api.readerIntentOutcome).toHaveBeenCalledWith({ routingId: "r_test_me_later", outcome: "used" });
  expect(api.readerInvokePreset.mock.calls[0][0]).toMatchObject({ preset: "test_me_later", learnerText: "quiz me on this later" });
  expect(await screen.findByText(/Consolidate · revisit once \(test me later\)/)).toBeTruthy();
});

it("a changed text discards the speculative routing and Enter routes again", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  api.readerRouteIntent
    .mockResolvedValueOnce(routed("test_me_later", { speculative: true, routingId: "r1" }))
    .mockResolvedValueOnce(routed("connect_it", { routingId: "r2" }));
  const { box } = await openBox();
  fireEvent.change(box, { target: { value: "quiz me" } });
  await act(async () => { vi.advanceTimersByTime(650); });
  await waitFor(() => expect(api.readerRouteIntent).toHaveBeenCalledTimes(1));
  fireEvent.change(box, { target: { value: "connect this to eigenvalues" } });
  fireEvent.keyDown(box, { key: "Enter" });
  await waitFor(() => expect(api.readerRouteIntent).toHaveBeenCalledTimes(2));
  expect(api.readerRouteIntent.mock.calls[1][0]).toMatchObject({ text: "connect this to eigenvalues", speculative: false });
  await waitFor(() => expect(api.readerIntentOutcome).toHaveBeenCalledWith({ routingId: "r1", outcome: "discarded" }));
  await waitFor(() => expect(api.readerInvokePreset).toHaveBeenCalledTimes(1));
  expect(api.readerInvokePreset.mock.calls[0][0]).toMatchObject({ preset: "connect_it" });
});

it("a routed ask opens the Ask tab, because the learner asked, in the routed answer mode", async () => {
  api.readerRouteIntent.mockResolvedValue(routed("ask_help_me_reason"));
  const { box } = await openBox();
  fireEvent.change(box, { target: { value: "why are the densities weighted by p?" } });
  fireEvent.keyDown(box, { key: "Enter" });
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledTimes(1));
  expect(api.readerAsk.mock.calls[0][0]).toMatchObject({ question: "why are the densities weighted by p?", answerMode: "help_me_reason", spanId: view.blocks[1].spanId });
  expect(await screen.findByText("Landed answer")).toBeTruthy();
});

it("an unavailable Decider routes to Ask", async () => {
  api.readerRouteIntent.mockResolvedValue({ ...routed("ask_answer_directly"), status: "fallback", reason: "unavailable" });
  const { box } = await openBox();
  fireEvent.change(box, { target: { value: "what?" } });
  fireEvent.keyDown(box, { key: "Enter" });
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledTimes(1));
  expect(api.readerAsk.mock.calls[0][0]).toMatchObject({ question: "what?", answerMode: "answer_directly" });
});

it("change opens the palette with the text kept and records the learner's pick", async () => {
  api.readerRouteIntent.mockResolvedValue(routed("ask_help_me_reason"));
  let release: (value: unknown) => void = () => undefined;
  api.readerAsk.mockReturnValue(new Promise((resolve) => { release = resolve; }));
  const { box } = await openBox();
  fireEvent.change(box, { target: { value: "make this a card" } });
  fireEvent.keyDown(box, { key: "Enter" });
  fireEvent.click(await screen.findByRole("button", { name: "change" }));
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  expect((screen.getByRole("textbox", { name: BOX }) as HTMLInputElement).value).toBe("make this a card");
  fireEvent.click(within(palette).getByRole("button", { name: "help me remember" }));
  await waitFor(() => expect(api.readerIntentOutcome).toHaveBeenCalledWith({ routingId: "r_ask_help_me_reason", outcome: "corrected", action: "help_me_remember" }));
  await waitFor(() => expect(api.readerInvokePreset).toHaveBeenCalledTimes(1));
  expect(api.readerInvokePreset.mock.calls[0][0]).toMatchObject({ preset: "help_me_remember", learnerText: "make this a card" });
  release({ eventId: "q", readerAnswerEventId: "a", parentExchangeId: null, answerMd: "late", answerMode: "help_me_reason", citations: [], manifest: {} });
});

it("a palette pick makes exactly the Notes palette's call (G3)", async () => {
  const { box } = await openBox();
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "help me remember" }));
  await waitFor(() => expect(api.readerInvokePreset).toHaveBeenCalledTimes(1));
  const fromBox = { ...api.readerInvokePreset.mock.calls[0][0], clientIdempotencyKey: "k" };
  // The same preset from the Notes rail (the learner opens it themselves).
  fireEvent.click(screen.getByRole("button", { name: "notes" }));
  fireEvent.click(await screen.findByRole("button", { name: "help me remember" }));
  await waitFor(() => expect(api.readerInvokePreset).toHaveBeenCalledTimes(2));
  const fromNotes = { ...api.readerInvokePreset.mock.calls[1][0], clientIdempotencyKey: "k" };
  expect(fromBox).toEqual(fromNotes);
  expect(api.readerRouteIntent).not.toHaveBeenCalled();
  void box;
});

it("the box never appears for a selection inside the rail", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findByText(view.blocks[1].markdown);
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  const composer = await screen.findByPlaceholderText("ask about this passage…");
  fireEvent.mouseUp(composer);
  await new Promise((resolve) => setTimeout(resolve, 200));
  expect(screen.queryByRole("textbox", { name: BOX })).toBeNull();
});

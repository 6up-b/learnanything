// RW6a Codex review fixes in the Reader (docs/reviews/reader-rw6a-codex-review.md):
// F2 one commitment whichever surface asks "revisit once" (card, Wrap up, Ask
// chip), with the key reused on a retry; F5 "open" opens that inquiry on Ask
// (expanded, in view, with its crumb); F6 `w` opens Wrap up where it is seen;
// F9 skim mutes the card and the rail's offer.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "./ReaderScreen";
import { setAlgoConfig } from "../app/algoConfig";
import { readerRenderViewFixture as view } from "../fixtures/readerRenderView";
import type { SourceLibraryCard } from "../api/dto";
import { resetReaderActivityForTests } from "./reader/activity";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
  readerLogActivity: vi.fn(), readerRestoreSource: vi.fn(), readerSetInquiryStatus: vi.fn(),
  readerInvokePreset: vi.fn(), readerSetMode: vi.fn(),
  readerRecap: vi.fn(), readerRecapEvent: vi.fn(), readerWrapUp: vi.fn(),
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true, inquiryEnabled: true } : { sources: [source.card] }, error: null }) }));
vi.mock("./reader/readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./reader/guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./reader/useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };

const root = {
  eventId: "root", parentExchangeId: null, extractionId: view.extractionId, spanId: "span_symmetric_prose",
  questionMd: "Why weighted by p?", answerMd: "Saved answer", answerMode: "answer_directly", citations: [],
  selectionSpanIds: ["span_symmetric_prose"], selectionQuoteMd: "Saved exact selection", createdAt: null,
  questionEventId: "q_root", resolution: "open",
};

const SESSION = { sessionId: "v1", extractionId: view.extractionId, visitIds: ["v1"], startedAt: "2026-10-09T20:00:00Z", endedAt: "2026-10-09T20:40:00Z", minutes: 40 };
const RECAP = {
  recapVersion: "rw6a-recap-v1", extractionId: view.extractionId, session: SESSION,
  continueAt: { sectionId: "u1", label: "Symmetric matrices" },
  stillOpen: [{ rootExchangeId: "root", questionEventId: "q_root", questionMd: "Why weighted by p?", spanId: "span_symmetric_prose", anchorSpanIds: ["span_symmetric_prose"], openedAt: "2026-10-09T20:05:00Z" }],
  unfinished: [], worthASecondLook: [], sinceLastTime: { demonstrated: [], checksRetired: [] },
};
const WRAP_UP = {
  version: 1, wrapUpVersion: "rw6a-wrap-up-v1", available: true, extractionId: view.extractionId, session: SESSION,
  resolved: [], worthReinforcing: [],
  stillOpen: [{ rootExchangeId: "root", questionMd: "Why weighted by p?", spanIds: ["span_symmetric_prose"], actions: [
    { action: "revisit_once", rpc: "reader.invoke_preset", params: { preset: "test_me_later", spanIds: ["span_symmetric_prose"] }, where: "reader" },
    { action: "keep_open" },
  ] }],
};

let scrolled: Element[] = [];

beforeEach(() => {
  vi.resetAllMocks();
  resetReaderActivityForTests();
  setAlgoConfig({ recap: { enabled: true, wrapUpEnabled: true } });
  scrolled = [];
  Element.prototype.scrollIntoView = vi.fn(function (this: Element) { scrolled.push(this); });
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [root] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerRestoreSource.mockResolvedValue({ eventId: "restored" });
  api.readerSetMode.mockResolvedValue({ eventId: "m", mode: "skim", presentsOwnerQuestions: "never" });
  api.readerRecap.mockResolvedValue({ version: 1, recap: RECAP, dismissed: false });
  api.readerRecapEvent.mockResolvedValue({ version: 1, eventId: "ev", event: "recap_shown" });
  api.readerWrapUp.mockResolvedValue(WRAP_UP);
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); });

async function card() {
  return screen.findByRole("region", { name: "Last time here" });
}

// -- F2 ---------------------------------------------------------------------------------------

it("F2: revisit once from the card commits once, and the card and Wrap up then show it done", async () => {
  let land: (value: unknown) => void = () => undefined;
  api.readerInvokePreset.mockImplementation(() => new Promise((resolve) => { land = resolve; }));
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const recap = await card();
  const revisit = await within(recap).findByRole("button", { name: "revisit once" });
  fireEvent.click(revisit);
  fireEvent.click(revisit);
  await waitFor(() => expect(api.readerInvokePreset).toHaveBeenCalledTimes(1));
  await act(async () => { land({ annotationId: "ann", anchorStatus: "exact", arc: null }); });
  await waitFor(() => expect(within(recap).queryByRole("button", { name: "revisit once" })).toBeNull());
  expect(recap.textContent).toContain("revisit once ✓");
  // Wrap up shares the state: done, not offered again.
  fireEvent.click(await screen.findByRole("button", { name: "Wrap up (under a minute)" }));
  const panel = await screen.findByRole("region", { name: "Wrap up" });
  expect(within(panel).queryByRole("button", { name: "revisit once" })).toBeNull();
  expect(panel.textContent).toContain("revisit once ✓");
  expect(api.readerInvokePreset).toHaveBeenCalledTimes(1);
});

it("F2: a retry after an uncertain result reuses the request's key", async () => {
  api.readerInvokePreset.mockRejectedValueOnce(new Error("timed out")).mockResolvedValueOnce({ annotationId: "ann", anchorStatus: "exact", arc: null });
  const onError = vi.fn();
  render(<ReaderScreen initialSource={source} onError={onError} />);
  const recap = await card();
  fireEvent.click(await within(recap).findByRole("button", { name: "revisit once" }));
  await waitFor(() => expect(onError).toHaveBeenCalled());
  fireEvent.click(await within(recap).findByRole("button", { name: "revisit once" }));
  await waitFor(() => expect(api.readerInvokePreset).toHaveBeenCalledTimes(2));
  const [first, second] = api.readerInvokePreset.mock.calls.map((call) => (call[0] as { clientIdempotencyKey: string }).clientIdempotencyKey);
  expect(second).toBe(first);
});

// -- F5 ---------------------------------------------------------------------------------------

it("F5: open shows that inquiry on Ask, expanded and in view, with its crumb", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const recap = await card();
  fireEvent.click(within(recap).getByRole("button", { name: "open" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "ask" }).getAttribute("aria-pressed")).toBe("true"));
  const header = await screen.findByRole("button", { name: /Why weighted by p\?/, expanded: true });
  expect(header).toBeTruthy();
  await waitFor(() => expect(scrolled.some((element) => (element as HTMLElement).dataset?.askId === "root")).toBe(true));
  const strip = screen.getByRole("navigation", { name: "Detour" });
  expect(within(strip).getByRole("button", { name: /Why weighted by p\?/ })).toBeTruthy();
});

// -- F6 ---------------------------------------------------------------------------------------

it("F6: w from the Ask tab, or with the rail collapsed, opens Wrap up where it can be seen", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findByRole("button", { name: "Wrap up (under a minute)" });
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  fireEvent.keyDown(document.body, { key: "\\" }); // collapse the rail
  fireEvent.keyDown(document.body, { key: "w" });
  const panel = await screen.findByRole("region", { name: "Wrap up" });
  expect(screen.getByRole("complementary", { name: "Reading guide" }).contains(panel)).toBe(true);
  expect(screen.getByRole("button", { name: "guide" }).getAttribute("aria-pressed")).toBe("true");
  await waitFor(() => expect(api.readerRecapEvent).toHaveBeenCalledWith(expect.objectContaining({ event: "wrap_up_opened" })));
});

// -- F9 ---------------------------------------------------------------------------------------

it("F9: skim mutes the card and the rail's offer; w still opens Wrap up on request", async () => {
  const onSkimmingChange = vi.fn();
  render(<ReaderScreen initialSource={source} onError={vi.fn()} onSkimmingChange={onSkimmingChange} />);
  await card();
  await screen.findByRole("button", { name: "Wrap up (under a minute)" });
  const [modeSelect] = screen.getAllByRole("combobox");
  fireEvent.keyDown(modeSelect, { key: "Enter" });
  fireEvent.mouseDown(await screen.findByRole("option", { name: "skim quickly" }));
  await waitFor(() => expect(screen.queryByRole("region", { name: "Last time here" })).toBeNull());
  expect(screen.queryByRole("button", { name: /last time ▸/ })).toBeNull();
  expect(screen.queryByRole("button", { name: "Wrap up (under a minute)" })).toBeNull();
  expect(screen.queryByText("wrap up")).toBeNull();
  await waitFor(() => expect(onSkimmingChange).toHaveBeenLastCalledWith(true));
  fireEvent.keyDown(document.body, { key: "w" });
  expect(await screen.findByRole("region", { name: "Wrap up" })).toBeTruthy();
});

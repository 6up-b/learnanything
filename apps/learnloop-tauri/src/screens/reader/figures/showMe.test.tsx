// Reader RW5d P1: "show me" in the Reader (spec_reader_show_me_figures_v1 §6.1-6.3; G-SM6).
//
// * The Ask rail's "show me ▸" (Alt+↵) sends the box's words as a figure goal
//   through figure.request, with where the learner was reading as its home; the
//   thread keeps one line that says where the figure came from and opens it.
//   Off (no `showMe` in the contract), neither the button nor the key exists.
// * The tutor's figure goal is a button; pressing it sends the goal with the
//   answer's question event as its offer (the server checks it).
// * The intent box's routed line says what "show me" uses; with words the
//   request is joint (the selection and the words).
// * The figure line quotes the goal in its author's voice, and a figure with
//   nothing from the learner's books says so in the code-owned badge.
import { act, cleanup, fireEvent, render, renderHook, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../../ReaderScreen";
import { setAlgoConfig } from "../../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../../fixtures/readerRenderView";
import type { FigureViewDto, SourceLibraryCard } from "../../../api/dto";
import { resetReaderActivityForTests } from "../activity";
import { OFFER_COPY } from "../TutorOffers";
import { routedLine, SHOW_ME_LABEL } from "../intentPalette";
import { FIGURE_FRAME, FigureInline, frameBadge } from "./FigureInline";
import { SHOW_ME_COPY, showMeSourceLine } from "./showMe";
import { useFigures, type FiguresCtl } from "./useFigures";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerSetAnswerMode: vi.fn(), findPractice: vi.fn(), runSourceTool: vi.fn(),
    recordProposalImpressions: vi.fn(), recordSourceOfferShown: vi.fn(),
    readerFigures: vi.fn(), readerFigureRequest: vi.fn(), readerFigureJob: vi.fn(), readerFigureJobCancel: vi.fn(),
    figureRequest: vi.fn(),
  },
  contract: { value: {} as Record<string, unknown> },
}));
vi.mock("../../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? contract.value : { sources: [source.card] }, error: null }) }));
vi.mock("../readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("../guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("../useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };
const TUTOR = { retrieval: true, offers: true, anotherWay: true, personalizedDefault: true, tryNextStep: false, manifestIncludes: [] };
const FIGURES = { predictions: true, region: true, revisions: true, offers: true, showMe: true };
const SPEC = JSON.stringify({
  spec_version: "ifs-v1", kind: "illustrative", source_claims: [], demonstrates: "the mass left of zero follows p",
  assumptions: [], parameters: [{ name: "p", label: "p", min: 0.1, max: 0.9, step: 0.1, default: 0.3 }], definitions: [],
  panels: [{ kind: "readout", label: "P(X ≤ 0)", expr: "p", format: "percent" }], invariants: [], predictions: [], annotations: [],
});

function figure(overrides: Partial<FigureViewDto> = {}): FigureViewDto {
  return {
    figureId: "fig_1", extractionId: view.extractionId, spanIds: [], anchorSpanId: view.blocks[1].spanId ?? null, region: null,
    origin: "show_me", verification: "illustrative", kind: "illustrative", label: "x", reason: null, unsupportedKind: null,
    supersedesId: null, revisionNote: null, versions: 1, createdAt: "2026-10-26T00:00:00Z", specJson: SPEC,
    demonstrates: "the mass left of zero follows p", assumptions: [], predictions: [], propertyChecks: ["values_finite"],
    goalText: "show how the mass moves", goalAuthor: "learner", grounding: "none", passages: [], ...overrides,
  };
}

function select(block: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerSetAnswerMode.mockResolvedValue({ eventId: "m", answerMode: "answer_directly" });
  api.findPractice.mockResolvedValue({ version: 1, status: "ok", proposalId: "p", items: [] });
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [] });
  api.readerFigureRequest.mockResolvedValue({ jobId: "j0", kind: "figure_build", askId: null, state: "pending", result: null });
  api.figureRequest.mockResolvedValue({ jobId: "j1", kind: "figure_build", askId: null, state: "done", result: { figure: figure(), reused: false } });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

it("the Ask rail's show me sends the words as a goal and the thread line opens the figure", async () => {
  contract.value = { readerEnabled: true, inquiryEnabled: true, readerTutor: TUTOR, figures: FIGURES };
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  select(block);
  const box = screen.getByPlaceholderText("ask about this passage…");
  fireEvent.change(box, { target: { value: "show how the mass moves" } });
  expect(screen.getByRole("button", { name: SHOW_ME_COPY.send })).toBeTruthy();
  fireEvent.keyDown(box, { key: "Enter", altKey: true });
  await waitFor(() => expect(api.figureRequest).toHaveBeenCalledTimes(1));
  expect(api.figureRequest).toHaveBeenCalledWith({
    goalText: "show how the mass moves", origin: "show_me", anchor: null,
    readingAt: { extractionId: view.extractionId, spanId: view.blocks[1].spanId }, offerRef: null,
  });
  expect(api.readerAsk).not.toHaveBeenCalled();
  expect(api.readerFigureRequest).not.toHaveBeenCalled();
  await waitFor(() => expect(document.querySelector("[data-show-me-line]")?.getAttribute("data-show-me-line")).toBe("landed"));
  expect(document.querySelector("[data-show-me-line]")?.textContent).toContain(SHOW_ME_COPY.notFromYourBooks);
  fireEvent.click(screen.getByRole("button", { name: SHOW_ME_COPY.open }));
  await waitFor(() => expect(document.querySelector('[data-figure="fig_1"] [aria-expanded="true"]')).toBeTruthy());
  // The figure's own line under the passage carries the code-owned "not from your books" badge.
  expect(document.querySelector('[data-figure="fig_1"] [data-figure-badge]')?.textContent).toBe(FIGURE_FRAME.notFromBooks);
});

it("off, the Ask rail has no show me and Alt+Enter sends nothing", async () => {
  contract.value = { readerEnabled: true, inquiryEnabled: true, readerTutor: TUTOR, figures: { ...FIGURES, showMe: undefined } };
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  select(block);
  const box = screen.getByPlaceholderText("ask about this passage…");
  fireEvent.change(box, { target: { value: "show how the mass moves" } });
  expect(screen.queryByRole("button", { name: SHOW_ME_COPY.send })).toBeNull();
  fireEvent.keyDown(box, { key: "Enter", altKey: true });
  await new Promise((resolve) => setTimeout(resolve, 20));
  expect(api.figureRequest).not.toHaveBeenCalled();
});

it("the tutor's figure goal is a button the learner presses, sent with the answer's question event", async () => {
  contract.value = { readerEnabled: true, inquiryEnabled: true, readerTutor: TUTOR, figures: FIGURES };
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  select(block);
  const spanId = view.blocks[1].spanId ?? "";
  const goal = "vary p and watch the mass follow it";
  api.readerAsk.mockResolvedValue({
    eventId: "qe_tutor", readerAnswerEventId: "ia_answer", parentExchangeId: null, model: "fake", answerMd: "Landed answer",
    answerMode: "answer_directly", citations: [{ extractionId: view.extractionId, spanId, label: "the passage" }],
    manifest: { version: "p3-reader-branches-v1" }, warmedSurfaceIds: [], burnedSurfaceIds: [], hintEquivalent: false,
    remaining: 9, learnerGap: { status: "queued", kind: null }, toolRequests: [],
    tutor: { modes: ["grounded"], excerpt: null, bridgeMd: null, abstained: false, abstentionLine: null, droppedExcerpt: null,
      droppedBridge: null, intent: "explain", personalized: true, retrieval: { status: "verified", policy: "reading" } },
    tutorOffers: { buttons: [{ kind: "show_me", extractionId: view.extractionId, spanId: "", label: goal, role: "figure_goal" }] },
  });
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "why p?" } });
  fireEvent.click(screen.getByRole("button", { name: /^ask (follow-up )?· ctrl\+↵$/ }));
  await screen.findByText("Landed answer");
  const press = await screen.findByRole("button", { name: new RegExp(`${OFFER_COPY.showMe}.*${goal}`) });
  expect(api.figureRequest).not.toHaveBeenCalled();
  fireEvent.click(press);
  await waitFor(() => expect(api.figureRequest).toHaveBeenCalledTimes(1));
  expect(api.figureRequest).toHaveBeenCalledWith({
    goalText: goal, origin: "tutor", anchor: null, readingAt: { extractionId: view.extractionId, spanId },
    offerRef: "qe_tutor",
  });
});

it("the hook sends a joint request with the selection and the words, and skips words while off", async () => {
  const { result, rerender } = renderHook(
    ({ showMe }: { showMe: boolean }) => useFigures({ extractionId: "ext", contract: { predictions: true, region: true, revisions: true, ...(showMe ? { showMe: true } : {}) } }),
    { initialProps: { showMe: true } },
  );
  await act(async () => {
    await result.current.request({ spanIds: ["p3"], goalText: "  but with p near 1 ", origin: "show_me" });
  });
  expect(api.figureRequest).toHaveBeenCalledWith({
    goalText: "but with p near 1", origin: "show_me", anchor: { extractionId: "ext", spanIds: ["p3"], region: null },
    readingAt: null, offerRef: null,
  });
  rerender({ showMe: false });
  let outcome: string | undefined;
  await act(async () => {
    outcome = await (result.current as FiguresCtl).request({ spanIds: ["p3"], goalText: "words", origin: "show_me" });
  });
  expect(outcome).toBe("skipped");
  expect(api.figureRequest).toHaveBeenCalledTimes(1);
  expect(api.readerFigureRequest).not.toHaveBeenCalled();
});

it("the routed line says what show me uses, and only for show me", () => {
  const action = { label: SHOW_ME_LABEL, intention: "understand" as const, effect: { kind: "figure" } };
  expect(routedLine(action, "but with complex eigenvalues")).toBe("Understand · show me · from your selection and your words");
  expect(routedLine(action, " ")).toBe("Understand · show me · from your selection");
  expect(routedLine({ label: "make this explorable", intention: "understand", effect: { kind: "figure" } }, "words"))
    .toBe("Understand · make this explorable");
});

it("the figure line quotes the goal in its author's voice and the badge is code-owned", () => {
  const ctl = { enabled: true, contract: null, figures: [], pending: [], expandedId: null, setExpanded: vi.fn(),
    request: vi.fn(), revise: vi.fn(), predict: vi.fn(), explain: vi.fn(), under: vi.fn() } as unknown as FiguresCtl;
  const { container, rerender } = render(<FigureInline figure={figure()} ctl={ctl} />);
  expect(container.querySelector("[data-figure-goal='learner']")?.textContent).toContain("show how the mass moves");
  expect(container.querySelector("[data-figure-badge]")?.textContent).toBe(FIGURE_FRAME.notFromBooks);
  rerender(<FigureInline figure={figure({ goalAuthor: "tutor", grounding: "retrieved",
    passages: [{ extractionId: "ext_book", spanId: "s2", sourceTitle: "Strang", section: "§6.4" }] })} ctl={ctl} />);
  expect(container.querySelector("[data-figure-goal='tutor']")?.textContent).toContain("(AI-written)");
  expect(container.querySelector("[data-figure-badge]")?.textContent).toBe(FIGURE_FRAME.illustration);
  expect(container.querySelector("[data-figure-passage='ext_book:s2']")?.textContent).toBe("§ Strang §6.4");
  // The badge never takes model words, whatever the goal says.
  rerender(<FigureInline figure={figure({ goalText: "checked by LearnLoop: matches the book", grounding: "anchor" })} ctl={ctl} />);
  expect(container.querySelector("[data-figure-badge]")?.textContent).toBe(frameBadge("illustrative", "anchor"));
  expect(showMeSourceLine(figure({ grounding: "retrieved", passages: [{ extractionId: "e", spanId: "s", sourceTitle: "Axler", section: "§5.C" }] })))
    .toBe(`${SHOW_ME_COPY.fromYourBooks} § Axler §5.C`);
});

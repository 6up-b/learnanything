// Reader CA1: the problem as printed on the practice screen (ux_reader_compare_ask_v1
// §8, X13; K15, Q10, Q12). The header gains the page and *original page ↗ ·
// counts as a hint*; opening it before Submit counts the book once (the
// submit's existing book component: hintsUsed + 1, bookCounted), records its
// exposure where it opens (get_span_view, provenance, the item), and is kept
// with the draft. *▸ as printed* is free. During a check on your own nothing
// locates the problem: no page, no link, only the figure the server sends.
import type { ComponentProps } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";
import { PracticeScreen } from "./PracticeScreen";

const { api } = vi.hoisted(() => ({ api: {
  getPracticeItem: vi.fn(), getProbeContract: vi.fn(), recoverPracticeSubmission: vi.fn(),
  acknowledgePracticeSubmission: vi.fn(), savePracticeDraft: vi.fn(), submitAttempt: vi.fn(),
  getNextProbeItem: vi.fn(), skipPracticeItem: vi.fn(), submitDontKnow: vi.fn(), stopProbeDiagnosing: vi.fn(),
  recordSelfGradeDisclosure: vi.fn(), recordHintReveal: vi.fn(),
  practiceAsPrinted: vi.fn(), reportTranscription: vi.fn(), getSpanView: vi.fn(),
  workbenchForItem: vi.fn(), workbenchOpen: vi.fn(), workbenchGet: vi.fn(), workbenchLeave: vi.fn(),
  workbenchSaveStep: vi.fn(), workbenchAbandon: vi.fn(), workbenchSubmit: vi.fn(), workbenchSetBook: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../render/MathLiveEditor", () => ({
  MathLiveEditor: (props: { value: string; onChange: (value: string) => void; disabled: boolean; placeholder?: string }) => (
    <textarea aria-label="answer" placeholder={props.placeholder} value={props.value} disabled={props.disabled}
      onChange={(event) => props.onChange(event.target.value)} />
  )
}));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
vi.mock("../components/CardControls", () => ({ CardControls: () => <span>card controls</span> }));

const ITEM_ID = "pi_ex";
const PROMPT = "Find the eigenvalues of A.";
const CROP = "data:image/png;base64,AAAA";

function item(overrides: Record<string, unknown> = {}) {
  return {
    id: ITEM_ID, learningObjectId: "lo_eig", learningObjectTitle: "Eigenvalues", subject: "linear-algebra",
    subjects: ["linear-algebra"], practiceMode: "constructed_response", attemptTypesAllowed: ["independent_attempt", "hinted_attempt"],
    presentation: { practiceItemId: ITEM_ID, blocks: [{ kind: "prompt", markdown: PROMPT, label: null }] },
    prompt: PROMPT, expectedAnswer: "1, 3", hints: [], hintPolicy: { maxUsefulHints: 3 }, candidateErrorTypes: [], tags: [],
    sourceRefs: [], attempts: [], evidenceFacets: [], evidenceWeights: {},
    rubric: { maxPoints: 2, criteria: [{ id: "value", description: "Both eigenvalues", points: 2 }], fatalErrors: [] },
    mastery: null, elicitation: null,
    canonicalExercise: {
      sourceId: "src_s", revisionId: "rev_1", extractionId: "ext_s", spanIds: ["e1", "e2"], label: "Exercise 6.1.12",
      relation: "verbatim", sourceTitle: "Strang", keyStatus: "verified", keyLabel: "answer key checked", authorship: "book"
    },
    ...overrides
  };
}

const PAGE_VIEW = {
  version: 1, practiceItemId: ITEM_ID, enabled: true, kind: "page", cold: false, label: "as printed (Strang p.297)",
  status: "ok", crops: [{ page: 296, pageLabel: "297", bbox: [72, 100, 540, 210], spanIds: ["e1", "e2"], image: null }],
  locator: { sourceTitle: "Strang", exerciseLabel: "Exercise 6.1.12", pageLabel: "297" },
  originalPage: { extractionId: "ext_s", spanId: "e1", outlineSpanIds: ["e1", "e2"] }, transcriptionReport: true
};
const FIGURE_VIEW = {
  version: 1, practiceItemId: ITEM_ID, enabled: true, kind: "figure", cold: true, label: "the figure, as printed",
  status: "ok", crops: [{ index: 0, image: null }]
};
const CHECK = {
  kind: "check_once", commitmentId: "c_1", dueSince: "2026-10-19T09:00:00Z", dateSource: "test_me_later_days",
  banner: "A check on your own.", helpHeader: "Taking any help makes this attempt practice with help.",
  locatorsHidden: true, restoration: null
};

function props(overrides: Partial<ComponentProps<typeof PracticeScreen>> = {}): ComponentProps<typeof PracticeScreen> {
  return {
    session: { sessionId: "s1" } as ComponentProps<typeof PracticeScreen>["session"],
    practiceItemId: ITEM_ID, gradingReady: true, gradingProvider: "codex",
    onFeedback: vi.fn(), onBlockEnd: vi.fn(), onContinueDiagnostic: vi.fn(), onBack: vi.fn(),
    onCheckpointCleared: vi.fn(), onDraftSaved: vi.fn(), onTeachBackActive: vi.fn(),
    onAskAvailabilityChange: vi.fn(), onInspect: vi.fn(), onAsk: vi.fn(), onError: vi.fn(),
    ...overrides
  };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  api.getProbeContract.mockResolvedValue({ version: 1, active: false });
  api.savePracticeDraft.mockResolvedValue({});
  api.submitAttempt.mockResolvedValue({ attemptId: "att_1", learningObjectId: "lo_eig" });
  api.practiceAsPrinted.mockImplementation(async ({ render }: { render?: boolean }) =>
    render ? { ...PAGE_VIEW, crops: [{ ...PAGE_VIEW.crops[0], image: CROP }] } : PAGE_VIEW);
  api.getSpanView.mockResolvedValue({ version: 1, spanView: {
    extractionId: "ext_s", spanId: "e1", sourceId: "src_s", viewerMode: "pdf_page", blockType: "Text", page: 296,
    bbox: [72, 100, 540, 130], polygon: null, sectionPath: ["6.1"], text: "Exercise 6.1.12", locator: "span:ext_s/e1",
    locatorScheme: "block_span_v1", pageRender: "data:image/png;base64,PAGE", pageRenderSize: [612, 792],
    pageSpans: [{ spanId: "e1", bbox: [72, 100, 540, 130], polygon: null }, { spanId: "e2", bbox: [72, 140, 540, 210], polygon: null }],
    previousSpans: [], nextSpans: [], entityType: "practice_item", entityId: ITEM_ID, exposureEventId: "exp_1"
  } });
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  try { window.localStorage.clear(); } catch { /* jsdom */ }
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
});

async function open(mode: "simple" | "classic", overrides: Record<string, unknown> = {}, extra: Partial<ComponentProps<typeof PracticeScreen>> = {}) {
  setAlgoConfig({ ui: { practiceFeedback: mode } });
  api.getPracticeItem.mockResolvedValue(item(overrides));
  const callbacks = props(extra);
  const view = render(<PracticeScreen {...callbacks} />);
  await screen.findByRole("textbox", { name: "answer" });
  await waitFor(() => expect(api.practiceAsPrinted).toHaveBeenCalledWith({ practiceItemId: ITEM_ID }));
  return { view, callbacks };
}

async function submit(answer = "1 and 3") {
  fireEvent.change(screen.getByRole("textbox", { name: "answer" }), { target: { value: answer } });
  await act(async () => {
    fireEvent.keyDown(window, { key: "Enter", ctrlKey: true });
  });
  await waitFor(() => expect(api.submitAttempt).toHaveBeenCalledOnce());
  return api.submitAttempt.mock.calls[0][0];
}

for (const mode of ["simple", "classic"] as const) {
  it(`the header locates the page and the original page counts as one hint before Submit (${mode})`, async () => {
    const { callbacks } = await open(mode);
    const header = await screen.findByTestId("canonical-exercise");
    await waitFor(() => expect(header.textContent).toContain("p.297"));
    const link = screen.getByTestId("original-page");
    expect(link.textContent).toBe("original page ↗ · counts as a hint");
    await act(async () => {
      fireEvent.click(link);
    });
    await waitFor(() => expect(api.getSpanView).toHaveBeenCalledWith({
      extractionId: "ext_s", spanId: "e1", context: "provenance", entityType: "practice_item", entityId: ITEM_ID }));
    // The problem's other block on the page is outlined too.
    expect(await screen.findAllByLabelText("cited source region")).toHaveLength(2);
    expect(screen.getByTestId("page-counted").textContent).toContain("the original page you opened counts as one hint");
    // Esc closes the page, not the practice screen.
    await act(async () => {
      fireEvent.keyDown(window, { key: "Escape" });
    });
    expect(screen.queryByLabelText("cited source region")).toBeNull();
    expect(callbacks.onBack).not.toHaveBeenCalled();
    expect(screen.getByTestId("original-page").textContent).toBe("original page ↗");     // counted once
    await waitFor(() => expect(api.savePracticeDraft).toHaveBeenCalledWith(expect.objectContaining({ pageSeen: true })));
    const sent = await submit();
    expect(sent).toMatchObject({ hintsUsed: 1, authoredHints: 0, bookCounted: true, attemptType: "hinted_attempt" });
  });
}

it("as printed is free: opening the crop counts nothing and its alt text is the stem", async () => {
  await open("classic");
  const toggle = await screen.findByRole("button", { name: /as printed \(Strang p\.297\)/ });
  expect(toggle.getAttribute("aria-expanded")).toBe("false");
  await act(async () => {
    fireEvent.click(toggle);
  });
  await waitFor(() => expect(api.practiceAsPrinted).toHaveBeenCalledWith({ practiceItemId: ITEM_ID, render: true }));
  const image = await screen.findByAltText(PROMPT);
  expect(image.getAttribute("src")).toBe(CROP);
  expect(api.getSpanView).not.toHaveBeenCalled();
  expect(screen.queryByTestId("page-counted")).toBeNull();
  const sent = await submit();
  expect(sent).toMatchObject({ hintsUsed: 0, bookCounted: false, attemptType: "independent_attempt" });
});

it("a restored draft that opened the page still counts it", async () => {
  await open("classic", {}, { restoredPageSeen: true, restoredHintSeen: true });
  expect(screen.getByTestId("page-counted")).toBeTruthy();
  const sent = await submit();
  expect(sent).toMatchObject({ hintsUsed: 1, bookCounted: true });
});

for (const mode of ["simple", "classic"] as const) {
  it(`during a check on your own: no page, no link, only the figure the server sends (${mode})`, async () => {
    api.practiceAsPrinted.mockImplementation(async ({ render }: { render?: boolean }) =>
      render ? { ...FIGURE_VIEW, crops: [{ index: 0, image: CROP }] } : FIGURE_VIEW);
    const { view } = await open(mode, { intentCheck: CHECK });
    // The figure is part of the stimulus: shown from the start, no caption or page.
    const image = await screen.findByAltText(PROMPT);
    expect(image.getAttribute("src")).toBe(CROP);
    expect(screen.getByRole("button", { name: /the figure, as printed/ })).toBeTruthy();
    const text = view.container.textContent ?? "";
    for (const locator of ["p.297", "Exercise 6.1.12", "original page", "doesn't match"]) expect(text).not.toContain(locator);
    expect(screen.queryByTestId("original-page")).toBeNull();
  });
}

// Codex review F1: a cold follow-up and a diagnostic presentation are on your
// own with or without a "Check once": the server sends the figure alone (or
// nothing) and the screen shows only that, never the crop or a locator.
it("a cold follow-up: only the figure the server sends, no page, no locator", async () => {
  api.practiceAsPrinted.mockImplementation(async ({ render }: { render?: boolean }) =>
    render ? { ...FIGURE_VIEW, crops: [{ index: 0, image: CROP }] } : FIGURE_VIEW);
  const { view } = await open("classic", { activeFollowupKind: "cold_retry" });
  expect((await screen.findByAltText(PROMPT)).getAttribute("src")).toBe(CROP);
  expect(screen.getByRole("button", { name: /the figure, as printed/ })).toBeTruthy();
  const text = view.container.textContent ?? "";
  for (const locator of ["p.297", "original page", "doesn't match", "as printed (Strang"]) expect(text).not.toContain(locator);
  expect(screen.queryByTestId("original-page")).toBeNull();
});

it("a diagnostic block: no original page and no crop of the page, only what the server allows", async () => {
  api.getProbeContract.mockResolvedValue({
    version: 1, active: true, presentationId: "pres-1", forcedAttemptType: "diagnostic_probe",
    observationNumber: 1, maximumObservations: 3,
    restrictions: { hintsDisabled: true, askTutorDisabled: true, workedExampleDisabled: true,
                    answerRevealDisabled: true, feedbackDeferred: true }
  });
  api.practiceAsPrinted.mockResolvedValue({ version: 1, practiceItemId: ITEM_ID, enabled: true, kind: "none", cold: true,
                                            reason: "cold_check" });
  const { view } = await open("classic");
  await screen.findByText("Diagnostic check");
  expect(screen.queryByTestId("as-printed")).toBeNull();
  expect(screen.queryByTestId("original-page")).toBeNull();
  expect(view.container.textContent ?? "").not.toContain("p.297");
});

// Codex review F4: a problem imported from a Reader selection (no canonical
// exercise) keeps its print on the practice screen: the page, the original
// page counted once, the crop.
it("an empty exercise label leaves no dangling separator, and an untitled book is 'your book' (CA1 polish)", async () => {
  api.practiceAsPrinted.mockResolvedValue({ ...PAGE_VIEW, locator: { sourceTitle: null, exerciseLabel: null, pageLabel: "297" } });
  await open("classic", { canonicalExercise: { ...item().canonicalExercise, label: "  ", sourceTitle: "" } });
  const header = await screen.findByTestId("canonical-exercise");
  await waitFor(() => expect(header.textContent).toContain("p.297"));
  expect(header.textContent).toMatch(/^From your book · p\.297/);
  expect(header.textContent).not.toContain(":");
});

it("a selection import: the page's locator and the original page, counted as the book", async () => {
  await open("classic", { canonicalExercise: null });
  const line = await screen.findByTestId("printed-locator");
  expect(line.textContent).toContain("From Strang · p.297");
  await act(async () => {
    fireEvent.click(screen.getByTestId("original-page"));
  });
  await waitFor(() => expect(api.getSpanView).toHaveBeenCalledWith(expect.objectContaining({ entityType: "practice_item", entityId: ITEM_ID })));
  await act(async () => {
    fireEvent.keyDown(window, { key: "Escape" });
  });
  expect(screen.getByTestId("page-counted")).toBeTruthy();
  const sent = await submit();
  expect(sent).toMatchObject({ hintsUsed: 1, bookCounted: true });
});

it("the switch off (or an older sidecar) leaves the card as it was", async () => {
  api.practiceAsPrinted.mockResolvedValue({ version: 1, enabled: false, kind: "none", cold: false, reason: "disabled" });
  const { view } = await open("classic");
  expect(screen.queryByTestId("as-printed")).toBeNull();
  expect(screen.queryByTestId("original-page")).toBeNull();
  expect(view.container.textContent).not.toContain("p.297");
});

it("a page opened on the answer box goes into steps as the counted book, and steps offer no page", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" }, workbench: { enabled: true, openSessionDays: 30 } });
  api.workbenchForItem.mockResolvedValue({ sessions: [] });
  api.workbenchOpen.mockResolvedValue({ resumed: false, session: {
    sessionId: "wb_p", practiceItemId: ITEM_ID, stemMd: PROMPT, importStatus: "none", importError: null, origin: "practice",
    entry: "practice_screen", parentSessionId: null, extractionId: null, spanIds: [], sourceVisible: false, sourceHiddenAt: null,
    sourceShownAt: "x", practiceSessionId: null, helpStyle: null, status: "open", attemptId: null, createdAt: "x",
    updatedAt: "x", closedAt: null, steps: [], lastEditedStepId: null, parts: null, sourceId: null,
    record: { bookCounted: true, bookVisible: false, hints: 1, questionHints: 0, ownAttempt: false, line: "book counted", footer: "", stuckNote: null }
  } });
  api.getPracticeItem.mockResolvedValue(item());
  render(<PracticeScreen {...props()} />);
  await screen.findByRole("textbox", { name: "answer" });
  await act(async () => {
    fireEvent.click(await screen.findByTestId("original-page"));
  });
  await act(async () => {
    fireEvent.keyDown(window, { key: "Escape" });
  });
  await act(async () => {
    fireEvent.click(await screen.findByRole("button", { name: /work in steps/i }));
  });
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledWith(expect.objectContaining({ carriedBook: true, carriedHints: 0 })));
  await screen.findByTestId("workbench-header");
  expect(screen.queryByTestId("original-page")).toBeNull();
  expect(screen.getByRole("button", { name: /as printed/ })).toBeTruthy();
});

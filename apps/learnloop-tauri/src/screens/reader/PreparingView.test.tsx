// Reading while LearnLoop gets the book ready (docs/specs/ux_learnloop_v1.md §6.3, W2).
import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { SourceLibraryCard } from "../../api/dto";
import { PreparingView } from "./PreparingView";

const { api, pane } = vi.hoisted(() => ({
  api: { readerPdfView: vi.fn(), getSourceLibrary: vi.fn(), sourceAction: vi.fn() },
  pane: vi.fn()
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/core", () => ({ convertFileSrc: (path: string, scheme: string) => `${scheme}://${path}`, invoke: vi.fn() }));
vi.mock("../../components/PdfReaderPane", () => ({
  PdfReaderPane: (props: { fileUrl: string; blocks: unknown[] }) => {
    pane(props);
    return <div data-testid="pdf">{props.fileUrl}</div>;
  }
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.restoreAllMocks();
  vi.useRealTimers();
});

const CARD: SourceLibraryCard = {
  sourceId: "src_1",
  title: "Probability",
  acquisitionKind: "pdf",
  canonicalUri: "/books/probability.pdf",
  workId: null,
  currentRevisionId: "rev_1",
  revisionCount: 1,
  readiness: "processing",
  unitCount: 0,
  blockCount: 0,
  extractionStatus: "running",
  suggestedRole: null,
  readerEnabled: true,
  updateAvailable: false,
  kindNoun: "book",
  subjectId: null,
  statusLine: { text: "Getting this book ready", tone: "working", action: null, details: null }
};

const MANIFEST = {
  available: true,
  preparing: true,
  fileName: "sha256-abc",
  extractionId: null,
  sourceId: "src_1",
  revisionId: "rev_1",
  blocks: []
};

describe("PreparingView", () => {
  it("shows the original PDF at once with one quiet status line", async () => {
    api.readerPdfView.mockResolvedValue(MANIFEST);
    api.getSourceLibrary.mockResolvedValue({ version: 1, sources: [CARD] });
    render(<PreparingView card={CARD} onBack={vi.fn()} onReady={vi.fn()} onError={vi.fn()} />);
    expect(screen.getByText("Probability")).toBeTruthy();
    expect(screen.getByText(/Getting this book ready/)).toBeTruthy();
    expect(await screen.findByTestId("pdf")).toBeTruthy();
    expect(screen.getByTestId("pdf").textContent).toBe("llpdf://sha256-abc");
    expect(pane).toHaveBeenCalledWith(expect.objectContaining({ blocks: [] }));
    expect(api.readerPdfView).toHaveBeenCalledWith({ extractionId: "src_1" });
    // Text-dependent features say when, on their own line; nothing is greyed out silently.
    expect(screen.getByText(/available in a minute or two/)).toBeTruthy();
  });

  // Usability round 1 (U7): a scan showed "◐ Couldn't read this PDF" over
  // "available in a minute or two". A book LearnLoop couldn't read says so,
  // offers its one action, and promises nothing.
  it("a book LearnLoop couldn't read says so, with its one action, and promises nothing", async () => {
    const scan: SourceLibraryCard = {
      ...CARD,
      readiness: "needs_extraction",
      statusLine: { text: "This PDF is a scan", tone: "quiet", action: { kind: "text_recognition", label: "Read it with text recognition" }, details: null }
    };
    api.readerPdfView.mockResolvedValue(MANIFEST);
    api.getSourceLibrary.mockResolvedValue({ version: 1, sources: [scan] });
    api.sourceAction.mockResolvedValue({ version: 1, sourceId: "src_1", action: "text_recognition", batchId: "b2" });
    render(<PreparingView card={scan} onBack={vi.fn()} onReady={vi.fn()} onError={vi.fn()} />);
    expect(await screen.findByTestId("pdf")).toBeTruthy();

    expect(screen.getByText("This PDF is a scan")).toBeTruthy();
    expect(screen.queryByText(/◐/)).toBeNull();
    expect(screen.queryByText(/available in a minute or two/)).toBeNull();
    screen.getByRole("button", { name: "Read it with text recognition" }).click();
    await waitFor(() => expect(api.sourceAction).toHaveBeenCalledWith({ sourceId: "src_1", action: "text_recognition" }));
  });

  it("says the book opens here when there is no original to show", async () => {
    api.readerPdfView.mockResolvedValue({ ...MANIFEST, available: false, fileName: null });
    api.getSourceLibrary.mockResolvedValue({ version: 1, sources: [CARD] });
    const web = { ...CARD, acquisitionKind: "web", kindNoun: "article", statusLine: { text: "Getting this article ready", tone: "working" as const, action: null, details: null } };
    render(<PreparingView card={web} onBack={vi.fn()} onReady={vi.fn()} onError={vi.fn()} />);
    expect(await screen.findByText("It opens here as soon as it is ready.")).toBeTruthy();
    expect(screen.queryByTestId("pdf")).toBeNull();
  });

  it("hands over to the full Reader as soon as the text is ready", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    api.readerPdfView.mockResolvedValue(MANIFEST);
    const ready = { ...CARD, readiness: "ready" as const, unitCount: 5, blockCount: 80, statusLine: null };
    api.getSourceLibrary.mockResolvedValueOnce({ version: 1, sources: [CARD] }).mockResolvedValue({ version: 1, sources: [ready] });
    const onReady = vi.fn();
    render(<PreparingView card={CARD} onBack={vi.fn()} onReady={onReady} onError={vi.fn()} />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(7000);
    });
    await waitFor(() => expect(onReady).toHaveBeenCalledWith(ready, null));
  });

  it("hands over at the page and place the learner scrolled to (review F8)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    api.readerPdfView.mockResolvedValue(MANIFEST);
    const ready = { ...CARD, readiness: "ready" as const, unitCount: 5, blockCount: 80, statusLine: null };
    api.getSourceLibrary.mockResolvedValueOnce({ version: 1, sources: [CARD] }).mockResolvedValue({ version: 1, sources: [ready] });
    const onReady = vi.fn();
    render(<PreparingView card={CARD} onBack={vi.fn()} onReady={onReady} onError={vi.fn()} />);
    const scroller = await screen.findByTestId("preparing-scroll");
    // The learner has scrolled to page 20 while the text was being prepared.
    scroller.insertAdjacentHTML(
      "beforeend",
      '<div data-pdf-page="18" data-width-points="612"></div><div data-pdf-page="19" data-width-points="612"></div>'
    );
    vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
      const page = (this as HTMLElement).dataset?.pdfPage;
      const top = page === "18" ? -900 : page === "19" ? -300 : 0;
      const height = page === undefined ? 700 : 800;
      return { top, bottom: top + height, height, width: 600, left: 0, right: 600, x: 0, y: top, toJSON: () => ({}) } as DOMRect;
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(7000);
    });
    await waitFor(() => expect(onReady).toHaveBeenCalled());
    const [card, position] = onReady.mock.calls[0];
    expect(card).toEqual(ready);
    expect(position.page).toBe(19);
    expect(position.offset).toBeCloseTo(300 / 800);
  });

  it("goes back to the Library", () => {
    api.readerPdfView.mockResolvedValue(MANIFEST);
    api.getSourceLibrary.mockResolvedValue({ version: 1, sources: [CARD] });
    const onBack = vi.fn();
    render(<PreparingView card={CARD} onBack={onBack} onReady={vi.fn()} onError={vi.fn()} />);
    screen.getByRole("button", { name: "← Library" }).click();
    expect(onBack).toHaveBeenCalled();
  });
});

// Exam protection by extraction identity, Codex review F4: the preparing
// Reader's marking sends back the reading and the proposal it showed, and a
// fresh confirmation returned for a stale one is asked again, never dropped.
describe("PreparingView marking exam material", () => {
  const HELD_BACK: SourceLibraryCard = {
    ...CARD,
    readiness: "ready",
    statusLine: {
      text: "This reading is held back until you mark its exam material",
      tone: "problem",
      action: { kind: "mark_exam_material", label: "Mark exam material on this reading" },
      details: null
    }
  };
  const SHOWN = {
    sourceId: "src_1",
    extractionId: "ext_b",
    revisionId: "rev_1",
    heldOutUnitIds: ["u2"],
    proposalHash: "sha256:b",
    needsConfirmation: true,
    title: "Mark exam material on this reading of Probability?",
    lines: ["Held out as exam material: Exam.", "These are suggested from what you marked before: check them."],
    confirmLabel: "Mark them",
    cancelLabel: "Not now"
  };
  const FRESH = {
    ...SHOWN,
    extractionId: "ext_c",
    heldOutUnitIds: [],
    proposalHash: "sha256:c",
    lines: [
      "This reading changed since you looked, so nothing was marked yet. Check it again:",
      "Nothing in this reading matches the exam material you marked before."
    ],
    confirmLabel: "Mark it"
  };
  const asking = (confirmation: typeof SHOWN) => ({
    version: 1, sourceId: "src_1", action: "mark_exam_material", needsConfirmation: true, confirmation
  });

  const open = async () => {
    api.readerPdfView.mockResolvedValue(MANIFEST);
    api.getSourceLibrary.mockResolvedValue({ version: 1, sources: [HELD_BACK] });
    render(<PreparingView card={HELD_BACK} onBack={vi.fn()} onReady={vi.fn()} onError={vi.fn()} />);
    expect(await screen.findByTestId("pdf")).toBeTruthy();
    await act(async () => {
      screen.getByRole("button", { name: "Mark exam material on this reading" }).click();
    });
  };

  it("sends the reading and the proposal shown, and asks again when they changed", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    api.sourceAction
      .mockResolvedValueOnce(asking(SHOWN))
      .mockResolvedValueOnce(asking(FRESH))
      .mockResolvedValueOnce({
        version: 1, sourceId: "src_1", action: "mark_exam_material",
        marked: { extractionId: "ext_c", heldOutUnitIds: [], fromExtractionIds: [] }
      });
    await open();
    await waitFor(() => expect(api.sourceAction).toHaveBeenCalledTimes(3));
    expect(api.sourceAction.mock.calls.map((call) => call[0])).toEqual([
      { sourceId: "src_1", action: "mark_exam_material" },
      { sourceId: "src_1", action: "mark_exam_material", confirmed: true, confirmedExtractionId: "ext_b", confirmedProposalHash: "sha256:b" },
      { sourceId: "src_1", action: "mark_exam_material", confirmed: true, confirmedExtractionId: "ext_c", confirmedProposalHash: "sha256:c" }
    ]);
    expect(confirm).toHaveBeenCalledTimes(2);
    expect(confirm.mock.calls[1][0]).toContain("This reading changed since you looked, so nothing was marked yet.");
  });

  it("marks nothing when the learner says not now to the fresh confirmation", async () => {
    vi.spyOn(window, "confirm").mockReturnValueOnce(true).mockReturnValueOnce(false);
    api.sourceAction.mockResolvedValueOnce(asking(SHOWN)).mockResolvedValueOnce(asking(FRESH));
    await open();
    await waitFor(() => expect(api.sourceAction).toHaveBeenCalledTimes(2));
    await act(async () => {
      await Promise.resolve();
    });
    expect(api.sourceAction).toHaveBeenCalledTimes(2);
  });
});

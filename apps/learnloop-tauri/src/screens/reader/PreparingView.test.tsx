// Reading while LearnLoop gets the book ready (docs/specs/ux_learnloop_v1.md §6.3, W2).
import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { SourceLibraryCard } from "../../api/dto";
import { PreparingView } from "./PreparingView";

const { api, pane } = vi.hoisted(() => ({
  api: { readerPdfView: vi.fn(), getSourceLibrary: vi.fn() },
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

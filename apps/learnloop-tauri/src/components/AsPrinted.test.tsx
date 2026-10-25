// Reader CA1: the problem-as-printed controls on their own (ux_reader_compare_ask_v1
// §8.2-§8.4, X13, X14): waiting and "no original" in place, the transcription
// report with the learner's optional text, your photo with its date, the
// per-device open memory, and the multi-block crop for Reader candidates and
// the book's solution.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { AsPrintedViewDto } from "../api/dto";
import { AS_PRINTED_COPY, AS_PRINTED_OPEN_KEY, AsPrinted, BlocksAsPrinted, PrintedAfterFeedback } from "./AsPrinted";

const { api } = vi.hoisted(() => ({ api: {
  practiceAsPrinted: vi.fn(), reportTranscription: vi.fn(), readerProblemCrops: vi.fn(), getCaptureMedia: vi.fn(),
  getSpanView: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));

const PAGE: AsPrintedViewDto = {
  enabled: true, kind: "page", cold: false, label: "as printed (Strang p.297)", status: "ok",
  crops: [{ page: 296, pageLabel: "297", bbox: [1, 2, 3, 4], spanIds: ["e1"], image: null }],
  locator: { sourceTitle: "Strang", exerciseLabel: "Exercise 6.1.12", pageLabel: "297" },
  originalPage: { extractionId: "ext", spanId: "e1", outlineSpanIds: ["e1"] }, transcriptionReport: true
};

let store: Map<string, string>;
beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  store = new Map();
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, String(v)),
      removeItem: (k: string) => void store.delete(k),
      clear: () => store.clear(),
    },
  });
});
afterEach(() => cleanup());

it("says it is cropping, then that the page image is not available, never another picture", async () => {
  let resolve: (value: AsPrintedViewDto) => void = () => {};
  api.practiceAsPrinted.mockReturnValue(new Promise<AsPrintedViewDto>((done) => { resolve = done; }));
  render(<AsPrinted view={PAGE} practiceItemId="pi" altText="Find λ." />);
  fireEvent.click(screen.getByRole("button", { name: /as printed/ }));
  expect(screen.getByRole("status").textContent).toContain(AS_PRINTED_COPY.pending);
  await act(async () => {
    resolve({ ...PAGE, status: "no_original" });
  });
  expect(screen.getByRole("status").textContent).toBe(AS_PRINTED_COPY.noOriginal);
  expect(screen.queryByRole("img")).toBeNull();
  // Opening is remembered on this device.
  expect(store.get(AS_PRINTED_OPEN_KEY)).toBe("1");
});

it("opens by itself where the device remembers it open", async () => {
  store.set(AS_PRINTED_OPEN_KEY, "1");
  api.practiceAsPrinted.mockResolvedValue({ ...PAGE, crops: [{ ...PAGE.crops![0], image: "data:image/png;base64,A" }] });
  render(<AsPrinted view={PAGE} practiceItemId="pi" altText="Find λ." />);
  expect((await screen.findByAltText("Find λ.")).getAttribute("src")).toBe("data:image/png;base64,A");
  fireEvent.click(screen.getByRole("button", { name: /zoom in/ }));
  expect((screen.getByAltText("Find λ.") as HTMLImageElement).style.width).toBe("150%");
});

it("reports the transcription with the learner's optional text, once", async () => {
  store.set(AS_PRINTED_OPEN_KEY, "1");
  api.practiceAsPrinted.mockResolvedValue({ ...PAGE, crops: [{ ...PAGE.crops![0], image: "data:image/png;base64,A" }] });
  api.reportTranscription.mockResolvedValue({ noticeId: "n1", status: "active", reports: 1 });
  render(<AsPrinted view={PAGE} practiceItemId="pi" altText="Find λ." />);
  fireEvent.click(await screen.findByRole("button", { name: /the transcription doesn't match the page/ }));
  fireEvent.change(screen.getByRole("textbox"), { target: { value: "  the sign of the 2 is minus  " } });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /send/ }));
  });
  expect(api.reportTranscription).toHaveBeenCalledWith({ practiceItemId: "pi", note: "the sign of the 2 is minus" });
  expect(screen.getByRole("status").textContent).toBe(AS_PRINTED_COPY.mismatchSent);
});

it("a card from a photo shows your photo with its date", async () => {
  api.getCaptureMedia.mockResolvedValue({ captureId: "cap", mime: "image/png", dataUrl: "data:image/png;base64,P" });
  const view: AsPrintedViewDto = { enabled: true, kind: "photo", cold: false, label: "your photo",
    photo: { captureId: "cap", capturedAt: "2026-10-04T08:00:00+00:00" } };
  render(<AsPrinted view={view} practiceItemId="pi" altText="Find λ." />);
  const toggle = screen.getByRole("button", { name: /your photo \(/ });
  expect(toggle.textContent).toMatch(/your photo \(.*4.*\)/);
  fireEvent.click(toggle);
  await waitFor(() => expect(api.getCaptureMedia).toHaveBeenCalledWith("cap"));
  expect((await screen.findByAltText("your photo of this problem")).getAttribute("src")).toBe("data:image/png;base64,P");
  expect(screen.queryByText(/doesn't match/)).toBeNull();
});

const BLOCKS = { extractionId: "ext", spanIds: ["s1", "s2"], status: "ok" as const, skippedSpanIds: [],
  crops: [{ page: 3, pageLabel: "4", bbox: [1, 2, 3, 4], spanIds: ["s1", "s2"], image: null as string | null }] };

it("a problem known by its blocks is cropped through the multi-block form, after a cheap first read", async () => {
  api.readerProblemCrops.mockImplementation(async ({ render }: { render?: boolean }) =>
    render === false ? BLOCKS : { ...BLOCKS, crops: [{ ...BLOCKS.crops[0], image: "data:image/png;base64,S" }] });
  render(<BlocksAsPrinted extractionId="ext" spanIds={["s1", "s2"]} label={AS_PRINTED_COPY.solutionAsPrinted} altText="the solution" />);
  await waitFor(() => expect(api.readerProblemCrops).toHaveBeenCalledWith({ extractionId: "ext", spanIds: ["s1", "s2"], render: false }));
  fireEvent.click(await screen.findByRole("button", { name: /the solution as printed/ }));
  await waitFor(() => expect(api.readerProblemCrops).toHaveBeenCalledWith({ extractionId: "ext", spanIds: ["s1", "s2"] }));
  expect((await screen.findByAltText("the solution")).getAttribute("src")).toBe("data:image/png;base64,S");
});

// Codex review F3: the switch off answers `disabled` and the host shows no
// *as printed* (a candidate, the book's solution, a workbench problem); no
// page or no box shows nothing either.
for (const status of ["disabled", "no_geometry", "not_found"] as const) {
  it(`a problem known by its blocks shows nothing when the server crops nothing (${status})`, async () => {
    api.readerProblemCrops.mockResolvedValue({ ...BLOCKS, status, crops: [] });
    const { container } = render(<BlocksAsPrinted extractionId="ext" spanIds={["s1"]} altText="x" />);
    await waitFor(() => expect(api.readerProblemCrops).toHaveBeenCalledOnce());
    expect(container.textContent).toBe("");
    expect(api.readerProblemCrops).toHaveBeenCalledTimes(1);
  });
}

it("a learner-drawn region rides with both reads (§12.4)", async () => {
  api.readerProblemCrops.mockResolvedValue(BLOCKS);
  const region = { spanId: "s1", page: 3, bbox: [1, 2, 3, 4] };
  render(<BlocksAsPrinted extractionId="ext" spanIds={["s1"]} altText="x" region={region} />);
  fireEvent.click(await screen.findByRole("button", { name: /as printed/ }));
  await waitFor(() => expect(api.readerProblemCrops).toHaveBeenCalledWith({ extractionId: "ext", spanIds: ["s1"], region }));
  expect(api.readerProblemCrops).toHaveBeenCalledWith({ extractionId: "ext", spanIds: ["s1"], render: false, region });
});

// Codex review F5: a page known without a box says the crop can't be made,
// and nothing stands in for it.
it("a page without a box: the crop says it can't be made, no picture", async () => {
  const view: AsPrintedViewDto = { ...PAGE, status: "no_geometry", crops: [], notice: AS_PRINTED_COPY.noCrop };
  api.practiceAsPrinted.mockResolvedValue(view);
  render(<AsPrinted view={view} practiceItemId="pi" altText="Find λ." />);
  fireEvent.click(screen.getByRole("button", { name: /as printed/ }));
  await waitFor(() => expect(screen.getByRole("status").textContent).toBe(AS_PRINTED_COPY.noCrop));
  expect(screen.queryByRole("img")).toBeNull();
});

// §8.3 (Codex review F6): *open in the Reader ↗* from the original page.
it("after feedback the original page opens the page itself and offers the Reader", async () => {
  api.practiceAsPrinted.mockResolvedValue({ ...PAGE, originalPage: { ...PAGE.originalPage!, sourceId: "src" } });
  api.getSpanView.mockResolvedValue({ spanView: { extractionId: "ext", spanId: "e1", viewerMode: "pdf_page", blockType: "Text",
    sectionPath: [], text: "t", locator: "span:ext/e1", locatorScheme: "block_span_v1", pageRender: "data:image/png;base64,P",
    pageRenderSize: [612, 792], bbox: [1, 2, 3, 4], pageSpans: [], previousSpans: [], nextSpans: [] } });
  const onOpenInReader = vi.fn();
  render(<PrintedAfterFeedback practiceItemId="pi" altText="Find λ." onOpenInReader={onOpenInReader} />);
  fireEvent.click(await screen.findByTestId("original-page"));
  await waitFor(() => expect(api.getSpanView).toHaveBeenCalledWith(expect.objectContaining({ extractionId: "ext", spanId: "e1",
    context: "provenance", entityType: "practice_item", entityId: "pi" })));
  fireEvent.click(await screen.findByTestId("open-in-reader"));
  expect(onOpenInReader).toHaveBeenCalledWith({ extractionId: "ext", spanId: "e1", outlineSpanIds: ["e1"], sourceId: "src" });
  expect(screen.queryByTestId("open-in-reader")).toBeNull();
});

it("after feedback: the full locator and a free, unlabelled original page", async () => {
  api.practiceAsPrinted.mockResolvedValue(PAGE);
  render(<PrintedAfterFeedback practiceItemId="pi" altText="Find λ." />);
  const block = await screen.findByTestId("feedback-as-printed");
  expect(block.textContent).toContain("Exercise 6.1.12 · Strang p.297");
  expect(screen.getByTestId("original-page").textContent).toBe(AS_PRINTED_COPY.originalPage);
});

it("nothing at all when the server shows nothing (a check due, the switch off, an older sidecar)", async () => {
  api.practiceAsPrinted.mockResolvedValue({ enabled: true, kind: "none", cold: true, reason: "cold_check" });
  const { container } = render(<PrintedAfterFeedback practiceItemId="pi" altText="x" />);
  await waitFor(() => expect(api.practiceAsPrinted).toHaveBeenCalled());
  expect(container.textContent).toBe("");
  api.practiceAsPrinted.mockReset();
  api.practiceAsPrinted.mockImplementation(() => { throw new TypeError("not a function"); });
  const older = render(<PrintedAfterFeedback practiceItemId="pi2" altText="x" />);
  expect(older.container.textContent).toBe("");
});

// Codex re-review F11: *open in the Reader ↗* opens the passage on screen,
// after the viewer's next/prev moved it, not the one the page opened at.
it("after next in the original page, the Reader opens the passage shown now", async () => {
  api.practiceAsPrinted.mockResolvedValue({ ...PAGE, originalPage: { ...PAGE.originalPage!, sourceId: "src" } });
  const spanView = (spanId: string, previous: string[], next: string[]) => ({ spanView: {
    extractionId: "ext", spanId, viewerMode: "pdf_page", blockType: "Text", sectionPath: [], text: `text ${spanId}`,
    locator: `span:ext/${spanId}`, locatorScheme: "block_span_v1", pageRender: "data:image/png;base64,P",
    pageRenderSize: [612, 792], bbox: [1, 2, 3, 4], pageSpans: [],
    previousSpans: previous.map((id) => ({ spanId: id, text: id, truncated: false })),
    nextSpans: next.map((id) => ({ spanId: id, text: id, truncated: false })) } });
  api.getSpanView.mockImplementation(({ spanId }: { spanId: string }) =>
    Promise.resolve(spanId === "e1" ? spanView("e1", [], ["e9"]) : spanView("e9", ["e1"], [])));
  const onOpenInReader = vi.fn();
  render(<PrintedAfterFeedback practiceItemId="pi" altText="Find λ." onOpenInReader={onOpenInReader} />);
  fireEvent.click(await screen.findByTestId("original-page"));
  fireEvent.click(await screen.findByRole("button", { name: "next →" }));
  await screen.findByText("text e9");
  fireEvent.click(screen.getByTestId("open-in-reader"));
  expect(onOpenInReader).toHaveBeenCalledWith({ extractionId: "ext", spanId: "e9", outlineSpanIds: ["e1"], sourceId: "src" });
});

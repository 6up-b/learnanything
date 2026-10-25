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

it("a problem known by its blocks is cropped through the multi-block form", async () => {
  api.readerProblemCrops.mockResolvedValue({ extractionId: "ext", spanIds: ["s1", "s2"], status: "ok", skippedSpanIds: [],
    crops: [{ page: 3, pageLabel: "4", bbox: [1, 2, 3, 4], spanIds: ["s1", "s2"], image: "data:image/png;base64,S" }] });
  render(<BlocksAsPrinted extractionId="ext" spanIds={["s1", "s2"]} label={AS_PRINTED_COPY.solutionAsPrinted} altText="the solution" />);
  fireEvent.click(screen.getByRole("button", { name: /the solution as printed/ }));
  await waitFor(() => expect(api.readerProblemCrops).toHaveBeenCalledWith({ extractionId: "ext", spanIds: ["s1", "s2"] }));
  expect((await screen.findByAltText("the solution")).getAttribute("src")).toBe("data:image/png;base64,S");
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

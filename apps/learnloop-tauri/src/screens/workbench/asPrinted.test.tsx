// Reader CA1 in the Reader workbench, the Codex review's fixes (F3, F4, F6):
// *original page ↗* opens the page itself (OpenInSource's page view, the
// problem's blocks outlined), only where the server found a page image, and
// *open in the Reader ↗* there takes the book pane to it; the switch off
// leaves neither the button nor a crop, bound or not; a problem opened from a
// region selection crops the learner's region before it binds.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ComponentProps } from "react";
import { Workbench } from "./Workbench";
import type { WorkbenchSessionDto } from "../../api/dto";

const api = vi.hoisted(() => ({
  workbenchSaveStep: vi.fn(), workbenchSetBook: vi.fn(), workbenchLeave: vi.fn(), workbenchAbandon: vi.fn(),
  workbenchReopen: vi.fn(), workbenchRefreshImport: vi.fn(), workbenchBind: vi.fn(), workbenchRetryImport: vi.fn(),
  workbenchSubmit: vi.fn(), workbenchGet: vi.fn(),
  practiceAsPrinted: vi.fn(), readerProblemCrops: vi.fn(), getSpanView: vi.fn(), reportTranscription: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => () => {}, destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../render/LiveMarkdownEditor", () => ({
  LiveMarkdownEditor: (p: { value: string; onChange: (value: string) => void; ariaLabel?: string }) => (
    <textarea aria-label={p.ariaLabel} value={p.value} onChange={(event) => p.onChange(event.target.value)} />
  ),
}));

function session(overrides: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return {
    sessionId: "wb1", practiceItemId: "pi_514", stemMd: "Exercise 5.14 Find the CDF of X.",
    importStatus: "none", importError: null, origin: "reader", entry: "work_through", parentSessionId: null,
    extractionId: "ext1", spanIds: ["b2", "b3"], sourceVisible: true, sourceHiddenAt: null, sourceShownAt: null,
    practiceSessionId: null, helpStyle: null, status: "open", attemptId: null, createdAt: "2026-10-17T09:00:00Z",
    updatedAt: "2026-10-17T09:00:00Z", closedAt: null, steps: [], lastEditedStepId: null,
    record: { bookCounted: true, bookVisible: true, hints: 1, questionHints: 0, ownAttempt: false, line: "book open", footer: "", stuckNote: null },
    parts: null, sourceId: "src1", ...overrides,
  };
}

function props(overrides: Partial<ComponentProps<typeof Workbench>> = {}): ComponentProps<typeof Workbench> {
  return {
    initial: session(), layout: "split", practiceSessionId: "ps1",
    onSession: vi.fn(), onLeave: vi.fn(), onAbandoned: vi.fn(), onSubmitted: vi.fn(), onError: vi.fn(),
    onPeekPassage: vi.fn(), ...overrides,
  };
}

const VIEW = {
  version: 1, practiceItemId: "pi_514", enabled: true, kind: "page", cold: false, label: "as printed (Book p.12)",
  status: "ok", crops: [{ page: 11, pageLabel: "12", bbox: [1, 2, 3, 4], spanIds: ["b2", "b3"], image: null }],
  locator: { sourceTitle: "Book", exerciseLabel: "Exercise 5.14", pageLabel: "12" },
  originalPage: { extractionId: "ext1", spanId: "b2", outlineSpanIds: ["b2", "b3"], sourceId: "src1" }, transcriptionReport: true,
};
const BLOCKS = { extractionId: "ext1", spanIds: ["b2", "b3"], status: "ok", skippedSpanIds: [],
  crops: [{ page: 11, pageLabel: "12", bbox: [1, 2, 3, 4], spanIds: ["b2", "b3"], image: null }] };

beforeEach(() => {
  vi.resetAllMocks();
  api.getSpanView.mockResolvedValue({ spanView: {
    extractionId: "ext1", spanId: "b2", viewerMode: "pdf_page", blockType: "Text", sectionPath: ["5"], text: "Exercise 5.14",
    locator: "span:ext1/b2", locatorScheme: "block_span_v1", pageRender: "data:image/png;base64,PAGE", pageRenderSize: [612, 792],
    bbox: [72, 100, 540, 130], page: 11, pageSpans: [{ spanId: "b2", bbox: [72, 100, 540, 130] }, { spanId: "b3", bbox: [72, 140, 540, 170] }],
    previousSpans: [], nextSpans: [],
  } });
});
afterEach(cleanup);

it("a bound problem's original page opens the page itself, not a jump in the text, and the Reader from there", async () => {
  api.practiceAsPrinted.mockResolvedValue(VIEW);
  const onPeekPassage = vi.fn();
  render(<Workbench {...props({ onPeekPassage })} />);
  fireEvent.click(await screen.findByTestId("workbench-original-page"));
  await waitFor(() => expect(api.getSpanView).toHaveBeenCalledWith(expect.objectContaining({
    extractionId: "ext1", spanId: "b2", context: "provenance", entityType: "practice_item", entityId: "pi_514" })));
  expect(onPeekPassage).not.toHaveBeenCalled();
  expect(await screen.findByText("pdf_page")).toBeTruthy();
  fireEvent.click(screen.getByTestId("open-in-reader"));
  expect(onPeekPassage).toHaveBeenCalledWith("b2", { extractionId: "ext1" });
  expect(screen.queryByTestId("open-in-reader")).toBeNull();
});

// Codex re-review F11: the passage on screen after next/prev, not the first one.
it("after prev in the original page, the Reader opens the passage shown now", async () => {
  api.practiceAsPrinted.mockResolvedValue(VIEW);
  const base = { viewerMode: "pdf_page", blockType: "Text", sectionPath: ["5"], locatorScheme: "block_span_v1",
    pageRender: "data:image/png;base64,PAGE", pageRenderSize: [612, 792], bbox: [72, 100, 540, 130], page: 11, pageSpans: [] };
  api.getSpanView.mockImplementation(({ spanId }: { spanId: string }) => Promise.resolve({ spanView: spanId === "b2"
    ? { ...base, extractionId: "ext1", spanId: "b2", text: "Exercise 5.14", locator: "span:ext1/b2",
        previousSpans: [{ spanId: "b1", text: "b1", truncated: false }], nextSpans: [] }
    : { ...base, extractionId: "ext1", spanId: "b1", text: "the worked example", locator: "span:ext1/b1",
        previousSpans: [], nextSpans: [{ spanId: "b2", text: "b2", truncated: false }] } }));
  const onPeekPassage = vi.fn();
  render(<Workbench {...props({ onPeekPassage })} />);
  fireEvent.click(await screen.findByTestId("workbench-original-page"));
  fireEvent.click(await screen.findByRole("button", { name: "← prev" }));
  await screen.findByText("the worked example");
  fireEvent.click(screen.getByTestId("open-in-reader"));
  expect(onPeekPassage).toHaveBeenCalledWith("b1", { extractionId: "ext1" });
});

it("no original page where the server found no page image, and none while the book is hidden", async () => {
  api.practiceAsPrinted.mockResolvedValue({ ...VIEW, status: "no_original", originalPage: null, notice: "x" });
  render(<Workbench {...props()} />);
  await screen.findByTestId("as-printed");
  expect(screen.queryByTestId("workbench-original-page")).toBeNull();
  cleanup();
  api.practiceAsPrinted.mockResolvedValue(VIEW);
  render(<Workbench {...props({ initial: session({ sourceVisible: false }) })} />);
  await screen.findByTestId("as-printed");
  expect(screen.queryByTestId("workbench-original-page")).toBeNull();
});

it("the switch off: a bound problem shows neither the crop nor the original page", async () => {
  api.practiceAsPrinted.mockResolvedValue({ version: 1, enabled: false, kind: "none", cold: false, reason: "disabled" });
  render(<Workbench {...props()} />);
  await waitFor(() => expect(api.practiceAsPrinted).toHaveBeenCalled());
  expect(screen.queryByTestId("as-printed")).toBeNull();
  expect(screen.queryByTestId("workbench-original-page")).toBeNull();
});

it("the switch off: a problem not yet bound shows neither the crop nor the original page", async () => {
  api.readerProblemCrops.mockResolvedValue({ ...BLOCKS, status: "disabled", crops: [] });
  render(<Workbench {...props({ initial: session({ practiceItemId: null, importStatus: "pending" }) })} />);
  await waitFor(() => expect(api.readerProblemCrops).toHaveBeenCalled());
  expect(screen.queryByTestId("blocks-as-printed")).toBeNull();
  expect(screen.queryByTestId("workbench-original-page")).toBeNull();
  expect(api.practiceAsPrinted).not.toHaveBeenCalled();
});

it("a problem not yet bound: its blocks' crop, its region, and the original page from the blocks' read", async () => {
  api.readerProblemCrops.mockResolvedValue(BLOCKS);
  const region = { spanId: "b3", page: 11, bbox: [80, 140, 300, 170] };
  const onPeekPassage = vi.fn();
  render(<Workbench {...props({ onPeekPassage, initial: session({ practiceItemId: null, importStatus: "pending", printRegion: region }) })} />);
  await waitFor(() => expect(api.readerProblemCrops).toHaveBeenCalledWith({ extractionId: "ext1", spanIds: ["b2", "b3"], render: false, region }));
  expect(api.readerProblemCrops).toHaveBeenCalledTimes(1);                  // one read serves the crop and the page
  expect(await screen.findByTestId("blocks-as-printed")).toBeTruthy();
  fireEvent.click(screen.getByTestId("workbench-original-page"));
  await waitFor(() => expect(api.getSpanView).toHaveBeenCalledWith(expect.objectContaining({ extractionId: "ext1", spanId: "b2", entityType: null })));
  expect(onPeekPassage).not.toHaveBeenCalled();
});

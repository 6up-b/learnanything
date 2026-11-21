// A section finished before its book is ready (docs/reviews/ux31-section-done-before-build.md): "Get the whole book
// ready for questions at once" (once "Build questions for the whole book at once") on a book whose every chapter is already built or being built queued a planner that found
// nothing, and the card was left with no line. The press now says what is true, and queues nothing.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ComponentProps } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { SourceLibraryCard } from "../api/dto";
import { clear } from "../api/queryCache";
import { findJargon } from "../copy/denyList";
import { LibraryPlace } from "./LibraryPlace";

const api = vi.hoisted(() => ({ getSourceLibrary: vi.fn(), sourceAction: vi.fn(), cancelIngestBatch: vi.fn() }));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn() }));
vi.mock("@tauri-apps/api/webview", () => ({ getCurrentWebview: () => ({ onDragDropEvent: () => Promise.resolve(() => {}) }) }));
vi.mock("../components/IntentControl", () => ({ IntentControl: () => null }));

const CARD: SourceLibraryCard = {
  sourceId: "src_sym",
  title: "Symmetric Matrices and Variance",
  acquisitionKind: "web",
  canonicalUri: "https://example.org/sym",
  workId: null,
  currentRevisionId: "rev_1",
  revisionCount: 1,
  readiness: "ready",
  unitCount: 1,
  blockCount: 59,
  extractionStatus: "completed",
  suggestedRole: null,
  readerEnabled: true,
  updateAvailable: false,
  kindNoun: "article",
  statusLine: { text: "Questions for this article are written as you finish sections", tone: "quiet", action: null, details: null }
};

function place() {
  api.getSourceLibrary.mockResolvedValue({ version: 1, sources: [CARD], pending: [] });
  const props: ComponentProps<typeof LibraryPlace> = {
    view: "books",
    onViewChange: vi.fn(),
    filesProps: {} as ComponentProps<typeof LibraryPlace>["filesProps"],
    aiConnection: null,
    onOpenBook: vi.fn(),
    onConnectAi: vi.fn(),
    onOpenImports: vi.fn(),
    onOpenChanges: vi.fn(),
    onOpenSettings: vi.fn(),
    onAdd: vi.fn(),
    addBusy: false,
    addMessage: null,
    dragging: false,
    openWhenReady: null,
    onOpenedWhenReady: vi.fn(),
    booksOnly: true
  };
  return render(<LibraryPlace {...props} />);
}

beforeEach(() => {
  clear();
  for (const fn of Object.values(api)) fn.mockReset();
});

afterEach(() => cleanup());

it("the whole-book press on an article already built says so, in plain words, as a status and not a failure", async () => {
  const NOTICE = "All of this article is ready for questions. Each section's questions are written when you finish it.";
  api.sourceAction.mockResolvedValue({ version: 1, sourceId: "src_sym", action: "build_whole_book", notice: NOTICE });
  place();
  fireEvent.click(await screen.findByRole("button", { name: "details ▸" }));
  fireEvent.click(screen.getByRole("button", { name: "Get the whole article ready for questions at once" }));
  await waitFor(() => expect(api.sourceAction).toHaveBeenCalledWith({ sourceId: "src_sym", action: "build_whole_book" }));
  const told = await screen.findByTestId("library-told");
  expect(told.textContent).toBe(NOTICE);
  expect(told.getAttribute("role")).toBe("status");
  expect(findJargon(NOTICE)).toEqual([]);
  // The card keeps its own line.
  expect(screen.getByText("Questions for this article are written as you finish sections")).toBeTruthy();
});

it("a press that started a build says nothing of its own: the card's line shows the build", async () => {
  api.sourceAction.mockResolvedValue({ version: 1, sourceId: "src_sym", action: "build_whole_book", batchId: "batch_1" });
  place();
  fireEvent.click(await screen.findByRole("button", { name: "details ▸" }));
  fireEvent.click(screen.getByRole("button", { name: "Get the whole article ready for questions at once" }));
  await waitFor(() => expect(api.sourceAction).toHaveBeenCalled());
  await waitFor(() => expect(api.getSourceLibrary.mock.calls.length).toBeGreaterThan(1));
  expect(screen.queryByTestId("library-told")).toBeNull();
});

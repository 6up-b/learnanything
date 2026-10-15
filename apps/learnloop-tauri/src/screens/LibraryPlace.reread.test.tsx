// Re-read safety (docs/reviews/reread-safety.md): reading a book again that the
// learner studies asks first, naming the pages, the cost and what moves to the
// new reading; the E1 repair is one tap on the card.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ComponentProps } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { SourceLibraryCard } from "../api/dto";
import { clear } from "../api/queryCache";
import { LibraryPlace } from "./LibraryPlace";

const api = vi.hoisted(() => ({ getSourceLibrary: vi.fn(), sourceAction: vi.fn(), cancelIngestBatch: vi.fn() }));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn() }));
vi.mock("@tauri-apps/api/webview", () => ({ getCurrentWebview: () => ({ onDragDropEvent: () => Promise.resolve(() => {}) }) }));

const CARD: SourceLibraryCard = {
  sourceId: "src_axler",
  title: "Linear Algebra Done Right",
  acquisitionKind: "pdf",
  canonicalUri: "/books/axler.pdf",
  workId: null,
  currentRevisionId: "rev_1",
  revisionCount: 1,
  readiness: "ready",
  unitCount: 60,
  blockCount: 489,
  extractionStatus: "completed",
  suggestedRole: null,
  readerEnabled: true,
  updateAvailable: false,
  kindNoun: "book",
  textRecognitionAvailable: true,
  statusLine: {
    text: "Text recognition didn't work this time, so this is a plainer reading",
    tone: "quiet",
    action: { kind: "text_recognition", label: "Read it again" },
    details: null
  }
};

const CONFIRMATION = {
  sourceId: "src_axler",
  extractionId: "ext_old",
  pageSelection: Array.from({ length: 26 }, (_, index) => index + 13),
  pages: 26,
  estimatedUsd: 0.00468,
  engine: "glm_ocr" as const,
  needsConfirmation: true,
  title: "Read “Linear Algebra Done Right” again with text recognition?",
  lines: [
    "Pages 14–39 (26 pages), as before.",
    "z.ai (GLM-OCR) reads it: less than $0.01.",
    "Your progress (11 sections), 4 notes and the passages your questions and notes cite move to the new reading. Anything that can't be matched is marked so you can place it again."
  ],
  confirmLabel: "Read it again",
  cancelLabel: "Not now"
};

function place(card: SourceLibraryCard = CARD) {
  api.getSourceLibrary.mockResolvedValue({ version: 1, sources: [card], pending: [] });
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

it("asks before reading a studied book again, naming pages, cost and what moves; OK reads it", async () => {
  api.sourceAction
    .mockResolvedValueOnce({ version: 1, sourceId: "src_axler", action: "text_recognition", needsConfirmation: true, confirmation: CONFIRMATION })
    .mockResolvedValueOnce({ version: 1, sourceId: "src_axler", action: "text_recognition", batchId: "batch_1" });
  place();
  fireEvent.click(await screen.findByRole("button", { name: "Read it again" }));
  const dialog = await screen.findByRole("alertdialog", { name: CONFIRMATION.title });
  for (const line of CONFIRMATION.lines) expect(within(dialog).getByText(line)).toBeTruthy();
  expect(api.sourceAction).toHaveBeenCalledTimes(1);
  expect(api.sourceAction).toHaveBeenLastCalledWith({ sourceId: "src_axler", action: "text_recognition" });

  await act(async () => {
    fireEvent.click(within(dialog).getByRole("button", { name: "Read it again" }));
  });
  await waitFor(() => expect(api.sourceAction).toHaveBeenCalledTimes(2));
  expect(api.sourceAction).toHaveBeenLastCalledWith({ sourceId: "src_axler", action: "text_recognition", confirmed: true });
  expect(screen.queryByRole("alertdialog")).toBeNull();
});

it("Not now reads nothing", async () => {
  api.sourceAction.mockResolvedValueOnce({ version: 1, sourceId: "src_axler", action: "text_recognition", needsConfirmation: true, confirmation: CONFIRMATION });
  place();
  fireEvent.click(await screen.findByRole("button", { name: "Read it again" }));
  const dialog = await screen.findByRole("alertdialog");
  fireEvent.click(within(dialog).getByRole("button", { name: "Not now" }));
  expect(screen.queryByRole("alertdialog")).toBeNull();
  expect(api.sourceAction).toHaveBeenCalledTimes(1);
});

it("a book whose file changed after it was read is repaired with one tap", async () => {
  api.sourceAction.mockResolvedValue({ version: 1, sourceId: "src_axler", action: "restore_reading", restoredRevisionId: "rev_1" });
  place({
    ...CARD,
    statusLine: {
      text: "This book's file changed after it was read",
      tone: "problem",
      action: { kind: "restore_reading", label: "Open the reading you had" },
      details: null
    }
  });
  fireEvent.click(await screen.findByRole("button", { name: "Open the reading you had" }));
  await waitFor(() => expect(api.sourceAction).toHaveBeenCalledWith({ sourceId: "src_axler", action: "restore_reading" }));
});

it("protection redesign: a held-back reading says why and is marked by the owner after naming what is held out", async () => {
  const MARK = {
    sourceId: "src_axler",
    extractionId: "ext_new",
    revisionId: "rev_1",
    heldOutUnitIds: ["h3"],
    proposalHash: "sha256:shown",
    needsConfirmation: true,
    title: "Mark exam material on this reading of “Linear Algebra Done Right”?",
    lines: [
      "Held out as exam material: 3 Exam review.",
      "These are suggested from what you marked in the other reading: check them. The rest of this reading becomes available for explanations, questions and search."
    ],
    confirmLabel: "Mark them",
    cancelLabel: "Not now"
  };
  api.sourceAction
    .mockResolvedValueOnce({ version: 1, sourceId: "src_axler", action: "mark_exam_material", needsConfirmation: true, confirmation: MARK })
    .mockResolvedValueOnce({
      version: 1,
      sourceId: "src_axler",
      action: "mark_exam_material",
      marked: { extractionId: "ext_new", heldOutUnitIds: ["h3"], fromExtractionIds: ["ext_old"] }
    });
  place({
    ...CARD,
    statusLine: {
      text: "This reading is held back until you mark its exam material",
      tone: "problem",
      action: { kind: "mark_exam_material", label: "Mark exam material on this reading" },
      details: null
    }
  });
  expect(await screen.findByText("This reading is held back until you mark its exam material")).toBeTruthy();
  fireEvent.click(await screen.findByRole("button", { name: "Mark exam material on this reading" }));
  const dialog = await screen.findByRole("alertdialog", { name: MARK.title });
  for (const line of MARK.lines) expect(within(dialog).getByText(line)).toBeTruthy();
  expect(api.sourceAction).toHaveBeenLastCalledWith({ sourceId: "src_axler", action: "mark_exam_material" });

  await act(async () => {
    fireEvent.click(within(dialog).getByRole("button", { name: "Mark them" }));
  });
  await waitFor(() => expect(api.sourceAction).toHaveBeenCalledTimes(2));
  // Bound to the reading and the proposal it showed (exam protection by extraction identity, F13).
  expect(api.sourceAction).toHaveBeenLastCalledWith({
    sourceId: "src_axler",
    action: "mark_exam_material",
    confirmed: true,
    confirmedExtractionId: "ext_new",
    confirmedProposalHash: "sha256:shown"
  });
  expect(screen.queryByRole("alertdialog")).toBeNull();
});

it("extraction identity: a marking confirmed after its reading changed asks again, and the fresh one is what is sent", async () => {
  const SHOWN = {
    sourceId: "src_axler",
    extractionId: "ext_b",
    revisionId: "rev_1",
    heldOutUnitIds: ["u2"],
    proposalHash: "sha256:b",
    needsConfirmation: true,
    title: "Mark exam material on this reading of “Linear Algebra Done Right”?",
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
  api.sourceAction
    .mockResolvedValueOnce({ version: 1, sourceId: "src_axler", action: "mark_exam_material", needsConfirmation: true, confirmation: SHOWN })
    .mockResolvedValueOnce({ version: 1, sourceId: "src_axler", action: "mark_exam_material", needsConfirmation: true, confirmation: FRESH })
    .mockResolvedValueOnce({
      version: 1,
      sourceId: "src_axler",
      action: "mark_exam_material",
      marked: { extractionId: "ext_c", heldOutUnitIds: [], fromExtractionIds: [] }
    });
  place({
    ...CARD,
    statusLine: {
      text: "This reading is held back until you mark its exam material",
      tone: "problem",
      action: { kind: "mark_exam_material", label: "Mark exam material on this reading" },
      details: null
    }
  });
  fireEvent.click(await screen.findByRole("button", { name: "Mark exam material on this reading" }));
  const first = await screen.findByRole("alertdialog", { name: SHOWN.title });
  await act(async () => {
    fireEvent.click(within(first).getByRole("button", { name: "Mark them" }));
  });
  const again = await screen.findByRole("alertdialog", { name: FRESH.title });
  for (const line of FRESH.lines) expect(within(again).getByText(line)).toBeTruthy();
  await act(async () => {
    fireEvent.click(within(again).getByRole("button", { name: "Mark it" }));
  });
  await waitFor(() => expect(api.sourceAction).toHaveBeenCalledTimes(3));
  expect(api.sourceAction).toHaveBeenLastCalledWith({
    sourceId: "src_axler",
    action: "mark_exam_material",
    confirmed: true,
    confirmedExtractionId: "ext_c",
    confirmedProposalHash: "sha256:c"
  });
});

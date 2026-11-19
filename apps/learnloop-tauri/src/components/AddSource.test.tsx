// One Add, zero decisions (docs/specs/ux_learnloop_v1.md §6.2, §8.2).
import { act, cleanup, fireEvent, render, renderHook, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { AddSourceResultDto } from "../api/dto";
import { findJargon } from "../copy/denyList";
import { AddSourceBox, addedItemDestination, pastExamKeptLine, useAddSource } from "./AddSource";

const { api, openDialog } = vi.hoisted(() => ({
  api: { addSource: vi.fn() },
  openDialog: vi.fn()
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/plugin-dialog", () => ({ open: openDialog }));
vi.mock("@tauri-apps/api/webview", () => ({ getCurrentWebview: () => ({ onDragDropEvent: () => Promise.resolve(() => {}) }) }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const PDF_ITEM = {
  source: "/books/probability.pdf",
  kind: "pdf",
  kindNoun: "book",
  status: "added" as const,
  sourceId: "src_1",
  revisionId: "rev_1",
  title: "Probability",
  batchId: "batch_1",
  preparing: true,
  message: null
};

describe("AddSourceBox", () => {
  it("adds a pasted link with Enter and nothing else to fill in", () => {
    const onAdd = vi.fn();
    render(<AddSourceBox onAdd={onAdd} size="hero" />);
    expect(screen.getByText("Drop a book, paper or lecture here")).toBeTruthy();
    const input = screen.getByLabelText("Paste a link");
    fireEvent.change(input, { target: { value: "  https://arxiv.org/abs/1706.03762 " } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onAdd).toHaveBeenCalledWith(["https://arxiv.org/abs/1706.03762"], {});
  });

  it("chooses one or several files", async () => {
    openDialog.mockResolvedValue(["/books/a.pdf", "/books/b.pdf"]);
    const onAdd = vi.fn();
    render(<AddSourceBox onAdd={onAdd} />);
    fireEvent.click(screen.getByRole("button", { name: "Choose a file…" }));
    await waitFor(() => expect(onAdd).toHaveBeenCalledWith(["/books/a.pdf", "/books/b.pdf"], {}));
    expect(openDialog).toHaveBeenCalledWith(expect.objectContaining({ multiple: true }));
  });

  it("keeps every choice under More options", () => {
    const onAdd = vi.fn();
    render(<AddSourceBox onAdd={onAdd} />);
    expect(screen.queryByLabelText("Only some pages")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "More options ▸" }));
    fireEvent.change(screen.getByLabelText("Only some pages"), { target: { value: "3-27" } });
    fireEvent.click(screen.getByLabelText("This is a past exam or problem set (no reading questions)"));
    // The per-book AI opt-out is retired (owner, 2026-10-13).
    expect(screen.queryByLabelText(/never send|on this computer/i)).toBeNull();
    fireEvent.click(screen.getByLabelText("Read with text recognition"));
    const input = screen.getByLabelText("Paste a link");
    fireEvent.change(input, { target: { value: "/books/exam.pdf" } });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    expect(onAdd).toHaveBeenCalledWith(["/books/exam.pdf"], {
      pages: "3-27",
      problemSet: true,
      textRecognition: true
    });
  });

  it("shows the plain line it is given", () => {
    render(<AddSourceBox onAdd={vi.fn()} message="Already in your library — opened where you left off." />);
    expect(screen.getByRole("status").textContent).toContain("Already in your library");
  });
});

describe("useAddSource", () => {
  it("opens the first added book and reports nothing else", async () => {
    const result: AddSourceResultDto = { items: [PDF_ITEM], opened: PDF_ITEM };
    api.addSource.mockResolvedValue(result);
    const onOpened = vi.fn();
    const onError = vi.fn();
    const { result: hook } = renderHook(() => useAddSource({ onOpened, onError }));
    await act(async () => {
      await hook.current.add(["/books/probability.pdf"]);
    });
    expect(api.addSource).toHaveBeenCalledWith({ sources: ["/books/probability.pdf"] });
    expect(onOpened).toHaveBeenCalledWith(PDF_ITEM, result);
    expect(hook.current.message).toBeNull();
    expect(onError).not.toHaveBeenCalled();
  });

  it("says why an input could not be added, in one line", async () => {
    const unsupported = {
      ...PDF_ITEM,
      source: "just words",
      kind: null,
      kindNoun: null,
      status: "unsupported" as const,
      sourceId: null,
      revisionId: null,
      batchId: null,
      preparing: false,
      message: "LearnLoop can't open this yet — it reads PDFs, web pages, arXiv, YouTube, Markdown, text and subtitles."
    };
    api.addSource.mockResolvedValue({ items: [unsupported], opened: null });
    const onOpened = vi.fn();
    const { result: hook } = renderHook(() => useAddSource({ onOpened, onError: vi.fn() }));
    await act(async () => {
      await hook.current.add(["just words"]);
    });
    expect(onOpened).not.toHaveBeenCalled();
    expect(hook.current.message).toBe(unsupported.message);
  });

  it("turns a refused request into a plain line", async () => {
    api.addSource.mockRejectedValue({ code: "invalid_page_range", message: "Range 9-3 runs backwards.", retryable: false });
    const onError = vi.fn();
    const { result: hook } = renderHook(() => useAddSource({ onOpened: vi.fn(), onError }));
    await act(async () => {
      await hook.current.add(["/books/a.pdf"], { pages: "9-3" });
    });
    expect(hook.current.message).toBe("Those pages don't look right — try a page or a range like 3-27. (Range 9-3 runs backwards.)");
    expect(onError).not.toHaveBeenCalled();
  });
});

// UX journey audit UX-5 (student-1 #33-39): "This is a past exam or problem
// set" was then opened in the Reader, whose refusal showed as a red error
// naming the source's id.
describe("UX-5: a past exam or problem set is kept in the Library, never opened in the Reader", () => {
  const EXAM = { ...PDF_ITEM, source: "/exams/quiz1.pdf", sourceId: "src_exam", title: "18.06 Linear Algebra, Exam 1" };

  it("the hook does not open it, and hands it over as kept", async () => {
    api.addSource.mockResolvedValue({ items: [EXAM], opened: EXAM });
    const onOpened = vi.fn();
    const onKept = vi.fn();
    const { result: hook } = renderHook(() => useAddSource({ onOpened, onKept }));
    await act(async () => {
      await hook.current.add(["/exams/quiz1.pdf"], { problemSet: true });
    });
    expect(api.addSource).toHaveBeenCalledWith({ sources: ["/exams/quiz1.pdf"], problemSet: true });
    expect(onOpened).not.toHaveBeenCalled();
    expect(onKept).toHaveBeenCalledWith(EXAM);
  });

  it("an added item whose library card has the reader off is kept too; the rest open as before", () => {
    expect(addedItemDestination(EXAM, { readerEnabled: false })).toBe("kept");
    expect(addedItemDestination(EXAM, { readerEnabled: true })).toBe("reader");
    expect(addedItemDestination(EXAM, undefined)).toBe("reader");
    expect(addedItemDestination({ ...EXAM, status: "queued", sourceId: null }, undefined)).toBe("wait");
  });

  it("says where it went and what it does, with no id and no jargon", () => {
    const line = pastExamKeptLine(EXAM.title);
    expect(line).toBe("\u201c18.06 Linear Algebra, Exam 1\u201d is in your Library as a past exam. It doesn't open in the Reader, and LearnLoop doesn't write questions from it.");
    expect(findJargon(line)).toEqual([]);
  });
});

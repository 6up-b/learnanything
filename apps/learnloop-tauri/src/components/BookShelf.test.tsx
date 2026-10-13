// The Library shelf and its book cards (docs/specs/ux_learnloop_v1.md §6.1 W1, §7.2 W3).
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { AiConnectionDto, SourceLibraryCard, SourceStatusLineDto } from "../api/dto";
import { BookCard, PendingCard } from "./BookCard";
import { BookShelf } from "./BookShelf";

vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn() }));
vi.mock("@tauri-apps/api/webview", () => ({ getCurrentWebview: () => ({ onDragDropEvent: () => Promise.resolve(() => {}) }) }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function card(statusLine: SourceStatusLineDto | null, overrides: Partial<SourceLibraryCard> = {}): SourceLibraryCard {
  return {
    sourceId: "src_1",
    title: "Probability",
    acquisitionKind: "pdf",
    canonicalUri: "/books/probability.pdf",
    workId: null,
    currentRevisionId: "rev_1",
    revisionCount: 1,
    readiness: "ready",
    unitCount: 12,
    blockCount: 400,
    extractionStatus: "completed",
    suggestedRole: null,
    readerEnabled: true,
    updateAvailable: false,
    kindNoun: "book",
    subjectId: "probability",
    statusLine,
    ...overrides
  };
}

const NEEDS_AI: AiConnectionDto = {
  canAuthor: false,
  provider: "codex_medium",
  providerLabel: "ChatGPT",
  consentKey: "codex",
  consented: false,
  consentedAt: null,
  needs: "connect",
  message: null,
  whatLeaves: "LearnLoop sends passages of the books you add, and your answers, to ChatGPT to write questions and give feedback.",
  chatgptSignedIn: false,
  openrouterKeyPresent: false
};

describe("BookCard", () => {
  it("shows one quiet line and runs its one action", () => {
    const onAction = vi.fn();
    const onContinue = vi.fn();
    const line: SourceStatusLineDto = { text: "Questions ready for Ch. 1–2", tone: "quiet", action: { kind: "undo_questions", label: "Undo" }, details: null };
    render(<BookCard card={card(line)} onContinue={onContinue} onAction={onAction} />);
    expect(screen.getByText("Probability")).toBeTruthy();
    expect(screen.getByText("Questions ready for Ch. 1–2")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Undo" }));
    expect(onAction).toHaveBeenCalledWith("undo_questions", expect.objectContaining({ sourceId: "src_1" }));
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(onContinue).toHaveBeenCalledWith(expect.objectContaining({ sourceId: "src_1" }));
  });

  // Usability round 1: details showed "Subject: introduction-to-probability".
  it("names the book's subject by its title in details", () => {
    const line: SourceStatusLineDto = { text: "Questions for Ch. 1–2 come up as you read", tone: "quiet", action: null, details: null };
    render(<BookCard card={card(line, { subjectId: "introduction-to-probability", subjectTitle: "Introduction to Probability" })} onContinue={vi.fn()} onAction={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "details ▸" }));
    expect(screen.getByText("Subject: Introduction to Probability")).toBeTruthy();
    expect(screen.queryByText(/introduction-to-probability/)).toBeNull();
    // Undo stays one tap away, in details.
    expect(screen.getByRole("button", { name: "Undo this book's questions" })).toBeTruthy();
  });

  it("can be opened while it is still being prepared", () => {
    const onContinue = vi.fn();
    const line: SourceStatusLineDto = { text: "Getting this book ready", tone: "working", action: null, details: null };
    render(<BookCard card={card(line, { readiness: "processing" })} onContinue={onContinue} onAction={vi.fn()} />);
    expect(screen.getByText(/Getting this book ready/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    expect(onContinue).toHaveBeenCalled();
  });

  it("keeps the receipts and choices behind details", () => {
    const onAction = vi.fn();
    const onOpenImports = vi.fn();
    const line: SourceStatusLineDto = {
      text: "Couldn't reach the page",
      tone: "problem",
      action: { kind: "retry", label: "Try again" },
      details: "HTTP 503 from example.org"
    };
    render(<BookCard card={card(line)} onContinue={vi.fn()} onAction={onAction} onOpenImports={onOpenImports} />);
    expect(screen.queryByText("HTTP 503 from example.org")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "details ▸" }));
    expect(screen.getByText("HTTP 503 from example.org")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Undo this book's questions" }));
    expect(onAction).toHaveBeenCalledWith("undo_questions", expect.anything());
    fireEvent.click(screen.getByRole("button", { name: "Build questions for the whole book" }));
    expect(onAction).toHaveBeenCalledWith("build_whole_book", expect.anything());
    fireEvent.click(screen.getByRole("button", { name: "Open in Imports & builds" }));
    expect(onOpenImports).toHaveBeenCalled();
  });

  it("keeps a book on this computer from its details, and lets it go again (review F1)", () => {
    const onAction = vi.fn();
    const { unmount } = render(<BookCard card={card(null)} onContinue={vi.fn()} onAction={onAction} />);
    fireEvent.click(screen.getByRole("button", { name: "details ▸" }));
    fireEvent.click(screen.getByRole("button", { name: "Keep this book on this computer" }));
    expect(onAction).toHaveBeenCalledWith("keep_local", expect.objectContaining({ sourceId: "src_1" }));
    unmount();
    render(<BookCard card={card(null, { keepLocal: true })} onContinue={vi.fn()} onAction={onAction} />);
    fireEvent.click(screen.getByRole("button", { name: "details ▸" }));
    expect(screen.getByText("Kept on this computer: nothing of it is sent to an AI.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Let LearnLoop write questions for it" }));
    expect(onAction).toHaveBeenCalledWith("share_with_ai", expect.anything());
  });

  it("never shows a file address as the title", () => {
    render(<BookCard card={card(null, { title: "file:///home/me/books/linear_algebra.pdf" })} onContinue={vi.fn()} onAction={vi.fn()} />);
    expect(screen.queryByText(/file:\/\//)).toBeNull();
    expect(screen.getByText("Linear Algebra")).toBeTruthy();
  });
});

describe("PendingCard", () => {
  it("lets a link that could not be fetched be tried again or removed", () => {
    const onRetry = vi.fn();
    const onRemove = vi.fn();
    const entry = {
      batchId: "b1",
      source: "https://example.org/notes",
      kind: "web",
      kindNoun: "article",
      title: "https://example.org/notes",
      statusLine: { text: "Couldn't reach the page", tone: "problem" as const, action: { kind: "retry" as const, label: "Try again" }, details: "HTTP 503" }
    };
    render(<PendingCard entry={entry} onRetry={onRetry} onRemove={onRemove} />);
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(onRetry).toHaveBeenCalledWith(entry);
    fireEvent.click(screen.getByRole("button", { name: "Remove" }));
    expect(onRemove).toHaveBeenCalledWith(entry);
  });

  it("offers no removal while the link is still being fetched", () => {
    const entry = {
      batchId: "b1",
      source: "https://example.org/notes",
      kind: "web",
      kindNoun: "article",
      title: "https://example.org/notes",
      statusLine: { text: "Getting this article ready", tone: "working" as const, action: null, details: null }
    };
    render(<PendingCard entry={entry} onRetry={vi.fn()} onRemove={vi.fn()} />);
    expect(screen.queryByRole("button", { name: "Remove" })).toBeNull();
  });
});

describe("BookShelf", () => {
  it("welcomes an empty library with one place to drop a book", () => {
    const onConnectAi = vi.fn();
    render(
      <BookShelf sources={[]} pending={[]} aiConnection={NEEDS_AI} onOpen={vi.fn()} onAction={vi.fn()} onConnectAi={onConnectAi} onAdd={vi.fn()} />
    );
    expect(screen.getByText("Drop a book, paper or lecture here")).toBeTruthy();
    expect(screen.getByText(/LearnLoop opens it right away/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Continue with ChatGPT · other…" }));
    expect(onConnectAi).toHaveBeenCalled();
  });

  it("shows the AI line only when nothing can write questions", () => {
    render(
      <BookShelf
        sources={[]}
        pending={[]}
        aiConnection={{ ...NEEDS_AI, canAuthor: true, needs: null }}
        onOpen={vi.fn()}
        onAction={vi.fn()}
        onConnectAi={vi.fn()}
        onAdd={vi.fn()}
      />
    );
    expect(screen.queryByText(/Connect an AI to get questions/)).toBeNull();
  });

  it("lists books and links still being fetched, with Add at the foot", () => {
    const onOpen = vi.fn();
    render(
      <BookShelf
        sources={[card(null), card(null, { sourceId: "src_2", title: "Attention Is All You Need", kindNoun: "paper" })]}
        pending={[{
          batchId: "b1",
          source: "https://example.org/notes",
          kind: "web",
          kindNoun: "article",
          title: "https://example.org/notes",
          statusLine: { text: "Getting this article ready", tone: "working", action: null, details: null }
        }]}
        aiConnection={null}
        onOpen={onOpen}
        onAction={vi.fn()}
        onConnectAi={vi.fn()}
        onAdd={vi.fn()}
      />
    );
    const shelf = screen.getByRole("list", { name: "Your books" });
    expect(within(shelf).getAllByRole("listitem")).toHaveLength(3);
    expect(screen.getByText(/Getting this article ready/)).toBeTruthy();
    expect(screen.getByText(/Drop more books here/)).toBeTruthy();
    fireEvent.click(within(shelf).getAllByRole("button", { name: "Continue" })[1]);
    expect(onOpen).toHaveBeenCalledWith(expect.objectContaining({ sourceId: "src_2" }));
  });
});

// UX Phase 1 usability round 2 (docs/reviews/ux-phase1.md, "Usability round 2 fixes").
describe("round 2", () => {
  const done: SourceStatusLineDto = {
    text: "Questions for Ch. 1–2 come up as you read",
    tone: "quiet",
    action: null,
    details: null,
    withoutAi: {
      text: "Questions for Ch. 1–2 come up as you read once an AI is connected",
      tone: "quiet",
      action: { kind: "connect_ai", label: "Connect" },
      details: null
    }
  };

  it("offers text recognition only on a book where it can run", () => {
    const { unmount } = render(<BookCard card={card(null, { textRecognitionAvailable: false })} onContinue={vi.fn()} onAction={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "details ▸" }));
    expect(screen.queryByRole("button", { name: "Read it again with text recognition" })).toBeNull();
    unmount();

    const onAction = vi.fn();
    render(<BookCard card={card(null, { textRecognitionAvailable: true })} onContinue={vi.fn()} onAction={onAction} />);
    fireEvent.click(screen.getByRole("button", { name: "details ▸" }));
    fireEvent.click(screen.getByRole("button", { name: "Read it again with text recognition" }));
    expect(onAction).toHaveBeenCalledWith("text_recognition", expect.anything());
  });

  it("says what questions need when no AI is connected, instead of promising them", () => {
    render(
      <BookShelf sources={[card(done)]} pending={[]} aiConnection={NEEDS_AI} onOpen={vi.fn()} onAction={vi.fn()} onConnectAi={vi.fn()} onAdd={vi.fn()} />
    );
    expect(screen.queryByText("Questions for Ch. 1–2 come up as you read")).toBeNull();
    expect(screen.getByText("Questions for Ch. 1–2 come up as you read once an AI is connected")).toBeTruthy();
  });

  it("keeps the as-you-read line when an AI can write questions", () => {
    render(
      <BookShelf
        sources={[card(done)]}
        pending={[]}
        aiConnection={{ ...NEEDS_AI, canAuthor: true, needs: null }}
        onOpen={vi.fn()}
        onAction={vi.fn()}
        onConnectAi={vi.fn()}
        onAdd={vi.fn()}
      />
    );
    expect(screen.getByText("Questions for Ch. 1–2 come up as you read")).toBeTruthy();
  });
});

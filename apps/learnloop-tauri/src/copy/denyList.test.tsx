// Plain words, enforced (docs/specs/ux_learnloop_v1.md §9, Phase 7.2 started
// in Phase 1): every learner surface Phase 1 adds is rendered with fixture
// data and must not show a term from the glossary's left column.
import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { AiConnectionDto, SourceLibraryCard, SourceStatusLineDto } from "../api/dto";
import { AddSourceBox } from "../components/AddSource";
import { BookCard } from "../components/BookCard";
import { BookShelf } from "../components/BookShelf";
import { ConnectAISheet } from "../components/ConnectAI";
import { PreparingView } from "../screens/reader/PreparingView";
import { DENY_TERMS, findJargon } from "./denyList";

const { api } = vi.hoisted(() => ({
  api: {
    getAiConnection: vi.fn(),
    connectAi: vi.fn(),
    getSourceLibrary: vi.fn(),
    readerPdfView: vi.fn(),
    chatgptPlanSigninStart: vi.fn(),
    chatgptPlanStatus: vi.fn(),
    setOpenrouterApiKey: vi.fn()
  }
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/core", () => ({ convertFileSrc: (path: string) => path, invoke: vi.fn() }));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

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

// Backend sentences the shelf, the Add box and the Reader show as they are
// (usability round 2), and the fixed strings this round adds to Today and the
// Reader. Their surfaces have their own tests; here they meet the deny-list.
const HOW_TO = "To add it, run uv sync --extra pdf in LearnLoop's folder, then restart LearnLoop.";
const SCAN_DETAILS =
  "Reading the words of a scan needs text recognition, which isn't installed on this computer. " +
  HOW_TO +
  " The pages still show in the Reader meanwhile.";
const ROUND2_SENTENCES = [
  "Text recognition isn't installed on this computer, so LearnLoop can't read the words of a scan yet. " + HOW_TO,
  "Text recognition isn't installed on this computer, so this was added without it. " + HOW_TO,
  "You answered this section's quick check: compare below, then keep reading.",
  "quick check",
  "◐ Opening Introduction to Probability…",
  "answer directly",
  "help me reason",
  "ask me first",
  "Begin today's plan on Start first.",
  "Pick a book to read, or search them all."
];

// Every line the sidecar can put on a card (learnloop.content.pipeline.add_source).
const LINES: SourceStatusLineDto[] = [
  { text: "Getting this book ready", tone: "working", action: null, details: null },
  { text: "Questions for Ch. 1–2 in about 5 min", tone: "working", action: null, details: null },
  { text: "Questions for Ch. 1–2 come up as you read", tone: "quiet", action: null, details: null },
  { text: "Questions need an AI connection", tone: "quiet", action: { kind: "connect_ai", label: "Connect" }, details: null },
  { text: "Questions wait for your OK", tone: "quiet", action: { kind: "connect_ai", label: "Review" }, details: null },
  { text: "Building questions for Ch. 1–2 would cost about $3.10", tone: "quiet", action: { kind: "build_now", label: "Build them" }, details: null },
  { text: "Questions for Ch. 3 need another try", tone: "problem", action: { kind: "retry", label: "Retry" }, details: null },
  { text: "Questions for Ch. 1–2 need a look", tone: "quiet", action: { kind: "open_changes", label: "Review" }, details: null },
  { text: "2 changes need a look", tone: "quiet", action: { kind: "open_changes", label: "Review" }, details: null },
  { text: "Questions for this book were taken back out", tone: "quiet", action: { kind: "build_now", label: "Build them again" }, details: null },
  { text: "Couldn't reach the page", tone: "problem", action: { kind: "retry", label: "Try again" }, details: null },
  { text: "This video has no captions", tone: "problem", action: { kind: "retry", label: "Try again" }, details: null },
  { text: "Couldn't read this PDF", tone: "problem", action: { kind: "retry", label: "Try again" }, details: null },
  { text: "Some pages look scanned", tone: "quiet", action: { kind: "text_recognition", label: "Read them with text recognition" }, details: null },
  { text: "Maths may look rough in the text view", tone: "quiet", action: { kind: "open_settings", label: "Fix it" }, details: null },
  { text: "Kept on this computer — no questions are written for it", tone: "quiet", action: null, details: null },
  // UX Phase 1 review (F1, F2, F9): the separate OK for whole files, the
  // budget lines and text recognition that isn't set up.
  { text: "Transcribing this recording sends it to an online service", tone: "quiet", action: { kind: "allow_upload", label: "OK" }, details: null },
  { text: "Reading this PDF sends the whole file to your AI", tone: "quiet", action: { kind: "allow_upload", label: "OK" }, details: null },
  { text: "Kept on this computer — this recording can't be read here", tone: "quiet", action: null, details: null },
  { text: "Paused — today's AI budget is used", tone: "quiet", action: { kind: "open_settings", label: "Raise it" }, details: null },
  { text: "Questions for Ch. 3 would cost more than expected", tone: "quiet", action: { kind: "build_now", label: "Build them" }, details: null },
  // Usability round 1 (U7): a scan, with and without text recognition installed.
  { text: "This PDF is a scan", tone: "quiet", action: { kind: "text_recognition", label: "Read it with text recognition" }, details: null },
  { text: "This PDF is a scan — LearnLoop can show its pages but can't read them yet", tone: "quiet", action: null, details: SCAN_DETAILS },
  { text: "Some pages look scanned — their words can't be read here yet", tone: "quiet", action: null, details: SCAN_DETAILS },
  { text: "Text recognition isn't set up", tone: "problem", action: { kind: "open_settings", label: "Set it up" }, details: null },
  // Usability round 2: no invented build time, a book with no questions yet,
  // a paper, and what a built book says while no AI is connected.
  { text: "Writing questions for Ch. 1–2", tone: "working", action: null, details: null },
  { text: "Questions for Ch. 1–2 in under a minute", tone: "working", action: null, details: null },
  { text: "Questions for this paper in about 2 min", tone: "working", action: null, details: null },
  { text: "No questions for this book yet", tone: "quiet", action: { kind: "retry", label: "Build them" }, details: null },
  { text: "Questions for Ch. 1–2 come up as you read once an AI is connected", tone: "quiet", action: { kind: "connect_ai", label: "Connect" }, details: null },
  { text: "Questions wait for your OK", tone: "quiet", action: { kind: "connect_ai", label: "Review" }, details: "Codex (your ChatGPT account)" }
];



const CONNECTION: AiConnectionDto = {
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

function expectPlain(text: string) {
  expect(findJargon(text)).toEqual([]);
}

describe("the deny-list", () => {
  it("catches the glossary's internal terms and lets plain words through", () => {
    expect(findJargon("Your vault has 3 facets in the study map")).toEqual(["vault", "facet", "study map"]);
    expect(findJargon("Extraction failed: synthesis proposal pending")).toEqual(["extraction", "synthesis", "proposal"]);
    expect(findJargon("Questions ready for Ch. 1–2 · Undo")).toEqual([]);
    expect(DENY_TERMS.length).toBeGreaterThan(30);
  });

  it("allows a term only through a named exemption", () => {
    expect(findJargon("Open in Imports & builds (was Ingest)", { ingest: "the old screen's name, for the owner" })).toEqual([]);
  });
});

describe("Phase 1 learner surfaces use plain words", () => {
  it("the Add box", () => {
    const { container } = render(<AddSourceBox onAdd={vi.fn()} size="hero" />);
    expectPlain(container.textContent ?? "");
  });

  it.each(LINES.map((line) => [line.text, line] as const))("a book card saying %s", (_text, line) => {
    const { container, getByRole } = render(
      <BookCard card={card(line, { textRecognitionAvailable: true })} onContinue={vi.fn()} onAction={vi.fn()} />
    );
    expectPlain(container.textContent ?? "");
    // Details too: what is on demand is plain as well (usability round 2).
    // The one OK's details name the AI it is for, as Settings does.
    fireEvent.click(getByRole("button", { name: "details ▸" }));
    const exemptions: Record<string, string> = line.details?.startsWith("Codex") ? { codex: "names the AI this OK is for, as Settings does" } : {};
    expect(findJargon(container.textContent ?? "", exemptions)).toEqual([]);
  });

  it.each(ROUND2_SENTENCES)("the sentence: %s", (sentence) => {
    expectPlain(sentence);
  });

  it("the empty shelf and a full one", () => {
    const empty = render(
      <BookShelf sources={[]} pending={[]} aiConnection={CONNECTION} onOpen={vi.fn()} onAction={vi.fn()} onConnectAi={vi.fn()} onAdd={vi.fn()} />
    );
    expectPlain(empty.container.textContent ?? "");
    empty.unmount();
    const full = render(
      <BookShelf
        sources={LINES.map((line, index) => card(line, { sourceId: `src_${index}` }))}
        pending={[{ batchId: "b1", source: "https://example.org/notes", kind: "web", kindNoun: "article", title: "https://example.org/notes", statusLine: LINES[0] }]}
        aiConnection={{ ...CONNECTION, canAuthor: true, needs: null }}
        onOpen={vi.fn()}
        onAction={vi.fn()}
        onConnectAi={vi.fn()}
        onAdd={vi.fn()}
      />
    );
    expectPlain(full.container.textContent ?? "");
  });

  it.each([
    ["connect", CONNECTION],
    ["consent", { ...CONNECTION, canAuthor: true, needs: "consent" as const }],
    ["connected", { ...CONNECTION, canAuthor: true, needs: null, consented: true }]
  ])("the connect sheet (%s)", async (_state, connection) => {
    api.getAiConnection.mockResolvedValue(connection);
    const { container, findByText } = render(<ConnectAISheet onClose={vi.fn()} onConnected={vi.fn()} onOpenSettings={vi.fn()} />);
    await findByText("Get questions on what you read");
    expectPlain(container.textContent ?? "");
  });

  // Usability round 2: a library set up with Codex names it on its one OK, as
  // Settings does; nothing else on the sheet is internal.
  it("the connect sheet's one OK in a library set up with Codex", async () => {
    const label = "Codex (your ChatGPT account)";
    api.getAiConnection.mockResolvedValue({
      ...CONNECTION,
      canAuthor: true,
      needs: "consent",
      providerLabel: label,
      whatLeaves: `LearnLoop sends passages of the books you add, and your answers, to ${label} to write questions and give feedback.`
    });
    const { container, findByText } = render(<ConnectAISheet onClose={vi.fn()} onConnected={vi.fn()} onOpenSettings={vi.fn()} />);
    await findByText(`LearnLoop is set up to use ${label}.`);
    expect(findJargon(container.textContent ?? "", { codex: "names the AI this library is set up with, as Settings does" })).toEqual([]);
  });

  it("the Reader while a book is prepared", async () => {
    api.readerPdfView.mockResolvedValue({ available: true, preparing: true, fileName: "sha256-x", extractionId: null, sourceId: "src_1", revisionId: "rev_1", blocks: [] });
    api.getSourceLibrary.mockResolvedValue({ version: 1, sources: [] });
    const preparing = card({ text: "Getting this book ready", tone: "working", action: null, details: null }, { readiness: "processing" });
    const { container, findByText } = render(<PreparingView card={preparing} onBack={vi.fn()} onReady={vi.fn()} onError={vi.fn()} />);
    await findByText(/Getting this book ready/);
    expectPlain(container.textContent ?? "");
  });
});

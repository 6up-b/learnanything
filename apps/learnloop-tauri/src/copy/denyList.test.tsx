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
import { WAITING_COPY } from "./waiting";
import {
  CONSENT_ACTION,
  GOAL_NOT_UP_TODAY,
  KEEP_GOING_NOTHING_LEAD,
  PLAN_FINISHED,
  causeActionLabel,
  causeSecondActionLabel,
  causeSentence,
  causeTopicsFailed,
  causeWait,
  goalCauseSentence,
  type TodayCause
} from "../app/todayCause";
import { NOTE_NO_SUBJECT, NO_ASK_NOT_YET, NO_ASK_SHORT_CHECK, NO_ASK_TEACH_BACK, NO_HINTS_ON_YOUR_OWN, NO_HINTS_SHORT_CHECK, quickCheckNothingToAsk } from "./refusals";
import { LESSON_KEPT, PLAN_STOPPED_WITH_MORE, continueLessonLine } from "../app/todayCause";
import { emptyGoalSentence } from "../components/GoalBanner";
import { HELP_COPY } from "../screens/workbench/helpModel";
import { REVIEW_REASON_CODES, reviewReasonLine } from "../app/practiceFeedback";
import { citationWords, sectionWords } from "../screens/reader/readerShared";
import { sessionTopicLine } from "../components/SessionFinishHud";
import { INTENT_COPY } from "../screens/reader/intentPalette";
import type { CalibrationSessionProgressDto, GoalDto, QuickCheckResultDto } from "../api/dto";

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
  // UX-11: a web page read before its equations were kept (learnloop/content/pipeline/reread.py).
  {
    text: "This page's text is missing 31 equations", tone: "quiet", action: { kind: "read_again", label: "Read it again" },
    details: "This page was read before LearnLoop kept a web page's equations and section titles. Reading it again from the copy saved when you added it keeps them; your progress and notes move to the new reading."
  },
  { text: "Couldn't reach the page", tone: "problem", action: { kind: "retry", label: "Try again" }, details: null },
  { text: "This video has no captions", tone: "problem", action: { kind: "retry", label: "Try again" }, details: null },
  { text: "Couldn't read this PDF", tone: "problem", action: { kind: "retry", label: "Try again" }, details: null },
  { text: "Some pages look scanned", tone: "quiet", action: { kind: "text_recognition", label: "Read them with text recognition" }, details: null },
  { text: "Maths may look rough in the text view", tone: "quiet", action: { kind: "open_settings", label: "Fix it" }, details: null },
  { text: "Never sent to an AI — no questions are written for it", tone: "quiet", action: null, details: null },
  // UX Phase 1 review (F1, F2, F9): the separate OK for whole files, the
  // budget lines and text recognition that isn't set up.
  { text: "Transcribing this recording sends it to an online service", tone: "quiet", action: { kind: "allow_upload", label: "OK" }, details: null },
  { text: "Reading this PDF sends the whole file to your AI", tone: "quiet", action: { kind: "allow_upload", label: "OK" }, details: null },
  { text: "Never sent to an AI — this recording can't be read here", tone: "quiet", action: null, details: null },
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
  { text: "No questions for this book yet", tone: "quiet", action: { kind: "retry", label: "Build them as you read" }, details: null },
  { text: "Questions for Ch. 1–2 come up as you read once an AI is connected", tone: "quiet", action: { kind: "connect_ai", label: "Connect" }, details: null },
  { text: "Questions wait for your OK", tone: "quiet", action: { kind: "connect_ai", label: "Review" }, details: "Codex (your ChatGPT account)" },
  // Finishing pass (#6): a PDF is a PDF until its text says book or paper.
  { text: "Getting this PDF ready", tone: "working", action: null, details: null },
  { text: "Questions for this PDF come up as you read", tone: "quiet", action: null, details: null },
  // UX-43: a build that found no topic to practise (docs/reviews/ux43-empty-build.md).
  {
    text: "LearnLoop found no topics to practise in this article", tone: "problem", action: { kind: "retry", label: "Try again" },
    details: "LearnLoop read it but came back without a topic to write questions from. Try again asks once more; your reading and the sections you finished are kept, and they get their questions once topics are found.",
    noTopics: true
  },
  { text: "LearnLoop found no topics to practise in Ch. 2", tone: "problem", action: { kind: "retry", label: "Try again" }, details: null, noTopics: true }
];



const BOOK = { sourceId: "src_1", title: "Probability", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const STAGE3_CAUSES: TodayCause[] = [
  { kind: "list_has_more" },
  { kind: "waiting_ok", title: "Probability", others: 2 },
  { kind: "needs_ai", title: "Probability" },
  { kind: "failed", title: "Probability", target: { sourceId: "src_1" }, build: false, retried: false },
  { kind: "needs_look", title: "Probability" },
  { kind: "on_the_way", title: "Probability", card: null, progress: null, minutes: null },
  { kind: "no_reading" },
  // First questions arrive (docs/reviews/ux-first-questions-today.md): every state it adds or rewords.
  { kind: "failed", title: "Probability", target: { sourceId: "src_1" }, build: true, retried: true },
  { kind: "failed", title: "Probability", target: { sourceId: "src_1" }, build: true, retried: false },
  { kind: "on_the_way", title: "Probability", card: BOOK, progress: { done: 1, total: 2 }, minutes: 3.6 },
  { kind: "on_the_way", title: "Probability", card: BOOK, progress: null, minutes: 0.2 },
  { kind: "questions_ready", title: "Probability", part: "Conditional probability", count: 5, itemId: "pi_1", card: BOOK },
  { kind: "questions_ready", title: "Probability", part: null, count: 1, itemId: null, card: BOOK },
  { kind: "section_writing", title: "Probability", part: "Conditional probability", card: BOOK },
  { kind: "section_writing", title: "Probability", part: null, card: BOOK },
  { kind: "section_failed", title: "Probability", part: "Conditional probability", resumeId: "batch_1" },
  { kind: "section_failed", title: "Probability", part: null, resumeId: "batch_1" },
  { kind: "finish_section", card: BOOK },
  { kind: "finish_section", card: null },
  { kind: "none_up", title: "Probability", card: BOOK },
  // A section finished before its book is ready (docs/reviews/ux31-section-done-before-build.md).
  { kind: "on_the_way", title: "Probability", card: BOOK, progress: null, minutes: null, waiting: { part: "Conditional probability" } },
  { kind: "on_the_way", title: "Probability", card: BOOK, progress: null, minutes: null, waiting: { part: null } },
  { kind: "section_waiting", title: "Probability", part: "Conditional probability", card: BOOK },
  { kind: "section_waiting", title: "Probability", part: null, card: BOOK },
  // Question writing you can follow (docs/reviews/ux-first-questions-progress.md).
  { kind: "on_the_way", title: "Probability", card: BOOK, progress: { done: 0, total: 2 }, minutes: null, firstBuild: true },
  { kind: "section_writing", title: "Probability", part: "Conditional probability", card: BOOK, progress: { done: 2, total: 8 } },
  { kind: "section_writing", title: "Probability", part: null, card: BOOK, progress: { done: 0, total: 1 } },
  { kind: "questions_ready_with_section_work", title: "Probability", part: "Conditional probability", count: 3, itemId: "pi_1", card: BOOK,
    writing: { progress: { done: 2, total: 8 } }, failedTopics: false, resumeId: null },
  { kind: "questions_ready_with_section_work", title: "Probability", part: null, count: 1, itemId: null, card: BOOK,
    writing: { progress: null }, failedTopics: true, resumeId: null },
  { kind: "questions_ready_with_section_work", title: "Probability", part: "Conditional probability", count: 2, itemId: "pi_1", card: BOOK,
    writing: null, failedTopics: true, resumeId: "batch_1" },
  // A build that found no topic to practise (docs/reviews/ux43-empty-build.md).
  { kind: "no_topics", title: "Probability", card: BOOK, sourceId: "src_1" }
];
const STAGE3_SENTENCES = [
  ...STAGE3_CAUSES.flatMap((cause) => [causeSentence(cause), goalCauseSentence(cause), causeActionLabel(cause) ?? "", causeSecondActionLabel(cause) ?? "",
    causeWait(cause)?.line ?? "", causeWait(cause)?.after ?? "", causeWait(cause)?.later ?? "", causeTopicsFailed(cause) ?? ""]),
  GOAL_NOT_UP_TODAY,
  PLAN_FINISHED,
  KEEP_GOING_NOTHING_LEAD,
  CONSENT_ACTION,
  NO_HINTS_ON_YOUR_OWN,
  NO_HINTS_SHORT_CHECK,
  NO_ASK_SHORT_CHECK,
  NO_ASK_TEACH_BACK,
  NO_ASK_NOT_YET,
  NOTE_NO_SUBJECT,
  // UX-43: what "Build questions for the whole article at once" says on a book whose build found no topic (add_source.py).
  "LearnLoop found no topics to practise in this article, so there are no questions to write from it yet. Try again on its card to look once more."
].filter(Boolean);

// Broken controls, second round (docs/reviews/ux-fix-round-2a.md): every sentence this round adds.
function emptyGoal(concepts: string[], total: number, practicable: number | null): GoalDto {
  return {
    dueAt: "2026-12-09T18:00:00Z", facetScope: { concepts, facets: [] }, practicableItemCount: practicable,
    report: { onTrackCount: 0, total, onTrackFraction: null, atRiskCount: 0, horizon: "", dueAt: null, certifiedCount: 0, examinedCount: 0,
              pace: { attemptsPerDay: 0, attemptsLast14d: 0, daysLeft: null, attemptsRemaining: 0, neededPerDay: null, onPace: null, attemptsLogged: 0, paceKind: "activity" } }
  } as unknown as GoalDto;
}
function nothingAsked(verdicts: QuickCheckResultDto["verdict"][]): string {
  const results = verdicts.map((verdict, index) => ({ learningObjectId: `lo_${index}`, learningObjectTitle: `Topic ${index}`, verdict, assumptionId: null, answers: [] }));
  return quickCheckNothingToAsk({ status: "completed", quickCheck: { learningObjectIds: [], k: 4, answered: 0, remaining: 4, finished: true, results } } as unknown as CalibrationSessionProgressDto) ?? "";
}
const ROUND_2A_SENTENCES = [
  continueLessonLine("Dot product"),
  LESSON_KEPT,
  PLAN_STOPPED_WITH_MORE,
  emptyGoalSentence(emptyGoal(["a", "b", "c"], 0, 0)) ?? "",
  emptyGoalSentence(emptyGoal(["a"], 0, 0)) ?? "",
  emptyGoalSentence(emptyGoal([], 4, 0)) ?? "",
  nothingAsked(["undecided"]),
  nothingAsked(["undecided", "learning"]),
  nothingAsked(["already_assumed"]),
  nothingAsked(["already_assumed", "already_assumed"]),
  HELP_COPY.noFittingHint,
  "sent"
];

// Group B of the same round: every review reason's words a feedback can show, and a web page's
// section names as the Reader now says them.
const ROUND_2B_SENTENCES = [
  ...REVIEW_REASON_CODES.flatMap((code) => reviewReasonLine(code) ?? []),
  ...["(intro)", "modeling-the-elevator-problem", "external-links", "the-real-world-case"].map(sectionWords)
];

// Broken controls, third round, group A (docs/reviews/ux-fix-round-3a.md): every sentence this round adds.
const ROUND_3A_CAUSES: TodayCause[] = [
  { kind: "section_writing", title: "Probability", part: "Conditional probability", card: BOOK, progress: { done: 2, total: 8 }, failedTopics: true },
  { kind: "section_writing", title: "Probability", part: null, card: BOOK, progress: null, failedTopics: true }
];
const ROUND_3A_SENTENCES = [
  ...ROUND_3A_CAUSES.flatMap((cause) => [causeSentence(cause), goalCauseSentence(cause), causeTopicsFailed(cause) ?? ""]),
  // UX-49: the session end's marks.
  ...([{ evidence: "on_your_own", finishedWithHelp: true }, { evidence: "on_your_own" }, { evidence: "with_help" }] as const).map((mark) =>
    sessionTopicLine({ learningObjectId: "lo_1", title: "Dot product", ...mark }))
];

// Broken controls, third round, group B (docs/reviews/ux-fix-round-3b.md): every sentence this round adds.
const ROUND_3B_SENTENCES = [
  // UX-50: the Notes rail's note box once the passage is highlighted.
  "save note", "add a note to this highlight…", "add to your note on this highlight…", "your note: “the gaps between arrivals matter”",
  // UX-51: the selection box's words.
  INTENT_COPY.whereThisGoes, INTENT_COPY.findsOnly("highlight"), INTENT_COPY.keptAsNote,
  // UX-56: Ask's source chips.
  ...["Wikipedia Elevator Paradox · modeling-the-elevator-problem", "Some Notes · root", "Wikipedia Elevator Paradox · (intro)"].map(citationWords),
  // UX-54: a book waiting its turn (the card's line is the sidecar's; Today's sentences).
  "Waiting its turn behind “Probability”",
  ...([
    { kind: "on_the_way", title: "Past Exam", card: BOOK, progress: null, minutes: null, behind: "Probability" },
    { kind: "on_the_way", title: "Probability", card: BOOK, progress: { done: 1, total: 2 }, minutes: null, queued: ["Past Exam"] },
    { kind: "on_the_way", title: "Probability", card: BOOK, progress: null, minutes: null, queued: ["Past Exam", "Notes"] }
  ] as TodayCause[]).map(causeSentence)
];

// UX-11: the confirmation before a web page is read again (learnloop/content/pipeline/reread.py web_reread_plan).
const UX11_SENTENCES = [
  "Read “Symmetric matrices and variance” again with its equations?",
  "Read on this computer from the copy saved when you added it: free.",
  "The new text keeps the 31 equations the old one left out, and each section's own title.",
  "The new text keeps each section's own title.",
  "Reading it sends nothing to an AI. Questions already written stay. Afterwards, as for any page you add, the new text may be indexed or checked against your topics, and a section whose text changed is read by the AI again before new questions are written from it."
];

// The Decider's sentence (Tier 1): the sheet names what its small judgments
// send to Perplexity, as Settings does, in the sheet's plain words.
const DECIDER_NOTE =
  "With an OpenRouter key, LearnLoop also asks Perplexity, through OpenRouter, short questions about your answers and questions (whether a mix-up or a gap is one it already knows) and about the book passages behind a reworded skill.";

const CONNECTION: AiConnectionDto = {
  canAuthor: false,
  provider: "codex_medium",
  providerLabel: "ChatGPT",
  consentKey: "codex",
  consented: false,
  consentedAt: null,
  needs: "connect",
  message: null,
  whatLeaves: `LearnLoop sends passages of the books you add, and your answers, to ChatGPT to write questions and give feedback. ${DECIDER_NOTE}`,
  deciderNote: DECIDER_NOTE,
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

  // UX fix stage 3: Today's causes, the goal's, the clocks' and the refusals' fixed words.
  it.each(STAGE3_SENTENCES)("the stage 3 sentence: %s", (sentence) => {
    expectPlain(sentence);
  });

  it.each(ROUND_2A_SENTENCES)("the broken controls 2 sentence: %s", (sentence) => {
    expect(sentence).not.toBe("");
    expectPlain(sentence);
  });

  it.each(ROUND_2B_SENTENCES)("the broken controls 2b sentence: %s", (sentence) => {
    expect(sentence).not.toBe("");
    expectPlain(sentence);
  });

  it.each(ROUND_3A_SENTENCES)("the broken controls 3a sentence: %s", (sentence) => {
    expect(sentence).not.toBe("");
    expectPlain(sentence);
  });

  it.each(ROUND_3B_SENTENCES)("the broken controls 3b sentence: %s", (sentence) => {
    expect(sentence).not.toBe("");
    expectPlain(sentence);
  });

  it.each(UX11_SENTENCES)("the read-again sentence: %s", (sentence) => {
    expectPlain(sentence);
  });

  // Waiting you can see (docs/reviews/ux-waiting.md): every line the shared waiting indicator says.
  it.each(Object.values(WAITING_COPY))("the waiting line: %s", (sentence) => {
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

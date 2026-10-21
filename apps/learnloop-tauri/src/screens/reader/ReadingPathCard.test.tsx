// Reader workbench RW7a: the Guide's reading path card (spec §10.1; UX §4.11, W1).
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReadingPathDto, ReadingPathExerciseDto, ReadingPathSectionDto } from "../../api/dto";
import { GuideRail, type GuideRailProps } from "./GuideRail";
import { ReadingPathCard } from "./ReadingPathCard";
import { READING_PATH_REFRESH_MS, exercisesWorthTrying, offeredChoice, readingPathRefreshKey, shouldPoll } from "./readingPath";
import { SEEN_REPORT_MS } from "./useReadingProgress";

const { api } = vi.hoisted(() => ({ api: {
  readerReadingPath: vi.fn(), readerReadingPathSetDepth: vi.fn(), readerReadingPathOverride: vi.fn(),
} }));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const DEPTHS = [
  { id: "get_the_idea" as const, label: "get the idea", means: "definitions, examples, visualizations" },
  { id: "learn_to_use_it" as const, label: "learn to use it", means: "explanations, worked examples, practice" },
  { id: "fluency" as const, label: "fluency", means: "novel problems, changed assumptions, delayed checks" },
];
const EXERCISE: ReadingPathExerciseDto = {
  label: "Exercise 5.14", extractionId: "ext", spanIds: ["s9"], page: 4, statement: "5.14 Derive the CDF.", preview: "5.14 Derive the CDF.",
  importRequest: { extractionId: "ext", sourceId: "src", revisionId: "rev", rawSelection: { nodes: [{ spanId: "s9", start: 0, end: 20 }] } },
};

function section(over: Partial<ReadingPathSectionDto> = {}): ReadingPathSectionDto {
  return {
    sectionId: "u54", title: "5.4 Mixtures", startSpanId: "s1", label: "core", chip: "core",
    reason: "you'll need it for 5.14", override: null, effectiveLabel: "core", exercise: EXERCISE, words: 900,
    learningObjectIds: ["lo_mix"], ...over,
  };
}

function path(over: Partial<ReadingPathDto> = {}): ReadingPathDto {
  return {
    extractionId: "ext", status: "ready", depth: "learn_to_use_it", depthLabel: "learn to use it", depthOrigin: "guide",
    intent: null, depths: DEPTHS, goal: null, goalLine: "No active goal covers this book: the path follows the depth you chose.",
    sections: [
      section(),
      section({ sectionId: "u55", title: "5.5 Sums vs mixtures", startSpanId: "s20", label: "enrichment", chip: "enrichment",
        reason: "skip unless you want sums vs mixtures", effectiveLabel: "enrichment", exercise: null }),
      section({ sectionId: "u53", title: "5.3 Conditioning", startSpanId: "s30", label: "already_shown", chip: "already shown ●",
        reason: "You've shown this on your own: Conditional probability.", effectiveLabel: "already_shown", exercise: null }),
    ],
    next: { text: "Next: read §5.4 Mixtures, then try Exercise 5.14 · about 5 min of reading", sectionId: "u54", spanId: "s1",
      exercise: EXERCISE, minutes: 5 },
    ...over,
  };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  Element.prototype.scrollIntoView = vi.fn();
});
afterEach(() => { cleanup(); vi.useRealTimers(); });

async function mount(props: Partial<Parameters<typeof ReadingPathCard>[0]> = {}) {
  const handlers = { onJump: vi.fn(), onTryExercise: vi.fn(), onError: vi.fn() };
  const utils = render(<ReadingPathCard extractionId="ext" {...handlers} {...props} />);
  await act(async () => { await Promise.resolve(); });
  return { ...utils, ...handlers };
}

it("asks once how deep to go, makes no call until answered, then shows the path", async () => {
  api.readerReadingPath.mockResolvedValue(path({ status: "ask_depth", depth: null, depthLabel: null, sections: [], next: null }));
  api.readerReadingPathSetDepth.mockResolvedValue(path());
  await mount();
  expect(screen.getByText("How deep do you want to go?")).toBeTruthy();
  expect(screen.queryByText(/Next: read/)).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: /learn to use it/ }));
  await act(async () => { await Promise.resolve(); });
  expect(api.readerReadingPathSetDepth).toHaveBeenCalledWith({ extractionId: "ext", depth: "learn_to_use_it" });
  expect(screen.getByText("your path · learn to use it")).toBeTruthy();
  expect(screen.getByText("Next: read §5.4 Mixtures, then try Exercise 5.14 · about 5 min of reading")).toBeTruthy();
});

it("shows each section's chip, its why on demand, and labels only the model's reasons as its reading", async () => {
  api.readerReadingPath.mockResolvedValue(path());
  await mount();
  expect(screen.getByText("core")).toBeTruthy();
  expect(screen.getByText("enrichment")).toBeTruthy();
  expect(screen.getByText("already shown ●")).toBeTruthy();
  expect(screen.queryByText("you'll need it for 5.14", { exact: false })).toBeNull();
  const whys = screen.getAllByRole("button", { name: /why/ });
  fireEvent.click(whys[0]);
  expect(screen.getByText(/you'll need it for 5\.14/)).toBeTruthy();
  expect(screen.getByText("model's reading")).toBeTruthy();
  fireEvent.click(whys[0]);
  fireEvent.click(whys[2]);
  // "already shown" is code's evidence line, never the model's reading.
  expect(screen.getByText(/You've shown this on your own/)).toBeTruthy();
  expect(screen.queryByText("model's reading")).toBeNull();
});

it("skip it on a core section and read it anyway on enrichment send the learner's choice and show it kept", async () => {
  api.readerReadingPath.mockResolvedValue(path());
  api.readerReadingPathOverride.mockResolvedValue(path({ sections: [
    section({ override: "skip", effectiveLabel: "skipped" }), path().sections[1], path().sections[2]] }));
  await mount();
  fireEvent.click(screen.getAllByRole("button", { name: /why/ })[0]);
  fireEvent.click(screen.getByRole("button", { name: "skip it" }));
  await act(async () => { await Promise.resolve(); });
  expect(api.readerReadingPathOverride).toHaveBeenCalledWith({ extractionId: "ext", depth: "learn_to_use_it", sectionId: "u54", choice: "skip" });
  expect(screen.getByText(/nothing is marked as known/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "undo" }));
  await act(async () => { await Promise.resolve(); });
  expect(api.readerReadingPathOverride).toHaveBeenLastCalledWith({ extractionId: "ext", depth: "learn_to_use_it", sectionId: "u54", choice: "none" });
});

it("one exercise worth trying opens through Try it, or the book when the workbench is off", async () => {
  api.readerReadingPath.mockResolvedValue(path());
  const first = await mount();
  fireEvent.click(screen.getByRole("button", { name: "Try it ▸" }));
  expect(first.onTryExercise).toHaveBeenCalledWith(EXERCISE);
  cleanup();
  const second = await mount({ onTryExercise: null });
  expect(screen.queryByRole("button", { name: "Try it ▸" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "open in the book ▸" }));
  expect(second.onJump).toHaveBeenCalledWith("s9");
});

it("reads the path again while it is being judged and stops once it lands", async () => {
  vi.useFakeTimers();
  api.readerReadingPath
    .mockResolvedValueOnce(path({ status: "judging", sections: [], next: null }))
    .mockResolvedValueOnce(path());
  render(<ReadingPathCard extractionId="ext" onJump={vi.fn()} onTryExercise={vi.fn()} onError={vi.fn()} />);
  await act(async () => { await Promise.resolve(); });
  expect(screen.getByText("◐ reading a path for this book…")).toBeTruthy();
  await act(async () => { vi.advanceTimersByTime(1600); await Promise.resolve(); });
  expect(api.readerReadingPath).toHaveBeenCalledTimes(2);
  expect(screen.getByText(/Next: read/)).toBeTruthy();
  await act(async () => { vi.advanceTimersByTime(5000); await Promise.resolve(); });
  expect(api.readerReadingPath).toHaveBeenCalledTimes(2);
});

it("a failed judgment says so with try again; a used budget names the money and offers no retry", async () => {
  api.readerReadingPath.mockResolvedValueOnce(path({ status: "failed", sections: [], next: null, reason: "judge_failed",
    message: "Couldn't read a path for this book just now. Try again ↵" })).mockResolvedValueOnce(path());
  await mount();
  fireEvent.click(screen.getByRole("button", { name: "try again ↵" }));
  await act(async () => { await Promise.resolve(); });
  expect(api.readerReadingPath).toHaveBeenLastCalledWith({ extractionId: "ext", retry: true });
  cleanup();
  api.readerReadingPath.mockResolvedValue(path({ status: "failed", sections: [], next: null, reason: "capped",
    message: "Today's reading-path budget ($0.50) is used. The book and the Guide still work." }));
  await mount();
  expect(screen.getByText(/budget \(\$0\.50\) is used/)).toBeTruthy();
  expect(screen.queryByRole("button", { name: "try again ↵" })).toBeNull();
});

it("names the plan setting a depth came from, and a withheld reading shows one line", async () => {
  api.readerReadingPath.mockResolvedValue(path({ depthOrigin: "intent", intent: { choice: "learn", label: "Learn" } }));
  await mount();
  expect(screen.getByText("from your Learn setting for this book")).toBeTruthy();
  cleanup();
  api.readerReadingPath.mockResolvedValue({ ...path({ status: "withheld", sections: [], next: null }),
    message: "This reading is held out for an exam: it has no reading path." });
  await mount();
  expect(screen.getByText(/held out for an exam/)).toBeTruthy();
  expect(screen.queryByText("YOUR PATH")).toBeNull();
});

it("the pure helpers: poll only while judging, offer skip on what to read and read anyway on the rest", () => {
  expect(shouldPoll(path({ status: "judging" }))).toBe(true);
  expect(shouldPoll(path({ status: "pending" }))).toBe(true);
  expect(shouldPoll(path({ status: "failed" }))).toBe(false);
  expect(shouldPoll(null)).toBe(false);
  expect(offeredChoice(section())).toBe("skip");
  expect(offeredChoice(section({ label: "prerequisite" }))).toBe("skip");
  expect(offeredChoice(section({ label: "assumed" }))).toBe("read_anyway");
  expect(offeredChoice(section({ override: "skip" }))).toBeNull();
  expect(exercisesWorthTrying(path()).map((s) => s.sectionId)).toEqual(["u54"]);
  expect(exercisesWorthTrying(path({ sections: [section({ override: "skip", effectiveLabel: "skipped" })] }))).toEqual([]);
});

function guideProps(over: Partial<GuideRailProps> = {}): GuideRailProps {
  const noop = () => undefined;
  return {
    visible: true, extractionId: "ext", offline: false,
    guidePlan: { sourceId: "src", extractionId: "ext", personalized: false, selectionBasis: "", sections: [],
      pendingDiagnosisAttemptIds: [], goalContext: { title: "Derive mixture distributions" } },
    guideLoading: false, currentGuideSection: null, currentSectionProgress: 0, currentQuestionOpen: false,
    boundaryChecksAvailable: false, authoringSections: [], revealedSections: [], completedSections: [],
    annotatedSpans: new Set(), openQuestionSections: [], setDismissedSections: noop, jumpToSpan: noop,
    revealSection: noop, completeSection: noop, onError: noop, boundaryBlock: null, boundarySkipped: false,
    setBoundarySkipped: noop, boundaryAnswered: false, setBoundaryAnswered: noop, boundaryResponse: "",
    setBoundaryResponse: noop, boundarySubmitted: false, setBoundarySubmitted: noop, questionControl: null,
    sendQuestionControl: noop, disposition: null, chooseDisposition: noop, ...over,
  } as unknown as GuideRailProps;
}

it("the Guide shows the path card in place of the goal card, and today's goal card without it", () => {
  const { container, rerender } = render(<GuideRail {...guideProps()} />);
  expect(screen.getByText("Reading toward your active goal")).toBeTruthy();
  const without = container.innerHTML;
  rerender(<GuideRail {...guideProps({ path: undefined })} />);
  expect(container.innerHTML).toBe(without);
  rerender(<GuideRail {...guideProps({ path: <div>the path card</div> })} />);
  expect(screen.getByText("the path card")).toBeTruthy();
  expect(screen.queryByText("Reading toward your active goal")).toBeNull();
});

// Codex review F3: a ready path follows the learner while the card stays mounted.
it("a ready card reads the path again when what it depends on changes, without a remount", async () => {
  vi.useFakeTimers();
  const after = path({ next: { text: "Next: read 5.6 Convolutions · about 2 min of reading", sectionId: "u56", spanId: "s40",
    exercise: null, minutes: 2 } });
  api.readerReadingPath.mockResolvedValueOnce(path()).mockResolvedValueOnce(after);
  const props = { extractionId: "ext", onJump: vi.fn(), onTryExercise: vi.fn(), onError: vi.fn() };
  const { rerender } = render(<ReadingPathCard {...props} refreshKey="|1" />);
  await act(async () => { await Promise.resolve(); });
  expect(screen.getByText(/Next: read §5\.4 Mixtures/)).toBeTruthy();
  // A ready path is not polled: nothing changes, nothing is read.
  await act(async () => { vi.advanceTimersByTime(10_000); await Promise.resolve(); });
  expect(api.readerReadingPath).toHaveBeenCalledTimes(1);
  // The learner finished 5.4 (and a burst of changes folds into one read).
  rerender(<ReadingPathCard {...props} refreshKey="u54|1" />);
  await act(async () => { vi.advanceTimersByTime(500); await Promise.resolve(); });
  rerender(<ReadingPathCard {...props} refreshKey="u54|2" />);
  await act(async () => { vi.advanceTimersByTime(READING_PATH_REFRESH_MS - 1); await Promise.resolve(); });
  expect(api.readerReadingPath).toHaveBeenCalledTimes(1);
  await act(async () => { vi.advanceTimersByTime(1); await Promise.resolve(); });
  expect(api.readerReadingPath).toHaveBeenCalledTimes(2);
  expect(api.readerReadingPath).toHaveBeenLastCalledWith({ extractionId: "ext" });
  expect(screen.getByText("Next: read 5.6 Convolutions · about 2 min of reading")).toBeTruthy();
  expect(screen.queryByText(/Next: read §5\.4 Mixtures/)).toBeNull();
});

it("the refresh key: a section counts once finished or every passage seen, and every signal is in it", () => {
  const sections = [{ id: "a", spanIds: ["s1", "s2"] }, { id: "b", spanIds: ["s3"] }, { id: "c", spanIds: [] }];
  const key = (completedSections: string[], sectionSeen: Record<string, number>, signals: Array<string | number> = [1],
    progressSaves = 0) => readingPathRefreshKey({ sections, completedSections, sectionSeen, progressSaves, signals });
  expect(key([], {})).toBe("|saved:0|1");
  expect(key([], { a: 1 })).toBe("|saved:0|1"); // half read: not done, no re-read
  expect(key([], { a: 2 })).toBe("a|saved:0|1");
  expect(key(["b"], { a: 2 })).toBe("a,b|saved:0|1");
  expect(key([], { c: 0 })).toBe("|saved:0|1"); // no passages: only completion counts
  expect(key([], {}, [1, 2, "w:open"])).toBe("|saved:0|1|2|w:open");
  // Re-review F3: a landed progress save is a change of its own.
  expect(key([], { a: 1 }, [1], 3)).toBe("|saved:3|1");
  // The common case folds into one read after the Reader's progress save.
  expect(READING_PATH_REFRESH_MS).toBeGreaterThan(SEEN_REPORT_MS);
});

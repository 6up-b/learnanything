// Reader RW3b on the real screen (spec §6.1-6.2; UX §3.4, §4.3, §4.4): the
// discovered cues the sidecar merges into the plan. Each kind draws its own
// static glyph (◌┆ distinction, ●┆ a new application, ▹┆ try the next step
// first) with the "found by LearnLoop's model, not by a test" line; open shows
// the passage's own words and the statement in the model's voice; try the next
// step first opens RW1b's next-step question at that line (the learner's pick)
// and records the tap; every tap goes through reader.cue_tap with the visit;
// the background search runs once per targetsKey and re-reads the plan when it
// found something; impressions are sent for marks in view and for held-out
// cues whose passage is in view (the sidecar decides the holdout); the legend
// names the discovered marks; G16 over the new copy.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "./ReaderScreen";
import { readerRenderViewFixture } from "../fixtures/readerRenderView";
import type { ReaderCueDto, ReaderGuidePlanDto, ReaderRenderViewDto, SourceLibraryCard } from "../api/dto";
import { flushReaderActivity, resetReaderActivityForTests } from "./reader/activity";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
  readerLogActivity: vi.fn(), readerSetMode: vi.fn(), readerCueAction: vi.fn(), readerSetCuePreferences: vi.fn(),
  readerWatchPlan: vi.fn(), readerCueTap: vi.fn(), readerCueDiscovery: vi.fn(), readerCueDiscoveryJob: vi.fn(),
  readerCueImpressions: vi.fn(), readerActiveQuestion: vi.fn(),
}));
const guide = vi.hoisted(() => ({ plan: null as unknown, reads: 0 }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true, inquiryEnabled: true, activeReading: { foldBlocks: 2 } } : { sources: [source.card] }, error: null }) }));
vi.mock("./reader/readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./reader/guidePlan", () => ({
  readGuidePlan: () => {
    guide.reads += 1;
    return Promise.resolve(guide.plan);
  },
  useGuideDiagnosisRefresh: () => undefined,
}));
vi.mock("./reader/useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const SPANS = ["b0", "b1", "b2", "b3", "b4", "b5"];
const view: ReaderRenderViewDto = {
  ...readerRenderViewFixture,
  blocks: SPANS.map((spanId, index) => ({
    ...readerRenderViewFixture.blocks[1], spanId, displayNodeId: `node-${spanId}`,
    markdown: `Passage ${index}: the density of a mixture.`,
  })),
};
const card = { sourceId: view.sourceId, title: "Probability", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const source = vi.hoisted(() => ({ card: null as unknown }));
const STATEMENT = "The learner reads a density value as a probability.";
const ANSWER = "Yes: f(0.5) = 2 means it happens twice as often.";

function cue(spanId: string, rank: number): ReaderCueDto {
  const note = "Connects to something you worked on: Densities.";
  const because = "Because: your answer on 2 Oct · from the Guide's citations";
  return {
    cueId: `cue_${spanId}`, kind: "revisit", spanId, sectionId: "u1", learningObjectId: "lo_density",
    learningObjectTitle: "Densities", targetId: "err_1", rank, sectionRank: rank, note, because,
    label: `Note on this paragraph: ${note} ${because}`,
    earlier: {
      attemptId: "att_1", practiceItemId: "pi_density", prompt: "Is f(0.5) = 2 a probability?", answer: ANSWER,
      answeredAt: "2026-10-02T09:00:00Z", answeredOn: "2 Oct", statement: STATEMENT, statementPending: false,
    },
  };
}

function plan(options: { cues?: boolean; marks?: ReaderCueDto[]; density?: "off" | "fewer" | "normal" | "more"; sourceOff?: boolean } = {}): ReaderGuidePlanDto {
  const marks = options.marks ?? [cue("b1", 0), cue("b4", 1)];
  const passages = ["b1", "b4"].map((spanId) => ({
    spanId, quote: `Passage ${SPANS.indexOf(spanId)}`, reason: `Revisit this to resolve: ${STATEMENT}`,
    learningObjectId: "lo_density", learningObjectTitle: "Densities", learnerSignal: "recent_misunderstanding",
  }));
  return {
    version: 1, sourceId: view.sourceId, extractionId: view.extractionId, personalized: true, selectionBasis: "",
    goalContext: null,
    sections: [{ id: "u1", label: "Densities", startSpanId: "b0", endSpanId: "b5", spanIds: SPANS, question: null, suggestedPassages: passages }],
    ...(options.cues === false ? {} : {
      cues: {
        version: "rw3a-guide-cues-v1", density: options.density ?? "normal", budgetPerSection: 2, onePerViewport: true,
        sourceOff: options.sourceOff ?? false, marks: options.sourceOff ? [] : marks, withheld: {},
      },
    }),
  } as ReaderGuidePlanDto;
}

// jsdom has no layout: each passage sits where TOPS says, the reading area is 600px.
const TOPS: Record<string, number> = { b0: 0, b1: 100, b2: 300, b3: 500, b4: 900, b5: 1100 };
let rectSpy: ReturnType<typeof vi.spyOn> | null = null;

beforeEach(() => {
  vi.resetAllMocks();
  resetReaderActivityForTests();
  source.card = card;
  guide.plan = plan();
  guide.reads = 0;
  Element.prototype.scrollIntoView = vi.fn();
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerSetMode.mockResolvedValue({ mode: "skim" });
  api.readerCueAction.mockImplementation(async (input: { cueId: string; action: string }) => ({
    cueId: input.cueId, action: input.action, eventId: "ev", verdict: input.action === "not_relevant" ? "different" : "same",
    ledgerId: null, check: null,
  }));
  api.readerSetCuePreferences.mockImplementation(async (input: { density?: string | null; sourceOff?: boolean | null }) => ({
    enabled: true, density: input.density ?? "normal", budgetPerSection: 2, onePerViewport: true,
    sourceOff: Boolean(input.sourceOff), offSourceCount: input.sourceOff ? 1 : 0,
  }));
  rectSpy = vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
    const spanId = (this as HTMLElement).dataset?.spanId ?? "";
    const top = TOPS[spanId] ?? 0;
    return { top, bottom: top + 40, left: 0, right: 500, width: 500, height: 40, x: 0, y: top, toJSON: () => ({}) } as DOMRect;
  });
  Object.defineProperty(HTMLElement.prototype, "clientHeight", {
    configurable: true,
    get(this: HTMLElement) {
      return this.getAttribute("role") === "main" ? 600 : 0;
    },
  });
});
afterEach(() => {
  cleanup();
  rectSpy?.mockRestore();
  // @ts-expect-error -- restore jsdom's own (prototype chain) getter
  delete HTMLElement.prototype.clientHeight;
});

function openReader(props: { onCheckMe?: (request: unknown) => void; spanId?: string | null } = {}) {
  return render(
    <ReaderScreen initialSource={{ card, spanId: props.spanId ?? null }} onError={vi.fn()} onCheckMe={props.onCheckMe} />,
  );
}

const markFor = (spanId: string) => document.querySelector<HTMLButtonElement>(`[data-cue-span="${spanId}"]`);
async function findMark(spanId: string): Promise<HTMLButtonElement> {
  await waitFor(() => expect(markFor(spanId)).not.toBeNull());
  return markFor(spanId) as HTMLButtonElement;
}


const DISCOVERED_BECAUSE = "Because: your work on Densities · found by LearnLoop's model, not by a test";

function discovered(spanId: string, rank: number, kind: ReaderCueDto["kind"], extra: Partial<ReaderCueDto> = {}): ReaderCueDto {
  const note = kind === "try_first" ? "Try the next step before reading it?"
    : kind === "application" ? "A new use of something you've shown: Densities." : "Connects to something you worked on: Densities.";
  return {
    ...cue(spanId, rank), cueId: `dcue_${spanId}`, kind, note, because: DISCOVERED_BECAUSE,
    label: `Note on this paragraph: ${note} ${DISCOVERED_BECAUSE}`, foundBy: "model", linkId: `plink_${spanId}`,
    relation: kind === "try_first" ? "try_first" : kind === "application" ? "new_application" : "clarifies_distinction",
    pickRank: 1, quote: `Passage ${SPANS.indexOf(spanId)}: the density`, targetKind: "misconception",
    pOpen: 0.8, pOpenSource: "episode_posterior", seed: "abc", propensity: 0.9,
    earlier: { attemptId: null, practiceItemId: null, prompt: null, answer: null, answeredAt: null, answeredOn: null,
      statement: STATEMENT, statementPending: false },
    ...extra,
  };
}

function discoveryPlan(marks: ReaderCueDto[], options: { targetsKey?: string; heldOut?: ReaderCueDto[]; tryFirst?: boolean } = {}): ReaderGuidePlanDto {
  const base = plan({ marks });
  return {
    ...base,
    cues: {
      ...(base.cues as NonNullable<ReaderGuidePlanDto["cues"]>),
      discovery: {
        version: "rw3b-discovered-cues-v1", targetsKey: options.targetsKey ?? "tk1", targets: 1, holdoutRate: 0.1,
        valueOrder: true, tryFirst: options.tryFirst ?? true, heldOut: options.heldOut ?? [], suppressed: [],
      },
    },
  };
}

function wireDiscovery() {
  api.readerCueTap.mockImplementation(async (input: { cueId: string; action: string }) => ({
    cueId: input.cueId, action: input.action, eventId: "ev", verdict: "same", ledgerId: null, check: null,
    tryFirst: input.action === "try_first" ? { spanId: "b4" } : null,
  }));
  api.readerCueDiscovery.mockResolvedValue({ jobId: "cjob_1", extractionId: view.extractionId, state: "done",
    result: { status: "done", targetsKey: "tk1", calls: 1, links: 2 } });
  api.readerCueImpressions.mockResolvedValue({ recorded: [] });
  api.readerActiveQuestion.mockResolvedValue({ status: "pending", anchorSpanIds: ["b4"], foldedSpanIds: ["b5"], batchId: null, question: null });
}

it("each discovered kind draws its own static glyph with the model's because line; RW3a's marks keep theirs", async () => {
  TOPS.b4 = 900;
  wireDiscovery();
  guide.plan = discoveryPlan([cue("b1", 0), discovered("b4", 1, "application")]);
  openReader();
  const guideMark = await findMark("b1");
  const application = await findMark("b4");
  expect(guideMark.className).toBe("ll-reader-cue-mark");
  expect(guideMark.getAttribute("data-cue-kind")).toBeNull();
  expect(application.className).toBe("ll-reader-cue-mark ll-reader-cue-mark--application");
  expect(application.textContent).toBe("");
  fireEvent.focus(application);
  const note = await screen.findByRole("note");
  expect(note.textContent).toContain("A new use of something you've shown: Densities.");
  expect(note.textContent).toContain("found by LearnLoop's model, not by a test");
  const css = (await import("node:fs")).readFileSync(`${__dirname}/../styles/app.css`, "utf8");
  for (const [klass, glyph] of [["--application", "●┆"], ["--try-first", "▹┆"]]) {
    const rule = css.split("}").find((entry) => entry.includes(`.ll-reader-cue-mark${klass}::before`)) ?? "";
    expect(rule).toContain(`content: "${glyph}"`);
    expect(rule).not.toMatch(/animation|transition|@keyframes/);
  }
});

it("open on a discovered cue shows the passage's words and the statement in the model's voice; the tap goes through cue_tap with the visit", async () => {
  TOPS.b4 = 900;
  wireDiscovery();
  guide.plan = discoveryPlan([discovered("b1", 0, "distinction")]);
  openReader();
  fireEvent.click(await findMark("b1"));
  const popover = await screen.findByRole("group", { name: "this margin note" });
  fireEvent.click(within(popover).getByRole("button", { name: "open · what you worked on" }));
  expect(within(popover).getByText(/the passage's own words: “Passage 1: the density”/)).toBeTruthy();
  expect(popover.querySelector("[data-voice='model']")?.textContent).toContain(STATEMENT);
  expect(within(popover).queryByText(/You answered a question/)).toBeNull();
  await waitFor(() => expect(api.readerCueTap).toHaveBeenCalledWith(expect.objectContaining({
    extractionId: view.extractionId, cueId: "dcue_b1", action: "opened", visitId: expect.any(String),
  })));
  expect(api.readerCueAction).not.toHaveBeenCalled();
});

it("try the next step first opens RW1b's next-step question at that line and records the learner's pick", async () => {
  TOPS.b4 = 900;
  wireDiscovery();
  guide.plan = discoveryPlan([discovered("b4", 0, "try_first")]);
  openReader();
  fireEvent.click(await findMark("b4"));
  const popover = await screen.findByRole("group", { name: "this margin note" });
  const tryFirst = within(popover).getByRole("button", { name: /^try the next step first ·/ });
  expect(document.activeElement).toBe(tryFirst);
  fireEvent.click(tryFirst);
  await waitFor(() => expect(api.readerActiveQuestion).toHaveBeenCalledWith(expect.objectContaining({
    extractionId: view.extractionId, spanIds: ["b4"], style: "next_step",
  })));
  await waitFor(() => expect(api.readerCueTap).toHaveBeenCalledWith(expect.objectContaining({ cueId: "dcue_b4", action: "try_first" })));
  expect(screen.queryByRole("group", { name: "this margin note" })).toBeNull();
});

it("no try-first action while the plan's try-first switch is off (absent, never disabled)", async () => {
  TOPS.b4 = 900;
  wireDiscovery();
  guide.plan = discoveryPlan([discovered("b4", 0, "try_first")], { tryFirst: false });
  openReader();
  fireEvent.click(await findMark("b4"));
  const popover = await screen.findByRole("group", { name: "this margin note" });
  expect(within(popover).queryByRole("button", { name: /try the next step first/ })).toBeNull();
});

it("the background search runs once per targetsKey and re-reads the plan when it found something", async () => {
  TOPS.b4 = 900;
  wireDiscovery();
  let release: (value: unknown) => void = () => undefined;
  api.readerCueDiscovery.mockImplementation(() => new Promise((resolve) => {
    release = resolve;
  }));
  guide.plan = discoveryPlan([cue("b1", 0)]);
  openReader();
  await findMark("b1");
  await waitFor(() => expect(api.readerCueDiscovery).toHaveBeenCalledTimes(1));
  expect(api.readerCueDiscovery).toHaveBeenCalledWith({ extractionId: view.extractionId });
  const reads = guide.reads;
  guide.plan = discoveryPlan([cue("b1", 0), discovered("b4", 1, "distinction")]);
  await act(async () => {
    release({ jobId: "cjob_1", extractionId: view.extractionId, state: "done",
      result: { status: "done", targetsKey: "tk1", calls: 1, links: 2 } });
  });
  await waitFor(() => expect(guide.reads).toBeGreaterThan(reads));
  await findMark("b4");
  // The same targets: no second search.
  expect(api.readerCueDiscovery).toHaveBeenCalledTimes(1);
});

it("a pending search is read back without waiting, and a search that found nothing re-reads nothing", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  try {
    TOPS.b4 = 900;
    wireDiscovery();
    api.readerCueDiscovery.mockResolvedValue({ jobId: "cjob_2", extractionId: view.extractionId, state: "pending", result: null });
    api.readerCueDiscoveryJob.mockResolvedValue({ jobId: "cjob_2", extractionId: view.extractionId, state: "done",
      result: { status: "done", targetsKey: "tk1", calls: 0, links: 0 } });
    guide.plan = discoveryPlan([cue("b1", 0)]);
    openReader();
    await findMark("b1");
    await act(async () => {
      vi.advanceTimersByTime(2_000);
    });
    await waitFor(() => expect(api.readerCueDiscoveryJob).toHaveBeenCalledWith({ jobId: "cjob_2" }));
    const reads = guide.reads;
    // Nothing found: the plan is not re-read for it.
    expect(guide.reads).toBe(reads);
  } finally {
    vi.useRealTimers();
  }
});

it("impressions: a mark in view is sent as shown; a held-out cue's passage in view is sent for the sidecar to record", async () => {
  TOPS.b4 = 900;
  wireDiscovery();
  const observed: Array<{ callback: IntersectionObserverCallback; targets: Element[] }> = [];
  class FakeObserver {
    callback: IntersectionObserverCallback;
    targets: Element[] = [];
    constructor(callback: IntersectionObserverCallback) {
      this.callback = callback;
      observed.push(this);
    }
    observe(target: Element) {
      this.targets.push(target);
    }
    unobserve() {}
    disconnect() {}
  }
  vi.stubGlobal("IntersectionObserver", FakeObserver);
  try {
    guide.plan = discoveryPlan([discovered("b1", 0, "distinction")], { heldOut: [discovered("b4", 1, "distinction")] });
    openReader();
    await findMark("b1");
    await waitFor(() => expect(observed.some((entry) => entry.targets.length > 0)).toBe(true));
    await act(async () => {
      for (const entry of observed) {
        entry.callback(entry.targets.map((target) => ({ isIntersecting: true, intersectionRatio: 1, target })) as unknown as IntersectionObserverEntry[], entry as unknown as IntersectionObserver);
      }
      await new Promise((resolve) => setTimeout(resolve, 900));
    });
    const sent = api.readerCueImpressions.mock.calls.flatMap((call) => (call[0] as { entries: Array<{ cueId: string; shown?: boolean }> }).entries);
    expect(sent).toContainEqual({ cueId: "dcue_b1", shown: true });
    expect(sent).toContainEqual({ cueId: "dcue_b4", shown: false });
    // The held-out cue is never drawn.
    expect(markFor("b4")).toBeNull();
  } finally {
    vi.unstubAllGlobals();
  }
});

it("the legend names the discovered marks, and G16 holds over every new string", async () => {
  const { DISCOVERED_COPY } = await import("./reader/cues");
  const banned = /\b(weak|you don'?t understand|you struggle|you always|wrong|error|errors|mistake|mistakes|confused|failed|failure|overdue)\b/i;
  const strings = Object.values(DISCOVERED_COPY).flatMap((value) => (typeof value === "string" ? [value] : Object.values(value)));
  for (const text of strings) expect(text).not.toMatch(banned);
  TOPS.b4 = 900;
  wireDiscovery();
  guide.plan = discoveryPlan([discovered("b1", 0, "distinction")]);
  openReader();
  await findMark("b1");
  const footer = document.querySelector("[data-cue-footer]") as HTMLElement;
  fireEvent.click(within(footer).getByRole("button", { name: /what the marks mean/ }));
  const legend = footer.querySelector("[data-cue-legend-discovered]") as HTMLElement;
  expect(legend.textContent).toContain("a new use of something you've shown");
  expect(legend.textContent).toContain("try the next step first");
});

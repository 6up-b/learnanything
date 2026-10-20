// Reader RW3b, Codex review fixes on the real screen, with the real Guide
// plan reads (only the sidecar is faked): F8 while the plan says a target can
// still be named (a learner-text gap being read), the Reader re-reads the plan,
// and the new targets ask for discovery in the same session; F12 "open" on a
// discovered cue shows the cited answer and the learner's own words in the
// learner's voice, the target's statement in the model's.
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
  // The real readGuidePlan reads through the (pass-through) cache to the sidecar.
  api.readerGuidePlan.mockImplementation(async () => {
    guide.reads += 1;
    return guide.plan;
  });
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

function discoveryPlan(marks: ReaderCueDto[], options: { targetsKey?: string; heldOut?: ReaderCueDto[]; tryFirst?: boolean; targetsPending?: boolean } = {}): ReaderGuidePlanDto {
  const base = plan({ marks });
  return {
    ...base,
    cues: {
      ...(base.cues as NonNullable<ReaderGuidePlanDto["cues"]>),
      discovery: {
        version: "rw3b-discovered-cues-v1", targetsKey: options.targetsKey ?? "tk1", targets: 1, holdoutRate: 0.1,
        valueOrder: true, tryFirst: options.tryFirst ?? true, heldOut: options.heldOut ?? [], suppressed: [],
        targetsPending: options.targetsPending ?? false,
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


it("F8: a gap that lands while the Reader is open asks for discovery in the same session", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  try {
    TOPS.b4 = 900;
    wireDiscovery();
    api.readerCueDiscovery.mockImplementation(async () => ({ jobId: "cjob", extractionId: view.extractionId,
      state: "done", result: { status: "done", targetsKey: (guide.plan as ReaderGuidePlanDto).cues?.discovery?.targetsKey ?? null,
        calls: 0, links: 0 } }));
    guide.plan = discoveryPlan([cue("b1", 0)], { targetsKey: "tk1", targetsPending: true });
    openReader();
    await findMark("b1");
    await waitFor(() => expect(api.readerCueDiscovery).toHaveBeenCalledTimes(1));
    // The gap lands: the next plan read has a new target and nothing pending.
    guide.plan = discoveryPlan([cue("b1", 0)], { targetsKey: "tk2", targetsPending: false });
    await act(async () => {
      vi.advanceTimersByTime(4_100);
    });
    await waitFor(() => expect(api.readerCueDiscovery).toHaveBeenCalledTimes(2));
    const reads = guide.reads;
    await act(async () => {
      vi.advanceTimersByTime(70_000);
    });
    // Nothing pending any more: no further re-reads for it.
    expect(guide.reads).toBe(reads);
  } finally {
    vi.useRealTimers();
  }
});

it("F12: open on a discovered cue shows the cited answer and the learner's own words, apart from the model's statement", async () => {
  TOPS.b4 = 900;
  wireDiscovery();
  guide.plan = discoveryPlan([discovered("b1", 0, "distinction", {
    earlier: { attemptId: "att_1", practiceItemId: "pi_density", prompt: "Is f(0.5) = 2 a probability?", answer: ANSWER,
      answeredAt: "2026-10-02T09:00:00Z", answeredOn: "2 Oct", statement: STATEMENT, statementPending: false,
      learnerText: "why can a density be bigger than one?", learnerTextKind: "tutor_question" },
  })]);
  openReader();
  fireEvent.click(await findMark("b1"));
  const popover = await screen.findByRole("group", { name: "this margin note" });
  fireEvent.click(within(popover).getByRole("button", { name: "open · what you worked on" }));
  expect(within(popover).getByText(/You answered a question on this on 2 Oct/)).toBeTruthy();
  expect(within(popover).getByText(/Is f\(0\.5\) = 2 a probability\?/)).toBeTruthy();
  const learner = Array.from(popover.querySelectorAll("[data-voice='learner']")).map((node) => node.textContent ?? "");
  expect(learner.some((text) => text.includes(ANSWER))).toBe(true);
  expect(learner.some((text) => text.includes("your question") && text.includes("why can a density be bigger than one?"))).toBe(true);
  const model = popover.querySelector("[data-voice='model']")?.textContent ?? "";
  expect(model).toContain(STATEMENT);
  expect(model).not.toContain(ANSWER);
});

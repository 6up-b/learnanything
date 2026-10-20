// Reader RW3b's switch-off pin (stage reader-rw3b): with every RW3b switch
// off the sidecar sends RW3a's cues exactly as at c9ad9cce1 (no discovered
// marks, no discovery key), and the Reader must draw them exactly as RW3a
// did: the same gutter, note, popover and footer markup, and no call RW3a
// never made (the api mock names only RW3a's calls, so a discovery request
// or an impression receipt would throw). The snapshots in
// __snapshots__/ReaderScreen.cuesSwitchOff.test.tsx.snap were written on the
// base commit, before any RW3b frontend code existed.
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
  readerWatchPlan: vi.fn(),
}));
const guide = vi.hoisted(() => ({ plan: null as unknown, reads: 0 }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true, inquiryEnabled: true } : { sources: [source.card] }, error: null }) }));
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


/** React's generated ids depend on render order; the markup is the contract. */
function markup(node: Element): string {
  return node.outerHTML.replace(/:r[0-9a-z]+:/g, ":r:").replace(/«r[0-9a-z]+»/g, "«r»");
}

it("RW3a's marks, note, popover and footer render exactly as at the base with RW3b off", async () => {
  TOPS.b4 = 900;
  openReader({ onCheckMe: vi.fn() });
  const mark = await findMark("b1");
  await findMark("b4");
  const gutter = Array.from(document.querySelectorAll("[data-cue-slot]")).map(markup);
  expect(gutter).toMatchSnapshot("gutter");
  fireEvent.focus(mark);
  expect(markup(await screen.findByRole("note"))).toMatchSnapshot("note");
  fireEvent.blur(mark);
  fireEvent.click(mark);
  const popover = await waitFor(() => {
    const found = document.querySelector("[data-cue-popover]");
    expect(found).not.toBeNull();
    return found as Element;
  });
  fireEvent.click(within(popover as HTMLElement).getByRole("button", { name: /^open/ }));
  expect(markup(document.querySelector("[data-cue-popover]") as Element)).toMatchSnapshot("popover");
  const footer = document.querySelector("[data-cue-footer]") as HTMLElement;
  fireEvent.click(within(footer).getByRole("button", { name: /what the marks mean/ }));
  expect(markup(document.querySelector("[data-cue-footer]") as Element)).toMatchSnapshot("footer");
  await act(async () => {
    flushReaderActivity();
  });
  // Only RW3a's own calls: the tap on "open" and the funnel's activity.
  expect(api.readerCueAction.mock.calls.map((call) => (call[0] as { action: string }).action)).toEqual(["opened"]);
  expect(api.readerSetCuePreferences).not.toHaveBeenCalled();
});

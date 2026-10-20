// RW3a on the real screen (spec §6.1-6.2; UX §3.4, §4.4, §7): the Guide's own
// misunderstanding passages as quiet margin marks. The mark's note and its
// "because" line (G16), the margin agreeing with the rail (G30), at most one
// mark per screenful and never on the restored passage, never while skimming,
// never animated (G13, G14), Alt+↓ / Alt+↑ between marks, the popover's
// actions (open, check me, not relevant with its why, fewer marks like this,
// marks off for the book or everywhere, each with undo), the impressions in
// the funnel, a transcript, and the kill switch (no marks, no control).
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

it("G30 and G16: the Guide's misunderstanding passage carries a quiet mark with its fixed note and why", async () => {
  TOPS.b4 = 900;
  openReader();
  const mark = await findMark("b1");
  // Its accessible name is the full sentence (UX §7.2).
  expect(screen.getAllByRole("button", { name: cue("b1", 0).label })).toContain(mark);
  // The mark sits beside its own passage (in the passage's gutter).
  expect(mark.closest("[data-span-id]")?.getAttribute("data-span-id")).toBe("b1");
  // Its glyph is CSS: no text node a selection or a marquee could quote.
  expect(mark.textContent).toBe("");
  expect(mark.className).toBe("ll-reader-cue-mark");
  fireEvent.focus(mark);
  const note = await screen.findByRole("note");
  expect(note.textContent).toContain("Connects to something you worked on: Densities.");
  expect(note.textContent).toContain("Because: your answer on 2 Oct · from the Guide's citations");
  // The rail's reason stays in the rail; the note never names the statement.
  expect(note.textContent).not.toContain("Revisit this to resolve");
  expect(note.textContent).not.toContain(STATEMENT);
  // Every drawn mark is one of the rail's misunderstanding passages (G30).
  const railSpans = new Set((guide.plan as ReaderGuidePlanDto).sections[0].suggestedPassages
    .filter((passage) => passage.learnerSignal === "recent_misunderstanding").map((passage) => passage.spanId));
  const drawn = Array.from(document.querySelectorAll<HTMLElement>("[data-cue-span]")).map((node) => node.dataset.cueSpan);
  expect(drawn.length).toBeGreaterThan(0);
  for (const spanId of drawn) expect(railSpans.has(spanId as string)).toBe(true);
  // The footer's density control and legend.
  const footer = screen.getByRole("group", { name: "margin marks" });
  expect(within(footer).getByRole("button", { name: "●normal" }).getAttribute("aria-pressed")).toBe("true");
  expect(screen.getByText("a display limit to protect your attention")).toBeTruthy();
});

it("G13: at most one mark per screenful -- a lower-ranked mark within one viewport of a higher-ranked one is not drawn", async () => {
  TOPS.b4 = 400; // 300px below b1, inside one 600px screenful
  openReader();
  await findMark("b1");
  expect(markFor("b4")).toBeNull();
  cleanup();
  TOPS.b4 = 900; // a screenful and more away: both are drawn
  openReader();
  await findMark("b1");
  expect(markFor("b4")).not.toBeNull();
});

it("G14: never on the passage the learner was restored to", async () => {
  TOPS.b4 = 900;
  openReader({ spanId: "b1" });
  await waitFor(() => expect(markFor("b4")).not.toBeNull());
  expect(markFor("b1")).toBeNull();
});

it("G14: skim mutes every mark; reading closely brings them back", async () => {
  TOPS.b4 = 900;
  openReader();
  await findMark("b1");
  const [modeSelect] = screen.getAllByRole("combobox");
  fireEvent.keyDown(modeSelect, { key: "Enter" });
  fireEvent.mouseDown(await screen.findByRole("option", { name: "skim quickly" }));
  await waitFor(() => expect(markFor("b1")).toBeNull());
  expect(markFor("b4")).toBeNull();
});

it("G14: a mark never animates and LearnLoop never moves focus to it", async () => {
  TOPS.b4 = 900;
  const elsewhere = document.createElement("button");
  document.body.appendChild(elsewhere);
  elsewhere.focus();
  openReader();
  const mark = await findMark("b1");
  expect(mark.style.animation ?? "").toBe("");
  expect(mark.style.transition ?? "").toBe("");
  expect(document.activeElement).toBe(elsewhere);
  elsewhere.remove();
});

it("Alt+↓ and Alt+↑ move between the marks in reading order", async () => {
  TOPS.b4 = 900;
  openReader();
  await findMark("b1");
  fireEvent.keyDown(window, { key: "ArrowDown", altKey: true });
  expect(document.activeElement).toBe(markFor("b1"));
  fireEvent.keyDown(document.activeElement as Element, { key: "ArrowDown", altKey: true });
  expect(document.activeElement).toBe(markFor("b4"));
  fireEvent.keyDown(document.activeElement as Element, { key: "ArrowUp", altKey: true });
  expect(document.activeElement).toBe(markFor("b1"));
});

it("Enter opens the popover; open shows the earlier work, the model's reading in its voice, and records the tap", async () => {
  TOPS.b4 = 900;
  openReader();
  const mark = await findMark("b1");
  fireEvent.click(mark);
  const popover = await screen.findByRole("group", { name: "this margin note" });
  fireEvent.click(within(popover).getByRole("button", { name: "open · what you worked on" }));
  expect(within(popover).getByText("You answered a question on this on 2 Oct.")).toBeTruthy();
  expect(within(popover).getByText(/the question: “Is f\(0.5\) = 2 a probability\?”/)).toBeTruthy();
  // The cited attempt itself: the learner's own answer, in the learner's voice (review F7).
  const learner = popover.querySelector("[data-voice='learner']");
  expect(learner?.textContent).toContain(ANSWER);
  expect(learner?.textContent).toContain("your answer");
  const voice = popover.querySelector("[data-voice='model']");
  expect(voice?.textContent).toContain(STATEMENT);
  expect(voice?.textContent).not.toContain(ANSWER);
  await waitFor(() => expect(api.readerCueAction).toHaveBeenCalledWith({ extractionId: view.extractionId, cueId: "cue_b1", action: "opened", text: null }));
  // Esc closes it and returns focus to the mark.
  fireEvent.keyDown(popover, { key: "Escape" });
  expect(screen.queryByRole("group", { name: "this margin note" })).toBeNull();
  expect(document.activeElement).toBe(mark);
});

it("not relevant… takes an optional why, says where it goes, and undo takes it back", async () => {
  TOPS.b4 = 900;
  openReader();
  fireEvent.click(await findMark("b1"));
  const popover = await screen.findByRole("group", { name: "this margin note" });
  fireEvent.click(within(popover).getByRole("button", { name: "not relevant…" }));
  expect(within(popover).getByText(/isn't read for gaps in your understanding/)).toBeTruthy();
  fireEvent.change(within(popover).getByRole("textbox", { name: "why? (optional)" }), { target: { value: "That was about variance." } });
  guide.plan = plan({ marks: [cue("b4", 0)] });
  fireEvent.click(within(popover).getByRole("button", { name: "send" }));
  await waitFor(() => expect(api.readerCueAction).toHaveBeenCalledWith({
    extractionId: view.extractionId, cueId: "cue_b1", action: "not_relevant", text: "That was about variance.",
  }));
  await waitFor(() => expect(markFor("b1")).toBeNull());
  expect(screen.getByText("Marked not relevant.")).toBeTruthy();
  guide.plan = plan();
  fireEvent.click(screen.getByRole("button", { name: "undo" }));
  await waitFor(() => expect(api.readerCueAction).toHaveBeenCalledWith({
    extractionId: view.extractionId, cueId: "cue_b1", action: "not_relevant_undone", text: null,
  }));
  await waitFor(() => expect(markFor("b1")).not.toBeNull());
});

it("fewer marks like this steps the density down a notch, remembered in vault config, with undo", async () => {
  TOPS.b4 = 900;
  openReader();
  fireEvent.click(await findMark("b1"));
  guide.plan = plan({ density: "fewer", marks: [cue("b1", 0)] });
  fireEvent.click(within(screen.getByRole("group", { name: "this margin note" })).getByRole("button", { name: "fewer marks like this" }));
  await waitFor(() => expect(api.readerSetCuePreferences).toHaveBeenCalledWith(expect.objectContaining({ density: "fewer", via: "fewer", sourceOff: null })));
  await waitFor(() => expect(markFor("b4")).toBeNull());
  expect(screen.getByText("Margin marks: fewer.")).toBeTruthy();
  expect(within(screen.getByRole("group", { name: "margin marks" })).getByRole("button", { name: "●fewer" })).toBeTruthy();
  guide.plan = plan();
  fireEvent.click(screen.getByRole("button", { name: "undo" }));
  await waitFor(() => expect(api.readerSetCuePreferences).toHaveBeenLastCalledWith(expect.objectContaining({ density: "normal", via: "undo" })));
  await waitFor(() => expect(markFor("b4")).not.toBeNull());
});

it("marks off for this book, and everywhere, from the mark itself, each undoable until the learner leaves", async () => {
  TOPS.b4 = 900;
  openReader();
  fireEvent.click(await findMark("b1"));
  guide.plan = plan({ sourceOff: true });
  fireEvent.click(within(screen.getByRole("group", { name: "this margin note" })).getByRole("button", { name: "marks off for this book" }));
  await waitFor(() => expect(api.readerSetCuePreferences).toHaveBeenCalledWith(expect.objectContaining({ sourceId: view.sourceId, sourceOff: true, via: "popover" })));
  await waitFor(() => expect(markFor("b1")).toBeNull());
  expect(screen.getByText("Margin marks are off for this book.", { selector: "[data-cue-receipt]" })).toBeTruthy();
  guide.plan = plan();
  fireEvent.click(screen.getByRole("button", { name: "undo" }));
  await waitFor(() => expect(api.readerSetCuePreferences).toHaveBeenLastCalledWith(expect.objectContaining({ sourceOff: false, via: "undo" })));
  await waitFor(() => expect(markFor("b1")).not.toBeNull());

  fireEvent.click(markFor("b1") as HTMLButtonElement);
  guide.plan = plan({ density: "off", marks: [] });
  fireEvent.click(within(screen.getByRole("group", { name: "this margin note" })).getByRole("button", { name: "marks off everywhere" }));
  await waitFor(() => expect(api.readerSetCuePreferences).toHaveBeenLastCalledWith(expect.objectContaining({ density: "off", via: "popover" })));
  await waitFor(() => expect(markFor("b1")).toBeNull());
  // The density control stays, so marks can come back from the footer.
  expect(within(screen.getByRole("group", { name: "margin marks" })).getByRole("button", { name: "●off" })).toBeTruthy();
});

it("check me finds one short question and the shell opens it, on your own, coming back to this passage", async () => {
  TOPS.b4 = 900;
  api.readerCueAction.mockImplementation(async (input: { cueId: string; action: string }) => ({
    cueId: input.cueId, action: input.action, eventId: "ev", verdict: "same", ledgerId: "l1",
    check: input.action === "check_me" ? { status: "found", practiceItemId: "pi_density_2", proposalId: "pp_1", prompt: "Compute P(0 ≤ X ≤ 0.5)." } : null,
  }));
  const onCheckMe = vi.fn();
  openReader({ onCheckMe });
  fireEvent.click(await findMark("b1"));
  fireEvent.click(within(screen.getByRole("group", { name: "this margin note" })).getByRole("button", { name: /^check me ·/ }));
  await waitFor(() => expect(onCheckMe).toHaveBeenCalledWith({
    practiceItemId: "pi_density_2", proposalId: "pp_1", spanId: "b1", card,
  }));
  expect(api.readerCueAction).toHaveBeenCalledWith(expect.objectContaining({ cueId: "cue_b1", action: "check_me" }));
});

it("check me says so plainly when nothing fits, and is absent when the shell cannot open an item", async () => {
  TOPS.b4 = 900;
  api.readerCueAction.mockImplementation(async (input: { cueId: string; action: string }) => ({
    cueId: input.cueId, action: input.action, eventId: "ev", verdict: "same", ledgerId: null,
    check: { status: "none", proposalId: "pp_2" },
  }));
  const onCheckMe = vi.fn();
  openReader({ onCheckMe });
  fireEvent.click(await findMark("b1"));
  const popover = screen.getByRole("group", { name: "this margin note" });
  fireEvent.click(within(popover).getByRole("button", { name: /^check me ·/ }));
  expect(await within(popover).findByText("Nothing in your practice fits this yet.")).toBeTruthy();
  expect(onCheckMe).not.toHaveBeenCalled();
  cleanup();
  openReader();
  fireEvent.click(await findMark("b1"));
  expect(within(screen.getByRole("group", { name: "this margin note" })).queryByRole("button", { name: /^check me/ })).toBeNull();
});

it("a mark counts once per visit when it comes into view, never because it was placed, with no learner-facing words", async () => {
  // Review F6: the funnel's "marks shown" is what the learner saw. The webview
  // reports a mark's visibility; jsdom has no layout, so this stands in for it.
  const observers: Array<{ callback: IntersectionObserverCallback; nodes: Element[] }> = [];
  vi.stubGlobal("IntersectionObserver", class {
    private entry: { callback: IntersectionObserverCallback; nodes: Element[] };
    constructor(callback: IntersectionObserverCallback) {
      this.entry = { callback, nodes: [] };
      observers.push(this.entry);
    }
    observe(node: Element) {
      this.entry.nodes.push(node);
    }
    unobserve(node: Element) {
      this.entry.nodes = this.entry.nodes.filter((entry) => entry !== node);
    }
    disconnect() {
      this.entry.nodes = [];
    }
  });
  const inView = (spanId: string, visible: boolean) => act(() => {
    for (const observer of observers) {
      for (const node of observer.nodes) {
        if (node.getAttribute("data-cue-span") !== spanId) continue;
        observer.callback(
          [{ isIntersecting: visible, intersectionRatio: visible ? 1 : 0, target: node } as unknown as IntersectionObserverEntry],
          {} as IntersectionObserver,
        );
      }
    }
  });
  const shownIds = () => {
    flushReaderActivity();
    return api.readerLogActivity.mock.calls
      .flatMap((call) => call[0].events as Array<{ event?: string; payload: Record<string, unknown> }>)
      .filter((event) => event.event === "cue_shown");
  };
  try {
    TOPS.b4 = 900;
    const { unmount } = openReader();
    await findMark("b1");
    await waitFor(() => expect(markFor("b4")).not.toBeNull());
    // Both marks are placed, but on opening only b1 is in the reading area.
    inView("b1", true);
    inView("b4", false);
    expect(shownIds().map((event) => event.payload.cue_id)).toEqual(["cue_b1"]);
    // Reading on brings b4 into view: counted once; b1 again adds nothing.
    inView("b4", true);
    inView("b1", true);
    inView("b4", true);
    unmount();
    const shown = shownIds();
    expect(shown.map((event) => event.payload.cue_id).sort()).toEqual(["cue_b1", "cue_b4"]);
    expect(shown[0].payload).toMatchObject({ element: "margin_mark", cue_kind: "revisit", density: "normal" });
    expect(JSON.stringify(shown)).not.toContain("Connects to");
  } finally {
    vi.unstubAllGlobals();
  }
});

it("discovery off: a sighting the webview buffered before the mark unmounted still counts, as in RW3a (F23)", async () => {
  // Codex verify F23: with discovery off the mark's observer is RW3a's, so a
  // visible entry delivered after skim unmounted the mark still records
  // cue_shown, exactly as before RW3b.
  const observers: Array<{ callback: IntersectionObserverCallback; nodes: Element[] }> = [];
  vi.stubGlobal("IntersectionObserver", class {
    private entry: { callback: IntersectionObserverCallback; nodes: Element[] };
    constructor(callback: IntersectionObserverCallback) {
      this.entry = { callback, nodes: [] };
      observers.push(this.entry);
    }
    // The nodes stay recorded after a disconnect: the browser's buffer.
    observe(node: Element) { this.entry.nodes.push(node); }
    unobserve() {}
    disconnect() {}
  });
  try {
    TOPS.b4 = 900;
    const { unmount } = openReader();
    await findMark("b1");
    const node = markFor("b1")!;
    const buffered = observers.filter((observer) => observer.nodes.includes(node));
    expect(buffered.length).toBeGreaterThan(0);
    // Skim unmounts the marks before the buffered entry is delivered.
    const [modeSelect] = screen.getAllByRole("combobox");
    fireEvent.keyDown(modeSelect, { key: "Enter" });
    fireEvent.mouseDown(await screen.findByRole("option", { name: "skim quickly" }));
    await waitFor(() => expect(markFor("b1")).toBeNull());
    act(() => {
      for (const observer of buffered) {
        observer.callback(
          [{ isIntersecting: true, intersectionRatio: 1, target: node } as unknown as IntersectionObserverEntry],
          {} as IntersectionObserver,
        );
      }
    });
    unmount();
    flushReaderActivity();
    const shown = api.readerLogActivity.mock.calls
      .flatMap((call) => call[0].events as Array<{ event?: string; payload: Record<string, unknown> }>)
      .filter((event) => event.event === "cue_shown");
    expect(shown.map((event) => event.payload.cue_id)).toEqual(["cue_b1"]);
  } finally {
    vi.unstubAllGlobals();
  }
});

it("a mark the learner never scrolled to is never counted shown", async () => {
  vi.stubGlobal("IntersectionObserver", class {
    observe() {}
    unobserve() {}
    disconnect() {}
  });
  try {
    TOPS.b4 = 900;
    const { unmount } = openReader();
    await findMark("b1");
    await waitFor(() => expect(markFor("b4")).not.toBeNull());
    unmount();
    flushReaderActivity();
    const events = api.readerLogActivity.mock.calls.flatMap((call) => call[0].events as Array<{ event?: string }>);
    expect(events.filter((event) => event.event === "cue_shown")).toEqual([]);
  } finally {
    vi.unstubAllGlobals();
  }
});

it("switched off (no cues in the plan): no marks and no density control", async () => {
  guide.plan = plan({ cues: false });
  openReader();
  await screen.findByText(view.blocks[1].markdown);
  await act(async () => {
    await Promise.resolve();
  });
  expect(document.querySelector("[data-cue-mark]")).toBeNull();
  expect(screen.queryByRole("group", { name: "margin marks" })).toBeNull();
});

it("a video transcript passage carries its mark like any source", async () => {
  const transcript: ReaderRenderViewDto = {
    ...readerRenderViewFixture,
    sourceId: "src_video",
    extractionId: "ext_video",
    blocks: [
      ["s1", "t=0.0-4.0", "A mixture picks a component, then samples from it."],
      ["s2", "t=4.0-9.0", "So the density is weighted by the chance of each component."],
    ].map(([spanId, locator, text]) => ({
      displayNodeId: `node-${spanId}`, spanId, blockType: "Caption", extractorBlockId: locator, markdown: text,
      sanitized: false, katexNodes: [], assets: [], health: { status: "ok", recommendedView: "derived", reasonFlags: [] },
    })),
  };
  const videoCard = { ...card, sourceId: "src_video", canonicalUri: "https://www.youtube.com/watch?v=hvjkcmzfix8" } as SourceLibraryCard;
  source.card = videoCard;
  api.readerRenderView.mockResolvedValue(transcript);
  api.readerWatchPlan.mockResolvedValue({ videoId: "hvjkcmzfix8", embedUrl: "https://www.youtube-nocookie.com/embed/x", pausePoints: [] });
  guide.plan = {
    ...plan({ marks: [{ ...cue("s2", 0), sectionId: "u1" }] }),
    sourceId: "src_video", extractionId: "ext_video",
    sections: [{ id: "u1", label: "Mixtures", startSpanId: "s1", endSpanId: "s2", spanIds: ["s1", "s2"], question: null, suggestedPassages: [] }],
  };
  render(<ReaderScreen initialSource={{ card: videoCard, spanId: null }} onError={vi.fn()} />);
  const mark = await findMark("s2");
  expect(mark.closest("[data-transcript-scroller]")).not.toBeNull();
});

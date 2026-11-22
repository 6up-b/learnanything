// A section's end finishes it on the phone too (algorithm tag mvp-0.63, docs/reviews/algorithm-mvp-0.63.md): the
// learner's own scrolling to the section's last passage queues the end in the outbox; once the host has it, its
// progress says whether the section is finished (from the tag it is), and only then the phone shows "Section finished"
// and draws the reading dose, once, with no press and no automatic move. "I've read this section" finishes it on the
// learner's word; "Read the next section" only moves; a quick check's "Done with this check" closes the check. And
// ledger UX-59: the reading count's observer has no root (the viewport), so the count is what was on screen.
import { vi } from "vitest";
import { act, answers, App, called, describe, expect, fireEvent, installFakeHost, it, render, screen, waitFor } from "../test/fakeHost";

installFakeHost();

class FakeObserver {
  static all: FakeObserver[] = [];
  static options: Array<IntersectionObserverInit | undefined> = [];
  readonly targets = new Set<HTMLElement>();
  constructor(readonly callback: IntersectionObserverCallback, options?: IntersectionObserverInit) {
    FakeObserver.all.push(this);
    FakeObserver.options.push(options);
  }
  observe(target: Element) {
    this.targets.add(target as HTMLElement);
  }
  unobserve(target: Element) {
    this.targets.delete(target as HTMLElement);
  }
  disconnect() {
    this.targets.clear();
    FakeObserver.all = FakeObserver.all.filter((one) => one !== this);
  }
  takeRecords() {
    return [];
  }
}

function screenShows(shown: string[]) {
  for (const observer of [...FakeObserver.all]) {
    const entries = [...observer.targets]
      .filter((target) => shown.includes(target.dataset.span ?? ""))
      .map((target) => ({ target, isIntersecting: true }) as unknown as IntersectionObserverEntry);
    if (entries.length) act(() => observer.callback(entries, observer as unknown as IntersectionObserver));
  }
}

function scrollByHand() {
  fireEvent.touchMove(window);
  fireEvent.scroll(document.querySelector(".book") as Element);
}

const guide = {
  version: 1, sourceId: "src1", extractionId: "ext1", personalized: false, selectionBasis: "x", goalContext: null,
  sections: [
    { id: "u1", label: "1 Vectors", startSpanId: "b0", endSpanId: "b2", spanIds: ["b0", "b1", "b2"], question: null, suggestedPassages: [] },
    { id: "u2", label: "2 Spans", startSpanId: "b3", endSpanId: "b4", spanIds: ["b3", "b4"], question: null, suggestedPassages: [] }
  ]
};
const block = (span: string, markdown: string) => ({
  displayNodeId: `node-${span}`, spanId: span, blockType: "Text", markdown, sanitized: false, katexNodes: [], assets: [],
  health: { status: "ok", recommendedView: "derived", reasonFlags: [] }, page: 0
});
const section = (sectionId: string, blocks: unknown[]) => ({
  version: 1, renderViewId: "rv1", extractionId: "ext1", revisionId: "rev1", sourceId: "src1", renderer: "r", rendererVersion: "1",
  contentHash: "c1", status: "ok", blocks, layers: {}, protection: { withheld: false, heldOutSpanIds: [], message: null },
  range: { sectionId, fromSpanId: null, toSpanId: null, blockCount: 3 }
});
const SECTIONS: Record<string, unknown> = {
  u1: section("u1", [block("b0", "# 1 Vectors"), block("b1", "Addition commutes."), block("b2", "Every space has a zero.")]),
  u2: section("u2", [block("b3", "# 2 Spans"), block("b4", "The span of a list.")])
};
const EXTRA_QUESTION = {
  version: 1, eligible: true, reason: null, drawId: "draw_q",
  offer: {
    drawId: "draw_q", variant: "extra_question", text: "One quick question on this?", why: "Offered at random, to learn how much of this helps you",
    content: { extractionId: "ext1", questionId: "aq_1" },
    question: { questionId: "aq_1", sectionId: "u1", prompt: "What does addition do with order?", expectedAnswer: "It commutes.", spanIds: ["b1"] }
  }
};
const WAIT = { timeout: 4000 };

type Progress = { sectionId: string; spansSeen?: number; reachedEnd?: boolean; completed?: boolean };
const progressSent = () => called("reader.mark_section_progress").map((call) => call.params as Progress);

/** The book, with the host finishing a section by its end when `endFinishes` (algorithm tag mvp-0.63) or not (below). */
async function openBook(endFinishes: boolean) {
  FakeObserver.all = [];
  FakeObserver.options = [];
  vi.stubGlobal("IntersectionObserver", FakeObserver);
  const finished = new Map<string, string>();
  Object.assign(answers, {
    get_source_library: { sources: [{ sourceId: "src1", title: "Linear Algebra Done Right", extractionId: "ext1", readerEnabled: true }] },
    "reader.guide_plan": guide,
    "reader.render_view": (call: { params: Record<string, unknown> }) => SECTIONS[String(call.params.sectionId)],
    "reader.get_progress": () => ({
      version: 1, extractionId: "ext1",
      sections: [...finished].map(([sectionId, cause]) => ({ extractionId: "ext1", sectionId, spansSeen: 3, spanCount: 3, revealedAt: null,
        completedAt: "2026-11-21T10:00:00Z", completionCause: cause, generationBatchId: null }))
    }),
    "reader.mark_section_progress": (call: { params: Record<string, unknown> }) => {
      const id = String(call.params.sectionId);
      if (!finished.has(id) && call.params.completed === true) finished.set(id, "learner_said");
      else if (!finished.has(id) && endFinishes && call.params.reachedEnd === true) finished.set(id, "reached_end");
      return { progress: {}, enqueuedGeneration: false, batchId: null };
    },
    "reader.log_activity": { recorded: 1 },
    "reader.dose_offer": EXTRA_QUESTION,
    "reader.dose_offer_event": { recorded: true },
    "reader.authored_question_action": { question: { questionId: "aq_1", status: "answered" } }
  });
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Read" }));
  fireEvent.click(await screen.findByRole("button", { name: /Linear Algebra Done Right/ }));
  await screen.findByText("Every space has a zero.");
}

async function readToTheEnd() {
  screenShows(["b0", "b1"]);
  scrollByHand();
  screenShows(["b2"]);
  await waitFor(() => expect(progressSent().some((one) => one.reachedEnd)).toBe(true), WAIT);
}

describe("the phone Reader's section end", () => {
  it("reading to the end finishes the section once the host has it: 'Section finished' and the dose, once, with no move", async () => {
    await openBook(true);
    await readToTheEnd();
    // Finished by the reading's end, and said so (UX-81).
    expect(await screen.findByText("Section finished: you read to the end.", undefined, WAIT)).toBeTruthy();
    expect(await screen.findByText("One quick question on this?")).toBeTruthy();
    expect(called("reader.dose_offer").map((call) => call.params.sectionId)).toEqual(["u1"]);
    // The end went alone: no completion was sent for it, and the phone stayed on the section.
    expect(progressSent().some((one) => one.completed)).toBe(false);
    expect(screen.getByText("Every space has a zero.")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "I’ve read this section" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Not now" }));
    // Navigation only; the dose is not drawn again.
    fireEvent.click(screen.getByRole("button", { name: "Read the next section" }));
    expect(await screen.findByText("The span of a list.")).toBeTruthy();
    expect(called("reader.dose_offer")).toHaveLength(1);
    expect(progressSent().some((one) => one.completed)).toBe(false);
  }, 15000);

  it("below the tag an end finishes nothing: nothing is shown finished; the learner's word finishes it and draws the dose once", async () => {
    await openBook(false);
    await readToTheEnd();
    await waitFor(() => expect(called("reader.get_progress").length).toBeGreaterThan(1), WAIT);
    expect(screen.queryByText("Section finished")).toBeNull();
    expect(called("reader.dose_offer")).toEqual([]);
    fireEvent.click(screen.getByRole("button", { name: "I’ve read this section" }));
    expect(await screen.findByText("Section finished")).toBeTruthy();
    await waitFor(() => expect(called("reader.dose_offer")).toHaveLength(1));
    await waitFor(() => expect(progressSent().filter((one) => one.completed)).toHaveLength(1));
  }, 15000);

  it("'Done with this check' closes the quick check: no completion of its own, no move", async () => {
    await openBook(false);
    fireEvent.click(screen.getByRole("button", { name: "I’ve read this section" }));
    fireEvent.click(await screen.findByRole("button", { name: "Try it" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Your answer" }), { target: { value: "Order doesn't matter." } });
    fireEvent.click(screen.getByRole("button", { name: "Compare with the source" }));
    fireEvent.click(await screen.findByRole("button", { name: "Done with this check" }));
    // The check closes; what the learner wrote and what it was compared with stay, folded (UX-79, below).
    expect(screen.queryByRole("group", { name: "Quick check" })).toBeNull();
    expect((screen.getByTestId("closed-check") as HTMLDetailsElement).open).toBe(false);
    expect(screen.getByText("Every space has a zero.")).toBeTruthy();
    await waitFor(() => expect(progressSent().filter((one) => one.completed)).toHaveLength(1));
  }, 15000);

  it("the last section's foot offers Back to Today, never a next section", async () => {
    await openBook(false);
    fireEvent.click(screen.getByRole("button", { name: "Read the next section" }));
    expect(await screen.findByText("The span of a list.")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Read the next section" })).toBeNull();
    expect(screen.getByRole("button", { name: "Back to Today" })).toBeTruthy();
  }, 15000);

  it("UX-59: the reading count's observer has no root, so the count is what was on screen, not what was laid out", async () => {
    await openBook(false);
    // Every observer the Reader made watches the viewport (no root): neither is rooted at the section's own box.
    expect(FakeObserver.options.length).toBeGreaterThanOrEqual(2);
    expect(FakeObserver.options.every((options) => !options?.root)).toBe(true);
    screenShows(["b0"]);
    await waitFor(() => expect(progressSent()).toHaveLength(1), WAIT);
    expect(progressSent()[0]).toMatchObject({ sectionId: "u1", spansSeen: 1, spanCount: 3 });
  }, 15000);
});

// The live walk sectionend-1 (2026-11-21), on the phone.
describe("the phone Reader's section end, after the walk", () => {
  it("UX-81: a tap meant for 'I've read this section' as the end finishes it does not move the reading on", async () => {
    await openBook(true);
    answers["reader.dose_offer"] = { version: 1, eligible: false, reason: "not_drawn", drawId: null, offer: null };
    await readToTheEnd();
    const ended = await screen.findByText("Section finished: you read to the end.", undefined, WAIT);
    expect(screen.queryByRole("button", { name: "I’ve read this section" })).toBeNull();
    // The tap arrives as the foot changes: it lands on "Read the next section", which lets it pass.
    fireEvent.click(screen.getByRole("button", { name: "Read the next section" }));
    expect(screen.getByText("Every space has a zero.")).toBeTruthy();
    expect(screen.queryByText("The span of a list.")).toBeNull();
    expect(ended.isConnected).toBe(true);
    // The learner's next press is theirs.
    fireEvent.click(screen.getByRole("button", { name: "Read the next section" }));
    expect(await screen.findByText("The span of a list.")).toBeTruthy();
  }, 15000);

  it("UX-79: closing the quick check keeps what the learner wrote and the intended answer, folded, one press to open", async () => {
    await openBook(false);
    fireEvent.click(screen.getByRole("button", { name: "I’ve read this section" }));
    fireEvent.click(await screen.findByRole("button", { name: "Try it" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Your answer" }), { target: { value: "Order doesn't matter." } });
    fireEvent.click(screen.getByRole("button", { name: "Compare with the source" }));
    fireEvent.click(await screen.findByRole("button", { name: "Done with this check" }));
    const kept = screen.getByTestId("closed-check") as HTMLDetailsElement;
    const summary = kept.querySelector("summary") as HTMLElement;
    expect(summary.textContent).toBe("Your answer to the quick check on “1 Vectors”");
    fireEvent.click(summary);
    expect(kept.textContent).toContain("Order doesn't matter.");
    expect(kept.textContent).toContain("It commutes.");
    expect(kept.textContent).toContain("What does addition do with order?");
    // Shown from what the phone holds: the answer was recorded once, when it was compared.
    expect(called("reader.authored_question_action")).toHaveLength(1);
    // Another section starts clean.
    fireEvent.click(screen.getByRole("button", { name: "Read the next section" }));
    expect(await screen.findByText("The span of a list.")).toBeTruthy();
    expect(screen.queryByTestId("closed-check")).toBeNull();
  }, 15000);
});

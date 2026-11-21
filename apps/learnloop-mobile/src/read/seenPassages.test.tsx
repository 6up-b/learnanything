// The phone's progress report names WHICH passages the learner's own reading had on screen (not only how many), and
// that a section's last passage was among them, through the outbox. Opening a section (Continue reading, Next, the
// section list) and a scroll the learner did not make observe nothing; a held-out passage is never read; finishing a
// section by its button sends the completion alone. Passages and ends are queued once each (the outbox and the host
// union them).
import { vi } from "vitest";
import { act, answers, App, called, describe, expect, fireEvent, installFakeHost, it, render, screen, waitFor } from "../test/fakeHost";

installFakeHost();

/** The browser's IntersectionObserver, driven by the test: `screenShows` says which passages are on screen. */
class FakeObserver {
  static all: FakeObserver[] = [];
  readonly targets = new Set<HTMLElement>();
  constructor(readonly callback: IntersectionObserverCallback) {
    FakeObserver.all.push(this);
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

function screenShows(shown: string[], gone: string[] = []) {
  for (const observer of [...FakeObserver.all]) {
    const entries = [...observer.targets]
      .filter((target) => shown.includes(target.dataset.span ?? "") || gone.includes(target.dataset.span ?? ""))
      .map((target) => ({ target, isIntersecting: shown.includes(target.dataset.span ?? "") }) as unknown as IntersectionObserverEntry);
    if (entries.length) act(() => observer.callback(entries, observer as unknown as IntersectionObserver));
  }
}

/** One delivery in which `span` came on screen and left again (a fast fling while the page was busy: the browser
 *  queues both changes and hands them over together). */
function screenFlashes(span: string) {
  for (const observer of [...FakeObserver.all]) {
    const target = [...observer.targets].find((one) => one.dataset.span === span);
    if (!target) continue;
    const entries = [true, false].map((isIntersecting) => ({ target, isIntersecting }) as unknown as IntersectionObserverEntry);
    act(() => observer.callback(entries, observer as unknown as IntersectionObserver));
  }
}

/** The learner's own finger moves the page: a touch, then the frame's scroll. */
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
const block = (span: string, markdown: string, extra: Record<string, unknown> = {}) => ({
  displayNodeId: `node-${span}`, spanId: span, blockType: "Text", markdown, sanitized: false, katexNodes: [], assets: [],
  health: { status: "ok", recommendedView: "derived", reasonFlags: [] }, page: 0, ...extra
});
const PROTECTION = { withheld: false, heldOutSpanIds: ["b4"], message: "held out" };
const section = (sectionId: string, blocks: unknown[]) => ({
  version: 1, renderViewId: "rv1", extractionId: "ext1", revisionId: "rev1", sourceId: "src1", renderer: "r", rendererVersion: "1",
  contentHash: "c1", status: "ok", blocks, layers: {}, protection: PROTECTION, range: { sectionId, fromSpanId: null, toSpanId: null, blockCount: 5 }
});
const SECTIONS: Record<string, unknown> = {
  u1: section("u1", [block("b0", "# 1 Vectors"), block("b1", "Addition commutes."), block("b2", "Every space has a zero.")]),
  u2: section("u2", [block("b3", "# 2 Spans"), block("b4", "", { withheld: true })])
};

type Progress = { sectionId: string; spansSeen?: number; seenSpanIds?: string[]; reachedEnd?: boolean; completed?: boolean };
const progressSent = () => called("reader.mark_section_progress").map((call) => call.params as Progress);
const passagesSent = (sectionId: string) => progressSent().filter((one) => one.sectionId === sectionId).flatMap((one) => one.seenSpanIds ?? []);
const WAIT = { timeout: 4000 };

async function openBook() {
  FakeObserver.all = [];
  vi.stubGlobal("IntersectionObserver", FakeObserver);
  Object.assign(answers, {
    get_source_library: { sources: [{ sourceId: "src1", title: "Linear Algebra Done Right", extractionId: "ext1", readerEnabled: true }] },
    "reader.guide_plan": guide,
    "reader.render_view": (call: { params: Record<string, unknown> }) => SECTIONS[String(call.params.sectionId)],
    "reader.get_progress": { version: 1, extractionId: "ext1", sections: [] },
    "reader.mark_section_progress": { progress: {}, enqueuedGeneration: false, batchId: null },
    "reader.log_activity": { recorded: 1 },
    "reader.dose_offer": { version: 1, eligible: false, reason: "switch_off", drawId: null, offer: null }
  });
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Read" }));
  fireEvent.click(await screen.findByRole("button", { name: /Linear Algebra Done Right/ }));
  await screen.findByText("Every space has a zero.");
}

describe("the phone Reader's seen passages", () => {
  it("opening a section observes nothing until the learner scrolls; then what is on screen is read, its end included", async () => {
    await openBook();
    screenShows(["b0", "b1"]);
    await waitFor(() => expect(progressSent()).toHaveLength(1), WAIT);
    // The count of what was laid out goes as before; no passage was read by the learner's hand yet.
    expect(progressSent()[0]).toEqual({ extractionId: "ext1", sectionId: "u1", spansSeen: 2, spanCount: 3 });
    scrollByHand();
    await waitFor(() => expect(passagesSent("u1")).toEqual(["b0", "b1"]), WAIT);
    screenShows(["b2"], ["b0"]);
    await waitFor(() => expect(passagesSent("u1")).toEqual(["b0", "b1", "b2"]), WAIT);
    const ends = progressSent().filter((one) => one.reachedEnd);
    expect(ends).toHaveLength(1);
    expect(ends[0]).toMatchObject({ sectionId: "u1", seenSpanIds: ["b2"], reachedEnd: true });
    expect(progressSent().some((one) => one.completed)).toBe(false);
  }, 15000);

  it("a scroll the learner did not make, opening the next section and finishing one observe nothing; a held-out passage is never read", async () => {
    await openBook();
    screenShows(["b0", "b1", "b2"]);
    fireEvent.scroll(document.querySelector(".book") as Element); // the page settling: no touch, wheel or key
    await waitFor(() => expect(progressSent()).toHaveLength(1), WAIT);
    expect(progressSent()[0].seenSpanIds).toBeUndefined();
    fireEvent.click(screen.getByRole("button", { name: "Next section" }));
    await screen.findByText(/held out for your exam/);
    await waitFor(() => expect(progressSent().some((one) => one.completed)).toBe(true), WAIT);
    // Finishing sends the completion, never the passages it did not observe.
    expect(progressSent().find((one) => one.completed)).toEqual({ extractionId: "ext1", sectionId: "u1", spansSeen: 3, spanCount: 3, completed: true });
    screenShows(["b3", "b4"]);
    scrollByHand();
    await waitFor(() => expect(passagesSent("u2")).toEqual(["b3"]), WAIT);
    // u2's last passage is held out: the phone never reads it, so it never reaches u2's end.
    expect(progressSent().some((one) => one.reachedEnd)).toBe(false);
    expect(passagesSent("u1")).toEqual([]);
  }, 15000);

  it("a passage that came on screen and left in one delivery, during the learner's own movement, was shown and is read", async () => {
    await openBook();
    screenShows(["b0", "b1"]);
    scrollByHand();
    await waitFor(() => expect(passagesSent("u1")).toEqual(["b0", "b1"]), WAIT);
    screenFlashes("b2");
    await waitFor(() => expect(passagesSent("u1")).toEqual(["b0", "b1", "b2"]), WAIT);
  }, 15000);
});

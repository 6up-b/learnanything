// The Reader with the original PDF's selection model (reader-pdf-selection):
// what a selection on the page becomes. The pane is a stand-in that keeps the
// props the Reader gives it, so a test can select as the pane would (its
// payload: exact nodes with code-point offsets) and read what the Reader
// draws (highlights from their placements on the open reading).
//
// * A selection's nodes reach the sidecar as the pane sent them (offsets
//   included), so a highlight anchors exactly and is drawn at once.
// * A selection on held-out material, or anywhere on a reading held back by
//   rule 4, offers no model action (no request, no remember-later preset, no
//   exercise import, no Ask); highlight, marks and notes stay.
// * Highlights come from the sidecar's placements: here and moved drawn,
//   flagged outlined, elsewhere not on the page.
// * A highlight removed from the page can be undone (the button or Ctrl+Z):
//   the undo names the delete it withdraws, and it is offered on the book it
//   was removed from only (Codex review F3, F4).
// * The Ask is held back by what it would send (Codex review F2): with no
//   selection on a reading held back by rule 4, after a selection is cleared,
//   on a held-out active passage.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { forwardRef, useImperativeHandle } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ReaderProtectionDto, ReaderRenderViewDto, SourceLibraryCard } from "../api/dto";
import { clear } from "../api/queryCache";
import type { PdfHighlight } from "../components/pdfSelection/highlights";
import { ReaderScreen } from "./ReaderScreen";

type PaneProps = {
  highlights?: PdfHighlight[];
  selection?: { spanId: string; nodes?: Array<{ spanId: string; start?: number; end?: number }> } | null;
  onTextSelection: (selection: unknown) => void;
  onHighlightRemove?: (id: string) => void;
  onHighlightOpen?: (id: string) => void;
  onSelectionCleared?: () => void;
};

const { invoke, pane } = vi.hoisted(() => ({
  invoke: vi.fn(),
  pane: { props: null as PaneProps | null },
}));
vi.mock("@tauri-apps/api/core", () => ({ invoke, convertFileSrc: (path: string) => path }));
vi.mock("../components/PdfReaderPane", () => ({
  PdfReaderPane: forwardRef(function FakePane(props: PaneProps, ref) {
    pane.props = props;
    useImperativeHandle(ref, () => ({ scrollToPage: () => undefined, scrollToSegment: () => undefined }));
    return <div data-testid="pdf-pane" />;
  }),
}));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));

const SOURCE_ID = "src_syn";
const EXTRACTION_ID = "ext_syn";
// A second book, with blocks of the same span ids (a span id is positional:
// s1 names another passage there).
const SOURCE_B = "src_b";
const EXTRACTION_B = "ext_b";
const TEXTS: Record<string, string> = {
  s1: "The quick brown fox jumps over the lazy dog.",
  s2: "Exercise 3. Show that every finite group of prime order is cyclic.",
};

const VIEW: ReaderRenderViewDto = {
  renderViewId: "rv_syn",
  extractionId: EXTRACTION_ID,
  revisionId: "rev_syn",
  sourceId: SOURCE_ID,
  renderer: "marker_markdown",
  rendererVersion: "1",
  contentHash: "sha256:syn",
  status: "ready",
  layers: {},
  blocks: Object.entries(TEXTS).map(([spanId, markdown]) => ({
    displayNodeId: `node-${spanId}`,
    spanId,
    blockType: "Text",
    markdown,
    sanitized: false,
    katexNodes: [],
    assets: [],
    health: { status: "ok", recommendedView: "derived", reasonFlags: [] },
  })),
};

const CARD: SourceLibraryCard = {
  sourceId: SOURCE_ID,
  title: "Synthetic Notes",
  acquisitionKind: "pdf",
  canonicalUri: null,
  workId: null,
  currentRevisionId: "rev_syn",
  revisionCount: 1,
  readiness: "ready",
  unitCount: 1,
  blockCount: 2,
  extractionStatus: "completed",
  suggestedRole: null,
  readerEnabled: true,
  updateAvailable: false,
};

const CARD_B: SourceLibraryCard = { ...CARD, sourceId: SOURCE_B, title: "Other Notes", currentRevisionId: "rev_b" };
const TEXTS_B: Record<string, string> = {
  s1: "A different first passage, in another book entirely.",
  s2: "Its second passage says something else again.",
};
const VIEW_B: ReaderRenderViewDto = {
  ...VIEW,
  renderViewId: "rv_b",
  extractionId: EXTRACTION_B,
  revisionId: "rev_b",
  sourceId: SOURCE_B,
  blocks: VIEW.blocks.map((block) => ({ ...block, markdown: TEXTS_B[block.spanId as string] })),
};

const HELD_OUT = "This passage is held out for your exam, so LearnLoop's models don't see it.";

const backend = {
  protection: { withheld: false, heldOutSpanIds: [], message: null } as ReaderProtectionDto,
  annotations: [] as unknown[],
  // The restore's answer: whether no other delete of it stands.
  restoreListed: true,
  // A delete that answers only when the test lets it.
  deleteGate: null as Promise<void> | null,
};

function head(id: string, placement: unknown, kind = "highlight", text = "") {
  return {
    annotation: { id },
    version: { annotationType: kind, learnerText: text },
    anchor: { status: "exact", extractionId: EXTRACTION_ID },
    segments: [{ spanId: "s1", exactQuote: "lazy dog", geometryJson: null }],
    placement,
  };
}

function sidecar(command: string, args?: { input?: Record<string, unknown> }): unknown {
  switch (command) {
    case "reader_prompt_contract":
      return {
        version: "1", context: "reader", readerEnabled: true, notSocraticByDefault: true,
        defaultAnswerMode: "answer_directly", answerModes: ["answer_directly"], mayReveal: [],
        manifestIncludes: [], manifestNeverIncludes: [], citations: "", exposureOnCommit: "",
      };
    case "get_source_library":
      return { version: 1, sources: [CARD, CARD_B] };
    case "reader_render_view":
      if (args?.input?.extractionId === SOURCE_B || args?.input?.extractionId === EXTRACTION_B) return { ...VIEW_B, protection: backend.protection };
      return { ...VIEW, protection: backend.protection };
    case "reader_guide_plan":
      return { version: 1, sourceId: SOURCE_ID, extractionId: EXTRACTION_ID, personalized: false, selectionBasis: "", goalContext: null, pendingDiagnosisAttemptIds: [], sections: [] };
    case "reader_get_progress":
      return { version: 1, extractionId: EXTRACTION_ID, sections: [] };
    case "reader_pdf_view":
      if (args?.input?.extractionId === EXTRACTION_B) {
        return {
          version: 1, available: true, fileName: "sha256-b", extractionId: EXTRACTION_B, sourceId: SOURCE_B, revisionId: "rev_b",
          blocks: Object.entries(TEXTS_B).map(([spanId, text], page) => ({ spanId, page, bbox: [72, 100, 540, 160], blockType: "Text", text })),
          pageSpans: [{ spanId: "s1", page: 0 }, { spanId: "s2", page: 1 }],
          protection: backend.protection,
        };
      }
      return {
        version: 1, available: true, fileName: "sha256-syn", extractionId: EXTRACTION_ID, sourceId: SOURCE_ID,
        revisionId: "rev_syn",
        blocks: Object.entries(TEXTS).map(([spanId, text], page) => ({ spanId, page, bbox: [72, 100, 540, 160], blockType: "Text", text })),
        pageSpans: [{ spanId: "s1", page: 0 }, { spanId: "s2", page: 1 }],
        protection: backend.protection,
      };
    case "reader_ask_history":
      return { version: 1, exchanges: [] };
    case "reader_source_annotations":
      return { version: 1, annotations: args?.input?.sourceId === SOURCE_B ? [] : backend.annotations };
    case "reader_source_requests":
      return { version: 1, requests: [] };
    case "reader_source_objects":
      return { version: 1, sourceObjects: [] };
    case "reader_proposal_inbox":
      return { version: 1, proposals: [] };
    case "reader_drain_outbox":
      return { version: 1, drained: [], failed: [] };
    case "reader_capture": {
      // As the sidecar does: anchored exactly from the nodes' own offsets,
      // then listed with its placement on the open reading.
      const nodes = (args?.input?.rawSelection as { nodes: Array<{ spanId: string; quote: string; start: number; end: number }> }).nodes;
      backend.annotations = [
        ...backend.annotations,
        head("ann_new", {
          state: "here",
          segments: nodes.map((node) => ({ spanId: node.spanId, codepointStart: node.start, codepointEnd: node.end, exactQuote: node.quote })),
          flagSpanId: null,
        }),
      ];
    }
      return { version: 1, annotationId: "ann_new", outboxId: "o1", interactionEventId: "e1", anchorStatus: "exact", captureKind: "annotation", deduplicated: false, receipt: "saved" };
    case "reader_delete_intent_annotation":
      return (backend.deleteGate ?? Promise.resolve()).then(() => ({ version: 1, eventId: "ev_del" }));
    case "reader_restore_annotation":
      return { version: 1, annotationId: "ann_here", restored: true, eventId: "ev_undo", listed: backend.restoreListed };
    case "reader_mark_section_progress":
      return { version: 1, progress: {}, enqueuedGeneration: false, batchId: null };
    case "reader_log_activity":
      return { version: 1 };
    default:
      throw { code: "not_mocked", message: `${command} is not mocked`, retryable: false };
  }
}

function memoryStorage(): Storage {
  const values = new Map<string, string>();
  return {
    get length() {
      return values.size;
    },
    clear: () => values.clear(),
    getItem: (key: string) => values.get(key) ?? null,
    key: (index: number) => Array.from(values.keys())[index] ?? null,
    removeItem: (key: string) => void values.delete(key),
    setItem: (key: string, value: string) => void values.set(key, String(value)),
  };
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "Date", "requestAnimationFrame", "cancelAnimationFrame"] });
  clear();
  pane.props = null;
  backend.protection = { withheld: false, heldOutSpanIds: [], message: null };
  backend.annotations = [];
  backend.restoreListed = true;
  backend.deleteGate = null;
  vi.stubGlobal("localStorage", memoryStorage());
  Element.prototype.scrollIntoView = vi.fn();
  invoke.mockReset().mockImplementation(async (command: string, args?: { input?: Record<string, unknown> }) => sidecar(command, args));
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

async function settle(ms = 0) {
  for (let i = 0; i < 8; i += 1) {
    await act(async () => {
      await vi.advanceTimersByTimeAsync(i === 0 ? ms : 20);
    });
  }
}

async function openBook(spanId: string | null = null) {
  render(<ReaderScreen onError={() => undefined} initialSource={{ card: CARD, spanId }} />);
  await settle(2_000);
  expect(pane.props).not.toBeNull();
}

/** Back to the library and into the other book. */
async function openOtherBook() {
  fireEvent.click(screen.getByRole("button", { name: "← Library" }));
  await settle();
  fireEvent.click(screen.getByText("Other Notes"));
  await settle(2_000);
}

function askTab() {
  fireEvent.click(screen.getAllByRole("button").find((button) => button.textContent?.trim().toLowerCase().startsWith("ask"))!);
}

/** What the pane hands over for the words `quote` of block `spanId`. */
function select(spanId: string, quote: string) {
  const text = TEXTS[spanId];
  const start = Array.from(text.slice(0, text.indexOf(quote))).length;
  const node = { spanId, quote, start, end: start + Array.from(quote).length };
  act(() => pane.props!.onTextSelection({ spanId, quote, nodes: [node], text: quote }));
  return node;
}

function calls(command: string): Array<Record<string, unknown>> {
  return invoke.mock.calls.filter(([name]) => name === command).map(([, args]) => (args as { input: Record<string, unknown> }).input);
}

describe("a selection on the original PDF", () => {
  it("anchors exactly: the capture sends the pane's nodes with their offsets, and the highlight is drawn at once", async () => {
    await openBook();
    const node = select("s1", "lazy dog");
    fireEvent.click(screen.getByRole("button", { name: "highlight" }));
    await settle();
    expect(calls("reader_capture")[0].rawSelection).toEqual({ nodes: [node] });
    const drawn = pane.props!.highlights!.find((highlight) => highlight.id === "ann_new");
    expect(drawn?.segments).toEqual([{ spanId: "s1", start: node.start, end: node.end }]);
    // The source's annotations are read with the open reading: placements.
    expect(calls("reader_source_annotations").every((input) => input.extractionId === EXTRACTION_ID)).toBe(true);
  });

  it("on held-out material offers no model action; highlight, marks and notes stay", async () => {
    backend.protection = { withheld: false, heldOutSpanIds: ["s2"], message: HELD_OUT };
    await openBook();
    select("s2", "every finite group");
    await settle();
    expect(document.querySelector("[data-capture-protected]")?.textContent).toContain("held out for your exam");
    for (const label of ["research this", "worked example", "test me later", "help me remember", "add exercise to practice"]) {
      expect(screen.queryByRole("button", { name: label })).toBeNull();
    }
    for (const label of ["highlight", "mark confusing", "not worth remembering"]) {
      expect(screen.getByRole("button", { name: label })).toBeTruthy();
    }
    // Ask offers no composer for it either.
    fireEvent.click(screen.getAllByRole("button").find((button) => button.textContent?.trim().toLowerCase().startsWith("ask"))!);
    await settle();
    expect(document.querySelector("[data-ask-protected]")?.textContent).toContain("held out for your exam");
    expect(screen.queryByPlaceholderText("ask about this passage…")).toBeNull();
    // A passage that is not held out offers them again.
    select("s1", "lazy dog");
    await settle();
    fireEvent.click(screen.getAllByRole("button").find((button) => button.textContent?.trim().toLowerCase().startsWith("notes"))!);
    await settle();
    expect(screen.getByRole("button", { name: "research this" })).toBeTruthy();
  });

  it("on a reading held back by rule 4 offers no model action anywhere", async () => {
    backend.protection = { withheld: true, heldOutSpanIds: [], message: "This book is held back until you mark its exam material." };
    await openBook();
    select("s1", "quick brown");
    await settle();
    expect(document.querySelector("[data-capture-protected]")?.textContent).toContain("held back until you mark");
    expect(screen.queryByRole("button", { name: "research this" })).toBeNull();
    expect(screen.queryByRole("button", { name: "add exercise to practice" })).toBeNull();
    expect(screen.getByRole("button", { name: "highlight" })).toBeTruthy();
  });
});

describe("highlights on the open reading", () => {
  it("are drawn from the sidecar's placements: here and moved on their words, flagged outlined, elsewhere not drawn", async () => {
    backend.annotations = [
      head("ann_here", { state: "here", segments: [{ spanId: "s1", codepointStart: 35, codepointEnd: 43, exactQuote: "lazy dog" }], flagSpanId: null }),
      head("ann_moved", { state: "moved", segments: [{ spanId: "s1", codepointStart: 4, codepointEnd: 15, exactQuote: "quick brown" }], flagSpanId: null }, "question", "why brown?"),
      head("ann_flag", { state: "flagged", segments: [], flagSpanId: "s2" }),
      head("ann_gone", { state: "elsewhere", segments: [], flagSpanId: null }),
    ];
    await openBook();
    const drawn = pane.props!.highlights!;
    expect(drawn.map((highlight) => [highlight.id, highlight.state])).toEqual([
      ["ann_here", "here"],
      ["ann_moved", "moved"],
      ["ann_flag", "flagged"],
    ]);
    expect(drawn[1]).toMatchObject({ kind: "question", note: "why brown?", segments: [{ spanId: "s1", start: 4, end: 15 }] });
    expect(drawn[2]).toMatchObject({ flagSpanId: "s2", segments: [] });
    // The rail says the same in words.
    fireEvent.click(screen.getAllByRole("button").find((button) => button.textContent?.trim().toLowerCase().startsWith("notes"))!);
    await settle();
    expect(document.querySelector("[data-placement='moved']")?.textContent).toBe("moved here when the book was read again");
  });

  it("a highlight removed from the page can be undone, by the button or by Ctrl+Z", async () => {
    backend.annotations = [
      head("ann_here", { state: "here", segments: [{ spanId: "s1", codepointStart: 35, codepointEnd: 43, exactQuote: "lazy dog" }], flagSpanId: null }),
    ];
    await openBook();
    backend.annotations = [];
    act(() => pane.props!.onHighlightRemove!("ann_here"));
    await settle();
    expect(calls("reader_delete_intent_annotation")).toEqual([{ annotationId: "ann_here" }]);
    expect(pane.props!.highlights).toEqual([]);
    expect(screen.getByRole("status").textContent).toContain("Highlight removed.");
    backend.annotations = [
      head("ann_here", { state: "here", segments: [{ spanId: "s1", codepointStart: 35, codepointEnd: 43, exactQuote: "lazy dog" }], flagSpanId: null }),
    ];
    fireEvent.click(screen.getByRole("button", { name: "undo" }));
    await settle();
    // The undo names the delete it withdraws (Codex review F3).
    expect(calls("reader_restore_annotation")).toEqual([{ annotationId: "ann_here", deleteEventId: "ev_del" }]);
    expect(pane.props!.highlights!.map((highlight) => highlight.id)).toEqual(["ann_here"]);
    expect(screen.queryByRole("status")).toBeNull();

    // Again, undone with Ctrl+Z this time; the offer leaves after a while.
    backend.annotations = [];
    act(() => pane.props!.onHighlightRemove!("ann_here"));
    await settle();
    fireEvent.keyDown(window, { key: "z", ctrlKey: true });
    await settle();
    expect(calls("reader_restore_annotation")).toHaveLength(2);
    backend.annotations = [];
    act(() => pane.props!.onHighlightRemove!("ann_here"));
    await settle(11_000);
    expect(screen.queryByRole("status")).toBeNull();
  });
});

describe("a removal's undo belongs to its book and its delete (Codex review F3, F4)", () => {
  const HERE = head("ann_here", { state: "here", segments: [{ spanId: "s1", codepointStart: 35, codepointEnd: 43, exactQuote: "lazy dog" }], flagSpanId: null });

  it("Ctrl+Z in another book opened within the undo's time does nothing there", async () => {
    backend.annotations = [HERE];
    await openBook();
    backend.annotations = [];
    act(() => pane.props!.onHighlightRemove!("ann_here"));
    await settle();
    expect(screen.getByRole("status").textContent).toContain("Highlight removed.");
    await openOtherBook();
    expect(screen.queryByRole("status")).toBeNull();
    fireEvent.keyDown(window, { key: "z", ctrlKey: true });
    await settle();
    expect(calls("reader_restore_annotation")).toEqual([]);
    // Book B's own (none): never book A's highlight on B's s1.
    expect(pane.props!.highlights).toEqual([]);
  });

  it("a delete that answers after another book opened leaves that book's list and offers no undo", async () => {
    backend.annotations = [HERE];
    await openBook();
    let release: () => void = () => undefined;
    backend.deleteGate = new Promise<void>((resolve) => {
      release = resolve;
    });
    backend.annotations = [];
    act(() => pane.props!.onHighlightRemove!("ann_here"));
    await settle();
    await openOtherBook();
    await act(async () => {
      release();
    });
    await settle();
    expect(screen.queryByRole("status")).toBeNull();
    expect(pane.props!.highlights).toEqual([]);
  });

  it("an undo while another delete of it stands does not draw it back", async () => {
    backend.annotations = [HERE];
    await openBook();
    backend.annotations = [];
    act(() => pane.props!.onHighlightRemove!("ann_here"));
    await settle();
    // Another window deleted it again meanwhile: the undo withdraws only this
    // removal's delete, and the sidecar says it stays hidden.
    backend.restoreListed = false;
    fireEvent.click(screen.getByRole("button", { name: "undo" }));
    await settle();
    expect(calls("reader_restore_annotation")).toEqual([{ annotationId: "ann_here", deleteEventId: "ev_del" }]);
    expect(pane.props!.highlights).toEqual([]);
  });
});

describe("the Ask, held back by what it would send (Codex review F2)", () => {
  const HELD_BACK = "This book is held back until you mark its exam material.";

  it("on a reading held back by rule 4: no composer after a selection is cleared", async () => {
    backend.protection = { withheld: true, heldOutSpanIds: [], message: HELD_BACK };
    await openBook();
    select("s1", "quick brown");
    await settle();
    act(() => pane.props!.onSelectionCleared!());
    await settle();
    askTab();
    await settle();
    expect(document.querySelector("[data-ask-protected]")?.textContent).toContain("held back until you mark");
    expect(screen.queryByPlaceholderText("ask about this passage…")).toBeNull();
  });

  it("on a reading held back by rule 4: no composer when it opens on a passage with no selection", async () => {
    backend.protection = { withheld: true, heldOutSpanIds: [], message: HELD_BACK };
    await openBook("s1");
    askTab();
    await settle();
    expect(document.querySelector("[data-ask-protected]")?.textContent).toContain("held back until you mark");
    expect(screen.queryByPlaceholderText("ask about this passage…")).toBeNull();
  });

  it("on held-out material: a held-out active passage offers no composer; another passage does", async () => {
    backend.protection = { withheld: false, heldOutSpanIds: ["s2"], message: HELD_OUT };
    await openBook("s2");
    askTab();
    await settle();
    expect(document.querySelector("[data-ask-protected]")?.textContent).toContain("held out for your exam");
    expect(screen.queryByPlaceholderText("ask about this passage…")).toBeNull();
    select("s1", "lazy dog");
    await settle();
    askTab();
    await settle();
    expect(screen.getByPlaceholderText("ask about this passage…")).toBeTruthy();
    expect(document.querySelector("[data-ask-protected]")).toBeNull();
  });
});

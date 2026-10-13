// The Reader's shell-facing part in UX Phase 1 (docs/specs/ux_learnloop_v1.md
// §6.3, §7.3, §10 items 1.4 and 1.10): a book still being prepared opens on its
// original at once; the picker no longer hides books that are not ready; the
// "reader is disabled" notice never flashes while settings load.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { forwardRef, useImperativeHandle } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { SourceLibraryCard } from "../api/dto";
import { clear } from "../api/queryCache";
import { readerRenderViewFixture } from "../fixtures/readerRenderView";
import { ReaderScreen } from "./ReaderScreen";

const { invoke, scrolls } = vi.hoisted(() => ({ invoke: vi.fn(), scrolls: [] as Array<[number, number | undefined]> }));
vi.mock("@tauri-apps/api/core", () => ({ invoke, convertFileSrc: (path: string) => path }));
vi.mock("../components/PdfReaderPane", () => ({
  PdfReaderPane: forwardRef(function MockPane(_props, ref) {
    useImperativeHandle(ref, () => ({
      scrollToSegment: () => undefined,
      scrollToPage: (page: number, offset?: number) => scrolls.push([page, offset])
    }));
    return (
      <div data-testid="pdf-pane">
        <div data-pdf-page="18" data-width-points="612" />
        <div data-pdf-page="19" data-width-points="612" />
      </div>
    );
  })
}));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));

const PREPARING: SourceLibraryCard = {
  sourceId: "src_new",
  title: "Probability",
  acquisitionKind: "pdf",
  canonicalUri: "/books/probability.pdf",
  workId: null,
  currentRevisionId: "rev_new",
  revisionCount: 1,
  readiness: "processing",
  unitCount: 0,
  blockCount: 0,
  extractionStatus: "running",
  suggestedRole: null,
  readerEnabled: true,
  updateAvailable: false,
  kindNoun: "book",
  subjectId: null,
  statusLine: { text: "Getting this book ready", tone: "working", action: null, details: null }
};

const backend = { contract: null as null | { readerEnabled: boolean }, calls: [] as string[], ready: false };
const READY: SourceLibraryCard = { ...PREPARING, readiness: "ready", unitCount: 4, blockCount: 9, extractionStatus: "completed", statusLine: null };

function sidecar(command: string): unknown {
  backend.calls.push(command);
  switch (command) {
    case "reader_prompt_contract":
      if (backend.contract === null) return new Promise(() => undefined); // still loading
      return {
        version: "1",
        context: "reader",
        readerEnabled: backend.contract.readerEnabled,
        notSocraticByDefault: true,
        defaultAnswerMode: "answer_directly",
        answerModes: ["answer_directly"],
        mayReveal: [],
        manifestIncludes: [],
        manifestNeverIncludes: [],
        citations: "",
        exposureOnCommit: ""
      };
    case "get_source_library":
      return { version: 1, sources: [backend.ready ? READY : PREPARING] };
    case "reader_pdf_view":
      if (backend.ready) {
        return {
          version: 1, available: true, preparing: false, fileName: "sha256-new", extractionId: readerRenderViewFixture.extractionId,
          sourceId: "src_new", revisionId: "rev_new",
          blocks: [
            { spanId: "s_p19_top", page: 19, bbox: [50, 40, 550, 200], blockType: "text" },
            { spanId: "s_p19_mid", page: 19, bbox: [50, 320, 550, 520], blockType: "text" }
          ]
        };
      }
      return { version: 1, available: true, preparing: true, fileName: "sha256-new", extractionId: null, sourceId: "src_new", revisionId: "rev_new", blocks: [] };
    case "reader_render_view":
      return { ...readerRenderViewFixture, sourceId: "src_new" };
    case "reader_search_sources":
      return { version: 1, hits: [] };
    default:
      throw { code: "not_mocked", message: `${command} is not mocked`, retryable: false };
  }
}

beforeEach(() => {
  vi.useFakeTimers();
  clear();
  backend.contract = { readerEnabled: true };
  backend.calls = [];
  backend.ready = false;
  scrolls.length = 0;
  invoke.mockReset().mockImplementation(async (command: string) => sidecar(command));
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.useRealTimers();
});

async function settle(ms = 0) {
  for (let i = 0; i < 6; i += 1) {
    await act(async () => {
      await vi.advanceTimersByTimeAsync(i === 0 ? ms : 0);
    });
  }
}

it("opens a book that is still being prepared on its original, without the full Reader's reads", async () => {
  render(<ReaderScreen onError={() => undefined} initialSource={{ card: PREPARING, spanId: null }} />);
  await settle();
  expect(screen.getByText(/Getting this book ready/)).toBeTruthy();
  expect(screen.getByTestId("pdf-pane")).toBeTruthy();
  expect(backend.calls).not.toContain("reader_render_view");
});

it("lists a book that is not ready yet on the picker, openable", async () => {
  render(<ReaderScreen onError={() => undefined} />);
  await settle();
  expect(screen.queryByText(/still getting ready/)).toBeNull();
  fireEvent.click(screen.getByText("Probability"));
  await settle();
  expect(screen.getByText(/Getting this book ready/)).toBeTruthy();
});

it("never flashes the disabled notice while settings are loading", async () => {
  backend.contract = null;
  render(<ReaderScreen onError={() => undefined} />);
  await settle();
  expect(screen.queryByText(/disabled/)).toBeNull();
  expect(screen.queryByText(/learnloop\.toml/)).toBeNull();
});

it("still says so when the reader really is off", async () => {
  backend.contract = { readerEnabled: false };
  render(<ReaderScreen onError={() => undefined} />);
  await settle();
  expect(screen.getByText(/disabled/)).toBeTruthy();
});

it("opens the full Reader where the learner had scrolled to in the original (review F8)", async () => {
  const stored = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => stored.get(key) ?? null,
    setItem: (key: string, value: string) => void stored.set(key, value),
    removeItem: (key: string) => void stored.delete(key)
  });
  render(<ReaderScreen onError={() => undefined} initialSource={{ card: PREPARING, spanId: null }} />);
  await settle();
  // Page 20 (index 19) is at the top of the view, 300 px of its 800 scrolled past.
  vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
    const page = (this as HTMLElement).dataset?.pdfPage;
    const top = page === "18" ? -900 : page === "19" ? -300 : 0;
    const height = page === undefined ? 700 : 800;
    return { top, bottom: top + height, height, width: 600, left: 0, right: 600, x: 0, y: top, toJSON: () => ({}) } as DOMRect;
  });
  backend.ready = true;
  await settle(3500);
  await settle();
  expect(backend.calls).toContain("reader_render_view");
  expect(scrolls).toEqual([[19, 0.375]]);
  // The passage there becomes the reading position, so the book reopens there too.
  expect(stored.get("learnloop.reader.position.src_new")).toBe("s_p19_mid");
  vi.unstubAllGlobals();
});

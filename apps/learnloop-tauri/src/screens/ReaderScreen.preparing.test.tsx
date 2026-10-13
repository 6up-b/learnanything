// The Reader's shell-facing part in UX Phase 1 (docs/specs/ux_learnloop_v1.md
// §6.3, §7.3, §10 items 1.4 and 1.10): a book still being prepared opens on its
// original at once; the picker no longer hides books that are not ready; the
// "reader is disabled" notice never flashes while settings load.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { forwardRef } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { SourceLibraryCard } from "../api/dto";
import { clear } from "../api/queryCache";
import { readerRenderViewFixture } from "../fixtures/readerRenderView";
import { ReaderScreen } from "./ReaderScreen";

const { invoke } = vi.hoisted(() => ({ invoke: vi.fn() }));
vi.mock("@tauri-apps/api/core", () => ({ invoke, convertFileSrc: (path: string) => path }));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: forwardRef(() => <div data-testid="pdf-pane" />) }));
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

const backend = { contract: null as null | { readerEnabled: boolean }, calls: [] as string[] };

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
      return { version: 1, sources: [PREPARING] };
    case "reader_pdf_view":
      return { version: 1, available: true, preparing: true, fileName: "sha256-new", extractionId: null, sourceId: "src_new", revisionId: "rev_new", blocks: [] };
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
  invoke.mockReset().mockImplementation(async (command: string) => sidecar(command));
});

afterEach(() => {
  cleanup();
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

// Keep the fixture import used: a ready source still opens the full Reader.
void readerRenderViewFixture;

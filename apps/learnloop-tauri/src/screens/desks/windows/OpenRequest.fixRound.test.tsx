// The Reader's retirement, review fix round: the app's open requests on the real desks (majors 8 and 9, ledger RDX-10
// and RDX-11). A book added while the desks were open is found (the desks read their library again before saying it is
// gone), a first library read that failed is tried again, and a slow open never takes the focus back from the book
// opened after it.
import { act, cleanup, fireEvent, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../../../app/algoConfig";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { invoke as fixtureInvoke } from "../../../fixtures/desks/fakeCore";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import type { SourceLibraryCard } from "../../../api/dto";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book, paper, video } = FIXTURE_SOURCES;
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };
const GONE = "isn't in your library any more";

type Server = ReturnType<typeof mountRealDesk>["server"];
const sourcesOnDesk = (server: Server) => server.state().desks[0].slots.flatMap((slot) => slot.windows)
  .map((window) => (window.content as { sourceId?: string } | null)?.sourceId).filter(Boolean);
const focusedSource = (server: Server) => {
  const desk = server.state().desks[0];
  const focus = desk.slots.flatMap((slot) => slot.windows).find((window) => window.windowId === desk.focusWindowId);
  return (focus?.content as { sourceId?: string } | null)?.sourceId ?? null;
};

beforeEach(() => {
  resetSidecar();
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("a book added while the desks are open opens from Add: the desks read their library again before calling it gone", async () => {
  let library: SourceLibraryCard[] = FIXTURE_LIBRARY.filter((card) => card.sourceId !== paper.sourceId);
  answers.set("get_source_library", () => ({ version: 1, sources: library }));
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  library = FIXTURE_LIBRARY; // Add finished: the app has the new card
  desk.rerender({ openRequest: { seq: 5, sourceId: paper.sourceId, spanId: null, reading: null } });
  await settleDesk(0, 20);
  await waitFor(() => expect(sourcesOnDesk(desk.server)).toContain(paper.sourceId));
  expect(document.body.textContent).not.toContain(GONE);
});

it("a first library read that failed is tried again for an open request, which then opens the book", async () => {
  let fail = true;
  answers.set("get_source_library", () => {
    if (fail) throw { code: "sidecar_unavailable", message: "restarting", retryable: true };
    return { version: 1, sources: FIXTURE_LIBRARY };
  });
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  fail = false;
  desk.rerender({ openRequest: { seq: 5, sourceId: paper.sourceId, spanId: null, reading: null } });
  await settleDesk(0, 20);
  await waitFor(() => expect(sourcesOnDesk(desk.server)).toContain(paper.sourceId));
});

it("a slow open never takes the focus back from the book opened after it", async () => {
  let release: () => void = () => undefined;
  const gate = new Promise<void>((resolve) => { release = resolve; });
  answers.set("reader_render_view", async (input) => {
    if (input.extractionId === paper.sourceId) await gate;
    return fixtureInvoke("reader_render_view", { input });
  });
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  desk.rerender({ openRequest: { seq: 5, sourceId: paper.sourceId, spanId: null, reading: null } });
  await settleDesk(0, 8);
  desk.rerender({ openRequest: { seq: 6, sourceId: video.sourceId, spanId: null, reading: null } });
  await settleDesk(0, 20);
  await waitFor(() => expect(focusedSource(desk.server)).toBe(video.sourceId));
  release();
  await settleDesk(0, 20);
  // Long enough for the desks' outbox to send whatever the late answer did (it sends after a short gathering).
  await new Promise((resolve) => setTimeout(resolve, 1200));
  expect(focusedSource(desk.server)).toBe(video.sourceId);
  expect(sourcesOnDesk(desk.server)).not.toContain(paper.sourceId);
});

// Major 10 (RDX-12): the app's check hand-off goes to one window of its book, not to every mounted copy of it.
it("a check chosen in the app opens once, though its book is open on two visited desks", async () => {
  setAlgoConfig({ workbench: { enabled: true, openSessionDays: 30 } });
  try {
    const desk = mountRealDesk();
    await settleDesk(0, 20);
    // Visit the attention desk (its own window of the paper mounts) and come back.
    await act(async () => { fireEvent.keyDown(window, { key: "j", code: "KeyJ", altKey: true }); });
    await settleDesk(0, 20);
    await act(async () => { fireEvent.keyDown(window, { key: "k", code: "KeyK", altKey: true }); });
    await settleDesk(0, 20);
    expect(document.querySelector('[data-desk-window="fx_w_paper2"]')).not.toBeNull();
    const check = {
      practiceItemId: "pi_check", spanId: `${paper.extractionId}_s1_1`, sourceId: paper.sourceId, stemMd: "Why scale the dot product?",
      schedulerCandidateId: null, planPresentationId: null,
      reading: { sourceId: paper.sourceId, revisionId: null, extractionId: paper.extractionId },
    };
    desk.rerender({ reader: { workbench: { practiceSessionId: "s1", checkMe: check as never, onCheckMeShown: vi.fn() } } as never });
    await settleDesk(0, 30);
    await waitFor(() => expect(inputsOf("workbench_open").length).toBeGreaterThan(0));
    await new Promise((resolve) => setTimeout(resolve, 300));
    expect(inputsOf("workbench_open")).toHaveLength(1);
  } finally {
    setAlgoConfig(undefined);
  }
});

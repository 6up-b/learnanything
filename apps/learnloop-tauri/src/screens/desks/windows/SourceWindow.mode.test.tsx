// How the learner reads a book on a desk, per window (the audit's §5, an orchestrator default the owner may change):
// skim quickly, read closely or mark for later, chosen in the window's source bar and stored where the old screen
// stored it (reader.set_mode, by reading); skimming mutes what it muted there: the recap card and the margin marks
// leave the window, and reading closely brings them back. The other window keeps its own way of reading.
import { cleanup, fireEvent, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderGuidePlanDto } from "../../../api/dto";
import { setAlgoConfig } from "../../../app/algoConfig";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_GUIDES, FIXTURE_SOURCES } from "../../../fixtures/desks/sources";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book, paper } = FIXTURE_SOURCES;
const windowOf = (windowId: string, source: { sourceId: string; extractionId: string }) => ({
  windowId, pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: source.sourceId, extractionId: source.extractionId, view: "render" },
});
const SESSION = { sessionId: "v1", extractionId: book.extractionId, visitIds: ["v1"], startedAt: "2026-11-22T20:00:00Z", endedAt: "2026-11-22T20:40:00Z", minutes: 40 };

function guideWithMark(extractionId: string): ReaderGuidePlanDto {
  const base = FIXTURE_GUIDES[extractionId];
  const spanId = base.sections[0].spanIds[1];
  const note = "Connects to something you worked on.";
  return {
    ...base, personalized: true,
    cues: { version: "rw3a-guide-cues-v1", density: "normal", budgetPerSection: 2, onePerViewport: true, sourceOff: false, withheld: {},
      marks: [{ cueId: `cue_${spanId}`, kind: "revisit", spanId, sectionId: base.sections[0].id, learningObjectId: "lo", learningObjectTitle: "Weights", targetId: "e1", rank: 0, sectionRank: 0,
        note, because: "Because: your answer", label: `Note on this paragraph: ${note}`, earlier: null }] },
  } as unknown as ReaderGuidePlanDto;
}

beforeEach(() => {
  resetSidecar();
  setAlgoConfig({ recap: { enabled: true, wrapUpEnabled: true } });
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("reader_set_mode", (input) => ({ mode: input.mode }));
  answers.set("reader_guide_plan", (input) => guideWithMark(String(input.extractionId)));
  answers.set("reader_recap", (input) => ({ version: 1, dismissed: false, recap: input.extractionId === book.extractionId ? {
    recapVersion: "r", extractionId: book.extractionId, session: SESSION, continueAt: null, stillOpen: [], unfinished: [],
    worthASecondLook: [], sinceLastTime: { demonstrated: [], checksRetired: [] },
  } : null }));
  answers.set("reader_recap_event", (input) => ({ version: 1, eventId: "ev", event: input.event }));
  answers.set("reader_wrap_up", () => ({ version: 1, wrapUpVersion: "w", available: false, extractionId: book.extractionId, session: null, resolved: [], stillOpen: [], worthReinforcing: [] }));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
});

const winEl = (windowId: string) => document.querySelector<HTMLElement>(`[data-desk-window="${windowId}"]`)!;

it("skimming is chosen in the window's source bar, stored by reading, and mutes that window's recap card and marks", async () => {
  mountRealDesk({ state: oneDesk([[windowOf("w_book", book) as never], [windowOf("w_paper", paper) as never]]) });
  await settleDesk(0, 20);
  await waitFor(() => expect(winEl("w_book").querySelector("[data-recap-card]")).not.toBeNull());
  await waitFor(() => expect(winEl("w_book").querySelector("[data-cue-span]")).not.toBeNull());
  await waitFor(() => expect(winEl("w_paper").querySelector("[data-cue-span]")).not.toBeNull());
  const bar = winEl("w_book").querySelector<HTMLElement>("[data-window-source-bar]")!;
  const select = within(bar).getByRole("combobox");
  fireEvent.keyDown(select, { key: "Enter" });
  fireEvent.mouseDown(await within(document.body).findByRole("option", { name: "skim quickly" }));
  await settleDesk(0, 4);
  expect(inputsOf("reader_set_mode")).toEqual([{ mode: "skim", extractionId: book.extractionId }]);
  await waitFor(() => expect(winEl("w_book").querySelector("[data-recap-card]")).toBeNull());
  expect(winEl("w_book").querySelector("[data-cue-span]")).toBeNull();
  // The other book reads as it did.
  expect(winEl("w_paper").querySelector("[data-cue-span]")).not.toBeNull();
  // Reading closely again brings them back.
  fireEvent.keyDown(within(bar).getByRole("combobox"), { key: "Enter" });
  fireEvent.mouseDown(await within(document.body).findByRole("option", { name: "read closely" }));
  await settleDesk(0, 4);
  await waitFor(() => expect(winEl("w_book").querySelector("[data-cue-span]")).not.toBeNull());
});

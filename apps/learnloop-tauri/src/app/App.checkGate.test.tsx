// A check open on the desks holds the whole app (spec §12.6; the RD7 review): no other place (Today, the old Reader,
// the library) shows while it is open; each gives way to a plain choice, back to the check or not now. The app reads
// whether one is open before it shows any place, and owns the check, so leaving the desks never drops it. The whole
// App, with the real desks over the fixture sidecar (fixtures/desks/realApp.tsx).
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { CheckCardDto } from "../api/dto";
import { clear } from "../api/queryCache";
import { appSidecar } from "../fixtures/desks/realApp";
import { answers, inputsOf, oneDesk, settleDesk } from "../fixtures/desks/realDesk";
import { FIXTURE_SOURCES } from "../fixtures/desks/sources";
import { resetProblemsForTests } from "../screens/desks/problem/problemPads";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("@tauri-apps/api/event", () => ({ listen: vi.fn(async () => () => undefined) }));
vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn(async () => null) }));
vi.mock("../components/useSourceFileDrop", () => ({ useSourceFileDrop: () => false, pickSourceFiles: async () => [] }));
vi.mock("../components/InboxStrip", () => ({ InboxStrip: () => null }));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

import { App } from "./App";

const { book } = FIXTURE_SOURCES;
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };
const SESSION = { version: 1, sessionId: "ps_1", startedAt: "2026-11-23T09:00:00Z", endedAt: null, energy: null, sleepQuality: null, availableMinutes: 25, notesMdPath: null, checkpoint: null };

function openCard(): CheckCardDto {
  return {
    administrationToken: "cad_open", commitmentId: "cm_1", itemRef: "pi_1", contractHash: "h", cold: true, state: "open",
    protection: { veilSetId: "v", method: "structural", groups: [], opened: [], veiled: [] },
    prompt: { prompt: "What is the gradient of the loss?" }, submissionId: null, eligibility: null, revision: 1,
  };
}

async function press(init: KeyboardEventInit) {
  await act(async () => {
    window.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, cancelable: true, ...init }));
  });
}

let open = true;

beforeEach(() => {
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  vi.stubGlobal("IntersectionObserver", class { observe() {} unobserve() {} disconnect() {} takeRecords() { return []; } });
  resetProblemsForTests();
  open = true;
  const app = appSidecar({ state: oneDesk([[BOOK_WINDOW as never]]), session: SESSION });
  vi.stubGlobal("localStorage", app.storage);
  // An administration was left open on the desks (a restart, or the learner went elsewhere mid-check).
  answers.set("check_open_inline", () => ({ administration: open ? openCard() : null }));
  answers.set("check_abandon_inline", () => {
    open = false;
    return {};
  });
  answers.set("check_protect_more", () => ({ veilAdditions: [], standing: [], revision: 1 }));
});
afterEach(() => {
  cleanup();
  clear();
  vi.unstubAllGlobals();
});

describe("a check open on the desks holds the app", () => {
  it("Today gives way to a plain choice; back to the check opens the desks with its card", async () => {
    render(<App />);
    await screen.findByRole("navigation", { name: "Places" });
    const gate = await screen.findByRole("dialog", { name: "a check is open" });
    expect(gate.textContent).toContain("A check is open on your desks");
    expect(document.querySelector("[data-testid='today-place'], .today-plan")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "back to the check" }));
    await settleDesk(0, 20);
    await waitFor(() => expect(document.querySelector("[data-check-card]")?.textContent).toContain("What is the gradient of the loss?"));
  });

  it("from the desks, the old Reader and Today give way to the same choice; not now closes the check and the place shows", async () => {
    render(<App />);
    await screen.findByRole("navigation", { name: "Places" });
    fireEvent.click(await screen.findByRole("button", { name: "back to the check" }));
    await settleDesk(0, 20);
    await waitFor(() => expect(document.querySelector("[data-check-card]")).toBeTruthy());
    // The desks' "old Reader": the old Reader would show the book with nothing veiled.
    fireEvent.click(screen.getByRole("button", { name: "old Reader" }));
    await screen.findByRole("dialog", { name: "a check is open" });
    expect(document.querySelector(`[data-span-id="${book.extractionId}_s1_1"]`)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "back to the check" }));
    await settleDesk(0, 20);
    await waitFor(() => expect(document.querySelector("[data-check-card]")).toBeTruthy());
    // Today by its key.
    await press({ key: "1", altKey: true });
    await screen.findByRole("dialog", { name: "a check is open" });
    fireEvent.click(screen.getByRole("button", { name: "not now" }));
    await waitFor(() => expect(inputsOf("check_abandon_inline")).toHaveLength(1));
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "a check is open" })).toBeNull());
  });

  it("before the app knows whether a check is open it shows no place; a failed read offers to read again", async () => {
    let fail = true;
    answers.set("check_open_inline", () => {
      if (fail) throw { code: "internal", message: "sidecar down" };
      return { administration: null };
    });
    render(<App />);
    await screen.findByRole("navigation", { name: "Places" });
    await waitFor(() => expect(document.querySelector('[data-check-gate="failed"]')).toBeTruthy());
    fail = false;
    fireEvent.click(screen.getByRole("button", { name: "try again" }));
    await waitFor(() => expect(document.querySelector("[data-check-gate]")).toBeNull());
  });
});

// Pen mode on the desks (spec §10.10, §5.4): alt+p and the ✎ chip, "simulate pen", the footer's pen hints, and a
// window's pen layer saving ink through the client's one write sequence.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { InkSaveInput, SourceLibraryCard } from "../../../api/dto";
import { FixtureDeskServer } from "../../../fixtures/desks/workspace";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import { DeskShell, type DeskTransport } from "../DeskShell";
import { usePenHost, type PenHost } from "./host";

vi.mock("../../../api/client", () => ({ api: {} }));
vi.mock("../windows/SourceWindow", () => ({ SourceWindow: () => null }));
vi.mock("../windows/PanelWindow", () => ({ PANEL_TITLES: { guide: "Guide", notes: "Notes", path: "Reading path", library: "Library" }, LibraryPanel: () => null, PathPanel: () => null, RailHostPanel: () => null }));

let seen: PenHost | null = null;
function Pane() {
  seen = usePenHost();
  return null;
}

function transportFor(server: FixtureDeskServer, library: SourceLibraryCard[] = FIXTURE_LIBRARY) {
  const inks: InkSaveInput[] = [];
  const transport: DeskTransport & { inks: InkSaveInput[] } = {
    inks,
    state: async () => server.state(),
    apply: async (input) => server.apply(input),
    applyInk: async (input) => {
      inks.push(input);
      return { version: 1, appliedSeq: input.seq, inkId: input.inkId, results: [{ status: "ok", duplicate: false }] };
    },
    library: async () => library,
    resolveExtraction: async (sourceId: string) => Object.values(FIXTURE_SOURCES).find((source) => source.sourceId === sourceId)?.extractionId ?? sourceId,
  };
  return transport;
}

let n = 0;
function mount() {
  const server = new FixtureDeskServer();
  const transport = transportFor(server);
  render(
    <DeskShell vaultKey={`vault-${Math.random()}`} onError={vi.fn()} transport={transport} renderPane={() => <Pane />}
      initialViewport={{ width: 1600, height: 960 }} mintId={(prefix) => `${prefix}_${++n}`} />,
  );
  return { server, transport };
}

async function flush() {
  await act(async () => {
    vi.advanceTimersByTime(300);
    await Promise.resolve();
  });
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

function altP() {
  act(() => {
    fireEvent.keyDown(window, { key: "Alt", code: "AltLeft", altKey: true });
    fireEvent.keyDown(window, { key: "π", code: "KeyP", altKey: true });
    fireEvent.keyUp(window, { key: "π", code: "KeyP", altKey: true });
    fireEvent.keyUp(window, { key: "Alt", code: "AltLeft" });
  });
}

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  const values = new Map<string, string>();
  vi.stubGlobal("localStorage", { getItem: (k: string) => values.get(k) ?? null, setItem: (k: string, v: string) => void values.set(k, v), removeItem: (k: string) => void values.delete(k), clear: () => values.clear() });
  seen = null;
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("pen mode", () => {
  it("alt+p and the ✎ chip turn it on and off; the footer shows the pen's hints while it is on", async () => {
    mount();
    await flush();
    const chip = screen.getByTitle("alt+p · pen mode");
    expect(chip.textContent).toBe("✎ pen off");
    expect(document.querySelector(".desk-shell.pen-mode")).toBeNull();
    altP();
    expect(chip.textContent).toBe("✎ pen on");
    expect(document.querySelector(".desk-shell.pen-mode")).not.toBeNull();
    expect(screen.getByText(/pen: underline · bracket · circle · scribble · strike/)).toBeTruthy();
    expect(seen?.on).toBe(true);
    fireEvent.click(chip);
    expect(chip.textContent).toBe("✎ pen off");
    expect(screen.queryByText(/pen: underline/)).toBeNull();
  });

  it("simulate pen turns pen mode on and lets the mouse draw", async () => {
    mount();
    await flush();
    fireEvent.click(screen.getByTitle("draw with the mouse as if it were a pen"));
    expect(seen?.simulate).toBe(true);
    expect(seen?.on).toBe(true);
  });

  it("a window's ink goes out in the client's one sequence, after the desk batches before it", async () => {
    const { transport } = mount();
    await flush();
    act(() => seen!.saveInk({ owner: { annotationId: "ann_1" }, inkId: "ink_1", strokes: [{ strokeId: "s1", points: [[1, 2, 0, 0.5, 0, 0]] }], pointerMeta: { pointerType: "pen" } }));
    expect(await seen!.settled()).toBe("saved");
    expect(transport.inks).toHaveLength(1);
    expect(transport.inks[0]).toMatchObject({ inkId: "ink_1", owner: { annotationId: "ann_1" } });
    expect(transport.inks[0].seq).toBeGreaterThanOrEqual(1);
    expect(transport.inks[0].clientId).toBeTruthy();
  });
});

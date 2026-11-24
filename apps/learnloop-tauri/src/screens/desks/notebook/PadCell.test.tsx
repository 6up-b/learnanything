// A marimo cell in a pad: its header and state, its code edited in place, ⇧↵ starting the pad's kernel (the framed
// group under the last cell) or running an edit in the live kernel.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { PadBlockDto } from "../../../api/dto";
import { PadsHostContext, type PadsHost } from "../pads/host";
import { PadCell } from "./PadCell";
import { notePadSession, padNotebookKey, resetPadNotebooksForTests } from "./padNotebooks";

const api = vi.hoisted(() => ({ notebookRunCells: vi.fn(), notebookStatus: vi.fn(), notebookOpen: vi.fn() }));
vi.mock("../../../api/client", () => ({ api }));

function block(blockId: string, bodyMd: string, provenance: PadBlockDto["provenance"] = "learner"): PadBlockDto {
  return { blockId, headVersionId: `v_${blockId}`, kind: "cell", bodyMd, payload: {}, provenance, positionKey: blockId, day: null,
    createdAt: "2026-11-23T00:00:00Z", updatedAt: "2026-11-23T00:00:00Z", submissions: [] };
}

const host = { store: { settled: vi.fn(async () => "saved") } } as unknown as PadsHost;
const blocks = [block("a", "x = 2"), block("b", "y = x * 3\ny", "tutor")];

function Cells({ onCommit = vi.fn() }: { onCommit?: (code: string) => void }) {
  return (
    <PadsHostContext.Provider value={host}>
      {blocks.map((each) => <PadCell key={each.blockId} padId="p1" block={each} blocks={blocks} editable onCommit={onCommit} />)}
    </PadsHostContext.Provider>
  );
}

beforeEach(() => {
  resetPadNotebooksForTests();
  api.notebookOpen.mockResolvedValue({ version: 1, sessionId: "nbs_1", owner: "pad:p1", state: "starting", stopReason: null, error: null,
    restarts: 0, framesAttached: 0, cells: [], startSeconds: [], frameUrl: "http://127.0.0.1:40123/s/x/", memoryBytes: null,
    padCells: { a: "c_a", b: "c_b" } });
  api.notebookStatus.mockResolvedValue({ version: 1, sessionId: "nbs_1", owner: "pad:p1", state: "starting", stopReason: null, error: null,
    restarts: 0, framesAttached: 0, cells: [], startSeconds: [], frameUrl: "http://127.0.0.1:40123/s/x/", memoryBytes: null });
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

it("shows each cell's header and code, the tutor's marked, and no kernel until ⇧↵", () => {
  render(<Cells />);
  expect(screen.getAllByText(/Python cell · ⇧↵/)).toHaveLength(2);
  expect(screen.getByText(/the tutor's/)).toBeTruthy();
  expect(screen.getAllByText("Ready to run")).toHaveLength(2);
  expect(document.querySelector("[data-cell-group]")).toBeNull();
});

it("⇧↵ commits the edit, waits for the pad's writes, and starts the pad's kernel under its last cell", async () => {
  const onCommit = vi.fn();
  render(<Cells onCommit={onCommit} />);
  fireEvent.click(screen.getByText("x = 2"));
  const area = screen.getByLabelText("edit this cell's code");
  fireEvent.change(area, { target: { value: "x = 5" } });
  await act(async () => {
    fireEvent.keyDown(area, { key: "Enter", shiftKey: true });
    await Promise.resolve();
    await Promise.resolve();
  });
  expect(onCommit).toHaveBeenCalledWith("x = 5");
  expect(host.store.settled).toHaveBeenCalled();
  const groups = document.querySelectorAll("[data-cell-group]");
  expect(groups).toHaveLength(1);
  expect(groups[0].closest("[data-cell-block]")?.getAttribute("data-cell-block")).toBe("b");
  await act(async () => {
    await Promise.resolve();
  });
  expect(api.notebookOpen).toHaveBeenCalledWith({ owner: "pad:p1", view: "app" });
});

it("with the kernel running, ⇧↵ runs the cell's code in it under the cell's name", async () => {
  render(<Cells />);
  await act(async () => {
    fireEvent.click(screen.getAllByLabelText("Run code")[0]);
    await Promise.resolve();
  });
  const opened = await api.notebookOpen();
  act(() => notePadSession(padNotebookKey("", "p1"), { ...opened, state: "ready" }));
  api.notebookRunCells.mockResolvedValue({ version: 1, sessionId: "nbs_1", ran: ["c_b"] });
  await act(async () => {
    fireEvent.click(screen.getAllByLabelText("Run code")[1]);
    await Promise.resolve();
  });
  expect(api.notebookRunCells).toHaveBeenCalledWith({ sessionId: "nbs_1", cells: [{ name: "c_b", code: "y = x * 3\ny" }] });
  expect(screen.getAllByText("running…").length).toBeGreaterThan(0);
});

it("escape puts the code back without writing it", () => {
  const onCommit = vi.fn();
  render(<Cells onCommit={onCommit} />);
  fireEvent.click(screen.getByText("x = 2"));
  const area = screen.getByLabelText("edit this cell's code");
  fireEvent.change(area, { target: { value: "x = 9" } });
  fireEvent.keyDown(area, { key: "Escape" });
  expect(onCommit).not.toHaveBeenCalled();
  expect(screen.getByText("x = 2")).toBeTruthy();
});

it("a pad of the same id in another vault starts nothing of this vault's kernel", async () => {
  const other = { store: { settled: vi.fn(async () => "saved"), clientId: "client-vault-b" } } as unknown as PadsHost;
  const mine = { store: { settled: vi.fn(async () => "saved"), clientId: "client-vault-a" } } as unknown as PadsHost;
  const view = render(
    <PadsHostContext.Provider value={mine}>
      <PadCell padId="p1" block={blocks[0]} blocks={blocks} editable onCommit={vi.fn()} />
    </PadsHostContext.Provider>,
  );
  await act(async () => {
    fireEvent.click(screen.getByLabelText("Run code"));
    await Promise.resolve();
  });
  view.unmount();
  render(
    <PadsHostContext.Provider value={other}>
      <PadCell padId="p1" block={blocks[0]} blocks={blocks} editable onCommit={vi.fn()} />
    </PadsHostContext.Provider>,
  );
  expect(screen.getByText("Ready to run")).toBeTruthy();
});

// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { PassagePromotedDto, PromotedJobDto, PromotedRowDto } from "../../../api/dto";
import { Poller } from "../../../api/poller";
import { ContextMenu, type PromotedApi } from "./ContextMenu";
import type { MenuRow } from "./model";

afterEach(cleanup);

const row = (rowId: string, extra: Partial<PromotedRowDto> = {}): PromotedRowDto => ({
  rowId, kind: "question", glyph: "?", label: `row ${rowId}`, reason: `why ${rowId}`, action: { verb: "open" }, learnerAt: null,
  checked: true, judgeRank: 0, basis: "union", extra: {}, ...extra,
} as unknown as PromotedRowDto);

function promotedApi(first: PassagePromotedDto, jobs: PromotedJobDto[] = []) {
  const labels: Array<[string, string]> = [];
  const cancelled: string[] = [];
  const api: PromotedApi = {
    passagePromoted: vi.fn(async () => first),
    passagePromotedJob: vi.fn(async () => jobs.shift() ?? { status: "running", done: false, rows: [], error: null } as unknown as PromotedJobDto),
    passagePromotedCancel: vi.fn(async ({ jobId }) => {
      cancelled.push(jobId);
      return { status: "cancelled", done: true, rows: [], error: null } as unknown as PromotedJobDto;
    }),
    label: (rowId, label) => labels.push([rowId, label]),
  };
  return { api, labels, cancelled };
}

const verbs = (runs: Record<string, () => void> = {}): MenuRow[] => [
  { id: "ask", glyph: "?", label: "Ask", key: "a", section: "verb", run: runs.ask },
  { id: "note", glyph: "›", label: "Note in margin", key: "n", section: "verb", run: runs.note },
  { id: "append", glyph: "⤓", label: "Append to “running”  ▸", key: "w", section: "verb", submenu: true },
  { id: "marimo", glyph: "◆", label: "marimo cell · arrives with notebooks", section: "insert", disabled: true },
  { id: "knows", glyph: "i", label: "What this knows", key: "i", section: "verb", aid: true, run: runs.knows },
];

const promoted = (rows: PromotedRowDto[], pendingJob: { jobId: string } | null = null): PassagePromotedDto =>
  ({ objectKey: "k", rows, cap: 4, pendingJob, paid: false }) as unknown as PassagePromotedDto;

describe("the context menu", () => {
  it("shows the cheap promoted rows at once, then the judged rows when the job on the poller is done", async () => {
    const poller = new Poller({ setInterval: () => 1, clearInterval: () => undefined });
    const { api } = promotedApi(promoted([row("r1")], { jobId: "j1" }), [
      { status: "done", done: true, rows: [row("r1"), row("r2", { checked: false, reason: "treats the same idea" })], error: null } as unknown as PromotedJobDto,
    ]);
    render(<ContextMenu header="a passage · “words”" rows={verbs()} at={{ x: 100, y: 100 }} object={{ objectKind: "passage", extractionId: "e", spanId: "s" }} promoted={api} poller={poller} owner="w1" onClose={() => undefined} />);
    await screen.findByText("row r1");
    expect(screen.getByText(/looking for more/)).toBeTruthy();
    expect(api.passagePromoted).toHaveBeenCalledWith({ objectKind: "passage", extractionId: "e", spanId: "s" });
    await act(async () => {
      await poller.tick();
    });
    await screen.findByText("row r2");
    expect(screen.getByText("treats the same idea · found by search, not checked")).toBeTruthy();
    expect(screen.queryByText(/looking for more/)).toBeNull();
  });

  it("cancels the judged job when the menu closes before it is done", async () => {
    const poller = new Poller({ setInterval: () => 1, clearInterval: () => undefined });
    const { api, cancelled } = promotedApi(promoted([], { jobId: "j9" }));
    const view = render(<ContextMenu header="h" rows={verbs()} at={{ x: 0, y: 0 }} object={{ objectKind: "passage", extractionId: "e", spanId: "s" }} promoted={api} poller={poller} onClose={() => undefined} />);
    await screen.findByText(/looking for more/);
    view.unmount();
    await waitFor(() => expect(cancelled).toEqual(["j9"]));
  });

  it("a parent's new object for the same calls neither asks again nor cancels the judged job", async () => {
    const poller = new Poller({ setInterval: () => 1, clearInterval: () => undefined });
    const { api, cancelled } = promotedApi(promoted([row("r1")], { jobId: "j2" }));
    const ui = () => <ContextMenu header="h" rows={verbs()} at={{ x: 0, y: 0 }} object={{ objectKind: "passage", extractionId: "e", spanId: "s" }} promoted={{ ...api }} poller={poller} onClose={() => undefined} />;
    const view = render(ui());
    await screen.findByText("row r1");
    view.rerender(ui());
    view.rerender(ui());
    await act(async () => {
      await Promise.resolve();
    });
    expect(api.passagePromoted).toHaveBeenCalledTimes(1);
    expect(cancelled).toEqual([]);
  });

  it("labels a promoted row opened, dismissed or not this by its row id; a dismissed row leaves the menu", async () => {
    const onPromoted = vi.fn();
    const onClose = vi.fn();
    const { api, labels } = promotedApi(promoted([row("r1"), row("r2")]));
    render(<ContextMenu header="h" rows={verbs()} at={{ x: 0, y: 0 }} object={{ objectKind: "passage", extractionId: "e", spanId: "s" }} promoted={api} onPromoted={onPromoted} onClose={onClose} />);
    const first = (await screen.findByText("row r1")).closest("button") as HTMLElement;
    fireEvent.click(within(first).getByText("not this"));
    expect(labels).toEqual([["r1", "not_this"]]);
    expect(screen.queryByText("row r1")).toBeNull();
    const second = screen.getByText("row r2").closest("button") as HTMLElement;
    fireEvent.click(within(second).getByLabelText("dismiss"));
    expect(labels).toEqual([["r1", "not_this"], ["r2", "dismiss"]]);
    expect(screen.queryByText("row r2")).toBeNull();
    expect(onPromoted).not.toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
  });

  it("opening a promoted row labels it opened, closes the menu and runs its action", async () => {
    const onPromoted = vi.fn();
    const onClose = vi.fn();
    const { api, labels } = promotedApi(promoted([row("r1")]));
    render(<ContextMenu header="h" rows={verbs()} at={{ x: 0, y: 0 }} object={{ objectKind: "passage", extractionId: "e", spanId: "s" }} promoted={api} onPromoted={onPromoted} onClose={onClose} />);
    fireEvent.click(await screen.findByText("row r1"));
    expect(labels).toEqual([["r1", "opened"]]);
    expect(onClose).toHaveBeenCalled();
    expect(onPromoted).toHaveBeenCalledWith(expect.objectContaining({ rowId: "r1" }));
  });

  it("moves with j/k and the arrows, runs with enter or a verb's letter, skips the disabled row, closes on escape and outside", () => {
    const runs = { ask: vi.fn(), note: vi.fn(), knows: vi.fn() };
    const onClose = vi.fn();
    render(<ContextMenu header="h" rows={verbs(runs)} at={{ x: 0, y: 0 }} onClose={onClose} />);
    const selected = () => document.querySelector(".desk-menu .mi.sel")?.textContent ?? "";
    expect(selected()).toContain("Ask");
    fireEvent.keyDown(window, { key: "j" });
    expect(selected()).toContain("Note in margin");
    fireEvent.keyDown(window, { key: "ArrowDown" });
    fireEvent.keyDown(window, { key: "ArrowDown" });
    // The marimo row is passed over: it arrives with notebooks.
    expect(selected()).toContain("What this knows");
    fireEvent.keyDown(window, { key: "k" });
    fireEvent.keyDown(window, { key: "ArrowUp" });
    fireEvent.keyDown(window, { key: "Enter" });
    expect(runs.note).toHaveBeenCalledTimes(1);
    fireEvent.keyDown(window, { key: "i" });
    expect(runs.knows).toHaveBeenCalledTimes(1);
    const marimo = screen.getByText("marimo cell · arrives with notebooks").closest("button") as HTMLButtonElement;
    expect(marimo.disabled).toBe(true);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
    fireEvent.mouseDown(document.body);
    expect(onClose).toHaveBeenCalledTimes(2);
  });

  it("leaves a chord to the desks (alt, ctrl, meta)", () => {
    const runs = { ask: vi.fn() };
    render(<ContextMenu header="h" rows={verbs(runs)} at={{ x: 0, y: 0 }} onClose={() => undefined} />);
    fireEvent.keyDown(window, { key: "a", altKey: true });
    fireEvent.keyDown(window, { key: "a", ctrlKey: true });
    expect(runs.ask).not.toHaveBeenCalled();
    fireEvent.keyDown(window, { key: "a" });
    expect(runs.ask).toHaveBeenCalledTimes(1);
  });

  it("opens the Append submenu of the desk's pads, the current one ticked, with a new pad last", () => {
    const onPick = vi.fn();
    render(<ContextMenu header="h" rows={verbs()} at={{ x: 0, y: 0 }} onClose={() => undefined}
      append={{ pads: [{ padId: "p1", title: "running · 23 Nov" }, { padId: "p2", title: "deriving" }], current: "p1", onPick }} />);
    fireEvent.keyDown(window, { key: "w" });
    const submenu = screen.getByRole("menu", { name: "append to" });
    expect(within(submenu).getByText("running · 23 Nov").closest("button")?.textContent).toContain("✓");
    expect(within(submenu).getByText("deriving").closest("button")?.textContent).not.toContain("✓");
    fireEvent.click(within(submenu).getByText("a new pad"));
    expect(onPick).toHaveBeenCalledWith("+");
    fireEvent.click(within(submenu).getByText("deriving"));
    expect(onPick).toHaveBeenCalledWith("p2");
  });

  it("keeps the verbs below the promoted block, What this knows after the separator", async () => {
    const { api } = promotedApi(promoted([row("r1")]));
    render(<ContextMenu header="h" rows={verbs()} at={{ x: 0, y: 0 }} object={{ objectKind: "passage", extractionId: "e", spanId: "s" }} promoted={api} onClose={() => undefined} />);
    await screen.findByText("row r1");
    const labels = [...document.querySelectorAll(".desk-menu > .mi, .desk-menu > .pro > .mi, .desk-menu > .sep")].map((each) => each.classList.contains("sep") ? "—" : each.querySelector(".t")?.firstChild?.textContent);
    expect(labels).toEqual(["row r1", "Ask", "Note in margin", "Append to “running”  ▸", "marimo cell · arrives with notebooks", "—", "What this knows"]);
  });
});

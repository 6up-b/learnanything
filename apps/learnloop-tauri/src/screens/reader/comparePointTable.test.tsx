// Reader CA4: the table by point (ux_reader_compare_ask_v1 §5, X3-X5; K13, K16).
//
// * The grid: a row per point, a column per book, the learner's column last;
//   each cell the book's verified words then LearnLoop's line, or "— not
//   addressed here" ("— not here" on a requested view); a view no book fills
//   reads "not found in your library". No summary, consensus or count.
// * Chips: exactly the relations the row's pairs returned ("the same claim"
//   only when every pair said it; "only in Axler" when one book alone is
//   quoted); ↵ on the row header opens the pairs (X4).
// * The keyboard map (§5.5): the roving focus starts on the first row header
//   and never moves on landing; arrows, Home and End; Space peeks, o opens,
//   t takes, - hides, v switches the layout, k keeps; `/` and Ctrl+↵ are left
//   to the comparison's controls.
// * Narrow: cards by point below the breakpoint, the grid again when wide.
// * By book: one card per book, remembered per device.
// * v1: a comparison with no points renders by book exactly as today, with
//   "compare again by point ▸" where a host offers it.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { CompareTableDto, ComparePointDto, KeptComparisonDto } from "../../api/dto";
import { CompareKeep } from "./CompareKeep";
import { CompareKeepContext, type CompareKeepContextValue } from "./compareKeepContext";
import { CompareGridActionsContext, ComparePointTable, POINT_COPY, type CompareGridActions } from "./ComparePointTable";
import { CHIP_LABELS, LAYOUT_KEY, cardsByPoint, moveCell, rowChips } from "./comparePoints";
import { COMPARE_AGAIN_COPY, CompareTable } from "./LibraryAnswer";
import { LibraryPane, useComparingStacked } from "./LibraryPane";
import type { LibraryAskController } from "./useLibraryAsk";

const { api } = vi.hoisted(() => ({
  api: { readerLibraryCompareKeep: vi.fn(), readerLibraryCompareRemove: vi.fn() },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const AXLER = "ext_axler:a1";
const STRANG = "ext_strang:s1";
const LAY = "ext_lay:l1";

function row(key: string, title: string, sourceId: string) {
  return { sourceId, sourceTitle: title, key, page: 12, isOpenSource: false, contributes: [], assumes: [], differs: [] };
}

function quoted(key: string, quote: string, line: string) {
  return { key, status: "quoted" as const, quote, line, spanKey: key, authorship: "ai" as const };
}

function absent(key: string) {
  return { key, status: "not_addressed" as const };
}

const POINTS: ComparePointDto[] = [
  { id: "p1", label: "existence argument", kind: "point", labelVoice: "model",
    cells: [quoted(AXLER, "every operator on a finite-dimensional complex space has an eigenvalue", "polynomial in A, no determinant"),
      quoted(STRANG, "the eigenvalues are the roots of det(A - λI) = 0", "roots of the characteristic polynomial")],
    relations: [{ leftKey: AXLER, rightKey: STRANG, relation: "different_assumptions", statement: "one avoids determinants",
      leftQuote: "every operator on a finite-dimensional", rightQuote: "the roots of det", authorship: "ai" }] },
  { id: "p2", label: "what's assumed of the field", kind: "point", labelVoice: "model",
    cells: [quoted(AXLER, "we assume F is C throughout", "needs ℂ explicitly"), absent(STRANG)], relations: [] },
  { id: "p3", label: "a geometric view", kind: "perspective", labelVoice: "learner",
    cells: [absent(AXLER), quoted(STRANG, "directions that A only stretches", "directions A only stretches")], relations: [] },
  { id: "p4", label: "an application", kind: "perspective", labelVoice: "learner",
    cells: [absent(AXLER), absent(STRANG)], relations: [] },
];

function table(extra: Partial<CompareTableDto> = {}): CompareTableDto {
  return {
    askId: "la_1", status: "ok", comparisonId: "scmp_1", header: "differences kept · each line quotes its own source",
    rows: [row(AXLER, "Axler", "src_axler"), row(STRANG, "Strang", "src_strang")],
    alsoDiscussedIn: [{ sourceId: "src_lay", sourceTitle: "Lay" }], unverifiedSources: [], droppedPins: [], droppedLineCount: 0,
    kept: null, contract: "source_compare.v2", points: POINTS,
    scope: { door: "ask_box", question: "why eigenvalues exist", sourceIds: [], anchorKeys: [] }, ...extra,
  };
}

const KEEP: CompareKeepContextValue = {
  settings: { library: true, tutor: true, perspectives: true, maxPerspectives: 4 }, onChanged: vi.fn(), openSourceId: null,
};

function kept(extra: Partial<KeptComparisonDto> = {}): KeptComparisonDto {
  return { askId: "la_1", keptAt: "2026-10-03T10:00:00Z", objects: [], relations: [], takes: [], notKept: 0, status: "proposed",
    label: "kept as proposals · nothing changes your map until you review them", layout: "by_point", hiddenPoints: [], ...extra };
}

function setWidth(width: number) {
  Object.defineProperty(window, "innerWidth", { configurable: true, writable: true, value: width });
  act(() => {
    window.dispatchEvent(new Event("resize"));
  });
}

function mount(value: CompareTableDto = table(), actions: CompareGridActions | null = null, keep: CompareKeepContextValue | null = KEEP) {
  return render(
    <CompareKeepContext.Provider value={keep}>
      <CompareGridActionsContext.Provider value={actions}>
        <CompareTable table={value} />
        <CompareKeep table={value} target={{ askId: value.askId }} />
      </CompareGridActionsContext.Provider>
    </CompareKeepContext.Provider>,
  );
}

function cell(row: number, col: number): HTMLElement {
  const found = document.querySelector<HTMLElement>(`[data-cell="${row}:${col}"]`);
  if (!found) throw new Error(`no cell ${row}:${col}`);
  return found;
}

// A per-test in-memory localStorage (this runner has none of its own).
const store = new Map<string, string>();
const storage = {
  getItem: (key: string) => store.get(key) ?? null,
  setItem: (key: string, value: string) => void store.set(key, String(value)),
  removeItem: (key: string) => void store.delete(key),
  clear: () => store.clear(),
};

/** Focus a cell as the learner would (React reads focus as focusin). */
function focusCell(node: HTMLElement) {
  act(() => node.focus());
  fireEvent.focusIn(node);
}

beforeEach(() => {
  store.clear();
  vi.stubGlobal("localStorage", storage);
  Object.defineProperty(window, "localStorage", { configurable: true, value: storage });
  setWidth(1400);
  api.readerLibraryCompareKeep.mockReset();
  api.readerLibraryCompareRemove.mockReset();
});
afterEach(() => cleanup());

// -- the chips, pure -----------------------------------------------------------------------------------

it("chips are exactly the relations the row's pairs returned", () => {
  const titles = new Map([[AXLER, "Axler"], [STRANG, "Strang"], [LAY, "Lay"]]);
  const three = (relations: ComparePointDto["relations"]): ComparePointDto => ({
    id: "p", label: "x", kind: "point", labelVoice: "model", relations,
    cells: [quoted(AXLER, "a", "a"), quoted(STRANG, "b", "b"), quoted(LAY, "c", "c")] });
  const rel = (left: string, right: string, relation: string) => ({ leftKey: left, rightKey: right, relation, statement: null, leftQuote: null, rightQuote: null });
  // "the same claim" only when every pair on the row said it.
  expect(rowChips(three([rel(AXLER, STRANG, "equivalent"), rel(STRANG, LAY, "equivalent")]), titles)).toEqual([]);
  expect(rowChips(three([rel(AXLER, STRANG, "equivalent"), rel(STRANG, LAY, "equivalent"), rel(AXLER, LAY, "equivalent")]), titles)
    .map((chip) => chip.label)).toEqual(["the same claim"]);
  // Every other label when at least one pair said it, in the table's order, never merged.
  expect(rowChips(three([rel(AXLER, STRANG, "disagreement"), rel(STRANG, LAY, "different_notation"), rel(AXLER, LAY, "equivalent")]), titles)
    .map((chip) => chip.label)).toEqual(["different notation", "they disagree"]);
  // One book alone quoted: "only in Axler", not a relation.
  expect(rowChips(POINTS[1], titles)).toEqual([{ kind: "only", key: AXLER, label: "only in Axler" }]);
  // No relation returned, no chip; "complementary" is never a chip.
  expect(rowChips({ ...POINTS[0], relations: [] }, titles)).toEqual([]);
  expect(Object.keys(CHIP_LABELS)).not.toContain("complementary");
});

it("the roving focus moves by cell and stops at the edges", () => {
  const cols = () => 4;
  expect(moveCell({ row: 0, col: 0 }, "ArrowRight", 3, cols)).toEqual({ row: 0, col: 1 });
  expect(moveCell({ row: 0, col: 3 }, "ArrowRight", 3, cols)).toEqual({ row: 0, col: 3 });
  expect(moveCell({ row: 2, col: 1 }, "ArrowDown", 3, cols)).toEqual({ row: 2, col: 1 });
  expect(moveCell({ row: 1, col: 2 }, "Home", 3, cols)).toEqual({ row: 1, col: 0 });
  expect(moveCell({ row: 1, col: 0 }, "End", 3, cols)).toEqual({ row: 1, col: 3 });
  // A hidden row is one cell: moving onto it lands on its header.
  expect(moveCell({ row: 0, col: 2 }, "ArrowDown", 3, (r) => (r === 1 ? 1 : 4))).toEqual({ row: 1, col: 0 });
  expect(moveCell({ row: 0, col: 0 }, "x", 3, cols)).toBeNull();
  expect(cardsByPoint(null, 1000)).toBe(true);
  expect(cardsByPoint(null, 1400)).toBe(false);
  expect(cardsByPoint(500, 1400)).toBe(true);
});

// -- the grid --------------------------------------------------------------------------------------------

it("renders a row per point and a column per book, each cell quoted or not addressed", () => {
  mount();
  const grid = screen.getByRole("grid", { name: "how your books treat this, by point" });
  expect(grid.closest("[data-layout]")?.getAttribute("data-layout")).toBe("grid");
  const headers = within(grid).getAllByRole("columnheader").map((node) => node.textContent);
  expect(headers).toEqual(["◇ point", "§ Axler p.12", "§ Strang p.12", "› you"]);
  const rows = within(grid).getAllByRole("rowheader").map((node) => node.textContent ?? "");
  expect(rows[0]).toContain("LearnLoop's point");
  expect(rows[0]).toContain("existence argument");
  expect(rows[1]).not.toContain("LearnLoop's point");
  // Book words first, LearnLoop's line under them, in their own voices.
  const first = cell(0, 1);
  expect(first.querySelector("[data-cell-voice='source']")?.textContent).toContain("every operator on a finite-dimensional");
  expect(first.querySelector("[data-cell-voice='model']")?.textContent).toContain("polynomial in A, no determinant");
  expect(first.getAttribute("aria-label")).toBe(
    "Axler, on existence argument. From the book: every operator on a finite-dimensional complex space has an eigenvalue LearnLoop's reading: polynomial in A, no determinant");
  expect(cell(1, 2).textContent).toBe(`— ${POINT_COPY.notAddressed}`);
  // A requested view: the learner's words, "not here" per book, "not found" for a row no book fills.
  const view = document.querySelector("[data-point='p3'] [data-row-voice]");
  expect(view?.getAttribute("data-row-voice")).toBe("learner");
  expect(cell(2, 1).textContent).toBe(`— ${POINT_COPY.notHere}`);
  expect(cell(3, 0).textContent).toContain(POINT_COPY.notFound);
  // No consensus, summary or count anywhere; the finished table says how long it is, once.
  const text = document.body.textContent ?? "";
  expect(text).not.toMatch(/summary|consensus|overall/i);
  expect(screen.getByRole("status").textContent).toBe("Comparison ready: 4 points");
  // The landing takes no focus.
  expect(grid.contains(document.activeElement)).toBe(false);
  expect(cell(0, 0).tabIndex).toBe(0);
  // CompareKeep's band is the grid's now (not drawn twice).
  expect(document.querySelector("[data-compare-keep]")).toBeNull();
});

it("a chip names the relation, and its pairs open on the row header (X4)", () => {
  mount();
  const chip = document.querySelector<HTMLElement>("[data-point='p1'] [data-chip='different_assumptions']")!;
  expect(chip.textContent).toBe("different assumptions");
  expect(chip.getAttribute("aria-label")).toBe("LearnLoop's reading of how they relate: different assumptions.");
  expect(document.querySelector("[data-point='p2'] [data-chip='only']")?.textContent).toBe("only in Axler");
  expect(document.querySelector("[data-pairs='p1']")).toBeNull();
  const header = cell(0, 0);
  focusCell(header);
  fireEvent.keyDown(header, { key: "Enter" });
  const pairs = document.querySelector("[data-pairs='p1']");
  expect(pairs?.textContent).toContain("Axler ⇄ Strang · different assumptions");
  expect(pairs?.textContent).toContain("one avoids determinants");
  fireEvent.keyDown(header, { key: "Escape" });
  expect(document.querySelector("[data-pairs='p1']")).toBeNull();
});

it("the keyboard map: arrows, Space peek, o open, ↵ expand, and the old keys left to the controls", () => {
  const onPeek = vi.fn();
  const onOpen = vi.fn();
  const outer = vi.fn();
  render(
    <div onKeyDown={(event) => outer(event.key, event.ctrlKey)}>
      <CompareKeepContext.Provider value={KEEP}>
        <CompareGridActionsContext.Provider value={{ onPeek, onOpen }}>
          <ComparePointTable table={table()} />
        </CompareGridActionsContext.Provider>
      </CompareKeepContext.Provider>
    </div>,
  );
  focusCell(cell(0, 0));
  fireEvent.keyDown(cell(0, 0), { key: "ArrowRight" });
  expect(document.activeElement).toBe(cell(0, 1));
  fireEvent.keyDown(cell(0, 1), { key: " " });
  expect(onPeek).toHaveBeenCalledWith({ spanKey: AXLER, sourceTitle: "Axler" });
  fireEvent.keyDown(cell(0, 1), { key: "o" });
  expect(onOpen).toHaveBeenCalledWith({ sourceId: "src_axler", extractionId: "ext_axler", spanId: "a1" });
  fireEvent.keyDown(cell(0, 1), { key: "End" });
  expect(document.activeElement).toBe(cell(0, 3));
  fireEvent.keyDown(cell(0, 3), { key: "ArrowDown" });
  expect(document.activeElement).toBe(cell(1, 3));
  fireEvent.keyDown(cell(1, 3), { key: "Home" });
  expect(document.activeElement).toBe(cell(1, 0));
  // Space on a cell with nothing verified peeks nothing.
  fireEvent.keyDown(cell(1, 0), { key: "ArrowRight" });
  fireEvent.keyDown(cell(1, 1), { key: "ArrowRight" });
  fireEvent.keyDown(cell(1, 2), { key: " " });
  expect(onPeek).toHaveBeenCalledTimes(1);
  // The grid's own keys stop at the grid; refine, add a book and the tutor reach the controls.
  outer.mockClear();
  fireEvent.keyDown(cell(1, 2), { key: "/" });
  fireEvent.keyDown(cell(1, 2), { key: "+" });
  fireEvent.keyDown(cell(1, 2), { key: "Enter", ctrlKey: true });
  fireEvent.keyDown(cell(1, 2), { key: "ArrowUp" });
  expect(outer.mock.calls).toEqual([["/", false], ["+", false], ["Enter", true]]);
});

it("↵ expands a long quote, and the screen reader hears not addressed spoken", () => {
  const long = "x ".repeat(100).trim();
  mount(table({ points: [{ ...POINTS[0], cells: [quoted(AXLER, long, "line"), absent(STRANG)] }] }));
  const quote = cell(0, 1).querySelector<HTMLElement>("[data-quote]")!;
  expect(quote.style.webkitLineClamp || quote.style.getPropertyValue("-webkit-line-clamp")).toBe("2");
  focusCell(cell(0, 1));
  fireEvent.keyDown(cell(0, 1), { key: "Enter" });
  expect(cell(0, 1).querySelector<HTMLElement>("[data-quote]")!.style.webkitLineClamp || "").toBe("");
  expect(cell(0, 2).getAttribute("aria-label")).toBe("Strang, on existence argument: not addressed here.");
});

it("t writes a take in the row, k keeps it with the hidden rows, - after keep hides through the server", async () => {
  api.readerLibraryCompareKeep.mockResolvedValueOnce({ askId: "la_1", kept: kept({ hiddenPoints: ["p2"],
    takes: [{ id: "rel_t", keys: [`${AXLER}#p1`], learnerText: "Axler's route generalizes", pointId: "p1" }] }), addedTakes: 1, alreadyKept: false });
  mount();
  focusCell(cell(0, 0));
  fireEvent.keyDown(cell(0, 0), { key: "t" });
  const box = screen.getByRole("textbox", { name: "your take on this row" });
  expect(document.activeElement).toBe(box); // the learner's key: the box takes the cursor
  fireEvent.change(box, { target: { value: "Axler's route generalizes" } });
  fireEvent.submit(box.closest("form")!);
  await waitFor(() => expect(document.querySelector("[data-point='p1'] [data-draft]")?.textContent).toContain("Axler's route generalizes"));
  expect(api.readerLibraryCompareKeep).not.toHaveBeenCalled(); // nothing kept until k
  // `-` on a row before keeping: the row folds to one line and isn't kept.
  focusCell(cell(1, 0));
  fireEvent.keyDown(cell(1, 0), { key: "-" });
  expect(document.querySelector("[data-point='p2'][data-hidden]")?.textContent).toContain("hidden: what's assumed of the field · show");
  fireEvent.keyDown(cell(1, 0), { key: "k" });
  await waitFor(() => expect(api.readerLibraryCompareKeep).toHaveBeenCalledTimes(1));
  expect(api.readerLibraryCompareKeep).toHaveBeenCalledWith({ askId: "la_1", comparisonId: "scmp_1",
    takes: [{ text: "Axler's route generalizes", pointId: "p1" }], hiddenPoints: ["p2"] });
  await screen.findByText("kept ⇄");
  expect(document.querySelector("[data-point='p1'] [data-cell-voice='learner']")?.textContent).toContain("Axler's route generalizes");
  // After a keep, showing the row again goes to the server (it proposes it again).
  api.readerLibraryCompareKeep.mockResolvedValueOnce({ askId: "la_1", kept: kept(), addedTakes: 0, alreadyKept: true });
  fireEvent.click(within(document.querySelector<HTMLElement>("[data-point='p2']")!).getByRole("button", { name: POINT_COPY.show }));
  await waitFor(() => expect(api.readerLibraryCompareKeep).toHaveBeenLastCalledWith({ askId: "la_1", comparisonId: "scmp_1", hiddenPoints: [] }));
  await waitFor(() => expect(document.querySelector("[data-point='p2'][data-hidden]")).toBeNull());
});

it("a take on the whole comparison sits in the table's foot", async () => {
  api.readerLibraryCompareKeep.mockResolvedValueOnce({ askId: "la_1", kept: kept({
    takes: [{ id: "rel_w", keys: [], learnerText: "two routes, one fact", about: "comparison" }] }), addedTakes: 1, alreadyKept: false });
  mount(table({ kept: kept() }));
  const foot = document.querySelector<HTMLElement>("[data-take-whole]")!;
  expect(foot.textContent).toContain(POINT_COPY.aboutWhole);
  fireEvent.click(within(foot).getByRole("button", { name: "add your take" }));
  const box = screen.getByRole("textbox", { name: "your take on the whole comparison" });
  fireEvent.change(box, { target: { value: "two routes, one fact" } });
  fireEvent.submit(box.closest("form")!);
  await waitFor(() => expect(api.readerLibraryCompareKeep).toHaveBeenCalledWith({ askId: "la_1", comparisonId: "scmp_1",
    takes: [{ text: "two routes, one fact", about: "comparison" }] }));
  await waitFor(() => expect(document.querySelector("[data-take-whole]")?.textContent).toContain("two routes, one fact"));
});

it("narrow: cards by point with the same keys, and the grid again when wide", () => {
  setWidth(1000);
  mount();
  const frame = document.querySelector("[data-compare-points]")!;
  expect(frame.getAttribute("data-layout")).toBe("cards");
  expect(document.querySelector("[data-compare-cards]")).not.toBeNull();
  expect(frame.textContent).toContain(POINT_COPY.cardKeys);
  focusCell(cell(0, 0));
  fireEvent.keyDown(cell(0, 0), { key: "ArrowRight" });
  expect(document.activeElement).toBe(cell(0, 1));
  fireEvent.keyDown(cell(0, 1), { key: "ArrowDown" });
  expect(document.activeElement).toBe(cell(1, 1));
  expect(cell(1, 1).textContent).toContain("Axler");
  setWidth(1400);
  expect(frame.getAttribute("data-layout")).toBe("grid");
});

it("v switches to by book, one card per book, and the choice is remembered", () => {
  mount();
  focusCell(cell(0, 0));
  fireEvent.keyDown(cell(0, 0), { key: "v" });
  const byBook = screen.getByRole("grid", { name: "how your books treat this, by book" });
  const books = byBook.querySelectorAll("[data-book]");
  expect(books).toHaveLength(2);
  expect(books[0].textContent).toContain("existence argument");
  expect(books[1].textContent).toContain(`— ${POINT_COPY.notAddressed}`);
  expect(window.localStorage.getItem(LAYOUT_KEY)).toBe("by_book");
  cleanup();
  mount();
  expect(document.querySelector("[data-compare-points]")?.getAttribute("data-layout")).toBe("by_book");
  fireEvent.click(screen.getByRole("button", { name: /by point/ }));
  expect(document.querySelector("[data-compare-points]")?.getAttribute("data-layout")).toBe("grid");
});

it("hidden rows of a kept comparison stay hidden when it reopens", () => {
  mount(table({ kept: kept({ hiddenPoints: ["p1"] }) }));
  expect(document.querySelector("[data-point='p1'][data-hidden]")?.textContent).toContain("hidden: existence argument");
  expect(screen.getByText("kept ⇄")).not.toBeNull();
});

it("keep off: the grid shows, with no keep, take or whole-comparison take", () => {
  mount(table(), null, null);
  expect(screen.getByRole("grid")).not.toBeNull();
  expect(screen.queryByRole("button", { name: "keep comparison ⇄" })).toBeNull();
  expect(document.querySelector("[data-take-whole]")).toBeNull();
  focusCell(cell(0, 0));
  fireEvent.keyDown(cell(0, 0), { key: "t" });
  expect(screen.queryByRole("textbox")).toBeNull();
});

// -- v1 comparisons: by book, as today --------------------------------------------------------------------

const V1: CompareTableDto = {
  askId: "la_1", status: "ok", comparisonId: "scmp_0", header: "differences kept · each line quotes its own source",
  rows: [
    { ...row(AXLER, "Axler", "src_axler"), contributes: [{ line: "adds the operator view", quote: "every operator", authorship: "ai" }],
      differs: [{ line: "one avoids determinants", quote: "every operator", relation: "disagreement", otherSourceTitle: "Strang", authorship: "ai" }] },
    { ...row(STRANG, "Strang", "src_strang"), contributes: [{ line: "computes", quote: "roots of det", authorship: "ai" }],
      differs: [{ line: "one avoids determinants", quote: "roots of det", relation: "disagreement", otherSourceTitle: "Axler", authorship: "ai" }] },
  ],
  alsoDiscussedIn: [], unverifiedSources: [], droppedPins: [], droppedLineCount: 0, kept: null,
};

it("a v1 comparison renders by book exactly as today, and can be compared again by point", () => {
  const onCompareAgain = vi.fn();
  mount(V1);
  expect(screen.queryByRole("grid")).toBeNull();
  const old = document.querySelector("[data-compare-table]")!;
  expect(old.textContent).toContain("contributes");
  expect(old.textContent).toContain("differs from the others");
  expect(document.querySelector("[data-compare-keep]")).not.toBeNull(); // today's relations band and keep
  expect(document.querySelector("[data-compare-again]")).toBeNull(); // only where a host offers it
  cleanup();
  mount(V1, { onCompareAgain });
  const again = document.querySelector<HTMLElement>("[data-compare-again]")!;
  expect(again.textContent).toContain(COMPARE_AGAIN_COPY.cost); // named before it runs
  expect(again.textContent).not.toMatch(/old/i);
  fireEvent.click(within(again).getByRole("button", { name: COMPARE_AGAIN_COPY.again }));
  expect(onCompareAgain).toHaveBeenCalledWith(V1);
});

// -- the posture: stacking and the re-clamp -------------------------------------------------------------------

function Stacked({ on }: { on: boolean }) {
  return <span data-stacked={String(useComparingStacked(on))} />;
}

it("the comparing posture stacks below the breakpoint (only while by point is on) and re-clamps on resize", () => {
  setWidth(1000);
  render(<><Stacked on /><Stacked on={false} /></>);
  const flags = [...document.querySelectorAll("[data-stacked]")].map((node) => node.getAttribute("data-stacked"));
  expect(flags).toEqual(["true", "false"]);
  setWidth(1400);
  expect(document.querySelector("[data-stacked]")?.getAttribute("data-stacked")).toBe("false");
  cleanup();
  window.localStorage.setItem("ll.library.splitWidth", "900");
  const ctl = { state: null, byPoint: true, closePeek: vi.fn() } as unknown as LibraryAskController;
  render(<LibraryPane ctl={ctl} compose={null} onCompose={vi.fn()} onAsk={vi.fn()} onOpenHit={null} onPracticePick={null} onClose={vi.fn()} />);
  const pane = document.querySelector<HTMLElement>("[data-comparing-pane]")!;
  expect(pane.style.width).toBe("900px");
  setWidth(1000); // the book keeps its 360 px: 1000 - 360
  expect(pane.style.width).toBe("640px");
  cleanup();
  render(<LibraryPane ctl={ctl} compose={null} onCompose={vi.fn()} onAsk={vi.fn()} onOpenHit={null} onPracticePick={null} onClose={vi.fn()} stacked />);
  expect(document.querySelector("[data-comparing-pane]")?.getAttribute("data-layout")).toBe("stacked");
  expect(screen.queryByRole("separator")).toBeNull();
  window.localStorage.removeItem("ll.library.splitWidth");
});

it("switched off the pane keeps its width at mount (RW4a's)", () => {
  window.localStorage.setItem("ll.library.splitWidth", "900");
  const ctl = { state: null, byPoint: false, closePeek: vi.fn() } as unknown as LibraryAskController;
  render(<LibraryPane ctl={ctl} compose={null} onCompose={vi.fn()} onAsk={vi.fn()} onOpenHit={null} onPracticePick={null} onClose={vi.fn()} />);
  const pane = document.querySelector<HTMLElement>("[data-comparing-pane]")!;
  setWidth(1000);
  expect(pane.style.width).toBe("900px");
  expect(screen.getByRole("separator")).not.toBeNull();
  window.localStorage.removeItem("ll.library.splitWidth");
});

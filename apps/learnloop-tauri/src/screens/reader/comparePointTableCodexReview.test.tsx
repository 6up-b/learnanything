// Reader CA4 Codex review (stage reader-ca4-table-by-point), the grid's and
// the hook's fixes:
//
// * F2: a take written on a row that is hidden before Keep stays in its row
//   (Keep leaves the row out, so the take is not sent with it), and goes with
//   the request that shows the row again after the keep.
// * F3: rapid hides on a kept comparison: one request at a time, each with the
//   latest wanted rows, so a later hide never shows an earlier one again.
// * F4: by book keeps the learner's takes (a card of their own) and `t` opens a
//   box there; an empty take cell has a pressable "add your take".
// * F6: "compare again by point" keeps the books the table shows.
// * F7: "where else is this explained? ▸" on a view no book fills is wired to
//   a library ask on that view's words.
// * F8: hiding the focused book cell moves the roving focus to the row header;
//   the grid always has one tab stop.
// * N1 (scoped verify): a hide pressed while the first Keep is in flight is
//   never undone by the Keep's reply; it is sent, in turn, once the keep is
//   there (and stays a local choice when the keep fails, sending nothing).
import { act, cleanup, fireEvent, render, renderHook, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { CompareTableDto, ComparePointDto, KeptComparisonDto, LibraryAskDto, ReaderPromptContractDto } from "../../api/dto";
import { CompareKeepContext, type CompareKeepContextValue } from "./compareKeepContext";
import { CompareGridActionsContext, ComparePointTable, POINT_COPY, type CompareGridActions } from "./ComparePointTable";
import { useLibraryAsk, type LibraryAskRequest } from "./useLibraryAsk";

const { api } = vi.hoisted(() => ({
  api: {
    readerLibraryCompareKeep: vi.fn(), readerLibraryCompareRemove: vi.fn(),
    readerLibraryAsk: vi.fn(), readerLibraryAskNotes: vi.fn(), readerLibraryCompare: vi.fn(), readerLibraryJob: vi.fn(),
    readerLibraryJobCancel: vi.fn(), getSpanView: vi.fn(),
  },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const AXLER = "ext_axler:a1";
const STRANG = "ext_strang:s1";

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
    cells: [quoted(AXLER, "every operator has an eigenvalue", "no determinant"), quoted(STRANG, "roots of det(A - λI)", "the polynomial")],
    relations: [] },
  { id: "p2", label: "what's assumed of the field", kind: "point", labelVoice: "model",
    cells: [quoted(AXLER, "we assume F is C", "needs ℂ"), absent(STRANG)], relations: [] },
  { id: "p3", label: "an application", kind: "perspective", labelVoice: "learner",
    cells: [absent(AXLER), absent(STRANG)], relations: [] },
];

function table(extra: Partial<CompareTableDto> = {}): CompareTableDto {
  return {
    askId: "la_1", status: "ok", comparisonId: "scmp_1", header: "differences kept · each line quotes its own source",
    rows: [row(AXLER, "Axler", "src_axler"), row(STRANG, "Strang", "src_strang")],
    alsoDiscussedIn: [], unverifiedSources: [], droppedPins: [], droppedLineCount: 0,
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

function mount(value: CompareTableDto = table(), actions: CompareGridActions | null = null) {
  return render(
    <CompareKeepContext.Provider value={KEEP}>
      <CompareGridActionsContext.Provider value={actions}>
        <ComparePointTable table={value} />
      </CompareGridActionsContext.Provider>
    </CompareKeepContext.Provider>,
  );
}

function cell(row: number, col: number): HTMLElement {
  const found = document.querySelector<HTMLElement>(`[data-cell="${row}:${col}"]`);
  if (!found) throw new Error(`no cell ${row}:${col}`);
  return found;
}

function focusCell(node: HTMLElement) {
  act(() => node.focus());
  fireEvent.focusIn(node);
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => { resolve = res; });
  return { promise, resolve };
}

const store = new Map<string, string>();
const storage = {
  getItem: (key: string) => store.get(key) ?? null,
  setItem: (key: string, value: string) => void store.set(key, String(value)),
  removeItem: (key: string) => void store.delete(key),
  clear: () => store.clear(),
};

beforeEach(() => {
  store.clear();
  Object.defineProperty(window, "localStorage", { configurable: true, value: storage });
  Object.defineProperty(window, "innerWidth", { configurable: true, writable: true, value: 1400 });
  for (const mock of Object.values(api)) mock.mockReset();
});
afterEach(() => { cleanup(); });

function writeTake(text: string) {
  const box = screen.getByRole("textbox", { name: "your take on this row" });
  fireEvent.change(box, { target: { value: text } });
  fireEvent.submit(box.closest("form")!);
}

it("F2: a take on a row hidden before Keep is not sent with the keep, and goes with showing the row", async () => {
  api.readerLibraryCompareKeep
    .mockResolvedValueOnce({ askId: "la_1", kept: kept({ hiddenPoints: ["p1"] }), addedTakes: 0, alreadyKept: false })
    .mockResolvedValueOnce({ askId: "la_1", kept: kept({ hiddenPoints: [],
      takes: [{ id: "rel_t", keys: [], learnerText: "Axler's route generalizes", pointId: "p1" }] }), addedTakes: 1, alreadyKept: true });
  mount();
  focusCell(cell(0, 0));
  fireEvent.keyDown(cell(0, 0), { key: "t" });
  writeTake("Axler's route generalizes");
  fireEvent.keyDown(cell(0, 0), { key: "-" });
  expect(document.querySelector("[data-point='p1'][data-hidden]")).not.toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "keep comparison ⇄" }));
  await waitFor(() => expect(api.readerLibraryCompareKeep).toHaveBeenCalledTimes(1));
  expect(api.readerLibraryCompareKeep.mock.calls[0][0]).toEqual({ askId: "la_1", comparisonId: "scmp_1", takes: [], hiddenPoints: ["p1"] });
  await waitFor(() => expect(screen.getByText("kept ⇄")).not.toBeNull());
  // Shown again after the keep: the take goes with it.
  fireEvent.click(within(document.querySelector<HTMLElement>("[data-point='p1'][data-hidden]")!).getByRole("button", { name: POINT_COPY.show }));
  await waitFor(() => expect(api.readerLibraryCompareKeep).toHaveBeenCalledTimes(2));
  expect(api.readerLibraryCompareKeep.mock.calls[1][0]).toEqual({ askId: "la_1", comparisonId: "scmp_1", hiddenPoints: [],
    takes: [{ text: "Axler's route generalizes", pointId: "p1" }] });
  await waitFor(() => expect(document.querySelector("[data-draft]")).toBeNull());
  expect(document.querySelector("[data-point='p1']")?.textContent).toContain("Axler's route generalizes");
});

it("F3: rapid hides on a kept comparison are sent one at a time with the latest rows, and none is undone", async () => {
  const first = deferred<unknown>();
  const second = deferred<unknown>();
  api.readerLibraryCompareKeep.mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
  mount(table({ kept: kept() }));
  focusCell(cell(0, 0));
  fireEvent.keyDown(cell(0, 0), { key: "-" });
  await waitFor(() => expect(api.readerLibraryCompareKeep).toHaveBeenCalledTimes(1));
  expect(api.readerLibraryCompareKeep.mock.calls[0][0].hiddenPoints).toEqual(["p1"]);
  // The second hide while the first is in flight: it reads hidden at once and waits its turn.
  fireEvent.keyDown(cell(0, 0), { key: "ArrowDown" });
  fireEvent.keyDown(cell(1, 0), { key: "-" });
  expect(document.querySelectorAll("[data-hidden]")).toHaveLength(2);
  await act(async () => { await Promise.resolve(); });
  expect(api.readerLibraryCompareKeep).toHaveBeenCalledTimes(1);
  await act(async () => { first.resolve({ askId: "la_1", kept: kept({ hiddenPoints: ["p1"] }), addedTakes: 0, alreadyKept: true }); });
  // The first reply doesn't show p2 again while its hide is waiting.
  expect(document.querySelectorAll("[data-hidden]")).toHaveLength(2);
  await waitFor(() => expect(api.readerLibraryCompareKeep).toHaveBeenCalledTimes(2));
  expect(api.readerLibraryCompareKeep.mock.calls[1][0].hiddenPoints).toEqual(["p1", "p2"]);
  await act(async () => { second.resolve({ askId: "la_1", kept: kept({ hiddenPoints: ["p1", "p2"] }), addedTakes: 0, alreadyKept: true }); });
  expect(document.querySelectorAll("[data-hidden]")).toHaveLength(2);
});

it("N1: a row hidden while the first Keep is in flight stays hidden and is sent once the keep is there", async () => {
  const keepReply = deferred<unknown>();
  const hideReply = deferred<unknown>();
  api.readerLibraryCompareKeep.mockReturnValueOnce(keepReply.promise).mockReturnValueOnce(hideReply.promise);
  mount();
  fireEvent.click(screen.getByRole("button", { name: "keep comparison ⇄" }));
  await waitFor(() => expect(api.readerLibraryCompareKeep).toHaveBeenCalledTimes(1));
  expect(api.readerLibraryCompareKeep.mock.calls[0][0].hiddenPoints).toEqual([]);
  // Hidden while the Keep is pending: the row collapses at once.
  focusCell(cell(0, 0));
  fireEvent.keyDown(cell(0, 0), { key: "-" });
  expect(document.querySelector("[data-point='p1'][data-hidden]")).not.toBeNull();
  await act(async () => { keepReply.resolve({ askId: "la_1", kept: kept({ hiddenPoints: [] }), addedTakes: 0, alreadyKept: false }); });
  // The Keep's reply (made before the hide) doesn't show the row again ...
  expect(document.querySelector("[data-point='p1'][data-hidden]")).not.toBeNull();
  // ... and the hide goes to the server in turn, superseding the row's proposals.
  await waitFor(() => expect(api.readerLibraryCompareKeep).toHaveBeenCalledTimes(2));
  expect(api.readerLibraryCompareKeep.mock.calls[1][0]).toEqual({ askId: "la_1", comparisonId: "scmp_1", hiddenPoints: ["p1"] });
  await act(async () => { hideReply.resolve({ askId: "la_1", kept: kept({ hiddenPoints: ["p1"] }), addedTakes: 0, alreadyKept: true }); });
  expect(document.querySelector("[data-point='p1'][data-hidden]")).not.toBeNull();
  expect(screen.getByText("kept ⇄")).not.toBeNull();
});

it("N1: a row shown again while the first Keep is in flight sends its waiting take with the show (F2 kept)", async () => {
  const keepReply = deferred<unknown>();
  api.readerLibraryCompareKeep
    .mockReturnValueOnce(keepReply.promise)
    .mockResolvedValueOnce({ askId: "la_1", kept: kept({ hiddenPoints: [],
      takes: [{ id: "rel_t", keys: [], learnerText: "Axler's route generalizes", pointId: "p1" }] }), addedTakes: 1, alreadyKept: true });
  mount();
  focusCell(cell(0, 0));
  fireEvent.keyDown(cell(0, 0), { key: "t" });
  writeTake("Axler's route generalizes");
  fireEvent.keyDown(cell(0, 0), { key: "-" });
  fireEvent.click(screen.getByRole("button", { name: "keep comparison ⇄" }));
  await waitFor(() => expect(api.readerLibraryCompareKeep).toHaveBeenCalledTimes(1));
  expect(api.readerLibraryCompareKeep.mock.calls[0][0]).toEqual({ askId: "la_1", comparisonId: "scmp_1", takes: [], hiddenPoints: ["p1"] });
  fireEvent.click(within(document.querySelector<HTMLElement>("[data-point='p1'][data-hidden]")!).getByRole("button", { name: POINT_COPY.show }));
  expect(document.querySelector("[data-point='p1'][data-hidden]")).toBeNull();
  await act(async () => { keepReply.resolve({ askId: "la_1", kept: kept({ hiddenPoints: ["p1"] }), addedTakes: 0, alreadyKept: false }); });
  expect(document.querySelector("[data-point='p1'][data-hidden]")).toBeNull();
  await waitFor(() => expect(api.readerLibraryCompareKeep).toHaveBeenCalledTimes(2));
  expect(api.readerLibraryCompareKeep.mock.calls[1][0]).toEqual({ askId: "la_1", comparisonId: "scmp_1", hiddenPoints: [],
    takes: [{ text: "Axler's route generalizes", pointId: "p1" }] });
  await waitFor(() => expect(document.querySelector("[data-draft]")).toBeNull());
  expect(document.querySelector("[data-point='p1']")?.textContent).toContain("Axler's route generalizes");
});

it("N1: when the first Keep fails, a hide pressed during it stays a local choice and keeps nothing", async () => {
  const keepReply = deferred<unknown>();
  let fail!: (error: unknown) => void;
  keepReply.promise = new Promise((_, reject) => { fail = reject; });
  api.readerLibraryCompareKeep.mockReturnValueOnce(keepReply.promise);
  mount();
  fireEvent.click(screen.getByRole("button", { name: "keep comparison ⇄" }));
  await waitFor(() => expect(api.readerLibraryCompareKeep).toHaveBeenCalledTimes(1));
  focusCell(cell(0, 0));
  fireEvent.keyDown(cell(0, 0), { key: "-" });
  await act(async () => { fail(new Error("offline")); });
  await act(async () => { await Promise.resolve(); });
  expect(api.readerLibraryCompareKeep).toHaveBeenCalledTimes(1);
  expect(document.querySelector("[data-point='p1'][data-hidden]")).not.toBeNull();
  expect(screen.queryByText("kept ⇄")).toBeNull();
  // Keep again: the hide goes with it, as any hide before a keep.
  api.readerLibraryCompareKeep.mockResolvedValueOnce({ askId: "la_1", kept: kept({ hiddenPoints: ["p1"] }), addedTakes: 0, alreadyKept: false });
  fireEvent.click(screen.getByRole("button", { name: "keep comparison ⇄" }));
  await waitFor(() => expect(api.readerLibraryCompareKeep).toHaveBeenCalledTimes(2));
  expect(api.readerLibraryCompareKeep.mock.calls[1][0].hiddenPoints).toEqual(["p1"]);
});

it("F4: by book keeps the learner's takes, t opens a box there, and an empty take cell has a pressable add", async () => {
  mount(table({ kept: kept({ takes: [{ id: "rel_t", keys: [], learnerText: "Axler's route generalizes", pointId: "p1" }] }) }));
  // By point: the empty cell of p2 can be pressed.
  const add = document.querySelector<HTMLElement>("[data-add-take='p2']")!;
  expect(add).not.toBeNull();
  fireEvent.click(add);
  expect(screen.getByRole("textbox", { name: "your take on this row" })).not.toBeNull();
  fireEvent.keyDown(screen.getByRole("textbox"), { key: "Escape" });
  focusCell(cell(0, 0));
  fireEvent.keyDown(cell(0, 0), { key: "v" });
  const you = document.querySelector<HTMLElement>("[data-book-you]")!;
  expect(you).not.toBeNull();
  expect(you.textContent).toContain("Axler's route generalizes");
  // `t` on a book's cell (Axler, p2) opens the box in the learner's card.
  focusCell(cell(0, 2));
  fireEvent.keyDown(cell(0, 2), { key: "t" });
  const box = within(you).getByRole("textbox", { name: "your take on this row" });
  expect(document.activeElement).toBe(box);
  // p1 has a take (no add); p3 is a view no book fills (no take on it).
  expect(within(you).queryByRole("button", { name: /add your take: existence argument/ })).toBeNull();
  expect(within(you).queryByRole("button", { name: /add your take: an application/ })).toBeNull();
});

it("F8: hiding the focused book cell moves the focus to the row header, and the grid keeps one tab stop", () => {
  mount();
  focusCell(cell(0, 1));
  fireEvent.keyDown(cell(0, 1), { key: "-" });
  expect(document.querySelector("[data-point='p1'][data-hidden]")).not.toBeNull();
  expect(document.activeElement).toBe(cell(0, 0));
  const stops = [...document.querySelectorAll<HTMLElement>("[data-cell]")].filter((node) => node.tabIndex === 0);
  expect(stops).toEqual([cell(0, 0)]);
});

it("F7: a view no book fills offers where else is this explained, with its words and the table's question", () => {
  const onWhereElse = vi.fn();
  mount(table(), { onWhereElse });
  const row = document.querySelector<HTMLElement>("[data-point='p3']")!;
  expect(row.textContent).toContain(POINT_COPY.notFound);
  fireEvent.click(within(row).getByRole("button", { name: POINT_COPY.whereElse }));
  expect(onWhereElse).toHaveBeenCalledWith("an application", "why eigenvalues exist");
});

// -- the hook ---------------------------------------------------------------------------------------------

const CONTRACT = {
  libraryAsk: { expandGraph: true, personalizedDefault: true, compare: true, compareScope: true, compareByPoint: true },
} as unknown as ReaderPromptContractDto;
const REQUEST: LibraryAskRequest = { query: "why eigenvalues exist", entry: "reader", extractionId: "ext_axler", spanIds: ["a1"] };
const ASK = {
  askId: "la_1", query: "why eigenvalues exist", entry: "reader", status: "ok", policy: "reading", personalized: true,
  basis: "keyword", learningObjectIds: [], extractionId: "ext_axler", anchorSpanIds: ["a1"], hits: [],
  groups: { sources: [], expansions: [] }, expansions: [], expandGraph: true, sourceCount: 0, passageCount: 0,
} as unknown as LibraryAskDto;

function job<T>(jobId: string, kind: string, result: T) {
  return { jobId, kind, askId: "la_1", state: "done", result };
}

it("F6: compare again by point keeps the books the table shows (pins alone would widen it)", async () => {
  api.readerLibraryAsk.mockResolvedValue(job("ljob_ask", "ask", ASK));
  api.readerLibraryCompare.mockResolvedValue(job("ljob_cmp", "compare", table()));
  const { result } = renderHook(() => useLibraryAsk({ contract: CONTRACT, openSourceId: null, onError: vi.fn() }));
  act(() => result.current.ask(REQUEST));
  await waitFor(() => expect(result.current.state?.ask.phase).toBe("landed"));
  const v1 = table({ contract: undefined, points: undefined,
    scope: { door: "ask_box", question: "why eigenvalues exist", sourceIds: ["src_axler", "src_strang"], anchorKeys: [] } });
  act(() => result.current.compareAgain(v1));
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(1));
  const payload = api.readerLibraryCompare.mock.calls[0][0];
  expect(payload.pinnedSpanKeys).toEqual([AXLER, STRANG]);
  expect(payload.sourceIds).toEqual(["src_axler", "src_strang"]);
});

it("F7: where else asks the library on the view's words, from the same open book and passage", async () => {
  api.readerLibraryAsk.mockResolvedValue(job("ljob_ask", "ask", ASK));
  const { result } = renderHook(() => useLibraryAsk({ contract: CONTRACT, openSourceId: null, onError: vi.fn() }));
  act(() => result.current.ask(REQUEST));
  await waitFor(() => expect(result.current.state?.ask.phase).toBe("landed"));
  act(() => result.current.whereElse("an application", "why eigenvalues exist"));
  await waitFor(() => expect(api.readerLibraryAsk).toHaveBeenCalledTimes(2));
  expect(api.readerLibraryAsk.mock.calls[1][0]).toEqual({ query: "why eigenvalues exist: an application",
    entry: "where_else_explained", extractionId: "ext_axler", spanIds: ["a1"], personalized: true });
});

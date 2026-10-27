// Reader CA5a: find this section in my other books (ux_reader_compare_ask_v1
// §6.2, §6.3, X7): the Guide footer's pressed action, the unchecked hits by
// book, peek and go there, compare, "not about this" with undo, and the hidden
// cases (judged coverage, a protected section, a failed quiet read). Codex
// review fix round: the peek is its own read (F1, F2), the correction is one
// operation (F3, F6), and late answers never land on another section or a
// folded list (F4, F7).
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { CorrespondentPeekDto, CorrespondentSectionDto, CorrespondentsDto } from "../../api/dto";
import { FIND_COPY, FindSection, type FindSectionProps } from "./FindSection";
import { GuideRail, type GuideRailProps } from "./GuideRail";

const { api } = vi.hoisted(() => ({ api: {
  readerCorrespondents: vi.fn(), readerCorrespondentPeek: vi.fn(), readerCorrespondentDismiss: vi.fn(),
} }));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const SECTION = { id: "u61", label: "6.1 Introduction to eigenvalues", startSpanId: "s1" };

function hit(over: Partial<CorrespondentSectionDto> = {}): CorrespondentSectionDto {
  return {
    extractionId: "ext_axler", sectionId: "ax5a", title: "5.A Invariant subspaces", sourceId: "src_axler", sourceTitle: "Axler",
    read: false, jump: { extractionId: "ext_axler", sectionId: "ax5a", spanId: "a7" }, treatment: null,
    label: "found by search, not checked", by: "search", ...over,
  };
}

const LAY_51 = hit({ extractionId: "ext_lay", sectionId: "lay51", title: "5.1 Eigenvectors and eigenvalues", sourceId: "src_lay", sourceTitle: "Lay",
  jump: { extractionId: "ext_lay", sectionId: "lay51", spanId: "l3" }, read: true });
const LAY_52 = hit({ extractionId: "ext_lay", sectionId: "lay52", title: "5.2 The characteristic equation", sourceId: "src_lay", sourceTitle: "Lay",
  jump: { extractionId: "ext_lay", sectionId: "lay52", spanId: "l9" } });

function view(over: Partial<CorrespondentsDto> = {}): CorrespondentsDto {
  return {
    extractionId: "ext_strang", sectionId: SECTION.id, status: "unchecked", learningObjects: [],
    search: {
      label: "found by search, not checked", correctableLearningObjectIds: ["lo_eigen", "lo_charpoly"],
      sources: [
        { sourceId: "src_axler", sourceTitle: "Axler", sections: [hit()] },
        { sourceId: "src_lay", sourceTitle: "Lay", sections: [LAY_51, LAY_52] },
      ],
    },
    checkableLearningObjectIds: ["lo_eigen", "lo_charpoly"],
    ...over,
  };
}

const QUIET_NONE = view({ status: "none", search: null });

function peekOf(target: CorrespondentSectionDto, texts: string[], page: number | null = null): { peek: CorrespondentPeekDto } {
  return { peek: {
    extractionId: target.extractionId, sectionId: target.sectionId, sourceId: target.sourceId, sourceTitle: target.sourceTitle,
    title: target.title, jumpSpanId: target.jump.spanId!, page,
    blocks: texts.map((text, index) => ({ spanId: index === 0 ? target.jump.spanId! : `${target.jump.spanId}_${index}`, blockType: "Text", page, text })),
    exposureEventIds: texts.map((_text, index) => `see_${index}`),
  } };
}

function operation(operationId: string, over: Record<string, unknown> = {}) {
  return { operation: { operationId, choice: "not_about", learningObjectIds: ["lo_eigen", "lo_charpoly"], undoOf: null, replayed: false, createdAt: "t", ...over } };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => { callback(0); return 0; });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

async function flush() {
  await act(async () => { await Promise.resolve(); await Promise.resolve(); });
}

async function mount(props: Partial<FindSectionProps> = {}) {
  const handlers = { onGoThere: vi.fn(), onCompare: vi.fn(), onError: vi.fn() };
  const utils = render(<FindSection extractionId="ext_strang" section={SECTION} {...handlers} {...props} />);
  await flush();
  return { ...utils, ...handlers };
}

async function pressFind(pressed: CorrespondentsDto = view()) {
  api.readerCorrespondents.mockResolvedValueOnce(pressed);
  fireEvent.click(screen.getByRole("button", { name: FIND_COPY.action }));
  await flush();
}

it("shows the pressed action in the footer after a quiet read that searches nothing", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  await mount();
  expect(api.readerCorrespondents).toHaveBeenCalledTimes(1);
  expect(api.readerCorrespondents).toHaveBeenCalledWith({ extractionId: "ext_strang", sectionId: "u61", searchFallback: false });
  expect(screen.getByRole("button", { name: "find this section in my other books ▸" })).toBeTruthy();
  // Unchecked hits never appear unasked.
  expect(screen.queryByText(/Invariant subspaces/)).toBeNull();
  expect(screen.queryByText(FIND_COPY.unchecked)).toBeNull();
});

it.each([
  ["judged coverage (CA5's one-line entry)", view({ status: "judged", search: null })],
  ["a protected section", view({ status: "withheld", search: null, message: "This section is protected material." })],
])("is hidden for %s", async (_name, quiet) => {
  api.readerCorrespondents.mockResolvedValueOnce(quiet);
  const { container } = await mount();
  expect(screen.queryByRole("button", { name: FIND_COPY.action })).toBeNull();
  expect(container.innerHTML).toBe("");
});

it("is hidden, with no error line, when the quiet read fails", async () => {
  api.readerCorrespondents.mockRejectedValueOnce({ code: "curriculum_disabled", message: "off" });
  const { container, onError } = await mount();
  expect(container.innerHTML).toBe("");
  expect(onError).not.toHaveBeenCalled();
});

it("pressed, lists the hits grouped by book, each found by search and not checked, with no treatment words", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  await mount();
  await pressFind();
  expect(api.readerCorrespondents).toHaveBeenLastCalledWith({ extractionId: "ext_strang", sectionId: "u61", searchFallback: true });
  const axler = screen.getByRole("group", { name: "Axler" });
  const lay = screen.getByRole("group", { name: "Lay" });
  expect(within(axler).getByText("§ 5.A Invariant subspaces")).toBeTruthy();
  expect(within(lay).getByText("§ 5.1 Eigenvectors and eigenvalues")).toBeTruthy();
  expect(within(lay).getByText("§ 5.2 The characteristic equation")).toBeTruthy();
  expect(screen.getAllByText(/found by search, not checked/)).toHaveLength(3);
  // A read section says so (a reading fact).
  expect(within(lay).getByText("found by search, not checked · read")).toBeTruthy();
  for (const word of ["introduces it", "develops it", "uses it", "mentions it"]) {
    expect(screen.queryByText(new RegExp(word))).toBeNull();
  }
  // Names, never a count of books or sections.
  expect(screen.queryByText(/\b[23] (books|sections)\b/)).toBeNull();
});

it("says so when the search found nothing, and offers a retry when it failed", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  await mount();
  await pressFind(view({ status: "none", search: { label: "x", sources: [], correctableLearningObjectIds: [] } }));
  expect(screen.getByText(FIND_COPY.nothing)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: FIND_COPY.fold }));
  api.readerCorrespondents.mockRejectedValueOnce(new Error("down"));
  fireEvent.click(screen.getByRole("button", { name: FIND_COPY.action }));
  await flush();
  expect(screen.getByText(new RegExp(FIND_COPY.failed))).toBeTruthy();
  api.readerCorrespondents.mockResolvedValueOnce(view());
  fireEvent.click(screen.getByRole("button", { name: FIND_COPY.retry }));
  await flush();
  expect(screen.getByText("§ 5.A Invariant subspaces")).toBeTruthy();
});

it("pressed on a section judged meanwhile, hides itself (CA5's list, not this one)", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  const { container } = await mount();
  await pressFind(view({ status: "judged", search: null }));
  expect(container.innerHTML).toBe("");
});

it("peeks at the section's first blocks in the rail, outlined, and Esc closes the peek and returns focus", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  api.readerCorrespondentPeek.mockResolvedValue(peekOf(hit(), ["Suppose T is an operator on V.", "A subspace U is invariant under T if Tu is in U."], 81));
  await mount();
  await pressFind();
  fireEvent.click(screen.getByRole("button", { name: "peek at Axler 5.A Invariant subspaces" }));
  await flush();
  // The hit's own section, read by the peek RPC (never the generic span read).
  expect(api.readerCorrespondentPeek).toHaveBeenCalledWith({ extractionId: "ext_axler", sectionId: "ax5a" });
  const peek = document.querySelector("[data-find-peek]") as HTMLElement;
  expect(peek.getAttribute("data-find-peek")).toBe("ext_axler/ax5a");
  expect(within(peek).getByText("Suppose T is an operator on V.")).toBeTruthy();
  expect(within(peek).getByText(/A subspace U is invariant/)).toBeTruthy();
  expect(within(peek).getByText(/Axler · 5\.A Invariant subspaces/)).toBeTruthy();
  const title = screen.getByText("§ 5.A Invariant subspaces");
  fireEvent.keyDown(title, { key: "Escape" });
  expect(document.querySelector("[data-find-peek]")).toBeNull();
  expect(document.activeElement).toBe(title);
  // Esc again folds the list back to the action.
  fireEvent.keyDown(title, { key: "Escape" });
  expect(screen.getByRole("button", { name: FIND_COPY.action })).toBeTruthy();
});

it("go there opens the other book at the section's jump locator (from the line and from the peek)", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  api.readerCorrespondentPeek.mockResolvedValue(peekOf(LAY_51, ["An eigenvector…"]));
  const { onGoThere } = await mount();
  await pressFind();
  fireEvent.click(screen.getByRole("button", { name: "go there: Axler 5.A Invariant subspaces" }));
  expect(onGoThere).toHaveBeenCalledWith({ sourceId: "src_axler", extractionId: "ext_axler", spanId: "a7" });
  fireEvent.click(screen.getByRole("button", { name: "peek at Lay 5.1 Eigenvectors and eigenvalues" }));
  await flush();
  const peek = document.querySelector("[data-find-peek]") as HTMLElement;
  fireEvent.click(within(peek).getByRole("button", { name: /go there/ }));
  expect(onGoThere).toHaveBeenLastCalledWith({ sourceId: "src_lay", extractionId: "ext_lay", spanId: "l3" });
});

it("keys: ↑↓ move between lines, Space peeks, ↵ goes there, c compares", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  api.readerCorrespondentPeek.mockResolvedValue(peekOf(LAY_51, ["An eigenvector…"]));
  const { onGoThere, onCompare } = await mount();
  await pressFind();
  const first = screen.getByText("§ 5.A Invariant subspaces");
  first.focus();
  fireEvent.keyDown(first, { key: "ArrowDown" });
  const second = screen.getByText("§ 5.1 Eigenvectors and eigenvalues");
  expect(document.activeElement).toBe(second);
  fireEvent.keyDown(second, { key: " " });
  await flush();
  expect(api.readerCorrespondentPeek).toHaveBeenCalledWith({ extractionId: "ext_lay", sectionId: "lay51" });
  fireEvent.keyDown(second, { key: "Enter" });
  expect(onGoThere).toHaveBeenCalledWith({ sourceId: "src_lay", extractionId: "ext_lay", spanId: "l3" });
  fireEvent.keyDown(second, { key: "c" });
  expect(onCompare).toHaveBeenCalledWith(LAY_51);
  // Wraps from the first line upward to the last.
  fireEvent.keyDown(second, { key: "ArrowUp" });
  fireEvent.keyDown(document.activeElement!, { key: "ArrowUp" });
  expect(document.activeElement).toBe(screen.getByText("§ 5.2 The characteristic equation"));
});

it("compare uses the given compare path; without one, no compare is offered", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  const { onCompare, unmount } = await mount();
  await pressFind();
  fireEvent.click(screen.getByRole("button", { name: "compare with Axler 5.A Invariant subspaces" }));
  expect(onCompare).toHaveBeenCalledWith(hit());
  unmount();
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  await mount({ onCompare: null });
  await pressFind();
  expect(screen.queryByRole("button", { name: /^compare with/ })).toBeNull();
});

it("not about this is one operation on this section and the hit, the line goes, and undo is an operation over it", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  api.readerCorrespondentDismiss.mockImplementation(async (input: { operationId: string; undoOf?: string | null }) =>
    operation(input.operationId, input.undoOf ? { choice: "none", undoOf: input.undoOf } : {}));
  await mount();
  await pressFind();
  fireEvent.click(screen.getByRole("button", { name: "not about this: Lay 5.2 The characteristic equation" }));
  await flush();
  expect(api.readerCorrespondentDismiss).toHaveBeenCalledTimes(1);
  const sent = api.readerCorrespondentDismiss.mock.calls[0][0];
  expect(sent).toEqual({ extractionId: "ext_strang", sectionId: "u61", targetExtractionId: "ext_lay", targetSectionId: "lay52",
    operationId: expect.stringMatching(/^ca5a_[A-Za-z0-9_-]+$/) });
  expect(screen.queryByText("§ 5.2 The characteristic equation")).toBeNull();
  expect(screen.getByText(/5\.2 The characteristic equation · not about this/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: FIND_COPY.whereThisGoes }));
  expect(screen.getByText(/never grades you/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: FIND_COPY.undo }));
  await flush();
  const undone = api.readerCorrespondentDismiss.mock.calls[1][0];
  expect(undone).toEqual({ extractionId: "ext_strang", sectionId: "u61", targetExtractionId: "ext_lay", targetSectionId: "lay52",
    operationId: expect.stringMatching(/^ca5a_/), undoOf: sent.operationId });
  expect(undone.operationId).not.toBe(sent.operationId);
  expect(screen.getByText("§ 5.2 The characteristic equation")).toBeTruthy();
});

it("F3: a correction that fails is said, nothing is sent to take it back, and pressing again resends the same operation", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  api.readerCorrespondentDismiss
    .mockRejectedValueOnce({ code: "internal", message: "The reply was lost." })
    .mockImplementation(async (input: { operationId: string }) => operation(input.operationId, { replayed: true }));
  const { onError } = await mount();
  await pressFind();
  fireEvent.click(screen.getByRole("button", { name: "not about this: Axler 5.A Invariant subspaces" }));
  await flush();
  expect(onError).toHaveBeenCalledWith("The reply was lost.");
  // No compensating request: the server either committed the whole operation or none of it.
  expect(api.readerCorrespondentDismiss).toHaveBeenCalledTimes(1);
  expect(screen.getByText("§ 5.A Invariant subspaces")).toBeTruthy();
  expect(screen.queryByRole("button", { name: FIND_COPY.undo })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "not about this: Axler 5.A Invariant subspaces" }));
  await flush();
  const [first, again] = api.readerCorrespondentDismiss.mock.calls.map((call) => call[0]);
  expect(again.operationId).toBe(first.operationId);
  expect(screen.getByText(/5\.A Invariant subspaces · not about this/)).toBeTruthy();
  expect(screen.getByRole("button", { name: FIND_COPY.undo })).toBeTruthy();
});

it("F6: a section with no LO still has not about this (the server records the pair)", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  api.readerCorrespondentDismiss.mockImplementation(async (input: { operationId: string }) => operation(input.operationId, { learningObjectIds: [] }));
  await mount();
  await pressFind(view({ search: { ...view().search!, correctableLearningObjectIds: [] }, checkableLearningObjectIds: [] }));
  fireEvent.click(screen.getByRole("button", { name: "not about this: Axler 5.A Invariant subspaces" }));
  await flush();
  expect(api.readerCorrespondentDismiss).toHaveBeenCalledWith(expect.objectContaining({ targetExtractionId: "ext_axler", targetSectionId: "ax5a" }));
  expect(screen.getByText(/5\.A Invariant subspaces · not about this/)).toBeTruthy();
});

it("F4: a correction started on one section never lands on the next one's list, nor its undo", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  const pending = deferred<ReturnType<typeof operation>>();
  api.readerCorrespondentDismiss.mockReturnValueOnce(pending.promise);
  const { rerender, onGoThere, onCompare, onError } = await mount();
  await pressFind();
  fireEvent.click(screen.getByRole("button", { name: "not about this: Lay 5.2 The characteristic equation" }));
  await flush();
  // Section B, whose search finds the same hit.
  api.readerCorrespondents.mockResolvedValueOnce(view({ status: "none", search: null, sectionId: "u62" }));
  rerender(<FindSection extractionId="ext_strang" section={{ id: "u62", label: "6.2 Diagonalizing", startSpanId: "s9" }}
    onGoThere={onGoThere} onCompare={onCompare} onError={onError} />);
  await flush();
  await pressFind(view({ sectionId: "u62" }));
  await act(async () => { pending.resolve(operation(api.readerCorrespondentDismiss.mock.calls[0][0].operationId)); await pending.promise; });
  await flush();
  expect(screen.getByText("§ 5.2 The characteristic equation")).toBeTruthy();
  expect(screen.queryByText(/· not about this/)).toBeNull();
  expect(screen.queryByRole("button", { name: FIND_COPY.undo })).toBeNull();
  // B's own line is still correctable, under B.
  api.readerCorrespondentDismiss.mockImplementation(async (input: { operationId: string }) => operation(input.operationId));
  fireEvent.click(screen.getByRole("button", { name: "not about this: Lay 5.2 The characteristic equation" }));
  await flush();
  expect(api.readerCorrespondentDismiss).toHaveBeenLastCalledWith(expect.objectContaining({ sectionId: "u62", targetSectionId: "lay52" }));
});

it("F4: a peek answered after the section changed never opens", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  const pending = deferred<{ peek: CorrespondentPeekDto }>();
  api.readerCorrespondentPeek.mockReturnValueOnce(pending.promise);
  const { rerender, onGoThere, onCompare, onError } = await mount();
  await pressFind();
  fireEvent.click(screen.getByRole("button", { name: "peek at Axler 5.A Invariant subspaces" }));
  api.readerCorrespondents.mockResolvedValueOnce(view({ status: "none", search: null, sectionId: "u62" }));
  rerender(<FindSection extractionId="ext_strang" section={{ id: "u62", label: "6.2 Diagonalizing", startSpanId: "s9" }}
    onGoThere={onGoThere} onCompare={onCompare} onError={onError} />);
  await flush();
  await pressFind(view({ sectionId: "u62" }));
  await act(async () => { pending.resolve(peekOf(hit(), ["Suppose T is an operator on V."])); await pending.promise; });
  await flush();
  expect(document.querySelector("[data-find-peek]")).toBeNull();
});

it("F1: a peek the server refuses (protected now) says so and closes", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  api.readerCorrespondentPeek.mockRejectedValueOnce({ code: "withheld", message: "This section is protected material: it has no correspondents." });
  const { onError } = await mount();
  await pressFind();
  fireEvent.click(screen.getByRole("button", { name: "peek at Axler 5.A Invariant subspaces" }));
  await flush();
  expect(onError).toHaveBeenCalledWith("This section is protected material: it has no correspondents.");
  expect(document.querySelector("[data-find-peek]")).toBeNull();
});

it("F1: the peek shows exactly the blocks the server returned, the first outlined", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  api.readerCorrespondentPeek.mockResolvedValueOnce(peekOf(LAY_52, ["5.2 The characteristic equation", "The eigenvalues of A are the roots."], 2));
  await mount();
  await pressFind();
  fireEvent.click(screen.getByRole("button", { name: "peek at Lay 5.2 The characteristic equation" }));
  await flush();
  const peek = document.querySelector("[data-find-peek]") as HTMLElement;
  const shown = Array.from(peek.querySelectorAll("[data-peek-span]")).map((node) => node.getAttribute("data-peek-span"));
  expect(shown).toEqual(["l9", "l9_1"]);
  expect((peek.querySelector("[data-peek-span='l9']") as HTMLElement).style.outline).toContain("1px solid");
  expect((peek.querySelector("[data-peek-span='l9_1']") as HTMLElement).style.outline).toBe("");
  expect(within(peek).getAllByText(/p\.2\b/).length).toBeGreaterThan(0);
});

it("F7: closing a pending search keeps it closed when the answer lands", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  await mount();
  const pending = deferred<CorrespondentsDto>();
  api.readerCorrespondents.mockReturnValueOnce(pending.promise);
  fireEvent.click(screen.getByRole("button", { name: FIND_COPY.action }));
  await flush();
  expect(screen.getByText(FIND_COPY.looking)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: FIND_COPY.fold }));
  await act(async () => { pending.resolve(view()); await pending.promise; });
  await flush();
  expect(screen.queryByText("§ 5.A Invariant subspaces")).toBeNull();
  expect(screen.getByRole("button", { name: FIND_COPY.action })).toBeTruthy();
});

it("F7: two searches answered in reverse order show the newer one", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  await mount();
  const older = deferred<CorrespondentsDto>();
  const newer = deferred<CorrespondentsDto>();
  api.readerCorrespondents.mockReturnValueOnce(older.promise).mockReturnValueOnce(newer.promise);
  fireEvent.click(screen.getByRole("button", { name: FIND_COPY.action }));
  fireEvent.click(screen.getByRole("button", { name: FIND_COPY.fold }));
  fireEvent.click(screen.getByRole("button", { name: FIND_COPY.action }));
  await act(async () => {
    newer.resolve(view({ search: { ...view().search!, sources: [{ sourceId: "src_lay", sourceTitle: "Lay", sections: [LAY_51] }] } }));
    await newer.promise;
  });
  await act(async () => { older.resolve(view()); await older.promise; });
  await flush();
  expect(screen.getByText("§ 5.1 Eigenvectors and eigenvalues")).toBeTruthy();
  expect(screen.queryByText("§ 5.A Invariant subspaces")).toBeNull();
});

it("a new section folds the list and reads quietly again", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  const { rerender, onGoThere, onCompare, onError } = await mount();
  await pressFind();
  api.readerCorrespondents.mockResolvedValueOnce(view({ status: "judged", search: null, sectionId: "u62" }));
  rerender(<FindSection extractionId="ext_strang" section={{ id: "u62", label: "6.2 Diagonalizing", startSpanId: "s9" }}
    onGoThere={onGoThere} onCompare={onCompare} onError={onError} />);
  await flush();
  expect(api.readerCorrespondents).toHaveBeenLastCalledWith({ extractionId: "ext_strang", sectionId: "u62", searchFallback: false });
  expect(screen.queryByText("§ 5.A Invariant subspaces")).toBeNull();
  expect(screen.queryByRole("button", { name: FIND_COPY.action })).toBeNull();
});

it("the Guide draws it in its footer slot, and draws nothing there without it", () => {
  const props = {
    visible: true, extractionId: "ext", offline: false, guidePlan: null, guideLoading: false, currentGuideSection: null,
    currentSectionProgress: 0, currentQuestionOpen: false, boundaryChecksAvailable: false, authoringSections: [],
    revealedSections: [], completedSections: [], annotatedSpans: new Set<string>(), openQuestionSections: [],
    setDismissedSections: vi.fn(), jumpToSpan: vi.fn(), revealSection: vi.fn(), completeSection: vi.fn(), onError: vi.fn(),
    boundaryBlock: null, boundarySkipped: false, setBoundarySkipped: vi.fn(), boundaryAnswered: false, setBoundaryAnswered: vi.fn(),
    boundaryResponse: "", setBoundaryResponse: vi.fn(), boundarySubmitted: false, setBoundarySubmitted: vi.fn(),
    questionControl: null, sendQuestionControl: vi.fn(), disposition: null, chooseDisposition: vi.fn(),
  } as unknown as GuideRailProps;
  const { rerender } = render(<GuideRail {...props} findSection={<div data-testid="find" />} footer={<div data-testid="footer" />} />);
  const find = screen.getByTestId("find");
  expect(find.compareDocumentPosition(screen.getByTestId("footer")) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  rerender(<GuideRail {...props} footer={<div data-testid="footer" />} />);
  expect(screen.queryByTestId("find")).toBeNull();
});

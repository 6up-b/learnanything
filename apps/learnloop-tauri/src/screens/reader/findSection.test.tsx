// Reader CA5a: find this section in my other books (ux_reader_compare_ask_v1
// §6.2, §6.3, X7): the Guide footer's pressed action, the unchecked hits by
// book, peek and go there, compare, "not about this" with undo, and the hidden
// cases (judged coverage, a protected section, a failed quiet read).
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { CorrespondentSectionDto, CorrespondentsDto } from "../../api/dto";
import { FIND_COPY, FindSection, type FindSectionProps } from "./FindSection";
import { GuideRail, type GuideRailProps } from "./GuideRail";

const { api } = vi.hoisted(() => ({ api: {
  readerCorrespondents: vi.fn(), curriculumCoverageCorrect: vi.fn(), getSpanView: vi.fn(),
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
  api.getSpanView.mockResolvedValue({ spanView: {
    extractionId: "ext_axler", spanId: "a7", page: 81, text: "Suppose T is an operator on V.", previousSpans: [],
    nextSpans: [{ spanId: "a8", text: "A subspace U is invariant under T if Tu is in U." }],
  } });
  await mount();
  await pressFind();
  fireEvent.click(screen.getByRole("button", { name: "peek at Axler 5.A Invariant subspaces" }));
  await flush();
  expect(api.getSpanView).toHaveBeenCalledWith({ extractionId: "ext_axler", spanId: "a7", context: "library" });
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
  api.getSpanView.mockResolvedValue({ spanView: { extractionId: "ext_lay", spanId: "l3", page: null, text: "An eigenvector…", previousSpans: [], nextSpans: [] } });
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
  api.getSpanView.mockResolvedValue({ spanView: { extractionId: "ext_lay", spanId: "l3", page: null, text: "An eigenvector…", previousSpans: [], nextSpans: [] } });
  const { onGoThere, onCompare } = await mount();
  await pressFind();
  const first = screen.getByText("§ 5.A Invariant subspaces");
  first.focus();
  fireEvent.keyDown(first, { key: "ArrowDown" });
  const second = screen.getByText("§ 5.1 Eigenvectors and eigenvalues");
  expect(document.activeElement).toBe(second);
  fireEvent.keyDown(second, { key: " " });
  await flush();
  expect(api.getSpanView).toHaveBeenCalledWith({ extractionId: "ext_lay", spanId: "l3", context: "library" });
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

it("not about this records C0a's correction for each of the section's LOs, the line goes, and undo clears it", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  api.curriculumCoverageCorrect.mockResolvedValue({ correction: {} });
  await mount();
  await pressFind();
  fireEvent.click(screen.getByRole("button", { name: "not about this: Lay 5.2 The characteristic equation" }));
  await flush();
  expect(api.curriculumCoverageCorrect.mock.calls.map((call) => call[0])).toEqual([
    { extractionId: "ext_lay", sectionId: "lay52", learningObjectId: "lo_eigen", choice: "not_about" },
    { extractionId: "ext_lay", sectionId: "lay52", learningObjectId: "lo_charpoly", choice: "not_about" },
  ]);
  expect(screen.queryByText("§ 5.2 The characteristic equation")).toBeNull();
  expect(screen.getByText(/5\.2 The characteristic equation · not about this/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: FIND_COPY.whereThisGoes }));
  expect(screen.getByText(/never grades you/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: FIND_COPY.undo }));
  await flush();
  expect(api.curriculumCoverageCorrect.mock.calls.slice(2).map((call) => call[0])).toEqual([
    { extractionId: "ext_lay", sectionId: "lay52", learningObjectId: "lo_eigen", choice: "none" },
    { extractionId: "ext_lay", sectionId: "lay52", learningObjectId: "lo_charpoly", choice: "none" },
  ]);
  expect(screen.getByText("§ 5.2 The characteristic equation")).toBeTruthy();
});

it("a correction that fails part way is taken back and said", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  api.curriculumCoverageCorrect
    .mockResolvedValueOnce({ correction: {} })
    .mockRejectedValueOnce({ code: "withheld", message: "This section is protected material." })
    .mockResolvedValue({ correction: {} });
  const { onError } = await mount();
  await pressFind();
  fireEvent.click(screen.getByRole("button", { name: "not about this: Axler 5.A Invariant subspaces" }));
  await flush();
  await flush();
  expect(onError).toHaveBeenCalledWith("This section is protected material.");
  expect(api.curriculumCoverageCorrect).toHaveBeenLastCalledWith(
    { extractionId: "ext_axler", sectionId: "ax5a", learningObjectId: "lo_eigen", choice: "none" });
  expect(screen.getByText("§ 5.A Invariant subspaces")).toBeTruthy();
});

it("with no LO on this section there is nothing to correct against, so no not about this", async () => {
  api.readerCorrespondents.mockResolvedValueOnce(QUIET_NONE);
  await mount();
  await pressFind(view({ search: { ...view().search!, correctableLearningObjectIds: [] } }));
  expect(screen.getByText("§ 5.A Invariant subspaces")).toBeTruthy();
  expect(screen.queryByRole("button", { name: /not about this/ })).toBeNull();
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

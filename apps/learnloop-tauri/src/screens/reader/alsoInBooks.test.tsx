// Reader CA5: "also in your books" (ux_reader_compare_ask_v1 §6.2, §6.3, §6.5):
// the Guide's one dim line over judged coverage (names, never counts; nothing
// without judged coverage; unchecked hits never put it on screen), its list by
// LO (treatments in plain words, the notation line in LearnLoop's voice, the
// kept relation, read marks, one section once with "also: …" on focus), the
// keys, the corrections with undo, "also about…", hiding it, and CA5a's
// deferred events.
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { CorrespondentPeekDto, CorrespondentSectionDto, CorrespondentsDto } from "../../api/dto";
import { ALSO_COPY, AlsoInBooks, alsoGroups, bookShort, lineNames, sectionShort, type AlsoInBooksProps } from "./AlsoInBooks";

const { api, log } = vi.hoisted(() => ({
  api: {
    readerCorrespondents: vi.fn(), readerCorrespondentPeek: vi.fn(), readerCorrespondentDismiss: vi.fn(), curriculumAlsoAbout: vi.fn(),
  },
  log: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("./activity", () => ({ logReaderAction: log }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const SECTION = { id: "u61", label: "6.1 Introduction to eigenvalues", startSpanId: "s1" };

function line(over: Partial<CorrespondentSectionDto> = {}): CorrespondentSectionDto {
  return {
    extractionId: "ext_axler", sectionId: "ax5a", title: "5.A Invariant subspaces", sourceId: "src_axler", sourceTitle: "Axler",
    read: false, jump: { extractionId: "ext_axler", sectionId: "ax5a", spanId: "a7" }, treatment: "introduces",
    treatmentWords: "introduces it", by: "judge", notation: null, notationLabel: null, roles: ["definition"], linkedByYou: false,
    kept: [], alsoLearningObjectIds: [], ...over,
  };
}

const AXLER = line();
const LAY_51 = line({ extractionId: "ext_lay", sectionId: "lay51", title: "5.1 Eigenvectors and eigenvalues", sourceId: "src_lay", sourceTitle: "Lay",
  jump: { extractionId: "ext_lay", sectionId: "lay51", spanId: "l3" }, treatment: "develops", treatmentWords: "develops it",
  notation: "uses row vectors", notationLabel: "LearnLoop's note (AI-written)", read: true });
const LAY_52 = line({ extractionId: "ext_lay", sectionId: "lay52", title: "5.2 The characteristic equation", sourceId: "src_lay", sourceTitle: "Lay",
  jump: { extractionId: "ext_lay", sectionId: "lay52", spanId: "l9" }, treatment: "develops", treatmentWords: "develops it",
  kept: [{ askId: "la_1", keptAt: "t", relations: ["different_notation"] }], alsoLearningObjectIds: ["lo_charpoly"] });
const LAY_52_UNDER_CHARPOLY = { ...LAY_52, alsoLearningObjectIds: ["lo_eigen"] };
const LAY_53 = line({ extractionId: "ext_lay", sectionId: "lay53", title: "5.3 Diagonalization", sourceId: "src_lay", sourceTitle: "Lay",
  jump: { extractionId: "ext_lay", sectionId: "lay53", spanId: "l20" }, treatment: "applies", treatmentWords: "uses it" });

function judged(over: Partial<CorrespondentsDto> = {}): CorrespondentsDto {
  return {
    extractionId: "ext_strang", sectionId: SECTION.id, status: "judged", search: null,
    learningObjects: [
      { learningObjectId: "lo_eigen", title: "eigenvalues of a linear map", sources: [
        { sourceId: "src_axler", sourceTitle: "Axler", sections: [AXLER] },
        { sourceId: "src_lay", sourceTitle: "Lay", sections: [LAY_51, LAY_52] },
      ] },
      { learningObjectId: "lo_charpoly", title: "the characteristic polynomial", sources: [
        { sourceId: "src_lay", sourceTitle: "Lay", sections: [LAY_52_UNDER_CHARPOLY, LAY_53] },
      ] },
    ],
    checkableLearningObjectIds: ["lo_eigen", "lo_charpoly"],
    ...over,
  };
}

function peekOf(target: CorrespondentSectionDto, texts: string[]): { peek: CorrespondentPeekDto } {
  return { peek: {
    extractionId: target.extractionId, sectionId: target.sectionId, sourceId: target.sourceId, sourceTitle: target.sourceTitle,
    title: target.title, jumpSpanId: target.jump.spanId!, page: 12,
    blocks: texts.map((text, index) => ({ spanId: `${target.jump.spanId}_${index}`, blockType: "Text", page: 12, text })),
    exposureEventIds: texts.map((_t, index) => `see_${index}`),
  } };
}

function operation(operationId: string, over: Record<string, unknown> = {}) {
  return { operation: { operationId, choice: "not_about", learningObjectIds: ["lo_eigen"], undoOf: null, replayed: false, createdAt: "t", ...over } };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  log.mockReset();
  vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => { callback(0); return 0; });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

async function flush() {
  await act(async () => { for (let i = 0; i < 6; i += 1) await Promise.resolve(); });
}

async function mount(props: Partial<AlsoInBooksProps> = {}, answer: CorrespondentsDto | Error = judged()) {
  if (answer instanceof Error) api.readerCorrespondents.mockRejectedValueOnce(answer);
  else api.readerCorrespondents.mockResolvedValueOnce(answer);
  const handlers = {
    onHide: vi.fn(), onGoThere: vi.fn(), onCompare: vi.fn(), onError: vi.fn(), onPeekChange: vi.fn(),
    onCoverageChanged: vi.fn(), onAvailableChange: vi.fn(),
  };
  const utils = render(<AlsoInBooks extractionId="ext_strang" section={SECTION} hidden={false} {...handlers} {...props} />);
  await flush();
  return { ...utils, ...handlers };
}

function collapsed() {
  return document.querySelector<HTMLButtonElement>("[data-also-collapsed]");
}

async function expand() {
  fireEvent.click(collapsed()!);
  await flush();
}

function title(target: CorrespondentSectionDto): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>(`[data-also-line="${target.extractionId}/${target.sectionId}"] [data-also-title]`)!;
}

// -- the one line ------------------------------------------------------------------------------------

it("names the books' sections in one dim line, read quietly (judged coverage only, no search)", async () => {
  const { onAvailableChange } = await mount();
  expect(api.readerCorrespondents).toHaveBeenCalledTimes(1);
  expect(api.readerCorrespondents).toHaveBeenCalledWith({ extractionId: "ext_strang", sectionId: "u61", searchFallback: false });
  const text = collapsed()!.textContent!;
  expect(text.startsWith("also in Axler §5.A, Lay §5.1")).toBe(true);
  expect(text.endsWith("▸")).toBe(true);
  // Names, never a count.
  expect(text).not.toMatch(/\b\d+ (books?|sections?)\b/);
  expect(onAvailableChange).toHaveBeenLastCalledWith(true);
});

it("ends with 'and others' when the names do not fit, still names", async () => {
  const many = Array.from({ length: 8 }, (_v, index) => line({
    extractionId: `ext_${index}`, sectionId: `s${index}`, sourceId: `src_${index}`, sourceTitle: `Book number ${index}`,
    title: `${index}.1 Eigen things`, jump: { extractionId: `ext_${index}`, sectionId: `s${index}`, spanId: `x${index}` },
  }));
  await mount({}, judged({ learningObjects: [{ learningObjectId: "lo_eigen", title: "eigenvalues", sources: many.map((section) => ({
    sourceId: section.sourceId, sourceTitle: section.sourceTitle, sections: [section] })) }] }));
  const text = collapsed()!.textContent!;
  expect(text).toContain("Book number 0 §0.1");
  expect(text.endsWith(`${ALSO_COPY.others} ▸`)).toBe(true);
  expect(text).not.toContain("Book number 7");
});

it.each([
  ["no coverage judged", judged({ status: "none", learningObjects: [] })],
  ["only unchecked search hits", judged({ status: "unchecked", learningObjects: [], search: { label: "found by search, not checked", correctableLearningObjectIds: [], sources: [
    { sourceId: "src_axler", sourceTitle: "Axler", sections: [line({ by: "search", treatment: null, label: "found by search, not checked" })] }] } })],
  ["a protected section", judged({ status: "withheld", learningObjects: [] })],
])("shows nothing at all for %s (no ghost line)", async (_name, answer) => {
  const { container, onAvailableChange } = await mount({}, answer);
  expect(container.innerHTML).toBe("");
  expect(onAvailableChange).not.toHaveBeenCalledWith(true);
});

it("shows nothing when the quiet read fails, and says nothing about it", async () => {
  const { container, onError } = await mount({}, new Error("sidecar busy"));
  expect(container.innerHTML).toBe("");
  expect(onError).not.toHaveBeenCalled();
});

it("hidden by the learner, leaves nothing behind", async () => {
  const { container } = await mount({ hidden: true });
  expect(container.innerHTML).toBe("");
});

it("never lists a search hit even inside a judged answer", () => {
  const groups = alsoGroups(judged({ learningObjects: [{ learningObjectId: "lo", title: "t", sources: [
    { sourceId: "src_axler", sourceTitle: "Axler", sections: [line({ by: "search" }), LAY_51] }] }] }));
  expect(groups[0].lines.map((entry) => entry.key)).toEqual(["ext_lay/lay51"]);
});

it("shortens a book to its title before a subtitle, and a section to its own number", () => {
  expect(sectionShort("5.A Invariant subspaces")).toBe("5.A");
  expect(sectionShort("Section 6.1 Inner products")).toBe("6.1");
  expect(sectionShort("Eigenvalues and you")).toBe("Eigenvalues and you");
  expect(bookShort("Linear Algebra Done Right: Fourth Edition")).toBe("Linear Algebra Done…");
  expect(lineNames(alsoGroups(judged()).flatMap((group) => group.lines)).names[0]).toBe("Axler §5.A");
});

// -- the list ---------------------------------------------------------------------------------------

it("expands into the list by LO in the API's order, each section once, in plain words", async () => {
  await mount();
  await expand();
  const list = screen.getByRole("list", { name: ALSO_COPY.title });
  const groups = within(list).getAllByRole("group");
  expect(groups.map((group) => group.getAttribute("aria-label"))).toEqual(["eigenvalues of a linear map", "the characteristic polynomial"]);
  // Lay §5.2 is under its first LO only.
  expect(within(groups[0]).getByText(/5\.2 The characteristic equation/)).toBeTruthy();
  expect(within(groups[1]).queryByText(/5\.2 The characteristic equation/)).toBeNull();
  expect(within(groups[1]).getByText(/5\.3 Diagonalization/)).toBeTruthy();
  // Treatments in words, the kept relation, the read mark; no model-written pair relation.
  expect(within(groups[0]).getByText("introduces it")).toBeTruthy();
  expect(within(groups[0]).getByText("develops it · read")).toBeTruthy();
  expect(within(groups[0]).getByText("develops it · you compared these: different notation")).toBeTruthy();
  expect(within(groups[1]).getByText("uses it")).toBeTruthy();
  // The notation line is LearnLoop's voice, labelled as its note.
  const notation = document.querySelector<HTMLElement>("[data-also-notation]")!;
  expect(notation.dataset.voice).toBe("model");
  expect(notation.textContent).toContain("uses row vectors");
  expect(notation.textContent).toContain("LearnLoop's note (AI-written)");
  expect(notation.textContent).not.toContain("◇");
  expect(screen.getByText(/space peek · ↵ go there · c compare · ⋯ not about this/)).toBeTruthy();
  expect(screen.queryByText(/s side by side/)).toBeNull();
});

it("on focus, the notation gets its ◇ and a section under two LOs says 'also: …'", async () => {
  await mount();
  await expand();
  act(() => { title(LAY_52).focus(); });
  expect(document.querySelector("[data-also-also]")!.textContent).toBe("also: the characteristic polynomial");
  act(() => { title(LAY_51).focus(); });
  expect(document.querySelector("[data-also-also]")).toBeNull();
  expect(document.querySelector("[data-also-notation]")!.textContent).toContain("◇ uses row vectors");
});

// -- keys --------------------------------------------------------------------------------------------

it("↑↓ move, Space peeks through the protected peek with a crumb, Esc closes it then folds", async () => {
  const { onPeekChange } = await mount();
  await expand();
  act(() => { title(AXLER).focus(); });
  fireEvent.keyDown(title(AXLER), { key: "ArrowDown" });
  expect(document.activeElement).toBe(title(LAY_51));
  fireEvent.keyDown(title(LAY_51), { key: "ArrowUp" });
  fireEvent.keyDown(title(AXLER), { key: "ArrowUp" });
  expect(document.activeElement).toBe(title(LAY_53));
  api.readerCorrespondentPeek.mockResolvedValueOnce(peekOf(LAY_51, ["An eigenvector of A…", "Second block"]));
  act(() => { title(LAY_51).focus(); });
  fireEvent.keyDown(title(LAY_51), { key: " " });
  await flush();
  expect(api.readerCorrespondentPeek).toHaveBeenCalledWith({ extractionId: "ext_lay", sectionId: "lay51" });
  expect(document.querySelector('[data-also-peek="ext_lay/lay51"]')).toBeTruthy();
  expect(screen.getByText("An eigenvector of A…")).toBeTruthy();
  expect(onPeekChange).toHaveBeenLastCalledWith({ label: "peek Lay §5.1" });
  expect(log).toHaveBeenCalledWith("corresponding_section_peeked", expect.objectContaining({
    extraction_id: "ext_strang", section_id: "u61", target_extraction_id: "ext_lay", target_section_id: "lay51",
    target_source_id: "src_lay", by: "judged", via: "also_list",
  }));
  fireEvent.keyDown(title(LAY_51), { key: "Escape" });
  expect(document.querySelector("[data-also-peek]")).toBeNull();
  expect(onPeekChange).toHaveBeenLastCalledWith(null);
  expect(document.activeElement).toBe(title(LAY_51));
  fireEvent.keyDown(title(LAY_51), { key: "Escape" });
  expect(document.querySelector("[data-also-expanded]")).toBeNull();
  expect(document.activeElement).toBe(collapsed());
});

it("↵ goes there through the Reader's detour and records it; c compares; s is a seam until CA6", async () => {
  const onSideBySide = vi.fn();
  const { onGoThere, onCompare } = await mount();
  await expand();
  act(() => { title(AXLER).focus(); });
  fireEvent.keyDown(title(AXLER), { key: "s" });
  expect(onSideBySide).not.toHaveBeenCalled();
  fireEvent.keyDown(title(AXLER), { key: "Enter" });
  expect(onGoThere).toHaveBeenCalledWith({ sourceId: "src_axler", extractionId: "ext_axler", spanId: "a7" });
  expect(log).toHaveBeenCalledWith("corresponding_section_opened", expect.objectContaining({ target_section_id: "ax5a", via: "also_list" }));
  fireEvent.keyDown(title(AXLER), { key: "c" });
  expect(onCompare).toHaveBeenCalledWith(AXLER);
  cleanup();
  // With CA6's entry passed, `s` opens side by side and is offered.
  await mount({ onSideBySide });
  await expand();
  act(() => { title(LAY_51).focus(); });
  fireEvent.keyDown(title(LAY_51), { key: "s" });
  expect(onSideBySide).toHaveBeenCalledWith(LAY_51);
  expect(screen.getByText(/s side by side/)).toBeTruthy();
});

it("comparing off: c does nothing and is not offered", async () => {
  await mount({ onCompare: null });
  await expand();
  act(() => { title(AXLER).focus(); });
  fireEvent.keyDown(title(AXLER), { key: "c" });
  expect(screen.queryByText(/c compare/)).toBeNull();
});

it("the Reader's x opens the list at its first line", async () => {
  const { rerender, ...handlers } = await mount();
  expect(document.querySelector("[data-also-expanded]")).toBeNull();
  rerender(<AlsoInBooks extractionId="ext_strang" section={SECTION} hidden={false} {...handlers} expandToken={1} />);
  await flush();
  expect(document.querySelector("[data-also-expanded]")).toBeTruthy();
  expect(document.activeElement).toBe(title(AXLER));
});

it("the detour strip's crumb closes the peek", async () => {
  const { rerender, ...handlers } = await mount();
  await expand();
  api.readerCorrespondentPeek.mockResolvedValueOnce(peekOf(AXLER, ["Invariant subspaces…"]));
  fireEvent.click(title(AXLER));
  await flush();
  expect(document.querySelector("[data-also-peek]")).toBeTruthy();
  rerender(<AlsoInBooks extractionId="ext_strang" section={SECTION} hidden={false} {...handlers} closePeekToken={1} />);
  await flush();
  expect(document.querySelector("[data-also-peek]")).toBeNull();
});

// -- corrections ----------------------------------------------------------------------------------

it("⋯ not about this is CA5a's one operation over the line's shared LOs, with undo", async () => {
  const { onCoverageChanged } = await mount();
  await expand();
  fireEvent.click(screen.getByRole("button", { name: "⋯ Lay 5.2 The characteristic equation" }));
  api.readerCorrespondentDismiss.mockResolvedValueOnce(operation("op_1", { learningObjectIds: ["lo_eigen", "lo_charpoly"] }));
  fireEvent.click(screen.getByRole("menuitem", { name: ALSO_COPY.notAbout }));
  await flush();
  const input = api.readerCorrespondentDismiss.mock.calls[0][0];
  expect(input).toMatchObject({ extractionId: "ext_strang", sectionId: "u61", targetExtractionId: "ext_lay", targetSectionId: "lay52",
    learningObjectIds: ["lo_eigen", "lo_charpoly"] });
  expect(input.operationId).toMatch(/^ca5a_/);
  const gone = document.querySelector('[data-also-gone="ext_lay/lay52"]')!;
  expect(gone.textContent).toContain("not about this");
  expect(onCoverageChanged).toHaveBeenCalledTimes(1);
  // The collapsed line no longer names it.
  fireEvent.click(within(gone as HTMLElement).getByRole("button", { name: ALSO_COPY.whereThisGoes }));
  expect(screen.getByText(ALSO_COPY.whereThisGoesText)).toBeTruthy();
  api.readerCorrespondentDismiss.mockResolvedValueOnce(operation("op_2", { choice: "none", undoOf: "op_1" }));
  fireEvent.click(within(gone as HTMLElement).getByRole("button", { name: ALSO_COPY.undo }));
  await flush();
  expect(api.readerCorrespondentDismiss.mock.calls[1][0]).toMatchObject({ undoOf: "op_1", targetSectionId: "lay52" });
  expect(document.querySelector('[data-also-gone="ext_lay/lay52"]')).toBeNull();
  expect(title(LAY_52)).toBeTruthy();
});

it("a failed correction keeps the line and resends the same operation", async () => {
  const { onError } = await mount();
  await expand();
  fireEvent.click(screen.getByRole("button", { name: "⋯ Axler 5.A Invariant subspaces" }));
  api.readerCorrespondentDismiss.mockRejectedValueOnce(new Error("lost"));
  fireEvent.click(screen.getByRole("menuitem", { name: ALSO_COPY.notAbout }));
  await flush();
  expect(onError).toHaveBeenCalled();
  expect(title(AXLER)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "⋯ Axler 5.A Invariant subspaces" }));
  api.readerCorrespondentDismiss.mockResolvedValueOnce(operation("op_9"));
  fireEvent.click(screen.getByRole("menuitem", { name: ALSO_COPY.notAbout }));
  await flush();
  const [first, second] = api.readerCorrespondentDismiss.mock.calls.map((call) => call[0].operationId);
  expect(second).toBe(first);
});

it("⋯ also about… resolves the learner's words through C0b's resolver and reads the list again", async () => {
  const { onCoverageChanged } = await mount();
  await expand();
  fireEvent.click(screen.getByRole("button", { name: "⋯ Lay 5.3 Diagonalization" }));
  fireEvent.click(screen.getByRole("menuitem", { name: ALSO_COPY.alsoAbout }));
  const box = screen.getByRole("textbox", { name: "also about… 5.3 Diagonalization" });
  fireEvent.change(box, { target: { value: "this is really about orthogonal projection" } });
  api.curriculumAlsoAbout.mockResolvedValueOnce({ status: "corrected", learningObjectId: "lo_proj", title: "orthogonal projection" });
  api.readerCorrespondents.mockResolvedValueOnce(judged());
  fireEvent.keyDown(box, { key: "Enter" });
  await flush();
  expect(api.curriculumAlsoAbout).toHaveBeenCalledWith({ extractionId: "ext_lay", sectionId: "lay53", text: "this is really about orthogonal projection" });
  expect(document.querySelector("[data-also-about-result]")!.textContent).toBe("noted: also about orthogonal projection");
  expect(onCoverageChanged).toHaveBeenCalled();
  expect(api.readerCorrespondents).toHaveBeenCalledTimes(2);
});

it("also about… that matches no topic says so and writes nothing more", async () => {
  await mount();
  await expand();
  fireEvent.click(screen.getByRole("button", { name: "⋯ Axler 5.A Invariant subspaces" }));
  fireEvent.click(screen.getByRole("menuitem", { name: ALSO_COPY.alsoAbout }));
  const box = screen.getByRole("textbox");
  fireEvent.change(box, { target: { value: "knitting" } });
  api.curriculumAlsoAbout.mockResolvedValueOnce({ status: "unmatched", learningObjectId: null, message: "None of your topics matches those words yet." });
  fireEvent.keyDown(box, { key: "Enter" });
  await flush();
  expect(document.querySelector("[data-also-about-result]")!.textContent).toBe("None of your topics matches those words yet.");
  expect(api.readerCorrespondents).toHaveBeenCalledTimes(1);
});

// -- hiding ------------------------------------------------------------------------------------------

it("the block's ⋯ hides it for this book or everywhere", async () => {
  const { onHide } = await mount();
  fireEvent.click(screen.getByRole("button", { name: `${ALSO_COPY.title}: more` }));
  fireEvent.click(screen.getByRole("menuitem", { name: ALSO_COPY.hideBook }));
  expect(onHide).toHaveBeenCalledWith("book");
  fireEvent.click(screen.getByRole("button", { name: `${ALSO_COPY.title}: more` }));
  fireEvent.click(screen.getByRole("menuitem", { name: ALSO_COPY.hideEverywhere }));
  expect(onHide).toHaveBeenLastCalledWith("everywhere");
});

it("a late answer for the section left behind never lands", async () => {
  let resolve!: (value: CorrespondentsDto) => void;
  api.readerCorrespondents.mockReturnValueOnce(new Promise<CorrespondentsDto>((res) => { resolve = res; }));
  const handlers = { onHide: vi.fn(), onGoThere: vi.fn(), onCompare: vi.fn(), onError: vi.fn() };
  const { rerender } = render(<AlsoInBooks extractionId="ext_strang" section={SECTION} hidden={false} {...handlers} />);
  api.readerCorrespondents.mockResolvedValueOnce(judged({ status: "none", learningObjects: [] }));
  rerender(<AlsoInBooks extractionId="ext_strang" section={{ ...SECTION, id: "u62" }} hidden={false} {...handlers} />);
  await flush();
  resolve(judged());
  await flush();
  expect(collapsed()).toBeNull();
});

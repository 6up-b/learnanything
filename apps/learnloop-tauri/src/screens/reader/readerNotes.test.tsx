// Curriculum C2 (spec §10.2, §10.3): the learner's notes, linked, in their own voice:
// the › margin mark opens the note(s) with "linked by LearnLoop's model" and a one-tap
// hide (with undo); a Pocket Notes page says so; the path line says "your note from
// 3 Oct"; Compare's band offers *use as my take* with the note's quote; *link one of your
// notes…* searches tend (the section title first, then the learner's words) and links by
// hand. Without the notes context (notes.enabled off or no tend) nothing renders.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { NoteLinkDto } from "../../api/dto";
import { NotesContext, type NotesContextValue } from "./notesContext";
import {
  NOTES_COPY, NoteLinkPicker, NoteMarkButton, NotesTakeBand, PathLineNotes, noteLabel, passagesOfKeys,
} from "./ReaderNotes";

const { api } = vi.hoisted(() => ({
  api: { notesDecide: vi.fn(), notesPassages: vi.fn(), notesSearch: vi.fn(), notesLink: vi.fn(), notesMarks: vi.fn(), notesPath: vi.fn() },
}));
vi.mock("../../api/client", () => ({ api }));

const SETTINGS = { enabled: true, lexicalOnly: false, pocketNotesLabel: "handwritten · transcribed by Pocket Notes", takePrefix: "From your note" };

function link(overrides: Partial<NoteLinkDto> = {}, note: Partial<NoteLinkDto["note"]> = {}): NoteLinkDto {
  return {
    linkId: "nl_1", noteKey: "/n/a.org#Eigen", targetKind: "passage", learningObjectId: "lo_eigen", extractionId: "ext_book",
    sectionId: "ch_eigen", spanId: "s1", goalId: "g", authorship: "ai", byLabel: "linked by LearnLoop's model",
    how: "restates", howWords: "puts it in your words", howLine: "your note restates it", line: "your note from 3 Oct",
    note: { title: "Linear algebra", heading: "Eigen stuff", capturedOn: "2026-10-03", dateLabel: "3 Oct", origin: "tend",
            originLabel: null, text: "Eigenvalues: Av = lv.", truncated: false, ...note },
    ...overrides,
  };
}

function withNotes(children: ReactNode, onChanged = vi.fn()) {
  const value: NotesContextValue = { settings: SETTINGS, onChanged, revision: 0 };
  return <NotesContext.Provider value={value}>{children}</NotesContext.Provider>;
}

beforeEach(() => {
  Object.values(api).forEach((fn) => fn.mockReset());
});
afterEach(cleanup);

it("labels a note in the learner's voice with its title, heading and date", () => {
  expect(noteLabel(link())).toBe("your note · Linear algebra › Eigen stuff · 3 Oct");
  expect(passagesOfKeys(["ext_book:s1", "bad", "ext_lay:s9"])).toEqual([
    { extractionId: "ext_book", spanId: "s1" }, { extractionId: "ext_lay", spanId: "s9" }]);
});

it("the › mark opens the note, says who linked it, and one tap hides it (with undo)", async () => {
  const onChanged = vi.fn();
  api.notesDecide.mockResolvedValueOnce({ linkId: "nl_hide", status: "rejected" }).mockResolvedValueOnce({ linkId: "nl_keep", status: "accepted" });
  render(withNotes(<NoteMarkButton mark={{ spanId: "s1", notes: [link(), link({ linkId: "nl_2" }, { heading: "Eigen page", origin: "pocket_notes", originLabel: SETTINGS.pocketNotesLabel })] }} />, onChanged));
  const mark = screen.getByRole("button", { name: /2 of your notes on this passage/ });
  expect(mark.textContent).toBe("›");
  fireEvent.click(mark);
  expect(screen.getAllByText("Eigenvalues: Av = lv.", { exact: false })).toHaveLength(2);
  expect(screen.getAllByText("linked by LearnLoop's model")).toHaveLength(2);
  expect(screen.getByText(SETTINGS.pocketNotesLabel)).toBeTruthy();
  fireEvent.click(screen.getAllByRole("button", { name: NOTES_COPY.hide })[0]);
  await waitFor(() => expect(screen.getByText(NOTES_COPY.hidden)).toBeTruthy());
  expect(api.notesDecide).toHaveBeenCalledWith({ linkId: "nl_1", choice: "hide" });
  expect(onChanged).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("button", { name: NOTES_COPY.undo }));
  await waitFor(() => expect(api.notesDecide).toHaveBeenLastCalledWith({ linkId: "nl_hide", choice: "keep" }));
});

it("the path line says your note from its date and opens it", () => {
  render(withNotes(<PathLineNotes notes={[link()]} />));
  const line = screen.getByRole("button", { name: /your note from 3 Oct/ });
  fireEvent.click(line);
  expect(screen.getByText("Eigenvalues: Av = lv.", { exact: false })).toBeTruthy();
});

it("Compare's band offers use as my take with the note's quote", async () => {
  api.notesPassages.mockResolvedValue({ notes: [link({ takeText: "From your note “Linear algebra › Eigen stuff”, 3 Oct: “Eigenvalues: Av = lv.”" })] });
  const onUse = vi.fn();
  render(withNotes(<NotesTakeBand keys={["ext_book:s1"]} onUse={onUse} />));
  const use = await screen.findByRole("button", { name: NOTES_COPY.useAsMyTake });
  expect(api.notesPassages).toHaveBeenCalledWith({ passages: [{ extractionId: "ext_book", spanId: "s1" }] });
  fireEvent.click(use);
  expect(onUse).toHaveBeenCalledWith(expect.stringMatching(/^From your note “Linear algebra › Eigen stuff”/));
  expect(screen.queryByRole("button", { name: NOTES_COPY.useAsMyTake })).toBeNull();
});

it("link one of your notes searches the section first, then the learner's words, and links by hand", async () => {
  const onChanged = vi.fn();
  const hit = { noteKey: "/n/p.md#Eigen page", path: "/n/p.md", title: "2026-10-03", heading: "Eigen page", headingPath: "Eigen page",
                line: 1, snippet: "Worked the 2x2 eigen example", capturedOn: "2026-10-03", origin: "pocket_notes", contentHash: "h", mtime: 1 };
  api.notesSearch.mockResolvedValueOnce({ query: "Chapter 5 Eigenvalues", hits: [hit] }).mockResolvedValueOnce({ query: "my page", hits: [] });
  api.notesLink.mockResolvedValue({ linkId: "nl_9", marks: [] });
  render(withNotes(<NoteLinkPicker extractionId="ext_book" spanId="s2" onClose={vi.fn()} onError={vi.fn()} />, onChanged));
  await screen.findByText(/your notes for this section: Chapter 5 Eigenvalues/);
  expect(api.notesSearch).toHaveBeenNthCalledWith(1, { extractionId: "ext_book", spanId: "s2" });
  expect(screen.getByText(SETTINGS.pocketNotesLabel)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: NOTES_COPY.linkHere }));
  await waitFor(() => expect(api.notesLink).toHaveBeenCalledWith({
    note: { path: "/n/p.md", line: 1, headingPath: "Eigen page", title: "2026-10-03", contentHash: "h", mtime: 1 },
    extractionId: "ext_book", spanId: "s2" }));
  await screen.findByText(`${NOTES_COPY.linked} ✓`);
  expect(onChanged).toHaveBeenCalled();
  fireEvent.change(screen.getByRole("textbox", { name: NOTES_COPY.searchPlaceholder }), { target: { value: "my page" } });
  fireEvent.submit(screen.getByRole("textbox", { name: NOTES_COPY.searchPlaceholder }).closest("form")!);
  await screen.findByText(NOTES_COPY.nothingFound);
  expect(api.notesSearch).toHaveBeenLastCalledWith({ query: "my page" });
});

it("without the notes context nothing renders and nothing is read", () => {
  const { container } = render(<>
    <NotesTakeBand keys={["ext_book:s1"]} onUse={vi.fn()} />
    <NoteLinkPicker extractionId="ext_book" spanId="s2" onClose={vi.fn()} onError={vi.fn()} />
  </>);
  expect(container.textContent).toBe("");
  expect(api.notesPassages).not.toHaveBeenCalled();
});

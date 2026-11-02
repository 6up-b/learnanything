// Curriculum C5 (spec §10.2, §12 C5; owner Q9): the opt-in for linked notes to steer
// suggestions. Settings shows it only where the notes are (the contract's `notes`), off by
// default, with honest copy; the notes surfaces say *where this goes* only with the opt-in
// on, and without it they are today's exactly (no disclosure added to a note's card).
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { NoteLinkDto, NotesContractDto } from "../../api/dto";
import { NotesContext, type NotesContextValue } from "./notesContext";
import { NOTES_COPY, NoteMarkButton } from "./ReaderNotes";
import { NOTES_GAPS_COPY, NotesGapsSettings } from "./NotesGapsSettings";

const { api, invalidate } = vi.hoisted(() => ({
  api: { readerPromptContract: vi.fn(), notesSetGaps: vi.fn(), notesDecide: vi.fn() },
  invalidate: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../api/queryCache", () => ({ invalidate }));

const NOTES: NotesContractDto = { enabled: true, meaning: false, pocketNotesLabel: "handwritten", takePrefix: "From your note" };

function link(): NoteLinkDto {
  return {
    linkId: "nl_1", noteKey: "/n/a.org#Eigen", targetKind: "passage", learningObjectId: "lo_eigen", extractionId: "ext_book",
    sectionId: "ch_eigen", spanId: "s1", goalId: "g", authorship: "ai", byLabel: "linked by LearnLoop's model",
    how: "restates", howWords: "puts it in your words", howLine: "your note restates it", line: "your note from 3 Oct",
    note: { title: "Linear algebra", heading: "Eigen stuff", capturedOn: "2026-10-03", dateLabel: "3 Oct", origin: "vault",
            originLabel: null, text: "Eigenvalues: Av = lv.", truncated: false },
  };
}

function withNotes(settings: NotesContractDto, children: ReactNode) {
  const value: NotesContextValue = {
    settings, onChanged: vi.fn(), revision: 0, hidden: new Map(), remember: vi.fn(), forget: vi.fn(),
  };
  return <NotesContext.Provider value={value}>{children}</NotesContext.Provider>;
}

const row = { display: "flex" } as const;

beforeEach(() => {
  Object.values(api).forEach((fn) => fn.mockReset());
  invalidate.mockReset();
});
afterEach(cleanup);

it("Settings offers the opt-in, off by default, with honest copy, and turning it on saves it", async () => {
  api.readerPromptContract.mockResolvedValue({ notes: NOTES });
  api.notesSetGaps.mockResolvedValue({ gapsEnabled: true, line: "x" });
  const onToast = vi.fn();
  render(<NotesGapsSettings rowStyle={row} labelStyle={row} onToast={onToast} />);
  const box = await screen.findByRole("checkbox", { name: NOTES_GAPS_COPY.toggle });
  expect(box.getAttribute("aria-checked")).toBe("false");
  expect(screen.getByText(NOTES_GAPS_COPY.line)).toBeTruthy();
  expect(NOTES_GAPS_COPY.line).toContain("only ever steers what to suggest, never grades you");
  fireEvent.click(box);
  await waitFor(() => expect(api.notesSetGaps).toHaveBeenCalledWith({ enabled: true }));
  await waitFor(() => expect(box.getAttribute("aria-checked")).toBe("true"));
  expect(invalidate).toHaveBeenCalledWith({ key: ["reader_prompt_contract"] });
  expect(onToast).toHaveBeenCalledWith(NOTES_GAPS_COPY.on);
});

it("Settings turns it off again, and shows nothing where the notes are not", async () => {
  api.readerPromptContract.mockResolvedValueOnce({ notes: { ...NOTES, gaps: true } });
  api.notesSetGaps.mockResolvedValue({ gapsEnabled: false, line: "x" });
  const onToast = vi.fn();
  const { unmount } = render(<NotesGapsSettings rowStyle={row} labelStyle={row} onToast={onToast} />);
  const box = await screen.findByRole("checkbox", { name: NOTES_GAPS_COPY.toggle });
  expect(box.getAttribute("aria-checked")).toBe("true");
  fireEvent.click(box);
  await waitFor(() => expect(api.notesSetGaps).toHaveBeenCalledWith({ enabled: false }));
  await waitFor(() => expect(onToast).toHaveBeenCalledWith(NOTES_GAPS_COPY.off));
  unmount();
  api.readerPromptContract.mockResolvedValueOnce({});
  const { container } = render(<NotesGapsSettings rowStyle={row} labelStyle={row} onToast={onToast} />);
  await waitFor(() => expect(api.readerPromptContract).toHaveBeenCalledTimes(2));
  expect(container.querySelector("[data-notes-gaps-settings]")).toBeNull();
  expect(api.notesSetGaps).toHaveBeenCalledTimes(1);
});

it("with the opt-in on, an open note says where this goes: it only steers suggestions", () => {
  render(withNotes({ ...NOTES, gaps: true }, <NoteMarkButton mark={{ spanId: "s1", notes: [link()] }} />));
  fireEvent.click(screen.getByRole("button", { name: /your note from 3 Oct/ }));
  const where = screen.getByRole("button", { name: NOTES_COPY.whereThisGoes });
  fireEvent.click(where);
  expect(screen.getByText(NOTES_COPY.whereLine)).toBeTruthy();
  expect(screen.getByText(NOTES_COPY.gapsLine)).toBeTruthy();
  expect(NOTES_COPY.gapsLine).toContain("never grades you");
});

it("without the opt-in, an open note is today's: no disclosure is added", () => {
  const { container } = render(withNotes(NOTES, <NoteMarkButton mark={{ spanId: "s1", notes: [link()] }} />));
  fireEvent.click(screen.getByRole("button", { name: /your note from 3 Oct/ }));
  expect(screen.queryByRole("button", { name: NOTES_COPY.whereThisGoes })).toBeNull();
  expect(container.querySelector("[data-notes-where]")).toBeNull();
  expect(screen.queryByText(NOTES_COPY.gapsLine)).toBeNull();
});

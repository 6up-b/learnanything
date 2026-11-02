// Curriculum C2 (spec §10.2, §10.3): the learner's notes, linked, in their own voice:
// the › margin mark opens the note(s) with "linked by LearnLoop's model" and a one-tap
// hide (with undo); a Pocket Notes page says so; the path line says "your note from
// 3 Oct"; Compare's band offers *use as my take* with the note's quote; *link one of your
// notes…* searches the vault's own notes (the section title first, then the learner's words; by
// meaning only while the contract offers it) and links by hand. Without the notes context
// (notes.enabled off) nothing renders.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { NoteLinkDto } from "../../api/dto";
import { NotesContext, type HiddenNote, type NotesContextValue } from "./notesContext";
import {
  NOTES_COPY, NOTES_POLL_MS, NoteLinkPicker, NoteMarkButton, NotesTakeBand, PathLineNotes, mergeMarks, noteLabel,
  passagesOfKeys, retainHidden, useNoteMarks, usePathNotes,
} from "./ReaderNotes";

const { api } = vi.hoisted(() => ({
  api: { notesDecide: vi.fn(), notesPassages: vi.fn(), notesSearch: vi.fn(), notesLink: vi.fn(), notesMarks: vi.fn(), notesPath: vi.fn() },
}));
vi.mock("../../api/client", () => ({ api }));

const SETTINGS = { enabled: true, meaning: false, pocketNotesLabel: "handwritten · transcribed by Pocket Notes", takePrefix: "From your note" };

function link(overrides: Partial<NoteLinkDto> = {}, note: Partial<NoteLinkDto["note"]> = {}): NoteLinkDto {
  return {
    linkId: "nl_1", noteKey: "/n/a.org#Eigen", targetKind: "passage", learningObjectId: "lo_eigen", extractionId: "ext_book",
    sectionId: "ch_eigen", spanId: "s1", goalId: "g", authorship: "ai", byLabel: "linked by LearnLoop's model",
    how: "restates", howWords: "puts it in your words", howLine: "your note restates it", line: "your note from 3 Oct",
    note: { title: "Linear algebra", heading: "Eigen stuff", capturedOn: "2026-10-03", dateLabel: "3 Oct", origin: "vault",
            originLabel: null, text: "Eigenvalues: Av = lv.", truncated: false, ...note },
    ...overrides,
  };
}

/** A notes context as the Reader provides it (the hidden links kept with their undo). */
function TestNotes({ children, onChanged }: { children: ReactNode; onChanged: () => void }) {
  const [hidden, setHidden] = useState<ReadonlyMap<string, HiddenNote>>(new Map());
  const value: NotesContextValue = {
    settings: SETTINGS, onChanged, revision: 0, hidden,
    remember: (entry, hiddenId) => setHidden((current) => new Map(current).set(entry.linkId, { link: entry, hiddenId })),
    forget: (linkId) => setHidden((current) => { const next = new Map(current); next.delete(linkId); return next; }),
  };
  return <NotesContext.Provider value={value}>{children}</NotesContext.Provider>;
}

function withNotes(children: ReactNode, onChanged = vi.fn()) {
  return <TestNotes onChanged={onChanged}>{children}</TestNotes>;
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
  const onUse = vi.fn().mockResolvedValue("kept");
  render(withNotes(<NotesTakeBand keys={["ext_book:s1"]} onUse={onUse} />));
  const use = await screen.findByRole("button", { name: NOTES_COPY.useAsMyTake });
  expect(api.notesPassages).toHaveBeenCalledWith({ passages: [{ extractionId: "ext_book", spanId: "s1" }] });
  fireEvent.click(use);
  expect(onUse).toHaveBeenCalledWith(expect.stringMatching(/^From your note “Linear algebra › Eigen stuff”/));
  await waitFor(() => expect(screen.queryByRole("button", { name: NOTES_COPY.useAsMyTake })).toBeNull());
});

it("use as my take is marked used only once kept: a failure keeps the action, another comparison resets it (F11)", async () => {
  api.notesPassages.mockResolvedValue({ notes: [link({ takeText: "From your note: “Eigenvalues: Av = lv.”" })] });
  const onUse = vi.fn().mockResolvedValueOnce("failed").mockResolvedValueOnce("drafted").mockResolvedValueOnce("kept");
  const { rerender } = render(withNotes(<NotesTakeBand keys={["ext_book:s1"]} onUse={onUse} />));
  fireEvent.click(await screen.findByRole("button", { name: NOTES_COPY.useAsMyTake }));
  await waitFor(() => expect(onUse).toHaveBeenCalledTimes(1));
  // Failed: nothing saved, the action stays to try again.
  const again = await screen.findByRole("button", { name: NOTES_COPY.useAsMyTake });
  await waitFor(() => expect((again as HTMLButtonElement).disabled).toBe(false));
  // Put in the draft (kept with the comparison later): not marked used either.
  fireEvent.click(again);
  await waitFor(() => expect(onUse).toHaveBeenCalledTimes(2));
  // Kept: marked used.
  const third = await screen.findByRole("button", { name: NOTES_COPY.useAsMyTake });
  await waitFor(() => expect((third as HTMLButtonElement).disabled).toBe(false));
  fireEvent.click(third);
  await waitFor(() => expect(screen.queryByRole("button", { name: NOTES_COPY.useAsMyTake })).toBeNull());
  expect(screen.getByText("✓")).toBeTruthy();
  // Another comparison: its notes have not been used.
  rerender(withNotes(<NotesTakeBand keys={["ext_book:s1", "ext_other:o1"]} onUse={onUse} />));
  expect(await screen.findByRole("button", { name: NOTES_COPY.useAsMyTake })).toBeTruthy();
});

function MarksHarness() {
  const ctl = useNoteMarks({ settings: SETTINGS, extractionId: "ext_book", offline: false });
  return (
    <NotesContext.Provider value={ctl.context}>
      {[...ctl.marks.values()].map((mark) => <NoteMarkButton key={mark.spanId} mark={mark} />)}
    </NotesContext.Provider>
  );
}

it("a hidden note keeps its card and undo after the refresh its hide starts, even the passage's last note (F5)", async () => {
  api.notesMarks
    .mockResolvedValueOnce({ extractionId: "ext_book", marks: [{ spanId: "s1", notes: [link()] }] })
    .mockResolvedValueOnce({ extractionId: "ext_book", marks: [] }) // the server no longer lists the hidden link
    .mockResolvedValue({ extractionId: "ext_book", marks: [{ spanId: "s1", notes: [link()] }] });
  api.notesDecide.mockResolvedValueOnce({ linkId: "nl_hide", status: "rejected" }).mockResolvedValueOnce({ linkId: "nl_keep", status: "accepted" });
  render(<MarksHarness />);
  fireEvent.click(await screen.findByRole("button", { name: /your note from 3 Oct: open it/ }));
  fireEvent.click(screen.getByRole("button", { name: NOTES_COPY.hide }));
  await waitFor(() => expect(api.notesMarks).toHaveBeenCalledTimes(2));
  await waitFor(() => expect(screen.getByText(NOTES_COPY.hidden)).toBeTruthy());
  fireEvent.click(screen.getByRole("button", { name: NOTES_COPY.undo }));
  await waitFor(() => expect(api.notesDecide).toHaveBeenLastCalledWith({ linkId: "nl_hide", choice: "keep" }));
  await waitFor(() => expect(api.notesMarks).toHaveBeenCalledTimes(3));
  await waitFor(() => expect(screen.getByText("Eigenvalues: Av = lv.", { exact: false })).toBeTruthy());
  expect(screen.queryByText(NOTES_COPY.hidden)).toBeNull();
});

it("retainHidden and mergeMarks keep only hidden cards a refresh dropped, where they were", () => {
  const hidden = new Map([["nl_2", { link: link({ linkId: "nl_2" }), hiddenId: "nl_h" }]]);
  const a = link({ linkId: "nl_1" });
  const b = link({ linkId: "nl_2" });
  const c = link({ linkId: "nl_3" });
  expect(retainHidden([a, b, c], [a, c], hidden).map((x) => x.linkId)).toEqual(["nl_1", "nl_2", "nl_3"]);
  expect(retainHidden([a, c], [a], hidden).map((x) => x.linkId)).toEqual(["nl_1"]); // not hidden: gone
  const merged = mergeMarks(new Map([["s9", { spanId: "s9", notes: [b] }]]), [], hidden);
  expect([...merged.keys()]).toEqual(["s9"]);
  expect(mergeMarks(new Map([["s9", { spanId: "s9", notes: [b] }]]), [], new Map()).size).toBe(0);
});

function PathHarness() {
  const byLo = usePathNotes("g", true);
  return <span data-testid="path">{(byLo.get("lo_eigen") ?? []).map((entry) => entry.note.text).join("|")}</span>;
}

it("while the background linking runs the path is read again, and its end refreshes every surface (F4)", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  try {
    const onChanged = vi.fn();
    api.notesPath
      .mockResolvedValueOnce({ goalId: "g", linking: "running", lines: [] })
      .mockResolvedValue({ goalId: "g", linking: "done", lines: [{ learningObjectId: "lo_eigen", notes: [link()] }] });
    render(withNotes(<PathHarness />, onChanged));
    await waitFor(() => expect(api.notesPath).toHaveBeenCalledTimes(1));
    expect(screen.getByTestId("path").textContent).toBe("");
    await act(async () => { vi.advanceTimersByTime(NOTES_POLL_MS.running + 10); });
    await waitFor(() => expect(screen.getByTestId("path").textContent).toBe("Eigenvalues: Av = lv."));
    expect(api.notesPath).toHaveBeenCalledTimes(2);
    expect(onChanged).toHaveBeenCalledTimes(1); // the marks and the other surfaces read again
    await act(async () => { vi.advanceTimersByTime(NOTES_POLL_MS.waiting * 2); });
    expect(api.notesPath).toHaveBeenCalledTimes(2); // done: no more polling
  } finally {
    vi.useRealTimers();
  }
});

it("a waiting linking is asked again later, quietly (F4)", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  try {
    api.notesPath.mockResolvedValue({ goalId: "g", linking: "waiting", lines: [] });
    render(withNotes(<PathHarness />));
    await waitFor(() => expect(api.notesPath).toHaveBeenCalledTimes(1));
    await act(async () => { vi.advanceTimersByTime(NOTES_POLL_MS.running + 10); });
    expect(api.notesPath).toHaveBeenCalledTimes(1);
    await act(async () => { vi.advanceTimersByTime(NOTES_POLL_MS.waiting); });
    await waitFor(() => expect(api.notesPath).toHaveBeenCalledTimes(2));
  } finally {
    vi.useRealTimers();
  }
});

it("link one of your notes searches the section first, then the learner's words, and links by hand", async () => {
  const onChanged = vi.fn();
  const hit = { noteKey: "capture:c1", refKind: "capture", refId: "c1", title: "captured note", heading: "",
                snippet: "Worked the 2x2 eigen example", capturedOn: "2026-10-03", origin: "vault", contentHash: "h" };
  api.notesSearch.mockResolvedValueOnce({ query: "Chapter 5 Eigenvalues", mode: "words", hits: [hit] })
    .mockResolvedValueOnce({ query: "my page", mode: "words", hits: [] });
  api.notesLink.mockResolvedValue({ linkId: "nl_9", marks: [] });
  render(withNotes(<NoteLinkPicker extractionId="ext_book" spanId="s2" onClose={vi.fn()} onError={vi.fn()} />, onChanged));
  await screen.findByText(/your notes for this section: Chapter 5 Eigenvalues/);
  expect(api.notesSearch).toHaveBeenNthCalledWith(1, { extractionId: "ext_book", spanId: "s2" });
  expect(screen.getByText("Worked the 2x2 eigen example")).toBeTruthy();
  // Embeddings off (meaning: false): no meaning toggle at all.
  expect(screen.queryByRole("button", { name: NOTES_COPY.byMeaning })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: NOTES_COPY.linkHere }));
  await waitFor(() => expect(api.notesLink).toHaveBeenCalledWith({
    note: { noteKey: "capture:c1" }, extractionId: "ext_book", spanId: "s2" }));
  await screen.findByText(`${NOTES_COPY.linked} ✓`);
  expect(onChanged).toHaveBeenCalled();
  fireEvent.change(screen.getByRole("textbox", { name: NOTES_COPY.searchPlaceholder }), { target: { value: "my page" } });
  fireEvent.submit(screen.getByRole("textbox", { name: NOTES_COPY.searchPlaceholder }).closest("form")!);
  await screen.findByText(NOTES_COPY.nothingFound);
  expect(api.notesSearch).toHaveBeenLastCalledWith({ query: "my page" });
});

it("with the vault's embeddings on, the picker offers a search by meaning", async () => {
  api.notesSearch.mockResolvedValue({ query: "spectrum", mode: "meaning", basis: "meaning:ready", hits: [] });
  render(<NotesContext.Provider value={{ settings: { ...SETTINGS, meaning: true }, onChanged: vi.fn(), revision: 0,
    hidden: new Map(), remember: vi.fn(), forget: vi.fn() }}>
    <NoteLinkPicker extractionId="ext_book" spanId="s2" onClose={vi.fn()} onError={vi.fn()} />
  </NotesContext.Provider>);
  await waitFor(() => expect(api.notesSearch).toHaveBeenCalledTimes(1));
  fireEvent.click(screen.getByRole("button", { name: NOTES_COPY.byMeaning }));
  fireEvent.change(screen.getByRole("textbox", { name: NOTES_COPY.searchPlaceholder }), { target: { value: "spectrum" } });
  fireEvent.submit(screen.getByRole("textbox", { name: NOTES_COPY.searchPlaceholder }).closest("form")!);
  await waitFor(() => expect(api.notesSearch).toHaveBeenLastCalledWith({ query: "spectrum", mode: "meaning" }));
  fireEvent.click(screen.getByRole("button", { name: NOTES_COPY.byWords }));
  fireEvent.submit(screen.getByRole("textbox", { name: NOTES_COPY.searchPlaceholder }).closest("form")!);
  await waitFor(() => expect(api.notesSearch).toHaveBeenLastCalledWith({ query: "spectrum" }));
});

it("without the notes context nothing renders and nothing is read", () => {
  const { container } = render(<>
    <NotesTakeBand keys={["ext_book:s1"]} onUse={vi.fn()} />
    <NoteLinkPicker extractionId="ext_book" spanId="s2" onClose={vi.fn()} onError={vi.fn()} />
  </>);
  expect(container.textContent).toBe("");
  expect(api.notesPassages).not.toHaveBeenCalled();
});

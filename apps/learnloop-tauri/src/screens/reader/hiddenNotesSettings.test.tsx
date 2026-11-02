// followups-nov1c C (curriculum C2 ruling R5): Settings lists the note links the learner
// hid and brings one back with "show again" (notes.decide keep, the existing decide path);
// nothing at all while nothing is hidden or the notes are off.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { HIDDEN_NOTES_COPY, HiddenNotesSettings } from "./HiddenNotesSettings";

const { api } = vi.hoisted(() => ({ api: { notesHidden: vi.fn(), notesDecide: vi.fn() } }));
vi.mock("../../api/client", () => ({ api }));

beforeEach(() => { for (const mock of Object.values(api)) mock.mockReset(); });
afterEach(cleanup);

const BY_HAND = {
  linkId: "nl_hand", hiddenAt: "2026-10-20T10:00:00Z", targetKind: "passage", learningObjectId: null,
  extractionId: "ext_book", where: "Linear Algebra › Chapter 5 Eigenvalues", byLabel: "linked by you",
  note: { title: "2026-10-03", heading: "Eigen page", dateLabel: "3 Oct", originLabel: "handwritten · transcribed by Pocket Notes" },
};
const BY_MODEL = {
  linkId: "nl_model", hiddenAt: "2026-10-19T10:00:00Z", targetKind: "learning_object", learningObjectId: "lo_eigen",
  extractionId: "ext_book", where: "the topic “Eigenvalues”", byLabel: "linked by LearnLoop's model",
  note: { title: "linear", heading: "Eigenvalues", dateLabel: null, originLabel: null },
};

async function settle() {
  await act(async () => { for (let i = 0; i < 4; i += 1) await Promise.resolve(); });
}

async function mount() {
  const onToast = vi.fn();
  const utils = render(<HiddenNotesSettings rowStyle={{}} labelStyle={{}} onToast={onToast} />);
  await settle();
  return { ...utils, onToast };
}

it("lists each hidden note with where it was and who linked it, never its text", async () => {
  api.notesHidden.mockResolvedValueOnce({ hidden: [BY_HAND, BY_MODEL] });
  await mount();
  expect(screen.getByText(HIDDEN_NOTES_COPY.label)).toBeTruthy();
  const rows = document.querySelectorAll("[data-hidden-note]");
  expect(rows).toHaveLength(2);
  expect(rows[0].textContent).toContain("2026-10-03 › Eigen page · 3 Oct");
  expect(rows[0].textContent).toContain("hidden from Linear Algebra › Chapter 5 Eigenvalues · linked by you");
  expect(rows[0].textContent).toContain("handwritten · transcribed by Pocket Notes");
  expect(rows[1].textContent).toContain("hidden from the topic “Eigenvalues” · linked by LearnLoop's model");
});

it("shows a note again through the existing decide path (keep), with honest copy per link", async () => {
  api.notesHidden.mockResolvedValueOnce({ hidden: [BY_HAND, BY_MODEL] });
  api.notesDecide.mockResolvedValue({ linkId: "nl_new", status: "accepted" });
  const { onToast } = await mount();
  fireEvent.click(screen.getByRole("button", { name: `${HIDDEN_NOTES_COPY.showAgain}: 2026-10-03 › Eigen page` }));
  await settle();
  expect(api.notesDecide).toHaveBeenCalledWith({ linkId: "nl_hand", choice: "keep" });
  expect(onToast).toHaveBeenLastCalledWith(HIDDEN_NOTES_COPY.shownByYou);
  expect(document.querySelectorAll("[data-hidden-note]")).toHaveLength(1);
  fireEvent.click(screen.getByRole("button", { name: `${HIDDEN_NOTES_COPY.showAgain}: linear › Eigenvalues` }));
  await settle();
  expect(api.notesDecide).toHaveBeenLastCalledWith({ linkId: "nl_model", choice: "keep" });
  expect(onToast).toHaveBeenLastCalledWith(HIDDEN_NOTES_COPY.shownByModel);
  expect(document.querySelector("[data-hidden-notes-settings]")).toBeNull();  // nothing left hidden
});

it("a model's passage link whose proposal is gone gets the model's copy, not the manual one (Codex review F4)", async () => {
  // A model-created link can target a passage and keep its topic (learningObjectId). Hidden,
  // then a later judgment stopped proposing it: keeping it only lifts the hide, so the toast
  // must not promise "shown again beside that passage".
  const MODEL_PASSAGE = {
    ...BY_MODEL, linkId: "nl_model_passage", targetKind: "passage", where: "Linear Algebra › Chapter 5 Eigenvalues",
  };
  api.notesHidden.mockResolvedValueOnce({ hidden: [MODEL_PASSAGE] });
  api.notesDecide.mockResolvedValueOnce({ linkId: "nl_new", status: "accepted" });
  const { onToast } = await mount();
  fireEvent.click(screen.getByRole("button", { name: `${HIDDEN_NOTES_COPY.showAgain}: linear › Eigenvalues` }));
  await settle();
  expect(api.notesDecide).toHaveBeenCalledWith({ linkId: "nl_model_passage", choice: "keep" });
  expect(onToast).toHaveBeenCalledWith(HIDDEN_NOTES_COPY.shownByModel);
  expect(onToast).not.toHaveBeenCalledWith(HIDDEN_NOTES_COPY.shownByYou);
});

it("a failed show-again says why and keeps the row", async () => {
  api.notesHidden.mockResolvedValueOnce({ hidden: [BY_HAND] });
  api.notesDecide.mockRejectedValueOnce(new Error("That note link doesn't exist."));
  const { onToast } = await mount();
  fireEvent.click(screen.getByRole("button", { name: `${HIDDEN_NOTES_COPY.showAgain}: 2026-10-03 › Eigen page` }));
  await settle();
  expect(onToast).toHaveBeenCalledTimes(1);
  expect(document.querySelectorAll("[data-hidden-note]")).toHaveLength(1);
});

it.each([
  ["nothing is hidden", () => api.notesHidden.mockResolvedValueOnce({ hidden: [] })],
  ["the notes are off (the RPC refuses)", () => api.notesHidden.mockRejectedValueOnce(new Error("notes_disabled"))],
])("renders nothing when %s", async (_name, arrange) => {
  arrange();
  await mount();
  expect(document.querySelector("[data-hidden-notes-settings]")).toBeNull();
});

it("names a vault note's kind in its row (followups batch 5 B: the origin part was blank for vault notes)", async () => {
  // C2b's notes are the vault's own: the server labels a Reader note or a capture, so the row
  // says where the note came from instead of ending at "linked by you".
  const READER_NOTE = {
    ...BY_HAND, linkId: "nl_vault", note: { title: "Lay", heading: "5.2 The characteristic equation › question",
      dateLabel: "1 Nov", originLabel: "your note in the Reader" },
  };
  const CAPTURE = {
    ...BY_MODEL, linkId: "nl_capture", note: { title: "captured note", heading: "eigen example",
      dateLabel: "2 Nov", originLabel: "your capture" },
  };
  api.notesHidden.mockResolvedValueOnce({ hidden: [READER_NOTE, CAPTURE] });
  await mount();
  const rows = document.querySelectorAll("[data-hidden-note]");
  expect(rows[0].textContent).toContain("Lay › 5.2 The characteristic equation › question · 1 Nov");
  expect(rows[0].textContent).toContain("hidden from Linear Algebra › Chapter 5 Eigenvalues · linked by you · your note in the Reader");
  expect(rows[1].textContent).toContain("linked by LearnLoop's model · your capture");
});

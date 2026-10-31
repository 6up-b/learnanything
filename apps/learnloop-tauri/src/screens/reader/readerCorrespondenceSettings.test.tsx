// Reader CA5: Settings brings "also in your books" back (ux_reader_compare_ask_v1
// §6.2): a row per thing hidden (everywhere, or a book by name) with "show
// again"; nothing when nothing is hidden or the feature is off.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { CORRESPONDENCE_SETTINGS_COPY, ReaderCorrespondenceSettings } from "./ReaderCorrespondenceSettings";

const { api } = vi.hoisted(() => ({ api: { readerCorrespondencePreferences: vi.fn(), readerSetCorrespondencePreferences: vi.fn() } }));
vi.mock("../../api/client", () => ({ api }));

beforeEach(() => { for (const mock of Object.values(api)) mock.mockReset(); });
afterEach(cleanup);

async function mount() {
  const onToast = vi.fn();
  const utils = render(<ReaderCorrespondenceSettings rowStyle={{}} labelStyle={{}} onToast={onToast} />);
  await act(async () => { for (let i = 0; i < 4; i += 1) await Promise.resolve(); });
  return { ...utils, onToast };
}

it("lists what was hidden, by name, and shows it again", async () => {
  api.readerCorrespondencePreferences.mockResolvedValueOnce({ enabled: true, hideEverywhere: true, hiddenSources: [{ sourceId: "src_strang", title: "Strang" }] });
  const { onToast } = await mount();
  expect(screen.getByText(CORRESPONDENCE_SETTINGS_COPY.everywhere)).toBeTruthy();
  expect(screen.getByText("hidden for Strang")).toBeTruthy();
  api.readerSetCorrespondencePreferences.mockResolvedValueOnce({ enabled: true, hideEverywhere: false, hiddenSources: [{ sourceId: "src_strang", title: "Strang" }] });
  fireEvent.click(screen.getAllByRole("button", { name: CORRESPONDENCE_SETTINGS_COPY.showAgain })[0]);
  await act(async () => { for (let i = 0; i < 4; i += 1) await Promise.resolve(); });
  expect(api.readerSetCorrespondencePreferences).toHaveBeenCalledWith({ hideEverywhere: false });
  expect(screen.queryByText(CORRESPONDENCE_SETTINGS_COPY.everywhere)).toBeNull();
  expect(onToast).toHaveBeenCalledWith(CORRESPONDENCE_SETTINGS_COPY.shown);
  api.readerSetCorrespondencePreferences.mockResolvedValueOnce({ enabled: true, hideEverywhere: false, hiddenSources: [] });
  fireEvent.click(screen.getByRole("button", { name: "show again: Strang" }));
  await act(async () => { for (let i = 0; i < 4; i += 1) await Promise.resolve(); });
  expect(api.readerSetCorrespondencePreferences).toHaveBeenLastCalledWith({ sourceId: "src_strang", hideSource: false });
  expect(document.querySelector("[data-correspondence-settings]")).toBeNull();
});

it.each([
  ["nothing is hidden", { enabled: true, hideEverywhere: false, hiddenSources: [] }],
  ["the feature is off", { enabled: false, hideEverywhere: false, hiddenSources: [] }],
])("shows nothing when %s", async (_name, prefs) => {
  api.readerCorrespondencePreferences.mockResolvedValueOnce(prefs);
  const { container } = await mount();
  expect(container.innerHTML).toBe("");
});

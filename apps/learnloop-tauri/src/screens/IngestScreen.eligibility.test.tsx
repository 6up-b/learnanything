// The Ingest screen takes two answers from the sidecar instead of copying its
// rules: the classifier's source kind as it comes (a copied map dropped
// "image"), and the engines under which a page range is refused (a copy
// disabled the range for every native engine, though an unready one with the
// fallback opted in reads the PDF locally and honours the range).
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { fireEvent } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { clear } from "../api/queryCache";
import { SOURCE_KINDS } from "../api/sourceKinds";

vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn(async () => null) }));
vi.mock("../components/useSourceFileDrop", () => ({ useSourceFileDrop: () => false, pickSourceFiles: async () => [] }));

const api = vi.hoisted(() => {
  const target: Record<string, unknown> = {};
  return new Proxy(target, {
    get: (store, name: string) => (name in store ? store[name] : () => new Promise(() => undefined))
  }) as Record<string, ReturnType<typeof vi.fn>>;
});
vi.mock("../api/client", () => ({ api }));

import { IngestScreen } from "./IngestScreen";

function settings(pdfEngine: string, refusing: string[]) {
  return { ingest: { pdfEngine, pdfEnginesRefusingPageRanges: refusing } };
}

beforeEach(() => {
  clear();
  for (const key of Object.keys(api)) delete (api as Record<string, unknown>)[key];
  api.getIngestJobs = vi.fn(async () => ({ jobs: [] }));
  api.listIngestBatches = vi.fn(async () => ({ batches: [] }));
});

afterEach(() => cleanup());

function showScreen() {
  render(<IngestScreen jobId={null} onJobIdChange={vi.fn()} onProceedToPropose={vi.fn()} />);
}

function pageInput(): HTMLInputElement {
  return screen.getAllByLabelText("PDF page selection")[0] as HTMLInputElement;
}

it("keeps the page range open under a native vault default the sidecar reads locally", async () => {
  api.getSettings = vi.fn(async () => settings("native", []));
  showScreen();
  await waitFor(() => expect(api.getSettings).toHaveBeenCalled());
  await screen.findByText(/auto \(vault default: native\)/);
  expect(pageInput().disabled).toBe(false);
});

it("closes the page range under exactly the engines the sidecar refuses it for", async () => {
  api.getSettings = vi.fn(async () => settings("native", ["auto", "native"]));
  showScreen();
  await screen.findByText(/auto \(vault default: native\)/);
  await waitFor(() => expect(pageInput().disabled).toBe(true));
});

it("takes the classifier's image kind as it comes", async () => {
  api.getSettings = vi.fn(async () => settings("auto", ["native"]));
  // A fragment hides the suffix from the screen's offline guess; the classifier reads the URL's path.
  api.classifyIngestSource = vi.fn(async () => ({ version: 1, kind: "image", normalizedSource: "x" }));
  showScreen();
  const input = await screen.findByPlaceholderText(/paste/i);
  fireEvent.change(input, { target: { value: "https://example.org/scan.png#page" } });
  await waitFor(() => expect(api.classifyIngestSource).toHaveBeenCalled(), { timeout: 2000 });
  await waitFor(() => expect(document.querySelector('[data-kind-chip="image"][data-active="true"]')).not.toBeNull());
  expect(document.querySelector('[data-kind-chip="web"][data-active="true"]')).toBeNull();
});

it("chips every kind the backend's table names, labelled from it", async () => {
  api.getSettings = vi.fn(async () => settings("auto", ["native"]));
  showScreen();
  await screen.findByText(/auto \(vault default: auto\)/);
  const chips = [...document.querySelectorAll("[data-kind-chip]")];
  expect(chips.map((chip) => chip.getAttribute("data-kind-chip"))).toEqual(SOURCE_KINDS.map((kind) => kind.category));
  chips.forEach((chip, index) => expect(chip.textContent?.endsWith(SOURCE_KINDS[index].label)).toBe(true));
});

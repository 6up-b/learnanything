import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { WriteCardDialog } from "./WriteCardDialog";

const { api } = vi.hoisted(() => ({
  api: { getFacetMastery: vi.fn(), getCaptureMedia: vi.fn(), authorPracticeItem: vi.fn() }
}));
vi.mock("../api/client", () => ({ api }));

beforeEach(() => {
  vi.clearAllMocks();
  api.getFacetMastery.mockResolvedValue({ facets: [] });
  api.getCaptureMedia.mockResolvedValue({ captureId: "capture-1", mime: "image/jpeg", dataUrl: "data:image/jpeg;base64,BBBB",
    width: 2048, height: 1365, originalWidth: 3000, originalHeight: 2000 });
});
afterEach(cleanup);

it("shows the captured photo beside the manual card editor", async () => {
  render(<WriteCardDialog captureId="capture-1" photoCaptureId="capture-1" onClose={() => {}} onCreated={() => {}} />);
  await act(async () => {});
  expect(api.getCaptureMedia).toHaveBeenCalledWith("capture-1");
  expect(screen.getByAltText("Captured photo").getAttribute("src")).toBe("data:image/jpeg;base64,BBBB");
  expect(screen.getByText(/3000×2000/)).toBeTruthy();
  expect(screen.getByPlaceholderText(/what a good answer should contain/)).toBeTruthy();
});

it("loads no photo for text captures and reports a missing original", async () => {
  render(<WriteCardDialog captureId="capture-2" onClose={() => {}} onCreated={() => {}} />);
  await act(async () => {});
  expect(api.getCaptureMedia).not.toHaveBeenCalled();
  cleanup();
  api.getCaptureMedia.mockRejectedValue({ code: "not_found", message: "The captured photo is missing from the originals store" });
  render(<WriteCardDialog captureId="capture-3" photoCaptureId="capture-3" onClose={() => {}} onCreated={() => {}} />);
  await act(async () => {});
  expect(screen.getByRole("alert").textContent).toContain("missing from the originals store");
});

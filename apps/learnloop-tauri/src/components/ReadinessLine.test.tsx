// Adaptive difficulty AD2+AD3 (§9.5, §12): the readiness line is labelled as a
// prediction, "untested" where the cell has no answer of its own, and "not yet
// predicted" with the subject view off.
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

const readiness = vi.fn();
vi.mock("../api/client", () => ({ api: { adaptiveDifficultyReadiness: (input: unknown) => readiness(input) } }));

import { ReadinessLine } from "./ReadinessLine";

afterEach(() => {
  cleanup();
  readiness.mockReset();
});

it("shows the prediction's line", async () => {
  readiness.mockResolvedValue({ version: 1, predicted: true, line: "Top level for this goal: not yet shown · likely ready (a prediction)", cells: [] });
  render(<ReadinessLine learningObjectId="lo1" />);
  await waitFor(() => expect(screen.getByTestId("readiness-line").textContent).toContain("(a prediction)"));
  expect(readiness).toHaveBeenCalledWith({ learningObjectId: "lo1" });
});

it("says untested, and not yet predicted with the switch off", async () => {
  readiness.mockResolvedValue({ version: 1, predicted: true, line: "Top level for this goal: untested", cells: [] });
  render(<ReadinessLine learningObjectId="lo2" />);
  await waitFor(() => expect(screen.getByTestId("readiness-line").textContent).toBe("Top level for this goal: untested"));
  cleanup();
  readiness.mockResolvedValue({ version: 1, predicted: false, line: "exam level: not yet predicted", cells: [] });
  render(<ReadinessLine learningObjectId="lo3" />);
  await waitFor(() => expect(screen.getByTestId("readiness-line").textContent).toBe("exam level: not yet predicted"));
});

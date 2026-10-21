// UX Phase 2, a finding Phase 1's usability round 1 deferred here (M-e,
// docs/reviews/ux-phase1.md): "The build-plan modal's Escape steps back
// instead of closing", and the modal held the tabs until "← back". In the
// simple shell Escape closes the modal from either step; "← back" still steps
// back. The classic shell keeps the old stepping.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";

vi.mock("../api/client", () => {
  const outline = {
    extractionId: "ext_1",
    revisionId: "rev_1",
    sourceId: "src_1",
    title: "A paper",
    authors: [],
    extractor: "pypdf",
    extractorVersion: "1",
    unitCount: 1,
    blockCount: 1,
    approxTokens: 1213,
    healthFlags: [],
    difficultPageCount: 0,
    units: [
      {
        unitId: "u1",
        parentUnitId: null,
        label: "Abstract",
        ordinal: 0,
        locator: {},
        semanticHash: "h",
        pageStart: 0,
        pageEnd: 0,
        blockCount: 1,
        blockCounts: {},
        structuralSignals: {},
        healthFlags: [],
        approxTokens: 1213,
        inventory: { status: "cached" }
      }
    ],
    selection: { selectedUnitIds: [], boundaryOverrides: [], needsReview: [], roleOverride: null }
  };
  const api = new Proxy(
    {
      getSourceOutline: vi.fn(async () => outline),
      saveUnitSelection: vi.fn(async () => ({}))
    } as Record<string, unknown>,
    { get: (target, name: string) => (name in target ? target[name] : () => new Promise(() => undefined)) }
  );
  return { api };
});

import { OutlinePlanFlow } from "./OutlineAndPlan";

afterEach(() => {
  cleanup();
  setAlgoConfig({});
});

async function openOnThePlanStep(onClose: () => void) {
  render(<OutlinePlanFlow sourceRef="src_1" subjectId={null} onClose={onClose} onOpenBatch={() => undefined} />);
  const planChip = await screen.findByText("2 · build plan");
  await act(async () => {
    fireEvent.click(planChip);
  });
}

function escape() {
  act(() => {
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  });
}

describe("the build-plan modal's Escape", () => {
  it("closes the modal in the simple shell, even on the build-plan step", async () => {
    setAlgoConfig({});
    const onClose = vi.fn();
    await openOnThePlanStep(onClose);
    escape();
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(screen.getByText("esc close")).toBeTruthy();
  });

  it("steps back in the classic shell, as before", async () => {
    setAlgoConfig({ ui: { shell: "classic" } });
    const onClose = vi.fn();
    await openOnThePlanStep(onClose);
    escape();
    expect(onClose).not.toHaveBeenCalled();
    expect(screen.getByText("esc back")).toBeTruthy();
  });
});

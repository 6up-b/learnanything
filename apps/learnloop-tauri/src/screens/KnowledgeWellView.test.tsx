import { cleanup, render } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { DecayPressureDto, KnowledgeFacetField, KnowledgeFacetPoint } from "../api/dto";
import { buildGeometry, buildStates, KnowledgeWellView } from "./KnowledgeWellView";

afterEach(cleanup);

const base = {
  id: "frontier", title: "Frontier", x: 0, y: 0,
  evidenceMass: 0, demonstratedMass: 0,
  requiredCapabilities: ["recall"], demonstratedCapabilities: [],
  hasBlueprints: true, capabilityArcs: [],
  learningObjectIds: [], ambiguityCandidates: [], ambiguityAttemptId: null,
  correction: null, locked: false, lockSources: []
};
const legacy: KnowledgeFacetPoint = { ...base, ready: 0.5, readyGhost: 0.5, readyVariance: 1 / 12 };
const untested: KnowledgeFacetPoint = { ...base, untested: true };
const demonstrated: KnowledgeFacetPoint = {
  ...base, id: "demonstrated", title: "Demonstrated",
  evidenceMass: 3, demonstratedMass: 1,
  ready: 0.6, readyGhost: 0.9, readyVariance: 0.02
};
const field = (points: KnowledgeFacetPoint[]): KnowledgeFacetField => ({
  points, graphNodes: [], edges: [], layoutVersion: "test",
  stress: 0, layoutValid: true, layoutWarning: null, nextGap: null
});
const view = (points: KnowledgeFacetPoint[], decay?: DecayPressureDto) => (
  <KnowledgeWellView field={field(points)} decay={decay} selected={null} onSelect={vi.fn()} onInspect={vi.fn()} />
);

it.each([true, false])("G6 preserves exact geometry, beads, ghosts and decay markers (history=%s)", (hasHistory) => {
  const decay: DecayPressureDto = {
    hasHistory, heldFlatCount: hasHistory ? 0 : 1,
    facets: [{
      facetId: demonstrated.id, learningObjectId: "lo", learningObjectTitle: "LO",
      readyNow: 0.6, crossesInDays: hasHistory ? 2 : null, hasHistory
    }]
  };
  const before = buildStates(field([legacy, demonstrated]), decay);
  const after = buildStates(field([untested, demonstrated]), decay);
  expect(after[0]).toEqual(before[0]); // sorted demonstrated point, untouched
  expect(buildGeometry(after)).toEqual(buildGeometry(before));
  expect(after[1].wellDepth).toBe(0);
  expect(after[1].showGhost).toBe(false);
  const { container, rerender } = render(view([legacy, demonstrated], decay));
  const bead = () => Array.from(container.querySelectorAll("g")).find(
    node => node.querySelector(":scope > title")?.textContent?.startsWith("Demonstrated\n")
  )?.outerHTML;
  const ghost = () => container.querySelector('circle[stroke-dasharray="4 3"]')?.outerHTML;
  const oldBead = bead();
  const oldGhost = ghost();
  expect(oldBead).toBeTruthy();
  expect(Boolean(oldGhost)).toBe(hasHistory);
  if (hasHistory) expect(oldBead).toContain("crosses target in ~2d");
  else expect(oldBead).toContain("held flat: not enough history");
  rerender(view([untested, demonstrated], decay));
  expect(bead()).toBe(oldBead);
  expect(ghost()).toBe(oldGhost);
});

it("G4 renders an unselected no-evidence facet as an outline with a small untested label, never Ready", () => {
  const { container, getByText } = render(view([untested]));
  expect(getByText("untested").getAttribute("font-size")).toBe("9.5");
  expect(container.textContent).not.toMatch(/Ready \d|NaN|assumed|inferred/);
  const marker = Array.from(container.querySelectorAll("g")).find(
    node => node.querySelector(":scope > title")?.textContent === "Frontier\nuntested"
  );
  expect(marker?.querySelector("circle")?.getAttribute("fill")).toBe("none");
  expect(buildGeometry(buildStates(field([untested]), null)).beads[0].z).toBe(0.012);
});

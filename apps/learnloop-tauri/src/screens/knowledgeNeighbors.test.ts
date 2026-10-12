import { expect, it } from "vitest";
import { neighborCaption } from "./knowledgeNeighbors";

const coverage = { enabled: true, modelId: "qwen/qwen3-embedding-8b", stems: 6, embedded: 5 };

it("names the wording ranking, its model and coverage, and disclaims a skill match", () => {
  expect(neighborCaption({ neighborBasis: "item_text" }, coverage)).toBe(
    "by similar wording · stored qwen/qwen3-embedding-8b vectors, 5/6 items embedded · not a same-skill match"
  );
});

it("says why an item kept facet/graph neighbours while other items are embedded", () => {
  expect(neighborCaption({ neighborBasis: "facet_graph" }, coverage)).toBe(
    "by shared facets + concept graph · wording vectors: 5/6 items embedded"
  );
});

it("claims nothing about wording when nothing is embedded or the switch is off", () => {
  expect(neighborCaption({ neighborBasis: "facet_graph" }, { ...coverage, embedded: 0 })).toBe(
    "by shared facets + concept graph"
  );
  expect(neighborCaption({ neighborBasis: "facet_graph" }, { ...coverage, enabled: false, stems: 0, embedded: 0 })).toBe(
    "by shared facets + concept graph"
  );
  expect(neighborCaption({ neighborBasis: "facet_graph" }, undefined)).toBe("by shared facets + concept graph");
});

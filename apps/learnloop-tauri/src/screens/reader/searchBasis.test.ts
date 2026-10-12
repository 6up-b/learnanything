import { describe, expect, it } from "vitest";
import { searchBasisLabel } from "./searchBasis";

const base = { query: "q", hits: [], searchedSources: 1 };

describe("searchBasisLabel", () => {
  it("says nothing when retrieval is off (plain substring search)", () => {
    expect(searchBasisLabel(base)).toBe("");
  });

  it("names keyword-only typing results and offers the deep search", () => {
    expect(searchBasisLabel({ ...base, basis: "keyword", deep: false })).toBe(
      " · keyword match · Enter also searches by meaning",
    );
  });

  it("never claims meaning when a deep search fell back to keywords", () => {
    expect(searchBasisLabel({ ...base, basis: "keyword", deep: true })).toBe(" · keyword match");
  });

  it("names meaning and a rewritten question only when they ranked hits", () => {
    expect(searchBasisLabel({ ...base, basis: "keyword+meaning", deep: true })).toBe(" · keyword + meaning");
    expect(searchBasisLabel({ ...base, basis: "keyword+meaning+rewrite", deep: true })).toBe(
      " · keyword + meaning + rewritten question",
    );
  });
});

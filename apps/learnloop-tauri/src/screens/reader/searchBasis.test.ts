import { describe, expect, it } from "vitest";
import type { ReaderMeaningSearchDto } from "../../api/dto";
import { searchBasisLabel } from "./searchBasis";

const base = { query: "q", hits: [], searchedSources: 1 };
const meaning = (status: string, sources = 4, sourcesCovered = 4): ReaderMeaningSearchDto => ({
  status, sources, sourcesCovered, blocks: 40, blocksCovered: 30
});

describe("searchBasisLabel", () => {
  it("says nothing when retrieval is off (plain substring search)", () => {
    expect(searchBasisLabel(base)).toBe("");
  });

  it("offers the deep search only when Enter would search by meaning", () => {
    expect(searchBasisLabel({ ...base, basis: "keyword", deep: false, meaningSearch: meaning("ready") })).toBe(
      " · keyword match · Enter also searches by meaning",
    );
    expect(
      searchBasisLabel({ ...base, basis: "keyword", deep: false, meaningSearch: meaning("partial", 4, 3) }),
    ).toBe(" · keyword match · Enter also searches by meaning (3 of 4 sources)");
    for (const status of ["incomplete", "disabled", "empty", "unavailable"]) {
      expect(searchBasisLabel({ ...base, basis: "keyword", deep: false, meaningSearch: meaning(status) })).toBe(
        " · keyword match",
      );
    }
    expect(searchBasisLabel({ ...base, basis: "keyword", deep: false })).toBe(" · keyword match");
  });

  it("never claims meaning when a deep search fell back to keywords", () => {
    expect(searchBasisLabel({ ...base, basis: "keyword", deep: true, meaningSearch: meaning("ready") })).toBe(
      " · keyword match",
    );
  });

  it("names exactly the parts that ranked hits", () => {
    expect(searchBasisLabel({ ...base, basis: "keyword+meaning", deep: true })).toBe(" · keyword + meaning");
    expect(searchBasisLabel({ ...base, basis: "keyword+meaning+rewrite", deep: true })).toBe(
      " · keyword + meaning + rewritten question",
    );
    expect(searchBasisLabel({ ...base, basis: "meaning", deep: true })).toBe(" · meaning");
    expect(searchBasisLabel({ ...base, basis: "keyword+rewrite", deep: true })).toBe(
      " · keyword + rewritten question",
    );
    expect(
      searchBasisLabel({ ...base, basis: "keyword+meaning", deep: true, meaningSearch: meaning("partial", 4, 3) }),
    ).toBe(" · keyword + meaning (3 of 4 sources)");
  });
});

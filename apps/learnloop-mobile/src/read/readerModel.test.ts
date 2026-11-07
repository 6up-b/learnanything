import { describe, expect, it } from "vitest";
import {
  llpdfPage,
  nextSectionId,
  pageLinkTarget,
  pagePath,
  pageWidthFor,
  protectionKey,
  resumeSection,
  sectionState,
  selectionProtected,
  storeNameOf,
  withPageLinks
} from "./readerModel";

const NAME = `sha256-${"ab".repeat(32)}`;
const sections = [
  { id: "u1", label: "1", startSpanId: "b0", endSpanId: "b2", spanIds: ["b0", "b1", "b2"], question: null, suggestedPassages: [] },
  { id: "u2", label: "2", startSpanId: "b3", endSpanId: "b4", spanIds: ["b3", "b4"], question: null, suggestedPassages: [] }
];
const progress = (rows: Array<{ sectionId: string; spansSeen?: number; completedAt?: string | null }>) => ({
  extractionId: "ext1",
  sections: rows.map((row) => ({ extractionId: "ext1", spanCount: 3, revealedAt: null, completedAt: null, generationBatchId: null, spansSeen: 0, ...row }))
});

describe("the Reader's pure parts (mobile v2 §3)", () => {
  it("asks for one of the host's two widths, never another (§3.3)", () => {
    expect(pageWidthFor(360, 2)).toBe(720);
    expect(pageWidthFor(390, 3)).toBe(1080);
    expect(pageWidthFor(1200, 3)).toBe(1080);
    expect(pagePath("ext1", 2, 720)).toBe("/api/v1/reader/page/ext1/2?w=720");
  });

  it("continues where the shared history says, and the next section follows in order (§3.1)", () => {
    expect(resumeSection(sections, null)).toBe("u1");
    expect(resumeSection(sections, progress([{ sectionId: "u1", completedAt: "t" }]))).toBe("u2");
    expect(resumeSection(sections, progress([{ sectionId: "u2", spansSeen: 1 }]))).toBe("u2");
    expect(nextSectionId(sections, "u1")).toBe("u2");
    expect(nextSectionId(sections, "u2")).toBeNull();
    expect(sectionState("u1", progress([{ sectionId: "u1", completedAt: "t" }]))).toBe("read");
    expect(sectionState("u1", progress([{ sectionId: "u1", spansSeen: 2 }]))).toBe("started");
    expect(sectionState("u2", null)).toBe("unread");
  });

  it("offers no Ask on what the reading holds out, by the desktop's rule", () => {
    const held = { withheld: false, heldOutSpanIds: ["b5"], message: "held" };
    expect(selectionProtected(held, ["b4", "b5"])).toBe(true);
    expect(selectionProtected(held, ["b4"])).toBe(false);
    expect(selectionProtected({ withheld: true, heldOutSpanIds: [], message: "m" }, ["b1"])).toBe(true);
    expect(protectionKey(held)).not.toBe(protectionKey({ ...held, heldOutSpanIds: ["b5", "b6"] }));
    expect(protectionKey(held)).toBe(protectionKey({ ...held, message: "another wording" }));
  });

  it("turns a prompt's stored page links into the host's pages, and leaves every other link alone (§2.3)", () => {
    expect(llpdfPage(`llpdf://localhost/${NAME}#page=3`)).toEqual({ name: NAME, page: 2 });
    expect(llpdfPage("llpdf://source/abc#page=3")).toBeNull();
    const rewritten = withPageLinks(`See [page 3](llpdf://localhost/${NAME}#page=3) and [that](llpdf://source/abc).`);
    expect(rewritten).toBe(`See [page 3](#llpage/${NAME}/2) and [that](llpdf://source/abc).`);
    expect(pageLinkTarget(`#llpage/${NAME}/2`)).toEqual({ name: NAME, page: 2 });
    expect(pageLinkTarget("#llpage/nope/2")).toBeNull();
    expect(storeNameOf(`canonical-sources/raw/${NAME}`)).toBe(NAME);
    expect(storeNameOf("figures/graph.png")).toBeNull();
  });
});

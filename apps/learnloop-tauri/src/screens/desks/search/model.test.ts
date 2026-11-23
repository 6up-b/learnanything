// Search's groups (spec §9.3): open on this desk first, the server's groups in order, the meaning rows merged
// with their tag, three rows a group until tab, an off group saying why, and the rows the keys move through.
import { describe, expect, it } from "vitest";
import type { SearchEverythingDto, SearchGroupDto } from "../../../api/dto";
import { meaningNote, selectableRows, shownGroups } from "./model";

function passage(spanId: string, byMeaning = false) {
  return { ref: { kind: "source" as const, sourceId: "src", extractionId: "ext" }, target: { spanId }, sourceId: "src", sourceTitle: "A book", extractionId: "ext", spanId, section: null, page: 3, snippet: `text of ${spanId}`, byMeaning };
}

const WORDS: SearchEverythingDto = {
  version: 1,
  query: "soft",
  groups: [
    { group: "passages", label: "passages and moments", basis: "words", status: "ok", rows: [passage("a"), passage("b"), passage("c"), passage("d")], more: false },
    { group: "notes", label: "your notes and highlights", basis: "words", status: "off", reason: "the notes are off", rows: [], more: false },
    { group: "sources", label: "sources in your library", basis: "words", status: "ok", rows: [], more: false },
  ],
  meaning: { status: "pending", jobId: "j1", groups: ["passages"], unavailable: [{ group: "pads", reason: "no meaning index of pad text" }] },
};

const base = { query: "soft", open: [{ windowId: "w1", title: "Softmax, a book" }, { windowId: "w2", title: "A video" }], words: WORDS, meaning: [] as SearchGroupDto[], meaningPending: true, expanded: new Set<string>(), deskTitle: () => "a desk" };

describe("the groups", () => {
  it("open on this desk first (by title), then the server's groups in order; an off group says why; empty ones go", () => {
    const groups = shownGroups(base);
    expect(groups.map((group) => group.id)).toEqual(["open", "passages", "notes"]);
    expect(groups[0].rows.map((row) => row.text)).toEqual(["Softmax, a book"]);
    expect(groups[2].off).toBe("the notes are off");
    expect(groups[1].pending).toBe(true);
  });

  it("three rows a group until it is expanded", () => {
    expect(shownGroups(base)[1]).toMatchObject({ hidden: 1 });
    expect(shownGroups(base)[1].rows).toHaveLength(3);
    expect(shownGroups({ ...base, expanded: new Set(["passages"]) })[1].rows).toHaveLength(4);
  });

  it("the meaning job's rows merge into their group with the tag, without repeating a word result", () => {
    const meaning: SearchGroupDto[] = [{ group: "passages", label: "passages and moments", basis: "meaning", status: "ok", rows: [passage("a", true), passage("z", true)], more: false }];
    const groups = shownGroups({ ...base, meaning, meaningPending: false, expanded: new Set(["passages"]) });
    const rows = groups[1].rows;
    expect(rows.map((row) => row.key.split(":").pop())).toEqual(["a", "b", "c", "d", "z"]);
    expect(rows[4]).toMatchObject({ byMeaning: true });
    expect(groups[1].pending).toBe(false);
  });

  it("the keys move through the shown rows in order; the meaning note names why a group cannot be searched by meaning", () => {
    expect(selectableRows(shownGroups(base)).map((row) => row.key)[0]).toBe("open:w1");
    expect(meaningNote({ ...WORDS, meaning: { status: "unavailable", jobId: null, unavailable: [{ group: "pads", reason: "no meaning index of pad text" }, { group: "threads", reason: "no meaning index of exchanges" }] } })).toBe("by meaning: no meaning index of pad text · no meaning index of exchanges");
  });
});

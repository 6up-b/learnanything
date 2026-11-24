// The client's pad model (spec §10.4, §10.5): each op as the server applies it, chained client-minted versions,
// fractional position keys, lift out, links with their heads, and re-stamping a queued op after a conflict.
import { describe, expect, it } from "vitest";
import type { PadViewDto } from "../../../api/dto";
import { PadOpConflict, PadOpRefusal, applyPadOp, fromPadView, isLearnersWords, keyAfter, keyBetween, restampPadOp, type Pads } from "./model";

const NOW = "2026-11-23T10:00:00Z";

function view(): PadViewDto {
  return {
    version: 1,
    pad: { padId: "p1", kind: "running", title: "running", kept: false, homeDeskId: "d1", workbenchSessionId: null, lessonId: null, version: 3, createdAt: NOW, updatedAt: NOW },
    blocks: [
      { blockId: "b2", headVersionId: "v2", kind: "source_quote", bodyMd: "a quote", payload: {}, provenance: "source", positionKey: "m", day: "2026-11-22", createdAt: NOW, updatedAt: NOW, submissions: [] },
      { blockId: "b1", headVersionId: "v1", kind: "text", bodyMd: "my words", payload: {}, provenance: "learner", positionKey: "g", day: "2026-11-22", createdAt: NOW, updatedAt: NOW, submissions: [{ submissionId: "s1", versionId: "v1", as: "teach_back", practiceItemId: "i1", attemptId: null, teachBackId: "t1", createdAt: NOW, current: true }] },
    ],
    anchors: [],
  };
}

const pads = (): Pads => ({ p1: fromPadView(view()) });

describe("position keys", () => {
  it("a key between two keys sorts between them, and before or after everything", () => {
    for (const [a, b] of [[null, null], [null, "g"], ["g", null], ["g", "m"], ["g", "h"], ["a", "a1"], ["V", "V0V"]] as const) {
      const key = keyBetween(a, b);
      if (a !== null) expect(key > a).toBe(true);
      if (b !== null) expect(key < b).toBe(true);
    }
  });

  it("a run of inserts after the same block stays in order", () => {
    let keys = ["g", "m"];
    for (let i = 0; i < 30; i += 1) {
      const key = keyBetween(keys[0], keys[1]);
      keys = [keys[0], key, ...keys.slice(1)];
      expect([...keys].sort()).toEqual(keys);
    }
  });
});

describe("applying ops", () => {
  it("blocks read in position order; an insert after a block lands right after it", () => {
    const state = pads().p1;
    expect(state.blocks.map((block) => block.blockId)).toEqual(["b1", "b2"]);
    const next = applyPadOp(pads(), "p1", { op: "insert_block", blockId: "b3", versionId: "v3", kind: "text", provenance: "learner", positionKey: keyAfter(state.blocks, "b1"), bodyMd: "new" }, NOW);
    expect(next.p1.blocks.map((block) => block.blockId)).toEqual(["b1", "b3", "b2"]);
  });

  it("edits chain on client-minted versions; a stale head is a conflict; a quote is not editable", () => {
    let state = applyPadOp(pads(), "p1", { op: "edit_block", blockId: "b1", expectedHead: "v1", versionId: "v1b", bodyMd: "edited" }, NOW);
    state = applyPadOp(state, "p1", { op: "edit_block", blockId: "b1", expectedHead: "v1b", versionId: "v1c", bodyMd: "edited again" }, NOW);
    expect(state.p1.blocks[0]).toMatchObject({ headVersionId: "v1c", bodyMd: "edited again" });
    // The submitted version is no longer the current words.
    expect(state.p1.blocks[0].submissions[0].current).toBe(false);
    expect(() => applyPadOp(state, "p1", { op: "edit_block", blockId: "b1", expectedHead: "v1", bodyMd: "x" }, NOW)).toThrow(PadOpConflict);
    expect(() => applyPadOp(state, "p1", { op: "edit_block", blockId: "b2", expectedHead: "v2", bodyMd: "x" }, NOW)).toThrow(PadOpRefusal);
  });

  it("lift out makes a named pad with the block and leaves a lifted stub", () => {
    const next = applyPadOp(pads(), "p1", { op: "lift_out", blockId: "b1", expectedHead: "v1", newPadId: "p2", newBlockId: "b9", title: "my words", stubVersionId: "v1s", newVersionId: "v9" }, NOW);
    expect(next.p1.blocks[0]).toMatchObject({ kind: "lifted", provenance: "learnloop", payload: { lifted_to_pad_id: "p2", lifted_block_id: "b9" } });
    expect(next.p2.pad).toMatchObject({ kind: "named", title: "my words", homeDeskId: "d1" });
    expect(next.p2.blocks[0]).toMatchObject({ blockId: "b9", kind: "text", bodyMd: "my words", provenance: "learner" });
  });

  it("a link names the head it expects; unlinking what is not linked is refused", () => {
    const linked = applyPadOp(pads(), "p1", { op: "link_anchor", blockId: "b2", extractionId: "e", spanId: "s", eventId: "ev1", expectedAnchorHead: null }, NOW);
    expect(linked.p1.anchors).toHaveLength(1);
    expect(() => applyPadOp(linked, "p1", { op: "link_anchor", blockId: "b2", extractionId: "e", spanId: "s", expectedAnchorHead: null }, NOW)).toThrow(PadOpConflict);
    expect(() => applyPadOp(pads(), "p1", { op: "unlink_anchor", blockId: "b2", extractionId: "e", spanId: "s", expectedAnchorHead: null }, NOW)).toThrow(PadOpRefusal);
  });

  it("an erase names an ink block of the pad and moves only the pad's change time", () => {
    const later = "2026-11-23T11:00:00Z";
    const withInk = applyPadOp(pads(), "p1", { op: "insert_block", blockId: "k1", kind: "ink", provenance: "ink_transcription", positionKey: "z" }, NOW);
    const erased = applyPadOp(withInk, "p1", { op: "erase_ink", blockId: "k1", strokeIds: ["s1"] }, later);
    expect(erased.p1.pad).toMatchObject({ updatedAt: later, version: 3 });
    expect(erased.p1.blocks).toEqual(withInk.p1.blocks);
    expect(() => applyPadOp(pads(), "p1", { op: "erase_ink", blockId: "b1", strokeIds: ["s1"] }, NOW)).toThrow(PadOpRefusal);
    expect(() => applyPadOp(pads(), "p1", { op: "erase_ink", blockId: "nope", strokeIds: ["s1"] }, NOW)).toThrow(PadOpRefusal);
  });

  it("set_title and keep expect the pad's version and bump it; block ops do not", () => {
    const kept = applyPadOp(pads(), "p1", { op: "keep", expectedVersion: 3 }, NOW);
    expect(kept.p1.pad).toMatchObject({ kept: true, version: 4 });
    const edited = applyPadOp(kept, "p1", { op: "edit_block", blockId: "b1", expectedHead: "v1", bodyMd: "e" }, NOW);
    expect(edited.p1.pad.version).toBe(4);
    expect(() => applyPadOp(kept, "p1", { op: "set_title", expectedVersion: 3, title: "t" }, NOW)).toThrow(PadOpConflict);
  });
});

describe("re-stamping after a conflict: the server's head is kept (RD4 review)", () => {
  const remote = () => applyPadOp(pads(), "p1", { op: "edit_block", blockId: "b1", expectedHead: "v1", versionId: "vR", bodyMd: "elsewhere" }, NOW);
  const keep = { blockId: "kb1", versionId: "vL.kb", label: "written over an older version" };

  it("a queued edit of a head another device changed keeps that head and lands as its own labelled block right after it", () => {
    const queued = { op: "edit_block" as const, blockId: "b1", expectedHead: "v1", versionId: "vL", bodyMd: "mine", keepBoth: keep };
    const rebased = restampPadOp(remote(), "p1", queued, NOW);
    expect(rebased.op).toMatchObject({ expectedHead: "v1", keepBoth: keep });
    const blocks = rebased.pads.p1.blocks;
    expect(blocks.find((block) => block.blockId === "b1")?.bodyMd).toBe("elsewhere");
    const kept = blocks.find((block) => block.blockId === "kb1");
    expect(kept).toMatchObject({ bodyMd: "mine", headVersionId: "vL.kb", kind: "text", provenance: "learner" });
    expect(kept?.payload.conflict).toMatchObject({ of_block_id: "b1", expected_head: "v1", server_head_version_id: "vR", label: "written over an older version" });
    expect(blocks.findIndex((block) => block.blockId === "kb1")).toBe(blocks.findIndex((block) => block.blockId === "b1") + 1);
  });

  it("an edit without keepBoth never overwrites newer words: it is refused", () => {
    const queued = { op: "edit_block" as const, blockId: "b1", expectedHead: "v1", versionId: "vL", bodyMd: "mine" };
    expect(() => restampPadOp(remote(), "p1", queued, NOW)).toThrow(PadOpRefusal);
  });

  it("a stale remove, move or lift is refused, never retried onto the newer text", () => {
    for (const op of [
      { op: "remove_block" as const, blockId: "b1", expectedHead: "v1" },
      { op: "move_block" as const, blockId: "b1", expectedHead: "v1", positionKey: "z" },
      { op: "lift_out" as const, blockId: "b1", expectedHead: "v1", newPadId: "p9", newBlockId: "b9", title: "lifted" },
    ]) {
      expect(() => restampPadOp(remote(), "p1", op, NOW), op.op).toThrow(PadOpRefusal);
    }
  });

  it("an edit of a block removed elsewhere keeps its words as their own block", () => {
    const removed = applyPadOp(pads(), "p1", { op: "remove_block", blockId: "b1", expectedHead: "v1" }, NOW);
    const queued = { op: "edit_block" as const, blockId: "b1", expectedHead: "v1", versionId: "vL", bodyMd: "mine", keepBoth: keep };
    const rebased = restampPadOp(removed, "p1", queued, NOW);
    expect(rebased.pads.p1.blocks.find((block) => block.blockId === "kb1")?.bodyMd).toBe("mine");
  });

  it("a second queued edit, typed on after the first, goes on in the block the first one's words landed in", () => {
    const redirects = new Map<string, { blockId: string; versionId: string }>();
    const first = restampPadOp(remote(), "p1", { op: "edit_block", blockId: "b1", expectedHead: "v1", versionId: "vL", bodyMd: "mine", keepBoth: keep }, NOW, redirects);
    const second = restampPadOp(first.pads, "p1", { op: "edit_block", blockId: "b1", expectedHead: "vL", versionId: "vL2", bodyMd: "mine, more", keepBoth: { blockId: "kb2", versionId: "vL2.kb", label: "x" } }, NOW, redirects);
    expect(second.op).toMatchObject({ blockId: "kb1", expectedHead: "vL.kb", bodyMd: "mine, more" });
    expect(second.pads.p1.blocks.find((block) => block.blockId === "kb1")?.bodyMd).toBe("mine, more");
    expect(second.pads.p1.blocks.some((block) => block.blockId === "kb2")).toBe(false);
  });
});

describe("whose words", () => {
  it("only the learner's text, notes, ink transcriptions and check answers are the learner's words", () => {
    const state = pads().p1;
    expect(isLearnersWords(state.blocks[0])).toBe(true);
    expect(isLearnersWords(state.blocks[1])).toBe(false);
  });
});

// What every stored window kind restores as (the Reader's retirement, phase 2 step 2): never a crash, never a window
// silently lost. The kinds are the ones the desks' content reference has ever had (desks/content_ref.py, migration 262
// and 271), the fixture workspace's windows, and shapes this version does not know.
import { describe, expect, it } from "vitest";
import type { ContentRefDto } from "../../../api/dto";
import { fixtureDeskState } from "../../../fixtures/desks/workspace";
import { bookContent, restoreContent, type Restored } from "./restore";

const KEEP: Restored = { kind: "keep" };

describe("restoreContent", () => {
  it.each<[string, unknown, Restored]>([
    ["a book", { kind: "source", sourceId: "s", extractionId: "e", view: "render" }, KEEP],
    ["a book's range", { kind: "source", sourceId: "s", extractionId: "e", range: { fromSpanId: "a", toSpanId: "b" } }, KEEP],
    ["a video", { kind: "video", sourceId: "s", extractionId: "e", t: 3 }, KEEP],
    ["a pad", { kind: "pad", padId: "p" }, KEEP],
    ["a lesson", { kind: "lesson", lessonId: "l" }, KEEP],
    ["a thread", { kind: "thread", rootExchangeId: "x" }, KEEP],
    ["a saved comparison", { kind: "compare", comparisonId: "c" }, KEEP],
    ["a compare query", { kind: "compare", query: "eigen" }, KEEP],
    ["a figure notebook", { kind: "figure_notebook", figureId: "f" }, KEEP],
    ["a book being prepared", { kind: "preparing", sourceId: "s" }, KEEP],
    // The Guide and Notes panels host the book window's rail until it leaves the portal; the library panel keeps its
    // kind (the orchestrator's calls, phase 2 step 2).
    ["a Guide panel", { kind: "panel", panel: "guide", extractionId: "e" }, KEEP],
    ["a Notes panel", { kind: "panel", panel: "notes", extractionId: "e" }, KEEP],
    ["a library panel", { kind: "panel", panel: "library" }, KEEP],
    // The reading's path is the book window's own.
    ["a reading-path panel", { kind: "panel", panel: "path", extractionId: "e" }, { kind: "book", sourceId: null, extractionId: "e", showPath: true }],
    ["a reading-path panel with no book", { kind: "panel", panel: "path" }, { kind: "inert", name: "a reading path with no book" }],
    // Damaged or unknown shapes.
    ["a book that lost its reading", { kind: "source", sourceId: "s" }, { kind: "book", sourceId: "s", extractionId: null, showPath: false }],
    ["a video that lost its source", { kind: "video", extractionId: "e" }, { kind: "book", sourceId: null, extractionId: "e", showPath: false }],
    ["a book naming nothing", { kind: "source" }, { kind: "inert", name: "a source window" }],
    ["a preparing book naming nothing", { kind: "preparing" }, { kind: "inert", name: "a book being prepared" }],
    ["an unknown kind naming a source", { kind: "original_scan", sourceId: "s" }, { kind: "book", sourceId: "s", extractionId: null, showPath: false }],
    ["an unknown kind naming a reading", { kind: "chapter_map", sourceId: "s", extractionId: "e" }, { kind: "book", sourceId: "s", extractionId: "e", showPath: false }],
    ["an unknown panel naming a reading", { kind: "panel", panel: "outline", extractionId: "e" }, { kind: "book", sourceId: null, extractionId: "e", showPath: false }],
    ["an unknown panel", { kind: "panel", panel: "outline" }, { kind: "inert", name: "an outline window" }],
    ["an unknown kind naming nothing", { kind: "whiteboard_v9", boardId: "b" }, { kind: "inert", name: "a whiteboard v9 window" }],
    ["no content", null, { kind: "inert", name: "a window with nothing to show" }],
    ["not an object", "source", { kind: "inert", name: "a window with nothing to show" }],
    ["no kind", { sourceId: "s" }, { kind: "book", sourceId: "s", extractionId: null, showPath: false }],
  ])("%s", (_name, stored, expected) => {
    expect(restoreContent(stored)).toEqual(expected);
  });

  it("covers every window the fixture workspace stores, and every kind of the content reference", () => {
    const stored = fixtureDeskState().desks.flatMap((desk) => desk.slots.flatMap((slot) => slot.windows));
    for (const window of stored) {
      if (window.kind === "pad_stack") continue;
      expect(restoreContent(window.content)).toEqual(KEEP);
    }
    // Every kind the type knows restores without throwing (a type-level list: a new kind must be added here).
    const kinds: Record<ContentRefDto["kind"], true> = {
      source: true, video: true, pad: true, lesson: true, thread: true, compare: true, panel: true, figure_notebook: true, preparing: true,
    };
    for (const kind of Object.keys(kinds)) expect(() => restoreContent({ kind })).not.toThrow();
  });

  it("opens a restored book on its reading, or as being prepared when it has none", () => {
    expect(bookContent("s", "e", false)).toEqual({ kind: "source", sourceId: "s", extractionId: "e", view: "render" });
    expect(bookContent("s", "e", true)).toEqual({ kind: "video", sourceId: "s", extractionId: "e" });
    expect(bookContent("s", null, false)).toEqual({ kind: "preparing", sourceId: "s" });
  });
});

// Relations, curved links and the gather order (spec §6.5, §6.6).
import { describe, expect, it } from "vitest";
import { fromDeskState } from "../model/workspace";
import { fixtureDeskState } from "../../../fixtures/desks/workspace";
import { curvedLinks, gatherOrder, relationsOf } from "./links";

const ws = fromDeskState(fixtureDeskState());

describe("relations", () => {
  it("a book's panels on its desk are explicit links (3); the same book on another desk is 2", () => {
    const relations = relationsOf(ws, "fx_w_book");
    expect(relations).toEqual([
      { windowId: "fx_w_guide", weight: 3, label: "its panel" },
      { windowId: "fx_w_path", weight: 3, label: "its panel" },
      { windowId: "fx_w_book_range", weight: 2, label: "same book" },
    ]);
    expect(relationsOf(ws, "fx_w_guide")[0]).toEqual({ windowId: "fx_w_book", weight: 3, label: "its book" });
  });

  it("a window opened beside another is linked to it both ways", () => {
    const opened = { ...ws, windows: { ...ws.windows, fx_w_paper: { ...ws.windows.fx_w_paper, view: { openedBeside: "fx_w_video" } } } };
    expect(relationsOf(opened, "fx_w_video")).toContainEqual({ windowId: "fx_w_paper", weight: 3, label: "opened beside" });
    expect(relationsOf(opened, "fx_w_paper")).toContainEqual({ windowId: "fx_w_video", weight: 3, label: "opened beside" });
  });
});

describe("curved links", () => {
  const from = { x: 0, y: 0, w: 760, h: 600 };

  it("dips below the cards on the same row and is a vertical S to another row, its label at u = .82", () => {
    const [same, other] = curvedLinks(from, [
      { rect: { x: 1540, y: 0, w: 760, h: 600 }, relation: { windowId: "a", weight: 3, label: "its panel" } },
      { rect: { x: 0, y: 1000, w: 760, h: 600 }, relation: { windowId: "b", weight: 2, label: "same book" } },
    ]);
    const control = (d: string) => d.match(/C ([\d.-]+) ([\d.-]+), ([\d.-]+) ([\d.-]+)/)!.slice(1).map(Number);
    const [, c1y, , c2y] = control(same.d);
    expect(c1y).toBeGreaterThan(600);
    expect(c2y).toBeGreaterThan(600);
    const [, d1y, , d2y] = control(other.d);
    expect(d1y).toBe(d2y);
    expect(d1y).toBe((600 + 1600) / 2);
    // Neighbouring links are offset 26 world px apart.
    expect(Number(other.d.split(" ")[1]) - Number(same.d.split(" ")[1])).toBe(26);
    expect(same.labelAt.x).toBeGreaterThan(1540);
  });
});

describe("gather", () => {
  it("keeps the unlinked windows before the focus, then the focus, the linked by weight, then the rest", () => {
    const slots = [["a"], ["b"], ["focus"], ["c"], ["linked1"], ["d"], ["linked2"]];
    const related = [{ windowId: "linked2", weight: 3 as const, label: "" }, { windowId: "linked1", weight: 2 as const, label: "" }];
    expect(gatherOrder(slots, "focus", related).order).toEqual([["a"], ["b"], ["focus"], ["linked2"], ["linked1"], ["c"], ["d"]]);
  });

  it("moves four at most and counts the rest that stayed", () => {
    const slots = [["focus"], ...["1", "2", "3", "4", "5", "6"].map((id) => [id])];
    const related = ["1", "2", "3", "4", "5", "6"].map((id) => ({ windowId: id, weight: 3 as const, label: "" }));
    const { order, stayed } = gatherOrder(slots, "focus", related);
    expect(order.slice(0, 5)).toEqual([["focus"], ["1"], ["2"], ["3"], ["4"]]);
    expect(stayed).toBe(2);
  });
});

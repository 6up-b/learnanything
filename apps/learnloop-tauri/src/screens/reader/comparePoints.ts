// Reader CA4: the table by point, its pure parts (ux_reader_compare_ask_v1 §5; K13).
//
// * `rowChips`: a row's agreement chips, exactly the relations its pairs
//   returned (§5.1's table): "the same claim" only when every pair of the
//   books quoted on the row returned it; every other label when at least one
//   pair did; "only in Axler" when one book alone has a verified cell. Never a
//   summary of them, never a relation the comparison didn't return, no colour.
// * `chipPairs`: the pairs behind a row's chips (X4), in the table's order.
// * The layout: by point (the grid, or cards by point when the pane is too
//   narrow for two columns or the window is below the app's breakpoint) or by
//   book (remembered per device); a v1 comparison has only by book.
// * `moveCell`: the grid's roving focus (§5.5).
import type { CompareTableDto, ComparePointDto, ComparePointRelationDto } from "../../api/dto";
import { NARROW_BREAKPOINT } from "../workbench/splitWidth";

/** The comparison's relations (compare_sources' RELATIONS, unchanged), in the chips' order. */
export const RELATION_ORDER = ["equivalent", "different_assumptions", "different_notation", "disagreement", "unclear"] as const;

/** The shipped plain words (CompareKeep's fine labels, less RW4d's mapping-only "complementary"). */
export const CHIP_LABELS: Record<(typeof RELATION_ORDER)[number], string> = {
  equivalent: "the same claim",
  different_assumptions: "different assumptions",
  different_notation: "different notation",
  disagreement: "they disagree",
  unclear: "unclear",
};

export type RowChip = { kind: "relation"; relation: string; label: string } | { kind: "only"; key: string; label: string };

/** The books' short names by column key. */
export function columnTitles(table: CompareTableDto): Map<string, string> {
  return new Map(table.rows.map((row) => [row.key, row.sourceTitle ?? "a source"]));
}

export function quotedKeys(point: ComparePointDto): string[] {
  return point.cells.filter((cell) => cell.status === "quoted").map((cell) => cell.key);
}

/** §5.1: a row's chips, from its pairs' relations and nothing else. */
export function rowChips(point: ComparePointDto, titles: Map<string, string>): RowChip[] {
  const quoted = quotedKeys(point);
  if (quoted.length === 1) {
    return [{ kind: "only", key: quoted[0], label: `only in ${titles.get(quoted[0]) ?? "one book"}` }];
  }
  const returned = point.relations.map((relation) => relation.relation);
  const pairsOnRow = (quoted.length * (quoted.length - 1)) / 2;
  const chips: RowChip[] = [];
  for (const relation of RELATION_ORDER) {
    const count = returned.filter((value) => value === relation).length;
    if (!count) continue;
    // "the same claim" needs every compared pair on the row to have said it.
    if (relation === "equivalent" && (count !== returned.length || returned.length < pairsOnRow)) continue;
    chips.push({ kind: "relation", relation, label: CHIP_LABELS[relation] });
  }
  return chips;
}

/** X4: the pairs behind a row's chips, in the chips' order. */
export function chipPairs(point: ComparePointDto): ComparePointRelationDto[] {
  const order = (relation: string) => {
    const at = (RELATION_ORDER as readonly string[]).indexOf(relation);
    return at < 0 ? RELATION_ORDER.length : at;
  };
  return [...point.relations].sort((a, b) => order(a.relation) - order(b.relation));
}

/** A row no book fills: a requested view "not found in your library". */
export function notFound(point: ComparePointDto): boolean {
  return quotedKeys(point).length === 0;
}

export type CompareLayout = "by_point" | "by_book";
export const LAYOUT_KEY = "ll.compare.layout";

/** The remembered layout on this device (by point unless the learner chose by book). */
export function readLayout(): CompareLayout {
  try {
    return window.localStorage.getItem(LAYOUT_KEY) === "by_book" ? "by_book" : "by_point";
  } catch {
    return "by_point";
  }
}

export function writeLayout(layout: CompareLayout): void {
  try {
    window.localStorage.setItem(LAYOUT_KEY, layout);
  } catch {
    // A per-device preference: the table works without it.
  }
}

/** Layout bounds (not learned constants): the point column, the narrowest
 *  readable cell, and the learner's column, in CSS px. */
export const POINT_COLUMN_PX = 190;
export const READABLE_CELL_PX = 220;
export const YOU_COLUMN_PX = 170;

/** Cards by point when the window is below the breakpoint or the pane can't
 *  hold the point column and two books at a readable width. */
export function cardsByPoint(paneWidth: number | null, windowWidth: number): boolean {
  if (windowWidth < NARROW_BREAKPOINT) return true;
  return paneWidth !== null && paneWidth > 0 && paneWidth < POINT_COLUMN_PX + 2 * READABLE_CELL_PX;
}

export interface CellPosition {
  row: number;
  col: number;
}

/** The grid's roving focus: arrows move a cell, Home/End reach the row's ends.
 *  `cols(row)` is how many focusable cells a row has (a hidden row has one). */
export function moveCell(at: CellPosition, key: string, rows: number, cols: (row: number) => number): CellPosition | null {
  const clampCol = (row: number, col: number) => Math.max(0, Math.min(col, cols(row) - 1));
  switch (key) {
    case "ArrowDown":
      return at.row + 1 < rows ? { row: at.row + 1, col: clampCol(at.row + 1, at.col) } : at;
    case "ArrowUp":
      return at.row > 0 ? { row: at.row - 1, col: clampCol(at.row - 1, at.col) } : at;
    case "ArrowRight":
      return { row: at.row, col: clampCol(at.row, at.col + 1) };
    case "ArrowLeft":
      return { row: at.row, col: clampCol(at.row, at.col - 1) };
    case "Home":
      return { row: at.row, col: 0 };
    case "End":
      return { row: at.row, col: cols(at.row) - 1 };
    default:
      return null;
  }
}

/** Whether a table is a comparison by point (else it renders by book, as today). */
export function byPoint(table: CompareTableDto): boolean {
  return table.contract === "source_compare.v2" && Array.isArray(table.points);
}

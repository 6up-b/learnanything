import type { ReaderSourceSearchDto } from "../../api/dto";

/** Slice 2 T6: say which evidence ranked the library search hits, never more.
 *  Typing runs the local keyword search; Enter adds meaning and, for a
 *  conceptual question, a rewritten query. No basis means retrieval is off
 *  (plain substring search), which is described by the hit count alone. */
export function searchBasisLabel(result: ReaderSourceSearchDto): string {
  const basis = result.basis;
  if (!basis || basis === "none") return "";
  const parts = basis.split("+");
  const used = parts.includes("meaning")
    ? parts.includes("rewrite")
      ? " · keyword + meaning + rewritten question"
      : " · keyword + meaning"
    : " · keyword match";
  return result.deep ? used : `${used} · Enter also searches by meaning`;
}

import type { ReaderSourceSearchDto } from "../../api/dto";

/** Slice 2 T6: say which evidence ranked the library search hits, never more.
 *  The label is built from the parts of ``basis`` that actually ranked hits
 *  (keyword, meaning, a rewritten question). Typing runs the local keyword
 *  search; the "Enter also searches by meaning" hint appears only when the
 *  stored index is ready (or partly ready) for a meaning search. No basis means
 *  retrieval is off (plain substring search), described by the hit count alone. */
export function searchBasisLabel(result: ReaderSourceSearchDto): string {
  const basis = result.basis;
  if (!basis || basis === "none") return "";
  const parts = new Set(basis.split("+"));
  const used: string[] = [];
  if (parts.has("keyword")) used.push("keyword");
  if (parts.has("meaning")) used.push(`meaning${coverage(result)}`);
  if (parts.has("rewrite")) used.push("rewritten question");
  if (used.length === 0) return "";
  const label = used.length === 1 && used[0] === "keyword" ? " · keyword match" : ` · ${used.join(" + ")}`;
  if (result.deep || !meaningReady(result)) return label;
  return `${label} · Enter also searches by meaning${coverage(result)}`;
}

function meaningReady(result: ReaderSourceSearchDto): boolean {
  const status = result.meaningSearch?.status;
  return status === "ready" || status === "partial";
}

/** " (3 of 4 sources)" while some sources are not embedded yet. */
function coverage(result: ReaderSourceSearchDto): string {
  const meaning = result.meaningSearch;
  if (!meaning || meaning.status !== "partial") return "";
  return ` (${meaning.sourcesCovered} of ${meaning.sources} sources)`;
}
